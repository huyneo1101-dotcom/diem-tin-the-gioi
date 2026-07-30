#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gọi Telegram Bot API qua `curl` — dùng chung cho telegram_setup.py và send_telegram.py.

VÌ SAO KHÔNG DÙNG urllib (đổi 27/07/2026, gặp lỗi thật trên máy Huy):
    urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] self-signed certificate in certificate chain
Máy có thiết bị chèn cert ở giữa (proxy/antivirus). `curl` tin được vì đọc keychain macOS,
còn Python dùng bundle CA riêng nên trượt. Cài `certifi` KHÔNG cứu được ca này — cert chèn
không nằm trong bundle nào cả. Cả repo vốn đã đi bằng curl (harvest.py, telegram_harvest.py),
nên đây cũng là về đúng một đường.

TOKEN KHÔNG BAO GIỜ NẰM TRONG THAM SỐ DÒNG LỆNH: URL được đưa qua `curl -K -` (đọc cấu hình
từ stdin), nên `ps aux` của người khác trên cùng máy không đọc được token. Payload JSON đi qua
file tạm chmod 600 rồi xoá ngay.

Ở đây cũng đặt `kiem_cau_hinh()` — luật DUY NHẤT quyết định "thiếu secret thì êm hay đỏ", dùng
chung cho `send_telegram.py` và `canary.py`. Để mỗi script tự viết luật là chắc chắn lệch nhau,
mà lệch âm thầm: một kênh kêu còn kênh kia câm thì rất lâu mới phát hiện.
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile

API = "https://api.telegram.org/bot{t}/{m}"


def kiem_cau_hinh(token: str, chats, viec: str = "") -> "int | None":
    """Cổng secret Telegram. Trả `None` = đủ, chạy tiếp · `0` = tắt có chủ ý · `1` = GÃY, để job ĐỎ.

    VÌ SAO KHÔNG "thiếu secret thì luôn thoát êm exit 0" (chốt cũ, bỏ 27/07/2026):
    chốt đó chỉ bảo vệ ca **CHƯA CẤU HÌNH** — repo mới, chưa ai cắm secret lần nào, không có gì
    để hỏng. Repo này đã cắm cả hai secret lúc 07:13 ngày 27/07/2026, nên từ giờ nó không còn
    bảo vệ gì nữa mà chỉ CHE ca secret bị xoá · bot bị `/revoke` · gõ nhầm tên secret. Khi đó
    phiên 21:00/22:00 chạy XANH mà kênh câm — và **Telegram nay là kênh DUY NHẤT** (email tắt
    bằng `GUI_EMAIL='0'`), tức Huy mất trắng bản tin mà không một dấu hiệu nào. Cùng lớp lỗi bắt
    được ở app Rèn cùng ngày: `TELEGRAM_BOT_TOKEN` chưa từng đặt, run 30250807802 vẫn *success*
    trong 10 giây suốt.

    VÌ SAO KHÔNG CHỈ CHÉP LOGIC CỦA RÈN ("có secret này mà thiếu secret kia thì đỏ"): Rèn có BA
    secret nên còn suy được ý định từ những cái còn lại. Ở đây chỉ có HAI, và ca đáng sợ nhất là
    **mất sạch cả hai** — đúng cái ca mà luật của Rèn lại đọc thành "chưa cấu hình" rồi thoát êm.
    Nên ý định phải khai BẰNG LỜI, không suy từ secret:

        mặc định (không đặt gì)   -> Telegram BẮT BUỘC, thiếu secret là ĐỎ
        TELEGRAM_BAT_BUOC = '0'   -> kênh tắt CÓ CHỦ Ý, thoát êm exit 0

    Mặc định là "bắt buộc" chứ không phải "tuỳ" để quên đặt biến KHÔNG tạo ra vùng câm mới —
    quên thì kêu, mà kêu thì sửa được; câm thì không ai biết. Muốn tắt kênh (như đã tắt email)
    thì đặt `TELEGRAM_BAT_BUOC: '0'` cạnh `GUI_EMAIL: '0'` trong workflow.
    """
    thieu = ([] if token else ["TELEGRAM_BOT_TOKEN"]) + ([] if chats else ["TELEGRAM_CHAT_ID"])
    if not thieu:
        return None
    nhan = f" ({viec})" if viec else ""
    if os.environ.get("TELEGRAM_BAT_BUOC", "1").strip() == "0":
        print(f"TELEGRAM_BAT_BUOC=0 — kênh Telegram đang TẮT có chủ ý{nhan}, bỏ qua êm "
              f"(thiếu: {', '.join(thieu)}).", file=sys.stderr)
        return 0
    print(f"❌ CẤU HÌNH GÃY{nhan} — THIẾU secret: {', '.join(thieu)}\n"
          "   Telegram là kênh gửi DUY NHẤT nên đây là SỰ CỐ, không phải 'chưa cấu hình'.\n"
          "   Cắm lại:  python3 scripts/telegram_setup.py\n"
          "   Kiểm:     gh secret list -R huyneo1101-dotcom/diem-tin-the-gioi\n"
          "   Nếu CỐ Ý tắt kênh: đặt TELEGRAM_BAT_BUOC: '0' trong workflow.", file=sys.stderr)
    return 1


