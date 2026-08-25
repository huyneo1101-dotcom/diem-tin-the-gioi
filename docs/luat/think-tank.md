# Think-tank — kho `analyses`, nguồn viện, cân đối khu vực — Điểm Tin Thế Giới

> Xẻ từ `CLAUDE.md` ngày 25/08/2026 để bản thi hành gọn lại (luật mục 31 của `~/.claude/CLAUDE.md`).
> **Nội dung giữ NGUYÊN VĂN, không cắt chữ nào** — chỉ đổi chỗ ở. Bản thi hành: [`../../CLAUDE.md`](../../CLAUDE.md).

### 4. `analyses` — bài phân tích THINK-TANK (mục 🧠 Phân tích → 🏛️ Think-tank)

#### 📦 TÁCH RA FILE RIÊNG `data/analyses.json` (30/07/2026, chỉ thị Huy)
`index.html` chạm **1,54 MB**, riêng 442 bài think-tank chiếm **520 KB thô / 147 KB sau nén = 34%**
dung lượng lần tải đầu — cho một mục nằm ở TAB CON mà người đọc bản tin ít khi mở. Tách xong
`index.html` còn **881 KB** (giảm 33%), web nạp kho sau khi trang đã hiện.
⚠️ **Đo trước khi kỳ vọng:** GitHub Pages vốn trả bản đã nén và tải hết trong **0,70 giây** — tách
chỉ tiết kiệm ~0,2 giây trên đường truyền tốt. Chỗ đáng giá thật là 3G/4G yếu và máy vào lần đầu.

| Mắt xích | Ở đâu |
|---|---|
| Nguồn sự thật | `data/analyses.json` — mảng bài, KHÔNG bọc object |
| Lớp đọc/ghi cho Python | `scripts/analyses_store.py` (`doc` · `ghi` · `kiem_index_rong`) |
| Web nạp | `loadAnalyses()` trong index.html, gọi ngay sau `render()` ở luồng boot |
| Offline | `data/analyses.json` nằm trong `SHELL` của `sw.js` (bump `diemtin-v49`) |
| Bộ test canh | `tests/test-tach-analyses.py` (9 ca + `--tu-kiem` 6 bản hỏng), đã nạp vào `khoe.py` |
| Script tách/kiểm | `scripts/tach_analyses.py` (idempotent, `--kiem` chỉ soi) |

⛔ **`DATA.analyses` trong index.html PHẢI LUÔN RỖNG.** Nó chỉ còn để `DATA.analyses||[]` không vỡ
trong lúc chờ fetch. Script nào đọc `data["analyses"]` từ index.html sẽ thấy **mảng rỗng** và:
(a) guardrail *"url ĐÃ CÓ trong DATA"* của `add_analyses.py` tê liệt → nạp trùng cả kho;
(b) ghi vào đó là ghi vào chỗ không ai đọc → mất bài. **Cả hai đều không phát ra lỗi nào.**
Vì vậy `analyses_store.doc()` **CHẶN CỨNG** khi file thiếu/hỏng thay vì trả rỗng cho êm.

⚠️ **Ba chỗ đã vá kèm, đừng gỡ:**
- `loadAnalyses()` nạp xong phải chạy lại **`importAnalysisConcepts()` · `commitSeen()` · `render()`**,
  và **`if(_firstRun)initSeen()`** — luồng boot chụp sổ đã-thấy TRƯỚC khi kho về, thiếu dòng này thì
  người mở web lần đầu thấy **442 nhãn MỚI**. Đã đo thật: bản đúng 0 nhãn, bản gỡ dòng vá đúng 442.
- `send-morning-email.js` đọc kho hiện tại từ `data/analyses.json` và bản trước từ `PREV_ANALYSES`
  (workflow `notify-morning.yml` ghi bằng `git show HEAD~1:data/analyses.json`). Cờ **`analysesKnown`
  khai bằng lời** — KHÔNG suy "prev.analyses rỗng nghĩa là trước đây chưa có bài": quên truyền biến
  thì email liệt kê nguyên kho như vừa nạp sáng nay. Cùng lớp lỗi với `TELEGRAM_BAT_BUOC`/`tu_dong=1`.
- `tra_cuu_tin.py` (bot Telegram) gắn kho vào `data["analyses"]` ngay trong `load_data()`, để phần
  còn lại của script không phải biết chuyện tách.

⚠️ **Bộ từ khoá khớp bài think-tank với tập trận (`drillTkConf`) có 2 lỗi đã đo, chưa sửa** (30/07):
(i) trần cứng `.slice(0,6)` mới là thứ giới hạn hiển thị — Pitch Black có **28 bài** qua cổng, Yudh
Abhyas 229, RIMPAC 149, đều bị cắt còn 6; (ii) từ khoá ngắn khớp CHUỖI CON sau khi `norm()` bỏ dấu —
`úc`→`uc` trúng **397/442 bài** (lực, mục, sức, thực, vực, chức), `nga` trúng 277 (ngày, ngăn, ngành).
Cổng `strong` không lọt bài sai, nhưng điểm nhiễu làm **xếp hạng 6 bài lọt vào bị sai**. Riêng Pitch
Black còn hẹp: `f-35` và `pitch black` trúng **0 bài** (kho viết về chính sách/liên minh, gần như
không gọi tên khí tài), chỉ `aukus` (16) + `không quân` (10) đang gánh. Sửa khi bắt tay viết bài.
Thêm đường nạp 27/07/2026 (chỉ thị Huy: *"quét tin buổi sáng nhớ quét thêm cả các bài từ think-tank"*).
**Vì sao mục này từng chết:** web đã có sẵn tab và mảng `DATA.analyses` từ lâu, nhưng KHÔNG script nào
ghi vào đó — chỉ `prune_news.py` xoá. Kết quả: bài mới nhất đứng ở 09/07 suốt 18 ngày. Đây là bài học
chung: **ra một mục trên web thì phải có đường nạp tự động, không thì nó chết chắc.**

Mỗi bài: `{date, outlet, author, title, summary, takeaway, topic, region, url}` (+ `_addedDate` do
script đóng dấu). `takeaway` = 1–2 câu ĐIỀU RÚT RA — đây là thứ web và email hiển thị nổi nhất, không
được bỏ trống.

**➕ `concepts` — khái niệm rút từ bài, chảy thẳng vào tab 📚 Khái niệm (thêm 29/07/2026, chỉ thị Huy).**
Mỗi bài có thể mang `concepts: [{term, def}]`; `importAnalysisConcepts()` trong index.html nạp chúng vào
sổ tay khái niệm, dùng CHUNG kho `dt.concepts` với khái niệm của tập trận nên không nhân đôi. Nguồn hiển
thị dưới mỗi thẻ là `outlet — tiêu đề bài`, khác với tập trận (ghi tên cuộc), để lần ngược được.
| Việc | Lệnh |
|---|---|
| Nạp khái niệm | `python3 scripts/set_analysis_concepts.py kn.json` — `[{url, concepts:[{term,def}]}]` |
| Soi bài nào chưa có | `python3 scripts/set_analysis_concepts.py --kiem` |
| Chứng minh guardrail còn sống | `python3 scripts/set_analysis_concepts.py --tu-kiem` (9 ca: 7 PHẢI CHẶN + 2 phải cho qua) |

Guardrail CHẶN: `url` không có trong DATA · thiếu `term`/`def` · `def` dưới 40 ký tự (giải thích cụt thì
thà không có) · `term` quá 90 ký tự (web cắt ở đó) · hai `term` trùng nhau trong CÙNG một bài · quá 6
khái niệm một bài. **KHÔNG chặn** khái niệm trùng giữa các bài hoặc trùng với tập trận — web tự khử
trùng theo tên đã bỏ dấu, chặn ở đây là chặn oan.
⚠️ **Bài không có thuật ngữ nào đáng lưu thì BỎ QUA bài đó**, đừng nhồi cho đủ số: sổ tay khái niệm là
công cụ LỌC, nhồi vào là hỏng đúng công dụng của nó. Quy trình phiên sáng: `docs/routine-web-scan.md`
Bước 4.4 mục 4.

### 🌏 BỐN KHU VỰC GẦN NHƯ TRẮNG BÀI — hai nguyên nhân chồng nhau (vá 06/08/2026)

> Huy hỏi: *"tại sao trong mục think-tank trên web tin tức, phần nam á, châu phi trung á và
> bắc cực ít bài thế"*.

**Số đo lúc bắt đầu**, trên kho 616 bài: Châu Âu/NATO **188** · Đông Á **174** · Ấn Độ Dương-TBD
**134** · Trung Đông 51 · Toàn cầu 48 · Châu Mỹ 8 · **Châu Phi 07 · Bắc Cực 04 · Nam Á 01 ·
Trung Á 01**. Bảy viện đầu bảng chiếm 462/616 bài (75%), thảy đều Anh · Mỹ · Úc.

**NGUYÊN NHÂN 01 — bảng nguồn không có viện chuyên của bốn vùng đó.** `THINKTANK_FEEDS` khai
32 feed, trong đó châu Phi có đúng SAIIA, Trung Á có đúng CACI Analyst, **Nam Á và Bắc Cực
không có nguồn nào**; bộ quét lô `QuetThinkTank/quet_thinktank.py` khai 33 nguồn thì cả 33 đều
là viện Mỹ · Anh · Âu · Úc · Nhật. Mà **87% kho được nạp bằng hai đợt quét lô** (415 bài ngày
30/07 + 119 bài 06/08), nên bốn vùng kia chỉ có bài khi một viện Anh-Mỹ-Úc tình cờ viết tới.

