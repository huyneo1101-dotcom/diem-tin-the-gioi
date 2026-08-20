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
  python3 scripts/add_analyses.py --candidates-dai  # BÀI DÀI: chỉ feed nghiên cứu, khung THÁNG
  python3 scripts/do_nguon_mot_muc.py               # dò nguồn nghi chỉ khai một mục

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
import concurrent.futures
import datetime
import email.utils
import html as html_mod
import json
import pathlib
import re
import subprocess
import sys
import urllib.parse
import xml.etree.ElementTree as ET
import zoneinfo

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import analyses_store  # noqa: E402

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
    # Institute for the Study of War — thêm 29/07/2026 khi rà nhãn `outlet` của DATA.analyses.
    # Viện thật (CLAUDE.md xếp @TheStudyofWar vào nhóm phân tích/OSINT tầng 3), nhưng domain là
    # `understandingwar.org` chứ không phải "isw.*" nên trước giờ lọt khỏi danh sách — guardrail
    # domain đang CHẶN OAN mọi bài ISW mới. Bài ISW cũ trong DATA vì thế được GIỮ, không phải xoá.
    "understandingwar.org",
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
    # `agsi.org` là tên miền MỚI của AGSIW (đổi tên viện, agsiw.org redirect sang đó) — giữ CẢ
    # HAI: bài cũ trong kho còn mang url agsiw.org, gỡ đi là guardrail chặn oan chính chúng.
    "mei.edu", "washingtoninstitute.org", "agsiw.org", "agsi.org", "carnegie-mec.org",
    "epc.ae", "gulfif.org",
    # Châu Phi · Sahel
    "africacenter.org", "saiia.org.za", "timbuktu-institute.org",
    # Mỹ Latin
    "wola.org", "dialogo-americas.com", "thedialogue.org",
    # Nam Á · Trung Á
    "idsa.in", "takshashila.org.in", "cacianalyst.org", "sipa.columbia.edu",
    # South Asian Voices — nền tảng của Stimson Center dành riêng cho cây bút Nam Á, tên miền
    # RIÊNG nên `stimson.org` không phủ được. Thêm 06/08/2026 cùng feed ở THINKTANK_FEEDS.
    "southasianvoices.org",
    # Đông Bắc Á · Đông Nam Á
    "jiia.or.jp", "spf.org", "tokyofoundation.org", "sejong.org", "fulcrum.sg",
    # Sasakawa Peace Foundation USA (Washington DC) — thêm 29/07/2026. Danh sách đã có `spf.org`
    # (quỹ mẹ ở Nhật) nhưng nhánh Mỹ xuất bản dưới domain RIÊNG `spfusa.org`, nên bài của họ
    # bị chặn oan. Cùng một quỹ, hai domain — đừng gộp bằng cách sửa `spf.org` thành hậu tố.
    "spfusa.org",
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
#
# ══ MỘT VIỆN CÓ THỂ CÓ HAI FEED: BLOG và NGHIÊN CỨU — hậu tố `[NC]` (thêm 06/08/2026) ══
# Phần lớn viện lớn xuất bản ở HAI nhịp khác nhau, và mỗi nhịp một feed riêng:
#   · BLOG — bình luận ngắn, ra hằng ngày. Lowy `the-interpreter` · ASPI `aspistrategist.org.au`
#     · RUSI `latest-commentary` · CSET `/feed/`.
#   · NGHIÊN CỨU — báo cáo dài, ra theo THÁNG. Lowy `/publications/` · ASPI `/report/`
#     · RUSI `/explore-our-research/` · CSET `/publication/`.
#
# CƠ CHẾ GÂY VẤP — bảng này khai đúng MỘT feed cho mỗi viện, và cái được khai luôn là feed
# BLOG (nó dễ tìm hơn, nằm ngay trang chủ). Hậu quả **không phát ra dấu hiệu nào**: feed blog
# vẫn ra bài đều mỗi ngày, danh sách ứng viên vẫn đầy, mục Think-tank trên web vẫn có bài mới
# mỗi sáng — nên không ai có lý do đi hỏi "còn thiếu gì". Đo trên `data/analyses.json` ngày
# 06/08/2026: **35/35 bài Lowy thuộc `/the-interpreter/`, 0 bài `/publications/`**; **81/81
# bài ASPI thuộc blog, 0 bài `aspi.org.au`**. Tức toàn bộ mảng BÁO CÁO của hai viện đầu ngành
# về Úc và Ấn Độ Dương - TBD chưa từng vào kho, suốt từ ngày dựng. Chỉ lộ ra khi Huy đi tìm
# một nghiên cứu cụ thể mà không thấy.
#
# ⚠️ Feed blog PHẢI GIỮ NGUYÊN — đây là THÊM mục nghiên cứu, không phải thay blog bằng nghiên
# cứu. Thay là mất ~35 bài Interpreter mỗi năm, tức vá một lỗ bằng cách mở một lỗ to hơn.
# ⚠️ Bốn feed `[NC]` đã FETCH THẬT 06/08/2026 (200 · lần lượt 50 · 10 · 20 · 10 item) và đã
# kiểm là chúng ra bài ở mục KHÁC với feed blog cùng viện — hai feed cùng viện mà ra chung một
# mục thì khai thêm chẳng được gì.
# ⚠️ ĐÃ THỬ VÀ CHẾT, ĐỪNG DÒ LẠI (đo 06/08/2026): `aspi.org.au/rss.xml` 403 ·
# `aspi.org.au/publications/feed` 403 · `rand.org/pubs.xml` 200 nhưng 0 item ·
# `rand.org/research.xml` 500 · `rusi.org/rss/latest-research.xml` 404 · `heritage.org/rss/reports`
# 403 · `cepa.org/comprehensive-reports/feed/` 404.
THINKTANK_FEEDS = [
    # — Ấn Độ Dương - Thái Bình Dương / Đông Á
    ("Lowy Institute", "https://www.lowyinstitute.org/the-interpreter/rss.xml", "Ấn Độ Dương - TBD"),
    ("Lowy Institute [NC]", "https://www.lowyinstitute.org/publications/rss.xml",
     "Ấn Độ Dương - TBD · nghiên cứu"),
    ("ASPI", "https://www.aspistrategist.org.au/feed/", "Úc · Ấn Độ Dương - TBD"),
    ("ASPI [NC]", "https://www.aspi.org.au/feed/", "Úc · Ấn Độ Dương - TBD · nghiên cứu"),
    # ASPI mục BÌNH LUẬN — thêm 07/08/2026 sau khi `do_nguon_mot_muc.py` nêu `aspi.org.au`
    # (10/10 bài đều `/report/`). Đúng hình dạng lỗ Lowy, và lần này lộ ra một biến thể mới:
    # ASPI chạy WordPress với KIỂU BÀI RIÊNG, mà `/feed/` của WordPress theo mặc định CHỈ trả
    # kiểu `post` — ở đây `post` chính là `/report/`. Nên feed đã khai chạy tốt, ra bài đều,
    # 200 mọi lượt, mà mảng `/opinions/` thì chưa từng có đường vào nào.
    # ⚠️ THAM SỐ PHẢI LÀ SỐ NHIỀU `opinions`, đúng `slug` trong `/wp-json/wp/v2/types`. Thử
    # `?post_type=opinion` (số ít) thì WordPress **lặng lẽ bỏ qua tham số và trả feed mặc
    # định** — 200, 10 item, nhìn y hệt feed đúng, chỉ là vẫn đủ 10 bài `/report/` cũ. Đây là
    # kiểu trượt tệ nhất khi dò feed: không lỗi, không rỗng, chỉ sai. Dò kiểu bài thì đọc
    # `/wp-json/wp/v2/types` rồi lấy `slug`, đừng đoán từ tên mục trên thanh điều hướng.
    # ⚠️ Đã fetch thật 07/08: 200 · 10 item · bài mới 16/07/2026 · cả 10 đều `/opinions/`.
    # ⚠️ KHÔNG khai `?post_type=news` (cũng 200 · 10 item · mới 30/07): đó là thông cáo nội bộ
    # của viện (ra mắt chương trình, cập nhật bộ dữ liệu), không phải bài phân tích.
    ("ASPI [BL]", "https://www.aspi.org.au/feed/?post_type=opinions",
     "Úc · Ấn Độ Dương - TBD · bình luận"),
    ("Fulcrum (ISEAS)", "https://fulcrum.sg/feed/", "Đông Nam Á"),
    ("MERICS", "https://merics.org/en/rss", "Trung Quốc"),
    ("Interpret China (CSIS)", "https://interpret.csis.org/feed/", "Trung Quốc"),
    # ChinaPower (CSIS) — thêm 06/08/2026 khi dựng `scripts/do_nguon_hai_mien.py`. CSIS xuất bản
    # dưới BỐN tên miền (`csis.org` · `amti` · `interpret` · `chinapower`), ba cái đầu đã có
    # đường quét còn `chinapower.csis.org` thì chưa — đúng hình dạng lỗ mà phép đo đó dò.
    # ⚠️ Viện này đăng THƯA (~1 bài/tháng: 06/07 · 30/04 · 24/02 · 12/02 · 05/02 · 13/01 năm
    # 2026) nên thường nằm trong dòng "feed không ra bài" của `--candidates` — đó là bình
    # thường, không phải feed hỏng. Cùng loại với USIP.
    # ⚠️ Feed này xếp item KHÔNG theo thời gian (WordPress đẩy bài ghim lên trước, item cũ nhất
    # từ 2016 nằm lẫn giữa bài 2026). Không sao vì `loc_ung_vien_feed` lọc theo `pubDate` chứ
    # không theo vị trí — nhưng đừng đọc item đầu feed thành "bài mới nhất".
    # ⚠️ Hai bài mới nhất là bài ĐĂNG CHÉO, link trỏ sang `www.csis.org` và
    # `scstradedashboard.csis.org`. Cái sau KHÔNG có trong THINKTANK_DOMAINS nên guardrail domain
    # sẽ chặn lúc nạp — chặn đúng, đó là trang bảng số liệu chứ không phải bài phân tích.
    ("ChinaPower (CSIS)", "https://chinapower.csis.org/feed/", "Trung Quốc"),
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
    # — Nam Á · Bắc Cực (thêm 06/08/2026 — Huy hỏi "sao mục think-tank ít bài Nam Á/châu Phi/
    # Trung Á/Bắc Cực thế"). Đo trên kho 616 bài hôm đó: Nam Á 01 · Trung Á 01 · Bắc Cực 04 ·
    # Châu Phi 07, trong khi Châu Âu/NATO 188 · Đông Á 174. Nguyên nhân đo được là bảng feed
    # KHÔNG có viện chuyên nào của Nam Á và Bắc Cực — hai vùng đó chỉ có bài khi một viện
    # Anh-Mỹ-Úc tình cờ viết tới. ORF thì đã có ở THINKTANK_HTML nhưng chỉ nhánh expert-speak.
    # ⚠️ FETCH THẬT 06/08/2026 trước khi khai, và ĐÃ THỬ-ĐÃ CHẾT thì ghi ở khối dưới bảng.
    ("South Asian Voices (Stimson)", "https://southasianvoices.org/feed/", "Nam Á"),
    # FIIA + ICDS: hai viện Bắc Âu/Baltic có mảng Bắc Cực. KHÔNG phải viện chuyên Bắc Cực —
    # viện chuyên duy nhất (thearcticinstitute.org) chặn theo vân tay TLS ở MỌI bậc của thang
    # `congcu/lay_trang.py`, chỉ còn đường trình duyệt, mà trình duyệt chỉ có ở phiên local nên
    # cắm vào đây là lớp quét ra kết quả khác nhau giữa local và CI.
    ("FIIA (Phần Lan)", "https://www.fiia.fi/en/feed", "Bắc Âu · Bắc Cực"),
    ("ICDS (Estonia)", "https://icds.ee/en/feed/", "Baltic · Bắc Cực"),
    ("Crisis Group", "https://www.crisisgroup.org/rss.xml", "Xung đột toàn cầu"),
    # RUSI — CÓ RSS, đo lại 30/07/2026 (20 item, bài mới 1 ngày). Trước đó bị xếp nhầm vào
    # WEBSEARCH_ONLY vì chỉ thử `/feed/` + `/rss.xml`; feed thật nằm ở `/rss/latest-commentary.xml`,
    # tìm ra bằng cách đọc thẻ <link rel=alternate> trong HTML trang chủ. Cùng bài học với UN News
    # (thiếu --compressed) và War on the Rocks (thiếu -A): đừng gạch một nguồn khi chưa dò hết
    # đường vào.
    ("RUSI", "https://www.rusi.org/rss/latest-commentary.xml", "Anh · chiến lược"),
    ("RUSI [NC]", "https://www.rusi.org/rss/latest-publications.xml", "Anh · chiến lược · nghiên cứu"),
    # CACI Analyst + USIP — hai feed ẩn tìm được 30/07/2026 bằng cách đọc thẻ
    # `<link rel="alternate">` trên trang chủ, cùng đường đã tìm ra feed RUSI. Cả hai vùng này
    # trước đó KHÔNG có nguồn tự động nào: Trung Á - Caucasus trắng hoàn toàn.
    # ⚠️ CACI: phải là `/publications/analytical-articles.feed` (10 item, bài mới 13/07). Feed ở
    # trang chủ (`/?format=feed`) CÓ trả 200 nhưng đứng từ 2012 — nhìn giống nhau, khác hẳn nhau.
    ("CACI Analyst", "https://www.cacianalyst.org/publications/analytical-articles.feed",
     "Trung Á · Caucasus"),
    # CACI mục FEATURE ARTICLES — thêm 07/08/2026, cùng lượt với ASPI [BL], sau khi
    # `do_nguon_mot_muc.py` nêu `cacianalyst.org` (6/6 bài đều `analytical-articles`).
    # Đã fetch thật: 200 · 10 item · bài mới 25/06/2026.
    # ⚠️ Viện này có 04 mục và KHÔNG mục nào tự khai feed trong thẻ <link rel="alternate">;
    # đường vào là ghép `.feed` vào sau đường dẫn mục, đúng lối đã tìm ra feed analytical.
    # ⚠️ CỐ Ý KHÔNG khai `publications/field-reports.feed` dù nó CŨNG trả 200 và cũng là RSS
    # hợp lệ: bài mới nhất của nó là **03/10/2016**, tức mục đã ngừng xuất bản gần một thập
    # niên. Khai vào thì mỗi lượt quét lại kéo tin 2016 vào hàng ứng viên. Cùng bẫy đã ghi cho
    # feed trang chủ CACI (`/?format=feed`, 200 nhưng đứng từ 2012): **feed sống và feed chết
    # trả về cùng một mã 200, phải đọc `pubDate` mới phân biệt được.**
    ("CACI Analyst [FA]", "https://www.cacianalyst.org/publications/feature-articles.feed",
     "Trung Á · Caucasus · chuyên đề"),
    # ⚠️ USIP đăng THƯA (bài mới nhất lúc thêm đã 35 ngày tuổi) nên thường xuyên nằm trong dòng
    # "feed không ra bài" — đó là bình thường, không phải feed hỏng.
    ("USIP", "https://www.usip.org/feed/", "Xung đột · hoà giải"),
    # — Mỹ · quốc phòng · xuyên suốt
    ("Atlantic Council", "https://www.atlanticcouncil.org/feed/", "Toàn cầu"),
    ("War on the Rocks", "https://warontherocks.com/feed/", "Chiến lược quân sự"),
    ("RAND", "https://www.rand.org/blog.xml", "Toàn cầu"),
    ("Hudson Institute", "https://www.hudson.org/rss.xml", "Mỹ · châu Á"),
    ("Heritage Foundation", "https://www.heritage.org/rss", "Mỹ"),
    ("CSET", "https://cset.georgetown.edu/feed/", "AI · công nghệ"),
    ("CSET [NC]", "https://cset.georgetown.edu/publications/feed/", "AI · công nghệ · nghiên cứu"),
    ("Modern War Institute", "https://mwi.westpoint.edu/feed/", "Tác chiến"),
    ("Small Wars Journal", "https://smallwarsjournal.com/feed", "Xung đột phi quy ước"),
    ("CIMSEC", "https://cimsec.org/feed/", "Hải quân · biển"),
    ("Arms Control Association", "https://www.armscontrol.org/rss.xml", "Hạt nhân · kiểm soát vũ khí"),
    # ══ Bổ sung 20/08/2026 — 05 viện NẰM SẴN trong THINKTANK_DOMAINS mà chưa từng có đường quét ══
    # CƠ CHẾ GÂY VẤP, đo 20/08: `THINKTANK_DOMAINS` có **35 domain** không xuất hiện ở
    # THINKTANK_FEEDS, THINKTANK_HTML lẫn WEBSEARCH_ONLY. Guardrail nạp cho chúng đi qua, nên
    # nhìn danh sách thì tưởng đã phủ; thực tế KHÔNG lớp nào quét về, và cũng không lớp nào giục
    # WebSearch. Trong đó có `cfr.org` — viện đối ngoại lớn nhất của Mỹ, feed 24 item ra bài mỗi
    # ngày, chưa từng vào kho. Đây là hỏng câm ở tầng danh sách chứ không ở tầng mã.
    # ⚠️ PHÉP ĐO PHẢI GIỮ: `THINKTANK_DOMAINS trừ (FEEDS ∪ HTML ∪ WEBSEARCH_ONLY)` — thêm domain
    # vào guardrail mà quên khai đường vào là lỗi không phát ra dấu hiệu nào.
    ("CFR", "https://www.cfr.org/feed/", "Mỹ · đối ngoại"),
    # ⚠️ FDD: phải là nhánh `category/analysis`, KHÔNG dùng `/feed/` gốc. Feed gốc trả 50 item
    # nhưng 32 nằm ở `/in_the_news/` — điểm báo, mà đường dẫn viết bằng gạch DƯỚI nên NOISE_PATHS
    # (`/in-the-news/`, gạch ngang) không chặn được. Nhánh này trả 50/50 dưới `/analysis/`.
    ("FDD", "https://www.fdd.org/category/analysis/feed/", "Trung Đông · Iran"),
    # Inter-American Dialogue — LẤP VÙNG MỸ LATIN, trước nay trắng hoàn toàn: `wola.org` 403 mọi
    # đường, `dialogo-americas.com` là tạp chí của Bộ Tư lệnh Miền Nam Hoa Kỳ (báo chí quân đội,
    # không phải viện). Feed này 10/10 bài dưới `/blogs/` của chính viện.
    ("Inter-American Dialogue", "https://thedialogue.org/feed", "Mỹ Latin"),
    # ⚠️ Elcano: dùng bản `/en/feed/` (tiếng Anh). Feed gốc `/feed/` cũng sống nhưng ra bài tiếng
    # Tây Ban Nha.
    ("Real Instituto Elcano", "https://www.realinstitutoelcano.org/en/feed/", "Nam Âu · Tây Ban Nha"),
    # ⚠️ SPF USA: phải là `/publications/feed/`, KHÔNG dùng `/feed/` gốc — sửa 21/08/2026 sau
    # khi `do_nguon_mot_muc.py` tố tên miền này. Câu ghi hôm 20/08 ("viện đăng RẤT thưa, bài mới
    # nhất đã 5 tháng tuổi") là kết luận SAI rút từ nhánh sai: feed gốc trả 12 item toàn
    # `/spfusa-news/` và `/congressional-outreach/`, tức tin nội bộ và chương trình quốc hội,
    # bài mới nhất 21/03/2026; còn `/publications/feed/` trả 12/12 item dưới `/publications/`
    # với bài mới nhất 01/08/2026. Viện ra bài đều, chỉ là đường vào khai nhầm nhánh — đúng
    # hình dạng Lowy và ASPI.
    # ⛔ Cố ý KHÔNG giữ thêm feed gốc: khác ca ASPI (ở đó cả blog lẫn báo cáo đều là nghiên cứu
    # của viện nên giữ cả hai), nhánh gốc ở đây là tin hoạt động chứ không phải nghiên cứu —
    # cùng loại với các feed điểm báo đã bỏ ngay phía dưới.
    ("SPF USA", "https://www.spfusa.org/publications/feed/", "Nhật - Mỹ"),
    # ══ Bổ sung 21/08/2026 — 02 feed DANH MỤC CON, đường mà vòng dò 20/08 không đi tới ══
    # CƠ CHẾ GÂY VẤP: vòng dò hôm trước hỏi `<link rel=alternate>` + `/feed/` + `/rss.xml`, tức
    # chỉ hỏi feed GỐC. Với WordPress, feed gốc trả kiểu bài `post`, còn ấn phẩm chính của viện
    # lại nằm dưới một CHUYÊN MỤC — và `/<category>/feed/` thì không lối dò nào ở trên chạm tới.
    # Cùng họ với bài học ASPI (`?post_type=` cho kiểu bài riêng), chỉ khác trục: ở đó là KIỂU
    # BÀI, ở đây là CHUYÊN MỤC.
    # ⚠️ `iseas.edu.sg/feed/` trả **108 KB nhưng 0 item** — nó phát HTML chứ không phát RSS, nên
    # phép dò chỉ đếm mã 200 sẽ đọc thành "có feed" còn phép dò đếm item đọc thành "không có
    # feed"; cả hai đều dẫn tới kết luận sai là ISEAS không có đường feed nào.
    ("ISEAS (Yusof Ishak)", "https://www.iseas.edu.sg/category/articles-commentaries/feed/",
     "Đông Nam Á"),
    # GulfIF: feed gốc SỐNG (10 item, bài mới trong ngày, 10/10 là nghiên cứu của chính viện —
    # không phải điểm báo). Vòng dò 20/08 chấm nó "không feed"; đo lại 21/08 thì trả 113 KB/10
    # item. Nghi là lượt dò hôm đó trượt tạm. Bài học: một lượt dò trượt KHÔNG đủ để gạch tên
    # nguồn — cùng luật đã ghi cho `probe_sources.py` (đo lại lẻ, tuần tự).
    ("Gulf International Forum", "https://gulfif.org/feed/", "Vùng Vịnh"),
    # ⛔ ĐÃ ĐO VÀ BỎ 20/08/2026, đừng cắm lại:
    # · `defensepriorities.org/feed/` — 10/10 item nằm ở `/in-the-media/`, tức điểm báo. Cắm vào
    #   thì NOISE_PATHS lọc sạch, được đúng con số 0 kèm một lượt curl mỗi ngày.
    # · `iss.europa.eu/rss.xml` (EUISS) — 10 item nhưng nội dung là "X discussing … in Euronews",
    #   "… cited in El Confidencial", tức trích dẫn truyền thông chứ không phải nghiên cứu. Cùng
    #   loại với feed SWP và Clingendael đã bỏ.
]

