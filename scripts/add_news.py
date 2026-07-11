#!/usr/bin/env python3
"""Chèn tin mới vào DATA trong index.html mà không cần đọc toàn bộ file.

Dùng: python3 scripts/add_news.py new_items.json
Hoặc: python3 scripts/add_news.py --recent-titles [N]
      In ra N tiêu đề gần nhất (mặc định 20) của worldNews + usNews + xNews +
      item của exercises/dipEvents, để nhúng vào prompt các agent quét nhằm
      tránh report lại tin/sự kiện đã có. Không ghi file, chỉ đọc.

new_items.json:
{
  "date": "YYYY-MM-DD",
  "worldNews": [ {...}, ... ],
  "usNews": [ {...}, ... ],
  "xNews": [ {...}, ... ],
  "exerciseUpdates": [ {"name": "<tên đúng exercise đã có trong DATA>", "items": [ {...}, ... ]} ],
  "dipEventUpdates": [ {"name": "<tên đúng dipEvent đã có trong DATA>", "items": [ {...}, ... ]} ]
}

Guardrail tự động (chặn = raise lỗi, phải sửa JSON rồi chạy lại; cảnh báo = in ra):
- CHẶN: thiếu field, category sai, sourceUrl/url không hợp lệ, date ngoài khung
  (cũ hơn MAX_AGE_DAYS ngày so với "date" của batch, hoặc ở tương lai),
  URL rác (live-blog / trang chủ), URL trùng nhau trong batch, URL đã có sẵn
  trong DATA, ID bài X vô lý (bịa), tên exercise/dipEvent không khớp.
- CẢNH BÁO: sourceName lạ (ngoài danh sách nguồn đã biết), tiêu đề trùng gần
  giống tin đã có, phần nào chưa đủ chỉ tiêu số lượng.
"""
import collections
import datetime
import json
import pathlib
import re
import sys
import urllib.parse

NEWS_REQUIRED_FIELDS = {"date", "category", "title", "summary", "sourceName", "sourceUrl", "significance"}
VALID_CATEGORIES = {"Kinh tế", "Chính trị", "Công nghệ quân sự", "Ngoại giao"}
MIN_PER_CATEGORY = 2
MAX_AGE_DAYS = 5  # backstop: tin cũ hơn ngần này (so với ngày batch) bị chặn

X_REQUIRED_FIELDS = {"date", "handle", "name", "title", "summary", "significance", "url"}
EVENT_ITEM_REQUIRED_FIELDS = {"date", "title", "summary", "sourceName", "sourceUrl"}

