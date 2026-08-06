# `tests/test-nguon-nghien-cuu.py --tu-kiem` HỎNG — báo chứ KHÔNG tự sửa (06/08/2026)

Cổng do phiên giám sát viết. Lệnh nghiệm thu chính **ĐẠT 18/18**; nhưng **harness `--tu-kiem`
của chính nó ra 0/3 bản hỏng bị bắt**, tức nó không chứng minh được gì. Sửa file cổng là làm
hỏng chính thứ đang đo mình, nên chỉ ghi lại đây.

## Cổng CÓ răng — đã đo riêng, đừng đọc 0/3 thành "cổng vô dụng"

Dựng 04 bản `scripts/add_analyses.py` hỏng rồi chạy cổng NGUYÊN VẸN lên chúng (qua biến
`ADD_ANALYSES`, chính seam cổng đã chừa sẵn) — **4/4 bị bắt**, mỗi bản đỏ đúng ca của nó:

| Bản hỏng | Kết quả |
|---|---|
| gỡ feed nghiên cứu Lowy khỏi `THINKTANK_FEEDS` | ĐỎ ca ★ 01 |
| gỡ `event-recordings` khỏi `NOISE_PATHS` | ĐỎ ca ★ 04 |
| hạ `MAX_AGE_DAYS_DAI` 60 → 7 | ĐỎ ca ★ 06 |
| gỡ hẳn `MAX_AGE_DAYS_DAI` | ĐỎ ca ★ 06 |

Vì vậy cổng đã nạp vào `BO_TEST` của `khoe.py` **không kèm cờ `--tu-kiem`** — khai kèm cờ là
mỗi sáng một dòng đỏ vĩnh viễn, mà bảng bị kêu oan vài lần thì hết được đọc.

## Hai chỗ hỏng trong harness

**01. Docstring hứa một đằng, mã làm một nẻo.** `tu_kiem()` khai *"Dựng bản add_analyses.py
HỎNG"*, nhưng thân hàm đọc `goc = SCRIPT.read_text(...)` rồi **không dùng** (`_ = goc` ở cuối
là dấu vết của chính chỗ hụt này); thứ nó thật sự đem đi thay là `ban_than`, tức CHÍNH FILE
CỔNG.

**02. Ba phép thay đều LÀM YẾU cổng, mà cổng yếu chạy trên bản đúng thì không thể đỏ.** Cả ba
dòng `BAN_HONG` đều gỡ hoặc vô hiệu một phép kiểm (bỏ feed Lowy khỏi bảng kiểm · đổi điều kiện
khung dài thành `True` · đổi ca đối chứng thành `True`). Gỡ một phép kiểm đang ĐẠT thì số ca
đỏ vẫn bằng 0 và mã thoát vẫn bằng 0, trong khi harness đòi `r.returncode != 0`. Điều kiện ấy
**bất khả thi theo cấu tạo**, không phải hỏng do một dòng viết nhầm.

Muốn phép mutation-của-cổng này có nghĩa thì phải có **fixture bản hỏng của SUBJECT**: dựng
`add_analyses.py` thiếu feed Lowy, rồi chứng minh cổng nguyên vẹn ĐỎ còn cổng đã bị làm yếu
thì XANH. Harness hiện không dựng fixture đó.

## Việc còn nợ

Sửa harness `--tu-kiem` của cổng — **thuộc quyền phiên giám sát**, phiên này không đụng.
Đo lại bằng: `python3 /Users/Huy/Claude/diem-tin-the-gioi/tests/test-nguon-nghien-cuu.py --tu-kiem`
(đo 06/08 10:1x: `0/3 bản hỏng bị bắt`).
