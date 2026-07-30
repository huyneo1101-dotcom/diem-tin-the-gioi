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
  5. Tin Jay Lâm gửi  -> CHỈ ở bản BUỔI TỐI (thêm 30/07/2026, Huy chốt: "tổng hợp file Jay
                         Lâm gửi cùng với kết quả quét tin buổi tối thành 1 file — như hàng
                         ngày vẫn làm"). Đọc Supabase `dt_jaylam_inbox` (bảng
                         `telegram_bot.py::xu_ly_tin_jaylam()` ghi khi Jay Lâm gửi file .docx
                         vào bot), lấy MỌI dòng CHƯA gộp — không giới hạn theo ngày, để một
                         bản tối bị trễ/skip không làm mất tin của ngày trước — rồi đánh dấu
                         đã gộp sau khi lưu file .docx thành công. Xem `doc_tin_jaylam_chua_gop()`.
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


# --- Mục 5: Tin Jay Lâm gửi qua bot (thêm 30/07/2026) --------------------
JAYLAM_SUPABASE_URL = "https://ltmlueqkajqmduoqghdf.supabase.co"
JAYLAM_BANG = "dt_jaylam_inbox"


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


def doc_tin_jaylam_chua_gop():
    """Tin Jay Lâm gửi qua bot, CHƯA nằm trong bản tin nào — đọc qua mã riêng `x-dt-key`
    (giống `telegram_bot.py:lich_su_gan_day()`), KHÔNG phải service key.

    Không giới hạn theo ngày — lấy MỌI dòng `da_gop = false`: nếu bản tối hôm qua bị
    trễ/skip thì tin của Jay Lâm không mất, nó dồn sang bản tối kế tiếp thay vì rơi khỏi
    khung ngày như tin quét thường (khác `pick_items`, cố ý).

    Thiếu mã / đọc hỏng -> [] và IN CẢNH BÁO — đây là phần LÀM GIÀU bản tin, không phải
    điều kiện cần để dựng file; hỏng ở đây không được làm cả file .docx biến mất.
    """
    key = _jaylam_anon_key()
    dt_key = _jaylam_dt_key()
    if not key or not dt_key:
        print("Thiếu SUPABASE_ANON_KEY/DT_BOT_KEY — bỏ qua mục Tin Jay Lâm gửi.",
              file=sys.stderr)
        return []
    try:
        p = subprocess.run(
            ["curl", "-sS", "--max-time", "30",
             f"{JAYLAM_SUPABASE_URL}/rest/v1/{JAYLAM_BANG}"
             "?select=id,ten,ten_file,noi_dung,created_at"
             "&da_gop=eq.false&order=created_at.asc",
             "-H", f"apikey: {key}", "-H", f"Authorization: Bearer {key}",
             "-H", f"x-dt-key: {dt_key}"],
            capture_output=True, text=True, timeout=35)
        rows = json.loads(p.stdout)
    except Exception as e:                              # noqa: BLE001
        print(f"Đọc tin Jay Lâm gửi hỏng ({e}) — bỏ qua mục này.", file=sys.stderr)
        return []
    if not isinstance(rows, list):
        print(f"Đọc tin Jay Lâm gửi trả về dạng lạ: {str(rows)[:200]} — bỏ qua mục này.",
              file=sys.stderr)
        return []
    return rows


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
    """Dòng đầu KHÔNG rỗng của `noi_dung` làm tiêu đề đại diện — Jay Lâm gửi nguyên văn
    một file tin tức nên dòng đầu gần như luôn là tiêu đề bài, giống cách tin quét thường
    có sẵn `title`. Không có dòng nào -> lùi về tên file."""
    for dong in (row.get("noi_dung") or "").splitlines():
        d = dong.strip()
        if d:
            return d[:200]
    return row.get("ten_file") or ""


def _jaylam_tokens(text):
    return set(re.sub(r"[^\w\s]", " ", _khong_dau(text)).split())


