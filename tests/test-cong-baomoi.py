#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TEST HỒI QUY CHO CỔNG BÁO MỚI của scripts/add_news.py.

⚠ VÌ SAO CÓ FILE NÀY — luật đúc 29.7.2026 (CLAUDE.md toàn cục, mục 17):
Cổng dàn ý của QuanSu đã CÂM từ ngày dựng tới 29.7.2026 mà không ai biết, vì nó thuộc loại
"hỏng thì im lặng cho qua": không có gì để chặn thì cổng im, và cổng chết cũng im y hệt.
Cổng Báo Mới ở đây CÙNG MỘT LOẠI — hỏng thì nó chỉ đơn giản là không nhắc gì, phiên quét
vẫn chạy xanh, và bài Báo Mới hợp chủ đề âm thầm rơi khỏi bản tin.

=> Mọi ca dưới đây gắn nhãn "PHẢI NHẮC" là ca dựng đúng điều kiện xấu rồi khẳng định cổng
   THẬT SỰ kêu. Test chỉ có ca "phải im" là chưa test.

Chạy:
    python3 tests/test-cong-baomoi.py
    python3 tests/test-cong-baomoi.py --tu-kiem   # chứng minh test này BẮT ĐƯỢC lỗi

`--tu-kiem` dựng các bản add_news.py ĐÃ GỠ ĐÚNG DÒNG BẢO VỆ rồi chạy lại chính bộ ca này
với `ADDNEWS_MOD` trỏ vào bản hỏng — mỗi bản hỏng phải làm ĐỎ đúng những ca đã khai. Test
xanh trên cả bản đúng lẫn bản hỏng là test vô dụng.
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

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SCRIPTS = REPO / "scripts"

# Seam để tự kiểm: trỏ sang một bản add_news.py khác (xem --tu-kiem).
MOD_PATH = pathlib.Path(os.environ.get("ADDNEWS_MOD") or (SCRIPTS / "add_news.py"))

# `add_news.baomoi_topic_hits` tự chèn thư mục của CHÍNH NÓ vào sys.path để `import topics`.
# Bản hỏng nằm ở thư mục tạm nên phải chèn sẵn scripts/ thật, nếu không ca nào cũng đỏ vì
# ImportError — đỏ vì lý do sai thì không chứng minh được gì.
sys.path.insert(0, str(SCRIPTS))


