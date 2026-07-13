#!/usr/bin/env python3
"""Xóa các tin CŨ không phù hợp sở thích khỏi worldNews/usNews trong index.html.

- CHỈ động vào `worldNews` và `usNews`. KHÔNG đụng `exercises` (tập trận),
  `dipEvents` (ngoại giao), `xNews`, `analyses`... — theo yêu cầu giữ lại tin cũ
  cho tập trận & ngoại giao.
- Nhận danh sách URL cần xóa: 1 URL mỗi dòng trong file (bỏ dòng trống / bắt đầu bằng #).
- Ghi lại DATA theo đúng cách add_news.py (json.dumps compact, splice vào chỗ cũ).

Dùng: python3 scripts/prune_news.py <file_urls.txt>
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "index.html"


def find_data_span(html: str):
    marker = "var DATA = "
    i = html.index(marker) + len(marker)
    start = i
    depth = 0
    while i < len(html):
        c = html[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return start, i + 1
        i += 1
    raise RuntimeError("Không tìm thấy DATA object")


def main():
    if len(sys.argv) < 2:
        print("Dùng: python3 scripts/prune_news.py <file_urls.txt>")
        sys.exit(1)
    urls = set()
    for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            urls.add(line)
    if not urls:
        print("Không có URL nào để xóa.")
        return

    html = HTML.read_text(encoding="utf-8")
    start, end = find_data_span(html)
    data = json.loads(html[start:end])

    removed = []
    for key in ("worldNews", "usNews"):
        arr = data.get(key, [])
        kept = []
        for a in arr:
            u = a.get("sourceUrl", "")
            if u in urls:
                removed.append((key, a.get("date", ""), a.get("title", "")))
            else:
                kept.append(a)
        data[key] = kept

    new_data_str = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    HTML.write_text(html[:start] + new_data_str + html[end:], encoding="utf-8")

    print(f"Đã xóa {len(removed)} tin khỏi worldNews/usNews:")
    for key, d, t in removed:
        print(f"  [{key}] {d} | {t[:70]}")
    matched = {u for u in urls}
    hit_urls = set()
    # báo URL nào không khớp tin nào (để rà soát)
    # (không bắt buộc, chỉ cảnh báo)
    print(f"Tổng URL yêu cầu xóa: {len(urls)} · đã xóa: {len(removed)}")


if __name__ == "__main__":
    main()
