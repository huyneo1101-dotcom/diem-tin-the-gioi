# Nhật ký vấp PHIÊN TỐI (đã bỏ 18/09/2026)

Dời NGUYÊN VĂN từ `docs/routine-web-scan.md` mục "PHIÊN TỐI — BỐI CẢNH RIÊNG" ngày 05/10/2026 (cắt cho phiên quét khỏi đọc 16 KB lịch sử mỗi lần khởi động).
Mốc tối không còn chạy; đọc số giờ ở đây như lịch sử, lịch thật ở [`LICH.md`](LICH.md). Phần CÒN HIỆU LỰC (bảng sổ trống hai nghĩa, lọc file Jay Lâm) vẫn nằm trong `routine-web-scan.md`.

---

## PHIÊN TỐI — BỐI CẢNH RIÊNG ⛔ ĐÃ BỎ 18/09/2026, GIỮ LÀM NHẬT KÝ VẤP

⛔ **Không còn mốc tối nào chạy.** Giữ nguyên phần này vì bốn cơ chế trong đó vẫn áp cho ca
sáng và đều là vấp thật: (i) tính biên ngược từ mốc CUỐI chứ không từ mốc đầu · (ii) cờ
`state.py` nói dối vì nó chỉ biết «đã chạy xong», không biết «đã gửi» · (iii) sổ trống có hai
nghĩa, phải đọc log run CI trước khi kết luận · (iv) chốt lô đang có khi sát hạn, đừng vòng
bổ sung. Đọc số giờ ở đây như lịch sử — lịch thật ở [`docs/LICH.md`](LICH.md).

(Dời nguyên văn từ stub task `web-scan-diem-tin-toi` ngày 27/07/2026:)

1. **Task tối là mốc LOCAL 21:15 của phiên TỐI.** Chuỗi phiên tối: CI GitHub 20:47 → **local 21:15** → CI 21:47 (lưới vét đã trễ hạn). Mốc `com.huy.routine-diemtin-sang` lo phiên SÁNG SỚM (04:30 · 04:45), không đụng tới phiên tối.

