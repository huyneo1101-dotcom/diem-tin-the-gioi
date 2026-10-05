# Quy trình EVENT-SCAN (Bước 4 của phiên SÁNG SỚM)

Dời NGUYÊN VĂN từ `docs/routine-web-scan.md` mục "Bước 4" ngày 05/10/2026 để phiên khởi động khỏi đọc 12 KB chỉ cần SAU khi bản tin 5 chủ đề xong (và phiên SKIP/nhường thì không cần). **Sửa quy trình event-scan thì sửa file NÀY.**

---

## Bước 4 — CHỈ PHIÊN SÁNG SỚM: gộp thêm sự kiện + tập trận + think-tank (gộp 28/07/2026)

> **Chỉ thị Huy 28/07/2026:** *"sự kiện sáng thì quét gộp với quét tin 4h sáng cũng được."* Trước đây
> đây là pipeline `event-scan` RIÊNG (CI `claude-event-scan.yml` 08:45/09:45 + task local
> `event-scan-diem-tin` 09:15/10:15) — 3 lần quét thật/ngày. Từ 28/07/2026 chỉ còn **2 lần quét
> thật/ngày**: phiên TỐI (bản tin 5 chủ đề) và phiên SÁNG SỚM (bản tin 5 chủ đề **+ sự kiện/tập
> trận/think-tank ngay trong CÙNG một phiên**). `claude-event-scan.yml` và task `event-scan-diem-tin`
> đã bị xoá/tắt — ĐỪNG dựng lại, đừng kích tay chúng.

**CHỈ chạy bước này khi phiên vừa xong ở TRÊN là phiên SÁNG SỚM** (giờ VN lúc bắt đầu < 14:00 —
đúng ô `state.py` đã tự suy ở Bước 1). Phiên TỐI **KHÔNG** làm bước này, dừng lại ở Bước 3.

⛔ **event-scan KHÔNG CÓ HẠN CHÓT** — `HAN_CHOT` 04:45 chỉ áp cho bản tin; event-scan chạy tới hết
khung ca sáng (09:00). `state.py skip event-scan` TỪ CHỐI (exit 13) mọi ghi chú viện cớ giờ/hạn chót
(vấp thật 25/09/2026, bộ test `tests/test-cong-event-han-chot.py`).

Đây là **pipeline THỨ HAI, khoá RIÊNG** (`event-scan`, khác `web-scan` ở Bước 1-3) — vẫn `claim` riêng,
`done`/`skip`/`fail` riêng, và **commit RIÊNG** (không gộp chung commit bản tin), vì `notify-morning.yml`
chỉ bắt tiền tố commit của pipeline này. Lý do giữ tách: `state.py`/`canary.py`/`notify-morning.yml`
đều phân biệt hai pipeline theo tên — gộp làm một sẽ vỡ cả khoá idempotent lẫn cổng gửi email/Telegram
sự kiện riêng (🎖️ khác 📰). Chỉ có **nơi kích** là gộp lại (chung 1 phiên/session), không phải **cơ chế**.

### 4.1 — Đồng bộ + giành khoá pipeline `event-scan`
```
git -C /Users/Huy/Claude/diem-tin-the-gioi pull --rebase origin main
python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/state.py claim event-scan
```
⛔ `cannot pull with rebase: You have unstaged changes` → xử theo đúng bảng ở **Bước 1** (fetch +
`rev-list --count HEAD..origin/main`; ra 0 thì ĐI TIẾP). Đừng dừng phiên, đừng stash, đừng commit hộ.
SKIP exit 10 = sáng nay đã xong (có thể do CI/local khác vừa chạy) — ghi 1 dòng SKIP vào log, commit +
push log, DỪNG bước này (phiên vẫn coi là hoàn tất bình thường, vì bản tin 5 chủ đề ở Bước 1-3 đã xong).
SKIP exit 11 = phiên khác đang giữ khoá `event-scan` — cũng SKIP êm, không chờ, không Monitor.
RUN exit 0 = giữ khoá, làm tiếp.

### 4.2a — Dò cuộc tập trận CÒN THIẾU trong `DATA.exercises` (thêm 07/08/2026)
```
python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/do_tap_tran_thieu.py
```
**Vì sao phải có bước này, và vì sao nó đứng TRƯỚC 4.2:** bước 4.2 giao agent tìm *"diễn biến tập
trận"*, mà `tap_tran.py` sinh từ khoá từ chính `DATA.exercises` — tức chỉ đi tìm tin cho cuộc ĐÃ CÓ
TÊN. Cuộc chưa có trong danh sách thì không ai tìm, không ai tìm thì không bao giờ vào danh sách. Đo
07/08/2026: `DATA.exercises` có 10 cuộc, một lượt đọc tay tìm ra **14 cuộc thiếu, 04 cuộc đang chạy
đúng hôm đó**. Script này hỏi ngược lại — *"tháng này Nhật và Philippines có tập chung gì không"* —
nên bắt được cả cuộc chưa ai đặt tên vào danh sách.

