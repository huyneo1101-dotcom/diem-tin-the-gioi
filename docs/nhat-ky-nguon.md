# Nhật ký ĐO NGUỒN — trang nào lấy bằng cách gì

<!-- Xẻ từ `CLAUDE.md` ngày 06/08/2026 để cắt chi phí token: toàn bộ file gốc được nạp lại
ở MỌI lượt của MỌI phiên đụng repo này (đo thật: ~99.000 token/lượt), trong khi phần lớn nội dung
là NHẬT KÝ VÁ LỖI chỉ cần đọc khi đụng đúng mảng đó.
⚠️ Nội dung dưới đây giữ NGUYÊN VĂN — cả luật lẫn "cơ chế gây vấp". Đừng rút gọn: phần kể lại
cơ chế chính là thứ ngăn phiên sau dựng lại đúng cái lỗi cũ.
⚠️ CLAUDE.md còn dòng trỏ sang từng mục. Đổi tên mục ở đây thì sửa dòng trỏ bên đó. -->

### 🔑 TRANG NÀO PHẢI LẤY BẰNG CÁCH NÀO — bảng tra (Huy chốt 30/07/2026)

> Nguyên văn Huy: *"thêm vào quy tắc hoặc ghi nhớ lại là trang nào phải xem bằng cách gì."*

**Cơ chế gây vấp:** curl trần là phản xạ mặc định, và khi nó trượt thì kết luận mặc định là "nguồn
chết". Cả hai đều sai — Akamai/Cloudflare nhận dạng **dấu vân tay TLS (JA3/JA4)** của curl · urllib ·
WebFetch rồi cắt kết nối, trong khi Chrome **cùng máy, cùng IP** (đo thật: 113.23.43.99, FPT Hà Nội)
vào bình thường. **Không phải chặn địa lý, nên VPN Mỹ không giải quyết gì.**

| Bậc | Cách lấy | Dùng khi | Ai gọi được |
|---|---|---|---|
| 1 | `curl -sL --compressed -A <UA Chrome>` | mặc định, ~85% nguồn | mọi phiên + CI |
| 2 | **`curl_cffi` `impersonate="chrome"`** (giả vân tay TLS) | bậc 1 trả 403 / thân mang dấu hiệu chặn | mọi phiên + CI, cần `pip install --user curl_cffi` |
| 2b | **THANG `congcu/lay_trang.py`** (thu_lai/thử lại thưa nhịp → wayback → pdf → api_rieng → relay_my, theo `bang-tra-web.json` từng tên miền) | bậc 2 vẫn trượt — CHỈ khi máy có `~/Claude/congcu` | **CHỈ local** — CI không có thư mục dùng chung này |
| 3 | **Browser pane** (`preview_start` → `javascript_tool` `fetch()` same-origin) | bậc 2b vẫn trượt, cần xác minh bằng mắt | CHỈ phiên local có Claude — **CI không dùng được** |
| 4 | `WebSearch site:<domain>` | không có feed, hoặc mọi bậc trên đều trượt | mọi phiên |

`harvest.py` **tự đi bậc 1 → bậc 2 → bậc 2b**: `curl()` dò thân trả về, thấy dấu hiệu chặn thì gọi
`lay_trang.lay()` (thang đầy đủ). Không phải sửa gì khi thêm nguồn mới.

**🪜 CẮM THANG 06 ĐƯỜNG VÀO `curl()` — 30/07/2026 (chỉ thị Huy), thay cho "chỉ thử ĐÚNG một lượt
curl_cffi" trước đó.** Dùng CHUNG một hàm với `App/QuanSu/kho-nen/kiem-url.py` (import
`congcu/lay_trang.py` bằng đường tuyệt đối, đừng dựng lại logic riêng ở từng repo — mục 14 CLAUDE.md
toàn cục cấm hai bản của cùng một thứ).
- **Đo thật lúc cắm** (đợt quét 108 nguồn RSS+HTML hôm đó, 6 nguồn hoàn toàn hỏng với "1 lượt
  curl_cffi"): thang cứu thêm **`spaceforce.mil`** (RSS, qua `wayback` — bản lưu còn trong khung nới
  CNQS 3 ngày) và **`navy.mil`** (HTML, qua `wayback` — 4 candidate mới, trước đó 0). Chạy lại đầy đủ
  cùng ngày còn cứu thêm `thediplomat.com` và `af.mil` (RSS, cả hai qua `wayback`). Vẫn KHÔNG cứu được
  `army.mil`/`marines.mil` hôm đó vì DNS zone `.mil` sập thật trong phiên đo (đúng bệnh "chập chờn") và
  bản lưu Wayback của chúng quá cũ (vài tháng, ngoài mọi khung ngày) — thang không phải phép màu, chỉ
  là thêm một lượt thử theo đúng cấu hình đã đo cho từng tên miền.
