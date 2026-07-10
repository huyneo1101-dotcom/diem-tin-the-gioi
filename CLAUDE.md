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

## Danh sách nguồn
| Nhóm | Nguồn |
|---|---|
| Quốc phòng/quân sự (Anh) | Defense News, Naval News, Breaking Defense, Defense One, SpaceNews, Task & Purpose |
| Quốc tế tổng hợp (Anh) | Al Jazeera, Al Arabiya, The Straits Times, The Moscow Times, South China Morning Post, Politico, Axios, The Hindu, Africanews |
| Kinh tế (Anh) | CNBC, Fortune |
| Việt | VnEconomy, VnExpress, Tuổi Trẻ, Thanh Niên, Dân Trí, Báo Mới, Thế giới & Việt Nam |

## Thứ tự ưu tiên khi chọn nguồn để quét (áp dụng từ 10/07/2026)
1. **Ưu tiên nguồn tiếng Anh** trước nguồn tiếng Việt. Nguồn Việt chỉ dùng bổ sung khi nguồn Anh không đủ tin, hoặc để lấy góc nhìn/tin trong nước.
2. **Trong nhóm đã chọn, ưu tiên nguồn có RSS feed** trước — nhanh và chính xác hơn tìm kiếm/web scraping thủ công. Nếu nguồn không có RSS hoặc RSS không truy cập được, mới dùng WebSearch/WebFetch.
3. **Ưu tiên nguồn CHƯA từng được quét trước đó.** Kiểm tra bằng `grep -oE "\"sourceName\":\"[^\"]+\"" index.html | sort | uniq -c` để biết nguồn nào đang bị bỏ sót.

## Chỉ tiêu số lượng mỗi lần quét (bắt buộc)
| Phần | Chỉ tiêu |
|---|---|
| `worldNews` | Tối thiểu 2, mục tiêu 2–3 tin **cho MỖI category** trong 4 category → tổng ~8–12 tin |
| `usNews` | Tối thiểu 2, mục tiêu 2–3 tin **cho MỖI category** trong 4 category → tổng ~8–12 tin |
| `xNews` | 4–5 tin mới |
| `exercises` (tập trận) | 1–2 tin cập nhật (vào sự kiện `ongoing` phù hợp) |
| `dipEvents` (ngoại giao) | 1–2 tin cập nhật (vào sự kiện `ongoing` phù hợp) |

Nếu một phần thực sự không đủ chỉ tiêu sau khi đã thử nhiều nguồn — chấp nhận thiếu, KHÔNG bịa tin/link, nêu rõ trong tóm tắt cuối.

## Kiến trúc quét: nhiều agent Haiku nhỏ (bắt buộc — để nhẹ và chống sập)
Không dùng 1 agent lớn ôm hết việc quét (dễ quá tải/timeout/tốn token). Session điều phối (session hiện tại) tự thực hiện các bước đọc `DATA`/kiểm tra nguồn đã dùng, sau đó **dùng tool Agent để giao việc quét cho các subagent chạy model Haiku (`model: "haiku"`)**, mỗi agent chỉ phụ trách MỘT phần vừa phải:

| Agent | Phạm vi | Sản lượng mỗi agent |
|---|---|---|
| 1 | Category "Kinh tế" — cả worldNews + usNews | ~4–6 tin |
| 2 | Category "Chính trị" — cả worldNews + usNews | ~4–6 tin |
| 3 | Category "Công nghệ quân sự" — cả worldNews + usNews | ~4–6 tin |
| 4 | Category "Ngoại giao" — cả worldNews + usNews | ~4–6 tin |
| 5 | xNews | 4–5 tin |
| 6 | exercises + dipEvents (cập nhật sự kiện ongoing) | 1–2 tin mỗi loại |

