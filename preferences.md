# Sở thích người đọc — điều hướng quét tin

File này là **cầu nối phản hồi**: người đọc bấm 👍 / 👎 trên từng tin, dữ liệu đồng bộ lên Supabase (KHÔNG hiển thị phân tích/sở thích gì trên giao diện — theo yêu cầu người dùng, mọi phân tích chỉ để quy trình quét tự dùng). Mỗi lần quét, skill `quet-tin` **đọc tổng hợp sở thích** rồi ưu tiên/giảm ưu tiên chuyên mục · khu vực · nguồn cho hợp gu người đọc.

## Lấy sở thích ở đâu — đọc `preferences.json` (tự động, đường DUY NHẤT)
File `preferences.json` ở gốc repo, do **GitHub Action `sync-preferences.yml`** cập nhật hằng ngày (18:00 VN): Action chạy trên máy GitHub, curl view `vote_stats` từ Supabase rồi commit vào `main`. Session quét chỉ cần **đọc file local** — luôn truy cập được, không phụ thuộc mạng ngoài. Cấu trúc:
```json
{"generatedAt":"...","source":"...","stats":[{"scope":"category|region|source","key":"...","up":N,"down":N,"net":N,"total":N}]}
```
Dùng `net` (👍−👎) làm điểm. Nếu `stats` rỗng → chưa ai vote, quét bình thường.

> **Vì sao cần GitHub Action:** lớp biên (Cloudflare) của `*.supabase.co` **chặn 403 mọi request từ môi trường quét/WebFetch** (kiểm chứng 12/07/2026 — kể cả endpoint health công khai), nhưng KHÔNG chặn máy GitHub Action và trình duyệt thật. Nên: trình duyệt người đọc ghi vote → Supabase; GitHub Action đọc Supabase → `preferences.json`; session quét đọc `preferences.json` (local). Vote cá nhân lưu riêng theo user (RLS), chỉ **bản tổng hợp** `vote_stats` công khai — không lộ ai vote gì. Schema: `docs/supabase-setup.sql`.

## Dữ liệu thô còn lưu ở đâu (cho phân tích sâu hơn về sau)
Bảng `votes` trên Supabase lưu MỖI vote kèm `title · category · region · source · v` (RLS theo user). `preferences.json` hiện chỉ mang tổng hợp category/region/source. Nếu về sau muốn phân tích sâu hơn (từ khóa/chủ đề từ tiêu đề, loại nội dung…), làm ở phía server/Action từ bảng `votes` này — KHÔNG cần thêm gì ở giao diện (giao diện chỉ thu vote, không phân tích).

## Cách áp dụng khi quét (đọc ở Bước 1 của skill)
- **Điểm dương** chuyên mục/khu vực/nguồn → **tăng** ưu tiên; **điểm âm** → **giảm** (vẫn giữ tối thiểu 2 tin/category, không bỏ hẳn mục nào).
- Đây là **định hướng mềm**, không ghi đè quy tắc chất lượng/nguồn 3 tầng trong CLAUDE.md.

## PHÁT HIỆN sở thích (cập nhật 12/07/2026 — từ 23 lượt vote, đã BỎ QUA ngày tháng)
Nguồn: `preferences.json` (Action kéo từ Supabase `vote_stats`). Điểm = 👍 − 👎.

### 🟢 Nội dung THÍCH — điểm chung
- **Chủ đề:** **Công nghệ quân sự** (7/7 thích, +7) và **Ngoại giao** (3/3 thích, +3) — thích gần như tuyệt đối.
- **Nguồn:** nghiêng mạnh về 2 nhóm — (a) **nguồn CHÍNH THỨC/chính phủ** (Bộ Ngoại giao Mỹ +2, Bộ Quốc phòng Anh, Hội đồng châu Âu, Bộ Ngoại giao Nhật, Văn phòng Thủ tướng Ấn Độ, Federal Reserve); (b) **báo QUỐC PHÒNG chuyên ngành** (Defense News +2, Naval News, Breaking Defense, SpaceNews, Task & Purpose). KHÔNG có nguồn tổng hợp đại chúng nào lọt nhóm thích.
- **Khu vực:** Châu Âu/NATO (+2), Trung Đông (+1), Châu Mỹ, Châu Phi (+1).
- **→ ĐIỂM CHUNG:** tin **quốc phòng/an ninh + ngoại giao cấp nhà nước**, ưu tiên **nguồn gốc chính thức & báo quốc phòng chuyên ngành**. Thích tin "sự kiện/chính sách cứng" hơn bình luận.

### 🔴 Nội dung KHÔNG THÍCH — điểm chung
- **Chủ đề:** **Chính trị** (5/6 không thích, −4) — mục bị ghét rõ nhất.
- **Nguồn:** **Al Jazeera** nổi bật nhất (4/5 không thích, −3), rồi CNBC (−1), Axios (−1), The Moscow Times (−1) — đều là **báo tổng hợp/đại chúng**.
- **Khu vực:** Đông Á (−1), Nam Á (−1), Nga–Ukraine (−1) hơi âm.
- **→ ĐIỂM CHUNG:** tin **chính trị chung chung** + **nguồn tổng hợp/bình luận đại chúng** (đặc biệt Al Jazeera); có xu hướng né tin **chiến sự Nga–Ukraine** lặp lại.
- *Trung tính:* Kinh tế (2/2, net 0).

### 🎯 Điều hướng quét (mềm — không ghi đè quy tắc 3 tầng)
- **Tăng:** Công nghệ quân sự, Ngoại giao; ưu tiên nguồn chính thức + báo quốc phòng chuyên ngành; khu vực Âu/NATO, Trung Đông.
- **Giảm:** tin "Chính trị" thuần; nguồn Al Jazeera / CNBC / Axios; hạn chế tin Nga–Ukraine trùng lặp.
- Vẫn giữ tối thiểu 2 tin/category, không bỏ hẳn mục nào.

> ⚠️ Đây mới là mức **chuyên mục/khu vực/nguồn**. Phân tích **tiêu đề/chủ đề chi tiết** (điểm chung ở mức từ khóa cụ thể như nước nào, vũ khí nào) cần view `vote_items` — xem `docs/supabase-setup.sql`; sau khi tạo view + Action chạy, `preferences.json` sẽ có mảng `items` (tiêu đề) để phân tích sâu hơn.

## Nhật ký cập nhật
- **12/07/2026:** phân tích lần đầu từ 23 vote (15👍/8👎) ở mức chuyên mục/khu vực/nguồn — thấy rõ thích Quốc phòng+Ngoại giao & nguồn chính thức/quốc phòng; ghét Chính trị chung & nguồn đại chúng (Al Jazeera).
