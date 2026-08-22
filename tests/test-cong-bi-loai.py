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



# ══ CỔNG BÀI ĐƯỢC 👍 (dựng 22/08/2026, việc 4 trong chốt 02/08 của Huy) ══════════════
NAY = datetime.datetime.now(datetime.timezone.utc)


def _moc(ngay_truoc):
    return (NAY - datetime.timedelta(days=ngay_truoc)).isoformat().replace("+00:00", "Z")


def _thich(*muc):
    """muc = (url, so_ngay_truoc). Trả thư mục repo giả có preferences.json."""
    tam = pathlib.Path(tempfile.mkdtemp(prefix="test-thich-"))
    (tam / "preferences.json").write_text(json.dumps({
        "liked": [{"item_id": u, "title": "Bài %s" % u[-3:], "category": "Kinh tế",
                   "source": "Reuters", "n": 1, "updated_at": _moc(d)}
                  for u, d in muc]}, ensure_ascii=False), encoding="utf-8")
    return tam


DATA_TRONG = {"worldNews": [], "usNews": [], "rejectedNews": []}


def ca8_bai_thich_chua_nap_phai_hien():
    tam = _thich(("https://x.test/a01", 1), ("https://x.test/a02", 3))
    ra = AN.bi_loai_duoc_thich(tam, DATA_TRONG)
    return len(ra) == 2, "chỉ nêu %d/2 bài đã 👍 mà chưa nạp" % len(ra)


def ca9_bai_da_bi_don_khoi_muc_van_phai_hien():
    """Mục Bị loại tự dọn sau 1 ngày — giao với `rejectedNews` là mất sạch bài 👍 muộn."""
    tam = _thich(("https://x.test/a01", 2))
    ra = AN.bi_loai_duoc_thich(tam, DATA_TRONG)   # rejectedNews RỖNG
    return len(ra) == 1 and ra[0]["con_trong_muc"] is False,         "bài đã bị dọn khỏi mục Bị loại vẫn phải được nêu, thực tế nêu %d bài" % len(ra)


def ca10_doi_chung_bai_da_nap_thi_im():
    tam = _thich(("https://x.test/a01", 1))
    data = {"worldNews": [{"sourceUrl": "https://x.test/a01"}], "usNews": [], "rejectedNews": []}
    ra = AN.bi_loai_duoc_thich(tam, data)
    return ra == [], "bài đã nạp rồi mà cổng vẫn nhắc — kêu oan mỗi lượt quét"


def ca11_doi_chung_thich_qua_lau_thi_im():
    tam = _thich(("https://x.test/a01", AN.BI_LOAI_THICH_SO_NGAY + 3))
    ra = AN.bi_loai_duoc_thich(tam, DATA_TRONG)
    return ra == [], "bài 👍 quá %d ngày vẫn bị lôi lên — hết là tin" % AN.BI_LOAI_THICH_SO_NGAY


def ca12_thieu_field_liked_phai_KEU():
    tam = pathlib.Path(tempfile.mkdtemp(prefix="test-thich-thieu-"))
    (tam / "preferences.json").write_text(json.dumps({"stats": [], "items": []}),
                                          encoding="utf-8")
    try:
        AN.bi_loai_duoc_thich(tam, DATA_TRONG)
    except AN.LoiNguonThich:
        return True, ""
    return False, "preferences.json thiếu field `liked` mà cổng IM — cổng câm vĩnh viễn " \
                  "trong khi workflow sync-preferences đã chết"


def ca13_khong_doc_duoc_preferences_phai_KEU():
    tam = pathlib.Path(tempfile.mkdtemp(prefix="test-thich-hong-"))
    try:
        AN.bi_loai_duoc_thich(tam, DATA_TRONG)   # không hề có file
    except AN.LoiNguonThich:
        return True, ""
    return False, "không có preferences.json mà cổng IM — im ở đây không phân biệt được " \
                  "với «không có bài nào được thích»"


