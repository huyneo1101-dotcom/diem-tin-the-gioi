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

## Quy trình mỗi lần quét
1. Đọc `DATA.generatedAt` hiện tại để tránh trùng tin cũ.
2. Áp dụng thứ tự ưu tiên nguồn ở trên.
3. Quét tin mới trong 24h qua. Mục tiêu ~10–20 tin Thế giới + ~5 tin Mỹ (linh hoạt).
4. Viết `title`/`summary` tiếng Việt (2–3 câu), `significance` (1 câu ý nghĩa/tác động). `sourceUrl` phải là link thật — không bịa link, tin không chắc link thì bỏ.
5. Chèn tin mới vào đầu mảng tương ứng (mới nhất lên trên), giữ nguyên tin cũ.
6. Cập nhật 3 field `generatedAt`.
7. Kiểm tra JSON trong `DATA` không vỡ cú pháp.
8. Commit theo mẫu: `Cap nhat ban tin DD/MM: +N tin (TG +x, My +y)`, push vào `main`.

## Đánh giá lại chiến lược quét
**Vào hoặc sau ngày 17/07/2026** (1 tuần kể từ khi áp dụng quy tắc này), xem lại:
- Nguồn nào có RSS ổn định, tin chất lượng, đúng chủ đề → giữ ưu tiên cao.
- Nguồn nào khó truy cập, tin trùng lặp/nhiễu, hoặc RSS không hoạt động → hạ ưu tiên hoặc loại bỏ.
- Cập nhật lại danh sách và thứ tự ưu tiên trong file này cho phù hợp.

## Ghi chú vận hành
- Routine tự động (lịch quét hằng ngày 20:00 giờ VN) **chưa tạo được** do lỗi phê duyệt MCP (`create_trigger` bị chặn, không rõ nguyên nhân — cần thử lại sau, có thể qua claude.ai/code trên web). Hiện tại quét tin được thực hiện thủ công khi người dùng yêu cầu.
