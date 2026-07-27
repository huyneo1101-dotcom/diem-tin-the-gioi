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
    "Nội bộ Mỹ": [
        "hạ viện mỹ", "thượng viện mỹ", "quốc hội mỹ", "điều trần", "phiên điều trần",
        "ủy ban quân vụ", "uỷ ban quân vụ", "thông qua dự luật", "dự luật quốc phòng",
        "ngân sách quốc phòng", "ndaa", "phê chuẩn",
    ],
}

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
    "Nội bộ Mỹ": [
        "senate armed services", "house armed services", "senate appropriations",
        "house appropriations", "congressional hearing", "testifies", "testimony",
        "markup", "committee vote", "floor vote", "house passes", "senate passes",
        "ndaa", "defense authorization", "defense appropriations", "confirmation hearing",
    ],
}


def _compile(table):
    return {
        topic: [re.compile(r"(?<!\w)" + re.escape(k) + r"(?!\w)", re.IGNORECASE) for k in kws]
        for topic, kws in table.items()
    }


_RE_VI = _compile(TOPIC_KEYWORDS_VI)
_RE_EN = _compile(TOPIC_KEYWORDS_EN)


def match_topic(text: str, lang: str = "both"):
    """Trả về tên chủ đề đầu tiên khớp, hoặc None. lang: 'vi' | 'en' | 'both'."""
    tables = []
    if lang in ("vi", "both"):
        tables.append(_RE_VI)
    if lang in ("en", "both"):
        tables.append(_RE_EN)
    for table in tables:
        for topic, pats in table.items():
            if any(p.search(text) for p in pats):
                return topic
    return None
