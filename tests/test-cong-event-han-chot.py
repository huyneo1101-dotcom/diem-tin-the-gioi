#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TEST CỔNG "event-scan KHÔNG CÓ HẠN CHÓT" (scripts/state.py + 02 file quy trình).

⚠ VÌ SAO CÓ FILE NÀY — sự cố THẬT sáng 25/09/2026:
Bản tin gửi 04:19. Phiên CI claim `event-scan` lúc 04:19:47 rồi 35 giây sau tự gọi
`state.py skip event-scan "het gio truoc han chot 04:45 ..."`; phiên 04:41 claim được (exit 0)
rồi lại SKIP đúng lý do đó. `HAN_CHOT` 04:45 chỉ áp cho BẢN TIN, event-scan được chạy tới 09:00.
Các mốc 06:30 và 07:00 exit 10 ở web-scan rồi kết thúc luôn, không ai chạy bù. Hậu quả: cả ngày
không có tin sự kiện / tập trận / think-tank, canary 10:48 kêu «cả 4 mốc không hoàn tất».

Hai lớp vá, test canh cả hai:
  (i)  `state.py skip event-scan` TỪ CHỐI (exit 13) ghi chú viện cớ giờ/hạn chót;
  (ii) prompt CI + quy trình local: exit 10 ở web-scan ca sáng vẫn phải claim event-scan.

Chạy:
    python3 tests/test-cong-event-han-chot.py
    python3 tests/test-cong-event-han-chot.py --tu-kiem   # chứng minh test BẮT ĐƯỢC lỗi
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unicodedata

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
STATE_THAT = REPO / "scripts" / "state.py"
PROMPT_THAT = REPO / ".github" / "prompts" / "web-scan-ci.md"
ROUTINE_THAT = REPO / "docs" / "routine-web-scan.md"

STATE_PY = pathlib.Path(os.environ.get("STATE_PY") or STATE_THAT)
PROMPT = pathlib.Path(os.environ.get("PROMPT_MD") or PROMPT_THAT)
ROUTINE = pathlib.Path(os.environ.get("ROUTINE_MD") or ROUTINE_THAT)

O = ["--slot", "sang"]
KET = []


def chay(kho, *args):
    env = dict(os.environ, STATE_LOGS_DIR=str(kho))
    env.pop("DIEMTIN_PHIEN_TEST", None)
    # claim đi qua cổng khung giờ (ca sáng 03:00-09:00) — ép qua để test chạy được mọi giờ.
    them = ["--bo-cong-gio", "test cong han chot"] if args[0] == "claim" else []
    return subprocess.run([sys.executable, str(STATE_PY), *args, *O, *them],
                          capture_output=True, text=True, env=env)


def trang_thai(kho, pipe="event-scan"):
    p = pathlib.Path(kho) / "state.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8")).get(pipe, {}).get("lastStatus")


def ca(ten, dat):
    KET.append((ten, bool(dat)))


