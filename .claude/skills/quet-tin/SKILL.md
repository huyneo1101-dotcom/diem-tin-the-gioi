---
name: quet-tin
description: >-
  Quét và cập nhật bản tin cho dự án "Điểm Tin Thế Giới" (worldNews · usNews · xNews ·
  tập trận · sự kiện ngoại giao). Dùng khi người dùng yêu cầu "quét tin", "cập nhật bản
  tin", "scan tin", hoặc khi Routine tự động chạy. Đóng gói kiến trúc 8 agent Sonnet, mô
  hình nguồn 3 tầng, ưu tiên nguồn chính phủ, ràng buộc chất lượng, guardrail add_news.py,
  chỉ tiêu số lượng và log. Chi tiết nguồn/RSS xem CLAUDE.md ở gốc repo.
---

# Skill: Quét tin "Điểm Tin Thế Giới"

Playbook vận hành để cập nhật bản tin. `CLAUDE.md` ở gốc repo là tài liệu tham chiếu ĐẦY ĐỦ
(bảng nguồn 3 tầng, URL RSS, cấu trúc `DATA`). Skill này là quy trình CHẠY từng bước.

## Nguyên tắc cốt lõi
- **Chất lượng > số lượng.** Thà ít tin đạt chuẩn còn hơn nhồi tin sai. Được phép trả mảng rỗng.
- **Nguồn 3 tầng (chuẩn INTREP):** sự kiện ← nguồn CHÍNH THỨC (tầng 1); số liệu ← nguồn DỮ LIỆU
  (tầng 2: IMF/WB/OECD/SIPRI...); nhận định (`significance`) ← VIỆN NGHIÊN CỨU (tầng 3). Báo chí
  chỉ để PHÁT HIỆN tin, luôn đối chiếu.
- **Ưu tiên nguồn chính phủ/chính thức**: khi tin từ thông báo chính thức, link THẲNG nguồn gốc
  (defense.gov, state.gov, nato.int, mofa..., baochinhphu.vn) thay vì báo dẫn lại. Truyền thông
  nhà nước độc tài (Xinhua/TASS/Global Times/KCNA) chỉ dùng cho phát ngôn của chính họ.
- **KHÔNG đọc trực tiếp `index.html` (~180KB)** — dùng grep + `scripts/add_news.py`.
- **KHÔNG tự sửa `index.html` bằng tay** — chèn tin qua script.

## Bước 0 — Log SỚM + idempotent (QUAN TRỌNG — push log NGAY để luôn có dấu vết)
```
NGAY=$(TZ='Asia/Ho_Chi_Minh' date +%F); T=$(date -u +%H:%MZ)
```
- Ghi `[$T] START` vào `logs/scan-$NGAY.log` rồi **commit + push NGAY LẬP TỨC**:
  `git add logs/ && git commit -q -m "log: start $NGAY $T" && git push origin main -q`
  (Bắt buộc push sớm: session tự động là ephemeral, nếu chết giữa lúc quét mà chưa push thì mất
  sạch dấu vết — đây chính là lý do trước đây Routine fail mà không có log nào.)
- **Checkpoint sau MỖI mốc lớn** (xong baseline · xong các agent · xong script · trước khi push tin):
  ghi thêm 1 dòng `[<giờ>] <mốc>: <tóm tắt>` vào log rồi push ngay → biết chính xác chết ở đâu.
- Idempotent — **dùng cờ riêng của pipeline `web-scan`, KHÔNG dùng `generatedAt`**:
  ```
  python3 scripts/state.py check web-scan
  ```
  In `SKIP` → buổi này đã quét xong: ghi log `SKIP`, push log, KẾT THÚC. In `RUN` → quét tiếp.
  Cờ tách theo BUỔI (`sang` trước 14:00 VN, `toi` từ 14:00) nên bản sáng không chặn bản tối.
  (`generatedAt` là ngày bản tin hiển thị trên web — Action nhập tin từ Drive lúc 08:00 cũng bump nó,
  nên dùng nó làm cờ sẽ khiến phiên quét SKIP oan. Đã xảy ra 20–21/07/2026.)
