#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CỔNG: TRANG HỎNG MÃ THÌ KHÔNG ĐƯỢC ĐƯA LÊN MẠNG — dựng 22/11/2026.

VÌ SAO CÓ FILE NÀY
──────────────────
Lượt quét CI 07/10/2026 21:44Z (commit 869f311) tự tay gỡ 03 tin trùng khỏi `index.html` bằng
mã viết tại chỗ, cắt nhầm 670 dòng mã nằm giữa khối `var DATA` và dòng
`var src=d&&d.src?d.src:''` của phần ôn khái niệm. Dòng DATA dính liền với đuôi `=d&&d.src…`
nên trình duyệt báo «Invalid destructuring assignment target» và KHÔNG chạy dòng mã nào:
trang trắng suốt 46 ngày (đo 22/11/2026 bằng Playwright trên bản GitHub Pages, chữ trên trang
= 0). Không cổng nào kêu: `canary.kiem_web()` chỉ so băm bản web với bản trên `main`, mà hai
bản cùng hỏng thì vẫn khớp. Từ 27/10 lượt quét sự kiện còn ghi ô `dates` dạng
`{start,end}`, lỗi thứ hai này cũng làm trang chết nếu lỗi thứ nhất được vá riêng.

Cổng đo 03 thứ trên đúng file sắp đưa lên:
  (1) MỌI khối <script> nội tuyến dịch được (node `new Function`, chỉ dịch, không chạy);
  (2) khối `var DATA` là JSON đọc được;
  (3) các hàm lõi còn được KHAI (bắt kiểu cắt mất mã mà cú pháp vẫn tình cờ lành).
Cắm ở `pages.yml` trước VÀ sau bước cắt bản nhẹ: hỏng thì bước dựng dừng, GitHub Pages giữ
bản đang chạy, và `canary.kiem_web()` sẽ kêu lệch ở lượt kế tiếp.

    python3 scripts/kiem_trang_chay.py [index.html]   # mã 0 đạt · 1 hỏng · 2 không đo được
    python3 scripts/kiem_trang_chay.py --tu-kiem

