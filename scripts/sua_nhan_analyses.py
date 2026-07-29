#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BẢO TRÌ NHÃN `outlet` CỦA MỤC 🏛️ Think-tank (DATA.analyses trong index.html).

VÌ SAO CÓ FILE NÀY (29.7.2026): guardrail của `add_analyses.py` kiểm theo DOMAIN chứ không
kiểm nhãn `outlet`, nên hai bài cùng một viện vẫn được nạp dưới hai tên khác nhau ('ASPI' và
'ASPI Strategist', cùng aspistrategist.org.au). Nhãn hiện thẳng ra web (dòng `.foot`) và còn
là khoá `voteMeta.src` mà hồ sơ độc giả dùng để học sở thích theo nguồn — nhãn tách đôi thì
tín hiệu bình chọn cũng bị chia đôi, học sai mà không báo lỗi.

Đây là loại hỏng CÂM: web vẫn hiện đẹp, không script nào kêu. Nên `--kiem` phải chạy được
độc lập và trả mã ≠ 0, kèm `--tu-kiem` chứng minh nó thật sự bắt được lỗi (CLAUDE.md mục 17).

Dùng:
    python3 scripts/sua_nhan_analyses.py --kiem        # LIỆT KÊ + soi lỗi, KHÔNG ghi gì
    python3 scripts/sua_nhan_analyses.py --gop-nhan    # áp OUTLET_CANON, ghi lại index.html
    python3 scripts/sua_nhan_analyses.py --xoa-url <url> [<url> ...]   # xoá bài theo url
    python3 scripts/sua_nhan_analyses.py --tu-kiem     # chứng minh --kiem BẮT ĐƯỢC lỗi

`--kiem` bắt 3 loại lỗi (mỗi loại một mã thoát riêng để cổng ngoài phân biệt được — xem
MA_LOI): domain mang nhiều nhãn · domain không phải viện nghiên cứu · hai bài cùng một bài
gốc (trùng slug cuối url, dạng warontherocks.com/<slug> và .../2026/07/<slug>).

