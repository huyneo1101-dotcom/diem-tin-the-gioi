# Điểm Tin Thế Giới — quy tắc quét tin

Trang tin tĩnh (PWA) tiếng Việt, deploy tự động lên GitHub Pages khi push vào `main`.

## Nơi lưu dữ liệu
Toàn bộ dữ liệu nằm trong `index.html`, biến `var DATA = {...}` (~170KB, xem mục "Quy trình" bên dưới — KHÔNG đọc trực tiếp file này). Các phần liên quan tới quét tin:

### 1. `worldNews` / `usNews` — tin theo chuyên mục
Mảng phẳng, tin mới nhất ở đầu. Mỗi tin:
```json
{"date":"YYYY-MM-DD","category":"...","title":"...","summary":"...","sourceName":"...","sourceUrl":"https://...","significance":"...","region":"..."}
```
- `category` (chọn 1): Kinh tế · Chính trị · Công nghệ quân sự · Ngoại giao
- `region` (chỉ tin thế giới, không bắt buộc): Châu Âu/NATO · Trung Đông · Đông Á · Toàn cầu · Châu Mỹ · Ấn Độ Dương - Thái Bình Dương
- Ngày cập nhật: `DATA.generatedAt`, `DATA.worldGeneratedAt`, `DATA.usGeneratedAt`

### 2. `xNews` — tin từ X/Twitter
Mảng phẳng, tin mới nhất ở đầu. Mỗi tin:
```json
{"date":"YYYY-MM-DD","handle":"@...","name":"Tên tài khoản","title":"...","summary":"...","significance":"...","url":"https://x.com/..."}
```
Ngày cập nhật: `DATA.xGeneratedAt`. Nguồn tham khảo — loại tài khoản đã dùng trước đây: quan chức/tổ chức chính thức (@NATO, @CENTCOM, @ZelenskyyUa), hãng tin lớn (@Reuters, @AJEnglish, @SkyNews, @CBSNews), tổ chức phân tích/OSINT (@TheStudyofWar, @EU_ISS, @thewarzonewire), nhà báo/chuyên gia uy tín (@BarakRavid, @AndrewSErickson). Ưu tiên tài khoản xác thực (verified/tổ chức chính thức), không lấy tin từ tài khoản vô danh/không rõ nguồn gốc.

### 3. `exercises` (tập trận) / `dipEvents` (sự kiện ngoại giao)
KHÁC với category "Ngoại giao" ở trên — đây là các **sự kiện lớn đang diễn ra** (hội nghị thượng đỉnh, cuộc tập trận đa quốc gia...), mỗi sự kiện là 1 object có `name`, `status` (`ongoing`/`recent`/`upcoming`...), `dates`, `location`, `scale`, `summary`, và một mảng con `items` chứa các tin cập nhật liên quan, mỗi item:
```json
{"date":"YYYY-MM-DD","title":"...","summary":"...","sourceName":"...","sourceUrl":"https://..."}
```
Với **`exercises` (tập trận)**: việc quét CHỈ cập nhật `items` con vào các sự kiện **đã có sẵn** (khớp đúng `name`) — không tự tạo tập trận mới qua script; nếu có tập trận lớn hoàn toàn mới, chỉ nêu trong tóm tắt cuối để người dùng quyết định. Ưu tiên cập nhật cho sự kiện `status: "ongoing"`.

Với **`dipEvents` (sự kiện ngoại giao)** — áp dụng từ 11/07/2026 — được phép **tự động TẠO sự kiện mới** cho các sự kiện ngoại giao đáng đưa (dùng field `newDipEvents`), gồm: **ký kết/hiệp định song phương hoặc đa phương** (vd Nhật–New Zealand ký ACSA), **thượng đỉnh / hội nghị cấp cao**, **thăm cấp nguyên thủ/bộ trưởng có kết quả cụ thể**, **sáng kiến/khuôn khổ ngoại giao lớn mới**. KHÔNG tạo sự kiện cho: điện đàm/cuộc gọi thường lệ, phát ngôn đơn lẻ, tin đồn. Mỗi sự kiện mới phải có đủ `name`, `status` (`ongoing`/`recent`/`upcoming`), `dates`, `location`, `scale`, `summary`, và ≥1 `items` (nguồn chứng minh — ưu tiên nguồn chính thức tầng 1). Script tự CHẶN nếu tên trùng/giống sự kiện đã có (Jaccard ≥ 0.6) → khi đó dùng `dipEventUpdates` để thêm item vào sự kiện cũ thay vì tạo trùng. Nếu một tin đã đưa ở `worldNews`/`usNews` được nâng thành sự kiện, bỏ bản ở mảng tin phẳng để URL không trùng 2 chỗ.

