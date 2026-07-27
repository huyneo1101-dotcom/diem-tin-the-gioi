# Routine HỒ SƠ ĐỘC GIẢ — 3 ngày/lần (NGUỒN SỰ THẬT DUY NHẤT)

> File này là nguồn sự thật về quy trình dựng hồ sơ sở thích đọc tin. SKILL.md của task
> `ho-so-doc-gia` chỉ là stub Read file này — **sửa quy trình thì sửa file này**, đừng sửa stub.
> Đặt trong repo chứ không phải `~/.claude/` vì vùng đó sensitive, mọi Edit đều bị hỏi quyền.

Mục đích: bản tin học dần từ chuyện người đọc **thật sự** quan tâm, thay vì đoán. Dữ liệu là
các câu hỏi người ta nhắn cho bot Telegram (`@diemtin24h_bot`).

Chạy **3 ngày một lần** (cron `0 10 */3 * *`, giờ VN). Đây là việc chậm, không có hạn chót —
lỡ một nhịp thì nhịp sau gánh, không cần cuống.

## Vì sao chạy LOCAL chứ không phải GitHub Actions

Đọc bảng `dt_bot_hoi` cần quyền cao hơn anon key. Nhét service key — thứ mở **toàn bộ**
database gồm ViNha, bi-a, Hương Diện — vào secret của một repo public là cái giá quá đắt cho
một việc chạy 10 lần/tháng. Thay vào đó có một **mã riêng chỉ mở quyền đọc 2 bảng `dt_*`**,
nằm ở `/Users/Huy/Claude/.dt-bot-key` (chmod 600, ngoài repo). Database chỉ giữ SHA-256 của
mã. Script tự đọc file đó, không cần truyền gì.

## ⚠️ MỌI LỆNH BASH PHẢI PHẲNG

Phiên này là scheduled task, nên hook `block-lenh-khong-phang.py` đang bật: lệnh chứa hàm/
brace, `$VAR`, `$(...)`, `for ... done` hay heredoc bị **chặn thẳng**. Chỉ dùng lệnh đơn,
pipe, hoặc chuỗi `&&`; đối số điền giá trị thật. Cần lặp/xử lý phức tạp thì gói vào
`python3 -c '...'` (nháy ĐƠN). Bị chặn thì **viết lại cho phẳng, KHÔNG xin quyền**.

Đường dẫn luôn TUYỆT ĐỐI, không `cd`.

## Bước 1 — Lấy số liệu

```
python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/ho_so_doc_gia.py --so-lieu
```

In ra theo từng người: số lượt hỏi, chủ đề hay hỏi, tỉ lệ trong/ngoài 5 chủ đề, giờ hay hỏi,
và các câu hỏi gần đây.

**"Không có dữ liệu" là kết quả hợp lệ** — nghĩa là chưa ai nhắn bot kể từ lần trước. Khi đó
ghi log, KHÔNG gửi Telegram (đừng làm phiền Huy bằng một tin rỗng), kết thúc.

## Bước 2 — Viết hồ sơ

Script chỉ **đếm**. Phần nhận định là việc của mày, và đây là chỗ dễ hỏng nhất:

⛔ **CHỈ VIẾT ĐIỀU ĐỌC RA ĐƯỢC TỪ CÂU HỎI THẬT.** Không suy diễn tính cách, nghề nghiệp,
quan điểm chính trị, hay hoàn cảnh cá nhân. Đây là hồ sơ **sở thích đọc tin**, không phải
chân dung con người. Huy đã bác một lần vì suy luận bắc cầu (27/07, mục khí tài) — cùng một
lỗi, ở đây hậu quả nặng hơn vì nó nói về một người thật.

Viết được: chủ đề hay hỏi và chủ đề không bao giờ đụng tới · hỏi tin mới hay hỏi bối cảnh ·
hỏi rộng ("có gì mới về X") hay hỏi điểm ("cuộc họp Fed ngày mai") · quan tâm có kéo dài qua
nhiều lần hỏi hay chỉ bật lên một lần · phần lớn câu hỏi nằm trong hay ngoài 5 chủ đề đang quét.

Không viết được: người này thân ai, làm nghề gì, nghiêng bên nào, tính cách ra sao.

Độ dài 4–8 câu cho mỗi người. Nêu cả **cái chưa biết** ("mới 3 lượt hỏi, chưa đủ để nói xu
hướng") thay vì viết chắc nịch trên dữ liệu mỏng.

## Bước 3 — Lưu

Mỗi người một file JSON rồi lưu:

```
python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/ho_so_doc_gia.py --luu /tmp/ho-so-<chat>.json
```

```json
{"chat_id": "…", "ten": "…", "tom_tat": "…",
 "chu_de_dem": {"Kinh tế Mỹ": 4, "Nga–Ukraine": 2}, "so_cau_hoi": 6}
```

Upsert theo `chat_id` — chạy lại là ghi đè hồ sơ cũ, đúng ý (hồ sơ phản ánh trạng thái mới nhất).

## Bước 4 — Gửi Huy

Một tin Telegram gọn cho chat của Huy (chat id **đầu tiên** trong `TELEGRAM_CHAT_ID`):

```
python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/telegram_bot.py --bao "<nội dung>" --chat <id>
```

Nội dung: mỗi người 2–4 dòng — hỏi bao nhiêu lần trong kỳ, quan tâm gì, **và một dòng
gợi ý cho bản tin** ("người này hỏi Nga–Ukraine 4/6 lần, mà đó là chủ đề đã cắt khỏi phạm vi
23/07 — cân nhắc mở lại hoặc để mục riêng").

Dòng gợi ý đó mới là thứ đáng tiền của cả routine này. Không có nó thì hồ sơ chỉ là thống kê.

## Bước 5 — Ghi log

Ghi `/Users/Huy/Claude/diem-tin-the-gioi/logs/ho-so-<ngày VN>.log` bằng tool Write: đã đọc
bao nhiêu lượt hỏi, viết hồ sơ cho mấy người, gửi Telegram chưa. Commit + push cùng log.
**KHÔNG commit gì khác** — routine này không đụng `index.html`.

Hỏng ở bất kỳ bước nào thì vẫn ghi log + push, và nhắn Huy một dòng nói hỏng ở đâu. Im lặng
là kiểu hỏng tệ nhất.
