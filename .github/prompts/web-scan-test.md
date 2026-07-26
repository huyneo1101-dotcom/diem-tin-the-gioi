Mày là PHIÊN TEST HẠ TẦNG CI của "Điểm Tin Thế Giới" (chạy tay trong GITHUB ACTIONS, mode=test). Mục tiêu: chứng minh trọn pipeline claim → quét → add_news → commit → push với chi phí NHỎ NHẤT — không phải ra bản tin đầy đủ.

## MÔI TRƯỜNG CI
- cwd = repo root diem-tin-the-gioi (đã checkout). Mọi đường dẫn RELATIVE: `python3 scripts/x.py`, `git add ...` — KHÔNG dùng `/Users/Huy/...`, KHÔNG `git -C`.
- Giờ hệ thống là UTC; ngày/giờ VN lấy bằng `TZ='Asia/Ho_Chi_Minh' date +%F` / `+%H:%M`.
- Git identity + quyền push có sẵn, push thẳng `origin main`.
- MỌI lệnh Bash phải PHẲNG: lệnh đơn / pipe / chuỗi `&&`, đối số giá trị thật. KHÔNG for/while, KHÔNG biến shell `$x`/`$(...)`, KHÔNG heredoc, KHÔNG hàm — lệnh ngoài allowlist bị từ chối tự động.
- Ghi log bằng tool Write/Edit vào `logs/scan-<ngày VN>.log`.

## VIỆC (BẢN TEST — GỌN)
1. `git pull --rebase origin main` rồi `python3 scripts/state.py claim web-scan`. exit 10/11 → ghi log SKIP, commit + push log, KẾT THÚC ÊM. exit 0 → tiếp.
2. Ghi `[<giờ>Z] START (CI TEST)` vào log, commit + push ngay.
3. Quét NHẸ: giao **1 agent duy nhất** (tool Agent, model "sonnet") tìm **3 tin** (tối thiểu 2, tối đa 4) trong 24–48h thuộc 2 chủ đề dễ có bài: **CNQS Mỹ** (usNews, category `Công nghệ quân sự`) và **Úc & Biển Đông** (worldNews, region `Ấn Độ Dương - Thái Bình Dương` hoặc `Đông Á`). Nhúng nguyên output `python3 scripts/add_news.py --recent-titles 20` vào prompt agent để chống trùng. CHUẨN CHẤT LƯỢNG GIỮ NGUYÊN: `date` trong 2 ngày gần nhất, `sourceUrl` trỏ thẳng bài thật (không trang chủ/live-blog), không bịa — thà 2 tin sạch còn hơn 4 tin ẩu. KHÔNG quét 5 chủ đề, KHÔNG vòng bổ sung, KHÔNG Báo Mới/xNews/sự kiện/dossier.
4. Gộp `/tmp/new_items.json` (chỉ khoá `date` + `worldNews`/`usNews`) rồi `python3 scripts/add_news.py /tmp/new_items.json`. Script chặn thì sửa/bỏ tin lỗi rồi chạy lại.
5. Kết thúc: `python3 scripts/state.py done web-scan "+N tin (QUET TEST CI)"` (agent trả rỗng thì `skip`). Commit ĐÚNG MẪU: `Cap nhat ban tin DD/MM: +N tin (QUET TEST TU DONG)` — `git add index.html logs/` rồi push; push bị từ chối → `git pull --rebase origin main` rồi push lại.
6. Báo cáo cuối 2-3 câu: mấy tin, chủ đề gì, push chưa.
