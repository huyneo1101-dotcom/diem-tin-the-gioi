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

⚠️ GIỚI HẠN ĐÃ BIẾT, ĐỪNG TƯỞNG LÀ ĐÃ PHỦ HẾT. Phép đo NÀY chỉ bắt **hình dạng Lowy** (một tên
miền, bài chia theo mục). Nó KHÔNG bắt **hình dạng ASPI** (viện xuất bản dưới HAI tên miền —
blog `aspistrategist.org.au`, báo cáo `aspi.org.au` — mà bảng chỉ khai một): với ASPI thì 81/81
bài nằm ở GỐC của tên miền blog, tức rơi vào nhóm ▫ và không được nêu.

  → Hình dạng thứ hai nay do **`scripts/do_nguon_hai_mien.py`** đo (dựng 06/08/2026), cổng
    nghiệm thu `tests/test-nguon-hai-mien.py`. Hai phép đo là hai lớp RỜI NHAU, không lớp nào
    thay được lớp nào — bảng kết quả sạch của MỘT phép đo không có nghĩa "mọi viện đã khai đủ",
    phải đọc cả hai. Cả hai đều đã nạp vào `BO_TEST` của `HeThong/khoe.py`.
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
    # ── thêm 07/08/2026, đã mở feed ra xem tận nơi chứ không suy từ bảng phân bố ──
    # amti: 8/8 item của `amti.csis.org/feed/` đều dạng `amti.csis.org/<slug>/`, không mục nào.
    "amti.csis.org",
    # icds: 8/8 item dạng `icds.ee/en/<slug>/` — `en` là TIỀN TỐ NGÔN NGỮ, đã bóc ở `phan_bo`.
    # Viện này phân loại nội dung bằng CATEGORY trong feed (Commentary · Analysis · Report ·
    # Brief · Policy paper · News) chứ không bằng đường dẫn, nên mọi loại nằm chung một tầng
    # và "mục đầu đường dẫn" không nói được gì.
    "icds.ee",
    # thêm 16/08/2026, đã mở feed ra xem tận nơi: 6/6 item của `southasianvoices.org/feed/`
    # đều dạng `southasianvoices.org/<slug-dai>/`, không mục nào — cùng hình dạng
    # aspistrategist/ussc/mwi. Feed đã khai trong THINKTANK_FEEDS, đây KHÔNG phải lỗ thiếu feed.
    "southasianvoices.org",
    # thêm 19/08/2026, đã mở `longwarjournal.org/feed` ra xem tận nơi: 15/15 item mới nhất dạng
    # `/archives/<năm>/<tháng>/<slug>.php` — bất kể chủ đề (Iran, Yemen, Somalia, Bắc Triều
    # Tiên, Mali đều rơi cùng khuôn). `archives` là tiền tố ngày tháng của MỌI bài trên site,
    # không phải mục phân loại, nên "mục đầu đường dẫn" không nói được gì — cùng hình dạng
    # aspistrategist/ussc/mwi. Feed đã khai trong THINKTANK_FEEDS, đây KHÔNG phải lỗ thiếu feed.
    "longwarjournal.org",
})

# Tiền tố NGÔN NGỮ — bóc trước khi tính mục. `icds.ee/en/<slug>` không có nghĩa là viện ấy chỉ
# xuất bản một mục tên `en`; đó là mảnh định tuyến ngôn ngữ, không phải mục.
# ⚠️ CỐ Ý CHỈ BÓC TIỀN TỐ NGÔN NGỮ, KHÔNG bóc "mảnh đầu nào cũng bóc". Phép bóc rộng ấy đã
# dựng thành bản hỏng và ĐO: nó biến MỌI mục thật thành "(GỐC)", nên tên miền đang xếp "nhiều
# mục" tụt xuống một mục và bị nêu OAN — đo trên kho thật 07/08/2026 thì hudson.org · cepa.org
# · lowyinstitute.org · cset.georgetown.edu cùng lúc vào nhóm ★.
# ⚠️ ĐÍNH CHÍNH ngay trong lượt dựng: chú thích bản đầu ghi phép bóc rộng sẽ "xoá lỗ hình dạng
# Lowy khỏi bảng". SAI — bản hỏng cho thấy Lowy VẪN bị nêu (6 bài `the-interpreter/<slug>` bóc
# xong thành 6 bài "(GỐC)", vẫn là một mục duy nhất). Chiều hỏng thật là CHẶN OAN, không phải
# lọt. Suy luận nghe rất trôi mà sai dấu; chỉ bản hỏng mới tố ra.
TIEN_TO_NGON_NGU = frozenset({"en", "eng", "english"})

