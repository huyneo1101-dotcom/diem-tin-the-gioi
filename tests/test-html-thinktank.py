#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CANH lớp [HTML] quét think-tank của `scripts/add_analyses.py` (dựng 30/07/2026).

VÌ SAO CẦN: lớp này thuộc loại **hỏng thì im lặng** đúng nghĩa. Nó quét HTML thô của trang
danh sách 10 viện không có RSS; mọi kiểu hỏng đều KHÔNG phát ra lỗi nào:

| Hỏng ở đâu | Hậu quả | Có thấy lỗi không |
|---|---|---|
| viện đổi giao diện ⇒ biểu thức path hết khớp | 0 bài, nhìn y hệt "hôm nay viện không ra bài" | KHÔNG |
| biểu thức path quá lỏng | link `/topics/`, `/programs/` lọt vào làm ứng viên | KHÔNG |
| mất lọc khung ngày | bài 6 tháng tuổi nằm chung danh sách "bài mới trong tuần" | KHÔNG |
| mất bước mở bài đọc meta | mọi viện không in ngày cạnh tiêu đề rơi khỏi danh sách | KHÔNG |
| mất quy đổi múi giờ | bài đăng đêm giờ Mỹ lệch một ngày, rơi ra/vào khung sai | KHÔNG |
| mất trần HTML_LINK_CAP | một trang lưu trữ kéo theo hàng trăm lượt curl | KHÔNG (chỉ chậm) |
| domain quét về không nằm trong THINKTANK_DOMAINS | quét ra bài rồi guardrail chặn lúc NẠP | KHÔNG, tới lúc nạp mới biết |

    python3 tests/test-html-thinktank.py
    python3 tests/test-html-thinktank.py --tu-kiem   # chứng minh bộ ca này BẮT ĐƯỢC lỗi

⚠️ Bộ ca này KHÔNG chạm mạng: `curl` của module bị tráo bằng bộ trang giả. Nhờ vậy nó chạy
được cả khi nguồn ngoài chết, và kết quả không đổi theo ngày.
⚠️ Nạp module trong TIẾN TRÌNH (không `subprocess`) — `subprocess` luôn nạp bản THẬT trên đĩa
nên `--tu-kiem` không tráo được bản hỏng, ca sẽ xanh trên cả bản đúng lẫn bản hỏng (bài học
`test-cong-vow.py` bên Rèn 66, 29/07/2026).
"""
import contextlib
import datetime
import importlib.util
import io
import os
import re
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "add_analyses.py"

# ⚠️ ĐỪNG BỎ DÒNG NÀY. Không có nó thì `--tu-kiem` CHẬP CHỜN — đo thật 30/07/2026: 6 lượt chạy
# ra 5 lần "1 bản hỏng không bị bắt" + 1 lần "đạt", cùng một mã nguồn. Nguyên nhân: các bản hỏng
# nối nhau ghi vào cùng một đường dẫn, mà `__pycache__` khoá theo (tên · size · mtime tính bằng
# GIÂY) — hai bản hỏng viết trong cùng một giây và tình cờ bằng size thì lượt sau nạp lại
# bytecode của lượt trước, tức đo nhầm bản hỏng. Bản hỏng nay còn mang thêm số thứ tự (xem
# `tu_kiem`), hai lớp chặn cùng một lỗi. Phép tự kiểm lúc xanh lúc đỏ còn tệ hơn không có: nó
# dạy người đọc bỏ qua màu đỏ.
sys.dont_write_bytecode = True

HOM_NAY = datetime.date(2026, 7, 30)          # ghim ngày để ca không đổi kết quả theo hôm chạy

# Trang thật nặng 70-500KB; chốt "trang dưới 2000 byte là trang chặn" trong `harvest_html_site`
# vì thế phải được thoả bằng độn, nếu không mọi ca dưới đây đỏ vì lý do sai.
DON = "<!-- " + ("noi dung phu cho du dai nhu trang that. " * 60) + " -->\n"

# ── Trang danh sách GIẢ, dựng theo đúng hình dạng đã đo được ở trang thật 30/07/2026 ────────
TRANG = DON + """<html><body>
<a href="/topics/an-ninh-nang-luong-vung-vinh">Chuyen muc an ninh nang luong Vung Vinh</a>
<div class="card"><span class="date">2026-07-29</span>
  <a href="/analysis/eo-bien-hormuz-va-thuy-loi-thuong-mai/">Eo bien Hormuz va tuyen thuong mai
  cua khu vuc Vung Vinh nam 2026</a></div>
<div class="card"><span class="date">2026-01-05</span>
  <a href="/analysis/bai-cu-tu-thang-mot-nam-nay/">Bai cu tu thang Mot khong duoc vao danh sach
  ung vien tuan nay</a></div>
<div class="card"><span class="date">2026-07-28</span>
  <a href="/analysis/hoi-thao-thang-tam-ve-vung-vinh/transcript/">Ban ghi hoi thao thang Tam
  ve an ninh Vung Vinh va bien Do</a></div>
<div class="card"><span class="date">2026-07-28</span>
  <a href="https://bao-khac.example.com/analysis/bai-o-ten-mien-khac/">Bai o ten mien khac
  khong duoc lay vao danh sach</a></div>
<div class="card"><span class="date">2026-07-27</span>
  <a href="/analysis/bai-nay-da-co-trong-kho-roi/">Bai nay da co trong kho DATA nen phai bi
  loai khoi ung vien</a></div>
<div class="card"><span class="date">2026-07-26</span>
  <a href="/analysis/ban-tin-podcast-hang-tuan-cua-vien/">Ban tin podcast hang tuan cua vien
  ve an ninh khu vuc</a></div>
<div class="card">
  <a href="/analysis/bai-khong-in-ngay-canh-tieu-de/">Bai nay khong in ngay canh tieu de nen
  phai mo trang bai ra doc meta</a></div>
<div class="card">
  <a href="/analysis/bai-dang-dem-gio-my/">Bai dang luc 23h30 gio My tuc da sang ngay hom sau
  o gio Viet Nam</a></div>
