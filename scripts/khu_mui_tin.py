#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CỔNG KHỬ MÙI A.I CHO TIÊU ĐỀ VÀ NỘI DUNG TỪNG TIN — dựng 14/11/2026.

Huy chốt 14/11/2026, nguyên văn: *"Nội dung và tiêu đề các bài phải chạy khử mùi A.I"*.
Áp cho mọi tin mới nạp qua `add_news.py`: tiêu đề (`title`, `name`) đo như MỘT câu, còn
`summary` và `significance` tách từng câu rồi đo từng câu.

Máy chấm là BẢN GỐC DUY NHẤT `App/QuanSu/khu-mui-ai.py` (hàm `cau_bi_chan`, cùng ngưỡng cấp
câu mà cổng dàn ý của bài phân tích dùng). Không chép bảng mẫu sang đây: hai bản sẽ tách
nhánh ở lần Huy chê thêm từ kế tiếp mà không ai thấy.

Đo trước khi cắm, 77 tin 12-14/11/2026: bản máy chấm cũ chặn 14 tin, trong đó 09 tin là chặn
oan («điều trần», họ «Trần», «giữa kỳ 3/11», «trát đòi») — đã vá ở máy chấm cùng lượt (ca
302-305 của `QuanSu/test-khu-mui-ai.py`). Sau vá còn 09/77 tin bị chặn, đều là lỗi giọng
thật: «bà + tên riêng» thay cho chức danh, khuôn «không A mà B», «phép thử», «chạm».

⛔ KHÔNG BAO GIỜ CHẶN TIN (Huy chốt 14/11/2026, nguyên văn: *"đừng có chặn tin, chỉ thay đổi cách
dịch, cách viết thôi"*). Khử mùi là việc của NGƯỜI VIẾT tin, làm TRƯỚC khi nạp: agent quét chạy
`python3 scripts/khu_mui_tin.py <new_items.json>`, viết lại đúng câu bị nêu, rồi mới gọi
`add_news.py`. Trong `add_news.py` cổng chỉ in nhắc, lô vẫn nạp đủ. Thiếu máy chấm (máy dự phòng
GitHub không có thư mục `App/QuanSu`) cũng chỉ in một dòng.

Dùng: python3 scripts/khu_mui_tin.py <new_items.json>   # mã 1 = còn câu nên viết lại
"""
import importlib.util
import os
import pathlib
import re
import unicodedata

KHU_MUI = pathlib.Path(os.environ.get("DIEMTIN_KHU_MUI")
                       or pathlib.Path.home() / "Claude" / "App" / "QuanSu" / "khu-mui-ai.py")

# Mảng nào của lô `new_items.json` mang chữ tiếng Việt do agent viết.
MANG_TIN = ("worldNews", "usNews", "baomoiNews", "xNews")
MANG_SU_KIEN = ("exerciseUpdates", "dipEventUpdates", "newDipEvents", "newExercises")
TRUONG_TIEU_DE = ("title", "name")
TRUONG_NOI_DUNG = ("summary", "significance")

_may = None


def nap_may_cham():
    """Nạp `khu-mui-ai.py` một lần. Trả None nếu không có file (máy dự phòng GitHub)."""
    global _may
    if _may is not None:
        return _may
    if not KHU_MUI.is_file():
        return None
    spec = importlib.util.spec_from_file_location("khu_mui_ai", KHU_MUI)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    if not hasattr(m, "cau_bi_chan"):
        raise RuntimeError(f"{KHU_MUI} không còn hàm cau_bi_chan — máy chấm đã đổi, sửa cổng này")
    _may = m
    return m


def tach_cau(text: str) -> list:
    t = unicodedata.normalize("NFC", str(text or "")).strip()
    return [c.strip() for c in re.split(r"(?<=[.!?])\s+", t) if c.strip()]


def cac_cau_cua_lo(new_items: dict) -> list:
    """[(nhãn, câu)] của mọi tiêu đề và mọi câu nội dung trong lô."""
    ra = []

    def mot_tin(nhan, it):
        for k in TRUONG_TIEU_DE:
            if it.get(k):
                ra.append((f"{nhan}.{k}", unicodedata.normalize("NFC", str(it[k])).strip()))
        for k in TRUONG_NOI_DUNG:
            for i, c in enumerate(tach_cau(it.get(k)), 1):
                ra.append((f"{nhan}.{k} câu {i}", c))

    for mang in MANG_TIN:
        for idx, it in enumerate(new_items.get(mang) or []):
            mot_tin(f"{mang}[{idx}]", it)
    for mang in MANG_SU_KIEN:
        for idx, ev in enumerate(new_items.get(mang) or []):
            if mang.startswith("new"):
                mot_tin(f"{mang}[{idx}]", ev)
            for j, it in enumerate(ev.get("items") or []):
                mot_tin(f"{mang}[{idx}].items[{j}]", it)
    return ra


def cau_can_viet_lai(new_items: dict) -> tuple:
    """(số câu đã đo, [dòng mô tả câu nên viết lại]). Máy chấm thiếu thì số câu = -1."""
    cau = cac_cau_cua_lo(new_items)
    may = nap_may_cham()
    if may is None:
        return -1, []
    hong = []
    for nhan, c in cau:
        chan, _diem, ghi, _ngay = may.cau_bi_chan(c)
        if chan:
            ly_do = [g.strip() for g in ghi if g.startswith("    ") or "—" in g][:2]
            hong.append(f"{nhan}: {c[:140]}\n      " + "\n      ".join(ly_do))
    return len(cau), hong


def kiem_lo(new_items: dict) -> list:
    """Dòng nhắc để `add_news.py` in. KHÔNG ném lỗi, KHÔNG chặn tin dù câu có mùi."""
    if not cac_cau_cua_lo(new_items):
        return []
    n, hong = cau_can_viet_lai(new_items)
    if n < 0:
        return [f"⚠ khử mùi KHÔNG CHẠY: không thấy máy chấm {KHU_MUI} — lô vẫn nạp đủ"]
    if not hong:
        return [f"✓ khử mùi: {n} câu tiêu đề và nội dung đều sạch"]
    return [f"⚠ khử mùi: {len(hong)}/{n} câu nên viết lại lần sau (lô VẪN NẠP ĐỦ, không chặn tin):"] \
        + ["  · " + h for h in hong]


def main(argv) -> int:
    import json
    if len(argv) != 2:
        print(__doc__)
        return 2
    lo = json.loads(pathlib.Path(argv[1]).read_text(encoding="utf-8"))
    n, hong = cau_can_viet_lai(lo)
    if n < 0:
        print(f"⚠ không thấy máy chấm {KHU_MUI} — tự soát theo LỚP THỨ TƯ trong SKILL.md")
        return 0
    if not hong:
        print(f"✓ {n} câu tiêu đề và nội dung đều sạch — nạp được")
        return 0
    print(f"✗ {len(hong)}/{n} câu nên viết lại (sửa cách viết, GIỮ NGUYÊN tin) rồi chạy lại:")
    for h in hong:
        print("  - " + h)
    return 1


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))
