#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CỔNG NGHIỆM THU việc vá lỗ "bảng nguồn think-tank chỉ khai feed BLOG" (dựng 06/08/2026).

VÌ SAO CẦN — lỗ này thuộc loại hỏng thì im lặng, đúng nghĩa. `add_analyses.py` khai Lowy
Institute bằng đúng một feed: `the-interpreter/rss.xml`, tức mục BÌNH LUẬN NGẮN. Mục NGHIÊN
CỨU của chính viện đó (`/publications/rss.xml`) chưa từng được khai, mà feed ấy sống bình
thường (đo 06/08/2026: HTTP 200, 50 item). Hậu quả đo được:

| Đo trên `data/analyses.json` 06/08/2026 | Con số |
|---|---|
| Bài Lowy, thảy đều thuộc `/the-interpreter/` | 35/35 |
| Bài Lowy thuộc `/publications/` | 0 |
| Bài ASPI, thảy đều thuộc blog `aspistrategist.org.au` | 81/81 |
| Bài ASPI thuộc `aspi.org.au` (báo cáo viện) | 0 |

Không dấu hiệu nào phát ra: feed blog vẫn ra bài đều, danh sách ứng viên vẫn đầy, mục web
vẫn có bài mới mỗi sáng. Chỉ khi Huy đi tìm một nghiên cứu cụ thể ("Understanding the Chinese
military threat to Australia", Lowy đăng 14/06/2026) mới lộ ra là kho chưa từng có nó.

LỚP THỨ HAI của cùng một lỗ: `MAX_AGE_DAYS = 7` nên kể cả khai đúng feed nghiên cứu thì một
báo cáo đăng 14/06 vẫn không bao giờ vào danh sách ứng viên — nghiên cứu dài ra theo tháng,
routine thì quét theo ngày. Vì vậy cổng này đo CẢ đường nạp quét theo tháng.

    python3 tests/test-nguon-nghien-cuu.py
    python3 tests/test-nguon-nghien-cuu.py --tu-kiem   # chứng minh bộ ca BẮT ĐƯỢC lỗi

⚠️ Cổng KHÔNG chạm mạng — chỉ đọc mã nguồn trên đĩa. Bốn feed dưới đây đã fetch thật một lần
lúc dựng (06/08/2026), kết quả ghi trong `FEED_NGHIEN_CUU`; đừng fetch lại mỗi lượt chạy, kẻo
cổng đỏ vì nguồn ngoài chập chờn chứ không phải vì mã hỏng.
"""
import importlib.util
import os
import pathlib
import re
import sys

sys.dont_write_bytecode = True

REPO = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = pathlib.Path(os.environ.get("ADD_ANALYSES", REPO / "scripts" / "add_analyses.py"))
KHOE = pathlib.Path("/Users/Huy/Claude/HeThong/khoe.py")

# ĐÃ FETCH THẬT 06/08/2026 (curl có UA trình duyệt + --compressed). Cột 3 = mục đầu đường dẫn
# của bài, dùng để phân biệt với feed blog đang khai — hai feed cùng viện mà ra chung một mục
# thì khai thêm chẳng được gì.
FEED_NGHIEN_CUU = [
    ("Lowy Institute", "https://www.lowyinstitute.org/publications/rss.xml", "/publications/"),
    ("ASPI", "https://www.aspi.org.au/feed/", "/report/"),
    ("RUSI", "https://www.rusi.org/rss/latest-publications.xml", "/explore-our-research/"),
    ("CSET", "https://cset.georgetown.edu/publications/feed/", "/publication/"),
]

# Feed BLOG đang khai — phải CÒN NGUYÊN. Ca đối chứng chống chặn oan: việc này là THÊM mục
# nghiên cứu, không phải thay blog bằng nghiên cứu. Thay là mất 35 bài Interpreter/năm.
FEED_BLOG_PHAI_GIU = [
    "https://www.lowyinstitute.org/the-interpreter/rss.xml",
    "https://www.aspistrategist.org.au/feed/",
    "https://www.rusi.org/rss/latest-commentary.xml",
    "https://cset.georgetown.edu/feed/",
]

# Feed publications của RUSI đẩy CẢ podcast và bản ghi sự kiện vào chung (đo 06/08: 5 mục
# riêng so với feed commentary thì 4 là podcast/recording). Không lọc thì mục Think-tank đầy
# "Episode 125 — Japan's intelligence reforms".
NHIEU_RUSI = ("/podcasts/", "event-recordings")

# Domain phải có trong THINKTANK_DOMAINS, nếu không thì quét ra bài rồi tới lúc NẠP mới bị
# guardrail chặn — hỏng ở một chỗ, lộ ra ở chỗ khác.
DOMAIN_PHAI_CO = ["aspi.org.au", "cset.georgetown.edu", "rusi.org", "lowyinstitute.org"]


def nap():
    spec = importlib.util.spec_from_file_location("aa_kiem", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def chay():
    """Trả danh sách (tên ca, đạt, lời). Ca có tiền tố ★ là ca PHẢI CHẶN."""
    ra = []
    nguon = SCRIPT.read_text(encoding="utf-8")
    mod = nap()
    urls_feed = {u for _, u, *_ in mod.THINKTANK_FEEDS}

    # ── 01 ★ mỗi viện có feed nghiên cứu đều phải được khai
    for ten, url, muc in FEED_NGHIEN_CUU:
        ra.append((
            f"★ 01 feed nghiên cứu {ten} ({muc}) đã khai",
            url in urls_feed,
            f"thiếu {url} trong THINKTANK_FEEDS",
        ))

    # ── 02 ca ĐỐI CHỨNG: feed blog không được thay mất
    for url in FEED_BLOG_PHAI_GIU:
        ra.append((
            f"02 đối chứng — feed blog còn nguyên: {url.split('/')[2]}",
            url in urls_feed,
            f"feed blog {url} bị gỡ — việc này là THÊM mục nghiên cứu, không phải thay",
        ))

    # ── 03 ★ domain của feed mới phải nằm trong guardrail domain
    for d in DOMAIN_PHAI_CO:
        ra.append((
            f"★ 03 domain {d} trong THINKTANK_DOMAINS",
            d in mod.THINKTANK_DOMAINS,
            f"{d} thiếu ⇒ quét ra bài rồi guardrail chặn lúc nạp",
        ))

    # ── 04 ★ lọc podcast/bản ghi sự kiện của feed publications RUSI
    noise = " ".join(mod.NOISE_PATHS)
    for m in NHIEU_RUSI:
        ra.append((
            f"★ 04 NOISE_PATHS lọc {m}",
            m in noise,
            f"thiếu {m} ⇒ mục Think-tank lọt podcast và bản ghi sự kiện RUSI",
        ))

    # ── 05 ★ đường nạp quét theo THÁNG, tách khỏi khung ngày của routine
    co_duong = bool(re.search(r"--candidates-dai|--thang|MAX_AGE_DAYS_DAI", nguon))
    ra.append((
        "★ 05 có đường nạp bài dài quét theo tháng",
        co_duong,
        "chưa có cờ quét khung rộng ⇒ nghiên cứu đăng 6 tuần trước không bao giờ vào ứng viên",
    ))
    khung = re.search(r"MAX_AGE_DAYS_DAI\s*=\s*(\d+)", nguon)
    ra.append((
        "★ 06 khung quét dài ≥ 30 ngày",
        bool(khung) and int(khung.group(1)) >= 30,
        "MAX_AGE_DAYS_DAI thiếu hoặc < 30 — khung hẹp thì đường nạp mới không giải quyết gì",
    ))

    # ── 07 ★ phép đo canh chính lỗ này, chạy tự động
    bo_test = REPO / "tests" / "test-nguon-nghien-cuu.py"
    ra.append((
        "★ 07 bộ test này đã nạp vào khoe.py",
        KHOE.exists() and "test-nguon-nghien-cuu.py" in KHOE.read_text(encoding="utf-8"),
        f"chưa khai {bo_test} trong BO_TEST của khoe.py ⇒ cổng không ai chạy",
    ))

    # ── 08 ★ phép đo phát hiện nguồn chỉ ra bài từ MỘT mục (chống tái diễn ở viện khác)
    do = REPO / "scripts" / "do_nguon_mot_muc.py"
    ra.append((
        "★ 08 có phép đo tự dò nguồn chỉ khai một mục",
        do.exists(),
        f"thiếu {do} — vá 4 viện hôm nay không chặn được viện thứ 5 mai mốt",
    ))
    return ra


def main():
    ra = chay()
    hong = 0
    for ten, dat, loi in ra:
        print(("  ✓ " if dat else "  ✗ ") + ten + ("" if dat else "  — " + loi))
        hong += 0 if dat else 1
    print(f"\n{len(ra) - hong}/{len(ra)} ca đạt" + ("" if not hong else f" · {hong} KHÔNG ĐẠT"))
    return 1 if hong else 0


# Bảng đặt CUỐI FILE, sau mã — neo trỏ vào chính dòng khai là bản hỏng "hỏng" ở bảng chứ
# không ở mã (luật khung_tu_kiem, mục 17 CLAUDE.md).
#
# ⚠️ BẢN HỎNG PHẢI GỠ LỚP VÁ TRONG `scripts/add_analyses.py`, KHÔNG PHẢI GỠ CA KHỎI FILE NÀY.
# Bản đầu của `tu_kiem` làm ngược: nó xoá dòng khai ca ra khỏi chính bộ test rồi chạy lại.
# Khi đó bộ test còn ÍT CA HƠN nhưng mọi ca còn lại vẫn xanh ⇒ mã thoát 0 ⇒ báo "bản hỏng
# không bị bắt" cho cả 3 bản, trong khi cổng hoàn toàn khoẻ. Đo thật 06/08/2026: 0/3. Gỡ ca
# ra khỏi bộ đo không chứng minh được gì về bộ đo — thứ phải hỏng là VẬT BỊ ĐO.
BAN_HONG = [
    # Neo kèm NHÃN viện: url của feed nghiên cứu còn xuất hiện lần nữa ở `URL_NGHIEN_CUU`
    # (danh sách feed mà `--candidates-dai` quét), neo bằng url trần thì khớp 2 chỗ.
    ("gỡ feed nghiên cứu Lowy khỏi bảng nguồn",
     '("Lowy Institute [NC]", "https://www.lowyinstitute.org/publications/rss.xml",',
     '("Lowy Institute [NC]", "https://www.lowyinstitute.org/KHONG-CO/rss.xml",'),
    ("gỡ feed báo cáo ASPI khỏi bảng nguồn",
     '("ASPI [NC]", "https://www.aspi.org.au/feed/",',
     '("ASPI [NC]", "https://www.aspi.org.au/KHONG-CO/",'),
    ("gỡ lọc podcast/bản ghi sự kiện của feed RUSI", '"/podcasts/"', '"/khong-loc-gi/"'),
    ("hạ khung quét dài về đúng khung ngày của routine",
     "MAX_AGE_DAYS_DAI = ", "MAX_AGE_DAYS_DAI = 7  #"),
]


def tu_kiem():
    """Dựng bản `add_analyses.py` HỎNG rồi chứng minh cổng này ĐỎ trên bản đó."""
    import hashlib
    import subprocess
    goc = SCRIPT.read_text(encoding="utf-8")

    # Ca đỏ trên bản ĐÚNG thì mọi phép so bên dưới mất nghĩa — bản hỏng cũng đỏ y hệt nên
    # không lệch gì, và `--tu-kiem` sẽ in ✅ trong khi cổng đang trượt (luật mục 18 CLAUDE.md).
    r0 = subprocess.run([sys.executable, str(pathlib.Path(__file__))],
                        capture_output=True, text=True, env={**os.environ})
    if r0.returncode != 0:
        print(r0.stdout.rstrip())
        print("\n⛔ CÒN CA ĐỎ TRÊN BẢN ĐÚNG — sửa cho hết đỏ rồi mới dựng bản hỏng.")
        return 1

    tong = 0
    for ten, tim, thay in BAN_HONG:
        if goc.count(tim) != 1:
            print("  ✗ %s — chuỗi neo khớp %d chỗ (phải đúng 1)" % (ten, goc.count(tim)))
            tong += 1
            continue
        noi = goc.replace(tim, thay, 1)
        dich = SCRIPT.parent / ("_thu-hong-%d-%s-%s" % (
            os.getpid(), hashlib.sha1(noi.encode()).hexdigest()[:8], SCRIPT.name))
        dich.write_text(noi, encoding="utf-8")
        try:
            r = subprocess.run([sys.executable, str(pathlib.Path(__file__))],
                               capture_output=True, text=True,
                               env={**os.environ, "ADD_ANALYSES": str(dich)})
            bat = r.returncode != 0
            print(("  ✓ " if bat else "  ✗ ") + ten + ("" if bat else " — bản hỏng KHÔNG bị bắt"))
            tong += 0 if bat else 1
        finally:
            dich.unlink(missing_ok=True)
    print(f"\n{len(BAN_HONG) - tong}/{len(BAN_HONG)} bản hỏng bị bắt")
    return 1 if tong else 0


if __name__ == "__main__":
    sys.exit(tu_kiem() if "--tu-kiem" in sys.argv else main())
