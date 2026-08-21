#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TEST CHO LỚP ĐO "BẢN NGƯỜI DÙNG ĐANG THẤY" của canary (.github/scripts/canary.py::kiem_web).

⚠ VÌ SAO CÓ FILE NÀY — ca hỏng thật sáng 21/08/2026: bản tin 04:17 nạp đủ vào index.html, email
đi đủ, sổ `da-gui-email.json` ghi đủ, canary im lặng — mà https://…github.io vẫn phục vụ bản
01:24. Nguyên nhân: commit do Actions đẩy bằng `GITHUB_TOKEN` không kích hoạt `on: push` của
`pages.yml`, nên trang chỉ được dựng lại khi máy Mac tình cờ đẩy một commit khác sau đó. Mọi
phép đo cũ của canary đều đọc FILE TRONG REPO nên không phép nào thấy được chuyện này.

Bộ này canh CẢ HAI CHIỀU:
 · chiều KÊU  — web lệch main dù chỉ 1 byte thì phải báo không khớp;
 · chiều IM   — mạng hỏng, HTTP 404/500, cổng chết: KHÔNG được kêu (kêu oan vài lần là Huy
                thôi đọc, lúc đó canary chết thật — cùng lý lẽ với test-canary-ban-tin.py).

Chạy HOÀN TOÀN OFFLINE: dựng máy chủ HTTP trên 127.0.0.1, trỏ canary vào bằng CANARY_WEB_URL.

Chạy:
    python3 tests/test-canary-web-lech.py
    python3 tests/test-canary-web-lech.py --tu-kiem   # chứng minh test này BẮT ĐƯỢC lỗi
