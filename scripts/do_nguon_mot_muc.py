#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TỰ DÒ nguồn think-tank chỉ ra bài từ ĐÚNG MỘT mục — dấu hiệu bảng feed còn thiếu một nửa.

VÌ SAO CÓ PHÉP ĐO NÀY. Ngày 06/08/2026 bắt được lỗ: `add_analyses.py::THINKTANK_FEEDS` khai
Lowy Institute bằng đúng một feed — `the-interpreter`, tức mục BÌNH LUẬN NGẮN — còn mục
NGHIÊN CỨU (`/publications/`) thì chưa từng khai, dù feed ấy sống bình thường. Đo trên kho khi
đó: **35/35 bài Lowy thuộc `/the-interpreter/`, 0 bài `/publications/`**.

Cơ chế gây vấp, và đây mới là phần đáng sợ: **không dấu hiệu nào phát ra.** Feed blog ra bài
đều mỗi ngày, danh sách ứng viên vẫn đầy, mục Think-tank trên web vẫn có bài mới mỗi sáng —
nên không ai có lý do đi hỏi "còn thiếu gì". Lỗ chỉ lộ ra khi có người tình cờ đi tìm một
nghiên cứu cụ thể mà không thấy. Vá tay bốn viện hôm nay thì viện thứ năm mai mốt vẫn hỏng y
hệt, cùng một cách, và cũng im lặng y hệt. Vì thế phải có một phép đo TỰ DÒ.

PHÉP ĐO. Đếm phân bố (tên miền, mục đầu của đường dẫn) trên `data/analyses.json`. Tên miền có
từ `NGUONG_BAI` bài trở lên mà **thảy đều rơi vào đúng MỘT mục** là ứng viên nghi thiếu feed —
một viện xuất bản thật thì bài rải ra nhiều mục (Hudson 71 bài / 5 mục · Atlantic Council 57
bài / 5 mục), dồn hết vào một mục nghĩa là đường vào chỉ có một cửa.

    python3 scripts/do_nguon_mot_muc.py             # báo cáo; mã 3 khi có ứng viên chưa duyệt
    python3 scripts/do_nguon_mot_muc.py --tu-kiem   # chứng minh phép đo BẮT ĐƯỢC lỗi

BỐN NHÓM, cố ý không gộp — gộp lại là kêu oan, mà bảng bị kêu oan vài lần thì hết được đọc:

  ★ NGHI THIẾU FEED  một mục · CÓ feed khai trong THINKTANK_FEEDS ⇒ đúng hình dạng của lỗ Lowy
  ○ CHƯA CÓ FEED     một mục · KHÔNG feed nào khai ⇒ diện WebSearch (xem WEBSEARCH_ONLY).
                     Bài vào kho bằng tay nên dồn một mục là chuyện đương nhiên, KHÔNG phải lỗi
  ▫ BÀI Ở GỐC        đặt bài thẳng ở gốc tên miền ⇒ "mục đầu đường dẫn" không tồn tại, phép đo
                     này vô nghĩa với chúng. Xếp riêng chứ đừng kêu
  ✓ NHIỀU MỤC        bình thường

