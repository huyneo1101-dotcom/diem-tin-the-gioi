#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DÒ API JSON của các viện JS-only — đường vào thứ BA, sau [RSS] và [HTML].

    python3 scripts/do_api_json.py
    python3 scripts/do_api_json.py --chi iiss

VÌ SAO CÓ SCRIPT NÀY (24/08/2026, chỉ thị Huy "thử tìm api json của mấy viện js-only").
Sau bốn vòng dò, phần nguồn còn lại của `WEBSEARCH_ONLY` phần lớn KHÔNG phải bị chặn — chúng
trả 200 với trang 60-800KB, chỉ là danh sách bài do JavaScript dựng sau khi tải, nên `curl`
lấy về cái khung rỗng. Đo được: iiss.org 58-64KB · orfonline.org/research 93KB ·
carnegieendowment.org/research 146KB — cả ba **0 link bài**.

Nhưng "JS dựng danh sách" nghĩa là ở đâu đó có một NGUỒN DỮ LIỆU mà JS ấy đọc. Ba dạng hay gặp,
và dạng đầu thậm chí không cần request thêm:

  (1) NHÚNG SẴN TRONG HTML — Next.js đổ toàn bộ dữ liệu trang vào `<script id="__NEXT_DATA__">`
      dưới dạng JSON. Bài CÓ trong HTML thô, chỉ là nằm trong JSON chứ không phải thẻ <a>, nên
      `html_article_links` (vốn chỉ quét <a href>) không thấy gì. Carnegie chạy Next.js — ghi
      chú 21/08 trong add_analyses.py đã nêu điều đó nhưng chỉ dùng nó để KẾT LUẬN BỎ.
  (2) API REST theo khuôn có sẵn — WordPress `/wp-json/wp/v2/posts`, Drupal `/jsonapi/node/…`.
      Rất nhiều viện chạy hai CMS này.
  (3) API riêng — địa chỉ nằm ngay trong HTML hoặc trong bundle JS (`/api/…`, `…/search?`,
      Algolia, GraphQL).

⚠️ SCRIPT NÀY CHỈ ĐO, KHÔNG KHAI. Nó in ra API nào sống và ra bài gì. Muốn dùng thật thì phải
dựng thêm một lớp `[API]` trong `add_analyses.py` — đó là việc riêng, làm sau khi biết có đáng
làm hay không. Đừng cắm URL API vào `THINKTANK_HTML`: lớp đó parse HTML, không parse JSON.

⚠️ Dùng chung `curl` của `add_analyses.py` (curl TRẦN, đúng công cụ sản xuất) — cùng lý do đã
ghi trong `do_ung_vien_html.py`: đo bằng công cụ khác thì ra kết luận khác.
"""
import argparse
import datetime
import importlib.util
import json
import pathlib
import re
import sys
import urllib.parse

sys.dont_write_bytecode = True
ROOT = pathlib.Path(__file__).resolve().parent.parent


def nap():
    spec = importlib.util.spec_from_file_location("aa_api", ROOT / "scripts" / "add_analyses.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# (tên, trang danh sách). Toàn bộ là nguồn ĐÃ ĐO LÀ JS-only ở các vòng trước — trang trả về
# hàng chục tới hàng trăm KB nhưng 0 link bài. Nguồn trả ~5KB (Cloudflare chặn) KHÔNG đưa vào
# đây: chặn thì API cũng chặn, dò chỉ tốn lượt.
MUC_TIEU = [
    ("IISS", "https://www.iiss.org/online-analysis/"),
    ("ORF [nghiên cứu]", "https://www.orfonline.org/research"),
    ("Carnegie Endowment", "https://carnegieendowment.org/research"),
    ("Carnegie Europe", "https://carnegieendowment.org/europe"),
    ("Takshashila", "https://takshashila.org.in/pages/research"),
    ("NUPI", "https://www.nupi.no/en/publications"),
    ("UI (Thuỵ Điển)", "https://www.ui.se/english/"),
    ("GIGA Hamburg", "https://www.giga-hamburg.de/en/publications"),
    ("EPC (Emirates)", "https://epc.ae/en/publications"),
    ("CEPS", "https://www.ceps.eu/ceps-publications/"),
]

# Khuôn API đoán được từ CMS, thử thẳng không cần đọc HTML.
KHUON = [
    ("WordPress", "/wp-json/wp/v2/posts?per_page=5"),
    ("Drupal JSON:API", "/jsonapi/node/article?page[limit]=5"),
    ("Drupal JSON:API (gốc)", "/jsonapi"),
]

# Địa chỉ trông như API, moi từ HTML thô.
RE_API = re.compile(
    r"""["'(]((?:https?://[^"'()\s]+|/)[^"'()\s]*?"""
    r"""(?:/api/|/wp-json/|/jsonapi|graphql|algolia|/search\?|\.json)[^"'()\s]*)["')]""",
    re.I)

