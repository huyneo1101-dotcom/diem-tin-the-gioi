# Kích workflow đúng giờ bằng cron-job.org (thay cron GitHub)

> Dựng 27/07/2026 sau khi đo được cron GitHub trễ 54' – 3h45 trên **8/10 mốc** trong 24h.
> Mốc `21:00` trễ 69' chính là thứ làm bản tin tối 26/07 vỡ hạn email 22:00.

**Vì sao cách này chạy đúng giờ:** `schedule` của GitHub xếp hàng chung toàn cầu và bị hoãn khi
tải cao; còn `workflow_dispatch` gọi qua API thì **chạy ngay lập tức**, không qua hàng đợi đó.
cron-job.org (miễn phí) chỉ làm một việc: đúng giờ thì gọi API giúp mình.

**Giữ nguyên cron GitHub hiện tại** — nó thành lớp dự phòng. Khoá idempotent (`state.py`) tự
SKIP nếu lớp trước đã quét xong, nên không sợ quét chồng.

---

## Bước 1 — Tạo token GitHub (2 phút)

Mở: **https://github.com/settings/personal-access-tokens/new**

| Ô | Điền |
|---|---|
| Token name | `cron-diem-tin` |
| Expiration | `1 year` (hoặc `No expiration`) |
| Repository access | **Only select repositories** → chọn `diem-tin-the-gioi` |
| Permissions → Repository permissions → **Actions** | **Read and write** |

Bấm **Generate token**, copy chuỗi `github_pat_...` — **nó chỉ hiện MỘT LẦN**.

> 🔒 Token này chỉ có quyền bấm nút chạy workflow trên đúng repo Điểm Tin. Không đọc được
> repo khác, không sửa được code, không đụng tới tài khoản. Lộ ra thì kẻ xấu nhiều nhất là
> chạy được workflow quét tin — và mình thu hồi trong 5 giây ở cùng trang trên.

## Bước 2 — Tạo tài khoản cron-job.org

**https://console.cron-job.org/signup** — email + mật khẩu, không cần thẻ.

## Bước 3 — Tạo cronjob đầu tiên

Bấm **CREATE CRONJOB**, điền:

**Title:** `Điểm Tin — quét TỐI`

**URL** (dán nguyên văn):
```
https://api.github.com/repos/huyneo1101-dotcom/diem-tin-the-gioi/actions/workflows/claude-web-scan.yml/dispatches
```

**Schedule:** chọn timezone **`Asia/Ho_Chi_Minh`**, đặt chạy hằng ngày lúc **21:00**.

Mở mục **ADVANCED** rồi điền tiếp:

- **Request method:** `POST`
- **Headers** — thêm 5 dòng (nút *Add header*):

| Key | Value |
|---|---|
| `Accept` | `application/vnd.github+json` |
| `Authorization` | `Bearer github_pat_...` ← dán token bước 1, **giữ chữ `Bearer ` phía trước** |
| `X-GitHub-Api-Version` | `2022-11-28` |
| `Content-Type` | `application/json` |
| `User-Agent` | `cron-job.org` |

> ⚠️ `User-Agent` là bắt buộc — GitHub API trả **403** cho request không có nó, và lỗi đó
> trông y hệt lỗi sai token nên rất mất công mò.

- **Request body:**
```json
{"ref":"main"}
```

Bấm **CREATE**. Thành công thì GitHub trả **204 No Content** (không có nội dung — đúng, không
phải lỗi).

## Bước 4 — Nhân bản cho các mốc còn lại

cron-job.org có nút **Clone** — nhân bản job vừa tạo rồi chỉ sửa *Title*, *URL*, *Schedule*:

| Title | URL kết thúc bằng | Giờ VN |
|---|---|---|
| Điểm Tin — gom nguồn TỐI | `harvest-ci.yml/dispatches` | 20:45 |
| Điểm Tin — quét TỐI | `claude-web-scan.yml/dispatches` | **21:00** |
| Điểm Tin — vét TỐI | `claude-web-scan.yml/dispatches` | 22:00 |
| Điểm Tin — gom nguồn SÁNG | `harvest-ci.yml/dispatches` | 03:45 |
| Điểm Tin — quét SÁNG | `claude-web-scan.yml/dispatches` | **04:00** |
| Điểm Tin — sự kiện SÁNG | `claude-event-scan.yml/dispatches` | 08:45 |

Phần URL trước tên file luôn giống nhau:
`https://api.github.com/repos/huyneo1101-dotcom/diem-tin-the-gioi/actions/workflows/`

## Bước 5 — Kiểm chứng

Trong cron-job.org bấm **TEST RUN** ở một job. Rồi ở máy chạy:

```
python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/ai_dang_quet.py
```

Đúng thì thấy `🟢 ĐANG CHẠY`. Hoặc kiểm trực tiếp — run mới phải có `event: workflow_dispatch`:

```
gh run list --repo huyneo1101-dotcom/diem-tin-the-gioi --limit 3 --json createdAt,event,name
```

---

## Khi nào biết là hỏng

- **401 Bad credentials** — token sai, hoặc quên chữ `Bearer ` trước token.
- **403 Forbidden** — thiếu header `User-Agent`, hoặc token không có quyền `Actions: write`,
  hoặc token hết hạn.
- **404 Not Found** — sai tên repo hoặc sai tên file workflow (phân biệt hoa thường).
- **422 Unprocessable** — thiếu `{"ref":"main"}` trong body, hoặc workflow chưa có
  `workflow_dispatch:` trong phần `on:` (cả 3 workflow trên đều đã có).

cron-job.org lưu lịch sử từng lần gọi kèm mã lỗi — vào job → tab **History** là thấy.

## Lưu ý vận hành

- **Token hết hạn là chuỗi quét chết câm.** Nếu đặt 1 năm, ghi luôn vào lịch một nhắc nhở
  trước ngày hết hạn. Đây là kiểu hỏng tệ nhất: không báo lỗi, chỉ đơn giản không có bản tin.
- cron-job.org tự **tắt job** sau nhiều lần lỗi liên tiếp — nên nếu bản tin biến mất vài ngày,
  chỗ đầu tiên phải xem là job còn `enabled` không.
- Đừng xoá cron GitHub. Nó trễ nhưng vẫn là lớp thứ hai miễn phí, và khoá idempotent lo phần
  chống quét chồng.
