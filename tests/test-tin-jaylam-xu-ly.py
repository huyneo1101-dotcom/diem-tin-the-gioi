#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test cho `scripts/tin_jaylam.py` — bước phiên quét TỐI biến tin Jay Lâm gửi thành TIN CHUẨN.

    python3 tests/test-tin-jaylam-xu-ly.py
    python3 tests/test-tin-jaylam-xu-ly.py --tu-kiem   # chứng minh test BẮT ĐƯỢC lỗi

Đây là một CỔNG (guardrail cho dữ liệu agent viết ra) nên theo mục 17 CLAUDE.md phải có ca
PHẢI CHẶN thật, không chỉ ca cho-qua: một guardrail câm nhìn y hệt guardrail sạch — đầu vào
đúng thì cả hai đều im lặng cho qua.

Không chạm mạng: `subprocess.run` của module bị thay bằng bản giả ghi lại lệnh PATCH.
"""
import contextlib
import datetime
import hashlib
import io
import json
import os
import pathlib
import shutil
import subprocess as SP
import sys
import tempfile
import zoneinfo

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SC = pathlib.Path(os.environ.get("TINJAYLAM_DIR") or (REPO / "scripts"))
sys.path.insert(0, str(SC))

import tin_jaylam as TJ          # noqa: E402

VN = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")
NOW = datetime.datetime(2026, 7, 30, 21, 0, tzinfo=VN)

CA = []


def kiem(ten, dat):
    dat = bool(dat)
    CA.append((ten, dat))
    print(("✓" if dat else "✗") + " " + ten)


def dong(id_, created_at, **kw):
    r = {"id": id_, "ten": "Jay Lâm", "ten_file": f"f{id_}.docx",
         "noi_dung": f"Nội dung tin số {id_}", "created_at": created_at}
    r.update(kw)
    return r


HANG_CHO = [dong(1, "2026-07-30T03:00:00Z"), dong(2, "2026-07-29T03:00:00Z")]

TOM_TAT_OK = ("Hạ viện Mỹ thông qua dự luật ngân sách quốc phòng năm tài khóa 2027 "
              "với tỷ lệ 218-210.")


class GiaMang:
    """Thay `subprocess.run` của module: GET trả `HANG_CHO`, PATCH ghi vào `self.patch`."""

    def __init__(self, rows=None, patch_hong=False):
        self.rows = HANG_CHO if rows is None else rows
        self.patch = []
        self.patch_hong = patch_hong

    def __enter__(self):
        self.goc = TJ.subprocess.run
        self.goc_env = {k: os.environ.get(k) for k in ("SUPABASE_ANON_KEY", "DT_BOT_KEY")}
        os.environ["SUPABASE_ANON_KEY"] = "sb_publishable_test"
        os.environ["DT_BOT_KEY"] = "ma-test"
        rows, patch, hong = self.rows, self.patch, self.patch_hong

        def gia(args, **kw):
            class P:
                returncode = 0
                stdout = ""
                stderr = ""
            if "-X" in args and "PATCH" in args:
                patch.append(args)
                if hong:
                    P.returncode = 22
                return P
            P.stdout = json.dumps(rows, ensure_ascii=False)
            return P

        TJ.subprocess.run = gia
        return self

    def __exit__(self, *a):
        TJ.subprocess.run = self.goc
        for k, v in self.goc_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return False


def chay_ghi(muc, rows=None, patch_hong=False):
    """Trả (mã thoát, stderr, danh sách lệnh PATCH)."""
    fd, tmp = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    pathlib.Path(tmp).write_text(json.dumps(muc, ensure_ascii=False), encoding="utf-8")
    buf_out, buf_err = io.StringIO(), io.StringIO()
    try:
        with GiaMang(rows, patch_hong) as g, contextlib.redirect_stdout(buf_out), \
                contextlib.redirect_stderr(buf_err):
            ma = TJ.ghi(tmp, now=NOW)
        return ma, buf_err.getvalue(), g.patch
    finally:
        pathlib.Path(tmp).unlink(missing_ok=True)


HOP_LE = {"id": 1, "tieu_de": "Hạ viện Mỹ thông qua ngân sách quốc phòng",
          "tom_tat": TOM_TAT_OK, "nguon_ten": "Reuters",
          "nguon_url": "https://reuters.com/world/bai-cu-the-123"}


# ------------------------------------------------ đối chứng: luồng bình thường
ma, err, patch = chay_ghi([HOP_LE])
kiem("[01] mục hợp lệ -> mã 0, có gọi PATCH", ma == 0 and len(patch) == 1)
than = json.loads(patch[0][-1]) if patch else {}
kiem("[02] PATCH ghi đủ 5 trường + da_xu_ly=true",
     than.get("da_xu_ly") is True and than.get("tieu_de") and than.get("tom_tat")
     and than.get("nguon_ten") == "Reuters" and than.get("nguon_url"))
kiem("[03] PATCH nhắm đúng id", any("id=eq.1" in a for a in patch[0]))

# nguon_url RỖNG vẫn cho qua — Jay Lâm tự gửi bài, không truy được gốc thì KHÔNG bỏ tin
ma, err, patch = chay_ghi([dict(HOP_LE, nguon_url="", nguon_ten="Jay Lâm gửi")])
kiem("[04] nguon_url RỖNG -> VẪN cho qua (không bỏ tin Jay Lâm tự gửi)",
     ma == 0 and len(patch) == 1)
kiem("[05] nguon_url rỗng -> ghi None, không ghi chuỗi rỗng",
     json.loads(patch[0][-1]).get("nguon_url") is None)

ma, err, patch = chay_ghi([dict(HOP_LE, la_cnqs=True)])
kiem("[06] la_cnqs=true -> ghi đúng cờ (được nới khung 3 ngày)",
     ma == 0 and json.loads(patch[0][-1]).get("la_cnqs") is True)
ma, err, patch = chay_ghi([HOP_LE])
kiem("[07] không khai la_cnqs -> mặc định false, không phải None",
     json.loads(patch[0][-1]).get("la_cnqs") is False)

ma, err, patch = chay_ghi([])
kiem("[08] mảng rỗng -> mã 0, không gọi PATCH", ma == 0 and patch == [])

# ------------------------------------------------------------ ca PHẢI CHẶN
ma, err, patch = chay_ghi([dict(HOP_LE, id=999)])
kiem("[09] PHẢI CHẶN id không nằm trong hàng chờ (đã gộp/đã xử lý/bịa)",
     ma == 1 and patch == [] and "không nằm trong hàng chờ" in err)

ma, err, patch = chay_ghi([HOP_LE, dict(HOP_LE, tieu_de="Tiêu đề khác cho cùng một id")])
kiem("[10] PHẢI CHẶN cùng một id xuất hiện hai lần",
     ma == 1 and patch == [] and "hai lần" in err)

ma, err, patch = chay_ghi([dict(HOP_LE, tieu_de="Ngắn")])
kiem("[11] PHẢI CHẶN tieu_de quá ngắn", ma == 1 and patch == [] and "tieu_de" in err)

ma, err, patch = chay_ghi([dict(HOP_LE, tieu_de="X" * 201)])
kiem("[12] PHẢI CHẶN tieu_de quá dài", ma == 1 and patch == [] and "tieu_de" in err)

ma, err, patch = chay_ghi([dict(HOP_LE, tom_tat="Quá ngắn.")])
kiem("[13] PHẢI CHẶN tom_tat cụt (dưới ngưỡng)",
     ma == 1 and patch == [] and "tom_tat" in err)

ma, err, patch = chay_ghi([dict(HOP_LE, nguon_ten="")])
kiem("[14] PHẢI CHẶN thiếu nguon_ten", ma == 1 and patch == [] and "nguon_ten" in err)

ma, err, patch = chay_ghi([dict(HOP_LE, nguon_url="https://reuters.com/")])
kiem("[15] PHẢI CHẶN nguon_url chỉ là trang chủ",
     ma == 1 and patch == [] and "trang chủ" in err)

ma, err, patch = chay_ghi([dict(HOP_LE, nguon_url="https://bbc.com/news/live-updates-abc")])
kiem("[16] PHẢI CHẶN nguon_url là live-blog/tổng hợp",
     ma == 1 and patch == [] and "live-blog" in err)

ma, err, patch = chay_ghi([dict(HOP_LE, la_cnqs="co")])
kiem("[17] PHẢI CHẶN la_cnqs không phải true/false",
     ma == 1 and patch == [] and "la_cnqs" in err)

ma, err, patch = chay_ghi([dict(HOP_LE, id="mot")])
kiem("[18] PHẢI CHẶN id không phải số", ma == 1 and patch == [] and "`id`" in err)

ma, err, patch = chay_ghi(["chuỗi trần chứ không phải object"])
kiem("[19] PHẢI CHẶN mục không phải object", ma == 1 and patch == [])

ma, err, patch = chay_ghi([HOP_LE], rows=[])
kiem("[20] PHẢI CHẶN khi hàng chờ rỗng (không ghi mù)",
     ma == 1 and patch == [] and "Hàng chờ rỗng" in err)

ma, err, patch = chay_ghi([HOP_LE], patch_hong=True)
kiem("[21] PHẢI KÊU khi PATCH hỏng -> mã 1, không báo xong oan",
     ma == 1 and "ghi hỏng" in err)

# một mục sai làm CẢ LÔ bị chặn — không ghi nửa vời rồi để agent đoán phần nào đã vào
ma, err, patch = chay_ghi([HOP_LE, dict(HOP_LE, id=2, tom_tat="cụt")])
kiem("[22] PHẢI CHẶN cả lô khi một mục sai (không ghi nửa vời)",
     ma == 1 and patch == [])

# --------------------------------------------- khung ngày ở bước LIỆT KÊ
kiem("[23] qua_han mặc định dùng khung RỘNG NHẤT (3 ngày, cho CNQS)",
     TJ.qua_han({"created_at": "2026-07-27T03:00:00Z"}, NOW) is False)
kiem("[24] qua_han: 4 ngày trước -> True",
     TJ.qua_han({"created_at": "2026-07-26T03:00:00Z"}, NOW) is True)
kiem("[25] qua_han: created_at hỏng -> True (phía KÊU)",
     TJ.qua_han({"created_at": "sai"}, NOW) is True)
kiem("[26] qua_han: truyền gioi_han hẹp thì siết đúng",
     TJ.qua_han({"created_at": "2026-07-28T03:00:00Z"}, NOW, gioi_han=1) is True)
kiem("[27] hằng số khớp add_news/harvest (1 và 3)",
     (TJ.MAX_AGE_DAYS, TJ.MAX_AGE_DAYS_CNQS) == (1, 3))

with GiaMang([dong(1, "2026-07-30T03:00:00Z"),
              dong(2, "2026-07-27T03:00:00Z"),
              dong(3, "2026-07-25T03:00:00Z")]):
    b_out, b_err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(b_out), contextlib.redirect_stderr(b_err):
        ma_lk = TJ.in_hang_cho(NOW)
    lk = b_out.getvalue()
kiem("[28] --liet-ke giữ tin 3 ngày (ứng viên CNQS), bỏ tin 5 ngày",
     ma_lk == 0 and "id=1" in lk and "Nội dung tin số 2" in lk
     and "Nội dung tin số 3" not in lk)
kiem("[29] --liet-ke nêu rõ cách khai la_cnqs để agent biết", "la_cnqs" in lk)

with GiaMang([]):
    b_out = io.StringIO()
    with contextlib.redirect_stdout(b_out), contextlib.redirect_stderr(io.StringIO()):
        ma_rong = TJ.in_hang_cho(NOW)
kiem("[30] --liet-ke hàng chờ rỗng -> mã 10 (quy ước 'không có gì làm')", ma_rong == 10)

# ---------------------------------------------------------------- TỰ KIỂM
BAN_HONG = [
    ("bỏ phép kiểm id nằm trong hàng chờ",
     "    if mid not in cho_phep_ids:\n"
     '        raise ValueError(f"{ctx}: không nằm trong hàng chờ (đã xử lý, đã gộp, '
     'hoặc id bịa)")',
     "    pass"),
    ("bỏ phép kiểm id trùng trong cùng file",
     "    if mid in da_thay:\n"
     '        raise ValueError(f"{ctx}: xuất hiện hai lần trong file")',
     "    pass"),
    ("bỏ phép kiểm độ dài tieu_de",
     "    if not TIEU_DE_MIN <= len(tieu_de) <= TIEU_DE_MAX:",
     "    if False:"),
    ("bỏ phép kiểm tom_tat cụt",
     "    if len(tom_tat) < TOM_TAT_MIN:",
     "    if False:"),
    ("bỏ phép kiểm nguon_ten",
     "    if not nguon_ten:",
     "    if False:"),
    ("bỏ phép kiểm chất lượng URL",
     "    if nguon_url:\n        check_url_quality(nguon_url, ctx)",
     "    if False:\n        check_url_quality(nguon_url, ctx)"),
    ("bỏ phép kiểm kiểu của la_cnqs",
     "    if not isinstance(la_cnqs, bool):",
     "    if False:"),
    ("cho ghi mù khi hàng chờ rỗng",
     "    if not cho_phep:\n"
     '        print("Hàng chờ rỗng (hoặc không đọc được) — không ghi gì.", file=sys.stderr)\n'
     "        return 1",
     "    if not cho_phep:\n"
     "        cho_phep = {m.get('id') for m in data if isinstance(m, dict)}"),
    ("nuốt lỗi PATCH -> báo xong oan",
     "    if hong:\n"
     '        print(f"CHẶN: ghi hỏng {len(hong)}/{len(sach)} dòng (id: {hong}).", '
     "file=sys.stderr)\n"
     "        return 1",
     "    if hong:\n        pass"),
    ("qua_han mặc định siết về khung HẸP -> bỏ mất ứng viên CNQS",
     "    gioi_han = MAX_AGE_DAYS_CNQS if gioi_han is None else gioi_han",
     "    gioi_han = MAX_AGE_DAYS if gioi_han is None else gioi_han"),
    ("qua_han fail-open khi created_at hỏng",
     "    except (ValueError, AttributeError, TypeError):\n        return True",
     "    except (ValueError, AttributeError, TypeError):\n        return False"),
    ("ghi nửa vời: mục sai chỉ bị bỏ qua thay vì chặn cả lô",
     "        except ValueError as e:\n"
     '            print(f"CHẶN: {e}", file=sys.stderr)\n'
     "            return 1",
     "        except ValueError as e:\n"
     '            print(f"CHẶN: {e}", file=sys.stderr)\n'
     "            continue"),
]

KHAI_DO = {
    "bỏ phép kiểm id nằm trong hàng chờ": ["09"],
    "bỏ phép kiểm id trùng trong cùng file": ["10"],
    "bỏ phép kiểm độ dài tieu_de": ["11", "12"],
    "bỏ phép kiểm tom_tat cụt": ["13", "22"],
    "bỏ phép kiểm nguon_ten": ["14"],
    "bỏ phép kiểm chất lượng URL": ["15", "16"],
    "bỏ phép kiểm kiểu của la_cnqs": ["17"],
    "cho ghi mù khi hàng chờ rỗng": ["20"],
    "nuốt lỗi PATCH -> báo xong oan": ["21"],
    "qua_han mặc định siết về khung HẸP -> bỏ mất ứng viên CNQS": ["23", "28"],
    "qua_han fail-open khi created_at hỏng": ["25"],
    "ghi nửa vời: mục sai chỉ bị bỏ qua thay vì chặn cả lô": ["22"],
}


def _so_ca(ten):
    return ten[1:3] if ten.startswith("[") else ""


def tu_kiem():
    goc = (SC / "tin_jaylam.py").read_text(encoding="utf-8")
    tong, trot = 0, []
    for ten, tim, thay in BAN_HONG:
        tong += 1
        if goc.count(tim) != 1:
            trot.append(f"{ten}: chuỗi neo khớp {goc.count(tim)} chỗ (phải đúng 1)")
            continue
        hong = goc.replace(tim, thay)
        sha = hashlib.sha1(hong.encode("utf-8")).hexdigest()[:8]
        d = pathlib.Path(tempfile.mkdtemp(prefix=f"tj-hong-{os.getpid()}-{sha}-"))
        try:
            for f in SC.glob("*.py"):
                shutil.copy2(f, d / f.name)
            (d / "tin_jaylam.py").write_text(hong, encoding="utf-8")
            env = dict(os.environ, TINJAYLAM_DIR=str(d))
            p = SP.run([sys.executable, str(pathlib.Path(__file__).resolve())],
                       capture_output=True, text=True, env=env, timeout=300)
            do = {_so_ca(l[2:]) for l in p.stdout.splitlines() if l.startswith("✗ ")}
            can = set(KHAI_DO.get(ten, []))
            tong_ca = len([l for l in p.stdout.splitlines() if l[:1] in ("✓", "✗")])
            if p.returncode == 0:
                trot.append(f"{ten}: bộ test VẪN XANH -> không bắt được lỗi")
            elif tong_ca and len(do) >= tong_ca:
                trot.append(f"{ten}: ĐỎ TOÀN BỘ ca -> phép thay phá cú pháp, không gỡ lớp vá")
            elif not can & do:
                trot.append(f"{ten}: ca cần đỏ {sorted(can)} vẫn xanh; đỏ thực tế {sorted(do)}")
            else:
                print(f"  ✓ {ten}: bắt được (ca đỏ {sorted(do)})")
        finally:
            shutil.rmtree(d, ignore_errors=True)
    print()
    if trot:
        print(f"TRƯỢT {len(trot)}/{tong} bản hỏng:")
        for t in trot:
            print("  - " + t)
        return 1
    print(f"✅ {tong}/{tong} bản hỏng đều bị bộ test bắt.")
    return 0


so_dat = sum(1 for _, ok in CA if ok)
print(f"\n{so_dat}/{len(CA)} ca đạt")
if "--tu-kiem" in sys.argv:
    if so_dat != len(CA):
        print("Bản THẬT đã đỏ — sửa xong hãy chạy --tu-kiem.")
        sys.exit(1)
    print("\n=== TỰ KIỂM: dựng bản tin_jaylam.py đã gỡ lớp bảo vệ ===")
    sys.exit(tu_kiem())
sys.exit(0 if so_dat == len(CA) else 1)
