#!/usr/bin/env python3
"""File Jay Lâm gửi qua bot = **BỘ LỌC**, không phải nguồn tin (Huy đảo nguyên tắc 01/08/2026).

> Nguyên văn: *"thay đổi hoàn toàn nguyên tắc. file của Jay Lâm gửi chỉ là để so sánh xem có
> tin nào mày quét được mà bị trùng với tin trong file đó không thôi"* · *"nếu có tin bị trùng
> với file Jay Lâm thì tự xoá khỏi tổng hợp tin đã quét đi và gửi file word (trong đó không có
> tin nào từ Jay Lâm)"*.

Trước 01/08 file Jay Lâm là NGUỒN: nội dung được tóm tắt lại rồi in thành mục 5 của bản tin.
Nay đảo hẳn — file đó không đóng góp một dòng nào vào bản tin, nó chỉ dùng để **bớt tin của
chính mình**: tin nào mình quét được mà Jay đã có thì bỏ đi, vì anh ta đọc rồi.

Ba lệnh, đi theo đúng thứ tự này trong phiên quét:

  python3 scripts/tin_jaylam.py --liet-ke            # (1) đọc file Jay để đối chiếu
  python3 scripts/tin_jaylam.py --ghi /tmp/bang.json # (2) lưu bảng đối chiếu đã trích
  python3 scripts/tin_jaylam.py --ghi-loai /tmp/loai.json  # (3) khai tin CỦA MÌNH bị loại

Lệnh thứ tư, cho file .docx Huy nhận rồi quăng thẳng vào khung chat (không đi qua bot):

  python3 scripts/tin_jaylam.py --nap-file ~/Downloads/ĐTN_M_01.9.2026.docx [--nhan <id>] [--thu]

Nó bóc link + chữ từ file, ghi bảng đối chiếu vào `logs/bang-doi-chieu-coquan.json`, rồi tự
loại khỏi bản tin những tin của mình trùng ĐÚNG ĐƯỜNG DẪN. Phần trùng SỰ KIỆN mà khác link
vẫn thuộc về agent: bảng nạp vào được in ra trong `--liet-ke` để đối chiếu bằng đọc hiểu.

(2) `/tmp/bang.json` — danh sách tin trích RA TỪ file Jay, để phiên sau khỏi đọc lại toàn văn:
    [{"id": 12, "tin": [{"tieu_de": "...", "url": "https://..."}, ...]}]

(3) `/tmp/loai.json` — tin của MÌNH trùng sự kiện với file Jay, ghi vào sổ `logs/trung-jaylam.json`:
    [{"url": "<sourceUrl tin của mình>", "tieu_de": "<tiêu đề tin của mình>",
      "id_jay": 12, "trung_voi": "<tiêu đề mảnh tương ứng bên file Jay>"}]

⚠️ **SO LINK THUẦN LÀ VÔ DỤNG — đã đo, đừng dựng lại đường đó.** Đối chiếu 12 tin quét tối
01/08 với 37 URL trong file Jay: **0 tin trùng URL**, trong khi đọc hiểu ra **03 tin trùng sự
kiện** (Mahan Air · tuần tra Scarborough · NITE-STAR 981 triệu USD). Jay viết lại bằng tiếng
Việt từ nguồn khác hẳn nguồn mình lấy. Link chỉ là chốt CHẮC khi tình cờ trùng — phép lọc
chính là AGENT ĐỌC HIỂU THEO SỰ KIỆN. Vì thế bước (3) không thể tự động hoá bằng script, và
cũng vì thế script này chỉ giữ vai bốc dữ liệu + guardrail, không tự phán trùng.

⚠️ **Đối chiếu phải so với FILE GỐC hoặc bảng trích ĐẦY ĐỦ, KHÔNG so với danh sách tin đã
viết lại của mình.** Vấp thật 01/08: danh sách 29 tin viết lại của phiên trước đã qua lọc
trùng rồi, nên đúng những tin trùng lại vắng mặt trong đó — dùng nó làm bảng đối chiếu thì
kết luận "không có tin nào trùng".

⚠️ **Khung ngày dùng khung RỘNG NHẤT (`MAX_AGE_DAYS_CNQS` = 3), không phải khung mặc định.**
Tin CNQS Mỹ của mình được nới tới 3 ngày lùi (`add_news.py::MAX_AGE_DAYS_CNQS`), nên một file
Jay gửi hôm nay còn phải làm bộ lọc cho tới bản tin của 3 ngày sau — cắt ở 2 ngày là để lọt
đúng nhóm tin đăng thưa nhất. Đây là chỗ Huy chốt *"mọi bản tin còn trong khung ngày (2-3
ngày), không phải chỉ bản kế tiếp"*.
"""
import datetime
import html
import json
import os
import pathlib
import re
import subprocess
import sys
import unicodedata
import urllib.parse
import zipfile
import zoneinfo

VN = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")
SUPABASE_URL = "https://ltmlueqkajqmduoqghdf.supabase.co"
BANG = "dt_jaylam_inbox"

# Khung ngày của tin quét thường — giữ NGUYÊN tên hai hằng số này dù chỉ `MAX_AGE_DAYS_CNQS`
# được dùng để cắt hàng chờ: chúng phải luôn bằng `add_news.py` / `harvest.py`, và
# `HeThong/dong-bo-luat.py` canh đúng theo tên. Lệch nhau là bộ lọc sống ngắn hơn tuổi tin mà
# nó phải lọc — hỏng câm, vì file .docx vẫn ra đời đủ mục.
MAX_AGE_DAYS = 1
MAX_AGE_DAYS_CNQS = 3

