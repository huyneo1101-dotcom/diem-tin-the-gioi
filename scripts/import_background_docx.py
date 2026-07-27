#!/usr/bin/env python3
"""Trích "file thông tin nền" (Word Background vN.docx của quy trình SA BÀN) → briefing.json
để nạp vào web qua set_exercise_briefing.py.

File nền có 2 phần cố định (quy tắc 80 QuanSu):
  PHẦN I  - BỐI CẢNH VÀ CÁC BÊN LIÊN QUAN   → backgroundDoc (trang 📔 Bối cảnh)
  PHẦN II - KHÁI NIỆM VÀ THUẬT NGỮ          → concepts [{term,def}] (trang 📚 Khái niệm)

Heading2 trong Word = tên tiểu mục (PHẦN I) hoặc tên thuật ngữ (PHẦN II).
Dòng "Bản đồ N: ..." là chú thích ảnh — bỏ (web bản text không nhúng ảnh nền).

Dùng:
  python3 scripts/import_background_docx.py "<đường dẫn .docx>" "<tên exercise KHỚP trong DATA>" [out.json]
Mặc định ghi /tmp/briefing_bg.json. Sau đó:
  python3 scripts/set_exercise_briefing.py /tmp/briefing_bg.json
"""
import json
import re
import sys
import zipfile

XML_UNESC = [("&amp;", "&"), ("&quot;", '"'), ("&lt;", "<"), ("&gt;", ">"), ("&apos;", "'")]


def unesc(s):
    for a, b in XML_UNESC:
        s = s.replace(a, b)
    return s


def read_paragraphs(docx_path):
    z = zipfile.ZipFile(docx_path)
    xml = z.read("word/document.xml").decode("utf-8")
    out = []
    for p in re.split(r"</w:p>", xml):
        style_m = re.search(r'w:pStyle w:val="([^"]+)"', p)
        style = style_m.group(1) if style_m else ""
        text = "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", p))
        text = unesc(text).strip()
        if text:
            out.append((style, text))
    return out


def is_map_caption(t):
    return bool(re.match(r"^Bản đồ\s*\d*\s*[:：]", t))


def main():
    if len(sys.argv) < 3:
        print("Dùng: import_background_docx.py <file.docx> <tên exercise> [out.json]", file=sys.stderr)
        sys.exit(1)
    docx_path, ex_name = sys.argv[1], sys.argv[2]
    out_path = sys.argv[3] if len(sys.argv) > 3 else "/tmp/briefing_bg.json"

    paras = read_paragraphs(docx_path)

    # Mốc chia phần: tìm dòng "PHẦN I" và "PHẦN II"
    idx1 = idx2 = None
    for i, (_, t) in enumerate(paras):
        u = t.upper()
        if idx1 is None and u.startswith("PHẦN I") and "PHẦN II" not in u:
            idx1 = i
        elif u.startswith("PHẦN II"):
            idx2 = i
            break
    if idx1 is None or idx2 is None:
        print(f"LỖI: không tìm thấy mốc 'PHẦN I' / 'PHẦN II' trong {docx_path}", file=sys.stderr)
        sys.exit(2)

    # PHẦN I → backgroundDoc (bỏ chính dòng "PHẦN I - ...", giữ Heading2 + đoạn)
    background_doc = []
    for style, t in paras[idx1 + 1:idx2]:
        if is_map_caption(t):
            continue
        background_doc.append({"t": "h" if style.startswith("Heading") else "p", "x": t})

    # PHẦN II → concepts: mỗi Heading2 mở một term, các đoạn sau tới Heading2 kế = def
    concepts = []
    cur = None
    for style, t in paras[idx2 + 1:]:
        if is_map_caption(t):
            continue
        if style.startswith("Heading"):
            if cur:
                concepts.append(cur)
            cur = {"term": t, "def": ""}
        elif cur is not None:
            cur["def"] = (cur["def"] + " " + t).strip() if cur["def"] else t
    if cur:
        concepts.append(cur)

    brief = [{"name": ex_name, "backgroundDoc": background_doc, "concepts": concepts}]
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(brief, f, ensure_ascii=False, indent=1)

    nh = sum(1 for b in background_doc if b["t"] == "h")
    print(f"OK: PHẦN I = {len(background_doc)} khối ({nh} tiểu mục) · PHẦN II = {len(concepts)} khái niệm → {out_path}")


if __name__ == "__main__":
    main()