# ══ ĐƯỜNG NẠP BÀI DÀI — quét theo THÁNG, tách khỏi routine quét theo NGÀY (dựng 06/08/2026) ══
#
# CƠ CHẾ GÂY VẤP — LỚP THỨ HAI của cùng một lỗ, và khai đúng feed ở trên KHÔNG chữa được nó.
# `MAX_AGE_DAYS = 7` là khung của routine sáng, đặt theo nhịp của feed BLOG. Nhưng báo cáo ra
# theo tháng, nên tới lúc ai đó cần nó thì nó đã ngoài khung từ lâu: bản báo cáo Lowy
# "Understanding the Chinese military threat to Australia" đăng 14/06/2026, tức **53 ngày**
# trước ngày dựng — khai feed `/publications/` xong thì `--candidates` vẫn không bao giờ liệt
# kê nó ra. Nghiên cứu ra theo tháng, routine quét theo ngày: hai nhịp không khớp nhau.
#
# Vì thế khung rộng đi kèm một CỜ RIÊNG (`--candidates-dai`), không nới khung của routine:
# nới `MAX_AGE_DAYS` là mỗi sáng danh sách ứng viên phình lên gấp mấy lần bằng bài đã đọc từ
# tuần trước, ngốn hết context của agent chọn bài — vá một lỗ bằng cách làm hỏng luồng đang
# chạy tốt.
# 60 ngày chứ không phải 30: 30 ngày vẫn bỏ sót đúng bản báo cáo 53 ngày tuổi đã nêu ở trên,
# tức khung đúng về nguyên tắc mà vẫn không giải quyết được ca đã sinh ra nó.
MAX_AGE_DAYS_DAI = 60