**NGUYÊN NHÂN 02 — nhãn khu vực bị hút về nhãn LỚN, và cái này che mất cái trên.** Kho **CÓ**
27 bài thật về Ấn Độ/Pakistan, nhưng 16 bài mang nhãn `Ấn Độ Dương - Thái Bình Dương` và chỉ
**01** mang nhãn `Nam Á`; 16 bài bàn Bắc Cực thì 5 nằm dưới `Châu Âu/NATO`, chỉ 4 mang nhãn
`Bắc Cực`. Nội dung có sẵn, chỉ là không hiện ở mục người đọc đang mở — nên nhìn vào web thì
tưởng thiếu nguồn, mà thêm nguồn xong vẫn thiếu nếu không sửa nhãn.

**Đã làm:** thêm 03 feed (`South Asian Voices` · `FIIA` · `ICDS`) vào `THINKTANK_FEEDS` và 06
nguồn vào bảng quét lô; quét bù 1.452 bài, lọc 78 bài điểm ≥3 từ 01/06/2026, tóm tắt tiếng Việt
**và gán nhãn khu vực ngay lúc viết**. Sau khi nạp: **Nam Á 01 → 16 · Trung Á 01 → 08 · Châu Phi
07 → 09**, tổng kho 656 → 733 bài.

⚠️ **BẮC CỰC KHÔNG VÁ ĐƯỢC BẰNG NGUỒN CHUYÊN — khai rõ để phiên sau đừng đi tìm lại.** Viện
chuyên duy nhất là `thearcticinstitute.org`: 403 với curl, và thang đầy đủ `congcu/lay_trang.py`
trượt HẾT mọi bậc, chỉ còn `trinh_duyet` — mà trình duyệt chỉ có ở phiên local nên cắm vào là
lớp quét ra kết quả khác nhau giữa local và CI. `highnorthnews.com` · `thebarentsobserver.com` ·
`arctictoday.com` thì sitemap sống và có bài 2026, nhưng là **BÁO tin tức**, không phải viện —
để vào mục tên là Think-tank là hỏng chính danh nghĩa của mục. FIIA và ICDS là hai viện Bắc Âu
có mảng Bắc Cực, dùng để bù, không thay được viện chuyên.

⚠️ **GÁN NHÃN LÀ VIỆC PHẢI DẶN RÕ TỪNG VÙNG, không dặn chung "gán region cho đúng".** Prompt của
đợt này liệt kê thẳng: bài về Ấn Độ · Pakistan · Bangladesh · Sri Lanka · Nepal · Maldives ·
Afghanistan → `Nam Á`, **đừng** gán `Ấn Độ Dương - Thái Bình Dương`; Kazakhstan · Uzbekistan ·
Turkmenistan · Kyrgyzstan · Tajikistan · Caucasus → `Trung Á`; vùng cực bắc · tuyến biển Bắc Cực
· Svalbard · Greenland → `Bắc Cực`. Không dặn ở mức đó thì nhãn lớn hút hết, đúng như 616 bài cũ.

⚠️ **ĐO PHÂN BỐ KHU VỰC BẰNG TỪ KHOÁ THÌ PHẢI LỌC NHIỄU TRƯỚC.** Phép đo đầu đếm chuỗi `Ấn Độ`
ra **52** bài, nhưng `Ấn Độ` khớp cả trong `Ấn Độ Dương` — bỏ chuỗi đó đi thì còn **27**. Con số
52 dẫn thẳng tới kết luận sai *"19 bài Ấn Độ bị gán nhầm Đông Á"*, trong khi phần lớn là bài Đông
Á có nhắc tới Ấn Độ Dương. Cùng lớp lỗi với luật đếm transcript ở `~/.claude/CLAUDE.md` mục 6.

#### 🚨 CƠ CHẾ CANH — `scripts/do_can_doi_khu_vuc.py` (dựng 06/08/2026)

Hai nguyên nhân trên **không có phép đo tự động nào canh** — chúng chỉ lộ ra khi Huy tự mở web
rồi tự hỏi. Vá tay bốn vùng hôm nay không chặn được vùng thứ năm mai mốt: nó sẽ hỏng y hệt,
cùng một cách, và cũng im lặng y hệt. Cổng đo cả hai nhánh, đã nạp `BO_TEST` của `khoe.py`.

| Nhánh | Đo gì | Kêu thế nào |
|---|---|---|
| ① NHÃN | với mỗi vùng: (a) số bài MANG nhãn · (b) số bài **TIÊU ĐỀ** nhắc tới vùng. Tỉ lệ a/b tụt dưới `NGUONG_TY_LE` (và b ≥ `NGUONG_BAI`) | **mã 3**, kèm danh sách bài nghi gán nhãn quá rộng |
| ② NGUỒN | vùng nào không feed/trang HTML nào khai nhãn khớp | **VÀNG, KHÔNG vào mã thoát** |

**Dòng khai HIỆN HÀNH: `NGUONG_TY_LE = 0.35` · `NGUONG_BAI = 5`** — sửa đúng dòng này khi đo
lại, đừng sửa bảng số đo trong docstring script (bảng đó là nhật ký hai kho).

- ⚠️ **CHỈ SOI TIÊU ĐỀ, đã thử quét cả `summary` rồi LOẠI.** Quét phần tóm tắt thì "nói về vùng"
  biến thành "có nhắc tới vùng": Nam Á vọt 35 → 76 bài, Trung Đông 47 → 131, vì một bài
  Nga-Ukraine nhắc Iran một câu cũng bị tính. Kêu ở mức đó là kêu oan hàng loạt, mà bảng bị kêu
  oan vài lần thì hết được đọc.
- ⚠️ **Ngưỡng lấy TỪ SỐ ĐO hai kho thật, không từ mong muốn.** Kho cũ (656 bài, trước khi vá):
  Nam Á 0,07 · Trung Á 0,25 · Bắc Cực 0,80 · Châu Phi 0,88. Kho nay (733 bài): Nam Á 0,46 ·
  Trung Á 1,00 · Bắc Cực 0,80 · Châu Phi 0,90. **0,35 nằm giữa khoảng trũng 0,25 ↔ 0,46.**
  Nghiệm thu: cổng **mã 3** trên kho cũ, **mã 0** trên kho nay — bằng chứng nó bắt đúng lỗi thật
  đã xảy ra, không phải bắt một lỗi tự bịa.
- ⚠️ **Tỉ lệ vượt 1,0 là bình thường** (bài về vùng mà tiêu đề không gọi tên vùng — Châu Mỹ 3,67).
  Chỉ chiều TỤT mới là dấu hiệu nhãn bị hút đi, nên cổng cố ý canh MỘT chiều.
- ⚠️ **Nhánh ② cố ý không vào mã thoát:** Bắc Cực không vá được (viện chuyên duy nhất chặn theo
  vân tay TLS ở mọi bậc thang, chỉ còn đường trình duyệt local-only), để nó ĐỎ là đỏ vĩnh viễn
  — rồi nhánh ① kêu thật cũng không ai thấy. Vùng đã kết luận không vá được thì ghi
  `NGUON_DA_DUYET` kèm lý do đã soi.
- ⚠️ **BA CÁI BẪY CÙNG MỘT HỌ — tên vùng NHỎ nằm lọt trong tên vùng LỚN**, cả ba đều sai trong
  im lặng và đều có ca test riêng: `Ấn Độ` ⊂ `Ấn Độ Dương` · `Nam Á` ⊂ `Đông Nam Á` (bắt được
  lúc dựng, 2 bài Đông Nam Á lọt vào nhóm Nam Á) · **cùng chuỗi đó ở nhánh ②**, nơi nhãn nguồn
  `Đông Nam Á` (Fulcrum) làm Nam Á tưởng đã có nguồn ⇒ **cổng câm đúng vùng thiếu nguồn nhất**.
  Mọi biểu thức phải neo lookahead/lookbehind; cấm cụm trần (`á`, `mỹ`). Và mỗi lần siết thì
  thêm ngay ca canh **chiều nới** (ca 06 · 08: `Ấn Độ` thật và nhãn `Nam Á` thật vẫn phải nhận).
- ⚠️ **`Toàn cầu` · `Châu Âu/NATO` · `Đông Á` · `Ấn Độ Dương - TBD` nằm NGOÀI phạm vi đo**
  (`KHONG_DO`) — chúng là vùng LỚN, tức bên HÚT nhãn chứ không phải bên bị hút, và không bộ từ
  khoá nào khoanh được chúng mà không nuốt nửa kho. Đừng đọc bảng sạch thành "mọi vùng cân đối".
- Bộ ca: **12 ca (07 ca PHẢI KÊU) · `--tu-kiem` bắt 10/10 bản hỏng**, canh cả hai chiều của cả
  hai ngưỡng (nới về 0 ⇒ không bao giờ kêu · siết lên 1,0 ⇒ kêu oan mọi vùng).
- ⚠️ **Hai bài học của chính đợt dựng, đừng lặp:** (i) ca đối chứng dựng kho thử bằng
  `NGUONG_BAI - 1` thì bản hỏng nới ngưỡng về 0 kéo luôn kho thử về rỗng ⇒ **ca vẫn xanh, ngưỡng
  mất người canh** — phải GHIM CỨNG con số (mục 25 CLAUDE.md toàn cục); (ii) bản hỏng làm tiến
  trình CHẾT thì stdout không có dòng ca nào, và `--tu-kiem` hiện ra thành *"đỏ thực tế: KHÔNG
  CÓ"* — nghe y như phép đo không có răng, mất 03 lượt chẩn đoán sai hướng. Nhánh ấy nay tự khai
  kèm stderr. **Chính bản hỏng đó lộ ra một lỗ THẬT**: `nhan_keu` chia cho `n` mà chỉ được che
  GIÁN TIẾP bởi việc `NGUONG_BAI` tình cờ ≥ 1 — hạ ngưỡng là cả script sập.

