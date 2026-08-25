# Gửi bản tin — kênh, sổ đã gửi, file Word, kích notify — Điểm Tin Thế Giới

> Xẻ từ `CLAUDE.md` ngày 25/08/2026 để bản thi hành gọn lại (luật mục 31 của `~/.claude/CLAUDE.md`).
> **Nội dung giữ NGUYÊN VĂN, không cắt chữ nào** — chỉ đổi chỗ ở. Bản thi hành: [`../../CLAUDE.md`](../../CLAUDE.md).

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

### 📩 EMAIL TỐI GỒM NHỮNG GÌ (chỉ thị Huy 27/07/2026 — quy tắc chốt)

> **Email tối = TOÀN BỘ tin đã quét được trong ngày, TRỪ ba loại:**
> 1. tin đã quét ở **phiên sáng sớm 03:47/04:47** (chúng đã đi trong email `📰 … BUỔI SÁNG`);
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

⚠️ **ĐÍNH CHÍNH 30/07/2026 — hai gạch đầu dòng trên nói về CƠ CHẾ, nhưng cơ chế bảo đảm "bản tối vẫn
có tin quét tay" nay KHÔNG còn là `loc_chua_gui`.** Đo thật trong `send_telegram.py`: nhánh tối đặt
`msgs = []` (dòng 366) theo chỉ thị Huy 27/07 *"chỉ gửi file word thôi"*, nên tin nhắn **không liệt kê
tin nào**; hai lời gọi `loc_chua_gui` ở dòng 308–309 chỉ còn chảy vào `total`, tức **con số trong
caption** *"— N tin mới"*. Thứ thật sự giữ đủ tin cho bản tối là **`.docx` cố ý KHÔNG lọc sổ** (dòng
cuối bảng dưới). Cộng thêm `GUI_EMAIL='0'` từ 27/07 nên thân email cũng không còn tồn tại.
**Hệ quả phải biết, đừng đọc bảng dưới theo nghĩa cũ:** sổ đã gửi hiện còn đúng **hai** người đọc có
tác dụng — (i) `canary.py` đọc để biết bản tin đã tới tay chưa (đây mới là công dụng chính hiện nay,
được `tests/test-canary-ban-tin.py` canh); (ii) con số caption Telegram. **Bật lại email
(`GUI_EMAIL='1'`) hoặc bật lại `build_messages` thì bảng dưới trở lại đúng nguyên văn** — vì thế giữ
nguyên lời gọi `loc_chua_gui`, đừng "dọn cho gọn" bằng cách gỡ nó.
⚠️ Kèm theo: ca 9 của `tests/test-so-da-gui.py` (*"sổ PHẢI còn người đọc"*) đếm lời gọi `loc_chua_gui`
trong `send_telegram.py` — nó **vẫn xanh và vẫn đúng về chữ**, nhưng thứ nó canh nay chỉ là con số
caption chứ không phải bộ tin gửi đi. Người đọc sổ mạnh nhất (`canary.py`) do bộ test khác canh. Đừng
đọc ca 9 thành *"sổ đang lọc tin khỏi bản tối"*.

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

| Thứ | Lọc sổ? | Đang chạy? (đo 30/07) | Vì sao |
|---|---|---|---|
| **Thân email tối** (`send-email.js`) | **CÓ** | **KHÔNG** — `GUI_EMAIL='0'` từ 27/07 | là thông báo — lặp tin đã báo thì thừa |
| **Tin nhắn Telegram** (`send_telegram.py`) | **CÓ** | **chỉ còn con số caption** — `msgs=[]`, không liệt kê tin | cùng vai với thân email; bật lại `build_messages` thì đúng nguyên văn |
| **File `.docx` đính kèm** (`make_docx.py`) | **CÓ, nhưng HẸP** — chỉ bỏ tin của ca SÁNG cùng ngày (`loc_bo_tin_ca_sang`), xem mục ngay dưới | **CÓ** — đây là kênh duy nhất mang nội dung | tin quét TAY giữa ngày không ghi sổ nên vẫn được giữ, đúng chỉ thị *"gửi file word tối nay… thì gộp cả 11 tin hôm nay đó vào"* |
| **Canary** (`canary.py`) | — chỉ ĐỌC sổ | **CÓ** | công dụng chính của sổ hiện nay: bằng chứng bản tin đã tới tay |

### 🌅 BẢN SÁNG GỘP TIN CA TỐI HÔM QUA (Huy chốt 26/08/2026)

