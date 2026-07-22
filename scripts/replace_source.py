#!/usr/bin/env python3
"""Thay NGUỒN của một tin đã có trong DATA (giữ nguyên vị trí trong mảng).

Dùng khi một tin đang dẫn nguồn tổng hợp tiếng Việt (Báo Mới...) và ta tìm được bài tương
đương từ nguồn nước ngoài uy tín / nguồn chính thức. Chỉ đổi nguồn + nội dung mô tả, KHÔNG
xoá rồi chèn lại — làm vậy tin sẽ nhảy lên đầu mảng và mất thứ tự thời gian.

Dùng: python3 scripts/replace_source.py replacements.json

replacements.json là một mảng, mỗi phần tử:
{
  "oldUrl": "https://baomoi.com/... (bắt buộc — dùng để tìm tin)",
  "sourceName": "Reuters",
  "sourceUrl":  "https://... (bài mới)",
  "date":       "YYYY-MM-DD",            (tuỳ chọn — mặc định giữ ngày cũ)
  "title":      "...",                    (tuỳ chọn)
  "summary":    "...",                    (tuỳ chọn)
  "significance":"...",                   (tuỳ chọn)
  "dropBaomoiFlag": true                  (tuỳ chọn — gỡ cờ _baomoi / nhãn 📌)
}

CHẶN (raise, phải sửa file rồi chạy lại): không tìm thấy `oldUrl`; thiếu `sourceUrl`;
`sourceUrl` mới trùng với một tin KHÁC đã có trong DATA; URL rác (trang chủ/live-blog);
`date` mới ngoài khung cho phép.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from add_news import (  # noqa: E402
    MAX_AGE_DAYS, check_url_quality, collect_existing_urls, find_data_span, parse_date,
)
import datetime  # noqa: E402

SECTIONS = ("worldNews", "usNews")


def main() -> None:
    if len(sys.argv) != 2:
        print("Dùng: replace_source.py <replacements.json>", file=sys.stderr)
        sys.exit(1)

    repo = pathlib.Path(__file__).resolve().parent.parent
    html_path = repo / "index.html"
    reps = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    if isinstance(reps, dict):
        reps = [reps]

    html = html_path.read_text(encoding="utf-8")
    start, end = find_data_span(html)
    data = json.loads(html[start:end])
    existing = collect_existing_urls(data)

    # bản đồ url -> (section, index) để tìm nhanh và biết tin nằm ở đâu
    loc = {}
    for sec in SECTIONS:
        for i, it in enumerate(data.get(sec, [])):
            u = it.get("sourceUrl")
            if u:
                loc[u] = (sec, i)

    today = datetime.date.today()
    done = []
    for idx, r in enumerate(reps):
        ctx = f"replacements[{idx}]"
        old = r.get("oldUrl")
        new = r.get("sourceUrl")
        if not old or not new:
            raise ValueError(f"{ctx}: cần cả 'oldUrl' và 'sourceUrl'")
        if old not in loc:
            raise ValueError(f"{ctx}: KHÔNG tìm thấy tin nào có sourceUrl = {old}")
        check_url_quality(new, ctx)
        if new != old and new in existing:
            raise ValueError(f"{ctx}: sourceUrl mới TRÙNG với tin khác đã có trong DATA: {new}")
        if r.get("date"):
            d = parse_date(r["date"])
            if d > today or (today - d).days > MAX_AGE_DAYS:
                raise ValueError(
                    f"{ctx}: date {r['date']} ngoài khung {MAX_AGE_DAYS + 1} ngày so với hôm nay {today}"
                )

        sec, i = loc[old]
        item = data[sec][i]
        before = {"sourceName": item.get("sourceName"), "sourceUrl": item.get("sourceUrl")}
        for f in ("sourceName", "sourceUrl", "date", "title", "summary", "significance", "region"):
            if r.get(f):
                item[f] = r[f]
        if r.get("dropBaomoiFlag"):
            item.pop("_baomoi", None)
        existing.discard(old)
        existing.add(new)
        loc.pop(old)
        loc[new] = (sec, i)
        done.append((sec, before, item))

    new_data = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    html_path.write_text(html[:start] + new_data + html[end:], encoding="utf-8")

    print(f"OK: đã thay nguồn cho {len(done)} tin.")
    for sec, before, item in done:
        print(f"  [{sec}] {item['title'][:62]}")
        print(f"      {before['sourceName']} → {item['sourceName']}")
        print(f"      {item['sourceUrl']}")


if __name__ == "__main__":
    main()
