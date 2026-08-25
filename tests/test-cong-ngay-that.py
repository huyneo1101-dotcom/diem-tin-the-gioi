#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TEST CỔNG NGÀY ĐĂNG THẬT — mở bài ra đo ngày, không tin `date` agent khai (25/08/2026).

Chạy:
    python3 tests/test-cong-ngay-that.py
    python3 tests/test-cong-ngay-that.py --tu-kiem   # chứng minh test BẮT ĐƯỢC lỗi

⚠ VÌ SAO PHẢI CÓ CA "PHẢI CHẶN". Cổng này im lặng tuyệt đối khi lô sạch — mà cổng chết cũng
im y hệt. Chính lớp cổng cũ (`check_date_window`) là ví dụ sống: nó chạy mọi phiên, không
bao giờ kêu, và vẫn để lọt 09 bài ngoài khung trong 334 bài đo ngày 25/08/2026 — nặng nhất
là bài South China Morning Post đăng 21/12/2024 khai `date` 29/07/2026.

⚠ CA CHỐNG CHẶN OAN cũng bắt buộc. Đo thật: 28/181 bài (15%) không có metadata ngày đọc
được. Một cổng chặn nhóm đó là cổng giết 15% bản tin mỗi phiên, và cổng nào cũng phải mở cờ
mới qua được thì nó dạy người dùng phản xạ mở cờ.

⚠ HAI TẦNG ĐO, giữ cả hai:
  - Ca 1-10 gọi thẳng `ngay_that.kiem_lo()` — đo LUẬT.
  - Ca 11-13 chạy `add_news.py` thật trên BẢN SAO repo — đo DÂY NỐI. Luật đúng mà không ai
    gọi thì bằng không; bản hỏng chỉ gỡ lời gọi sẽ lọt sạch ca 1-10.
