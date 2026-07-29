# Điểm Tin Thế Giới — quy tắc quét tin

Trang tin tĩnh (PWA) tiếng Việt, deploy tự động lên GitHub Pages khi push vào `main`.

## ⚠️ CẬP NHẬT PHẠM VI 2026-07-23 (chỉ thị Huy — GHI ĐÈ các mục "Chỉ tiêu số lượng", "Kiến trúc quét", "Chu kỳ bản tin" bên dưới)
Bản tin **2 phiên/ngày, CÙNG 5 chủ đề** (chỉ thị Huy 26/07/2026): **TỐI 21:00** và **SÁNG SỚM 04:00**
(đêm VN = ngày làm việc Mỹ nên nhiều tin mới; cả 2 phiên đều gửi email). Mốc CHÍNH chạy trên **GitHub
Actions** `claude-web-scan.yml` (giờ VN: tối **21:00** + vét 22:00, sáng sớm **04:00/05:00** — máy Mac tắt vẫn ra bản
tin); scheduled task local `web-scan` là DỰ PHÒNG cho **CẢ HAI** phiên (cron `30 4,5,21 * * *` giờ VN):
CI không quét thì 30 phút sau local nhảy vào, CI đã xong/đang chạy thì local SKIP êm qua khoá `state.py`.
**Đổi 27/07/2026 (chỉ thị Huy):** mốc CI sáng dời 04:30 → **04:00** và phiên sáng sớm **CÓ dự phòng local
04:30/05:30** — vì sáng 27/07 cron CI 04:30 không nổ (GitHub hay trễ/bỏ cron lúc tải cao) mà phiên sáng
khi đó không có lưới local nên suýt mất trắng bản tin. Xen kẽ đầy đủ: **CI 04:00 → local 04:30 → CI 05:00
→ local 05:30**. Local chỉ chạy khi máy đã thức: cần lịch `pmset repeat wakeorpoweron … 04:25`.
**⏰ HẠN CHÓT EMAIL TỐI 22:00 (chỉ thị Huy 27/07/2026):** email bản tin tối phải tới hộp thư **muộn nhất
22:00**, nên phiên tối tính NGƯỢC từ mốc cuối chứ không phải mốc đầu — quét ~20' (đo thật 16–21') +
email ~20 giây ⇒ lớp cuối phải fire chậm nhất **21:15**, và lớp cuối phải là LOCAL vì cron GitHub trễ
5–20', còn task local đúng giờ hơn. Phiên tối vì thế là **2 lớp TRONG HẠN: CI 21:00 → local 21:15**,
cộng **1 lớp VÉT ngoài hạn: CI 22:00** (chỉ chạy khi cả hai lớp trên đều chết — GitHub bỏ cron *và* máy
Mac ngủ; email hôm đó ~22:22, quá hạn nhưng thà muộn còn hơn mất bản tin). **KHÔNG dời 2 lớp đầu trễ
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
   **MỞ RỘNG 27/07/2026: tin liên quan tới CÁC NƯỚC KHÁC trong khu vực Biển Đông** — Malaysia, Indonesia,
   Brunei, Đài Loan, Việt Nam, và hoạt động của Nhật/Ấn/Hàn tại vùng biển này; đàm phán COC ASEAN–Trung
   Quốc; các thực thể Natuna, Bãi Tư Chính, Luconia, Bãi Cỏ Rong. → `worldNews`.
