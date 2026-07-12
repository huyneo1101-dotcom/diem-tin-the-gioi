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

## Cách áp dụng khi quét (đọc ở Bước 1 của skill)
- **Điểm dương cao** (nhiều 👍) → **tăng** chỉ tiêu/độ ưu tiên cho chuyên mục/khu vực/nguồn đó (trong giới hạn chỉ tiêu tối thiểu mỗi category vẫn giữ nguyên — không bỏ hẳn mục nào).
- **Điểm âm** (nhiều 👎) → **giảm** ưu tiên, tránh nguồn/kiểu tin đó khi có lựa chọn tương đương; KHÔNG loại bỏ hoàn toàn một category (vẫn giữ tối thiểu 2 tin/category theo CLAUDE.md).
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
