#!/usr/bin/env python3
"""CỔNG: trần agent con của phiên quét phải còn nguyên ở CẢ BA nơi phiên đọc.

VÌ SAO CÓ FILE NÀY — sự cố thật sáng 05/10/2026: phiên local 04:35 quét lại đủ khi CI 04:00
vẫn chạy, dùng 06 agent con và hai vòng bổ sung (~11 triệu token quy đổi, chung ví hạn mức với
CI) mà vẫn hụt sàn 5/6 mục vì cổng NGÀY ĐĂNG THẬT chặn các nguồn lớn. Luật "tối đa 01 vòng bổ
sung" chỉ nằm trong chữ, nên bộ test này canh chữ đó không bị gỡ hoặc quay về "1–2 vòng".

Chạy:  python3 tests/test-tran-agent-quet.py
       python3 tests/test-tran-agent-quet.py --tu-kiem
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FILES = {
    "SKILL": ROOT / ".claude/skills/quet-tin/SKILL.md",
    "ROUTINE": ROOT / "docs/routine-web-scan.md",
    "PROMPT_CI": ROOT / ".github/prompts/web-scan-ci.md",
}
CUM_TRAN = "TRẦN AGENT CON"
CUM_MOT_VONG = "01 agent bổ sung duy nhất"
CUM_CU = "1–2 vòng bổ sung là đủ"


def do(noi_dung):
    """Trả danh sách lỗi (rỗng = đạt)."""
    loi = []
    for ten, nd in noi_dung.items():
        if CUM_TRAN not in nd:
            loi.append(f"{ten}: mất khối «{CUM_TRAN}»")
        if CUM_MOT_VONG not in nd:
            loi.append(f"{ten}: mất câu «{CUM_MOT_VONG}»")
    if CUM_CU in noi_dung["SKILL"]:
        loi.append("SKILL: còn câu cũ cho phép 1–2 vòng bổ sung")
    return loi


def doc():
    return {k: v.read_text(encoding="utf-8") for k, v in FILES.items()}


def main(argv):
    nd = doc()
    loi = do(nd)
    for l in loi:
        print("  ✗", l)
    if not loi:
        print("  ✓ trần agent con còn nguyên ở 3 nơi, câu cũ đã gỡ")
    if "--tu-kiem" not in argv:
        return 1 if loi else 0
    if loi:
        print("✗ bản đúng đã đỏ, sửa trước khi tự kiểm")
        return 1
    hong = {
        "SKILL gỡ khối trần": ("SKILL", lambda s: s.replace(CUM_TRAN, "XXX")),
        "ROUTINE gỡ câu một vòng": ("ROUTINE", lambda s: s.replace(CUM_MOT_VONG, "XXX")),
        "PROMPT CI gỡ khối trần": ("PROMPT_CI", lambda s: s.replace(CUM_TRAN, "XXX")),
        "SKILL quay về 1–2 vòng": ("SKILL", lambda s: s + "\n" + CUM_CU),
    }
    lot = 0
    for ten, (k, f) in hong.items():
        h = dict(nd)
        h[k] = f(nd[k])
        bat = bool(do(h))
        print(("  ✓ bắt được: " if bat else "  ✗ LỌT: ") + ten)
        lot += 0 if bat else 1
    print(("✅ TỰ KIỂM ĐẠT" if not lot else f"✗ TỰ KIỂM TRƯỢT {lot}") + f" ({len(hong) - lot}/{len(hong)})")
    return 1 if lot else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
