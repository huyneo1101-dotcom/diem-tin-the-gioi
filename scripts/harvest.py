#!/usr/bin/env python3
"""Gom ỨNG VIÊN tin cho 5 chủ đề — chạy TRƯỚC khi giao agent.

Dùng:  python3 scripts/harvest.py                 # cả RSS + Google News
       python3 scripts/harvest.py --rss           # chỉ RSS trong bảng CLAUDE.md
       python3 scripts/harvest.py --gnews         # chỉ Google News
       python3 scripts/harvest.py --json /tmp/ung-vien.json    # ghi thêm ra JSON

VÌ SAO CÓ SCRIPT NÀY (dựng 27/07/2026, chỉ thị Huy "quét sao cho đầy đủ hơn"):
Đo thật trên DATA — 161 nguồn từng đóng góp tin, NHƯNG các nguồn chuyên đúng chủ
đề lại chưa đóng góp bài nào: Long War Journal 0 (Mali), AllAfrica 0 (Sahel),
Philstar/Inquirer 0 (Biển Đông), Lowy + ABC News AU 0 (Úc), gCaptain/Shephard 0.
Nguyên nhân KHÔNG phải nguồn chết — curl từ máy này trả 200 hết. Nguyên nhân là
**WebFetch của subagent bị chặn 403** nên agent rơi về WebSearch và quét tuỳ duyên.
Hậu quả đo được: sáng 27/07 agent Mali kết luận "không có bài mới" trong khi
Google News có 88 item Mali/Sahel trong 48h, gồm tin Bloomberg 26/07 (Liên minh
Sahel tăng quân lên 18.000) — bỏ sót thật.

=> Máy đi lấy, agent đi thẩm định. Script không "quên" nguồn như agent.

HAI LỚP, KHÁC NHAU VỀ ĐỘ TIN CẬY — output ghi rõ:
  [RSS]   có link bài GỐC thật -> agent kiểm nội dung rồi dùng luôn được.
  [GNEWS] Google News RSS chỉ là RADAR phát hiện đề tài: link của nó là link
          redirect news.google.com (KHÔNG resolve được bằng HEAD, nó redirect
          bằng JS) và tiêu đề bị rút gọn. Agent PHẢI tự tìm bài gốc (WebSearch
          theo tiêu đề + tên nguồn) rồi mới nạp. TUYỆT ĐỐI không nạp link
          news.google.com vào DATA.
          Lưu ý điều khoản: feed này Google cấp cho mục đích đọc tin cá nhân —
          ta dùng đúng vai đó (phát hiện đề tài cho bản tin riêng), rồi trích
          dẫn và dẫn link về BÀI GỐC của toà soạn, không tái xuất bản nội dung
          của Google.

KHUNG NGÀY: hôm nay + hôm qua theo giờ VN — khớp đúng `MAX_AGE_DAYS=1` của
`add_news.py` (chỉ thị Huy 27/07: "quét ngày 26 thì chỉ được lấy tin tối đa
ngày 25"). Item ngoài khung bị loại ngay tại đây cho agent đỡ mất công.
"""
import argparse
import datetime
import email.utils
import json
import pathlib
import re
import subprocess
import sys
import urllib.parse
import xml.etree.ElementTree as ET
import zoneinfo

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from topics import match_topic  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
VN = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")

# Google News: mỗi chủ đề một truy vấn. `when:2d` để Google lọc sẵn 2 ngày,
# ta vẫn lọc lại theo pubDate vì "2d" của Google rộng hơn khung của ta.
GNEWS_QUERIES = {
    "Úc & Biển Đông": [
        '"South China Sea" OR Scarborough OR "Second Thomas Shoal" OR "West Philippine Sea"',
        'AUKUS OR "Australian Defence Force" OR "Royal Australian Navy"',
    ],
    "CNQS Mỹ": [
        '"U.S. Air Force" OR "U.S. Navy" OR Pentagon missile OR hypersonic OR "Space Force"',
        '"defense contract" OR "awarded a contract" Pentagon',
    ],
    "Mỹ – Mali": ['Mali OR JNIM OR Sahel OR Bamako OR "Africa Corps"'],
    "Predator's Run": ['"Predator\'s Run"'],
    "Nội bộ Mỹ": [
        '"Senate Armed Services" hearing OR "House Armed Services" markup',
        '"House passes" OR "Senate passes" defense bill OR NDAA',
    ],
}


