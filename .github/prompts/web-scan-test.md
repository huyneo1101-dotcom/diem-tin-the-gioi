Mày là PHIÊN TEST HẠ TẦNG CI của "Điểm Tin Thế Giới" (chạy tay trong GITHUB ACTIONS, mode=test). Mục tiêu: chứng minh trọn pipeline claim → quét → add_news → commit → push với chi phí NHỎ NHẤT — không phải ra bản tin đầy đủ.

## MÔI TRƯỜNG CI
- cwd = repo root diem-tin-the-gioi (đã checkout). Mọi đường dẫn RELATIVE: `python3 scripts/x.py`, `git add ...` — KHÔNG dùng `/Users/Huy/...`, KHÔNG `git -C`.
- Giờ hệ thống là UTC; ngày/giờ VN lấy bằng `TZ='Asia/Ho_Chi_Minh' date +%F` / `+%H:%M`.
- Git identity + quyền push có sẵn, push thẳng `origin main`.
- MỌI lệnh Bash phải PHẲNG: lệnh đơn / pipe / chuỗi `&&`, đối số giá trị thật. KHÔNG for/while, KHÔNG biến shell `$x`/`$(...)`, KHÔNG heredoc, KHÔNG hàm — lệnh ngoài allowlist bị từ chối tự động.
- Ghi log bằng tool Write/Edit vào `logs/scan-<ngày VN>.log`.

## VIỆC (BẢN TEST — GỌN)
🔒 **PHIÊN NÀY KHÔNG ĐƯỢC ĐỂ DẤU VẾT LÊN BẢN THẬT.** Workflow đã đặt sẵn `DIEMTIN_PHIEN_TEST=1` nên `state.py` tự ghi vào `logs/state-test.json`, KHÔNG chiếm ô khoá của bản tin thật — lệnh vẫn gõ y như phiên thường, không phải thêm gì. Mọi lệnh `state.py` phải in dòng `⚠️ PHIEN TEST … KHONG dung cham co that`; **KHÔNG thấy dòng đó thì DỪNG NGAY**, ghi log FAIL rồi kết thúc — biến môi trường đã rơi mất, chạy tiếp là chiếm ô khoá của bản tin tối (đúng sự cố 29/07/2026). ⛔ TUYỆT ĐỐI KHÔNG tự `unset`/đổi biến đó, KHÔNG sửa tay `logs/state.json`, KHÔNG truyền `tu_dong=1` khi kích notify.

1. `git pull --rebase origin main` rồi `python3 scripts/state.py claim web-scan`. exit 10/11 → ghi log SKIP, commit + push log, KẾT THÚC ÊM. exit 0 → tiếp.
2. Ghi `[<giờ>Z] START (CI TEST)` vào log, commit + push ngay.
3. Quét NHẸ: giao **1 agent duy nhất** (tool Agent, model "sonnet") tìm **3 tin** (tối thiểu 2, tối đa 4) trong khung **48h** (hôm nay + hôm qua giờ VN) thuộc **BẤT KỲ chủ đề nào hợp gu web** — khí tài/CNQS (mọi nước), AUKUS/QP Úc, Biển Đông, hiệp định/khuôn khổ an ninh-QP, kinh tế vĩ mô định chế, chính trị thể chế/ngân sách QP — bỏ vào `worldNews` hoặc `usNews` với category đúng. Nhúng nguyên output `python3 scripts/add_news.py --recent-titles 20` vào prompt agent để chống trùng. Gợi ý nguồn nhiều bài cuối tuần: The Guardian World, DVIDS, The War Zone, Defense News, SCMP, Nikkei Asia, Al Jazeera, BBC World. CHUẨN CHẤT LƯỢNG GIỮ NGUYÊN: `date` trong 2 ngày gần nhất, `sourceUrl` trỏ thẳng bài thật (không trang chủ/live-blog), không bịa — thà 2 tin sạch còn hơn 4 tin ẩu. Ứng viên bị trùng thì cho agent tìm lại với nguồn KHÁC, tối đa 3 vòng. KHÔNG quét 5 chủ đề, KHÔNG Báo Mới/xNews/sự kiện/dossier.
4. Gộp `/tmp/new_items.json` (chỉ khoá `date` + `worldNews`/`usNews`) rồi `python3 scripts/add_news.py /tmp/new_items.json`. Script chặn thì sửa/bỏ tin lỗi rồi chạy lại.
5. Kết thúc: `python3 scripts/state.py done web-scan "+N tin (QUET TEST CI)"` (agent trả rỗng thì `skip`). Commit ĐÚNG MẪU: `Cap nhat ban tin DD/MM: +N tin (QUET TEST TU DONG)` — `git add index.html logs/` rồi push; push bị từ chối → `git pull --rebase origin main` rồi push lại.
6. Báo cáo cuối 2-3 câu: mấy tin, chủ đề gì, push chưa.
