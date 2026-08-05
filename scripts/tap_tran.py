#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Nguồn sự thật DUY NHẤT về "cuộc tập trận nào đang diễn ra" — dựng 05/08/2026.

> Chỉ thị Huy 05/08/2026, nguyên văn: *"Đang có tập trận nào thì chỉ tập trung quét thông tin
> về tập trận đó. Tự động mở rộng nguồn quét tuỳ theo tập trận để tìm được tối đa thông tin."*

## Lỗ mà module này bịt

Trước đây chủ đề 05 **neo CỨNG vào tên một kỳ tập trận** (`"Predator's Run"`, rồi `"Pitch
Black"`) rải ở **05 chỗ**: `harvest.py::GNEWS_QUERIES` · `harvest.py::UU_TIEN_CHU_DE` +
danh sách in cuối · `telegram_harvest.py::order` · `topics.py` (HAI bảng) · `prompt_chatgpt.py`
(khối luật + mẫu JSON + tên khoá CLI). Kỳ tập trận kết thúc mà quên sửa một chỗ là **chủ đề 05
câm trong im lặng** — đã xảy ra thật hai lần (02/08/2026 ghi lại đủ trong CLAUDE.md): mục báo
`0 bài` mỗi phiên trong khi cuộc tập trận mới chạy rầm rộ, và bảng kết quả vẫn đủ 5 dòng nên
đọc vào chỉ tưởng hôm đó không có tin.

Nay nhãn chủ đề là hằng **`"Tập trận"`** (không bao giờ đổi), còn **NỘI DUNG** — từ khoá, truy
vấn, nguồn — sinh ĐỘNG từ chính `DATA.exercises` mỗi lần chạy. Đổi kỳ tập trận không phải sửa
dòng mã nào: chỉ cần cuộc mới có mặt trong `DATA.exercises` với `dates` đúng khuôn.

## Ba cái bẫy đã đo, đừng vấp lại

⛔ **KHÔNG tin trường `status` trong DATA.** Đo thật 05/08/2026: `Predator's Run 2026` (kết thúc
29/07) và `RIMPAC 2026` (kết thúc 31/07) đều **vẫn mang `status: "ongoing"`** — web không hiển
thị sai vì nó tự suy bằng `effStatus` từ `dates`, nên không ai buồn sửa `status`. Quét theo
`status` thì hôm nay đi tìm tin cho 03 cuộc, 02 trong đó đã tàn: vừa tốn truy vấn vừa đẩy chủ
đề vào cảnh "có ứng viên nhưng toàn tin cũ". `status` ở đây CHỈ là fallback khi `dates` không
parse nổi ngày (`"Tháng 9/2026"`).

⚠️ **`doc_dai_ngay` là bản Python của `index.html::evRange` — hai bản luật song song.** Không
tránh được (web chạy JS, harvest chạy Python), nên: thứ tự 03 mẫu regex phải GIỮ NGUYÊN như
bên JS — mẫu "ngày/tháng - ngày/tháng/năm" phải thử TRƯỚC, nếu không `"20/7 - 7/8/2026"` bị
mẫu "chung tháng" bắt nhầm thành 20→7 tháng 8. Ca test đọc thẳng `index.html` và so kết quả
hai bên trên cùng bộ chuỗi.

