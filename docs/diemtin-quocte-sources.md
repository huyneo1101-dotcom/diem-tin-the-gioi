# Nguồn quốc tế / quốc phòng — Điểm Tin Thế Giới

> **🔀 ĐÃ GỘP 25/07/2026** — các nguồn trong file này đã được đối chiếu với bảng RSS trong
> `CLAUDE.md`; nguồn nào chưa có mà fetch thật còn sống đã được thêm vào mục **"Gộp từ kho tư liệu
> cũ"** của bảng đó (18 nguồn quốc tế). File này giờ là **kho tra cứu**, KHÔNG phải nguồn chân lý —
> quy trình quét chỉ đọc `CLAUDE.md` + Phụ lục trong `.claude/skills/quet-tin/SKILL.md`.
> Cột "✓" ở dưới chỉ đếm số `<item>` lúc dò 09/07, **không đo tuổi bài** — CSIS bị chấm "10 ✓" trong
> khi feed bỏ hoang từ 2016. Muốn dùng nguồn nào thì fetch kiểm lại trước.

> **Bản sao thuộc Điểm Tin** (copy từ SA BÀN `QuanSu/nguon-tin.md` ngày 2026-07-09 để TÁCH ĐỘC LẬP).
> Dùng cho: **"Công nghệ quân sự" (nhất là CNQS Mỹ)** → Nhóm 1–3; **CNQS đồng minh** → Nhóm 6/2 (→ tab Thế giới); **toàn bộ "Phân tích"** → Nhóm 5 + The Diplomat; **thời sự Thế giới/Mỹ (CT/KT/NG)** → Nhóm 7 + báo lớn.
> Cột **RSS** đã dò ngày 2026-07-09 (curl + đếm `<item>`). Feed sống → dùng RSS trước; "⚠️ chặn/không feed" → crawl HTML hoặc WebSearch.
>
> ⚠️ Truyền thông nhà nước Nga/Trung (TASS, RIA, Global Times, Tân Hoa Xã) **KHÔNG** dùng làm nguồn khách quan.

---

## 🇺🇸 Nhóm 1 — Báo chuyên ngành quốc phòng Mỹ
1. **Defense News** — https://www.defensenews.com/ · RSS: `https://www.defensenews.com/arc/outboundfeeds/rss/` ✓
2. **Breaking Defense** — https://breakingdefense.com/ · RSS: `https://breakingdefense.com/feed/` ✓
3. **Defense One** — https://www.defenseone.com/ · RSS: `https://www.defenseone.com/rss/all/` (25 ✓)
4. **DefenseScoop** — https://defensescoop.com/ · RSS: `https://defensescoop.com/feed/` (10 ✓)
5. **Inside Defense** — https://insidedefense.com/ (trả phí)
6. **Defense Daily** — https://www.defensedaily.com/ · RSS: `https://www.defensedaily.com/feed/` (50 ✓)
7. **National Defense Magazine** — https://www.nationaldefensemagazine.org/ · ⚠️ feed trả rỗng → crawl HTML
8. **C4ISRNET** — https://www.c4isrnet.com/ · RSS: `https://www.c4isrnet.com/arc/outboundfeeds/rss/` (25 ✓)
9. **Military.com** — https://www.military.com/ · ⚠️ curl lỗi/không feed ổn định → crawl HTML
10. **The War Zone (TWZ)** — https://www.twz.com/ · RSS: `https://www.twz.com/feed` ✓

## ✈️⚓🛰️ Nhóm 2 — Chuyên theo quân chủng / không gian
11. **USNI News** — https://news.usni.org/ · ⚠️ feed 403 chặn bot → WebSearch/HTML
12. **Naval News** — https://www.navalnews.com/ · RSS: `https://www.navalnews.com/feed/` ✓
13. **Air & Space Forces Magazine** — https://www.airandspaceforces.com/ · RSS: `https://www.airandspaceforces.com/feed/` ✓
14. **SpaceNews** — https://spacenews.com/ · RSS: `https://spacenews.com/feed/` (24 ✓)
15. **Aviation Week** — https://aviationweek.com/ · RSS: `https://aviationweek.com/rss.xml` (10 ✓)
16. **Military Times** — https://www.militarytimes.com/ · RSS: `https://www.militarytimes.com/arc/outboundfeeds/rss/` (25 ✓)
17. **Stars and Stripes** — https://www.stripes.com/ · ⚠️ feed 404 → crawl HTML
18. **Sandboxx News** — https://www.sandboxx.us/news/ · RSS: `https://www.sandboxx.us/news/feed/` (15 ✓)

