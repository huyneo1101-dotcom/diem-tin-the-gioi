#!/usr/bin/env python3
"""Bộ từ khoá 5 CHỦ ĐỀ dùng chung cho cả hai đường lọc tin.

MỘT nguồn sự thật cho:
  - `add_news.py`  -> cổng Báo Mới (tin tiếng VIỆT)
  - `harvest.py`   -> gom ứng viên từ RSS + Google News (tin tiếng ANH là chính)

Vì sao gộp vào đây: hai bộ từ khoá để rời ở hai file thì sớm muộn cũng lệch —
sửa một bên quên bên kia, và chỗ quên chính là chỗ tin lọt lưới.

⚠️ KHỚP THEO RANH GIỚI TỪ, không phải substring: bản đầu của cổng Báo Mới dùng
`k in text` nên "úc" khớp luôn chữ "thúc" trong "thúc đẩy tăng trưởng", lôi cả
bài kinh tế vào danh sách ứng viên.

Chỉnh từ khoá thì chỉnh Ở ĐÂY. Thấy tin đúng gu bị lọt lưới -> thêm từ khoá vào
đúng chủ đề, đừng nới lỏng ngưỡng khớp.
"""
import re
import unicodedata

# ---------------------------------------------------------------- tiếng Việt
# Dùng cho kho Báo Mới. Cố tình để RỘNG: mục đích là NHẮC cho phiên quét nhìn
# thấy, không phải tự quyết thay — thà nhắc thừa vài bài còn hơn im lặng bỏ sót.
TOPIC_KEYWORDS_VI = {
    "Úc & Biển Đông": [
        # "scarborough" TRỐNG khớp cả Scarborough ở Toronto/Maine (tai nạn xe buýt, cáo phó
        # đã lọt thật) -> bắt buộc kèm bãi cạn/shoal.
        "biển đông", "trường sa", "hoàng sa", "bãi cạn scarborough", "scarborough shoal",
        "cỏ mây", "bãi cạn",
        "đá vành khăn", "đá chữ thập", "đường lưỡi bò", "phán quyết pca", "unclos",
        "hải cảnh", "dân quân biển", "tuần duyên", "philippines", "manila",
        "balikatan", "kamandag", "aukus", "australia", "úc", "canberra",
        "tàu ngầm hạt nhân", "biển tây philippines",
        # CÁC NƯỚC KHÁC trong khu vực Biển Đông (mở rộng theo chỉ thị Huy 27/07/2026):
        # tranh chấp/tuần tra/tập trận của Malaysia, Indonesia, Brunei, Đài Loan, và
        # hoạt động của Nhật/Ấn Độ/Hàn tại vùng biển này cũng thuộc chủ đề.
        "malaysia", "indonesia", "brunei", "đài loan", "natuna", "bãi tư chính",
        "luconia", "bãi cỏ rong", "trường sa lớn", "biển hoa đông", "coc",
        "bộ quy tắc ứng xử",
        # CHIẾN TRANH VÙNG XÁM + hoạt động quân sự ở Biển Đông, và tin quân sự của Úc nói
        # chung (mở rộng theo chỉ thị Huy 02/08/2026). Bảng này là bảng GỢI Ý nên được
        # rộng; bảng NEO bên dưới vẫn hẹp, các từ vùng xám cố ý KHÔNG có ở đó vì chúng
        # không tự neo được vào vùng biển này.
        "vùng xám", "vòi rồng", "đâm va", "chiếu laser", "cắt cáp", "bồi đắp",
        "quân sự hoá", "phong toả", "raaf", "không quân hoàng gia úc", "pitch black",
        "talisman sabre", "tàu ngầm aukus",
    ],
    "CNQS Mỹ": [
        "lầu năm góc", "không quân mỹ", "hải quân mỹ", "lục quân mỹ", "thủy quân lục chiến",
        "space force", "quân đội mỹ", "bộ quốc phòng mỹ", "f-35", "f-22", "b-21", "b-2",
        "patriot", "thaad", "himars", "tomahawk", "sentinel", "minuteman", "reaper",
        "tên lửa mỹ", "drone mỹ", "uav mỹ", "hạm đội", "tàu sân bay", "khu trục",
        "siêu vượt âm", "siêu thanh", "golden dome", "phòng thủ tên lửa", "răn đe hạt nhân",
    ],
    "Mỹ – Mali": [
        "mali", "sahel", "jnim", "bamako", "africom", "burkina faso", "niger",
        "wagner", "africa corps", "tuareg", "azawad", "kidal", "gao", "timbuktu",
        "liên minh các quốc gia sahel",
    ],
    # ⛔ NHÃN CỐ ĐỊNH "Tập trận" — KHÔNG bao giờ đổi theo tên kỳ tập trận (05/08/2026).
    # Trước đây khoá này mang tên riêng ("Predator's Run", rồi "Pitch Black") và mỗi lần đổi kỳ
    # phải sửa đủ 05 chỗ; quên một chỗ là chủ đề câm trong im lặng (đã xảy ra 2 lần).
    # Danh sách dưới CỐ Ý RỖNG: từ khoá thật do `scripts/tap_tran.py::tu_khoa` sinh từ chính
    # `DATA.exercises` rồi bơm vào bằng `nap_tu_khoa_tap_tran()` lúc chạy. Để sẵn từ chung như
    # "tập trận"/"exercise" ở đây là hút mọi tin quân sự vào mục này — chủ đề 05 chỉ nhắm 1–2
    # tin/phiên nên rộng tay là hỏng cả bảng.
    "Tập trận": [],
    # 4 NHÓM theo thứ tự ưu tiên (chỉ thị Huy 27/07/2026) — nhóm 1 BẮT BUỘC tìm trước,
    # thiếu chỉ tiêu mới xuống 2, 3, 4. Xem chi tiết trong CLAUDE.md / SKILL quét tin.
    # Ở đây CHỈ để từ khoá TỰ ĐỦ (nhắc tới là biết chuyện nội bộ Mỹ). Từ khoá chung chung
    # của nhóm 3-4 (biểu tình, thuế quan, lạm phát...) nằm ở WEAK_NEED_US bên dưới vì
    # chúng cần kèm ngữ cảnh Mỹ — nếu không sẽ lôi cả tin Philippines/Singapore/Nhật vào.
    "Nội bộ Mỹ": [
        # (1) điều trần + kết quả bỏ phiếu thông qua dự luật
        "hạ viện mỹ", "thượng viện mỹ", "quốc hội mỹ", "điều trần", "phiên điều trần",
        "ủy ban quân vụ", "uỷ ban quân vụ", "thông qua dự luật", "dự luật quốc phòng",
        "ngân sách quốc phòng", "ndaa",
        # (2) sáng kiến / chiến lược của chính quyền Trump trên kênh chính thống các bộ
        "sắc lệnh hành pháp", "nhà trắng công bố", "chiến lược quốc gia",
        "bộ ngoại giao mỹ", "bộ quốc phòng mỹ", "bộ tài chính mỹ", "bộ thương mại mỹ",
        "bộ an ninh nội địa",
        # (4) kinh tế Mỹ + nội các
        "cục dự trữ liên bang", "lạm phát mỹ", "bộ trưởng mỹ",
    ],
}

