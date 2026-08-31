#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TEST phép đo GIỜ BẢN TIN TỚI TAY (scripts/do_gio_ban_tin.py).

⚠ VÌ SAO CÓ FILE NÀY: phép đo này là lớp duy nhất hỏi *bản tin tới tay lúc mấy giờ* thay vì
*quy trình đã chạy chưa*. Nó chỉ có giá trị nếu KÊU đúng lúc phải kêu — nên ca chính ở đây
là ca PHẢI KÊU, dựng lại đúng hai đêm 30 và 31/08/2026 (ca sáng gửi 01:08 và 01:25, ca tối
vắng mặt) rồi khẳng định phép đo trả mã 1 chứ không im.

Chạy:
    python3 tests/test-do-gio-ban-tin.py
    python3 tests/test-do-gio-ban-tin.py --tu-kiem
"""
import contextlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

os.environ["TZ"] = "Asia/Ho_Chi_Minh"
with contextlib.suppress(AttributeError):
    time.tzset()

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
DO_THAT = REPO / "scripts" / "do_gio_ban_tin.py"
DO_PY = pathlib.Path(os.environ.get("DO_GIO_PY") or DO_THAT)

DAT, KEU, KHONG_DO_DUOC = 0, 1, 2


@contextlib.contextmanager
def so_gia(lan_gui):
    d = pathlib.Path(tempfile.mkdtemp(prefix="do-gio-"))
    f = d / "da-gui-email.json"
    f.write_text(json.dumps({"lan_gui": lan_gui}, ensure_ascii=False), encoding="utf-8")
    try:
        yield f
    finally:
        shutil.rmtree(d, ignore_errors=True)


def chay(so, gio_gia, them=()):
    return subprocess.run(
        [sys.executable, str(DO_PY), "--so", str(so), "--gio-gia", gio_gia, *them],
        capture_output=True, text=True, timeout=60)


def gui(luc, buoi, n=5):
    return {"luc": luc, "buoi": buoi, "urls": [f"u{i}" for i in range(n)]}


# Sổ "sạch": ca sáng 31/08 gửi 04:41, ca tối 30/08 gửi 21:22.
SACH = [gui("2026-08-30T21:22:00+07:00", "toi"), gui("2026-08-31T04:41:00+07:00", "sang")]
# Sổ THẬT hai đêm hỏng: sáng 31/08 gửi 01:25, ca tối 30/08 không có dòng nào.
HONG_THAT = [gui("2026-08-30T01:08:53+07:00", "sang"), gui("2026-08-31T01:25:31+07:00", "sang")]

CA = []


def ca(ten):
    def deco(f):
        CA.append((ten, f))
        return f
    return deco


# ═══════════ ca PHẢI KÊU ═══════════

@ca('01. PHẢI KÊU: đúng sổ thật của hai đêm hỏng (sáng 01:25 · tối vắng) -> mã 1')
def _():
    with so_gia(HONG_THAT) as s:
        r = chay(s, "2026-08-31T12:00:00+07:00")
    return r.returncode == KEU, f"exit={r.returncode} · {r.stdout.strip()[:250]}"


@ca('02. PHẢI KÊU: nói rõ ca sáng SAI_GIO và ca tối VANG, không gộp thành một chữ chung')
def _():
    with so_gia(HONG_THAT) as s:
        r = chay(s, "2026-08-31T12:00:00+07:00", ["--json"])
    d = json.loads(r.stdout)
    tt = {k["ca"]: k["trang_thai"] for k in d["ket"]}
    return (tt.get("sang") == "SAI_GIO" and tt.get("toi") == "VANG"), f"{tt}"


@ca('03. PHẢI KÊU: ca sáng gửi 01:08 (đêm 30/08) cũng bị bắt')
def _():
    with so_gia([gui("2026-08-30T01:08:53+07:00", "sang"),
                 gui("2026-08-29T21:30:00+07:00", "toi")]) as s:
        r = chay(s, "2026-08-30T12:00:00+07:00")
    return r.returncode == KEU and "SAI_GIO" in r.stdout, f"exit={r.returncode} · {r.stdout[:250]}"


@ca('04. PHẢI KÊU: ca tối gửi 23:50 (quá khung 23:30) -> SAI_GIO')
def _():
    with so_gia([gui("2026-08-30T23:50:00+07:00", "toi"),
                 gui("2026-08-31T04:41:00+07:00", "sang")]) as s:
        r = chay(s, "2026-08-31T12:00:00+07:00", ["--json"])
    tt = {k["ca"]: k["trang_thai"] for k in json.loads(r.stdout)["ket"]}
    return tt.get("toi") == "SAI_GIO", f"{tt}"


@ca('05. PHẢI KÊU: ca sáng vắng hẳn và đã quá 09:00 -> VANG, không chờ nữa')
def _():
    with so_gia([gui("2026-08-30T21:22:00+07:00", "toi")]) as s:
        r = chay(s, "2026-08-31T12:00:00+07:00", ["--json"])
    tt = {k["ca"]: k["trang_thai"] for k in json.loads(r.stdout)["ket"]}
    return (tt.get("sang") == "VANG" and r.returncode == KEU), f"{tt} · exit={r.returncode}"


@ca('06. PHẢI KÊU: sổ hỏng/không đọc được thì trả mã 2, KHÔNG âm thầm báo đạt')
def _():
    d = pathlib.Path(tempfile.mkdtemp(prefix="do-gio-hong-"))
    try:
        f = d / "so.json"
        f.write_text("{ khong phai json", encoding="utf-8")
        r = chay(f, "2026-08-31T12:00:00+07:00")
        thieu = chay(d / "khong-co-file.json", "2026-08-31T12:00:00+07:00")
    finally:
        shutil.rmtree(d, ignore_errors=True)
    return (r.returncode == KHONG_DO_DUOC and thieu.returncode == KHONG_DO_DUOC), \
        f"sổ hỏng exit={r.returncode} · sổ thiếu exit={thieu.returncode}"


@ca('07. PHẢI KÊU: khung giờ phải LẤY TỪ state.py, không chép số (đổi state.py là đổi theo)')
def _():
    with so_gia(SACH) as s:
        r = chay(s, "2026-08-31T12:00:00+07:00", ["--json"])
    khung = {k["ca"]: k["khung"] for k in json.loads(r.stdout)["ket"]}
    import importlib.util
    sp = importlib.util.spec_from_file_location("st", REPO / "scripts" / "state.py")
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    mong = {c: list(v) for c, v in m.KHUNG_GIO.items()}
    return khung == mong, f"phép đo dùng {khung} · state.py khai {mong}"


# ═══════════ ca chống kêu oan ═══════════

@ca('08. Sổ sạch (sáng 04:41 · tối 21:22) -> mã 0, im lặng')
def _():
    with so_gia(SACH) as s:
        r = chay(s, "2026-08-31T12:00:00+07:00")
    return r.returncode == DAT, f"exit={r.returncode} · {r.stdout.strip()[:250]}"


@ca('09. Chống kêu oan: 06:00 sáng, ca sáng chưa gửi nhưng còn trong khung -> CHUA_TOI_GIO')
def _():
    with so_gia([gui("2026-08-30T21:22:00+07:00", "toi")]) as s:
        r = chay(s, "2026-08-31T06:00:00+07:00", ["--json"])
    tt = {k["ca"]: k["trang_thai"] for k in json.loads(r.stdout)["ket"]}
    return tt.get("sang") == "CHUA_TOI_GIO", f"{tt}"


@ca('10. Chống kêu oan: ca tối xét NGÀY HÔM QUA, không hỏi ca tối chưa tới giờ của hôm nay')
def _():
    with so_gia(SACH) as s:
        r = chay(s, "2026-08-31T12:00:00+07:00", ["--json"])
    ngay = {k["ca"]: k["ngay"] for k in json.loads(r.stdout)["ket"]}
    return (ngay.get("toi") == "2026-08-30" and ngay.get("sang") == "2026-08-31"), f"{ngay}"


@ca('11. Biên khung: sáng 03:00 và 09:00 đạt · 02:59 và 09:01 kêu')
def _():
    xau = []
    for luc, mong in (("2026-08-31T03:00:00+07:00", "DUNG_GIO"),
                      ("2026-08-31T09:00:00+07:00", "DUNG_GIO"),
                      ("2026-08-31T02:59:00+07:00", "SAI_GIO"),
                      ("2026-08-31T09:01:00+07:00", "SAI_GIO")):
        with so_gia([gui("2026-08-30T21:22:00+07:00", "toi"), gui(luc, "sang")]) as s:
            r = chay(s, "2026-08-31T12:00:00+07:00", ["--json"])
        tt = {k["ca"]: k["trang_thai"] for k in json.loads(r.stdout)["ket"]}
        if tt.get("sang") != mong:
            xau.append(f"{luc[11:16]}: {tt.get('sang')} (mong {mong})")
    return not xau, " · ".join(xau)


@ca('12. Ca `sukien` không bị xét giờ (nó đi kèm ca sáng, không phải bản tin riêng)')
def _():
    with so_gia(SACH + [gui("2026-08-31T01:25:33+07:00", "sukien", 1)]) as s:
        r = chay(s, "2026-08-31T12:00:00+07:00")
    return r.returncode == DAT, f"exit={r.returncode} · {r.stdout.strip()[:250]}"


@ca('13. Lấy lần gửi MỚI NHẤT trong ngày, không lấy lần đầu (có ca chạy bù)')
def _():
    with so_gia([gui("2026-08-30T21:22:00+07:00", "toi"),
                 gui("2026-08-31T01:25:00+07:00", "sang"),
                 gui("2026-08-31T04:41:00+07:00", "sang")]) as s:
        r = chay(s, "2026-08-31T12:00:00+07:00", ["--json"])
    k = {x["ca"]: x for x in json.loads(r.stdout)["ket"]}["sang"]
    return (k["gio"] == "04:41" and k["trang_thai"] == "DUNG_GIO"), f"{k}"


# ═══════════════════════════ tự kiểm: bản hỏng ═══════════════════════════
BAN_HONG = [
    ("do_gio_ban_tin.py: bỏ phép so khung, cái gì cũng đúng giờ",
     DO_THAT, "DO_GIO_PY", "do_gio_ban_tin.py",
     ("        trong = dau <= phut <= cuoi", "        trong = True"),
     [2, 3, 4, 11]),
    ("do_gio_ban_tin.py: ca vắng mặt bị nuốt thành đạt",
     DO_THAT, "DO_GIO_PY", "do_gio_ban_tin.py",
     ('                ket.append({"ca": ca, "ngay": ngay, "trang_thai": "VANG",',
      '                ket.append({"ca": ca, "ngay": ngay, "trang_thai": "DUNG_GIO",'),
     [2, 5]),
    ("do_gio_ban_tin.py: mã thoát luôn 0 (kêu trên màn hình mà máy đọc thấy đạt)",
     DO_THAT, "DO_GIO_PY", "do_gio_ban_tin.py",
     ('    return 1 if any(k["trang_thai"] in ("SAI_GIO", "VANG") for k in r["ket"]) else 0',
      "    return 0"),
     [1, 3, 5]),
    ("do_gio_ban_tin.py: sổ hỏng thì trả 0 thay vì kêu không đo được",
     DO_THAT, "DO_GIO_PY", "do_gio_ban_tin.py",
     ("        print(json.dumps({\"loi\": msg}) if a.json else f\"⚠️  {msg}\")\n        return 2",
      "        return 0"),
     [6]),
    ("do_gio_ban_tin.py: chép cứng khung giờ thay vì đọc state.py",
     DO_THAT, "DO_GIO_PY", "do_gio_ban_tin.py",
     ("    return dict(m.KHUNG_GIO)", '    return {"sang": (0, 1439), "toi": (0, 1439)}'),
     [2, 3, 4, 5, 7, 11]),
    ("do_gio_ban_tin.py: ca tối hỏi ngày HÔM NAY (kêu oan mỗi sáng)",
     DO_THAT, "DO_GIO_PY", "do_gio_ban_tin.py",
     ('        ngay = (hom_qua if ca == "toi" else hom_nay).isoformat()',
      "        ngay = hom_nay.isoformat()"),
     [4, 8, 10, 12]),
]


def tu_kiem() -> int:
    print("TỰ KIỂM — dựng bản đã gỡ dòng bảo vệ, các ca đã khai PHẢI ĐỎ")
    print("═" * 78)
    hong = 0
    for nhan, f_that, seam, ten, (tim, thay), ca_phai_do in BAN_HONG:
        goc = f_that.read_text(encoding="utf-8")
        if goc.count(tim) != 1:
            print(f"  ✗ {nhan}\n        │ KHÔNG áp được phép thay: {goc.count(tim)} chỗ khớp "
                  f"trong {f_that.name} (cần đúng 1).")
            hong += 1
            continue
        d = pathlib.Path(tempfile.mkdtemp(prefix="do-gio-hong-"))
        (d / ten).write_text(goc.replace(tim, thay), encoding="utf-8")
        # DOGIO_ROOT: bản hỏng nằm ngoài repo nên phải trỏ ROOT về repo thật, nếu không
        # nó chết vì sai đường dẫn và tự kiểm "bắt được lỗi" mà chưa hề chạm tới lỗi cấy.
        env = dict(os.environ, **{seam: str(d / ten)}, DOGIO_ROOT=str(REPO))
        r = subprocess.run([sys.executable, str(pathlib.Path(__file__).resolve())],
                           capture_output=True, text=True, env=env)
        do = {int(dong[4:].split(".")[0])
              for dong in r.stdout.splitlines() if dong.startswith("  ✗ ")}
        thieu = set(ca_phai_do) - do
        thua = do - set(ca_phai_do)
        ok = not thieu
        print(f"  {'✓' if ok else '✗'} {nhan}")
        print(f"        │ ca đỏ: {sorted(do) or 'KHÔNG CÓ CA NÀO ĐỎ'} · cần đỏ: {ca_phai_do}"
              + (f" · đỏ thêm ngoài dự kiến: {sorted(thua)}" if thua else ""))
        if not ok:
            hong += 1
            print(f"        │ ⚠ ca {sorted(thieu)} VẪN XANH trên bản hỏng.")
        shutil.rmtree(d, ignore_errors=True)
    print("═" * 78)
    if hong:
        print(f"✗ {hong}/{len(BAN_HONG)} phép thử tự kiểm THẤT BẠI.")
        return 1
    print(f"✓ {len(BAN_HONG)}/{len(BAN_HONG)} bản hỏng đều bị bắt — bộ test này có giá trị.")
    return 0


def main() -> int:
    if "--tu-kiem" in sys.argv:
        return tu_kiem()
    print("TEST PHÉP ĐO GIỜ BẢN TIN — kêu khi bản tin tới sai giờ hoặc vắng mặt")
    print(f"(bản đang thử: {DO_PY})")
    print("─" * 78)
    hong = 0
    for ten, f in CA:
        try:
            ok, out = f()
        except Exception as e:                                   # noqa: BLE001
            ok, out = False, f"LỖI CHẠY: {e.__class__.__name__}: {e}"
        print(f"  {'✓' if ok else '✗'} {ten}")
        if not ok:
            hong += 1
            for dong in str(out or "(không có đầu ra)").strip().split("\n")[:8]:
                print(f"        │ {dong}")
    print("─" * 78)
    if hong:
        print(f"✗ {hong}/{len(CA)} ca HỎNG — phép đo chưa đáng tin.")
        return 1
    print(f"✓ {len(CA)}/{len(CA)} ca đạt — sai giờ thì kêu, đúng giờ thì im.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