- **Nhân đợt đo này bắt được một lỗi thật trong CHÍNH `congcu/lay_trang.py`:** `duong_wayback()` thiếu
  modifier `id_` nên nội dung RSS/XML có lúc trả về đúng trang phát lại của Wayback (giao diện JS, 0
  mục) thay vì byte gốc đã lưu — đã vá tại nguồn (thêm `id_` vào URL), nghiệm thu chéo trên 8 domain
  khác đang dùng wayback trong `bang-tra-web.json`: không domain nào mất rescue, chỉ nhẹ hơn (không
  dính banner Wayback). Ca test `ca_26` trong `congcu/test-lay-trang.py` canh đúng chỗ này.
- **CHỈ CẮM ĐƯỢC KHI MÁY CÓ `~/Claude/congcu`.** CI (GitHub Actions) checkout đúng repo này, không có
  thư mục dùng chung đó, nên `curl()` TỰ LÙI VỀ đúng logic cũ (1 lượt curl_cffi, hàm
  `_lay_bang_van_tay_chrome` giữ nguyên) — fail-open CÓ TIẾNG, in ra ở cuối `bao_nguon_hong()`
  (`🪜 Thang lấy trang bị chặn: KHÔNG có — máy thiếu …`). Không phải lỗ hổng: CI vốn đã đủ dùng plain
  curl_cffi cho hầu hết nguồn (chạy từ IP Mỹ).
- Sổ ghi vết `VET_NGUON["thang_cuu"]` (dict `{đường: [url,...]}`) tách riêng khỏi `cffi_va_duoc` — bậc
  nào KHÁC `curl_cffi` (wayback/thu_lai/pdf/api_rieng/relay_my) mới vào đây, in kèm tên bậc đã cứu.

**Đo thật 30/07/2026 — 108 nguồn, 3 cấu hình curl, rồi mở lại từng cái bằng trình duyệt:**

| Nhóm | Số | Nguồn | Lấy bằng |
|---|---|---|---|
| Bậc 1 đủ | 87/108 | phần lớn bảng RSS | curl |
| **Chặn vân tay TLS — bậc 2 cứu được** | **16** | Breaking Defense (30 item) · Naval Technology (10) · army.mil (45) · **13 trang Thượng viện** (12 uỷ ban + thông cáo chung) | `curl_cffi` |
| Chặn theo IP — chỉ CI | 3 | thediplomat.com (local 1/6 lượt) · census.gov (Cloudflare chặn cả Chrome) · occ.treas.gov (drop im lặng) | lô CI `ung-vien-ci.json` |
| **URL chết, nguồn còn sống** | 1 | Uỷ ban Tư pháp Hạ viện | đổi sang URL mới, curl trần chạy lại được |
| Chập chờn | 1 | af.mil | thử lại, đừng gạch tên |

⚠️ **Thêm header đầy đủ hay ép HTTP/1.1 KHÔNG cứu được nguồn nào** — đã đo cả 3 cấu hình × 108 nguồn,
số nguồn hỏng y hệt (21/108). Đừng mất công đi đường đó nữa: reset xảy ra ở **bước bắt tay TLS**, tức
TRƯỚC khi header kịp gửi (`thediplomat.com`: TCP nối được rồi `Connection reset by peer` sau **0,043
giây**). Hỏng trong dưới 1 giây không bao giờ là mạng chậm — đó là chữ ký của tường lửa ứng dụng.
⚠️ **403 KHÔNG phải lúc nào cũng lộ ra là rỗng hay ngắn.** Trang lỗi của Naval Technology dài **19.357
byte và mở đầu bằng `<?xml`** nên `items_of` parse ra 0 item mà không ném lỗi gì. Vì vậy `harvest.py`
dò theo **DẤU HIỆU trong thân** (`403 forbidden` · `access denied` · `attention required` · `just a
moment` · `request forbidden`), không dò theo cỡ.
⚠️ **Thiếu `curl_cffi` thì harvest vẫn chạy nhưng KÊU** (`⚠️ N nguồn bị chặn mà máy KHÔNG có curl_cffi`).
Fail-open có tiếng — im lặng ở đây là tạo đúng vùng câm mà bản vá này sinh ra để bịt.

