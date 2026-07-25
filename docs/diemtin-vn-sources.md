# Báo Việt Nam uy tín — nguồn quét cho Điểm Tin Thế Giới

> **🔀 ĐÃ GỘP 25/07/2026** — 5 nguồn VN còn sống (VietnamPlus, Nhân Dân, Báo Chính phủ, VietnamNet,
> Báo Thế giới & Việt Nam) đã vào bảng RSS trong `CLAUDE.md`, mục **"Gộp từ kho tư liệu cũ"**.
> Nhắc lại: nguồn VN là **ưu tiên #2** — tiếng Anh trước. File này giờ là kho tra cứu.

> Danh sách báo VN uy tín cho tác vụ `diemtin-cap-nhat-hang-ngay` (mục Thế giới & Mỹ, và mục quân sự).
> **Lợi thế:** tiếng Việt (khỏi dịch), ít bị chặn, fetch tốt. Dùng chuyên mục **Thế giới / Quốc tế** của báo.
> `sourceName` = tên báo VN; `sourceUrl` = bài trên báo VN (kể cả khi bài dẫn lại nguồn quốc tế).
> Tác vụ `diemtin-mo-rong-x-accounts` (19h) tự BỒI thêm báo VN uy tín MỚI vào đây hằng ngày (chỉ báo chính thống, đã kiểm fetch được, không trùng). Sửa tay cũng được.

## Đã kiểm fetch được (dùng ngay)
- **VnExpress** — https://vnexpress.net/the-gioi · RSS: `https://vnexpress.net/rss/the-gioi.rss` (kiểm 09/07 = 60 mục ✓)
- **Tuổi Trẻ** — https://tuoitre.vn/the-gioi.htm · RSS: `https://tuoitre.vn/rss/the-gioi.rss` (kiểm 09/07 = 50 mục ✓)
- **Thanh Niên** — https://thanhnien.vn/the-gioi.htm · RSS: `https://thanhnien.vn/rss/the-gioi.rss` (kiểm 09/07 = 50 mục; ⚠️ có mã hoá HTML entity, giải mã khi parse ✓)
- **VietnamNet** — https://vietnamnet.vn/the-gioi · RSS: `https://vietnamnet.vn/rss/the-gioi.rss` (kiểm 09/07 = 1000 mục, RẤT giàu ✓)
- **Znews** — https://znews.vn/the-gioi.html · RSS: `https://znews.vn/rss/the-gioi.rss` (⚠️ đuôi `.rss`, kiểm 09/07 = 46 mục)
- **Dân Trí** — https://dantri.com.vn/the-gioi.htm · RSS: `https://dantri.com.vn/rss/the-gioi.rss` (kiểm 09/07 = 100 mục ✓)

