#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NHÌN TRƯỚC rồi mới kích bot — chạy trên máy Mac, mỗi 60 giây.

    python3 scripts/nhin_truoc_kich_bot.py            # nhìn, có tin mới thì kích
    python3 scripts/nhin_truoc_kich_bot.py --kho      # chỉ nhìn và in ra, KHÔNG kích
    python3 scripts/nhin_truoc_kich_bot.py --luu-token  # dán token vào máy (chạy MỘT LẦN)

VÌ SAO CÓ FILE NÀY (Huy chốt 28/07/2026, sau khi hỏi "kích mỗi 1 phút có nhiều quá không"):
`cron: */5` của telegram-bot.yml bị GitHub bỏ gần hết mốc — đo thật, các lần chạy cách nhau
66–148 phút. Lớp vá đầu là LaunchAgent kích mù mỗi 5 phút; muốn xuống 1 phút thì thành 1.440
run/ngày, không tốn tiền (repo public) nhưng **chôn lấp tab Actions** — đúng cái công cụ dùng
để chẩn đoán khi bản tin hỏng — và đẻ một đống run `cancelled` do `concurrency`.

Cách này giữ độ trễ ~1 phút mà số run/ngày chỉ bằng **số lượt hỏi thật**: máy nhìn hàng đợi
Telegram trước, không có tin thì không kích gì.

⚠️ **`getUpdates` KHÔNG kèm `offset` chỉ NHÌN, không xoá hàng đợi.** Telegram chỉ coi là đã
nhận khi có ai đó gọi lại với `offset = id + 1` — việc đó do chính workflow làm. Nếu script
này lỡ xác nhận thì workflow sẽ thấy hàng đợi rỗng và câu hỏi mất hẳn. **Đừng bao giờ truyền
`offset` ở đây.**

