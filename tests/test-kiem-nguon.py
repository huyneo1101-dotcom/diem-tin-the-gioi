#!/usr/bin/env python3
"""Bộ test canh lớp lấy nguồn của harvest.py + phép đo kiem_nguon.py.

    python3 tests/test-kiem-nguon.py            # chạy 25 ca
    python3 tests/test-kiem-nguon.py --tu-kiem  # chứng minh test BẮT ĐƯỢC lỗi

Cập nhật 30/07/2026 khi cắm thang `congcu/lay_trang.py` vào `harvest.curl()`: nhóm A-E
(ca 1-20) đo bậc 2 CŨ (`GiaLap` ép `_LAY_TRANG = False`, dùng khi máy KHÔNG có
`~/Claude/congcu`); nhóm F (ca 21-25, `GiaLapThang`) đo nhánh THẬT máy Huy đi hằng ngày.

VÌ SAO PHẢI CÓ (luật mục 17 CLAUDE.md toàn cục): cổng này thuộc loại "hỏng thì im lặng".
Nguồn bị chặn không kêu — nó chỉ không đóng góp ứng viên, y hệt feed sống mà hôm nay
không có bài hợp chủ đề. Chạy trăm lần "thấy nó không kêu" không chứng minh được gì.

TẤT ĐỊNH, KHÔNG GỌI MẠNG: mọi ca thay `subprocess.run` bằng thân giả. Ca dựng bằng cách
gọi ra Internet thì có lần may mắn qua được và `--tu-kiem` báo trượt OAN (luật "ca canh
phải tất định — đo ARGV, đừng đo cuộc đua").
"""
import argparse
import contextlib
import importlib.util
import io
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

# ── Thân trả về THẬT, chép từ đo ngày 30/07/2026 ───────────────────────────────
# Naval Technology: 403 nhưng thân MỞ ĐẦU BẰNG `<?xml` và dài 19.357 byte -> parse ra
# 0 item mà KHÔNG ném lỗi. Đây là ca hiểm nhất, giữ nguyên hình dạng thật.
THAN_403_XML = (b'<?xml version="1.0" encoding="utf-8"?><!DOCTYPE html PUBLIC '
                b'"-//W3C//DTD XHTML 1.0 Strict//EN"><html><head><title>403 Forbidden</title>'
                b'</head><body><h1>Error 403 Forbidden</h1><p>Forbidden</p><h3>Error 54113</h3>'
                b'</body></html>' + b"<!-- padding -->" * 1200)
# armed-services.senate.gov + army.mil (Akamai)
THAN_ACCESS_DENIED = (b"<HTML><HEAD><TITLE>Access Denied</TITLE></HEAD><BODY><H1>Access Denied</H1>"
                      b" You don't have permission to access this server.<P>Reference #18.48532217")
# breakingdefense.com (nginx)
THAN_403_NGINX = (b"<html><head><title>403 Forbidden</title></head><body><center><h1>403 Forbidden"
                  b"</h1></center><hr><center>nginx</center></body></html>"
                  + b"<!-- a padding to disable MSIE and Chrome friendly error page -->" * 60)
# census.gov (Cloudflare)
THAN_CLOUDFLARE = (b"<!DOCTYPE html><html><head><title>Attention Required! | Cloudflare</title>"
                   b"</head><body>Sorry, you have been blocked</body></html>" + b" " * 5000)

FEED_THAT = (b'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
             b"<title>Breaking Defense</title>"
             + b"<item><title>Tin quoc phong</title><link>https://x/1</link>"
               b"<pubDate>Wed, 29 Jul 2026 10:00:00 GMT</pubDate></item>" * 30
             + b"</channel></rss>")
TRANG_HTML_THAT = (b"<!DOCTYPE html><html><body>"
                   + b'<a href="/news/press-releases/abc">Chairman Rogers Applauds House Passage'
                     b' of FY27 NDAA</a>' * 400 + b"</body></html>")