## Nguồn theo 3 tầng (chuẩn báo cáo/INTREP — áp dụng từ 11/07/2026)
**Nguyên tắc:** dữ kiện/sự kiện neo vào nguồn CHÍNH THỨC (tầng 1); số liệu kinh tế/quân sự neo vào nguồn DỮ LIỆU (tầng 2); kết luận/nhận định chiến lược (field `significance` + phần Phân tích) neo vào VIỆN NGHIÊN CỨU (tầng 3). Báo chí/hãng tin (dưới cùng) dùng để PHÁT HIỆN sự kiện sớm, KHÔNG tự mình làm chỗ dựa cho kết luận — luôn đối chiếu. Tin quân sự chỉ có 1 nguồn (Army Recognition/Naval News/blog) → kiểm chứng thêm bằng thông cáo bộ quốc phòng/ảnh chính thức/Janes/SIPRI. Khi tin bắt nguồn từ thông báo chính thức, link THẲNG tới nguồn gốc tầng 1 thay vì báo dẫn lại.

### Tầng 1 — Nguồn chính thức (xác minh sự kiện; ưu tiên cao nhất)
| Nhóm | Nguồn chính thức | Handle X |
|---|---|---|
| Đa phương | NATO (nato.int), Liên Hợp Quốc (news.un.org, UN Meetings Coverage, Hội đồng Bảo an), EU/Hội đồng châu Âu (consilium.europa.eu), EEAS (eeas.europa.eu), ASEAN (asean.org) | @NATO, @UN, @EUCouncil, @ASEAN |
| Mỹ | Nhà Trắng (whitehouse.gov), Bộ Quốc phòng (defense.gov), Bộ Ngoại giao (state.gov), CENTCOM (centcom.mil), Lực lượng Không gian/Hải quân/Lục quân, Fed (federalreserve.gov), Quốc hội/CRS | @WhiteHouse, @DeptofDefense, @StateDept, @CENTCOM, @SecRubio |
| QP/NG các nước | Bộ QP Anh (gov.uk), Australia (defence.gov.au), Nhật (mod.go.jp), Hàn (mnd.go.kr), Ấn Độ, Philippines, TQ (mod.gov.cn), Nga; Bộ Ngoại giao (mofa.go.jp...); Phủ TT Ukraine (president.gov.ua) | @ZelenskyyUa |
| Việt | Chính phủ (baochinhphu.vn), Bộ Ngoại giao (mofa.gov.vn), Bộ Quốc phòng, Thông tấn xã VN (TTXVN/vietnamplus.vn), Nhân Dân (nhandan.vn), Quân đội Nhân dân (qdnd.vn) | |

**CẢNH BÁO truyền thông nhà nước độc tài** (Xinhua, TASS, Global Times, Press TV, KCNA, Sputnik...): CHỈ dùng cho phát ngôn/tuyên bố CỦA CHÍNH HỌ (vd "Trung Quốc thông báo tập trận X", "Nga tuyên bố Y") — KHÔNG dùng làm nguồn trung lập cho sự kiện gây tranh cãi, thương vong, hay bên thứ ba. Ngoại lệ của quy tắc "ưu tiên nguồn chính phủ".

### Tầng 2 — Nguồn dữ liệu (xác minh số liệu kinh tế/quân sự)
| Chủ đề | Nguồn |
|---|---|
| Kinh tế vĩ mô/tài chính/thương mại | IMF (imf.org — WEO), World Bank (data.worldbank.org), OECD (oecd.org), WTO (wto.org), BIS (bis.org), UNCTAD (unctad.org) |
| Năng lượng | IEA (iea.org) |
| Quốc phòng (số liệu) | SIPRI (sipri.org — chi tiêu QP, chuyển giao vũ khí), IISS Military Balance (*phần lớn trả phí*), Janes (*trả phí*) |