Nguyên văn: *"từ giờ bản tin 4h sáng hãy gộp cả tin quét được lúc 9h tối vào, nhớ đối chiếu với
cả file Jay Lâm gửi để chống trùng lặp"*.

**Vì sao tin ca tối vắng mặt trong bản sáng trước đó:** `pick_items` lấy HỢP của (mới so với
commit cha) và (`_addedDate == generatedAt`). Phiên sáng ghi `generatedAt` là ngày MỚI nên tin nạp
tối qua không phải "hôm nay"; còn commit cha lại chính là commit của lô tối qua nên chúng cũng
không "mới". Tin rơi khỏi cả hai vế, không lệnh nào báo — .docx vẫn ra đời đủ mục.

| Mảnh | Việc |
|---|---|
| `make_docx.py::gop_tin_ca_toi(items, cur, kind, now)` | Bản SÁNG gộp thêm tin có `_addedDate` = HÔM QUA; bản TỐI không gọi |
| `make_docx.py::_doc_url_buoi(buoi, ngay)` | Một đường đọc sổ đã gửi dùng chung cho cả lọc bản tối lẫn gộp bản sáng |
| `make_docx.py::_khoa_tin(it)` | Khoá nhận dạng: `sourceUrl`, thiếu link thì lùi về tiêu đề + tóm tắt |
| `tests/test-gop-tin-ca-toi.py` | **18 ca · `--tu-kiem` bắt 7/7 bản hỏng**, đã nạp `BO_TEST` của `HeThong/khoe.py` |

- ⛔ **Chỉ trừ tin đã gửi ở ca SÁNG hôm qua, KHÔNG trừ theo dòng `toi`.** Trừ theo `toi` là xoá
  đúng nhóm tin vừa được lệnh gộp vào. Nhóm phải loại là bản sáng hôm qua — lặp lại nó nghĩa là
  đọc cùng một tin hai buổi sáng liền. Ca [07] và [12] canh hai chiều này.
- ⛔ **Gộp phải đứng TRƯỚC bộ lọc Jay Lâm trong `main()`.** File Jay Lâm thường tới SAU bản tin
  tối — đo 25/08/2026: bản tối gửi khoảng 22:10, file `ĐTN_M_25.8.2026.docx` tới 23:29 — nên
  nhóm tin ca tối là nhóm **chưa từng được đối chiếu**, tức nhóm cần lọc nhất. Gộp sau bộ lọc thì
  chúng đi thẳng vào bản tin, không dấu hiệu nào. Ca [09]-[11] canh đúng chỗ đó.
- ⚠️ **FAIL VỀ PHÍA GỘP DƯ:** sổ đã gửi thiếu hoặc hỏng ⇒ không trừ được gì, bản sáng lặp lại tin
  của bản sáng hôm qua — Huy thấy ngay khi đọc. Hướng ngược lại là mất tin trong im lặng.
- ⚠️ **Khoá nhận dạng không được rỗng.** Tin thiếu link (hay gặp ở mục tập trận) mà cùng mang khoá
  `""` thì tin ca tối bị coi là đã có rồi rơi khỏi bản tin. Ca [18] là ca duy nhất lộ được lỗi
  này: phải có tin SÁNG NAY cũng thiếu link thì khoá rỗng mới nằm sẵn trong tập đã-có.
- ⚠️ **Phiên quét sáng phải đối chiếu Jay Lâm cho CẢ tin ca tối hôm qua**, không chỉ lô vừa nạp —
  xem bước 3b của `.github/prompts/web-scan-ci.md`.

### ⛔ BẢN TỐI LẶP NGUYÊN SI TIN CA SÁNG — luật có mà KHÔNG ai thi hành (vá 01/08/2026)

**Huy bắt được:** tin Healio *"Uỷ ban HELP Thượng viện bỏ phiếu thông qua đề cử Giám đốc CDC…"*
(`healio.com/news/pediatrics/20260730/senators-vote-to-advance-schwartz-cdc-nomination`) nằm trong
CẢ bản `.docx` sáng lẫn bản tối 31/07. Đo toàn sổ thì đây không phải tin lẻ: **100% tin ca sáng
lặp lại trong bản tối, cả 4/4 ngày còn trong sổ** — 28/07 **9/9** · 29/07 **17/17** · 30/07
**16/16** · 31/07 **6/6**.

