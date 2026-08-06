# Mục LỖI THỜI và ngoài phạm vi quét

<!-- Xẻ từ `CLAUDE.md` ngày 06/08/2026 để cắt chi phí token: toàn bộ file gốc được nạp lại
ở MỌI lượt của MỌI phiên đụng repo này (đo thật: ~99.000 token/lượt), trong khi phần lớn nội dung
là NHẬT KÝ VÁ LỖI chỉ cần đọc khi đụng đúng mảng đó.
⚠️ Nội dung dưới đây giữ NGUYÊN VĂN — cả luật lẫn "cơ chế gây vấp". Đừng rút gọn: phần kể lại
cơ chế chính là thứ ngăn phiên sau dựng lại đúng cái lỗi cũ.
⚠️ CLAUDE.md còn dòng trỏ sang từng mục. Đổi tên mục ở đây thì sửa dòng trỏ bên đó. -->

## Tab "Cà phê" (ngoài chủ đề tin — thêm 24-25/07/2026)
Tab **☕ Cà phê**: tìm quán cà phê làm việc HN, xếp theo khoảng cách từ điểm xuất phát. **Mốc xuất phát THEO USER** (Huy chốt 25/07/2026: *"với ngừoi dùng huyneo thì chỉ để 2 điểm xuất phát mặc định… với ngừoi dùng lamgiaphat thì chỉ để điểm mặc định là Trường chinh (ẩn điểm mặc định … với người dùng này)"*) — `huyneo` → **Núi Trúc + Nguyễn Khuyến**; `lamgiaphat` → **Trường Chinh** (ẩn 2 mốc kia); user khác → không có mốc mặc định, tự lưu mốc riêng vào `localStorage dt.cafeLocs`. ⚠ Dòng này từng ghi gộp *"(Giảng Võ/Trường Chinh/GPS)"* — **sai cả cấu trúc lẫn địa danh** (mốc Giảng Võ đã đổi sang Núi Trúc), phát hiện 30/07 khi rà quy tắc chưa ghi. Nguồn sự thật là chú thích ngay trên `renderCafes` trong `index.html`, đừng sửa dòng này rời khỏi code. Dữ liệu `DATA.workCafes` (embed index.html); code `renderCafes`/`cf*`/CSS `.cf-*`. Scheduled task local **`cafe-rating-retry`** (`15 9 * * 2,5`) vét dần rating Google còn thiếu qua `scripts/cafe_ratings.py` (--missing/--apply), commit **`Cap nhat rating quan ca phe: ...`** — tiền tố này KHÔNG khớp gate email nên không gửi mail. Chi tiết: memory `diem-tin-tab-cafe`.

## ~~Chỉ tiêu số lượng (SÀN CỨNG 15+15)~~ — ⚠️ LỖI THỜI 2026-07-23, xem banner đầu file (giờ là 5 chủ đề × 5–10 bài)
**SÀN CỨNG TỔNG NGÀY (gộp cả phiên sáng + tối): `worldNews` ≥ 15 tin · `usNews` ≥ 15 tin — CHẤT LƯỢNG CAO.**
Cơ chế 2 phiên:
- **Phiên SÁNG (10:15):** nhắm **~10 tin/mục** là đủ — không cần ép đủ 15 ngay, để phần còn lại cho tối.
- **Phiên TỐI (20:15):** đọc tín hiệu tổng ngày, **bổ sung cho tổng ngày mỗi mục đạt ≥ 15**. **CHƯA ĐỦ THÌ CHƯA DỪNG** → giao thêm agent Sonnet riêng mục thiếu, chạy lại `add_news.py`, LẶP tới khi cả hai mục ≥15.
- Nếu **một phiên SKIP/FAIL** (phiên kia không chạy): phiên còn lại gánh toàn bộ — kéo tổng ngày lên đủ 15/mục.

Đo bằng: `add_news.py` gắn `_addedDate` = ngày đưa lên cho mỗi tin, dòng cuối in `SÀN CỨNG TỔNG NGÀY … worldNews X/15 · usNews Y/15` (đếm tin `_addedDate == hôm nay`, gộp cả 2 phiên).

