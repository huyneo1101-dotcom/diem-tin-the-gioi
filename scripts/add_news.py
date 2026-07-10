#!/usr/bin/env python3
"""Chèn tin mới vào DATA trong index.html mà không cần đọc toàn bộ file.

Dùng: python3 scripts/add_news.py new_items.json

new_items.json:
{
  "date": "YYYY-MM-DD",
  "worldNews": [ {...}, ... ],
  "usNews": [ {...}, ... ]
}

Tin mới được chèn vào ĐẦU worldNews/usNews hiện có trong index.html.
generatedAt/worldGeneratedAt/usGeneratedAt được cập nhật theo "date"
(chỉ field nào có tin mới tương ứng mới được cập nhật).
"""
import collections
import json
import pathlib
import sys

REQUIRED_FIELDS = {"date", "category", "title", "summary", "sourceName", "sourceUrl", "significance"}
VALID_CATEGORIES = {"Kinh tế", "Chính trị", "Công nghệ quân sự", "Ngoại giao"}
MIN_PER_CATEGORY = 2


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


def validate_items(items: list, label: str) -> None:
    for idx, item in enumerate(items):
        missing = REQUIRED_FIELDS - item.keys()
        if missing:
            raise ValueError(f"{label}[{idx}] thiếu field: {missing}")
        if item["category"] not in VALID_CATEGORIES:
            raise ValueError(f"{label}[{idx}] category không hợp lệ: {item['category']}")
        if not item["sourceUrl"].startswith("http"):
            raise ValueError(f"{label}[{idx}] sourceUrl không hợp lệ: {item['sourceUrl']}")


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
    date = new_items.get("date")

    validate_items(world_new, "worldNews")
    validate_items(us_new, "usNews")

    html = html_path.read_text(encoding="utf-8")
    start, end = find_data_span(html)
    data = json.loads(html[start:end])

    data["worldNews"] = world_new + data.get("worldNews", [])
    data["usNews"] = us_new + data.get("usNews", [])
    if date:
        data["generatedAt"] = date
        if world_new:
            data["worldGeneratedAt"] = date
        if us_new:
            data["usGeneratedAt"] = date

    new_data_str = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    html_path.write_text(html[:start] + new_data_str + html[end:], encoding="utf-8")

    print(f"OK: +{len(world_new)} tin Thế giới, +{len(us_new)} tin Mỹ. generatedAt={date}")
    print("Phân bổ category (batch vừa thêm):")
    world_ok = category_report(world_new, "worldNews") if world_new else True
    us_ok = category_report(us_new, "usNews") if us_new else True
    if not (world_ok and us_ok):
        print("=> Còn category thiếu tin (< 2). Nếu đã thử hết nguồn hợp lý, chấp nhận và nêu rõ trong tóm tắt cuối; nếu chưa, quét bổ sung rồi chạy lại script.")


if __name__ == "__main__":
    main()
