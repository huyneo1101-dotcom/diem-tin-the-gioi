#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test cho `scripts/tin_jaylam.py --nap-file` — nạp file .docx CỤC BỘ làm bộ lọc chống trùng.

    python3 tests/test-nap-file-coquan.py
    python3 tests/test-nap-file-coquan.py --tu-kiem   # chứng minh test BẮT ĐƯỢC lỗi

Vì sao có nhánh này (dựng 01/09/2026): `doc_hang_cho()` chỉ thấy file Jay Lâm gửi qua bot
Telegram. File cơ quan Huy nhận rồi quăng vào khung chat nằm ở `~/Downloads/` thì không có
cửa nào vào sổ chống trùng — hôm 01/09 phải bóc 27 link của `ĐTN_M_01.9.2026.docx` bằng tay.

Hai chiều lệch KHÁC HẲN nhau, mỗi chiều có ca canh riêng:
  - bóc SÓT link  -> tin cơ quan đã có vẫn lọt vào bản tin (lặp tin, Huy đọc là thấy);
  - khớp THỪA     -> tin của mình biến mất khỏi bản tin (MẤT TIN, không ai thấy).
Vì thế `chuan_url` cố ý chuẩn hoá HẸP, và ca [17] canh đúng chiều nới tay đó: cắt sạch chuỗi
truy vấn thì hai bài khác nhau trên cùng một trang gộp làm một và một tin bị xoá oan.