# Ứng viên ĐÃ SOI TẬN NƠI rồi — kèm lý do, để lần chạy sau không kêu lại. Đây là chỗ ghi kết
# quả triage, KHÔNG phải chỗ giấu ứng viên khó: mỗi dòng phải nói được đã soi cái gì.
DA_DUYET = {
    # ⚠️ `lowyinstitute.org` ĐÃ GỠ 07/08/2026 — đúng theo dòng dặn của chính nó. Kho nay 53 bài
    # chia `the-interpreter` (46) + `publications` (7), tên miền đã tự rời nhóm ★. Dòng duyệt
    # sống lâu hơn lý do của nó thì thành chỗ miễn trừ vĩnh viễn, nên gỡ đúng lúc mới là phần
    # thi hành của cơ chế này.
    "rusi.org":
        "SOI 07/08/2026, KHÔNG phải lỗ — phép đo không áp được cho lối đặt URL của RUSI. "
        "Fetch thật `/rss/latest-publications.xml`: 200, bài mới 06/08/2026, item rải ra "
        "`/news-and-comment/rusi-reflects/`, `/news-and-comment/video-commentary/`, "
        "`/explore-our-research/publications/rusi-newsbrief/` và `.../commentary/` — tức đường "
        "vào KHÔNG chỉ có một cửa. Kho dồn `explore-our-research (16)` vì RUSI để trọn mảng "
        "nghiên cứu dưới MỘT container, mục thật nằm ở mảnh thứ ba (`commentary` 15 · "
        "`rusi-defence-systems` 1). Cả feed bình luận lẫn feed nghiên cứu đều đã khai.",
    "aspi.org.au":
        "ĐÃ VÁ 07/08/2026 — LỖ THẬT, đúng hình dạng Lowy. `aspi.org.au/feed/` chỉ trả kiểu bài "
        "`post` (= `/report/`), nên mảng `/opinions/` chưa từng có đường vào; đã khai thêm "
        "`ASPI [BL]` = `/feed/?post_type=opinions` (fetch thật: 200 · 10 item · bài mới "
        "16/07/2026). Kho vẫn 10/10 bài `/report/` vì lô bài mục mới chưa nạp; nạp xong thì "
        "tên miền này tự rời danh sách, lúc đó GỠ dòng này đi.",
    "cacianalyst.org":
        "ĐÃ VÁ 07/08/2026 — LỖ THẬT. Viện có 04 mục, mới khai feed `analytical-articles`; đã "
        "khai thêm `CACI Analyst [FA]` = `/publications/feature-articles.feed` (fetch thật: "
        "200 · 10 item · bài mới 25/06/2026). Mục `field-reports` CÓ feed hợp lệ nhưng bài mới "
        "nhất là 03/10/2016 nên cố ý KHÔNG khai. Kho vẫn 6/6 bài `analytical-articles` vì lô "
        "bài mục mới chưa nạp; nạp xong thì tự rời danh sách, lúc đó GỠ dòng này đi.",
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
        if seg and seg[0].lower() in TIEN_TO_NGON_NGU:
            seg = seg[1:]
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

    # ── 08 đối chứng: `/en/` là tiền tố NGÔN NGỮ, không phải mục (thêm 07/08/2026 cùng bản vá)
    # Không bóc thì `icds.ee` hiện "en (7)" — một mục duy nhất — và bị nêu OAN suốt đời, vì
    # không feed nào sửa được chuyện đó. Ca dựng ở dạng bài CÓ mục thật dưới tiền tố, để đo
    # đúng phép bóc chứ không đo nhờ nhóm "bài ở gốc" gánh.
    k = phan_loai(_kho_gia([("https://vien-moi.org/en/publications/bai-%d", 5),
                            ("https://vien-moi.org/en/commentary/bai-%d", 4)]), co_feed)
    ra.append(("08 đối chứng — tiền tố ngôn ngữ /en/ KHÔNG được đọc thành mục",
               not k["nghi"] and [d for d, _, _ in k["nhieu_muc"]] == ["vien-moi.org"],
               f"tiền tố ngôn ngữ bị đọc thành mục ⇒ nêu oan: {k}"))

    # ── 09 chống NỚI phép bóc: mảnh KHÔNG phải tiền tố ngôn ngữ thì phải giữ nguyên làm mục.
    # ⚠️ Ca này đo đúng chiều hỏng ĐÃ ĐO ĐƯỢC (chặn oan), không phải chiều suy ra ban đầu. Bản
    # đầu của ca dựng kho hình dạng Lowy rồi đòi nó "vẫn bị nêu" — chạy bản hỏng mới thấy Lowy
    # bị nêu ở CẢ hai bản, tức ca xanh trên cả hai và không canh được gì. Nay ca neo vào tên
    # miền có mục THẬT: bóc rộng làm `report` và `commentary` cùng biến thành "(GỐC)".
    k = phan_loai(_kho_gia([("https://vien-moi.org/report/bai-%d", 5),
                            ("https://vien-moi.org/commentary/bai-%d", 4)]), co_feed)
    ra.append(("09 chống nới — mảnh KHÔNG phải tiền tố ngôn ngữ phải được giữ làm mục",
               not k["nghi"] and dict(k["nhieu_muc"][0][2]) == {"report": 5, "commentary": 4}
               if k["nhieu_muc"] else False,
               f"phép bóc nới quá tay, mục thật bị xoá thành (GỐC) ⇒ nêu oan: {k}"))
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
    # ── 02 bản hỏng canh HAI CHIỀU của phép bóc tiền tố ngôn ngữ (thêm 07/08/2026) ──
    # ⚠️ Chuỗi neo dưới đây CỐ Ý CẮT LÀM ĐÔI (`"…NGON" "_NGU:…"`). Phép đếm chạy trên TOÀN VĂN
    # file, nên một chuỗi neo viết liền sẽ khớp cả dòng mã lẫn chính dòng khai này ⇒ "khớp 3
    # chỗ (phải đúng 1)" và không bản hỏng nào dựng được. Sáu dòng phía trên thoát được là nhờ
    # chúng có dấu nháy phải escape (`\"`) nên văn bản nguồn khác văn bản mã — ở đây không có
    # dấu nháy nào, phải cắt tay. Đừng "dọn cho gọn" bằng cách nối lại.
    ("gỡ phép bóc tiền tố ngôn ngữ — `/en/` bị đọc thành mục, nêu oan vĩnh viễn",
     "        if seg and seg[0].lower() in TIEN_TO_NGON" "_NGU:\n            seg = seg[1:]",
     "        if False:\n            seg = seg[1:]", [8]),
    # Chiều NỚI phải dựng bằng cách THAY phép bóc, không gỡ được: cơ chế BAN_HONG chỉ tháo lớp
    # bảo vệ, mà ở đây thiệt hại đến từ việc bóc RỘNG HƠN chứ không phải bóc hụt.
    # Khai [2, 9] chứ không khai ca 06: bản hỏng này cũng làm ca 06 đỏ (hudson · cepa · lowy ·
    # cset), nhưng ca 06 đọc kho THẬT nên danh sách ấy đổi theo từng đợt nạp bài — neo vào nó
    # là dựng một ca chập chờn, mà ca chập chờn dạy người đọc bỏ qua màu đỏ.
    ("NỚI phép bóc thành 'mảnh đầu nào cũng bóc' — mục thật thành (GỐC), nêu oan hàng loạt",
     "        if seg and seg[0].lower() in TIEN_TO_NGON" "_NGU:",
     "        if seg:", [2, 9]),
]


if __name__ == "__main__":
    if "--tu-kiem" in sys.argv:
        sys.exit(tu_kiem())
    if "--ca" in sys.argv:            # chạy bộ ca, dùng bởi chính --tu-kiem
        sys.exit(tu_kiem_chay())
    sys.exit(bao_cao())
