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
(Đã BỎ mục Mạng xã hội (X) — ngoài phạm vi.)

⛔ MỤC 5 "Tin Jay Lâm gửi" ĐÃ BỎ HẲN 01/08/2026 — Huy đảo nguyên tắc: *"file của Jay Lâm gửi
chỉ là để so sánh xem có tin nào mày quét được mà bị trùng với tin trong file đó không thôi"*
· *"nếu có tin bị trùng với file Jay Lâm thì tự xoá khỏi tổng hợp tin đã quét đi và gửi file
word (trong đó không có tin nào từ Jay Lâm)"*. File Jay Lâm nay là **BỘ LỌC**: nó không đóng
góp dòng nào vào bản tin, chỉ dùng để bớt tin CỦA MÌNH mà anh ta đã đọc rồi.
Việc đối chiếu cần đọc hiểu theo SỰ KIỆN nên thuộc về PHIÊN QUÉT (có agent), không làm được
ở đây; phiên quét khai kết quả vào sổ `logs/trung-jaylam.json` qua
`scripts/tin_jaylam.py --ghi-loai`, và file này chỉ việc đọc sổ rồi bỏ tin — xem
`doc_url_trung_jaylam()` / `loc_bo_trung_jaylam()`. Vì thế file này KHÔNG còn chạm Supabase.

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


def _kho_chu(it):
    return " ".join(str(it.get(k, "")) for k in ("title", "summary", "region", "significance"))


# Bảng neo của chủ đề 2 nằm ở `scripts/topics.py` — MỘT hàm kiểm tra duy nhất, dùng chung
# với cổng nạp `add_news.py`. Chép bảng sang đây thì hai bản tách nhánh ở lần vá sau mà
# không ai thấy.
#
# ⚠️ ĐÁNH ĐỔI CÓ CHỦ Ý, khác hẳn `_khong_dau` ở trên (hàm đó chép tại chỗ vì nó chỉ là
# 2 dòng, chép không sinh ra nguồn sự thật thứ hai). Ở đây phần chép sẽ là một BẢNG TỪ
# KHOÁ ~50 mục — thứ chắc chắn được sửa tiếp và chắc chắn lệch. Nên chấp nhận import chéo
# thư mục, và CỐ Ý ĐỂ NÉM LỖI thay vì `try/except` cho êm: import hỏng thì .docx không
# sinh ra và CI đỏ ngay, còn `except: lambda _: True` thì mục 2 lặng lẽ trở lại làm cái
# thùng chứa — đúng thứ đang đi vá. File mất thì có tiếng kêu; file sai nội dung thì không.
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "scripts"))
from topics import neo_uc_bien_dong  # noqa: E402


