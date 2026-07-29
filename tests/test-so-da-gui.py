#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TEST HỒI QUY CHO SỔ ĐÃ GỬI (.github/scripts/so_da_gui.py + make_docx.loc_chua_gui).

⚠ VÌ SAO CÓ FILE NÀY — luật đúc 29.7.2026 (CLAUDE.md toàn cục, mục 17):
Sổ đã gửi là cổng loại "hỏng thì im lặng cho qua". Hỏng theo HAI CHIỀU, chiều nào cũng câm:
  · sổ không đọc được / không lọc  -> bản tin TỐI liệt kê lại nguyên si tin đã gửi buổi SÁNG;
  · sổ ghi QUÁ PHẠM VI (email sự kiện buổi sáng ghi cả usNews/worldNews) -> tin thường bị
    xoá sổ trước khi kịp lên bản tin tối. Đây là MẤT TIN, tệ hơn trùng tin, và cũng không
    phát ra tiếng nào.
Không ca "PHẢI LỌC" và "PHẢI GIỮ ĐÚNG PHẠM VI" thì cả hai chiều đều không thể phát hiện.

Chạy:
    python3 tests/test-so-da-gui.py
    python3 tests/test-so-da-gui.py --tu-kiem   # chứng minh test này BẮT ĐƯỢC lỗi