⚠️ **BÀI LẤY QUA SITEMAP KHÔNG CÓ TIÊU ĐỀ — `quet_thinktank.py` suy từ slug, và nó xấu.** Đo
06/08: **48/67** bài dính, ra `America S Munitions Challenge Industrial Constraints` (mất dấu
nháy, mất hoa thường tên riêng: `NATO` → `Nato`, `Indo-Pacific` → `Indo Pacific`). Không lỗi nào
phát ra, bài vẫn nạp được — chỉ là tiêu đề, thứ ĐẦU TIÊN người đọc nhìn thấy, đọc như máy dịch.
Vá bằng `QuetThinkTank/lay_tieu_de_that.py` (mở trang lấy `og:title`/`<title>`), chạy trên lô ĐÃ
CHỌN chứ không chạy lúc quét — quét thì mỗi nguồn sitemap trả hàng nghìn `<loc>` (ORF 1.082 bài).
Lấy lại được 47/48. **Hai lỗi của chính bản vá, cả hai đều câm, đừng dựng lại:** (i) đọc thẻ meta
bằng `content=["\'](.*?)["\']` thì nháy đóng khớp cả hai loại, mà ORF khai thẻ bằng nháy ĐƠN
trong khi tiêu đề chứa `Japan's` ⇒ trả về `Buying Time, Not Immunity: Japan`, **cụt mà vẫn nghe
hợp lý**; phải dùng backreference buộc nháy đóng cùng loại nháy mở. (ii) cắt đuôi tên viện theo
hình dạng chung (`… - <chữ gì đó>`) ăn mất nửa sau của tiêu đề thật; phải cắt theo **danh sách
tên viện**.

⚠️ **NHÃN `outlet` CỦA BỘ QUÉT LÔ KHÁC BẢNG FEED — đợt nạp sinh ngay 02 nhãn đôi.**
`quet_thinktank.py` khai tên nguồn kèm chú thích khu vực cho dễ đọc bảng (`ORF (Ấn Độ)`,
`SAIIA (Nam Phi)`) trong khi kho đã có nhãn trần. Đã gộp về nhãn của `add_analyses.py` theo đúng
luật ở mục 🏷️ bên dưới, và **chốt trước** `cacianalyst.org` → `CACI Analyst` dù domain đó hiện
mới có một nhãn — lô nạp kế tiếp qua bộ quét lô sẽ tách nhãn nếu không chốt.

### 📚 MỘT VIỆN CÓ HAI FEED: BLOG và NGHIÊN CỨU — bảng chỉ khai một nửa (vá 06/08/2026)

**Cơ chế gây vấp.** `THINKTANK_FEEDS` khai mỗi viện đúng MỘT feed, và cái được khai luôn là
feed **BLOG** — nó nằm ngay trang chủ nên dễ tìm hơn. Mục **NGHIÊN CỨU** của chính viện đó,
xuất bản ở một feed khác, chưa từng được khai. Đo trên `data/analyses.json` ngày 06/08/2026:

| | Con số |
|---|---|
| Bài Lowy thuộc `/the-interpreter/` (blog) | **35/35** |
| Bài Lowy thuộc `/publications/` (nghiên cứu) | **0** |
| Bài ASPI thuộc blog `aspistrategist.org.au` | **81/81** |
| Bài ASPI thuộc `aspi.org.au` (báo cáo viện) | **0** |

Điều đáng sợ không phải con số mà là **không dấu hiệu nào phát ra**: feed blog ra bài đều mỗi
ngày, danh sách ứng viên vẫn đầy, mục Think-tank trên web vẫn có bài mới mỗi sáng — nên không
ai có lý do đi hỏi *"còn thiếu gì"*. Toàn bộ mảng báo cáo của hai viện đầu ngành về Úc và Ấn
Độ Dương - TBD nằm ngoài kho suốt từ ngày dựng, chỉ lộ ra khi có người đi tìm một nghiên cứu
cụ thể mà không thấy.

**04 feed nghiên cứu đã khai** (fetch thật 06/08/2026, hậu tố nhãn `[NC]` trong bảng):

| Viện | Feed nghiên cứu | Đo | Bài nằm ở |
|---|---|---|---|
| Lowy Institute | `https://www.lowyinstitute.org/publications/rss.xml` | 200 · 50 item | `/publications/` |
| ASPI | `https://www.aspi.org.au/feed/` | 200 · 10 item | `/report/` |
| RUSI | `https://www.rusi.org/rss/latest-publications.xml` | 200 · 20 item | `/explore-our-research/` |
| CSET | `https://cset.georgetown.edu/publications/feed/` | 200 · 10 item | `/publication/` |

⚠️ **Feed BLOG phải giữ nguyên** — đây là THÊM mục nghiên cứu, không phải thay blog bằng
nghiên cứu. Thay là mất ~35 bài Interpreter mỗi năm, tức vá một lỗ bằng cách mở một lỗ to hơn.
Ca 02 của `tests/test-nguon-nghien-cuu.py` canh đúng chiều này.
⚠️ **Feed publications của RUSI trộn CẢ podcast lẫn bản ghi sự kiện** — đo 06/08: 4/20 item là
`/podcasts/` · `/members-event-recordings/` · `/research-event-recordings/`. Đã thêm
`event-recordings` vào `NOISE_PATHS`; hai mục bản ghi sự kiện **KHÔNG khớp** `/event/` hay
`/events/` có sẵn (đường dẫn là `members-event-recordings`, không có dấu `/` trước chữ
`event`) — đó mới là chỗ hở thật. Không lọc thì mục Think-tank đầy dòng kiểu *"Episode 125 —
Japan's intelligence reforms"*, tức một tập ghi âm được trình bày như một nghiên cứu.
⛔ **ĐÃ THỬ VÀ CHẾT, ĐỪNG DÒ LẠI** (đo 06/08/2026): `aspi.org.au/rss.xml` 403 ·
`aspi.org.au/publications/feed` 403 · `rand.org/pubs.xml` 200 nhưng **0 item** ·
`rand.org/research.xml` 500 · `rusi.org/rss/latest-research.xml` 404 · `heritage.org/rss/reports`
403 · `cepa.org/comprehensive-reports/feed/` 404.

#### `--candidates-dai` — đường quét theo THÁNG, dùng khi nào

**Lớp thứ hai của cùng một lỗ, và khai đúng feed KHÔNG chữa được nó.** `MAX_AGE_DAYS = 7` đặt
theo nhịp của feed blog, còn báo cáo ra theo tháng — nên bản Lowy *"Understanding the Chinese
military threat to Australia"* đăng 13/06/2026, tức **53 ngày** trước, vẫn không bao giờ vào
danh sách ứng viên dù feed đã khai đúng. Nghiên cứu ra theo tháng, routine quét theo ngày.

```
python3 scripts/add_analyses.py --candidates-dai   # CHỈ 4 feed nghiên cứu, khung 60 ngày
```

- **Chạy TAY khi cần bổ sung kho nền, KHÔNG cắm vào phiên quét nào.** `--candidates` giữ
  nguyên **khung 7 ngày** và nguyên phép lọc — routine sáng không đổi một tham số nào.
- ⚠️ **Nhưng 04 feed `[NC]` nằm TRONG `THINKTANK_FEEDS` nên `--candidates` cũng quét chúng** —
  đó là hệ quả bắt buộc của việc khai vào bảng, không phải sơ suất. Đo 06/08: cộng thêm
  **07 bài/ngày** vào danh sách sáng (Lowy 1 · ASPI 1 · RUSI 4 · CSET 1), thảy đều là nghiên
  cứu ra trong đúng 7 ngày qua, tức thứ lẽ ra phải có ở đó từ đầu. Muốn routine sáng tuyệt đối
  không đổi thì phải loại `URL_NGHIEN_CUU` khỏi vòng lặp của `list_candidates` — **đừng làm**:
  báo cáo mới ra trong tuần là thứ đáng đọc nhất, gạt nó khỏi danh sách sáng là dựng lại đúng
  vùng câm vừa bịt, chỉ hẹp hơn.
- ⚠️ **Đừng "dọn cho gọn" bằng cách nới thẳng `MAX_AGE_DAYS`**: mỗi sáng danh sách ứng viên
  phình lên gấp mấy lần bằng bài đã đọc từ tuần trước, ngốn hết context của agent chọn bài —
  vá một lỗ bằng cách làm hỏng luồng đang chạy tốt.
- **`MAX_AGE_DAYS_DAI = 60`, không phải 30**: 30 ngày vẫn bỏ sót đúng bản báo cáo 53 ngày tuổi
  đã sinh ra việc này, tức khung đúng về nguyên tắc mà không giải quyết được ca thật.
- Nghiệm thu 06/08: ra **40 ứng viên**, gồm đúng bản báo cáo Lowy 13/06.
- ⚠️ `URL_NGHIEN_CUU` là bảng thứ hai bên cạnh `THINKTANK_FEEDS`, nên `feeds_dai()` **KÊU** khi
  một URL ở đó không còn trong bảng feed. Không có phép canh này thì đổi tên miền một feed là
  đường quét dài lặng lẽ bỏ viện ấy — đúng loại hỏng câm cả mục này sinh ra để chặn.

#### `scripts/do_nguon_mot_muc.py` — tự dò viện thứ 5

Vá tay 04 viện hôm nay không chặn được viện thứ 5 mai mốt, mà viện thứ 5 sẽ hỏng cùng một cách
và cũng im lặng y hệt. Phép đo đếm phân bố (tên miền, mục đầu đường dẫn) trên kho: tên miền
từ **5 bài** trở lên mà thảy đều rơi vào **đúng một mục** là ứng viên nghi thiếu feed — viện
xuất bản thật thì bài rải nhiều mục (Hudson 71 bài/5 mục · Atlantic Council 57 bài/5 mục).

Phân **04 nhóm**, cố ý không gộp — gộp lại là kêu oan, mà bảng bị kêu oan vài lần thì hết được đọc:

| Nhóm | Nghĩa | Kêu? |
|---|---|---|
| ★ NGHI THIẾU FEED | một mục · **CÓ** feed khai trong `THINKTANK_FEEDS` | **CÓ** (mã 3) |
| ○ CHƯA CÓ FEED | một mục · không feed nào khai ⇒ diện WebSearch, bài vào kho bằng tay nên dồn một mục là đương nhiên | không |
| ▫ BÀI Ở GỐC | `MIEN_BAI_O_GOC` — đặt bài thẳng ở gốc tên miền nên "mục đầu đường dẫn" không tồn tại | không |
| ✓ NHIỀU MỤC | bình thường | không |

