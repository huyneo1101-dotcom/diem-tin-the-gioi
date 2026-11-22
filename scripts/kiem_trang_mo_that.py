#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CỔNG: MỞ TRANG BẰNG TRÌNH DUYỆT THẬT TRƯỚC KHI ĐƯA LÊN MẠNG — dựng 22/11/2026.

VÌ SAO CÓ FILE NÀY
──────────────────
`kiem_trang_chay.py` chỉ DỊCH mã (không chạy), nên bắt được kiểu hỏng 07/10/2026 (cắt nhầm 670
dòng, trang trắng 46 ngày) nhưng KHÔNG bắt được lỗi chỉ lộ khi trang CHẠY. Đo được ngay lượt vá:
ghép lại mã xong, trang vẫn trắng vì từ 27/10 lượt quét sự kiện ghi ô `dates` dạng
`{start,end}` và `(ev.dates||'').replace` ném TypeError lúc vẽ — cú pháp hoàn toàn lành.
Cổng này phục vụ thư mục trang qua http cục bộ, mở bằng trình duyệt thật, rồi đòi:
  (1) không có lỗi JS nào thoát ra (`pageerror`);
  (2) trang hiện ít nhất `CHU_TOI_THIEU` ký tự chữ và có tên trang.
Cắm ở `pages.yml` SAU bước cắt bản nhẹ (đo đúng thứ người đọc tải về): hỏng thì dừng dựng,
GitHub Pages giữ bản đang chạy, `canary.kiem_web()` kêu lệch ở lượt sau.

    python3 scripts/kiem_trang_mo_that.py [thư mục trang]   # 0 đạt · 1 hỏng · 2 không đo được
    python3 scripts/kiem_trang_mo_that.py --tu-kiem

