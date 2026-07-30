# Routine WEB-SCAN — bản tin 5 chủ đề (NGUỒN SỰ THẬT DUY NHẤT)

> **File này là nguồn sự thật duy nhất về quy trình quét bản tin cho CẢ HAI phiên** (sáng sớm + tối).
> Dời từ `~/.claude/scheduled-tasks/web-scan-diem-tin/SKILL.md` vào repo ngày 27/07/2026 — vùng `~/.claude/` là sensitive, mọi Edit vào đó đều bị hỏi quyền bất kể allowlist, trong khi file này rất hay phải vá bài học mới. Repo thì Edit/Write đã allow toàn phần + có git history.
> **Ai đọc file này:** task local `web-scan-diem-tin` (phiên SÁNG SỚM 04:30/05:30) và task local `web-scan-diem-tin-toi` (phiên TỐI 21:15) — SKILL.md của 2 task đó giờ chỉ là stub trỏ về đây. **Sửa quy trình thì sửa file này**, đừng sửa stub.

Quét tin và xuất bản bản tin cho web "Điểm Tin Thế Giới" (https://huyneo1101-dotcom.github.io/diem-tin-the-gioi).
Repo: /Users/Huy/Claude/diem-tin-the-gioi (git remote SSH, push thẳng nhánh `main`).

Bản tin 2 phiên/ngày cùng playbook 5 chủ đề: TỐI (ô khoá `toi`) + SÁNG SỚM (ô khoá `sang`), cả hai đều gửi email + file Word. **Từ 28/07/2026, phiên SÁNG SỚM sau khi xong bản tin 5 chủ đề còn làm TIẾP pipeline `event-scan` (sự kiện/tập trận/think-tank, trước đây là phiên riêng) trong CÙNG session — xem Bước 4.**

⚠️ **PHÂN VAI: quy trình dưới đây là CHUNG cho cả hai phiên; mày là phiên nào thì xem stub task đã giao mày việc.** Task `web-scan-diem-tin` lo phiên SÁNG SỚM; task `web-scan-diem-tin-toi` lo phiên TỐI (tách 27/07/2026 vì phiên tối có hạn chót email cứng, cần fire sớm hơn để có biên; một task chỉ nhận một biểu thức cron nên phải tách). Cả hai task **KHÔNG chép lại quy trình** mà cùng Read file này — để hai phiên không bao giờ lệch nhau. Phiên TỐI có thêm mục "PHIÊN TỐI — BỐI CẢNH RIÊNG" ở cuối file.

| Phiên | CI chính | local | CI dự phòng | local lưới cuối | Ai chạy phần local |
|---|---|---|---|---|---|
| SÁNG SỚM | **03:47** VN | **04:30** | 04:47 | 05:30 | task `web-scan-diem-tin` |
| TỐI | 20:47 VN | 21:15 ← lớp cuối trong hạn | 21:47 = lớp VÉT đã trễ | — | task `web-scan-diem-tin-toi` |

📅 **BẢNG LỊCH ĐẦY ĐỦ + NGUỒN SỰ THẬT: [`docs/LICH.md`](LICH.md)** — sinh từ chính dòng `cron:`
của workflow bằng `python3 scripts/kiem_lich.py --sinh`. Số giờ ở bảng trên là bản rút gọn cho
tiện đọc; **lệch nhau thì `LICH.md` thắng**. Cổng `kiem_lich.py --kiem` canh việc này (dựng
30/07/2026 sau khi bắt được **47 chỗ** trong tài liệu còn ghi lịch CI cũ 21:00/22:00/04:00/05:00,
tức lịch đã dời sớm 13 phút mà không ai sửa những chỗ chép lại).

Nguyên nhân dời CI sáng: mốc CI 04:30 cũ **không nổ** sáng 27/07 (GitHub hay trễ/bỏ cron lúc tải cao) mà phiên sáng khi đó không có lưới local → mất trắng bản tin sáng. CI vì thế lên 04:00 để local 04:30 kịp gánh, rồi **dời tiếp về 03:47** (và cả 04 mốc sớm 13 phút) để `harvest-ci.yml` xong trước khi phiên quét bắt đầu.

⏰ **PHIÊN TỐI CÓ HẠN CHÓT CỨNG: email muộn nhất 22:00** (chỉ thị Huy 27/07/2026): phiên chạy ở mốc tối **quá 21:45 chưa nạp xong thì chốt lô đang có**, `add_news.py` + commit ngay, phần thiếu ghi `scan-gaps.json`; không vòng bổ sung lần 3-4 để gom cho đủ chỉ tiêu. **Phiên SÁNG SỚM KHÔNG có hạn chót này** — cứ quét đủ 5 chủ đề bình thường. Chi tiết phiên tối: mục cuối file.

Cách làm ở MỌI mốc là như nhau: cứ `claim` như thường — CI đã xong/đang chạy thì SKIP êm, CI không quét (trễ/chết/hết quota) thì mày quét đủ 5 chủ đề rồi commit `Cap nhat ban tin ...` (email + .docx do Action `notify-email.yml` tự gửi khi thấy push `index.html` với tiền tố commit đó — local push cũng kích như CI, không phải làm gì thêm). Phiên sáng 10:15 kiểu cũ vẫn bỏ.
⚠️ Local chỉ chạy khi app Claude đang mở và máy đã thức — mốc 04:30 phụ thuộc lịch wake của máy (`pmset repeat wakeorpoweron`); máy ngủ thì mốc này im, đó là lý do vẫn giữ CI 03:47/04:47 làm mốc chính.

PHẠM VI (chỉ thị Huy 2026-07-23): mỗi phiên CHỈ quét 5 CHỦ ĐỀ, mỗi chủ đề 5–10 bài, khung 24 GIỜ gần nhất (nới 48h nếu chủ đề đó thiếu <5 bài):
⛔ **"Nới 48h" = HÔM NAY + HÔM QUA, KHÔNG phải lùi 2 ngày lịch** (chỉ thị Huy 27/07/2026: *"quét tin ngày 26 thì chỉ được lấy tin tối đa là ngày 25, không được phép lấy tin ngày 24"*). Giao prompt agent thì **ghi thẳng 2 ngày cụ thể** thay vì chữ "48h" — agent hay hiểu thành lùi 2 ngày. Tin cũ hơn: BỎ, ghi `logs/loai-tin.md` + lý do vào `scan-gaps.json`, thà chủ đề về 0. `add_news.py` cũng chặn cứng (kiểm ngày 2 lớp: so batch VÀ so hôm nay giờ VN) nên nhận về cũng không nạp được; gặp lỗi "cũ hơn 1 ngày so với HÔM NAY" thì bỏ tin, ĐỪNG lùi ngày batch để lách.
1. Nội bộ Mỹ — **5 NHÓM, HAI HẠNG ƯU TIÊN (chỉ thị Huy 27/07/2026, GHI ĐÈ mức "SIẾT" cũ). BẮT BUỘC vét cạn nhóm (1) TRƯỚC; chưa đủ chỉ tiêu mới lấy sang các nhóm còn lại, và (2)(3)(4)(5) NGANG HÀNG NHAU:** (1) TOÀN BỘ phiên điều trần trong ngày + TOÀN BỘ kết quả bỏ phiếu thông qua dự luật; (2) sáng kiến + chiến lược của chính quyền Trump trên kênh chính thống các bộ (sắc lệnh, memorandum, chiến lược quốc gia, fact sheet, thông cáo bộ); (3) diễn biến biểu tình/tuần hành; (4) hoạt động kinh tế Mỹ + hoạt động khác của các bộ và Nhà Trắng (Trump + bộ sậu action); (5) **BẦU CỬ** — bầu cử giữa nhiệm kỳ/sơ bộ, tranh cử, thăm dò, quy định cử tri, kiểm phiếu, redistricting/gerrymander, đua ghế Thượng viện/Hạ viện/thống đốc (tách riêng 27/07/2026, trước gộp chung nhóm 3). → usNews, category Chính trị (nhóm 4 có thể Kinh tế). Nhóm 3-4-5 ĐẢO lại phần cấm cũ, nhưng phải là chuyện NỘI BỘ MỸ — từ khoá chung như protest/tariff/election phải kèm ngữ cảnh Mỹ. Số nhóm 2→5 là NHÃN, không phải thứ tự.
2. Úc & Biển Đông — AUKUS/QP Úc (region Ấn Độ Dương - Thái Bình Dương) + chủ quyền/tuần tra/tập trận Biển Đông (region Đông Á). **MỞ RỘNG 27/07/2026: tìm thêm tin CÁC NƯỚC KHÁC quanh Biển Đông** — Malaysia, Indonesia, Brunei, Đài Loan, Việt Nam, đàm phán COC ASEAN-Trung Quốc, các thực thể Natuna/Bãi Tư Chính/Luconia/Bãi Cỏ Rong. → worldNews.
⛔ **Nhật/Ấn/Hàn CHỈ tính khi hoạt động TẠI vùng biển này — quốc phòng NỘI BỘ của họ KHÔNG thuộc chủ đề** (siết 28/07/2026, Huy bắt lỗi): tối 28/07 lọt tin "Hàn Quốc luật hoá cam kết phi hạt nhân để thúc đẩy dự án tàu ngầm hạt nhân" (Korea Herald) — thuần luật NPT + chương trình tàu ngầm trong nước Hàn, không một chữ Biển Đông. **Chuẩn nhận: tin phải neo được vào một QUỐC GIA ven Biển Đông hoặc chính VÙNG BIỂN đó, không phải neo vào loại khí tài.** Cửa lọt ở `scripts/topics.py`: từ khoá `"nuclear submarine"` để trần khớp mọi nước có tàu ngầm hạt nhân — đã bỏ, vì tin AUKUS thật luôn có `aukus`/`australia` (cùng bẫy với `"scarborough"` trần khớp thị trấn Scarborough).
3. CNQS Mỹ — khí tài/hệ thống cụ thể (tên lửa, phòng không, hải quân, không gian, laser, drone). → usNews, category Công nghệ quân sự. ⏳ **KHUNG NGÀY NỚI RIÊNG: lùi tới 3 ngày** (quét 27 thì lấy được tới 24); 4 chủ đề còn lại vẫn chỉ hôm nay + hôm qua. add_news.py áp theo category nên phải đặt đúng `"category":"Công nghệ quân sự"`.
4. Mỹ–Mali — Mỹ cân nhắc/không kích JNIM ở Sahel (gắn Mali/JNIM/Bamako/Sahel). → usNews, dossier 🟤 Mỹ – Mali.
5. Tập trận Predator's Run 2026 (Mỹ–Úc–Philippines, tới ~29/7) → cập nhật qua exerciseUpdates (tên khớp "Predator's Run 2026 (tập trận Mỹ - Úc - Philippines)").
BỎ khỏi phạm vi: Kinh tế, Ngoại giao chung, xNews, các vùng thế giới khác, tạo mới dipEvents, và sàn 15+15. Báo Mới: vẫn quét nhưng CHỈ giữ bài hợp 5 chủ đề.

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
git -C /Users/Huy/Claude/diem-tin-the-gioi pull --rebase origin main
python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/state.py claim web-scan
git -C /Users/Huy/Claude/diem-tin-the-gioi add logs/
git -C /Users/Huy/Claude/diem-tin-the-gioi commit -q -m "log: claim web-scan phien toi (local)"
git -C /Users/Huy/Claude/diem-tin-the-gioi push origin main -q
```
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
Đọc TRỰC TIẾP file `/Users/Huy/Claude/diem-tin-the-gioi/.claude/skills/quet-tin/SKILL.md` (tool Skill KHÔNG đăng ký skill này — gọi qua tool sẽ báo "Unknown skill", cứ Read thẳng file) và làm ĐÚNG playbook trong đó (đã cập nhật theo 5 chủ đề). CLAUDE.md gốc repo tự nạp — đọc banner "CẬP NHẬT PHẠM VI 2026-07-23" ở đầu file.
🧭 **PHÂN VAI (chốt 29/07/2026) — file kia là playbook NỘI DUNG, file NÀY là quy trình CHẠY.** SKILL.md giữ 5 chủ đề + tiêu chí lọc · kiến trúc agent · thang xác minh · guardrail `add_news.py` · `scan-gaps.json` · phụ lục nguồn. **Lịch/mốc giờ/hạn chót/khoá/commit chỉ được viết ở FILE NÀY** — đừng chép sang SKILL.md. Vì sao: tới 29/07 SKILL.md vẫn ghi "chỉ chạy 1 lần/ngày, TỐI 22:00 (dự phòng 23:00)" trong khi lịch thật đã là 2 phiên/ngày từ 26/07 — hai bộ luật song song thì bộ ít người sửa sẽ mục, mà nó lại là bộ phiên quét đọc trước. Ngược lại **KHÔNG được rút SKILL.md thành stub trỏ về đây**: chính dòng trên bảo đọc nó, trỏ ngược lại là vòng tròn và mất sạch playbook nội dung (cả CI cũng đọc nó qua `.github/prompts/web-scan-ci.md`).
GIỮ NHỊP TIM: sau mỗi mốc lớn (xong baseline · xong agent · xong script) chạy `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/state.py beat web-scan` + ghi checkpoint log + push. Khoá hết hạn sau 30' không nhịp.
⏱️ **BEAT TRƯỚC KHI LÀM VIỆC LÂU, KHÔNG PHẢI SAU KHI XONG** (vá 28/07/2026, đo thật trên CI): "sau mỗi mốc lớn" nghe thì đủ nhưng thực tế nhịp ĐẦU TIÊN chỉ tới khi vòng agent xong — mà đó là chặng dài nhất phiên. Phiên tối CI 28/07: start 21:00 → beat đầu **21:26**, tức 25' không nhịp, cách ngưỡng thối 30' đúng **5 phút**. Agent chậm thêm 5' nữa là khoá tự mở TRONG LÚC phiên vẫn đang quét, mốc kế cướp khoá → **hai phiên cùng quét**, đúng sự cố 26/07. Vì vậy beat thêm ở **(a) ngay sau `harvest.py` + `telegram_harvest.py`** và **(b) ngay TRƯỚC khi giao lô agent**; nguyên tắc chung: **hai nhịp liên tiếp không cách quá ~15 phút**.
Ràng buộc cứng: KHÔNG dùng Read đọc cả index.html; mọi thao tác chèn tin qua `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/add_news.py /tmp/new_items.json`; khung 24h (nới 48h nếu thiếu); được trả mảng rỗng, KHÔNG bịa tin/link.

## Bước 3 — Kết thúc (LUÔN gọi 1 trong 3)
- Nạp được tin: `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/state.py done web-scan "<tóm tắt số tin mỗi chủ đề>"`
- Lô rỗng: `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/state.py skip web-scan "<lý do>"`
- Lỗi giữa chừng: `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/state.py fail web-scan "<lý do>"` rồi VẪN ghi log + push
**TRƯỚC KHI COMMIT — BẮT BUỘC ghi `logs/scan-gaps.json`** (chỉ thị Huy 25/07/2026: email phải ghi cả **chủ đề thiếu VÀ lý do**). Lý do thiếu là kiến thức của phiên quét, Action không tự suy ra được → không ghi file thì email MẤT mục này. Dùng tool Write, liệt kê đủ 5 chủ đề (+ Báo Mới), mỗi chủ đề `{name, count, target, min, thieu, reason}`; `date` của file **PHẢI khớp `DATA.generatedAt`** (nạp nhiều lô thì lấy ngày lô chạy CUỐI) — lệch là `send-email.js` bỏ cả mục để không gửi lý do hôm trước. Mẫu JSON đầy đủ + quy tắc viết `reason`: xem **Bước 4b** trong `.claude/skills/quet-tin/SKILL.md`.

`git -C /Users/Huy/Claude/diem-tin-the-gioi add index.html logs/` (phải có logs/state.json VÀ logs/scan-gaps.json), commit mẫu `Cap nhat ban tin DD/MM: +N tin (5 chu de)`, push `main` — đều qua `git -C /Users/Huy/Claude/diem-tin-the-gioi ...`. Push bị từ chối → `git -C ... pull --rebase origin main` rồi push lại; nếu pull báo unstaged changes ở file KHÔNG thuộc lô này thì cứ push, đừng commit hộ file lạ (luật này nay áp cho CẢ Bước 1 — xem bảng ở đó; thiếu nó ở Bước 1 chính là chỗ phiên chết ngay dòng đầu 27/07 và 29/07).
Email + file Word tự gửi lamgiaphat1603@gmail.com qua GitHub Action notify-email khi có commit `Cap nhat ban tin` — skill không cần làm gì thêm NGOÀI việc ghi `logs/scan-gaps.json` ở trên.

Báo cáo cuối ngắn gọn: số tin mỗi chủ đề (Nội bộ Mỹ / Úc-Biển Đông / CNQS Mỹ / Mali / Predator), chủ đề nào thiếu (đã nới 48h chưa), trạng thái push.

## Bước 4 — CHỈ PHIÊN SÁNG SỚM: gộp thêm sự kiện + tập trận + think-tank (gộp 28/07/2026)

> **Chỉ thị Huy 28/07/2026:** *"sự kiện sáng thì quét gộp với quét tin 4h sáng cũng được."* Trước đây
> đây là pipeline `event-scan` RIÊNG (CI `claude-event-scan.yml` 08:45/09:45 + task local
> `event-scan-diem-tin` 09:15/10:15) — 3 lần quét thật/ngày. Từ 28/07/2026 chỉ còn **2 lần quét
> thật/ngày**: phiên TỐI (bản tin 5 chủ đề) và phiên SÁNG SỚM (bản tin 5 chủ đề **+ sự kiện/tập
> trận/think-tank ngay trong CÙNG một phiên**). `claude-event-scan.yml` và task `event-scan-diem-tin`
> đã bị xoá/tắt — ĐỪNG dựng lại, đừng kích tay chúng.

**CHỈ chạy bước này khi phiên vừa xong ở TRÊN là phiên SÁNG SỚM** (giờ VN lúc bắt đầu < 14:00 —
đúng ô `state.py` đã tự suy ở Bước 1). Phiên TỐI **KHÔNG** làm bước này, dừng lại ở Bước 3.

Đây là **pipeline THỨ HAI, khoá RIÊNG** (`event-scan`, khác `web-scan` ở Bước 1-3) — vẫn `claim` riêng,
`done`/`skip`/`fail` riêng, và **commit RIÊNG** (không gộp chung commit bản tin), vì `notify-morning.yml`
chỉ bắt tiền tố commit của pipeline này. Lý do giữ tách: `state.py`/`canary.py`/`notify-morning.yml`
đều phân biệt hai pipeline theo tên — gộp làm một sẽ vỡ cả khoá idempotent lẫn cổng gửi email/Telegram
sự kiện riêng (🎖️ khác 📰). Chỉ có **nơi kích** là gộp lại (chung 1 phiên/session), không phải **cơ chế**.

### 4.1 — Đồng bộ + giành khoá pipeline `event-scan`
```
git -C /Users/Huy/Claude/diem-tin-the-gioi pull --rebase origin main
python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/state.py claim event-scan
```
⛔ `cannot pull with rebase: You have unstaged changes` → xử theo đúng bảng ở **Bước 1** (fetch +
`rev-list --count HEAD..origin/main`; ra 0 thì ĐI TIẾP). Đừng dừng phiên, đừng stash, đừng commit hộ.
SKIP exit 10 = sáng nay đã xong (có thể do CI/local khác vừa chạy) — ghi 1 dòng SKIP vào log, commit +
push log, DỪNG bước này (phiên vẫn coi là hoàn tất bình thường, vì bản tin 5 chủ đề ở Bước 1-3 đã xong).
SKIP exit 11 = phiên khác đang giữ khoá `event-scan` — cũng SKIP êm, không chờ, không Monitor.
RUN exit 0 = giữ khoá, làm tiếp.

### 4.2 — Quét sự kiện + tập trận
Giao agent (tool Agent, `model: "sonnet"`): nhúng nguyên output
`python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/add_news.py --recent-titles 20` để chống trùng;
tìm **sự kiện ngoại giao có ký kết** trong 48h + **diễn biến tập trận** + tin liên quan (`relate`, đăng
trong 48h). Gộp `/tmp/new_items_event.json` (chỉ khoá `newDipEvents`/`dipEventUpdates`/`newExercises`/
`exerciseUpdates` + `date`) rồi `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/add_news.py /tmp/new_items_event.json`.
Nhịp tim: `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/state.py beat event-scan` — beat NGAY
TRƯỚC khi giao agent (không đợi agent xong), hai nhịp liên tiếp không cách quá ~15 phút (cùng bài học
vá 28/07/2026 đã áp cho pipeline `web-scan` ở Bước 2).

### 4.3 — Bối cảnh + khái niệm tập trận
Với **mỗi cuộc tập trận MỚI vừa tạo** (`newExercises`) VÀ **mỗi cuộc đang diễn ra CHƯA có `background`**,
giao agent Sonnet viết `background` (2–4 câu bối cảnh chiến lược, nhiều đoạn ngăn `\n`) + `concepts`
(3–6 thuật ngữ, `[{term,def}]`, def 1 câu). Ghi `/tmp/briefing.json` =
`[{"name":"<khớp đúng name>","background":"...","concepts":[...]}]` rồi
`python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/set_exercise_briefing.py /tmp/briefing.json`.
Không viết lại cho cuộc đã có background trừ khi diễn biến đổi bối cảnh lớn.

### 4.4 — Bài phân tích think-tank (mỗi phiên sáng sớm, không chỉ Chủ nhật)
Mục 🧠 Phân tích → 🏛️ Think-tank (`DATA.analyses`).
1. `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/add_analyses.py --candidates` — ứng viên
   **hai lớp**, xếp theo khu vực: `[RSS]` 27 viện có feed, rồi `[HTML]` 10 viện không có feed nhưng
   quét được trang danh sách (thêm 30/07/2026 — đo lần đầu: 159 + 44 ứng viên). Dòng cuối in vùng
   **vẫn** phải bù bằng `WebSearch site:<domain>`, đã trừ sẵn nguồn hai lớp trên đã phủ.
   - Thấy dòng ⚠️ *"Trang HTML KHÔNG ra link bài nào"* → viện đó đổi giao diện, biểu thức đường dẫn
     đã chết. Chạy `add_analyses.py --kiem-html` để soi rồi sửa `THINKTANK_HTML`; **đừng đọc thành
     "hôm nay viện không ra bài"**, hai ca đó khác nhau và script đã tách riêng thông điệp.
   - Ứng viên `[HTML]` có ngày lấy từ trang danh sách hoặc từ meta trang bài. Vẫn phải MỞ ĐỌC như
     mọi ứng viên khác ở bước 2 — bước đó tự xác nhận lại ngày.
2. Giao agent Sonnet chọn **4–6 bài**, phủ **ít nhất 2–3 khu vực khác nhau** (1–2 bài trọng tâm cũ:
   Úc/AUKUS · Biển Đông · răn đe hạt nhân/CNQS · Mỹ–Trung–Đài Loan · Mali/Sahel; 1–2 bài vùng khác
   đang có chuyện). LOẠI: chính trị xã hội nội bộ Mỹ, quảng bá viện, điểm sách, điểm báo. Agent phải
   MỞ ĐỌC từng bài (WebFetch) rồi viết tiếng Việt đủ field (`title`/`summary`/`takeaway`/`topic`/
   `region`/`author`/`outlet`/`date`). Số liệu mập mờ/lỗi ký tự → BỎ, không đoán.
3. Ghi `/tmp/analyses.json` = `{"date":"<hôm nay VN>","analyses":[...]}` rồi
   `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/add_analyses.py /tmp/analyses.json`.
4. **SINH KHÁI NIỆM cho đúng những bài vừa nạp** (thêm 29/07/2026, chỉ thị Huy) — mục 📚 Khái niệm
   gom khái niệm từ CẢ tập trận lẫn think-tank, mà bài viện nghiên cứu mới là chỗ thuật ngữ lạ dày
   nhất. Với mỗi bài vừa nạp, rút **1–3 thuật ngữ** người đọc phổ thông không hiểu ngay (học thuyết,
   cơ chế, hiệp định, khí tài, chiến thuật), viết định nghĩa **tiếng Việt 1–3 câu tự nó đứng được**
   — đọc riêng dòng đó vẫn hiểu, không cần mở bài. Ghi `/tmp/kn-analyses.json`:
   ```
   [{"url":"<url ĐÚNG như vừa nạp>","concepts":[{"term":"...","def":"..."}]}]
   ```
   rồi `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/set_analysis_concepts.py /tmp/kn-analyses.json`.
   - **Bài không có thuật ngữ nào đáng lưu thì BỎ QUA bài đó** — sổ tay là để lọc, nhồi cho đủ số là
     làm hỏng chính tác dụng của nó. Guardrail chặn lô rỗng nên đừng khai `"concepts":[]`, cứ bỏ hẳn
     mục đó ra khỏi mảng.
   - Guardrail CHẶN: url không có trong DATA · thiếu `term`/`def` · `def` dưới 40 ký tự · `term` quá
     90 ký tự · hai `term` trùng nhau trong cùng bài · quá 6 khái niệm/bài. Đọc lỗi rồi sửa JSON.
   - Trùng khái niệm với bài khác hoặc với tập trận thì **KHÔNG sao** — web dùng chung kho
     `dt.concepts` và tự khử trùng theo tên đã bỏ dấu.
   - Kiểm còn bài nào chưa có: `python3 .../set_analysis_concepts.py --kiem`.

### 4.5 — Chủ nhật: báo cáo tuần Mỹ-Trung-Nga
Chỉ khi `TZ='Asia/Ho_Chi_Minh' date +%u` in ra `7`:
```
python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/weekly_context.py --out /tmp/weekly_ctx.json
```
Giao 1 agent **model: "opus"** (BẮT BUỘC Opus): đọc `/tmp/weekly_ctx.json`, viết nhận định tuần 3 nước
(mỗi nước lede + 3–5 luận điểm, mỗi luận điểm 1–3 link nội dòng markdown `[cụm chữ](url-thật-trong-ngữ-liệu)`
— không bịa url). Ghi `/tmp/weekly.json` đúng schema `scripts/add_weekly.py` (thứ tự us→cn→ru, KHÔNG
kèm `generatedAt`) rồi `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/add_weekly.py /tmp/weekly.json`.

### 4.6 — Kết thúc pipeline `event-scan` (LUÔN một trong ba)
- Nạp được: `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/state.py done event-scan "<tóm tắt>"`
- Rỗng: `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/state.py skip event-scan "<lý do>"`
- Lỗi: `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/state.py fail event-scan "<lý do>"` (vẫn push log)

Commit message QUYẾT ĐỊNH email sáng riêng (`notify-morning.yml` bắt tiền tố — KHÁC tiền tố
`Cap nhat ban tin` của Bước 3):
- Có sự kiện/tập trận: `Cap nhat su kien DD/MM: +N su kien/tap tran[, +M bai think-tank][, bao cao tuan]`
- CHỈ báo cáo tuần: `Dang bao cao tuan DD/MM`
- CHỈ think-tank: vẫn `Cap nhat su kien DD/MM: +M bai think-tank` — đã tính vào gate email sáng.
- Rỗng thật: message tự do, KHÔNG dùng 2 tiền tố trên.

`git -C /Users/Huy/Claude/diem-tin-the-gioi add index.html data/ logs/` (phải có `logs/state.json`; **`data/` là BẮT BUỘC** — bài think-tank nằm ở `data/analyses.json` từ 30/07/2026, bỏ sót thì bài nạp xong KHÔNG lên web mà cũng không có lỗi nào) → commit
**RIÊNG với commit bản tin của Bước 3** → push. Bị từ chối → `pull --rebase` rồi push lại.

Báo cáo cuối (gộp vào báo cáo cuối chung của phiên): số sự kiện mới/cập nhật, số tập trận cập nhật, có
báo cáo tuần không (nếu CN), trạng thái push của CẢ HAI commit (bản tin + sự kiện).

## PHIÊN TỐI — BỐI CẢNH RIÊNG (task `web-scan-diem-tin-toi`)

Phần này chỉ áp cho phiên chạy ở mốc TỐI (dời nguyên văn từ stub task `web-scan-diem-tin-toi` ngày 27/07/2026):

1. **Task tối là mốc LOCAL 21:15 của phiên TỐI.** Chuỗi phiên tối: CI GitHub 20:47 → **local 21:15** → CI 21:47 (lưới vét đã trễ hạn). Task `web-scan-diem-tin` lo phiên SÁNG SỚM (04:30/05:30), không đụng tới phiên tối.

2. **HẠN CHÓT CỨNG: email bản tin tối phải tới hộp thư MUỘN NHẤT 22:00** (chỉ thị Huy 27/07/2026). Mốc local 21:15 là **lớp cuối cùng còn kịp hạn** — mốc CI 21:47 sau đó chạy xong thì email đã ~22:10, tức đã trễ. Đừng ỷ vào nó.
   - Quét mất ~20 phút (đo thật: CI 26/07 hết 20m45s, local 27/07 hết 16'), email gửi ~20 giây sau commit.
   - Mốc 21:15 cho biên ~15 phút phòng lúc fire trễ. Lý do có biên này: tối 26/07 mốc local 21:30 mãi 21:41 mới `claim` xong (jitter + khởi động session + `git pull --rebase` timeout 2 phút) — trễ 11 phút chứ không phải 3,5 phút jitter.
   - **Quá 21:45 mà chưa nạp xong thì CHỐT lô đang có**: chạy `add_news.py` với những tin đã gom được, ghi phần thiếu vào `logs/scan-gaps.json`, commit + push NGAY. Thà 3 tin sạch gửi lúc 21:50 còn hơn 8 tin gửi lúc 22:20.
   - Vì vậy: quét gọn, KHÔNG vòng bổ sung lần 3-4 để gom cho đủ chỉ tiêu, KHÔNG đi tìm thêm khi đã có tin dùng được.

3. **`claim` trả SKIP thì dừng hẳn ngay** (exit 10 = CI 20:47 đã xong, exit 11 = CI đang chạy): ghi 1 dòng SKIP vào `logs/scan-<ngày VN>.log`, commit + push log, KẾT THÚC. Không gắn Monitor, không chờ, không điều tra thêm.

   ⛔ **NGOẠI LỆ DUY NHẤT của điều 3 — exit 10 mà SỔ ĐÃ GỬI CHƯA CÓ DÒNG CỦA CA NÀY** (đúc 29/07/2026, sự cố thật). Trước khi SKIP êm ở **mốc LOCAL 21:15** (lớp cuối còn kịp hạn), đọc `logs/da-gui-email.json` và soi dòng cuối cùng có `buoi == "toi"`:
   | Sổ có dòng `toi` ngày hôm nay | Làm gì |
   |---|---|
   | **CÓ** | SKIP êm theo đúng điều 3. Bản tin đã tới tay, không quét lại |
   | **KHÔNG** | Cờ `lastSuccess` đang NÓI DỐI → **QUÉT THẬT**, commit tiền tố `Cap nhat ban tin` như thường |

   **Cơ chế gây vấp:** `state.py` chỉ ghi nhận *"pipeline đã chạy xong"*, nó **không biết bản tin có được GỬI hay không** — hai chuyện khác nhau. Tối 29/07 một **phiên TEST hạ tầng CI** (`MODE=test`, quét nhẹ 1 agent, nạp đúng +1 tin) chạy lúc **17:34** và gọi `state.py done web-scan`, chiếm luôn ô `toi` của ngày. Commit của nó rơi **ngoài khung giờ gửi** (cổng 2 của `notify-email.yml` đòi ≥20:30) nên không kích email/Telegram. Hậu quả dây chuyền: CI (khi đó 21:00, nay 20:47) → exit 10 SKIP · local 21:15 → exit 10 SKIP · CI vét → cũng sẽ SKIP. **Cả bốn lớp im lặng, không lớp nào hỏng, mà bản tin tối mất trắng.** Canary 22:45 có kêu nhưng lúc đó đã quá hạn 22:00.

   ⛔ **NHƯNG SỔ TRỐNG CÓ HAI NGHĨA — phiên LOCAL phải đọc log run CI trước khi kết luận** (đúc
   30/07/2026, sự cố thật ở phiên SÁNG SỚM; **áp cho CẢ hai phiên**, không riêng phiên tối):
   | Sổ trống vì | Dấu hiệu | Làm gì |
   |---|---|---|
   | Bản tin **thật sự chưa gửi** | không có run `notify-email.yml` nào, hoặc run ĐỎ | QUÉT THẬT theo bảng trên |
   | **Khâu GHI SỔ hỏng**, bản tin ĐÃ tới tay | run `notify-email.yml` XANH + log có dòng `Đã gửi … file .docx tới <chat>` | **KHÔNG quét lại.** Ghi bù sổ bằng `python3 .github/scripts/so_da_gui.py --ghi --buoi sang\|toi` rồi commit |

   ✅ **VÁ GỐC — ĐÃ LÀM 30/07/2026.** Luật hợp nhất sổ dời vào **`.github/scripts/ghi_so_push.py`**
   (dùng chung cho cả hai workflow): sổ là dữ liệu **append-only** nên không `pull --rebase` nữa mà
   *lấy sổ mới nhất của remote rồi ghi lại dòng của mình*, thử lại trên đỉnh mới nếu bị chen ⇒ không
   còn xung đột để mà hỏng. Chi tiết + 04 cái bẫy kèm theo: mục "🔀 HAI WORKFLOW GHI CÙNG SỔ" trong
   `CLAUDE.md`. Bộ test canh `tests/test-ghi-so-push.py` (10 ca · `--tu-kiem` bắt 6/6 bản hỏng, riêng
   bản hỏng "dùng lại `pull --rebase`" làm 6/10 ca đỏ), đã nạp vào `khoe.py`.
   ⚠️ **NHƯNG BẢNG KIỂM Ở TRÊN VẪN CẦN, ĐỪNG GỠ** — cùng lý do với cổng phiên test: vá gốc chỉ bịt
   đường *race giữa hai workflow*, còn các ca khác làm sổ trống (workflow bị huỷ giữa bước ghi, mất
   mạng cả 5 vòng, người bấm tay gửi bù) thì phép đọc `gh run list` vẫn là thứ duy nhất phân biệt được
   "chưa gửi thật" với "khâu ghi sổ hỏng".

   **Cơ chế gây vấp:** sáng 30/07 bước *"Ghi sổ đã gửi"* của `notify-email.yml` rebase hỏng
   (`could not apply … (sang)`) vì `notify-morning.yml` ghi cùng file `logs/da-gui-email.json`
   **trước đó 7 giây** — hệ quả dây chuyền của việc gộp `event-scan` vào cùng session sáng
   (28/07). Bản tin đã gửi lúc 04:28 mà sổ trống, nên: canary ca `sang` kêu oan và nhắn Telegram,
   còn hai phiên CI dự phòng (05:00 · 05:37) kết luận "mất bản tin" rồi chạy lại vòng quét bổ sung
   tốn token. Chúng không sai về lập luận — chúng **không đọc được `gh run list`** (bị chặn
   *requires approval* trong CI) nên thiếu đúng mảnh bằng chứng quyết định.

   ⇒ **Phiên LOCAL chạy trên máy Huy GỌI ĐƯỢC `gh`, đó là lợi thế phải dùng**, đừng bỏ qua rồi
   suy đoán như phiên CI:
   ```
   gh run list -R huyneo1101-dotcom/diem-tin-the-gioi --workflow notify-email.yml --limit 2 --json databaseId,createdAt,conclusion --jq '.[] | [.databaseId, .createdAt, .conclusion] | @tsv'
   gh run view <id> -R huyneo1101-dotcom/diem-tin-the-gioi --log | grep -iE 'Da gui|GUI_EMAIL|khong push duoc so'
   ```
   ⚠️ **`Đã gửi 0 message + file .docx` là BÌNH THƯỜNG, không phải hỏng** — `msgs=[]` trong
   `send_telegram.py` là cố ý (chỉ thị Huy 27/07: *"chỉ gửi file word thôi"*). Thấy `0 message`
   rồi kết luận kênh câm là đọc nhầm; bằng chứng gửi được nằm ở cụm `+ file .docx tới <chat>`.

   Vì sao phải kiểm bằng SỔ chứ không bằng `state.json`: sổ đã gửi được ghi ở **bước CUỐI sau khi đã gửi xong mọi kênh**, nên nó là dấu vết việc-đã-làm; còn `lastSuccess` chỉ là lời tự khai của một phiên. Đây đúng nguyên tắc số 1 của canary — **kiểm ĐẦU RA, không kiểm quy trình** — nay áp luôn cho chính phiên quét.

   ⛔ **KHÔNG sửa `logs/state.json` để lách.** `--force` chỉ cướp khoá `RUNNING`, không bỏ qua cờ đã-xong, và đó là **đúng thiết kế** — đừng thêm cờ mới. Không cần sửa gì cả: cổng gửi của `notify-email.yml` xét **commit message + khung giờ VN**, hoàn toàn không xét khoá, nên cứ quét rồi commit là email/Telegram vẫn đi. Mốc CI vét (21:47) sau đó vẫn thấy exit 10 và SKIP nên **không có nguy cơ quét chồng** (exit 10 khác exit 11: 10 = đã xong, 11 = đang chạy — chỉ 11 mới là dấu hiệu có phiên sống).

   ⚠️ **Ghi rõ vào `scan-gaps.json` (mục `note`) và vào log** rằng phiên này quét đè lên cờ đã-xong, kèm lý do — để người đọc sau không tưởng có hai phiên tranh nhau.

   ✅ **Vá gốc — ĐÃ LÀM 29/07/2026.** Nhánh `MODE=test` của `claude-web-scan.yml` nay chạy với biến môi trường **`DIEMTIN_PHIEN_TEST=1`** (đặt ở tầng `env:` của step quét, nên `claude -p` và mọi lệnh Bash con đều thừa hưởng — cơ chế, không phải lời hứa trong prompt). `state.py` thấy biến đó thì chuyển toàn bộ đường ghi sang `logs/state-test.json` (đã `.gitignore`): phiên test vẫn nghiệm thu được trọn pipeline `claim → beat → done`, chỉ là ghi vào sổ riêng, **không chiếm được ô khoá thật**. Nó vẫn đọc `logs/state.json` để nhường phiên THẬT đang chạy (exit 11), và **không bao giờ exit 10** vì cờ thật đã xong — test phải chạy lại được bất kể giờ nào. Ý định khai bằng lời, không suy từ `MODE`/tên workflow: mặc định là phiên THẬT, quên đặt biến thì hành vi y như cũ chứ không tạo vùng câm mới (cùng bài học với `tu_dong=1` và `TELEGRAM_BAT_BUOC`). Bộ test canh: `tests/test-cong-phien-test.py` (11 ca, 5 bản hỏng đều bị `--tu-kiem` bắt).

   ⚠️ **Nhưng ngoại lệ ở trên VẪN CẦN, đừng gỡ.** Vá gốc chỉ bịt đường `MODE=test`; đường **bấm tay `workflow_dispatch` mode=normal giữa ngày** thì vẫn `done` và chiếm ô khoá đúng như cũ, trong khi commit của nó rơi ngoài khung giờ gửi nên không kích email. Phép kiểm sổ là thứ duy nhất bắt được ca đó.

   🔁 **Từ 29/07/2026 phép kiểm này áp cho CẢ PHIÊN CI** (`.github/prompts/web-scan-ci.md` BƯỚC 1) — vì mốc **CI vét 21:47 là lớp CUỐI**, máy Mac ngủ thì không còn ai đứng sau nó. Bản CI có thêm một chốt chống kêu oan mà bản local không cần: **`lastRunAt` cách hiện tại < 20 phút thì cứ SKIP êm** — phiên anh em vừa xong, `notify-email.yml` còn đang chạy, mà sổ chỉ được ghi ở bước CUỐI nên chưa kịp hiện. Bản local 21:15 không dính ca này vì lúc đó CI 20:47 còn `RUNNING` (exit 11, không phải 10).

4. Ghi log dùng chữ **"phien toi"**. Giờ VN lúc chạy là 21:15 nên `state.py` tự chọn ô `toi`, không cần truyền gì thêm.
