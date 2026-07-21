#!/usr/bin/env python3
"""Cờ trạng thái riêng cho từng pipeline — logs/state.json.

VÌ SAO CÓ FILE NÀY: trước đây cả 2 pipeline dùng chung `DATA.generatedAt` làm cờ
idempotent. Action nhập tin từ Drive chạy 08:00 bump generatedAt = hôm nay → routine
quét 6-agent buổi tối thấy "đã xong hôm nay" và SKIP vĩnh viễn (xNews kẹt 3 ngày,
tập trận/sự kiện ngoại giao không ai cập nhật). `generatedAt` là NGÀY BẢN TIN hiển thị
trên web — không phải cờ chạy việc. Tách ra đây, mỗi pipeline một dòng riêng.

Pipeline đang dùng:
  drive-import  — GitHub Action import-news-from-drive.yml (08:00 & 20:00 VN)
  web-scan      — routine Claude quét 6+1 agent Sonnet (08:15 & 20:15 VN, dự phòng 09:15 & 21:15)

CỜ TÁCH THEO BUỔI, không phải theo ngày: mỗi ngày có 2 bản tin (sáng + tối). Nếu chỉ so
theo ngày thì bản sáng xong sẽ làm bản tối cùng ngày bị SKIP oan — đúng cái bệnh mà việc
tách cờ khỏi generatedAt vừa sửa, chỉ khác quy mô. Buổi tự suy từ giờ VN lúc chạy:
trước 14:00 = "sang", từ 14:00 = "toi" (che được cả lần fire dự phòng 09:15 và 21:15).

Dùng:
  python3 scripts/state.py check web-scan       # in RUN / SKIP; exit 0 = nên chạy, 10 = buổi này đã xong
  python3 scripts/state.py show                 # in toàn bộ trạng thái
  python3 scripts/state.py done web-scan "+12 tin"   # xong VÀ có nội dung  -> chặn lần fire sau
  python3 scripts/state.py skip web-scan "khong co file"  # chạy nhưng không có gì -> KHÔNG chặn
  python3 scripts/state.py fail web-scan "session limit"  # lỗi -> KHÔNG chặn, lần sau quét lại
  ... thêm --slot sang|toi để ép buổi (chạy tay ngoài giờ); mặc định tự suy từ giờ VN.
"""
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

os.environ["TZ"] = "Asia/Ho_Chi_Minh"
try:
    time.tzset()
except AttributeError:  # Windows
    pass

STATE_PATH = Path(__file__).resolve().parent.parent / "logs" / "state.json"
PIPELINES = ("drive-import", "web-scan")
SLOTS = ("sang", "toi")
SLOT_SPLIT_HOUR = 14  # < 14:00 VN = buổi sáng (fire 08:15 + dự phòng 09:15); >= 14:00 = buổi tối


def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def current_slot() -> str:
    return "sang" if datetime.now().hour < SLOT_SPLIT_HOUR else "toi"


def load() -> dict:
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save(state: dict) -> None:
    STATE_PATH.parent.mkdir(exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def record(pipeline: str, status: str, note: str = "", slot: str = None) -> dict:
    """Ghi nhận 1 lần chạy. CHỈ status DONE mới đẩy lastSuccess của buổi (tức mới chặn fire sau)."""
    slot = slot or current_slot()
    state = load()
    entry = state.get(pipeline, {})
    entry["lastRunAt"] = datetime.now().astimezone().isoformat(timespec="seconds")
    entry["lastSlot"] = slot
    entry["lastStatus"] = status
    entry["note"] = note
    if status == "DONE":
        success = entry.get("lastSuccess") or {}
        success[slot] = today()
        entry["lastSuccess"] = success
    state[pipeline] = entry
    save(state)
    return entry


def last_success(entry: dict, slot: str) -> str:
    return (entry.get("lastSuccess") or {}).get(slot)


def should_run(pipeline: str, slot: str = None) -> bool:
    slot = slot or current_slot()
    return last_success(load().get(pipeline, {}), slot) != today()


def main() -> None:
    args = sys.argv[1:]
    slot = None
    if "--slot" in args:
        i = args.index("--slot")
        slot = args[i + 1] if i + 1 < len(args) else ""
        if slot not in SLOTS:
            print(f"--slot phai la: {' | '.join(SLOTS)}", file=sys.stderr)
            sys.exit(2)
        del args[i : i + 2]
    cmd = args[0] if args else "show"

    if cmd == "show":
        state = load()
        if not state:
            print(f"(chua co {STATE_PATH.name})")
            return
        now_slot = slot or current_slot()
        print(f"Hom nay {today()}, buoi hien tai: {now_slot}\n")
        for name, e in state.items():
            done = " · ".join(f"{s}={last_success(e, s) or '-'}" for s in SLOTS)
            flag = "" if last_success(e, now_slot) == today() else f"  <- buoi {now_slot} CHUA xong"
            print(f"{name:<14} {done}  lastStatus={e.get('lastStatus','-')} lastRunAt={e.get('lastRunAt','-')}{flag}")
            if e.get("note"):
                print(f"{'':<14} note: {e['note']}")
        return

    if len(args) < 2 or args[1] not in PIPELINES:
        print(f"Pipeline phai la mot trong: {', '.join(PIPELINES)}", file=sys.stderr)
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    pipeline = args[1]
    use_slot = slot or current_slot()

    if cmd == "check":
        if should_run(pipeline, use_slot):
            print(f"RUN — {pipeline} buoi {use_slot} ngay {today()} chua xong, tien hanh quet.")
            sys.exit(0)
        e = load()[pipeline]
        print(
            f"SKIP — {pipeline} buoi {use_slot} ngay {today()} DA XONG "
            f"(lan chay cuoi {e.get('lastRunAt')}). Khong lam lai."
        )
        sys.exit(10)

    if cmd in ("done", "skip", "fail"):
        note = args[2] if len(args) > 2 else ""
        e = record(pipeline, cmd.upper(), note, use_slot)
        print(f"{pipeline}[{use_slot}]: {e['lastStatus']} @ {e['lastRunAt']}" + (f" — {note}" if note else ""))
        return

    print(f"Lenh khong hop le: {cmd}", file=sys.stderr)
    print(__doc__, file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