# Từ khoá YẾU: tự nó không đủ để kết luận thuộc chủ đề, PHẢI kèm ngữ cảnh nước tương ứng.
# Dựng 27/07/2026 sau khi mở rộng Nội bộ Mỹ sang 4 nhóm: "protest" kéo theo tin nghị sĩ
# Philippines mặc đồ đen phản đối, "inflation" kéo theo chính sách tiền tệ Singapore và
# chi tiêu vốn Nhật Bản — đều không phải nội bộ Mỹ.
WEAK_NEED_US = {
    "Nội bộ Mỹ": [
        "sắc lệnh", "sáng kiến", "bỏ phiếu", "phê chuẩn", "nội các",
        "biểu tình", "tuần hành", "bầu cử giữa nhiệm kỳ", "bầu cử sơ bộ", "cử tri",
        "fed", "thuế quan", "trừng phạt",
        "executive order", "protest", "protests", "demonstration", "demonstrations",
        "rally", "rallies", "federal reserve", "tariff", "tariffs", "sanctions",
        "jobs report", "inflation", "cabinet meeting", "secretary announces",
        "national strategy", "fact sheet", "policy directive",
        # nhóm 5 BẦU CỬ (Huy bổ sung 27/07/2026) — vẫn là từ khoá YẾU vì "election",
        # "ballot", "campaign" xuất hiện đầy trong tin bầu cử nước khác; phải kèm ngữ cảnh Mỹ.
        "election", "elections", "midterm", "midterms", "primary election", "primaries",
        "ballot", "ballots", "voter", "voters", "turnout", "campaign trail",
        "redistricting", "gerrymander", "gerrymandering", "early voting", "absentee",
        "mail-in", "senate race", "house race", "caucus",
        "bầu cử", "cử tri", "tranh cử", "ứng cử viên", "kiểm phiếu", "phiếu bầu",
    ],
}