</body></html>"""

BAI_CO_META = """<html><head>
<script type="application/ld+json">{"@type":"Article","datePublished":"2026-07-28T09:00:00+00:00"}</script>
</head><body>noi dung</body></html>"""

BAI_DEM_GIO_MY = """<html><head>
<meta property="article:published_time" content="2026-07-29T23:30:00-04:00" />
</head><body>noi dung</body></html>"""

# FAS bọc cả thẻ bài trong <a> nên tiêu đề dính đuôi máy móc.
TRANG_DUOI_TIEU_DE = DON + """<html><body>
<div class="card"><span class="date">2026-07-29</span>
  <a href="/publication/bao-cao-ve-rui-ro-hat-nhan/">Bao cao ve rui ro hat nhan toan cau nam
  2026 07.29.26 | 4 min read read more</a></div>
</body></html>"""

# Trang challenge của Cloudflare — CỐ Ý để trong đó một link đúng dạng bài. Không có link nào
# thì ca "trang bị chặn" xanh cả trên bản đúng lẫn bản gỡ chốt (trang lỗi vốn không ra link),
# tức ca vô dụng. Có link thì ca mới đo được đúng cái chốt đang canh.
TRANG_CHAN = ("<html><body><h1>Just a moment...</h1><p>Checking your browser</p>"
              '<a href="/analysis/quay-lai-trang-danh-sach-phan-tich/">Quay lai trang danh sach '
              "phan tich cua vien</a></body></html>")

TRANG_NHIEU_LINK = DON + "<html><body>" + "".join(
    f'<div class="card"><span class="date">2026-07-29</span>'
    f'<a href="/analysis/bai-so-{i:03d}-trong-trang-luu-tru/">Bai so {i:03d} trong trang luu tru '
    f'cua vien nghien cuu</a></div>' for i in range(40)) + "</body></html>"

# ── Trang kiểu JIIA: ngày nằm trong TÊN FILE, còn cạnh tiêu đề chỉ in NĂM/THÁNG ────────────
# Dựng theo hình dạng đo được 20/08/2026 ở `jiia.or.jp/en/column/`. Đây là ca mà bước (1) và
# bước (2) đều ra kết quả SAI chứ không phải ra rỗng — nguy hiểm hơn hẳn, vì rỗng thì `--kiem-html`
# kêu còn sai thì không ai thấy.
TRANG_NGAY_TRONG_TEN_FILE = DON + """<html><body>
<div class="card"><span class="date">2026/07/20</span>
  <a href="/eng/report/2026/07/20260728.html">Bao cao ve chuyen doi cong nghiep quoc phong
  Nhat Ban nam 2026 Taro Yamada (Vien truong) 28.07.2026</a></div>
<div class="card"><span class="date">2026/07/26</span>
  <a href="/eng/report/2026/07/bao-cao-thuong-nien-cua-vien.html">Bao cao thuong nien cua vien
  ve an ninh khu vuc Dong Bac A</a></div>
<div class="card"><span class="date">2026/07/25</span>
  <a href="/eng/report/2026/07/asb44en-20260712345.html">Ma bao cao co chuoi so dai khong phai
  la ngay thang gi ca</a></div>
