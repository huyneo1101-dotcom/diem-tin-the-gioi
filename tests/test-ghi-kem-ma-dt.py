#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test chiều GHI vào 2 bảng dt_* phải kèm mã `x-dt-key` (thêm 22/11/2026).

    python3 tests/test-ghi-kem-ma-dt.py            # chạy bộ ca trên bản thật
    python3 tests/test-ghi-kem-ma-dt.py --tu-kiem  # dựng bản hỏng, chứng minh bộ ca còn răng

VÌ SAO: trước 22/11 RLS insert của `dt_jaylam_inbox` và `dt_bot_hoi` là `true` cho anon.
Khoá công khai nằm trong mọi app dùng chung kho Supabase này, nên người lạ chèn được dòng
tuỳ ý, và phiên quét tin trên máy Mac đọc lại nguyên văn trong chế độ không hỏi quyền. Nay
RLS đòi `dt_ma_hop_le()`; bên ghi thiếu mã là 401 câm, nên hai hàm ghi phải (i) gửi kèm mã
và (ii) thiếu mã thì KÊU rồi dừng, không gửi mù.

Không chạm mạng thật: `subprocess.run` bị tráo, chỉ đọc lại tham số curl.
"""
import importlib.util
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest.mock as mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
# Bản hỏng nằm ở thư mục tạm nên phải tự mở đường tới các module anh em (tg_api…).
sys.path.insert(0, str(ROOT / "scripts"))
CA = []


def kiem(ten, dat):
    CA.append((ten, bool(dat)))
    print(("✓" if dat else "✗") + " " + ten)


def nap(duong, ten):
    spec = importlib.util.spec_from_file_location(ten, duong)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class Tra:
    def __init__(self):
        self.lenh = []

    def __call__(self, args, **kw):
        self.lenh.append(args)
        return subprocess.CompletedProcess(args, 0, stdout="\n@@201", stderr="")


def co_ma(args, ma):
    return any(args[i] == "-H" and args[i + 1] == f"x-dt-key: {ma}" for i in range(len(args) - 1))


def chay(tb_path, bl_path):
    CA.clear()
    moi = {"SUPABASE_ANON_KEY": "sb_publishable_thu_khong_that", "DT_BOT_KEY": "ma-thu-123",
           "DT_KEY_FILE": "/khong/co/file/nay"}
    with mock.patch.dict(os.environ, moi):
        tb = nap(tb_path, "tb_ghi_ma")
        bl = nap(bl_path, "bl_ghi_ma")
        t = Tra()
        with mock.patch.object(tb.subprocess, "run", t):
            ok = tb.luu_tin_jaylam("1", "Jay", "a.docx", "noi dung")
        kiem("[1] jaylam: có mã thì gửi kèm header x-dt-key", ok and t.lenh and co_ma(t.lenh[0], "ma-thu-123"))
        t = Tra()
        with mock.patch.object(bl.subprocess, "run", t):
            rc = bl.ghi({"chat_id": "1", "cau_hoi": "x"})
        kiem("[2] bot_luu: có mã thì gửi kèm header x-dt-key", rc == 0 and t.lenh and co_ma(t.lenh[0], "ma-thu-123"))
    moi["DT_BOT_KEY"] = ""
    with mock.patch.dict(os.environ, moi):
        tb = nap(tb_path, "tb_ghi_ma2")
        bl = nap(bl_path, "bl_ghi_ma2")
        t = Tra()
        with mock.patch.object(tb.subprocess, "run", t):
            ok = tb.luu_tin_jaylam("1", "Jay", "a.docx", "noi dung")
        kiem("[3] PHẢI CHẶN — jaylam thiếu mã: trả False, không gửi mù", ok is False and not t.lenh)
        t = Tra()
        with mock.patch.object(bl.subprocess, "run", t):
            rc = bl.ghi({"chat_id": "1", "cau_hoi": "x"})
        kiem("[4] PHẢI CHẶN — bot_luu thiếu mã: mã thoát 1, không gửi mù", rc == 1 and not t.lenh)
    return all(d for _, d in CA)


def ban_hong(goc, bo):
    t = goc.read_text(encoding="utf-8")
    assert bo in t, f"không tìm thấy dòng cần gỡ trong {goc.name}"
    d = pathlib.Path(tempfile.mkdtemp()) / ("hong_" + goc.name)
    d.write_text(t.replace(bo, "", 1), encoding="utf-8")
    return d


def main():
    tb, bl = ROOT / "scripts" / "telegram_bot.py", ROOT / "scripts" / "bot_luu.py"
    if "--tu-kiem" not in sys.argv:
        dat = chay(tb, bl)
        print(f"\n{sum(d for _, d in CA)}/{len(CA)} ca đạt")
        return 0 if dat else 1
    hong = [
        ("gỡ header ở jaylam", ban_hong(tb, '         "-H", f"x-dt-key: {dt_key}",\n'), bl),
        ("gỡ header ở bot_luu", tb, ban_hong(bl, '         "-H", f"x-dt-key: {ma}",\n')),
        ("gỡ chốt thiếu mã ở jaylam", ban_hong(tb, "    if not dt_key:\n"
         '        print("[jaylam] THIẾU mã DT_BOT_KEY — bảng dt_jaylam_inbox đã khoá chiều ghi, "\n'
         '              "không lưu được tin", file=sys.stderr)\n        return False\n'), bl),
        ("gỡ chốt thiếu mã ở bot_luu", tb, ban_hong(bl, "    if not ma:\n"
         '        print("Thiếu mã DT_BOT_KEY — bảng dt_bot_hoi đã khoá chiều ghi (22/11/2026).",\n'
         "              file=sys.stderr)\n        return 1\n")),
    ]
    rang = True
    for ten, a, b in hong:
        bat = not chay(a, b)
        print(f"{'✓' if bat else '✗'} bản hỏng «{ten}» {'bị bắt' if bat else 'LỌT'}\n")
        rang &= bat
    print("TỰ KIỂM:", "còn răng" if rang else "MẤT RĂNG")
    return 0 if rang else 1


if __name__ == "__main__":
    sys.exit(main())
