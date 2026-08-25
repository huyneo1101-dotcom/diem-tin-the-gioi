# Telegram — gửi, canary, bot hỏi–đáp, đường Jay Lâm — Điểm Tin Thế Giới

> Xẻ từ `CLAUDE.md` ngày 25/08/2026 để bản thi hành gọn lại (luật mục 31 của `~/.claude/CLAUDE.md`).
> **Nội dung giữ NGUYÊN VĂN, không cắt chữ nào** — chỉ đổi chỗ ở. Bản thi hành: [`../../CLAUDE.md`](../../CLAUDE.md).

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

### 📤 GỬI TAY MỘT BẢN TIN CHO HUY: ĐI BẰNG BOT ĐIỂM TIN, KHÔNG PHẢI BOT CÁ NHÂN (Huy chốt 01/08/2026)

Nguyên văn: *"đmm không gửi qua điểm tin bot gửi qua rèn 66 bot làm cc gì"*.

**Cơ chế gây vấp:** mục 7c của CLAUDE.md toàn cục dạy *"tài liệu cho Huy đọc → gửi Telegram qua
`congcu/gui_tele.py`"*, và công cụ đó đi bằng **bot cá nhân `@ren66_bot`**. Luật ấy viết cho tài
liệu chung — báo cáo, bài phân tích, ghi chú — nhưng khi cần gửi tay một bản tin dựng lại thì phản
xạ vẫn với lấy đúng công cụ đó, vì nó là "công cụ gửi Telegram" duy nhất nhớ được. Sai chỗ dùng:
bản tin Điểm Tin có kênh riêng của nó (`@diemtin24h_bot`) — đó là nơi Huy đọc bản tin hằng ngày,
nơi Huy `/xoa` được tin rác, nơi bot trả lời câu hỏi về chính bản tin. Đẩy một bản tin sang bot
cá nhân là tách nó khỏi cả dòng chảy đó.

- **Bản tin, file `.docx` bản tin, bản dựng lại/bổ sung → `@diemtin24h_bot`.** Bot cá nhân chỉ
  dành cho tài liệu KHÔNG thuộc Điểm Tin.
- **Gửi cho AI CHAT NÀO: TOÀN BỘ danh sách chat — Huy VÀ Jay Lâm**, y hệt bản tự động. Huy chốt
  01/08/2026, nguyên văn: *"bản tin thì gửi cho cả Jay chứ thằng ngu"*.
  ⚠️ **Cơ chế gây vấp, đã vấp thật ngay lượt đầu:** repo này có sẵn một luật rất mạnh —
  *"cảnh báo hạ tầng gửi cho người vận hành, không gửi cho người đọc"* (canary) và
  *"mọi thứ rút ra từ chat của Jay Lâm chỉ đi tới chat chủ"* (tin đề xuất, hồ sơ độc giả). Cả hai
  đều đúng, và cả hai đều thu hẹp về `chat_chu()`, nên phản xạ khi gửi tay là thu hẹp theo. Nhưng
  chúng nói về **thứ nội bộ**, còn **bản tin là sản phẩm CHO người đọc** — Jay Lâm là người đọc,
  và bản dựng lại chính là bản thay cho bản đã hỏng mà anh ta đã nhận. Phân biệt theo **NỘI DUNG
  gửi đi**, không theo chuyện gửi tay hay tự động.
  | Gửi gì | Tới đâu |
  |---|---|
  | bản tin, `.docx` bản tin, bản dựng lại/bổ sung | **toàn bộ danh sách chat** |
  | cảnh báo canary, tin đề xuất, hồ sơ độc giả, bản sao file Jay Lâm gửi | chat **CHỦ** |
- **Chat id nằm NGOÀI repo** (repo này PUBLIC): `/Users/Huy/Claude/.tg-bot.json`, chmod 600,
  `chats[0]` = Huy · `chats[1]` = Jay Lâm. Trước 01/08 mảng đó RỖNG nên phiên local không biết
  gửi đi đâu — nay đã điền, và `nhin_truoc_kich_bot.py` cũng hết kích run cho chat lạ.
