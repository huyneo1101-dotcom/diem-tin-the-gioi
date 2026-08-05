---
name: quet-tin
description: >-
  Playbook NỘI DUNG quét bản tin "Điểm Tin Thế Giới" — 5 chủ đề, kiến trúc agent Sonnet, nguồn 3
  tầng, guardrail add_news.py. Dùng khi người dùng yêu cầu "quét tin", "cập nhật bản tin", "scan
  tin", hoặc khi routine tự động chạy. Bản tin chạy 2 PHIÊN/NGÀY cùng playbook này: TỐI 20:47 +
  SÁNG SỚM 03:47 (giờ VN — bảng lịch thật: docs/LICH.md). 5 chủ đề: Nội bộ Mỹ (5 nhóm, 2 hạng ưu tiên) · Úc & Biển Đông · CNQS Mỹ ·
  Mỹ–Mali · tập trận Predator's Run 2026. LỊCH/khoá/commit/push KHÔNG nằm ở file này — nguồn sự thật
  là docs/routine-web-scan.md; bảng nguồn/RSS xem CLAUDE.md gốc repo.
---

# Skill: Quét tin "Điểm Tin Thế Giới" (bản TẬP TRUNG 5 chủ đề — chỉ thị Huy 2026-07-23)

## 🧭 PHÂN VAI — file này là gì, KHÔNG phải gì (chốt 29/07/2026)
> Ba tài liệu, **mỗi luật chỉ được viết ở ĐÚNG MỘT chỗ**. Sửa nhầm chỗ là đẻ ra hai bộ luật song
> song, và hai bộ luật song song chắc chắn lệch — đúng bệnh đã bắt được ngày 29/07 (file này còn
> ghi "chỉ chạy 1 lần/ngày, TỐI 22:00" trong khi lịch thật đã là 2 phiên/ngày từ 26/07).

| Tài liệu | Giữ luật gì | Ai đọc |
|---|---|---|
| **File này** (`.claude/skills/quet-tin/SKILL.md`) | **NỘI DUNG quét**: 5 chủ đề + tiêu chí lọc · kiến trúc agent · thang xác minh · guardrail `add_news.py` · `scan-gaps.json` · phụ lục nguồn | Phiên local (qua `docs/routine-web-scan.md` Bước 2) **và** phiên CI (qua `.github/prompts/web-scan-ci.md`) |
| `docs/routine-web-scan.md` | **QUY TRÌNH CHẠY**: lịch/mốc giờ · `state.py` claim/beat/done · pull-rebase · commit/push · pipeline `event-scan` phiên sáng | Task local `web-scan-diem-tin` (sáng sớm) + `web-scan-diem-tin-toi` (tối) |
| `CLAUDE.md` gốc repo | **PHẠM VI + NGUỒN**: bảng nguồn 3 tầng, URL RSS, cấu trúc `DATA`, cơ chế email/Telegram | Tự nạp mọi phiên |

⛔ **ĐỪNG rút file này thành stub trỏ sang `routine-web-scan.md`** — file đó **trỏ VÀO đây** ở Bước 2,
và `.github/prompts/web-scan-ci.md` cũng vậy. Trỏ ngược lại là vòng tròn, cả CI lẫn local mất sạch
playbook nội dung.
⛔ **ĐỪNG chép lịch/mốc giờ vào đây.** Cần biết mốc nào, hạn chót nào → đọc `docs/routine-web-scan.md`.
📌 Câu *"SKILL.md của các task giờ chỉ là stub"* trong CLAUDE.md nói về **stub của scheduled task**
(`~/.claude/scheduled-tasks/*/SKILL.md`, 5 dòng, Read file repo) — **KHÔNG phải file này**.

## ⭐ PHẠM VI MỚI (2026-07-23 — GHI ĐÈ mọi mô tả 4-chuyên-mục / sàn 15+15 cũ)
Bản tin chạy **2 phiên/ngày, CÙNG playbook 5 chủ đề này** (mốc giờ cụ thể: `docs/routine-web-scan.md`).
Mỗi phiên **CHỈ quét 5 chủ đề**, **mỗi chủ đề 5–10 bài** (best-effort — thiếu thì thôi, KHÔNG bịa):

1. **Nội bộ Mỹ — 5 NHÓM, HAI HẠNG ƯU TIÊN** (chỉ thị Huy 27/07/2026, GHI ĐÈ mức "SIẾT" cũ) — `usNews`,
   category `Chính trị` (nhóm 4 có thể `Kinh tế`). **BẮT BUỘC vét cạn nhóm (1) TRƯỚC; chỉ khi chưa đủ
   chỉ tiêu 5–10 bài mới lấy sang các nhóm còn lại — và (2)(3)(4)(5) NGANG HÀNG, không có thứ tự giữa
   chúng.** Đừng nhảy cóc bỏ qua nhóm 1, cũng đừng coi nhóm 2 hơn nhóm 5.
   1. **[HẠNG 1] Điều trần + bỏ phiếu** — liệt kê **TOÀN BỘ phiên điều trần trong ngày** (hearing,
      testimony, mark-up, chất vấn quan chức) + **TOÀN BỘ kết quả** hội đồng/uỷ ban/hai viện **bỏ
      phiếu thông qua dự luật** (committee vote, floor vote, passage của bill/nghị quyết/NDAA/ngân sách).
   2. **Sáng kiến & chiến lược chính quyền Trump** công bố trên **kênh chính thống của các bộ**: sắc
      lệnh hành pháp, presidential memorandum, chiến lược quốc gia, fact sheet Nhà Trắng, thông cáo
      của State/Treasury/Commerce/DHS…
   3. **Biểu tình**: diễn biến biểu tình, tuần hành, đình công.
   4. **Kinh tế Mỹ + động thái bộ sậu**: Fed, thuế quan, trừng phạt, số liệu vĩ mô; và các hoạt động
      khác của Nhà Trắng + nội các (Trump và bộ sậu action).
   5. **BẦU CỬ** *(tách riêng 27/07/2026 — trước gộp chung nhóm 3)*: bầu cử giữa nhiệm kỳ, bầu cử sơ
      bộ, tranh cử/vận động, thăm dò dư luận, quy định cử tri, kiểm phiếu, phân định lại khu vực bầu
      cử (redistricting/gerrymander), đua ghế Thượng viện/Hạ viện/thống đốc.
   ⚠️ Nhóm 3, 4, 5 **đảo lại** phần cấm cũ (drama/đảng phái/horserace/biểu tình nay ĐƯỢC nhận) — nhưng
   chỉ khi nhóm 1 đã cạn thật. Số nhóm 2→5 là NHÃN, không phải thứ tự ưu tiên. Và phải là chuyện **NỘI BỘ MỸ**: từ khoá nhóm 3–4 rất chung nên
   `scripts/topics.py` bắt buộc kèm ngữ cảnh Mỹ (`WEAK_NEED_US`) — thực tế đã lọt tin nghị sĩ
   Philippines mặc đồ đen phản đối, chính sách tiền tệ Singapore, chi tiêu vốn Nhật Bản.
