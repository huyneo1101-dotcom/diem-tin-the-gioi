#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test BỘ LỌC Jay Lâm trong file .docx bản tin (Huy đảo nguyên tắc 01/08/2026).

    python3 tests/test-tin-jaylam-trong-docx.py
    python3 tests/test-tin-jaylam-trong-docx.py --tu-kiem   # chứng minh test BẮT ĐƯỢC lỗi

Bộ này TRƯỚC 01/08/2026 có 59 ca đo mục 5 "Tin Jay Lâm gửi" — mục đó đã bỏ hẳn cùng ngày:
*"file của Jay Lâm gửi chỉ là để so sánh xem có tin nào mày quét được mà bị trùng với tin
trong file đó không thôi"*. Nay `make_docx.py` chỉ còn một việc liên quan tới Jay Lâm: đọc sổ
`logs/trung-jaylam.json` rồi BỎ tin CỦA MÌNH mà anh ta đã có.

Bốn thứ dễ hỏng câm mà bộ này canh (mục 17 CLAUDE.md — hỏng thì im lặng cho qua):
  (1) phép lọc phải phủ CẢ BA mục (usNews · worldNews · events) — bỏ sót một mục thì file vẫn
      ra đời đủ, chỉ lặp tin ở đúng mục đó. Đây là đúng cơ chế đã gây lỗi 01/08 với
      `loc_bo_tin_ca_sang` (phủ 3 mục quét, quên mục 5);
  (2) áp CẢ HAI BUỔI — bản sáng cũng phải lọc, vì file Jay gửi tối qua còn hiệu lực 3 ngày;
  (3) sổ thiếu/hỏng phải FAIL VỀ PHÍA KHÔNG LỌC **nhưng CÓ TIẾNG** — im lặng thì bước
      `--ghi-loai` bị bỏ nhiều phiên liền mà không phân biệt được với "hôm nay không trùng";
  (4) tin bị bỏ phải được KÊU ra kèm tiêu đề — xoá tin là mất nội dung, phải soi ngược được.

Không chạm mạng: `make_docx.py` từ 01/08/2026 KHÔNG còn đường đọc Supabase nào (ca [12] canh).
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
MD.prev_data = lambda: None     # xem test-so-da-gui.py — bỏ phụ thuộc lịch sử git thật
MD._url_ca_sang = lambda now: set()   # tách khỏi sổ đã gửi; ca [13] tự bật lại

SANG = datetime.datetime(2026, 8, 2, 6, 0, tzinfo=VN)
TOI = datetime.datetime(2026, 8, 2, 21, 0, tzinfo=VN)

U_US = "https://thehill.com/dieu-tran-uy-ban"
U_WORLD = "https://reuters.com/tuan-tra-scarborough"
U_EV = "https://dvidshub.net/predator-run-ban-dan-that"

DATA_GIA = {
    "generatedAt": "2026-08-02",
    "usNews": [{"date": "2026-08-02", "_addedDate": "2026-08-02", "category": "Chính trị",
                "title": "Uỷ ban Quân vụ điều trần về ngân sách",
                # ⚠️ File .docx in `summary`, KHÔNG in `title` (xem `item_body`). Mọi phép so
                # "tin có trong file không" phải nhắm vào chuỗi của `summary`; nhắm vào
                # `title` thì mọi ca đều đỏ dù phép lọc chạy đúng — đã vấp thật khi dựng bộ
                # này. `title` chỉ dùng cho dòng KÊU ở stderr (ca [17]).
                "summary": "Phiên điều trần về ngân sách quốc phòng.", "sourceUrl": U_US}],
    "worldNews": [{"date": "2026-08-02", "_addedDate": "2026-08-02", "category": "Chính trị",
                   "title": "Philippines tuần tra Scarborough",
                   "summary": "Tuần tra chung tại bãi cạn Scarborough.",
                   "sourceUrl": U_WORLD}],
    "exercises": [{"name": "Predator's Run 2026", "items": [
        {"date": "2026-08-02", "_addedDate": "2026-08-02",
         "title": "Predator's Run bắn đạn thật",
         "summary": "Bài bắn đạn thật tại Townsville.", "sourceUrl": U_EV}]}],
}

CA = []


def kiem(ten, dat):
    dat = bool(dat)
    CA.append((ten, dat))
    print(("✓" if dat else "✗") + " " + ten)