# Nguồn đã biết (chỉ để CẢNH BÁO nếu gặp nguồn lạ, không chặn — nguồn mới hợp lệ vẫn xuất hiện)
KNOWN_SOURCES = {
    # Báo chí
    "Defense News", "Naval News", "Breaking Defense", "Defense One", "SpaceNews", "Task & Purpose",
    "Al Jazeera", "Al Arabiya", "The Straits Times", "The Moscow Times", "South China Morning Post",
    "Politico", "Axios", "The Hindu", "Africanews", "CNBC", "Fortune",
    "VnEconomy", "VnExpress", "Tuổi Trẻ", "Thanh Niên", "Dân Trí", "Báo Mới", "Thế giới & Việt Nam",
    "Reuters", "Kyiv Post", "The Kyiv Independent", "Korea Times", "ANTARA News", "CGTN",
    # Wire + báo chí quốc tế (bổ sung 11/07 từ bộ nguồn chuẩn báo cáo)
    "Associated Press", "AP", "Agence France-Presse", "AFP", "Bloomberg", "Financial Times",
    "Wall Street Journal", "The Economist", "Nikkei Asia", "BBC", "Deutsche Welle", "France 24",
    "The Japan Times", "The Korea Herald", "USNI News", "C4ISRNet", "Army Recognition", "Oryx",
    "The Diplomat", "Foreign Policy", "Foreign Affairs",
    # Nguồn dữ liệu (tầng 2)
    "OECD", "WTO", "BIS", "UNCTAD", "IEA", "SIPRI", "IISS", "Janes",
    # Viện nghiên cứu (tầng 3)
    "CSIS", "RAND", "RUSI", "Chatham House", "CSET", "Brookings", "Carnegie Endowment", "CFR",
    "CNAS", "Atlantic Council", "Lowy Institute", "ASPI", "ISEAS", "RSIS", "ORF", "MERICS",
    "Jamestown Foundation", "ECFR", "Stimson Center", "Hudson Institute",
    # Tổ chức/cơ quan chính thức bổ sung (tầng 1)
    "EEAS", "ASEAN", "Hội đồng Bảo an Liên Hợp Quốc", "DARPA", "CISA", "NIST", "ENISA", "NATO DIANA",
    "Thông tấn xã Việt Nam", "Nhân Dân", "Quân đội Nhân dân",
    # Nguồn chính phủ/chính thức (primary — ưu tiên cao)
    "NATO", "Liên Hợp Quốc", "United Nations", "EU", "Hội đồng châu Âu", "IMF",
    "Nhà Trắng", "The White House", "Bộ Quốc phòng Mỹ", "U.S. Department of Defense",
    "Bộ Ngoại giao Mỹ", "U.S. Department of State", "CENTCOM", "Lực lượng Không gian Mỹ",
    "Fed", "Federal Reserve", "Bộ Quốc phòng Anh", "Chính phủ Anh", "Phủ Tổng thống Ukraine",
    "World Bank", "Ngân hàng Thế giới", "Royal Navy", "Bộ Ngoại giao Nhật Bản",
    "Chính phủ Việt Nam", "Báo Chính phủ", "Bộ Ngoại giao Việt Nam",
    # Truyền thông nhà nước (chỉ dùng cho phát ngôn của chính họ — xem CLAUDE.md)
    "Xinhua", "TASS",
}

# Pattern URL rác: trang live-blog / tổng hợp liên tục (không phải bài viết cố định)
URL_BLOCK_PATTERNS = [
    re.compile(r"/live(?:[-/]|$)", re.I),
    re.compile(r"live-updates", re.I),
    re.compile(r"live-blog|liveblog", re.I),
    re.compile(r"live-news", re.I),
]