# Rác hay lọt qua truy vấn Google News — loại thẳng, khỏi tốn mắt agent.
# (Thực tế lần chạy đầu: mục CÁO PHÓ ở thị trấn Scarborough/Maine, 3 bản "Week in review",
#  bài daylight saving time... đều lọt vào danh sách ứng viên.)
NOISE_PATTERNS = [
    "obituary", "funeral home", "week in review", "test your knowledge", "horoscope",
    "daylight saving", "recipe", "box score", "high school", "weather forecast",
    "live updates:", "photos of the week", "crossword",
    # Tên nước làm từ khoá (Mali, Niger, Philippines, Australia) kéo theo cả tin thể thao,
    # hình sự, giải trí — thực tế lọt: bóng đá châu Phi, buôn người sang Mali, "vua giàu
    # nhất châu Phi", đại sứ du lịch Philippines.
    "afcon", "soccer", "football", "world cup", "trafficking", "prostit",
    "tourism ambassador", "beauty pageant", "box office", "celebrity",
]

# Trần số ứng viên in ra MỖI CHỦ ĐỀ. Không có trần thì một chủ đề nóng (Biển Đông hôm
# tàu chìm: 110 bài) sẽ nhấn chìm 4 chủ đề còn lại và ngốn hết context của agent.
PER_TOPIC_CAP = 20

# Nguồn không đủ tư cách làm nguồn tin cho bản tin (mạng xã hội, trang tổng hợp tự động).
# Google News có index cả post Facebook — đã lọt thật ở lần chạy đầu.
NOISE_SOURCES = {"facebook.com", "twitter.com", "x.com", "reddit.com", "youtube.com",
                 "legacy | obituary search", "medium.com"}

# Feed mà MỌI item đều thuộc một chủ đề, bất kể tiêu đề có từ khoá hay không.
# Cần vì tiêu đề của feed hợp đồng Lầu Năm Góc là "Contracts for July 24, 2026" — không chứa
# chữ nào khớp bộ từ khoá, nhưng bên trong là toàn bộ hợp đồng quốc phòng Mỹ ký hôm đó.
FORCE_TOPIC = {
    "DoD Contracts": "CNQS Mỹ",
    "DoD News Releases": "CNQS Mỹ",
}


def norm_title(t: str) -> set:
    return set(re.sub(r"[^\w\s]", " ", t.lower()).split())


def is_noise(title: str) -> bool:
    tl = title.lower()
    return any(p in tl for p in NOISE_PATTERNS)


def same_story(a: str, b: str) -> bool:
    """Hai tiêu đề có phải cùng một sự kiện (nhiều báo đưa lại) — Jaccard thô."""
    sa, sb = norm_title(a), norm_title(b)
    if not sa or not sb:
        return False
    return len(sa & sb) / len(sa | sb) >= 0.5


def curl(url: str, timeout: int = 25) -> bytes:
    p = subprocess.run(
        ["curl", "-sL", "--compressed", "--max-time", str(timeout), "-A", UA, url],
        capture_output=True,
    )
    return p.stdout or b""


def feeds_from_claude_md():
    """Lấy (tên nguồn, url) từ các bảng RSS trong CLAUDE.md — dùng lại cách của rss_check.py.

    Đọc thẳng CLAUDE.md thay vì hardcode: thêm nguồn vào bảng đó là harvest tự quét,
    không phải sửa hai chỗ.
    """
    text = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    try:
        block = text[text.index("## URL RSS"):]
        block = block[: block.index("\n## ", 1)]
    except ValueError:
        print("Không tìm thấy mục '## URL RSS' trong CLAUDE.md", file=sys.stderr)
        return []
    out, seen = [], set()
    for line in block.split("\n"):
        if not line.startswith("|"):
            continue
        clean = re.sub(r"`[^`]*`", "", line)  # bỏ URL cũ đánh dấu SAI trong backtick
        m = re.search(r"https?://\S+", clean)
        if not m:
            continue
        url = m.group(0).rstrip("|").strip()
        name = line.split("|")[1].strip()
        if url in seen:
            continue
        seen.add(url)
        out.append((name, url))
    return out


