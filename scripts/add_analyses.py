#!/usr/bin/env python3
"""Nạp BÀI PHÂN TÍCH THINK-TANK vào DATA.analyses trong index.html.

Vì sao có file này (dựng 27/07/2026 — chỉ thị Huy: *"quét tin buổi sáng nhớ quét thêm cả
các bài từ think-tank"*): web ĐÃ có sẵn tab 🧠 Phân tích → mục con 🏛️ Think-tank đọc
`DATA.analyses`, nhưng TRƯỚC file này KHÔNG có script nào ghi vào mảng đó — chỉ có
`prune_news.py` xoá. Hệ quả: mục Think-tank đứng im từ 09/07/2026, bài mới nhất 18 ngày
tuổi, trong khi bảng nguồn tầng 3 trong CLAUDE.md liệt kê hơn 30 viện nghiên cứu.
Không có đường nạp thì mục chết là tất yếu, không phải do quên.

KHÁC `add_news.py`: đây KHÔNG phải tin thời sự. Bài viện nghiên cứu đăng thưa (một viện
ra 1–3 bài/tuần) và không "ôi" sau 24h, nên khung ngày nới thành MAX_AGE_DAYS = 7 thay vì
1. Đổi lại, `outlet` bị SIẾT: phải là viện nghiên cứu thật (kiểm theo DOMAIN của url, xem
THINKTANK_DOMAINS) — mục tên là "Think-tank" mà lọt bài Al Jazeera/Naval News thì hỏng
chính danh nghĩa của mục (18 bài cũ trong DATA có lẫn như vậy, đó là dữ liệu đời trước).

Dùng:
  python3 scripts/add_analyses.py --candidates      # LIỆT KÊ ứng viên từ RSS 13 viện (bước 1)
  python3 scripts/add_analyses.py /tmp/analyses.json # NẠP bài đã chọn + dịch (bước 2)

/tmp/analyses.json:
{
  "date": "YYYY-MM-DD",              # ngày neo lô (mặc định: hôm nay giờ VN)
  "analyses": [
    {
      "date":     "YYYY-MM-DD",      # ngày ĐĂNG bài
      "outlet":   "CSIS",            # tên viện — hiện trên web
      "author":   "Tên tác giả",     # có thể để "" nếu bài không ghi
      "title":    "Tiêu đề dịch sang tiếng Việt",
      "summary":  "2-3 câu bài viết nói gì",
      "takeaway": "1-2 câu: điều rút ra / vì sao đáng đọc",
      "topic":    "Răn đe hạt nhân", # nhãn ngắn, hiện thành badge
      "region":   "Đông Á",          # tuỳ chọn, xem VALID_REGIONS
      "url":      "https://www.csis.org/analysis/..."
    }
  ]
}

Guardrail CHẶN (raise, phải sửa JSON rồi chạy lại):
- thiếu field bắt buộc (date/outlet/title/summary/takeaway/url);
- `date` sai định dạng, ở TƯƠNG LAI, hoặc cũ hơn MAX_AGE_DAYS ngày — kiểm HAI LỚP như
  add_news.py: so với `date` của lô VÀ so với hôm nay theo giờ VN thật (bịt đường neo lô
  về ngày cũ để nhét bài cổ);
- `url` không http(s), là trang chủ, hoặc trỏ live-blog;
- `url` trùng nhau trong lô, hoặc đã có trong DATA (bất kỳ mảng nào — kể cả đã nạp làm tin
  thường ở worldNews/usNews, tránh một bài nằm 2 chỗ);
- domain của `url` không thuộc THINKTANK_DOMAINS.

CẢNH BÁO (in ra, không chặn): `region` ngoài danh sách; tiêu đề nghi trùng bài đã có
(Jaccard ≥ 0.6).

Gặp lỗi "domain không phải think-tank": đây KHÔNG phải lỗi để lách bằng cách đổi url.
Bài không phải của viện nghiên cứu thì BỎ (đưa vào bản tin thường nếu là tin). Nếu đúng là
viện nghiên cứu thật mà chưa có trong danh sách → thêm domain vào THINKTANK_DOMAINS.
"""
import datetime
import email.utils
import json
import pathlib
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
import zoneinfo

VN = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")