Đầu ra **02 nhóm**, xử lý khác nhau:
- **★ CÓ TÊN RIÊNG** → xác minh nguồn rồi nạp thẻ mới bằng `add_news.py` khoá `newExercises`, gộp
  luôn vào `/tmp/new_items_event.json` của bước 4.2.
- **○ KHÔNG TÊN CHUỖI** → hoạt động chung ngắn ngày (tuần tra ba bên, diễn tập hàng hải một lượt).
  Đọc tay: đáng thành thẻ thì nạp, không thì bỏ qua. **Đây là nhóm mà bảng chuỗi tập trận vốn mù**,
  đừng bỏ qua cả nhóm cho nhanh.

⚠️ **Chạy ~3–4 phút (28 truy vấn Google News), KHÔNG phải cổng chặn.** Script luôn trả mã 0; hỏng thì
in cảnh báo rồi thôi. Quá giờ hoặc mạng trục trặc thì bỏ bước này, ghi một dòng vào log, đi tiếp 4.2 —
mất một bước phụ còn hơn trễ bản tin.
⚠️ **Tin về cuộc ĐÃ CÓ mà tiêu đề không nêu tên cuộc sẽ rơi vào nhóm ○** (ví dụ *"S. Korean Air Force
joins multinational exercise in Australia"* là Pitch Black). Đây là giới hạn đã biết của phép khớp
theo tên, không phải lỗi — đọc thấy thì bỏ qua.
⚠️ Sổ `logs/tap-tran-da-soi.json` giữ 14 ngày để khỏi báo lại tin đã đọc; muốn xem lại từ đầu thì
thêm `--khong-so`. **Phải `git add logs/` cùng lô** như mọi sổ khác.

### 4.2 — Quét sự kiện + tập trận
Giao agent (tool Agent, `model: "sonnet"`): nhúng nguyên output
`python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/add_news.py --recent-titles 20` để chống trùng;
tìm **sự kiện ngoại giao có ký kết** trong 48h + **diễn biến tập trận** + tin liên quan (`relate`, đăng
trong 48h). Gộp `/tmp/new_items_event.json` (chỉ khoá `newDipEvents`/`dipEventUpdates`/`newExercises`/
`exerciseUpdates` + `date`) rồi `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/add_news.py /tmp/new_items_event.json`.
Nhịp tim: `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/beat_push.py event-scan` — ⛔ KHÔNG
`state.py beat` trần (vá 20/09/2026, xem Bước 2 phía trên). Beat NGAY
TRƯỚC khi giao agent (không đợi agent xong), hai nhịp liên tiếp không cách quá ~15 phút (cùng bài học
vá 28/07/2026 đã áp cho pipeline `web-scan` ở Bước 2).

### 4.3 — Bối cảnh + khái niệm tập trận
Với **mỗi cuộc tập trận MỚI vừa tạo** (`newExercises`) VÀ **mỗi cuộc đang diễn ra CHƯA có `background`**,
giao agent Sonnet viết `background` (2–4 câu bối cảnh chiến lược, nhiều đoạn ngăn `\n`) + `concepts`
(3–6 thuật ngữ, `[{term,def}]`, def 1 câu). Ghi `/tmp/briefing.json` =
`[{"name":"<khớp đúng name>","background":"...","concepts":[...]}]` rồi
`python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/set_exercise_briefing.py /tmp/briefing.json`.
Không viết lại cho cuộc đã có background trừ khi diễn biến đổi bối cảnh lớn.

### 4.4 — Bài phân tích think-tank (mỗi phiên sáng sớm, không chỉ Chủ nhật)
Mục 🧠 Phân tích → 🏛️ Think-tank (`DATA.analyses`).
1. `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/add_analyses.py --candidates` — ứng viên
   **hai lớp**, xếp theo khu vực: `[RSS]` 27 viện có feed, rồi `[HTML]` 10 viện không có feed nhưng
   quét được trang danh sách (thêm 30/07/2026 — đo lần đầu: 159 + 44 ứng viên). Dòng cuối in vùng
   **vẫn** phải bù bằng `WebSearch site:<domain>`, đã trừ sẵn nguồn hai lớp trên đã phủ.
   - Thấy dòng ⚠️ *"Trang HTML KHÔNG ra link bài nào"* → viện đó đổi giao diện, biểu thức đường dẫn
     đã chết. Chạy `add_analyses.py --kiem-html` để soi rồi sửa `THINKTANK_HTML`; **đừng đọc thành
     "hôm nay viện không ra bài"**, hai ca đó khác nhau và script đã tách riêng thông điệp.
   - Ứng viên `[HTML]` có ngày lấy từ trang danh sách hoặc từ meta trang bài. Vẫn phải MỞ ĐỌC như
     mọi ứng viên khác ở bước 2 — bước đó tự xác nhận lại ngày.
2. Giao agent Sonnet chọn **4–6 bài**, phủ **ít nhất 2–3 khu vực khác nhau** (1–2 bài trọng tâm cũ:
   Úc/AUKUS · Biển Đông · răn đe hạt nhân/CNQS · Mỹ–Trung–Đài Loan · Mali/Sahel; 1–2 bài vùng khác
   đang có chuyện). LOẠI: chính trị xã hội nội bộ Mỹ, quảng bá viện, điểm sách, điểm báo. Agent phải
   MỞ ĐỌC từng bài (WebFetch) rồi viết tiếng Việt đủ field (`title`/`summary`/`takeaway`/`topic`/
   `region`/`author`/`outlet`/`date`). Số liệu mập mờ/lỗi ký tự → BỎ, không đoán.
3. Ghi `/tmp/analyses.json` = `{"date":"<hôm nay VN>","analyses":[...]}` rồi
   `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/add_analyses.py /tmp/analyses.json`.
4. **SINH KHÁI NIỆM cho đúng những bài vừa nạp** (thêm 29/07/2026, chỉ thị Huy) — mục 📚 Khái niệm
   gom khái niệm từ CẢ tập trận lẫn think-tank, mà bài viện nghiên cứu mới là chỗ thuật ngữ lạ dày
   nhất. Với mỗi bài vừa nạp, rút **1–3 thuật ngữ** người đọc phổ thông không hiểu ngay (học thuyết,
   cơ chế, hiệp định, khí tài, chiến thuật), viết định nghĩa **tiếng Việt 1–3 câu tự nó đứng được**
   — đọc riêng dòng đó vẫn hiểu, không cần mở bài. Ghi `/tmp/kn-analyses.json`:
   ```
   [{"url":"<url ĐÚNG như vừa nạp>","concepts":[{"term":"...","def":"..."}]}]
   ```
   rồi `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/set_analysis_concepts.py /tmp/kn-analyses.json`.
   - **Bài không có thuật ngữ nào đáng lưu thì BỎ QUA bài đó** — sổ tay là để lọc, nhồi cho đủ số là
     làm hỏng chính tác dụng của nó. Guardrail chặn lô rỗng nên đừng khai `"concepts":[]`, cứ bỏ hẳn
     mục đó ra khỏi mảng.
   - Guardrail CHẶN: url không có trong DATA · thiếu `term`/`def` · `def` dưới 40 ký tự · `term` quá
     90 ký tự · hai `term` trùng nhau trong cùng bài · quá 6 khái niệm/bài. Đọc lỗi rồi sửa JSON.
   - Trùng khái niệm với bài khác hoặc với tập trận thì **KHÔNG sao** — web dùng chung kho
     `dt.concepts` và tự khử trùng theo tên đã bỏ dấu.
   - Kiểm còn bài nào chưa có: `python3 .../set_analysis_concepts.py --kiem`.

### 4.5 — Chủ nhật: báo cáo tuần Mỹ-Trung-Nga
Chỉ khi `TZ='Asia/Ho_Chi_Minh' date +%u` in ra `7`:
```
python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/weekly_context.py --out /tmp/weekly_ctx.json
```
Giao 1 agent **model: "opus"** (BẮT BUỘC Opus): đọc `/tmp/weekly_ctx.json`, viết nhận định tuần 3 nước
(mỗi nước lede + 3–5 luận điểm, mỗi luận điểm 1–3 link nội dòng markdown `[cụm chữ](url-thật-trong-ngữ-liệu)`
— không bịa url). Ghi `/tmp/weekly.json` đúng schema `scripts/add_weekly.py` (thứ tự us→cn→ru, KHÔNG
kèm `generatedAt`) rồi `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/add_weekly.py /tmp/weekly.json`.

### 4.6 — Kết thúc pipeline `event-scan` (LUÔN một trong ba)
- Nạp được: `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/state.py done event-scan "<tóm tắt>"`
- Rỗng: `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/state.py skip event-scan "<lý do>"`
- Lỗi: `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/state.py fail event-scan "<lý do>"` (vẫn push log)

Commit message QUYẾT ĐỊNH email sáng riêng (`notify-morning.yml` bắt tiền tố — KHÁC tiền tố
`Cap nhat ban tin` của Bước 3):
- Có sự kiện/tập trận: `Cap nhat su kien DD/MM: +N su kien/tap tran[, +M bai think-tank][, bao cao tuan]`
- CHỈ báo cáo tuần: `Dang bao cao tuan DD/MM`
- CHỈ think-tank: vẫn `Cap nhat su kien DD/MM: +M bai think-tank` — đã tính vào gate email sáng.
- Rỗng thật: message tự do, KHÔNG dùng 2 tiền tố trên.

`git -C /Users/Huy/Claude/diem-tin-the-gioi add index.html data/ logs/` (phải có `logs/state.json`; **`data/` là BẮT BUỘC** — bài think-tank nằm ở `data/analyses.json` từ 30/07/2026, bỏ sót thì bài nạp xong KHÔNG lên web mà cũng không có lỗi nào) → commit
**RIÊNG với commit bản tin của Bước 3** → push. Bị từ chối → `pull --rebase` rồi push lại.

Báo cáo cuối (gộp vào báo cáo cuối chung của phiên): số sự kiện mới/cập nhật, số tập trận cập nhật, có
báo cáo tuần không (nếu CN), trạng thái push của CẢ HAI commit (bản tin + sự kiện).