2. **Úc & Biển Đông** — `worldNews`. **Úc**: AUKUS, QP/khí tài Úc, ADF, an ninh Úc–Mỹ/Nhật/Anh, chính
   sách Thái Bình Dương (region `Ấn Độ Dương - Thái Bình Dương`). **Biển Đông**: chủ quyền biển, đụng
   độ/tuần tra, phán quyết, tập trận, hoạt động Philippines/VN/TQ/Mỹ (region `Đông Á`). category theo
   nội dung (CNQS/Ngoại giao/Chính trị).
   ➕ **MỞ RỘNG 27/07/2026 (chỉ thị Huy): tìm thêm tin của CÁC NƯỚC KHÁC trong khu vực Biển Đông** —
   Malaysia, Indonesia, Brunei, Đài Loan; đàm phán **COC** ASEAN–Trung Quốc; các thực thể Natuna, Bãi
   Tư Chính (Vanguard Bank), Luconia, Bãi Cỏ Rong (Reed Bank); hoạt động của Nhật/Ấn/Hàn tại vùng biển
   này. Đây là dư địa lớn khi diễn biến Philippines–Trung Quốc đã nạp hết ở phiên trước.
   ⛔ **SIẾT 01/08/2026 — "tại vùng biển này" là ĐIỀU KIỆN, không phải lời dẫn** (Huy bắt: *"hàn quốc
   liên quan đ gì đến biển đông và Úc mà cứ cho vào???"* — bản tối 01/08 mục này 04 tin thì 03 sai).
   Tin quốc phòng **nội bộ** Nhật/Ấn/Hàn/Trung Quốc (phóng thử tên lửa, ký hợp đồng đóng tàu, luật
   quốc phòng trong nước) **KHÔNG thuộc chủ đề này**. Câu chữ của tin phải tự neo được vào Úc/AUKUS,
   vào vùng biển & thực thể Biển Đông, hoặc vào một nước ven biển đó. **`add_news.py` nay CHẶN CỨNG
   tin `worldNews` không neo được** — nạp vào sẽ báo lỗi, không phải cảnh báo suông. Tin thuộc chủ đề
   khác thì chuyển sang `usNews`; ngoài 5 chủ đề thì bỏ, ghi `logs/loai-tin.md`.
3. **CNQS Mỹ** — `usNews`, category `Công nghệ quân sự`. Khí tài/hệ thống cụ thể: tên lửa, phòng không,
   hải quân, không gian/Space Force, laser, AI quân sự, tàu ngầm, drone, siêu vượt âm.
   ⏳ **KHUNG NGÀY NỚI RIÊNG CHO CHỦ ĐỀ NÀY: lùi tới 3 ngày** (chỉ thị Huy 27/07/2026 — "quét ngày 27
   thì có thể lấy tin xuống tận ngày 24"). 4 chủ đề còn lại VẪN chỉ hôm nay + hôm qua. `add_news.py`
   áp theo **category**: item `Công nghệ quân sự` được lùi 3 ngày (`MAX_AGE_DAYS_CNQS`), item khác lùi
   1 ngày — nên nhớ đặt đúng category, đặt sai là bị chặn oan hoặc lọt tin cũ.
4. **Mỹ–Mali** — `usNews` (dossier `🟤 Mỹ – Mali`). Mỹ cân nhắc/triển khai quân sự ở Mali nhắm JNIM
   (al-Qaeda): không kích drone, phản ứng Mali/Nga (Africa Corps)/JNIM, diễn biến Sahel–Bamako. Tin
   gắn Mali/JNIM/Bamako/Sahel để tự vào dossier. Nguồn: defense.gov, state.gov, centcom.mil (AFRICOM),
   Reuters/AP/AFP, WaPo. 2–5 bài.
   🔄 **ĐỔI KÊNH GỬI 05/08/2026 (chỉ thị Huy), KHÔNG đổi cách quét:** tin Mali **vẫn quét, vẫn nạp
   `usNews` y như cũ**, nhưng **RỜI khỏi file Word bản tin** và nay đi ở **bản sáng 🎖️ Sự kiện & Tập
   trận**, cạnh tập trận và think-tank. Nguyên văn: *"bỏ mục Mali trong file word gửi tele hàng ngày.
   Thêm mục Mali vào kết quả phần quét tập trận và thinktank."* Phiên quét KHÔNG phải làm gì thêm —
   `make_docx.py` tự bỏ mục, `send-morning-email.js::diffMali` tự nhặt. Chi tiết + 03 bảng khoá phải
   khớp nhau: CLAUDE.md gốc repo.
5. **Tập trận ĐANG DIỄN RA** — cập nhật qua `exerciseUpdates`, `name` khớp **ĐÚNG** tên trong
   `DATA.exercises`. Diễn biến mới: khoa mục, bài bắn, lần đầu của từng nước, tuyên bố chỉ huy, khai
   mạc/bế mạc. 1–2 tin.
   🔄 **KHÔNG CÒN NEO CỨNG MỘT KỲ TẬP TRẬN (05/08/2026, chỉ thị Huy:** *"đang có tập trận nào thì chỉ
   tập trung quét thông tin về tập trận đó. Tự động mở rộng nguồn quét tuỳ theo tập trận"*). Máy tự
   xác định cuộc nào đang chạy và tự sinh truy vấn + nguồn bản địa theo nước đăng cai —
   `scripts/tap_tran.py`, bơm vào bảng chủ đề bằng `harvest.py::nap_tap_tran_dang_chay()`.
   - **Cuộc nào đang chạy thì đọc dòng `🎖️ Tập trận đang bám: …` mà `harvest.py` in ra**, đừng tự
     nhớ tên kỳ. Không có cuộc nào thì nó nói thẳng, và chủ đề này trống là ĐÚNG.
   - ⛔ **Đừng tin trường `status` trong `DATA.exercises`** — đo thật 05/08: `Predator's Run` và
     `RIMPAC` đã kết thúc từ 29/07 và 31/07 mà vẫn mang `status: "ongoing"` (web tự suy từ `dates`
     nên không ai buồn sửa). Trạng thái thật tính từ `dates`.
   - Nguồn: nguồn tầng 1 của **nước đăng cai** (Úc → defence.gov.au/airforce.gov.au · Đài Loan →
     mnd.gov.tw · Philippines → pna.gov.ph…), cộng pacom.mil, dvidshub.net, janes.com.

**KHÔNG quét** (đã bỏ khỏi phạm vi): Kinh tế, Ngoại giao chung, xNews (X/Twitter), tin thế giới các
vùng khác (Trung Đông, Châu Âu, Nga–Ukraine…), tạo mới dipEvents. Chỉ đụng tới 5 chủ đề trên.

**Khung thời gian: tin trong 24 GIỜ gần nhất** (theo giờ VN). Chủ đề nào **thiếu** (<5 bài) trong 24h
thì **NỚI thành 48 giờ** cho riêng chủ đề đó. KHÔNG nới quá 48h, KHÔNG bịa tin/link.

> ⛔ **"NỚI 48H" = HÔM NAY + HÔM QUA, HẾT** (chỉ thị Huy 27/07/2026, nguyên văn: *"ví dụ quét tin ngày 26
> thì chỉ được lấy tin tối đa là ngày 25. không được phép lấy tin ngày 24"*). Đừng hiểu 48h thành "lùi 2
> ngày lịch". Quét ngày 27 → chỉ nhận `date` 27/07 hoặc 26/07; tin 25/07 là **QUÁ CŨ**, bỏ luôn, ghi vào
> `logs/loai-tin.md`, và ghi lý do thiếu vào `scan-gaps.json` — thà chủ đề đó về 0 còn hơn nhét tin cũ.
> **Vì sao phải nói rõ:** phiên tối 26/07 hiểu 48h = lùi 2 ngày nên nạp 3 tin ngày **24/07** vào bản tin,
> Huy mở file Word ra thấy ngay. Nó lách được vì mẹo "tách lô, neo lô A về ngày cũ" (dùng để né
> `MAX_AGE_DAYS` khi lô trải 2 ngày) vô tình cũng kéo lùi luôn khung tin.
> **Đã bịt bằng máy 27/07:** `add_news.py` giờ kiểm ngày **hai lớp** — so với `date` batch VÀ so với ngày
> thật hôm nay (giờ VN). Neo batch về ngày nào cũng vô ích, tin quá 1 ngày tuổi bị CHẶN thẳng. Gặp lỗi
> "cũ hơn 1 ngày so với HÔM NAY" thì **bỏ tin đó**, TUYỆT ĐỐI đừng lùi ngày batch để lách.

**Báo Mới: được phép quét** — nhưng LỌC chỉ giữ bài hợp 5 chủ đề trên (xem Agent Báo Mới).

## Nguyên tắc cốt lõi (giữ nguyên)
- **Chất lượng > số lượng.** Thà ít tin đạt chuẩn còn hơn nhồi tin sai. Được phép trả mảng rỗng.
- **Nguồn 3 tầng (chuẩn INTREP):** sự kiện ← nguồn CHÍNH THỨC (tầng 1); số liệu ← nguồn DỮ LIỆU (tầng
  2); nhận định (`significance`) ← VIỆN NGHIÊN CỨU (tầng 3). Báo chí chỉ để PHÁT HIỆN tin, luôn đối chiếu.
- **Ưu tiên nguồn chính phủ/chính thức**: tin từ thông báo chính thức → link THẲNG nguồn gốc
  (defense.gov, state.gov, centcom.mil, defence.gov.au, nato.int, mofa…). Truyền thông nhà nước độc tài
  (Xinhua/TASS/Global Times/KCNA) chỉ dùng cho phát ngôn của chính họ.
- **KHÔNG đọc trực tiếp `index.html`** — dùng grep + `scripts/add_news.py`.
- **KHÔNG tự sửa `index.html` bằng tay** — chèn tin qua script.

## Bước 0 — Log SỚM + idempotent (QUAN TRỌNG — push log NGAY để luôn có dấu vết)
> ⚠️ **Mốc giờ, hạn chót, thứ tự CI/local: đọc `docs/routine-web-scan.md`, KHÔNG đọc ở đây.**
> Bước 0 chỉ giữ mấy luật **gắn với nội dung quét** mà nơi khác không có: lệnh phẳng, checkpoint
> chỉ `git add logs/`, và cách dùng cờ `state.py`. Trước 29/07/2026 bước này còn chép cả lịch
> ("chạy 22:00, dự phòng 23:00") và đã lệch 3 ngày so với lịch thật — đừng chép lại lần nữa.
⚠️ **MỌI LỆNH BASH PHẢI PHẲNG — không wrapper, không biến, không vòng lặp** (25–26/07/2026 treo 3 lần:
prefix `cd() { echo "cd disabled"; };` → flag "expansion obfuscation"; biến `$f` trong
`for f in ...; do grep .../$f.jsonl; done` → flag "simple_expansion" — harness gặp các cú pháp đó là
BỎ QUA allowlist, bật prompt xin quyền, routine treo chờ bấm nút dù lệnh bên trong hợp lệ).
Chỉ dùng lệnh đơn / pipe / chuỗi `&&`; "không dùng cd" = ĐỪNG GỌI `cd`, KHÔNG phải vô hiệu hoá nó.
Lấy ngày/giờ bằng 2 lệnh riêng `TZ='Asia/Ho_Chi_Minh' date +%F` và `date -u +%H:%MZ`, rồi ĐIỀN GIÁ
TRỊ THẬT vào các lệnh sau (không dùng `$NGAY`/`$T`). Cần lặp nhiều file → viết N lệnh rời hoặc gói
vào `python3 -c '...'` (đã allowlist), tuyệt đối không bash for/heredoc.
- Ghi `[<giờ>Z] START` vào `logs/scan-<ngày VN>.log` (tool Write/Edit) rồi **commit + push NGAY LẬP TỨC**:
  `git -C /Users/Huy/Claude/diem-tin-the-gioi add logs/ && git -C /Users/Huy/Claude/diem-tin-the-gioi commit -q -m "log: start <ngày> <giờ>Z phien toi" && git -C /Users/Huy/Claude/diem-tin-the-gioi push origin main -q`
  (Chữ trong log ghi theo phiên mình đang chạy: **"phien toi"** hoặc **"phien sang som"** — biết mình
  là phiên nào bằng `TZ='Asia/Ho_Chi_Minh' date +%H:%M`, trước 14:00 = sáng sớm, từ 14:00 = tối.)
  (Session tự động là ephemeral — chết giữa lúc quét mà chưa push thì mất sạch dấu vết.)
- **Checkpoint sau MỖI mốc lớn** (xong baseline · xong các agent · xong script · trước khi push tin):
  ghi thêm dòng `[<giờ>] <mốc>: <tóm tắt>` vào log, chạy `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/state.py beat web-scan` rồi
  push ngay → biết chết ở đâu + gia hạn khoá. **Nhịp tim bắt buộc**: khoá tự hết hạn sau 30' không có nhịp.
- ⚠️ **Checkpoint CHỈ `git add logs/` — TUYỆT ĐỐI KHÔNG kèm `index.html`** (sự cố 25/07/2026).
  `index.html` chỉ được commit ĐÚNG MỘT LẦN, ở commit cuối `Cap nhat ban tin ...`. Lý do: commit
  checkpoint mang tên `log: ...` KHÔNG khớp gate `^Cap nhat ban tin` nên không kích khâu gửi, nhưng nó
  vẫn nằm ở `HEAD~1` của commit bản tin — mà `make_docx.py` dựng file Word bằng diff với `HEAD~1`.
  Hôm 25/07 checkpoint 22:23 đã ôm sẵn 12 tin, tới commit bản tin 22:41 diff chỉ còn 3 → **file Word
  gửi Huy mất 12/15 tin** dù web hiện đủ. (`make_docx.py` đã được vá lấy HỢP `diff` ∪ `today_items`
  nên không còn mất tin, nhưng vẫn giữ nguyên tắc này — đừng dựa vào một lớp chặn.)
  Nạp tin nhiều lô giữa chừng thì cứ chạy `add_news.py`, để `index.html` ở trạng thái chưa commit,
  checkpoint bằng `git -C /Users/Huy/Claude/diem-tin-the-gioi add logs/` thôi.
- Idempotent + khoá — **dùng cờ riêng pipeline `web-scan`, KHÔNG dùng `generatedAt`**:
  ```
  python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/state.py claim web-scan
  ```
  ⚠️ **PUSH `logs/state.json` NGAY SAU KHI CLAIM, TRƯỚC khi làm baseline** (sự cố 26/07/2026): khoá đồng
  bộ QUA GIT — phiên nào chưa push khoá thì phiên kia pull về vẫn thấy "không ai giữ khoá" và claim tiếp.
  Local claim 21:41 mà để dành push → CI pull 22:09 không thấy khoá → hai phiên cùng quét, local mất
  trắng công baseline. Và **trước khi chạy `add_news.py` phải `pull --rebase` + đọc lại `logs/state.json`**:
  thấy `lastRunAt`/`heartbeat` của phiên khác mới hơn mình = đã bị cướp khoá → DỪNG, ghi log SKIP,
  **KHÔNG gọi `state.py skip/fail`** (ghi đè RUNNING + nhả khoá của phiên đang chạy), `reset --hard
  origin/main` rồi commit riêng dòng log.
  `SKIP` (exit 10) → buổi này đã quét xong · `SKIP` (exit 11) → **có phiên khác đang chạy**, không quét
  chồng. Cả hai: ghi log `SKIP`, push log, KẾT THÚC. `RUN` (exit 0) → đã giữ khoá, quét tiếp.
  Cờ theo BUỔI: `state.py` TỰ suy ô từ giờ VN lúc chạy (trước 14:00 = `sang`, từ 14:00 = `toi`) —
  routine KHÔNG phải truyền gì thêm. Mốc nào của phiên nào, mốc nào là dự phòng: **`docs/routine-web-scan.md`**
  (bảng đầu file). Mốc sau thấy mốc trước đã DONE thì `claim` tự trả SKIP, không quét chồng.
- **Kéo bản mới nhất về trước khi làm gì**: `git pull --rebase origin main`.
  ⛔ Báo `cannot pull with rebase: You have unstaged changes` → **ĐỪNG DỪNG PHIÊN**: `git fetch origin main`
  rồi `git rev-list --count HEAD..origin/main`; ra **0** thì pull vốn là lệnh rỗng → đi tiếp bình thường,
  ra **>0** thì mới FAIL. TUYỆT ĐỐI không `git stash`, không commit hộ file lạ. Chi tiết + bảng đo:
  `docs/routine-web-scan.md` Bước 1.
- Lỗi ở bất kỳ bước: ghi `[<giờ>] FAIL tại <bước>: <lý do>`, chạy `python3 scripts/state.py fail
  web-scan "<lý do>"` (nhả khoá + KHÔNG chặn lần fire sau), push log, dừng.

## Bước 1 — Nguồn + dữ liệu nền
Đọc mục **"Nguồn theo 3 tầng"** + bảng **"URL RSS đã biết"** trong `CLAUDE.md`, VÀ **Phụ lục "NGUỒN MỞ
RỘNG theo 5 chủ đề"** ở cuối skill này (danh sách nguồn cụ thể cho từng chủ đề — chọn vài nguồn hợp rồi
nhúng vào prompt agent). Ưu tiên nguồn quốc phòng/chính thức Mỹ + Úc + AFRICOM cho 5 chủ đề này. Lấy dữ liệu nền:
```
python3 scripts/harvest.py --gop-ci --json /tmp/ung-vien.json           # ⭐ GOM ỨNG VIÊN — chạy TRƯỚC
grep -oE '"sourceName":"[^"]+"' index.html | sort | uniq -c | sort -rn   # nguồn đã dùng nhiều → né
python3 scripts/add_news.py --recent-titles 20                          # tiêu đề gần đây → chống trùng
python3 scripts/add_news.py --baomoi-pending                            # 2 nhóm Báo Mới
```

### ⭐ `harvest.py` — MÁY ĐI LẤY, AGENT ĐI THẨM ĐỊNH (bắt buộc từ 27/07/2026)
Quét **67 feed RSS trong bảng CLAUDE.md + 8 truy vấn Google News**, lọc theo khung hôm nay + hôm qua và
theo từ khoá 5 chủ đề (`scripts/topics.py`), bỏ rác + gộp các bản trùng của cùng một sự kiện, in ứng
viên theo từng chủ đề (kèm `--json` để nhúng vào prompt agent).

**Vì sao bắt buộc:** đo thật trên DATA — 161 nguồn từng đóng góp tin, nhưng nguồn chuyên đúng chủ đề
lại **0 tin**: Long War Journal (Mali), AllAfrica (Sahel), Philstar + Inquirer (Biển Đông), Lowy +
ABC News AU (Úc), gCaptain, Shephard. Không phải nguồn chết — curl từ máy trả 200 hết. Nguyên nhân là
**WebFetch của subagent bị chặn 403**, nên agent rơi về WebSearch và quét tuỳ duyên. Hậu quả đo được:
sáng 27/07 agent Mali kết luận "không có bài mới" trong khi Google News có 88 item Mali/Sahel trong
48h, gồm tin Bloomberg 26/07 (Liên minh Sahel tăng quân lên 18.000) — bỏ sót thật, phải nạp bù sau.
Ngay lần chạy đầu, harvest bắt được `gCaptain — Three Clashes in a Week Escalate China-Philippines Sea
Feud` và `The Hill — GOP senator ahead of Fauci testimony`, đều từ nguồn agent chưa từng chạm tới.

**Cách dùng kết quả — ĐỌC KỸ, đây là chỗ dễ sai:**
- `[RSS]` có link bài GỐC thật → kiểm nội dung rồi dùng luôn được.
- `[HTML]` — quét thẳng trang thông cáo của các trang KHÔNG có RSS (thêm 27/07/2026 sau khi Huy nhắc
  *"không có RSS thì mày vẫn xem được mà"*). **Chủ lực là uỷ ban Quốc hội — tức đúng nhóm 1** (điều
  trần + bỏ phiếu), nhóm luôn thiếu tin nhất: thực tế bắt được "Chairman Rogers Applauds House Passage
  of FY27 NDAA", "House Passes H.R. 9770", "Cole Testifies at Rules Committee". Link là link gốc thật,
  NHƯNG **ngày lấy từ khối HTML quanh link nên có thể sai** → phải mở bài kiểm ngày sự kiện như `[GNEWS]`.
  ⚠️ **PHIÊN CI QUÉT ĐƯỢC NHIỀU HƠN PHIÊN LOCAL** (đo thật 27/07 bằng `scripts/probe_sources.py` chạy ở
  cả hai nơi): local đọc được **10** trang, CI đọc được **25** — vì **toàn bộ uỷ ban THƯỢNG VIỆN chỉ CI
  mới vào được** (local 403), cộng census.gov và occ.treas.gov. `harvest.py` tự nhận biết môi trường qua
  biến `GITHUB_ACTIONS` và bỏ qua nhóm CI-only khi chạy local, nên **số trang in ra khác nhau là ĐÚNG,
  đừng đi truy bug**. Ngược lại CI hụt 3 nguồn local có (`axios.com`, `flightglobal.com`, `rappler.com`).
- ⭐ **`--gop-ci` — vá phần chênh đó cho phiên local** (thêm 27/07/2026). Workflow `harvest-ci.yml` tách
  riêng KHÂU THU THẬP: chạy thuần `curl` trên runner Mỹ, **không gọi Claude nên không tốn quota**, mất
  ~2-3 phút, chạy lúc **20:45 · 21:45 · 03:45 · 04:45 VN** (trước mỗi mốc quét ~15 phút) rồi commit lô
  ứng viên vào `docs/ung-vien-ci.json`. Phiên local `pull --rebase` (đã làm ở Bước 1) rồi chạy
  `harvest.py --gop-ci` để gộp. Nhờ vậy **kể cả khi lớp CI-quét-bằng-Claude chết vì hết quota hay
  GitHub bỏ cron, nguyên liệu vẫn được lấy từ Mỹ** — trước đây phần chênh 15 trang Thượng viện mất trắng.
  Lô CI mang nhãn `[CI-HTML]` / `[CI-RSS]` để phân biệt. Script tự BỎ lô nếu **lệch khung ngày** hoặc
  **quá 4 tiếng** (khung ngày của mốc sáng và mốc tối cùng ngày là giống hệt nhau, chỉ so khung thì lô
  04:45 vẫn "hợp lệ" lúc 21:15 và bản tin tối sẽ thiếu sạch tin ban ngày) — thấy dòng `[CI] ... BỎ`
  trên stderr là bình thường, cứ đi tiếp bằng lô local.
- `[GNEWS]` chỉ là **RADAR phát hiện đề tài**: link là redirect `news.google.com` (không resolve bằng
  HEAD được, nó redirect bằng JS) và tiêu đề bị rút gọn. **Agent PHẢI tự tìm bài gốc** (WebSearch theo
  tiêu đề + tên nguồn) rồi mới nạp. TUYỆT ĐỐI không nạp link `news.google.com` vào DATA.
- ⚠️ **Ngày in ra là NGÀY ĐĂNG BÀI, KHÔNG phải ngày sự kiện.** Nhiều trang đăng lại tin cũ với pubDate
  mới: 27/07 harvest hiện "US House passes $1.15 trillion defence bill" ngày 26/07, nhưng cuộc bỏ phiếu
  216-212 diễn ra **22/07** — ngoài khung, phải bỏ. Luôn mở bài, neo `date` theo NGÀY SỰ KIỆN.
- Harvest **không thay thế** agent: nó lo độ PHỦ (không sót nguồn), agent lo độ ĐÚNG (thẩm định, chống
  trùng sự kiện, viết tiếng Việt). Vẫn giao đủ 5 luồng agent như Bước 2 — nhưng nhúng ứng viên của
  chủ đề tương ứng vào prompt để agent khỏi mò lại từ đầu.

Nhúng nguyên khối `--recent-titles` vào prompt MỌI agent để né trùng (gồm cả tin Drive vừa nạp 20:00).
`preferences.json` (👍/👎) chỉ là điều hướng mềm — với phạm vi tập trung này, 5 chủ đề là ưu tiên số 1.

## Bước 2 — Giao agent Sonnet (song song, `model: "sonnet"`, run_in_background:false)
Chỉ **5 luồng** cho 5 chủ đề (gộp Mali+Predator vào 1 agent; Báo Mới 1 agent nếu có bài hợp topic):

| Agent | Chủ đề | Sản lượng (24h, nới 48h nếu thiếu) |
|---|---|---|
| A | **Nội bộ Mỹ (5 nhóm, 2 hạng)** → `usNews` cat `Chính trị`/`Kinh tế` | **5–10** — vét cạn nhóm (1) điều trần + bỏ phiếu TRƯỚC, thiếu mới lấy sang (2) sáng kiến/chiến lược các bộ · (3) biểu tình · (4) kinh tế Mỹ + Nhà Trắng/nội các · (5) bầu cử — bốn nhóm này NGANG HÀNG. Xem PHẠM VI MỚI mục 1. Prompt agent phải nêu RÕ hai hạng này và bắt agent báo lại đã cạn nhóm 1 chưa + số bài mỗi nhóm. |
| B | **Úc & Biển Đông** → `worldNews` | **5–10** — Úc (region IPAC) + Biển Đông (region Đông Á). |
| C | **CNQS Mỹ** → `usNews` cat `Công nghệ quân sự` | **5–10** — khí tài/hệ thống cụ thể. |
| D | **Mỹ–Mali + Predator's Run 2026** | Mali 2–5 (`usNews` dossier) · Predator 1–2 (`exerciseUpdates`). |
| BM | **Báo Mới** (nếu `--baomoi-pending` có bài hợp 5 chủ đề) | Bài ĐÃ LƯU: giữ hết (field `baomoiNews`). Ứng viên chuyên mục: **CHỈ chọn bài hợp 5 chủ đề**, 2–5 bài, `worldNews`/`usNews` như thường. Không có bài hợp → bỏ qua agent này. |

**Agent Báo Mới — TRUY NGƯỢC VỀ NGUỒN GỐC** (giữ nguyên quy tắc cũ): Báo Mới là trang tổng hợp. Với mỗi
bài: mở `sourceUrl` (WebFetch) đọc nội dung, **tìm bài gốc nước ngoài** đúng sự kiện (đăng ≤48h), **mở
WebFetch xác nhận có thật + đúng ngày**, lấy `sourceName`+`sourceUrl`+`title`+`summary`+`significance`
theo bài GỐC (đổi cả tiêu đề lẫn URL). Không tìm được: bài ĐÃ LƯU → giữ link Báo Mới; ứng viên chuyên
mục → bỏ, chọn bài khác. Cả hai chỉ giữ bài hợp 5 chủ đề.

⚠️ **HỄ ĐÃ ĐỔI URL SANG NGUỒN GỐC LÀ PHẢI KÈM `"_baomoiUrl":"<link Báo Mới>"` — CẢ bài đã lưu LẪN ứng
viên chuyên mục** (sửa 27/07/2026; trước đây ghi nhầm là ứng viên chuyên mục không cần). Thiếu field
này, `collect_existing_urls` mất dấu link Báo Mới cũ → cổng Báo Mới + `--baomoi-pending` vẫn coi bài
"chưa nạp" và phiên sau nạp lại y hệt, mà guardrail trùng URL KHÔNG bắt được vì URL đã đổi. Gặp thật
với tin "Tàu 015-Trần Hưng Đạo thăm Manila" ngày 27/07.

🚪 **CỔNG BÁO MỚI (dựng 27/07/2026 — cưỡng bức, không dựa vào trí nhớ).** `add_news.py` tự lọc kho Báo
Mới theo bộ từ khoá 5 chủ đề rồi in danh sách ứng viên KHỚP mà chưa nạp, ở **cả hai** lệnh phiên quét
bắt buộc chạy: `--recent-titles` (đầu phiên) và lúc nạp lô (dòng CUỐI, ngay trước khi commit). Thấy
cổng báo còn ứng viên thì **phải xử lý từng bài**: truy về gốc rồi nạp, HOẶC loại và ghi lý do vào
`logs/loai-tin.md` + mục "Báo Mới" trong `scan-gaps.json`. **Không được im lặng bỏ qua.** Vì sao có
cổng: phiên sáng 27/07 bỏ hẳn vòng Báo Mới khi Huy giục quét nhanh, suýt mất 1 tin Biển Đông hợp chủ
đề; lời hứa "lần sau nhớ" không chặn được, chỉ có thứ đập vào mắt mỗi lần chạy script mới chặn được.

**Nhúng vào MỌI prompt agent** (agent KHÔNG thấy hội thoại chính — viết prompt độc lập, đủ ngữ cảnh):
- **Chủ đề + tiêu chí lọc riêng** của agent đó (copy đúng đoạn PHẠM VI MỚI tương ứng).
- **Khung thời gian: CHỈ tin đăng trong 24 GIỜ gần nhất** (theo giờ VN). Nếu chủ đề khan (<5 bài) →
  được nới thành **48 giờ**. TUYỆT ĐỐI không lấy tin cũ hơn 48h, không bịa.
  **Viết THẲNG 2 ngày cụ thể vào prompt agent, đừng viết chữ "24h/48h"** — agent hay hiểu 48h thành lùi
  2 ngày lịch. Ví dụ phiên ngày 27/07: *"chỉ nhận bài đăng 27/07 hoặc 26/07; tin 25/07 trở về trước là
  QUÁ CŨ, bỏ"*. `add_news.py` cũng chặn cứng đúng biên này nên nhận về cũng không nạp được.
- **THANG XÁC MINH — bao nhiêu nguồn là đủ** (chốt 27/07/2026, xem bảng đầy đủ trong `CLAUDE.md` mục
  "THANG XÁC MINH"): nguồn **tầng 1 chính thức** đọc được → ĐỦ, không cần báo chí xác nhận lại; **wire /
  báo chuyên ngành / báo phổ thông uy tín** → một nguồn là đủ; **trang tổng hợp hoặc dẫn lại** (Báo Mới,
  RealClear*, Investing.com, Yahoo/AOL/MSN) → BẮT BUỘC truy về bài gốc, không ra gốc thì cần 2 nguồn
  độc lập, không thì bỏ; **link không mở được bằng tool** (403/302) KHÔNG phải lý do bỏ nếu nội dung đã
  xác nhận được qua đường khác. Đừng bỏ tin tầng 1 chỉ vì chưa thấy báo nào đưa lại.
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
- **Ràng buộc chất lượng**: (a) `date` đúng khung 24h/48h; (b) `sourceUrl` trỏ THẲNG 1 bài cụ thể,
  KHÔNG trang chủ/"live"/live-blog/tổng hợp, link KHỚP nội dung; (c) `sourceName` trong danh sách nguồn
  được giao HOẶC nguồn chính thức phù hợp; (d) thà ÍT còn hơn sai — được phép trả mảng rỗng.
- **Ưu tiên nguồn chính phủ/chính thức** (link thẳng nguồn gốc) + **nguồn tiếng Anh có RSS** trước
  (URL RSS: xem bảng trong CLAUDE.md, đưa thẳng URL cho agent).
- **Chống trùng**: dán NGUYÊN khối `--recent-titles` (bước 1) vào prompt; dặn không report lại tin đã có.
- **⛔ TIN NỐI TIẾP — GIỮ TIN, NHƯNG CÂU MỞ PHẢI VÀO THẲNG PHẦN MỚI** (luật 30/07/2026, sau khi người
  đọc bản tin tối nhắn *"tin trên bị trùng á"*). **Đây KHÔNG phải luật chống trùng** — tin nối tiếp là
  tin thật, sự kiện mới, phải giữ. Chỗ hỏng nằm ở CÁCH VIẾT tóm tắt.
  **Cơ chế gây vấp:** tin The Hill *"Trump đòi bổ sung quyền áp thuế Iran vào dự luật trừng phạt Nga
  mang tên Graham"* (30/07) mở đầu tóm tắt bằng *"Sau khi Thượng viện thông qua dự luật trừng phạt
  Nga-Iran mang tên cố Thượng nghị sĩ Lindsey Graham với tỷ lệ 86-12, …"* — mà đó đúng là **nguyên
  sự kiện đã gửi hôm trước** (tin Straits Times, bản tin 29/07). Người đọc lướt tiêu đề + dòng đầu
  thấy y hệt hôm qua nên kêu trùng; phần MỚI (Trump đòi thêm quyền) nằm ở vế sau, phải đọc hết mới thấy.
  | | |
  |---|---|
  | ❌ SAI | *"Sau khi Thượng viện thông qua dự luật … với tỷ lệ 86-12, Tổng thống Trump yêu cầu bổ sung quyền áp thuế quan nhắm vào Iran."* |
  | ✅ ĐÚNG | *"Tổng thống Trump yêu cầu bổ sung quyền áp thuế quan nhắm vào Iran vào dự luật trừng phạt Nga đã được Thượng viện thông qua hôm 28/7."* |
  Ba việc bắt buộc: (i) **câu đầu nêu diễn biến MỚI**, chủ ngữ là chủ thể của diễn biến mới; (ii) phần
  đã gửi hôm trước rút còn **một vế phụ ngắn** làm mốc, đặt sau, không kể lại số liệu chi tiết của nó
  (tỷ lệ bỏ phiếu, danh sách nghị sĩ bảo trợ…); (iii) **tiêu đề đừng lặp nguyên cụm định danh** của tin
  cũ nếu diễn ra được cách khác.
  **Máy nhắc ở đâu:** `add_news.py` in `[CẢNH BÁO] tiêu đề nghi trùng (Jaccard …)` kèm hướng dẫn trên
  khi tiêu đề mới gần tiêu đề cũ (ngưỡng `JACCARD_CANH_BAO_TIEU_DE = 0.4`). **Đây là CẢNH BÁO, không
  chặn** — thấy nó thì sửa câu mở rồi nạp lại, đừng bỏ tin. Bộ test canh:
  `tests/test-canh-bao-tin-noi-tiep.py`.
- **Đa dạng sự kiện**: mỗi tin 1 sự kiện KHÁC NHAU.
- Yêu cầu agent CHỈ trả JSON kết quả (mảng tin của chủ đề đó), không giải thích dài.

## Bước 3 — Review + gộp
Session điều phối **tự review từng tin** theo ràng buộc chất lượng, loại tin không đạt (sai khung giờ,
link rác/không khớp, trùng, không đúng 5 chủ đề, tin "nội bộ Mỹ" nhưng không neo được vào nước Mỹ…).

**Ghi tin bị loại** vào `logs/loai-tin.md` (dạng chữ: `[chủ đề] tiêu đề (nguồn, ngày) — lý do`). Field
`rejectedNews` trong JSON là TUỲ CHỌN với phạm vi mới (không bắt buộc gom tin loại như trước) — chỉ thêm
nếu có tin đúng chủ đề nhưng lệch khung giờ, đáng để người dùng cứu.

Gộp vào `/tmp/new_items.json`:
> ⚠️ **`date` batch = NGÀY TIN MỚI NHẤT trong lô** (thường là hôm qua nếu quét sau nửa đêm / máy chạy
> trễ), KHÔNG phải ngày hệ thống. Script chặn tin cũ hơn 1 ngày so với `date` này — neo sai (theo hôm
> nay) sẽ chặn oan tin nới-48h.
> ⛔ **Nhưng neo lùi KHÔNG kéo lùi được khung tin** (bịt 27/07/2026): script kiểm thêm lớp thứ hai — mọi
> tin phải trong vòng 1 ngày so với **HÔM NAY giờ VN thật**. Neo `date` batch về 25/07 để nạp tin 24/07
> là đường lách đã bị chặn (chính là cách 3 tin ngày 24/07 lọt vào bản tin tối 26/07).
```json
{
  "date": "YYYY-MM-DD",
  "worldNews": [ ... ], "usNews": [ ... ],
  "baomoiNews": [ ... ],
  "exerciseUpdates": [ {"name":"Predator's Run 2026 (tập trận Mỹ - Úc - Philippines)","items":[ ... ]} ],
  "rejectedNews": [ {"date","category","title","summary","sourceName","sourceUrl","region","reason"} ]
}
```
`category` chỉ 4 giá trị hợp lệ (Kinh tế/Chính trị/Công nghệ quân sự/Ngoại giao); 5 chủ đề map: Nội bộ Mỹ→
Chính trị, CNQS Mỹ→Công nghệ quân sự, Úc/Biển Đông→theo nội dung, Mali→Ngoại giao/CNQS/Chính trị.

## Bước 4 — Chèn bằng script (guardrail chặn lần cuối)
```
python3 scripts/add_news.py /tmp/new_items.json
```
Script **CHẶN** (sửa JSON rồi chạy lại): thiếu field; category sai; date ngoài khung (`MAX_AGE_DAYS=1`,
kiểm **HAI LỚP**: lùi tối đa 1 ngày so với `date` batch **VÀ** lùi tối đa 1 ngày so với **hôm nay giờ VN
thật**. Vì vậy đặt `date` batch = **NGÀY TIN MỚI NHẤT trong lô**, KHÔNG neo theo ngày hệ thống; khi đó
tin nới-48h = hôm trước vẫn khít khung. Neo `date` theo hôm nay mà tin mới nhất là hôm qua thì tin 48h
bị chặn oan — lỗi hay mắc. Còn báo *"cũ hơn 1 ngày so với HÔM NAY"* thì tin đó thật sự quá cũ: **BỎ**,
đừng lùi ngày batch để lách); URL trang
chủ/live-blog; URL trùng trong batch hoặc đã có trong
DATA; tên exercise (`exerciseUpdates`) không khớp entry có sẵn. **CẢNH BÁO** (không chặn): nguồn lạ;
tiêu đề nghi trùng.
- **KHÔNG còn sàn 15+15.** Dòng script in `SÀN CỨNG … X/15 · Y/15` là DI SẢN cũ — **BỎ QUA nó**. Mục
  tiêu mới là **mỗi chủ đề 5–10 bài** (tự đếm theo chủ đề, không theo world/us tổng).
- Chủ đề nào **<5 bài trong 24h** → giao thêm agent cho riêng chủ đề đó với khung **48h**; vẫn thiếu thì
  CHẤP NHẬN (ghi rõ trong tóm tắt), KHÔNG bịa/nhồi. Không lặp vô hạn — 1–2 vòng bổ sung là đủ.

## Bước 4b — Ghi `logs/scan-gaps.json` (BẮT BUỘC — bản tin gửi đi lấy mục "Chủ đề thiếu và lý do" từ đây)
Chỉ thị Huy 25/07/2026: **bản tin gửi đi phải ghi cả chủ đề thiếu VÀ lý do**. Lý do là kiến thức của
phiên quét, GitHub Action không tự suy ra được → phiên quét phải ghi ra file, khâu gửi đọc file đó và
dựng mục. **Không ghi file = bản tin thiếu mục này.**
> 📵 **Kênh gửi hiện nay là TELEGRAM, không phải email** (chỉ thị Huy 27/07/2026 — `GUI_EMAIL='0'`
> trong `notify-email.yml`/`notify-morning.yml`). `send_telegram.py` cũng đọc `scan-gaps.json` nên
> yêu cầu ghi file KHÔNG đổi. Bật lại email = đổi biến đó thành `'1'`.

Ghi `logs/scan-gaps.json` (đè bản cũ, dùng tool Write), liệt kê ĐỦ 5 chủ đề (+ Báo Mới nếu có nạp):
```json
{
  "date": "<= đúng DATA.generatedAt sau khi chạy add_news.py, KHÔNG phải ngày hệ thống>",
  "session": "toi",
  "topics": [
    {"name":"Nội bộ Mỹ (điều trần + bỏ phiếu dự luật)","count":0,"target":"5-10","min":5,"thieu":true,
     "reason":"<vì sao thiếu: đã nới 48h chưa, nguồn nào cạn/chặn, tin nào bị loại vì lý do gì>"},
    {"name":"Công nghệ quân sự Mỹ","count":8,"target":"5-10","min":5,"thieu":false,"reason":""}
  ],
  "note": "<tuỳ chọn: tin bị loại đáng chú ý, trỏ tới logs/loai-tin.md>"
}
```
- `date` **PHẢI khớp `DATA.generatedAt`** — `send-email.js` so hai giá trị này, LỆCH thì bỏ cả mục (chống
  gửi lý do của hôm trước). Nạp nhiều lô thì lấy ngày của lô CHẠY CUỐI.
- `thieu` là cờ tường minh (không có thì script suy từ `count < min`). Chủ đề ĐỦ vẫn phải liệt kê để
  email in được dòng sản lượng cả 5 chủ đề; khi đó `reason` để rỗng.
- `reason` viết cho NGƯỜI ĐỌC, nêu nguyên nhân thật (Quốc hội nghỉ họp, nguồn 403/timeout, tin trùng sự
  kiện, ngoài khung 48h…), KHÔNG viết chung chung kiểu "không tìm được tin".
- Kiểm mắt trước khi push — **kênh đang chạy là Telegram, dùng lệnh này** (chạy được trên máy Huy):
  `DRY_RUN=1 python3 .github/scripts/send_telegram.py` → in nguyên tin nhắn sẽ gửi, gồm mục
  "Chủ đề thiếu và lý do", KHÔNG gửi thật.
  Bản email (đang tắt, `GUI_EMAIL='0'`): `DRY_RUN=1 node .github/scripts/send-email.js` → ghi
  `/tmp/email-preview.html`. ⚠️ **Máy Huy KHÔNG có `node`** — chỉ chạy được ở nơi có node, hoặc kiểm
  cú pháp/logic bằng `jsc` với stub `require` (xem CLAUDE.md).

## Bước 4c — CẢ HAI PHIÊN: dùng file Jay Lâm làm BỘ LỌC (đảo nguyên tắc 01/08/2026)

> Nguyên văn Huy: *"thay đổi hoàn toàn nguyên tắc. file của Jay Lâm gửi chỉ là để so sánh xem có tin
> nào mày quét được mà bị trùng với tin trong file đó không thôi"* · *"nếu có tin bị trùng với file
> Jay Lâm thì tự xoá khỏi tổng hợp tin đã quét đi và gửi file word (trong đó không có tin nào từ
> Jay Lâm)"*.

⛔ **MỤC 5 "Tin Jay Lâm gửi" ĐÃ BỎ HẲN.** File Jay Lâm không còn đóng góp một dòng nào vào bản tin.
Nó chỉ dùng để **bớt tin CỦA MÌNH**: tin nào mình quét được mà anh ta đã có thì bỏ đi, vì anh ta đọc
rồi. Bản tin gửi ra chỉ còn phần Jay Lâm CHƯA có. Mọi chỉ dẫn cũ về tóm tắt-để-đăng, `la_cnqs`,
`nguon_ten`, nhãn xác minh đều hết hiệu lực.

⏰ **KÍCH BOT HÚT TELEGRAM TRƯỚC, RỒI MỚI ĐỌC** (giữ nguyên từ 30/07/2026). File Jay Lâm gửi chỉ vào
bảng khi `telegram-bot.yml` chạy, mà GitHub chạy workflow đó **cách nhau 01-02 giờ** dù cron khai
`*/5`. Tối 30/07: file gửi 21:20 VN, đọc lúc 21:25 chỉ thấy file HÔM TRƯỚC. Hàng chờ có dữ liệu nên
nhìn như đang chạy đúng — không lỗi, không cảnh báo.

```
gh workflow run telegram-bot.yml --repo huyneo1101-dotcom/diem-tin-the-gioi
gh run watch <id> --exit-status --interval 15    # ~2 phút
python3 scripts/tin_jaylam.py --liet-ke          # mã 10 = không có file nào -> bỏ qua bước này
python3 scripts/tin_jaylam.py --ghi /tmp/bang-jaylam.json      # (2) lưu bảng đối chiếu
python3 scripts/tin_jaylam.py --ghi-loai /tmp/loai-jaylam.json # (3) khai tin của mình bị bỏ
```
Không gọi được `gh` (phiên CI hay bị chặn *requires approval*) thì **ghi một dòng vào log rằng chưa
kích được bot** rồi đi tiếp — fail-open CÓ TIẾNG.

### (2) `--ghi` — trích BẢNG ĐỐI CHIẾU từ file Jay Lâm
`--liet-ke` in TOÀN VĂN với file chưa trích, in BẢNG GỌN với file đã trích. Đọc toàn văn rồi nộp:
`[{"id": <id>, "tin": [{"tieu_de": "...", "url": "https://..."}, ...]}]`

- **Trích ĐỦ MỌI TIN trong file, không lọc, không chọn lọc.** Đây là bảng đối chiếu — sót một tin là
  tin đó sẽ lọt vào bản tin dù Jay Lâm đã có. Script cảnh báo `TRÍCH SÓT` khi file nhiều link mà
  trích quá ít, nhưng cảnh báo đó chỉ bắt được ca lệch nặng.
- `url` **được phép rỗng** — Jay Lâm viết lại bằng tiếng Việt, nhiều tin không kèm link. URL chỉ là
  chốt phụ; script không dùng `check_url_quality` nên link trang chủ vẫn nhận.
- Trích xong thì lần sau khỏi đọc lại toàn văn (34.000 ký tự/file) — bảng lưu trong Supabase và
  `--liet-ke` in lại nó suốt **3 ngày** file còn hiệu lực.

### (3) `--ghi-loai` — khai tin CỦA MÌNH bị bỏ
`[{"url": "<sourceUrl tin của mình>", "tieu_de": "<tiêu đề tin của mình>", "id_jay": <id>,
"trung_voi": "<mảnh tương ứng bên file Jay>"}]`

⚠️ **SO LINK THUẦN LÀ VÔ DỤNG — đã đo, đừng dựng lại đường đó.** Đối chiếu 12 tin quét tối 01/08 với
37 URL trong file Jay Lâm ra **0 tin trùng URL**, trong khi đọc hiểu ra **03 tin trùng sự kiện**
(Mahan Air · tuần tra Scarborough · NITE-STAR 981 triệu USD). Jay Lâm viết lại bằng tiếng Việt từ
nguồn khác hẳn nguồn mình lấy. **Phép lọc là ĐỌC HIỂU THEO SỰ KIỆN**; link chỉ là chốt chắc khi tình
cờ trùng.

⚠️ **Đối chiếu phải so với FILE GỐC hoặc bảng trích ĐẦY ĐỦ, KHÔNG so với danh sách tin đã viết lại
của mình.** Vấp thật 01/08: danh sách 29 tin viết lại của phiên trước đã qua lọc trùng rồi, nên đúng
những tin trùng lại vắng mặt trong đó — dùng nó làm bảng đối chiếu thì kết luận "không có tin nào
trùng".

- **Phạm vi lọc: MỌI tin còn trong khung ngày (2-3 ngày), không chỉ lô vừa nạp.** File Jay Lâm gửi
  hôm nay vẫn phải lọc tin CNQS Mỹ mình đăng từ 3 ngày trước.
- `trung_voi` **bắt buộc** — xoá tin là mất nội dung, phải soi ngược được vì sao. Script chặn nếu
  thiếu.
- **Không chắc thì ĐỪNG khai.** Hai chiều lệch khác hẳn nhau: sót một tin ⇒ bản tin lặp tin Jay Lâm
  đã có (Huy thấy được); khai thừa ⇒ **tin của mình biến mất, không ai thấy**.
- Sổ nằm ở `logs/trung-jaylam.json` — **phải `git add logs/` cùng bản tin**, không thì
  `make_docx.py` không thấy sổ và bản .docx vẫn lặp tin.

⚠️ **BỎ BƯỚC NÀY THÌ BẢN TIN LẶP TIN JAY LÂM ĐÃ CÓ** — không mất tin, không lỗi, chỉ là anh ta đọc
lại thứ đã đọc. Quá hạn 21:45 của phiên tối thì vẫn **chốt bản tin trước**, bỏ bước này; file Jay Lâm
còn hiệu lực 3 ngày nên bản tin sau vẫn lọc được phần còn lại.
## Bước 5 — Xuất bản + log
- `git add index.html logs/` phải gồm **`logs/scan-gaps.json`** (cùng `logs/state.json`).
- `python3 scripts/state.py done web-scan "+N tin (5 chủ đề)"` — CHỈ khi thật sự nạp được tin; lô rỗng
  thì `skip` để lần fire sau còn quét lại.
- Commit: `Cap nhat ban tin DD/MM: +N tin (5 chu de)`; `git -C /Users/Huy/Claude/diem-tin-the-gioi add index.html logs/`
  (phải có `logs/state.json`). Push `main` (deploy → GitHub Pages): `git -C /Users/Huy/Claude/diem-tin-the-gioi push origin main`.
  Push bị từ chối → `git -C /Users/Huy/Claude/diem-tin-the-gioi pull --rebase origin main` rồi push lại.
- **Gửi bản tin + file Word tự động**: GitHub Action `notify-email.yml` bắt commit `Cap nhat ban tin`
  → xuất .docx toàn bộ tin vừa quét (đúng format bản tin mẫu) + gửi **Telegram** (`send_telegram.py`).
  KHÔNG cần làm gì thêm trong skill — chỉ cần commit đúng mẫu `Cap nhat ban tin ...`.
  ⚠️ Action còn có **cổng khung giờ**: chỉ bắn ở 03:30–07:00 hoặc ≥20:30 giờ VN. Quét TAY giữa ngày thì
  Action im, tin nằm chờ ca tối — đó là hành vi ĐÚNG, đừng đi truy bug (chi tiết: CLAUDE.md mục
  "CHỈ CÓ 2 CA BẮN EMAIL BẢN TIN MỖI NGÀY").
- Ghi log `[$T] DONE: ...`. FAIL ở bước nào cũng VẪN push log.

## Bước 6 — Tóm tắt cuối
Ngắn gọn: số tin mỗi chủ đề (Nội bộ Mỹ / Úc-Biển Đông / CNQS Mỹ / Mali / Predator), chủ đề nào thiếu +
lý do (đã nới 48h chưa), nguồn nổi bật, trạng thái push. KHÔNG liệt kê lại nội dung từng tin.

⚠️ **NÊU RÕ BƯỚC NÀO BỊ CẮT — ngay trong tóm tắt gửi Huy, không chỉ chôn trong `scan-gaps.json`**
(rút từ 27/07/2026: Huy bảo "quét nhanh 15 phút", Zim cắt vòng Báo Mới, có ghi vào `scan-gaps.json`
nhưng **không nói trong báo cáo cuối** — nên Huy phải tự hỏi lại "mày vẫn quét Báo Mới chứ?"). Áp cho
mọi lần rút gọn quy trình dù vì lý do gì (Huy giục nhanh, sát hạn chót 21:45, nguồn chết, agent lỗi):
liệt kê thẳng **bước bị bỏ + vì sao + hệ quả** thành một dòng riêng. Huy bác bỏ cũng được, nhưng phải
được biết mà bác — im lặng cắt bước là thứ Huy không có cách nào phát hiện.

## Phụ lục — NGUỒN MỞ RỘNG theo 5 chủ đề (bổ sung 25/07/2026)
Agent điều phối chọn vài nguồn hợp chủ đề rồi nhúng vào prompt agent (đừng dán cả phụ lục). Ưu tiên
tầng 1 (chính thức, link thẳng) → wire (Reuters/AP/AFP) → chuyên ngành. Nguồn có RSS thì đưa thẳng URL
cho agent fetch; nguồn không RSS thì dùng WebSearch `site:domain`.

### 1. Nội bộ Mỹ (điều trần + bỏ phiếu thông qua)
- **Bản ghi bỏ phiếu chính thức**: clerk.house.gov/Votes · senate.gov/legislative/LIS/roll_call_lists ·
  congress.gov (tra bill + trạng thái). GovTrack/govtrack.us chỉ để TRA, link bài báo kèm.
- **Uỷ ban** (lịch điều trần + thông cáo): armedservices.house.gov · appropriations.house.gov ·
  foreignaffairs.house.gov · armed-services.senate.gov · appropriations.senate.gov · foreign.senate.gov ·
  banking.senate.gov · intelligence.senate.gov (đủ 101 uỷ ban trong `docs/nguon-chinh-thuc-my.md`).
- **Video/tường thuật**: C-SPAN (c-span.org). **Báo chuyên Quốc hội**: The Hill, Politico, Roll Call,
  Punchbowl News, NOTUS (notus.org), CQ. **Cơ quan liên bang**: Government Executive (govexec.com),
  Federal News Network. **Phân tích luật**: CRS (crsreports.congress.gov).

### 2. Úc & Biển Đông
- **Úc chính thức**: defence.gov.au · minister.defence.gov.au · pm.gov.au · dfat.gov.au · aph.gov.au
  (nghị viện). **Phân tích Úc**: ASPI The Strategist (aspistrategist.org.au), Lowy Interpreter
  (lowyinstitute.org/the-interpreter). **Báo Úc**: ABC News AU (abc.net.au), The Australian, SMH,
  Defence Connect (defenceconnect.com.au), Australian Defence Magazine, ADBR.
- **Biển Đông**: AMTI/CSIS (amti.csis.org — bản đồ/phân tích) · Philippine Coast Guard (coastguard.gov.ph) ·
  Philippine News Agency (pna.gov.ph) · Rappler · Inquirer · Philstar · GMA News · Manila Bulletin ·
  BenarNews · Radio Free Asia · The Maritime Executive · gCaptain · Naval News · Nikkei Asia · SCMP ·
  VN: vietnamplus.vn, thanhnien.vn. **TQ (chỉ phát ngôn của họ)**: mod.gov.cn, mfa.gov.cn.

### 3. CNQS Mỹ
- **Chính thức**: defense.gov · war.gov/News/Contracts (hợp đồng hằng ngày) · navy.mil · army.mil ·
  af.mil · spaceforce.mil · dvidshub.net · DARPA (darpa.mil) · Missile Defense Agency (mda.mil) ·
  DIU (diu.mil) · NAVSEA. **Chuyên ngành**: Defense News, Breaking Defense, Defense One, Naval News,
  USNI News, C4ISRNet, SpaceNews, Air & Space Forces Magazine, DefenseScoop, The War Zone, National
  Defense Magazine (nationaldefensemagazine.org), Defense Daily, Inside Defense, Aviation Week, Naval
  Technology. **Nhà thầu (thông báo của họ)**: Lockheed Martin, RTX, Boeing, Northrop Grumman, General
  Dynamics. *Kiểm chứng thêm*: Janes, SIPRI, Army Recognition (chỉ tham khảo).

### 4. Mỹ–Mali (JNIM/Sahel)
- **Chính thức**: africom.mil (AFRICOM — chính) · defense.gov · state.gov · centcom.mil. **Theo dõi
  khủng bố/JNIM**: FDD Long War Journal (longwarjournal.org) · Jamestown Foundation (Terrorism Monitor /
  Militant Leadership Monitor) · Critical Threats (criticalthreats.org — AEI). **Dữ liệu xung đột**:
  ACLED (acleddata.com). **Phân tích Phi**: ISS Africa (issafrica.org) · Africa Center for Strategic
  Studies (africacenter.org). **Báo**: Reuters, AP, AFP, WaPo, France24/RFI, Al Jazeera, Jeune Afrique,
  The Africa Report, BBC Africa.

### 5. Predator's Run 2026 (Mỹ–Úc–Philippines)
- **Chính thức**: pacom.mil (INDOPACOM) · usarpac.army.mil (US Army Pacific) · marines.mil / III MEF ·
  army.mil · defence.gov.au · army.gov.au (Australian Army, 1st Division) · dvidshub.net (thông cáo +
  ảnh diễn tập). **Philippines**: Philippine Army, AFP (armedforces). **Báo**: ABC News AU, Defence
  Connect, ADBR, The Townsville Bulletin (địa phương), Naval News. Từ khoá WebSearch: "Predator's Run
  2026", "Exercise Carabaroo 2026".

### ✅ RSS nguồn mở rộng — ĐÃ VERIFY BẰNG FETCH THẬT 25/07/2026
Chạy tốt (đưa THẲNG URL cho agent):
| Nguồn | RSS URL | item |
|---|---|---|
| The Hill (chung) | https://thehill.com/feed/ | 100 |
| The Hill — Defense | https://thehill.com/policy/defense/feed/ | 15 |
| Roll Call | https://rollcall.com/feed/ | 10 |
| Government Executive | https://www.govexec.com/rss/all/ | 22 |
| ABC News AU (world) | https://www.abc.net.au/news/feed/51120/rss.xml | 25 |
| Lowy Interpreter | https://www.lowyinstitute.org/the-interpreter/rss.xml | 50 |
| AMTI/CSIS (Biển Đông) | https://amti.csis.org/feed/ | 10 |
| Rappler | https://www.rappler.com/feed/ | 10 |
| Philstar (headlines) | https://www.philstar.com/rss/headlines | 10 |
| Inquirer | https://www.inquirer.net/fullfeed/ | 20 |
| gCaptain | https://gcaptain.com/feed/ | 12 |
| Naval Technology | https://www.naval-technology.com/feed/ | 10 |
| The War Zone (TWZ) | https://www.twz.com/feed | 44 |
| DefenseScoop | https://defensescoop.com/feed/ | 10 |
| Aviation Week | https://aviationweek.com/rss.xml | 10 |
| Long War Journal (Mali/JNIM) | https://www.longwarjournal.org/feed | 30 |
| DVIDS news (Predator) | https://www.dvidshub.net/rss/news | 20 |

Bổ sung 25/07/2026 — gộp từ kho tư liệu `docs/diemtin-*-sources.md`, đã fetch thật cùng ngày:
| Nguồn | RSS URL | item | Chủ đề |
|---|---|---|---|
| Defense Daily | https://www.defensedaily.com/feed/ | 50 | 3 |
| Air & Space Forces Magazine | https://www.airandspaceforces.com/feed/ | 9 | 3 |
| Military Times | https://www.militarytimes.com/arc/outboundfeeds/rss/ | 25 | 3 |
| FlightGlobal | https://www.flightglobal.com/rss/ | 10 | 3 |
| The Aviationist | https://theaviationist.com/feed/ | 15 | 3 |
| Soldier Systems Daily | https://soldiersystems.net/feed/ | 6 | 3 |
| Sandboxx News | https://www.sandboxx.us/news/feed/ | 15 | 3 |
| DVIDS (toàn bộ, rộng hơn /rss/news) | https://www.dvidshub.net/rss/all | 419 | 3 + 5 |
| Shephard Media | https://www.shephardmedia.com/news/feed/ | 10 | 3 + 2 |
| The Japan Times | https://www.japantimes.co.jp/feed/ | 30 | 2 |
| Yonhap | https://en.yna.co.kr/RSS/news.xml | 97 | 2 |
| AllAfrica | https://allafrica.com/tools/headlines/rdf/latest/headlines.rdf | 30 | 4 |
| Federal News Network — Defense | https://federalnewsnetwork.com/category/defense-main/feed/ | 15 | 1 |
| Atlantic Council | https://www.atlanticcouncil.org/feed/ | 100 | phân tích |
| Foreign Policy | https://foreignpolicy.com/feed/ | 25 | phân tích |
| Bellingcat | https://www.bellingcat.com/feed/ | 10 | OSINT |
| The Guardian — World | https://www.theguardian.com/world/rss | 45 | chung |
| Semafor | https://www.semafor.com/rss.xml | 261 | chung |
| NPR — World | https://feeds.npr.org/1004/rss.xml | 10 | chung |
| VietnamPlus (TTXVN) | https://www.vietnamplus.vn/rss/thegioi.rss | 50 | 2 · VN |
| Nhân Dân | https://nhandan.vn/rss/thegioi-1231.rss | 50 | VN |
| Báo Chính phủ | https://baochinhphu.vn/quoc-te.rss | 50 | VN |
| VietnamNet | https://vietnamnet.vn/rss/the-gioi.rss | 1000 | VN |
| Báo Thế giới & Việt Nam | https://baoquocte.vn/rss_feed/ | 25 | VN ngoại giao |

Nguồn VN là **ưu tiên #2** (tiếng Anh trước) — dùng khi cần góc trong nước hoặc tin Biển Đông.
**Feed CHẾT, đừng thử lại:** CSIS `csis.org/rss.xml` (bài mới nhất 2016) · War on the Rocks (403) ·
DARPA `darpa.mil/rss.xml` (không phân giải tên miền) → WebSearch `site:...`.

KHÔNG có RSS dùng được → **WebSearch `site:domain`** (đã thử, 403/404/0-item 25/07): NOTUS
(notus.org) · Punchbowl (trả phí) · C-SPAN · Defence Connect · ADBR · Philippine News Agency
(pna.gov.ph) · Manila Bulletin (mb.com.ph) · Radio Free Asia (rfa.org) · The Maritime Executive ·
National Defense Magazine · Jeune Afrique · The Africa Report · RFI (rfi.fr) · ISS Africa (issafrica.org).
Nguồn chính thức (.gov/.mil/committee) vốn ít RSS ổn định — mặc định WebSearch `site:...`.