- **Mất danh sách thì dò lại thế này**, đừng đoán: đọc `chat_id` trong bảng `dt_bot_hoi` (mã
  `x-dt-key` ở `/Users/Huy/Claude/.dt-bot-key`), rồi gọi `getChat` từng id để lấy TÊN.
  `getUpdates` **không dùng được** — hàng đợi đã bị workflow xác nhận nên gần như luôn rỗng, và
  gọi kèm `offset` là nuốt mất câu hỏi đang chờ.
- **Đường gửi:** `send_telegram.send_document(token, chat, file, caption)` — đừng tự dựng lời gọi
  multipart mới.

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
lúc phiên còn đang làm đúng việc. Cùng lỗi với ca `toi` từng kêu khi lớp vét (khi đó 22:00, nay
21:47) chưa gửi xong.

**Hai nguyên tắc, đừng "dọn cho gọn" mất:**
1. **Kiểm ĐẦU RA, không kiểm quy trình.** Không hỏi "job có chạy không" (job xanh mà gửi rỗng
   vẫn là hỏng) mà hỏi "bản tin có tới tay không". Bằng chứng là **sổ đã gửi** — thứ chỉ được
   ghi ở BƯỚC CUỐI sau khi đã gửi xong mọi kênh, nên là dấu vết việc-đã-làm chứ không phải lời
   tự khai của một job.
2. **Người báo phải KHÁC người làm.** Workflow riêng, cron riêng, `permissions: contents: read`,
   không import gì của đường quét. Chết cùng lúc với routine thì nó vô nghĩa.

⏰ **Chạy sau LỚP CUỐI, không phải sau HẠN CHÓT.** Hạn email tối là 22:00 nhưng lớp vét CI 21:47
gửi tới ~22:10 — đó là thiết kế bình thường. Kêu lúc 22:05 là kêu oan, mà cảnh báo kêu oan vài
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

⛔ **PHẢI ĐẾM CẢ FILE, KHÔNG CHỈ TEXT — lỗ này CÂM từ ngày dựng 28/07, vá 30/07/2026.**
Bản đầu lọc `if not (m.get("text") or "").strip(): continue`, tức **mù hoàn toàn với update
dạng `document`**, trong khi `telegram_bot.py:388` xử lý `.docx` đầy đủ. Đúng lớp lỗi đã ghi ở
mục "hai bộ luật song song chắc chắn lệch": hai nơi cùng quyết định *update này có đáng xử lý
không* mà mỗi nơi một luật, nên **mọi file Jay Lâm gửi đều phải nằm chờ cron GitHub** — cron
mà chính mục này đo được là 66-148 phút một lần.
**Cơ chế gây vấp:** không có dấu hiệu nào để nghi. Script vẫn mã 0, log vẫn đều đặn dòng
*"Có 1 tin đang chờ → kích"*, chỉ là **mọi dòng đó đều do TEXT gây ra**. Số đo tối 30/07: file
tới trước bản tin ~20 phút và lỡ mất bản tin; hai file vào được hôm đó đều nhờ nguyên nhân
khác — id=1 (Supabase ghi 21:06:44) **ăn ké** lượt kích 21:06:24 do Huy nhắn text (đối chiếu
`dt_bot_hoi`: ba câu trả lời 21:08:10 · 21:10:07 · 21:11:33 khớp ba lượt kích 21:06/21:07/21:09),
id=2 (21:34:46) do phiên sau **kích tay**. Tức lớp kích-từ-máy **chưa từng tự kích vì một file**.
⚠️ **File KHÔNG xét `MAX_AGE_PHUT`** — khớp đúng nhánh `document` của workflow, nhánh đó cũng
không xét tuổi. Siết ở đây là dựng lại chính cảnh lệch luật vừa vá: file gửi đêm lúc máy ngủ,
sáng mở máy đã quá 360 phút ⇒ script lặng lẽ bỏ trong khi workflow vẫn nhận. Hướng lệch phải là
**kích thừa một run, không phải mất một file**. Text quá cũ thì vẫn bỏ như cũ.
⚠️ **File không phải `.docx` cũng kích** — workflow vẫn tốn một lượt để nhắn *"chỉ nhận .docx"*
cho người gửi; bỏ qua ở đây là người gửi ngồi chờ một phản hồi không bao giờ tới.
Bộ test canh: `tests/test-nhin-truoc-kich-bot.py` — **13 ca (05 ca PHẢI KÍCH) · `--tu-kiem` bắt
5/5 bản hỏng**, đã nạp `khoe.py`. Hai bản hỏng canh hai chiều ngược nhau của cùng phép miễn tuổi
(áp `MAX_AGE` cho cả file ⇒ đỏ ca 2 · miễn tuổi cho cả text ⇒ đỏ ca 7), vì siết và nới đều hỏng.

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

