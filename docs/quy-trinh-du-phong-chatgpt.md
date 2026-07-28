# DỰ PHÒNG — quét bản tin TỐI bằng ChatGPT khi hết hạn mức Claude

> Dựng 28/07/2026 theo yêu cầu Huy: *"xuất cho tao quy tắc quét tin buổi tối có thể sử dụng cho
> chatgpt, đề phòng tối nay hết token"*.

**Đọc trước một điều:** ChatGPT KHÔNG có repo, KHÔNG có Bash, KHÔNG push git được. Nên nó không
thay được cả routine — nó chỉ thay được **một khâu**: thẩm định tin + viết. Ba khâu còn lại vẫn
chạy trên máy Mac bằng terminal, và **không khâu nào tốn hạn mức Claude**.

| Khâu | Ai làm | Tốn hạn mức Claude? |
|---|---|---|
| 1. Gom ứng viên (`harvest.py` — 67 RSS + trang HTML uỷ ban) | máy Mac | ❌ |
| 2. Chọn tin + kiểm ngày sự kiện + viết `summary`/`significance` | **ChatGPT** | ❌ |
| 3. Guardrail + chèn vào `index.html` (`add_news.py`) | máy Mac | ❌ |
| 4. Bản kê chủ đề thiếu + commit + push → Telegram tự gửi | máy Mac | ❌ |

---

## Bước 1 — Sinh prompt, MỖI CHỦ ĐỀ MỘT ĐOẠN CHAT RIÊNG

```bash
python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/prompt_chatgpt.py --chu-de cnqs
```

Năm giá trị: `my` (Nội bộ Mỹ) · `uc` (Úc & Biển Đông) · `cnqs` (CNQS Mỹ) · `mali` · `predator`.
Lần đầu chạy sẽ mất ~3 phút vì nó tự gọi `harvest.py --gop-ci`; các lần sau dùng lại lô đó nên
gần như tức thì. Nó tự điền **ngày cụ thể của hôm nay**, tự nhúng khối chống trùng
(`--recent-titles 20`), tự lọc ứng viên ngoài khung, và chỉ nhúng luật của đúng chủ đề đó.

⛔ **Chạy không có `--chu-de` cũng được nhưng ĐỪNG dùng cho bản tin thật.** Prompt gộp cả 5 chủ đề
là ~41.000 ký tự với ~87 link — ChatGPT sẽ mở vài cái rồi viết `summary` từ tiêu đề cho phần còn
lại, tức vi phạm luật số 1 mà không nói gì. Đây đúng là lý do playbook gốc chia **5 agent nhỏ**
thay vì một agent to (`.claude/skills/quet-tin/SKILL.md` bước 2) — đường ChatGPT cũng phải chia y
như vậy. Tách ra thì mỗi prompt còn ~20–25k ký tự, ≤20 ứng viên.

**DÁN THẲNG nội dung vào khung chat — đừng upload file .md.** Upload thì ChatGPT coi là tài liệu
tham khảo và đọc lướt; dán thẳng thì nó coi là chỉ thị. **Bật chế độ duyệt web**, không có thì nó
không mở được bài và luật số 1 sẽ bắt nó bỏ gần hết tin.

📌 File `docs/quy-trinh-du-phong-chatgpt.md` (chính file mày đang đọc) **KHÔNG dán vào ChatGPT** —
nó là hướng dẫn cho mày, đầy lệnh terminal và `git push`. Dán vào chỉ làm ChatGPT tưởng phải chạy
lệnh rồi trả về hướng dẫn thay vì JSON.

## Bước 2 — Lấy JSON về (làm lần lượt cho từng chủ đề)

