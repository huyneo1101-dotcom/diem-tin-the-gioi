# Tin Jay Lâm gửi — đường nhận và vai BỘ LỌC

<!-- Xẻ từ `CLAUDE.md` ngày 06/08/2026 để cắt chi phí token: toàn bộ file gốc được nạp lại
ở MỌI lượt của MỌI phiên đụng repo này (đo thật: ~99.000 token/lượt), trong khi phần lớn nội dung
là NHẬT KÝ VÁ LỖI chỉ cần đọc khi đụng đúng mảng đó.
⚠️ Nội dung dưới đây giữ NGUYÊN VĂN — cả luật lẫn "cơ chế gây vấp". Đừng rút gọn: phần kể lại
cơ chế chính là thứ ngăn phiên sau dựng lại đúng cái lỗi cũ.
⚠️ CLAUDE.md còn dòng trỏ sang từng mục. Đổi tên mục ở đây thì sửa dòng trỏ bên đó. -->

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
