#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TEST: kích CI trượt vì MẤT MẠNG thì phải CHỜ MẠNG VỀ, không được bỏ lượt.

⚠ VÌ SAO CÓ FILE NÀY — sự cố THẬT tối 30/08/2026:
`com.huy.diemtin-kich-ci` nổ ĐÚNG giờ 21:00 và 22:00 (log ghi "khớp mốc (lệch 0')"),
nhưng cả 06 lần gọi `gh workflow run` đều trả `error connecting to api.github.com` —
mạng nhà rớt. Script thử 03 lần trong 04 phút rồi dừng hẳn; mạng về lúc nào cũng không
còn ai kích lại, nên bản tin TỐI mất trắng. Sổ đã gửi trống dòng `[toi]` ngày 30/08.

Đây là hỏng CÂM đúng nghĩa: job nổ đúng giờ, mã thoát có, log có dòng báo động — mà
người dùng chỉ thấy "hôm nay không có bản tin". Ca chính ở đây là ca PHẢI CHẶN: dựng
đúng cảnh mất mạng rồi khẳng định script KHÔNG bỏ lượt.

Chạy:
    python3 tests/test-kich-ci-mat-mang.py
    python3 tests/test-kich-ci-mat-mang.py --tu-kiem

Chạy hoàn toàn offline: `gh` giả bằng script shell, phép đo mạng ghim bằng
KICHCI_MANG_GIA, nhịp chờ hạ xuống 1 giây bằng KICHCI_NHIP_GIAY.
"""
import contextlib
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
KICH_THAT = REPO / "scripts" / "kich_ci.py"
KICH_PY = pathlib.Path(os.environ.get("KICH_CI_PY") or KICH_THAT)

# `gh` giả: kịch bản khai bằng biến môi trường GH_GIA_KICH_BAN.
#   "mang"     -> luôn trả lỗi mạng
#   "quyen"    -> luôn trả lỗi quyền (KHÔNG phải lỗi mạng)
#   "mang-roi-ok" -> lần gọi `workflow run` đầu lỗi mạng, các lần sau thành công
GH_GIA = r'''#!/bin/bash
dem="$GH_GIA_DEM"
case "$1" in
  run)   # `gh run list ...` -> danh sách run
     if [ -f "$dem" ] && [ "$(cat "$dem")" -ge 1 ]; then
        echo '[{"databaseId":222},{"databaseId":111}]'
     else
        echo '[{"databaseId":111}]'
     fi
     exit 0 ;;
  workflow)
     case "$GH_GIA_KICH_BAN" in
       mang)
          echo "error connecting to api.github.com" >&2
          echo "check your internet connection or https://githubstatus.com" >&2
          exit 1 ;;
       quyen)
          echo "HTTP 403: Resource not accessible by integration" >&2
          exit 1 ;;
       mang-roi-ok)
          n=0; [ -f "$dem.wf" ] && n=$(cat "$dem.wf")
          if [ "$n" -eq 0 ]; then
             echo 1 > "$dem.wf"
             echo "error connecting to api.github.com" >&2
             exit 1
          fi
          echo 1 > "$dem"
          exit 0 ;;
     esac
     exit 0 ;;
esac
exit 0
'''


@contextlib.contextmanager
def san(kich_ban, mang_gia, tran_phut=1, nhip_giay=1):
    """Dựng sân: gh giả + các seam. Trả (thư mục, env)."""
    d = pathlib.Path(tempfile.mkdtemp(prefix="kich-mat-mang-"))
    gh = d / "gh"
    gh.write_text(GH_GIA, encoding="utf-8")
    gh.chmod(0o755)
    (d / "dem").write_text("0", encoding="utf-8")
    (d / "dem.wf").write_text("0", encoding="utf-8")
    env = dict(
        os.environ,
        KICHCI_GH=str(gh),
        KICHCI_MANG_GIA=mang_gia,
        KICHCI_TRAN_CHO_PHUT=str(tran_phut),
        KICHCI_NHIP_GIAY=str(nhip_giay),
        GH_GIA_KICH_BAN=kich_ban,
        GH_GIA_DEM=str(d / "dem"),
    )
    try:
        yield d, env
    finally:
        shutil.rmtree(d, ignore_errors=True)


def chay(env, args, timeout=90):
    return subprocess.run([sys.executable, str(KICH_PY), *args],
                          capture_output=True, text=True, env=env, timeout=timeout)


CA = []


def ca(ten):
    def deco(f):
        CA.append((ten, f))
        return f
    return deco


# ═══════════════ ca PHẢI CHẶN — mất mạng thì KHÔNG được bỏ lượt ═══════════════

@ca('01. PHẢI CHẶN: mất mạng thì script phải NÓI ra là đang chờ, không lặng lẽ bỏ lượt')
def _():
    with san("mang", mang_gia="0") as (d, env):
        r = chay(env, ["--wf", "claude-web-scan.yml"])
    return "chờ mạng về" in r.stdout, f"stdout: {r.stdout.strip()[-300:]}"


@ca('02. PHẢI CHẶN: mất mạng thì KHÔNG được đốt hết 3 lần thử rồi thôi (đúng lỗi 30/08)')
def _():
    with san("mang", mang_gia="0") as (d, env):
        r = chay(env, ["--wf", "claude-web-scan.yml"])
    so_lan = r.stdout.count("lần 2/3") + r.stdout.count("lần 3/3")
    return so_lan == 0, f"vẫn đốt lần thử: {so_lan} · stdout: {r.stdout.strip()[-300:]}"


@ca('03. PHẢI CHẶN: mạng về giữa chừng thì phải kích LẠI và ăn (không bỏ lượt)')
def _():
    with san("mang-roi-ok", mang_gia="1") as (d, env):
        r = chay(env, ["--wf", "claude-web-scan.yml"])
    return (r.returncode == 0 and "mạng đã về" in r.stdout and "đã tạo run mới" in r.stdout), \
        f"exit={r.returncode} · stdout: {r.stdout.strip()[-300:]}"


@ca('04. PHẢI CHẶN: hết trần chờ mà mạng chưa về thì phải BÁO ĐỘNG, không im')
def _():
    with san("mang", mang_gia="0") as (d, env):
        r = chay(env, ["--wf", "claude-web-scan.yml"])
    return (r.returncode == 1 and "hết trần" in r.stdout), \
        f"exit={r.returncode} · stdout: {r.stdout.strip()[-300:]}"


@ca('05. PHẢI CHẶN chặn-oan: lỗi KHÔNG phải mạng (403) thì đừng chờ, báo ngay')
def _():
    with san("quyen", mang_gia="1") as (d, env):
        r = chay(env, ["--wf", "claude-web-scan.yml"], timeout=180)
    return ("chờ mạng về" not in r.stdout and r.returncode == 1), \
        f"exit={r.returncode} · stdout: {r.stdout.strip()[-300:]}"


@ca('06. PHẢI CHẶN: nhận diện lỗi mạng phải phủ đủ các câu gh/curl hay trả')
def _():
    import importlib.util
    sp = importlib.util.spec_from_file_location("kc", KICH_PY)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    phai_bat = [
        "error connecting to api.github.com",
        "dial tcp: lookup api.github.com: no such host",
        "Could not resolve host: api.github.com",
        "connect: network is unreachable",
        "urlopen error [Errno 8] nodename nor servname provided, or not known",
    ]
    khong_duoc_bat = [
        "HTTP 403: Resource not accessible by integration",
        "could not find any workflows named claude-web-scan.yml",
        "gh: authentication token expired",
    ]
    xau = [f"BỎ SÓT: {t[:50]}" for t in phai_bat if not m.la_loi_mang(t)]
    xau += [f"BẮT OAN: {t[:50]}" for t in khong_duoc_bat if m.la_loi_mang(t)]
    return not xau, " · ".join(xau)


@ca('07. PHẢI CHẶN: chuỗi rỗng/None không được tính là lỗi mạng (fail về phía KÊU)')
def _():
    import importlib.util
    sp = importlib.util.spec_from_file_location("kc", KICH_PY)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return (not m.la_loi_mang("") and not m.la_loi_mang(None)), "chuỗi rỗng bị coi là lỗi mạng"


# ═══════════════ ca chống chặn oan ═══════════════

@ca('08. Mạng bình thường: kích ăn ngay, không đụng tới nhánh chờ')
def _():
    with san("mang-roi-ok", mang_gia="1") as (d, env):
        (d / "dem.wf").write_text("1", encoding="utf-8")
        env = dict(env)
        r = chay(env, ["--wf", "claude-web-scan.yml"])
    return (r.returncode == 0 and "chờ mạng về" not in r.stdout), \
        f"exit={r.returncode} · stdout: {r.stdout.strip()[-300:]}"


@ca('09. Vòng chờ KHÔNG lặp vô hạn: chờ nhiều nhất một vòng rồi dừng')
def _():
    with san("mang-roi-ok", mang_gia="0") as (d, env):
        t0 = time.time()
        r = chay(env, ["--wf", "claude-web-scan.yml"], timeout=120)
        mat = time.time() - t0
    # trần 1 phút + nhịp 1 giây => phải xong dưới ~80 giây, không nhân đôi
    return mat < 80, f"mất {mat:.0f}s (trần chờ 60s) · exit={r.returncode}"


@ca('10. Seam đo mạng phải THẬT SỰ ghim được (nếu không, mọi ca trên đo mạng thật)')
def _():
    import importlib.util
    sp = importlib.util.spec_from_file_location("kc", KICH_PY)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    os.environ["KICHCI_MANG_GIA"] = "0"
    try:
        tat = m.co_mang()
        os.environ["KICHCI_MANG_GIA"] = "1"
        bat = m.co_mang()
    finally:
        os.environ.pop("KICHCI_MANG_GIA", None)
    return (tat is False and bat is True), f"ghim 0 -> {tat} · ghim 1 -> {bat}"


# ═══════════════════════════ tự kiểm: bản hỏng ═══════════════════════════
BAN_HONG = [
    ("kich_ci.py: gỡ nhánh chờ mạng (đúng hành vi cũ, tối 30/08 mất bản tin)",
     KICH_THAT, "KICH_CI_PY", "kich_ci.py",
     ("            if la_loi_mang(loi):", "            if False:"),
     [1, 2, 3, 4]),
    ("kich_ci.py: la_loi_mang() luôn False (cổng có mặt nhưng không bao giờ kêu)",
     KICH_THAT, "KICH_CI_PY", "kich_ci.py",
     ("    return any(m in t for m in MAU_LOI_MANG)", "    return False"),
     [1, 2, 3, 4, 6]),
    ("kich_ci.py: la_loi_mang() luôn True (chặn oan — lỗi quyền cũng ngồi chờ)",
     KICH_THAT, "KICH_CI_PY", "kich_ci.py",
     ("    return any(m in t for m in MAU_LOI_MANG)", "    return True"),
     [5, 6, 7]),
    ("kich_ci.py: chờ xong mạng về vẫn KHÔNG kích lại (chờ suông)",
     KICH_THAT, "KICH_CI_PY", "kich_ci.py",
     ("                if cho_mang_ve(log):", "                if False and cho_mang_ve(log):"),
     [3]),
    ("kich_ci.py: hết trần thì im lặng trả True (giấu lỗi)",
     KICH_THAT, "KICH_CI_PY", "kich_ci.py",
     ('    log_fn(f"   📡 hết trần {TRAN_CHO_MANG_PHUT}\' mà mạng vẫn chưa về")\n    return False',
      '    return True'),
     [4]),
    ("kich_ci.py: seam đo mạng lặng lẽ rơi về đo thật",
     KICH_THAT, "KICH_CI_PY", "kich_ci.py",
     ('    gia = (os.environ.get("KICHCI_MANG_GIA") or "").strip()', '    gia = ""'),
     [10]),
]


def tu_kiem() -> int:
    print("TỰ KIỂM — dựng bản đã gỡ dòng bảo vệ, các ca đã khai PHẢI ĐỎ")
    print("═" * 78)
    hong = 0
    for nhan, f_that, seam, ten, (tim, thay), ca_phai_do in BAN_HONG:
        goc = f_that.read_text(encoding="utf-8")
        if goc.count(tim) != 1:
            print(f"  ✗ {nhan}\n        │ KHÔNG áp được phép thay: {goc.count(tim)} chỗ khớp "
                  f"trong {f_that.name} (cần đúng 1). Mã nguồn đã đổi → sửa lại test.")
            hong += 1
            continue
        d = pathlib.Path(tempfile.mkdtemp(prefix="kich-hong-"))
        (d / ten).write_text(goc.replace(tim, thay), encoding="utf-8")
        env = dict(os.environ, **{seam: str(d / ten)})
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
            print(f"        │ ⚠ ca {sorted(thieu)} VẪN XANH trên bản hỏng → test không bắt "
                  f"được lỗi này.")
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
    print("TEST KÍCH CI KHI MẤT MẠNG — mất mạng thì chờ mạng về, không bỏ lượt bản tin")
    print(f"(bản đang thử: {KICH_PY})")
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
        print(f"✗ {hong}/{len(CA)} ca HỎNG — mất mạng vẫn có thể làm mất nguyên một bản tin.")
        return 1
    print(f"✓ {len(CA)}/{len(CA)} ca đạt — mất mạng thì chờ, lỗi khác thì báo ngay.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