## 🏛️ Nhóm 3 — Nguồn chính thức Mỹ (phần lớn .mil chặn curl → WebSearch)
19. **Bộ Quốc phòng Mỹ (defense.gov)** — https://www.defense.gov/
20. **DVIDS** — https://www.dvidshub.net/ · RSS: `https://www.dvidshub.net/rss/all` (RẤT giàu, ~400 mục ✓)
21. **U.S. Army** — https://www.army.mil/ · ⚠️ RSS 403 → WebSearch
22. **U.S. Navy** — https://www.navy.mil/
23. **U.S. Air Force** — https://www.af.mil/
24. **U.S. Space Force** — https://www.spaceforce.mil/
25. **DARPA** — https://www.darpa.mil/ · RSS: `https://www.darpa.mil/rss.xml` (10 ✓)

## 📰 Nhóm 4 — Hãng tin & báo lớn (mảng an ninh-QP)
26. **Reuters — Aerospace & Defense** — https://www.reuters.com/business/aerospace-defense/ (hay chặn fetch)
27. **AP News — Military** — https://apnews.com/hub/military (hay chặn fetch)
28. **Bloomberg** — https://www.bloomberg.com/ (tường phí)
29. **The Wall Street Journal** — https://www.wsj.com/politics/national-security (tường phí)
30. **The New York Times** — https://www.nytimes.com/section/us/politics (tường phí)
31. **The Washington Post** — https://www.washingtonpost.com/national-security/ (tường phí)

## 🔎 Nhóm 5 — OSINT & think tank / phân tích (cho tab Phân tích)
32. **Janes** — https://www.janes.com/ · ⚠️ feed 404 → WebSearch
33. **CSIS** — https://www.csis.org/ · RSS: `https://www.csis.org/rss.xml` (10 ✓)
34. **RAND** — https://www.rand.org/ · ⚠️ feed 404 → WebSearch
35. **IISS** — https://www.iiss.org/ · ⚠️ feed 403 → WebSearch
36. **War on the Rocks** — https://warontherocks.com/ · RSS: `https://warontherocks.com/feed/` (100 ✓)
51. **ISW** — https://www.understandingwar.org/ · ⚠️ feed 403 → WebSearch (allowed_domains)
52. **CNAS** — https://www.cnas.org/ · ⚠️ feed 404 → WebSearch
53. **Atlantic Council** — https://www.atlanticcouncil.org/ · RSS: `https://www.atlanticcouncil.org/feed/` (100 ✓)
54. **SIPRI** — https://www.sipri.org/ · ⚠️ feed 404 → WebSearch
55. **Bellingcat** — https://www.bellingcat.com/ · RSS: `https://www.bellingcat.com/feed/` (10 ✓)

## 🌍 Nhóm 6 — Quốc tế / đồng minh (CNQS đồng minh → tab Thế giới)
37. **The Defense Post** — https://thedefensepost.com/ · ⚠️ feed trả rỗng → crawl HTML
38. **Shephard Media** — https://www.shephardmedia.com/ · RSS: `https://www.shephardmedia.com/news/feed/` (⚠️ có `/news/`; 10 ✓)
39. **Army Recognition** — https://www.armyrecognition.com/ · ⚠️ feed 404 → crawl HTML
40. **NATO** — https://www.nato.int/ · ⚠️ feed path 404 → crawl HTML/WebSearch & Bộ QP các nước ([Úc](https://www.defence.gov.au/), [Anh](https://www.gov.uk/government/organisations/ministry-of-defence)…)
56. **The Diplomat** — https://thediplomat.com/ · RSS: `https://thediplomat.com/feed/` (⚠️ curl 000 trong env này — dùng WebFetch/WebSearch; feed WordPress thật)
57. **Nikkei Asia** — https://asia.nikkei.com/ (SEARCH-được, fetch hay 403)
58. **Yonhap News** — https://en.yna.co.kr/ · RSS: `https://en.yna.co.kr/RSS/news.xml` (102 ✓)
59. **Defence Connect** — https://www.defenceconnect.com.au/ · ⚠️ feed 404 → crawl HTML
60. **Defence24** — https://defence24.com/ · RSS: `https://defence24.com/rss` (50 ✓)