# Feed nào thuộc mảng NGHIÊN CỨU — `--candidates-dai` CHỈ quét bằng đây. Khai bằng URL chứ
# không thêm cột thứ tư vào `THINKTANK_FEEDS` vì đã có 3 chỗ giải nén đúng 3 cột; thêm cột là
# sửa cả ba, mà sót một chỗ thì lỗi hiện ra ở nơi khác hẳn.
# ⚠️ Hai bảng thì phải có phép canh cho chúng đừng tách nhánh: `feeds_dai()` đối chiếu và KÊU
# khi một URL ở đây không còn trong `THINKTANK_FEEDS`. Không có phép canh đó thì đổi tên miền
# một feed là đường quét dài lặng lẽ bỏ viện ấy — đúng loại hỏng câm mà cả mục này sinh ra để
# chặn.
URL_NGHIEN_CUU = frozenset({
    "https://www.lowyinstitute.org/publications/rss.xml",
    "https://www.aspi.org.au/feed/",
    "https://www.rusi.org/rss/latest-publications.xml",
    "https://cset.georgetown.edu/publications/feed/",
})


def feeds_dai():
    """Các feed NGHIÊN CỨU, lấy thẳng từ `THINKTANK_FEEDS` để hai bảng không tách nhánh."""
    ra = [f for f in THINKTANK_FEEDS if f[1] in URL_NGHIEN_CUU]
    if len(ra) != len(URL_NGHIEN_CUU):
        thieu = URL_NGHIEN_CUU - {f[1] for f in THINKTANK_FEEDS}
        die("URL_NGHIEN_CUU lệch THINKTANK_FEEDS — feed nghiên cứu sau không còn được khai: "
            + " · ".join(sorted(thieu))
            + "\n       Sửa URL ở CẢ HAI chỗ, đừng gỡ một bên cho hết kêu.")
    return ra

# Đường dẫn KHÔNG phải bài phân tích, tuy nằm chung feed. Không lọc thì mục Think-tank đầy
# mẩu "chuyên gia X được Coindesk trích dẫn" — Atlantic Council đẩy cả chuyên mục
# /insight-impact/in-the-news/ vào feed (thực tế 33 bài/7 ngày thì 8 là loại này).
NOISE_PATHS = (
    "/in-the-news/", "/insight-impact/", "/press-release", "/media-advisory",
    "/event/", "/events/", "/podcast", "/newsletter", "/webinar", "/transcript",
    # Arms Control Association đẩy cả mục điểm báo (bài CNN/NYT trích lời chuyên gia) vào
    # feed — không phải nghiên cứu của viện.
    "/media-citations/", "/in-the-media", "/press-mention",
    # ——— Feed publications của RUSI (thêm 06/08/2026 cùng lượt khai feed nghiên cứu).
    # Feed đó trộn CẢ podcast lẫn bản ghi sự kiện vào chung với báo cáo: đo 06/08, trong 5 mục
    # nó có mà feed commentary không có thì 4 là `/podcasts/` · `/members-event-recordings/` ·
    # `/research-event-recordings/`. Không lọc thì mục Think-tank đầy dòng kiểu
    # "Episode 125 — Japan's intelligence reforms", tức một tập ghi âm được trình bày như một
    # nghiên cứu.
    # ⚠️ `/podcasts/` về mặt chuỗi ĐÃ được `/podcast` ở trên phủ — giữ dòng này là để khai
    # tường minh nguồn sinh ra nó, đừng đọc thành hai phép lọc khác nhau.
    "/podcasts/",
    # Hai mục bản ghi sự kiện của RUSI KHÔNG khớp `/event/` hay `/events/` ở trên (đường dẫn là
    # `/members-event-recordings/`, không có dấu `/` trước chữ `event`) — đây mới là chỗ hở thật.
    "event-recordings",
)

