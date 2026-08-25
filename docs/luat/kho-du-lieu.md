# Nơi lưu dữ liệu — tin, X, tập trận, sự kiện ngoại giao — Điểm Tin Thế Giới

> Xẻ từ `CLAUDE.md` ngày 25/08/2026 để bản thi hành gọn lại (luật mục 31 của `~/.claude/CLAUDE.md`).
> **Nội dung giữ NGUYÊN VĂN, không cắt chữ nào** — chỉ đổi chỗ ở. Bản thi hành: [`../../CLAUDE.md`](../../CLAUDE.md).

## Nơi lưu dữ liệu
Dữ liệu nằm trong `index.html`, biến `var DATA = {...}` (xem mục "Quy trình" bên dưới — KHÔNG đọc trực tiếp file này).

> ⚠️ **NGOẠI LỆ DUY NHẤT: bài think-tank nằm ở `data/analyses.json`** (tách 30/07/2026 — xem mục 4).
> `DATA.analyses` trong `index.html` LUÔN RỖNG; web nạp kho bằng `loadAnalyses()` sau khi trang đã hiện.
> Script Python phải đi qua `scripts/analyses_store.py`, và **mọi commit có nạp think-tank phải
> `git add data/`** — bỏ sót thì bài nạp xong không lên web mà không có lỗi nào.

Các phần liên quan tới quét tin:

### 1. `worldNews` / `usNews` — tin theo chuyên mục
Mảng phẳng, tin mới nhất ở đầu. Mỗi tin:
```json
{"date":"YYYY-MM-DD","category":"...","title":"...","summary":"...","sourceName":"...","sourceUrl":"https://...","significance":"...","region":"..."}
```
- `category` (chọn 1): Kinh tế · Chính trị · Công nghệ quân sự · Ngoại giao
- `region` (chỉ tin thế giới, không bắt buộc): Châu Âu/NATO · Trung Đông · Đông Á · Toàn cầu · Châu Mỹ · Ấn Độ Dương - Thái Bình Dương
- Ngày cập nhật: `DATA.generatedAt`, `DATA.worldGeneratedAt`, `DATA.usGeneratedAt`
- **Giờ cập nhật (thêm 24/07/2026)**: `DATA.generatedTime` / `worldGeneratedTime` / `usGeneratedTime` / `xGeneratedTime` — `HH:MM` giờ VN lúc chạy `add_news.py`, ô "Cập nhật" trên web hiện `23-07-26 20:30`. Để RIÊNG chứ không nhét vào `generatedAt` vì `generatedAt` phải giữ đúng dạng `YYYY-MM-DD` (notify-push.yml grep bằng regex ngày; send-email.js + make_docx.py `split('-')` và so với `_addedDate`).

### 2. `xNews` — tin từ X/Twitter
Mảng phẳng, tin mới nhất ở đầu. Mỗi tin:
```json
{"date":"YYYY-MM-DD","handle":"@...","name":"Tên tài khoản","title":"...","summary":"...","significance":"...","url":"https://x.com/..."}
```
Ngày cập nhật: `DATA.xGeneratedAt`. **Danh sách tra cứu chính: [`docs/mangxahoi-chinh-thuc-my.md`](docs/mangxahoi-chinh-thuc-my.md) — 173 handle X đã xác minh của cơ quan chính phủ và uỷ ban Quốc hội Mỹ (chỉ gồm tài khoản được liên kết từ website chính thức). Ngoài ra — loại tài khoản đã dùng trước đây: quan chức/tổ chức chính thức (@NATO, @CENTCOM, @ZelenskyyUa), hãng tin lớn (@Reuters, @AJEnglish, @SkyNews, @CBSNews), tổ chức phân tích/OSINT (@TheStudyofWar, @EU_ISS, @thewarzonewire), nhà báo/chuyên gia uy tín (@BarakRavid, @AndrewSErickson). Ưu tiên tài khoản xác thực (verified/tổ chức chính thức), không lấy tin từ tài khoản vô danh/không rõ nguồn gốc.