NGAY_KEY = re.compile(r"(date|published|created|updated|pubdate|datetime)", re.I)
TIEU_DE_KEY = re.compile(r"^(title|headline|name|heading)$", re.I)
URL_KEY = re.compile(r"^(url|link|path|slug|href|alias)$", re.I)


def la_ngay(v):
    if not isinstance(v, str) or not (8 <= len(v) <= 40):
        return None
    m = re.search(r"(20\d\d)-(\d\d)-(\d\d)", v)
    if not m:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def moi_bai(obj, sau=0, duong=""):
    """Lùng khắp cây JSON, trả [(đường dẫn trong JSON, tiêu đề, url/slug, ngày)].

    Không đoán trước cấu trúc: mỗi CMS đặt tên trường một kiểu (`title` / `title.rendered` /
    `attributes.title`), nên tìm theo HÌNH DẠNG — dict nào có một trường trông như tiêu đề và
    một trường trông như ngày thì coi là một bài.
    """
    ra = []
    if sau > 8:
        return ra
    if isinstance(obj, dict):
        tieu_de = url = ngay = None
        for k, v in obj.items():
            if isinstance(v, dict) and "rendered" in v:      # WordPress bọc thêm một tầng
                v = v.get("rendered")
            if TIEU_DE_KEY.match(k) and isinstance(v, str) and 15 < len(v) < 250:
                tieu_de = tieu_de or v
            elif URL_KEY.match(k) and isinstance(v, str) and len(v) > 8:
                url = url or v
            elif NGAY_KEY.search(k):
                ngay = ngay or la_ngay(v)
        if tieu_de and ngay:
            ra.append((duong or "<gốc>", tieu_de, url, ngay))
        for k, v in obj.items():
            ra += moi_bai(v, sau + 1, f"{duong}.{k}" if duong else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj[:60]):
            ra += moi_bai(v, sau + 1, f"{duong}[]")
    return ra


def thu_json(mod, url, today, nhan=""):
    """Gọi một URL, nếu ra JSON thì moi bài. Trả dict mô tả, hoặc None nếu không phải JSON."""
    body = mod.curl(url)
    if not body:
        return {"url": url, "nhan": nhan, "ma": "rỗng", "bai": []}
    try:
        data = json.loads(body.decode("utf-8", "replace"))
    except Exception:
        return None
    bai = moi_bai(data)
    # Gộp theo đường dẫn trong JSON: chỗ nào ra nhiều bài nhất chính là danh sách bài.
    theo_duong = {}
    for duong, t, u, d in bai:
        theo_duong.setdefault(duong, []).append((d, t, u))
    tot = max(theo_duong.items(), key=lambda kv: len(kv[1])) if theo_duong else None
    return {
        "url": url, "nhan": nhan, "ma": f"{len(body)//1024}KB", "duong": tot[0] if tot else None,
        "bai": sorted(tot[1], reverse=True) if tot else [],
        "trong_khung": sum(1 for d, _, _ in (tot[1] if tot else [])
                           if d <= today and (today - d).days <= mod.MAX_AGE_DAYS),
    }


