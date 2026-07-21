#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quet bai MOI tren Bao Moi theo chuyen muc -> baomoi-topics.json (kho ung vien).

KHAC voi baomoi_sync.py: file kia keo "bai da luu" (bookmark ca nhan, CAN cookie,
nguoi dung tu chon nen dang thang len web). File nay quet chuyen muc cong khai
(KHONG can cookie) de lay bai moi -> chi la KHO UNG VIEN, phien quet se chon loc
theo bo loc so thich roi moi dang.

Trang chuyen muc Bao Moi la Next.js: du lieu bai nam trong <script id="__NEXT_DATA__">,
va moi item co SHAPE GIONG HET item cua API "bai da luu" (contentId/title/date/url/
publisher) -> dung lai classify()/region_of()/normalize() cua baomoi_sync.py.

Chay boi GitHub Action sync-baomoi.yml (cung luc voi baomoi_sync.py).
"""
import gzip
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from baomoi_sync import VN_TZ, ROOT, normalize  # noqa: E402  (dung chung bo phan loai)

# Chuyen muc cong khai da xac minh 22/07/2026 (quan-su / chinh-tri KHONG ton tai -> 404;
# bai quan su nam lan trong the-gioi, bo tu khoa classify() se nhat ra).
TOPICS = ["the-gioi", "kinh-te", "khoa-hoc-cong-nghe"]

MAX_AGE_HOURS = 24  # chi lay bai dang trong 24h gan nhat
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
)


def fetch_html(slug):
    req = urllib.request.Request(
        f"https://baomoi.com/{slug}.epi",
        headers={"User-Agent": UA, "Accept-Encoding": "gzip", "Accept-Language": "vi;q=0.9"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
    return raw.decode("utf-8", "replace")


def extract_items(html):
    """Lay moi object bai viet trong __NEXT_DATA__ (title + url + date unix)."""
    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S)
    if not m:
        return []
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return []
    out = []

    def walk(o):
        if isinstance(o, dict):
            if o.get("title") and o.get("url") and o.get("date"):
                out.append(o)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(data)
    return out


def main():
    cutoff = int(time.time()) - MAX_AGE_HOURS * 3600
    items, seen = [], set()
    stats = {"tong": 0, "qua_cu": 0, "ngoai_chu_de": 0}

    for slug in TOPICS:
        try:
            raw_items = extract_items(fetch_html(slug))
        except urllib.error.HTTPError as e:
            print(f"CANH BAO: chuyen muc {slug} loi HTTP {e.code} — bo qua", file=sys.stderr)
            continue
        except Exception as e:  # noqa
            print(f"CANH BAO: chuyen muc {slug} loi mang: {e} — bo qua", file=sys.stderr)
            continue

        kept = 0
        for it in raw_items:
            stats["tong"] += 1
            try:
                ts = int(it.get("date") or 0)
            except (TypeError, ValueError):
                continue
            if ts < cutoff:
                stats["qua_cu"] += 1
                continue
            norm = normalize(it)  # tra None neu khong thuoc 4 chu de cua web
            if not norm:
                stats["ngoai_chu_de"] += 1
                continue
            url = norm["sourceUrl"].split("#")[0]  # bo duoi "#|index3" cua link chuyen muc
            if not url or url in seen:
                continue
            seen.add(url)
            norm["sourceUrl"] = url
            norm["topic"] = slug
            items.append(norm)
            kept += 1
        print(f"{slug}: {kept} bai giu lai / {len(raw_items)} bai tren trang", file=sys.stderr)
        time.sleep(0.3)

    if stats["tong"] == 0:
        print("LOI: khong doc duoc bai nao tu ca 3 chuyen muc. Khong ghi de du lieu cu.", file=sys.stderr)
        return 5

    items.sort(key=lambda x: x["date"], reverse=True)
    out = {
        "generatedAt": datetime.now(VN_TZ).strftime("%Y-%m-%dT%H:%M:%S%z"),
        "count": len(items),
        "source": f"Bao Moi - quet chuyen muc {', '.join(TOPICS)} (24h gan nhat, loc 4 chu de cua web)",
        "note": "KHO UNG VIEN — phien quet chon loc theo bo loc so thich roi moi dang, khong dang het.",
        "items": items,
    }
    with open(os.path.join(ROOT, "baomoi-topics.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    from collections import Counter

    dist = Counter(i["category"] for i in items)
    print(
        f"OK: {len(items)} ung vien trong 24h (tu {stats['tong']} bai; "
        f"{stats['qua_cu']} qua cu, {stats['ngoai_chu_de']} ngoai chu de). Phan bo: {dict(dist)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
