#!/usr/bin/env python3
"""Đo nguồn của harvest.py có THẬT SỰ lấy được bài không — chống "nguồn chết câm".

    python3 scripts/kiem_nguon.py            # đo nhóm TRỌNG YẾU (nhanh, ~20 nguồn)
    python3 scripts/kiem_nguon.py --tat-ca   # đo mọi feed + trang HTML trong CLAUDE.md
    python3 scripts/kiem_nguon.py --json /tmp/kq.json

Mã thoát: 0 = mọi nguồn trọng yếu còn sống · 1 = có nguồn hỏng · 2 = không đo được.

VÌ SAO CÓ SCRIPT NÀY (30/07/2026, sau khi Huy bắt được vụ kho nền QuanSu khai
"defence.gov.au timeout hoàn toàn" trong khi 19/19 URL trả 200 qua trình duyệt):
nguồn bị chặn KHÔNG kêu. Nó chỉ đơn giản là không đóng góp ứng viên nào — giống hệt
một feed sống mà hôm nay không có bài hợp chủ đề. Không có gì phân biệt hai ca đó,
nên Breaking Defense (403 với curl trần) nằm chết trong bảng nguồn nhiều ngày trong
khi CLAUDE.md vẫn ghi nó "25 item, mới 2h".

ĐO QUA CHÍNH `harvest.curl` — cố ý, đừng viết lại phép lấy nội dung ở đây: hai bộ luật
song song chắc chắn lệch nhau, mà lệch âm thầm. Sửa đường lấy trong harvest.py thì phép
đo này tự đo theo đường mới.
"""
import argparse
import json
import pathlib
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import harvest  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Nhóm TRỌNG YẾU: mỗi chủ đề vài nguồn chủ lực, CỘNG toàn bộ nguồn đã đo được là phải đi
# bằng vân tay TLS Chrome (30/07/2026) — đó là nhóm dễ chết câm nhất, vì chúng trả 403
# kèm thân dài trông như XML hợp lệ.
# ⚠️ Giữ danh sách NGẮN: phép đo này chạy trong `/khoe` mỗi sáng, dài quá thì thành ra
# một vòng quét thứ hai.
TRONG_YEU = [
    # (tên, url, loại, có phải nguồn từng bị chặn vân tay không)
    ("Breaking Defense", "https://breakingdefense.com/full-rss-feed/", "RSS", True),
    ("Naval Technology", "https://www.naval-technology.com/feed/", "RSS", True),
    ("Lục quân Mỹ — army.mil", "https://www.army.mil/rss/static/1.xml", "RSS", True),
    ("UB Quân vụ Thượng viện", "https://www.armed-services.senate.gov/press-releases", "HTML", True),
    ("UB Đối ngoại Thượng viện", "https://www.foreign.senate.gov/press", "HTML", True),
    ("UB Chuẩn chi Thượng viện", "https://www.appropriations.senate.gov/news/majority", "HTML", True),
    ("UB Tư pháp Hạ viện", "https://judiciary.house.gov/media/press-releases", "HTML", False),
    ("Defense News", "https://www.defensenews.com/arc/outboundfeeds/rss/category/global/?outputType=xml", "RSS", False),
    ("Defense One", "https://www.defenseone.com/rss/all/", "RSS", False),
    ("DoD Contracts", "https://www.war.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=400&Site=945&max=20", "RSS", False),
    ("DVIDS (toàn bộ)", "https://www.dvidshub.net/rss/all", "RSS", False),
    ("The War Zone (TWZ)", "https://www.twz.com/feed", "RSS", False),
    ("Long War Journal (Mali)", "https://www.longwarjournal.org/feed", "RSS", False),
    ("AllAfrica", "https://allafrica.com/tools/headlines/rdf/latest/headlines.rdf", "RSS", False),
    ("Lowy Interpreter", "https://www.lowyinstitute.org/the-interpreter/rss.xml", "RSS", False),
    ("ABC News AU", "https://www.abc.net.au/news/feed/51120/rss.xml", "RSS", False),
    ("Philstar", "https://www.philstar.com/rss/headlines", "RSS", False),
    ("Inquirer", "https://www.inquirer.net/fullfeed/", "RSS", False),
    ("Nhà Trắng — Presidential Actions", "https://www.whitehouse.gov/presidential-actions/feed/", "RSS", False),
    ("The Hill", "https://thehill.com/feed/", "RSS", False),
]

# Nguồn ĐÃ ĐO là chặn cả hai đường từ máy local (30/07/2026) — CI runner Mỹ vẫn lấy được,
# nên chúng KHÔNG phải lỗi cần sửa, chỉ là phần local không gánh nổi. Đo vẫn đo, nhưng
# hỏng thì ghi VÀNG chứ không ĐỎ: kêu ĐỎ mỗi sáng cho một thứ không sửa được thì vài hôm
# là hết ai đọc bảng, lúc nguồn khác chết thật cũng không ai thấy.
CHI_CI_LAY_DUOC = {
    "https://thediplomat.com/feed/",
    "https://www.af.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=1&max=20",
    "https://www.census.gov/newsroom/press-releases.html",
    "https://www.occ.treas.gov/news-events/newsroom/news-issuances-by-year/news-releases/index-news-releases.html",
}


