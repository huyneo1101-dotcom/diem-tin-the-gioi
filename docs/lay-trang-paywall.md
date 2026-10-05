# Bài dính paywall: thang lấy trang + darkread.io

Dời NGUYÊN VĂN từ bước 2 của `.claude/skills/quet-tin/SKILL.md` ngày 05/10/2026.

---

- **⛔ DÍNH PAYWALL THÌ ĐỌC THỬ BẰNG `darkread.io` TRƯỚC KHI BỎ TIN** (chỉ thị Huy 05/08/2026: *"thêm
  vào quy trình quét tin: dính paywall thì đọc thử bằng darkread.io"*).
  **Cơ chế gây vấp:** thang lấy trang (`congcu/lay_trang.py`) chỉ được `harvest.py` gọi tới khi thân
  trả về mang **dấu hiệu chặn** (403, "just a moment"…). Bài paywall thì ngược lại — máy chủ trả
  **200 kèm vài đoạn đầu**, không dấu hiệu nào, nên thang KHÔNG kích và bài lặng lẽ bị bỏ với lý do
  "không đọc được nội dung". Đây là bước của **agent/người quét**, không phải của script.
  ```bash
  python3 /Users/Huy/Claude/congcu/lay_trang.py <url>
  ```
  Thang nay đi lần lượt `curl_cffi → thu_lai → ua_bot → wayback → darkread`; muốn thử riêng một
  bậc thì thêm `--duong=ua_bot` hoặc `--duong=darkread`.
  - **`ua_bot` = đổi User-Agent sang bot tìm kiếm/mạng xã hội** (Huy chốt 05/08/2026). Đo cùng
    ngày: Japan Times từ **403 → 200 kèm trọn thân bài**; Economist trả thêm khối bài mà trình
    duyệt thường không có (mới là phần đầu); WSJ vẫn 401, FT vẫn ra trang "Subscribe to read".
    ⚠️ Đây là **giả danh bot** — nhiều báo cấm trong điều khoản, lạm dụng thì bị chặn IP; nên nó
    đứng sau các đường thường, đừng gọi thẳng `--duong=ua_bot` cho cả lô.
  - **`archive.today` là công cụ mạnh nhất cho báo trả tiền nhưng KHÔNG tự động hoá được** — script
    nhận 429, trình duyệt trong app đòi bấm duyệt từng thao tác. Mở tay được, đừng cắm vào quy trình.
  - **Khai đúng mức, đừng kỳ vọng sai:** darkread KHÔNG vượt paywall cứng. Đo 05/08/2026 trên 06 bài:
    ăn `japantimes.co.jp` (729 chữ, thang vốn trượt hoàn toàn) · `asia.nikkei.com` chỉ ra phần lead
    (494 chữ) · trượt hẳn ở `wsj.com` · `ft.com` · `economist.com` · `38north.org`. Coi nó là **một
    lượt thử thêm**, không phải cửa mở.
  - **Bản lấy về là BẢN READER RÚT GỌN, có thể chỉ là phần miễn phí** — dùng để đối chiếu dữ kiện thì
    được, nhưng `sourceUrl` vẫn phải là **URL gốc**, tuyệt đối không ghi link `darkread.io` vào tin.
  - ⚠️ **CHỈ chạy được ở phiên LOCAL** — CI checkout đúng repo này, không có `~/Claude/congcu`. Phiên
    CI gặp paywall thì xử như cũ: xác nhận nội dung qua nguồn thứ hai, không được thì bỏ tin.
  - Đo được một tên miền mới đi lọt bằng đường này thì **ghi vào `congcu/bang-tra-web.json`** (khoá
    `duong` thêm `"darkread"`), kẻo phiên sau đo lại từ số không.
