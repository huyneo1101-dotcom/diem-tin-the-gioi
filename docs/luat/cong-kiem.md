# Cổng kiểm và bộ test của repo — Điểm Tin Thế Giới

> Xẻ từ `CLAUDE.md` ngày 25/08/2026 để bản thi hành gọn lại (luật mục 31 của `~/.claude/CLAUDE.md`).
> **Nội dung giữ NGUYÊN VĂN, không cắt chữ nào** — chỉ đổi chỗ ở. Bản thi hành: [`../../CLAUDE.md`](../../CLAUDE.md).

## 🧪 TEST CỔNG KIỂM — `tests/` (dựng 29/07/2026, áp luật mục 17 CLAUDE.md toàn cục)

**Luật:** mọi cổng/hook/checker trong repo này **phải có ít nhất MỘT ca PHẢI CHẶN** — dựng đúng
điều kiện xấu rồi khẳng định nó thật sự chặn/kêu. Test chỉ có ca "phải cho qua" là **chưa test**.

**Vì sao (bài học QuanSu 29/07/2026):** cổng dàn ý người duyệt ở `App/QuanSu/intrep-to-docx.py`
đã **CÂM từ ngày dựng** (bug NFD tên file macOS) mà không ai biết, vì nó thuộc loại *"hỏng thì im
lặng cho qua"* — không có gì để chặn thì cổng im, và cổng chết cũng im y hệt. Chạy trăm lần "thấy
nó không kêu" không chứng minh được gì. Mọi cổng của repo này đều cùng loại đó.

