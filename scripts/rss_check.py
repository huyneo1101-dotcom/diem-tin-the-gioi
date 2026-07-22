#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kiem tra suc khoe cac URL RSS ghi trong bang o CLAUDE.md.

Doc thang bang "URL RSS" trong CLAUDE.md (khong hardcode danh sach o day — de bang do
luon la nguon chan ly duy nhat), roi voi tung URL: fetch, parse XML, dem <item>, do bai
moi nhat cach bao lau. In ra bang ket qua + goi y cap nhat.

Dung: python3 scripts/rss_check.py [--timeout 25]

LUU Y: BAT BUOC giai nen gzip (curl --compressed). Lan verify dau 22/07/2026, UN News bi
cham nham la "hong" chi vi thieu buoc nay — server tra gzip, parse ra nhi phan.
"""
import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
)
ATOM = "{http://www.w3.org/2005/Atom}"
TMP = "/tmp/_rss_check.bin"


def urls_from_claude_md():
    """Lay (ten nguon, url) tu cac bang RSS trong CLAUDE.md.

    Bo qua URL nam trong backtick — do la URL CU da duoc danh dau SAI trong bang
    "DA SUA URL", khong phai URL dang dung.
    """
    text = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    try:
        block = text[text.index("## URL RSS") :]
        block = block[: block.index("\n## ", 1)]
    except ValueError:
        print("Khong tim thay muc '## URL RSS' trong CLAUDE.md", file=sys.stderr)
        return []
    out, seen = [], set()
    for line in block.split("\n"):
        if not line.startswith("|"):
            continue
        clean = re.sub(r"`[^`]*`", "", line)  # bo URL cu trong backtick
        m = re.search(r"https?://\S+", clean)
        if not m:
            continue
        url = m.group(0).rstrip("|").strip()
        name = line.split("|")[1].strip()
        if url in seen:
            continue
        seen.add(url)
        out.append((name, url))
    return out


def check(url, timeout):
    p = subprocess.run(
        ["curl", "-sL", "--compressed", "--max-time", str(timeout), "-A", UA,
         "-o", TMP, "-w", "%{http_code}", url],
        capture_output=True, text=True,
    )
    code = (p.stdout or "").strip() or "000"
    try:
        raw = Path(TMP).read_bytes().decode("utf-8", "replace")
    except FileNotFoundError:
        return code, 0, "khong tai duoc", ""
    try:
        root = ET.fromstring(raw.strip())
    except Exception:
        return code, 0, "KHONG PHAI XML", raw.strip()[:46].replace("\n", " ")

    items = (root.findall(".//item") or root.findall(f".//{ATOM}entry")
             or root.findall(".//{http://purl.org/rss/1.0/}item"))
    if not items:
        return code, 0, "XML nhung KHONG co item", ""

    dates = []
    for it in items:
        for tag in ("pubDate", "{http://purl.org/dc/elements/1.1/}date",
                    f"{ATOM}published", f"{ATOM}updated"):
            e = it.find(tag)
            if e is None or not e.text:
                continue
            try:
                d = (parsedate_to_datetime(e.text) if tag == "pubDate"
                     else datetime.fromisoformat(e.text.replace("Z", "+00:00")))
                dates.append(d if d.tzinfo else d.replace(tzinfo=timezone.utc))
            except Exception:
                pass
            break
    if not dates:
        return code, len(items), "OK", "feed khong ghi ngay"
    hours = (datetime.now(timezone.utc) - max(dates)).total_seconds() / 3600
    note = f"moi {hours:.0f}h truoc" + ("  <-- FEED GAN NHU DUNG" if hours > 72 else "")
    return code, len(items), "OK", note


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=int, default=25)
    args = ap.parse_args()

    feeds = urls_from_claude_md()
    if not feeds:
        return 1
    print(f"Kiem {len(feeds)} URL RSS lay tu bang trong CLAUDE.md\n")
    print(f"{'Nguon':<28}{'HTTP':<6}{'item':>5}  {'trang thai':<24}ghi chu")
    print("-" * 92)
    bad = []
    for name, url in feeds:
        code, n, st, extra = check(url, args.timeout)
        print(f"{name:<28}{code:<6}{n:>5}  {st:<24}{extra}")
        if st != "OK":
            bad.append((name, url, code, st))

    print()
    if bad:
        print(f"{len(bad)} nguon CO VAN DE — sua hoac chuyen sang WebSearch trong CLAUDE.md:")
        for name, url, code, st in bad:
            print(f"  - {name}: HTTP {code}, {st}\n      {url}")
        print("\nTruoc khi gach mot nguon: kiem lai xem co phai loi giai nen khong (da dung"
              "\n--compressed), va thu WebFetch — Cloudflare co the chan curl ma khong chan WebFetch"
              "\n(hoac nguoc lai). Chi bo khi CA HAI deu hong.")
    else:
        print("Tat ca URL trong bang deu chay tot.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
