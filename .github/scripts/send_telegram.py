#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gửi bản tin vừa quét qua Telegram Bot API — song song với email, KHÔNG thay email.

Chạy:
    TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=... python3 .github/scripts/send_telegram.py
    DRY_RUN=1 python3 .github/scripts/send_telegram.py     # in ra màn hình, không gửi

Biến môi trường:
    TELEGRAM_BOT_TOKEN  bắt buộc (trừ DRY_RUN)  — token @BotFather cấp
    TELEGRAM_CHAT_ID    bắt buộc (trừ DRY_RUN)  — id người/nhóm/kênh nhận; nhiều nơi thì
                        ngăn bằng dấu phẩy ("123456789,-1001234567890")
    DOCX_PATH           tuỳ chọn — đường dẫn .docx đính kèm (workflow truyền vào; rỗng thì
                        script tự gọi make_docx.py để dựng)
    SUBJECT_TAG         tuỳ chọn — tiền tố gắn trước tiêu đề (vd "[TEST] ")
    DRY_RUN             =1 thì chỉ in, không gọi API

VÌ SAO KHÔNG COPY LOGIC CHỌN TIN: script này `import` thẳng `make_docx.py` để dùng lại
`extract_data` / `pick_items` / `build_sections`. Bản tin trong Telegram vì thế LUÔN gồm
đúng bộ tin của file .docx đính kèm email — kể cả khi make_docx sửa cách chọn tin về sau
(bẫy commit nhiều lần / lô neo ngày cũ, xem CLAUDE.md). Copy code là cách chắc chắn để
hai bên lệch nhau sau vài tháng.