# KHÔNG có RSS dùng được — đã thử ÍT NHẤT 2 biến thể URL mỗi nơi (27/07/2026), ĐỪNG thử lại.
# Xếp theo KHU VỰC để phiên sáng biết vùng nào đang trống RSS mà chủ động `WebSearch
# site:<domain>`. Lý do hỏng: phần lớn Cloudflare 403 · vài nơi 404 · Africa Center và AGSIW
# trả RSS hợp lệ nhưng feed RỖNG (0 item) · IFRI feed đứng từ 2023.
#
# ⚠️ ĐO LẠI 30/07/2026 — "KHÔNG CÓ RSS" ≠ "KHÔNG ĐỌC ĐƯỢC". Dò cả 40 domain bằng curl có UA
# trình duyệt, thử CẢ dạng `www.` lẫn không: **29/40 trả 200 và đọc được HTML bình thường**;
# chỉ 11 domain thật sự chặn (10 Cloudflare 403 + idsa.in hỏng DNS từ máy Huy, cùng kiểu với
# zone `.mil`). Nghĩa là phần lớn danh sách này chỉ THIẾU FEED, không phải mất nguồn — quét
# HTML trang danh sách vẫn lấy được bài (đúng cách lớp `[HTML]` của harvest.py đang làm).
# Ba cái bẫy đã vấp khi đo, đừng lặp lại:
#   (a) chỉ thử `https://<domain>/` là hụt — `spf.org` và `usip.org` trả 000/hỏng ở dạng trần
#       nhưng 200 với `www.`; kết luận "site chết" khi đó là SAI;
#   (b) `agsiw.org` nay redirect sang **agsi.org** (viện đổi tên) — đó mới là lý do feed cũ
#       trả 0 item, không phải feed hỏng. Domain mới đã thêm vào THINKTANK_DOMAINS;
#   (c) trong 10 domain Cloudflare 403, **08 mở được bằng TRÌNH DUYỆT THẬT** (38north, ecfr,
#       chathamhouse, clingendael, inss.org.il, mei, nti, thearcticinstitute, thebulletin) —
#       challenge chỉ chặn client không chạy JS. Còn chặn hẳn ở mọi đường: globsec.org (kẹt
#       challenge vĩnh viễn) · thesoufancenter.org (403 cứng) · idsa.in (DNS).
WEBSEARCH_ONLY = {
    "Trung Đông": ["mei.edu", "washingtoninstitute.org", "inss.org.il", "agsi.org", "carnegie-mec.org"],
    "Châu Phi · Sahel": ["africacenter.org", "issafrica.org"],
    "Mỹ Latin": ["wola.org", "dialogo-americas.com"],
    "Nam Á": ["orfonline.org", "idsa.in", "takshashila.org.in"],
    "Đông Bắc Á": ["38north.org", "jiia.or.jp", "spf.org", "eastasiaforum.org"],
    # cacianalyst.org đã RỜI danh sách này 30/07/2026 — có feed thật ở
    # `/publications/analytical-articles.feed`, xem THINKTANK_FEEDS.
    "Trung Á · Caucasus": [],
    "Bắc Cực": ["thearcticinstitute.org"],
    "Hạt nhân · khủng bố": ["thebulletin.org", "nti.org", "fas.org", "ctc.westpoint.edu", "thesoufancenter.org"],
    # SWP + Clingendael CÓ feed chạy được nhưng là feed ĐIỂM BÁO, không phải nghiên cứu:
    # SWP phát link thẳng ra cicero.de/deutschlandfunk.de (guardrail domain chặn), còn
    # Clingendael phát dưới chính domain của nó (`/node/NNNNN`, tiêu đề dạng "… / DW (Jul 21)")
    # nên guardrail KHÔNG chặn được — đó mới là loại nguy hiểm, bài báo lọt vào mục Think-tank
    # mà trông như bài viện. Đã BỎ khỏi THINKTANK_FEEDS, muốn bài của họ thì WebSearch.
    # RUSI đã RỜI danh sách này 30/07/2026 — feed thật `/rss/latest-commentary.xml` chạy tốt,
    # xem THINKTANK_FEEDS ở trên.
    "Châu Âu": ["ecfr.eu", "chathamhouse.org", "globsec.org", "ifri.org",
                "swp-berlin.org", "clingendael.org"],
    # usip.org đã RỜI danh sách này 30/07/2026 — feed `/feed/` chạy thật (10 item), xem
    # THINKTANK_FEEDS. Số còn lại vẫn không có feed; phần nào quét được HTML thì dòng in ra ở
    # cuối `--candidates` tự trừ đi.
    "Viện lớn của Mỹ": ["csis.org", "brookings.edu", "cnas.org", "stimson.org",
                        "carnegieendowment.org", "fpri.org", "belfercenter.org",
                        "wilsoncenter.org", "iiss.org"],
    # ══ Bổ sung 20/08/2026 — 30 viện trước đây IM LẶNG hoàn toàn ══
    # Chúng nằm trong `THINKTANK_DOMAINS` (guardrail cho nạp) nhưng KHÔNG có ở FEEDS, KHÔNG có ở
    # HTML, và cũng KHÔNG có ở đây — nên không lớp nào quét về, mà `--candidates` cũng không giục
    # agent tìm. Nhìn `THINKTANK_DOMAINS` thì tưởng đã phủ. Đã dò feed cả 35 domain thuộc diện
    # này (thẻ `<link rel=alternate>` + `/feed/` + `/rss.xml`): chỉ 07 có feed, 05 đã cắm vào
    # THINKTANK_FEEDS, 02 bị bỏ vì là feed điểm báo. Số còn lại xếp xuống đây.
    # ✅ ĐÃ DÒ QUÉT HTML 21/08/2026 — 11/30 domain rời khỏi đây: 09 lên `THINKTANK_HTML`
    # (ISW · NBR · USSC · PIIE · Defense Priorities · Timbuktu · Egmont · EUISS · SIPRI) và
    # 02 lên `THINKTANK_FEEDS` qua feed danh mục con (ISEAS · GulfIF). 19 domain còn lại nằm
    # đây kèm LÝ DO ĐÃ ĐO ở ngay dưới — chúng không còn là "chưa dò", nên đừng dò lại từ đầu.
    "Mỹ · viện và tạp chí": ["aei.org", "cato.org", "csbaonline.org",
                             "foreignaffairs.com", "sipa.columbia.edu"],
    "Châu Âu · viện quốc gia": ["carnegieeurope.eu", "ceps.eu",
                                "giga-hamburg.de", "ispionline.it", "nupi.no",
                                "pism.pl", "prif.org", "ui.se"],
    "Vùng Vịnh": ["epc.ae"],
    "Bắc Cực · báo chuyên": ["highnorthnews.com"],
    "Đông Á · Đông Nam Á": ["rsis.edu.sg", "sejong.org", "tokyofoundation.org"],
}

# ⛔ ĐÃ DÒ QUÉT HTML VÀ BỎ (21/08/2026) — số đo kèm lý do, để phiên sau đừng dò lại rồi mới biết.
# Ba nhóm nguyên nhân KHÁC HẲN nhau; gộp chung một chữ "không quét được" là mất thông tin cần
# để biết cái nào đáng thử lại về sau.
#
# (a) TRANG DANH SÁCH KHÔNG TRẢ VỀ HTML — mọi đường thử đều ra vài KB, tức chặn hoặc dựng bằng
#     JS. Không biểu thức path nào cứu được:
#     · rsis.edu.sg 5,7 KB · aei.org 5,5 KB · sipa.columbia.edu 5,7 KB · cato.org 949 B ·
#       csbaonline.org 103 B · ispionline.it 552 B · pism.pl 212 B · sejong.org 1,4 KB
#     · epc.ae 15 KB và giga-hamburg.de 31-33 KB: đọc được HTML nhưng **0 href bài nội bộ**,
#       danh sách dựng bằng JS.
#     · carnegieeurope.eu: chuyển hướng sang `carnegieendowment.org/europe/` (Next.js), mà
#       Carnegie Endowment đã nằm sẵn ở danh sách "ĐÃ THỬ VÀ BỎ" phía trên vì JS-only.
#
# (b) LẤY ĐƯỢC LINK NHƯNG KHÔNG LẤY ĐƯỢC NGÀY — nguy hơn nhóm (a) vì trang danh sách trả về
#     hàng trăm KB nên nhìn như đang chạy, chỉ có `khong_ngay` là tố:
#     · ceps.eu — trang danh sách 379 KB, 16 link đúng, nhưng trang BÀI lẻ trả **5,9 KB** và
#       không mang meta ngày nào trong 04 mẫu của `_META_DATE_PATTERNS`. Đo: 11/16 link không
#       ngày ⇒ bị bỏ hết. Chặn ở tầng trang bài, không phải tầng biểu thức path.
#     · tokyofoundation.org — bài nằm ở `/research/detail.php?id=…`, 11/16 link không dò được
#       ngày. Ngoài ra mọi bài chung một `path` nên biểu thức path mất hết khả năng phân loại.
#
# (c) LẤY ĐƯỢC ĐỦ NHƯNG NỘI DUNG KHÔNG THUỘC MỤC NÀY — đây là loại phải chặn bằng phán xét,
#     không cổng máy nào bắt được:
#     · nupi.no — `/en/publications/cristin-pub/…` là bản ghi thư mục của chương sách và bài
#       tạp chí học thuật (chỉ có abstract), không phải bình luận chính sách kịp thời; bài mới
#       nhất lúc đo đã 38 ngày.
#     · prif.org — 2 link khớp, cả hai không ngày; bài thật nằm ở `blog.prif.org`, một TÊN MIỀN
#       KHÁC nên guardrail domain sẽ chặn khi nạp.
#     · ui.se — ấn phẩm phát dưới dạng **PDF** (`/globalassets/…pdf`), không có trang bài HTML.
#     · highnorthnews.com — đọc được (251 KB) nhưng là **BÁO tin tức Bắc Cực, không phải viện**.
#       Để vào mục tên là Think-tank là hỏng chính danh nghĩa của mục; cùng lý do đã ghi cho
#       thebarentsobserver.com và arctictoday.com.
#     · foreignaffairs.com — tạp chí trả phí, bài xếp theo khu vực (`/china/…`, `/ukraine/…`)
#       nên không có tiền tố nào tách được bài khỏi trang chuyên mục.

# Domain CŨ của một viện đã đổi tên miền: guardrail phải giữ (bài cũ trong kho còn mang url cũ)
# nhưng KHÔNG cần đường quét riêng — tên miền mới mới là chỗ quét. Miễn chúng khỏi phép đo
# "domain nào chưa có đường quét", nếu không phép đo đó kêu oan mãi mãi.
DOMAIN_CU_DA_CHUYEN = {"agsiw.org": "agsi.org", "spf.org": "spf.org"}


