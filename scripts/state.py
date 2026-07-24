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

KHOÁ CHỐNG CHẠY CHỒNG (thêm 22/07/2026): mốc chính và mốc dự phòng chỉ cách nhau 60 phút
mà một phiên quét mất ~60 phút, nên `check` (chỉ biết ĐÃ XONG hay chưa) sẽ để lần fire dự
phòng khởi động phiên THỨ HAI song song — hai phiên cùng quét, cùng push, tốn token đôi và
đụng nhau lúc rebase. `claim` giành khoá trước khi quét; `done/skip/fail` nhả khoá.
Khoá dùng HEARTBEAT chứ không phải hạn giờ cứng: phiên chết giữa chừng mà khoá không tự
mở thì còn tệ hơn không có khoá (mất luôn bản tin của buổi đó). Không có nhịp nào trong
LOCK_STALE_MIN phút -> coi như phiên đã chết, cho phiên mới giành khoá.

Dùng:
  python3 scripts/state.py claim web-scan       # GIÀNH khoá + kiểm tra; 0 = quét đi, 10 = xong rồi, 11 = đang chạy
  python3 scripts/state.py beat web-scan        # nhịp tim — gọi ở MỖI checkpoint, nếu không khoá sẽ tự hết hạn
  python3 scripts/state.py check web-scan       # CHỈ hỏi, không giành khoá (dùng để chẩn đoán)
  python3 scripts/state.py show                 # in toàn bộ trạng thái
  python3 scripts/state.py done web-scan "+12 tin"   # xong VÀ có nội dung  -> chặn lần fire sau, nhả khoá
  python3 scripts/state.py skip web-scan "khong co file"  # chạy nhưng không có gì -> nhả khoá, KHÔNG chặn
  python3 scripts/state.py fail web-scan "session limit"  # lỗi -> nhả khoá, KHÔNG chặn, lần sau quét lại
  ... thêm --slot sang|toi để ép buổi (chạy tay ngoài giờ); mặc định tự suy từ giờ VN.
  ... thêm --force cho `claim` để cướp khoá của phiên đang chạy (chỉ khi biết chắc nó đã chết).
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
PIPELINES = ("drive-import", "web-scan", "event-scan")
SLOTS = ("sang", "toi")
SLOT_SPLIT_HOUR = 14  # < 14:00 VN = buổi sáng (fire 09:15 + dự phòng 10:15); >= 14:00 = buổi tối
# Không có nhịp tim trong ngần này phút -> coi phiên đang chạy là đã chết, cho giành lại khoá.
# Đặt 30': phiên khoẻ ghi checkpoint dày hơn thế nhiều (sau baseline, sau agent, sau script).
LOCK_STALE_MIN = 30


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


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def minutes_since(stamp: str):
    """Số phút kể từ mốc ISO; None nếu không đọc được."""
    try:
        return (datetime.now().astimezone() - datetime.fromisoformat(stamp)).total_seconds() / 60
    except (TypeError, ValueError):
        return None


def is_running(entry: dict) -> bool:
    """Đang có phiên chạy VÀ nhịp tim còn tươi. Nhịp cũ quá = phiên đã chết, khoá tự mở."""
    if entry.get("lastStatus") != "RUNNING":
        return False
    age = minutes_since(entry.get("heartbeat", ""))
    return age is not None and age < LOCK_STALE_MIN


def record(pipeline: str, status: str, note: str = "", slot: str = None) -> dict:
    """Ghi nhận 1 lần chạy. CHỈ status DONE mới đẩy lastSuccess của buổi (tức mới chặn fire sau).

    Mọi status kết thúc (DONE/SKIP/FAIL) đều NHẢ KHOÁ bằng cách xoá heartbeat.
    """
    slot = slot or current_slot()
    state = load()
    entry = state.get(pipeline, {})
    entry["lastRunAt"] = now_iso()
    entry["lastSlot"] = slot
    entry["lastStatus"] = status
    entry["note"] = note
    if status == "RUNNING":
        entry["heartbeat"] = now_iso()
    else:
        entry.pop("heartbeat", None)  # nhả khoá
    if status == "DONE":
        success = entry.get("lastSuccess") or {}
        success[slot] = today()
        entry["lastSuccess"] = success
    state[pipeline] = entry
    save(state)
    return entry


def beat(pipeline: str) -> str:
    """Nhịp tim: gia hạn khoá. Trả về thông báo để in ra."""
    state = load()
    entry = state.get(pipeline, {})
    if entry.get("lastStatus") != "RUNNING":
        return f"{pipeline}: khong o trang thai RUNNING — bo qua nhip tim"
    entry["heartbeat"] = now_iso()
    state[pipeline] = entry
    save(state)
    return f"{pipeline}: nhip tim @ {entry['heartbeat']}"


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
    force = "--force" in args
    if force:
        args.remove("--force")
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
            if is_running(e):
                age = minutes_since(e.get("heartbeat", "")) or 0
                print(f"{'':<14} 🔒 DANG CHAY — nhip tim {age:.0f}' truoc (khoa het han sau {LOCK_STALE_MIN}')")
            elif e.get("lastStatus") == "RUNNING":
                print(f"{'':<14} ⚠️  danh dau RUNNING nhung nhip tim da cu -> coi nhu CHET, khoa da mo")
            if e.get("note"):
                print(f"{'':<14} note: {e['note']}")
        return

    if len(args) < 2 or args[1] not in PIPELINES:
        print(f"Pipeline phai la mot trong: {', '.join(PIPELINES)}", file=sys.stderr)
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    pipeline = args[1]
    use_slot = slot or current_slot()

    if cmd in ("check", "claim"):
        entry = load().get(pipeline, {})
        if not should_run(pipeline, use_slot):
            print(
                f"SKIP — {pipeline} buoi {use_slot} ngay {today()} DA XONG "
                f"(lan chay cuoi {entry.get('lastRunAt')}). Khong lam lai."
            )
            sys.exit(10)
        if is_running(entry) and not force:
            age = minutes_since(entry.get("heartbeat", "")) or 0
            print(
                f"SKIP — {pipeline} DANG CO PHIEN KHAC CHAY (nhip tim {age:.0f}' truoc, bat dau "
                f"{entry.get('lastRunAt')}). Khong chay chong len. Neu chac chan phien do da chet: "
                f"them --force."
            )
            sys.exit(11)
        if cmd == "claim":
            record(pipeline, "RUNNING", "dang quet", use_slot)
            extra = " (da CUOP khoa bang --force)" if force and is_running(entry) else ""
            print(f"RUN — {pipeline} buoi {use_slot} ngay {today()} chua xong, da giu khoa{extra}. Quet di.")
        else:
            print(f"RUN — {pipeline} buoi {use_slot} ngay {today()} chua xong (check: KHONG giu khoa).")
        sys.exit(0)

    if cmd == "beat":
        print(beat(pipeline))
        return

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