## 🇺🇸 Nhóm 1+ — Chính sách & hợp đồng QP Mỹ (mở rộng)
41. **Politico — Defense** — https://www.politico.com/news/defense · RSS: `https://www.politico.com/rss/defense.xml` (30 ✓ — feed QP chạy dù trang thường 403)
42. **The Hill — Defense** — https://thehill.com/policy/defense/ · RSS: `https://thehill.com/policy/defense/feed/` (15 ✓)
43. **GovConWire** — https://www.govconwire.com/ · ⚠️ feed 403 → crawl HTML
44. **Task & Purpose** — https://taskandpurpose.com/ · RSS: `https://taskandpurpose.com/feed/` (29 ✓)
45. **Federal News Network — Defense** — https://federalnewsnetwork.com/category/defense-main/ · RSS: `https://federalnewsnetwork.com/category/defense-main/feed/` (15 ✓)

## ✈️⚓🛰️ Nhóm 2+ — Chuyên ngành sâu (mở rộng)
46. **FlightGlobal** — https://www.flightglobal.com/defence · RSS: `https://www.flightglobal.com/rss/` (10 ✓)
47. **Naval Technology** — https://www.naval-technology.com/ · ⚠️ feed 403 → WebSearch
48. **Via Satellite** — https://www.satellitetoday.com/ · ⚠️ feed 403 → crawl HTML
49. **Soldier Systems Daily** — https://soldiersystems.net/ · RSS: `https://soldiersystems.net/feed/` (6 ✓)
50. **The Aviationist** — https://theaviationist.com/ · RSS: `https://theaviationist.com/feed/` (15 ✓)

## 🌍 Nhóm 7 — Báo lớn thế giới (CT / KT / NG cho Thế giới & Mỹ)
61. **The Guardian** — https://www.theguardian.com/international · RSS: `https://www.theguardian.com/world/rss` ✓
62. **POLITICO** — https://www.politico.com/ (RSS trang chính 403; dùng feed QP mục 41 hoặc WebSearch)
63. **South China Morning Post (SCMP)** — https://www.scmp.com/ · RSS: `https://www.scmp.com/rss/91/feed` ✓
64. **CNN** — https://edition.cnn.com/ (CNN bỏ RSS; dùng WebSearch)
65. **The New York Times** — https://www.nytimes.com/ (tường phí)
66. **The Times** — https://www.thetimes.com/ (tường phí)