"""
import hashlib
import http.server
import importlib.util
import os
import pathlib
import subprocess
import sys
import tempfile
import threading

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
GS = REPO / ".github" / "scripts"
MOD_PATH = pathlib.Path(os.environ.get("CANARY_WEB_MOD") or (GS / "canary.py"))
CANARY_YML = REPO / ".github" / "workflows" / "canary.yml"
PAGES_YML = REPO / ".github" / "workflows" / "pages.yml"


def _nap():
    spec = importlib.util.spec_from_file_location("canary_web_duoi_thu", MOD_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _May:
    """Máy chủ HTTP giả: trả `than` với mã `ma`. Dùng `ma=0` để mô phỏng cổng chết."""

    def __init__(self, than: bytes, ma: int = 200):
        self.than, self.ma = than, ma
        th = self

        class H(http.server.BaseHTTPRequestHandler):
            def do_GET(self):                                    # noqa: N802
                self.send_response(th.ma)
                self.send_header("Content-Length", str(len(th.than)))
                self.end_headers()
                self.wfile.write(th.than)

            def log_message(self, *a):                           # im lặng
                pass

        self.srv = http.server.HTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}/index.html"

    def __enter__(self):
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *a):
        self.srv.shutdown()
        self.srv.server_close()


def _do(than_web: bytes, than_repo: bytes, ma: int = 200, url=None):
    """Chạy kiem_web với web trả `than_web` và index.html trong repo là `than_repo`."""
    M = _nap()
    with tempfile.TemporaryDirectory() as d:
        goc = pathlib.Path(d)
        (goc / "index.html").write_bytes(than_repo)
        M.ROOT = goc
        os.environ.pop("CANARY_BO_KIEM_WEB", None)
        if url is not None:
            return M.kiem_web(url)
        with _May(than_web, ma) as may:
            return M.kiem_web(may.url)


CA = []


def ca(ten):
    def deco(f):
        CA.append((f"{len(CA) + 1:02d}. {ten}", f))
        return f
    return deco


@ca("PHẢI KÊU: web phục vụ bản CŨ, main đã có bản mới")
def _c1():
    khop, mota = _do(b"<html>ban tin 19/08</html>", b"<html>ban tin 21/08</html>")
    return (not khop), mota


@ca("PHẢI KÊU: lệch đúng MỘT byte (không được 'gần đúng thì cho qua')")
def _c2():
    khop, mota = _do(b"<html>x</html>", b"<html>y</html>")
    return (not khop), mota


@ca("PHẢI IM: web khớp bit-đối-bit với main")
def _c3():
    than = b"<html>ban tin 21/08</html>"
    khop, mota = _do(than, than)
    return khop, mota


@ca("PHẢI IM: HTTP 404 (không đo được thì không kêu oan)")
def _c4():
    khop, mota = _do(b"khong thay", b"<html>ban tin</html>", ma=404)
    return khop and "404" in mota, mota


@ca("PHẢI IM: HTTP 500")
def _c5():
    khop, mota = _do(b"loi", b"<html>ban tin</html>", ma=500)
    return khop and "500" in mota, mota


@ca("PHẢI IM: cổng chết / mạng hỏng")
def _c6():
    # Cổng 1 trên localhost: curl trả mã != 0 gần như tức thì.
    khop, mota = _do(b"", b"<html>ban tin</html>", url="http://127.0.0.1:1/index.html")
    return khop, mota


@ca("PHẢI IM: repo không có index.html (chạy ngoài repo)")
def _c7():
    M = _nap()
    with tempfile.TemporaryDirectory() as d:
        M.ROOT = pathlib.Path(d)
        khop, mota = M.kiem_web("http://127.0.0.1:1/index.html")
    return khop, mota


@ca("bam_blob khớp ĐÚNG `git hash-object` (phép so phải là sha1 kiểu git)")
def _c8():
    M = _nap()
    than = b"noi dung bat ky\n\x00\xff nhi phan"
    with tempfile.TemporaryDirectory() as d:
        f = pathlib.Path(d) / "x.bin"
        f.write_bytes(than)
        r = subprocess.run(["git", "hash-object", str(f)], capture_output=True, text=True)
    that = r.stdout.strip()
    ta = M.bam_blob(than)
    return ta == that, f"bam_blob={ta} · git hash-object={that}"


@ca("canary.yml KHÔNG được khai CANARY_WEB_URL/CANARY_BO_KIEM_WEB (cửa hậu làm lớp đo câm)")
def _c9():
    t = CANARY_YML.read_text(encoding="utf-8")
    xau = [k for k in ("CANARY_WEB_URL", "CANARY_BO_KIEM_WEB") if k in t]
    return (not xau), f"tìm thấy trong canary.yml: {xau}"


@ca("pages.yml phải dựng lại trang khi CI đẩy commit (nhánh workflow_run + checkout ref main)")
def _c10():
    t = PAGES_YML.read_text(encoding="utf-8")
    thieu = []
    if "workflow_run" not in t:
        thieu.append("workflow_run — commit do Actions đẩy bằng GITHUB_TOKEN không kích on:push")
    if "Claude web-scan" not in t:
        thieu.append("tên workflow quét tin trong danh sách workflow_run")
    if "ref: main" not in t:
        thieu.append("ref: main ở checkout — workflow_run checkout SHA CŨ, deploy lại bản cũ")
    return (not thieu), " · ".join(thieu)


# Bản hỏng cho --tu-kiem: (nhãn, (tìm, thay), các ca PHẢI ĐỎ)
BAN_HONG = [
    ("lệch cũng báo khớp (lớp đo câm hoàn toàn)",
     ("    if tren_web == tren_main:", "    if True:"),
     [1, 2]),
    # Chỉ ca [03] đỏ, KHÔNG phải 4-7: mấy ca đó trả kết quả trước khi chạy tới phép so
    # (404/500/cổng chết/không có index.html đều thoát sớm). Khai dư là tự kiểm báo oan.
    ("khớp cũng báo lệch (kêu oan mọi ngày)",
     ("    if tren_web == tren_main:", "    if False:"),
     [3]),
    ("so bằng ĐỘ DÀI thay vì nội dung (đổi 1 byte thì lọt)",
     ("    tren_web = bam_blob(than)\n    tren_main = bam_blob(trong_repo.read_bytes())",
      "    tren_web = str(len(than))\n    tren_main = str(trong_repo.stat().st_size)"),
     [2]),
    ("bỏ phép kiểm mã HTTP (trang lỗi 404 bị coi là nội dung thật → kêu oan)",
     ('    if ma != "200":', "    if False:"),
     [4, 5]),
    ("bam_blob bỏ tiền tố blob (không còn khớp git hash-object)",
     ('    return hashlib.sha1(b"blob %d\\0" % len(data) + data).hexdigest()',
      "    return hashlib.sha1(data).hexdigest()"),
     [8]),
]


def tu_kiem() -> int:
    goc = (GS / "canary.py").read_text(encoding="utf-8")
    print("TỰ KIỂM — dựng bản canary.py đã gỡ dòng bảo vệ, các ca đã khai PHẢI ĐỎ")
    print("=" * 78)
    hong = 0
    for nhan, (tim, thay), ca_phai_do in BAN_HONG:
        if goc.count(tim) != 1:
            hong += 1
            print(f"  ✗ {nhan}\n        │ ⚠ mẫu tìm khớp {goc.count(tim)} lần, phải đúng 1 — "
                  f"canary.py đã đổi, sửa lại mẫu trong BAN_HONG.")
            continue
        # ⚠ Bản hỏng phải nằm CÙNG THƯ MỤC với canary.py thật: module tính `ROOT` từ chính
        # `__file__` rồi `sys.path.insert(ROOT/"scripts")` để nạp `tg_api`. Để file hỏng ở
        # /tmp thì import chết ngay lúc nạp ⇒ MỌI ca đỏ, tự kiểm báo "bắt được" vì một lý do
        # hoàn toàn khác với lỗi vừa cấy — đúng nghĩa test mất răng. Đã vấp thật 21/08/2026.
        f = GS / "_canary-hong-tam.py"
        try:
            f.write_text(goc.replace(tim, thay), encoding="utf-8")
            r = subprocess.run([sys.executable, str(HERE / "test-canary-web-lech.py")],
                               capture_output=True, text=True,
                               env={**os.environ, "CANARY_WEB_MOD": str(f)})
        finally:
            f.unlink(missing_ok=True)
        do = {int(d[4:].split(".")[0]) for d in r.stdout.splitlines() if d.startswith("  ✗ ")}
        thieu = set(ca_phai_do) - do
        # Đỏ TOÀN BỘ ca dùng module (01-08) là dấu hiệu bản hỏng không nạp được, chứ không
        # phải lỗi cấy bị bắt — coi như tự kiểm THẤT BẠI, đừng ăn mừng nhầm.
        sap = do >= set(range(1, 9)) and set(ca_phai_do) != set(range(1, 9))
        ok = (not thieu) and not sap
        print(f"  {'✓' if ok else '✗'} {nhan}")
        print(f"        │ ca đỏ: {sorted(do) or 'KHÔNG CÓ CA NÀO ĐỎ'} · cần đỏ: {ca_phai_do}")
        if not ok:
            hong += 1
            if sap:
                print("        │ ⚠ CẢ 01-08 cùng đỏ → bản hỏng không nạp được (import chết), "
                      "không phải lỗi cấy bị bắt.")
            if thieu:
                print(f"        │ ⚠ ca {sorted(thieu)} VẪN XANH trên bản hỏng → test không bắt được lỗi này.")
    print("=" * 78)
    if hong:
        print(f"✗ {hong}/{len(BAN_HONG)} phép thử tự kiểm THẤT BẠI.")
        return 1
    print(f"✓ {len(BAN_HONG)}/{len(BAN_HONG)} bản hỏng đều bị bắt — bộ test này có giá trị.")
    return 0


def main() -> int:
    if "--tu-kiem" in sys.argv:
        return tu_kiem()
    print("TEST LỚP ĐO BẢN WEB — web lệch main phải KÊU, không đo được phải IM\n"
          f"(bản đang thử: {MOD_PATH})")
    print("-" * 78)
    hong = 0
    for ten, f in CA:
        try:
            ok, out = f()
        except Exception as e:                                   # noqa: BLE001
            ok, out = False, f"LỖI CHẠY: {e.__class__.__name__}: {e}"
        print(f"  {'✓' if ok else '✗'} {ten}")
        if not ok:
            hong += 1
            for d in str(out or "(không có đầu ra)").strip().split("\n")[:6]:
                print(f"        │ {d}")
    print("-" * 78)
    if hong:
        print(f"✗ {hong}/{len(CA)} ca HỎNG — lớp đo 'bản người dùng đang thấy' không còn tin được.")
        return 1
    print(f"✓ {len(CA)}/{len(CA)} ca đạt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