### Thông tấn / chính thống (thêm 2026-07-09, đã kiểm fetch)
- **VietnamPlus (TTXVN)** — https://www.vietnamplus.vn/thegioi.vnp · RSS: `https://www.vietnamplus.vn/rss/thegioi.rss` (kiểm 09/07 = 50 mục ✓)
- **Báo Tin Tức (TTXVN)** — https://baotintuc.vn/the-gioi.html · RSS: `https://baotintuc.vn/the-gioi.rss` (dạng này chạy, KHÔNG có `/rss/`; kiểm 09/07)
- **Nhân Dân** — https://nhandan.vn/thegioi · RSS: `https://nhandan.vn/rss/thegioi-1231.rss` (kiểm 09/07 = 50 mục ✓)
- **VOV** — https://vov.vn/the-gioi · ⚠️ RSS chặn bot (403 mọi biến thể, kiểm 09/07) → crawl HTML
- **Báo Chính phủ** — https://baochinhphu.vn/quoc-te.htm · RSS: `https://baochinhphu.vn/quoc-te.rss` (KHÔNG có `/rss/`, giống `home.rss`; kiểm 09/07 = 50 mục ✓)
- **VTV (Đài Truyền hình VN)** — https://vtv.vn/the-gioi.htm · RSS: `https://vtv.vn/rss/the-gioi.rss` (kiểm 09/07 = 500 mục, RẤT giàu nhưng lẫn thời tiết/đời sống → LỌC theo 4 chủ đề ✓)
### Ngoại giao chuyên sâu
- **Báo Thế giới & Việt Nam (Bộ Ngoại giao)** — https://baoquocte.vn/the-gioi · RSS: `https://baoquocte.vn/rss_feed/` (feed "Thế giới 24h"; `/rss/the-gioi.rss` = 404, dùng URL này; kiểm 09/07 = 25 mục)
### Kinh tế / tài chính quốc tế
- **VnEconomy** — https://vneconomy.vn/the-gioi.htm · RSS: `https://vneconomy.vn/the-gioi.rss` (kiểm 09/07 = 50 mục ✓)
- **CafeF** — https://cafef.vn/tai-chinh-quoc-te.chn · RSS: `https://cafef.vn/tai-chinh-quoc-te.rss` (kiểm 09/07 = 50 mục; tài chính quốc tế, LỌC bỏ tin nội địa/đời sống ✓)
- **Báo Đầu tư** — https://baodautu.vn/quoc-te-d3/ · ⚠️ RSS `quoc-te.rss`/`quoc-te-d3.rss` trả feed RỖNG (kiểm 09/07) → crawl HTML
### Tổng hợp thêm
- **Sài Gòn Giải Phóng** — https://www.sggp.org.vn/thegioi/ · ⚠️ không tìm được RSS (mọi mẫu 404, kiểm 09/07) → crawl HTML
- **Tiền Phong** — https://tienphong.vn/the-gioi/ · RSS: `https://tienphong.vn/rss/the-gioi-5.rss` (⚠️ ĐÚNG id **5**; `the-gioi-12` là mục pháp luật/nội địa — SAI; kiểm 09/07 = 50 mục ✓)
- **Công an Nhân dân** — https://cand.vn/the-gioi · ⚠️ RSS `cand.vn/rss/the-gioi.rss` trả tin PHÁP LUẬT nội địa (sai mục, kiểm 09/07) → crawl HTML mục Thế giới
- **Báo Nghệ An** — https://baonghean.vn/quoc-te · ⚠️ RSS `quoc-te.rss` trả feed RỖNG, không lộ `<link rss>` (kiểm 09/07) → crawl HTML

### Tổng hợp / aggregator (thêm 2026-07-09, đã kiểm fetch)
- **Báo Mới — Thế giới** — https://baomoi.com/the-gioi.epi
- **Báo Mới — Kinh tế** — https://baomoi.com/kinh-te.epi
- **Báo Mới — Khoa học công nghệ** — https://baomoi.com/khoa-hoc-cong-nghe.epi (thêm 2026-07-09, đã kiểm fetch)
  > CHỦ YẾU công nghệ tiêu dùng/khoa học/y tế → phần lớn LOẠI TRỪ theo scope 4 chủ đề. CHỈ lấy bài có góc **quốc phòng/CNQS** (drone chiến sự, khí tài…) hoặc **địa chính trị/kinh tế công nghệ** (AI chủ quyền quốc gia, bán dẫn, cạnh tranh công nghệ nước lớn, chính sách công nghệ chiến lược). KHÔNG lấy review máy/gadget/thủ thuật/tin khoa học-y tế thường.
  > Là trang TỔNG HỢP (gom bài từ nhiều báo VN) → tốt để BẮT tin đang nóng. Khi đăng nên ưu tiên dẫn link BÀI GỐC ở báo nguồn (Báo Mới có ghi nguồn); nếu không lấy được link gốc thì dẫn Báo Mới cũng được. `sourceName` = tên báo gốc nếu biết, không thì "Báo Mới".

> ⚠️ ĐÃ BỎ bản tiếng Anh khi đã có bản tiếng Việt: VnExpress International (e.vnexpress.net), Vietnam News (vietnamnews.vn), Tuoi Tre News (tuoitrenews.vn).

## Quốc phòng / quân sự (nếu fetch được)
<!-- Báo Quân đội Nhân dân, ANTĐ... tác vụ mở rộng tự thêm nếu kiểm fetch được -->

## Ghi chú
- Chỉ báo CHÍNH THỐNG, uy tín. KHÔNG thêm trang lá cải/tổng hợp không rõ nguồn.
- Trước khi thêm một báo mới: PHẢI WebFetch thử chuyên mục thế giới của nó → mở được (200, có nội dung) mới thêm; 404/redirect-loop/tường phí → bỏ.