</body></html>"""

GOC = "https://vien-gia.example.org"
TRANG_DS = f"{GOC}/analysis/"
PATH_RE = r"^/analysis/[^/]{15,}"

KHO_GIA = {f"{GOC}/analysis/bai-nay-da-co-trong-kho-roi/"}

BO_TRANG = {
    TRANG_DS: TRANG,
    f"{GOC}/analysis/bai-khong-in-ngay-canh-tieu-de/": BAI_CO_META,
    f"{GOC}/analysis/bai-dang-dem-gio-my/": BAI_DEM_GIO_MY,
    f"{GOC}/publications/": TRANG_DUOI_TIEU_DE,
    f"{GOC}/bi-chan/": TRANG_CHAN,
    f"{GOC}/luu-tru/": TRANG_NHIEU_LINK,
    f"{GOC}/eng-column/": TRANG_NGAY_TRONG_TEN_FILE,
}


def nap_module(duong_dan=None):
    """Nạp add_analyses.py (bản thật hoặc bản hỏng) rồi tráo `curl` bằng bộ trang giả."""
    p = pathlib.Path(duong_dan or SCRIPT)
    spec = importlib.util.spec_from_file_location(f"aa_{os.getpid()}_{p.stem}", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # URL lạ trả rỗng: nhờ vậy `list_candidates` chạy được mà không chạm mạng thật.
    mod.curl = lambda url: BO_TRANG.get(url, "").encode("utf-8")
    return mod


def _quet(mod, trang=TRANG_DS, path_re=PATH_RE, kho=None):
    rows, st = mod.harvest_html_site(("Viện giả", trang, path_re, "Khu vực giả"),
                                     kho if kho is not None else KHO_GIA, HOM_NAY)
    return {l.rsplit("/", 2)[-2] if l.endswith("/") else l.rsplit("/", 1)[-1]: (d, t)
            for d, t, l in rows}, st, rows


# ─────────────────────────────── các ca ───────────────────────────────
def ca_lay_duoc_bai_moi(mod):
    slug, _st, _ = _quet(mod)
    if "eo-bien-hormuz-va-thuy-loi-thuong-mai" not in slug:
        return "bài mới trong khung 7 ngày KHÔNG được lấy — lớp quét coi như chết"
    if slug["eo-bien-hormuz-va-thuy-loi-thuong-mai"][0] != datetime.date(2026, 7, 29):
        return f"ngày sai: {slug['eo-bien-hormuz-va-thuy-loi-thuong-mai'][0]}"
    return None


def ca_loai_bai_ngoai_khung(mod):
    slug, _st, _ = _quet(mod)
    if "bai-cu-tu-thang-mot-nam-nay" in slug:
        return "bài tháng Một lọt vào danh sách 'bài mới trong tuần'"
    return None


def ca_loai_link_dieu_huong(mod):
    slug, _st, _ = _quet(mod)
    if any("an-ninh-nang-luong" in s for s in slug):
        return "link chuyên mục /topics/ lọt vào làm ứng viên bài"
    return None


def ca_loai_duong_dan_rac(mod):
    """Đường dẫn rác phải khớp CẢ biểu thức path, nếu không thì biểu thức path gánh mất và
    ca này xanh cả trên bản đã gỡ NOISE_PATHS — tức đo nhầm lớp (bài học 29/07: bảo vệ nhiều
    lớp chồng nhau thì gỡ một lớp vẫn xanh)."""
    slug, _st, _ = _quet(mod)
    if any("hoi-thao-thang-tam" in s or "transcript" in s for s in slug):
        return "link /transcript (NOISE_PATHS) lọt vào làm ứng viên bài"
    return None


def ca_loai_ten_mien_khac(mod):
    slug, _st, _ = _quet(mod)
    if any("ten-mien-khac" in s for s in slug):
        return "link sang tên miền khác lọt vào — mục Think-tank sẽ dính bài báo chí"
    return None


def ca_loai_bai_da_co(mod):
    slug, _st, _ = _quet(mod)
    if "bai-nay-da-co-trong-kho-roi" in slug:
        return "bài đã có trong kho vẫn được liệt kê — agent tốn công chọn rồi bị guardrail chặn"
    return None


def ca_giu_bai_co_chu_podcast_trong_tieu_de(mod):
    """ĐỐI CHỨNG: lọc rác phải theo ĐƯỜNG DẪN, không theo tiêu đề."""
    slug, _st, _ = _quet(mod)
    if "ban-tin-podcast-hang-tuan-cua-vien" not in slug:
        return "bài có chữ 'podcast' trong TIÊU ĐỀ bị loại oan — lọc rác đang bắt nhầm tiêu đề"
    return None


def ca_mo_bai_lay_ngay_that(mod):
    slug, _st, _ = _quet(mod)
    if "bai-khong-in-ngay-canh-tieu-de" not in slug:
        return "bài không in ngày cạnh tiêu đề bị bỏ — bước mở trang bài đọc meta đã chết"
    if slug["bai-khong-in-ngay-canh-tieu-de"][0] != datetime.date(2026, 7, 28):
        return f"ngày đọc từ meta sai: {slug['bai-khong-in-ngay-canh-tieu-de'][0]}"
    return None


def ca_quy_doi_mui_gio(mod):
    slug, _st, _ = _quet(mod)
    if "bai-dang-dem-gio-my" not in slug:
        return "bài đăng đêm giờ Mỹ bị bỏ"
    d = slug["bai-dang-dem-gio-my"][0]
    if d != datetime.date(2026, 7, 30):
        return f"đăng 29/07 23h30 giờ Mỹ (-04:00) phải ra 30/07 giờ VN, đang ra {d}"
    return None


def ca_don_duoi_tieu_de(mod):
    slug, _st, _ = _quet(mod, trang=f"{GOC}/publications/", path_re=r"^/publication/[^/]{10,}",
                         kho=set())
    if not slug:
        return "không lấy được bài nào từ trang kiểu FAS"
    t = list(slug.values())[0][1]
    if "read more" in t or "min read" in t or "07.29.26" in t:
        return f"tiêu đề còn dính đuôi máy móc: {t!r}"
    return None


def ca_tran_so_link(mod):
    _slug, st, rows = _quet(mod, trang=f"{GOC}/luu-tru/", kho=set())
    if st["link"] > mod.HTML_LINK_CAP:
        return (f"trang lưu trữ 40 bài lấy hết {st['link']} link — mất trần HTML_LINK_CAP, "
                f"mỗi link là một lượt curl dò ngày")
    return None


def ca_trang_bi_chan_khong_ra_link(mod):
    _slug, st, _ = _quet(mod, trang=f"{GOC}/bi-chan/", kho=set())
    if st["link"]:
        return "trang challenge của Cloudflare vẫn ra link bài — sẽ nạp rác"
    return None


def ca_path_chet_thi_phai_keu(mod):
    """PHẢI KÊU: biểu thức path không khớp gì ⇒ `--kiem-html` phải thoát mã 3, không im."""
    goc, goc_dom = mod.THINKTANK_HTML, mod.THINKTANK_DOMAINS
    mod.THINKTANK_HTML = [("Viện giả", TRANG_DS, r"^/khong-bao-gio-khop/[^/]+", "Khu vực giả")]
    mod.THINKTANK_DOMAINS = _dom_chi_vien_gia(mod)
    try:
        buf = io.StringIO()
        ma = 0
        try:
            with contextlib.redirect_stdout(buf):
                mod.kiem_html()
        except SystemExit as ex:
            ma = ex.code or 0
        if ma == 0:
            return "biểu thức path chết mà --kiem-html vẫn báo bình thường (mã 0)"
        if "CHẾT" not in buf.getvalue():
            return "có kêu nhưng không chỉ ra trang nào chết"
        return None
    finally:
        mod.THINKTANK_HTML, mod.THINKTANK_DOMAINS = goc, goc_dom


def _dom_chi_vien_gia(mod):
    """Guardrail rút về ĐÚNG domain của trang giả, dùng cho hai ca tráo `THINKTANK_HTML`.

    Vì sao cần: `kiem_html` gộp HAI nhánh vào một mã thoát — trang chết (mã 3) và domain mồ côi
    (mã 4). Ca nào tráo `THINKTANK_HTML` bằng bảng một dòng thì mọi domain HTML THẬT lập tức
    thành mồ côi, nên ca đối chứng đỏ vì nhánh nó KHÔNG định đo. Trước 21/08/2026 nó xanh chỉ
    vì mọi domain trong bảng HTML khi ấy tình cờ còn nằm cả ở `WEBSEARCH_ONLY`; 09 viện cắm
    hôm đó rời khỏi danh sách ấy là giả định ngầm vỡ ngay. Ghim guardrail lại là cách cô lập
    đúng nhánh, thay vì nới điều kiện của ca cho hết đỏ.
    """
    import urllib.parse
    return {urllib.parse.urlparse(TRANG_DS).netloc.replace("www.", "")}


def ca_trang_song_thi_khong_keu_oan(mod):
    """ĐỐI CHỨNG của ca trên: trang ra link bình thường thì tuyệt đối không được kêu."""
    goc, goc_dom = mod.THINKTANK_HTML, mod.THINKTANK_DOMAINS
    mod.THINKTANK_HTML = [("Viện giả", TRANG_DS, PATH_RE, "Khu vực giả")]
    mod.THINKTANK_DOMAINS = _dom_chi_vien_gia(mod)
    try:
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                mod.kiem_html()
        except SystemExit as ex:
            if ex.code:
                return f"trang sống mà --kiem-html kêu chết (mã {ex.code})"
        return None
    finally:
        mod.THINKTANK_HTML, mod.THINKTANK_DOMAINS = goc, goc_dom


def ca_domain_phai_qua_duoc_guardrail(mod):
    """Domain quét về mà không thuộc THINKTANK_DOMAINS thì tới lúc NẠP mới bị chặn."""
    import urllib.parse
    thieu = []
    for _ten, url, _re, _kv in mod.THINKTANK_HTML:
        dom = urllib.parse.urlparse(url).netloc.replace("www.", "")
        if not mod.is_thinktank(f"https://{dom}/x"):
            thieu.append(dom)
    if thieu:
        return ("domain quét về nhưng guardrail nạp sẽ chặn: " + " · ".join(thieu)
                + " — thêm vào THINKTANK_DOMAINS")
    return None


def ca_khong_giuc_websearch_nguon_da_quet(mod):
    """Nguồn đã có feed/HTML thì không được nằm trong dòng 'phải bù bằng WebSearch'."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        mod.list_candidates()
    duoi = buf.getvalue().split("phải bù bằng")[-1]
    thua = [d for d in ("csis.org", "cnas.org", "wilsoncenter.org", "belfercenter.org",
                        "fpri.org", "orfonline.org", "spf.org", "eastasiaforum.org",
                        "agsi.org", "fas.org", "usip.org", "cacianalyst.org") if d in duoi]
    if thua:
        return ("giục WebSearch chính nguồn vừa quét xong: " + " · ".join(thua))
    return None


