#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TEST HỒI QUY: NGÀY ĐĂNG CỦA ITEM FEED + GÁN CỨNG CHỦ ĐỀ CHO NGUỒN ANH — vá 05/09/2026.

⚠ VÌ SAO CÓ FILE NÀY (Huy hỏi 05/09/2026: *"sao điểm tin sáng nay không có tin của Anh
vậy?"*). Bản tin sáng 05/09 mục "Úc, Anh & Biển Đông" có 02 tin, không tin nào về nước Anh,
trong khi các feed Anh hôm đó có bài thật trong khung ngày. Truy ra HAI lỗi câm chồng nhau:

  - `harvest.parse_date` cắt chuỗi theo độ dài cố định 24 ký tự (mẫu `+0000`) trước khi đưa
    vào `strptime`. Múi giờ Atom viết có dấu hai chấm (`+01:00`) dài 25, bị cắt cụt thành
    `+01:0` → `%z` trượt → trả None. Đo 05/09/2026: **20/20 item** của feed Atom Bộ Quốc
    phòng Anh (gov.uk) ra ngày `?`, nên phiên quét nào cũng coi là không rõ ngày rồi loại.
  - `harvest` chỉ gán cứng chủ đề theo TÊN feed, và bảng chỉ có hai nguồn Mỹ. Tiêu đề của
    gov.uk phần lớn không tự nhắc "UK"/"British" ("Key milestone reached for future Navy
    support ship", "CDLS Industry Commendations 2026"), nên `match_topic` không neo được và
    12/20 item rơi hẳn kể cả khi đã đọc đúng ngày.

Cả hai lỗi đều IM LẶNG: feed vẫn sống, bảng nguồn vẫn xanh, phiên quét vẫn báo DONE, chỉ có
mục tin nước Anh lặng lẽ rỗng. => Mọi ca gắn nhãn PHẢI CHẶN là ca dựng đúng điều kiện xấu
rồi khẳng định mã THẬT SỰ bắt được. Test chỉ có ca "phải cho qua" là chưa test.

Chạy:
    python3 tests/test-ngay-feed-va-gan-chu-de.py
    python3 tests/test-ngay-feed-va-gan-chu-de.py --tu-kiem   # chứng minh test BẮT ĐƯỢC lỗi

`--tu-kiem` dựng bản sao repo ĐÃ GỠ ĐÚNG DÒNG VÁ rồi chạy lại chính bộ ca này; mỗi bản hỏng
phải làm ĐỎ đúng những ca đã khai. Xanh trên cả bản đúng lẫn bản hỏng là test vô dụng.

⚠ Bản hỏng KHÔNG ghi đè file thật — nhiều phiên Claude chạy song song trên cùng repo
(CLAUDE.md toàn cục, mục 9b), ghi đè là xoá việc của phiên khác.

Cả bộ ca chạy OFFLINE: không gọi mạng, không phụ thuộc feed hôm nay còn bài hay không.
"""
import datetime
import hashlib
import importlib.util
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

# Seam để tự kiểm: trỏ sang một BẢN SAO repo khác.
REPO = pathlib.Path(os.environ.get("NGAYFEED_REPO",
                                   pathlib.Path(__file__).resolve().parent.parent))


def _nap():
    sys.path.insert(0, str(REPO / "scripts"))
    spec = importlib.util.spec_from_file_location("harvest_dut", REPO / "scripts" / "harvest.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


H = _nap()
D = datetime.date

# ── mẫu XML thật, cắt từ feed ngày 05/09/2026 (không gọi mạng) ─────────────────
ATOM_GOVUK = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Key milestone reached for future Navy support ship</title>
    <link href="https://www.gov.uk/government/news/key-milestone"/>
    <updated>2026-09-03T15:08:50+01:00</updated>
  </entry>
  <entry>
    <title>CDLS Industry Commendations 2026</title>
    <link href="https://www.gov.uk/government/news/cdls-2026"/>
    <updated>2026-09-04T09:15:02+01:00</updated>
  </entry>
</feed>
"""

URL_GOVUK = ("https://www.gov.uk/search/news-and-communications.atom"
             "?organisations%5B%5D=ministry-of-defence")

CA = []


def ca(so, mo_ta):
    def deco(fn):
        CA.append((so, mo_ta, fn))
        return fn
    return deco


# ═══════════════ nhóm 1: đọc ngày (ca 1-8) ═══════════════
@ca(1, "PHẢI CHẶN — múi giờ có dấu hai chấm '+01:00' (Atom gov.uk) phải ra ĐÚNG ngày")
def _():
    # 15:08 giờ London (+01:00) = 21:08 giờ VN cùng ngày.
    assert H.parse_date("2026-09-03T15:08:50+01:00") == D(2026, 9, 3)


@ca(2, "PHẢI CHẶN — '+01:00' lúc nửa đêm London phải quy sang ngày VN kế tiếp")
def _():
    # 23:30 ngày 03 giờ London = 05:30 ngày 04 giờ VN. Sai múi giờ là lệch nguyên một ngày,
    # đủ để tin rơi ra ngoài khung 2 ngày.
    assert H.parse_date("2026-09-03T23:30:00+01:00") == D(2026, 9, 4)


@ca(3, "múi giờ 'Z' (UTC) vẫn đọc đúng")
def _():
    assert H.parse_date("2026-09-04T02:00:00Z") == D(2026, 9, 4)


@ca(4, "múi giờ dạng '+0000' không dấu hai chấm vẫn đọc đúng")
def _():
    assert H.parse_date("2026-09-04T00:00:00+0000") == D(2026, 9, 4)


@ca(5, "RFC 822 (pubDate của RSS 2.0) vẫn đọc đúng")
def _():
    assert H.parse_date("Fri, 04 Sep 2026 07:30:00 +0000") == D(2026, 9, 4)


@ca(6, "ngày trần '2026-09-04' vẫn đọc đúng")
def _():
    assert H.parse_date("2026-09-04") == D(2026, 9, 4)


@ca(7, "chuỗi rác và rỗng phải trả None, không được đoán bừa")
def _():
    for rac in ("", None, "hôm qua", "not a date", "2026-13-45T99:99:99+01:00"):
        assert H.parse_date(rac) is None, rac


@ca(8, "PHẢI CHẶN — 2/2 item của feed Atom gov.uk phải đọc ra ngày, không item nào ra '?'")
def _():
    raw = H.items_of(ATOM_GOVUK)
    assert len(raw) == 2, raw
    ngay = [H.parse_date(p) for _, _, p, _ in raw]
    assert all(n is not None for n in ngay), f"còn item ra ngày ?: {ngay}"
    assert ngay == [D(2026, 9, 3), D(2026, 9, 4)], ngay


# ═══════════════ nhóm 2: gán cứng chủ đề (ca 11-16) ═══════════════
@ca(11, "PHẢI CHẶN — tin gov.uk KHÔNG có chữ UK/British trong tiêu đề vẫn phải vào chủ đề 2")
def _():
    # Đây chính là 12/20 item đã rơi câm trước bản vá.
    assert H.match_topic("Key milestone reached for future Navy support ship", "both") != \
        "Úc & Biển Đông", "ca này chỉ có nghĩa khi match_topic KHÔNG tự neo được"
    assert H.forced_topic("**GOV.UK — Bộ Quốc phòng Anh**", URL_GOVUK) == "Úc & Biển Đông"


@ca(12, "PHẢI CHẶN — gán cứng tra theo URL, đổi tên feed trong bảng CLAUDE.md không làm hỏng")
def _():
    # Tên trong bảng có đánh dấu in đậm; sửa bảng bỏ đậm là hỏng câm nếu tra theo tên.
    assert H.forced_topic("GOV.UK Bo Quoc phong Anh", URL_GOVUK) == "Úc & Biển Đông"
    assert H.forced_topic("tên bất kỳ", "https://ukdefencejournal.org.uk/feed/") == "Úc & Biển Đông"
    assert H.forced_topic("tên bất kỳ", "https://navylookout.com/feed/") == "Úc & Biển Đông"


@ca(13, "PHẢI CHẶN — BBC News UK và Guardian Politics CỐ Ý không được gán cứng")
def _():
    # Hai feed đó trộn thể thao, tội phạm địa phương, giải trí — gán cứng là kéo rác vào.
    assert H.forced_topic("**BBC News UK**", "https://feeds.bbci.co.uk/news/uk/rss.xml") is None
    assert H.forced_topic("**The Guardian — Politics (Anh)**",
                          "https://www.theguardian.com/politics/rss") is None


@ca(14, "gán cứng theo TÊN của hai nguồn Mỹ cũ vẫn còn tác dụng")
def _():
    assert H.forced_topic("DoD Contracts", "https://www.war.gov/contracts.xml") == "CNQS Mỹ"
    assert H.forced_topic("DoD News Releases", "https://www.war.gov/news.xml") == "CNQS Mỹ"


@ca(15, "feed lạ không nằm trong bảng nào thì KHÔNG được gán cứng")
def _():
    assert H.forced_topic("Báo lạ", "https://vnexpress.net/rss/tin-moi-nhat.rss") is None


@ca(16, "PHẢI CHẶN — hai lỗi ghép: item gov.uk phải vừa có ngày vừa có chủ đề")
def _():
    # Ca gác cả đường đi: đọc feed → ra ngày → gán chủ đề. Gỡ một trong hai lớp vá là đỏ.
    raw = H.items_of(ATOM_GOVUK)
    forced = H.forced_topic("**GOV.UK — Bộ Quốc phòng Anh**", URL_GOVUK)
    lot = [(H.parse_date(p), forced or H.match_topic(t, "both")) for t, _, p, _ in raw]
    assert all(n is not None and c == "Úc & Biển Đông" for n, c in lot), lot


# ═══════════════════════════ tự kiểm: bản hỏng ═══════════════════════════
# (nhãn · phép thay trong scripts/harvest.py · các ca BẮT BUỘC phải đỏ)
BAN_HONG = [
    ("parse_date: bỏ nhánh fromisoformat (đưa lại bệnh cắt cụt '+01:00')",
     ('    try:\n'
      '        d = datetime.datetime.fromisoformat(raw.replace("Z", "+00:00"))\n'
      '        return d.astimezone(VN).date() if d.tzinfo else d.date()\n'
      '    except Exception:\n'
      '        pass\n'),
     '',
     [1, 2, 8, 16]),

    ("parse_date: cắt lại chuỗi theo độ dài cố định trước khi đọc",
     '    raw = raw.strip()\n',
     '    raw = raw.strip()[:len("2026-07-27T00:00:00+0000")]\n',
     [1, 2, 8, 16]),

    ("parse_date: bỏ quy đổi múi giờ, lấy thẳng ngày theo giờ gốc",
     '        return d.astimezone(VN).date() if d.tzinfo else d.date()',
     '        return d.date()',
     [2]),

    ("harvest_rss: quay lại tra gán cứng chỉ theo TÊN feed (nguồn Anh rơi câm)",
     '''def forced_topic(name: str, url: str):
    """Chủ đề gán cứng cho một feed, tra theo tên trước rồi tới URL."""
    t = FORCE_TOPIC.get(name)
    if t:
        return t
    for manh, chu_de in FORCE_TOPIC_URL.items():
        if manh in (url or ""):
            return chu_de
    return None''',
     '''def forced_topic(name: str, url: str):
    return FORCE_TOPIC.get(name)''',
     [11, 12, 16]),

    ("FORCE_TOPIC_URL: nhét thêm BBC News UK (kéo rác thể thao/địa phương vào chủ đề 2)",
     '    "navylookout.com": "Úc & Biển Đông",',
     '    "navylookout.com": "Úc & Biển Đông",\n    "feeds.bbci.co.uk": "Úc & Biển Đông",',
     [13]),

    ("forced_topic: luôn trả 'Úc & Biển Đông' (cổng câm, cái gì cũng nhận)",
     '''    t = FORCE_TOPIC.get(name)
    if t:
        return t''',
     '''    return "Úc & Biển Đông"
    t = FORCE_TOPIC.get(name)
    if t:
        return t''',
     [13, 14, 15]),
]


def chay_ca() -> int:
    print(f"BỘ CA — ngày đăng feed + gán cứng chủ đề nguồn Anh  (repo: {REPO})")
    print("=" * 78)
    do = 0
    for so, mo_ta, fn in CA:
        try:
            fn()
            print(f"  ✓ {so}. {mo_ta}")
        except Exception as e:
            do += 1
            print(f"  ✗ {so}. {mo_ta}\n        │ {type(e).__name__}: {e}")
    print("=" * 78)
    if do:
        print(f"✗ {do}/{len(CA)} ca ĐỎ")
        return 1
    print(f"✓ {len(CA)}/{len(CA)} ca xanh")
    return 0


def _dung_ban_sao(d: pathlib.Path, tim: str, thay: str):
    (d / "scripts").mkdir(parents=True)
    goc = pathlib.Path(__file__).resolve().parent.parent
    for f in ("harvest.py", "topics.py", "tap_tran.py"):
        shutil.copy2(goc / "scripts" / f, d / "scripts" / f)
    shutil.copy2(goc / "CLAUDE.md", d / "CLAUDE.md")
    p = d / "scripts" / "harvest.py"
    p.write_text(p.read_text(encoding="utf-8").replace(tim, thay, 1), encoding="utf-8")


def tu_kiem() -> int:
    print("TỰ KIỂM — dựng bản repo đã gỡ dòng vá, các ca đã khai PHẢI ĐỎ")
    print("=" * 78)
    goc = (pathlib.Path(__file__).resolve().parent.parent / "scripts" / "harvest.py"
           ).read_text(encoding="utf-8")
    hong = 0
    for nhan, tim, thay, ca_phai_do in BAN_HONG:
        if goc.count(tim) != 1:
            print(f"  ✗ {nhan}\n        │ KHÔNG áp được phép thay: {goc.count(tim)} chỗ khớp "
                  f"(cần đúng 1). Mã nguồn đã đổi → sửa lại test.")
            hong += 1
            continue
        dau = hashlib.sha1((tim + thay).encode()).hexdigest()[:8]
        d = pathlib.Path(tempfile.mkdtemp(prefix=f"ngayfeed-{os.getpid()}-{dau}-"))
        try:
            _dung_ban_sao(d, tim, thay)
            env = dict(os.environ, NGAYFEED_REPO=str(d))
            r = subprocess.run([sys.executable, str(pathlib.Path(__file__).resolve())],
                               capture_output=True, text=True, env=env)
        finally:
            shutil.rmtree(d, ignore_errors=True)
        do = {int(dong[4:].split(".")[0])
              for dong in r.stdout.splitlines() if dong.startswith("  ✗ ")}
        if len(do) == len(CA):
            print(f"  ✗ {nhan}\n        │ MỌI ca đều đỏ → phép thay nhiều khả năng làm vỡ "
                  f"cú pháp chứ không chứng minh ca nào có răng.")
            hong += 1
            continue
        thieu = set(ca_phai_do) - do
        thua = do - set(ca_phai_do)
        ok = not thieu
        print(f"  {'✓' if ok else '✗'} {nhan}")
        print(f"        │ ca đỏ: {sorted(do) or 'KHÔNG CÓ CA NÀO ĐỎ'} · cần đỏ: {ca_phai_do}"
              + (f" · đỏ thêm ngoài dự kiến: {sorted(thua)}" if thua else ""))
        if not ok:
            hong += 1
    print("=" * 78)
    if hong:
        print(f"✗ {hong}/{len(BAN_HONG)} phép thử tự kiểm THẤT BẠI — bộ test chưa chứng minh "
              "được là có răng.")
        return 1
    print(f"✓ {len(BAN_HONG)}/{len(BAN_HONG)} bản hỏng đều bị bắt — bộ test này có giá trị.")
    return 0


def main() -> int:
    if "--tu-kiem" in sys.argv:
        return tu_kiem()
    return chay_ca()


if __name__ == "__main__":
    sys.exit(main())
