# Sở thích người đọc — điều hướng quét tin

File này là **cầu nối phản hồi**: người đọc bấm 👍 / 👎 trên từng tin, dữ liệu đồng bộ lên Supabase (KHÔNG hiển thị phân tích/sở thích gì trên giao diện — theo yêu cầu người dùng, mọi phân tích chỉ để quy trình quét tự dùng). Mỗi lần quét, skill `quet-tin` **đọc tổng hợp sở thích** rồi ưu tiên/giảm ưu tiên chuyên mục · khu vực · nguồn cho hợp gu người đọc.

> **Định hướng = TỔNG HỢP vote của MỌI tài khoản người đọc** (view `vote_stats`/`vote_items` gộp tất cả user, không tách riêng). Vote của **người đọc thật là định hướng CHÍNH** cho việc quét; các vote ban đầu của chủ trang chỉ là **hạt giống mồi** khi chưa có ai vote. Người đọc vote càng nhiều thì hồ sơ càng nghiêng theo họ. (Khi lượng vote người đọc đủ lớn, có thể cân nhắc giảm trọng số / loại các vote mồi `item_id` bắt đầu bằng `calib:` để readers chi phối hoàn toàn — chưa cần làm bây giờ.)

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

## PHÁT HIỆN sở thích (cập nhật 13/07/2026 — từ 121 lượt vote, độ tin cậy CAO, đã BỎ QUA ngày tháng)
Nguồn: `preferences.json` (`stats` + `items`). 101 👍 / 23 👎 (124 tiêu đề). Gồm 23 tin thật + 100 tin mẫu cân bằng + vote cứu tin ở mục Bị loại → đủ để tách rõ trục sở thích.

### 🟢 THÍCH — điểm chung
- **Trục chủ đề rõ nhất:** **Công nghệ quân sự (32👍/0👎)** và **Ngoại giao (31👍/0👎)** — thích TUYỆT ĐỐI, không một tin nào bị ghét. **Kinh tế vĩ mô (22👍/3👎)** cũng thích mạnh.
- **Nội dung thích:** khí tài/hệ thống QP cụ thể (tên lửa, phòng không, hải quân, không gian/Space Force, laser, AI quân sự, tàu ngầm); **hiệp định/khuôn khổ an ninh–quốc phòng** (ACSA, RAA, đối tác chiến lược, tuyên bố chung có kết quả); **chính sách vĩ mô & định chế** (Fed/ECB/BOJ, IMF/OECD/WTO/BIS/World Bank, nợ công, thuế toàn cầu, chuỗi cung ứng chip).
- **Chính trị được thích CÓ CHỌN LỌC (14👍/19👎, net −5):** chỉ loại **thể chế/luật/trừng phạt/chiến lược** — cải cách Thượng viện Anh, EU AI Act, ngân sách quốc phòng, cải tổ nội các, **dự luật/lệnh trừng phạt Nga & Iran**, sửa hiến pháp phòng vệ (Nhật). Các vote mới đều là tin trừng phạt/thể chế → càng khẳng định lằn ranh này.
- **Nguồn:** báo quốc phòng chuyên ngành (Defense News, Naval News, Breaking Defense, SpaceNews, Task & Purpose) + nguồn chính thức (Bộ NG Mỹ/Nhật, Bộ QP Anh, Hội đồng châu Âu, Fed) = **luôn tích cực**. Wire (Reuters/AFP) trung tính, thích/ghét tùy nội dung.
- **Khu vực KHÔNG phải trục ưu tiên mạnh** — tin thích trải đều Âu/NATO, Châu Mỹ, Ấn Độ Dương-TBD, Đông Á, Toàn cầu. Trục quyết định là **CHỦ ĐỀ + KIỂU TIN**, không phải khu vực.

### 🔴 KHÔNG THÍCH — điểm chung (23👎, trong đó 19 là Chính trị)
- **Cáo phó / cái chết cá nhân** (≈5): TNS Graham, cựu Quốc vương Qatar, TNS California, cựu quan chức hoàng gia Vịnh... → **né gần như tuyệt đối tin người qua đời**.
- **Chính trị NHÂN VẬT / drama / bê bối cá nhân**: cựu thủ tướng lưu vong trở về, bắt lãnh đạo đối lập, dán nhãn 'điệp viên', triệu tập phóng viên, kết án tham nhũng, thống đốc không tái tranh cử, thủ lĩnh từ chức.
- **Đua bầu cử / horserace** (thắng–thua đảng phái): bầu cử địa phương Đài Loan, Nam Phi mất đa số.
- **Chính trị DOMESTIC xã hội/tư pháp** (kể cả mang tính thể chế): cải cách công tố Hàn, luật nhập cư Canada, Tòa Tối cao Mỹ giới hạn cơ quan liên bang → **ghét dù là "thể chế"**, vì thuộc nội bộ/hành chính, không mang màu an ninh–chiến lược.
- **Lợi nhuận DOANH NGHIỆP đơn lẻ** (3/3 dislike Kinh tế): UBS lãi quý, Delta lãi kỷ lục, VW giảm công suất → **ghét tin lãi/lỗ/vận hành từng công ty**.
- **Nga–Ukraine chiến sự lặp lại** (Zelensky/Patriot).

