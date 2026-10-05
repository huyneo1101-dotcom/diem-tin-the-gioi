#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TEST LỚP 2 CỦA KHOÁ QUÉT TIN: "khoá hết hạn mà run CI còn sống thì KHÔNG được giành khoá".

⚠ VÌ SAO CÓ FILE NÀY — sự cố THẬT sáng 05/10/2026 (lặp lại sự cố 19/09/2026):
CI kích tay 04:00 giờ VN claim `web-scan`, nhịp tim cuối 04:04:34 rồi chờ agent con. Phiên local
04:35 đo nhịp 31 phút > `LOCK_STALE_MIN` (30') ⇒ coi CI đã chết, giành khoá, quét lại TOÀN BỘ
(~106 lượt, 06 agent con, ~11 triệu quy đổi) trong khi CI vẫn sống và cũng quét xong. Cả hai
dùng chung ví hạn mức của Huy (CI chạy bằng CLAUDE_CODE_OAUTH_TOKEN) ⇒ ví chạm 92% trong khung
5 giờ. Vá nhịp tim ở `beat_push.py` hai lần mà vẫn hở vì phụ thuộc phiên CI nhớ gọi nhịp.
Bản vá này đổi nguồn sự thật: hỏi GitHub run `in_progress` của claude-web-scan.yml.

Chạy:
    python3 tests/test-cong-ci-song.py
    python3 tests/test-cong-ci-song.py --tu-kiem   # chứng minh test này BẮT ĐƯỢC lỗi

Không cần thư viện ngoài, không gọi mạng (seam DIEMTIN_CI_RUNS_FILE thay cho `gh run list`).
"""
import contextlib
import datetime
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
STATE_PY = pathlib.Path(os.environ.get("STATE_PY") or STATE_THAT)

O = ["--slot", "toi"]


def luc(phut_truoc: float) -> str:
    t = datetime.datetime.now().astimezone() - datetime.timedelta(minutes=phut_truoc)
    return t.isoformat(timespec="seconds")


@contextlib.contextmanager
def kho_gia():
    d = pathlib.Path(tempfile.mkdtemp(prefix="ci-song-"))
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


def gieo(kho: pathlib.Path, pipe="web-scan", nhip_phut_truoc=45):
    """Sổ khoá: RUNNING với nhịp tim cách đây `nhip_phut_truoc` phút."""
    (kho / "state.json").write_text(json.dumps(
        {pipe: {"lastRunAt": luc(60), "lastSlot": "toi", "lastStatus": "RUNNING",
                "note": "dang quet", "heartbeat": luc(nhip_phut_truoc)}}), encoding="utf-8")


def runs(kho: pathlib.Path, *ds, hong=False):
    """File giả cho `gh run list`. ds = [(id, số phút đã chạy)]. hong=True ⇒ JSON hỏng (gh lỗi)."""
    p = kho / "runs.json"
    p.write_text("{khong phai json" if hong else json.dumps(
        [{"databaseId": i, "startedAt": luc(m)} for i, m in ds]), encoding="utf-8")
    return p


def chay(kho, args, runs_file=None, **env_them):
    env = dict(os.environ, STATE_LOGS_DIR=str(kho), STATE_GIO_GIA="21:00", **env_them)
    for k in ("DIEMTIN_PHIEN_TEST", "GITHUB_RUN_ID", "DIEMTIN_CI_RUNS_FILE"):
        env.pop(k, None)
    env.update({k: v for k, v in env_them.items()})
    if runs_file is not None:
        env["DIEMTIN_CI_RUNS_FILE"] = str(runs_file)
    return subprocess.run([sys.executable, str(STATE_PY), *args],
                          capture_output=True, text=True, env=env)


CA = []


def ca(ten):
    def deco(f):
        CA.append((ten, f))
        return f
    return deco


@ca("1. PHẢI CHẶN — nhịp tim cũ 45' nhưng run CI còn chạy 50' ⇒ claim phải exit 11 (sự cố 05/10)")
def _():
    with kho_gia() as d:
        gieo(d)
        r = chay(d, ["claim", "web-scan", *O], runs(d, (111, 50)))
    return r.returncode == 11, f"exit {r.returncode} (cần 11) · {r.stdout.strip()[:200]}"


@ca("2. PHẢI CHẶN — cùng ca với event-scan (cùng lớp 2 cho cả hai pipeline)")
def _():
    with kho_gia() as d:
        gieo(d, pipe="event-scan")
        r = chay(d, ["claim", "event-scan", *O], runs(d, (111, 50)))
    return r.returncode == 11, f"exit {r.returncode} (cần 11) · {r.stdout.strip()[:200]}"


@ca("3. chống chặn oan — nhịp cũ và GitHub KHÔNG có run nào sống ⇒ CI thật sự chết, claim phải qua (exit 0)")
def _():
    with kho_gia() as d:
        gieo(d)
        r = chay(d, ["claim", "web-scan", *O], runs(d))
    return r.returncode == 0, f"exit {r.returncode} (cần 0 — nếu 11 thì lưới local mất tác dụng) · {r.stdout.strip()[:200]}"


@ca("4. chống chặn oan — run 'sống' đã quá trần 135' (kẹt) không được giữ khoá mãi")
def _():
    with kho_gia() as d:
        gieo(d)
        r = chay(d, ["claim", "web-scan", *O], runs(d, (111, 200)))
    return r.returncode == 0, f"exit {r.returncode} (cần 0) · {r.stdout.strip()[:200]}"


@ca("5. chống chặn oan — run duy nhất đang sống là CHÍNH MÌNH (GITHUB_RUN_ID) thì không tự chặn mình")
def _():
    with kho_gia() as d:
        gieo(d)
        r = chay(d, ["claim", "web-scan", *O], runs(d, (111, 5)), GITHUB_RUN_ID="111")
    return r.returncode == 0, f"exit {r.returncode} (cần 0) · {r.stdout.strip()[:200]}"


@ca("6. PHẢI KÊU — không hỏi được GitHub (gh lỗi) ⇒ không im: stderr phải nói rõ, rồi mới theo luật nhịp cũ")
def _():
    with kho_gia() as d:
        gieo(d)
        r = chay(d, ["claim", "web-scan", *O], runs(d, hong=True))
    return ("khong hoi duoc GitHub" in r.stderr and r.returncode == 0), \
        f"exit {r.returncode} (cần 0) · stderr: {r.stderr.strip()[:200]!r}"


@ca("7. đường thoát — --force vẫn cướp được khoá khi biết chắc run kia kẹt")
def _():
    with kho_gia() as d:
        gieo(d)
        r = chay(d, ["claim", "web-scan", *O, "--force"], runs(d, (111, 50)))
    return r.returncode == 0, f"exit {r.returncode} (cần 0) · {r.stdout.strip()[:200]}"


@ca("8. luật cũ không đổi — nhịp tim CÒN TƯƠI ⇒ exit 11 dù GitHub báo không có run nào")
def _():
    with kho_gia() as d:
        gieo(d, nhip_phut_truoc=3)
        r = chay(d, ["claim", "web-scan", *O], runs(d))
    return r.returncode == 11, f"exit {r.returncode} (cần 11) · {r.stdout.strip()[:200]}"


@ca("9. luật cũ không đổi — sổ trống, không có khoá nào ⇒ claim thường (exit 0), không gọi hỏi GitHub vô ích")
def _():
    with kho_gia() as d:
        r = chay(d, ["claim", "web-scan", *O], runs(d, (111, 50)))
    return r.returncode == 0, f"exit {r.returncode} (cần 0 — chỉ khoá RUNNING cũ mới bị lớp 2 soi) · {r.stdout.strip()[:200]}"


# (nhãn · file thật · biến seam · tên · (tìm, thay) · ca BẮT BUỘC đỏ)
BAN_HONG = [
    ("state.py: lớp 2 bị tắt (không hỏi GitHub nữa — đúng hành vi cũ sáng 05/10)",
     STATE_THAT, "STATE_PY", "state.py",
     ("            song = ci_dang_song()", "            song = None"), [1, 2]),
    ("state.py: không lọc tuổi run (run kẹt hàng ngày giữ khoá mãi)",
     STATE_THAT, "STATE_PY", "state.py",
     ("        if tuoi is not None and tuoi < CI_TRAN_PHUT:", "        if tuoi is not None:"), [4]),
    ("state.py: không trừ run của chính mình (tự chặn mình trong CI)",
     STATE_THAT, "STATE_PY", "state.py",
     ('        if str(row.get("databaseId")) == cua_minh:', "        if False:"), [5]),
    ("state.py: lỗi gọi GitHub bị nuốt im (không còn kêu)",
     STATE_THAT, "STATE_PY", "state.py",
     ('CO THE quet chong len CI dang chay.", file=sys.stderr)',
      'CO THE quet chong len CI dang chay.", file=open(os.devnull, "w"))'), [6]),
    ("state.py: --force không còn cướp được khoá (mất đường thoát)",
     STATE_THAT, "STATE_PY", "state.py",
     ('entry.get("lastStatus") == "RUNNING" and not is_running(entry) and not force\n',
      'entry.get("lastStatus") == "RUNNING" and not is_running(entry)\n'), [7]),
    ("state.py: danh sách rỗng bị coi như 'có run sống' (chặn oan, lưới local chết)",
     STATE_THAT, "STATE_PY", "state.py",
     ("            if song:\n", "            if song is not None:\n"), [3, 4, 5]),
]


def tu_kiem() -> int:
    print("TỰ KIỂM — dựng bản đã gỡ dòng bảo vệ, các ca đã khai PHẢI ĐỎ")
    print("═" * 78)
    hong = 0
    for nhan, f_that, seam, ten, (tim, thay), ca_phai_do in BAN_HONG:
        goc = f_that.read_text(encoding="utf-8")
        if goc.count(tim) != 1:
            print(f"  ✗ {nhan}\n        │ KHÔNG áp được phép thay: {goc.count(tim)} chỗ khớp "
                  f"(cần đúng 1). Mã nguồn đã đổi → sửa lại test.")
            hong += 1
            continue
        d = pathlib.Path(tempfile.mkdtemp(prefix="ci-song-hong-"))
        (d / ten).write_text(goc.replace(tim, thay), encoding="utf-8")
        env = dict(os.environ, **{seam: str(d / ten)})
        r = subprocess.run([sys.executable, str(pathlib.Path(__file__).resolve())],
                           capture_output=True, text=True, env=env)
        do = {int(dong[4:].split(".")[0])
              for dong in r.stdout.splitlines() if dong.startswith("  ✗ ")}
        thieu = set(ca_phai_do) - do
        ok = not thieu
        print(f"  {'✓' if ok else '✗'} {nhan}")
        print(f"        │ ca đỏ: {sorted(do) or 'KHÔNG CÓ CA NÀO ĐỎ'} · cần đỏ: {ca_phai_do}")
        if not ok:
            hong += 1
            print(f"        │ ⚠ ca {sorted(thieu)} VẪN XANH trên bản hỏng → test không bắt được lỗi này.")
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
    print("TEST LỚP 2 KHOÁ QUÉT TIN — run CI còn sống thì không giành khoá")
    print(f"(bản đang thử: {STATE_PY})")
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
        print(f"✗ {hong}/{len(CA)} ca HỎNG.")
        return 1
    print(f"✓ {len(CA)}/{len(CA)} ca đạt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
