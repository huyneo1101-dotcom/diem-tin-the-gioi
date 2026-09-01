#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test FORM FILE WORD THEO MẪU CỦA CƠ QUAN (Huy chốt 01/09/2026).

    python3 tests/test-form-docx-mau.py
    python3 tests/test-form-docx-mau.py --tu-kiem   # chứng minh test BẮT ĐƯỢC lỗi

Chỉ thị nguyên văn: *"từ bây giờ các kết quả quét tin xuất file docx phải theo form như file
tao đính kèm."* — file mẫu `ĐTN_M_01.9.2026.docx`, do cơ quan soạn.

Vì sao phải có bộ này: form là thứ HỎNG CÂM tuyệt đối. Sai thụt dòng, sai giãn dòng, thêm
lại dòng tiêu đề, tách link xuống dòng riêng — không lệnh nào lỗi, file .docx vẫn ra đời đủ
tin, Telegram vẫn gửi, CI vẫn xanh; chỉ người nhận mở ra mới thấy khác bản của cơ quan, mà
lúc đó bản tin đã đi rồi. Mọi con số dưới đây đo bằng cách bóc `word/document.xml` của chính
file mẫu, không lấy theo trí nhớ.

07 điểm bộ này canh:
  (1) KHÔNG có dòng tiêu đề "ĐIỂM TIN NGÀY …" — mẫu vào thẳng mục (1).
  (2) Đầu mục dạng "(N) Tên mục", KHÔNG phải "N. Tên mục".
  (3) Mỗi tin mở bằng "Ngày d.M.yyyy," — ngày CÓ số 0 dẫn, tháng KHÔNG.
  (4) Link nằm CÙNG đoạn với nội dung, không xuống dòng riêng.
  (5) Khuôn đoạn: thụt dòng đầu 720 twips · giãn dòng `line=360 lineRule=exact` · cách đoạn 120.
  (6) Khổ A4 + lề 1440 twips cả bốn phía.
  (7) Mục địa bàn chia 03 tiểu mục đậm: Anh · Australia · Biển Đông.
Cộng 02 điểm về PHÂN MỤC mà form mới sinh ra:
  (8) Bảng neo đối ngoại không được chứa tên nước một âm tiết để trần ("duc" khớp "tình dục").
  (9) Chữ đầu tóm tắt chỉ hạ khi là từ chức năng, KHÔNG hạ chức danh ("Đại tướng" giữ hoa).

