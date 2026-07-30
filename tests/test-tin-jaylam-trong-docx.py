#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test cho mục 5 "Tin Jay Lâm gửi" trong file .docx bản tin (thêm 30/07/2026, Huy sửa lại
thiết kế: KHÔNG gửi file riêng, mà GỘP THẲNG vào .docx bản tin tối như hàng ngày vẫn làm).

    python3 tests/test-tin-jaylam-trong-docx.py

Canh 3 việc dễ hỏng câm nhất của kiểu tích hợp này (mục 17 CLAUDE.md — hỏng thì im lặng cho
qua, không ai biết): (1) mục Jay Lâm CHỈ được vào bản buổi TỐI, không phải buổi sáng; (2) bộ
lọc chống trùng phải chặn được tin Jay Lâm gửi mà quét thường ĐÃ có; (3) tin bị lọc trùng vẫn
phải được đánh dấu `da_gop`, kẻo nó nằm lại vĩnh viễn và tối nào cũng bị lọc lại.

Không chạm mạng thật: `doc_tin_jaylam_chua_gop`/`danh_dau_da_gop_jaylam` đều bị monkeypatch.
Yêu cầu `pip3 install python-docx` (giống mọi test khác đụng `make_docx.py`).
"""
import contextlib
import datetime
import io
import json
import os
import pathlib
import shutil
import sys
import tempfile
import zoneinfo

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
GS = pathlib.Path(os.environ.get("MAKEDOCX_DIR") or (REPO / ".github" / "scripts"))
sys.path.insert(0, str(GS))

import make_docx as MD          # noqa: E402
from docx import Document       # noqa: E402

VN = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")
MD.prev_data = lambda: None     # xem test-so-da-gui.py — bỏ phụ thuộc lịch sử git thật

SANG = datetime.datetime(2026, 7, 30, 6, 0, tzinfo=VN)
TOI = datetime.datetime(2026, 7, 30, 21, 0, tzinfo=VN)

DATA_GIA = {
    "generatedAt": "2026-07-30",
    "worldNews": [{"date": "2026-07-30", "_addedDate": "2026-07-30",
                   "title": "Tin thế giới quét được", "category": "Chính trị",
                   "sourceUrl": "https://reuters.com/tin-the-gioi"}],
    "usNews": [], "exercises": [],
}

CA = []


def kiem(ten, dat):
    dat = bool(dat)
    CA.append((ten, dat))
    print(("✓" if dat else "✗") + " " + ten)


class ThuMucGia:
    """Ghim cwd vào thư mục tạm có index.html giả, dọn sạch khi thoát."""

    def __enter__(self):
        self.cu = os.getcwd()
        self.d = pathlib.Path(tempfile.mkdtemp(prefix="jaylam-docx-"))
        (self.d / "index.html").write_text(
            "<html><script>var DATA = " + json.dumps(DATA_GIA, ensure_ascii=False)
            + ";</script></html>", encoding="utf-8")
        os.chdir(self.d)
        return self.d

    def __exit__(self, *a):
        os.chdir(self.cu)
        shutil.rmtree(self.d, ignore_errors=True)
        return False


def chay(now, doc_fn, danhdau_fn):
    goc_doc, goc_danhdau = MD.doc_tin_jaylam_chua_gop, MD.danh_dau_da_gop_jaylam
    MD.doc_tin_jaylam_chua_gop, MD.danh_dau_da_gop_jaylam = doc_fn, danhdau_fn
    buf_out, buf_err = io.StringIO(), io.StringIO()
    try:
        with ThuMucGia(), contextlib.redirect_stdout(buf_out), \
                contextlib.redirect_stderr(buf_err):
            MD.main(now=now)
    finally:
        MD.doc_tin_jaylam_chua_gop, MD.danh_dau_da_gop_jaylam = goc_doc, goc_danhdau
    out, err = buf_out.getvalue(), buf_err.getvalue()
    dong = [l for l in out.splitlines() if l.startswith("DOCX=")]
    path = dong[-1][len("DOCX="):].strip() if dong else ""
    full = "\n".join(p.text for p in Document(path).paragraphs) if path else ""
    return full, err


# --- ca la_buoi_toi() thuần, không cần dựng file --------------------------
kiem("la_buoi_toi() sáng sớm -> False",
     MD.la_buoi_toi(datetime.datetime(2026, 7, 30, 5, 0, tzinfo=VN)) is False)
kiem("la_buoi_toi() đúng ngưỡng 14h -> True",
     MD.la_buoi_toi(datetime.datetime(2026, 7, 30, 14, 0, tzinfo=VN)) is True)
kiem("la_buoi_toi() tối -> True",
     MD.la_buoi_toi(datetime.datetime(2026, 7, 30, 21, 0, tzinfo=VN)) is True)

# --- ca 1 — PHẢI CHẶN: buổi SÁNG không được đụng Jay Lâm dù có tin chờ ----
goi = {"doc": 0}


def doc_co_tin():
    goi["doc"] += 1
    return [{"id": 1, "ten": "Jay Lâm", "ten_file": "a.docx",
              "noi_dung": "Một tin lạ Jay Lâm gửi", "created_at": "2026-07-30T02:00:00Z"}]


def danhdau_khong_goi(ids):
    raise AssertionError("KHÔNG được đánh dấu gộp ở buổi sáng")


full, _ = chay(SANG, doc_co_tin, danhdau_khong_goi)
kiem("buổi sáng: KHÔNG gọi doc_tin_jaylam_chua_gop()", goi["doc"] == 0)
kiem("buổi sáng: file không có mục 'Tin Jay Lâm gửi'", "Tin Jay Lâm gửi" not in full)

# --- ca 2 — luồng bình thường buổi TỐI ------------------------------------
danhdau_goi = []


def doc_binh_thuong():
    return [{"id": 2, "ten": "Jay Lâm", "ten_file": "b.docx",
              "noi_dung": "Một tin hoàn toàn khác quét tin không có",
              "created_at": "2026-07-30T09:15:00Z"}]


def danhdau_ghi(ids):
    danhdau_goi.extend(ids)


full2, _ = chay(TOI, doc_binh_thuong, danhdau_ghi)
kiem("buổi tối: có mục 'Tin Jay Lâm gửi'", "Tin Jay Lâm gửi" in full2)
kiem("buổi tối: có nội dung tin", "Một tin hoàn toàn khác" in full2)
kiem("buổi tối: vẫn giữ tin quét thường", "Tin thế giới quét được" in full2)
kiem("buổi tối: đánh dấu đã gộp đúng id", danhdau_goi == [2])

# --- ca 3 — PHẢI CHẶN: chống trùng với tin quét thường ĐÃ CÓ --------------
danhdau_goi.clear()


def doc_trung():
    return [{"id": 3, "ten": "Jay Lâm", "ten_file": "c.docx",
              "noi_dung": "Tin thế giới quét được", "created_at": "2026-07-30T10:00:00Z"}]


full3, err3 = chay(TOI, doc_trung, danhdau_ghi)
kiem("chống trùng: KHÔNG hiện mục 'Tin Jay Lâm gửi' khi trùng tin đã có",
     "Tin Jay Lâm gửi" not in full3)
kiem("chống trùng: VẪN đánh dấu đã gộp (không nằm lại vĩnh viễn)", danhdau_goi == [3])
kiem("chống trùng: có in cảnh báo lý do", "nghi trùng" in err3)

# --- ca 4 — chống trùng GIỮA các dòng Jay Lâm với nhau, giữ dòng ĐẦU ------
danhdau_goi.clear()


def doc_hai_dong_trung_nhau():
    return [
        {"id": 4, "ten": "Jay Lâm", "ten_file": "d1.docx",
         "noi_dung": "Sự kiện đặc biệt hôm nay tại Hà Nội", "created_at": "2026-07-30T08:00:00Z"},
        {"id": 5, "ten": "Jay Lâm", "ten_file": "d2.docx",
         "noi_dung": "Sự kiện đặc biệt hôm nay tại Hà Nội", "created_at": "2026-07-30T08:05:00Z"},
    ]


full4, _ = chay(TOI, doc_hai_dong_trung_nhau, danhdau_ghi)
kiem("trùng nội bộ Jay Lâm: chỉ hiện MỘT lần trong file",
     full4.count("Sự kiện đặc biệt hôm nay tại Hà Nội") == 1)
kiem("trùng nội bộ Jay Lâm: cả 2 id đều được đánh dấu đã gộp",
     sorted(danhdau_goi) == [4, 5])

# --- ca 5 — PHẢI CHẶN: không có Supabase key -> [] êm, KHÔNG làm vỡ file -
# Dùng đúng hàm THẬT (chưa bị monkeypatch — `chay()` luôn phục hồi bản gốc sau mỗi lần
# gọi), để đo đúng nhánh `_jaylam_anon_key()`/`DT_BOT_KEY` rỗng của chính production code.
os.environ.pop("SUPABASE_ANON_KEY", None)
os.environ.pop("DT_BOT_KEY", None)
full5, err5 = chay(TOI, MD.doc_tin_jaylam_chua_gop, lambda ids: None)
kiem("thiếu SUPABASE_ANON_KEY/DT_BOT_KEY: không có mục Jay Lâm, không lỗi",
     "Tin Jay Lâm gửi" not in full5)
kiem("thiếu key: có cảnh báo rõ ràng", "Thiếu SUPABASE_ANON_KEY" in err5)

so_dat = sum(1 for _, ok in CA if ok)
print(f"\n{so_dat}/{len(CA)} ca đạt")
sys.exit(0 if so_dat == len(CA) else 1)
