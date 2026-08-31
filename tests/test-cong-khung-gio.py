#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TEST CỔNG KHUNG GIỜ của scripts/state.py — phiên sai giờ KHÔNG được nhận ca.

⚠ VÌ SAO CÓ FILE NÀY — sự cố THẬT, Huy kêu sáng 31/08/2026 "sao điểm tin sáng nay vẫn
chạy 1h sáng":
Cron GitHub trễ bất định 2-4 tiếng (đo 6 ngày liền qua `gh run list`: mốc `47 13 * * *`
tức 20:47 giờ VN thật sự khởi động lúc 17:23-18:11Z, tức 00:23-01:11 giờ VN HÔM SAU).
`current_slot()` chỉ hỏi đồng hồ, thấy 00:46 < 14:00 nên gán ô "sang" — phiên TỐI trễ
biến thành phiên SÁNG, quét và GỬI bản tin lúc 01:25 sáng, đồng thời chiếm mất ô "sang"
khiến mọi mốc sáng thật (local 04:30/04:45, CI 03:47/04:47) đều exit 10 SKIP. Ô "toi"
hôm đó không còn ai chạy: sổ đã gửi trống dòng `[toi]` cả 30/08 lẫn 31/08, lần cuối là
29/08 21:30.

Đây đúng loại hỏng CÂM của mục 17 CLAUDE.md: mọi lớp đều báo thành công, log đầy đủ,
canary im lặng — chỉ có Huy nhận bản tin lúc 1 giờ sáng và mất hẳn bản tin tối. Vì vậy
ca chính ở đây là ca PHẢI CHẶN: ghim giờ vào đúng lúc xấu rồi khẳng định `claim` trả
exit 12 và KHÔNG hề đụng vào sổ.

Chạy:
    python3 tests/test-cong-khung-gio.py
    python3 tests/test-cong-khung-gio.py --tu-kiem   # chứng minh test này BẮT ĐƯỢC lỗi

Không cần thư viện ngoài.
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
STATE_THAT = REPO / "scripts" / "state.py"

# Seam để tự kiểm: bản đang thử. Mặc định là bản thật.
STATE_PY = pathlib.Path(os.environ.get("STATE_PY") or STATE_THAT)

CHAN = 12   # mã thoát của cổng khung giờ
XONG = 10   # ca đã xong hôm nay
CHAY = 0    # được quét


def chay(kho: pathlib.Path, args, gio=None, phien_test=None):
    """Gọi state.py trong một 'repo' giả, ghim giờ bằng seam STATE_GIO_GIA."""
    env = dict(os.environ, STATE_LOGS_DIR=str(kho))
    env.pop("DIEMTIN_PHIEN_TEST", None)
    env.pop("STATE_GIO_GIA", None)
    if gio is not None:
        env["STATE_GIO_GIA"] = gio
    if phien_test is not None:
        env["DIEMTIN_PHIEN_TEST"] = phien_test
    return subprocess.run([sys.executable, str(STATE_PY), *args],
                          capture_output=True, text=True, env=env)


@contextlib.contextmanager
def kho_gia():
    d = pathlib.Path(tempfile.mkdtemp(prefix="khung-gio-"))
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


