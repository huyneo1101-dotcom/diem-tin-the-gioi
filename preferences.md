# Sở thích người đọc — điều hướng quét tin

File này là **cầu nối phản hồi**: người đọc bấm 👍 / 👎 trên từng tin (mục **⭐ Đã lưu → 📊 Sở thích**), dữ liệu đồng bộ lên Supabase. Mỗi lần quét, quy trình (skill `quet-tin`) **đọc tổng hợp sở thích** rồi ưu tiên/giảm ưu tiên chuyên mục · khu vực · nguồn cho hợp gu người đọc, và cập nhật bảng trọng số dưới đây.

## Lấy sở thích ở đâu (tự động, ưu tiên `preferences.json`)
**A. Tự động — đọc `preferences.json` (ĐƯỜNG CHÍNH):** file này ở gốc repo, được **GitHub Action `sync-preferences.yml`** cập nhật hằng ngày (18:00 VN): Action chạy trên máy GitHub, curl view `vote_stats` từ Supabase rồi commit vào `main`. Session quét chỉ cần **đọc file local** — luôn truy cập được, không phụ thuộc mạng ngoài. Cấu trúc:
```json
{"generatedAt":"...","source":"...","stats":[{"scope":"category|region|source","key":"...","up":N,"down":N,"net":N,"total":N}]}
```
Dùng `net` (👍−👎) làm điểm. Nếu `stats` rỗng → chưa ai vote, quét bình thường.

**B. Thủ công — export JSON (khi cần chỉnh tay):** người đọc bấm **"📤 Xuất hồ sơ sở thích (JSON)"** (tab ⭐ Đã lưu → 📊 Sở thích) → gửi file `diemtin-sothich.json` cho agent → agent cập nhật bảng trọng số dưới đây.

> **Vì sao cần GitHub Action:** lớp biên (Cloudflare) của `*.supabase.co` **chặn 403 mọi request từ môi trường quét/WebFetch** (kiểm chứng 12/07/2026 — kể cả endpoint health công khai), nhưng KHÔNG chặn máy GitHub Action và trình duyệt thật. Nên: trình duyệt người đọc ghi vote → Supabase; GitHub Action đọc Supabase → `preferences.json`; session quét đọc `preferences.json` (local). Vote cá nhân lưu riêng theo user (RLS), chỉ **bản tổng hợp** `vote_stats` công khai — không lộ ai vote gì. Schema: `docs/supabase-setup.sql`.

## Các tiêu chí đánh giá mối quan tâm
Hồ sơ sở thích (file export `diemtin-sothich.json`) suy từ **nhiều tín hiệu**, có trọng số: 👍 +2 · 👎 −2 · lưu ★ +3 · đã đọc +1. Gồm các chiều:
- **`byCategory` / `byRegion` / `bySource`** — điểm 👍/👎 theo chuyên mục · khu vực · nguồn (chiều này cũng có ở view Supabase tự động).
- **`keywords`** — chủ đề/từ khóa (danh từ riêng) rút từ tiêu đề tin đã vote/lưu, kèm điểm tổng hợp. Đây là chiều **mịn nhất, giá trị nhất** để bám đúng chủ đề (vd "Iran", "NATO", "Biển Đông", "bán dẫn", "F-16").
- **`byXhandle`** — sở thích theo từng tài khoản X (@NATO, @Reuters…).
- **`implicit`** — tín hiệu ngầm: số bài đã lưu ★ / đã đọc, phân theo chuyên mục (quan tâm dù không vote).
- **`engagementRate`** — tỷ lệ tương tác chuẩn hóa: trong số tin đã XEM (dt.seen) theo chuyên mục/nguồn, bao nhiêu % được thích/lưu (`eng/seen`). Phân biệt "thấy nhiều nhưng chán" vs "thấy ít nhưng mê" — chính xác hơn đếm thô.
- **`criteria`** — bộ tiêu chí suy diễn: `kindPref` (loại nội dung thích: tin/X/phân tích/tập trận/ngoại giao), `avgAgeDays` (độ mới TB tin quan tâm), `lang` (nguồn Việt vs Anh), `opinion` (tỷ lệ tin bình luận/quan điểm), `avoidTopics` (chủ đề điểm âm nên tránh), `cooccur` (cặp chủ đề hay đi cùng), `concepts` (khái niệm đang theo dõi).
> Lưu ý: mọi chiều trừ category/region/source chỉ có qua **export thủ công** (localStorage, không đồng bộ Supabase). View Supabase tự động (`preferences.json`) chỉ có category/region/source.

## Cách áp dụng khi quét (đọc ở Bước 1 của skill)
- **Chủ đề/từ khóa điểm cao** → chủ động tìm thêm tin về đúng chủ đề đó; **điểm âm** → giảm.
- **Điểm dương** chuyên mục/khu vực/nguồn → **tăng** ưu tiên; **điểm âm** → **giảm** (vẫn giữ tối thiểu 2 tin/category, không bỏ hẳn mục nào).
- Đây là **định hướng mềm**, không ghi đè quy tắc chất lượng/nguồn 3 tầng trong CLAUDE.md.

## Trọng số hiện tại
*(Chưa có dữ liệu — cập nhật sau lần export đầu tiên. Điểm = số 👍 trừ số 👎.)*

### Theo chuyên mục
| Chuyên mục | Điểm | Ghi chú |
|---|---|---|
| Kinh tế | 0 | |
| Chính trị | 0 | |
| Công nghệ quân sự | 0 | |
| Ngoại giao | 0 | |

### Theo khu vực
| Khu vực | Điểm | Ghi chú |
|---|---|---|
| *(chưa có)* | | |

### Theo nguồn
| Nguồn | Điểm | Ghi chú |
|---|---|---|
| *(chưa có)* | | |

## Nhật ký cập nhật
- (chưa có lần cập nhật nào)
