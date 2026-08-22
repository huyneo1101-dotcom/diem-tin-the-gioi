#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TEST HỒI QUY CHO MỤC "BỊ LOẠI" của scripts/add_news.py — luật KHÔNG CÓ TRẦN.

Huy chốt 02/08/2026 nguyên văn: *"bị loại chỉ là những bài không đúng chủ đề hoặc không nằm
trong khung ngày cho phép. không có số lượng tối đa cho bài bị loại."* Trần cũ (20 tổng /
10 phần Báo Mới) gỡ ngày 22/08/2026.

⚠ VÌ SAO CÓ FILE NÀY. Trần là loại hỏng CÂM hoàn hảo: đặt lại một con số thì mục Bị loại chỉ
ngắn đi, phiên quét vẫn xanh, bản tin vẫn gửi, không lệnh nào báo lỗi — và bài người dùng
đáng lẽ được rà để 👍 cứu thì lặng lẽ không bao giờ hiện ra. Chiều ngược cũng phải canh: gỡ
trần quá tay mà nuốt luôn phép chống trùng thì mục Bị loại đầy bài lặp.

Đã vấp 02/08/2026: hạ hai hằng số về 0 thì nhánh (b) `len(clean) >= REJECTED_PER_RUN -
len(baomoi_rejects)` có vế phải ÂM, vòng lặp thoát ngay lượt đầu và tin agent chủ động loại
bị cắt SẠCH — hỏng ngược ý và hỏng câm. Ca 3 dưới đây canh đúng chiều đó.

Chạy:
    python3 tests/test-cong-bi-loai.py
    python3 tests/test-cong-bi-loai.py --tu-kiem   # chứng minh test này BẮT ĐƯỢC lỗi
