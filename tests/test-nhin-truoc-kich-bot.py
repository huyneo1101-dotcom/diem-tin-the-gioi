#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cổng: `nhin_truoc_kich_bot.py` phải KÍCH khi có FILE, không chỉ khi có TEXT.

VÌ SAO CÓ BỘ NÀY (30/07/2026) — lỗ này hỏng CÂM suốt từ 28/07:
`telegram_bot.py:388` xử lý `document` đầy đủ (tải · trích · lưu Supabase), nhưng
`nhin_truoc_kich_bot.py` lại lọc `if not (m.get("text") or "").strip(): continue` nên
**mù hoàn toàn với file .docx**. Hai nơi cùng quyết định "update này có đáng xử lý
không" mà mỗi nơi một luật ⇒ file Jay Lâm gửi phải nằm chờ cron GitHub, mà cron đó đo
thật là 66-148 phút một lần.

Không có gì báo lỗi: script vẫn chạy, vẫn mã 0, log vẫn có dòng "đã kích" — chỉ là
những dòng đó đều do TEXT gây ra. Tối 30/07 file tới trước bản tin ~20 phút và lỡ mất
bản tin; hai file vào được hôm đó đều nhờ nguyên nhân khác (một cái ăn ké lượt kích do
Huy nhắn text lúc 21:06, một cái do phiên sau kích tay lúc 21:34).

    python3 tests/test-nhin-truoc-kich-bot.py            # chạy bộ ca
    python3 tests/test-nhin-truoc-kich-bot.py --tu-kiem  # chứng minh bộ ca BẮT được lỗi