CHỐT AN TOÀN (bắt chước `send-email.js`): thiếu file · JSON lỗi · `date` trong
`logs/scan-gaps.json` ≠ `DATA.generatedAt` → BỎ mục "Chủ đề thiếu", chỉ log, KHÔNG làm
vỡ tin nhắn. Bản tin quan trọng hơn phần phụ chú.
"""
import datetime
import html
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import urllib.request
import zoneinfo

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
VN = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")
API = "https://api.telegram.org/bot{token}/{method}"

# Telegram chặn message > 4096 ký tự. Chừa biên cho thẻ HTML bị đếm nguyên văn.
MAX_LEN = 3800
# Trần số sự kiện trong bản tin sáng — xem chú thích trong build_morning_messages.
MORNING_MAX_EVENTS = 12


def _load_make_docx():
    """Nạp make_docx.py như module (tên file không phải identifier hợp lệ để import thường)."""
    path = pathlib.Path(__file__).resolve().parent / "make_docx.py"
    spec = importlib.util.spec_from_file_location("make_docx", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def slot_label(now=None):
    """SÁNG / TỐI theo giờ VN — cùng ngưỡng 14h với `send-email.js` và ô khoá `state.py`.

    Đổi lịch quét thì phải xem lại ngưỡng này ở CẢ BA nơi.
    """
    now = now or datetime.datetime.now(VN)
    return "SÁNG" if now.hour < 14 else "TỐI"


def read_gaps(generated_at):
    """Mục 'Chủ đề thiếu và lý do'. Trả [] khi có bất kỳ nghi ngờ nào (xem docstring)."""
    p = ROOT / "logs" / "scan-gaps.json"
    try:
        g = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[gaps] bỏ mục — không đọc được {p}: {e}", file=sys.stderr)
        return []
    if g.get("date") != generated_at:
        print(f"[gaps] bỏ mục — date {g.get('date')!r} ≠ generatedAt {generated_at!r} "
              "(chống gửi lý do của phiên trước)", file=sys.stderr)
        return []
    topics = g.get("topics") or []
    if not isinstance(topics, list) or not topics:
        print("[gaps] bỏ mục — topics rỗng", file=sys.stderr)
        return []
    return topics


def esc(s):
    return html.escape(str(s or ""), quote=False)


def build_messages(sections, generated_at, total, gaps, tag=""):
    """Dựng danh sách message HTML, mỗi cái ≤ MAX_LEN. Cắt theo TIN, không cắt giữa tin."""
    try:
        y, m, d = generated_at.split("-")
        ngay = f"{int(d)}/{int(m)}"
    except Exception:
        ngay = generated_at

    head = (f"{esc(tag)}📰 <b>Điểm Tin Thế Giới BUỔI {slot_label()} {esc(ngay)}</b> "
            f"({total} tin)")

    blocks = [head]
    idx = 0
    for name, items in sections:
        if not items:
            continue
        idx += 1
        blocks.append(f"\n<b>{idx}. {esc(name)}</b>")
        for it in items:
            title = esc(it.get("title") or it.get("summary") or "")
            url = it.get("sourceUrl") or ""
            src = esc(it.get("sourceName") or "")
            if url:
                line = f"• <a href=\"{esc(url)}\">{title}</a>"
            else:
                line = f"• {title}"
            if src:
                line += f" <i>— {src}</i>"
            blocks.append(line)

    if gaps:
        # `thieu` là cờ tường minh; không có thì suy từ count < min (giống send-email.js).
        thieu = [t for t in gaps
                 if (t["thieu"] if t.get("thieu") is not None
                     else (t.get("count", 0) < t.get("min", 0)))]
        blocks.append("\n<b>⚠️ Chủ đề thiếu và lý do</b>")
        if not thieu:
            blocks.append("• Không chủ đề nào thiếu.")
        for t in thieu:
            blocks.append(f"• <b>{esc(t.get('name'))}</b> "
                          f"({t.get('count', '?')}/{t.get('target', '?')}): "
                          f"{esc(t.get('reason') or 'không ghi lý do')}")

    # Gộp block thành message ≤ MAX_LEN, không cắt giữa một dòng tin.
    msgs, cur = [], ""
    for b in blocks:
        piece = (b if not cur else "\n" + b)
        if len(cur) + len(piece) > MAX_LEN:
            msgs.append(cur)
            cur = b
        else:
            cur += piece
    if cur:
        msgs.append(cur)
    return msgs


def build_morning_messages(pl, tag=""):
    """Message cho bản tin SÁNG (sự kiện & tập trận) — dựng từ payload của send-morning-email.js.

    KHÔNG tự diff lại DATA: `send-morning-email.js` đã quyết định "hôm nay có gì mới" và ghi
    ra file; đọc lại file đó thì gate gửi của Telegram luôn khớp email, không có cảnh một
    kênh gửi còn kênh kia im.
    """
    bits = " + ".join(pl.get("subjBits") or []) or "cập nhật mới"
    blocks = [f"{esc(tag)}🎖️ <b>Sự kiện &amp; Tập trận {esc(pl.get('ddmm'))}</b> — {esc(bits)}"]

    # Cap số sự kiện: email dài thì cuộn, Telegram dài thì thành CHỤC thông báo liên tiếp
    # (đo thật 27/07: 22 sự kiện -> 6 tin nhắn). Phần bị cắt PHẢI nói ra, không im lặng —
    # đọc thấy 12 sự kiện mà tưởng đó là tất cả thì tệ hơn là biết mình đang xem bản rút gọn.
    all_events = pl.get("events") or []
    events = all_events[:MORNING_MAX_EVENTS]
    for ev in events:
        nhan = "Tập trận" if ev.get("kind") == "ex" else "Ngoại giao"
        moi = " · <b>MỚI</b>" if ev.get("isNewEvent") else ""
        meta = " · ".join(x for x in (ev.get("dates"), ev.get("location")) if x)
        blocks.append(f"\n<b>[{nhan}]</b>{moi} {esc(ev.get('name'))}"
                      + (f"\n<i>{esc(meta)}</i>" if meta else ""))
        for it in ev.get("items") or []:
            url = it.get("sourceUrl") or ""
            t = esc(it.get("title"))
            blocks.append(f"• <a href=\"{esc(url)}\">{t}</a>" if url else f"• {t}")

    if len(all_events) > len(events):
        con = len(all_events) - len(events)
        blocks.append(f"\n<i>… và {con} sự kiện/tập trận nữa — xem đầy đủ trên trang.</i>")
        print(f"[morning] cắt bớt {con}/{len(all_events)} sự kiện cho vừa Telegram",
              file=sys.stderr)

    w = pl.get("weekly")
    if w:
        blocks.append(f"\n📊 <b>Báo cáo tuần {esc(w.get('weekStart'))}–{esc(w.get('weekEnd'))}</b>")
        for c in w.get("countries") or []:
            pts = " · ".join(esc(p) for p in (c.get("points") or []))
            blocks.append(f"• {esc(c.get('flag'))} <b>{esc(c.get('name'))}</b>: {pts}")

    anas = pl.get("analyses") or []
    if anas:
        blocks.append("\n🏛️ <b>Think-tank</b>")
        for a in anas:
            t = esc(a.get("title"))
            url = a.get("url") or ""
            line = f"• <a href=\"{esc(url)}\">{t}</a>" if url else f"• {t}"
            if a.get("outlet"):
                line += f" <i>— {esc(a['outlet'])}</i>"
            blocks.append(line)
            if a.get("takeaway"):
                blocks.append(f"  <i>{esc(a['takeaway'])}</i>")

    feats = pl.get("features") or []
    if feats:
        blocks.append("\n🆕 <b>Mới trên web</b>")
        for f in feats:
            blocks.append(f"• <b>{esc(f.get('title'))}</b>: {esc(f.get('desc'))}")

    tip = pl.get("tip")
    if tip:
        duong = (pl.get("webUrl", "") + tip.get("path", "")) if tip.get("path") else ""
        blocks.append(f"\n💡 <b>{esc(tip.get('title'))}</b>\n{esc(tip.get('desc'))}"
                      + (f"\n{esc(duong)}" if duong else ""))

    if pl.get("webUrl"):
        blocks.append(f"\n<a href=\"{esc(pl['webUrl'])}\">Mở trang Điểm Tin</a>")

    msgs, cur = [], ""
    for b in blocks:
        piece = (b if not cur else "\n" + b)
        if len(cur) + len(piece) > MAX_LEN:
            msgs.append(cur)
            cur = b
        else:
            cur += piece
    if cur:
        msgs.append(cur)
    return msgs


def api(token, method, payload=None, files=None):
    url = API.format(token=token, method=method)
    if files is None:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8"))

    # multipart/form-data cho sendDocument
    boundary = "----dtwgTelegramBoundary7e3f"
    body = b""
    for k, v in (payload or {}).items():
        body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n"
                 f"{v}\r\n").encode("utf-8")
    for field, path in files.items():
        p = pathlib.Path(path)
        body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"; "
                 f"filename=\"{p.name}\"\r\n"
                 "Content-Type: application/octet-stream\r\n\r\n").encode("utf-8")
        body += p.read_bytes() + b"\r\n"
    body += f"--{boundary}--\r\n".encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))


def send_all(token, chats, msgs, docx="", caption=""):
    for chat in chats:
        for m in msgs:
            r = api(token, "sendMessage", {
                "chat_id": chat, "text": m, "parse_mode": "HTML",
                "disable_web_page_preview": True,
            })
            if not r.get("ok"):
                print(f"LỖI sendMessage tới {chat}: {r}", file=sys.stderr)
                return 1
        if docx:
            r = api(token, "sendDocument", {"chat_id": chat, "caption": caption},
                    {"document": docx})
            if not r.get("ok"):
                print(f"LỖI sendDocument tới {chat}: {r}", file=sys.stderr)
                return 1
        print(f"Đã gửi {len(msgs)} message{' + file .docx' if docx else ''} tới {chat}")
    return 0


def run_morning(token, chats, tag, dry):
    """Bản tin SÁNG — sự kiện & tập trận. Đọc payload do send-morning-email.js ghi ra."""
    path = os.environ.get("TELEGRAM_PAYLOAD", "/tmp/morning-telegram.json")
    try:
        pl = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except Exception as e:
        # Không có payload = email sáng đã quyết định KHÔNG gửi (không có gì mới), hoặc
        # workflow chạy hụt bước. Cả hai trường hợp đều im lặng, không phải lỗi.
        print(f"Không đọc được payload {path} ({e}) — không gửi Telegram sáng.", file=sys.stderr)
        return 0
    msgs = build_morning_messages(pl, tag)
    if dry:
        print(f"=== DRY_RUN (sáng) — {len(msgs)} message ===")
        for i, m in enumerate(msgs, 1):
            print(f"\n----- message {i}/{len(msgs)} ({len(m)} ký tự) -----")
            print(m)
        return 0
    return send_all(token, chats, msgs)


def main():
    dry = os.environ.get("DRY_RUN") == "1"
    morning = "--morning" in sys.argv
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chats = [c.strip() for c in os.environ.get("TELEGRAM_CHAT_ID", "").split(",") if c.strip()]
    tag = os.environ.get("SUBJECT_TAG", "")

    if not dry and (not token or not chats):
        print("THIẾU TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID — bỏ qua, KHÔNG coi là lỗi.",
              file=sys.stderr)
        return 0

    if morning:
        return run_morning(token, chats, tag, dry)

    md = _load_make_docx()
    cur = md.extract_data((ROOT / "index.html").read_text(encoding="utf-8"))
    prev = md.prev_data()
    us = md.pick_items(cur, prev, "usNews")
    world = md.pick_items(cur, prev, "worldNews")
    events = md.pick_items(cur, prev, "events")
    sections = md.build_sections(us, world, events)
    total = sum(len(items) for _, items in sections)

    if total == 0:
        print("Không có tin mới trong lần publish này — không gửi Telegram.", file=sys.stderr)
        return 0

    generated_at = cur.get("generatedAt", "")
    gaps = read_gaps(generated_at)
    msgs = build_messages(sections, generated_at, total, gaps, tag)

    # File .docx: workflow đã dựng thì dùng lại, chưa có thì tự dựng (chạy tay ở local).
    docx = os.environ.get("DOCX_PATH", "").strip()
    if not docx:
        try:
            out = subprocess.run(
                [sys.executable, str(pathlib.Path(__file__).resolve().parent / "make_docx.py")],
                capture_output=True, text=True, cwd=str(ROOT), timeout=120)
            for line in out.stdout.splitlines():
                if line.startswith("DOCX="):
                    docx = line[len("DOCX="):].strip()
        except Exception as e:
            print(f"[docx] không dựng được file đính kèm: {e}", file=sys.stderr)
    if docx and not pathlib.Path(docx).is_file():
        print(f"[docx] không thấy file {docx} — gửi tin nhắn không kèm file", file=sys.stderr)
        docx = ""

    if dry:
        print(f"=== DRY_RUN — {len(msgs)} message, {total} tin, docx={docx or '(không có)'} ===")
        for i, m in enumerate(msgs, 1):
            print(f"\n----- message {i}/{len(msgs)} ({len(m)} ký tự) -----")
            print(m)
        return 0

    return send_all(token, chats, msgs, docx, f"Bản tin đầy đủ {generated_at}")


if __name__ == "__main__":
    sys.exit(main())