⚠ FAIL-CLOSED: thiếu playwright hay không mở được trình duyệt thì trả 2, KHÔNG trả 0.
Trên máy GitHub dùng Chrome cài sẵn (`channel="chrome"`), không tải trình duyệt; trên Mac lùi
về Chromium đi kèm playwright.
"""
import functools
import http.server
import pathlib
import socketserver
import sys
import tempfile
import threading

ROOT = pathlib.Path(__file__).resolve().parent.parent
# Bản tin thật hiện ~5.100 ký tự chữ ngay khi mở (đo 22/11/2026, khung 390×844); trang trắng
# do lỗi JS hiện 0-1 ký tự. Ngưỡng đặt xa cả hai đầu.
CHU_TOI_THIEU = 800
TEN_TRANG = "Điểm Tin Thế Giới"


class _Im(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def _phuc_vu(thu_muc):
    h = functools.partial(_Im, directory=str(thu_muc))
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("127.0.0.1", 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def mo_trang(thu_muc, cho_ms=2500):
    """(chữ, list lỗi JS) — hoặc None khi không đo được (thiếu playwright/trình duyệt)."""
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None
    srv = _phuc_vu(thu_muc)
    try:
        with sync_playwright() as pw:
            b = None
            for kw in ({"channel": "chrome"}, {}):
                try:
                    b = pw.chromium.launch(**kw)
                    break
                except Exception:
                    continue
            if b is None:
                return None
            try:
                p = b.new_page(viewport={"width": 390, "height": 844})
                loi = []
                p.on("pageerror", lambda e: loi.append(str(e)[:200]))
                p.goto("http://127.0.0.1:%d/index.html" % srv.server_address[1],
                       wait_until="networkidle", timeout=90000)
                p.wait_for_timeout(cho_ms)
                chu = p.evaluate("() => document.body ? document.body.innerText : ''")
                return chu, loi
            finally:
                b.close()
    except Exception:
        return None
    finally:
        srv.shutdown()
        srv.server_close()


def phan_xet(kq):
    """(mã, list lý do). 0 đạt · 1 hỏng · 2 không đo được."""
    if kq is None:
        return 2, ["KHÔNG ĐO ĐƯỢC: thiếu playwright hoặc không mở được trình duyệt"]
    chu, loi = kq
    ly_do = ["lỗi JS khi chạy: " + x for x in loi]
    if len(chu.strip()) < CHU_TOI_THIEU:
        ly_do.append("trang chỉ hiện %d ký tự chữ (sàn %d) — trang trắng" % (len(chu.strip()), CHU_TOI_THIEU))
    if TEN_TRANG not in chu:
        ly_do.append("không thấy tên trang «%s»" % TEN_TRANG)
    return (1 if ly_do else 0), ly_do


def main(argv):
    d = pathlib.Path(argv[0]) if argv else ROOT
    if not (d / "index.html").exists():
        print("🟡 không thấy %s/index.html" % d)
        return 2
    ma, ly_do = phan_xet(mo_trang(d))
    if ma == 0:
        print("🟢 mở trang thật: không lỗi JS, trang hiện chữ bình thường")
    else:
        print(("🔴 TRANG HỎNG KHI CHẠY" if ma == 1 else "🟡 CHƯA ĐO ĐƯỢC") + " — %s:" % d)
        for x in ly_do:
            print("   " + x)
    return ma


# ── tự kiểm ────────────────────────────────────────────────────────────────────────────────
_DAY = "<p>" + ("Bản tin thử nghiệm có đủ chữ để vượt sàn. " * 40) + "</p>"
TRANG_THU = {
    "lanh": "<html><head><meta charset=\"utf-8\"></head><body><h1>%s</h1><div id=r></div><script>document.getElementById('r').innerHTML=%r;</script></body></html>",
    # Hình lỗi 22/11: cú pháp lành, ném TypeError lúc vẽ ⇒ không chữ nào hiện.
    "loi_chay": "<html><head><meta charset=\"utf-8\"></head><body><div id=r></div><script>var ev={dates:{start:'2026-11-19'}};"
                "var s=(ev.dates||'').replace(/-/g,'');document.getElementById('r').innerHTML=%r+%r;</script></body></html>",
    # Vẽ xong rồi mới ném lỗi (một mục hỏng giữa trang): đủ chữ, chỉ phép bắt lỗi JS thấy.
    "loi_sau_ve": "<html><head><meta charset=\"utf-8\"></head><body><h1>%s</h1><div id=r></div><script>document.getElementById('r').innerHTML=%r;"
                  "null.x;</script></body></html>",
    # Trắng mà không lỗi nào thoát ra (ví dụ vẽ vào nhầm chỗ, dữ liệu rỗng).
    "trang_trang": "<html><head><meta charset=\"utf-8\"></head><body><div id=r></div><script>var x=1;</script></body></html>",
}


def _dung(ten):
    d = pathlib.Path(tempfile.mkdtemp(prefix="dt-mo-that-"))
    if ten == "lanh":
        html = TRANG_THU["lanh"] % (TEN_TRANG, _DAY)
    elif ten in ("loi_chay", "loi_sau_ve"):
        html = TRANG_THU[ten] % (TEN_TRANG, _DAY)
    else:
        html = TRANG_THU[ten]
    (d / "index.html").write_text(html, encoding="utf-8")
    return d


def tu_kiem():
    ca = []

    def c(t, dk):
        ca.append((t, bool(dk)))

    kq_lanh = mo_trang(_dung("lanh"), 300)
    c("00 · máy mở được trình duyệt (thiếu thì mọi ca dưới vô nghĩa)", kq_lanh is not None)
    c("01 · ĐỐI CHỨNG: trang lành → 0", phan_xet(kq_lanh)[0] == 0)
    m, l = phan_xet(mo_trang(_dung("loi_chay"), 300))
    c("02 · PHẢI CHẶN: cú pháp lành nhưng ném lỗi lúc chạy (hình lỗi ô ngày 22/11) → 1",
      m == 1 and any("lỗi JS" in x for x in l))
    m, l = phan_xet(mo_trang(_dung("trang_trang"), 300))
    c("03 · PHẢI CHẶN: trang trắng không lỗi → 1", m == 1 and any("trang trắng" in x for x in l))
    m, l = phan_xet(mo_trang(_dung("loi_sau_ve"), 300))
    c("03b · PHẢI CHẶN: trang vẽ đủ chữ rồi mới ném lỗi → 1, chỉ vì lỗi JS",
      m == 1 and l and all("lỗi JS" in x for x in l))
    c("04 · PHẢI KÊU: không đo được → 2, không trả 0", phan_xet(None)[0] == 2)
    c("05 · PHẢI CHẶN: đủ chữ nhưng thiếu tên trang → 1",
      phan_xet(("x" * 2000, []))[0] == 1)
    c("06 · sàn chữ ghim cứng 800 (ca neo theo hằng số là ca mất răng)", CHU_TOI_THIEU == 800)
    for t, d in ca:
        print(("  ✅ " if d else "  ❌ ") + t)
    so_dat = sum(d for _, d in ca)

    g = globals()
    ban_hong = [
        ("bỏ qua lỗi JS", "phan_xet",
         lambda kq: (2, ["x"]) if kq is None else ((0, []) if len(kq[0].strip()) >= CHU_TOI_THIEU and TEN_TRANG in kq[0] else (1, ["y"]))),
        ("bỏ sàn chữ", "phan_xet",
         lambda kq: (2, ["x"]) if kq is None else ((1, ["e"]) if kq[1] else (0, []))),
        ("không đo được mà trả 0", "phan_xet", lambda kq: (0, []) if kq is None else _PX(kq)),
    ]
    _PX_goc = phan_xet
    g["_PX"] = _PX_goc
    loi_chay = mo_trang(_dung("loi_chay"), 300)
    trang = mo_trang(_dung("trang_trang"), 300)
    sau_ve = mo_trang(_dung("loi_sau_ve"), 300)
    bat = 0
    for ten, ham, thay in ban_hong:
        g[ham] = thay
        try:
            do = ((phan_xet(loi_chay)[0] != 1) or (phan_xet(trang)[0] != 1)
                  or (phan_xet(sau_ve)[0] != 1) or (phan_xet(None)[0] != 2))
        finally:
            g[ham] = _PX_goc
        bat += do
        print(("  ✅ bản hỏng bị bắt: " if do else "  ❌ bản hỏng LỌT: ") + ten)
    print("\n%d/%d ca đạt · %d/%d bản hỏng bị bắt" % (so_dat, len(ca), bat, len(ban_hong)))
    return 0 if so_dat == len(ca) and bat == len(ban_hong) else 1


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(tu_kiem() if "--tu-kiem" in a else main(a))