PATH_RE_TEN_FILE = r"^/eng/report/20\d\d/\d\d/[^/]+\.html$"


def ca_ngay_lay_tu_ten_file(mod):
    """PHẢI CHẶN: tên file `20260728.html` là ngày THẬT, thắng con số in cạnh tiêu đề.

    Trang danh sách in `2026/07/20` cho cả mục, nên bỏ bước (1b) thì mọi bài của viện này nhận
    chung ngày 20/07 — vẫn nằm trong khung 7 ngày, vẫn ra danh sách, chỉ SAI ngày. Ca này vì thế
    phải đo GIÁ TRỊ ngày chứ không đo bài có mặt hay không.
    """
    slug, _st, _ = _quet(mod, trang=f"{GOC}/eng-column/", path_re=PATH_RE_TEN_FILE, kho=set())
    if "20260728.html" not in slug:
        return "bài có ngày trong tên file bị rơi khỏi danh sách"
    d = slug["20260728.html"][0]
    if d != datetime.date(2026, 7, 28):
        return f"ngày sai: {d} — phải là 2026-07-28 lấy từ tên file, không phải ngày in cạnh tiêu đề"
    return None


def ca_cat_duoi_ngay_trong_tieu_de(mod):
    """PHẢI CHẶN: tiêu đề không được mang đuôi `28.07.2026` — JIIA bọc cả khối bài trong <a>."""
    slug, _st, _ = _quet(mod, trang=f"{GOC}/eng-column/", path_re=PATH_RE_TEN_FILE, kho=set())
    t = slug.get("20260728.html", (None, ""))[1]
    if t.rstrip().endswith("28.07.2026"):
        return f"tiêu đề còn dính đuôi ngày: …{t[-40:]}"
    if "Taro Yamada" not in t:
        return "cắt quá tay — phần tên tác giả cũng bị nuốt mất"
    return None


def ca_khong_doc_chuoi_so_dai_thanh_ngay(mod):
    """ĐỐI CHỨNG hai chiều cho bước (1b): tên file KHÔNG phải ngày thì phải nhường lại bước (2).

    `asb44en-20260712345` có 11 chữ số liền — mã báo cáo, không phải ngày. Đọc bừa 8 số đầu ra
    12/07 là sai lặng; đúng thì bài này lấy 25/07 in cạnh tiêu đề. Và bài slug chữ phải lấy 26/07.
    """
    slug, _st, _ = _quet(mod, trang=f"{GOC}/eng-column/", path_re=PATH_RE_TEN_FILE, kho=set())
    if slug.get("asb44en-20260712345.html", (None,))[0] != datetime.date(2026, 7, 25):
        return (f"chuỗi số dài bị đọc thành ngày: "
                f"{slug.get('asb44en-20260712345.html', ('vắng mặt',))[0]} — phải là 2026-07-25")
    if slug.get("bao-cao-thuong-nien-cua-vien.html", (None,))[0] != datetime.date(2026, 7, 26):
        return "bài tên file bằng chữ không còn lấy được ngày cạnh tiêu đề"
    return None


def ca_moi_domain_deu_co_duong_quet(mod):
    """PHẢI CHẶN: domain trong guardrail mà không feed / không HTML / không cả WebSearch.

    Đây là hỏng câm ở tầng DANH SÁCH, không ở tầng mã: thêm domain vào `THINKTANK_DOMAINS` rồi
    quên khai đường vào thì không lớp nào quét, không lớp nào giục, và không dấu hiệu nào phát
    ra. Đo 20/08/2026 trước khi vá: 35 domain im lặng, trong đó có `cfr.org`.
    """
    thieu = sorted(mod.domain_chua_co_duong_quet())
    if thieu:
        return (f"{len(thieu)} domain trong THINKTANK_DOMAINS không có đường quét nào: "
                + " · ".join(thieu[:8]) + (" …" if len(thieu) > 8 else ""))
    return None