Yêu cầu `pip3 install python-docx`.
"""
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess as SP
import sys
import tempfile
import zipfile
import datetime
import zoneinfo

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
GS = pathlib.Path(os.environ.get("MAKEDOCX_DIR") or (REPO / ".github" / "scripts"))
sys.path.insert(0, str(GS))

import make_docx as MD          # noqa: E402

VN = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")
MD.prev_data = lambda: None
MD._url_ca_sang = lambda now: set()
MD.loc_chua_gui = lambda items: items
MD.gop_tin_ca_toi = lambda items, cur, kind, now: items

TOI = datetime.datetime(2026, 9, 1, 21, 0, tzinfo=VN)
HOM_NAY = "2026-09-01"

# Lô giả phủ ĐỦ 04 mục + 03 tiểu mục. Tóm tắt cố ý chọn đúng các thế khó:
#   - "Đại tướng…" bắt đầu bằng chức danh -> PHẢI giữ hoa sau "Ngày …,"
#   - "tại Hội nghị…" bắt đầu bằng trạng ngữ -> PHẢI hạ chữ đầu
#   - "Hạ viện … tội phạm tình dục" -> tin NỘI BỘ thuần, không được rơi sang "Đối ngoại Mỹ"
DATA_GIA = {
    "generatedAt": HOM_NAY,
    "usNews": [
        {"date": HOM_NAY, "_addedDate": HOM_NAY, "category": "Kinh tế",
         "title": "Mỹ trừng phạt thêm ngân hàng liên quan Iran",
         "summary": "tại Hội nghị Bộ trưởng Tài chính G20, Mỹ tuyên bố trừng phạt thêm một "
                    "ngân hàng nhằm siết giao dịch của Iran.",
         "sourceUrl": "https://reuters.com/doi-ngoai-iran"},
        {"date": HOM_NAY, "_addedDate": HOM_NAY, "category": "Chính trị",
         "title": "Chủ tịch Hội đồng Tham mưu trưởng nói về bầu cử giữa nhiệm kỳ",
         "summary": "Đại tướng Dan Caine khẳng định quân đội không triển khai lực lượng liên "
                    "bang tới các điểm bỏ phiếu.",
         "sourceUrl": "https://reuters.com/noi-bo-caine"},
        {"date": HOM_NAY, "_addedDate": HOM_NAY, "category": "Chính trị",
         "title": "Hạ viện Mỹ thông qua đạo luật bảo vệ nạn nhân",
         "summary": "Hạ viện Mỹ bỏ phiếu miệng thông qua đạo luật buộc tòa án ban lệnh cấm "
                    "tiếp xúc với kẻ phạm tội tình dục hoặc trọng tội bạo lực liên bang.",
         "sourceUrl": "https://thehill.com/noi-bo-kayleigh"},
        {"date": HOM_NAY, "_addedDate": HOM_NAY, "category": "Công nghệ quân sự",
         "title": "Bộ Chiến tranh Mỹ mở rộng năng lực đánh chặn",
         "summary": "Bộ Chiến tranh Mỹ ký thỏa thuận khung 7 năm nhằm tăng công suất sản "
                    "xuất tên lửa đánh chặn PAC-3 MSE.",
         "sourceUrl": "https://war.gov/khcn-pac3"},
    ],
    "worldNews": [
        {"date": HOM_NAY, "_addedDate": HOM_NAY, "category": "Chính trị",
         "title": "Tàu tuần tra Hải quân Hoàng gia Anh thăm Ream",
         "summary": "tàu tuần tra HMS Tamar của Royal Navy lần đầu thăm Căn cứ Hải quân Ream "
                    "và huấn luyện chung trong một tuần.",
         "sourceUrl": "https://ukdefencejournal.org.uk/dia-ban-anh"},
        {"date": HOM_NAY, "_addedDate": HOM_NAY, "category": "Chính trị",
         "title": "Thủ tướng Australia dự Diễn đàn Quần đảo Thái Bình Dương",
         "summary": "Thủ tướng Australia bắt đầu chuyến công tác Palau dự Hội nghị Lãnh đạo "
                    "PIF lần thứ 55.",
         "sourceUrl": "https://pm.gov.au/dia-ban-uc"},
        {"date": HOM_NAY, "_addedDate": HOM_NAY, "category": "Chính trị",
         "title": "AUKUS: Anh và Australia ký thoả thuận đóng tàu ngầm",
         "summary": "Royal Navy và Royal Australian Navy công bố mốc mới của chương trình "
                    "tàu ngầm AUKUS tại Canberra.",
         "sourceUrl": "https://defence.gov.au/dia-ban-aukus"},
        {"date": HOM_NAY, "_addedDate": HOM_NAY, "category": "Chính trị",
         "title": "Philippines tái khẳng định phán quyết 2016",
         "summary": "Tổng thống Philippines tái khẳng định quyền hàng hải theo Phán quyết "
                    "Trọng tài năm 2016 tại Biển Đông.",
         "sourceUrl": "https://inquirer.net/dia-ban-bien-dong"},
    ],
    "exercises": [],
}

CA = []


def kiem(ten, dat, chi_tiet=""):
    CA.append((ten, bool(dat)))
    print(("✓" if dat else "✗") + " " + ten + (("\n      │ " + str(chi_tiet)) if not dat else ""))


class ThuMucGia:
    def __enter__(self):
        self.cu = os.getcwd()
        self.d = pathlib.Path(tempfile.mkdtemp(prefix="form-docx-"))
        (self.d / "index.html").write_text(
            "<html><script>var DATA = " + json.dumps(DATA_GIA, ensure_ascii=False)
            + ";</script></html>", encoding="utf-8")
        os.chdir(self.d)
        return self.d

    def __exit__(self, *a):
        os.chdir(self.cu)
        shutil.rmtree(self.d, ignore_errors=True)
        return False


def dung():
    """Chạy MD.main() rồi trả (list đoạn, xml document, xml styles).

    Mỗi đoạn là dict: text · dam · co_link · spacing · ind.
    """
    import contextlib
    import io as _io
    with ThuMucGia():
        buf = _io.StringIO()
        with contextlib.redirect_stdout(buf):
            MD.main(now=TOI)
        dong = [l for l in buf.getvalue().splitlines() if l.startswith("DOCX=")]
        assert dong, "make_docx không in dòng DOCX= — bước dựng đã hỏng"
        path = dong[-1][len("DOCX="):]
        assert path and os.path.exists(path), f"không thấy file .docx: {path!r}"
        z = zipfile.ZipFile(path)
        doc = z.read("word/document.xml").decode("utf-8")
        sty = z.read("word/styles.xml").decode("utf-8")
        z.close()
        os.unlink(path)

    doan = []
    for pa in re.findall(r"<w:p\b.*?</w:p>|<w:p\b[^>]*/>", doc, re.S):
        txt = "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", pa, re.S))
        txt = txt.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        spc = re.search(r"<w:spacing ([^/>]*)/>", pa)
        ind = re.search(r"<w:ind ([^/>]*)/>", pa)
        doan.append({
            "text": txt,
            "dam": "<w:b/>" in pa or '<w:b w:val="1"' in pa,
            "link": "<w:hyperlink" in pa,
            "spacing": spc.group(1) if spc else "",
            "ind": ind.group(1) if ind else "",
        })
    return doan, doc, sty


DOAN, XML, STYLES = dung()
CHU = [d["text"] for d in DOAN]
DAU_MUC = [d for d in DOAN if d["dam"] and d["text"].startswith("(")]
TIN = [d for d in DOAN if d["link"]]


# ══════════════════════ (1) không có dòng tiêu đề ══════════════════════
kiem("[01] PHẢI CHẶN: KHÔNG có dòng tiêu đề 'ĐIỂM TIN NGÀY …' — mẫu vào thẳng mục (1)",
     not any("ĐIỂM TIN" in t.upper() for t in CHU), CHU[:3])

kiem("[02] PHẢI CHẶN: đoạn ĐẦU TIÊN của file là đầu mục '(1) …'",
     CHU and CHU[0].startswith("(1) "), CHU[:2] if CHU else "file rỗng")


# ══════════════════════ (2) đầu mục '(N) Tên' ══════════════════════
kiem("[03] PHẢI CHẶN: đầu mục đánh số kiểu '(N) ', KHÔNG phải 'N. '",
     len(DAU_MUC) >= 3
     and all(re.match(r"^\(\d+\) \S", d["text"]) for d in DAU_MUC)
     and not any(re.match(r"^\d+\.\s", t) for t in CHU),
     [d["text"] for d in DAU_MUC])

kiem("[04] PHẢI CHẶN: đủ 04 tên mục theo mẫu, đúng thứ tự",
     [re.sub(r"^\(\d+\) ", "", d["text"]) for d in DAU_MUC]
     == [MD.MUC_DOI_NGOAI, MD.MUC_NOI_BO, MD.MUC_DIA_BAN, MD.MUC_KHCN],
     [d["text"] for d in DAU_MUC])


# ══════════════════════ (3) tiền tố ngày ══════════════════════
kiem("[05] PHẢI CHẶN: MỌI tin mở bằng 'Ngày d.M.yyyy,'",
     TIN and all(re.match(r"^Ngày \d{2}\.\d{1,2}\.\d{4}, ", d["text"]) for d in TIN),
     [d["text"][:40] for d in TIN])

kiem("[06] PHẢI CHẶN: khuôn ngày là '01.9.2026' — ngày CÓ số 0 dẫn, tháng KHÔNG",
     MD.ngay_form("2026-09-01") == "01.9.2026"
     and MD.ngay_form("2026-08-31") == "31.8.2026"
     and MD.ngay_form("2026-12-05") == "05.12.2026",
     [MD.ngay_form("2026-09-01"), MD.ngay_form("2026-08-31"), MD.ngay_form("2026-12-05")])

kiem("[07] PHẢI CHẶN: tin KHÔNG mở bằng gạch đầu dòng '- '",
     not any(t.lstrip().startswith(("- ", "– ", "• ")) for t in CHU),
     [t[:30] for t in CHU if t.lstrip().startswith(("- ", "– ", "• "))])

kiem("[08] PHẢI CHẶN: tầng quét tự viết 'Ngày 31/8/2026,' trong summary thì phải CẮT, "
     "không in hai lần",
     MD.than_tin({"date": "2026-08-31", "summary": "Ngày 31/8/2026, Hạ viện Mỹ họp."})
     == "Ngày 31.8.2026, Hạ viện Mỹ họp.",
     MD.than_tin({"date": "2026-08-31", "summary": "Ngày 31/8/2026, Hạ viện Mỹ họp."}))


# ══════════════════════ (4) link cùng đoạn ══════════════════════
kiem("[09] PHẢI CHẶN: link nằm CÙNG đoạn với nội dung, không có đoạn chỉ-chứa-link",
     TIN and all(len(d["text"].strip()) > 60 for d in TIN)
     and not any(d["link"] and d["text"].strip().startswith("http") for d in DOAN),
     [d["text"][:50] for d in TIN if len(d["text"].strip()) <= 60])

kiem("[10] đối chứng: số đoạn mang link ĐÚNG BẰNG số tin (8 tin lô giả)",
     len(TIN) == 8, f"{len(TIN)} đoạn có link")


# ══════════════════════ (5) khuôn đoạn ══════════════════════
kiem("[11] PHẢI CHẶN: mỗi đoạn tin thụt dòng đầu 720 twips",
     TIN and all('w:firstLine="720"' in d["ind"] for d in TIN),
     [d["ind"] for d in TIN[:3]])

kiem("[12] PHẢI CHẶN: giãn dòng CHÍNH XÁC — line=360 lineRule=exact (mẫu dùng exact)",
     TIN and all('w:line="360"' in d["spacing"] and 'w:lineRule="exact"' in d["spacing"]
                 for d in TIN),
     [d["spacing"] for d in TIN[:3]])

kiem("[13] PHẢI CHẶN: cách đoạn 120 twips (6pt)",
     TIN and all('w:after="120"' in d["spacing"] for d in TIN),
     [d["spacing"] for d in TIN[:3]])

kiem("[14] PHẢI CHẶN: chữ Times New Roman 14pt khai ở style Normal (sz 28 half-point)",
     re.search(r'w:styleId="Normal".*?Times New Roman.*?<w:sz w:val="28"/>', STYLES, re.S)
     is not None,
     re.search(r'<w:style [^>]*w:styleId="Normal".*?</w:style>', STYLES, re.S).group(0)[:200]
     if re.search(r'<w:style [^>]*w:styleId="Normal".*?</w:style>', STYLES, re.S) else "-")


# ══════════════════════ (6) khổ giấy + lề ══════════════════════
kiem("[15] PHẢI CHẶN: khổ A4 (pgSz ~11907x16839) + lề 1440 twips cả bốn phía",
     re.search(r'<w:pgSz w:w="119\d\d" w:h="168\d\d"', XML) is not None
     and re.search(r'<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"', XML)
     is not None,
     re.search(r"<w:sectPr.*?</w:sectPr>", XML, re.S).group(0)[:220])


# ══════════════════════ (7) tiểu mục của mục địa bàn ══════════════════════
def _sau_dau_muc(ten_muc):
    """Các đoạn nằm giữa đầu mục `ten_muc` và đầu mục kế tiếp."""
    i = next((k for k, d in enumerate(DOAN)
              if d["dam"] and d["text"].endswith(ten_muc)), None)
    if i is None:
        return []
    j = next((k for k in range(i + 1, len(DOAN))
              if DOAN[k]["dam"] and DOAN[k]["text"].startswith("(")), len(DOAN))
    return DOAN[i + 1:j]


KHOI_DIA_BAN = _sau_dau_muc(MD.MUC_DIA_BAN)
NHAN_TIEU_MUC = [d["text"] for d in KHOI_DIA_BAN if d["dam"] and d["text"].strip()]

def _la_day_con(nho, lon):
    it = iter(lon)
    return all(x in it for x in nho)


# ⚠️ TỪ 01/09/2026 BẮT ĐỦ 03 NHÃN, không còn đo dãy con. Trước khi Huy chốt mở phạm vi
# quét sang Anh (cùng ngày, muộn hơn vài giờ) thì tiểu mục "Anh" LUÔN RỖNG và ca này chỉ
# đo được dãy con; nay `topics.NEO_ANH` đã nối vào `NEO_UC_BIEN_DONG` nên tin Anh qua được
# cổng nạp, và một tiểu mục Anh rỗng lại có nghĩa là ĐƯỜNG QUÉT ANH ĐÃ ĐỨT — phải đỏ.
kiem("[16] PHẢI CHẶN: mục địa bàn chia ĐỦ 03 tiểu mục ĐẬM, đúng thứ tự Anh · Australia · Biển Đông",
     NHAN_TIEU_MUC == list(MD.THU_TU_TIEU_MUC), NHAN_TIEU_MUC)

kiem("[17] PHẢI CHẶN: tin xếp ĐÚNG tiểu mục — HMS Tamar về 'Anh', không rơi xuống 'Biển Đông'",
     MD.tieu_muc_dia_ban(DATA_GIA["worldNews"][0]) == MD.TM_ANH
     and MD.tieu_muc_dia_ban(DATA_GIA["worldNews"][1]) == MD.TM_UC
     and MD.tieu_muc_dia_ban(DATA_GIA["worldNews"][3]) == MD.TM_BIEN_DONG,
     [MD.tieu_muc_dia_ban(t) for t in DATA_GIA["worldNews"]])

# Ca DUY NHẤT bắt được thứ tự giành Úc-trước-Anh: tin chỉ dính MỘT nước thì đảo thứ tự
# cũng ra cùng kết quả, nên ba tin của ca 17 không đủ để lộ lỗi.
kiem("[28] PHẢI CHẶN: tin dính CẢ Anh lẫn Úc (AUKUS) về 'Australia', không về 'Anh'",
     MD.tieu_muc_dia_ban(DATA_GIA["worldNews"][2]) == MD.TM_UC,
     MD.tieu_muc_dia_ban(DATA_GIA["worldNews"][2]))

kiem("[18] PHẢI CHẶN: tiểu mục RỖNG thì KHÔNG in nhãn trống",
     all(not (d["dam"] and d["text"].strip() and
              KHOI_DIA_BAN[k + 1:k + 2] and KHOI_DIA_BAN[k + 1]["dam"])
         for k, d in enumerate(KHOI_DIA_BAN)),
     [d["text"] for d in KHOI_DIA_BAN if d["dam"]])


# ══════════════════════ (8) bảng neo đối ngoại ══════════════════════
kiem("[19] PHẢI CHẶN: 'tội phạm tình dục' KHÔNG được kéo tin nội bộ sang mục Đối ngoại "
     "(neo 'duc' để trần — cùng lớp lỗi 'Malice/Mali' vá 26/08/2026)",
     not MD.la_doi_ngoai_my(DATA_GIA["usNews"][2]),
     [k for k, p in zip(MD.NEO_DOI_NGOAI, MD._RE_DOI_NGOAI)
      if p.search(MD._khong_dau(MD._kho_chu(DATA_GIA["usNews"][2])))])

kiem("[20] PHẢI CHẶN: 'biện pháp'/'tư pháp'/'ngã' không được khớp neo nước "
     "(Pháp/Nga để trần)",
     not MD.la_doi_ngoai_my({"category": "Chính trị", "title": "Toà án Mỹ",
                             "summary": "Thẩm phán áp dụng biện pháp tư pháp sau khi bị "
                                        "cáo ngã tại phiên xử."}),
     "neo nước một âm tiết vẫn để trần")

kiem("[21] đối chứng chống chặn oan: tin Mỹ trừng phạt Iran VẪN vào mục Đối ngoại",
     MD.la_doi_ngoai_my(DATA_GIA["usNews"][0]), "tin Iran rơi khỏi mục Đối ngoại")

kiem("[22] đối chứng: tin nội bộ thuần (tướng Caine nói về bầu cử) ở lại mục Nội bộ Mỹ",
     not MD.la_doi_ngoai_my(DATA_GIA["usNews"][1]),
     [k for k, p in zip(MD.NEO_DOI_NGOAI, MD._RE_DOI_NGOAI)
      if p.search(MD._khong_dau(MD._kho_chu(DATA_GIA["usNews"][1])))])


# ══════════════════════ (9) hạ chữ đầu ══════════════════════
kiem("[23] PHẢI CHẶN: CHỨC DANH giữ hoa sau 'Ngày …,' — mẫu ghi 'Đại tướng Dan Caine'",
     MD.than_tin(DATA_GIA["usNews"][1]).startswith(f"Ngày 01.9.2026, Đại tướng"),
     MD.than_tin(DATA_GIA["usNews"][1])[:50])

kiem("[24] PHẢI CHẶN: từ chức năng HẠ chữ đầu — mẫu ghi 'Ngày …, tại Hội nghị …'",
     MD.than_tin({"date": HOM_NAY, "summary": "Tại Hội nghị G20, Mỹ nêu quan điểm."})
     == "Ngày 01.9.2026, tại Hội nghị G20, Mỹ nêu quan điểm.",
     MD.than_tin({"date": HOM_NAY, "summary": "Tại Hội nghị G20, Mỹ nêu quan điểm."}))

kiem("[25] PHẢI CHẶN: TÊN CƠ QUAN giữ hoa — mẫu ghi 'Quân đội Mỹ và Indonesia khai mạc'",
     MD.than_tin({"date": HOM_NAY, "summary": "Quân đội Mỹ và Indonesia khai mạc tập trận."})
     .startswith("Ngày 01.9.2026, Quân đội"),
     MD.than_tin({"date": HOM_NAY, "summary": "Quân đội Mỹ và Indonesia khai mạc tập trận."}))

kiem("[26] PHẢI CHẶN: không có `date` hợp lệ thì in thân tin trần, KHÔNG bịa ngày",
     MD.than_tin({"date": "", "summary": "Bộ Quốc phòng công bố."}) == "Bộ Quốc phòng công bố."
     and MD.ngay_form("thang 9/2026") == "",
     MD.than_tin({"date": "", "summary": "Bộ Quốc phòng công bố."}))

kiem("[27] PHẢI CHẶN: NEO_UC là tập con của NEO_UC_BIEN_DONG (lệch -> tin Úc rơi Biển Đông)",
     (lambda: (__import__("topics").NEO_UC,
               all(k in __import__("topics").NEO_UC_BIEN_DONG
                   for k in __import__("topics").NEO_UC))[1])(),
     "bảng NEO_UC đã tách nhánh khỏi bảng lớn")


# ══════════════════════ TỰ KIỂM ══════════════════════
BAN_HONG = [
    ("thêm lại dòng tiêu đề 'ĐIỂM TIN NGÀY'",
     "    idx = 0\n    for name, items in sections:",
     '    _pt = doc.add_paragraph()\n    set_font(_pt.add_run("ĐIỂM TIN NGÀY 1.9.2026"), '
     'size=SIZE, bold=True)\n    idx = 0\n    for name, items in sections:'),
    ("đánh số đầu mục kiểu 'N.' thay vì '(N)'",
     'add_dau_muc(doc, f"({idx}) {name}")',
     'add_dau_muc(doc, f"{idx}. {name}")'),
    ("bỏ tiền tố 'Ngày d.M.yyyy,' khỏi thân tin",
     '    return f"Ngày {d}, {_noi_sau_ngay(body)}" if (d and body) else body',
     "    return body"),
    ("khuôn ngày sai: tháng cũng có số 0 dẫn (01.09.2026)",
     'return f"{m.group(3)}.{int(m.group(2))}.{m.group(1)}" if m else ""',
     'return f"{m.group(3)}.{m.group(2)}.{m.group(1)}" if m else ""'),
    ("tách link ra đoạn riêng như bản trước 01/09/2026",
     "    url = it.get(\"sourceUrl\")\n    if url:\n        add_hyperlink(p, url, url)",
     "    url = it.get(\"sourceUrl\")\n    if url:\n        p2 = _dinh_dang_doan("
     "doc.add_paragraph())\n        add_hyperlink(p2, url, url)"),
    ("giãn dòng auto thay vì exact",
     'spc.set(qn("w:lineRule"), "exact")',
     'spc.set(qn("w:lineRule"), "auto")'),
    ("mất thụt dòng đầu 0,5 inch",
     "    pf.first_line_indent = Inches(0.5)\n    pf.space_after",
     "    pf.space_after"),
    ("lề trái/phải trở lại 1,25 inch",
     "        s.left_margin = Inches(1.0)\n        s.right_margin = Inches(1.0)",
     "        s.left_margin = Inches(1.25)\n        s.right_margin = Inches(1.25)"),
    ("mục địa bàn in phẳng, không chia tiểu mục",
     "        if name == MUC_DIA_BAN:",
     "        if False:"),
    ("neo nước một âm tiết để trần trở lại ('duc' khớp 'tình dục')",
     '    "nuoc duc", "germany", "german", "berlin", "ba lan", "poland",',
     '    "duc", "phap", "nga", "ba lan", "poland",'),
    ("hạ chữ đầu cả CHỨC DANH ('Đại tướng' -> 'đại tướng')",
     '    "truyền", "khảo", "cuộc", "hoạt", "phát", "bang", "tàu", "máy", "đoàn",',
     '    "truyền", "khảo", "cuộc", "hoạt", "phát", "bang", "tàu", "đại", "quân",'),
    ("đảo thứ tự tiểu mục: Anh giành trước Úc (tin AUKUS rơi khỏi 'Australia')",
     "    if neo_uc(kho):\n        return TM_UC\n    if neo_anh(kho):\n        return TM_ANH",
     "    if neo_anh(kho):\n        return TM_ANH\n    if neo_uc(kho):\n        return TM_UC"),
]

KHAI_DO = {
    "thêm lại dòng tiêu đề 'ĐIỂM TIN NGÀY'": [1, 2],
    "đánh số đầu mục kiểu 'N.' thay vì '(N)'": [2, 3],
    "bỏ tiền tố 'Ngày d.M.yyyy,' khỏi thân tin": [5, 8, 23, 24],
    "khuôn ngày sai: tháng cũng có số 0 dẫn (01.09.2026)": [6],
    "tách link ra đoạn riêng như bản trước 01/09/2026": [9, 10],
    "giãn dòng auto thay vì exact": [12],
    "mất thụt dòng đầu 0,5 inch": [11],
    "lề trái/phải trở lại 1,25 inch": [15],
    "mục địa bàn in phẳng, không chia tiểu mục": [16],
    "neo nước một âm tiết để trần trở lại ('duc' khớp 'tình dục')": [19, 20],
    "hạ chữ đầu cả CHỨC DANH ('Đại tướng' -> 'đại tướng')": [23],
    "đảo thứ tự tiểu mục: Anh giành trước Úc (tin AUKUS rơi khỏi 'Australia')": [28],
}


def _so_ca(dong):
    try:
        return int(dong.split("]")[0].lstrip("["))
    except Exception:                                  # noqa: BLE001
        return -1


def tu_kiem():
    """Mỗi bản hỏng chạy trong thư mục copy riêng mang PID + sha1 nội dung — xem chú thích
    cùng tên ở `tests/test-gop-tin-ca-toi.py`."""
    goc = (GS / "make_docx.py").read_text(encoding="utf-8")
    goc_topics = (REPO / "scripts" / "topics.py").read_text(encoding="utf-8")
    tong, trot = 0, []
    for ten, tim, thay in BAN_HONG:
        tong += 1
        nguon, la_topics = (goc, False)
        if goc.count(tim) != 1:
            if goc_topics.count(tim) == 1:
                nguon, la_topics = goc_topics, True
            else:
                trot.append(f"{ten}: chuỗi neo khớp {goc.count(tim)} chỗ trong make_docx "
                            f"và {goc_topics.count(tim)} chỗ trong topics (phải đúng 1)")
                continue
        hong = nguon.replace(tim, thay)
        sha = hashlib.sha1(hong.encode("utf-8")).hexdigest()[:8]
        d = pathlib.Path(tempfile.mkdtemp(prefix=f"form-hong-{os.getpid()}-{sha}-"))
        try:
            gs = d / ".github" / "scripts"
            gs.mkdir(parents=True)
            (d / "scripts").mkdir()
            for f in GS.glob("*.py"):
                shutil.copy2(f, gs / f.name)
            for f in (REPO / "scripts").glob("*.py"):
                shutil.copy2(f, d / "scripts" / f.name)
            if la_topics:
                (d / "scripts" / "topics.py").write_text(hong, encoding="utf-8")
            else:
                (gs / "make_docx.py").write_text(hong, encoding="utf-8")
            env = dict(os.environ, MAKEDOCX_DIR=str(gs))
            p = SP.run([sys.executable, str(pathlib.Path(__file__).resolve())],
                       capture_output=True, text=True, env=env, timeout=300)
            do = {_so_ca(l[2:]) for l in p.stdout.splitlines() if l.startswith("✗ ")}
            can = set(KHAI_DO.get(ten, []))
            tong_ca = len([l for l in p.stdout.splitlines() if l[:1] in ("✓", "✗")])
            if p.returncode == 0:
                trot.append(f"{ten}: bộ test VẪN XANH -> không bắt được lỗi")
            elif tong_ca and len(do) >= tong_ca:
                trot.append(f"{ten}: ĐỎ TOÀN BỘ ca -> phép thay phá cú pháp, không gỡ lớp vá")
            elif not can & do:
                trot.append(f"{ten}: ca cần đỏ {sorted(can)} vẫn xanh; đỏ thực tế {sorted(do)}")
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


so_dat = sum(1 for _, ok in CA if ok)
print(f"\n{so_dat}/{len(CA)} ca đạt")
if "--tu-kiem" in sys.argv:
    print("\n── TỰ KIỂM: dựng bản make_docx.py/topics.py đã gỡ lớp vá ──")
    sys.exit(tu_kiem())
sys.exit(0 if so_dat == len(CA) else 1)