| Bộ test | Cổng nó canh | Ca |
|---|---|---|
| `tests/test-cong-baomoi.py` | Cổng Báo Mới chống bỏ sót (`scripts/add_news.py`) | 8 — 3 PHẢI NHẮC, 4 chống nhắc oan, 1 kiểm cổng còn nằm trên đường đi của `--recent-titles` |
| `tests/test-so-da-gui.py` | Sổ đã gửi (`so_da_gui.py` + `make_docx.loc_chua_gui` + `loc_bo_tin_ca_sang`) | **14 ca · `--tu-kiem` bắt 8/8 bản hỏng** — 5 PHẢI LOẠI/PHẢI ĐÚNG PHẠM VI, 3 chống lọc oan, 1 kiểm còn người đọc sổ, **5 ca mới cho lọc tin ca sáng**: 1 PHẢI LOẠI + 3 chống lọc oan (dòng `toi` · bản SÁNG · ngày khác) + 1 kiểm `main()` còn gọi cho cả 3 loại |
| `tests/test-canh-bao-tin-noi-tiep.py` | Lớp cảnh báo TIN NỐI TIẾP (`add_news.warn_similar_titles`, ngưỡng `JACCARD_CANH_BAO_TIEU_DE`) | **10 ca · `--tu-kiem` bắt 5/5 bản hỏng** — 3 PHẢI KÊU (gồm ca đòi ĐÚNG lời nhắc, không chỉ đòi có kêu), 3 chống kêu oan + 1 ca biên, 1 hồi quy con số ngưỡng, 1 kiểm còn nằm trên đường đi, 1 kiểm ngưỡng lọc THẬT của mục Jay Lâm KHÔNG bị hạ theo. Bản hỏng canh **cả hai chiều**: nâng lại 0.6 (câm trở lại) và hạ về 0 (kêu mọi cặp) |
| `tests/test-canary-ban-tin.py` | Canary bản tin (`.github/scripts/canary.py`) | 10 — 7 PHẢI KÊU, 3 PHẢI IM (gồm ca hồi quy kêu oan 00:23 ngày 28/07) |
| `tests/test-cong-phien-test.py` | Cổng "phiên TEST không đụng cờ thật" (`scripts/state.py` + `claude-web-scan.yml`) | 11 — 5 PHẢI CHẶN, 4 chống chặn oan + đối chứng, 1 kiểm cổng còn nằm trên đường đi (đọc chính file yml), 1 kiểm banner |
| `scripts/sua_nhan_analyses.py --tu-kiem` | Chính `--kiem` của nó (nhãn `outlet` mục Think-tank) | 5 — 3 PHẢI CHẶN, 2 PHẢI CHO QUA + 1 đối chứng. **Test nằm TRONG script** chứ không ở `tests/` vì cổng và bộ ca dùng chung dữ liệu giả |
| `tests/test-tach-analyses.py` | Việc tách kho think-tank ra `data/analyses.json` (30/07/2026) | 9 ca — mọi mắt xích đều hỏng-thì-im-lặng: mục Think-tank trống · 442 nhãn MỚI · guardrail trùng-url tê liệt · offline mất kho. `--tu-kiem` dựng 4 bản hỏng |
| `scripts/analyses_store.py --tu-kiem` | Chính lớp đọc/ghi kho | 3 PHẢI CHẶN (thiếu file · JSON hỏng · không phải mảng) + cổng hồi quy "index.html phải rỗng" |
| `tests/test-cong-luat-push.py` | Cổng "workflow có LỊCH thì cấm rebase file DÙNG CHUNG" (`.github/scripts/kiem_luat_push.py`) | 11 ca — 4 PHẢI CHẶN (bật lại lịch drive-import · `git add logs/` · `git add -A` · dạng `"on":` có nháy), 4 đối chứng chống chặn oan, 2 fail-closed (yml hỏng · thư mục rỗng đều phải trả mã 2), 1 soi thư mục workflow THẬT. `--tu-kiem` bắt 8/8 bản hỏng |
| `tests/test-ghi-so-push.py` | Sổ đã gửi chịu được HAI workflow ghi cùng lúc (`.github/scripts/ghi_so_push.py`) | 10 ca — 2 CA CHÍNH (giữ đủ hai dòng · URL tính đúng một lần) · 2 PHẢI CHẶN (nhân dòng · `--hard` đè index.html) · 1 PHẢI KÊU · 4 đối chứng · 1 kiểm cổng còn nằm trên đường đi (soi 2 file yml). `--tu-kiem` bắt 6/6 bản hỏng |
| `tests/test-bang-nguon-claude-md.py` | Đường ĐỌC BẢNG NGUỒN từ CLAUDE.md + phép lấy TIÊU ĐỀ của lớp `[HTML]` | 13 ca — 6 PHẢI CHẶN (nhắc tên bảng trong văn xuôi ×1/×3 · bảng HTML lọt vào lớp RSS · feed giao với trang HTML · thẻ `<a>` gộp tóm tắt vẫn phải ra tiêu đề qua `aria-label` · và qua `<h4 class=title>` kèm tiêu đề phải sạch), 7 đối chứng (cột `CI` bị bỏ ở local · đủ 06 trang quân chủng · Navy+Marines có ở local · tên không mang dấu `**` · không có bảng thì trả rỗng êm · tiêu đề đổi chữ vẫn đọc được · **chống nới tay**: không có nguồn tiêu đề sạch thì BỎ chứ không nạp tiêu đề rác). `--tu-kiem` bắt 5/5 bản hỏng |
| `tests/test-nhan-tin-jaylam.py` | Nhận file `.docx` Jay Lâm gửi qua bot (`docx_text.py` · `telegram_bot.py::xu_ly_tin_jaylam` · `gui_ban_sao_cho_chu` · `_la_chat_chu`) | **23 ca · `--tu-kiem` bắt 7/7 bản hỏng** — 4 PHẢI CHẶN (không phải `.docx` · tải hỏng · file rỗng → KHÔNG gọi `luu_tin_jaylam`), 4 ca trích chữ, 1 ca luồng bình thường, **3 ca trần độ dài** (hồi quy file thật 34.525 ký tự · vượt trần PHẢI báo · dưới trần không kêu oan), **6 ca chuyển tiếp bản sao** (đúng `file_id` + caption · VẪN gửi khi tải hỏng · VẪN gửi khi Supabase hỏng · KHÔNG gửi ngược cho chính chat chủ · thiếu chat chủ không crash · gọi THẲNG hàm để canh chốt bên trong), **5 ca chat chủ** |
| `tests/test-tin-jaylam-trong-docx.py` | **BỘ LỌC** Jay Lâm trong `.docx` bản tin (`make_docx.py`) | **20 ca · `--tu-kiem` bắt 11/11 bản hỏng** — lọc phủ **CẢ BA** mục `usNews`/`worldNews`/`events` (bỏ sót một mục là lặp tin ở đúng mục đó) · áp **CẢ HAI buổi** (file gửi tối qua còn hiệu lực 3 ngày) · sổ thiếu/JSON hỏng/không phải mảng đều **fail về phía KHÔNG lọc nhưng CÓ TIẾNG** · dòng sổ thiếu url không được lọc oan tin có `sourceUrl` rỗng · tin bị bỏ phải KÊU kèm tiêu đề để soi ngược · hồi quy: mục 5 và đường Supabase đã bỏ hẳn, `la_buoi_toi` vẫn còn cho `ten_file()` |
| `tests/test-cong-kich-notify.py` | Cổng "chỉ phiên TỰ NẠP mới được kích notify" (`state.py::ghi_co_da_nap` + `.github/scripts/quyet_dinh_kich.py` + `claude-web-scan.yml`) | **10 ca · `--tu-kiem` bắt 3/3 bản hỏng** — 3 PHẢI CHẶN (chưa `done` · sau `skip` · sau `fail` đều KHÔNG kích), 3 chống chặn oan, 1 ca hai pipeline độc lập, **2 ca đọc chính file yml** (phải gọi `quyet_dinh_kich.py`; KHÔNG được quay lại `git log --format=%s`), 1 ca chạy `--tu-kiem` của chính script quyết định |
| `tests/test-tin-jaylam-xu-ly.py` | Ba lệnh của `scripts/tin_jaylam.py` (`--liet-ke`/`--ghi`/`--ghi-loai`) | **39 ca (14 PHẢI CHẶN) · `--tu-kiem` bắt 19/19 bản hỏng** — `--ghi`: id bịa/trùng · `tin` rỗng · tiêu đề ngoài 10-200 · url xấu thì BỎ url chứ không chặn cả lô · cảnh báo TRÍCH SÓT · PATCH hỏng phải KÊU. `--ghi-loai`: **`trung_voi` bắt buộc** (không có thì không soi ngược được vì sao mất tin) · dedupe theo url · cắt `GIU_NGAY` cả hai chiều · `id_jay` ngoài khung thì cảnh báo chứ không chặn. `--liet-ke`: dòng ĐÃ trích vẫn nằm trong hàng chờ (query KHÔNG lọc `da_xu_ly`) · đóng sổ dòng quá khung · khung RỘNG NHẤT 3 ngày |