def _run(cfg: str, extra=None) -> dict:
    p = subprocess.run(
        ["curl", "-sS", "--compressed", "--max-time", "120", "-K", "-"] + (extra or []),
        input=cfg, capture_output=True, text=True)
    out = (p.stdout or "").strip()
    if not out:
        return {"ok": False, "description": (p.stderr or "curl không trả về gì").strip()[:300]}
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return {"ok": False, "description": f"phản hồi không phải JSON: {out[:200]}"}


def call(token: str, method: str, payload=None) -> dict:
    """Gọi một method của Bot API với payload JSON."""
    url = API.format(t=token, m=method)
    if not payload:
        return _run(f'url = "{url}"\n')
    fd, tmp = tempfile.mkstemp(suffix=".json")
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
        return _run(f'url = "{url}"\n'
                    'header = "Content-Type: application/json"\n'
                    f'data = "@{tmp}"\n')
    finally:
        pathlib.Path(tmp).unlink(missing_ok=True)


def send_document(token: str, chat_id: str, path: str, caption: str = "") -> dict:
    """sendDocument — để curl tự dựng multipart, khỏi phải bịa boundary bằng tay."""
    url = API.format(t=token, m="sendDocument")
    return _run(f'url = "{url}"\n',
                ["-F", f"chat_id={chat_id}", "-F", f"caption={caption}",
                 "-F", f"document=@{path}"])


def tai_file(token: str, file_id: str, dich: str) -> bool:
    """Tải file người dùng gửi cho bot (theo `file_id`) về đường dẫn `dich`.

    Hai bước — `getFile` trả `file_path` tạm thời, rồi tải qua endpoint file/ riêng — cả hai
    đi qua `curl -K -` (stdin) như `call()`, TOKEN KHÔNG NẰM TRONG ARGV (xem docstring đầu file).
    Bot API giới hạn 20MB cho `getFile`; tin tức .docx bình thường không chạm ngưỡng đó.
    """
    r = call(token, "getFile", {"file_id": file_id})
    file_path = (r.get("result") or {}).get("file_path") if r.get("ok") else None
    if not file_path:
        return False
    url = f"https://api.telegram.org/file/bot{token}/{file_path}"
    p = subprocess.run(
        ["curl", "-sS", "--max-time", "60", "-K", "-", "-o", dich],
        input=f'url = "{url}"\n', capture_output=True, text=True)
    if p.returncode != 0:
        return False
    try:
        return pathlib.Path(dich).stat().st_size > 0
    except OSError:
        return False
