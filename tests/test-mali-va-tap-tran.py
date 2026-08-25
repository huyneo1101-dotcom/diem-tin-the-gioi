#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TEST hai thay đổi ngày 05/08/2026 (chỉ thị Huy).

> Nguyên văn: *"bỏ mục Mali trong file word gửi tele hàng ngày. Thêm mục Mali vào kết quả
> phần quét tập trận và thinktank. Đang có tập trận nào thì chỉ tập trung quét thông tin về
> tập trận đó. Tự động mở rộng nguồn quét tuỳ theo tập trận để tìm được tối đa thông tin."*

## Vì sao cả hai thay đổi này đều thuộc loại HỎNG THÌ IM LẶNG

- **Mali rời .docx**: nếu phần "thêm vào bản sáng" hụt (quên gate, quên payload, ba bảng khoá
  lệch nhau) thì tin Mali **mất hẳn khỏi mọi kênh gửi** — vẫn nằm trên web, vẫn được quét,
  nên không script nào báo lỗi và bảng `scan-gaps` vẫn ghi "Mali: đủ".
- **Tập trận động**: bảng từ khoá chủ đề 05 để RỖNG mặc định, chỉ được bơm lúc chạy. Quên gọi
  `nap_tap_tran_dang_chay()` ở một lớp quét nào đó là lớp ấy không xếp nổi bài nào vào chủ đề
  — y hệt cảnh "0 bài mỗi phiên" đã vá 02/08, chỉ khác nguyên nhân.

Chạy:
    python3 tests/test-mali-va-tap-tran.py
    python3 tests/test-mali-va-tap-tran.py --tu-kiem
