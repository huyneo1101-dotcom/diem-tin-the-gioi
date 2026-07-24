#!/usr/bin/env python3
"""Ghi BÁO CÁO TUẦN (Mỹ · Trung Quốc · Nga) vào DATA.weeklyReport trong index.html.

Báo cáo tuần là bài TỔNG HỢP & NHẬN ĐỊNH do agent Opus viết mỗi sáng Chủ nhật (giờ VN),
hiển thị ở tab Phân tích → mục con "Báo cáo tuần". KHÁC với tin chạy hằng ngày: đây là 1
object DUY NHẤT trong DATA (ghi đè bản tuần trước), không phải mảng cộng dồn.

Dùng: python3 scripts/add_weekly.py weekly.json

weekly.json:
{
  "weekStart": "YYYY-MM-DD",          # đầu tuần (thứ Hai)
  "weekEnd":   "YYYY-MM-DD",          # cuối tuần (Chủ nhật = ngày đăng)
  "countries": [
    {
      "key": "us|cn|ru",
      "flag": "🇺🇸",
      "name": "Mỹ",
      "lede": "1-2 câu tổng quan cả tuần của nước này",
      "points": [
        {"title": "Tiêu đề luận điểm",
         "body":  "Đoạn phân tích. Chỗ nhắc tới tin đã có, gắn LINK NỘI DÒNG dạng markdown "
                  "[cụm chữ](https://url-bài-gốc) — web đổi thành chữ xanh gạch chân bấm được.",
         "sources": [ {"name": "Reuters", "url": "https://..."} ]}
      ]
    },
    ... (đủ 3 nước us, cn, ru)
  ]
}

Guardrail (CHẶN = raise, phải sửa JSON rồi chạy lại):
- thiếu weekStart/weekEnd sai định dạng ngày;
- không đủ 3 nước us/cn/ru;
- nước thiếu name/points, hoặc point thiếu title;
- sourceUrl không phải http(s) hoặc là link trang chủ/live-blog.
`generatedAt` script tự đóng dấu = ngày chạy (giờ VN).
"""
import datetime
import json
import pathlib
import re
import sys
import zoneinfo

REQUIRED_KEYS = {"us", "cn", "ru"}
BAD_URL = re.compile(r"/(live|live-blog|live-updates|liveblog)(/|$)", re.I)


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


def die(msg: str) -> None:
    raise SystemExit(f"LỖI: {msg}")


def validate(report: dict) -> None:
    for k in ("weekStart", "weekEnd"):
        v = report.get(k)
        if not v:
            die(f"thiếu '{k}'")
        try:
            datetime.date.fromisoformat(v)
        except ValueError:
            die(f"'{k}'='{v}' không đúng định dạng YYYY-MM-DD")

    countries = report.get("countries") or []
    keys = {c.get("key") for c in countries}
    missing = REQUIRED_KEYS - keys
    if missing:
        die(f"thiếu nước: {', '.join(sorted(missing))} (cần đủ us, cn, ru)")

    for c in countries:
        if not c.get("name"):
            die(f"nước '{c.get('key')}' thiếu 'name'")
        pts = c.get("points") or []
        if not pts:
            die(f"nước '{c.get('name')}' không có 'points' nào")
        for p in pts:
            if not p.get("title"):
                die(f"nước '{c.get('name')}' có point thiếu 'title'")
            for s in p.get("sources") or []:
                u = s.get("url", "")
                if u and (not u.startswith(("http://", "https://")) or BAD_URL.search(u)):
                    die(f"nguồn '{s.get('name')}' url không hợp lệ hoặc là live-blog: {u}")


def main() -> None:
    if len(sys.argv) != 2:
        print("Dùng: add_weekly.py weekly.json", file=sys.stderr)
        sys.exit(1)

    report = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    validate(report)

    now_vn = datetime.datetime.now(zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh"))
    report["generatedAt"] = now_vn.strftime("%Y-%m-%d")
    report["generatedTime"] = now_vn.strftime("%H:%M")

    repo_root = pathlib.Path(__file__).resolve().parent.parent
    html_path = repo_root / "index.html"
    html = html_path.read_text(encoding="utf-8")
    start, end = find_data_span(html)
    data = json.loads(html[start:end])

    data["weeklyReport"] = report
    new_data = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    html_path.write_text(html[:start] + new_data + html[end:], encoding="utf-8")

    npts = sum(len(c.get("points") or []) for c in report["countries"])
    print(
        f"OK: đã ghi báo cáo tuần {report['weekStart']}→{report['weekEnd']} "
        f"({len(report['countries'])} nước, {npts} luận điểm). generatedAt={report['generatedAt']} {report['generatedTime']}"
    )


if __name__ == "__main__":
    main()