### 3. `exercises` (tập trận) / `dipEvents` (sự kiện ngoại giao)
KHÁC với category "Ngoại giao" ở trên — đây là các **sự kiện lớn đang diễn ra** (hội nghị thượng đỉnh, cuộc tập trận đa quốc gia...), mỗi sự kiện là 1 object có `name`, `status` (`ongoing`/`recent`/`upcoming`...), `dates`, `location`, `scale`, `summary`, và một mảng con `items` chứa các tin cập nhật liên quan, mỗi item:
```json
{"date":"YYYY-MM-DD","title":"...","summary":"...","sourceName":"...","sourceUrl":"https://..."}
```
Với **`exercises` (tập trận)**: cập nhật `items` con vào cuộc **đã có** (khớp `name`) qua `exerciseUpdates`; **được phép TẠO cuộc tập trận MỚI** qua `newExercises` (phiên sáng `event-scan` chủ động quét tập trận lớn KHẮP THẾ GIỚI đang/sắp diễn ra — không chỉ Ấn Độ Dương-TBD). Ưu tiên cập nhật `status: "ongoing"`. `dates` ghi dạng CÓ ngày/tháng/năm để web tự suy trạng thái (`effStatus`).

⚠️ **`dates` CHỈ CÓ MỘT MỐC LÀM WEB HIỆN "✓ Đã kết thúc" CHO CUỘC ĐANG CHẠY — đúc 07/08/2026.**
Mẫu thứ ba của `evRange` bắt một ngày lẻ `d/m/yyyy` rồi trả `a === b`, nên `effStatus` so `t > b` và ra
`recent` **ngay trong ngày khai mạc**. `tap_tran.py::trang_thai` sao y hành vi ấy, nên cuộc đó cũng
rơi khỏi `dang_dien_ra` và **không được bơm từ khoá vào lượt quét tin**. Đo thật khi nạp SEACAT 2026 và
diễn tập Hạm đội Thái Bình Dương Nga: cả hai khai `status: "ongoing"`, cả hai bị xếp `recent`.
- **Cơ chế gây vấp:** nhánh lùi về `status` **chỉ chạy khi `evRange` trả `null`**, tức khi không mẫu
  nào khớp. Một chuỗi có ĐÚNG một ngày thì mẫu vẫn khớp, nên nhánh lùi không bao giờ tới. Nói cách
  khác, chuỗi một mốc **tệ hơn** chuỗi không đọc được ngày nào — và không có dấu hiệu nào để nghi, vì
  thẻ vẫn hiện đủ tên, địa bàn, quy mô, tóm tắt, chỉ có mỗi nhãn trạng thái là sai.
- **Cách viết đúng khi CHƯA BIẾT ngày kết thúc:** ghi ngày bằng chữ, không dùng dấu gạch chéo —
  `"Khai mạc ngày 04 tháng 8 năm 2026; ngày kết thúc chưa công bố"`. Không mẫu nào khớp ⇒ `evRange`
  trả `null` ⇒ lùi về `status`, đúng đường đã thiết kế sẵn.
- ⛔ **CẤM bịa một ngày kết thúc cho đủ khuôn `d/m – d/m/yyyy`.** Nhãn trạng thái khi ấy đúng nhưng
  trang lại khai một dữ kiện không nguồn, và nó nằm ngay cạnh phần quy mô có nguồn nên đọc vào không
  phân biệt được.
