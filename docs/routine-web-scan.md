# Routine WEB-SCAN — bản tin 5 chủ đề (NGUỒN SỰ THẬT DUY NHẤT)

> **File này là nguồn sự thật duy nhất về quy trình quét bản tin.**

⛔ **PHIÊN TỐI BỎ HẲN 18/09/2026 — chữ nào dưới đây nói "phiên tối" là LỊCH SỬ.** Nay **01 phiên/ngày: SÁNG SỚM**. Chỉ thị Huy: *"chỉ cần gửi tin 4h sáng thôi, không phải quét và gửi buổi tối nữa đâu"*. Lịch sử và 04 cơ chế vấp còn áp: [`nhat-ky-vap-phien-toi.md`](nhat-ky-vap-phien-toi.md).
⛔ **ĐỪNG CẮM LẠI MỐC TỐI KHI THẤY BẢN SÁNG MỎNG.** Bản mỏng là việc của SÀN và KHUNG NGÀY (`scripts/soi_muc_cam.py`), không phải việc của lịch. Cổng canh: `kiem_lich.py` phép đo D chặn mọi cron của đường quét rơi vào khung 19:00-23:59 VN.

> Dời từ `~/.claude/scheduled-tasks/web-scan-diem-tin/SKILL.md` vào repo ngày 27/07/2026 — vùng `~/.claude/` là sensitive, mọi Edit vào đó đều bị hỏi quyền bất kể allowlist, trong khi file này rất hay phải vá bài học mới. Repo thì Edit/Write đã allow toàn phần + có git history.
> **Ai đọc file này:** mốc local `com.huy.routine-diemtin-sang` (phiên SÁNG SỚM **04:30 · 04:45**) và mốc local `com.huy.routine-diemtin-toi` (phiên TỐI 21:15) — cả hai là LaunchAgent gọi `claude -p --model sonnet`, KHÔNG còn là scheduled task của app (đổi 06/08, đo lại 18/08/2026) — SKILL.md của 2 task đó giờ chỉ là stub trỏ về đây. **Sửa quy trình thì sửa file này**, đừng sửa stub.

