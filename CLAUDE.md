# Điểm Tin Thế Giới — quy tắc quét tin

Trang tin tĩnh (PWA) tiếng Việt, deploy tự động lên GitHub Pages khi push vào `main`.

## 📚 FILE NÀY ĐÃ XẺ 06/08/2026 — nhật ký vá lỗi nằm ở `docs/`, không mất chữ nào

**Vì sao:** file này được nạp lại ở **MỌI lượt của MỌI phiên** đụng repo — phiên local, phiên CI
(`claude -p` trong `claude-web-scan.yml`), phiên bot Telegram, phiên remote. Đo thật 06/08/2026:
**317.442 byte ≈ 99.000 token mỗi lượt**, mà một phiên quét có hàng chục lượt cộng nhiều subagent.
Phần lớn dung lượng là **nhật ký vá lỗi** — chỉ cần đọc khi đụng đúng mảng đó, không phải mỗi lượt.
Sau khi xẻ: **103 KB ≈ 32.000 token** (giảm 68%). **Không dòng nào bị xoá** — đã đối chiếu đủ 2.636
dòng khác rỗng của bản gốc, và 24 bộ test cho kết quả y hệt trước khi xẻ.

| File | Chứa gì |
|---|---|
| [`docs/luat-gui-ban-tin.md`](docs/luat-gui-ban-tin.md) | email · Telegram · sổ đã gửi · canary · cổng kích notify · `ghi_so_push.py` · Mali sang bản sáng |
| [`docs/luat-bot-telegram.md`](docs/luat-bot-telegram.md) | bot hỏi–đáp · lịch sử chat · `/xoa` · quét kênh Telegram · học từ người đọc |
| [`docs/luat-tin-jaylam.md`](docs/luat-tin-jaylam.md) | đường nhận `.docx` + vai BỘ LỌC của file Jay Lâm gửi |
| [`docs/luat-think-tank.md`](docs/luat-think-tank.md) | kho `data/analyses.json` · feed viện · các phép đo nguồn thiếu · nhãn `outlet` |
| [`docs/luat-chu-de.md`](docs/luat-chu-de.md) | cổng chủ đề 2 (Úc & Biển Đông) · Báo Mới truy ngược · bẫy lô tin · phiên test |
| [`docs/luat-test-cong.md`](docs/luat-test-cong.md) | bảng 24 bộ test + luật `--tu-kiem` + các bẫy khi dựng bản hỏng |
| [`docs/nhat-ky-nguon.md`](docs/nhat-ky-nguon.md) | trang nào lấy bằng cách gì · các lần đo/đảo lại nhãn nguồn |
| [`docs/luat-lich-su.md`](docs/luat-lich-su.md) | mục LỖI THỜI (sàn 15+15, chu kỳ cũ, kiến trúc 8 agent) · Drive import · tab Cà phê |

⚠️ **FILE NÀY VẪN LÀ CẤU HÌNH, KHÔNG PHẢI CHỈ LÀ CHỮ.** `harvest.py` · `rss_check.py` ·
`probe_sources.py` đọc khối mục **URL RSS** → `##` kế tiếp; `harvest.py` còn đọc bảng
`🕸️ TRANG HTML QUÉT TRỰC TIẾP`. **Mọi dòng bảng có URL trong hai chỗ đó phải ở lại đây** — xẻ tiếp
thì chỉ được chuyển VĂN XUÔI. Số phải khớp sau mỗi lần sửa: **83 feed · 31 trang (CI) · 25 (local)**.
```
python3 tests/test-bang-nguon-claude-md.py               # phải 14/14
python3 tests/test-bang-nguon-claude-md.py --tu-kiem     # phải bắt 6/6 bản hỏng
```

⛔ **CHÍNH LƯỢT XẺ NÀY ĐÃ KÍCH HOẠT MỘT LỖ CÂM — kể lại để đừng dựng lại.** Câu dặn ngay trên có
nhắc chuỗi `##` + `URL RSS` liền nhau; `feeds_from_claude_md` khi đó còn dùng `text.index("## URL
RSS")` **thô**, nên nó cắt trúng câu văn ở ĐẦU file thay vì cắt ở bảng thật ⇒ **0 feed**, lớp
`[RSS]` chết sạch. Không lỗi, không cảnh báo, bảng vẫn nguyên 114 dòng nên soi bằng mắt thấy đủ —
và `tests/test-bang-nguon-claude-md.py` **vẫn xanh 13/13** vì mọi ca của nó dựng trên dữ liệu giả,
không ca nào đo file thật. Đây ĐÚNG con lỗi đã vá cho bảng HTML hồi 30/07 (`_vi_tri_tieu_de`) —
hôm đó **chỉ vá một nửa**, lớp RSS bị bỏ quên suốt từ đó.
- **Đã vá gốc:** cả ba script nay neo vào **DÒNG TIÊU ĐỀ** qua `harvest._vi_tri_tieu_de`, dùng
  CHUNG một hàm (`rss_check.py`/`probe_sources.py` import từ `harvest`, không chép sang).
- **Đã có răng:** ca **[14]** + một bản hỏng riêng trong `--tu-kiem`. Ca dùng **ngưỡng tuyệt đối**
  (`> 50 feed`) chứ không so hai phía — vì file thật NAY đã chứa câu nhắc, nên phép so tương đối
  sẽ cùng về 0 ở cả hai phía và ĐẠT oan, mất răng y hệt ca 3.
- **Bài học:** bộ test chỉ chạy trên dữ liệu giả thì không biết file thật đã hỏng. Sau khi sửa
  CLAUDE.md, ngoài chạy test còn phải **đếm trên chính file thật** — đó là lý do có 3 con số ở trên.
⚠️ **Thêm mục mới thì cân nhắc viết thẳng vào `docs/` rồi để một dòng trỏ ở đây**, đừng mặc định
bồi vào file này — mỗi KB thêm vào đây là một khoản thu mỗi lượt của mọi phiên, còn `docs/` chỉ
tốn khi có người mở ra đọc.

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

## 📵 ĐÃ TẮT EMAIL — TELEGRAM LÀ KÊNH DUY NHẤT (chỉ thị Huy 27/07/2026)

> Nguyên văn: *"từ giờ không cần gửi email cho ai nữa, gửi telegram thôi."*

Cơ chế: biến **`GUI_EMAIL: '0'`** đặt trong cả `notify-email.yml` lẫn `notify-morning.yml`; hai script
JS đọc biến này và bỏ khâu `sendMail`. **Bật lại = đổi thành `'1'`**, không phải dựng lại gì.

⚠️ **Chỗ đặt lệnh bỏ qua KHÁC NHAU ở hai script — cố ý, đừng "cho gọn":**
| Script | Thoát ở đâu | Vì sao |
|---|---|---|
| `send-email.js` | **ngay đầu `main()`** | không có tác dụng phụ nào Telegram cần |
| `send-morning-email.js` | **ngay TRƯỚC `sendMail`** | payload Telegram sáng được ghi ngay phía trên, và đây là chỗ DUY NHẤT biết "hôm nay có gì mới" — thoát sớm là **Telegram sáng chết theo** |

Kèm: `send-morning-email.js` chỉ bắt buộc secret `EMAIL_USER/PASS` khi `GUI_EMAIL != '0'`, để sau này
gỡ hẳn secret email khỏi repo thì Telegram sáng vẫn chạy.

⚠️ **Đã BỎ `continue-on-error` ở CẢ HAI bước gửi Telegram.** Trước đây nuốt lỗi vì email gánh chính;
nay Telegram là kênh duy nhất nên hỏng phải làm job **ĐỎ** — không để Huy mất bản tin trong im lặng.

Nghiệm thu thật trên CI 27/07 (run 30250819712): `GUI_EMAIL=0 — BỎ QUA gửi email` + `Đã gửi 2 message
+ file .docx` tới cả 2 chat.

> 📄 **⛔ "THIẾU SECRET → THOÁT ÊM" ĐÃ BỎ (siết 27/07/2026) — thiếu secret nay là job ĐỎ** → [`docs/luat-gui-ban-tin.md`](docs/luat-gui-ban-tin.md) — thiếu secret Telegram = job ĐỎ; luật ở `tg_api.kiem_cau_hinh()`

## ⚠️ HAI PHIÊN QUÉT + HAI EMAIL (chốt 24/07/2026 — GỘP NƠI KÍCH 28/07/2026)
> **28/07/2026 (chỉ thị Huy: *"sự kiện sáng thì quét gộp với quét tin 4h sáng cũng được"*):**
> pipeline `event-scan` KHÔNG còn là phiên quét riêng — nó chạy NGAY SAU bản tin 5 chủ đề, trong
> CÙNG session của phiên SÁNG SỚM. Còn **2 lần quét thật/ngày** (tối + sáng sớm), không phải 3.
> `claude-event-scan.yml` đã XOÁ; task local `event-scan-diem-tin` đã TẮT. Nhưng **khoá/commit/
> email của hai pipeline vẫn TÁCH RIÊNG như cũ** — chỉ nơi kích (session nào gọi) là gộp lại, xem
> `docs/routine-web-scan.md` Bước 4 + `.github/prompts/web-scan-ci.md` BƯỚC 6.
- **Bản tin (TỐI 20:47 + SÁNG SỚM 03:47)** — CI `claude-web-scan.yml` là mốc chính (tối 20:47 + vét 21:47, sáng sớm 03:47/04:47 VN), local dự phòng CẢ HAI phiên bằng **2 task tách riêng**: `web-scan-diem-tin` (sáng 04:30/05:30) và `web-scan-diem-tin-toi` (tối 21:15): 5 chủ đề (xem banner trên). Commit
  `Cap nhat ban tin ...` → `notify-email.yml` gửi **email tối** (tiêu đề điểm tin + .docx đính kèm).