"""
import datetime
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))

MOD_PATH = pathlib.Path(os.environ.get("ADDNEWS_MOD") or (SCRIPTS / "add_news.py"))


def _nap(path: pathlib.Path):
    spec = importlib.util.spec_from_file_location("add_news_bi_loai", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


AN = _nap(MOD_PATH)
HOM_NAY = datetime.date.today()
NGAY = HOM_NAY.isoformat()

# Lô ứng viên Báo Mới cố ý LỚN HƠN HẲN trần cũ (10) và lệch nặng về một chuyên mục, đúng
# hình dạng kho thật: xếp theo độ ưu tiên mà có trần thì một mục ăn hết slot.
SO_UNG_VIEN = 46
SO_AGENT_LOAI = 27


def _kho_baomoi(n=SO_UNG_VIEN):
    cats = ["Quân sự", "Kinh tế", "Ngoại giao", "Xã hội"]
    ra = []
    for i in range(n):
        c = cats[0] if i < n - 6 else cats[1 + (i % 3)]   # lệch nặng về mục đầu
        ra.append({"date": NGAY, "category": c, "title": "Ứng viên số %d" % i,
                   "sourceName": "Báo Mới", "topic": "bỏ đi",
                   "sourceUrl": "https://baomoi.com/ung-vien-%d.epi" % i,
                   "region": "Đông Nam Á"})
    return ra


def _agent_loai(n=SO_AGENT_LOAI):
    return [{"date": NGAY, "title": "Tin agent loại số %d" % i,
             "sourceName": "Reuters", "reason": "ngoài khung ngày",
             "sourceUrl": "https://reuters.com/agent-loai-%d" % i} for i in range(n)]


def _chay(du_lieu=None, ung_vien=None, agent_loai=None):
    """Gọi thẳng `gop_bi_loai` với kho Báo Mới giả đặt trong thư mục tạm."""
    tam = pathlib.Path(tempfile.mkdtemp(prefix="test-bi-loai-"))
    kho = _kho_baomoi() if ung_vien is None else ung_vien
    (tam / "baomoi-topics.json").write_text(
        json.dumps({"items": kho}, ensure_ascii=False), encoding="utf-8")
    data = {"worldNews": [], "usNews": [], "rejectedNews": []} if du_lieu is None else du_lieu
    return AN.gop_bi_loai(
        data, _agent_loai() if agent_loai is None else agent_loai,
        tam, NGAY, HOM_NAY)


def ca1_moi_ung_vien_baomoi_deu_vao():
    clean, bm, _kept, _p = _chay()
    return len(bm) == SO_UNG_VIEN, "vào %d/%d ứng viên Báo Mới" % (len(bm), SO_UNG_VIEN)


def ca2_du_ca_bon_chuyen_muc():
    _c, bm, _k, _p = _chay()
    so_muc = len({i.get("category") for i in bm})
    return so_muc == 4, "chỉ thấy %d/4 chuyên mục — lô lệch đã nuốt mất mục khác" % so_muc


def ca3_moi_tin_agent_loai_deu_vao():
    clean, _bm, _k, _p = _chay()
    return len(clean) == SO_AGENT_LOAI, \
        "vào %d/%d tin agent chủ động loại (đây là loại tin GIÁ TRỊ NHẤT của mục)" \
        % (len(clean), SO_AGENT_LOAI)


def ca4_lo_that_lon_van_khong_bi_cat():
    """Lô gấp bốn lần lô thường: một trần ẩn ở đâu đó sẽ lộ ra ở kích thước này."""
    clean, bm, _k, _p = _chay(ung_vien=_kho_baomoi(180), agent_loai=_agent_loai(120))
    return len(bm) == 180 and len(clean) == 120, \
        "lô lớn bị cắt: %d/180 ứng viên · %d/120 tin agent loại" % (len(bm), len(clean))


def ca5_doi_chung_chong_trung_van_con():
    """Chiều NỚI: gỡ trần không được nuốt luôn phép chống trùng."""
    kho = _kho_baomoi(5)
    data = {"worldNews": [{"sourceUrl": kho[0]["sourceUrl"]}], "usNews": [],
            "rejectedNews": [{"sourceUrl": kho[1]["sourceUrl"], "addedAt": NGAY}]}
    _c, bm, _k, _p = _chay(du_lieu=data, ung_vien=kho, agent_loai=[])
    urls = {i["sourceUrl"] for i in bm}
    return (len(bm) == 3 and kho[0]["sourceUrl"] not in urls
            and kho[1]["sourceUrl"] not in urls), \
        "phải bỏ 2 bài đã có (1 live + 1 đang nằm trong Bị loại), thực tế vào %d/5" % len(bm)


def ca6_doi_chung_tin_agent_xep_truoc():
    """Bỏ trần rồi thì thứ tự là thứ duy nhất còn giữ ưu tiên cho tin agent loại."""
    goc = (SCRIPTS / "add_news.py").read_text(encoding="utf-8") \
        if MOD_PATH.name == "add_news.py" else MOD_PATH.read_text(encoding="utf-8")
    neo = 'data["rejectedNews"] = clean + baomoi_rejects + kept_existing'
    return goc.count(neo) == 1, \
        "không tìm thấy đúng một chỗ ghép `clean` TRƯỚC `baomoi_rejects` — tin agent chủ " \
        "động loại hết được ưu tiên hiện trên đầu"


def ca7_khong_nhanh_nao_con_cat_theo_tran():
    """Soi TĨNH: cấm mọi trần theo số lượng quay lại trong thân `gop_bi_loai`."""
    nguon = MOD_PATH.read_text(encoding="utf-8")
    a = nguon.index("def gop_bi_loai(")
    b = nguon.index("\ndef ", a + 10)
    than = nguon[a:b]
    xau = [t for t in ("REJECTED_PER_RUN", "BAOMOI_REJECT_PER_RUN", "[:20]", "[:10]")
           if t in than]
    return not xau, "thân hàm còn dấu vết trần: %s" % ", ".join(xau)


CA = [
    ("1. MỌI ứng viên Báo Mới đều vào mục Bị loại (không trần)", ca1_moi_ung_vien_baomoi_deu_vao),
    ("2. Lô lệch nặng vẫn ra đủ 04 chuyên mục", ca2_du_ca_bon_chuyen_muc),
    ("3. MỌI tin agent chủ động loại đều vào (bẫy trần-0 đã vấp 02/08)", ca3_moi_tin_agent_loai_deu_vao),
    ("4. Lô gấp bốn lần vẫn không bị cắt (lộ trần ẩn)", ca4_lo_that_lon_van_khong_bi_cat),
    ("5. ĐỐI CHỨNG: phép chống trùng vẫn còn (chiều NỚI)", ca5_doi_chung_chong_trung_van_con),
    ("6. ĐỐI CHỨNG: tin agent loại vẫn xếp TRƯỚC ứng viên Báo Mới", ca6_doi_chung_tin_agent_xep_truoc),
    ("7. Soi tĩnh: không nhánh nào còn cắt theo trần", ca7_khong_nhanh_nao_con_cat_theo_tran),
]

BAN_HONG = [
    ("đặt lại trần 10 cho ứng viên Báo Mới",
     ("    while any(by_cat[c] for c in cats):",
      "    while len(baomoi_rejects) < 10 and any(by_cat[c] for c in cats):"),
     [1, 4]),
    ("đặt lại trần 20 cho tin agent chủ động loại",
     ("    clean = []\n    for it in rejected_new:",
      "    clean = []\n    for it in rejected_new:\n        if len(clean) >= 20:\n            break"),
     [3, 4]),
    ("bẫy trần-0 của 02/08: vế phải âm cắt sạch nhánh (b)",
     ("    clean = []\n    for it in rejected_new:",
      "    clean = []\n    for it in rejected_new:\n        if len(clean) >= 0 - len(baomoi_rejects):\n            break"),
     [3, 4]),
    ("bỏ vòng xoay chuyên mục (lô lệch nuốt hết mục khác)",
     ("    cats = sorted(by_cat, key=lambda c: REJECT_CATEGORY_ORDER.get(c, 9))",
      "    cats = sorted(by_cat, key=lambda c: REJECT_CATEGORY_ORDER.get(c, 9))[:1]"),
     [1, 2, 4]),
    ("gỡ phép chống trùng của ứng viên Báo Mới (chiều NỚI)",
     ("        if not it.get(\"title\") or not u or u in live_urls or u in existing_urls:\n            continue\n        by_cat[it.get(\"category\", \"\")].append(it)",
      "        by_cat[it.get(\"category\", \"\")].append(it)"),
     [5]),
    ("đảo thứ tự ghép: ứng viên Báo Mới đè lên tin agent loại",
     ('data["rejectedNews"] = clean + baomoi_rejects + kept_existing',
      'data["rejectedNews"] = baomoi_rejects + clean + kept_existing'),
     [6]),
]


def tu_kiem() -> int:
    goc = (SCRIPTS / "add_news.py").read_text(encoding="utf-8")
    print("TỰ KIỂM — dựng bản add_news.py đã gỡ dòng bảo vệ, các ca đã khai PHẢI ĐỎ")
    print("═" * 78)
    hong = 0
    for nhan, (tim, thay), ca_phai_do in BAN_HONG:
        if goc.count(tim) != 1:
            print("  ✗ %s\n        │ KHÔNG áp được phép thay: %d chỗ khớp (cần đúng 1)."
                  % (nhan, goc.count(tim)))
            hong += 1
            continue
        f = SCRIPTS / ".add_news_tu_kiem_bi_loai.py"
        try:
            f.write_text(goc.replace(tim, thay), encoding="utf-8")
            env = dict(os.environ, ADDNEWS_MOD=str(f))
            r = subprocess.run([sys.executable, str(pathlib.Path(__file__).resolve())],
                               capture_output=True, text=True, env=env)
        finally:
            f.unlink(missing_ok=True)
        do = {int(d[4:].split(".")[0]) for d in r.stdout.splitlines() if d.startswith("  ✗ ")}
        thieu = set(ca_phai_do) - do
        ok = not thieu
        print("  %s %s" % ("✓" if ok else "✗", nhan))
        print("        │ ca đỏ: %s · cần đỏ: %s"
              % (sorted(do) or "KHÔNG CÓ CA NÀO ĐỎ", ca_phai_do))
        if not ok:
            hong += 1
            print("        │ ⚠ ca %s VẪN XANH trên bản hỏng." % sorted(thieu))
    print("═" * 78)
    if hong:
        print("✗ %d/%d phép thử tự kiểm THẤT BẠI." % (hong, len(BAN_HONG)))
        return 1
    print("✓ %d/%d bản hỏng đều bị bắt — bộ test này có giá trị." % (len(BAN_HONG), len(BAN_HONG)))
    return 0


def main() -> int:
    if "--tu-kiem" in sys.argv:
        return tu_kiem()
    print("TEST MỤC BỊ LOẠI — luật KHÔNG CÓ TRẦN\n(bản đang thử: %s)" % MOD_PATH)
    print("─" * 78)
    hong = 0
    for ten, f in CA:
        try:
            ok, mota = f()
        except Exception as e:
            ok, mota = False, "nổ: %r" % e
        print("  %s %s%s" % ("✓" if ok else "✗", ten, "" if ok else "\n        │ " + mota))
        if not ok:
            hong += 1
    print("─" * 78)
    if hong:
        print("✗ %d/%d ca TRƯỢT — mục Bị loại đang bị cắt." % (hong, len(CA)))
        return 1
    print("✓ %d/%d ca đạt — mục Bị loại không còn trần nào." % (len(CA), len(CA)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