#### 📌 CHỈ THỊ GỐC CỦA CẢ MỤC NÀY — chat của Jay Lâm (Huy 27/07/2026 14:52)
> Nguyên văn: *"từ giờ, từ những đoạn chat của Jay Lâm, tự động thêm những tin tức mày thấy
> hợp lý vào web tin tức, đồng thời nghiên cứu sở thích/tư duy của người này liên quan đến
> vấn đề tin tức."*

Ghi lại 30/07/2026 sau khi rà quy tắc chưa ghi: hai vế của chỉ thị **đều đang chạy**, nhưng
tên "Jay Lâm" chỉ còn nằm trong `scripts/bot_luu.py` (docstring mẫu) và một dòng log — tức
**đường đi thì có, mệnh lệnh sinh ra nó thì không ai ghi**. Phiên sau đọc từng mảnh rời sẽ
tưởng đó là tính năng tự phát sinh và gỡ đi mà không biết đang gỡ một chỉ thị của Huy.

| Vế của chỉ thị | Chạy ở đâu | Trạng thái đo 30/07 |
|---|---|---|
| **"tự động thêm tin từ chat vào web"** | `.github/prompts/telegram-bot.md` mục *"Sau khi trả lời"* → trường `tin_de_xuat` → `scripts/bot_luu.py` ghi `dt_bot_hoi` + nhắn Huy | Chạy — **nhưng ở dạng ĐỀ XUẤT, không phải tự nạp** |
| **"nghiên cứu sở thích/tư duy"** | routine `ho-so-doc-gia` (cron `0 10 */3 * *`) → `scripts/ho_so_doc_gia.py` → bảng `dt_ho_so_doc_gia`; quy trình ở `docs/routine-ho-so-doc-gia.md` | Chạy thật lần đầu 10:04 ngày 30/07 — Jay 12 lượt hỏi, 2 tin đã đề xuất từ đó |

⚠️ **Vế 1 đã bị chính Huy hạ cấp trong CÙNG ngày 27/07** từ *"tự động thêm"* xuống *"chỉ đề
xuất, người duyệt là Huy"* (dòng ngay trên + `telegram-bot.md` dòng cuối mục 3). **Đây không
phải việc bỏ dở, đừng đi "hoàn thiện" nó bằng cách cho bot gọi `add_news.py`** — nạp thẳng
tin lên bản tin công khai từ một đoạn chat riêng là đúng thứ Huy chốt không làm.

⛔ **Ràng buộc kênh — Jay Lâm là NGƯỜI NGOÀI, không phải người vận hành.** Mọi thứ RÚT RA từ
chat của người này (hồ sơ sở thích, tin đề xuất, nguyên văn câu hỏi) là **báo cáo cho Huy**,
chỉ được đi tới **một** người: `tin_de_xuat` gửi chat **đầu tiên** trong `TELEGRAM_CHAT_ID`
(`telegram_bot.py:chat_chu()`), hồ sơ độc giả gửi qua **`@huyclaude_bot`** bằng
`viec_bot.py --bao`. Cơ chế gây vấp: `TELEGRAM_CHAT_ID` của repo này có **cả Jay Lâm**, nên
mọi script lặp qua cả danh sách sẽ gửi hồ sơ về chính người bị lập hồ sơ. Cùng luật với
canary: *cảnh báo/báo cáo vận hành gửi cho người vận hành, không gửi cho người đọc.*

### 🔄 ĐẢO NGUYÊN TẮC 01/08/2026 — FILE JAY LÂM GỬI LÀ **BỘ LỌC**, KHÔNG PHẢI NGUỒN TIN

> Nguyên văn Huy: *"thay đổi hoàn toàn nguyên tắc. file của Jay Lâm gửi chỉ là để so sánh xem
> có tin nào mày quét được mà bị trùng với tin trong file đó không thôi"* · *"nếu có tin bị
> trùng với file Jay Lâm thì tự xoá khỏi tổng hợp tin đã quét đi và gửi file word (trong đó
> không có tin nào từ Jay Lâm)"*.

