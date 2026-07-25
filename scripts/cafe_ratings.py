#!/usr/bin/env python3
"""Điền dần RATING GOOGLE cho các quán trong DATA.workCafes (index.html).

Google Maps chặn cào trực tiếp nên rating chỉ lấy được dần qua tìm kiếm/nguồn thứ ba →
routine `cafe-rating-retry` chạy định kỳ, mỗi lần vét thêm phần tra được, tới khi hết quán
thiếu (có thể KHÔNG bao giờ đủ 100% — đây là giới hạn đã biết, không phải lỗi).

Dùng:
  python3 scripts/cafe_ratings.py --missing [out.json]
      In (hoặc ghi) danh sách quán CHƯA có googleRating: [{name,address,mapsUrl}] để giao agent tra.
  python3 scripts/cafe_ratings.py --apply ratings.json
      ratings.json = [{"name":"<khớp đúng name>","googleRating":4.5,"googleReviews":320}, ...]
      CHỈ điền cho quán đang thiếu; bỏ qua name không khớp hoặc thiếu số. In số quán đã điền / còn thiếu.
"""
import json
import pathlib
import sys


def find_data_span(html: str):
    marker = "var DATA = "
    start = html.index(marker) + len(marker)
    depth = 0
    in_str = esc = False
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
    raise ValueError("Không tìm thấy điểm kết thúc var DATA")


def load():
    repo = pathlib.Path(__file__).resolve().parent.parent
    html_path = repo / "index.html"
    html = html_path.read_text(encoding="utf-8")
    s, e = find_data_span(html)
    return html_path, html, s, e, json.loads(html[s:e])


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("--missing", "--apply"):
        print(__doc__)
        sys.exit(1)
    _, html, s, e, data = load()
    cafes = data.get("workCafes") or []

    if sys.argv[1] == "--missing":
        miss = [
            {"name": c.get("name"), "address": c.get("address", ""), "mapsUrl": c.get("mapsUrl", "")}
            for c in cafes if not c.get("googleRating")
        ]
        out = json.dumps(miss, ensure_ascii=False, indent=1)
        if len(sys.argv) > 2:
            pathlib.Path(sys.argv[2]).write_text(out, encoding="utf-8")
            print(f"OK: {len(miss)}/{len(cafes)} quán chưa có rating → ghi {sys.argv[2]}")
        else:
            print(out)
        return

    # --apply
    ratings = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
    by_name = {r.get("name"): r for r in ratings if r.get("name")}
    html_path, html, s, e, data = load()
    cafes = data.get("workCafes") or []
    filled = 0
    for c in cafes:
        if c.get("googleRating"):
            continue
        r = by_name.get(c.get("name"))
        if r and r.get("googleRating"):
            c["googleRating"] = r["googleRating"]
            if r.get("googleReviews"):
                c["googleReviews"] = r["googleReviews"]
            filled += 1
    still = sum(1 for c in cafes if not c.get("googleRating"))
    if filled:
        new = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        html_path.write_text(html[:s] + new + html[e:], encoding="utf-8")
    print(f"OK: điền thêm {filled} rating. Còn thiếu {still}/{len(cafes)} quán.")


if __name__ == "__main__":
    main()