Yêu cầu: `pip3 install python-docx` (make_docx.py import `docx` ngay từ đầu file).
"""
import datetime
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
GS_THAT = REPO / ".github" / "scripts"

# Seam để tự kiểm: thư mục chứa bản so_da_gui.py + make_docx.py đang thử. Mặc định là bản thật.
GS = pathlib.Path(os.environ.get("SODAGUI_DIR") or GS_THAT)
sys.path.insert(0, str(GS))

import make_docx as MD          # noqa: E402
import so_da_gui as SDG         # noqa: E402

# `prev_data()` chạy `git show HEAD~1:index.html` trong thư mục hiện tại — kết quả phụ thuộc
# lịch sử repo nên ca thử sẽ trôi theo thời gian. Ghim về None: khi đó `pick_items` rơi về
# luật "đưa lên hôm nay", đúng thứ ta muốn đo.
MD.prev_data = lambda: None

HOM_NAY = datetime.date.today().isoformat()

U_WORLD = "https://reuters.com/world/tin-the-gioi-1"
U_US = "https://apnews.com/article/tin-my-2"
U_EVENT = "https://abc.net.au/news/predator-run-3"

DATA_GIA = {
    "generatedAt": HOM_NAY,
    "worldNews": [{"date": HOM_NAY, "_addedDate": HOM_NAY, "title": "Tin thế giới",
                   "category": "Chính trị", "sourceUrl": U_WORLD}],
    "usNews": [{"date": HOM_NAY, "_addedDate": HOM_NAY, "title": "Tin Mỹ",
                "category": "Chính trị", "sourceUrl": U_US}],
    "exercises": [{"name": "Predator's Run", "items": [
        {"date": HOM_NAY, "_addedDate": HOM_NAY, "title": "Diễn biến tập trận",
         "sourceUrl": U_EVENT}]}],
}


class RepoGia:
    """Ghim `SO` (file sổ) và `ROOT` (nơi đọc index.html) vào một thư mục tạm rồi trả lại."""

    def __init__(self, so=None):
        self.so = so
        self.d = None

    def __enter__(self):
        self.d = pathlib.Path(tempfile.mkdtemp(prefix="sodagui-"))
        (self.d / "logs").mkdir()
        (self.d / "index.html").write_text(
            "<html><script>var DATA = " + json.dumps(DATA_GIA, ensure_ascii=False)
            + ";</script></html>", encoding="utf-8")
        if self.so is not None:
            (self.d / "logs" / "da-gui-email.json").write_text(
                self.so if isinstance(self.so, str)
                else json.dumps(self.so, ensure_ascii=False), encoding="utf-8")
        self._so_cu, self._root_cu = SDG.SO, SDG.ROOT
        SDG.SO = self.d / "logs" / "da-gui-email.json"
        SDG.ROOT = self.d
        return self.d

    def __exit__(self, *a):
        SDG.SO, SDG.ROOT = self._so_cu, self._root_cu
        shutil.rmtree(self.d, ignore_errors=True)
        return False


def lan_gui(urls, buoi="sang", tre_ngay=0):
    luc = datetime.datetime.now(SDG.VN) - datetime.timedelta(days=tre_ngay)
    return {"luc": luc.isoformat(timespec="seconds"), "buoi": buoi, "urls": list(urls)}


def tin(url):
    return {"sourceUrl": url, "title": "x"}


# ═════════════════════════════ các ca thử ═════════════════════════════
CA = []


def ca(ten):
    def deco(f):
        CA.append((ten, f))
        return f
    return deco


@ca('1. URL đã nằm trong sổ → loc_chua_gui PHẢI LOẠI nó')
def _():
    with RepoGia({"lan_gui": [lan_gui([U_WORLD])]}):
        con = MD.loc_chua_gui([tin(U_WORLD), tin(U_US)])
    urls = [it["sourceUrl"] for it in con]
    return urls == [U_US], f"còn lại: {urls}"


@ca('2. Sổ có NHIỀU lần gửi → phải loại tin của MỌI lần, không chỉ lần cuối')
def _():
    so = {"lan_gui": [lan_gui([U_WORLD], "sang", 1), lan_gui([U_US], "toi")]}
    with RepoGia(so):
        con = MD.loc_chua_gui([tin(U_WORLD), tin(U_US), tin(U_EVENT)])
    urls = [it["sourceUrl"] for it in con]
    return urls == [U_EVENT], f"còn lại: {urls}"


@ca('3. `--chi events` → sổ KHÔNG được nuốt URL tin thường (ghi thừa = MẤT TIN)')
def _():
    with RepoGia():
        urls = SDG._tin_cua_ban_tin_nay(("events",))
    return U_EVENT in urls and U_WORLD not in urls and U_US not in urls, f"ghi: {sorted(urls)}"


@ca('4. Ghi mặc định → phải gồm ĐỦ cả 3 loại (thiếu loại nào là loại đó gửi lại)')
def _():
    with RepoGia():
        urls = SDG._tin_cua_ban_tin_nay()
    return {U_WORLD, U_US, U_EVENT} <= urls, f"ghi: {sorted(urls)}"


@ca(f'5. Bản ghi cũ hơn GIU_NGAY={SDG.GIU_NGAY} ngày → PHẢI bị cắt khỏi sổ')
def _():
    cu = "https://cu.example/tin-rat-cu"
    with RepoGia({"lan_gui": [lan_gui([cu], "toi", SDG.GIU_NGAY + 3)]}):
        SDG.ghi_lan_gui([U_WORLD], "toi")
        con = SDG.url_da_gui()
    return cu not in con and U_WORLD in con, f"sổ sau khi ghi: {sorted(con)}"


@ca('6. CHƯA có sổ (chạy lần đầu) → giữ NGUYÊN danh sách (thà gửi trùng còn hơn gửi rỗng)')
def _():
    with RepoGia():
        con = MD.loc_chua_gui([tin(U_WORLD), tin(U_US)])
    return len(con) == 2, f"còn lại: {len(con)} tin"


@ca('7. Sổ HỎNG (JSON vỡ) → giữ NGUYÊN danh sách, không được nuốt sạch bản tin')
def _():
    with RepoGia("{ đây không phải JSON"):
        con = MD.loc_chua_gui([tin(U_WORLD), tin(U_US)])
    return len(con) == 2, f"còn lại: {len(con)} tin"


@ca('8. Sổ đúng dạng nhưng URL chưa từng gửi → phải GIỮ (chống lọc oan)')
def _():
    with RepoGia({"lan_gui": [lan_gui(["https://khac.example/z"])]}):
        con = MD.loc_chua_gui([tin(U_WORLD), tin(U_US)])
    return len(con) == 2, f"còn lại: {len(con)} tin"


@ca('9. Sổ PHẢI còn người đọc: send_telegram.py vẫn gọi loc_chua_gui (kiểm tĩnh)')
def _():
    # Cổng sống mà không ai gọi thì vẫn là cổng câm. Đây là kiểm TĨNH (đọc mã nguồn) chứ
    # không phải kiểm hành vi — chỉ khẳng định lời gọi còn đó, không khẳng định nó chạy.
    src = (GS_THAT / "send_telegram.py").read_text(encoding="utf-8")
    n = src.count("loc_chua_gui(")
    return n >= 2, f"đếm được {n} lời gọi loc_chua_gui( trong send_telegram.py (cần >= 2)"


# ═══════════════════════════ tự kiểm: bản hỏng ═══════════════════════════
# (nhãn · file · phép thay · các ca BẮT BUỘC phải đỏ)
BAN_HONG = [
    ("so_da_gui: đọc sổ về rỗng (cổng câm hoàn toàn)", "so_da_gui.py",
     ('        out.update(u for u in (lan.get("urls") or []) if u)', '        pass'),
     [1, 2, 5]),
    ("so_da_gui: bỏ phép cắt bản ghi quá hạn", "so_da_gui.py",
     ('            if datetime.datetime.fromisoformat(lan["luc"]) >= han:',
      '            if True:'),
     [5]),
    ("so_da_gui: `--chi` bị bỏ qua, luôn ghi cả 3 loại", "so_da_gui.py",
     ('    for kind in kinds:', '    for kind in KIND_MAC_DINH:'),
     [3]),
    ("make_docx: loc_chua_gui trả nguyên danh sách (không lọc)", "make_docx.py",
     ('    out = [it for it in items if it.get("sourceUrl") not in da_gui]',
      '    out = list(items)'),
     [1, 2]),
]


def tu_kiem() -> int:
    print("TỰ KIỂM — dựng bản đã gỡ dòng bảo vệ, các ca đã khai PHẢI ĐỎ")
    print("═" * 78)
    hong = 0
    for nhan, ten_file, (tim, thay), ca_phai_do in BAN_HONG:
        goc = (GS_THAT / ten_file).read_text(encoding="utf-8")
        if goc.count(tim) != 1:
            print(f"  ✗ {nhan}\n        │ KHÔNG áp được phép thay: {goc.count(tim)} chỗ khớp "
                  f"trong {ten_file} (cần đúng 1). Mã nguồn đã đổi → sửa lại test.")
            hong += 1
            continue
        d = pathlib.Path(tempfile.mkdtemp(prefix="sodagui-hong-"))
        for f in ("so_da_gui.py", "make_docx.py"):
            shutil.copy2(GS_THAT / f, d / f)
        (d / ten_file).write_text(goc.replace(tim, thay), encoding="utf-8")
        env = dict(os.environ, SODAGUI_DIR=str(d))
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


def main() -> int:
    if "--tu-kiem" in sys.argv:
        return tu_kiem()
    print(f"TEST SỔ ĐÃ GỬI — mọi ca 'PHẢI LOẠI' phải thật sự loại\n(bản đang thử: {GS})")
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
        print(f"✗ {hong}/{len(CA)} ca HỎNG — sổ đã gửi không còn chặn đúng, sửa trước khi gửi bản tin.")
        return 1
    print(f"✓ {len(CA)}/{len(CA)} ca đạt — sổ đã gửi còn sống.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
