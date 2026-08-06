# Luật CHỦ ĐỀ và nạp tin — chủ đề 2, Báo Mới, guardrail lô tin, phiên test

<!-- Xẻ từ `CLAUDE.md` ngày 06/08/2026 để cắt chi phí token: toàn bộ file gốc được nạp lại
ở MỌI lượt của MỌI phiên đụng repo này (đo thật: ~99.000 token/lượt), trong khi phần lớn nội dung
là NHẬT KÝ VÁ LỖI chỉ cần đọc khi đụng đúng mảng đó.
⚠️ Nội dung dưới đây giữ NGUYÊN VĂN — cả luật lẫn "cơ chế gây vấp". Đừng rút gọn: phần kể lại
cơ chế chính là thứ ngăn phiên sau dựng lại đúng cái lỗi cũ.
⚠️ CLAUDE.md còn dòng trỏ sang từng mục. Đổi tên mục ở đây thì sửa dòng trỏ bên đó. -->

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
