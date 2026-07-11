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
Việc quét CHỈ cập nhật `items` con vào các sự kiện **đã có sẵn** (khớp đúng `name`) — không tự tạo sự kiện mới (tránh dữ liệu sai lệch/trùng). Ưu tiên cập nhật cho sự kiện có `status: "ongoing"` (đang diễn ra) vì khả năng có tin mới cao nhất. Nếu có sự kiện lớn hoàn toàn mới (một hội nghị/tập trận chưa từng có trong `exercises`/`dipEvents`) — không tự thêm qua script, chỉ nêu trong tóm tắt cuối để người dùng quyết định có thêm entry mới hay không.

## Nguồn chính phủ/chính thức (ƯU TIÊN CAO NHẤT — dùng khi tin bắt nguồn từ thông báo/phát ngôn chính thức)
Ưu tiên link THẲNG tới nguồn gốc chính thức khi một tin dựa trên thông báo/phát ngôn/tài liệu của chính phủ, quân đội, tổ chức đa phương — vì đây là nguồn sơ cấp (primary), chính xác nhất, ít bị diễn giải sai. Vẫn dùng báo chí (danh sách dưới) cho tin không có nguồn chính thức, cho tường thuật/phân tích, và để đối chiếu.

| Nhóm | Nguồn chính thức | Handle X |
|---|---|---|
| Đa phương | NATO (nato.int), Liên Hợp Quốc (news.un.org), EU/Hội đồng châu Âu (consilium.europa.eu), IMF (imf.org) | @NATO, @UN, @EUCouncil, @IMFNews |
| Mỹ | Nhà Trắng (whitehouse.gov), Bộ Quốc phòng (defense.gov), Bộ Ngoại giao (state.gov), CENTCOM (centcom.mil), Lực lượng Không gian/Hải quân/Lục quân, Fed (federalreserve.gov) | @WhiteHouse, @DeptofDefense, @StateDept, @CENTCOM, @SecRubio |
| Nước khác | Bộ Quốc phòng Anh (gov.uk), Phủ Tổng thống Ukraine (president.gov.ua), các bộ ngoại giao/quốc phòng liên quan | @ZelenskyyUa |
| Việt | Chính phủ (baochinhphu.vn), Bộ Ngoại giao (mofa.gov.vn), Bộ Quốc phòng | |

**CẢNH BÁO truyền thông nhà nước độc tài** (Xinhua, TASS, Global Times, Press TV, KCNA, Sputnik...): CHỈ dùng cho phát ngôn/tuyên bố CỦA CHÍNH HỌ (vd "Trung Quốc thông báo tập trận X", "Nga tuyên bố Y") — KHÔNG dùng làm nguồn trung lập cho sự kiện gây tranh cãi, thương vong, hay bên thứ ba; luôn ưu tiên nguồn độc lập cho các nội dung đó. Đây là ngoại lệ của quy tắc "ưu tiên nguồn chính phủ".

## Danh sách nguồn (báo chí — dùng cho tường thuật/phân tích và tin không có nguồn chính thức)
| Nhóm | Nguồn |
|---|---|
| Quốc phòng/quân sự (Anh) | Defense News, Naval News, Breaking Defense, Defense One, SpaceNews, Task & Purpose |
| Quốc tế tổng hợp (Anh) | Al Jazeera, Al Arabiya, The Straits Times, The Moscow Times, South China Morning Post, Politico, Axios, The Hindu, Africanews |
| Kinh tế (Anh) | CNBC, Fortune |
| Việt | VnEconomy, VnExpress, Tuổi Trẻ, Thanh Niên, Dân Trí, Báo Mới, Thế giới & Việt Nam |

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
Chạy `python3 scripts/add_news.py /tmp/new_items.json` sẽ tự động **CHẶN (raise lỗi, phải sửa JSON rồi chạy lại)** nếu gặp: thiếu field bắt buộc; `category` sai; `date` ngoài khung (cũ hơn 5 ngày so với ngày batch, hoặc ở tương lai); `sourceUrl` là trang chủ hoặc live-blog/live-updates; URL trùng nhau trong batch; URL đã có sẵn trong `DATA` (tin trùng); status ID X vô lý (quá ngắn hoặc kết thúc nhiều số 0 — nghi bịa); tên exercise/dipEvent không khớp entry có sẵn. Ngoài ra **CẢNH BÁO (in ra, không chặn)**: `sourceName` lạ ngoài danh sách nguồn đã biết; tiêu đề nghi trùng với tin cũ (Jaccard ≥ 0.6); phần nào chưa đủ chỉ tiêu số lượng. Khi script chặn: đọc thông báo, sửa/bỏ tin lỗi trong JSON rồi chạy lại — KHÔNG tự sửa `index.html` bằng tay.

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
     "dipEventUpdates": [ {"name": "<tên đúng đã có trong DATA>", "items": [ {...} ]} ]
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
- **Retry cho tới khi xong**: Routine fire mỗi giờ trong khung tối (20:00–23:00 VN = `0 13-16 * * *` UTC, 4 lần). Nhờ bước idempotent, khi đã xong thì các lần fire sau tự no-op; nếu chưa xong thì lần sau quét lại. (Scheduler tối thiểu 1 giờ/lần — không đặt 15 phút được; nếu cần 15 phút phải chuyển sang GitHub Actions.)

## Ghi chú vận hành
- Routine tự động chạy mỗi giờ khung tối 20:00–23:00 giờ VN (`0 13-16 * * *` UTC), tạo session mới mỗi lần, tự đọc file này để lấy quy tắc, có log + idempotent + retry (xem mục trên).
- Việc quét thực tế (WebSearch/WebFetch/RSS) được giao cho các subagent chạy **model Sonnet** theo kiến trúc ở trên — session điều phối review + gộp kết quả, chạy script, commit/push. KHÔNG đọc `index.html` (172KB) trực tiếp — dùng `scripts/add_news.py`.
- **Bài học lần quét đầu 10/07/2026** (đã xử lý): tỷ lệ loại tin cao do (1) Haiku yếu → đã đổi Sonnet; (2) agent thiếu danh sách chống trùng đầy đủ chéo mục → đã bắt buộc nhúng nguyên khối `--recent-titles` cho mọi agent; (3) không có kiểm tra máy → đã thêm guardrail trong script; (4) WebFetch lỗi 403 hệ thống nên không tự verify link được — nếu sau này WebFetch ổn định, có thể thêm 1 pass verify `sourceUrl` bằng WebFetch trước khi publish (tùy chọn, tốn token).
- **Đã thử và KHÔNG khả thi**: dùng `curl` thuần trong Bash để tự kiểm tra link chết (`sourceUrl`) trước khi publish — môi trường chặn `curl`/kết nối HTTPS thô tới domain ngoài ở tầng network policy (chỉ tool WebFetch/WebSearch mới có đường truy cập web được duyệt riêng). Đừng thử lại `curl -I` để check link — sẽ luôn bị từ chối (403 ở tầng proxy). Nếu cần verify link, phải dùng WebFetch (tốn token hơn) — hiện KHÔNG bắt buộc làm bước này, dựa vào quy tắc "không chắc link thì bỏ" là chính.