⚠️ GIỚI HẠN ĐÃ BIẾT, ĐỪNG TƯỞNG LÀ ĐÃ PHỦ HẾT. Phép đo bắt được **hình dạng Lowy** (một tên
miền, bài chia theo mục), KHÔNG bắt được **hình dạng ASPI** (viện xuất bản dưới HAI tên miền —
blog `aspistrategist.org.au`, báo cáo `aspi.org.au` — mà bảng chỉ khai một). Với ASPI thì 81/81
bài nằm ở GỐC của tên miền blog, tức rơi vào nhóm ▫ và không được nêu. Hai hình dạng cần hai
phép đo khác nhau; ở đây mới có một. Đừng đọc bảng kết quả sạch thành "mọi viện đã khai đủ".
"""
import collections
import importlib.util
import json
import os
import pathlib
import sys
import urllib.parse

sys.dont_write_bytecode = True

REPO = pathlib.Path(__file__).resolve().parent.parent
KHO = pathlib.Path(os.environ.get("DO_NGUON_KHO", REPO / "data" / "analyses.json"))
ADD_ANALYSES = pathlib.Path(
    os.environ.get("ADD_ANALYSES", REPO / "scripts" / "add_analyses.py"))

# Từ ngưỡng này trở lên mới kết luận. Dưới ngưỡng thì "dồn một mục" không nói lên gì — một
# viện mới nạp 2 bài thì đương nhiên cả 2 cùng mục, kêu vào đó là kêu oan hàng loạt.
NGUONG_BAI = 5

# Tên miền đặt bài THẲNG Ở GỐC (`domain.org/ten-bai`), không chia mục. Với chúng thì "mục đầu
# của đường dẫn" chính là tên bài, nên mỗi bài một "mục" hoặc thảy đều rơi vào ô (GỐC) — phép
# đo này không nói được gì. Xếp riêng chứ đừng kêu.
# ⚠️ Danh sách lấy TỪ SỐ ĐO trên kho thật 06/08/2026, không phải từ phỏng đoán: aspistrategist
# 81/81 ở gốc · ussc 31/31 · mwi 15/15 · cimsec 5/5 · warontherocks 24/37. `jamestown.org` thêm
# theo cùng lối xuất bản dù kho hiện chưa đủ bài để đo.
# ⚠️ Thêm một tên miền vào đây là TẮT phép đo cho nó — chỉ thêm khi đã mở vài url ra xem tận
# nơi là bài nằm ở gốc thật, đừng thêm cho hết kêu.
MIEN_BAI_O_GOC = frozenset({
    "aspistrategist.org.au",
    "ussc.edu.au",
    "mwi.westpoint.edu",
    "cimsec.org",
    "jamestown.org",
    "warontherocks.com",
    "smallwarsjournal.com",
    "eastasiaforum.org",
})

# Ứng viên ĐÃ SOI TẬN NƠI rồi — kèm lý do, để lần chạy sau không kêu lại. Đây là chỗ ghi kết
# quả triage, KHÔNG phải chỗ giấu ứng viên khó: mỗi dòng phải nói được đã soi cái gì.
DA_DUYET = {
    "lowyinstitute.org":
        "ĐÃ VÁ 06/08/2026 — feed nghiên cứu `/publications/rss.xml` đã khai vào "
        "THINKTANK_FEEDS. Kho vẫn 35/35 bài `/the-interpreter/` vì lô bài mục mới chưa nạp; "
        "nạp xong thì tên miền này tự rời danh sách, lúc đó GỠ dòng này đi.",
}


def nap_feeds():
    """URL feed đang khai -> tập tên miền đã có đường quét tự động."""
    spec = importlib.util.spec_from_file_location("aa_do_nguon", ADD_ANALYSES)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    ra = set()
    for _, url, *_ in mod.THINKTANK_FEEDS:
        ra.add(urllib.parse.urlparse(url).netloc.replace("www.", ""))
    return ra


def doc_kho(duong: pathlib.Path):
    """Đọc kho bài. Hỏng thì KÊU chứ không trả rỗng — kho rỗng và kho không đọc được cho ra
    cùng một bảng sạch, mà đó là hai chuyện khác hẳn nhau."""
    try:
        d = json.loads(duong.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"✗ Không có kho bài: {duong}", file=sys.stderr)
        raise SystemExit(2)
    except json.JSONDecodeError as e:
        print(f"✗ Kho bài hỏng JSON ({duong}): {e}", file=sys.stderr)
        raise SystemExit(2)
    if not isinstance(d, list):
        print(f"✗ Kho bài phải là một MẢNG, đọc ra {type(d).__name__}: {duong}", file=sys.stderr)
        raise SystemExit(2)
    return d


def phan_bo(bai):
    """[(tên miền, Counter mục đầu đường dẫn)] — bài không có url hợp lệ thì bỏ qua."""
    g = collections.defaultdict(collections.Counter)
    for b in bai:
        u = urllib.parse.urlparse((b or {}).get("url", "") or "")
        if not u.netloc:
            continue
        dom = u.netloc.replace("www.", "")
        seg = [s for s in u.path.split("/") if s]
        # Chỉ có 1 mảnh nghĩa là bài nằm ngay ở gốc (`domain.org/ten-bai`) — không có "mục".
        g[dom][seg[0] if len(seg) > 1 else "(GỐC)"] += 1
    return g


def phan_loai(bai, co_feed):
    """Phân 4 nhóm -> dict(nghi, chua_feed, o_goc, nhieu_muc), mỗi mục là [(dom, n, Counter)]."""
    ra = {"nghi": [], "chua_feed": [], "o_goc": [], "nhieu_muc": []}
    for dom, c in phan_bo(bai).items():
        n = sum(c.values())
        if n < NGUONG_BAI:
            continue
        if dom in MIEN_BAI_O_GOC:
            ra["o_goc"].append((dom, n, c))
        elif len(c) > 1:
            ra["nhieu_muc"].append((dom, n, c))
        elif dom in co_feed:
            ra["nghi"].append((dom, n, c))
        else:
            ra["chua_feed"].append((dom, n, c))
    for k in ra:
        ra[k].sort(key=lambda x: -x[1])
    return ra


def _in_nhom(nhan, muc):
    for dom, n, c in muc:
        goi = " · ".join(f"{k} ({v})" for k, v in c.most_common(4))
        print(f"  {nhan} {dom:26s} {n:3d} bài  →  {goi}")


def bao_cao(kho=None):
    bai = doc_kho(kho or KHO)
    kq = phan_loai(bai, nap_feeds())
    print(f"=== DÒ NGUỒN CHỈ RA BÀI TỪ MỘT MỤC ({len(bai)} bài · ngưỡng {NGUONG_BAI}) ===\n")

    chua_duyet = [x for x in kq["nghi"] if x[0] not in DA_DUYET]
    print(f"★ NGHI THIẾU FEED NGHIÊN CỨU ({len(kq['nghi'])} tên miền)")
    if kq["nghi"]:
        _in_nhom("★", kq["nghi"])
        for dom, _, _ in kq["nghi"]:
            if dom in DA_DUYET:
                print(f"      ↳ đã duyệt: {DA_DUYET[dom]}")
    else:
        print("  (không có)")

    print(f"\n○ CHƯA CÓ FEED NÀO — diện WebSearch, KHÔNG phải lỗi ({len(kq['chua_feed'])})")
    _in_nhom("○", kq["chua_feed"]) if kq["chua_feed"] else print("  (không có)")
    print(f"\n▫ BÀI Ở GỐC — phép đo không áp dụng ({len(kq['o_goc'])})")
    _in_nhom("▫", kq["o_goc"]) if kq["o_goc"] else print("  (không có)")
    print(f"\n✓ NHIỀU MỤC — bình thường ({len(kq['nhieu_muc'])})")
    _in_nhom("✓", kq["nhieu_muc"]) if kq["nhieu_muc"] else print("  (không có)")

    if chua_duyet:
        print("\n⚠️ Tên miền nghi thiếu feed nghiên cứu mà CHƯA ai soi: "
              + " · ".join(d for d, _, _ in chua_duyet))
        print("   Việc phải làm: mở trang viện, đọc thẻ <link rel=\"alternate\"> tìm feed của "
              "mục còn thiếu (đường đã tìm ra feed RUSI và CACI). Có feed thì khai vào "
              "THINKTANK_FEEDS; không có thì ghi một dòng vào DA_DUYET kèm lý do đã soi.")
        return 3
    return 0


# ─────────────────────────── tự kiểm ───────────────────────────

def _kho_gia(rows):
    """rows = [(url, số bài)] -> danh sách bài giả."""
    ra = []
    for url, n in rows:
        ra += [{"url": url % i if "%" in url else url + f"-{i}"} for i in range(n)]
    return ra


def cac_ca():
    """[(tên ca, đạt, lời)] — ca có ★ là ca PHẢI NÊU."""
    ra = []
    co_feed = {"lowyinstitute.org", "aspistrategist.org.au", "vien-moi.org"}

    # ── 01 ★ đúng hình dạng lỗ Lowy: một mục, đủ ngưỡng, có feed khai
    k = phan_loai(_kho_gia([("https://www.vien-moi.org/the-blog/bai-%d", 6)]), co_feed)
    ra.append(("★ 01 nguồn 6 bài dồn MỘT mục, có feed khai ⇒ phải bị nêu",
               [d for d, _, _ in k["nghi"]] == ["vien-moi.org"],
               f"không vào nhóm nghi: {k}"))

    # ── 02 đối chứng chống kêu oan: bài rải nhiều mục
    k = phan_loai(_kho_gia([("https://www.vien-moi.org/the-blog/bai-%d", 5),
                            ("https://www.vien-moi.org/report/bai-%d", 4)]), co_feed)
    ra.append(("02 đối chứng — bài rải 2 mục ⇒ KHÔNG nêu",
               not k["nghi"] and [d for d, _, _ in k["nhieu_muc"]] == ["vien-moi.org"],
               f"kêu oan nguồn đã rải nhiều mục: {k}"))

    # ── 03 đối chứng: dưới ngưỡng
    k = phan_loai(_kho_gia([("https://www.vien-moi.org/the-blog/bai-%d", NGUONG_BAI - 1)]), co_feed)
    ra.append((f"03 đối chứng — {NGUONG_BAI - 1} bài (dưới ngưỡng {NGUONG_BAI}) ⇒ KHÔNG nêu",
               not k["nghi"] and not k["chua_feed"], f"kêu oan nguồn dưới ngưỡng: {k}"))

    # ── 04 đối chứng: tên miền đặt bài ở GỐC — phép đo vô nghĩa, phải xếp riêng
    k = phan_loai(_kho_gia([("https://www.aspistrategist.org.au/bai-%d", 20)]), co_feed)
    ra.append(("04 đối chứng — miền bài ở GỐC ⇒ xếp nhóm riêng, KHÔNG nêu",
               not k["nghi"] and [d for d, _, _ in k["o_goc"]] == ["aspistrategist.org.au"],
               f"miền bài ở gốc bị kêu oan: {k}"))

    # ── 05 đối chứng: một mục nhưng KHÔNG có feed nào khai ⇒ diện WebSearch
    k = phan_loai(_kho_gia([("https://www.brookings.edu/articles/bai-%d", 10)]), co_feed)
    ra.append(("05 đối chứng — một mục mà CHƯA có feed ⇒ nhóm WebSearch, KHÔNG nêu",
               not k["nghi"] and [d for d, _, _ in k["chua_feed"]] == ["brookings.edu"],
               f"nguồn chưa có feed bị xếp nhầm thành thiếu feed nghiên cứu: {k}"))

    # ── 06 ★ CA VÀNG trên kho THẬT: ứng viên nào cũng phải đã được soi
    that = phan_loai(doc_kho(KHO), nap_feeds())
    chua = [d for d, _, _ in that["nghi"] if d not in DA_DUYET]
    ra.append(("★ 06 ca vàng — kho THẬT không còn ứng viên nào chưa soi",
               not chua,
               "chưa soi: " + " · ".join(chua) + " — khai feed mục còn thiếu, hoặc ghi "
               "một dòng DA_DUYET kèm lý do đã soi"))

    # ── 07 ★ kho hỏng phải KÊU, không được trả bảng sạch
    import tempfile
    with tempfile.TemporaryDirectory() as t:
        xau = pathlib.Path(t) / "hong.json"
        xau.write_text('{"analyses": []}', encoding="utf-8")
        try:
            doc_kho(xau)
            ok = False
        except SystemExit as e:
            ok = e.code == 2
    ra.append(("★ 07 kho không phải MẢNG ⇒ kêu mã 2, không trả bảng sạch", ok,
               "kho hỏng bị nuốt — kho rỗng và kho không đọc được ra cùng một bảng"))
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
    if tu_kiem_chay():
        print("\n✗ TRƯỢT: bộ ca đã ĐỎ trên bản ĐÚNG — sửa chỗ đó trước, dựng bản hỏng lúc "
              "này không chứng minh được gì.")
        return 1
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
            os.getpid(), hashlib.sha1(noi.encode()).hexdigest()[:8], pathlib.Path(__file__).name))
        dich.write_text(noi, encoding="utf-8")
        try:
            r = subprocess.run([sys.executable, str(dich), "--ca"],
                               capture_output=True, text=True)
            do = [ln for ln in r.stdout.splitlines() if ln.startswith("  ✗")]
            het_do = len(do) == len([l for l in r.stdout.splitlines()
                                     if l.startswith(("  ✓", "  ✗"))])
            if het_do and do:
                print(f"  ✗ {ten} — MỌI ca đều đỏ: phép thay phá hỏng nền chứ không gỡ một "
                      f"lớp vá, sửa lại phép thay")
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
    ("gỡ phép đếm số mục — coi mọi nguồn là một mục",
     "        elif len(c) > 1:\n            ra[\"nhieu_muc\"].append((dom, n, c))",
     "        elif False:\n            ra[\"nhieu_muc\"].append((dom, n, c))", [2]),
    ("gỡ phép loại miền bài ở GỐC",
     "        if dom in MIEN_BAI_O_GOC:\n            ra[\"o_goc\"].append((dom, n, c))",
     "        if False:\n            ra[\"o_goc\"].append((dom, n, c))", [4]),
    ("gỡ phép phân biệt nguồn CHƯA có feed",
     "        elif dom in co_feed:\n            ra[\"nghi\"].append((dom, n, c))",
     "        elif True:\n            ra[\"nghi\"].append((dom, n, c))", [5]),
    ("nới ngưỡng về 0 — kêu cả nguồn mới nạp vài bài",
     "        if n < NGUONG_BAI:\n            continue",
     "        if False:\n            continue", [3]),
    ("nhóm nghi không bao giờ có ai — phép đo mất răng",
     "            ra[\"nghi\"].append((dom, n, c))",
     "            ra[\"nhieu_muc\"].append((dom, n, c))", [1]),
    ("kho hỏng thì nuốt, trả mảng rỗng cho êm",
     "        print(f\"✗ Kho bài phải là một MẢNG, đọc ra {type(d).__name__}: {duong}\", file=sys.stderr)\n        raise SystemExit(2)",
     "        return []", [7]),
]


if __name__ == "__main__":
    if "--tu-kiem" in sys.argv:
        sys.exit(tu_kiem())
    if "--ca" in sys.argv:            # chạy bộ ca, dùng bởi chính --tu-kiem
        sys.exit(tu_kiem_chay())
    sys.exit(bao_cao())
