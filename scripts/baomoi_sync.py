#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dong bo danh sach "Bai da luu" tu tai khoan Bao Moi -> baomoi-saved.json.

CHI GIU cac bai thuoc dung 4 chu de cua web tin tuc (Kinh te / Chinh tri /
Cong nghe quan su / Ngoai giao); bo cac bai ngoai chu de (the thao, giai tri,
suc khoe, gia dinh, tam ly...). Cac bai giu lai duoc web TRON THANG vao luong
tin (DATA.worldNews) khi tai trang — khong co tab rieng, khong phan tich so thich.

Chay boi GitHub Action. Doc cookie dang nhap tu bien moi truong BAOMOI_COOKIE.
Endpoint user/get/contents-by-type KHONG kiem tra `sig` (da xac minh) — chi can
cookie hop le. Cookie het han -> API tra err -801 -> script bao loi, khong ghi de.
"""
import gzip
import io
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

API_BASE = "https://w-api.baomoi.com/api/v1/user/get/contents-by-type"
API_KEY = "kI44ARvPwaqL7v0KuDSM0rGORtdY1nnw"
VERSION = "0.8.26"
SIG = "a88b5f86ea991fd566dc12486b55889db9108f47bd475dad83529a25fd1bd0d3"  # khong bi kiem tra
LIST_TYPE_SAVED = 3

# Chi dang len web bai DANG trong 24h gan nhat (yeu cau nguoi dung 22/07/2026).
# Bookmark cu hon van nam trong tai khoan Bao Moi, chi khong duoc dua vao web.
MAX_AGE_HOURS = 24

VN_TZ = timezone(timedelta(hours=7))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- 4 chu de cua web (khop dung tin cua site). Thu tu = uu tien khi hoa. ---
CAT4 = [
    ("Công nghệ quân sự", [
        "tên lửa", "tiêm kích", "chiến đấu cơ", "tàu ngầm", "tàu chiến", "chiến hạm",
        "khu trục", "drone", "uav", "radar", "phòng không", "hải quân", "lục quân",
        "không quân", "vũ khí", "quân sự", "quốc phòng", "xe tăng", "f-22", "f-35",
        "s-400", "patriot", "thaad", "himars", "laser", "vệ tinh", "space force",
        "hạt nhân", "khí tài", "siêu vượt âm", "siêu thanh", "trực thăng", "hạm đội",
        "căn cứ quân sự", "tập trận", "diễn tập", "tàng hình", "đánh chặn",
        "không kích", "tập kích", "tái sử dụng",
    ]),
    ("Ngoại giao", [
        "ngoại giao", "hiệp định", "thượng đỉnh", "hội nghị", "ký kết", "ký thỏa thuận",
        "đàm phán", "đại sứ", "công du", "đối tác chiến lược", "liên minh",
        "tuyên bố chung", "song phương", "đa phương", "hội đàm", "asean",
        "liên hợp quốc", "đối thoại", "địa chính trị", "quan hệ",
    ]),
    ("Kinh tế", [
        "kinh tế", "gdp", "lạm phát", "fed", "lãi suất", "thương mại", "thuế quan",
        "xuất khẩu", "nhập khẩu", "chip", "bán dẫn", "tỷ giá", "ngân hàng", "imf",
        "wto", "oecd", "chứng khoán", "dầu", "dầu mỏ", "diesel", "khí đốt",
        "năng lượng", "đầu tư", "chuỗi cung ứng", "tài chính", "doanh nghiệp",
        "tăng trưởng", "suy thoái", "thị trường", "kiểm soát xuất khẩu",
    ]),
    ("Chính trị", [
        "bầu cử", "quốc hội", "tổng thống", "thủ tướng", "chính phủ", "hiến pháp",
        "biểu tình", "nội các", "trừng phạt", "phe đối lập", "đảo chính", "từ chức",
        "bất ổn", "chính quyền",
    ]),
]

# Khu vuc (tuy chon) — khop theo thu tu uu tien, lay khu vuc dau tien trung.
REGIONS = [
    ("Trung Đông", ["iran", "israel", "syria", "hormuz", "gaza", "ả rập", "saudi",
                     "uae", "yemen", "lebanon", "trung đông", "houthi"]),
    ("Châu Âu/NATO", ["nato", "ukraine", "nga", "châu âu", " eu ", "đức", "pháp",
                       "ba lan", "baltic", "moscow", "kiev", "zelensky"]),
    ("Đông Á", ["trung quốc", "nhật bản", "hàn quốc", "triều tiên", "đài loan",
                "bắc kinh", "đông á", "tokyo"]),
    ("Ấn Độ Dương - Thái Bình Dương", ["asean", "biển đông", "philippines", "ấn độ",
                                        "úc", "australia", "thái bình dương", "việt nam"]),
    ("Châu Mỹ", ["canada", "brazil", "mexico", "argentina", "mỹ latinh", "châu mỹ"]),
]


def build_url(page):
    return (f"{API_BASE}?listType={LIST_TYPE_SAVED}&page={page}&ctime={int(time.time())}"
            f"&version={VERSION}&sig={SIG}&apiKey={API_KEY}")


def fetch(url, cookie):
    req = urllib.request.Request(url, headers={
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"),
        "Accept": "*/*", "Accept-Language": "vi;q=0.9",
        "Referer": "https://baomoi.com/", "Origin": "https://baomoi.com",
        "Accept-Encoding": "gzip", "Cookie": cookie,
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
    return json.loads(raw.decode("utf-8", "replace"))


def classify(title):
    t = title.lower()
    best, best_n = None, 0
    for cat, kws in CAT4:  # thu tu = uu tien tie-break
        n = sum(1 for k in kws if k in t)
        if n > best_n:
            best, best_n = cat, n
    return best


def region_of(title):
    t = " " + title.lower() + " "
    for reg, kws in REGIONS:
        if any(k in t for k in kws):
            return reg
    return ""


def normalize(item):
    """Tra ve tin dang chuan cua web, hoac None neu khong thuoc 4 chu de."""
    title = (item.get("title") or "").strip()
    cat = classify(title)
    if not cat:
        return None
    url_path = item.get("url") or item.get("redirectUrl") or ""
    full_url = ("https://baomoi.com" + url_path) if url_path.startswith("/") else url_path
    ts = item.get("date") or 0
    try:
        date_str = datetime.fromtimestamp(int(ts), VN_TZ).strftime("%Y-%m-%d")
    except (ValueError, OSError, TypeError):
        date_str = ""
    return {
        "date": date_str,
        "category": cat,
        "title": title,
        "summary": "",
        "sourceName": (item.get("publisher") or {}).get("name", "") or "Báo Mới",
        "sourceUrl": full_url,
        "region": region_of(title),
    }


def main():
    cookie = os.environ.get("BAOMOI_COOKIE", "").strip()
    if not cookie:
        print("LOI: thieu bien moi truong BAOMOI_COOKIE (GitHub Secret).", file=sys.stderr)
        return 3

    max_pages = int(os.environ.get("BAOMOI_MAX_PAGES", "40"))
    items, seen, seen_ids = [], set(), set()
    total_raw = 0
    cutoff = int(time.time()) - MAX_AGE_HOURS * 3600
    too_old = 0
    for page in range(1, max_pages + 1):
        try:
            data = fetch(build_url(page), cookie)
        except urllib.error.HTTPError as e:
            print(f"LOI HTTP {e.code} o trang {page}", file=sys.stderr)
            return 4
        except Exception as e:  # noqa
            print(f"LOI mang o trang {page}: {e}", file=sys.stderr)
            return 4

        if data.get("err") == -801 or "đăng nhập" in str(data.get("msg", "")):
            print("LOI: cookie het han / chua dang nhap (err -801). "
                  "Hay bat lai cookie va cap nhat secret BAOMOI_COOKIE.", file=sys.stderr)
            return 2

        raw = (data.get("data") or {}).get("items") or []
        if not raw:
            break
        new_ids = 0
        for it in raw:
            key = it.get("contentId") or it.get("id")
            if key in seen_ids:
                continue
            seen_ids.add(key)
            new_ids += 1
            total_raw += 1
            try:
                ts = int(it.get("date") or 0)
            except (TypeError, ValueError):
                ts = 0
            if ts < cutoff:  # bookmark cu -> khong dua len web
                too_old += 1
                continue
            norm = normalize(it)
            if norm and norm["sourceUrl"] and norm["sourceUrl"] not in seen:
                seen.add(norm["sourceUrl"])
                items.append(norm)
        print(f"trang {page}: +{new_ids} bai (giu {len(items)}/{total_raw} dung chu de)",
              file=sys.stderr)
        if new_ids == 0:
            break
        time.sleep(0.3)

    if total_raw == 0:
        print("CANH BAO: khong lay duoc bai nao. Khong ghi de du lieu cu.", file=sys.stderr)
        return 5

    out = {
        "generatedAt": datetime.now(VN_TZ).strftime("%Y-%m-%dT%H:%M:%S%z"),
        "count": len(items),
        "source": (
            f"Bao Moi - bai da luu (loc dung 4 chu de cua web + chi bai dang trong "
            f"{MAX_AGE_HOURS}h, tu dong qua GitHub Action)"
        ),
        "items": items,
    }
    with open(os.path.join(ROOT, "baomoi-saved.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    from collections import Counter
    dist = Counter(i["category"] for i in items)
    print(
        f"OK: giu {len(items)}/{total_raw} bai (bo {too_old} bai dang qua {MAX_AGE_HOURS}h, "
        f"{total_raw - too_old - len(items)} bai ngoai 4 chu de). Phan bo: {dict(dist)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
