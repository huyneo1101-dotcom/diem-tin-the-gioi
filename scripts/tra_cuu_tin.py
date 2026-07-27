#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trích tin từ DATA ra dạng gọn để làm NGỮ CẢNH cho câu hỏi — không đọc cả index.html.

Dùng:
    python3 scripts/tra_cuu_tin.py --days 3                  # tin 3 ngày gần nhất
    python3 scripts/tra_cuu_tin.py --tim "biển đông" --days 7
    python3 scripts/tra_cuu_tin.py --days 2 --full           # kèm cả `significance`
    python3 scripts/tra_cuu_tin.py --days 3 --max-chars 40000

VÌ SAO CÓ SCRIPT NÀY: `index.html` nặng ~780KB và CLAUDE.md CẤM Read cả file. Bot Telegram
(và bất kỳ phiên nào cần trả lời câu hỏi về tin) cần một lát cắt gọn của DATA — script này
in ra text phẳng, đã lọc theo ngày/từ khoá, cắt trần độ dài để không thổi bay context.

Bao gồm: worldNews · usNews · item của exercises và dipEvents · analyses (think-tank).
Bỏ: rejectedNews (tin đã loại), workCafes (quán cà phê).
"""
import argparse
import datetime
import json
import pathlib
import re
import sys
import unicodedata
import zoneinfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
VN = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")
# Trần mặc định: đủ rộng cho câu hỏi thường gặp, vẫn nhỏ hơn context của một phiên `claude -p`.
DEFAULT_MAX_CHARS = 60000


def load_data():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    i = html.index("var DATA = ") + len("var DATA = ")
    d, j = 0, i
    while True:
        if html[j] == "{":
            d += 1
        elif html[j] == "}":
            d -= 1
            if d == 0:
                break
        j += 1
    return json.loads(html[i:j + 1])


def bo_dau(s: str) -> str:
    """Bỏ dấu tiếng Việt để tìm 'bien dong' cũng khớp 'Biển Đông'."""
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d")


def trong_khung(ngay: str, moc: str) -> bool:
    return bool(ngay) and ngay >= moc


def gom(data, days):
    today = datetime.datetime.now(VN).date()
    moc = (today - datetime.timedelta(days=days)).isoformat()
    ra = []

    for khoa, nhan in (("worldNews", "Thế giới"), ("usNews", "Mỹ")):
        for it in data.get(khoa, []) or []:
            if trong_khung(it.get("date", ""), moc):
                ra.append({
                    "loai": nhan, "ngay": it.get("date", ""),
                    "muc": it.get("category", ""), "vung": it.get("region") or "",
                    "tieu_de": it.get("title", ""), "tom_tat": it.get("summary", ""),
                    "y_nghia": it.get("significance", ""),
                    "nguon": it.get("sourceName", ""), "url": it.get("sourceUrl", ""),
                })

    for khoa, nhan in (("exercises", "Tập trận"), ("dipEvents", "Sự kiện ngoại giao")):
        for ev in data.get(khoa, []) or []:
            for it in ev.get("items", []) or []:
                if trong_khung(it.get("date", ""), moc):
                    ra.append({
                        "loai": nhan, "ngay": it.get("date", ""),
                        "muc": ev.get("name", ""), "vung": ev.get("location") or "",
                        "tieu_de": it.get("title", ""), "tom_tat": it.get("summary", ""),
                        "y_nghia": "",
                        "nguon": it.get("sourceName", ""), "url": it.get("sourceUrl", ""),
                    })

    for it in data.get("analyses", []) or []:
        if trong_khung(it.get("date", ""), moc):
            ra.append({
                "loai": "Think-tank", "ngay": it.get("date", ""),
                "muc": it.get("outlet", ""), "vung": it.get("region") or "",
                "tieu_de": it.get("title", ""), "tom_tat": it.get("summary", ""),
                "y_nghia": it.get("takeaway", ""),
                "nguon": it.get("outlet", ""), "url": it.get("url", ""),
            })

    ra.sort(key=lambda x: x["ngay"], reverse=True)
    return ra


def loc_tu_khoa(items, tu_khoa):
    """Khớp KHÔNG dấu, và mọi từ trong truy vấn đều phải xuất hiện (AND, không phải OR).

    OR làm truy vấn 2 chữ như 'biển đông' khớp mọi bài có chữ 'đông' — thực tế kéo về cả
    tin Đông Á, mùa đông, Đông Nam Á. AND giữ kết quả đúng ý người hỏi.
    """
    tokens = [t for t in bo_dau(tu_khoa).split() if t]
    if not tokens:
        return items
    ra = []
    for it in items:
        kho = bo_dau(" ".join(str(it.get(k, "")) for k in
                             ("tieu_de", "tom_tat", "y_nghia", "muc", "vung", "nguon")))
        if all(t in kho for t in tokens):
            ra.append(it)
    return ra


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=2, help="lùi bao nhiêu ngày (mặc định 2)")
    ap.add_argument("--tim", metavar="TỪ KHOÁ", help="lọc theo từ khoá (không dấu cũng khớp)")
    ap.add_argument("--full", action="store_true", help="in cả phần 'ý nghĩa'")
    ap.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
    ap.add_argument("--json", metavar="PATH", help="ghi ra JSON thay vì in text")
    args = ap.parse_args()

    data = load_data()
    items = gom(data, args.days)
    if args.tim:
        items = loc_tu_khoa(items, args.tim)

    if args.json:
        pathlib.Path(args.json).write_text(
            json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Đã ghi {len(items)} tin ra {args.json}")
        return 0

    today = datetime.datetime.now(VN).date().isoformat()
    dau = [f"NGÀY HÔM NAY (giờ VN): {today}",
           f"BẢN TIN CẬP NHẬT LẦN CUỐI: {data.get('generatedAt', '?')}"
           f" {data.get('generatedTime', '')}",
           f"SỐ TIN TRONG KHUNG {args.days} NGÀY: {len(items)}"
           + (f" (đã lọc từ khoá: {args.tim})" if args.tim else ""), ""]
    print("\n".join(dau))

    tong = sum(len(x) for x in dau)
    da_in = 0
    for it in items:
        khoi = [f"[{it['ngay']}] [{it['loai']}/{it['muc']}] {it['tieu_de']}"]
        if it["tom_tat"]:
            khoi.append(f"   {it['tom_tat']}")
        if args.full and it["y_nghia"]:
            khoi.append(f"   Ý nghĩa: {it['y_nghia']}")
        khoi.append(f"   Nguồn: {it['nguon']} — {it['url']}")
        doan = "\n".join(khoi)
        # Cắt trần để không thổi bay context — nhưng NÓI RA đã cắt bao nhiêu, không im lặng.
        if tong + len(doan) > args.max_chars:
            print(f"\n… (còn {len(items) - da_in} tin nữa, đã cắt cho vừa "
                  f"{args.max_chars} ký tự — thu hẹp --days hoặc thêm --tim để xem tiếp)")
            break
        print(doan)
        tong += len(doan) + 1
        da_in += 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
