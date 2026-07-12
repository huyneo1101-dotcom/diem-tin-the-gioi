# Sở thích người đọc — điều hướng quét tin

File này là **cầu nối phản hồi**: người đọc bấm 👍 / 👎 trên từng tin (lưu ở `localStorage dt.votes`, mục **⭐ Đã lưu → 📊 Sở thích**), rồi bấm **"Xuất hồ sơ sở thích (JSON)"** → gửi file `diemtin-sothich.json` cho agent. Agent cập nhật các trọng số dưới đây. Mỗi lần quét, quy trình (skill `quet-tin`) **đọc file này** để ưu tiên/giảm ưu tiên chuyên mục · khu vực · nguồn cho hợp gu người đọc.

> Votes nằm trên trình duyệt người đọc — session quét (server) KHÔNG đọc được localStorage. Đường duy nhất đưa phản hồi vào là: (a) export JSON rồi cập nhật file này, hoặc (b) sau này đồng bộ qua Supabase. Hiện dùng (a).

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