"Chất lượng cao" = qua guardrail + đúng nguồn 3 tầng + đúng bộ lọc sở thích + link thẳng bài gốc trong khung 2 ngày. **KHÔNG hạ chuẩn để nhồi cho đủ số**: không bịa tin/link, không lấy tin cũ hơn hôm qua, không nhét tin rác. Chính trị nội bộ Mỹ đã SIẾT còn điều trần + bỏ phiếu thông qua dự luật (xem bộ lọc), nên **sàn 15 tin us giờ dựa chủ yếu vào CNQS + Ngoại giao + Kinh tế us + điều trần/bỏ phiếu** — thiếu thì giao thêm agent các mục đó, TUYỆT ĐỐI KHÔNG nới lại nội bộ Mỹ (đảng phái/drama/horserace...) để lấp cho đủ.

Phân bổ GỢI Ý CẢ NGÀY trong mỗi mục ≥15 (linh hoạt, miễn tổng mục đạt sàn):
| Category | Gợi ý mỗi mục (world / us) |
|---|---|
| **Công nghệ quân sự** | 4–6 tin (chủ đề thích nhất — khí tài/hệ thống cụ thể) |
| **Ngoại giao** | 4–6 tin (hiệp định/khuôn khổ an ninh–QP, thượng đỉnh có kết quả) |
| **Kinh tế** | 2–4 tin (vĩ mô/chính sách/chuỗi cung ứng chiến lược) |
| **Chính trị** | 3–5 tin (world: thể chế/chiến lược great-power · **us nội bộ: CHỈ phiên điều trần + kết quả bỏ phiếu thông qua dự luật**) |
| 🎯 **Trọng tâm chủ động** | **Úc · Biển Đông · Nội bộ Mỹ** — nằm rải trong 4 category trên, mỗi trọng tâm 1–2 tin/phiên nếu có |

| Phần khác | Chỉ tiêu (KHÔNG tính vào sàn 15+15) |
|---|---|
| `xNews` | 2–4 tin (ưu tiên tài khoản QP/an ninh/chính thức) |
| `exercises` (tập trận) | 1–2 tin cập nhật (sự kiện `ongoing`) |
| `dipEvents` (ngoại giao) | **2–4 tin cập nhật + CHỦ ĐỘNG tạo 1–2 sự kiện MỚI mỗi ngày** — mỗi sự kiện PHẢI có `status` đúng: `upcoming` · `ongoing` · `recent` |

→ Tổng **≥30 tin bản tin/ngày** (15 world + 15 us) + xNews + sự kiện. **Fallback bất khả kháng:** chỉ khi đã giao ≥3 vòng agent bổ sung mà vẫn không đủ tin SẠCH (ngày cực khan / môi trường lỗi) mới chấp nhận thiếu — ghi RÕ trong tóm tắt còn thiếu bao nhiêu và vì sao. Thiếu vì lười giao thêm agent thì KHÔNG chấp nhận. Tuyệt đối không bịa để lấp.