class ThuMucGia:
    """Ghim cwd vào thư mục tạm có index.html giả + sổ loại giả, dọn sạch khi thoát.

    cwd quan trọng: `MD.SO_TRUNG_JAYLAM` là đường dẫn TƯƠNG ĐỐI (`logs/trung-jaylam.json`),
    đúng như production — workflow chạy `python3 .github/scripts/make_docx.py` từ gốc repo.
    """

    def __init__(self, so=None, data=None):
        self.so = so
        self.data = data if data is not None else DATA_GIA

    def __enter__(self):
        self.cu = os.getcwd()
        self.d = pathlib.Path(tempfile.mkdtemp(prefix="jaylam-loc-"))
        (self.d / "index.html").write_text(
            "<html><script>var DATA = " + json.dumps(self.data, ensure_ascii=False)
            + ";</script></html>", encoding="utf-8")
        if self.so is not None:
            (self.d / "logs").mkdir(exist_ok=True)
            noi = self.so if isinstance(self.so, str) else json.dumps(
                self.so, ensure_ascii=False)
            (self.d / "logs" / "trung-jaylam.json").write_text(noi, encoding="utf-8")
        os.chdir(self.d)
        return self.d

    def __exit__(self, *a):
        os.chdir(self.cu)
        shutil.rmtree(self.d, ignore_errors=True)
        return False


def chay(now=TOI, so=None, data=None):
    """Chạy MD.main() với sổ loại `so` (list -> JSON, str -> ghi nguyên văn, None -> không
    có file). Trả (toàn văn .docx, stderr)."""
    buf_out, buf_err = io.StringIO(), io.StringIO()
    with ThuMucGia(so, data), contextlib.redirect_stdout(buf_out), \
            contextlib.redirect_stderr(buf_err):
        MD.main(now=now)
    out, err = buf_out.getvalue(), buf_err.getvalue()
    dong = [l for l in out.splitlines() if l.startswith("DOCX=")]
    path = dong[-1][len("DOCX="):].strip() if dong else ""
    full = "\n".join(p.text for p in Document(path).paragraphs) if path else ""
    return full, err


def chay_bat_loi(**kw):
    """Như `chay()` nhưng KHÔNG để ngoại lệ thoát ra — trả `(văn, err, loi)`.

    ⚠️ Bắt buộc cho ca đo nhánh fail-open. Nếu ca đó gọi thẳng `chay()` thì một bản hỏng
    kiểu `raise` sẽ giết cả bộ test ngay tại ca ấy: các ca sau không kịp in, `--tu-kiem`
    thấy 0 dòng ✗ rồi kết luận "bộ test vẫn xanh" — tức bản hỏng LỌT trong khi thực tế nó
    phá tan. Đã vấp thật khi dựng bộ này.
    """
    try:
        van, err = chay(**kw)
        return van, err, None
    except Exception as e:                                   # noqa: BLE001
        return "", "", e


def so_dong(url, tieu_de="Tin của mình bị trùng", trung_voi="Mảnh tương ứng bên file Jay"):
    return {"url": url, "tieu_de": tieu_de, "trung_voi": trung_voi,
            "id_jay": 7, "ngay": "2026-08-02"}


# ---------- (A) PHẢI LỌC — phủ đủ ba mục ----------
van, err = chay(so=[so_dong(U_US)])
kiem("[01] usNews: tin có URL trong sổ -> KHÔNG vào file",
     "điều trần về ngân sách quốc phòng" not in van and "bãi cạn Scarborough" in van)

van, err = chay(so=[so_dong(U_WORLD)])
kiem("[02] worldNews: tin có URL trong sổ -> KHÔNG vào file",
     "bãi cạn Scarborough" not in van and "điều trần về ngân sách quốc phòng" in van)

van, err = chay(so=[so_dong(U_EV)])
kiem("[03] events: item tập trận có URL trong sổ -> KHÔNG vào file",
     "Bài bắn đạn thật" not in van and "điều trần về ngân sách quốc phòng" in van)

van, _ = chay(now=SANG, so=[so_dong(U_US)])
kiem("[04] BẢN SÁNG cũng lọc (file Jay gửi tối qua còn hiệu lực 3 ngày)",
     "điều trần về ngân sách quốc phòng" not in van and "bãi cạn Scarborough" in van)

