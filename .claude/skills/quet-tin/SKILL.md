---
name: quet-tin
description: >-
  Quét và cập nhật bản tin cho dự án "Điểm Tin Thế Giới". Dùng khi người dùng yêu cầu "quét tin",
  "cập nhật bản tin", "scan tin", hoặc khi Routine tự động chạy. Bản tin CHỈ chạy buổi TỐI 22:00,
  TẬP TRUNG 5 chủ đề: Nội bộ Mỹ (siết) · Úc & Biển Đông · CNQS Mỹ · Mỹ–Mali · tập trận Predator's
  Run 2026. Đóng gói kiến trúc agent Sonnet, mô hình nguồn 3 tầng, guardrail add_news.py, log +
  khoá idempotent. Chi tiết nguồn/RSS xem CLAUDE.md ở gốc repo.
---

# Skill: Quét tin "Điểm Tin Thế Giới" (bản TẬP TRUNG 5 chủ đề — chỉ thị Huy 2026-07-23)

Playbook vận hành để cập nhật bản tin. `CLAUDE.md` ở gốc repo là tài liệu tham chiếu ĐẦY ĐỦ
(bảng nguồn 3 tầng, URL RSS, cấu trúc `DATA`). Skill này là quy trình CHẠY từng bước.

## ⭐ PHẠM VI MỚI (2026-07-23 — GHI ĐÈ mọi mô tả 4-chuyên-mục / sàn 15+15 cũ)
Bản tin **CHỈ chạy MỘT lần/ngày, buổi TỐI 22:00** (dự phòng 23:00). Mỗi phiên **CHỈ quét 5 chủ đề**,
**mỗi chủ đề 5–10 bài** (best-effort — thiếu thì thôi, KHÔNG bịa):

1. **Nội bộ Mỹ (SIẾT)** — `usNews`, category `Chính trị`. **CHỈ nhận 2 loại:** (a) phiên **điều trần**
   Quốc hội/uỷ ban (hearing, testimony, mark-up, chất vấn quan chức); (b) **kết quả bỏ phiếu THÔNG QUA
   dự luật** (committee vote, floor vote, passage của bill/nghị quyết/NDAA/ngân sách). **LOẠI** phần còn
   lại: drama/đảng phái, chân dung/động thái chính trị gia, horserace bầu cử, biểu tình, nhập cư, cải
   cách tư pháp thuần, bê bối cá nhân.
2. **Úc & Biển Đông** — `worldNews`. **Úc**: AUKUS, QP/khí tài Úc, ADF, an ninh Úc–Mỹ/Nhật/Anh, chính
   sách Thái Bình Dương (region `Ấn Độ Dương - Thái Bình Dương`). **Biển Đông**: chủ quyền biển, đụng
   độ/tuần tra, phán quyết, tập trận, hoạt động Philippines/VN/TQ/Mỹ (region `Đông Á`). category theo
   nội dung (CNQS/Ngoại giao/Chính trị).
3. **CNQS Mỹ** — `usNews`, category `Công nghệ quân sự`. Khí tài/hệ thống cụ thể: tên lửa, phòng không,
   hải quân, không gian/Space Force, laser, AI quân sự, tàu ngầm, drone, siêu vượt âm.
4. **Mỹ–Mali** — `usNews` (dossier `🟤 Mỹ – Mali`). Mỹ cân nhắc/triển khai quân sự ở Mali nhắm JNIM
   (al-Qaeda): không kích drone, phản ứng Mali/Nga (Africa Corps)/JNIM, diễn biến Sahel–Bamako. Tin
   gắn Mali/JNIM/Bamako/Sahel để tự vào dossier. Nguồn: defense.gov, state.gov, centcom.mil (AFRICOM),
   Reuters/AP/AFP, WaPo. 2–5 bài.
5. **Tập trận Predator's Run 2026** (Mỹ–Úc–Philippines, Townsville, tới ~29/7) — cập nhật qua
   `exerciseUpdates`, tên khớp `"Predator's Run 2026 (tập trận Mỹ - Úc - Philippines)"`. Diễn biến mới:
   bài bắn đạn thật, tình huống hợp đồng, tuyên bố chỉ huy. Nguồn: pacom.mil, marines.mil,
   defence.gov.au, dvidshub.net. Kết thúc (~29/7) → đổi `status`→`recent`. 1–2 tin.

**KHÔNG quét** (đã bỏ khỏi phạm vi): Kinh tế, Ngoại giao chung, xNews (X/Twitter), tin thế giới các
vùng khác (Trung Đông, Châu Âu, Nga–Ukraine…), tạo mới dipEvents. Chỉ đụng tới 5 chủ đề trên.

**Khung thời gian: tin trong 24 GIỜ gần nhất** (theo giờ VN). Chủ đề nào **thiếu** (<5 bài) trong 24h
thì **NỚI thành 48 giờ** cho riêng chủ đề đó. KHÔNG nới quá 48h, KHÔNG bịa tin/link.

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
```
NGAY=$(TZ='Asia/Ho_Chi_Minh' date +%F); T=$(date -u +%H:%MZ)
```
- Ghi `[$T] START` vào `logs/scan-$NGAY.log` rồi **commit + push NGAY LẬP TỨC**:
  `git add logs/ && git commit -q -m "log: start $NGAY $T" && git push origin main -q`
  (Session tự động là ephemeral — chết giữa lúc quét mà chưa push thì mất sạch dấu vết.)