Không có nhóm ○ thì Brookings · CNAS · CSIS · SPF USA bị kêu oan ngay lượt chạy đầu — cả bốn
đều một mục, nhưng vì **chưa có feed nào**, tức một trạng thái khác hẳn đã ghi ở `WEBSEARCH_ONLY`.
`MIEN_BAI_O_GOC` lấy TỪ SỐ ĐO chứ không từ phỏng đoán (aspistrategist 81/81 ở gốc · ussc 31/31
· mwi 15/15 · cimsec 5/5). **Thêm một tên miền vào đó là TẮT phép đo cho nó** — chỉ thêm khi
đã mở vài url xem tận nơi, đừng thêm cho hết kêu.
- `DA_DUYET` là chỗ ghi kết quả đã soi tận nơi, kèm lý do — **không phải chỗ giấu ứng viên khó**.
- `--tu-kiem` (7 ca · 6 bản hỏng) gồm **01 ca vàng chạy trên KHO THẬT**: ứng viên nào chưa ai
  soi thì ĐỎ. Đã nạp `BO_TEST` của `khoe.py`, nên một viện mới vượt ngưỡng là sáng hôm sau biết.
- ⚠️ **GIỚI HẠN, đừng đọc bảng sạch thành "mọi viện đã khai đủ".** Phép đo bắt **hình dạng
  Lowy** (một tên miền, bài chia theo mục), KHÔNG bắt **hình dạng ASPI** (viện xuất bản dưới
  HAI tên miền, bảng chỉ khai một) — bài ASPI nằm ở GỐC tên miền blog nên rơi vào nhóm ▫. Hai
  hình dạng cần hai phép đo; hình dạng thứ hai xem mục ngay dưới.

#### `scripts/do_nguon_hai_mien.py` — phép đo THỨ HAI: viện dưới HAI tên miền (dựng 06/08/2026)

**CƠ CHẾ GÂY VẤP — cùng một lối im lặng, khác chỗ nấp.** Phép đo thứ nhất đếm phân bố MỤC bên
trong một tên miền, nên nó chỉ nhìn thấy viện nào chia bài theo mục. ASPI thì không: nó đặt bài
thẳng ở gốc tên miền blog `aspistrategist.org.au`, còn báo cáo nằm ở một tên miền HOÀN TOÀN
KHÁC là `aspi.org.au`. Đo 06/08/2026: **81/81 bài ASPI thuộc blog, 0 bài `aspi.org.au`** — và
vì bài nằm ở gốc nên phép đo thứ nhất xếp nó vào nhóm ▫ "phép đo không áp dụng" rồi im. Tức lỗ
đứng ngay giữa bảng kết quả mà bảng vẫn sạch. Và **không dấu hiệu nào phát ra**: tên miền blog
ra bài đều mỗi ngày nên danh sách ứng viên vẫn đầy, mục Think-tank vẫn có bài mới mỗi sáng,
không ai có lý do đi hỏi *"còn thiếu gì"*. Lỗ ASPI cụ thể đã vá (feed `aspi.org.au/feed/`, khai
trong commit `34f8973`); phép đo này để **viện thứ ba mai mốt không hỏng im lặng y hệt**.

**Phép đo.** Gom tên miền trong `THINKTANK_DOMAINS` thành nhóm CÙNG MỘT VIỆN theo hai hình dạng
— (a) tên miền con của cùng một tên đăng ký (`amti.csis.org` · `csis.org`); (b) chung gốc tên
đăng ký (`aspi.org.au` / `aspistrategist.org.au`, kể cả lối `the<tên>` và `<tên>blog`) — rồi
đối chiếu với tập tên miền đã có đường quét tự động (`THINKTANK_FEEDS` **hoặc** `THINKTANK_HTML`).
Nhóm nào đường quét phủ tên miền này mà không phủ tên miền kia thì **LỆCH**.

```
python3 scripts/do_nguon_hai_mien.py             # báo cáo; mã 3 khi còn nhóm chưa soi
python3 scripts/do_nguon_hai_mien.py --tu-kiem   # 13 ca · 10 bản hỏng
python3 tests/test-nguon-hai-mien.py             # cổng nghiệm thu, 20 ca hộp đen
```

- ⚠️ **Cả nhóm đều CÓ đường, hoặc cả nhóm đều CHƯA, thì KHÔNG lệch.** Cả viện thuộc diện
  WebSearch là một lựa chọn đã khai (`WEBSEARCH_ONLY`), không phải một lỗ — kêu vào đó là kêu
  oan hàng loạt, mà bảng bị kêu oan vài lần thì hết được đọc.
- ⚠️ **BA CÁI BẪY, dựng sai là kêu oan ngay lượt đầu** (đều đã thành ca đối chứng trong cổng):
  **(1) so trên TÊN ĐĂNG KÝ, không so cả chuỗi tên miền** — `iss.europa.eu` và `issafrica.org`
  khớp nhau ở chuỗi `iss`, nhưng `iss` bên trái là tên miền CON còn tên đăng ký của nó là
  `europa`; EUISS và ISS Africa là hai viện khác hẳn. **(2) phải biết ĐUÔI CÔNG CỘNG NHIỀU
  MẢNH** — `iseas.edu.sg` và `rsis.edu.sg` lấy hai mảnh cuối thì ra chung `edu.sg`, trong khi
  tên đăng ký thật là `iseas` và `rsis`; thiếu bảng `DUOI_NHIEU_MANH` là mọi viện Úc gom một
  cục, mọi viện Singapore gom một cục. **(3) ngưỡng tiền tố chung phải ≥ 4 ký tự** — `cepa.org`
  và `ceps.eu` chung 3 ký tự đầu mà là hai viện khác nhau.
- ⚠️ **Cộng một bảng `MIEN_TRO_CHUNG`**: `ctc.westpoint.edu` (Combating Terrorism Center) và
  `mwi.westpoint.edu` (Modern War Institute) là hai viện khác nhau cùng trọ dưới tên miền một
  trường đại học. Gom theo hình dạng (a) mà không loại tên miền đại học là kêu oan. Thêm tên
  miền vào bảng đó là **TẮT phép đo** cho mọi viện trọ dưới nó — chỉ thêm tên miền của tổ chức
  CHỦ NHÀ, đừng thêm tên miền của chính viện.
- **BỐN NHÓM KHÔNG PHẢI LỖI, đã ghi `DA_DUYET`**: `spf.org`/`spfusa.org` (hai nhánh thật của
  quỹ Sasakawa — Tokyo và Washington, hai ban biên tập riêng) · `agsi.org`/`agsiw.org` (viện
  ĐỔI TÊN, tên cũ redirect sang tên mới; giữ cả hai chỉ để bài cũ trong kho không bị guardrail
  domain chặn oan) · `ctc`/`mwi.westpoint.edu` · `dialogo-americas.com`/`thedialogue.org`
  (phép gom dán chúng vào nhau vì chung 6 ký tự sau khi bóc `the`, nhưng một bên là tạp chí của
  Bộ Chỉ huy miền Nam Hoa Kỳ, bên kia là viện Inter-American Dialogue).
- **Hướng lệch CÓ CHỦ Ý: phép gom cố ý RỘNG.** Gom thừa một nhóm thì tốn đúng một dòng
  `DA_DUYET`; gom hụt thì lỗ nằm im tiếp — mà im lặng chính là thứ phép đo này sinh ra để chặn.
- **Đã xử lý ngay lượt dựng — CSIS xuất bản dưới BỐN tên miền** (`csis.org` · `amti` ·
  `interpret` · `chinapower`), ba cái đầu có đường quét còn `chinapower.csis.org` thì không.
  Đã tìm ra feed thật `https://chinapower.csis.org/feed/` (200 · 10 item) bằng cách đọc thẻ
  `<link rel="alternate">` trên trang chủ — cùng đường đã tìm ra feed RUSI và CACI — và khai
  vào `THINKTANK_FEEDS`. ⚠️ Viện này đăng **THƯA (~1 bài/tháng)** nên thường nằm trong dòng
  *"feed không ra bài"*, đó là bình thường; và feed xếp item **KHÔNG theo thời gian** (bài ghim
  từ 2016 nằm lẫn giữa bài 2026) — vô hại vì `loc_ung_vien_feed` lọc theo `pubDate` chứ không
  theo vị trí, nhưng **đừng đọc item đầu feed thành "bài mới nhất"**.
- `--tu-kiem` gồm **01 ca vàng chạy trên BẢNG NGUỒN THẬT**: nhóm lệch nào chưa ai soi thì ĐỎ.
  Đã nạp `BO_TEST` của `khoe.py` cùng cổng, nên một viện mới lệch là sáng hôm sau biết.
- ⚠️ **Ca đối chứng của bản hỏng phải tránh chỗ CÓ HAI LỚP CÙNG CHE.** Ca kiểm bảng
  `MIEN_TRO_CHUNG` cố ý KHÔNG dùng cặp `ctc`/`mwi.westpoint.edu` — cặp đó vừa bị bảng ấy loại
  vừa nằm trong `DA_DUYET`, nên gỡ bảng đi mà ca vẫn xanh. Tương tự, ca kiểm hình dạng (a) dùng
  tên đăng ký **3 ký tự** (`vbc.org` / `blog.vbc.org`): tên dài hơn ngưỡng thì hình dạng (b)
  gánh luôn, gỡ lớp (a) cũng không ai thấy.