### Tầng 3 — Nguồn phân tích/viện nghiên cứu (cho `significance` + phần Phân tích)
| Khu vực/chủ đề | Nguồn |
|---|---|
| Mỹ | CSIS (+ChinaPower, AMTI về Biển Đông), RAND, Brookings, Carnegie, CFR, CNAS, Atlantic Council, Stimson, Hudson |
| Anh/Âu | RUSI, Chatham House, IISS, ECFR, SWP (Đức), IFRI (Pháp) |
| Ấn Độ Dương-TBD | Lowy Institute, ASPI (Úc), ISEAS-Yusof Ishak, RSIS (Singapore), ORF (Ấn Độ) |
| TQ/Đông Á | MERICS, Jamestown Foundation, NBR |
| Bắc Âu/Baltic/Nga | ICDS (Estonia), FIIA (Phần Lan), Belfer Center |
| Công nghệ/AI/bán dẫn/mạng | CSET (Georgetown), CSIS Strategic Technologies, CNAS Tech & National Security, DARPA, CISA, NIST, ENISA, NATO DIANA |

### Báo chí (phát hiện tin nhanh — LUÔN đối chiếu tầng 1/2/3 trước khi kết luận)
| Nhóm | Nguồn |
|---|---|
| Wire (ưu tiên RẤT CAO — chuẩn, ít bình luận) | Reuters, Associated Press (AP), Agence France-Presse (AFP) |
| Kinh tế/tài chính (*một số trả phí*) | Bloomberg, Financial Times, Wall Street Journal, The Economist, CNBC, Fortune, Nikkei Asia |
| Quốc tế/khu vực | BBC, Deutsche Welle, France 24, Al Jazeera, Al Arabiya, The Straits Times, The Japan Times, The Korea Herald, South China Morning Post, Politico, Axios, The Hindu, Africanews, The Moscow Times |
| Quốc phòng chuyên ngành | Defense News, Breaking Defense, Defense One, Naval News, USNI News, C4ISRNet, SpaceNews, Task & Purpose; *tham khảo nhanh, cần kiểm chứng*: Army Recognition, Oryx |
| Phân tích chính sách (chọn lọc, *một số trả phí*) | The Diplomat, Foreign Policy, Foreign Affairs |
| Việt | VnEconomy, VnExpress, Tuổi Trẻ, Thanh Niên, Dân Trí, Báo Mới, Thế giới & Việt Nam |

**Bộ nguồn rút gọn nên ưu tiên hằng ngày (20 nguồn):** Reuters, AP, AFP, Financial Times, Bloomberg, Nikkei Asia, NATO, ASEAN, UN Meetings Coverage, IMF, World Bank, OECD, SIPRI, IISS, Janes, CSIS, RAND, RUSI, Chatham House, CSET — đủ 4 lớp: tin nhanh · dữ liệu kinh tế · dữ liệu quân sự · phân tích chiến lược.

## URL RSS đã biết (CHƯA VERIFY bằng fetch thật — dùng thử trước, có sự cố thì fallback WebSearch ngay)
Tổng hợp qua WebSearch ngày 10/07/2026, lúc đó WebFetch trong môi trường đang lỗi 403 hệ thống (kể cả với example.com) nên chưa mở thử được để xác nhận nội dung XML thật. Mục đích: agent dùng thẳng URL này thay vì tốn 1 bước tìm kiếm "RSS feed của X ở đâu" mỗi lần quét — nếu URL nào lỗi/không parse được, bỏ ngay, không retry, chuyển sang WebSearch cho nguồn đó, và cân nhắc sửa lại dòng tương ứng trong bảng này.

