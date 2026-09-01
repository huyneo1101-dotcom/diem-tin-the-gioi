# Điểm Tin Thế Giới — quy tắc quét tin

Trang tin tĩnh (PWA) tiếng Việt, deploy tự động lên GitHub Pages khi push vào `main`.

⛔ **COMMIT DO ACTIONS ĐẨY KHÔNG TỰ DỰNG LẠI TRANG — đã vá 21/08/2026, đừng gỡ.** GitHub chặn
`GITHUB_TOKEN` kích hoạt workflow khác (chống vòng lặp), nên mọi commit `Cap nhat ban tin` của
`claude-scan-ci` **không** chạm tới `on: push` của `pages.yml`; trang chỉ được dựng lại khi máy
Mac tình cờ đẩy một commit sau đó. Sáng 21/08 không có commit local nào ⇒ bản tin 04:17 nạp đủ,
email đi đủ, sổ ghi đủ, canary im lặng, mà web vẫn phục vụ bản 01:24 — **hỏng mà không phát ra
tiếng nào**. Hai lớp vá: (i) `pages.yml` thêm nhánh `workflow_run` (nghe theo WORKFLOW nên không
dính rào) kèm `checkout ref: main` (bỏ dòng này là dựng lại đúng bản cũ, vì `workflow_run` mang
SHA lúc workflow gốc khởi động); (ii) `canary.py::kiem_web()` đo **bản người dùng đang thấy** —
sha1 kiểu git blob của `index.html` trên github.io so với bản trên `main`, lệch thì nhắn Telegram.
Bộ canh: `tests/test-canary-web-lech.py` — **10 ca (03 ca PHẢI KÊU) · `--tu-kiem` bắt 5/5 bản
hỏng**, đã nạp `BO_TEST` của `HeThong/khoe.py`. Dựng lại tay: `gh workflow run pages.yml`.

⛔ **`workflow_run` KHÔNG ĂN VỚI `claude-web-scan.yml` — vá 26/08/2026, đừng gỡ dòng kích
thẳng.** Đo `gh api .../pages.yml/runs` nhiều ngày: dựng lại qua `workflow_run` chỉ khớp giờ
`sync-baomoi`/`sync-preferences`, chưa từng khớp giờ phiên quét tin dù có tên trong danh sách
nghe — web đứng bản cũ tới khi workflow khác tình cờ chạy qua. Vá: `claude-web-scan.yml` (bước
"Kích email/push/morning") gọi thêm `gh workflow run pages.yml --ref main`, cùng cơ chế
`actions: write` đã dùng cho `notify-email.yml`. `workflow_run` giữ làm lưới dự phòng.

⛔ **TRANG ĐẨY LÊN PAGES LÀ BẢN ĐÃ CẮT — `index.html` TRONG REPO VẪN ĐỦ KHO, ĐỪNG "DỌN".**
Từ 21/08/2026 `pages.yml` chạy `python3 scripts/cat_nhe_trang.py --tai-cho` ngay trước
`upload-pages-artifact`: index.html còn **lát đầu** (357.088 byte thô / 108.709 nén, bớt **80%**
so với 1.719.986 / 486.042), toàn bộ kho ra `data/kho.json` (1.515.777 byte) và trang tự nạp
bằng `loadKho()` sau khi đã hiện chữ. Lát đầu giữ 45 tin Mỹ · 30 tin thế giới · 15 tin X · 29
cuộc tập trận (bỏ `concepts`/`background`/`backgroundDoc`, giữ 01 item mới nhất mỗi cuộc); cà
phê, bản tuần, ngoại giao, tin bị loại để rỗng. Đo bằng `--kiem`.
- **Bước cắt CHỈ chạy trong runner, KHÔNG commit gì.** `main` giữ index.html đủ dữ liệu để 21
  script Python ghi vào như cũ — đó là lý do không phải sửa `add_news.py`, `harvest.py`, …
- ⛔ **CẤM chạy `--tai-cho` trên máy Mac rồi commit.** Bản cụt mất kho mà mọi script vẫn ghi vào
  đấy như thường, không lệnh nào báo lỗi. Hai rào: `.gitignore` chặn `/data/kho.json`, và ca 01
  của bộ test bắt cờ `_nhe` trong index.html của repo.
- ⛔ **`analyses` TUYỆT ĐỐI không vào `kho.json`.** Bài think-tank có kho riêng
  (`data/analyses.json`, tách 30/07/2026); hai lời gọi fetch chạy song song nên ghi đè là mục
  🏛️ Think-tank trống mà không có lỗi nào hiện ra. Chặn ở cả hai đầu: `KHONG_TACH` trong
  `cat_nhe_trang.py` và `if(k!=='analyses')` trong `loadKho()`.
- ⚠️ **`canary.py::kiem_web()` nay so bản web với bản DỰNG LẠI** (`ban_mong_doi()` gọi chính
  `cat_nhe()`), không so bytes thô của repo nữa — bỏ bước dựng khỏi `pages.yml` là canary kêu
  lệch **mọi ca**, kêu oan vài lần là thôi đọc.
- ⛔ **`sw.js` phải `ignoreSearch` cho request CÙNG GỐC — đừng gỡ.** `loadKho()` và
  `loadAnalyses()` gắn `?t=<mốc hiện tại>` để né cache, mà `caches.match` mặc định so cả chuỗi
  truy vấn ⇒ bản precache **không bao giờ khớp**, hàm rơi xuống trả `index.html`, `r.json()` ném
  lỗi và `catch` nuốt gọn. Đo 21/08/2026 trên bản đang chạy: `match('data/kho.json?t=999999')`
  trả undefined, thêm `ignoreSearch` thì trúng — tức precache offline đã **vô tác dụng từ
  30/07/2026**, mở offline mục 🏛️ Think-tank vẫn trống dù sw.js khai precache nó. Chỉ áp cho
  cùng gốc: chuỗi truy vấn của Supabase (`?select=cid,tags`) MANG NGHĨA.
- Bộ canh: `tests/test-cat-nhe-trang.py` — **17 ca · `--tu-kiem` bắt 20/20 bản hỏng**, đã nạp
  `BO_TEST` của `HeThong/khoe.py`.
- ⚖️ **Phép cân trang: `HeThong/khoe.py::trang_diemtin_phinh()`** (nạp 21/08/2026). Kích thước
  `index.html` trên đĩa KHÔNG nói gì về thứ người đọc tải, nên phép đo dựng lại đúng bản đã
  cắt rồi cân byte gzip của **lát đầu**: hiện **109.127 / trần `TRAN_TRANG_DT_NEN` = 125.000**.
  Vượt trần ⇒ VÀNG; **bước cắt mất tác dụng ⇒ ĐỎ** — `cat_nhe()` trượt vẫn trả HTML hợp lệ nên
  `pages.yml` vẫn xanh và trang lại nặng 1,7 MB, không dấu hiệu nào. Trần là **ratchet, chỉ hạ**:
  nới lên quá 25% so với số đo hiện tại thì chính phép đo kêu VÀNG. 05 ca trong `khoe.py --tu-kiem`.
  ⚠️ KHÁC `canary.kiem_web()`, đừng gộp: canary hỏi *bản trên mạng có khớp bản dựng không*,
  phép cân này hỏi *bản dựng có còn gọn không*.

⛔ **NGÀY CỦA TIN LÀ NGÀY ĐĂNG THẬT, ĐO BẰNG CÁCH MỞ BÀI — vá 25/08/2026, đừng gỡ.**
`check_date_window` chỉ đối chiếu trường `date` trong JSON của lô với ngày batch và với hôm
nay, mà cả hai vế đều là con số **do chính agent viết ra**: khai `date` bằng ngày quét là lô
đi qua cổng, dù bài đăng từ bao giờ. Đo thật 25/08 bằng cách mở lại 334 bài đã nạp và đọc
metadata ngày: lô 15-24/08 có **03/153 bài** ngoài khung (lệch 19 · 12 · 07 ngày), lô đối
chứng 10-31/07 có **06/164 bài**, nặng nhất là bài South China Morning Post đăng **21/12/2024**
mang `date` 29/07/2026, lệch 585 ngày. Không phải bệnh của một phiên hay một model: hai lô
cách nhau một tháng cho cùng tỷ lệ (2,0% và 3,7%), tức lỗ này mở suốt từ đầu.
- **Cổng mới `scripts/ngay_that.py`**, gọi trong `add_news.py::main` ngay sau các `validate_*`:
  mở từng `sourceUrl` (đi bằng `harvest.curl`, 08 bài song song), đọc **metadata có cấu trúc**
  theo thứ tự `datePublished` → `article:published_time` → `<time datetime>` →
  `citation_publication_date`, rồi so với trần `tran_ngay(category)`.
