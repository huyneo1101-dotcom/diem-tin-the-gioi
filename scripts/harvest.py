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
import topics  # noqa: E402
import tap_tran  # noqa: E402
from topics import match_topic, us_subgroup, us_rank, neo_uc, neo_anh  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
VN = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")

# Google News: mỗi chủ đề một truy vấn. `when:2d` để Google lọc sẵn 2 ngày,
# ta vẫn lọc lại theo pubDate vì "2d" của Google rộng hơn khung của ta.
GNEWS_QUERIES = {
    "Úc & Biển Đông": [
        '"South China Sea" OR Scarborough OR "Second Thomas Shoal" OR "West Philippine Sea"',
        'AUKUS OR "Australian Defence Force" OR "Royal Australian Navy"',
        # ⚠️ KHÔNG QUÂN Úc từng là lỗ hổng CÂM: dòng trên chỉ có Navy, nên mọi tin của
        # Không quân Hoàng gia Úc (RAAF) — quân chủng chủ trì Pitch Black, kỳ tập trận
        # không chiến lớn nhất Nam bán cầu, 20 nước, 20/07–07/08/2026 tại Bắc Úc — không
        # có truy vấn nào bắt. Đo thật 02/08/2026: truy vấn dòng trên trả 0 kết quả cho
        # tin "KC-30A của Úc lần đầu tiếp dầu Rafale Ấn Độ" (Janes 31/07), trong khi hai
        # truy vấn dưới trả về đúng nó. Chủ đề 5 cũng không đỡ được vì nó neo cứng vào
        # "Predator's Run", tập trận đã kết thúc cuối tháng 7.
        '"Royal Australian Air Force" OR RAAF',
        '"Pitch Black" Australia exercise',
        # các nước khác quanh Biển Đông (mở rộng 27/07/2026 theo chỉ thị Huy)
        'Malaysia OR Indonesia OR Vietnam OR Taiwan maritime "South China Sea" patrol OR protest',
        '"code of conduct" ASEAN China sea OR Natuna OR "Vanguard Bank"',
        # CHIẾN TRANH VÙNG XÁM ở Biển Đông (chỉ thị Huy 02/08/2026). Mỗi truy vấn phải TỰ
        # NEO vào vùng biển này — để trần "gray zone" hay "water cannon" là kéo về cả vùng
        # xám Baltic, eo biển Đài Loan và vòi rồng biểu tình.
        '"South China Sea" "water cannon" OR ramming OR laser OR blockade OR "gray zone"',
        '"South China Sea" "maritime militia" OR "China Coast Guard" OR "land reclamation"',
        # Quân sự Úc nói chung, ngoài AUKUS và ngoài Biển Đông (chỉ thị Huy 02/08/2026)
        'Australia military OR defence exercise OR deployment OR "defence budget"',
        # ── NƯỚC ANH (mở phạm vi 01/09/2026, Huy chốt sau khi đưa mẫu file Word của cơ quan
        # có hẳn tiểu mục "Anh"). Mẫu 01/09 gồm cả tin quốc phòng (radar tàu Type 23, HMS
        # Tamar thăm Ream), kinh tế (Thống đốc Ngân hàng Anh cảnh báo bong bóng AI), chính
        # trường (Thủ tướng, Công đảng, thăm dò) và đối ngoại (đội phản ứng nhanh tới Nepal)
        # — nên phạm vi là "tin đáng chú ý về nước Anh", không riêng quốc phòng.
        # ⛔ MỖI TRUY VẤN PHẢI TỰ NEO VÀO ANH. "Royal Navy" để trần thì được (đặc chỉ Anh),
        # nhưng "Labour Party" hay "Treasury" để trần là kéo về cả Úc lẫn Mỹ.
        '"Royal Navy" OR "Royal Air Force" OR "UK Ministry of Defence" OR "British Army"',
        '"UK government" OR "British Prime Minister" OR "Downing Street" OR Westminster politics',
        '"Bank of England" OR "UK economy" OR "British economy"',
        '"UK foreign policy" OR "Britain sanctions" OR "British foreign secretary"',
    ],
    "CNQS Mỹ": [
        '"U.S. Air Force" OR "U.S. Navy" OR Pentagon missile OR hypersonic OR "Space Force"',
        '"defense contract" OR "awarded a contract" Pentagon',
    ],
    "Mỹ – Mali": ['Mali OR JNIM OR Sahel OR Bamako OR "Africa Corps"'],
    # ⛔ CHỦ ĐỀ 05 KHÔNG CÒN NEO CỨNG TÊN KỲ TẬP TRẬN (05/08/2026, chỉ thị Huy: *"đang có tập
    # trận nào thì chỉ tập trung quét thông tin về tập trận đó"*). Danh sách để RỖNG ở đây;
    # truy vấn thật sinh lúc chạy từ `DATA.exercises` qua `scripts/tap_tran.py::truy_van` và
    # được `nap_tap_tran_dang_chay()` bơm vào chính dict này. Nhờ vậy đổi kỳ tập trận không
    # phải sửa dòng mã nào — trước đây phải sửa đủ 05 chỗ và quên một chỗ là chủ đề câm.
    # ⚠️ CỐ Ý KHÔNG có `OR RAAF` trong truy vấn sinh ra (xem `tap_tran.truy_van`). Chủ đề này
    # giành URL TRƯỚC chủ đề 02 (xem UU_TIEN_CHU_DE), nên truy vấn rộng sẽ kéo mọi tin Không
    # quân Úc vào mục tập trận — tin RAAF không dính kỳ nào phải thuộc chủ đề 02.
    topics.CHU_DE_TAP_TRAN: [],
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

# Gán cứng chủ đề theo URL feed — cho những nguồn mà MỌI bài đều thuộc một chủ đề,
# nhưng tiêu đề không tự nhắc tên nước nên `match_topic` không neo được.
# ⛔ Vá 05/09/2026, đừng gỡ. Đo thật trên feed Atom Bộ Quốc phòng Anh: 20 item, chỉ 8
# item có chữ "UK"/"British"/"Royal Navy" ngay trong tiêu đề, 12 item còn lại rơi câm
# ("Key milestone reached for future Navy support ship", "Fast-paced funding for
# force-protection innovation", "CDLS Industry Commendations 2026"...). Đây là cùng một
# bệnh đã bắt được ở feed DoD Contracts ("Contracts for July 24, 2026" không chứa từ
# khoá nào) — chữa bằng cùng một thuốc. Tra theo URL chứ không theo tên vì tên trong
# bảng CLAUDE.md có đánh dấu in đậm, sửa bảng là hỏng câm.
# ⚠️ CHỈ nguồn chuyên một chủ đề mới được vào đây. BBC News UK và Guardian Politics
# CỐ Ý đứng ngoài: hai feed đó trộn thể thao, tội phạm địa phương, giải trí — gán cứng
# là kéo cả rác vào chủ đề.
FORCE_TOPIC_URL = {
    "gov.uk/search/news-and-communications.atom": "Úc & Biển Đông",
    "ukdefencejournal.org.uk": "Úc & Biển Đông",
    "navylookout.com": "Úc & Biển Đông",
    # ── 05 NGUỒN CHÍNH THỨC MỸ, thêm 05/09/2026 sau khi `scripts/soi_muc_cam.py` đo lần
    # đầu và bắt được đúng hình dạng câm đã tả ở trên. Số đo hôm ấy: Nhà Trắng 30 item ·
    # SEC 25 · FTC 10 · USTR 10 · BEA 11 — tổng 86 item sống, ngày đọc được 86/86, mà
    # **0 item neo được chủ đề nào**, tức 05 nguồn tầng 1 nằm trong bảng từ 27/07/2026 mà
    # chưa từng đóng góp một ứng viên nào. Nguyên nhân giống hệt gov.uk: tiêu đề thông cáo
    # không tự nhắc tên nước ("Supporting America's Ranchers", "SEC Charges San Francisco
    # Bay Area Private Fund Executives", "GDP (Second Estimate) and Corporate Profits").
    # Cả 05 đều là feed của MỘT cơ quan liên bang Mỹ, mọi item đều là hành động của chính
    # quyền Mỹ — đúng điều kiện "chuyên một chủ đề" nói ở trên, không phải feed trộn.
    "whitehouse.gov/presidential-actions": "Nội bộ Mỹ",
    "sec.gov/news/pressreleases": "Nội bộ Mỹ",
    "ftc.gov/feeds/press-release": "Nội bộ Mỹ",
    "ustr.gov/rss.xml": "Nội bộ Mỹ",
    "bea.gov/news/rss": "Nội bộ Mỹ",
}


def forced_topic(name: str, url: str):
    """Chủ đề gán cứng cho một feed, tra theo tên trước rồi tới URL."""
    t = FORCE_TOPIC.get(name)
    if t:
        return t
    for manh, chu_de in FORCE_TOPIC_URL.items():
        if manh in (url or ""):
            return chu_de
    return None


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


# ── LẤY NỘI DUNG: curl thường, bị chặn thì đi hết THANG của `congcu/lay_trang.py` ──
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
#
# 🪜 CẮM THANG 06 ĐƯỜNG 30/07/2026 (chỉ thị Huy) — trước bản này chỉ thử ĐÚNG một lượt
# curl_cffi khi bị chặn; nay bị chặn thì đi hết thang đã dựng ở `congcu/lay_trang.py`
# (curl_cffi → thử lại thưa nhịp → wayback → …, theo đúng cấu hình từng tên miền trong
# `bang-tra-web.json`). Đo thật khi cắm (đợt quét RSS+HTML 108 nguồn hôm đó, 6 nguồn
# hoàn toàn hỏng với "1 lượt curl_cffi"): thang cứu thêm `spaceforce.mil` (RSS, qua
# wayback — bản lưu còn nằm trong khung nới CNQS 3 ngày) và `navy.mil` (HTML, qua
# wayback — trang tươi). Còn `army.mil` / `af.mil` / `marines.mil` không cứu được hôm
# đó vì DNS zone `.mil` sập thật trong phiên đo (đúng bệnh "chập chờn" đã ghi ở
# CLAUDE.md) và bản lưu Wayback của chúng đã quá cũ (vài tháng, ngoài mọi khung ngày).
# Nhân đợt đo này bắt được một lỗi thật trong CHÍNH `lay_trang.py`: `duong_wayback()`
# thiếu modifier `id_` nên RSS/XML có lúc về đúng trang phát lại rỗng — đã vá tại nguồn
# (congcu/lay_trang.py), không vá riêng ở đây, vì mọi nơi dùng thang đều hưởng lợi.
#
# CHỈ CẮM ĐƯỢC Ở MÁY CÓ `~/Claude/congcu` (local) — CI (GitHub Actions) checkout đúng
# repo này, không có thư mục dùng chung đó, nên TỰ LÙI VỀ đúng logic cũ (1 lượt
# curl_cffi, hàm `_lay_bang_van_tay_chrome` giữ nguyên bên dưới). Đây là fail-open CÓ
# TIẾNG (in ra cuối phiên qua `bao_nguon_hong()`), không phải lỗ hổng: CI vốn đã đủ
# dùng plain curl_cffi cho hầu hết nguồn (chạy từ IP Mỹ), còn nguồn nào CI cần đường
# khác thì đã có cơ chế "Chạy ở = CI" riêng trong bảng CLAUDE.md.
CONGCU_DIR = "/Users/Huy/Claude/congcu"

DAU_HIEU_CHAN = (b"403 forbidden", b"error 403", b"access denied",
                 b"attention required", b"just a moment", b"request forbidden")

# Sổ ghi vết trong RAM: nguồn nào phải nhờ đường nào, nguồn nào chịu chết.
# `main()` in ra cuối — nguồn chết mà không ai kêu thì sống mãi (bài học cổng câm NFD).
VET_NGUON = {"cffi_va_duoc": [], "chan_ca_hai": [], "cffi_vang_mat": set(),
             "thang_cuu": {}}

_CFFI = None       # None = chưa thử import trực tiếp · False = máy không có curl_cffi
_LAY_TRANG = None  # None = chưa thử nạp thang · False = máy KHÔNG có `~/Claude/congcu`


def _nghi_bi_chan(body: bytes) -> bool:
    if not body:
        return True
    dau = body[:3000].lower()
    return any(d in dau for d in DAU_HIEU_CHAN)


def _lay_trang_module():
    """Nạp `congcu/lay_trang.py` một lần. Thiếu (đường không tồn tại, thường là CI) -> False.

    KHÔNG vendor một bản chép vào repo này — mục 14 CLAUDE.md toàn cục cấm hai bản của
    cùng một thứ (chắc chắn lệch, mà lệch âm thầm). Máy nào không có thư mục dùng chung
    này thì tự lùi về bản dự phòng `_lay_bang_van_tay_chrome` ngay bên dưới.
    """
    global _LAY_TRANG
    if _LAY_TRANG is None:
        try:
            if CONGCU_DIR not in sys.path:
                sys.path.insert(0, CONGCU_DIR)
            import lay_trang as _lt  # noqa: PLC0415
            _LAY_TRANG = _lt
        except ImportError:
            _LAY_TRANG = False
    return _LAY_TRANG


def _lay_bang_van_tay_chrome(url: str, timeout: int) -> bytes:
    """Một lượt curl_cffi thẳng — CHỈ dùng khi máy KHÔNG có thang (không có `congcu`, vd CI).

    Đây là bản dự phòng, không phải bản chính: máy có `congcu` đi qua thang đầy đủ trong
    `curl()` thay vì hàm này. Giữ lại để CI vẫn có đúng mức bảo vệ như trước khi cắm thang.

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

    lt = _lay_trang_module()
    if lt is False:
        # Không có `~/Claude/congcu` (CI, hoặc máy khác) -> lùi về đúng cách cũ.
        if _CFFI is False:
            VET_NGUON["cffi_vang_mat"].add(url)
            return body
        body2 = _lay_bang_van_tay_chrome(url, timeout)
        if _CFFI is False:      # vừa phát hiện thiếu thư viện ngay trong lượt này
            VET_NGUON["cffi_vang_mat"].add(url)
            return body
        if body2 and not _nghi_bi_chan(body2):
            VET_NGUON["cffi_va_duoc"].append(url)
            return body2
        VET_NGUON["chan_ca_hai"].append(url)
        return body

    # Có thang đầy đủ: curl_cffi -> thu_lai -> wayback -> … theo bang-tra-web.json.
    try:
        kq = lt.lay(url)
    except Exception:
        VET_NGUON["chan_ca_hai"].append(url)
        return body
    if kq["duong"] and kq["raw"] and not _nghi_bi_chan(kq["raw"]):
        if kq["duong"] == "curl_cffi":
            VET_NGUON["cffi_va_duoc"].append(url)
        else:
            VET_NGUON["thang_cuu"].setdefault(kq["duong"], []).append(url)
        return kq["raw"]
    if "curl_cffi" in (kq.get("vi_sao") or ""):   # thư viện vắng mặt ở MỌI bậc của thang
        VET_NGUON["cffi_vang_mat"].add(url)
        return body
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
    except ValueError:
        print("Không tìm thấy mục '## URL RSS' trong CLAUDE.md", file=sys.stderr)
        return []
    # Mục nguồn là mục CUỐI file thì không còn tiêu đề `##` nào phía sau — lấy tới hết file.
    # Trước 25/08/2026 chỗ này ném ValueError chung với nhánh trên rồi trả rỗng, tức MỌI feed
    # biến mất trong im lặng chỉ vì ai đó chuyển mục nguồn xuống cuối. Ca [10] của
    # tests/test-bang-nguon-claude-md.py canh đúng chiều này.
    if "\n## " in block[1:]:
        block = block[: block.index("\n## ", 1)]
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
    """Ngày đăng của một item feed, quy về múi giờ VN.

    ⛔ KHÔNG CẮT CHUỖI THEO ĐỘ DÀI CỐ ĐỊNH — đã vá 05/09/2026, đừng đưa lại.
    Bản cũ cắt `raw[:24]` theo mẫu `2026-07-27T00:00:00+0000` rồi mới đưa vào
    `strptime`. Múi giờ Atom viết dạng có dấu hai chấm (`+01:00`) dài 25 ký tự,
    nên bị cắt cụt thành `...+01:0` và `%z` trượt → hàm trả None. Hậu quả đo được
    05/09/2026: toàn bộ 20 item của feed Atom Bộ Quốc phòng Anh (gov.uk) — nguồn
    chính thức tầng 1 của tin nước Anh — luôn ra ngày "?", nên mọi phiên quét đều
    coi là không rõ ngày rồi loại; chủ đề "Úc, Anh & Biển Đông" mất nguồn Anh
    chính thức mà không phát ra tiếng nào. Đường đúng: `fromisoformat` trước
    (Python 3.11+ đọc được cả `Z` lẫn `+01:00`), `strptime` chỉ còn làm lưới hứng.
    """
    if not raw:
        return None
    raw = raw.strip()
    try:
        return email.utils.parsedate_to_datetime(raw).astimezone(VN).date()
    except Exception:
        pass
    try:
        d = datetime.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return d.astimezone(VN).date() if d.tzinfo else d.date()
    except Exception:
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            d = datetime.datetime.strptime(raw[:len("2026-07-27T00:00:00+0000")], fmt)
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
        forced = forced_topic(name, url)
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
    thang_cuu = VET_NGUON.get("thang_cuu", {})

    lt = _lay_trang_module()
    print(f"\n🪜 Thang lấy trang bị chặn: {'ĐANG DÙNG (' + CONGCU_DIR + ')' if lt else ('KHÔNG có — máy thiếu `' + CONGCU_DIR + '`, đã lùi về 1 lượt curl_cffi (CI là ca bình thường)' if lt is False else 'chưa nguồn nào cần tới')}")
    if cffi_va:
        print(f"\n🔓 {len(cffi_va)} nguồn phải lấy bằng VÂN TAY TLS Chrome (curl trần bị chặn):")
        for u in cffi_va:
            print(f"     {u[:130]}")
    for duong, ds in thang_cuu.items():
        print(f"\n🪜 {len(ds)} nguồn CỨU ĐƯỢC nhờ bậc `{duong}` của thang (curl_cffi trần cũng chặn):")
        for u in ds:
            print(f"     {u[:130]}")
    if thieu_cffi:
        print(f"\n⚠️  {len(thieu_cffi)} nguồn bị chặn mà máy KHÔNG có `curl_cffi` để thử lại — "
              f"đang mất tin. Cài:  python3 -m pip install --user curl_cffi")
        for u in sorted(thieu_cffi)[:10]:
            print(f"     {u[:130]}")
    if chan:
        print(f"\n⛔ {len(chan)} nguồn chặn HẾT MỌI ĐƯỜNG đã thử:")
        for u in chan:
            print(f"     {u[:130]}")
    if rong:
        print(f"\n⛔ {len(rong)} FEED RSS TRẢ 0 ITEM — nghi chết hoặc đổi URL, "
              f"kiểm bằng `python3 scripts/kiem_nguon.py`:")
        for ten, u in rong:
            print(f"     {ten} — {u[:120]}")
    if not (rong or chan or thieu_cffi):
        print("\n✅ Mọi feed đều trả item; không nguồn nào bị chặn hết mọi đường.")


# Thứ tự GIÀNH URL khi hai chủ đề cùng bắt được một bài. Khâu gộp cuối khử trùng theo URL
# trên TOÀN lô, nên bài nào tới trước thì chủ đề đó giữ; chủ đề tới sau mất bài đó vĩnh viễn.
#
# ⚠️ CƠ CHẾ GÂY VẤP (đo thật 02/08/2026) — vì sao phải khai tường minh chứ không dựa vào thứ
# tự khai trong GNEWS_QUERIES: ngày 02/08 chủ đề 02 được thêm truy vấn `"Pitch Black"
# Australia exercise` (để bắt tin Không quân Úc), mà trong dict chủ đề 02 đứng TRƯỚC chủ đề
# 05. Từ đó mọi tin Pitch Black bị chủ đề 02 ăn trước, và chủ đề 05 báo **0 bài mỗi phiên**
# trong khi truy vấn của nó vẫn trả về 5–8 tin đúng khung ngày. Không lỗi, không cảnh báo:
# bảng vẫn đủ 5 dòng, dòng cuối chỉ ghi "(không có ứng viên nào)" — đọc vào tưởng hôm đó
# không có tin. Dựa vào thứ tự dict là mong manh gấp đôi, vì người sau sắp lại dict cho gọn
# sẽ dựng lại đúng lỗ này mà không hay.
#
# Nguyên tắc xếp: chủ đề HẸP đứng trước chủ đề RỘNG. Mục tập trận là hẹp nhất (một kỳ tập
# trận đang chạy, nạp qua `exerciseUpdates` vào đúng thẻ), nên nó giành trước mục 02.
# Chủ đề không có tên trong danh sách này thì xuống cuối, giữ nguyên thứ tự tương đối.
UU_TIEN_CHU_DE = (topics.CHU_DE_TAP_TRAN, "Mỹ – Mali", "CNQS Mỹ", "Úc & Biển Đông", "Nội bộ Mỹ")


def nap_tap_tran_dang_chay(hom_nay, im=False):
    """Bơm cuộc tập trận ĐANG diễn ra vào bảng chủ đề + bảng truy vấn. Trả danh sách cuộc.

    Chỉ thị Huy 05/08/2026: *"Đang có tập trận nào thì chỉ tập trung quét thông tin về tập
    trận đó. Tự động mở rộng nguồn quét tuỳ theo tập trận."* Gọi NGAY ĐẦU `main()`, trước mọi
    lớp quét — bơm sau là lớp RSS/HTML đã phân loại xong bằng bảng rỗng.

    Fail-OPEN có tiếng: không có cuộc nào (hoặc đọc `index.html` hỏng) thì chủ đề 05 im lặng
    đúng như trước, nhưng in một dòng nói rõ vì sao — im hẳn thì không phân biệt được "hôm nay
    giữa hai kỳ tập trận" với "đường đọc DATA đã hỏng".
    """
    try:
        exs = tap_tran.doc_exercises()
        dang = tap_tran.dang_dien_ra(exs, hom_nay)
    except Exception as e:                                    # pragma: no cover
        print(f"⚠️  không đọc được DATA.exercises ({e}) — chủ đề tập trận sẽ trống",
              file=sys.stderr)
        return []
    keys, qs = [], []
    for ex in dang:
        keys.extend(tap_tran.tu_khoa(ex))
        qs.extend(tap_tran.truy_van(ex))
    topics.nap_tu_khoa_tap_tran(keys)
    GNEWS_QUERIES[topics.CHU_DE_TAP_TRAN] = qs
    if not im:
        if dang:
            print(f"🎖️  Tập trận đang bám: {tap_tran.tom_tat(dang)}", file=sys.stderr)
            print(f"    từ khoá: {', '.join(keys)}", file=sys.stderr)
            print(f"    truy vấn: {' | '.join(qs)}", file=sys.stderr)
            dom = tap_tran.nguon_mo_rong(dang)
            print(f"    nguồn bản địa nên ưu tiên ({len(dom)}): {', '.join(dom[:12])}"
                  + (" …" if len(dom) > 12 else ""), file=sys.stderr)
        else:
            print("🎖️  KHÔNG có cuộc tập trận nào đang/sắp diễn ra trong DATA.exercises — "
                  "chủ đề tập trận sẽ trống (đúng, không phải lỗi)", file=sys.stderr)
    return dang


CHU_DE_DIA_BAN = "Úc & Biển Đông"
# Ba nhánh của chủ đề 2, ĐÚNG thứ tự giành của `make_docx.tieu_muc_dia_ban` (Úc trước Anh:
# tin dính cả hai gần như luôn là AUKUS, thuộc về Úc). Dùng chung `neo_uc`/`neo_anh` của
# `topics.py` — cùng một phép neo với tầng xuất bản, nên hạn ngạch ở đây khớp đúng với tiểu
# mục người đọc thấy trong file Word.
NHANH_DIA_BAN = ("Australia", "Anh", "Biển Đông")


def nhanh_dia_ban(tieu_de: str) -> str:
    if neo_uc(tieu_de):
        return "Australia"
    if neo_anh(tieu_de):
        return "Anh"
    return "Biển Đông"


def sap_ung_vien(topic: str, lst: list) -> list:
    """Thứ tự in ứng viên của MỘT chủ đề — quyết định 20 bài nào agent được nhìn thấy.

    ⛔ KHÔNG SẮP THEO CHUỖI NGÀY — đã vá 05/09/2026, đừng đưa lại. Bản cũ dùng
    `sorted(lst, key=lambda x: x["ngay"], reverse=True)`, mà `ngay` là CHUỖI và tin không
    đọc được ngày mang giá trị `"?"`. Ký tự `?` (0x3F) lớn hơn `2` (0x32), nên `reverse=True`
    đẩy TOÀN BỘ tin ngày `?` lên ĐẦU danh sách — đúng nhóm tin mà agent loại thẳng vì không
    rõ ngày. Đo trên lô ứng viên thật phiên tối 05/09/2026: **13/20 slot** của chủ đề 2 bị
    tin ngày `?` chiếm (08 bài gov.uk cộng 05 bài rác thuần: bóng đá, El Nino, phim outback),
    chỉ còn 07 slot cho tin có ngày thật. Hỏng câm hoàn hảo: danh sách vẫn đủ 20 dòng.

    ⛔ VÀ PHẢI CẤP HẠN NGẠCH CHO TỪNG NHÁNH ĐỊA BÀN. Sửa phép sắp xếp thôi KHÔNG đủ — đo lại
    cùng lô đó: hai bài UK Defence Journal có ngày thật (*"British aircraft carrier deploying
    to deter Russia"*, *"British warship fires gun near Falklands"*) chỉ nhích từ hạng 37-38
    lên **24-25/46**, vẫn nằm ngoài trần 20, và số nguồn Anh có ngày thật lọt tầm nhìn vẫn là
    **0**. Nguyên nhân: chủ đề 2 gộp ba địa bàn có sản lượng lệch hẳn nhau — tin Biển Đông,
    Philippines, Đài Loan đăng dày mỗi ngày, tin Anh thưa và hay rơi vào ngày hôm qua — nên
    xếp thuần theo ngày là nhánh thưa bị dìm có hệ thống. Đây đúng cơ chế mà chính hàm này
    đã phải vá cho "Nội bộ Mỹ" (xem chú thích dưới: *"nhóm đăng dày chiếm hết chỗ"*), chỉ
    khác mảng. Trộn LUÂN PHIÊN theo nhánh thì nhánh nào cũng có chỗ, và nhánh cạn bài thì tự
    nhường phần còn lại — không phải cấp phát cứng.

    Sàn 02 tin mỗi mục (Huy chốt 05/09/2026) đứng hay đổ ở chính hàm này: agent không nhìn
    thấy bài thì không có cách nào nạp, và mọi cổng phía sau chỉ đo được cái đã nạp.
    """
    if topic == "Nội bộ Mỹ":
        # Xếp theo HẠNG ưu tiên trước, ngày sau. Huy chốt 27/07: vét cạn nhóm (1) điều trần
        # + bỏ phiếu rồi mới tới các nhóm còn lại — và bốn nhóm còn lại NGANG NHAU
        # (2 sáng kiến/chiến lược · 3 biểu tình · 4 kinh tế+nội các · 5 bầu cử), nên xếp
        # theo `us_rank` chứ KHÔNG theo số nhóm; xếp theo số nhóm sẽ dìm bầu cử xuống cuối.
        # Xếp thuần theo ngày cũng hỏng: nhóm đăng dày (biểu tình/bầu cử/thuế quan) chiếm hết chỗ.
        for h in lst:
            h["nhom"] = us_subgroup(h["tieu_de"])
        return sorted(lst, key=lambda x: (us_rank(x["nhom"]), x["ngay"] == "?",
                                          -_daykey(x["ngay"])))
    if topic == CHU_DE_DIA_BAN:
        theo_nhanh = {n: [] for n in NHANH_DIA_BAN}
        for h in sorted(lst, key=lambda x: (x["ngay"] == "?", -_daykey(x["ngay"]))):
            theo_nhanh[nhanh_dia_ban(h["tieu_de"])].append(h)
        ra = []
        for i in range(max(len(v) for v in theo_nhanh.values()) if lst else 0):
            for n in NHANH_DIA_BAN:
                if i < len(theo_nhanh[n]):
                    ra.append(theo_nhanh[n][i])
        return ra
    return sorted(lst, key=lambda x: (x["ngay"] == "?", -_daykey(x["ngay"])))


def uu_tien_chu_de(hits):
    """Sắp lô ứng viên theo UU_TIEN_CHU_DE trước khi khử trùng URL.

    Sort ỔN ĐỊNH: trong cùng một chủ đề, thứ tự cũ giữ nguyên — đó là điều kiện để lô local
    vẫn đứng trước lô CI (xem chú thích ở chỗ gộp `doc_ung_vien_ci`), và để bản đầu của một
    sự kiện vẫn là bản được giữ khi `same_story` loại các bản sau.
    """
    thu_tu = {t: i for i, t in enumerate(UU_TIEN_CHU_DE)}
    return sorted(hits, key=lambda h: thu_tu.get(h.get("chu_de"), len(thu_tu)))


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

    # Bơm cuộc tập trận đang chạy TRƯỚC mọi lớp quét — bơm sau thì lớp RSS/HTML đã phân loại
    # xong bằng bảng từ khoá rỗng và mọi tin tập trận rơi sang chủ đề khác (hoặc rớt hẳn).
    nap_tap_tran_dang_chay(str(today))

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
    hits = uu_tien_chu_de(hits)
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
    for topic in ("Nội bộ Mỹ", "Úc & Biển Đông", "CNQS Mỹ", "Mỹ – Mali",
                  topics.CHU_DE_TAP_TRAN):
        lst = by_topic.get(topic, [])
        extra = f" — in {PER_TOPIC_CAP} bài" if len(lst) > PER_TOPIC_CAP else ""
        print(f"\n-- {topic} ({len(lst)} bài{extra}) --")
        if not lst:
            print("   (không có ứng viên nào trong khung hôm nay + hôm qua)")
        ordered = sap_ung_vien(topic, lst)
        if topic == "Nội bộ Mỹ":
            print("   (hạng 1 = nhóm 1 điều trần+bỏ phiếu, vét trước; "
                  "nhóm 2/3/4/5 NGANG NHAU, xếp theo ngày)")
        elif topic == CHU_DE_DIA_BAN:
            print("   (trộn LUÂN PHIÊN 03 nhánh Australia · Anh · Biển Đông để nhánh thưa "
                  "không bị nhánh đăng dày dìm khỏi trần in — sàn 02 tin mỗi mục)")
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