| Nguồn | RSS URL |
|---|---|
| Defense News | https://www.defensenews.com/arc/outboundfeeds/rss/category/global/?outputType=xml |
| Naval News | https://www.navalnews.com/feed/ |
| Breaking Defense | https://breakingdefense.com/full-rss-feed/ |
| Defense One | https://www.defenseone.com/rss/all/ |
| SpaceNews | https://spacenews.com/feed/ |
| Task & Purpose | https://taskandpurpose.com/feed |
| Al Jazeera | https://www.aljazeera.com/xml/rss/all.xml |
| Al Arabiya | https://english.alarabiya.net/rss/en_default.xml |
| The Straits Times | https://www.straitstimes.com/news/world/rss.xml |
| The Moscow Times | https://www.themoscowtimes.com/rss/news |
| South China Morning Post | https://www.scmp.com/rss/5/feed/ |
| Politico | http://www.politico.com/rss/politicopicks.xml |
| Axios | https://www.axios.com/feeds/feed.rss |
| CNBC | https://www.cnbc.com/id/100727362/device/rss/rss.html |
| Fortune | https://content.fortune.com/feed/ |
| The Hindu | https://www.thehindu.com/news/international/feeder/default.rss |
| Africanews | https://www.africanews.com/feed/rss |
| BBC World | http://feeds.bbci.co.uk/news/world/rss.xml |
| Deutsche Welle | https://rss.dw.com/rdf/rss-en-world |
| France 24 | https://www.france24.com/en/rss |
| UN News | https://news.un.org/feed/subscribe/en/news/all/rss.xml |
| NATO | https://www.nato.int/cps/en/natohq/news.rss (chưa chắc; fallback WebSearch site:nato.int) |
| USNI News | https://news.usni.org/feed |
| C4ISRNet | https://www.c4isrnet.com/arc/outboundfeeds/rss/?outputType=xml |
| The Diplomat | https://thediplomat.com/feed/ |
| Nikkei Asia | https://asia.nikkei.com/rss (một phần trả phí) |
| Reuters / AP / AFP | Không có RSS công khai ổn định — dùng WebSearch (site:reuters.com / apnews.com / barrons/afp) |
| VnEconomy | https://vneconomy.vn/rss/home.rss (chưa chắc, thử fallback trang RSS tổng https://vneconomy.vn/rss.html nếu lỗi) |
| VnExpress | https://vnexpress.net/rss/the-gioi.rss |
| Tuổi Trẻ | https://tuoitre.vn/rss/the-gioi.rss |
| Thanh Niên | https://thanhnien.vn/rss/the-gioi.rss |
| Dân Trí | http://dantri.com.vn/Thegioi.rss |
| Báo Mới | Không có RSS xác định được — dùng WebSearch |
| Thế giới & Việt Nam | Không có RSS xác định được — dùng WebSearch |

## Thứ tự ưu tiên khi chọn nguồn để quét (áp dụng từ 10/07/2026, cập nhật 10/07 thêm ưu tiên #1)
1. **Ưu tiên nguồn chính phủ/chính thức (primary).** Khi một tin dựa trên thông báo/phát ngôn/tài liệu chính thức, ưu tiên link THẲNG tới nguồn gốc (defense.gov, nato.int, state.gov, whitehouse.gov, baochinhphu.vn...) thay vì chỉ dẫn lại báo chí. Chủ động tìm tin đáng đưa từ các nguồn chính thức này. LƯU Ý ngoại lệ truyền thông nhà nước độc tài (xem cảnh báo ở mục "Nguồn chính phủ/chính thức").
2. **Ưu tiên nguồn tiếng Anh** trước nguồn tiếng Việt. Nguồn Việt chỉ dùng bổ sung khi nguồn Anh không đủ tin, hoặc để lấy góc nhìn/tin trong nước.
3. **Ưu tiên nguồn có RSS feed** trước — nhanh và chính xác hơn tìm kiếm/web scraping thủ công. Nếu nguồn không có RSS hoặc RSS không truy cập được, mới dùng WebSearch/WebFetch.
4. **Ưu tiên nguồn CHƯA từng được quét trước đó.** Kiểm tra bằng `grep -oE "\"sourceName\":\"[^\"]+\"" index.html | sort | uniq -c` để biết nguồn nào đang bị bỏ sót.
5. **Điều hướng theo sở thích người đọc.** Người đọc bấm 👍/👎 trên từng tin, đồng bộ lên Supabase (giao diện KHÔNG hiển thị phân tích sở thích — chỉ thu vote; phân tích là việc của quy trình quét). Mỗi lần quét, session **đọc file local `preferences.json`** (gốc repo) để ưu tiên (điểm dương `net`) / giảm ưu tiên (điểm âm) chuyên mục · khu vực · nguồn. File này do **GitHub Action `sync-preferences.yml`** tự cập nhật hằng ngày: Action chạy trên máy GitHub (không bị Cloudflare chặn như môi trường quét), curl view công khai `vote_stats` từ Supabase rồi commit vào `main`. Đây là **định hướng mềm**: vẫn giữ tối thiểu 2 tin/category, không bỏ hẳn mục nào, không ghi đè quy tắc nguồn 3 tầng/chất lượng. (Chi tiết: `preferences.md`. Schema: `docs/supabase-setup.sql`.) LƯU Ý: KHÔNG tự WebFetch `*.supabase.co` khi quét — bị chặn 403 (đã kiểm chứng 12/07), việc lấy dữ liệu đã có Action lo.