# Bài viện nghiên cứu đăng thưa và giữ giá trị lâu hơn tin thời sự -> khung rộng hơn
# MAX_AGE_DAYS=1 của add_news.py. 7 ngày = vừa đủ để phiên sáng nhặt được bài ra cuối
# tuần trước mà không biến mục thành kho lưu trữ bài cũ.
MAX_AGE_DAYS = 7

REQUIRED_FIELDS = {"date", "outlet", "title", "summary", "takeaway", "url"}

VALID_REGIONS = {
    "Châu Âu/NATO", "Trung Đông", "Đông Á", "Toàn cầu", "Châu Mỹ",
    "Ấn Độ Dương - Thái Bình Dương", "Châu Phi", "Nam Á",
}

# Domain của viện nghiên cứu (tầng 3 trong CLAUDE.md) + vài nơi xuất bản nghiên cứu chiến
# lược tương đương. Kiểm theo DOMAIN chứ không theo tên `outlet` vì tên viết mỗi lúc một
# kiểu ("CSIS" / "Center for Strategic and International Studies" / "CSIS ChinaPower").
THINKTANK_DOMAINS = {
    # Mỹ
    "csis.org", "amti.csis.org", "chinapower.csis.org", "rand.org", "brookings.edu",
    "carnegieendowment.org", "carnegieeurope.eu", "cfr.org", "foreignaffairs.com",
    "cnas.org", "atlanticcouncil.org", "stimson.org", "hudson.org", "csbaonline.org",
    "belfercenter.org", "cset.georgetown.edu", "wilsoncenter.org", "usip.org",
    "heritage.org", "aei.org", "cato.org", "piie.com", "fpri.org", "gmfus.org",
    "defensepriorities.org", "longwarjournal.org", "fdd.org", "38north.org",
    "warontherocks.com", "nbr.org", "jamestown.org",
    # Anh / châu Âu
    "rusi.org", "chathamhouse.org", "iiss.org", "ecfr.eu", "swp-berlin.org",
    "ifri.org", "clingendael.org", "egmontinstitute.be", "realinstitutoelcano.org",
    "ispionline.it", "ui.se", "nupi.no", "prif.org", "giga-hamburg.de", "pism.pl",
    "icds.ee", "fiia.fi",
    # Ấn Độ Dương - Thái Bình Dương
    "lowyinstitute.org", "aspi.org.au", "aspistrategist.org.au", "iseas.edu.sg",
    "rsis.edu.sg", "orfonline.org", "merics.org", "eastasiaforum.org",
    # Trung Đông / châu Phi
    "inss.org.il", "issafrica.org", "crisisgroup.org",
    # Dữ liệu (tầng 2) nhưng xuất bản phân tích
    "sipri.org",
}

BAD_URL = re.compile(r"/(live|live-blog|live-updates|liveblog)(/|$)", re.I)

# RSS của các viện — VERIFY BẰNG FETCH THẬT 27/07/2026 (curl có UA + --compressed).
# ⚠️ Phải kèm cả hai cờ đó: War on the Rocks trả 403 khi curl trần (CLAUDE.md từng chấm
# "BỎ HẲN" vì vậy), nhưng có UA thì trả 100 item bình thường.
THINKTANK_FEEDS = [
    ("Atlantic Council", "https://www.atlanticcouncil.org/feed/"),
    ("Lowy Institute", "https://www.lowyinstitute.org/the-interpreter/rss.xml"),
    ("ASPI", "https://www.aspistrategist.org.au/feed/"),
    ("War on the Rocks", "https://warontherocks.com/feed/"),
    ("Jamestown Foundation", "https://jamestown.org/feed/"),
    ("Long War Journal", "https://www.longwarjournal.org/feed"),
    ("RAND", "https://www.rand.org/blog.xml"),
    ("MERICS", "https://merics.org/en/rss"),
    ("CSET", "https://cset.georgetown.edu/feed/"),
    ("Hudson Institute", "https://www.hudson.org/rss.xml"),
    ("Heritage Foundation", "https://www.heritage.org/rss"),
    ("AMTI/CSIS", "https://amti.csis.org/feed/"),
    ("Crisis Group", "https://www.crisisgroup.org/rss.xml"),
]