- ⛔ **KHÔNG quét ngày trong văn bản tự do.** Bài quân sự nào cũng dày đặc ngày lịch sử; phép
  bắt ngày trôi nổi từng gán bài 2026 thành 06/06/1944 và loại nhầm 46 bài (QuetThinkTank
  29/07/2026). Ca 10 của bộ test canh đúng điều này.
- ⛔ **TRANG KHÔNG IN NGÀY THÌ BỎ TIN — chỉ thị Huy 25/08/2026, nguyên văn *"trang không ghi
  ngày thì bỏ đi"*.** Không in ngày ở đâu cả thì không có cách nào biết bài cũ hay mới. Đo
  trước khi siết: 20/181 bài lô tháng 8 và 32/200 bài lô tháng 7 rơi vào nhóm này (11% và 16%),
  nguồn hay gặp là DVIDS · PACOM · war.gov · Xinhua · Al Jazeera.
- ⚠ **Nhưng TRANG KHÔNG MỞ ĐƯỢC thì vẫn GIỮ**, kèm dòng `⚠ NGÀY THẬT`. Chặn ở nhánh này là để
  đường truyền của máy chạy quyết định bản tin có tin hay không, và nguồn nào trả 403 thì mất
  trắng. Lằn ranh đo bằng thẻ `<title>`: CNN và CNBC tải về 300 KB **không có nổi `<title>`**
  (trang dựng bằng JavaScript hoặc bị chặn), trong khi DVIDS/PACOM/war.gov có `<title>` đúng
  tên bài — nhóm sau mới thật sự là "trang không in ngày". Bỏ lằn ranh này là loại oan theo
  chất lượng mạng, ca 14 của bộ test canh đúng chỗ đó.
- **Thêm mẫu cho nguồn không có metadata chuẩn thay vì chịu mất nguồn:** DVIDS in ngày trong
  bảng `Date Posted: 08.22.2026` (neo vào NHÃN, không lấy `Date Taken` — đó là ngày chụp ảnh,
  có thể trước ngày đăng hàng tuần). Nguồn nào bị loại nhiều thì soi HTML tìm neo tương tự rồi
  bổ sung vào `doc_ngay`, đừng nới trần ngày.
- **Đường thoát hợp lệ khi metadata nguồn ghi sai:** `--bo-cong-ngay-that="lý do"`, lý do bắt
  buộc và được in ra.
- **Bộ canh:** `tests/test-cong-ngay-that.py` — **15 ca (07 PHẢI CHẶN · 03 ca đầu-cuối) ·
  `--tu-kiem` bắt 9/9 bản hỏng**, chạy offline qua seam `NGAYTHAT_KHO_GIA`, đã nạp `BO_TEST`
  của `HeThong/khoe.py`. Nghiệm thu qua mạng thật 25/08: lô mang đúng URL bài SCMP 2024 bị
  chặn với thông điệp `bài đăng THẬT ngày 2024-12-21 (đọc bằng datePublished)`.

## 🗺️ LUẬT ĐÃ XẺ RA 07 FILE — mở đúng file trước khi sửa (xẻ 25/08/2026)

File này là **bản thi hành**: chỉ giữ luật phải-làm, đường dẫn, ngưỡng số, và bảng nguồn mà máy đọc.
Cơ chế gây vấp, nhật ký vá và số đo từng đợt nằm ở `docs/luat/` — **xẻ ra nguyên văn, không cắt chữ
nào**. Trước khi sửa một mảng thì mở file của mảng đó, đừng sửa theo trí nhớ.

| Việc đang làm | Mở file | Luật nóng nhất của file đó |
|---|---|---|
| Phạm vi quét, chủ đề, khung ngày, kiến trúc agent, khoá phiên, guardrail nạp tin | [`docs/luat/pham-vi-quet.md`](docs/luat/pham-vi-quet.md) | Tin không tự neo được vào chủ đề thì BỎ, cấm dồn vào mục "Úc & Biển Đông"; phiên test hạ tầng phải khai `DIEMTIN_PHIEN_TEST=1` |
| Khâu gửi: file Word, sổ đã gửi, cổng bắn notify, email | [`docs/luat/gui-ban-tin.md`](docs/luat/gui-ban-tin.md) | **FORM .docx bám mẫu cơ quan `ĐTN_M_01.9.2026.docx` (01/09/2026): 04 mục `(N) …`, mục 3 chia 03 tiểu mục, tin mở bằng `Ngày d.M.yyyy,`, link CÙNG đoạn, khổ A4 lề 1,0"**; email đã tắt (`GUI_EMAIL='0'`) nên `.docx` là kênh DUY NHẤT mang nội dung; bản tối phải bỏ tin ca sáng cùng ngày, bản sáng phải GỘP tin ca tối hôm qua (26/08/2026) |
| Telegram: gửi bản tin, canary, bot hỏi–đáp, đường nhận file của Jay Lâm | [`docs/luat/telegram.md`](docs/luat/telegram.md) | Thiếu secret Telegram là job ĐỎ, cấm thoát êm; canary chỉ nhắn cho Huy; token để NGOÀI repo (`/Users/Huy/Claude/.tg-bot.json`, chmod 600) |
| Thêm hoặc sửa cổng kiểm, chạy bộ test | [`docs/luat/cong-kiem.md`](docs/luat/cong-kiem.md) | Test xanh chưa đủ — phải chạy `--tu-kiem` chứng minh bắt được bản hỏng; **sửa chính `CLAUDE.md` cũng phải chạy test** vì file này LÀ cấu hình |
| Nạp tin, tập trận, sự kiện ngoại giao vào kho | [`docs/luat/kho-du-lieu.md`](docs/luat/kho-du-lieu.md) | Sửa `dates`/`status` của cuộc đã nạp phải đi bằng `scripts/sua_thong_tin_tap_tran.py`, cấm sửa tay và cấm bịa ngày kết thúc |
| Nguồn think-tank, kho `analyses`, cân đối khu vực, dò feed còn thiếu | [`docs/luat/think-tank.md`](docs/luat/think-tank.md) | `DATA.analyses` trong `index.html` phải LUÔN RỖNG (kho thật ở `data/analyses.json`); feed sống và feed chết cùng trả mã 200, phải đọc `pubDate` mới phân biệt |
| Log, tự phục hồi, Báo Mới, cổng bài được 👍, Google Drive, tab Cà phê | [`docs/luat/van-hanh.md`](docs/luat/van-hanh.md) | Tin Báo Mới phải truy ngược về nguồn gốc trước khi nạp |

⚠️ **Thêm luật mới thì thêm vào file của mảng, đừng thêm vào đây.** Trần chống phình của file này nằm ở
`HeThong/khoe.py::TRAN_LUAT_MANG` — nó là ratchet, chỉ hạ theo mỗi lần nén, cấm nới lên cho vừa file
đã phình.

## ⏱️ LỊCH VÀ PHẠM VI QUÉT — bản rút gọn

📅 **MỌI SỐ GIỜ Ở ĐÂY LÀ BẢN CHÉP LẠI — nguồn sự thật là [`docs/LICH.md`](docs/LICH.md)** (sinh từ
chính dòng `cron:`). Lệch nhau thì `LICH.md` thắng. Canh bằng `python3 scripts/kiem_lich.py --kiem`;
sửa cron thì chạy `--sinh` rồi soi lại mọi chỗ chép.

**Hai phiên mỗi ngày, cùng 5 chủ đề.** Mốc chính chạy trên GitHub Actions `claude-web-scan.yml` (giờ
VN: tối **20:47** + lớp vét 21:47 · sáng sớm **03:47/04:47**) — máy Mac tắt vẫn ra bản tin; scheduled
task local là **dự phòng** cho cả hai phiên (tối `web-scan-diem-tin-toi` 21:15 · sáng
`web-scan-diem-tin` 04:30/05:30). CI đã xong hoặc đang chạy thì local SKIP êm qua khoá `state.py`.

⏰ **Hạn chót bản tin tối là 22:00** nên phiên tối tính ngược từ mốc cuối: quá **21:45** chưa xong thì
chốt lô đang có, commit ngay, phần thiếu ghi `logs/scan-gaps.json`. Không dời hai lớp đầu trễ hơn,
không biến lớp vét 21:47 thành mốc chính.