**Đo lại về sau:** `python3 scripts/kiem_nguon.py` (nhóm trọng yếu, ~20 nguồn, mã thoát 1 khi có nguồn
hỏng) hoặc `--tat-ca`. Bộ test canh: `tests/test-kiem-nguon.py` (25 ca · `--tu-kiem` bắt 10/10 bản
hỏng — nhóm A-E đo bậc 2 cũ, nhóm F ca 21-25 đo nhánh CÓ thang qua `GiaLapThang`).

#### 📊 Kết quả dò TOÀN BỘ nguồn ở CẢ HAI môi trường (27/07/2026, `scripts/probe_sources.py`)
288 URL / 154 domain, dò từ máy Mac và từ GitHub runner (Mỹ), rồi so:
| | local (máy Huy) | CI (Mỹ) |
|---|---|---|
| RSS đọc được | 78 domain | 77 |
| HTML đọc được | 39 | **58** |
| 403 | 31 | **16** |

- **114 domain cả hai đọc được** — phần lớn bảng nguồn.
- **21 domain CHỈ CI đọc được** → local mất hẳn. Gồm **TOÀN BỘ uỷ ban THƯỢNG VIỆN** (armed-services,
  foreign, appropriations, intelligence, judiciary, banking, finance, budget, commerce, energy, hsgac,
  rules, agriculture, indian, jec, sbc + trang thông cáo chung) và census.gov, occ.treas.gov. Đây **đảo
  lại** ghi chú cũ "uỷ ban Thượng viện 403, chỉ WebSearch được" — sai vì chỉ đo ở local.
- **3 domain CHỈ local đọc được** (CI bị 403): `axios.com`, `flightglobal.com`, `rappler.com` → phiên CI
  sẽ hụt 3 nguồn này, bù bằng Google News/local.
- ~~**16 domain cả hai chịu**~~ → **CON SỐ NÀY SAI, xem mục đo lại ngay dưới.** Danh sách cũ:
  bls.gov, commerce.gov, defense.gov, dhs.gov, eda.gov, nsa.gov, ntia.gov, transportation.gov,
  usda.gov, senate.gov, và 6 trang quân chủng navy/marines/centcom/pacom/jcs/uscg.

#### 🔄 ĐO LẠI 30/07/2026 BẰNG CÔNG CỤ ĐÃ VÁ — bảng số trên dựng bằng curl TRẦN nên phóng đại "403"
Toàn bộ ảnh chụp 27/07 ở trên đo bằng `curl` trần, tức nó **không phân biệt được nguồn bị chặn THẬT
với nguồn chỉ bị chặn vì công cụ đo** (Akamai/Cloudflare cắt theo dấu vân tay TLS). Sau khi
`probe_sources.py` được vá để đi bậc 2 bằng `curl_cffi`, đo lại từ CI (run 30516868251, 287 URL):

| | CI 30/07 — curl trần | CI 30/07 — có bậc 2 |
|---|---|---|
| RSS | 77 | **82** |
| HTML | 173 | **195** |
| **403** | **31** | **6** |
| LỖI | 6 | 4 |

**27 URL chỉ đọc được nhờ vân tay TLS**, trong đó có cả 06 trang quân chủng ở dòng gạch trên. `403`
còn lại chỉ 03 domain: `commerce.gov`, `eda.gov`, `flightglobal.com`.
⛔ **Nhóm "cả hai chịu" nay chỉ còn phần `.gov` chưa đo lại từ local** — 06 trang quân chủng đã RỜI
nhóm này và vào bảng "🕸️ TRANG HTML QUÉT TRỰC TIẾP". Đừng đọc lại danh sách gạch ngang ở trên như
danh sách còn hiệu lực.

