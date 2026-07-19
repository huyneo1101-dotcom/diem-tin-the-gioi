# Hiến chương biên tập "Điểm Tin Thế Giới" (hồ sơ KHAI BÁO chủ động)

> **Nguồn gốc:** hồ sơ sở thích tin do chủ trang **khai báo chủ động qua 11 vòng hỏi-đáp** (app "Điểm Tin news preference detection"), chốt và lưu lại làm memory. Đây là bản KHAI BÁO — khác với `preferences.md` là bản SUY TỪ HÀNH VI vote 👍/👎.

## Vai trò & thứ tự ưu tiên (đọc kỹ — để KHÔNG conflict khi quét)
Ba hồ sơ quy tắc trong repo, phân lớp rõ:
1. **Lớp 1 — Hiến chương (file này):** quyết định **CẤU TRÚC · TRIẾT LÝ · CÁCH VIẾT**. Ổn định, ít đổi.
2. **Lớp 2 — Tín hiệu hành vi (`preferences.md` / `preferences.json`, từ vote):** **tinh chỉnh MỨC ưu tiên chủ đề/khu vực/nguồn TRONG khuôn khổ Lớp 1**. Cập nhật hằng ngày.
3. **Lớp 3 — Vận hành (`CLAUDE.md` / `SKILL.md`):** nguồn 3 tầng, guardrail, quy trình chạy.

**QUY TẮC THẮNG–THUA khi mâu thuẫn:**
- Mâu thuẫn về *cấu trúc / triết lý / cách viết* → **Lớp 1 (hiến chương) thắng**.
- Mâu thuẫn về *mức ưu tiên chủ đề trong khuôn khổ* → **Lớp 2 (vote) điều chỉnh** (vì vote là định hướng chính cho mức độ).
- Không lớp nào ghi đè **quy tắc nguồn 3 tầng / chất lượng** ở Lớp 3.

## Hồ sơ (chốt sau 11 vòng)

### Chọn tin
- Phân bổ chủ đề / khu vực / xung đột–hợp tác **đều để tự nhiên theo tin thật** (không ép tỷ lệ).
- **Ít tin hơn / chọn lọc hơn** (chất > lượng).
- **Ưu tiên nước lớn**, không kéo vùng xa.
- Bớt phát biểu suông + tin đồn.
- **VN chỉ khi gắn quốc tế.**
- **TQ để tự nhiên** (không đậm thêm, không né thêm).

### Theo mảng
- **CNQS:** không quân / tên lửa, hạt nhân / răn đe, không gian / mạng. **(hải quân là mảng PHỤ)**
- **Kinh tế:** cả 4 góc — năng lượng, thương chiến, ngân hàng trung ương, châu Á / VN.
- **Phi nhà nước + KHCN dân sự:** chỉ khi có tầm chiến lược.
- **Tài nguyên / khí hậu:** chỉ khi gắn cạnh tranh nước lớn.

### Viết tin
- Khô gọn, giọng báo chí **trung tính**.
- **Số liệu cụ thể.**
- Tin nhạy cảm **đưa đầy đủ, không né**.
- Bối cảnh chỉ thêm khi rắc rối.
- **Thuật ngữ tiếng Anh để trong ngoặc.**
- Tên riêng tuỳ độ phổ biến.
- **Giữ giờ gốc sự kiện.**

### Phân tích
- Là **tóm tắt bài ngoài** (trung lập = chọn nguồn cân bằng, **gồm học giả TQ / Nga phi nhà nước**).
- **Muốn NHIỀU phân tích hơn** (ngược với tin thường).
- Tóm tắt ngắn + takeaway.
- **Không tự dự báo.**

### Cấu trúc
- **Lõi = Thế giới / Mỹ** (ngang nhau, giữ theo chủ đề).
- **4 hồ sơ sống** (theo dõi liên tục): Nga–Ukraine · Trung Đông · Đài Loan / Biển Đông · Mỹ–Trung.
- Lớp kiến thức mở rộng.
- Cuối tuần **bù bằng phân tích**.
- **Bỏ ảnh.**

### Việc CODE sau (trạng thái)
- ✅ **Tab VN & Biển Đông** (chủ quyền biển + kinh tế VN quốc tế) — tab `🇻🇳 VN·Biển Đông`, lọc tự động Thế giới+Mỹ+X theo từ khoá VN/Biển Đông.
- ✅ **Tin nổi bật lên đầu** — dải "⭐ Nổi bật" (Công nghệ quân sự & Ngoại giao có `significance`) ở đầu tab Bài mới.
- ✅ **Nhãn độ tin cậy theo từng tin** — badge 🏛️ Chính thức / 📊 Dữ liệu / 🧠 Phân tích / 📡 Hãng tin / 📰 Báo chí, suy từ `sourceName` theo mô hình nguồn 3 tầng.
- ✅ **Mục theo dõi 4 hồ sơ sống** — segment "🧵 Hồ sơ" (trong tab Chuyên đề) đổi thành 4 hồ sơ: Nga–Ukraine · Trung Đông · Đài Loan/Biển Đông · Mỹ–Trung (gom tin+X theo từ khoá).
- ⏳ **Siết cap tin thường + nới cap phân tích** — UI đã sẵn (tab 🧠 Phân tích không giới hạn; tab Bài mới cap 40). Phần còn lại là **việc QUÉT** (agent sản xuất thêm mục `analyses`) — điều chỉnh ở quy tắc quét, không phải code UI.
- ⏳ **Cập nhật 12h trưa** — cần thêm 1 Routine quét lúc 12:00 VN (tốn token hằng ngày) → chờ chủ trang quyết định bật hay không.

## Hoà giải với hồ sơ VOTE (`preferences.md`) — 5 điểm từng lệch
| # | Điểm lệch | Chốt (áp dụng khi quét) |
|---|---|---|
| 1 | **Hải quân**: vote thích ngang, khai báo xếp phụ | Vẫn NHẬN tin hải quân; nhưng khi phải cắt bớt CNQS, **ưu tiên không quân/tên lửa/không gian/mạng trước, hải quân sau**. |
| 2 | **Khu vực**: vote trung lập, khai báo ưu tiên nước lớn | Chủ đề là trục chính; khi 2 tin ngang chất → **ưu tiên tin dính nước lớn**, HẠ (không loại) vùng xa. |
| 3 | **Nga–Ukraine**: vote loại tin lặp, khai báo là hồ sơ sống | **Theo dõi hồ sơ sống** (bước ngoặt / ngoại giao / vũ khí mới) NHƯNG **loại tin chiến sự lặp** (đường tiền tuyến hằng ngày). |
| 4 | **Số lượng vs phân tích** | **Dung hoà (hiện trạng):** giữ quota ~10–20 tin/ngày, **không sàn cứng mỗi category**, ưu tiên chất. Lớp phân tích chuyên sâu = việc CODE sau (chưa làm). |
| 5 | **VN & Biển Đông** chưa được nhấn | Ưu tiên tin **chủ quyền biển + kinh tế VN quốc tế** (theo tinh thần "VN chỉ khi gắn quốc tế"). Tab riêng = việc CODE sau. |
