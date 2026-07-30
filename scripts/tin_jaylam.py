#!/usr/bin/env python3
"""Xử lý tin Jay Lâm gửi qua bot thành TIN CHUẨN (tiêu đề · tóm tắt · nguồn + URL).

Chỉ thị Huy 30/07/2026: *"tin Jay Lâm gửi cũng là tin kèm url và tóm tắt gần giống định
dạng mẫu"*. Trước đó mục 5 của file .docx dán NGUYÊN VĂN tới 20.000 ký tự trong khi 4 mục
quét thường chỉ 1-2 câu — bản tin mất cân đối, và người đọc phải tự đọc cả bài để biết tin
gì. Việc truy URL gốc + viết tóm tắt cần suy nghĩ nên KHÔNG làm được trong `make_docx.py`
(chạy trong workflow, không có agent); nó thuộc về PHIÊN QUÉT TỐI — nơi đã có sẵn agent và
đã quen luật truy ngược bài gốc (xem mục "TRUY NGƯỢC VỀ NGUỒN GỐC" của Báo Mới trong
CLAUDE.md, cùng nguyên tắc).

Dùng:
  python3 scripts/tin_jaylam.py --liet-ke          # in hàng chờ cho agent đọc (mã 10 = rỗng)
  python3 scripts/tin_jaylam.py --ghi /tmp/x.json  # ghi tiêu đề/tóm tắt/nguồn lên Supabase

/tmp/x.json:  [{"id": 12, "tieu_de": "...", "tom_tat": "...",
                "nguon_ten": "Reuters", "nguon_url": "https://...",
                "la_cnqs": false}]

`la_cnqs: true` cho tin thuộc CNQS Mỹ (khí tài · hệ thống · hợp đồng quốc phòng) — nhóm DUY
NHẤT được nới khung ngày tới 3 ngày lùi, y như tin quét thường. Huy nêu 30/07/2026: *"tao cần
tin cnqs Mỹ thì tin cũ 3 ngày vẫn để lại"*. Khai sai cờ này là loại oan tin Jay Lâm gửi.

`nguon_url` được phép RỖNG — Jay Lâm tự gửi bài, không truy được nguồn gốc thì vẫn GIỮ tin
(cùng luật Agent 7 của Báo Mới: bài người dùng tự đưa thì không được bỏ), chỉ là mục 5 in
"(không truy được nguồn gốc)". Nhưng có `nguon_url` thì nó phải là BÀI CỤ THỂ — dùng chung
`add_news.check_url_quality`, không viết lại luật.
"""
import datetime
import json
import os
import pathlib
import re
import subprocess
import sys
import zoneinfo

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from add_news import check_url_quality  # noqa: E402  (luật URL: một nơi định nghĩa)

VN = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")
SUPABASE_URL = "https://ltmlueqkajqmduoqghdf.supabase.co"
BANG = "dt_jaylam_inbox"

# Khung ngày — Huy chốt 30/07/2026: áp ĐÚNG khung tin quét thường, tức KHÔNG phải một con số
# duy nhất. Mặc định hôm nay + hôm qua; riêng CNQS Mỹ nới tới 3 ngày lùi, đúng như
# `add_news.py::MAX_AGE_DAYS_CNQS` và `harvest.py::CNQS_LOOKBACK_DAYS` (tin khí tài/hợp đồng
# đăng thưa, cuối tuần Mỹ gần như trắng). Huy nêu thẳng: *"tao cần tin cnqs Mỹ thì tin cũ 3
# ngày vẫn để lại (ví dụ hôm nay 27 thì có thể giữ lại tin tận ngày 24)"*.
#
# `--liet-ke` lọc theo khung RỘNG NHẤT (3 ngày) — lúc đó chưa ai biết tin thuộc chủ đề gì, cắt
# theo khung hẹp là bỏ mất ứng viên CNQS trước khi agent kịp đọc. Việc áp khung ĐÚNG theo chủ
# đề là của `make_docx.py`, sau khi agent đã khai cờ `la_cnqs`.
# ⚠️ Hai con số này còn được nhắc ở `.github/scripts/make_docx.py` (nơi thật sự BỎ tin quá hạn)
# và ở add_news.py/harvest.py. Đã đăng ký `HeThong/dong-bo-luat.py` để lệch nhau là báo không đạt.
MAX_AGE_DAYS = 1
MAX_AGE_DAYS_CNQS = 3

TIEU_DE_MIN, TIEU_DE_MAX = 10, 200
TOM_TAT_MIN = 40


ROOT = pathlib.Path(__file__).resolve().parent.parent
DT_KEY_FILE = pathlib.Path("/Users/Huy/Claude/.dt-bot-key")


def _anon_key():
    """Env trước, lùi về khoá publishable nhúng sẵn trong `index.html` — CÙNG quy ước
    `telegram_bot.py::_anon_key()` và `make_docx.py::_jaylam_anon_key()`."""
    k = (os.environ.get("SUPABASE_ANON_KEY") or "").strip()
    if k:
        return k
    try:
        html_txt = (ROOT / "index.html").read_text(encoding="utf-8")
    except OSError:
        return ""
    m = re.search(r"sb_publishable_[A-Za-z0-9_-]{10,}", html_txt)
    return m.group(0) if m else ""


