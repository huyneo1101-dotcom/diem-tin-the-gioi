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
- `date` sai định dạng hoặc ở TƯƠNG LAI (xét cả so với ngày lô lẫn so với hôm nay giờ VN).
  ⛔ **KHÔNG còn chặn bài CŨ** — bỏ 29/07/2026 theo chỉ thị Huy, vì mục này nay kiêm KHO
  NỀN cho việc viết phân tích tập trận: bài viện ra 6 tháng trước vẫn dùng làm nền tốt.
  `MAX_AGE_DAYS` giờ CHỈ còn áp cho `--candidates` (khung liệt kê ứng viên hằng ngày),
  không áp cho khâu nạp. Guardrail tuổi của `add_news.py` (tin thời sự) giữ nguyên;
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

# Khung LIỆT KÊ ứng viên của `--candidates` (luồng routine sáng nhặt bài mới trong tuần).
# ⛔ KHÔNG còn là guardrail nạp: khâu nạp đã BỎ chặn tuổi bài 29/07/2026 (xem `check_date`)
# để mục này kiêm kho nền cho bài phân tích tập trận. Đổi số ở đây chỉ đổi phạm vi liệt kê.
MAX_AGE_DAYS = 7

# Trần số bài in ra MỖI VIỆN. 26 viện × 12 bài thì danh sách ứng viên dài hơn cả bài phân
# tích, ngốn hết context của agent chọn bài.
PER_FEED_CAP = 8

REQUIRED_FIELDS = {"date", "outlet", "title", "summary", "takeaway", "url"}

# Khớp bảng màu `RCOLOR` trong index.html (dòng ~347) — region ngoài bảng đó vẫn hiện được
# nhưng chấm màu rơi về xám mặc định. Thêm khu vực mới thì thêm cả màu bên index.html.
VALID_REGIONS = {
    "Châu Âu/NATO", "Trung Đông", "Đông Á", "Toàn cầu", "Châu Mỹ",
    "Ấn Độ Dương - Thái Bình Dương", "Châu Phi", "Nam Á", "Bắc Cực", "Trung Á",
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
    # United States Studies Centre (ĐH Sydney) — thêm 29/07/2026 khi nạp bài nền tập trận.
    # Viện thật, chuyên chính sách Mỹ ở Ấn Độ Dương - TBD; không có RSS dùng được nên chỉ
    # tới qua WebSearch/bảng chọn, vì vậy trước giờ chưa lọt vào danh sách.
    "ussc.edu.au",
    # Trung Đông / châu Phi
    "inss.org.il", "issafrica.org", "crisisgroup.org",
    # Dữ liệu (tầng 2) nhưng xuất bản phân tích
    "sipri.org",
    # ——— Bổ sung 27/07/2026 khi mở rộng theo KHU VỰC (chỉ thị Huy). Gồm CẢ nơi không có RSS
    # (xem WEBSEARCH_ONLY): bài tìm được bằng WebSearch vẫn phải nạp được, nếu không thì
    # guardrail domain sẽ chặn oan chính đường bù cho vùng trống RSS.
    # Nga · Đông Âu · châu Âu
    "cepa.org", "ridl.io", "globsec.org", "bruegel.org", "ceps.eu", "iss.europa.eu",
    # Trung Đông
    "mei.edu", "washingtoninstitute.org", "agsiw.org", "carnegie-mec.org",
    "epc.ae", "gulfif.org",
    # Châu Phi · Sahel
    "africacenter.org", "saiia.org.za", "timbuktu-institute.org",
    # Mỹ Latin
    "wola.org", "dialogo-americas.com", "thedialogue.org",
    # Nam Á · Trung Á
    "idsa.in", "takshashila.org.in", "cacianalyst.org", "sipa.columbia.edu",
    # Đông Bắc Á · Đông Nam Á
    "jiia.or.jp", "spf.org", "tokyofoundation.org", "sejong.org", "fulcrum.sg",
    "interpret.csis.org",
    # Bắc Cực
    "thearcticinstitute.org", "highnorthnews.com",
    # Hạt nhân · kiểm soát vũ khí · khủng bố
    "armscontrol.org", "thebulletin.org", "nti.org", "fas.org",
    "ctc.westpoint.edu", "thesoufancenter.org",
    # Quân sự · hải quân
    "mwi.westpoint.edu", "smallwarsjournal.com", "cimsec.org", "gmfus.org",
}