Quét tin và xuất bản bản tin cho web "Điểm Tin Thế Giới" (https://huyneo1101-dotcom.github.io/diem-tin-the-gioi).
Repo: /Users/Huy/Claude/diem-tin-the-gioi (git remote SSH, push thẳng nhánh `main`).

Bản tin **01 phiên/ngày** theo playbook 5 chủ đề: SÁNG SỚM (ô khoá `sang`), gửi email + file Word. (Trước 18/09/2026 còn phiên TỐI ô khoá `toi` — đã bỏ, xem khối đầu file.) **Từ 28/07/2026, phiên SÁNG SỚM sau khi xong bản tin 5 chủ đề còn làm TIẾP pipeline `event-scan` (sự kiện/tập trận/think-tank, trước đây là phiên riêng) trong CÙNG session — xem Bước 4.**

⚠️ **PHÂN VAI: quy trình dưới đây là CHUNG cho cả hai phiên; mày là phiên nào thì xem stub task đã giao mày việc.** Task `web-scan-diem-tin` lo phiên SÁNG SỚM; task `web-scan-diem-tin-toi` lo phiên TỐI (tách 27/07/2026 vì phiên tối có hạn chót email cứng, cần fire sớm hơn để có biên; một task chỉ nhận một biểu thức cron nên phải tách). Cả hai task **KHÔNG chép lại quy trình** mà cùng Read file này — để hai phiên không bao giờ lệch nhau. Phiên TỐI có thêm mục "PHIÊN TỐI — BỐI CẢNH RIÊNG" ở cuối file.

## ⚡ BƯỚC 0 — CLAIM NGAY, PHIÊN NHƯỜNG PHẢI RẺ (thêm 05/08/2026, chỉ thị Huy tiết kiệm limit)

**Đọc xong khối này thì CHẠY 3 LỆNH CỦA BƯỚC 1 LUÔN** (pull → claim → ghi_log_push), rồi mới đọc
tiếp phần còn lại nếu được quét. Vì sao: đo 7 ngày cuối 07/2026, mỗi phiên local "nhường CI" vẫn
đốt **~1,9 triệu token quy đổi / 26-27 lượt tool** — phần lớn lượt là thăm dò quanh việc claim
(xem log cũ, show trạng thái, đọc thêm tài liệu) trong khi kết cục đã định là SKIP. Ba lớp CI +
local mỗi ngày nhân số phiên nhường lên, nên phiên nhường phải rẻ như một cú gõ cửa.

- **Claim trả SKIP (exit 12 — SAI GIỜ)** → ghi 1 dòng SKIP vào log, commit + push, **KẾT THÚC NGAY**. Cổng khung giờ (`KHUNG_GIO` trong `scripts/state.py`, cắm 31/08/2026): ca `sang` chỉ nhận 03:00-09:00, ca `toi` chỉ nhận 19:30-23:30 giờ VN. ⛔ **KHÔNG lách bằng `--bo-cong-gio`.** Sự cố gốc: cron GitHub trễ 4 tiếng, mốc TỐI nổ lúc 00:46 giờ VN, tự nhận là phiên sáng, gửi bản tin lúc 01:25 sáng rồi chiếm ô `sang` — bản tin TỐI mất hẳn 30/08 và 31/08. Bộ canh: `tests/test-cong-khung-gio.py`.
- **Claim trả SKIP (exit 10 hoặc 11)** → làm đúng 02 việc rồi **KẾT THÚC NGAY**: (i) ghi 1 dòng
  SKIP vào `logs/scan-<ngày VN>.log` bằng tool Write/Edit; (ii) chạy `ghi_log_push.py` cho dòng
  đó. Trả lời đúng một câu. **Toàn phiên SKIP không quá ~7 lượt tool.**
  ⛔ **Ca SÁNG: trước khi kết thúc, chạy thêm đúng 01 lệnh `state.py claim event-scan`** — exit
  10/11/12 thì kết thúc như trên; exit 0 thì nhảy sang Bước 4 chạy bù event-scan. Vá 25/09/2026:
  phiên gửi bản tin tự SKIP event-scan, mọi mốc sau exit 10 rồi kết thúc nên không lớp nào chạy bù.
- ⛔ **CẤM ở lối SKIP:** `state.py show` · đọc log ngày cũ · `gh run list` · đọc `LICH.md` /
  `CLAUDE.md` repo / skill `quet-tin` · mọi lệnh thăm dò "cho chắc". Khoá heartbeat + mốc dự
  phòng đã lo phần theo dõi (dòng KẾT THÚC ở Bước 1 vẫn nguyên hiệu lực).
- **Riêng exit 10 ở mốc TỐI** vẫn giữ phép kiểm sổ đã gửi (mục "PHIÊN TỐI" điều 3) — đó là 1-2
  lệnh, không phải giấy phép đi thăm dò rộng.
- Claim trả **RUN (exit 0)** → đọc tiếp từ Bước 1b trở đi và quét như thường — mức chi cho phiên
  quét thật không đổi.

| Phiên | CI chính | local | CI dự phòng | local lưới cuối | Ai chạy phần local |
|---|---|---|---|---|---|
| SÁNG SỚM | **03:47** VN | **04:05** | 04:47 | **04:35** | LaunchAgent `com.huy.routine-diemtin-sang` |

⛔ Hàng **TỐI** (20:47 · 21:15 · 21:47) gỡ 18/09/2026 cùng phiên tối.

📅 **BẢNG LỊCH ĐẦY ĐỦ + NGUỒN SỰ THẬT: [`docs/LICH.md`](LICH.md)** — sinh từ chính dòng `cron:`
của workflow bằng `python3 scripts/kiem_lich.py --sinh`. Số giờ ở bảng trên là bản rút gọn cho
tiện đọc; **lệch nhau thì `LICH.md` thắng**. Cổng `kiem_lich.py --kiem` canh việc này (dựng
30/07/2026 sau khi bắt được **47 chỗ** trong tài liệu còn ghi lịch CI cũ 21:00/22:00/04:00/05:00,
tức lịch đã dời sớm 13 phút mà không ai sửa những chỗ chép lại).

Cách làm ở MỌI mốc là như nhau: cứ `claim` như thường — CI đã xong/đang chạy thì SKIP êm, CI không quét (trễ/chết/hết quota) thì mày quét đủ 5 chủ đề rồi commit `Cap nhat ban tin ...` (email + .docx do Action `notify-email.yml` tự gửi khi thấy push `index.html` với tiền tố commit đó — local push cũng kích như CI, không phải làm gì thêm). Phiên sáng 10:15 kiểu cũ vẫn bỏ.
⚠️ Local chỉ chạy khi app Claude đang mở và máy đã thức — mốc 04:30 phụ thuộc lịch wake của máy (`pmset repeat wakeorpoweron`); máy ngủ thì mốc này im, đó là lý do vẫn giữ CI 03:47/04:47 làm mốc chính.

PHẠM VI (chỉ thị Huy 2026-07-23): mỗi phiên CHỈ quét 5 chủ đề, khung hôm nay + hôm qua (CNQS lùi tới 3 ngày), sàn 05 tin mỗi mục. ⛔ "Nới 48h" là HÔM NAY + HÔM QUA, không phải lùi 2 ngày lịch. **Nội dung đầy đủ chỉ viết ở SKILL.md mục "PHẠM VI MỚI"** (đọc ở Bước 2 khi quét; không chép lại ở đây để hai bản khỏi lệch nhau). Ngoài 5 chủ đề thì bỏ, kể cả Báo Mới chỉ giữ bài hợp 5 chủ đề.

KHÔNG dùng `cd` (gây prompt xin quyền, routine chạy lúc khuya/sáng sớm khi Huy không có mặt). Mọi lệnh dùng ĐƯỜNG DẪN TUYỆT ĐỐI: script là `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/<x>.py` (script tự tìm repo root từ `__file__`, không cần đứng trong repo), git là `git -C /Users/Huy/Claude/diem-tin-the-gioi ...`. Ghi log dùng tool Edit/Write vào `/Users/Huy/Claude/diem-tin-the-gioi/logs/scan-<ngày VN>.log` thay vì `cat >>`.
⚠️ **MỌI LỆNH BASH PHẢI PHẲNG — KHÔNG WRAPPER, KHÔNG BIẾN, KHÔNG VÒNG LẶP** (sự cố 25–26/07/2026: routine treo chờ bấm nút 3 lần vì 3 kiểu lệnh "fancy"). Harness soi CÚ PHÁP lệnh: hễ chứa hàm/brace (`cd() { ... };` — flag "expansion obfuscation"), biến shell hay `$(...)` (`$NGAY`, `$f` — flag "simple_expansion"), hay `for ... do ... done`/heredoc, là nó BỎ QUA ALLOWLIST và bật prompt xin quyền — DÙ lệnh bên trong hợp lệ. Quy tắc áp cho MỌI lệnh trong phiên, kể cả lệnh chẩn đoán tuỳ hứng (ps, grep transcript...):
- Chỉ dùng lệnh PHẲNG: một lệnh đơn, pipe (`|`), hoặc chuỗi `&&` của lệnh đơn — đối số là GIÁ TRỊ THẬT, gõ đầy đủ.
- Cần ngày/giờ: chạy riêng `TZ='Asia/Ho_Chi_Minh' date +%F` / `date -u +%H:%MZ` rồi điền literal vào lệnh sau.
- Cần lặp nhiều file: viết N lệnh rời (ví dụ 2 dòng `grep -c 'x' <path đầy đủ>` thay vì `for f in ...; do grep $f; done` — chính vụ 26/07: dạng rời khớp `Bash(grep *)` chạy thẳng, dạng for bị treo).
- Lặp phức tạp hơn: gói vào `python3 -c '...'` (đã allowlist) thay vì bash script.
- "Không dùng cd" = ĐỪNG GỌI `cd`, KHÔNG phải vô hiệu hoá nó bằng hàm chắn.
- 🔒 Từ 27/07/2026 quy tắc này được **hook cưỡng bức**: `/Users/Huy/Claude/hooks/block-lenh-khong-phang.py` (dời khỏi `~/.claude/hooks/` ngày 29/07/2026 vì vùng đó bị classifier chặn sửa) chặn thẳng lệnh có hàm/brace/`for`/heredoc/`$VAR`/`$(...)`/backtick trong phiên scheduled-task. Bị chặn thì **viết lại lệnh cho phẳng, KHÔNG xin quyền cho lệnh cũ**. Nội dung trong nháy ĐƠN được bỏ qua nên `python3 -c '...'` và `awk '{print $1}'` vẫn chạy bình thường.
Lệnh sạch dạng `git -C /Users/Huy/Claude/diem-tin-the-gioi add|commit|push ...` tự khớp allowlist, chạy không hỏi.
🔁 **LỖI MẠNG / LỖI SERVER — TỰ RETRY, KHÔNG BỎ CUỘC SỚM** (chỉ thị Huy 26/07/2026): WebSearch/WebFetch lỗi (timeout, 5xx, connection) → thử lại tới 3 lần, đổi nguồn/từ khoá nếu vẫn hỏng; `git push`/`git pull` lỗi mạng → chạy `sleep 30` rồi thử lại, tối đa 3 vòng; agent con chết giữa chừng → giao lại đúng 1 lần. Sau 3 lần vẫn hỏng: `state.py fail web-scan "mat mang/loi server: <chi tiet>"` + ghi log + cố push log (cũng retry 3 lần) — mốc dự phòng sau sẽ tự quét lại, không cần chờ mạng vô hạn.

## Bước 1 — Đồng bộ + giành khoá
```
python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/don_ton_du.py
git -C /Users/Huy/Claude/diem-tin-the-gioi pull --rebase origin main
python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/state.py claim web-scan
python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/ghi_log_push.py --file logs/scan-<ngày VN>.log --nhan "log: claim web-scan (local)"
```

⛔ **DÒNG ĐẦU LÀ BẮT BUỘC, LUÔN CHẠY TRƯỚC `pull --rebase`** (thêm 07/08/2026, chỉ thị Huy:
*"lần sau phải tự động đẩy việc dở, không được để ảnh hưởng đến việc quét tin"*). Sự cố thật
sáng 07/08: một phiên khác dựng `scripts/do_can_doi_khu_vuc.py` + sửa `CLAUDE.md` lúc 21:37 tối
trước rồi kết phiên không commit; mốc quét local 04:30 chết ngay dòng đầu tiên
(`cannot pull with rebase: You have unstaged changes`) — đúng lúc GitHub cũng không cấp máy chạy
CI đêm đó (mọi run 22:56→04:45 chết sau 15 phút, 0 bước). Cả hai lớp cùng chết, bản tin sáng
muộn một tiếng.
`don_ton_du.py` tự phân loại tồn dư theo TUỔI FILE (mtime, ngưỡng 90 phút — đủ rộng để không bao
giờ giật việc khỏi tay phiên đang gõ thật): file **NGUỘI** thuộc `scripts/`·`tests/`·`docs/`·
`.claude/`·`.github/` hoặc đuôi `.py/.md/.yml/.sql` → tự commit + push (message KHÔNG khớp tiền
tố `Cap nhat ban tin`/`Cap nhat su kien` nên không kích nhầm cổng gửi email); file **sinh tự
động** (`logs/`, `baomoi-*.json`, `docs/ung-vien-ci.json`, `preferences.json`) → bỏ thay đổi cục
bộ (`git checkout --`, lượt `pull --rebase` kế tiếp tự lấy đúng bản remote mới nhất); file
**CẦN NGƯỜI** (`index.html`, `sw.js`, `manifest.json`, `data/analyses.json`) hoặc file **NÓNG**
(< 90 phút tuổi — phiên khác đang gõ thật) → KHÔNG đụng, in cảnh báo, mã thoát khác 0.
⚠️ **Script không chặn phiên dù mã thoát ≠ 0** — cứ đọc tiếp dòng 2 như thường. Còn `index.html`
tồn dư (mã 3) hoặc file NÓNG (mã 4) thì `pull --rebase` ở dòng 2 vẫn có thể bị chặn — xử tiếp
theo đúng bảng "DÒNG 1 BÁO lỗi" ngay dưới, KHÔNG bỏ qua bước đó.
Bộ test canh: `tests/test-don-ton-du.py` (11 ca · `--tu-kiem` bắt 4/4 bản hỏng).
⚠️ **Vá này KHÔNG đảm bảo bản tin sáng luôn tới trước một giờ cố định** (Huy hỏi 07/08/2026 sau
khi vá). Nó chỉ đóng đúng MỘT nguyên nhân — tồn dư chặn `pull --rebase`. Đêm 06→07/08 GitHub
không cấp máy chạy CI suốt **22:56→05:15 (~6 tiếng)**, mọi run chết sau 15 phút không chạy nổi
bước nào — đó mới là phần chiếm phần lớn độ trễ hôm đó, và nó nằm ngoài tầm với: GitHub tự cấp
máy lại lúc 05:15 chứ không phải nhờ bản vá này. Lưới local vẫn còn hai điều kiện chưa ai bịt
được: máy Mac phải đang THỨC (`pmset repeat wakeorpoweron`) và app Claude phải đang MỞ.

⛔ **COMMIT CHỈ-CÓ-LOG PHẢI ĐI QUA `ghi_log_push.py`, KHÔNG `git add logs/` + `commit` + `push`**
(vá 02/08/2026 — sự cố thật sáng đó). Sáng 02/08 có **04 phiên** cùng append vào
`logs/scan-2026-08-02.log` (CI 03:47 · local 04:30 · lớp vét 04:47 · một phiên gọi lại). Mỗi
phiên push bị từ chối thì `pull --rebase`, mà hai dòng thêm vào cùng vị trí là **xung đột văn
bản** ⇒ rebase hỏng ⇒ repo nằm lại ở trạng thái rebase dở ⇒ phiên local 05:30 vào thì chết ngay
lệnh ĐẦU TIÊN: `error: Pulling is not possible because you have unmerged files`. Repo kẹt như
thế thì **mọi phiên sau đều chết ở Bước 1**, kể cả phiên tối có hạn chót gửi 22:00, và tiếng
kêu duy nhất là một dòng `fatal` không ai đọc.
Script dùng CHUNG hàm hợp nhất với sổ đã gửi (`ghi_so_push.day_len_remote`): lấy bản mới nhất
của remote rồi ghép dòng của mình vào, **không bao giờ rebase** nên không có xung đột để mà
hỏng. Cứ ghi log bằng tool Edit/Write như thường, rồi gọi script — nó tự chụp dòng của phiên
mình trước khi đụng git.
⚠️ **CHỈ áp cho commit chỉ chứa log.** Commit bản tin (`index.html` + `logs/`) ở Bước 3 vẫn đi
đường cũ — `index.html` KHÔNG phải append-only, hai lô tin cùng chèn vào đầu mảng là xung đột
thật, git không hợp nhất hộ được.
Bộ test canh: `tests/test-ghi-log-push.py` (07 ca · `--tu-kiem` bắt 3/3 bản hỏng).
⛔ **GỌI `ghi_log_push.py` THÌ ĐỪNG PIPE VÀO `tail` — MÃ THOÁT BỊ NUỐT, SCRIPT CHẾT MÀ NHÌN NHƯ
XONG** (đúc 03/08/2026, đo thật ở phiên local 05:18). Mã thoát của một pipeline là mã thoát của
lệnh CUỐI, tức của `tail`, và `tail` thì gần như luôn trả 0. Hôm đó mạng chập chờn:
`ghi_log_push.py` chết ở `git fetch -q origin main rc=128: Connection to github.com closed by
remote host`, traceback in ra đầy đủ — nhưng harness báo **"completed (exit code 0)"**, đọc vào
là tưởng đã push xong. Dòng log chỉ lên được remote nhờ **ăn ké** commit của một phiên chạy bù
đang chạy song song cuốn theo; không có phiên đó thì dòng log mất trắng, không một tiếng kêu.
- **Gọi trần, không pipe.** Cần cắt bớt output thì đọc file output, đừng cắt bằng `tail`.
- **Xác minh bằng REMOTE, không tin mã thoát**: `git -C <repo> fetch origin main` rồi
  `git -C <repo> show FETCH_HEAD:logs/scan-<ngày VN>.log | grep -c '<mốc giờ của dòng mình>'`
  phải ra `1`. Đọc `git show origin/main:…` là đọc ref LOCAL — ref đó có thể cũ, đúng bẫy
  `rev-list` quên `fetch` đã ghi ở Bước 1.
- **Hướng lệch:** mất một dòng log không làm hỏng bản tin, nhưng log là thứ DUY NHẤT để chẩn
  đoán khi phiên sau hỏng — mất nó là mất đúng thứ cần lúc đi truy bug.
⛔ **DÒNG 1 BÁO `cannot pull with rebase: You have unstaged changes` → ĐỪNG DỪNG PHIÊN, ĐI TIẾP.**
Vá 29/07/2026 sau khi lỗi này chặn thật lần thứ hai (lần đầu sáng 27/07; lần 29/07 do một phiên khác
dựng `tests/` + sửa `CLAUDE.md` rồi ngừng giữa chừng không commit).

**Cơ chế — đo bằng repo thử, không phải suy đoán:** `pull --rebase` phải TUA LẠI cây thư mục (gỡ commit
local ra, đặt commit remote vào, phát lại commit local lên trên), nên nó ghi đè file trong thư mục làm
việc nhiều lượt. Thay đổi chưa commit thì không nằm trong commit nào cũng không nằm trong index — ghi đè
là mất trắng, không lôi lại được. Vì vậy git **từ chối ngay từ đầu, TRƯỚC cả khi xét có gì để rebase hay
không**. Kết quả đo:

| Trạng thái repo | `pull --rebase` |
|---|---|
| Chỉ có file **untracked** (thư mục lạ, file mới chưa `git add`) | **rc 0** — chạy bình thường, untracked KHÔNG chặn |
| Có file **tracked bị sửa** | rc 128 |
| Tracked bị sửa **+ remote 0 commit mới** | **vẫn rc 128** — chặn dù pull vốn là lệnh rỗng |

⇒ Bị chặn KHÔNG có nghĩa là có xung đột. Phải phân biệt bằng 2 lệnh phẳng:
```
git -C /Users/Huy/Claude/diem-tin-the-gioi fetch origin main
git -C /Users/Huy/Claude/diem-tin-the-gioi rev-list --count HEAD..origin/main
```
⚠️ **PHẢI fetch TRƯỚC rồi mới `rev-list`** — `rev-list` đọc ref `origin/main` trong repo, không đi
mạng. Chạy `rev-list` mà quên `fetch` thì nó đọc ref CŨ và **luôn ra 0**, tức routine luôn kết luận
"không có gì mới" rồi quét ra bản tin cũ — hỏng câm, số in ra vẫn đẹp. Đã đo trên `git 2.39.5` của
máy Huy: trước fetch ra `0`, sau fetch ra `2` (đúng số commit remote đang có thêm).
Nghi bản git khác không tự cập nhật ref thì đổi vế phải thành `FETCH_HEAD` — `git fetch` LUÔN ghi
ref này, đo cũng ra `2`.

| Số in ra | Làm gì |
|---|---|
| **0** | pull vốn là lệnh rỗng, việc dở của phiên khác không liên quan → **ĐI TIẾP từ dòng 2 (`state.py claim`)**, quét bình thường |
| **> 0** | có commit mới thật, không đồng bộ được thì quét ra bản tin cũ → chạy `git -C /Users/Huy/Claude/diem-tin-the-gioi status --short` để biết file lạ là gì, ghi log FAIL + `state.py fail web-scan "repo co viec do chua commit: <ten file>"`, push log, KẾT THÚC |

⛔ **TUYỆT ĐỐI KHÔNG `git stash` và KHÔNG commit hộ file lạ** (mục 14 quy tắc toàn cục) — đó là việc đang
làm dở của phiên khác, stash là giấu mất, commit hộ là ký tên vào việc chưa xong. Luật này vốn đã có ở
**Bước 3 (khâu push cuối phiên)**; **nó thiếu ở Bước 1 chính là lý do phiên chết ngay dòng đầu.**
⚠️ Áp y hệt cho MỌI chỗ khác trong file này gọi `pull --rebase` (trước `add_news.py`, lúc push bị từ chối).

⚠️ **PUSH `logs/state.json` NGAY SAU KHI CLAIM — TRƯỚC khi làm baseline** (sự cố 26/07/2026, phiên local
21:30): khoá `state.py` đồng bộ QUA GIT, nên phiên nào chưa push khoá thì phiên kia pull về vẫn thấy
"không ai giữ khoá" và claim tiếp. Local claim 21:41 nhưng để dành push tới cuối bước log → CI pull lúc
22:09 không thấy khoá → **hai phiên cùng quét**, local phải bỏ hết công baseline để nhường. Push khoá
ngay là cách duy nhất để phiên kia nhìn thấy.
⚠️ **Trước khi chạy `add_news.py`, `pull --rebase` rồi ĐỌC LẠI `logs/state.json` xem mình còn giữ khoá
không.** (Pull bị chặn vì unstaged changes → xử theo bảng ở đầu Bước 1, đừng dừng phiên.)
Thấy `lastRunAt`/`heartbeat` của phiên khác mới hơn mình → phiên kia đã cướp khoá: DỪNG, ghi
log SKIP, KHÔNG gọi `state.py skip/fail` (gọi là ghi đè trạng thái RUNNING và nhả khoá của phiên đang
chạy), `rebase --abort` + `reset --hard origin/main` rồi commit riêng dòng log.
BẮT BUỘC pull --rebase trước (2 GitHub Action nạp tin chạy 20:00/20:05 trước đó). claim in ra: SKIP exit 10 = tối nay đã có bản tin; SKIP exit 11 = phiên khác đang chạy (KHÔNG quét chồng); RUN exit 0 = đã giữ khoá, quét tiếp. Cả 2 SKIP: ghi 1 dòng SKIP vào logs/scan-<ngày VN>.log, commit + push log, KẾT THÚC. KẾT THÚC = dừng hẳn phiên ngay — KHÔNG gắn Monitor/script theo dõi phiên kia, không chờ, không điều tra thêm (khoá heartbeat + mốc dự phòng đã lo việc đó).

## Bước 1b — GOM ỨNG VIÊN (bắt buộc từ 27/07/2026, chạy TRƯỚC khi giao agent)
```
python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/harvest.py --gop-ci --json /tmp/ung-vien.json
```
⭐ **Cờ `--gop-ci` là bắt buộc ở phiên LOCAL** (thêm 27/07/2026). Lớp `[HTML]` chạy ở máy Mac chỉ vào
được 10 trang, chạy ở runner Mỹ vào được 25 — 21 domain **chỉ CI đọc được**, trong đó có TOÀN BỘ uỷ ban
THƯỢNG VIỆN (đúng nhóm 1: điều trần + bỏ phiếu, nhóm luôn thiếu tin nhất) và 2 feed `.mil` mà máy Mac
không phân giải nổi DNS. Workflow `harvest-ci.yml` chạy thuần curl (không gọi Claude, không tốn quota)
lúc 20:45 · 21:45 · 03:45 · 04:45 VN và commit lô ứng viên vào `docs/ung-vien-ci.json`; `--gop-ci` gộp
lô đó vào. Đã `pull --rebase` ở bước 1 nên file luôn là bản mới nhất. Lô quá 4 tiếng hoặc lệch khung
ngày thì script tự BỎ và in lý do ra stderr — thấy dòng `[CI] ... BỎ` thì đó là bình thường (CI trễ
cron), KHÔNG phải bug, cứ đi tiếp bằng lô local.

Máy đi lấy, agent đi thẩm định: script quét 67 feed RSS + 8 truy vấn Google News, lọc theo khung hôm nay + hôm qua và theo 5 chủ đề, rồi in ứng viên. Lý do bắt buộc: **WebFetch của subagent bị chặn 403** trong khi curl từ máy trả 200 — nên agent tự quét là sót nguồn (Long War Journal, AllAfrica, Philstar, Inquirer, Lowy, gCaptain đều 0 tin dù nằm trong bảng nguồn). Sáng 27/07 agent Mali báo "không có bài mới" trong khi Google News có 88 item, gồm tin Bloomberg phải nạp bù sau.
Đọc kỹ 3 điều trong output: `[RSS]` có link gốc dùng được; `[GNEWS]` chỉ là RADAR, phải tự tìm bài gốc, KHÔNG nạp link news.google.com; và **ngày in ra là ngày ĐĂNG BÀI, không phải ngày SỰ KIỆN** — nhiều trang đăng lại tin cũ với pubDate mới, phải mở bài kiểm rồi neo `date` theo ngày sự kiện.

Chạy tiếp lớp Telegram (thêm 27/07/2026):
```
python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/telegram_harvest.py
```
Quét kênh Telegram công khai trong `docs/telegram-channels.md`. Lớp `[TG]` **cùng vai RADAR với `[GNEWS]`**: link `t.me` TUYỆT ĐỐI không được nạp vào `sourceUrl`, phải truy về bài gốc — script in sẵn dòng `link dẫn:` là URL ngoài mà bài Telegram trỏ tới, dùng nó trước khi WebSearch. Kênh gắn `⚠️nhanuoc` (TASS/Sputnik/Rybar) chỉ dùng cho phát ngôn CỦA CHÍNH HỌ.
Độ phủ đo thật: mạnh ở **Mỹ–Mali/Sahel** (@AfricaIntel thường kèm link africanews/theafricareport — nguồn mà curl hay bị 403) và một phần **CNQS Mỹ** (@OSINTdefender); **gần như trắng Úc & Biển Đông** vì không kênh nào vừa sống vừa đúng chuyên môn. Đây là lớp BỔ SUNG, thiếu nó không phải lý do hoãn bản tin — lỗi mạng/kênh chết thì bỏ qua, đi tiếp.
Có session Telethon trong môi trường (`TG_API_ID`/`TG_API_HASH`/`TG_SESSION`) thì thêm `--mtproto` để đọc luôn kênh tắt xem trước web; thiếu biến thì script tự lùi về đường web, không lỗi.

## Bước 2 — Quét
Đọc TRỰC TIẾP file `/Users/Huy/Claude/diem-tin-the-gioi/.claude/skills/quet-tin/SKILL.md` (tool Skill KHÔNG đăng ký skill này — gọi qua tool sẽ báo "Unknown skill", cứ Read thẳng file) và làm ĐÚNG playbook trong đó (đã cập nhật theo 5 chủ đề). CLAUDE.md gốc repo tự nạp — đọc mục "LỊCH VÀ PHẠM VI QUÉT" trong đó; bản đầy đủ ở `docs/luat/pham-vi-quet.md`.
🧭 **PHÂN VAI (chốt 29/07/2026) — file kia là playbook NỘI DUNG, file NÀY là quy trình CHẠY.** SKILL.md giữ 5 chủ đề + tiêu chí lọc · kiến trúc agent · thang xác minh · guardrail `add_news.py` · `scan-gaps.json` · phụ lục nguồn. **Lịch/mốc giờ/hạn chót/khoá/commit chỉ được viết ở FILE NÀY** — đừng chép sang SKILL.md. Vì sao: tới 29/07 SKILL.md vẫn ghi "chỉ chạy 1 lần/ngày, TỐI 22:00 (dự phòng 23:00)" trong khi lịch thật đã là 2 phiên/ngày từ 26/07 — hai bộ luật song song thì bộ ít người sửa sẽ mục, mà nó lại là bộ phiên quét đọc trước. Ngược lại **KHÔNG được rút SKILL.md thành stub trỏ về đây**: chính dòng trên bảo đọc nó, trỏ ngược lại là vòng tròn và mất sạch playbook nội dung (cả CI cũng đọc nó qua `.github/prompts/web-scan-ci.md`).
GIỮ NHỊP TIM: sau mỗi mốc lớn (xong baseline · xong agent · xong script) chạy `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/beat_push.py web-scan` + ghi checkpoint log. Khoá hết hạn sau 30' không nhịp. ⛔ **DÙNG ĐÚNG `beat_push.py`, KHÔNG gọi `state.py beat` trần** (vá 20/09/2026 — sự cố thật đêm 19/09, `logs/scan-2026-09-19.log` dòng `[21:45Z]`: CI beat cục bộ đúng nhịp nhưng quên đẩy git, máy khác thấy nhịp cũ rồi giành khoá quét chồng, phí ~12 triệu token). `beat_push.py` gộp cứng ghi-nhịp-tim + đẩy git thành một lệnh, tự lo cả pull/rebase an toàn — không cần gọi `push` rời sau đó nữa.
⏱️ **BEAT TRƯỚC KHI LÀM VIỆC LÂU, KHÔNG PHẢI SAU KHI XONG** (vá 28/07/2026, đo thật trên CI): "sau mỗi mốc lớn" nghe thì đủ nhưng thực tế nhịp ĐẦU TIÊN chỉ tới khi vòng agent xong — mà đó là chặng dài nhất phiên. Phiên tối CI 28/07: start 21:00 → beat đầu **21:26**, tức 25' không nhịp, cách ngưỡng thối 30' đúng **5 phút**. Agent chậm thêm 5' nữa là khoá tự mở TRONG LÚC phiên vẫn đang quét, mốc kế cướp khoá → **hai phiên cùng quét**, đúng sự cố 26/07. Vì vậy beat thêm ở **(a) ngay sau `harvest.py` + `telegram_harvest.py`** và **(b) ngay TRƯỚC khi giao lô agent**; nguyên tắc chung: **hai nhịp liên tiếp không cách quá ~15 phút**.
⛔ **TRẦN AGENT CON: tối đa 06 lần giao agent cả phiên (05 luồng gốc + 01 agent bổ sung duy nhất, giao một lần); hụt sàn sau đó thì CHỐT, không vòng thứ hai** (vá 05/10/2026, chi tiết ở SKILL.md Bước 3-4).
Ràng buộc cứng: KHÔNG dùng Read đọc cả index.html; mọi thao tác chèn tin qua `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/add_news.py /tmp/new_items.json`; khung 24h (nới 48h nếu thiếu); được trả mảng rỗng, KHÔNG bịa tin/link.

## Bước 2b — CẢ HAI PHIÊN: dùng file Jay Lâm làm BỘ LỌC (đảo nguyên tắc 01/08/2026)
Làm SAU khi đã nạp tin quét, TRƯỚC khi commit. **Nội dung đầy đủ: điều 5 mục "PHIÊN TỐI — BỐI CẢNH RIÊNG" cuối file này** — đọc thẳng điều đó, cả hai phiên đều làm y hệt (chỉ khác: hạn chót 21:45 là của riêng phiên tối).

⛔ **MỤC 5 "Tin Jay Lâm gửi" ĐÃ BỎ HẲN 01/08/2026.** Huy đảo nguyên tắc: file Jay Lâm gửi **chỉ dùng để so xem tin mình quét có trùng tin anh ta đã có không**, trùng thì bỏ tin CỦA MÌNH đi. Nó không đóng góp dòng nào vào bản tin nữa. Bỏ bước này thì bản tin **lặp lại tin Jay Lâm đã đọc** — không mất tin, không lỗi, không cảnh báo.

## Bước 3 — Kết thúc (LUÔN gọi 1 trong 3)
- Nạp được tin: `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/state.py done web-scan "<tóm tắt số tin mỗi chủ đề>"`
- Lô rỗng: `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/state.py skip web-scan "<lý do>"`
- Lỗi giữa chừng: `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/state.py fail web-scan "<lý do>"` rồi VẪN ghi log + push
**TRƯỚC KHI COMMIT — BẮT BUỘC ghi `logs/scan-gaps.json`** (chỉ thị Huy 25/07/2026: email phải ghi cả **chủ đề thiếu VÀ lý do**). Lý do thiếu là kiến thức của phiên quét, Action không tự suy ra được → không ghi file thì email MẤT mục này. Dùng tool Write, liệt kê đủ 5 chủ đề (+ Báo Mới), mỗi chủ đề `{name, count, target, min, thieu, reason}`; `date` của file **PHẢI khớp `DATA.generatedAt`** (nạp nhiều lô thì lấy ngày lô chạy CUỐI) — lệch là `send-email.js` bỏ cả mục để không gửi lý do hôm trước. Mẫu JSON đầy đủ + quy tắc viết `reason`: xem **Bước 4b** trong `.claude/skills/quet-tin/SKILL.md`.

`git -C /Users/Huy/Claude/diem-tin-the-gioi add index.html logs/` (phải có logs/state.json VÀ logs/scan-gaps.json), commit mẫu `Cap nhat ban tin DD/MM: +N tin (5 chu de)`, push `main` — đều qua `git -C /Users/Huy/Claude/diem-tin-the-gioi ...`. Push bị từ chối → `git -C ... pull --rebase origin main` rồi push lại; nếu pull báo unstaged changes ở file KHÔNG thuộc lô này thì cứ push, đừng commit hộ file lạ (luật này nay áp cho CẢ Bước 1 — xem bảng ở đó; thiếu nó ở Bước 1 chính là chỗ phiên chết ngay dòng đầu 27/07 và 29/07).
Email + file Word tự gửi lamgiaphat1603@gmail.com qua GitHub Action notify-email khi có commit `Cap nhat ban tin` — skill không cần làm gì thêm NGOÀI việc ghi `logs/scan-gaps.json` ở trên.

Báo cáo cuối ngắn gọn: số tin mỗi chủ đề (Nội bộ Mỹ / Úc-Biển Đông / CNQS Mỹ / Mali / Tập trận), chủ đề nào thiếu (đã nới 48h chưa), trạng thái push.
📌 **Tin Mali từ 05/08/2026 KHÔNG vào file Word bản tin nữa** (chỉ thị Huy) — vẫn quét, vẫn nạp `usNews`, nhưng đi ở **bản sáng 🎖️ Sự kiện & Tập trận**. Phiên quét không phải làm gì thêm; `make_docx.py` in một dòng ghi vết mỗi lần bỏ. Vẫn ghi mục Mali vào `scan-gaps.json` như thường.

## Bước 4 — CHỈ PHIÊN SÁNG SỚM: gộp thêm sự kiện + tập trận + think-tank (nội dung dời sang [`quy-trinh-event-scan.md`](quy-trinh-event-scan.md) 05/10/2026)

Làm khi (i) vừa xong bản tin 5 chủ đề ở phiên SÁNG SỚM (giờ VN lúc bắt đầu < 14:00), hoặc (ii) lối SKIP ở Bước 0 mà `state.py claim event-scan` trả exit 0. **Đến lúc đó mới Read `docs/quy-trinh-event-scan.md`** (đừng đọc trước: 12 KB chỉ dùng một lần ở cuối phiên). Phiên nhường/SKIP exit 10-11-12 không đọc file ấy. Phiên TỐI (đã bỏ) không làm bước này.

## PHIÊN TỐI — BỐI CẢNH RIÊNG ⛔ ĐÃ BỎ 18/09/2026 (bản đầy đủ: [`nhat-ky-vap-phien-toi.md`](nhat-ky-vap-phien-toi.md))

⛔ **Không còn mốc tối nào chạy.** Điều 1-4 (mốc 21:15, hạn chót 22:00, SKIP êm, sổ đã gửi) là lịch sử, đã dời sang file nhật ký; chỉ mở khi cần biết *vì sao* một luật ra đời. Bốn cơ chế vẫn áp cho ca sáng: (i) tính biên ngược từ mốc CUỐI chứ không từ mốc đầu · (ii) cờ `state.py` nói dối vì chỉ biết «đã chạy xong», không biết «đã gửi» · (iii) sổ trống có hai nghĩa · (iv) chốt lô đang có khi sát hạn, đừng vòng bổ sung.

**Điều 3 còn hiệu lực — SỔ ĐÃ GỬI TRỐNG CÓ HAI NGHĨA, phiên LOCAL đọc log run CI trước khi kết luận** (áp mọi phiên; phiên local gọi được `gh`, phiên CI thì không):
| Sổ trống vì | Dấu hiệu | Làm gì |
|---|---|---|
| Bản tin **thật sự chưa gửi** | không có run `notify-email.yml` nào, hoặc run ĐỎ | QUÉT THẬT |
| **Khâu GHI SỔ hỏng**, bản tin ĐÃ tới tay | run `notify-email.yml` XANH + log có dòng `Đã gửi … file .docx tới <chat>` | **KHÔNG quét lại.** Ghi bù sổ bằng `python3 .github/scripts/so_da_gui.py --ghi --buoi sang\|toi` rồi commit |

```
gh run list -R huyneo1101-dotcom/diem-tin-the-gioi --workflow notify-email.yml --limit 2 --json databaseId,createdAt,conclusion --jq '.[] | [.databaseId, .createdAt, .conclusion] | @tsv'
gh run view <id> -R huyneo1101-dotcom/diem-tin-the-gioi --log | grep -iE 'Da gui|GUI_EMAIL|khong push duoc so'
```
`Đã gửi 0 message + file .docx` là BÌNH THƯỜNG (chỉ thị Huy 27/07: chỉ gửi file word); bằng chứng gửi được là cụm `+ file .docx tới <chat>`. ⛔ KHÔNG sửa `logs/state.json` để lách cờ đã-xong: cổng gửi email xét commit message + khung giờ VN, không xét khoá.

5. **DÙNG FILE JAY LÂM LÀM BỘ LỌC — làm SAU khi đã nạp tin quét, TRƯỚC khi commit** (đảo nguyên tắc 01/08/2026).

   > Nguyên văn Huy: *"thay đổi hoàn toàn nguyên tắc. file của Jay Lâm gửi chỉ là để so sánh xem có tin nào mày quét được mà bị trùng với tin trong file đó không thôi"* · *"nếu có tin bị trùng với file Jay Lâm thì tự xoá khỏi tổng hợp tin đã quét đi và gửi file word (trong đó không có tin nào từ Jay Lâm)"*.

   ⛔ **MỤC 5 "Tin Jay Lâm gửi" ĐÃ BỎ HẲN.** File Jay Lâm không đóng góp dòng nào vào bản tin; nó chỉ dùng để **bớt tin CỦA MÌNH** mà anh ta đã đọc rồi. Mọi chỉ dẫn cũ về tóm tắt-để-đăng, `la_cnqs`, `nguon_ten`, nhãn xác minh đều hết hiệu lực.

   ⏰ **KÍCH BOT HÚT TELEGRAM NGAY TRƯỚC KHI ĐỌC — bỏ bước này là bỏ sót file gửi sát giờ** (giữ nguyên từ 30/07/2026). **Cơ chế gây vấp:** file Jay Lâm gửi chỉ vào bảng `dt_jaylam_inbox` khi `telegram-bot.yml` chạy, mà workflow đó khai cron `*/5` nhưng GitHub thực tế chạy nó **cách nhau 01 tới 02 giờ** (đo 30/07: 00:15 · 02:29 · 03:37 · 06:12 · 09:05 · 11:19 · 12:59 UTC). Tối 30/07 Jay Lâm gửi file lúc 21:20 VN, phiên quét đọc lúc 21:25 và **chỉ thấy file của HÔM TRƯỚC**. Không lỗi, không cảnh báo — hàng chờ có dữ liệu nên nhìn như đang chạy đúng.
   ```
   gh workflow run telegram-bot.yml --repo huyneo1101-dotcom/diem-tin-the-gioi
   ```
   Chờ run đó xong (`gh run watch <id> --exit-status --interval 15`, ~2 phút) rồi mới đọc. **Fail-open CÓ TIẾNG:** gọi `gh` không được (phiên CI hay bị chặn *requires approval*) thì ghi một dòng vào log rằng **chưa kích được bot** rồi đi tiếp — im lặng ở đây là dựng lại đúng vùng câm vừa bịt.
   ```
   python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/tin_jaylam.py --liet-ke
   ```
   | Mã thoát | Nghĩa |
   |---|---|
   | **10** | không có file nào trong khung ngày — BỎ QUA bước này, đi tiếp |
   | **0** | có file: in TOÀN VĂN với file chưa trích, in BẢNG GỌN với file đã trích |

   **(a) Trích bảng đối chiếu** (chỉ với file chưa trích) — trích **ĐỦ MỌI TIN trong file, không lọc, không chọn lọc**; sót một tin là tin đó lọt vào bản tin dù Jay Lâm đã có:
   ```
   python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/tin_jaylam.py --ghi /tmp/bang-jaylam.json
   ```
   `[{"id": <id>, "tin": [{"tieu_de": "...", "url": "https://..."}, ...]}]` — `url` được phép rỗng (Jay Lâm viết lại bằng tiếng Việt, nhiều tin không kèm link). Trích xong thì 3 ngày sau vẫn dùng lại được, khỏi đọc lại 34.000 ký tự mỗi phiên.

   **(b) Đối chiếu rồi khai tin CỦA MÌNH bị bỏ:**
   ```
   python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/tin_jaylam.py --ghi-loai /tmp/loai-jaylam.json
   ```
   `[{"url": "<sourceUrl tin của mình>", "tieu_de": "<tiêu đề tin của mình>", "id_jay": <id>, "trung_voi": "<mảnh tương ứng bên file Jay>"}]`

   ⚠️ **SO LINK THUẦN LÀ VÔ DỤNG — đã đo, đừng dựng lại đường đó.** Đối chiếu 12 tin quét tối 01/08 với 37 URL trong file Jay Lâm ra **0 tin trùng URL**, trong khi đọc hiểu ra **03 tin trùng sự kiện** (Mahan Air · tuần tra Scarborough · NITE-STAR 981 triệu USD). Jay Lâm viết lại bằng tiếng Việt từ nguồn khác hẳn. **Phép lọc là ĐỌC HIỂU THEO SỰ KIỆN**; link chỉ là chốt chắc khi tình cờ trùng.
   ⚠️ **Đối chiếu phải so với FILE GỐC hoặc bảng trích ĐẦY ĐỦ, KHÔNG so với danh sách tin đã viết lại của mình.** Vấp thật 01/08: danh sách 29 tin viết lại của phiên trước đã qua lọc trùng rồi, nên đúng những tin trùng lại vắng mặt trong đó — dùng nó làm bảng đối chiếu thì kết luận "không có tin nào trùng".
   ⚠️ **Phạm vi lọc: MỌI tin còn trong khung ngày (2-3 ngày), không chỉ lô vừa nạp** — file Jay Lâm gửi hôm nay vẫn phải lọc tin CNQS Mỹ mình đăng từ 3 ngày trước.
   ⚠️ **`trung_voi` bắt buộc** — xoá tin là mất nội dung, phải soi ngược được vì sao. Script chặn nếu thiếu.
   ⚠️ **Không chắc thì ĐỪNG khai.** Sót một tin ⇒ bản tin lặp tin Jay Lâm đã có (Huy thấy được); khai thừa ⇒ **tin của mình biến mất, không ai thấy**.
   ⚠️ **Sổ nằm ở `logs/trung-jaylam.json` — phải `git add logs/` cùng bản tin**, không thì `make_docx.py` không thấy sổ và bản .docx vẫn lặp tin.
   ⚠️ **Một mục sai làm CHẶN CẢ LÔ** (mã 1, không ghi gì) — sửa mục lỗi rồi chạy lại, đừng bỏ mục lỗi đi rồi ghi phần còn lại.
   ⛔ **BỎ BƯỚC NÀY THÌ BẢN TIN LẶP TIN JAY LÂM ĐÃ CÓ** — không mất tin, không lỗi. Quá hạn 21:45 của điều 2 thì vẫn **chốt bản tin trước**, bỏ bước này; file Jay Lâm còn hiệu lực 3 ngày nên bản tin sau vẫn lọc được phần còn lại.
   ✅ **PHIÊN SÁNG SỚM CŨNG LÀM BƯỚC NÀY.** File gửi 21:34 tối qua còn hiệu lực tới bản tin sáng nay; bỏ ở phiên sáng thì bản sáng lặp tin.

   Bộ test canh: `tests/test-tin-jaylam-xu-ly.py` (39 ca · 19 bản hỏng) và `tests/test-tin-jaylam-trong-docx.py` (20 ca · 11 bản hỏng).
