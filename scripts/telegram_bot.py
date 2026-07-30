#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bot hỏi–đáp Telegram: đọc câu hỏi mới, và gửi câu trả lời về.

    python3 scripts/telegram_bot.py --doc                 # đọc câu hỏi mới
    python3 scripts/telegram_bot.py --tra-loi tl.txt --chat 123   # gửi trả lời
    python3 scripts/telegram_bot.py --bao "..." --chat 123        # gửi một dòng thông báo

`--doc` in câu hỏi ra stdout, ghi `/tmp/tg-questions.json`, và trả mã thoát:
    0  = có câu hỏi mới      10 = không có gì      1 = lỗi

⚠️ KHÔNG LƯU OFFSET VÀO REPO. Telegram tự giữ hàng đợi update chưa xác nhận trong 24h;
gọi `getUpdates?offset=<id cuối + 1>` là nó xoá các update cũ. Dùng chính cơ chế đó làm
"con trỏ đã đọc" thì không phải commit file state mỗi 5 phút (rác lịch sử git, và đụng
`git pull --rebase` của phiên quét đang chạy).

⚠️ XÁC NHẬN NGAY SAU KHI ĐỌC, TRƯỚC KHI XỬ LÝ. Nếu xác nhận sau, một câu hỏi làm Claude
lỗi sẽ được đọc lại mỗi 5 phút và lỗi mãi mãi. Đổi lại, câu hỏi bị mất nếu workflow chết
giữa chừng — nên workflow gửi ngay tin "đang xử lý" và gửi tin báo lỗi nếu hỏng, để Huy
không bao giờ rơi vào cảnh im lặng không biết vì sao.

⚠️ CHỈ TRẢ LỜI CHAT TRONG DANH SÁCH TRẮNG (`TELEGRAM_CHAT_ID`). Bot Telegram ai cũng nhắn
được — không lọc thì người lạ dùng được hạn mức Claude của Huy và đọc được dữ liệu bản tin.

⚠️ KHÔNG IN NỘI DUNG CÂU HỎI RA STDOUT (chốt 27/07/2026). Stdout của phiên này đi thẳng vào
log GitHub Actions, mà repo đang PUBLIC — đã kiểm: khách vãng lai không đăng nhập thì không
xem được log, nhưng người có tài khoản GitHub bất kỳ thì rất có thể xem được (public repo =
ai cũng có quyền đọc). Câu hỏi người ta nhắn riêng cho bot không nên nằm ở đó. Log chỉ in
chat id + độ dài — đủ để chẩn đoán.

