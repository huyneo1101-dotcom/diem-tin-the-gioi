#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dựng hồ sơ sở thích đọc tin của từng người nhắn bot, từ bảng `dt_bot_hoi`.

    python3 scripts/ho_so_doc_gia.py --so-lieu            # in thống kê thô (không cần AI)
    python3 scripts/ho_so_doc_gia.py --so-lieu --chat 6777454309
    python3 scripts/ho_so_doc_gia.py --luu ho-so.json     # lưu hồ sơ đã viết vào Supabase

CHIA VIỆC — phần đếm được thì đếm, phần cần đọc hiểu thì để người/AI làm:
  · `--so-lieu` chỉ **đếm**: bao nhiêu câu hỏi, chủ đề nào hay hỏi, tỉ lệ trong/ngoài phạm
    vi, giờ hay hỏi. Không suy diễn tính cách — đó là chỗ dễ bịa nhất.
  · Phần **nhận định** (người này quan tâm gì, hỏi theo lối nào) do phiên Claude Code đọc
    số liệu + câu hỏi thật rồi viết, xong lưu lại bằng `--luu`.

VÌ SAO KHÔNG CHẠY TRONG GITHUB ACTIONS: đọc `dt_bot_hoi` cần quyền cao hơn anon (RLS chỉ
mở INSERT cho anon). Nhét service key — thứ mở TOÀN BỘ database gồm cả ViNha, bi-a, Hương
Diện — vào secret của một repo public là cái giá quá đắt cho một việc chạy mỗi tuần một
lần. Phiên Claude Code local đã có sẵn quyền qua MCP Supabase, dùng luôn cho rẻ và an toàn.

VÌ SAO CÓ FILE NÀY thay vì để phiên tự truy vấn: cùng một cách đếm cho mọi lần chạy, và
số liệu không phụ thuộc việc phiên hôm đó nhớ đếm kiểu gì.
"""
import argparse
import collections
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = "https://ltmlueqkajqmduoqghdf.supabase.co"


def anon_key():
    k = os.environ.get("SUPABASE_ANON_KEY", "").strip()
    if k:
        return k
    import re
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    m = re.search(r"sb_publishable_[A-Za-z0-9_-]{10,}", html)
    return m.group(0) if m else ""


def so_lieu(rows, chat=None):
    if chat:
        rows = [r for r in rows if str(r.get("chat_id")) == str(chat)]
    if not rows:
        print("Không có dữ liệu.")
        return
    theo_chat = collections.defaultdict(list)
    for r in rows:
        theo_chat[r.get("chat_id")].append(r)

    for cid, rs in sorted(theo_chat.items(), key=lambda x: -len(x[1])):
        ten = next((r.get("ten") for r in rs if r.get("ten")), "") or "(không tên)"
        dem = collections.Counter()
        for r in rs:
            for c in (r.get("chu_de") or []):
                dem[c] += 1
        trong = sum(1 for r in rs if r.get("trong_pham_vi") is True)
        ngoai = sum(1 for r in rs if r.get("trong_pham_vi") is False)
        de_xuat = sum(len(r.get("tin_de_xuat") or []) for r in rs)
        gio = collections.Counter(str(r.get("created_at", ""))[11:13] for r in rs)

        print(f"\n=== {ten} (chat …{str(cid)[-4:]}) — {len(rs)} lượt hỏi ===")
        print(f"  Trong 5 chủ đề: {trong} · Ngoài phạm vi: {ngoai}")
        print(f"  Tin đã đề xuất từ các câu hỏi này: {de_xuat}")
        if dem:
            print("  Chủ đề hay hỏi: " + " · ".join(
                f"{k} ({v})" for k, v in dem.most_common(8)))
        if gio:
            print("  Giờ hay hỏi (UTC): " + " ".join(
                f"{h}h×{n}" for h, n in sorted(gio.items())))
        print("  Câu hỏi gần đây:")
        for r in rs[:8]:
            print(f"    · [{str(r.get('created_at', ''))[:10]}] {(r.get('cau_hoi') or '')[:110]}")


def luu(ho_so):
    """Lưu hồ sơ đã viết vào `dt_ho_so_doc_gia` (upsert theo chat_id)."""
    key = anon_key()
    if not key:
        print("Không tìm được key Supabase.", file=sys.stderr)
        return 1
    p = subprocess.run(
        ["curl", "-sS", "--max-time", "30", "-X", "POST",
         f"{URL}/rest/v1/dt_ho_so_doc_gia",
         "-H", f"apikey: {key}", "-H", f"Authorization: Bearer {key}",
         "-H", "Content-Type: application/json",
         "-H", "Prefer: resolution=merge-duplicates,return=minimal",
         "-w", "\n@@%{http_code}", "-d", json.dumps(ho_so, ensure_ascii=False)],
        capture_output=True, text=True)
    out = (p.stdout or "").strip()
    ma = out.rsplit("@@", 1)[-1] if "@@" in out else "?"
    if ma.startswith("2"):
        print(f"Đã lưu hồ sơ cho {ho_so.get('chat_id')}.")
        return 0
    print(f"Lưu hồ sơ HỎNG (HTTP {ma}): {out[:300]}", file=sys.stderr)
    return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--so-lieu", action="store_true", help="in thống kê thô")
    ap.add_argument("--chat", help="lọc theo một chat id")
    ap.add_argument("--tu-json", metavar="PATH",
                    help="đọc dữ liệu dt_bot_hoi từ file JSON (phiên Claude Code xuất ra "
                         "bằng MCP Supabase) thay vì tự gọi API")
    ap.add_argument("--luu", metavar="PATH", help="lưu hồ sơ (file JSON) vào Supabase")
    args = ap.parse_args()

    if args.luu:
        return luu(json.loads(pathlib.Path(args.luu).read_text(encoding="utf-8")))

    if args.so_lieu:
        if not args.tu_json:
            print("Cần --tu-json: anon key KHÔNG đọc được dt_bot_hoi (RLS chỉ mở INSERT).\n"
                  "Trong phiên Claude Code, dùng MCP Supabase chạy:\n"
                  "  select * from dt_bot_hoi order by created_at desc limit 500;\n"
                  "rồi ghi kết quả ra JSON và truyền vào --tu-json.", file=sys.stderr)
            return 1
        rows = json.loads(pathlib.Path(args.tu_json).read_text(encoding="utf-8"))
        so_lieu(rows, args.chat)
        return 0

    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
