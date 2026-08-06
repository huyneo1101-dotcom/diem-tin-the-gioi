# Bot Telegram — hỏi đáp, lịch sử chat, quét kênh, học từ người đọc

<!-- Xẻ từ `CLAUDE.md` ngày 06/08/2026 để cắt chi phí token: toàn bộ file gốc được nạp lại
ở MỌI lượt của MỌI phiên đụng repo này (đo thật: ~99.000 token/lượt), trong khi phần lớn nội dung
là NHẬT KÝ VÁ LỖI chỉ cần đọc khi đụng đúng mảng đó.
⚠️ Nội dung dưới đây giữ NGUYÊN VĂN — cả luật lẫn "cơ chế gây vấp". Đừng rút gọn: phần kể lại
cơ chế chính là thứ ngăn phiên sau dựng lại đúng cái lỗi cũ.
⚠️ CLAUDE.md còn dòng trỏ sang từng mục. Đổi tên mục ở đây thì sửa dòng trỏ bên đó. -->

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
