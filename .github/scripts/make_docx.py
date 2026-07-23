#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tạo file .docx "ĐIỂM TIN NGÀY d.M.yyyy" chứa các tin VỪA QUÉT ĐƯỢC trong lần publish này.
Cách xác định "tin mới của lần quét": diff DATA trong index.html (HEAD) với bản trước
(git show HEAD~1:index.html) — URL nào chưa có ở bản trước là tin của lần quét này.

Chia mục theo khu vực (giống bản tin mẫu):
  1. Mỹ           -> usNews
  2. Thế giới     -> worldNews
  3. Mạng xã hội (X) -> xNews
  4. Sự kiện      -> items mới trong exercises + dipEvents

Định dạng mỗi tin khớp ảnh mẫu:
  - Dòng tiêu đề: "- <title>" in NGHIÊNG + ĐẬM
  - Đoạn nội dung: căn đều (justify)
  - Link nguồn: hyperlink xanh gạch chân
Xuất ra đường dẫn in ở stdout (dòng cuối "DOCX=<path>"). Rỗng (không có tin) -> in "DOCX=" (bỏ trống).

Chạy: python3 .github/scripts/make_docx.py
"""
import json, os, subprocess, sys

from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.opc.constants import RELATIONSHIP_TYPE as RT

FONT = "Times New Roman"


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
    """Gom mọi item con của exercises + dipEvents thành list phẳng."""
    items = []
    for grp in ("exercises", "dipEvents"):
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
    """Trả list tin mới (có trong cur, không có trong prev)."""
    if kind == "x":
        cur_list = cur.get("xNews", []) or []
        key = "url"
    elif kind == "events":
        cur_list = event_items(cur)
        key = "sourceUrl"
    else:
        cur_list = cur.get(kind, []) or []  # worldNews / usNews
        key = "sourceUrl"

    if prev is None:
        # Không có bản trước -> fallback: lấy tin đưa lên hôm nay
        today = cur.get("generatedAt")
        return [it for it in cur_list
                if it.get("_addedDate") == today or it.get("date") == today]

    if kind == "x":
        prev_urls = urls_of(prev.get("xNews", []) or [], "url")
    elif kind == "events":
        prev_urls = urls_of(event_items(prev), "sourceUrl")
    else:
        prev_urls = urls_of(prev.get(kind, []) or [], "sourceUrl")

    return [it for it in cur_list if it.get(key) and it.get(key) not in prev_urls]


def today_items(cur, kind):
    """Toàn bộ tin đưa lên hôm nay (fallback khi diff rỗng)."""
    today = cur.get("generatedAt")
    if kind == "x":
        lst = cur.get("xNews", []) or []
    elif kind == "events":
        lst = event_items(cur)
    else:
        lst = cur.get(kind, []) or []
    return [it for it in lst if it.get("_addedDate") == today or it.get("date") == today]


# ---------- docx helpers ----------
def set_font(run, size=13, bold=False, italic=False, color=None):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    if color:
        run.font.color.rgb = color
    # đảm bảo font áp cho cả ký tự tiếng Việt
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
    sz = OxmlElement("w:sz"); sz.set(qn("w:val"), "26"); rpr.append(sz)  # 13pt
    color = OxmlElement("w:color"); color.set(qn("w:val"), "1155CC"); rpr.append(color)
    u = OxmlElement("w:u"); u.set(qn("w:val"), "single"); rpr.append(u)
    r.append(rpr)
    t = OxmlElement("w:t"); t.set(qn("xml:space"), "preserve"); t.text = text
    r.append(t)
    hyperlink.append(r)
    paragraph._p.append(hyperlink)


def item_title(it, kind):
    if kind == "x":
        who = it.get("name") or it.get("handle") or ""
        base = it.get("title") or it.get("summary") or ""
        return f"{base} ({who})" if who else base
    return it.get("title", "")


def item_body(it):
    parts = []
    if it.get("summary"):
        parts.append(it["summary"].strip())
    if it.get("significance"):
        parts.append(it["significance"].strip())
    return " ".join(parts)


def item_url(it, kind):
    return it.get("url") if kind == "x" else it.get("sourceUrl")


def add_item(doc, it, kind):
    # tiêu đề in nghiêng đậm, mở đầu "- "
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run("- " + item_title(it, kind))
    set_font(run, size=13, bold=True, italic=True)

    body = item_body(it)
    if body:
        pb = doc.add_paragraph()
        pb.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        pb.paragraph_format.space_after = Pt(2)
        set_font(pb.add_run(body), size=13)

    url = item_url(it, kind)
    if url:
        pu = doc.add_paragraph()
        pu.paragraph_format.space_after = Pt(8)
        add_hyperlink(pu, url, url)


def main():
    with open("index.html", "r", encoding="utf-8") as f:
        cur = extract_data(f.read())
    prev = prev_data()

    sections = [
        ("Mỹ", diff_new(cur, prev, "usNews"), "usNews"),
        ("Thế giới", diff_new(cur, prev, "worldNews"), "worldNews"),
        ("Mạng xã hội (X)", diff_new(cur, prev, "x"), "x"),
        ("Sự kiện", diff_new(cur, prev, "events"), "events"),
    ]
    total = sum(len(items) for _, items, _ in sections)

    # Fallback: diff rỗng (chạy tay / không có tin mới trong commit) -> lấy toàn bộ tin đưa lên hôm nay
    if total == 0:
        sections = [
            ("Mỹ", today_items(cur, "usNews"), "usNews"),
            ("Thế giới", today_items(cur, "worldNews"), "worldNews"),
            ("Mạng xã hội (X)", today_items(cur, "x"), "x"),
            ("Sự kiện", today_items(cur, "events"), "events"),
        ]
        total = sum(len(items) for _, items, _ in sections)
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
    # tiêu đề căn giữa, đậm
    pt = doc.add_paragraph()
    pt.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pt.paragraph_format.space_after = Pt(10)
    set_font(pt.add_run(f"ĐIỂM TIN NGÀY {title_date}"), size=15, bold=True)

    idx = 0
    for name, items, kind in sections:
        if not items:
            continue
        idx += 1
        ph = doc.add_paragraph()
        ph.paragraph_format.space_before = Pt(6)
        ph.paragraph_format.space_after = Pt(4)
        set_font(ph.add_run(f"{idx}. {name}"), size=14, bold=True)
        for it in items:
            add_item(doc, it, kind)

    safe = (gen or "diem-tin").replace("/", "-")
    out = f"/tmp/Diem-tin-ngay-{safe}.docx"
    doc.save(out)
    print(f"DOCX={out}")


if __name__ == "__main__":
    main()