2. **HẠN CHÓT CỨNG: email bản tin tối phải tới hộp thư MUỘN NHẤT 22:00** (chỉ thị Huy 27/07/2026). Mốc local 21:15 là **lớp cuối cùng còn kịp hạn** — mốc CI 21:47 sau đó chạy xong thì email đã ~22:10, tức đã trễ. Đừng ỷ vào nó.
   - Quét mất ~20 phút (đo thật: CI 26/07 hết 20m45s, local 27/07 hết 16'), email gửi ~20 giây sau commit.
   - Mốc 21:15 cho biên ~15 phút phòng lúc fire trễ. Lý do có biên này: tối 26/07 mốc local 21:30 mãi 21:41 mới `claim` xong (jitter + khởi động session + `git pull --rebase` timeout 2 phút) — trễ 11 phút chứ không phải 3,5 phút jitter.
   - **Quá 21:45 mà chưa nạp xong thì CHỐT lô đang có**: chạy `add_news.py` với những tin đã gom được, ghi phần thiếu vào `logs/scan-gaps.json`, commit + push NGAY. Thà 3 tin sạch gửi lúc 21:50 còn hơn 8 tin gửi lúc 22:20.
   - Vì vậy: quét gọn, KHÔNG vòng bổ sung lần 3-4 để gom cho đủ chỉ tiêu, KHÔNG đi tìm thêm khi đã có tin dùng được.

3. **`claim` trả SKIP thì dừng hẳn ngay** (exit 10 = CI 20:47 đã xong, exit 11 = CI đang chạy): ghi 1 dòng SKIP vào `logs/scan-<ngày VN>.log`, commit + push log, KẾT THÚC. Không gắn Monitor, không chờ, không điều tra thêm.

   ⛔ **NGOẠI LỆ DUY NHẤT của điều 3 — exit 10 mà SỔ ĐÃ GỬI CHƯA CÓ DÒNG CỦA CA NÀY** (đúc 29/07/2026, sự cố thật). Trước khi SKIP êm ở **mốc LOCAL 21:15** (lớp cuối còn kịp hạn), đọc `logs/da-gui-email.json` và soi dòng cuối cùng có `buoi == "toi"`:
   | Sổ có dòng `toi` ngày hôm nay | Làm gì |
   |---|---|
   | **CÓ** | SKIP êm theo đúng điều 3. Bản tin đã tới tay, không quét lại |
   | **KHÔNG** | Cờ `lastSuccess` đang NÓI DỐI → **QUÉT THẬT**, commit tiền tố `Cap nhat ban tin` như thường |

   **Cơ chế gây vấp:** `state.py` chỉ ghi nhận *"pipeline đã chạy xong"*, nó **không biết bản tin có được GỬI hay không** — hai chuyện khác nhau. Tối 29/07 một **phiên TEST hạ tầng CI** (`MODE=test`, quét nhẹ 1 agent, nạp đúng +1 tin) chạy lúc **17:34** và gọi `state.py done web-scan`, chiếm luôn ô `toi` của ngày. Commit của nó rơi **ngoài khung giờ gửi** (cổng 2 của `notify-email.yml` đòi ≥20:30) nên không kích email/Telegram. Hậu quả dây chuyền: CI (khi đó 21:00, nay 20:47) → exit 10 SKIP · local 21:15 → exit 10 SKIP · CI vét → cũng sẽ SKIP. **Cả bốn lớp im lặng, không lớp nào hỏng, mà bản tin tối mất trắng.** Canary 22:45 có kêu nhưng lúc đó đã quá hạn 22:00.

   ⛔ **NHƯNG SỔ TRỐNG CÓ HAI NGHĨA — phiên LOCAL phải đọc log run CI trước khi kết luận** (đúc
   30/07/2026, sự cố thật ở phiên SÁNG SỚM; **áp cho CẢ hai phiên**, không riêng phiên tối):
   | Sổ trống vì | Dấu hiệu | Làm gì |
   |---|---|---|
   | Bản tin **thật sự chưa gửi** | không có run `notify-email.yml` nào, hoặc run ĐỎ | QUÉT THẬT theo bảng trên |
   | **Khâu GHI SỔ hỏng**, bản tin ĐÃ tới tay | run `notify-email.yml` XANH + log có dòng `Đã gửi … file .docx tới <chat>` | **KHÔNG quét lại.** Ghi bù sổ bằng `python3 .github/scripts/so_da_gui.py --ghi --buoi sang\|toi` rồi commit |

   ✅ **VÁ GỐC — ĐÃ LÀM 30/07/2026.** Luật hợp nhất sổ dời vào **`.github/scripts/ghi_so_push.py`**
   (dùng chung cho cả hai workflow): sổ là dữ liệu **append-only** nên không `pull --rebase` nữa mà
   *lấy sổ mới nhất của remote rồi ghi lại dòng của mình*, thử lại trên đỉnh mới nếu bị chen ⇒ không
   còn xung đột để mà hỏng. Chi tiết + 04 cái bẫy kèm theo: mục "🔀 HAI WORKFLOW GHI CÙNG SỔ" trong
   `CLAUDE.md`. Bộ test canh `tests/test-ghi-so-push.py` (10 ca · `--tu-kiem` bắt 6/6 bản hỏng, riêng
   bản hỏng "dùng lại `pull --rebase`" làm 6/10 ca đỏ), đã nạp vào `khoe.py`.
   ⚠️ **NHƯNG BẢNG KIỂM Ở TRÊN VẪN CẦN, ĐỪNG GỠ** — cùng lý do với cổng phiên test: vá gốc chỉ bịt
   đường *race giữa hai workflow*, còn các ca khác làm sổ trống (workflow bị huỷ giữa bước ghi, mất
   mạng cả 5 vòng, người bấm tay gửi bù) thì phép đọc `gh run list` vẫn là thứ duy nhất phân biệt được
   "chưa gửi thật" với "khâu ghi sổ hỏng".

   **Cơ chế gây vấp:** sáng 30/07 bước *"Ghi sổ đã gửi"* của `notify-email.yml` rebase hỏng
   (`could not apply … (sang)`) vì `notify-morning.yml` ghi cùng file `logs/da-gui-email.json`
   **trước đó 7 giây** — hệ quả dây chuyền của việc gộp `event-scan` vào cùng session sáng
   (28/07). Bản tin đã gửi lúc 04:28 mà sổ trống, nên: canary ca `sang` kêu oan và nhắn Telegram,
   còn hai phiên CI dự phòng (05:00 · 05:37) kết luận "mất bản tin" rồi chạy lại vòng quét bổ sung
   tốn token. Chúng không sai về lập luận — chúng **không đọc được `gh run list`** (bị chặn
   *requires approval* trong CI) nên thiếu đúng mảnh bằng chứng quyết định.

   ⇒ **Phiên LOCAL chạy trên máy Huy GỌI ĐƯỢC `gh`, đó là lợi thế phải dùng**, đừng bỏ qua rồi
   suy đoán như phiên CI:
   ```
   gh run list -R huyneo1101-dotcom/diem-tin-the-gioi --workflow notify-email.yml --limit 2 --json databaseId,createdAt,conclusion --jq '.[] | [.databaseId, .createdAt, .conclusion] | @tsv'
   gh run view <id> -R huyneo1101-dotcom/diem-tin-the-gioi --log | grep -iE 'Da gui|GUI_EMAIL|khong push duoc so'
   ```
   ⚠️ **`Đã gửi 0 message + file .docx` là BÌNH THƯỜNG, không phải hỏng** — `msgs=[]` trong
   `send_telegram.py` là cố ý (chỉ thị Huy 27/07: *"chỉ gửi file word thôi"*). Thấy `0 message`
   rồi kết luận kênh câm là đọc nhầm; bằng chứng gửi được nằm ở cụm `+ file .docx tới <chat>`.

   Vì sao phải kiểm bằng SỔ chứ không bằng `state.json`: sổ đã gửi được ghi ở **bước CUỐI sau khi đã gửi xong mọi kênh**, nên nó là dấu vết việc-đã-làm; còn `lastSuccess` chỉ là lời tự khai của một phiên. Đây đúng nguyên tắc số 1 của canary — **kiểm ĐẦU RA, không kiểm quy trình** — nay áp luôn cho chính phiên quét.

   ⛔ **KHÔNG sửa `logs/state.json` để lách.** `--force` chỉ cướp khoá `RUNNING`, không bỏ qua cờ đã-xong, và đó là **đúng thiết kế** — đừng thêm cờ mới. Không cần sửa gì cả: cổng gửi của `notify-email.yml` xét **commit message + khung giờ VN**, hoàn toàn không xét khoá, nên cứ quét rồi commit là email/Telegram vẫn đi. Mốc CI vét (21:47) sau đó vẫn thấy exit 10 và SKIP nên **không có nguy cơ quét chồng** (exit 10 khác exit 11: 10 = đã xong, 11 = đang chạy — chỉ 11 mới là dấu hiệu có phiên sống).

   ⚠️ **Ghi rõ vào `scan-gaps.json` (mục `note`) và vào log** rằng phiên này quét đè lên cờ đã-xong, kèm lý do — để người đọc sau không tưởng có hai phiên tranh nhau.

   ✅ **Vá gốc — ĐÃ LÀM 29/07/2026.** Nhánh `MODE=test` của `claude-web-scan.yml` nay chạy với biến môi trường **`DIEMTIN_PHIEN_TEST=1`** (đặt ở tầng `env:` của step quét, nên `claude -p` và mọi lệnh Bash con đều thừa hưởng — cơ chế, không phải lời hứa trong prompt). `state.py` thấy biến đó thì chuyển toàn bộ đường ghi sang `logs/state-test.json` (đã `.gitignore`): phiên test vẫn nghiệm thu được trọn pipeline `claim → beat → done`, chỉ là ghi vào sổ riêng, **không chiếm được ô khoá thật**. Nó vẫn đọc `logs/state.json` để nhường phiên THẬT đang chạy (exit 11), và **không bao giờ exit 10** vì cờ thật đã xong — test phải chạy lại được bất kể giờ nào. Ý định khai bằng lời, không suy từ `MODE`/tên workflow: mặc định là phiên THẬT, quên đặt biến thì hành vi y như cũ chứ không tạo vùng câm mới (cùng bài học với `tu_dong=1` và `TELEGRAM_BAT_BUOC`). Bộ test canh: `tests/test-cong-phien-test.py` (11 ca, 5 bản hỏng đều bị `--tu-kiem` bắt).

   ⚠️ **Nhưng ngoại lệ ở trên VẪN CẦN, đừng gỡ.** Vá gốc chỉ bịt đường `MODE=test`; đường **bấm tay `workflow_dispatch` mode=normal giữa ngày** thì vẫn `done` và chiếm ô khoá đúng như cũ, trong khi commit của nó rơi ngoài khung giờ gửi nên không kích email. Phép kiểm sổ là thứ duy nhất bắt được ca đó.

   🔁 **Từ 29/07/2026 phép kiểm này áp cho CẢ PHIÊN CI** (`.github/prompts/web-scan-ci.md` BƯỚC 1) — vì mốc **CI vét 21:47 là lớp CUỐI**, máy Mac ngủ thì không còn ai đứng sau nó. Bản CI có thêm một chốt chống kêu oan mà bản local không cần: **`lastRunAt` cách hiện tại < 20 phút thì cứ SKIP êm** — phiên anh em vừa xong, `notify-email.yml` còn đang chạy, mà sổ chỉ được ghi ở bước CUỐI nên chưa kịp hiện. Bản local 21:15 không dính ca này vì lúc đó CI 20:47 còn `RUNNING` (exit 11, không phải 10).

4. Ghi log dùng chữ **"phien toi"**. Giờ VN lúc chạy là 21:15 nên `state.py` tự chọn ô `toi`, không cần truyền gì thêm.


---

## Phụ lục — hai đoạn cắt khỏi `routine-web-scan.md` ngày 05/10/2026

**Nguyên nhân dời CI sáng:** mốc CI 04:30 cũ không nổ sáng 27/07 (GitHub hay trễ/bỏ cron lúc tải cao) mà phiên sáng khi đó không có lưới local nên mất trắng bản tin sáng. CI vì thế lên 04:00 để local 04:30 kịp gánh, rồi dời tiếp về 03:47 (cả 04 mốc sớm 13 phút) để `harvest-ci.yml` xong trước khi phiên quét bắt đầu.

**Hạn chót phiên tối cũ:** email muộn nhất 22:00 (chỉ thị Huy 27/07/2026); quá 21:45 chưa nạp xong thì chốt lô đang có, không vòng bổ sung lần 3-4. Phiên SÁNG SỚM không có hạn chót này.