**Mục 5 "Tin Jay Lâm gửi" BỎ HẲN.** File Jay gửi không còn đóng góp một dòng nào vào bản tin;
nó chỉ dùng để **loại bớt tin của chính mình**: tin nào mình quét được mà Jay đã có thì bỏ đi,
vì anh ta đọc rồi. Bản tin gửi ra vì thế chỉ còn phần Jay CHƯA có.

✅ **ĐÃ VÁ XONG MÃ 02/08/2026.** Mọi mô tả về mục 5 trong file này đã gỡ; thứ còn lại là đường
NHẬN file (không đổi) và ba lệnh mới của `tin_jaylam.py`.

| Mảnh | Việc |
|---|---|
| `scripts/tin_jaylam.py --liet-ke` | In dữ liệu đối chiếu: **TOÀN VĂN** với file chưa trích, **BẢNG GỌN** với file đã trích (rẻ hơn ~90%, dùng suốt 3 ngày file còn hiệu lực). Đóng sổ `da_gop` dòng hết khung ngay tại chỗ đọc |
| `scripts/tin_jaylam.py --ghi` | Lưu **BẢNG ĐỐI CHIẾU** trích từ file Jay vào cột `tom_tat` (JSON), đặt `da_xu_ly=true`. Guardrail: id ngoài khung/trùng · `tin` rỗng · tiêu đề ngoài 10-200 · cảnh báo TRÍCH SÓT |
| `scripts/tin_jaylam.py --ghi-loai` | Ghi sổ `logs/trung-jaylam.json` — tin **CỦA MÌNH** bị bỏ. Guardrail: url phải http(s) · `tieu_de` 10-300 · **`trung_voi` bắt buộc** · `id_jay` bắt buộc. Dedupe theo url, giữ `GIU_NGAY = 7` |
| `.github/scripts/make_docx.py` | `doc_url_trung_jaylam()` đọc sổ, `loc_bo_trung_jaylam()` bỏ tin khỏi **CẢ BA** mục (`usNews`/`worldNews`/`events`), CẢ HAI buổi. Không còn chạm Supabase |
| `tests/test-tin-jaylam-xu-ly.py` | **39 ca · `--tu-kiem` bắt 19/19 bản hỏng** |
| `tests/test-tin-jaylam-trong-docx.py` | **20 ca · `--tu-kiem` bắt 11/11 bản hỏng** |

⚠️ **Sổ `logs/trung-jaylam.json` phải `git add logs/` cùng bản tin** — không thì `make_docx.py`
chạy trong workflow không thấy sổ và bản .docx vẫn lặp tin. Thiếu sổ là **fail-open CÓ TIẾNG**:
in một dòng cảnh báo rồi giữ nguyên tin. Hướng lệch có chủ ý là LẶP tin (Huy thấy được), không
phải MẤT tin.
⚠️ **Khung ngày dùng khung RỘNG NHẤT (`MAX_AGE_DAYS_CNQS` = 3), không phải khung mặc định.** Tin
CNQS Mỹ của mình được nới 3 ngày lùi, nên file Jay gửi hôm nay còn phải làm bộ lọc cho tới bản
tin của 3 ngày sau — cắt ở 2 ngày là để lọt đúng nhóm đăng thưa nhất. Đây là chỗ Huy chốt *"mọi
bản tin còn trong khung ngày (2-3 ngày), không phải chỉ bản kế tiếp"*.

**04 quyết định Huy chốt qua bảng chọn, dùng làm spec khi vá:**

| # | Điểm | Chốt |
|---|---|---|
| 1 | So trùng bằng gì | **Agent đọc hiểu theo SỰ KIỆN**, có link thì link là chốt chắc |
| 2 | `scripts/tin_jaylam.py` | **Đổi mục đích**: thôi tóm tắt để đăng, chuyển sang **trích danh sách tin trong file Jay** làm bảng đối chiếu. Giữ nguyên hàng chờ · `da_gop` · guardrail |
| 3 | Phạm vi lọc | **Mọi bản tin còn trong khung ngày (2-3 ngày)**, không phải chỉ bản kế tiếp |
| 4 | Bản tối 01/08 đã lỡ gửi | Đã dựng lại bản không có tin Jay và **gửi lại cả hai chat** lúc 22:5x |

