#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TỰ DÒ viện xuất bản dưới HAI TÊN MIỀN mà bảng nguồn chỉ khai một — phép đo THỨ HAI.

VÌ SAO CÓ PHÉP ĐO NÀY. `scripts/do_nguon_mot_muc.py` (dựng 06/08/2026) bắt được **hình dạng
Lowy**: một tên miền, bài chia theo mục, mục nghiên cứu chưa khai. Nó tự khai giới hạn ngay
trong docstring — nó KHÔNG bắt được **hình dạng ASPI**: viện xuất bản dưới hai tên miền khác
nhau, blog `aspistrategist.org.au` và báo cáo `aspi.org.au`, mà bảng chỉ khai một. Với ASPI thì
81/81 bài nằm ở GỐC tên miền blog nên rơi vào nhóm "phép đo không áp dụng" và chưa từng được
nêu lần nào. Hai hình dạng cần hai phép đo; đây là phép đo thứ hai.

CƠ CHẾ GÂY VẤP — giống hệt lỗ đầu, và đó mới là phần đáng sợ: **không dấu hiệu nào phát ra.**
Tên miền blog ra bài đều mỗi ngày nên danh sách ứng viên vẫn đầy, mục Think-tank trên web vẫn
có bài mới mỗi sáng, không ai có lý do đi hỏi "còn thiếu gì". Vá tay ASPI hôm nay thì viện thứ
ba mai mốt vẫn hỏng y hệt, cùng một cách, và cũng im lặng y hệt.

PHÉP ĐO. Gom tên miền trong `THINKTANK_DOMAINS` thành NHÓM CÙNG MỘT VIỆN, rồi đối chiếu với
tập tên miền ĐÃ có đường quét tự động (feed trong `THINKTANK_FEEDS` hoặc trang danh sách trong
`THINKTANK_HTML`). Nhóm nào đường quét phủ tên miền này mà không phủ tên miền kia thì **LỆCH** —
đó đúng là hình dạng của lỗ. Cả nhóm đều có đường, hoặc cả nhóm đều không, thì KHÔNG lệch: cả
viện thuộc diện WebSearch là một lựa chọn đã khai, không phải một lỗ.

    python3 scripts/do_nguon_hai_mien.py             # báo cáo; mã 3 khi còn nhóm chưa soi
    python3 scripts/do_nguon_hai_mien.py --tu-kiem   # chứng minh phép đo BẮT ĐƯỢC lỗi

HAI HÌNH DẠNG GOM, cố ý tách rời vì chúng bảo vệ hai ca khác nhau:
  (a) TÊN MIỀN CON của cùng một tên đăng ký — `amti.csis.org` · `chinapower.csis.org` ·
      `interpret.csis.org` · `csis.org`.
  (b) CHUNG GỐC TÊN ĐĂNG KÝ — `aspi.org.au` / `aspistrategist.org.au`. Phủ luôn lối đặt tên
      blog `the<tên>` (`thevienbien.org` / `vienbien.org`) và `<tên>blog` · `<tên>strategist`.

⚠️ BA CÁI BẪY ĐÃ ĐO ĐƯỢC, dựng sai là kêu oan hàng loạt — mà bảng bị kêu oan vài lần thì hết
được đọc, lúc có lỗ thật cũng không ai nhìn:

  1. PHẢI SO TRÊN TÊN ĐĂNG KÝ, KHÔNG so trên cả chuỗi tên miền. `iss.europa.eu` và
     `issafrica.org` khớp nhau ở chuỗi "iss", nhưng "iss" bên trái là TÊN MIỀN CON còn tên đăng
     ký của nó là "europa" — EUISS và ISS Africa là hai viện khác hẳn nhau.
  2. PHẢI BIẾT ĐUÔI CÔNG CỘNG NHIỀU MẢNH. `iseas.edu.sg` và `rsis.edu.sg` lấy hai mảnh cuối thì
     ra chung "edu.sg", trong khi tên đăng ký thật là "iseas" và "rsis" — hai viện Singapore
     khác nhau. Thiếu bảng `DUOI_NHIEU_MANH` là mọi viện Úc gom một cục, mọi viện Singapore gom
     một cục.
  3. NGƯỠNG TIỀN TỐ CHUNG PHẢI ≥ 4 KÝ TỰ. `cepa.org` và `ceps.eu` chung 3 ký tự đầu mà là hai
     viện khác nhau (CEPA và CEPS).