def co_so(kho: pathlib.Path) -> dict:
    try:
        return json.loads((kho / "state.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


CA = []


def ca(ten):
    def deco(f):
        CA.append((ten, f))
        return f
    return deco


# ═════════════════════ ca PHẢI CHẶN — giờ xấu, không được quét ═════════════════════

@ca('01. PHẢI CHẶN: 00:46 (đúng giờ sự cố 31/08) claim ô "sang" -> exit 12')
def _():
    with kho_gia() as d:
        r = chay(d, ["claim", "web-scan", "--slot", "sang"], gio="00:46")
    return r.returncode == CHAN, f"exit={r.returncode} · {r.stdout.strip()[:200]}"


@ca('02. PHẢI CHẶN: 00:46 KHÔNG được ghi gì vào sổ (chặn xong sổ vẫn trống)')
def _():
    with kho_gia() as d:
        chay(d, ["claim", "web-scan", "--slot", "sang"], gio="00:46")
        so = co_so(d)
    return so == {}, f"so sau khi bi chan: {json.dumps(so, ensure_ascii=False)[:200]}"


@ca('03. PHẢI CHẶN: 01:11 (mốc trễ thứ hai cùng đêm) -> exit 12')
def _():
    with kho_gia() as d:
        r = chay(d, ["claim", "web-scan", "--slot", "sang"], gio="01:11")
    return r.returncode == CHAN, f"exit={r.returncode} · {r.stdout.strip()[:200]}"


@ca('04. PHẢI CHẶN: 14:30 (giữa chiều, ô "toi") -> exit 12')
def _():
    with kho_gia() as d:
        r = chay(d, ["claim", "web-scan", "--slot", "toi"], gio="14:30")
    return r.returncode == CHAN, f"exit={r.returncode} · {r.stdout.strip()[:200]}"


@ca('05. PHẢI CHẶN: 10:22 (cron trễ sang trưa, ô "sang") -> exit 12')
def _():
    with kho_gia() as d:
        r = chay(d, ["claim", "web-scan", "--slot", "sang"], gio="10:22")
    return r.returncode == CHAN, f"exit={r.returncode} · {r.stdout.strip()[:200]}"


@ca('06. PHẢI CHẶN: event-scan cũng bị soi giờ, không riêng web-scan')
def _():
    with kho_gia() as d:
        r = chay(d, ["claim", "event-scan", "--slot", "sang"], gio="00:46")
    return r.returncode == CHAN, f"exit={r.returncode} · {r.stdout.strip()[:200]}"


@ca('07. PHẢI CHẶN: `check` cũng bị soi giờ (không được lách qua đường đọc)')
def _():
    with kho_gia() as d:
        r = chay(d, ["check", "web-scan", "--slot", "sang"], gio="00:46")
    return r.returncode == CHAN, f"exit={r.returncode} · {r.stdout.strip()[:200]}"


@ca('08. PHẢI CHẶN: --bo-cong-gio KHÔNG kèm lý do thì từ chối (exit 2)')
def _():
    with kho_gia() as d:
        r = chay(d, ["claim", "web-scan", "--slot", "sang", "--bo-cong-gio"], gio="00:46")
    return r.returncode == 2, f"exit={r.returncode} · {(r.stderr or r.stdout).strip()[:200]}"


@ca('09. PHẢI CHẶN: thông điệp nói rõ GIỜ và KHUNG để đọc log biết ngay vì sao')
def _():
    with kho_gia() as d:
        r = chay(d, ["claim", "web-scan", "--slot", "sang"], gio="00:46")
    ra = r.stdout
    return ("00:46" in ra and "03:00-09:00" in ra), f"stdout: {ra.strip()[:200]}"


# ═════════════════════ ca PHẢI CHO QUA — không được chặn oan ═════════════════════

@ca('10. 04:30 (mốc local sáng) claim ô "sang" -> exit 0, quét bình thường')
def _():
    with kho_gia() as d:
        r = chay(d, ["claim", "web-scan", "--slot", "sang"], gio="04:30")
    return r.returncode == CHAY, f"exit={r.returncode} · {r.stdout.strip()[:200]}"


@ca('11. 03:47 và 04:47 (hai mốc CI sáng) đều lọt')
def _():
    xau = []
    for g in ("03:47", "04:47"):
        with kho_gia() as d:
            r = chay(d, ["claim", "web-scan", "--slot", "sang"], gio=g)
        if r.returncode != CHAY:
            xau.append(f"{g}: exit={r.returncode}")
    return not xau, " · ".join(xau)


@ca('12. 20:47 · 21:15 · 21:47 · 22:00 (bốn lớp tối) đều lọt')
def _():
    xau = []
    for g in ("20:47", "21:15", "21:47", "22:00"):
        with kho_gia() as d:
            r = chay(d, ["claim", "web-scan", "--slot", "toi"], gio=g)
        if r.returncode != CHAY:
            xau.append(f"{g}: exit={r.returncode}")
    return not xau, " · ".join(xau)


@ca('13. Biên khung: 03:00 và 09:00 lọt, 02:59 và 09:01 bị chặn')
def _():
    xau = []
    for g, mong in (("03:00", CHAY), ("09:00", CHAY), ("02:59", CHAN), ("09:01", CHAN)):
        with kho_gia() as d:
            r = chay(d, ["claim", "web-scan", "--slot", "sang"], gio=g)
        if r.returncode != mong:
            xau.append(f"{g}: exit={r.returncode}, mong {mong}")
    return not xau, " · ".join(xau)


@ca('14. Đường thoát: --bo-cong-gio kèm lý do thì quét được, và IN lý do ra')
def _():
    with kho_gia() as d:
        r = chay(d, ["claim", "web-scan", "--slot", "sang",
                     "--bo-cong-gio", "chay bu tay sau khi may ngu"], gio="00:46")
    return (r.returncode == CHAY and "chay bu tay sau khi may ngu" in r.stdout), \
        f"exit={r.returncode} · {r.stdout.strip()[:200]}"


@ca('15. Phiên TEST hạ tầng bỏ qua cổng giờ (phải chạy lại được bất kể giờ nào)')
def _():
    with kho_gia() as d:
        r = chay(d, ["claim", "web-scan", "--slot", "sang"], gio="00:46", phien_test="1")
    return r.returncode == CHAY, f"exit={r.returncode} · {r.stdout.strip()[:200]}"


@ca('16. Cổng giờ đứng TRƯỚC cổng đã-xong: sai giờ vẫn là 12, không phải 10')
def _():
    with kho_gia() as d:
        chay(d, ["claim", "web-scan", "--slot", "sang"], gio="04:30")
        chay(d, ["done", "web-scan", "--slot", "sang", "xong roi"], gio="04:40")
        r_dung = chay(d, ["claim", "web-scan", "--slot", "sang"], gio="05:00")
        r_sai = chay(d, ["claim", "web-scan", "--slot", "sang"], gio="00:46")
    return (r_dung.returncode == XONG and r_sai.returncode == CHAN), \
        f"trong khung exit={r_dung.returncode} (mong {XONG}) · ngoai khung " \
        f"exit={r_sai.returncode} (mong {CHAN})"


@ca('17. drive-import KHÔNG bị cổng giờ (pipeline đã tắt lịch, đừng chặn oan)')
def _():
    with kho_gia() as d:
        r = chay(d, ["claim", "drive-import", "--slot", "sang"], gio="00:46")
    return r.returncode == CHAY, f"exit={r.returncode} · {r.stdout.strip()[:200]}"


@ca('18. Seam giờ giả phải THẬT SỰ ghim được giờ (nếu không, mọi ca trên đo giờ thật)')
def _():
    ma = (
        "import importlib.util,sys;"
        f"sp=importlib.util.spec_from_file_location('st', r'{STATE_PY}');"
        "m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);"
        "t=m.gio_hien_tai();print(f'{t.hour:02d}:{t.minute:02d}')"
    )
    r = subprocess.run([sys.executable, "-c", ma], capture_output=True, text=True,
                       env=dict(os.environ, STATE_GIO_GIA="00:46"))
    return r.stdout.strip() == "00:46", f"gio_hien_tai() tra: {r.stdout.strip()!r} · {r.stderr.strip()[:150]}"


# ═══════════════════════════ tự kiểm: bản hỏng ═══════════════════════════
# (nhãn · file thật · biến seam · tên bản hỏng · phép thay · các ca BẮT BUỘC phải đỏ)
BAN_HONG = [
    ("state.py: gỡ hẳn cổng giờ khỏi claim (đúng hành vi cũ, đêm 31/08)",
     STATE_THAT, "STATE_PY", "state.py",
     ("        if pipeline in (\"web-scan\", \"event-scan\") and not la_phien_test():",
      "        if False:"),
     [1, 2, 3, 4, 5, 6, 7, 9, 13, 14, 16]),
    ("state.py: ngoai_khung() luôn trả rỗng (cổng có mặt nhưng không bao giờ kêu)",
     STATE_THAT, "STATE_PY", "state.py",
     ("    if dau <= phut <= cuoi:\n        return \"\"",
      "    if True:\n        return \"\""),
     [1, 2, 3, 4, 5, 6, 7, 9, 13, 16]),
    ("state.py: khung \"sang\" nới ra cả ngày (nới trần cho vừa lỗi)",
     STATE_THAT, "STATE_PY", "state.py",
     ('KHUNG_GIO = {"sang": (3 * 60, 9 * 60), "toi": (19 * 60 + 30, 23 * 60 + 30)}',
      'KHUNG_GIO = {"sang": (0, 24 * 60), "toi": (19 * 60 + 30, 23 * 60 + 30)}'),
     [1, 2, 3, 5, 9, 13, 16]),
    ("state.py: cổng giờ đặt SAU cổng đã-xong (thứ tự sai, phiên trễ vẫn chiếm ô)",
     STATE_THAT, "STATE_PY", "state.py",
     ("            ly_do = ngoai_khung(use_slot)", "            ly_do = \"\""),
     [1, 2, 3, 4, 5, 6, 7, 9, 13, 16]),
    ("state.py: --bo-cong-gio nhận lý do rỗng (đường thoát mở toang)",
     STATE_THAT, "STATE_PY", "state.py",
     ("        if not bo_cong_gio.strip():", "        if False:"),
     [8]),
    ("state.py: seam giờ giả lặng lẽ rơi về giờ thật (cổng không đo được nữa)",
     STATE_THAT, "STATE_PY", "state.py",
     ("    gia = (os.environ.get(GIO_GIA_ENV) or \"\").strip()", "    gia = \"\""),
     [18]),
    ("state.py: cổng chặn cả phiên TEST (chặn oan, không test được ban ngày)",
     STATE_THAT, "STATE_PY", "state.py",
     ("        if pipeline in (\"web-scan\", \"event-scan\") and not la_phien_test():",
      "        if pipeline in (\"web-scan\", \"event-scan\"):"),
     [15]),
    ("state.py: cổng chặn MỌI pipeline (chặn oan drive-import)",
     STATE_THAT, "STATE_PY", "state.py",
     ("        if pipeline in (\"web-scan\", \"event-scan\") and not la_phien_test():",
      "        if not la_phien_test():"),
     [17]),
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
        d = pathlib.Path(tempfile.mkdtemp(prefix="khung-gio-hong-"))
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
        print(f"✗ {hong}/{len(BAN_HONG)} phép thử tự kiểm THẤT BẠI — bộ test chưa chứng minh "
              f"được là nó bắt được lỗi.")
        return 1
    print(f"✓ {len(BAN_HONG)}/{len(BAN_HONG)} bản hỏng đều bị bắt — bộ test này có giá trị.")
    return 0


def tien_kiem() -> bool:
    """Chốt an toàn: hai seam phải thật sự có tác dụng, nếu không thì mọi ca chạy mù."""
    with kho_gia() as d:
        r = chay(d, ["show"])
        if "chua co" not in r.stdout:
            print("✗ TIỀN KIỂM HỎNG — STATE_LOGS_DIR không ghim được thư mục logs, DỪNG để "
                  "khỏi phá logs/state.json thật.")
            print(f"    stdout: {r.stdout.strip()[:300]}")
            return False
    return True


def main() -> int:
    if "--tu-kiem" in sys.argv:
        return tu_kiem()
    print("TEST CỔNG KHUNG GIỜ — phiên khởi động sai giờ không được nhận ca, không được quét")
    print(f"(bản đang thử: {STATE_PY})")
    print("─" * 78)
    if not tien_kiem():
        return 1
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
        print(f"✗ {hong}/{len(CA)} ca HỎNG — cron trễ vẫn có thể cướp ca và gửi bản tin sai giờ.")
        return 1
    print(f"✓ {len(CA)}/{len(CA)} ca đạt — phiên sai giờ bị chặn, phiên đúng giờ không bị chặn oan.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