"""
import argparse
import hashlib
import importlib.util
import io
import json
import os
import pathlib
import re
import sys
import tempfile
import time
import contextlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "nhin_truoc_kich_bot.py"

CHAT_HUY = "111114309"
CHAT_LA = "999999999"


def nap(duong_dan=None):
    """Nạp module trong tiến trình. Seam `NHINTRUOC_MOD` để `--tu-kiem` tráo bản hỏng.

    Nạp bằng importlib chứ không subprocess vì phải monkeypatch `call`/`kich` — nhưng
    vì thế tên bản hỏng BẮT BUỘC mang sha1 nội dung (xem `dung_ban_hong`), không thì
    hai bản hỏng ghi cùng một tên trong cùng một giây sẽ dùng lại `.pyc` của bản trước.
    """
    p = pathlib.Path(duong_dan or os.environ.get("NHINTRUOC_MOD") or SCRIPT)
    sys.path.insert(0, str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(f"ntkb_{p.stem}", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def chay(updates, *, so_cu=None, chats=(CHAT_HUY,), duong_dan=None, kho=False):
    """Chạy `main()` với hàng đợi giả. Trả (đã_kích, số_tin_thấy, stdout)."""
    mod = nap(duong_dan)
    dau_vet = {"kich": False}

    mod.call = lambda token, method, params=None: {"ok": True, "result": list(updates)}
    mod.doc_cau_hinh = lambda: ("111:GIA", list(chats))

    def kich_gia():
        dau_vet["kich"] = True
        return True

    mod.kich = kich_gia

    fd, so_file = tempfile.mkstemp(prefix=f"so-{os.getpid()}-", suffix=".json")
    os.close(fd)
    try:
        if so_cu is None:
            os.unlink(so_file)
        else:
            pathlib.Path(so_file).write_text(json.dumps(so_cu), encoding="utf-8")
        mod.SO = pathlib.Path(so_file)

        argv_cu = sys.argv
        sys.argv = ["nhin_truoc_kich_bot.py"] + (["--kho"] if kho else [])
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                mod.main()
        finally:
            sys.argv = argv_cu
    finally:
        pathlib.Path(so_file).unlink(missing_ok=True)

    out = buf.getvalue()
    m = re.search(r"Có (\d+) tin đang chờ", out)
    return dau_vet["kich"], (int(m.group(1)) if m else 0), out


def up(uid, *, text=None, file_name=None, chat=CHAT_HUY, tuoi_phut=1):
    """Dựng một update Telegram. `file_name` => update dạng document (không có `text`)."""
    m = {"chat": {"id": int(chat)}, "date": time.time() - tuoi_phut * 60}
    if text is not None:
        m["text"] = text
    if file_name is not None:
        m["document"] = {"file_name": file_name, "file_id": "BQAC-gia"}
    return {"update_id": uid, "message": m}


# ─────────────────────────── BỘ CA ───────────────────────────
# Mỗi ca: (số, tên, hàm trả True/False)

def ca_01():
    """PHẢI KÍCH — update chỉ có document (.docx), không có text. Đây là ca gốc của cả bộ."""
    kich, n, _ = chay([up(1, file_name="30.7 ĐTN huong M.docx")])
    return kich and n == 1


def ca_02():
    """PHẢI KÍCH — file gửi ĐÊM, đã quá MAX_AGE_PHUT. Nhánh document của workflow không
    xét tuổi, nên siết ở đây là mất file lúc máy vừa ngủ dậy."""
    kich, n, _ = chay([up(1, file_name="tin.docx", tuoi_phut=600)])
    return kich and n == 1


def ca_03():
    """PHẢI KÍCH — file KHÔNG phải .docx vẫn kích: workflow vẫn tốn một lượt để nhắn
    'chỉ nhận .docx' cho người gửi. Bỏ qua ở đây là người gửi không nhận được phản hồi."""
    kich, _, _ = chay([up(1, file_name="tin.pdf")])
    return kich


def ca_04():
    """PHẢI KÍCH — hàng đợi lẫn cả file lẫn text, đếm đủ 2."""
    kich, n, _ = chay([up(1, file_name="a.docx"), up(2, text="FED họp lúc nào?")])
    return kich and n == 2


def ca_05():
    """HỒI QUY — text bình thường vẫn kích y như trước khi vá."""
    kich, n, _ = chay([up(1, text="tập trận predator run kết thúc chưa?")])
    return kich and n == 1


def ca_06():
    """CHỐNG KÍCH OAN — file của người LẠ thì bỏ, workflow cũng bỏ, kích là phí một run."""
    kich, _, _ = chay([up(1, file_name="tin.docx", chat=CHAT_LA)])
    return not kich


def ca_07():
    """CHỐNG NỚI TAY — TEXT quá cũ vẫn phải bỏ. Miễn tuổi chỉ dành cho file; nới cả text
    là kích lại những câu hỏi mà workflow sẽ vứt vì quá hạn."""
    kich, _, _ = chay([up(1, text="câu hỏi từ hôm kia", tuoi_phut=600)])
    return not kich


def ca_08():
    """CHỐNG KÍCH OAN — update không text không file (ảnh, sticker, tin vào nhóm) thì bỏ."""
    kich, _, _ = chay([up(1)])
    return not kich


def ca_09():
    """CHỐNG KÍCH OAN — hàng đợi rỗng thì im lặng, không kích."""
    kich, _, out = chay([])
    return (not kich) and "đang chờ" not in out


def ca_10():
    """CHỐNG DỘI — file đã kích rồi, chưa quá KICH_LAI_SAU_PHUT thì không kích lại."""
    kich, _, _ = chay([up(7, file_name="a.docx")],
                      so_cu={"id": 7, "luc": time.time(), "loi": 0})
    return not kich


def ca_11():
    """PHẢI KÍCH LẠI — cùng lô file cũ nhưng đã quá KICH_LAI_SAU_PHUT (workflow chết giữa
    chừng thì file không được nằm lại vĩnh viễn)."""
    mod = nap()
    lau = (mod.KICH_LAI_SAU_PHUT + 5) * 60
    kich, _, _ = chay([up(7, file_name="a.docx")],
                      so_cu={"id": 7, "luc": time.time() - lau, "loi": 0})
    return kich


def ca_12():
    """`--kho` chỉ nhìn, tuyệt đối không kích — kể cả khi có file."""
    kich, n, out = chay([up(1, file_name="a.docx")], kho=True)
    return (not kich) and n == 1 and "--kho" in out


def ca_13():
    """ĐỐI CHỨNG NGƯỢC — file có `caption` (không phải `text`) vẫn phải kích. Caption nằm
    ở khoá riêng, ai vá bằng cách thêm `or m.get("caption")` mà quên `document` sẽ trượt
    ca 01 chứ không phải ca này; ca này canh chiều ngược lại: đừng đòi phải CÓ caption."""
    u = up(1, file_name="a.docx")
    u["message"]["caption"] = ""
    kich, _, _ = chay([u])
    return kich


CAC_CA = [
    (1, "PHẢI KÍCH: update chỉ có document", ca_01),
    (2, "PHẢI KÍCH: file quá MAX_AGE vẫn kích", ca_02),
    (3, "PHẢI KÍCH: file không phải .docx", ca_03),
    (4, "PHẢI KÍCH: lẫn file + text, đếm đủ 2", ca_04),
    (5, "HỒI QUY: text thường vẫn kích", ca_05),
    (6, "CHỐNG OAN: file của người lạ", ca_06),
    (7, "CHỐNG NỚI: text quá cũ vẫn bỏ", ca_07),
    (8, "CHỐNG OAN: update không text không file", ca_08),
    (9, "CHỐNG OAN: hàng đợi rỗng", ca_09),
    (10, "CHỐNG DỘI: lô cũ trong 10 phút", ca_10),
    (11, "PHẢI KÍCH LẠI: lô cũ quá 10 phút", ca_11),
    (12, "--kho chỉ nhìn, không kích", ca_12),
    (13, "ĐỐI CHỨNG: file có caption rỗng", ca_13),
]


# ─────────────────────── BẢN HỎNG (--tu-kiem) ───────────────────────
# (nhãn, chuỗi neo, chuỗi thay, các ca PHẢI ĐỎ)
BAN_HONG = [
    ("trả lại luật cũ: chỉ xét text",
     '        la_file = bool(m.get("document"))\n'
     '        if not la_file and not (m.get("text") or "").strip():\n',
     '        la_file = False\n'
     '        if not la_file and not (m.get("text") or "").strip():\n',
     [1, 2, 3, 4, 12, 13]),

    ("áp MAX_AGE cho cả file",
     '        if not la_file and bay_gio - float(m.get("date", 0)) > MAX_AGE_PHUT * 60:\n',
     '        if bay_gio - float(m.get("date", 0)) > MAX_AGE_PHUT * 60:\n',
     [2]),

    ("bỏ lọc danh sách chat",
     '        if chats and str((m.get("chat") or {}).get("id", "")) not in chats:\n'
     '            continue        # người lạ nhắn -> workflow cũng bỏ, kích là phí một run\n',
     '        if False:\n'
     '            continue        # người lạ nhắn -> workflow cũng bỏ, kích là phí một run\n',
     [6]),

    # KHAI ĐÚNG MỘT CA 8, đừng thêm ca 7: ca 7 mang text nên nó bị chặn ở phép xét tuổi
    # phía dưới, tức phép thay này KHÔNG đi qua nhánh của nó. Khai thừa thì `--tu-kiem`
    # báo trượt vì lý do sai, che mất bản hỏng thật sự không bắt được.
    ("nhận mọi update, kể cả không text không file",
     '        if not la_file and not (m.get("text") or "").strip():\n'
     '            continue\n',
     '        if False:\n'
     '            continue\n',
     [8]),

    # Chiều NỚI của phép miễn tuổi — bản vá cho file miễn `MAX_AGE_PHUT`, ai nới luôn cho
    # text thì câu hỏi quá hạn sẽ được kích lại dù workflow sẽ vứt chúng.
    ("miễn tuổi cho CẢ text, không riêng file",
     '        if not la_file and bay_gio - float(m.get("date", 0)) > MAX_AGE_PHUT * 60:\n'
     '            continue\n',
     '        if False:\n'
     '            continue\n',
     [7]),
]


def dung_ban_hong(nhan, cu, moi):
    """Ghi bản hỏng vào ĐÚNG thư mục scripts/ (nó `import tg_api` cạnh mình).

    Tên mang PID **và sha1 NỘI DUNG**: module được nạp bằng importlib nên hai bản hỏng
    ghi cùng tên trong cùng một giây sẽ khiến `SourceFileLoader` dùng lại `.pyc` của bản
    trước — phép tự kiểm khi đó nói dối mà không báo lỗi gì.
    """
    goc = SCRIPT.read_text(encoding="utf-8")
    if goc.count(cu) != 1:
        return None, f"chuỗi neo khớp {goc.count(cu)} chỗ (phải đúng 1)"
    noi_dung = goc.replace(cu, moi)
    sha = hashlib.sha1(noi_dung.encode("utf-8")).hexdigest()[:8]
    p = SCRIPT.parent / f"_thu-hong-{os.getpid()}-{sha}-nhin-truoc.py"
    p.write_text(noi_dung, encoding="utf-8")
    return p, None


def chay_bo_ca(duong_dan=None):
    do = []
    for so, ten, ham in CAC_CA:
        cu = os.environ.get("NHINTRUOC_MOD")
        if duong_dan:
            os.environ["NHINTRUOC_MOD"] = str(duong_dan)
        try:
            dat = bool(ham())
        except Exception as e:                                   # noqa: BLE001
            dat, ten = False, f"{ten}  [lỗi: {type(e).__name__}]"
        finally:
            if duong_dan:
                os.environ.pop("NHINTRUOC_MOD", None)
                if cu:
                    os.environ["NHINTRUOC_MOD"] = cu
        if not dat:
            do.append(so)
        if not duong_dan:
            print(f"  {'✓' if dat else '✗'} [{so:>2}] {ten}")
    return do


def tu_kiem():
    print("── TỰ KIỂM: dựng bản hỏng, các ca đã khai PHẢI đỏ ──")
    tong, dat = len(BAN_HONG), 0
    for nhan, cu, moi, can_do in BAN_HONG:
        p, loi = dung_ban_hong(nhan, cu, moi)
        if loi:
            print(f"  ✗ {nhan}: KHÔNG áp được phép thay — {loi}")
            continue
        try:
            do = chay_bo_ca(p)
        finally:
            p.unlink(missing_ok=True)
        if len(do) == len(CAC_CA):
            print(f"  ✗ {nhan}: ĐỎ TOÀN BỘ {len(do)} ca — phép thay hỏng cú pháp, "
                  f"không phải gỡ lớp vá. Sửa lại phép thay.")
            continue
        thieu = [c for c in can_do if c not in do]
        if thieu:
            print(f"  ✗ {nhan}: ca {thieu} VẪN XANH (đỏ thực tế: {sorted(do)})")
            continue
        dat += 1
        print(f"  ✓ {nhan}: bắt được — ca đỏ {sorted(do)}")
    print(f"\n{dat}/{tong} bản hỏng bị bắt")
    return 0 if dat == tong else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tu-kiem", action="store_true")
    a = ap.parse_args()
    if a.tu_kiem:
        return tu_kiem()
    print(f"── {len(CAC_CA)} ca cho nhin_truoc_kich_bot.py ──")
    do = chay_bo_ca()
    print(f"\n{len(CAC_CA) - len(do)}/{len(CAC_CA)} ca đạt"
          + (f" · KHÔNG ĐẠT: {sorted(do)}" if do else ""))
    return 1 if do else 0


if __name__ == "__main__":
    sys.exit(main())
