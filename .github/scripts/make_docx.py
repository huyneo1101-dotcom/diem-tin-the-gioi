#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tạo file .docx "ĐIỂM TIN NGÀY d.M.yyyy" chứa các tin VỪA QUÉT ĐƯỢC trong lần publish này.
Cách xác định "tin mới của lần quét": diff DATA trong index.html (HEAD) với bản trước
(git show HEAD~1:index.html) — URL nào chưa có ở bản trước là tin của lần quét này.

BÁM CHẶT format bản tin mẫu buổi tối (Diem-tin-ngay-2026-07-23.docx — 5 chủ đề):
  1. Nội bộ Mỹ        -> usNews category "Chính trị", region "Bắc Mỹ" (điều trần + bỏ phiếu)
  2. Úc và Biển Đông  -> worldNews
  3. QS-KHCN          -> mọi usNews còn lại (CNQS Mỹ + Mỹ–Mali) + item tập trận/sự kiện mới
(Đã BỎ mục Mạng xã hội (X) — ngoài phạm vi.)

Định dạng khớp mẫu:
  - Chữ: Times New Roman 14pt toàn bộ.
  - Tiêu đề "ĐIỂM TIN NGÀY d.M.yyyy": căn giữa, đậm, 14pt.
  - Đầu mục "N. <tên>": căn đều (justify), đậm, 14pt.
  - Mỗi tin: MỘT đoạn "- <nội dung>" (summary + significance), căn đều, 14pt, chữ thường
    (không đậm/nghiêng); dòng dưới là link nguồn (hyperlink xanh gạch chân).
  - Lề: trái/phải 1.25 inch, trên/dưới 1.0 inch.
Xuất ra đường dẫn in ở stdout (dòng cuối "DOCX=<path>"). Rỗng (không có tin) -> in "DOCX=".

Chạy: python3 .github/scripts/make_docx.py
"""
import json, subprocess

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.opc.constants import RELATIONSHIP_TYPE as RT

FONT = "Times New Roman"
SIZE = 14  # pt — khớp mẫu


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


def is_noibo_my(it):
    """Nội bộ Mỹ = usNews chính trị trong nước (điều trần/bỏ phiếu). Mali (Châu Phi) KHÔNG tính."""
    return it.get("category") == "Chính trị" and it.get("region") == "Bắc Mỹ"


def build_sections(us, world, events):
    """Chia theo 5 chủ đề, gộp thành 3 mục của bản tin mẫu."""
    sec1 = [it for it in us if is_noibo_my(it)]            # 1. Nội bộ Mỹ
    sec3_us = [it for it in us if not is_noibo_my(it)]     # CNQS Mỹ + Mỹ–Mali
    return [
        ("Nội bộ Mỹ", sec1),
        ("Úc và Biển Đông", list(world)),
        ("QS-KHCN", sec3_us + list(events)),
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
    """Nội dung tin: summary + significance (fallback title nếu thiếu summary)."""
    parts = []
    if it.get("summary"):
        parts.append(it["summary"].strip())
    if it.get("significance"):
        parts.append(it["significance"].strip())
    if not parts and it.get("title"):
        parts.append(it["title"].strip())
    return " ".join(parts)


def add_item(doc, it):
    body = item_body(it)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(2)
    set_font(p.add_run("- " + body), size=SIZE)

    url = it.get("sourceUrl")
    if url:
        pu = doc.add_paragraph()
        pu.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        pu.paragraph_format.space_after = Pt(8)
        add_hyperlink(pu, url, url)


def main():
    with open("index.html", "r", encoding="utf-8") as f:
        cur = extract_data(f.read())
    prev = prev_data()

    us = diff_new(cur, prev, "usNews")
    world = diff_new(cur, prev, "worldNews")
    events = diff_new(cur, prev, "events")
    if not (us or world or events):
        # Fallback: chạy tay / không có tin mới trong commit -> lấy tin đưa lên hôm nay
        us = today_items(cur, "usNews")
        world = today_items(cur, "worldNews")
        events = today_items(cur, "events")

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
        for it in items:
            add_item(doc, it)

    safe = (gen or "diem-tin").replace("/", "-")
    out = f"/tmp/Diem-tin-ngay-{safe}.docx"
    doc.save(out)
    print(f"DOCX={out}")


if __name__ == "__main__":
    main()