⛔ `--xoa-url` là đường DUY NHẤT để xoá, và phải gõ đủ url. KHÔNG có chế độ "tự dọn bài lạ":
xoá dữ liệu là quyết định của Huy, không phải của script (CLAUDE.md mục 1).
"""
import collections
import json
import os
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import analyses_store  # noqa: E402
from add_analyses import THINKTANK_DOMAINS, domain_of  # noqa: E402

# Seam để bộ test trỏ vào một repo giả trong thư mục tạm.
# ⚠️ Đổi 30/07/2026: trước là ANALYSES_INDEX (trỏ file index.html giả) — bài think-tank nay
# nằm ở data/analyses.json nên seam phải là THƯ MỤC REPO, không phải file index.html.
REPO_ROOT = pathlib.Path(
    os.environ.get("ANALYSES_REPO") or (pathlib.Path(__file__).resolve().parent.parent)
)

# Nhãn CHUẨN theo domain. Chốt theo tên tự xưng của nơi xuất bản, không theo tên viện mẹ:
# aspistrategist.org.au là blog The Strategist của ASPI, còn aspi.org.au mới là báo cáo của
# viện — để chung một nhãn 'ASPI' thì sau này không phân biệt được hai loại.
# Thêm dòng vào đây mỗi khi phát hiện một domain bị gọi bằng hai tên.
OUTLET_CANON = {
    "aspistrategist.org.au": "ASPI Strategist",
}

MA_LOI = {"nhan_doi": 2, "ngoai_vien": 3, "trung_bai": 4}

# Cặp trùng ĐÃ ĐƯA HUY QUYẾT và Huy chọn GIỮ CẢ HAI. Có danh sách này vì cổng kêu đi kêu lại
# một thứ đã xử xong thì lần sau không ai đọc nữa — đúng lỗi mà canary bản tin đã vấp (xem
# CLAUDE.md, mục canary "kêu oan vài lần là hết ai đọc").
# ⚠️ Chỉ thêm vào đây SAU KHI Huy đã quyết giữ, không phải để làm cổng im cho gọn.
TRUNG_DA_DUYET = {
    # 29/07/2026 — hai bản dịch của cùng bài War on the Rocks 08/07 về hải tặc Somalia.
    "warontherocks.com/somali-pirates-are-back-but-the-coalition-that-beat-them-isnt-coming",
}


def doc_data(repo: pathlib.Path) -> dict:
    """Trả về dict bọc {"analyses": [...]} để `kiem()` và `_fixture()` dùng chung một hình dạng."""
    return {"analyses": analyses_store.doc(repo)}


def ghi_data(repo: pathlib.Path, data: dict) -> None:
    analyses_store.ghi(repo, data.get("analyses") or [])


def slug_cuoi(url: str) -> str:
    """Khoá nhận diện 'cùng một bài gốc': domain + đoạn path cuối cùng.

    Bắt đúng cặp warontherocks.com/<slug>/ và warontherocks.com/2026/07/<slug>/ — hai url
    khác chuỗi nên guardrail trùng-url của add_analyses.py cho lọt cả hai, dù curl cho thấy
    bản có ngày redirect 301 về bản không ngày.
    """
    path = re.sub(r"^https?://", "", url.strip(), flags=re.I).split("?")[0].split("#")[0]
    doan = [p for p in path.split("/") if p]
    if len(doan) < 2:
        return path.lower()
    return (domain_of(url) + "/" + doan[-1]).lower()


def kiem(data: dict) -> int:
    an = data.get("analyses") or []
    print(f"=== DATA.analyses: {len(an)} bài ===\n")

    theo_domain = collections.defaultdict(list)
    for a in an:
        theo_domain[domain_of(a.get("url", ""))].append(a)

    print(f"{'NHÃN outlet':<34} {'DOMAIN':<28} SỐ BÀI  VIỆN?")
    for dom in sorted(theo_domain):
        for nhan, n in sorted(collections.Counter(a.get("outlet", "") for a in theo_domain[dom]).items()):
            vien = "✓" if dom in THINKTANK_DOMAINS else "✗ KHÔNG"
            print(f"{nhan:<34} {dom:<28} {n:>5}   {vien}")

    loi = []

    nhan_doi = {d: sorted({a.get("outlet", "") for a in v}) for d, v in theo_domain.items()}
    nhan_doi = {d: ns for d, ns in nhan_doi.items() if len(ns) > 1}
    if nhan_doi:
        loi.append("nhan_doi")
        print("\n⛔ MỘT DOMAIN — NHIỀU NHÃN (web hiện thành hai nguồn khác nhau, hồ sơ độc giả học sai):")
        for d, ns in sorted(nhan_doi.items()):
            chuan = OUTLET_CANON.get(d)
            goi_y = f" → gộp về '{chuan}' (chạy --gop-nhan)" if chuan else " → THÊM domain này vào OUTLET_CANON rồi chạy --gop-nhan"
            print(f"   {d}: {' | '.join(repr(n) for n in ns)}{goi_y}")

    ngoai = [a for a in an if domain_of(a.get("url", "")) not in THINKTANK_DOMAINS]
    if ngoai:
        loi.append("ngoai_vien")
        print("\n⛔ DOMAIN KHÔNG THUỘC THINKTANK_DOMAINS (dữ liệu đời cũ — guardrail nay đã chặn loại này):")
        for a in sorted(ngoai, key=lambda x: str(x.get("date"))):
            print(f"   [{a.get('date')}] {a.get('outlet')} — {domain_of(a.get('url',''))}")
            print(f"      {a.get('title','')[:90]}")
            print(f"      {a.get('url')}")
        print("   → Đúng là viện nghiên cứu: thêm domain vào THINKTANK_DOMAINS (add_analyses.py).")
        print("     Là báo chí: HỎI Huy rồi mới `--xoa-url`. Script KHÔNG tự xoá.")

    trung = {k: v for k, v in collections.Counter(slug_cuoi(a.get("url", "")) for a in an).items()
             if v > 1 and k not in TRUNG_DA_DUYET}
    if trung:
        loi.append("trung_bai")
        print("\n⛔ HAI BẢN CỦA CÙNG MỘT BÀI (trùng slug cuối url — guardrail trùng-url không bắt được):")
        for k in sorted(trung):
            print(f"   {k}")
            for a in an:
                if slug_cuoi(a.get("url", "")) == k:
                    print(f"      [{a.get('date')}] {a.get('title','')[:70]}")
                    print(f"         {a.get('url')}")

    if not loi:
        print("\n✓ Không phát hiện lỗi nhãn/domain/trùng bài.")
        return 0
    print(f"\n✗ {len(loi)} loại lỗi: {', '.join(loi)}")
    return MA_LOI[loi[0]]


def gop_nhan(repo: pathlib.Path) -> int:
    data = doc_data(repo)
    doi = []
    for a in data.get("analyses") or []:
        chuan = OUTLET_CANON.get(domain_of(a.get("url", "")))
        if chuan and a.get("outlet") != chuan:
            doi.append((a.get("outlet"), chuan, a.get("title", "")[:60]))
            a["outlet"] = chuan
    if not doi:
        print("Không có nhãn nào cần gộp.")
        return 0
    for cu, moi, t in doi:
        print(f"  '{cu}' → '{moi}'  |  {t}")
    ghi_data(repo, data)
    print(f"OK: đã gộp nhãn cho {len(doi)} bài, ghi lại {analyses_store.TEN_FILE}.")
    return 0


def xoa_url(repo: pathlib.Path, urls: list) -> int:
    data = doc_data(repo)
    an = data.get("analyses") or []
    can = {u.strip().rstrip("/") for u in urls}
    giu, bo = [], []
    for a in an:
        (bo if a.get("url", "").strip().rstrip("/") in can else giu).append(a)
    thieu = can - {a.get("url", "").strip().rstrip("/") for a in bo}
    if thieu:
        # Gõ sai url mà script báo "đã xoá 0 bài" thì dễ tưởng là xong. Chặn thẳng.
        print("LỖI: không tìm thấy url trong DATA.analyses:")
        for u in sorted(thieu):
            print(f"   {u}")
        return 1
    for a in bo:
        print(f"  XOÁ [{a.get('date')}] {a.get('outlet')} — {a.get('title','')[:70]}")
        print(f"       {a.get('url')}")
    data["analyses"] = giu
    ghi_data(repo, data)
    print(f"OK: đã xoá {len(bo)} bài. Còn lại {len(giu)} bài.")
    return 0


# ——— Tự kiểm: mỗi ca dựng đúng một dữ liệu XẤU rồi khẳng định --kiem THẬT SỰ kêu ———
_BAI_SACH = {
    "date": "2026-07-27", "region": "Đông Á", "topic": "X", "outlet": "CSIS", "author": "",
    "title": "Bài sạch", "summary": "s", "takeaway": "t",
    "url": "https://www.csis.org/analysis/bai-sach/",
}


def _fixture(bai_them: list) -> dict:
    return {"analyses": [dict(_BAI_SACH)] + bai_them}


_CA_TU_KIEM = [
    ("PHẢI CHẶN — một domain hai nhãn", [
        dict(_BAI_SACH, outlet="ASPI", url="https://www.aspistrategist.org.au/a/"),
        dict(_BAI_SACH, outlet="ASPI Strategist", url="https://www.aspistrategist.org.au/b/"),
    ], "nhan_doi"),
    ("PHẢI CHẶN — domain không phải viện nghiên cứu", [
        dict(_BAI_SACH, outlet="Al Jazeera", url="https://www.aljazeera.com/news/2026/7/9/x"),
    ], "ngoai_vien"),
    ("PHẢI CHẶN — hai bản cùng một bài gốc", [
        dict(_BAI_SACH, outlet="War on the Rocks", url="https://warontherocks.com/somali-pirates/"),
        dict(_BAI_SACH, outlet="War on the Rocks", url="https://warontherocks.com/2026/07/somali-pirates/"),
    ], "trung_bai"),
    # Cặp trong TRUNG_DA_DUYET phải im; ca "trùng bài" ngay trên dùng slug KHÁC nên vẫn phải
    # đỏ — hai ca đi cùng nhau mới chứng minh miễn trừ đúng phạm vi, không tắt luôn cả cổng.
    ("PHẢI CHO QUA — cặp trùng Huy đã duyệt giữ", [
        dict(_BAI_SACH, outlet="War on the Rocks",
             url="https://warontherocks.com/somali-pirates-are-back-but-the-coalition-that-beat-them-isnt-coming/"),
        dict(_BAI_SACH, outlet="War on the Rocks",
             url="https://warontherocks.com/2026/07/somali-pirates-are-back-but-the-coalition-that-beat-them-isnt-coming/"),
    ], None),
    ("PHẢI CHO QUA — dữ liệu sạch", [], None),
]


def tu_kiem() -> int:
    hong = 0
    for nhan, them, mong_doi in _CA_TU_KIEM:
        ma = kiem(_fixture(them))
        that_bai = (ma != MA_LOI[mong_doi]) if mong_doi else (ma != 0)
        print(f"{'✗ ĐỎ' if that_bai else '✓'} {nhan} (mã {ma}, mong đợi {MA_LOI.get(mong_doi, 0)})\n{'-'*78}")
        hong += that_bai
    # Ca ĐỐI CHỨNG: gỡ đúng dòng bắt trùng-bài thì ca 'trung_bai' PHẢI hết kêu. Nếu vẫn kêu
    # thì ca đó đang đỏ vì lý do khác, không chứng minh được gì.
    goc = globals()["slug_cuoi"]
    globals()["slug_cuoi"] = lambda u: u  # bản HỎNG: so nguyên url, y như guardrail cũ
    ma_hong = kiem(_fixture(_CA_TU_KIEM[2][1]))
    globals()["slug_cuoi"] = goc
    doi_chung_hong = ma_hong == MA_LOI["trung_bai"]
    print(f"{'✗ ĐỎ' if doi_chung_hong else '✓'} ĐỐI CHỨNG — bản gỡ slug_cuoi phải KHÔNG bắt được ca trùng bài (mã {ma_hong})")
    hong += doi_chung_hong

    if hong:
        print(f"\n✗ {hong} phép thử tự kiểm THẤT BẠI — bộ kiểm này chưa chứng minh được là nó bắt lỗi.")
        return 1
    print(f"\n✓ Toàn bộ {len(_CA_TU_KIEM)} ca + 1 đối chứng đều đúng — --kiem thật sự bắt được lỗi.")
    return 0


def main() -> int:
    argv = sys.argv[1:]
    if "--tu-kiem" in argv:
        return tu_kiem()
    if "--gop-nhan" in argv:
        return gop_nhan(REPO_ROOT)
    if "--xoa-url" in argv:
        urls = argv[argv.index("--xoa-url") + 1:]
        if not urls:
            print("LỖI: --xoa-url cần ít nhất một url.")
            return 1
        return xoa_url(REPO_ROOT, urls)
    return kiem(doc_data(REPO_ROOT))


if __name__ == "__main__":
    raise SystemExit(main())
