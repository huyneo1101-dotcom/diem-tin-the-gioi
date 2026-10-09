#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TEST CỔNG "claude-web-scan.yml PHẢI KHAI --model sonnet Ở MỌI LỆNH claude -p".

VÌ SAO CÓ FILE NÀY: CI không đọc ~/.claude/settings.json của máy nên lệnh `claude -p` không
khai model sẽ lấy model mặc định của gói (nhiều khả năng Opus). Phiên quét 04:00 chạy tới 700
lượt, là chỗ ăn hạn mức lớn nhất sáng sớm. Quét theo playbook là việc theo khuôn nên chạy
Sonnet (mục 23 CLAUDE.md). Gỡ cờ này là hỏng câm: bản tin vẫn ra, chỉ có hạn mức cạn nhanh hơn.

Chạy:
    python3 tests/test-model-web-scan-ci.py
    python3 tests/test-model-web-scan-ci.py --tu-kiem   # chứng minh test này BẮT ĐƯỢC lỗi
"""
import pathlib
import re
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
YML_THAT = HERE.parent / ".github" / "workflows" / "claude-web-scan.yml"

LENH_CLAUDE = re.compile(r'claude -p "\$\(cat \$PROMPT_FILE\)"[^\n]*')


def kiem_tra(duong_yml: pathlib.Path) -> list[str]:
    if not duong_yml.exists():
        return [f"không thấy file {duong_yml}"]
    noi_dung = duong_yml.read_text(encoding="utf-8")
    lenh = LENH_CLAUDE.findall(noi_dung)
    if not lenh:
        return ["không tìm thấy lệnh `claude -p \"$(cat $PROMPT_FILE)\"` nào, test cần sửa theo mã nguồn mới"]
    loi = []
    # Hai lệnh: lần chạy chính và lần retry. Thiếu cờ ở một trong hai là hỏng.
    if len(lenh) < 2:
        loi.append(f"chỉ thấy {len(lenh)} lệnh claude -p, đáng lẽ phải có 02 (chính + retry)")
    for i, l in enumerate(lenh, 1):
        if "--model sonnet" not in l:
            loi.append(f"lệnh claude -p thứ {i} thiếu `--model sonnet`")
    return loi


def tu_kiem() -> int:
    print("TỰ KIỂM: dựng bản đã gỡ --model sonnet, cổng phải ĐỎ")
    goc = YML_THAT.read_text(encoding="utf-8")
    ca = {
        "gỡ cờ ở MỌI lệnh": goc.replace(" --model sonnet", ""),
        "gỡ cờ ở riêng lệnh retry": goc[::-1].replace(" --model sonnet"[::-1], "", 1)[::-1],
    }
    ket = 0
    for ten, hong in ca.items():
        d = pathlib.Path(tempfile.mkdtemp(prefix="web-scan-model-hong-"))
        p = d / "claude-web-scan.yml"
        p.write_text(hong, encoding="utf-8")
        loi = kiem_tra(p)
        ok = bool(loi) and hong != goc
        print(f"  {'✓' if ok else '✗'} {ten}: {loi or 'KHÔNG BẮT ĐƯỢC GÌ'}")
        ket |= 0 if ok else 1
    print("✓ tự kiểm đạt" if not ket else "✗ TỰ KIỂM THẤT BẠI")
    return ket


def main() -> int:
    if "--tu-kiem" in sys.argv:
        return tu_kiem()
    loi = kiem_tra(YML_THAT)
    if loi:
        print("✗ HỎNG:")
        for l in loi:
            print(f"  - {l}")
        return 1
    print("✓ đạt: mọi lệnh claude -p của claude-web-scan.yml đều khai --model sonnet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
