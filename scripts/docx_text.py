#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trích text thô từ file .docx — bóc thẳng `word/document.xml`, KHÔNG cần python-docx.

Dùng cho bot Telegram (`telegram_bot.py`): tin Jay Lâm gửi vào chỉ cần đọc được nội dung để
lưu Supabase, không cần giữ định dạng — bóc XML rẻ hơn cài thêm thư viện chỉ cho một việc đọc.

VÌ SAO PHẢI DÙNG `zipfile`, KHÔNG PHẢI `python-docx`: file .docx là một file zip; nội dung nằm
trong `word/document.xml`. Bóc trực tiếp tránh phụ thuộc thêm gói ngoài trong workflow chạy mỗi
5 phút — `python-docx` chỉ cần cho việc XUẤT file (make_docx.py, gop_tin_jaylam.py), không cần
cho việc ĐỌC ở đây.

Mỗi đoạn `<w:p>` đóng lại thành một dòng — khớp cách người đọc nhìn văn bản Word.
"""
import html
import re
import zipfile


def trich(path, max_chars=20000):
    """Trả text thô của file .docx tại `path`. Hỏng/không đọc được -> chuỗi rỗng."""
    try:
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf-8", errors="replace")
    except Exception:
        return ""
    xml = re.sub(r"</w:p>", "\n", xml)
    xml = re.sub(r"<[^>]+>", "", xml)
    text = html.unescape(xml)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    if max_chars and len(text) > max_chars:
        text = text[:max_chars].rstrip() + "…"
    return text
