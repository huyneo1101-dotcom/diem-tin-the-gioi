# Nguồn mở rộng theo 5 chủ đề + RSS đã verify

Dời NGUYÊN VĂN từ phụ lục `.claude/skills/quet-tin/SKILL.md` ngày 05/10/2026 (phụ lục chỉ dùng khi giao agent một chủ đề cụ thể, không cần nạp mỗi lần khởi động).

---

## Phụ lục — NGUỒN MỞ RỘNG theo 5 chủ đề (bổ sung 25/07/2026)
Agent điều phối chọn vài nguồn hợp chủ đề rồi nhúng vào prompt agent (đừng dán cả phụ lục). Ưu tiên
tầng 1 (chính thức, link thẳng) → wire (Reuters/AP/AFP) → chuyên ngành. Nguồn có RSS thì đưa thẳng URL
cho agent fetch; nguồn không RSS thì dùng WebSearch `site:domain`.

### 1. Nội bộ Mỹ (điều trần + bỏ phiếu thông qua)
- **Bản ghi bỏ phiếu chính thức**: clerk.house.gov/Votes · senate.gov/legislative/LIS/roll_call_lists ·
  congress.gov (tra bill + trạng thái). GovTrack/govtrack.us chỉ để TRA, link bài báo kèm.
- **Uỷ ban** (lịch điều trần + thông cáo): armedservices.house.gov · appropriations.house.gov ·
  foreignaffairs.house.gov · armed-services.senate.gov · appropriations.senate.gov · foreign.senate.gov ·
  banking.senate.gov · intelligence.senate.gov (đủ 101 uỷ ban trong `docs/nguon-chinh-thuc-my.md`).
- **Video/tường thuật**: C-SPAN (c-span.org). **Báo chuyên Quốc hội**: The Hill, Politico, Roll Call,
  Punchbowl News, NOTUS (notus.org), CQ. **Cơ quan liên bang**: Government Executive (govexec.com),
  Federal News Network. **Phân tích luật**: CRS (crsreports.congress.gov).

### 2. Úc & Biển Đông
- **Úc chính thức**: defence.gov.au · minister.defence.gov.au · pm.gov.au · dfat.gov.au · aph.gov.au
  (nghị viện). **Phân tích Úc**: ASPI The Strategist (aspistrategist.org.au), Lowy Interpreter
  (lowyinstitute.org/the-interpreter), Crikey (crikey.com.au — chính trường/AUKUS), The Conversation
  Úc (theconversation.com/au). **Báo Úc**: ABC News AU (abc.net.au), The Australian, SMH — dùng
  `/rss/politics/federal.xml` và `/rss/world.xml`, KHÔNG dùng `/rss/national.xml` (thuần tin trong
  nước, gần như không chạm chủ đề — xem "Nguồn MỚI cho Úc & Biển Đông — thêm 21/09/2026" ở CLAUDE.md),
  Defence Connect (defenceconnect.com.au — đã thử, RSS chết), Australian Defence Magazine (đã thử,
  RSS chết), ADBR.
- **Biển Đông**: AMTI/CSIS (amti.csis.org — bản đồ/phân tích) · Philippine Coast Guard (coastguard.gov.ph) ·
  Philippine News Agency (pna.gov.ph, đã thử 403) · Rappler · Inquirer · Philstar · GMA News · Manila
  Bulletin (đã thử 403) · BenarNews (đã thử, RSS chết) · Radio Free Asia (đã thử, RSS chết) · The
  Maritime Executive · gCaptain · Naval News (đã thử, chặn Cloudflare) · Nikkei Asia (đã thử, feed
  rỗng) · SCMP · Channel News Asia (channelnewsasia.com, feed Asia) · The Straits Times
  (straitstimes.com/news/asia) — hai nguồn Singapore này phủ cùng lúc Trung Quốc/Malaysia/Việt Nam/
  Philippines/Đài Loan, tiêu đề tự nhắc tên nước nên khớp chủ đề ngay. VN: vietnamplus.vn,
  thanhnien.vn. **TQ (chỉ phát ngôn của họ)**: mod.gov.cn, mfa.gov.cn.