"""
import hashlib
import importlib.util
import io
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
REPO_THU = pathlib.Path(os.environ.get("MALITT_REPO") or REPO)

MAKE_DOCX = REPO_THU / ".github" / "scripts" / "make_docx.py"
MORNING_JS = REPO_THU / ".github" / "scripts" / "send-morning-email.js"
TELEGRAM_PY = REPO_THU / ".github" / "scripts" / "send_telegram.py"
ADD_NEWS = REPO_THU / "scripts" / "add_news.py"
TAP_TRAN = REPO_THU / "scripts" / "tap_tran.py"
TOPICS = REPO_THU / "scripts" / "topics.py"
HARVEST = REPO_THU / "scripts" / "harvest.py"


def _nap(ten, path):
    khoa = ten + "_" + hashlib.sha1(str(path).encode()).hexdigest()[:8]
    spec = importlib.util.spec_from_file_location(khoa, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[khoa] = mod
    spec.loader.exec_module(mod)
    return mod


sys.path.insert(0, str(REPO_THU / "scripts"))
MD = _nap("make_docx", MAKE_DOCX)
TT = _nap("tap_tran", TAP_TRAN)
TOP = _nap("topics", TOPICS)
NG_MORNING = MORNING_JS.read_text(encoding="utf-8")
NG_TELEGRAM = TELEGRAM_PY.read_text(encoding="utf-8")
NG_HARVEST = HARVEST.read_text(encoding="utf-8")


def tin(title, url, summary="", cat="Chính trị", region=""):
    d = {"date": "2026-08-05", "category": cat, "title": title, "summary": summary,
         "sourceName": "Reuters", "sourceUrl": url, "significance": "x"}
    if region:
        d["region"] = region
    return d


# ── A. Mali rời .docx ─────────────────────────────────────────────────────────
def ca_01():
    """PHẢI CHẶN — .docx KHÔNG còn mục "Mỹ – Mali"."""
    secs = MD.build_sections([tin("Mỹ cân nhắc không kích JNIM ở Mali", "https://a/1")], [], [])
    ten = [t for t, _ in secs]
    assert not any("Mali" in t for t in ten), \
        f"mục Mali vẫn còn trong .docx (chỉ thị Huy 05/08 là BỎ): {ten}"


def ca_02():
    """PHẢI CHẶN — tin Mali KHÔNG được rơi sang mục khác của .docx.

    Đây là chiều hỏng nguy hiểm hơn cả việc còn mục: bỏ mục mà quên giữ phép lọc thì tin Sahel
    dồn vào "Nội bộ Mỹ", đúng lỗi Huy bắt 27/07 (*"đang tin khcn-qs tự nhiên thấy lòi ra tin
    Mali"*), chỉ khác chỗ rơi.
    """
    t = tin("Mỹ cân nhắc không kích JNIM ở Mali", "https://a/1")
    secs = MD.build_sections([t], [], [])
    for ten, ds in secs:
        assert not any(x.get("sourceUrl") == "https://a/1" for x in ds), \
            f"tin Mali lọt vào mục {ten!r} — phép lọc Mali đã bị gỡ cùng lúc bỏ mục"


def ca_03():
    """Đối chứng — tin KHÔNG phải Mali vẫn vào .docx bình thường."""
    t = tin("Thượng viện Mỹ thông qua dự luật ngân sách", "https://a/2")
    secs = MD.build_sections([t], [], [])
    co = [ten for ten, ds in secs if any(x.get("sourceUrl") == "https://a/2" for x in ds)]
    assert co, "tin thường bị mất khỏi .docx — bản vá bỏ mục Mali đã cắt nhầm"


def ca_04():
    """PHẢI KÊU — bỏ tin Mali phải in dòng ghi vết, không im lặng."""
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        MD.build_sections([tin("Diễn biến Sahel: JNIM tấn công Bamako", "https://a/3")], [], [])
    ra = buf.getvalue()
    assert "Mali" in ra and "docx" in ra.lower(), \
        f"bỏ tin Mali mà KHÔNG kêu — không ai soi ngược được bản tin rụng mấy tin: {ra!r}"


def ca_05():
    """Đối chứng chống kêu oan — lô không có tin Mali thì KHÔNG in dòng đó."""
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        MD.build_sections([tin("Hải quân Mỹ nhận tàu ngầm mới", "https://a/4",
                               cat="Công nghệ quân sự")], [], [])
    assert "Mali" not in buf.getvalue(), "kêu oan: lô không có tin Mali mà vẫn báo đã bỏ"


# ── B. Mali vào bản sáng ──────────────────────────────────────────────────────
def ca_06():
    """PHẢI CHẶN — `send-morning-email.js` phải có `diffMali` và gọi nó."""
    assert "function diffMali(" in NG_MORNING, "thiếu hàm diffMali — Mali không lên bản sáng"
    assert re.search(r"const\s+malis\s*=\s*diffMali\(", NG_MORNING), \
        "diffMali có mà KHÔNG ai gọi — hàm đúng mà không chạy thì mục vẫn trống"


def ca_07():
    """PHẢI CHẶN — Mali phải nằm trong GATE mở email sáng.

    Không có trong gate thì ngày nào chỉ có tin Mali là mất trắng: .docx đã bỏ mục này rồi,
    không còn kênh nào khác mang nó đi.
    """
    m = re.search(r"if \(!evs\.length[^)]*\)\s*\{", NG_MORNING)
    assert m, "không tìm thấy câu lệnh gate"
    assert "!malis.length" in m.group(0), \
        f"gate KHÔNG xét tin Mali → ngày chỉ có Mali sẽ không gửi gì: {m.group(0)!r}"


def ca_08():
    """PHẢI CHẶN — payload Telegram phải mang khoá `mali`, và `send_telegram.py` phải đọc."""
    assert re.search(r"^\s*mali:\s*malis\.slice", NG_MORNING, re.M), \
        "payload Telegram thiếu khoá `mali` → email có mục mà Telegram không có"
    assert 'pl.get("mali")' in NG_TELEGRAM, \
        "send_telegram.py không đọc khoá `mali` → khối Mali không bao giờ in ra"


def ca_09():
    """PHẢI CHẶN — BA bảng khoá Mali phải khớp nhau.

    `make_docx.py::MALI_KEYS` (lọc khỏi .docx) · `add_news.py::MALI_KEYS_ADD` (ngoại lệ cổng
    neo chủ đề 2) · bảng trong `send-morning-email.js` (đưa vào bản sáng). Lệch nhau thì tin
    Sahel vừa rơi khỏi .docx vừa không lên bản sáng — MẤT HẲN, không lỗi nào.
    """
    js = re.search(r"const MALI_KEYS = \[(.*?)\];", NG_MORNING, re.S)
    assert js, "không đọc được bảng khoá Mali trong send-morning-email.js"
    bo_js = set(re.findall(r"'([^']+)'", js.group(1)))
    bo_py = set(MD.MALI_KEYS)
    assert bo_js == bo_py, (
        "bảng khoá Mali LỆCH giữa make_docx.py và send-morning-email.js — "
        f"chỉ JS có: {sorted(bo_js - bo_py)} · chỉ Python có: {sorted(bo_py - bo_js)}")
    ng_add = ADD_NEWS.read_text(encoding="utf-8")
    m = re.search(r"MALI_KEYS_ADD\s*=\s*\((.*?)\)", ng_add, re.S)
    if m:
        bo_add = set(re.findall(r'"([^"]+)"', m.group(1)))
        assert bo_add <= bo_py, \
            f"add_news.py có khoá Mali mà make_docx.py không có: {sorted(bo_add - bo_py)}"


def ca_10():
    """Đối chứng — `laTinMali` phía JS nhận đúng tin Sahel và bỏ qua tin thường.

    Chạy THẬT bằng `jsc` (máy Huy không có node) chứ không đọc mã bằng mắt: bảng khoá đúng mà
    hàm bỏ dấu sai thì "Mali" vẫn nhận được còn "Sahel"/"châu Phi" thì không.
    """
    jsc = ("/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Helpers/jsc")
    if not os.path.exists(jsc):
        return  # máy không có jsc thì bỏ qua, đừng đỏ oan
    src = NG_MORNING[NG_MORNING.index("const MALI_KEYS"):NG_MORNING.index("function diffMali")]
    thu = ('%s\nvar ok1 = laTinMali({title:"Diễn biến Sahel hôm nay"});\n'
           'var ok2 = laTinMali({summary:"lực lượng Africa Corps của Nga"});\n'
           'var no1 = laTinMali({title:"Thượng viện Mỹ bỏ phiếu ngân sách"});\n'
           'print(ok1 + "," + ok2 + "," + no1);' % src)
    d = pathlib.Path(tempfile.mkdtemp())
    try:
        f = d / "thu.js"
        f.write_text(thu, encoding="utf-8")
        r = subprocess.run([jsc, str(f)], capture_output=True, text=True)
        ra = (r.stdout or "").strip()
        assert ra == "true,true,false", \
            f"laTinMali chạy sai (mong 'true,true,false'): {ra!r} · stderr={r.stderr[:200]!r}"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def ca_27():
    """PHẢI CHẶN — khoá Mali phải khớp theo BIÊN TỪ, ở CẢ BA nơi.

    Đo 26/08/2026 trên kho thật: tin *"Hải quân Mỹ công bố tên lửa không đối không tầm xa
    AIM-424 Malice"* bị gán chủ đề Mỹ–Mali vì chuỗi "mali" nằm trong chữ "Malice", rồi bị loại
    khỏi .docx theo chỉ thị 05/08/2026 — mất một tin công nghệ quân sự mà .docx vẫn đủ mục, tức
    hỏng câm. Cùng lối đó "niger" khớp "Nigeria".

    Ca [09] chỉ so BẢNG KHOÁ giữa ba nơi; bảng giống nhau mà phép so khác nhau thì vẫn lệch —
    đó là lỗ ca này bịt.
    """
    xau = [{"title": "Hải quân Mỹ công bố tên lửa không đối không tầm xa AIM-424 Malice"},
           {"title": "Nigeria đặt mua drone của Thổ Nhĩ Kỳ"},
           {"summary": "Bang California siết luật về malicious code"}]
    for it in xau:
        assert not MD.la_tin_mali(it), \
            f"make_docx nhận nhầm tin không phải Sahel: {(it.get('title') or it.get('summary'))!r}"
    ng_add = ADD_NEWS.read_text(encoding="utf-8")
    assert "_RE_MALI_ADD" in ng_add and "k in strip_accents(hay).lower()" not in ng_add, \
        "add_news.py còn so khoá Mali bằng chuỗi con — 'mali' sẽ khớp 'Malice'"
    assert "RE_MALI.some" in NG_MORNING and "MALI_KEYS.some(k => kho.includes(k))" not in NG_MORNING, \
        "send-morning-email.js còn so khoá Mali bằng chuỗi con"


def ca_28():
    """Đối chứng — tin Sahel THẬT vẫn phải nhận đủ, cả ba nơi (chống siết quá tay)."""
    tot = [{"title": "Quân đội Mali giao tranh với JNIM tại Kidal"},
           {"summary": "Pháp rút quân khỏi Sahel"},
           {"title": "Niger trục xuất đại sứ Mỹ"},
           {"summary": "Africa Corps của Nga hiện diện tại Bamako"}]
    for it in tot:
        assert MD.la_tin_mali(it), \
            f"bỏ sót tin Sahel thật: {(it.get('title') or it.get('summary'))!r}"


def ca_29():
    """Đối chứng — `laTinMali` phía JS cũng phải theo BIÊN TỪ (chạy thật bằng `jsc`)."""
    jsc = ("/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Helpers/jsc")
    if not os.path.exists(jsc):
        return  # máy không có jsc thì bỏ qua, đừng đỏ oan
    src = NG_MORNING[NG_MORNING.index("const MALI_KEYS"):NG_MORNING.index("function diffMali")]
    thu = ('%s\nvar no1 = laTinMali({title:"Hải quân Mỹ công bố tên lửa AIM-424 Malice"});\n'
           'var no2 = laTinMali({title:"Nigeria mua drone"});\n'
           'var ok1 = laTinMali({title:"Quân đội Mali giao tranh với JNIM"});\n'
           'print(no1 + "," + no2 + "," + ok1);' % src)
    d = pathlib.Path(tempfile.mkdtemp())
    try:
        f = d / "thu.js"
        f.write_text(thu, encoding="utf-8")
        r = subprocess.run([jsc, str(f)], capture_output=True, text=True)
        ra = (r.stdout or "").strip()
        assert ra == "false,false,true", \
            f"laTinMali phía JS còn so chuỗi con (mong 'false,false,true'): {ra!r}"
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ── C. Tập trận động ──────────────────────────────────────────────────────────
EX_ONGOING = {"name": "Pitch Black 2026 (Úc chủ trì, 20 nước tham gia)",
              "dates": "20/7 – 7/8/2026", "status": "ongoing",
              "location": "RAAF Darwin và Tindal", "summary": "Úc chủ trì, 20 nước"}
# status khai SAI (còn 'ongoing') dù đã kết thúc — ca thật trong DATA ngày 05/08/2026.
EX_DA_TAN = {"name": "Predator's Run 2026 (tập trận Mỹ - Úc - Philippines)",
             "dates": "21-29/07/2026", "status": "ongoing",
             "location": "Townsville, Queensland", "summary": "Mỹ - Úc - Philippines"}
EX_SAP = {"name": "Hán Quang 42 - Han Kuang 2026 (Đài Loan)",
          "dates": "5 – 14/8/2026", "status": "upcoming",
          "location": "Toàn đảo Đài Loan", "summary": "Đài Loan"}


def ca_11():
    """PHẢI CHẶN — cuộc đã KẾT THÚC không được coi là đang diễn ra, dù `status` khai `ongoing`.

    Đo thật 05/08/2026: `Predator's Run` (hết 29/07) và `RIMPAC` (hết 31/07) đều vẫn mang
    `status: "ongoing"` trong DATA — web không hiện sai vì nó tự suy từ `dates`, nên không ai
    buồn sửa. Quét theo `status` là đi tìm tin cho hai kỳ đã tàn.
    """
    ra = TT.dang_dien_ra([EX_DA_TAN], "2026-08-05")
    assert ra == [], f"cuộc đã kết thúc vẫn được bám (tin theo `status` thay vì `dates`): {ra}"


def ca_12():
    """PHẢI CHẶN — cuộc đang chạy phải được nhận, kể cả khi `status` khai `upcoming`."""
    ra = TT.dang_dien_ra([EX_SAP], "2026-08-05")
    assert len(ra) == 1, f"cuộc đang chạy (5–14/8, hôm nay 5/8) bị bỏ sót: {ra}"


def ca_13():
    """Đối chứng — không có cuộc nào đang chạy thì lấy cuộc SẮP diễn ra trong 7 ngày."""
    ra = TT.dang_dien_ra([EX_SAP], "2026-08-01")
    assert len(ra) == 1, "cuộc khai mạc sau 4 ngày phải được bám trước (tin chuẩn bị)"
    ra2 = TT.dang_dien_ra([EX_SAP], "2026-07-01")
    assert ra2 == [], f"cuộc còn hơn một tháng nữa mà đã bám: {ra2}"


def ca_14():
    """PHẢI CHẶN — từ khoá sinh ra KHÔNG được chứa mảnh tên nước.

    `"Toàn đảo Đài Loan"` từng cho ra `'loan'`, mà `'loan'` khớp trong "hỗn loạn"/"loan báo"
    → chủ đề tập trận hút tin vu vơ. Hỏng theo chiều RỘNG nên rất khó thấy trên bảng.
    """
    ks = TT.tu_khoa(EX_SAP)
    assert "loan" not in ks, f"từ khoá rác 'loan' lọt vào: {ks}"
    for k in ks:
        assert len(k) >= 4, f"từ khoá quá ngắn, sẽ khớp bừa: {k!r} trong {ks}"


def ca_15():
    """PHẢI CHẶN — từ khoá phải có CẢ dạng có dấu.

    `topics.match_topic` so regex trên văn bản GỐC (bảng tiếng Việt viết có dấu), nên bơm mỗi
    bản không dấu là chủ đề câm với mọi tiêu đề tiếng Việt.
    """
    ks = TT.tu_khoa(EX_SAP)
    assert any("á" in k or "Á" in k for k in ks), \
        f"không có từ khoá dạng CÓ DẤU → không khớp tiêu đề tiếng Việt: {ks}"
    assert "han quang" in ks, f"không có dạng KHÔNG DẤU → không khớp tiêu đề tiếng Anh: {ks}"


def ca_16():
    """Đối chứng — địa danh của cuộc VẪN được giữ làm từ khoá."""
    ks = TT.tu_khoa(EX_ONGOING)
    assert "darwin" in ks and "tindal" in ks, \
        f"mất địa danh — báo chí hay nhắc căn cứ thay vì tên cuộc: {ks}"


def ca_17():
    """PHẢI CHẶN — nước ĐĂNG CAI suy từ `location` trước, không phải từ `summary`.

    Vấp thật lúc dựng: gộp cả `summary` nên "Hán Quang 42 (Đài Loan)" trả `my` lên đầu và truy
    vấn thành `"Hán Quang" US` — đi hỏi báo Mỹ về một cuộc tập trận của Đài Loan.
    """
    ex = dict(EX_SAP, summary="Mỹ và Nhật Bản theo dõi sát cuộc diễn tập của Đài Loan")
    assert TT.nuoc_chu_nha(ex) == "dai loan", \
        f"nhận sai nước đăng cai: {TT.nuoc_chu_nha(ex)!r} (phải là 'dai loan')"


def ca_18():
    """PHẢI CHẶN — truy vấn phải mang TÊN RIÊNG, không được rộng.

    Chủ đề 05 giành URL trước chủ đề 02 nên truy vấn rộng sẽ nuốt cả tin không quân Úc thường.
    """
    qs = TT.truy_van(EX_ONGOING)
    assert qs, "không sinh được truy vấn nào"
    for q in qs:
        assert "pitch black" in q.lower(), f"truy vấn mất neo tên cuộc: {q!r}"
        assert "raaf" not in q.lower(), f"truy vấn quá rộng, nuốt tin RAAF thuần: {q!r}"


def ca_19():
    """Đối chứng — nguồn mở rộng phải bám nước ĐĂNG CAI."""
    dom = TT.nguon_mo_rong([EX_ONGOING])
    assert "defence.gov.au" in dom, f"thiếu nguồn tầng 1 của nước chủ nhà: {dom[:8]}"
    dom2 = TT.nguon_mo_rong([EX_SAP])
    assert any("tw" in d for d in dom2), f"thiếu nguồn bản địa Đài Loan: {dom2[:8]}"


def ca_20():
    """PHẢI CHẶN — `harvest.py::main()` phải gọi `nap_tap_tran_dang_chay` TRƯỚC các lớp quét.

    Hàm đúng mà gọi sau thì lớp RSS/HTML đã phân loại xong bằng bảng từ khoá RỖNG — chủ đề 05
    trống trơn, y hệt cảnh đã vá 02/08 nhưng nguyên nhân khác.
    """
    i_nap = NG_HARVEST.find("nap_tap_tran_dang_chay(str(today))")
    i_quet = NG_HARVEST.find("hits += harvest_rss(")
    assert i_nap > 0, "main() KHÔNG gọi nap_tap_tran_dang_chay — chủ đề tập trận sẽ trống"
    assert i_nap < i_quet, "gọi nạp SAU lớp quét — phân loại chạy trên bảng rỗng"


def ca_21():
    """PHẢI CHẶN — bảng chủ đề 05 phải RỖNG mặc định (không neo cứng tên kỳ nào)."""
    assert TOP.TOPIC_KEYWORDS_VI.get(TOP.CHU_DE_TAP_TRAN) == [], \
        "chủ đề tập trận có từ khoá cứng — đổi kỳ là phải sửa tay, đúng lỗ vừa vá"
    assert TOP.CHU_DE_TAP_TRAN not in ("Pitch Black", "Predator's Run"), \
        "nhãn chủ đề vẫn là tên một kỳ tập trận"


def ca_22():
    """PHẢI CHẶN — tin mang TÊN CUỘC phải về chủ đề 05, kể cả khi có từ khoá của chủ đề 02.

    Đây là lỗ đo được lúc dựng bộ test này (05/08/2026): tiêu đề thật *"Exercise Pitch Black
    wraps up at RAAF Darwin"* chứa `RAAF`, mà bảng "Úc & Biển Đông" đứng TRƯỚC trong thứ tự
    duyệt của `match_topic` — nên ở LỚP RSS/HTML (mỗi bài chỉ được gán MỘT nhãn) tin tập trận
    bị chủ đề 02 ăn mất, và `uu_tien_chu_de` không cứu được vì nó chỉ xử tranh chấp giữa hai
    bản CÙNG URL. Vá bằng cách đưa chủ đề tập trận lên đầu bảng duyệt khi bơm.
    """
    TOP.nap_tu_khoa_tap_tran(TT.tu_khoa(EX_ONGOING))
    try:
        assert TOP.match_topic("Exercise Pitch Black wraps up at RAAF Darwin", "both") \
            == TOP.CHU_DE_TAP_TRAN, "tin tập trận không được xếp vào chủ đề 05 sau khi bơm"
    finally:
        TOP.nap_tu_khoa_tap_tran([])


def ca_26():
    """Đối chứng chống nới tay — tin Úc/Biển Đông KHÔNG dính tên cuộc vẫn ở chủ đề 02.

    Đưa chủ đề tập trận lên đầu bảng duyệt là con dao hai lưỡi: bơm từ khoá quá rộng thì mọi
    tin không quân Úc chảy hết vào mục tập trận. Ca này canh đúng chiều đó.
    """
    TOP.nap_tu_khoa_tap_tran(TT.tu_khoa(EX_ONGOING))
    try:
        assert TOP.match_topic("RAAF receives new KC-30A tanker for Indo-Pacific ops", "both") \
            == "Úc & Biển Đông", "tin RAAF thuần bị mục tập trận nuốt — bơm từ khoá quá rộng"
        assert TOP.match_topic("China Coast Guard blocks Philippine boat at Scarborough",
                               "both") == "Úc & Biển Đông", "tin Biển Đông bị xếp nhầm"
    finally:
        TOP.nap_tu_khoa_tap_tran([])


def ca_23():
    """PHẢI CHẶN — bơm lần sau GHI ĐÈ, không cộng dồn.

    Cộng dồn thì từ khoá của kỳ đã tàn nằm lại và chủ đề bám tin cũ mãi.
    """
    TOP.nap_tu_khoa_tap_tran(["pitch black"])
    TOP.nap_tu_khoa_tap_tran(["han quang"])
    try:
        assert TOP.TOPIC_KEYWORDS_VI[TOP.CHU_DE_TAP_TRAN] == ["han quang"], \
            f"bơm cộng dồn: {TOP.TOPIC_KEYWORDS_VI[TOP.CHU_DE_TAP_TRAN]}"
        assert TOP.match_topic("Exercise Pitch Black at Darwin", "both") != TOP.CHU_DE_TAP_TRAN, \
            "bảng regex chưa được ghi đè — match_topic vẫn dùng từ khoá kỳ cũ"
    finally:
        TOP.nap_tu_khoa_tap_tran([])


def ca_24():
    """PHẢI CHẶN — `telegram_harvest.py` cũng phải bơm, không chỉ `harvest.py`.

    Hai lớp quét chạy trong hai tiến trình riêng, mỗi lớp nạp `topics` của chính nó.
    """
    ng = (REPO_THU / "scripts" / "telegram_harvest.py").read_text(encoding="utf-8")
    assert "nap_tu_khoa_tap_tran" in ng, \
        "lớp Telegram không bơm từ khoá tập trận → không xếp được bài nào vào chủ đề 05"


def ca_25():
    """Đối chứng — `doc_dai_ngay` khớp ĐÚNG `index.html::evRange` trên các khuôn ngày thật."""
    bo = [("20/7 – 7/8/2026", (20260720, 20260807)),
          ("21-29/07/2026", (20260721, 20260729)),
          ("13 – 24/7/2026 (giai đoạn 2)", (20260713, 20260724)),
          ("24/7/2026", (20260724, 20260724)),
          ("Tháng 9/2026", None)]
    for s, mong in bo:
        assert TT.doc_dai_ngay(s) == mong, \
            f"parse sai {s!r}: {TT.doc_dai_ngay(s)} (mong {mong})"


CA = [
    ("[01] PHẢI CHẶN: .docx KHÔNG còn mục Mỹ – Mali", ca_01),
    ("[02] PHẢI CHẶN: tin Mali không rơi sang mục khác của .docx", ca_02),
    ("[03] đối chứng: tin thường vẫn vào .docx", ca_03),
    ("[04] PHẢI KÊU: bỏ tin Mali phải in dòng ghi vết", ca_04),
    ("[05] đối chứng: lô không có Mali thì không kêu oan", ca_05),
    ("[06] PHẢI CHẶN: bản sáng có diffMali và CÓ GỌI nó", ca_06),
    ("[07] PHẢI CHẶN: Mali nằm trong gate mở email sáng", ca_07),
    ("[08] PHẢI CHẶN: payload Telegram có khoá mali và bên kia đọc", ca_08),
    ("[09] PHẢI CHẶN: ba bảng khoá Mali khớp nhau", ca_09),
    ("[10] đối chứng: laTinMali phía JS chạy đúng (jsc thật)", ca_10),
    ("[11] PHẢI CHẶN: cuộc đã tàn không được bám dù status ongoing", ca_11),
    ("[12] PHẢI CHẶN: cuộc đang chạy được bám dù status upcoming", ca_12),
    ("[13] đối chứng: cuộc sắp khai mạc trong 7 ngày mới được bám", ca_13),
    ("[14] PHẢI CHẶN: từ khoá không chứa mảnh tên nước", ca_14),
    ("[15] PHẢI CHẶN: từ khoá có CẢ dạng có dấu", ca_15),
    ("[16] đối chứng: địa danh của cuộc vẫn được giữ", ca_16),
    ("[17] PHẢI CHẶN: nước đăng cai suy từ location trước", ca_17),
    ("[18] PHẢI CHẶN: truy vấn mang tên riêng, không rộng", ca_18),
    ("[19] đối chứng: nguồn mở rộng bám nước đăng cai", ca_19),
    ("[20] PHẢI CHẶN: harvest gọi nạp TRƯỚC các lớp quét", ca_20),
    ("[21] PHẢI CHẶN: bảng chủ đề 05 rỗng mặc định", ca_21),
    ("[22] PHẢI CHẶN: tin mang tên cuộc về chủ đề 05 dù có RAAF", ca_22),
    ("[23] PHẢI CHẶN: bơm lần sau ghi đè, không cộng dồn", ca_23),
    ("[24] PHẢI CHẶN: lớp Telegram cũng bơm từ khoá", ca_24),
    ("[25] đối chứng: doc_dai_ngay khớp evRange trên khuôn thật", ca_25),
    ("[26] đối chứng: tin RAAF/Biển Đông thuần vẫn ở chủ đề 02", ca_26),
    ("[27] PHẢI CHẶN: khoá Mali khớp theo BIÊN TỪ ở cả ba nơi ('Malice' không phải Mali)", ca_27),
    ("[28] đối chứng: tin Sahel thật vẫn nhận đủ", ca_28),
    ("[29] đối chứng: laTinMali phía JS cũng theo biên từ (jsc thật)", ca_29),
]

# (nhãn, (tìm, thay), các ca PHẢI ĐỎ)
BAN_HONG = [
    ("trả lại mục Mali vào .docx",
     ('        (MUC_GHI_NGAY, sec3 + list(events)),\n    ]',
      '        (MUC_GHI_NGAY, sec3 + list(events)),\n        ("Mỹ – Mali", mali),\n    ]'),
     [1]),
    ("bỏ mục Mali NHƯNG gỡ luôn phép lọc (tin Sahel dồn vào mục 1)",
     ("    mali = [it for it in us + world if la_tin_mali(it)]",
      "    mali = []"),
     [2]),
    ("bỏ tin Mali trong im lặng, không kêu",
     ('    if mali:\n        # KÊU, không im.', '    if False:\n        # KÊU, không im.'),
     [4]),
    ("Mali rơi khỏi gate mở email sáng",
     ("if (!evs.length && !weekly && !anas.length && !malis.length) {",
      "if (!evs.length && !weekly && !anas.length) {"),
     [7]),
    ("payload Telegram thiếu khoá mali",
     ("      mali: malis.slice(0, MALI_MAX).map(a => ({",
      "      maliBoQua: malis.slice(0, MALI_MAX).map(a => ({"),
     [8]),
    ("bảng khoá Mali phía JS lệch khỏi bản Python",
     ("const MALI_KEYS = ['mali', 'jnim', 'bamako', 'sahel',",
      "const MALI_KEYS = ['mali', 'jnim', 'bamako',"),
     [9, 10]),
    ("tin `status` thay vì tính từ `dates` (bám cả kỳ đã tàn)",
     ('    ongoing = [e for e in exs if trang_thai(e, hom_nay) == "ongoing"]',
      '    ongoing = [e for e in exs if (e.get("status") or "") == "ongoing"]'),
     [11, 12]),
    ("bỏ lọc mảnh tên nước khỏi từ khoá (rác 'loan' quay lại)",
     ("        if k not in _manh_nuoc:\n            ra.append(k)",
      "        ra.append(k)"),
     [14]),
    # ⚠️ Phải gỡ CẢ HAI chỗ sinh dạng có dấu (tên có năm VÀ tên không năm). Bản đầu chỉ gỡ chỗ
    # thứ nhất ⇒ nhánh `kn` vẫn sinh "hán quang" và ca [15] xanh — đúng bẫy "còn lớp khác che"
    # đã đúc trong CLAUDE.md: gỡ một lớp thì lớp kia gánh, và mình tưởng ca đó vô dụng.
    ("chỉ sinh từ khoá dạng KHÔNG DẤU",
     ("        ra.append(tn.lower())\n"
      "        if _khong_dau(tn) != tn.lower():\n"
      "            ra.append(_khong_dau(tn))\n"
      "        kn = ten_khong_nam(tn)\n"
      "        if kn and kn != tn:\n"
      "            ra.append(kn.lower())\n"
      "            if _khong_dau(kn) != kn.lower():\n"
      "                ra.append(_khong_dau(kn))",
      "        ra.append(_khong_dau(tn))\n"
      "        kn = ten_khong_nam(tn)\n"
      "        if kn and kn != tn:\n"
      "            ra.append(_khong_dau(kn))"),
     [15]),
    ("nước đăng cai lấy từ cac_nuoc()[0] (gộp cả summary)",
     ('    for truong in ("location", "name"):',
      '    for truong in ("summary", "location", "name"):'),
     [17]),
    ("không đưa chủ đề tập trận lên đầu bảng duyệt (chủ đề 02 ăn mất)",
     ("    for bang in (_RE_VI, _RE_EN):\n        cu = {k: v for k, v in bang.items() "
      "if k != CHU_DE_TAP_TRAN}\n        bang.clear()\n"
      "        bang[CHU_DE_TAP_TRAN] = list(pats)\n        bang.update(cu)",
      "    _RE_VI[CHU_DE_TAP_TRAN] = list(pats)\n    _RE_EN[CHU_DE_TAP_TRAN] = list(pats)"),
     [22]),
    ("bơm từ khoá CỘNG DỒN thay vì ghi đè",
     ("    TOPIC_KEYWORDS_VI[CHU_DE_TAP_TRAN] = list(keys)",
      "    TOPIC_KEYWORDS_VI[CHU_DE_TAP_TRAN] = "
      "list(TOPIC_KEYWORDS_VI.get(CHU_DE_TAP_TRAN) or []) + list(keys)"),
     [23]),
    ("khoá Mali quay lại so CHUỖI CON ('mali' khớp 'Malice')",
     ("    return any(p.search(kho) for p in _RE_MALI)",
      "    return any(k in kho for k in MALI_KEYS)"),
     [27]),
    ("nạp tập trận SAU các lớp quét",
     ("    nap_tap_tran_dang_chay(str(today))\n\n    chi_dinh =",
      "    chi_dinh ="),
     [20]),
]

_FILE_CHEP = [
    (".github/scripts", ("make_docx.py", "send-morning-email.js", "send_telegram.py",
                         "so_da_gui.py", "kiem_luat_push.py")),
    ("scripts", ("tap_tran.py", "topics.py", "harvest.py", "add_news.py",
                 "telegram_harvest.py", "tin_jaylam.py", "analyses_store.py")),
]


def _dung_ban_sao(dich, tim, thay):
    """Bản sao repo tối giản, GIỮ NGUYÊN CÂY thư mục.

    ⚠️ `make_docx.py` suy đường tới `scripts/` từ vị trí CHÍNH NÓ (`dirname` ba lần) để
    `from topics import ...`. Copy phẳng thì phép suy đó trỏ ra ngoài thư mục tạm ⇒
    `ModuleNotFoundError` ngay lúc nạp ⇒ tiến trình con không in nổi một dòng ✓/✗ và
    `--tu-kiem` đọc thành "0 ca đỏ". Đây là bẫy đã ghi trong CLAUDE.md, vấp thật 02/08.
    """
    da_thay = 0
    for thu_muc, tens in _FILE_CHEP:
        (dich / thu_muc).mkdir(parents=True, exist_ok=True)
        for ten in tens:
            goc_p = REPO / thu_muc / ten
            if not goc_p.exists():
                continue
            noi_dung = goc_p.read_text(encoding="utf-8")
            if tim in noi_dung:
                noi_dung = noi_dung.replace(tim, thay)
                da_thay += 1
            (dich / thu_muc / ten).write_text(noi_dung, encoding="utf-8")
    for ten in ("index.html",):
        if (REPO / ten).exists():
            shutil.copy2(REPO / ten, dich / ten)
    return da_thay


def chay():
    print(f"TEST Mali rời .docx + tập trận động — {REPO_THU}")
    print("═" * 78)
    do = []
    for nhan, fn in CA:
        try:
            fn()
            print(f"  ✓ {nhan}")
        except Exception as e:
            print(f"  ✗ {nhan}\n        │ {e}")
            do.append(int(nhan[1:3]))
    print("═" * 78)
    print(f"{len(CA) - len(do)}/{len(CA)} ca đạt" + (f" · ĐỎ: {do}" if do else ""))
    return 1 if do else 0


def tu_kiem():
    print("TỰ KIỂM — dựng bản đã gỡ dòng bảo vệ, các ca đã khai PHẢI ĐỎ")
    print("═" * 78)
    goc = "\n".join(
        (REPO / tm / t).read_text(encoding="utf-8")
        for tm, tens in _FILE_CHEP for t in tens if (REPO / tm / t).exists())
    hong = 0
    for nhan, (tim, thay), ca_phai_do in BAN_HONG:
        if goc.count(tim) != 1:
            print(f"  ✗ {nhan}\n        │ KHÔNG áp được phép thay: {goc.count(tim)} chỗ khớp "
                  f"(cần đúng 1). Mã nguồn đã đổi → sửa lại neo, đừng sửa ca.")
            hong += 1
            continue
        d = pathlib.Path(tempfile.mkdtemp(
            prefix="malitt-%d-%s-" % (os.getpid(),
                                      hashlib.sha1(thay.encode()).hexdigest()[:8])))
        try:
            _dung_ban_sao(d, tim, thay)
            env = dict(os.environ, MALITT_REPO=str(d))
            r = subprocess.run([sys.executable, str(pathlib.Path(__file__).resolve())],
                               capture_output=True, text=True, env=env)
        finally:
            shutil.rmtree(d, ignore_errors=True)
        do = {int(m.group(1)) for m in
              (re.match(r"\s*✗ \[(\d+)\]", dong) for dong in r.stdout.splitlines()) if m}
        # Bản hỏng làm ĐỎ TOÀN BỘ ca = phép thay phá nền (lỗi cú pháp/import), không phải gỡ
        # đúng một lớp vá — nó không chứng minh được ca nào có răng.
        if len(do) == len(CA):
            print(f"  ✗ {nhan}\n        │ ĐỎ TOÀN BỘ {len(CA)} ca → phép thay phá nền, "
                  f"sửa lại phép thay")
            hong += 1
            continue
        thieu = [c for c in ca_phai_do if c not in do]
        if thieu:
            print(f"  ✗ {nhan}\n        │ ca {thieu} VẪN XANH trên bản hỏng "
                  f"(đỏ thực tế: {sorted(do)}) → ca đó không bắt được lỗi")
            hong += 1
        else:
            print(f"  ✓ {nhan} — ca {ca_phai_do} đỏ đúng như khai")
    print("═" * 78)
    print("❌ %d bản hỏng LỌT" % hong if hong else "✅ Mọi bản hỏng đều bị bắt")
    return 1 if hong else 0


if __name__ == "__main__":
    sys.exit(tu_kiem() if "--tu-kiem" in sys.argv else chay())