Mỗi đoạn chat trả một khối JSON + một khối liệt kê chủ đề thiếu. Lưu **khối JSON** vào
`/tmp/tu-chatgpt-<chủ đề>.json` (dán cả ```json fence và lời dẫn cũng được, script tự bóc), rồi:

```bash
python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/prompt_chatgpt.py --nap /tmp/tu-chatgpt-cnqs.json
```

Nó bóc fence → validate → bỏ khoá lạ ChatGPT tự thêm → ghi `/tmp/new_items.json` → gọi
`add_news.py`. Guardrail chặn thì nó in rõ tin nào lỗi: sửa/bỏ tin đó trong
`/tmp/new_items.json` rồi chạy lại `python3 scripts/add_news.py /tmp/new_items.json`.

Nạp **từng chủ đề một, nhiều lần** là an toàn — `add_news.py` cộng dồn, và lần chạy CUỐI quyết định
`DATA.generatedAt` (nhớ để `date` của bản kê ở bước 3 khớp giá trị đó).

## Bước 3 — Bản kê chủ đề thiếu (BẮT BUỘC, đừng bỏ)

Không có file này thì tin nhắn Telegram **mất hẳn** mục "Chủ đề thiếu và lý do". Lấy khối liệt kê
ChatGPT viết ở bước 2 làm nguyên liệu, ghi vào `logs/scan-gaps.json`:

```json
{
  "date": "<PHẢI khớp DATA.generatedAt sau khi chạy add_news.py>",
  "session": "toi",
  "topics": [
    {"name":"Nội bộ Mỹ (điều trần + bỏ phiếu dự luật)","count":6,"target":"5-10","min":5,"thieu":false,"reason":""},
    {"name":"Úc & Biển Đông","count":5,"target":"5-10","min":5,"thieu":false,"reason":""},
    {"name":"Công nghệ quân sự Mỹ","count":0,"target":"5-10","min":5,"thieu":true,
     "reason":"Mọi ứng viên hoặc trùng sự kiện đã nạp, hoặc sự kiện thật ngoài khung dù đăng lại hôm nay."},
    {"name":"Mỹ – Mali","count":0,"target":"2-5","min":2,"thieu":true,"reason":"..."},
    {"name":"Predator's Run 2026","count":0,"target":"1-2","min":1,"thieu":true,"reason":"..."}
  ],
  "note": "Phiên quét dự phòng bằng ChatGPT (hết hạn mức Claude)."
}
```

Lấy `date` đúng bằng: `grep -oE '"generatedAt":"[^"]+"' index.html | head -1`

## Bước 4 — Nhả khoá + push

```bash
python3 /Users/Huy/Claude/diem-tin-the-gioi/scripts/state.py done web-scan "quet bang ChatGPT: +N tin"
git -C /Users/Huy/Claude/diem-tin-the-gioi add index.html logs/
git -C /Users/Huy/Claude/diem-tin-the-gioi commit -m "Cap nhat ban tin DD/MM: +N tin (5 chu de)"
git -C /Users/Huy/Claude/diem-tin-the-gioi push origin main
```

Push xong là **xong** — `notify-email.yml` tự dựng file Word `Diem-tin-toi-21h-<ngày>.docx` và gửi
Telegram, không cần Claude tí nào.

⚠️ **`state.py done` KHÔNG được bỏ.** Bỏ nó thì mốc CI 21:47 thấy chưa ai xong sẽ quét lại — vừa
tốn đúng cái hạn mức mày đang tiết kiệm, vừa có thể nạp trùng.
⚠️ Commit phải bắt đầu bằng **`Cap nhat ban tin`** và push **sau 20:30** giờ VN, nếu không cổng
khung giờ của `notify-email.yml` chặn và Telegram im.

---

## Ba cái bẫy của đường ChatGPT

**1. Ngày ĐĂNG ≠ ngày SỰ KIỆN — đây là chỗ hỏng nhiều nhất.** Nhiều trang đăng lại tin cũ với ngày
mới. Ca thật: bài "US House passes $1.15 trillion defence bill" hiện ngày 26/07 nhưng cuộc bỏ phiếu
diễn ra 22/07. Prompt đã dặn, nhưng khi soi JSON ChatGPT trả về thì **tự mở lại 2–3 link đáng ngờ
nhất** để kiểm — `add_news.py` chỉ so được `date` mày ghi, nó không biết ngày sự kiện thật.

**2. Guardrail KHÔNG bắt trùng SỰ KIỆN.** Nó chỉ bắt trùng URL và tiêu đề giống ≥ 60%. Cùng một
sự kiện mà khác nguồn, khác cách quy đổi số liệu thì lọt cả hai lớp (ca thật 25/07: "Úc rót 4,6 tỷ
AUD cho xưởng tàu ngầm AUKUS" trùng tin đã có "Australia đầu tư 3,2 tỷ USD cho tàu ngầm hạt nhân
AUKUS" — cùng số tiền, khác đơn vị). Sau khi nạp, grep từ khoá riêng của từng tin:

```bash
grep -o '"title":"[^"]*"' /Users/Huy/Claude/diem-tin-the-gioi/index.html | grep -i "<tu khoa>"
```

Ra 2 dòng cùng sự kiện → xoá bản mới bằng `python3 scripts/prune_news.py <file_urls.txt>`. **Không
sửa tay `index.html`.**

**2b. Chạy `--nap` là ĐỘNG THẬT vào `index.html`, kể cả với lô RỖNG.** `add_news.py` bump
`generatedTime` mỗi lần chạy, nên một lần chạy thử cũng để lại `M index.html`. Muốn thử nghiệm thì
xong việc nhớ `git -C /Users/Huy/Claude/diem-tin-the-gioi checkout -- index.html`, đừng để tồn dư —
tồn dư chưa commit làm **nghẽn `git pull --rebase` ở bước 1 của mọi phiên routine sau** (gặp thật
sáng 27/07).

**3. ChatGPT bịa `summary` từ tiêu đề khi không mở được bài.** Prompt có luật "không mở được thì
BỎ", nhưng đây là loại lỗi guardrail không thấy được: tin trông sạch, link mở được, mà nội dung
tóm tắt sai. Nếu thấy `summary` chung chung không có con số/tên riêng/địa danh cụ thể → nghi ngay,
mở bài kiểm.

## Chất lượng so với đường Claude

Thật thà: **thấp hơn**, và chỗ hụt nằm đúng ở khâu phán đoán — truy bài gốc từ trang tổng hợp, phát
hiện ngày sự kiện lệch ngày đăng, nhận ra trùng sự kiện khác URL, và chịu trả về rỗng thay vì nhồi
cho đủ số. Đó là lý do bước 1 đưa sẵn ứng viên có link thật cho ChatGPT: giảm việc phán đoán xuống
mức thấp nhất có thể.

Dùng cái này khi **hết hạn mức**, không dùng thay đường chính.

## Sửa quy tắc thì sửa ở đâu

Nguồn sự thật vẫn là `.claude/skills/quet-tin/SKILL.md` + `CLAUDE.md` gốc repo. Luật trong
`scripts/prompt_chatgpt.py` là **bản sao rút gọn** cho ChatGPT — đổi phạm vi quét thì sửa hai file
gốc trước, rồi mới đối chiếu lại hàm `sinh()` trong script. Đừng để hai bộ luật lệch nhau âm thầm.
