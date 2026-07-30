#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test cho phần NHẬN tin Jay Lâm gửi qua bot (thêm 30/07/2026): bóc chữ từ `.docx`
(`scripts/docx_text.py`) và nhánh xử lý trong `telegram_bot.py::xu_ly_tin_jaylam()`.

    python3 tests/test-nhan-tin-jaylam.py

Phần GỘP vào bản tin tối (`make_docx.py`) có bộ test riêng: `tests/test-tin-jaylam-trong-docx.py`.
Không chạm mạng thật: `call`/`tai_file`/`luu_tin_jaylam` đều bị monkeypatch trong telegram_bot.
"""
import importlib.util
import os
import pathlib
import sys
import tempfile
import unittest.mock as mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import docx_text  # noqa: E402
from docx import Document  # noqa: E402

# Seam cho `--tu-kiem`: mặc định nạp bản THẬT; bản hỏng truyền qua env. Nạp bằng importlib
# chứ không `import telegram_bot` thẳng, để tráo được bản hỏng — và vì thế tên file bản hỏng
# PHẢI mang sha1 nội dung (xem `_ban_hong`), kẻo hai bản liên tiếp ghi cùng tên trong cùng
# một giây làm SourceFileLoader đọc lại .pyc của bản trước.
_MOD = os.environ.get("TGBOT_MOD") or str(ROOT / "scripts" / "telegram_bot.py")
_spec = importlib.util.spec_from_file_location("tb_duoi_thu", _MOD)
tb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tb)

CA = []


def kiem(ten, dat):
    dat = bool(dat)
    CA.append((ten, dat))
    print(("✓" if dat else "✗") + " " + ten)


def docx_mau(doan):
    d = Document()
    for p in doan:
        d.add_paragraph(p)
    tmp = tempfile.mktemp(suffix=".docx")
    d.save(tmp)
    return tmp


# --- docx_text.trich() ----------------------------------------------------
kiem("trich() file không tồn tại -> rỗng, không crash",
     docx_text.trich("/khong/co/that.docx") == "")

f1 = docx_mau(["Dòng một có dấu: Đà Nẵng", "Dòng hai"])
t1 = docx_text.trich(f1)
kiem("trich() giữ dấu tiếng Việt", "Đà Nẵng" in t1)
kiem("trich() giữ đủ các dòng", "Dòng một" in t1 and "Dòng hai" in t1)

f2 = docx_mau(["a" * 100])
t2 = docx_text.trich(f2, max_chars=10)
kiem("trich() cắt đúng độ dài + có dấu …", len(t2) == 11 and t2.endswith("…"))

f3 = tempfile.mktemp(suffix=".docx")
pathlib.Path(f3).write_text("không phải file zip/docx thật", encoding="utf-8")
kiem("trich() file .docx giả (không phải zip) -> rỗng", docx_text.trich(f3) == "")

# --- telegram_bot.xu_ly_tin_jaylam() — CA PHẢI CHẶN ------------------------
with mock.patch.object(tb, "call") as call_m, \
        mock.patch.object(tb, "tai_file") as tai_m, \
        mock.patch.object(tb, "luu_tin_jaylam") as luu_m:
    tb.xu_ly_tin_jaylam("111", "111", {"from": {"first_name": "Jay Lâm"}},
                         {"file_name": "anh.jpg", "file_id": "abc"})
kiem("xu_ly_tin_jaylam() từ chối file không phải .docx -> KHÔNG tải, KHÔNG lưu",
     not tai_m.called and not luu_m.called and call_m.called
     and ".docx" in call_m.call_args.args[2]["text"])

with mock.patch.object(tb, "call") as call_m, \
        mock.patch.object(tb, "tai_file", return_value=False) as tai_m, \
        mock.patch.object(tb, "luu_tin_jaylam") as luu_m:
    tb.xu_ly_tin_jaylam("111", "111", {"from": {"first_name": "Jay Lâm"}},
                         {"file_name": "tin.docx", "file_id": "abc"})
kiem("xu_ly_tin_jaylam() tải file hỏng -> KHÔNG lưu, có báo lỗi",
     tai_m.called and not luu_m.called and "hỏng" in call_m.call_args.args[2]["text"])

f4 = docx_mau(["Tin thật từ Jay Lâm"])
with mock.patch.object(tb, "call") as call_m, \
        mock.patch.object(tb, "tai_file",
                           side_effect=lambda tok, fid, dich: pathlib.Path(f4).rename(dich)
                           or True) as tai_m, \
        mock.patch.object(tb, "luu_tin_jaylam", return_value=True) as luu_m:
    tb.xu_ly_tin_jaylam("111", "111", {"from": {"first_name": "Jay Lâm"}},
                         {"file_name": "tin.docx", "file_id": "abc"})
kiem("xu_ly_tin_jaylam() luồng bình thường -> lưu đúng nội dung, báo đã nhận",
     luu_m.called and "Jay Lâm" in luu_m.call_args.args[1]
     and "Tin thật" in luu_m.call_args.args[3]
     and "Đã nhận" in call_m.call_args.args[2]["text"])

with mock.patch.object(tb, "call") as call_m, \
        mock.patch.object(tb, "tai_file", return_value=True) as tai_m, \
        mock.patch.object(tb, "luu_tin_jaylam", return_value=False) as luu_m:
    tb.xu_ly_tin_jaylam("111", "111", {"from": {"first_name": "Jay Lâm"}},
                         {"file_name": "rong.docx", "file_id": "abc"})
kiem("xu_ly_tin_jaylam() file rỗng/không đọc được -> không gọi lưu, báo lỗi",
     not luu_m.called and ("rỗng hoặc hỏng" in call_m.call_args.args[2]["text"]))

# --- TRẦN ĐỘ DÀI — ca hồi quy của lỗi cắt câm 30/07/2026 -------------------
# Lỗi thật: file bản tin ngày của Jay Lâm dài 34.525 ký tự bị trần 20.000 xén mất 14.525 ký
# tự và 20 URL, mà tin xác nhận vẫn báo "Đã nhận" — không dấu hiệu nào ở cả hai đầu.
def _chay_voi_file(f, ten_file="tin.docx"):
    """Chạy xu_ly_tin_jaylam với file .docx có sẵn, trả (mock call, mock luu)."""
    with mock.patch.object(tb, "call") as call_m, \
            mock.patch.object(tb, "tai_file",
                              side_effect=lambda tok, fid, dich:
                              pathlib.Path(f).replace(dich) or True), \
            mock.patch.object(tb, "luu_tin_jaylam", return_value=True) as luu_m:
        tb.xu_ly_tin_jaylam("111", "111", {"from": {"first_name": "Jay Lâm"}},
                            {"file_name": ten_file, "file_id": "abc"})
    return call_m, luu_m


# Ca 6 — HỒI QUY: file cỡ thật (34.525 ký tự) phải vào Supabase ĐỦ, không mất chữ nào.
DAI_THAT = 34525
f5 = docx_mau(["x" * DAI_THAT])
call5, luu5 = _chay_voi_file(f5)
kiem(f"file {DAI_THAT} ký tự (cỡ file Jay Lâm gửi thật) -> lưu ĐỦ, không bị cắt",
     luu5.called and len(luu5.call_args.args[3]) >= DAI_THAT
     and "…" not in luu5.call_args.args[3][-3:])

# Ca 7 — PHẢI KÊU: vượt trần thì cắt, nhưng tin xác nhận phải NÓI RA là đã cắt.
f6 = docx_mau(["y" * (tb.JAYLAM_MAX_CHARS + 5000)])
call6, luu6 = _chay_voi_file(f6)
_txt6 = call6.call_args.args[2]["text"] if call6.called else ""
kiem("file vượt trần -> tin xác nhận PHẢI báo bị cắt (không im lặng)",
     luu6.called and ("cắt" in _txt6 or "vượt trần" in _txt6))

# Ca 8 — ĐỐI CHỨNG chống kêu oan: file dưới trần thì tuyệt đối không được nhắc chuyện cắt.
f7 = docx_mau(["z" * 500])
call7, luu7 = _chay_voi_file(f7)
_txt7 = call7.call_args.args[2]["text"] if call7.called else ""
kiem("file dưới trần -> KHÔNG nhắc chuyện cắt (chống kêu oan)",
     luu7.called and "cắt" not in _txt7 and "vượt trần" not in _txt7)

so_dat = sum(1 for _, ok in CA if ok)
print(f"\n{so_dat}/{len(CA)} ca đạt")


# --- --tu-kiem: chứng minh bộ ca trên BẮT ĐƯỢC lỗi ------------------------
BAN_HONG = [
    # (nhãn, chuỗi tìm, chuỗi thay, các ca PHẢI đỏ — khớp theo chuỗi con của tên ca)
    ("trả trần về 20.000 như bản cũ",
     "JAYLAM_MAX_CHARS = 200000", "JAYLAM_MAX_CHARS = 20000",
     ["cỡ file Jay Lâm gửi thật"]),
    # Vẫn cắt, nhưng nuốt lời cảnh báo — đúng hành vi câm của bản cũ. Neo kèm dòng
    # `them = ""` phía trên vì `if bi_cat:` một mình xuất hiện hai lần trong hàm.
    ("cắt trong im lặng (gỡ lời cảnh báo, vẫn cắt)",
     '            them = ""\n            if bi_cat:',
     '            them = ""\n            if False:',
     ["PHẢI báo bị cắt"]),
]


def _tu_kiem():
    import hashlib
    import re
    import subprocess
    goc = (ROOT / "scripts" / "telegram_bot.py").read_text(encoding="utf-8")
    tat_ca_dat = True
    for nhan, tim, thay, phai_do in BAN_HONG:
        if goc.count(tim) != 1:
            print(f"✗ [{nhan}] chuỗi neo khớp {goc.count(tim)} chỗ (phải đúng 1)")
            tat_ca_dat = False
            continue
        noi_dung = goc.replace(tim, thay)
        sha = hashlib.sha1(noi_dung.encode()).hexdigest()[:8]
        hong = ROOT / "scripts" / f"_thu-hong-{os.getpid()}-{sha}-telegram_bot.py"
        try:
            hong.write_text(noi_dung, encoding="utf-8")
            moi = dict(os.environ, TGBOT_MOD=str(hong))
            moi.pop("TU_KIEM", None)
            p = subprocess.run([sys.executable, str(pathlib.Path(__file__).resolve())],
                               capture_output=True, text=True, env=moi)
            do = [re.sub(r"^✗ ", "", d) for d in p.stdout.splitlines()
                  if d.startswith("✗")]
            thieu = [c for c in phai_do if not any(c in d for d in do)]
            if p.returncode == 0 or thieu:
                print(f"✗ [{nhan}] TRƯỢT — ca cần đỏ chưa đỏ: {thieu or 'không ca nào đỏ'}"
                      f" · đỏ thực tế: {do}")
                tat_ca_dat = False
            elif len(do) == len(CA):
                print(f"✗ [{nhan}] TRƯỢT — ĐỎ TOÀN BỘ {len(CA)} ca: phép thay phá hỏng nền "
                      "chứ không gỡ đúng một lớp vá. Sửa lại phép thay.")
                tat_ca_dat = False
            else:
                print(f"✓ [{nhan}] bị bắt — {len(do)} ca đỏ: {do}")
        finally:
            hong.unlink(missing_ok=True)
    print("\n✅ --tu-kiem ĐẠT" if tat_ca_dat else "\n❌ --tu-kiem TRƯỢT")
    return 0 if tat_ca_dat else 1


if "--tu-kiem" in sys.argv:
    sys.exit(_tu_kiem())
sys.exit(0 if so_dat == len(CA) else 1)