# Khớp theo ranh giới từ nên phải liệt kê CẢ dạng số nhiều: "midterm" không khớp "midterms"
# (thực tế lọt: "Trump administration ... ahead of midterms" bị bỏ sót ở bản đầu).
US_CONTEXT = [
    "mỹ", "hoa kỳ", "nhà trắng", "washington", "trump", "quốc hội mỹ",
    "u.s.", "us", "usa", "united states", "america", "american", "white house",
    "congress", "congressional", "capitol hill", "pentagon", "federal",
    # đảng phái / chức danh Mỹ — "House Republicans ... midterm playbook" không có chữ
    # US/America nào nhưng rõ ràng là chuyện nội bộ Mỹ
    "gop", "republican", "republicans", "democrat", "democrats",
    "senator", "senators", "lawmakers", "house republicans", "house democrats",
]

# ------------------------------------------------------------------ tiếng Anh
# Dùng cho RSS + Google News.
TOPIC_KEYWORDS_EN = {
    "Úc & Biển Đông": [
        # "scarborough" TRỐNG thì khớp cả thị trấn Scarborough (Maine, Anh) — thực tế đã lôi
        # một mục CÁO PHÓ vào danh sách ứng viên. Bắt buộc kèm "shoal"/"reef".
        "south china sea", "west philippine sea", "spratly", "paracel", "scarborough shoal",
        "scarborough reef", "second thomas shoal", "sabina shoal", "mischief reef",
        "unclos", "nine-dash",
        "china coast guard", "maritime militia", "philippine coast guard", "philippines",
        "manila", "balikatan", "kamandag", "aukus", "australia", "australian",
        # ⛔ BỎ "nuclear submarine" (28/07/2026) — TRỐNG NGỮ CẢNH y hệt bẫy "scarborough" ở trên.
        # Nó vốn thêm để bắt tàu ngầm AUKUS, nhưng khớp MỌI nước có chương trình tàu ngầm hạt
        # nhân. Lọt thật: "South Korea legislates non-nuclear weapons pledge for nuclear
        # submarine program" (Korea Herald 28/07) — tin thuần nội bộ Hàn Quốc + NPT, không một
        # chữ Biển Đông, vẫn được xếp vào "Úc & Biển Đông" và lên bản tin tối.
        # Bỏ được vì THỪA: tin tàu ngầm AUKUS luôn có "aukus"/"australia"/"australian" (đã có
        # trong danh sách này), còn tàu ngầm hạt nhân TQ/Mỹ ở vùng biển này thì khớp qua
        # "south china sea". Từ khoá tự đủ phải neo được QUỐC GIA hoặc VÙNG BIỂN, không phải
        # neo vào loại khí tài.
        "canberra", "adf", "royal australian navy", "collins-class",
        # các nước khác quanh Biển Đông (mở rộng 27/07/2026)
        "malaysia", "indonesia", "brunei", "taiwan", "natuna", "vanguard bank",
        "luconia shoals", "reed bank", "code of conduct", "asean maritime",
        # vùng xám + quân sự Úc nói chung (chỉ thị Huy 02/08/2026) — xem chú thích bản VI
        "gray zone", "grey zone", "water cannon", "ramming", "cable cutting",
        "land reclamation", "militarisation", "blockade", "raaf",
        "royal australian air force", "pitch black", "talisman sabre",
    ],
    "CNQS Mỹ": [
        "pentagon", "u.s. air force", "us air force", "u.s. navy", "us navy", "u.s. army",
        "us army", "marine corps", "space force", "darpa", "f-35", "f-22", "b-21", "b-2",
        "patriot", "thaad", "himars", "tomahawk", "sentinel", "minuteman", "reaper",
        "hypersonic", "missile defense", "golden dome", "aircraft carrier", "destroyer",
        "nuclear deterrence", "loyal wingman", "collaborative combat aircraft",
        "defense contract", "awarded a contract",
    ],
    "Mỹ – Mali": [
        "mali", "sahel", "jnim", "bamako", "africom", "burkina faso", "niger",
        "wagner", "africa corps", "tuareg", "azawad", "kidal", "timbuktu",
        "alliance of sahel states",
    ],
    # Xem chú thích ở bảng tiếng Việt — nhãn cố định, từ khoá bơm động.
    "Tập trận": [],
    # 4 NHÓM theo thứ tự ưu tiên (chỉ thị Huy 27/07/2026) — nhóm 1 tìm TRƯỚC, thiếu mới xuống 2/3/4.
    # Chỉ để từ khoá TỰ ĐỦ ở đây; từ khoá chung của nhóm 3-4 nằm ở WEAK_NEED_US (cần ngữ cảnh Mỹ).
    "Nội bộ Mỹ": [
        # (1) điều trần + bỏ phiếu thông qua dự luật
        "senate armed services", "house armed services", "senate appropriations",
        "house appropriations", "congressional hearing", "testifies", "testimony",
        "markup", "committee vote", "floor vote", "house passes", "senate passes",
        "ndaa", "defense authorization", "defense appropriations", "confirmation hearing",
        # (2) sáng kiến / chiến lược chính quyền, công bố trên kênh chính thống các bộ
        "presidential memorandum", "white house announces",
        "state department announces", "treasury announces", "commerce department",
    ],
}