Không chạm mạng, không chạm sổ thật: `SO_COQUAN` · `SO_LOAI` · `INDEX` của module đều bị
ghim sang file tạm trong suốt bộ test.
"""
import contextlib
import datetime
import hashlib
import io
import json
import os
import pathlib
import shutil
import subprocess as SP
import sys
import tempfile
import zipfile
import zoneinfo

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SC = pathlib.Path(os.environ.get("TINJAYLAM_DIR") or (REPO / "scripts"))
sys.path.insert(0, str(SC))

import tin_jaylam as TJ          # noqa: E402

VN = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")
NOW = datetime.datetime(2026, 9, 1, 22, 0, tzinfo=VN)

CA = []
TMP = pathlib.Path(tempfile.mkdtemp(prefix=f"napfile-{os.getpid()}-"))


def kiem(ten, dat):
    dat = bool(dat)
    CA.append((ten, dat))
    print(("✓" if dat else "✗") + " " + ten)


# --- dựng file .docx giả ---------------------------------------------------
# Dựng bằng `zipfile` thuần, KHÔNG qua thư viện docx: file này là dữ liệu ĐẦU VÀO của test,
# không phải tài liệu giao cho ai, và bộ test phải chạy được cả trên máy chạy của CI nơi
# không cài python-docx.
XML_DAU = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
           '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
           ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
           '<w:body>')
XML_CUOI = "</w:body></w:document>"
REL_DAU = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
           '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/'
           'relationships">')
REL_CUOI = "</Relationships>"
LOAI_HL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"


def _thoat(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def docx_gia(ten, doan, thieu_document=False, khong_zip=False):
    """Dựng một .docx giả. `doan` = [(chữ, url_hyperlink hoặc None), ...]."""
    p = TMP / ten
    if khong_zip:
        p.write_text("day khong phai zip", encoding="utf-8")
        return p
    body, rels, n = [], [], 0
    for chu, url in doan:
        runs = f"<w:r><w:t xml:space=\"preserve\">{_thoat(chu)}</w:t></w:r>"
        if url:
            n += 1
            rid = f"rId{n}"
            rels.append(f'<Relationship Id="{rid}" Type="{LOAI_HL}" '
                        f'Target="{_thoat(url)}" TargetMode="External"/>')
            runs += (f'<w:hyperlink r:id="{rid}"><w:r><w:t>{_thoat(url)}</w:t></w:r>'
                     "</w:hyperlink>")
        body.append(f"<w:p>{runs}</w:p>")
    with zipfile.ZipFile(p, "w") as z:
        if not thieu_document:
            z.writestr("word/document.xml", XML_DAU + "".join(body) + XML_CUOI)
        z.writestr("word/_rels/document.xml.rels", REL_DAU + "".join(rels) + REL_CUOI)
    return p


def ghim(index_data=None):
    """Ghim mọi đường ghi/đọc của module vào thư mục tạm, và DỌN sổ của ca trước.

    Không dọn thì ca sau đọc phải sổ ca trước để lại — chính chỗ này từng làm ca [25] đỏ oan
    khi bản mã đang đúng.
    """
    TJ.SO_COQUAN = TMP / "bang-doi-chieu-coquan.json"
    TJ.SO_LOAI = TMP / "trung-jaylam.json"
    for f in (TJ.SO_COQUAN, TJ.SO_LOAI):
        f.unlink(missing_ok=True)
    idx = TMP / "index-gia.html"
    idx.write_text("<html><script>var DATA = "
                   + json.dumps(index_data or {}, ensure_ascii=False)
                   + ";</script></html>", encoding="utf-8")
    TJ.INDEX = idx


def chay(f, *a, **kw):
    """Chạy một hàm, trả (mã, stdout+stderr)."""
    so, se = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(so), contextlib.redirect_stderr(se):
        try:
            ma = f(*a, **kw)
        except SystemExit as e:                                  # noqa: PERF203
            ma = e.code
    return ma, so.getvalue() + se.getvalue()


def doc(p):
    try:
        return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


IDX_MAU = {
    "usNews": [
        {"sourceUrl": "https://a.com/tin-1", "title": "Tin một của mình"},
        {"sourceUrl": "https://b.com/tin-2", "title": "Tin hai của mình"},
    ],
    "worldNews": [{"sourceUrl": "https://c.com/tin-3", "title": "Tin ba của mình"}],
    "exercises": [{"name": "Predator", "items": [
        {"sourceUrl": "https://d.com/tin-4", "title": "Tin bốn trong tập trận"}]}],
}


# ==========================================================================
# NHÓM A — bóc link và chữ từ .docx
# ==========================================================================
f_co_ban = docx_gia("co-ban.docx", [
    ("Ngày 01.9.2026, tin thứ nhất về một chuyện gì đó. ", "https://a.com/tin-1"),
    ("Ngày 31.8.2026, tin thứ hai cũng đáng chú ý. ", "https://b.com/tin-2"),
    ("Ngày 30.8.2026, tin dán link trần https://z.com/tin-tran và hết.", None),
])
_ten, _tin = TJ.boc_docx(f_co_ban)
kiem("[01] bóc đủ 03 link (02 hyperlink + 01 link dán trần)", len(_tin) == 3)
kiem("[02] tiêu đề = chữ của đoạn, đã bỏ phần link dính đuôi",
     _tin[0]["tieu_de"] == "Ngày 01.9.2026, tin thứ nhất về một chuyện gì đó."
     and "http" not in _tin[0]["tieu_de"])
kiem("[03] link dán TRẦN trong chữ (không có quan hệ rels) vẫn được bóc",
     any(t["url"] == "https://z.com/tin-tran" for t in _tin))

f_ngoac = docx_gia("ngoac.docx", [
    ("Ngày 01.9.2026, bầu cử sơ bộ tại Massachusetts theo Ballotpedia. "
     "https://ballotpedia.org/Senate_(September_1_primary) rồi hết.", None),
    ("Ngày 01.9.2026, một tin khác kết bằng dấu chấm. https://k.com/bai-2.", None),
    ("Ngày 01.9.2026, tin trong ngoặc (xem https://k.com/bai-3) rồi hết.", None),
])
_u = {t["url"] for t in TJ.boc_docx(f_ngoac)[1]}
kiem("[04] KHÔNG cắt `)` khi ngoặc trong đường dẫn cân bằng (ca lỗi thật 01/09)",
     "https://ballotpedia.org/Senate_(September_1_primary)" in _u)
kiem("[05] cắt dấu chấm cuối câu dính đuôi link", "https://k.com/bai-2" in _u)
kiem("[06] cắt `)` khi ngoặc MẤT cân bằng (ngoặc của câu văn)", "https://k.com/bai-3" in _u)

f_tron = docx_gia("tron-chu.docx", [("", "https://a.com/chi-co-link")])
_t2 = TJ.boc_docx(f_tron)[1]
kiem("[07] đoạn chỉ có link, không chữ -> GIỮ tin kèm nhãn cảnh báo (không bỏ)",
     len(_t2) == 1 and len(_t2[0]["tieu_de"]) >= TJ.TIEU_DE_MIN
     and "⚠" in _t2[0]["tieu_de"])

f_lap = docx_gia("lap.docx", [
    ("Ngày 01.9.2026, một tin duy nhất nhắc lại nhiều dạng link. ", "https://a.com/tin-1"),
    ("Ngày 01.9.2026, cũng tin đó, dạng khác. ", "http://www.a.com/tin-1/?utm_source=tele"),
])
kiem("[08] cùng một bài viết dưới 02 dạng link -> gộp còn 01 tin",
     len(TJ.boc_docx(f_lap)[1]) == 1)


# ==========================================================================
# NHÓM B — ca PHẢI CHẶN
# ==========================================================================
ghim(IDX_MAU)

_ma, _ra = chay(TJ.nap_file, str(TMP / "khong-ton-tai.docx"), now=NOW)
kiem("[09] PHẢI CHẶN: file không tồn tại", _ma == 1 and "CHẶN" in _ra)

_ma, _ra = chay(TJ.nap_file, str(docx_gia("khong-zip.docx", [], khong_zip=True)), now=NOW)
kiem("[10] PHẢI CHẶN: file không mở được như zip (.doc cũ, hoặc hỏng)",
     _ma == 1 and "CHẶN" in _ra)

_ma, _ra = chay(TJ.nap_file, str(docx_gia("thieu-doc.docx", [], thieu_document=True)),
                now=NOW)
kiem("[11] PHẢI CHẶN: zip thiếu word/document.xml", _ma == 1 and "CHẶN" in _ra)

f_rong = docx_gia("khong-link.docx", [("Ngày 01.9.2026, một đoạn chữ không có link nào.",
                                       None)])
_ma, _ra = chay(TJ.nap_file, str(f_rong), now=NOW)
kiem("[12] PHẢI CHẶN: bóc ra 0 đường dẫn (bộ lọc rỗng thì im lặng không chặn gì)",
     _ma == 1 and "CHẶN" in _ra)

_ma, _ra = chay(TJ.nap_file, str(f_co_ban), nhan="x", now=NOW)
kiem("[13] PHẢI CHẶN: `--nhan` ngắn hơn NHAN_MIN", _ma == 1 and "CHẶN" in _ra)
_ma, _ra = chay(TJ.nap_file, str(f_co_ban), nhan="d" * (TJ.NHAN_MAX + 1), now=NOW)
kiem("[14] PHẢI CHẶN: `--nhan` dài hơn NHAN_MAX", _ma == 1 and "CHẶN" in _ra)


# ==========================================================================
# NHÓM C — chuẩn hoá URL: đúng vừa đủ, KHÔNG nới tay
# ==========================================================================
kiem("[15] chuan_url bỏ scheme, `www.`, `/` cuối, và tham số theo dõi",
     TJ.chuan_url("https://a.com/tin-1")
     == TJ.chuan_url("http://www.A.com/tin-1/?utm_source=x&fbclid=y"))
kiem("[16] chuan_url phân biệt hai bài khác đường dẫn",
     TJ.chuan_url("https://a.com/tin-1") != TJ.chuan_url("https://a.com/tin-2"))
kiem("[17] chuan_url GIỮ chuỗi truy vấn mang nghĩa (cắt sạch là xoá oan tin)",
     TJ.chuan_url("https://a.com/bai?id=1") != TJ.chuan_url("https://a.com/bai?id=2")
     and TJ.chuan_url("https://a.com/bai?id=1") != TJ.chuan_url("https://a.com/bai"))
kiem("[18] chuan_url bỏ mảnh `#` và không phân biệt thứ tự tham số",
     TJ.chuan_url("https://a.com/b?x=1&y=2#doan")
     == TJ.chuan_url("https://a.com/b?y=2&x=1"))


# ==========================================================================
# NHÓM D — nạp thật: ghi sổ, lọc trùng, `--thu`
# ==========================================================================
ghim(IDX_MAU)
_ma, _ra = chay(TJ.nap_file, str(f_co_ban), now=NOW)
_so_cq, _so_loai = doc(TJ.SO_COQUAN), doc(TJ.SO_LOAI)
kiem("[19] nạp xong: mã 0, sổ đối chiếu cục bộ có đúng 01 file và 03 tin",
     _ma == 0 and isinstance(_so_cq, list) and len(_so_cq) == 1
     and len(_so_cq[0]["tin"]) == 3)
kiem("[20] nhãn mặc định = tên file bỏ đuôi", _so_cq[0]["nhan"] == "co-ban")
kiem("[21] tin của mình trùng đường dẫn -> vào sổ loại (02 tin: a.com, b.com)",
     isinstance(_so_loai, list) and len(_so_loai) == 2)
kiem("[22] sổ loại giữ url NGUYÊN VĂN của tin mình (make_docx so nguyên văn)",
     {r["url"] for r in _so_loai} == {"https://a.com/tin-1", "https://b.com/tin-2"})
kiem("[23] tin của mình KHÔNG có trong file cơ quan thì không bị loại",
     all("c.com" not in r["url"] and "d.com" not in r["url"] for r in _so_loai))
kiem("[24] mỗi dòng sổ loại mang `trung_voi` + `id_jay` là nhãn -> soi ngược được",
     all(len(r.get("trung_voi") or "") >= TJ.TRUNG_VOI_MIN and r.get("id_jay") == "co-ban"
         for r in _so_loai))

# `--thu` không được chạm sổ nào
ghim(IDX_MAU)
_ma, _ra = chay(TJ.nap_file, str(f_co_ban), thu=True, now=NOW)
kiem("[25] `--thu`: in ra nhưng KHÔNG ghi sổ nào",
     _ma == 0 and doc(TJ.SO_COQUAN) is None and doc(TJ.SO_LOAI) is None)

# nạp lại cùng nhãn -> thay thế, không nhân đôi; sổ loại cũ của dòng khác được giữ
ghim(IDX_MAU)
TJ.SO_LOAI.write_text(json.dumps([{"url": "https://cu.com/tin-cu", "tieu_de": "Tin cũ đã loại",
                                   "trung_voi": "mảnh bên file cũ", "id_jay": 7,
                                   "ngay": NOW.date().isoformat()}], ensure_ascii=False),
                      encoding="utf-8")
chay(TJ.nap_file, str(f_co_ban), now=NOW)
chay(TJ.nap_file, str(f_co_ban), now=NOW)
kiem("[26] nạp lại cùng nhãn -> thay thế trong sổ, không nhân đôi",
     len(doc(TJ.SO_COQUAN)) == 1)
kiem("[27] dòng sổ loại có sẵn từ đường khác được GIỮ, không bị ghi đè mất",
     any(r["url"] == "https://cu.com/tin-cu" for r in doc(TJ.SO_LOAI)))

# cắt theo GIU_NGAY
ghim(IDX_MAU)
chay(TJ.nap_file, str(f_co_ban), nhan="ban-cu", now=NOW)
_sau = NOW + datetime.timedelta(days=TJ.GIU_NGAY + 1)
chay(TJ.nap_file, str(f_co_ban), nhan="ban-moi", now=_sau)
kiem(f"[28] mục quá {TJ.GIU_NGAY} ngày bị cắt khỏi sổ đối chiếu cục bộ",
     [r["nhan"] for r in doc(TJ.SO_COQUAN)] == ["ban-moi"])


# ==========================================================================
# NHÓM E — `id_jay` dạng NHÃN trong `--ghi-loai`
# ==========================================================================
ghim(IDX_MAU)
chay(TJ.nap_file, str(f_co_ban), nhan="ĐTN_M_01.9.2026", now=NOW)


def _loai(id_jay):
    f = TMP / "loai.json"
    f.write_text(json.dumps([{"url": "https://c.com/tin-3",
                              "tieu_de": "Tin ba của mình, tiêu đề đủ dài để qua cổng",
                              "trung_voi": "mảnh tương ứng bên file cơ quan gửi",
                              "id_jay": id_jay}], ensure_ascii=False), encoding="utf-8")
    return chay(TJ.ghi_loai, str(f), now=NOW)


TJ._headers = lambda: None          # chặn mọi lời gọi mạng của `doc_hang_cho`
_ma, _ra = _loai("ĐTN_M_01.9.2026")
kiem("[29] `id_jay` là NHÃN có thật trong sổ cục bộ -> cho qua",
     _ma == 0 and any(r["url"] == "https://c.com/tin-3" for r in doc(TJ.SO_LOAI)))
_ma, _ra = _loai("NHAN_BIA_KHONG_CO")
kiem("[30] PHẢI CHẶN: `id_jay` là nhãn BỊA (không có trong sổ) -> không soi ngược được",
     _ma == 1 and "CHẶN" in _ra)
_ma, _ra = _loai("")
kiem("[31] PHẢI CHẶN: `id_jay` rỗng", _ma == 1 and "CHẶN" in _ra)


# ==========================================================================
# NHÓM F — `--liet-ke` và phân tích cờ
# ==========================================================================
ghim(IDX_MAU)
chay(TJ.nap_file, str(f_co_ban), nhan="co-quan-01", now=NOW)
TJ.doc_hang_cho = lambda now=None: ([], [])      # hàng chờ Supabase RỖNG
_ma, _ra = chay(TJ.in_hang_cho, NOW)
kiem("[32] `--liet-ke` in bảng cục bộ NGAY CẢ KHI hàng chờ Supabase rỗng",
     _ma == 0 and "co-quan-01" in _ra and "https://a.com/tin-1" in _ra)
kiem("[33] `--liet-ke` nói rõ việc còn lại là đối chiếu theo SỰ KIỆN", "SỰ KIỆN" in _ra)

kiem("[34] cờ `--nap-file` nhận cả dạng `--nap-file=X`",
     TJ._gia_tri(["--nap-file=/a/b.docx"], "--nap-file") == "/a/b.docx"
     and TJ._gia_tri(["--nap-file", "/a/b.docx"], "--nap-file") == "/a/b.docx"
     and TJ._gia_tri(["--liet-ke"], "--nap-file") is None)
_ma, _ra = chay(TJ.main, ["--nap-file"])
kiem("[35] PHẢI CHẶN: `--nap-file` không kèm đường dẫn", _ma == 1)


# ==========================================================================
BAN_HONG = [
    ("bỏ chặn `bóc ra 0 link` -> bộ lọc rỗng, im lặng không chặn gì",
     '    if not tin:\n'
     '        # Cùng lẽ với `kiem_mot_bang`: file tin mà bóc ra 0 link nghĩa là bước bóc đã '
     'hỏng,\n'
     '        # và một bộ lọc rỗng thì im lặng không chặn gì cả.\n'
     '        raise ValueError(f"{p.name}: bóc ra 0 đường dẫn',
     '    if False:\n        raise ValueError(f"{p.name}: bóc ra 0 đường dẫn'),
    ("cắt `)` vô điều kiện -> link có ngoặc hợp lệ thành link ma",
     '        elif u[-1] == ")" and u.count(")") > u.count("("):',
     '        elif u[-1] == ")":'),
    ("bỏ nhánh link dán TRẦN -> mất câm những đoạn người soạn dán vội",
     '        urls += [_cat_dau_duoi(u) for u in _RE_URL_TRAN.findall(chu)]',
     '        urls += []'),
    ("đoạn chỉ có link thì BỎ tin -> để lọt đúng tin phải cắt",
     '        if len(tieu_de) < TIEU_DE_MIN:',
     '        if False:'),
    ("bỏ kiểm độ dài `--nhan` -> nhãn vô nghĩa, sổ loại không soi ngược được",
     '    if not NHAN_MIN <= len(nhan) <= NHAN_MAX:',
     '    if False:'),
    ("`id_jay` dạng nhãn cho qua không đối chiếu sổ -> trỏ vào hư không",
     '        if nhan not in co:',
     '        if False:'),
    ("chuan_url cắt sạch chuỗi truy vấn -> gộp nhầm hai bài, XOÁ OAN một tin",
     '    q = [(k, v) for k, v in urllib.parse.parse_qsl(p.query, keep_blank_values=True)\n'
     '         if k.lower() not in THAM_SO_BO]',
     '    q = []'),
    ("ghi bản CHUẨN HOÁ vào sổ loại thay vì url nguyên văn -> make_docx không khớp nổi",
     '            trung.append({"url": it["url"],',
     '            trung.append({"url": chuan_url(it["url"]),'),
    ("`--thu` vẫn ghi sổ -> xem trước mà đã đổi dữ liệu",
     '    if thu:\n'
     '        print("— `--thu`: chỉ xem trước, KHÔNG ghi sổ nào.")\n'
     '        return 0',
     '    if False:\n        return 0'),
    ("bỏ cắt theo GIU_NGAY -> file cơ quan làm bộ lọc vô thời hạn",
     '    giu = [r for r in theo_nhan.values() if (r.get("ngay") or "") >= han]',
     '    giu = list(theo_nhan.values())'),
    ("`--liet-ke` thoát sớm khi hàng chờ rỗng -> bảng cục bộ không bao giờ hiện",
     '        return 0 if co_quan else 10',
     '        return 10'),
]

KHAI_DO = {
    "bỏ chặn `bóc ra 0 link` -> bộ lọc rỗng, im lặng không chặn gì": ["12"],
    "cắt `)` vô điều kiện -> link có ngoặc hợp lệ thành link ma": ["04"],
    "bỏ nhánh link dán TRẦN -> mất câm những đoạn người soạn dán vội": ["01", "03"],
    "đoạn chỉ có link thì BỎ tin -> để lọt đúng tin phải cắt": ["07"],
    "bỏ kiểm độ dài `--nhan` -> nhãn vô nghĩa, sổ loại không soi ngược được": ["13", "14"],
    "`id_jay` dạng nhãn cho qua không đối chiếu sổ -> trỏ vào hư không": ["30"],
    "chuan_url cắt sạch chuỗi truy vấn -> gộp nhầm hai bài, XOÁ OAN một tin": ["17"],
    "ghi bản CHUẨN HOÁ vào sổ loại thay vì url nguyên văn -> make_docx không khớp nổi":
        ["22"],
    "`--thu` vẫn ghi sổ -> xem trước mà đã đổi dữ liệu": ["25"],
    "bỏ cắt theo GIU_NGAY -> file cơ quan làm bộ lọc vô thời hạn": ["28"],
    "`--liet-ke` thoát sớm khi hàng chờ rỗng -> bảng cục bộ không bao giờ hiện": ["32", "33"],
}


def _so_ca(ten):
    return ten[1:3] if ten.startswith("[") else ""


def tu_kiem():
    """Dựng từng bản `tin_jaylam.py` đã GỠ một lớp bảo vệ rồi chạy lại chính bộ ca này."""
    goc = (SC / "tin_jaylam.py").read_text(encoding="utf-8")
    tong, trot = 0, []
    for ten, tim, thay in BAN_HONG:
        tong += 1
        if goc.count(tim) != 1:
            trot.append(f"{ten}: chuỗi neo khớp {goc.count(tim)} chỗ (phải đúng 1)")
            continue
        hong = goc.replace(tim, thay)
        sha = hashlib.sha1(hong.encode("utf-8")).hexdigest()[:8]
        d = pathlib.Path(tempfile.mkdtemp(prefix=f"tj-hong-{os.getpid()}-{sha}-"))
        try:
            for f in SC.glob("*.py"):
                shutil.copy2(f, d / f.name)
            (d / "tin_jaylam.py").write_text(hong, encoding="utf-8")
            env = dict(os.environ, TINJAYLAM_DIR=str(d))
            p = SP.run([sys.executable, str(pathlib.Path(__file__).resolve())],
                       capture_output=True, text=True, env=env, timeout=300)
            do = {_so_ca(l[2:]) for l in p.stdout.splitlines() if l.startswith("✗ ")}
            can = set(KHAI_DO.get(ten, []))
            if p.returncode == 0:
                trot.append(f"{ten}: bộ test VẪN XANH -> không bắt được lỗi")
            elif len(do) >= len([l for l in p.stdout.splitlines()
                                 if l[:1] in ("✓", "✗")]):
                trot.append(f"{ten}: ĐỎ TOÀN BỘ ca -> phép thay phá cú pháp, không gỡ lớp vá")
            elif not can & do:
                trot.append(f"{ten}: ca cần đỏ {sorted(can)} vẫn xanh; đỏ thực tế "
                            f"{sorted(do)}")
            else:
                print(f"  ✓ {ten}: bắt được (ca đỏ {sorted(do)})")
        finally:
            shutil.rmtree(d, ignore_errors=True)
    print()
    if trot:
        print(f"TRƯỢT {len(trot)}/{tong} bản hỏng:")
        for t in trot:
            print("  - " + t)
        return 1
    print(f"✅ {tong}/{tong} bản hỏng đều bị bộ test bắt.")
    return 0


shutil.rmtree(TMP, ignore_errors=True)
so_dat = sum(1 for _, ok in CA if ok)
print(f"\n{so_dat}/{len(CA)} ca đạt")
if "--tu-kiem" in sys.argv:
    if so_dat != len(CA):
        print("Bản THẬT đã đỏ — sửa xong hãy chạy --tu-kiem.")
        sys.exit(1)
    print("\n=== TỰ KIỂM: dựng bản tin_jaylam.py đã gỡ lớp bảo vệ ===")
    sys.exit(tu_kiem())
sys.exit(0 if so_dat == len(CA) else 1)
