# Vận hành — log, Báo Mới, Google Drive, tab Cà phê, ghi chú — Điểm Tin Thế Giới

> Xẻ từ `CLAUDE.md` ngày 25/08/2026 để bản thi hành gọn lại (luật mục 31 của `~/.claude/CLAUDE.md`).
> **Nội dung giữ NGUYÊN VĂN, không cắt chữ nào** — chỉ đổi chỗ ở. Bản thi hành: [`../../CLAUDE.md`](../../CLAUDE.md).

## Tab "Cà phê" (ngoài chủ đề tin — thêm 24-25/07/2026)
Tab **☕ Cà phê**: tìm quán cà phê làm việc HN, xếp theo khoảng cách từ điểm xuất phát. **Mốc xuất phát THEO USER** (Huy chốt 25/07/2026: *"với ngừoi dùng huyneo thì chỉ để 2 điểm xuất phát mặc định… với ngừoi dùng lamgiaphat thì chỉ để điểm mặc định là Trường chinh (ẩn điểm mặc định … với người dùng này)"*) — `huyneo` → **Núi Trúc + Nguyễn Khuyến**; `lamgiaphat` → **Trường Chinh** (ẩn 2 mốc kia); user khác → không có mốc mặc định, tự lưu mốc riêng vào `localStorage dt.cafeLocs`. ⚠ Dòng này từng ghi gộp *"(Giảng Võ/Trường Chinh/GPS)"* — **sai cả cấu trúc lẫn địa danh** (mốc Giảng Võ đã đổi sang Núi Trúc), phát hiện 30/07 khi rà quy tắc chưa ghi. Nguồn sự thật là chú thích ngay trên `renderCafes` trong `index.html`, đừng sửa dòng này rời khỏi code. Dữ liệu `DATA.workCafes` (embed index.html); code `renderCafes`/`cf*`/CSS `.cf-*`. Scheduled task local **`cafe-rating-retry`** (`15 9 * * 2,5`) vét dần rating Google còn thiếu qua `scripts/cafe_ratings.py` (--missing/--apply), commit **`Cap nhat rating quan ca phe: ...`** — tiền tố này KHÔNG khớp gate email nên không gửi mail. Chi tiết: memory `diem-tin-tab-cafe`.

## Log & tự phục hồi (Routine tự động)
Routine chạy trong session mới (ephemeral) nên phải để lại dấu vết để chẩn đoán khi lỗi:
- **Log bắt buộc mỗi lần chạy**: ghi vào `logs/scan-<NGÀY-VN>.log` (ngày theo `TZ='Asia/Ho_Chi_Minh' date +%F`) các mốc: START, kết quả từng agent/phần, chạy script, và DONE/SKIP/FAIL kèm lý do. **Luôn commit + push file log** kể cả khi quét thất bại (git không cần mạng ngoài nên push được ngay cả khi WebSearch/WebFetch bị chặn) — đây là cách duy nhất biết Routine fail ở đâu.
- **Idempotent (chống chạy trùng)**: đầu mỗi lần chạy, `python3 scripts/state.py claim <pipeline>` (dùng `claim` để GIÀNH KHOÁ, không phải `check` — `check` chỉ hỏi, không chặn được phiên chạy chồng). exit 10 = buổi đó ĐÃ XONG · exit 11 = phiên khác đang chạy → cả hai: ghi log `SKIP`, push log, KẾT THÚC. exit 0 = quét bình thường, xong thì `state.py done <pipeline> "<tóm tắt>"` và commit `logs/state.json` kèm bản tin. **KHÔNG dùng `generatedAt` làm cờ** (xem mục trên).
- **Retry cho tới khi xong (xen kẽ CI/local từ 26/07/2026)**: bản tin TỐI (hạn chót email 22:00): CI 20:47 → local 21:15 (2 lớp trong hạn, local là task RIÊNG `web-scan-diem-tin-toi`) → CI 21:47 (lớp VÉT, chỉ khi 2 lớp trước chết); bỏ hẳn mốc 21:30/22:30; bản tin SÁNG SỚM (từ 27/07/2026 CÓ local dự phòng): CI 03:47 → local 04:30 → CI 04:47 → local 05:30. **event-scan sáng — GỘP 28/07/2026: dùng CHUNG 4 mốc trên**, chạy NGAY SAU bản tin trong cùng session (không còn mốc 08:45/09:15/09:45/10:15 riêng). Nhờ khoá idempotent `state.py`, mốc nào thấy DONE/RUNNING thì tự SKIP; phiên chết giữa chừng thì 30' sau heartbeat thối, mốc kế cướp khoá quét lại. Cron local là giờ LOCAL (Asia/Ho_Chi_Minh), **KHÔNG phải UTC**; cron CI là UTC.
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
| `baomoi-topics.json` | **Quét chuyên mục công khai** (`the-gioi`, `kinh-te`, `khoa-hoc-cong-nghe`) | Không | **KHO ỨNG VIÊN** (~50–100 bài) → **đúng chủ đề là cho vào, KHÔNG có trần số lượng** (Huy chốt 02/08/2026, bỏ luật cũ «lấy ~3–6 bài tốt nhất») → `worldNews` như tin thường, KHÔNG gắn `_baomoi` |