def la_uc_bien_dong(it):
    """Tin có tự neo được vào Úc hoặc Biển Đông không? (điều kiện vào mục 2)

    ⚠️ VÁ 01/08/2026 — Huy bắt: *"hàn quốc liên quan đ gì đến biển đông và Úc mà cứ cho
    vào???"*. Trước đây mục 2 được định nghĩa là **MỌI `worldNews` trừ Mali**, tức một cái
    thùng: tin thế giới nào lọt qua tầng quét cũng tự động được dán nhãn "Úc và Biển Đông",
    nên tên mục là một lời hứa còn nội dung là phần dư. Bản tối 01/08 có 04 tin thì 03 sai
    (Nhật phóng Tomahawk từ JS Chokai · Trung Quốc phóng YJ-20 · Hàn ký 7,8 nghìn tỷ won
    với Hanwha Ocean) — cả ba không dính Úc, không dính Biển Đông.

    Đây là CÙNG con lỗi đã vá hai lần ở `is_noibo_my`, chỉ khác mảng: mục nào được định
    nghĩa bằng "phần còn lại" thì mọi phân loại thiếu sót đều đổ vào nó. Nay cả bốn mục
    đều định nghĩa DƯƠNG.

    Tin rớt KHÔNG biến mất — lưới an toàn ở `build_sections` gom về mục 1 kèm cảnh báo, vì
    mất tin tệ hơn xếp nhầm mục. Chính cảnh báo đó là tín hiệu cho biết tầng quét đã lọt.
    """
    return neo_uc_bien_dong(_kho_chu(it))


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
    sec2 = [it for it in world                                        # 2. Úc & Biển Đông
            if khong_phai_mali(it) and la_uc_bien_dong(it)]
    sec3 = [it for it in us                                           # 3. CNQS Mỹ (+ Predator)
            if la_qs_khcn(it) and khong_phai_mali(it)]

    # LƯỚI AN TOÀN — không được để tin nào rơi ra ngoài mọi mục.
    da_xep = urls_of(sec1) | urls_of(sec2) | urls_of(sec3) | mali_urls
    roi = [it for it in us + world
           if it.get("sourceUrl") and it.get("sourceUrl") not in da_xep]
    if roi:
        # Tách riêng nhóm tin THẾ GIỚI rơi vì không neo được vào Úc/Biển Đông (siết
        # 01/08/2026). Nhóm này khác hẳn nhóm rơi vì thiếu category: nó nói rằng TẦNG QUÉT
        # đã nạp tin ngoài phạm vi 5 chủ đề, tức phải sửa ở `add_news.py`/phiên quét chứ
        # không phải sửa phân loại ở đây. Gộp chung một dòng cảnh báo thì hai nguyên nhân
        # khác nhau ra cùng một câu chữ, và người đọc sẽ đi sửa nhầm chỗ.
        world_urls = urls_of(world)
        lac_muc2 = [it for it in roi if it.get("sourceUrl") in world_urls]
        if lac_muc2:
            print(f"⚠️  {len(lac_muc2)} tin worldNews KHÔNG neo được vào Úc/Biển Đông -> "
                  f"tạm dồn vào 'Nội bộ Mỹ' để không mất tin. Đây là lỗi TẦNG QUÉT, "
                  f"không phải lỗi phân loại: "
                  + " | ".join((it.get("title") or "")[:45] for it in lac_muc2[:5]),
                  file=sys.stderr)
        con_lai = [it for it in roi if it.get("sourceUrl") not in world_urls]
        if con_lai:
            print(f"⚠️  {len(con_lai)} tin không khớp mục nào -> dồn vào 'Nội bộ Mỹ'. "
                  f"Xem lại phân loại: "
                  + " | ".join(f"[{it.get('category')}] {(it.get('title') or '')[:45]}"
                               for it in con_lai[:5]), file=sys.stderr)
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

    Một đường đọc sổ duy nhất cho mọi nơi cần biết "tin nào đã gửi ca sáng" — hai nơi tự đọc
    sổ riêng thì chắc chắn lệch nhau, mà lệch âm thầm (mục 14 CLAUDE.md toàn cục). Người gọi
    thứ hai (`loc_jaylam_ca_sang`) đã bỏ cùng mục 5 ngày 01/08/2026; nay chỉ còn
    `loc_bo_tin_ca_sang`, nhưng vẫn giữ hàm tách riêng để lớp sau khỏi tự dựng lại.

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


# --- File Jay Lâm gửi = BỘ LỌC: bỏ tin CỦA MÌNH mà anh ta đã có ----------
# Huy đảo nguyên tắc 01/08/2026 (xem docstring đầu file). Mục 5 và toàn bộ đường đọc Supabase
# đã bỏ; thứ còn lại ở đây là lớp MỎNG đọc sổ do phiên quét khai.
#
# ⚠️ Vì sao phép lọc không nằm ở file này: so LINK THUẦN là vô dụng — đo 01/08 trên 12 tin
# quét và 37 URL trong file Jay ra **0 tin trùng URL**, trong khi đọc hiểu ra **03 tin trùng
# sự kiện** (Mahan Air · tuần tra Scarborough · NITE-STAR 981 triệu USD), vì Jay Lâm viết lại
# bằng tiếng Việt từ nguồn khác hẳn. Đọc hiểu theo sự kiện cần agent, mà file này chạy trong
# workflow `notify-email.yml` — không có agent. Nên phiên quét khai kết quả vào sổ, file này
# chỉ so URL với sổ đó.
#
# ⚠️ Hằng số khung ngày (`JAYLAM_MAX_AGE_DAYS…`) đã XOÁ khỏi file này, cố ý: sổ tự cắt theo
# `tin_jaylam.py::GIU_NGAY`, nên ở đây không còn phép đo tuổi nào. Nếu `HeThong/dong-bo-luat.py`
# còn khai file này là nơi trích khung ngày Điểm Tin thì phải gỡ dòng đó, kẻo nó báo
# "KHÔNG ĐO ĐƯỢC" vĩnh viễn.
SO_TRUNG_JAYLAM = "logs/trung-jaylam.json"


def la_buoi_toi(now):
    """True nếu `now` (giờ VN) rơi vào buổi TỐI — cùng ngưỡng 14h với `ten_file()`.

    Tách thành hàm riêng để test được KHÔNG cần giả lập `datetime.now()`: truyền thẳng
    một mốc giờ cụ thể vào là đủ.

    ⚠️ Mục 5 đã bỏ nên hàm này CHỈ còn phục vụ `ten_file()`. Đừng thấy hết chỗ gọi trong
    logic mục 5 mà xoá — tên file `-sang-som-5h-`/`-toi-21h-` vẫn dựa vào ngưỡng này.
    """
    return now.hour >= 14


