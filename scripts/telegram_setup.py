#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cài đặt bot Telegram cho Điểm Tin — CHẠY MỘT LẦN, TỰ HUY CHẠY TRONG TERMINAL.

    python3 scripts/telegram_setup.py

Làm giúp 4 việc: kiểm token sống không · tự dò chat_id (khỏi phải đi tìm) · gửi một tin
thử để chắc chắn tới nơi · đặt luôn hai GitHub secret bằng `gh` nếu máy có.

TRƯỚC KHI CHẠY, làm 2 bước trong Telegram (mất ~1 phút):
  1. Mở Telegram, tìm **@BotFather** → gõ `/newbot` → đặt tên và username (phải kết thúc
     bằng `bot`). BotFather trả về một token dạng `123456789:AAH...`.
  2. Tìm bot vừa tạo theo username → bấm **START** rồi nhắn cho nó một chữ bất kỳ.
     Bắt buộc: Telegram KHÔNG cho bot nhắn trước người chưa từng nhắn nó.

Muốn nhận trong NHÓM: thêm bot vào nhóm rồi nhắn một tin trong nhóm — script sẽ thấy cả
chat nhóm (id âm) và hỏi chọn.

⚠️ Token bot = quyền điều khiển bot. Đừng dán vào chat hay commit. Lộ thì `/revoke` trong
BotFather. Script này KHÔNG ghi token ra file nào.
"""
import getpass
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from tg_api import call  # noqa: E402


def main():
    print(__doc__)
    # getpass: token KHÔNG hiện trên màn hình và không vào lịch sử terminal. Bản đầu dùng
    # input() nên token in nguyên văn ra màn hình — đúng thứ không được để lộ.
    token = getpass.getpass("Dán token của @BotFather (gõ/dán xong Enter, "
                            "màn hình sẽ không hiện gì): ").strip()
    if not token or ":" not in token:
        print("Token không hợp lệ (phải có dạng 123456789:AAH...).", file=sys.stderr)
        return 1

    me = call(token, "getMe")
    if not me.get("ok"):
        print(f"❌ Token không dùng được: {me.get('description')}", file=sys.stderr)
        return 1
    print(f"✅ Bot: @{me['result'].get('username')} ({me['result'].get('first_name')})")

    up = call(token, "getUpdates")
    if not up.get("ok"):
        print(f"❌ getUpdates lỗi: {up.get('description')}", file=sys.stderr)
        return 1

    chats = {}
    for u in up.get("result", []):
        msg = u.get("message") or u.get("channel_post") or {}
        c = msg.get("chat") or {}
        if c.get("id"):
            ten = c.get("title") or " ".join(
                x for x in (c.get("first_name"), c.get("last_name")) if x) or "?"
            chats[str(c["id"])] = f"{ten} [{c.get('type')}]"

    if not chats:
        print("\n❌ Chưa thấy cuộc trò chuyện nào.")
        print("   → Mở Telegram, tìm bot theo username ở trên, bấm START rồi nhắn một chữ,")
        print("     sau đó chạy lại script này.")
        print("   (Telegram không cho bot nhắn trước người chưa từng nhắn nó — không có")
        print("    cách nào lách, kể cả biết sẵn số điện thoại.)")
        return 1

    print("\nCác nơi có thể nhận bản tin:")
    ids = list(chats)
    for i, cid in enumerate(ids, 1):
        print(f"  {i}. {cid}  —  {chats[cid]}")
    chon = input("Chọn số (nhiều nơi thì ngăn bằng dấu phẩy, Enter = tất cả): ").strip()
    if chon:
        try:
            ids = [ids[int(x.strip()) - 1] for x in chon.split(",")]
        except (ValueError, IndexError):
            print("Lựa chọn không hợp lệ.", file=sys.stderr)
            return 1
    chat_id = ",".join(ids)

    for cid in ids:
        r = call(token, "sendMessage", {
            "chat_id": cid,
            "text": "✅ <b>Điểm Tin Thế Giới</b> đã nối với Telegram.\n"
                    "Từ giờ bản tin sẽ gửi vào đây cùng lúc với email.",
            "parse_mode": "HTML"})
        print(("✅ Đã gửi tin thử tới " + cid) if r.get("ok")
              else f"❌ Gửi tới {cid} lỗi: {r.get('description')}")

    print(f"\nTELEGRAM_CHAT_ID = {chat_id}")
    if input("\nĐặt luôn 2 secret trên GitHub bằng `gh`? [Y/n] ").strip().lower() in ("", "y"):
        for name, val in (("TELEGRAM_BOT_TOKEN", token), ("TELEGRAM_CHAT_ID", chat_id)):
            p = subprocess.run(["gh", "secret", "set", name, "--body", val],
                               capture_output=True, text=True)
            print(f"  {name}: " + ("OK" if p.returncode == 0
                                   else f"LỖI {p.stderr.strip()[:120]}"))
        print("\nXong. Bản tin tối/sáng tiếp theo sẽ tự gửi qua Telegram.")
    else:
        print("\nTự đặt sau bằng:")
        print("  gh secret set TELEGRAM_BOT_TOKEN   # dán token khi được hỏi")
        print(f"  gh secret set TELEGRAM_CHAT_ID --body '{chat_id}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
