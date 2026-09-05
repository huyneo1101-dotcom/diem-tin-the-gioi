#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dò cuộc tập trận CHƯA CÓ trong `DATA.exercises` — dựng 07/08/2026.

## Vòng luẩn quẩn mà script này cắt

`tap_tran.py` sinh từ khoá và truy vấn **từ chính `DATA.exercises`**, tức nó chỉ đi tìm tin
cho cuộc ĐÃ CÓ TÊN trong danh sách. Cuộc chưa có trong danh sách thì không ai đi tìm, mà
không ai tìm thì nó không bao giờ vào được danh sách. Đo 07/08/2026: `DATA.exercises` có 10
cuộc, thảy đều là chuỗi lớn có tên riêng; một lượt đọc tay kho nền cộng web tìm ra **14 cuộc
thiếu, trong đó 04 cuộc ĐANG chạy đúng hôm đó**.

Nguyên nhân gốc nằm ở tầng trên nữa: nguồn tổng hợp lịch diễn tập xếp theo **quân số và địa
bàn**, nên loại sạch cuộc ngắn ngày, ít quân, không công bố quân số — và loại luôn cả loại
hoạt động chung **không mang tên chuỗi** (hoạt động hợp tác hàng hải ba bên Nhật – Philippines
– Hoa Kỳ chẳng hạn). Mọi phép kiểm đang có đều chạy trên **dòng đang có**, nên mù với dòng
không tồn tại.

## Cách cắt: truy vấn theo KHUÔN, không theo TÊN

Truy vấn không hỏi *"có tin gì về Pitch Black không"* mà hỏi *"tháng này Nhật và Philippines
có tập chung gì không"* — khuôn `<nước A> <nước B> exercise <tháng năm>`. Khuôn không cần biết
trước tên cuộc, nên bắt được cả cuộc chưa ai đặt tên vào danh sách.

Đầu ra tách **02 nhóm**, cố ý không gộp — hai nhóm này xử lý khác hẳn nhau:

| Nhóm | Nghĩa | Xử lý |
|---|---|---|
| ★ CÓ TÊN RIÊNG | tiêu đề nêu tên một cuộc mà `DATA.exercises` không có | nạp thẻ mới bằng `add_news.py --newExercises` |
| ○ KHÔNG TÊN | hoạt động chung không mang tên chuỗi | đọc tay rồi quyết; đây đúng là loại mà bảng chuỗi tập trận mù |

⚠️ **Nhóm ○ KHÔNG phải nhiễu — nó là sản phẩm chính.** Cám dỗ lớn nhất khi bảo trì file này là
bỏ nhóm ○ cho bảng gọn, vì nó dài hơn và khó xử lý hơn. Bỏ nó là dựng lại đúng vùng mù đã
sinh ra script.

## Vì sao là công cụ GỢI Ý, không phải cổng chặn

Đầu ra là *"chỗ này đáng đọc"*, không phải một phán xét đúng/sai — nên script **luôn trả mã
0** trừ khi chính nó hỏng. Cắm nó làm cổng chặn phiên quét thì một hôm Google News đổi khuôn
là cả bản tin chết vì một mục phụ.

## Dùng

    python3 scripts/do_tap_tran_thieu.py                # dò thật, in bảng
    python3 scripts/do_tap_tran_thieu.py --thang 8      # ép tháng (mặc định: tháng này)
    python3 scripts/do_tap_tran_thieu.py --khong-so     # bỏ qua sổ đã soi, in lại từ đầu
    python3 scripts/do_tap_tran_thieu.py --tu-kiem      # chứng minh phép lọc còn răng
