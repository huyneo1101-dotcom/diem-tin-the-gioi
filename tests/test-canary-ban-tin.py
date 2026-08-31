#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TEST HỒI QUY CHO CANARY BẢN TIN (.github/scripts/canary.py).

⚠ VÌ SAO CÓ FILE NÀY — luật đúc 29.7.2026 (CLAUDE.md toàn cục, mục 17):
Canary là cổng "hỏng thì im lặng cho qua" ở dạng thuần khiết: ngày bình thường nó IM, nên
canary đã chết trông y hệt một ngày yên ổn. Nó lại là lớp cuối cùng — mọi cảnh báo khác đều
đòi routine phải CHẠY mới báo được, chỉ canary bắt được ca "không chạy phát nào".

Nó còn hỏng theo chiều NGƯỢC LẠI, và chiều đó đã xảy ra thật: 28/07/2026 cron GitHub đẩy ca
`toi` sang 00:23, `hom_nay()` nhảy ngày nên canary đi hỏi "bản tin tối NGÀY MAI đâu" và nhắn
báo động oan trong khi bản tin đã gửi lúc 21:37 hôm trước. Kêu oan vài lần là hết ai đọc —
lúc đó canary chết thật. Nên bộ này có CẢ ca "PHẢI KÊU" lẫn ca "PHẢI IM ở đúng mốc đã vấp".

Test chạy HOÀN TOÀN OFFLINE: `DRY_RUN=1`, sổ/state trỏ vào thư mục tạm, đồng hồ bị ghim.

Chạy:
    python3 tests/test-canary-ban-tin.py
    python3 tests/test-canary-ban-tin.py --tu-kiem   # chứng minh test này BẮT ĐƯỢC lỗi
