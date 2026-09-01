#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test BẢN SÁNG GỘP TIN CA TỐI HÔM QUA (Huy chốt 26/08/2026).

    python3 tests/test-gop-tin-ca-toi.py
    python3 tests/test-gop-tin-ca-toi.py --tu-kiem   # chứng minh test BẮT ĐƯỢC lỗi

Nguyên văn chỉ thị: *"từ giờ bản tin 4h sáng hãy gộp cả tin quét được lúc 9h tối vào, nhớ
đối chiếu với cả file Jay Lâm gửi để chống trùng lặp"*.

Cơ chế gây vấp mà bộ này canh — cả bốn đều HỎNG CÂM, file .docx vẫn ra đời đủ mục:
  (1) tin ca tối rơi khỏi bản sáng vì `pick_items` lấy HỢP của (mới so commit cha) và
      (`_addedDate == generatedAt`): sáng nay `generatedAt` là ngày MỚI, còn commit cha lại
      chính là commit của lô tối qua — tin tối qua trượt cả hai vế;
  (2) gộp nhầm sang bản TỐI thì bản tối lặp lại nguyên tin của hôm qua;
  (3) không trừ tin đã gửi ở ca SÁNG hôm qua thì sáng nào cũng đọc lại bản sáng hôm trước;
  (4) gộp SAU bộ lọc Jay Lâm thì đúng nhóm tin vừa gộp không được đối chiếu — mà file Jay
      Lâm thường tới SAU bản tin tối (đo 25/08/2026: bản tối gửi ~22:10, file tới 23:29),
      tức nhóm tin này là nhóm CẦN lọc nhất.

Yêu cầu `pip3 install python-docx`.
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
GS = pathlib.Path(os.environ.get("MAKEDOCX_DIR") or (REPO / ".github" / "scripts"))
sys.path.insert(0, str(GS))

import make_docx as MD          # noqa: E402
from docx import Document       # noqa: E402

VN = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")
MD.prev_data = lambda: None     # bỏ phụ thuộc lịch sử git thật (xem test-so-da-gui.py)
MD._url_ca_sang = lambda now: set()      # bản tối: tách khỏi sổ đã gửi

SANG = datetime.datetime(2026, 8, 26, 4, 0, tzinfo=VN)     # bản 04h
TOI = datetime.datetime(2026, 8, 26, 21, 0, tzinfo=VN)     # bản tối cùng ngày

HOM_NAY, HOM_QUA, HOM_KIA = "2026-08-26", "2026-08-25", "2026-08-24"

U_MOI = "https://reuters.com/tin-quet-sang-nay"
U_TOI_US = "https://thehill.com/tin-ca-toi-hom-qua"
U_TOI_WORLD = "https://manilatimes.net/tuan-tra-co-may-toi-qua"
U_TOI_EV = "https://dvidshub.net/predator-run-toi-qua"
U_SANG_HQ = "https://apnews.com/tin-ban-sang-hom-qua"
U_CU = "https://npr.org/tin-hom-kia"


def _tin(url, ngay, tieu_de, tom_tat):
    return {"date": ngay, "_addedDate": ngay, "category": "Chính trị",
            "title": tieu_de, "summary": tom_tat, "sourceUrl": url}


DATA_GIA = {
    "generatedAt": HOM_NAY,
    "usNews": [
        _tin(U_MOI, HOM_NAY, "Tin quét sáng nay", "Phiên điều trần ngân sách sáng nay."),
        _tin(U_TOI_US, HOM_QUA, "Tin ca tối hôm qua", "Thượng viện bỏ phiếu tối qua."),
        _tin(U_SANG_HQ, HOM_QUA, "Tin bản sáng hôm qua", "Toà bác đơn kiện sáng hôm qua."),
        _tin(U_CU, HOM_KIA, "Tin hôm kia", "Bộ Tài chính công bố hôm kia."),
    ],
    "worldNews": [
        _tin(U_TOI_WORLD, HOM_QUA, "Tuần tra Bãi Cỏ Mây",
             "Tiếp tế Bãi Cỏ Mây, tàu Trung Quốc bám theo."),
    ],
    "exercises": [{"name": "Predator's Run 2026", "items": [
        {"date": HOM_QUA, "_addedDate": HOM_QUA, "title": "Predator's Run bắn đạn thật",
         "summary": "Bài bắn đạn thật tại Townsville.", "sourceUrl": U_TOI_EV}]}],
}

CA = []


def kiem(ten, dat):
    CA.append((ten, bool(dat)))
    print(("✓" if dat else "✗") + " " + ten)