| `tests/test-mali-va-tap-tran.py` | Mali rời `.docx` + sang bản sáng · tập trận bám ĐỘNG (`make_docx` · `send-morning-email.js` · `send_telegram.py` · `tap_tran.py` · `topics.py` · `harvest.py`) | **26 ca · `--tu-kiem` bắt 12/12 bản hỏng** — 5 ca Mali rời .docx (gồm 1 PHẢI KÊU + 1 chống kêu oan) · 5 ca Mali vào bản sáng (gate · payload · **ba bảng khoá khớp nhau** · chạy `laTinMali` thật bằng `jsc`) · 16 ca tập trận động (cuộc đã tàn dù `status: ongoing` phải bị loại · cuộc đang chạy dù khai `upcoming` phải nhận · từ khoá không chứa mảnh tên nước · có CẢ dạng có dấu · nước đăng cai suy từ `location` · truy vấn không rộng · nạp TRƯỚC lớp quét · bơm GHI ĐÈ không cộng dồn · chống nới tay tin RAAF thuần) |
| `tests/test-uu-tien-chu-de.py` | Một chủ đề ăn mất ứng viên của chủ đề khác (`harvest.py::UU_TIEN_CHU_DE` + `uu_tien_chu_de`) | **10 ca (05 PHẢI CHẶN) · `--tu-kiem` bắt 7/7 bản hỏng** — tin Pitch Black bị chủ đề 02 bắt trước vẫn phải về chủ đề 05 · `main()` phải gọi hàm sort **TRƯỚC** vòng khử trùng URL (hàm đúng mà không ai gọi thì lỗ vẫn nguyên) · truy vấn chủ đề 05 không được chứa `RAAF` · **đối chứng chiều ngược**: chủ đề 02 phải CÒN truy vấn Không quân Úc · mọi chủ đề trong `GNEWS_QUERIES` phải đã khai thứ tự · sort ổn định để lô local vẫn đứng trước lô CI |

Chạy cả năm sau mỗi lần sửa `add_news.py` · `so_da_gui.py` · `ghi_so_push.py` · `make_docx.py` · `canary.py` · `state.py` · `telegram_bot.py` · `docx_text.py` · `harvest.py` · `claude-web-scan.yml` · `notify-email.yml` · `notify-morning.yml`:
```
python3 /Users/Huy/Claude/diem-tin-the-gioi/tests/test-cong-baomoi.py
python3 /Users/Huy/Claude/diem-tin-the-gioi/tests/test-uu-tien-chu-de.py
python3 /Users/Huy/Claude/diem-tin-the-gioi/tests/test-so-da-gui.py
python3 /Users/Huy/Claude/diem-tin-the-gioi/tests/test-canary-ban-tin.py
python3 /Users/Huy/Claude/diem-tin-the-gioi/tests/test-cong-phien-test.py
python3 /Users/Huy/Claude/diem-tin-the-gioi/tests/test-ghi-so-push.py
python3 /Users/Huy/Claude/diem-tin-the-gioi/tests/test-nhan-tin-jaylam.py
python3 /Users/Huy/Claude/diem-tin-the-gioi/tests/test-tin-jaylam-trong-docx.py
python3 /Users/Huy/Claude/diem-tin-the-gioi/tests/test-tin-jaylam-xu-ly.py
```