def domain_chua_co_duong_quet() -> set:
    """`THINKTANK_DOMAINS` trừ đi mọi domain đã có đường quét (feed · HTML · WebSearch).

    Phép đo cho một hỏng câm ở tầng DANH SÁCH: thêm domain vào guardrail rồi quên khai đường
    vào thì không lớp nào quét, không lớp nào giục, và không dấu hiệu nào phát ra. Đo 20/08/2026
    trước khi vá: **35 domain**, trong đó có `cfr.org`.
    """
    co = set(DOMAIN_CU_DA_CHUYEN)
    co |= {urllib.parse.urlparse(u).netloc.replace("www.", "") for _, u, _ in THINKTANK_FEEDS}
    co |= {urllib.parse.urlparse(u).netloc.replace("www.", "") for _, u, _, _ in THINKTANK_HTML}
    for ds in WEBSEARCH_ONLY.values():
        co |= set(ds)
    return THINKTANK_DOMAINS - co

# ─────────────────────────── LỚP [HTML] — viện KHÔNG có RSS ───────────────────────────
# Vì sao có lớp này (30/07/2026): đo lại 40 domain trong WEBSEARCH_ONLY thì 29 cái trả 200
# và render sẵn HTML. **"Không có RSS" ≠ "không đọc được"** — phần lớn danh sách trên chỉ
# thiếu FEED, mà thiếu feed thì trước giờ vùng đó phụ thuộc hoàn toàn vào việc agent có nhớ
# `WebSearch site:<domain>` hay không. Cơ chế mượn từ lớp [HTML] của `harvest.py` (quét trang
# danh sách thông cáo uỷ ban Quốc hội Mỹ).
#
# ⚠️ KHÁC harvest.py ở khâu NGÀY — chỗ này là điểm yếu nhất của mọi phép quét HTML thô.
# harvest.py đoán ngày từ khối HTML quanh link nên có thể sai, và phải dặn agent mở bài kiểm
# lại. Ở đây làm được tốt hơn vì trang BÀI của viện phơi ngày chuẩn trong `ld+json
# datePublished` / `article:published_time` / `<time datetime>` (đo thật 30/07: 5/5 nơi thử
# đều có). Thứ tự dò, dừng ở cái đầu tiên ra kết quả:
#   (1) ngày nhúng trong chính đường dẫn (`/2026/07/28/…`) — miễn phí, chính xác tuyệt đối;
#   (2) ngày trong khối HTML quanh link — miễn phí, có thể dính ngày của bài hàng xóm;
#   (3) MỞ trang bài đọc meta — tốn 1 lượt curl (đo: 0,2–1,3 giây/bài) nhưng là ngày THẬT.
# Vì (3) chỉ chạy cho link mà (1)(2) trượt, và bị chặn trần `HTML_LINK_CAP`, chi phí cả lớp
# đo được là ~15–25 giây cho toàn bộ bảng.
#
# ⛔ KHÔNG đưa domain sau vào đây dù trình duyệt mở được: 38north · ecfr.eu · chathamhouse ·
# clingendael · inss.org.il · mei.edu · nti.org · thearcticinstitute · thebulletin. Chúng
# chặn theo dấu vân tay TLS (Cloudflare challenge), chỉ TRÌNH DUYỆT THẬT vào được — mà
# trình duyệt chỉ có ở phiên local, CI thì không. Cắm vào đây là lớp này ra kết quả KHÁC
# NHAU giữa local và CI, đúng kiểu hỏng câm khó truy nhất. Cần bài của họ thì WebSearch.
#
# Cột: (tên viện, trang danh sách, biểu thức đường dẫn BÀI, khu vực).
# Biểu thức path là thứ giữ cho lớp này không nuốt link điều hướng: trang danh sách nào cũng
# đầy link `/topics/…`, `/programs/…`, `/author/…` có tiêu đề dài y như bài thật.
THINKTANK_HTML = [
    ("AGSI (Gulf States)", "https://agsi.org/analysis/",
     r"^/analysis/[^/]{15,}/?$", "Vùng Vịnh · Trung Đông"),
    ("East Asia Forum", "https://eastasiaforum.org/",
     r"^/20\d\d/\d\d/\d\d/[^/]{10,}", "Đông Á · Đông Nam Á"),
    ("Belfer Center", "https://www.belfercenter.org/research-analysis",
     r"^/research-analysis/[^/]{15,}", "Mỹ · an ninh quốc tế"),
    ("FPRI", "https://www.fpri.org/",
     r"^/article/20\d\d/\d\d/[^/]{10,}", "Mỹ · địa chiến lược"),
    ("CSIS", "https://www.csis.org/analysis",
     r"^/analysis/[^/]{15,}", "Toàn cầu · viện lớn"),
    ("ORF", "https://www.orfonline.org/expert-speak",
     r"^/expert-speak/[^/]{15,}", "Nam Á"),
    ("CNAS", "https://www.cnas.org/publications",
     r"^/publications/[^/]+/[^/]{10,}", "Mỹ · quốc phòng"),
    # Wilson: phải là `/insight-analysis`, KHÔNG phải `/publications`. Trang `/publications`
    # trả 200 và có link `/article/…` nên nhìn như đang chạy, nhưng đó là trang giới thiệu
    # với bài nổi bật ĐỜI 2025 — đo 30/07: 8 link, 0 bài trong khung 7 ngày. `/insight-analysis`
    # mới là danh sách xếp theo thời gian (bài mới nhất cùng ngày).
    ("Wilson Center", "https://www.wilsoncenter.org/insight-analysis",
     r"^/article/[^/]{15,}", "Mỹ · toàn cầu"),
    ("FAS", "https://fas.org/publications/",
     r"^/publication/[^/]{10,}", "Hạt nhân · khoa học"),
    ("SPF (IINA)", "https://www.spf.org/iina/en/articles/",
     r"^/iina/en/articles/[^/]+\.html$", "Nhật Bản"),
    # ─── Bổ sung 20/08/2026 — 05 viện lấp bốn vùng mục Think-tank gần như trắng ───
    # Đo lúc cắm (số bài trang danh sách trả về / bài mới nhất): ACSS 6/07-08 · CTC 9/31-07 ·
    # IFRI 6/16-07 · SWP 6/18-08 · JIIA 8/17-08. Bốn viện đầu đăng THƯA (1-4 bài/tháng) nên
    # lớp này ra 0 bài phần lớn các ngày — đó là bình thường, không phải biểu thức path chết;
    # phân biệt hai ca bằng `--kiem-html` (nó in SỐ LINK khớp, khác hẳn số bài trong khung).
    #
    # ⚠️ ACSS: dùng `/in-focus/` chứ KHÔNG dùng `/research/`. Cả hai trả 200 và `/research/`
    # còn cho nhiều link hơn (16 so với 6), nhưng `/research/` xếp theo CHỦ ĐỀ nên bài mới nhất
    # trên đó đã 5 tháng tuổi, trong khi `/in-focus/` xếp theo thời gian. Đúng bài học Wilson
    # Center: nhiều link không có nghĩa là danh sách mới.
    ("Africa Center (ACSS)", "https://africacenter.org/in-focus/",
     r"^/(?:publication|spotlight)/[^/]{15,}", "Châu Phi · Sahel"),
    # ⚠️ CTC: bài nằm THẲNG ở gốc tên miền, không có tiền tố nào — biểu thức path vì thế phải
    # chặn bằng ĐỘ DÀI (≥30 ký tự, một segment) thay vì bằng tiền tố. Mọi lối điều hướng của
    # họ đều ngắn hơn (`/topics/…`, `/regions/…`, `/ctc-sentinel/`) hoặc có hai segment.
    ("CTC Sentinel (West Point)", "https://ctc.westpoint.edu/ctc-sentinel/",
     r"^/[a-z0-9-]{30,}/?$", "Khủng bố · cực đoan"),
    # ⚠️ IFRI: `/en/publications/all` mới là danh sách; `/en/publications-list` và
    # `/en/all-publications` cùng trả 200 nhưng chỉ 9 KB, tức trang rỗng. Bỏ `external-articles`
    # khỏi biểu thức: đó là bài người của viện đăng trên BÁO khác, url trỏ ra ngoài.
    ("IFRI", "https://www.ifri.org/en/publications/all",
     r"^/en/(?:studies|memos|briefings|papers|editorials|notes|reports)/[^/]{10,}", "Châu Âu · Pháp"),
    # ⚠️ SWP: feed của họ ĐÃ BỊ BỎ khỏi THINKTANK_FEEDS vì là feed ĐIỂM BÁO (phát link thẳng ra
    # cicero.de/deutschlandfunk.de). Lớp HTML này lấy nhánh khác hẳn — `/en/publication/…` là
    # nghiên cứu do chính viện xuất bản dưới domain của mình. Đừng đọc ghi chú bỏ-feed rồi suy ra
    # "SWP là nguồn đã loại".
    ("SWP Berlin", "https://www.swp-berlin.org/en",
     r"^/en/publication/[^/]{15,}", "Châu Âu · Đức"),
    # ⚠️ JIIA: trang `/en/column/` liệt kê bài, nhưng link trỏ sang nhánh `/eng/report/…` —
    # host vẫn là `jiia.or.jp` nên guardrail domain không chặn. Ngày lấy từ TÊN FILE, xem
    # `ngay_trong_ten_file`.
    ("JIIA (Nhật)", "https://www.jiia.or.jp/en/column/",
     r"^/eng/(?:report|column)/20\d\d/\d\d/[^/]+\.html$", "Nhật Bản"),
    # ─── Bổ sung 21/08/2026 — 09 viện dò từ khối "30 viện IM LẶNG" của WEBSEARCH_ONLY ───
    # Vòng 20/08 mới dò FEED cho khối đó rồi xếp phần còn lại xuống WebSearch, kèm lời dặn
    # "CHƯA dò quét HTML cho nhóm này". Đây là vòng dò ấy. Đo 21/08 (link khớp / bài mới nhất):
    # ISW 16/19-08 · NBR 16/19-08 · USSC 16/17-08 · PIIE 10/17-08 · DefPri 14/18-08 ·
    # Timbuktu 16/17-08 · Egmont 6/16-07 · EUISS 10/09-07 · SIPRI 16/02-07.
    #
    # ⚠️ ISW ra 3-4 bài MỖI NGÀY và tất cả đều là loạt định kỳ cùng tên khác ngày ("Russian
    # Offensive Campaign Assessment, August 19, 2026"). Đo 21/08: 16/16 link khớp đều thuộc
    # loạt này, tức viện này một mình chiếm trọn `HTML_LINK_CAP` của chính nó. Không lấn viện
    # khác (cap tính theo TỪNG trang), nhưng agent chọn bài phải biết đây là báo cáo tình hình
    # định kỳ chứ không phải nghiên cứu mới: lấy nhiều nhất 1-2 bài, ưu tiên bản "Special
    # Report". Nhồi cả loạt vào kho là biến mục Think-tank thành nhật ký chiến sự.
    ("ISW", "https://understandingwar.org/publications",
     r"^/research/[a-z-]+/[^/]{15,}/?$", "Nga-Ukraine · Trung Đông"),
    ("NBR", "https://www.nbr.org/publications/",
     r"^/publication/[^/]{15,}", "Đông Á"),
    # ⚠️ USSC và Egmont đặt bài THẲNG ở gốc tên miền, nên biểu thức phải chặn bằng ĐỘ DÀI như
    # CTC. Ngưỡng 30 ký tự lấy TỪ SỐ ĐO chứ không từ phỏng đoán: trang người của USSC
    # (`/dr-michael-green`, 16 ký tự) và lối điều hướng (`/publications`, `/topics`) đều ngắn
    # hơn nhiều, còn bài ngắn nhất đo được vẫn trên 40 ký tự.
    ("USSC (Úc)", "https://www.ussc.edu.au/publications",
     r"^/[a-z0-9-]{30,}/?$", "Úc · quan hệ Mỹ-Úc"),
    # PIIE: dùng `/blogs` (gộp mọi nhánh blog) chứ không neo riêng `realtime-economics` — đo
    # cả hai ra cùng số bài trong khung, nhưng nhánh gộp không chết khi viện mở nhánh blog mới.
    ("PIIE", "https://www.piie.com/blogs",
     r"^/blogs/[a-z-]+/20\d\d/[^/]{10,}", "Kinh tế quốc tế"),
    # ⚠️ Defense Priorities: feed của họ ĐÃ BỊ BỎ ngay phía trên vì 10/10 item nằm ở
    # `/in-the-media/` — điểm báo. Lớp HTML này lấy nhánh KHÁC HẲN: `/explainers/` và
    # `/policy-papers/` là bài do chính viện viết. Cùng ca với SWP; đừng đọc ghi chú bỏ-feed rồi
    # suy ra "Defense Priorities là nguồn đã loại".
    ("Defense Priorities", "https://www.defensepriorities.org/explainers/",
     r"^/(?:explainers|policy-papers)/[^/]{15,}/?$", "Mỹ · đại chiến lược"),
    # ⚠️ Timbuktu: chạy Joomla nên đường dẫn mang `/index.php/<chuyên mục>/item/<id>-<slug>`.
    # Bài phần lớn TIẾNG PHÁP — đúng thứ cần cho vùng Sahel, nơi nguồn tiếng Anh mỏng nhất.
    ("Timbuktu Institute", "https://timbuktu-institute.org/index.php/publications",
     r"^/index\.php/[^/]+/item/\d+-[^/]{10,}", "Châu Phi · Sahel"),
    ("Egmont", "https://www.egmontinstitute.be/publications/",
     r"^/[a-z0-9-]{30,}/?$", "Châu Âu · Bỉ"),
    # ⚠️ EUISS: `rss.xml` của họ ĐÃ BỊ BỎ 20/08 vì là điểm báo ("X discussing … in Euronews").
    # Nhánh `/publications/<loại>/…` lấy ở đây là nghiên cứu do chính viện xuất bản — lại đúng
    # ca SWP một lần nữa, nên hai ghi chú ấy KHÔNG mâu thuẫn nhau.
    ("EUISS", "https://www.iss.europa.eu/publications/commentary",
     r"^/publications/[a-z-]+/[^/]{15,}", "Châu Âu · EU"),
    # ⚠️ SIPRI: biểu thức phải mở cờ `(?i)`. Trang của họ trộn `/commentary/essay/…` viết thường
    # với `/commentary/Topical-backgrounder` viết HOA trong CÙNG một trang danh sách; thiếu cờ
    # thì mất đúng nhánh backgrounder mà không dấu hiệu nào, vì nhánh essay vẫn ra link.
    ("SIPRI", "https://www.sipri.org/commentary",
     r"(?i)^/commentary/[a-z-]+/20\d\d/[^/]{10,}", "Dữ liệu · giải trừ quân bị"),
]