⚠️ **`tests/test-nguon-nghien-cuu.py --tu-kiem` ĐANG HỎNG (0/3)** — harness của nó đem thay
CHÍNH FILE CỔNG chứ không thay `add_analyses.py` như docstring khai, và cả 03 phép thay đều
LÀM YẾU cổng, mà cổng yếu chạy trên bản đúng thì không thể đỏ. Cổng vẫn **CÓ răng**: đo riêng
06/08 bằng 04 bản `add_analyses.py` hỏng qua seam `ADD_ANALYSES` thì **4/4 bị bắt**, mỗi bản đỏ
đúng ca của nó. Vì vậy cổng nạp vào `khoe.py` **không kèm cờ `--tu-kiem`**. Chi tiết và cách đo
lại: `logs/loi-cong-nguon-nghien-cuu.md`.

| Bước | Lệnh | Ghi chú |
|---|---|---|
| Liệt kê ứng viên | `python3 scripts/add_analyses.py --candidates` | Fetch RSS **24 viện đã verify fetch thật 27/07**, xếp theo KHU VỰC (xem `THINKTANK_FEEDS`). Tự bỏ bài đã có trong DATA, đường dẫn rác (`/in-the-news/`, `/media-citations/`, `/event/`…) và tham số `utm_*`. Dòng cuối in **vùng không có RSS + domain** để bù bằng WebSearch |
| Nạp | `python3 scripts/add_analyses.py /tmp/analyses.json` | Guardrail: xem docstring đầu file |

⚠️ **War on the Rocks KHÔNG chết** — bảng "BỎ HẲN" phía trên ghi 403 là do curl trần; thêm `-A <UA>`
và `--compressed` thì feed trả 100 item bình thường. Cùng bài học với UN News hồi 22/07: đừng gạch một
nguồn khi chưa loại trừ lỗi header/giải nén.
**KHÔNG có RSS dùng được** (đã thử 2 biến thể URL mỗi nơi 27/07, đừng thử lại): CSIS · Brookings ·
~~RUSI~~ · Chatham House · ORF · CNAS · FPRI (trả HTML) · 38 North · Stimson (Cloudflare) · USIP (404) ·
Carnegie · Belfer · Wilson Center (XML hợp lệ nhưng 0 item) → `WebSearch site:<domain>`.

### 🔍 ĐO LẠI TOÀN BỘ NGUỒN THINK-TANK BỊ CHẶN — 30/07/2026 (chỉ thị Huy: kiểm bằng trình duyệt thật)
Dò lại cả **40 domain** trong `WEBSEARCH_ONLY` bằng curl có UA trình duyệt, thử **CẢ dạng `www.` lẫn
không**, rồi mở bằng trình duyệt những cái curl chịu. Kết quả đảo lại phần lớn đánh giá cũ:

| Nhóm | Số | Ý nghĩa |
|---|---|---|
| curl **đọc được HTML** (200) | **29/40** | chỉ THIẾU FEED, không mất nguồn — quét HTML trang danh sách vẫn lấy được bài |
| Cloudflare 403 nhưng **trình duyệt mở được** | 08 | 38north · ecfr.eu · chathamhouse · clingendael · inss.org.il · mei.edu · nti.org · thearcticinstitute · thebulletin |
| **chặn hẳn ở mọi đường** | 03 | globsec.org (kẹt challenge) · thesoufancenter.org (403 cứng) · idsa.in (DNS hỏng từ máy Huy) |