Và một bảng loại trừ theo TÊN MIỀN TRỌ CHUNG: `ctc.westpoint.edu` (Combating Terrorism Center)
với `mwi.westpoint.edu` (Modern War Institute) là HAI VIỆN KHÁC NHAU cùng trọ dưới tên miền một
trường đại học. Gom theo hình dạng (a) mà không loại tên miền đại học là kêu oan.

⚠️ HƯỚNG LỆCH CÓ CHỦ Ý: phép gom cố ý RỘNG. Gom thừa một nhóm thì tốn đúng một dòng `DA_DUYET`;
gom hụt thì lỗ nằm im tiếp — mà im lặng chính là thứ phép đo này sinh ra để chặn.
"""
import importlib.util
import itertools
import os
import pathlib
import sys
import urllib.parse

sys.dont_write_bytecode = True

REPO = pathlib.Path(__file__).resolve().parent.parent
ADD_ANALYSES = pathlib.Path(
    os.environ.get("ADD_ANALYSES", REPO / "scripts" / "add_analyses.py"))

# Đuôi công cộng NHIỀU MẢNH — bẫy số 2 ở docstring. Lấy hai mảnh cuối làm tên miền đăng ký thì
# `iseas.edu.sg` và `rsis.edu.sg` ra chung "edu.sg" và bị gom thành một viện.
# ⚠️ Đây KHÔNG phải bản đầy đủ của Public Suffix List — chỉ cần phủ những đuôi mà bảng nguồn
# think-tank thật sự dùng, cộng vài đuôi cùng họ để viện mới thêm vào không vấp ngay. Thêm một
# đuôi vào đây là AN TOÀN (tách nhóm ra); thiếu một đuôi mới là chỗ gom oan.
DUOI_NHIEU_MANH = frozenset({
    "org.au", "edu.au", "com.au", "net.au", "gov.au",
    "co.uk", "org.uk", "ac.uk", "gov.uk",
    "or.jp", "co.jp", "ne.jp", "ac.jp", "go.jp",
    "edu.sg", "org.sg", "com.sg", "gov.sg",
    "org.za", "co.za", "ac.za",
    "org.in", "edu.in", "co.in", "ac.in",
    "org.il", "ac.il", "co.il",
    "com.br", "com.cn", "org.cn", "edu.cn", "co.kr", "or.kr", "re.kr",
    "com.tr", "org.tw", "com.tw", "edu.tw", "org.nz", "co.nz", "ac.nz",
})

# Tên miền mà NHIỀU VIỆN KHÁC NHAU cùng trọ — gom theo hình dạng (a) ở đây là kêu oan. Đo trên
# bảng thật 06/08/2026: `ctc.westpoint.edu` (Combating Terrorism Center) và `mwi.westpoint.edu`
# (Modern War Institute) là hai viện riêng, ngân sách riêng, ban biên tập riêng — chung nhau
# đúng cái tên miền của trường.
# ⚠️ Thêm một tên miền vào đây là TẮT phép đo cho mọi viện trọ dưới nó. Chỉ thêm tên miền của
# TỔ CHỨC CHỦ NHÀ (trường đại học, tập đoàn), đừng thêm tên miền của chính viện.
MIEN_TRO_CHUNG = frozenset({
    "westpoint.edu", "georgetown.edu", "columbia.edu", "harvard.edu", "stanford.edu",
    "mit.edu", "jhu.edu", "sydney.edu.au", "anu.edu.au", "nus.edu.sg", "ntu.edu.sg",
})

# Số ký tự đầu phải chung nhau thì mới coi là cùng một gốc tên — bẫy số 3. Hạ ngưỡng này là gom
# `cepa.org` với `ceps.eu`; nâng nó lên là bỏ sót `agsi.org` / `agsiw.org`.
NGUONG_TIEN_TO = 4

# Blog của viện hay đặt tên bằng cách dán "the" vào trước tên viện (`thevienbien.org` cho viện
# `vienbien.org`). Bóc tiền tố đó ra rồi mới so, nếu không thì hai tên chung tiền tố 0 ký tự.
TIEN_TO_BLOG = "the"

# Nhóm ĐÃ SOI TẬN NƠI rồi — kèm lý do, để lần chạy sau không kêu lại. Khoá là tuple tên miền ĐÃ
# SẮP; mọi tên miền nêu trong một khoá sẽ bị TRỪ khỏi nhóm chứa nó.
# ⚠️ Đây là chỗ ghi kết quả triage, KHÔNG phải chỗ giấu nhóm khó: mỗi dòng phải nói được đã soi
# cái gì, và cổng `tests/test-nguon-hai-mien.py` bắt lý do dài tối thiểu 40 ký tự — một dòng
# trống nghĩa là nhóm đó bị GIẤU chứ không phải đã duyệt.
DA_DUYET = {
    ("spf.org", "spfusa.org"):
        "Đã soi 06/08/2026 — HAI NHÁNH THẬT của cùng một quỹ Sasakawa, không phải một viện bị "
        "khai thiếu nửa: `spf.org` là quỹ mẹ ở Tokyo, `spfusa.org` là Sasakawa Peace Foundation "
        "USA đặt tại Washington DC, hai ban biên tập riêng và hai dòng xuất bản riêng. Nhánh "
        "Nhật đã có trang danh sách IINA trong THINKTANK_HTML; nhánh Mỹ thuộc diện WebSearch.",
    ("agsi.org", "agsiw.org"):
        "Đã soi 06/08/2026 — viện ĐỔI TÊN chứ không phải hai tên miền song song: `agsiw.org` "
        "redirect sang `agsi.org`. Giữ cả hai trong THINKTANK_DOMAINS chỉ để bài cũ trong kho "
        "còn mang url agsiw.org không bị guardrail domain chặn oan; khai thêm đường quét cho "
        "tên miền cũ là quét đúng nội dung đó lần thứ hai.",
    ("ctc.westpoint.edu", "mwi.westpoint.edu"):
        "Đã soi 06/08/2026 — HAI VIỆN KHÁC NHAU cùng trọ dưới tên miền của Học viện West Point: "
        "Combating Terrorism Center và Modern War Institute. MWI đã có feed riêng trong "
        "THINKTANK_FEEDS, CTC thuộc diện WebSearch (Cloudflare 403). Bảng MIEN_TRO_CHUNG đã "
        "tách chúng ra rồi; dòng này ghi lại để phiên sau khỏi soi lại từ đầu.",
    ("dialogo-americas.com", "thedialogue.org"):
        "Đã soi 06/08/2026 — phép gom dán chúng vào nhau vì sau khi bóc tiền tố 'the' thì hai "
        "tên chung 6 ký tự đầu ('dialog'), nhưng đây là hai nơi khác hẳn: `dialogo-americas.com` "
        "là tạp chí Diálogo Américas của Bộ Chỉ huy miền Nam Hoa Kỳ, còn `thedialogue.org` là "
        "viện Inter-American Dialogue ở Washington. Cả hai hiện đều thuộc diện WebSearch.",
}


def tach_ten(dom: str):
    """`amti.csis.org` -> ('csis.org', 'csis'). Trả (tên miền ĐĂNG KÝ, TÊN đăng ký).

    Tên đăng ký là nhãn đứng ngay trước đuôi công cộng — thứ duy nhất so được giữa hai viện.
    So trên cả chuỗi tên miền là dính bẫy số 1 (`iss.europa.eu` vs `issafrica.org`).
    """
    dom = (dom or "").lower().strip().strip(".")
    if dom.startswith("www."):
        dom = dom[4:]
    manh = [m for m in dom.split(".") if m]
    # Đuôi hai mảnh (`org.au`, `edu.sg`) thì tên đăng ký lùi thêm một nhãn nữa — bẫy số 2.
    so_manh = 3 if len(manh) >= 3 and ".".join(manh[-2:]) in DUOI_NHIEU_MANH else 2
    if len(manh) < so_manh:
        return dom, (manh[0] if manh else dom)
    return ".".join(manh[-so_manh:]), manh[-so_manh]


def goc_ten(ten: str) -> str:
    """Bóc tiền tố `the` của tên blog. Giữ nguyên khi bóc xong còn quá ngắn để so."""
    if ten.startswith(TIEN_TO_BLOG) and len(ten) > len(TIEN_TO_BLOG) + NGUONG_TIEN_TO:
        return ten[len(TIEN_TO_BLOG):]
    return ten


def chung_goc(ten_a: str, ten_b: str) -> bool:
    """Hai tên đăng ký có chung gốc không — dùng cho hình dạng (b)."""
    a, b = goc_ten(ten_a), goc_ten(ten_b)
    chung = 0
    for x, y in zip(a, b):
        if x != y:
            break
        chung += 1
    return chung >= NGUONG_TIEN_TO


def cung_vien(a: str, b: str) -> bool:
    """Hai tên miền có thuộc CÙNG MỘT VIỆN không."""
    dk_a, ten_a = tach_ten(a)
    dk_b, ten_b = tach_ten(b)
    # Tên miền trọ chung: nhiều viện dưới một mái, không suy ra được gì từ tên miền.
    if dk_a in MIEN_TRO_CHUNG or dk_b in MIEN_TRO_CHUNG:
        return False
    if dk_a == dk_b:                       # (a) tên miền con của cùng một tên đăng ký
        return True
    if chung_goc(ten_a, ten_b):            # (b) chung gốc tên đăng ký
        return True
    return False


def gom_nhom(mien):
    """Gom tên miền thành các nhóm CÙNG VIỆN (>= 2 tên miền). Trả list tuple đã sắp."""
    mien = sorted({(d or "").lower().strip() for d in mien if (d or "").strip()})
    cha = {d: d for d in mien}

    def tim(x):
        while cha[x] != x:
            cha[x] = cha[cha[x]]
            x = cha[x]
        return x

    for a, b in itertools.combinations(mien, 2):
        if cung_vien(a, b):
            ra, rb = tim(a), tim(b)
            if ra != rb:
                cha[rb] = ra

    nhom = {}
    for d in mien:
        nhom.setdefault(tim(d), []).append(d)
    return sorted(tuple(sorted(v)) for v in nhom.values() if len(v) > 1)


def _tru_da_duyet(nhom):
    """Bỏ khỏi nhóm mọi tên miền nêu trong một khoá DA_DUYET nằm TRỌN trong nhóm đó."""
    bo = set()
    for khoa in DA_DUYET:
        if set(khoa) <= set(nhom):
            bo |= set(khoa)
    return tuple(d for d in nhom if d not in bo)


def cac_cap_lech(mien, co_duong):
    """Nhóm cùng viện mà đường quét phủ tên miền này nhưng KHÔNG phủ tên miền kia.

    Cả nhóm đều có đường, hoặc cả nhóm đều không, thì KHÔNG lệch — cả viện thuộc diện WebSearch
    là một lựa chọn đã khai, không phải một lỗ.
    """
    co_duong = {(d or "").lower().strip() for d in co_duong}
    ra = []
    for nhom in gom_nhom(mien):
        con = _tru_da_duyet(nhom)
        if len(con) < 2:
            continue
        co = [d for d in con if d in co_duong]
        khong = [d for d in con if d not in co_duong]
        if co and khong:
            ra.append(con)
    return sorted(ra)


def _mien_cua(url: str) -> str:
    return urllib.parse.urlparse(url).netloc.replace("www.", "").lower()


def nap_bang():
    """(THINKTANK_DOMAINS, tập tên miền ĐÃ có đường quét tự động).

    Nạp hỏng thì KÊU mã 2 chứ không trả rỗng — bảng rỗng và bảng không đọc được cho ra cùng một
    báo cáo sạch, mà đó là hai chuyện khác hẳn nhau.
    """
    try:
        spec = importlib.util.spec_from_file_location("aa_do_hai_mien", ADD_ANALYSES)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mien = set(mod.THINKTANK_DOMAINS)
        co_duong = {_mien_cua(f[1]) for f in mod.THINKTANK_FEEDS}
        co_duong |= {_mien_cua(h[1]) for h in mod.THINKTANK_HTML}
    except SystemExit:
        raise
    except Exception as e:                       # noqa: BLE001
        print(f"✗ Không đọc được bảng nguồn ({ADD_ANALYSES}): {type(e).__name__}: {e}",
              file=sys.stderr)
        raise SystemExit(2)
    if not mien or not co_duong:
        print(f"✗ Bảng nguồn rỗng bất thường ({ADD_ANALYSES}): {len(mien)} tên miền, "
              f"{len(co_duong)} tên miền có đường quét", file=sys.stderr)
        raise SystemExit(2)
    return mien, co_duong


def bao_cao() -> int:
    mien, co_duong = nap_bang()
    nhom_het = gom_nhom(mien)
    lech = cac_cap_lech(mien, co_duong)
    print(f"=== DÒ VIỆN XUẤT BẢN DƯỚI HAI TÊN MIỀN ({len(mien)} tên miền · "
          f"{len(co_duong)} có đường quét · {len(nhom_het)} nhóm cùng viện) ===\n")

    print(f"★ NHÓM LỆCH — có đường quét cho tên miền này, KHÔNG có cho tên miền kia ({len(lech)})")
    if lech:
        for n in lech:
            co = [d for d in n if d in co_duong]
            khong = [d for d in n if d not in co_duong]
            print(f"  ★ {' · '.join(n)}")
            print(f"      có đường quét: {', '.join(co)}")
            print(f"      CHƯA có      : {', '.join(khong)}")
    else:
        print("  (không có)")

    print(f"\n✓ NHÓM ĐỀU NHAU — cả nhóm có đường, hoặc cả nhóm chưa có ({len(nhom_het) - len(lech)})")
    for n in nhom_het:
        if n in lech:
            continue
        con = _tru_da_duyet(n)
        nhan = "đã duyệt" if len(con) < 2 else (
            "đều CÓ" if all(d in co_duong for d in con) else "đều CHƯA")
        print(f"  ✓ {' · '.join(n)}  [{nhan}]")
        for khoa in sorted(DA_DUYET):
            if set(khoa) <= set(n):
                print(f"      ↳ {DA_DUYET[khoa]}")

    if lech:
        print("\n⚠️ Nhóm lệch mà CHƯA ai soi: " + " · ".join(" · ".join(n) for n in lech))
        print("   Việc phải làm: mở trang của tên miền còn thiếu, đọc thẻ "
              "<link rel=\"alternate\"> tìm feed (đường đã tìm ra feed RUSI, CACI và "
              "ChinaPower). Có feed thì khai vào THINKTANK_FEEDS; quét được HTML thì khai vào "
              "THINKTANK_HTML kèm biểu thức đường dẫn bài; không có đường nào thì ghi một dòng "
              "vào DA_DUYET kèm lý do đã soi.")
        return 3
    return 0


# ─────────────────────────── tự kiểm ───────────────────────────

def _lech(mien, co_duong):
    """Gọi phép đo với bảng giả, trả tập nhóm lệch (mỗi nhóm một tuple đã sắp)."""
    return {tuple(n) for n in cac_cap_lech(set(mien), set(co_duong))}


def cac_ca():
    """[(tên ca, đạt, lời)] — ca có ★ là ca PHẢI NÊU."""
    ra = []

    # ── 01 ★ hình dạng ASPI: chung GỐC TÊN, khác tên miền đăng ký, chỉ blog có đường quét.
    # Chỉ lớp (b) cứu được ca này — hai tên miền đăng ký khác nhau nên lớp (a) không với tới.
    k = _lech({"aspi.org.au", "aspistrategist.org.au"}, {"aspistrategist.org.au"})
    ra.append(("★ 01 hình dạng ASPI — chung gốc tên, chỉ BLOG có đường quét ⇒ phải nêu",
               k == {("aspi.org.au", "aspistrategist.org.au")}, f"nêu thực tế: {sorted(k)}"))

    # ── 02 ★ hình dạng TÊN MIỀN CON, tên đăng ký NGẮN (3 ký tự).
    # Cố ý để tên đăng ký ngắn hơn NGUONG_TIEN_TO: lớp (b) không với tới, nên ca này đo ĐÚNG
    # lớp (a). Dùng tên 4+ ký tự thì cả hai lớp cùng che, gỡ một lớp mà ca vẫn xanh.
    k = _lech({"vbc.org", "blog.vbc.org"}, {"blog.vbc.org"})
    ra.append(("★ 02 tên miền CON, tên đăng ký 3 ký tự ⇒ phải nêu (đo đúng lớp gom (a))",
               k == {("blog.vbc.org", "vbc.org")}, f"nêu thực tế: {sorted(k)}"))

    # ── 03 ★ blog đặt tên dạng the<tên>
    k = _lech({"vienbien.org", "thevienbien.org"}, {"thevienbien.org"})
    ra.append(("★ 03 blog dạng the<tên> ⇒ phải nêu",
               k == {("thevienbien.org", "vienbien.org")}, f"nêu thực tế: {sorted(k)}"))

    # ── 04 đối chứng — cả nhóm ĐỀU có đường quét
    k = _lech({"aspi.org.au", "aspistrategist.org.au"},
              {"aspi.org.au", "aspistrategist.org.au"})
    ra.append(("04 đối chứng — cả nhóm ĐỀU có đường quét ⇒ KHÔNG nêu", not k,
               f"kêu oan: {sorted(k)}"))

    # ── 05 đối chứng — cả nhóm ĐỀU chưa có đường quét (diện WebSearch, đã khai, không phải lỗ)
    k = _lech({"aspi.org.au", "aspistrategist.org.au"}, set())
    ra.append(("05 đối chứng — cả nhóm ĐỀU chưa có đường ⇒ KHÔNG nêu", not k,
               f"kêu oan diện WebSearch: {sorted(k)}"))

    # ── 06 đối chứng — bẫy 3: chung 3 ký tự đầu, hai viện khác nhau
    k = _lech({"cepa.org", "ceps.eu"}, {"cepa.org"})
    ra.append((f"06 đối chứng — cepa/ceps chung 3 ký tự (< ngưỡng {NGUONG_TIEN_TO}) ⇒ KHÔNG nêu",
               not k, f"gom oan hai viện khác nhau: {sorted(k)}"))

    # ── 07 đối chứng — bẫy 2: chung ĐUÔI CÔNG CỘNG nhiều mảnh
    k = _lech({"iseas.edu.sg", "rsis.edu.sg"}, {"rsis.edu.sg"})
    ra.append(("07 đối chứng — iseas/rsis chung đuôi công cộng edu.sg ⇒ KHÔNG nêu", not k,
               f"lấy hai mảnh cuối làm tên miền đăng ký nên gom oan: {sorted(k)}"))

    # ── 08 đối chứng — tên miền TRỌ CHUNG của một trường đại học.
    # Cố ý KHÔNG dùng cặp ctc/mwi.westpoint.edu: cặp đó nằm trong DA_DUYET nên có HAI lớp cùng
    # che, gỡ bảng MIEN_TRO_CHUNG mà ca vẫn xanh — không chứng minh được gì về bảng ấy.
    k = _lech({"cset.georgetown.edu", "sfs.georgetown.edu"}, {"cset.georgetown.edu"})
    ra.append(("08 đối chứng — hai viện trọ chung tên miền đại học ⇒ KHÔNG nêu", not k,
               f"gom oan hai viện cùng trọ một trường: {sorted(k)}"))

    # ── 09 đối chứng — bẫy 1: "iss" nằm ở TÊN MIỀN CON, không phải tên đăng ký
    k = _lech({"iss.europa.eu", "issafrica.org"}, {"issafrica.org"})
    ra.append(("09 đối chứng — iss.europa.eu / issafrica.org ⇒ KHÔNG nêu", not k,
               f"so trên cả chuỗi tên miền nên gom oan: {sorted(k)}"))

    # ── 10 ★ DA_DUYET phải TRỪ đúng nhóm đã soi (agsi/agsiw lệch thật, nhưng đã duyệt)
    k = _lech({"agsi.org", "agsiw.org"}, {"agsi.org"})
    ra.append(("★ 10 nhóm đã ghi DA_DUYET ⇒ KHÔNG nêu lại", not k,
               f"phép trừ DA_DUYET không chạy: {sorted(k)}"))

    # ── 11 ★ CA VÀNG trên bảng THẬT: mọi nhóm lệch đều đã được xử lý
    mien, co_duong = nap_bang()
    con = cac_cap_lech(mien, co_duong)
    ra.append(("★ 11 ca vàng — bảng nguồn THẬT không còn nhóm lệch nào chưa soi",
               not con,
               "chưa soi: " + " · ".join(" · ".join(n) for n in con) + " — khai đường quét cho "
               "tên miền còn thiếu, hoặc ghi một dòng DA_DUYET kèm lý do đã soi"))

    # ── 12/13 ★ bảng nguồn hỏng phải KÊU mã 2, không được trả bảng sạch.
    # HAI ca cho HAI NHÁNH khác nhau, cố ý không gộp: bảng RỖNG đi qua phép đo độ dài, còn bảng
    # KHÔNG NẠP ĐƯỢC đi qua nhánh bắt ngoại lệ. Gộp một ca thì bản hỏng gỡ nhánh này vẫn xanh
    # nhờ nhánh kia — ca dựng ở nhánh mà phép thay không đi qua (mục 17 CLAUDE.md).
    import tempfile
    global ADD_ANALYSES
    cu = ADD_ANALYSES
    for so, nhan, than, loi in (
        (12, "bảng nguồn RỖNG",
         "THINKTANK_DOMAINS = set()\nTHINKTANK_FEEDS = []\nTHINKTANK_HTML = []\n",
         "bảng rỗng bị nuốt — bảng rỗng và bảng đầy đủ ra cùng một báo cáo sạch"),
        (13, "bảng nguồn KHÔNG NẠP ĐƯỢC",
         "raise RuntimeError('bảng hỏng')\n",
         "bảng không nạp được bị nuốt — mất luôn tiếng kêu duy nhất"),
    ):
        try:
            with tempfile.TemporaryDirectory() as t:
                xau = pathlib.Path(t) / "hong.py"
                xau.write_text(than, encoding="utf-8")
                ADD_ANALYSES = xau
                try:
                    nap_bang()
                    ok = False
                except SystemExit as e:
                    ok = e.code == 2
        finally:
            ADD_ANALYSES = cu
        ra.append((f"★ {so} {nhan} ⇒ kêu mã 2, không trả bảng sạch", ok, loi))
    return ra


def tu_kiem_chay():
    ra = cac_ca()
    hong = 0
    for ten, dat, loi in ra:
        print(("  ✓ " if dat else "  ✗ ") + ten + ("" if dat else "  — " + loi))
        hong += 0 if dat else 1
    print(f"\n{len(ra) - hong}/{len(ra)} ca đạt" + ("" if not hong else f" · {hong} KHÔNG ĐẠT"))
    return 1 if hong else 0


def tu_kiem():
    """Dựng bản CHÍNH FILE NÀY đã gỡ đúng một lớp vá, rồi chứng minh ca tương ứng ĐỎ."""
    import hashlib
    import subprocess
    goc = pathlib.Path(__file__).read_text(encoding="utf-8")
    # Ca đỏ trên bản ĐÚNG thì cũng đỏ ở bản hỏng, nên không làm lệch phép so nào — `--tu-kiem`
    # sẽ in dấu đạt trong khi phép đo đang trượt (mục 18 CLAUDE.md). Chặn ngay ở đây.
    if tu_kiem_chay():
        print("\n✗ TRƯỢT: bộ ca đã ĐỎ trên bản ĐÚNG — sửa chỗ đó trước, dựng bản hỏng lúc này "
              "không chứng minh được gì.")
        return 1
    print()
    tong = 0
    for ten, tim, thay, ca_do in BAN_HONG:
        if goc.count(tim) != 1:
            print(f"  ✗ {ten} — chuỗi neo khớp {goc.count(tim)} chỗ (phải đúng 1)")
            tong += 1
            continue
        noi = goc.replace(tim, thay, 1)
        # Bản hỏng phải nằm CÙNG thư mục `scripts/` (nó suy REPO từ vị trí chính nó), và tên
        # mang PID + sha1 nội dung: hai phiên chạy chồng thì không xoá bản hỏng của nhau, và
        # hai bản hỏng cùng giây không dính lại `.pyc` của bản trước (mục 17 CLAUDE.md).
        dich = pathlib.Path(__file__).parent / ("_thu-hong-%d-%s-%s" % (
            os.getpid(), hashlib.sha1(noi.encode()).hexdigest()[:8],
            pathlib.Path(__file__).name))
        dich.write_text(noi, encoding="utf-8")
        try:
            r = subprocess.run([sys.executable, str(dich), "--ca"],
                               capture_output=True, text=True)
            do = [ln for ln in r.stdout.splitlines() if ln.startswith("  ✗")]
            moi_dong = [ln for ln in r.stdout.splitlines() if ln.startswith(("  ✓", "  ✗"))]
            if do and len(do) == len(moi_dong):
                print(f"  ✗ {ten} — MỌI ca đều đỏ: phép thay phá hỏng nền chứ không gỡ một lớp "
                      f"vá, sửa lại phép thay")
                tong += 1
                continue
            can = [f"[{i}]" for i in ca_do]
            bat = r.returncode != 0 and all(any(f" {i:02d} " in ln for ln in do) for i in ca_do)
            print(("  ✓ " if bat else "  ✗ ") + ten
                  + ("" if bat else f" — cần ca {can} đỏ; đỏ thực tế: {do or 'KHÔNG CÓ'}"))
            tong += 0 if bat else 1
        finally:
            dich.unlink(missing_ok=True)
    print(f"\n{len(BAN_HONG) - tong}/{len(BAN_HONG)} bản hỏng bị bắt")
    return 1 if tong else 0


# Bảng đặt CUỐI FILE, sau mã: neo trỏ vào chính dòng khai thì bản hỏng "hỏng" ở bảng chứ không
# ở mã — vẫn chạy, vẫn không lỗi, chỉ là chứng minh mất sạch giá trị (mục 17 CLAUDE.md).
BAN_HONG = [
    ("gỡ lớp gom theo TÊN MIỀN CON (hình dạng a)",
     "    if dk_a == dk_b:                       # (a) tên miền con của cùng một tên đăng ký\n"
     "        return True",
     "    if False:\n        return True", [2]),
    ("gỡ lớp gom theo GỐC TÊN ĐĂNG KÝ (hình dạng b)",
     "    if chung_goc(ten_a, ten_b):            # (b) chung gốc tên đăng ký\n        return True",
     "    if False:\n        return True", [1, 3]),
    # ⚠️ Neo phải KÈM DÒNG LIỀN KỀ: `NGUONG_TIEN_TO = 4` trần thì khớp cả dòng khai trong chính
    # bảng này ⇒ `--tu-kiem` báo "chuỗi neo khớp 2 chỗ" (mục 17 CLAUDE.md). Viết dòng liền kề
    # bằng ký tự thoát `\n` nên bản thân dòng khai không chứa chuỗi neo.
    ("nới ngưỡng tiền tố về 1 — gom cả hai viện chỉ chung vài ký tự đầu",
     "NGUONG_TIEN_TO = 4\n\n# Blog của viện hay đặt tên",
     "NGUONG_TIEN_TO = 1\n\n# Blog của viện hay đặt tên", [6]),
    ("gỡ bảng ĐUÔI CÔNG CỘNG nhiều mảnh — lấy phăng hai mảnh cuối",
     "    so_manh = 3 if len(manh) >= 3 and \".\".join(manh[-2:]) in DUOI_NHIEU_MANH else 2",
     "    so_manh = 2", [7]),
    ("gỡ bảng TÊN MIỀN TRỌ CHUNG — gom mọi viện trọ chung một trường đại học",
     "    if dk_a in MIEN_TRO_CHUNG or dk_b in MIEN_TRO_CHUNG:\n        return False",
     "    if False:\n        return False", [8]),
    ("gỡ điều kiện LỆCH — nêu mọi nhóm, kể cả nhóm đều nhau",
     "        if co and khong:\n            ra.append(con)",
     "        if True:\n            ra.append(con)", [4, 5]),
    ("gỡ phép TRỪ DA_DUYET — kêu lại nhóm đã soi",
     "        con = _tru_da_duyet(nhom)\n        if len(con) < 2:",
     "        con = tuple(nhom)\n        if len(con) < 2:", [10]),
    ("gỡ phép bóc tiền tố 'the' của tên blog",
     "    if ten.startswith(TIEN_TO_BLOG) and len(ten) > len(TIEN_TO_BLOG) + NGUONG_TIEN_TO:\n"
     "        return ten[len(TIEN_TO_BLOG):]",
     "    if False:\n        return ten", [3]),
    ("bảng nguồn RỖNG thì nuốt, trả bảng rỗng cho êm",
     "        print(f\"✗ Bảng nguồn rỗng bất thường ({ADD_ANALYSES}): {len(mien)} tên miền, \"\n"
     "              f\"{len(co_duong)} tên miền có đường quét\", file=sys.stderr)\n"
     "        raise SystemExit(2)",
     "        return set(), set()", [12]),
    ("bảng nguồn KHÔNG NẠP ĐƯỢC thì nuốt, trả bảng rỗng cho êm",
     "        print(f\"✗ Không đọc được bảng nguồn ({ADD_ANALYSES}): {type(e).__name__}: {e}\",\n"
     "              file=sys.stderr)\n"
     "        raise SystemExit(2)",
     "        return set(), set()", [13]),
]


if __name__ == "__main__":
    if "--tu-kiem" in sys.argv:
        sys.exit(tu_kiem())
    if "--ca" in sys.argv:            # chạy bộ ca, dùng bởi chính --tu-kiem
        sys.exit(tu_kiem_chay())
    sys.exit(bao_cao())