def _nap(path: pathlib.Path):
    spec = importlib.util.spec_from_file_location("add_news_duoi_thu", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


AN = _nap(MOD_PATH)

HOM_NAY = datetime.date.today().isoformat()
HOM_KIA = (datetime.date.today() - datetime.timedelta(days=3)).isoformat()

# Tiêu đề khớp CHẮC CHẮN một chủ đề (từ khoá tự đủ "biển đông" trong topics.py).
TIN_HOP = {
    "date": HOM_NAY,
    "category": "Quân sự",
    "title": "Tàu hải cảnh Trung Quốc áp sát bãi Cỏ Mây trên Biển Đông",
    "sourceName": "Báo Mới",
    "sourceUrl": "https://baomoi.com/tau-hai-canh-ap-sat-co-may-1.epi",
    "region": "Đông Nam Á",
}
# Tiêu đề KHÔNG thuộc chủ đề nào — dùng để bắt cổng nhắc oan.
TIN_LAC = {
    "date": HOM_NAY,
    "category": "Xã hội",
    "title": "Giá vé máy bay nội địa dịp hè tăng nhẹ so với cùng kỳ",
    "sourceName": "Báo Mới",
    "sourceUrl": "https://baomoi.com/gia-ve-may-bay-he-2.epi",
    "region": "Việt Nam",
}
# Bẫy substring: chuỗi "úc" nằm trong "thúc đẩy". Khớp thô thì bài kinh tế này lọt vào
# chủ đề "Úc & Biển Đông" — đúng con bug đã sửa bằng cách khớp theo ranh giới từ.
TIN_BAY_THUC = {
    "date": HOM_NAY,
    "category": "Kinh tế",
    "title": "Chính phủ thúc đẩy tăng trưởng tín dụng những tháng cuối năm",
    "sourceName": "Báo Mới",
    "sourceUrl": "https://baomoi.com/thuc-day-tang-truong-3.epi",
    "region": "Việt Nam",
}


def dung_kho(saved=(), topics=()):
    """Dựng repo giả chỉ có 2 file kho Báo Mới. Trả về đường dẫn thư mục."""
    d = pathlib.Path(tempfile.mkdtemp(prefix="congbaomoi-"))
    (d / "baomoi-saved.json").write_text(
        json.dumps({"items": list(saved)}, ensure_ascii=False), encoding="utf-8")
    (d / "baomoi-topics.json").write_text(
        json.dumps({"items": list(topics)}, ensure_ascii=False), encoding="utf-8")
    return d


def chay_cong(repo_gia, existing=frozenset()):
    """Gọi cổng, trả về đúng chữ nó in ra."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        AN.print_baomoi_gate(repo_gia, set(existing))
    return buf.getvalue()


def keu(out):
    return "⚠️" in out and "CỔNG BÁO MỚI" in out


def im(out):
    return "✅" in out and "CỔNG BÁO MỚI" in out


# ═════════════════════════════ các ca thử ═════════════════════════════
CA = []


def ca(ten):
    def deco(f):
        CA.append((ten, f))
        return f
    return deco


@ca('1. Ứng viên chuyên mục hợp chủ đề, CHƯA nạp → PHẢI NHẮC')
def _():
    d = dung_kho(topics=[TIN_HOP])
    out = chay_cong(d)
    shutil.rmtree(d, ignore_errors=True)
    return keu(out) and TIN_HOP["title"] in out, out


@ca('2. Bài NGƯỜI DÙNG tự lưu hợp chủ đề, CHƯA nạp → PHẢI NHẮC (kho thứ hai)')
def _():
    d = dung_kho(saved=[TIN_HOP])
    out = chay_cong(d)
    shutil.rmtree(d, ignore_errors=True)
    return keu(out) and TIN_HOP["title"] in out, out


@ca('3. Cùng bài đó nhưng ĐÃ nạp (URL có trong DATA) → phải IM (chống nhắc oan)')
def _():
    d = dung_kho(topics=[TIN_HOP])
    out = chay_cong(d, {TIN_HOP["sourceUrl"]})
    shutil.rmtree(d, ignore_errors=True)
    return im(out), out


@ca('4. Đã nạp qua NGUỒN GỐC, chỉ giữ `_baomoiUrl` → phải IM (chống nạp lại y hệt)')
def _():
    # Đây là lý do tồn tại của `_baomoiUrl`: tin đã truy về bài gốc nước ngoài thì sourceUrl
    # không còn là link Báo Mới, cổng sẽ coi bài đó "chưa nạp" và phiên sau nạp lại lần nữa.
    data = {"worldNews": [{
        "sourceUrl": "https://reuters.com/world/asia-pacific/xyz",
        "_baomoiUrl": TIN_HOP["sourceUrl"],
    }]}
    d = dung_kho(topics=[TIN_HOP])
    out = chay_cong(d, AN.collect_existing_urls(data))
    shutil.rmtree(d, ignore_errors=True)
    return im(out), out


@ca('5. Bài KHÔNG thuộc chủ đề nào → phải IM (chống nhắc oan)')
def _():
    d = dung_kho(topics=[TIN_LAC])
    out = chay_cong(d)
    shutil.rmtree(d, ignore_errors=True)
    return im(out), out


@ca('6. Bẫy substring "thúc đẩy" chứa "úc" → phải IM (khớp theo ranh giới từ)')
def _():
    d = dung_kho(topics=[TIN_BAY_THUC])
    out = chay_cong(d)
    shutil.rmtree(d, ignore_errors=True)
    return im(out), out


@ca('7. Bài hợp chủ đề nhưng ĐĂNG QUÁ KHUNG NGÀY → phải IM (kho cũ không kéo bài chết dậy)')
def _():
    d = dung_kho(topics=[dict(TIN_HOP, date=HOM_KIA)])
    out = chay_cong(d)
    shutil.rmtree(d, ignore_errors=True)
    return im(out), out


@ca('8. Cổng PHẢI nằm trên đường đi của `--recent-titles` → PHẢI in ra khi chạy thật')
def _():
    # Cổng sống mà không ai gọi thì vẫn là cổng câm. Ca này chạy đúng lệnh mà phiên quét chạy.
    r = subprocess.run([sys.executable, str(MOD_PATH), "--recent-titles", "1"],
                       capture_output=True, text=True, cwd=str(REPO))
    out = r.stdout + r.stderr
    return r.returncode == 0 and "CỔNG BÁO MỚI" in out, out[-1200:]


# ═══════════════════════════ tự kiểm: bản hỏng ═══════════════════════════
# (nhãn · phép thay trong mã nguồn · các ca BẮT BUỘC phải đỏ)
BAN_HONG = [
    ("gỡ cả 2 kho khỏi vòng quét (cổng câm hoàn toàn)",
     ('for fname in ("baomoi-saved.json", "baomoi-topics.json"):', 'for fname in ():'),
     [1, 2]),
    ("bỏ kho bài NGƯỜI DÙNG TỰ LƯU",
     ('for fname in ("baomoi-saved.json", "baomoi-topics.json"):',
      'for fname in ("baomoi-topics.json",):'),
     [2]),
    ("gỡ phép loại bài ĐÃ NẠP (cổng nhắc oan)",
     ('            if not url or url in existing:', '            if not url:'),
     [3, 4]),
    ("gỡ phép lọc KHUNG NGÀY của kho",
     ('    cutoff = datetime.date.today() - datetime.timedelta(days=MAX_AGE_DAYS)',
      '    cutoff = datetime.date(1970, 1, 1)'),
     [7]),
    ("gỡ lời gọi cổng khỏi `--recent-titles` (cổng sống nhưng không ai gọi)",
     ('        print_baomoi_gate(repo_root, collect_existing_urls(json.loads(html[s:e])))',
      '        pass'),
     [8]),
]


def tu_kiem() -> int:
    goc = (SCRIPTS / "add_news.py").read_text(encoding="utf-8")
    print("TỰ KIỂM — dựng bản add_news.py đã gỡ dòng bảo vệ, các ca đã khai PHẢI ĐỎ")
    print("═" * 78)
    hong = 0
    for nhan, (tim, thay), ca_phai_do in BAN_HONG:
        if goc.count(tim) != 1:
            print(f"  ✗ {nhan}\n        │ KHÔNG áp được phép thay: tìm thấy "
                  f"{goc.count(tim)} chỗ khớp (cần đúng 1). Mã nguồn đã đổi → sửa lại test.")
            hong += 1
            continue
        # Bản hỏng phải nằm TRONG scripts/ chứ không phải thư mục tạm: ca 8 chạy nó như một
        # script thật, mà nó tự suy repo_root = thư mục cha của chính mình. Để ở /tmp thì ca 8
        # đỏ vì không tìm thấy index.html — đỏ vì lý do sai thì không chứng minh được gì.
        f = SCRIPTS / ".add_news_tu_kiem.py"
        try:
            f.write_text(goc.replace(tim, thay), encoding="utf-8")
            env = dict(os.environ, ADDNEWS_MOD=str(f))
            r = subprocess.run([sys.executable, str(pathlib.Path(__file__).resolve())],
                               capture_output=True, text=True, env=env)
        finally:
            f.unlink(missing_ok=True)
        # CHỈ lấy dòng ca (thụt 2 dấu cách) — dòng tổng kết cũng bắt đầu bằng "✗".
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
    print(f"TEST CỔNG BÁO MỚI — mọi ca 'PHẢI NHẮC' phải thật sự nhắc\n(bản đang thử: {MOD_PATH})")
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
            for dong in (out or "(không có đầu ra)").strip().split("\n")[:8]:
                print(f"        │ {dong}")
    print("─" * 78)
    if hong:
        print(f"✗ {hong}/{len(CA)} ca HỎNG — cổng Báo Mới không còn chặn đúng, sửa trước khi quét tin.")
        return 1
    print(f"✓ {len(CA)}/{len(CA)} ca đạt — cổng Báo Mới còn sống.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