### 🔑 QUY TẮC LỌC (rút ra, độ tin cậy cao — dùng khi quét)
1. **Thể chế/luật/chiến lược > cá nhân/drama/cáo phó.** Ghét mạnh nhất: cáo phó, nhân vật chính trị, đua bầu cử.
2. **Vĩ mô/chính sách/hệ thống > lợi nhuận công ty đơn lẻ.** (Kinh tế: 3/3 tin bị ghét đều là earnings công ty.)
3. **"Cứu" được nhờ gắn chủ đề chiến lược:** tin công ty/chính trị vẫn được thích NẾU gắn quốc phòng / chip–AI / chuỗi cung ứng / địa chính trị (vd Boeing=máy bay quân sự, Samsung=chip AI, VW=khủng hoảng ngành). Cùng chủ thể, khung "chiến lược/ngành" được thích, khung "chỉ số vận hành" bị ghét.
4. **An ninh–đối ngoại–great power > nội bộ xã hội/tư pháp.** Chính trị domestic (nhập cư, tư pháp, công tố) leans ghét.
5. **Khu vực trung lập** — không thiên vị vùng; ưu tiên theo chủ đề/kiểu tin.

### 🎯 Điều hướng quét (mềm — không ghi đè quy tắc nguồn 3 tầng)
- **Tăng mạnh:** Công nghệ quân sự (khí tài/hệ thống cụ thể, không gian, tên lửa/phòng không, hải quân, AI quân sự); Ngoại giao (hiệp định/khuôn khổ an ninh có kết quả); Kinh tế vĩ mô/chính sách/chuỗi cung ứng chiến lược.
- **Trong Chính trị:** ưu tiên tin **luật/hiến pháp/ngân sách QP/trừng phạt/chiến lược great-power**; **né** cáo phó, nhân vật/bê bối, đua bầu cử, nội bộ xã hội-tư pháp.
- **Trong Kinh tế:** ưu tiên vĩ mô/định chế; **né** tin lãi–lỗ công ty đơn lẻ trừ khi gắn chủ đề chiến lược.
- **Né:** cáo phó nói chung; Nga–Ukraine chiến sự lặp lại. Nguồn Al Jazeera lệch tiêu cực (phần lớn do gắn tin chính trị/nhân vật).
- Vẫn giữ tối thiểu 2 tin/category, không bỏ hẳn mục nào.

## Nhật ký cập nhật
- **12/07/2026 (a):** phân tích lần đầu từ 23 vote (15👍/8👎) — thích Quốc phòng+Ngoại giao, ghét Chính trị chung; rút quy tắc cấu trúc>cá nhân, vĩ mô>vi mô.
- **12/07/2026 (b):** phân tích lại từ **117 vote** (94👍/23👎, thêm 100 tin mẫu cân bằng). Xác nhận & làm SẮC: QP+Ngoại giao thích tuyệt đối; ghét = cáo phó + chính trị nhân vật + đua bầu cử + lợi nhuận công ty đơn lẻ. Bổ sung quy tắc: (3) tin "cứu" được nhờ gắn chủ đề chiến lược; (4) an ninh–đối ngoại > nội bộ xã hội/tư pháp; (5) khu vực không phải trục ưu tiên.
- **13/07/2026 (routine tự động):** **121 vote** (101👍/23👎). +7 vote 👍 (từ việc chủ trang cứu tin ở mục Bị loại) — **không đảo gu**, chỉ CỦNG CỐ: Ngoại giao 27→31👍 (vẫn 0👎), CNQS 31→32, Chính trị 12→14👍 (2 tin mới đều là **trừng phạt Nga/Iran** = thể chế). 5 quy tắc lọc giữ nguyên. Vote vẫn 100% của chủ trang, chưa có người đọc khác.
