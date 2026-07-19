# Đồng bộ "Bài đã lưu" từ Báo Mới

Tự động kéo danh sách bài bạn đã lưu (bookmark) trong tài khoản Báo Mới về web,
kèm phân tích sở thích. Chạy hằng ngày bằng GitHub Action (không đụng tới quy
trình quét tin thế giới).

## Thành phần

| File | Vai trò |
|---|---|
| `scripts/baomoi_sync.py` | Fetch danh sách đã lưu + chuẩn hoá + phân tích sở thích |
| `.github/workflows/sync-baomoi.yml` | Chạy script hằng ngày (17:30 giờ VN), commit nếu đổi |
| `baomoi-saved.json` | Danh sách bài đã lưu (web đọc để hiển thị tab **📌 Báo Mới**) |
| `baomoi-analysis.json` | Phân tích: phân bổ chủ đề, nguồn hay lưu, từ khoá |
| `baomoi-preferences.md` | Bản phân tích dạng đọc được cho người |

## Cách hoạt động

Endpoint: `https://w-api.baomoi.com/api/v1/user/get/contents-by-type?listType=3`
(`listType=3` = danh sách đã lưu). Đã kiểm chứng thực nghiệm (18/07/2026):
server **không kiểm tra tham số `sig`** — chỉ cần **cookie đăng nhập** hợp lệ.
Vì vậy script dùng `ctime` hiện tại + một `sig` bất kỳ; thứ duy nhất cần giữ là cookie.

## Bí mật cần cấu hình: `BAOMOI_COOKIE`

Cookie đăng nhập Báo Mới, lưu ở **Settings → Secrets and variables → Actions →
New repository secret**, tên `BAOMOI_COOKIE`. Giá trị là **toàn bộ chuỗi cookie**
(gồm `bmsid=...` là quan trọng nhất) lấy từ một request đã đăng nhập.

> ⚠️ KHÔNG commit cookie vào repo. Nó chỉ nằm trong GitHub Secret.

## Khi Action báo lỗi -801 (cookie hết hạn) — cách làm mới cookie

Session đăng nhập Báo Mới hết hạn theo chu kỳ. Khi đó Action fail với thông báo
`err -801 / "Bạn cần đăng nhập..."`. Làm mới:

1. Mở `https://baomoi.com` trên máy tính, **đăng nhập lại**.
2. F12 → tab **Network** → lọc **Fetch/XHR** → vào trang **Đã lưu** (hoặc F5).
3. Tìm request `contents-by-type?listType=3` → chuột phải → **Copy → Copy as cURL**.
4. Lấy phần trong `-b '...'` (chuỗi cookie) → cập nhật lại secret `BAOMOI_COOKIE`.
5. Vào tab **Actions** → workflow **Sync Baomoi saved articles** → **Run workflow**
   để chạy lại ngay (không cần chờ tới 17:30).

## Lịch chạy & phạm vi

- Cron `30 10 * * *` (17:30 giờ VN) + chạy tay qua **Run workflow**.
- Lịch chỉ kích hoạt khi workflow nằm trên nhánh mặc định (`main`).
- Web chỉ hiển thị dữ liệu mới sau khi nhánh được **merge lên `main`** (GitHub Pages
  deploy từ `main`).

## Hiển thị trên web

Tab **📌 Báo Mới** trong `index.html`: fetch `baomoi-saved.json` +
`baomoi-analysis.json` lúc tải trang, hiện tóm tắt sở thích (biểu đồ phân bổ chủ đề,
từ khoá) + danh sách bài, lọc theo chủ đề và ô tìm kiếm chung.