⚠️ **Nước chủ trì suy từ `name` + `location` + `summary`, và có thể ra NHIỀU nước** — tập trận
đa quốc gia là chuyện thường (Pitch Black 20 nước). Lấy hết, vì mục đích là MỞ RỘNG nguồn chứ
không phải phân loại; sai một nước chỉ tốn thêm một truy vấn, còn sót một nước là mất nguồn
tầng 1 của chính nước chủ nhà.
"""
import io
import json
import os
import re
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
INDEX = os.path.join(ROOT, "index.html")


def _khong_dau(s):
    s = unicodedata.normalize("NFD", str(s or "").lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn").replace("đ", "d")


def doc_exercises(duong_dan=None):
    """Đọc mảng `DATA.exercises` từ index.html.

    Fail-OPEN có tiếng: file thiếu/hỏng thì trả `[]` và để bên gọi kêu. Chặn cứng ở đây là
    làm cả lượt harvest chết vì một mục phụ — mất bản tin tệ hơn mất một chủ đề.
    """
    p = duong_dan or INDEX
    try:
        h = io.open(p, encoding="utf-8").read()
    except Exception:
        return []
    i = h.find("var DATA")
    if i < 0:
        return []
    i = h.find("{", i)
    d, j = 0, i
    while j < len(h):
        if h[j] == "{":
            d += 1
        elif h[j] == "}":
            d -= 1
            if d == 0:
                break
        j += 1
    try:
        D = json.loads(h[i:j + 1])
    except Exception:
        return []
    exs = D.get("exercises")
    return exs if isinstance(exs, list) else []


def doc_dai_ngay(dates):
    """Bản Python của `index.html::evRange`. Trả (a, b) dạng số YYYYMMDD, hoặc None.

    THỨ TỰ 03 MẪU PHẢI GIỮ NGUYÊN — xem cảnh báo ở docstring đầu file.
    """
    s = re.sub(r"[–—]", "-", str(dates or ""))
    m = re.search(r"(\d{1,2})/(\d{1,2})\s*-\s*(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if m:
        d1, mo1, d2, mo2, y = (int(x) for x in m.groups())
        return (y * 10000 + mo1 * 100 + d1, y * 10000 + mo2 * 100 + d2)
    m = re.search(r"(\d{1,2})\s*-\s*(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if m:
        d1, d2, mo, y = (int(x) for x in m.groups())
        return (y * 10000 + mo * 100 + d1, y * 10000 + mo * 100 + d2)
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if m:
        d, mo, y = (int(x) for x in m.groups())
        return (y * 10000 + mo * 100 + d, y * 10000 + mo * 100 + d)
    return None


def trang_thai(ex, hom_nay):
    """`ongoing` / `upcoming` / `recent`. `hom_nay` là chuỗi 'YYYY-MM-DD' giờ VN."""
    r = doc_dai_ngay(ex.get("dates"))
    if not r:
        return ex.get("status") or "recent"
    p = str(hom_nay).split("-")
    try:
        t = int(p[0]) * 10000 + int(p[1]) * 100 + int(p[2])
    except Exception:
        return ex.get("status") or "recent"
    a, b = r
    return "upcoming" if t < a else ("recent" if t > b else "ongoing")


def dang_dien_ra(exs, hom_nay, sap_toi_ngay=7):
    """Cuộc ĐANG diễn ra; không có cuộc nào thì lấy cuộc SẮP diễn ra trong `sap_toi_ngay`.

    Vì sao có nhánh "sắp diễn ra": giữa hai kỳ tập trận luôn có quãng trống, mà tin chuẩn bị
    (điều quân, khai mạc, danh sách nước tham gia) rơi đúng vào quãng đó. Không có nhánh này
    thì chủ đề 05 lại về 0 bài — đúng cảnh vừa đi vá.
    """
    ongoing = [e for e in exs if trang_thai(e, hom_nay) == "ongoing"]
    if ongoing:
        return ongoing
    gan = []
    for e in exs:
        if trang_thai(e, hom_nay) != "upcoming":
            continue
        r = doc_dai_ngay(e.get("dates"))
        if not r:
            continue
        p = str(hom_nay).split("-")
        try:
            import datetime
            t = datetime.date(int(p[0]), int(p[1]), int(p[2]))
            a = datetime.date(r[0] // 10000, (r[0] // 100) % 100, r[0] % 100)
        except Exception:
            continue
        if 0 <= (a - t).days <= sap_toi_ngay:
            gan.append(e)
    return gan


def ten_ngan(name):
    """`"Pitch Black 2026 (Úc chủ trì, 20 nước tham gia)"` → `"Pitch Black 2026"`.

    Cắt ở dấu ngoặc đơn và ở dấu gạch nối có khoảng trắng (`"Hán Quang 42 - Han Kuang 2026"`
    → `"Hán Quang 42"`). Tên trong ngoặc là phần mô tả, đưa vào truy vấn chỉ làm nhiễu.
    """
    s = str(name or "").split("(")[0]
    s = re.split(r"\s+[-–—]\s+", s)[0]
    return s.strip()


def ten_khong_nam(ten):
    """Bỏ đuôi năm/số hiệu: `"Pitch Black 2026"` → `"Pitch Black"`, `"Neptune Strike 26-3"`
    → `"Neptune Strike"`. Đây mới là cụm báo chí hay dùng làm tên riêng."""
    return re.sub(r"\s+\d[\d\-/]*$", "", str(ten or "")).strip()


# Nước → nguồn tầng 1 + báo bản địa. Dùng để MỞ RỘNG truy vấn theo nước chủ nhà của kỳ tập
# trận đang chạy (chỉ thị Huy 05/08/2026). Khoá là chuỗi ĐÃ BỎ DẤU, viết thường.
# ⚠️ Đây là bảng gợi ý cho truy vấn Google News, KHÔNG phải bảng neo chủ đề — được phép rộng.
NGUON_THEO_NUOC = {
    "uc": ["defence.gov.au", "airforce.gov.au", "navy.gov.au", "army.gov.au",
           "australiandefence.com.au", "defenceconnect.com.au", "abc.net.au"],
    "my": ["war.gov", "dvidshub.net", "pacom.mil", "navy.mil", "marines.mil", "af.mil"],
    "nhat": ["mod.go.jp", "japantimes.co.jp", "asia.nikkei.com"],
    "an do": ["pib.gov.in", "thehindu.com", "idrw.org"],
    "philippines": ["pna.gov.ph", "inquirer.net", "rappler.com", "philstar.com"],
    "indonesia": ["thejakartapost.com", "antaranews.com"],
    "malaysia": ["thestar.com.my", "nst.com.my"],
    "singapore": ["mindef.gov.sg", "straitstimes.com"],
    "han quoc": ["mnd.go.kr", "en.yna.co.kr", "koreaherald.com"],
    "anh": ["gov.uk", "forces.net", "ukdefencejournal.org.uk"],
    "phap": ["defense.gouv.fr", "opex360.com"],
    "canada": ["canada.ca", "ottawacitizen.com"],
    "new zealand": ["nzdf.mil.nz", "rnz.co.nz"],
    "duc": ["bmvg.de", "hartpunkt.de"],
    "ukraine": ["mil.gov.ua", "kyivindependent.com"],
    "dai loan": ["mnd.gov.tw", "taipeitimes.com", "focustaiwan.tw"],
    "trung quoc": ["mod.gov.cn", "scmp.com"],
    "nga": ["tass.com"],
    "peru": ["gob.pe", "elcomercio.pe"],
    "iceland": ["government.is"],
    "romania": ["mapn.ro"],
    "na uy": ["forsvaret.no"],
    "ba lan": ["gov.pl"],
}

# Nhận nước từ chữ trong `name` + `location` + `summary`. Mỗi nước vài cách gọi, viết KHÔNG
# DẤU vì so sau khi bỏ dấu. Cố ý KHÔNG dùng `topics.py` — bảng bên đó phục vụ phân loại chủ
# đề, trộn vào là hai việc khác nhau dùng chung một bảng rồi kéo nhau lệch.
TU_NHAN_NUOC = {
    "uc": ["uc", "australia", "australian", "raaf", "adf", "darwin", "tindal", "amberley",
           "queensland", "townsville"],
    "my": ["my", "hoa ky", "u.s.", "us ", "american", "pentagon", "usaf", "usmc", "hawaii"],
    "nhat": ["nhat", "japan", "jasdf", "jmsdf"],
    "an do": ["an do", "india", "indian", "uttarakhand"],
    "philippines": ["philippines", "manila", "luzon", "palawan"],
    "indonesia": ["indonesia", "jakarta", "natuna"],
    "malaysia": ["malaysia", "kuala lumpur"],
    "singapore": ["singapore"],
    "han quoc": ["han quoc", "korea", "seoul"],
    "anh": ["anh quoc", "united kingdom", "royal navy", "royal air force", "portland", "britain"],
    "phap": ["phap", "france", "french"],
    "canada": ["canada", "canadian"],
    "new zealand": ["new zealand", "nzdf"],
    "duc": ["duc", "germany", "german"],
    "ukraine": ["ukraine", "ukrainian", "odesa"],
    "dai loan": ["dai loan", "taiwan", "taipei"],
    "trung quoc": ["trung quoc", "china", "chinese", "pla"],
    "nga": ["nga ", "russia", "russian"],
    "peru": ["peru"],
    "iceland": ["iceland"],
    "romania": ["romania"],
    "na uy": ["na uy", "norway"],
    "ba lan": ["ba lan", "poland"],
}


# Tên dùng trong truy vấn tiếng Anh. Bảng RIÊNG, không suy từ khoá bằng `.replace()` — đã
# vấp thật lúc dựng: `nuoc.replace("uc","Australia")` biến "trung quoc" thành "trung qAustralia".
TEN_ANH = {
    "uc": "Australia", "my": "US", "nhat": "Japan", "an do": "India",
    "philippines": "Philippines", "indonesia": "Indonesia", "malaysia": "Malaysia",
    "singapore": "Singapore", "han quoc": "South Korea", "anh": "UK", "phap": "France",
    "canada": "Canada", "new zealand": "New Zealand", "duc": "Germany",
    "ukraine": "Ukraine", "dai loan": "Taiwan", "trung quoc": "China", "nga": "Russia",
    "peru": "Peru", "iceland": "Iceland", "romania": "Romania", "na uy": "Norway",
    "ba lan": "Poland",
}


def _nuoc_trong(chuoi):
    """Nước nhận ra trong một chuỗi, xếp theo VỊ TRÍ XUẤT HIỆN (sớm nhất trước).

    Xếp theo vị trí chứ không theo thứ tự khai trong dict: nước chủ nhà gần như luôn được
    nhắc trước trong `name`/`location`, còn thứ tự dict thì tuỳ người gõ.
    """
    kho = _khong_dau(chuoi)
    tim = []
    for nuoc, tu in TU_NHAN_NUOC.items():
        vt = min((kho.find(t) for t in tu if kho.find(t) >= 0), default=-1)
        if vt >= 0:
            tim.append((vt, nuoc))
    return [n for _, n in sorted(tim)]


def cac_nuoc(ex):
    """Mọi nước dính tới cuộc tập trận, suy từ name + location + summary + scale."""
    return _nuoc_trong(" ".join(str(ex.get(k, "")) for k in
                                ("name", "location", "summary", "scale")))


def nuoc_chu_nha(ex):
    """Nước ĐĂNG CAI — dùng để chọn nguồn bản địa cho truy vấn.

    ⚠️ Suy từ `location` TRƯỚC, `name` sau, KHÔNG dùng `cac_nuoc()[0]`. Vấp thật lúc dựng:
    `cac_nuoc` gộp cả `summary` nên với "Hán Quang 42 (Đài Loan)" nó trả `my` lên đầu (phần
    tóm tắt nhắc Mỹ trước Đài Loan) ⇒ truy vấn thành `"Hán Quang" US`, tức đi hỏi báo Mỹ về
    một cuộc tập trận của Đài Loan. Nơi DIỄN RA mới là nơi có nguồn tầng 1 và báo bản địa.
    """
    for truong in ("location", "name"):
        ds = _nuoc_trong(str(ex.get(truong, "")))
        if ds:
            return ds[0]
    ds = cac_nuoc(ex)
    return ds[0] if ds else ""


def tu_khoa(ex):
    """Từ khoá nhận diện tin của cuộc này — bơm vào `topics.py` lúc chạy.

    Gồm: tên ngắn (có năm), tên không năm, và các địa danh trong `location`. Địa danh là thứ
    báo chí hay dùng khi không nhắc tên tập trận (*"tại căn cứ Tindal"*).

    ⚠️ **Trả CẢ hai dạng: CÓ DẤU và KHÔNG DẤU.** `topics.match_topic` so regex trên văn bản
    GỐC (bảng `TOPIC_KEYWORDS_VI` viết có dấu), nên một từ khoá đã bỏ dấu như `"han quang"`
    KHÔNG BAO GIỜ khớp tiêu đề tiếng Việt `"Hán Quang"` — bơm vào là chủ đề câm mà bảng vẫn
    đủ dòng. Ngược lại, tiêu đề tiếng Anh viết `"Han Kuang"` nên bản không dấu cũng cần.
    """
    ra = []
    tn = ten_ngan(ex.get("name"))
    if tn:
        ra.append(tn.lower())
        if _khong_dau(tn) != tn.lower():
            ra.append(_khong_dau(tn))
        kn = ten_khong_nam(tn)
        if kn and kn != tn:
            ra.append(kn.lower())
            if _khong_dau(kn) != kn.lower():
                ra.append(_khong_dau(kn))
    # Địa danh trong `location`: CHỈ lấy từ đơn viết hoa THUẦN ASCII, dài ≥4 (Darwin, Tindal,
    # Amberley, Queensland, Townsville, Portland…).
    # ⚠️ Bản đầu quét "cụm chữ hoa liên tiếp" bằng `[A-ZÀ-Ỹ]` và sinh RÁC ngay lượt chạy đầu:
    # `'u khong'`, `'an hoang'`, `'a tindal'`, `'lanh'` — vì dải `À-Ỹ` không phủ hết chữ Việt
    # dạng tổ hợp nên regex cắt giữa từ. Một từ khoá rác như `'lanh'` khớp mọi tin có "lãnh",
    # tức chủ đề tập trận hút nhầm cả tin lãnh đạo/lãnh thổ — hỏng theo chiều rộng, khó thấy.
    # Địa danh cần bắt đều là tên riêng nước ngoài viết ASCII, nên siết vào đó là đủ và sạch.
    # ⚠️ Và loại từ nào chỉ là MỘT MẢNH của tên nước: "Toàn đảo Đài Loan" cho ra `'loan'`, mà
    # `'loan'` khớp chuỗi con trong "hỗn loạn", "loan báo" → chủ đề tập trận hút tin vu vơ.
    # Tên nước đã được `cac_nuoc()` lo, không cần nó làm từ khoá nhận diện lần nữa.
    # Chỉ loại MẢNH của cụm NHIỀU TỪ ("dai loan" → bỏ "loan"). Từ đơn đứng riêng trong bảng
    # thì GIỮ: "darwin"/"tindal"/"amberley" vừa là dấu nhận nước Úc vừa là địa danh của chính
    # kỳ tập trận, và đó là cụm báo chí hay dùng khi không nhắc tên cuộc. Bản đầu loại cả từ
    # đơn nên quét sạch 04 địa danh của Pitch Black — siết quá tay cũng là một kiểu hỏng câm.
    _manh_nuoc = set()
    for tu in TU_NHAN_NUOC.values():
        for t in tu:
            phan = t.split()
            if len(phan) > 1:
                _manh_nuoc.update(p for p in phan if len(p) >= 3)
    for cum in re.findall(r"\b[A-Z][a-z]{3,}\b", str(ex.get("location") or "")):
        k = _khong_dau(cum)
        if k not in _manh_nuoc:
            ra.append(k)
    # khử trùng, giữ thứ tự
    thay, out = set(), []
    for k in ra:
        if k and k not in thay:
            thay.add(k)
            out.append(k)
    return out


def truy_van(ex):
    """Truy vấn Google News cho cuộc này.

    ⚠️ **CỐ Ý HẸP.** Chủ đề "Tập trận" giành URL TRƯỚC chủ đề "Úc & Biển Đông"
    (`harvest.py::UU_TIEN_CHU_DE`), nên một truy vấn rộng kiểu `RAAF` hay `Australia exercise`
    sẽ hút mọi tin không quân Úc vào mục tập trận, kể cả tin không dính kỳ nào — đúng lỗi đã
    vá 02/08/2026. Mỗi truy vấn phải mang TÊN RIÊNG của cuộc.
    """
    tn = ten_ngan(ex.get("name"))
    if not tn:
        return []
    kn = ten_khong_nam(tn) or tn
    ra = ['"%s" exercise' % kn]
    # Thêm ĐÚNG MỘT truy vấn theo nước ĐĂNG CAI, để với tới báo bản địa mà không nhân số truy
    # vấn theo số nước tham gia — Pitch Black có 20 nước, mỗi nước một truy vấn là 20 lượt gọi
    # cho một chủ đề nhắm 1–2 tin.
    ch = nuoc_chu_nha(ex)
    if ch and TEN_ANH.get(ch):
        ra.append('"%s" %s' % (kn, TEN_ANH[ch]))
    return ra


def nguon_mo_rong(exs_dang_chay):
    """Danh sách domain nên ưu tiên khi quét cuộc đang chạy — gộp theo mọi nước dính tới.

    Trả về danh sách domain, KHÔNG phải URL feed: `harvest.py` dùng nó để ưu tiên/ghi vết, còn
    việc lấy nội dung vẫn đi qua bảng RSS + Google News như cũ. Cố ý không tự thêm feed mới
    giữa lúc chạy — thêm nguồn là việc phải đo trước (xem bảng đường vào trong CLAUDE.md).
    """
    ra, thay = [], set()
    for ex in exs_dang_chay:
        for n in cac_nuoc(ex):
            for d in NGUON_THEO_NUOC.get(n, []):
                if d not in thay:
                    thay.add(d)
                    ra.append(d)
    return ra


def tom_tat(exs_dang_chay):
    """Một dòng cho log/bảng kết quả: đang bám cuộc nào."""
    if not exs_dang_chay:
        return "KHÔNG có cuộc tập trận nào đang/sắp diễn ra trong DATA.exercises"
    return " · ".join("%s (%s)" % (ten_ngan(e.get("name")), e.get("dates") or "?")
                      for e in exs_dang_chay)