```
python3 scripts/add_news.py --baomoi-pending   # in cả 2 nhóm, đã bỏ bài quá 24h + bài đã có trong DATA
```
### TRUY NGƯỢC VỀ NGUỒN GỐC (bắt buộc từ 23/07/2026)
Báo Mới là trang TỔNG HỢP — gần như mọi bài quốc tế trên đó đều dẫn lại từ một nguồn nước ngoài.
Agent 7 và 8 phải **tìm bài gốc** (nguồn chính thức → wire → báo quốc tế uy tín), **đăng trong 24h**,
**mở bằng WebFetch để xác nhận có thật**, rồi lấy `sourceName` + `sourceUrl` + `title` + `summary` +
`significance` theo bài gốc — **đổi cả tiêu đề lẫn URL**, không giữ cách đặt tiêu đề của bản dẫn lại.
- Không tìm được: **CẢ Agent 7 LẪN Agent 8 GIỮ link báo Việt Nam hoặc link Báo Mới, KHÔNG bỏ bài**
  (Huy chốt 02/08/2026, đổi luật cũ bắt Agent 8 bỏ bài rồi chọn ứng viên khác).
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
phải liệt kê lại — `add_news.py` tự đọc `baomoi-topics.json` và lấy phần chưa dùng. **KHÔNG CÓ TRẦN**
(Huy chốt 02/08/2026: *"bị loại chỉ là những bài không đúng chủ đề hoặc không nằm trong khung ngày
cho phép. không có số lượng tối đa cho bài bị loại"*; hai hằng số `REJECTED_PER_RUN`/
`BAOMOI_REJECT_PER_RUN` gỡ hẳn 22/08/2026). Vòng xoay 4 chuyên mục **giữ lại nhưng nay chỉ quyết THỨ
TỰ hiện trên web**, không quyết bài nào bị cắt: xoay theo CNQS → Ngoại giao → Kinh tế → Chính trị nên
mục thích hơn nổi lên trước. Tin agent CHỦ ĐỘNG loại xếp TRƯỚC ứng viên Báo Mới trong danh sách.
⛔ **Đừng vá bằng cách hạ hai hằng số về 0** — đã thử 02/08 và hỏng CÂM ngược ý (vế phải âm cắt sạch
nhánh tin agent loại). Cổng canh: `tests/test-cong-bi-loai.py` (14 ca · 12 bản hỏng).

### 🚪 CỔNG BÀI ĐƯỢC 👍 (dựng 22/08/2026)
Huy chốt 02/08/2026: *"tự tổng hợp những bài bị loại được bấm nút thích hằng ngày để thêm vào lần
gửi tin tiếp theo (miễn vẫn đúng các tiêu chí)"*. `add_news.py` in cổng này ở **cả hai** lệnh phiên
quét bắt buộc chạy, ngay sau cổng Báo Mới. Thấy cổng còn bài thì **phải xử lý từng bài**: nạp nếu
vẫn đúng khung ngày + chủ đề + không trùng, HOẶC ghi lý do vào `logs/loai-tin.md`.