**Cơ chế gây vấp — luật không hỏng, LỚP THI HÀNH của nó biến mất.** Mục *"📩 EMAIL TỐI GỒM NHỮNG
GÌ"* ở trên khai rõ từ 27/07: bản tối = tin cả ngày **TRỪ tin đã quét ở phiên sáng sớm**. Lúc đó
người thi hành là **thân email** (`send-email.js` gọi `loc_chua_gui`), còn `.docx` cố ý KHÔNG lọc
vì nó chỉ là file đính kèm của lá thư đã lọc. Cùng ngày 27/07, `GUI_EMAIL='0'` tắt email ⇒ `.docx`
thành **kênh DUY NHẤT mang nội dung**, tức vai trò của nó đổi hẳn mà chú thích *"KHÔNG lọc sổ ở
đây"* thì đứng nguyên. Từ đó luật sống trong tài liệu, không sống trong mã. Không lỗi, không cảnh
báo, `.docx` vẫn ra đời đủ mục — chỉ là mỗi tối đọc lại nguyên bộ tin đã đọc sáng.

| Mảnh | Việc |
|---|---|
| `so_da_gui.py::url_da_gui_buoi(buoi, ngay)` | URL đã gửi ở ĐÚNG một buổi trong ĐÚNG một ngày VN |
| `make_docx.py::loc_bo_tin_ca_sang(items, now)` | Bản TỐI bỏ tin trùng dòng `sang` cùng ngày; bản SÁNG không lọc |
| `make_docx.py::main()` | gọi cho CẢ `usNews` · `worldNews` · `events` |
| `tests/test-so-da-gui.py` | **14 ca · `--tu-kiem` bắt 8/8 bản hỏng** |

⚠️ **TUYỆT ĐỐI KHÔNG bọc `loc_chua_gui` vào `main()`** — chú thích cũ cảnh báo đúng chỗ này, chỉ
sai ở chỗ kết luận "vậy thì đừng lọc gì cả". `loc_chua_gui` đọc TOÀN sổ, nên bản dựng lại trong
ngày (`-bo-sung`, gửi bù bằng tay) sẽ thấy chính lô của mình đã nằm trong sổ và ra file **RỖNG**.
Ca 11 canh đúng chiều này; bản hỏng *"lọc theo toàn sổ"* làm nó đỏ.
⚠️ **Chỉ đọc dòng `buoi == "sang"`, và chỉ của NGÀY HÔM NAY.** Tin quét TAY giữa ngày vốn không
ghi sổ (chỉ ca chính thức mới ghi, xem `tu_dong=1`) nên tự nhiên không bị đụng — giữ đúng chỉ thị
*"quét tay xong có gửi email thì email tối vẫn phải có các tin đó"*.
⚠️ **Bản tin trôi qua nửa đêm thì không lọc gì** (ngày mới không khớp dòng `sang` hôm trước). Cố ý:
hướng lệch là LẶP một bản tin, không phải MẤT tin. Ca 13 canh chiều nới của phép so ngày.
⚠️ **Bài học chung, rộng hơn ca này:** tắt một kênh gửi là **đổi vai của mọi kênh còn lại**. Trước
khi đặt một cờ kiểu `GUI_EMAIL='0'`, soi xem kênh sắp tắt có đang MỘT MÌNH thi hành luật nào không
— cùng họ với *"dời file thì phải dời cả thứ đang đo nó"*.

⛔ **VÁ TIẾP CÙNG NGÀY: PHÉP LỌC TRÊN CHỈ PHỦ 03 MỤC QUÉT THƯỜNG, TIN JAY LÂM ĐI LỌT** (01/08/2026).
Đo tối 01/08: **04 tin Jay Lâm lặp nguyên si bản tin sáng cùng ngày**. **Cơ chế gây vấp:** hai lớp
chống trùng đứng cạnh nhau mà mỗi lớp hụt một nửa, và chỗ hụt của chúng chồng lên nhau —
`loc_bo_tin_ca_sang` áp đúng `usNews`/`worldNews`/`events`, **không áp mục 5**; còn
`loc_trung_jaylam` thì so tiêu đề với tin của **CHÍNH bản đang dựng**, không biết gì về bản sáng.
Không lỗi, không cảnh báo — file .docx vẫn đủ mục.
📜 **Bản vá hôm đó (`loc_jaylam_ca_sang`) đã BỎ 01/08/2026 cùng mục 5** — mục 5 không còn thì
không còn gì để lọc ở đó. **Nhưng cơ chế gây vấp thì vẫn nguyên giá trị và đã lặp lại một lần
nữa**: hai lớp chống trùng đứng cạnh nhau, mỗi lớp hụt một mục, chỗ hụt chồng lên nhau. Vì thế
lớp lọc mới (`loc_bo_trung_jaylam`) được canh bằng ca [01]-[03] cho **cả ba** mục — bỏ sót một
mục thì file vẫn ra đời đủ, chỉ lặp tin ở đúng mục đó.

