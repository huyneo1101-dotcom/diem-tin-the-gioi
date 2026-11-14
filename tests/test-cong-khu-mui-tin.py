#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TEST CỔNG KHỬ MÙI A.I CHO TIN (scripts/khu_mui_tin.py) — dựng 14/11/2026.

Huy chốt 14/11/2026: *"Nội dung và tiêu đề các bài phải chạy khử mùi A.I"*. Cổng này thuộc
loại HỎNG THÌ IM: tách câu hụt, quên một mảng tin, hay `add_news.py` thôi gọi cổng thì lô vẫn
nạp êm và bản tin vẫn đi, chỉ là chữ chưa qua máy chấm. Chỉ ca PHẢI CHẶN mới phân biệt được.

Chạy:
    python3 tests/test-cong-khu-mui-tin.py
    python3 tests/test-cong-khu-mui-tin.py --tu-kiem   # dựng bản hỏng, ca đã khai phải đỏ
"""
import importlib.util
import os
import pathlib
import shutil
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parent.parent
THU = pathlib.Path(os.environ.get("KHUMUI_TIN_THU") or REPO / "scripts")


def _nap():
    spec = importlib.util.spec_from_file_location("khu_mui_tin_thu", THU / "khu_mui_tin.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


K = _nap()


def tin(title, summary="", significance=""):
    return {"date": "2026-11-14", "category": "Chính trị", "title": title, "summary": summary,
            "significance": significance, "sourceName": "Reuters",
            "sourceUrl": "https://www.reuters.com/world/x-2026-11-14/"}


SACH = tin("Thượng viện Mỹ mở phiên điều trần về ngân sách quốc phòng năm 2027",
           "Uỷ ban Quân vụ Thượng viện mở phiên điều trần ngày 19/11. Bộ trưởng Quốc phòng trình "
           "bày đề xuất tăng ngân sách đóng tàu.",
           "Phiên điều trần cho thấy mức ưu tiên của Quốc hội với ngành đóng tàu.")


BAN = tin("Mỹ hoan nghênh bà Doreen Bogdan-Martin tái đắc cử Tổng thư ký ITU",
          "Bộ Ngoại giao Mỹ ra thông cáo hoan nghênh kết quả bầu cử.")


def _bao(lo):
    """Dòng nhắc của cổng. Ném lỗi ở đây là SAI — Huy cấm chặn tin 14/11/2026."""
    return "\n".join(K.kiem_lo(lo))


CA = []


def ca(ten):
    def boc(f):
        CA.append((ten, f))
        return f
    return boc


@ca("1. PHẢI BÁO — tiêu đề mang «bà + tên riêng» thay cho chức danh")
def _():
    ra = _bao({"usNews": [BAN]})
    return "usNews[0].title" in ra and "nên viết lại" in ra, ra


@ca("2. PHẢI BÁO — lỗi nằm ở CÂU THỨ HAI của nội dung (tách câu không được hụt)")
def _():
    ra = _bao({"worldNews": [tin(
        "Australia ký hợp đồng mua thêm tàu ngầm",
        "Bộ Quốc phòng Australia ký hợp đồng ngày 13/11. Canberra không kỳ vọng ra thoả thuận mới "
        "mà coi đây là điểm khởi đầu đối thoại.")]})
    return "summary câu 2" in ra, ra


@ca("3. PHẢI BÁO — tin diễn biến tập trận (exerciseUpdates) cũng được soát")
def _():
    ra = _bao({"exerciseUpdates": [{"name": "Tập trận X", "items": [tin(
        "Cuộc tập trận là phép thử cho khả năng phối hợp của hai lực lượng")]}]})
    return "exerciseUpdates[0].items[0]" in ra, ra


@ca("4. Tin sạch, có «điều trần» — không nhắc gì")
def _():
    ra = _bao({"usNews": [SACH]})
    return "đều sạch" in ra and "nên viết lại" not in ra, ra


@ca("5. PHẢI CHẶN — câu có mùi KHÔNG được làm chặn tin (Huy cấm chặn 14/11/2026)")
def _():
    try:
        ra = K.kiem_lo({"usNews": [BAN, SACH]})
    except Exception as e:                                             # noqa: BLE001
        return False, f"cổng ném {type(e).__name__} — tin bị chặn: {e}"
    return any("VẪN NẠP ĐỦ" in d for d in ra), ra


@ca("6. PHẢI CHẶN — thiếu máy chấm (máy Mac lẫn máy dự phòng GitHub) chỉ in nhắc, không chặn")
def _():
    goc_km, goc_may = K.KHU_MUI, K._may
    try:
        K.KHU_MUI, K._may = pathlib.Path("/khong/co/khu-mui-ai.py"), None
        ra = K.kiem_lo({"usNews": [SACH]})
    except Exception as e:                                             # noqa: BLE001
        return False, f"cổng ném {type(e).__name__}: {e}"
    finally:
        K.KHU_MUI, K._may = goc_km, goc_may
    return any("KHÔNG CHẠY" in d for d in ra), ra


@ca("7. PHẢI CHẶN — add_news.py gọi khử mùi TRƯỚC cổng ngày đăng thật")
def _():
    ng = (THU / "add_news.py").read_text(encoding="utf-8")
    i = ng.find("khu_mui_tin.kiem_lo(new_items)")
    j = ng.find("ngay_that.kiem_lo(")
    return 0 < i < j, f"vị trí gọi khử mùi {i}, gọi ngày đăng thật {j}"


@ca("8. PHẢI CHẶN — lệnh tự soát của agent trả mã 1 khi còn câu nên viết lại, 0 khi sạch")
def _():
    import json
    import subprocess
    d = pathlib.Path(tempfile.mkdtemp(prefix="_khumuitin-"))
    try:
        (d / "ban.json").write_text(json.dumps({"usNews": [BAN]}, ensure_ascii=False), encoding="utf-8")
        (d / "sach.json").write_text(json.dumps({"usNews": [SACH]}, ensure_ascii=False), encoding="utf-8")
        ma = [subprocess.run([sys.executable, str(THU / "khu_mui_tin.py"), str(d / f)],
                             capture_output=True, text=True).returncode for f in ("ban.json", "sach.json")]
    finally:
        shutil.rmtree(d, ignore_errors=True)
    return ma == [1, 0], f"mã thoát (lô bẩn, lô sạch) = {ma}"


BAN_HONG = [
    # ca 3 cũng đặt lỗi ở tiêu đề nên đỏ theo — đúng thiết kế, không phải nhiễu.
    ("tiêu đề không được đo", "khu_mui_tin.py",
     'TRUONG_TIEU_DE = ("title", "name")', "TRUONG_TIEU_DE = ()", [1, 3, 5, 8]),
    ("tách câu chỉ giữ câu đầu", "khu_mui_tin.py",
     '    return [c.strip() for c in re.split(r"(?<=[.!?])\\s+", t) if c.strip()]',
     '    return [c.strip() for c in re.split(r"(?<=[.!?])\\s+", t) if c.strip()][:1]', [2]),
    ("bỏ sót tin sự kiện và tập trận", "khu_mui_tin.py",
     "    for mang in MANG_SU_KIEN:", "    for mang in ():", [3]),
    ("câu có mùi lại làm CHẶN tin (lối cũ Huy đã bỏ)", "khu_mui_tin.py",
     '    return [f"⚠ khử mùi: {len(hong)}/{n}',
     '    raise ValueError(str(hong))\n    return [f"⚠ khử mùi: {len(hong)}/{n}', [1, 2, 3, 5]),
    ("thiếu máy chấm thì chặn tin", "khu_mui_tin.py",
     '        return [f"⚠ khử mùi KHÔNG CHẠY',
     '        raise ValueError("thiếu máy chấm")\n        return [f"⚠ khử mùi KHÔNG CHẠY', [6]),
    ("add_news.py thôi gọi khử mùi", "add_news.py",
     "    for dong in khu_mui_tin.kiem_lo(new_items):", "    for dong in []:", [7]),
    ("lệnh tự soát luôn trả 0 (agent không biết phải viết lại)", "khu_mui_tin.py",
     "    print(f\"✗ {len(hong)}/{n} câu nên viết lại", "    return 0\n    print(f\"✗ {len(hong)}/{n} câu nên viết lại", [8]),
]


def chay() -> int:
    print(f"TEST CỔNG KHỬ MÙI TIN — {THU}")
    print("=" * 78)
    do = []
    for ten, f in CA:
        try:
            ok, chi_tiet = f()
        except Exception as e:                                         # noqa: BLE001
            ok, chi_tiet = False, f"{type(e).__name__}: {e}"
        print(f"  {'✓' if ok else '✗'} {ten}")
        if not ok:
            do.append(ten.split(".")[0])
            print(f"        │ {str(chi_tiet)[:400]}")
    print("=" * 78)
    print(f"{'✗' if do else '✓'} {len(CA) - len(do)}/{len(CA)} ca đạt")
    if do:
        print("CA_DO=" + ",".join(do))
    return 1 if do else 0


def tu_kiem() -> int:
    import subprocess
    print("TỰ KIỂM — dựng bản hỏng, ca đã khai PHẢI đỏ")
    hong = 0
    for nhan, tep, tim, thay, phai_do in BAN_HONG:
        d = pathlib.Path(tempfile.mkdtemp(prefix="_hong-khumuitin-"))
        try:
            for f in ("khu_mui_tin.py", "add_news.py"):
                shutil.copy2(REPO / "scripts" / f, d / f)
            p = d / tep
            nd = p.read_text(encoding="utf-8")
            if nd.count(tim) != 1:
                print(f"  ✗ {nhan}\n        │ phép thay khớp {nd.count(tim)} chỗ (cần 1) — mã đã đổi")
                hong += 1
                continue
            p.write_text(nd.replace(tim, thay), encoding="utf-8")
            r = subprocess.run([sys.executable, __file__], capture_output=True, text=True,
                               env=dict(os.environ, KHUMUI_TIN_THU=str(d)))
            dong = [l for l in r.stdout.splitlines() if l.startswith("CA_DO=")]
            do = sorted(int(x) for x in dong[0][6:].split(",")) if dong else []
            ok = do == sorted(phai_do)
            hong += not ok
            print(f"  {'✓' if ok else '✗'} {nhan}\n        │ ca đỏ: {do} · cần đỏ: {phai_do}")
        finally:
            shutil.rmtree(d, ignore_errors=True)
    print("=" * 78)
    print(f"{'✗' if hong else '✓'} {len(BAN_HONG) - hong}/{len(BAN_HONG)} bản hỏng bị bắt")
    return 1 if hong else 0


if __name__ == "__main__":
    sys.exit(tu_kiem() if "--tu-kiem" in sys.argv else chay())
