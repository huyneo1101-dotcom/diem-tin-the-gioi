#!/usr/bin/env python3
"""Gắn "thông tin nền" (Bối cảnh + Khái niệm) vào các cuộc tập trận trong DATA.exercises.

Web hiển thị 2 thẻ dưới mỗi tập trận: 📔 Bối cảnh (ex.background) + 📚 Khái niệm (ex.concepts).
Nội dung do phiên quét sáng (event-scan) sinh ra khi tạo "file thông tin nền" cho tập trận.

Dùng: python3 scripts/set_exercise_briefing.py briefing.json
briefing.json = [
  {"name":"<khớp đúng name exercise đã có>",
   "background":"Đoạn bối cảnh (có thể nhiều đoạn, ngăn bằng \\n).",
   "concepts":[{"term":"Chuỗi đảo thứ nhất","def":"tuyến đảo Nhật–Đài Loan–Philippines"}, ...]}
]
Chỉ cập nhật exercise có tên KHỚP (bỏ qua tên lạ). In số cuộc đã gắn.
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


def main():
    if len(sys.argv) != 2:
        print("Dùng: set_exercise_briefing.py briefing.json", file=sys.stderr)
        sys.exit(1)
    briefs = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    by_name = {b.get("name"): b for b in briefs if b.get("name")}

    repo = pathlib.Path(__file__).resolve().parent.parent
    html_path = repo / "index.html"
    html = html_path.read_text(encoding="utf-8")
    s, e = find_data_span(html)
    data = json.loads(html[s:e])

    exs = data.get("exercises") or []
    hit = 0
    for ex in exs:
        b = by_name.get(ex.get("name"))
        if not b:
            continue
        if b.get("background"):
            ex["background"] = b["background"]
        if b.get("concepts"):
            ex["concepts"] = [
                {"term": k.get("term", ""), "def": k.get("def", "")}
                for k in b["concepts"] if k and (k.get("term") or k.get("def"))
            ]
        hit += 1

    miss = [n for n in by_name if not any(x.get("name") == n for x in exs)]
    if hit:
        new = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        html_path.write_text(html[:s] + new + html[e:], encoding="utf-8")
    print(f"OK: gắn thông tin nền cho {hit}/{len(exs)} cuộc tập trận."
          + (f" Tên không khớp (bỏ qua): {miss}" if miss else ""))


if __name__ == "__main__":
    main()