van, _ = chay(so=[so_dong(U_US), so_dong(U_WORLD), so_dong(U_EV)])
kiem("[05] cả ba tin đều trùng -> KHÔNG dựng file (DOCX rỗng)", van == "")


# ---------- (B) CHỐNG LỌC OAN ----------
van, _ = chay(so=[so_dong("https://apnews.com/tin-khac-han")])
kiem("[06] URL không có trong sổ -> giữ nguyên cả ba tin",
     all(t in van for t in ("điều trần về ngân sách quốc phòng", "bãi cạn Scarborough",
                            "Bài bắn đạn thật")))

van, _ = chay(so=[])
kiem("[07] sổ RỖNG -> không lọc gì",
     all(t in van for t in ("điều trần về ngân sách quốc phòng", "bãi cạn Scarborough")))

van, err, loi = chay_bat_loi(so=None)
kiem("[08] KHÔNG có file sổ -> giữ nguyên tin, KHÔNG ném lỗi (fail về phía KHÔNG lọc)",
     loi is None and "điều trần về ngân sách quốc phòng" in van
     and "bãi cạn Scarborough" in van)
kiem("[09] KHÔNG có file sổ -> vẫn phải KÊU (im lặng thì không phân biệt được với "
     "'hôm nay không trùng')", "trung-jaylam.json" in err)

van, err = chay(so="{ khong phai json")
kiem("[10] sổ JSON HỎNG -> không lọc + kêu",
     "điều trần về ngân sách quốc phòng" in van and "hỏng" in err.lower())

van, err = chay(so='{"url": "x"}')
kiem("[11] sổ không phải MẢNG -> không lọc + kêu",
     "điều trần về ngân sách quốc phòng" in van and "không phải mảng" in err)

# Dòng sổ thiếu `url` không được biến thành chuỗi rỗng trong tập lọc: tin nào `sourceUrl`
# rỗng sẽ bị bỏ oan, mà đó là ca tin sự kiện thiếu link — vẫn phải vào bản tin.
DATA_RONG_URL = json.loads(json.dumps(DATA_GIA))
DATA_RONG_URL["usNews"][0]["sourceUrl"] = ""
van, _ = chay(so=[{"tieu_de": "thiếu url", "trung_voi": "x", "id_jay": 1,
                   "ngay": "2026-08-02"}], data=DATA_RONG_URL)
kiem("[12] dòng sổ THIẾU url -> không lọc oan tin có sourceUrl rỗng",
     "điều trần về ngân sách quốc phòng" in van)


# ---------- (C) HỒI QUY: mục 5 và đường Supabase đã bỏ hẳn ----------
van, _ = chay(so=[])
kiem("[13] file KHÔNG còn mục 'Tin Jay Lâm gửi'", "Tin Jay Lâm gửi" not in van)
kiem("[14] file KHÔNG còn dòng nhãn 'chưa qua thang xác minh nguồn'",
     "chưa qua thang xác minh" not in van)

_src = (GS / "make_docx.py").read_text(encoding="utf-8")
kiem("[15] make_docx KHÔNG còn đường đọc Supabase (không chạm mạng khi dựng file)",
     "supabase.co" not in _src and "dt_jaylam_inbox" not in _src)
kiem("[16] `la_buoi_toi` VẪN CÒN — `ten_file()` dựa vào nó, đừng xoá theo mục 5",
     "def la_buoi_toi" in _src and "buoi = \"sang-som-5h\"" in _src)


# ---------- (D) KÊU ĐỦ ĐỂ SOI NGƯỢC ----------
van, err = chay(so=[so_dong(U_US)])
kiem("[17] tin bị bỏ phải được KÊU kèm tiêu đề (soi ngược được vì sao mất tin)",
     "Bộ lọc Jay Lâm" in err and "điều trần" in err)
kiem("[18] dòng kêu nói rõ MỤC nào bị bỏ", "usNews" in err)


# ---------- (E) SỐNG CHUNG VỚI LỌC CA SÁNG ----------
goc_url_sang = MD._url_ca_sang
MD._url_ca_sang = lambda now: {U_WORLD}
try:
    van, err = chay(so=[so_dong(U_US)])
finally:
    MD._url_ca_sang = goc_url_sang
kiem("[19] lọc ca sáng + lọc Jay Lâm chạy CÙNG LÚC, không cái nào nuốt cái nào",
     "điều trần về ngân sách quốc phòng" not in van and "bãi cạn Scarborough" not in van
     and "Bài bắn đạn thật" in van)


