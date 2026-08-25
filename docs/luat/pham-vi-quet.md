# Phạm vi quét, chủ đề và kiến trúc phiên quét — Điểm Tin Thế Giới

> Xẻ từ `CLAUDE.md` ngày 25/08/2026 để bản thi hành gọn lại (luật mục 31 của `~/.claude/CLAUDE.md`).
> **Nội dung giữ NGUYÊN VĂN, không cắt chữ nào** — chỉ đổi chỗ ở. Bản thi hành: [`../../CLAUDE.md`](../../CLAUDE.md).

## ⚠️ CẬP NHẬT PHẠM VI 2026-07-23 (chỉ thị Huy — GHI ĐÈ các mục "Chỉ tiêu số lượng", "Kiến trúc quét", "Chu kỳ bản tin" bên dưới)
Bản tin **2 phiên/ngày, CÙNG 5 chủ đề** (chỉ thị Huy 26/07/2026): **TỐI 20:47** và **SÁNG SỚM 03:47**
(đêm VN = ngày làm việc Mỹ nên nhiều tin mới; cả 2 phiên đều gửi email). Mốc CHÍNH chạy trên **GitHub
Actions** `claude-web-scan.yml` (giờ VN: tối **20:47** + vét 21:47, sáng sớm **03:47/04:47** — máy Mac tắt vẫn ra bản
tin); scheduled task local `web-scan` là DỰ PHÒNG cho **CẢ HAI** phiên (cron `30 4,5,21 * * *` giờ VN):
CI không quét thì ~30 phút sau local nhảy vào, CI đã xong/đang chạy thì local SKIP êm qua khoá `state.py`.

📅 **MỌI SỐ GIỜ TRONG FILE NÀY LÀ BẢN CHÉP LẠI — NGUỒN SỰ THẬT LÀ [`docs/LICH.md`](docs/LICH.md)**
(sinh từ chính dòng `cron:`). Lệch nhau thì `LICH.md` thắng. Canh bằng
`python3 scripts/kiem_lich.py --kiem`, dựng 30/07/2026 sau khi bắt được **47 chỗ** trong tài liệu còn
ghi lịch CI cũ (21:00 · 22:00 · 04:00 · 05:00) — cả 04 mốc đã dời sớm 13 phút mà không chỗ chép lại nào
được sửa. **Sửa cron thì chạy `--sinh` rồi soi lại các chỗ chép.**