**Đường dữ liệu** (đừng đo lại): nút 👍 trên thẻ Bị loại gọi `castVote` → bảng `votes` Supabase,
khoá `item_id` chính là `sourceUrl`. View công khai **`vote_thich_theo_bai`** gom theo `item_id`,
chỉ `v=1`, cửa sổ 21 ngày, KHÔNG kèm `user_id`, chỉ cấp quyền `SELECT`. `sync-preferences.yml` kéo
về `preferences.json` field **`liked`**.
- ⚠ **KHÔNG dùng được `vote_items`** — view đó gom theo TIÊU ĐỀ nên không trả về địa chỉ bài.
- ⚠ **KHÔNG dùng được `dt.promoted`** — nút *kéo vào Bài mới* chỉ ghi localStorage máy người đọc.
- ⚠ **Cổng đọc THẲNG danh sách 👍, KHÔNG giao với `rejectedNews`**: mục Bị loại tự dọn sau
  `REJECTED_KEEP_DAYS` = 1 ngày, nên bài 👍 muộn đã biến mất. Đo 22/08: 21 bài đã 👍 mà chưa nạp,
  **không bài nào** còn nằm trong mục Bị loại — giao hai tập là mất sạch.
- Cửa sổ nêu lại: `BI_LOAI_THICH_SO_NGAY` = 7 ngày kể từ lúc BẤM 👍, không phải từ ngày đăng bài.
- **Fail về phía KÊU:** `preferences.json` không đọc được, hoặc thiếu hẳn field `liked` (workflow
  `sync-preferences` chết), thì cổng in ĐỎ — im ở đó không phân biệt được với «không có bài nào».
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

## Nhập tin từ Google Drive (pipeline `drive-import`)

> ### ⛔ ĐÃ TẮT LỊCH 30/07/2026 (Huy chốt) — chỉ còn chạy tay
> Workflow **giữ nguyên, không xoá**; chỉ bỏ `schedule`, còn `workflow_dispatch`. Chạy lại bằng
> `gh workflow run import-news-from-drive.yml`. Hai lý do, đều đo được:
> **01. Nguồn đã khô.** `logs/state.json` → `drive-import.lastSuccess.sang = 2026-07-21`; mọi phiên từ
> 22/07 tới 29/07 ghi note *"khong tim thay file ban-tin-chien-luoc nao"*, log ngày đều đúng 261 byte
> cùng một khuôn. 09 ngày chạy không ra tin mà workflow vẫn báo `success` — chết câm, bảng CI vẫn xanh.
> **02. Nó là workflow tự động CUỐI CÙNG hợp nhất file dùng chung bằng rebase.** Bước "Commit if
> changed" `git add index.html logs/` rồi `git pull --rebase` — cùng lớp lỗi đã gây sự cố sổ đã gửi
> sáng 30/07. Phiên quét local sáng 30/07 chạy bù lúc 07:41 và 07:48, cách mốc 07:23 đúng **18 phút**.
> **Bật lại lịch thì phải vá khối commit trước** — cổng `.github/scripts/kiem_luat_push.py` chặn cứng
> (mục dưới). Và **đừng bê nguyên `ghi_so_push.py` sang**: sổ là append-only nên git hợp nhất được, còn
> `index.html` thì không — hai lô tin cùng chèn vào đầu mảng `DATA.news` là xung đột văn bản gần như
> chắc chắn. Đường đúng cho file này: push bị từ chối → `fetch` → bỏ lô của mình → **chạy lại
> `add_news.py`** với chính `/tmp/new_items.json` trên đỉnh mới (nó dedupe theo URL) → commit → push.

Action `import-news-from-drive.yml` (trước đây 08:00 & 20:00 VN) tìm **mọi** file `ban-tin-chien-luoc-YYYY-MM-DD-HHMM-ICT.json`
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
  | `web-scan-diem-tin` | `30 4,5 * * *` (DỰ PHÒNG phiên SÁNG SỚM, sau CI 03:47/04:47) | `docs/routine-web-scan.md` (Bước 1-3 = bản tin, **Bước 4 = event-scan gộp**) | Bản tin 5 chủ đề **+ sự kiện/tập trận/think-tank** — phiên sáng sớm |
  | `web-scan-diem-tin-toi` | `15 21 * * *` (DỰ PHÒNG phiên TỐI, sau CI 20:47 — lớp CUỐI còn kịp hạn email 22:00) | `docs/routine-web-scan.md` (chung file với phiên sáng sớm để hai phiên không lệch nhau; mục "PHIÊN TỐI — BỐI CẢNH RIÊNG" cuối file) | Bản tin 5 chủ đề — phiên tối |
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

---