def nap(ten_module, duong_dan):
    spec = importlib.util.spec_from_file_location(ten_module, duong_dan)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[ten_module] = mod
    spec.loader.exec_module(mod)
    return mod


HARVEST_PATH = pathlib.Path(os.environ.get("HARVEST_MOD", SCRIPTS / "harvest.py"))
KIEMNGUON_PATH = pathlib.Path(os.environ.get("KIEMNGUON_MOD", SCRIPTS / "kiem_nguon.py"))


class GiaLap:
    """Thay subprocess.run của harvest + đường vân tay TLS bằng thân giả.

    ⚠️ Ép `hv._LAY_TRANG = False` (máy KHÔNG có `~/Claude/congcu`) — mọi ca trong nhóm
    này được dựng TRƯỚC khi cắm thang 30/07/2026 và đo đúng bậc 2 cũ
    (`_lay_bang_van_tay_chrome`). Máy thật của Huy CÓ `congcu`; không ép thì `curl()` đi
    qua `lt.lay()` thật (không mock được ở đây) và toàn bộ GiaLap thành vô dụng dù bảng
    vẫn xanh. Nhóm THANG bên dưới dùng `GiaLapThang` để đo đúng nhánh máy Huy đi hằng ngày.
    """

    def __init__(self, hv, than_curl, than_cffi=None, co_cffi=True):
        self.hv, self.than_curl, self.than_cffi, self.co_cffi = hv, than_curl, than_cffi, co_cffi
        self.so_lan_cffi = 0

    def __enter__(self):
        self._run_cu = self.hv.subprocess.run
        self._cffi_cu = self.hv._lay_bang_van_tay_chrome
        self._CFFI_cu = self.hv._CFFI
        self._lt_cu = self.hv._LAY_TRANG
        self.hv._LAY_TRANG = False
        self.hv.VET_NGUON = {"cffi_va_duoc": [], "chan_ca_hai": [], "cffi_vang_mat": set(),
                              "thang_cuu": {}}

        class KQ:
            pass

        def run_gia(cmd, **kw):
            k = KQ()
            k.stdout, k.stderr, k.returncode = self.than_curl, b"", 0
            return k

        def cffi_gia(url, timeout):
            self.so_lan_cffi += 1
            if not self.co_cffi:
                self.hv._CFFI = False
                return b""
            return self.than_cffi or b""

        self.hv.subprocess.run = run_gia
        self.hv._lay_bang_van_tay_chrome = cffi_gia
        self.hv._CFFI = None if self.co_cffi else None
        return self

    def __exit__(self, *a):
        self.hv.subprocess.run = self._run_cu
        self.hv._lay_bang_van_tay_chrome = self._cffi_cu
        self.hv._CFFI = self._CFFI_cu
        self.hv._LAY_TRANG = self._lt_cu


class GiaLapThang:
    """Tráo `_LAY_TRANG` bằng module GIẢ có `.lay(url)` — canh nhánh CÓ thang của `curl()`.

    `ham_lay(url)` trả dict như `lay_trang.lay()` thật (`duong`/`raw`/`ma`/`byte`/`vi_sao`).
    `than_curl` là thân bậc 1 (raw curl qua subprocess), thường cố tình chặn để rơi xuống thang.
    """

    def __init__(self, hv, than_curl, ham_lay):
        self.hv, self.than_curl, self.ham_lay = hv, than_curl, ham_lay
        self.goi = []

    def __enter__(self):
        self._run_cu = self.hv.subprocess.run
        self._lt_cu = self.hv._LAY_TRANG
        self._cffi_cu = self.hv._lay_bang_van_tay_chrome
        self._CFFI_cu = self.hv._CFFI
        self.hv._CFFI = None
        self.hv.VET_NGUON = {"cffi_va_duoc": [], "chan_ca_hai": [], "cffi_vang_mat": set(),
                              "thang_cuu": {}}

        class KQ:
            pass

        def run_gia(cmd, **kw):
            k = KQ()
            k.stdout, k.stderr, k.returncode = self.than_curl, b"", 0
            return k

        def cffi_khong_duoc_goi(url, timeout):
            # KHÔNG ra mạng: nếu bản hỏng lỡ rơi về nhánh bậc-2-cũ, thân RỖNG bị `_nghi_bi_chan`
            # tính là chặn nên luôn rơi vào chan_ca_hai — tất định, không phụ thuộc mạng thật.
            return b""

        class _ThangGia:
            def lay(_self, url, **kw):
                self.goi.append(url)
                return self.ham_lay(url)

        self.hv.subprocess.run = run_gia
        self.hv._lay_bang_van_tay_chrome = cffi_khong_duoc_goi
        self.hv._LAY_TRANG = _ThangGia()
        return self

    def __exit__(self, *a):
        self.hv.subprocess.run = self._run_cu
        self.hv._lay_bang_van_tay_chrome = self._cffi_cu
        self.hv._CFFI = self._CFFI_cu
        self.hv._LAY_TRANG = self._lt_cu