## Chỉ tiêu số lượng mỗi lần quét (bắt buộc)
| Phần | Chỉ tiêu |
|---|---|
| `worldNews` | Tối thiểu 2, mục tiêu 2–3 tin **cho MỖI category** trong 4 category → tổng ~8–12 tin |
| `usNews` | Tối thiểu 2, mục tiêu 2–3 tin **cho MỖI category** trong 4 category → tổng ~8–12 tin |
| `xNews` | 4–5 tin mới |
| `exercises` (tập trận) | 1–2 tin cập nhật (vào sự kiện `ongoing` phù hợp) |
| `dipEvents` (ngoại giao) | 1–2 tin cập nhật (vào sự kiện `ongoing` phù hợp) |

Nếu một phần thực sự không đủ chỉ tiêu sau khi đã thử nhiều nguồn — chấp nhận thiếu, KHÔNG bịa tin/link, nêu rõ trong tóm tắt cuối.

## Kiến trúc quét: nhiều agent Sonnet nhỏ (bắt buộc — để nhẹ và chống sập)
Không dùng 1 agent lớn ôm hết việc quét (dễ quá tải/timeout/tốn token). Session điều phối (session hiện tại) tự thực hiện các bước đọc `DATA`/kiểm tra nguồn đã dùng, sau đó **dùng tool Agent để giao việc quét cho các subagent chạy model Sonnet (`model: "sonnet"`)**, mỗi agent chỉ phụ trách MỘT phần vừa phải:

> Ghi chú model (10/07/2026): trước dùng Haiku cho rẻ nhưng lần quét đầu tiên tỷ lệ lỗi cao (~40-50% tin bị loại: sai ngày, link rác/không khớp, trùng tin cũ, mâu thuẫn dữ liệu, bịa ID). Đã đổi sang **Sonnet** để tin thu thập chính xác hơn từ đầu (tốn token hơn Haiku nhưng giảm mạnh vòng quét lại + công review). Guardrail tự động trong `add_news.py` (xem mục Guardrail) vẫn là lớp chặn cuối cùng bất kể model nào.

| Agent | Phạm vi | Sản lượng mỗi agent |
|---|---|---|
| 1 | Category "Kinh tế" — cả worldNews + usNews | ~4–6 tin |
| 2 | Category "Chính trị" — cả worldNews + usNews | ~4–6 tin |
| 3 | Category "Công nghệ quân sự" — cả worldNews + usNews | ~4–6 tin |
| 4 | Category "Ngoại giao" — cả worldNews + usNews | ~4–6 tin |
| 5 | xNews | 4–5 tin |
| 6 | exercises + dipEvents (cập nhật sự kiện ongoing) | 1–2 tin mỗi loại |