Quy tắc khi giao việc cho từng agent (viết prompt độc lập, đầy đủ ngữ cảnh vì subagent KHÔNG thấy hội thoại chính):
- Nêu rõ: phạm vi (category/phần), chỉ tiêu số lượng, danh sách nguồn phù hợp (lọc từ bảng nguồn ở trên theo đúng thứ tự ưu tiên Anh > RSS > chưa quét), định dạng field bắt buộc đúng như trên.
- Yêu cầu agent CHỈ trả lời bằng đoạn JSON kết quả (mảng tin của phần đó) — không giải thích dài dòng, để việc gộp kết quả ở agent điều phối rẻ.
- Không bịa link — bỏ tin nếu không chắc `sourceUrl`.
- Gọi các agent này song song trong cùng 1 lượt (không cần tuần tự) để tiết kiệm thời gian, dùng `run_in_background: false` vì cần kết quả ngay để lắp ráp.

Sau khi các agent trả kết quả, session điều phối gộp toàn bộ JSON con thành 1 file `/tmp/new_items.json` theo đúng format ở dưới, rồi chạy script để ghi vào `index.html`.

## Quy trình mỗi lần quét (tối ưu token — QUAN TRỌNG)
`index.html` nặng ~170KB. **TUYỆT ĐỐI KHÔNG dùng tool Read để đọc toàn bộ `index.html`.**

1. Kiểm tra ngày cập nhật gần nhất bằng grep: `grep -oE '"generatedAt":"[^"]+"' index.html | head -1`
2. Kiểm tra tần suất nguồn đã dùng bằng grep: `grep -oE '"sourceName":"[^"]+"' index.html | sort | uniq -c | sort -rn`
3. Giao việc cho 6 agent Haiku theo bảng kiến trúc ở trên, mỗi agent tự áp dụng thứ tự ưu tiên nguồn + ưu tiên RSS.
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
   Script tự động: chèn tin mới vào đầu các mảng tương ứng, cập nhật `generatedAt`/`worldGeneratedAt`/`usGeneratedAt`/`xGeneratedAt`, chèn `items` vào đúng entry `exercises`/`dipEvents` khớp tên, validate field bắt buộc, in bảng phân bổ category + cảnh báo phần nào chưa đủ chỉ tiêu. Nếu báo lỗi (vd tên exercise/dipEvent không khớp), sửa lại JSON rồi chạy lại — không tự sửa `index.html` bằng tay.
   - Nếu phần nào thiếu chỉ tiêu, giao thêm 1 agent Haiku bổ sung riêng cho phần đó rồi chạy lại script (script cộng dồn an toàn, không tạo trùng vì mỗi lần chỉ gồm tin mới).
6. Commit theo mẫu: `Cap nhat ban tin DD/MM: +N tin (TG +x, My +y, X +z)`, push vào `main`.
7. Tóm tắt cuối cùng: ngắn gọn — tổng số tin từng phần, bảng phân bổ category, phần nào thiếu chỉ tiêu (nếu có), trạng thái push. Không liệt kê lại toàn bộ nội dung từng tin.

## Đánh giá lại chiến lược quét
**Vào hoặc sau ngày 17/07/2026** (1 tuần kể từ khi áp dụng quy tắc này), xem lại:
- Nguồn nào có RSS ổn định, tin chất lượng, đúng chủ đề → giữ ưu tiên cao.
- Nguồn nào khó truy cập, tin trùng lặp/nhiễu, hoặc RSS không hoạt động → hạ ưu tiên hoặc loại bỏ.
- Cập nhật lại danh sách và thứ tự ưu tiên trong file này cho phù hợp.

## Ghi chú vận hành
- Routine tự động **đã tạo thành công** (10/07/2026), chạy mỗi ngày 20:00 giờ VN (`0 13 * * *` UTC), tạo session mới mỗi lần chạy, tự đọc file này để lấy quy tắc.
- Việc quét thực tế (WebSearch/WebFetch/RSS) được giao cho các subagent chạy **model Haiku** (rẻ, nhanh) theo kiến trúc ở trên — session điều phối chỉ lo gộp kết quả, chạy script, commit/push (rẻ, ít token). KHÔNG đọc `index.html` (172KB) trực tiếp — dùng `scripts/add_news.py`.