def ca14_cong_phai_nam_tren_duong_di_cua_lenh_phien_quet():
    """Cổng sống mà không ai gọi thì y như cổng chết."""
    # Chạy MOD_PATH chứ không phải add_news.py thật: lúc `--tu-kiem` thì MOD_PATH là bản
    # hỏng: chạy bản thật ở đây thì ca luôn xanh và bản hỏng "gỡ lời gọi cổng" không bị bắt.
    # Bản hỏng nằm trong scripts/ nên nó vẫn tự suy đúng repo_root.
    r = subprocess.run([sys.executable, str(MOD_PATH), "--recent-titles", "1"],
                       capture_output=True, text=True, cwd=str(REPO))
    return "CỔNG BÀI 👍" in r.stdout, \
        "chạy `--recent-titles` mà KHÔNG in cổng bài 👍 (mã %s)" % r.returncode

CA = [
    ("1. MỌI ứng viên Báo Mới đều vào mục Bị loại (không trần)", ca1_moi_ung_vien_baomoi_deu_vao),
    ("2. Lô lệch nặng vẫn ra đủ 04 chuyên mục", ca2_du_ca_bon_chuyen_muc),
    ("3. MỌI tin agent chủ động loại đều vào (bẫy trần-0 đã vấp 02/08)", ca3_moi_tin_agent_loai_deu_vao),
    ("4. Lô gấp bốn lần vẫn không bị cắt (lộ trần ẩn)", ca4_lo_that_lon_van_khong_bi_cat),
    ("5. ĐỐI CHỨNG: phép chống trùng vẫn còn (chiều NỚI)", ca5_doi_chung_chong_trung_van_con),
    ("6. ĐỐI CHỨNG: tin agent loại vẫn xếp TRƯỚC ứng viên Báo Mới", ca6_doi_chung_tin_agent_xep_truoc),
    ("7. Soi tĩnh: không nhánh nào còn cắt theo trần", ca7_khong_nhanh_nao_con_cat_theo_tran),
    ("8. Bài đã 👍 mà chưa nạp → PHẢI hiện", ca8_bai_thich_chua_nap_phai_hien),
    ("9. Bài đã bị dọn khỏi mục Bị loại vẫn PHẢI hiện", ca9_bai_da_bi_don_khoi_muc_van_phai_hien),
    ("10. ĐỐI CHỨNG: bài đã nạp rồi thì im (chiều NỚI)", ca10_doi_chung_bai_da_nap_thi_im),
    ("11. ĐỐI CHỨNG: 👍 quá cửa sổ ngày thì im (chiều NỚI)", ca11_doi_chung_thich_qua_lau_thi_im),
    ("12. Thiếu field `liked` → PHẢI KÊU chứ không im", ca12_thieu_field_liked_phai_KEU),
    ("13. Không đọc được preferences.json → PHẢI KÊU", ca13_khong_doc_duoc_preferences_phai_KEU),
    ("14. Cổng PHẢI nằm trên đường đi của `--recent-titles`", ca14_cong_phai_nam_tren_duong_di_cua_lenh_phien_quet),
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
    # ── cổng bài được 👍 ────────────────────────────────────────────────────────
    ("lỗi đọc preferences.json thoát êm (fail-open, đúng lối cổng chết)",
     ('        raise LoiNguonThich("không đọc được preferences.json: %r" % e)',
      '        return []'),
     [13]),
    ("thiếu field `liked` coi như sạch (cổng câm khi workflow chết)",
     ('    if "liked" not in pref:', '    if False and "liked" not in pref:'),
     [12]),
    ("giao với `rejectedNews` (mất sạch bài 👍 muộn — mục tự dọn sau 1 ngày)",
     ('        if not u or u in da_nap:\n            continue',
      '        if not u or u in da_nap or u not in con_trong_muc:\n            continue'),
     [8, 9]),
    ("gỡ phép loại bài ĐÃ NẠP (cổng nhắc oan mỗi lượt quét)",
     ('        if not u or u in da_nap:\n            continue',
      '        if not u:\n            continue'),
     [10]),
    ("gỡ cửa sổ ngày (lôi cả bài 👍 từ ba tuần trước)",
     ('        if khi is not None and (bay_gio - khi).days > BI_LOAI_THICH_SO_NGAY:\n            continue',
      '        pass'),
     [11]),
    ("gỡ lời gọi cổng khỏi `--recent-titles` (cổng sống nhưng không ai gọi)",
     ('        print_bi_loai_thich_gate(repo_root, _d)', '        pass'),
     [14]),
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
