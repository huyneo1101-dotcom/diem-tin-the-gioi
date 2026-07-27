# Kênh Telegram làm nguồn tin — bảng tra của `scripts/telegram_harvest.py`

Script đọc **thẳng bảng dưới đây**: thêm/bớt kênh chỉ sửa ở một chỗ. Dòng hợp lệ phải bắt đầu
bằng `| @handle |`. Cột 3 là **hạng**, quyết định cách agent được phép dùng:

| Hạng | Nghĩa | Agent được phép làm gì |
|---|---|---|
| `osint` | Kênh tổng hợp/quan sát, không thuộc nhà nước nào | RADAR — truy về bài gốc rồi mới nạp |
| `radar` | Kênh tổng hợp tin nhanh, chất lượng không đồng đều | RADAR — bắt buộc truy gốc, không trích thẳng |
| `nhanuoc` | Truyền thông nhà nước độc tài | CHỈ dùng cho phát ngôn CỦA CHÍNH HỌ (CLAUDE.md) |
| `tonghop-vi` | Kênh tin tiếng Việt tổng hợp, **dịch lại và KHÔNG dẫn nguồn** | Nặng nhất: phải WebSearch tìm bài gốc theo nội dung; **không tìm được thì BỎ**, đúng luật trang tổng hợp trong CLAUDE.md |
| `chinhthuc` | Kênh chính thức của cơ quan nhà nước dân chủ | Tầng 1, vẫn nên link về web chính thức thay vì t.me |

⛔ **KHÔNG kênh nào trong bảng này được dùng làm `sourceUrl`.** Telegram là mạng xã hội, nằm
ngoài thang xác minh nguồn của CLAUDE.md — vai của nó đúng bằng vai `[GNEWS]` trong
`harvest.py`: phát hiện đề tài, rồi agent tự truy về thông cáo chính thức / wire / báo chuyên
ngành. Script đã trích sẵn mọi link ngoài mà bài Telegram dẫn tới để đỡ công truy ngược.

## Bảng kênh (verify bằng fetch thật 27/07/2026)

Cột **Đường** cho biết lấy được bằng cách nào: `web` = đọc được qua `t.me/s/` (không cần gì
thêm); `mtproto` = kênh TẮT xem trước web, chỉ đọc được khi chạy `--mtproto` với session
Telethon. Kênh `mtproto` vẫn để trong bảng: chạy đường web nó chỉ hiện ở dòng "không đọc
được" ở cuối, không gây lỗi.

| Kênh | Nội dung | Hạng | Đường |
|---|---|---|---|
| @AfricaIntel | Tin châu Phi & Sahel — chủ đề 4 (Mỹ–Mali) | osint | web |
| @warmonitors | Global News Monitor — xung đột toàn cầu | radar | web |
| @rnintel | Rerum Novarum — breaking + intel | radar | web |
| @BellumActaNews | Bellum Acta — intel, cảnh báo khẩn | radar | web |
| @GeneralMCNews | The General — chính trị & an ninh Mỹ, chủ đề 1 | radar | web |
| @AMK_Mapping | Bản đồ diễn biến xung đột | radar | web |
| @OSINTLive | OSINT tổng hợp | radar | web |
| @rybar_in_english | Rybar bản tiếng Anh | nhanuoc | web |
| @SputnikInt | Sputnik International | nhanuoc | web |
| @tass_agency | TASS (tiếng Nga) | nhanuoc | web |
| @OSINTdefender | Quốc phòng & xung đột toàn cầu — kênh lớn nhất mảng này | osint | web |
| @quantin | Quán Tin — chính trị quốc tế, tiếng Việt (Huy theo dõi) | tonghop-vi | web |
| @tra_da_via_he | Trà đá vỉa hè — tin thế giới 24h, tiếng Việt (Huy theo dõi) | tonghop-vi | web |
| @militarylandnet | MilitaryLand.net — bản đồ & diễn biến đơn vị | osint | mtproto |

## ⚠️ Đã dò và KHÔNG dùng được — đừng thử lại