## 🌐 Nhóm 8 — Hãng/báo quốc tế lớn, thời sự chung (RSS ✓, thêm 2026-07-09)
> Dùng cho Thế giới & Mỹ (KT/CT/NG). Tất cả feed đã kiểm 09/07 = 200 + có mục → DÙNG THẲNG, đừng WebFetch trang HTML kẻo dính 403.
67. **Al Jazeera** — https://www.aljazeera.com/ · RSS: `https://www.aljazeera.com/xml/rss/all.xml` (25 ✓)
68. **BBC News — World** — https://www.bbc.com/news/world · RSS: `https://feeds.bbci.co.uk/news/world/rss.xml` (30 ✓)
69. **Deutsche Welle (DW)** — https://www.dw.com/ · RSS: `https://rss.dw.com/rdf/rss-en-world` (12 ✓)
70. **France 24** — https://www.france24.com/en/ · RSS: `https://www.france24.com/en/rss` (24 ✓)
71. **Euronews** — https://www.euronews.com/ · RSS: `https://www.euronews.com/rss` (50 ✓)
72. **The Moscow Times** (Nga, độc lập) — https://www.themoscowtimes.com/ · RSS: `https://www.themoscowtimes.com/rss/news` (50 ✓)
73. **Meduza** (Nga, độc lập) — https://meduza.io/en · RSS: `https://meduza.io/rss/en/all` (30 ✓)
74. **Al-Monitor** (Trung Đông) — https://www.al-monitor.com/ · RSS: `https://www.al-monitor.com/rss` (20 ✓)
75. **The National** (Vùng Vịnh/UAE) — https://www.thenationalnews.com/ · RSS: `https://www.thenationalnews.com/arc/outboundfeeds/rss/?outputType=xml` (100 ✓)
76. **Semafor** — https://www.semafor.com/ · RSS: `https://www.semafor.com/rss.xml` (225 — rất giàu ✓)
77. **NPR — World** — https://www.npr.org/sections/world/ · RSS: `https://feeds.npr.org/1004/rss.xml` (225 ✓)
78. **CNBC International** (Kinh tế) — https://www.cnbc.com/world/ · RSS: `https://www.cnbc.com/id/100727362/device/rss/rss.html` (30 ✓)
79. **Foreign Policy** (phân tích) — https://foreignpolicy.com/ · RSS: `https://foreignpolicy.com/feed/` (25 ✓)
80. **The Conversation — Global** (phân tích học thuật) — https://theconversation.com/global · RSS: `https://theconversation.com/global/articles.atom` (Atom `<entry>`, 50 ✓)
81. **The Independent — World** — https://www.independent.co.uk/news/world · RSS: `https://www.independent.co.uk/news/world/rss` (60 ✓)
82. **CBC — World** (Canada) — https://www.cbc.ca/news/world · RSS: `https://www.cbc.ca/webfeed/rss/rss-world` (20 ✓)

## 🗺️ Nhóm 9 — Khu vực / đa dạng địa lý (RSS ✓, thêm 2026-07-09)
83. **The Straits Times — World** (Singapore/ĐNA) — https://www.straitstimes.com/world · RSS: `https://www.straitstimes.com/news/world/rss.xml` (50 ✓)
84. **The Hindu — International** (Nam Á) — https://www.thehindu.com/news/international/ · RSS: `https://www.thehindu.com/news/international/feeder/default.rss` (60 ✓)
85. **The Times of India — World** — https://timesofindia.indiatimes.com/world · RSS: `https://timesofindia.indiatimes.com/rssfeeds/296589292.cms` (20 ✓)
86. **The Japan Times** — https://www.japantimes.co.jp/ · RSS: `https://www.japantimes.co.jp/feed/` (30 ✓ — RSS chạy dù trang thường hay chặn fetch)
87. **The Jerusalem Post** (Trung Đông/Israel) — https://www.jpost.com/ · RSS: `https://www.jpost.com/rss/rssfeedsheadlines.aspx` (60 ✓)
88. **Le Monde (English)** (Pháp/Châu Âu) — https://www.lemonde.fr/en/ · RSS: `https://www.lemonde.fr/en/rss/une.xml` (18 ✓)
89. **Africanews** (Châu Phi) — https://www.africanews.com/ · RSS: `https://www.africanews.com/feed/rss` (50 ✓)
90. **AllAfrica** (Châu Phi, tổng hợp) — https://allafrica.com/ · RSS: `https://allafrica.com/tools/headlines/rdf/latest/headlines.rdf` (30 ✓)
91. **MercoPress** (Nam Mỹ/Nam Đại Tây Dương) — https://en.mercopress.com/ · RSS: `https://en.mercopress.com/rss` (10 ✓)
92. **Buenos Aires Herald** (Argentina/Mỹ Latinh) — https://buenosairesherald.com/ · RSS: `https://buenosairesherald.com/feed` (10 ✓)
93. **Anadolu Agency — World** (Thổ Nhĩ Kỳ, hãng NHÀ NƯỚC → chỉ dẫn dữ kiện, không xem là khách quan) — https://www.aa.com.tr/en · RSS: `https://www.aa.com.tr/en/rss/default?cat=world` (18)

---
*93 nguồn: 1–66 copy từ SA BÀN + 67–93 báo/hãng quốc tế lớn (dò RSS 09/07). Tổng ~53 feed RSS sống; nguồn chặn bot/không feed → WebSearch/HTML. Sửa nguồn tại đây — độc lập với `QuanSu/nguon-tin.md`.*
