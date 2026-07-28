# Routine WEB-SCAN — bản tin 5 chủ đề (NGUỒN SỰ THẬT DUY NHẤT)

> **File này là nguồn sự thật duy nhất về quy trình quét bản tin cho CẢ HAI phiên** (sáng sớm + tối).
> Dời từ `~/.claude/scheduled-tasks/web-scan-diem-tin/SKILL.md` vào repo ngày 27/07/2026 — vùng `~/.claude/` là sensitive, mọi Edit vào đó đều bị hỏi quyền bất kể allowlist, trong khi file này rất hay phải vá bài học mới. Repo thì Edit/Write đã allow toàn phần + có git history.
> **Ai đọc file này:** task local `web-scan-diem-tin` (phiên SÁNG SỚM 04:30/05:30) và task local `web-scan-diem-tin-toi` (phiên TỐI 21:15) — SKILL.md của 2 task đó giờ chỉ là stub trỏ về đây. **Sửa quy trình thì sửa file này**, đừng sửa stub.

Quét tin và xuất bản bản tin cho web "Điểm Tin Thế Giới" (https://huyneo1101-dotcom.github.io/diem-tin-the-gioi).
Repo: /Users/Huy/Claude/diem-tin-the-gioi (git remote SSH, push thẳng nhánh `main`).

Bản tin 2 phiên/ngày cùng playbook 5 chủ đề: TỐI (ô khoá `toi`) + SÁNG SỚM (ô khoá `sang`), cả hai đều gửi email + file Word.

⚠️ **PHÂN VAI: quy trình dưới đây là CHUNG cho cả hai phiên; mày là phiên nào thì xem stub task đã giao mày việc.** Task `web-scan-diem-tin` lo phiên SÁNG SỚM; task `web-scan-diem-tin-toi` lo phiên TỐI (tách 27/07/2026 vì phiên tối có hạn chót email cứng, cần fire sớm hơn để có biên; một task chỉ nhận một biểu thức cron nên phải tách). Cả hai task **KHÔNG chép lại quy trình** mà cùng Read file này — để hai phiên không bao giờ lệch nhau. Phiên TỐI có thêm mục "PHIÊN TỐI — BỐI CẢNH RIÊNG" ở cuối file.

| Phiên | CI chính | local | CI dự phòng | local lưới cuối | Ai chạy phần local |
|---|---|---|---|---|---|
| SÁNG SỚM | **04:00** VN | **04:30** | 05:00 | 05:30 | task `web-scan-diem-tin` |
| TỐI | 21:00 VN | 21:15 ← lớp cuối trong hạn | 22:00 = lớp VÉT đã trễ | — | task `web-scan-diem-tin-toi` |

Nguyên nhân dời CI sáng: mốc CI 04:30 cũ **không nổ** sáng 27/07 (GitHub hay trễ/bỏ cron lúc tải cao) mà phiên sáng khi đó không có lưới local → mất trắng bản tin sáng. Giờ CI lên 04:00 để local 04:30 kịp gánh.

⏰ **PHIÊN TỐI CÓ HẠN CHÓT CỨNG: email muộn nhất 22:00** (chỉ thị Huy 27/07/2026): phiên chạy ở mốc tối **quá 21:45 chưa nạp xong thì chốt lô đang có**, `add_news.py` + commit ngay, phần thiếu ghi `scan-gaps.json`; không vòng bổ sung lần 3-4 để gom cho đủ chỉ tiêu. **Phiên SÁNG SỚM KHÔNG có hạn chót này** — cứ quét đủ 5 chủ đề bình thường. Chi tiết phiên tối: mục cuối file.

Cách làm ở MỌI mốc là như nhau: cứ `claim` như thường — CI đã xong/đang chạy thì SKIP êm, CI không quét (trễ/chết/hết quota) thì mày quét đủ 5 chủ đề rồi commit `Cap nhat ban tin ...` (email + .docx do Action `notify-email.yml` tự gửi khi thấy push `index.html` với tiền tố commit đó — local push cũng kích như CI, không phải làm gì thêm). Phiên sáng 10:15 kiểu cũ vẫn bỏ.
⚠️ Local chỉ chạy khi app Claude đang mở và máy đã thức — mốc 04:30 phụ thuộc lịch wake của máy (`pmset repeat wakeorpoweron`); máy ngủ thì mốc này im, đó là lý do vẫn giữ CI 04:00/05:00 làm mốc chính.

PHẠM VI (chỉ thị Huy 2026-07-23): mỗi phiên CHỈ quét 5 CHỦ ĐỀ, mỗi chủ đề 5–10 bài, khung 24 GIỜ gần nhất (nới 48h nếu chủ đề đó thiếu <5 bài):
⛔ **"Nới 48h" = HÔM NAY + HÔM QUA, KHÔNG phải lùi 2 ngày lịch** (chỉ thị Huy 27/07/2026: *"quét tin ngày 26 thì chỉ được lấy tin tối đa là ngày 25, không được phép lấy tin ngày 24"*). Giao prompt agent thì **ghi thẳng 2 ngày cụ thể** thay vì chữ "48h" — agent hay hiểu thành lùi 2 ngày. Tin cũ hơn: BỎ, ghi `logs/loai-tin.md` + lý do vào `scan-gaps.json`, thà chủ đề về 0. `add_news.py` cũng chặn cứng (kiểm ngày 2 lớp: so batch VÀ so hôm nay giờ VN) nên nhận về cũng không nạp được; gặp lỗi "cũ hơn 1 ngày so với HÔM NAY" thì bỏ tin, ĐỪNG lùi ngày batch để lách.
1. Nội bộ Mỹ — **5 NHÓM, HAI HẠNG ƯU TIÊN (chỉ thị Huy 27/07/2026, GHI ĐÈ mức "SIẾT" cũ). BẮT BUỘC vét cạn nhóm (1) TRƯỚC; chưa đủ chỉ tiêu mới lấy sang các nhóm còn lại, và (2)(3)(4)(5) NGANG HÀNG NHAU:** (1) TOÀN BỘ phiên điều trần trong ngày + TOÀN BỘ kết quả bỏ phiếu thông qua dự luật; (2) sáng kiến + chiến lược của chính quyền Trump trên kênh chính thống các bộ (sắc lệnh, memorandum, chiến lược quốc gia, fact sheet, thông cáo bộ); (3) diễn biến biểu tình/tuần hành; (4) hoạt động kinh tế Mỹ + hoạt động khác của các bộ và Nhà Trắng (Trump + bộ sậu action); (5) **BẦU CỬ** — bầu cử giữa nhiệm kỳ/sơ bộ, tranh cử, thăm dò, quy định cử tri, kiểm phiếu, redistricting/gerrymander, đua ghế Thượng viện/Hạ viện/thống đốc (tách riêng 27/07/2026, trước gộp chung nhóm 3). → usNews, category Chính trị (nhóm 4 có thể Kinh tế). Nhóm 3-4-5 ĐẢO lại phần cấm cũ, nhưng phải là chuyện NỘI BỘ MỸ — từ khoá chung như protest/tariff/election phải kèm ngữ cảnh Mỹ. Số nhóm 2→5 là NHÃN, không phải thứ tự.
2. Úc & Biển Đông — AUKUS/QP Úc (region Ấn Độ Dương - Thái Bình Dương) + chủ quyền/tuần tra/tập trận Biển Đông (region Đông Á). **MỞ RỘNG 27/07/2026: tìm thêm tin CÁC NƯỚC KHÁC quanh Biển Đông** — Malaysia, Indonesia, Brunei, Đài Loan, Việt Nam, đàm phán COC ASEAN-Trung Quốc, các thực thể Natuna/Bãi Tư Chính/Luconia/Bãi Cỏ Rong. → worldNews.
⛔ **Nhật/Ấn/Hàn CHỈ tính khi hoạt động TẠI vùng biển này — quốc phòng NỘI BỘ của họ KHÔNG thuộc chủ đề** (siết 28/07/2026, Huy bắt lỗi): tối 28/07 lọt tin "Hàn Quốc luật hoá cam kết phi hạt nhân để thúc đẩy dự án tàu ngầm hạt nhân" (Korea Herald) — thuần luật NPT + chương trình tàu ngầm trong nước Hàn, không một chữ Biển Đông. **Chuẩn nhận: tin phải neo được vào một QUỐC GIA ven Biển Đông hoặc chính VÙNG BIỂN đó, không phải neo vào loại khí tài.** Cửa lọt ở `scripts/topics.py`: từ khoá `"nuclear submarine"` để trần khớp mọi nước có tàu ngầm hạt nhân — đã bỏ, vì tin AUKUS thật luôn có `aukus`/`australia` (cùng bẫy với `"scarborough"` trần khớp thị trấn Scarborough).
3. CNQS Mỹ — khí tài/hệ thống cụ thể (tên lửa, phòng không, hải quân, không gian, laser, drone). → usNews, category Công nghệ quân sự. ⏳ **KHUNG NGÀY NỚI RIÊNG: lùi tới 3 ngày** (quét 27 thì lấy được tới 24); 4 chủ đề còn lại vẫn chỉ hôm nay + hôm qua. add_news.py áp theo category nên phải đặt đúng `"category":"Công nghệ quân sự"`.
4. Mỹ–Mali — Mỹ cân nhắc/không kích JNIM ở Sahel (gắn Mali/JNIM/Bamako/Sahel). → usNews, dossier 🟤 Mỹ – Mali.
5. Tập trận Predator's Run 2026 (Mỹ–Úc–Philippines, tới ~29/7) → cập nhật qua exerciseUpdates (tên khớp "Predator's Run 2026 (tập trận Mỹ - Úc - Philippines)").
BỎ khỏi phạm vi: Kinh tế, Ngoại giao chung, xNews, các vùng thế giới khác, tạo mới dipEvents, và sàn 15+15. Báo Mới: vẫn quét nhưng CHỈ giữ bài hợp 5 chủ đề.

KHÔNG dùng `cd` (gây prompt xin quyền, routine chạy lúc 22:00 khi Huy không có mặt). Mọi lệnh dùng ĐƯỜNG DẪN TUYỆT ĐỐI: script là `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/<x>.py` (script tự tìm repo root từ `__file__`, không cần đứng trong repo), git là `git -C /Users/Huy/Claude/diem-tin-the-gioi ...`. Ghi log dùng tool Edit/Write vào `/Users/Huy/Claude/diem-tin-the-gioi/logs/scan-<ngày VN>.log` thay vì `cat >>`.
⚠️ **MỌI LỆNH BASH PHẢI PHẲNG — KHÔNG WRAPPER, KHÔNG BIẾN, KHÔNG VÒNG LẶP** (sự cố 25–26/07/2026: routine treo chờ bấm nút 3 lần vì 3 kiểu lệnh "fancy"). Harness soi CÚ PHÁP lệnh: hễ chứa hàm/brace (`cd() { ... };` — flag "expansion obfuscation"), biến shell hay `$(...)` (`$NGAY`, `$f` — flag "simple_expansion"), hay `for ... do ... done`/heredoc, là nó BỎ QUA ALLOWLIST và bật prompt xin quyền — DÙ lệnh bên trong hợp lệ. Quy tắc áp cho MỌI lệnh trong phiên, kể cả lệnh chẩn đoán tuỳ hứng (ps, grep transcript...):
- Chỉ dùng lệnh PHẲNG: một lệnh đơn, pipe (`|`), hoặc chuỗi `&&` của lệnh đơn — đối số là GIÁ TRỊ THẬT, gõ đầy đủ.
- Cần ngày/giờ: chạy riêng `TZ='Asia/Ho_Chi_Minh' date +%F` / `date -u +%H:%MZ` rồi điền literal vào lệnh sau.
- Cần lặp nhiều file: viết N lệnh rời (ví dụ 2 dòng `grep -c 'x' <path đầy đủ>` thay vì `for f in ...; do grep $f; done` — chính vụ 26/07: dạng rời khớp `Bash(grep *)` chạy thẳng, dạng for bị treo).
- Lặp phức tạp hơn: gói vào `python3 -c '...'` (đã allowlist) thay vì bash script.
- "Không dùng cd" = ĐỪNG GỌI `cd`, KHÔNG phải vô hiệu hoá nó bằng hàm chắn.
- 🔒 Từ 27/07/2026 quy tắc này được **hook cưỡng bức**: `/Users/Huy/.claude/hooks/block-lenh-khong-phang.py` chặn thẳng lệnh có hàm/brace/`for`/heredoc/`$VAR`/`$(...)`/backtick trong phiên scheduled-task. Bị chặn thì **viết lại lệnh cho phẳng, KHÔNG xin quyền cho lệnh cũ**. Nội dung trong nháy ĐƠN được bỏ qua nên `python3 -c '...'` và `awk '{print $1}'` vẫn chạy bình thường.
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
⚠️ **PUSH `logs/state.json` NGAY SAU KHI CLAIM — TRƯỚC khi làm baseline** (sự cố 26/07/2026, phiên local
21:30): khoá `state.py` đồng bộ QUA GIT, nên phiên nào chưa push khoá thì phiên kia pull về vẫn thấy
"không ai giữ khoá" và claim tiếp. Local claim 21:41 nhưng để dành push tới cuối bước log → CI pull lúc
22:09 không thấy khoá → **hai phiên cùng quét**, local phải bỏ hết công baseline để nhường. Push khoá
ngay là cách duy nhất để phiên kia nhìn thấy.
⚠️ **Trước khi chạy `add_news.py`, `pull --rebase` rồi ĐỌC LẠI `logs/state.json` xem mình còn giữ khoá
không.** Thấy `lastRunAt`/`heartbeat` của phiên khác mới hơn mình → phiên kia đã cướp khoá: DỪNG, ghi
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
GIỮ NHỊP TIM: sau mỗi mốc lớn (xong baseline · xong agent · xong script) chạy `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/state.py beat web-scan` + ghi checkpoint log + push. Khoá hết hạn sau 30' không nhịp.
⏱️ **BEAT TRƯỚC KHI LÀM VIỆC LÂU, KHÔNG PHẢI SAU KHI XONG** (vá 28/07/2026, đo thật trên CI): "sau mỗi mốc lớn" nghe thì đủ nhưng thực tế nhịp ĐẦU TIÊN chỉ tới khi vòng agent xong — mà đó là chặng dài nhất phiên. Phiên tối CI 28/07: start 21:00 → beat đầu **21:26**, tức 25' không nhịp, cách ngưỡng thối 30' đúng **5 phút**. Agent chậm thêm 5' nữa là khoá tự mở TRONG LÚC phiên vẫn đang quét, mốc kế cướp khoá → **hai phiên cùng quét**, đúng sự cố 26/07. Vì vậy beat thêm ở **(a) ngay sau `harvest.py` + `telegram_harvest.py`** và **(b) ngay TRƯỚC khi giao lô agent**; nguyên tắc chung: **hai nhịp liên tiếp không cách quá ~15 phút**.
Ràng buộc cứng: KHÔNG dùng Read đọc cả index.html; mọi thao tác chèn tin qua `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/add_news.py /tmp/new_items.json`; khung 24h (nới 48h nếu thiếu); được trả mảng rỗng, KHÔNG bịa tin/link.

## Bước 3 — Kết thúc (LUÔN gọi 1 trong 3)
- Nạp được tin: `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/state.py done web-scan "<tóm tắt số tin mỗi chủ đề>"`
- Lô rỗng: `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/state.py skip web-scan "<lý do>"`
- Lỗi giữa chừng: `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/state.py fail web-scan "<lý do>"` rồi VẪN ghi log + push
**TRƯỚC KHI COMMIT — BẮT BUỘC ghi `logs/loai-tin.json`** (chỉ thị Huy 28/07/2026: *"mỗi khi gửi hãy gửi thêm 1 file word nữa, trong đó gồm các tin đã bị loại dù thuộc đúng 5 chủ đề. ghi rõ lý do bị loại"*). Đây là nguồn CHÍNH của file Word thứ hai `Diem-tin-BI-LOAI-<buổi>-<ngày>.docx`. Cấu trúc + quy tắc viết `reason`: xem **Bước 3** trong `.claude/skills/quet-tin/SKILL.md`. `date` PHẢI khớp `DATA.generatedAt`, lệch là bị bỏ và rơi xuống fallback trích `loai-tin.md` (mất chủ đề + link). Không loại tin nào thì ghi `items: []`.

**TRƯỚC KHI COMMIT — BẮT BUỘC ghi `logs/scan-gaps.json`** (chỉ thị Huy 25/07/2026: email phải ghi cả **chủ đề thiếu VÀ lý do**). Lý do thiếu là kiến thức của phiên quét, Action không tự suy ra được → không ghi file thì email MẤT mục này. Dùng tool Write, liệt kê đủ 5 chủ đề (+ Báo Mới), mỗi chủ đề `{name, count, target, min, thieu, reason}`; `date` của file **PHẢI khớp `DATA.generatedAt`** (nạp nhiều lô thì lấy ngày lô chạy CUỐI) — lệch là `send-email.js` bỏ cả mục để không gửi lý do hôm trước. Mẫu JSON đầy đủ + quy tắc viết `reason`: xem **Bước 4b** trong `.claude/skills/quet-tin/SKILL.md`.

`git -C /Users/Huy/Claude/diem-tin-the-gioi add index.html logs/` (phải có logs/state.json VÀ logs/scan-gaps.json VÀ logs/loai-tin.json), commit mẫu `Cap nhat ban tin DD/MM: +N tin (5 chu de)`, push `main` — đều qua `git -C /Users/Huy/Claude/diem-tin-the-gioi ...`. Push bị từ chối → `git -C ... pull --rebase origin main` rồi push lại; nếu pull báo unstaged changes ở file KHÔNG thuộc lô này thì cứ push, đừng commit hộ file lạ.
Email + file Word tự gửi lamgiaphat1603@gmail.com qua GitHub Action notify-email khi có commit `Cap nhat ban tin` — skill không cần làm gì thêm NGOÀI việc ghi `logs/scan-gaps.json` ở trên.

Báo cáo cuối ngắn gọn: số tin mỗi chủ đề (Nội bộ Mỹ / Úc-Biển Đông / CNQS Mỹ / Mali / Predator), chủ đề nào thiếu (đã nới 48h chưa), trạng thái push.

## PHIÊN TỐI — BỐI CẢNH RIÊNG (task `web-scan-diem-tin-toi`)

Phần này chỉ áp cho phiên chạy ở mốc TỐI (dời nguyên văn từ stub task `web-scan-diem-tin-toi` ngày 27/07/2026):

1. **Task tối là mốc LOCAL 21:15 của phiên TỐI.** Chuỗi phiên tối: CI GitHub 21:00 → **local 21:15** → CI 22:00 (lưới vét đã trễ hạn). Task `web-scan-diem-tin` lo phiên SÁNG SỚM (04:30/05:30), không đụng tới phiên tối.

2. **HẠN CHÓT CỨNG: email bản tin tối phải tới hộp thư MUỘN NHẤT 22:00** (chỉ thị Huy 27/07/2026). Mốc local 21:15 là **lớp cuối cùng còn kịp hạn** — mốc CI 22:00 sau đó chạy xong thì email đã ~22:22, tức đã trễ. Đừng ỷ vào nó.
   - Quét mất ~20 phút (đo thật: CI 26/07 hết 20m45s, local 27/07 hết 16'), email gửi ~20 giây sau commit.
   - Mốc 21:15 cho biên ~15 phút phòng lúc fire trễ. Lý do có biên này: tối 26/07 mốc local 21:30 mãi 21:41 mới `claim` xong (jitter + khởi động session + `git pull --rebase` timeout 2 phút) — trễ 11 phút chứ không phải 3,5 phút jitter.
   - **Quá 21:45 mà chưa nạp xong thì CHỐT lô đang có**: chạy `add_news.py` với những tin đã gom được, ghi phần thiếu vào `logs/scan-gaps.json`, commit + push NGAY. Thà 3 tin sạch gửi lúc 21:50 còn hơn 8 tin gửi lúc 22:20.
   - Vì vậy: quét gọn, KHÔNG vòng bổ sung lần 3-4 để gom cho đủ chỉ tiêu, KHÔNG đi tìm thêm khi đã có tin dùng được.

3. **`claim` trả SKIP thì dừng hẳn ngay** (exit 10 = CI 21:00 đã xong, exit 11 = CI đang chạy): ghi 1 dòng SKIP vào `logs/scan-<ngày VN>.log`, commit + push log, KẾT THÚC. Không gắn Monitor, không chờ, không điều tra thêm.

4. Ghi log dùng chữ **"phien toi"**. Giờ VN lúc chạy là 21:15 nên `state.py` tự chọn ô `toi`, không cần truyền gì thêm.