def loc_trung_jaylam(rows, tieu_de_da_co):
    """Bộ lọc chống trùng cho mục Jay Lâm — CÙNG NGƯỠNG Jaccard ≥ 0.6 mà
    `add_news.py:warn_similar_titles()` dùng cho tin quét thường, viết TẠI CHỖ (không
    import chéo thư mục, xem docstring `_khong_dau`). Hai chiều:
      (a) trùng với tin ĐÃ CÓ trong bản tin (quét thường vừa chọn) -> Jay Lâm gửi đúng tin
          web đã tự quét được, không cần đưa vào mục riêng nữa;
      (b) trùng GIỮA các dòng Jay Lâm với nhau -> gửi trùng/gửi lại cùng một bài.
    Trả về DANH SÁCH HIỂN THỊ (đã loại trùng) — ids bị loại vẫn được đánh dấu đã gộp ở nơi
    gọi, vì nội dung của chúng coi như đã có mặt trong bản tin qua bản còn lại.
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


def _jaylam_gio(created_at):
    try:
        return (datetime.datetime.fromisoformat((created_at or "").replace("Z", "+00:00"))
                .astimezone(VN).strftime("%H:%M"))
    except (ValueError, AttributeError):
        return "--:--"


def add_jaylam_item(doc, row):
    """Một tin Jay Lâm gửi: dòng đậm 'HH:MM — tên_file (tên người)' rồi đoạn nội dung —
    khác `add_item` vì đây là nguyên văn Jay Lâm gửi, không có `sourceUrl`/`summary`."""
    nhan = doc.add_paragraph()
    nhan.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    nhan.paragraph_format.space_after = Pt(2)
    set_font(nhan.add_run(f"{_jaylam_gio(row.get('created_at'))} — "
                           f"{row.get('ten_file') or '(không tên)'} "
                           f"({row.get('ten') or 'Jay Lâm'})"),
             size=SIZE, bold=True)
    than = doc.add_paragraph((row.get("noi_dung") or "(rỗng)").strip())
    than.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    than.paragraph_format.space_after = Pt(8)
    for run in than.runs:
        set_font(run, size=SIZE)


def main(now=None):
    now = now or datetime.datetime.now(VN)
    with open("index.html", "r", encoding="utf-8") as f:
        cur = extract_data(f.read())
    prev = prev_data()

    # ⚠️ KHÔNG lọc sổ đã gửi ở đây. Chỉ thị Huy 27/07/2026: *"gửi file word tối nay sau khi
    # quét lúc 9h thì gộp cả 11 tin hôm nay đó vào"*. FILE WORD là BẢN TỔNG HỢP CẢ NGÀY —
    # thứ Huy lưu lại — nên phải đủ mọi tin nạp trong ngày, kể cả tin đã báo qua email sáng.
    # Chỉ THÂN EMAIL và TIN NHẮN TELEGRAM mới lọc sổ, vì chúng là thông báo, lặp lại thì thừa.
    # Đừng "cho nhất quán" bằng cách bọc loc_chua_gui vào đây — đó là đúng con lỗi vừa sửa.
    us = pick_items(cur, prev, "usNews")
    world = pick_items(cur, prev, "worldNews")
    events = pick_items(cur, prev, "events")

    sections = build_sections(us, world, events)

    # Mục 5 — CHỈ ở bản buổi TỐI (xem docstring đầu file + `la_buoi_toi()`).
    jaylam_goc = doc_tin_jaylam_chua_gop() if la_buoi_toi(now) else []
    jaylam_hien = []
    if jaylam_goc:
        tieu_de_da_co = [it.get("title") or "" for it in us + world + list(events)]
        jaylam_hien = loc_trung_jaylam(jaylam_goc, tieu_de_da_co)

    total = sum(len(items) for _, items in sections) + len(jaylam_hien)
    if total == 0:
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
        for row in jaylam_hien:
            add_jaylam_item(doc, row)

    out = f"/tmp/{ten_file(gen, now)}"
    doc.save(out)
    # Đánh dấu SAU khi save thành công — và đánh dấu HẾT (kể cả dòng bị lọc trùng, xem
    # docstring `loc_trung_jaylam`), không chỉ những dòng thực sự hiện trong file.
    if jaylam_goc:
        danh_dau_da_gop_jaylam([r["id"] for r in jaylam_goc])
    print(f"DOCX={out}")


if __name__ == "__main__":
    main()