Ba luật rút ra vẫn áp cho lớp lọc mới:
- **Một đường đọc sổ duy nhất** (`_url_ca_sang(now)` cho sổ đã gửi; `doc_url_trung_jaylam()` cho
  sổ loại). Hai nơi tự đọc một sổ thì chắc chắn lệch, mà lệch âm thầm.
- ⚠️ **Fail-OPEN có tiếng:** đọc sổ hỏng ⇒ trả tập rỗng, giữ nguyên tin, **in cảnh báo**. Hướng
  lệch phải là LẶP một bản tin, không phải MẤT tin. Ca [08]-[11] của
  `tests/test-tin-jaylam-trong-docx.py` canh chiều này; bản hỏng đổi sang ném lỗi làm chúng đỏ.
  Ca đó phải bọc `try/except` — bản hỏng kiểu `raise` giết cả bộ test nên `--tu-kiem` thấy 0 dòng
  đỏ rồi kết luận "vẫn xanh", tức bản hỏng LỌT trong khi thực tế nó phá tan (vấp thật 02/08).
- ⚠️ **Ca test đọc sổ phải dựng SỔ GIẢ, đừng đọc sổ thật của repo** — sổ chỉ giữ `GIU_NGAY = 7`
  nên ca neo vào một ngày cụ thể sẽ tự tắt sau một tuần, tức bản hỏng lọt mà bảng vẫn xanh. Ca
  [60]/[61] của `test-so-da-gui.py` ghim `so_da_gui.SO`; `SoGia` trong `test-tin-jaylam-xu-ly.py`
  ghim `tin_jaylam.SO_LOAI`.

### 🟤 MALI RỜI FILE WORD, SANG BẢN SÁNG (chỉ thị Huy 05/08/2026)

> Nguyên văn: *"bỏ mục Mali trong file word gửi tele hàng ngày. Thêm mục Mali vào kết quả
> phần quét tập trận và thinktank."*

Tin Mali **vẫn quét, vẫn nạp `usNews`/`worldNews`, vẫn lên web y như cũ** — chỉ đổi **KÊNH
GỬI**: rời `.docx` của bản tin, sang **bản sáng 🎖️ Sự kiện & Tập trận**, đứng sau Think-tank.

| Mảnh | Việc |
|---|---|
| `make_docx.py::build_sections` | BỎ tuple `("Mỹ – Mali", mali)`; **GIỮ NGUYÊN phép lọc** + `mali_urls` trong `da_xep`; in một dòng ghi vết mỗi lần bỏ |
| `send-morning-email.js::diffMali` | Nhặt tin Mali mới từ `usNews`+`worldNews`, so với `HEAD~1` (không có thì lùi về `_addedDate`) |
| `send-morning-email.js` | `maliHtml()` · Mali nằm trong **GATE** mở email · `subjBits` · payload `mali` |
| `send_telegram.py::build_morning_messages` | Khối `🟤 Mỹ – Mali`, đọc `pl["mali"]` |
| `tests/test-mali-va-tap-tran.py` | **26 ca · `--tu-kiem` bắt 12/12 bản hỏng** |

⚠️ **BỎ MỤC KHÔNG PHẢI BỎ PHÉP LỌC.** Đây là chỗ dễ vá sai nhất: xoá luôn `mali`/`mali_urls`
thì tin Sahel hết bị tách ra và mục 1 "Nội bộ Mỹ" lại hứng chúng — đúng con lỗi Huy bắt
27/07/2026 (*"đang tin khcn-qs tự nhiên thấy lòi ra tin Mali"*), chỉ khác chỗ rơi. Ca [02] canh.
⚠️ **Mali PHẢI nằm trong gate mở email sáng.** Không có thì ngày nào chỉ có tin Mali là **mất
trắng**: `.docx` đã bỏ mục này rồi, không còn kênh nào khác mang nó đi. Ca [07] canh.
⚠️ **BA bảng khoá Mali phải khớp nhau** — `make_docx.py::MALI_KEYS` · `add_news.py::MALI_KEYS_ADD`
· bảng trong `send-morning-email.js`. JS không import được Python nên không tránh được việc
chép; lệch nhau thì tin Sahel vừa rơi khỏi `.docx` vừa không lên bản sáng, tức **mất hẳn mà
không lỗi nào**. Ca [09] đọc thẳng cả ba nơi, ca [10] chạy `laTinMali` THẬT bằng `jsc`.
⚠️ **Hệ quả về thời điểm, biết trước để đừng tưởng là bug:** tin Mali quét ở phiên TỐI sẽ lên
bản sáng HÔM SAU (bản sáng chỉ chạy buổi sáng). Đây là đánh đổi đã chấp nhận khi đổi kênh.