def find_data_span(html: str) -> tuple[int, int]:
    marker = "var DATA = "
    start = html.index(marker) + len(marker)
    depth = 0
    in_str = False
    esc = False
    i = start
    while i < len(html):
        c = html[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return start, i + 1
        i += 1
    raise ValueError("Không tìm thấy điểm kết thúc của var DATA")


def parse_date(s: str) -> datetime.date:
    return datetime.date.fromisoformat(s)


def check_date_window(date_str: str, ref: datetime.date, ctx: str) -> None:
    try:
        d = parse_date(date_str)
    except (ValueError, TypeError):
        raise ValueError(f"{ctx}: date không đúng định dạng YYYY-MM-DD: {date_str!r}")
    if d > ref:
        raise ValueError(f"{ctx}: date {date_str} ở TƯƠNG LAI so với ngày batch {ref} — nghi sai/bịa")
    if (ref - d).days > MAX_AGE_DAYS:
        raise ValueError(
            f"{ctx}: date {date_str} cũ hơn {MAX_AGE_DAYS} ngày so với batch {ref} — tin quá cũ, bỏ hoặc thay tin mới hơn"
        )


def check_url_quality(url: str, ctx: str) -> None:
    for pat in URL_BLOCK_PATTERNS:
        if pat.search(url):
            raise ValueError(f"{ctx}: URL có vẻ là trang live-blog/tổng hợp, không phải bài viết cố định: {url}")
    parsed = urllib.parse.urlparse(url)
    if parsed.path.strip("/") == "" and not parsed.query:
        raise ValueError(f"{ctx}: URL chỉ trỏ tới trang chủ, không phải bài viết cụ thể: {url}")


def check_x_id(url: str, ctx: str) -> None:
    m = re.search(r"/status/(\d+)", url)
    if not m:
        raise ValueError(f"{ctx}: url X không có dạng .../status/<id>: {url}")
    sid = m.group(1)
    if len(sid) < 15:
        raise ValueError(f"{ctx}: status ID X quá ngắn ({sid}) — nghi bịa (ID thật ~19 chữ số)")
    if re.search(r"0{5,}$", sid):
        raise ValueError(f"{ctx}: status ID X kết thúc bằng nhiều số 0 ({sid}) — nghi bịa")


def validate_news_items(items: list, label: str, ref: datetime.date) -> None:
    for idx, item in enumerate(items):
        ctx = f"{label}[{idx}]"
        missing = NEWS_REQUIRED_FIELDS - item.keys()
        if missing:
            raise ValueError(f"{ctx} thiếu field: {missing}")
        if item["category"] not in VALID_CATEGORIES:
            raise ValueError(f"{ctx} category không hợp lệ: {item['category']}")
        if not item["sourceUrl"].startswith("http"):
            raise ValueError(f"{ctx} sourceUrl không hợp lệ: {item['sourceUrl']}")
        check_date_window(item["date"], ref, ctx)
        check_url_quality(item["sourceUrl"], ctx)


def validate_x_items(items: list, ref: datetime.date) -> None:
    for idx, item in enumerate(items):
        ctx = f"xNews[{idx}]"
        missing = X_REQUIRED_FIELDS - item.keys()
        if missing:
            raise ValueError(f"{ctx} thiếu field: {missing}")
        if not item["url"].startswith("http"):
            raise ValueError(f"{ctx} url không hợp lệ: {item['url']}")
        check_date_window(item["date"], ref, ctx)
        check_x_id(item["url"], ctx)


def validate_event_updates(updates: list, label: str, ref: datetime.date) -> None:
    for u_idx, update in enumerate(updates):
        if "name" not in update or "items" not in update:
            raise ValueError(f"{label}[{u_idx}] cần có 'name' và 'items'")
        for idx, item in enumerate(update["items"]):
            ctx = f"{label}[{u_idx}].items[{idx}]"
            missing = EVENT_ITEM_REQUIRED_FIELDS - item.keys()
            if missing:
                raise ValueError(f"{ctx} thiếu field: {missing}")
            if not item["sourceUrl"].startswith("http"):
                raise ValueError(f"{ctx} sourceUrl không hợp lệ: {item['sourceUrl']}")
            check_date_window(item["date"], ref, ctx)
            check_url_quality(item["sourceUrl"], ctx)


def iter_new_urls(new_items: dict):
    for label in ("worldNews", "usNews"):
        for idx, it in enumerate(new_items.get(label, [])):
            yield f"{label}[{idx}]", it["sourceUrl"]
    for idx, it in enumerate(new_items.get("xNews", [])):
        yield f"xNews[{idx}]", it["url"]
    for label, key in (("exerciseUpdates", "exerciseUpdates"), ("dipEventUpdates", "dipEventUpdates")):
        for u_idx, upd in enumerate(new_items.get(key, [])):
            for idx, it in enumerate(upd["items"]):
                yield f"{label}[{u_idx}].items[{idx}]", it["sourceUrl"]


def collect_existing_urls(data: dict) -> set:
    urls = set()
    for it in data.get("worldNews", []) + data.get("usNews", []):
        urls.add(it.get("sourceUrl"))
    for it in data.get("xNews", []):
        urls.add(it.get("url"))
    for ev in data.get("exercises", []) + data.get("dipEvents", []):
        for it in ev.get("items", []):
            urls.add(it.get("sourceUrl"))
    return urls


def check_duplicate_urls(new_items: dict, data: dict) -> None:
    existing = collect_existing_urls(data)
    seen = {}
    for ctx, url in iter_new_urls(new_items):
        if url in seen:
            raise ValueError(f"{ctx}: URL trùng với {seen[url]} trong cùng batch: {url}")
        seen[url] = ctx
        if url in existing:
            raise ValueError(f"{ctx}: URL đã có sẵn trong DATA (tin trùng): {url}")


def norm_tokens(title: str) -> set:
    return set(re.sub(r"[^\w\s]", " ", title.lower()).split())


def warn_similar_titles(new_items: dict, data: dict) -> None:
    existing = []
    for it in data.get("worldNews", []) + data.get("usNews", []):
        existing.append(it.get("title", ""))
    for it in data.get("xNews", []):
        existing.append(it.get("title", ""))
    existing_tokens = [(t, norm_tokens(t)) for t in existing if t]

    new_titles = []
    for label in ("worldNews", "usNews", "xNews"):
        for it in new_items.get(label, []):
            new_titles.append(it.get("title", ""))

    for nt in new_titles:
        nts = norm_tokens(nt)
        if not nts:
            continue
        for old, ots in existing_tokens:
            if not ots:
                continue
            jaccard = len(nts & ots) / len(nts | ots)
            if jaccard >= 0.6:
                print(f"  [CẢNH BÁO] tiêu đề nghi trùng (Jaccard {jaccard:.2f}):")
                print(f"      mới: {nt}")
                print(f"      cũ : {old}")
                break


def warn_unknown_sources(new_items: dict) -> None:
    unknown = set()
    for label in ("worldNews", "usNews"):
        for it in new_items.get(label, []):
            if it["sourceName"] not in KNOWN_SOURCES:
                unknown.add(it["sourceName"])
    for key in ("exerciseUpdates", "dipEventUpdates"):
        for upd in new_items.get(key, []):
            for it in upd["items"]:
                if it["sourceName"] not in KNOWN_SOURCES:
                    unknown.add(it["sourceName"])
    if unknown:
        print(f"  [CẢNH BÁO] nguồn lạ ngoài danh sách đã biết (kiểm tra lại độ tin cậy): {', '.join(sorted(unknown))}")


def apply_event_updates(existing_events: list, updates: list, label: str) -> int:
    by_name = {e["name"]: e for e in existing_events}
    added = 0
    for update in updates:
        name = update["name"]
        if name not in by_name:
            available = ", ".join(sorted(by_name.keys()))
            raise ValueError(f"{label}: không tìm thấy '{name}'. Tên hiện có: {available}")
        entry = by_name[name]
        entry["items"] = update["items"] + entry.get("items", [])
        added += len(update["items"])
    return added


def category_report(items: list, label: str) -> bool:
    counts = collections.Counter(item["category"] for item in items)
    ok = True
    print(f"  {label}: {len(items)} tin")
    for cat in sorted(VALID_CATEGORIES):
        n = counts.get(cat, 0)
        flag = "" if n >= MIN_PER_CATEGORY else "  <-- THIẾU (cần >= 2)"
        if n < MIN_PER_CATEGORY:
            ok = False
        print(f"    {cat}: {n}{flag}")
    return ok


def print_recent_titles(html_path: pathlib.Path, n: int) -> None:
    html = html_path.read_text(encoding="utf-8")
    start, end = find_data_span(html)
    data = json.loads(html[start:end])
    for label in ("worldNews", "usNews"):
        items = data.get(label, [])
        print(f"{label} ({min(n, len(items))} gần nhất):")
        for item in items[:n]:
            print(f"  [{item['date']}] {item['title']}")
    xitems = data.get("xNews", [])
    print(f"xNews ({min(n, len(xitems))} gần nhất):")
    for item in xitems[:n]:
        print(f"  [{item['date']}] {item['handle']}: {item['title']}")
    for label in ("exercises", "dipEvents"):
        print(f"{label} — item cập nhật gần nhất mỗi sự kiện:")
        for ev in data.get(label, []):
            recent = ev.get("items", [])[:3]
            titles = "; ".join(it["title"] for it in recent) or "(chưa có item)"
            print(f"  * {ev['name']} [{ev.get('status','?')}]: {titles}")


def main() -> None:
    if len(sys.argv) >= 2 and sys.argv[1] == "--recent-titles":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        repo_root = pathlib.Path(__file__).resolve().parent.parent
        print_recent_titles(repo_root / "index.html", n)
        return

    if len(sys.argv) != 2:
        print("Dùng: add_news.py <new_items.json>  |  add_news.py --recent-titles [N]", file=sys.stderr)
        sys.exit(1)

    repo_root = pathlib.Path(__file__).resolve().parent.parent
    html_path = repo_root / "index.html"
    new_items = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))

    world_new = new_items.get("worldNews", [])
    us_new = new_items.get("usNews", [])
    x_new = new_items.get("xNews", [])
    exercise_updates = new_items.get("exerciseUpdates", [])
    dip_updates = new_items.get("dipEventUpdates", [])
    date = new_items.get("date")

    if not date:
        raise ValueError("new_items.json thiếu 'date' (YYYY-MM-DD của batch) — cần để kiểm tra khung ngày")
    ref = parse_date(date)

    validate_news_items(world_new, "worldNews", ref)
    validate_news_items(us_new, "usNews", ref)
    validate_x_items(x_new, ref)
    validate_event_updates(exercise_updates, "exerciseUpdates", ref)
    validate_event_updates(dip_updates, "dipEventUpdates", ref)

    html = html_path.read_text(encoding="utf-8")
    start, end = find_data_span(html)
    data = json.loads(html[start:end])

    # Cross-check với dữ liệu đang có (chặn URL trùng; cảnh báo tiêu đề gần giống)
    # Phải chạy TRƯỚC khi chèn để so với tin cũ, tránh tự trùng với tin vừa thêm.
    check_duplicate_urls(new_items, data)
    similar_warnings_data = {
        "worldNews": list(data.get("worldNews", [])),
        "usNews": list(data.get("usNews", [])),
        "xNews": list(data.get("xNews", [])),
    }

    data["worldNews"] = world_new + data.get("worldNews", [])
    data["usNews"] = us_new + data.get("usNews", [])
    data["xNews"] = x_new + data.get("xNews", [])

    exercise_items_added = apply_event_updates(data.get("exercises", []), exercise_updates, "exerciseUpdates")
    dip_items_added = apply_event_updates(data.get("dipEvents", []), dip_updates, "dipEventUpdates")

    data["generatedAt"] = date
    if world_new:
        data["worldGeneratedAt"] = date
    if us_new:
        data["usGeneratedAt"] = date
    if x_new:
        data["xGeneratedAt"] = date

    new_data_str = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    html_path.write_text(html[:start] + new_data_str + html[end:], encoding="utf-8")

    print(
        f"OK: +{len(world_new)} tin Thế giới, +{len(us_new)} tin Mỹ, +{len(x_new)} tin X, "
        f"+{exercise_items_added} tin tập trận, +{dip_items_added} tin ngoại giao (sự kiện). generatedAt={date}"
    )
    # Cảnh báo (không chặn)
    warn_unknown_sources(new_items)
    warn_similar_titles(new_items, similar_warnings_data)
    print("Phân bổ category (batch vừa thêm):")
    world_ok = category_report(world_new, "worldNews") if world_new else True
    us_ok = category_report(us_new, "usNews") if us_new else True
    if not (world_ok and us_ok):
        print("=> Còn category thiếu tin (< 2). Nếu đã thử hết nguồn hợp lý, chấp nhận và nêu rõ trong tóm tắt cuối; nếu chưa, quét bổ sung rồi chạy lại script.")
    if len(x_new) < 4:
        print(f"  xNews: {len(x_new)} tin  <-- THIẾU (mục tiêu 4-5)")
    if exercise_items_added < 1:
        print("  exercises: 0 tin cập nhật  <-- THIẾU (mục tiêu 1-2)")
    if dip_items_added < 1:
        print("  dipEvents: 0 tin cập nhật  <-- THIẾU (mục tiêu 1-2)")


if __name__ == "__main__":
    main()