### 3. CNQS Mỹ
- **Chính thức**: defense.gov · war.gov/News/Contracts (hợp đồng hằng ngày) · navy.mil · army.mil ·
  af.mil · spaceforce.mil · dvidshub.net · DARPA (darpa.mil) · Missile Defense Agency (mda.mil) ·
  DIU (diu.mil) · NAVSEA. **Chuyên ngành**: Defense News, Breaking Defense, Defense One, Naval News,
  USNI News, C4ISRNet, SpaceNews, Air & Space Forces Magazine, DefenseScoop, The War Zone, National
  Defense Magazine (nationaldefensemagazine.org), Defense Daily, Inside Defense, Aviation Week, Naval
  Technology. **Nhà thầu (thông báo của họ)**: Lockheed Martin, RTX, Boeing, Northrop Grumman, General
  Dynamics. *Kiểm chứng thêm*: Janes, SIPRI, Army Recognition (chỉ tham khảo).

### 4. Mỹ–Mali (JNIM/Sahel)
- **Chính thức**: africom.mil (AFRICOM — chính) · defense.gov · state.gov · centcom.mil. **Theo dõi
  khủng bố/JNIM**: FDD Long War Journal (longwarjournal.org) · Jamestown Foundation (Terrorism Monitor /
  Militant Leadership Monitor) · Critical Threats (criticalthreats.org — AEI). **Dữ liệu xung đột**:
  ACLED (acleddata.com). **Phân tích Phi**: ISS Africa (issafrica.org) · Africa Center for Strategic
  Studies (africacenter.org). **Báo**: Reuters, AP, AFP, WaPo, France24/RFI, Al Jazeera, Jeune Afrique,
  The Africa Report, BBC Africa.

### 5. Predator's Run 2026 (Mỹ–Úc–Philippines)
- **Chính thức**: pacom.mil (INDOPACOM) · usarpac.army.mil (US Army Pacific) · marines.mil / III MEF ·
  army.mil · defence.gov.au · army.gov.au (Australian Army, 1st Division) · dvidshub.net (thông cáo +
  ảnh diễn tập). **Philippines**: Philippine Army, AFP (armedforces). **Báo**: ABC News AU, Defence
  Connect, ADBR, The Townsville Bulletin (địa phương), Naval News. Từ khoá WebSearch: "Predator's Run
  2026", "Exercise Carabaroo 2026".

### ✅ RSS nguồn mở rộng — ĐÃ VERIFY BẰNG FETCH THẬT 25/07/2026
Chạy tốt (đưa THẲNG URL cho agent):
| Nguồn | RSS URL | item |
|---|---|---|
| The Hill (chung) | https://thehill.com/feed/ | 100 |
| The Hill — Defense | https://thehill.com/policy/defense/feed/ | 15 |
| Roll Call | https://rollcall.com/feed/ | 10 |
| Government Executive | https://www.govexec.com/rss/all/ | 22 |
| ABC News AU (world) | https://www.abc.net.au/news/feed/51120/rss.xml | 25 |
| Lowy Interpreter | https://www.lowyinstitute.org/the-interpreter/rss.xml | 50 |
| AMTI/CSIS (Biển Đông) | https://amti.csis.org/feed/ | 10 |
| Rappler | https://www.rappler.com/feed/ | 10 |
| Philstar (headlines) | https://www.philstar.com/rss/headlines | 10 |
| Inquirer | https://www.inquirer.net/fullfeed/ | 20 |
| gCaptain | https://gcaptain.com/feed/ | 12 |
| Naval Technology | https://www.naval-technology.com/feed/ | 10 |
| The War Zone (TWZ) | https://www.twz.com/feed | 44 |
| DefenseScoop | https://defensescoop.com/feed/ | 10 |
| Aviation Week | https://aviationweek.com/rss.xml | 10 |
| Long War Journal (Mali/JNIM) | https://www.longwarjournal.org/feed | 30 |
| DVIDS news (Predator) | https://www.dvidshub.net/rss/news | 20 |

