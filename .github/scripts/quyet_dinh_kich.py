#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quyết định job quét này có được kích notify hay không — ĐỌC CỜ, KHÔNG ĐỌC `git log`.

VÌ SAO CÓ FILE NÀY (sự cố thật tối 31/07/2026 — Huy nhận HAI bản tin, 21:24 và 21:26):
bước "Kích email/push/morning" của `claude-web-scan.yml` trước đây quyết định bằng
    git pull --rebase origin main
    new_msgs=$(git log <base.sha>..HEAD --format=%s)
    echo "$new_msgs" | grep -qiE '^Cap nhat ban tin'  &&  gh workflow run notify-email.yml
Chú thích trong yml khai ý định là *"commit mới TRONG JOB NÀY"*, nhưng phép đo lại chạy SAU
`git pull` nên khoảng `base..HEAD` nuốt luôn commit của **phiên khác** vừa push xen vào.

Số đo hôm đó:
| 14:00:19Z | run 30636762079 (mốc 20:47) khởi động, giành khoá, quét thật |
| 14:11:17Z | run 30637541239 (lớp vét) khởi động → chụp base.sha → `claim` trả exit 10 → SKIP |
| 14:23:49Z | phiên chính commit `4fffa97 Cap nhat ban tin 31/07` → kích → BẢN 1 (9 tin) |
| 14:25:33Z | phiên VÉT ghi commit log rồi tới bước kích, `git pull` kéo `4fffa97` về |
| 14:25:50Z | grep khớp commit của người ta → kích lần 2 → BẢN 2 ("không có tin mới") |

⛔ ĐỪNG "SỬA CHO GỌN" BẰNG CÁCH ĐO GIT SỚM HƠN. Phép đo thuần git không phân biệt được ở đây:
phiên SKIP cũng phải `pull --rebase` để push nổi commit log của chính nó, nên commit của phiên
kia đã nằm trong cây local TRƯỚC cả bước kích. Đo `HEAD` trước pull cũng thủng đúng ca đó.

⇒ Ý ĐỊNH KHAI BẰNG LỜI: chỉ phiên nào TỰ TAY gọi `scripts/state.py done <pipeline>` mới để lại
cờ (`state.py:ghi_co_da_nap`). Phiên SKIP không được gọi `done` (luật routine: SKIP thì chỉ ghi
log) nên vĩnh viễn không có cờ. Cùng bài học với `tu_dong=1` · `TELEGRAM_BAT_BUOC` ·
`DIEMTIN_PHIEN_TEST` — mặc định là KHÔNG kích, quên khai thì mất một lần gửi (canary 22:45 bắt
được), chứ không phải gửi thừa trong im lặng.

Cờ nằm ở thư mục tạm nên **chỉ sống trong đúng một job** — job khác, máy khác không thấy. Đó
chính là thứ `git log` không có.

Dùng:
    python3 .github/scripts/quyet_dinh_kich.py            # in ban_tin=… / su_kien=… ra stdout
    python3 .github/scripts/quyet_dinh_kich.py --tu-kiem  # chứng minh bộ ca bắt được lỗi

