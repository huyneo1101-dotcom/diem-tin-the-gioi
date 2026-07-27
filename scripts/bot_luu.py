#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lưu hội thoại bot + tin đề xuất vào Supabase (bảng `dt_bot_hoi`).

    python3 scripts/bot_luu.py --json /tmp/ban-ghi.json

File JSON là một object:
    {
      "chat_id": "6777454309",
      "ten": "Jay Lâm",
      "cau_hoi": "...",
      "tra_loi": "...",
      "chu_de": ["CNQS Mỹ", "Kinh tế Mỹ"],
      "trong_pham_vi": true,
      "tin_de_xuat": [{"title": "...", "url": "...", "source": "...",
                       "date": "2026-07-27", "ly_do": "..."}]
    }

VÌ SAO SUPABASE CHỨ KHÔNG PHẢI FILE TRONG REPO: repo `diem-tin-the-gioi` là PUBLIC —
lưu câu hỏi của người khác vào repo là công khai với cả internet.

VÌ SAO ANON KEY LÀ ĐỦ: RLS trên `dt_bot_hoi` chỉ mở INSERT cho anon, không mở SELECT.
Đã kiểm thật: chèn trả 201, đọc trả `[]` dù bảng có dữ liệu. Nên workflow ghi được mà
KHÔNG cần service key — tránh phải nhét một credential mở-toàn-database vào GitHub secret
của một repo public. Việc ĐỌC (tổng hợp hồ sơ) là đường riêng, có quyền riêng.

Key lấy theo thứ tự: biến môi trường `SUPABASE_ANON_KEY` → moi từ `index.html` (nó vốn
công khai trong đó, không phải bí mật).
"""
import argparse
import json
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = "https://ltmlueqkajqmduoqghdf.supabase.co"
BANG = "dt_bot_hoi"


def anon_key():
    k = os.environ.get("SUPABASE_ANON_KEY", "").strip()
    if k:
        return k
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    # Bắt CẢ HAI dạng: publishable key kiểu mới (`sb_publishable_…`, đang dùng) và JWT anon
    # kiểu cũ. Bản đầu chỉ bắt JWT nên không thấy key nào — web đã chuyển sang publishable.
    m = re.search(r"sb_publishable_[A-Za-z0-9_-]{10,}", html)
    if m:
        return m.group(0)
    m = re.search(r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{40,}\.[A-Za-z0-9_-]{20,}", html)
    return m.group(0) if m else ""


def ghi(ban_ghi):
    key = anon_key()
    if not key:
        print("Không tìm được anon key (env SUPABASE_ANON_KEY hoặc trong index.html).",
              file=sys.stderr)
        return 1
    # curl chứ không phải urllib: máy Huy có cert chèn giữa làm urllib trượt
    # CERTIFICATE_VERIFY_FAILED (xem scripts/tg_api.py). Đi cùng một đường cho nhất quán.
    p = subprocess.run(
        ["curl", "-sS", "--max-time", "30", "-X", "POST", f"{URL}/rest/v1/{BANG}",
         "-H", f"apikey: {key}", "-H", f"Authorization: Bearer {key}",
         "-H", "Content-Type: application/json",
         "-H", "Prefer: return=minimal",
         "-w", "\n@@%{http_code}",
         "-d", json.dumps(ban_ghi, ensure_ascii=False)],
        capture_output=True, text=True)
    out = (p.stdout or "").strip()
    ma = out.rsplit("@@", 1)[-1] if "@@" in out else "?"
    if ma.startswith("2"):
        print(f"Đã lưu vào Supabase ({BANG}).")
        return 0
    print(f"Lưu Supabase HỎNG (HTTP {ma}): {out[:300]} {p.stderr[:200]}", file=sys.stderr)
    return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", metavar="PATH", required=True,
                    help="file JSON chứa bản ghi cần lưu")
    args = ap.parse_args()
    try:
        bg = json.loads(pathlib.Path(args.json).read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Không đọc được {args.json}: {e}", file=sys.stderr)
        return 1
    if not bg.get("chat_id") or not bg.get("cau_hoi"):
        print("Thiếu chat_id hoặc cau_hoi.", file=sys.stderr)
        return 1
    # Chỉ giữ đúng các cột có thật — thừa khoá là Supabase trả 400 và mất cả bản ghi.
    cot = ("chat_id", "ten", "cau_hoi", "tra_loi", "chu_de", "trong_pham_vi", "tin_de_xuat")
    return ghi({k: bg[k] for k in cot if k in bg})


if __name__ == "__main__":
    sys.exit(main())