- **Chạy lúc 09:15 & 20:15 VN** (dự phòng 10:15 & 21:15 — tự no-op nếu mốc chính đã DONE).
  Trước đó Action đã nạp sẵn: `import-news-from-drive` (08:00/20:00) + `sync-baomoi` (08:05/20:05, sinh `baomoi-saved.json` + `baomoi-topics.json`).
  **Kéo bản mới nhất về trước khi làm gì**: `git pull --rebase origin main` — nếu không sẽ quét
  trùng đúng những tin 2 Action vừa nạp.
- Nếu lỗi ở bất kỳ bước nào: ghi `[<giờ>] FAIL tại <bước>: <lý do ngắn>`, chạy
  `python3 scripts/state.py fail web-scan "<lý do>"` (FAIL không chặn lần fire sau), push log, rồi dừng.

## Bước 1 — Nguồn + dữ liệu nền
**Nguồn quét lấy từ `CLAUDE.md`** (tự nạp trong context): đọc mục **"Nguồn theo 3 tầng"** (chính
thức · dữ liệu · phân tích · báo chí) và bảng **"URL RSS đã biết"** để biết dùng nguồn nào cho
category nào và URL RSS tương ứng. Skill không tự chứa danh sách nguồn — CLAUDE.md là nguồn chân lý
duy nhất (tránh lệch khi cập nhật).

Sau đó lấy dữ liệu nền (chỉ grep, không đọc cả file):
```
grep -oE '"sourceName":"[^"]+"' index.html | sort | uniq -c | sort -rn   # nguồn đã dùng nhiều → né
python3 scripts/add_news.py --recent-titles 20                          # tiêu đề gần đây → chống trùng
python3 scripts/add_news.py --baomoi-pending                            # 2 nhóm Báo Mới → Agent 7 + 8
```
Output `--recent-titles` đã bao gồm tin Action Drive vừa nạp lúc 08:00/20:00 → nhúng nguyên khối
vào prompt mọi agent là tự động né trùng với bản tin Drive.

**Đọc sở thích người đọc** (suy từ 👍/👎) để điều hướng mềm — đọc file LOCAL, không cần mạng ngoài:
```
cat preferences.json   # {stats:[{scope,key,up,down,net,total}]} — GitHub Action tu cap nhat hang ngay tu Supabase
```
Dùng `net` (👍−👎) làm điểm: `scope=category/region/source`, điểm dương → ưu tiên; điểm âm → giảm ưu tiên.
Nếu `stats` rỗng → chưa có vote, quét bình thường. KHÔNG tự WebFetch Supabase khi quét: `*.supabase.co` bị
Cloudflare chặn 403 từ môi trường quét — việc lấy dữ liệu đã do GitHub Action `sync-preferences.yml` lo.
Giao diện KHÔNG hiển thị phân tích sở thích (theo yêu cầu người dùng) — chỉ thu vote; phân tích là việc của
quy trình quét từ `preferences.json`.

Áp dụng: chuyên mục/khu vực/nguồn điểm dương (`net`>0) → ưu tiên hơn; điểm âm → giảm ưu tiên (vẫn giữ
tối thiểu 2 tin/category theo CLAUDE.md, không bỏ hẳn mục nào, không ghi đè quy tắc nguồn 3 tầng). Nhúng
top ưu tiên / cần tránh vào prompt agent ở Bước 2.