def _dt_key():
    """Mã `x-dt-key` — env trước, lùi về file ngoài repo (chỉ có trên máy Huy)."""
    k = (os.environ.get("DT_BOT_KEY") or "").strip()
    if k:
        return k
    try:
        return DT_KEY_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _curl(args, ctx):
    """Trả (ok, stdout). Lỗi mạng/parse KHÔNG được nuốt — in ra rồi trả về phía KÊU."""
    try:
        p = subprocess.run(["curl", "-sS", "--max-time", "30"] + args,
                           capture_output=True, text=True, timeout=35)
    except Exception as e:                                   # noqa: BLE001
        print(f"{ctx}: gọi curl hỏng ({e}).", file=sys.stderr)
        return False, ""
    if p.returncode != 0:
        print(f"{ctx}: curl mã {p.returncode} — {(p.stderr or '').strip()[:200]}",
              file=sys.stderr)
        return False, p.stdout or ""
    return True, p.stdout or ""


def _headers():
    key, dt_key = _anon_key(), _dt_key()
    if not key or not dt_key:
        return None
    return ["-H", f"apikey: {key}", "-H", f"Authorization: Bearer {key}",
            "-H", f"x-dt-key: {dt_key}"]


def qua_han(row, now=None, gioi_han=None):
    """True nếu tin gửi cũ hơn `gioi_han` ngày so với hôm nay (giờ VN).

    `gioi_han` mặc định là khung RỘNG NHẤT (`MAX_AGE_DAYS_CNQS`) vì hàm này chạy ở bước liệt
    kê hàng chờ — lúc đó chưa biết tin thuộc chủ đề gì, cắt hẹp là bỏ mất ứng viên CNQS.

    Đọc `created_at` hỏng -> trả True (phía KÊU): một dòng không đo được tuổi thì đừng lặng
    lẽ cho vào bản tin như tin mới — nó sẽ được in ra trong danh sách quá hạn để người xem.
    """
    now = now or datetime.datetime.now(VN)
    gioi_han = MAX_AGE_DAYS_CNQS if gioi_han is None else gioi_han
    try:
        t = datetime.datetime.fromisoformat(
            (row.get("created_at") or "").replace("Z", "+00:00")).astimezone(VN)
    except (ValueError, AttributeError, TypeError):
        return True
    return (now.date() - t.date()).days > gioi_han


def doc_hang_cho(now=None):
    """(trong_khung, qua_han_list) — các dòng chưa gộp & chưa xử lý.

    Thiếu mã / đọc hỏng -> ([], []) kèm cảnh báo: đây là phần LÀM GIÀU bản tin, hỏng ở đây
    không được làm chết cả phiên quét.
    """
    h = _headers()
    if not h:
        print("Thiếu SUPABASE_ANON_KEY/DT_BOT_KEY — không đọc được tin Jay Lâm gửi.",
              file=sys.stderr)
        return [], []
    ok, out = _curl(
        [f"{SUPABASE_URL}/rest/v1/{BANG}"
         "?select=id,ten,ten_file,noi_dung,created_at"
         "&da_gop=eq.false&da_xu_ly=eq.false&order=created_at.asc"] + h,
        "Đọc hàng chờ tin Jay Lâm")
    if not ok:
        return [], []
    try:
        rows = json.loads(out)
    except json.JSONDecodeError:
        print(f"Đọc hàng chờ trả về dạng lạ: {out[:200]}", file=sys.stderr)
        return [], []
    if not isinstance(rows, list):
        print(f"Đọc hàng chờ trả về dạng lạ: {str(rows)[:200]}", file=sys.stderr)
        return [], []
    trong, ngoai = [], []
    for r in rows:
        (ngoai if qua_han(r, now) else trong).append(r)
    return trong, ngoai


def in_hang_cho(now=None):
    trong, ngoai = doc_hang_cho(now)
    if ngoai:
        print(f"⚠️ {len(ngoai)} tin Jay Lâm gửi đã QUÁ KHUNG {MAX_AGE_DAYS_CNQS + 1} ngày "
              "(rộng nhất, kể cả khung nới của CNQS Mỹ) — bỏ qua, không cần tóm tắt "
              "(make_docx sẽ đánh dấu đã gộp):")
        for r in ngoai:
            print(f"   - id={r.get('id')} {r.get('created_at')} {r.get('ten_file')}")
    if not trong:
        print("Không có tin Jay Lâm nào chờ xử lý.")
        return 10
    print(f"=== {len(trong)} TIN JAY LÂM GỬI CHỜ XỬ LÝ ===")
    print(f"Khung ngày: mặc định {MAX_AGE_DAYS + 1} ngày (hôm nay + hôm qua); tin thuộc "
          f"CNQS Mỹ (khí tài · hệ thống · hợp đồng quốc phòng) khai `la_cnqs: true` để được "
          f"nới tới {MAX_AGE_DAYS_CNQS} ngày lùi.")
    for r in trong:
        print(f"\n--- id={r.get('id')} | gửi {r.get('created_at')} | "
              f"file: {r.get('ten_file')} | người gửi: {r.get('ten') or 'Jay Lâm'} ---")
        print((r.get("noi_dung") or "").strip())
    return 0