⚠️ **Chống dội theo CẢ id LẪN thời gian.** Update chưa được workflow xác nhận thì phút sau nhìn
vẫn thấy — kích lại là thừa. Nhưng nếu chỉ nhớ id thì workflow chết giữa chừng sẽ làm câu hỏi
nằm lại mãi mà không ai kích nữa. Nên: id mới -> kích ngay; id cũ -> chỉ kích lại sau
`KICH_LAI_SAU_PHUT`.
"""
import argparse
import datetime
import json
import os
import pathlib
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from tg_api import call  # noqa: E402

GH = "/opt/homebrew/bin/gh"
REPO = "huyneo1101-dotcom/diem-tin-the-gioi"
WF = "telegram-bot.yml"

# Token + danh sách chat để NGOÀI repo (repo này public), chmod 600. Cùng kiểu .dt-bot-key.
FILE_CAU_HINH = pathlib.Path(os.environ.get("TG_BOT_FILE", "/Users/Huy/Claude/.tg-bot.json"))
SO = pathlib.Path("/tmp/tg-nhin-truoc.json")
LOG_LOI_LIEN_TIEP = 5          # bấy nhiêu lần lỗi liên tiếp thì bật notification macOS
KICH_LAI_SAU_PHUT = 10
KICH_MU_MOI_PHUT = 5           # khi chưa có token: lùi về kích mù, giãn như LaunchAgent đời đầu
# Khớp MAX_AGE_PHUT của telegram_bot.py: tin quá cũ thì workflow cũng bỏ, kích là phí một run.
MAX_AGE_PHUT = 360


def log(msg):
    print(f"[{datetime.datetime.now():%d/%m %H:%M:%S}] {msg}", flush=True)


def bao_dong(msg):
    """Notification macOS — chỉ thấy khi Huy ở máy, nhưng script này vốn chỉ chạy khi máy thức."""
    subprocess.run(["osascript", "-e",
                    f'display notification "{msg}" with title "Bot Điểm Tin"'],
                   capture_output=True)


def doc_cau_hinh():
    try:
        d = json.loads(FILE_CAU_HINH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "", []
    return d.get("token", "").strip(), [str(c) for c in (d.get("chats") or [])]


def doc_so():
    try:
        return json.loads(SO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"id": 0, "luc": 0, "loi": 0}


def ghi_so(d):
    try:
        SO.write_text(json.dumps(d), encoding="utf-8")
    except OSError:
        pass


def kich() -> bool:
    p = subprocess.run([GH, "workflow", "run", WF, "--repo", REPO],
                       capture_output=True, text=True, timeout=120)
    if p.returncode == 0:
        return True
    log(f"   ❌ gh workflow run hỏng: {(p.stderr or p.stdout).strip()[:160]}")
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kho", action="store_true", help="chỉ nhìn, không kích")
    ap.add_argument("--luu-token", action="store_true", help="dán token + chat id vào máy")
    args = ap.parse_args()

    if args.luu_token:
        return luu_token()

    token, chats = doc_cau_hinh()
    if not token:
        # LÙI VỀ CÁCH CŨ, đừng chết hẳn: chưa dán token thì kích mù như LaunchAgent đời đầu,
        # nhưng giãn ra `KICH_MU_MOI_PHUT` để không thành 1.440 run/ngày. Bot vẫn chạy, chỉ
        # kém tối ưu — khác hẳn với việc im lặng không kích gì cho tới lúc Huy rảnh dán token.
        so = doc_so()
        if (time.time() - so.get("luc", 0)) / 60 < KICH_MU_MOI_PHUT:
            return 0
        log(f"Chưa có token trong {FILE_CAU_HINH} — tạm KÍCH MÙ mỗi {KICH_MU_MOI_PHUT} phút. "
            f"Dán token bằng: python3 {pathlib.Path(__file__).resolve()} --luu-token")
        if args.kho:
            return 0
        if kich():
            so["luc"] = time.time()
            ghi_so(so)
        return 0

    r = call(token, "getUpdates", {"timeout": 0, "allowed_updates": ["message"]})
    so = doc_so()
    if not r.get("ok"):
        so["loi"] = so.get("loi", 0) + 1
        ghi_so(so)
        log(f"getUpdates lỗi ({so['loi']} lần liên tiếp): {r.get('description')}")
        if so["loi"] == LOG_LOI_LIEN_TIEP:
            bao_dong(f"Không nhìn được hàng đợi Telegram {LOG_LOI_LIEN_TIEP} lần liên tiếp")
        return 1
    so["loi"] = 0

    bay_gio = time.time()
    moi = []
    for u in r.get("result") or []:
        m = u.get("message") or {}
        # PHẢI ĐẾM CẢ FILE, KHÔNG CHỈ TEXT (vá 30/07/2026). Bản đầu chỉ xét `text` nên script
        # MÙ HOÀN TOÀN với `.docx` Jay Lâm gửi — mà `telegram_bot.py:388` thì xử lý `document`
        # đầy đủ. Hai nơi cùng quyết định "update này có đáng xử lý không" mà mỗi nơi một luật:
        # bên workflow nhận, bên nhìn-trước bỏ qua ⇒ file phải nằm chờ cron GitHub (đo thật:
        # các lần chạy cách nhau 66-148 phút). Tối 30/07 file tới trước bản tin ~20 phút mà
        # không lớp tự động nào kích, nên nó lỡ mất bản tin tối — hai file vào được hôm đó đều
        # do nguyên nhân khác: một cái ăn ké lượt kích do Huy nhắn text, một cái do kích tay.
        la_file = bool(m.get("document"))
        if not la_file and not (m.get("text") or "").strip():
            continue
        if chats and str((m.get("chat") or {}).get("id", "")) not in chats:
            continue        # người lạ nhắn -> workflow cũng bỏ, kích là phí một run
        # File KHÔNG xét tuổi — khớp đúng nhánh `document` của workflow, nhánh đó cũng không
        # xét `MAX_AGE_PHUT`. Siết ở đây là dựng lại đúng cảnh lệch luật vừa vá: file gửi đêm
        # lúc máy ngủ, sáng mở máy đã quá 360 phút ⇒ script lặng lẽ bỏ, trong khi workflow vẫn
        # nhận được. Hướng lệch phải là KÍCH THỪA một run, không phải mất một file.
        if not la_file and bay_gio - float(m.get("date", 0)) > MAX_AGE_PHUT * 60:
            continue
        moi.append(u["update_id"])

    if not moi:
        ghi_so(so)
        return 0            # im lặng — đây là 99% số lần chạy, đừng làm phình log

    lon_nhat = max(moi)
    cu = so.get("id", 0)
    lau = (bay_gio - so.get("luc", 0)) / 60
    if lon_nhat <= cu and lau < KICH_LAI_SAU_PHUT:
        ghi_so(so)          # đã kích cho lô này rồi, workflow đang xử lý — đừng kích chồng
        return 0

    vi_sao = "tin mới" if lon_nhat > cu else f"lô cũ chưa được xử lý sau {lau:.0f} phút"
    log(f"Có {len(moi)} tin đang chờ ({vi_sao}) -> kích {WF}")
    if args.kho:
        log("   --kho: không kích.")
        return 0
    if kich():
        log("   ✅ đã kích")
        so["id"], so["luc"] = lon_nhat, bay_gio
        ghi_so(so)
        return 0
    ghi_so(so)              # KHÔNG cập nhật mốc: lần sau phải thử lại
    return 1


def luu_token() -> int:
    """Dán token vào máy. Huy tự chạy — Zim không nhập hộ bí mật."""
    import getpass
    print("Token này CHỈ dùng để NHÌN hàng đợi (getUpdates), không gửi gì.")
    print("Lấy lại token: @BotFather -> /mybots -> chọn bot -> API Token.\n")
    # getpass: token không hiện lên màn hình, không vào lịch sử terminal. Bài học 27/07 —
    # bản đầu dùng input() nên token in nguyên văn, ảnh chụp gửi đi là lộ, phải /revoke.
    token = getpass.getpass("Dán token (gõ xong Enter, màn hình sẽ không hiện gì): ").strip()
    if not token:
        print("Không có gì được dán.", file=sys.stderr)
        return 1
    r = call(token, "getMe")
    if not r.get("ok"):
        print(f"Token không dùng được: {r.get('description')}", file=sys.stderr)
        return 1
    ten = (r.get("result") or {}).get("username", "?")
    print(f"✅ Token đúng — bot @{ten}")

    print("\nDán các chat id được phép (ngăn bằng dấu phẩy).")
    print("Để trống = nhận mọi chat (không nên: người lạ nhắn cũng làm tốn một lần kích).")
    chats = [c.strip() for c in input("chat id: ").split(",") if c.strip()]

    FILE_CAU_HINH.write_text(json.dumps({"token": token, "chats": chats}, indent=2),
                             encoding="utf-8")
    FILE_CAU_HINH.chmod(0o600)
    print(f"\n✅ Đã lưu {FILE_CAU_HINH} (chmod 600, NGOÀI repo vì repo public).")
    print("Thử ngay:  python3 " + str(pathlib.Path(__file__).resolve()) + " --kho")
    return 0


if __name__ == "__main__":
    sys.exit(main())