### Bộ LỌC SỞ THÍCH (bắt buộc — nhúng vào mọi agent; nguồn: `diemtin-content-prefs.md` + `preferences.md`)
> **Hai hồ sơ, không conflict:** `diemtin-content-prefs.md` = **Hiến chương** (cấu trúc/triết lý/cách viết — thắng khi lệch về mấy thứ đó); `preferences.md`/`preferences.json` = **vote** (tinh chỉnh mức ưu tiên chủ đề). Bảng hoà giải 5 điểm từng lệch (hải quân xếp phụ · ưu tiên nước lớn · Nga–Ukraine chỉ giữ diễn biến MỚI · dung hoà số lượng · nhấn VN–Biển Đông khi gắn quốc tế) nằm CUỐI `diemtin-content-prefs.md` — theo đúng bảng đó.
**ƯU TIÊN (tìm nhiều):** khí tài/công nghệ QP cụ thể (tên lửa, phòng không, hải quân, không gian/Space Force, laser, AI quân sự, tàu ngầm, drone); hiệp định/khuôn khổ an ninh–QP có kết quả (ACSA/RAA/đối tác chiến lược); Kinh tế vĩ mô & định chế (Fed/ECB/BOJ/IMF/OECD/WTO/BIS/WB, nợ công, thuế, chuỗi cung ứng chip); Chính trị THỂ CHẾ/luật/hiến pháp/ngân sách QP/trừng phạt/chiến lược great-power.
**LOẠI BỎ (KHÔNG đưa vào worldNews/usNews):** ❌ cáo phó/người qua đời; ❌ chính trị NHÂN VẬT/bê bối/drama/scandal cá nhân; ❌ đua bầu cử horserace (thắng–thua đảng phái, bầu cử địa phương); ❌ lợi nhuận/vận hành DOANH NGHIỆP đơn lẻ (trừ khi gắn QP / chip–AI / chuỗi cung ứng chiến lược); ❌ chính trị nội bộ xã hội/tư pháp thuần (nhập cư, cải cách công tố…); ❌ tin Nga–Ukraine chiến sự lặp lại.

**🎯 TRỌNG TÂM CHỦ ĐỘNG mỗi phiên — thêm 23/07/2026 (chỉ thị người dùng, GHI ĐÈ các dòng trên khi va chạm):** mỗi lần quét CHỦ ĐỘNG tìm cho đủ 3 trọng tâm này, nhắm **1–2 tin/trọng tâm/phiên nếu có** (best-effort, không đủ thì thôi):
1. **Úc** — AUKUS, quốc phòng/khí tài Úc, ADF, quan hệ an ninh Úc–Mỹ/Nhật/Anh, chính sách Thái Bình Dương của Úc. Gán `region: "Ấn Độ Dương - Thái Bình Dương"`.
2. **Biển Đông** — chủ quyền biển, đụng độ/tuần tra, phán quyết, tập trận, hoạt động của Philippines/VN/TQ/Mỹ ở Biển Đông. Nâng từ "VN chỉ khi gắn quốc tế" thành trọng tâm CHỦ ĐỘNG. Gán `region: "Đông Á"` (hoặc "Ấn Độ Dương - Thái Bình Dương").
3. **Nội bộ Mỹ (usNews) — CHỈ tiến trình lập pháp (chỉ thị người dùng 23/07/2026, siết lại từ "mở toàn bộ"):** với tin CHÍNH TRỊ NỘI BỘ Mỹ, **CHỈ nhận 2 loại**: (a) **các phiên điều trần** Quốc hội/uỷ ban (hearing, testimony, mark-up, chất vấn quan chức); (b) **kết quả hội đồng/uỷ ban/hai viện bỏ phiếu THÔNG QUA dự luật** (committee vote, floor vote, passage của bill/nghị quyết/NDAA/ngân sách...). **LOẠI** phần còn lại của chính trị nội bộ Mỹ: tranh cãi đảng phái/drama, chân dung/động thái chính trị gia, horserace bầu cử, biểu tình, chính sách nhập cư, cải cách tư pháp thuần, bê bối cá nhân... (Lưu ý: tin CHÍNH SÁCH/HÀNH PHÁP gắn quốc phòng–an ninh–kinh tế–ngoại giao vẫn nhận BÌNH THƯỜNG qua các category tương ứng; ràng buộc này chỉ áp cho mục CHÍNH TRỊ NỘI BỘ. Tin thế giới ngoài Mỹ vẫn theo bộ lọc gốc.)

