#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DÒ ỨNG VIÊN cho bảng `THINKTANK_HTML` — đo THẬT trước khi khai, không khai rồi mới biết.

    python3 scripts/do_ung_vien_html.py                  # dò cả bảng ứng viên
    python3 scripts/do_ung_vien_html.py --chi brookings  # lọc theo tên/domain
    python3 scripts/do_ung_vien_html.py --json /tmp/x.json

VÌ SAO CÓ SCRIPT NÀY (15/08/2026). Bảng `WEBSEARCH_ONLY` trong `add_analyses.py` ghi 40 viện
"không có RSS", và phép đo 30/07/2026 cho thấy **29/40 vẫn trả 200 và đọc được HTML** — tức
phần lớn chỉ THIẾU FEED chứ không mất nguồn. Lớp `[HTML]` sinh ra để vá đúng chỗ đó, nhưng
tới nay mới khai 12 trang. Muốn khai thêm thì phải trả lời được ba câu cho từng ứng viên:

  1. trang danh sách có trả HTML thô không (hay JS-only / Cloudflare chặn)?
  2. link bài nằm ở đường dẫn hình dạng nào (để viết biểu thức path)?
  3. có bài nào rơi vào khung `MAX_AGE_DAYS` không (trang lưu trữ đời 2023 thì khai vô ích)?

⚠️ ĐO BẰNG CHÍNH MÃ SẢN XUẤT, KHÔNG CHÉP LẠI. Script này `import` thẳng `harvest_html_site`,
`html_article_links`, `curl` của `add_analyses.py`. Hai bộ luật song song thì chắc chắn lệch,
mà lệch âm thầm: dò bằng `requests` + BeautifulSoup sẽ báo "đọc được" cho trang mà `curl` trần
của sản xuất lấy về rỗng. Cái giá của bài học đó đã trả một lần ở `probe_sources.py` (xem khối
"VÁ 30/07/2026" trong file ấy) — đừng trả lần hai.

⚠️ PHẢI CHẠY Ở CI (`ubuntu-latest`), KHÔNG kết luận từ máy local. Luồng quét thật chạy trên
GitHub runner (`claude-web-scan.yml`), nên "đọc được" chỉ có nghĩa khi đo từ đó: máy Mac của
Huy hỏng DNS zone `.mil`, còn runner thì bị vài trang chặn IP datacenter. Đo nhầm chỗ là dựng
bảng nguồn sai cho cả hai nơi.

⚠️ `add_analyses.curl` là `curl` TRẦN (không curl_cffi) — cố ý giữ nguyên. Lớp `[HTML]` sản
xuất đi bằng đúng công cụ đó, nên nếu ở đây ta dò bằng vân tay TLS Chrome thì sẽ kết luận
"khai được" cho trang mà sản xuất lấy về trang challenge. Đo phải khổ đúng bằng lúc chạy thật.