⚠️ **SO LINK THUẦN LÀ VÔ DỤNG — đã đo, đừng dựng lại đường đó.** Đối chiếu 12 tin quét tối
01/08 với 37 URL trong file Jay: **0 tin trùng URL**, trong khi đọc hiểu ra **03 tin trùng
sự kiện** (Mahan Air · tuần tra Scarborough · NITE-STAR 981 triệu USD). Lý do: Jay viết lại
bằng tiếng Việt từ nguồn khác hẳn nguồn mình lấy. Link chỉ dùng làm chốt CHẮC khi tình cờ
trùng, không dùng làm phép lọc chính.
⚠️ **Đối chiếu phải so với FILE GỐC, không so với danh sách tin đã trích/viết lại.** Vấp thật
trong chính lượt dựng bản thay thế: danh sách 29 tin viết lại của phiên trước **đã qua lọc
trùng rồi**, nên đúng những tin trùng lại vắng mặt trong đó — dùng nó làm bảng đối chiếu thì
kết luận "không có tin nào trùng".
⚠️ **Tin bị loại phải ghi lại** (`logs/loai-tin.md` hoặc dòng kêu trong log workflow) kèm mảnh
tương ứng bên file Jay — xoá tin là mất nội dung, phải soi ngược được.

### 📎 ĐƯỜNG NHẬN: Jay Lâm gửi file .docx qua bot → `dt_jaylam_inbox` (dựng 30/07/2026)

Huy hỏi 30/07: *"Jay Lâm gửi vào bot tin tức trên tele 1 file docx thì mày có đọc được và tự
tổng hợp vào file docx cuối ngày không?"* — đường NHẬN dựng hôm đó vẫn nguyên vẹn; chỉ VAI của
nội dung nhận về là đã đảo (01/08: từ NGUỒN TIN thành BỘ LỌC, xem mục ngay trên).

| Mảnh | Việc |
|---|---|
| Bảng Supabase `dt_jaylam_inbox` | `chat_id, ten, ten_file, noi_dung, ngay_vn, da_gop, created_at, tieu_de, tom_tat, da_xu_ly` (+ `nguon_ten, nguon_url, la_cnqs` — **di sản thiết kế cũ, KHÔNG còn ai ghi/đọc**). RLS: INSERT mở cho anon (giống `dt_bot_hoi`) · SELECT/UPDATE chỉ qua `dt_ma_hop_le()` (mã `x-dt-key`) |
| `scripts/docx_text.py` | Bóc chữ từ `.docx` bằng `zipfile` + regex trên `word/document.xml` — KHÔNG cần `python-docx` chỉ để ĐỌC |
| `scripts/telegram_bot.py::xu_ly_tin_jaylam()` | Chạy NGAY trong `--doc` (rẻ, không cần `claude -p`, giống lệnh `/xoa`): **bỏ qua file của CHAT CHỦ** (xem `_la_chat_chu`), từ chối nếu không phải `.docx`, tải bằng `tg_api.tai_file()`, trích chữ, ghi Supabase (`da_gop=false`), xác nhận NGẮN cho người gửi, và **gửi bản sao file về chat chủ** |
| `scripts/tin_jaylam.py` | Bước của PHIÊN QUÉT (CẢ HAI buổi): `--liet-ke` in dữ liệu đối chiếu + đóng sổ dòng hết khung · `--ghi` lưu bảng đối chiếu trích từ file · `--ghi-loai` ghi sổ `logs/trung-jaylam.json`. Xem mục "ĐẢO NGUYÊN TẮC" ngay trên |
| `.github/scripts/make_docx.py` | **KHÔNG còn mục 5 và KHÔNG còn chạm Supabase.** Chỉ đọc `logs/trung-jaylam.json` rồi bỏ tin của mình khỏi CẢ BA mục (`doc_url_trung_jaylam` / `loc_bo_trung_jaylam`) |