def parse_date(raw: str):
    if not raw:
        return None
    try:
        return email.utils.parsedate_to_datetime(raw).astimezone(VN).date()
    except Exception:
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            d = datetime.datetime.strptime(raw.strip()[:len("2026-07-27T00:00:00+0000")], fmt)
            if d.tzinfo:
                return d.astimezone(VN).date()
            return d.date()
        except Exception:
            continue
    return None


def items_of(xml_bytes: bytes):
    """Trả [(title, link, pubDate, sourceName)] cho cả RSS 2.0, RDF lẫn Atom."""
    try:
        root = ET.fromstring(xml_bytes)
    except Exception:
        return []
    out = []
    for it in root.iter():
        tag = it.tag.split("}")[-1]
        if tag not in ("item", "entry"):
            continue
        get = lambda n: next(  # noqa: E731
            (c.text for c in it if c.tag.split("}")[-1] == n and c.text), None
        )
        title = get("title") or ""
        link = get("link")
        if not link:  # Atom để link trong attribute
            for c in it:
                if c.tag.split("}")[-1] == "link" and c.attrib.get("href"):
                    link = c.attrib["href"]
                    break
        pub = get("pubDate") or get("published") or get("updated") or get("date")
        src = ""
        for c in it:
            if c.tag.split("}")[-1] == "source":
                src = (c.text or "").strip()
        out.append((title.strip(), (link or "").strip(), pub, src))
    return out


def harvest_rss(window):
    hits = []
    feeds = feeds_from_claude_md()
    print(f"[RSS] quét {len(feeds)} feed từ bảng trong CLAUDE.md...", file=sys.stderr)
    for name, url in feeds:
        forced = FORCE_TOPIC.get(name)
        for title, link, pub, _ in items_of(curl(url)):
            d = parse_date(pub)
            if d is not None and d not in window:
                continue
            topic = forced or match_topic(title, "both")
            if not topic:
                continue
            hits.append({
                "lop": "RSS", "chu_de": topic, "ngay": d.isoformat() if d else "?",
                "tieu_de": title, "nguon": name, "url": link,
            })
    return hits


def harvest_gnews(window):
    hits = []
    n = sum(len(v) for v in GNEWS_QUERIES.values())
    print(f"[GNEWS] chạy {n} truy vấn Google News...", file=sys.stderr)
    for topic, queries in GNEWS_QUERIES.items():
        for q in queries:
            url = ("https://news.google.com/rss/search?q="
                   + urllib.parse.quote(q + " when:2d")
                   + "&hl=en-US&gl=US&ceid=US:en")
            for title, link, pub, src in items_of(curl(url)):
                d = parse_date(pub)
                if d is not None and d not in window:
                    continue
                # Google News gắn " - Tên nguồn" vào cuối tiêu đề -> tách ra cho sạch
                t = title.rsplit(" - ", 1)[0] if " - " in title else title
                # ⚠️ PHẢI lọc lại bằng từ khoá, KHÔNG tin chủ đề của query. Toán tử OR trong
                # query Google rất lỏng: query Biển Đông trả về tai nạn xe buýt ở Scarborough
                # (Toronto), query Quốc hội Mỹ trả về một vụ hành hung ở Đức. Bản đầu gán thẳng
                # chu_de = topic của query nên rác vào sạch.
                if not match_topic(t, "both"):
                    continue
                if src and src.lower() in NOISE_SOURCES:
                    continue
                hits.append({
                    "lop": "GNEWS", "chu_de": topic, "ngay": d.isoformat() if d else "?",
                    "tieu_de": t, "nguon": src or "?", "url": link,
                })
    return hits