⚠️ **Đọc số liệu dò cẩn thận:** dò 288 URL bằng nhiều luồng dễ bị **rate-limit tạm** — lần này
`thehill.com` trả 429 và `thediplomat.com` trả 000 ở local dù bình thường vẫn chạy tốt. Thấy một nguồn
đang dùng được bỗng báo hỏng thì **kiểm lại lẻ một lần** trước khi kết luận, đừng gạch tên ngay.
Từ 30/07 script **tự làm việc này**: sau vòng đa luồng nó đo LẠI LẺ, TUẦN TỰ mọi nguồn bị chấm hỏng và
đánh dấu `da_thu_2_lan` — vòng lẻ ở CI 30/07 cứu được 0/10, tức 10 nguồn đó hỏng thật.
Dò lại về sau: `python3 scripts/probe_sources.py --json /tmp/probe-local.json` (local) và workflow
`probe-sources.yml` (CI, ghi `docs/probe-ci.json`). **Cả hai nơi đều cần `curl_cffi`** — thiếu thì
script vẫn chạy nhưng KÊU ra danh sách domain chưa kết luận được, đừng bỏ qua dòng đó.

## 🪖 Trang .mil — vì sao chẩn đoán 27/07 sai một nửa (đo lại 30/07/2026)

⛔ **Câu cũ "máy Mac không phân giải nổi DNS zone `.mil`" ĐÚNG VỚI `af.mil`, SAI VỚI `army.mil`.**
Đo lại 30/07: `socket.getaddrinfo('www.army.mil')` trả **118.69.17.187** (node Akamai đặt trong hạ tầng
FPT), TLS bắt tay xong xuôi, rồi server trả **403 Access Denied** — tức bị chặn **vân tay TLS**, không
phải DNS. Đi bằng `impersonate="chrome"` thì ra 200 và 45 item nội dung THẬT (đã đọc tận nơi: bài
"21st Theater Signal Brigade holds change of command ceremony", pubDate 29/07/2026).
- **`dig` NÓI DỐI ở đây, `getaddrinfo` mới là thứ ứng dụng dùng.** `dig www.army.mil` trả *"connection
  timed out; no servers could be reached"* (nó hỏi thẳng authority của zone `.mil`, vướng DNSSEC) trong
  khi resolver hệ thống trả IP bình thường. Chẩn đoán DNS bằng `dig` rồi kết luận "không phân giải được"
  là cách sinh ra ghi chú sai này. Kiểm bằng `python3 -c "import socket;print(socket.getaddrinfo(h,443))"`.
- **Đo đa luồng cho ra kết quả SAI ở đây.** Vòng dò 8 luồng chấm cả `af.mil` lẫn `army.mil` là `000`;
  đo lẻ tuần tự thì `af.mil` ra **200/20 item** còn `army.mil` ra **403**. Cùng bẫy đã ghi ở mục "Kết quả
  dò TOÀN BỘ nguồn": thấy nguồn đang dùng bỗng báo hỏng thì **kiểm lại lẻ** trước khi gạch tên.
- `af.mil` vẫn thuộc nhóm chập chờn (getaddrinfo lúc được lúc không) → cứ để trong bảng, `kiem_nguon.py`
  xếp nó vào nhóm VÀNG "chỉ CI lấy được ổn định", không kêu ĐỎ mỗi sáng.

🔄 **ĐẢO LẠI 30/07/2026 — câu cũ *"trang HTML của chúng 403 với cả CI lẫn local (WAF chặn IP
datacenter)"* là kết luận của một CÔNG CỤ ĐO SAI, không phải của các trang đó.** Cả 06 tên miền đều
trả **200 và thân sạch** khi đi bằng vân tay TLS Chrome, nên cả 06 nay nằm trong bảng
**"🕸️ TRANG HTML QUÉT TRỰC TIẾP"** và `harvest.py` quét chúng qua lớp `[HTML]`. Số đo CI 30/07
(run 30516868251): PACOM **228.361B** · Navy 114.720B · JCS 74.037B · USCG 68.712B · Marines 65.170B ·
CENTCOM 46.728B. Ở local, Navy (114.451B) và Marines (65.170B) cũng lấy được; 04 cái còn lại vướng
**DNS**, không vướng WAF — chi tiết và cách phân nhãn `cả hai`/`CI` ghi ở chính bảng đó.
- **Cơ chế gây vấp:** `probe_sources.py` chỉ gọi **curl trần**, mà curl trần bị Akamai cắt theo dấu
  vân tay TLS ⇒ nó chấm `403` ⇒ bảng ghi "403 cả hai nơi" ⇒ `harvest.py` bỏ nguồn. Không lỗi, không
  cảnh báo, và bảng trông như có căn cứ vì đúng là có số đo — số đo của công cụ sai. Cùng lớp với
  luật *"đừng chẩn đoán từ output do chính mình cắt"*: ở đây là output do chính công cụ của mình bóp.