Bù lại, Huy vẫn theo dõi được đầy đủ: `--tra-loi` TỰ ĐỘNG chuyển tiếp câu hỏi + câu trả lời
về chat của Huy khi người hỏi không phải Huy. Cố ý đặt trong script chứ không nhờ prompt —
prompt thì Claude có thể quên, còn cơ chế thì không.
"""
import argparse
import datetime
import html
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import zoneinfo

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from tg_api import call, tai_file  # noqa: E402
import docx_text  # noqa: E402

VN = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")

QUESTIONS = "/tmp/tg-questions.json"
# Bỏ câu hỏi cũ hơn ngần này — tránh trả lời một câu Huy hỏi từ hôm qua khi bot vừa hồi sinh
# sau sự cố (Telegram giữ hàng đợi tới 24h).
#
# ⚠️ 60 → 360 PHÚT (28/07/2026). Ngưỡng 60' được đặt khi tin rằng cron `*/5` chạy mỗi 5 phút.
# ĐO THẬT 12 vòng gần nhất: khoảng cách giữa hai lần chạy là **66–148 phút**, không lần nào
# gần 5 phút — GitHub hạ ưu tiên mạnh cron tần suất cao trên repo public. Hệ quả: câu hỏi rơi
# vào khoảng cách >60' bị vứt với lý do "quá cũ", mà `--doc` đã xác nhận offset ngay khi đọc
# nên câu đó MẤT HẲN — Huy hỏi và không bao giờ nhận được trả lời, cũng không có dấu hiệu gì.
# 360' nuốt được nhịp tệ nhất đo được (148') với biên rộng, mà vẫn chặn đúng ca nó sinh ra để
# chặn: bot chết qua đêm rồi hồi sinh, moi câu hỏi 20 tiếng tuổi ra trả lời.
MAX_AGE_PHUT = 360
MAX_LEN = 3800


def danh_sach_chat():
    return [c.strip() for c in os.environ.get("TELEGRAM_CHAT_ID", "").split(",") if c.strip()]


def chats_cho_phep():
    return set(danh_sach_chat())


def chat_chu():
    """Chat của Huy — nơi nhận bản sao hội thoại của người khác.

    Mặc định là chat ĐẦU TIÊN trong `TELEGRAM_CHAT_ID` (telegram_setup.py liệt kê theo thứ
    tự Huy chọn, và Huy là người bấm START đầu tiên). Đặt `TELEGRAM_OWNER_CHAT` để ghi đè
    nếu thứ tự đó đổi.
    """
    rieng = os.environ.get("TELEGRAM_OWNER_CHAT", "").strip()
    if rieng:
        return rieng
    ds = danh_sach_chat()
    return ds[0] if ds else ""


XOA_TOI_DA = 20


def xu_ly_xoa(token, m, chat) -> None:
    """Lệnh `/xoa [n]` — xoá tin rác KHỎI CẢ HAI PHÍA của cuộc trò chuyện.

    Vì sao phải reply chứ không có lệnh kiểu "/xoa 5 tin cuối": Bot API **không cho đọc lịch
    sử chat**. Không có phương thức nào liệt kê tin đã gửi, và `getUpdates` chỉ trả tin ĐẾN
    bot. Bot cũng không lưu `message_id` của tin nó gửi. Nhưng khi người dùng REPLY, update
    mang theo `reply_to_message.message_id` — đó là đường duy nhất để bot biết chính xác phải
    xoá tin nào.

    `n > 1` xoá n tin LIÊN TIẾP tính từ tin được reply. `message_id` trong một chat là số
    tăng dần qua MỌI tin (cả bot lẫn người), nên n tin liên tiếp = `id, id+1, … id+n-1` —
    đúng những gì Huy đang nhìn thấy trên màn hình. Trần `XOA_TOI_DA` để một lần gõ nhầm
    không quét sạch cả bản tin.

    GIỚI HẠN CỨNG CỦA TELEGRAM, không lách được: **chỉ xoá được tin gửi trong 48 giờ**. Cũ
    hơn thì API trả lỗi và tin nằm lại — phải xoá tay trong app.
    """
    rep = m.get("reply_to_message") or {}
    goc = rep.get("message_id")
    phan = (m.get("text") or "").split()
    try:
        so = max(1, min(XOA_TOI_DA, int(phan[1]))) if len(phan) > 1 else 1
    except ValueError:
        so = 1

    if not goc:
        call(token, "sendMessage", {
            "chat_id": chat,
            "text": ("Cách dùng: REPLY vào tin rác rồi gõ /xoa\n"
                     f"Xoá nhiều tin liên tiếp: /xoa 5 (tối đa {XOA_TOI_DA}), tính từ tin mày reply.\n\n"
                     "Telegram chỉ cho bot xoá tin trong 48 giờ gần nhất."),
            "disable_web_page_preview": True})
        return

    xong, hong = 0, []
    for i in range(so):
        r = call(token, "deleteMessage", {"chat_id": chat, "message_id": goc + i})
        if r.get("ok"):
            xong += 1
        else:
            hong.append(r.get("description") or "?")
    # Xoá luôn chính lệnh /xoa: để lại thì chat vẫn còn rác, chỉ là rác khác.
    call(token, "deleteMessage", {"chat_id": chat, "message_id": m.get("message_id")})

    print(f"[xoa] chat …{chat[-4:]}: xoá {xong}/{so} tin", file=sys.stderr)
    if not hong:
        return          # xoá sạch thì im — tin biến mất đã là phản hồi rõ nhất
    # Hỏng thì PHẢI nói, kèm lý do thật của Telegram: im lặng ở đây làm Huy tưởng đã xoá.
    ly_do = hong[0]
    them = ("\n(Tin quá 48 giờ thì bot không xoá được — phải xoá tay trong app.)"
            if "too old" in ly_do.lower() or "can't be deleted" in ly_do.lower() else "")
    call(token, "sendMessage", {
        "chat_id": chat,
        "text": f"Xoá được {xong}/{so} tin. Lỗi: {ly_do}{them}",
        "disable_web_page_preview": True})


# --- Lịch sử chat làm ngữ cảnh (thêm 28/07/2026, Huy hỏi "cho bot lưu lại lịch sử chat
# làm ngữ cảnh được không") ---
ROOT = pathlib.Path(__file__).resolve().parent.parent
SUPABASE_URL = "https://ltmlueqkajqmduoqghdf.supabase.co"
# Mã cấp quyền ĐỌC 2 bảng dt_* — cùng file/env với ho_so_doc_gia.py, KHÔNG phải service key
# (thứ mở toàn bộ database gồm ViNha/bi-a/Hương Diện). Xem CLAUDE.md mục "Bot hỏi–đáp".
DT_KEY_FILE = pathlib.Path(os.environ.get("DT_KEY_FILE", "/Users/Huy/Claude/.dt-bot-key"))
LICH_SU_PHUT = 60          # chỉ tính là "cùng hội thoại" nếu hỏi trong 1 tiếng gần đây
LICH_SU_GIOI_HAN = 5       # tối đa 5 lượt gần nhất — đừng nhồi cả tháng vào ngữ cảnh
LICH_SU_TRA_LOI_MAX = 500  # cắt câu trả lời cũ dài, đừng để 1 câu nuốt hết chỗ ngữ cảnh


def _anon_key():
    k = os.environ.get("SUPABASE_ANON_KEY", "").strip()
    if k:
        return k
    try:
        src = (ROOT / "index.html").read_text(encoding="utf-8")
    except OSError:
        return ""
    m = re.search(r"sb_publishable_[A-Za-z0-9_-]{10,}", src)
    return m.group(0) if m else ""


def _dt_bot_key():
    k = os.environ.get("DT_BOT_KEY", "").strip()
    if k:
        return k
    try:
        return DT_KEY_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def lich_su_gan_day(chat):
    """Lượt hỏi-đáp gần đây CỦA CÙNG chat này — làm ngữ cảnh cho câu hỏi tiếp theo.

    VÌ SAO CẦN: mỗi lần bot chạy là một tiến trình GitHub Actions MỚI, không tự nhớ gì giữa
    hai lượt hỏi — "còn trong tháng 8?" mà không biết câu trước hỏi về tập trận NATO thì
    không trả lời được. Bảng `dt_bot_hoi` đã ghi MỌI lượt hỏi-đáp từ 27/07 (`bot_luu.py`),
    chỉ thiếu đường ĐỌC LẠI nó trước khi trả lời — hàm này là đường đó.

    Đi qua mã riêng `x-dt-key` (giống `ho_so_doc_gia.py`), KHÔNG dùng service key: mã này
    chỉ mở quyền đọc 2 bảng `dt_*`, không mở toàn bộ database.

    ⚠️ Giới hạn CẢ THỜI GIAN lẫn SỐ LƯỢNG — không lấy "toàn bộ lịch sử": câu hỏi hôm qua
    không cùng mạch chuyện với câu hỏi hôm nay, nạp vào chỉ gây nhiễu — nguy hơn nữa nếu bot
    coi nhầm đó là ngữ cảnh còn hiệu lực rồi trả lời theo thông tin đã cũ.

    Hỏng/thiếu mã (secret chưa cắm, mạng lỗi) → trả `[]`, ĐỪNG làm cả `--doc` hỏng theo:
    lịch sử là phần LÀM GIÀU câu trả lời, không phải điều kiện cần để trả lời được.
    """
    key, ma = _anon_key(), _dt_bot_key()
    if not key or not ma:
        return []
    han = (datetime.datetime.now(datetime.timezone.utc)
           - datetime.timedelta(minutes=LICH_SU_PHUT)).isoformat()
    try:
        p = subprocess.run(
            ["curl", "-sS", "--max-time", "20",
             f"{SUPABASE_URL}/rest/v1/dt_bot_hoi"
             f"?select=cau_hoi,tra_loi,created_at&chat_id=eq.{chat}"
             f"&created_at=gte.{han}&order=created_at.desc&limit={LICH_SU_GIOI_HAN}",
             "-H", f"apikey: {key}", "-H", f"Authorization: Bearer {key}",
             "-H", f"x-dt-key: {ma}"],
            capture_output=True, text=True, timeout=25)
        rows = json.loads(p.stdout)
        if not isinstance(rows, list):
            return []
    except Exception as e:                      # noqa: BLE001 - best-effort, xem docstring
        print(f"   ⚠️  không lấy được lịch sử chat: {e}", file=sys.stderr)
        return []
    rows.reverse()   # Supabase trả mới→cũ; đọc như hội thoại thì phải cũ→mới.
    ra = []
    for r in rows:
        tl = r.get("tra_loi") or ""
        if len(tl) > LICH_SU_TRA_LOI_MAX:
            tl = tl[:LICH_SU_TRA_LOI_MAX] + "…"
        ra.append({"cau_hoi": r.get("cau_hoi") or "", "tra_loi": tl})
    return ra


# --- Tin Jay Lâm gửi file .docx — gộp thành tổng hợp cuối ngày (thêm 30/07/2026, Huy hỏi) ---
# Huy chốt: file cuối ngày là TÀI LIỆU RIÊNG cho Huy đọc, KHÔNG tự động nạp lên bản tin công
# khai (xem mục "Ràng buộc kênh — Jay Lâm là NGƯỜI NGOÀI" trong CLAUDE.md — cùng nguyên tắc).
# Lưu vào Supabase (KHÔNG lưu file/text vào repo — repo PUBLIC, xem docstring `bot_luu.py`),
# gộp mỗi tối bằng `scripts/gop_tin_jaylam.py`, gửi CHỈ tới chat_chu() (chat riêng của Huy).
JAYLAM_BANG = "dt_jaylam_inbox"
JAYLAM_MAX_CHARS = 20000


def luu_tin_jaylam(chat, ten, ten_file, noi_dung):
    """Ghi một tin Jay Lâm gửi vào bảng `dt_jaylam_inbox`. Trả True/False.

    RLS insert mở cho anon (giống `dt_bot_hoi`, xem `bot_luu.py`) — không cần mã riêng để ghi,
    chỉ cần mã riêng (`x-dt-key`) để ĐỌC LẠI lúc gộp cuối ngày (`gop_tin_jaylam.py`).
    """
    key = _anon_key()
    if not key:
        return False
    ngay_vn = datetime.datetime.now(VN).date().isoformat()
    ban_ghi = {"chat_id": chat, "ten": ten, "ten_file": ten_file,
               "noi_dung": noi_dung, "ngay_vn": ngay_vn}
    p = subprocess.run(
        ["curl", "-sS", "--max-time", "30", "-X", "POST",
         f"{SUPABASE_URL}/rest/v1/{JAYLAM_BANG}",
         "-H", f"apikey: {key}", "-H", f"Authorization: Bearer {key}",
         "-H", "Content-Type: application/json", "-H", "Prefer: return=minimal",
         "-w", "\n@@%{http_code}", "-d", json.dumps(ban_ghi, ensure_ascii=False)],
        capture_output=True, text=True)
    out = (p.stdout or "").strip()
    ma = out.rsplit("@@", 1)[-1] if "@@" in out else "?"
    return ma.startswith("2")


def xu_ly_tin_jaylam(token, chat, m, doc_att):
    """Nhận file .docx đính kèm — tải, trích text, lưu Supabase, xác nhận với người gửi.

    Xử lý NGAY trong `--doc` (rẻ, không cần `claude -p`) — giống lệnh `/xoa`: đây là việc cơ
    học (tải + bóc XML + ghi DB), không cần suy nghĩ, bắt chờ cài Claude Code là vô lý.
    """
    ten_file = doc_att.get("file_name") or "(không tên)"
    ten_nguoi = (m.get("from") or {}).get("first_name", "")
    if not ten_file.lower().endswith(".docx"):
        call(token, "sendMessage", {
            "chat_id": chat,
            "text": f"Chỉ nhận file .docx tin tức — '{ten_file}' không phải .docx, bỏ qua."})
        return
    fd, tmp = tempfile.mkstemp(suffix=".docx")
    os.close(fd)
    try:
        if not tai_file(token, doc_att.get("file_id"), tmp):
            call(token, "sendMessage", {
                "chat_id": chat, "text": f"Tải file '{ten_file}' hỏng, gửi lại giúp tao."})
            return
        noi_dung = docx_text.trich(tmp, max_chars=JAYLAM_MAX_CHARS)
        if not noi_dung:
            call(token, "sendMessage", {
                "chat_id": chat,
                "text": f"Không đọc được nội dung '{ten_file}' (file rỗng hoặc hỏng)."})
            return
        if luu_tin_jaylam(chat, ten_nguoi, ten_file, noi_dung):
            call(token, "sendMessage", {
                "chat_id": chat,
                "text": (f"Đã nhận: {ten_file} ({len(noi_dung)} ký tự) — "
                         "sẽ gộp vào bản tổng hợp cuối ngày.")})
        else:
            call(token, "sendMessage", {
                "chat_id": chat,
                "text": f"Đã đọc '{ten_file}' nhưng lưu hỏng — báo lại cho Huy giúp tao."})
    finally:
        pathlib.Path(tmp).unlink(missing_ok=True)


def doc(token):
    cho_phep = chats_cho_phep()
    if not cho_phep:
        print("Thiếu TELEGRAM_CHAT_ID — không biết ai được phép hỏi.", file=sys.stderr)
        return 1

    r = call(token, "getUpdates", {"timeout": 0, "allowed_updates": ["message"]})
    if not r.get("ok"):
        print(f"getUpdates lỗi: {r.get('description')}", file=sys.stderr)
        return 1
    updates = r.get("result") or []
    if not updates:
        print("Không có tin nhắn mới.")
        return 10

    # Xác nhận NGAY (xem docstring): offset = id cuối + 1 xoá cả lô khỏi hàng đợi Telegram.
    last = max(u["update_id"] for u in updates)
    call(token, "getUpdates", {"offset": last + 1, "limit": 1, "timeout": 0})

    bay_gio = datetime.datetime.now(datetime.timezone.utc).timestamp()
    hoi, bo_la, bo_cu = [], 0, 0
    for u in updates:
        m = u.get("message") or {}
        chat = str((m.get("chat") or {}).get("id", ""))
        doc_att = m.get("document")
        if doc_att and chat:
            if chat not in cho_phep:
                bo_la += 1
                continue
            xu_ly_tin_jaylam(token, chat, m, doc_att)
            continue
        text = (m.get("text") or "").strip()
        if not text or not chat:
            continue
        if chat not in cho_phep:
            bo_la += 1
            continue
        if bay_gio - float(m.get("date", 0)) > MAX_AGE_PHUT * 60:
            bo_cu += 1
            # Bỏ thì phải NÓI. Trước đây chỉ in stderr vào log Actions — người hỏi ngồi chờ
            # một câu trả lời không bao giờ tới, y hệt kiểu hỏng mà cả repo này chống lại.
            gio = int((bay_gio - float(m.get("date", 0))) / 3600)
            call(token, "sendMessage", {
                "chat_id": chat,
                "text": (f"Câu này gửi {gio} tiếng trước, quá cũ nên tao bỏ qua — hỏi lại giúp tao.\n"
                         "(Bot chạy theo lịch GitHub, có lúc bị dồn tới 2 tiếng mới tới lượt.)"),
                "disable_web_page_preview": True})
            continue
        if text.startswith("/start"):
            continue
        # Xử lý NGAY trong bước --doc (rẻ, ~15 giây) chứ không đẩy sang `claude -p`: xoá tin
        # là việc cơ học, không cần suy nghĩ, và bắt Huy chờ 1-3 phút cài Claude Code chỉ để
        # xoá một tin rác thì vô lý.
        if text.startswith("/xoa"):
            xu_ly_xoa(token, m, chat)
            continue
        hoi.append({"chat": chat, "text": text,
                    "ten": (m.get("from") or {}).get("first_name", "")})

    if bo_la:
        print(f"Bỏ {bo_la} tin nhắn từ chat NGOÀI danh sách trắng.", file=sys.stderr)
    if bo_cu:
        print(f"Bỏ {bo_cu} tin nhắn cũ hơn {MAX_AGE_PHUT} phút.", file=sys.stderr)
    if not hoi:
        print("Không có câu hỏi hợp lệ.")
        return 10

    # Nhiều câu liên tiếp từ cùng một người: gộp thành một lượt hỏi, trả lời một lần.
    gop, ten_theo_chat = {}, {}
    for h in hoi:
        gop.setdefault(h["chat"], []).append(h["text"])
        if h.get("ten"):
            ten_theo_chat[h["chat"]] = h["ten"]
    ket = [{"chat": c, "ten": ten_theo_chat.get(c, ""), "text": "\n".join(t),
            "lich_su": lich_su_gan_day(c)}
           for c, t in gop.items()]

    pathlib.Path(QUESTIONS).write_text(
        json.dumps(ket, ensure_ascii=False, indent=2), encoding="utf-8")
    # ⚠️ CHỈ in chat id + độ dài, KHÔNG in nội dung — stdout đi vào log Actions của một repo
    # public (xem docstring đầu file). Huy vẫn đọc được đầy đủ qua bản chuyển tiếp Telegram.
    print(f"Có {len(ket)} lượt hỏi:")
    for k in ket:
        print(f"  [chat …{k['chat'][-4:]}] {len(k['text'])} ký tự")
    return 0


def gui(token, chat, noi_dung):
    """Gửi text thường (không parse_mode) — câu trả lời của Claude là markdown tự do,
    ép parse_mode HTML/Markdown sẽ khiến Telegram từ chối cả tin khi gặp ký tự lạ."""
    con = noi_dung.strip()
    if not con:
        return 0
    phan = []
    while con:
        if len(con) <= MAX_LEN:
            phan.append(con)
            break
        # Cắt ở lần xuống dòng gần nhất để không đứt giữa câu.
        cat = con.rfind("\n", 0, MAX_LEN)
        if cat < MAX_LEN // 2:
            cat = MAX_LEN
        phan.append(con[:cat])
        con = con[cat:].lstrip("\n")
    for p in phan:
        r = call(token, "sendMessage",
                 {"chat_id": chat, "text": p, "disable_web_page_preview": True})
        if not r.get("ok"):
            print(f"sendMessage lỗi: {r.get('description')}", file=sys.stderr)
            return 1
    print(f"Đã gửi {len(phan)} tin nhắn tới {chat}")
    return 0


def chuyen_tiep_cho_chu(token, chat_goc, tra_loi):
    """Gửi bản sao (câu hỏi + câu trả lời) về chat của Huy khi người hỏi KHÔNG phải Huy.

    Gắn vào chính `--tra-loi` chứ không tách thành lệnh riêng: Claude gọi `--tra-loi` để
    trả lời, nên chuyển tiếp xảy ra tự động: không có đường nào trả lời mà quên chuyển tiếp.
    Hỏng ở bước này KHÔNG được làm hỏng việc trả lời — bọc try/except, chỉ log.
    """
    chu = chat_chu()
    if not chu or chat_goc == chu:
        return
    try:
        ten = ""
        try:
            for q in json.loads(pathlib.Path(QUESTIONS).read_text(encoding="utf-8")):
                if q.get("chat") == chat_goc:
                    ten, cau_hoi = q.get("ten", ""), q.get("text", "")
                    break
            else:
                cau_hoi = "(không đọc được câu hỏi gốc)"
        except Exception:
            cau_hoi = "(không đọc được câu hỏi gốc)"
        nhan = f"{ten} (…{chat_goc[-4:]})" if ten else f"chat …{chat_goc[-4:]}"
        ban_sao = (f"📋 BẢN SAO — {nhan} vừa hỏi bot:\n\n"
                   f"❓ {cau_hoi}\n\n"
                   f"💬 Tao trả lời:\n{tra_loi}")
        gui(token, chu, ban_sao)
    except Exception as e:
        print(f"[chuyển tiếp] hỏng, bỏ qua: {e}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", action="store_true", help="đọc câu hỏi mới")
    ap.add_argument("--tra-loi", metavar="FILE", help="gửi nội dung file về chat")
    ap.add_argument("--bao", metavar="TEXT", help="gửi một dòng thông báo")
    ap.add_argument("--bao-tat-ca", metavar="TEXT",
                    help="gửi một dòng thông báo tới MỌI chat đang có câu hỏi chờ "
                         "(đọc /tmp/tg-questions.json) — dùng trong workflow để khỏi heredoc")
    ap.add_argument("--chat", help="chat id nhận (bắt buộc với --tra-loi/--bao)")
    args = ap.parse_args()

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("Thiếu TELEGRAM_BOT_TOKEN.", file=sys.stderr)
        return 1

    if args.doc:
        return doc(token)
    if args.bao_tat_ca:
        try:
            qs = json.loads(pathlib.Path(QUESTIONS).read_text(encoding="utf-8"))
        except Exception as e:
            # Không có file = không có ai đang chờ. Không phải lỗi.
            print(f"Không đọc được {QUESTIONS} ({e}) — không gửi cho ai.", file=sys.stderr)
            return 0
        cho_phep = chats_cho_phep()
        for q in qs:
            if q.get("chat") in cho_phep:
                gui(token, q["chat"], args.bao_tat_ca)
        return 0
    if args.tra_loi or args.bao:
        if not args.chat:
            print("Thiếu --chat.", file=sys.stderr)
            return 1
        if args.chat not in chats_cho_phep():
            print(f"chat {args.chat} không nằm trong danh sách trắng — từ chối gửi.",
                  file=sys.stderr)
            return 1
        noi_dung = (pathlib.Path(args.tra_loi).read_text(encoding="utf-8")
                    if args.tra_loi else args.bao)
        ma = gui(token, args.chat, noi_dung)
        # Chỉ chuyển tiếp với --tra-loi (câu trả lời thật), KHÔNG với --bao (tin "đang tra",
        # tin báo lỗi) — chuyển tiếp cả những cái đó thì chat của Huy thành bãi rác.
        if ma == 0 and args.tra_loi:
            chuyen_tiep_cho_chu(token, args.chat, noi_dung)
        return ma
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
