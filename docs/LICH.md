# LỊCH CHẠY — nguồn sự thật cho MỌI số giờ trong tài liệu

> **Bảng dưới đây SINH TỪ chính dòng `cron:` của các workflow** — chạy
> `python3 scripts/kiem_lich.py --sinh` để sinh lại, `--kiem` để soi lệch.
> Chỗ nào trong tài liệu cần số giờ thì **trỏ về file này** thay vì chép số ra.

**Vì sao có file này (bắt được 30/07/2026):** `claude-web-scan.yml` dời cả 04 mốc sớm 13 phút
(21:00→20:47 · 22:00→21:47 · 04:00→03:47 · 05:00→04:47) và `harvest-ci.yml` dời theo, nhưng
**47 chỗ trong tài liệu vẫn ghi lịch cũ** — `CLAUDE.md` 25 chỗ · `docs/routine-web-scan.md` 15 ·
skill `quet-tin` 4 · `.github/prompts/web-scan-ci.md` 3. Chú thích của chính `canary.yml` còn
ghi *"sau lớp vét TỐI (CI 21:00 · local 21:15 · vét CI 22:00)"* — cả ba số đều đã chết.
Cơ chế: giờ chạy bị chép ra hàng chục chỗ cho người đọc tiện, mà **không chỗ nào là nguồn sự
thật**; sửa cron thì không có gì bắt phải sửa những chỗ chép lại. Cái giá không phải sai chữ
nghĩa mà là **phiên sau tính biên thời gian theo mốc đã chết** — đúng lỗi đã khiến mốc canary
`sukien` phải dời hai lần.

⛔ **PHIÊN TỐI BỎ HẲN 18/09/2026** — chỉ thị Huy, nguyên văn: *"chỉ cần gửi tin 4h sáng thôi,
không phải quét và gửi buổi tối nữa đâu"*. Gỡ cùng lượt: 02 cron tối của `claude-web-scan.yml`
(20:47 · 21:47) · 02 cron tối của `harvest-ci.yml` (20:32 · 21:32) · cron canary ca `toi`
(22:45) · 03 mốc tối trong `kich_ci.py::LICH`. Đo trước khi gỡ: sổ `logs/da-gui-email.json`
không có dòng `[toi]` nào từ 13/09 tới 18/09 — bản tối đã tự chết im 06 đêm liền.
Phần LOCAL của phiên tối đã tắt từ trước: `com.huy.routine-diemtin-toi.plist` và
`com.huy.diemtin-giu-thuc-toi.plist` nằm trong `~/Library/LaunchAgents/_tat-hd-va-diemtin-toi/`,
còn plist `diemtin-kich-ci`/`diemtin-kiem-ci` đo 18/09 cũng chỉ còn mốc sáng — bảng khai tay
dưới đây đã mục theo và được sửa lại cùng lượt.
⛔ **ĐỪNG CẮM LẠI MỐC TỐI KHI THẤY BẢN SÁNG MỎNG** — đó là việc của SÀN và KHUNG NGÀY
(`scripts/soi_muc_cam.py::SAN_MOI_MUC`), không phải việc của lịch.

## Trình tự các lớp (đọc theo hàng, đây là thứ hay bị tính sai biên)

| Phiên | Lớp 1 (CI) | Lớp 2 (local) | Lớp 3 (CI) | Lớp 4 (local) | Hạn chót |
|---|---|---|---|---|---|
| **SÁNG SỚM** | local 04:00 ← lớp CHÍNH | **local 04:05** ← lớp cuối còn kịp hạn | CI 03:47/04:47 (trễ 2-4h, lưới) | local 04:35/04:40 = lớp VÉT (đã trễ hạn) | tới tay **04:45** |

⛔ **HẠN CHÓT CA SÁNG LÀ 04:45 — Huy chốt 31/08/2026 ở mốc 04:30**, nguyên văn *"tin buổi sáng
bắt buộc phải có lúc 4h30 sáng"*; **nới sang 04:45 ngày 17/09/2026**. Hằng số ở
`scripts/state.py::HAN_CHOT`, phép đo ở `scripts/do_gio_ban_tin.py`, canary soi cùng số đó.
Mốc kích chính vẫn giữ **04:00** (không đổi theo hạn) — quét đo được 16-21 phút nên vẫn còn
biên. Đừng nới hạn cho vừa lịch; muốn đổi lịch thì đổi mốc kích, không đổi hạn.

`harvest-ci.yml` chạy **trước mỗi mốc CI ~15 phút** để lô ứng viên còn tươi (`harvest.py` bỏ lô
quá 4 tiếng). Canary chạy **sau lớp cuối**, không phải sau hạn chót: ca `sang` 06:15 ·
ca `sukien` 07:00. Ca `toi` còn chạy tay được (`workflow_dispatch`) để soi lịch sử, không còn cron.

⚠️ **Lịch mốc LOCAL không đo được tự động** — nó nằm trong plist LaunchAgent chứ không nằm cạnh
workflow. Phần local trong bảng dưới là **khai tay** trong `LOCAL_KHAI_TAY` của
`scripts/kiem_lich.py`; đổi giờ plist thì phải sửa ở đó, không có ai canh hộ.