def do_mot(mod, ten, trang, today):
    print(f"── {ten}\n   trang: {trang}")
    body = mod.curl(trang).decode("utf-8", "replace")
    print(f"   HTML thô: {len(body)//1024}KB")
    if len(body) < 2000:
        print("   ⛔ trang bị chặn/rỗng — API cũng sẽ chặn, bỏ qua\n")
        return []
    goc = f"{urllib.parse.urlparse(trang).scheme}://{urllib.parse.urlparse(trang).netloc}"
    ket = []

    # (1) __NEXT_DATA__ — dữ liệu nhúng SẴN, không tốn request nào.
    m = re.search(r'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>', body, re.S)
    if m:
        try:
            data = json.loads(m.group(1))
            bai = moi_bai(data)
            theo = {}
            for duong, t, u, d in bai:
                theo.setdefault(duong, []).append((d, t, u))
            tot = max(theo.items(), key=lambda kv: len(kv[1])) if theo else None
            n = len(tot[1]) if tot else 0
            trong = sum(1 for d, _, _ in (tot[1] or []) if d <= today
                        and (today - d).days <= mod.MAX_AGE_DAYS) if tot else 0
            dau = "✅" if trong else ("◻️ " if n else "❌")
            print(f"   {dau} __NEXT_DATA__ nhúng sẵn: {n} bài · {trong} trong khung"
                  + (f" · ở `{tot[0]}`" if tot else ""))
            for d, t, u in (tot[1][:3] if tot else []):
                print(f"        · {d}  {t[:78]}")
                print(f"          {u}")
            bid = data.get("buildId")
            if bid:
                print(f"        buildId={bid} ⇒ có thể gọi /_next/data/{bid}/<đường>.json")
            ket.append(("__NEXT_DATA__", n, trong))
        except Exception as ex:
            print(f"   ❌ __NEXT_DATA__ có nhưng parse hỏng: {type(ex).__name__}")
    else:
        print("   – không có __NEXT_DATA__")

    # (2) khuôn CMS quen thuộc
    for nhan, duoi in KHUON:
        r = thu_json(mod, goc + duoi, today, nhan)
        if r is None:
            continue
        n = len(r["bai"])
        dau = "✅" if r.get("trong_khung") else ("◻️ " if n else "❌")
        print(f"   {dau} {nhan}: {duoi}  [{r['ma']}] {n} bài · {r.get('trong_khung', 0)} trong khung")
        for d, t, u in r["bai"][:2]:
            print(f"        · {d}  {t[:78]}")
        if n:
            ket.append((duoi, n, r.get("trong_khung", 0)))

    # (3) địa chỉ trông như API, moi từ chính HTML
    thay = []
    for mm in RE_API.finditer(body):
        u = mm.group(1)
        if u.startswith("/"):
            u = goc + u
        if urllib.parse.urlparse(u).netloc.replace("www.", "") not in (
                urllib.parse.urlparse(goc).netloc.replace("www.", ""),):
            continue                       # bỏ CDN/analytics bên thứ ba
        if any(u.endswith(e) for e in (".js", ".css", ".png", ".jpg", ".svg", ".woff2")):
            continue
        if u not in thay:
            thay.append(u)
    thay = thay[:6]
    if thay:
        print(f"   ↳ địa chỉ trông như API tìm thấy trong HTML ({len(thay)}):")
        for u in thay:
            r = thu_json(mod, u, today, "từ HTML")
            if r is None:
                print(f"        – {u[:110]}  (không trả JSON)")
                continue
            n = len(r["bai"])
            dau = "✅" if r.get("trong_khung") else ("◻️ " if n else "❌")
            print(f"        {dau} {u[:110]}  [{r['ma']}] {n} bài · {r.get('trong_khung', 0)} trong khung")
            for d, t, _ in r["bai"][:2]:
                print(f"             · {d}  {t[:70]}")
            if n:
                ket.append((u, n, r.get("trong_khung", 0)))
    print()
    return [(ten, *k) for k in ket]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chi")
    a = ap.parse_args()
    mod = nap()
    today = datetime.datetime.now(mod.VN).date()
    print(f"=== DÒ API JSON · {today.isoformat()} (giờ VN) · khung {mod.MAX_AGE_DAYS} ngày ===")
    print("Cột `trong khung` >0 nghĩa là đường này lấy được bài mới NGAY hôm nay.\n")
    tat = []
    for ten, trang in MUC_TIEU:
        if a.chi and a.chi.lower() not in ten.lower() and a.chi.lower() not in trang.lower():
            continue
        tat += do_mot(mod, ten, trang, today)
    print("=== TÓM TẮT — đường ra được bài trong khung ===")
    an = [t for t in tat if t[3]]
    for ten, duong, n, trong in sorted(an, key=lambda x: -x[3]):
        print(f"  {ten:22s} {trong:3d} bài trong khung / {n:3d}  ←  {str(duong)[:80]}")
    if not an:
        print("  (không đường nào ra bài trong khung)")


if __name__ == "__main__":
    main()
