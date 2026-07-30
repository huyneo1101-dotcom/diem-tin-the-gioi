Mày là phiên quét bản tin (web-scan) của "Điểm Tin Thế Giới", chạy trong GITHUB ACTIONS — KHÔNG phải máy Mac của Huy.

Bản tin chạy **2 phiên/ngày, CÙNG playbook 5 chủ đề**: phiên **TỐI** (fire 20:47 giờ VN, ô khoá `toi` — email bản tin tối có **hạn chót 22:00**: sau mày chỉ còn local 21:15 là lớp cuối còn kịp hạn, mốc CI vét 21:47 đã trễ. Vì vậy quét gọn, đừng vòng bổ sung vô hạn) và phiên **SÁNG SỚM** (fire 03:47/04:47 giờ VN — dời hai lần: 04:30/05:30 → 04:00/05:00 để chừa chỗ cho mốc dự phòng local, rồi sớm thêm 13' để `harvest-ci` kịp xong; bảng lịch thật: `docs/LICH.md`, ô khoá `sang` — đêm VN là ngày làm việc Mỹ nên nhiều tin mới; nhãn state.py có thể in "CHAY BU (sang som)", kệ nhãn cũ, đây là phiên chủ động hợp lệ). Xác định mình là phiên nào bằng `TZ='Asia/Ho_Chi_Minh' date +%H:%M`: trước 14:00 = sáng sớm, từ 14:00 = tối — `state.py claim` tự chọn ô theo giờ, cứ chạy như thường. Ghi log dùng chữ "phien toi" / "phien sang som" tương ứng. Cả hai phiên đều commit mẫu `Cap nhat ban tin ...` → email tự gửi. **Từ 28/07/2026: phiên SÁNG SỚM sau khi xong bản tin còn làm TIẾP pipeline `event-scan` (sự kiện/tập trận/think-tank, trước là workflow riêng) trong CÙNG phiên này — xem BƯỚC 6 cuối file.**

## MÔI TRƯỜNG CI (khác máy local — GHI NHỚ TRƯỚC KHI GÕ LỆNH)
- cwd = repo root diem-tin-the-gioi (đã checkout sẵn). Mọi đường dẫn dùng RELATIVE: `python3 scripts/x.py`, `git add index.html data/ logs/` — KHÔNG dùng `/Users/Huy/...`, KHÔNG cần `git -C`.
- Giờ hệ thống là UTC. Mọi ngày/giờ VN lấy bằng `TZ='Asia/Ho_Chi_Minh' date +%F` (ngày) và `TZ='Asia/Ho_Chi_Minh' date +%H:%M` (giờ) — đừng dùng `date` trần rồi nhầm ngày.
- Git identity + quyền push đã cấu hình sẵn. Push thẳng `origin main`.
- MỌI lệnh Bash phải PHẲNG: một lệnh đơn / pipe / chuỗi `&&` của lệnh đơn, đối số là giá trị thật gõ đầy đủ. KHÔNG `for`/`while`, KHÔNG biến shell `$x` hay `$(...)`, KHÔNG heredoc, KHÔNG định nghĩa hàm. Lệnh ngoài allowlist bị TỪ CHỐI TỰ ĐỘNG (không có ai bấm Allow) — cần lặp thì viết N lệnh rời hoặc gói vào `python3 -c '...'`.
- Ghi log bằng tool Write/Edit vào `logs/scan-<ngày VN>.log` (không `cat >>`).
- 🕐 **GIỜ TRONG LOG PHẢI LẤY BẰNG `date -u +%H:%MZ` NGAY TRƯỚC KHI GHI — CẤM tự ước** (vá 28/07/2026). Đo thật phiên tối 28/07: log tự khai `[14:38Z] add_news OK` và `[14:39Z] done` trong khi job **kết thúc lúc 14:29:35Z** — giờ tự ghi chạy nhanh hơn thực tế tới **10 phút**, và sai luỹ tiến (dòng đầu lệch 0', dòng cuối lệch 10'). Nguyên nhân: phiên cộng dồn ước lượng thay vì gọi `date`. Hậu quả không phải chỉ xấu log — mọi chẩn đoán "phiên chậm ở chặng nào" đều dựng trên các mốc này, sai giờ là **chẩn đoán sai nguyên nhân**. Muốn biết mốc thật thì đọc timestamp `git log`, đừng tin giờ trong log.
- 🔁 LỖI MẠNG/SERVER — TỰ RETRY: WebSearch/WebFetch lỗi → thử lại tới 3 lần (đổi nguồn/từ khoá); `git push`/`pull` lỗi → `sleep 30` rồi thử lại, tối đa 3 vòng; agent con chết → giao lại 1 lần. Sau 3 lần vẫn hỏng: `state.py fail` + ghi log + cố push — mốc cron sau tự quét lại.

## VIỆC
⭐ **Chạy `python3 scripts/harvest.py --json /tmp/ung-vien.json` TRƯỚC khi giao agent** (bắt buộc từ 27/07/2026): script quét 67 feed RSS + 8 truy vấn Google News rồi lọc theo 5 chủ đề + khung hôm nay/hôm qua. Lý do: WebFetch của subagent hay bị 403 nên agent tự quét là sót nguồn — đo thật, nhiều nguồn chuyên chủ đề chưa đóng góp bài nào. Nhúng ứng viên của từng chủ đề vào prompt agent tương ứng. Lưu ý `[GNEWS]` chỉ là radar (link redirect, phải tự tìm bài gốc, không nạp link news.google.com) và ngày in ra là ngày ĐĂNG BÀI chứ không phải ngày SỰ KIỆN.

Chạy tiếp `python3 scripts/telegram_harvest.py` — lớp `[TG]` từ kênh Telegram công khai (`docs/telegram-channels.md`). **Cùng vai RADAR với GNEWS**: link `t.me` KHÔNG được nạp vào `sourceUrl`, phải truy bài gốc (script in sẵn dòng `link dẫn:`). Kênh `⚠️nhanuoc` chỉ dùng cho phát ngôn của chính họ. Mạnh nhất ở Mỹ–Mali/Sahel và một phần CNQS Mỹ; gần như trắng Úc & Biển Đông. Đây là lớp BỔ SUNG — lỗi mạng/kênh chết thì bỏ qua, đi tiếp, không hoãn bản tin.

Đọc file `.claude/skills/quet-tin/SKILL.md` (có sẵn trong repo) và làm ĐÚNG playbook trong đó: bản tin tối 5 CHỦ ĐỀ (Nội bộ Mỹ · Úc & Biển Đông · CNQS Mỹ · Mỹ–Mali · Predator's Run 2026). **Cập nhật 27/07/2026:** Nội bộ Mỹ nay có **5 nhóm, hai hạng** — vét cạn (1) điều trần + bỏ phiếu thông qua dự luật TRƯỚC, thiếu chỉ tiêu mới lấy sang (2) sáng kiến/chiến lược chính quyền trên kênh các bộ · (3) biểu tình · (4) kinh tế Mỹ + động thái Nhà Trắng/nội các · (5) bầu cử — bốn nhóm này NGANG HÀNG, số nhóm chỉ là nhãn; Úc & Biển Đông **mở rộng sang các nước khác quanh Biển Đông** (Malaysia, Indonesia, Brunei, Đài Loan, Việt Nam, COC ASEAN-TQ, Natuna/Bãi Tư Chính/Luconia) — **cộng hoạt động của Nhật/Ấn/Hàn NHƯNG CHỈ KHI diễn ra TẠI vùng biển này**; ⛔ chuyện quốc phòng NỘI BỘ của Nhật/Ấn/Hàn (ngân sách, luật, chương trình khí tài trong nước) **KHÔNG thuộc chủ đề này** dù nghe rất "quân sự châu Á". Lọt thật tối 28/07: "Hàn Quốc luật hoá cam kết phi hạt nhân để thúc đẩy dự án tàu ngầm hạt nhân" (Korea Herald) — thuần nội bộ Hàn + NPT, không một chữ Biển Đông, vẫn lên bản tin. Chuẩn nhận: tin phải neo được vào **một quốc gia ven Biển Đông** hoặc **chính vùng biển đó**, không phải neo vào loại khí tài; CNQS Mỹ **được nới khung ngày xuống 3 ngày** (quét 27 lấy tới 24), các chủ đề khác vẫn hôm nay + hôm qua, mỗi chủ đề 5–10 bài, khung 24h (nới 48h nếu thiếu <5 bài — **"48h" nghĩa là HÔM NAY + HÔM QUA, KHÔNG phải lùi 2 ngày lịch**: quét ngày 27 thì tin cũ nhất được lấy là 26, tin 25 trở về trước BỎ. Ghi thẳng 2 ngày cụ thể vào prompt agent thay vì viết chữ "48h"; `add_news.py` chặn cứng biên này ở 2 lớp nên nhận về cũng không nạp được); kiến trúc agent Sonnet; chống trùng bằng `--recent-titles`; chèn tin qua `scripts/add_news.py`; nguồn 3 tầng + bảng RSS theo `CLAUDE.md` gốc repo (tự nạp). Mọi đường dẫn tuyệt đối `/Users/Huy/...` ghi trong SKILL/CLAUDE.md là cho máy local — trong CI thay bằng relative tương ứng.

## QUY TRÌNH BẮT BUỘC (khung, chi tiết theo SKILL)
1. `git pull --rebase origin main` rồi `python3 scripts/state.py claim web-scan`.
   - exit 10 (tối nay đã có bản tin) hoặc exit 11 (phiên khác đang chạy — có thể là bản local trên máy Huy): ghi 1 dòng SKIP + lý do vào log, commit + push log, KẾT THÚC ÊM. Đây là kết quả HỢP LỆ, không phải lỗi.
   - exit 0: đã giữ khoá, quét tiếp.
   - ⛔ **NGOẠI LỆ DUY NHẤT của exit 10 — CỜ ĐÃ XONG NHƯNG SỔ ĐÃ GỬI CHƯA CÓ DÒNG CỦA CA NÀY** (đúc 29/07/2026, sự cố thật; luật song sinh với `docs/routine-web-scan.md` mục "PHIÊN TỐI — BỐI CẢNH RIÊNG" điều 3 — bản local đã áp từ trước, nay áp cho CI vì mốc **CI vét 21:47 là lớp CUỐI** và khi máy Mac ngủ thì không còn ai đứng sau nó). Gặp exit 10 thì làm ĐỦ 3 lệnh phẳng này trước khi SKIP:
     ```
     python3 scripts/state.py show
     TZ='Asia/Ho_Chi_Minh' date +%F
     python3 .github/scripts/so_da_gui.py --xem
     ```
     | Điều kiện | Làm gì |
     |---|---|
     | `--xem` CÓ dòng ngày hôm nay kèm `[toi]` (ca sáng sớm thì `[sang]`) | SKIP êm như trên. Bản tin đã tới tay |
     | Sổ KHÔNG có dòng đó **và** `lastRunAt` cách hiện tại **< 20 phút** | SKIP êm — phiên anh em vừa xong, `notify-email.yml` còn đang chạy, sổ ghi ở bước CUỐI nên chưa kịp hiện |
     | Sổ KHÔNG có dòng đó **và** `lastRunAt` cách hiện tại **≥ 20 phút** | Cờ đang NÓI DỐI → **QUÉT THẬT**, commit tiền tố `Cap nhat ban tin` như thường |

     **Cơ chế:** `state.py` chỉ ghi nhận *"pipeline đã chạy xong"* — nó KHÔNG biết bản tin có được GỬI hay không, hai chuyện khác nhau. Cổng gửi của `notify-email.yml` xét **commit message + khung giờ VN (≥20:30 hoặc 03:30–07:00)**, hoàn toàn không xét khoá. Nên một phiên chạy GIỮA NGÀY (ví dụ Huy bấm tay `workflow_dispatch` mode=normal lúc 15:00) vẫn `done` và chiếm ô khoá, trong khi commit của nó rơi ngoài khung giờ nên không kích email/Telegram — mọi lớp buổi tối sau đó exit 10 rồi SKIP, **cả chuỗi im lặng mà bản tin mất trắng**. Đúng chuyện đã xảy ra tối 29/07 (thủ phạm hôm đó là nhánh `MODE=test`, nay đã vá bằng `DIEMTIN_PHIEN_TEST`; nhưng đường bấm tay giữa ngày thì vẫn còn nên phép kiểm này vẫn cần).
     Vì sao kiểm bằng SỔ chứ không bằng `state.json`: sổ được ghi ở **bước CUỐI sau khi đã gửi xong mọi kênh** nên là dấu vết việc-đã-làm, còn `lastSuccess` chỉ là lời tự khai của một phiên. Đúng nguyên tắc số 1 của canary — **kiểm ĐẦU RA, không kiểm quy trình**.
     ⛔ **KHÔNG sửa tay `logs/state.json` để lách**, KHÔNG dùng `--force` (nó chỉ cướp khoá `RUNNING`, không bỏ qua cờ đã-xong — đúng thiết kế). Cứ quét rồi commit là email/Telegram vẫn đi. Lớp sau vẫn thấy exit 10 và SKIP nên không có nguy cơ quét chồng.
     ⚠️ Ghi rõ vào `logs/scan-gaps.json` (mục `note`) và vào log rằng phiên này **quét đè lên cờ đã-xong** kèm lý do, để người đọc sau không tưởng có hai phiên tranh nhau.
2. Ghi `[<giờ UTC>Z] START (CI)` vào log, commit + push NGAY (mẫu: `git add logs/ && git commit -q -m "log: start <ngày> <giờ>Z phien toi (CI)" && git push origin main -q`).
3. Quét theo SKILL. Sau mỗi mốc lớn: ghi checkpoint log + `python3 scripts/state.py beat web-scan` + push log.
   ⏱️ **BEAT NGAY TRƯỚC KHI GIAO AGENT, đừng đợi agent xong mới beat** (vá 28/07/2026). Khoá thối sau **30 phút không nhịp** (`LOCK_STALE_MIN`), mà vòng agent là chặng DÀI NHẤT của phiên — beat "sau mỗi mốc lớn" nghĩa là nhịp đầu tiên chỉ tới khi agent xong. Đo thật phiên tối 28/07: start 21:00 → beat đầu tiên **21:26**, tức 25 phút không nhịp, chỉ cách ngưỡng thối **5 phút**. Vòng agent chậm thêm 5 phút nữa là khoá tự mở TRONG LÚC phiên vẫn đang quét → mốc kế (local 21:15 hoặc CI 22:00) cướp khoá và **quét chồng**, đúng sự cố hai phiên cùng quét hôm 26/07.
   Vì vậy beat ở CẢ BA chỗ này, không chỉ ở mốc lớn: **(a) ngay sau `harvest.py` + `telegram_harvest.py`** · **(b) ngay TRƯỚC khi giao lô agent** · **(c) sau khi gom xong kết quả agent**. Nguyên tắc: **hai nhịp liên tiếp không được cách quá ~15 phút**; sắp làm việc gì dự kiến lâu thì beat trước khi bắt đầu, không phải sau khi xong.
3b. **CHỈ PHIÊN TỐI — xử lý tin Jay Lâm gửi thành TIN CHUẨN, sau khi nạp tin quét, TRƯỚC khi commit** (thêm 30/07/2026, chỉ thị Huy: *"tin Jay Lâm gửi cũng là tin kèm url và tóm tắt gần giống định dạng mẫu"*).
   ```
   python3 scripts/tin_jaylam.py --liet-ke
   ```
   Mã **10** = không có tin chờ, bỏ qua bước này. Mã **0** = có tin: với mỗi tin, truy về bài gốc theo đúng luật TRUY NGƯỢC của Báo Mới (nguồn chính thức → wire → báo chuyên ngành; WebFetch xác nhận bài có thật), viết `tieu_de` + `tom_tat` 1-2 câu, rồi:
   ```
   python3 scripts/tin_jaylam.py --ghi /tmp/jaylam.json
   ```
   `[{"id": <id>, "tieu_de": "...", "tom_tat": "...", "nguon_ten": "Reuters", "nguon_url": "https://...", "la_cnqs": false}]`
   - ⛔ **`la_cnqs: true` cho tin CNQS Mỹ** (khí tài · hệ thống · hợp đồng quốc phòng) — nhóm DUY NHẤT được nới khung **3 ngày lùi**, y như tin quét thường. Khai hụt là loại oan đúng nhóm Huy cần nhất.
   - Không truy được bài gốc thì VẪN GIỮ tin: `nguon_ten: "Jay Lâm gửi"`, bỏ trống `nguon_url`. Đừng nhét link bừa — guardrail chặn trang chủ và live-blog.
   - Một mục sai là CHẶN CẢ LÔ (mã 1, không ghi gì): sửa mục lỗi rồi chạy lại.
   - **Quá hạn 21:45 thì BỎ bước này**, chốt bản tin trước. Tin không xử lý kịp không mất — mục 5 tự lùi về nguyên văn đã cắt, hoặc vào bản tối hôm sau.
   - Phiên SÁNG SỚM **không làm** bước này (mục 5 chỉ có ở bản buổi tối).
4. Kết thúc — LUÔN một trong ba: `python3 scripts/state.py done web-scan "<tóm tắt>"` (nạp được tin) / `skip` (lô rỗng) / `fail` (lỗi giữa chừng, VẪN push log).
   Commit bản tin đúng mẫu `Cap nhat ban tin DD/MM: +N tin (5 chu de)` — `git add index.html data/ logs/` (phải có logs/state.json) rồi push. Push bị từ chối → `git pull --rebase origin main` rồi push lại; pull báo unstaged changes ở file KHÔNG thuộc lô này thì cứ push, đừng commit hộ file lạ.
5. Báo cáo cuối NGẮN GỌN: số tin mỗi chủ đề, chủ đề nào thiếu (đã nới 48h chưa), trạng thái push.

## RÀNG BUỘC CỨNG
- KHÔNG đọc cả `index.html` bằng tool Read (170KB) — grep + `scripts/add_news.py`.
- KHÔNG bịa tin/link; không chắc `sourceUrl` thì bỏ tin. Được phép trả ít tin nếu ngày khan — ghi rõ trong tóm tắt.
- Email + file Word do GitHub Action `notify-email.yml` tự lo khi thấy commit `Cap nhat ban tin` — mày không cần gửi gì.

## BƯỚC 6 — CHỈ PHIÊN SÁNG SỚM: gộp thêm sự kiện + tập trận + think-tank (gộp 28/07/2026)

> Chỉ thị Huy 28/07/2026: *"sự kiện sáng thì quét gộp với quét tin 4h sáng cũng được."* Pipeline
> `event-scan` (trước đây là workflow riêng `claude-event-scan.yml`, ĐÃ XOÁ) nay chạy NGAY TRONG
> phiên này khi mày là ca sáng sớm — không phải một session khác.

**CHỈ làm bước này nếu mày xác định ở Bước 1 mình là phiên SÁNG SỚM** (`TZ='Asia/Ho_Chi_Minh' date +%H:%M` < 14:00). Phiên TỐI dừng ở Bước 5, không đọc tiếp phần này.

Đây là pipeline THỨ HAI, khoá RIÊNG (`event-scan`, khác `web-scan` ở trên) và **commit RIÊNG** — không
gộp vào commit bản tin, vì `notify-morning.yml` chỉ bắt tiền tố commit của pipeline này (email 🎖️ Sự
kiện & Tập trận khác hẳn email 📰 bản tin). Chỉ nơi kích là gộp lại (1 session), cơ chế khoá/gửi vẫn
tách như cũ.

1. `git pull --rebase origin main` rồi `python3 scripts/state.py claim event-scan`.
   - exit 10 (sáng nay đã xong) / exit 11 (phiên khác đang chạy): ghi 1 dòng SKIP vào log, commit +
     push log, DỪNG bước này (phiên vẫn coi là hoàn tất — bản tin 5 chủ đề ở Bước 5 đã xong).
   - exit 0: giữ khoá, làm tiếp. Ghi `[<giờ UTC>Z] START event-scan (CI, gop vao sang som)` vào log.
2. Quét sự kiện + tập trận bằng agent (tool Agent, model "sonnet"): nhúng nguyên output
   `python3 scripts/add_news.py --recent-titles 20`; tìm sự kiện ngoại giao có ký kết trong 48h +
   diễn biến tập trận + tin liên quan; gộp `/tmp/new_items_event.json` (chỉ khoá newDipEvents/
   dipEventUpdates/newExercises/exerciseUpdates + date) rồi
   `python3 scripts/add_news.py /tmp/new_items_event.json`. Beat: `python3 scripts/state.py beat event-scan`
   NGAY TRƯỚC khi giao agent, hai nhịp không cách quá ~15 phút.
3. BỐI CẢNH + KHÁI NIỆM: mỗi cuộc tập trận MỚI hoặc đang diễn ra CHƯA có `background` → agent Sonnet
   viết `background` (2–4 câu, `\n` ngăn đoạn) + `concepts` ([{term,def}]). Ghi `/tmp/briefing.json`
   rồi `python3 scripts/set_exercise_briefing.py /tmp/briefing.json`.
   ⚠️ Bước NẠP file Word "thông tin nền" (`import_background_docx.py`) CHỈ chạy được ở máy local
   (file nằm trên Desktop Huy) — CI bỏ qua phần đó, chỉ làm phần agent sinh `background` ngắn.
3b. BÀI THINK-TANK (mỗi phiên sáng sớm, KHÔNG chỉ Chủ nhật):
   - `python3 scripts/add_analyses.py --candidates` → ứng viên HAI LỚP: `[RSS]` 27 viện có feed +
     `[HTML]` 10 viện quét thẳng trang danh sách (thêm 30/07/2026). Dòng ⚠️ "Trang HTML KHÔNG ra
     link bài nào" nghĩa là viện đó đổi giao diện, KHÔNG phải hôm nay không có bài — ghi vào tóm
     tắt cuối phiên để phiên local sửa `THINKTANK_HTML`, đừng bỏ qua.
   - Giao agent Sonnet chọn 4–6 bài, phủ ít nhất 2–3 khu vực (1–2 bài trọng tâm cũ: Úc/AUKUS · Biển
     Đông · CNQS · Mỹ-Trung-Đài Loan · Mali/Sahel; 1–2 bài vùng khác đang có chuyện). LOẠI: chính trị
     xã hội nội bộ Mỹ, quảng bá viện, điểm sách/điểm báo. Agent MỞ ĐỌC (WebFetch) rồi viết tiếng Việt
     đủ field. Số liệu mập mờ → BỎ, không đoán.
   - Ghi `/tmp/analyses.json` rồi `python3 scripts/add_analyses.py /tmp/analyses.json`.
   - **SINH KHÁI NIỆM cho chính những bài vừa nạp** (29/07/2026): mỗi bài rút 1–3 thuật ngữ người
     đọc phổ thông không hiểu ngay, định nghĩa tiếng Việt 1–3 câu ĐỌC RIÊNG VẪN HIỂU. Ghi
     `/tmp/kn-analyses.json` = `[{"url":"...","concepts":[{"term":"...","def":"..."}]}]` rồi
     `python3 scripts/set_analysis_concepts.py /tmp/kn-analyses.json`. Bài không có thuật ngữ đáng
     lưu thì BỎ HẲN khỏi mảng (đừng khai mảng concepts rỗng — guardrail chặn). Guardrail còn chặn:
     url lạ · thiếu term/def · def dưới 40 ký tự · term quá 90 ký tự · trùng term trong cùng bài ·
     quá 6 khái niệm/bài. Trùng với khái niệm bài khác thì không sao, web tự khử trùng.
4. CHỦ NHẬT (`TZ='Asia/Ho_Chi_Minh' date +%u` = 7): báo cáo tuần.
   `python3 scripts/weekly_context.py --out /tmp/weekly_ctx.json` → giao 1 agent model "opus" (BẮT
   BUỘC Opus) đọc file, viết nhận định tuần 3 nước kèm link nội dòng markdown dùng đúng url ngữ liệu
   → ghi `/tmp/weekly.json` (us→cn→ru, không kèm generatedAt) → `python3 scripts/add_weekly.py /tmp/weekly.json`.
5. Kết thúc — LUÔN một trong ba: `state.py done event-scan "<tóm tắt>"` / `skip` / `fail` (vẫn push log).
   Commit tiền tố (QUYẾT ĐỊNH email sáng, KHÁC tiền tố `Cap nhat ban tin`):
   - Có sự kiện/tập trận: `Cap nhat su kien DD/MM: +N su kien/tap tran[, +M bai think-tank][, bao cao tuan]`
   - CHỈ báo cáo tuần: `Dang bao cao tuan DD/MM`
   - CHỈ think-tank: vẫn `Cap nhat su kien DD/MM: +M bai think-tank`
   - Rỗng thật: message tự do, không dùng 2 tiền tố trên.
   `git add index.html data/ logs/` (phải có `logs/state.json`; **`data/` là BẮT BUỘC** — bài
   think-tank nằm ở `data/analyses.json` từ 30/07/2026, bỏ sót thì bài nạp xong KHÔNG lên web
   mà cũng không có lỗi nào) → commit RIÊNG với commit bản tin → push
   (bị từ chối → `pull --rebase` rồi push lại).
6. Báo cáo cuối (gộp chung với báo cáo Bước 5): số sự kiện/tập trận, có báo cáo tuần không, trạng thái
   push của CẢ HAI commit.
