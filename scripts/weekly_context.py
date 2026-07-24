#!/usr/bin/env python3
"""Trích NGỮ LIỆU cho báo cáo tuần (Mỹ · Trung Quốc · Nga).

Gom tin worldNews + usNews trong 7 ngày gần nhất (theo giờ VN) liên quan tới từng nước,
in ra JSON {weekStart, weekEnd, counts, buckets:{us,cn,ru}}. Agent Opus đọc file này để
tổng hợp thành DATA.weeklyReport (KHÔNG tự bịa nguồn — chỉ dùng url trong đây).

Dùng: python3 scripts/weekly_context.py [--out FILE] [--end YYYY-MM-DD]
  --end : ngày cuối tuần (mặc định hôm nay giờ VN). weekStart = end - 6 ngày.
"""
import datetime
import json
import pathlib
import re
import sys
import zoneinfo

US = re.compile(r"\bmỹ\b|hoa kỳ|washington|nhà trắng|lầu năm góc|pentagon|trump|rubio|hegseth|quốc hội mỹ|hạ viện|thượng viện|\bfed\b|lockheed|boeing|northrop|raytheon|\brtx\b|space force|centcom|ustr|lầu năm", re.I)
CN = re.compile(r"trung quốc|bắc kinh|beijing|tập cận bình|vương nghị|đài loan|biển đông|nhân dân tệ|\bpla\b|hải quân trung|đất hiếm|scarborough|cỏ mây", re.I)
RU = re.compile(r"\bnga\b|moscow|moskva|kremlin|putin|lavrov|ukraine|kiev|kyiv|wagner|zelensky|donbas|belgorod|hắc hải|biển đen", re.I)


def find_data_span(html: str):
    marker = "var DATA = "
    start = html.index(marker) + len(marker)
    depth = in_str = esc = 0
    i = start
    while i < len(html):
        c = html[i]
        if in_str:
            if esc:
                esc = 0
            elif c == "\\":
                esc = 1
            elif c == '"':
                in_str = 0
        else:
            if c == '"':
                in_str = 1
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return start, i + 1
        i += 1
    raise ValueError("Không tìm thấy điểm kết thúc var DATA")


def main() -> None:
    args = sys.argv[1:]
    out_path = None
    end = None
    if "--out" in args:
        out_path = args[args.index("--out") + 1]
    if "--end" in args:
        end = datetime.date.fromisoformat(args[args.index("--end") + 1])
    if end is None:
        end = datetime.datetime.now(zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")).date()
    start = end - datetime.timedelta(days=6)

    repo = pathlib.Path(__file__).resolve().parent.parent
    html = (repo / "index.html").read_text(encoding="utf-8")
    s, e = find_data_span(html)
    data = json.loads(html[s:e])

    def recent(a):
        try:
            return start <= datetime.date.fromisoformat((a.get("date") or "")[:10]) <= end
        except ValueError:
            return False

    def txt(a):
        return " ".join([a.get("title", ""), a.get("summary", ""), a.get("significance", "")])

    pool = (data.get("worldNews") or []) + (data.get("usNews") or [])
    buckets = {"us": [], "cn": [], "ru": []}
    seen = set()
    for a in pool:
        if not recent(a):
            continue
        u = a.get("sourceUrl", "")
        if u in seen:
            continue
        seen.add(u)
        t = txt(a)
        row = {k: a.get(k) for k in ("date", "category", "title", "summary", "significance")}
        row["src"] = a.get("sourceName")
        row["url"] = u
        if US.search(t):
            buckets["us"].append(row)
        if CN.search(t):
            buckets["cn"].append(row)
        if RU.search(t):
            buckets["ru"].append(row)

    out = {
        "weekStart": start.isoformat(),
        "weekEnd": end.isoformat(),
        "counts": {k: len(v) for k, v in buckets.items()},
        "buckets": buckets,
    }
    s_out = json.dumps(out, ensure_ascii=False, indent=1)
    if out_path:
        pathlib.Path(out_path).write_text(s_out, encoding="utf-8")
        print(f"OK: ghi ngữ liệu tuần {start}→{end} vào {out_path} (us={out['counts']['us']}, cn={out['counts']['cn']}, ru={out['counts']['ru']})")
    else:
        print(s_out)


if __name__ == "__main__":
    main()