# ĐÃ THỬ VÀ BỎ (30/07/2026) — ghi lại để phiên sau đừng dựng lại rồi mới biết:
# · `stimson.org` — CHỈ trang chủ đọc được (`/research/`, `/commentary/`, `/2026/` đều 403).
#   Trang chủ là khối bài nổi bật, đo được 0/16 bài trong khung 7 ngày, mà mỗi trang bài nặng
#   573KB/5,4 giây — tức chiếm quá nửa thời lượng cả bảng để đổi lấy không gì. Muốn bài Stimson
#   thì WebSearch.
# · `issafrica.org` — danh sách bài dựng bằng JS, HTML thô chỉ có link điều hướng (`/research/
#   books-and-other-publications`…). Không có biểu thức path nào cứu được.
# · `washingtoninstitute.org`, `carnegieendowment.org`, `iiss.org`, `brookings.edu` — cùng lý do
#   JS-only: trang trả 200, 100-800KB, mà 0 link bài trong HTML thô.

# Trần số link BÀI lấy từ mỗi trang danh sách. Trang danh sách xếp bài mới trước, nên cắt ở
# đây gần như không mất bài trong khung 7 ngày; đổi lại chặn được ca trang lưu trữ trả về
# hàng trăm link rồi kéo theo hàng trăm lượt curl dò ngày.
HTML_LINK_CAP = 16
HTML_WORKERS = 8

# Ngày trong khối HTML quanh link. Ba dạng viện hay dùng; dạng "28 July 2026" (Anh) phải có
# vì nếu thiếu thì các viện châu Âu rơi hết xuống bước (3) tốn curl.
_HTML_DATE_PATTERNS = [
    re.compile(r"(20\d\d-\d\d-\d\d)"),
    # Dạng gạch chéo — SPF/IINA in `2026/07/07` ngay cạnh tiêu đề. Thiếu mẫu này thì cả 16 bài
    # của họ rơi xuống bước (3), mà trang bài SPF KHÔNG có meta ngày nào ⇒ mất trắng nguồn Nhật.
    re.compile(r"(20\d\d/\d{1,2}/\d{1,2})"),
    re.compile(r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+20\d\d)"),
    re.compile(r"(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?,?\s+20\d\d)"),
]
_MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}

