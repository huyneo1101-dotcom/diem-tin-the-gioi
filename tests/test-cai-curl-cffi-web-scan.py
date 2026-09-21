#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TEST CỔNG "claude-web-scan.yml PHẢI CÀI curl_cffi TRƯỚC KHI QUÉT".

⚠ VÌ SAO CÓ FILE NÀY — sự cố thật phiên sáng 21/09/2026:
`harvest-ci.yml` và `probe-sources.yml` đều có bước `pip install curl_cffi` trước khi quét,
nhưng `claude-web-scan.yml` (workflow chính ra bản tin sáng sớm 5 chủ đề) lại THIẾU bước này
từ đầu — chỉ có Setup Python rồi cài thẳng Claude Code. Thiếu gói giả vân tay TLS Chrome khiến
`harvest.py`/`ngay_that.py` lùi về 1 lượt curl trần, bị chặn ở đúng nhóm nguồn hay dò vân tay
TLS (Bloomberg, state.gov, The Hill, Lockheed newsroom, The War Zone, Zona Militar,
BusinessMirror). Hậu quả đo được: cổng NGÀY ĐĂNG THẬT chặn 12/29 tin ứng viên (~41%) trong một
phiên, 6/9 mục hụt sàn 5 tin/ngày (logs/loai-tin.md mục 2026-09-21).

Ca chính ở đây là ca PHẢI CHẶN: dựng bản workflow đã gỡ đúng bước cài curl_cffi, khẳng định
cổng này ĐỎ.

Chạy:
    python3 tests/test-cai-curl-cffi-web-scan.py
    python3 tests/test-cai-curl-cffi-web-scan.py --tu-kiem   # chứng minh test này BẮT ĐƯỢC lỗi

Không cần thư viện ngoài.
"""
import pathlib
import re
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent

YML_THAT = REPO / ".github" / "workflows" / "claude-web-scan.yml"

BUOC_CAN = "pip install --quiet curl_cffi"
BUOC_TRUOC = "Cài Claude Code"  # bước phải nạp curl_cffi trước bước này


def kiem_tra(duong_yml: pathlib.Path) -> list[str]:
    """Trả về danh sách lỗi (rỗng = đạt)."""
    loi = []
    if not duong_yml.exists():
        return [f"không thấy file {duong_yml}"]
    noi_dung = duong_yml.read_text(encoding="utf-8")
    if BUOC_CAN not in noi_dung:
        loi.append(f"thiếu bước cài curl_cffi (không thấy chuỗi {BUOC_CAN!r})")
        return loi
    vi_tri_cai = noi_dung.find(BUOC_CAN)
    vi_tri_claude = noi_dung.find(BUOC_TRUOC)
    if vi_tri_claude != -1 and vi_tri_cai > vi_tri_claude:
        loi.append("bước cài curl_cffi nằm SAU bước cài Claude Code/quét — cài trễ vô nghĩa")
    # Bước phải nằm trong nhánh có điều kiện gate (không chạy khi thiếu secret)
    doan = noi_dung[max(0, vi_tri_cai - 300):vi_tri_cai]
    if "steps.gate.outputs.run == 'true'" not in doan:
        loi.append("bước cài curl_cffi không gắn điều kiện gate.outputs.run — có thể chạy dù đã bỏ qua phiên")
    return loi


def tu_kiem() -> int:
    print("TỰ KIỂM — dựng bản đã gỡ bước cài curl_cffi, cổng phải ĐỎ")
    print("═" * 78)
    goc = YML_THAT.read_text(encoding="utf-8")
    khop = re.search(
        r"\n {6}# Vân tay TLS Chrome.*?run: python3 -m pip install --quiet curl_cffi \|\| true\n",
        goc, re.S,
    )
    if not khop:
        print("  ✗ KHÔNG áp được phép gỡ: không tìm thấy đúng khối bước cài curl_cffi trong "
              "claude-web-scan.yml (mã nguồn đã đổi → sửa lại test).")
        return 1
    hong = goc.replace(khop.group(0), "\n")
    d = pathlib.Path(tempfile.mkdtemp(prefix="web-scan-yml-hong-"))
    duong_hong = d / "claude-web-scan.yml"
    duong_hong.write_text(hong, encoding="utf-8")
    loi = kiem_tra(duong_hong)
    ok = bool(loi)
    print(f"  {'✓' if ok else '✗'} bản gỡ bước cài curl_cffi phải bị cổng chặn")
    print(f"        │ lỗi bắt được: {loi or 'KHÔNG BẮT ĐƯỢC GÌ'}")
    print("═" * 78)
    if not ok:
        print("✗ TỰ KIỂM THẤT BẠI — cổng không bắt được bản hỏng.")
        return 1
    print("✓ tự kiểm đạt — cổng bắt được bản thiếu bước cài curl_cffi.")
    return 0


def main() -> int:
    if "--tu-kiem" in sys.argv:
        return tu_kiem()
    print("TEST CỔNG claude-web-scan.yml PHẢI CÀI curl_cffi")
    print(f"(bản đang thử: {YML_THAT})")
    loi = kiem_tra(YML_THAT)
    if loi:
        print("✗ HỎNG:")
        for l in loi:
            print(f"  - {l}")
        return 1
    print("✓ đạt — claude-web-scan.yml có bước cài curl_cffi trước khi quét.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