# ------------------------------------------------- NEO của chủ đề 2 "Úc & Biển Đông"
# ⛔ BẢNG NÀY KHÁC HẲN `TOPIC_KEYWORDS_*["Úc & Biển Đông"]` Ở TRÊN — đừng gộp lại.
# Hai bảng phục vụ hai việc NGƯỢC CHIỀU nhau:
#   - `TOPIC_KEYWORDS_*` để GỢI Ý ứng viên  -> cố ý RỘNG, thà nhắc thừa còn hơn bỏ sót.
#   - `NEO_UC_BIEN_DONG` để CHẶN tin lạc mục -> phải HẸP, mỗi từ tự nó neo được vào
#     Úc hoặc vào Biển Đông, không cần đọc thêm câu nào khác.
#
# Vì sao có (Huy bắt 01/08/2026: *"hàn quốc liên quan đ gì đến biển đông và Úc mà cứ cho
# vào???"*): chủ đề 2 khai *"hoạt động của Nhật/Ấn/Hàn TẠI VÙNG BIỂN NÀY"*. Mệnh đề "tại
# vùng biển này" là ĐIỀU KIỆN, nhưng không cổng nào kiểm nên nó bị đọc thành "tin quốc
# phòng Nhật/Ấn/Hàn". Bản tối 01/08 lọt 03 tin: Nhật phóng Tomahawk từ JS Chokai · Trung
# Quốc phóng YJ-20 · Hàn ký 7,8 nghìn tỷ won với Hanwha Ocean — không tin nào dính Úc hay
# Biển Đông. Nay tin muốn vào mục 2 phải khớp ÍT NHẤT MỘT từ dưới đây.
#
# ⚠️ CỐ Ý KHÔNG có Nhật/Hàn/Ấn/Trung Quốc trong bảng — đó chính là điều kiện đang thiếu.
# Tin của bốn nước ấy chỉ vào mục 2 khi câu chữ tự mang một neo bên dưới (ví dụ "Japan and
# the Philippines patrol the South China Sea" khớp cả `philippines` lẫn `south china sea`).
#
# ⚠️ Viết KHÔNG DẤU: hàm so sánh bỏ dấu tiếng Việt trước khi khớp, nên "biển đông" phải
# ghi "bien dong". Ghi có dấu thì từ đó KHÔNG BAO GIỜ khớp — hỏng câm.
NEO_UC_BIEN_DONG = [
    # -- vùng biển & thực thể tranh chấp
    "bien dong", "south china sea", "west philippine sea", "bien tay philippines",
    "truong sa", "hoang sa", "spratly", "spratlys", "paracel", "paracels",
    "scarborough", "second thomas", "sabina shoal", "mischief reef", "thitu",
    "co may", "bai co rong", "reed bank", "bai tu chinh", "vanguard bank",
    "natuna", "luconia", "da vanh khan", "da chu thap", "whitsun",
    "duong luoi bo", "nine-dash", "nine dash", "unclos", "phan quyet pca",
    # ⛔ CỐ Ý KHÔNG có "bien hoa dong"/"east china sea"/"senkaku": Biển Hoa Đông là biển
    #    KHÁC. Bảng gợi ý ở trên có "biển hoa đông" (để nhắc người quét nhìn), nhưng dùng
    #    nó làm NEO thì mọi va chạm Nhật–Trung ở Senkaku lại vào mục "Úc và Biển Đông" —
    #    đúng con lỗi đang vá, chỉ đổi tên nước.
    # -- lực lượng chấp pháp đặc thù vùng biển này
    "hai canh", "china coast guard", "philippine coast guard", "pcg",
    "dan quan bien", "maritime militia",
    # ⛔ KHÔNG lấy "tuan duyen"/"coast guard" trần: tuần duyên Nhật, Hàn, Mỹ đều khớp.
    # -- các nước ven Biển Đông (khai của Huy 27/07/2026 liệt đích danh)
    "philippines", "philippine", "manila", "malaysia", "indonesia", "brunei",
    "dai loan", "taiwan", "viet nam", "vietnam", "ha noi", "hanoi",
    # -- cơ chế & tập trận gắn liền vùng biển
    "balikatan", "kamandag", "code of conduct", "bo quy tac ung xu", "asean maritime",
    # ⛔ KHÔNG lấy "coc" trần (3 ký tự, khớp bậy quá dễ) — dùng dạng viết đủ ở trên.
    # -- Úc
    "uc", "australia", "australian", "canberra", "aukus", "adf",
    "royal australian navy", "collins-class", "hmas",
    # Không quân Úc + tập trận do Úc chủ trì — thêm 02/08/2026 sau khi lỗ này làm sót
    # tin "KC-30A của Úc lần đầu tiếp dầu Rafale Ấn Độ tại Pitch Black" (Janes 31/07):
    # bảng chỉ có Hải quân, còn "australian" thì không khớp chuỗi viết tắt "RAAF".
    "raaf", "royal australian air force", "pitch black", "talisman sabre",
    "tindal", "amberley",
    # ⛔ CỐ Ý KHÔNG thêm "vung xam"/"gray zone"/"water cannon"/"voi rong": chiến tranh vùng
    #    xám thuộc PHẠM VI chủ đề (xem CLAUDE.md) nhưng KHÔNG tự neo được vào vùng biển này
    #    — vùng xám còn có ở Baltic, eo biển Đài Loan, Bắc Cực. Tin vùng xám vào mục 2 nhờ
    #    neo sẵn có ("bien dong", "philippines", "hai canh", "dan quan bien"...). Thêm vào
    #    đây là mở lại đúng lỗ Huy bắt 01/08.
    # ⛔ KHÔNG lấy tên thành phố Úc trần ("darwin", "perth", "sydney"): Darwin còn là tên
    #    người, Perth còn ở Scotland — neo phải chỉ đích danh nước hoặc vùng biển.
]

