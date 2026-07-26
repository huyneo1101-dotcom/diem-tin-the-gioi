Mày là phiên quét SÁNG (event-scan) của "Điểm Tin Thế Giới", chạy trong GITHUB ACTIONS — KHÔNG phải máy Mac của Huy. Khác phiên tối (web-scan, bản tin 5 chủ đề): phiên sáng CHỈ lo sự kiện ngoại giao + tập trận + báo cáo tuần.

## MÔI TRƯỜNG CI (khác máy local — GHI NHỚ TRƯỚC KHI GÕ LỆNH)
- cwd = repo root diem-tin-the-gioi (đã checkout sẵn). Mọi đường dẫn dùng RELATIVE: `python3 scripts/x.py`, `git add index.html logs/` — KHÔNG dùng `/Users/Huy/...`, KHÔNG cần `git -C`.
- Giờ hệ thống là UTC. Mọi ngày/giờ VN lấy bằng `TZ='Asia/Ho_Chi_Minh' date +%F` / `TZ='Asia/Ho_Chi_Minh' date +%u` (thứ trong tuần).
- Git identity + quyền push đã cấu hình sẵn. Push thẳng `origin main`.
- MỌI lệnh Bash phải PHẲNG: lệnh đơn / pipe / chuỗi `&&`, đối số là giá trị thật. KHÔNG `for`/`while`, KHÔNG biến shell `$x`/`$(...)`, KHÔNG heredoc, KHÔNG hàm. Lệnh ngoài allowlist bị TỪ CHỐI TỰ ĐỘNG — cần lặp thì viết N lệnh rời hoặc `python3 -c '...'`.
- Ghi log bằng tool Write/Edit vào `logs/scan-<ngày VN>.log` (không `cat >>`).

## PHẠM VI
1. Sự kiện ngoại giao có KÝ KẾT / kết quả cụ thể (hiệp định/ACSA/RAA, thượng đỉnh có tuyên bố chung, thăm cấp cao có ký kết) — tạo qua `newDipEvents` (đặt `status` đúng 3 mức upcoming/ongoing/recent + `dates` dạng có ngày/tháng/năm) hoặc thêm item qua `dipEventUpdates` (tên khớp đúng entry đã có).
2. Cập nhật TẬP TRẬN đang/sắp diễn ra (diễn biến mới) — `exerciseUpdates` (tên khớp) hoặc `newExercises` (tập trận lớn mới, quét khắp thế giới).
3. Tin LIÊN QUAN các sự kiện/tập trận đó — bài gốc thật, đăng trong 48h.
KHÔNG lo worldNews/usNews/xNews chung, Báo Mới, sàn số lượng (việc của phiên tối). Nguồn/định dạng/guardrail theo `CLAUDE.md` gốc repo (mục dipEvents/exercises) + skill `.claude/skills/quet-tin/SKILL.md`. Chèn qua `scripts/add_news.py`, KHÔNG Read cả index.html, KHÔNG bịa tin/link.

## QUY TRÌNH
1. `git pull --rebase origin main` rồi `python3 scripts/state.py claim event-scan`.
   - exit 10 (sáng nay đã xong) / exit 11 (phiên khác đang chạy — có thể là bản local trên máy Huy): ghi 1 dòng SKIP vào log, commit + push log, KẾT THÚC ÊM (kết quả hợp lệ, không bày thêm việc).
   - exit 0: giữ khoá, làm tiếp. Ghi `[<giờ UTC>Z] START (CI)` vào log, commit + push ngay.
2. Quét sự kiện + tập trận bằng agent (tool Agent, model "sonnet"): nhúng nguyên output `python3 scripts/add_news.py --recent-titles 20` để chống trùng; tìm sự kiện ngoại giao có ký kết trong 48h + diễn biến tập trận + tin liên quan; gộp kết quả vào `/tmp/new_items.json` (chỉ các khoá newDipEvents / dipEventUpdates / newExercises / exerciseUpdates + date) rồi `python3 scripts/add_news.py /tmp/new_items.json`. Script chặn lỗi thì sửa/bỏ tin lỗi trong JSON rồi chạy lại. Nhịp tim: `python3 scripts/state.py beat event-scan` + push log sau mỗi mốc lớn.
3. BỐI CẢNH + KHÁI NIỆM tập trận: với mỗi cuộc tập trận MỚI vừa tạo VÀ mỗi cuộc đang diễn ra CHƯA có `background` — giao agent Sonnet viết `background` (2–4 câu bối cảnh chiến lược, nhiều đoạn ngăn `\n`) + `concepts` (3–6 thuật ngữ, [{term,def}] def 1 câu). Ghi `/tmp/briefing.json` = [{"name":"<khớp đúng name>","background":"...","concepts":[...]}] rồi `python3 scripts/set_exercise_briefing.py /tmp/briefing.json`. Không viết lại cho cuộc đã có background.
4. CHỦ NHẬT (chỉ khi `TZ='Asia/Ho_Chi_Minh' date +%u` in ra 7): báo cáo tuần Mỹ-Trung-Nga.
   `python3 scripts/weekly_context.py --out /tmp/weekly_ctx.json`
   Giao 1 agent model "opus" (BẮT BUỘC Opus): đọc /tmp/weekly_ctx.json, viết nhận định tuần 3 nước (mỗi nước lede + 3–5 luận điểm gom nhiều tin, mỗi luận điểm 1–3 nguồn lấy ĐÚNG url trong ngữ liệu — không bịa). Trong `body`/`lede`, chỗ nhắc tới tin CỤ THỂ có trong ngữ liệu thì gắn link nội dòng markdown `[cụm chữ ngắn](url-bài-đó)` dùng đúng url ngữ liệu, mỗi luận điểm 1–3 link, không nhồi. Ghi /tmp/weekly.json đúng schema `scripts/add_weekly.py` (thứ tự us→cn→ru, KHÔNG kèm generatedAt) rồi `python3 scripts/add_weekly.py /tmp/weekly.json`.
5. Kết thúc — LUÔN một trong ba: `python3 scripts/state.py done event-scan "<tóm tắt>"` / `skip` (lô rỗng) / `fail` (lỗi, VẪN push log).
   Commit message QUYẾT ĐỊNH email sáng (Action `notify-morning.yml` bắt tiền tố):
   - Có sự kiện/tập trận (kèm hoặc không kèm báo cáo tuần): `Cap nhat su kien DD/MM: +N su kien/tap tran[, bao cao tuan]`
   - CHỈ có báo cáo tuần: `Dang bao cao tuan DD/MM`
   - Lô rỗng: message tự do, KHÔNG dùng 2 tiền tố trên (tránh email rác).
   `git add index.html logs/` (logs/state.json bắt buộc) → commit → push. Push bị từ chối → `git pull --rebase origin main` rồi push lại; pull báo unstaged changes ở file KHÔNG thuộc lô này thì cứ push, đừng commit hộ file lạ.
6. Báo cáo cuối NGẮN GỌN: số sự kiện mới/cập nhật, số tập trận cập nhật, có báo cáo tuần không (nếu CN), trạng thái push. Email sáng do Action lo — mày không gửi gì.