## Bước 2 — Giao 8 agent Sonnet (song song, `model: "sonnet"`, run_in_background:false)
| Agent | Phạm vi | Sản lượng (khung 2 ngày, best-effort) |
|---|---|---|
| 1 | Kinh tế — worldNews + usNews | 1–2 mỗi mục (CHỈ vĩ mô/chính sách/chuỗi cung ứng chiến lược) |
| 2 | Chính trị — worldNews + usNews | 1–2 mỗi mục (CHỈ thể chế/luật/chiến lược great-power) |
| 3 | Công nghệ quân sự — worldNews + usNews | **2–4 mỗi mục** (chủ đề thích nhất) |
| 4 | Ngoại giao — worldNews + usNews | **2–4 mỗi mục** (hiệp định/khuôn khổ an ninh-QP có kết quả) |
| 5 | xNews | 2–4 tin (ưu tiên QP/an ninh/chính thức) |
| 6 | exercises + dipEvents (cập nhật `ongoing` + tạo sự kiện ngoại giao mới nếu có) | 1–2 mỗi loại |
| 7 | **Báo Mới — bài đã lưu** (viết `summary` + `significance`) | TẤT CẢ bài trong nhóm "BÀI ĐÃ LƯU" |
| 8 | **Báo Mới — ứng viên chuyên mục** (chọn lọc) | **3–6 bài** tốt nhất trong kho ~50–100 ứng viên |

Cả 2 agent này KHÔNG quét web tìm tin mới — chỉ xử lý danh sách có sẵn từ
`python3 scripts/add_news.py --baomoi-pending` (bước 1). Output lệnh đó tách sẵn 2 nhóm; nhúng
NGUYÊN KHỐI nhóm tương ứng vào prompt từng agent. Cả 2 nhóm đã được lọc "đăng trong 24h" — **KHÔNG
nới khung này**, và không có bài nào trong nhóm thì bỏ qua agent tương ứng.

Việc chung của cả 2: mở `sourceUrl` (WebFetch) đọc nội dung thật → viết `summary` 2–3 câu +
`significance` (ý nghĩa chiến lược) đúng giọng bản tin; không đọc được thì viết từ tiêu đề, KHÔNG
bịa chi tiết. Giữ nguyên `date`/`title`/`sourceName`/`sourceUrl`; sửa `category`/`region` nếu bộ
từ khoá phân loại sai (`category` chỉ trong 4 mục hợp lệ).

Khác nhau ở chỗ:
- **Agent 7 — bài đã lưu**: người dùng TỰ tay bookmark → lấy **HẾT**, **KHÔNG áp bộ lọc sở thích**
  (không loại vì "không hợp gu"). Trả về field **`baomoiNews`** → web gắn nhãn 📌 Đã lưu.
- **Agent 8 — ứng viên chuyên mục**: đây là feed công khai, phần lớn là nhiễu → **ÁP ĐÚNG bộ lọc sở
  thích** như tin thường (loại cáo phó/drama/horserace/lợi nhuận doanh nghiệp đơn lẻ...), ưu tiên
  Công nghệ quân sự + Ngoại giao, mỗi bài một sự kiện KHÁC nhau, né trùng với `--recent-titles`.
  Chỉ chọn **3–6 bài** đáng đưa nhất. Trả về field **`worldNews`** như tin thường (KHÔNG phải
  `baomoiNews`, không gắn nhãn 📌 — đây không phải bài người dùng lưu).
  **KHÔNG cần liệt kê các bài không chọn** — `add_news.py` tự lấy 10 bài trong số còn lại đổ vào
  mục 🚫 Bị loại (chia đều 4 chuyên mục theo vòng xoay, ~3-3-2-2), khỏi tốn token viết lại.

Tổng thực tế ~10–20 tin/ngày (CHỈ 2 ngày gần nhất) — đủ thì lấy, thiếu thì thôi, KHÔNG nới ngày/bộ lọc. Dồn cho Công nghệ quân sự + Ngoại giao. Xem chỉ tiêu + **Bộ LỌC SỞ THÍCH** trong CLAUDE.md.

**Nhúng vào MỌI prompt agent** (agent KHÔNG thấy hội thoại chính — viết prompt độc lập):
- **BỘ LỌC SỞ THÍCH (bắt buộc — từ `preferences.md`/CLAUDE.md):** ƯU TIÊN khí tài/hệ thống QP cụ thể,
  hiệp định an ninh-QP, Kinh tế vĩ mô/chuỗi cung ứng chiến lược, Chính trị thể chế/chiến lược. **LOẠI BỎ**:
  cáo phó/người qua đời, chính trị nhân vật/bê bối/drama, đua bầu cử horserace, lợi nhuận công ty đơn lẻ
  (trừ khi gắn QP/chip-AI/chuỗi cung ứng), nội bộ xã hội-tư pháp thuần, Nga–Ukraine chiến sự lặp lại.