def existing_urls_and_titles():
    """URL + tiêu đề đã có trong DATA — để loại ứng viên trùng ngay tại đây."""
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    i = html.index("var DATA = ") + len("var DATA = ")
    d, j = 0, i
    while True:
        if html[j] == "{":
            d += 1
        elif html[j] == "}":
            d -= 1
            if d == 0:
                break
        j += 1
    data = json.loads(html[i:j + 1])
    urls, titles = set(), []
    for k in ("worldNews", "usNews"):
        for it in data.get(k, []) or []:
            if it.get("sourceUrl"):
                urls.add(it["sourceUrl"])
            if it.get("_baomoiUrl"):
                urls.add(it["_baomoiUrl"])
            if it.get("title"):
                titles.append(it["title"].lower())
    for key in ("exercises", "dipEvents"):
        for ev in data.get(key, []) or []:
            for it in ev.get("items", []) or []:
                if it.get("sourceUrl"):
                    urls.add(it["sourceUrl"])
                if it.get("title"):
                    titles.append(it["title"].lower())
    return urls, titles


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rss", action="store_true", help="chỉ quét RSS trong bảng CLAUDE.md")
    ap.add_argument("--gnews", action="store_true", help="chỉ quét Google News")
    ap.add_argument("--json", metavar="PATH", help="ghi kết quả ra file JSON")
    args = ap.parse_args()

    today = datetime.datetime.now(VN).date()
    window = {today, today - datetime.timedelta(days=1)}
    print(f"Khung ngày: {sorted(window)[0]} .. {sorted(window)[1]} (hôm nay + hôm qua, giờ VN)",
          file=sys.stderr)

    hits = []
    if not args.gnews:
        hits += harvest_rss(window)
    if not args.rss:
        hits += harvest_gnews(window)

    urls, titles = existing_urls_and_titles()
    out, seen = [], set()
    bo_rac = bo_trung_data = bo_trung_nhau = 0
    for h in hits:
        if h["url"] in urls or h["url"] in seen:
            continue
        seen.add(h["url"])
        if is_noise(h["tieu_de"]):
            bo_rac += 1
            continue
        # trùng tin ĐÃ CÓ trong DATA
        if any(same_story(h["tieu_de"], t) for t in titles):
            bo_trung_data += 1
            continue
        # trùng nhau trong chính lô ứng viên (nhiều báo đưa cùng 1 sự kiện) -> giữ bản đầu
        if any(x["chu_de"] == h["chu_de"] and same_story(x["tieu_de"], h["tieu_de"]) for x in out):
            bo_trung_nhau += 1
            continue
        out.append(h)

    by_topic = {}
    for h in out:
        by_topic.setdefault(h["chu_de"], []).append(h)

    print(f"\n=== ỨNG VIÊN THEO 5 CHỦ ĐỀ — {len(out)} bài trong khung ngày ===")
    print(f"    (đã lọc: {bo_rac} rác · {bo_trung_data} trùng tin đã có · "
          f"{bo_trung_nhau} bản trùng nhau của cùng sự kiện)")
    for topic in ("Nội bộ Mỹ", "Úc & Biển Đông", "CNQS Mỹ", "Mỹ – Mali", "Predator's Run"):
        lst = by_topic.get(topic, [])
        extra = f" — in {PER_TOPIC_CAP} bài mới nhất" if len(lst) > PER_TOPIC_CAP else ""
        print(f"\n-- {topic} ({len(lst)} bài{extra}) --")
        if not lst:
            print("   (không có ứng viên nào trong khung hôm nay + hôm qua)")
        for h in sorted(lst, key=lambda x: x["ngay"], reverse=True)[:PER_TOPIC_CAP]:
            print(f"   [{h['lop']}][{h['ngay']}] {h['tieu_de'][:105]}")
            print(f"        {h['nguon']} — {h['url'][:120]}")

    print("\n⚠️  [GNEWS] = RADAR, link là redirect news.google.com: PHẢI tự tìm bài gốc "
          "(WebSearch theo tiêu đề + tên nguồn) rồi mới nạp. KHÔNG nạp link news.google.com.")
    print("⚠️  [RSS] có link gốc thật nhưng VẪN phải kiểm nội dung + chống trùng sự kiện trước khi nạp.")
    print("⚠️  NGÀY Ở ĐÂY LÀ NGÀY ĐĂNG BÀI, KHÔNG PHẢI NGÀY SỰ KIỆN. Nhiều trang đăng lại tin cũ")
    print("    với pubDate mới — thực tế 27/07: 'US House passes $1.15 trillion defence bill' hiện")
    print("    ngày 26/07 nhưng cuộc bỏ phiếu 216-212 diễn ra 22/07, tức NGOÀI khung; tin Patriot")
    print("    PAC-2 trên Báo Mới cũng vậy (đăng 26/07, sự kiện 23/07). Trước khi nạp phải đọc bài")
    print("    và neo `date` theo NGÀY SỰ KIỆN — ngoài khung hôm nay + hôm qua thì BỎ.")

    if args.json:
        pathlib.Path(args.json).write_text(
            json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nĐã ghi {len(out)} ứng viên ra {args.json}")


if __name__ == "__main__":
    main()
