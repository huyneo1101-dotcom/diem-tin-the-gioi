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
| **SÁNG SỚM** | 03:47 | 04:30 | 04:47 | 05:30 | không có |

`harvest-ci.yml` chạy **trước mỗi mốc CI ~15 phút** để lô ứng viên còn tươi (`harvest.py` bỏ lô
quá 4 tiếng). Canary chạy **sau lớp cuối**, không phải sau hạn chót: ca `toi` 22:45 (lớp vét
21:47 + quét ~20' ⇒ gửi ~22:10) · ca `sang` 06:15 · ca `sukien` 07:00.

⚠️ **Lịch task LOCAL không đo được tự động** — app Claude giữ cron trong DB riêng, trên đĩa chỉ
có `~/.claude/scheduled-tasks/<id>/SKILL.md` (đã kiểm 30/07/2026). Phần local trong bảng dưới là
**khai tay** trong `LOCAL_KHAI_TAY` của `scripts/kiem_lich.py`; đổi cron task thì phải sửa ở đó,
không có ai canh hộ. Con số `fire ~` đã tính jitter thật của app.

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
| `web-scan-diem-tin` | `30 4,5 * * *` | 04:30 · 05:30 (jitter ~209s ⇒ fire ~04:33) | bật | dự phòng bản tin SÁNG SỚM + event-scan (Bước 4) |
| `web-scan-diem-tin-toi` | `15 21 * * *` | 21:15 (jitter ~377s ⇒ fire ~21:21) | bật | dự phòng bản tin TỐI — lớp CUỐI còn kịp hạn email 22:00 |
| `event-scan-diem-tin` | `15 9,10 * * *` | 09:15 · 10:15 | TẮT 28/07 | gộp vào web-scan-diem-tin, đừng bật lại |
<!-- LICH:END -->