def ca_kiem_html_keu_khi_co_domain_mo_coi(mod):
    """PHẢI CHẶN: `--kiem-html` phải KÊU (mã 4) khi có domain mồ côi, không im lặng đi qua."""
    goc = dict(mod.WEBSEARCH_ONLY)
    mod.THINKTANK_DOMAINS = set(mod.THINKTANK_DOMAINS) | {"vien-mo-coi-gia.example.org"}
    try:
        buf = io.StringIO()
        ma = 0
        try:
            with contextlib.redirect_stdout(buf):
                mod.kiem_html()
        except SystemExit as ex:
            ma = ex.code
        ra = buf.getvalue()
        if "vien-mo-coi-gia.example.org" not in ra:
            return "--kiem-html KHÔNG nêu tên domain mồ côi"
        if ma not in (3, 4):
            return f"--kiem-html thoát mã {ma} — phải khác 0 để routine biết mà kêu"
        return None
    finally:
        mod.THINKTANK_DOMAINS = set(mod.THINKTANK_DOMAINS) - {"vien-mo-coi-gia.example.org"}
        mod.WEBSEARCH_ONLY = goc


def _path_re(mod, ten_vien: str) -> str:
    """Biểu thức path của MỘT viện, tra theo tên trong bảng thật.

    Bốn ca dưới đo chính DỮ LIỆU trong `THINKTANK_HTML` chứ không đo mã chung, nên chúng chạy
    thuần trên biểu thức — không chạm mạng, không cần trang giả. Đây là chỗ duy nhất bắt được
    lỗi kiểu "sửa một dòng bảng cho gọn": mã vẫn đúng, mọi trang khác vẫn ra bài, chỉ viện ấy
    lặng lẽ hụt một nhánh.
    """
    for ten, _url, rx, _kv in mod.THINKTANK_HTML:
        if ten == ten_vien:
            return rx
    raise AssertionError(f"không còn dòng nào tên '{ten_vien}' trong THINKTANK_HTML")


def ca_sipri_bat_ca_nhanh_viet_hoa(mod):
    """PHẢI KHỚP: SIPRI trộn `/commentary/essay/…` thường với `/commentary/Topical-backgrounder`
    HOA trong CÙNG một trang. Thiếu cờ `(?i)` thì mất đúng nhánh backgrounder mà không dấu hiệu
    nào — nhánh essay vẫn ra link nên `--kiem-html` vẫn báo OK."""
    rx = re.compile(_path_re(mod, "SIPRI"))
    thuong = "/commentary/essay/2026/united-states-deal-iran-could-put-freedom-navigation-risk"
    hoa = "/commentary/Topical-backgrounder/2026/how-maintain-multilateral-cooperation-export"
    if not rx.search(thuong):
        return "biểu thức SIPRI không khớp cả nhánh viết thường"
    if not rx.search(hoa):
        return "biểu thức SIPRI mất nhánh viết HOA `Topical-backgrounder` — thiếu cờ (?i)"
    return None


def ca_isw_khong_nuot_trang_chuyen_muc(mod):
    """ĐỐI CHỨNG chống nới: ISW đặt bài ở `/research/<vùng>/<slug>/`, còn `/research/<vùng>/`
    là trang chuyên mục. Nới biểu thức là mỗi lượt quét nạp thêm 3 trang chuyên mục làm "bài",
    và chúng có tiêu đề nghe hợp lý nên nhìn danh sách không phân biệt được."""
    rx = re.compile(_path_re(mod, "ISW"))
    bai = "/research/russia-ukraine/russian-offensive-campaign-assessment-august-19-2026/"
    if not rx.search(bai):
        return "biểu thức ISW không còn khớp bài thật"
    for muc in ("/research/russia-ukraine/", "/research/middle-east/", "/research/"):
        if rx.search(muc):
            return f"biểu thức ISW nuốt trang chuyên mục {muc}"
    return None


def ca_bai_o_goc_khong_nuot_dieu_huong(mod):
    """USSC và Egmont đặt bài THẲNG ở gốc tên miền nên biểu thức chỉ còn ĐỘ DÀI để chặn. Ca này
    canh cả hai chiều: bài thật phải qua, mà trang người và lối điều hướng phải rớt."""
    for ten, bai, rac in (
        ("USSC (Úc)", "/liberty-yards-us-maritime-revival-as-an-alliance-project",
         ("/dr-michael-green", "/publications", "/topics", "/experts")),
        ("Egmont", "/the-ankara-summit-its-trumps-nato-europe-just-lives-in-it/",
         ("/publications/", "/staff/", "/events", "/topics/")),
    ):
        rx = re.compile(_path_re(mod, ten))
        if not rx.search(bai):
            return f"{ten}: biểu thức không còn khớp bài thật {bai}"
        for r in rac:
            if rx.search(r):
                return f"{ten}: biểu thức nuốt lối điều hướng {r}"
    return None


def ca_timbuktu_khop_duong_dan_joomla(mod):
    """Timbuktu chạy Joomla: `/index.php/<chuyên mục>/item/<id>-<slug>`. Mảnh `item/<id>-` là
    thứ duy nhất tách bài khỏi trang chuyên mục, vì cả hai đều nằm dưới `/index.php/`."""
    rx = re.compile(_path_re(mod, "Timbuktu Institute"))
    bai = "/index.php/toutes-l-actualites/item/1701-cheikh-el-hadji-malick-sy-un-soufisme"
    if not rx.search(bai):
        return "biểu thức Timbuktu không còn khớp bài thật"
    for r in ("/index.php/publications", "/index.php/l-institut/preambule", "/index.php/timbuktu-tv"):
        if rx.search(r):
            return f"biểu thức Timbuktu nuốt trang chuyên mục {r}"
    return None


_FEED_MAU = (b'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
             b"<item><title>Bai nghien cuu ve an ninh vung Vinh</title>"
             b"<link>https://vien-gia.example.org/bai-mot/</link>"
             b"<pubDate>Thu, 20 Aug 2026 15:12:34 +0000</pubDate></item>"
             b"</channel></rss>")