BAD_URL = re.compile(r"/(live|live-blog|live-updates|liveblog)(/|$)", re.I)

# RSS của các viện — VERIFY BẰNG FETCH THẬT 27/07/2026 (curl có UA + --compressed).
# ⚠️ Phải kèm cả hai cờ đó: War on the Rocks trả 403 khi curl trần (CLAUDE.md từng chấm
# "BỎ HẲN" vì vậy), nhưng có UA thì trả 100 item bình thường.
# Cột 3 = khu vực/mảng chính. Có cột này để nhìn phát biết mình đang phủ đâu và TRỐNG đâu
# (chỉ thị Huy 27/07/2026: "có thể quét các bài think tank về các khu vực quan trọng khác").
THINKTANK_FEEDS = [
    # — Ấn Độ Dương - Thái Bình Dương / Đông Á
    ("Lowy Institute", "https://www.lowyinstitute.org/the-interpreter/rss.xml", "Ấn Độ Dương - TBD"),
    ("ASPI", "https://www.aspistrategist.org.au/feed/", "Úc · Ấn Độ Dương - TBD"),
    ("Fulcrum (ISEAS)", "https://fulcrum.sg/feed/", "Đông Nam Á"),
    ("MERICS", "https://merics.org/en/rss", "Trung Quốc"),
    ("Interpret China (CSIS)", "https://interpret.csis.org/feed/", "Trung Quốc"),
    ("AMTI/CSIS", "https://amti.csis.org/feed/", "Biển Đông"),
    # — Nga · Đông Âu · châu Âu
    ("CEPA", "https://cepa.org/feed/", "Nga · Đông Âu"),
    ("Riddle Russia", "https://ridl.io/feed/", "Nga (nội tình)"),
    ("Jamestown Foundation", "https://jamestown.org/feed/", "Nga · Trung Á · TQ"),
    ("GMF", "https://www.gmfus.org/rss.xml", "Xuyên Đại Tây Dương ⚠️ lẫn tin tổ chức"),
    ("Bruegel", "https://www.bruegel.org/rss.xml", "Kinh tế châu Âu"),
    # — Trung Đông · châu Phi · Sahel
    ("Long War Journal", "https://www.longwarjournal.org/feed", "Sahel · khủng bố"),
    ("SAIIA", "https://saiia.org.za/research/feed/", "Châu Phi"),
    ("Crisis Group", "https://www.crisisgroup.org/rss.xml", "Xung đột toàn cầu"),
    # — Mỹ · quốc phòng · xuyên suốt
    ("Atlantic Council", "https://www.atlanticcouncil.org/feed/", "Toàn cầu"),
    ("War on the Rocks", "https://warontherocks.com/feed/", "Chiến lược quân sự"),
    ("RAND", "https://www.rand.org/blog.xml", "Toàn cầu"),
    ("Hudson Institute", "https://www.hudson.org/rss.xml", "Mỹ · châu Á"),
    ("Heritage Foundation", "https://www.heritage.org/rss", "Mỹ"),
    ("CSET", "https://cset.georgetown.edu/feed/", "AI · công nghệ"),
    ("Modern War Institute", "https://mwi.westpoint.edu/feed/", "Tác chiến"),
    ("Small Wars Journal", "https://smallwarsjournal.com/feed", "Xung đột phi quy ước"),
    ("CIMSEC", "https://cimsec.org/feed/", "Hải quân · biển"),
    ("Arms Control Association", "https://www.armscontrol.org/rss.xml", "Hạt nhân · kiểm soát vũ khí"),
]

# Đường dẫn KHÔNG phải bài phân tích, tuy nằm chung feed. Không lọc thì mục Think-tank đầy
# mẩu "chuyên gia X được Coindesk trích dẫn" — Atlantic Council đẩy cả chuyên mục
# /insight-impact/in-the-news/ vào feed (thực tế 33 bài/7 ngày thì 8 là loại này).
NOISE_PATHS = (
    "/in-the-news/", "/insight-impact/", "/press-release", "/media-advisory",
    "/event/", "/events/", "/podcast", "/newsletter", "/webinar", "/transcript",
    # Arms Control Association đẩy cả mục điểm báo (bài CNN/NYT trích lời chuyên gia) vào
    # feed — không phải nghiên cứu của viện.
    "/media-citations/", "/in-the-media", "/press-mention",
)