### 🔀 HAI WORKFLOW GHI CÙNG SỔ CÁCH 07 GIÂY — luật hợp nhất ở `ghi_so_push.py` (vá 30/07/2026)

**Sự cố thật sáng 30/07:** `notify-morning.yml` ghi `logs/da-gui-email.json` lúc 21:28:01Z,
`notify-email.yml` ghi lúc **21:28:08Z** — cùng một file, cách nhau **07 giây**. Khối lệnh cũ (chép y
nhau ở hai workflow) commit local rồi `git pull --rebase origin main`: rebase phải phát lại commit của
mình lên trên commit của workflow kia, hai bên sửa đúng cùng chỗ trong JSON nên **xung đột**
(`error: could not apply 7209062… (sang)`). Rebase hỏng để repo ở trạng thái rebase dở nên **cả 5 vòng
retry chết tiếp**, chỉ còn `::warning::khong push duoc so da gui`.
Hậu quả: bản tin sáng ĐÃ tới tay lúc 04:28 mà sổ trống ⇒ (a) canary ca `sang` **kêu oan** + nhắn
Telegram cho Huy; (b) hai phiên CI dự phòng (05:00 · 05:37) kết luận "mất bản tin" rồi chạy lại vòng
quét bổ sung tốn token. **Đây là hệ quả dây chuyền của việc gộp `event-scan` vào cùng session sáng
(28/07)** — trước đó hai bên cách nhau ~4 tiếng nên lỗi này ngủ yên.

**Cách vá — ĐỪNG REBASE, SỔ LÀ DỮ LIỆU APPEND-ONLY.** Hai lần gửi là hai DÒNG khác nhau trong
`lan_gui`, không phải hai phiên bản tranh nhau của một dòng; nên hợp nhất đúng là *lấy sổ mới nhất của
remote rồi ghi lại dòng của mình*. Luật nằm ở **ĐÚNG MỘT chỗ: `.github/scripts/ghi_so_push.py`**, cả
hai workflow gọi chung — đừng chép logic git trở lại file yml.

| Pha | Làm gì | Vì sao thứ tự này |
|---|---|---|
| **0** | chạy `so_da_gui.py --ghi` **một lần duy nhất**, giữ lại *dòng vừa thêm* | `so_da_gui` chọn URL bằng `make_docx.pick_items`, tức **diff `index.html` với `HEAD~1`**. Tính sau khi đã `reset` sang đỉnh remote là diff với lô của PHIÊN KHÁC ⇒ sổ ăn URL không phải của mình, mà **URL vào sổ nghĩa là bản tin sau BỎ tin đó** — mất tin, không phải trùng tin |
| **1** | mỗi vòng: `fetch` → `reset --mixed FETCH_HEAD` → `checkout FETCH_HEAD -- <sổ>` → append dòng của pha 0 → commit **chỉ file sổ** → `push HEAD:main`; bị từ chối thì ngủ rồi vòng lại | không bao giờ gọi `pull --rebase` ⇒ không bao giờ có xung đột để mà hỏng |

⚠️ **`--mixed` chứ KHÔNG `--hard`**: `--hard` kéo cả `index.html` của lô khác về, và commit của mình
khi đó không còn chỉ chứa file sổ.
⚠️ **Bước `checkout FETCH_HEAD -- <sổ>` là chỗ giữ dòng của workflow kia** — bỏ nó là ghi đè mất dòng
đó, đúng bệnh cũ nhưng theo đường khác. Append là **idempotent** (đã có thì không thêm), nên retry bao
nhiêu vòng cũng không nhân đôi dòng.
⚠️ **Pha 1 KHÔNG cắt bản ghi quá `GIU_NGAY`** — việc cắt là của `so_da_gui.ghi_lan_gui`. Cùng lắm sổ
giữ thêm vài dòng cũ tới lần ghi kế, mà giữ dư URL cũ chỉ khiến bản tin sau bỏ qua tin cũ: hướng lệch
an toàn. Đừng thêm luật cắt thứ hai.
⚠️ **Hết vòng mà chưa push được thì trả mã ≠ 0 + in `::error::`**, không trả 0 cho êm — sổ trống chính
là thứ làm canary kêu oan và làm phiên dự phòng quét lại. Bước vẫn giữ `continue-on-error: true` nên
job không đỏ, nhưng phải để lại dấu vết lần được.