# KHÔNG có RSS dùng được (kiểm 27/07/2026 — đã thử 2 biến thể URL mỗi nơi, ĐỪNG thử lại):
#   Brookings · RUSI · Chatham House · ORF · CNAS · FPRI — trả HTML thay vì XML;
#   38 North · Stimson — Cloudflare "Just a moment"; USIP — 404;
#   Carnegie · Belfer · Wilson Center — XML hợp lệ nhưng 0 item.
#   CSIS (csis.org) — feed bỏ hoang từ 2016 (xem CLAUDE.md).
# Muốn bài của mấy nơi này thì dùng WebSearch `site:<domain>`, đừng chờ RSS.
# Đường dẫn KHÔNG phải bài phân tích, tuy nằm chung feed. Không lọc thì mục Think-tank đầy
# mẩu "chuyên gia X được Coindesk trích dẫn" — Atlantic Council đẩy cả chuyên mục
# /insight-impact/in-the-news/ vào feed (thực tế 33 bài/7 ngày thì 8 là loại này).
NOISE_PATHS = (
    "/in-the-news/", "/insight-impact/", "/press-release", "/media-advisory",
    "/event/", "/events/", "/podcast", "/newsletter", "/webinar", "/transcript",
)

WEBSEARCH_ONLY = [
    "csis.org", "brookings.edu", "rusi.org", "chathamhouse.org", "orfonline.org",
    "cnas.org", "38north.org", "stimson.org", "carnegieendowment.org", "fpri.org",
    "belfercenter.org", "wilsoncenter.org", "usip.org", "iiss.org",
]


def die(msg: str) -> None:
    raise SystemExit(f"LỖI: {msg}")


def find_data_span(html: str) -> tuple[int, int]:
    """Định vị object JSON của `var DATA = {...}` (bỏ qua ngoặc nằm trong chuỗi)."""
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


def domain_of(url: str) -> str:
    m = re.match(r"https?://([^/]+)", url.strip(), re.I)
    if not m:
        return ""
    # removeprefix chứ KHÔNG lstrip("www."): lstrip loại theo TẬP ký tự nên
    # "www.wilsoncenter.org" thành "ilsoncenter.org" (mất luôn chữ w đầu tên viện).
    host = m.group(1).lower().split(":")[0]
    return host.removeprefix("www.")


def is_thinktank(url: str) -> bool:
    """Domain (hoặc domain cha) có nằm trong danh sách viện nghiên cứu không."""
    host = domain_of(url)
    if not host:
        return False
    parts = host.split(".")
    for i in range(len(parts) - 1):
        if ".".join(parts[i:]) in THINKTANK_DOMAINS:
            return True
    return False


def is_homepage(url: str) -> bool:
    """URL trỏ trang chủ/trang mục thay vì một bài cụ thể."""
    m = re.match(r"https?://[^/]+(/.*)?$", url.strip(), re.I)
    if not m:
        return True
    path = (m.group(1) or "/").rstrip("/")
    return path in ("", "/") or len(path.strip("/").split("/")) < 2 and not re.search(r"[-_]\w+[-_]", path)


def norm_title(t: str) -> set:
    return set(re.sub(r"[^\w\s]", " ", t.lower()).split())