def doc_url_trung_jaylam():
    """Tập URL tin CỦA MÌNH đã được phiên quét xác định là trùng file Jay Lâm.

    Nguồn: `logs/trung-jaylam.json`, do `scripts/tin_jaylam.py --ghi-loai` ghi sau khi agent
    đối chiếu theo SỰ KIỆN. Sổ tự cắt theo `GIU_NGAY` bên đó nên ở đây không đo tuổi.

    ⚠️ FAIL VỀ PHÍA KHÔNG LỌC, và đó là chủ ý: sổ thiếu/hỏng thì bản tin LẶP một tin Jay Lâm
    đã có — phiền nhưng Huy thấy được ngay khi đọc; còn fail về phía lọc thì tin biến mất
    khỏi bản tin mà không ai biết. Xoá tin là hướng lệch tệ hơn lặp tin.
    ⚠️ Nhưng KHÔNG được im: thiếu sổ vẫn in một dòng, kẻo bước `--ghi-loai` bị bỏ nhiều phiên
    liền mà nhìn log không phân biệt được với "hôm nay không có tin nào trùng".
    """
    try:
        with open(SO_TRUNG_JAYLAM, "r", encoding="utf-8") as f:
            rows = json.load(f)
    except FileNotFoundError:
        print(f"Không có {SO_TRUNG_JAYLAM} — không lọc tin trùng file Jay Lâm. "
              "(Bước `tin_jaylam.py --ghi-loai` của phiên quét chưa từng chạy?)",
              file=sys.stderr)
        return set()
    except (OSError, json.JSONDecodeError) as e:
        print(f"Đọc {SO_TRUNG_JAYLAM} hỏng ({e}) — KHÔNG lọc, giữ nguyên tin.",
              file=sys.stderr)
        return set()
    if not isinstance(rows, list):
        print(f"{SO_TRUNG_JAYLAM} không phải mảng — KHÔNG lọc, giữ nguyên tin.",
              file=sys.stderr)
        return set()
    return {(r.get("url") or "").strip() for r in rows
            if isinstance(r, dict) and (r.get("url") or "").strip()}


def loc_bo_trung_jaylam(items, urls, ten_muc=""):
    """Bỏ khỏi bản tin những tin mà Jay Lâm đã có (Huy chốt 01/08/2026).

    So bằng `sourceUrl` — ở ĐÂY thì so URL là đúng, khác hẳn việc dùng URL để PHÁT HIỆN
    trùng. Cái được so là URL tin của chính mình, do agent liệt kê ra sau khi đã đọc hiểu;
    nó chỉ đóng vai khoá tra cứu, không phải phép đo giống nhau.

    Kêu từng tin bị bỏ: xoá tin là mất nội dung, phải soi ngược được (sổ giữ cả `trung_voi`).
    """
    if not urls:
        return items
    out = [it for it in items if (it.get("sourceUrl") or "").strip() not in urls]
    if len(out) != len(items):
        bo = [it for it in items if (it.get("sourceUrl") or "").strip() in urls]
        print(f"Bộ lọc Jay Lâm{' [' + ten_muc + ']' if ten_muc else ''}: bỏ {len(bo)} tin "
              "Jay Lâm đã có: "
              + "; ".join((it.get("title") or it.get("sourceUrl") or "?")[:70] for it in bo),
              file=sys.stderr)
    return out


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

    # Bộ lọc Jay Lâm — bỏ tin mình quét được mà anh ta đã có (Huy chốt 01/08/2026).
    # Áp cho CẢ BA mục: cơ chế gây vấp của `loc_bo_tin_ca_sang` bản đầu là chỉ áp 03 mục quét
    # mà quên mục 5, nên lỗ trùng vẫn hở; ở đây không còn mục 5 nhưng vẫn phải phủ đủ ba,
    # tin Jay Lâm gửi có cả tin thế giới lẫn tin tập trận.
    trung_jl = doc_url_trung_jaylam()
    us = loc_bo_trung_jaylam(us, trung_jl, "usNews")
    world = loc_bo_trung_jaylam(world, trung_jl, "worldNews")
    events = loc_bo_trung_jaylam(events, trung_jl, "events")

    sections = build_sections(us, world, events)

    total = sum(len(items) for _, items in sections)
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

    out = f"/tmp/{ten_file(gen, now)}"
    doc.save(out)
    # ⚠️ KHÔNG còn bước đánh dấu Supabase nào ở đây (bỏ 01/08/2026 cùng mục 5). Việc đóng sổ
    # dòng Jay Lâm hết khung ngày nay nằm ở `scripts/tin_jaylam.py::in_hang_cho()` — tức ở
    # chính chỗ đọc hàng chờ, thay vì ở chỗ dựng file. Đừng dựng lại đường ghi Supabase từ
    # file này: nó chạy trong workflow `notify-email.yml` mà workflow đó có thể chạy nhiều
    # lần cho cùng một bản tin.
    print(f"DOCX={out}")


if __name__ == "__main__":
    main()
