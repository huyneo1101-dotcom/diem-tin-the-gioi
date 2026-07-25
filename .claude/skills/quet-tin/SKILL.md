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
⚠️ **LỆNH NGUYÊN DẠNG — KHÔNG WRAPPER, KHÔNG BIẾN SHELL** (sự cố 25/07/2026: phiên tối thêm prefix
`cd() { echo "cd disabled"; };` trước lệnh git → harness coi chuỗi `{`+`"` là "expansion obfuscation",
BỎ QUA allowlist, bật prompt xin quyền, routine treo chờ bấm nút). "Không dùng cd" = ĐỪNG GỌI `cd`,
KHÔNG phải vô hiệu hoá nó. Lấy ngày/giờ bằng 2 lệnh riêng `TZ='Asia/Ho_Chi_Minh' date +%F` và
`date -u +%H:%MZ`, rồi ĐIỀN GIÁ TRỊ THẬT vào các lệnh sau (không dùng `$NGAY`/`$T` trong lệnh git).
- Ghi `[<giờ>Z] START` vào `logs/scan-<ngày VN>.log` (tool Write/Edit) rồi **commit + push NGAY LẬP TỨC**:
  `git -C /Users/Huy/Claude/diem-tin-the-gioi add logs/ && git -C /Users/Huy/Claude/diem-tin-the-gioi commit -q -m "log: start <ngày> <giờ>Z phien toi" && git -C /Users/Huy/Claude/diem-tin-the-gioi push origin main -q`
  (Session tự động là ephemeral — chết giữa lúc quét mà chưa push thì mất sạch dấu vết.)
- **Checkpoint sau MỖI mốc lớn** (xong baseline · xong các agent · xong script · trước khi push tin):
  ghi thêm dòng `[<giờ>] <mốc>: <tóm tắt>` vào log, chạy `python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/state.py beat web-scan` rồi
  push ngay → biết chết ở đâu + gia hạn khoá. **Nhịp tim bắt buộc**: khoá tự hết hạn sau 30' không có nhịp.
- Idempotent + khoá — **dùng cờ riêng pipeline `web-scan`, KHÔNG dùng `generatedAt`**:
  ```
  python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/state.py claim web-scan
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
Đọc mục **"Nguồn theo 3 tầng"** + bảng **"URL RSS đã biết"** trong `CLAUDE.md`, VÀ **Phụ lục "NGUỒN MỞ
RỘNG theo 5 chủ đề"** ở cuối skill này (danh sách nguồn cụ thể cho từng chủ đề — chọn vài nguồn hợp rồi
nhúng vào prompt agent). Ưu tiên nguồn quốc phòng/chính thức Mỹ + Úc + AFRICOM cho 5 chủ đề này. Lấy dữ liệu nền:
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
> ⚠️ **`date` batch = NGÀY TIN MỚI NHẤT trong lô** (thường là hôm qua nếu quét sau nửa đêm / máy chạy
> trễ), KHÔNG phải ngày hệ thống. Script chặn tin cũ hơn 1 ngày so với `date` này — neo sai (theo hôm
> nay) sẽ chặn oan tin nới-48h.
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
Script **CHẶN** (sửa JSON rồi chạy lại): thiếu field; category sai; date ngoài khung (`MAX_AGE_DAYS=1`
— script chỉ cho lùi TỐI ĐA 1 ngày so với `date` batch. Vì vậy đặt `date` batch = **NGÀY TIN MỚI NHẤT
trong lô**, KHÔNG neo theo ngày hệ thống; khi đó tin nới-48h = hôm trước vẫn khít khung 1 ngày. Nếu neo
`date` theo hôm nay mà tin mới nhất là hôm qua thì tin 48h bị chặn oan — lỗi hay mắc); URL trang
chủ/live-blog; URL trùng trong batch hoặc đã có trong
DATA; tên exercise (`exerciseUpdates`) không khớp entry có sẵn. **CẢNH BÁO** (không chặn): nguồn lạ;
tiêu đề nghi trùng.
- **KHÔNG còn sàn 15+15.** Dòng script in `SÀN CỨNG … X/15 · Y/15` là DI SẢN cũ — **BỎ QUA nó**. Mục
  tiêu mới là **mỗi chủ đề 5–10 bài** (tự đếm theo chủ đề, không theo world/us tổng).
- Chủ đề nào **<5 bài trong 24h** → giao thêm agent cho riêng chủ đề đó với khung **48h**; vẫn thiếu thì
  CHẤP NHẬN (ghi rõ trong tóm tắt), KHÔNG bịa/nhồi. Không lặp vô hạn — 1–2 vòng bổ sung là đủ.

## Bước 5 — Xuất bản + log
- `python3 scripts/state.py done web-scan "+N tin (5 chủ đề)"` — CHỈ khi thật sự nạp được tin; lô rỗng
  thì `skip` để lần fire sau còn quét lại.
- Commit: `Cap nhat ban tin DD/MM: +N tin (5 chu de)`; `git -C /Users/Huy/Claude/diem-tin-the-gioi add index.html logs/`
  (phải có `logs/state.json`). Push `main` (deploy → GitHub Pages): `git -C /Users/Huy/Claude/diem-tin-the-gioi push origin main`.
  Push bị từ chối → `git -C /Users/Huy/Claude/diem-tin-the-gioi pull --rebase origin main` rồi push lại.
- **Email + file Word tự động**: GitHub Action `notify-email.yml` bắt commit `Cap nhat ban tin` → xuất
  .docx toàn bộ tin vừa quét (đúng format bản tin mẫu) + gửi lamgiaphat1603@gmail.com. KHÔNG cần làm gì
  thêm trong skill — chỉ cần commit đúng mẫu `Cap nhat ban tin ...`.
- Ghi log `[$T] DONE: ...`. FAIL ở bước nào cũng VẪN push log.

## Bước 6 — Tóm tắt cuối
Ngắn gọn: số tin mỗi chủ đề (Nội bộ Mỹ / Úc-Biển Đông / CNQS Mỹ / Mali / Predator), chủ đề nào thiếu +
lý do (đã nới 48h chưa), nguồn nổi bật, trạng thái push. KHÔNG liệt kê lại nội dung từng tin.

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