def ca_feed_co_dong_trong_dau_file(mod):
    """PHẢI ĐỌC ĐƯỢC: một ký tự xuống dòng trước `<?xml` là đủ để ET từ chối CẢ feed.

    WordPress in thừa newline như vậy khá thường. Hỏng câm hạng nặng: `parse_feed` trả None ⇒
    0 item ⇒ nguồn hiện ở dòng "Feed không ra bài nào trong khung ngày", nhìn y hệt viện đăng
    thưa thật. Đo 21/08/2026 trên bảng 44 feed: Gulf International Forum nằm chết đúng kiểu này
    ngay lượt vừa cắm, feed thật có 113 KB và 10 item.
    """
    if len(mod.feed_items(_FEED_MAU)) != 1:
        return "feed sạch mà đã không đọc được — ca hỏng, sửa ca trước khi kết luận về mã"
    for rac, ten in ((b"\n", "dòng trống"), (b"  \n\t", "khoảng trắng"),
                     (b"\xef\xbb\xbf", "BOM UTF-8")):
        if len(mod.feed_items(rac + _FEED_MAU)) != 1:
            return f"feed mở đầu bằng {ten} bị đọc thành 0 item"
    return None


def ca_rac_dau_file_khong_phai_khoang_trang_van_bi_loai(mod):
    """ĐỐI CHỨNG chống nới: chỉ được cắt KHOẢNG TRẮNG và BOM.

    Rác đầu file mà không phải khoảng trắng thì đó là trang lỗi hoặc trang challenge dán trước
    XML; đọc nó thành feed là nạp rác vào kho — hướng lệch tệ hơn hẳn việc bỏ sót một nguồn.
    """
    for rac in (b"<!-- loi may chu -->", b"Attention Required! ", b"<html><body>403"):
        if mod.feed_items(rac + _FEED_MAU):
            return f"rác đầu file {rac[:20]!r} vẫn được đọc thành feed"
    return None


CA = [
    ("lấy được bài mới trong khung 7 ngày", ca_lay_duoc_bai_moi),
    ("feed mở đầu bằng dòng trống/BOM vẫn đọc được item", ca_feed_co_dong_trong_dau_file),
    ("rác đầu file KHÔNG phải khoảng trắng vẫn bị loại (đối chứng)",
     ca_rac_dau_file_khong_phai_khoang_trang_van_bi_loai),
    ("SIPRI: biểu thức bắt CẢ nhánh viết HOA", ca_sipri_bat_ca_nhanh_viet_hoa),
    ("ISW: KHÔNG nuốt trang chuyên mục (đối chứng)", ca_isw_khong_nuot_trang_chuyen_muc),
    ("bài đặt ở GỐC: khớp bài, không khớp điều hướng (USSC · Egmont)",
     ca_bai_o_goc_khong_nuot_dieu_huong),
    ("Timbuktu: khớp đúng đường dẫn Joomla /item/<id>-", ca_timbuktu_khop_duong_dan_joomla),
    ("mọi domain trong guardrail đều có đường quét", ca_moi_domain_deu_co_duong_quet),
    ("--kiem-html KÊU khi có domain mồ côi", ca_kiem_html_keu_khi_co_domain_mo_coi),
    ("ngày lấy từ TÊN FILE thắng ngày in cạnh tiêu đề", ca_ngay_lay_tu_ten_file),
    ("cắt đuôi ngày dd.mm.yyyy khỏi tiêu đề", ca_cat_duoi_ngay_trong_tieu_de),
    ("KHÔNG đọc chuỗi số dài trong tên file thành ngày (đối chứng)",
     ca_khong_doc_chuoi_so_dai_thanh_ngay),
    ("LOẠI bài ngoài khung ngày", ca_loai_bai_ngoai_khung),
    ("LOẠI link điều hướng /topics/", ca_loai_link_dieu_huong),
    ("LOẠI đường dẫn rác /events/", ca_loai_duong_dan_rac),
    ("LOẠI link sang tên miền khác", ca_loai_ten_mien_khac),
    ("LOẠI bài đã có trong kho", ca_loai_bai_da_co),
    ("GIỮ bài có chữ 'podcast' trong tiêu đề (đối chứng)", ca_giu_bai_co_chu_podcast_trong_tieu_de),
    ("mở trang bài đọc meta khi danh sách không in ngày", ca_mo_bai_lay_ngay_that),
    ("quy đổi múi giờ về giờ VN", ca_quy_doi_mui_gio),
    ("dọn đuôi máy móc trong tiêu đề", ca_don_duoi_tieu_de),
    ("trần HTML_LINK_CAP chặn trang lưu trữ", ca_tran_so_link),
    ("trang bị chặn không ra link rác", ca_trang_bi_chan_khong_ra_link),
    ("biểu thức path CHẾT thì --kiem-html PHẢI KÊU", ca_path_chet_thi_phai_keu),
    ("trang sống thì --kiem-html KHÔNG kêu oan (đối chứng)", ca_trang_song_thi_khong_keu_oan),
    ("mọi domain quét về đều qua được guardrail nạp", ca_domain_phai_qua_duoc_guardrail),
    ("không giục WebSearch nguồn đã quét tự động", ca_khong_giuc_websearch_nguon_da_quet),
]


def chay(mod=None, im=False) -> int:
    mod = mod or nap_module()
    hong = 0
    for ten, fn in CA:
        try:
            ly_do = fn(mod)
        except Exception as ex:  # noqa: BLE001 — ca ném ngoại lệ cũng là ca ĐỎ
            ly_do = f"ngoại lệ: {type(ex).__name__}: {ex}"
        if ly_do:
            hong += 1
        if not im:
            print(f"{'✅' if not ly_do else '❌'} {ten}" + (f"\n     → {ly_do}" if ly_do else ""))
    if not im:
        print()
        print(f"{'TẤT CẢ ĐẠT' if not hong else f'{hong}/{len(CA)} CA ĐỎ'} ({len(CA)} ca)")
    return hong


