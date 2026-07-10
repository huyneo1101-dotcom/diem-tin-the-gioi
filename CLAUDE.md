# Điểm Tin Thế Giới — quy tắc quét tin

Trang tin tĩnh (PWA) tiếng Việt, deploy tự động lên GitHub Pages khi push vào `main`.

## Nơi lưu dữ liệu
Toàn bộ tin nằm trong `index.html`, biến `var DATA = {...}`:
- `DATA.worldNews` — mảng tin Thế giới
- `DATA.usNews` — mảng tin Mỹ
- `DATA.generatedAt`, `DATA.worldGeneratedAt`, `DATA.usGeneratedAt` — ngày cập nhật (`YYYY-MM-DD`)

Mỗi tin:
```json
{"date":"YYYY-MM-DD","category":"...","title":"...","summary":"...","sourceName":"...","sourceUrl":"https://...","significance":"...","region":"..."}
```
`region` chỉ dùng cho tin thế giới, không bắt buộc.

- `category` (chọn 1): Kinh tế · Chính trị · Công nghệ quân sự · Ngoại giao
- `region`: Châu Âu/NATO · Trung Đông · Đông Á · Toàn cầu · Châu Mỹ · Ấn Độ Dương - Thái Bình Dương

## Danh sách nguồn
| Nhóm | Nguồn |
|---|---|
| Quốc phòng/quân sự (Anh) | Defense News, Naval News, Breaking Defense, Defense One, SpaceNews, Task & Purpose |
| Quốc tế tổng hợp (Anh) | Al Jazeera, Al Arabiya, The Straits Times, The Moscow Times, South China Morning Post, Politico, Axios, The Hindu, Africanews |
| Kinh tế (Anh) | CNBC, Fortune |
| Việt | VnEconomy, VnExpress, Tuổi Trẻ, Thanh Niên, Dân Trí, Báo Mới, Thế giới & Việt Nam |

## Thứ tự ưu tiên khi chọn nguồn để quét (áp dụng từ 10/07/2026)
Áp dụng theo thứ tự sau, không phải chọn ngẫu nhiên:

1. **Ưu tiên nguồn tiếng Anh** trước nguồn tiếng Việt. Nguồn Việt chỉ dùng bổ sung khi nguồn Anh không đủ tin, hoặc để lấy góc nhìn/tin trong nước.
2. **Trong nhóm đã chọn, ưu tiên nguồn có RSS feed** trước — quét qua RSS sẽ nhanh và chính xác hơn tìm kiếm/web scraping thủ công. Nếu nguồn không có RSS hoặc RSS không truy cập được, mới dùng WebSearch/WebFetch.
3. **Ưu tiên nguồn CHƯA từng được quét trước đó.** Trước khi quét, kiểm tra tần suất `sourceName` đã xuất hiện trong `DATA` (ví dụ bằng `grep -oE "\"sourceName\":\"[^\"]+\"" index.html | sort | uniq -c`) để biết nguồn nào đang bị bỏ sót, ưu tiên quét các nguồn đó trước khi quay lại các nguồn đã dùng nhiều.

## Quy trình mỗi lần quét (tối ưu token — QUAN TRỌNG)
`index.html` nặng ~170KB. **TUYỆT ĐỐI KHÔNG dùng tool Read để đọc toàn bộ `index.html`** — sẽ tốn rất nhiều token một cách không cần thiết. Thay vào đó:

1. Kiểm tra ngày cập nhật gần nhất bằng grep, không đọc cả file:
   `grep -oE '"generatedAt":"[^"]+"' index.html | head -1`
2. Kiểm tra tần suất nguồn đã dùng (để áp dụng ưu tiên #3 ở trên) bằng grep, không đọc cả file:
   `grep -oE '"sourceName":"[^"]+"' index.html | sort | uniq -c | sort -rn`
3. Áp dụng thứ tự ưu tiên nguồn ở trên. Ưu tiên đọc tin qua RSS (nhẹ, có cấu trúc) hơn WebFetch nguyên trang báo (nặng, nhiều nhiễu). Khi tóm tắt, dựa vào phần mô tả/summary có sẵn trong RSS thay vì fetch toàn bộ bài viết nếu đã đủ thông tin.
4. Quét tin mới trong 24h qua. Mục tiêu ~10–15 tin Thế giới + ~4–5 tin Mỹ (không cần cố đạt mức tối đa, ưu tiên chất lượng và tiết kiệm số lượt gọi tool).
5. Viết `title`/`summary` tiếng Việt (2–3 câu, súc tích), `significance` (1 câu). `sourceUrl` phải là link thật — không bịa link, tin không chắc link thì bỏ.
6. Gom TOÀN BỘ tin mới (world + us) thành một file JSON nhỏ, ví dụ ghi bằng heredoc vào `/tmp/new_items.json`, format:
   ```json
   {"date":"YYYY-MM-DD","worldNews":[{...}],"usNews":[{...}]}
   ```
7. Chèn vào `index.html` bằng script có sẵn, KHÔNG dùng Edit/Write trực tiếp lên `index.html`:
   `python3 scripts/add_news.py /tmp/new_items.json`
   Script tự động: chèn tin mới vào đầu mảng tương ứng, cập nhật `generatedAt`/`worldGeneratedAt`/`usGeneratedAt`, validate field bắt buộc và category hợp lệ, không đụng tới các phần khác của `DATA` (`analyses`, `xNews`, `exercises`, `dipEvents`, `terms`...). Nếu script báo lỗi, sửa lại `/tmp/new_items.json` rồi chạy lại — không tự sửa `index.html` bằng tay.
8. Commit theo mẫu: `Cap nhat ban tin DD/MM: +N tin (TG +x, My +y)`, push vào `main`.
9. Trong tóm tắt trả lời cuối cùng, chỉ cần ngắn gọn (số tin, nguồn, trạng thái push) — không cần liệt kê lại toàn bộ nội dung từng tin đã viết (nội dung đã nằm trong commit).

## Đánh giá lại chiến lược quét
**Vào hoặc sau ngày 17/07/2026** (1 tuần kể từ khi áp dụng quy tắc này), xem lại:
- Nguồn nào có RSS ổn định, tin chất lượng, đúng chủ đề → giữ ưu tiên cao.
- Nguồn nào khó truy cập, tin trùng lặp/nhiễu, hoặc RSS không hoạt động → hạ ưu tiên hoặc loại bỏ.
- Cập nhật lại danh sách và thứ tự ưu tiên trong file này cho phù hợp.

## Ghi chú vận hành
- Routine tự động **đã tạo thành công** (10/07/2026), chạy mỗi ngày 20:00 giờ VN (`0 13 * * *` UTC), tạo session mới mỗi lần chạy, tự đọc file này để lấy quy tắc.
- Mỗi lần Routine chạy tốn token cho: đọc `CLAUDE.md` (nhỏ), vài lệnh grep (nhỏ), WebSearch/WebFetch/RSS cho từng nguồn (khoản lớn nhất, tỷ lệ thuận với số nguồn quét), và output tóm tắt cuối. KHÔNG đọc `index.html` (172KB) — dùng `scripts/add_news.py` để tránh tốn token không cần thiết. Nếu vẫn cần tối ưu thêm, giảm số nguồn/tin mỗi lần quét ở bước 4 của quy trình.