- **Phiên SÁNG (event-scan)** — chạy NGAY SAU bản tin 5 chủ đề, trong CÙNG job/session của phiên
  SÁNG SỚM ở trên (CI `claude-web-scan.yml` 03:47/04:47 + local `web-scan-diem-tin` 04:30/05:30 —
  không còn mốc CI/local riêng). Quy trình: **`docs/routine-web-scan.md` Bước 4** (nguồn sự thật
  duy nhất — `docs/routine-event-scan.md` chỉ còn là stub trỏ sang đó). CHỈ quét **sự kiện ngoại
  giao có ký kết + cập nhật tập trận + tin liên quan + 4–6 BÀI THINK-TANK** (mục 4 phần "Nơi lưu
  dữ liệu"). **Chủ nhật** chạy thêm **agent OPUS** viết **báo cáo tuần Mỹ-Trung-Nga**
  (`weekly_context.py` → agent Opus → `add_weekly.py` ghi `DATA.weeklyReport`). Idempotent: `state.py …
  event-scan` — vẫn `claim`/`done` RIÊNG với `web-scan`, và **commit RIÊNG** (không gộp vào commit
  bản tin) tiền tố `Cap nhat su kien ...` (hoặc `Dang bao cao tuan ...` nếu chỉ có báo cáo) — job CI
  tự dò cả hai commit mới trong cùng lần chạy để kích đúng notify tương ứng (xem bước "Kích
  email/push/morning" trong `claude-web-scan.yml`).
- **Email SÁNG** — `notify-morning.yml` bắt 2 tiền tố commit trên, so diff với commit trước (HEAD~1) để
  biết sự kiện/tập trận mới + báo cáo tuần mới, gửi **1 email gộp** cho lamgiaphat1603 (`send-morning-email.js`).
  Không có gì mới thì không gửi. Báo cáo tuần hiển thị ở tab **Phân tích → mục con "Báo cáo tuần"**.
  **⚠️ Subject email này ĐỔI 27/07/2026 (chỉ thị Huy): `🎖️ Sự kiện & Tập trận DD/MM — …`**, bỏ hẳn tên cũ
  `🌏 Bản tin sáng …`. Lý do: tên cũ trùng chữ với bản tin 5 chủ đề phiên sáng sớm (`📰 Điểm Tin Thế Giới
  BUỔI SÁNG …`) nên nhìn hộp thư không phân biệt được hai email khác hẳn nhau về nội dung. Quy tắc chung:
  **email này gọi theo NỘI DUNG (sự kiện/tập trận), email bản tin gọi theo BUỔI** — đừng đặt tên hai cái
  cùng chứa chữ "sáng", và giữ emoji khác nhau (🎖️ vs 📰) để liếc là ra.

> 📄 **📩 EMAIL TỐI GỒM NHỮNG GÌ (chỉ thị Huy 27/07/2026 — quy tắc chốt)** → [`docs/luat-gui-ban-tin.md`](docs/luat-gui-ban-tin.md) — bản tối = tin cả ngày TRỪ ca sáng sớm / tập trận-sự kiện / think-tank

> 📄 **⛔ BẢN TỐI LẶP NGUYÊN SI TIN CA SÁNG — luật có mà KHÔNG ai thi hành (vá 01/08/2026)** → [`docs/luat-gui-ban-tin.md`](docs/luat-gui-ban-tin.md) — `loc_bo_tin_ca_sang` + sổ đã gửi; vì sao tắt email làm luật mất người thi hành

> 📄 **🟤 MALI RỜI FILE WORD, SANG BẢN SÁNG (chỉ thị Huy 05/08/2026)** → [`docs/luat-gui-ban-tin.md`](docs/luat-gui-ban-tin.md) — Mali rời `.docx`, sang bản sáng 🎖️ Sự kiện & Tập trận

> 📄 **🔀 HAI WORKFLOW GHI CÙNG SỔ CÁCH 07 GIÂY — luật hợp nhất ở `ghi_so_push.py` (vá 30/07/2026)** → [`docs/luat-gui-ban-tin.md`](docs/luat-gui-ban-tin.md) — sổ append-only: ĐỪNG `pull --rebase`; kèm cổng `kiem_luat_push.py`

> 📄 **⛔ CHỈ PHIÊN TỰ NẠP MỚI ĐƯỢC KÍCH NOTIFY — cờ tường minh, không dò `git log` (vá 31/07/2026)** → [`docs/luat-gui-ban-tin.md`](docs/luat-gui-ban-tin.md) — cờ tường minh `ghi_co_da_nap`, không dò `git log`

> 📄 **🆕 Mới trên web + 💡 Có thể bạn chưa biết — trong email SÁNG (chỉ thị Huy 27/07/2026)** → [`docs/luat-gui-ban-tin.md`](docs/luat-gui-ban-tin.md) — hai mục cuối email sáng (`whats-new.json`) + GIAO DIỆN mẫu 4 Digest tối giản

> 📄 **Tab "Cà phê" (ngoài chủ đề tin — thêm 24-25/07/2026)** → [`docs/luat-lich-su.md`](docs/luat-lich-su.md) — ngoài chủ đề tin — tab ☕ tìm quán cà phê HN

## 📨 TELEGRAM — kênh gửi thứ hai + lớp nguồn thứ ba (thêm 27/07/2026, chỉ thị Huy)

> 📄 **Gửi bản tin qua Telegram** → [`docs/luat-gui-ban-tin.md`](docs/luat-gui-ban-tin.md) — `send_telegram.py`, giãn dòng `chunk()`, secret, `curl` thay `urllib`

> 📄 **📤 GỬI TAY MỘT BẢN TIN CHO HUY: ĐI BẰNG BOT ĐIỂM TIN, KHÔNG PHẢI BOT CÁ NHÂN (Huy chốt 01/08/2026)** → [`docs/luat-gui-ban-tin.md`](docs/luat-gui-ban-tin.md) — bản tin đi bằng `@diemtin24h_bot`, gửi cho CẢ danh sách chat

> 📄 **🐤 CANARY — báo khi bản tin KHÔNG tới nơi (thêm 27/07/2026, chỉ thị Huy)** → [`docs/luat-gui-ban-tin.md`](docs/luat-gui-ban-tin.md) — 3 ca cron, kiểm ĐẦU RA chứ không kiểm quy trình

> 📄 **Bot hỏi–đáp qua Telegram (thêm 27/07/2026 — "option 3", chạy MIỄN PHÍ)** → [`docs/luat-bot-telegram.md`](docs/luat-bot-telegram.md) — cron 5 phút, 2 bước DATA + nghiên cứu, độ trễ thật 66–148 phút

> 📄 **🧠 Bot nhớ lịch sử chat gần đây (thêm 28/07/2026, Huy hỏi)** → [`docs/luat-bot-telegram.md`](docs/luat-bot-telegram.md) — `lich_su_gan_day`, `nhin_truoc_kich_bot.py`, lệnh `/xoa`, canary chỉ nhắn chat chủ

> 📄 **Học từ câu hỏi người đọc (thêm 27/07/2026, chỉ thị Huy)** → [`docs/luat-bot-telegram.md`](docs/luat-bot-telegram.md) — phân loại lượt hỏi, `dt_bot_hoi`, hồ sơ độc giả + CHỈ THỊ GỐC 27/07 về chat Jay Lâm

> 📄 **⛔ TIN MỚI PHẢI XẾP VÀO MỤC CÓ SẴN — TẠO MỤC MỚI PHẢI HỎI HUY TRƯỚC** → [`docs/luat-chu-de.md`](docs/luat-chu-de.md) — bảng mục có sẵn; tạo mục mới phải hỏi Huy

> 📄 **⛔ MỤC "ÚC VÀ BIỂN ĐÔNG" TỪNG LÀ THÙNG CHỨA MỌI TIN THẾ GIỚI — ĐÃ VÁ 02 TẦNG 01/08/2026 (Huy bắt cùng ngày)** → [`docs/luat-chu-de.md`](docs/luat-chu-de.md) — vá 02 tầng: `check_neo_chu_de_2` + `la_uc_bien_dong`

> 📄 **🔄 ĐẢO NGUYÊN TẮC 01/08/2026 — FILE JAY LÂM GỬI LÀ **BỘ LỌC**, KHÔNG PHẢI NGUỒN TIN** → [`docs/luat-tin-jaylam.md`](docs/luat-tin-jaylam.md) — file Jay Lâm là BỘ LỌC, không phải nguồn tin

> 📄 **📎 ĐƯỜNG NHẬN: Jay Lâm gửi file .docx qua bot → `dt_jaylam_inbox` (dựng 30/07/2026)** → [`docs/luat-tin-jaylam.md`](docs/luat-tin-jaylam.md) — `dt_jaylam_inbox`, `docx_text.py`, trần độ dài

> 📄 **📤 BẢN SAO FILE PHẢI VỀ THẲNG CHAT CỦA HUY TRÊN TELEGRAM (chỉ thị Huy 30/07/2026)** → [`docs/luat-tin-jaylam.md`](docs/luat-tin-jaylam.md) — `gui_ban_sao_cho_chu`, đặt TRƯỚC bước tải

> 📄 **⛔ FILE DO CHÍNH HUY GỬI KHÔNG PHẢI TIN — không vào hàng chờ (30/07/2026)** → [`docs/luat-tin-jaylam.md`](docs/luat-tin-jaylam.md) — `_la_chat_chu`, so BẰNG chứ không so chuỗi con

> 📄 **📜 ĐÃ XOÁ 01/08/2026 — toàn bộ thiết kế "mục 5 Tin Jay Lâm gửi"** → [`docs/luat-tin-jaylam.md`](docs/luat-tin-jaylam.md) — di sản mục 5 đã bỏ — 3 bài học còn hiệu lực

> 📄 **Quét tin từ kênh Telegram** → [`docs/luat-bot-telegram.md`](docs/luat-bot-telegram.md) — `telegram_harvest.py`, 4 cái bẫy, đường MTProto

> 📄 **🧪 TEST CỔNG KIỂM — `tests/` (dựng 29/07/2026, áp luật mục 17 CLAUDE.md toàn cục)** → [`docs/luat-test-cong.md`](docs/luat-test-cong.md) — bảng 24 bộ test + luật `--tu-kiem` + các bẫy khi dựng bản hỏng

## Nơi lưu dữ liệu
Dữ liệu nằm trong `index.html`, biến `var DATA = {...}` (xem mục "Quy trình" bên dưới — KHÔNG đọc trực tiếp file này).

> ⚠️ **NGOẠI LỆ DUY NHẤT: bài think-tank nằm ở `data/analyses.json`** (tách 30/07/2026 — xem mục 4).
> `DATA.analyses` trong `index.html` LUÔN RỖNG; web nạp kho bằng `loadAnalyses()` sau khi trang đã hiện.
> Script Python phải đi qua `scripts/analyses_store.py`, và **mọi commit có nạp think-tank phải
> `git add data/`** — bỏ sót thì bài nạp xong không lên web mà không có lỗi nào.

Các phần liên quan tới quét tin:

### 1. `worldNews` / `usNews` — tin theo chuyên mục
Mảng phẳng, tin mới nhất ở đầu. Mỗi tin:
```json
{"date":"YYYY-MM-DD","category":"...","title":"...","summary":"...","sourceName":"...","sourceUrl":"https://...","significance":"...","region":"..."}
```
- `category` (chọn 1): Kinh tế · Chính trị · Công nghệ quân sự · Ngoại giao
- `region` (chỉ tin thế giới, không bắt buộc): Châu Âu/NATO · Trung Đông · Đông Á · Toàn cầu · Châu Mỹ · Ấn Độ Dương - Thái Bình Dương
- Ngày cập nhật: `DATA.generatedAt`, `DATA.worldGeneratedAt`, `DATA.usGeneratedAt`
- **Giờ cập nhật (thêm 24/07/2026)**: `DATA.generatedTime` / `worldGeneratedTime` / `usGeneratedTime` / `xGeneratedTime` — `HH:MM` giờ VN lúc chạy `add_news.py`, ô "Cập nhật" trên web hiện `23-07-26 20:30`. Để RIÊNG chứ không nhét vào `generatedAt` vì `generatedAt` phải giữ đúng dạng `YYYY-MM-DD` (notify-push.yml grep bằng regex ngày; send-email.js + make_docx.py `split('-')` và so với `_addedDate`).

### 2. `xNews` — tin từ X/Twitter
Mảng phẳng, tin mới nhất ở đầu. Mỗi tin:
```json
{"date":"YYYY-MM-DD","handle":"@...","name":"Tên tài khoản","title":"...","summary":"...","significance":"...","url":"https://x.com/..."}
```
Ngày cập nhật: `DATA.xGeneratedAt`. **Danh sách tra cứu chính: [`docs/mangxahoi-chinh-thuc-my.md`](docs/mangxahoi-chinh-thuc-my.md) — 173 handle X đã xác minh của cơ quan chính phủ và uỷ ban Quốc hội Mỹ (chỉ gồm tài khoản được liên kết từ website chính thức). Ngoài ra — loại tài khoản đã dùng trước đây: quan chức/tổ chức chính thức (@NATO, @CENTCOM, @ZelenskyyUa), hãng tin lớn (@Reuters, @AJEnglish, @SkyNews, @CBSNews), tổ chức phân tích/OSINT (@TheStudyofWar, @EU_ISS, @thewarzonewire), nhà báo/chuyên gia uy tín (@BarakRavid, @AndrewSErickson). Ưu tiên tài khoản xác thực (verified/tổ chức chính thức), không lấy tin từ tài khoản vô danh/không rõ nguồn gốc.

### 3. `exercises` (tập trận) / `dipEvents` (sự kiện ngoại giao)
KHÁC với category "Ngoại giao" ở trên — đây là các **sự kiện lớn đang diễn ra** (hội nghị thượng đỉnh, cuộc tập trận đa quốc gia...), mỗi sự kiện là 1 object có `name`, `status` (`ongoing`/`recent`/`upcoming`...), `dates`, `location`, `scale`, `summary`, và một mảng con `items` chứa các tin cập nhật liên quan, mỗi item:
```json
{"date":"YYYY-MM-DD","title":"...","summary":"...","sourceName":"...","sourceUrl":"https://..."}
```
Với **`exercises` (tập trận)**: cập nhật `items` con vào cuộc **đã có** (khớp `name`) qua `exerciseUpdates`; **được phép TẠO cuộc tập trận MỚI** qua `newExercises` (phiên sáng `event-scan` chủ động quét tập trận lớn KHẮP THẾ GIỚI đang/sắp diễn ra — không chỉ Ấn Độ Dương-TBD). Ưu tiên cập nhật `status: "ongoing"`. `dates` ghi dạng CÓ ngày/tháng/năm để web tự suy trạng thái (`effStatus`).

**BỐI CẢNH + KHÁI NIỆM (thông tin nền — cập nhật 25/07/2026):** mỗi cuộc tập trận có thể mang `background` (đoạn Bối cảnh chiến lược, nhiều đoạn ngăn bằng `\n`) + `concepts` ([{term,def}]) — web hiện 2 thẻ **📔 Bối cảnh** + **📚 Khái niệm** dưới mỗi cuộc (hàm `drillBriefing`). Chỉ thị Huy: **TỰ ĐỘNG sinh Bối cảnh khi phát hiện tập trận MỚI, và thêm Bối cảnh cho mọi cuộc ĐANG diễn ra chưa có.** Sinh qua agent rồi ghi bằng `scripts/set_exercise_briefing.py briefing.json` (`[{name,background,concepts}]`). Quy trình routine: xem `docs/routine-event-scan.md` Bước 2b.

Với **`dipEvents` (sự kiện ngoại giao)** — áp dụng từ 11/07/2026 — được phép **tự động TẠO sự kiện mới** cho các sự kiện ngoại giao đáng đưa (dùng field `newDipEvents`), gồm: **ký kết/hiệp định song phương hoặc đa phương** (vd Nhật–New Zealand ký ACSA), **thượng đỉnh / hội nghị cấp cao**, **thăm cấp nguyên thủ/bộ trưởng có kết quả cụ thể**, **sáng kiến/khuôn khổ ngoại giao lớn mới**. KHÔNG tạo sự kiện cho: điện đàm/cuộc gọi thường lệ, phát ngôn đơn lẻ, tin đồn. **TĂNG số sự kiện ngoại giao mỗi ngày** (chủ động tạo 1–2 sự kiện mới + cập nhật item cho sự kiện đang chạy). Mỗi sự kiện mới phải có đủ `name`, `status`, `dates`, `location`, `scale`, `summary`, và ≥1 `items`. **`status` PHÂN LOẠI đúng 3 mức** (giao diện hiển thị theo nhóm này): `upcoming` = **Sắp diễn ra** (thượng đỉnh/hội nghị chưa họp) · `ongoing` = **Đang diễn ra** (đang họp/đàm phán nhiều ngày) · `recent` = **Đã kết thúc** (đã ký/đã họp xong). Khi một sự kiện `ongoing`/`upcoming` kết thúc, dùng `dipEventUpdates` KÈM đổi trạng thái (nêu trong tóm tắt để cập nhật status sang `recent`) (nguồn chứng minh — ưu tiên nguồn chính thức tầng 1). **LƯU Ý (24/07/2026): giao diện giờ tự SUY trạng thái hiển thị từ dải ngày `dates` so với hôm nay** (hàm `effStatus` trong `index.html`: parse "19-24/07/2026", "20/7 – 7/8/2026", "24/7/2026"… → trong khoảng = Đang diễn ra, trước = Sắp, sau = Đã kết thúc). Vì vậy KHÔNG cần sửa tay `status` mỗi ngày cho các mốc có `dates` rõ; `status` lưu trong DATA chỉ còn là **fallback** khi `dates` không parse được ngày (vd "Tháng 9/2026", "Cuối năm 2026"). Vẫn nên đặt `status` hợp lý lúc tạo, và ưu tiên ghi `dates` dạng có ngày/tháng/năm để auto hoạt động. Script tự CHẶN nếu tên trùng/giống sự kiện đã có (Jaccard ≥ 0.6) → khi đó dùng `dipEventUpdates` để thêm item vào sự kiện cũ thay vì tạo trùng. Nếu một tin đã đưa ở `worldNews`/`usNews` được nâng thành sự kiện, bỏ bản ở mảng tin phẳng để URL không trùng 2 chỗ.

### 4. `analyses` — bài phân tích THINK-TANK (mục 🧠 Phân tích → 🏛️ Think-tank)

> 📄 **📦 TÁCH RA FILE RIÊNG `data/analyses.json` (30/07/2026, chỉ thị Huy)** → [`docs/luat-think-tank.md`](docs/luat-think-tank.md) — `data/analyses.json`, `analyses_store.py`, 3 chỗ đã vá kèm

> 📄 **🌏 BỐN KHU VỰC GẦN NHƯ TRẮNG BÀI — hai nguyên nhân chồng nhau (vá 06/08/2026)** → [`docs/luat-think-tank.md`](docs/luat-think-tank.md) — Nam Á/Trung Á/Châu Phi/Bắc Cực — thiếu nguồn + nhãn bị hút

> 📄 **📚 MỘT VIỆN CÓ HAI FEED: BLOG và NGHIÊN CỨU — bảng chỉ khai một nửa (vá 06/08/2026)** → [`docs/luat-think-tank.md`](docs/luat-think-tank.md) — feed BLOG vs NGHIÊN CỨU; `--candidates-dai`; `do_nguon_mot_muc.py`; `do_nguon_hai_mien.py`

> 📄 **🔍 ĐO LẠI TOÀN BỘ NGUỒN THINK-TANK BỊ CHẶN — 30/07/2026 (chỉ thị Huy: kiểm bằng trình duyệt thật)** → [`docs/luat-think-tank.md`](docs/luat-think-tank.md) — 40 domain dò lại 30/07, Cloudflare vs curl

> 📄 **🚪 BẢNG ĐƯỜNG VÀO TỪNG NGUỒN — trang nào phải xem bằng cách gì (chỉ thị Huy 30/07/2026)** → [`docs/luat-think-tank.md`](docs/luat-think-tank.md) — 5 bậc đường vào + thứ tự phải đi khi nghi nguồn chết

> 📄 **🕸️ LỚP [HTML] QUÉT THINK-TANK — viện không có RSS (dựng 30/07/2026)** → [`docs/luat-think-tank.md`](docs/luat-think-tank.md) — `THINKTANK_HTML`, ngày lấy theo 3 bước

> 📄 **🏷️ Nhãn `outlet` — bảo trì bằng `scripts/sua_nhan_analyses.py` (dựng 29/07/2026)** → [`docs/luat-think-tank.md`](docs/luat-think-tank.md) — `sua_nhan_analyses.py`, chọn nhãn chuẩn theo bảng feed

## ✅ THANG XÁC MINH — bao nhiêu nguồn là ĐỦ để nạp một tin (chốt 27/07/2026)
Trước đây chỉ có luật cụt "không chắc link thì bỏ", nên thực tế xử lý lệch nhau: cùng ngày 27/07 tao
**bỏ** tin hợp đồng Space Force 400,4 triệu USD (vì search 6 trang chuyên ngành không ra) nhưng lại
**nạp** tin tàu 015-Trần Hưng Đạo (link gốc qdnd.vn trả 302 với mọi công cụ). Huy hỏi đúng chỗ: vấn đề
không phải "thiếu nguồn xác nhận" mà là **thiếu thang**. Thang chuẩn:

| Nguồn của tin | Cần xác nhận thêm? |
|---|---|
| **Tầng 1 — chính thức** (war.gov/defense.gov, navy.mil, state.gov, whitehouse.gov, defence.gov.au, qdnd.vn, mofa…) — đọc được nội dung | **KHÔNG.** Thông cáo chính thức TỰ NÓ là xác nhận. Đừng bắt nó phải được báo chí đưa lại mới cho nạp |
| **Wire** (Reuters, AP, AFP, Bloomberg) hoặc **báo chuyên ngành lớn** (Defense News, Breaking Defense, Defense One, Naval News, SpaceNews, DefenseScoop, Janes…) | **KHÔNG**, một nguồn là đủ |
| **Báo phổ thông uy tín** (BBC, Al Jazeera, SCMP, Nikkei, The Hill, CBS…) | **KHÔNG**, một nguồn là đủ |
| **Trang TỔNG HỢP / DẪN LẠI** (Báo Mới, RealClear*, Investing.com, Yahoo/AOL, MSN, aggregator vô danh) | **CÓ — bắt buộc truy về BÀI GỐC.** Ra gốc thì dùng gốc; không ra gốc thì cần **2 nguồn độc lập** cùng khẳng định, không thì BỎ |
| **Nguồn không mở được bằng tool** (403/302 loop/paywall) | Không phải lý do bỏ nếu **nội dung** đã được xác nhận qua đường khác (WebSearch snippet, nguồn thứ hai). **Dính PAYWALL thì thử `python3 /Users/Huy/Claude/congcu/lay_trang.py --duong=darkread <url>` TRƯỚC khi bỏ** (chỉ thị Huy 05/08/2026) — chi tiết và giới hạn ở `.claude/skills/quet-tin/SKILL.md` mục THANG XÁC MINH. Nếu KHÔNG xác nhận được chữ nào thì BỎ — đó là ca The Africa Report 25/07 |
| **Truyền thông nhà nước độc tài** (Xinhua, TASS, Global Times, KCNA…) | Chỉ dùng cho phát ngôn CỦA CHÍNH HỌ; sự kiện tranh chấp/thương vong phải có nguồn thứ hai |

**Nơi xác nhận HỢP ĐỒNG QUỐC PHÒNG** (mảng hay phải kiểm chéo nhất — danh sách cũ chỉ có 6 trang, quá
hẹp): trước hết là **trang Contracts chính thức** (`war.gov/News/Contracts/`), rồi tới **thông cáo của
chính nhà thầu** (lockheedmartin.com, gd.com, rtx.com, northropgrumman.com — họ luôn ra thông cáo khi
trúng hợp đồng lớn), rồi **báo chuyên hợp đồng**: GovConWire, ExecutiveGov, Defense Daily, Inside
Defense, Seapower (Navy League), National Defense Magazine, Shephard, Janes — cộng với 6 trang cũ
(SpaceNews, DefenseScoop, Breaking Defense, Defense News, C4ISRNet, Air & Space Forces).

⚠️ **Nhiều hợp đồng trong CÙNG một trang Contracts** thì `add_news.py` chặn vì trùng URL — đúng thiết
kế. Cách xử lý: **gộp thành MỘT tin** ("Lầu Năm Góc công bố loạt hợp đồng ngày DD/MM: …, …"), hoặc lấy
tin từ thông cáo riêng của nhà thầu để có URL khác. Đừng bỏ tin chỉ vì đụng guardrail này.

## 🎯 BẢNG ĐỘ GẦN NGUỒN — cổng chặn tin kênh tuyên truyền đứng một mình (dựng 06/08/2026)

**Dòng khai hiện hành — SỬA ĐÚNG DÒNG NÀY khi bảng đổi, đừng sửa phần nhật ký phía dưới:**
bảng độ gần đang canh **109 hãng**, dấu vân tay `1fe3b2dc1b92a8b97f03e106208c98c3857d81ee`
(độ gần 1: 18 · 2: 44 · 3: 41 · 4: 6).

⚠️ **CHỮ "ĐỘ GẦN" LÀ CỐ Ý, KHÔNG PHẢI "TẦNG".** Mục *"Nguồn theo 3 tầng"* ngay bên dưới xếp
nguồn theo **công dụng** — ở đó tầng 3 là viện nghiên cứu, dùng để neo nhận định, tức vị trí
CAO. Bảng này xếp theo **độ gần sự việc** — ở đây mức 3 là trang tổng hợp/dẫn lại, tức vị trí
THẤP. CSIS mang số 3 ở cả hai bảng với hai ý nghĩa trái ngược; Reuters là "báo chí dưới cùng"
ở bảng cũ nhưng mức 2 ở bảng này. Giữ chung một chữ là gài sẵn một chỗ đọc nhầm mà không tool
nào bắt được, nên Huy chốt 06/08/2026: bảng mới gọi là **độ gần**, bảng cũ giữ nguyên tên.

| Độ gần | Nghĩa |
|---|---|
| 1 | nguồn gốc chính thức — chính bên tạo ra sự việc, hoặc người quan sát trực tiếp |
| 2 | hãng tin có phóng viên tại chỗ |
| 3 | trang tổng hợp / dẫn lại |
| 4 | kênh tuyên truyền |

**VÌ SAO CÓ BẢNG NÀY.** Mục THANG XÁC MINH phía trên đã có sẵn dòng luật *"truyền thông nhà
nước độc tài: chỉ dùng cho phát ngôn của chính họ; sự kiện tranh chấp/thương vong phải có
nguồn thứ hai"* từ 27/07/2026. Luật đúng và đủ — thứ thiếu là **chỗ tra**: nó gọi tên LOẠI
nguồn chứ không gọi tên HÃNG, nên mỗi lượt quét lại phải xếp loại bằng phán đoán (*"Zona
Militar thuộc loại nào?"*, *"The Epoch Times thì sao?"*), phán đoán đó không được ghi lại ở
đâu, và không cổng nào đo được nó đã xảy ra hay chưa. Bảng biến phán đoán ấy thành phép tra.

**Cắm ở đâu:** `scripts/do_gan.py` (một hàm kiểm tra duy nhất, `add_news.py` GỌI — cấm chép
logic sang nơi khác) · bảng `data/do-gan-nguon.json`.

**HAI ĐƯỜNG QUA CỔNG cho tin độ gần 4, cố ý là hai chứ không phải một:**
- `"nguonThuHai": "<url>"` — phải khác **tên miền gốc** với `sourceUrl`. Dùng khi tin là sự
  kiện tranh chấp/thương vong, hoặc nói về bên thứ ba.
- `"phatNgonCuaChinhHo": true` — dùng khi tin là phát ngôn/hành động do CHÍNH bên đó công bố.

⚠️ **Đường thứ hai BẮT BUỘC phải có, nếu không cổng chặn oan đúng loại tin mà luật gốc cho
phép.** Đo trên 497 tin đang sống ngày 06/08: cổng chạm 03 tin, thì 02 tin là Trung Quốc
công bố việc của chính Trung Quốc (Global Times) — hợp lệ theo luật gốc — chỉ 01 tin (The
Epoch Times viết về cam kết của Tổng thống Philippines) mới là ca luật gốc nhắm tới. Cổng nào
ở luồng bình thường luôn phải mở cờ mới qua được là cổng chết: nó dạy người dùng phản xạ mở
cờ, mà mở cờ quen tay thì mọi cổng còn lại mất giá theo. Đường thứ hai không phải lỗ hổng —
nó là một lời khai được GHI vào tin, tức đúng thứ trước giờ vẫn xảy ra trong đầu người quét
mà không để lại dấu vết nào.

**Phạm vi cố ý hẹp:** chỉ chặn `worldNews` · `usNews` · `baomoiNews` · items của sự kiện.
`xNews` chỉ **cảnh báo**, không chặn — luồng đó được trình bày trên web đúng như bản chất của
nó (tiếng nói mạng xã hội chưa thẩm định), nên bắt nó có nguồn thứ hai là đổi bản chất luồng
chứ không phải vá một lỗ. Nguồn **chưa có trong bảng cũng không bị chặn**: đo 06/08 thì 39%
số tin đang sống mang tên nguồn chưa xếp loại, chặn cả nhóm đó là chặn oan hàng loạt.

**Cờ mở cổng — CÓ THẬT, được đọc, và để lại dấu:**
```bash
python3 scripts/add_news.py /tmp/new_items.json --bo-cong-do-gan="lý do cụ thể"
```

⚠️ **BẢNG TRONG REPO LÀ BẢN CHÉP — bản gốc ở `App/RenPhanTich/du-lieu/nguon.json`.** Buộc
phải chép vì `add_news.py` chạy **cả trên máy chạy của GitHub Actions**
(`import-news-from-drive.yml`, `claude-web-scan.yml`), nơi `/Users/Huy/Claude/App/` không tồn
tại — trỏ đường dẫn tuyệt đối là cổng chết câm trên CI: không tra được thì không chặn được,
và không có lỗi nào phát ra. Đã có hai bản thì phải có phép đo canh cho chúng đừng tách nhánh.
**Sửa bảng thì sửa BẢN GỐC rồi chạy `python3 scripts/dong_bo_do_gan.py --sinh`**, đừng sửa tay
bản trong repo (`--kiem` tính lại dấu vân tay từ chính nội dung nên sửa tay là lộ ngay).

**Chuỗi canh — 03 mắt, mỗi mắt một phép đo khác nhau:**
| Mắt | Đo gì | Chạy ở đâu |
|---|---|---|
| `scripts/dong_bo_do_gan.py --kiem` | bản gốc ↔ bản chép trong repo | `khoe.py` mỗi sáng |
| `tests/test-cong-do-gan.py --tu-kiem` | bản chép ↔ hành vi cổng (16 ca · 10 bản hỏng) | `khoe.py` mỗi sáng |
| `HeThong/dong-bo-luat.py --kiem` | bản chép ↔ dòng khai hiện hành ở đầu mục này | `khoe.py` lớp 8 |

**Số đo lúc dựng (06/08/2026):** bảng khớp 61% số tin đang sống (388/638) — tin thế giới 65%,
tin Mỹ 66%, tin bị loại 34%, mạng xã hội 54%; kho bài think-tank khớp 87% (443/506). Phần hụt
lớn nhất là mục Bị loại: 56/86 tin đến từ báo trong nước qua Báo Mới, chưa có tên nào trong
bảng. Độ gần 4 xuất hiện 07 lần trong dữ liệu sống (Global Times ×2, The Epoch Times ×1, cộng
04 tài khoản mạng xã hội) — tức cổng có việc thật để làm.

## Nguồn theo 3 tầng (chuẩn báo cáo/INTREP — áp dụng từ 11/07/2026)
**Nguyên tắc:** dữ kiện/sự kiện neo vào nguồn CHÍNH THỨC (tầng 1); số liệu kinh tế/quân sự neo vào nguồn DỮ LIỆU (tầng 2); kết luận/nhận định chiến lược (field `significance` + phần Phân tích) neo vào VIỆN NGHIÊN CỨU (tầng 3). Báo chí/hãng tin (dưới cùng) dùng để PHÁT HIỆN sự kiện sớm, KHÔNG tự mình làm chỗ dựa cho kết luận — luôn đối chiếu. Tin quân sự chỉ có 1 nguồn (Army Recognition/Naval News/blog) → kiểm chứng thêm bằng thông cáo bộ quốc phòng/ảnh chính thức/Janes/SIPRI. Khi tin bắt nguồn từ thông báo chính thức, link THẲNG tới nguồn gốc tầng 1 thay vì báo dẫn lại.

### Tầng 1 — Nguồn chính thức (xác minh sự kiện; ưu tiên cao nhất)
| Nhóm | Nguồn chính thức | Handle X |
|---|---|---|
| Đa phương | NATO (nato.int), Liên Hợp Quốc (news.un.org, UN Meetings Coverage, Hội đồng Bảo an), EU/Hội đồng châu Âu (consilium.europa.eu), EEAS (eeas.europa.eu), ASEAN (asean.org) | @NATO, @UN, @EUCouncil, @ASEAN |
| Mỹ | Nhà Trắng (whitehouse.gov), Bộ Quốc phòng (defense.gov), Bộ Ngoại giao (state.gov), CENTCOM (centcom.mil), Lực lượng Không gian/Hải quân/Lục quân, Fed (federalreserve.gov), Quốc hội/CRS | @WhiteHouse, @DeptofDefense, @StateDept, @CENTCOM, @SecRubio |
| QP/NG các nước | Bộ QP Anh (gov.uk), Australia (defence.gov.au), Nhật (mod.go.jp), Hàn (mnd.go.kr), Ấn Độ, Philippines, TQ (mod.gov.cn), Nga; Bộ Ngoại giao (mofa.go.jp...); Phủ TT Ukraine (president.gov.ua) | @ZelenskyyUa |
| Việt | Chính phủ (baochinhphu.vn), Bộ Ngoại giao (mofa.gov.vn), Bộ Quốc phòng, Thông tấn xã VN (TTXVN/vietnamplus.vn), Nhân Dân (nhandan.vn), Quân đội Nhân dân (qdnd.vn) | |

**📁 Bộ nguồn chính thức Mỹ MỞ RỘNG (thêm 22/07/2026)** — hai file tra cứu trong `docs/`, dùng khi cần link thẳng nguồn gốc:
| File | Nội dung | Dùng cho |
|---|---|---|
| [`docs/nguon-chinh-thuc-my.md`](docs/nguon-chinh-thuc-my.md) | **199 URL / 85 domain** — trang thông cáo & cập nhật chính thức: Nhà Trắng · OMB/CEA/OSTP · State · ODNI/NSA · DoD + 6 quân chủng + CENTCOM/PACOM · Treasury/Fed/SEC/CFTC/FDIC · USTR/Commerce/BIS · BEA/BLS/Census · **49 uỷ ban Thượng viện + 52 uỷ ban Hạ viện** | Agent Kinh tế · Chính trị · CNQS · Ngoại giao |
| [`docs/mangxahoi-chinh-thuc-my.md`](docs/mangxahoi-chinh-thuc-my.md) | **173 handle X đã xác minh** (chỉ tài khoản được liên kết từ web chính thức của cơ quan) — hành pháp 39 · quốc phòng 9 · lãnh đạo cấp cao 27 · Thượng viện 45 · Hạ viện 53 | **Agent xNews** |

**KHÔNG dán nguyên file vào prompt agent** — quá dài. Agent điều phối chọn vài dòng hợp với category của từng agent rồi nhúng. Hai file này CHƯA verify bằng fetch thật (khác bảng RSS ở dưới); URL nào lỗi thì bỏ, không retry.

**CẢNH BÁO truyền thông nhà nước độc tài** (Xinhua, TASS, Global Times, Press TV, KCNA, Sputnik...): CHỈ dùng cho phát ngôn/tuyên bố CỦA CHÍNH HỌ (vd "Trung Quốc thông báo tập trận X", "Nga tuyên bố Y") — KHÔNG dùng làm nguồn trung lập cho sự kiện gây tranh cãi, thương vong, hay bên thứ ba. Ngoại lệ của quy tắc "ưu tiên nguồn chính phủ".

### Tầng 2 — Nguồn dữ liệu (xác minh số liệu kinh tế/quân sự)
| Chủ đề | Nguồn |
|---|---|
| Kinh tế vĩ mô/tài chính/thương mại | IMF (imf.org — WEO), World Bank (data.worldbank.org), OECD (oecd.org), WTO (wto.org), BIS (bis.org), UNCTAD (unctad.org) |
| Năng lượng | IEA (iea.org) |
| Quốc phòng (số liệu) | SIPRI (sipri.org — chi tiêu QP, chuyển giao vũ khí), IISS Military Balance (*phần lớn trả phí*), Janes (*trả phí*) |

### Tầng 3 — Nguồn phân tích/viện nghiên cứu (cho `significance` + phần Phân tích)
| Khu vực/chủ đề | Nguồn |
|---|---|
| Mỹ | CSIS (+ChinaPower, AMTI về Biển Đông), RAND, Brookings, Carnegie, CFR, CNAS, Atlantic Council, Stimson, Hudson |
| Anh/Âu | RUSI, Chatham House, IISS, ECFR, SWP (Đức), IFRI (Pháp) |
| Ấn Độ Dương-TBD | Lowy Institute, ASPI (Úc), ISEAS-Yusof Ishak, RSIS (Singapore), ORF (Ấn Độ) |
| TQ/Đông Á | MERICS, Jamestown Foundation, NBR |
| Bắc Âu/Baltic/Nga | ICDS (Estonia), FIIA (Phần Lan), Belfer Center |
| Công nghệ/AI/bán dẫn/mạng | CSET (Georgetown), CSIS Strategic Technologies, CNAS Tech & National Security, DARPA, CISA, NIST, ENISA, NATO DIANA |

### Báo chí (phát hiện tin nhanh — LUÔN đối chiếu tầng 1/2/3 trước khi kết luận)
| Nhóm | Nguồn |
|---|---|
| Wire (ưu tiên RẤT CAO — chuẩn, ít bình luận) | Reuters, Associated Press (AP), Agence France-Presse (AFP) |
| Kinh tế/tài chính (*một số trả phí*) | Bloomberg, Financial Times, Wall Street Journal, The Economist, CNBC, Fortune, Nikkei Asia |
| Quốc tế/khu vực | BBC, Deutsche Welle, France 24, Al Jazeera, Al Arabiya, The Straits Times, The Japan Times, The Korea Herald, South China Morning Post, Politico, Axios, The Hindu, Africanews, The Moscow Times |
| Quốc phòng chuyên ngành | Defense News, Breaking Defense, Defense One, Naval News, USNI News, C4ISRNet, SpaceNews, Task & Purpose; *tham khảo nhanh, cần kiểm chứng*: Army Recognition, Oryx |
| Phân tích chính sách (chọn lọc, *một số trả phí*) | The Diplomat, Foreign Policy, Foreign Affairs |
| Việt | VnEconomy, VnExpress, Tuổi Trẻ, Thanh Niên, Dân Trí, Báo Mới, Thế giới & Việt Nam |

**Bộ nguồn rút gọn nên ưu tiên hằng ngày (20 nguồn):** Reuters, AP, AFP, Financial Times, Bloomberg, Nikkei Asia, NATO, ASEAN, UN Meetings Coverage, IMF, World Bank, OECD, SIPRI, IISS, Janes, CSIS, RAND, RUSI, Chatham House, CSET — đủ 4 lớp: tin nhanh · dữ liệu kinh tế · dữ liệu quân sự · phân tích chiến lược.

## URL RSS — ĐÃ VERIFY BẰNG FETCH THẬT ngày 22/07/2026
Trước đây bảng này chỉ tổng hợp qua WebSearch và tự ghi "CHƯA VERIFY" (môi trường cũ chặn `curl`).
Máy hiện tại mạng thông nên đã mở thử **từng URL**: kiểm HTTP code, parse XML, đếm `<item>`, đo bài
mới nhất cách bao lâu. Kết quả: **23 nguồn chạy tốt · 3 sửa được URL · 5 bỏ hẳn · 1 gần như chết**.

⚠️ **Nếu tự kiểm lại, nhớ `curl --compressed`.** Lần chạy đầu UN News bị chấm "hỏng" chỉ vì thiếu cờ
này (server trả gzip, parse ra nhị phân). Đừng gạch một nguồn khi chưa loại trừ lỗi giải nén.

### Dùng tốt — đã xác nhận có item mới
| Nguồn | RSS URL | Kiểm 22/07 |
|---|---|---|
| Defense News | https://www.defensenews.com/arc/outboundfeeds/rss/category/global/?outputType=xml | 25 item, mới 1h |
| Naval News | https://www.navalnews.com/feed/ | 10 item, mới 1h |
| Breaking Defense | https://breakingdefense.com/full-rss-feed/ | 30 item, mới 2h |
| Defense One | https://www.defenseone.com/rss/all/ | 22 item, mới 16h |
| SpaceNews | https://spacenews.com/feed/ | 24 item, mới 6h |
| Task & Purpose | https://taskandpurpose.com/feed | 34 item, mới 1h |
| C4ISRNet | https://www.c4isrnet.com/arc/outboundfeeds/rss/?outputType=xml | 25 item, mới 6h |
| Al Jazeera | https://www.aljazeera.com/xml/rss/all.xml | 25 item, mới <1h |
| BBC World | http://feeds.bbci.co.uk/news/world/rss.xml | 31 item, mới <1h |
| Deutsche Welle | https://rss.dw.com/rdf/rss-en-world | 11 item, mới 4h |
| France 24 | https://www.france24.com/en/rss | 24 item, mới 1h |
| UN News | https://news.un.org/feed/subscribe/en/news/all/rss.xml | 30 item, mới 6h |
| The Straits Times | https://www.straitstimes.com/news/world/rss.xml | 50 item, mới <1h |
| The Moscow Times | https://www.themoscowtimes.com/rss/news | 50 item, mới 2h |
| South China Morning Post | https://www.scmp.com/rss/5/feed/ | 50 item, mới 4h |
| The Hindu | https://www.thehindu.com/news/international/feeder/default.rss | 60 item, mới <1h |
| Africanews | https://www.africanews.com/feed/rss | 50 item, mới 2h |
| Axios | https://www.axios.com/feeds/feed.rss | 100 item, mới 1h |
| CNBC | https://www.cnbc.com/id/100727362/device/rss/rss.html | 30 item, mới <1h |
| The Diplomat | https://thediplomat.com/feed/ | 30 item, mới 6h |
| VnExpress | https://vnexpress.net/rss/the-gioi.rss | 60 item, mới 1h |
| Thanh Niên | https://thanhnien.vn/rss/the-gioi.rss | 50 item, mới 4h |
| Tuổi Trẻ | https://tuoitre.vn/rss/the-gioi.rss | 50 item (feed không ghi ngày) |

### ĐÃ SỬA URL — URL cũ trong bảng này trả 404 / XML rỗng
| Nguồn | URL cũ (SAI) | URL ĐÚNG | Kiểm 22/07 |
|---|---|---|---|
| Nikkei Asia | `https://asia.nikkei.com/rss` → 404 | https://asia.nikkei.com/rss/feed/nar | 50 item |
| VnEconomy | `https://vneconomy.vn/rss/home.rss` → XML rỗng | https://vneconomy.vn/tin-moi.rss | 50 item, mới 4h |
| Dân Trí | `http://dantri.com.vn/Thegioi.rss` → 404 | https://dantri.com.vn/rss/the-gioi.rss | 100 item, mới 2h |

### BỎ HẲN — đừng thử lại, dùng WebSearch cho các nguồn này
| Nguồn | Lý do (kiểm 22/07) |
|---|---|
| NATO | `news.rss`, `rss/rss_newsroom.xml`, `rss.xml` đều 404 → `WebSearch site:nato.int` |
| USNI News | 403 với **cả `curl` LẪN WebFetch** (Cloudflare) — agent cũng không đọc được |
| Politico | Cloudflare "Just a moment"; WebFetch báo thẳng không fetch được domain này |
| Al Arabiya | 403, trả HTML tiếng Ả Rập. Thử `/tools/rss`, `/rss.xml`, `/feed/rss2/en.xml` đều hỏng |
| Reuters / AP / AFP | Không có RSS công khai ổn định — WebSearch (site:reuters.com / apnews.com) |
| Báo Mới | Đã có `baomoi_sync.py` + `baomoi_topics.py` |
| ~~Thế giới & Việt Nam~~ | ⚠️ **Đảo lại 25/07/2026** — URL thử hồi đó (`/rss/the-gioi.rss`) sai; feed thật `baoquocte.vn/rss_feed/` chạy tốt, xem bảng "Gộp từ kho tư liệu cũ" |

⚠️ **Fortune** (https://content.fortune.com/feed/) parse được 30 item nhưng bài mới nhất **120h (5 ngày)
trước** — feed thật nhưng gần như đứng. Ưu tiên thấp, đừng trông vào nó cho tin trong ngày.

**Cách kiểm lại về sau:** `scripts/rss_check.py` (đọc thẳng bảng này trong CLAUDE.md rồi fetch từng URL).

### Nguồn MỞ RỘNG 5 chủ đề — verify fetch thật 25/07/2026 (gộp vào để `rss_check.py` tự kiểm)
Bổ sung cho 5 chủ đề (Nội bộ Mỹ · Úc–Biển Đông · CNQS Mỹ · Mali · Pitch Black). Chi tiết cách dùng từng
nguồn xem Phụ lục trong `.claude/skills/quet-tin/SKILL.md`.
| Nguồn | RSS URL | Kiểm 25/07 |
|---|---|---|
| The Hill | https://thehill.com/feed/ | 100 item |
| The Hill — Defense | https://thehill.com/policy/defense/feed/ | 15 item |
| Roll Call | https://rollcall.com/feed/ | 10 item |
| Government Executive | https://www.govexec.com/rss/all/ | 22 item |
| ABC News AU (world) | https://www.abc.net.au/news/feed/51120/rss.xml | 25 item |
| Lowy Interpreter | https://www.lowyinstitute.org/the-interpreter/rss.xml | 50 item |
| AMTI/CSIS (Biển Đông) | https://amti.csis.org/feed/ | 10 item |
| Rappler | https://www.rappler.com/feed/ | 10 item |
| Philstar (headlines) | https://www.philstar.com/rss/headlines | 10 item |
| Inquirer | https://www.inquirer.net/fullfeed/ | 20 item |
| gCaptain | https://gcaptain.com/feed/ | 12 item |
| Naval Technology | https://www.naval-technology.com/feed/ | 10 item |
| The War Zone (TWZ) | https://www.twz.com/feed | 44 item |
| DefenseScoop | https://defensescoop.com/feed/ | 10 item |
| Aviation Week | https://aviationweek.com/rss.xml | 10 item |
| Long War Journal (Mali/JNIM) | https://www.longwarjournal.org/feed | 30 item |
| DVIDS news (tập trận) | https://www.dvidshub.net/rss/news | 20 item |

⚠️ **Feed fetch được nhưng ĐỨNG — đừng trông vào cho tin trong ngày** (kiểm 25/07): **AMTI/CSIS** bài
mới nhất ~81 ngày trước (nguồn phân tích tầng 3, đăng thưa — dùng làm nền/bối cảnh Biển Đông thôi);
**Aviation Week** (`rss.xml`) ~115 ngày trước (gần như chết như Fortune → WebSearch cho tin CNQS trong
ngày). Lowy Interpreter ~32h (blog phân tích, chấp nhận được).

**WebSearch-only (không RSS dùng được — kiểm 25/07, ĐỪNG đưa vào bảng trên):** NOTUS · Punchbowl (trả
phí) · C-SPAN · Defence Connect · ADBR · Philippine News Agency (pna.gov.ph 403) · Manila Bulletin (403)
· Radio Free Asia (rfa.org) · The Maritime Executive · National Defense Magazine · Jeune Afrique (403) ·
The Africa Report (403) · RFI (rfi.fr) · ISS Africa → dùng `WebSearch site:domain`.

### Trang CHÍNH THỨC Mỹ có RSS — verify fetch thật 27/07/2026 (đưa `docs/nguon-chinh-thuc-my.md` vào đường quét)
Huy gửi file `trang chính thống của Mỹ.doc` (199 URL / 85 domain) và bảo kiểm xem đã có chưa. Kết quả
đối chiếu: **199/199 URL ĐÃ có** trong `docs/nguon-chinh-thuc-my.md` từ 22/07 — nhưng đó chỉ là **danh
sách tra cứu**, không nằm trong đường quét: **0/85 domain có trong bảng RSS**, và **76/85 chưa bao giờ
đóng góp một tin nào**. Đúng bệnh "có mục mà không có đường nạp thì mục chết".
Đã dò RSS cho 30 domain hợp 5 chủ đề, **9 cái chạy** → đưa vào bảng để `harvest.py` tự quét:
| Nguồn | RSS URL | Kiểm 27/07 | Hợp nhóm/chủ đề |
|---|---|---|---|
| Nhà Trắng — Presidential Actions | https://www.whitehouse.gov/presidential-actions/feed/ | 30 item | **Nội bộ Mỹ nhóm 2** (sắc lệnh, memorandum) |
| Uỷ ban Đối ngoại Hạ viện | https://foreignaffairs.house.gov/rss.xml | 10 item | **Nội bộ Mỹ nhóm 1** (điều trần/thông cáo uỷ ban) |
| Cục Dự trữ Liên bang | https://www.federalreserve.gov/feeds/press_all.xml | 20 item | Nội bộ Mỹ nhóm 4 |
| SEC | https://www.sec.gov/news/pressreleases.rss | 25 item | Nội bộ Mỹ nhóm 4 |
| FTC | https://www.ftc.gov/feeds/press-release.xml | 10 item | Nội bộ Mỹ nhóm 4 |
| USTR | https://www.ustr.gov/rss.xml | 10 item | Nội bộ Mỹ nhóm 4 (thuế quan) |
| BEA | https://www.bea.gov/news/rss | 12 item | Nội bộ Mỹ nhóm 4 (số liệu vĩ mô) |
| Bộ Năng lượng | https://www.energy.gov/rss.xml | 10 item | nhóm 2/4 + hạt nhân |
| Lực lượng Không gian Mỹ | https://www.spaceforce.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=1060&max=20 | 20 item | **CNQS Mỹ** |

⚠️ **KHÔNG có RSS dùng được — đừng thử lại, dùng WebSearch `site:domain`** (kiểm 27/07): các uỷ ban
Thượng viện (armed-services, foreign, appropriations, intelligence — đều 403) · armedservices.house.gov
· state.gov · commerce.gov · justice.gov · dhs.gov · home.treasury.gov · bls.gov · dni.gov · stripes.com.
### 🪖 Trang .mil — chẩn đoán 27/07 SAI MỘT NỬA, đo lại 30/07/2026
| Nguồn | RSS URL | Kiểm 30/07 từ LOCAL |
|---|---|---|
| Lục quân Mỹ | https://www.army.mil/rss/static/1.xml | **43–45 item** — lấy được, phải đi bằng vân tay TLS |
| Không quân Mỹ — Air Force Link News | https://www.af.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=1&max=20 | chập chờn: có lượt 20 item, phần lớn không phân giải nổi tên miền |

⚠️ **BẪY `Site=1`:** tham số này trả **feed của Air Force bất kể domain** — thử `marines.mil` và
`news.uscg.mil` với `Site=1` đều ra y hệt "Air Force Link News". Thêm cả ba vào bảng là nạp trùng nội
dung ba lần. Phải kiểm tiêu đề thật trước khi tin một feed `DesktopModules`.
⛔ **Chưa tìm được feed RSS riêng** (mọi biến thể ContentType/Site đã thử đều 0 item): `navy.mil`,
`marines.mil`, `centcom.mil`, `pacom.mil`, `jcs.mil`, `news.uscg.mil`. Phần này vẫn đúng — **nhưng câu
kế tiếp thì SAI và đã bỏ.**

> 📄 Vì sao bảng này thành ra như vậy (số đo, hai lần đảo lại nhãn, các bẫy khi đo) →
> [`docs/nhat-ky-nguon.md`](docs/nhat-ky-nguon.md)

### 🕸️ TRANG HTML QUÉT TRỰC TIẾP — không có RSS nhưng vẫn đọc được (thêm 27/07/2026)
**Cột "Chạy ở"** — `cả hai` = local + CI đều đọc được · **`CI`** = CHỈ GitHub runner đọc được, máy Mac
bị chặn (harvest local tự bỏ qua, xem `html_pages_from_claude_md`). Đo bằng `scripts/probe_sources.py`
chạy ở cả hai nơi (27/07/2026), **đo lại 30/07/2026 bằng `kiem_nguon.py` + trình duyệt**.
| Trang | URL | Chạy ở | Nhóm/chủ đề |
|---|---|---|---|
| Uỷ ban Quân vụ Hạ viện | https://armedservices.house.gov/news/press-releases | cả hai | **Nội bộ Mỹ nhóm 1** |
| Uỷ ban Chuẩn chi Hạ viện | https://appropriations.house.gov/news/press-releases | cả hai | **Nội bộ Mỹ nhóm 1** |
| Uỷ ban Tình báo Hạ viện | https://intelligence.house.gov/news/ | cả hai | Nội bộ Mỹ nhóm 1 |
| Uỷ ban Tư pháp Hạ viện | https://judiciary.house.gov/media/press-releases | cả hai | Nội bộ Mỹ nhóm 1 |
| Uỷ ban An ninh Nội địa Hạ viện | https://homeland.house.gov/news/ | cả hai | Nội bộ Mỹ nhóm 1 |
| Uỷ ban Giám sát Hạ viện | https://oversight.house.gov/news/ | cả hai | Nội bộ Mỹ nhóm 1 |
| Uỷ ban Tài chính Hạ viện | https://financialservices.house.gov/news/ | cả hai | nhóm 1 + 4 |
| Uỷ ban Thuế vụ Hạ viện | https://waysandmeans.house.gov/news/ | cả hai | nhóm 1 + 4 |
| Uỷ ban Ngân sách Hạ viện | https://budget.house.gov/news | cả hai | nhóm 1 + 4 |
| Uỷ ban Khoa học Hạ viện | https://science.house.gov/news | cả hai | nhóm 1 |
| **Uỷ ban Quân vụ THƯỢNG VIỆN** | https://www.armed-services.senate.gov/press-releases | cả hai | **Nội bộ Mỹ nhóm 1** |
| **Uỷ ban Đối ngoại Thượng viện** | https://www.foreign.senate.gov/press | cả hai | **Nội bộ Mỹ nhóm 1** |
| **Uỷ ban Chuẩn chi Thượng viện** | https://www.appropriations.senate.gov/news/majority | cả hai | **Nội bộ Mỹ nhóm 1** |
| **Uỷ ban Tình báo Thượng viện** | https://www.intelligence.senate.gov/reports-publications/press-releases/ | cả hai | **Nội bộ Mỹ nhóm 1** |
| **Uỷ ban Tư pháp Thượng viện** | https://www.judiciary.senate.gov/press/ | cả hai | Nội bộ Mỹ nhóm 1 |
| Uỷ ban Ngân hàng Thượng viện | https://www.banking.senate.gov/newsroom | cả hai | nhóm 1 + 4 |
| Uỷ ban Tài chính Thượng viện | https://www.finance.senate.gov/chairmans-news | cả hai | nhóm 1 + 4 |
| Uỷ ban Ngân sách Thượng viện | https://www.budget.senate.gov/chairman/newsroom | cả hai | nhóm 1 + 4 |
| Uỷ ban Thương mại Thượng viện | https://www.commerce.senate.gov/press/ | cả hai | nhóm 1 + 4 |
| Uỷ ban Năng lượng Thượng viện | https://www.energy.senate.gov/newsroom | cả hai | nhóm 1 |
| Uỷ ban An ninh Nội địa Thượng viện (HSGAC) | https://www.hsgac.senate.gov/media/majority-news/ | cả hai | nhóm 1 |
| Uỷ ban Quy tắc Thượng viện | https://www.rules.senate.gov/news/press-releases | cả hai | nhóm 1 |
| Thông cáo chung Thượng viện | https://www.pressphotographers.senate.gov/senate/senate-press-releases/ | cả hai | nhóm 1 |
| **Hải quân Mỹ** | https://www.navy.mil/Press-Office/Press-Releases/ | cả hai | **Úc & Biển Đông** · CNQS Mỹ |
| **Thuỷ quân lục chiến Mỹ** | https://www.marines.mil/News/Press-Releases/ | cả hai | **Úc & Biển Đông** · **Pitch Black** |
| **PACOM (Bộ Chỉ huy Ấn Độ Dương-TBD)** | https://www.pacom.mil/Media/News/News-Articles/ | **CI** | **Úc & Biển Đông** · **Pitch Black** |
| **CENTCOM** | https://www.centcom.mil/MEDIA/PUBLIC-RELEASES/ | **CI** | **Mỹ–Mali** · CNQS Mỹ |
| **JCS (Hội đồng Tham mưu trưởng Liên quân)** | https://www.jcs.mil/Media/News/ | **CI** | CNQS Mỹ · Úc & Biển Đông |
| **Tuần duyên Mỹ (USCG)** | https://www.news.uscg.mil/Press-Releases/ | **CI** | Úc & Biển Đông |
| Census Bureau | https://www.census.gov/newsroom/press-releases.html | **CI** | nhóm 4 (số liệu) |
| OCC (Kiểm soát Tiền tệ) | https://www.occ.treas.gov/news-events/newsroom/news-issuances-by-year/news-releases/index-news-releases.html | **CI** | nhóm 4 |

⚠️ Đây là **quét HTML thô**, nhiễu cao hơn RSS: có thể lẫn link điều hướng, và **ngày lấy từ khối HTML
quanh link nên có thể sai** — agent PHẢI mở bài kiểm ngày sự kiện như với lớp `[GNEWS]`.
- **Nghiệm thu một trang mới thì đếm 3 con số**, đừng dừng ở mã 200: số link qua bộ lọc đường dẫn ·
  số khớp `match_topic` · và độ dài tiêu đề lấy ra. Trang 200 mà 0 link là dòng bảng vô dụng.
> 📄 **📊 Kết quả dò TOÀN BỘ nguồn ở CẢ HAI môi trường (27/07/2026, `scripts/probe_sources.py`)** → [`docs/nhat-ky-nguon.md`](docs/nhat-ky-nguon.md) — ảnh chụp 27/07 bằng curl trần (đã bị bản đo 30/07 đảo lại)

> 📄 **🔄 ĐO LẠI 30/07/2026 BẰNG CÔNG CỤ ĐÃ VÁ — bảng số trên dựng bằng curl TRẦN nên phóng đại "403"** → [`docs/nhat-ky-nguon.md`](docs/nhat-ky-nguon.md) — đo lại có bậc 2: 403 tụt 31 → 6

> 📄 Vì sao bảng này thành ra như vậy (số đo, hai lần đảo lại nhãn, các bẫy khi đo) →
> [`docs/nhat-ky-nguon.md`](docs/nhat-ky-nguon.md)

### RealClear — verify fetch thật 27/07/2026 (Huy chỉ định thêm)
| Nguồn | RSS URL | Kiểm 27/07 | Hợp chủ đề |
|---|---|---|---|
| RealClearDefense | https://www.realcleardefense.com/index.xml | 126 item, mới trong ngày | 3 CNQS Mỹ · 2 Úc–Biển Đông |
| RealClearPolitics | https://www.realclearpolitics.com/index.xml | có item mới trong ngày | 1 Nội bộ Mỹ (cả 4 nhóm) |
| RealClearWorld | https://www.realclearworld.com/index.xml | 200 | chung |

⚠️ **Chỉ `index.xml` chạy** — `/feed/`, `/politics.xml` và cả trang chủ đều trả **403** với curl. Đừng
đổi sang dạng khác.
⚠️ **RealClear là trang TỔNG HỢP** (giống Báo Mới): phần lớn item là bài **bình luận/phân tích** của
tác giả khác đăng lại trên tên miền realclear*, link trỏ về chính realclear chứ không về toà soạn gốc.
Vì vậy: (a) ưu tiên các item là TIN (vd "Pentagon Awards Largest-Ever F-35 Spare Parts Contract") hơn
là bài opinion; (b) **truy về bài gốc** như quy tắc Báo Mới — mở bài, tìm nguồn gốc (thông cáo chính
thức / wire / báo chuyên ngành) rồi lấy link đó; không tìm được thì giữ link realclear nhưng phải ghi
rõ `sourceName` là RealClearDefense/Politics để người đọc biết đây là trang tổng hợp.

### Nguồn CHÍNH THỨC Lầu Năm Góc — verify fetch thật 27/07/2026 (mỏ tin CNQS chưa khai thác)
`defense.gov` nay **redirect sang `war.gov`** (đổi tên bộ). Trang `war.gov/News/Contracts/` trả 403 với
curl, NHƯNG hai feed RSS dưới đây chạy tốt — đây là nguồn TẦNG 1 cho chủ đề CNQS Mỹ, trước giờ chưa
dùng lần nào:
| Nguồn | RSS URL | Kiểm 27/07 |
|---|---|---|
| DoD Contracts | https://www.war.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=400&Site=945&max=20 | có "Contracts for July 24/23/22, 2026" |
| DoD News Releases | https://www.war.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=9&Site=945&max=20 | có thông cáo mới (vd hợp đồng Oracle ~7 tỷ USD) |

⚠️ **Tiêu đề feed Contracts là "Contracts for July 24, 2026" — KHÔNG chứa từ khoá chủ đề nào**, nên
`harvest.py` phải gán cứng chủ đề cho hai nguồn này qua `FORCE_TOPIC`, đừng lọc bằng từ khoá. Mỗi item
là một trang gộp TẤT CẢ hợp đồng quốc phòng ký hôm đó — agent phải mở đọc và tự chọn hợp đồng đáng đưa
(khí tài cụ thể, giá trị lớn), không nạp cả trang.

**Đã thử và KHÔNG dùng được (đừng thử lại):** `armed-services.senate.gov/rss/hearings` — 403 ·
`c-span.org/rss/` — 403 · `war.gov/News/Contracts/` (trang HTML) — 403. Muốn theo lịch điều trần thì
dùng RSS The Hill (đã có trong bảng, thực tế bắt được tin "GOP senator ahead of Fauci testimony") hoặc
truy vấn Google News trong `harvest.py`.

### Gộp từ kho tư liệu cũ — verify fetch thật 25/07/2026
Ba file `docs/diemtin-*-sources.md` / `-x-accounts.md` (dò 09/07, trước giờ KHÔNG nguồn nào trong quy
trình quét đọc tới) đã được đối chiếu với bảng trên; phần dưới là các nguồn CHƯA có mặt và **fetch
thật hôm nay còn sống**. Cột "hợp chủ đề" = chủ đề trong 5 chủ đề đang quét.
| Nguồn | RSS URL | Kiểm 25/07 | Hợp chủ đề |
|---|---|---|---|
| Defense Daily | https://www.defensedaily.com/feed/ | 50 item, mới 12h | 3 CNQS Mỹ |
| Air & Space Forces Magazine | https://www.airandspaceforces.com/feed/ | 9 item, mới 13h | 3 CNQS Mỹ |
| Military Times | https://www.militarytimes.com/arc/outboundfeeds/rss/ | 25 item, mới 12h | 3 CNQS Mỹ |
| FlightGlobal | https://www.flightglobal.com/rss/ | 10 item, mới 12h | 3 CNQS Mỹ |
| The Aviationist | https://theaviationist.com/feed/ | 15 item, mới 15h | 3 CNQS Mỹ |
| Soldier Systems Daily | https://soldiersystems.net/feed/ | 6 item, mới 9h | 3 CNQS Mỹ |
| Sandboxx News | https://www.sandboxx.us/news/feed/ | 15 item, mới 11h | 3 CNQS Mỹ |
| DVIDS (toàn bộ) | https://www.dvidshub.net/rss/all | 419 item, mới 2h | 3 + 5 Pitch Black |
| Shephard Media | https://www.shephardmedia.com/news/feed/ | 10 item, mới 23h | 3 + 2 Úc |
| The Japan Times | https://www.japantimes.co.jp/feed/ | 30 item, mới 1h | 2 Biển Đông |
| Yonhap (Hàn Quốc) | https://en.yna.co.kr/RSS/news.xml | 97 item, mới trong ngày | 2 Biển Đông |
| AllAfrica | https://allafrica.com/tools/headlines/rdf/latest/headlines.rdf | 30 item, mới 14h | 4 Mali/Sahel |
| Federal News Network — Defense | https://federalnewsnetwork.com/category/defense-main/feed/ | 15 item, mới 10h | 1 Nội bộ Mỹ |
| Atlantic Council | https://www.atlanticcouncil.org/feed/ | 100 item, mới 17h | tầng 3 phân tích |
| Foreign Policy | https://foreignpolicy.com/feed/ | 25 item, mới 12h | tầng 3 phân tích |
| Bellingcat | https://www.bellingcat.com/feed/ | 10 item, mới 18h | OSINT kiểm chứng |
| The Guardian — World | https://www.theguardian.com/world/rss | 45 item, mới <1h | chung |
| Semafor | https://www.semafor.com/rss.xml | 261 item, mới 14h | chung |
| NPR — World | https://feeds.npr.org/1004/rss.xml | 10 item, mới 12h | chung |
| VietnamPlus (TTXVN) | https://www.vietnamplus.vn/rss/thegioi.rss | 50 item, mới trong ngày | 2 + VN tầng 1 |
| Nhân Dân | https://nhandan.vn/rss/thegioi-1231.rss | 50 item, mới trong ngày | VN tầng 1 |
| Báo Chính phủ | https://baochinhphu.vn/quoc-te.rss | 50 item (feed không ghi ngày) | VN tầng 1 |
| VietnamNet | https://vietnamnet.vn/rss/the-gioi.rss | 1000 item, mới <1h | VN chung |
| Báo Thế giới & Việt Nam | https://baoquocte.vn/rss_feed/ | 25 item, mới <1h | VN ngoại giao |

⚠️ **Sửa lại đánh giá cũ:** Thế giới & Việt Nam trước bị xếp "WebSearch-only" (bảng BỎ HẲN) vì thử
`/rss/the-gioi.rss` → 404. Feed thật là `rss_feed/` và chạy tốt → đã chuyển lên bảng này.
⚠️ **DVIDS `/rss/all`** (419 item) rộng hơn `/rss/news` (20 item) đang dùng — giàu tin diễn tập/ảnh
đơn vị, nhưng lẫn nhiều thông cáo địa phương; dùng cho tập trận/CNQS thì lọc theo từ khoá.
⚠️ **Nguồn VN vẫn là ưu tiên #2** (xem "Thứ tự ưu tiên" bên dưới: tiếng Anh trước) — thêm vào đây để
có URL sẵn khi cần góc nhìn trong nước / tin Biển Đông, KHÔNG phải để thay nguồn tiếng Anh.

**Kho tư liệu đã kiểm nhưng KHÔNG dùng được (đừng thử lại):** CSIS `csis.org/rss.xml` — parse được 10
item nhưng bài mới nhất **tháng 3/2016**, feed bỏ hoang 10 năm (bản dò 09/07 chấm "10 ✓" vì chỉ đếm
item, không đo tuổi bài) → `WebSearch site:csis.org`, riêng Biển Đông đã có `amti.csis.org/feed/` ·
War on the Rocks `warontherocks.com/feed/` — 403 · DARPA `darpa.mil/rss.xml` — không phân giải được
tên miền (thử 2 lần) → `WebSearch site:darpa.mil`.

## Thứ tự ưu tiên khi chọn nguồn để quét (áp dụng từ 10/07/2026, cập nhật 10/07 thêm ưu tiên #1)
1. **Ưu tiên nguồn chính phủ/chính thức (primary).** Khi một tin dựa trên thông báo/phát ngôn/tài liệu chính thức, ưu tiên link THẲNG tới nguồn gốc (defense.gov, nato.int, state.gov, whitehouse.gov, baochinhphu.vn...) thay vì chỉ dẫn lại báo chí. Chủ động tìm tin đáng đưa từ các nguồn chính thức này. LƯU Ý ngoại lệ truyền thông nhà nước độc tài (xem cảnh báo ở mục "Nguồn chính phủ/chính thức").
2. **Ưu tiên nguồn tiếng Anh** trước nguồn tiếng Việt. Nguồn Việt chỉ dùng bổ sung khi nguồn Anh không đủ tin, hoặc để lấy góc nhìn/tin trong nước.
3. **Ưu tiên nguồn có RSS feed** trước — nhanh và chính xác hơn tìm kiếm/web scraping thủ công. Nếu nguồn không có RSS hoặc RSS không truy cập được, mới dùng WebSearch/WebFetch.
4. **Ưu tiên nguồn CHƯA từng được quét trước đó.** Kiểm tra bằng `grep -oE "\"sourceName\":\"[^\"]+\"" index.html | sort | uniq -c` để biết nguồn nào đang bị bỏ sót.
5. **Điều hướng theo sở thích người đọc.** Người đọc bấm 👍/👎 trên từng tin, đồng bộ lên Supabase (giao diện KHÔNG hiển thị phân tích sở thích — chỉ thu vote; phân tích là việc của quy trình quét). Mỗi lần quét, session **đọc file local `preferences.json`** (gốc repo) để ưu tiên (điểm dương `net`) / giảm ưu tiên (điểm âm) chuyên mục · khu vực · nguồn. File này do **GitHub Action `sync-preferences.yml`** tự cập nhật hằng ngày: Action chạy trên máy GitHub (không bị Cloudflare chặn như môi trường quét), curl view công khai `vote_stats` từ Supabase rồi commit vào `main`. Đây là **định hướng mềm**: vẫn giữ tối thiểu 2 tin/category, không bỏ hẳn mục nào, không ghi đè quy tắc nguồn 3 tầng/chất lượng. (Chi tiết: `preferences.md`. Schema: `docs/supabase-setup.sql`.) LƯU Ý: KHÔNG tự WebFetch `*.supabase.co` khi quét — bị chặn 403 (đã kiểm chứng 12/07), việc lấy dữ liệu đã có Action lo.

> 📄 **~~Chỉ tiêu số lượng (SÀN CỨNG 15+15)~~ — ⚠️ LỖI THỜI 2026-07-23, xem banner đầu file (giờ là 5 chủ đề × 5–10 bài)** → [`docs/luat-lich-su.md`](docs/luat-lich-su.md) — LỖI THỜI 23/07 — sàn 15+15 đã bỏ; kèm Bộ LỌC SỞ THÍCH + 3 trọng tâm chủ động

> 📄 **Kiến trúc quét: nhiều agent Sonnet nhỏ (bắt buộc — để nhẹ và chống sập)** → [`docs/luat-lich-su.md`](docs/luat-lich-su.md) — bảng 8 agent (LỖI THỜI 23/07) + cơ chế agent còn đúng

## Guardrail tự động trong `scripts/add_news.py` (lớp chặn cuối, không tốn token)
Chạy `python3 scripts/add_news.py /tmp/new_items.json` sẽ tự động **CHẶN (raise lỗi, phải sửa JSON rồi chạy lại)** nếu gặp: thiếu field bắt buộc; `category` sai; `date` ngoài khung — kiểm **HAI LỚP** (siết 27/07/2026): cũ hơn 1 ngày so với ngày batch, **VÀ** cũ hơn 1 ngày so với **HÔM NAY theo giờ VN thật**, hoặc ở tương lai. Lớp thứ hai bịt đường lách "tách lô, neo lô A về ngày cũ" — chính cách 3 tin ngày 24/07 lọt vào bản tin 26/07. Gặp lỗi *"cũ hơn 1 ngày so với HÔM NAY"* thì BỎ tin, đừng lùi ngày batch; `sourceUrl` là trang chủ hoặc live-blog/live-updates; URL trùng nhau trong batch; URL đã có sẵn trong `DATA` (tin trùng); status ID X vô lý (quá ngắn hoặc kết thúc nhiều số 0 — nghi bịa); tên exercise/dipEvent (trong `*Updates`) không khớp entry có sẵn; tên sự kiện trong `newDipEvents` trùng/giống sự kiện đã có (Jaccard ≥ 0.6) hoặc thiếu field bắt buộc của sự kiện. Ngoài ra **CẢNH BÁO (in ra, không chặn)**: `sourceName` lạ ngoài danh sách nguồn đã biết; tiêu đề nghi trùng với tin cũ (Jaccard ≥ 0.6); phần nào chưa đủ chỉ tiêu số lượng. Khi script chặn: đọc thông báo, sửa/bỏ tin lỗi trong JSON rồi chạy lại — KHÔNG tự sửa `index.html` bằng tay.

> 📄 **⚠️ HAI BẪY khi lô tin trải QUÁ 2 NGÀY (gặp thật phiên tối 25/07/2026 — đọc trước khi nạp)** → [`docs/luat-chu-de.md`](docs/luat-chu-de.md) — tách lô làm rơi tin khỏi .docx; guardrail không bắt trùng SỰ KIỆN

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

> 📄 **~~Chu kỳ bản tin: 2 lần/ngày~~ — ⚠️ LỖI THỜI 2026-07-23: giờ CHỈ 1 lần/ngày buổi TỐI 22:00 (dự phòng 23:00), xem banner đầu file** → [`docs/luat-lich-su.md`](docs/luat-lich-su.md) — LỖI THỜI 23/07 — lịch thật ở docs/LICH.md

> 📄 **🔒 PHIÊN TEST HẠ TẦNG KHÔNG ĐƯỢC ĐỤNG CỜ THẬT — `DIEMTIN_PHIEN_TEST=1` (vá 29/07/2026)** → [`docs/luat-chu-de.md`](docs/luat-chu-de.md) — `DIEMTIN_PHIEN_TEST=1` → sổ riêng `state-test.json`

## Log & tự phục hồi (Routine tự động)
Routine chạy trong session mới (ephemeral) nên phải để lại dấu vết để chẩn đoán khi lỗi:
- **Log bắt buộc mỗi lần chạy**: ghi vào `logs/scan-<NGÀY-VN>.log` (ngày theo `TZ='Asia/Ho_Chi_Minh' date +%F`) các mốc: START, kết quả từng agent/phần, chạy script, và DONE/SKIP/FAIL kèm lý do. **Luôn commit + push file log** kể cả khi quét thất bại (git không cần mạng ngoài nên push được ngay cả khi WebSearch/WebFetch bị chặn) — đây là cách duy nhất biết Routine fail ở đâu.
- **Idempotent (chống chạy trùng)**: đầu mỗi lần chạy, `python3 scripts/state.py claim <pipeline>` (dùng `claim` để GIÀNH KHOÁ, không phải `check` — `check` chỉ hỏi, không chặn được phiên chạy chồng). exit 10 = buổi đó ĐÃ XONG · exit 11 = phiên khác đang chạy → cả hai: ghi log `SKIP`, push log, KẾT THÚC. exit 0 = quét bình thường, xong thì `state.py done <pipeline> "<tóm tắt>"` và commit `logs/state.json` kèm bản tin. **KHÔNG dùng `generatedAt` làm cờ** (xem mục trên).
- **Retry cho tới khi xong (xen kẽ CI/local từ 26/07/2026)**: bản tin TỐI (hạn chót email 22:00): CI 20:47 → local 21:15 (2 lớp trong hạn, local là task RIÊNG `web-scan-diem-tin-toi`) → CI 21:47 (lớp VÉT, chỉ khi 2 lớp trước chết); bỏ hẳn mốc 21:30/22:30; bản tin SÁNG SỚM (từ 27/07/2026 CÓ local dự phòng): CI 03:47 → local 04:30 → CI 04:47 → local 05:30. **event-scan sáng — GỘP 28/07/2026: dùng CHUNG 4 mốc trên**, chạy NGAY SAU bản tin trong cùng session (không còn mốc 08:45/09:15/09:45/10:15 riêng). Nhờ khoá idempotent `state.py`, mốc nào thấy DONE/RUNNING thì tự SKIP; phiên chết giữa chừng thì 30' sau heartbeat thối, mốc kế cướp khoá quét lại. Cron local là giờ LOCAL (Asia/Ho_Chi_Minh), **KHÔNG phải UTC**; cron CI là UTC.
- **Cờ tách theo Ô `sang`/`toi`, không chỉ theo ngày.** Ô tự suy từ giờ VN lúc chạy (trước 14:00 = `sang`, từ 14:00 = `toi`), routine KHÔNG cần truyền gì thêm; chạy tay ngoài giờ thì ép bằng `--slot sang|toi`. Ý nghĩa của ô KHÁC nhau theo pipeline:
  - `drive-import` (Action 08:00 & 20:00) — đúng nghĩa 2 buổi/ngày: nếu so thuần theo ngày thì lô sáng DONE sẽ làm lô tối cùng ngày SKIP oan.
  - `web-scan` (1 phiên/ngày buổi tối) và `event-scan` (1 phiên/ngày buổi sáng) — ô còn lại KHÔNG phải "phiên thứ hai", nó là ô **CHẠY BÙ** khi máy ngủ. Ví dụ bản tin tối 24/07 không chạy được, mở máy 03:46 ngày 25 mới chạy bù → lần đó rơi vào ô `sang` nên KHÔNG chiếm ô `toi` của ngày 25, và bản tin tối 25 vẫn quét bình thường. **ĐỪNG "dọn cho gọn" thành mỗi pipeline một ô cố định** — làm vậy lần chạy bù sẽ ăn luôn suất của ngày mới, mất 1 bản tin.
  - Nhãn in ra đã nói rõ điều này (sửa 25/07/2026, `SLOT_LABELS` trong `state.py`): `web-scan [phien toi]` vs `web-scan [phien toi CHAY BU (sang som)]`. Trước đây in "web-scan buoi sang" khiến đọc log tưởng web có phiên sáng. Nhãn CHỈ là chữ hiển thị — khoá và `lastSuccess` vẫn dùng key `sang`/`toi`.

## Báo Mới — HAI nguồn, xử lý KHÁC NHAU (cập nhật 22/07/2026)
Action `sync-baomoi.yml` sinh 2 file, **cả hai chỉ giữ bài đăng trong 24H gần nhất** (lọc theo
timestamp thật của Báo Mới) và đúng 4 chủ đề của web. Cả hai đều thiếu `summary` + `significance`
(2 field guardrail bắt buộc) nên phải qua agent viết bổ sung.

| File | Nguồn | Cần cookie | Cách dùng |
|---|---|---|---|
| `baomoi-saved.json` | Bài **người dùng tự bookmark** | Có (`BAOMOI_COOKIE`) | Lấy **HẾT**, KHÔNG áp bộ lọc sở thích → section `baomoiNews` → `DATA.worldNews` kèm cờ `_baomoi` (nhãn 📌 Đã lưu) |
| `baomoi-topics.json` | **Quét chuyên mục công khai** (`the-gioi`, `kinh-te`, `khoa-hoc-cong-nghe`) | Không | **KHO ỨNG VIÊN** (~50–100 bài) → CHỌN LỌC theo bộ lọc sở thích, lấy ~3–6 bài tốt nhất → `worldNews` như tin thường, KHÔNG gắn `_baomoi` |

```
python3 scripts/add_news.py --baomoi-pending   # in cả 2 nhóm, đã bỏ bài quá 24h + bài đã có trong DATA
```
> 📄 **TRUY NGƯỢC VỀ NGUỒN GỐC (bắt buộc từ 23/07/2026)** → [`docs/luat-chu-de.md`](docs/luat-chu-de.md) — Báo Mới: truy về bài gốc, bắt buộc `_baomoiUrl`

> 📄 **Nhập tin từ Google Drive (pipeline `drive-import`)** → [`docs/luat-lich-su.md`](docs/luat-lich-su.md) — pipeline `drive-import` — ĐÃ TẮT LỊCH 30/07, chỉ chạy tay

## Ghi chú vận hành
- **Hai routine nằm ở ĐÂU** (cập nhật 28/07/2026): đều là **scheduled task LOCAL trên máy Mac của Huy**, không phải routine trên claude.ai. Quản lý ở mục "Scheduled" trên sidebar, hoặc bằng tool `mcp__scheduled-tasks__*`. Cron **giờ LOCAL (Asia/Ho_Chi_Minh), KHÔNG phải UTC**. **NGUỒN SỰ THẬT về quy trình nằm TRONG REPO** (`docs/routine-web-scan.md` — `docs/routine-event-scan.md` từ 28/07/2026 chỉ còn là stub trỏ sang đó, xem banner đầu file đó); SKILL.md của các **scheduled task** (`~/.claude/scheduled-tasks/<taskId>/SKILL.md`) giờ chỉ là stub 5 dòng Read file repo tương ứng — **sửa quy trình thì sửa file trong docs/, ĐỪNG đụng stub**.

  ⚠️ **"Stub" ở đây CHỈ nói về `~/.claude/scheduled-tasks/*/SKILL.md`, KHÔNG phải `.claude/skills/quet-tin/SKILL.md` trong repo** (làm rõ 29/07/2026 sau khi câu cũ bị đọc thành mâu thuẫn). Skill `quet-tin` **là playbook NỘI DUNG thật, 460+ dòng, KHÔNG được rút thành stub**: `docs/routine-web-scan.md` Bước 2 và `.github/prompts/web-scan-ci.md` đều bảo phiên quét *"Đọc file `.claude/skills/quet-tin/SKILL.md` và làm ĐÚNG playbook trong đó"* — cho nó trỏ ngược lại `docs/` là **vòng tròn**, cả CI lẫn local mất sạch playbook. Phân vai: skill giữ **NỘI DUNG quét** (5 chủ đề, agent, guardrail, `scan-gaps.json`, phụ lục nguồn) · `docs/routine-web-scan.md` giữ **QUY TRÌNH CHẠY** (lịch, khoá, commit/push) · CLAUDE.md giữ **phạm vi + nguồn**. Bảng phân vai đầy đủ nằm ở đầu chính skill đó.

  | taskId | cron | Nguồn sự thật quy trình | Việc |
  |---|---|---|---|
  | `web-scan-diem-tin` | `30 4,5 * * *` (DỰ PHÒNG phiên SÁNG SỚM, sau CI 03:47/04:47) | `docs/routine-web-scan.md` (Bước 1-3 = bản tin, **Bước 4 = event-scan gộp**) | Bản tin 5 chủ đề **+ sự kiện/tập trận/think-tank** — phiên sáng sớm |
  | `web-scan-diem-tin-toi` | `15 21 * * *` (DỰ PHÒNG phiên TỐI, sau CI 20:47 — lớp CUỐI còn kịp hạn email 22:00) | `docs/routine-web-scan.md` (chung file với phiên sáng sớm để hai phiên không lệch nhau; mục "PHIÊN TỐI — BỐI CẢNH RIÊNG" cuối file) | Bản tin 5 chủ đề — phiên tối |
  | ~~`event-scan-diem-tin`~~ | **TẮT 28/07/2026** (`enabled: false`, không xoá) | ~~`docs/routine-event-scan.md`~~ | Việc gộp vào `web-scan-diem-tin` (dòng trên), xem banner `docs/routine-event-scan.md` |

  Mốc CHÍNH là workflow GitHub Actions `claude-web-scan.yml` (chạy `claude -p` với prompt
  `.github/prompts/web-scan-ci.md`, secret `CLAUDE_CODE_OAUTH_TOKEN`, máy Mac tắt vẫn chạy; xong tự
  kích notify-email/notify-morning/notify-push qua `gh workflow run`). **`claude-event-scan.yml` đã
  XOÁ 28/07/2026** — việc của nó nay nằm ở BƯỚC 6 trong CHÍNH `web-scan-ci.md`, chạy khi CI xác định
  mình đang ở ca sáng sớm.

  Mỗi lần fire tạo session mới, stub SKILL.md dẫn nó Read file quy trình trong `docs/`, có log + khoá idempotent (`state.py claim <pipeline>`) + mốc dự phòng.
- **Routine phải viết lệnh bằng ĐƯỜNG DẪN TUYỆT ĐỐI** (chốt 25/07/2026): `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/<x>.py` và `git -C /Users/Huy/Claude/diem-tin-the-gioi ...`. **TUYỆT ĐỐI KHÔNG `cd repo && ...`** — harness bật prompt xin quyền riêng cho `cd` ("can execute untrusted hooks from the target directory"), routine chạy lúc Huy không có mặt sẽ treo giữa đường chờ bấm nút. Các script đều tự tìm repo root từ `__file__` nên không cần đứng trong repo. Allowlist ở `/Users/Huy/Claude/.claude/settings.local.json` phải là **pattern** (`Bash(git -C /path *)`, `Bash(python3 /path/scripts/*)`), không phải câu lệnh literal do bấm "Always allow" — literal chỉ khớp đúng một chuỗi, đổi một chữ là hỏi lại. **VÀ mọi lệnh Bash phải PHẲNG — không wrapper, không biến, không vòng lặp (25–26/07/2026, treo 3 lần):** hễ lệnh chứa hàm/brace (`cd() { echo "cd disabled"; };` — flag "expansion obfuscation"), biến shell/`$(...)` (`$NGAY`, `$f` — flag "simple_expansion"), `for ... done` hay heredoc là harness BỎ QUA allowlist và vẫn bật prompt, dù lệnh bên trong hợp lệ (vụ 26/07: `for f in ...; do grep .../$f.jsonl; done` treo, trong khi 2 dòng `grep <path đầy đủ>` viết rời thì khớp `Bash(grep *)` chạy thẳng). Chỉ dùng lệnh đơn / pipe / chuỗi `&&`, đối số điền giá trị thật: ngày giờ chạy `date` riêng rồi điền literal; lặp nhiều file → viết N lệnh rời hoặc gói vào `python3 -c`. "Không dùng cd" = đừng gọi `cd`, không phải vô hiệu hoá nó.
- **⚠️ ĐỪNG để tồn dư chưa commit trong repo — nó làm NGHẼN bước 1 của mọi phiên routine sau** (gặp thật
  sáng 27/07/2026): `git pull --rebase origin main` chết ngay với *"cannot pull with rebase: You have
  unstaged changes"*, phiên routine dừng ở dòng đầu tiên. Lúc đó `git fetch` cho thấy **0 commit mới** —
  tức pull vốn là no-op, phiên bị chặn bởi chính việc dở của phiên khác chứ không phải xung đột thật.
  Hai vế: (a) **phiên nào sửa file thì commit trước khi rời máy**, đừng để `index.html`/`scripts/*` treo
  ở trạng thái modified; (b) phiên routine gặp lỗi này thì **`git fetch` trước để biết có commit mới
  thật hay không** — không có thì cứ đi tiếp, **KHÔNG stash và KHÔNG commit hộ file lạ** (mục 14 quy tắc
  toàn cục: thấy việc dở của người khác thì báo, không tự quyết).
- **HẠN CHẾ phải biết**: scheduled task local **chỉ chạy khi app Claude đang mở**; app đóng lúc tới giờ thì nó chạy bù ở lần mở kế tiếp. Từ 26/07/2026 điều này ĐỠ nghiêm trọng vì mốc chính đã là GitHub Actions (chạy không cần máy) — máy tắt thì CI vẫn ra bản tin; local chỉ là lưới cuối khi CI trễ/chết/hết quota. Bản tin ra trễ bất thường → kiểm tra `state.py show` + `gh run list` trước khi đi truy bug.
- **Nhiều nơi cùng push vào `main`** (3 Action + routine quét). Cả 3 workflow đã có `pull --rebase` + retry 5 lần khi push bị từ chối; routine quét nếu push fail thì cũng `git pull --rebase origin main` rồi push lại.
- Việc quét thực tế (WebSearch/WebFetch/RSS) được giao cho các subagent chạy **model Sonnet** theo kiến trúc ở trên — session điều phối review + gộp kết quả, chạy script, commit/push. KHÔNG đọc `index.html` (172KB) trực tiếp — dùng `scripts/add_news.py`.
- **Bài học lần quét đầu 10/07/2026** (đã xử lý): tỷ lệ loại tin cao do (1) Haiku yếu → đã đổi Sonnet; (2) agent thiếu danh sách chống trùng đầy đủ chéo mục → đã bắt buộc nhúng nguyên khối `--recent-titles` cho mọi agent; (3) không có kiểm tra máy → đã thêm guardrail trong script; (4) WebFetch lỗi 403 hệ thống nên không tự verify link được — nếu sau này WebFetch ổn định, có thể thêm 1 pass verify `sourceUrl` bằng WebFetch trước khi publish (tùy chọn, tốn token).
- **Đã thử và KHÔNG khả thi**: dùng `curl` thuần trong Bash để tự kiểm tra link chết (`sourceUrl`) trước khi publish — môi trường chặn `curl`/kết nối HTTPS thô tới domain ngoài ở tầng network policy (chỉ tool WebFetch/WebSearch mới có đường truy cập web được duyệt riêng). Đừng thử lại `curl -I` để check link — sẽ luôn bị từ chối (403 ở tầng proxy). Nếu cần verify link, phải dùng WebFetch (tốn token hơn) — hiện KHÔNG bắt buộc làm bước này, dựa vào quy tắc "không chắc link thì bỏ" là chính.

---

> 📄 **BÀI HỌC GHI SỔ SONG SONG (xẻ từ `~/.claude/CLAUDE.md` mục 17, ngày 31/07/2026)** → [`docs/luat-lich-su.md`](docs/luat-lich-su.md) — bài học xẻ từ CLAUDE.md toàn cục 31/07