# --------------------------------------------------------------- tự kiểm
# Mỗi bản hỏng gỡ đúng MỘT lớp bảo vệ và khai ca nào PHẢI đỏ theo. Khai thừa ca là tự bịt mắt
# mình: `--tu-kiem` sẽ báo trượt vì lý do sai (bài học 29/07 ở QuanSu).
BAN_HONG = [
    ("bỏ lọc NOISE_PATHS",
     lambda s: s.replace("        if any(p in link.lower() for p in NOISE_PATHS):\n"
                         "            continue\n", "", 1),
     "LOẠI đường dẫn rác /events/"),
    ("bỏ kiểm tên miền",
     lambda s: s.replace('if pr.scheme not in ("http", "https") or pr.netloc.replace("www.", "") != host:',
                         'if pr.scheme not in ("http", "https"):', 1),
     "LOẠI link sang tên miền khác"),
    ("bỏ lọc khung ngày",
     lambda s: s.replace("        if d > today_vn or (today_vn - d).days > MAX_AGE_DAYS:",
                         "        if False:", 1),
     "LOẠI bài ngoài khung ngày"),
    ("bỏ lọc bài đã có trong kho",
     lambda s: s.replace("        if link in existing or link.split(\"?\")[0] in existing:",
                         "        if False:", 1),
     "LOẠI bài đã có trong kho"),
    ("bỏ bước mở trang bài đọc meta",
     lambda s: s.replace("        if d is None:\n            d = ngay_mo.get(link)\n", "", 1),
     "mở trang bài đọc meta khi danh sách không in ngày"),
    # ⚠️ Neo phải kèm dòng phía trên: chuỗi `return d.astimezone(VN)…` có ở CẢ `parse_feed_date`
    # lẫn `parse_html_date`, thay nhầm cái đầu thì bản hỏng không đụng tới lớp đang đo và ca
    # vẫn xanh — đúng cái bẫy "chuỗi neo hết duy nhất" của luật tự kiểm.
    ("bỏ quy đổi múi giờ về giờ VN (trong parse_html_date)",
     lambda s: s.replace('        d = datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))\n'
                         "        return d.astimezone(VN).date() if d.tzinfo else d.date()",
                         '        d = datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))\n'
                         "        return d.date()", 1),
     "quy đổi múi giờ về giờ VN"),
    ("bỏ trần HTML_LINK_CAP",
     lambda s: s.replace("        if len(out) >= HTML_LINK_CAP:\n            break\n", "", 1),
     "trần HTML_LINK_CAP chặn trang lưu trữ"),
    ("bỏ dọn đuôi máy móc trong tiêu đề",
     lambda s: s.replace('        title = re.sub(r"\\s*\\d\\d\\.\\d\\d\\.\\d\\d\\s*\\|.*$", "", title)\n',
                         "", 1),
     "dọn đuôi máy móc trong tiêu đề"),
    ("--kiem-html thấy trang chết mà không kêu",
     lambda s: s.replace('              + " · ".join(chet))\n        raise SystemExit(3)',
                         '              + " · ".join(chet))'),
     "biểu thức path CHẾT thì --kiem-html PHẢI KÊU"),
    # Bản hỏng gỡ nhánh HTML chứ không gỡ nhánh FEEDS, vì hiện KHÔNG domain nào nằm đồng thời
    # ở THINKTANK_FEEDS và WEBSEARCH_ONLY (usip.org + cacianalyst.org đã rời WEBSEARCH_ONLY khi
    # tìm ra feed của chúng). Nhánh FEEDS vì thế chưa có ca đỏ nào canh — nó là lớp chắn cho
    # LẦN SAU tìm được feed của một domain còn trong bảng, khai thẳng ra đây thay vì để một ca
    # xanh giả tạo làm người đọc tưởng cả hai nhánh đều được đo.
    ("bỏ trừ nguồn đã quét HTML khỏi danh sách WebSearch",
     lambda s: s.replace('    da_phu = {urllib.parse.urlparse(u).netloc.replace("www.", "") '
                         'for _, u, _, _ in THINKTANK_HTML}\n', "    da_phu = set()\n", 1),
     "không giục WebSearch nguồn đã quét tự động"),
    ("bỏ bước (1b) đọc ngày từ tên file",
     lambda s: s.replace("        if d is None:                             # (1b) ngày YYYYMMDD "
                         "nằm trong TÊN FILE\n            d = ngay_trong_ten_file(pr.path)\n", "", 1),
     "ngày lấy từ TÊN FILE thắng ngày in cạnh tiêu đề"),
    ("nới bước (1b) — đọc bừa 8 số đầu, không cần ranh giới",
     lambda s: s.replace('_TEN_FILE_NGAY = re.compile(r"(?:^|[^0-9])(20\\d\\d)(\\d\\d)(\\d\\d)(?:[^0-9]|$)")',
                         '_TEN_FILE_NGAY = re.compile(r"(20\\d\\d)(\\d\\d)(\\d\\d)")', 1),
     "KHÔNG đọc chuỗi số dài trong tên file thành ngày (đối chứng)"),
    ("bỏ cắt khoảng trắng đầu file trong parse_feed",
     lambda s: s.replace('    xml_bytes = xml_bytes.lstrip(b"\\xef\\xbb\\xbf").lstrip()\n', "", 1),
     "feed mở đầu bằng dòng trống/BOM vẫn đọc được item"),
    ("nới phép cắt đầu file — cắt tới dấu `<` đầu tiên",
     lambda s: s.replace('    xml_bytes = xml_bytes.lstrip(b"\\xef\\xbb\\xbf").lstrip()',
                         '    k = xml_bytes.find(b"<?xml")\n'
                         '    xml_bytes = xml_bytes[k:] if k > 0 else xml_bytes', 1),
     "rác đầu file KHÔNG phải khoảng trắng vẫn bị loại (đối chứng)"),
    # ── 04 bản hỏng cho các viện cắm 21/08/2026. Chúng thay DÒNG BẢNG chứ không thay mã chung:
    # lỗi loại này không làm hỏng lớp quét, chỉ làm một viện hụt nhánh — nên phải có ca riêng.
    ("bỏ cờ (?i) khỏi biểu thức SIPRI",
     lambda s: s.replace(r'r"(?i)^/commentary/[a-z-]+/20\d\d/[^/]{10,}"',
                         r'r"^/commentary/[a-z-]+/20\d\d/[^/]{10,}"', 1),
     "SIPRI: biểu thức bắt CẢ nhánh viết HOA"),
    ("nới biểu thức ISW cho khớp cả trang chuyên mục",
     lambda s: s.replace(r'r"^/research/[a-z-]+/[^/]{15,}/?$"', r'r"^/research/[a-z-]+/[^/]*"', 1),
     "ISW: KHÔNG nuốt trang chuyên mục (đối chứng)"),
    ("hạ ngưỡng độ dài slug gốc của USSC 30 -> 10",
     lambda s: s.replace('    ("USSC (Úc)", "https://www.ussc.edu.au/publications",\n'
                         '     r"^/[a-z0-9-]{30,}/?$", "Úc · quan hệ Mỹ-Úc"),',
                         '    ("USSC (Úc)", "https://www.ussc.edu.au/publications",\n'
                         '     r"^/[a-z0-9-]{10,}/?$", "Úc · quan hệ Mỹ-Úc"),', 1),
     "bài đặt ở GỐC: khớp bài, không khớp điều hướng (USSC · Egmont)"),
    ("bỏ mảnh item/<id>- khỏi biểu thức Timbuktu",
     lambda s: s.replace(r'r"^/index\.php/[^/]+/item/\d+-[^/]{10,}"',
                         r'r"^/index\.php/[^/]{10,}"', 1),
     "Timbuktu: khớp đúng đường dẫn Joomla /item/<id>-"),
    ("bỏ cắt đuôi ngày dd.mm.yyyy khỏi tiêu đề",
     lambda s: s.replace('        title = re.sub(r"\\s*\\d{1,2}[./]\\d{1,2}[./]20\\d\\d\\s*$", "", '
                         'title).strip(" |·–—")\n', "", 1),
     "cắt đuôi ngày dd.mm.yyyy khỏi tiêu đề"),
    # ⚠️ Bản hỏng này neo vào một DÒNG DỮ LIỆU của `WEBSEARCH_ONLY`, nên mỗi lần bảng đổi là
    # phải sửa neo trong CÙNG lượt — `--tu-kiem` báo "KHÔNG áp được phép thay" chứ không im,
    # nhưng lượt chạy thường vẫn xanh nên chỉ `--tu-kiem` mới tố. Đã vỡ một lần 21/08/2026 khi
    # `gulfif.org` rời bảng để lên `THINKTANK_FEEDS`.
    ("bỏ khai đường quét cho một domain (mô phỏng quên khai)",
     lambda s: s.replace('    "Vùng Vịnh": ["epc.ae"],\n', "", 1),
     "mọi domain trong guardrail đều có đường quét"),
    ("--kiem-html thấy domain mồ côi mà không kêu",
     lambda s: s.replace("    mo_coi = sorted(domain_chua_co_duong_quet())",
                         "    mo_coi = []", 1),
     "--kiem-html KÊU khi có domain mồ côi"),
    ("bỏ chốt trang quá ngắn (403/challenge)",
     lambda s: s.replace("    if len(body) < 2000:", "    if False:", 1),
     "trang bị chặn không ra link rác"),
]