**Bộ test canh: `tests/test-ghi-so-push.py`** — 10 ca, dựng repo git THẬT (remote bare + 2 clone = hai
workflow). Nghiệm thu 30/07: 10/10 ca đạt · `--tu-kiem` bắt **6/6** bản hỏng, trong đó bản hỏng "dùng
lại `pull --rebase`" (chính bản CŨ) làm **6/10 ca đỏ**. Nghiệm thu thêm bằng đường THẬT (`so_da_gui.py`
thật, clone của repo thật, remote bare local): sổ giữ đủ hai dòng, commit chỉ đụng file sổ.

#### Cổng phủ CẢ LỚP LỖI: `.github/scripts/kiem_luat_push.py` (dựng 30/07/2026)
Bản vá trên chỉ bịt **đúng hai** workflow ghi sổ. Lớp lỗi rộng hơn thế: workflow nào hội đủ **03 điều
kiện** — (i) chạy theo **LỊCH**, tức không ai ngồi canh; (ii) commit một file **NHIỀU nguồn cùng ghi**;
(iii) hợp nhất bằng **`pull --rebase`** — đều tái diễn được đúng sự cố ấy. Cổng quét mọi
`.github/workflows/*.yml` và chặn đúng tổ hợp đó, để phiên sau không chép khối lệnh cũ vào workflow mới.

Phải đủ **cả ba** điều kiện, vì đo thật (`git log --format='%an' -- <file>`, từ 01/07/2026) cho thấy
chúng không cùng mức rủi ro:

| File | Số nguồn ghi | |
|---|---|---|
| `index.html` | **05** | DÙNG CHUNG |
| `logs/state.json` | **03** | DÙNG CHUNG |
| `logs/da-gui-email.json` | **02** | DÙNG CHUNG |
| `docs/ung-vien-ci.json` · `baomoi-saved.json` · `docs/probe-ci.json` | 01 | riêng — rebase không có gì để xung đột |

Bỏ bớt điều kiện nào cũng thành **cổng chết** (mục 17 CLAUDE.md toàn cục — cổng luôn phải mở cờ mới qua
được thì bị mở quen tay, rồi mọi cổng còn lại mất giá trị theo): bỏ (i) thì chạy tay cũng bị chặn dù có
người canh; bỏ (ii) thì `harvest-ci` · `sync-baomoi` · `sync-preferences` · `probe-sources` đỏ oan cả
loạt; bỏ (iii) thì mọi workflow commit `index.html` đều đỏ, kể cả cái hợp nhất đúng cách. Sau khi
`import-news-from-drive.yml` bỏ cron, **không workflow nào vi phạm** — cổng xanh ở luồng bình thường.

⚠️ **Fail-CLOSED**: yml hỏng cú pháp → mã **2**; thư mục không có workflow nào → mã **2**. Không bao giờ
trả 0 — *"không thấy vi phạm"* và *"không nhìn được"* là hai chuyện khác nhau, lẫn chúng vào nhau đúng
là kiểu chết câm cổng này sinh ra để chặn.
⚠️ **Bẫy YAML 1.1**: khoá `on:` không nháy bị `yaml.safe_load` parse thành **boolean `True`**, không phải
chuỗi `"on"`. Đọc thiếu nhánh đó là cổng coi mọi workflow đều không có lịch ⇒ **câm hoàn toàn**. Cổng đọc
cả hai dạng, và có ca test riêng cho dạng `"on":` có nháy.
⚠️ **Giới hạn đã biết**: cổng chỉ đọc lệnh git viết thẳng trong `run:` của yml. Lệnh git do phiên
`claude -p` tự gõ bên trong `claude-web-scan.yml` nằm ngoài tầm — chỗ đó do playbook quét canh.