class ThuMucGia:
    """cwd tạm mang index.html giả + sổ trùng Jay Lâm giả — `MD.SO_TRUNG_JAYLAM` là đường
    dẫn TƯƠNG ĐỐI, đúng như production (workflow chạy từ gốc repo)."""

    def __init__(self, so_jl=None, data=None):
        self.so_jl = so_jl
        self.data = data if data is not None else DATA_GIA

    def __enter__(self):
        self.cu = os.getcwd()
        self.d = pathlib.Path(tempfile.mkdtemp(prefix="gop-ca-toi-"))
        (self.d / "index.html").write_text(
            "<html><script>var DATA = " + json.dumps(self.data, ensure_ascii=False)
            + ";</script></html>", encoding="utf-8")
        if self.so_jl is not None:
            (self.d / "logs").mkdir(exist_ok=True)
            (self.d / "logs" / "trung-jaylam.json").write_text(
                json.dumps(self.so_jl, ensure_ascii=False), encoding="utf-8")
        os.chdir(self.d)
        return self.d

    def __exit__(self, *a):
        os.chdir(self.cu)
        shutil.rmtree(self.d, ignore_errors=True)
        return False


def chay(now=SANG, da_gui_sang=(), so_jl=None, data=None):
    """Chạy MD.main(). `da_gui_sang` = tập URL sổ khai đã gửi ở ca SÁNG hôm qua.
    Trả (toàn văn .docx, stderr)."""
    goc = MD._doc_url_buoi
    MD._doc_url_buoi = lambda buoi, ngay: set(da_gui_sang)
    buf_out, buf_err = io.StringIO(), io.StringIO()
    try:
        with ThuMucGia(so_jl, data), contextlib.redirect_stdout(buf_out), \
                contextlib.redirect_stderr(buf_err):
            MD.main(now=now)
    finally:
        MD._doc_url_buoi = goc
    out, err = buf_out.getvalue(), buf_err.getvalue()
    dong = [l for l in out.splitlines() if l.startswith("DOCX=")]
    path = dong[-1][len("DOCX="):].strip() if dong else ""
    van = "\n".join(p.text for p in Document(path).paragraphs) if path else ""
    return van, err


def so_dong_jl(url):
    return {"url": url, "tieu_de": "Tin của mình trùng file Jay Lâm",
            "trung_voi": "Mảnh tương ứng bên file Jay", "id_jay": 34, "ngay": HOM_QUA}


# ---------- (A) PHẢI GỘP ----------
van, err = chay()
kiem("[01] bản SÁNG: tin ca TỐI hôm qua được gộp vào (usNews)",
     "Thượng viện bỏ phiếu tối qua" in van)
kiem("[02] bản SÁNG vẫn giữ tin quét sáng nay", "điều trần ngân sách sáng nay" in van)
kiem("[03] gộp phủ mục worldNews", "Tiếp tế Bãi Cỏ Mây" in van)
kiem("[04] gộp phủ mục events (tập trận)", "bắn đạn thật tại Townsville" in van)
kiem("[05] tin gộp thêm phải được KÊU ra stderr (xoá/thêm tin đều phải soi ngược được)",
     "Ca tối" in err and "gộp thêm" in err)

# ---------- (B) PHẢI CHẶN ----------
van, err = chay(now=TOI)
kiem("[06] BẢN TỐI: KHÔNG gộp tin hôm qua (tin đó đã đi trong bản tối hôm qua)",
     "Thượng viện bỏ phiếu tối qua" not in van)

van, err = chay(da_gui_sang={U_SANG_HQ})
kiem("[07] tin ĐÃ GỬI ở ca SÁNG hôm qua -> KHÔNG gộp lại (không đọc hai buổi sáng liền)",
     "Toà bác đơn kiện sáng hôm qua" not in van
     and "Thượng viện bỏ phiếu tối qua" in van)

van, err = chay()
kiem("[08] tin HÔM KIA -> không gộp (chỉ gộp đúng ca tối hôm qua)",
     "Bộ Tài chính công bố hôm kia" not in van)

# Ca then chốt của chỉ thị 26/08: nhóm tin gộp thêm PHẢI đi qua bộ lọc Jay Lâm, vì file Jay
# Lâm thường tới SAU bản tin tối nên chính nhóm này chưa từng được đối chiếu.
van, err = chay(so_jl=[so_dong_jl(U_TOI_US)])
kiem("[09] tin gộp thêm mà TRÙNG file Jay Lâm -> bị bỏ khỏi bản sáng",
     "Thượng viện bỏ phiếu tối qua" not in van
     and "điều trần ngân sách sáng nay" in van)
kiem("[10] tin gộp thêm bị bộ lọc Jay Lâm bỏ -> có dòng kêu",
     "Bộ lọc Jay Lâm" in err)