**Không toà soạn quốc phòng nào có kênh Telegram.** Dò thật 27/07: `@DefenseNews`,
`@breakingdefense`, `@thewarzone`, `@SpaceNewsInc`, `@JanesINTEL`, `@ipdefenseforum` đều
**không tồn tại**. ⚠️ Bẫy tên: `@navalnews` **không phải** Naval News mà là kênh
"Навальный News" tiếng Nga — kiểm `og:title` trước khi tin vào handle nghe hợp lý.

**Kênh có thật nhưng TẮT xem trước web** (cần MTProto): `@militarylandnet`
(MilitaryLand.net), `@DefenceU`. **Chỉ có hai** — danh sách này từng dài hơn nhiều vì lần dò
đầu chưa phân biệt "tắt preview" với "không tồn tại".

⚠️ **VIẾT SAI HOA/THƯỜNG LÀ MẤT KÊNH.** `@sentdefender` trả về trang tắt preview, nhưng
`@OSINTdefender` — cùng kênh, viết đúng hoa — thì **web preview chạy bình thường**, 20 bài,
mới nhất trong ngày. Trước khi kết luận một kênh "phải dùng MTProto", thử lại đúng cách viết
hoa mà `og:title` trả về.

**Sống nhưng đứng quá lâu, không dùng cho tin trong ngày:** `@AustralianDefence` (17 ngày),
`@Osintlatestnews` (4 ngày), `@osinttechnical` (preview kẹt ở 27/06/2022 dù kênh còn sống),
`@PhilippineNews` (4 tháng), `@IntelSlavaZ` (4 năm), `@AZgeopolitics`, `@Faytuks`.

**Không tồn tại:** `@nato_watch`, `@ausdefence`, `@ADFnews`, `@SahelWatch`, `@JNIMwatch`,
`@AFRICOMwatch`, `@inquirerdotnet`, `@rapplerdotcom`, `@IndoPacific`, `@Taiwan_Affairs`,
`@PLAWatch`, `@SahelIntel`, `@Africa_Defense`, `@nato`, `@UN_News_Centre`, `@NATOpress`,
`@natochannel`, `@UNNews`, `@unitednations`, `@militaryland`.

**Không có kênh Telegram — thử mọi biến thể tên, ĐỪNG tìm lại:**
| Muốn tìm | Đã thử | Kết quả |
|---|---|---|
| SCSPI (theo dõi Biển Đông) | `@scspi`, `@SCS_PI`, `@SCSPI_PKU`, `@scspi_org`, `@SCS_Probing_Initiative` | `@scspi` là kênh **cá nhân tên "Silvia"**, còn lại không tồn tại |
| Indo-Pacific News | `@IndoPacificNews`, `@IndoPacific_News`, `@indopacificnews`, `@IndoPacNews` | không tồn tại |
| NATO chính thức | `@nato`, `@NATO_HQ`, `@NATOpress`, `@natochannel` | `@NATO_HQ` là kênh **giả mạo** ("NATO-HQ Usibjonov_98") |
| UN News chính thức | `@UN_News_Centre`, `@un_news`, `@UNNews`, `@unitednations` | `@un_news` là kênh **"УкрСнюс"**, không liên quan |

⚠️ **Bẫy mạo danh cơ quan là có thật** — hai trong bốn dòng trên trả về kênh mang tên gần
giống cơ quan thật. Luôn xem `og:title` (cột TÊN của `--probe`) trước khi đưa vào bảng; tên
lệch một chữ là loại. Không cơ quan chính thức nào (NATO, UN, Lầu Năm Góc) có kênh Telegram
đọc được — muốn nguồn tầng 1 thì dùng RSS/web như `harvest.py` đang làm.

## Kết luận thẳng về độ phủ (27/07/2026)

Đã dò **77 kênh**. Telegram qua đường xem trước web phủ được **chủ đề 4 (Mali/Sahel)** và một
phần **chủ đề 1 (nội bộ Mỹ)**; **KHÔNG phủ được chủ đề 2 (Úc & Biển Đông) và 3 (CNQS Mỹ)** —
mảng đó không có kênh nào vừa sống vừa đúng chuyên môn. Nhóm kênh còn sống chủ yếu là
aggregator địa chính trị chất lượng không đồng đều, nên lớp `[TG]` **bổ sung** cho RSS +
Google News chứ không thay được. Đừng kỳ vọng nó thành mỏ tin chính.