# ---------- (F) Đường ĐỌC SỔ dùng chung với tin_jaylam.py ----------
sys.path.insert(0, str(REPO / "scripts"))
kiem("[20] make_docx và tin_jaylam trỏ CÙNG một đường dẫn sổ",
     MD.SO_TRUNG_JAYLAM.endswith("logs/trung-jaylam.json")
     and str(pathlib.Path("logs/trung-jaylam.json")) in
     str((REPO / MD.SO_TRUNG_JAYLAM)))


BAN_HONG = [
    ("bỏ lọc Jay Lâm ở usNews",
     '    us = loc_bo_trung_jaylam(us, trung_jl, "usNews")',
     "    pass"),
    ("bỏ lọc Jay Lâm ở worldNews",
     '    world = loc_bo_trung_jaylam(world, trung_jl, "worldNews")',
     "    pass"),
    ("bỏ lọc Jay Lâm ở events",
     '    events = loc_bo_trung_jaylam(events, trung_jl, "events")',
     "    pass"),
    # Dựng lại đúng lỗi cũ của `loc_bo_tin_ca_sang` bản đầu: khoá phép lọc vào riêng bản tối.
    ("khoá phép lọc vào riêng bản TỐI (bản sáng lặp lại tin Jay đã có)",
     "    trung_jl = doc_url_trung_jaylam()",
     "    trung_jl = doc_url_trung_jaylam() if la_buoi_toi(now) else set()"),
    ("thiếu sổ -> KÊU LÊN rồi ném lỗi (fail-CLOSED: mất tin thay vì lặp tin)",
     '    except FileNotFoundError:\n'
     '        print(f"Không có {SO_TRUNG_JAYLAM} — không lọc tin trùng file Jay Lâm. "',
     '    except FileNotFoundError:\n'
     '        raise\n'
     '        print(f"Không có {SO_TRUNG_JAYLAM} — không lọc tin trùng file Jay Lâm. "'),
    ("thiếu sổ -> im lặng bỏ qua (không phân biệt được với 'hôm nay không trùng')",
     '        print(f"Không có {SO_TRUNG_JAYLAM} — không lọc tin trùng file Jay Lâm. "\n'
     '              "(Bước `tin_jaylam.py --ghi-loai` của phiên quét chưa từng chạy?)",\n'
     '              file=sys.stderr)\n'
     '        return set()',
     "        return set()"),
    ("JSON hỏng -> nuốt lỗi trong im lặng",
     '        print(f"Đọc {SO_TRUNG_JAYLAM} hỏng ({e}) — KHÔNG lọc, giữ nguyên tin.",\n'
     '              file=sys.stderr)\n'
     '        return set()',
     "        return set()"),
    ("sổ không phải mảng -> nuốt trong im lặng",
     '        print(f"{SO_TRUNG_JAYLAM} không phải mảng — KHÔNG lọc, giữ nguyên tin.",\n'
     '              file=sys.stderr)\n'
     '        return set()',
     "        return set()"),
    ("dòng sổ thiếu url vẫn vào tập lọc -> bỏ oan tin có sourceUrl rỗng",
     '    return {(r.get("url") or "").strip() for r in rows\n'
     '            if isinstance(r, dict) and (r.get("url") or "").strip()}',
     '    return {(r.get("url") or "").strip() for r in rows if isinstance(r, dict)}'),
    ("bỏ tiếng kêu khi loại tin -> mất tin trong im lặng, không soi ngược được",
     '        print(f"Bộ lọc Jay Lâm{\' [\' + ten_muc + \']\' if ten_muc else \'\'}: bỏ '
     '{len(bo)} tin "\n'
     '              "Jay Lâm đã có: "\n'
     '              + "; ".join((it.get("title") or it.get("sourceUrl") or "?")[:70] '
     'for it in bo),\n'
     '              file=sys.stderr)',
     "        pass"),
    # Dựng lại mục 5 đã bỏ: chứng minh ca [13]/[14] có răng chứ không phải ca hồi quy suông.
    ("dựng lại mục 5 'Tin Jay Lâm gửi' trong file",
     '    out = f"/tmp/{ten_file(gen, now)}"',
     '    ph = doc.add_paragraph()\n'
     '    set_font(ph.add_run("9. Tin Jay Lâm gửi"), size=SIZE, bold=True)\n'
     '    pn = doc.add_paragraph()\n'
     '    set_font(pn.add_run("Nội dung do Jay Lâm gửi qua bot, chưa qua thang xác minh '
     'nguồn của bản tin."), size=SIZE - 1, italic=True)\n'
     '    out = f"/tmp/{ten_file(gen, now)}"'),
]

