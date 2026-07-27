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

GỬI CHO NGƯỜI KHÁC NỮA — chọn 1 trong 3, rồi chạy lại script này:
  a) **Từng người**: người đó tự mở `t.me/<username bot>` và bấm START. Không có đường nào
     khác — Telegram CẤM bot nhắn trước người chưa từng nhắn nó, biết số điện thoại cũng
     không gửi được. Chạy lại script, họ sẽ hiện trong danh sách, chọn nhiều số ngăn bằng
     dấu phẩy.
  b) **NHÓM** (gọn nhất khi có vài người): tạo nhóm → thêm bot vào → **nhắn `/start` trong
     nhóm**. ⚠️ Phải là `/start` hoặc câu có @tên_bot: bot trong nhóm mặc định bật "privacy
     mode", tin thường nó KHÔNG nhận nên script sẽ không thấy nhóm đâu. Sau này thêm/bớt
     người chỉ việc mời vào nhóm, không phải sửa secret.
  c) **KÊNH** (phát một chiều cho nhiều người): tạo kênh → thêm bot làm **admin** (phải có
     quyền đăng bài) → đăng một tin bất kỳ trong kênh. Người đọc chỉ cần bấm Join theo link
     mời, không phải tương tác gì với bot.

Script gộp mọi nơi đã chọn vào `TELEGRAM_CHAT_ID` (ngăn bằng dấu phẩy) — bản tin gửi tới
tất cả. Chạy lại script là GHI ĐÈ secret cũ, nên lần nào cũng chọn ĐỦ mọi nơi cần nhận.

⚠️ Token bot = quyền điều khiển bot. Đừng dán vào chat hay commit. Lộ thì `/revoke` trong
BotFather. Script này KHÔNG ghi token ra file nào.
"""
import getpass
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from tg_api import call  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
REPO = "huyneo1101-dotcom/diem-tin-the-gioi"


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
        u = me["result"].get("username")
        print("\n❌ Chưa thấy cuộc trò chuyện nào.")
        print(f"   → Mở https://t.me/{u} → bấm START → chạy lại script này.")
        print("   (Telegram không cho bot nhắn trước người chưa từng nhắn nó — không có")
        print("    cách nào lách, kể cả biết sẵn số điện thoại.)")
        print("   Nếu định gửi vào NHÓM: đã thêm bot vào nhóm thì phải nhắn `/start` trong")
        print(f"   nhóm (hoặc câu có @{u}) — bot bật privacy mode nên KHÔNG thấy tin thường.")
        print("   Nếu định gửi vào KÊNH: bot phải là ADMIN và kênh phải có ít nhất 1 bài đăng.")
        return 1

    print("\nCác nơi có thể nhận bản tin:")
    ids = list(chats)
    for i, cid in enumerate(ids, 1):
        print(f"  {i}. {cid}  —  {chats[cid]}")
    print("  (Thiếu người/nhóm nào? Bảo họ bấm START với bot — hoặc nhắn `/start` trong nhóm")
    print("   — rồi chạy lại script. Xem đầu file để biết cách cho nhóm và kênh.)")
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
        ok = True
        for name, val in (("TELEGRAM_BOT_TOKEN", token), ("TELEGRAM_CHAT_ID", chat_id)):
            # ⚠️ cwd=ROOT là BẮT BUỘC: `gh` dò repo từ thư mục hiện tại. Script này thường
            # được chạy bằng đường dẫn tuyệt đối từ thư mục khác (~), khi đó gh không biết
            # repo nào và fail. Đã vấp thật 27/07 — secret im lặng không được đặt.
            p = subprocess.run(["gh", "secret", "set", name, "--body", val],
                               capture_output=True, text=True, cwd=str(ROOT))
            if p.returncode == 0:
                print(f"  {name}: OK")
            else:
                ok = False
                print(f"  {name}: LỖI — {(p.stderr or p.stdout).strip()[:200]}")
        if ok:
            print("\n✅ Xong. Kiểm lại bằng:  gh secret list --repo "
                  "huyneo1101-dotcom/diem-tin-the-gioi | grep TELEGRAM")
            print("Bản tin tối/sáng tiếp theo sẽ tự gửi qua Telegram, và bot trả lời được câu hỏi.")
        else:
            print("\n⚠️ Có secret chưa đặt được — xem lỗi ở trên. Đặt tay bằng lệnh dưới.")
            print(f"  gh secret set TELEGRAM_BOT_TOKEN --repo {REPO}   # dán token khi được hỏi")
            print(f"  gh secret set TELEGRAM_CHAT_ID --repo {REPO} --body '{chat_id}'")
    else:
        print("\nTự đặt sau bằng:")
        print(f"  gh secret set TELEGRAM_BOT_TOKEN --repo {REPO}   # dán token khi được hỏi")
        print(f"  gh secret set TELEGRAM_CHAT_ID --repo {REPO} --body '{chat_id}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