- **Ràng buộc chất lượng**: (a) `date` CHỈ **2 ngày gần nhất — hôm nay + hôm qua** (giờ VN), không lấy cũ hơn; (b) `sourceUrl` trỏ
  THẲNG 1 bài viết cụ thể, KHÔNG trang chủ / "live" / live-blog / tổng hợp, link KHỚP nội dung;
  (c) `sourceName` chỉ trong danh sách nguồn được giao HOẶC nguồn chính thức phù hợp; (d) xNews:
  KHÔNG bịa status ID (ID thật ~19 chữ số ngẫu nhiên, không tròn số); (e) thà ít còn hơn sai.
- **Ưu tiên nguồn chính phủ** khi tin từ thông báo chính thức (link thẳng nguồn gốc).
- **Ưu tiên nguồn ít dùng** (theo output bước 1) và **tiếng Anh + có RSS** trước (URL RSS: xem
  bảng trong CLAUDE.md — đưa thẳng URL cho agent, đừng bắt tự dò).
- **Đa dạng sự kiện**: mỗi tin 1 sự kiện KHÁC NHAU; không để nhiều báo đưa cùng 1 chuyện thành
  nhiều tin.
- **Chống trùng**: dán NGUYÊN khối output `--recent-titles` (bước 1) vào prompt TẤT CẢ 6 agent;
  dặn không report lại tin/sự kiện đã có kể cả dưới góc nhìn khác.
- **Cảnh báo mâu thuẫn dữ liệu**: tóm tắt trạng thái sự kiện đang tiếp diễn (vd Mỹ-Iran) và dặn
  agent không đưa tin mâu thuẫn.
- **THU tin bị loại vì NGÀY (bắt buộc — để mục 🚫 Bị loại luôn có tin mới mỗi ngày):** mỗi agent
  category, ngoài mảng tin ĐẠT, phải trả THÊM mảng `rejectedNews` gồm các tin **đúng CHỦ ĐỀ THÍCH**
  mà agent tìm thấy nhưng phải bỏ **vì đăng ngoài khung 2 ngày** (tức 3-7 ngày trước) — KÈM
  `sourceUrl` thẳng bài cụ thể + `reason` (vd "ngoài khung 2 ngày, đăng 11/07"). Đây chính là lứa tin
  "vừa rơi khỏi khung" để người dùng rà/cứu; KHÔNG chỉ nêu bằng văn xuôi. Mỗi agent ~3-6 tin loại là đủ.
- Yêu cầu agent CHỈ trả JSON kết quả, không giải thích dài.

**Agent 6 — tạo sự kiện ngoại giao mới**: được phép TẠO `newDipEvents` cho ký kết song/đa phương,
thượng đỉnh, thăm cấp cao có kết quả, sáng kiến lớn (KHÔNG cho điện đàm/phát ngôn lẻ). Mỗi sự kiện
đủ `name/status/dates/location/scale/summary` + ≥1 `items`. Nếu sự kiện giống cái đã có → dùng
`dipEventUpdates` thay vì tạo mới (script sẽ chặn nếu trùng).

## Bước 3 — Review + gộp
Session điều phối **tự review từng tin** theo ràng buộc chất lượng, loại tin không đạt (sai ngày,
link rác/không khớp, trùng chéo mục, mâu thuẫn, ID nghi bịa, nguồn ngoài danh sách).

