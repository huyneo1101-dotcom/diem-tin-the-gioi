#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tạo file .docx "ĐIỂM TIN NGÀY d.M.yyyy" chứa các tin VỪA QUÉT ĐƯỢC trong lần publish này.
Cách xác định "tin mới của lần quét": diff DATA trong index.html (HEAD) với bản trước
(git show HEAD~1:index.html) — URL nào chưa có ở bản trước là tin của lần quét này.

BÁM CHẶT format FILE MẪU buổi tối Huy gửi (Diem-tin-ngay-2026-07-23.docx — 5 chủ đề). Đó là
tên file MẪU, KHÔNG phải tên file script này xuất ra — tên xuất ra do `ten_file()` đặt:
  1. Nội bộ Mỹ        -> usNews category "Chính trị", KHÔNG phải chuyện Mali (điều trần + bỏ phiếu)
  2. Úc và Biển Đông  -> worldNews, trừ tin Mali
  3. QS-KHCN          -> usNews còn lại (CNQS Mỹ) + item tập trận/sự kiện mới (gồm Predator's Run)
                         — mục DUY NHẤT ghi kèm ngày tin, vì chỉ nó được nới khung 3 ngày
  4. Mỹ – Mali        -> tin Mali/Sahel gom từ CẢ usNews lẫn worldNews (tách riêng 27/07/2026
                         sau khi Huy bắt lỗi tin Mali lòi ra giữa mục QS-KHCN)
  5. Tin Jay Lâm gửi  -> CẢ HAI BUỔI (mở cho bản SÁNG 30/07/2026 — trước đó CHỈ bản tối).
                         Huy chốt: "Jay Lâm gửi tin muộn sau đợt quét buổi tối thì tự động
                         gộp tin vào bản tin sáng". Cơ chế gây vấp của bản cũ: phiên quét tối
                         chạy 20:47-21:26 còn file Jay Lâm gửi lúc 21:34 — muộn hơn cả bản
                         .docx cuối cùng — nên tin nằm chờ tới 20:47 HÔM SAU, mà khung ngày
                         khi đó đã đẩy nó sang nhóm quá hạn rồi đóng sổ. Tức tin gửi trong
                         khoảng 21:30-23:59 gần như KHÔNG BAO GIỜ tới tay, và không dấu hiệu
                         nào: file .docx vẫn ra đời bình thường, chỉ thiếu mục 5.
                         Đọc Supabase `dt_jaylam_inbox` (bảng
                         `telegram_bot.py::xu_ly_tin_jaylam()` ghi khi Jay Lâm gửi file .docx
                         vào bot) rồi đánh dấu đã gộp sau khi lưu file thành công.
                         In theo ĐÚNG khuôn 4 mục trên — tóm tắt 1-2 câu + link nguồn — vì
                         Huy chốt 30/07/2026: "tin Jay Lâm gửi cũng là tin kèm url và tóm tắt
                         gần giống định dạng mẫu". Phần tóm tắt + truy URL gốc do PHIÊN QUÉT
                         làm (`scripts/tin_jaylam.py`, cần agent nên không làm được ở đây) —
                         CẢ phiên sáng LẪN phiên tối đều phải chạy bước đó. Dòng CHƯA qua
                         bước đó thì KHÔNG vào file (Huy chốt 01/08/2026, bỏ hẳn nhánh dán
                         nguyên văn — xem `tach_chua_tom_tat()`): nó nằm chờ, không đóng sổ,
                         để bản tin kế tiếp gộp lại dưới dạng tin chuẩn.
                         Khung ngày: y như tin quét thường — mặc định 2 ngày, tin CNQS Mỹ
                         (cờ `la_cnqs`) được nới 3 ngày lùi; quá hạn thì bỏ + đánh dấu đã
                         gộp + cảnh báo. KHÔNG có trần số lượng.
                         Xem `doc_tin_jaylam_chua_gop()` và `add_jaylam_item()`.
(Đã BỎ mục Mạng xã hội (X) — ngoài phạm vi.)

Định dạng khớp mẫu:
  - Chữ: Times New Roman 14pt toàn bộ.
  - Tiêu đề "ĐIỂM TIN NGÀY d.M.yyyy": căn giữa, đậm, 14pt.
  - Đầu mục "N. <tên>": căn đều (justify), đậm, 14pt.
  - Mỗi tin: MỘT đoạn "- <nội dung>" (CHỈ summary — đã bỏ significance từ 27/07/2026), căn đều, 14pt, chữ thường
    (không đậm/nghiêng); dòng dưới là link nguồn (hyperlink xanh gạch chân).
  - Lề: trái/phải 1.25 inch, trên/dưới 1.0 inch.
Xuất ra đường dẫn in ở stdout (dòng cuối "DOCX=<path>"). Rỗng (không có tin) -> in "DOCX=".
Tên file GỌI THEO BUỔI (chỉ thị Huy 28/07/2026): /tmp/Diem-tin-sang-som-5h-<ngày>.docx hoặc
/tmp/Diem-tin-toi-21h-<ngày>.docx — xem hàm `ten_file()`.

Chạy: python3 .github/scripts/make_docx.py
"""
import datetime, json, os, re, subprocess, sys, unicodedata, zoneinfo

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.opc.constants import RELATIONSHIP_TYPE as RT

FONT = "Times New Roman"
SIZE = 14  # pt — khớp mẫu

VN = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")


def ten_file(gen, now=None):
    """Tên file .docx GỌI THEO BUỔI (chỉ thị Huy 28/07/2026): nhìn tên là biết bản nào.

      Diem-tin-sang-som-5h-<ngày>.docx  ·  Diem-tin-toi-21h-<ngày>.docx

    Ngưỡng buổi 14h giờ VN — CÙNG quy ước với `send_telegram.py:slot_label`,
    `send-email.js` và ô khoá `scripts/state.py`. Đổi lịch quét thì xem lại cả bốn nơi.

    ⚠️ ĐÂY LÀ NƠI DUY NHẤT ĐẶT TÊN FILE. Telegram (kênh gửi duy nhất hiện nay) hiện
    đúng basename của file trên đĩa, còn `send-email.js` lấy lại bằng `path.basename`
    thay vì tự ghép tên — hai bộ luật song song chắc chắn sẽ lệch, mà lệch âm thầm.
    """
    now = now or datetime.datetime.now(VN)
    buoi = "sang-som-5h" if now.hour < 14 else "toi-21h"
    return f"Diem-tin-{buoi}-{(gen or 'khong-ro-ngay').replace('/', '-')}.docx"


def extract_data(html):
    i = html.find("var DATA")
    if i < 0:
        raise ValueError('không thấy "var DATA"')
    start = html.find("{", i)
    depth = 0
    end = -1
    for k in range(start, len(html)):
        c = html[k]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                end = k
                break
    if end < 0:
        raise ValueError("không đóng được object DATA")
    return json.loads(html[start:end + 1])


def prev_data():
    """DATA của index.html ở commit cha (HEAD~1). Lỗi -> None."""
    try:
        out = subprocess.run(
            ["git", "show", "HEAD~1:index.html"],
            capture_output=True, text=True, timeout=60,
        )
        if out.returncode != 0 or not out.stdout:
            return None
        return extract_data(out.stdout)
    except Exception:
        return None


def event_items(data):
    """Gom item con của exercises (Predator...) thành list phẳng.

    CHỈ lấy `exercises` — bản tin TỐI không đưa sự kiện ngoại giao (dipEvents do phiên
    SÁNG tạo, gửi qua notify-morning). Predator's Run gộp vào mục QS-KHCN.
    """
    items = []
    for grp in ("exercises",):
        for ev in data.get(grp, []) or []:
            ev_name = ev.get("name", "")
            for it in ev.get("items", []) or []:
                it = dict(it)
                it["_event"] = ev_name
                items.append(it)
    return items


def urls_of(items, key="sourceUrl"):
    return {it.get(key) for it in items if it.get(key)}


def diff_new(cur, prev, kind):
    """Trả list tin mới (có trong cur, không có trong prev). kind: usNews|worldNews|events."""
    if kind == "events":
        cur_list = event_items(cur)
    else:
        cur_list = cur.get(kind, []) or []  # worldNews / usNews

    if prev is None:
        # Không có bản trước -> fallback: lấy tin đưa lên hôm nay
        today = cur.get("generatedAt")
        return [it for it in cur_list
                if it.get("_addedDate") == today or it.get("date") == today]

    if kind == "events":
        prev_urls = urls_of(event_items(prev))
    else:
        prev_urls = urls_of(prev.get(kind, []) or [])

    return [it for it in cur_list if it.get("sourceUrl") and it.get("sourceUrl") not in prev_urls]


def today_items(cur, kind):
    """Toàn bộ tin đưa lên hôm nay (fallback khi diff rỗng)."""
    today = cur.get("generatedAt")
    lst = event_items(cur) if kind == "events" else (cur.get(kind, []) or [])
    return [it for it in lst if it.get("_addedDate") == today or it.get("date") == today]


def pick_items(cur, prev, kind):
    """Tin của bản tin hôm nay = HỢP của (mới so với commit cha) và (_addedDate/date == generatedAt).

    ⚠️ Sự cố 25/07/2026 — docx chỉ có 3/15 tin: phiên quét commit `index.html` HAI lần
    (một commit `log: checkpoint ...` giữa chừng, rồi commit `Cap nhat ban tin` cuối).
    Chỉ commit cuối gửi email, nhưng lúc đó HEAD~1 đã chứa sẵn 12 tin nạp ở lô đầu nên
    `diff_new` chỉ còn 3 tin — và fallback cũ chỉ chạy khi diff RỖNG HẲN nên không cứu.
    Ngược lại, chỉ dùng `today_items` lại hụt tin của lô neo ngày cũ (`_addedDate` lệch
    `generatedAt`, xem "HAI BẪY khi lô tin trải QUÁ 2 NGÀY" trong CLAUDE.md).
    → Lấy HỢP để chắc cả hai chiều. Giữ nguyên thứ tự trong mảng gốc, không trùng lặp.
    """
    lst = event_items(cur) if kind == "events" else (cur.get(kind, []) or [])
    today = cur.get("generatedAt")
    new_urls = urls_of(diff_new(cur, prev, kind))
    out = []
    for it in lst:
        is_today = it.get("_addedDate") == today or it.get("date") == today
        url = it.get("sourceUrl")
        if is_today or (url and url in new_urls):
            out.append(it)
    return out


# Từ khoá nhận tin chủ đề 4 (Mỹ–Mali/Sahel) — cũng nằm trong `usNews` với category
# "Chính trị", nên phải tách ra khỏi mục "Nội bộ Mỹ". Viết KHÔNG DẤU vì so sau khi bỏ dấu.
MALI_KEYS = ("mali", "jnim", "bamako", "sahel", "azawad", "niger", "burkina",
             "africa corps", "chau phi", "sahen")
# Region được coi là "trong nước Mỹ". Rỗng cũng tính — xem chú thích trong is_noibo_my.
REGION_NOI_BO = ("", "Bắc Mỹ", "Châu Mỹ")


def _khong_dau(s):
    """Bỏ dấu tiếng Việt để so từ khoá. Cố ý viết tại chỗ thay vì import từ
    `scripts/tra_cuu_tin.py`: file này nằm trên đường đi của email hằng ngày, một lỗi
    import chéo thư mục là mất file .docx của cả bản tin."""
    s = unicodedata.normalize("NFD", str(s or "").lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn").replace("đ", "d")


def la_tin_mali(it):
    kho = _khong_dau(" ".join(str(it.get(k, "")) for k in
                              ("title", "summary", "region", "significance")))
    return any(k in kho for k in MALI_KEYS)


# Category của tin thuộc mục QS-KHCN. Đây là danh sách DƯƠNG — xem chú thích is_noibo_my.
CATEGORY_QSKHCN = ("Công nghệ quân sự",)


def la_qs_khcn(it):
    return (it.get("category") or "") in CATEGORY_QSKHCN


def is_noibo_my(it):
    """Nội bộ Mỹ = tin `usNews` KHÔNG phải khí tài, KHÔNG phải chuyện Mali/Sahel.

    ⚠️ VÁ LẦN 1 (27/07/2026) — trước đây điều kiện là `region == "Bắc Mỹ"`, và mục 1 của
    file .docx vì thế LUÔN RỖNG: mọi tin `usNews` nạp gần đây đều không có `region` (đếm
    thật: 9/9 tin đều `region: None`). Vì vậy region RỖNG vẫn được tính là nội bộ Mỹ — đó
    là trạng thái bình thường của dữ liệu. Đừng "siết cho chặt" bằng cách bắt buộc có
    region: làm vậy là tái lập đúng con bug đó.

    ⚠️ VÁ LẦN 2 (27/07/2026, sau khi Huy bắt lỗi tin Mali lòi ra mục QS-KHCN) — điều kiện
    cũ `category == "Chính trị"` cũng sai, chỉ theo hướng ngược lại: nó BỎ SÓT tin **Kinh
    tế** và **Ngoại giao**, mà theo 5 nhóm Nội bộ Mỹ Huy chốt thì nhóm 4 chính là *"hoạt
    động kinh tế Mỹ + hoạt động khác của các bộ và Nhà Trắng"*. Đếm thật trên DATA: 30 tin
    `Kinh tế` + 21 tin `Ngoại giao` đang bị dồn xuống mục khí tài — thực tế lọt vào bản
    27/07: "Mỹ áp gói thuế quan mới 10-12,5% lên khoảng 60 đối tác thương mại".

    GỐC của cả hai lần vá là cùng một thứ: **QS-KHCN từng được định nghĩa là "mọi usNews
    còn lại" — một cái thùng rác**, nên mọi phân loại thiếu sót đều đổ vào đó. Nay CẢ HAI
    mục đều định nghĩa DƯƠNG: QS-KHCN = category "Công nghệ quân sự"; Nội bộ Mỹ = phần còn
    lại KHÔNG phải khí tài và KHÔNG phải Mali. Thêm category mới thì cân nhắc nó thuộc mục
    nào, đừng để rơi tự do.
    """
    if la_qs_khcn(it):
        return False
    if la_tin_mali(it):
        return False
    return (it.get("region") or "") in REGION_NOI_BO


# Mục DUY NHẤT ghi kèm ngày tin trong .docx. Phải khớp ĐÚNG tên mục ở build_sections —
# đổi tên mục mà quên sửa đây thì ngày lặng lẽ biến mất, không có lỗi nào bật lên.
MUC_GHI_NGAY = "QS-KHCN"


def build_sections(us, world, events):
    """Chia thành 4 mục của bản tin.

    ⚠️ ĐÃ VÁ 27/07/2026 — Huy bắt lỗi: *"đang tin khcn-qs tự nhiên thấy lòi ra tin Mali, và
    chẳng thấy mục mali đâu"*. Trước đây hàm này chỉ dựng 3 mục và mục QS-KHCN được định
    nghĩa là "MỌI usNews còn lại", nên tin Mỹ–Mali (một trong 5 chủ đề, có mục riêng trên
    web) bị dồn vào đó nằm lẫn giữa tin khí tài — người đọc vừa thấy lạc lõng vừa mất hẳn
    một chủ đề. Thực tế lọt vào bản 27/07: "Al Jazeera phân tích liên minh JNIM", "Niger
    Abdourahamane Tiani… Mali, Burkina".

    Nay Mali có MỤC RIÊNG. Hai điểm phải giữ:
    - Lọc Mali từ CẢ `us` LẪN `world`: tin Sahel nằm ở mảng nào cũng có thể, và trước đây
      `world` được đổ nguyên vào "Úc và Biển Đông" nên tin Mali trong `world` sẽ lọt vào mục
      Biển Đông — đúng cùng một con lỗi, chỉ khác chỗ.
    - Ba nhánh phải LOẠI TRỪ NHAU, nếu không một tin sẽ in hai lần ở hai mục.
    - Và phải PHỦ HẾT: từ khi QS-KHCN thôi làm "thùng rác hứng phần còn lại", một tin không
      khớp nhánh nào sẽ BIẾN MẤT khỏi file mà không báo gì. Lưới cuối bên dưới gom phần rơi
      về mục 1 và in cảnh báo — mất tin tệ hơn nhiều so với xếp nhầm mục.

    Predator's Run vẫn nằm trong QS-KHCN qua `events` (bản tin mẫu để vậy, Huy không đụng).
    """
    mali = [it for it in us + world if la_tin_mali(it)]
    mali_urls = urls_of(mali)

    def khong_phai_mali(it):
        return it.get("sourceUrl") not in mali_urls

    sec1 = [it for it in us if is_noibo_my(it)]                       # 1. Nội bộ Mỹ
    sec2 = [it for it in world if khong_phai_mali(it)]                # 2. Úc & Biển Đông
    sec3 = [it for it in us                                           # 3. CNQS Mỹ (+ Predator)
            if la_qs_khcn(it) and khong_phai_mali(it)]

    # LƯỚI AN TOÀN — không được để tin nào rơi ra ngoài mọi mục.
    da_xep = urls_of(sec1) | urls_of(sec2) | urls_of(sec3) | mali_urls
    roi = [it for it in us + world
           if it.get("sourceUrl") and it.get("sourceUrl") not in da_xep]
    if roi:
        print(f"⚠️  {len(roi)} tin không khớp mục nào -> dồn vào 'Nội bộ Mỹ'. "
              f"Xem lại phân loại: "
              + " | ".join(f"[{it.get('category')}] {(it.get('title') or '')[:45]}"
                           for it in roi[:5]), file=sys.stderr)
        sec1 = sec1 + roi

    return [
        ("Nội bộ Mỹ", sec1),
        ("Úc và Biển Đông", sec2),
        (MUC_GHI_NGAY, sec3 + list(events)),
        ("Mỹ – Mali", mali),
    ]


# ---------- docx helpers ----------
def set_font(run, size=SIZE, bold=False, italic=False, color=None):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    if color:
        run.font.color.rgb = color
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for a in ("w:ascii", "w:hAnsi", "w:cs"):
        rfonts.set(qn(a), FONT)


def add_hyperlink(paragraph, url, text):
    part = paragraph.part
    r_id = part.relate_to(url, RT.HYPERLINK, is_external=True)
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)
    r = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    rfonts = OxmlElement("w:rFonts")
    for a in ("w:ascii", "w:hAnsi", "w:cs"):
        rfonts.set(qn(a), FONT)
    rpr.append(rfonts)
    sz = OxmlElement("w:sz"); sz.set(qn("w:val"), str(SIZE * 2)); rpr.append(sz)  # 14pt
    color = OxmlElement("w:color"); color.set(qn("w:val"), "0000FF"); rpr.append(color)
    u = OxmlElement("w:u"); u.set(qn("w:val"), "single"); rpr.append(u)
    r.append(rpr)
    t = OxmlElement("w:t"); t.set(qn("xml:space"), "preserve"); t.text = text
    r.append(t)
    hyperlink.append(r)
    paragraph._p.append(hyperlink)


def item_body(it):
    """Nội dung tin trong .docx: CHỈ `summary` (fallback `title` nếu thiếu summary).

    ⚠️ ĐÃ BỎ `significance` khỏi đây (chỉ thị Huy 27/07/2026: "ở nội dung tóm tắt tin trong
    file docx thì bỏ những câu đánh giá ở cuối"). Trước đây ghép `summary + significance`
    thành một đoạn, nên mỗi tin đều kết bằng một câu bình luận kiểu "cho thấy...", "phản
    ánh..." — đọc rất sáo và không phải thứ Huy cần trong bản tin.
    `significance` VẪN được giữ trong `DATA` và vẫn hiển thị trên web — chỉ không đưa vào
    file Word gửi kèm email. Đừng "dọn cho gọn" bằng cách xoá field này khỏi guardrail.
    """
    if it.get("summary"):
        return it["summary"].strip()
    if it.get("title"):
        return it["title"].strip()
    return ""


def ngay_ngan(s):
    """'2026-07-24' -> '24/07'. Không parse được thì trả nguyên chuỗi (còn hơn nuốt mất)."""
    s = str(s or "").strip()
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", s)
    return f"{m.group(3)}/{m.group(2)}" if m else s


def add_item(doc, it, ghi_ngay=False):
    """Một tin trong .docx: đoạn '- <tóm tắt>' rồi dòng link nguồn.

    `ghi_ngay=True` chèn '(dd/mm) ' vào ĐẦU đoạn — bật cho mục QS-KHCN (chỉ thị Huy
    27/07/2026). Chỉ mục này cần vì nó là mục DUY NHẤT được nới khung ngày: CNQS Mỹ lấy
    lùi tới 3 ngày (`MAX_AGE_DAYS_CNQS` trong add_news.py, `CNQS_LOOKBACK_DAYS` trong
    harvest.py), nên bản tin ngày 27 có thể chứa tin ngày 24 — không ghi ngày thì người
    đọc mặc định hiểu là tin hôm nay. Bốn mục còn lại chỉ có hôm nay + hôm qua nên ghi
    ngày vào đó chỉ làm rối.
    """
    body = item_body(it)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(2)
    d = ngay_ngan(it.get("date")) if ghi_ngay else ""
    set_font(p.add_run(f"- ({d}) {body}" if d else "- " + body), size=SIZE)

    url = it.get("sourceUrl")
    if url:
        pu = doc.add_paragraph()
        pu.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        pu.paragraph_format.space_after = Pt(8)
        add_hyperlink(pu, url, url)


def loc_chua_gui(items):
    """Bỏ tin ĐÃ nằm trong một bản tin đã gửi trước đó (sổ logs/da-gui-email.json).

    Chỉ thị Huy 27/07/2026: bản tin TỐI phải "loại cả những tin đã quét lúc 4h 5h sáng" —
    tức chỉ gồm tin thu được SAU lần gửi trước. Không có sổ (chạy lần đầu, file lỗi) thì
    trả nguyên danh sách: thà gửi trùng còn hơn gửi rỗng.
    """
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from so_da_gui import url_da_gui
        da_gui = url_da_gui()
    except Exception as e:                  # noqa: BLE001
        print(f"Không đọc được sổ đã gửi ({e}) — giữ nguyên toàn bộ tin.", file=sys.stderr)
        return items
    if not da_gui:
        return items
    out = [it for it in items if it.get("sourceUrl") not in da_gui]
    if len(out) != len(items):
        print(f"Sổ đã gửi: bỏ {len(items) - len(out)} tin đã có trong bản tin trước.",
              file=sys.stderr)
    return out


def _url_ca_sang(now):
    """URL đã gửi ở ca SÁNG cùng ngày, hoặc tập RỖNG nếu không áp được.

    Một đường đọc sổ duy nhất cho CẢ tin quét thường (`loc_bo_tin_ca_sang`) LẪN tin Jay Lâm
    (`loc_jaylam_ca_sang`) — hai nơi tự đọc sổ riêng thì chắc chắn lệch nhau, mà lệch âm
    thầm (mục 14 CLAUDE.md toàn cục).

    Rỗng nghĩa là KHÔNG lọc gì: bản sáng (tin vừa nạp, chưa từng gửi) · sổ chưa có dòng nào ·
    đọc sổ hỏng. Hướng lệch có chủ ý là LẶP một bản tin, không phải MẤT tin.
    """
    if not la_buoi_toi(now):
        return set()
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from so_da_gui import url_da_gui_buoi
        return url_da_gui_buoi("sang", now.strftime("%Y-%m-%d")) or set()
    except Exception as e:                  # noqa: BLE001
        print(f"Không đọc được sổ ca sáng ({e}) — giữ nguyên toàn bộ tin.", file=sys.stderr)
        return set()


def loc_bo_tin_ca_sang(items, now):
    """Bỏ khỏi bản TỐI những tin đã gửi ở ca SÁNG cùng ngày (Huy chốt 01/08/2026).

    ⚠️ ĐẢO LẠI chú thích cũ trong `main()` (*"KHÔNG lọc sổ ở đây… đừng cho nhất quán bằng
    cách bọc loc_chua_gui vào"*). Chú thích đó viết 27/07 khi THÂN EMAIL còn sống và chính
    nó gánh vai thực thi luật *"email tối = tin cả ngày TRỪ tin ca sáng sớm"*. Từ khi
    `GUI_EMAIL='0'` (27/07) thân email tắt và `.docx` thành kênh DUY NHẤT mang nội dung —
    tức lớp thực thi luật biến mất trong im lặng, còn luật thì vẫn nằm trong CLAUDE.md.
    Đo thật 01/08 trên sổ: **100% tin ca sáng lặp lại trong bản tối, cả 4/4 ngày** (28/07
    9/9 · 29/07 17/17 · 30/07 16/16 · 31/07 6/6).

    Phần chú thích cũ VẪN ĐÚNG ở chỗ nó cảnh báo: đừng bọc `loc_chua_gui` vào đây. Hàm đó
    lọc theo TOÀN sổ nên sẽ giết cả bản dựng lại của chính ca tối. Ở đây chỉ đọc dòng
    `buoi == "sang"` của ĐÚNG ngày hôm nay — xem `so_da_gui.url_da_gui_buoi`.

    Bản SÁNG không gọi hàm này: tin của nó vừa nạp, chưa từng gửi.
    """
    da_gui = _url_ca_sang(now)
    if not da_gui:
        return items
    out = [it for it in items if it.get("sourceUrl") not in da_gui]
    if len(out) != len(items):
        print(f"Ca sáng: bỏ {len(items) - len(out)} tin đã gửi trong bản tin sáng nay.",
              file=sys.stderr)
    return out


# --- Mục 5: Tin Jay Lâm gửi qua bot (thêm 30/07/2026) --------------------
JAYLAM_SUPABASE_URL = "https://ltmlueqkajqmduoqghdf.supabase.co"
JAYLAM_BANG = "dt_jaylam_inbox"

# Khung ngày — Huy chốt 30/07/2026: áp ĐÚNG khung tin quét thường, tức KHÔNG phải một con số
# duy nhất. Mặc định hôm nay + hôm qua; riêng CNQS Mỹ nới tới 3 ngày lùi.
# Huy nêu thẳng: *"tao cần tin cnqs Mỹ thì tin cũ 3 ngày vẫn để lại (ví dụ hôm nay 27 thì có
# thể giữ lại tin tận ngày 24)"* — áp trần 2 ngày cho mọi tin Jay Lâm là loại oan đúng nhóm
# khí tài/hợp đồng quốc phòng, nhóm mà tin đăng thưa và cuối tuần Mỹ gần như trắng.
# Cờ `la_cnqs` do phiên quét tối khai (`scripts/tin_jaylam.py`).
# ⚠️ Hai con số này khớp `add_news.py::MAX_AGE_DAYS`/`MAX_AGE_DAYS_CNQS`,
# `harvest.py::CNQS_LOOKBACK_DAYS` và `scripts/tin_jaylam.py`. Đã đăng ký
# `HeThong/dong-bo-luat.py` để các nơi lệch nhau là báo không đạt.
JAYLAM_MAX_AGE_DAYS = 1
JAYLAM_MAX_AGE_DAYS_CNQS = 3

# ⛔ NHÁNH DÁN NGUYÊN VĂN ĐÃ BỎ HẲN 01/08/2026 (Huy chốt) — trước đó dòng chưa qua bước tóm
# tắt được in thẳng `noi_dung` vào file, cắt ở `JAYLAM_FALLBACK_CHARS` = 50.000.
#
# Cơ chế gây vấp của nhánh cũ: nó KHÔNG phải nhánh hiếm mà là nhánh THƯỜNG TRỰC (phiên quét
# chạy 20:47-21:26, Jay Lâm gửi file 21:06 và 21:34 — tới sau khi bước tóm tắt đã xong), nên
# gần như tối nào bản .docx cũng có một khối chữ thô vài chục nghìn ký tự dán giữa bản tin:
# không tiêu đề, không link, không cắt theo từng tin, lẫn cả mục lục và ghi chú của file gốc.
# Đo tối 01/08/2026: một dòng như vậy dài 34.525 ký tự, bằng cả bốn mục tin cộng lại. Người
# đọc không phân biệt được đâu là tin. "Thà thô còn hơn mất tin" nghe hợp lý nhưng đo ra thì
# cái thô ấy làm hỏng cả bản tin, trong khi tin KHÔNG mất: mục 5 nay dựng ở CẢ HAI buổi và
# dòng chưa xử lý hưởng khung 3 ngày (`jaylam_gioi_han_ngay`), tức nó chờ đúng một phiên có
# chạy `tin_jaylam.py` rồi ra dưới dạng tin chuẩn.
#
# Rủi ro còn lại, khai rõ để phiên sau đừng tưởng là kín: cả sáng lẫn tối cùng bỏ bước tóm
# tắt 3 ngày liên tiếp thì dòng đó rơi vào nhóm quá hạn và bị đóng sổ mà CHƯA từng tới tay
# ai. `main()` kêu riêng ca này (`chưa từng tóm tắt`), không gộp vào cảnh báo quá hạn chung.
# Chỉ thị Huy 30/07/2026: mục này KHÔNG đi qua thang nguồn 3 tầng như 4 mục quét, nên phải
# nói thẳng ra để người đọc không tin ngang nhau.
JAYLAM_NHAN_XAC_MINH = ("Nội dung do Jay Lâm gửi qua bot, chưa qua thang xác minh nguồn "
                        "của bản tin.")


def la_buoi_toi(now):
    """True nếu `now` (giờ VN) rơi vào buổi TỐI — cùng ngưỡng 14h với `ten_file()`.

    Tách thành hàm riêng để test được KHÔNG cần giả lập `datetime.now()`: truyền thẳng
    một mốc giờ cụ thể vào là đủ.
    """
    return now.hour >= 14


def _jaylam_dt_key():
    """Mã `x-dt-key` — CÙNG quy ước với `telegram_bot.py:_dt_bot_key()`: env trước,
    lùi về file `/Users/Huy/Claude/.dt-bot-key` (chỉ có trên máy Huy). CI chỉ có env
    (secret `DT_BOT_KEY`); routine local dự phòng thì có cả hai, và env vẫn thắng nếu đặt."""
    k = os.environ.get("DT_BOT_KEY", "").strip()
    if k:
        return k
    try:
        with open("/Users/Huy/Claude/.dt-bot-key", "r", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def _jaylam_anon_key():
    k = os.environ.get("SUPABASE_ANON_KEY", "").strip()
    if k:
        return k
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            html_txt = f.read()
    except OSError:
        return ""
    m = re.search(r"sb_publishable_[A-Za-z0-9_-]{10,}", html_txt)
    return m.group(0) if m else ""


def jaylam_gioi_han_ngay(row):
    """Khung ngày áp cho MỘT dòng: 3 ngày nếu là tin CNQS Mỹ, 1 ngày nếu không.

    Dòng CHƯA được phiên quét xử lý cũng hưởng khung RỘNG — lúc đó không ai biết nó thuộc chủ
    đề gì, mà siết hẹp thì một phiên quét chết giữa chừng sẽ kéo theo việc LOẠI OAN tin CNQS
    (hướng lệch phải là giữ tin, không phải mất tin).
    """
    if not row.get("da_xu_ly"):
        return JAYLAM_MAX_AGE_DAYS_CNQS
    return JAYLAM_MAX_AGE_DAYS_CNQS if row.get("la_cnqs") else JAYLAM_MAX_AGE_DAYS


def jaylam_qua_han(row, now):
    """True nếu tin gửi cũ hơn khung ngày của chính dòng đó (xem `jaylam_gioi_han_ngay`).

    Đọc `created_at` hỏng -> True (phía KÊU): dòng không đo được tuổi thì đừng lặng lẽ vào
    bản tin như tin mới. Nó vẫn được đánh dấu đã gộp + in cảnh báo nên không nằm lại mãi.
    """
    try:
        t = datetime.datetime.fromisoformat(
            (row.get("created_at") or "").replace("Z", "+00:00")).astimezone(VN)
    except (ValueError, AttributeError, TypeError):
        return True
    return (now.date() - t.date()).days > jaylam_gioi_han_ngay(row)


def doc_tin_jaylam_chua_gop(now):
    """(trong_khung, qua_han) — tin Jay Lâm gửi CHƯA nằm trong bản tin nào, đọc qua mã riêng
    `x-dt-key` (giống `telegram_bot.py:lich_su_gan_day()`), KHÔNG phải service key.

    Huy chốt 30/07/2026 qua bảng chọn: áp khung 2 ngày như tin quét thường. Nhóm `qua_han`
    KHÔNG vào file nhưng VẪN được đánh dấu đã gộp ở nơi gọi kèm cảnh báo — không đánh dấu
    thì tối nào chúng cũng bị đọc ra rồi loại lại, tức nằm lại vĩnh viễn.

    Thiếu mã / đọc hỏng -> ([], []) và IN CẢNH BÁO — đây là phần LÀM GIÀU bản tin, không phải
    điều kiện cần để dựng file; hỏng ở đây không được làm cả file .docx biến mất.
    """
    key = _jaylam_anon_key()
    dt_key = _jaylam_dt_key()
    if not key or not dt_key:
        print("Thiếu SUPABASE_ANON_KEY/DT_BOT_KEY — bỏ qua mục Tin Jay Lâm gửi.",
              file=sys.stderr)
        return [], []
    try:
        p = subprocess.run(
            ["curl", "-sS", "--max-time", "30",
             f"{JAYLAM_SUPABASE_URL}/rest/v1/{JAYLAM_BANG}"
             "?select=id,ten,ten_file,noi_dung,created_at"
             ",tieu_de,tom_tat,nguon_ten,nguon_url,da_xu_ly,la_cnqs"
             "&da_gop=eq.false&order=created_at.asc",
             "-H", f"apikey: {key}", "-H", f"Authorization: Bearer {key}",
             "-H", f"x-dt-key: {dt_key}"],
            capture_output=True, text=True, timeout=35)
        rows = json.loads(p.stdout)
    except Exception as e:                              # noqa: BLE001
        print(f"Đọc tin Jay Lâm gửi hỏng ({e}) — bỏ qua mục này.", file=sys.stderr)
        return [], []
    if not isinstance(rows, list):
        print(f"Đọc tin Jay Lâm gửi trả về dạng lạ: {str(rows)[:200]} — bỏ qua mục này.",
              file=sys.stderr)
        return [], []
    trong, ngoai = [], []
    for r in rows:
        (ngoai if jaylam_qua_han(r, now) else trong).append(r)
    if ngoai:
        print(f"Tin Jay Lâm gửi: BỎ {len(ngoai)} tin quá khung ngày "
              "(vẫn đánh dấu đã gộp): "
              + "; ".join(f"id={r.get('id')} {r.get('created_at')} {r.get('ten_file')} "
                          f"[khung {jaylam_gioi_han_ngay(r) + 1} ngày]" for r in ngoai),
              file=sys.stderr)
    return trong, ngoai


def danh_dau_da_gop_jaylam(ids):
    """UPDATE `da_gop = true` cho các dòng vừa đưa vào file .docx — CHỈ gọi SAU khi
    `doc.save()` đã thành công, để tin không bị đánh dấu "đã gộp" khi file chưa ra đời."""
    if not ids:
        return
    key = _jaylam_anon_key()
    dt_key = _jaylam_dt_key()
    if not key or not dt_key:
        return
    subprocess.run(
        ["curl", "-sS", "--max-time", "30", "-X", "PATCH",
         f"{JAYLAM_SUPABASE_URL}/rest/v1/{JAYLAM_BANG}?id=in.({','.join(str(i) for i in ids)})",
         "-H", f"apikey: {key}", "-H", f"Authorization: Bearer {key}",
         "-H", f"x-dt-key: {dt_key}", "-H", "Content-Type: application/json",
         "-H", "Prefer: return=minimal", "-d", '{"da_gop": true}'],
        capture_output=True, text=True, timeout=35)


def _jaylam_tieu_de(row):
    """Tiêu đề đại diện, dùng cho bộ lọc chống trùng.

    Ưu tiên `tieu_de` do phiên quét tối viết (`scripts/tin_jaylam.py`) — nó đã truy về bài
    gốc nên khớp tiêu đề tin quét thường tốt hơn hẳn. Chưa xử lý thì lùi về dòng đầu KHÔNG
    rỗng của `noi_dung` (Jay Lâm gửi nguyên văn một file tin tức nên dòng đầu gần như luôn
    là tiêu đề bài), cuối cùng lùi về tên file.
    """
    td = (row.get("tieu_de") or "").strip()
    if td:
        return td[:200]
    for dong in (row.get("noi_dung") or "").splitlines():
        d = dong.strip()
        if d:
            return d[:200]
    return row.get("ten_file") or ""


def _jaylam_tokens(text):
    return set(re.sub(r"[^\w\s]", " ", _khong_dau(text)).split())


def loc_trung_jaylam(rows, tieu_de_da_co):
    """Bộ lọc chống trùng cho mục Jay Lâm — Jaccard ≥ 0.6, viết TẠI CHỖ (không import chéo
    thư mục, xem docstring `_khong_dau`). Hai chiều:
      (a) trùng với tin ĐÃ CÓ trong bản tin (quét thường vừa chọn) -> Jay Lâm gửi đúng tin
          web đã tự quét được, không cần đưa vào mục riêng nữa;
      (b) trùng GIỮA các dòng Jay Lâm với nhau -> gửi trùng/gửi lại cùng một bài.
    Trả về DANH SÁCH HIỂN THỊ (đã loại trùng) — ids bị loại vẫn được đánh dấu đã gộp ở nơi
    gọi, vì nội dung của chúng coi như đã có mặt trong bản tin qua bản còn lại.

    ⚠️ NGƯỠNG 0.6 Ở ĐÂY LÀ RIÊNG, ĐỪNG "ĐỒNG BỘ" VỚI `add_news.py` (tách 30/07/2026). Trước
    đó hai nơi dùng chung con số 0.6 và docstring này ghi "CÙNG NGƯỠNG"; ngày 30/07 lớp cảnh
    báo bên `add_news` hạ xuống 0.4 (`JACCARD_CANH_BAO_TIEU_DE`) để bắt tin NỐI TIẾP. Hai vai
    khác hẳn nhau: bên kia chỉ IN CẢNH BÁO cho người soạn (kêu thừa thì tốn một dòng đọc),
    còn hàm này LỌC THẬT — hạ ngưỡng ở đây là lọc oan, tức MẤT TIN của Jay Lâm khỏi mục 5 mà
    không ai thấy. Ca 10 của `tests/test-canh-bao-tin-noi-tiep.py` canh đúng chỗ này.
    """
    da_co = [t for t in (_jaylam_tokens(t) for t in tieu_de_da_co) if t]
    giu, da_dua = [], []
    for row in rows:
        tk = _jaylam_tokens(_jaylam_tieu_de(row))
        if not tk:
            giu.append(row)
            continue
        trung = any(len(tk & o) / len(tk | o) >= 0.6 for o in da_co) or \
            any(len(tk & o) / len(tk | o) >= 0.6 for o in da_dua)
        if trung:
            print(f"Tin Jay Lâm gửi '{_jaylam_tieu_de(row)[:60]}' nghi trùng tin đã có "
                  "trong bản tin -> bỏ khỏi mục riêng (vẫn đánh dấu đã gộp).",
                  file=sys.stderr)
            continue
        giu.append(row)
        da_dua.append(tk)
    return giu


def _jaylam_ngay_gio(created_at):
    """'30/07 09:15' giờ VN. Huy chốt 30/07/2026: ghi cả NGÀY, không chỉ giờ — mục này áp
    khung 2 ngày nên tin hôm qua vẫn vào được, chỉ ghi giờ thì nhìn như tin hôm nay."""
    try:
        return (datetime.datetime.fromisoformat((created_at or "").replace("Z", "+00:00"))
                .astimezone(VN).strftime("%d/%m %H:%M"))
    except (ValueError, AttributeError):
        return "--/-- --:--"


def da_tom_tat(row):
    """Dòng đã qua bước `scripts/tin_jaylam.py` của phiên quét: có cờ `da_xu_ly` VÀ có
    `tom_tat` thật. Xét cả hai vì `--ghi` đặt cờ theo lô — cờ bật mà tóm tắt rỗng thì in ra
    chỉ còn cái gạch đầu dòng trống, tức hỏng câm."""
    return bool(row.get("da_xu_ly")) and bool((row.get("tom_tat") or "").strip())


def tach_chua_tom_tat(rows):
    """Tách hàng chờ thành (ĐÃ tóm tắt, CHƯA tóm tắt).

    Chỉ nhóm đầu được vào file .docx; nhóm sau nằm chờ và KHÔNG đóng sổ (Huy chốt
    01/08/2026 — xem khối chú thích chỗ nhánh dán nguyên văn đã bỏ). Đây là lớp lọc DUY
    NHẤT cho việc đó: `add_jaylam_item` có chốt chặn thứ hai nhưng chốt ấy chỉ để không in
    ra tin rỗng nếu về sau có ai gọi thẳng hàm, không phải lớp thay thế cho phép tách này.
    """
    du, cho = [], []
    for r in rows:
        (du if da_tom_tat(r) else cho).append(r)
    return du, cho


def loc_jaylam_ca_sang(rows, now):
    """Bỏ khỏi bản TỐI dòng Jay Lâm có `nguon_url` ĐÃ đi trong bản SÁNG cùng ngày.
    Trả `(giữ, bỏ)`; nhóm bỏ VẪN đóng sổ vì nội dung của nó đã tới tay Huy sáng nay.

    Vá 01/08/2026. **Cơ chế gây vấp:** `loc_bo_tin_ca_sang` chỉ áp cho 03 mục quét thường,
    còn `loc_trung_jaylam` chỉ so tiêu đề với tin của CHÍNH bản đang dựng — nên tin Jay Lâm
    trùng bản tin sáng không lớp nào chặn. Đo tối 01/08: 04 tin lặp nguyên si bản sáng cùng
    ngày.

    ⚠️ Chỉ bắt được ca TRÙNG ĐÚNG URL. Jay Lâm gửi cùng sự kiện nhưng nguồn khác thì lọt —
    đó là giới hạn đã biết, không phải bug; siết bằng so tiêu đề sẽ lọc oan tin nối tiếp.
    """
    da_gui = _url_ca_sang(now)
    if not da_gui:
        return list(rows), []
    giu, bo = [], []
    for r in rows:
        u = (r.get("nguon_url") or "").strip()
        (bo if u and u in da_gui else giu).append(r)
    if bo:
        print(f"Tin Jay Lâm gửi: bỏ {len(bo)} tin đã đi trong bản tin SÁNG nay "
              "(vẫn đánh dấu đã gộp): "
              + "; ".join(f"id={r.get('id')} {r.get('nguon_url')}" for r in bo),
              file=sys.stderr)
    return giu, bo


def add_jaylam_item(doc, row):
    """Một tin Jay Lâm gửi, in theo ĐÚNG khuôn 4 mục quét thường (`add_item`): đoạn
    '- (dd/mm hh:mm) <tóm tắt>' rồi dòng link nguồn.

    Chỉ thị Huy 30/07/2026: *"tin Jay Lâm gửi cũng là tin kèm url và tóm tắt gần giống định
    dạng mẫu"*. `tieu_de`/`tom_tat`/`nguon_*` do phiên quét viết (`scripts/tin_jaylam.py`).

    Điều kiện tiên quyết: `da_tom_tat(row)` đúng — `main()` đã lọc bằng
    `tach_chua_tom_tat`. Chốt chặn dưới đây là lớp thứ hai, chỉ để không lặng lẽ in ra một
    gạch đầu dòng rỗng nếu về sau có đường gọi khác; nó KÊU rồi bỏ qua chứ không in.
    """
    if not da_tom_tat(row):
        print(f"Tin Jay Lâm id={row.get('id')} ({row.get('ten_file')}) chưa có tóm tắt mà "
              "vẫn được đưa tới add_jaylam_item -> BỎ QUA. Lọc bằng tach_chua_tom_tat() "
              "trước khi gọi.", file=sys.stderr)
        return
    dau = f"- ({_jaylam_ngay_gio(row.get('created_at'))}) "
    than_txt = dau + (row.get("tom_tat") or "").strip()
    url = (row.get("nguon_url") or "").strip()
    nguon_ten = (row.get("nguon_ten") or "").strip()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(2)
    set_font(p.add_run(than_txt), size=SIZE)

    pu = doc.add_paragraph()
    pu.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pu.paragraph_format.space_after = Pt(8)
    if url:
        add_hyperlink(pu, url, url)
    else:
        # Không truy được bài gốc thì vẫn GIỮ tin (cùng luật Agent 7 của Báo Mới) nhưng phải
        # nói rõ, kẻo người đọc tưởng tin thiếu link do lỗi dựng file.
        set_font(pu.add_run(f"Nguồn: {nguon_ten or 'Jay Lâm gửi'} "
                            "(không truy được bài gốc)"), size=SIZE, italic=True)


def main(now=None):
    now = now or datetime.datetime.now(VN)
    with open("index.html", "r", encoding="utf-8") as f:
        cur = extract_data(f.read())
    prev = prev_data()

    # ⚠️ ĐỪNG bọc `loc_chua_gui` vào đây — nó lọc theo TOÀN sổ nên giết cả bản dựng lại của
    # chính ca tối. Thứ đúng là `loc_bo_tin_ca_sang`: chỉ bỏ tin đã gửi ở ca SÁNG CÙNG NGÀY
    # (Huy chốt 01/08/2026 sau khi bắt được tin Healio/Schwartz-CDC lặp ở cả hai bản). Chỉ
    # thị 27/07 *"file word gộp cả 11 tin hôm nay"* nói về tin quét TAY giữa ngày — nhóm đó
    # không ghi sổ nên vẫn được giữ nguyên. Xem docstring của hàm.
    us = loc_bo_tin_ca_sang(pick_items(cur, prev, "usNews"), now)
    world = loc_bo_tin_ca_sang(pick_items(cur, prev, "worldNews"), now)
    events = loc_bo_tin_ca_sang(pick_items(cur, prev, "events"), now)

    sections = build_sections(us, world, events)

    # Mục 5 — CẢ HAI BUỔI (mở cho bản SÁNG 30/07/2026, xem docstring đầu file).
    # ⚠️ KHÔNG khoá theo `la_buoi_toi(now)` nữa: file gửi sau 21:30 tới muộn hơn cả bản .docx
    # cuối cùng của phiên tối, nên bản cũ để nó chờ tới 20:47 hôm sau — lúc đó khung ngày đã
    # đẩy sang nhóm quá hạn rồi đóng sổ. Hàng chờ tự lọc theo `da_gop`, nên bản nào dựng
    # trước thì bản đó gộp; không có đường một tin vào cả hai bản.
    # Khung ngày GIỮ NGUYÊN 2 ngày (CNQS 3) — đã xét: tin gửi muộn nhất 23:59 tới bản sáng
    # 03:47 hôm sau chỉ cách 1 ngày lịch, vẫn trong khung. Nới thêm là nhận tin cũ hơn chuẩn
    # tin quét thường, tức hạ chuẩn chứ không phải vá lỗ.
    # `jaylam_qh` = tin quá khung: KHÔNG vào file nhưng VẪN đánh dấu đã gộp (xem
    # `doc_tin_jaylam_chua_gop`). Không trần số lượng — Huy chốt 30/07/2026.
    jaylam_goc, jaylam_qh = doc_tin_jaylam_chua_gop(now)
    # Dòng chưa qua bước tóm tắt: KHÔNG vào file, KHÔNG đóng sổ — chờ phiên sau (Huy chốt
    # 01/08/2026). Kêu ngay tại đây, trước nhánh `total == 0`, kẻo hôm nào cả bản tin rỗng
    # thì cảnh báo bị nuốt cùng.
    jaylam_du, jaylam_cho = tach_chua_tom_tat(jaylam_goc)
    jaylam_du, jaylam_sang = loc_jaylam_ca_sang(jaylam_du, now)
    if jaylam_cho:
        print(f"Tin Jay Lâm gửi: GIỮ LẠI {len(jaylam_cho)} dòng CHƯA qua bước tóm tắt "
              "(không vào file, không đóng sổ — chờ bản tin sau): "
              + "; ".join(f"id={r.get('id')} {r.get('ten_file')}" for r in jaylam_cho)
              + ". Kiểm bước `tin_jaylam.py` trong playbook quét tin.", file=sys.stderr)
    # Ca MẤT TIN THẬT, tách khỏi cảnh báo quá hạn chung: dòng hết khung ngày mà chưa phiên
    # nào tóm tắt thì nó bị đóng sổ dưới đây và chưa từng tới tay ai đọc.
    qh_chua_tt = [r for r in jaylam_qh if not da_tom_tat(r)]
    if qh_chua_tt:
        print(f"⚠️ Tin Jay Lâm gửi: {len(qh_chua_tt)} dòng HẾT KHUNG NGÀY mà CHƯA TỪNG được "
              "tóm tắt -> đóng sổ, không bản tin nào đăng: "
              + "; ".join(f"id={r.get('id')} {r.get('created_at')} {r.get('ten_file')}"
                          for r in qh_chua_tt)
              + ". Bước `tin_jaylam.py` đã bị bỏ nhiều phiên liên tiếp.", file=sys.stderr)

    jaylam_hien = []
    if jaylam_du:
        tieu_de_da_co = [it.get("title") or "" for it in us + world + list(events)]
        jaylam_hien = loc_trung_jaylam(jaylam_du, tieu_de_da_co)

    total = sum(len(items) for _, items in sections) + len(jaylam_hien)
    if total == 0:
        # Hôm nay 0 tin -> không có file. Nhóm QUÁ HẠN vẫn phải đánh dấu: nó bị bỏ hẳn, không
        # phụ thuộc việc file có ra đời hay không, và để lại thì tối nào cũng loại lại.
        # `jaylam_sang` cũng đóng sổ: nội dung của nó đã tới tay Huy trong bản SÁNG nay,
        # không phụ thuộc việc tối nay có file hay không.
        # Nhóm còn trong khung (`jaylam_du`/`jaylam_cho`) thì KHÔNG — chúng chưa vào bản
        # tin nào, và không có file thì cũng không có gì tới tay Huy để mà đóng sổ.
        if jaylam_qh or jaylam_sang:
            danh_dau_da_gop_jaylam([r["id"] for r in jaylam_sang + jaylam_qh])
        print("DOCX=")
        return

    gen = cur.get("generatedAt", "")
    try:
        y, m, d = gen.split("-")
        title_date = f"{int(d)}.{int(m)}.{y}"
    except Exception:
        title_date = gen

    doc = Document()
    # Lề khớp mẫu: trái/phải 1.25", trên/dưới 1.0"
    for s in doc.sections:
        s.left_margin = Inches(1.25)
        s.right_margin = Inches(1.25)
        s.top_margin = Inches(1.0)
        s.bottom_margin = Inches(1.0)

    # Tiêu đề căn giữa, đậm, 14pt
    pt = doc.add_paragraph()
    pt.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pt.paragraph_format.space_after = Pt(10)
    set_font(pt.add_run(f"ĐIỂM TIN NGÀY {title_date}"), size=SIZE, bold=True)

    idx = 0
    for name, items in sections:
        if not items:
            continue
        idx += 1
        ph = doc.add_paragraph()
        ph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        ph.paragraph_format.space_before = Pt(8)
        ph.paragraph_format.space_after = Pt(4)
        set_font(ph.add_run(f"{idx}. {name}"), size=SIZE, bold=True)
        # QS-KHCN là mục duy nhất được nới khung ngày (tới 3 ngày) -> phải ghi rõ ngày tin.
        ghi_ngay = name == MUC_GHI_NGAY
        for it in items:
            add_item(doc, it, ghi_ngay=ghi_ngay)

    if jaylam_hien:
        idx += 1
        ph = doc.add_paragraph()
        ph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        ph.paragraph_format.space_before = Pt(8)
        ph.paragraph_format.space_after = Pt(4)
        set_font(ph.add_run(f"{idx}. Tin Jay Lâm gửi"), size=SIZE, bold=True)
        # Nhãn xác minh — Huy chốt 30/07/2026: mục này không đi qua thang nguồn 3 tầng nên
        # phải nói thẳng, kẻo người đọc lướt qua tin ngang với 4 mục đã xác minh.
        pn = doc.add_paragraph()
        pn.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        pn.paragraph_format.space_after = Pt(4)
        set_font(pn.add_run(JAYLAM_NHAN_XAC_MINH), size=SIZE - 1, italic=True)
        for row in jaylam_hien:
            add_jaylam_item(doc, row)

    out = f"/tmp/{ten_file(gen, now)}"
    doc.save(out)
    # Đánh dấu SAU khi save thành công. Đóng sổ cả dòng bị lọc trùng (xem docstring
    # `loc_trung_jaylam`) lẫn dòng QUÁ KHUNG NGÀY: bỏ sót nhóm quá hạn thì tối nào chúng cũng
    # được đọc ra rồi loại lại, tức nằm lại vĩnh viễn trong hàng chờ.
    #
    # ⚠️ `jaylam_cho` (chưa tóm tắt) CỐ Ý KHÔNG có mặt ở đây — nó không vào file thì cũng
    # không được coi là đã đăng. Đo thật tối 30/07/2026 ở bản cũ: dòng id=1 tới lúc 21:06,
    # bản .docx 21:29 in nguyên văn rồi đánh dấu luôn, nên bản 21:33 — bản CUỐI CÙNG Huy
    # nhận — mất sạch mục 5. Không đóng sổ thì bản tin kế tiếp gộp lại dưới dạng tin chuẩn;
    # tới hết khung ngày mà vẫn chưa ai tóm tắt thì nó rơi vào `jaylam_qh` và đóng sổ ở đó,
    # kèm dòng kêu riêng phía trên — không có đường kẹt vĩnh viễn.
    can_danh_dau = [r["id"] for r in jaylam_du + jaylam_sang + jaylam_qh]
    if can_danh_dau:
        danh_dau_da_gop_jaylam(can_danh_dau)
    print(f"DOCX={out}")


if __name__ == "__main__":
    main()