| # | Chủ đề | Nạp vào | Khung ngày |
|---|---|---|---|
| 1 | **Nội bộ Mỹ** — hạng 1: **toàn bộ điều trần + toàn bộ kết quả bỏ phiếu**; hạng 2 (ngang hàng nhau, chỉ lấy khi hạng 1 đã cạn): sáng kiến và chiến lược chính quyền trên kênh chính thống của các bộ · biểu tình · kinh tế Mỹ và động thái bộ sậu · bầu cử | `usNews`, cat `Chính trị` (nhóm kinh tế có thể là `Kinh tế`) | hôm nay + hôm qua |
| 2 | **Úc & Biển Đông** — mọi tin quân sự liên quan tới Úc, cả ba quân chủng; hoạt động quân sự và chiến tranh vùng xám ở Biển Đông; các nước ven vùng biển đó | `worldNews` | hôm nay + hôm qua |
| 3 | **CNQS Mỹ** — khí tài, hệ thống, hợp đồng | `usNews`, cat `Công nghệ quân sự` | **lùi tới 3 ngày** |
| 4 | **Mỹ – Mali** — Mỹ cân nhắc hoặc không kích JNIM ở Sahel | `usNews`, dossier `🟤 Mỹ – Mali` | hôm nay + hôm qua |
| 5 | **Tập trận đang diễn ra** | `exerciseUpdates`, `name` khớp đúng tên trong `DATA.exercises` | hôm nay + hôm qua |

- ⛔ **"Nới 48h" = HÔM NAY + HÔM QUA, không phải lùi 2 ngày lịch** (chỉ thị Huy 27/07/2026). Tin cũ hơn
  thì bỏ, ghi `logs/loai-tin.md` kèm lý do trong `scan-gaps.json`, thà chủ đề về 0. `add_news.py` kiểm
  ngày hai lớp nên neo lùi `date` của lô không lách được.
- ⛔ **Khung 3 ngày của chủ đề 3 khai ở hai nơi** — `MAX_AGE_DAYS_CNQS` trong `add_news.py` (áp theo
  **category**) và `CNQS_LOOKBACK_DAYS` trong `harvest.py`. Sửa một bên phải sửa bên kia.
- ⛔ **Chủ đề 5 sinh ĐỘNG từ `DATA.exercises`**, nhãn là hằng `topics.CHU_DE_TAP_TRAN = "Tập trận"`;
  đổi kỳ tập trận **không phải sửa dòng mã nào**. Thêm chủ đề vào `GNEWS_QUERIES` thì phải khai luôn
  vào `harvest.py::UU_TIEN_CHU_DE`, quên khai là chủ đề đó bị chủ đề rộng hơn ăn mất URL, hỏng câm.
- **Bỏ khỏi phạm vi:** kinh tế chung, ngoại giao chung, `xNews`, các vùng thế giới khác, tạo mới
  `dipEvents`, và sàn cứng 15+15. **Báo Mới** vẫn quét nhưng chỉ giữ bài hợp 5 chủ đề trên.
- **Quy trình vận hành đầy đủ của một phiên quét: `.claude/skills/quet-tin/SKILL.md`.** Đầy đủ luật
  phạm vi, nhóm ưu tiên nội bộ Mỹ, bảng neo Úc & Biển Đông và nhật ký vá: `docs/luat/pham-vi-quet.md`.

## ✅ THANG XÁC MINH — bao nhiêu nguồn là ĐỦ để nạp một tin (chốt 27/07/2026)
Trước đây chỉ có luật cụt "không chắc link thì bỏ", nên thực tế xử lý lệch nhau: cùng ngày 27/07 tao
**bỏ** tin hợp đồng Space Force 400,4 triệu USD (vì search 6 trang chuyên ngành không ra) nhưng lại
**nạp** tin tàu 015-Trần Hưng Đạo (link gốc qdnd.vn trả 302 với mọi công cụ). Huy hỏi đúng chỗ: vấn đề
không phải "thiếu nguồn xác nhận" mà là **thiếu thang**. Thang chuẩn:

| Nguồn của tin | Cần xác nhận thêm? |
|---|---|
| **Tầng 1 — chính thức** (war.gov/defense.gov, navy.mil, state.gov, whitehouse.gov, defence.gov.au, qdnd.vn, mofa…) — đọc được nội dung | **KHÔNG.** Thông cáo chính thức TỰ NÓ là xác nhận. Đừng bắt nó phải được báo chí đưa lại mới cho nạp |
| **Wire** (Reuters, AP, AFP, Bloomberg) hoặc **báo chuyên ngành lớn** (Defense News, Breaking Defense, Defense One, Naval News, SpaceNews, DefenseScoop, Janes…) | **KHÔNG**, một nguồn là đủ |
| **Báo phổ thông uy tín** (BBC, Al Jazeera, SCMP, Nikkei, The Hill, CBS…) | **KHÔNG**, một nguồn là đủ |
| **Trang TỔNG HỢP / DẪN LẠI** (Báo Mới, RealClear*, Investing.com, Yahoo/AOL, MSN, aggregator vô danh) | **CÓ — bắt buộc truy về BÀI GỐC.** Ra gốc thì dùng gốc; không ra gốc thì cần **2 nguồn độc lập** cùng khẳng định, không thì BỎ |
| **Nguồn không mở được bằng tool** (403/302 loop/paywall) | Không phải lý do bỏ nếu **nội dung** đã được xác nhận qua đường khác (WebSearch snippet, nguồn thứ hai). **Dính PAYWALL thì thử `python3 /Users/Huy/Claude/congcu/lay_trang.py --duong=darkread <url>` TRƯỚC khi bỏ** (chỉ thị Huy 05/08/2026) — chi tiết và giới hạn ở `.claude/skills/quet-tin/SKILL.md` mục THANG XÁC MINH. Nếu KHÔNG xác nhận được chữ nào thì BỎ — đó là ca The Africa Report 25/07 |
| **Truyền thông nhà nước độc tài** (Xinhua, TASS, Global Times, KCNA…) | Chỉ dùng cho phát ngôn CỦA CHÍNH HỌ; sự kiện tranh chấp/thương vong phải có nguồn thứ hai |

**Nơi xác nhận HỢP ĐỒNG QUỐC PHÒNG** (mảng hay phải kiểm chéo nhất — danh sách cũ chỉ có 6 trang, quá
hẹp): trước hết là **trang Contracts chính thức** (`war.gov/News/Contracts/`), rồi tới **thông cáo của
chính nhà thầu** (lockheedmartin.com, gd.com, rtx.com, northropgrumman.com — họ luôn ra thông cáo khi
trúng hợp đồng lớn), rồi **báo chuyên hợp đồng**: GovConWire, ExecutiveGov, Defense Daily, Inside
Defense, Seapower (Navy League), National Defense Magazine, Shephard, Janes — cộng với 6 trang cũ
(SpaceNews, DefenseScoop, Breaking Defense, Defense News, C4ISRNet, Air & Space Forces).

⚠️ **Nhiều hợp đồng trong CÙNG một trang Contracts** thì `add_news.py` chặn vì trùng URL — đúng thiết
kế. Cách xử lý: **gộp thành MỘT tin** ("Lầu Năm Góc công bố loạt hợp đồng ngày DD/MM: …, …"), hoặc lấy
tin từ thông cáo riêng của nhà thầu để có URL khác. Đừng bỏ tin chỉ vì đụng guardrail này.

## 🎯 BẢNG ĐỘ GẦN NGUỒN — cổng chặn tin kênh tuyên truyền đứng một mình (dựng 06/08/2026)

**Dòng khai hiện hành — SỬA ĐÚNG DÒNG NÀY khi bảng đổi, đừng sửa phần nhật ký phía dưới:**
bảng độ gần đang canh **109 hãng**, dấu vân tay `1fe3b2dc1b92a8b97f03e106208c98c3857d81ee`
(độ gần 1: 18 · 2: 44 · 3: 41 · 4: 6).

⚠️ **CHỮ "ĐỘ GẦN" LÀ CỐ Ý, KHÔNG PHẢI "TẦNG".** Mục *"Nguồn theo 3 tầng"* ngay bên dưới xếp
nguồn theo **công dụng** — ở đó tầng 3 là viện nghiên cứu, dùng để neo nhận định, tức vị trí
CAO. Bảng này xếp theo **độ gần sự việc** — ở đây mức 3 là trang tổng hợp/dẫn lại, tức vị trí
THẤP. CSIS mang số 3 ở cả hai bảng với hai ý nghĩa trái ngược; Reuters là "báo chí dưới cùng"
ở bảng cũ nhưng mức 2 ở bảng này. Giữ chung một chữ là gài sẵn một chỗ đọc nhầm mà không tool
nào bắt được, nên Huy chốt 06/08/2026: bảng mới gọi là **độ gần**, bảng cũ giữ nguyên tên.

| Độ gần | Nghĩa |
|---|---|
| 1 | nguồn gốc chính thức — chính bên tạo ra sự việc, hoặc người quan sát trực tiếp |
| 2 | hãng tin có phóng viên tại chỗ |
| 3 | trang tổng hợp / dẫn lại |
| 4 | kênh tuyên truyền |

