#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TEST CỔNG "PHIÊN TEST KHÔNG ĐỤNG CỜ THẬT" (scripts/state.py + claude-web-scan.yml).

⚠ VÌ SAO CÓ FILE NÀY — sự cố THẬT tối 29/07/2026:
Nhánh `MODE=test` của `claude-web-scan.yml` (phiên "PHIEN TEST HA TANG CI", quét nhẹ 1 agent)
gọi `python3 scripts/state.py done web-scan` lúc 17:34 giờ VN và CHIẾM ô khoá `toi` của cả
ngày. Commit của nó rơi NGOÀI khung giờ gửi (cổng 2 của `notify-email.yml` đòi >= 20:30) nên
không kích email/Telegram. Hậu quả dây chuyền: CI 21:00 -> exit 10 SKIP · local 21:15 ->
exit 10 SKIP · CI 22:00 -> cũng SKIP. **Cả ba lớp im lặng, không lớp nào báo hỏng, mà bản tin
tối suýt mất trắng.** Chỉ cứu được vì phiên local 21:15 quét đè lên cờ (gửi 21:34).

Đây đúng loại cổng "hỏng thì im lặng cho qua" mà mục 17 CLAUDE.md nói tới: phiên test không
chiếm cờ thì mọi thứ im lặng — mà phiên test CHIẾM cờ thì cũng im lặng y hệt, chỉ khác là bản
tin biến mất. Chạy trăm lần "thấy nó không kêu" không chứng minh được gì. Vì vậy ca chính ở
đây là ca PHẢI CHẶN: dựng đúng điều kiện xấu (phiên test gọi `claim` rồi `done`) rồi khẳng
định cờ THẬT không hề bị chiếm, và ba lớp sau vẫn quét được.

Chạy:
    python3 tests/test-cong-phien-test.py
    python3 tests/test-cong-phien-test.py --tu-kiem   # chứng minh test này BẮT ĐƯỢC lỗi

Không cần thư viện ngoài.
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
YML_THAT = REPO / ".github" / "workflows" / "claude-web-scan.yml"

# Seam để tự kiểm: bản đang thử. Mặc định là bản thật.
STATE_PY = pathlib.Path(os.environ.get("STATE_PY") or STATE_THAT)
YML = pathlib.Path(os.environ.get("WEBSCAN_YML") or YML_THAT)

# ⚠ Bản hỏng của state.py ĐƯỢC PHÉP nằm ngoài scripts/ — khác luật chung ở CLAUDE.md mục 17.
# Lý do: state.py KHÔNG import gì của repo, và thư mục logs của nó đã lấy từ biến STATE_LOGS_DIR
# chứ không suy từ `__file__`. Đặt bản hỏng ngoài repo còn AN TOÀN HƠN: lỡ seam STATE_LOGS_DIR
# hỏng thì nó ghi vào <tạm>/logs chứ không xoá sổ cờ thật của repo. (Vẫn có chốt `tien_kiem()`
# bên dưới để bắt đúng ca seam hỏng đó.)

HOM_NAY = datetime.datetime.now().strftime("%Y-%m-%d")
PIPE = "web-scan"
O = ["--slot", "toi"]   # ép ô để ca thử không phụ thuộc giờ chạy (mốc 14:00 của state.py)


def chay(kho: pathlib.Path, args, phien_test=None):
    """Gọi state.py trong một 'repo' giả. phien_test=None => phiên THẬT."""
    env = dict(os.environ, STATE_LOGS_DIR=str(kho))
    env.pop("DIEMTIN_PHIEN_TEST", None)
    if phien_test is not None:
        env["DIEMTIN_PHIEN_TEST"] = phien_test
    return subprocess.run([sys.executable, str(STATE_PY), *args],
                          capture_output=True, text=True, env=env)


@contextlib.contextmanager
def kho_gia():
    """Thư mục logs tạm — mọi ca thử ghi vào đây, không đụng logs/state.json thật."""
    d = pathlib.Path(tempfile.mkdtemp(prefix="phien-test-"))
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