⚠️ **`tom_tat` nay chứa BẢNG ĐỐI CHIẾU dạng JSON, không phải tóm tắt-để-đăng.** Cột đó vốn giữ
tóm tắt của thiết kế cũ; tái dùng làm chỗ chứa bảng trích là cố ý — mã `x-dt-key` chỉ có quyền
SELECT/UPDATE, thêm cột mới phải chạy migration bằng tay, mà một cột text đủ dùng. `tieu_de`
nay chỉ là nhãn `"Bảng đối chiếu: N tin"`.
⚠️ **KHÔNG lưu file gốc hay toàn văn vào repo** — repo này **PUBLIC** (cùng lý do `bot_luu.py`
không ghi câu hỏi vào file trong repo). Toàn văn đi qua Supabase; sổ `logs/trung-jaylam.json`
chỉ chứa URL + tiêu đề tin CỦA MÌNH (vốn đã công khai) và một dòng `trung_voi` là tiêu đề tin
thời sự — không chứa ghi chú riêng của Jay Lâm.
⚠️ **`tai_file()` (trong `tg_api.py`) giữ token ngoài `argv`** — đi qua `curl -K -` (stdin) như
`call()`, không để token lộ trong `ps aux`.
⚠️ **Mã `x-dt-key` đọc theo CÙNG quy ước với `telegram_bot.py:_dt_bot_key()`** — env `DT_BOT_KEY`
trước, lùi về file `/Users/Huy/Claude/.dt-bot-key` (chỉ có ở máy Huy).
⚠️ **Chưa quét được ảnh/PDF/text dán thẳng** — Huy xác nhận Jay Lâm gửi dưới dạng `.docx`; file
khác định dạng bị `xu_ly_tin_jaylam()` từ chối kèm lời nhắc gửi lại đúng `.docx`.

⚠️ **TRẦN ĐỘ DÀI TỪNG CẮT MẤT 42% NỘI DUNG TRONG IM LẶNG — vá 30/07/2026, ngay lô đầu tiên.**
File thật đầu tiên Jay Lâm gửi (`29.7 ĐTN huong M.docx`, 21:06 ngày 30/07) dài **34.525 ký tự /
76 URL**; `JAYLAM_MAX_CHARS = 20000` xén còn 20.001, **mất 14.524 ký tự và 20 URL** — cắt ngang
giữa một URL, mất trọn mục AUKUS và mục viện trợ Australia–Việt Nam. **Cơ chế gây vấp:** trần
đặt theo phỏng đoán lúc dựng, chưa ai đo file thật; `docx_text.trich()` cắt xong chỉ thêm dấu
`…` rồi trả về, nên bên gọi **không còn đường nào biết độ dài gốc** — file vừa đúng trần và file
bị xén một nửa cho ra cùng một con số. Tin xác nhận vẫn báo *"Đã nhận: … (20001 ký tự)"*.
- Trần nay **200.000** (vẫn giữ để chặn file khổng lồ làm vỡ payload Supabase).
- `xu_ly_tin_jaylam()` **trích ĐỦ trước** (`max_chars=0`), đo `do_dai_that`, rồi mới cắt — và khi
  cắt thật thì **báo thẳng trong tin xác nhận** cho người gửi + in stderr. Fail-open CÓ TIẾNG.
- **Đừng gộp hai bước lại "cho gọn"** (`trich(tmp, max_chars=JAYLAM_MAX_CHARS)`): cắt trước khi
  đo là mất luôn đại lượng dùng để so ngưỡng.
- Với vai BỘ LỌC, cắt nội dung còn nguy hơn trước: phần bị cắt là phần **không bao giờ được đối
  chiếu**, nên tin tương ứng lọt vào bản tin dù Jay Lâm đã có — mà không dấu hiệu nào.

### 📤 BẢN SAO FILE PHẢI VỀ THẲNG CHAT CỦA HUY TRÊN TELEGRAM (chỉ thị Huy 30/07/2026)

> Nguyên văn: *"Jay Lâm gửi file docx lên bot điểm tin thì phải copy file đó gửi cho tao trên
> tele. Một ngày Jay có thể gửi 2-3 file."*

Trước đó file chỉ chảy vào Supabase rồi tối mới hiện ra dưới dạng **tin đã tóm tắt** trong mục 5
của `.docx` bản tin — tức Huy **không bao giờ cầm được file gốc**, mà tóm tắt thì mất bảng biểu,
mất thứ tự mục, mất phần bị bộ lọc chống trùng gạt đi. Với nhịp 2-3 file/ngày thì đó là 2-3 lần
mất bản gốc mỗi ngày.

`telegram_bot.py::gui_ban_sao_cho_chu()` — `sendDocument` với **chính `file_id`** (Telegram dùng
lại file đã có trên máy chủ, không phải tải lên lần nữa; `file_id` chỉ dùng lại được bởi CÙNG
bot, ở đây đúng vậy). Gửi tới `chat_chu()`, đúng ràng buộc kênh của mục này.

