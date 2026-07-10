#!/usr/bin/env python3
"""Chèn tin mới vào DATA trong index.html mà không cần đọc toàn bộ file.

Dùng: python3 scripts/add_news.py new_items.json

new_items.json:
{
  "date": "YYYY-MM-DD",
  "worldNews": [ {...}, ... ],
  "usNews": [ {...}, ... ],
  "xNews": [ {...}, ... ],
  "exerciseUpdates": [ {"name": "<tên đúng exercise đã có trong DATA>", "items": [ {...}, ... ]} ],
  "dipEventUpdates": [ {"name": "<tên đúng dipEvent đã có trong DATA>", "items": [ {...}, ... ]} ]
}

- worldNews/usNews: chèn vào ĐẦU mảng, cập nhật generatedAt tương ứng.
- xNews: chèn vào ĐẦU mảng, cập nhật xGeneratedAt.
- exerciseUpdates/dipEventUpdates: tìm entry có "name" khớp CHÍNH XÁC trong
  exercises/dipEvents, chèn "items" vào đầu mảng items con của entry đó.
  Nếu không tìm thấy "name" khớp -> báo lỗi kèm danh sách tên hiện có
  (không tự tạo entry mới để tránh trùng/lệch dữ liệu).
"""
import collections
import json
import pathlib
import sys

NEWS_REQUIRED_FIELDS = {"date", "category", "title", "summary", "sourceName", "sourceUrl", "significance"}
VALID_CATEGORIES = {"Kinh tế", "Chính trị", "Công nghệ quân sự", "Ngoại giao"}
MIN_PER_CATEGORY = 2

X_REQUIRED_FIELDS = {"date", "handle", "name", "title", "summary", "significance", "url"}

EVENT_ITEM_REQUIRED_FIELDS = {"date", "title", "summary", "sourceName", "sourceUrl"}


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


def validate_news_items(items: list, label: str) -> None:
    for idx, item in enumerate(items):
        missing = NEWS_REQUIRED_FIELDS - item.keys()
        if missing:
            raise ValueError(f"{label}[{idx}] thiếu field: {missing}")
        if item["category"] not in VALID_CATEGORIES:
            raise ValueError(f"{label}[{idx}] category không hợp lệ: {item['category']}")
        if not item["sourceUrl"].startswith("http"):
            raise ValueError(f"{label}[{idx}] sourceUrl không hợp lệ: {item['sourceUrl']}")


def validate_x_items(items: list) -> None:
    for idx, item in enumerate(items):
        missing = X_REQUIRED_FIELDS - item.keys()
        if missing:
            raise ValueError(f"xNews[{idx}] thiếu field: {missing}")
        if not item["url"].startswith("http"):
            raise ValueError(f"xNews[{idx}] url không hợp lệ: {item['url']}")


def validate_event_updates(updates: list, label: str) -> None:
    for u_idx, update in enumerate(updates):
        if "name" not in update or "items" not in update:
            raise ValueError(f"{label}[{u_idx}] cần có 'name' và 'items'")
        for idx, item in enumerate(update["items"]):
            missing = EVENT_ITEM_REQUIRED_FIELDS - item.keys()
            if missing:
                raise ValueError(f"{label}[{u_idx}].items[{idx}] thiếu field: {missing}")
            if not item["sourceUrl"].startswith("http"):
                raise ValueError(f"{label}[{u_idx}].items[{idx}] sourceUrl không hợp lệ: {item['sourceUrl']}")


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


def main() -> None:
    if len(sys.argv) != 2:
        print("Dùng: add_news.py <new_items.json>", file=sys.stderr)
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

    validate_news_items(world_new, "worldNews")
    validate_news_items(us_new, "usNews")
    validate_x_items(x_new)
    validate_event_updates(exercise_updates, "exerciseUpdates")
    validate_event_updates(dip_updates, "dipEventUpdates")

    html = html_path.read_text(encoding="utf-8")
    start, end = find_data_span(html)
    data = json.loads(html[start:end])

    data["worldNews"] = world_new + data.get("worldNews", [])
    data["usNews"] = us_new + data.get("usNews", [])
    data["xNews"] = x_new + data.get("xNews", [])

    exercise_items_added = apply_event_updates(data.get("exercises", []), exercise_updates, "exerciseUpdates")
    dip_items_added = apply_event_updates(data.get("dipEvents", []), dip_updates, "dipEventUpdates")

    if date:
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
