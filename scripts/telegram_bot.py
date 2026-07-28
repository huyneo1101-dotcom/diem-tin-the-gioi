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
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from tg_api import call  # noqa: E402

QUESTIONS = "/tmp/tg-questions.json"
# Bỏ câu hỏi cũ hơn ngần này — tránh trả lời một câu Huy hỏi từ hôm qua khi bot vừa hồi sinh
# sau sự cố (Telegram giữ hàng đợi tới 24h).
MAX_AGE_PHUT = 60
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
        text = (m.get("text") or "").strip()
        chat = str((m.get("chat") or {}).get("id", ""))
        if not text or not chat:
            continue
        if chat not in cho_phep:
            bo_la += 1
            continue
        if bay_gio - float(m.get("date", 0)) > MAX_AGE_PHUT * 60:
            bo_cu += 1
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
    ket = [{"chat": c, "ten": ten_theo_chat.get(c, ""), "text": "\n".join(t)}
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