3. **CNQS Mỹ** — khí tài/hệ thống cụ thể. → `usNews`, cat `Công nghệ quân sự`.
   ⏳ **KHUNG NGÀY NỚI RIÊNG: lùi tới 3 ngày** (chỉ thị Huy 27/07/2026 — "quét ngày 27 thì có thể lấy tin
   xuống tận ngày 24"), trong khi 4 chủ đề còn lại vẫn chỉ hôm nay + hôm qua. Lý do: tin khí tài/hợp đồng
   đăng thưa, cuối tuần Mỹ gần như trắng. Cưỡng bức bằng `MAX_AGE_DAYS_CNQS = 3` trong `add_news.py`
   (áp theo **category** `Công nghệ quân sự`) và `CNQS_LOOKBACK_DAYS` trong `harvest.py` — sửa một bên
   phải sửa bên kia.
4. **Mỹ–Mali** — Mỹ cân nhắc/không kích JNIM ở Sahel. → `usNews`, dossier `🟤 Mỹ – Mali`.
5. **Tập trận Predator's Run 2026** — diễn biến tới ~29/7. → `exerciseUpdates` (tên khớp).

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
| Sáng sớm (fire 04:00–05:30) | `Diem-tin-sang-som-5h-<YYYY-MM-DD>.docx` |
| Tối (fire 21:00–22:30) | `Diem-tin-toi-21h-<YYYY-MM-DD>.docx` |

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

### ⛔ "THIẾU SECRET → THOÁT ÊM" ĐÃ BỎ (siết 27/07/2026) — thiếu secret nay là job ĐỎ

**Cơ chế gây vấn đề:** chốt `thiếu TELEGRAM_BOT_TOKEN/CHAT_ID → in cảnh báo rồi exit 0` chỉ bảo vệ
đúng MỘT ca: **CHƯA CẤU HÌNH** (repo mới, chưa ai cắm secret — không có gì để hỏng). Cả hai secret
đã cắm lúc **07:13 ngày 27/07/2026**, nên từ giờ chốt đó không bảo vệ gì nữa mà chỉ **CHE** ca secret
bị xoá · bot bị `/revoke` · gõ nhầm tên secret. Khi đó phiên 21:00/22:00 chạy **XANH** mà kênh câm —
và Telegram nay là **kênh DUY NHẤT**, tức mất trắng bản tin không một dấu hiệu. Cùng lớp lỗi bắt được
ở app Rèn cùng ngày: `TELEGRAM_BOT_TOKEN` chưa từng đặt mà run 30250807802 vẫn *success* 10 giây suốt.

**Luật nằm ở MỘT chỗ:** `scripts/tg_api.py:kiem_cau_hinh()` — `send_telegram.py` và `canary.py` gọi
chung. Đừng để mỗi script tự viết luật: hai bộ luật song song chắc chắn lệch, mà lệch âm thầm.

| Tình huống | Kết quả |
|---|---|
| Đủ secret | chạy bình thường |
| Thiếu 1 hoặc CẢ HAI secret | **exit 1 → job ĐỎ**, in rõ secret nào thiếu + cách cắm lại |
| `TELEGRAM_BAT_BUOC='0'` | thoát êm exit 0 — kênh tắt CÓ CHỦ Ý |
| `DRY_RUN=1` | không cần secret |

⚠️ **KHÔNG chép nguyên logic của Rèn sang.** Rèn có BA secret nên còn suy được ý định từ những cái
còn lại ("có cái này mà thiếu cái kia → gãy"). Ở đây chỉ có HAI, và ca đáng sợ nhất là **mất sạch cả
hai** — đúng cái ca mà luật của Rèn lại đọc thành "chưa cấu hình" rồi thoát êm. Vì thế ý định phải
**khai bằng lời** (`TELEGRAM_BAT_BUOC`), không suy từ secret.
⚠️ **Mặc định là BẮT BUỘC**, không phải "tuỳ": quên đặt biến thì kêu (sửa được), chứ không tạo vùng
câm mới. Muốn tắt kênh thì đặt `TELEGRAM_BAT_BUOC: '0'` cạnh `GUI_EMAIL: '0'` trong workflow.
⚠️ **Thêm secret Telegram mới thì phải thêm vào `kiem_cau_hinh()`**, không thì nó lọt vào vùng câm.

**Ngoại lệ DUY NHẤT — `telegram-bot.yml` (bot hỏi-đáp) vẫn thoát êm**, có chủ ý: cron 5 phút nên mất
secret là **~288 job đỏ/ngày**, mà cảnh báo kêu liên tục thì Huy tắt thông báo và mất luôn cảnh báo
THẬT của bản tin; ngoài ra bot có phản hồi tự nhiên (nhắn mà không thấy trả lời là biết ngay), khác
hẳn bản tin — im lặng ở bản tin không phân biệt được với "hôm nay không có tin". Bù lại nó in
`::warning::` để trang run vẫn có dấu vết.

**Vá kèm cùng lớp lỗi — nhánh `.docx` của `send_telegram.py`.** Trước đây *"không có file .docx →
return 0"* gộp chung hai ca khác hẳn nhau; nay tách:
| Ca | Kết quả |
|---|---|
| `make_docx.py` chạy xong, in `DOCX=` **rỗng** = hôm nay 0 tin | exit 0 — im lặng đúng |
| `make_docx.py` rc≠0 · không in dòng `DOCX=` · không spawn được | **exit 1** (in kèm stdout/stderr) |
| `DOCX_PATH` workflow truyền vào mà **file không tồn tại** | **exit 1** — bước dựng đã hỏng |

Nghiệm thu 27/07 — chạy thật **13/13 ca đúng**: mất cả hai secret → 1 · mất một secret → 1 ·
`TELEGRAM_BAT_BUOC=0` → 0 · `DRY_RUN` → 0 · `--morning` mất secret → 1 · canary mất secret khi bản tin
đang hụt → 1 (ca tệ nhất: canary câm là hỏng chồng hỏng) · canary tắt chủ ý → 0 + `::warning::` ·
4 nhánh docx → 1/1/0/1.

📌 **`DISCORD_WEBHOOK` vẫn nằm trên repo** (đặt 24/07) dù đã bỏ Discord — **không script/workflow nào
đọc nó**, nên nó KHÔNG rơi vào chốt nào và không tạo vùng câm. Là secret rác, xoá được bằng
`gh secret delete DISCORD_WEBHOOK -R huyneo1101-dotcom/diem-tin-the-gioi` — nhưng xoá là mất URL
webhook (khó đảo ngược) nên **chờ Huy quyết**, đừng tự xoá.

## ⚠️ HAI PHIÊN QUÉT + HAI EMAIL (chốt 24/07/2026 — GỘP NƠI KÍCH 28/07/2026)
> **28/07/2026 (chỉ thị Huy: *"sự kiện sáng thì quét gộp với quét tin 4h sáng cũng được"*):**
> pipeline `event-scan` KHÔNG còn là phiên quét riêng — nó chạy NGAY SAU bản tin 5 chủ đề, trong
> CÙNG session của phiên SÁNG SỚM. Còn **2 lần quét thật/ngày** (tối + sáng sớm), không phải 3.
> `claude-event-scan.yml` đã XOÁ; task local `event-scan-diem-tin` đã TẮT. Nhưng **khoá/commit/
> email của hai pipeline vẫn TÁCH RIÊNG như cũ** — chỉ nơi kích (session nào gọi) là gộp lại, xem
> `docs/routine-web-scan.md` Bước 4 + `.github/prompts/web-scan-ci.md` BƯỚC 6.
- **Bản tin (TỐI 21:00 + SÁNG SỚM 04:00)** — CI `claude-web-scan.yml` là mốc chính (tối 21:00 + vét 22:00, sáng sớm 04:00/05:00 VN), local dự phòng CẢ HAI phiên bằng **2 task tách riêng**: `web-scan-diem-tin` (sáng 04:30/05:30) và `web-scan-diem-tin-toi` (tối 21:15): 5 chủ đề (xem banner trên). Commit
  `Cap nhat ban tin ...` → `notify-email.yml` gửi **email tối** (tiêu đề điểm tin + .docx đính kèm).
- **Phiên SÁNG (event-scan)** — chạy NGAY SAU bản tin 5 chủ đề, trong CÙNG job/session của phiên
  SÁNG SỚM ở trên (CI `claude-web-scan.yml` 04:00/05:00 + local `web-scan-diem-tin` 04:30/05:30 —
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

### 📩 EMAIL TỐI GỒM NHỮNG GÌ (chỉ thị Huy 27/07/2026 — quy tắc chốt)

> **Email tối = TOÀN BỘ tin đã quét được trong ngày, TRỪ ba loại:**
> 1. tin đã quét ở **phiên sáng sớm 04:00/05:00** (chúng đã đi trong email `📰 … BUỔI SÁNG`);
> 2. tin **tập trận / sự kiện ngoại giao** (đã đi trong email `🎖️ Sự kiện & Tập trận`);
> 3. bài **think-tank** (`DATA.analyses` — cũng thuộc email sáng).
>
> **⇒ Tin quét TAY giữa ngày KHÔNG gửi email riêng — nó nằm chờ và dồn hết vào bản tin TỐI.**
> Nguyên văn Huy: *"tao quét tin 4h, rồi quét tin 8h45, rồi quét tay thêm hai lần trong ngày,
> thì tin buổi tối chỉ quét bình thường + các tin lấy được từ 2 lần quét tay đó thôi."*
>
> **⇒ VÀ NẾU ĐÃ LỠ GỬI EMAIL Ở LẦN QUÉT TAY ĐÓ, BẢN TỐI VẪN PHẢI CÓ CHÚNG.** Nguyên văn Huy:
> *"ví dụ mà tao quét tay 2 lần giữa ngày xong có gửi email đi thì email tối vẫn phải có các
> tin đó."* Chỉ tin của **ca SÁNG SỚM** mới bị loại khỏi bản tối, không phải mọi tin đã gửi.

**Cơ chế bảo đảm điều đó:** bước `Ghi sổ đã gửi` chỉ chạy khi `push` **HOẶC** có input
`tu_dong == '1'`. Người bấm tay thì không truyền cờ → **KHÔNG ghi sổ** → tin không bị đánh dấu
"đã gửi" → bản tối vẫn liệt kê. Nói cách khác **chỉ lần gửi của một ca chính thức mới để lại dấu
trong sổ**; mọi lần gửi tay đều là "gửi thêm", không trừ đi thứ gì của bản tối.

⚠️ **ĐIỀU KIỆN CŨ CHỈ CÓ `event_name == 'push'` — SAI TỪ KHI CÓ CI, vá 28/07/2026.** GitHub cố ý
KHÔNG cho push bằng `GITHUB_TOKEN` kích workflow khác (chống đệ quy), nên `claude-web-scan.yml` /
`claude-event-scan.yml` buộc phải tự gọi `gh workflow run` — tức **mọi bản tin do CI ra đều là
`workflow_dispatch` và rơi hết khỏi sổ**. Hai quy tắc đúng riêng lẻ, ghép lại thì thủng.
Đo thật sáng 28/07: bản tin sáng tới tay Huy lúc 04:18 (9 tin, kèm .docx) mà sổ trống trơn ⇒
(a) canary ca `sang` kêu oan "hỏng ở khâu GỬI"; (b) nặng hơn — sổ chính là thứ lọc "tin đã gửi",
nên bản tin TỐI cùng ngày sẽ liệt kê lại đúng 9 tin đó, **lặp lại lỗi Huy đã bắt hôm 27/07**.
Nay CI kích kèm `-f tu_dong=1`; nhánh `MODE=test` cố tình KHÔNG truyền (test không để dấu vết).
**Bài học:** phân biệt bằng **Ý ĐỊNH khai bằng lời**, đừng suy từ **KIỂU SỰ KIỆN** — cùng một lỗi
với `TELEGRAM_BAT_BUOC` ở mục "thiếu secret" phía trên. Thêm đường kích notify mới thì phải
truyền cờ này, không thì nó lọt vào vùng câm y hệt.

**📱 TELEGRAM ÁP Y HỆT EMAIL** (Huy chốt 27/07: *"và với telegram thì cũng vậy"*). Không phải nhờ
chép lại luật mà nhờ **dùng chung hạ tầng** — giữ nguyên thế này, đừng tách ra:
- bước `Gửi Telegram` nằm trong CHÍNH `notify-email.yml` và dùng CHUNG `steps.chk.outputs.go`, nên nó
  qua đúng hai cổng (commit + khung giờ) — quét tay giữa ngày thì Telegram cũng im, y như email;
- `send_telegram.py` gọi `md.loc_chua_gui(...)`, tức đọc CHUNG `logs/da-gui-email.json` — nên gửi tay
  không ghi sổ thì bản Telegram buổi tối cũng vẫn có tin của lần quét tay đó.
⚠️ Đừng cho Telegram một cổng riêng hay một sổ riêng: hai bộ luật song song chắc chắn sẽ lệch nhau, và
lệch âm thầm — email đúng còn Telegram sai thì rất lâu mới phát hiện.

**CHỈ CÓ 2 CA BẮN EMAIL BẢN TIN MỖI NGÀY** — `notify-email.yml` có **hai cổng**, phải qua CẢ HAI:
| Cổng | Điều kiện |
|---|---|
| 1. commit | message bắt đầu `Cap nhat ban tin` |
| 2. **khung giờ VN** | **03:30–07:00** (ca sáng sớm) hoặc **≥ 20:30** (ca tối) |

Ngoài hai khung đó → **không gửi**, chỉ in `::notice::` và tin nằm chờ ca tối. `workflow_dispatch`
(chạy tay) vẫn luôn gửi — dùng để test hoặc gửi bù khi lỡ ca.
⚠️ Cổng 2 thêm 27/07/2026 vì trước đó chỉ xét commit message: **mọi lần quét TAY giữa ngày đều bắn
một email riêng** — đo thật, lần quét tay 11:12 ngày 27/07 đã gửi email kèm .docx. Tệ hơn, tin đó vào
sổ đã gửi nên bản tin TỐI lại LOẠI chúng — đúng ngược ý Huy.
⚠️ Trong script phải viết `gio=$((10#$(… date +%H%M)))`: `date +%H%M` cho `0845`, bash coi số 0 đầu là
**bát phân** nên `[ 0845 -ge 330 ]` vỡ với *"value too great for base"* — hỏng đúng toàn bộ ca sáng.

**Vì sao cần quy tắc này:** `notify-email.yml` kích theo **PUSH** chứ không theo cron, nên phiên sáng
sớm và phiên tối đều bắn email — mà cả ba kênh (thân email, `.docx`, tin nhắn Telegram) đều từng chọn
tin bằng luật "cùng ngày" `_addedDate == generatedAt`. Kết quả: bản tối liệt kê lại y nguyên tin đã gửi
sáng. Huy bắt lỗi 27/07.

**Cơ chế thực thi — SỔ ĐÃ GỬI `logs/da-gui-email.json`** (`.github/scripts/so_da_gui.py`), KHÔNG dùng mốc
giờ: `_addedDate` chỉ có độ phân giải NGÀY, và mốc giờ vỡ ngay khi bản tin gửi trễ qua nửa đêm, phải gửi
lại tay, hoặc mốc dự phòng chạy bù. Sổ URL thì đúng trong mọi trường hợp đó.

| Thứ | Lọc sổ? | Vì sao |
|---|---|---|
| **Thân email tối** (`send-email.js`) | **CÓ** | là thông báo — lặp tin đã báo thì thừa |
| **Tin nhắn Telegram** (`send_telegram.py`) | **CÓ** | cùng vai với thân email |
| **File `.docx` đính kèm** (`make_docx.py`) | **KHÔNG** | là **bản tổng hợp CẢ NGÀY** Huy lưu lại — chỉ thị Huy: *"gửi file word tối nay… thì gộp cả 11 tin hôm nay đó vào"* |

Ba cái bẫy đã vấp thật, đừng lặp lại:
- **Ghi sổ phải là bước CUỐI**, sau CẢ email lẫn Telegram. Ghi sớm hơn thì Telegram đọc sổ thấy chính lô
  vừa gửi và lọc sạch → **Telegram rỗng**.
- **Chỉ ghi sổ khi `github.event_name == 'push'`.** Hai lần chạy tay `workflow_dispatch` lúc 14:24/14:36
  ngày 27/07 đã ghi 11 tin của cả ngày vào sổ, suýt làm bản tối bỏ sạch chúng — trong khi chúng được quét
  rải rác **09:13–14:17**, không phải phiên sáng. Chạy tay là để TEST, không được để dấu vết lên bản thật.
- **`notify-morning.yml` ghi sổ với `--chi events`**, tuyệt đối không ghi `usNews`/`worldNews`: email đó
  CHỈ gửi sự kiện, ghi thừa là **xoá sổ tin thường trước khi chúng kịp lên bản tin tối** — mất tin, chứ
  không phải trùng tin.
- `send_telegram.py` dựng `.docx` **TRƯỚC** khi xét `total == 0`, và `total == 0` vẫn gửi file kèm — nếu
  không, hôm nào mọi tin đều đã báo là Huy mất luôn file tổng hợp.

### 🆕 Mới trên web + 💡 Có thể bạn chưa biết — trong email SÁNG (chỉ thị Huy 27/07/2026)
Email sáng có thêm 2 mục cuối, nguồn dữ liệu là **`whats-new.json` ở gốc repo** (`send-morning-email.js`:
`readWhatsNew` · `freshFeatures` · `tipOfDay` · `featuresHtml` · `tipHtml`):
| Mục | Lấy gì | Quy tắc |
|---|---|---|
| 🆕 Mới trên web | `features[]` có `date` trong **7 ngày** gần nhất so với `DATA.generatedAt`, tối đa **3** mục, mới nhất trước | Chỉ ghi tính năng **NGƯỜI ĐỌC nhìn thấy**. KHÔNG ghi việc sửa routine/CI/quy tắc quét — người đọc không quan tâm và cũng không kiểm được |
| 💡 Có thể bạn chưa biết | 1 mẹo trong `tips[]`, chọn bằng `số ngày kể từ epoch % số mẹo` | **Xoay theo NGÀY, không random**: chạy lại cùng ngày (retry/`workflow_dispatch`) ra cùng mẹo; mẹo thêm vào cuối mảng chắc chắn tới lượt |

**Gate gửi email KHÔNG đổi** — vẫn phải có sự kiện/tập trận mới hoặc báo cáo tuần mới. Hai mục này ăn
theo email đã chắc chắn gửi; một mẹo dùng web KHÔNG đáng một lá mail. **Chốt an toàn** giống mục "Chủ đề
thiếu" của `send-email.js`: thiếu file · JSON lỗi · mảng rỗng → **bỏ cả mục, chỉ log**, không làm vỡ email.

⚠️ **Ra tính năng mới trên web thì PHẢI thêm một mục vào `whats-new.json`** — không thêm thì người đọc
không bao giờ biết web có gì mới (chính là lý do Huy yêu cầu mục này). Mọi câu chữ trong file **phải đối
chiếu thật với `index.html`** trước khi ghi (nhãn tab, tên nút, đường dẫn trang) — hứa tính năng chưa có
là lỗi nặng hơn không giới thiệu gì. Xem `_doc` trong chính file đó.
**Máy Huy KHÔNG có `node`** → kiểm script email bằng `/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Helpers/jsc`
với stub `require`/`process`/`console` (đã dùng thật 27/07, bắt được cả nhánh thiếu file).

#### GIAO DIỆN email sáng = mẫu 4 "Digest tối giản" (Huy chốt 27/07/2026)
Chọn từ 5 mẫu trong `docs/mockup-newsletter-sang-v1.html` (Intel Brief · báo in cổ điển · thẻ hiện đại ·
**digest tối giản ← đang dùng** · bảng điều khiển). Đặc trưng phải GIỮ khi sửa về sau:
- **KHÔNG nền màu, KHÔNG thẻ bo tròn** — chỉ typography + số mục ở lề + đường kẻ mảnh `#eceff3`.
  Đây cũng là lý do mẫu này an toàn nhất: không ô nào dựa vào `background-color` nên dark mode của
  Gmail/Outlook không thể tạo ra cảnh chữ trắng trên nền trắng.
- **Số mục chạy LIÊN TỤC** qua mọi khối có nội dung (mỗi sự kiện một số → báo cáo tuần → Mới trên web),
  khối rỗng thì số dồn lên, không để lỗ `01 → 03`. Mục mẹo dùng 💡 thay số.
- Hằng số màu ở đầu phần giao diện: `ACCENT` (tập trận `#b45309` hổ phách · ngoại giao `#0f766e` xanh
  mòng) · `INK`/`BODY`/`MUTED`/`RULE`. Sửa màu thì sửa ở đó, đừng rải hex trong từng hàm.
- `evBlockHtml` có **2 nhánh**: 1 tin mới → tít là TIÊU ĐỀ TIN, tên sự kiện lùi xuống dòng meta; nhiều
  tin mới → tít là TÊN SỰ KIỆN rồi liệt kê từng tin. Sửa một nhánh thì kiểm luôn nhánh kia.

**Xem trước KHÔNG gửi thật:** `.github/scripts/preview-morning-email.jsc.js` — nó `load()` nguyên
`send-morning-email.js` (không copy code, khỏi lệch) rồi dựng HTML từ dữ liệu thật trong `index.html`:
```
/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Helpers/jsc /Users/Huy/Claude/diem-tin-the-gioi/.github/scripts/preview-morning-email.jsc.js > /Users/Huy/Claude/diem-tin-the-gioi/docs/preview-email-sang-mau4.html
```
Mở file HTML đó trong trình duyệt để soi. Bản xem trước gần nhất đã commit sẵn ở đường dẫn trên.
⚠️ Link "Đọc báo cáo tuần đầy đủ" đã **bỏ `#analysis`** (trỏ thẳng `WEB_URL`): index.html không đọc
`location.hash` nên hash cũ chỉ mở trang chủ — hứa sai chỗ nhảy tới. Nếu sau này web có hash routing
thì mới trỏ lại `#analysis`.

## Tab "Cà phê" (ngoài chủ đề tin — thêm 24-25/07/2026)
Tab **☕ Cà phê**: tìm quán cà phê làm việc HN, xếp theo khoảng cách từ điểm xuất phát (Giảng Võ/Trường Chinh/GPS). Dữ liệu `DATA.workCafes` (embed index.html); code `renderCafes`/`cf*`/CSS `.cf-*`. Scheduled task local **`cafe-rating-retry`** (`15 9 * * 2,5`) vét dần rating Google còn thiếu qua `scripts/cafe_ratings.py` (--missing/--apply), commit **`Cap nhat rating quan ca phe: ...`** — tiền tố này KHÔNG khớp gate email nên không gửi mail. Chi tiết: memory `diem-tin-tab-cafe`.

## 📨 TELEGRAM — kênh gửi thứ hai + lớp nguồn thứ ba (thêm 27/07/2026, chỉ thị Huy)

### Gửi bản tin qua Telegram
`.github/scripts/send_telegram.py` — step Telegram nằm SAU step email trong cả hai workflow.
⚠️ **Hai câu mô tả cũ ở đây đã BỊ ĐẢO, đừng đọc theo trí nhớ:** (a) *"Telegram chạy song song,
KHÔNG thay email"* → sai từ 27/07, **email đã tắt, Telegram là kênh DUY NHẤT** (`GUI_EMAIL='0'`);
(b) *"`continue-on-error: true`, Telegram hỏng không được làm đỏ"* và *"thiếu secret thì thoát êm
exit 0"* → **cả hai đã bỏ**: `continue-on-error` gỡ khỏi hai bước gửi, và thiếu secret nay là job
ĐỎ (xem mục "⛔ THIẾU SECRET → THOÁT ÊM ĐÃ BỎ" ở trên).

| Bản tin | Workflow | Lệnh | Nội dung |
|---|---|---|---|
| 5 chủ đề (tối + sáng sớm) | `notify-email.yml` | `send_telegram.py` | Tiêu đề tin theo 3 mục + "Chủ đề thiếu và lý do" + **file .docx đính kèm** |
| Sự kiện & Tập trận (sáng) | `notify-morning.yml` | `send_telegram.py --morning` | Sự kiện/tập trận mới + báo cáo tuần + think-tank + Mới trên web + mẹo |

**📐 GIÃN DÒNG — mỗi ý một khối, các khối cách nhau MỘT DÒNG TRỐNG (chỉ thị Huy 28/07/2026):**
nguyên văn *"giữa các tin và giữa các ý thì xuống dòng rồi cách 1 dòng nữa cho dễ đọc"*. Trước đó
mọi dòng dính liền nhau nên khối Think-tank và "Mới trên web" đọc thành một mảng chữ đặc.
Luật nằm ở **ĐÚNG MỘT chỗ: `send_telegram.py:chunk()`** — nó vừa nối khối bằng `\n\n` vừa cắt
message ≤ `MAX_LEN`; **cả bản tối lẫn bản sáng đều gọi hàm này**, đừng tách ra thành hai vòng nối
riêng như bản cũ (hai bộ luật song song chắc chắn lệch).
| Là MỘT khối (dính nhau bằng `\n` đơn) | Là HAI khối (cách nhau dòng trống) |
|---|---|
| Tên sự kiện + dòng `<i>ngày · địa điểm</i>` | Sự kiện này với sự kiện kia |
| Tít bài think-tank + câu *điều rút ra* | Bài think-tank này với bài kia |
| Mẹo: tiêu đề + mô tả + đường dẫn | Từng tin, từng mục "Mới trên web", từng luận điểm báo cáo tuần |

⚠️ **Đừng thêm `"\n"` vào đầu chuỗi tiêu đề mục nữa** — cách cũ tự chèn khoảng cách bằng tay; nay
`chunk()` lo hết, thêm nữa là ra **hai** dòng trống.
⚠️ **Luận điểm báo cáo tuần trước gộp bằng `" · "`** thành một đoạn chạy dài — nay mỗi luận điểm một
dòng `– …` riêng. Đây chính là chỗ Huy gọi là "giữa các ý".
⚠️ Giãn dòng làm message DÀI THÊM ~15% ký tự → có thể tăng số message Telegram. Đó là đánh đổi đã
chấp nhận; `MAX_LEN` vẫn cắt đúng ranh giới khối nên không có tin nào bị xé đôi.

**KHÔNG viết lại logic chọn tin ở phía Python.** Nhánh tối `import` thẳng `make_docx.py`
(`pick_items`/`build_sections`) nên Telegram luôn đúng bằng bộ tin trong .docx. Nhánh sáng đọc
`/tmp/morning-telegram.json` do **`send-morning-email.js` tự ghi ra trước khi gửi mail** — nhờ
vậy **gate gửi của hai kênh không bao giờ lệch**: không có gì mới thì không có payload, Telegram
im đúng lúc email im. Ghi TRƯỚC `sendMail` chứ không phải sau, để Gmail chết thì Telegram vẫn tới.

Secret cần: `TELEGRAM_BOT_TOKEN` (@BotFather) + `TELEGRAM_CHAT_ID` (nhiều nơi nhận thì ngăn bằng
dấu phẩy). Cài một lần bằng `python3 scripts/telegram_setup.py` (kiểm token · tự dò chat_id ·
gửi tin thử · `gh secret set`).

⚠️ **GỌI BOT API PHẢI QUA `curl`, KHÔNG QUA `urllib`** (`scripts/tg_api.py` — dùng chung cho cả
setup lẫn send). Máy Huy có thiết bị chèn cert ở giữa nên `urllib` trượt thẳng
`CERTIFICATE_VERIFY_FAILED: self-signed certificate in certificate chain`; `curl` tin được vì
đọc keychain macOS. **Cài `certifi` KHÔNG cứu** — cert chèn không nằm trong bundle CA nào. Cả
repo vốn đã đi bằng curl (`harvest.py`, `telegram_harvest.py`), đây là về đúng một đường.
Kiểm nhanh mà không cần token thật: gọi `call('111:GIA','getMe')` phải trả `error_code 401` —
ra 401 tức mạng + parse JSON đều thông, chỉ token sai.

⚠️ **TOKEN KHÔNG ĐƯỢC HIỆN RA MÀN HÌNH.** `telegram_setup.py` nhận token bằng `getpass`, và
`tg_api.py` đưa URL qua `curl -K -` (stdin) thay vì tham số dòng lệnh — nếu không, token nằm
trong `ps aux` và trong lịch sử terminal. Bản đầu dùng `input()` nên token in nguyên văn lên
màn hình; ảnh chụp màn hình gửi đi là lộ luôn (đã xảy ra 27/07 → phải `/revoke` lấy token mới).
Lộ token thì vào @BotFather gõ `/revoke`, rồi chạy lại `telegram_setup.py`.

Xem trước không gửi thật:
```
DRY_RUN=1 python3 .github/scripts/send_telegram.py
/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Helpers/jsc /Users/Huy/Claude/diem-tin-the-gioi/.github/scripts/preview-morning-telegram.jsc.js
```
File `preview-morning-telegram.jsc.js` chạy NGUYÊN `main()` của send-morning-email.js với
nodemailer giả — kiểm được cả đoạn ghi payload, thứ mà kiểm cú pháp không bắt được (máy Huy
không có `node`). Nó KHÔNG set `PREV_HTML` nên coi mọi sự kiện là mới (22 cái) — đừng lấy con
số đó đánh giá độ dài tin nhắn hằng ngày. Trần **12 sự kiện/tin nhắn** (`MORNING_MAX_EVENTS`),
phần cắt được nói rõ bằng dòng "… và N sự kiện nữa", không im lặng.

### 🐤 CANARY — báo khi bản tin KHÔNG tới nơi (thêm 27/07/2026, chỉ thị Huy)
`.github/scripts/canary.py` + `.github/workflows/canary.yml`. Ngày bình thường nó **im lặng**;
chỉ nhắn Telegram khi bản tin đã hụt.

**Lỗ nó bịt:** mọi cảnh báo khác của repo đều do CHÍNH routine phát ra, nên chúng đòi routine
phải CHẠY mới báo được. Kiểu hỏng nguy hiểm nhất lại là **không chạy phát nào** — máy Mac đóng
nắp/caffeinate không giữ nổi · GitHub bỏ cron lúc tải cao (đã xảy ra sáng 27/07, chính vì thế
mới dời 04:30→04:00) · phiên chết trước khi push, mà `notify-email.yml` kích theo PUSH nên
không có push là không có gì hết. Cả ba đều **im lặng tuyệt đối**: Huy không phân biệt được
"hôm nay không có tin đáng" với "cả hệ thống chết từ chiều".

| Cron (VN) | Ca | Kiểm gì |
|---|---|---|
| **22:45** | `toi` | sổ `logs/da-gui-email.json` có dòng `buoi: toi` ngày hôm nay chưa |
| **06:15** | `sang` | như trên, `buoi: sang` |
| **07:00** | `sukien` | `logs/state.json` → `event-scan.lastSuccess.sang == hôm nay` |

⏰ **Mốc ca `sukien` đã dời HAI lần, đừng đọc theo trí nhớ:** 10:45 → **06:20** (28/07, khi
`event-scan` gộp vào phiên sáng sớm nên lớp cuối của nó trùng lớp cuối web-scan) → **07:00**
(29/07). Lần dời thứ hai vì 06:20 vẫn sát: local 05:30 + jitter ~3'30, quét bản tin 16–21',
rồi event-scan chạy TIẾP trong cùng session ~15–25' ⇒ xong đúng quanh 06:20 — canary kêu ngay
lúc phiên còn đang làm đúng việc. Cùng lỗi với ca `toi` từng kêu khi lớp vét 22:00 chưa gửi xong.

**Hai nguyên tắc, đừng "dọn cho gọn" mất:**
1. **Kiểm ĐẦU RA, không kiểm quy trình.** Không hỏi "job có chạy không" (job xanh mà gửi rỗng
   vẫn là hỏng) mà hỏi "bản tin có tới tay không". Bằng chứng là **sổ đã gửi** — thứ chỉ được
   ghi ở BƯỚC CUỐI sau khi đã gửi xong mọi kênh, nên là dấu vết việc-đã-làm chứ không phải lời
   tự khai của một job.
2. **Người báo phải KHÁC người làm.** Workflow riêng, cron riêng, `permissions: contents: read`,
   không import gì của đường quét. Chết cùng lúc với routine thì nó vô nghĩa.

⏰ **Chạy sau LỚP CUỐI, không phải sau HẠN CHÓT.** Hạn email tối là 22:00 nhưng lớp vét CI 22:00
gửi tới ~22:22 — đó là thiết kế bình thường. Kêu lúc 22:05 là kêu oan, mà cảnh báo kêu oan vài
lần là hết ai đọc, lúc đó canary chết thật. Đánh đổi có chủ ý: báo trễ hạn ~45' nhưng không nhiễu.

**Ba ca chẩn đoán** — canary phải nói HỎNG Ở KHÂU NÀO, không chỉ "có gì đó sai": sổ có dòng →
im lặng · sổ trống mà state DONE → *hỏng khâu GỬI, hoặc phiên 0 tin nên không có commit kích
notify* · sổ trống và state chưa DONE → *hỏng khâu QUÉT*, in kèm `lastRunAt/lastStatus/note`.

📅 **NGÀY CỦA CA ≠ NGÀY TRÊN ĐỒNG HỒ (vá 28/07/2026).** Canary ca `toi` cron 22:45 VN nhưng
GitHub chạy lúc **00:23** — trễ 1h38, ăn hết biên 1h15 tới nửa đêm. Qua nửa đêm thì "hôm nay"
nhảy sang ngày mới, canary đi hỏi *"bản tin tối NGÀY MAI đâu"* rồi kêu oan, trong khi bản tối
27/07 đã gửi 21:37 và nằm trong sổ. Tin nhắn tự mâu thuẫn: tiêu đề "CHƯA có" mà dòng dưới in
`lastRun … DONE`. Nay `canary.py:ngay_cua_ca()` quy đổi: **ca `toi`, mốc trước 12:00 thuộc về
NGÀY HÔM TRƯỚC** — áp cho CẢ lúc canary chạy LẪN mốc `luc` đọc từ sổ (dùng chung một hàm, đừng
để mỗi bên tự tính), nhờ vậy bản tối trôi qua nửa đêm vẫn được tính đúng ca. Ca `sang` và
`sukien` cách nửa đêm >13 tiếng nên không quy đổi. **Dời cron sớm hơn KHÔNG chữa gốc** — độ trễ
cron GitHub không ép được, chỉ mua thêm biên.

**Ba giới hạn đã biết, đừng tưởng là bug:** (a) gửi TAY (bấm nút, không có `tu_dong=1`) cố ý
KHÔNG ghi sổ → hôm nào gửi bù bằng tay thì canary vẫn kêu, và như thế là đúng (ca tự động đã
hỏng thật);
(b) bước ghi sổ có `continue-on-error` + retry push 5 lần — hỏng cả 5 thì bản tin tới tay mà sổ
trống → kêu oan, ca này hiếm và đã có `::warning::` riêng; (c) ca `sukien` KHÔNG kiểm sổ vì
`notify-morning.yml` cố ý không gửi khi không có gì mới — "im lặng" ở đó là hành vi ĐÚNG.

⚠️ **Thiếu secret Telegram → exit 1 job ĐỎ** (siết 27/07/2026, câu cũ ghi "thoát êm exit 0" đã BỎ):
canary chỉ chạy tới khâu gửi khi bản tin ĐÃ hụt, nên nuốt lỗi ở đây là nuốt luôn tiếng kêu cuối cùng.
Kênh tắt có chủ ý (`TELEGRAM_BAT_BUOC='0'`) thì exit 0 nhưng vẫn in `::warning::` kèm nội dung cảnh
báo. Gửi được → exit 0; gửi hỏng → exit 1. Xem trước không gửi thật:
```
DRY_RUN=1 python3 .github/scripts/canary.py --ca toi
```

### Bot hỏi–đáp qua Telegram (thêm 27/07/2026 — "option 3", chạy MIỄN PHÍ)
Huy nhắn câu hỏi cho **@diemtin24h_bot**; workflow `telegram-bot.yml` (cron **mỗi 5 phút**)
đọc hàng đợi Telegram và chạy `claude -p` để trả lời, dùng **CHUNG secret
`CLAUDE_CODE_OAUTH_TOKEN`** với routine quét → **không phát sinh hoá đơn Claude API**.

🔎 **MỌI câu hỏi PHẢI được nghiên cứu, không chỉ lọc DATA (chỉ thị Huy 28/07/2026):**
*"yêu cầu với mọi câu hỏi phải tự nghiên cứu để đưa ra câu trả lời hoàn thiện và bao quát
nhất."* Trước đó bot CHỈ dùng `tra_cuu_tin.py` lọc từ DATA bản tin, WebSearch bị cấm dùng
cho việc trả lời (chỉ được dùng ở việc RIÊNG — đề xuất tin mới). Hệ quả: DATA thiếu là bot
nói thẳng "không có", dù thật ra tìm thêm là ra. Nay `.github/prompts/telegram-bot.md` bắt
buộc 2 bước cho MỌI câu hỏi thời sự: (1) DATA bản tin trước — rẻ, đã qua guardrail + chuẩn
nguồn 3 tầng; (2) LUÔN WebSearch/WebFetch thêm dù bước 1 đủ hay thiếu, vì bản tin quét theo
chu kỳ nên có thể trễ hàng giờ so với lúc Huy hỏi.

⚠️ **ĐẢO LẠI 28/07/2026 — bỏ nhãn tách "trong DATA" / "(ngoài bản tin)".** Bản đầu bắt trả
lời phải gắn `"(ngoài bản tin)"` cho tin tự tìm thêm; thực tế agent viết thành **hai đoạn
tách rời** ("Tra DATA bản tin: …" rồi xuống dòng "(Ngoài bản tin) …"), Huy bác vì đọc rời
rạc như hai câu trả lời dán lại. Nay **MỘT câu trả lời hợp nhất** — trộn DATA + nghiên cứu
thêm thành một mạch văn, không thuật lại "tao tra ở đâu". Độ tin cậy vẫn thấy được qua
**tên nguồn + link** trích kèm mỗi khẳng định (Reuters khác một blog vô danh) — không cần
nhãn riêng nữa.

⛔ **BẮT ĐƯỢC THẬT NGAY SAU ĐÓ, CÙNG NGÀY 28/07: "tên nguồn" không tự động ra "link bấm
được".** Một câu trả lời gói gọn nguồn vào dòng cuối *"Nguồn: Yahoo Finance, CBS News, NBC
News, Washington Post (xem link trong phần trên)"* — nhưng cả tin nhắn không một URL nào,
người đọc không bấm vào đâu được. Gốc rễ: `send_telegram.py:gui()` gửi **text thuần, KHÔNG
đặt `parse_mode`** (cố ý — để ký tự lạ không làm Telegram từ chối cả tin), nên **markdown
kiểu `[tên](url)` không render** — Telegram chỉ tự bấm được với **URL trần** đứng ngay
trong văn bản. Vá: `telegram-bot.md` bắt URL thật phải nằm NGAY CẠNH tên nguồn mỗi lần nhắc
tới, không gom vào một dòng "Nguồn: …" cuối tin mà không kèm URL. Không có URL cụ thể cho
một nguồn thì bỏ hẳn câu dựa vào nguồn đó, đừng nhắc tên suông.

⚠️ **KHÔNG lẫn với việc "đề xuất tin"** (mục dưới) — hai việc CÙNG dùng WebSearch nhưng
tiêu chuẩn khác hẳn: nghiên cứu-để-trả-lời thì tìm gì cũng được miễn có nguồn; còn đưa vào
`tin_de_xuat` là đề nghị lên bản tin CÔNG KHAI nên vẫn phải qua đúng khung hôm nay/hôm qua +
nguồn 3 tầng + tối đa 3 tin — tình cờ tìm thấy đúng loại đó thì lọc qua điều kiện rồi mới
đưa, không phải mọi thứ tìm được lúc trả lời đều tự động thành đề xuất.
⚠️ **Tốn thời gian hơn**, không phải chỉ tốn cron: bump `--max-turns` 60 → **90** vì giờ mỗi
lượt hỏi cộng dồn HAI vòng WebSearch (trả lời + đề xuất tin), thay vì một.

⛔ **Bắt được thật 28/07/2026: bot trả lời bằng tiếng Việt KHÔNG DẤU** ("Hien khong co tap
tran NATO..."). Không phải lỗi code — đã kiểm không script nào strip dấu (`grep unidecode/
normalize` ra rỗng), là agent tự viết vậy. Vá bằng chỉ dẫn tường minh trong
`telegram-bot.md` kèm ví dụ ĐÚNG/SAI cụ thể, vì câu cũ "Tiếng Việt, xưng tao" không đủ rõ
để chặn — mô tả gián tiếp qua CLAUDE.md không ăn chắc bằng ví dụ dán thẳng vào prompt.

### 🧠 Bot nhớ lịch sử chat gần đây (thêm 28/07/2026, Huy hỏi)

Mỗi lần bot chạy là một tiến trình GitHub Actions **hoàn toàn mới** — không tự nhớ gì giữa
hai lượt hỏi. Câu ellipsis kiểu *"còn trong tháng 8?"* không có nghĩa nếu đọc riêng lẻ. Vá
bằng cách ĐỌC LẠI dữ liệu đã ghi sẵn, không phải thêm bộ nhớ mới: bảng `dt_bot_hoi` đã lưu
mọi lượt hỏi-đáp từ 27/07 (`bot_luu.py` ghi ở cuối mỗi lượt), chỉ thiếu đường đọc lại nó
TRƯỚC khi trả lời.

`telegram_bot.py:lich_su_gan_day(chat)` — chạy trong bước `--doc` (rẻ, không cần `claude
-p`), gắn thêm field `lich_su: [{cau_hoi, tra_loi}]` vào mỗi lượt hỏi trong
`/tmp/tg-questions.json`. Ba giới hạn cố ý:
- **Lọc đúng `chat_id`** — lịch sử của Jay không bao giờ lẫn vào ngữ cảnh của Huy.
- **Tối đa 5 lượt, trong 1 tiếng gần đây** (`LICH_SU_GIOI_HAN`/`LICH_SU_PHUT`) — không lấy
  "toàn bộ lịch sử": câu hỏi hôm qua không cùng mạch chuyện với câu hỏi hôm nay, nạp vào
  chỉ gây nhiễu, nguy hơn nữa nếu bot coi nhầm đó là ngữ cảnh còn hiệu lực.
- **Cắt mỗi `tra_loi` cũ ở 500 ký tự** — một câu trả lời dài không được nuốt hết chỗ.

⚠️ **Chỉ để HIỂU Ý, không phải để CHÉP LẠI câu trả lời cũ** — nhắc thẳng trong
`telegram-bot.md`: đọc `lich_su` để biết đang hỏi tiếp cái gì, nhưng vẫn phải chạy đủ 2
bước (DATA + nghiên cứu thêm) ở mục trên, vì dữ liệu có thể đã đổi từ lượt trước tới giờ.

Đi qua đúng mã riêng `x-dt-key` đã dùng cho `ho_so_doc_gia.py` (đọc quyền hạn chế 2 bảng
`dt_*`, không phải service key mở toàn bộ database). Secret **`DT_BOT_KEY` mới cắm cho CI**
28/07/2026 (trước đó mã này chỉ có trên máy Huy, dùng cho routine local); thiếu secret thì
`lich_su_gan_day()` tự trả `[]` và `--doc` vẫn chạy bình thường — lịch sử là phần LÀM GIÀU
câu trả lời, không phải điều kiện cần.

⚠️ **ĐỘ TRỄ THẬT KHÔNG PHẢI 1–3 PHÚT — đo lại 28/07/2026: 66–148 PHÚT.** Câu "trễ 1–3 phút"
ở đây suy từ `cron: */5` chứ chưa ai đo. Thực tế 12 vòng gần nhất cách nhau 66 · 67 · 68 · 87 ·
90 · 110 · **148** phút — GitHub hạ ưu tiên mạnh cron tần suất cao trên repo public, không lần
nào gần 5 phút. **Không ép được** (cùng bản chất với cron canary trễ 1h38). Hệ quả đã vá:
`MAX_AGE_PHUT` 60 → **360**, vì câu hỏi rơi vào khoảng cách >60' bị vứt với lý do "quá cũ" — mà
`--doc` xác nhận offset ngay khi đọc nên câu đó **mất hẳn**, người hỏi không có dấu hiệu gì. Nay
bỏ câu quá cũ thì **nhắn cho người hỏi biết** thay vì chỉ in stderr.
Đánh đổi cũ vẫn đúng về bản chất (miễn phí, đổi lấy độ trễ), chỉ là con số lớn hơn nhiều.

**Vì sao GitHub bỏ mốc — đo chứ không đoán (28/07/2026, Huy hỏi "sao lại trễ vậy"):**
`startedAt − createdAt = 0 giây` ở **mọi** run schedule của repo ⇒ **không phải xếp hàng chờ
runner**, mà là GitHub *không tạo run*. `schedule` là dịch vụ best-effort trên hàng đợi dùng
chung: tải cao thì hoãn, hoãn đủ lâu thì **bỏ hẳn, không chạy bù**; repo public dùng runner
miễn phí nên ưu tiên thấp nhất — chính mặt trái của thứ khiến cron 5 phút không tốn tiền.
⚠️ **Độ trễ BẤT ĐỊNH, đừng tìm quy luật theo phút hay tần suất** — cùng dòng `cron: '47 21'`
của web-scan có lần trễ **2 phút**, lần trễ **122 phút**; canary `45 15` trễ 98', `15 23` trễ
56'. Suy "đặt phút lẻ thì thoáng" là kết luận từ mẫu 1 lần, đã thử và sai.

🖥️ **LaunchAgent `com.huy.diemtin-bot-telegram` (dựng 28/07/2026, Huy chọn)** — máy Mac chạy
`nhin_truoc_kich_bot.py` mỗi **60 giây**, đúng cách đã dùng cho bản tin: dispatch
qua API chạy NGAY (đo: lệnh phát 21:00:00 → run tạo 21:00:20Z), chỉ cron mới bị bỏ. Nghiệm thu
lần đầu: kích lúc 10:10 trong khi cron gần nhất là 07:09 — **3 tiếng GitHub không gọi phát nào**.
`StartInterval` chứ không phải `StartCalendarInterval`: máy vừa ngủ dậy thì launchd chạy bù
ngay một lần rồi mới vào chu kỳ — đúng thứ cần cho "Huy vừa mở máy và đang hỏi bot".
Đánh đổi: **chỉ chạy khi máy thức**; máy ngủ thì rơi về cron như cũ. Không mất câu hỏi (ngưỡng
360 phút đã lo), chỉ chậm. Cố tình KHÔNG dựng caffeinate cho việc này — bot hỏi-đáp không có
hạn chót như bản tin. Log: `tail -30 /tmp/diemtin-bot-kich.log`.

👁️ **NHÌN TRƯỚC RỒI MỚI KÍCH** (`scripts/nhin_truoc_kich_bot.py`, Huy chốt 28/07 sau khi hỏi
*"kích mỗi 1 phút có nhiều quá không"*). Kích mù mỗi phút = **1.440 run/ngày**: rate limit chỉ
tốn 3,6% (180/5000 call một giờ) và không mất tiền vì repo public — nhưng nó **chôn lấp tab
Actions**, đúng công cụ dùng để chẩn đoán khi bản tin hỏng, và đẻ hàng loạt run `cancelled` do
`concurrency`. Nay máy gọi `getUpdates` trước, chỉ kích khi thật sự có tin ⇒ độ trễ vẫn ~1 phút
mà **số run/ngày bằng số lượt hỏi thật**.

| | Kích mù 1 phút | Nhìn trước |
|---|---|---|
| Độ trễ | ~1 phút | ~1 phút |
| Run/ngày | 1.440 | = số lượt hỏi |

⚠️ **`getUpdates` ở đây TUYỆT ĐỐI KHÔNG được kèm `offset`** — không có offset thì chỉ NHÌN;
Telegram chỉ coi là đã nhận khi ai đó gọi lại với `offset = id + 1`, và việc đó là của workflow.
Script này lỡ xác nhận thì workflow thấy hàng đợi rỗng và **câu hỏi mất hẳn**.
⚠️ **Chống dội theo CẢ id LẪN thời gian:** update chưa được workflow xác nhận thì phút sau nhìn
vẫn thấy — kích lại là thừa. Nhưng chỉ nhớ id thôi thì workflow chết giữa chừng sẽ làm câu hỏi
nằm lại vĩnh viễn. Nên id mới → kích ngay; id cũ → kích lại sau `KICH_LAI_SAU_PHUT = 10`.
⚠️ Token + danh sách chat ở **`/Users/Huy/Claude/.tg-bot.json`** (chmod 600, NGOÀI repo vì repo
public), dán bằng `--luu-token` (getpass, Huy tự chạy). **Chưa có token thì script tự lùi về
kích mù mỗi 5 phút** — bot kém tối ưu chứ không chết, đó là lý do đổi LaunchAgent được ngay mà
không cần chờ dán token.
Muốn tức thì thì phải chuyển sang Claude API + API key riêng (~78–170k đ/tháng với Haiku
4.5 ở mức ~20 câu/ngày, ~340k đ với Sonnet 5) — Huy đã cân nhắc và chọn miễn phí.

| Mảnh | Việc |
|---|---|
| `scripts/tra_cuu_tin.py` | Trích tin từ DATA ra text gọn làm ngữ cảnh (`--days`, `--tim`, `--full`). **Đây là cách DUY NHẤT được phép lấy tin cho bot** — Read `index.html` (780KB) là thổi bay context |
| `scripts/telegram_bot.py` | `--doc` đọc câu hỏi mới · `--tra-loi FILE --chat` gửi trả lời · `--bao-tat-ca TEXT` báo mọi chat đang chờ |
| `.github/prompts/telegram-bot.md` | Prompt cho `claude -p`: giọng văn, độ dài, cấm bịa, cấm commit |
| `.github/workflows/telegram-bot.yml` | Cron 5' → đọc → báo "đang tra" → cài Claude → trả lời → báo lỗi nếu hỏng |

**Bốn quyết định thiết kế, đừng "dọn cho gọn" mất:**
1. **KHÔNG lưu offset vào repo.** Telegram giữ hàng đợi update chưa xác nhận 24h; gọi
   `getUpdates?offset=<id cuối+1>` là nó tự xoá. Dùng chính cơ chế đó làm con trỏ đã-đọc →
   khỏi commit file state mỗi 5 phút (rác git, và đụng `git pull --rebase` của phiên quét).
2. **Xác nhận NGAY sau khi đọc, TRƯỚC khi gọi Claude.** Xác nhận sau thì một câu hỏi làm
   Claude lỗi sẽ được đọc lại mỗi 5 phút và lỗi mãi mãi. Đổi lại có thể mất câu hỏi nếu
   workflow chết giữa chừng — nên workflow **gửi ngay tin "⏳ đang tra"** và **gửi tin báo
   lỗi khi `failure()`**; im lặng là kiểu hỏng tệ nhất.
3. **Danh sách trắng theo `TELEGRAM_CHAT_ID`.** Bot Telegram ai cũng nhắn được — không lọc
   thì người lạ xài hạn mức Claude của Huy. Lọc ở CẢ hai đầu: `--doc` bỏ chat lạ, và
   `--tra-loi/--bao` từ chối gửi ra ngoài danh sách.
3b. **KHÔNG in nội dung câu hỏi vào log, CHUYỂN TIẾP bản sao cho Huy qua Telegram** (chốt
   27/07/2026). Stdout đi thẳng vào log GitHub Actions của một repo **public**. Đã kiểm
   thực tế: khách không đăng nhập thì **không** xem được log (trang job hiện "Sign in to
   view logs") và API tải log đòi quyền admin (`403 Must have admin rights`) — nhưng người
   có tài khoản GitHub bất kỳ thì rất có thể xem được, vì public repo cho mọi người quyền
   đọc. Câu người ta nhắn riêng cho bot không nên nằm ở đó. Log nay chỉ in
   `[chat …4309] 38 ký tự`.
   Bù lại Huy vẫn theo dõi đủ: `--tra-loi` **tự động** gửi bản sao (câu hỏi + câu trả lời)
   về chat của Huy khi người hỏi không phải Huy. **Đặt trong script chứ không nhờ prompt** —
   prompt thì Claude có thể quên, cơ chế thì không. Chat của Huy = phần tử ĐẦU trong
   `TELEGRAM_CHAT_ID`, ghi đè bằng `TELEGRAM_OWNER_CHAT`. Chỉ chuyển tiếp với `--tra-loi`;
   `--bao` (tin "đang tra", tin báo lỗi) thì không, kẻo chat của Huy thành bãi rác.
4. **Bước đọc chạy TRƯỚC bước cài Claude Code.** Không có câu hỏi thì job dừng sau ~15 giây
   và không cài gì — đó là lý do cron 5 phút không tốn gì đáng kể.

#### 🗑️ Lệnh `/xoa` — dọn tin rác khỏi cả hai phía (thêm 28/07/2026, chỉ thị Huy)
**REPLY vào tin rác rồi gõ `/xoa`** → bot xoá tin đó *và* xoá luôn dòng lệnh. `/xoa 5` xoá 5
tin LIÊN TIẾP tính từ tin được reply (trần `XOA_TOI_DA = 20`). Xử lý ngay trong bước `--doc`,
KHÔNG đẩy sang `claude -p`: xoá là việc cơ học, bắt chờ 1–3 phút cài Claude Code thì vô lý.

⚠️ **Vì sao bắt buộc phải REPLY, không làm được "/xoa 5 tin cuối":** Bot API **không cho đọc
lịch sử chat** — không có phương thức liệt kê tin đã gửi, `getUpdates` chỉ trả tin ĐẾN bot, và
bot không lưu `message_id` của tin nó gửi. Reply là đường DUY NHẤT để bot biết id cần xoá
(`reply_to_message.message_id`). `/xoa n` chạy được vì `message_id` tăng dần qua mọi tin trong
chat, nên n tin liên tiếp = `id … id+n-1`.
⚠️ **Trần cứng 48 GIỜ của Telegram** — cũ hơn thì API từ chối, phải xoá tay trong app. Bot báo
rõ lỗi thật thay vì im (im ở đây làm Huy tưởng đã xoá).
⚠️ Bot xoá được **cả tin đến lẫn tin đi** trong private chat — nên nó dọn được cả câu hỏi lỡ gõ.

#### Canary CHỈ nhắn cho Huy, không nhắn cho người đọc (sửa 28/07/2026)
`canary.py:gui()` trước đây gửi tới **mọi** chat trong `TELEGRAM_CHAT_ID`. Sai đối tượng: nội
dung là *"hỏng ở khâu QUÉT · lastRun … · Chạy tay: gh workflow run …"* — người đọc bản tin không
làm gì được với nó, không kiểm chứng được, **và cũng không xoá đi được** (bot chỉ xoá trong 48h,
mà Huy không có mặt trong đoạn chat đó để `/xoa`). Nay chỉ gửi chat CHỦ (phần tử đầu trong
`TELEGRAM_CHAT_ID`, ghi đè bằng `TELEGRAM_OWNER_CHAT`) — cùng quy ước với `telegram_bot.py`.
Kiểm cấu hình vẫn soi cả danh sách nên mất secret vẫn ĐỎ. **Quy tắc chung: cảnh báo hạ tầng gửi
cho người vận hành, không gửi cho người đọc.** Thêm kênh cảnh báo mới thì áp đúng luật này.

⚠️ **Cron 5 phút miễn phí VÌ REPO ĐANG PUBLIC** (GitHub Actions không giới hạn phút cho repo
public). Chuyển repo sang private là lịch này ngốn hạn mức 2.000 phút/tháng → phải giãn cron
hoặc đổi sang webhook.
⚠️ **Chuỗi trong `run:` một dòng mà chứa `": "` sẽ làm vỡ YAML** (YAML đọc thành mapping) —
đã vấp thật với `Log: $RUN_URL`. Dùng block scalar `run: |`.
⚠️ Prompt cấm bot commit/push. Phiên bot chỉ đọc; `permissions: contents: read`.

### Học từ câu hỏi người đọc (thêm 27/07/2026, chỉ thị Huy)
Mỗi lượt hỏi bot được phân loại, lưu lại, và nếu gợi ra tin đáng đưa thì **đề xuất cho Huy
qua Telegram**. Huy đã chốt: **bot CHỈ đề xuất, không tự nạp web** · hồ sơ lưu **Supabase**.

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

**Routine `ho-so-doc-gia`** — scheduled task local, cron `0 10 */3 * *` (10:00 giờ VN, 3
ngày/lần). Quy trình: `docs/routine-ho-so-doc-gia.md` (nguồn sự thật; SKILL.md chỉ là stub).
"Không có dữ liệu" là kết quả hợp lệ → ghi log, KHÔNG gửi Telegram, kết thúc.

⚠️ **Chia việc giữa đếm và nhận định.** `--so-lieu` chỉ ĐẾM (số lượt, chủ đề hay hỏi, tỉ lệ
trong/ngoài phạm vi, giờ hay hỏi). Phần "người này quan tâm gì, hỏi theo lối nào" do phiên
đọc số liệu + câu hỏi thật rồi viết — vì đó đúng là chỗ dễ bịa nhất, và Huy đã bác một lần
vì suy luận bắc cầu (27/07, mục khí tài).

⚠️ Prompt CẤM bot tự nạp tin (`add_news.py`, sửa `index.html`) — người duyệt là Huy.
Chuẩn tin đề xuất giống hệt chuẩn bản tin: khung hôm nay + hôm qua, nguồn theo thang 3 tầng,
`url` là bài cụ thể, **tối đa 3 tin, thà rỗng còn hơn đề xuất rác**.

### Quét tin từ kênh Telegram
`scripts/telegram_harvest.py` + bảng kênh `docs/telegram-channels.md` (script đọc thẳng bảng đó —
thêm kênh chỉ sửa một chỗ). Lớp `[TG]` **cùng vai RADAR với `[GNEWS]`**: Telegram là mạng xã hội,
nằm ngoài thang xác minh nguồn → **link `t.me` TUYỆT ĐỐI không được vào `sourceUrl`**, phải truy
về bài gốc; script in sẵn dòng `link dẫn:` (URL ngoài mà bài Telegram trỏ tới) để đỡ công.
Kênh hạng `nhanuoc` (TASS/Sputnik/Rybar) chỉ dùng cho phát ngôn CỦA CHÍNH HỌ.

**Độ phủ thật (đo 27/07, dò 77 kênh):** mạnh ở **Mỹ–Mali/Sahel** (@AfricaIntel hay kèm link
africanews/theafricareport — nguồn curl thường 403) và một phần **CNQS Mỹ** (@OSINTdefender);
**gần như trắng Úc & Biển Đông** — không kênh nào vừa sống vừa đúng chuyên môn. Là lớp BỔ SUNG,
không thay được RSS + Google News. Thiếu nó KHÔNG phải lý do hoãn bản tin.

⚠️ **Bốn cái bẫy đã vấp thật, đừng vấp lại:**
1. **Sai hoa/thường là mất kênh.** `@sentdefender` trả trang tắt preview; `@OSINTdefender` — cùng
   kênh, viết đúng hoa — chạy bình thường, 20 bài/ngày. Suýt phải dựng cả MTProto vì lỗi này.
2. **Kênh mạo danh cơ quan.** `@NATO_HQ` = "NATO-HQ Usibjonov_98", `@un_news` = "УкрСнюс",
   `@scspi` = kênh cá nhân tên "Silvia", `@navalnews` = "Навальный News" chứ không phải Naval
   News. Luôn xem `og:title` (cột TÊN của `--probe`) trước khi tin vào handle nghe hợp lý.
   **Không cơ quan chính thức nào có kênh Telegram đọc được** — tầng 1 vẫn phải lấy qua RSS/web.
3. **"Không có message" ≠ "không tồn tại".** Mở `t.me/<kênh>` (không `/s/`): `og:title` ra
   "Telegram: Contact @x" là không tồn tại; ra tên thật là có thật mà tắt preview. `--probe` đã
   phân biệt sẵn hai ca này.
4. **Khớp chủ đề trên 200 ký tự ĐẦU bài** (`HEAD_CHARS`), không phải cả bài — bài Telegram dài
   kiểu digest, khớp toàn văn kéo tin Triều Tiên/Trung Quốc vào "CNQS Mỹ" chỉ vì cuối bài có chữ
   Pentagon. Siết lại giảm 10 ứng viên xuống 4, cả 4 đều đúng chủ đề.

**Đường MTProto** (`--mtproto`, Telethon): đọc được cả kênh tắt xem trước web. Cần
`TG_API_ID`/`TG_API_HASH`/`TG_SESSION`, tạo bằng `python3 scripts/telegram_login.py` — **Huy tự
chạy trong terminal, Zim không nhập hộ** vì bước đó nhập số điện thoại + OTP + 2FA. Session
string = quyền đọc TOÀN BỘ tài khoản Telegram, đừng dán vào chat, huỷ bằng Telegram → Settings →
Devices. Chạy TUẦN TỰ, không đa luồng (MTProto tính giới hạn theo tài khoản, bắn song song là ăn
FloodWait). Thiếu biến thì tự lùi về đường web, không lỗi. Sau khi sửa lại lỗi hoa/thường ở bẫy
1, MTProto **chỉ còn cần cho `@militarylandnet` và `@DefenceU`** — giá trị nhỏ hơn nhiều so với
ước tính ban đầu.

## 🧪 TEST CỔNG KIỂM — `tests/` (dựng 29/07/2026, áp luật mục 17 CLAUDE.md toàn cục)

**Luật:** mọi cổng/hook/checker trong repo này **phải có ít nhất MỘT ca PHẢI CHẶN** — dựng đúng
điều kiện xấu rồi khẳng định nó thật sự chặn/kêu. Test chỉ có ca "phải cho qua" là **chưa test**.

**Vì sao (bài học QuanSu 29/07/2026):** cổng dàn ý người duyệt ở `App/QuanSu/intrep-to-docx.py`
đã **CÂM từ ngày dựng** (bug NFD tên file macOS) mà không ai biết, vì nó thuộc loại *"hỏng thì im
lặng cho qua"* — không có gì để chặn thì cổng im, và cổng chết cũng im y hệt. Chạy trăm lần "thấy
nó không kêu" không chứng minh được gì. Mọi cổng của repo này đều cùng loại đó.

| Bộ test | Cổng nó canh | Ca |
|---|---|---|
| `tests/test-cong-baomoi.py` | Cổng Báo Mới chống bỏ sót (`scripts/add_news.py`) | 8 — 3 PHẢI NHẮC, 4 chống nhắc oan, 1 kiểm cổng còn nằm trên đường đi của `--recent-titles` |
| `tests/test-so-da-gui.py` | Sổ đã gửi (`so_da_gui.py` + `make_docx.loc_chua_gui`) | 9 — 5 PHẢI LOẠI/PHẢI ĐÚNG PHẠM VI, 3 chống lọc oan, 1 kiểm còn người đọc sổ |
| `tests/test-canary-ban-tin.py` | Canary bản tin (`.github/scripts/canary.py`) | 10 — 7 PHẢI KÊU, 3 PHẢI IM (gồm ca hồi quy kêu oan 00:23 ngày 28/07) |
| `tests/test-cong-phien-test.py` | Cổng "phiên TEST không đụng cờ thật" (`scripts/state.py` + `claude-web-scan.yml`) | 11 — 5 PHẢI CHẶN, 4 chống chặn oan + đối chứng, 1 kiểm cổng còn nằm trên đường đi (đọc chính file yml), 1 kiểm banner |
| `scripts/sua_nhan_analyses.py --tu-kiem` | Chính `--kiem` của nó (nhãn `outlet` mục Think-tank) | 5 — 3 PHẢI CHẶN, 2 PHẢI CHO QUA + 1 đối chứng. **Test nằm TRONG script** chứ không ở `tests/` vì cổng và bộ ca dùng chung dữ liệu giả |

Chạy cả bốn sau mỗi lần sửa `add_news.py` · `so_da_gui.py` · `make_docx.py` · `canary.py` · `state.py` · `claude-web-scan.yml`:
```
python3 /Users/Huy/Claude/diem-tin-the-gioi/tests/test-cong-baomoi.py
python3 /Users/Huy/Claude/diem-tin-the-gioi/tests/test-so-da-gui.py
python3 /Users/Huy/Claude/diem-tin-the-gioi/tests/test-canary-ban-tin.py
python3 /Users/Huy/Claude/diem-tin-the-gioi/tests/test-cong-phien-test.py
```

⚠️ **TEST XANH CHƯA ĐỦ — phải chứng minh test BẮT ĐƯỢC lỗi.** Mỗi file có cờ `--tu-kiem`: nó tự
dựng các bản mã nguồn **đã gỡ đúng dòng bảo vệ** rồi chạy lại chính bộ ca đó với biến môi trường
(`ADDNEWS_MOD` / `SODAGUI_DIR` / `CANARY_TIN_MOD`), và **các ca đã khai phải ĐỎ**. Xanh trên cả bản
đúng lẫn bản hỏng thì test đó vô dụng. Kết quả 29/07: 5/5 · 4/4 · 6/6 bản hỏng đều bị bắt.
Huy hỏi *"cổng đó chặn được chưa"* → câu trả lời **không bao giờ là lời hứa**, mà là chạy `--tu-kiem`
rồi đưa kết quả.

⚠️ **Bản hỏng phải nằm TRONG thư mục thật của script**, không phải `/tmp`: `add_news.py` và
`canary.py` tự suy repo root từ vị trí của chính mình (`import topics`, `from tg_api import …`,
đọc `index.html`). Để ở `/tmp` thì mọi ca đỏ vì `ImportError`/thiếu file — **đỏ vì lý do sai thì
không chứng minh được gì**. Cả hai file test đã ghi bản hỏng vào đúng thư mục rồi `unlink` trong
`finally`.

⚠️ **Ca thử phải ĐỌC bảng ánh xạ từ chính mã nguồn, đừng chép tay.** Đã bẫy một lần: ca `sukien`
của canary soi ô **`sang`** của pipeline `event-scan`, không phải ô `sukien` — chép tay là test đỏ
oan và tưởng cổng hỏng.

## Nơi lưu dữ liệu
Toàn bộ dữ liệu nằm trong `index.html`, biến `var DATA = {...}` (~170KB, xem mục "Quy trình" bên dưới — KHÔNG đọc trực tiếp file này). Các phần liên quan tới quét tin:

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
Thêm đường nạp 27/07/2026 (chỉ thị Huy: *"quét tin buổi sáng nhớ quét thêm cả các bài từ think-tank"*).
**Vì sao mục này từng chết:** web đã có sẵn tab và mảng `DATA.analyses` từ lâu, nhưng KHÔNG script nào
ghi vào đó — chỉ `prune_news.py` xoá. Kết quả: bài mới nhất đứng ở 09/07 suốt 18 ngày. Đây là bài học
chung: **ra một mục trên web thì phải có đường nạp tự động, không thì nó chết chắc.**

Mỗi bài: `{date, outlet, author, title, summary, takeaway, topic, region, url}` (+ `_addedDate` do
script đóng dấu). `takeaway` = 1–2 câu ĐIỀU RÚT RA — đây là thứ web và email hiển thị nổi nhất, không
được bỏ trống.

**➕ `concepts` — khái niệm rút từ bài, chảy thẳng vào tab 📚 Khái niệm (thêm 29/07/2026, chỉ thị Huy).**
Mỗi bài có thể mang `concepts: [{term, def}]`; `importAnalysisConcepts()` trong index.html nạp chúng vào
sổ tay khái niệm, dùng CHUNG kho `dt.concepts` với khái niệm của tập trận nên không nhân đôi. Nguồn hiển
thị dưới mỗi thẻ là `outlet — tiêu đề bài`, khác với tập trận (ghi tên cuộc), để lần ngược được.
| Việc | Lệnh |
|---|---|
| Nạp khái niệm | `python3 scripts/set_analysis_concepts.py kn.json` — `[{url, concepts:[{term,def}]}]` |
| Soi bài nào chưa có | `python3 scripts/set_analysis_concepts.py --kiem` |
| Chứng minh guardrail còn sống | `python3 scripts/set_analysis_concepts.py --tu-kiem` (9 ca: 7 PHẢI CHẶN + 2 phải cho qua) |

Guardrail CHẶN: `url` không có trong DATA · thiếu `term`/`def` · `def` dưới 40 ký tự (giải thích cụt thì
thà không có) · `term` quá 90 ký tự (web cắt ở đó) · hai `term` trùng nhau trong CÙNG một bài · quá 6
khái niệm một bài. **KHÔNG chặn** khái niệm trùng giữa các bài hoặc trùng với tập trận — web tự khử
trùng theo tên đã bỏ dấu, chặn ở đây là chặn oan.
⚠️ **Bài không có thuật ngữ nào đáng lưu thì BỎ QUA bài đó**, đừng nhồi cho đủ số: sổ tay khái niệm là
công cụ LỌC, nhồi vào là hỏng đúng công dụng của nó. Quy trình phiên sáng: `docs/routine-web-scan.md`
Bước 4.4 mục 4.

| Bước | Lệnh | Ghi chú |
|---|---|---|
| Liệt kê ứng viên | `python3 scripts/add_analyses.py --candidates` | Fetch RSS **24 viện đã verify fetch thật 27/07**, xếp theo KHU VỰC (xem `THINKTANK_FEEDS`). Tự bỏ bài đã có trong DATA, đường dẫn rác (`/in-the-news/`, `/media-citations/`, `/event/`…) và tham số `utm_*`. Dòng cuối in **vùng không có RSS + domain** để bù bằng WebSearch |
| Nạp | `python3 scripts/add_analyses.py /tmp/analyses.json` | Guardrail: xem docstring đầu file |

⚠️ **War on the Rocks KHÔNG chết** — bảng "BỎ HẲN" phía trên ghi 403 là do curl trần; thêm `-A <UA>`
và `--compressed` thì feed trả 100 item bình thường. Cùng bài học với UN News hồi 22/07: đừng gạch một
nguồn khi chưa loại trừ lỗi header/giải nén.
**KHÔNG có RSS dùng được** (đã thử 2 biến thể URL mỗi nơi 27/07, đừng thử lại): CSIS · Brookings · RUSI ·
Chatham House · ORF · CNAS · FPRI (trả HTML) · 38 North · Stimson (Cloudflare) · USIP (404) · Carnegie ·
Belfer · Wilson Center (XML hợp lệ nhưng 0 item) → `WebSearch site:<domain>`.

**Guardrail riêng, khác `add_news.py`:** khung ngày **7 ngày** (bài viện đăng thưa, không "ôi" sau 24h)
nhưng vẫn kiểm HAI LỚP như add_news nên neo lô về ngày cũ không lách được; và `outlet` bị SIẾT theo
**DOMAIN** (`THINKTANK_DOMAINS`) — mục tên là Think-tank mà lọt bài Al Jazeera/Naval News thì hỏng chính
danh nghĩa của mục (18 bài đời cũ trong DATA có lẫn như vậy). Gặp lỗi domain → **BỎ bài**, đừng đổi url
cho lọt; đúng là viện thật mà thiếu thì thêm domain vào danh sách trong script.

### 🏷️ Nhãn `outlet` — bảo trì bằng `scripts/sua_nhan_analyses.py` (dựng 29/07/2026)
Guardrail của `add_analyses.py` kiểm theo **DOMAIN**, **không kiểm nhãn `outlet`** — cố ý, vì tên viện
viết mỗi lúc một kiểu. Cái giá: cùng một domain vẫn nạp được dưới hai tên khác nhau, và web thì hiện
`outlet` ra thẳng dòng `.foot` **đồng thời dùng nó làm khoá `voteMeta.src`** của hồ sơ độc giả — nhãn
tách đôi là tín hiệu bình chọn cũng chia đôi, học sai mà không có dấu hiệu gì. Bắt được thật 29/07:
`'ASPI'` và `'ASPI Strategist'` cùng `aspistrategist.org.au`.
```
python3 scripts/sua_nhan_analyses.py --kiem       # liệt kê nhãn+domain, soi 3 loại lỗi (mã 2/3/4)
python3 scripts/sua_nhan_analyses.py --gop-nhan   # áp OUTLET_CANON (domain → nhãn chuẩn)
python3 scripts/sua_nhan_analyses.py --tu-kiem    # chứng minh --kiem bắt được lỗi
```
| `--kiem` bắt | Xử lý |
|---|---|
| Một domain nhiều nhãn | thêm dòng vào `OUTLET_CANON` rồi `--gop-nhan` |
| Domain ngoài `THINKTANK_DOMAINS` | **đúng là viện thật → thêm domain**, đừng xoá bài (ca ISW `understandingwar.org` 29/07: guardrail đang chặn oan cả bài mới). Là báo chí → **HỎI Huy** rồi mới `--xoa-url` |
| Hai bản cùng một bài gốc | trùng **slug cuối url** — `warontherocks.com/<slug>` và `.../2026/07/<slug>` là hai chuỗi khác nhau nên guardrail trùng-url cho lọt cả hai. Huy chốt giữ → ghi vào `TRUNG_DA_DUYET` |

⚠️ **Script KHÔNG tự xoá bài** — `--xoa-url` phải gõ đủ url, và xoá là quyết định của Huy. Ghi url +
tiêu đề vào `logs/loai-tin.md` TRƯỚC khi xoá.
⚠️ Chạy `--kiem` sau mỗi đợt nạp think-tank lớn. Con số "18 bài đời cũ lẫn báo chí" ở đoạn trên là số
**tại thời điểm 27/07**; `prune_news.py` đã dọn bớt, tới 29/07 chỉ còn 4 (3 báo chí đã xoá + 1 ISW giữ
lại) — đừng lấy số 18 làm mốc kiểm.

**Email sáng** (`send-morning-email.js`): có khối 🏛️ Think-tank riêng, và **bài think-tank mới cũng đủ
để mở email** kể cả khi không có sự kiện/tập trận nào (hàm `diffAnalyses`; không có bản HEAD~1 để so thì
dựa vào `_addedDate == generatedAt`). Quy trình phiên sáng: `docs/routine-web-scan.md` **Bước 4.4** /
`.github/prompts/web-scan-ci.md` **BƯỚC 6** (địa chỉ cũ `routine-event-scan.md` Bước 2c /
`event-scan-ci.md` bước 3b đã chết từ 28/07/2026: file prompt bị xoá, file docs còn lại là stub).

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
| **Nguồn không mở được bằng tool** (403/302 loop/paywall) | Không phải lý do bỏ nếu **nội dung** đã được xác nhận qua đường khác (WebSearch snippet, nguồn thứ hai). Nếu KHÔNG xác nhận được chữ nào thì BỎ — đó là ca The Africa Report 25/07 |
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
Bổ sung cho 5 chủ đề (Nội bộ Mỹ · Úc–Biển Đông · CNQS Mỹ · Mali · Predator). Chi tiết cách dùng từng
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
| DVIDS news (Predator) | https://www.dvidshub.net/rss/news | 20 item |

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
### 🪖 Trang .mil — CHỈ ĐỌC ĐƯỢC TỪ CI, KHÔNG đọc được từ máy Mac (chẩn đoán 27/07/2026)
Huy hỏi "8 trang quân chủng có cách nào đọc được không" → đào ra nguyên nhân thật, KHÔNG phải bị chặn IP
hay sai user-agent: **máy Mac không phân giải nổi DNS zone `.mil`**. Cloudflare DoH trả đúng lý do:
`EDE(9): DNSKEY Missing no SEP matching the DS found for mil` + `EDE(22): No Reachable Authority` — tức
**DNSSEC của zone `.mil` lỗi/không tới được authority từ đây**. Thử `dig @8.8.8.8` và `@1.1.1.1` đều
SERVFAIL, `+cd` cũng không cứu. Đây là giới hạn tầng DNS, không vá được bằng cờ curl.
**Nhưng GitHub runner (Mỹ) phân giải được hết** → chạy test thật trên CI và thu được 2 feed dùng được:
| Nguồn | RSS URL | Kiểm 27/07 (từ CI) |
|---|---|---|
| Không quân Mỹ — Air Force Link News | https://www.af.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=1&max=20 | 10 item, mới 25/07 |
| Lục quân Mỹ | https://www.army.mil/rss/static/1.xml | 2 item, mới 27/07 |

⚠️ **Hai feed này CHỈ chạy trong CI.** Trên máy local, `harvest.py` sẽ fail êm (curl không phân giải được
→ trả rỗng → bỏ qua), nên **kết quả harvest local ÍT HƠN CI vài ứng viên** — đó là bình thường, đừng đi
truy bug. CI mới là mốc chính nên chỗ này không mất tin.
⚠️ **BẪY `Site=1`:** tham số này trả **feed của Air Force bất kể domain** — thử `marines.mil` và
`news.uscg.mil` với `Site=1` đều ra y hệt "Air Force Link News". Thêm cả ba vào bảng là nạp trùng nội
dung ba lần. Phải kiểm tiêu đề thật trước khi tin một feed `DesktopModules`.
⛔ **Chưa tìm được feed riêng** (mọi biến thể ContentType/Site đã thử đều 0 item): `navy.mil`,
`marines.mil`, `centcom.mil`, `pacom.mil`, `jcs.mil`, `news.uscg.mil`. Trang HTML của chúng **403 với cả
CI lẫn local** (WAF chặn IP datacenter). **Thay thế: DVIDS** (`dvidshub.net/rss/all` — đã có trong bảng,
gom tin của mọi quân chủng) và feed hợp đồng/thông cáo `war.gov`.

### 🕸️ TRANG HTML QUÉT TRỰC TIẾP — không có RSS nhưng vẫn đọc được (thêm 27/07/2026)
Huy nhắc đúng: *"không có RSS thì mày vẫn xem được mà"*. Kiểm lại 85 domain trong file nguồn chính thức
Mỹ: **42 mở được HTML bằng curl** (chỉ 34 chặn 403). `harvest.py` có lớp `[HTML]` quét thẳng trang danh
sách thông cáo — lấy link + tiêu đề + ngày (tìm trong khối HTML quanh mỗi link).
**Giá trị lớn nhất: toàn bộ uỷ ban HẠ VIỆN đều mở được**, mà đó chính là **nhóm 1** (điều trần + bỏ
phiếu) — nhóm luôn thiếu tin nhất. Thực tế lần chạy đầu bắt được "Chairman Rogers Applauds House Passage
of FY27 NDAA", "House Passes H.R. 9770", "Opening Statement at the FY27 NDAA Markup".

**Cột "Chạy ở"** — `cả hai` = local + CI đều đọc được · **`CI`** = CHỈ GitHub runner đọc được, máy Mac
bị 403 (harvest local tự bỏ qua, xem `html_pages_from_claude_md`). Đo bằng `scripts/probe_sources.py`
chạy ở cả hai nơi (27/07/2026).

| Trang | URL | Chạy ở | Nhóm/chủ đề |
|---|---|---|---|
| Uỷ ban Quân vụ Hạ viện | https://armedservices.house.gov/news/press-releases | cả hai | **Nội bộ Mỹ nhóm 1** |
| Uỷ ban Chuẩn chi Hạ viện | https://appropriations.house.gov/news/press-releases | cả hai | **Nội bộ Mỹ nhóm 1** |
| Uỷ ban Tình báo Hạ viện | https://intelligence.house.gov/news/ | cả hai | Nội bộ Mỹ nhóm 1 |
| Uỷ ban Tư pháp Hạ viện | https://judiciary.house.gov/news/documentquery.aspx?DocumentTypeID=2 | cả hai | Nội bộ Mỹ nhóm 1 |
| Uỷ ban An ninh Nội địa Hạ viện | https://homeland.house.gov/news/ | cả hai | Nội bộ Mỹ nhóm 1 |
| Uỷ ban Giám sát Hạ viện | https://oversight.house.gov/news/ | cả hai | Nội bộ Mỹ nhóm 1 |
| Uỷ ban Tài chính Hạ viện | https://financialservices.house.gov/news/ | cả hai | nhóm 1 + 4 |
| Uỷ ban Thuế vụ Hạ viện | https://waysandmeans.house.gov/news/ | cả hai | nhóm 1 + 4 |
| Uỷ ban Ngân sách Hạ viện | https://budget.house.gov/news | cả hai | nhóm 1 + 4 |
| Uỷ ban Khoa học Hạ viện | https://science.house.gov/news | cả hai | nhóm 1 |
| **Uỷ ban Quân vụ THƯỢNG VIỆN** | https://www.armed-services.senate.gov/press-releases | **CI** | **Nội bộ Mỹ nhóm 1** |
| **Uỷ ban Đối ngoại Thượng viện** | https://www.foreign.senate.gov/press | **CI** | **Nội bộ Mỹ nhóm 1** |
| **Uỷ ban Chuẩn chi Thượng viện** | https://www.appropriations.senate.gov/news/majority | **CI** | **Nội bộ Mỹ nhóm 1** |
| **Uỷ ban Tình báo Thượng viện** | https://www.intelligence.senate.gov/reports-publications/press-releases/ | **CI** | **Nội bộ Mỹ nhóm 1** |
| **Uỷ ban Tư pháp Thượng viện** | https://www.judiciary.senate.gov/press/ | **CI** | Nội bộ Mỹ nhóm 1 |
| Uỷ ban Ngân hàng Thượng viện | https://www.banking.senate.gov/newsroom | **CI** | nhóm 1 + 4 |
| Uỷ ban Tài chính Thượng viện | https://www.finance.senate.gov/chairmans-news | **CI** | nhóm 1 + 4 |
| Uỷ ban Ngân sách Thượng viện | https://www.budget.senate.gov/chairman/newsroom | **CI** | nhóm 1 + 4 |
| Uỷ ban Thương mại Thượng viện | https://www.commerce.senate.gov/press/ | **CI** | nhóm 1 + 4 |
| Uỷ ban Năng lượng Thượng viện | https://www.energy.senate.gov/newsroom | **CI** | nhóm 1 |
| Uỷ ban An ninh Nội địa Thượng viện (HSGAC) | https://www.hsgac.senate.gov/media/majority-news/ | **CI** | nhóm 1 |
| Uỷ ban Quy tắc Thượng viện | https://www.rules.senate.gov/news/press-releases | **CI** | nhóm 1 |
| Thông cáo chung Thượng viện | https://www.pressphotographers.senate.gov/senate/senate-press-releases/ | **CI** | nhóm 1 |
| Census Bureau | https://www.census.gov/newsroom/press-releases.html | **CI** | nhóm 4 (số liệu) |
| OCC (Kiểm soát Tiền tệ) | https://www.occ.treas.gov/news-events/newsroom/news-issuances-by-year/news-releases/index-news-releases.html | **CI** | nhóm 4 |

⚠️ Đây là **quét HTML thô**, nhiễu cao hơn RSS: có thể lẫn link điều hướng, và **ngày lấy từ khối HTML
quanh link nên có thể sai** — agent PHẢI mở bài kiểm ngày sự kiện như với lớp `[GNEWS]`.

#### 📊 Kết quả dò TOÀN BỘ nguồn ở CẢ HAI môi trường (27/07/2026, `scripts/probe_sources.py`)
288 URL / 154 domain, dò từ máy Mac và từ GitHub runner (Mỹ), rồi so:
| | local (máy Huy) | CI (Mỹ) |
|---|---|---|
| RSS đọc được | 78 domain | 77 |
| HTML đọc được | 39 | **58** |
| 403 | 31 | **16** |

- **114 domain cả hai đọc được** — phần lớn bảng nguồn.
- **21 domain CHỈ CI đọc được** → local mất hẳn. Gồm **TOÀN BỘ uỷ ban THƯỢNG VIỆN** (armed-services,
  foreign, appropriations, intelligence, judiciary, banking, finance, budget, commerce, energy, hsgac,
  rules, agriculture, indian, jec, sbc + trang thông cáo chung) và census.gov, occ.treas.gov. Đây **đảo
  lại** ghi chú cũ "uỷ ban Thượng viện 403, chỉ WebSearch được" — sai vì chỉ đo ở local.
- **3 domain CHỈ local đọc được** (CI bị 403): `axios.com`, `flightglobal.com`, `rappler.com` → phiên CI
  sẽ hụt 3 nguồn này, bù bằng Google News/local.
- **16 domain cả hai chịu**: bls.gov, commerce.gov, defense.gov, dhs.gov, eda.gov, nsa.gov, ntia.gov,
  transportation.gov, usda.gov, senate.gov, và 6 trang quân chủng navy/marines/centcom/pacom/jcs/uscg
  → chỉ còn WebSearch/Google News, hoặc DVIDS thay thế cho nhóm quân chủng.

⚠️ **Đọc số liệu dò cẩn thận:** dò 288 URL bằng nhiều luồng dễ bị **rate-limit tạm** — lần này
`thehill.com` trả 429 và `thediplomat.com` trả 000 ở local dù bình thường vẫn chạy tốt. Thấy một nguồn
đang dùng được bỗng báo hỏng thì **kiểm lại lẻ một lần** trước khi kết luận, đừng gạch tên ngay.
Dò lại về sau: `python3 scripts/probe_sources.py --json /tmp/probe-local.json` (local) và workflow
`probe-sources.yml` (CI, ghi `docs/probe-ci.json`).

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
| DVIDS (toàn bộ) | https://www.dvidshub.net/rss/all | 419 item, mới 2h | 3 + 5 Predator |
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
đơn vị, nhưng lẫn nhiều thông cáo địa phương; dùng cho Predator/CNQS thì lọc theo từ khoá.
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
- **Tập trận Predator's Run** — thẻ `exercises` đã tạo: `"Predator's Run 2026 (tập trận Mỹ - Úc - Philippines)"` (khai mạc 21/7, kéo dài tới ~29/7, Townsville). **Mỗi phiên CHỦ ĐỘNG tìm diễn biến mới** (bài bắn đạn thật, tình huống hợp đồng, tuyên bố chỉ huy) → cập nhật qua `exerciseUpdates` (khớp đúng tên). Nguồn: pacom.mil, marines.mil, defence.gov.au, dvidshub.net, army Úc. **Khi tập trận KẾT THÚC (~29/7)** → dùng `exerciseUpdates` kèm nêu trong tóm tắt để đổi `status` sang `recent`.
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

## Log & tự phục hồi (Routine tự động)
Routine chạy trong session mới (ephemeral) nên phải để lại dấu vết để chẩn đoán khi lỗi:
- **Log bắt buộc mỗi lần chạy**: ghi vào `logs/scan-<NGÀY-VN>.log` (ngày theo `TZ='Asia/Ho_Chi_Minh' date +%F`) các mốc: START, kết quả từng agent/phần, chạy script, và DONE/SKIP/FAIL kèm lý do. **Luôn commit + push file log** kể cả khi quét thất bại (git không cần mạng ngoài nên push được ngay cả khi WebSearch/WebFetch bị chặn) — đây là cách duy nhất biết Routine fail ở đâu.
- **Idempotent (chống chạy trùng)**: đầu mỗi lần chạy, `python3 scripts/state.py claim <pipeline>` (dùng `claim` để GIÀNH KHOÁ, không phải `check` — `check` chỉ hỏi, không chặn được phiên chạy chồng). exit 10 = buổi đó ĐÃ XONG · exit 11 = phiên khác đang chạy → cả hai: ghi log `SKIP`, push log, KẾT THÚC. exit 0 = quét bình thường, xong thì `state.py done <pipeline> "<tóm tắt>"` và commit `logs/state.json` kèm bản tin. **KHÔNG dùng `generatedAt` làm cờ** (xem mục trên).
- **Retry cho tới khi xong (xen kẽ CI/local từ 26/07/2026)**: bản tin TỐI (hạn chót email 22:00): CI 21:00 → local 21:15 (2 lớp trong hạn, local là task RIÊNG `web-scan-diem-tin-toi`) → CI 22:00 (lớp VÉT, chỉ khi 2 lớp trước chết); bỏ hẳn mốc 21:30/22:30; bản tin SÁNG SỚM (từ 27/07/2026 CÓ local dự phòng): CI 04:00 → local 04:30 → CI 05:00 → local 05:30. **event-scan sáng — GỘP 28/07/2026: dùng CHUNG 4 mốc trên**, chạy NGAY SAU bản tin trong cùng session (không còn mốc 08:45/09:15/09:45/10:15 riêng). Nhờ khoá idempotent `state.py`, mốc nào thấy DONE/RUNNING thì tự SKIP; phiên chết giữa chừng thì 30' sau heartbeat thối, mốc kế cướp khoá quét lại. Cron local là giờ LOCAL (Asia/Ho_Chi_Minh), **KHÔNG phải UTC**; cron CI là UTC.
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
### TRUY NGƯỢC VỀ NGUỒN GỐC (bắt buộc từ 23/07/2026)
Báo Mới là trang TỔNG HỢP — gần như mọi bài quốc tế trên đó đều dẫn lại từ một nguồn nước ngoài.
Agent 7 và 8 phải **tìm bài gốc** (nguồn chính thức → wire → báo quốc tế uy tín), **đăng trong 24h**,
**mở bằng WebFetch để xác nhận có thật**, rồi lấy `sourceName` + `sourceUrl` + `title` + `summary` +
`significance` theo bài gốc — **đổi cả tiêu đề lẫn URL**, không giữ cách đặt tiêu đề của bản dẫn lại.
- Không tìm được: **Agent 7 GIỮ link Báo Mới** (người dùng tự bookmark, không được bỏ tin) ·
  **Agent 8 BỎ bài đó**, chọn ứng viên khác (kho 50–90 bài, không cần hạ chuẩn nguồn).
- Số liệu lấy theo bài gốc: bản dẫn lại hay làm tròn/rút gọn sai (thực tế 22/07 — "87 tỷ" thay vì
  87,6 tỷ; "tính tới 21/7" thay vì "hết năm tài khóa 30/9").
- **MỌI tin truy ngược từ Báo Mới — Agent 7 VÀ Agent 8 — phải thêm `"_baomoiUrl": "<link Báo Mới gốc>"`.**
  Thiếu nó thì: (a) `loadBaomoi` dedupe theo url + tiêu đề, đổi cả hai là bài trong `baomoi-saved.json`
  bị trộn lại thành tin THỨ HAI trên web; (b) `collect_existing_urls` mất dấu link cũ nên
  `--baomoi-pending` và **cổng Báo Mới** coi bài đó "chưa nạp" và phiên sau nạp lại y hệt — guardrail
  trùng URL không bắt được vì URL đã đổi sang nguồn gốc.
  ⚠️ **Sửa 27/07/2026:** trước đây mục này ghi "Agent 8 KHÔNG cần field này" — SAI, và đã gây lỗi thật:
  tin "Tàu 015-Trần Hưng Đạo thăm Manila" (ứng viên chuyên mục, đổi link sang qdnd.vn) nạp xong vẫn
  hiện trong danh sách chưa nạp, tối cùng ngày sẽ bị nạp lại. Lý do (b) vốn đã áp cho cả hai agent —
  câu miễn trừ cho Agent 8 mâu thuẫn với chính lý do đó.
- Đổi nguồn cho tin ĐÃ nằm trong `DATA` thì dùng `scripts/replace_source.py` (giữ nguyên vị trí
  trong mảng; xoá rồi chèn lại sẽ làm tin nhảy lên đầu, mất thứ tự thời gian).

**Ứng viên không được chọn → tự vào mục 🚫 Bị loại** (người dùng 👍 để cứu lên bản tin). Agent KHÔNG
phải liệt kê lại — `add_news.py` tự đọc `baomoi-topics.json` và lấy phần chưa dùng. Hạn mức mỗi lần
quét (hằng số đầu `add_news.py`): `REJECTED_PER_RUN = 20` tổng, trong đó `BAOMOI_REJECT_PER_RUN = 10`
là ứng viên Báo Mới — **chia đều 4 chuyên mục theo vòng xoay**, mỗi mục lấy bài mới nhất trước. Vòng
xoay đi theo thứ tự CNQS → Ngoại giao → Kinh tế → Chính trị nên mục thích hơn vẫn nhiều hơn (3-3-2-2);
mục nào hết bài thì mục khác lấp chỗ. (Xếp thuần theo độ ưu tiên thì hỏng: kho lệch nặng — có hôm 45
Kinh tế / 5 Ngoại giao — nên 1 mục ăn hết 10 slot, người dùng không thấy ứng viên của 3 mục còn lại.)
**Tổng mục Bị loại không cap theo số lượng** — chỉ giới hạn lượng thêm mỗi lần, để một lô ~80 ứng viên
Báo Mới không nhấn chìm loại tin giá trị hơn: tin ĐÚNG GU mà agent phải loại vì ngày/nghi trùng.

**Tự dọn mục quá 2 ngày** (`REJECTED_KEEP_DAYS = 1`): tính theo `addedAt` = **ngày được ĐƯA VÀO mục**,
KHÔNG phải ngày đăng bài — nên nhóm "tin đúng gu vừa rơi khỏi khung 3–7 ngày" vẫn vào được như cũ,
chỉ là nằm trong mục 2 ngày rồi tự rụng. Trạng thái ổn định ~80 mục (4 lô × 20), không phình vô hạn.
Mục cũ chưa có `addedAt` được đóng dấu ngày hiện tại để sống thêm một vòng thay vì biến mất ngay.
> ⚠️ Tin người dùng đã 👍 "kéo vào Bài mới" (`PROMOTED`) trước đây CHỈ lưu id trong localStorage
> `dt.promoted` rồi render lại từ `DATA.rejectedNews` — dọn mục là mất luôn tin đã cứu. Đã vá
> 22/07/2026: `rescueItem()` lưu thêm snapshot vào `dt.promotedSnap` và `rescuedItems()` fallback
> sang snapshot (đúng cách tính năng "Lưu tin"/`dt.fav` vẫn làm). Đã test trên trình duyệt thật.
Lệnh này **tự loại bài ngoài khung ngày** trước khi tới tay agent — nếu Action lỗi và file trong
repo là bản cũ, agent sẽ không nhìn thấy bài quá hạn, tránh việc guardrail chặn NGUYÊN LÔ và mất
cả bản tin. `baomoiNews` áp đúng khung ngày như tin thường (chốt chặn lớp hai).

**Không có chuyên mục quân sự riêng trên Báo Mới** (`quan-su`, `chinh-tri` đều 404 — đã kiểm chứng
22/07/2026); bài quân sự nằm lẫn trong `the-gioi`, bộ từ khoá `CAT4` ở đầu `scripts/baomoi_sync.py`
nhặt ra. Trang chuyên mục là Next.js: dữ liệu nằm trong `<script id="__NEXT_DATA__">`, item có
shape GIỐNG HỆT item của API bài đã lưu nên `baomoi_topics.py` dùng lại `normalize()` của
`baomoi_sync.py`. Quét chuyên mục chạy TRƯỚC và độc lập với bước cần cookie — cookie hết hạn
(err -801, xem `docs/baomoi-sync.md`) thì vẫn còn nguồn này.

`loadBaomoi` trong `index.html` VẪN GIỮ, thành đường nhanh: bài vừa bookmark hiện ngay trên web
mà không phải chờ tới phiên quét kế tiếp; khi phiên quét đã nạp bài đó vào `DATA` thì `loadBaomoi`
tự bỏ qua (nó dedupe theo tiêu đề). Nó đọc thẳng `baomoi-saved.json` nên tự động cũng chỉ hiện
bài trong 24h. Không có tab riêng, KHÔNG phân tích sở thích.
Khi Action fail vì cookie hết hạn (err -801) → làm mới cookie theo `docs/baomoi-sync.md`.
Endpoint chỉ cần cookie, KHÔNG kiểm tra `sig` (đã kiểm chứng 18/07/2026). Bộ lọc chủ đề:
`CAT4` ở đầu `scripts/baomoi_sync.py`.

## Nhập tin từ Google Drive (pipeline `drive-import` — CHỈ chạy bằng GitHub Action)
Action `import-news-from-drive.yml` (08:00 & 20:00 VN) tìm **mọi** file `ban-tin-chien-luoc-YYYY-MM-DD-HHMM-ICT.json`
trong khung 2 ngày trên Drive, **gộp tất cả thành 1 batch** (dedupe theo URL — ấn bản mới thắng; item ngoài
khung 2 ngày bị đẩy sang `rejectedNews` thay vì làm hỏng cả lô), rồi chạy `add_news.py`. Cần secret
`GOOGLE_DRIVE_FOLDER_ID` + `GDRIVE_API_KEY`. Log: `logs/gdrive-<ngày>.log` + `logs/state.json`.
**KHÔNG tạo routine Claude làm việc này nữa** — trước đây có cả routine Claude lẫn Action cùng nhập, trùng việc.
> Lỗi cũ đã sửa 21/07/2026: script xử lý từng file rồi cùng ghi đè `/tmp/new_items.json`, nên khi Drive có
> 2 ấn bản thì file chạy sau (ấn bản CŨ hơn) xoá sạch kết quả của ấn bản mới → mất tin âm thầm.

## Ghi chú vận hành
- **Hai routine nằm ở ĐÂU** (cập nhật 28/07/2026): đều là **scheduled task LOCAL trên máy Mac của Huy**, không phải routine trên claude.ai. Quản lý ở mục "Scheduled" trên sidebar, hoặc bằng tool `mcp__scheduled-tasks__*`. Cron **giờ LOCAL (Asia/Ho_Chi_Minh), KHÔNG phải UTC**. **NGUỒN SỰ THẬT về quy trình nằm TRONG REPO** (`docs/routine-web-scan.md` — `docs/routine-event-scan.md` từ 28/07/2026 chỉ còn là stub trỏ sang đó, xem banner đầu file đó); SKILL.md của các **scheduled task** (`~/.claude/scheduled-tasks/<taskId>/SKILL.md`) giờ chỉ là stub 5 dòng Read file repo tương ứng — **sửa quy trình thì sửa file trong docs/, ĐỪNG đụng stub**.

  ⚠️ **"Stub" ở đây CHỈ nói về `~/.claude/scheduled-tasks/*/SKILL.md`, KHÔNG phải `.claude/skills/quet-tin/SKILL.md` trong repo** (làm rõ 29/07/2026 sau khi câu cũ bị đọc thành mâu thuẫn). Skill `quet-tin` **là playbook NỘI DUNG thật, 460+ dòng, KHÔNG được rút thành stub**: `docs/routine-web-scan.md` Bước 2 và `.github/prompts/web-scan-ci.md` đều bảo phiên quét *"Đọc file `.claude/skills/quet-tin/SKILL.md` và làm ĐÚNG playbook trong đó"* — cho nó trỏ ngược lại `docs/` là **vòng tròn**, cả CI lẫn local mất sạch playbook. Phân vai: skill giữ **NỘI DUNG quét** (5 chủ đề, agent, guardrail, `scan-gaps.json`, phụ lục nguồn) · `docs/routine-web-scan.md` giữ **QUY TRÌNH CHẠY** (lịch, khoá, commit/push) · CLAUDE.md giữ **phạm vi + nguồn**. Bảng phân vai đầy đủ nằm ở đầu chính skill đó.

  | taskId | cron | Nguồn sự thật quy trình | Việc |
  |---|---|---|---|
  | `web-scan-diem-tin` | `30 4,5 * * *` (DỰ PHÒNG phiên SÁNG SỚM, sau CI 04:00/05:00) | `docs/routine-web-scan.md` (Bước 1-3 = bản tin, **Bước 4 = event-scan gộp**) | Bản tin 5 chủ đề **+ sự kiện/tập trận/think-tank** — phiên sáng sớm |
  | `web-scan-diem-tin-toi` | `15 21 * * *` (DỰ PHÒNG phiên TỐI, sau CI 21:00 — lớp CUỐI còn kịp hạn email 22:00) | `docs/routine-web-scan.md` (chung file với phiên sáng sớm để hai phiên không lệch nhau; mục "PHIÊN TỐI — BỐI CẢNH RIÊNG" cuối file) | Bản tin 5 chủ đề — phiên tối |
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