# KHÔNG có RSS dùng được — đã thử ÍT NHẤT 2 biến thể URL mỗi nơi (27/07/2026), ĐỪNG thử lại.
# Xếp theo KHU VỰC để phiên sáng biết vùng nào đang trống RSS mà chủ động `WebSearch
# site:<domain>`. Lý do hỏng: phần lớn Cloudflare 403 · vài nơi 404 · Africa Center và AGSIW
# trả RSS hợp lệ nhưng feed RỖNG (0 item) · IFRI feed đứng từ 2023.
WEBSEARCH_ONLY = {
    "Trung Đông": ["mei.edu", "washingtoninstitute.org", "inss.org.il", "agsiw.org", "carnegie-mec.org"],
    "Châu Phi · Sahel": ["africacenter.org", "issafrica.org"],
    "Mỹ Latin": ["wola.org", "dialogo-americas.com"],
    "Nam Á": ["orfonline.org", "idsa.in", "takshashila.org.in"],
    "Đông Bắc Á": ["38north.org", "jiia.or.jp", "spf.org", "eastasiaforum.org"],
    "Trung Á · Caucasus": ["cacianalyst.org"],
    "Bắc Cực": ["thearcticinstitute.org"],
    "Hạt nhân · khủng bố": ["thebulletin.org", "nti.org", "fas.org", "ctc.westpoint.edu", "thesoufancenter.org"],
    # SWP + Clingendael CÓ feed chạy được nhưng là feed ĐIỂM BÁO, không phải nghiên cứu:
    # SWP phát link thẳng ra cicero.de/deutschlandfunk.de (guardrail domain chặn), còn
    # Clingendael phát dưới chính domain của nó (`/node/NNNNN`, tiêu đề dạng "… / DW (Jul 21)")
    # nên guardrail KHÔNG chặn được — đó mới là loại nguy hiểm, bài báo lọt vào mục Think-tank
    # mà trông như bài viện. Đã BỎ khỏi THINKTANK_FEEDS, muốn bài của họ thì WebSearch.
    "Châu Âu": ["ecfr.eu", "chathamhouse.org", "rusi.org", "globsec.org", "ifri.org",
                "swp-berlin.org", "clingendael.org"],
    "Viện lớn của Mỹ": ["csis.org", "brookings.edu", "cnas.org", "stimson.org",
                        "carnegieendowment.org", "fpri.org", "belfercenter.org",
                        "wilsoncenter.org", "usip.org", "iiss.org"],
}


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