Quy tắc khi giao việc cho từng agent (viết prompt độc lập, đầy đủ ngữ cảnh vì subagent KHÔNG thấy hội thoại chính):
- **KHÔNG bảo subagent tự đọc `CLAUDE.md`** — file này ngày càng dài, để 6 agent cùng đọc là lãng phí token 6 lần. Agent điều phối tự trích đúng phần cần (nguồn phù hợp + URL RSS nếu có + định dạng field) rồi nhúng thẳng nội dung đó vào prompt của từng agent.
- Nêu rõ: phạm vi (category/phần), chỉ tiêu số lượng, danh sách nguồn phù hợp kèm URL RSS đã biết (xem bảng RSS bên dưới — đưa thẳng URL, không bắt agent tự dò), định dạng field bắt buộc đúng như trên.
- **Ràng buộc chất lượng — nhúng vào MỌI prompt agent** (rút ra từ lỗi lần quét đầu 10/07): (a) `date` phải trong 48h–3 ngày gần nhất, KHÔNG lấy tin cũ hơn; (b) `sourceUrl` phải trỏ THẲNG tới 1 bài viết cụ thể, KHÔNG dùng link trang chủ / "live updates" / live-blog / trang tổng hợp, và link phải KHỚP đúng nội dung tin; (c) `sourceName` chỉ trong danh sách nguồn được giao (báo chí) HOẶC nguồn chính phủ/chính thức phù hợp; (d) với xNews: KHÔNG bịa status ID (ID thật ~19 chữ số ngẫu nhiên, không tròn số); (e) thà ÍT tin đạt chuẩn còn hơn nhồi tin sai — được phép trả mảng rỗng.
- **Ưu tiên nguồn chính phủ/chính thức**: khi tin bắt nguồn từ thông báo/phát ngôn chính thức (defense.gov, nato.int, state.gov, whitehouse.gov, centcom.mil, baochinhphu.vn, mofa.gov.vn...), ưu tiên link thẳng nguồn gốc đó thay vì báo dẫn lại. Với truyền thông nhà nước độc tài (Xinhua/TASS/Global Times/Press TV/KCNA): chỉ dùng cho phát ngôn của chính họ, không làm nguồn trung lập cho sự kiện tranh cãi/thương vong.
- **Đa dạng hoá sự kiện**: mỗi tin trong batch nên là một sự kiện/câu chuyện KHÁC NHAU. Tránh việc 2-3 "tin" trong cùng category thực chất chỉ là cùng 1 sự kiện do nhiều báo đưa lại — vậy chỉ tính 1, chọn nguồn tường thuật tốt nhất.
- **Chống trùng với tin cũ (BẮT BUỘC nhúng ĐẦY ĐỦ, không cắt rời từng mục)**: agent điều phối chạy `python3 scripts/add_news.py --recent-titles 20` (rẻ, không đọc cả file — output gồm tiêu đề gần đây của worldNews + usNews + xNews + item các sự kiện) rồi dán **NGUYÊN khối output đó vào prompt của TẤT CẢ 6 subagent** (kể cả agent xNews và agent exercise), kèm dặn "không report lại bất kỳ tin/sự kiện nào đã có trong danh sách này, kể cả dưới tiêu đề/góc nhìn khác, trừ khi có diễn biến MỚI HẲN". Lý do phải nhúng đủ cho mọi agent: lần quét đầu agent xNews/exercise re-report tin mà agent worldNews đã lấy vì chỉ được đưa danh sách rời của mục mình.
- **Cảnh báo dữ liệu thực tế mâu thuẫn**: khi có sự kiện đang tiếp diễn (vd chiến sự, ngừng bắn), agent điều phối phải tóm tắt trạng thái mới nhất đã đăng và dặn agent không đưa tin mâu thuẫn với trạng thái đó (lần đầu có agent đưa tin "ngừng bắn vẫn duy trì" trong khi dữ liệu đã ghi ngừng bắn bị chấm dứt).
- Yêu cầu agent CHỈ trả lời bằng đoạn JSON kết quả (mảng tin của phần đó) — không giải thích dài dòng, để việc gộp kết quả ở agent điều phối rẻ.
- Không bịa link — bỏ tin nếu không chắc `sourceUrl`.
- Gọi các agent này song song trong cùng 1 lượt (không cần tuần tự) để tiết kiệm thời gian, dùng `run_in_background: false` vì cần kết quả ngay để lắp ráp.

Sau khi các agent trả kết quả, session điều phối **tự review từng tin** (đối chiếu ràng buộc chất lượng trên) trước khi gộp — loại tin không đạt, giữ tin tốt. Rồi gộp toàn bộ JSON con thành 1 file `/tmp/new_items.json` theo đúng format ở dưới, chạy script (script sẽ chặn lần cuối các lỗi máy bắt được).