van, err = chay(so_jl=[so_dong_jl(U_TOI_EV)])
kiem("[11] lọc Jay Lâm phủ cả tin tập trận gộp thêm",
     "bắn đạn thật tại Townsville" not in van and "Tiếp tế Bãi Cỏ Mây" in van)

# ---------- (C) CHỐNG GỘP OAN / FAIL-OPEN ----------
van, err = chay(da_gui_sang={U_TOI_US})
kiem("[12] chỉ trừ theo dòng `sang` — dòng khai đúng URL ca tối thì tin đó không gộp",
     "Thượng viện bỏ phiếu tối qua" not in van)


def _no_so_da_gui(buoi, ngay):
    raise OSError("sổ đã gửi không đọc được")


loi_ngoai = None
try:
    import so_da_gui                                  # noqa: E402
    goc_url = so_da_gui.url_da_gui_buoi
    so_da_gui.url_da_gui_buoi = _no_so_da_gui
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        tap = MD._doc_url_buoi("sang", HOM_QUA)
    so_da_gui.url_da_gui_buoi = goc_url
except Exception as e:                                # noqa: BLE001
    tap, buf, loi_ngoai = None, io.StringIO(), e
kiem("[13] sổ đã gửi HỎNG -> trả tập rỗng, KHÔNG ném lỗi (fail về phía GỘP DƯ, không mất tin)",
     loi_ngoai is None and tap == set())
kiem("[14] sổ đã gửi hỏng -> vẫn phải KÊU", "không đọc được sổ" in buf.getvalue().lower())

# Tin thiếu `sourceUrl` (hay gặp ở mục tập trận): khoá nhận dạng không được gộp chúng làm một.
DATA_KHONG_URL = json.loads(json.dumps(DATA_GIA))
DATA_KHONG_URL["usNews"] = [
    _tin(U_MOI, HOM_NAY, "Tin quét sáng nay", "Phiên điều trần ngân sách sáng nay."),
    dict(_tin("", HOM_QUA, "Tin tối qua thiếu link A",
              "Hải quân Mỹ công bố tên lửa tầm xa mới tối qua."), sourceUrl=""),
    dict(_tin("", HOM_QUA, "Tin tối qua thiếu link B",
              "Lục quân Mỹ thử xe tự hành chống drone tối qua."), sourceUrl=""),
]
van, err = chay(data=DATA_KHONG_URL)
kiem("[15] hai tin ca tối THIẾU LINK -> gộp đủ CẢ HAI, không nuốt mất tin",
     "tên lửa tầm xa mới tối qua" in van and "xe tự hành chống drone tối qua" in van)

# Ca 18 là ca DUY NHẤT bắt được khoá nhận dạng rỗng: chỉ khi tin SÁNG NAY cũng thiếu link
# thì khoá "" mới đã nằm sẵn trong tập đã-có, khiến tin ca tối thiếu link bị coi là trùng rồi
# rơi khỏi bản tin. Hai tin ca tối thiếu link (ca 15) không đủ để lộ lỗi này.
DATA_CA_HAI_KHONG_URL = json.loads(json.dumps(DATA_GIA))
DATA_CA_HAI_KHONG_URL["usNews"] = [
    dict(_tin("", HOM_NAY, "Tin sáng nay thiếu link",
              "Bộ Chiến tranh công bố ngân sách sáng nay."), sourceUrl=""),
    dict(_tin("", HOM_QUA, "Tin tối qua thiếu link",
              "Lục quân Mỹ thử xe tự hành chống drone tối qua."), sourceUrl=""),
]
van, err = chay(data=DATA_CA_HAI_KHONG_URL)
kiem("[18] tin SÁNG NAY thiếu link không được nuốt mất tin CA TỐI cũng thiếu link",
     "ngân sách sáng nay" in van and "xe tự hành chống drone tối qua" in van)

van, err = chay()
# ⚠️ Neo vào GIỮA câu, không neo chữ đầu: từ form 01/09/2026 mỗi tin mở bằng
# "Ngày d.M.yyyy, " nên chữ đầu của tóm tắt bị hạ nếu là từ chức năng
# (`make_docx.TU_HA_CHU_DAU`) — "Phiên điều trần…" ra "phiên điều trần…". Neo cả chữ đầu
# thì ca này đỏ vì CHÍNH TẢ chứ không vì tin lặp, đúng lối làm cổng kiểm mất răng.
kiem("[16] không tin nào lặp hai lần trong file",
     van.count("Thượng viện bỏ phiếu tối qua") == 1
     and van.count("điều trần ngân sách sáng nay") == 1)