def chay_cac_ca():
    hv = nap("harvest", HARVEST_PATH)
    kn = nap("kiem_nguon", KIEMNGUON_PATH)
    kn.harvest = hv
    ca = []

    def ghi(so, ten, dat, chi_tiet=""):
        ca.append((so, ten, dat, chi_tiet))

    # ── Nhóm A: bộ dò dấu hiệu chặn — 4 ca PHẢI CHẶN + 2 chống chặn oan ──────────
    ghi(1, "PHẢI CHẶN: thân 403 mở đầu bằng <?xml (Naval Technology)",
        hv._nghi_bi_chan(THAN_403_XML) is True)
    ghi(2, "PHẢI CHẶN: thân Access Denied (senate.gov · army.mil)",
        hv._nghi_bi_chan(THAN_ACCESS_DENIED) is True)
    ghi(3, "PHẢI CHẶN: thân 403 nginx (Breaking Defense)",
        hv._nghi_bi_chan(THAN_403_NGINX) is True)
    ghi(4, "PHẢI CHẶN: thân Cloudflare Attention Required (census.gov)",
        hv._nghi_bi_chan(THAN_CLOUDFLARE) is True)
    ghi(5, "PHẢI CHẶN: thân rỗng", hv._nghi_bi_chan(b"") is True)
    ghi(6, "chống chặn oan: feed RSS thật không bị coi là bị chặn",
        hv._nghi_bi_chan(FEED_THAT) is False)
    ghi(7, "chống chặn oan: trang HTML thật không bị coi là bị chặn",
        hv._nghi_bi_chan(TRANG_HTML_THAT) is False)

    # ── Nhóm B: curl() có thật sự thử lại bằng vân tay TLS không ─────────────────
    with GiaLap(hv, THAN_403_NGINX, FEED_THAT) as g:
        body = hv.curl("https://breakingdefense.com/full-rss-feed/")
        ghi(8, "curl bị 403 thì PHẢI thử lại bằng vân tay TLS và lấy được feed",
            body == FEED_THAT and g.so_lan_cffi == 1
            and hv.VET_NGUON["cffi_va_duoc"] == ["https://breakingdefense.com/full-rss-feed/"],
            f"so_lan_cffi={g.so_lan_cffi} vet={hv.VET_NGUON['cffi_va_duoc']}")

    with GiaLap(hv, FEED_THAT, b"KHONG DUOC GOI") as g:
        body = hv.curl("https://ok/feed")
        ghi(9, "chống gọi thừa: curl thành công thì KHÔNG đụng tới vân tay TLS",
            body == FEED_THAT and g.so_lan_cffi == 0, f"so_lan_cffi={g.so_lan_cffi}")

    with GiaLap(hv, THAN_403_NGINX, THAN_403_NGINX):
        hv.curl("https://chan-ca-hai/feed")
        ghi(10, "PHẢI KÊU: chặn cả hai đường thì vào sổ chan_ca_hai",
            hv.VET_NGUON["chan_ca_hai"] == ["https://chan-ca-hai/feed"],
            str(hv.VET_NGUON["chan_ca_hai"]))

    with GiaLap(hv, THAN_403_NGINX, None, co_cffi=False):
        hv.curl("https://thieu-thu-vien/feed")
        ghi(11, "PHẢI KÊU: máy thiếu curl_cffi thì ghi sổ (fail-open CÓ TIẾNG)",
            hv.VET_NGUON["cffi_vang_mat"] == {"https://thieu-thu-vien/feed"},
            str(hv.VET_NGUON["cffi_vang_mat"]))

    # ── Nhóm C: phép đo kiem_nguon.py ───────────────────────────────────────────
    with GiaLap(hv, THAN_403_XML, THAN_403_XML):
        r = kn.do_mot("Naval Technology", "https://naval-technology.com/feed/", "RSS")
        ghi(12, "PHẢI CHẶN: feed 403-dạng-XML bị chấm HỎNG, không phải 'sống mà hết bài'",
            r["dat"] is False and "chặn" in r["ly_do"], str(r))

    with GiaLap(hv, THAN_403_XML, THAN_403_XML):
        r = kn.do_mot("UB Thượng viện", "https://x.senate.gov/press", "HTML")
        ghi(13, "PHẢI CHẶN: trang HTML 403 dài 19KB vẫn bị chấm HỎNG (cỡ không cứu nổi)",
            r["dat"] is False, str(r))

    with GiaLap(hv, FEED_THAT, None):
        r = kn.do_mot("Breaking Defense", "https://ok/feed", "RSS")
        ghi(14, "chống chấm oan: feed thật 30 item phải ĐẠT", r["dat"] is True and r["item"] == 30,
            str(r))

    with GiaLap(hv, TRANG_HTML_THAT, None):
        r = kn.do_mot("UB Hạ viện", "https://ok/press", "HTML")
        ghi(15, "chống chấm oan: trang HTML thật phải ĐẠT", r["dat"] is True, str(r))

    # ── Nhóm D: mã thoát — phép đo có KÊU RA NGOÀI được không ────────────────────
    with GiaLap(hv, THAN_403_NGINX, THAN_403_NGINX):
        kn_nguon_cu = kn.TRONG_YEU
        kn.TRONG_YEU = [("Feed hỏng", "https://hong/feed", "RSS", True)]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ma = kn.main([])
        kn.TRONG_YEU = kn_nguon_cu
        ghi(16, "PHẢI KÊU: có nguồn hỏng thì mã thoát = 1 và in ⛔",
            ma == 1 and "⛔" in buf.getvalue(), f"ma={ma}")

    with GiaLap(hv, FEED_THAT, None):
        kn_nguon_cu = kn.TRONG_YEU
        kn.TRONG_YEU = [("Feed ổn", "https://ok/feed", "RSS", False)]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ma = kn.main([])
        kn.TRONG_YEU = kn_nguon_cu
        ghi(17, "chống kêu oan: mọi nguồn đạt thì mã thoát = 0", ma == 0, f"ma={ma}")

    # Nguồn đã biết chỉ CI lấy được -> VÀNG, KHÔNG được làm mã thoát thành 1
    with GiaLap(hv, THAN_403_NGINX, THAN_403_NGINX):
        kn_nguon_cu = kn.TRONG_YEU
        kn.TRONG_YEU = [("The Diplomat", "https://thediplomat.com/feed/", "RSS", True)]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ma = kn.main([])
        kn.TRONG_YEU = kn_nguon_cu
        ghi(18, "chống kêu oan: nguồn đã biết chỉ-CI-lấy-được ra VÀNG, mã thoát vẫn 0",
            ma == 0 and "🟡" in buf.getvalue(), f"ma={ma}")

    # ── Nhóm E: harvest báo feed rỗng ───────────────────────────────────────────
    hv.VET_NGUON = {"cffi_va_duoc": [], "chan_ca_hai": [], "cffi_vang_mat": set(),
                    "feed_rong": [("The Diplomat", "https://thediplomat.com/feed/")]}
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        hv.bao_nguon_hong()
    ghi(19, "PHẢI KÊU: harvest in cảnh báo khi có feed trả 0 item",
        "0 ITEM" in buf.getvalue().upper() and "Diplomat" in buf.getvalue(),
        buf.getvalue()[:120])

    hv.VET_NGUON = {"cffi_va_duoc": [], "chan_ca_hai": [], "cffi_vang_mat": set()}
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        hv.bao_nguon_hong()
    ghi(20, "chống kêu oan: mọi nguồn ổn thì harvest báo ✅", "✅" in buf.getvalue(),
        buf.getvalue()[:120])

    # ── Nhóm F: THANG lấy trang bị chặn (congcu/lay_trang.py), cắm 30/07/2026 ───────
    # Máy Huy CÓ ~/Claude/congcu, nên đây là nhánh curl() thật sự đi qua hằng ngày —
    # nhóm A-E ở trên chỉ đo bậc 2 CŨ (fail-open khi máy KHÁC không có congcu).
    def kq_thang(duong, ma=200, byte=1000, vi_sao=""):
        return {"duong": duong, "raw": FEED_THAT if duong else b"", "ma": ma, "byte": byte,
                "vi_sao": vi_sao}

    with GiaLapThang(hv, THAN_403_NGINX, lambda u: kq_thang("wayback")) as g:
        body = hv.curl("https://x/feed")
        ghi(21, "PHẢI CỨU: bậc 1 chặn, thang cứu bằng bậc `wayback` (không phải curl_cffi)",
            body == FEED_THAT and hv.VET_NGUON["thang_cuu"].get("wayback") == ["https://x/feed"],
            f"body={body[:60]} vet={hv.VET_NGUON}")

    with GiaLapThang(hv, FEED_THAT, lambda u: kq_thang("", vi_sao="KHONG duoc goi")) as g:
        body = hv.curl("https://ok/feed")
        ghi(22, "chống gọi thừa: bậc 1 sạch thì KHÔNG đụng tới thang",
            body == FEED_THAT and g.goi == [], f"goi={g.goi}")

    with GiaLapThang(hv, THAN_403_NGINX, lambda u: kq_thang("", vi_sao="waf")) as g:
        hv.curl("https://chan-het/feed")
        ghi(23, "PHẢI KÊU: thang trượt hết mọi bậc thì vào chan_ca_hai",
            hv.VET_NGUON["chan_ca_hai"] == ["https://chan-het/feed"], str(hv.VET_NGUON))

    with GiaLapThang(hv, THAN_403_NGINX,
                      lambda u: kq_thang("", vi_sao="THIẾU curl_cffi — mọi trang mất")) as g:
        hv.curl("https://x/feed2")
        ghi(24, "PHẢI KÊU: thang báo thiếu curl_cffi thì ghi cffi_vang_mat, KHÔNG chan_ca_hai",
            hv.VET_NGUON["cffi_vang_mat"] == {"https://x/feed2"}
            and hv.VET_NGUON["chan_ca_hai"] == [], str(hv.VET_NGUON))

    with GiaLapThang(hv, THAN_403_NGINX, lambda u: kq_thang("curl_cffi")) as g:
        hv.curl("https://x/feed3")
        ghi(25, "PHẢI GHI ĐÚNG SỔ: thang cứu bằng CHÍNH curl_cffi thì vào cffi_va_duoc, "
                "không vào thang_cuu",
            hv.VET_NGUON["cffi_va_duoc"] == ["https://x/feed3"] and hv.VET_NGUON["thang_cuu"] == {},
            str(hv.VET_NGUON))

    return ca