**VÌ SAO CÓ BẢNG NÀY.** Mục THANG XÁC MINH phía trên đã có sẵn dòng luật *"truyền thông nhà
nước độc tài: chỉ dùng cho phát ngôn của chính họ; sự kiện tranh chấp/thương vong phải có
nguồn thứ hai"* từ 27/07/2026. Luật đúng và đủ — thứ thiếu là **chỗ tra**: nó gọi tên LOẠI
nguồn chứ không gọi tên HÃNG, nên mỗi lượt quét lại phải xếp loại bằng phán đoán (*"Zona
Militar thuộc loại nào?"*, *"The Epoch Times thì sao?"*), phán đoán đó không được ghi lại ở
đâu, và không cổng nào đo được nó đã xảy ra hay chưa. Bảng biến phán đoán ấy thành phép tra.

**Cắm ở đâu:** `scripts/do_gan.py` (một hàm kiểm tra duy nhất, `add_news.py` GỌI — cấm chép
logic sang nơi khác) · bảng `data/do-gan-nguon.json`.

**HAI ĐƯỜNG QUA CỔNG cho tin độ gần 4, cố ý là hai chứ không phải một:**
- `"nguonThuHai": "<url>"` — phải khác **tên miền gốc** với `sourceUrl`. Dùng khi tin là sự
  kiện tranh chấp/thương vong, hoặc nói về bên thứ ba.
- `"phatNgonCuaChinhHo": true` — dùng khi tin là phát ngôn/hành động do CHÍNH bên đó công bố.

⚠️ **Đường thứ hai BẮT BUỘC phải có, nếu không cổng chặn oan đúng loại tin mà luật gốc cho
phép.** Đo trên 497 tin đang sống ngày 06/08: cổng chạm 03 tin, thì 02 tin là Trung Quốc
công bố việc của chính Trung Quốc (Global Times) — hợp lệ theo luật gốc — chỉ 01 tin (The
Epoch Times viết về cam kết của Tổng thống Philippines) mới là ca luật gốc nhắm tới. Cổng nào
ở luồng bình thường luôn phải mở cờ mới qua được là cổng chết: nó dạy người dùng phản xạ mở
cờ, mà mở cờ quen tay thì mọi cổng còn lại mất giá theo. Đường thứ hai không phải lỗ hổng —
nó là một lời khai được GHI vào tin, tức đúng thứ trước giờ vẫn xảy ra trong đầu người quét
mà không để lại dấu vết nào.

**Phạm vi cố ý hẹp:** chỉ chặn `worldNews` · `usNews` · `baomoiNews` · items của sự kiện.
`xNews` chỉ **cảnh báo**, không chặn — luồng đó được trình bày trên web đúng như bản chất của
nó (tiếng nói mạng xã hội chưa thẩm định), nên bắt nó có nguồn thứ hai là đổi bản chất luồng
chứ không phải vá một lỗ. Nguồn **chưa có trong bảng cũng không bị chặn**: đo 06/08 thì 39%
số tin đang sống mang tên nguồn chưa xếp loại, chặn cả nhóm đó là chặn oan hàng loạt.

**Cờ mở cổng — CÓ THẬT, được đọc, và để lại dấu:**
```bash
python3 scripts/add_news.py /tmp/new_items.json --bo-cong-do-gan="lý do cụ thể"
```

⚠️ **BẢNG TRONG REPO LÀ BẢN CHÉP — bản gốc ở `App/RenPhanTich/du-lieu/nguon.json`.** Buộc
phải chép vì `add_news.py` chạy **cả trên máy chạy của GitHub Actions**
(`import-news-from-drive.yml`, `claude-web-scan.yml`), nơi `/Users/Huy/Claude/App/` không tồn
tại — trỏ đường dẫn tuyệt đối là cổng chết câm trên CI: không tra được thì không chặn được,
và không có lỗi nào phát ra. Đã có hai bản thì phải có phép đo canh cho chúng đừng tách nhánh.
**Sửa bảng thì sửa BẢN GỐC rồi chạy `python3 scripts/dong_bo_do_gan.py --sinh`**, đừng sửa tay
bản trong repo (`--kiem` tính lại dấu vân tay từ chính nội dung nên sửa tay là lộ ngay).

**Chuỗi canh — 03 mắt, mỗi mắt một phép đo khác nhau:**
| Mắt | Đo gì | Chạy ở đâu |
|---|---|---|
| `scripts/dong_bo_do_gan.py --kiem` | bản gốc ↔ bản chép trong repo | `khoe.py` mỗi sáng |
| `tests/test-cong-do-gan.py --tu-kiem` | bản chép ↔ hành vi cổng (16 ca · 10 bản hỏng) | `khoe.py` mỗi sáng |
| `HeThong/dong-bo-luat.py --kiem` | bản chép ↔ dòng khai hiện hành ở đầu mục này | `khoe.py` lớp 8 |

**Số đo lúc dựng (06/08/2026):** bảng khớp 61% số tin đang sống (388/638) — tin thế giới 65%,
tin Mỹ 66%, tin bị loại 34%, mạng xã hội 54%; kho bài think-tank khớp 87% (443/506). Phần hụt
lớn nhất là mục Bị loại: 56/86 tin đến từ báo trong nước qua Báo Mới, chưa có tên nào trong
bảng. Độ gần 4 xuất hiện 07 lần trong dữ liệu sống (Global Times ×2, The Epoch Times ×1, cộng
04 tài khoản mạng xã hội) — tức cổng có việc thật để làm.

## Nguồn theo 3 tầng (chuẩn báo cáo/INTREP — áp dụng từ 11/07/2026)
**Nguyên tắc:** dữ kiện/sự kiện neo vào nguồn CHÍNH THỨC (tầng 1); số liệu kinh tế/quân sự neo vào nguồn DỮ LIỆU (tầng 2); kết luận/nhận định chiến lược (field `significance` + phần Phân tích) neo vào VIỆN NGHIÊN CỨU (tầng 3). Báo chí/hãng tin (dưới cùng) dùng để PHÁT HIỆN sự kiện sớm, KHÔNG tự mình làm chỗ dựa cho kết luận — luôn đối chiếu. Tin quân sự chỉ có 1 nguồn (Army Recognition/Naval News/blog) → kiểm chứng thêm bằng thông cáo bộ quốc phòng/ảnh chính thức/Janes/SIPRI. Khi tin bắt nguồn từ thông báo chính thức, link THẲNG tới nguồn gốc tầng 1 thay vì báo dẫn lại.

### Tầng 1 — Nguồn chính thức (xác minh sự kiện; ưu tiên cao nhất)
| Nhóm | Nguồn chính thức | Handle X |
|---|---|---|
| Đa phương | NATO (nato.int), Liên Hợp Quốc (news.un.org, UN Meetings Coverage, Hội đồng Bảo an), EU/Hội đồng châu Âu (consilium.europa.eu), EEAS (eeas.europa.eu), ASEAN (asean.org) | @NATO, @UN, @EUCouncil, @ASEAN |
| Mỹ | Nhà Trắng (whitehouse.gov), Bộ Quốc phòng (defense.gov), Bộ Ngoại giao (state.gov), CENTCOM (centcom.mil), Lực lượng Không gian/Hải quân/Lục quân, Fed (federalreserve.gov), Quốc hội/CRS | @WhiteHouse, @DeptofDefense, @StateDept, @CENTCOM, @SecRubio |
| QP/NG các nước | Bộ QP Anh (gov.uk), Australia (defence.gov.au), Nhật (mod.go.jp), Hàn (mnd.go.kr), Ấn Độ, Philippines, TQ (mod.gov.cn), Nga; Bộ Ngoại giao (mofa.go.jp...); Phủ TT Ukraine (president.gov.ua) | @ZelenskyyUa |
| Việt | Chính phủ (baochinhphu.vn), Bộ Ngoại giao (mofa.gov.vn), Bộ Quốc phòng, Thông tấn xã VN (TTXVN/vietnamplus.vn), Nhân Dân (nhandan.vn), Quân đội Nhân dân (qdnd.vn) | |

**📁 Bộ nguồn chính thức Mỹ MỞ RỘNG (thêm 22/07/2026)** — hai file tra cứu trong `docs/`, dùng khi cần link thẳng nguồn gốc:
| File | Nội dung | Dùng cho |
|---|---|---|
| [`docs/nguon-chinh-thuc-my.md`](docs/nguon-chinh-thuc-my.md) | **199 URL / 85 domain** — trang thông cáo & cập nhật chính thức: Nhà Trắng · OMB/CEA/OSTP · State · ODNI/NSA · DoD + 6 quân chủng + CENTCOM/PACOM · Treasury/Fed/SEC/CFTC/FDIC · USTR/Commerce/BIS · BEA/BLS/Census · **49 uỷ ban Thượng viện + 52 uỷ ban Hạ viện** | Agent Kinh tế · Chính trị · CNQS · Ngoại giao |
| [`docs/mangxahoi-chinh-thuc-my.md`](docs/mangxahoi-chinh-thuc-my.md) | **173 handle X đã xác minh** (chỉ tài khoản được liên kết từ web chính thức của cơ quan) — hành pháp 39 · quốc phòng 9 · lãnh đạo cấp cao 27 · Thượng viện 45 · Hạ viện 53 | **Agent xNews** |

**KHÔNG dán nguyên file vào prompt agent** — quá dài. Agent điều phối chọn vài dòng hợp với category của từng agent rồi nhúng. Hai file này CHƯA verify bằng fetch thật (khác bảng RSS ở dưới); URL nào lỗi thì bỏ, không retry.

**CẢNH BÁO truyền thông nhà nước độc tài** (Xinhua, TASS, Global Times, Press TV, KCNA, Sputnik...): CHỈ dùng cho phát ngôn/tuyên bố CỦA CHÍNH HỌ (vd "Trung Quốc thông báo tập trận X", "Nga tuyên bố Y") — KHÔNG dùng làm nguồn trung lập cho sự kiện gây tranh cãi, thương vong, hay bên thứ ba. Ngoại lệ của quy tắc "ưu tiên nguồn chính phủ".

### Tầng 2 — Nguồn dữ liệu (xác minh số liệu kinh tế/quân sự)
| Chủ đề | Nguồn |
|---|---|
| Kinh tế vĩ mô/tài chính/thương mại | IMF (imf.org — WEO), World Bank (data.worldbank.org), OECD (oecd.org), WTO (wto.org), BIS (bis.org), UNCTAD (unctad.org) |
| Năng lượng | IEA (iea.org) |
| Quốc phòng (số liệu) | SIPRI (sipri.org — chi tiêu QP, chuyển giao vũ khí), IISS Military Balance (*phần lớn trả phí*), Janes (*trả phí*) |

### Tầng 3 — Nguồn phân tích/viện nghiên cứu (cho `significance` + phần Phân tích)
| Khu vực/chủ đề | Nguồn |
|---|---|
| Mỹ | CSIS (+ChinaPower, AMTI về Biển Đông), RAND, Brookings, Carnegie, CFR, CNAS, Atlantic Council, Stimson, Hudson |
| Anh/Âu | RUSI, Chatham House, IISS, ECFR, SWP (Đức), IFRI (Pháp) |
| Ấn Độ Dương-TBD | Lowy Institute, ASPI (Úc), ISEAS-Yusof Ishak, RSIS (Singapore), ORF (Ấn Độ) |
| TQ/Đông Á | MERICS, Jamestown Foundation, NBR |
| Bắc Âu/Baltic/Nga | ICDS (Estonia), FIIA (Phần Lan), Belfer Center |
| Công nghệ/AI/bán dẫn/mạng | CSET (Georgetown), CSIS Strategic Technologies, CNAS Tech & National Security, DARPA, CISA, NIST, ENISA, NATO DIANA |

### Báo chí (phát hiện tin nhanh — LUÔN đối chiếu tầng 1/2/3 trước khi kết luận)
| Nhóm | Nguồn |
|---|---|
| Wire (ưu tiên RẤT CAO — chuẩn, ít bình luận) | Reuters, Associated Press (AP), Agence France-Presse (AFP) |
| Kinh tế/tài chính (*một số trả phí*) | Bloomberg, Financial Times, Wall Street Journal, The Economist, CNBC, Fortune, Nikkei Asia |
| Quốc tế/khu vực | BBC, Deutsche Welle, France 24, Al Jazeera, Al Arabiya, The Straits Times, The Japan Times, The Korea Herald, South China Morning Post, Politico, Axios, The Hindu, Africanews, The Moscow Times |
| Quốc phòng chuyên ngành | Defense News, Breaking Defense, Defense One, Naval News, USNI News, C4ISRNet, SpaceNews, Task & Purpose; *tham khảo nhanh, cần kiểm chứng*: Army Recognition, Oryx |
| Phân tích chính sách (chọn lọc, *một số trả phí*) | The Diplomat, Foreign Policy, Foreign Affairs |
| Việt | VnEconomy, VnExpress, Tuổi Trẻ, Thanh Niên, Dân Trí, Báo Mới, Thế giới & Việt Nam |

**Bộ nguồn rút gọn nên ưu tiên hằng ngày (20 nguồn):** Reuters, AP, AFP, Financial Times, Bloomberg, Nikkei Asia, NATO, ASEAN, UN Meetings Coverage, IMF, World Bank, OECD, SIPRI, IISS, Janes, CSIS, RAND, RUSI, Chatham House, CSET — đủ 4 lớp: tin nhanh · dữ liệu kinh tế · dữ liệu quân sự · phân tích chiến lược.

## URL RSS — ĐÃ VERIFY BẰNG FETCH THẬT ngày 22/07/2026
Trước đây bảng này chỉ tổng hợp qua WebSearch và tự ghi "CHƯA VERIFY" (môi trường cũ chặn `curl`).
Máy hiện tại mạng thông nên đã mở thử **từng URL**: kiểm HTTP code, parse XML, đếm `<item>`, đo bài
mới nhất cách bao lâu. Kết quả: **23 nguồn chạy tốt · 3 sửa được URL · 5 bỏ hẳn · 1 gần như chết**.

⚠️ **Nếu tự kiểm lại, nhớ `curl --compressed`.** Lần chạy đầu UN News bị chấm "hỏng" chỉ vì thiếu cờ
này (server trả gzip, parse ra nhị phân). Đừng gạch một nguồn khi chưa loại trừ lỗi giải nén.

### Dùng tốt — đã xác nhận có item mới
| Nguồn | RSS URL | Kiểm 22/07 |
|---|---|---|
| Defense News | https://www.defensenews.com/arc/outboundfeeds/rss/category/global/?outputType=xml | 25 item, mới 1h |
| Naval News | https://www.navalnews.com/feed/ | 10 item, mới 1h |
| Breaking Defense | https://breakingdefense.com/full-rss-feed/ | 30 item, mới 2h |
| Defense One | https://www.defenseone.com/rss/all/ | 22 item, mới 16h |
| SpaceNews | https://spacenews.com/feed/ | 24 item, mới 6h |
| Task & Purpose | https://taskandpurpose.com/feed | 34 item, mới 1h |
| C4ISRNet | https://www.c4isrnet.com/arc/outboundfeeds/rss/?outputType=xml | 25 item, mới 6h |
| Al Jazeera | https://www.aljazeera.com/xml/rss/all.xml | 25 item, mới <1h |
| BBC World | http://feeds.bbci.co.uk/news/world/rss.xml | 31 item, mới <1h |
| Deutsche Welle | https://rss.dw.com/rdf/rss-en-world | 11 item, mới 4h |
| France 24 | https://www.france24.com/en/rss | 24 item, mới 1h |
| UN News | https://news.un.org/feed/subscribe/en/news/all/rss.xml | 30 item, mới 6h |
| The Straits Times | https://www.straitstimes.com/news/world/rss.xml | 50 item, mới <1h |
| The Moscow Times | https://www.themoscowtimes.com/rss/news | 50 item, mới 2h |
| South China Morning Post | https://www.scmp.com/rss/5/feed/ | 50 item, mới 4h |
| The Hindu | https://www.thehindu.com/news/international/feeder/default.rss | 60 item, mới <1h |
| Africanews | https://www.africanews.com/feed/rss | 50 item, mới 2h |
| Axios | https://www.axios.com/feeds/feed.rss | 100 item, mới 1h |
| CNBC | https://www.cnbc.com/id/100727362/device/rss/rss.html | 30 item, mới <1h |
| The Diplomat | https://thediplomat.com/feed/ | 30 item, mới 6h |
| VnExpress | https://vnexpress.net/rss/the-gioi.rss | 60 item, mới 1h |
| Thanh Niên | https://thanhnien.vn/rss/the-gioi.rss | 50 item, mới 4h |
| Tuổi Trẻ | https://tuoitre.vn/rss/the-gioi.rss | 50 item (feed không ghi ngày) |

### ĐÃ SỬA URL — URL cũ trong bảng này trả 404 / XML rỗng
| Nguồn | URL cũ (SAI) | URL ĐÚNG | Kiểm 22/07 |
|---|---|---|---|
| Nikkei Asia | `https://asia.nikkei.com/rss` → 404 | https://asia.nikkei.com/rss/feed/nar | 50 item |
| VnEconomy | `https://vneconomy.vn/rss/home.rss` → XML rỗng | https://vneconomy.vn/tin-moi.rss | 50 item, mới 4h |
| Dân Trí | `http://dantri.com.vn/Thegioi.rss` → 404 | https://dantri.com.vn/rss/the-gioi.rss | 100 item, mới 2h |

### BỎ HẲN — đừng thử lại, dùng WebSearch cho các nguồn này
| Nguồn | Lý do (kiểm 22/07) |
|---|---|
| NATO | `news.rss`, `rss/rss_newsroom.xml`, `rss.xml` đều 404 → `WebSearch site:nato.int` |
| USNI News | 403 với **cả `curl` LẪN WebFetch** (Cloudflare) — agent cũng không đọc được |
| Politico | Cloudflare "Just a moment"; WebFetch báo thẳng không fetch được domain này |
| Al Arabiya | 403, trả HTML tiếng Ả Rập. Thử `/tools/rss`, `/rss.xml`, `/feed/rss2/en.xml` đều hỏng |
| Reuters / AP / AFP | Không có RSS công khai ổn định — WebSearch (site:reuters.com / apnews.com) |
| Báo Mới | Đã có `baomoi_sync.py` + `baomoi_topics.py` |
| ~~Thế giới & Việt Nam~~ | ⚠️ **Đảo lại 25/07/2026** — URL thử hồi đó (`/rss/the-gioi.rss`) sai; feed thật `baoquocte.vn/rss_feed/` chạy tốt, xem bảng "Gộp từ kho tư liệu cũ" |

⚠️ **Fortune** (https://content.fortune.com/feed/) parse được 30 item nhưng bài mới nhất **120h (5 ngày)
trước** — feed thật nhưng gần như đứng. Ưu tiên thấp, đừng trông vào nó cho tin trong ngày.

**Cách kiểm lại về sau:** `scripts/rss_check.py` (đọc thẳng bảng này trong CLAUDE.md rồi fetch từng URL).

### Nguồn MỞ RỘNG 5 chủ đề — verify fetch thật 25/07/2026 (gộp vào để `rss_check.py` tự kiểm)
Bổ sung cho 5 chủ đề (Nội bộ Mỹ · Úc–Biển Đông · CNQS Mỹ · Mali · Pitch Black). Chi tiết cách dùng từng
nguồn xem Phụ lục trong `.claude/skills/quet-tin/SKILL.md`.
| Nguồn | RSS URL | Kiểm 25/07 |
|---|---|---|
| The Hill | https://thehill.com/feed/ | 100 item |
| The Hill — Defense | https://thehill.com/policy/defense/feed/ | 15 item |
| Roll Call | https://rollcall.com/feed/ | 10 item |
| Government Executive | https://www.govexec.com/rss/all/ | 22 item |
| ABC News AU (world) | https://www.abc.net.au/news/feed/51120/rss.xml | 25 item |
| Lowy Interpreter | https://www.lowyinstitute.org/the-interpreter/rss.xml | 50 item |
| AMTI/CSIS (Biển Đông) | https://amti.csis.org/feed/ | 10 item |
| Rappler | https://www.rappler.com/feed/ | 10 item |
| Philstar (headlines) | https://www.philstar.com/rss/headlines | 10 item |
| Inquirer | https://www.inquirer.net/fullfeed/ | 20 item |
| gCaptain | https://gcaptain.com/feed/ | 12 item |
| Naval Technology | https://www.naval-technology.com/feed/ | 10 item |
| The War Zone (TWZ) | https://www.twz.com/feed | 44 item |
| DefenseScoop | https://defensescoop.com/feed/ | 10 item |
| Aviation Week | https://aviationweek.com/rss.xml | 10 item |
| Long War Journal (Mali/JNIM) | https://www.longwarjournal.org/feed | 30 item |
| DVIDS news (tập trận) | https://www.dvidshub.net/rss/news | 20 item |

⚠️ **Feed fetch được nhưng ĐỨNG — đừng trông vào cho tin trong ngày** (kiểm 25/07): **AMTI/CSIS** bài
mới nhất ~81 ngày trước (nguồn phân tích tầng 3, đăng thưa — dùng làm nền/bối cảnh Biển Đông thôi);
**Aviation Week** (`rss.xml`) ~115 ngày trước (gần như chết như Fortune → WebSearch cho tin CNQS trong
ngày). Lowy Interpreter ~32h (blog phân tích, chấp nhận được).

**WebSearch-only (không RSS dùng được — kiểm 25/07, ĐỪNG đưa vào bảng trên):** NOTUS · Punchbowl (trả
phí) · C-SPAN · Defence Connect · ADBR · Philippine News Agency (pna.gov.ph 403) · Manila Bulletin (403)
· Radio Free Asia (rfa.org) · The Maritime Executive · National Defense Magazine · Jeune Afrique (403) ·
The Africa Report (403) · RFI (rfi.fr) · ISS Africa → dùng `WebSearch site:domain`.

### Trang CHÍNH THỨC Mỹ có RSS — verify fetch thật 27/07/2026 (đưa `docs/nguon-chinh-thuc-my.md` vào đường quét)
Huy gửi file `trang chính thống của Mỹ.doc` (199 URL / 85 domain) và bảo kiểm xem đã có chưa. Kết quả
đối chiếu: **199/199 URL ĐÃ có** trong `docs/nguon-chinh-thuc-my.md` từ 22/07 — nhưng đó chỉ là **danh
sách tra cứu**, không nằm trong đường quét: **0/85 domain có trong bảng RSS**, và **76/85 chưa bao giờ
đóng góp một tin nào**. Đúng bệnh "có mục mà không có đường nạp thì mục chết".
Đã dò RSS cho 30 domain hợp 5 chủ đề, **9 cái chạy** → đưa vào bảng để `harvest.py` tự quét:
| Nguồn | RSS URL | Kiểm 27/07 | Hợp nhóm/chủ đề |
|---|---|---|---|
| Nhà Trắng — Presidential Actions | https://www.whitehouse.gov/presidential-actions/feed/ | 30 item | **Nội bộ Mỹ nhóm 2** (sắc lệnh, memorandum) |
| Uỷ ban Đối ngoại Hạ viện | https://foreignaffairs.house.gov/rss.xml | 10 item | **Nội bộ Mỹ nhóm 1** (điều trần/thông cáo uỷ ban) |
| Cục Dự trữ Liên bang | https://www.federalreserve.gov/feeds/press_all.xml | 20 item | Nội bộ Mỹ nhóm 4 |
| SEC | https://www.sec.gov/news/pressreleases.rss | 25 item | Nội bộ Mỹ nhóm 4 |
| FTC | https://www.ftc.gov/feeds/press-release.xml | 10 item | Nội bộ Mỹ nhóm 4 |
| USTR | https://www.ustr.gov/rss.xml | 10 item | Nội bộ Mỹ nhóm 4 (thuế quan) |
| BEA | https://www.bea.gov/news/rss | 12 item | Nội bộ Mỹ nhóm 4 (số liệu vĩ mô) |
| Bộ Năng lượng | https://www.energy.gov/rss.xml | 10 item | nhóm 2/4 + hạt nhân |
| Lực lượng Không gian Mỹ | https://www.spaceforce.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=1060&max=20 | 20 item | **CNQS Mỹ** |

⚠️ **KHÔNG có RSS dùng được — đừng thử lại, dùng WebSearch `site:domain`** (kiểm 27/07): các uỷ ban
Thượng viện (armed-services, foreign, appropriations, intelligence — đều 403) · armedservices.house.gov
· state.gov · commerce.gov · justice.gov · dhs.gov · home.treasury.gov · bls.gov · dni.gov · stripes.com.
### 🪖 Trang .mil — chẩn đoán 27/07 SAI MỘT NỬA, đo lại 30/07/2026
| Nguồn | RSS URL | Kiểm 30/07 từ LOCAL |
|---|---|---|
| Lục quân Mỹ | https://www.army.mil/rss/static/1.xml | **43–45 item** — lấy được, phải đi bằng vân tay TLS |
| Không quân Mỹ — Air Force Link News | https://www.af.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=1&max=20 | chập chờn: có lượt 20 item, phần lớn không phân giải nổi tên miền |

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
⚠️ **BẪY `Site=1`:** tham số này trả **feed của Air Force bất kể domain** — thử `marines.mil` và
`news.uscg.mil` với `Site=1` đều ra y hệt "Air Force Link News". Thêm cả ba vào bảng là nạp trùng nội
dung ba lần. Phải kiểm tiêu đề thật trước khi tin một feed `DesktopModules`.
⛔ **Chưa tìm được feed RSS riêng** (mọi biến thể ContentType/Site đã thử đều 0 item): `navy.mil`,
`marines.mil`, `centcom.mil`, `pacom.mil`, `jcs.mil`, `news.uscg.mil`. Phần này vẫn đúng — **nhưng câu
kế tiếp thì SAI và đã bỏ.**

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

### 🕸️ TRANG HTML QUÉT TRỰC TIẾP — không có RSS nhưng vẫn đọc được (thêm 27/07/2026)
Huy nhắc đúng: *"không có RSS thì mày vẫn xem được mà"*. Kiểm lại 85 domain trong file nguồn chính thức
Mỹ: **42 mở được HTML bằng curl** (chỉ 34 chặn 403). `harvest.py` có lớp `[HTML]` quét thẳng trang danh
sách thông cáo — lấy link + tiêu đề + ngày (tìm trong khối HTML quanh mỗi link).
**Giá trị lớn nhất: toàn bộ uỷ ban HẠ VIỆN đều mở được**, mà đó chính là **nhóm 1** (điều trần + bỏ
phiếu) — nhóm luôn thiếu tin nhất. Thực tế lần chạy đầu bắt được "Chairman Rogers Applauds House Passage
of FY27 NDAA", "House Passes H.R. 9770", "Opening Statement at the FY27 NDAA Markup".

**Cột "Chạy ở"** — `cả hai` = local + CI đều đọc được · **`CI`** = CHỈ GitHub runner đọc được, máy Mac
bị chặn (harvest local tự bỏ qua, xem `html_pages_from_claude_md`). Đo bằng `scripts/probe_sources.py`
chạy ở cả hai nơi (27/07/2026), **đo lại 30/07/2026 bằng `kiem_nguon.py` + trình duyệt**.

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

| Trang | URL | Chạy ở | Nhóm/chủ đề |
|---|---|---|---|
| Uỷ ban Quân vụ Hạ viện | https://armedservices.house.gov/news/press-releases | cả hai | **Nội bộ Mỹ nhóm 1** |
| Uỷ ban Chuẩn chi Hạ viện | https://appropriations.house.gov/news/press-releases | cả hai | **Nội bộ Mỹ nhóm 1** |
| Uỷ ban Tình báo Hạ viện | https://intelligence.house.gov/news/ | cả hai | Nội bộ Mỹ nhóm 1 |
| Uỷ ban Tư pháp Hạ viện | https://judiciary.house.gov/media/press-releases | cả hai | Nội bộ Mỹ nhóm 1 |
| Uỷ ban An ninh Nội địa Hạ viện | https://homeland.house.gov/news/ | cả hai | Nội bộ Mỹ nhóm 1 |
| Uỷ ban Giám sát Hạ viện | https://oversight.house.gov/news/ | cả hai | Nội bộ Mỹ nhóm 1 |
| Uỷ ban Tài chính Hạ viện | https://financialservices.house.gov/news/ | cả hai | nhóm 1 + 4 |
| Uỷ ban Thuế vụ Hạ viện | https://waysandmeans.house.gov/news/ | cả hai | nhóm 1 + 4 |
| Uỷ ban Ngân sách Hạ viện | https://budget.house.gov/news | cả hai | nhóm 1 + 4 |
| Uỷ ban Khoa học Hạ viện | https://science.house.gov/news | cả hai | nhóm 1 |
| **Uỷ ban Quân vụ THƯỢNG VIỆN** | https://www.armed-services.senate.gov/press-releases | cả hai | **Nội bộ Mỹ nhóm 1** |
| **Uỷ ban Đối ngoại Thượng viện** | https://www.foreign.senate.gov/press | cả hai | **Nội bộ Mỹ nhóm 1** |
| **Uỷ ban Chuẩn chi Thượng viện** | https://www.appropriations.senate.gov/news/majority | cả hai | **Nội bộ Mỹ nhóm 1** |
| **Uỷ ban Tình báo Thượng viện** | https://www.intelligence.senate.gov/reports-publications/press-releases/ | cả hai | **Nội bộ Mỹ nhóm 1** |
| **Uỷ ban Tư pháp Thượng viện** | https://www.judiciary.senate.gov/press/ | cả hai | Nội bộ Mỹ nhóm 1 |
| Uỷ ban Ngân hàng Thượng viện | https://www.banking.senate.gov/newsroom | cả hai | nhóm 1 + 4 |
| Uỷ ban Tài chính Thượng viện | https://www.finance.senate.gov/chairmans-news | cả hai | nhóm 1 + 4 |
| Uỷ ban Ngân sách Thượng viện | https://www.budget.senate.gov/chairman/newsroom | cả hai | nhóm 1 + 4 |
| Uỷ ban Thương mại Thượng viện | https://www.commerce.senate.gov/press/ | cả hai | nhóm 1 + 4 |
| Uỷ ban Năng lượng Thượng viện | https://www.energy.senate.gov/newsroom | cả hai | nhóm 1 |
| Uỷ ban An ninh Nội địa Thượng viện (HSGAC) | https://www.hsgac.senate.gov/media/majority-news/ | cả hai | nhóm 1 |
| Uỷ ban Quy tắc Thượng viện | https://www.rules.senate.gov/news/press-releases | cả hai | nhóm 1 |
| Thông cáo chung Thượng viện | https://www.pressphotographers.senate.gov/senate/senate-press-releases/ | cả hai | nhóm 1 |
| **Hải quân Mỹ** | https://www.navy.mil/Press-Office/Press-Releases/ | cả hai | **Úc & Biển Đông** · CNQS Mỹ |
| **Thuỷ quân lục chiến Mỹ** | https://www.marines.mil/News/Press-Releases/ | cả hai | **Úc & Biển Đông** · **Pitch Black** |
| **PACOM (Bộ Chỉ huy Ấn Độ Dương-TBD)** | https://www.pacom.mil/Media/News/News-Articles/ | **CI** | **Úc & Biển Đông** · **Pitch Black** |
| **CENTCOM** | https://www.centcom.mil/MEDIA/PUBLIC-RELEASES/ | **CI** | **Mỹ–Mali** · CNQS Mỹ |
| **JCS (Hội đồng Tham mưu trưởng Liên quân)** | https://www.jcs.mil/Media/News/ | **CI** | CNQS Mỹ · Úc & Biển Đông |
| **Tuần duyên Mỹ (USCG)** | https://www.news.uscg.mil/Press-Releases/ | **CI** | Úc & Biển Đông |
| Census Bureau | https://www.census.gov/newsroom/press-releases.html | **CI** | nhóm 4 (số liệu) |
| OCC (Kiểm soát Tiền tệ) | https://www.occ.treas.gov/news-events/newsroom/news-issuances-by-year/news-releases/index-news-releases.html | **CI** | nhóm 4 |

⚠️ Đây là **quét HTML thô**, nhiễu cao hơn RSS: có thể lẫn link điều hướng, và **ngày lấy từ khối HTML
quanh link nên có thể sai** — agent PHẢI mở bài kiểm ngày sự kiện như với lớp `[GNEWS]`.

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
- **Nghiệm thu một trang mới thì đếm 3 con số**, đừng dừng ở mã 200: số link qua bộ lọc đường dẫn ·
  số khớp `match_topic` · và độ dài tiêu đề lấy ra. Trang 200 mà 0 link là dòng bảng vô dụng.

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

### RealClear — verify fetch thật 27/07/2026 (Huy chỉ định thêm)
| Nguồn | RSS URL | Kiểm 27/07 | Hợp chủ đề |
|---|---|---|---|
| RealClearDefense | https://www.realcleardefense.com/index.xml | 126 item, mới trong ngày | 3 CNQS Mỹ · 2 Úc–Biển Đông |
| RealClearPolitics | https://www.realclearpolitics.com/index.xml | có item mới trong ngày | 1 Nội bộ Mỹ (cả 4 nhóm) |
| RealClearWorld | https://www.realclearworld.com/index.xml | 200 | chung |

⚠️ **Chỉ `index.xml` chạy** — `/feed/`, `/politics.xml` và cả trang chủ đều trả **403** với curl. Đừng
đổi sang dạng khác.
⚠️ **RealClear là trang TỔNG HỢP** (giống Báo Mới): phần lớn item là bài **bình luận/phân tích** của
tác giả khác đăng lại trên tên miền realclear*, link trỏ về chính realclear chứ không về toà soạn gốc.
Vì vậy: (a) ưu tiên các item là TIN (vd "Pentagon Awards Largest-Ever F-35 Spare Parts Contract") hơn
là bài opinion; (b) **truy về bài gốc** như quy tắc Báo Mới — mở bài, tìm nguồn gốc (thông cáo chính
thức / wire / báo chuyên ngành) rồi lấy link đó; không tìm được thì giữ link realclear nhưng phải ghi
rõ `sourceName` là RealClearDefense/Politics để người đọc biết đây là trang tổng hợp.

### Nguồn CHÍNH THỨC Lầu Năm Góc — verify fetch thật 27/07/2026 (mỏ tin CNQS chưa khai thác)
`defense.gov` nay **redirect sang `war.gov`** (đổi tên bộ). Trang `war.gov/News/Contracts/` trả 403 với
curl, NHƯNG hai feed RSS dưới đây chạy tốt — đây là nguồn TẦNG 1 cho chủ đề CNQS Mỹ, trước giờ chưa
dùng lần nào:
| Nguồn | RSS URL | Kiểm 27/07 |
|---|---|---|
| DoD Contracts | https://www.war.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=400&Site=945&max=20 | có "Contracts for July 24/23/22, 2026" |
| DoD News Releases | https://www.war.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=9&Site=945&max=20 | có thông cáo mới (vd hợp đồng Oracle ~7 tỷ USD) |

⚠️ **Tiêu đề feed Contracts là "Contracts for July 24, 2026" — KHÔNG chứa từ khoá chủ đề nào**, nên
`harvest.py` phải gán cứng chủ đề cho hai nguồn này qua `FORCE_TOPIC`, đừng lọc bằng từ khoá. Mỗi item
là một trang gộp TẤT CẢ hợp đồng quốc phòng ký hôm đó — agent phải mở đọc và tự chọn hợp đồng đáng đưa
(khí tài cụ thể, giá trị lớn), không nạp cả trang.

**Đã thử và KHÔNG dùng được (đừng thử lại):** `armed-services.senate.gov/rss/hearings` — 403 ·
`c-span.org/rss/` — 403 · `war.gov/News/Contracts/` (trang HTML) — 403. Muốn theo lịch điều trần thì
dùng RSS The Hill (đã có trong bảng, thực tế bắt được tin "GOP senator ahead of Fauci testimony") hoặc
truy vấn Google News trong `harvest.py`.

### Gộp từ kho tư liệu cũ — verify fetch thật 25/07/2026
Ba file `docs/diemtin-*-sources.md` / `-x-accounts.md` (dò 09/07, trước giờ KHÔNG nguồn nào trong quy
trình quét đọc tới) đã được đối chiếu với bảng trên; phần dưới là các nguồn CHƯA có mặt và **fetch
thật hôm nay còn sống**. Cột "hợp chủ đề" = chủ đề trong 5 chủ đề đang quét.
| Nguồn | RSS URL | Kiểm 25/07 | Hợp chủ đề |
|---|---|---|---|
| Defense Daily | https://www.defensedaily.com/feed/ | 50 item, mới 12h | 3 CNQS Mỹ |
| Air & Space Forces Magazine | https://www.airandspaceforces.com/feed/ | 9 item, mới 13h | 3 CNQS Mỹ |
| Military Times | https://www.militarytimes.com/arc/outboundfeeds/rss/ | 25 item, mới 12h | 3 CNQS Mỹ |
| FlightGlobal | https://www.flightglobal.com/rss/ | 10 item, mới 12h | 3 CNQS Mỹ |
| The Aviationist | https://theaviationist.com/feed/ | 15 item, mới 15h | 3 CNQS Mỹ |
| Soldier Systems Daily | https://soldiersystems.net/feed/ | 6 item, mới 9h | 3 CNQS Mỹ |
| Sandboxx News | https://www.sandboxx.us/news/feed/ | 15 item, mới 11h | 3 CNQS Mỹ |
| DVIDS (toàn bộ) | https://www.dvidshub.net/rss/all | 419 item, mới 2h | 3 + 5 Pitch Black |
| Shephard Media | https://www.shephardmedia.com/news/feed/ | 10 item, mới 23h | 3 + 2 Úc |
| The Japan Times | https://www.japantimes.co.jp/feed/ | 30 item, mới 1h | 2 Biển Đông |
| Yonhap (Hàn Quốc) | https://en.yna.co.kr/RSS/news.xml | 97 item, mới trong ngày | 2 Biển Đông |
| AllAfrica | https://allafrica.com/tools/headlines/rdf/latest/headlines.rdf | 30 item, mới 14h | 4 Mali/Sahel |
| Federal News Network — Defense | https://federalnewsnetwork.com/category/defense-main/feed/ | 15 item, mới 10h | 1 Nội bộ Mỹ |
| Atlantic Council | https://www.atlanticcouncil.org/feed/ | 100 item, mới 17h | tầng 3 phân tích |
| Foreign Policy | https://foreignpolicy.com/feed/ | 25 item, mới 12h | tầng 3 phân tích |
| Bellingcat | https://www.bellingcat.com/feed/ | 10 item, mới 18h | OSINT kiểm chứng |
| The Guardian — World | https://www.theguardian.com/world/rss | 45 item, mới <1h | chung |
| Semafor | https://www.semafor.com/rss.xml | 261 item, mới 14h | chung |
| NPR — World | https://feeds.npr.org/1004/rss.xml | 10 item, mới 12h | chung |
| VietnamPlus (TTXVN) | https://www.vietnamplus.vn/rss/thegioi.rss | 50 item, mới trong ngày | 2 + VN tầng 1 |
| Nhân Dân | https://nhandan.vn/rss/thegioi-1231.rss | 50 item, mới trong ngày | VN tầng 1 |
| Báo Chính phủ | https://baochinhphu.vn/quoc-te.rss | 50 item (feed không ghi ngày) | VN tầng 1 |
| VietnamNet | https://vietnamnet.vn/rss/the-gioi.rss | 1000 item, mới <1h | VN chung |
| Báo Thế giới & Việt Nam | https://baoquocte.vn/rss_feed/ | 25 item, mới <1h | VN ngoại giao |

⚠️ **Sửa lại đánh giá cũ:** Thế giới & Việt Nam trước bị xếp "WebSearch-only" (bảng BỎ HẲN) vì thử
`/rss/the-gioi.rss` → 404. Feed thật là `rss_feed/` và chạy tốt → đã chuyển lên bảng này.
⚠️ **DVIDS `/rss/all`** (419 item) rộng hơn `/rss/news` (20 item) đang dùng — giàu tin diễn tập/ảnh
đơn vị, nhưng lẫn nhiều thông cáo địa phương; dùng cho tập trận/CNQS thì lọc theo từ khoá.
⚠️ **Nguồn VN vẫn là ưu tiên #2** (xem "Thứ tự ưu tiên" bên dưới: tiếng Anh trước) — thêm vào đây để
có URL sẵn khi cần góc nhìn trong nước / tin Biển Đông, KHÔNG phải để thay nguồn tiếng Anh.

**Kho tư liệu đã kiểm nhưng KHÔNG dùng được (đừng thử lại):** CSIS `csis.org/rss.xml` — parse được 10
item nhưng bài mới nhất **tháng 3/2016**, feed bỏ hoang 10 năm (bản dò 09/07 chấm "10 ✓" vì chỉ đếm
item, không đo tuổi bài) → `WebSearch site:csis.org`, riêng Biển Đông đã có `amti.csis.org/feed/` ·
War on the Rocks `warontherocks.com/feed/` — 403 · DARPA `darpa.mil/rss.xml` — không phân giải được
tên miền (thử 2 lần) → `WebSearch site:darpa.mil`.

## 🔚 Hết bản thi hành — phần luật còn lại nằm ở `docs/luat/`

Bảng tra ở đầu file. Bảy file: `pham-vi-quet.md` · `gui-ban-tin.md` · `telegram.md` · `cong-kiem.md`
· `kho-du-lieu.md` · `think-tank.md` · `van-hanh.md`.

⛔ **ĐỪNG XOÁ MỤC NÀY, VÀ ĐỪNG ĐẨY BẢNG NGUỒN XUỐNG CUỐI FILE.** Ba script bóc bảng nguồn
(`harvest.py` · `rss_check.py` · `probe_sources.py`) cắt khối bảng từ tiêu đề mục nguồn **tới tiêu đề
`##` kế tiếp**. Trước 25/08/2026 cả ba trả **rỗng** khi không còn tiêu đề nào phía sau, tức mọi feed
biến mất mà lô tin vẫn ra đời bình thường. Nay cả ba đã vá để lấy tới hết file (ca [10] và [11] của
`tests/test-bang-nguon-claude-md.py` canh đúng chiều này), nhưng mục chốt này vẫn giữ làm lớp thứ hai.