⚠️ **Lời gọi đặt TRƯỚC bước tải/trích/lưu, không phải sau — cố ý.** Ba nhánh phía sau đều hỏng
được (tải hỏng · file rỗng · Supabase từ chối), mà lỗi phía bot không phải lý do để Huy mất file
người ta đã gửi. Đặt sau là mất bản sao đúng lúc cần nhất. Bản hỏng *"dời lời gọi xuống sau bước
tải"* trong `--tu-kiem` canh đúng chỗ này và làm đỏ **đúng 01 ca** (nhánh tải hỏng) — hai ca còn
lại vẫn xanh, nên phép thay kiểu **xoá hẳn** lời gọi không đo được thứ tự, đừng dùng.
⚠️ **Không gửi ngược cho chính chat chủ** khi Huy tự gửi file (có ca đối chứng canh).
⚠️ **Gửi hỏng thì KÊU stderr nhưng KHÔNG làm hỏng luồng nhận** — file vẫn phải vào Supabase.
Ngược lại, im lặng khi hỏng là Huy tưởng hôm đó Jay không gửi gì.
⚠️ **Caption không mang nội dung file** (luật 3b: log Actions của repo PUBLIC), chỉ có tên người
gửi + tên file.

### ⛔ FILE DO CHÍNH HUY GỬI KHÔNG PHẢI TIN — không vào hàng chờ (30/07/2026)

> Nguyên văn Huy: *"tao gửi file word lên thì không phải tổng hợp tin"*.

**Cơ chế gây vấp:** nhánh `document` trong `telegram_bot.py::doc()` nhận file của **MỌI chat
trong danh sách cho phép**, mà `TELEGRAM_CHAT_ID` có cả Huy — nên file Huy tự gửi (bản tin vừa
dựng, tài liệu đang đọc, file gửi nhầm) đều lặng lẽ vào `dt_jaylam_inbox` rồi quay lại ở mục 5
của chính bản tin hôm đó. Không lỗi, không cảnh báo, và tin xác nhận còn hứa *"sẽ vào bản tin
TỐI hôm nay"* nên đọc vào là tưởng đúng ý.

`telegram_bot.py::_la_chat_chu(chat)` — so BẰNG chuỗi với `chat_chu()`, chặn ngay đầu
`xu_ly_tin_jaylam()`. Bốn chốt, đều có ca test:
- **Đặt TRƯỚC cả phép kiểm `.docx`** — với chat chủ thì loại file không quan trọng, file nào
  cũng không phải tin; dạy Huy về đuôi file ở đó là lạc đề.
- **Vẫn xác nhận, và NÓI RÕ là không lên bản tin** (chỉ thị Huy) — im lặng thì Huy tưởng nó đã
  vào hàng chờ như file của người ngoài.
- ⚠️ **So BẰNG, tuyệt đối không so chuỗi con**: id Telegram của hai người có thể là tiền tố của
  nhau, mà nhận nhầm người ngoài thành chat chủ nghĩa là **MẤT TIN** của họ — hướng lệch tệ
  nhất. Ca 16 dựng đúng cặp id chuỗi con để canh chiều nới này.
- ⚠️ **Không xác định được chat chủ (`TELEGRAM_CHAT_ID` rỗng) → KHÔNG chặn ai**, xử lý y như
  trước bản vá: thà nhận thừa một file còn hơn nuốt mất tin.
- ⚠️ **Bản vá này che mất chốt trong `gui_ban_sao_cho_chu`** (hàm đó không còn được gọi tới khi
  chat == chủ), làm ca cũ *"chat chủ tự gửi file → KHÔNG chuyển tiếp ngược"* mất răng. Đã neo
  lại bằng một ca **gọi THẲNG `gui_ban_sao_cho_chu`**; ca cũ nay là ca hành vi tổng thể được
  hai lớp bảo vệ nên cố ý KHÔNG khai vào `BAN_HONG` nào.

