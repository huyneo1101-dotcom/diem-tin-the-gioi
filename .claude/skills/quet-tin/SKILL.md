---
name: quet-tin
description: >-
  Quét và cập nhật bản tin cho dự án "Điểm Tin Thế Giới" (worldNews · usNews · xNews ·
  tập trận · sự kiện ngoại giao). Dùng khi người dùng yêu cầu "quét tin", "cập nhật bản
  tin", "scan tin", hoặc khi Routine tự động chạy. Đóng gói kiến trúc 6 agent Sonnet, mô
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
- **Checkpoint sau MỖI mốc lớn** (xong baseline · xong 6 agent · xong script · trước khi push tin):
  ghi thêm 1 dòng `[<giờ>] <mốc>: <tóm tắt>` vào log rồi push ngay → biết chính xác chết ở đâu.
- Idempotent: `grep -oE '"generatedAt":"[^"]+"' index.html | head -1`. Nếu == `$NGAY` → đã xong:
  ghi `SKIP`, push log, KẾT THÚC (không quét lại).
- Nếu lỗi ở bất kỳ bước nào: ghi `[<giờ>] FAIL tại <bước>: <lý do ngắn>`, push log, rồi dừng.

## Bước 1 — Nguồn + dữ liệu nền
**Nguồn quét lấy từ `CLAUDE.md`** (tự nạp trong context): đọc mục **"Nguồn theo 3 tầng"** (chính
thức · dữ liệu · phân tích · báo chí) và bảng **"URL RSS đã biết"** để biết dùng nguồn nào cho
category nào và URL RSS tương ứng. Skill không tự chứa danh sách nguồn — CLAUDE.md là nguồn chân lý
duy nhất (tránh lệch khi cập nhật).

Sau đó lấy dữ liệu nền (chỉ grep, không đọc cả file):
```
grep -oE '"sourceName":"[^"]+"' index.html | sort | uniq -c | sort -rn   # nguồn đã dùng nhiều → né
python3 scripts/add_news.py --recent-titles 20                          # tiêu đề gần đây → chống trùng
```

**Đọc sở thích người đọc** (suy từ 👍/👎) để điều hướng mềm:
- **Đường chính — `preferences.md`:** đọc bảng trọng số (cập nhật tay từ file `diemtin-sothich.json`
  người đọc export). Đây là cầu nối đáng tin cậy.
- **Thử tự động (best-effort):** WebFetch view `vote_stats` —
  `https://ltmlueqkajqmduoqghdf.supabase.co/rest/v1/vote_stats?select=*&apikey=sb_publishable_74Lm6cc0CkoOOzy3A4IRrQ_BX0jHQcg`
  → JSON `{scope,key,up,down,net}`. ⚠️ `*.supabase.co` **thường 403 với WebFetch** (Cloudflare chặn
  máy chủ — đã kiểm chứng 12/07); nếu lỗi thì BỎ QUA ngay, dùng `preferences.md`. Nếu may mắn đọc được
  thì cập nhật lại bảng trong `preferences.md` cho khớp và commit.

Áp dụng: chuyên mục/khu vực/nguồn điểm dương (`net`>0) → ưu tiên hơn; điểm âm → giảm ưu tiên (vẫn giữ
tối thiểu 2 tin/category theo CLAUDE.md, không bỏ hẳn mục nào, không ghi đè quy tắc nguồn 3 tầng). Nhúng
top ưu tiên / cần tránh vào prompt agent ở Bước 2. Nếu lấy được từ Supabase, cập nhật lại bảng trong
`preferences.md` cho khớp (và commit).

## Bước 2 — Giao 6 agent Sonnet (song song, `model: "sonnet"`, run_in_background:false)
| Agent | Phạm vi | Sản lượng |
|---|---|---|
| 1 | Kinh tế — worldNews + usNews | 2–3 tin mỗi mục |
| 2 | Chính trị — worldNews + usNews | 2–3 tin mỗi mục |
| 3 | Công nghệ quân sự — worldNews + usNews | 2–3 tin mỗi mục |
| 4 | Ngoại giao — worldNews + usNews | 2–3 tin mỗi mục |
| 5 | xNews | 4–5 tin |
| 6 | exercises + dipEvents (cập nhật `ongoing` + tạo sự kiện ngoại giao mới nếu có) | 1–2 mỗi loại |

**Nhúng vào MỌI prompt agent** (agent KHÔNG thấy hội thoại chính — viết prompt độc lập):
- **Ràng buộc chất lượng**: (a) `date` trong 48h–3 ngày, ưu tiên mới nhất; (b) `sourceUrl` trỏ
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
- Yêu cầu agent CHỈ trả JSON kết quả, không giải thích dài.

**Agent 6 — tạo sự kiện ngoại giao mới**: được phép TẠO `newDipEvents` cho ký kết song/đa phương,
thượng đỉnh, thăm cấp cao có kết quả, sáng kiến lớn (KHÔNG cho điện đàm/phát ngôn lẻ). Mỗi sự kiện
đủ `name/status/dates/location/scale/summary` + ≥1 `items`. Nếu sự kiện giống cái đã có → dùng
`dipEventUpdates` thay vì tạo mới (script sẽ chặn nếu trùng).

## Bước 3 — Review + gộp
Session điều phối **tự review từng tin** theo ràng buộc chất lượng, loại tin không đạt (sai ngày,
link rác/không khớp, trùng chéo mục, mâu thuẫn, ID nghi bịa, nguồn ngoài danh sách). Gộp vào
`/tmp/new_items.json`:
```json
{
  "date": "YYYY-MM-DD",
  "worldNews": [ ... ], "usNews": [ ... ], "xNews": [ ... ],
  "exerciseUpdates": [ {"name":"<tên đúng đã có>","items":[ ... ]} ],
  "dipEventUpdates": [ {"name":"<tên đúng đã có>","items":[ ... ]} ],
  "newDipEvents": [ {"name","status","dates","location","scale","summary","items":[ ... ]} ]
}
```
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
- Commit: `Cap nhat ban tin DD/MM: +N tin (TG +x, My +y, X +z)`; `git add index.html logs/`.
- Push nhánh `main` (branch deploy → GitHub Pages tự cập nhật). Ghi log `[$T] DONE: ...`. Nếu FAIL
  ở bất kỳ bước nào, ghi log `FAIL tại <bước>: <lý do>` và VẪN push log (git không cần mạng ngoài).

## Bước 6 — Tóm tắt cuối
Ngắn gọn: tổng số tin từng phần, bảng phân bổ category, phần thiếu chỉ tiêu (nếu có), nguồn nổi bật,
trạng thái push. KHÔNG liệt kê lại nội dung từng tin.