**Bộ test canh: `tests/test-cong-luat-push.py`** — 11 ca (04 PHẢI CHẶN · 04 đối chứng chống chặn oan ·
02 fail-closed · 01 soi thư mục workflow THẬT của repo). Nghiệm thu 30/07: 11/11 đạt · `--tu-kiem` bắt
**8/8** bản hỏng. Gọi thẳng `main()` trong tiến trình (`redirect_stdout`) chứ **không** `subprocess` —
subprocess nạp lại bản thật trên đĩa nên `--tu-kiem` không tráo được bản hỏng, ca sẽ xanh trên cả bản
đúng lẫn bản hỏng. `--tu-kiem` còn tự bắt lỗi của chính nó: bản hỏng làm đỏ **toàn bộ** ca là phép thay
phá hỏng nền chứ không gỡ đúng một lớp vá, báo TRƯỢT.

Ba cái bẫy đã vấp thật, đừng lặp lại:
- **Ghi sổ phải là bước CUỐI**, sau CẢ email lẫn Telegram. Ghi sớm hơn thì Telegram đọc sổ thấy chính lô
  vừa gửi và lọc sạch → **Telegram rỗng**.
- **Chỉ ghi sổ khi `github.event_name == 'push'`.** Hai lần chạy tay `workflow_dispatch` lúc 14:24/14:36
  ngày 27/07 đã ghi 11 tin của cả ngày vào sổ, suýt làm bản tối bỏ sạch chúng — trong khi chúng được quét
  rải rác **09:13–14:17**, không phải phiên sáng. Chạy tay là để TEST, không được để dấu vết lên bản thật.
- **`notify-morning.yml` ghi sổ với `--chi events`**, tuyệt đối không ghi `usNews`/`worldNews`: email đó
  CHỈ gửi sự kiện, ghi thừa là **xoá sổ tin thường trước khi chúng kịp lên bản tin tối** — mất tin, chứ
  không phải trùng tin.
  ⚠️ **Đo 30/07: loại `events` trong sổ hiện KHÔNG có ai đọc** — `loc_chua_gui` chỉ áp `usNews`/`worldNews`,
  còn sự kiện/tập trận đi bằng payload riêng `/tmp/morning-telegram.json`. Tức đây là ghi một chiều, vô
  hại. **Nhưng chốt `--chi events` vẫn phải giữ nguyên**: giá trị của nó là chặn đường ghi THỪA hai loại
  kia, không phải để có ai đọc `events`. Ca 3 của `tests/test-so-da-gui.py` canh đúng chỗ này, và bản
  hỏng *"`--chi` bị bỏ qua, luôn ghi cả 3 loại"* làm ca đó không đạt — đừng gỡ vì tưởng nó vô dụng.
- `send_telegram.py` dựng `.docx` **TRƯỚC** khi xét `total == 0`, và `total == 0` vẫn gửi file kèm — nếu
  không, hôm nào mọi tin đều đã báo là Huy mất luôn file tổng hợp.

### ⛔ CHỈ PHIÊN TỰ NẠP MỚI ĐƯỢC KÍCH NOTIFY — cờ tường minh, không dò `git log` (vá 31/07/2026)

**Sự cố thật:** tối 31/07 Huy nhận **HAI** file `.docx` y hệt nhau — 21:24 kèm caption *"9 tin
mới"*, 21:26 kèm *"không có tin mới so với bản trước"*. Cả hai run `notify-email.yml` đều là
`workflow_dispatch` (30638444028 · 30638555318), tức có **hai** lời gọi `gh workflow run`.

| Giờ UTC | Việc |
|---|---|
| 14:00:19 | run `30636762079` (mốc 20:47) khởi động, giành khoá, **quét thật** |
| 14:11:17 | run `30637541239` (lớp vét) khởi động → chụp `base.sha` → `claim` trả **exit 10** → SKIP, không quét gì |
| 14:23:49 | phiên chính commit `4fffa97 Cap nhat ban tin 31/07` → kích → **bản 1** |
| 14:25:33 | phiên VÉT ghi commit log rồi tới bước kích, `git pull --rebase` **kéo `4fffa97` về** |
| 14:25:50 | `git log <base>..HEAD | grep '^Cap nhat ban tin'` khớp commit của người ta → kích → **bản 2** |