# Meta ngày trên trang bài, xếp theo độ tin cậy giảm dần. `<time datetime>` để CUỐI vì trang
# danh sách/bài hay có thêm khối "bài liên quan" cũng dùng thẻ đó.
_META_DATE_PATTERNS = [
    re.compile(r'property="article:published_time"[^>]*content="([^"]+)"'),
    re.compile(r'content="([^"]+)"[^>]*property="article:published_time"'),
    re.compile(r'"datePublished"\s*:\s*"([^"]+)"'),
    re.compile(r"<time[^>]+datetime=\"([^\"]+)\""),
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
    """Mọi URL đã có trong DATA — để một bài không nằm 2 chỗ (analyses + worldNews).

    ⚠️ Bài think-tank KHÔNG còn nằm trong `data` (tách ra data/analyses.json 30/07/2026),
    nên phải đọc thêm từ store. Bỏ bước này thì guardrail trùng-url thấy mảng rỗng và
    cho nạp lại nguyên kho — kiểu hỏng câm, không có thông báo nào.
    """
    urls = set()
    for it in analyses_store.doc(pathlib.Path(__file__).resolve().parent.parent):
        for f in ("url", "sourceUrl", "_baomoiUrl"):
            if it.get(f):
                urls.add(it[f].strip())
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

    ⚠️ Rác ở ĐẦU file cũng giết cả feed, và giết êm hơn hẳn rác ở cuối: feed Gulf International
    Forum mở đầu bằng đúng MỘT ký tự xuống dòng trước `<?xml …?>` (WordPress hay in thừa như
    vậy khi một plugin phát ra newline trước header), ET ném "XML or text declaration not at
    start of entity" ⇒ `parse_feed` trả None ⇒ `feed_items` trả rỗng ⇒ feed hiện ra ở dòng
    "Feed không ra bài nào trong khung ngày". Nhìn dòng đó không phân biệt được với viện đăng
    thưa thật, nên nguồn có thể nằm chết trong bảng nhiều tháng. Đo 21/08/2026: feed ấy trả
    113 KB và 10 item hợp lệ, chỉ vướng đúng một ký tự thừa.
    ⚠️ Chỉ cắt KHOẢNG TRẮNG và BOM, không cắt gì khác: rác đầu file mà không phải khoảng trắng
    thì đó là trang lỗi hoặc trang challenge, và đọc nó thành feed mới là hỏng thật.
    """
    xml_bytes = xml_bytes.lstrip(b"\xef\xbb\xbf").lstrip()
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


def parse_html_date(raw: str):
    """'2026-07-28T15:02:05+00:00' / 'Jul 29, 2026' / '28 July 2026' / '2026-07-28' -> date.

    Chuỗi có múi giờ được quy về giờ VN trước khi lấy phần ngày — bài đăng 23h giờ Mỹ là
    ngày HÔM SAU ở VN, lệch một ngày là đủ để rơi ra/vào khung MAX_AGE_DAYS.
    """
    if not raw:
        return None
    s = raw.strip()
    try:
        d = datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
        return d.astimezone(VN).date() if d.tzinfo else d.date()
    except ValueError:
        pass
    try:
        return datetime.date.fromisoformat(s[:10])
    except ValueError:
        pass
    m = re.match(r"(20\d\d)/(\d{1,2})/(\d{1,2})", s)
    if m:
        try:
            return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    m = re.match(r"([A-Za-z]+)\.?\s+(\d{1,2}),?\s+(20\d\d)", s)
    if m and m.group(1)[:3].lower() in _MONTHS:
        return datetime.date(int(m.group(3)), _MONTHS[m.group(1)[:3].lower()], int(m.group(2)))
    m = re.match(r"(\d{1,2})\s+([A-Za-z]+)\.?,?\s+(20\d\d)", s)
    if m and m.group(2)[:3].lower() in _MONTHS:
        return datetime.date(int(m.group(3)), _MONTHS[m.group(2)[:3].lower()], int(m.group(1)))
    return None


# Ngày nhét trong TÊN FILE, dạng `20260817.html` (thêm 20/08/2026 khi cắm JIIA).
# CƠ CHẾ GÂY VẤP: JIIA đặt đường dẫn `/eng/report/2026/08/20260817.html` — bước (1) đòi đủ
# `/YYYY/M/D/` nên trượt, và bước (2) thì trang danh sách của họ CHỈ in `2026/08` cạnh tiêu đề,
# tức chỉ có năm-tháng. Kết quả: mọi bài JIIA nhận ngày mồng 20 của tháng đó, lệch tới 19 ngày
# mà không dấu hiệu nào — bài cũ lọt vào khung 7 ngày, bài mới bị đẩy ra ngoài. Đo thật lúc cắm:
# bài `20260817.html` dò ra 2026-08-20 (lệch 3 ngày).
# ⚠️ Chỉ đọc phần TÊN FILE (bỏ đuôi), và 8 chữ số phải đứng trọn giữa hai ranh giới không phải
# số — nếu không thì mã báo cáo kiểu `asb44en-2026081712` cũng bị đọc thành ngày.
_TEN_FILE_NGAY = re.compile(r"(?:^|[^0-9])(20\d\d)(\d\d)(\d\d)(?:[^0-9]|$)")


def ngay_trong_ten_file(path: str):
    """`/eng/report/2026/08/20260817.html` -> date(2026, 8, 17). None nếu không có."""
    ten = path.rstrip("/").rsplit("/", 1)[-1]
    ten = re.sub(r"\.(?:html?|php|aspx?|pdf)$", "", ten, flags=re.I)
    m = _TEN_FILE_NGAY.search(ten)
    if not m:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def html_article_links(page_url: str, path_re: str, body: str):
    """[(tiêu đề, url tuyệt đối, ngày|None)] — bài trên một trang danh sách, giữ thứ tự trang.

    Ngày ở đây mới là ngày RẺ: lấy từ đường dẫn hoặc từ khối HTML quanh link. Link nào chưa
    có ngày sẽ được `resolve_dates` mở bài đọc meta.
    """
    rx = re.compile(path_re)
    host = urllib.parse.urlparse(page_url).netloc.replace("www.", "")

    # Mọi ngày xuất hiện trên trang, kèm vị trí. Gán ngày cho link theo NGƯỜI GẦN NHẤT: một
    # ngày chỉ thuộc về link nào gần nó hơn cả. Cách cũ (quét ±800 ký tự quanh link rồi lấy
    # ngày ĐẦU TIÊN gặp) sai câm hai kiểu, cả hai đã dựng thành ca test: (a) link không có ngày
    # riêng thì ăn ngày của bài BÊN TRÊN — bài hôm nay bị gán ngày hôm kia; (b) bài cũ nằm ngay
    # dưới bài mới thì ăn ngày của bài mới, tức bài tháng Một lọt vào danh sách "bài trong tuần".
    moc_ngay = []
    for pat in _HTML_DATE_PATTERNS:
        for mm in pat.finditer(body):
            d = parse_html_date(mm.group(1))
            if d:
                moc_ngay.append((mm.start(), d))
    moc_ngay.sort()

    out, seen = [], set()
    neo = [a.start() for a in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', body, re.S | re.I)
           if rx.search(urllib.parse.urlparse(urllib.parse.urljoin(page_url, a.group(1))).path)]

    def ngay_gan_nhat(vi_tri: int):
        """Ngày gần link nhất, với điều kiện chính link này cũng là link gần ngày đó nhất."""
        tot, kc_tot = None, 10 ** 9
        for vt, d in moc_ngay:
            kc = abs(vt - vi_tri)
            if kc > 800 or kc >= kc_tot:
                continue
            if any(abs(vt - n) < kc for n in neo if n != vi_tri):
                continue          # ngày này thuộc về link khác, không được mượn
            tot, kc_tot = d, kc
        return tot

    for a in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', body, re.S | re.I):
        href, raw = a.group(1), a.group(2)
        title = html_mod.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw))).strip()
        # Thẻ <a> có thuộc tính chứa dấu `>` (SPF nhét cả tiêu đề vào `title="…"`) làm phép
        # cắt thẻ ở trên bắt đầu giữa chừng thuộc tính, ra tiêu đề dính đuôi `…War">China's…`.
        # Cắt ở lần `">` cuối cùng là lấy lại đúng phần văn bản.
        if '">' in title:
            title = title.rsplit('">', 1)[-1].strip()
        # Thẻ <a> bọc CẢ thẻ bài (FAS) nên tiêu đề dính đuôi máy móc: "… 07.29.26 | 4 min
        # read read more". Cắt ở dấu hiệu đầu tiên của đuôi đó.
        title = re.sub(r"\s*\d\d\.\d\d\.\d\d\s*\|.*$", "", title)
        title = re.sub(r"\s*(?:\d+\s*min read|read more|Read More)\s*$", "", title).strip(" |·–—")
        # JIIA bọc cả khối bài trong <a> nên tiêu đề nuốt luôn tên tác giả và ngày ở cuối:
        # "… into Sustainable Prosperity Soichiro Chiba (Founder, Thousandleaf) 17.08.2026".
        # Cắt đuôi ngày dạng `dd.mm.yyyy` / `dd/mm/yyyy` (khác đuôi `07.29.26 |` của FAS ở chỗ
        # năm đủ 4 số và KHÔNG có dấu gạch đứng theo sau).
        title = re.sub(r"\s*\d{1,2}[./]\d{1,2}[./]20\d\d\s*$", "", title).strip(" |·–—")
        if len(title) < 25 or len(title) > 200:
            continue
        full = urllib.parse.urljoin(page_url, href)
        pr = urllib.parse.urlparse(full)
        if pr.scheme not in ("http", "https") or pr.netloc.replace("www.", "") != host:
            continue
        if not rx.search(pr.path):
            continue
        link = clean_url(full)
        if link in seen:
            continue
        if any(p in link.lower() for p in NOISE_PATHS):
            continue
        seen.add(link)
        d = None
        mu = re.search(r"/(20\d\d)/(\d{1,2})/(\d{1,2})/", pr.path)
        if mu:                                    # (1) ngày nằm ngay trong đường dẫn
            try:
                d = datetime.date(int(mu.group(1)), int(mu.group(2)), int(mu.group(3)))
            except ValueError:
                d = None
        if d is None:                             # (1b) ngày YYYYMMDD nằm trong TÊN FILE
            d = ngay_trong_ten_file(pr.path)
        if d is None:                             # (2) ngày gần link nhất trên trang
            d = ngay_gan_nhat(a.start())
        out.append((title, link, d))
        if len(out) >= HTML_LINK_CAP:
            break
    return out


def fetch_article_date(url: str):
    """(3) Mở trang bài, đọc meta ngày. Trả None nếu bài không phơi ngày nào."""
    body = curl(url).decode("utf-8", "replace")
    for pat in _META_DATE_PATTERNS:
        m = pat.search(body)
        if m:
            d = parse_html_date(m.group(1))
            if d:
                return d
    return None


def harvest_html_site(site, existing: set, today_vn: datetime.date):
    """Quét MỘT trang danh sách -> (rows trong khung ngày, thống kê).

    Thống kê được trả về để `--candidates` in ra chỗ hụt thay vì im lặng: một viện đổi giao
    diện là biểu thức path hết khớp và lớp này trả 0 bài — nhìn danh sách thì không phân biệt
    được với "hôm nay viện đó không ra bài".
    """
    name, page_url, path_re, _area = site
    body = curl(page_url).decode("utf-8", "replace")
    st = {"trang_byte": len(body), "link": 0, "da_co": 0, "khong_ngay": 0, "ngoai_khung": 0}
    if len(body) < 2000:                 # 403/challenge trả trang lỗi vài KB
        return [], st
    links = html_article_links(page_url, path_re, body)
    st["link"] = len(links)
    can_mo = [(t, u) for t, u, d in links if d is None and u not in existing]
    ngay_mo = {}
    if can_mo:
        with concurrent.futures.ThreadPoolExecutor(max_workers=HTML_WORKERS) as ex:
            for (t, u), d in zip(can_mo, ex.map(fetch_article_date, [u for _, u in can_mo])):
                ngay_mo[u] = d
    rows = []
    for title, link, d in links:
        if link in existing or link.split("?")[0] in existing:
            st["da_co"] += 1
            continue
        if d is None:
            d = ngay_mo.get(link)
        if d is None:
            st["khong_ngay"] += 1
            continue
        if d > today_vn or (today_vn - d).days > MAX_AGE_DAYS:
            st["ngoai_khung"] += 1
            continue
        rows.append((d, title, link))
    rows.sort(reverse=True)
    return rows, st


def harvest_thinktank_html(existing: set, today_vn: datetime.date):
    """Quét CẢ bảng THINKTANK_HTML -> [(tên, khu vực, rows, thống kê)]."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        kq = list(ex.map(lambda s: harvest_html_site(s, existing, today_vn), THINKTANK_HTML))
    return [(s[0], s[3], rows, st) for s, (rows, st) in zip(THINKTANK_HTML, kq)]


def kiem_html() -> None:
    """Soi sức khoẻ bảng THINKTANK_HTML — dùng khi nghi một viện đổi giao diện.

    In cho từng trang: kích thước, số link bài khớp biểu thức path, ngày dò được. Trang nào
    ra **0 link** là biểu thức path đã chết (hoặc trang bị chặn), phải sửa — chứ không phải
    hôm đó viện không ra bài. Đây là phép đo phân biệt hai ca đó, vì trong `--candidates`
    chúng nhìn y hệt nhau.
    """
    today_vn = datetime.datetime.now(VN).date()
    print(f"=== SOI BẢNG THINKTANK_HTML ({len(THINKTANK_HTML)} trang · {today_vn.isoformat()}) ===")
    chet = []
    for name, area, rows, st in harvest_thinktank_html(set(), today_vn):
        co = "OK " if st["link"] else "CHẾT"
        print(f"[{co}] {name:22s} trang={st['trang_byte']//1024:4d}KB link={st['link']:3d} "
              f"trong-khung={len(rows):2d} không-ngày={st['khong_ngay']:2d} "
              f"ngoài-khung={st['ngoai_khung']:2d}  ({area})")
        if not st["link"]:
            chet.append(name)
    # Đo luôn hỏng câm ở tầng DANH SÁCH — domain nằm trong guardrail mà không đường nào quét.
    # Đặt ở đây vì `--kiem-html` là chỗ duy nhất người ta mở ra khi nghi lớp quét có vấn đề.
    mo_coi = sorted(domain_chua_co_duong_quet())
    if mo_coi:
        print(f"\n⚠️ {len(mo_coi)} domain nằm trong THINKTANK_DOMAINS mà KHÔNG có đường quét nào "
              f"(không feed, không HTML, không cả WebSearch) — bài của họ không bao giờ tới:\n   "
              + " · ".join(mo_coi))
    if chet:
        print("\n⚠️ Trang KHÔNG ra link bài nào — sửa biểu thức path hoặc bỏ khỏi bảng: "
              + " · ".join(chet))
        raise SystemExit(3)
    if mo_coi:
        raise SystemExit(4)
    print("\nMọi trang đều ra link bài; mọi domain trong guardrail đều có đường quét.")


def loc_ung_vien_feed(url: str, khung: int, existing: set, today_vn: datetime.date):
    """Ứng viên của MỘT feed trong khung `khung` ngày -> [(ngày, tít, link)] mới nhất trước.

    Một hàm lọc duy nhất cho cả `--candidates` (khung ngày) lẫn `--candidates-dai` (khung
    tháng): hai đường quét mà mỗi đường tự viết lấy phép lọc thì chắc chắn lệch, và lệch âm
    thầm — đường này bỏ bài trùng, đường kia không.
    """
    rows = []
    for title, link, d in feed_items(curl(url)):
        if d is None or (today_vn - d).days > khung or d > today_vn:
            continue
        link = clean_url(link)
        if link in existing or link.split("?")[0] in existing:
            continue
        if any(p in link.lower() for p in NOISE_PATHS):
            continue
        rows.append((d, title, link))
    rows.sort(reverse=True)
    return rows


def list_candidates_dai() -> None:
    """Ứng viên BÀI DÀI: chỉ các feed NGHIÊN CỨU, khung `MAX_AGE_DAYS_DAI` ngày.

    Tách hẳn khỏi `--candidates` để routine sáng KHÔNG đổi hành vi — xem khối chú thích ở
    `MAX_AGE_DAYS_DAI`. Chạy tay khi cần bổ sung kho nền, không cắm vào phiên quét nào.
    """
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    html = (repo_root / "index.html").read_text(encoding="utf-8")
    start, end = find_data_span(html)
    existing = collect_existing_urls(json.loads(html[start:end]))

    today_vn = datetime.datetime.now(VN).date()
    feeds = feeds_dai()
    print(f"=== ỨNG VIÊN BÀI DÀI ({len(feeds)} feed nghiên cứu · đăng trong "
          f"{MAX_AGE_DAYS_DAI} ngày, tính tới {today_vn.isoformat()}) ===")
    tong, trong = 0, []
    for name, url, area in feeds:
        rows = loc_ung_vien_feed(url, MAX_AGE_DAYS_DAI, existing, today_vn)
        if not rows:
            trong.append(f"{name} ({area})")
            continue
        print(f"\n## {name} — {area} ({len(rows)} bài)")
        for d, title, link in rows[:PER_FEED_CAP]:
            print(f"  [{d.isoformat()}] {title}\n      {link}")
        if len(rows) > PER_FEED_CAP:
            print(f"  … còn {len(rows) - PER_FEED_CAP} bài nữa (cắt bớt cho gọn context)")
        tong += len(rows)
    print(f"\n=== TỔNG {tong} ứng viên bài dài ===")
    if trong:
        # Feed nghiên cứu ra bài theo tháng nên "không có bài mới" là chuyện thường — in ra để
        # phân biệt với ca feed đã chết, đừng đọc thành lỗi.
        print("Feed không ra bài nào trong khung: " + " · ".join(trong))


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
        rows = loc_ung_vien_feed(url, MAX_AGE_DAYS, existing, today_vn)
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

    # ─── Lớp [HTML]: viện không có RSS, quét thẳng trang danh sách ───
    print(f"\n=== ỨNG VIÊN [HTML] — {len(THINKTANK_HTML)} viện KHÔNG có RSS ===")
    html_total, html_empty, html_chet = 0, [], []
    for name, area, rows, st in harvest_thinktank_html(existing, today_vn):
        if not st["link"]:
            # Trang không ra LINK NÀO khác hẳn "hôm nay không có bài mới": biểu thức path đã
            # chết hoặc trang bị chặn. Phải kêu, không thì lớp này mục ruỗng trong im lặng.
            html_chet.append(name)
            continue
        if not rows:
            html_empty.append(f"{name} ({area})")
            continue
        print(f"\n## {name} [HTML] — {area} ({len(rows)} bài)")
        for d, title, link in rows[:PER_FEED_CAP]:
            print(f"  [{d.isoformat()}] {title}\n      {link}")
        if len(rows) > PER_FEED_CAP:
            print(f"  … còn {len(rows) - PER_FEED_CAP} bài nữa (cắt bớt cho gọn context)")
        html_total += len(rows)

    print(f"\n=== TỔNG {total + html_total} ứng viên ({total} từ RSS · {html_total} từ HTML) ===")
    if empty:
        # In ra để phiên sáng BIẾT vùng nào đang trống mà bù bằng WebSearch, thay vì tưởng
        # là hôm nay không có gì đáng đọc.
        print("Feed không ra bài nào trong khung ngày: " + " · ".join(empty))
    if html_empty:
        print("Trang HTML không ra bài nào trong khung ngày: " + " · ".join(html_empty))
    if html_chet:
        print("⚠️ Trang HTML KHÔNG ra link bài nào — biểu thức path có thể đã chết, chạy "
              "`--kiem-html` để soi: " + " · ".join(html_chet))
    print("\nVùng vẫn phải bù bằng `WebSearch site:<domain>` (không RSS, không quét HTML được):")
    # Trừ đi những domain nay ĐÃ có đường tự động — kể cả qua feed lẫn qua lớp HTML. Không trừ
    # thì danh sách này giục agent đi WebSearch chính nguồn vừa quét xong, tốn lượt tìm kiếm mà
    # ra đúng bài đã nằm ngay bên trên.
    da_phu = {urllib.parse.urlparse(u).netloc.replace("www.", "") for _, u, _, _ in THINKTANK_HTML}
    da_phu |= {urllib.parse.urlparse(u).netloc.replace("www.", "") for _, u, _ in THINKTANK_FEEDS}
    for area, doms in WEBSEARCH_ONLY.items():
        con = [d for d in doms if d not in da_phu]
        if con:
            print(f"  {area}: " + " · ".join(con))


def main() -> None:
    if len(sys.argv) == 2 and sys.argv[1] == "--candidates":
        list_candidates()
        return
    if len(sys.argv) == 2 and sys.argv[1] == "--candidates-dai":
        list_candidates_dai()
        return
    if len(sys.argv) == 2 and sys.argv[1] == "--kiem-html":
        kiem_html()
        return
    if len(sys.argv) != 2:
        print("Dùng: add_analyses.py /tmp/analyses.json  |  --candidates  "
              "|  --candidates-dai  |  --kiem-html", file=sys.stderr)
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
    kho = analyses_store.doc(repo_root)          # nguồn sự thật: data/analyses.json
    existing_titles = [a.get("title", "") for a in kho]

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
    merged = clean + kho
    merged.sort(key=lambda a: str(a.get("date") or ""), reverse=True)
    # Ghi vào data/analyses.json, KHÔNG ghi vào index.html: từ 30/07/2026 `DATA.analyses`
    # trong index.html luôn rỗng, web nạp bài qua loadAnalyses(). Xem scripts/analyses_store.py.
    analyses_store.ghi(repo_root, merged)
    for e in analyses_store.kiem_index_rong(repo_root):
        die(e)

    for w in warnings:
        print(f"⚠️  CẢNH BÁO: {w}")
    outlets = ", ".join(sorted({c["outlet"] for c in clean}))
    print(f"OK: đã nạp {len(clean)} bài think-tank ({outlets}). Tổng mục Phân tích: {len(merged)} bài.")
    hom_nay = sum(1 for a in merged if a.get("_addedDate") == today_vn.isoformat())
    print(f"    Nạp trong ngày {today_vn.isoformat()}: {hom_nay} bài.")


if __name__ == "__main__":
    main()