⚠️ **TRẦN ĐỘ DÀI TỪNG CẮT MẤT 42% NỘI DUNG TRONG IM LẶNG — vá 30/07/2026, ngay lô đầu tiên.**
File thật đầu tiên Jay Lâm gửi (`29.7 ĐTN huong M.docx`, 21:06 ngày 30/07) dài **34.525 ký tự /
76 URL**; `JAYLAM_MAX_CHARS = 20000` xén còn 20.001, **mất 14.524 ký tự và 20 URL** — cắt ngang
giữa một URL, mất trọn mục AUKUS (chuyến thăm Mỹ của Bộ trưởng Công nghiệp Quốc phòng Úc) và mục
viện trợ Australia–Việt Nam. **Cơ chế gây vấp:** trần đặt theo phỏng đoán lúc dựng, chưa ai đo
file thật; `docx_text.trich()` cắt xong chỉ thêm dấu `…` rồi trả về, nên bên gọi **không còn
đường nào biết độ dài gốc** — file vừa đúng trần và file bị xén một nửa cho ra cùng một con số.
Tin xác nhận vẫn báo *"Đã nhận: … (20001 ký tự)"*, tức cả người gửi lẫn Huy đều tưởng đủ.
- Trần nâng lên **200.000** (vẫn giữ để chặn file khổng lồ làm vỡ payload Supabase).
- `xu_ly_tin_jaylam()` nay **trích ĐỦ trước** (`max_chars=0`), đo `do_dai_that`, rồi mới cắt —
  và khi cắt thật thì **báo thẳng trong tin xác nhận** cho người gửi + in stderr. Fail-open CÓ
  TIẾNG; im lặng ở đây là dựng lại đúng vùng câm vừa bịt.
- **Đừng gộp hai bước lại "cho gọn"** (`trich(tmp, max_chars=JAYLAM_MAX_CHARS)`): cắt trước khi
  đo là mất luôn đại lượng dùng để so ngưỡng.
- Bộ test `tests/test-nhan-tin-jaylam.py` nay **12 ca · `--tu-kiem` bắt 2/2 bản hỏng** (trả trần
  về 20.000 ⇒ đỏ ca hồi quy 34.525 ký tự · cắt mà nuốt lời cảnh báo ⇒ đỏ ca PHẢI KÊU), kèm 01 ca
  đối chứng chống kêu oan (file dưới trần không được nhắc chuyện cắt). Bộ này trước đó **không
  có `--tu-kiem`** — đã bổ sung cùng lượt, nạp module qua seam `TGBOT_MOD`, tên bản hỏng mang
  **PID + sha1 nội dung** (nạp bằng `importlib` nên không có sha1 là dính lại `.pyc` bản trước).

### 📜 ĐÃ XOÁ 01/08/2026 — toàn bộ thiết kế "mục 5 Tin Jay Lâm gửi"

Bốn mục từng nằm ở đây (BỐN ĐIỂM CHỐT 30/07 · nhánh dán nguyên văn · bảng đóng sổ `da_gop` ·
"mục 5 mở cho cả bản sáng") mô tả một thiết kế **không còn tồn tại trong mã**: mục 5 đã bỏ hẳn
khi Huy đảo nguyên tắc, cùng với `tach_chua_tom_tat` · `loc_jaylam_ca_sang` · `loc_trung_jaylam`
· `add_jaylam_item` · `danh_dau_da_gop_jaylam` · `jaylam_qua_han` · `JAYLAM_MAX_AGE_DAYS*`.
Giữ tài liệu của mã đã xoá là gài lỗi cho phiên sau — nó sẽ đi tìm hàm không có, hoặc tệ hơn,
dựng lại chúng. Cần soi lịch sử thì `git log -- .github/scripts/make_docx.py`.

**Ba bài học của đợt đó vẫn còn hiệu lực, đã chuyển sang chỗ dùng được:**
- *khung ngày 2 ngày, CNQS Mỹ nới 3 ngày* → nay là khung file Jay Lâm còn hiệu lực làm bộ lọc,
  `tin_jaylam.py::MAX_AGE_DAYS_CNQS`; vẫn đăng ký `HeThong/dong-bo-luat.py`;
- *đánh dấu `da_gop` phải đứng SAU khi việc thật sự xong* → nay `--liet-ke` đóng sổ dòng hết
  khung ngay tại chỗ đọc, không còn phụ thuộc `doc.save()`;
- *một lớp lọc bỏ sót một mục là hỏng câm* → ca [01]-[03] của
  `tests/test-tin-jaylam-trong-docx.py` canh cả ba mục.

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
