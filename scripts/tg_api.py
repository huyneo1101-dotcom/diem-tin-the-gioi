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
"""
import json
import os
import pathlib
import subprocess
import tempfile

API = "https://api.telegram.org/bot{t}/{m}"


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
