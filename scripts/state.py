#!/usr/bin/env python3
"""Cờ trạng thái riêng cho từng pipeline — logs/state.json.

VÌ SAO CÓ FILE NÀY: trước đây cả 2 pipeline dùng chung `DATA.generatedAt` làm cờ
idempotent. Action nhập tin từ Drive chạy 08:00 bump generatedAt = hôm nay → routine
quét 6-agent buổi tối thấy "đã xong hôm nay" và SKIP vĩnh viễn (xNews kẹt 3 ngày,
tập trận/sự kiện ngoại giao không ai cập nhật). `generatedAt` là NGÀY BẢN TIN hiển thị
trên web — không phải cờ chạy việc. Tách ra đây, mỗi pipeline một dòng riêng.

Pipeline đang dùng:
  drive-import  — GitHub Action import-news-from-drive.yml (08:00 & 20:00 VN)
  web-scan      — routine Claude quét 6 agent Sonnet (19:00/20:00/21:00 VN)

Dùng:
  python3 scripts/state.py check web-scan       # in RUN / SKIP; exit 0 = nên chạy, 10 = đã xong hôm nay
  python3 scripts/state.py show                 # in toàn bộ trạng thái
  python3 scripts/state.py done web-scan "+12 tin"   # xong VÀ có nội dung  -> chặn lần fire sau
  python3 scripts/state.py skip web-scan "khong co file"  # chạy nhưng không có gì -> KHÔNG chặn
  python3 scripts/state.py fail web-scan "session limit"  # lỗi -> KHÔNG chặn, lần sau quét lại
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


def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def load() -> dict:
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save(state: dict) -> None:
    STATE_PATH.parent.mkdir(exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def record(pipeline: str, status: str, note: str = "") -> dict:
    """Ghi nhận 1 lần chạy. CHỈ status DONE mới đẩy lastSuccessDate (tức mới chặn lần fire sau)."""
    state = load()
    entry = state.get(pipeline, {})
    entry["lastRunAt"] = datetime.now().astimezone().isoformat(timespec="seconds")
    entry["lastStatus"] = status
    entry["note"] = note
    if status == "DONE":
        entry["lastSuccessDate"] = today()
    state[pipeline] = entry
    save(state)
    return entry


def should_run(pipeline: str) -> bool:
    return load().get(pipeline, {}).get("lastSuccessDate") != today()


def main() -> None:
    args = sys.argv[1:]
    cmd = args[0] if args else "show"

    if cmd == "show":
        state = load()
        if not state:
            print(f"(chua co {STATE_PATH.name})")
            return
        for name, e in state.items():
            flag = "" if e.get("lastSuccessDate") == today() else "  <- hom nay CHUA xong"
            print(
                f"{name:<14} lastSuccessDate={e.get('lastSuccessDate','-')} "
                f"lastStatus={e.get('lastStatus','-')} lastRunAt={e.get('lastRunAt','-')}{flag}"
            )
            if e.get("note"):
                print(f"{'':<14} note: {e['note']}")
        return

    if len(args) < 2 or args[1] not in PIPELINES:
        print(f"Pipeline phai la mot trong: {', '.join(PIPELINES)}", file=sys.stderr)
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    pipeline = args[1]

    if cmd == "check":
        if should_run(pipeline):
            print(f"RUN — {pipeline} chua chay xong hom nay ({today()}), tien hanh quet.")
            sys.exit(0)
        e = load()[pipeline]
        print(f"SKIP — {pipeline} da xong hom nay ({today()}), lan chay cuoi {e.get('lastRunAt')}. Khong lam lai.")
        sys.exit(10)

    if cmd in ("done", "skip", "fail"):
        note = args[2] if len(args) > 2 else ""
        e = record(pipeline, cmd.upper(), note)
        print(f"{pipeline}: {e['lastStatus']} @ {e['lastRunAt']}" + (f" — {note}" if note else ""))
        return

    print(f"Lenh khong hop le: {cmd}", file=sys.stderr)
    print(__doc__, file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