⚠️ **SỬA CHÍNH `CLAUDE.md` CŨNG PHẢI CHẠY TEST — tài liệu này LÀ CẤU HÌNH, không phải chỉ là chữ**
(đúc 30/07/2026, vấp thật ngay trong lượt thêm 06 trang quân chủng vào bảng). `harvest.py` đọc bảng
nguồn thẳng từ file này, nên **một câu văn xuôi cũng làm chết một lớp quét**: chỉ vì viết
*"nay cả 06 nằm trong bảng «🕸️ TRANG HTML QUÉT TRỰC TIẾP»"* ở một mục đứng TRƯỚC bảng thật, hàm
`text.index(<tên bảng>)` cắt lấy đoạn văn ấy và trả về **0 trang** — lớp `[HTML]` mất sạch 25 trang
(gồm toàn bộ uỷ ban Hạ viện, tức nhóm 1), đồng thời lớp RSS ăn thêm 31 request vô ích (83 → 114 feed).
Không lỗi, không cảnh báo, và bảng trong tài liệu vẫn còn nguyên nên soi bằng mắt thì thấy đủ.
- **Sau mỗi lần sửa bảng nguồn trong CLAUDE.md, chạy `tests/test-bang-nguon-claude-md.py`** — nó
  ĐẾM số trang và số feed đọc ra được, tức đo đúng thứ mắt không thấy.
- **Đã vá gốc bằng cơ chế:** `harvest._vi_tri_tieu_de()` neo vào dòng tiêu đề `### …`, và nhánh dự
  phòng chọn khối có nhiều dòng bảng nhất thay vì lùi về `text.index` (lùi về đó là mở lại đúng lỗ
  vừa bịt — ca 10 của bộ test bắt được chỗ này ngay lúc dựng). Nay tài liệu nhắc tên bảng bao nhiêu
  lần cũng được.
- **Luật chung:** mọi file mà script đọc để lấy cấu hình đều phải coi là mã nguồn. `CLAUDE.md` của
  repo này đang cấp dữ liệu cho `harvest.py` (bảng RSS + bảng HTML), `probe_sources.py`,
  `rss_check.py`, `kiem_lich.py` — sửa nó là sửa cấu hình của bốn script.

⚠️ **TEST XANH CHƯA ĐỦ — phải chứng minh test BẮT ĐƯỢC lỗi.** Mỗi file có cờ `--tu-kiem`: nó tự
dựng các bản mã nguồn **đã gỡ đúng dòng bảo vệ** rồi chạy lại chính bộ ca đó với biến môi trường
(`ADDNEWS_MOD` / `SODAGUI_DIR` / `CANARY_TIN_MOD`), và **các ca đã khai phải ĐỎ**. Xanh trên cả bản
đúng lẫn bản hỏng thì test đó vô dụng. Kết quả 29/07: 5/5 · 4/4 · 6/6 bản hỏng đều bị bắt.
Huy hỏi *"cổng đó chặn được chưa"* → câu trả lời **không bao giờ là lời hứa**, mà là chạy `--tu-kiem`
rồi đưa kết quả.

⚠️ **Bản hỏng phải nằm TRONG thư mục thật của script**, không phải `/tmp`: `add_news.py` và
`canary.py` tự suy repo root từ vị trí của chính mình (`import topics`, `from tg_api import …`,
đọc `index.html`). Để ở `/tmp` thì mọi ca đỏ vì `ImportError`/thiếu file — **đỏ vì lý do sai thì
không chứng minh được gì**. Cả hai file test đã ghi bản hỏng vào đúng thư mục rồi `unlink` trong
`finally`.

⚠️ **BẢN HỎNG ĐẶT Ở THƯ MỤC TẠM THÌ PHẢI DỰNG NGUYÊN CÂY `<tmp>/.github/scripts` +
`<tmp>/scripts`, KHÔNG copy phẳng** (vá 02/08/2026, hồi quy thật). `make_docx.py` suy đường tới
`scripts/` từ vị trí **CHÍNH NÓ** (`dirname` ba lần từ `__file__`) để `from topics import
neo_uc_bien_dong`. Copy phẳng vào một thư mục tạm thì phép suy đó trỏ ra ngoài
`/var/folders/...` ⇒ `ModuleNotFoundError` **ngay lúc nạp module** ⇒ tiến trình con không in
được một dòng `✓`/`✗` nào ⇒ `--tu-kiem` đọc thành *"KHÔNG CÓ CA NÀO ĐỎ"* hoặc *"ĐỎ TOÀN BỘ"*.
- **Đo thật:** `test-so-da-gui.py` **8/8** bản hỏng trượt, `test-tin-jaylam-trong-docx.py`
  **11/11** trượt — cùng lúc, cùng nguyên nhân.