Mạng KHÔNG được tham gia: HTML đi qua seam `NGAYTHAT_KHO_GIA` (file JSON {url: html}). Bộ
test phụ thuộc internet là bộ test đỏ ngẫu nhiên, và đỏ ngẫu nhiên thì người ta thôi đọc.
"""
import datetime
import hashlib
import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent

# Seam để tự kiểm: trỏ sang một BẢN SAO repo khác (xem --tu-kiem).
REPO_THU = pathlib.Path(os.environ.get("NGAYTHAT_REPO") or REPO)

HOM_NAY = datetime.date.today()
REF = HOM_NAY


def _nap(ten: str, path: pathlib.Path):
    """Tên module DUY NHẤT theo đường dẫn — hai bản khác nhau cùng tên thì bản sau đè bản
    trước trong sys.modules và ca sẽ đo nhầm bản."""
    dau = hashlib.sha1(str(path).encode()).hexdigest()[:8]
    ten_that = f"{ten}_{dau}"
    spec = importlib.util.spec_from_file_location(ten_that, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[ten_that] = mod
    spec.loader.exec_module(mod)
    return mod


def mod():
    return _nap("ngay_that", REPO_THU / "scripts" / "ngay_that.py")


def _tran(cat=""):
    return 3 if cat == "Công nghệ quân sự" else 1


def _html(ngay_iso, kieu="jsonld"):
    if kieu == "jsonld":
        return '<script type="application/ld+json">{"datePublished":"%sT08:00:00Z"}</script>' % ngay_iso
    if kieu == "meta":
        return '<meta property="article:published_time" content="%sT08:00:00+00:00">' % ngay_iso
    if kieu == "time":
        return '<time datetime="%s">hôm nọ</time>' % ngay_iso
    if kieu == "citation":
        d = datetime.date.fromisoformat(ngay_iso)
        return '<meta name="citation_publication_date" content="Tue, %d/%d/%d - 12:00" />' % (
            d.month, d.day, d.year)
    raise ValueError(kieu)


def _do(url_html, items):
    """(loi, canh_bao) với kho HTML giả tiêm thẳng vào kiem_lo."""
    m = mod()
    return m.kiem_lo(items, REF, _tran, tai=lambda u: url_html.get(u, ""))


def _it(ngay_khai, url="https://vd.test/a", cat="Chính trị", ctx="usNews[0]"):
    return {"ctx": ctx, "url": url, "date": ngay_khai, "category": cat}


def _ngay(lui):
    return (HOM_NAY - datetime.timedelta(days=lui)).isoformat()


# ---------------------------------------------------------------------------
# Ca 1-10 — đo LUẬT
# ---------------------------------------------------------------------------

def ca_01():
    """PHẢI CHẶN — bài đăng 19 ngày trước nhưng lô khai ngày hôm nay.

    Đúng ca thật đã lọt: điều trần Thượng viện đăng 05/08/2026, nạp 24/08 với `date` 24/08.
    """
    loi, _ = _do({"https://vd.test/a": _html(_ngay(19))}, [_it(_ngay(0))])
    assert loi, "cổng KHÔNG chặn bài đăng trước 19 ngày"
    assert "đăng THẬT" in loi[0], loi[0]


def ca_02():
    """PHẢI CHẶN — bài cũ 585 ngày (ca South China Morning Post 21/12/2024)."""
    loi, _ = _do({"https://vd.test/a": _html("2024-12-21")}, [_it(_ngay(0))])
    assert loi, "cổng KHÔNG chặn bài cũ 585 ngày"


def ca_03():
    """PHẢI CHẶN — bài cũ 2 ngày ở chủ đề thường (trần 1 ngày)."""
    loi, _ = _do({"https://vd.test/a": _html(_ngay(2))}, [_it(_ngay(0))])
    assert loi, "cổng KHÔNG chặn bài 2 ngày tuổi ở chủ đề trần 1 ngày"


def ca_04():
    """PHẢI CHẶN — Công nghệ quân sự cũ 4 ngày (trần nới 3 ngày, vẫn quá)."""
    loi, _ = _do({"https://vd.test/a": _html(_ngay(4))},
                 [_it(_ngay(0), cat="Công nghệ quân sự")])
    assert loi, "cổng KHÔNG chặn tin CNQS cũ 4 ngày"


def ca_05():
    """CHO QUA — Công nghệ quân sự cũ 3 ngày, đúng phần nới riêng của chủ đề này.

    Đối chứng cho ca 4: thiếu nó thì một cổng chặn mọi thứ quá 1 ngày vẫn "đạt" ca 4.
    """
    loi, _ = _do({"https://vd.test/a": _html(_ngay(3))},
                 [_it(_ngay(3), cat="Công nghệ quân sự")])
    assert not loi, f"chặn oan tin CNQS 3 ngày tuổi: {loi}"


def ca_06():
    """CHO QUA — bài hôm qua, khai đúng ngày hôm qua."""
    loi, _ = _do({"https://vd.test/a": _html(_ngay(1))}, [_it(_ngay(1))])
    assert not loi, f"chặn oan tin hôm qua: {loi}"


def ca_07():
    """PHẢI CHẶN — trang mở được nhưng KHÔNG in ngày ở đâu cả.

    Chỉ thị Huy 25/08/2026: "trang không ghi ngày thì bỏ đi". Không in ngày thì không có
    cách nào biết bài cũ hay mới. Trang phải có <title> mới tính là "mở được".
    """
    loi, _ = _do({"https://vd.test/a": "<html><title>Bài không ghi ngày</title>"
                                       "<body>nội dung</body></html>"}, [_it(_ngay(0))])
    assert loi, "cổng CHO QUA bài ở trang không in ngày"
    assert "KHÔNG in ngày" in loi[0], loi[0]


def ca_08():
    """CHO QUA + KÊU — trang KHÔNG MỞ ĐƯỢC (tải về rỗng) vẫn nạp được, có cảnh báo.

    Ranh giới với ca 07, và là ranh giới bắt buộc: chặn theo mạng nghĩa là để đường truyền
    của máy chạy quyết định bản tin có tin hay không, và nguồn nào trả 403 thì mất trắng.
    """
    loi, cb = _do({}, [_it(_ngay(0))])
    assert not loi, f"chặn oan khi không tải được trang: {loi}"
    assert cb, "không tải được trang mà cổng im lặng hoàn toàn"


def ca_09():
    """Đọc được cả 04 dạng metadata — thiếu dạng nào là nguồn dùng dạng đó lọt câm."""
    m = mod()
    for kieu in ("jsonld", "meta", "time", "citation"):
        ngay, cach = m.doc_ngay(_html("2026-08-05", kieu))
        assert ngay == "2026-08-05", f"dạng {kieu} đọc ra {ngay!r} ({cach})"


def ca_10():
    """KHÔNG bắt ngày trôi nổi trong văn bản tự do.

    Bẫy đã vấp thật ở QuetThinkTank 29/07/2026: bài mở đầu bằng cuộc đổ bộ Normandy bị gán
    ngày 06/06/1944, loại nhầm 46 bài. Bài quân sự nào cũng dày đặc ngày lịch sử.
    """
    m = mod()
    ngay, _ = m.doc_ngay("<p>Ngày 6 June 1944, quân Đồng minh đổ bộ Normandy. "
                         "Published September 2, 1945.</p>")
    assert ngay is None, f"bắt ngày trôi nổi trong thân bài: {ngay}"


# ---------------------------------------------------------------------------
# Ca 11-13 — đo DÂY NỐI (chạy add_news.py thật)
# ---------------------------------------------------------------------------

def _ban_sao_repo() -> pathlib.Path:
    d = pathlib.Path(tempfile.mkdtemp(prefix=f"ngaythat-e2e-{os.getpid()}-"))
    (d / "scripts").mkdir()
    for f in (REPO_THU / "scripts").glob("*.py"):
        shutil.copy2(f, d / "scripts" / f.name)
    shutil.copytree(REPO / "data", d / "data")
    shutil.copy2(REPO / "index.html", d / "index.html")
    for ten in ("baomoi-saved.json", "baomoi-topics.json"):
        if (REPO / ten).exists():
            shutil.copy2(REPO / ten, d / ten)
    return d


def _tin_that(ngay_khai, url, cat="Chính trị"):
    return {"date": ngay_khai, "category": cat, "title": "Tin thử cổng ngày thật " + url[-6:],
            "summary": "Nội dung thử nghiệm dài vừa đủ để qua các cổng hình thức của add_news.",
            "sourceName": "Reuters", "sourceUrl": url,
            "significance": "Ý nghĩa thử nghiệm cho bộ ca kiểm cổng ngày đăng thật."}


def _chay_add_news(lo: dict, kho_html: dict, them_co=()) -> tuple:
    d = _ban_sao_repo()
    try:
        f = d / "lo.json"
        f.write_text(json.dumps(lo, ensure_ascii=False), encoding="utf-8")
        kho = d / "kho.json"
        kho.write_text(json.dumps(kho_html, ensure_ascii=False), encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(d / "scripts" / "add_news.py"), str(f), *them_co],
            capture_output=True, text=True,
            env=dict(os.environ, NGAYTHAT_KHO_GIA=str(kho)))
        return r.returncode, (r.stdout + r.stderr)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def ca_11():
    """PHẢI CHẶN (đầu-cuối): `add_news.py` từ chối lô có bài đăng ngoài khung.

    Ca DUY NHẤT chứng minh cổng ĐƯỢC GỌI. Bản hỏng gỡ lời gọi khỏi `add_news.py` vẫn qua
    sạch ca 1-10 vì luật trong `ngay_that.py` còn nguyên.
    """
    url = "https://vd.test/cu"
    rc, out = _chay_add_news(
        {"date": HOM_NAY.isoformat(), "usNews": [_tin_that(HOM_NAY.isoformat(), url)]},
        {url: _html(_ngay(19))})
    assert rc != 0, f"add_news.py NẠP bài đăng 19 ngày trước (rc={rc})\n{out[-1500:]}"
    assert "NGÀY ĐĂNG THẬT" in out, f"chặn nhưng không phải vì cổng ngày thật:\n{out[-1500:]}"


def ca_12():
    """CHO QUA (đầu-cuối): cùng lô đó, bài đăng hôm nay thì nạp được.

    Đối chứng bắt buộc: thiếu nó thì ca 11 đỏ vì bất kỳ lý do gì cũng trông như "đã chặn".
    """
    url = "https://vd.test/moi"
    rc, out = _chay_add_news(
        {"date": HOM_NAY.isoformat(), "usNews": [_tin_that(HOM_NAY.isoformat(), url)]},
        {url: _html(_ngay(0))})
    assert rc == 0, f"chặn oan bài đăng hôm nay (rc={rc})\n{out[-2000:]}"


def ca_13():
    """Cờ `--bo-cong-ngay-that` phải KÈM LÝ DO, và lý do phải được in ra.

    Cờ mở cổng không để lại dấu vết thì tương đương không có cổng.
    """
    url = "https://vd.test/cu2"
    lo = {"date": HOM_NAY.isoformat(), "usNews": [_tin_that(HOM_NAY.isoformat(), url)]}
    kho = {url: _html(_ngay(19))}
    rc, out = _chay_add_news(lo, kho, ("--bo-cong-ngay-that",))
    assert rc != 0 and "phải kèm LÝ DO" in out, f"cờ trần không lý do vẫn đi qua:\n{out[-800:]}"
    rc2, out2 = _chay_add_news(lo, kho, ('--bo-cong-ngay-that=metadata nguồn ghi sai',))
    assert rc2 == 0, f"cờ có lý do vẫn bị chặn (rc={rc2})\n{out2[-1200:]}"
    assert "metadata nguồn ghi sai" in out2, f"mở cổng mà không in lý do:\n{out2[-800:]}"


def ca_14():
    """CHO QUA + KÊU — bản tải về không có thẻ <title> thì tính là KHÔNG MỞ ĐƯỢC.

    Đo 25/08/2026: CNN và CNBC trả về 300 KB không có nổi <title> (trang dựng bằng
    JavaScript hoặc bị chặn), trong khi DVIDS/PACOM/war.gov có <title> đúng tên bài. Thiếu
    lằn ranh này thì mọi trang bị chặn đều bị xử như "trang không in ngày" và bị loại oan.
    """
    loi, cb = _do({"https://vd.test/a": "<html><body>" + "x" * 5000 + "</body></html>"},
                  [_it(_ngay(0))])
    assert not loi, f"xử trang nghi bị chặn như trang không in ngày: {loi}"
    assert cb and "nghi bị chặn" in cb[0], f"không nêu lý do nghi bị chặn: {cb}"


def ca_15():
    """Đọc được ngày trong bảng DVIDS (`Date Posted: 08.22.2026`), KHÔNG lấy `Date Taken`.

    DVIDS là nguồn thông cáo quân sự dùng nhiều nhất cho chủ đề Công nghệ quân sự và không
    có JSON-LD/og/time — thiếu mẫu này là cả nguồn bị loại sạch từ 25/08/2026. `Date Taken`
    là ngày chụp ảnh, có thể trước ngày đăng hàng tuần, lấy nhầm là chặn oan.
    """
    m = mod()
    html = ("<html><title>DVIDS</title><table>"
            "<tr><td>Date Taken:</td><td>08.01.2026</td></tr>"
            "<tr><td>Date Posted:</td><td>08.22.2026 07:35</td></tr></table></html>")
    ngay, cach = m.doc_ngay(html)
    assert ngay == "2026-08-22", f"đọc ra {ngay!r} ({cach}) thay vì ngày Date Posted"


CAC_CA = [
    (1, "PHẢI CHẶN — bài cũ 19 ngày khai ngày hôm nay", ca_01),
    (2, "PHẢI CHẶN — bài cũ 585 ngày (ca SCMP 2024)", ca_02),
    (3, "PHẢI CHẶN — bài cũ 2 ngày ở chủ đề trần 1 ngày", ca_03),
    (4, "PHẢI CHẶN — CNQS cũ 4 ngày (quá trần nới 3)", ca_04),
    (5, "cho qua — CNQS cũ 3 ngày, đúng phần nới riêng", ca_05),
    (6, "cho qua — bài hôm qua khai đúng hôm qua", ca_06),
    (7, "PHẢI CHẶN — trang mở được nhưng không in ngày", ca_07),
    (8, "cho qua + KÊU — trang không mở được (tải về rỗng)", ca_08),
    (9, "đọc được cả 04 dạng metadata ngày", ca_09),
    (10, "KHÔNG bắt ngày trôi nổi trong thân bài", ca_10),
    (11, "PHẢI CHẶN (đầu-cuối) — add_news.py gọi cổng thật", ca_11),
    (12, "cho qua (đầu-cuối) — bài đăng hôm nay nạp được", ca_12),
    (13, "cờ mở cổng phải kèm lý do và in lý do ra", ca_13),
    (14, "cho qua + KÊU — bản tải về không có <title> (nghi bị chặn)", ca_14),
    (15, "đọc ngày trong bảng DVIDS, không lấy Date Taken", ca_15),
]


def chay() -> list:
    do = []
    for so, nhan, fn in CAC_CA:
        try:
            fn()
            print(f"  ✓ [{so:02d}] {nhan}")
        except Exception as e:                                  # noqa: BLE001
            print(f"  ✗ [{so:02d}] {nhan}\n        │ {e}")
            do.append(so)
    return do


# ---------------------------------------------------------------------------
# --tu-kiem
# ---------------------------------------------------------------------------

TEN_FILE = {
    "ngay_that": ("scripts", "ngay_that.py"),
    "add_news": ("scripts", "add_news.py"),
}

BAN_HONG = [
    ("add_news: gỡ lời gọi cổng (luật còn nguyên, không ai gọi)",
     "add_news",
     ("    if can_do and not bo_cong_ngay_that:",
      "    if False:"),
     [11]),

    ("add_news: cờ mở cổng nhận lý do RỖNG (mở cổng không để lại dấu)",
     "add_news",
     ("    if co_co_ngay and not bo_cong_ngay_that:",
      "    if False:"),
     [13]),

    ("ngay_that: bỏ so trần, chỉ chặn bài ở tương lai (cổng ngừng phát hiện bài cũ)",
     "ngay_that",
     ("        if that < gioi_han:",
      "        if False:"),
     [1, 2, 3, 4, 11]),

    ("ngay_that: cho qua bài ở trang không in ngày (cổng ngừng bắt cả nhóm)",
     "ngay_that",
     ("            if cach.startswith('không lấy được'):",
      "            if True:"),
     [7]),

    ("ngay_that: xử trang KHÔNG MỞ ĐƯỢC như trang không in ngày (loại oan theo mạng)",
     "ngay_that",
     ("            if cach.startswith('không lấy được'):",
      "            if False:"),
     [8, 14]),

    ("ngay_that: bỏ mẫu bảng DVIDS (mất sạch một nguồn thông cáo quân sự)",
     "ngay_that",
     ("    m = re.search(r'Date\\s+Posted:\\s*</td>\\s*<td>\\s*(\\d{2})\\.(\\d{2})\\.(\\d{4})', h, re.I)",
      "    m = None"),
     [15]),

    ("ngay_that: bỏ lằn ranh <title> (trang bị chặn bị xử như trang không in ngày)",
     "ngay_that",
     ("    if not re.search(r'<title[^>]*>\\s*\\S', h, re.I):",
      "    if False:"),
     [14]),

    ("ngay_that: áp trần 1 ngày cho mọi chủ đề (chặn oan Công nghệ quân sự)",
     "ngay_that",
     ("        tran = tran_theo_cat(it.get('category', ''))",
      "        tran = 1"),
     [5]),

    ("ngay_that: bắt cả ngày trôi nổi trong thân bài (gán bài 2026 thành 1944)",
     "ngay_that",
     ("    return None, 'không có metadata ngày'",
      "    m = re.search(r'([A-Z][a-z]+)\\s+(\\d{1,2}),\\s*(\\d{4})', h)\n"
      "    if m and m.group(1) in THANG:\n"
      "        return '%04d-%02d-%02d' % (int(m.group(3)), THANG[m.group(1)], int(m.group(2))), 'ngày trôi nổi'\n"
      "    return None, 'không có metadata ngày'"),
     [10]),
]


def _dung_ban_sao(d: pathlib.Path, file_hong: str, tim: str, thay: str) -> None:
    (d / "scripts").mkdir(parents=True, exist_ok=True)
    for f in (REPO / "scripts").glob("*.py"):
        shutil.copy2(f, d / "scripts" / f.name)
    shutil.copytree(REPO / "data", d / "data")
    thu_muc, ten_file = TEN_FILE[file_hong]
    p = d / thu_muc / ten_file
    p.write_text(p.read_text(encoding="utf-8").replace(tim, thay, 1), encoding="utf-8")


def tu_kiem() -> int:
    print("Chạy bộ ca trên BẢN ĐÚNG trước — ca đỏ ở đây thì dựng bản hỏng cũng vô nghĩa.")
    r = subprocess.run([sys.executable, str(pathlib.Path(__file__).resolve())],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout)
        print("✗ TRƯỢT: bộ ca đã ĐỎ trên bản đúng. Sửa cho xanh rồi mới tự kiểm.")
        return 1
    print(f"  bản đúng: {len(CAC_CA)}/{len(CAC_CA)} ca đạt\n")

    hong = 0
    for nhan, file_hong, (tim, thay), ca_phai_do in BAN_HONG:
        thu_muc, ten_file = TEN_FILE[file_hong]
        goc = (REPO / thu_muc / ten_file).read_text(encoding="utf-8")
        if goc.count(tim) != 1:
            print(f"  ✗ {nhan}\n        │ KHÔNG áp được phép thay: {goc.count(tim)} chỗ khớp "
                  f"(cần đúng 1). Mã nguồn đã đổi → sửa lại neo, đừng sửa ca.")
            hong += 1
            continue
        dau = hashlib.sha1((tim + thay).encode()).hexdigest()[:8]
        d = pathlib.Path(tempfile.mkdtemp(prefix=f"ngaythat-{os.getpid()}-{dau}-"))
        try:
            _dung_ban_sao(d, file_hong, tim, thay)
            env = dict(os.environ, NGAYTHAT_REPO=str(d))
            r = subprocess.run([sys.executable, str(pathlib.Path(__file__).resolve())],
                               capture_output=True, text=True, env=env)
            do_that = set()
            for dong in r.stdout.splitlines():
                if dong.strip().startswith("✗ ["):
                    do_that.add(int(dong.split("[")[1].split("]")[0]))
            if len(do_that) == len(CAC_CA):
                print(f"  ✗ {nhan}\n        │ MỌI ca đều đỏ → phép thay làm hỏng cú pháp.")
                hong += 1
                continue
            thieu = set(ca_phai_do) - do_that
            thua = do_that - set(ca_phai_do)
            if thieu:
                print(f"  ✗ {nhan}\n        │ ca {sorted(thieu)} VẪN XANH trên bản hỏng "
                      f"→ ca đó không bắt được lỗi. Đỏ thực tế: {sorted(do_that)}")
                hong += 1
            elif thua:
                print(f"  ✗ {nhan}\n        │ đỏ THÊM ca {sorted(thua)} ngoài khai báo "
                      f"→ khai lại cho đúng, kẻo che mất bản hỏng thật")
                hong += 1
            else:
                print(f"  ✓ {nhan} → đỏ đúng ca {sorted(do_that)}")
        finally:
            shutil.rmtree(d, ignore_errors=True)

    print()
    if hong:
        print(f"✗ TRƯỢT: {hong}/{len(BAN_HONG)} bản hỏng KHÔNG bị bắt.")
        return 1
    print(f"✅ {len(BAN_HONG)}/{len(BAN_HONG)} bản hỏng đều bị bắt.")
    return 0


def main() -> int:
    if "--tu-kiem" in sys.argv:
        return tu_kiem()
    print(f"CỔNG NGÀY ĐĂNG THẬT — {len(CAC_CA)} ca (repo đo: {REPO_THU})")
    do = chay()
    print()
    if do:
        print(f"✗ {len(do)}/{len(CAC_CA)} ca HỎNG: {do}")
        return 1
    print(f"✅ {len(CAC_CA)}/{len(CAC_CA)} ca đạt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