- ⚠️ **`evRange` QUÉT TOÀN CHUỖI, nên MỌI ngày dạng `d/m/yyyy` ở BẤT KỲ đâu trong `dates` đều bị bắt
  — kể cả ngày nằm trong lời chú thích.** Vấp thật cùng ngày 07/08/2026, **ngay sau khi luật ở trên
  vừa được đúc**: ba thẻ ghi `"Tháng 8/2026; ngày cụ thể chưa công bố tính tới 7/8/2026"`, và cụm
  *"tính tới 7/8/2026"* khớp mẫu thứ ba ⇒ `a = b = 07/8/2026` ⇒ cả ba hiện **"● Đang diễn ra"** trong
  khi `status` khai `upcoming` và cuộc chưa khai mạc. Biết luật chưa đủ: phải soi cả phần chú thích.
  - **`"Tháng 8/2026"` thì AN TOÀN** — mẫu đòi `\d{1,2}/\d{1,2}/\d{4}`, mà `8/2026` chỉ có hai nhóm.
  - **Mốc đo trong chú thích thì ghi bằng chữ** (`tính tới ngày 07 tháng 8 năm 2026`) hoặc bỏ hẳn.
  - **Nghiệm thu bắt buộc sau mỗi lô nạp:** chạy chính `evRange` và `effStatus` bóc từ `index.html`
    bằng `node` rồi đọc nhãn từng cuộc, đừng tin `status` đã khai trong payload.
- Đã đo và KHÔNG vá `evRange`: sửa nó là đụng hai bản luật song song (JS trên web và Python trong
  `tap_tran.py`, xem ca [25] của `tests/test-mali-va-tap-tran.py`), trong khi đường viết đúng đã có sẵn
  và không tốn gì.

⛔ **SỬA `dates`/`status` CỦA CUỘC ĐÃ NẠP: DÙNG `scripts/sua_thong_tin_tap_tran.py`, CẤM SỬA TAY
`index.html`** (dựng 07/08/2026). `add_news.py::apply_event_updates` chỉ chạm `entry["items"]`, nên
trước đó **không đường nào** sửa `dates` · `status` · `location` · `scale` · `summary` của một cuộc
đã có — mà tập trận lớn hay công bố ngày sát khai mạc, tức đây là việc thường xuyên nhất.
```bash
python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/sua_thong_tin_tap_tran.py --kiem
```
| Việc | Lệnh |
|---|---|
| Sửa | `sua_thong_tin_tap_tran.py sua.json` — `[{"name":"<khớp ĐÚNG>","dates":"…","status":"…"}]` |
| Nghiệm thu | `--kiem` in nhãn MỌI cuộc suy từ `dates`, mã 3 khi có thẻ `status` khai lệch |
| Chứng minh còn răng | `--tu-kiem` — **21 ca (14 PHẢI CHẶN) · 06 bản hỏng**, đã nạp `khoe.py` |

- **Hai bẫy ở trên nay là CỔNG MÁY, không còn phải nhớ**: `dates` một mốc lẻ bị chặn (cờ mở
  `--cho-phep-mot-moc` cho cuộc thật sự gói trong một ngày), và nhãn suy từ `dates` phải KHỚP
  `status` khai — đây là thứ bắt được ngày lẫn trong lời chú thích.
- ⚠️ **Sửa `dates` thì BẮT BUỘC khai `status` cùng lượt.** Ý định khai bằng lời, cùng bài học với
  `tu_dong=1` · `TELEGRAM_BAT_BUOC` · `DIEMTIN_PHIEN_TEST`: tự suy `status` từ `dates` rồi ghi đè cho
  êm là làm phép kiểm chéo hoá cổng chết — hai đại lượng cùng suy từ một nguồn thì không bao giờ lệch.
- ⚠️ **Cố ý KHÔNG cho sửa `name`** (khoá tra của `exerciseUpdates`, đổi là mọi lô nạp sau trượt),
  `items` (dùng `add_news.py`), `background`/`concepts` (dùng `set_exercise_briefing.py`). Khai nhầm
  vào đây thì bị chặn kèm chỉ đường, không im lặng bỏ qua.