def tu_kiem() -> int:
    print("=== Chạy trên bản THẬT (mọi ca phải xanh) ===")
    if chay():
        print("\n✗ Bản thật đã đỏ — sửa xong hãy tự kiểm.")
        return 1
    goc = SCRIPT.read_text(encoding="utf-8")
    hong = 0
    print("\n=== Chạy trên các bản HỎNG (ca đã khai phải ĐỎ) ===")
    for stt, (ten, lam_hong, ca_phai_do) in enumerate(BAN_HONG, 1):
        moi = lam_hong(goc)
        if moi == goc:
            print(f"❌ {ten}: KHÔNG áp được phép thay — chuỗi neo không còn khớp mã nguồn")
            hong += 1
            continue
        # Bản hỏng phải nằm TRONG thư mục thật: add_analyses.py import analyses_store cạnh nó.
        # Tên mang PID để hai phiên cùng tự kiểm không xoá bản hỏng của nhau (luật 30/07/2026),
        # và mang SỐ THỨ TỰ để hai bản hỏng trong CÙNG một lượt không trùng đường dẫn — trùng
        # thì dính bẫy __pycache__ nói ở đầu file.
        tam = SCRIPT.parent / f"_thu-hong-{os.getpid()}-{stt:02d}-add_analyses.py"
        try:
            tam.write_text(moi, encoding="utf-8")
            try:
                mod = nap_module(tam)
            except SyntaxError as ex:
                print(f"❌ {ten}: phép thay làm HỎNG CÚ PHÁP ({ex}) — sửa lại phép thay")
                hong += 1
                continue
            do_ca = {}
            for t, f in CA:
                try:
                    do_ca[t] = f(mod) is not None
                except Exception:  # noqa: BLE001
                    do_ca[t] = True
            if all(do_ca.values()):
                # Bản hỏng làm đỏ TOÀN BỘ ca thì nó chỉ chứng minh Python biết báo lỗi, không
                # chứng minh ca nào có răng (luật 30/07/2026, ViecBot).
                print(f"❌ {ten}: làm ĐỎ TOÀN BỘ {len(CA)} ca — phép thay phá nền, sửa lại")
                hong += 1
                continue
            do = do_ca[ca_phai_do]
            print(f"{'✅' if do else '❌'} {ten}\n     → ca '{ca_phai_do}' "
                  f"{'ĐỎ đúng như khai' if do else 'VẪN XANH — ca đó vô dụng'}")
            hong += 0 if do else 1
        finally:
            tam.unlink(missing_ok=True)
    print()
    print("TỰ KIỂM ĐẠT — bộ ca này thật sự bắt được lỗi" if not hong
          else f"✗ {hong} bản hỏng KHÔNG bị bắt")
    return 1 if hong else 0


if __name__ == "__main__":
    raise SystemExit(tu_kiem() if "--tu-kiem" in sys.argv else (1 if chay() else 0))