- **Kèm theo, `probe_sources.py` còn có một nhãn CÂM TỪ NGÀY DỰNG:** nhãn `DNS` chỉ khớp khi stderr
  chứa `Could not resolve host`, nhưng script chạy `curl -s` — cờ đó triệt tiêu luôn thông báo lỗi.
  Bằng chứng: bản local 27/07 và bản CI 30/07 đều có **đúng 0 mục `DNS`** trên 287 URL, trong khi zone
  `.mil` thật sự không phân giải được ở local. Tên miền chết bị dồn vào nhãn `LỖI` chung với timeout —
  hai nguyên nhân khác hẳn nhau và chữa theo hai hướng khác nhau. Đã vá thành `-sS`.
- **DVIDS vẫn giữ** (`dvidshub.net/rss/all`) và feed `war.gov` vẫn giữ: chúng gom tin mọi quân chủng
  nên là lớp phủ rộng, còn 06 trang trên là nguồn tầng 1 theo từng bộ chỉ huy. Hai thứ bổ sung nhau,
  không thay nhau.

> 📄 **🔑 TRANG NÀO PHẢI LẤY BẰNG CÁCH NÀO — bảng tra (Huy chốt 30/07/2026)** → [`docs/nhat-ky-nguon.md`](docs/nhat-ky-nguon.md) — 4 bậc lấy trang (curl → curl_cffi → thang → WebSearch)


## 🕸️ Bảng TRANG HTML — lịch sử đo và hai lần đảo lại nhãn `CI`/`cả hai`

Huy nhắc đúng: *"không có RSS thì mày vẫn xem được mà"*. Kiểm lại 85 domain trong file nguồn chính thức
Mỹ: **42 mở được HTML bằng curl** (chỉ 34 chặn 403). `harvest.py` có lớp `[HTML]` quét thẳng trang danh
sách thông cáo — lấy link + tiêu đề + ngày (tìm trong khối HTML quanh mỗi link).
**Giá trị lớn nhất: toàn bộ uỷ ban HẠ VIỆN đều mở được**, mà đó chính là **nhóm 1** (điều trần + bỏ
phiếu) — nhóm luôn thiếu tin nhất. Thực tế lần chạy đầu bắt được "Chairman Rogers Applauds House Passage
of FY27 NDAA", "House Passes H.R. 9770", "Opening Statement at the FY27 NDAA Markup".


🔄 **ĐẢO LẠI 30/07/2026 — 13 trang THƯỢNG VIỆN chuyển từ `CI` sang `cả hai`.** Nhãn `CI` cũ dựa
trên phép đo bằng curl trần, mà curl trần thì bị chặn theo **vân tay TLS** chứ không phải theo IP: đã mở
đủ **13/13** trang bằng trình duyệt tại chính máy này, và `curl_cffi impersonate="chrome"` cũng trả 200
cho cả 13. Nay `harvest.py` tự đi bậc 2 nên local quét được luôn — đây là **nhóm 1 (điều trần + bỏ
phiếu)**, nhóm luôn thiếu tin nhất, nên phần chênh này đáng kể.
⚠️ Giữ `CI` cho `census.gov` và `occ.treas.gov`: hai trang này chặn **cả trình duyệt** tại máy local
(census trả trang Cloudflare *"Sorry, you have been blocked"*, occ drop im lặng hết 25 giây) — đó mới
đúng là chặn theo IP, và CI vẫn lấy được.

