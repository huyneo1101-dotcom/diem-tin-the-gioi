# Sở thích người đọc — điều hướng quét tin

File này là **cầu nối phản hồi**: người đọc bấm 👍 / 👎 trên từng tin (mục **⭐ Đã lưu → 📊 Sở thích**), dữ liệu đồng bộ lên Supabase. Mỗi lần quét, quy trình (skill `quet-tin`) **đọc tổng hợp sở thích** rồi ưu tiên/giảm ưu tiên chuyên mục · khu vực · nguồn cho hợp gu người đọc, và cập nhật bảng trọng số dưới đây.

## Lấy sở thích ở đâu (2 đường)
**A. Thử tự động — Supabase view `vote_stats` (best-effort, KHÔNG đảm bảo):** session quét WebFetch view tổng hợp công khai (chỉ số đếm, không lộ danh tính):
```
https://ltmlueqkajqmduoqghdf.supabase.co/rest/v1/vote_stats?select=*&apikey=sb_publishable_74Lm6cc0CkoOOzy3A4IRrQ_BX0jHQcg
```
Trả JSON `{scope: category|region|source, key, up, down, net, total}`; dùng `net` (👍−👎) làm điểm.
> ⚠️ **Đã kiểm chứng 12/07/2026:** lớp biên (Cloudflare) của `*.supabase.co` **chặn 403 mọi request từ WebFetch/máy chủ** (kể cả endpoint health công khai), trong khi trình duyệt thật vẫn vào được. Nên đường A khi quét **thường thất bại** → thử 1 lần, lỗi thì bỏ, dùng đường B. (Trình duyệt người đọc ghi vote lên Supabase vẫn CHẠY bình thường — chỉ phía đọc bằng máy chủ mới bị chặn.)

**B. Thủ công — export JSON (ĐƯỜNG CHÍNH, đảm bảo):** người đọc bấm **"📤 Xuất hồ sơ sở thích (JSON)"** (tab ⭐ Đã lưu → 📊 Sở thích) → gửi file `diemtin-sothich.json` cho agent → agent cập nhật bảng trọng số dưới đây rồi commit. Đây là cầu nối đáng tin cậy vì không phụ thuộc lớp biên Supabase.

> Vote cá nhân lưu riêng theo user (RLS), chỉ **bản tổng hợp** `vote_stats` công khai. Không lộ ai đã vote gì. Schema: `docs/supabase-setup.sql`.

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
