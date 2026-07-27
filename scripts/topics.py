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
    "Predator's Run": ["predator's run", "predator run", "townsville", "carabaroo"],
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
        "canberra", "adf", "royal australian navy", "nuclear submarine", "collins-class",
        # các nước khác quanh Biển Đông (mở rộng 27/07/2026)
        "malaysia", "indonesia", "brunei", "taiwan", "natuna", "vanguard bank",
        "luconia shoals", "reed bank", "code of conduct", "asean maritime",
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
    "Predator's Run": ["predator's run", "predators run", "townsville", "carabaroo"],
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


def _compile(table):
    return {
        topic: [re.compile(r"(?<!\w)" + re.escape(k) + r"(?!\w)", re.IGNORECASE) for k in kws]
        for topic, kws in table.items()
    }


_RE_VI = _compile(TOPIC_KEYWORDS_VI)
_RE_EN = _compile(TOPIC_KEYWORDS_EN)
_RE_WEAK = _compile(WEAK_NEED_US)
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
