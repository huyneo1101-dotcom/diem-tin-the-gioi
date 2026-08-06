#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CỔNG NGHIỆM THU phép đo THỨ HAI: một viện xuất bản dưới HAI TÊN MIỀN, bảng chỉ khai một.

VÌ SAO CẦN — `scripts/do_nguon_mot_muc.py` (dựng 06/08/2026) tự khai giới hạn của nó ngay
trong docstring: nó bắt được **hình dạng Lowy** (một tên miền, bài chia theo mục, mục nghiên
cứu chưa khai), KHÔNG bắt được **hình dạng ASPI** — viện xuất bản dưới hai tên miền khác nhau,
blog `aspistrategist.org.au` và báo cáo `aspi.org.au`, mà bảng feed chỉ khai một. Với ASPI thì
81/81 bài nằm ở GỐC tên miền blog nên rơi vào nhóm "phép đo không áp dụng" và không được nêu
lần nào. Hai hình dạng cần hai phép đo; tới trước cổng này mới có một.

Cơ chế gây vấp giống hệt lỗ đầu, và đó là lý do phải có phép đo chứ không phải vá tay: **không
dấu hiệu nào phát ra**. Tên miền blog ra bài đều mỗi ngày nên danh sách ứng viên vẫn đầy, mục
Think-tank trên web vẫn có bài mới mỗi sáng, không ai có lý do đi hỏi "còn thiếu gì". Vá tay
ASPI hôm nay thì viện thứ ba mai mốt vẫn hỏng y hệt và cũng im lặng y hệt.

    python3 tests/test-nguon-hai-mien.py

⚠️ CỔNG NÀY CỐ Ý KHÔNG CÓ `--tu-kiem` CỦA RIÊNG NÓ. Toàn bộ ca hành vi dưới đây là ca HỘP ĐEN:
chúng nạp `scripts/do_nguon_hai_mien.py` rồi gọi thẳng hàm với bảng tên miền GIẢ, nên một bản
cài đặt rỗng trượt ngay ca 01-05, còn một bản cài đặt ngây thơ (gom bừa theo tiền tố, hoặc lấy
hai mảnh cuối tên miền làm "cùng viện") trượt ngay ca 12-18. Không cần dựng bản hỏng để chứng
minh chúng có răng — chúng đo hành vi, không đo hình dạng mã nguồn. Phần chứng minh còn lại là
`--tu-kiem` CỦA CHÍNH `do_nguon_hai_mien.py`, và ca 22 dưới đây bắt buộc phải có nó.

════════════════════ HỢP ĐỒNG — `scripts/do_nguon_hai_mien.py` PHẢI CÓ ════════════════════

  cac_cap_lech(mien, co_duong) -> list[tuple[str, ...]]
      mien     : tập tên miền viện (hình dạng của `THINKTANK_DOMAINS`)
      co_duong : tập tên miền ĐÃ có đường quét tự động — feed RSS trong `THINKTANK_FEEDS`
                 HOẶC trang danh sách trong `THINKTANK_HTML`
      trả về   : danh sách các NHÓM LỆCH — nhóm tên miền cùng một viện mà đường quét phủ
                 tên miền này nhưng không phủ tên miền kia. Mỗi nhóm là một tuple tên miền
                 ĐÃ SẮP; danh sách trả về cũng đã sắp; và ĐÃ TRỪ mọi cặp khai trong DA_DUYET.
                 Nhóm mà CẢ HAI phía đều có đường quét, hoặc CẢ HAI phía đều không có, thì
                 KHÔNG phải nhóm lệch — cả viện thuộc diện WebSearch không phải là lỗi.

  DA_DUYET : dict — khoá là tuple tên miền ĐÃ SẮP, giá trị là lý do đã soi tận nơi (chuỗi).
             Đây là chỗ ghi kết quả triage, KHÔNG phải chỗ giấu cặp khó: mỗi dòng phải nói
             được đã soi cái gì. Bắt buộc có sẵn ba cặp đối chứng ở ca 12-14.

  bao_cao() -> int : in bảng ra stdout; trả 3 khi còn nhóm lệch CHƯA ai soi, 0 khi sạch.

════════════════════════════ BA CẶP KHÔNG PHẢI LỖI, ĐỪNG KÊU ════════════════════════════

  spf.org / spfusa.org         hai NHÁNH THẬT của cùng một quỹ (Sasakawa Nhật Bản và
                               Sasakawa Peace Foundation USA ở Washington) — hai ban biên
                               tập riêng, không phải một viện bị khai thiếu nửa
  agsi.org / agsiw.org         viện ĐỔI TÊN, `agsiw.org` redirect sang `agsi.org`; giữ cả
                               hai chỉ để bài cũ trong kho không bị guardrail chặn oan
  ctc.westpoint.edu /          HAI VIỆN KHÁC NHAU cùng trọ dưới tên miền một trường đại học
  mwi.westpoint.edu            (Combating Terrorism Center và Modern War Institute). Gom
                               theo tên miền mẹ mà không loại trường đại học là kêu oan