def doc(p: pathlib.Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def co_xong(kho: pathlib.Path, ten="state.json", pipe=PIPE, o="toi"):
    """Giá trị lastSuccess[o] trong sổ `ten` — None nghĩa là chưa ai chiếm ô đó."""
    return ((doc(kho / ten).get(pipe) or {}).get("lastSuccess") or {}).get(o)


def gieo_dang_chay(kho: pathlib.Path):
    """Giả lập PHIÊN THẬT đang quét: RUNNING + nhịp tim còn tươi."""
    luc = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    (kho / "state.json").write_text(json.dumps(
        {PIPE: {"lastRunAt": luc, "lastSlot": "toi", "lastStatus": "RUNNING",
                "note": "dang quet", "heartbeat": luc}}, ensure_ascii=False), encoding="utf-8")


# ═════════════════════════════ các ca thử ═════════════════════════════
CA = []


def ca(ten):
    def deco(f):
        CA.append((ten, f))
        return f
    return deco


@ca('1. PHẢI CHẶN — phiên TEST claim+done KHÔNG được chiếm ô `toi` của cờ thật (sự cố 29/07)')
def _():
    with kho_gia() as d:
        chay(d, ["claim", PIPE, *O], phien_test="1")
        chay(d, ["done", PIPE, "+1 tin (QUET TEST CI)", *O], phien_test="1")
        chiem = co_xong(d)
        con = sorted(p.name for p in d.iterdir())
    return chiem is None, f"lastSuccess.toi trong state.json = {chiem!r} · file trong logs: {con}"


@ca('2. PHẢI CHẶN — sau phiên TEST, ba lớp thật (CI 21:00 · local 21:15 · CI 22:00) vẫn claim được')
def _():
    with kho_gia() as d:
        chay(d, ["claim", PIPE, *O], phien_test="1")
        chay(d, ["done", PIPE, "+1 tin (QUET TEST CI)", *O], phien_test="1")
        r = chay(d, ["claim", PIPE, *O])            # lớp thật kế tiếp
    return r.returncode == 0, f"claim của phiên thật trả exit {r.returncode} (cần 0) · {r.stdout.strip()}"


@ca('3. PHẢI CHẶN — phiên TEST claim KHÔNG được ghi RUNNING/khoá vào cờ thật')
def _():
    with kho_gia() as d:
        chay(d, ["claim", PIPE, *O], phien_test="1")
        that = doc(d / "state.json")
    return that == {}, f"state.json thật sau khi phiên test claim: {json.dumps(that, ensure_ascii=False)}"


@ca('4. PHẢI CHẶN — phiên THẬT đang chạy thì phiên TEST phải SKIP (exit 11), không quét chồng')
def _():
    with kho_gia() as d:
        gieo_dang_chay(d)
        r = chay(d, ["claim", PIPE, *O], phien_test="1")
    return r.returncode == 11, f"exit {r.returncode} (cần 11) · {r.stdout.strip()}"


@ca('5. PHẢI CHẶN chặn-oan — cờ thật đã DONE hôm nay, phiên TEST vẫn phải chạy lại được')
def _():
    with kho_gia() as d:
        chay(d, ["claim", PIPE, *O])
        chay(d, ["done", PIPE, "+9 tin (5 chu de)", *O])
        r = chay(d, ["claim", PIPE, *O], phien_test="1")
    return r.returncode == 0, f"exit {r.returncode} (cần 0 — test là để chạy lại) · {r.stdout.strip()}"


@ca('6. chống chặn oan — phiên THẬT done vẫn phải chiếm ô `toi` như cũ')
def _():
    with kho_gia() as d:
        chay(d, ["claim", PIPE, *O])
        chay(d, ["done", PIPE, "+9 tin (5 chu de)", *O])
        chiem = co_xong(d)
    return chiem == HOM_NAY, f"lastSuccess.toi = {chiem!r} (cần {HOM_NAY!r})"


@ca('7. chống chặn oan — phiên THẬT: claim lần 2 sau done vẫn phải exit 10 (khoá cũ nguyên vẹn)')
def _():
    with kho_gia() as d:
        r1 = chay(d, ["claim", PIPE, *O])
        chay(d, ["done", PIPE, "+9 tin (5 chu de)", *O])
        r2 = chay(d, ["claim", PIPE, *O])
    return (r1.returncode, r2.returncode) == (0, 10), \
        f"claim lần 1 exit {r1.returncode} (cần 0) · lần 2 exit {r2.returncode} (cần 10)"


@ca('8. phiên TEST vẫn nghiệm thu được pipeline — done phải ghi vào state-test.json, không no-op')
def _():
    with kho_gia() as d:
        chay(d, ["claim", PIPE, *O], phien_test="1")
        chay(d, ["done", PIPE, "+1 tin (QUET TEST CI)", *O], phien_test="1")
        chiem = co_xong(d, "state-test.json")
    return chiem == HOM_NAY, f"lastSuccess.toi trong state-test.json = {chiem!r} (cần {HOM_NAY!r})"


@ca('9. đối chứng — DIEMTIN_PHIEN_TEST="0" là phiên THẬT, không bật nhầm chế độ test')
def _():
    with kho_gia() as d:
        chay(d, ["claim", PIPE, *O], phien_test="0")
        chay(d, ["done", PIPE, "+9 tin (5 chu de)", *O], phien_test="0")
        chiem = co_xong(d)
    return chiem == HOM_NAY, f"lastSuccess.toi trong state.json = {chiem!r} (cần {HOM_NAY!r})"


@ca('10. cổng còn NẰM TRÊN ĐƯỜNG ĐI — claude-web-scan.yml đặt biến, buộc theo inputs.mode')
def _():
    # Kiểm TĨNH: state.py có chặn đúng cũng vô nghĩa nếu workflow quên đặt biến ở nhánh test.
    dong = [d.strip() for d in YML.read_text(encoding="utf-8").splitlines()
            if "DIEMTIN_PHIEN_TEST" in d and not d.strip().startswith("#")]
    ok = len(dong) == 1 and "inputs.mode" in dong[0] and "'test'" in dong[0]
    return ok, f"dòng khai biến trong {YML.name}: {dong or 'KHÔNG CÓ'}"


@ca('11. phiên TEST phải in banner cảnh báo (web-scan-test.md bắt phiên DỪNG khi thiếu dòng này)')
def _():
    with kho_gia() as d:
        r = chay(d, ["claim", PIPE, *O], phien_test="1")
    ra = r.stdout
    return "PHIEN TEST" in ra and "KHONG dung cham co that" in ra, f"stdout: {ra.strip()[:200]}"


# ═══════════════════════════ tự kiểm: bản hỏng ═══════════════════════════
# (nhãn · file thật · biến seam · tên bản hỏng · phép thay · các ca BẮT BUỘC phải đỏ)
BAN_HONG = [
    ("state.py: state_path() luôn trả cờ thật (phiên test ghi đè state.json)",
     STATE_THAT, "STATE_PY", "state.py",
     ("    return STATE_TEST_PATH if la_phien_test() else STATE_PATH", "    return STATE_PATH"),
     [1, 2, 3, 8]),
    ("state.py: la_phien_test() luôn False (biến môi trường bị bỏ qua — đúng hành vi cũ)",
     STATE_THAT, "STATE_PY", "state.py",
     ('    return (os.environ.get(TEST_ENV) or "").strip().lower() in TEST_ON', "    return False"),
     [1, 2, 3, 5, 8, 11]),
    ("state.py: phiên test KHÔNG còn nhường phiên thật đang chạy",
     STATE_THAT, "STATE_PY", "state.py",
     ("            if is_running(that) and not force:", "            if False:"),
     [4]),
    ("state.py: la_phien_test() luôn True (chặn oan — phiên thật mất cờ)",
     STATE_THAT, "STATE_PY", "state.py",
     ('    return (os.environ.get(TEST_ENV) or "").strip().lower() in TEST_ON', "    return True"),
     [6, 7, 9]),
    ("workflow: nhánh test không đặt DIEMTIN_PHIEN_TEST nữa (cổng rơi khỏi đường đi)",
     YML_THAT, "WEBSCAN_YML", "claude-web-scan.yml",
     ("          DIEMTIN_PHIEN_TEST: ${{ inputs.mode == 'test' && '1' || '0' }}",
      "          KHONG_CO_BIEN_NAY: '0'"),
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
        d = pathlib.Path(tempfile.mkdtemp(prefix="phien-test-hong-"))
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
            print(f"        │ ⚠ ca {sorted(thieu)} VẪN XANH trên bản hỏng → test không bắt được lỗi này.")
        shutil.rmtree(d, ignore_errors=True)
    print("═" * 78)
    if hong:
        print(f"✗ {hong}/{len(BAN_HONG)} phép thử tự kiểm THẤT BẠI — bộ test chưa chứng minh được "
              f"là nó bắt được lỗi.")
        return 1
    print(f"✓ {len(BAN_HONG)}/{len(BAN_HONG)} bản hỏng đều bị bắt — bộ test này có giá trị.")
    return 0


def tien_kiem() -> bool:
    """Chốt an toàn: seam STATE_LOGS_DIR phải thật sự ghim được thư mục logs.

    Nếu nó không có tác dụng thì MỌI ca thử bên dưới sẽ đọc/ghi `logs/state.json` THẬT của
    repo — vừa cho kết quả sai vừa phá cờ vận hành. Thà dừng hẳn còn hơn chạy mù.
    """
    with kho_gia() as d:
        r = chay(d, ["show"])
    if "chua co" in r.stdout:
        return True
    print("✗ TIỀN KIỂM HỎNG — STATE_LOGS_DIR không ghim được thư mục logs, DỪNG để khỏi phá "
          "logs/state.json thật.")
    print(f"    stdout: {r.stdout.strip()[:300]}")
    return False


def main() -> int:
    if "--tu-kiem" in sys.argv:
        return tu_kiem()
    print("TEST CỔNG PHIÊN TEST — phiên test hạ tầng KHÔNG được chiếm ô khoá của bản tin thật")
    print(f"(bản đang thử: {STATE_PY} · {YML})")
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
        print(f"✗ {hong}/{len(CA)} ca HỎNG — phiên test có thể chiếm ô khoá của bản tin thật, "
              f"sửa trước khi chạy MODE=test.")
        return 1
    print(f"✓ {len(CA)}/{len(CA)} ca đạt — phiên test không đụng được cờ thật.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
