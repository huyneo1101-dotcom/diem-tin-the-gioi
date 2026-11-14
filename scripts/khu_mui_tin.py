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

⚠ Máy chạy dự phòng trên GitHub không có thư mục `App/QuanSu`. Ở đó cổng KÊU một dòng rồi
cho qua, để bản tin dự phòng vẫn tới tay; trên máy Mac mà thiếu máy chấm thì CHẶN, vì đó là
dấu hiệu đường dẫn đã trôi chứ không phải môi trường khác.
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


def kiem_lo(new_items: dict, bo_cong: str = "") -> list:
    """Trả danh sách dòng cảnh báo để in. Ném ValueError khi có câu bị chặn.

    `bo_cong` = lý do bỏ cổng (cờ `--bo-cong-khu-mui="..."`): vẫn đo và in, nhưng không chặn.
    """
    cau = cac_cau_cua_lo(new_items)
    if not cau:
        return []
    may = nap_may_cham()
    if may is None:
        if os.environ.get("GITHUB_ACTIONS"):
            return [f"⚠ CỔNG KHỬ MÙI KHÔNG CHẠY: máy dự phòng không có {KHU_MUI.name} — "
                    f"{len(cau)} câu nạp mà chưa qua khử mùi"]
        raise ValueError(f"CỔNG KHỬ MÙI: không thấy máy chấm ở {KHU_MUI} — đường dẫn đã trôi, "
                         "sửa KHU_MUI trong scripts/khu_mui_tin.py hoặc đặt DIEMTIN_KHU_MUI")
    hong = []
    for nhan, c in cau:
        chan, _diem, ghi, _ngay = may.cau_bi_chan(c)
        if chan:
            ly_do = [g.strip() for g in ghi if g.startswith("    ") or "—" in g][:2]
            hong.append(f"{nhan}: {c[:140]}\n      " + "\n      ".join(ly_do))
    if not hong:
        return [f"✓ khử mùi: {len(cau)} câu tiêu đề và nội dung đều qua"]
    if bo_cong:
        return [f"⚠ CỔNG KHỬ MÙI bị bỏ qua theo cờ — lý do: {bo_cong}"] + \
               ["  · " + h for h in hong]
    raise ValueError(
        "CỔNG KHỬ MÙI A.I chặn %d/%d câu (Huy chốt 14/11/2026: tiêu đề và nội dung mọi tin phải "
        "qua khử mùi). Viết lại đúng câu bị nêu theo gợi ý rồi nạp lại:\n  - %s"
        % (len(hong), len(cau), "\n  - ".join(hong)))