# ── Bản hỏng cho --tu-kiem ─────────────────────────────────────────────────────
# Mỗi mục: (tên, file gốc, phép thay, các ca PHẢI ĐỎ)
BAN_HONG = [
    # ⚠️ KHÔNG khai ca 16 vào đây dù trực giác bảo nên: ca 16 chấm một feed RSS, mà nhánh
    # RSS còn LỚP THỨ HAI che (đếm <item> — thân 403 parse ra -1 nên vẫn hỏng). Khai thừa
    # thì --tu-kiem báo trượt vì lý do sai, che mất bản hỏng thật sự không bắt được.
    ("gỡ bộ dò dấu hiệu chặn (luôn coi là không bị chặn)", "harvest.py",
     ("    dau = body[:3000].lower()\n    return any(d in dau for d in DAU_HIEU_CHAN)",
      "    dau = body[:3000].lower()\n    return False"),
     [1, 2, 3, 4, 8, 10, 11, 12, 13]),
    ("curl KHÔNG thử lại bằng vân tay TLS", "harvest.py",
     ("    body2 = _lay_bang_van_tay_chrome(url, timeout)",
      "    body2 = b''"),
     [8]),
    # ⚠️ Phải gỡ CẢ HAI nhánh ghi sổ, không phải một. Sổ được ghi ở hai chỗ chồng nhau
    # (biết trước là thiếu thư viện · vừa phát hiện thiếu ngay trong lượt này); gỡ một chỗ
    # thì chỗ kia gánh, ca vẫn XANH và mình tưởng ca đó vô dụng. Đã vấp thật khi dựng bộ
    # này 30/07 — cùng lỗi với luật "bảo vệ nhiều lớp" ở mục 17 CLAUDE.md toàn cục.
    # ⚠️ 30/07/2026: nhánh này lồng thêm một cấp bên trong `if lt is False:` khi cắm thang
    # (mục 17 CLAUDE.md toàn cục — thêm cổng mới thì soi lại chuỗi neo, dễ hết duy nhất).
    ("quên ghi sổ khi máy thiếu curl_cffi (fail-open CÂM) — gỡ CẢ HAI nhánh", "harvest.py",
     ('        if _CFFI is False:\n            VET_NGUON["cffi_vang_mat"].add(url)\n'
      "            return body\n"
      "        body2 = _lay_bang_van_tay_chrome(url, timeout)\n"
      "        if _CFFI is False:      # vừa phát hiện thiếu thư viện ngay trong lượt này\n"
      '            VET_NGUON["cffi_vang_mat"].add(url)\n            return body',
      "        if _CFFI is False:\n            return body\n"
      "        body2 = _lay_bang_van_tay_chrome(url, timeout)\n"
      "        if _CFFI is False:\n            return body"),
     [11]),
    ("harvest im lặng khi feed trả 0 item", "harvest.py",
     ('        print(f"\\n⛔ {len(rong)} FEED RSS TRẢ 0 ITEM',
      '        print(f"\\n   {len(rong)} khong sao dau'),
     [19]),
    ("phép đo chấm mọi thân là ĐẠT", "kiem_nguon.py",
     ("        dat = item > 0", "        dat = True"),
     [12, 16]),
    ("phép đo bỏ dò dấu hiệu ở nhánh HTML, chỉ xét cỡ", "kiem_nguon.py",
     ("        dat = bool(body) and not harvest._nghi_bi_chan(body) and len(body) > 8000",
      "        dat = bool(body) and len(body) > 8000"),
     [13]),
    ("main luôn trả mã 0 (nuốt tiếng kêu)", "kiem_nguon.py",
     ("    return 1 if do_ else 0", "    return 0"),
     [16]),
    ("gỡ nhánh CÓ thang, luôn lùi về bậc 2 cũ dù máy có congcu", "harvest.py",
     ("    lt = _lay_trang_module()\n    if lt is False:",
      "    lt = _lay_trang_module()\n    if True:"),
     [21, 24, 25]),
    ("gỡ phân biệt curl_cffi/thang_cuu (mọi bậc thang đều ghi thang_cuu)", "harvest.py",
     ('        if kq["duong"] == "curl_cffi":\n            VET_NGUON["cffi_va_duoc"].append(url)\n'
      '        else:\n            VET_NGUON["thang_cuu"].setdefault(kq["duong"], []).append(url)',
      '        VET_NGUON["thang_cuu"].setdefault(kq["duong"], []).append(url)'),
     [25]),
    ("gỡ nhánh khai thiếu curl_cffi ở thang (mọi lượt trượt đều vào chan_ca_hai)", "harvest.py",
     ('    if "curl_cffi" in (kq.get("vi_sao") or ""):   # thư viện vắng mặt ở MỌI bậc của thang\n'
      '        VET_NGUON["cffi_vang_mat"].add(url)\n        return body\n',
      ""),
     [24]),
]


