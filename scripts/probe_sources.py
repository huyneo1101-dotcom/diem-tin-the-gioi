#!/usr/bin/env python3
"""Dò TOÀN BỘ nguồn: cái nào đọc được bằng RSS, cái nào bằng HTML, cái nào chịu.

Dùng:  python3 scripts/probe_sources.py --json /tmp/probe-local.json
       python3 scripts/probe_sources.py --json docs/probe-ci.json     (chạy trong CI)

VÌ SAO CÓ SCRIPT NÀY (chỉ thị Huy 27/07/2026: "kiểm tra lại toàn bộ các danh sách nguồn xem
cái nào mở được bằng html và cái nào xem được bằng CI chạy ở Mỹ"): môi trường quyết định
nguồn nào sống. Đo thật hôm 27/07:
  - Máy Mac KHÔNG phân giải nổi DNS zone `.mil` (DNSSEC lỗi: EDE(9)/EDE(22)) -> mọi trang
    quân chủng trả `000`, trong khi GitHub runner ở Mỹ phân giải được hết.
  - Ngược lại, một số trang chặn IP datacenter GitHub (403) nhưng mở bình thường từ máy Huy
    (war.gov, spaceforce.mil).
Nghĩa là KHÔNG có một danh sách nguồn đúng cho cả hai nơi. Phải đo ở CẢ HAI rồi hợp nhất.

Phân loại mỗi URL:
  RSS   — tải được và parse ra >=1 <item>/<entry>  -> harvest lớp [RSS] dùng luôn
  HTML  — 200 và body đủ lớn nhưng không phải feed -> harvest lớp [HTML] scrape được
  403   — máy chủ từ chối (WAF/chặn bot)           -> phải qua WebSearch/GNews
  DNS   — không phân giải được tên miền            -> chỉ môi trường khác mới đọc nổi
  LỖI   — timeout / lỗi mạng khác
"""
import argparse
import concurrent.futures
import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.parse
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"


def urls_from(text):
    out = []
    for m in re.finditer(r"https?://[^\s\"'<>)\]|]+", text):
        u = m.group(0).rstrip(".,;").split("?utm_source")[0]
        out.append(u)
    return out


def collect_targets():
    """Gom mọi URL cần dò: bảng RSS + bảng HTML trong CLAUDE.md, và danh sách nguồn chính thức Mỹ."""
    targets = {}

    cm = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    try:
        block = cm[cm.index("## URL RSS"):]
        block = block[: block.index("\n## ", 1)]
    except ValueError:
        block = ""
    for line in block.split("\n"):
        if not line.startswith("|"):
            continue
        clean = re.sub(r"`[^`]*`", "", line)
        m = re.search(r"https?://\S+", clean)
        if not m:
            continue
        url = m.group(0).rstrip("|").strip()
        name = line.split("|")[1].strip()
        targets.setdefault(url, name or url)

    p = ROOT / "docs" / "nguon-chinh-thuc-my.md"
    if p.exists():
        for u in urls_from(p.read_text(encoding="utf-8", errors="replace")):
            targets.setdefault(u, "nguon-chinh-thuc-my")
    return sorted(targets.items())


def probe(item):
    url, name = item
    # KHÔNG dùng -A: một số trang .mil trả 200 với curl mặc định nhưng 403 khi giả trình duyệt
    # (thực tế army.mil). Thử lần 2 kèm UA nếu lần 1 hỏng.
    for flags in ([], ["-A", UA]):
        p = subprocess.run(
            ["curl", "-sL", "--compressed", "--max-time", "15"] + flags +
            ["-w", "\n__CODE__%{http_code}", url],
            capture_output=True)
        raw = p.stdout.decode("utf-8", "replace")
        err = p.stderr.decode("utf-8", "replace")
        code = "000"
        body = raw
        if "__CODE__" in raw:
            body, _, code = raw.rpartition("\n__CODE__")
        code = code.strip() or "000"
        if code == "000":
            if "Could not resolve host" in err or "Could not resolve host" in raw:
                if flags:
                    return dict(url=url, name=name, kind="DNS", code="000", size=0)
                continue
            if flags:
                return dict(url=url, name=name, kind="LỖI", code="000", size=0)
            continue
        size = len(body)
        if code == "200":
            n = 0
            try:
                root = ET.fromstring(body.strip())
                n = sum(1 for e in root.iter() if e.tag.split("}")[-1] in ("item", "entry"))
            except Exception:
                n = 0
            if n:
                return dict(url=url, name=name, kind="RSS", code=code, size=size, items=n)
            if size > 3000:
                return dict(url=url, name=name, kind="HTML", code=code, size=size)
            return dict(url=url, name=name, kind="LỖI", code="200-rỗng", size=size)
        if code in ("401", "403"):
            if flags:
                return dict(url=url, name=name, kind="403", code=code, size=size)
            continue
        return dict(url=url, name=name, kind="LỖI", code=code, size=size)
    return dict(url=url, name=name, kind="LỖI", code="000", size=0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", metavar="PATH", help="ghi kết quả ra JSON")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    targets = collect_targets()
    moi_truong = "CI" if os.environ.get("GITHUB_ACTIONS") else "local"
    print(f"Dò {len(targets)} URL — môi trường: {moi_truong}", file=sys.stderr)

    res = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        for i, r in enumerate(ex.map(probe, targets), 1):
            res.append(r)
            if i % 25 == 0:
                print(f"  ... {i}/{len(targets)}", file=sys.stderr)

    by = {}
    for r in res:
        by.setdefault(r["kind"], []).append(r)

    print(f"\n=== KẾT QUẢ ({moi_truong}) ===")
    for k in ("RSS", "HTML", "403", "DNS", "LỖI"):
        lst = by.get(k, [])
        print(f"  {k:5s}: {len(lst)}")
    for k in ("RSS", "HTML"):
        print(f"\n-- {k} ({len(by.get(k, []))}) --")
        for r in sorted(by.get(k, []), key=lambda x: x["url"]):
            extra = f" [{r.get('items')} item]" if r.get("items") else ""
            print(f"   {urllib.parse.urlparse(r['url']).netloc:32s}{extra} {r['url'][:88]}")
    for k in ("403", "DNS", "LỖI"):
        doms = sorted(set(urllib.parse.urlparse(r["url"]).netloc for r in by.get(k, [])))
        print(f"\n-- {k}: {len(doms)} domain --")
        for i in range(0, len(doms), 4):
            print("   " + ", ".join(doms[i:i + 4]))

    if args.json:
        pathlib.Path(args.json).write_text(
            json.dumps({"moi_truong": moi_truong, "ket_qua": res}, ensure_ascii=False, indent=2),
            encoding="utf-8")
        print(f"\nĐã ghi {len(res)} kết quả ra {args.json}", file=sys.stderr)


if __name__ == "__main__":
    main()