- ✅ **Thêm 30/07 chiều — dò `<link rel=alternate>` trên CẢ 40 domain, ra thêm 02 feed ẩn:**
  **CACI Analyst** `https://www.cacianalyst.org/publications/analytical-articles.feed` (10 item, bài mới
  13/07) mở lại vùng **Trung Á · Caucasus** vốn trắng hoàn toàn; **USIP** `https://www.usip.org/feed/`
  (10 item, nhưng đăng thưa — bài mới nhất đã 35 ngày lúc thêm, nên thường nằm trong dòng "feed không
  ra bài", đó là bình thường). Cả hai đã RỜI `WEBSEARCH_ONLY`.
  ⚠️ CACI có **hai** feed cùng trả 200: cái ở trang chủ (`/?format=feed`) đứng từ **2012**. Đọc
  `pubDate` item đầu trước khi tin, đừng dừng ở mã 200.
- ✅ **RUSI đã có RSS trở lại** → đưa vào `THINKTANK_FEEDS`: `https://www.rusi.org/rss/latest-commentary.xml`
  (**8 bài/khung ngày** ngay lần chạy đầu). Feed nằm ở path lạ, tìm ra bằng cách đọc thẻ
  `<link rel="alternate">` trong HTML trang chủ — **đó là bước phải làm trước khi gạch một nguồn**, cùng
  bài học UN News (thiếu `--compressed`) và War on the Rocks (thiếu `-A`).
- ⚠️ **`agsiw.org` đã đổi tên miền thành `agsi.org`** (viện đổi tên) — đó mới là lý do feed cũ trả 0 item,
  không phải feed hỏng. Đã thêm `agsi.org` vào `THINKTANK_DOMAINS` và **giữ cả `agsiw.org`**, vì bài cũ
  trong kho còn mang url cũ, gỡ đi là guardrail chặn oan chính chúng.
- ⚠️ **Chỉ thử `https://<domain>/` là hụt**: `spf.org` và `usip.org` trả 000/hỏng ở dạng trần nhưng **200**
  với `www.` — vòng đo đầu của chính phiên này đã chấm sai hai cái đó. Luôn thử cả hai dạng.
- ⚠️ **Cloudflare challenge cần vài giây**: trang trả "Just a moment..." rồi mới ra nội dung; đọc một lần
  thấy challenge mà kết luận "chặn" là sai. Đọc lại 2–3 lượt (có lượt ném lỗi `innerText` của null giữa
  chừng — bình thường, đọc tiếp).
- 📌 Trình duyệt **trong app** đủ để vượt Cloudflare, KHÔNG cần Chrome thật (`list_connected_browsers`
  trả rỗng khi tiện ích chưa mở). Nhưng đường này **chỉ có ở phiên local** — CI không dùng được, nên
  đừng đưa 08 domain kia vào `THINKTANK_FEEDS`.

**Guardrail riêng, khác `add_news.py`:** khung ngày **7 ngày** (bài viện đăng thưa, không "ôi" sau 24h)
nhưng vẫn kiểm HAI LỚP như add_news nên neo lô về ngày cũ không lách được; và `outlet` bị SIẾT theo
**DOMAIN** (`THINKTANK_DOMAINS`) — mục tên là Think-tank mà lọt bài Al Jazeera/Naval News thì hỏng chính
danh nghĩa của mục (18 bài đời cũ trong DATA có lẫn như vậy). Gặp lỗi domain → **BỎ bài**, đừng đổi url
cho lọt; đúng là viện thật mà thiếu thì thêm domain vào danh sách trong script.

### 🚪 BẢNG ĐƯỜNG VÀO TỪNG NGUỒN — trang nào phải xem bằng cách gì (chỉ thị Huy 30/07/2026)

> Nguyên văn: *"thêm vào quy tắc hoặc ghi nhớ lại là trang nào phải xem bằng cách gì."*

**Cơ chế gây vấp:** mỗi phiên lại tự đi dò lại từ đầu, và dò bằng ĐÚNG MỘT công cụ rồi kết luận
"nguồn chết" — 30/07 đo được 31/40 domain bị xếp nhầm vào diện chặn chỉ vì thử mỗi `curl`. Kết quả
dò không được ghi lại thì phiên sau vừa tốn công dò lại, vừa dễ ra kết luận ngược nhau. Bảng dưới
là **nguồn sự thật về ĐƯỜNG VÀO**; bảng RSS phía trên là nguồn sự thật về URL feed.

| # | Đường vào | Dùng cho | Cắm ở đâu | Chạy được ở |
|---|---|---|---|---|
| 1 | **RSS** | nguồn có feed sống | `THINKTANK_FEEDS` (viện) · bảng RSS đầu file (báo) | local + CI |
| 2 | **Quét HTML trang danh sách** (`curl` có UA) | không feed nhưng render sẵn HTML | `THINKTANK_HTML` (viện) · bảng 🕸️ TRANG HTML (uỷ ban Mỹ) | local + CI |
| 3 | **Chỉ CI đọc được** | trang chặn IP nhà nhưng mở cho runner Mỹ | cột "Chạy ở = CI" trong bảng 🕸️ | **CI thôi** |
| 4 | **Trình duyệt thật** (Browser pane) | Cloudflare challenge — chặn theo vân tay TLS | KHÔNG cắm vào script nào | **local thôi** |
| 5 | **WebSearch `site:<domain>`** | JS-only, 404, DNS hỏng | `WEBSEARCH_ONLY` | local + CI |

**Thứ tự phải đi khi gặp một nguồn mới hoặc nghi một nguồn chết** — dừng ở bước đầu tiên ra kết quả,
và **chỉ được kết luận "chết" sau khi đi hết 5 bước**:
1. thử `curl -sL --compressed -A '<UA trình duyệt>'` — thiếu `-A` thì War on the Rocks 403, thiếu
   `--compressed` thì UN News ra nhị phân; hai lần gạch nhầm nguồn đều từ đây;
2. thử **cả `www.` lẫn không** — `spf.org` và `usip.org` trả 000 ở dạng trần, 200 với `www.`;
3. đọc thẻ `<link rel="alternate" type="application/rss+xml">` trên trang chủ — feed hay nấp ở path
   lạ: RUSI ở `/rss/latest-commentary.xml`, CACI ở `/publications/analytical-articles.feed`, USIP ở
   `/feed/`. Cả ba đều từng bị xếp "không có RSS";
4. mở bằng **trình duyệt trong app** — Cloudflare challenge cần chờ 6–8 giây rồi mới ra nội dung;
5. hết cả bốn thì mới `WebSearch site:<domain>`, và ghi vào `WEBSEARCH_ONLY` kèm lý do.

⚠️ **Ba cái bẫy khi đọc kết quả dò:**
- **`403`/`307` không đồng nghĩa với chặn** — Cloudflare "Just a moment…" trả 403 cho máy quét mà
  trình duyệt vào bình thường (usni · pna.gov.ph · rsis · japantimes).
- **Hỏng trong dưới 1 giây không bao giờ là mạng chậm** — đó là chữ ký tường lửa ứng dụng. HTTP/2
  trả `INTERNAL_ERROR` sau 0,12–0,28 giây; timeout thật thì đủ 25 giây.
- **Feed trả 200 chưa chắc là feed sống** — CACI có hai feed cùng trả 200, cái ở trang chủ đứng từ
  **2012**, cái ở trang chuyên mục thì mới hôm kia. Luôn đọc `pubDate` của item đầu.

⚠️ **Đường 4 KHÔNG được cắm vào script.** Trình duyệt chỉ có ở phiên local; cắm vào là lớp quét ra
kết quả khác nhau giữa local và CI — hỏng câm khó truy nhất. Hiện thuộc diện này: 38north · ecfr.eu ·
chathamhouse · clingendael · inss.org.il · mei.edu · nti.org · thearcticinstitute · thebulletin.
⚠️ **Chặn hẳn ở mọi đường** (đo 30/07, đừng thử lại): globsec.org (kẹt challenge vĩnh viễn) ·
thesoufancenter.org (403 cứng) · idsa.in (DNS hỏng từ máy Huy, cùng kiểu zone `.mil`).
⚠️ **Trang `.mil`**: máy Mac KHÔNG phân giải nổi DNS zone `.mil` (DNSSEC lỗi) — đường 3 trong bảng,
xem mục "🪖 Trang .mil" phía trên. Đây là giới hạn tầng DNS, không vá được bằng cờ curl.

### 🕸️ LỚP [HTML] QUÉT THINK-TANK — viện không có RSS (dựng 30/07/2026)
`add_analyses.py` nay có lớp thứ hai bên cạnh RSS: quét thẳng trang danh sách publications của **10
viện** không có feed. Trước đó những viện này phụ thuộc hoàn toàn vào việc agent có nhớ `WebSearch
site:<domain>` hay không — tức một mục có tồn tại hay không tuỳ trí nhớ của phiên.

| | |
|---|---|
| Bảng cấu hình | `THINKTANK_HTML` trong `scripts/add_analyses.py` — (tên viện, trang danh sách, biểu thức đường dẫn BÀI, khu vực) |
| Soi sức khoẻ | `python3 scripts/add_analyses.py --kiem-html` — ~3 giây, chạm mạng thật. Mã 3 = trang chết · mã 4 = có domain mồ côi |
| Bộ test canh | `tests/test-html-thinktank.py` (**21 ca** · `--tu-kiem` bắt **16/16** bản hỏng), đã nạp `khoe.py` |
| Sản lượng đo 30/07 | **44 ứng viên** trong khung 7 ngày, cộng với 159 từ RSS |
| Số viện HIỆN HÀNH | **24** (10 dựng 30/07 + 05 thêm 20/08 + 09 thêm 21/08/2026) |

**➕ 05 VIỆN THÊM 20/08/2026 — lấp bốn vùng gần như trắng.** ACSS (`/in-focus/`, châu Phi ·
Sahel) · CTC Sentinel West Point (khủng bố) · IFRI (`/en/publications/all`, Pháp) · SWP Berlin
(`/en`, Đức) · JIIA (`/en/column/`, Nhật). Bốn viện đầu đăng THƯA 1-4 bài/tháng nên lớp này ra
0 bài phần lớn các ngày — bình thường, phân biệt với path chết bằng `--kiem-html` (nó in SỐ LINK
khớp, khác hẳn số bài trong khung).
- ⚠️ **ACSS phải là `/in-focus/`, KHÔNG phải `/research/`** dù `/research/` cho nhiều link hơn
  (16 so với 6): `/research/` xếp theo CHỦ ĐỀ nên bài mới nhất trên đó đã 5 tháng tuổi. Đúng bài
  học Wilson Center — nhiều link không có nghĩa là danh sách mới.
- ⚠️ **CTC đặt bài THẲNG ở gốc tên miền**, không tiền tố nào, nên biểu thức path phải chặn bằng
  ĐỘ DÀI (`^/[a-z0-9-]{30,}/?$`) thay vì bằng tiền tố.
- ⚠️ **SWP: đừng đọc ghi chú bỏ-feed rồi suy ra "SWP là nguồn đã loại".** Feed của họ bị bỏ vì là
  feed ĐIỂM BÁO; nhánh `/en/publication/…` lấy ở đây là nghiên cứu do chính viện xuất bản.

**🗓️ BƯỚC (1b) — NGÀY NẰM TRONG TÊN FILE** (thêm 20/08/2026 cùng lượt cắm JIIA). JIIA dùng đường
dẫn `/eng/report/2026/08/20260817.html`: bước (1) đòi đủ `/YYYY/M/D/` nên trượt, còn trang danh
sách CHỈ in `2026/08` cạnh tiêu đề. Kết quả cũ: mọi bài JIIA nhận chung ngày mồng 20 của tháng
đó, lệch tới 19 ngày **mà vẫn nằm trong khung 7 ngày** nên không ai thấy. Nay đọc 8 chữ số trong
TÊN FILE, có ranh giới hai đầu để mã báo cáo kiểu `asb44en-20260712345` không bị đọc thành ngày.
Cả hai chiều đều có ca test và bản hỏng riêng.

**Ngày lấy theo 3 bước, dừng ở bước đầu tiên ra kết quả** — đây là chỗ khác lớp `[HTML]` của
`harvest.py` (bên đó đoán ngày quanh link nên phải dặn agent mở bài kiểm lại):
(i) ngày nhúng trong đường dẫn (`/2026/07/28/…`); (ii) ngày **gần link nhất** trên trang; (iii) mở
trang bài đọc `ld+json datePublished` / `article:published_time` / `<time datetime>`.

⚠️ **Bước (ii) phải là "gần nhất", KHÔNG phải "đầu tiên trong ±800 ký tự"** — bản đầu viết kiểu quét
cửa sổ và sai câm hai chiều, cả hai đã dựng thành ca test: bài không có ngày riêng thì **ăn ngày của
bài bên trên**, còn bài cũ nằm dưới bài mới thì **ăn ngày của bài mới** ⇒ bài tháng Một lọt vào danh
sách "bài trong tuần". Luật đúng: một ngày chỉ thuộc về link nào gần nó hơn cả.
⚠️ **Trang trả dưới 2000 byte bị coi là trang chặn** — trang challenge vài KB vẫn có link điều hướng,
không chốt là nạp rác.
⚠️ **Đổi bảng `THINKTANK_HTML` thì domain phải có trong `THINKTANK_DOMAINS`**, nếu không quét ra bài
rồi tới lúc NẠP mới bị guardrail chặn. Đã có ca test canh đúng chỗ này.
⚠️ **Trang ra 0 link ≠ hôm nay viện không ra bài.** `--kiem-html` phân biệt hai ca đó (thoát mã 3 kèm
tên trang), còn `--candidates` in dòng cảnh báo riêng. Đừng gộp hai thông điệp lại.

**Đã thử và BỎ, đừng dựng lại:** `stimson.org` (chỉ trang chủ đọc được, 0/16 bài trong khung, trang
bài 573KB/5,4 giây — chiếm quá nửa thời lượng cả bảng để đổi lấy không gì) · `issafrica.org`,
`washingtoninstitute.org`, `carnegieendowment.org`, `iiss.org`, `brookings.edu` (danh sách dựng bằng
JS, HTML thô chỉ có link điều hướng).

### 🕳️ 35 VIỆN NẰM TRONG GUARDRAIL MÀ KHÔNG LỚP NÀO QUÉT — vá 20/08/2026
Hỏng câm ở tầng DANH SÁCH, không ở tầng mã. `THINKTANK_DOMAINS` (danh sách guardrail dùng khi
NẠP) có **35 domain** không xuất hiện ở `THINKTANK_FEEDS`, `THINKTANK_HTML` lẫn `WEBSEARCH_ONLY`.
Hậu quả: không lớp nào quét về, và `--candidates` cũng không giục agent tìm — nhìn danh sách
guardrail thì tưởng đã phủ. Trong số đó có **`cfr.org`**, viện đối ngoại lớn nhất của Mỹ, feed 24
item ra bài mỗi ngày, chưa từng vào kho suốt từ ngày dựng.

**Đã dò feed cả 35 domain** (thẻ `<link rel="alternate">` + `/feed/` + `/rss.xml`) — chỉ 07 có
feed sống, và trong 07 thì 02 phải bỏ:

| Cắm vào `THINKTANK_FEEDS` | Vì sao |
|---|---|
| CFR `https://www.cfr.org/feed/` | 24 item, 19 bài `/articles/`, ra bài hằng ngày |
| FDD `https://www.fdd.org/category/analysis/feed/` | **nhánh `category/analysis`, KHÔNG dùng `/feed/` gốc** — feed gốc có 32/50 item nằm ở `/in_the_news/`, mà đường dẫn viết bằng gạch DƯỚI nên `NOISE_PATHS` (`/in-the-news/`, gạch ngang) không chặn được |
| Inter-American Dialogue `https://thedialogue.org/feed` | **lấp vùng Mỹ Latin**, trước nay trắng hoàn toàn |
| Real Instituto Elcano `https://www.realinstitutoelcano.org/en/feed/` | bản `/en/` — feed gốc ra bài tiếng Tây Ban Nha |
| SPF USA `https://www.spfusa.org/feed/` | đăng rất thưa, gần như luôn nằm trong dòng "feed không ra bài" — bình thường, giống USIP |

⛔ **ĐÃ ĐO VÀ BỎ, đừng cắm lại:** `defensepriorities.org/feed/` (10/10 item ở `/in-the-media/`,
tức điểm báo) · `iss.europa.eu/rss.xml` EUISS (nội dung là *"X discussing … in Euronews"*, trích
dẫn truyền thông chứ không phải nghiên cứu — cùng loại với feed SWP và Clingendael đã bỏ).

**30 domain còn lại xếp xuống `WEBSEARCH_ONLY`** theo khu vực — hướng lệch AN TOÀN (bài vẫn tới
được qua WebSearch), **không phải kết luận "không quét HTML được"**.
✅ **Lời dặn "viện nào hay ra bài thì đo `--kiem-html` rồi nâng lên `THINKTANK_HTML`" ĐÃ THI HÀNH
21/08/2026 — 11/30 domain đã rời khỏi đây, xem mục ngay dưới.** Đừng đọc đoạn này rồi đi dò lại
từ đầu: 19 domain còn ở `WEBSEARCH_ONLY` nay đều mang lý do đã đo.

**Phép đo phải giữ:** `add_analyses.domain_chua_co_duong_quet()` = `THINKTANK_DOMAINS` trừ
(FEEDS ∪ HTML ∪ WEBSEARCH_ONLY ∪ `DOMAIN_CU_DA_CHUYEN`). `--kiem-html` in tên domain mồ côi rồi
thoát **mã 4**; hai ca test canh cả phép đo lẫn việc `--kiem-html` có kêu hay không.
⚠️ `DOMAIN_CU_DA_CHUYEN` miễn trừ tên miền CŨ của viện đã đổi tên (`agsiw.org` → `agsi.org`):
guardrail phải giữ chúng cho bài cũ trong kho, nhưng chúng không cần đường quét riêng — không
miễn thì phép đo kêu oan mãi mãi.

**Sản lượng đo 20/08/2026 sau cả hai đợt vá:** 206 → **254 ứng viên** (215 RSS · 39 HTML).

### ✅ DÒ QUÉT HTML CHO 30 VIỆN CÒN LẠI — 21/08/2026 (nối tiếp mục ngay trên)

Mục trên xếp 30 domain xuống `WEBSEARCH_ONLY` kèm lời dặn *"CHƯA dò quét HTML cho nhóm này"*.
Đây là vòng dò ấy. Kết quả: **11/30 rời khỏi WebSearch** — 09 lên `THINKTANK_HTML`, 02 lên
`THINKTANK_FEEDS`; 19 còn lại nằm nguyên nhưng nay mang **lý do đã đo**, không còn là "chưa dò".

| Lên `THINKTANK_HTML` | Trang danh sách | Đo 21/08 (link · bài mới nhất) |
|---|---|---|
| **ISW** | `understandingwar.org/publications` | 16 · 19/08 |
| **NBR** | `nbr.org/publications/` | 16 · 19/08 |
| **USSC (Úc)** | `ussc.edu.au/publications` | 16 · 17/08 |
| **PIIE** | `piie.com/blogs` | 10 · 17/08 |
| **Defense Priorities** | `defensepriorities.org/explainers/` | 14 · 18/08 |
| **Timbuktu Institute** | `timbuktu-institute.org/index.php/publications` | 16 · 17/08 |
| Egmont | `egmontinstitute.be/publications/` | 6 · 16/07 |
| EUISS | `iss.europa.eu/publications/commentary` | 10 · 09/07 |
| SIPRI | `sipri.org/commentary` | 16 · 02/07 |

**Sản lượng, đo hai bản CÙNG một thời điểm** (bản cũ lấy từ `git show HEAD:`, chạy cạnh bản mới
để loại yếu tố ngày khác nhau): **222 → 247 ứng viên** · HTML 34 → 56 · RSS 188 → 191.

⚠️ **ISW ra 3-4 bài MỖI NGÀY và tất cả đều là loạt định kỳ** (*"Russian Offensive Campaign
Assessment, August 19, 2026"*). Đo 21/08: 16/16 link khớp đều thuộc loạt này, tức viện này một
mình chiếm trọn `HTML_LINK_CAP` của chính nó. Không lấn viện khác (trần tính theo TỪNG trang),
nhưng agent chọn bài phải biết đây là báo cáo tình hình định kỳ chứ không phải nghiên cứu mới:
lấy nhiều nhất 1-2 bài, ưu tiên bản *"Special Report"*. Nhồi cả loạt vào kho là biến mục
Think-tank thành nhật ký chiến sự.
⚠️ **Defense Priorities và EUISS đều đã bị BỎ FEED hôm 20/08 vì feed của chúng là điểm báo** —
lớp HTML lấy nhánh KHÁC HẲN (`/explainers/` · `/publications/commentary/`), là bài do chính
viện viết. Đúng ca SWP; hai ghi chú ấy KHÔNG mâu thuẫn nhau, đừng đọc ghi chú bỏ-feed rồi suy
ra "nguồn đã loại".

#### ⛔ HAI LỖ CÂM BẮT ĐƯỢC TRONG CHÍNH VÒNG DÒ NÀY — cả hai đều nằm ngoài phạm vi việc đang làm

**(1) `parse_feed` chết vì MỘT ký tự xuống dòng ở đầu file.** Feed Gulf International Forum mở
đầu bằng `\n` trước `<?xml …?>` (WordPress hay in thừa như vậy khi một plugin phát ra newline
trước header). `ET.fromstring` ném *"XML or text declaration not at start of entity"* ⇒
`parse_feed` trả `None` ⇒ `feed_items` trả rỗng ⇒ nguồn hiện ra ở dòng *"Feed không ra bài nào
trong khung ngày"* — **nhìn dòng đó không phân biệt được với viện đăng thưa thật**, nên một
nguồn có thể nằm chết trong bảng hàng tháng. Feed ấy thật ra trả 113 KB và 10 item hợp lệ.
Đã vá bằng `lstrip` BOM + khoảng trắng; quét lại toàn bộ 44 feed thì **chỉ GulfIF dính**.
⚠️ Chỉ cắt **khoảng trắng và BOM**, không cắt gì khác — rác đầu file mà không phải khoảng trắng
thì đó là trang lỗi hoặc trang challenge, đọc nó thành feed mới là hỏng thật. Ca [03] canh
chiều nới này, bản hỏng *"cắt tới `<?xml` đầu tiên"* làm nó đỏ.

**(2) SPF USA khai nhầm nhánh feed — cùng hình dạng Lowy và ASPI.** `do_nguon_mot_muc.py` tố
tên miền này ngay lượt chạy đầu. Feed khai hôm 20/08 là `/feed/` gốc: 12 item toàn
`/spfusa-news/` và `/congressional-outreach/`, bài mới nhất **21/03/2026** — nên chú thích lúc
ấy kết luận *"viện đăng RẤT thưa"*. Đo lại: `/publications/feed/` trả 12/12 item dưới
`/publications/`, bài mới nhất **01/08/2026**. Viện ra bài đều, chỉ là đường vào khai nhầm
nhánh. Đã đổi feed và ghi `DA_DUYET`.
⚠️ **Cố ý KHÔNG giữ thêm feed gốc**, khác ca ASPI (ở đó cả blog lẫn báo cáo đều là nghiên cứu
nên giữ cả hai): nhánh gốc ở đây là tin hoạt động, cùng loại với các feed điểm báo đã bỏ.
⚠️ **Bài học chung của cả hai lỗ:** một dòng *"feed không ra bài"* và một chú thích *"viện đăng
thưa"* đều là **kết luận**, không phải số đo. Trước khi tin, đọc `pubDate` của item đầu và xem
item rơi vào MỤC nào — đó là hai phép đo phân biệt được "nguồn thưa" với "khai nhầm nhánh" và
với "parser chết".

⛔ **ĐÃ DÒ QUÉT HTML VÀ BỎ (21/08/2026) — đừng dò lại.** Ba nhóm nguyên nhân khác hẳn nhau, ghi
đủ trong `add_analyses.py` ngay dưới `WEBSEARCH_ONLY`; tóm tắt:
- **(a) không trả về HTML** (chặn hoặc JS-only): rsis.edu.sg 5,7 KB · aei.org 5,5 KB ·
  sipa.columbia.edu 5,7 KB · cato.org 949 B · csbaonline.org 103 B · ispionline.it 552 B ·
  pism.pl 212 B · sejong.org 1,4 KB · epc.ae và giga-hamburg.de đọc được nhưng 0 href bài ·
  carnegieeurope.eu chuyển hướng sang Carnegie Endowment (đã biết JS-only).
- **(b) có link, KHÔNG có ngày** — nguy hơn (a) vì trang danh sách trả hàng trăm KB nên nhìn như
  đang chạy: ceps.eu (trang bài lẻ trả 5,9 KB, không meta ngày nào; 11/16 link không ngày) ·
  tokyofoundation.org (`/research/detail.php?id=…`, 11/16 không ngày, mọi bài chung một path).
- **(c) lấy được đủ nhưng nội dung không thuộc mục này** — phải chặn bằng phán xét, không cổng
  máy nào bắt: nupi.no (bản ghi thư mục học thuật, chỉ abstract) · prif.org (bài thật ở
  `blog.prif.org`, TÊN MIỀN khác nên guardrail chặn khi nạp) · ui.se (ấn phẩm là PDF) ·
  highnorthnews.com (**BÁO tin tức Bắc Cực, không phải viện**) · foreignaffairs.com (tạp chí
  trả phí, bài xếp theo khu vực nên không tiền tố nào tách được bài khỏi trang chuyên mục).

**Bộ test canh:** `tests/test-html-thinktank.py` nay **27 ca · `--tu-kiem` bắt 22/22 bản hỏng**
(thêm 06 ca: 02 cho `parse_feed` hai chiều · 04 cho biểu thức path của các viện hình dạng lạ —
SIPRI phải mở cờ `(?i)` vì trang trộn `/commentary/essay/` thường với `/commentary/
Topical-backgrounder` HOA; ISW không được nuốt trang chuyên mục; USSC · Egmont đặt bài ở GỐC nên
chỉ còn ĐỘ DÀI để chặn; Timbuktu chạy Joomla `/index.php/<mục>/item/<id>-<slug>`).
⚠️ Ca đối chứng *"trang sống thì `--kiem-html` KHÔNG kêu oan"* đã phải vá cùng lượt: nó tráo
`THINKTANK_HTML` bằng bảng một dòng, mà `kiem_html` gộp HAI nhánh vào một mã thoát (trang chết =
3 · domain mồ côi = 4), nên mọi domain HTML thật lập tức thành mồ côi và ca đỏ vì nhánh nó KHÔNG
định đo. Trước 21/08 nó xanh chỉ vì mọi domain trong bảng HTML khi ấy **tình cờ** còn nằm cả ở
`WEBSEARCH_ONLY`; 09 viện rời danh sách ấy là giả định ngầm vỡ ngay. Đã cô lập bằng cách ghim
guardrail về đúng domain của trang giả — **không nới điều kiện của ca cho hết đỏ**.

### 🏷️ Nhãn `outlet` — bảo trì bằng `scripts/sua_nhan_analyses.py` (dựng 29/07/2026)
Guardrail của `add_analyses.py` kiểm theo **DOMAIN**, **không kiểm nhãn `outlet`** — cố ý, vì tên viện
viết mỗi lúc một kiểu. Cái giá: cùng một domain vẫn nạp được dưới hai tên khác nhau, và web thì hiện
`outlet` ra thẳng dòng `.foot` **đồng thời dùng nó làm khoá `voteMeta.src`** của hồ sơ độc giả — nhãn
tách đôi là tín hiệu bình chọn cũng chia đôi, học sai mà không có dấu hiệu gì. Bắt được thật 29/07:
`'ASPI'` và `'ASPI Strategist'` cùng `aspistrategist.org.au`.
```
python3 scripts/sua_nhan_analyses.py --kiem       # liệt kê nhãn+domain, soi 3 loại lỗi (mã 2/3/4)
python3 scripts/sua_nhan_analyses.py --gop-nhan   # áp OUTLET_CANON (domain → nhãn chuẩn)
python3 scripts/sua_nhan_analyses.py --tu-kiem    # chứng minh --kiem bắt được lỗi
```
| `--kiem` bắt | Xử lý |
|---|---|
| Một domain nhiều nhãn | thêm dòng vào `OUTLET_CANON` rồi `--gop-nhan` — **chọn nhãn chuẩn theo `add_analyses.py::THINKTANK_FEEDS`, đừng chỉ đếm số bài** (xem ⚠️ dưới bảng) |
| Domain ngoài `THINKTANK_DOMAINS` | **đúng là viện thật → thêm domain**, đừng xoá bài (ca ISW `understandingwar.org` 29/07: guardrail đang chặn oan cả bài mới). Là báo chí → **HỎI Huy** rồi mới `--xoa-url` |
| Hai bản cùng một bài gốc | trùng **slug cuối url** — `warontherocks.com/<slug>` và `.../2026/07/<slug>` là hai chuỗi khác nhau nên guardrail trùng-url cho lọt cả hai. Huy chốt giữ → ghi vào `TRUNG_DA_DUYET` |

⚠️ **CHỌN NHÃN CHUẨN THÌ SOI `add_analyses.py::THINKTANK_FEEDS` TRƯỚC, ĐỪNG CHỈ ĐẾM SỐ BÀI** (đúc
30/07/2026). Bảng feed đó là **nơi sinh nhãn cho mọi lô nạp về sau**, nên chọn khác nó là cổng sạch
hôm nay rồi tách nhãn lại ở bài kế tiếp của chính domain ấy — sửa mà không đóng được nguồn sinh lỗi.
Ca thật: `fulcrum.sg` mang `'Fulcrum'` (1 bài) | `'Fulcrum (ISEAS)'` (1 bài) — **1-1 nên số lượng
không phân xử được**, bảng feed khai `("Fulcrum (ISEAS)", …)` nên lấy theo bảng feed. Đừng đọc chú
thích "chốt theo tên tự xưng, không theo tên viện mẹ" ở đầu `OUTLET_CANON` một mình rồi suy ra
`'Fulcrum'`: câu đó viết cho ca **hai domain khác nhau của cùng một viện** (`aspistrategist.org.au`
là blog The Strategist, `aspi.org.au` mới là báo cáo viện), không phải cho ca một domain hai nhãn.
⚠️ **Script KHÔNG tự xoá bài** — `--xoa-url` phải gõ đủ url, và xoá là quyết định của Huy. Ghi url +
tiêu đề vào `logs/loai-tin.md` TRƯỚC khi xoá.
⚠️ Chạy `--kiem` sau mỗi đợt nạp think-tank lớn. Con số "18 bài đời cũ lẫn báo chí" ở đoạn trên là số
**tại thời điểm 27/07**; `prune_news.py` đã dọn bớt, tới 29/07 chỉ còn 4 (3 báo chí đã xoá + 1 ISW giữ
lại) — đừng lấy số 18 làm mốc kiểm.

**Email sáng** (`send-morning-email.js`): có khối 🏛️ Think-tank riêng, và **bài think-tank mới cũng đủ
để mở email** kể cả khi không có sự kiện/tập trận nào (hàm `diffAnalyses`; không có bản HEAD~1 để so thì
dựa vào `_addedDate == generatedAt`). Quy trình phiên sáng: `docs/routine-web-scan.md` **Bước 4.4** /
`.github/prompts/web-scan-ci.md` **BƯỚC 6** (địa chỉ cũ `routine-event-scan.md` Bước 2c /
`event-scan-ci.md` bước 3b đã chết từ 28/07/2026: file prompt bị xoá, file docs còn lại là stub).

## DÒ FEED CÒN THIẾU — 03 bẫy đúc 07/08/2026

Đợt triage 05 tên miền mà `scripts/do_nguon_mot_muc.py` nêu. Kết quả: **02 lỗ thật**
(`aspi.org.au` mục `/opinions/` · `cacianalyst.org` mục Feature Articles), 03 còn lại là
phép đo không áp được cho lối đặt URL của viện.

- ⛔ **WORDPRESS `/feed/` CHỈ TRẢ KIỂU BÀI `post` — mọi kiểu bài riêng đều nằm ngoài.** ASPI để
  `/report/` làm kiểu `post`, còn `/opinions/`, `/news/`, `/podcast/` là kiểu riêng. Feed đã
  khai chạy tốt, 200 mọi lượt, ra bài đều — mà mảng bình luận **chưa từng có đường vào nào**.
  Đường dò: đọc `/wp-json/wp/v2/types`, lấy `slug`, rồi `?post_type=<slug>`.
  - ⚠️ **THAM SỐ PHẢI ĐÚNG `slug`, và sai thì KHÔNG có lỗi nào phát ra.** Thử
    `?post_type=opinion` (số ít) thì WordPress **lặng lẽ bỏ tham số và trả feed mặc định**:
    200 · 10 item · nhìn y hệt feed đúng, chỉ là vẫn đủ 10 bài cũ. Đừng đoán tên kiểu bài từ
    nhãn trên thanh điều hướng — đọc `types` rồi lấy `slug`.
- ⛔ **FEED SỐNG VÀ FEED CHẾT TRẢ VỀ CÙNG MÃ 200 — phải đọc `pubDate` mới phân biệt.** CACI có
  04 mục: `feature-articles.feed` bài mới **25/06/2026** (khai), `field-reports.feed` bài mới
  **03/10/2016** (cố ý KHÔNG khai — khai vào là mỗi lượt quét lại kéo tin 2016 vào hàng ứng
  viên). Cùng bẫy đã ghi cho feed trang chủ CACI (`/?format=feed`, 200 nhưng đứng từ 2012).
- ⚠️ **PHÉP ĐO "MỘT MỤC" ĐỌC MẢNH ĐẦU ĐƯỜNG DẪN, nên mù với 02 lối đặt URL** — cả hai đều là
  nêu OAN, không phải lọt:
  - **tiền tố ngôn ngữ** (`icds.ee/en/<slug>`): đã vá, `phan_bo` bóc `TIEN_TO_NGON_NGU` trước
    khi tính mục, rồi tên miền vào `MIEN_BAI_O_GOC`.
  - **container duy nhất** (`rusi.org/explore-our-research/...`): mục thật nằm ở mảnh THỨ BA.
    **CỐ Ý không vá bằng máy**, chỉ ghi `DA_DUYET` — xem gạch dưới.
- ⚠️ **ĐÃ DỰNG BẢN HỎNG VÀ ĐO: nới phép bóc thành "mảnh đầu nào cũng bóc" gây CHẶN OAN HÀNG
  LOẠT, không phải giấu lỗ.** Chú thích bản đầu suy rằng nó sẽ xoá lỗ hình dạng Lowy khỏi bảng
  — SAI: Lowy bóc xong vẫn còn đúng một mục `(GỐC)` nên vẫn bị nêu. Thiệt hại thật là mọi mục
  thật biến thành `(GỐC)`, đo trên kho thật thì `hudson.org` · `cepa.org` · `lowyinstitute.org`
  · `cset.georgetown.edu` cùng lúc vào nhóm ★. **Suy luận nghe rất trôi mà sai dấu; chỉ bản
  hỏng mới tố ra** — đừng viết chú thích cơ chế trước khi dựng bản hỏng và đọc kết quả.
- **`DA_DUYET` là sổ triage, không phải chỗ miễn trừ vĩnh viễn.** Dòng `lowyinstitute.org` đã
  GỠ 07/08 đúng theo lời dặn của chính nó (kho nay 46/7 hai mục, tên miền tự rời nhóm ★). Dòng
  duyệt sống lâu hơn lý do của nó thì thành lỗ hổng.
- Nghiệm thu 07/08: `do_nguon_mot_muc.py --tu-kiem` **9/9 ca · 8/8 bản hỏng**; 03 bộ khác đụng
  `THINKTANK_FEEDS` (`test-html-thinktank` · `test-nguon-hai-mien` · `test-nguon-nghien-cuu`)
  đều chạy lại và xanh.