⚠ FAIL-CLOSED: không có `node` thì trả 2, KHÔNG trả 0 — «không đo được» khác «không thấy lỗi».
"""
import json
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Hàm lõi phải còn được khai. Chọn hàm nằm RẢI khắp file (đầu, giữa, cuối) và hàm mà mất đi
# là mất cả một mảng: vẽ trang · đọc ngày tập trận · nút thông báo · ôn khái niệm.
HAM_LOI = ("esc", "fmtVN", "render", "evRange", "datesChu", "pushRow", "enablePush",
           "sbSavePushSub", "sbRemovePushSub", "toggleFav", "makeDocx")

JS_DICH = ("const fs=require('fs');const a=JSON.parse(fs.readFileSync(0,'utf8'));"
           "const r=a.map(function(s,i){try{new Function(s);return null}"
           "catch(e){return 'khối '+(i+1)+': '+e.message}});"
           "process.stdout.write(JSON.stringify(r))")


def tim_node():
    for p in (shutil.which("node"), "/opt/homebrew/bin/node", "/usr/local/bin/node", "/usr/bin/node"):
        if p and pathlib.Path(p).exists():
            return p
    return None


def khoi_script(html):
    return re.findall(r"<script>(.*?)</script>", html, re.S)


def dich_thu(khoi, node):
    """list lỗi (rỗng = dịch được hết). None = không đo được."""
    if not node:
        return None
    try:
        r = subprocess.run([node, "-e", JS_DICH], input=json.dumps(khoi), capture_output=True,
                           text=True, timeout=120)
        return [x for x in json.loads(r.stdout) if x]
    except Exception:
        return None


def doc_data(html):
    i = html.find("var DATA = ")
    if i < 0:
        return "không thấy `var DATA = `"
    s = i + len("var DATA = ")
    sau = 0
    try:
        _, sau = json.JSONDecoder().raw_decode(html, s)
    except ValueError as e:
        return "khối DATA không phải JSON đọc được: %s" % e
    duoi = html[sau:sau + 40].lstrip(" \t")
    if not (duoi.startswith(";") or duoi.startswith("\n")):
        return "khối DATA dính liền mã phía sau: %r" % duoi[:30]
    return None


def ham_thieu(khoi):
    goc = "\n".join(khoi)
    return [h for h in HAM_LOI if not re.search(r"\bfunction\s+%s\s*\(" % re.escape(h), goc)]


def kiem(html, node="__tim__"):
    """(mã, list lỗi). 0 đạt · 1 hỏng · 2 không đo được."""
    node = tim_node() if node == "__tim__" else node
    khoi = khoi_script(html)
    if not khoi:
        return 1, ["không có khối <script> nội tuyến nào"]
    loi = []
    d = doc_data(html)
    if d:
        loi.append(d)
    loi += ["thiếu hàm %s()" % h for h in ham_thieu(khoi)]
    dich = dich_thu(khoi, node)
    if dich is None:
        return 2, loi + ["KHÔNG ĐO ĐƯỢC cú pháp: thiếu node hoặc node lỗi"]
    loi += ["lỗi cú pháp " + x for x in dich]
    return (1 if loi else 0), loi


def main(argv):
    p = pathlib.Path(argv[0]) if argv else ROOT / "index.html"
    try:
        html = p.read_text(encoding="utf-8")
    except OSError as e:
        print("🟡 không đọc được %s: %s" % (p, e))
        return 2
    ma, loi = kiem(html)
    if ma == 0:
        print("🟢 %s: mã trang dịch được, DATA đọc được, đủ %d hàm lõi" % (p.name, len(HAM_LOI)))
    else:
        print(("🔴 TRANG HỎNG" if ma == 1 else "🟡 CHƯA ĐO ĐƯỢC") + " — %s:" % p)
        for x in loi:
            print("   " + x)
    return ma


# ── tự kiểm ────────────────────────────────────────────────────────────────────────────────
def _trang(data='{"a":1}', ma=None, noi=";\n"):
    ma = ma if ma is not None else "".join("function %s(){}\n" % h for h in HAM_LOI)
    return "<html><script>var x=1;</script><script>\nvar DATA = %s%s%s</script></html>" % (data, noi, ma)


def tu_kiem():
    ca = []
    node = tim_node()

    def c(ten, dk):
        ca.append((ten, bool(dk)))

    c("00 · máy có node để đo (thiếu thì mọi ca dưới vô nghĩa)", node)
    c("01 · trang lành → 0", kiem(_trang(), node)[0] == 0)
    # Đúng hình lỗi 07/10: DATA dính đuôi `=d&&d.src…` của dòng bị cắt.
    hong = _trang(noi="", ma="=d&&d.src?d.src:'';\n" + "".join("function %s(){}\n" % h for h in HAM_LOI))
    m, l = kiem(hong, node)
    c("02 · PHẢI CHẶN: DATA dính đuôi mã (hình lỗi 869f311) → 1, kêu cả cú pháp lẫn DATA",
      m == 1 and any("cú pháp" in x for x in l) and any("dính liền" in x for x in l))
    m, l = kiem(_trang(ma="function a({b}=1{}\n" + "".join("function %s(){}\n" % h for h in HAM_LOI)), node)
    c("03 · PHẢI CHẶN: lỗi cú pháp ở khối mã (DATA lành) → 1", m == 1 and any("cú pháp" in x for x in l))
    m, l = kiem(_trang(ma="".join("function %s(){}\n" % h for h in HAM_LOI if h != "pushRow")), node)
    c("04 · PHẢI CHẶN: cú pháp lành nhưng mất hàm lõi → 1, nêu đúng tên", m == 1 and l == ["thiếu hàm pushRow()"])
    m, l = kiem(_trang(data='{"a":1,}'), node)
    c("05 · PHẢI CHẶN: DATA không phải JSON → 1", m == 1 and any("JSON" in x for x in l))
    m, l = kiem(_trang(), None)
    c("06 · PHẢI KÊU: không có node → 2, không được trả 0", m == 2)
    c("07 · PHẢI CHẶN: trang không có khối script → 1", kiem("<html></html>", node)[0] == 1)
    c("08 · ĐỐI CHỨNG: `function x (` có dấu cách vẫn tính là đã khai",
      kiem(_trang(ma="".join("function %s (){}\n" % h for h in HAM_LOI)), node)[0] == 0)
    for t, d in ca:
        print(("  ✅ " if d else "  ❌ ") + t)
    so_dat = sum(d for _, d in ca)

    # Bản hỏng: gỡ từng răng của cổng rồi chạy lại đúng các ca PHẢI CHẶN.
    g = globals()
    ban_hong = [
        ("dich_thu luôn trả rỗng", "dich_thu", lambda khoi, node: [] if node else None, "03"),
        ("doc_data luôn coi là lành", "doc_data", lambda html: None, "05"),
        ("ham_thieu luôn rỗng", "ham_thieu", lambda khoi: [], "04"),
        ("không node mà vẫn trả kết quả rỗng", "dich_thu", lambda khoi, node: [], "06"),
    ]
    bat = 0
    for ten, ham, thay, ca_so in ban_hong:
        cu = g[ham]
        g[ham] = thay
        try:
            if ca_so == "03":
                do = kiem(_trang(ma="function a({b}=1{}\n" + "".join(
                    "function %s(){}\n" % h for h in HAM_LOI)), node)[0] != 1
            elif ca_so == "05":
                do = kiem(_trang(data='{"a":1,}'), node)[0] != 1
            elif ca_so == "04":
                do = kiem(_trang(ma="".join("function %s(){}\n" % h for h in HAM_LOI if h != "pushRow")), node)[0] != 1
            else:
                do = kiem(_trang(), None)[0] != 2
        finally:
            g[ham] = cu
        bat += do
        print(("  ✅ bản hỏng bị bắt: " if do else "  ❌ bản hỏng LỌT: ") + ten)
    print("\n%d/%d ca đạt · %d/%d bản hỏng bị bắt" % (so_dat, len(ca), bat, len(ban_hong)))
    return 0 if so_dat == len(ca) and bat == len(ban_hong) else 1


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(tu_kiem() if "--tu-kiem" in a else main(a))