def kiem_mot(m, cho_phep_ids, da_thay):
    """Guardrail cho một mục trong file --ghi. Raise ValueError khi không đạt."""
    if not isinstance(m, dict):
        raise ValueError(f"mục không phải object: {str(m)[:80]}")
    try:
        mid = int(m.get("id"))
    except (TypeError, ValueError):
        raise ValueError(f"thiếu/sai `id`: {m.get('id')!r}")
    ctx = f"id={mid}"
    if mid not in cho_phep_ids:
        raise ValueError(f"{ctx}: không nằm trong hàng chờ (đã xử lý, đã gộp, hoặc id bịa)")
    if mid in da_thay:
        raise ValueError(f"{ctx}: xuất hiện hai lần trong file")
    tieu_de = (m.get("tieu_de") or "").strip()
    if not TIEU_DE_MIN <= len(tieu_de) <= TIEU_DE_MAX:
        raise ValueError(f"{ctx}: `tieu_de` phải dài {TIEU_DE_MIN}-{TIEU_DE_MAX} ký tự "
                         f"(đang {len(tieu_de)})")
    tom_tat = (m.get("tom_tat") or "").strip()
    if len(tom_tat) < TOM_TAT_MIN:
        raise ValueError(f"{ctx}: `tom_tat` phải từ {TOM_TAT_MIN} ký tự trở lên "
                         f"(đang {len(tom_tat)}) — tóm tắt cụt thì thà không có")
    nguon_ten = (m.get("nguon_ten") or "").strip()
    if not nguon_ten:
        raise ValueError(f"{ctx}: thiếu `nguon_ten` (không truy được bài gốc thì ghi "
                         '"Jay Lâm gửi")')
    nguon_url = (m.get("nguon_url") or "").strip()
    if nguon_url:
        check_url_quality(nguon_url, ctx)
    la_cnqs = m.get("la_cnqs", False)
    if not isinstance(la_cnqs, bool):
        raise ValueError(f"{ctx}: `la_cnqs` phải là true/false, đang {la_cnqs!r}")
    return {"id": mid, "tieu_de": tieu_de, "tom_tat": tom_tat,
            "nguon_ten": nguon_ten, "nguon_url": nguon_url or None,
            "la_cnqs": la_cnqs}


def ghi(duong_dan, now=None):
    try:
        data = json.loads(pathlib.Path(duong_dan).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"Không đọc được {duong_dan}: {e}", file=sys.stderr)
        return 1
    if not isinstance(data, list):
        print("File phải là MỘT MẢNG [{id, tieu_de, tom_tat, nguon_ten, nguon_url}].",
              file=sys.stderr)
        return 1
    if not data:
        print("Mảng rỗng — không có gì để ghi.")
        return 0

    trong, _ = doc_hang_cho(now)
    cho_phep = {r.get("id") for r in trong}
    if not cho_phep:
        print("Hàng chờ rỗng (hoặc không đọc được) — không ghi gì.", file=sys.stderr)
        return 1

    sach, da_thay = [], set()
    for m in data:
        try:
            ok = kiem_mot(m, cho_phep, da_thay)
        except ValueError as e:
            print(f"CHẶN: {e}", file=sys.stderr)
            return 1
        da_thay.add(ok["id"])
        sach.append(ok)

    h = _headers()
    if not h:
        print("Thiếu SUPABASE_ANON_KEY/DT_BOT_KEY — không ghi được.", file=sys.stderr)
        return 1
    hong = []
    for m in sach:
        than = {k: v for k, v in m.items() if k != "id"}
        than["da_xu_ly"] = True
        ok, _ = _curl(
            ["-X", "PATCH", f"{SUPABASE_URL}/rest/v1/{BANG}?id=eq.{m['id']}"] + h +
            ["-H", "Content-Type: application/json", "-H", "Prefer: return=minimal",
             "-d", json.dumps(than, ensure_ascii=False)],
            f"Ghi tin Jay Lâm id={m['id']}")
        if not ok:
            hong.append(m["id"])
    if hong:
        print(f"CHẶN: ghi hỏng {len(hong)}/{len(sach)} dòng (id: {hong}).", file=sys.stderr)
        return 1
    print(f"✅ Đã xử lý {len(sach)} tin Jay Lâm gửi -> sẽ vào mục riêng của bản tin TỐI.")
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--liet-ke" in argv:
        return in_hang_cho()
    if "--ghi" in argv:
        i = argv.index("--ghi")
        if i + 1 >= len(argv):
            print("Thiếu đường dẫn file sau --ghi.", file=sys.stderr)
            return 1
        return ghi(argv[i + 1])
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