"""
import contextlib
import importlib.util
import io
import os
import pathlib
import sys

sys.dont_write_bytecode = True

REPO = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = pathlib.Path(
    os.environ.get("DO_NGUON_HAI_MIEN", REPO / "scripts" / "do_nguon_hai_mien.py"))
KHOE = pathlib.Path("/Users/Huy/Claude/HeThong/khoe.py")


def nap():
    """Nạp phép đo. Chưa có file thì trả None — cổng đỏ đủ ca, không nổ giữa chừng."""
    if not SCRIPT.exists():
        return None
    spec = importlib.util.spec_from_file_location("do_hai_mien_kiem", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _goi(mod, mien, co_duong):
    """Gọi hàm theo hợp đồng, chuẩn hoá kết quả thành tập các tuple đã sắp."""
    ra = mod.cac_cap_lech(set(mien), set(co_duong))
    return {tuple(sorted(n)) for n in ra}


# ── Bảng ca hành vi ────────────────────────────────────────────────────────────────────
# (số ca, tên, tập tên miền, tập đã có đường quét, nhóm PHẢI nêu hoặc None nếu KHÔNG được nêu)
CA_HANH_VI = [
    # ★ PHẢI NÊU — đúng bốn hình dạng của lỗ
    (1, "★ hình dạng ASPI: gốc tên chung, chỉ BLOG có đường quét",
     {"aspi.org.au", "aspistrategist.org.au"}, {"aspistrategist.org.au"},
     ("aspi.org.au", "aspistrategist.org.au")),
    (2, "★ chiều ngược: chỉ tên miền BÁO CÁO có đường quét",
     {"aspi.org.au", "aspistrategist.org.au"}, {"aspi.org.au"},
     ("aspi.org.au", "aspistrategist.org.au")),
    (3, "★ hình dạng tên miền CON: amti.csis.org có đường, csis.org không",
     {"csis.org", "amti.csis.org"}, {"amti.csis.org"},
     ("amti.csis.org", "csis.org")),
    (4, "★ blog đặt tên dạng the<tên>: thevienbien.org / vienbien.org",
     {"vienbien.org", "thevienbien.org"}, {"thevienbien.org"},
     ("thevienbien.org", "vienbien.org")),
    (5, "★ blog đặt tên dạng <tên>blog: vienbienblog.org / vienbien.org",
     {"vienbien.org", "vienbienblog.org"}, {"vienbien.org"},
     ("vienbien.org", "vienbienblog.org")),

    # đối chứng CHỐNG KÊU OAN — mỗi ca dựng sao cho một bản cài đặt ngây thơ SẼ nêu nhầm
    (10, "đối chứng — cả hai tên miền ĐỀU có đường quét ⇒ không lệch",
     {"aspi.org.au", "aspistrategist.org.au"}, {"aspi.org.au", "aspistrategist.org.au"}, None),
    (11, "đối chứng — cả hai ĐỀU chưa có đường quét ⇒ diện WebSearch, không phải lỗi",
     {"aspi.org.au", "aspistrategist.org.au"}, set(), None),
    (12, "đối chứng — spf.org / spfusa.org là HAI NHÁNH thật của cùng quỹ",
     {"spf.org", "spfusa.org"}, {"spf.org"}, None),
    (13, "đối chứng — agsi.org / agsiw.org là viện ĐỔI TÊN",
     {"agsi.org", "agsiw.org"}, {"agsi.org"}, None),
    (14, "đối chứng — ctc/mwi.westpoint.edu là HAI VIỆN trọ chung tên miền đại học",
     {"ctc.westpoint.edu", "mwi.westpoint.edu"}, {"mwi.westpoint.edu"}, None),
    (15, "đối chứng — iseas/rsis.edu.sg chung ĐUÔI công cộng edu.sg, không cùng viện",
     {"iseas.edu.sg", "rsis.edu.sg"}, {"rsis.edu.sg"}, None),
    (16, "đối chứng — cepa.org / ceps.eu chung 3 ký tự đầu, là hai viện khác nhau",
     {"cepa.org", "ceps.eu"}, {"cepa.org"}, None),
    (17, "đối chứng — iss.europa.eu / issafrica.org: 'iss' nằm ở TÊN MIỀN CON, không phải "
         "tên đăng ký",
     {"iss.europa.eu", "issafrica.org"}, {"issafrica.org"}, None),
    (18, "đối chứng — hai viện không liên quan gì nhau",
     {"rand.org", "cato.org"}, {"rand.org"}, None),
]


def chay():
    """Trả danh sách (tên ca, đạt, lời). Ca có tiền tố ★ là ca PHẢI NÊU."""
    ra = []
    mod = nap()

    # ── 00 hợp đồng tối thiểu: có file và có hàm
    co_ham = bool(mod) and callable(getattr(mod, "cac_cap_lech", None))
    ra.append((
        "★ 00 có phép đo dò viện xuất bản dưới HAI tên miền",
        co_ham,
        f"thiếu {SCRIPT} hoặc thiếu hàm cac_cap_lech(mien, co_duong) — xem HỢP ĐỒNG trong "
        "docstring cổng này",
    ))

    for so, ten, mien, co_duong, mong in CA_HANH_VI:
        nhan = f"{'★ ' if mong else ''}{so:02d} {ten}"
        if not co_ham:
            ra.append((nhan, False, "chưa có phép đo để gọi"))
            continue
        try:
            kq = _goi(mod, mien, co_duong)
        except Exception as e:                       # noqa: BLE001 — lỗi nào cũng là ca đỏ
            ra.append((nhan, False, f"gọi cac_cap_lech ném lỗi: {type(e).__name__}: {e}"))
            continue
        if mong:
            ra.append((nhan, mong in kq,
                       f"phải nêu nhóm {mong}, nêu thực tế: {sorted(kq) or 'KHÔNG NÊU GÌ'}"))
        else:
            ra.append((nhan, not kq,
                       f"kêu oan — không được nêu gì, nêu thực tế: {sorted(kq)}"))

    # ── 21 bảng đã duyệt phải đúng hình dạng và phải nói được lý do
    if mod is None:
        ra.append(("★ 21 DA_DUYET khai đủ ba cặp đối chứng kèm lý do", False,
                   "chưa có phép đo"))
    else:
        dd = getattr(mod, "DA_DUYET", None)
        hinh_dang = isinstance(dd, dict) and all(
            isinstance(k, tuple) and len(k) >= 2 and tuple(sorted(k)) == k
            and isinstance(v, str) and len(v) >= 40 for k, v in dd.items())
        ra.append((
            "★ 21 DA_DUYET là dict{tuple đã sắp: lý do ≥ 40 ký tự}",
            bool(dd) and hinh_dang,
            "DA_DUYET thiếu, sai hình dạng, hoặc có dòng không nói được đã soi cái gì — "
            "một dòng trống nghĩa là cặp đó bị GIẤU chứ không phải đã duyệt",
        ))

    # ── 22 phép đo phải tự chứng minh được là nó bắt được lỗi
    nguon = SCRIPT.read_text(encoding="utf-8") if SCRIPT.exists() else ""
    so_ban_hong = nguon.count('    ("') if "BAN_HONG" in nguon else 0
    ra.append((
        "★ 22 phép đo có --tu-kiem kèm ít nhất 06 bản hỏng",
        "--tu-kiem" in nguon and "BAN_HONG" in nguon and so_ban_hong >= 6,
        "thiếu --tu-kiem hoặc bảng BAN_HONG quá mỏng — mỗi lớp vá (gom theo tên miền con · "
        "gom theo gốc tên · ngưỡng tiền tố · bảng ngoại lệ · loại tên miền đại học · điều "
        "kiện LỆCH) phải có một bản hỏng canh",
    ))

    # ── 23 nạp vào khoe.py, không thì cổng không ai chạy
    khoe = KHOE.read_text(encoding="utf-8") if KHOE.exists() else ""
    for ten_file in ("test-nguon-hai-mien.py", "do_nguon_hai_mien.py"):
        ra.append((
            f"★ 23 {ten_file} đã nạp vào BO_TEST của khoe.py",
            ten_file in khoe,
            f"chưa khai {ten_file} trong khoe.py ⇒ hỏng cũng không ai biết",
        ))

    # ── 24 CA VÀNG trên bảng THẬT: mọi nhóm lệch có thật đều đã được soi
    if mod is None or not callable(getattr(mod, "bao_cao", None)):
        ra.append(("★ 24 ca vàng — bảng nguồn THẬT không còn nhóm lệch nào chưa soi", False,
                   "chưa có bao_cao() để chạy trên bảng thật"))
    else:
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                ma = mod.bao_cao()
            loi = ("bao_cao() trả %r — còn nhóm lệch chưa ai soi. Việc phải làm: mở trang "
                   "viện xem tên miền còn thiếu có feed/trang danh sách nào không; có thì "
                   "khai vào THINKTANK_FEEDS hoặc THINKTANK_HTML, không có thì ghi một dòng "
                   "DA_DUYET kèm lý do đã soi.\n%s" % (ma, buf.getvalue().rstrip()))
        except Exception as e:                       # noqa: BLE001
            ma, loi = None, f"bao_cao() ném lỗi: {type(e).__name__}: {e}"
        ra.append(("★ 24 ca vàng — bảng nguồn THẬT không còn nhóm lệch nào chưa soi",
                   ma == 0, loi))
    return ra


def main():
    ra = chay()
    hong = 0
    for ten, dat, loi in ra:
        print(("  ✓ " if dat else "  ✗ ") + ten + ("" if dat else "  — " + loi))
        hong += 0 if dat else 1
    print(f"\n{len(ra) - hong}/{len(ra)} ca đạt" + ("" if not hong else f" · {hong} KHÔNG ĐẠT"))
    return 1 if hong else 0


if __name__ == "__main__":
    sys.exit(main())