CỘT `duong_dan_hay_gap` mới là thứ đáng đọc nhất khi một ứng viên ra 0 link: nó liệt kê hình
dạng đường dẫn CÓ THẬT trên trang, nhờ vậy sửa được biểu thức path ngay vòng sau thay vì đoán
mò thêm một lượt CI nữa (mỗi lượt ~3-5 phút).
"""
import argparse
import collections
import datetime
import html as html_mod
import importlib.util
import json
import pathlib
import re
import sys
import urllib.parse

sys.dont_write_bytecode = True

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "add_analyses.py"


def nap():
    spec = importlib.util.spec_from_file_location("aa_ung_vien", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── BẢNG ỨNG VIÊN ────────────────────────────────────────────────────────────────────────
# Mỗi mục: (tên, khu vực, [trang danh sách…], [biểu thức path thử…]).
# Khai NHIỀU trang và NHIỀU biểu thức cho mỗi viện là cố ý: một lượt CI mất vài phút, nên thà
# thử rộng một lượt còn hơn đúng-một-đoán rồi phải chạy lại. Trang nào ăn thì giữ, còn lại bỏ.
UNG_VIEN = [
    # ── ĐỐI CHỨNG — hai trang ĐÃ KHAI trong `THINKTANK_HTML` sau lượt đo 15/08/2026.
    # Để lại đây để lần dò sau còn so được: trang từng ăn mà nay ra 0 link nghĩa là viện đổi
    # giao diện, và biết ở đây thì rẻ hơn nhiều so với biết lúc `--candidates` lặng lẽ trả 0 bài.
    # (`--kiem-html` cũng canh việc này, nhưng nó chỉ soi bảng đã khai; chỗ này soi được cả
    # trang chưa khai, nên hai phép bổ cho nhau.)
    ("Brookings", "Mỹ · viện lớn · đối ngoại", [
        "https://www.brookings.edu/topic/international-affairs/",
    ], [r"^/articles/[^/]{15,}"]),
    ("Carnegie Endowment", "Mỹ · viện lớn · bình luận", [
        "https://carnegieendowment.org/emissary",
    ], [r"^/emissary/20\d\d/\d\d/[^/]{10,}"]),

    # ── CHỖ THÊM ỨNG VIÊN MỚI. Thêm vào đây rồi chạy trên CI, ĐỌC SỐ, mới khai vào
    # `add_analyses.py`. Đừng làm ngược lại.
    # ⛔ Đã đo 15/08 và BỎ, đừng dựng lại (lý do ghi ở khối "ĐÃ THỬ VÀ BỎ" trong add_analyses.py):
    #    iiss.org · orfonline.org/research · carnegie-mec.org · jiia.or.jp · africacenter.org ·
    #    issafrica.org · takshashila.org.in · swp-berlin.org · wola.org · ctc.westpoint.edu ·
    #    washingtoninstitute.org · stimson.org (trang HTML — nhưng FEED thì sống, đã khai).
]

# Feed RSS đáng thử cùng lượt: nếu một viện HÓA RA có feed sống thì khai feed LUÔN TỐT HƠN quét
# HTML (rẻ hơn, ngày chuẩn hơn, không vỡ khi viện đổi giao diện). Bảng `WEBSEARCH_ONLY` chép
# rằng chúng "không có RSS", nhưng chữ đó có từ 27/07 và đã sai ít nhất 3 lần từ đó (usip.org,
# cacianalyst.org, rusi.org đều lần lượt tìm ra feed thật). Nên đo lại, đừng tin bảng.
FEED_THU = [
    # ── ĐỐI CHỨNG — hai feed ĐÃ KHAI trong `THINKTANK_FEEDS` sau lượt đo 15/08/2026.
    # Cột `mới-nhất` mới là cột phải đọc: feed chết và feed sống đều trả 200 kèm đủ số item.
    ("Stimson", "https://www.stimson.org/feed/"),            # 15/08: 12 item · 7 trong khung
    ("Diálogo Américas", "https://dialogo-americas.com/feed/"),  # 15/08: 10 item · 10 trong khung
    # ⛔ `ifri.org` (`/en/rss.xml`) — 200 · 10 item · nhưng bài mới nhất 03/06/2022. Giữ trong
    # danh sách dò như một CA MẪU cho cái bẫy đó: nếu một ngày nó ra `mới-nhất` gần đây thì viện
    # đã hồi sinh feed và khai được; còn không thì mỗi lượt chạy nhắc lại rằng nó vẫn chết.
    ("IFRI (ca mẫu: feed 200 nhưng bỏ hoang)", "https://www.ifri.org/en/rss.xml"),
]


def duong_dan_hay_gap(mod, page_url: str, body: str, top: int = 18):
    """Hình dạng đường dẫn CÓ THẬT trên trang — đọc cái này để viết biểu thức path.

    Chỉ đếm link CÙNG HOST và có văn bản neo đủ dài (>=25 ký tự, đúng ngưỡng
    `html_article_links` dùng), vì link điều hướng ngắn không bao giờ là bài.
    """
    host = urllib.parse.urlparse(page_url).netloc.replace("www.", "")
    dem = collections.Counter()
    for a in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', body, re.S | re.I):
        title = html_mod.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", a.group(2)))).strip()
        if len(title) < 25:
            continue
        pr = urllib.parse.urlparse(urllib.parse.urljoin(page_url, a.group(1)))
        if pr.netloc.replace("www.", "") != host:
            continue
        seg = [s for s in pr.path.split("/") if s]
        if not seg:
            continue
        # Gộp theo 2 đoạn đầu, thay đoạn trông như slug/ngày bằng ký hiệu để hình dạng lộ ra.
        hd = []
        for s in seg[:2]:
            if re.fullmatch(r"20\d\d", s):
                hd.append("<năm>")
            elif re.fullmatch(r"\d{1,2}", s):
                hd.append("<số>")
            elif len(s) > 20:
                hd.append("<slug>")
            else:
                hd.append(s)
        dem["/" + "/".join(hd) + ("/…" if len(seg) > 2 else "")] += 1
    return dem.most_common(top)


def do_mot_trang(mod, ten, khu_vuc, page_url, path_res, today_vn):
    body = mod.curl(page_url).decode("utf-8", "replace")
    ra = {
        "ten": ten, "khu_vuc": khu_vuc, "trang": page_url,
        "byte": len(body), "bien_the": [],
    }
    # Cùng ngưỡng 2000 byte mà `harvest_html_site` dùng để chấm "trang bị chặn" — báo cùng một
    # con số thì đọc kết quả ở đây suy ra được hành vi lúc chạy thật, không phải quy đổi.
    if len(body) < 2000:
        ra["chan"] = True
        ra["duong_dan"] = []
        return ra
    ra["chan"] = False
    ra["duong_dan"] = duong_dan_hay_gap(mod, page_url, body)
    for path_re in path_res:
        # Gọi thẳng đường sản xuất: `harvest_html_site` bọc cả `html_article_links`, lọc
        # NOISE_PATHS, mở bài đọc meta ngày, và lọc khung ngày.
        rows, st = mod.harvest_html_site((ten, page_url, path_re, khu_vuc), set(), today_vn)
        ra["bien_the"].append({
            "path_re": path_re,
            "link": st["link"], "trong_khung": len(rows),
            "khong_ngay": st["khong_ngay"], "ngoai_khung": st["ngoai_khung"],
            "mau": [(d.isoformat(), t[:80], u) for d, t, u in rows[:3]],
        })
    return ra


def do_feed(mod, ten, url, today_vn):
    body = mod.curl(url)
    items = mod.feed_items(body)
    # ⚠️ `feed_items` TRẢ VỀ SẴN `date` ở cột 3 (nó gọi `parse_feed_date` bên trong, xem
    # `add_analyses.py`). Gọi `parse_feed_date` lần nữa lên chính cái `date` đó thì LUÔN ra
    # None — và hỏng theo kiểu câm hoàn hảo: mọi feed đều hiện "N item · 0 trong khung · không
    # đọc được ngày", tức feed SỐNG bị chấm y hệt feed CHẾT. Đã vấp thật ở vòng 2 (15/08/2026):
    # Stimson/IFRI/Diálogo bị báo là chết oan. Cột 3 dùng thẳng, đừng parse lại.
    trong = []
    for t, link, d in items:
        if d and (today_vn - d).days <= mod.MAX_AGE_DAYS and d <= today_vn:
            trong.append((d.isoformat(), (t or "")[:80], link))
    trong.sort(reverse=True)
    # NGÀY BÀI MỚI NHẤT — bắt buộc phải in ra, kể cả khi `trong_khung` = 0. Feed CHẾT và feed
    # SỐNG-nhưng-đăng-thưa đều hiện ra là "200 · N item · 0 trong khung", nhìn y hệt nhau; chỉ
    # `pubDate` mới nhất mới tách được. Đây đúng cái bẫy đã ghi cho CACI: feed trang chủ trả 200
    # với 10 item nhưng bài mới nhất từ 2012, khai vào là mỗi lượt quét kéo tin 2012 về.
    moi = [d for _t, _l, d in items if d]
    return {
        "ten": ten, "url": url, "byte": len(body), "item": len(items),
        "moi_nhat": max(moi).isoformat() if moi else None,
        "tuoi_ngay": (today_vn - max(moi)).days if moi else None,
        "trong_khung": len(trong), "mau": trong[:3],
        # Mục đầu đường dẫn của bài — dùng để biết feed này ra bài ở mảng nào, tức có trùng
        # với feed/trang đã khai cho cùng viện hay không (bài học `[NC]` 06/08).
        "muc": collections.Counter(
            "/" + urllib.parse.urlparse(l).path.strip("/").split("/")[0]
            for _t, l, _p in items if l).most_common(4),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chi", help="lọc theo tên viện hoặc domain (khớp chuỗi con, không phân biệt hoa thường)")
    ap.add_argument("--json", help="ghi kết quả thô ra file")
    ap.add_argument("--bo-feed", action="store_true", help="bỏ qua phần dò RSS")
    a = ap.parse_args()

    mod = nap()
    today_vn = datetime.datetime.now(mod.VN).date()
    loc = (a.chi or "").lower()

    print(f"=== DÒ ỨNG VIÊN [HTML] · {today_vn.isoformat()} (giờ VN) · "
          f"khung {mod.MAX_AGE_DAYS} ngày ===")
    print("Đọc cột `trong-khung`: >0 nghĩa là khai được NGAY. =0 mà `link`>0 nghĩa là biểu thức")
    print("path đúng nhưng trang không có bài mới — xem `ngoài-khung` trước khi kết luận.\n")

    kq_html = []
    for ten, khu_vuc, trangs, path_res in UNG_VIEN:
        if loc and loc not in ten.lower() and not any(loc in t.lower() for t in trangs):
            continue
        print(f"── {ten}  ({khu_vuc})")
        for page_url in trangs:
            r = do_mot_trang(mod, ten, khu_vuc, page_url, path_res, today_vn)
            kq_html.append(r)
            if r["chan"]:
                print(f"   ⛔ {page_url}\n      trang {r['byte']} byte (<2000) — bị chặn / rỗng")
                continue
            print(f"   • {page_url}  [{r['byte']//1024}KB]")
            for b in r["bien_the"]:
                dau = "✅" if b["trong_khung"] else ("◻️ " if b["link"] else "❌")
                print(f"      {dau} {b['path_re']}")
                print(f"         link={b['link']:3d} trong-khung={b['trong_khung']:2d} "
                      f"không-ngày={b['khong_ngay']:2d} ngoài-khung={b['ngoai_khung']:2d}")
                for d, t, u in b["mau"]:
                    print(f"           · {d}  {t}")
                    print(f"             {u}")
            if not any(b["link"] for b in r["bien_the"]):
                print("         ↳ đường dẫn CÓ THẬT trên trang (để sửa biểu thức path):")
                for hd, n in r["duong_dan"]:
                    print(f"             {n:3d}×  {hd}")
        print()

    kq_feed = []
    if not a.bo_feed:
        print("=== DÒ RSS (feed sống thì LUÔN hơn quét HTML) ===")
        for ten, url in FEED_THU:
            if loc and loc not in ten.lower() and loc not in url.lower():
                continue
            r = do_feed(mod, ten, url, today_vn)
            kq_feed.append(r)
            dau = "✅" if r["trong_khung"] else ("◻️ " if r["item"] else "❌")
            moi = (f"mới-nhất={r['moi_nhat']} ({r['tuoi_ngay']}n)" if r["moi_nhat"]
                   else "mới-nhất=KHÔNG ĐỌC ĐƯỢC NGÀY")
            print(f"{dau} {ten:24s} item={r['item']:3d} trong-khung={r['trong_khung']:2d} "
                  f"{moi:32s} [{r['byte']//1024}KB]  {url}")
            for d, t, u in r["mau"]:
                print(f"     · {d}  {t}")
            if r["item"] and r["muc"]:
                print(f"     mục: {', '.join(f'{m}×{n}' for m, n in r['muc'])}")

    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(
            {"ngay": today_vn.isoformat(), "html": kq_html, "feed": kq_feed},
            ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nĐã ghi {a.json}")

    an = [r for r in kq_html if any(b["trong_khung"] for b in r["bien_the"])]
    print(f"\n=== TÓM TẮT: {len(an)}/{len(kq_html)} trang ăn (có bài trong khung) · "
          f"{sum(1 for f in kq_feed if f['trong_khung'])}/{len(kq_feed)} feed sống ===")
    for r in an:
        b = max(r["bien_the"], key=lambda x: x["trong_khung"])
        print(f"  {r['ten']:22s} {b['trong_khung']:2d} bài  {r['trang']}  {b['path_re']}")


if __name__ == "__main__":
    main()