def clean_url(u: str) -> str:
    """Bỏ tham số theo dõi (utm_*, fbclid…) khỏi URL.

    CIMSEC gắn `?utm_source=rss&utm_medium=rss&utm_campaign=…` vào MỌI link trong feed.
    Không cắt thì: (a) url lưu vào DATA bẩn, (b) dedupe hụt — cùng một bài mà khác chuỗi
    utm sẽ lọt qua kiểm trùng và nạp hai lần.
    """
    u = (u or "").strip()
    if "?" not in u:
        return u
    base, _, query = u.partition("?")
    keep = [p for p in query.split("&")
            if p and not p.lower().startswith(("utm_", "fbclid=", "gclid=", "mc_cid=", "mc_eid="))]
    return base + ("?" + "&".join(keep) if keep else "")


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
    """Kiểm ngày bài think-tank.

    ⛔ **BỎ CHẶN TUỔI BÀI 29/07/2026 — chỉ thị Huy: *"bỏ chặn bài cũ hơn 7 ngày chỉ riêng
    trong mục think-tank"*.** Mục này nay kiêm KHO NỀN cho việc viết phân tích tập trận:
    một bài RAND/CSBA ra tháng 2 vẫn dùng làm nền tốt như bài ra tuần này — khác hẳn tin
    thời sự, thứ mà "cũ 2 ngày" là hỏng thật. Khung 7 ngày cũ được đặt cho luồng routine
    sáng nhặt bài mới; nó chưa bao giờ đúng với vai kho nền.

    Cái KHÔNG bỏ: bài ở **TƯƠNG LAI** vẫn chặn — đó là lỗi dữ liệu (ngày gõ nhầm, meta sai
    của trang nguồn), không phải bài cũ hợp lệ. Chặn tương lai xét theo CẢ ngày lô LẪN hôm
    nay thật (giờ VN) để neo lô về tương lai cũng không lách được.

    ⚠️ Guardrail tuổi bài của `add_news.py` (tin thời sự) KHÔNG đổi — đừng chép luật này
    sang đó: hai mục khác hẳn nhau về bản chất, gộp luật là mở lại đúng lỗ hổng 26/07.
    """
    try:
        d = datetime.date.fromisoformat(item_date)
    except ValueError:
        die(f"date='{item_date}' không đúng định dạng YYYY-MM-DD")
    if d > batch_date:
        die(f"date='{item_date}' ở TƯƠNG LAI so với ngày lô {batch_date.isoformat()}")
    if d > today_vn:
        die(f"date='{item_date}' ở TƯƠNG LAI so với HÔM NAY ({today_vn.isoformat()}, giờ VN)")


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


def parse_feed(xml_bytes: bytes):
    """Parse XML, có FALLBACK cắt tới thẻ đóng cuối cùng.

    Vì sao cần fallback: feed Arms Control Association trả XML hợp lệ NHƯNG server nhét
    thêm nội dung sau `</rss>` → ET báo "junk after document element" và ta suýt gạch nhầm
    một nguồn hạt nhân đang sống (10 item). Cắt tới thẻ đóng rồi parse lại là lấy được.
    """
    try:
        return ET.fromstring(xml_bytes)
    except Exception:
        pass
    for close in (b"</rss>", b"</feed>", b"</rdf:RDF>"):
        k = xml_bytes.rfind(close)
        if k > 0:
            try:
                return ET.fromstring(xml_bytes[:k + len(close)])
            except Exception:
                continue
    return None


def feed_items(xml_bytes: bytes):
    """[(title, link, ngày)] cho cả RSS 2.0, RDF lẫn Atom."""
    root = parse_feed(xml_bytes)
    if root is None:
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
    empty = []
    print(f"=== ỨNG VIÊN THINK-TANK ({len(THINKTANK_FEEDS)} viện · đăng trong {MAX_AGE_DAYS} ngày, "
          f"tính tới {today_vn.isoformat()}) ===")
    for name, url, area in THINKTANK_FEEDS:
        rows = []
        for title, link, d in feed_items(curl(url)):
            if d is None or (today_vn - d).days > MAX_AGE_DAYS or d > today_vn:
                continue
            link = clean_url(link)
            if link in existing or link.split("?")[0] in existing:
                continue
            if any(p in link.lower() for p in NOISE_PATHS):
                continue
            rows.append((d, title, link))
        if not rows:
            empty.append(f"{name} ({area})")
            continue
        rows.sort(reverse=True)
        print(f"\n## {name} — {area} ({len(rows)} bài)")
        for d, title, link in rows[:PER_FEED_CAP]:
            print(f"  [{d.isoformat()}] {title}\n      {link}")
        if len(rows) > PER_FEED_CAP:
            print(f"  … còn {len(rows) - PER_FEED_CAP} bài nữa (cắt bớt cho gọn context)")
        total += len(rows)
    print(f"\n=== TỔNG {total} ứng viên ===")
    if empty:
        # In ra để phiên sáng BIẾT vùng nào đang trống mà bù bằng WebSearch, thay vì tưởng
        # là hôm nay không có gì đáng đọc.
        print("Feed không ra bài nào trong khung ngày: " + " · ".join(empty))
    print("\nVùng KHÔNG có RSS — chủ động bù bằng `WebSearch site:<domain>` khi vùng đó vắng:")
    for area, doms in WEBSEARCH_ONLY.items():
        print(f"  {area}: " + " · ".join(doms))


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

        url = clean_url(it["url"])
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