🔄 **ĐẢO LẠI LẦN HAI, 30/07/2026 — 06 TRANG QUÂN CHỦNG VÀO BẢNG. Trước đó chúng bị xếp "cả hai
chịu" và bị bỏ hoàn toàn.** Nguyên nhân gốc không nằm ở các trang đó mà ở **công cụ đo**:
`scripts/probe_sources.py` chỉ gọi **curl trần**, nên mọi trang chặn theo vân tay TLS đều bị nó chấm
`403` rồi ghi vào bảng thành nguồn chết. Vá công cụ (thêm bậc 2 `curl_cffi`) rồi đo lại từ CI, số
`403` tụt từ **31 xuống 6** và **27 nguồn** đọc được nhờ vân tay TLS — trong đó có cả 06 trang này.
Số đo CI 30/07 (run 30516868251): PACOM **228.361B** · JCS 74.037B · USCG 68.712B · CENTCOM 46.728B ·
Navy 114.720B · Marines 65.170B, tất cả 200 và thân không mang dấu hiệu chặn.
Giá trị: PACOM và Marines là nguồn **tầng 1** cho chủ đề 2 (Úc & Biển Đông) và chủ đề 5 (Pitch Black
Run) — hai chủ đề vẫn hay thiếu bài; CENTCOM là tầng 1 cho chủ đề 4 (Mỹ–Mali).

⚠️ **Vì sao Navy/Marines là `cả hai` mà PACOM/CENTCOM/JCS/USCG chỉ `CI`** — khác biệt nằm ở **DNS,
không phải ở WAF**: zone `.mil` đang lỗi DNSSEC nên `getaddrinfo` ở local trả `gaierror` cho
`pacom/centcom/jcs/news.uscg` (0/4 lượt), trong khi `navy.mil`/`marines.mil` vẫn phân giải được 4/4
(184.85.126.103 và 184.85.124.244, node Akamai trong hạ tầng FPT). Local đo được Navy **114.451B** và
Marines **65.170B** — riêng Marines khít từng byte với số đo CI, tức cùng một nội dung.
⚠️ **Nhánh DNS này CHẬP CHỜN theo thời điểm, đừng đọc nhãn `CI` thành "local vĩnh viễn không lấy
được".** Cùng lượt đo 30/07, `www.army.mil` cũng **0/4** dù bảng RSS ghi nó lấy được 43–45 item cùng
ngày; và một số đo trước đó trong ngày lấy được `pacom.mil` **228.363B** ngay tại local. Nhãn `CI` ở
đây là **hướng lệch an toàn**: harvest local bỏ qua chúng nên không tốn lượt curl để nhận `gaierror`,
còn CI thì luôn lấy được. DNS zone `.mil` khoẻ lại thì nâng lên `cả hai`, và phép đo để quyết là
`getaddrinfo`, không phải `dig`.


⚠️ **THÊM TRANG VÀO BẢNG CHƯA CHẮC LÀ RA TIN — phải đếm LINK, không chỉ xem trang trả 200**
(đúc 30/07/2026, bắt được ngay trong lượt thêm 06 trang quân chủng). `marines.mil` trả 200 và
65.170 byte, nhưng lớp `[HTML]` lấy ra **0 link bài trên 10 link có thật**: thẻ `<a>` của CMS
**ArticleCS** (DoD dùng cho mọi trang quân chủng) bọc cả ngày + tiêu đề + **đoạn tóm tắt**, nên text
gộp dài **268–418 ký tự** và bị trần `len(title) > 200` loại sạch. Hỏng câm kiểu tệ nhất: nguồn nằm
trong bảng, trang trả 200, mà nó không bao giờ đóng góp một ứng viên nào — nhìn đâu cũng tưởng đang chạy.
- **Đã vá:** khi text thẻ `<a>` không đạt khuôn 25–200 ký tự, `harvest_html` lấy tiêu đề từ
  **`aria-label`**, rồi tới **`<h4 class="title">`**. Một bản vá phủ cả 06 trang quân chủng vì chúng
  dùng chung CMS. Đo sau vá: Marines **0 → 10 link, 8 khớp chủ đề** (MV-22B Osprey · Counter Drone ·
  ODIN Reporting System); nhóm uỷ ban Hạ viện **không đổi** (15/11/1 link trước và sau).
- **Hướng lệch có chủ ý:** không có nguồn tiêu đề sạch nào thì **BỎ bài**, tuyệt đối không nạp cả cục
  text lẫn tóm tắt làm `title` — ca 13 của bộ test canh đúng chiều nới tay này.