"""
import contextlib
import datetime
import importlib.util
import io
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import types

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
GS = REPO / ".github" / "scripts"
# Seam để tự kiểm: trỏ sang một bản canary.py khác (xem --tu-kiem).
MOD_PATH = pathlib.Path(os.environ.get("CANARY_TIN_MOD") or (GS / "canary.py"))
# Bộ này chạy OFFLINE, mà `canary.main()` từ 21/08/2026 còn gọi thêm lớp đo "bản người dùng
# đang thấy" (curl tới github.io). Tắt lớp đó ở đây để test không phụ thuộc mạng — lớp đó có
# bộ riêng: tests/test-canary-web-lech.py.
os.environ["CANARY_BO_KIEM_WEB"] = "1"

VN = datetime.datetime.now().astimezone().tzinfo   # thay ngay sau khi nạp module


def _nap():
    spec = importlib.util.spec_from_file_location("canary_tin_duoi_thu", MOD_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ghim_dong_ho(M, luc: str):
    """Ghim `datetime.datetime.now(VN)` bên trong module về một mốc cố định.

    Canary đọc giờ thẳng từ `datetime` nên không có seam sẵn. Không ghim được đồng hồ thì ca
    hồi quy 00:23 (bug kêu oan 28/07) KHÔNG đời nào chạy tới — mà đó chính là ca đắt nhất.
    """
    moc = datetime.datetime.strptime(luc, "%Y-%m-%d %H:%M").replace(tzinfo=M.VN)

    class DT(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return moc

    M.datetime = types.SimpleNamespace(datetime=DT, timedelta=datetime.timedelta)


def chay(ca, so=None, state=None, luc="2026-07-29 22:45"):
    """Chạy canary với sổ/state giả và đồng hồ ghim. Trả (mã thoát, đầu ra)."""
    M = _nap()
    d = pathlib.Path(tempfile.mkdtemp(prefix="canarytin-"))
    (d / "logs").mkdir()
    if so is not None:
        (d / "logs" / "da-gui-email.json").write_text(
            so if isinstance(so, str) else json.dumps(so, ensure_ascii=False), encoding="utf-8")
    if state is not None:
        (d / "logs" / "state.json").write_text(
            json.dumps(state, ensure_ascii=False), encoding="utf-8")
    M.SO = d / "logs" / "da-gui-email.json"
    M.STATE = d / "logs" / "state.json"
    ghim_dong_ho(M, luc)

    argv_cu, os_cu = sys.argv, os.environ.get("DRY_RUN")
    sys.argv = ["canary.py", "--ca", ca]
    os.environ["DRY_RUN"] = "1"
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            ma = M.main()
    except SystemExit as e:                       # argparse lỗi
        ma = e.code
    finally:
        sys.argv = argv_cu
        if os_cu is None:
            os.environ.pop("DRY_RUN", None)
        else:
            os.environ["DRY_RUN"] = os_cu
        shutil.rmtree(d, ignore_errors=True)
    return ma, buf.getvalue()


def so_gui(buoi, luc, n=12):
    return {"lan_gui": [{"luc": luc, "buoi": buoi,
                         "urls": [f"https://x.example/{i}" for i in range(n)]}]}


# Ca nào soi pipeline/ô nào — ĐỌC THẲNG từ canary.py chứ không chép tay. Bảng này đã bẫy
# test một lần: ca `sukien` soi ô **"sang"** của `event-scan`, không phải ô "sukien".
BANG_CA = {k: (v[1], v[2]) for k, v in _nap().CA.items()}


def state(ca="toi", ngay="2026-07-29", status="DONE"):
    pipeline, o = BANG_CA[ca]
    return {pipeline: {"lastSuccess": {o: ngay} if status == "DONE" else {},
                       "lastRunAt": f"{ngay}T21:05:00+07:00", "lastStatus": status,
                       "note": "ghi chú thử"}}


def keu(out):
    return "--- DRY_RUN, không gửi ---" in out


def im(out):
    return not keu(out) and "[canary]" in out


# ═════════════════════════════ các ca thử ═════════════════════════════
CA = []


def ca(ten):
    def deco(f):
        CA.append((ten, f))
        return f
    return deco


@ca('1. Ca TỐI: sổ TRỐNG mà phiên quét DONE → PHẢI KÊU, chỉ đúng khâu GỬI')
def _():
    ma, out = chay("toi", so={"lan_gui": []}, state=state())
    return keu(out) and "khâu GỬI" in out, out


@ca('2. Ca TỐI: sổ TRỐNG và phiên quét CHƯA xong → PHẢI KÊU, chỉ đúng khâu QUÉT')
def _():
    ma, out = chay("toi", so={"lan_gui": []}, state=state(status="RUNNING"))
    return keu(out) and "khâu QUÉT" in out, out


@ca('3. Ca TỐI: sổ CÓ bản tin tối hôm nay → phải IM (chống kêu oan)')
def _():
    ma, out = chay("toi", so=so_gui("toi", "2026-07-29T21:37:00+07:00"), state=state())
    return im(out) and ma == 0, out


@ca('4. HỒI QUY 28/07: canary chạy 00:23, bản tin tối HÔM TRƯỚC đã gửi 21:37 → phải IM')
def _():
    # Đúng ca đã kêu oan thật. `hom_nay()` nhảy ngày qua nửa đêm; phải quy về NGÀY CỦA CA.
    ma, out = chay("toi", so=so_gui("toi", "2026-07-28T21:37:00+07:00"),
                   state=state(ngay="2026-07-28"), luc="2026-07-29 00:23")
    return im(out) and ma == 0, out


@ca('5. Cùng mốc 00:23 nhưng sổ chỉ có bản tin của 2 NGÀY TRƯỚC → PHẢI KÊU (chống im oan)')
def _():
    # Chữa kêu oan mà chữa quá tay thành "cái gì cũng tính là đã gửi" thì canary chết câm.
    ma, out = chay("toi", so=so_gui("toi", "2026-07-27T21:37:00+07:00"),
                   state=state(ngay="2026-07-28"), luc="2026-07-29 00:23")
    return keu(out), out


@ca('6. Ca TỐI: sổ chỉ có bản tin SÁNG cùng ngày → PHẢI KÊU THIẾU (buổi khác không tính)')
def _():
    # Đòi đúng LOẠI tiếng kêu, không chỉ đòi "có kêu": từ 31/08/2026 canary còn một tiếng
    # kêu thứ hai (SAI GIỜ), và nếu ca này nhận bừa tiếng nào cũng được thì bản hỏng "sổ nào
    # cũng tính là đã gửi" lọt lưới — tự kiểm đã bắt đúng chỗ đó.
    ma, out = chay("toi", so=so_gui("sang", "2026-07-29T05:20:00+07:00"), state=state())
    return keu(out) and "CHƯA có" in out, out


@ca('6b. HỒI QUY 31/08: bản tin SÁNG có gửi nhưng lúc 01:25 → PHẢI KÊU SAI GIỜ')
def _():
    # Sự cố thật: cron GitHub trễ 4h, mốc TỐI nổ lúc 00:46 rồi tự nhận là ca sáng và gửi
    # lúc 01:25. Canary cũ chỉ hỏi "có gửi không" nên im tuyệt đối; Huy là người phát hiện.
    ma, out = chay("sang", so=so_gui("sang", "2026-07-29T01:25:00+07:00"),
                   state=state(ca="sang", ngay="2026-07-29"), luc="2026-07-29 06:15")
    return keu(out) and "SAI GIỜ" in out and "01:25" in out, out


@ca('6c. Chống kêu oan: bản tin sáng gửi 04:18 (kịp hạn 04:30) → phải IM')
def _():
    ma, out = chay("sang", so=so_gui("sang", "2026-07-29T04:18:00+07:00"),
                   state=state(ca="sang", ngay="2026-07-29"), luc="2026-07-29 06:15")
    return im(out) and ma == 0, out


@ca('6d. Ca TỐI gửi 22:40 (quá hạn chót 22:00) → PHẢI KÊU SAI GIỜ')
def _():
    ma, out = chay("toi", so=so_gui("toi", "2026-07-29T22:40:00+07:00"), state=state())
    return keu(out) and "SAI GIỜ" in out, out


@ca('6e. Bản tin sáng gửi 04:50 (trễ hạn 04:30 chỉ 20 phút) → PHẢI KÊU')
def _():
    # Đúng cảnh của lịch CŨ: mốc kích 04:30 + quét 16-21 phút = 04:50, tức LUÔN vỡ hạn mà
    # không lớp nào kêu. Ca này canh việc ai đó lặng lẽ nới hạn cho vừa lịch chạy.
    ma, out = chay("sang", so=so_gui("sang", "2026-07-29T04:50:00+07:00"),
                   state=state(ca="sang", ngay="2026-07-29"), luc="2026-07-29 06:15")
    return keu(out) and "SAI GIỜ" in out, out


@ca('7. Sổ HỎNG (JSON vỡ) → PHẢI KÊU, canary không được chết câm vì file rác')
def _():
    ma, out = chay("toi", so="{ đây không phải JSON", state=state())
    return keu(out), out


@ca('8. THIẾU HẲN sổ (file chưa có) → PHẢI KÊU')
def _():
    ma, out = chay("toi", so=None, state=state())
    return keu(out), out


@ca('9. Ca SỰ KIỆN: phiên event-scan CHƯA xong → PHẢI KÊU')
def _():
    ma, out = chay("sukien", so={"lan_gui": []},
                   state=state("sukien", status="RUNNING"))
    return keu(out) and "SỰ KIỆN" in out, out


@ca('10. Ca SỰ KIỆN: phiên DONE → phải IM, dù sổ TRỐNG (không gửi là hành vi ĐÚNG)')
def _():
    ma, out = chay("sukien", so={"lan_gui": []},
                   state=state("sukien"))
    return im(out) and ma == 0, out


# ═══════════════════════════ tự kiểm: bản hỏng ═══════════════════════════
BAN_HONG = [
    ("bỏ phép quy đổi NGÀY CỦA CA (tái sinh bug kêu oan 28/07)",
     ('    if ca == "toi" and luc.hour < 12:', '    if False:'),
     [4]),
    ("sổ nào cũng tính là đã gửi (canary câm hoàn toàn)",
     ('        if lan.get("buoi") == buoi and ngay_ca_tu_iso(buoi, str(lan.get("luc", ""))) == ngay:',
      '        if True:'),
     [5, 6]),
    ("bỏ phép kiểm dạng sổ (file rác làm canary chết giữa chừng)",
     ('    if not so or not isinstance(so.get("lan_gui"), list):', '    if False:'),
     [7, 8]),
    ("phiên quét lúc nào cũng coi là DONE",
     ('    xong = (p.get("lastSuccess") or {}).get(o) == ngay', '    xong = True'),
     [2, 9]),
    ("nuốt tiếng kêu ở nhánh sáng/tối (biết hụt mà không báo)",
     ('    print(f"::warning::canary {args.ca}: {khau} | {mota}")\n    return gui(text)',
      '    return 0'),
     [1, 2, 5, 6, 7, 8]),
    ("nhánh 'đã gửi' luôn đúng (im mọi ngày)",
     ('    if lan:', '    if True:'),
     [1, 2, 5, 6, 7, 8]),
]


def tu_kiem() -> int:
    goc = (GS / "canary.py").read_text(encoding="utf-8")
    print("TỰ KIỂM — dựng bản canary.py đã gỡ dòng bảo vệ, các ca đã khai PHẢI ĐỎ")
    print("═" * 78)
    hong = 0
    for nhan, (tim, thay), ca_phai_do in BAN_HONG:
        if goc.count(tim) != 1:
            print(f"  ✗ {nhan}\n        │ KHÔNG áp được phép thay: {goc.count(tim)} chỗ khớp "
                  f"(cần đúng 1). Mã nguồn đã đổi → sửa lại test.")
            hong += 1
            continue
        # Bản hỏng phải nằm TRONG .github/scripts/: canary tự suy ROOT từ vị trí của chính nó
        # rồi `from tg_api import ...`. Để ở /tmp thì mọi ca đỏ vì ImportError — đỏ vì lý do
        # sai thì không chứng minh được gì.
        f = GS / ".canary_tu_kiem.py"
        try:
            f.write_text(goc.replace(tim, thay), encoding="utf-8")
            env = dict(os.environ, CANARY_TIN_MOD=str(f))
            r = subprocess.run([sys.executable, str(pathlib.Path(__file__).resolve())],
                               capture_output=True, text=True, env=env)
        finally:
            f.unlink(missing_ok=True)
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
    print("═" * 78)
    if hong:
        print(f"✗ {hong}/{len(BAN_HONG)} phép thử tự kiểm THẤT BẠI — bộ test chưa chứng minh được "
              f"là nó bắt được lỗi.")
        return 1
    print(f"✓ {len(BAN_HONG)}/{len(BAN_HONG)} bản hỏng đều bị bắt — bộ test này có giá trị.")
    return 0


def main() -> int:
    if "--tu-kiem" in sys.argv:
        return tu_kiem()
    print("TEST CANARY BẢN TIN — mọi ca 'PHẢI KÊU' phải thật sự kêu, mọi ca 'PHẢI IM' phải im\n"
          f"(bản đang thử: {MOD_PATH})")
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
        print(f"✗ {hong}/{len(CA)} ca HỎNG — canary bản tin không còn kêu đúng; "
              f"canary câm nghĩa là bản tin hụt mà không ai biết.")
        return 1
    print(f"✓ {len(CA)}/{len(CA)} ca đạt — canary bản tin còn sống.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