**Cơ chế gây vấp:** chú thích trong yml khai ý định là *"commit mới TRONG JOB NÀY"*, nhưng phép
đo chạy **sau** `git pull` nên khoảng `base..HEAD` nuốt cả commit của phiên khác vừa push xen
vào. Job vét khởi động trước phiên chính commit 12 phút, nên cửa sổ đó chắc chắn nuốt.
⛔ **Đừng "sửa cho gọn" bằng cách đo git sớm hơn** — phiên SKIP cũng phải `pull --rebase` để
push nổi commit log của chính nó, nên commit của phiên kia đã nằm trong cây local TRƯỚC bước
kích. Phép đo thuần git không phân biệt được ca này.

| Mảnh | Việc |
|---|---|
| `scripts/state.py::ghi_co_da_nap` | `done <pipeline>` ghi cờ `diemtin-da-nap-<pipeline>` vào **thư mục tạm** (`DIEMTIN_CO_DIR` là seam cho test) — chỉ sống trong đúng một job, đó chính là thứ `git log` không có |
| `.github/scripts/quyet_dinh_kich.py` | đọc cờ, in `ban_tin=…` / `su_kien=…`; **fail-CLOSED có tiếng** (không đọc được cờ → mã 2 → step ĐỎ) |
| `claude-web-scan.yml` bước kích | `. /tmp/quyet-dinh-kich.env` rồi xét `$ban_tin` / `$su_kien` — KHÔNG còn `new_msgs` |
| `tests/test-cong-kich-notify.py` | **10 ca · `--tu-kiem` bắt 3/3 bản hỏng**, đã nạp `khoe.py` |

⚠️ **Ý ĐỊNH KHAI BẰNG LỜI** — cùng bài học với `tu_dong=1` · `TELEGRAM_BAT_BUOC` ·
`DIEMTIN_PHIEN_TEST`: chỉ phiên nào **tự tay** gọi `state.py done` mới có cờ. Phiên SKIP không
được gọi `done` (luật routine) nên vĩnh viễn không có cờ.
⚠️ **`skip`/`fail` KHÔNG ghi cờ** — ca 02/03 của bộ test canh đúng chỗ này, và bản hỏng *"ghi cờ
cho MỌI status"* làm chúng đỏ.
⚠️ **Phiên test VẪN ghi cờ** — cố ý: nhánh `MODE=test` tự kích với `subject_tag` riêng và không
truyền `tu_dong`, nên nó không để dấu lên sổ đã gửi; chặn cờ ở đó là làm nhánh test hết nghiệm
thu được.
⚠️ **Hướng lệch của bản vá là MẤT một lần gửi, không phải gửi thừa** — quên khai cờ thì canary
22:45 bắt được (sổ trống); còn gửi thừa thì không cơ chế nào kêu, chỉ Huy tự thấy. Vì vậy step
`Ghi lại HEAD trước khi quét` (`steps.base`) nay **không còn ai đọc**, giữ lại chỉ để ghi vết
chẩn đoán — đừng dựng lại nhánh quyết định dựa vào nó.

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
⚠️ **ĐÍNH CHÍNH 02/08/2026 — câu cũ "index.html không đọc `location.hash`" ĐÃ SAI, đừng đọc theo
trí nhớ.** Web nay CÓ hash routing đầy đủ: `HASH_TABS` + `HASH_SEG` + `hashApply()`/`hashStr()` trong
`index.html`. Dạng hash: `#<tab>` · `#<tab>/<mục con>` (vd `#analysis/weekly`) · và từ 02/08 thêm
**tầng 3 cho báo cáo tuần**: `#analysis/weekly/<us|cn|ru>` mở đúng mục rồi **cuộn thẳng tới khối nước
đó** (`renderWeekly` gắn `id="wk-<key>"`, `cuonWk()` cuộn).
- **Neo lạ thì BỎ QUA chứ không chặn cả hash** — `#analysis/weekly/zzz` vẫn mở đúng mục, chỉ không
  cuộn. Tới đúng mục vẫn hơn rơi về trang chủ.
- **KHÔNG dùng `behavior:'smooth'`**: đo 02/08 — khung xem có chiều cao 0 thì smooth **không nhúc
  nhích và cũng không ném lỗi** (nên `try/catch` không đỡ được), còn `scrollIntoView()` trần thì cuộn
  đúng vị trí. Link mở từ Telegram cần thấy ngay, không cần hiệu ứng.
- Nghiệm thu 02/08 trên trình duyệt thật: `#analysis/weekly/ru` → `scrollY` 20766 · `/us` → 2374 ·
  `#analysis/weekly` (không neo) → mở đúng mục, `wkGoto=null`.