- **Checkpoint sau MỖI mốc lớn** (xong baseline · xong các agent · xong script · trước khi push tin):
  ghi thêm dòng `[<giờ>] <mốc>: <tóm tắt>` vào log, chạy `python3 scripts/state.py beat web-scan` rồi
  push ngay → biết chết ở đâu + gia hạn khoá. **Nhịp tim bắt buộc**: khoá tự hết hạn sau 30' không có nhịp.
- Idempotent + khoá — **dùng cờ riêng pipeline `web-scan`, KHÔNG dùng `generatedAt`**:
  ```
  python3 scripts/state.py claim web-scan
  ```
  `SKIP` (exit 10) → buổi này đã quét xong · `SKIP` (exit 11) → **có phiên khác đang chạy**, không quét
  chồng. Cả hai: ghi log `SKIP`, push log, KẾT THÚC. `RUN` (exit 0) → đã giữ khoá, quét tiếp.
  Cờ theo BUỔI: giờ chỉ còn buổi TỐI (`toi`, từ 14:00 VN) — mốc chính 22:00, dự phòng 23:00 tự no-op
  nếu 22:00 đã DONE.
- **Chạy 22:00 VN** (dự phòng 23:00). Trước đó Action đã nạp sẵn: `import-news-from-drive` (20:00) +
  `sync-baomoi` (20:05). **Kéo bản mới nhất về trước khi làm gì**: `git pull --rebase origin main`.
- Lỗi ở bất kỳ bước: ghi `[<giờ>] FAIL tại <bước>: <lý do>`, chạy `python3 scripts/state.py fail
  web-scan "<lý do>"` (nhả khoá + KHÔNG chặn lần fire sau), push log, dừng.

## Bước 1 — Nguồn + dữ liệu nền
Đọc mục **"Nguồn theo 3 tầng"** + bảng **"URL RSS đã biết"** trong `CLAUDE.md` để biết nguồn/URL cho
từng chủ đề (ưu tiên nguồn quốc phòng/chính thức Mỹ + Úc + AFRICOM cho 5 chủ đề này). Lấy dữ liệu nền:
```
grep -oE '"sourceName":"[^"]+"' index.html | sort | uniq -c | sort -rn   # nguồn đã dùng nhiều → né
python3 scripts/add_news.py --recent-titles 20                          # tiêu đề gần đây → chống trùng
python3 scripts/add_news.py --baomoi-pending                            # 2 nhóm Báo Mới
```
Nhúng nguyên khối `--recent-titles` vào prompt MỌI agent để né trùng (gồm cả tin Drive vừa nạp 20:00).
`preferences.json` (👍/👎) chỉ là điều hướng mềm — với phạm vi tập trung này, 5 chủ đề là ưu tiên số 1.

## Bước 2 — Giao agent Sonnet (song song, `model: "sonnet"`, run_in_background:false)
Chỉ **5 luồng** cho 5 chủ đề (gộp Mali+Predator vào 1 agent; Báo Mới 1 agent nếu có bài hợp topic):

| Agent | Chủ đề | Sản lượng (24h, nới 48h nếu thiếu) |
|---|---|---|
| A | **Nội bộ Mỹ (SIẾT)** → `usNews` cat `Chính trị` | **5–10** — CHỈ điều trần + bỏ phiếu thông qua dự luật (xem PHẠM VI MỚI mục 1). Thiếu thì thôi, KHÔNG nới sang drama/đảng phái. |
| B | **Úc & Biển Đông** → `worldNews` | **5–10** — Úc (region IPAC) + Biển Đông (region Đông Á). |
| C | **CNQS Mỹ** → `usNews` cat `Công nghệ quân sự` | **5–10** — khí tài/hệ thống cụ thể. |
| D | **Mỹ–Mali + Predator's Run 2026** | Mali 2–5 (`usNews` dossier) · Predator 1–2 (`exerciseUpdates`). |
| BM | **Báo Mới** (nếu `--baomoi-pending` có bài hợp 5 chủ đề) | Bài ĐÃ LƯU: giữ hết (field `baomoiNews`). Ứng viên chuyên mục: **CHỈ chọn bài hợp 5 chủ đề**, 2–5 bài, `worldNews`/`usNews` như thường. Không có bài hợp → bỏ qua agent này. |

**Agent Báo Mới — TRUY NGƯỢC VỀ NGUỒN GỐC** (giữ nguyên quy tắc cũ): Báo Mới là trang tổng hợp. Với mỗi
bài: mở `sourceUrl` (WebFetch) đọc nội dung, **tìm bài gốc nước ngoài** đúng sự kiện (đăng ≤48h), **mở
WebFetch xác nhận có thật + đúng ngày**, lấy `sourceName`+`sourceUrl`+`title`+`summary`+`significance`
theo bài GỐC (đổi cả tiêu đề lẫn URL). Không tìm được: bài ĐÃ LƯU → giữ link Báo Mới + thêm
`"_baomoiUrl":"<link Báo Mới>"`; ứng viên chuyên mục → bỏ, chọn bài khác. Cả hai chỉ giữ bài hợp 5 chủ đề.