## Guardrail tự động trong `scripts/add_news.py` (lớp chặn cuối, không tốn token)
Chạy `python3 scripts/add_news.py /tmp/new_items.json` sẽ tự động **CHẶN (raise lỗi, phải sửa JSON rồi chạy lại)** nếu gặp: thiếu field bắt buộc; `category` sai; `date` ngoài khung (cũ hơn 5 ngày so với ngày batch, hoặc ở tương lai); `sourceUrl` là trang chủ hoặc live-blog/live-updates; URL trùng nhau trong batch; URL đã có sẵn trong `DATA` (tin trùng); status ID X vô lý (quá ngắn hoặc kết thúc nhiều số 0 — nghi bịa); tên exercise/dipEvent (trong `*Updates`) không khớp entry có sẵn; tên sự kiện trong `newDipEvents` trùng/giống sự kiện đã có (Jaccard ≥ 0.6) hoặc thiếu field bắt buộc của sự kiện. Ngoài ra **CẢNH BÁO (in ra, không chặn)**: `sourceName` lạ ngoài danh sách nguồn đã biết; tiêu đề nghi trùng với tin cũ (Jaccard ≥ 0.6); phần nào chưa đủ chỉ tiêu số lượng. Khi script chặn: đọc thông báo, sửa/bỏ tin lỗi trong JSON rồi chạy lại — KHÔNG tự sửa `index.html` bằng tay.

## Quy trình mỗi lần quét (tối ưu token — QUAN TRỌNG)
`index.html` nặng ~170KB. **TUYỆT ĐỐI KHÔNG dùng tool Read để đọc toàn bộ `index.html`.**

1. Kiểm tra ngày cập nhật gần nhất bằng grep: `grep -oE '"generatedAt":"[^"]+"' index.html | head -1`
2. Kiểm tra tần suất nguồn đã dùng bằng grep: `grep -oE '"sourceName":"[^"]+"' index.html | sort | uniq -c | sort -rn`
2b. Lấy tiêu đề gần đây để chống trùng: `python3 scripts/add_news.py --recent-titles 20`
3. Giao việc cho 6 agent Sonnet theo bảng kiến trúc ở trên, mỗi agent tự áp dụng thứ tự ưu tiên nguồn + ưu tiên RSS (dùng URL RSS đã chốt sẵn ở bảng dưới nếu có), nhúng NGUYÊN khối danh sách tiêu đề gần đây (bước 2b) + ràng buộc chất lượng + quy tắc đa dạng hoá sự kiện vào prompt MỖI agent.
4. Gộp kết quả các agent thành 1 file JSON, ví dụ ghi bằng heredoc vào `/tmp/new_items.json`, format:
   ```json
   {
     "date": "YYYY-MM-DD",
     "worldNews": [ {...} ],
     "usNews": [ {...} ],
     "xNews": [ {...} ],
     "exerciseUpdates": [ {"name": "<tên đúng đã có trong DATA>", "items": [ {...} ]} ],
     "dipEventUpdates": [ {"name": "<tên đúng đã có trong DATA>", "items": [ {...} ]} ],
     "newDipEvents": [ {"name":"...","status":"recent","dates":"...","location":"...","scale":"...","summary":"...","items":[ {...} ]} ]
   }
   ```
5. Chèn vào `index.html` bằng script có sẵn, KHÔNG dùng Edit/Write trực tiếp lên `index.html`:
   `python3 scripts/add_news.py /tmp/new_items.json`
   Script tự động chèn tin + cập nhật ngày + validate + guardrail (xem mục "Guardrail tự động" ở trên để biết các lỗi bị CHẶN vs CẢNH BÁO). Nếu script chặn, sửa/bỏ tin lỗi trong JSON rồi chạy lại — không tự sửa `index.html` bằng tay.
   - Nếu phần nào thiếu chỉ tiêu, giao thêm 1 agent Sonnet bổ sung riêng cho phần đó rồi chạy lại script (script cộng dồn an toàn, không tạo trùng vì mỗi lần chỉ gồm tin mới).
6. Commit theo mẫu: `Cap nhat ban tin DD/MM: +N tin (TG +x, My +y, X +z)`, push vào `main`.
7. Tóm tắt cuối cùng: ngắn gọn — tổng số tin từng phần, bảng phân bổ category, phần nào thiếu chỉ tiêu (nếu có), trạng thái push. Không liệt kê lại toàn bộ nội dung từng tin.