- **Nghiệm thu 07/08 khi cắm**: bảng tố đúng 03 thẻ `status` lệch mà CLAUDE.md đã ghi từ 05/08 nhưng
  chưa ai sửa được vì thiếu đường (`Hán Quang 42` khai `upcoming` khi đang chạy · `Predator's Run` và
  `RIMPAC` khai `ongoing` khi đã tàn). Sửa xong, chạy lại chính `evRange`/`effStatus` bóc từ
  `index.html` bằng `node`: **0/24 cuộc lệch**.

🔎 **DÒ CUỘC TẬP TRẬN CÒN THIẾU — `scripts/do_tap_tran_thieu.py`, cắm vào phiên quét SÁNG bước 4.2a**
(dựng 07/08/2026). **Vòng luẩn quẩn nó cắt:** `tap_tran.py` sinh từ khoá từ chính `DATA.exercises`, tức
chỉ đi tìm tin cho cuộc **ĐÃ CÓ TÊN**; cuộc chưa có thì không ai tìm, không ai tìm thì không bao giờ vào
danh sách. Đo 07/08: DATA có 10 cuộc, một lượt đọc tay ra **14 cuộc thiếu, 04 đang chạy đúng hôm đó**.
Script hỏi ngược theo **KHUÔN** (`<nước A> <nước B> exercise <tháng năm>`) nên không cần biết trước tên.

| Nhóm đầu ra | Nghĩa | Xử lý |
|---|---|---|
| **★ CÓ TÊN RIÊNG** | tên cuộc không khớp cuộc nào trong DATA | nạp thẻ mới `add_news.py --newExercises` |
| **○ KHÔNG TÊN CHUỖI** | hoạt động chung ngắn ngày | đọc tay rồi quyết — **đây là nhóm bảng chuỗi vốn mù** |

- **Nghiệm thu 07/08**: 28 truy vấn → 67 ứng viên, nhóm ★ tìm đúng **02 cuộc thật còn thiếu**
  (`Exercise Carabaroo` Philippines–Úc tam phương · `Exercise MILAN-2026` Ấn Độ, kỳ 13 tại
  Visakhapatnam). **29 ca (18 PHẢI CHẶN) · 11 bản hỏng**, đã nạp `khoe.py`.
- ⚠️ **Là công cụ GỢI Ý, luôn trả mã 0** — cắm làm cổng chặn thì một hôm Google News đổi khuôn là chết
  cả bản tin vì một mục phụ. Sát giờ thì bỏ bước, ghi một dòng log rồi đi tiếp.
- ⚠️ **04 lớp hỏng đều CÂM, bảng vẫn đầy dòng** — đo thật lúc dựng: neo quá chặt rớt 5/6 tiêu đề mẫu ·
  neo quá nới kéo tin điều tra dân số và tin sức khoẻ vào · đếm nước theo **chuỗi con** làm
  `red**uc**es` thành 02 nước (cùng họ lỗi `úc → uc trúng 397/442 bài`) · bỏ khử trùng thì 40 tin thật
  in ra **135 dòng**, mà bảng lặp là bảng không ai đọc hết.
- ⚠️ **Đừng bỏ nhóm ○ cho bảng gọn** — nó dài hơn và khó xử hơn nhóm ★, nhưng chính nó là sản phẩm:
  hoạt động hợp tác hàng hải ba bên không mang tên chuỗi nên không có hàng nào trong bảng để đặt vào.
- ⚠️ **Giới hạn đã biết:** tin về cuộc ĐÃ CÓ mà tiêu đề không nêu tên cuộc sẽ rơi vào nhóm ○ (ví dụ
  *"S. Korean Air Force joins multinational exercise in Australia"* chính là Pitch Black). Không phải
  lỗi — đọc thấy thì bỏ qua.
