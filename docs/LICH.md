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

## Trình tự các lớp (đọc theo hàng, đây là thứ hay bị tính sai biên)

| Phiên | Lớp 1 (CI) | Lớp 2 (local) | Lớp 3 (CI) | Lớp 4 (local) | Hạn chót |
|---|---|---|---|---|---|
| **TỐI** | 20:47 | **21:15** ← lớp cuối còn kịp hạn | 21:47 = lớp VÉT (đã trễ hạn) | — | email **22:00** |
| **SÁNG SỚM** | local 04:00 ← lớp CHÍNH | **local 04:05** ← lớp cuối còn kịp hạn | CI 03:47/04:47 (trễ 2-4h, lưới) | local 04:35/04:40 = lớp VÉT (đã trễ hạn) | tới tay **04:30** |

⛔ **HẠN CHÓT CA SÁNG LÀ 04:30 — Huy chốt 31/08/2026**, nguyên văn *"tin buổi sáng bắt buộc
phải có lúc 4h30 sáng"*. Hằng số ở `scripts/state.py::HAN_CHOT`, phép đo ở
`scripts/do_gio_ban_tin.py`, canary soi cùng số đó. Quét đo được 16-21 phút nên mốc kích
chính phải là **04:00** (trước là 04:30, tức bản tin sớm nhất cũng 04:50 — LUÔN vỡ hạn).
Đừng nới hạn cho vừa lịch; muốn đổi lịch thì đổi mốc kích, không đổi hạn.

`harvest-ci.yml` chạy **trước mỗi mốc CI ~15 phút** để lô ứng viên còn tươi (`harvest.py` bỏ lô
quá 4 tiếng). Canary chạy **sau lớp cuối**, không phải sau hạn chót: ca `toi` 22:45 (lớp vét
21:47 + quét ~20' ⇒ gửi ~22:10) · ca `sang` 06:15 · ca `sukien` 07:00.

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
| `canary.yml` | `45 15 * * *` | 22:45 |
| `canary.yml` | `15 23 * * *` | 06:15 |
| `canary.yml` | `0 0 * * *` | 07:00 |
| `claude-web-scan.yml` | `47 13 * * *` | 20:47 |
| `claude-web-scan.yml` | `47 14 * * *` | 21:47 |
| `claude-web-scan.yml` | `47 20 * * *` | 03:47 |
| `claude-web-scan.yml` | `47 21 * * *` | 04:47 |
| `harvest-ci.yml` | `32 13 * * *` | 20:32 |
| `harvest-ci.yml` | `32 14 * * *` | 21:32 |
| `harvest-ci.yml` | `32 20 * * *` | 03:32 |
| `harvest-ci.yml` | `32 21 * * *` | 04:32 |
| `sync-baomoi.yml` | `28 0,12 * * *` | 07:28 · 19:28 |
| `sync-preferences.yml` | `30 0 * * *` | 07:30 |
| `telegram-bot.yml` | `*/5 * * * *` | (không cố định) |

| Task LOCAL (khai tay — xem docstring `kiem_lich.py`) | cron | Giờ VN | Trạng thái | Việc |
|---|---|---|---|---|
| `com.huy.routine-diemtin-sang` | `5,35 4 * * *` | 04:05 · 04:35 | bật | dự phòng bản tin SÁNG SỚM + event-scan (Bước 4) — LaunchAgent headless sonnet; dời từ 04:30·04:45 ngày 31/08/2026 vì HẠN CHÓT tới tay là 04:30 (state.py::HAN_CHOT) |
| `com.huy.routine-diemtin-toi` | `15 21 * * *` | 21:15 | bật | dự phòng bản tin TỐI — lớp CUỐI còn kịp hạn email 22:00 — LaunchAgent headless sonnet |
| `com.huy.diemtin-giu-thuc-som` | `40 3 * * *` | 03:40 | bật | caffeinate 90' giữ máy thức cho các mốc local sáng — CẶP với `pmset repeat` 03:40. Bảng này từng khai 03:41 trong khi plist thật khai 03:40; đo lại 31/08/2026, sửa theo plist |
| `com.huy.diemtin-giu-thuc` | `26 4 * * *` | 04:26 | bật (lưới 2) | caffeinate 90' — mốc cũ cặp với pmset 04:25 đã đổi, giữ làm lưới thứ hai |
| `com.huy.diemtin-giu-thuc-toi` | `40 20 * * *` | 20:40 | bật | caffeinate 90' giữ máy thức cho mốc local tối 21:15 |
| `com.huy.diemtin-kich-ci` | `45 20 * * * | 0 21 * * * | 0 22 * * * | 45 3 * * * | 0 4 * * * | 40 4 * * *` | 20:45 · 21:00 · 22:00 · 03:45 · 04:00 · 04:40 | bật | kích workflow CI ĐÚNG GIỜ từ máy Mac (cron GitHub trễ 2-4h); ba mốc sáng dời từ 04:30 ngày 31/08/2026 để bản tin kịp HẠN CHÓT 04:30 — bảng mốc thật ở kich_ci.py::LICH |
| `com.huy.diemtin-kiem-ci` | `35 21 * * * | 15 4 * * *` | 21:35 · 04:15 | bật | kiểm chéo `kich_ci.py --kiem`: chưa có bản tin thì bấm lại. Mốc sáng kéo từ 05:15 về 04:15 ngày 31/08/2026 để còn cứu được TRONG hạn 04:30, không chỉ cứu khỏi mất hẳn |
<!-- LICH:END -->