_RE_NEO = [re.compile(r"(?<!\w)" + re.escape(k) + r"(?!\w)", re.IGNORECASE)
           for k in NEO_UC_BIEN_DONG]


def bo_dau(s) -> str:
    """Bỏ dấu tiếng Việt để so khớp. `đ` -> `d` (unicodedata không tách được chữ này)."""
    s = unicodedata.normalize("NFD", str(s or "").lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn").replace("đ", "d")


def neo_uc_bien_dong(text) -> bool:
    """Văn bản có tự neo được vào Úc hoặc Biển Đông không?

    Đây là HÀM KIỂM TRA DUY NHẤT của chủ đề 2 — `add_news.py` (cổng nạp) và
    `.github/scripts/make_docx.py` (cổng dựng file Word) đều GỌI nó, không bên nào chép
    lại bảng. Hai bản chép sẽ tách nhánh ở lần vá sau mà không ai thấy.
    """
    hay = bo_dau(text)
    return any(p.search(hay) for p in _RE_NEO)


def _compile(table):
    return {
        topic: [re.compile(r"(?<!\w)" + re.escape(k) + r"(?!\w)", re.IGNORECASE) for k in kws]
        for topic, kws in table.items()
    }


_RE_VI = _compile(TOPIC_KEYWORDS_VI)
_RE_EN = _compile(TOPIC_KEYWORDS_EN)
_RE_WEAK = _compile(WEAK_NEED_US)

# Nhãn chủ đề 05. Hằng số để nơi khác đừng gõ lại chuỗi bằng tay — gõ sai một ký tự là chủ đề
# rơi khỏi `UU_TIEN_CHU_DE`/bảng kết quả mà không ai báo.
CHU_DE_TAP_TRAN = "Tập trận"


def nap_tu_khoa_tap_tran(keys):
    """Bơm từ khoá của (các) cuộc tập trận ĐANG diễn ra vào bảng phân loại, lúc chạy.

    Vì sao phải có đường bơm thay vì để bảng tĩnh: xem chú thích tại khoá `"Tập trận"` trong
    `TOPIC_KEYWORDS_VI`. `harvest.py` và `telegram_harvest.py` gọi hàm này NGAY ĐẦU phiên, sau
    khi đọc `DATA.exercises`.

    Ghi vào CẢ `TOPIC_KEYWORDS_*` lẫn bảng regex đã biên dịch — quên bảng regex thì
    `match_topic` vẫn dùng bản cũ và không có gì báo lỗi.
    Gọi nhiều lần thì GHI ĐÈ, không cộng dồn: hai cuộc kết thúc rồi mà từ khoá còn nằm lại là
    chủ đề bám tin của kỳ đã tàn.
    """
    keys = [str(k).strip() for k in (keys or []) if str(k).strip()]
    TOPIC_KEYWORDS_VI[CHU_DE_TAP_TRAN] = list(keys)
    TOPIC_KEYWORDS_EN[CHU_DE_TAP_TRAN] = list(keys)
    pats = [re.compile(r"(?<!\w)" + re.escape(k) + r"(?!\w)", re.IGNORECASE) for k in keys]
    # ⚠️ ĐƯA CHỦ ĐỀ TẬP TRẬN LÊN ĐẦU bảng duyệt. `match_topic` trả chủ đề ĐẦU TIÊN khớp, mà
    # bảng "Úc & Biển Đông" đứng trước và chứa `raaf`/`royal australian air force` — nên tiêu
    # đề thật kiểu *"Exercise Pitch Black wraps up at RAAF Darwin"* bị chủ đề 02 bắt mất ngay
    # ở LỚP RSS/HTML, nơi mỗi bài chỉ được gán MỘT nhãn nên `uu_tien_chu_de` (chỉ xử lý tranh
    # chấp giữa hai bản cùng URL) không có gì để cứu. Đo thật 05/08/2026 khi dựng ca [22].
    # Mutate TẠI CHỖ (clear+update) chứ không gán lại tên: `match_topic` giữ tham chiếu tới
    # chính object này.
    for bang in (_RE_VI, _RE_EN):
        cu = {k: v for k, v in bang.items() if k != CHU_DE_TAP_TRAN}
        bang.clear()
        bang[CHU_DE_TAP_TRAN] = list(pats)
        bang.update(cu)
    return keys
_RE_US_CTX = [re.compile(r"(?<!\w)" + re.escape(k) + r"(?!\w)", re.IGNORECASE) for k in US_CONTEXT]


def _has_us_context(text: str) -> bool:
    return any(p.search(text) for p in _RE_US_CTX)


# Nhận diện ứng viên "Nội bộ Mỹ" thuộc NHÓM nào.
# Huy chốt 27/07/2026: vét cạn nhóm 1 (điều trần + bỏ phiếu) rồi mới tới các nhóm sau.
# BỔ SUNG cùng ngày: tách **bầu cử** thành nhóm 5 RIÊNG, "ưu tiên ngang bằng với 2, 3, 4"
# (trước đó bầu cử bị gộp chung vào nhóm 3 với biểu tình).
# ⚠️ THỨ HẠNG CHỈ CÓ HAI MỨC: nhóm 1 = hạng 1; nhóm 2/3/4/5 = hạng 2, NGANG NHAU — số thứ tự
# 2→5 chỉ là NHÃN phân loại, KHÔNG phải thứ tự ưu tiên. Đừng xếp nhóm 2 trên nhóm 5.
# Nếu chỉ xếp ứng viên theo ngày thì agent sẽ toàn thấy nhóm đăng dày (biểu tình/bầu cử/thuế
# quan) và luật "nhóm 1 trước" thành vô nghĩa — nên harvest phải xếp theo HẠNG.
US_SUBGROUPS = {
    1: ["điều trần", "phiên điều trần", "thông qua dự luật", "bỏ phiếu", "ủy ban quân vụ",
        "uỷ ban quân vụ", "ndaa", "dự luật quốc phòng", "ngân sách quốc phòng",
        "hearing", "testimony", "testifies", "markup", "mark-up", "committee vote",
        "floor vote", "house passes", "senate passes", "committee approves",
        "defense authorization", "defense appropriations", "confirmation hearing"],
    2: ["sắc lệnh", "chiến lược quốc gia", "nhà trắng công bố", "sáng kiến",
        "executive order", "presidential memorandum", "white house announces",
        "national strategy", "fact sheet", "policy directive", "state department announces",
        "treasury announces", "commerce department"],
    3: ["biểu tình", "tuần hành", "đình công",
        "protest", "protests", "demonstration", "demonstrations", "rally", "rallies",
        "march on", "walkout", "strike action"],
    4: ["fed", "cục dự trữ liên bang", "thuế quan", "lạm phát", "trừng phạt", "nội các",
        "federal reserve", "tariff", "tariffs", "sanctions", "jobs report", "inflation",
        "cabinet meeting", "secretary announces"],
    # 5 — BẦU CỬ (Huy bổ sung 27/07/2026, ngang hàng 2/3/4)
    5: ["bầu cử", "bầu cử giữa nhiệm kỳ", "bầu cử sơ bộ", "cử tri", "tranh cử", "ứng cử viên",
        "kiểm phiếu", "phiếu bầu", "vận động tranh cử", "phân định khu vực bầu cử",
        "election", "elections", "midterm", "midterms", "primary election", "primaries",
        "ballot", "ballots", "voter", "voters", "turnout", "campaign trail", "candidate",
        "candidates", "redistricting", "gerrymander", "gerrymandering", "early voting",
        "absentee", "mail-in", "polling place", "senate race", "house race", "governor race",
        "dnc", "rnc", "caucus"],
}
_RE_SUB = {g: [re.compile(r"(?<!\w)" + re.escape(k) + r"(?!\w)", re.IGNORECASE) for k in kws]
           for g, kws in US_SUBGROUPS.items()}

# Hạng ưu tiên: chỉ nhóm 1 được ưu tiên tuyệt đối; 2/3/4/5 ngang nhau.
US_RANK = {1: 1, 2: 2, 3: 2, 4: 2, 5: 2, 9: 3}


def us_subgroup(text: str) -> int:
    """NHÃN nhóm 1-5 của một ứng viên Nội bộ Mỹ; 9 = không rõ (xếp cuối).

    Nhãn KHÁC hạng ưu tiên — dùng `us_rank()` để xếp thứ tự.
    """
    for g in (1, 2, 3, 4, 5):
        if any(p.search(text) for p in _RE_SUB[g]):
            return g
    return 9


def us_rank(subgroup: int) -> int:
    """Hạng ưu tiên để XẾP: 1 = điều trần/bỏ phiếu (vét trước), 2 = bốn nhóm còn lại (ngang nhau)."""
    return US_RANK.get(subgroup, 3)


def match_topic(text: str, lang: str = "both"):
    """Trả về tên chủ đề đầu tiên khớp, hoặc None. lang: 'vi' | 'en' | 'both'.

    Hai vòng: từ khoá TỰ ĐỦ trước; nếu không khớp thì mới xét từ khoá YẾU, và từ khoá yếu
    chỉ tính khi văn bản CÓ ngữ cảnh Mỹ (xem WEAK_NEED_US).
    """
    tables = []
    if lang in ("vi", "both"):
        tables.append(_RE_VI)
    if lang in ("en", "both"):
        tables.append(_RE_EN)
    for table in tables:
        for topic, pats in table.items():
            if any(p.search(text) for p in pats):
                return topic
    for topic, pats in _RE_WEAK.items():
        if any(p.search(text) for p in pats) and _has_us_context(text):
            return topic
    return None