**Đổi 27/07/2026 (chỉ thị Huy):** mốc CI sáng dời 04:30 → **04:00** và phiên sáng sớm **CÓ dự phòng local
04:30/05:30** — vì sáng 27/07 cron CI 04:30 không nổ (GitHub hay trễ/bỏ cron lúc tải cao) mà phiên sáng
khi đó không có lưới local nên suýt mất trắng bản tin. **Dời tiếp: cả 04 mốc CI sớm 13 phút** để
`harvest-ci.yml` (chạy trước 15') kịp xong trước phiên quét. Xen kẽ đầy đủ nay là: **CI 03:47 → local
04:30 → CI 04:47 → local 05:30**. Local chỉ chạy khi máy đã thức: cần lịch `pmset repeat wakeorpoweron … 04:25`.
**⏰ HẠN CHÓT EMAIL TỐI 22:00 (chỉ thị Huy 27/07/2026):** email bản tin tối phải tới hộp thư **muộn nhất
22:00**, nên phiên tối tính NGƯỢC từ mốc cuối chứ không phải mốc đầu — quét ~20' (đo thật 16–21') +
email ~20 giây ⇒ lớp cuối phải fire chậm nhất **21:15**, và lớp cuối phải là LOCAL vì cron GitHub trễ
5–20', còn task local đúng giờ hơn. Phiên tối vì thế là **2 lớp TRONG HẠN: CI 20:47 → local 21:15**,
cộng **1 lớp VÉT ngoài hạn: CI 21:47** (chỉ chạy khi cả hai lớp trên đều chết — GitHub bỏ cron *và* máy
Mac ngủ; email hôm đó ~22:10, quá hạn nhưng thà muộn còn hơn mất bản tin). **KHÔNG dời 2 lớp đầu trễ
hơn, KHÔNG biến lớp vét thành mốc chính.** Phiên chạy ở mốc 21:15 phải ưu tiên GỬI ĐÚNG GIỜ hơn là gom
đủ tin: quá 21:45 chưa xong thì chốt lô đang có, commit ngay, phần thiếu ghi `scan-gaps.json`.
**Vì sao 21:15 chứ không phải 21:30:** tối 26/07 mốc local 21:30 mãi **21:41** mới `claim` xong (jitter +
khởi động session + `git pull --rebase` timeout 2') — trễ 11' chứ không phải 3,5' như jitter danh nghĩa;
cộng 20' quét là email rơi ~22:02, VỠ hạn. 21:15 mua thêm 15' biên. Đây cũng là lý do phiên tối phải
tách thành scheduled task RIÊNG `web-scan-diem-tin-toi` (một task chỉ nhận một biểu thức cron, mà phiên
sáng đang ở phút 30).
**Phiên sáng 10:15 kiểu cũ vẫn BỎ.** Mỗi phiên **CHỈ quét 5 chủ đề, mỗi chủ đề 5–10
bài, khung 24 GIỜ gần nhất — nới 48h nếu chủ đề đó thiếu (<5 bài):**
⛔ **"Nới 48h" = HÔM NAY + HÔM QUA, không phải lùi 2 ngày lịch** (chỉ thị Huy 27/07/2026: *"quét tin ngày
26 thì chỉ được lấy tin tối đa là ngày 25, không được phép lấy tin ngày 24"*). Tin cũ hơn thì BỎ, ghi
`logs/loai-tin.md` + nêu lý do trong `scan-gaps.json`, thà chủ đề về 0. Đã cưỡng bức bằng `add_news.py`
(kiểm ngày 2 lớp — xem mục Guardrail), nên neo lùi `date` batch không lách được nữa.
1. **Nội bộ Mỹ — 5 NHÓM, HAI HẠNG ƯU TIÊN (chỉ thị Huy 27/07/2026, GHI ĐÈ mức "SIẾT" cũ).**
   **BẮT BUỘC tìm cho hết nhóm (1) trước; chỉ khi KHÔNG ĐỦ CHỈ TIÊU mới lấy sang các nhóm còn lại —
   và (2), (3), (4), (5) NGANG HÀNG NHAU, không có thứ tự giữa chúng.**
   | Hạng | # | Nhóm | Gồm |
   |---|---|---|---|
   | **1** | **1** | **Điều trần + bỏ phiếu** | TOÀN BỘ phiên điều trần trong ngày + TOÀN BỘ kết quả hội đồng/uỷ ban/hai viện bỏ phiếu thông qua dự luật |
   | 2 | 2 | Sáng kiến & chiến lược chính quyền | Trump government initiative + strategy công bố trên **kênh chính thống của các bộ** (sắc lệnh, memorandum, chiến lược quốc gia, fact sheet, thông cáo bộ) |
   | 2 | 3 | Biểu tình | Diễn biến biểu tình, tuần hành, đình công |
   | 2 | 4 | Kinh tế Mỹ + động thái bộ sậu | Hoạt động kinh tế Mỹ (Fed, thuế quan, trừng phạt, số liệu) + hoạt động khác của các bộ và Nhà Trắng (Trump + nội các) |
   | 2 | **5** | **Bầu cử** *(tách riêng 27/07/2026 theo chỉ thị Huy — trước gộp chung nhóm 3)* | Bầu cử giữa nhiệm kỳ, bầu cử sơ bộ, tranh cử/vận động, thăm dò, quy định cử tri, kiểm phiếu, phân định lại khu vực bầu cử (redistricting/gerrymander), đua ghế Thượng viện/Hạ viện/thống đốc |

   → `usNews`, cat `Chính trị` (nhóm 4 có thể là `Kinh tế` nếu đúng nội dung). Nhóm 3, 4, 5 **đảo lại**
   phần cấm cũ (drama/đảng phái/horserace/biểu tình) — nay được nhận, nhưng CHỈ khi nhóm 1 đã cạn.
   ⚠️ **Số nhóm 2→5 chỉ là NHÃN phân loại, KHÔNG phải thứ tự** — `harvest.py` xếp bằng `us_rank()`
   chứ không bằng số nhóm; xếp theo số sẽ dìm bầu cử xuống cuối, trái chỉ thị "ngang bằng".
   ⚠️ Từ khoá nhóm 3–4 rất chung (protest, tariff, inflation) nên **phải neo vào ngữ cảnh Mỹ**: đã cưỡng
   bức bằng `WEAK_NEED_US` trong `scripts/topics.py` (thực tế lọt: nghị sĩ Philippines mặc đồ đen phản
   đối, chính sách tiền tệ Singapore, chi tiêu vốn Nhật Bản).
2. **Úc & Biển Đông** — AUKUS/QP Úc (region IPAC) + chủ quyền/tuần tra/tập trận Biển Đông (region Đông Á),
   **MỞ RỘNG 02/08/2026 (chỉ thị Huy):** chủ đề này còn gồm **(a) mọi tin QUÂN SỰ liên quan tới Úc**,
   không riêng AUKUS — ngân sách quốc phòng, mua sắm khí tài, tập trận do Úc chủ trì hay tham gia,
   triển khai lực lượng, cả ba quân chủng (⚠️ trước 02/08 bảng neo chỉ có Hải quân, nên tin của
   **Không quân Hoàng gia Úc / RAAF** — quân chủng chủ trì Pitch Black — không khớp neo nào và bị
   chặn oan; đo thật: tin KC-30A tiếp dầu Rafale Ấn Độ ngày 31/07 sót cả ở tầng quét lẫn tầng neo);
   và **(b) hoạt động quân sự cùng CHIẾN TRANH VÙNG XÁM ở Biển Đông** — vòi rồng, đâm va, chiếu laser,
   cắt cáp ngầm, dân quân biển, hải cảnh, bồi đắp, quân sự hoá thực thể, phong toả tiếp tế.
   ⛔ **Từ chỉ vùng xám KHÔNG được đưa vào bảng neo `NEO_UC_BIEN_DONG`** — "vùng xám", "gray zone",
   "vòi rồng", "cắt cáp" đều KHÔNG tự neo được vào vùng biển này (vùng xám còn ở Baltic, Bắc Cực,
   eo biển Đài Loan), thêm vào là mục 2 trở lại thành cái thùng, đúng lỗi Huy bắt 01/08. Tin vùng xám
   vào mục 2 nhờ neo sẵn có (`bien dong`, `philippines`, `hai canh`, `dan quan bien`…). Chúng chỉ nằm
   ở **bảng gợi ý** `TOPIC_KEYWORDS_VI/EN` (dùng để phân loại ứng viên, được phép rộng) và ở truy vấn
   Google News — nơi đã tự neo bằng cụm `"South China Sea"`. Ca 17·18·19 của
   `tests/test-cong-uc-bien-dong.py` canh cả ba chiều: vùng xám Biển Đông phải qua · tin RAAF không có
   chữ "Úc" phải qua · vùng xám Baltic phải bị chặn.
   **MỞ RỘNG 27/07/2026: tin liên quan tới CÁC NƯỚC KHÁC trong khu vực Biển Đông** — Malaysia, Indonesia,
   Brunei, Đài Loan, Việt Nam, và hoạt động của Nhật/Ấn/Hàn tại vùng biển này; đàm phán COC ASEAN–Trung
   Quốc; các thực thể Natuna, Bãi Tư Chính, Luconia, Bãi Cỏ Rong. → `worldNews`.
   ⛔ **"TẠI VÙNG BIỂN NÀY" LÀ ĐIỀU KIỆN, KHÔNG PHẢI LỜI DẪN** (siết 01/08/2026, Huy bắt: *"hàn quốc
   liên quan đ gì đến biển đông và Úc mà cứ cho vào???"*). Tin quốc phòng **nội bộ** Nhật/Ấn/Hàn/Trung
   Quốc — phóng thử tên lửa, ký hợp đồng đóng tàu, luật quốc phòng trong nước — **KHÔNG thuộc chủ đề
   này** dù nghe rất "quân sự châu Á". Chuẩn nhận: câu chữ phải tự neo được vào **Úc/AUKUS**, vào
   **vùng biển & thực thể Biển Đông**, hoặc vào **một nước ven biển đó**. Nay đã cưỡng bức 02 tầng —
   `add_news.py::check_neo_chu_de_2` (cổng nạp) và `make_docx.py::la_uc_bien_dong` (cổng dựng .docx),
   bảng neo dùng chung ở `scripts/topics.py::NEO_UC_BIEN_DONG`. Xem mục "ĐÃ VÁ 02 TẦNG" bên dưới.
3. **CNQS Mỹ** — khí tài/hệ thống cụ thể. → `usNews`, cat `Công nghệ quân sự`.
   ⏳ **KHUNG NGÀY NỚI RIÊNG: lùi tới 3 ngày** (chỉ thị Huy 27/07/2026 — "quét ngày 27 thì có thể lấy tin
   xuống tận ngày 24"), trong khi 4 chủ đề còn lại vẫn chỉ hôm nay + hôm qua. Lý do: tin khí tài/hợp đồng
   đăng thưa, cuối tuần Mỹ gần như trắng. Cưỡng bức bằng `MAX_AGE_DAYS_CNQS = 3` trong `add_news.py`
   (áp theo **category** `Công nghệ quân sự`) và `CNQS_LOOKBACK_DAYS` trong `harvest.py` — sửa một bên
   phải sửa bên kia.
4. **Mỹ–Mali** — Mỹ cân nhắc/không kích JNIM ở Sahel. → `usNews`, dossier `🟤 Mỹ – Mali`.
   🔄 **ĐỔI KÊNH GỬI 05/08/2026 — xem mục "MALI RỜI FILE WORD" bên dưới.** Quét và nạp KHÔNG đổi.
5. **Tập trận ĐANG DIỄN RA** (nhãn chủ đề cố định `Tập trận`) → `exerciseUpdates`, `name` khớp ĐÚNG tên trong `DATA.exercises`.
   ✅ **VÁ GỐC 05/08/2026 (chỉ thị Huy: *"đang có tập trận nào thì chỉ tập trung quét thông tin về tập trận đó. Tự động mở rộng nguồn quét tuỳ theo tập trận để tìm được tối đa thông tin"*) — HẾT phải "sửa đủ 05 chỗ".** Trước đó chủ đề 05 neo cứng tên một kỳ (`Predator's Run`, rồi `Pitch Black`) rải ở 05 chỗ, và **đổi kỳ mà quên một chỗ là chủ đề câm trong im lặng — đã xảy ra thật hai lần**. Nay nhãn là hằng `topics.CHU_DE_TAP_TRAN = "Tập trận"` (không bao giờ đổi), còn từ khoá/truy vấn/nguồn sinh ĐỘNG từ chính `DATA.exercises` mỗi lượt chạy. Đổi kỳ tập trận **không phải sửa dòng mã nào**.
   | Mảnh | Việc |
   |---|---|
   | `scripts/tap_tran.py` | Nguồn sự thật: `dang_dien_ra` · `tu_khoa` · `truy_van` · `nuoc_chu_nha` · `nguon_mo_rong` |
   | `topics.py::nap_tu_khoa_tap_tran()` | Bơm từ khoá vào bảng phân loại lúc chạy; bảng mặc định CỐ Ý RỖNG |
   | `harvest.py::nap_tap_tran_dang_chay()` | Gọi ở ĐẦU `main()`, in dòng `🎖️ Tập trận đang bám: …` |
   | `telegram_harvest.py` | Bơm riêng — hai lớp quét chạy hai tiến trình, mỗi lớp nạp `topics` của mình |
   | `prompt_chatgpt.py::_luat_tap_tran()` | Khối luật + tên mẫu JSON sinh động theo cuộc đang chạy |
   | `tests/test-mali-va-tap-tran.py` | **26 ca · `--tu-kiem` bắt 12/12 bản hỏng** |
   - ⛔ **KHÔNG tin trường `status` trong DATA** — đo thật 05/08/2026: `Predator's Run` (hết 29/07) và `RIMPAC` (hết 31/07) **vẫn mang `status: "ongoing"`** vì web tự suy từ `dates` nên không ai buồn sửa; ngược lại `Hán Quang 42` khai `upcoming` trong khi dải ngày 5–14/8 đã chứa hôm nay. Trạng thái thật tính bằng `tap_tran.trang_thai()` (bản Python của `index.html::evRange`). `status` chỉ là fallback khi `dates` không parse nổi ngày (`"Tháng 9/2026"`).
   - **Không có cuộc nào đang chạy thì lấy cuộc SẮP diễn ra trong 7 ngày** — giữa hai kỳ luôn có quãng trống, mà tin chuẩn bị (điều quân, khai mạc, danh sách nước tham gia) rơi đúng vào đó. Không có nhánh này thì chủ đề 05 lại về 0 bài.
   - ⚠️ **Bơm từ khoá phải đưa chủ đề tập trận lên ĐẦU bảng duyệt của `match_topic`.** Đo lúc dựng: tiêu đề thật *"Exercise Pitch Black wraps up at RAAF Darwin"* chứa `RAAF`, mà bảng "Úc & Biển Đông" đứng trước ⇒ ở **lớp RSS/HTML** (mỗi bài chỉ được gán MỘT nhãn) tin tập trận bị chủ đề 02 ăn mất, và `uu_tien_chu_de` không cứu được vì nó chỉ xử tranh chấp giữa hai bản CÙNG URL. Ca [22] canh chiều này, ca [26] canh chiều nới tay (tin RAAF thuần vẫn phải ở chủ đề 02).
   - ⚠️ **Ba cái bẫy đã vấp NGAY lượt chạy đầu, đừng dựng lại:** (i) tách địa danh bằng regex `[A-ZÀ-Ỹ]` sinh từ khoá RÁC (`'lanh'`, `'u khong'`) vì dải đó không phủ hết chữ Việt tổ hợp — nay chỉ lấy từ ASCII viết hoa, và loại mảnh của tên nước (`"Đài Loan"` → bỏ `'loan'`, vì `'loan'` khớp trong "hỗn loạn"); (ii) `nuoc_chu_nha` phải suy từ `location` TRƯỚC, gộp cả `summary` thì "Hán Quang (Đài Loan)" ra `US`; (iii) dịch tên nước bằng `.replace()` biến `"trung quoc"` thành `"trung qAustralia"` — phải dùng bảng `TEN_ANH`.
   - ⚠️ **Từ khoá phải sinh CẢ dạng CÓ DẤU** — `match_topic` so regex trên văn bản GỐC, bơm mỗi bản bỏ dấu là câm với mọi tiêu đề tiếng Việt. Ca [15] canh.
   ⛔ **VÀ SỬA ĐỦ 05 CHỖ VẪN CHƯA ĐỦ — chủ đề 05 còn câm thêm một tầng nữa, vá cùng ngày 02/08/2026.** Khâu gộp cuối `harvest.py::main` khử trùng theo **URL trên TOÀN lô**, nên bài nào tới trước thì chủ đề đó giữ, chủ đề tới sau mất bài vĩnh viễn. Cùng ngày, chủ đề 02 được thêm truy vấn `"Pitch Black" Australia exercise` (để bắt tin Không quân Úc) mà trong `GNEWS_QUERIES` chủ đề 02 đứng **TRƯỚC** chủ đề 05 ⇒ mục tập trận báo **0 bài mỗi phiên** trong khi truy vấn của chính nó vẫn trả về **5–8 tin đúng khung ngày**. Đo thật: sửa xong 05 chỗ lúc 21:06, chạy `harvest.py --gnews` lúc 22:0x vẫn ra `-- Pitch Black (0 bài) --`. Không lỗi, không cảnh báo, bảng vẫn đủ 5 dòng — đọc vào chỉ thấy *"(không có ứng viên nào trong khung hôm nay + hôm qua)"* và tưởng hôm đó không có tin.
   - **Thứ tự giành URL nay khai TƯỜNG MINH ở `harvest.py::UU_TIEN_CHU_DE`**, không dựa vào thứ tự khai trong dict — dựa vào thứ tự dict thì người sau sắp lại dict cho gọn sẽ dựng lại đúng lỗ này mà không hay. Nguyên tắc xếp: chủ đề **HẸP đứng trước chủ đề RỘNG**; mục tập trận hẹp nhất nên giành trước mục 02.
   - **Thêm chủ đề mới vào `GNEWS_QUERIES` thì phải khai luôn vào `UU_TIEN_CHU_DE`** — quên khai thì nó xuống cuối và bị chủ đề khác ăn mất, hỏng câm y hệt. Ca [08] canh đúng chỗ này.
   - ⚠️ **Truy vấn của chủ đề 05 CỐ Ý không có `OR RAAF`.** Vì nó giành URL trước, một truy vấn rộng sẽ kéo mọi tin Không quân Úc vào mục tập trận, kể cả tin không dính kỳ tập trận nào. Tin RAAF chung đã có truy vấn riêng ở chủ đề 02 — và chủ đề 02 **phải giữ** truy vấn đó (ca [07] canh chiều ngược, bỏ đi là tin RAAF câm trở lại).
   - Nghiệm thu 02/08: chủ đề 05 **0 → 6 bài**, chủ đề 02 từ 68 → 60 (đúng phần chuyển sang mục riêng), không mục nào mất bài. Bộ test `tests/test-uu-tien-chu-de.py` — **10 ca (05 ca PHẢI CHẶN) · `--tu-kiem` bắt 7/7 bản hỏng**, đã nạp `BO_TEST` của `HeThong/khoe.py`.

**BỎ khỏi phạm vi:** Kinh tế, Ngoại giao chung, xNews (X/Twitter), các vùng thế giới khác, tạo mới
dipEvents, và **SÀN CỨNG 15+15**. **Báo Mới:** vẫn quét nhưng CHỈ giữ bài hợp 5 chủ đề trên.
Chi tiết vận hành đầy đủ: **`.claude/skills/quet-tin/SKILL.md`** (mục "PHẠM VI MỚI"). Các mục
"15+15 / 4 chuyên mục / 2 lần-ngày" bên dưới CHỈ còn giá trị tham khảo lịch sử — KHÔNG áp dụng nữa.
**Email + file Word:** Action `notify-email.yml` tự xuất .docx toàn bộ tin vừa quét (đúng format bản
tin mẫu) + gửi **lamgiaphat1603@gmail.com** khi có commit `Cap nhat ban tin`.
**⚠️ SUBJECT PHẢI GHI RÕ BUỔI (chỉ thị Huy 27/07/2026):** `📰 Điểm Tin Thế Giới BUỔI SÁNG 27/07 (5 tin)`
/ `… BUỔI TỐI …` — nhìn tiêu đề là biết ngay bản nào, không phải mở ra đoán. `send-email.js` suy buổi
từ **giờ VN lúc Action chạy** (`Intl.DateTimeFormat` timeZone `Asia/Ho_Chi_Minh`, <14h = SÁNG, ≥14h =
TỐI — cùng quy ước ô khoá của `state.py`), áp cho cả subject và tiêu đề trong thân email.
Đổi lịch quét thì phải xem lại ngưỡng 14h này.

**📄 TÊN FILE .docx GỌI THEO MỐC GIỜ (chỉ thị Huy 28/07/2026 — GHI ĐÈ tên cũ
`Diem-tin-<ngày>-sang.docx` / `-toi.docx`):**
| Buổi | Tên file |
|---|---|
| Sáng sớm (fire 03:47–05:30) | `Diem-tin-sang-som-5h-<YYYY-MM-DD>.docx` |
| Tối (fire 20:47–22:30) | `Diem-tin-toi-21h-<YYYY-MM-DD>.docx` |
| Bản dựng lại trong ngày | tên trên **cộng thêm đúng `-bo-sung`** |

⛔ **CẤM ĐƯA TÊN NGƯỜI VÀO TÊN FILE .docx — tên Jay Lâm, tên Huy, hay tên bất cứ ai** (chỉ thị Huy
30/07/2026, nguyên văn: *"đừng bao giờ cho tên Jay Lâm hay tên con vào tên file word. ghi thêm chữ
bổ sung được rồi"*). **Cơ chế gây vấp:** tối 30/07 một bản dựng lại được đặt tay là
`…-BO-SUNG-tin-JayLam.docx` để tự phân biệt với bản gốc, rồi gửi qua Telegram — mà Telegram hiển
thị **đúng basename**, nên tên người đi thẳng vào đoạn chat CÓ NGƯỜI NGOÀI, và chính người bị nêu
tên nhận được file mang tên mình. Tên file là thứ đi ra ngoài cùng file, không phải ghi chú nội bộ.
Cần phân biệt bản nào thì thêm hậu tố mô tả **VIỆC** (`-bo-sung`), không bao giờ mô tả **NGƯỜI**.
Áp cho cả file do `make_docx.py` sinh lẫn file đặt tay khi dựng lại.

⚠️ **Luật đặt tên nằm ở ĐÚNG MỘT chỗ: `make_docx.py:ten_file()`** — nó là nơi sinh file, và
Telegram (kênh gửi DUY NHẤT hiện nay) hiển thị đúng basename của file trên đĩa. `send-email.js`
lấy lại bằng `path.basename(docxPath)` chứ **KHÔNG tự ghép tên**. Trước 28/07/2026 hai nơi ghép
riêng: file trên Telegram tên `Diem-tin-ngay-<ngày>.docx` **không phân biệt buổi** (hai bản cùng
ngày trùng tên nhau), còn email lại gắn `-sang`/`-toi` — cùng một file mà hai kênh gọi hai tên.
Đừng tách ra lại: hai bộ luật song song chắc chắn lệch, mà lệch âm thầm.
⚠️ Ngưỡng buổi 14h giờ VN nay nằm ở **BỐN** nơi — `make_docx.py:ten_file` · `send_telegram.py:slot_label`
· `send-email.js` · `scripts/state.py`. Đổi lịch quét thì xem lại cả bốn. **Email tối (24/07/2026):
chỉ liệt kê TIÊU ĐỀ điểm tin, KHÔNG tóm tắt** — chi tiết nằm trong file .docx đính kèm. **(Đã BỎ Discord.)**

**⚠️ Email BẮT BUỘC có mục "Chủ đề thiếu và lý do" (chỉ thị Huy 25/07/2026) — `logs/scan-gaps.json`.**
Lý do một chủ đề thiếu bài (Quốc hội nghỉ họp, nguồn 403/timeout, tin trùng sự kiện, ngoài khung 48h…)
là **kiến thức của phiên quét**, GitHub Action KHÔNG tự suy ra được từ `DATA`. Đường dẫn dữ liệu:
| Ai | Làm gì |
|---|---|
| Phiên quét (`web-scan`) | Trước khi commit, ghi `logs/scan-gaps.json`: `{date, session, topics:[{name,count,target,min,thieu,reason}], note}` — liệt kê ĐỦ 5 chủ đề (+ Báo Mới), kể cả chủ đề đủ (để email in dòng sản lượng). Mẫu + quy tắc viết `reason`: **Bước 4b** trong `.claude/skills/quet-tin/SKILL.md`. Phải `git add logs/` kèm bản tin. |
| `.github/scripts/send-email.js` | Hàm `readGaps` + `buildGapsHtml`/`buildGapsText` dựng khối "Sản lượng N chủ đề" (đỏ ở chủ đề thiếu) + "⚠️ Chủ đề thiếu và lý do" trong CẢ bản HTML lẫn bản text. |

**Chốt an toàn:** `send-email.js` **BỎ cả mục** (chỉ log, không làm vỡ email) khi — thiếu file · JSON
lỗi · `topics` rỗng · **`date` trong file ≠ `DATA.generatedAt`** (chống gửi lý do của hôm trước). Vì vậy
`date` của file phải khớp `generatedAt` sau khi chạy `add_news.py`; nạp nhiều lô thì lấy ngày lô CHẠY
CUỐI. `thieu` là cờ tường minh, không có thì suy từ `count < min`.
**Xem trước email không gửi thật:** `DRY_RUN=1 node .github/scripts/send-email.js` → in bản text + ghi
`/tmp/email-preview.html`. (Máy Huy chưa cài `node`; kiểm cú pháp/logic không cần node được bằng
`/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Helpers/jsc` với stub `require`/`console`.)

### ⛔ TIN MỚI PHẢI XẾP VÀO MỤC CÓ SẴN — TẠO MỤC MỚI PHẢI HỎI HUY TRƯỚC
Chỉ thị Huy 27/07/2026, áp cho **mọi** đề xuất tin, không riêng bot Telegram.

Web đã có đủ chỗ cho gần như mọi tin quốc tế — cái bị siết hôm 23/07 là **phạm vi QUÉT**,
không phải cấu trúc lưu. Tin Nga–Ukraine, Trung Đông, châu Âu… vẫn xếp vừa `worldNews` với
`category` + `region` phù hợp. Vì vậy **đừng đề nghị dựng mục mới cho tin ngoài 5 chủ đề** —
đó là phản xạ sai, và một mục mới kéo theo sửa giao diện, sửa script nạp, sửa email/.docx.

| Mục có sẵn | Dùng cho |
|---|---|
| `worldNews` | Tin thế giới, **kể cả ngoài 5 chủ đề** — cần `category` + `region` |
| `usNews` | Tin về Mỹ — cần `category` |
| `exercises` → `items` | Diễn biến cuộc tập trận ĐÃ CÓ (tên khớp chính xác) |
| `dipEvents` → `items` | Diễn biến sự kiện ngoại giao ĐÃ CÓ (tên khớp chính xác) |
| `analyses` | Bài viện nghiên cứu — cần `outlet` + `takeaway` |

Không xếp vừa mục nào thì **nói thẳng "không có mục phù hợp"** và để Huy quyết. Tạo mục mới
là **quyết định của Huy**, không phải chuyện tự làm rồi báo sau.

| Mảnh | Việc |
|---|---|
| Bảng `dt_bot_hoi` | Mỗi lượt hỏi: `cau_hoi`, `tra_loi`, `chu_de[]`, `trong_pham_vi`, `tin_de_xuat` (jsonb) |
| Bảng `dt_ho_so_doc_gia` | Hồ sơ sở thích đọc tin theo `chat_id` |
| `scripts/bot_luu.py` | Bot ghi một lượt hỏi vào `dt_bot_hoi` |
| `scripts/ho_so_doc_gia.py` | `--so-lieu` đếm thống kê thô · `--luu` lưu hồ sơ đã viết |
| `.github/prompts/telegram-bot.md` | Mục "Sau khi trả lời" — phân loại, tìm tin, lưu, đề xuất |

⚠️ **RLS cố ý CHẶT — anon chỉ INSERT, KHÔNG SELECT.** Repo này PUBLIC nên anon key nằm
công khai trong `index.html`; nếu mở SELECT thì ai cũng đọc được câu hỏi người khác nhắn
riêng cho bot. Đã kiểm thật bằng chính anon key đó: chèn trả **201**, đọc trả **`[]`** dù
bảng có dữ liệu. Nhờ vậy workflow ghi được mà **không cần service key** trong GitHub secret.

⚠️ **ĐỌC `dt_bot_hoi` dùng MÃ RIÊNG, KHÔNG dùng service key.** Service key mở **toàn bộ
database** — gồm ViNha, bi-a, Hương Diện; quá đắt cho một việc chạy 10 lần/tháng. Thay vào
đó có mã chỉ mở quyền đọc 2 bảng `dt_*`, gửi qua header `x-dt-key`:
| | |
|---|---|
| Mã nằm ở | `/Users/Huy/Claude/.dt-bot-key` (chmod 600, **NGOÀI repo** vì repo public) |
| Database giữ | Chỉ **SHA-256** của mã — đọc được DB cũng không suy ngược ra mã |
| Cơ chế | Hàm `public.dt_ma_hop_le()` + policy SELECT/UPDATE, migration `dt_quyen_doc_bang_ma_rieng` |
| Đổi mã | Sinh mã mới vào file đó → tính lại sha256 → chạy lại migration với hash mới |
Đã kiểm 3 ca: không mã → `[]` · mã đúng → đọc được · mã sai → `[]`.
⚠️ `--luu` **cũng phải gửi header này**: upsert = INSERT + UPDATE, mà UPDATE chỉ mở khi có
mã. Thiếu nó thì lần lưu thứ hai trở đi im lặng không ghi đè — hồ sơ đứng yên ở bản đầu.

⚠️ **KHÔNG dựa vào MCP Supabase cho phiên tự động.** MCP này là connector claude.ai, có thể
**vắng mặt trong phiên headless/cron** — đó là lý do routine đi bằng mã riêng + `curl` chứ
không gọi MCP.

### ⛔ MỤC "ÚC VÀ BIỂN ĐÔNG" TỪNG LÀ THÙNG CHỨA MỌI TIN THẾ GIỚI — ĐÃ VÁ 02 TẦNG 01/08/2026 (Huy bắt cùng ngày)

> Nguyên văn: *"hàn quốc liên quan đ gì đến biển đông và Úc mà cứ cho vào???"*

**Số đo tối 01/08:** mục đó có 04 tin thì **03 sai** — Nhật phóng thử Tomahawk từ JS Chokai ·
Trung Quốc phóng thử YJ-20 · Hàn Quốc ký hợp đồng 7,8 nghìn tỷ won với Hanwha Ocean. Cả ba đều
là tin quốc phòng châu Á **không dính Úc, không dính Biển Đông**. Chỉ tin Bisalloy/AUKUS đúng.

**Cơ chế gây vấp — HAI tầng, và tầng dưới làm tầng trên vô hình:**
- **Tầng QUÉT:** chủ đề 2 khai *"hoạt động của Nhật/Ấn/Hàn **tại vùng biển này**"*. Mệnh đề
  "tại vùng biển này" là ĐIỀU KIỆN, nhưng đọc lướt thì thành "tin quốc phòng Nhật/Ấn/Hàn" —
  và không guardrail nào kiểm chủ đề, `add_news.py` chỉ kiểm ngày · URL · trùng.
- **Tầng DỰNG FILE:** `make_docx.py::build_sections` đặt `sec2 = MỌI worldNews trừ Mali`. Tên
  mục là một lời hứa, nội dung là cái thùng — nên tin thế giới nào lọt qua tầng quét cũng tự
  động được dán nhãn "Úc và Biển Đông". **Đây mới là chỗ che lỗi:** nếu mục có tên trung thực
  thì lỗi tầng quét đã lộ ra từ nhiều bản tin trước.

⚠️ **Đừng vá bằng cách đổi tên mục thành "Thế giới".** Làm thế là hợp thức hoá tin ngoài phạm
vi: 5 chủ đề đã chốt 23/07 không có mục "tin quốc phòng châu Á nói chung". Vá đúng là **siết
tầng quét** (tin Nhật/Hàn/Ấn/TQ chỉ nhận khi gắn Biển Đông hoặc gắn Úc) rồi mới bàn tới việc
mục 2 có cần lưới an toàn riêng không.
⚠️ **Nhưng cũng đừng để mất tin trong im lặng.** `build_sections` cố ý có lưới cuối gom tin
không khớp mục nào về mục 1 kèm cảnh báo, vì *mất tin tệ hơn xếp nhầm mục* — siết sec2 thì
phải kiểm lại lưới đó còn kêu đúng không, đừng để tin rơi ra ngoài file.
**✅ ĐÃ VÁ 01/08/2026 — 02 tầng cùng lượt, giữ CẢ HAI, đừng bỏ tầng nào.**

| Tầng | Chỗ vá | Chặn gì |
|---|---|---|
| Nạp lên web | `scripts/add_news.py::check_neo_chu_de_2`, gọi trong `validate_news_items` **chỉ khi `label == "worldNews"`** | tin lạc chủ đề không lên được `index.html` |
| Dựng file .docx | `.github/scripts/make_docx.py::la_uc_bien_dong`, siết `sec2` | tin lạc chủ đề không được dán nhãn mục 2 |

Bảng neo là **`scripts/topics.py::NEO_UC_BIEN_DONG`** — một nguồn sự thật, `make_docx.py`
**import** chứ không chép (import chéo thư mục, cố ý để ném lỗi nếu hỏng: file .docx không
sinh ra và CI đỏ ngay, còn `try/except` cho êm thì mục 2 lặng lẽ trở lại làm cái thùng).

⚠️ **Bảng neo KHÁC HẲN `TOPIC_KEYWORDS_*["Úc & Biển Đông"]` — đừng gộp lại.** Hai bảng ngược
chiều nhau: bảng cũ để **GỢI Ý ứng viên** nên cố ý RỘNG (thà nhắc thừa còn hơn bỏ sót); bảng
neo để **CHẶN** nên phải HẸP, mỗi từ tự nó neo được vào Úc hoặc vào Biển Đông.
⚠️ **Cố ý KHÔNG có Nhật/Hàn/Ấn/Trung Quốc trong bảng neo** — đó chính là điều kiện đang
thiếu. Tin bốn nước ấy chỉ vào mục 2 khi câu chữ tự mang một neo (ví dụ *"Japan and the
Philippines patrol the South China Sea"*).
⚠️ **Cố ý KHÔNG có `bien hoa dong`/`senkaku`**: Biển Hoa Đông là biển KHÁC — để nó vào thì
mọi va chạm Nhật–Trung ở Senkaku lại rơi vào mục "Úc và Biển Đông", đúng con lỗi vừa vá.
⚠️ **KHÔNG có cửa mở bằng cờ.** Tin không neo được thì thuộc chủ đề khác (chuyển `usNews`)
hoặc ngoài phạm vi (bỏ, ghi `logs/loai-tin.md`). Mở một cửa ở đây là dựng lại cái thùng dưới
tên khác.
⚠️ **Cổng nạp CHỈ áp cho `worldNews`, không áp `baomoiNews`** dù tin Báo Mới cũng được gộp
vào `worldNews` khi ghi — Báo Mới có 4 chuyên mục và cổng riêng, chặn ở đây là chặn oan tin
Báo Mới thuộc chủ đề Nội bộ Mỹ. Phần hở đó do tầng `make_docx.py` gánh: nó lọc trên `world`
**sau** khi đã gộp.
⚠️ **Ngoại lệ Mali phải giữ** (`MALI_KEYS_ADD` trong `add_news.py`): chủ đề 4 đôi khi nằm ở
`worldNews` và có mục riêng. Giữ đồng bộ với `MALI_KEYS` bên `make_docx.py` — hai nơi lệch
thì tin Sahel bị chặn ở tầng này trong khi tầng kia vẫn chờ nó.

**Lưới an toàn vẫn nguyên, và nay KÊU TÁCH nguyên nhân:** tin rớt không biến mất, vẫn dồn về
mục 1 (*mất tin tệ hơn xếp nhầm mục*). Nhưng dòng cảnh báo tách làm hai — *"tin worldNews
KHÔNG neo được vào Úc/Biển Đông … Đây là lỗi TẦNG QUÉT"* so với dòng cũ *"không khớp mục
nào → xem lại phân loại"*. Gộp chung một câu thì hai nguyên nhân khác nhau ra cùng chữ và
người đọc đi sửa nhầm chỗ.

**Số đo nghiệm thu 01/08:**
- Trên **dữ liệu thật**: 38 tin `worldNews` từ 28/07 → **34 nhận · 04 rớt**, và 04 tin rớt
  đúng là 03 tin Huy chê + tin *"Hàn Quốc luật hóa cam kết… tàu ngầm hạt nhân"* mà mục
  28/07 bên trên đã ghi là lọt oan. Không tin Biển Đông/Philippines/Úc/Đài Loan nào bị chặn.
- Chạy `make_docx.py` thật: lưới kêu đúng **03 tin**, file .docx vẫn sinh ra, tin không mất.
- Bộ test `tests/test-cong-uc-bien-dong.py`: **16 ca (08 PHẢI CHẶN · 08 đối chứng chống chặn
  oan) · 10/10 bản hỏng đều bị bắt**, gồm 01 bản hỏng canh **chiều nới** (thêm thẳng
  japan/korea/china vào bảng neo). Đã nạp `BO_TEST` của `HeThong/khoe.py`.
- 17/17 bộ test của repo vẫn đạt sau khi vá.

⚠️ **Bẫy khi sửa bộ test này:** `--tu-kiem` KHÔNG ghi đè file thật — mỗi bản hỏng dựng một
**bản sao repo tối giản** trong thư mục tạm mang PID + sha1 nội dung, giữ nguyên cấu trúc
`scripts/` + `.github/scripts/` để `make_docx.py` vẫn tự tìm `../../scripts/topics.py` của
BẢN SAO. Repo này thường có nhiều phiên Claude chạy song song; ghi đè file thật là xoá việc
của phiên khác.
⚠️ **Ca test phải dùng `category` THẬT** (`VALID_CATEGORIES`). Vấp lúc dựng: đặt
`category: "Quân sự"` thì cổng category chặn trước, 03 ca "PHẢI CHẶN" vẫn XANH nhưng xanh vì
**lý do sai** — đo nhầm nhánh mà bảng kết quả trông vẫn bình thường.

## Thứ tự ưu tiên khi chọn nguồn để quét (áp dụng từ 10/07/2026, cập nhật 10/07 thêm ưu tiên #1)
1. **Ưu tiên nguồn chính phủ/chính thức (primary).** Khi một tin dựa trên thông báo/phát ngôn/tài liệu chính thức, ưu tiên link THẲNG tới nguồn gốc (defense.gov, nato.int, state.gov, whitehouse.gov, baochinhphu.vn...) thay vì chỉ dẫn lại báo chí. Chủ động tìm tin đáng đưa từ các nguồn chính thức này. LƯU Ý ngoại lệ truyền thông nhà nước độc tài (xem cảnh báo ở mục "Nguồn chính phủ/chính thức").
2. **Ưu tiên nguồn tiếng Anh** trước nguồn tiếng Việt. Nguồn Việt chỉ dùng bổ sung khi nguồn Anh không đủ tin, hoặc để lấy góc nhìn/tin trong nước.
3. **Ưu tiên nguồn có RSS feed** trước — nhanh và chính xác hơn tìm kiếm/web scraping thủ công. Nếu nguồn không có RSS hoặc RSS không truy cập được, mới dùng WebSearch/WebFetch.
4. **Ưu tiên nguồn CHƯA từng được quét trước đó.** Kiểm tra bằng `grep -oE "\"sourceName\":\"[^\"]+\"" index.html | sort | uniq -c` để biết nguồn nào đang bị bỏ sót.
5. **Điều hướng theo sở thích người đọc.** Người đọc bấm 👍/👎 trên từng tin, đồng bộ lên Supabase (giao diện KHÔNG hiển thị phân tích sở thích — chỉ thu vote; phân tích là việc của quy trình quét). Mỗi lần quét, session **đọc file local `preferences.json`** (gốc repo) để ưu tiên (điểm dương `net`) / giảm ưu tiên (điểm âm) chuyên mục · khu vực · nguồn. File này do **GitHub Action `sync-preferences.yml`** tự cập nhật hằng ngày: Action chạy trên máy GitHub (không bị Cloudflare chặn như môi trường quét), curl view công khai `vote_stats` từ Supabase rồi commit vào `main`. Đây là **định hướng mềm**: vẫn giữ tối thiểu 2 tin/category, không bỏ hẳn mục nào, không ghi đè quy tắc nguồn 3 tầng/chất lượng. (Chi tiết: `preferences.md`. Schema: `docs/supabase-setup.sql`.) LƯU Ý: KHÔNG tự WebFetch `*.supabase.co` khi quét — bị chặn 403 (đã kiểm chứng 12/07), việc lấy dữ liệu đã có Action lo.

## ~~Chỉ tiêu số lượng (SÀN CỨNG 15+15)~~ — ⚠️ LỖI THỜI 2026-07-23, xem banner đầu file (giờ là 5 chủ đề × 5–10 bài)
**SÀN CỨNG TỔNG NGÀY (gộp cả phiên sáng + tối): `worldNews` ≥ 15 tin · `usNews` ≥ 15 tin — CHẤT LƯỢNG CAO.**
Cơ chế 2 phiên:
- **Phiên SÁNG (10:15):** nhắm **~10 tin/mục** là đủ — không cần ép đủ 15 ngay, để phần còn lại cho tối.
- **Phiên TỐI (20:15):** đọc tín hiệu tổng ngày, **bổ sung cho tổng ngày mỗi mục đạt ≥ 15**. **CHƯA ĐỦ THÌ CHƯA DỪNG** → giao thêm agent Sonnet riêng mục thiếu, chạy lại `add_news.py`, LẶP tới khi cả hai mục ≥15.
- Nếu **một phiên SKIP/FAIL** (phiên kia không chạy): phiên còn lại gánh toàn bộ — kéo tổng ngày lên đủ 15/mục.

Đo bằng: `add_news.py` gắn `_addedDate` = ngày đưa lên cho mỗi tin, dòng cuối in `SÀN CỨNG TỔNG NGÀY … worldNews X/15 · usNews Y/15` (đếm tin `_addedDate == hôm nay`, gộp cả 2 phiên).

"Chất lượng cao" = qua guardrail + đúng nguồn 3 tầng + đúng bộ lọc sở thích + link thẳng bài gốc trong khung 2 ngày. **KHÔNG hạ chuẩn để nhồi cho đủ số**: không bịa tin/link, không lấy tin cũ hơn hôm qua, không nhét tin rác. Chính trị nội bộ Mỹ đã SIẾT còn điều trần + bỏ phiếu thông qua dự luật (xem bộ lọc), nên **sàn 15 tin us giờ dựa chủ yếu vào CNQS + Ngoại giao + Kinh tế us + điều trần/bỏ phiếu** — thiếu thì giao thêm agent các mục đó, TUYỆT ĐỐI KHÔNG nới lại nội bộ Mỹ (đảng phái/drama/horserace...) để lấp cho đủ.

Phân bổ GỢI Ý CẢ NGÀY trong mỗi mục ≥15 (linh hoạt, miễn tổng mục đạt sàn):
| Category | Gợi ý mỗi mục (world / us) |
|---|---|
| **Công nghệ quân sự** | 4–6 tin (chủ đề thích nhất — khí tài/hệ thống cụ thể) |
| **Ngoại giao** | 4–6 tin (hiệp định/khuôn khổ an ninh–QP, thượng đỉnh có kết quả) |
| **Kinh tế** | 2–4 tin (vĩ mô/chính sách/chuỗi cung ứng chiến lược) |
| **Chính trị** | 3–5 tin (world: thể chế/chiến lược great-power · **us nội bộ: CHỈ phiên điều trần + kết quả bỏ phiếu thông qua dự luật**) |
| 🎯 **Trọng tâm chủ động** | **Úc · Biển Đông · Nội bộ Mỹ** — nằm rải trong 4 category trên, mỗi trọng tâm 1–2 tin/phiên nếu có |

| Phần khác | Chỉ tiêu (KHÔNG tính vào sàn 15+15) |
|---|---|
| `xNews` | 2–4 tin (ưu tiên tài khoản QP/an ninh/chính thức) |
| `exercises` (tập trận) | 1–2 tin cập nhật (sự kiện `ongoing`) |
| `dipEvents` (ngoại giao) | **2–4 tin cập nhật + CHỦ ĐỘNG tạo 1–2 sự kiện MỚI mỗi ngày** — mỗi sự kiện PHẢI có `status` đúng: `upcoming` · `ongoing` · `recent` |

→ Tổng **≥30 tin bản tin/ngày** (15 world + 15 us) + xNews + sự kiện. **Fallback bất khả kháng:** chỉ khi đã giao ≥3 vòng agent bổ sung mà vẫn không đủ tin SẠCH (ngày cực khan / môi trường lỗi) mới chấp nhận thiếu — ghi RÕ trong tóm tắt còn thiếu bao nhiêu và vì sao. Thiếu vì lười giao thêm agent thì KHÔNG chấp nhận. Tuyệt đối không bịa để lấp.

### Bộ LỌC SỞ THÍCH (bắt buộc — nhúng vào mọi agent; nguồn: `diemtin-content-prefs.md` + `preferences.md`)
> **Hai hồ sơ, không conflict:** `diemtin-content-prefs.md` = **Hiến chương** (cấu trúc/triết lý/cách viết — thắng khi lệch về mấy thứ đó); `preferences.md`/`preferences.json` = **vote** (tinh chỉnh mức ưu tiên chủ đề). Bảng hoà giải 5 điểm từng lệch (hải quân xếp phụ · ưu tiên nước lớn · Nga–Ukraine chỉ giữ diễn biến MỚI · dung hoà số lượng · nhấn VN–Biển Đông khi gắn quốc tế) nằm CUỐI `diemtin-content-prefs.md` — theo đúng bảng đó.
**ƯU TIÊN (tìm nhiều):** khí tài/công nghệ QP cụ thể (tên lửa, phòng không, hải quân, không gian/Space Force, laser, AI quân sự, tàu ngầm, drone); hiệp định/khuôn khổ an ninh–QP có kết quả (ACSA/RAA/đối tác chiến lược); Kinh tế vĩ mô & định chế (Fed/ECB/BOJ/IMF/OECD/WTO/BIS/WB, nợ công, thuế, chuỗi cung ứng chip); Chính trị THỂ CHẾ/luật/hiến pháp/ngân sách QP/trừng phạt/chiến lược great-power.
**LOẠI BỎ (KHÔNG đưa vào worldNews/usNews):** ❌ cáo phó/người qua đời; ❌ chính trị NHÂN VẬT/bê bối/drama/scandal cá nhân; ❌ đua bầu cử horserace (thắng–thua đảng phái, bầu cử địa phương); ❌ lợi nhuận/vận hành DOANH NGHIỆP đơn lẻ (trừ khi gắn QP / chip–AI / chuỗi cung ứng chiến lược); ❌ chính trị nội bộ xã hội/tư pháp thuần (nhập cư, cải cách công tố…); ❌ tin Nga–Ukraine chiến sự lặp lại.

**🎯 TRỌNG TÂM CHỦ ĐỘNG mỗi phiên — thêm 23/07/2026 (chỉ thị người dùng, GHI ĐÈ các dòng trên khi va chạm):** mỗi lần quét CHỦ ĐỘNG tìm cho đủ 3 trọng tâm này, nhắm **1–2 tin/trọng tâm/phiên nếu có** (best-effort, không đủ thì thôi):
1. **Úc** — AUKUS, quốc phòng/khí tài Úc, ADF, quan hệ an ninh Úc–Mỹ/Nhật/Anh, chính sách Thái Bình Dương của Úc. Gán `region: "Ấn Độ Dương - Thái Bình Dương"`.
2. **Biển Đông** — chủ quyền biển, đụng độ/tuần tra, phán quyết, tập trận, hoạt động của Philippines/VN/TQ/Mỹ ở Biển Đông. Nâng từ "VN chỉ khi gắn quốc tế" thành trọng tâm CHỦ ĐỘNG. Gán `region: "Đông Á"` (hoặc "Ấn Độ Dương - Thái Bình Dương").
3. **Nội bộ Mỹ (usNews) — CHỈ tiến trình lập pháp (chỉ thị người dùng 23/07/2026, siết lại từ "mở toàn bộ"):** với tin CHÍNH TRỊ NỘI BỘ Mỹ, **CHỈ nhận 2 loại**: (a) **các phiên điều trần** Quốc hội/uỷ ban (hearing, testimony, mark-up, chất vấn quan chức); (b) **kết quả hội đồng/uỷ ban/hai viện bỏ phiếu THÔNG QUA dự luật** (committee vote, floor vote, passage của bill/nghị quyết/NDAA/ngân sách...). **LOẠI** phần còn lại của chính trị nội bộ Mỹ: tranh cãi đảng phái/drama, chân dung/động thái chính trị gia, horserace bầu cử, biểu tình, chính sách nhập cư, cải cách tư pháp thuần, bê bối cá nhân... (Lưu ý: tin CHÍNH SÁCH/HÀNH PHÁP gắn quốc phòng–an ninh–kinh tế–ngoại giao vẫn nhận BÌNH THƯỜNG qua các category tương ứng; ràng buộc này chỉ áp cho mục CHÍNH TRỊ NỘI BỘ. Tin thế giới ngoài Mỹ vẫn theo bộ lọc gốc.)

**📌 HAI CHỦ ĐỀ CHÚ TRỌNG QUÉT HÀNG NGÀY — thêm 23/07/2026 (chỉ thị người dùng):**
- **Tập trận Pitch Black 2026** *(thay Predator's Run từ 02/08/2026 — kỳ đó đã kết thúc)* — thẻ `exercises` đã có: `"Pitch Black 2026 (Úc chủ trì, 20 nước tham gia)"` (20/7–7/8, Darwin/Tindal/Amberley, ~100 máy bay, hơn 2.500 quân nhân). **Mỗi phiên CHỦ ĐỘNG tìm diễn biến mới** (khoa mục bay, tiếp dầu trên không, lần đầu của từng nước, tuyên bố chỉ huy) → cập nhật qua `exerciseUpdates` (khớp đúng tên). Nguồn: defence.gov.au, airforce.gov.au, janes.com, dvidshub.net, pacom.mil. **Khi tập trận KẾT THÚC (7/8)** → dùng `exerciseUpdates` kèm nêu trong tóm tắt để đổi `status` sang `recent`, VÀ đổi chủ đề 05 sang kỳ tập trận kế tiếp theo đúng 05 chỗ liệt kê ở mục "5 chủ đề" đầu file — bỏ bước sau là chủ đề 05 lại báo 0 tin mỗi phiên trong im lặng.
- **Mỹ – Mali** — hồ sơ sống mới (dossier `🟤 Mỹ – Mali` trong mục Hồ sơ). **Mỗi phiên theo dõi diễn biến** việc Mỹ cân nhắc/triển khai phương án quân sự ở Mali nhắm JNIM (al-Qaeda): quyết định không kích drone, phản ứng của Mali/Nga (Africa Corps)/JNIM, diễn biến Sahel–Bamako. Tin gắn Mali/JNIM/Bamako/Sahel để tự vào dossier. Ưu tiên nguồn: defense.gov, state.gov, centcom.mil (AFRICOM), Reuters/AP/AFP, WaPo. Đa số là tin **usNews** (chính sách/hành động của Mỹ).

**Nguyên tắc "cứu":** tin công ty/chính trị VẪN nhận nếu gắn chủ đề chiến lược (vd Boeing↔máy bay quân sự, Samsung↔chip AI).
**Khu vực (hoà giải hiến chương):** chọn theo chủ đề/kiểu tin là chính, NHƯNG khi 2 tin ngang chất → ưu tiên tin dính **nước lớn**, hạ (không loại) vùng xa. **VN chỉ khi gắn quốc tế; TQ để tự nhiên** (không đậm/né thêm).
**Trong CNQS:** ưu tiên không quân/tên lửa · hạt nhân–răn đe · không gian/mạng; **hải quân là mảng phụ** (vẫn nhận, nhưng cắt sau cùng).
**Nga–Ukraine:** giữ như hồ sơ sống — chỉ nhận **diễn biến MỚI** (bước ngoặt/ngoại giao/vũ khí mới), loại tin chiến sự lặp.

Nếu một phần thực sự không đủ chỉ tiêu sau khi đã thử nhiều nguồn — chấp nhận thiếu, KHÔNG bịa tin/link, KHÔNG nới bộ lọc để nhồi tin không đúng gu, nêu rõ trong tóm tắt cuối.

## Kiến trúc quét: nhiều agent Sonnet nhỏ (bắt buộc — để nhẹ và chống sập)
> ⚠️ 2026-07-23: bảng 8 agent (Kinh tế/Chính trị/CNQS/Ngoại giao/xNews/exercises/2 Báo Mới) LỖI THỜI. Giờ chỉ 5 luồng cho 5 chủ đề — xem `.claude/skills/quet-tin/SKILL.md` Bước 2. Cơ chế agent Sonnet + chống trùng + review bên dưới vẫn đúng.
Không dùng 1 agent lớn ôm hết việc quét (dễ quá tải/timeout/tốn token). Session điều phối (session hiện tại) tự thực hiện các bước đọc `DATA`/kiểm tra nguồn đã dùng, sau đó **dùng tool Agent để giao việc quét cho các subagent chạy model Sonnet (`model: "sonnet"`)**, mỗi agent chỉ phụ trách MỘT phần vừa phải:

> Ghi chú model (10/07/2026): trước dùng Haiku cho rẻ nhưng lần quét đầu tiên tỷ lệ lỗi cao (~40-50% tin bị loại: sai ngày, link rác/không khớp, trùng tin cũ, mâu thuẫn dữ liệu, bịa ID). Đã đổi sang **Sonnet** để tin thu thập chính xác hơn từ đầu (tốn token hơn Haiku nhưng giảm mạnh vòng quét lại + công review). Guardrail tự động trong `add_news.py` (xem mục Guardrail) vẫn là lớp chặn cuối cùng bất kể model nào.

| Agent | Phạm vi | Sản lượng mỗi agent |
|---|---|---|
| 1 | Category "Kinh tế" — cả worldNews + usNews | ~4–6 tin |
| 2 | Category "Chính trị" — cả worldNews + usNews | ~4–6 tin |
| 3 | Category "Công nghệ quân sự" — cả worldNews + usNews | ~4–6 tin |
| 4 | Category "Ngoại giao" — cả worldNews + usNews | ~4–6 tin |
| 5 | xNews | 4–5 tin |
| 6 | exercises + dipEvents (cập nhật ongoing + **TẠO thêm sự kiện ngoại giao mới, đặt đúng status upcoming/ongoing/recent**) | tập trận 1–2; **ngoại giao 2–4 cập nhật + 1–2 sự kiện mới** |

Quy tắc khi giao việc cho từng agent (viết prompt độc lập, đầy đủ ngữ cảnh vì subagent KHÔNG thấy hội thoại chính):
- **KHÔNG bảo subagent tự đọc `CLAUDE.md`** — file này ngày càng dài, để 6 agent cùng đọc là lãng phí token 6 lần. Agent điều phối tự trích đúng phần cần (nguồn phù hợp + URL RSS nếu có + định dạng field) rồi nhúng thẳng nội dung đó vào prompt của từng agent.
- Nêu rõ: phạm vi (category/phần), chỉ tiêu số lượng, danh sách nguồn phù hợp kèm URL RSS đã biết (xem bảng RSS bên dưới — đưa thẳng URL, không bắt agent tự dò), định dạng field bắt buộc đúng như trên.
- **Ràng buộc chất lượng — nhúng vào MỌI prompt agent** (rút ra từ lỗi lần quét đầu 10/07): (a) `date` CHỈ trong **2 ngày gần nhất — hôm nay + hôm qua** (theo giờ VN), TUYỆT ĐỐI KHÔNG lấy tin cũ hơn hôm qua; (b) `sourceUrl` phải trỏ THẲNG tới 1 bài viết cụ thể, KHÔNG dùng link trang chủ / "live updates" / live-blog / trang tổng hợp, và link phải KHỚP đúng nội dung tin; (c) `sourceName` chỉ trong danh sách nguồn được giao (báo chí) HOẶC nguồn chính phủ/chính thức phù hợp; (d) với xNews: KHÔNG bịa status ID (ID thật ~19 chữ số ngẫu nhiên, không tròn số); (e) thà ÍT tin đạt chuẩn còn hơn nhồi tin sai — được phép trả mảng rỗng.
- **Ưu tiên nguồn chính phủ/chính thức**: khi tin bắt nguồn từ thông báo/phát ngôn chính thức (defense.gov, nato.int, state.gov, whitehouse.gov, centcom.mil, baochinhphu.vn, mofa.gov.vn...), ưu tiên link thẳng nguồn gốc đó thay vì báo dẫn lại. Với truyền thông nhà nước độc tài (Xinhua/TASS/Global Times/Press TV/KCNA): chỉ dùng cho phát ngôn của chính họ, không làm nguồn trung lập cho sự kiện tranh cãi/thương vong.
- **Đa dạng hoá sự kiện**: mỗi tin trong batch nên là một sự kiện/câu chuyện KHÁC NHAU. Tránh việc 2-3 "tin" trong cùng category thực chất chỉ là cùng 1 sự kiện do nhiều báo đưa lại — vậy chỉ tính 1, chọn nguồn tường thuật tốt nhất.
- **Chống trùng với tin cũ (BẮT BUỘC nhúng ĐẦY ĐỦ, không cắt rời từng mục)**: agent điều phối chạy `python3 scripts/add_news.py --recent-titles 20` (rẻ, không đọc cả file — output gồm tiêu đề gần đây của worldNews + usNews + xNews + item các sự kiện) rồi dán **NGUYÊN khối output đó vào prompt của TẤT CẢ 6 subagent** (kể cả agent xNews và agent exercise), kèm dặn "không report lại bất kỳ tin/sự kiện nào đã có trong danh sách này, kể cả dưới tiêu đề/góc nhìn khác, trừ khi có diễn biến MỚI HẲN". Lý do phải nhúng đủ cho mọi agent: lần quét đầu agent xNews/exercise re-report tin mà agent worldNews đã lấy vì chỉ được đưa danh sách rời của mục mình.
- **Cảnh báo dữ liệu thực tế mâu thuẫn**: khi có sự kiện đang tiếp diễn (vd chiến sự, ngừng bắn), agent điều phối phải tóm tắt trạng thái mới nhất đã đăng và dặn agent không đưa tin mâu thuẫn với trạng thái đó (lần đầu có agent đưa tin "ngừng bắn vẫn duy trì" trong khi dữ liệu đã ghi ngừng bắn bị chấm dứt).
- Yêu cầu agent CHỈ trả lời bằng đoạn JSON kết quả (mảng tin của phần đó) — không giải thích dài dòng, để việc gộp kết quả ở agent điều phối rẻ.
- Không bịa link — bỏ tin nếu không chắc `sourceUrl`.
- Gọi các agent này song song trong cùng 1 lượt (không cần tuần tự) để tiết kiệm thời gian, dùng `run_in_background: false` vì cần kết quả ngay để lắp ráp.

Sau khi các agent trả kết quả, session điều phối **tự review từng tin** (đối chiếu ràng buộc chất lượng trên) trước khi gộp — loại tin không đạt, giữ tin tốt. **Ghi mọi tin bị loại vào `logs/loai-tin.md`** kèm lý do (đánh dấu ⭐ + để lên đầu các tin CHỦ ĐỀ THÍCH bị loại — để người dùng rà xem có loại nhầm không), commit cùng bản tin. Rồi gộp toàn bộ JSON con thành 1 file `/tmp/new_items.json` theo đúng format ở dưới, chạy script (script sẽ chặn lần cuối các lỗi máy bắt được).

## Guardrail tự động trong `scripts/add_news.py` (lớp chặn cuối, không tốn token)
Chạy `python3 scripts/add_news.py /tmp/new_items.json` sẽ tự động **CHẶN (raise lỗi, phải sửa JSON rồi chạy lại)** nếu gặp: thiếu field bắt buộc; `category` sai; `date` ngoài khung — kiểm **HAI LỚP** (siết 27/07/2026): cũ hơn 1 ngày so với ngày batch, **VÀ** cũ hơn 1 ngày so với **HÔM NAY theo giờ VN thật**, hoặc ở tương lai. Lớp thứ hai bịt đường lách "tách lô, neo lô A về ngày cũ" — chính cách 3 tin ngày 24/07 lọt vào bản tin 26/07. Gặp lỗi *"cũ hơn 1 ngày so với HÔM NAY"* thì BỎ tin, đừng lùi ngày batch; `sourceUrl` là trang chủ hoặc live-blog/live-updates; URL trùng nhau trong batch; URL đã có sẵn trong `DATA` (tin trùng); status ID X vô lý (quá ngắn hoặc kết thúc nhiều số 0 — nghi bịa); tên exercise/dipEvent (trong `*Updates`) không khớp entry có sẵn; tên sự kiện trong `newDipEvents` trùng/giống sự kiện đã có (Jaccard ≥ 0.6) hoặc thiếu field bắt buộc của sự kiện. Ngoài ra **CẢNH BÁO (in ra, không chặn)**: `sourceName` lạ ngoài danh sách nguồn đã biết; tiêu đề nghi trùng với tin cũ (Jaccard ≥ 0.6); phần nào chưa đủ chỉ tiêu số lượng. Khi script chặn: đọc thông báo, sửa/bỏ tin lỗi trong JSON rồi chạy lại — KHÔNG tự sửa `index.html` bằng tay.

### ⚠️ HAI BẪY khi lô tin trải QUÁ 2 NGÀY (gặp thật phiên tối 25/07/2026 — đọc trước khi nạp)
`MAX_AGE_DAYS = 1` chỉ cho lùi 1 ngày so với `date` batch. Khi một phiên có tin trải 3 ngày (vd tin
23/07 của chủ đề nới-48h + tin 25/07 vừa đăng) thì **KHÔNG có giá trị `date` batch nào nhận được cả
hai** — neo 25/07 thì tin 23/07 bị chặn "quá cũ", neo 24/07 thì tin 25/07 bị chặn "ở TƯƠNG LAI". Phải
**TÁCH THÀNH NHIỀU LÔ**, mỗi lô neo `date` riêng (lô A `date=24/07` cho tin 23–24/07, lô B `date=25/07`
cho tin 25/07), chạy `add_news.py` lần lượt — script cộng dồn an toàn, `generatedAt` lấy theo lô CHẠY
SAU CÙNG nên để lô ngày mới nhất chạy cuối.

⛔ **TỪ 27/07/2026 TÌNH HUỐNG NÀY GẦN NHƯ KHÔNG CÒN — và tách lô KHÔNG còn dùng để lấy tin cũ được.**
Khung tin giờ là hôm nay + hôm qua tính theo **ngày VN thật**, nên một lô hợp lệ trải tối đa 2 ngày,
mà 2 ngày thì một `date` batch duy nhất đã nhận hết. Tách lô chỉ còn ý nghĩa khi phiên chạy vắt qua nửa
đêm. Neo lô về ngày cũ hơn để nhét tin 2+ ngày tuổi thì `add_news.py` chặn thẳng ở lớp kiểm thứ hai —
đó chính là lỗ hổng đã cho 3 tin ngày 24/07 vào bản tin tối 26/07 (Huy phát hiện qua file Word).

**BẪY 1 — tách lô làm rơi tin khỏi file Word gửi email.** `add_news.py` đặt `_addedDate` = **ngày neo
lô** (không phải ngày chạy), còn `.github/scripts/make_docx.py` lọc **CỨNG** `_addedDate == generatedAt
or date == generatedAt` (hàm `today_items`, **KHÔNG có fallback** — khác `send-email.js` có bù bằng tin
mới nhất). Hệ quả: tin của lô neo ngày cũ **rơi sạch khỏi file .docx đính kèm email**, người đọc mất
gần hết bản tin dù web vẫn hiện đủ. → Sau khi nạp xong TẤT CẢ các lô, **patch `_addedDate` của mọi tin
vừa nạp về ngày phiên** (= `generatedAt`) rồi mới commit. Kiểm nhanh:
```
python3 - <<'PY'
import json,pathlib
h=pathlib.Path('index.html').read_text(encoding='utf-8')
i=h.index('var DATA = ')+len('var DATA = '); d=0; j=i
while True:
    if h[j]=='{': d+=1
    elif h[j]=='}':
        d-=1
        if d==0: break
    j+=1
D=json.loads(h[i:j+1]); g=D['generatedAt']
for k in ('worldNews','usNews'):
    print(k, sum(1 for x in D[k] if x.get('_addedDate')==g), 'tin co _addedDate ==', g)
PY
```
Số này phải khớp số tin thực nạp trong phiên; lệch là có lô bị neo ngày cũ, phải patch.

**BẪY 2 — guardrail KHÔNG bắt trùng SỰ KIỆN, chỉ bắt trùng URL và tiêu đề Jaccard ≥ 0.6.** Cùng một
sự kiện nhưng khác nguồn + khác cách quy đổi số liệu thì **lọt cả hai lớp**: thực tế 25/07 nạp trùng
"Úc rót thêm **4,6 tỷ AUD** cho xưởng tàu ngầm AUKUS Osborne" trong khi DATA đã có "Australia đầu tư
thêm **3,2 tỷ USD** cho chương trình tàu ngầm hạt nhân AUKUS" (cùng số tiền, khác đơn vị → Jaccard
thấp), và trùng CoAspire/CHAOS 70 triệu USD giữa Defense Daily và Naval News. → Sau khi nạp, **grep từ
khoá RIÊNG của từng tin** (tên khí tài, tên chương trình, địa danh, con số) trong `index.html` để kiểm
chéo, đừng chỉ tin dòng OK của script:
```
grep -o '"title":"[^"]*"' index.html | grep -i "<tu khoa>"
```
Ra 2 dòng cùng sự kiện → xoá bản mới bằng `python3 scripts/prune_news.py <file_urls.txt>` (1 URL mỗi
dòng). **KHÔNG sửa tay `index.html`.** Ghi tin đã xoá vào `logs/loai-tin.md` kèm lý do.

**BẪY 3 — commit `index.html` NHIỀU LẦN trong một phiên làm file Word mất tin** (gặp thật 25/07/2026,
đã vá). `.github/scripts/make_docx.py` dựng docx bằng **diff `index.html` với `HEAD~1`**, không phải
"tin của hôm nay". Phiên tối 25/07 commit checkpoint `log: checkpoint 15:32Z da nap 14 tin` (22:23) đã
kèm luôn `index.html` chứa 12 tin lô đầu; commit bản tin thật (22:41) vì thế chỉ diff ra **3 tin** →
email đính kèm docx 3/15 tin, mất sạch mục CNQS Mỹ và Mali. Fallback cũ chỉ chạy khi diff RỖNG HẲN nên
không cứu. Hai lớp phòng, làm cả hai:
- **Script (đã vá):** `pick_items()` lấy **HỢP** của `diff_new` và `today_items` thay cho diff đơn thuần
  → đúng cả khi commit nhiều lần lẫn khi lô neo `_addedDate` ngày cũ.
- **Quy trình:** checkpoint giữa phiên **chỉ `git add logs/`**, `index.html` chỉ vào commit cuối
  `Cap nhat ban tin ...`. Xem Bước 0 trong `.claude/skills/quet-tin/SKILL.md`.

Kiểm nhanh docx sẽ có bao nhiêu tin TRƯỚC khi push (cần `pip install python-docx`):
```
python3 .github/scripts/make_docx.py
```
In ra `DOCX=<đường dẫn>`; mở đếm mục — số tin phải khớp số tin thực nạp trong phiên.

## Quy trình mỗi lần quét (tối ưu token — QUAN TRỌNG)
`index.html` nặng ~170KB. **TUYỆT ĐỐI KHÔNG dùng tool Read để đọc toàn bộ `index.html`.**

1. Kiểm tra ngày cập nhật gần nhất bằng grep: `grep -oE '"generatedAt":"[^"]+"' index.html | head -1`
2. Kiểm tra tần suất nguồn đã dùng bằng grep: `grep -oE '"sourceName":"[^"]+"' index.html | sort | uniq -c | sort -rn`
2b. Lấy tiêu đề gần đây để chống trùng: `python3 scripts/add_news.py --recent-titles 20`
3. Giao việc cho 6 agent Sonnet theo bảng kiến trúc ở trên, mỗi agent tự áp dụng thứ tự ưu tiên nguồn + ưu tiên RSS (dùng URL RSS đã chốt sẵn ở bảng dưới nếu có), nhúng NGUYÊN khối danh sách tiêu đề gần đây (bước 2b) + ràng buộc chất lượng + quy tắc đa dạng hoá sự kiện vào prompt MỖI agent.
4. Gộp kết quả các agent thành 1 file JSON, ví dụ ghi bằng heredoc vào `/tmp/new_items.json`, format:
   ```json
   {
     "date": "YYYY-MM-DD",
     "worldNews": [ {...} ],
     "usNews": [ {...} ],
     "xNews": [ {...} ],
     "exerciseUpdates": [ {"name": "<tên đúng đã có trong DATA>", "items": [ {...} ]} ],
     "dipEventUpdates": [ {"name": "<tên đúng đã có trong DATA>", "items": [ {...} ]} ],
     "newDipEvents": [ {"name":"...","status":"recent","dates":"...","location":"...","scale":"...","summary":"...","items":[ {...} ]} ],
     "rejectedNews": [ {"date":"...","category":"...","title":"...","summary":"...","sourceName":"...","sourceUrl":"...","region":"...","reason":"<lý do loại>"} ]
   }
   ```
5. Chèn vào `index.html` bằng script có sẵn, KHÔNG dùng Edit/Write trực tiếp lên `index.html`:
   `python3 scripts/add_news.py /tmp/new_items.json`
   Script tự động chèn tin + cập nhật ngày + validate + guardrail (xem mục "Guardrail tự động" ở trên để biết các lỗi bị CHẶN vs CẢNH BÁO). Nếu script chặn, sửa/bỏ tin lỗi trong JSON rồi chạy lại — không tự sửa `index.html` bằng tay.
   - **KIỂM TRA SÀN CỨNG TỔNG NGÀY:** dòng cuối script in `SÀN CỨNG TỔNG NGÀY … worldNews X/15 · usNews Y/15` (đếm tin `_addedDate == hôm nay`, gộp cả phiên sáng + tối). Xử lý theo phiên:
     - **Phiên SÁNG:** nhắm ~10/mục là đủ, KHÔNG cần lặp tới 15 — để tối bù. Đạt ~10 thì dừng.
     - **Phiên TỐI (và mọi phiên khi phiên kia đã SKIP/FAIL):** nếu mục nào **< 15**, **giao thêm agent Sonnet bổ sung** riêng mục đó (chỉ rõ category còn thiếu + nguồn/góc CHƯA khai thác — dư địa bù là CNQS/Ngoại giao/Kinh tế us + điều trần/bỏ phiếu thông qua dự luật; KHÔNG nới lại nội bộ Mỹ để lấp), chạy lại script. **LẶP cho tới khi script in `✅ ĐẠT SÀN NGÀY`.** Script cộng dồn an toàn. Chỉ dừng khi đạt sàn HOẶC đã ≥3 vòng bổ sung mà thật sự cạn tin sạch (ghi rõ log + tóm tắt).
6. Commit theo mẫu: `Cap nhat ban tin DD/MM: +N tin (TG +x, My +y, X +z)`, push vào `main`.
7. Tóm tắt cuối cùng: ngắn gọn — tổng số tin từng phần, bảng phân bổ category, phần nào thiếu chỉ tiêu (nếu có), trạng thái push. Không liệt kê lại toàn bộ nội dung từng tin.

## Đánh giá lại chiến lược quét
✅ **Đã làm 22/07/2026** — verify toàn bộ bảng RSS bằng fetch thật (xem mục "URL RSS" ở trên): sửa 3 URL
sai (Nikkei, VnEconomy, Dân Trí), bỏ 4 nguồn chặn/chết (NATO, USNI, Politico, Al Arabiya), hạ ưu tiên
Fortune (feed đứng 5 ngày). Công cụ: `python3 scripts/rss_check.py`.

**Lần đánh giá tới — vào hoặc sau 22/08/2026** (1 tháng):
- Chạy lại `scripts/rss_check.py`; URL nào hỏng thì sửa hoặc chuyển sang WebSearch ngay trong bảng.
- Nguồn nào tin trùng lặp/nhiễu, không đúng gu → hạ ưu tiên. Nguồn nào chưa từng đóng góp tin nào
  vào bản tin (`grep -oE '"sourceName":"[^"]+"' index.html | sort | uniq -c`) → cân nhắc bỏ.
- Xem lại 2 nguồn Báo Mới: chuyên mục nào cho ứng viên tốt, tỷ lệ được chọn/bị loại thế nào.

## ~~Chu kỳ bản tin: 2 lần/ngày~~ — ⚠️ LỖI THỜI 2026-07-23: giờ CHỈ 1 lần/ngày buổi TỐI 22:00 (dự phòng 23:00), xem banner đầu file
Mỗi mốc là MỘT chu kỳ khép kín, 3 nguồn nạp nối tiếp nhau rồi ra **một bản tin hợp nhất**:

| Giờ VN | Ai chạy | Việc |
|---|---|---|
| **08:00** / 20:00 | Action `import-news-from-drive.yml` | Nạp file `ban-tin-chien-luoc-*.json` từ Drive vào `DATA` |
| **08:05** / 20:05 | Action `sync-baomoi.yml` | `baomoi-saved.json` (bài đã lưu) + `baomoi-topics.json` (ứng viên quét chuyên mục) |
| **10:15** / 20:15 | Scheduled task local `web-scan` (7+1 agent Sonnet) | Quét web + nạp Báo Mới vào `DATA` → publish |
| 11:15 / 21:15 | Scheduled task local `web-scan` (dự phòng) | Chỉ chạy nếu mốc chính chết; cờ `state.json` làm nó tự no-op khi đã xong |

**VÌ SAO Drive + Báo Mới chạy TRƯỚC phiên quét** (chứ không phải quét xong mới gộp): chống trùng chỉ chạy một chiều — phiên quét đọc `--recent-titles` + URL đã có trong `index.html` nên né được tin Drive/Báo Mới vừa nạp; ngược lại thì không. Đặt 2 nguồn kia trước thì bản tin sạch trùng hơn, kết quả cuối vẫn là một bản tin gộp, deploy một lần.

Cờ idempotent theo pipeline (xem mục dưới): `drive-import` và `web-scan`.

**Cờ idempotent nằm ở `logs/state.json`, KHÔNG phải `DATA.generatedAt`.** `generatedAt` là *ngày bản tin hiển thị trên web* — dùng nó làm cờ chạy việc thì Action Drive nhập lúc 08:00 sẽ bump nó và làm routine quét tối SKIP vĩnh viễn (đã xảy ra 20–21/07: `xGeneratedAt` kẹt ở 19/07, tập trận/sự kiện ngoại giao không ai cập nhật). Mỗi pipeline giờ có dòng riêng, chỉ tự chặn CHÍNH NÓ.

```
python3 scripts/state.py claim web-scan     # giành KHOÁ + kiểm tra: 0=quét đi · 10=xong rồi · 11=đang chạy
python3 scripts/state.py beat  web-scan     # nhịp tim — gọi ở MỖI checkpoint, nếu không khoá tự hết hạn
python3 scripts/state.py done  web-scan "+12 tin (TG+5, My+5, X+2)"
python3 scripts/state.py fail  web-scan "session limit"    # FAIL/SKIP nhả khoá, KHÔNG chặn lần fire sau
python3 scripts/state.py show                              # xem cả 2 pipeline, cả 2 buổi, trạng thái khoá
```
Chỉ `done` mới đẩy `lastSuccess[buổi]` → chỉ khi thật sự nạp được tin mới chặn lần fire kế tiếp; `fail`/`skip` để lần sau quét lại.

### 🔒 PHIÊN TEST HẠ TẦNG KHÔNG ĐƯỢC ĐỤNG CỜ THẬT — `DIEMTIN_PHIEN_TEST=1` (vá 29/07/2026)
**Sự cố thật tối 29/07:** nhánh `MODE=test` của `claude-web-scan.yml` (phiên "PHIEN TEST HA TANG CI",
quét nhẹ 1 agent) gọi `state.py done web-scan` lúc **17:34** và chiếm ô khoá `toi` của cả ngày. Commit
của nó rơi **ngoài khung giờ gửi** (cổng 2 của `notify-email.yml` đòi ≥20:30) nên không kích
email/Telegram. Hậu quả dây chuyền: CI 21:00 · local 21:15 · CI 22:00 đều nhận **exit 10** rồi SKIP —
**cả ba lớp im lặng, không lớp nào báo hỏng, mà bản tin tối suýt mất trắng.** Chỉ cứu được vì phiên
local 21:15 quét đè lên cờ (gửi 21:34); canary 22:45 có kêu nhưng đã quá hạn 22:00.

**Cơ chế vá:** workflow đặt `DIEMTIN_PHIEN_TEST: ${{ inputs.mode == 'test' && '1' || '0' }}` ở tầng
`env:` của step quét → `claude -p` và mọi lệnh Bash con thừa hưởng → `state.py` chuyển toàn bộ đường
ghi sang `logs/state-test.json` (đã `.gitignore`).
| | |
|---|---|
| Phiên test vẫn làm được | trọn pipeline `claim → beat → done`, ghi vào sổ riêng — nghiệm thu hạ tầng không mất giá trị |
| Phiên test KHÔNG làm được | chiếm ô khoá thật · ghi `RUNNING`/khoá lên `logs/state.json` |
| Phiên test VẪN đọc cờ thật | để nhường phiên THẬT đang chạy (**exit 11**) — bỏ chốt này là mở đường quét chồng |
| Phiên test KHÔNG bao giờ | **exit 10** vì bản tin thật đã xong — test phải chạy lại được bất kể giờ nào |

⚠️ **Ý ĐỊNH KHAI BẰNG LỜI, không suy từ `MODE`/tên workflow/giờ chạy** — cùng lỗi đã vấp với `tu_dong=1`
(suy từ `event_name == 'push'`) và `TELEGRAM_BAT_BUOC` (suy từ số secret còn lại). **Mặc định là phiên
THẬT**: quên đặt biến thì hành vi y như cũ, không tạo vùng câm mới.
⚠️ `STATE_LOGS_DIR` là seam **CHỈ dành cho bộ test** (ghim thư mục logs vào chỗ tạm) — vận hành thật
tuyệt đối không đặt.
⚠️ **Vá gốc này KHÔNG bịt hết** — đường **bấm tay `workflow_dispatch` mode=normal giữa ngày** vẫn `done`
và chiếm ô khoá y như cũ, mà commit của nó cũng rơi ngoài khung giờ gửi. Thứ bắt được ca đó là **phép
kiểm sổ đã gửi khi gặp exit 10**: `docs/routine-web-scan.md` mục "PHIÊN TỐI" điều 3 (bản local) và
`.github/prompts/web-scan-ci.md` BƯỚC 1 (bản CI, có thêm chốt "lastRunAt < 20 phút thì SKIP êm" để khỏi
kêu oan lúc `notify-email.yml` còn đang chạy). Đừng gỡ phép kiểm đó vì "đã vá gốc rồi".
Bộ test canh: `tests/test-cong-phien-test.py` (11 ca · `--tu-kiem` bắt được 5/5 bản hỏng).

**Khoá chống chạy chồng (thêm 22/07/2026).** Mốc chính và mốc dự phòng cách nhau đúng 60 phút mà một
phiên quét mất ~60 phút → `check` (chỉ biết ĐÃ XONG hay chưa) để lần fire dự phòng khởi động phiên THỨ
HAI song song: hai phiên cùng quét, cùng push, tốn token đôi, đụng nhau lúc rebase. `claim` giữ khoá,
`done/skip/fail` nhả khoá.
Khoá dùng **heartbeat** chứ không phải hạn giờ cứng — phiên chết mà khoá không tự mở thì còn tệ hơn
không có khoá (mất luôn bản tin của buổi đó). Không có nhịp nào trong `LOCK_STALE_MIN` = 30 phút →
coi phiên đã chết, phiên mới giành được khoá. Biết chắc phiên cũ đã chết thì `claim --force`.