Mã thoát: 0 = quyết định xong (đọc hai dòng để biết kích gì) · 2 = KHÔNG đọc được cờ.
Fail-CLOSED CÓ TIẾNG: hỏng thì mã 2 làm step ĐỎ và không kích — "không đọc được" khác "không
có gì để kích", lẫn hai cái đó vào nhau đúng là kiểu chết câm file này sinh ra để chặn.
"""
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO / "scripts"))

# Dùng CHUNG đường dẫn cờ với state.py — KHÔNG chép lại quy ước tên file sang đây. Hai nơi tự
# ghép tên thì lệch âm thầm ngay lần đổi tên đầu tiên, và hỏng theo hướng "không bao giờ kích".
import state  # noqa: E402

# pipeline -> tên biến in ra cho workflow
NHAN = (("web-scan", "ban_tin"), ("event-scan", "su_kien"))


def da_nap(pipeline: str) -> bool:
    """Phiên NÀY có tự tay `done` pipeline đó không? Lỗi đọc đĩa thì ném — fail-closed CÓ TIẾNG."""
    return state.co_path(pipeline).exists()


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--tu-kiem" in argv:
        return tu_kiem()
    try:
        ket_qua = [(bien, da_nap(pipeline)) for pipeline, bien in NHAN]
    except OSError as loi:
        print(f"::error::khong doc duoc co da-nap: {loi}", file=sys.stderr)
        return 2
    for bien, co in ket_qua:
        print(f"{bien}={'1' if co else '0'}")
    return 0


# ─────────────────────────── TỰ KIỂM ───────────────────────────
def _chay(thu_muc) -> dict:
    """Chạy main() trong tiến trình (KHÔNG subprocess — subprocess nạp lại bản THẬT trên đĩa
    nên --tu-kiem không tráo được bản hỏng, ca sẽ xanh trên cả bản đúng lẫn bản hỏng)."""
    import io
    import contextlib

    cu = os.environ.get(state.CO_DIR_ENV)
    os.environ[state.CO_DIR_ENV] = str(thu_muc)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            ma = main([])
    finally:
        if cu is None:
            os.environ.pop(state.CO_DIR_ENV, None)
        else:
            os.environ[state.CO_DIR_ENV] = cu
    ra = dict(
        dong.split("=", 1) for dong in buf.getvalue().splitlines() if "=" in dong
    )
    ra["_ma"] = str(ma)
    return ra


def tu_kiem() -> int:
    import tempfile

    ca = []
    with tempfile.TemporaryDirectory() as td:
        thu_muc = Path(td)

        # [1] PHẢI CHẶN — hồi quy đúng sự cố 31/07: phiên SKIP không có cờ nào, dù cây git
        #     của nó ĐÃ chứa commit `Cap nhat ban tin` của phiên khác (kéo về lúc rebase).
        ra = _chay(thu_muc)
        ca.append(("[1] phien SKIP (khong co co) -> KHONG kich", ra.get("ban_tin") == "0"))

        # [2] chống chặn oan — phiên thật `done web-scan` thì PHẢI kích bản tin.
        state.co_path("web-scan")  # chỉ để chắc hàm còn tồn tại
        os.environ[state.CO_DIR_ENV] = str(thu_muc)
        state.ghi_co_da_nap("web-scan")
        ra = _chay(thu_muc)
        ca.append(("[2] da `done web-scan` -> KICH ban tin", ra.get("ban_tin") == "1"))

        # [3] hai pipeline ĐỘC LẬP — cờ bản tin không được kéo theo email sự kiện.
        ca.append(("[3] chi co co web-scan -> KHONG kich su kien", ra.get("su_kien") == "0"))

        # [4] chống chặn oan phía sự kiện.
        state.ghi_co_da_nap("event-scan")
        ra = _chay(thu_muc)
        ca.append(("[4] da `done event-scan` -> KICH su kien", ra.get("su_kien") == "1"))

        # [5] fail-CLOSED: thư mục cờ không đọc được thì mã 2, KHÔNG âm thầm trả 0.
        class _No:
            def exists(self):
                raise OSError("gia lap dia hong")

        goc = state.co_path
        state.co_path = lambda p: _No()
        try:
            ra = _chay(thu_muc)
        finally:
            state.co_path = goc
        ca.append(("[5] khong doc duoc co -> ma 2 (fail-closed)", ra.get("_ma") == "2"))

        os.environ.pop(state.CO_DIR_ENV, None)

    do = [t for t, ok in ca if not ok]
    for ten, ok in ca:
        print(("  ✓ " if ok else "  ✗ ") + ten)
    if do:
        print(f"TRUOT: {len(do)}/{len(ca)} ca khong dat")
        return 1
    print(f"DAT {len(ca)}/{len(ca)} ca")
    return 0


if __name__ == "__main__":
    sys.exit(main())
