#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dong bo danh sach "Bai da luu" tu tai khoan Bao Moi -> baomoi-saved.json,
va phan tich so thich -> baomoi-analysis.json + baomoi-preferences.md.

Chay boi GitHub Action (moi truong co mang mo). Doc cookie dang nhap tu bien
moi truong BAOMOI_COOKIE (luu trong GitHub Secret, KHONG commit vao repo).

Phat hien tu thuc nghiem (18/07/2026): endpoint user/get/contents-by-type
KHONG kiem tra tham so `sig` — chi can cookie dang nhap hop le. Vi vay script
dung ctime hien tai + mot sig bat ky. Khi cookie het han, API tra
{"err":-801,"msg":"Ban can dang nhap..."} -> script bao loi, KHONG ghi de du lieu cu.
"""
import gzip
import io
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from collections import Counter
from datetime import datetime, timezone, timedelta

API_BASE = "https://w-api.baomoi.com/api/v1/user/get/contents-by-type"
API_KEY = "kI44ARvPwaqL7v0KuDSM0rGORtdY1nnw"
VERSION = "0.8.26"
# sig khong bi kiem tra (da xac minh) — dung 1 gia tri co dinh hop le ve hinh thuc.
SIG = "a88b5f86ea991fd566dc12486b55889db9108f47bd475dad83529a25fd1bd0d3"
LIST_TYPE_SAVED = 3  # 3 = danh sach bai da luu

VN_TZ = timezone(timedelta(hours=7))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- Phan loai chu de theo tu khoa (taxonomy tong quat cho tin da luu ca nhan) ---
# Thu tu = do uu tien khi hoa (nhieu tu khop nhat thang; hoa thi theo thu tu nay).
CATEGORY_KEYWORDS = [
    ("Gia đình & Nuôi dạy con", [
        "cha mẹ", "mẹ chồng", "nàng dâu", "dạy con", "con gái", "con trai", "con yêu",
        "con ghét", "gia đình", "vợ chồng", "hôn nhân", "học thêm", "cha là", "con là",
        "nuôi dạy", "đứa trẻ", "trẻ không muốn", "làm cha", "làm mẹ", "con cái",
    ]),
    ("Tâm lý & Kỹ năng sống", [
        "tâm lý", "dấu hiệu", "thói quen", "tính cách", "người độc hại", "tử tế",
        "độc đoán", "cảm xúc", "trò truyện", "trò chuyện", "sở hữu", "hiện hữu",
        "bản lĩnh", "áp lực", "suy ngẫm", "lựa chọn", "đối mặt", "con bạc", "giúp người",
        "quên đi", "phong cách", "chuyện tình cảm", "trưởng thành", "thấu hiểu",
    ]),
    ("Sức khỏe & Dinh dưỡng", [
        "sức khỏe", "dinh dưỡng", "ăn sáng", "thực phẩm", "dạ dày", "thoái hóa",
        "tuổi thọ", "loại nước", "chế độ ăn", "mất tập trung", "căn bệnh", "giấc ngủ",
        "não", "gan", "tim mạch", "ung thư", "vitamin", "miễn dịch", "uống nước",
    ]),
    ("Thể thao", [
        "bóng đá", "barca", "real madrid", "yamal", "vinicius", "cầu thủ", "ghi bàn",
        "cú đúp", "vô địch", "hlv", "đội tuyển", "áo số", "ngoại hạng", "champions league",
        "world cup", "sea games", "bàn thắng",
    ]),
    ("Giải trí", [
        "sao nữ", "sao nam", "hoa hậu", "diễn viên", "ca sĩ", "bộ phim", "showbiz",
        "nghệ sĩ", "đạo diễn", "cắt cảnh", "thái hòa", "quyền linh", "vóc dáng",
        "khao khát", "lọ lem", "phim điện ảnh", "mv", "concert",
    ]),
    ("Quân sự & Quốc phòng", [
        "tiêm kích", "tên lửa", "quân sự", "không kích", "tập kích", "hải quân",
        "vũ khí", "f-22", "f-35", "nato", "tàu ngầm", "quốc phòng", "chiến dịch",
        "vũ trụ", "tàng hình", "uav", "drone", "tàu chiến", "phòng không", "hạt nhân",
        "chiến hạm", "quân đội", "khí tài",
    ]),
    ("Kinh tế & Năng lượng", [
        "kinh tế", "dầu", "năng lượng", "thương mại", "xuất khẩu", "nhập khẩu", "chip",
        "doanh nghiệp", "lạm phát", "thị trường", "dầu mỏ", "diesel", "tài chính",
        "giá dầu", "đầu tư", "gdp", "lãi suất", "khí đốt", "chứng khoán", "tỷ giá",
        "thuế", "ngân hàng", "chuỗi cung ứng",
    ]),
    ("Ngoại giao & Thế giới", [
        "ngoại giao", "hội nghị", "thượng đỉnh", "asean", "eu", "quan hệ", "đối thoại",
        "hiệp định", "địa chính trị", "liên minh", "trump", "ukraine", "iran", "zelensky",
        "bất ổn", "từ chức", "canada", "liên hợp quốc", "đàm phán", "cấm vận", "trừng phạt",
    ]),
    ("Đời sống & Cảnh giác", [
        "lừa đảo", "cảnh giác", "chiêu trò", "số điện thoại", "nhấc máy", "cuộc gọi",
        "chiếm đoạt", "giả mạo", "bẫy", "mạo danh",
    ]),
]

STOPWORDS = set("""
và của các với cho một những được đã sẽ khi trong ngoài trên dưới về từ đến
là có không tại theo sau trước giữa vì nên mà hay hoặc nhưng cũng vẫn thì này
đó ra vào lên xuống người nước ông bà bị bởi để rằng như vậy tới cùng qua
""".split())


def build_url(list_type, page):
    ctime = int(time.time())
    return (f"{API_BASE}?listType={list_type}&page={page}&ctime={ctime}"
            f"&version={VERSION}&sig={SIG}&apiKey={API_KEY}")


def fetch(url, cookie):
    req = urllib.request.Request(url, headers={
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"),
        "Accept": "*/*",
        "Accept-Language": "vi;q=0.9",
        "Referer": "https://baomoi.com/",
        "Origin": "https://baomoi.com",
        "Accept-Encoding": "gzip",
        "Cookie": cookie,
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
    if raw[:2] == b"\x1f\x8b":  # gzip magic
        raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
    return json.loads(raw.decode("utf-8", "replace"))


def normalize(item):
    url_path = item.get("url") or item.get("redirectUrl") or ""
    full_url = ("https://baomoi.com" + url_path) if url_path.startswith("/") else url_path
    ts = item.get("date") or 0
    try:
        date_str = datetime.fromtimestamp(int(ts), VN_TZ).strftime("%Y-%m-%d")
    except (ValueError, OSError, TypeError):
        date_str = ""
    class_names = item.get("classNames") or ""
    content_types = item.get("contentTypes") or []
    is_video = ("is-video" in class_names) or (2 in content_types)
    title = (item.get("title") or "").strip()
    return {
        "id": item.get("contentId") or item.get("id"),
        "title": title,
        "url": full_url,
        "source": (item.get("publisher") or {}).get("name", ""),
        "date": date_str,
        "ts": int(ts) if ts else 0,
        "thumb": item.get("thumbL") or item.get("thumb") or "",
        "isVideo": is_video,
        "category": classify(title),
    }


def classify(title):
    t = title.lower()
    best, best_n = "Khác", 0
    for cat, kws in CATEGORY_KEYWORDS:  # thu tu = uu tien tie-break
        n = sum(1 for k in kws if k in t)
        if n > best_n:
            best, best_n = cat, n
    return best


def keyphrases(title):
    # Bigram (cum 2 tieng lien tiep) — hop voi tieng Viet da am tiet, tranh tu vun.
    ws = [w for w in re.findall(r"[a-zà-ỹ0-9]+", title.lower()) if len(w) >= 2]
    out = []
    for i in range(len(ws) - 1):
        a, b = ws[i], ws[i + 1]
        if a in STOPWORDS or b in STOPWORDS or a.isdigit() or b.isdigit():
            continue
        out.append(a + " " + b)
    return out


def analyze(items):
    by_cat = Counter(it["category"] for it in items)
    by_source = Counter(it["source"] for it in items if it["source"])
    kw = Counter()
    for it in items:
        kw.update(set(keyphrases(it["title"])))  # set() -> dem theo so bai, khong nhan doi trong 1 tieu de
    total = len(items)

    def pct(n):
        return round(100.0 * n / total, 1) if total else 0.0

    cat_rank = [{"name": c, "count": n, "percent": pct(n)}
                for c, n in by_cat.most_common()]
    src_rank = [{"name": s, "count": n} for s, n in by_source.most_common(15)]
    kw_rank = [{"word": w, "count": n} for w, n in kw.most_common(25) if n >= 2]

    top_cat = cat_rank[0]["name"] if cat_rank else "—"
    summary = (
        f"Trong {total} bài đã lưu, chủ đề nổi bật nhất là \"{top_cat}\" "
        f"({cat_rank[0]['count'] if cat_rank else 0} bài). "
        + "Phân bổ chủ đề: "
        + ", ".join(f"{c['name']} {c['count']}" for c in cat_rank) + ". "
        + ("Nguồn hay lưu nhất: "
           + ", ".join(f"{s['name']} ({s['count']})" for s in src_rank[:5]) + "."
           if src_rank else "")
    )
    return {
        "generatedAt": datetime.now(VN_TZ).strftime("%Y-%m-%dT%H:%M:%S%z"),
        "total": total,
        "byCategory": cat_rank,
        "bySource": src_rank,
        "topKeywords": kw_rank,
        "summary": summary,
    }


def write_markdown(analysis, items):
    lines = ["# Phân tích sở thích từ bài đã lưu (Báo Mới)", ""]
    lines.append(f"_Cập nhật: {analysis['generatedAt']} — tổng {analysis['total']} bài._")
    lines.append("")
    lines.append(analysis["summary"])
    lines.append("")
    lines.append("## Phân bổ theo chủ đề")
    lines.append("| Chủ đề | Số bài | Tỷ lệ |")
    lines.append("|---|---:|---:|")
    for c in analysis["byCategory"]:
        lines.append(f"| {c['name']} | {c['count']} | {c['percent']}% |")
    lines.append("")
    lines.append("## Nguồn hay lưu")
    lines.append("| Nguồn | Số bài |")
    lines.append("|---|---:|")
    for s in analysis["bySource"]:
        lines.append(f"| {s['name']} | {s['count']} |")
    lines.append("")
    if analysis["topKeywords"]:
        lines.append("## Từ khoá lặp lại nhiều")
        lines.append(", ".join(f"{k['word']} ({k['count']})" for k in analysis["topKeywords"]))
        lines.append("")
    return "\n".join(lines)


def main():
    cookie = os.environ.get("BAOMOI_COOKIE", "").strip()
    if not cookie:
        print("LOI: thieu bien moi truong BAOMOI_COOKIE (GitHub Secret).", file=sys.stderr)
        return 3

    max_pages = int(os.environ.get("BAOMOI_MAX_PAGES", "40"))
    all_items, seen = [], set()
    for page in range(1, max_pages + 1):
        url = build_url(LIST_TYPE_SAVED, page)
        try:
            data = fetch(url, cookie)
        except urllib.error.HTTPError as e:
            print(f"LOI HTTP {e.code} o trang {page}", file=sys.stderr)
            return 4
        except Exception as e:  # noqa
            print(f"LOI mang o trang {page}: {e}", file=sys.stderr)
            return 4

        err = data.get("err")
        if err == -801 or "đăng nhập" in str(data.get("msg", "")):
            print("LOI: cookie het han / chua dang nhap (err -801). "
                  "Hay bat lai cookie va cap nhat secret BAOMOI_COOKIE.", file=sys.stderr)
            return 2

        items = (data.get("data") or {}).get("items") or []
        if not items:
            break
        new = 0
        for it in items:
            key = it.get("contentId") or it.get("id")
            if key in seen:
                continue
            seen.add(key)
            all_items.append(normalize(it))
            new += 1
        print(f"trang {page}: +{new} bai (tong {len(all_items)})", file=sys.stderr)
        if new == 0:
            break
        time.sleep(0.3)

    if not all_items:
        print("CANH BAO: khong lay duoc bai nao (danh sach rong?). "
              "Khong ghi de du lieu cu.", file=sys.stderr)
        return 5

    analysis = analyze(all_items)
    saved = {
        "generatedAt": analysis["generatedAt"],
        "count": len(all_items),
        "source": "Bao Moi - bai da luu (tu dong qua GitHub Action)",
        "items": all_items,
    }

    with open(os.path.join(ROOT, "baomoi-saved.json"), "w", encoding="utf-8") as f:
        json.dump(saved, f, ensure_ascii=False, indent=1)
    with open(os.path.join(ROOT, "baomoi-analysis.json"), "w", encoding="utf-8") as f:
        json.dump(analysis, f, ensure_ascii=False, indent=1)
    with open(os.path.join(ROOT, "baomoi-preferences.md"), "w", encoding="utf-8") as f:
        f.write(write_markdown(analysis, all_items))

    print(f"OK: {len(all_items)} bai da luu. Chu de top: {analysis['byCategory'][:1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