TIEU_DE_MIN, TIEU_DE_MAX = 10, 200
# Tiêu đề tin CỦA MÌNH nới rộng hơn: tiêu đề tự viết dài hơn tiêu đề trích từ file Jay.
TIEU_DE_MINH_MAX = 300
TRUNG_VOI_MIN = 10

# Sổ loại giữ 7 ngày. Dài hơn khung lọc (3 ngày) có chủ đích: giữ dư vài ngày chỉ khiến một
# URL đã rời bản tin nằm lại trong sổ — vô hại; cắt sớm thì mất bằng chứng để soi ngược khi
# Huy hỏi "sao tin này biến mất".
GIU_NGAY = 7

ROOT = pathlib.Path(__file__).resolve().parent.parent
SO_LOAI = ROOT / "logs" / "trung-jaylam.json"
DT_KEY_FILE = pathlib.Path("/Users/Huy/Claude/.dt-bot-key")
SO_COQUAN = ROOT / "logs" / "bang-doi-chieu-coquan.json"
INDEX = ROOT / "index.html"

# Nhãn của một file nạp cục bộ — nó đóng vai `id_jay` trong sổ loại, nên phải soi ngược được
# về đúng file cơ quan đã gửi. Quá ngắn thì vô nghĩa, quá dài thì tràn dòng log.
NHAN_MIN, NHAN_MAX = 3, 60
# Tham số theo dõi bỏ khi CHUẨN HOÁ url để so khớp. Cố ý là danh sách HẸP: `?s=`, `?id=`,
# `?select=` mang nghĩa ở nhiều trang, bỏ bừa là gộp nhầm hai bài khác nhau thành một.
THAM_SO_BO = ("utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
              "utm_id", "fbclid", "gclid", "mc_cid", "mc_eid")


def _anon_key():
    """Env trước, lùi về khoá publishable nhúng sẵn trong `index.html` — CÙNG quy ước
    `telegram_bot.py::_anon_key()`."""
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


def han_giu_so(now):
    """Mốc ngày cũ nhất còn được giữ trong sổ — MỘT bản gốc cho cả ba sổ.

    Trước 01/09/2026 phép này được viết lại ở từng chỗ ghi sổ; khi nhánh `--nap-file` thêm
    hai chỗ nữa thì bản hỏng "cắt sổ theo hạn 0 ngày" của `test-tin-jaylam-xu-ly.py` không
    còn neo được vào đúng một dòng, tức lớp vá đó mất phép canh mà không ai thấy.
    """
    return (now.date() - datetime.timedelta(days=GIU_NGAY)).isoformat()