def chay_ca():
    # ── PHẢI CHẶN ──────────────────────────────────────────────────────────────
    chan = {
        "nguyên văn 04:20": "het gio truoc han chot 04:45 - da tieu ton nhieu thoi gian",
        "nguyên văn 04:41": "chi con ~4 phut khi claim khoa, khong du de chay pipeline moi",
        "có dấu, gõ NFD": unicodedata.normalize("NFD", "hết giờ trước hạn chót"),
        "chỉ ghi 'không kịp'": "khong kip xac minh su kien",
    }
    for ten, note in chan.items():
        with tempfile.TemporaryDirectory() as kho:
            chay(kho, "claim", "event-scan")
            r = chay(kho, "skip", "event-scan", note)
            ca(f"PHẢI CHẶN skip event-scan [{ten}] → exit 13, cờ giữ RUNNING",
               r.returncode == 13 and trang_thai(kho) == "RUNNING")

    # ── PHẢI CHO QUA ───────────────────────────────────────────────────────────
    with tempfile.TemporaryDirectory() as kho:
        chay(kho, "claim", "event-scan")
        r = chay(kho, "skip", "event-scan", "mang hong, 3/3 nguon tra 503")
        ca("cho qua skip event-scan lý do thật (mạng hỏng)",
           r.returncode == 0 and trang_thai(kho) == "SKIP")
    with tempfile.TemporaryDirectory() as kho:
        chay(kho, "claim", "web-scan")
        r = chay(kho, "skip", "web-scan", "het gio truoc han chot 04:45")
        ca("cho qua skip web-scan có chữ hạn chót (cổng chỉ áp event-scan)",
           r.returncode == 0 and trang_thai(kho, "web-scan") == "SKIP")
    with tempfile.TemporaryDirectory() as kho:
        chay(kho, "claim", "event-scan")
        r = chay(kho, "fail", "event-scan", "het gio job 130 phut")
        ca("cho qua fail event-scan (fail không chặn lần sau, không cần cổng)",
           r.returncode == 0 and trang_thai(kho) == "FAIL")

    # ── QUY TRÌNH: exit 10 ở web-scan ca sáng vẫn phải claim event-scan ────────
    p = unicodedata.normalize("NFC", PROMPT.read_text(encoding="utf-8"))
    ca("prompt CI: exit 10 web-scan → nhảy sang BƯỚC 6",
       "NHẢY THẲNG SANG BƯỚC 6" in p)
    ca("prompt CI: khai event-scan KHÔNG CÓ HẠN CHÓT", "event-scan KHÔNG CÓ HẠN CHÓT" in p)
    d = unicodedata.normalize("NFC", ROUTINE.read_text(encoding="utf-8"))
    ca("quy trình local: lối SKIP ca sáng vẫn claim event-scan",
       "Ca SÁNG: trước khi kết thúc, chạy thêm đúng 01 lệnh `state.py claim event-scan`" in d)


def bao():
    hong = [t for t, d in KET if not d]
    for t, d in KET:
        print(("  ✅ " if d else "  ❌ ") + t)
    print(f"{len(KET) - len(hong)}/{len(KET)} ca đạt")
    return 0 if not hong else 1


def tu_kiem():
    """Dựng bản hỏng (gỡ đúng dòng vá), chạy lại test, mỗi bản hỏng PHẢI làm test rớt."""
    src = STATE_THAT.read_text(encoding="utf-8")
    dong = 'if cmd == "skip" and pipeline == "event-scan" and ly_do_han_chot(note):'
    assert dong in src, "không tìm thấy dòng vá trong state.py — tự kiểm mất răng"
    pr = PROMPT_THAT.read_text(encoding="utf-8")
    rt = ROUTINE_THAT.read_text(encoding="utf-8")
    hong = {
        "state.py bỏ cổng": ("STATE_PY", "state.py", src.replace(dong, "if False:")),
        "state.py chỉ so chữ không dấu": ("STATE_PY", "state.py", src.replace(
            's = "".join(c for c in s if unicodedata.category(c) != "Mn").replace("đ", "d")',
            "pass")),
        "prompt CI mất lối sang BƯỚC 6": ("PROMPT_MD", "p.md",
                                         pr.replace("NHẢY THẲNG SANG BƯỚC 6", "KẾT THÚC ÊM")),
        "quy trình local mất dòng claim": ("ROUTINE_MD", "r.md",
                                          rt.replace("Ca SÁNG: trước khi kết thúc", "Ca SÁNG")),
    }
    loi = 0
    with tempfile.TemporaryDirectory() as tam:
        for ten, (bien, file, noi_dung) in hong.items():
            f = pathlib.Path(tam) / file
            f.write_text(noi_dung, encoding="utf-8")
            r = subprocess.run([sys.executable, __file__], capture_output=True, text=True,
                               env=dict(os.environ, **{bien: str(f)}))
            bat = r.returncode != 0
            print(("  ✅ bắt được: " if bat else "  ❌ LỌT: ") + ten)
            loi += 0 if bat else 1
    # Bản thật phải đạt, không thì tự kiểm vô nghĩa.
    r = subprocess.run([sys.executable, __file__], capture_output=True, text=True)
    print(("  ✅ " if r.returncode == 0 else "  ❌ ") + "bản thật đạt")
    return 0 if loi == 0 and r.returncode == 0 else 1


if __name__ == "__main__":
    if "--tu-kiem" in sys.argv:
        sys.exit(tu_kiem())
    chay_ca()
    sys.exit(bao())
