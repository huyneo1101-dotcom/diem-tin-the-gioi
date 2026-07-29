# Routine EVENT-SCAN — ĐÃ GỘP vào routine-web-scan.md (28/07/2026)

> Chỉ thị Huy 28/07/2026: *"sự kiện sáng thì quét gộp với quét tin 4h sáng cũng được."*
>
> Pipeline `event-scan` (sự kiện ngoại giao + tập trận + think-tank + báo cáo tuần Chủ nhật) **không
> còn là phiên quét riêng**. Nó nay chạy NGAY SAU bản tin 5 chủ đề, trong CÙNG một session của phiên
> SÁNG SỚM (`web-scan`, ô khoá `sang`) — xem **`docs/routine-web-scan.md` → "Bước 4 — CHỈ PHIÊN SÁNG
> SỚM: gộp thêm sự kiện + tập trận + think-tank"**.
>
> Đã xoá/tắt: workflow `.github/workflows/claude-event-scan.yml` (xoá khỏi repo), task local
> `event-scan-diem-tin` (tắt `enabled: false`, không xoá — dễ khôi phục nếu cần tách lại). Cron
> ngoài `cron-job.org` job "sự kiện SÁNG" trỏ `claude-event-scan.yml` cũng thành job chết — Huy cần
> tự tắt/xoá trên trang cron-job.org (ngoài tầm với của Zim, xem `docs/cron-ngoai.md`).
>
> **Sửa quy trình pipeline `event-scan` thì sửa Bước 4 trong `docs/routine-web-scan.md`, ĐỪNG sửa file
> này.** File này giữ lại chỉ để tra cứu lịch sử/git blame — nội dung quy trình đầy đủ đã dời sang đó
> nguyên vẹn, không có gì bị bỏ sót khi gộp.