def tu_kiem():
    print("=== TỰ KIỂM: dựng bản hỏng, các ca đã khai PHẢI ĐỎ ===\n")
    tong_dat = 0
    for ten, file_goc, (cu, moi), ca_phai_do in BAN_HONG:
        goc = SCRIPTS / file_goc
        src = goc.read_text(encoding="utf-8")
        if src.count(cu) != 1:
            print(f"⛔ {ten}: KHÔNG áp được phép thay: {src.count(cu)} chỗ khớp")
            continue
        # Bản hỏng phải nằm TRONG thư mục thật (harvest import `topics`), và tên mang PID
        # để hai phiên chạy --tu-kiem cùng lúc không xoá bản hỏng của nhau (luật mục 17).
        ban = SCRIPTS / f"_thu-hong-{os.getpid()}-{file_goc}"
        try:
            ban.write_text(src.replace(cu, moi), encoding="utf-8")
            env = dict(os.environ)
            env["HARVEST_MOD" if file_goc == "harvest.py" else "KIEMNGUON_MOD"] = str(ban)
            p = subprocess.run([sys.executable, str(pathlib.Path(__file__).resolve())],
                               capture_output=True, env=env, timeout=300)
            out = p.stdout.decode("utf-8", "replace")
            do_thuc = {int(m) for m in re.findall(r"^\s*✗ \[(\d+)\]", out, re.M)}
            thieu = set(ca_phai_do) - do_thuc
            if len(do_thuc) == len(re.findall(r"^\s*[✓✗] \[", out, re.M)):
                print(f"⛔ {ten}: TRƯỢT — bản hỏng làm ĐỎ TOÀN BỘ ca, tức phép thay phá hỏng "
                      f"cú pháp chứ không gỡ đúng một lớp vá. Sửa lại phép thay.")
            elif thieu:
                print(f"⛔ {ten}: TRƯỢT — ca {sorted(thieu)} VẪN XANH (đỏ thực: {sorted(do_thuc)})")
            else:
                print(f"✅ {ten}: bắt được (ca đỏ: {sorted(do_thuc)})")
                tong_dat += 1
        finally:
            ban.unlink(missing_ok=True)
    print(f"\n=== {tong_dat}/{len(BAN_HONG)} bản hỏng bị bắt ===")
    return 0 if tong_dat == len(BAN_HONG) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tu-kiem", action="store_true")
    args = ap.parse_args()
    if args.tu_kiem:
        return tu_kiem()
    ca = chay_cac_ca()
    for so, ten, dat, chi_tiet in ca:
        print(f"  {'✓' if dat else '✗'} [{so}] {ten}")
        if not dat and chi_tiet:
            print(f"        {chi_tiet[:200]}")
    rot = [c for c in ca if not c[2]]
    print(f"\n=== {len(ca)-len(rot)}/{len(ca)} ca đạt ===")
    return 1 if rot else 0


if __name__ == "__main__":
    sys.exit(main())