Bổ sung 25/07/2026 — gộp từ kho tư liệu `docs/diemtin-*-sources.md`, đã fetch thật cùng ngày:
| Nguồn | RSS URL | item | Chủ đề |
|---|---|---|---|
| Defense Daily | https://www.defensedaily.com/feed/ | 50 | 3 |
| Air & Space Forces Magazine | https://www.airandspaceforces.com/feed/ | 9 | 3 |
| Military Times | https://www.militarytimes.com/arc/outboundfeeds/rss/ | 25 | 3 |
| FlightGlobal | https://www.flightglobal.com/rss/ | 10 | 3 |
| The Aviationist | https://theaviationist.com/feed/ | 15 | 3 |
| Soldier Systems Daily | https://soldiersystems.net/feed/ | 6 | 3 |
| Sandboxx News | https://www.sandboxx.us/news/feed/ | 15 | 3 |
| DVIDS (toàn bộ, rộng hơn /rss/news) | https://www.dvidshub.net/rss/all | 419 | 3 + 5 |
| Shephard Media | https://www.shephardmedia.com/news/feed/ | 10 | 3 + 2 |
| The Japan Times | https://www.japantimes.co.jp/feed/ | 30 | 2 |
| Yonhap | https://en.yna.co.kr/RSS/news.xml | 97 | 2 |
| AllAfrica | https://allafrica.com/tools/headlines/rdf/latest/headlines.rdf | 30 | 4 |
| Federal News Network — Defense | https://federalnewsnetwork.com/category/defense-main/feed/ | 15 | 1 |
| Atlantic Council | https://www.atlanticcouncil.org/feed/ | 100 | phân tích |
| Foreign Policy | https://foreignpolicy.com/feed/ | 25 | phân tích |
| Bellingcat | https://www.bellingcat.com/feed/ | 10 | OSINT |
| The Guardian — World | https://www.theguardian.com/world/rss | 45 | chung |
| Semafor | https://www.semafor.com/rss.xml | 261 | chung |
| NPR — World | https://feeds.npr.org/1004/rss.xml | 10 | chung |
| VietnamPlus (TTXVN) | https://www.vietnamplus.vn/rss/thegioi.rss | 50 | 2 · VN |
| Nhân Dân | https://nhandan.vn/rss/thegioi-1231.rss | 50 | VN |
| Báo Chính phủ | https://baochinhphu.vn/quoc-te.rss | 50 | VN |
| VietnamNet | https://vietnamnet.vn/rss/the-gioi.rss | 1000 | VN |
| Báo Thế giới & Việt Nam | https://baoquocte.vn/rss_feed/ | 25 | VN ngoại giao |

Nguồn VN là **ưu tiên #2** (tiếng Anh trước) — dùng khi cần góc trong nước hoặc tin Biển Đông.
**Feed CHẾT, đừng thử lại:** CSIS `csis.org/rss.xml` (bài mới nhất 2016) · War on the Rocks (403) ·
DARPA `darpa.mil/rss.xml` (không phân giải tên miền) → WebSearch `site:...`.

KHÔNG có RSS dùng được → **WebSearch `site:domain`** (đã thử, 403/404/0-item 25/07): NOTUS
(notus.org) · Punchbowl (trả phí) · C-SPAN · Defence Connect · ADBR · Philippine News Agency
(pna.gov.ph) · Manila Bulletin (mb.com.ph) · Radio Free Asia (rfa.org) · The Maritime Executive ·
National Defense Magazine · Jeune Afrique · The Africa Report · RFI (rfi.fr) · ISS Africa (issafrica.org).
Nguồn chính thức (.gov/.mil/committee) vốn ít RSS ổn định — mặc định WebSearch `site:...`.