- ⛔ **HAI BẪY KHI NẠP TỪ BẢNG NÀY, cả hai bắt được ngay lượt chạy đầu 07/08 — script in cảnh báo
  nhưng vẫn phải tự kiểm:**
  - **Tin CŨ đăng lại mang ngày mới.** `when:7d` lọc theo ngày Google gán, không theo ngày sự kiện:
    `Exercise MILAN-2026` vào bảng với ngày 07/08 trong khi cuộc đã chạy xong **15–25/02/2026**. Luôn
    mở bài đọc ngày DIỄN RA trước khi nạp; cùng họ với BẪY NĂM đã ghi ở phần bàn giao tập trận.
  - **Cuộc con của cuộc đã có.** `Exercise Carabaroo 2026` (Lục quân Philippines, Townsville, từ
    21/7) là **thành phần nằm TRONG `Predator's Run 2026`** — thẻ đó đã có trong DATA. Xếp làm
    `exerciseUpdates` của thẻ cũ; dựng thẻ mới là tách đôi cùng một cuộc.

**🎯 Ô ĐIỂM NHẤN TRANG CHỦ CHỌN CUỘC TẬP TRẬN ĐỘNG (chỉ thị Huy 07/08/2026 — trước đó neo cứng
`Predator's Run`).** `renderHome()` từng lọc `/predator/i` để lấy cuộc lên hero, nên kỳ đó kết thúc
**29/07** mà ô vẫn treo nhãn *"Đang diễn ra"* hơn một tuần, còn Pitch Black (20/7–7/8) và Hán Quang 42
(5–14/8) đang chạy thật thì **không bao giờ lên trang chủ**. **Cơ chế gây vấp:** hỏng câm hoàn toàn —
khối vẫn hiện đủ tít, tóm tắt, dòng *"Mới nhất:"* và nút *"Xem tập trận →"*, chỉ là nói sai; nhìn
trang chủ không có dấu hiệu nào để nghi. Cùng lớp lỗi với việc chủ đề 05 từng neo tên một kỳ ở 05 chỗ
(mục "5 chủ đề" đầu file) — đổi kỳ là câm, chỉ khác chỗ câm.
- Cuộc chính = cuộc `effStatus(e)==='ongoing'` có **tin mới nhất**, hoà thì lấy cuộc khai mạc muộn hơn.
- ⛔ **Chọn bằng `effStatus` (suy từ `dates`), TUYỆT ĐỐI không đọc trường `status` tĩnh** — `status`
  gán lúc quét và không ai sửa khi ngày trôi (đo 05/08: `Predator's Run` và `RIMPAC` đều đã tàn mà vẫn
  mang `"ongoing"`, còn `Hán Quang 42` khai `"upcoming"` trong khi dải ngày đã chứa hôm nay). Đây là
  cùng một cảnh báo đã ghi ở chủ đề 05.
- **Nhiều cuộc cùng chạy thì các cuộc còn lại hiện thành nút** dưới hero (`Cũng đang diễn ra: …`) —
  bỏ đi là chúng biến mất im lặng, đúng bệnh vừa vá.
- **Không cuộc nào đang chạy thì lấy cuộc SẮP diễn ra gần nhất VÀ ĐỔI NHÃN** thành *"Sắp diễn ra"* —
  giữa hai kỳ luôn có quãng trống; giữ nguyên nhãn cũ là dựng lại đúng lời nói dối vừa gỡ.
- `DATA.exercises` rỗng → **bỏ hẳn khối hero**, cột Hồ sơ Mỹ–Mali vẫn nguyên (hành vi cũ, đã giữ).
- Nghiệm thu 07/08 trên trình duyệt thật (Chromium headless, không lỗi JS): hero ra Hán Quang 42 +
  chip Pitch Black · bấm chip → đúng `topic|drills|Pitch Black…` · ép hết cuộc về quá khứ → nhãn đổi
  *"Sắp diễn ra"* · `exercises=[]` → 0 khối `.bs-main`, trang vẫn sống.