**📌 HAI CHỦ ĐỀ CHÚ TRỌNG QUÉT HÀNG NGÀY — thêm 23/07/2026 (chỉ thị người dùng):**
- **Tập trận Pitch Black 2026** *(thay Predator's Run từ 02/08/2026 — kỳ đó đã kết thúc)* — thẻ `exercises` đã có: `"Pitch Black 2026 (Úc chủ trì, 20 nước tham gia)"` (20/7–7/8, Darwin/Tindal/Amberley, ~100 máy bay, hơn 2.500 quân nhân). **Mỗi phiên CHỦ ĐỘNG tìm diễn biến mới** (khoa mục bay, tiếp dầu trên không, lần đầu của từng nước, tuyên bố chỉ huy) → cập nhật qua `exerciseUpdates` (khớp đúng tên). Nguồn: defence.gov.au, airforce.gov.au, janes.com, dvidshub.net, pacom.mil. **Khi tập trận KẾT THÚC (7/8)** → dùng `exerciseUpdates` kèm nêu trong tóm tắt để đổi `status` sang `recent`, VÀ đổi chủ đề 05 sang kỳ tập trận kế tiếp theo đúng 05 chỗ liệt kê ở mục "5 chủ đề" đầu file — bỏ bước sau là chủ đề 05 lại báo 0 tin mỗi phiên trong im lặng.
- **Mỹ – Mali** — hồ sơ sống mới (dossier `🟤 Mỹ – Mali` trong mục Hồ sơ). **Mỗi phiên theo dõi diễn biến** việc Mỹ cân nhắc/triển khai phương án quân sự ở Mali nhắm JNIM (al-Qaeda): quyết định không kích drone, phản ứng của Mali/Nga (Africa Corps)/JNIM, diễn biến Sahel–Bamako. Tin gắn Mali/JNIM/Bamako/Sahel để tự vào dossier. Ưu tiên nguồn: defense.gov, state.gov, centcom.mil (AFRICOM), Reuters/AP/AFP, WaPo. Đa số là tin **usNews** (chính sách/hành động của Mỹ).

**Nguyên tắc "cứu":** tin công ty/chính trị VẪN nhận nếu gắn chủ đề chiến lược (vd Boeing↔máy bay quân sự, Samsung↔chip AI).
**Khu vực (hoà giải hiến chương):** chọn theo chủ đề/kiểu tin là chính, NHƯNG khi 2 tin ngang chất → ưu tiên tin dính **nước lớn**, hạ (không loại) vùng xa. **VN chỉ khi gắn quốc tế; TQ để tự nhiên** (không đậm/né thêm).
**Trong CNQS:** ưu tiên không quân/tên lửa · hạt nhân–răn đe · không gian/mạng; **hải quân là mảng phụ** (vẫn nhận, nhưng cắt sau cùng).
**Nga–Ukraine:** giữ như hồ sơ sống — chỉ nhận **diễn biến MỚI** (bước ngoặt/ngoại giao/vũ khí mới), loại tin chiến sự lặp.

Nếu một phần thực sự không đủ chỉ tiêu sau khi đã thử nhiều nguồn — chấp nhận thiếu, KHÔNG bịa tin/link, KHÔNG nới bộ lọc để nhồi tin không đúng gu, nêu rõ trong tóm tắt cuối.

## Kiến trúc quét: nhiều agent Sonnet nhỏ (bắt buộc — để nhẹ và chống sập)
> ⚠️ 2026-07-23: bảng 8 agent (Kinh tế/Chính trị/CNQS/Ngoại giao/xNews/exercises/2 Báo Mới) LỖI THỜI. Giờ chỉ 5 luồng cho 5 chủ đề — xem `.claude/skills/quet-tin/SKILL.md` Bước 2. Cơ chế agent Sonnet + chống trùng + review bên dưới vẫn đúng.
Không dùng 1 agent lớn ôm hết việc quét (dễ quá tải/timeout/tốn token). Session điều phối (session hiện tại) tự thực hiện các bước đọc `DATA`/kiểm tra nguồn đã dùng, sau đó **dùng tool Agent để giao việc quét cho các subagent chạy model Sonnet (`model: "sonnet"`)**, mỗi agent chỉ phụ trách MỘT phần vừa phải:

> Ghi chú model (10/07/2026): trước dùng Haiku cho rẻ nhưng lần quét đầu tiên tỷ lệ lỗi cao (~40-50% tin bị loại: sai ngày, link rác/không khớp, trùng tin cũ, mâu thuẫn dữ liệu, bịa ID). Đã đổi sang **Sonnet** để tin thu thập chính xác hơn từ đầu (tốn token hơn Haiku nhưng giảm mạnh vòng quét lại + công review). Guardrail tự động trong `add_news.py` (xem mục Guardrail) vẫn là lớp chặn cuối cùng bất kể model nào.

| Agent | Phạm vi | Sản lượng mỗi agent |
|---|---|---|
| 1 | Category "Kinh tế" — cả worldNews + usNews | ~4–6 tin |
| 2 | Category "Chính trị" — cả worldNews + usNews | ~4–6 tin |
| 3 | Category "Công nghệ quân sự" — cả worldNews + usNews | ~4–6 tin |
| 4 | Category "Ngoại giao" — cả worldNews + usNews | ~4–6 tin |
| 5 | xNews | 4–5 tin |
| 6 | exercises + dipEvents (cập nhật ongoing + **TẠO thêm sự kiện ngoại giao mới, đặt đúng status upcoming/ongoing/recent**) | tập trận 1–2; **ngoại giao 2–4 cập nhật + 1–2 sự kiện mới** |

Quy tắc khi giao việc cho từng agent (viết prompt độc lập, đầy đủ ngữ cảnh vì subagent KHÔNG thấy hội thoại chính):
- **KHÔNG bảo subagent tự đọc `CLAUDE.md`** — file này ngày càng dài, để 6 agent cùng đọc là lãng phí token 6 lần. Agent điều phối tự trích đúng phần cần (nguồn phù hợp + URL RSS nếu có + định dạng field) rồi nhúng thẳng nội dung đó vào prompt của từng agent.
- Nêu rõ: phạm vi (category/phần), chỉ tiêu số lượng, danh sách nguồn phù hợp kèm URL RSS đã biết (xem bảng RSS bên dưới — đưa thẳng URL, không bắt agent tự dò), định dạng field bắt buộc đúng như trên.
- **Ràng buộc chất lượng — nhúng vào MỌI prompt agent** (rút ra từ lỗi lần quét đầu 10/07): (a) `date` CHỈ trong **2 ngày gần nhất — hôm nay + hôm qua** (theo giờ VN), TUYỆT ĐỐI KHÔNG lấy tin cũ hơn hôm qua; (b) `sourceUrl` phải trỏ THẲNG tới 1 bài viết cụ thể, KHÔNG dùng link trang chủ / "live updates" / live-blog / trang tổng hợp, và link phải KHỚP đúng nội dung tin; (c) `sourceName` chỉ trong danh sách nguồn được giao (báo chí) HOẶC nguồn chính phủ/chính thức phù hợp; (d) với xNews: KHÔNG bịa status ID (ID thật ~19 chữ số ngẫu nhiên, không tròn số); (e) thà ÍT tin đạt chuẩn còn hơn nhồi tin sai — được phép trả mảng rỗng.
- **Ưu tiên nguồn chính phủ/chính thức**: khi tin bắt nguồn từ thông báo/phát ngôn chính thức (defense.gov, nato.int, state.gov, whitehouse.gov, centcom.mil, baochinhphu.vn, mofa.gov.vn...), ưu tiên link thẳng nguồn gốc đó thay vì báo dẫn lại. Với truyền thông nhà nước độc tài (Xinhua/TASS/Global Times/Press TV/KCNA): chỉ dùng cho phát ngôn của chính họ, không làm nguồn trung lập cho sự kiện tranh cãi/thương vong.
- **Đa dạng hoá sự kiện**: mỗi tin trong batch nên là một sự kiện/câu chuyện KHÁC NHAU. Tránh việc 2-3 "tin" trong cùng category thực chất chỉ là cùng 1 sự kiện do nhiều báo đưa lại — vậy chỉ tính 1, chọn nguồn tường thuật tốt nhất.
- **Chống trùng với tin cũ (BẮT BUỘC nhúng ĐẦY ĐỦ, không cắt rời từng mục)**: agent điều phối chạy `python3 scripts/add_news.py --recent-titles 20` (rẻ, không đọc cả file — output gồm tiêu đề gần đây của worldNews + usNews + xNews + item các sự kiện) rồi dán **NGUYÊN khối output đó vào prompt của TẤT CẢ 6 subagent** (kể cả agent xNews và agent exercise), kèm dặn "không report lại bất kỳ tin/sự kiện nào đã có trong danh sách này, kể cả dưới tiêu đề/góc nhìn khác, trừ khi có diễn biến MỚI HẲN". Lý do phải nhúng đủ cho mọi agent: lần quét đầu agent xNews/exercise re-report tin mà agent worldNews đã lấy vì chỉ được đưa danh sách rời của mục mình.
- **Cảnh báo dữ liệu thực tế mâu thuẫn**: khi có sự kiện đang tiếp diễn (vd chiến sự, ngừng bắn), agent điều phối phải tóm tắt trạng thái mới nhất đã đăng và dặn agent không đưa tin mâu thuẫn với trạng thái đó (lần đầu có agent đưa tin "ngừng bắn vẫn duy trì" trong khi dữ liệu đã ghi ngừng bắn bị chấm dứt).
- Yêu cầu agent CHỈ trả lời bằng đoạn JSON kết quả (mảng tin của phần đó) — không giải thích dài dòng, để việc gộp kết quả ở agent điều phối rẻ.
- Không bịa link — bỏ tin nếu không chắc `sourceUrl`.
- Gọi các agent này song song trong cùng 1 lượt (không cần tuần tự) để tiết kiệm thời gian, dùng `run_in_background: false` vì cần kết quả ngay để lắp ráp.

Sau khi các agent trả kết quả, session điều phối **tự review từng tin** (đối chiếu ràng buộc chất lượng trên) trước khi gộp — loại tin không đạt, giữ tin tốt. **Ghi mọi tin bị loại vào `logs/loai-tin.md`** kèm lý do (đánh dấu ⭐ + để lên đầu các tin CHỦ ĐỀ THÍCH bị loại — để người dùng rà xem có loại nhầm không), commit cùng bản tin. Rồi gộp toàn bộ JSON con thành 1 file `/tmp/new_items.json` theo đúng format ở dưới, chạy script (script sẽ chặn lần cuối các lỗi máy bắt được).

## ~~Chu kỳ bản tin: 2 lần/ngày~~ — ⚠️ LỖI THỜI 2026-07-23: giờ CHỈ 1 lần/ngày buổi TỐI 22:00 (dự phòng 23:00), xem banner đầu file
Mỗi mốc là MỘT chu kỳ khép kín, 3 nguồn nạp nối tiếp nhau rồi ra **một bản tin hợp nhất**:

| Giờ VN | Ai chạy | Việc |
|---|---|---|
| **08:00** / 20:00 | Action `import-news-from-drive.yml` | Nạp file `ban-tin-chien-luoc-*.json` từ Drive vào `DATA` |
| **08:05** / 20:05 | Action `sync-baomoi.yml` | `baomoi-saved.json` (bài đã lưu) + `baomoi-topics.json` (ứng viên quét chuyên mục) |
| **10:15** / 20:15 | Scheduled task local `web-scan` (7+1 agent Sonnet) | Quét web + nạp Báo Mới vào `DATA` → publish |
| 11:15 / 21:15 | Scheduled task local `web-scan` (dự phòng) | Chỉ chạy nếu mốc chính chết; cờ `state.json` làm nó tự no-op khi đã xong |

**VÌ SAO Drive + Báo Mới chạy TRƯỚC phiên quét** (chứ không phải quét xong mới gộp): chống trùng chỉ chạy một chiều — phiên quét đọc `--recent-titles` + URL đã có trong `index.html` nên né được tin Drive/Báo Mới vừa nạp; ngược lại thì không. Đặt 2 nguồn kia trước thì bản tin sạch trùng hơn, kết quả cuối vẫn là một bản tin gộp, deploy một lần.

Cờ idempotent theo pipeline (xem mục dưới): `drive-import` và `web-scan`.

**Cờ idempotent nằm ở `logs/state.json`, KHÔNG phải `DATA.generatedAt`.** `generatedAt` là *ngày bản tin hiển thị trên web* — dùng nó làm cờ chạy việc thì Action Drive nhập lúc 08:00 sẽ bump nó và làm routine quét tối SKIP vĩnh viễn (đã xảy ra 20–21/07: `xGeneratedAt` kẹt ở 19/07, tập trận/sự kiện ngoại giao không ai cập nhật). Mỗi pipeline giờ có dòng riêng, chỉ tự chặn CHÍNH NÓ.

```
python3 scripts/state.py claim web-scan     # giành KHOÁ + kiểm tra: 0=quét đi · 10=xong rồi · 11=đang chạy
python3 scripts/state.py beat  web-scan     # nhịp tim — gọi ở MỖI checkpoint, nếu không khoá tự hết hạn
python3 scripts/state.py done  web-scan "+12 tin (TG+5, My+5, X+2)"
python3 scripts/state.py fail  web-scan "session limit"    # FAIL/SKIP nhả khoá, KHÔNG chặn lần fire sau
python3 scripts/state.py show                              # xem cả 2 pipeline, cả 2 buổi, trạng thái khoá
```
Chỉ `done` mới đẩy `lastSuccess[buổi]` → chỉ khi thật sự nạp được tin mới chặn lần fire kế tiếp; `fail`/`skip` để lần sau quét lại.

## Nhập tin từ Google Drive (pipeline `drive-import`)

> ### ⛔ ĐÃ TẮT LỊCH 30/07/2026 (Huy chốt) — chỉ còn chạy tay
> Workflow **giữ nguyên, không xoá**; chỉ bỏ `schedule`, còn `workflow_dispatch`. Chạy lại bằng
> `gh workflow run import-news-from-drive.yml`. Hai lý do, đều đo được:
> **01. Nguồn đã khô.** `logs/state.json` → `drive-import.lastSuccess.sang = 2026-07-21`; mọi phiên từ
> 22/07 tới 29/07 ghi note *"khong tim thay file ban-tin-chien-luoc nao"*, log ngày đều đúng 261 byte
> cùng một khuôn. 09 ngày chạy không ra tin mà workflow vẫn báo `success` — chết câm, bảng CI vẫn xanh.
> **02. Nó là workflow tự động CUỐI CÙNG hợp nhất file dùng chung bằng rebase.** Bước "Commit if
> changed" `git add index.html logs/` rồi `git pull --rebase` — cùng lớp lỗi đã gây sự cố sổ đã gửi
> sáng 30/07. Phiên quét local sáng 30/07 chạy bù lúc 07:41 và 07:48, cách mốc 07:23 đúng **18 phút**.
> **Bật lại lịch thì phải vá khối commit trước** — cổng `.github/scripts/kiem_luat_push.py` chặn cứng
> (mục dưới). Và **đừng bê nguyên `ghi_so_push.py` sang**: sổ là append-only nên git hợp nhất được, còn
> `index.html` thì không — hai lô tin cùng chèn vào đầu mảng `DATA.news` là xung đột văn bản gần như
> chắc chắn. Đường đúng cho file này: push bị từ chối → `fetch` → bỏ lô của mình → **chạy lại
> `add_news.py`** với chính `/tmp/new_items.json` trên đỉnh mới (nó dedupe theo URL) → commit → push.

Action `import-news-from-drive.yml` (trước đây 08:00 & 20:00 VN) tìm **mọi** file `ban-tin-chien-luoc-YYYY-MM-DD-HHMM-ICT.json`
trong khung 2 ngày trên Drive, **gộp tất cả thành 1 batch** (dedupe theo URL — ấn bản mới thắng; item ngoài
khung 2 ngày bị đẩy sang `rejectedNews` thay vì làm hỏng cả lô), rồi chạy `add_news.py`. Cần secret
`GOOGLE_DRIVE_FOLDER_ID` + `GDRIVE_API_KEY`. Log: `logs/gdrive-<ngày>.log` + `logs/state.json`.
**KHÔNG tạo routine Claude làm việc này nữa** — trước đây có cả routine Claude lẫn Action cùng nhập, trùng việc.
> Lỗi cũ đã sửa 21/07/2026: script xử lý từng file rồi cùng ghi đè `/tmp/new_items.json`, nên khi Drive có
> 2 ấn bản thì file chạy sau (ấn bản CŨ hơn) xoá sạch kết quả của ấn bản mới → mất tin âm thầm.

## BÀI HỌC GHI SỔ SONG SONG (xẻ từ `~/.claude/CLAUDE.md` mục 17, ngày 31/07/2026)

Nội dung dưới đây nằm nguyên văn ở `~/.claude/CLAUDE.md` mục 17 cho tới 31/07/2026, xẻ về đây theo MẢNG để cắt khối lượng nạp mỗi phiên. **Giữ nguyên cả luật lẫn cơ chế gây vấp** — đừng rút gọn. File gốc còn dòng trỏ nêu tên từng bài học.

**HAI TIẾN TRÌNH GHI CÙNG MỘT FILE APPEND-ONLY → ĐỪNG `pull --rebase`** (đúc 30/07/2026, sự
cố thật ở Điểm Tin). Hai workflow ghi `logs/da-gui-email.json` cách nhau **07 giây**; khối lệnh
cũ commit local rồi `git pull --rebase` ⇒ rebase phát lại commit của mình lên trên commit kia,
hai bên sửa đúng cùng chỗ trong JSON nên **xung đột**, và rebase hỏng để repo ở trạng thái
rebase dở nên **cả 5 vòng retry chết tiếp**. **Cơ chế gây vấp:** vòng retry nhìn như đã lo
chuyện tranh chấp, nhưng nó thử lại **đúng cái phép toán vừa hỏng** trên **đúng trạng thái đã
bẩn** — retry chỉ chữa được lỗi *tạm thời* (mạng), không chữa được lỗi *xác định* (xung đột).
- **Sổ/log/hàng đợi là dữ liệu append-only**: hai lần ghi là hai DÒNG khác nhau, không phải hai
  phiên bản tranh nhau của một dòng. Nên hợp nhất đúng là **lấy bản mới nhất của remote rồi ghi
  lại dòng của mình** (`fetch` → `reset --mixed FETCH_HEAD` → `checkout FETCH_HEAD -- <file>` →
  append → commit **chỉ file đó** → `push HEAD:main`), thử lại trên đỉnh mới nếu bị chen. Không
  gọi rebase thì không có xung đột để mà hỏng.
- **`--mixed` chứ không `--hard`** — `--hard` kéo cả file khác của lô người ta về, commit của
  mình hết còn sạch.
- **Tính nội dung dòng TRƯỚC khi đụng git, đúng một lần.** Ở Điểm Tin, danh sách URL được tính
  bằng diff `index.html` với `HEAD~1`; tính lại sau khi đã `reset` là diff với **lô của phiên
  khác** ⇒ ghi thừa URL ⇒ bản tin sau BỎ tin đó. Đây là **mất dữ liệu**, không phải trùng.
- **Retry hết lượt thì trả mã ≠ 0**, đừng fail-open: file không được cập nhật là thứ khiến hệ
  thống giám sát **kêu oan chỗ khác** (canary Điểm Tin kêu "hỏng khâu GỬI" trong khi bản tin đã
  tới tay, còn hai phiên dự phòng thì quét lại tốn token).
- **Lỗi này ngủ yên rất lâu rồi thức dậy vì lịch đổi**: trước 28/07 hai workflow cách nhau ~4
  tiếng, gộp phiên xong mới còn 7 giây. **Dồn hai việc vào cùng một mốc thì phải soi lại xem
  chúng có ghi chung file nào không** — đừng chỉ nghĩ về thời lượng.