def dem_item(body: bytes) -> int:
    """Số <item>/<entry> parse được. -1 = không phải XML."""
    try:
        root = ET.fromstring(body)
    except Exception:
        return -1
    return sum(1 for it in root.iter() if it.tag.split("}")[-1] in ("item", "entry"))


def do_mot(ten, url, loai):
    """Đo một nguồn qua ĐÚNG đường harvest.py dùng. Trả dict kết quả."""
    body = harvest.curl(url)
    item = dem_item(body)
    if loai == "RSS":
        dat = item > 0
        ly_do = "" if dat else (
            "thân rỗng" if not body else
            ("bị chặn (thân mang dấu hiệu 403/Access Denied)"
             if harvest._nghi_bi_chan(body) else "parse được nhưng 0 item"))
    else:
        # Trang HTML: đạt khi lấy được thân đủ dài và KHÔNG mang dấu hiệu chặn.
        # Ngưỡng 8000 byte lấy từ đo thật: thân 403 của các trang này dài 394–19.357 byte
        # nhưng luôn mang dấu hiệu, còn trang thật nhỏ nhất (foreign.senate.gov) 40.000+.
        dat = bool(body) and not harvest._nghi_bi_chan(body) and len(body) > 8000
        ly_do = "" if dat else (
            "thân rỗng" if not body else
            ("bị chặn (thân mang dấu hiệu 403/Access Denied)"
             if harvest._nghi_bi_chan(body) else f"thân chỉ {len(body)} byte, nghi trang lỗi"))
    return {"ten": ten, "url": url, "loai": loai, "dat": dat,
            "item": item, "byte": len(body), "ly_do": ly_do}


def chay(nguon, im_lang=False):
    kq = [do_mot(ten, url, loai) for ten, url, loai, _ in nguon]
    do_ = [k for k in kq if not k["dat"] and k["url"] not in CHI_CI_LAY_DUOC]
    vang = [k for k in kq if not k["dat"] and k["url"] in CHI_CI_LAY_DUOC]
    if not im_lang:
        print(f"=== ĐO {len(kq)} NGUỒN — {len(kq)-len(do_)-len(vang)} đạt · "
              f"{len(do_)} HỎNG · {len(vang)} chỉ-CI-lấy-được ===")
        for k in kq:
            if k["dat"]:
                dau, ghi = "✅", (f"{k['item']} item" if k["loai"] == "RSS" else f"{k['byte']} byte")
            elif k["url"] in CHI_CI_LAY_DUOC:
                dau, ghi = "🟡", f"{k['ly_do']} — đã biết, CI vẫn lấy được"
            else:
                dau, ghi = "⛔", k["ly_do"]
            print(f"  {dau} {k['ten'][:36]:<36} {ghi}")
        if harvest.VET_NGUON["cffi_va_duoc"]:
            print(f"\n🔓 {len(harvest.VET_NGUON['cffi_va_duoc'])} nguồn lấy được nhờ vân tay TLS Chrome "
                  f"(curl trần bị chặn)")
        if harvest.VET_NGUON["cffi_vang_mat"]:
            print(f"\n⚠️  Máy KHÔNG có `curl_cffi` — {len(harvest.VET_NGUON['cffi_vang_mat'])} nguồn "
                  f"bị chặn không thử lại được. Cài: python3 -m pip install --user curl_cffi")
    return kq, do_, vang


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tat-ca", action="store_true", help="đo mọi feed + trang HTML trong CLAUDE.md")
    ap.add_argument("--json", metavar="PATH", help="ghi kết quả ra JSON")
    ap.add_argument("--im-lang", action="store_true", help="chỉ trả mã thoát, không in bảng")
    args = ap.parse_args(argv)

    if args.tat_ca:
        nguon = [(n, u, "RSS", False) for n, u in harvest.feeds_from_claude_md()]
        nguon += [(n, u, "HTML", False) for n, u in harvest.html_pages_from_claude_md()]
    else:
        nguon = TRONG_YEU
    if not nguon:
        print("⛔ Không lấy được danh sách nguồn nào từ CLAUDE.md — không đo được.", file=sys.stderr)
        return 2

    kq, do_, _ = chay(nguon, im_lang=args.im_lang)
    if args.json:
        pathlib.Path(args.json).write_text(
            json.dumps(kq, ensure_ascii=False, indent=2), encoding="utf-8")
    return 1 if do_ else 0


if __name__ == "__main__":
    sys.exit(main())
