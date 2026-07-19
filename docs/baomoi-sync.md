# Đồng bộ "Bài đã lưu" từ Báo Mới → luồng tin

Tự động lấy danh sách bài bạn đã lưu (bookmark) trong tài khoản Báo Mới, **lọc chỉ
giữ bài đúng 4 chủ đề của web** (Kinh tế · Chính trị · Công nghệ quân sự · Ngoại
giao), rồi **trộn thẳng vào luồng tin** của web (hiện trong tab **🆕 Bài mới** và
**🌍 Thế giới**, có gắn nhãn **📌 Đã lưu**). Bài ngoài chủ đề (thể thao, giải trí,
sức khỏe, gia đình, tâm lý…) bị loại. **Không có tab riêng, không phân tích sở thích.**

## Thành phần

| File | Vai trò |
|---|---|
| `scripts/baomoi_sync.py` | Fetch bài đã lưu, lọc đúng 4 chủ đề, xuất `baomoi-saved.json` (dạng tin) |
| `.github/workflows/sync-baomoi.yml` | Chạy script hằng ngày (17:30 giờ VN), commit nếu đổi |
| `baomoi-saved.json` | Danh sách bài đã lọc; web fetch lúc tải trang và trộn vào `DATA.worldNews` |

## Cách hoạt động

Endpoint: `https://w-api.baomoi.com/api/v1/user/get/contents-by-type?listType=3`
(`listType=3` = danh sách đã lưu). Đã kiểm chứng (18/07/2026): server **không kiểm
tra tham số `sig`** — chỉ cần **cookie đăng nhập** hợp lệ.

Web (`index.html`, hàm `loadBaomoi`) fetch `baomoi-saved.json` lúc tải trang, bỏ tin
trùng tiêu đề với tin đã có, rồi nối vào `DATA.worldNews` → tự hiện trong các tab tin
thường (kèm nhãn 📌 Đã lưu). Không đụng tới quy trình quét tin.

## Bí mật cần cấu hình: `BAOMOI_COOKIE`

Cookie đăng nhập Báo Mới, lưu ở **Settings → Secrets and variables → Actions →
New repository secret**, tên `BAOMOI_COOKIE`, giá trị là **toàn bộ chuỗi cookie**
(gồm `bmsid=...`) từ một request đã đăng nhập. **KHÔNG commit cookie vào repo.**

## Khi Action báo lỗi -801 (cookie hết hạn) — làm mới cookie

1. Mở `https://baomoi.com` trên máy tính, **đăng nhập lại**.
2. F12 → **Network** → lọc **Fetch/XHR** → vào trang **Đã lưu** (hoặc F5).
3. Tìm request `contents-by-type?listType=3` → chuột phải → **Copy → Copy as cURL**.
4. Lấy phần trong `-b '...'` (chuỗi cookie) → cập nhật lại secret `BAOMOI_COOKIE`.
5. Tab **Actions** → **Sync Baomoi saved articles** → **Run workflow** để chạy lại ngay.

## Lịch chạy

- Cron `30 10 * * *` (17:30 giờ VN) + **Run workflow** thủ công.
- Lịch chỉ chạy khi workflow ở nhánh mặc định (`main`).
- Web chỉ cập nhật sau khi nhánh được merge lên `main` (GitHub Pages deploy từ `main`).

## Điều chỉnh bộ lọc chủ đề

Từ khoá 4 chủ đề nằm trong `CAT4` ở đầu `scripts/baomoi_sync.py`. Muốn giữ/loại thêm
loại bài nào thì thêm/bớt từ khoá tương ứng; bài không khớp chủ đề nào sẽ bị bỏ.