"""
import argparse
import datetime
import io
import json
import os
import pathlib
import re
import sys
import unicodedata
import urllib.parse

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SO = ROOT / "logs" / "tap-tran-da-soi.json"
GIU_NGAY = 14

# Cặp nước trọng tâm. Khai TƯỜNG MINH thay vì sinh mọi tổ hợp: n nước cho n² cặp, mà phần lớn
# cặp không bao giờ tập chung — mỗi cặp là một lượt gọi mạng, nên tổ hợp đầy đủ vừa chậm vừa
# đẩy bảng đầy dòng rỗng. Danh sách bám đúng 05 chủ đề của bản tin, KHÔNG phải mọi nước.
CAP_NUOC = [
    ("United States", "Japan"), ("United States", "Philippines"),
    ("United States", "Australia"), ("United States", "South Korea"),
    ("United States", "Indonesia"), ("United States", "India"),
    ("United States", "Thailand"), ("United States", "Vietnam"),
    ("Japan", "Philippines"), ("Japan", "Australia"), ("Japan", "India"),
    ("Australia", "Philippines"), ("Australia", "Indonesia"),
    ("India", "Philippines"), ("South Korea", "Philippines"),
    ("China", "Russia"), ("Russia", "Belarus"),
    ("NATO", "Baltic"), ("France", "Indo-Pacific"), ("United Kingdom", "Indo-Pacific"),
]

# Quân chủng theo nước — bắt cuộc một nước chủ trì mà cặp nước không phủ.
NUOC_QUAN_CHUNG = [
    ("Philippines", "navy"), ("Philippines", "air force"),
    ("Japan", "Maritime Self-Defense Force"), ("Australia", "navy"),
    ("Indonesia", "navy"), ("India", "navy"), ("Vietnam", "navy"),
    ("Taiwan", "military"),
]

# Từ chỉ hoạt động tập trận. Có cả tiếng Indonesia (latihan) và tiếng Việt vì Google News trả
# cả nguồn bản địa.
TU_TAP_TRAN = (
    "exercise", "exercises", "drill", "drills", "wargame", "war game", "war games",
    "manoeuvre", "manoeuvres", "maneuver", "maneuvers", "joint training",
    "latihan", "tap tran", "dien tap", "military training",
)

# Neo quân sự: `drill` một mình còn nghĩa là khoan dầu/khoan đất, `exercise` là tập thể dục.
# Đo lúc dựng: bỏ neo này thì truy vấn "Vietnam navy exercise" trả về cả tin khoan thăm dò
# dầu khí và tin thể dục buổi sáng.
#
# ⚠️ Bản đầu CHỈ có neo này và **bỏ sót gần hết tin thật** — đo 07/08 trên 06 tiêu đề mẫu thì
# 5/6 rớt, gồm cả "US and Japan navies begin joint exercise off Okinawa" (danh sách có `navy`
# nhưng không có `navies`) và "Exercise Kamandag kicks off in the Philippines" (không từ quân
# sự nào ngoài chính tên cuộc). Tiêu đề tập trận thường chỉ nêu TÊN NƯỚC cộng chữ exercise,
# nên neo bằng từ vựng quân sự một mình là đo sai bản chất. Nay có 03 lối vào, xem
# `la_tin_tap_tran`.
NEO_QUAN_SU = (
    "militar", "navy", "navies", "naval", "air force", "army", "troops", "forces",
    "defence", "defense", "warship", "fighter jet", "marines", "coast guard", "amphibious",
    "live-fire", "live fire", "maritime", "soldiers", "sailors", "airmen", "combat",
    "quan su", "hai quan", "khong quan", "lu quan", "tni", "jsdf", "self-defense force",
    "pentagon", "nato",
)

# Từ đứng cạnh "exercise" nhưng KHÔNG phải tên cuộc. Chốt chống nới tay của lối vào (c):
# "Daily exercise reduces heart disease" bóc ra tên riêng "Daily" nếu không có bảng này.
TU_VO_HAI = {
    "daily", "morning", "evening", "weekly", "breathing", "stretching", "physical",
    "cardio", "aerobic", "yoga", "fire", "evacuation", "emergency", "earthquake",
    "tsunami", "safety", "drilling", "accounting", "budget", "tabletop", "writing",
    "self-enumeration", "census", "no", "stock", "listening", "branding",
}

# Chủ đề CHẮC CHẮN không phải tập trận quân sự — loại thẳng dù tiêu đề có tên nước và chữ
# exercise. Đo trên lượt chạy thật đầu tiên (07/08, 28 truy vấn): lối vào "01 nước + tên
# riêng" kéo vào "Self-enumeration exercise for India's 16th Census" và "No exercise, no
# supplements, just Shinrin-yoku: Japan introduced forest bathing".
# ⚠️ Là danh sách HỮU HẠN, cố ý. Đã cân nhắc rồi bỏ phương án siết lối (b) xuống «chỉ nhận từ
# 02 nước»: nó loại luôn "Balikatan exercise begins in Luzon", tức mất đúng loại cuộc thật mà
# script sinh ra để tìm. Thà giữ một bảng phải bảo trì còn hơn siết mất sản phẩm chính.
CHU_DE_KHONG_QUAN_SU = (
    "census", "supplement", "forest bathing", "wellness", "fitness", "workout", "gym",
    "diet", "weight loss", "heart disease", "dental", "yoga", "meditation", "school drill",
    "fire drill", "earthquake drill", "evacuation drill", "stock market", "accounting",
)

# Không nhận làm TÊN RIÊNG của cuộc: tên nước, tổ chức, quân chủng, từ chung.
KHONG_PHAI_TEN_RIENG = {
    "us", "u.s", "usa", "united", "states", "america", "american", "japan", "japanese",
    "china", "chinese", "russia", "russian", "korea", "korean", "australia", "australian",
    "philippines", "philippine", "india", "indian", "indonesia", "indonesian", "vietnam",
    "vietnamese", "taiwan", "taiwanese", "thailand", "thai", "malaysia", "singapore",
    "france", "french", "britain", "british", "uk", "nato", "asean", "eu", "belarus",
    "navy", "naval", "army", "air", "force", "forces", "marine", "marines", "military",
    "joint", "annual", "first", "second", "third", "new", "major", "large", "biggest",
    "coast", "guard", "defence", "defense", "allied", "allies", "multinational", "the",
    "seoul", "tokyo", "beijing", "manila", "canberra", "washington", "moscow", "hanoi",
    "north", "south", "east", "west", "sea", "island", "islands", "strait", "pacific",
    "indo", "asia", "asian", "region", "regional", "bilateral", "trilateral",
    # Giới từ/liên từ — bắt được ở lượt chạy thật 07/08: "US To Hold Naval Exercise With
    # Bangladesh" bóc ra tên cuộc "With Bangladesh".
    "with", "in", "off", "near", "for", "and", "to", "at", "on", "of", "by", "from",
    "begins", "concludes", "kicks", "wraps", "holds", "hold", "starts", "ends",
    "successfully", "largest", "biggest", "next", "this", "last",
    # Tên nước còn thiếu so với bảng gốc.
    "bangladesh", "sri", "lanka", "pakistan", "myanmar", "cambodia", "laos", "brunei",
    "mongolia", "nepal", "fiji", "tonga", "papua", "guinea", "peru", "chile", "brazil",
    "argentina", "canada", "germany", "italy", "spain", "poland", "norway", "sweden",
    "finland", "denmark", "netherlands", "turkey", "greece", "romania", "ukraine",
}


def _kd(s):
    """Bỏ dấu, thường hoá — dùng cho MỌI phép so khớp tiếng Việt (macOS trả NFD)."""
    s = unicodedata.normalize("NFD", str(s or "").lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn").replace("đ", "d")


def _harvest():
    sys.path.insert(0, str(HERE))
    import harvest
    return harvest


def _tap_tran():
    sys.path.insert(0, str(HERE))
    import tap_tran
    return tap_tran


def hom_nay_vn():
    return (datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(hours=7)).date()


def dem_nuoc(tieu_de, tt=None):
    """Đếm số nước/khối nhận ra trong tiêu đề. Dùng CHUNG bảng `tap_tran.TU_NHAN_NUOC`.

    ⚠️ Khớp theo RANH GIỚI TỪ, tuyệt đối không theo chuỗi con. Bảng đó viết cho văn bản tiếng
    Việt nên có khoá 02-03 ký tự (`uc` cho Úc, `duc` cho Đức, `nga`, `my`); đo 07/08 thì khớp
    chuỗi con làm "Daily exercise red**uc**es heart disease" đếm ra **02 nước** và lọt thẳng
    vào bảng. Cùng họ với lỗi `úc → uc trúng 397/442 bài` đã ghi ở CLAUDE.md.
    """
    tt = tt or _tap_tran()
    t = _kd(tieu_de)
    n = 0
    for _, tu in tt.TU_NHAN_NUOC.items():
        for w in tu:
            if re.search(r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(w.strip()), t):
                n += 1
                break
    return n


def _ten_khuon_chat(tieu_de):
    """Chỉ khuôn `Exercise|Drill|Operation <Tên>` — từ khoá đứng TRƯỚC tên.

    Khuôn NGƯỢC (`<Tên> exercise`) cố ý không dùng ở đây: nó trúng mọi danh từ thường đứng
    trước chữ exercise, đo 07/08 thì "Stock exercise routine for office workers" bóc ra tên
    riêng "Stock". `ten_rieng_trong` vẫn giữ cả hai khuôn vì nó chỉ chạy SAU khi tin đã được
    nhận, lúc đó việc đoán tên rộng tay một chút là vô hại.
    """
    m = re.search(r"(?:Exercise|Drill|Operation)\s+([A-Z][A-Za-z'’\-]+"
                  r"(?:\s+[A-Z][A-Za-z'’\-]+){0,3})", str(tieu_de or ""))
    if not m:
        return None
    tu = [w for w in re.split(r"\s+", m.group(1)) if w]
    while tu and _kd(tu[0]).strip(".'’-") in KHONG_PHAI_TEN_RIENG:
        tu.pop(0)
    while tu and _kd(tu[-1]).strip(".'’-") in KHONG_PHAI_TEN_RIENG:
        tu.pop()
    return " ".join(tu) if tu else None


def la_tin_tap_tran(tieu_de, tt=None):
    """Tiêu đề có nói về một cuộc tập trận không?

    Bắt buộc có từ chỉ tập trận, RỒI phải qua ÍT NHẤT MỘT trong 03 lối vào — một lối là
    không đủ, đã đo ở chú thích `NEO_QUAN_SU`:
      (a) từ vựng quân sự;
      (b) ≥02 nước/khối, hoặc 01 nước cộng một tên riêng không vô hại;
      (c) khuôn CHẶT `Exercise <Tên riêng>`.
    """
    t = _kd(tieu_de)
    if not any(w in t for w in TU_TAP_TRAN):
        return False
    if any(w in t for w in CHU_DE_KHONG_QUAN_SU):
        return False
    return True
    ten = ten_rieng_trong(tieu_de)
    co_ten = bool(ten) and _kd(ten) not in TU_VO_HAI
    n = dem_nuoc(tieu_de, tt)
    if n >= 2 or (n >= 1 and co_ten):
        return True
    chat = _ten_khuon_chat(tieu_de)
    return bool(chat) and _kd(chat) not in TU_VO_HAI


def ten_rieng_trong(tieu_de):
    """Bóc tên riêng của cuộc từ tiêu đề, hoặc None.

    Hai khuôn báo chí hay dùng: `Exercise Pitch Black`, và `Pitch Black exercise`.
    Loại ứng viên chỉ gồm tên nước/quân chủng/từ chung — nếu không thì mọi tiêu đề đều ra
    "tên riêng" và nhóm ○ rỗng vĩnh viễn, tức mất đúng nhóm script này sinh ra để tìm.
    """
    s = str(tieu_de or "")
    hoa = r"[A-Z][A-Za-z'’\-]+(?:\s+[A-Z][A-Za-z'’\-]+){0,3}"
    for mau in (r"(?:Exercise|Drill|Operation)\s+(%s)" % hoa,
                r"(%s)\s+(?:exercise|drill|wargame)" % hoa):
        m = re.search(mau, s)
        if not m:
            continue
        ung = m.group(1).strip()
        tu = [w for w in re.split(r"\s+", ung) if w]
        con = [w for w in tu if _kd(w).strip(".'’-") not in KHONG_PHAI_TEN_RIENG]
        if not con:
            continue
        # Giữ nguyên cụm liền mạch còn lại, bỏ phần đầu/cuối là từ chung.
        while tu and _kd(tu[0]).strip(".'’-") in KHONG_PHAI_TEN_RIENG:
            tu.pop(0)
        while tu and _kd(tu[-1]).strip(".'’-") in KHONG_PHAI_TEN_RIENG:
            tu.pop()
        if tu:
            return " ".join(tu)
    return None


def da_co_trong_data(tieu_de, exs, tt=None):
    """Tiêu đề nói về cuộc ĐÃ CÓ? Trả tên cuộc đó, hoặc None.

    Khớp bằng tên cuộc đã bỏ năm (`"Pitch Black 2026"` -> `"pitch black"`), vì báo chí gọi
    cuộc bằng tên chuỗi chứ không kèm năm. Cuộc mang hai tên (`"Hán Quang 42 - Han Kuang
    2026"`) thì thử CẢ HAI vế — bỏ vế tiếng Anh là mọi tin quốc tế về cuộc đó bị báo thành
    cuộc mới.
    """
    tt = tt or _tap_tran()
    t = _kd(tieu_de)
    for e in exs:
        goc = str(e.get("name") or "")
        ve = [goc.split("(")[0]] + re.split(r"\s+[-–—]\s+", goc.split("(")[0])
        for v in ve:
            ten = _kd(tt.ten_khong_nam(v.strip()))
            if len(ten) >= 4 and ten in t:
                return e.get("name")
    return None


def sinh_truy_van(ngay, thang=None):
    """Truy vấn theo KHUÔN. Cố ý không mang tên cuộc nào."""
    thang = thang or ngay.month
    ten_thang = datetime.date(ngay.year, thang, 1).strftime("%B")
    q = []
    for a, b in CAP_NUOC:
        q.append('"%s" "%s" exercise %s %d' % (a, b, ten_thang, ngay.year))
    for n, qc in NUOC_QUAN_CHUNG:
        q.append('"%s" %s exercise OR drill %s %d' % (n, qc, ten_thang, ngay.year))
    return q


def doc_so():
    """Fail-OPEN có tiếng: sổ hỏng thì coi như chưa soi gì, in cảnh báo. Hướng lệch là báo
    LẶP một dòng, không phải bỏ sót một cuộc."""
    try:
        d = json.loads(SO.read_text(encoding="utf-8"))
        if not isinstance(d, dict):
            raise ValueError("sổ không phải object")
        return d
    except FileNotFoundError:
        return {}
    except Exception as e:
        print("  ⚠️ đọc sổ đã soi hỏng (%s) — coi như chưa soi gì" % e, file=sys.stderr)
        return {}


def ghi_so(d, ngay):
    han = (ngay - datetime.timedelta(days=GIU_NGAY)).isoformat()
    d = {u: v for u, v in d.items() if str(v) >= han}
    try:
        SO.parent.mkdir(parents=True, exist_ok=True)
        SO.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception as e:
        print("  ⚠️ không ghi được sổ đã soi: %s" % e, file=sys.stderr)
    return d


def loc(hits, exs, tt=None):
    """hits = [{tieu_de, url, nguon, ngay}] -> {"co_ten": [...], "khong_ten": [...]}

    ⚠️ KHỬ TRÙNG là bắt buộc, không phải để bảng gọn. 28 truy vấn theo khuôn chồng lấn nhau
    rất nhiều (một tin Biển Đông khớp cả cặp Mỹ–Philippines lẫn cặp Nhật–Philippines), đo lượt
    chạy đầu 07/08: 135 dòng đầu ra chỉ ứng với ~40 tin thật, cùng một tiêu đề lặp tới 04 lần.
    Bảng lặp là bảng không ai đọc hết, mà không đọc hết thì đúng dòng cuối bị bỏ qua.
    Khử theo URL VÀ theo tiêu đề đã chuẩn hoá — Google News cấp URL khác nhau cho cùng một bài
    khi nó tới từ hai truy vấn, nên khử theo URL một mình là hụt.

    Nhóm ★ chỉ nhận tên bóc bằng KHUÔN CHẶT. Dùng `ten_rieng_trong` ở đây thì "US To Hold Naval
    Exercise With Bangladesh" ra tên cuộc "With Bangladesh", và "…drill" ra "August" — bảng ★
    đầy tên rác thì mất luôn giá trị của việc tách hai nhóm.
    """
    tt = tt or _tap_tran()
    co_ten, khong_ten = [], []
    thay_url, thay_td = set(), set()
    for h in hits:
        td = h.get("tieu_de") or ""
        u = h.get("url") or ""
        khoa_td = re.sub(r"[^a-z0-9 ]+", " ", _kd(td))
        khoa_td = " ".join(khoa_td.split())
        if (u and u in thay_url) or (khoa_td and khoa_td in thay_td):
            continue
        if not la_tin_tap_tran(td, tt):
            continue
        if da_co_trong_data(td, exs, tt):
            continue
        thay_url.add(u)
        thay_td.add(khoa_td)
        ten = _ten_khuon_chat(td)
        (co_ten if ten else khong_ten).append(dict(h, ten_doan=ten))
    return {"co_ten": co_ten, "khong_ten": khong_ten}


def chay(thang=None, dung_so=True, gioi_han=None):
    hv = _harvest()
    tt = _tap_tran()
    ngay = hom_nay_vn()
    exs = tt.doc_exercises()
    if not exs:
        print("⚠️ KHÔNG đọc được DATA.exercises — mọi tin sẽ bị báo là cuộc mới. Dừng.",
              file=sys.stderr)
        return 2

    qs = sinh_truy_van(ngay, thang)
    if gioi_han:
        qs = qs[:gioi_han]
    print("Dò cuộc tập trận còn thiếu — %d truy vấn theo KHUÔN, %d cuộc đang có trong DATA."
          % (len(qs), len(exs)), file=sys.stderr)

    hits, hong = [], 0
    for q in qs:
        url = ("https://news.google.com/rss/search?q="
               + urllib.parse.quote(q + " when:7d") + "&hl=en-US&gl=US&ceid=US:en")
        try:
            items = hv.items_of(hv.curl(url))
        except Exception as e:
            hong += 1
            print("  ⚠️ truy vấn hỏng (%s): %s" % (type(e).__name__, q), file=sys.stderr)
            continue
        if not items:
            hong += 1
            continue
        for title, link, pub, src in items:
            t = title.rsplit(" - ", 1)[0] if " - " in title else title
            d = hv.parse_date(pub)
            hits.append({"tieu_de": t, "url": link, "nguon": src or "?",
                         "ngay": d.isoformat() if d else "?"})

    if hong == len(qs):
        print("⚠️ TOÀN BỘ %d truy vấn không trả kết quả — nghi mạng hoặc Google News đổi "
              "khuôn, KHÔNG phải hôm nay không có tập trận nào." % hong, file=sys.stderr)
        return 0

    kq = loc(hits, exs, tt)
    so = doc_so() if dung_so else {}
    moi = {k: [h for h in v if h["url"] not in so] for k, v in kq.items()}

    tong = len(moi["co_ten"]) + len(moi["khong_ten"])
    print("\n%d ứng viên (đã lọc %d tin trùng cuộc đã có · %d tin đã soi lần trước)"
          % (tong, len(hits) - len(kq["co_ten"]) - len(kq["khong_ten"]),
             (len(kq["co_ten"]) + len(kq["khong_ten"])) - tong))
    if hong:
        print("  ⚠️ %d/%d truy vấn không ra kết quả — phần đó KHÔNG được soi." % (hong, len(qs)))

    print("\n⚠️ TRƯỚC KHI NẠP BẤT KỲ DÒNG NÀO: mở bài đọc NGÀY DIỄN RA của cuộc, đừng tin ngày\n"
          "   của tin. `when:7d` lọc theo ngày Google gán, mà bài cũ đăng lại vẫn mang ngày mới —\n"
          "   đo 07/08: 'Exercise MILAN-2026' lọt vào bảng với ngày 07/08 trong khi cuộc đã chạy\n"
          "   xong từ 15–25/02/2026. Và kiểm cuộc có phải THÀNH PHẦN của cuộc đã có không:\n"
          "   'Exercise Carabaroo' là phần Lục quân Philippines nằm TRONG Predator's Run — xếp làm\n"
          "   item của thẻ cũ, đừng dựng thẻ mới.")

    for nhan, khoa, ghi in (("★ CÓ TÊN RIÊNG — nạp thẻ mới bằng add_news.py --newExercises",
                             "co_ten", "tên đoán"),
                            ("○ KHÔNG TÊN CHUỖI — hoạt động chung, đọc tay rồi quyết",
                             "khong_ten", "")):
        v = moi[khoa]
        print("\n%s  (%d)" % (nhan, len(v)))
        for h in v:
            phu = ("  [%s]" % h["ten_doan"]) if h.get("ten_doan") else ""
            print("  · %s%s\n      %s · %s\n      %s"
                  % (h["tieu_de"][:150], phu, h["ngay"], h["nguon"], h["url"]))

    if dung_so:
        for v in moi.values():
            for h in v:
                so[h["url"]] = ngay.isoformat()
        ghi_so(so, ngay)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--thang", type=int, help="ép tháng dò (mặc định tháng này)")
    ap.add_argument("--khong-so", action="store_true", help="bỏ qua sổ đã soi")
    ap.add_argument("--gioi-han", type=int, help="chỉ chạy N truy vấn đầu (để thử nhanh)")
    ap.add_argument("--tu-kiem", action="store_true")
    ap.add_argument("--chi-bo-ca", action="store_true")
    a = ap.parse_args(argv)
    if a.chi_bo_ca:
        return bo_ca()
    if a.tu_kiem:
        return tu_kiem()
    return chay(thang=a.thang, dung_so=not a.khong_so, gioi_han=a.gioi_han)


# ─────────────────────────────────────────────────────────────────────────────
# BỘ CA
# ─────────────────────────────────────────────────────────────────────────────
EXS_MAU = [
    {"name": "Pitch Black 2026 (Úc chủ trì, 20 nước tham gia)"},
    {"name": "Hán Quang 42 - Han Kuang 2026 (Đài Loan)"},
    {"name": "RIMPAC 2026 (Rim of the Pacific)"},
]


def _ca(ten, ham):
    try:
        ham()
    except AssertionError as e:
        print("  ✗ %s — %s" % (ten, e))
        return False
    except Exception as e:
        print("  ✗ %s — lỗi lạ: %s: %s" % (ten, type(e).__name__, e))
        return False
    print("  ✓ %s" % ten)
    return True


def bo_ca():
    print("Bộ ca do_tap_tran_thieu.py")
    ok = []
    tt = _tap_tran()

    def _bat(td):
        assert la_tin_tap_tran(td), "KHÔNG nhận là tin tập trận: %r" % td

    def _bo(td):
        assert not la_tin_tap_tran(td), "nhận NHẦM là tin tập trận: %r" % td

    ok.append(_ca("[01] PHẢI BẮT: tin tập trận tiếng Anh",
                  lambda: _bat("US and Japan navies begin joint exercise off Okinawa")))
    ok.append(_ca("[02] PHẢI BẮT: tin tập trận tiếng Indonesia",
                  lambda: _bat("TNI gelar latihan bersama militer dengan Australia")))
    ok.append(_ca("[03] PHẢI BẮT: tin tập trận tiếng Việt",
                  lambda: _bat("Hải quân Việt Nam diễn tập chung với Ấn Độ")))
    ok.append(_ca("[04] PHẢI BỎ: 'drill' nghĩa khoan dầu, không có neo quân sự",
                  lambda: _bo("Oil company starts drilling exercise in the North Sea")))
    ok.append(_ca("[05] PHẢI BỎ: 'exercise' nghĩa thể dục",
                  lambda: _bo("Daily exercise reduces heart disease, study finds")))
    ok.append(_ca("[06] PHẢI BỎ: tin quân sự nhưng KHÔNG phải tập trận",
                  lambda: _bo("Philippine Navy commissions new frigate")))

    def _ten(td, mong):
        got = ten_rieng_trong(td)
        assert got == mong, "bóc ra %r, mong %r (từ %r)" % (got, mong, td)

    ok.append(_ca("[07] PHẢI BÓC: khuôn 'Exercise <Tên>'",
                  lambda: _ten("Exercise Pitch Black wraps up at RAAF Darwin", "Pitch Black")))
    ok.append(_ca("[08] PHẢI BÓC: khuôn '<Tên> exercise'",
                  lambda: _ten("Balikatan exercise begins in Luzon", "Balikatan")))
    ok.append(_ca("[09] PHẢI BỎ TÊN: tiêu đề chỉ có tên NƯỚC, không có tên riêng",
                  lambda: _ten("US and Japan joint exercise begins", None)))
    ok.append(_ca("[10] PHẢI BỎ TÊN: 'Navy exercise' không phải tên riêng",
                  lambda: _ten("Navy exercise concludes in the Pacific", None)))

    def _daco(td, mong):
        got = da_co_trong_data(td, EXS_MAU, tt)
        assert (got is not None) == mong, "da_co=%r, mong có=%r (từ %r)" % (got, mong, td)

    ok.append(_ca("[11] PHẢI NHẬN ĐÃ CÓ: tên khớp cuộc trong DATA (bỏ năm)",
                  lambda: _daco("Pitch Black 2026 concludes at Darwin", True)))
    ok.append(_ca("[12] PHẢI NHẬN ĐÃ CÓ: khớp VẾ TIẾNG ANH của tên hai vế",
                  lambda: _daco("Taiwan wraps up Han Kuang drills", True)))
    ok.append(_ca("[13] đối chứng: cuộc KHÔNG có trong DATA thì không nhận nhầm",
                  lambda: _daco("Malabar exercise begins in Bay of Bengal", False)))

    def _ca14():
        # Phép lọc tổng: tin cuộc đã có bị loại, tin cuộc mới vào đúng nhóm.
        hits = [
            {"tieu_de": "Exercise Pitch Black concludes at RAAF Darwin", "url": "u1"},
            {"tieu_de": "Exercise Kamandag kicks off in the Philippines", "url": "u2"},
            {"tieu_de": "Japan, Philippines and US hold joint maritime drills", "url": "u3"},
            {"tieu_de": "Stock exercise routine for office workers", "url": "u4"},
        ]
        r = loc(hits, EXS_MAU, tt)
        ten = [h["url"] for h in r["co_ten"]]
        khong = [h["url"] for h in r["khong_ten"]]
        assert ten == ["u2"], "nhóm CÓ TÊN sai: %r" % ten
        assert khong == ["u3"], "nhóm KHÔNG TÊN sai: %r" % khong
    ok.append(_ca("[14] PHẢI CHẶN: phép lọc tổng chia đúng 02 nhóm, loại cuộc đã có", _ca14))

    def _ca15():
        # Nhóm ○ là SẢN PHẨM, không được bỏ. Hoạt động chung không tên phải nằm trong đầu ra.
        r = loc([{"tieu_de": "US, Japan, Philippines begin trilateral naval exercise",
                  "url": "x"}], EXS_MAU, tt)
        assert len(r["khong_ten"]) == 1, "hoạt động chung không tên bị bỏ mất"
    ok.append(_ca("[15] PHẢI CHẶN: hoạt động chung KHÔNG tên vẫn phải ra bảng", _ca15))

    def _ca16():
        q = sinh_truy_van(datetime.date(2026, 8, 7))
        assert q, "không sinh được truy vấn nào"
        gop = " ".join(q).lower()
        for cam in ("pitch black", "rimpac", "han kuang", "predator"):
            assert cam not in gop, "truy vấn mang TÊN CUỘC %r — quay lại vòng luẩn quẩn" % cam
        assert "august 2026" in gop, "truy vấn không neo tháng/năm"
    ok.append(_ca("[16] PHẢI CHẶN: truy vấn theo KHUÔN, tuyệt đối không mang tên cuộc", _ca16))

    def _ca17():
        q8 = " ".join(sinh_truy_van(datetime.date(2026, 8, 7)))
        q9 = " ".join(sinh_truy_van(datetime.date(2026, 8, 7), thang=9))
        assert "september 2026" in q9.lower() and "september" not in q8.lower(), \
            "cờ --thang không đổi được tháng trong truy vấn"
    ok.append(_ca("[17] đối chứng: cờ --thang có thật, đổi được tháng", _ca17))

    def _ca18():
        import tempfile
        global SO
        cu = SO
        try:
            with tempfile.TemporaryDirectory() as d:
                SO = pathlib.Path(d) / "so.json"
                assert doc_so() == {}, "sổ chưa có phải trả rỗng"
                SO.write_text("{ hong", encoding="utf-8")
                assert doc_so() == {}, "sổ HỎNG phải fail-open về rỗng, không ném lỗi"
                ng = datetime.date(2026, 8, 7)
                ghi_so({"u1": "2026-08-06", "cu": "2026-07-01"}, ng)
                con = json.loads(SO.read_text(encoding="utf-8"))
                assert "u1" in con, "dòng trong hạn bị cắt oan"
                assert "cu" not in con, "dòng quá %d ngày không bị cắt" % GIU_NGAY
        finally:
            SO = cu
    ok.append(_ca("[18] PHẢI CHẶN: sổ fail-open có tiếng + cắt đúng hạn giữ", _ca18))

    def _ca19():
        # DATA rỗng thì phải DỪNG, không được báo cả kho thành "cuộc mới".
        src = pathlib.Path(__file__).read_text(encoding="utf-8").split("# BỘ CA")[0]
        assert "if not exs:" in src and "return 2" in src, \
            "thiếu chốt DATA rỗng -> dừng; không có nó thì mọi tin bị báo là cuộc mới"
    ok.append(_ca("[19] PHẢI CHẶN: DATA rỗng thì dừng, không báo cả kho là cuộc mới", _ca19))

    def _ca20():
        src = pathlib.Path(__file__).read_text(encoding="utf-8").split("# BỘ CA")[0]
        assert "import tap_tran" in src and "import harvest" in src, \
            "không dùng chung tap_tran/harvest — luật bị chép?"
        assert "def curl" not in src, "có hàm curl viết lại trong file này"
    ok.append(_ca("[20] PHẢI CHẶN: dùng chung harvest/tap_tran, không chép", _ca20))

    # ── ca canh 02 lỗi đã vá 07/08 (bản đầu mắc cả hai) ──
    def _ca21():
        n = dem_nuoc("Daily exercise reduces heart disease, study finds", tt)
        assert n == 0, ("đếm ra %d nước — bảng TU_NHAN_NUOC đang khớp CHUỖI CON "
                        "(uc/duc trúng trong 'reduces')" % n)
        assert dem_nuoc("US and Japan hold joint exercise", tt) >= 2, \
            "siết quá tay: tiêu đề có 02 nước thật mà không đếm được"
    ok.append(_ca("[21] PHẢI CHẶN: đếm nước theo ranh giới TỪ, không theo chuỗi con", _ca21))

    ok.append(_ca("[22] PHẢI BỎ: khuôn NGƯỢC không được làm lối vào ('Stock exercise')",
                  lambda: _bo("Stock exercise routine for office workers")))
    ok.append(_ca("[23] đối chứng chống siết quá tay: 01 nước + tên riêng vẫn PHẢI bắt",
                  lambda: _bat("Balikatan exercise begins in Luzon")))

    # ── ca canh 03 lỗi lộ ra ở LƯỢT CHẠY THẬT đầu tiên 07/08 ──
    def _ca24():
        hits = [
            {"tieu_de": "Exercise Kamandag kicks off in the Philippines", "url": "a"},
            {"tieu_de": "Exercise Kamandag kicks off in the Philippines", "url": "b"},
            {"tieu_de": "Exercise Kamandag kicks off in the Philippines!", "url": "a"},
        ]
        r = loc(hits, EXS_MAU, tt)
        n = len(r["co_ten"]) + len(r["khong_ten"])
        assert n == 1, "khử trùng hỏng: %d dòng cho cùng một tin (URL khác + dấu câu khác)" % n
    ok.append(_ca("[24] PHẢI CHẶN: khử trùng theo CẢ url lẫn tiêu đề chuẩn hoá", _ca24))

    def _ca25():
        r = loc([{"tieu_de": "US To Hold Naval Exercise With Bangladesh, Sell Hardware",
                  "url": "z"}], EXS_MAU, tt)
        ten = [h["ten_doan"] for h in r["co_ten"]]
        assert not ten, "nhóm ★ nhận tên RÁC %r — phải dùng khuôn chặt" % ten
        assert len(r["khong_ten"]) == 1, "tin thật bị bỏ mất thay vì chuyển sang nhóm ○"
    ok.append(_ca("[25] PHẢI CHẶN: nhóm ★ không nhận tên rác kiểu 'With Bangladesh'", _ca25))

    ok.append(_ca("[26] PHẢI BỎ: điều tra dân số có chữ exercise + tên nước",
                  lambda: _bo("Self-enumeration exercise for India's 16th Census kicks off")))
    ok.append(_ca("[27] PHẢI BỎ: tin sức khoẻ có chữ exercise + tên nước",
                  lambda: _bo("No exercise, no supplements: Japan's forest bathing works")))
    ok.append(_ca("[28] đối chứng: tập trận thật của cùng nước đó vẫn PHẢI bắt",
                  lambda: _bat("India and Japan begin joint naval exercise")))
    # Ca dành RIÊNG cho bảng CHU_DE_KHONG_QUAN_SU: 02 nước nên lối (b) cho qua, và tên riêng
    # không nằm trong TU_VO_HAI — tức không lớp nào khác che, chỉ bảng chủ đề chặn được.
    ok.append(_ca("[29] PHẢI BỎ: nghiên cứu sức khoẻ có ĐỦ 02 nước",
                  lambda: _bo("US and Japan researchers study exercise and heart disease")))

    print("─" * 78)
    print("%d/%d ca đạt" % (sum(ok), len(ok)))
    return 0 if all(ok) else 1


BAN_HONG = [
    {"ten": "bỏ mọi lối vào, nhận mọi tin có chữ exercise",
     "tim": "    if any(w in t for w in NEO_QUAN_SU):\n        return True",
     # KHÔNG khai [06]: tiêu đề đó không có từ chỉ tập trận nào nên bị chặn ở lớp TRƯỚC, phép
     # thay này không đụng tới. Khai thừa là `--tu-kiem` trượt vì lý do sai.
     # KHÔNG khai [05]/[26]/[27]: chúng bị bảng CHU_DE_KHONG_QUAN_SU chặn ở lớp TRƯỚC.
     "thay": "    return True", "do": ["[04]", "[14]", "[22]"]},
    # Phép thay phải gỡ HẾT các lớp cùng bảo vệ một hành vi: bản đầu chỉ đổi `con = tu` thì
    # hai vòng `while` phía dưới VẪN cắt từ chung, nên không ca nào đỏ — "còn lớp khác che".
    {"ten": "thôi loại tên nước/từ chung khỏi ứng viên tên riêng",
     "tim": ("        con = [w for w in tu if _kd(w).strip(\".'’-\") not in KHONG_PHAI_TEN_RIENG]\n"
             "        if not con:\n            continue\n"
             "        # Giữ nguyên cụm liền mạch còn lại, bỏ phần đầu/cuối là từ chung.\n"
             "        while tu and _kd(tu[0]).strip(\".'’-\") in KHONG_PHAI_TEN_RIENG:\n"
             "            tu.pop(0)\n"
             "        while tu and _kd(tu[-1]).strip(\".'’-\") in KHONG_PHAI_TEN_RIENG:\n"
             "            tu.pop()"),
     # Chỉ [10]: ba ca kia dựng ở nhánh mà phép thay KHÔNG đi qua — tiêu đề của chúng có từ
     # thường đứng ngay trước "exercise"/"drills" nên regex chữ hoa không khớp, hàm trả None
     # ở cả hai bản. Đo trước rồi mới khai, đừng suy.
     "thay": "        pass", "do": ["[10]"]},
    {"ten": "chỉ khớp vế đầu của tên hai vế (mất vế tiếng Anh)",
     "tim": "        ve = [goc.split(\"(\")[0]] + re.split(r\"\\s+[-–—]\\s+\", goc.split(\"(\")[0])",
     "thay": "        ve = [goc.split(\"(\")[0]]", "do": ["[12]"]},
    {"ten": "bỏ nhóm KHÔNG TÊN cho bảng gọn",
     "tim": "        (co_ten if ten else khong_ten).append(dict(h, ten_doan=ten))",
     "thay": "        if ten: co_ten.append(dict(h, ten_doan=ten))", "do": ["[14]", "[15]"]},
    {"ten": "truy vấn quay lại neo TÊN CUỘC",
     "tim": "        q.append('\"%s\" \"%s\" exercise %s %d' % (a, b, ten_thang, ngay.year))",
     "thay": "        q.append('\"%s\" \"%s\" Pitch Black RIMPAC %s %d' % (a, b, ten_thang, ngay.year))",
     "do": ["[16]"]},
    {"ten": "sổ hỏng thì ném lỗi thay vì fail-open",
     "tim": "        print(\"  ⚠️ đọc sổ đã soi hỏng (%s) — coi như chưa soi gì\" % e, file=sys.stderr)\n        return {}",
     "thay": "        raise", "do": ["[18]"]},
    {"ten": "sổ không cắt hạn giữ",
     "tim": "    d = {u: v for u, v in d.items() if str(v) >= han}",
     "thay": "    d = dict(d)", "do": ["[18]"]},
    {"ten": "đếm nước quay lại khớp CHUỖI CON (uc/duc trúng trong 'reduces')",
     "tim": '            if re.search(r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(w.strip()), t):',
     "thay": "            if w.strip() in t:", "do": ["[21]"]},
    # ĐÃ THỬ RỒI BỎ: bản hỏng đổi lối vào (c) sang khuôn NGƯỢC không làm ca nào đỏ, vì
    # `_ten_khuon_chat` là tập con của `ten_rieng_trong` và phần chênh đã bị lối (b) cùng
    # TU_VO_HAI che hết. Đừng dựng lại — nó chỉ làm --tu-kiem trượt vì lý do sai.
    {"ten": "bỏ khử trùng (bảng lặp 3-4 lần mỗi tin)",
     "tim": "        if (u and u in thay_url) or (khoa_td and khoa_td in thay_td):\n            continue",
     "thay": "        pass", "do": ["[24]"]},
    {"ten": "khuôn chặt thôi cắt từ chung (tên rác 'With Bangladesh' vào nhóm ★)",
     "tim": ('    while tu and _kd(tu[0]).strip(".\'’-") in KHONG_PHAI_TEN_RIENG:\n'
             "        tu.pop(0)\n"
             '    while tu and _kd(tu[-1]).strip(".\'’-") in KHONG_PHAI_TEN_RIENG:\n'
             "        tu.pop()\n"
             '    return " ".join(tu) if tu else None'),
     "thay": '    return " ".join(tu) if tu else None', "do": ["[25]"]},
    {"ten": "bỏ bảng chủ đề không quân sự (census/sức khoẻ lọt vào)",
     "tim": "    if any(w in t for w in CHU_DE_KHONG_QUAN_SU):\n        return False",
     # CHỈ [29]: ca [26]/[27] còn bị TU_VO_HAI che nên không đỏ khi gỡ riêng bảng này.
     "thay": "    pass", "do": ["[29]"]},
]


def tu_kiem():
    import hashlib
    import re as _re
    import subprocess

    if bo_ca() != 0:
        print("\nTRƯỢT: bộ ca đã đỏ trên bản ĐÚNG.")
        return 1
    goc = pathlib.Path(__file__).read_text(encoding="utf-8")
    _cat = "\nBAN_HONG = ["
    than, duoi = goc.split(_cat, 1)
    duoi = _cat + duoi
    tong_ca = len(_re.findall(r'_ca\("\[\d+\]', goc))
    print("\nĐO BẢN HỎNG — %d bản:" % len(BAN_HONG))
    hong = 0
    for b in BAN_HONG:
        if than.count(b["tim"]) != 1:
            print("  ✗ %s — chuỗi neo khớp %d chỗ trong thân mã (phải đúng 1)"
                  % (b["ten"], than.count(b["tim"])))
            hong += 1
            continue
        nd = than.replace(b["tim"], b["thay"]) + duoi
        sha = hashlib.sha1(nd.encode("utf-8")).hexdigest()[:8]
        p = HERE / ("_thu-hong-%d-%s-do_tap_tran_thieu.py" % (os.getpid(), sha))
        try:
            p.write_text(nd, encoding="utf-8")
            r = subprocess.run([sys.executable, str(p), "--chi-bo-ca"],
                               capture_output=True, text=True)
            do_that = set(_re.findall(r"^  ✗ (\[\d+\])", r.stdout, _re.M))
            if not r.stdout.strip():
                print("  ✗ %s — bản hỏng KHÔNG in dòng ca nào:\n      %s"
                      % (b["ten"], (r.stderr or "").strip()[:300]))
                hong += 1
                continue
            if len(do_that) >= tong_ca:
                print("  ✗ %s — ĐỎ TOÀN BỘ %d ca: phép thay phá nền" % (b["ten"], len(do_that)))
                hong += 1
                continue
            thieu = [c for c in b["do"] if c not in do_that]
            if thieu:
                print("  ✗ %s — ca %s KHÔNG đỏ (đỏ thực tế: %s)"
                      % (b["ten"], ", ".join(thieu), ", ".join(sorted(do_that)) or "KHÔNG CÓ"))
                hong += 1
            else:
                print("  ✓ %s — bắt được (%s đỏ)" % (b["ten"], ", ".join(sorted(do_that))))
        finally:
            try:
                p.unlink()
            except OSError:
                pass
    print("─" * 78)
    print("%d/%d bản hỏng bị bắt" % (len(BAN_HONG) - hong, len(BAN_HONG)))
    return 0 if hong == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
