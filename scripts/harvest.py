#!/usr/bin/env python3
"""Gom ỨNG VIÊN tin cho 5 chủ đề — chạy TRƯỚC khi giao agent.

Dùng:  python3 scripts/harvest.py                 # cả RSS + Google News
       python3 scripts/harvest.py --rss           # chỉ RSS trong bảng CLAUDE.md
       python3 scripts/harvest.py --gnews         # chỉ Google News
       python3 scripts/harvest.py --json /tmp/ung-vien.json    # ghi thêm ra JSON
       python3 scripts/harvest.py --gop-ci                     # LOCAL: gộp thêm lô runner Mỹ gom sẵn
       python3 scripts/harvest.py --ci-out docs/ung-vien-ci.json   # CI: ghi lô cho local gộp (harvest-ci.yml)

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

ĐO LẠI 30/07/2026 — 05 nguồn nêu trên KHÔNG bị chặn, và nay đã đóng góp thật:
AllAfrica 2 ứng viên · Philstar 2 · Lowy 2 · gCaptain 1 · Long War Journal 0
(feed vẫn trả 30 item, chỉ là hôm đó không bài nào hợp chủ đề Mali — khác hẳn
"bị chặn"). Tức chính script này đã sửa được vấn đề nó sinh ra để sửa. Nhưng
đợt đo cùng ngày lại lòi ra một lớp lỗi KHÁC hẳn, ở ngay bên dưới: 16 nguồn bị
chặn theo VÂN TAY TLS — xem chú thích hàm `curl` và bảng tra trong CLAUDE.md.

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
import os
import pathlib
import re
import subprocess
import sys
import urllib.parse
import xml.etree.ElementTree as ET
import zoneinfo

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from topics import match_topic, us_subgroup, us_rank  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
VN = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")

# Google News: mỗi chủ đề một truy vấn. `when:2d` để Google lọc sẵn 2 ngày,
# ta vẫn lọc lại theo pubDate vì "2d" của Google rộng hơn khung của ta.
GNEWS_QUERIES = {
    "Úc & Biển Đông": [
        '"South China Sea" OR Scarborough OR "Second Thomas Shoal" OR "West Philippine Sea"',
        'AUKUS OR "Australian Defence Force" OR "Royal Australian Navy"',
        # các nước khác quanh Biển Đông (mở rộng 27/07/2026 theo chỉ thị Huy)
        'Malaysia OR Indonesia OR Vietnam OR Taiwan maritime "South China Sea" patrol OR protest',
        '"code of conduct" ASEAN China sea OR Natuna OR "Vanguard Bank"',
    ],
    "CNQS Mỹ": [
        '"U.S. Air Force" OR "U.S. Navy" OR Pentagon missile OR hypersonic OR "Space Force"',
        '"defense contract" OR "awarded a contract" Pentagon',
    ],
    "Mỹ – Mali": ['Mali OR JNIM OR Sahel OR Bamako OR "Africa Corps"'],
    "Predator's Run": ['"Predator\'s Run"'],
    # 4 NHÓM theo thứ tự ưu tiên Huy chốt 27/07/2026 — nhóm 1 trước, thiếu mới tới 2/3/4.
    "Nội bộ Mỹ": [
        # (1) điều trần + bỏ phiếu thông qua dự luật  ← BẮT BUỘC, tìm trước
        '"Senate Armed Services" hearing OR "House Armed Services" markup OR testimony',
        '"House passes" OR "Senate passes" OR "committee approves" bill',
        # (2) sáng kiến/chiến lược chính quyền trên kênh chính thống các bộ
        '"executive order" OR "White House announces" OR "national strategy" Trump',
        # (3) biểu tình
        'protest OR rally OR demonstration United States Washington',
        # (4) kinh tế Mỹ + động thái Trump và nội các
        '"Federal Reserve" OR tariff OR sanctions OR "jobs report" United States',
        # (5) BẦU CỬ — nhóm riêng, ngang hàng 2/3/4 (Huy bổ sung 27/07/2026)
        'midterms OR "primary election" OR redistricting OR "voter" United States 2026',
        '"Senate race" OR "House race" OR campaign OR poll midterm elections',
    ],
}

# Khung ngày NỚI RIÊNG cho CNQS Mỹ: quét ngày 27 thì lấy được tới ngày 24 (chỉ thị Huy
# 27/07/2026). Khớp `MAX_AGE_DAYS_CNQS` trong add_news.py — sửa một bên phải sửa bên kia,
# nếu không harvest sẽ đưa ứng viên mà guardrail chặn (hoặc bỏ sót ứng viên hợp lệ).
CNQS_LOOKBACK_DAYS = 3


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


def _daykey(s: str) -> int:
    """'2026-07-27' -> 20260727 để sắp xếp; '?' -> 0."""
    try:
        return int(s.replace("-", ""))
    except (ValueError, AttributeError):
        return 0


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


# ── LẤY NỘI DUNG: curl thường, bị chặn thì thử lại bằng vân tay TLS của Chrome ──
# VÌ SAO (đo thật 30/07/2026): Akamai và Cloudflare nhận dạng dấu vân tay TLS (JA3/JA4)
# của curl/urllib rồi cắt kết nối, trong khi Chrome CÙNG MÁY CÙNG IP vào bình thường
# (đo: Browser pane đi ra bằng đúng 113.23.43.99 như curl). KHÔNG phải chặn địa lý.
# Đo lẻ tuần tự 21 nguồn hỏng: 16 nguồn curl 403 mà `impersonate="chrome"` trả 200 —
# gồm Breaking Defense (30 item), Naval Technology (10), army.mil (45) và 13 trang
# Thượng viện. Thêm header đầy đủ hay ép HTTP/1.1 KHÔNG cứu được cái nào: đã đo
# cả 3 cấu hình × 108 nguồn, số nguồn hỏng y hệt nhau (21/108).
#
# ⚠️ 403 KHÔNG phải lúc nào cũng lộ ra là rỗng hay ngắn: trang lỗi của Naval Technology
# dài 19.357 byte và MỞ ĐẦU BẰNG `<?xml`, nên `items_of` parse ra 0 item mà không ném
# lỗi — hỏng câm hoàn hảo. Vì vậy phải dò theo DẤU HIỆU trong thân, không dò theo cỡ.
DAU_HIEU_CHAN = (b"403 forbidden", b"error 403", b"access denied",
                 b"attention required", b"just a moment", b"request forbidden")

# Sổ ghi vết trong RAM: nguồn nào phải nhờ vân tay TLS, nguồn nào chịu chết.
# `main()` in ra cuối — nguồn chết mà không ai kêu thì sống mãi (bài học cổng câm NFD).
VET_NGUON = {"cffi_va_duoc": [], "chan_ca_hai": [], "cffi_vang_mat": set()}

_CFFI = None  # None = chưa thử import · False = máy không có curl_cffi


def _nghi_bi_chan(body: bytes) -> bool:
    if not body:
        return True
    dau = body[:3000].lower()
    return any(d in dau for d in DAU_HIEU_CHAN)


def _lay_bang_van_tay_chrome(url: str, timeout: int) -> bytes:
    """Thử lại bằng curl_cffi (giả vân tay TLS Chrome). Thiếu thư viện thì trả rỗng.

    Fail-open CÓ TIẾNG: thiếu `curl_cffi` thì harvest vẫn chạy (CI không cần nó — runner
    Mỹ curl thẳng được), nhưng ghi vào VET_NGUON để cuối phiên còn in ra. Im lặng ở đây
    là tạo đúng vùng câm mà cả hàm này sinh ra để bịt.
    Cài ở máy local:  python3 -m pip install --user curl_cffi
    """
    global _CFFI
    if _CFFI is False:
        return b""
    if _CFFI is None:
        try:
            from curl_cffi import requests as _r  # noqa: PLC0415
            _CFFI = _r
        except ImportError:
            _CFFI = False
            return b""
    try:
        r = _CFFI.get(url, impersonate="chrome", timeout=timeout)
        return r.content if r.status_code == 200 else b""
    except Exception:
        return b""


def curl(url: str, timeout: int = 25) -> bytes:
    p = subprocess.run(
        ["curl", "-sL", "--compressed", "--max-time", str(timeout), "-A", UA, url],
        capture_output=True,
    )
    body = p.stdout or b""
    if not _nghi_bi_chan(body):
        return body
    if _CFFI is False:
        VET_NGUON["cffi_vang_mat"].add(url)
        return body
    body2 = _lay_bang_van_tay_chrome(url, timeout)
    if _CFFI is False:          # vừa phát hiện thiếu thư viện ngay trong lượt này
        VET_NGUON["cffi_vang_mat"].add(url)
        return body
    if body2 and not _nghi_bi_chan(body2):
        VET_NGUON["cffi_va_duoc"].append(url)
        return body2
    VET_NGUON["chan_ca_hai"].append(url)
    return body


KEY_BANG_HTML = "TRANG HTML QUÉT TRỰC TIẾP"


def _vi_tri_tieu_de(text: str, key: str) -> int:
    """Vị trí dòng TIÊU ĐỀ `### … <key>`, KHÔNG phải lần xuất hiện đầu tiên của chuỗi `key`.

    ⚠️ Vá 30/07/2026 — bug đã xảy ra thật và là hỏng CÂM hoàn hảo. Bản cũ dùng `text.index(key)`,
    nên chỉ cần một chỗ trong VĂN XUÔI nhắc tên bảng (`nay cả 06 nằm trong bảng "🕸️ TRANG HTML
    QUÉT TRỰC TIẾP"`) mà chỗ đó đứng TRƯỚC bảng thật, là hàm cắt lấy đoạn văn ấy rồi trả về
    **0 trang** — lớp [HTML] chết sạch, không lỗi, không cảnh báo, và bảng trong CLAUDE.md vẫn
    còn nguyên 25 dòng nên soi bằng mắt thì thấy đủ. Đo thật lúc bắt được: 25 trang -> 0.
    Neo vào tiêu đề thì tài liệu tự do nhắc tên bảng bao nhiêu lần cũng được.

    ⚠️ Nhánh dự phòng KHÔNG được lùi về `text.index(key)` — đó chính là bug đang vá, nên lùi về
    nó là mở lại đúng cái lỗ vừa bịt (ca 10 của bộ test bắt được chỗ này ngay lúc dựng). Thay vào
    đó, xét MỌI lần chuỗi xuất hiện rồi lấy lần nào mở ra khối có nhiều dòng bảng nhất: định dạng
    tiêu đề có thể đổi, còn "khối nào thật sự chứa bảng" thì đo được.
    """
    for m in re.finditer(r"^#{2,4} .*$", text, re.M):
        if key in m.group(0):
            return m.start()

    def dem_dong_bang(i):
        rest = text[i:]
        j = rest.index("\n### ", 1) if "\n### " in rest[1:] else len(rest)
        return sum(1 for ln in rest[:j].split("\n")
                   if ln.startswith("|") and re.search(r"https?://\S+", ln))

    vi_tri = [m.start() for m in re.finditer(re.escape(key), text)]
    return max(vi_tri, key=dem_dong_bang)


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
    # Bảng "TRANG HTML QUÉT TRỰC TIẾP" nằm cùng mục ## URL RSS nhưng KHÔNG phải feed —
    # cắt ra, nếu không lớp RSS sẽ tốn 8 request vô ích và số feed in ra bị sai (81 -> 89).
    if KEY_BANG_HTML in block:
        i = _vi_tri_tieu_de(block, KEY_BANG_HTML)
        rest = block[i:]
        j = rest.index("\n### ", 1) if "\n### " in rest[1:] else len(rest)
        block = block[:i] + rest[j:]
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


def html_pages_from_claude_md():
    """Lấy (tên trang, url) từ bảng '🕸️ TRANG HTML QUÉT TRỰC TIẾP' trong CLAUDE.md.

    Bảng có cột "Chạy ở": `cả hai` hoặc `CI`. Trang đánh dấu **CI** chỉ GitHub runner đọc được
    (máy Mac bị 403) — đo thật 27/07/2026 bằng `scripts/probe_sources.py` chạy ở cả hai nơi:
    TOÀN BỘ uỷ ban THƯỢNG VIỆN thuộc nhóm này. Chạy ở local thì bỏ qua chúng, khỏi tốn 15 lượt
    curl chỉ để nhận 403.
    """
    text = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    key = KEY_BANG_HTML
    if key not in text:
        return []
    block = text[_vi_tri_tieu_de(text, key):]
    block = block[: block.index("\n### ", 1)] if "\n### " in block[1:] else block
    la_ci = bool(os.environ.get("GITHUB_ACTIONS"))
    out, seen, bo_qua = [], set(), 0
    for line in block.split("\n"):
        if not line.startswith("|"):
            continue
        m = re.search(r"https?://\S+", line)
        if not m:
            continue
        url = m.group(0).rstrip("|").strip()
        cols = [c.strip() for c in line.split("|")]
        # bỏ dấu ** của markdown: bảng CLAUDE.md in đậm vài tên -> lọt thẳng vào prompt agent
        name = re.sub(r"\*+", "", cols[1]).strip() if len(cols) > 1 else url
        ci_only = any(re.fullmatch(r"\*{0,2}CI\*{0,2}", c) for c in cols[2:])
        if url in seen:
            continue
        seen.add(url)
        if ci_only and not la_ci:
            bo_qua += 1
            continue
        out.append((name, url))
    if bo_qua:
        print(f"[HTML] bỏ qua {bo_qua} trang chỉ CI đọc được (đang chạy ở local)", file=sys.stderr)
    return out


# Ngày trong HTML: "July 22, 2026" hoặc "2026-07-22" hoặc "07/22/2026"
_DATE_PATTERNS = [
    re.compile(r"(20\d\d-\d\d-\d\d)"),
    re.compile(r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+20\d\d)"),
    re.compile(r"(\d{1,2}/\d{1,2}/20\d\d)"),
]
_MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}


def parse_date_loose(s: str):
    """Parse ngày kiểu 'July 22, 2026' / '2026-07-22' / '07/22/2026' -> date."""
    s = s.strip()
    try:
        return datetime.date.fromisoformat(s)
    except ValueError:
        pass
    m = re.match(r"([A-Za-z]+)\.?\s+(\d{1,2}),?\s+(20\d\d)", s)
    if m and m.group(1)[:3].lower() in _MONTHS:
        return datetime.date(int(m.group(3)), _MONTHS[m.group(1)[:3].lower()], int(m.group(2)))
    m = re.match(r"(\d{1,2})/(\d{1,2})/(20\d\d)", s)
    if m:
        return datetime.date(int(m.group(3)), int(m.group(1)), int(m.group(2)))
    return None


def _lam_sach(s: str) -> str:
    """Gộp khoảng trắng + giải mã vài thực thể HTML hay gặp. Dùng CHUNG cho mọi đường lấy tiêu đề.

    Viết một chỗ để tiêu đề lấy từ text thẻ <a>, từ `aria-label` và từ `<h4 class="title">` không
    thể khác nhau về cách làm sạch — lệch nhau thì cùng một bài ra hai tiêu đề tuỳ đường đi.
    """
    s = re.sub(r"\s+", " ", s).strip()
    return (s.replace("&amp;", "&").replace("&#39;", "'").replace("&quot;", '"')
             .replace("&nbsp;", " ").replace("&rsquo;", "'").strip())


def harvest_html(window):
    """Quét thẳng trang danh sách thông cáo (không có RSS).

    Huy nhắc 27/07/2026: "không có RSS thì mày vẫn xem được mà" — đúng. Kiểm lại thì 42/85 domain
    nguồn chính thức Mỹ mở được HTML bằng curl; đặc biệt TOÀN BỘ uỷ ban Hạ viện, tức đúng nhóm 1
    (điều trần + bỏ phiếu) — nhóm luôn thiếu tin nhất.
    ⚠️ Nhiễu cao hơn RSS và NGÀY lấy từ khối HTML quanh link nên có thể sai → output đánh dấu
    `[HTML]`, agent phải mở bài kiểm ngày sự kiện như với `[GNEWS]`.
    """
    pages = html_pages_from_claude_md()
    if not pages:
        return []
    print(f"[HTML] quét {len(pages)} trang không có RSS (uỷ ban Hạ viện...)...", file=sys.stderr)
    hits = []
    for name, page_url in pages:
        body = curl(page_url).decode("utf-8", "replace")
        base = "{0.scheme}://{0.netloc}".format(urllib.parse.urlparse(page_url))
        for m in re.finditer(r'<a([^>]+href="([^"]+)"[^>]*)>(.*?)</a>', body, re.S | re.I):
            thuoc_tinh, href, raw = m.group(1), m.group(2), m.group(3)
            title = _lam_sach(re.sub(r"<[^>]+>", " ", raw))
            if not 25 <= len(title) <= 200:
                # Thẻ <a> bọc cả ngày + tiêu đề + đoạn tóm tắt thì text gộp dài 268-418 ký tự và
                # bị trần 200 loại sạch. Đo thật 30/07: marines.mil có 10 link bài, MẤT CẢ 10 —
                # trang trả 200 nên nhìn đâu cũng tưởng nguồn đang chạy, chỉ là nó không bao giờ
                # đóng góp ứng viên nào. Đúng loại hỏng câm: "nguồn vào bảng mà không ra tin".
                # Lấy tiêu đề sạch theo 2 nguồn của CMS ArticleCS (DoD dùng cho MỌI trang quân
                # chủng: marines · navy · pacom · centcom · jcs · uscg) — một bản vá phủ cả 06.
                thay = ""
                al = re.search(r'aria-label="([^"]{25,200})"', thuoc_tinh, re.I)
                if al:
                    thay = _lam_sach(al.group(1))
                else:
                    h = re.search(r'<h[1-6][^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</h[1-6]>',
                                  raw, re.S | re.I)
                    if h:
                        thay = _lam_sach(re.sub(r"<[^>]+>", " ", h.group(1)))
                if not 25 <= len(thay) <= 200:
                    continue
                title = thay
            if not re.search(r"/(news|press|media|hearing|markup|document)", href, re.I):
                continue
            topic = match_topic(title, "both")
            if not topic:
                continue
            # ngày: tìm trong khối HTML quanh link (±600 ký tự)
            around = body[max(0, m.start() - 600): m.end() + 600]
            d = None
            for pat in _DATE_PATTERNS:
                mm = pat.search(around)
                if mm:
                    d = parse_date_loose(mm.group(1))
                    if d:
                        break
            if d is not None and d not in window_for(topic, window):
                continue
            url = href if href.startswith("http") else urllib.parse.urljoin(base, href.lstrip("/"))
            hits.append({
                "lop": "HTML", "chu_de": topic, "ngay": d.isoformat() if d else "?",
                "tieu_de": title, "nguon": name, "url": url,
            })
    return hits


def window_for(topic: str, base: set) -> set:
    """Khung ngày của từng chủ đề. CNQS Mỹ được nới xuống CNQS_LOOKBACK_DAYS ngày."""
    if topic != "CNQS Mỹ":
        return base
    today = max(base)
    return {today - datetime.timedelta(days=i) for i in range(CNQS_LOOKBACK_DAYS + 1)}


def harvest_rss(window):
    hits = []
    feeds = feeds_from_claude_md()
    print(f"[RSS] quét {len(feeds)} feed từ bảng trong CLAUDE.md...", file=sys.stderr)
    for name, url in feeds:
        forced = FORCE_TOPIC.get(name)
        raw = items_of(curl(url))
        # Đếm item THÔ, trước mọi bộ lọc. Phân biệt hai chuyện khác hẳn nhau mà nhìn kết
        # quả cuối thì giống hệt: feed CHẾT (0 item) khác feed sống mà hôm nay không có
        # bài khớp chủ đề. Không tách ra thì một feed chết nằm im hàng tháng — đúng bệnh
        # đã bắt được 30/07: Breaking Defense 403 từ lúc nào không ai biết, bảng CLAUDE.md
        # vẫn ghi "25 item, mới 2h".
        if not raw:
            VET_NGUON.setdefault("feed_rong", []).append((name, url))
        for title, link, pub, _ in raw:
            d = parse_date(pub)
            topic = forced or match_topic(title, "both")
            if not topic:
                continue
            if d is not None and d not in window_for(topic, window):
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
                if d is not None and d not in window_for(topic, window):
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


# ── Lô ứng viên do CI (runner Mỹ) gom sẵn ──────────────────────────────────────
# VÌ SAO: lớp [HTML] ở local chỉ quét được 10 trang, còn CI quét 25 (toàn bộ uỷ ban
# THƯỢNG VIỆN + 2 feed .mil chỉ phân giải được DNS từ Mỹ — xem docs/probe-ci.json).
# Trước 27/07 phần chênh đó mất trắng mỗi khi CI chết và local phải gánh. Nay workflow
# `harvest-ci.yml` chạy THUẦN curl (không gọi Claude, không tốn quota) trước mỗi mốc
# quét, commit lô ứng viên vào file này; phiên local `git pull` rồi gộp vào.
CI_FILE = ROOT / "docs" / "ung-vien-ci.json"
CI_TOI_DA_PHUT = 240   # quá 4 tiếng coi như ôi -> bỏ, đừng nạp tin cũ của phiên trước


def ghi_ung_vien_ci(path, out, window):
    """CI ghi lô ứng viên kèm dấu thời gian + khung ngày để local kiểm độ tươi.

    Chỉ ghi [RSS] + [HTML]: bên nhận (`doc_ung_vien_ci`) vốn đã bỏ [GNEWS], mà lớp đó
    chiếm ~70% dung lượng — file này commit vào repo 4 lần/ngày nên cắt đi cho đỡ phình.
    """
    out = [h for h in out if h.get("lop") != "GNEWS"]
    payload = {
        "tao_luc": datetime.datetime.now(VN).isoformat(timespec="seconds"),
        "moi_truong": "CI" if os.environ.get("GITHUB_ACTIONS") else "local",
        "khung_ngay": sorted(d.isoformat() for d in window),
        "ung_vien": out,
    }
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nĐã ghi lô ứng viên CI ({len(out)} bài) ra {path}")


def doc_ung_vien_ci(window):
    """Đọc lô CI nếu còn TƯƠI. Trả list hit (rỗng nếu không dùng được) — im lặng thất bại.

    Hai cổng kiểm, phải qua CẢ HAI:
      1. `khung_ngay` khớp khung đang quét (chống dùng lô của ngày khác);
      2. tuổi <= CI_TOI_DA_PHUT — vì khung ngày của mốc SÁNG (04:30) và mốc TỐI (21:15)
         cùng ngày là GIỐNG HỆT nhau (hôm nay + hôm qua), chỉ so khung thì lô 04:15
         vẫn "hợp lệ" lúc 21:15 và bản tin tối sẽ thiếu sạch tin ban ngày.
    """
    if not CI_FILE.exists():
        print(f"[CI] không có {CI_FILE.name} — bỏ qua, chỉ dùng lô local", file=sys.stderr)
        return []
    try:
        payload = json.loads(CI_FILE.read_text(encoding="utf-8"))
        tao_luc = datetime.datetime.fromisoformat(payload["tao_luc"])
        khung = payload.get("khung_ngay") or []
        hits = payload.get("ung_vien") or []
    except (ValueError, KeyError, OSError) as e:
        print(f"[CI] {CI_FILE.name} hỏng ({e}) — bỏ qua", file=sys.stderr)
        return []
    if khung != sorted(d.isoformat() for d in window):
        print(f"[CI] lô CI thuộc khung {khung} ≠ khung đang quét — BỎ", file=sys.stderr)
        return []
    tuoi = (datetime.datetime.now(VN) - tao_luc).total_seconds() / 60
    if tuoi > CI_TOI_DA_PHUT or tuoi < -10:
        print(f"[CI] lô CI tạo lúc {payload['tao_luc']} ({tuoi:.0f} phút trước) — "
              f"quá {CI_TOI_DA_PHUT} phút, BỎ", file=sys.stderr)
        return []
    # CHỈ lấy [RSS] + [HTML], BỎ [GNEWS]. Đây là chỗ sai lần chạy thử đầu (27/07): gộp cả lô
    # thì nhận thêm 220 mục Google News mà local tự quét được y hệt (Google không chặn local),
    # lại là lớp rác nhất (bóng đá Mali, cáo phó, cá độ) — và link GNEWS là redirect sinh mới
    # mỗi lần gọi nên bộ lọc trùng URL KHÔNG bắt được, thành nhân đôi rác trong prompt agent.
    # [RSS] + [HTML] thì link là link gốc ổn định: trùng thì bị loại sạch ở vòng lọc bên dưới,
    # còn lại đúng PHẦN CHÊNH (15 trang uỷ ban Thượng viện + 2 feed .mil chỉ CI vào được),
    # tiện thể vá luôn những feed chập chờn lúc local quét.
    hits = [h for h in hits if h.get("lop") != "GNEWS"]
    for h in hits:
        h["lop"] = f"CI-{h.get('lop', '?')}"
    print(f"[CI] gộp {len(hits)} ứng viên [RSS]+[HTML] do runner Mỹ gom lúc {payload['tao_luc']} "
          f"({tuoi:.0f} phút trước) — đã bỏ lớp [GNEWS] vì local tự quét được", file=sys.stderr)
    return hits


def bao_nguon_hong():
    """In tình trạng nguồn ở CUỐI mỗi lần chạy — nguồn chết mà không ai kêu thì sống mãi.

    VÌ SAO PHẢI IN (bài học 30/07/2026): trước bản vá này, feed bị chặn chỉ đơn giản là
    không đóng góp ứng viên nào, y hệt một feed sống mà hôm nay không có bài hợp chủ đề.
    Không có gì phân biệt hai ca đó, nên Breaking Defense · Naval Technology · army.mil
    nằm chết trong bảng nguồn suốt nhiều ngày trong khi tài liệu vẫn ghi chúng "dùng tốt".
    Cùng họ với cổng dàn ý câm vì NFD ở QuanSu: hỏng thì im lặng, mà sạch cũng im lặng.
    """
    rong = VET_NGUON.get("feed_rong", [])
    cffi_va = VET_NGUON["cffi_va_duoc"]
    chan = VET_NGUON["chan_ca_hai"]
    thieu_cffi = VET_NGUON["cffi_vang_mat"]

    if cffi_va:
        print(f"\n🔓 {len(cffi_va)} nguồn phải lấy bằng VÂN TAY TLS Chrome (curl trần bị chặn):")
        for u in cffi_va:
            print(f"     {u[:130]}")
    if thieu_cffi:
        print(f"\n⚠️  {len(thieu_cffi)} nguồn bị chặn mà máy KHÔNG có `curl_cffi` để thử lại — "
              f"đang mất tin. Cài:  python3 -m pip install --user curl_cffi")
        for u in sorted(thieu_cffi)[:10]:
            print(f"     {u[:130]}")
    if chan:
        print(f"\n⛔ {len(chan)} nguồn chặn CẢ HAI đường (curl trần + vân tay Chrome):")
        for u in chan:
            print(f"     {u[:130]}")
    if rong:
        print(f"\n⛔ {len(rong)} FEED RSS TRẢ 0 ITEM — nghi chết hoặc đổi URL, "
              f"kiểm bằng `python3 scripts/kiem_nguon.py`:")
        for ten, u in rong:
            print(f"     {ten} — {u[:120]}")
    if not (rong or chan or thieu_cffi):
        print("\n✅ Mọi feed đều trả item; không nguồn nào bị chặn cả hai đường.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rss", action="store_true", help="chỉ quét RSS trong bảng CLAUDE.md")
    ap.add_argument("--gnews", action="store_true", help="chỉ quét Google News")
    ap.add_argument("--html", action="store_true", help="chỉ quét trang HTML không có RSS")
    ap.add_argument("--json", metavar="PATH", help="ghi kết quả ra file JSON")
    ap.add_argument("--ci-out", metavar="PATH", nargs="?", const=str(CI_FILE),
                    help="ghi lô ứng viên (kèm dấu thời gian) cho phiên khác gộp lại — "
                         f"mặc định {CI_FILE.relative_to(ROOT)}")
    ap.add_argument("--gop-ci", action="store_true",
                    help=f"gộp thêm lô ứng viên trong {CI_FILE.relative_to(ROOT)} nếu còn tươi")
    args = ap.parse_args()

    today = datetime.datetime.now(VN).date()
    window = {today, today - datetime.timedelta(days=1)}
    cnqs = sorted(window_for("CNQS Mỹ", window))
    print(f"Khung ngày: {sorted(window)[0]} .. {sorted(window)[1]} (hôm nay + hôm qua, giờ VN) · "
          f"riêng CNQS Mỹ nới: {cnqs[0]} .. {cnqs[-1]}", file=sys.stderr)

    chi_dinh = args.rss or args.gnews or args.html
    hits = []
    if args.rss or not chi_dinh:
        hits += harvest_rss(window)
    if args.html or not chi_dinh:
        hits += harvest_html(window)
    if args.gnews or not chi_dinh:
        hits += harvest_gnews(window)
    if args.gop_ci:
        # Gộp TRƯỚC vòng lọc bên dưới, không phải sau: lô CI gom lúc 20:45 chưa biết những
        # tin mà lớp CI 21:00 vừa nạp vào DATA — phải để nó đi qua đúng bộ lọc trùng/rác
        # với DATA hiện tại. Lô local đứng trước nên khi trùng sự kiện thì bản local được giữ.
        hits += doc_ung_vien_ci(window)

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
        extra = f" — in {PER_TOPIC_CAP} bài" if len(lst) > PER_TOPIC_CAP else ""
        print(f"\n-- {topic} ({len(lst)} bài{extra}) --")
        if not lst:
            print("   (không có ứng viên nào trong khung hôm nay + hôm qua)")
        if topic == "Nội bộ Mỹ":
            # Xếp theo HẠNG ưu tiên trước, ngày sau. Huy chốt 27/07: vét cạn nhóm (1) điều trần
            # + bỏ phiếu rồi mới tới các nhóm còn lại — và bốn nhóm còn lại NGANG NHAU
            # (2 sáng kiến/chiến lược · 3 biểu tình · 4 kinh tế+nội các · 5 bầu cử), nên xếp
            # theo `us_rank` chứ KHÔNG theo số nhóm; xếp theo số nhóm sẽ dìm bầu cử xuống cuối.
            # Xếp thuần theo ngày cũng hỏng: nhóm đăng dày (biểu tình/bầu cử/thuế quan) chiếm hết chỗ.
            for h in lst:
                h["nhom"] = us_subgroup(h["tieu_de"])
            ordered = sorted(
                lst, key=lambda x: (us_rank(x["nhom"]), x["ngay"] == "?", -_daykey(x["ngay"])))
            print("   (hạng 1 = nhóm 1 điều trần+bỏ phiếu, vét trước; "
                  "nhóm 2/3/4/5 NGANG NHAU, xếp theo ngày)")
        else:
            ordered = sorted(lst, key=lambda x: x["ngay"], reverse=True)
        for h in ordered[:PER_TOPIC_CAP]:
            nhom = f"[nhóm {h['nhom']}]" if h.get("nhom") and h["nhom"] != 9 else ""
            print(f"   [{h['lop']}][{h['ngay']}]{nhom} {h['tieu_de'][:100]}")
            print(f"        {h['nguon']} — {h['url'][:120]}")

    bao_nguon_hong()

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

    if args.ci_out:
        ghi_ung_vien_ci(args.ci_out, out, window)


if __name__ == "__main__":
    main()