def jaccard(a: str, b: str) -> float:
    sa, sb = norm_title(a), norm_title(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def collect_existing_urls(data: dict) -> set:
    """Mọi URL đã có trong DATA — để một bài không nằm 2 chỗ (analyses + worldNews)."""
    urls = set()
    for key in ("analyses", "worldNews", "usNews", "xNews", "rejectedNews"):
        for it in data.get(key) or []:
            for f in ("url", "sourceUrl", "_baomoiUrl"):
                if it.get(f):
                    urls.add(it[f].strip())
    for key in ("exercises", "dipEvents"):
        for ev in data.get(key) or []:
            for it in ev.get("items") or []:
                if it.get("sourceUrl"):
                    urls.add(it["sourceUrl"].strip())
    return urls


def check_date(item_date: str, batch_date: datetime.date, today_vn: datetime.date) -> None:
    """Khung ngày kiểm HAI LỚP: so với ngày lô VÀ so với hôm nay thật (giờ VN).

    Lớp thứ hai bịt đường "neo lô về ngày cũ để nhét bài cổ" — đúng lỗ hổng đã cho 3 tin
    ngày 24/07 lọt vào bản tin 26/07 bên add_news.py.
    """
    try:
        d = datetime.date.fromisoformat(item_date)
    except ValueError:
        die(f"date='{item_date}' không đúng định dạng YYYY-MM-DD")
    if d > batch_date:
        die(f"date='{item_date}' ở TƯƠNG LAI so với ngày lô {batch_date.isoformat()}")
    if (batch_date - d).days > MAX_AGE_DAYS:
        die(f"date='{item_date}' cũ hơn {MAX_AGE_DAYS} ngày so với ngày lô {batch_date.isoformat()} — BỎ bài này")
    if (today_vn - d).days > MAX_AGE_DAYS:
        die(
            f"date='{item_date}' cũ hơn {MAX_AGE_DAYS} ngày so với HÔM NAY ({today_vn.isoformat()}, giờ VN) "
            f"— BỎ bài, ĐỪNG lùi ngày lô để lách"
        )


def curl(url: str) -> bytes:
    UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
    try:
        r = subprocess.run(
            ["curl", "-sL", "--compressed", "--max-time", "20", "-A", UA, url],
            capture_output=True,
        )
        return r.stdout
    except Exception:
        return b""


def feed_items(xml_bytes: bytes):
    """[(title, link, ngày)] cho cả RSS 2.0, RDF lẫn Atom."""
    try:
        root = ET.fromstring(xml_bytes)
    except Exception:
        return []
    out = []
    for it in root.iter():
        if it.tag.split("}")[-1] not in ("item", "entry"):
            continue
        title = link = None
        pub = None
        for c in it:
            tag = c.tag.split("}")[-1]
            if tag == "title" and c.text:
                title = c.text.strip()
            elif tag == "link":
                link = (c.text or c.attrib.get("href") or "").strip()
            elif tag in ("pubDate", "published", "updated", "date") and c.text and not pub:
                pub = c.text.strip()
        if title and link:
            out.append((title, link, parse_feed_date(pub)))
    return out


def parse_feed_date(raw):
    if not raw:
        return None
    try:
        return email.utils.parsedate_to_datetime(raw).astimezone(VN).date()
    except Exception:
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            d = datetime.datetime.strptime(raw[:25], fmt)
            return d.astimezone(VN).date() if d.tzinfo else d.date()
        except Exception:
            continue
    return None


def list_candidates() -> None:
    """In ứng viên think-tank trong khung MAX_AGE_DAYS, đã bỏ bài đã có trong DATA.

    Đây là bước 1 của phiên sáng: agent đọc danh sách này rồi CHỌN bài đáng đưa, mở đọc,
    dịch tiêu đề + viết summary/takeaway tiếng Việt. Không nạp thẳng từ đây — tiêu đề RSS
    là tiếng Anh và chưa có `takeaway`, hai thứ guardrail bắt buộc.
    """
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    html = (repo_root / "index.html").read_text(encoding="utf-8")
    start, end = find_data_span(html)
    data = json.loads(html[start:end])
    existing = collect_existing_urls(data)

    today_vn = datetime.datetime.now(VN).date()
    total = 0
    print(f"=== ỨNG VIÊN THINK-TANK (đăng trong {MAX_AGE_DAYS} ngày, tính tới {today_vn.isoformat()}) ===")
    for name, url in THINKTANK_FEEDS:
        rows = []
        for title, link, d in feed_items(curl(url)):
            if d is None or (today_vn - d).days > MAX_AGE_DAYS or d > today_vn:
                continue
            if link.split("?")[0] in existing or link in existing:
                continue
            if any(p in link.lower() for p in NOISE_PATHS):
                continue
            rows.append((d, title, link))
        if not rows:
            continue
        rows.sort(reverse=True)
        print(f"\n## {name} ({len(rows)} bài)")
        for d, title, link in rows[:12]:
            print(f"  [{d.isoformat()}] {title}\n      {link}")
        total += len(rows)
    print(f"\n=== TỔNG {total} ứng viên ===")
    print("Viện KHÔNG có RSS (dùng WebSearch site:<domain>): " + " · ".join(WEBSEARCH_ONLY))


def main() -> None:
    if len(sys.argv) == 2 and sys.argv[1] == "--candidates":
        list_candidates()
        return
    if len(sys.argv) != 2:
        print("Dùng: add_analyses.py /tmp/analyses.json  |  add_analyses.py --candidates", file=sys.stderr)
        sys.exit(1)

    payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    items = payload.get("analyses") if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        die("JSON phải có khoá 'analyses' là một mảng (hoặc chính nó là mảng)")
    if not items:
        print("Lô rỗng — không có gì để nạp.")
        return

    today_vn = datetime.datetime.now(VN).date()
    batch_raw = payload.get("date") if isinstance(payload, dict) else None
    try:
        batch_date = datetime.date.fromisoformat(batch_raw) if batch_raw else today_vn
    except ValueError:
        die(f"'date' của lô = '{batch_raw}' không đúng định dạng YYYY-MM-DD")

    repo_root = pathlib.Path(__file__).resolve().parent.parent
    html_path = repo_root / "index.html"
    html = html_path.read_text(encoding="utf-8")
    start, end = find_data_span(html)
    data = json.loads(html[start:end])

    existing_urls = collect_existing_urls(data)
    existing_titles = [a.get("title", "") for a in data.get("analyses") or []]

    seen_batch = set()
    warnings = []
    clean = []
    for i, it in enumerate(items, 1):
        missing = REQUIRED_FIELDS - {k for k, v in it.items() if str(v).strip()}
        if missing:
            die(f"bài #{i} ('{it.get('title', '?')[:50]}') thiếu field: {', '.join(sorted(missing))}")

        check_date(it["date"], batch_date, today_vn)

        url = it["url"].strip()
        if not url.startswith(("http://", "https://")):
            die(f"bài #{i} url không phải http(s): {url}")
        if BAD_URL.search(url):
            die(f"bài #{i} url trỏ live-blog: {url}")
        if is_homepage(url):
            die(f"bài #{i} url là trang chủ/trang mục, không phải bài cụ thể: {url}")
        if not is_thinktank(url):
            die(
                f"bài #{i} domain '{domain_of(url)}' KHÔNG thuộc danh sách viện nghiên cứu.\n"
                f"       Mục này là 🏛️ Think-tank — bài báo chí thường thì BỎ (hoặc đưa vào bản tin "
                f"qua add_news.py).\n"
                f"       Nếu đây đúng là viện nghiên cứu thật: thêm domain vào THINKTANK_DOMAINS "
                f"trong scripts/add_analyses.py."
            )
        if url in seen_batch:
            die(f"bài #{i} trùng url với bài khác trong cùng lô: {url}")
        if url in existing_urls:
            die(f"bài #{i} url ĐÃ CÓ trong DATA (bài trùng): {url}")
        seen_batch.add(url)

        region = (it.get("region") or "").strip()
        if region and region not in VALID_REGIONS:
            warnings.append(f"bài #{i} region lạ: '{region}' (không chặn, nhưng web lọc theo khu vực sẽ không gom đúng)")

        for old in existing_titles:
            if jaccard(it["title"], old) >= 0.6:
                warnings.append(f"bài #{i} tiêu đề nghi TRÙNG bài đã có: '{old[:60]}'")
                break

        clean.append({
            "date": it["date"],
            "region": region,
            "topic": (it.get("topic") or "").strip() or "Phân tích",
            "outlet": it["outlet"].strip(),
            "author": (it.get("author") or "").strip(),
            "title": it["title"].strip(),
            "summary": it["summary"].strip(),
            "takeaway": it["takeaway"].strip(),
            "url": url,
            # Ngày ĐƯA LÊN (khác `date` = ngày đăng bài). Email sáng dùng field này để biết
            # bài nào vừa nạp trong phiên, không phải bài cũ nằm sẵn trong mảng.
            "_addedDate": today_vn.isoformat(),
        })

    # Bài mới lên đầu, rồi sắp toàn mảng theo ngày đăng giảm dần cho khớp cách web hiển thị.
    merged = clean + (data.get("analyses") or [])
    merged.sort(key=lambda a: str(a.get("date") or ""), reverse=True)
    data["analyses"] = merged

    new_data = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    html_path.write_text(html[:start] + new_data + html[end:], encoding="utf-8")

    for w in warnings:
        print(f"⚠️  CẢNH BÁO: {w}")
    outlets = ", ".join(sorted({c["outlet"] for c in clean}))
    print(f"OK: đã nạp {len(clean)} bài think-tank ({outlets}). Tổng mục Phân tích: {len(merged)} bài.")
    hom_nay = sum(1 for a in merged if a.get("_addedDate") == today_vn.isoformat())
    print(f"    Nạp trong ngày {today_vn.isoformat()}: {hom_nay} bài.")


if __name__ == "__main__":
    main()