- ⚠️ **Sửa `index.html` thì bump `C` trong `sw.js`** (nay `diemtin-v50`) — không bump thì máy đã cài
  PWA vẫn ăn bản cache cũ, tức bản vá không tới người đọc mà cũng không báo lỗi gì.

**BỐI CẢNH + KHÁI NIỆM (thông tin nền — cập nhật 25/07/2026):** mỗi cuộc tập trận có thể mang `background` (đoạn Bối cảnh chiến lược, nhiều đoạn ngăn bằng `\n`) + `concepts` ([{term,def}]) — web hiện 2 thẻ **📔 Bối cảnh** + **📚 Khái niệm** dưới mỗi cuộc (hàm `drillBriefing`). Chỉ thị Huy: **TỰ ĐỘNG sinh Bối cảnh khi phát hiện tập trận MỚI, và thêm Bối cảnh cho mọi cuộc ĐANG diễn ra chưa có.** Sinh qua agent rồi ghi bằng `scripts/set_exercise_briefing.py briefing.json` (`[{name,background,concepts}]`). Quy trình routine: xem `docs/routine-event-scan.md` Bước 2b.

Với **`dipEvents` (sự kiện ngoại giao)** — áp dụng từ 11/07/2026 — được phép **tự động TẠO sự kiện mới** cho các sự kiện ngoại giao đáng đưa (dùng field `newDipEvents`), gồm: **ký kết/hiệp định song phương hoặc đa phương** (vd Nhật–New Zealand ký ACSA), **thượng đỉnh / hội nghị cấp cao**, **thăm cấp nguyên thủ/bộ trưởng có kết quả cụ thể**, **sáng kiến/khuôn khổ ngoại giao lớn mới**. KHÔNG tạo sự kiện cho: điện đàm/cuộc gọi thường lệ, phát ngôn đơn lẻ, tin đồn. **TĂNG số sự kiện ngoại giao mỗi ngày** (chủ động tạo 1–2 sự kiện mới + cập nhật item cho sự kiện đang chạy). Mỗi sự kiện mới phải có đủ `name`, `status`, `dates`, `location`, `scale`, `summary`, và ≥1 `items`. **`status` PHÂN LOẠI đúng 3 mức** (giao diện hiển thị theo nhóm này): `upcoming` = **Sắp diễn ra** (thượng đỉnh/hội nghị chưa họp) · `ongoing` = **Đang diễn ra** (đang họp/đàm phán nhiều ngày) · `recent` = **Đã kết thúc** (đã ký/đã họp xong). Khi một sự kiện `ongoing`/`upcoming` kết thúc, dùng `dipEventUpdates` KÈM đổi trạng thái (nêu trong tóm tắt để cập nhật status sang `recent`) (nguồn chứng minh — ưu tiên nguồn chính thức tầng 1). **LƯU Ý (24/07/2026): giao diện giờ tự SUY trạng thái hiển thị từ dải ngày `dates` so với hôm nay** (hàm `effStatus` trong `index.html`: parse "19-24/07/2026", "20/7 – 7/8/2026", "24/7/2026"… → trong khoảng = Đang diễn ra, trước = Sắp, sau = Đã kết thúc). Vì vậy KHÔNG cần sửa tay `status` mỗi ngày cho các mốc có `dates` rõ; `status` lưu trong DATA chỉ còn là **fallback** khi `dates` không parse được ngày (vd "Tháng 9/2026", "Cuối năm 2026"). Vẫn nên đặt `status` hợp lý lúc tạo, và ưu tiên ghi `dates` dạng có ngày/tháng/năm để auto hoạt động. Script tự CHẶN nếu tên trùng/giống sự kiện đã có (Jaccard ≥ 0.6) → khi đó dùng `dipEventUpdates` để thêm item vào sự kiện cũ thay vì tạo trùng. Nếu một tin đã đưa ở `worldNews`/`usNews` được nâng thành sự kiện, bỏ bản ở mảng tin phẳng để URL không trùng 2 chỗ.