DATA_RONG = {"generatedAt": HOM_NAY, "usNews": [], "worldNews": [], "exercises": []}
van, err = chay(data=DATA_RONG)
kiem("[17] kho rỗng -> không dựng file, không ném lỗi", van == "")


# ---------- TỰ KIỂM: dựng bản make_docx.py đã gỡ lớp vá ----------
BAN_HONG = [
    ("gỡ hẳn phép gộp (bản sáng lại mất tin ca tối)",
     "    if la_buoi_toi(now):\n        return items\n    lst = event_items(cur) if kind",
     "    return items\n    lst = event_items(cur) if kind"),
    ("gộp cả bản TỐI (bỏ rào buổi)",
     "    if la_buoi_toi(now):\n        return items\n    lst = event_items(cur) if kind",
     "    if False:\n        return items\n    lst = event_items(cur) if kind"),
    ("không trừ tin đã gửi ca sáng hôm qua",
     'da_gui_sang = _doc_url_buoi("sang", hom_qua)',
     "da_gui_sang = set()"),
    ("gộp SAU bộ lọc Jay Lâm (nhóm gộp thêm không được đối chiếu)",
     '    us = gop_tin_ca_toi(us, cur, "usNews", now)',
     '    _ = gop_tin_ca_toi(us, cur, "usNews", now)'),
    ("nới khung ngày: gộp mọi tin cũ, không chỉ hôm qua",
     '== hom_qua]',
     '<= hom_qua]'),
    ("khoá tin rỗng khi thiếu link (nuốt mất tin ca tối không có URL)",
     '    return url or ("T:" + str(it.get("title") or "") + "|" + str(it.get("summary") or "")[:60])',
     "    return url"),
    ("bỏ dòng kêu khi gộp",
     '    print(f"Ca tối {hom_qua}: gộp thêm {len(them)} tin vào bản sáng: "',
     '    print(f"" or ("Ca toi da gop" and "")[:0] or "" if False else "", end="") or print(f"x{hom_qua}{len(them)}: "'),
]
KHAI_DO = {
    "gỡ hẳn phép gộp (bản sáng lại mất tin ca tối)": [1, 3, 4],
    "gộp cả bản TỐI (bỏ rào buổi)": [6],
    "không trừ tin đã gửi ca sáng hôm qua": [7, 12],
    "gộp SAU bộ lọc Jay Lâm (nhóm gộp thêm không được đối chiếu)": [1],
    "nới khung ngày: gộp mọi tin cũ, không chỉ hôm qua": [8],
    "khoá tin rỗng khi thiếu link (nuốt mất tin ca tối không có URL)": [18],
    "bỏ dòng kêu khi gộp": [5],
}


def _so_ca(dong):
    try:
        return int(dong.split("]")[0].lstrip("["))
    except Exception:                                  # noqa: BLE001
        return -1


def tu_kiem():
    """Mỗi bản hỏng nằm trong thư mục copy riêng mang PID + sha1 NỘI DUNG: tên cố định làm
    hai phiên chạy chồng xoá bản hỏng của nhau, và cùng đường dẫn làm `__pycache__` phát lại
    bytecode của bản hỏng trước (mục 17 + 23 CLAUDE.md)."""
    goc = (GS / "make_docx.py").read_text(encoding="utf-8")
    tong, trot = 0, []
    for ten, tim, thay in BAN_HONG:
        tong += 1
        if goc.count(tim) != 1:
            trot.append(f"{ten}: chuỗi neo khớp {goc.count(tim)} chỗ (phải đúng 1)")
            continue
        hong = goc.replace(tim, thay)
        sha = hashlib.sha1(hong.encode("utf-8")).hexdigest()[:8]
        d = pathlib.Path(tempfile.mkdtemp(prefix=f"gop-hong-{os.getpid()}-{sha}-"))
        try:
            # PHẢI giữ cấu trúc `<repo>/.github/scripts` + `<repo>/scripts`: make_docx.py suy
            # đường tới `scripts/` từ vị trí chính nó để `from topics import ...`.
            gs = d / ".github" / "scripts"
            gs.mkdir(parents=True)
            (d / "scripts").mkdir()
            for f in GS.glob("*.py"):
                shutil.copy2(f, gs / f.name)
            for f in (REPO / "scripts").glob("*.py"):
                shutil.copy2(f, d / "scripts" / f.name)
            (gs / "make_docx.py").write_text(hong, encoding="utf-8")
            env = dict(os.environ, MAKEDOCX_DIR=str(gs))
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
    print("\n=== TỰ KIỂM: dựng bản make_docx.py đã gỡ lớp bảo vệ ===")
    sys.exit(tu_kiem())
sys.exit(0 if so_dat == len(CA) else 1)
