#!/usr/bin/env python3
"""GHI LOG NGÀY RỒI PUSH — chịu được nhiều phiên quét ghi cùng lúc.

VÌ SAO CÓ FILE NÀY (sự cố thật sáng 02/08/2026):
sáng đó có **04 phiên** cùng đụng `logs/scan-2026-08-02.log` — CI 03:47 · local 04:30 ·
lớp vét 04:47 · một phiên gọi lại. Mỗi phiên append một dòng vào CUỐI file rồi
`git pull --rebase` khi push bị từ chối. Hai dòng thêm vào cùng một vị trí là **xung đột
văn bản**, rebase hỏng để repo ở trạng thái rebase dở, và phiên local 05:30 vào thì
`git pull --rebase` chết ngay dòng lệnh ĐẦU TIÊN:

    error: Pulling is not possible because you have unmerged files.

Repo kẹt như thế thì **mọi phiên sau đều chết ở Bước 1** — kể cả phiên tối 20:47/21:15,
là phiên có hạn chót gửi 22:00. Không có tiếng kêu nào ngoài một dòng `fatal`.

Đây ĐÚNG lớp lỗi đã vá cho `logs/da-gui-email.json` hồi 30/07 bằng `ghi_so_push.py`; log
ngày chỉ là một file append-only khác. Nên script này **KHÔNG chép lại logic git** mà gọi
thẳng `ghi_so_push.day_len_remote()` — hai bản logic song song chắc chắn lệch nhau, mà
lệch âm thầm.

CÁCH DÙNG (phiên quét, sau khi đã ghi log bằng tool Edit/Write như thường):
    python3 scripts/ghi_log_push.py --file logs/scan-2026-08-02.log \\
        --nhan "log: SKIP web-scan phien sang som (local 05:30)"

⚠️ CHỈ dùng cho commit **chỉ chứa log**. Commit bản tin (`index.html` + `logs/`) vẫn đi
đường cũ: `index.html` KHÔNG phải append-only, hai lô tin cùng chèn vào đầu mảng là xung
đột thật, phải xử theo mục "Nhập tin từ Google Drive" trong CLAUDE.md.

Bộ test canh: `tests/test-ghi-log-push.py`.
"""
import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".github" / "scripts"))

import ghi_so_push as gsp  # noqa: E402  (phải chèn sys.path trước)


def hop_nhat_dong(dong_cua_minh):
    """Trả callback ghép dòng của phiên mình vào bản REMOTE, giữ thứ tự, KHÔNG nhân đôi.

    Idempotent: `day_len_remote` gọi lại ở mỗi vòng retry, chạy bao nhiêu lần cũng ra một
    kết quả. So theo NỘI DUNG dòng — hai phiên viết y hệt nhau thì coi như một, vì log
    trùng từng chữ là dòng thừa chứ không phải dòng mất.
    """
    def _ghep(p):
        cu = []
        if p.exists():
            cu = p.read_text(encoding="utf-8").splitlines()
        da_co = set(cu)
        them = [d for d in dong_cua_minh if d.strip() and d not in da_co]
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("\n".join(cu + them) + "\n", encoding="utf-8")
    return _ghep


def ghi_va_push(rel, nhan="", vong=gsp.VONG_MAC_DINH, ngu=None):
    """Đẩy phần log của phiên mình lên `main`. Trả 0 = xong, 1 = hết vòng chưa push được."""
    p = ROOT / rel
    if not p.exists():
        print(f"::error::khong co file {rel} — phien phai ghi log TRUOC khi goi script nay")
        return 2

    # ── PHA 0: chụp dòng của phiên mình TRƯỚC khi đụng git ──
    # Bắt buộc: `day_len_remote` sẽ `checkout FETCH_HEAD -- <file>`, tức GHI ĐÈ bản local
    # bằng bản remote. Đọc sau bước đó là đọc log của phiên KHÁC, và phần của mình mất sạch.
    dong_cua_minh = p.read_text(encoding="utf-8").splitlines()
    print(f"log cua phien nay: {len([d for d in dong_cua_minh if d.strip()])} dong")

    gsp._git("config", "user.name", "claude-scan-local")
    gsp._git("config", "user.email", "noreply@anthropic.com")
    kw = {"vong": vong, "nhan": "log ngay",
          "hau_qua": "Log TRONG thi khong lan duoc phien nao hong o dau — "
                     "xem tests/test-ghi-log-push.py"}
    if ngu is not None:
        kw["ngu"] = ngu
    return gsp.day_len_remote(rel, hop_nhat_dong(dong_cua_minh),
                              nhan or f"log: cap nhat {pathlib.Path(rel).name}", **kw)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--file", required=True,
                    help="đường dẫn TƯƠNG ĐỐI từ gốc repo, vd logs/scan-2026-08-02.log")
    ap.add_argument("--nhan", default="", help="commit message")
    ap.add_argument("--vong", type=int, default=gsp.VONG_MAC_DINH)
    a = ap.parse_args(argv)
    return ghi_va_push(a.file, a.nhan, a.vong)


if __name__ == "__main__":
    sys.exit(main())