⚠️ **SỬA 18/08/2026 — PHẦN LOCAL KHÔNG CÒN LÀ SCHEDULED TASK CỦA APP CLAUDE.** Từ 06/08/2026 cả
hai mốc chuyển sang LaunchAgent gọi `routine-claude-headless.py` (`claude -p --model sonnet`), và
tới 18/08/2026 `list_scheduled_tasks` trả về **RỖNG** — không còn task nào trong app. Bảng cũ khai
`web-scan-diem-tin` cron `30 4,5` tức 04:30 · **05:30** là số đã chết: plist thật khai **04:30 và
04:45**, không có mốc 05:30 nào. Không có tiếng kêu nào khi lệch, vì cổng `--kiem` chỉ đối chiếu
phần CI với dòng `cron:` thật, còn phần local thì chính bảng khai tay là "sự thật".
Đo lại bằng: `grep -A14 StartCalendarInterval ~/Library/LaunchAgents/com.huy.routine-diemtin-*.plist`

⚠️ **MỐC LOCAL SÁNG CHỈ SỐNG KHI MÁY THỨC — cặp `pmset repeat` với job caffeinate.** `pmset -g sched`
hiện khai `wakepoweron at 3:40AM`, còn job giữ thức cũ `com.huy.diemtin-giu-thuc` lại nằm ở **04:26**
(dựng theo lịch pmset 04:25 đã đổi). Máy nắp đóng chỉ DarkWake 28-45 giây rồi ngủ lại nên tới 04:26
máy đang ngủ, launchd nổ muộn. Đo sáng 18/08: mốc 04:30 của `com.huy.diemtin-kich-ci` mãi **04:40:12**
mới chạy. Đã vá 18/08 bằng job mới `com.huy.diemtin-giu-thuc-som` ở **03:41**, tức 01 phút sau lúc
pmset đánh thức. **Đổi `pmset repeat` thì phải đổi giờ job đó theo.**

<!-- LICH:BEGIN — sinh bằng scripts/kiem_lich.py --sinh, ĐỪNG sửa tay -->
| Workflow CI | cron (UTC) | Giờ VN |
|---|---|---|
| `canary.yml` | `15 23 * * *` | 06:15 |
| `canary.yml` | `0 0 * * *` | 07:00 |
| `claude-web-scan.yml` | `47 20 * * *` | 03:47 |
| `claude-web-scan.yml` | `47 21 * * *` | 04:47 |
| `harvest-ci.yml` | `32 20 * * *` | 03:32 |
| `harvest-ci.yml` | `32 21 * * *` | 04:32 |
| `sync-baomoi.yml` | `28 0,12 * * *` | 07:28 · 19:28 |
| `sync-preferences.yml` | `30 0 * * *` | 07:30 |
| `telegram-bot.yml` | `*/5 * * * *` | (không cố định) |

| Task LOCAL (khai tay — xem docstring `kiem_lich.py`) | cron | Giờ VN | Trạng thái | Việc |
|---|---|---|---|---|
| `com.huy.routine-diemtin-sang` | `5,35 4 * * *` | 04:05 · 04:35 | bật | dự phòng bản tin SÁNG SỚM + event-scan (Bước 4) — LaunchAgent headless sonnet; dời từ 04:30·04:45 ngày 31/08/2026 vì HẠN CHÓT tới tay là 04:30 (state.py::HAN_CHOT) |
| `com.huy.diemtin-giu-thuc-som` | `40 3 * * *` | 03:40 | bật | caffeinate 90' giữ máy thức cho các mốc local sáng — CẶP với `pmset repeat` 03:40. Bảng này từng khai 03:41 trong khi plist thật khai 03:40; đo lại 31/08/2026, sửa theo plist |
| `com.huy.diemtin-giu-thuc` | `26 4 * * *` | 04:26 | bật (lưới 2) | caffeinate 90' — mốc cũ cặp với pmset 04:25 đã đổi, giữ làm lưới thứ hai |
| `com.huy.diemtin-kich-ci` | `45 3 * * * | 0 4 * * * | 40 4 * * *` | 03:45 · 04:00 · 04:40 | bật | kích workflow CI ĐÚNG GIỜ từ máy Mac (cron GitHub trễ 2-4h); ba mốc sáng dời từ 04:30 ngày 31/08/2026 để bản tin kịp HẠN CHÓT — bảng mốc thật ở kich_ci.py::LICH. Ba mốc TỐI (20:45 · 21:00 · 22:00) gỡ 18/09/2026 cùng phiên tối |
| `com.huy.diemtin-kiem-ci` | `15 4 * * *` | 04:15 | bật | kiểm chéo `kich_ci.py --kiem`: chưa có bản tin thì bấm lại. Mốc sáng kéo từ 05:15 về 04:15 ngày 31/08/2026 để còn cứu được TRONG hạn, không chỉ cứu khỏi mất hẳn. Mốc tối 21:35 gỡ 18/09/2026 cùng phiên tối |
<!-- LICH:END -->