## Đánh giá lại chiến lược quét
**Vào hoặc sau ngày 17/07/2026** (1 tuần kể từ khi áp dụng quy tắc này), xem lại:
- Nguồn nào có RSS ổn định, tin chất lượng, đúng chủ đề → giữ ưu tiên cao.
- Nguồn nào khó truy cập, tin trùng lặp/nhiễu, hoặc RSS không hoạt động → hạ ưu tiên hoặc loại bỏ.
- Cập nhật lại danh sách và thứ tự ưu tiên trong file này cho phù hợp.
- **Verify lại bảng "URL RSS đã biết"** ở trên bằng dữ liệu thực tế 1 tuần quét: URL nào agent xác nhận dùng được (trả JSON hợp lệ) → giữ; URL nào lỗi/sai → sửa hoặc đánh dấu "Không có RSS".

## Log & tự phục hồi (Routine tự động)
Routine chạy trong session mới (ephemeral) nên phải để lại dấu vết để chẩn đoán khi lỗi:
- **Log bắt buộc mỗi lần chạy**: ghi vào `logs/scan-<NGÀY-VN>.log` (ngày theo `TZ='Asia/Ho_Chi_Minh' date +%F`) các mốc: START, kết quả từng agent/phần, chạy script, và DONE/SKIP/FAIL kèm lý do. **Luôn commit + push file log** kể cả khi quét thất bại (git không cần mạng ngoài nên push được ngay cả khi WebSearch/WebFetch bị chặn) — đây là cách duy nhất biết Routine fail ở đâu.
- **Idempotent (chống chạy trùng)**: đầu mỗi lần chạy, đọc `grep -oE '"generatedAt":"[^"]+"' index.html | head -1`. Nếu `generatedAt` == ngày hôm nay (VN) → bản tin hôm nay ĐÃ XONG, ghi log `SKIP`, push log, KẾT THÚC (không quét lại).
- **Retry cho tới khi xong**: Routine fire mỗi giờ lúc 19:00, 20:00, 21:00 VN (`0 12-14 * * *` UTC — bắt đầu 7h tối, chưa xong thì 8h, rồi 9h). Nhờ bước idempotent, khi đã xong thì các lần fire sau tự no-op; nếu chưa xong thì lần sau quét lại. (Scheduler tối thiểu 1 giờ/lần — không đặt 15 phút được; nếu cần 15 phút phải chuyển sang GitHub Actions.)

## Ghi chú vận hành
- Routine tự động chạy lúc 19:00 → 20:00 → 21:00 giờ VN (`0 12-14 * * *` UTC), tạo session mới mỗi lần, tự đọc file này để lấy quy tắc, có log + idempotent + retry (xem mục trên).
- Việc quét thực tế (WebSearch/WebFetch/RSS) được giao cho các subagent chạy **model Sonnet** theo kiến trúc ở trên — session điều phối review + gộp kết quả, chạy script, commit/push. KHÔNG đọc `index.html` (172KB) trực tiếp — dùng `scripts/add_news.py`.
- **Bài học lần quét đầu 10/07/2026** (đã xử lý): tỷ lệ loại tin cao do (1) Haiku yếu → đã đổi Sonnet; (2) agent thiếu danh sách chống trùng đầy đủ chéo mục → đã bắt buộc nhúng nguyên khối `--recent-titles` cho mọi agent; (3) không có kiểm tra máy → đã thêm guardrail trong script; (4) WebFetch lỗi 403 hệ thống nên không tự verify link được — nếu sau này WebFetch ổn định, có thể thêm 1 pass verify `sourceUrl` bằng WebFetch trước khi publish (tùy chọn, tốn token).
- **Đã thử và KHÔNG khả thi**: dùng `curl` thuần trong Bash để tự kiểm tra link chết (`sourceUrl`) trước khi publish — môi trường chặn `curl`/kết nối HTTPS thô tới domain ngoài ở tầng network policy (chỉ tool WebFetch/WebSearch mới có đường truy cập web được duyệt riêng). Đừng thử lại `curl -I` để check link — sẽ luôn bị từ chối (403 ở tầng proxy). Nếu cần verify link, phải dùng WebFetch (tốn token hơn) — hiện KHÔNG bắt buộc làm bước này, dựa vào quy tắc "không chắc link thì bỏ" là chính.