def qua_han(row, now=None, gioi_han=None):
    """True nếu file gửi cũ hơn `gioi_han` ngày so với hôm nay (giờ VN).

    Mặc định là khung RỘNG NHẤT (`MAX_AGE_DAYS_CNQS`) — xem docstring đầu file.

    Đọc `created_at` hỏng -> True (phía KÊU): một dòng không đo được tuổi thì đừng để nó làm
    bộ lọc vô thời hạn; nó được in ra trong danh sách quá hạn để người xem.
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
    """(trong_khung, qua_han_list) — mọi dòng chưa đóng sổ (`da_gop=false`).

    ⚠️ KHÔNG lọc `da_xu_ly` như bản cũ. Dòng đã trích bảng đối chiếu vẫn phải hiện ra: nó còn
    làm bộ lọc cho các bản tin kế tiếp trong khung 3 ngày (Huy chốt điểm 3). Bản cũ lọc
    `da_xu_ly=eq.false` vì lúc đó mỗi dòng chỉ dùng ĐÚNG MỘT LẦN để in vào mục 5.

    Thiếu mã / đọc hỏng -> ([], []) kèm cảnh báo: đây là phần LÀM SẠCH bản tin, hỏng ở đây
    không được làm chết cả phiên quét.
    """
    h = _headers()
    if not h:
        print("Thiếu SUPABASE_ANON_KEY/DT_BOT_KEY — không đọc được file Jay Lâm gửi.",
              file=sys.stderr)
        return [], []
    ok, out = _curl(
        [f"{SUPABASE_URL}/rest/v1/{BANG}"
         "?select=id,ten,ten_file,noi_dung,created_at,da_xu_ly,tom_tat"
         "&da_gop=eq.false&order=created_at.asc"] + h,
        "Đọc hàng chờ file Jay Lâm")
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


def doc_bang_doi_chieu(row):
    """Bảng đối chiếu đã trích của một dòng, hoặc [] nếu chưa trích / lưu hỏng.

    Lưu trong cột `tom_tat` dưới dạng JSON — cột đó vốn giữ tóm tắt-để-đăng của thiết kế cũ,
    nay tái dùng làm chỗ chứa bảng trích. Cố ý KHÔNG xin thêm cột mới: mã `x-dt-key` chỉ có
    quyền SELECT/UPDATE, thêm cột phải chạy migration bằng tay, mà một cột text đủ dùng.

    Parse hỏng -> [] + cảnh báo, và nơi gọi sẽ in toàn văn trở lại: hướng lệch phải là ĐỌC
    THỪA (tốn token), không phải mất bộ lọc trong im lặng.
    """
    raw = (row.get("tom_tat") or "").strip()
    if not raw:
        return []
    try:
        tin = json.loads(raw)
    except json.JSONDecodeError:
        print(f"id={row.get('id')}: bảng đối chiếu lưu hỏng (không phải JSON) — sẽ in lại "
              "toàn văn để trích lại.", file=sys.stderr)
        return []
    if not isinstance(tin, list) or not tin:
        print(f"id={row.get('id')}: bảng đối chiếu rỗng/dạng lạ — sẽ in lại toàn văn.",
              file=sys.stderr)
        return []
    return tin


def dong_so(ids, ctx="đóng sổ"):
    """`da_gop = true` cho các dòng đã hết khung ngày — thôi làm bộ lọc.

    Bản cũ để `make_docx.py` đóng sổ (nó là nơi "gộp" tin vào file). Nay make_docx không còn
    đọc Supabase nữa, nên việc dọn phải nằm ở chính chỗ đọc hàng chờ, kẻo dòng quá hạn nằm
    lại vĩnh viễn và phiên nào cũng đọc ra rồi loại lại.
    """
    if not ids:
        return True
    h = _headers()
    if not h:
        return False
    ok, _ = _curl(
        ["-X", "PATCH",
         f"{SUPABASE_URL}/rest/v1/{BANG}?id=in.({','.join(str(i) for i in ids)})",
         "-H", "Content-Type: application/json", "-H", "Prefer: return=minimal",
         "-d", '{"da_gop": true}'] + h, ctx)
    return ok


def in_hang_cho(now=None):
    """In dữ liệu đối chiếu cho agent, rồi dọn dòng quá khung.

    Hai nhóm in ra khác nhau có chủ đích:
      - dòng CHƯA trích -> in TOÀN VĂN, agent phải đọc rồi nộp bảng đối chiếu qua `--ghi`;
      - dòng ĐÃ trích  -> chỉ in bảng đối chiếu (gọn hơn ~90%), khỏi đọc lại 34.000 ký tự
        mỗi phiên trong suốt 3 ngày file đó còn hiệu lực.
    """
    trong, ngoai = doc_hang_cho(now)
    if ngoai:
        print(f"⚠️ {len(ngoai)} file Jay Lâm gửi đã QUÁ KHUNG {MAX_AGE_DAYS_CNQS + 1} ngày "
              "-> đóng sổ, thôi làm bộ lọc:")
        for r in ngoai:
            print(f"   - id={r.get('id')} {r.get('created_at')} {r.get('ten_file')}")
        if not dong_so([r.get("id") for r in ngoai if r.get("id") is not None]):
            print("⚠️ Đóng sổ nhóm quá hạn KHÔNG thành — phiên sau sẽ đọc lại chúng.",
                  file=sys.stderr)
    co_quan = in_so_coquan(now)
    if not trong:
        print("Không có file Jay Lâm nào trong hàng chờ Supabase.")
        return 0 if co_quan else 10

    chua, roi = [], []
    for r in trong:
        (roi if doc_bang_doi_chieu(r) else chua).append(r)

    print(f"=== {len(trong)} FILE JAY LÂM CÒN HIỆU LỰC LÀM BỘ LỌC ===")
    print("Đây là tin Jay Lâm ĐÃ CÓ. Việc cần làm: đối chiếu THEO SỰ KIỆN với tin mình vừa "
          "quét, tin nào trùng thì khai qua `--ghi-loai` để bỏ khỏi bản tin gửi đi. "
          "KHÔNG đưa bất kỳ nội dung nào dưới đây vào bản tin.")

    if roi:
        print(f"\n### {len(roi)} file ĐÃ TRÍCH — dùng thẳng bảng dưới, khỏi đọc lại toàn văn")
        for r in roi:
            tin = doc_bang_doi_chieu(r)
            print(f"\n--- id={r.get('id')} | gửi {r.get('created_at')} | "
                  f"{r.get('ten_file')} | {len(tin)} tin ---")
            for t in tin:
                if not isinstance(t, dict):
                    continue
                u = (t.get("url") or "").strip()
                print(f"  • {(t.get('tieu_de') or '').strip()}" + (f"  [{u}]" if u else ""))

    if chua:
        print(f"\n### {len(chua)} file CHƯA TRÍCH — đọc toàn văn, rồi nộp bảng qua `--ghi`")
        for r in chua:
            print(f"\n--- id={r.get('id')} | gửi {r.get('created_at')} | "
                  f"file: {r.get('ten_file')} | người gửi: {r.get('ten') or 'Jay Lâm'} ---")
            print((r.get("noi_dung") or "").strip())
    return 0


# --- (2) Bảng đối chiếu trích từ file Jay ---------------------------------

def _dem_url(text):
    return len(re.findall(r"https?://", text or ""))


def kiem_mot_bang(m, cho_phep_ids, da_thay, noi_dung_theo_id):
    """Guardrail cho một mục trong file `--ghi`. Raise ValueError khi không đạt."""
    if not isinstance(m, dict):
        raise ValueError(f"mục không phải object: {str(m)[:80]}")
    try:
        mid = int(m.get("id"))
    except (TypeError, ValueError):
        raise ValueError(f"thiếu/sai `id`: {m.get('id')!r}")
    ctx = f"id={mid}"
    if mid not in cho_phep_ids:
        raise ValueError(f"{ctx}: không nằm trong khung ngày (đã đóng sổ, hoặc id bịa)")
    if mid in da_thay:
        raise ValueError(f"{ctx}: xuất hiện hai lần trong file")
    tin = m.get("tin")
    if not isinstance(tin, list) or not tin:
        raise ValueError(f"{ctx}: `tin` phải là mảng KHÔNG rỗng — file Jay Lâm là file tin, "
                         "trích ra 0 tin nghĩa là bước đọc đã hỏng")
    sach = []
    for k, t in enumerate(tin, 1):
        c2 = f"{ctx} tin#{k}"
        if not isinstance(t, dict):
            raise ValueError(f"{c2}: không phải object")
        td = (t.get("tieu_de") or "").strip()
        if not TIEU_DE_MIN <= len(td) <= TIEU_DE_MAX:
            raise ValueError(f"{c2}: `tieu_de` phải dài {TIEU_DE_MIN}-{TIEU_DE_MAX} ký tự "
                             f"(đang {len(td)})")
        url = (t.get("url") or "").strip()
        if url and not url.startswith(("http://", "https://")):
            # KHÔNG chặn: URL ở đây chỉ là chốt phụ, phép lọc chính là đọc hiểu theo sự kiện.
            # Cố ý KHÔNG dùng `add_news.check_url_quality` — Jay Lâm dẫn cả link trang chủ,
            # mà chặn cả lô vì một link xấu là mất nguyên bảng đối chiếu.
            print(f"{c2}: `url` không phải http(s) -> bỏ URL, giữ tiêu đề.", file=sys.stderr)
            url = ""
        sach.append({"tieu_de": td, "url": url})
    so_url = _dem_url(noi_dung_theo_id.get(mid, ""))
    if so_url >= 6 and len(sach) * 3 < so_url:
        print(f"⚠️ {ctx}: file gốc có {so_url} link mà chỉ trích {len(sach)} tin — nghi TRÍCH "
              "SÓT. Tin bỏ sót ở đây là tin sẽ lọt vào bản tin dù Jay Lâm đã có.",
              file=sys.stderr)
    return {"id": mid, "tin": sach}


def ghi_bang(duong_dan, now=None):
    try:
        data = json.loads(pathlib.Path(duong_dan).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"Không đọc được {duong_dan}: {e}", file=sys.stderr)
        return 1
    if not isinstance(data, list):
        print("File phải là MỘT MẢNG [{id, tin: [{tieu_de, url}]}].", file=sys.stderr)
        return 1
    if not data:
        print("Mảng rỗng — không có gì để ghi.")
        return 0

    trong, _ = doc_hang_cho(now)
    cho_phep = {r.get("id") for r in trong}
    noi_dung = {r.get("id"): (r.get("noi_dung") or "") for r in trong}
    if not cho_phep:
        print("Hàng chờ rỗng (hoặc không đọc được) — không ghi gì.", file=sys.stderr)
        return 1

    sach, da_thay = [], set()
    for m in data:
        try:
            ok = kiem_mot_bang(m, cho_phep, da_thay, noi_dung)
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
        than = {"da_xu_ly": True,
                "tieu_de": f"Bảng đối chiếu: {len(m['tin'])} tin"[:TIEU_DE_MAX],
                "tom_tat": json.dumps(m["tin"], ensure_ascii=False)}
        ok, _ = _curl(
            ["-X", "PATCH", f"{SUPABASE_URL}/rest/v1/{BANG}?id=eq.{m['id']}"] + h +
            ["-H", "Content-Type: application/json", "-H", "Prefer: return=minimal",
             "-d", json.dumps(than, ensure_ascii=False)],
            f"Ghi bảng đối chiếu id={m['id']}")
        if not ok:
            hong.append(m["id"])
    if hong:
        print(f"CHẶN: ghi hỏng {len(hong)}/{len(sach)} dòng (id: {hong}).", file=sys.stderr)
        return 1
    tong = sum(len(m["tin"]) for m in sach)
    print(f"✅ Đã lưu bảng đối chiếu: {len(sach)} file, {tong} tin. "
          "Phiên sau đọc thẳng bảng này, không phải đọc lại toàn văn.")
    return 0


# --- (3) Sổ loại: tin CỦA MÌNH trùng file Jay -----------------------------

def doc_so_loai():
    """Sổ loại trên đĩa. Không có/hỏng -> [] (phía KHÔNG lọc).

    Hướng lệch có chủ ý: sổ hỏng thì bản tin LẶP một tin Jay đã có — phiền nhưng thấy được;
    còn nếu fail về phía lọc thì tin biến mất mà không ai biết. Xoá tin là hướng tệ hơn.
    """
    try:
        d = json.loads(SO_LOAI.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return d if isinstance(d, list) else []


def kiem_mot_loai(m, cho_phep_ids):
    """Guardrail cho một mục trong file `--ghi-loai`. Raise ValueError khi không đạt."""
    if not isinstance(m, dict):
        raise ValueError(f"mục không phải object: {str(m)[:80]}")
    url = (m.get("url") or "").strip()
    if not url.startswith(("http://", "https://")):
        raise ValueError(f"`url` phải là link tin CỦA MÌNH (http/https): {url[:80]!r}")
    td = (m.get("tieu_de") or "").strip()
    if not TIEU_DE_MIN <= len(td) <= TIEU_DE_MINH_MAX:
        raise ValueError(f"{url[:60]}: `tieu_de` (tin của mình) phải dài "
                         f"{TIEU_DE_MIN}-{TIEU_DE_MINH_MAX} ký tự (đang {len(td)})")
    trung_voi = (m.get("trung_voi") or "").strip()
    if len(trung_voi) < TRUNG_VOI_MIN:
        # Luật đã đúc: "tin bị loại phải ghi lại kèm mảnh tương ứng bên file Jay — xoá tin là
        # mất nội dung, phải soi ngược được". Không có mảnh đối ứng thì không soi ngược nổi,
        # và cũng không phân biệt được lọc đúng với lọc oan.
        raise ValueError(f"{url[:60]}: thiếu `trung_voi` (mảnh tương ứng bên file Jay Lâm, "
                         f"tối thiểu {TRUNG_VOI_MIN} ký tự) — không có thì không soi ngược "
                         "được vì sao tin bị bỏ")
    tho = m.get("id_jay")
    try:
        id_jay = int(tho)
    except (TypeError, ValueError):
        # Nhánh NHÃN: file .docx nạp cục bộ qua `--nap-file` không có id Supabase, nó mang
        # nhãn chuỗi (vd "ĐTN_M_01.9.2026"). Chấp nhận, NHƯNG chỉ khi nhãn đó thật sự có
        # trong sổ đối chiếu cục bộ — nếu không thì `trung_voi` trỏ vào hư không và không ai
        # soi ngược được vì sao tin biến mất. Đây là chỗ duy nhất nới kiểu của `id_jay`.
        nhan = unicodedata.normalize("NFC", str(tho or "").strip())
        if not nhan:
            raise ValueError(f"{url[:60]}: thiếu/sai `id_jay`: {tho!r}")
        co = nhan_con_hieu_luc()
        if nhan not in co:
            raise ValueError(
                f"{url[:60]}: `id_jay`={nhan!r} không phải id hàng chờ, cũng không phải nhãn "
                f"nào trong sổ đối chiếu cục bộ ({sorted(co) or 'sổ rỗng'}) — nạp file bằng "
                "`--nap-file` trước, hoặc khai đúng nhãn")
        return {"url": url, "tieu_de": td[:TIEU_DE_MINH_MAX],
                "trung_voi": trung_voi[:TIEU_DE_MAX], "id_jay": nhan}
    if cho_phep_ids and id_jay not in cho_phep_ids:
        # CẢNH BÁO chứ không chặn: dòng Jay có thể vừa hết khung và bị đóng sổ giữa chừng,
        # mà chặn ở đây là giữ lại một tin Huy đã xác định là trùng.
        print(f"⚠️ {url[:60]}: `id_jay`={id_jay} không còn trong khung ngày — vẫn ghi.",
              file=sys.stderr)
    return {"url": url, "tieu_de": td[:TIEU_DE_MINH_MAX],
            "trung_voi": trung_voi[:TIEU_DE_MAX], "id_jay": id_jay}


def ghi_loai(duong_dan, now=None):
    now = now or datetime.datetime.now(VN)
    try:
        data = json.loads(pathlib.Path(duong_dan).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"Không đọc được {duong_dan}: {e}", file=sys.stderr)
        return 1
    if not isinstance(data, list):
        print("File phải là MỘT MẢNG [{url, tieu_de, id_jay, trung_voi}].", file=sys.stderr)
        return 1
    if not data:
        print("Không có tin nào trùng file Jay Lâm — sổ loại giữ nguyên.")
        return 0

    trong, _ = doc_hang_cho(now)
    cho_phep = {r.get("id") for r in trong}

    sach = []
    for m in data:
        try:
            sach.append(kiem_mot_loai(m, cho_phep))
        except ValueError as e:
            print(f"CHẶN: {e}", file=sys.stderr)
            return 1

    ngay = now.date().isoformat()
    cu = doc_so_loai()
    # Dedupe theo URL, bản MỚI thắng (lý do trùng có thể được khai lại rõ hơn).
    theo_url = {}
    for r in cu:
        if isinstance(r, dict) and (r.get("url") or "").strip():
            theo_url[r["url"].strip()] = r
    for m in sach:
        theo_url[m["url"]] = dict(m, ngay=ngay)

    han = han_giu_so(now)
    giu = [r for r in theo_url.values() if (r.get("ngay") or "") >= han]
    giu.sort(key=lambda r: (r.get("ngay") or "", r.get("url") or ""))

    try:
        SO_LOAI.parent.mkdir(parents=True, exist_ok=True)
        SO_LOAI.write_text(json.dumps(giu, ensure_ascii=False, indent=1) + "\n",
                           encoding="utf-8")
    except OSError as e:
        print(f"CHẶN: không ghi được {SO_LOAI}: {e}", file=sys.stderr)
        return 1
    print(f"✅ Sổ loại: thêm {len(sach)} tin trùng file Jay Lâm, tổng {len(giu)} dòng còn "
          f"trong {GIU_NGAY} ngày -> {SO_LOAI}")
    print("   Nhớ `git add logs/` cùng bản tin, nếu không make_docx sẽ không thấy sổ.")
    for m in sach:
        print(f"   - {m['tieu_de'][:70]}\n     trùng: {m['trung_voi'][:70]}")
    return 0


# --- (4) Nạp file .docx CỤC BỘ làm bộ lọc ---------------------------------
#
# Vì sao có nhánh này: `doc_hang_cho()` chỉ đọc hàng chờ trên Supabase, tức chỉ thấy file do
# Jay Lâm gửi qua bot Telegram. File cơ quan Huy nhận rồi quăng thẳng vào khung chat nằm ở
# `~/Downloads/` thì KHÔNG có cửa nào vào sổ chống trùng — 01/09/2026 phải bóc 27 link của
# `ĐTN_M_01.9.2026.docx` bằng tay rồi tự soạn `logs/trung-jaylam.json`. Nhánh này thay đúng
# việc tay đó.
#
# ⚠️ Nhánh này CHỈ bắt được trùng ĐƯỜNG DẪN, và điều đó là đủ dùng vì file cơ quan dẫn thẳng
# nguồn gốc (đo 01/09: 5/25 tin quét được khớp đúng đường dẫn). Nó KHÔNG thay được phép đối
# chiếu theo SỰ KIỆN — file Jay Lâm viết lại bằng tiếng Việt từ nguồn khác nên 0/12 tin trùng
# link mà 3 tin trùng sự kiện (đo 01/08, ghi ở đầu file). Vì thế bảng trích ra vẫn được in
# trong `--liet-ke` để agent đọc hiểu, chứ không phải nạp xong là xong.

_RE_DOAN = re.compile(r"<w:p[ >].*?</w:p>", re.S)
_RE_HYPERLINK = re.compile(r'<w:hyperlink[^>]*r:id="(rId\d+)"')
_RE_WT = re.compile(r"<w:t[^>]*>(.*?)</w:t>", re.S)
_RE_REL = re.compile(r"<Relationship\b[^>]*?/?>")
_RE_URL_TRAN = re.compile(r"https?://[^\s<>\"']+")
# Dấu câu dính đuôi một link dán trần. `)` KHÔNG nằm ở đây: nhiều đường dẫn mang ngoặc đơn
# hợp lệ (Ballotpedia, Wikipedia), cắt bừa là ra link 404 rồi ghi vào sổ như một tin khác.
_DAU_DUOI = ".,;:!?\u2019\u201d"


def _cat_dau_duoi(u):
    """Bỏ dấu câu dính đuôi link dán trần, cắt `)` CHỈ khi ngoặc mất cân bằng.

    Đo thật 01/09/2026 trên `ĐTN_M_01.9.2026.docx`: cắt `)` vô điều kiện làm link
    `ballotpedia.org/..._(September_1_Democratic_primary)` cụt mất ký tự cuối, nên nó không
    khớp với chính bản hyperlink của cùng đoạn và file bóc ra 28 link thay vì 27 — một link
    ma, và là link không mở được.
    """
    u = (u or "").strip()
    while u:
        if u[-1] in _DAU_DUOI:
            u = u[:-1]
        elif u[-1] == ")" and u.count(")") > u.count("("):
            u = u[:-1]
        else:
            break
    return u


def chuan_url(u):
    """Dạng chuẩn của một URL, CHỈ để so khớp — không bao giờ ghi dạng này vào sổ.

    `make_docx.loc_bo_trung_jaylam()` so `sourceUrl` NGUYÊN VĂN với `url` trong sổ, nên sổ
    phải giữ link gốc của tin mình; bản chuẩn hoá chỉ sống trong bộ nhớ lúc đối chiếu.

    Chuẩn hoá hẹp có chủ ý: hạ chữ thường tên miền, bỏ `www.`, bỏ khác biệt http/https, bỏ
    dấu `/` cuối, bỏ mảnh `#`, bỏ đúng danh sách tham số theo dõi ở `THAM_SO_BO`. Bỏ rộng tay
    hơn (cắt sạch query) là gộp nhầm hai bài khác nhau trên cùng một trang thành một, tức
    XOÁ OAN một tin khỏi bản tin — hướng lệch tệ hơn hẳn việc bỏ lọt một tin trùng.
    """
    u = unicodedata.normalize("NFC", (u or "").strip())
    if not u:
        return ""
    try:
        p = urllib.parse.urlsplit(u)
    except ValueError:
        return u.lower()
    host = (p.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    duong = urllib.parse.unquote(p.path or "").rstrip("/")
    q = [(k, v) for k, v in urllib.parse.parse_qsl(p.query, keep_blank_values=True)
         if k.lower() not in THAM_SO_BO]
    q.sort()
    truy_van = urllib.parse.urlencode(q) if q else ""
    return f"{host}{duong}" + (f"?{truy_van}" if truy_van else "")


def _chu_sach(s):
    return re.sub(r"\s+", " ", (s or "").replace(" ", " ")).strip()


def boc_docx(duong_dan):
    """(ten_file, [{tieu_de, url}]) bóc ra từ một file .docx. Raise ValueError khi hỏng.

    Lấy link theo HAI đường, vì file cơ quan gửi trộn cả hai dạng: (i) hyperlink thật —
    `w:hyperlink r:id` trỏ vào `word/_rels/document.xml.rels`; (ii) link dán trần trong chữ,
    không tạo quan hệ nào. Bỏ đường (ii) là mất câm đúng những đoạn người soạn dán vội.

    Tiêu đề của một tin = chữ của CHÍNH đoạn chứa link, đã bỏ phần link dính đuôi.
    """
    p = pathlib.Path(duong_dan)
    if not p.is_file():
        raise ValueError(f"không thấy file: {p}")
    try:
        with zipfile.ZipFile(p) as z:
            ten = set(z.namelist())
            if "word/document.xml" not in ten:
                raise ValueError(f"{p.name}: không phải file .docx (thiếu word/document.xml)")
            doc = z.read("word/document.xml").decode("utf-8", "replace")
            rels_raw = (z.read("word/_rels/document.xml.rels").decode("utf-8", "replace")
                        if "word/_rels/document.xml.rels" in ten else "")
    except zipfile.BadZipFile:
        raise ValueError(f"{p.name}: không mở được như file nén (.docx hỏng, hoặc là .doc cũ)")

    rels = {}
    for r in _RE_REL.findall(rels_raw):
        if "/hyperlink" not in r:
            continue
        mid = re.search(r'Id="([^"]+)"', r)
        mt = re.search(r'Target="([^"]+)"', r)
        if not mid or not mt:
            continue
        t = html.unescape(mt.group(1)).strip()
        if t.startswith(("http://", "https://")):
            rels[mid.group(1)] = t

    tin, da_thay = [], set()
    for doan in _RE_DOAN.findall(doc):
        chu = _chu_sach(html.unescape("".join(_RE_WT.findall(doan))))
        urls = [rels[i] for i in _RE_HYPERLINK.findall(doan) if i in rels]
        urls += [_cat_dau_duoi(u) for u in _RE_URL_TRAN.findall(chu)]
        if not urls:
            continue
        tieu_de = _chu_sach(_RE_URL_TRAN.sub("", chu))
        if len(tieu_de) < TIEU_DE_MIN:
            # Giữ tin, KHÔNG bỏ: một đoạn chỉ có link vẫn là một tin cơ quan đã có, bỏ nó là
            # để lọt đúng tin mình phải cắt. Nhãn dài đủ để `trung_voi` soi ngược được.
            tieu_de = "⚠ đoạn không có chữ, chỉ có đường dẫn"
        for u in urls:
            k = chuan_url(u)
            if not k or k in da_thay:
                continue
            da_thay.add(k)
            tin.append({"tieu_de": tieu_de[:TIEU_DE_MAX], "url": u})

    if not tin:
        # Cùng lẽ với `kiem_mot_bang`: file tin mà bóc ra 0 link nghĩa là bước bóc đã hỏng,
        # và một bộ lọc rỗng thì im lặng không chặn gì cả.
        raise ValueError(f"{p.name}: bóc ra 0 đường dẫn — file không phải bản tin, hoặc "
                         "cấu trúc .docx khác khuôn (kiểm lại bằng cách mở file)")
    return p.name, tin


def doc_so_coquan():
    """Sổ bảng đối chiếu cục bộ. Không có/hỏng -> [] (phía KHÔNG lọc, như `doc_so_loai`)."""
    try:
        d = json.loads(SO_COQUAN.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return [r for r in d if isinstance(r, dict)] if isinstance(d, list) else []


def nhan_con_hieu_luc(now=None):
    """Tập nhãn file cục bộ còn trong sổ — dùng làm `id_jay` hợp lệ cho `--ghi-loai`."""
    return {(r.get("nhan") or "").strip() for r in doc_so_coquan()
            if (r.get("nhan") or "").strip()}


def tin_cua_minh():
    """[{url, tieu_de}] mọi tin đang sống trong `index.html`.

    Tập URL lấy thẳng từ `add_news.collect_existing_urls()` — bản gốc DUY NHẤT của phép
    "những link nào đang nằm trong kho". Chép lại vòng duyệt ở đây là hai bản tách nhánh: nạp
    thêm một nhánh tin mới bên `add_news` mà quên sửa bên này thì nhánh đó không bao giờ được
    lọc trùng, hỏng câm. Vòng duyệt phía dưới chỉ để GẮN TIÊU ĐỀ cho các URL ấy.
    """
    sys.path.insert(0, str(ROOT / "scripts"))
    import add_news                                             # noqa: PLC0415

    html_txt = INDEX.read_text(encoding="utf-8")
    a, b = add_news.find_data_span(html_txt)
    data = json.loads(html_txt[a:b])

    tieu_de = {}
    for nhanh in ("worldNews", "usNews", "xNews", "baomoiNews"):
        for it in data.get(nhanh, []) or []:
            for k in ("sourceUrl", "url", "_baomoiUrl"):
                u = (it.get(k) or "").strip()
                if u:
                    tieu_de.setdefault(u, (it.get("title") or it.get("text") or "").strip())
    for grp in ("exercises", "dipEvents"):
        for ev in data.get(grp, []) or []:
            for it in ev.get("items", []) or []:
                u = (it.get("sourceUrl") or "").strip()
                if u:
                    tieu_de.setdefault(u, (it.get("title") or "").strip())

    ra = []
    for u in add_news.collect_existing_urls(data):
        u = (u or "").strip()
        if u:
            ra.append({"url": u, "tieu_de": tieu_de.get(u) or "(không rõ tiêu đề)"})
    return ra


def in_so_coquan(now=None):
    """In bảng đối chiếu của các file .docx nạp cục bộ. Trả về số file còn hiệu lực.

    In CẢ khi hàng chờ Supabase rỗng: hai nguồn file độc lập nhau, và nguồn cục bộ chính là
    nguồn hay có mặt hơn (file cơ quan gửi thẳng cho Huy). Bảng in ra để agent đối chiếu theo
    SỰ KIỆN — phần `--nap-file` đã tự lo phần trùng đường dẫn.
    """
    now = now or datetime.datetime.now(VN)
    han = han_giu_so(now)
    so = [r for r in doc_so_coquan() if (r.get("ngay") or "") >= han]
    if not so:
        return 0
    tong = sum(len(r.get("tin") or []) for r in so)
    print(f"\n=== {len(so)} FILE CƠ QUAN NẠP CỤC BỘ ({tong} tin) — bộ lọc theo SỰ KIỆN ===")
    print("Tin trùng ĐƯỜNG DẪN đã được `--nap-file` loại tự động. Việc còn lại: đọc bảng "
          "dưới, tin nào của mình trùng SỰ KIỆN mà khác link thì khai qua `--ghi-loai` với "
          "`id_jay` là NHÃN của file.")
    for r in so:
        print(f"\n--- nhãn={r.get('nhan')!r} | nạp {r.get('ngay')} | {r.get('ten_file')} | "
              f"{len(r.get('tin') or [])} tin ---")
        for t2 in r.get("tin") or []:
            if isinstance(t2, dict):
                u = (t2.get("url") or "").strip()
                print(f"  • {(t2.get('tieu_de') or '').strip()}" + (f"  [{u}]" if u else ""))
    return len(so)


def nap_file(duong_dan, nhan=None, thu=False, now=None):
    """Nạp một .docx cục bộ vào sổ đối chiếu, rồi tự loại tin mình trùng ĐƯỜNG DẪN."""
    now = now or datetime.datetime.now(VN)
    try:
        ten_file, tin = boc_docx(duong_dan)
    except ValueError as e:
        print(f"CHẶN: {e}", file=sys.stderr)
        return 1

    nhan = unicodedata.normalize("NFC", (nhan or "").strip()) or \
        unicodedata.normalize("NFC", pathlib.Path(duong_dan).stem.strip())
    if not NHAN_MIN <= len(nhan) <= NHAN_MAX:
        print(f"CHẶN: `--nhan` phải dài {NHAN_MIN}-{NHAN_MAX} ký tự (đang {len(nhan)}: "
              f"{nhan[:80]!r}) — nhãn là thứ soi ngược về file cơ quan đã gửi.",
              file=sys.stderr)
        return 1

    print(f"📄 {ten_file} -> nhãn {nhan!r}: bóc được {len(tin)} tin")

    try:
        cua_minh = tin_cua_minh()
    except (OSError, ValueError, json.JSONDecodeError, ImportError) as e:
        print(f"CHẶN: không đọc được tin của mình trong index.html ({e}).", file=sys.stderr)
        return 1

    theo_khoa = {}
    for t in tin:
        theo_khoa.setdefault(chuan_url(t["url"]), t)
    trung = []
    for it in cua_minh:
        t = theo_khoa.get(chuan_url(it["url"]))
        if t:
            trung.append({"url": it["url"], "tieu_de": it["tieu_de"][:TIEU_DE_MINH_MAX],
                          "trung_voi": f"có trong file {ten_file} cơ quan gửi "
                                       "(khớp ĐÚNG đường dẫn)"[:TIEU_DE_MAX],
                          "id_jay": nhan, "ngay": now.date().isoformat()})
    trung.sort(key=lambda r: r["url"])

    print(f"🔎 Đối chiếu {len(cua_minh)} tin đang sống trong kho: {len(trung)} tin trùng "
          "ĐƯỜNG DẪN")
    for r in trung:
        print(f"   - {r['tieu_de'][:90]}\n     {r['url']}")
    if not trung:
        print("   (0 tin trùng link. KHÔNG có nghĩa là 0 tin trùng SỰ KIỆN — chạy "
              "`--liet-ke` rồi đối chiếu nội dung.)")

    if thu:
        print("— `--thu`: chỉ xem trước, KHÔNG ghi sổ nào.")
        return 0

    # Sổ đối chiếu cục bộ: dedupe theo nhãn, bản mới thắng; cắt theo `GIU_NGAY` như sổ loại.
    han = han_giu_so(now)
    theo_nhan = {(r.get("nhan") or "").strip(): r for r in doc_so_coquan()
                 if (r.get("nhan") or "").strip()}
    theo_nhan[nhan] = {"nhan": nhan, "ten_file": ten_file,
                       "ngay": now.date().isoformat(), "tin": tin}
    giu = [r for r in theo_nhan.values() if (r.get("ngay") or "") >= han]
    giu.sort(key=lambda r: (r.get("ngay") or "", r.get("nhan") or ""))
    try:
        SO_COQUAN.parent.mkdir(parents=True, exist_ok=True)
        SO_COQUAN.write_text(json.dumps(giu, ensure_ascii=False, indent=1) + "\n",
                             encoding="utf-8")
    except OSError as e:
        print(f"CHẶN: không ghi được {SO_COQUAN}: {e}", file=sys.stderr)
        return 1
    print(f"✅ Sổ đối chiếu cục bộ: {len(giu)} file còn trong {GIU_NGAY} ngày -> {SO_COQUAN}")

    if not trung:
        return 0

    cu = doc_so_loai()
    theo_url = {}
    for r in cu:
        if isinstance(r, dict) and (r.get("url") or "").strip():
            theo_url[r["url"].strip()] = r
    for r in trung:
        theo_url[r["url"]] = r
    giu_loai = [r for r in theo_url.values() if (r.get("ngay") or "") >= han]
    giu_loai.sort(key=lambda r: (r.get("ngay") or "", r.get("url") or ""))
    try:
        SO_LOAI.write_text(json.dumps(giu_loai, ensure_ascii=False, indent=1) + "\n",
                           encoding="utf-8")
    except OSError as e:
        print(f"CHẶN: không ghi được {SO_LOAI}: {e}", file=sys.stderr)
        return 1
    print(f"✅ Sổ loại: thêm {len(trung)} tin trùng, tổng {len(giu_loai)} dòng -> {SO_LOAI}")
    print("   Nhớ commit cả logs/, nếu không make_docx sẽ không thấy sổ.")
    return 0


def _gia_tri(argv, co):
    """Giá trị của một cờ dạng `--co X` hoặc `--co=X`. Không có -> None."""
    for i, a in enumerate(argv):
        if a == co:
            return argv[i + 1] if i + 1 < len(argv) else ""
        if a.startswith(co + "="):
            return a.split("=", 1)[1]
    return None


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--liet-ke" in argv:
        return in_hang_cho()
    dd = _gia_tri(argv, "--nap-file")
    if dd is not None:
        if not dd:
            print("Thiếu đường dẫn file .docx sau --nap-file.", file=sys.stderr)
            return 1
        return nap_file(dd, nhan=_gia_tri(argv, "--nhan"), thu="--thu" in argv)
    for co, ham in (("--ghi-loai", ghi_loai), ("--ghi", ghi_bang)):
        if co in argv:
            i = argv.index(co)
            if i + 1 >= len(argv):
                print(f"Thiếu đường dẫn file sau {co}.", file=sys.stderr)
                return 1
            return ham(argv[i + 1])
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