- **Cơ chế gây vấp:** commit `8b8a993` (phiên khác) thêm import chéo thư mục vào `make_docx.py`
  và **không sửa hai bộ test dựng bản hỏng của chính file đó** — đúng luật đã đúc *"thêm cổng
  mới vào script đang có bộ test canh thì phải sửa bộ test ngay trong lượt đó"*, chỉ khác chỗ
  áp: ở đây thứ được thêm không phải cổng mà là một `import`.
- **Bảng kết quả VẪN XANH ở lượt chạy thường** — chỉ `--tu-kiem` mới lộ ra. Tức bộ test mất
  sạch khả năng chứng minh mà không dấu hiệu nào; đây là hỏng câm của chính công cụ đo hỏng câm.
- Mẫu đúng có sẵn: `_dung_ban_sao()` trong `tests/test-cong-uc-bien-dong.py`.

⚠️ **Ca thử phải ĐỌC bảng ánh xạ từ chính mã nguồn, đừng chép tay.** Đã bẫy một lần: ca `sukien`
của canary soi ô **`sang`** của pipeline `event-scan`, không phải ô `sukien` — chép tay là test đỏ
oan và tưởng cổng hỏng.

## ⛔ `vote_stats` + `vote_items` CỐ Ý CHẠY QUYỀN CHỦ SỞ HỮU — advisor kêu ERROR là kêu ĐÚNG THIẾT KẾ, ĐỪNG "VÁ"

Advisor bảo mật Supabase xếp `public.vote_stats` và `public.vote_items` vào lỗi mức **ERROR**
loại `security_definer_view` (phát hiện 14/08/2026). Ở đây đó là **chủ ý, không phải lỗi**:
hai view khai `with (security_invoker = false)` để gộp phiếu của **toàn bộ người đọc** rồi trả
về **chỉ số đếm**, cho GitHub Action `sync-preferences.yml` đọc bằng khoá công khai mà dựng
`preferences.json`. Bật `security_invoker = on` là mỗi lần Action gọi chỉ thấy phiếu của chính
nó, tức **0 dòng** ⇒ `preferences.json` rỗng ⇒ mất hẳn phần điều hướng quét theo sở thích.

Số đo nghiệm thu 14/08/2026, gọi thật bằng khoá công khai (`sb_publishable_74Lm…`):

| Đường gọi | Kết quả | Ý nghĩa |
|---|---|---|
| `GET /rest/v1/vote_stats` | trả dòng, cột `scope · key · up · down · net · total` | Action còn chạy được |
| `GET /rest/v1/vote_items` | trả dòng, cột `sign · title · category · region · source · n` | tiêu đề là tin công khai |
| `GET /rest/v1/votes` | **0 dòng** | bảng nền vẫn kín |
| `GET /rest/v1/votes?select=user_id` | **0 dòng** | danh tính người bình chọn không lọt |

Bảng nền `public.votes` đã bật RLS với đúng một policy `own_votes` (`auth.uid() = user_id`), nên
người ngoài không đọc được `user_id` lẫn từng phiếu lẻ. Toàn bộ 313 phiếu của 02 tài khoản chỉ
mang tiêu đề tin, chuyên mục, khu vực, nguồn — **không cột nào chứa tên người, số điện thoại hay
ghi chú tự do**, tức nằm ngoài lớp DANH TÍNH của mục 25 `~/.claude/CLAUDE.md`.

Hai view này đã nằm sẵn trong danh sách `BANG_MO` của `HeThong/canh-ro-ri-supabase.py` với ghi
chú "cố ý công khai". Dựng view tổng hợp mới trong nhóm này thì cùng lượt đó phải **khai vào
`BANG_MO`**, và phải đo lại 04 đường trên — thiếu ca đo bảng nền `votes` thì siết hay nới đều
không ai biết.

⚠️ Chỗ khác thì luật ngược lại: view của **Sổ Công Nợ** (`cn_v_*`) bắt buộc `security_invoker = on`
vì chúng chở dữ liệu tiền của mẹ Huy — xem `App/CongNo/CLAUDE.md`. Phân biệt bằng **nội dung view
chở**, không bằng mức advisor.

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
