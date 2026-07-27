#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tạo SESSION STRING cho Telethon — CHẠY MỘT LẦN, TỰ HUY CHẠY TRONG TERMINAL.

    python3 scripts/telegram_login.py

Cần trước: vào https://my.telegram.org → API development tools → tạo app → lấy
**api_id** và **api_hash**. Script sẽ hỏi cả hai, rồi hỏi số điện thoại và mã OTP
Telegram gửi tới app.

⚠️ VÌ SAO HUY PHẢI TỰ CHẠY, KHÔNG PHẢI ZIM: bước này nhập số điện thoại + mã OTP +
(nếu bật) mật khẩu 2FA của chính tài khoản Telegram. Đó là thông tin đăng nhập — Zim
không nhập hộ, kể cả khi được bảo cứ nhập.

⚠️ SESSION STRING = QUYỀN ĐỌC TOÀN BỘ TÀI KHOẢN TELEGRAM. Ai có chuỗi đó là đăng nhập
được vào Telegram của mày mà không cần OTP. Vì vậy:
  - ĐỪNG dán nó vào chat, đừng commit vào repo (đã có .gitignore, nhưng đừng thử).
  - Cất vào GitHub secret bằng lệnh in ra ở cuối script.
  - Muốn huỷ: Telegram → Settings → Devices → chấm dứt phiên "Diem Tin harvest".
  - Chuỗi này chỉ cấp quyền ĐỌC vì script quét chỉ gọi API đọc lịch sử kênh, nhưng bản
    thân chuỗi thì không giới hạn được — mất là mất cả tài khoản.
"""
import sys

try:
    from telethon.sync import TelegramClient
    from telethon.sessions import StringSession
except ImportError:
    print("Thiếu telethon. Cài:  python3 -m pip install telethon", file=sys.stderr)
    sys.exit(1)


def main():
    print(__doc__)
    api_id = input("api_id (số, lấy ở my.telegram.org): ").strip()
    api_hash = input("api_hash: ").strip()
    if not api_id.isdigit() or not api_hash:
        print("api_id phải là số và api_hash không được rỗng.", file=sys.stderr)
        return 1

    # device_model đặt tên rõ để nhận ra trong danh sách thiết bị mà chấm dứt khi cần.
    with TelegramClient(StringSession(), int(api_id), api_hash,
                        device_model="Diem Tin harvest", system_version="macOS") as client:
        s = client.session.save()
        me = client.get_me()
        print(f"\n✅ Đăng nhập xong: {me.first_name} (@{me.username or 'không có username'})")
        print("\n=== SESSION STRING (KHÔNG dán cho ai, kể cả Zim) ===")
        print(s)
        print("\nCất vào GitHub secret bằng 3 lệnh sau (chạy trong repo):")
        print(f"  gh secret set TG_API_ID --body '{api_id}'")
        print("  gh secret set TG_API_HASH --body '<api_hash vừa nhập>'")
        print("  gh secret set TG_SESSION   # dán chuỗi trên khi được hỏi")
        print("\nDùng ở máy:  export TG_API_ID=... TG_API_HASH=... TG_SESSION='...'")
        print("  rồi  python3 scripts/telegram_harvest.py --mtproto")
    return 0


if __name__ == "__main__":
    sys.exit(main())