**BẮT BUỘC ghi tin bị loại** vào 2 nơi: (a) `logs/loai-tin.md` (append 1 mục ngày mới, dạng chữ để
người dùng đọc: `[chủ đề/mục] tiêu đề (nguồn, ngày) — lý do loại`, **⭐ để riêng lên đầu** các tin
CHỦ ĐỀ THÍCH — Công nghệ quân sự · Ngoại giao · Kinh tế vĩ mô — bị loại); (b) field **`rejectedNews`**
trong `/tmp/new_items.json` (dạng có cấu trúc, để hiện ở mục **🚫 Bị loại** trên web — người dùng bấm
👍 cứu vào Bài mới / 👎 xác nhận không thích). Ưu tiên đưa các tin CHỦ ĐỀ THÍCH bị loại (nhất là loại
do ngày/nghi trùng) vào `rejectedNews` để người dùng có cơ hội cứu.

Gộp tin ĐẠT + tin bị loại vào `/tmp/new_items.json`:
```json
{
  "date": "YYYY-MM-DD",
  "worldNews": [ ... ], "usNews": [ ... ], "xNews": [ ... ],
  "baomoiNews": [ ... ],
  "exerciseUpdates": [ {"name":"<tên đúng đã có>","items":[ ... ]} ],
  "dipEventUpdates": [ {"name":"<tên đúng đã có>","items":[ ... ]} ],
  "newDipEvents": [ {"name","status","dates","location","scale","summary","items":[ ... ]} ],
  "rejectedNews": [ {"date","category","title","summary","sourceName","sourceUrl","region","reason":"<lý do loại>"} ]
}
```
`rejectedNews` KHÔNG bị guardrail ngày/trùng-DATA (là tin bị loại, có thể cũ) — chỉ cần `title`+`sourceUrl`+`reason`.
Nếu một tin phẳng được nâng thành `newDipEvents`, bỏ nó khỏi worldNews/usNews để URL không trùng.

## Bước 4 — Chèn bằng script (guardrail chặn lần cuối)
```
python3 scripts/add_news.py /tmp/new_items.json
```
Script **CHẶN** (sửa JSON rồi chạy lại): thiếu field; category sai; date ngoài khung (>5 ngày/tương
lai); URL trang chủ/live-blog; URL trùng trong batch hoặc đã có trong DATA; status ID X nghi bịa;
tên exercise/dipEvent (`*Updates`) không khớp; tên `newDipEvents` trùng sự kiện đã có (Jaccard≥0.6)
hoặc thiếu field. **CẢNH BÁO** (không chặn): nguồn lạ; tiêu đề nghi trùng; phần chưa đủ chỉ tiêu.
- Đọc bảng phân bổ category script in ra. Category nào <2 tin (world/us) → giao thêm 1 agent Sonnet
  bổ sung riêng phần đó rồi chạy lại (script cộng dồn an toàn nếu cùng `date`).
- Nếu thật sự không đủ tin sạch → chấp nhận, nêu rõ trong tóm tắt.

## Bước 5 — Xuất bản + log
- Đánh dấu xong: `python3 scripts/state.py done web-scan "+N tin (TG +x, My +y, X +z)"` — CHỈ gọi khi
  thật sự nạp được tin; lô rỗng thì dùng `skip` để lần fire sau còn quét lại.
- Commit: `Cap nhat ban tin DD/MM: +N tin (TG +x, My +y, X +z)`; `git add index.html logs/`
  (`logs/state.json` nằm trong đó — phải commit kèm, nếu không lần fire sau sẽ quét lại từ đầu).
- Push nhánh `main` (branch deploy → GitHub Pages tự cập nhật). **Push bị từ chối** (3 GitHub Action
  cũng push vào `main`) → `git pull --rebase origin main` rồi push lại, tối đa vài lần.
- Ghi log `[$T] DONE: ...`. Nếu FAIL ở bất kỳ bước nào, ghi log `FAIL tại <bước>: <lý do>` và VẪN
  push log (git không cần mạng ngoài).

## Bước 6 — Tóm tắt cuối
Ngắn gọn: tổng số tin từng phần, bảng phân bổ category, phần thiếu chỉ tiêu (nếu có), nguồn nổi bật,
trạng thái push. KHÔNG liệt kê lại nội dung từng tin.