**Nhúng vào MỌI prompt agent** (agent KHÔNG thấy hội thoại chính — viết prompt độc lập, đủ ngữ cảnh):
- **Chủ đề + tiêu chí lọc riêng** của agent đó (copy đúng đoạn PHẠM VI MỚI tương ứng).
- **Khung thời gian: CHỈ tin đăng trong 24 GIỜ gần nhất** (theo giờ VN). Nếu chủ đề khan (<5 bài) →
  được nới thành **48 giờ**. TUYỆT ĐỐI không lấy tin cũ hơn 48h, không bịa.
- **Ràng buộc chất lượng**: (a) `date` đúng khung 24h/48h; (b) `sourceUrl` trỏ THẲNG 1 bài cụ thể,
  KHÔNG trang chủ/"live"/live-blog/tổng hợp, link KHỚP nội dung; (c) `sourceName` trong danh sách nguồn
  được giao HOẶC nguồn chính thức phù hợp; (d) thà ÍT còn hơn sai — được phép trả mảng rỗng.
- **Ưu tiên nguồn chính phủ/chính thức** (link thẳng nguồn gốc) + **nguồn tiếng Anh có RSS** trước
  (URL RSS: xem bảng trong CLAUDE.md, đưa thẳng URL cho agent).
- **Chống trùng**: dán NGUYÊN khối `--recent-titles` (bước 1) vào prompt; dặn không report lại tin đã có.
- **Đa dạng sự kiện**: mỗi tin 1 sự kiện KHÁC NHAU.
- Yêu cầu agent CHỈ trả JSON kết quả (mảng tin của chủ đề đó), không giải thích dài.

## Bước 3 — Review + gộp
Session điều phối **tự review từng tin** theo ràng buộc chất lượng, loại tin không đạt (sai khung giờ,
link rác/không khớp, trùng, không đúng 5 chủ đề, nội bộ Mỹ ngoài phạm vi siết…).

**Ghi tin bị loại** vào `logs/loai-tin.md` (dạng chữ: `[chủ đề] tiêu đề (nguồn, ngày) — lý do`). Field
`rejectedNews` trong JSON là TUỲ CHỌN với phạm vi mới (không bắt buộc gom tin loại như trước) — chỉ thêm
nếu có tin đúng chủ đề nhưng lệch khung giờ, đáng để người dùng cứu.

Gộp vào `/tmp/new_items.json`:
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
Script **CHẶN** (sửa JSON rồi chạy lại): thiếu field; category sai; date ngoài khung (script cho tối đa
2 ngày — 48h nằm trong khung này, OK); URL trang chủ/live-blog; URL trùng trong batch hoặc đã có trong
DATA; tên exercise (`exerciseUpdates`) không khớp entry có sẵn. **CẢNH BÁO** (không chặn): nguồn lạ;
tiêu đề nghi trùng.
- **KHÔNG còn sàn 15+15.** Dòng script in `SÀN CỨNG … X/15 · Y/15` là DI SẢN cũ — **BỎ QUA nó**. Mục
  tiêu mới là **mỗi chủ đề 5–10 bài** (tự đếm theo chủ đề, không theo world/us tổng).
- Chủ đề nào **<5 bài trong 24h** → giao thêm agent cho riêng chủ đề đó với khung **48h**; vẫn thiếu thì
  CHẤP NHẬN (ghi rõ trong tóm tắt), KHÔNG bịa/nhồi. Không lặp vô hạn — 1–2 vòng bổ sung là đủ.

## Bước 5 — Xuất bản + log
- `python3 scripts/state.py done web-scan "+N tin (5 chủ đề)"` — CHỈ khi thật sự nạp được tin; lô rỗng
  thì `skip` để lần fire sau còn quét lại.
- Commit: `Cap nhat ban tin DD/MM: +N tin (5 chu de)`; `git add index.html logs/` (phải có
  `logs/state.json`). Push `main` (deploy → GitHub Pages). Push bị từ chối → `git pull --rebase origin
  main` rồi push lại.
- **Email + file Word tự động**: GitHub Action `notify-email.yml` bắt commit `Cap nhat ban tin` → xuất
  .docx toàn bộ tin vừa quét (đúng format bản tin mẫu) + gửi lamgiaphat1603@gmail.com. KHÔNG cần làm gì
  thêm trong skill — chỉ cần commit đúng mẫu `Cap nhat ban tin ...`.
- Ghi log `[$T] DONE: ...`. FAIL ở bước nào cũng VẪN push log.

## Bước 6 — Tóm tắt cuối
Ngắn gọn: số tin mỗi chủ đề (Nội bộ Mỹ / Úc-Biển Đông / CNQS Mỹ / Mali / Predator), chủ đề nào thiếu +
lý do (đã nới 48h chưa), nguồn nổi bật, trạng thái push. KHÔNG liệt kê lại nội dung từng tin.