KHAI_DO = {
    "bỏ lọc Jay Lâm ở usNews": ["01", "05", "17", "18", "19"],
    "bỏ lọc Jay Lâm ở worldNews": ["02", "05"],
    "bỏ lọc Jay Lâm ở events": ["03", "05"],
    "khoá phép lọc vào riêng bản TỐI (bản sáng lặp lại tin Jay đã có)": ["04"],
    "thiếu sổ -> KÊU LÊN rồi ném lỗi (fail-CLOSED: mất tin thay vì lặp tin)": ["08", "09"],
    "thiếu sổ -> im lặng bỏ qua (không phân biệt được với 'hôm nay không trùng')": ["09"],
    "JSON hỏng -> nuốt lỗi trong im lặng": ["10"],
    "sổ không phải mảng -> nuốt trong im lặng": ["11"],
    "dòng sổ thiếu url vẫn vào tập lọc -> bỏ oan tin có sourceUrl rỗng": ["12"],
    "bỏ tiếng kêu khi loại tin -> mất tin trong im lặng, không soi ngược được":
        ["17", "18"],
    "dựng lại mục 5 'Tin Jay Lâm gửi' trong file": ["13", "14"],
}


def _so_ca(ten):
    return ten[1:3] if ten.startswith("[") else ""


def tu_kiem():
    """Dựng từng bản `make_docx.py` đã GỠ một lớp bảo vệ rồi chạy lại chính bộ ca này.

    Bản hỏng nằm trong thư mục copy riêng mang PID + sha1 NỘI DUNG (mục 17 + 23 CLAUDE.md):
    tên cố định làm hai phiên chạy chồng xoá bản hỏng của nhau, và cùng đường dẫn làm
    `__pycache__` phát lại bytecode của bản hỏng TRƯỚC.
    """
    goc = (GS / "make_docx.py").read_text(encoding="utf-8")
    tong, trot = 0, []
    for ten, tim, thay in BAN_HONG:
        tong += 1
        if goc.count(tim) != 1:
            trot.append(f"{ten}: chuỗi neo khớp {goc.count(tim)} chỗ (phải đúng 1)")
            continue
        hong = goc.replace(tim, thay)
        sha = hashlib.sha1(hong.encode("utf-8")).hexdigest()[:8]
        d = pathlib.Path(tempfile.mkdtemp(prefix=f"jl-hong-{os.getpid()}-{sha}-"))
        try:
            # ⚠️ PHẢI GIỮ NGUYÊN CẤU TRÚC THƯ MỤC `<repo>/.github/scripts` + `<repo>/scripts`.
            # `make_docx.py` suy đường tới `scripts/` từ vị trí CHÍNH NÓ (lên 3 cấp từ
            # `__file__`) để `from topics import neo_uc_bien_dong`. Copy phẳng vào một thư mục
            # tạm thì phép suy đó trỏ ra ngoài `/var/folders/...` ⇒ `ModuleNotFoundError` ngay
            # lúc nạp ⇒ bản con không in được dòng ✓/✗ nào ⇒ `--tu-kiem` đọc thành "ĐỎ TOÀN BỘ"
            # và TRƯỢT cả 11 bản hỏng. Vấp thật 02/08/2026 ngay sau khi phiên khác thêm import
            # chéo đó vào `make_docx.py` mà không sửa các bộ test dựng bản hỏng của file này.
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
            if p.returncode == 0:
                trot.append(f"{ten}: bộ test VẪN XANH -> không bắt được lỗi")
            elif len(do) >= len([l for l in p.stdout.splitlines()
                                 if l[:1] in ("✓", "✗")]):
                trot.append(f"{ten}: ĐỎ TOÀN BỘ ca -> phép thay phá cú pháp, không gỡ lớp vá")
            elif not can & do:
                trot.append(f"{ten}: ca cần đỏ {sorted(can)} vẫn xanh; đỏ thực tế "
                            f"{sorted(do)}")
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
