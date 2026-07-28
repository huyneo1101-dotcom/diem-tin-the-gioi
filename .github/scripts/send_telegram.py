#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gửi bản tin vừa quét qua Telegram Bot API — KÊNH GỬI DUY NHẤT (email đã tắt 27/07/2026).

Chạy:
    TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=... python3 .github/scripts/send_telegram.py
    DRY_RUN=1 python3 .github/scripts/send_telegram.py     # in ra màn hình, không gửi

Biến môi trường:
    TELEGRAM_BOT_TOKEN  bắt buộc (trừ DRY_RUN)  — token @BotFather cấp
    TELEGRAM_CHAT_ID    bắt buộc (trừ DRY_RUN)  — id người/nhóm/kênh nhận; nhiều nơi thì
                        ngăn bằng dấu phẩy ("123456789,-1001234567890")
    TELEGRAM_BAT_BUOC   tuỳ chọn — ='0' thì thiếu secret sẽ thoát êm (kênh tắt có chủ ý).
                        Mặc định BẮT BUỘC: thiếu secret là job ĐỎ. Xem `tg_api.kiem_cau_hinh`
    DOCX_PATH           tuỳ chọn — đường dẫn .docx đính kèm (workflow truyền vào; rỗng thì
                        script tự gọi make_docx.py để dựng)
    SUBJECT_TAG         tuỳ chọn — tiền tố gắn trước tiêu đề (vd "[TEST] ")
    DRY_RUN             =1 thì chỉ in, không gọi API

⚠️ KHÔNG CÒN CHỐT "thiếu secret thì thoát êm cả nắm" (bỏ 27/07/2026). Nó chỉ đúng khi CHƯA
cấu hình; repo này đã cắm secret nên chốt đó chỉ còn tác dụng che ca mất secret. Lý do đầy đủ
trong docstring của `scripts/tg_api.py:kiem_cau_hinh`. Cùng tinh thần: mọi ca "không gửi được"
dưới đây phải phân biệt KHÔNG CÓ GÌ ĐỂ GỬI (êm) với HỎNG (đỏ).

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
import zoneinfo

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
VN = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")

# Gọi API qua curl, KHÔNG qua urllib: máy Huy có cert chèn giữa nên urllib trượt
# CERTIFICATE_VERIFY_FAILED (gặp thật 27/07/2026). Chi tiết trong scripts/tg_api.py.
sys.path.insert(0, str(ROOT / "scripts"))
from tg_api import call, kiem_cau_hinh, send_document  # noqa: E402

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


def chunk(blocks):
    """Nối các khối bằng DÒNG TRỐNG rồi cắt thành message ≤ MAX_LEN, không cắt giữa khối.

    Chỉ thị Huy 28/07/2026: *"giữa các tin và giữa các ý thì xuống dòng rồi cách 1 dòng nữa
    cho dễ đọc"*. Vì vậy **mỗi đơn vị đọc được là MỘT khối** (một tin, một bài think-tank kèm
    câu 'điều rút ra', một luận điểm báo cáo tuần, một mục 'Mới trên web') và các khối cách
    nhau đúng một dòng trống. Dòng nào thuộc CÙNG một ý (tên sự kiện + dòng ngày/địa điểm,
    tít bài + takeaway) thì nằm CHUNG một khối, ngăn bằng `\\n` đơn — đừng tách ra, tách là
    ý bị xé đôi bởi khoảng trắng.

    ⚠️ Đừng thêm `"\\n"` vào đầu tiêu đề mục nữa (cách cũ): giờ khoảng cách do hàm này lo,
    thêm nữa là thành hai dòng trống. Dùng CHUNG cho cả bản tối lẫn bản sáng — hai bộ luật
    song song chắc chắn lệch nhau.
    """
    msgs, cur = [], ""
    for b in blocks:
        piece = (b if not cur else "\n\n" + b)
        if len(cur) + len(piece) > MAX_LEN:
            msgs.append(cur)
            cur = b
        else:
            cur += piece
    if cur:
        msgs.append(cur)
    return msgs


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
        blocks.append(f"<b>{idx}. {esc(name)}</b>")
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
        blocks.append("<b>⚠️ Chủ đề thiếu và lý do</b>")
        if not thieu:
            blocks.append("• Không chủ đề nào thiếu.")
        for t in thieu:
            blocks.append(f"• <b>{esc(t.get('name'))}</b> "
                          f"({t.get('count', '?')}/{t.get('target', '?')}): "
                          f"{esc(t.get('reason') or 'không ghi lý do')}")

    return chunk(blocks)


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
        # Tên sự kiện + dòng ngày/địa điểm là CÙNG một ý → chung khối, ngăn bằng \n đơn.
        blocks.append(f"<b>[{nhan}]</b>{moi} {esc(ev.get('name'))}"
                      + (f"\n<i>{esc(meta)}</i>" if meta else ""))
        for it in ev.get("items") or []:
            url = it.get("sourceUrl") or ""
            t = esc(it.get("title"))
            blocks.append(f"• <a href=\"{esc(url)}\">{t}</a>" if url else f"• {t}")

    if len(all_events) > len(events):
        con = len(all_events) - len(events)
        blocks.append(f"<i>… và {con} sự kiện/tập trận nữa — xem đầy đủ trên trang.</i>")
        print(f"[morning] cắt bớt {con}/{len(all_events)} sự kiện cho vừa Telegram",
              file=sys.stderr)

    w = pl.get("weekly")
    if w:
        blocks.append(f"📊 <b>Báo cáo tuần {esc(w.get('weekStart'))}–{esc(w.get('weekEnd'))}</b>")
        for c in w.get("countries") or []:
            # MỖI LUẬN ĐIỂM MỘT KHỐI. Trước đây gộp bằng " · " thành một đoạn chạy dài —
            # đúng chỗ Huy gọi là "giữa các ý" cần giãn ra.
            blocks.append(f"• {esc(c.get('flag'))} <b>{esc(c.get('name'))}</b>")
            for p in c.get("points") or []:
                blocks.append(f"– {esc(p)}")

    anas = pl.get("analyses") or []
    if anas:
        blocks.append("🏛️ <b>Think-tank</b>")
        for a in anas:
            t = esc(a.get("title"))
            url = a.get("url") or ""
            line = f"• <a href=\"{esc(url)}\">{t}</a>" if url else f"• {t}"
            if a.get("outlet"):
                line += f" <i>— {esc(a['outlet'])}</i>"
            # Tít + câu 'điều rút ra' là một ý → chung khối.
            if a.get("takeaway"):
                line += f"\n<i>{esc(a['takeaway'])}</i>"
            blocks.append(line)

    feats = pl.get("features") or []
    if feats:
        blocks.append("🆕 <b>Mới trên web</b>")
        for f in feats:
            blocks.append(f"• <b>{esc(f.get('title'))}</b>: {esc(f.get('desc'))}")

    tip = pl.get("tip")
    if tip:
        duong = (pl.get("webUrl", "") + tip.get("path", "")) if tip.get("path") else ""
        blocks.append(f"💡 <b>{esc(tip.get('title'))}</b>\n{esc(tip.get('desc'))}"
                      + (f"\n{esc(duong)}" if duong else ""))

    if pl.get("webUrl"):
        blocks.append(f"<a href=\"{esc(pl['webUrl'])}\">Mở trang Điểm Tin</a>")

    return chunk(blocks)


def send_all(token, chats, msgs, docx="", caption="", files=None):
    """`files` = [(path, caption), ...] gửi SAU file chính.

    Dùng cho file Word thứ hai — TIN BỊ LOẠI (chỉ thị Huy 28/07/2026). Gửi sau `docx`
    chứ không gộp chung: bản tin chính phải tới tay trước, file phụ trợ hỏng thì cũng
    không được kéo theo bản tin chính.
    """
    for chat in chats:
        for m in msgs:
            r = call(token, "sendMessage", {
                "chat_id": chat, "text": m, "parse_mode": "HTML",
                "disable_web_page_preview": True,
            })
            if not r.get("ok"):
                print(f"LỖI sendMessage tới {chat}: {r}", file=sys.stderr)
                return 1
        if docx:
            r = send_document(token, chat, docx, caption)
            if not r.get("ok"):
                print(f"LỖI sendDocument tới {chat}: {r}", file=sys.stderr)
                return 1
        n_phu = 0
        for path, cap in (files or []):
            r = send_document(token, chat, path, cap)
            if not r.get("ok"):
                # KHÔNG return 1: bản tin chính đã gửi xong ở trên. Xem ghi chú "vì sao file
                # phụ không làm đỏ job" ở `dung_file_loai()`.
                print(f"::warning::Không gửi được file phụ {path} tới {chat}: {r}",
                      file=sys.stderr)
                continue
            n_phu += 1
        print(f"Đã gửi {len(msgs)} message{' + file .docx' if docx else ''}"
              f"{f' + {n_phu} file phụ' if n_phu else ''} tới {chat}")
    return 0


def dung_file_loai():
    """File Word THỨ HAI — tin bị loại dù đúng 5 chủ đề (chỉ thị Huy 28/07/2026).

    Trả (path, caption) hoặc None. Workflow dựng sẵn thì dùng lại qua `DOCX_LOAI_PATH`,
    chưa có thì tự gọi `make_docx_loai.py` (chạy tay ở local).

    ⚠️ HỎNG Ở ĐÂY **KHÔNG** LÀM ĐỎ JOB — cố ý, ngược với nhánh .docx chính. Lý do: bước
    `Ghi sổ đã gửi` chạy SAU bước Telegram, nên bước Telegram đỏ là sổ KHÔNG được ghi →
    canary kêu oan *và* bản tin TỐI hôm sau liệt kê lại nguyên lô tin đã gửi (đúng lỗi
    Huy bắt hôm 27/07). Đánh đổi một file phụ lấy nguyên cơ chế chống lặp tin là lỗ vốn.
    ⚠️ Nhưng KHÔNG im lặng: in `::warning::` để trang run có dấu vết, và caller nhắn
    một dòng về CHAT CHỦ để Huy thấy ngay trên điện thoại — cùng quy ước với `canary.py`
    (cảnh báo hạ tầng gửi cho người vận hành, không gửi cho người đọc).
    """
    path = os.environ.get("DOCX_LOAI_PATH", "").strip()
    if not path:
        try:
            out = subprocess.run(
                [sys.executable,
                 str(pathlib.Path(__file__).resolve().parent / "make_docx_loai.py")],
                capture_output=True, text=True, cwd=str(ROOT), timeout=120)
        except Exception as e:  # noqa: BLE001
            return None, f"không chạy được make_docx_loai.py: {e}"
        dong = [l for l in out.stdout.splitlines() if l.startswith("DOCX_LOAI=")]
        if out.returncode != 0 or not dong:
            return None, (f"make_docx_loai.py hỏng (rc={out.returncode}): "
                          f"{out.stderr.strip()[-300:]}")
        path = dong[-1][len("DOCX_LOAI="):].strip()
        if not path:
            return None, ""      # hôm nay không loại tin nào — im lặng ĐÚNG
    if not pathlib.Path(path).is_file():
        return None, f"không thấy file {path}"
    return path, ""


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

    if not dry:
        rc = kiem_cau_hinh(token, chats, "bản tin sáng" if morning else "bản tin")
        if rc is not None:
            return rc

    if morning:
        return run_morning(token, chats, tag, dry)

    md = _load_make_docx()
    cur = md.extract_data((ROOT / "index.html").read_text(encoding="utf-8"))
    prev = md.prev_data()
    # TIN NHẮN Telegram lọc sổ đã gửi (giống THÂN EMAIL): đây là thông báo, lặp lại tin đã
    # báo buổi sáng thì thừa. Ngược lại FILE .docx đính kèm KHÔNG lọc — nó là bản tổng hợp
    # cả ngày Huy lưu lại (chỉ thị Huy 27/07). Hai thứ lệch nhau là CỐ Ý, không phải bug.
    us = md.loc_chua_gui(md.pick_items(cur, prev, "usNews"))
    world = md.loc_chua_gui(md.pick_items(cur, prev, "worldNews"))
    # KHÔNG liệt kê tin TẬP TRẬN/SỰ KIỆN ở đây — chúng thuộc email `🎖️ Sự kiện & Tập trận`
    # buổi sáng (quy tắc "EMAIL TỐI GỒM NHỮNG GÌ" trong CLAUDE.md, chỉ thị Huy 27/07). Làm vậy
    # tin nhắn Telegram khớp đúng THÂN EMAIL — vốn chỉ đọc worldNews + usNews.
    # ⚠️ Chỉ bỏ khỏi phần LIỆT KÊ. FILE .docx đính kèm VẪN giữ chúng: đó là bản tổng hợp cả
    # ngày, và `events` là đường duy nhất Predator's Run vào bản tin tối (xem `event_items`).
    sections = md.build_sections(us, world, [])
    total = sum(len(items) for _, items in sections)

    generated_at = cur.get("generatedAt", "")

    # File .docx: workflow đã dựng thì dùng lại, chưa có thì tự dựng (chạy tay ở local).
    # DỰNG TRƯỚC khi xét `total == 0` — chỉ thị Huy 27/07: *"file word của telegram cũng phải
    # có 11 tin này"*. `total` đã bị lọc sổ, nên nó về 0 ngay khi mọi tin trong lô đã báo ở
    # bản trước; thoát sớm lúc đó thì Huy MẤT LUÔN file tổng hợp cả ngày, dù file vẫn đầy đủ.
    # KHÔNG CÓ TIN ĐỂ GỬI ≠ DỰNG FILE HỎNG — hai ca này trước đây cùng `return 0`, nên nếu
    # make_docx chết (thiếu python-docx, index.html vỡ, timeout) thì bản tin biến mất mà job
    # vẫn XANH. Đúng lớp lỗi với chốt secret vừa siết ở trên, nên siết luôn một thể:
    #   make_docx chạy xong, in "DOCX=" rỗng  -> hôm nay 0 tin, im lặng đúng   -> exit 0
    #   make_docx lỗi / không in DOCX= / file không tồn tại -> SỰ CỐ           -> exit 1
    docx = os.environ.get("DOCX_PATH", "").strip()
    tu_workflow = bool(docx)
    if not docx:
        try:
            out = subprocess.run(
                [sys.executable, str(pathlib.Path(__file__).resolve().parent / "make_docx.py")],
                capture_output=True, text=True, cwd=str(ROOT), timeout=120)
        except Exception as e:
            print(f"❌ [docx] không chạy được make_docx.py: {e}", file=sys.stderr)
            return 1
        dong = [l for l in out.stdout.splitlines() if l.startswith("DOCX=")]
        if out.returncode != 0 or not dong:
            print(f"❌ [docx] make_docx.py hỏng (rc={out.returncode}) — bản tin KHÔNG gửi được.\n"
                  f"   stdout: {out.stdout.strip()[-500:]}\n"
                  f"   stderr: {out.stderr.strip()[-500:]}", file=sys.stderr)
            return 1
        docx = dong[-1][len("DOCX="):].strip()
        if not docx:
            print("Hôm nay không có tin nào để dựng .docx — không gửi, KHÔNG coi là lỗi.",
                  file=sys.stderr)
            return 0

    if not pathlib.Path(docx).is_file():
        # Workflow đã bảo có file mà không thấy => bước dựng ở trên đã hỏng, không phải "0 tin".
        print(f"❌ [docx] không thấy file {docx}"
              + (" (DOCX_PATH do workflow truyền vào)" if tu_workflow else "")
              + " — bản tin CHỈ gửi bằng file nên đây là SỰ CỐ.", file=sys.stderr)
        return 1

    # CHỈ GỬI FILE .docx, KHÔNG liệt kê tin trong tin nhắn (chỉ thị Huy 27/07/2026:
    # *"không gửi full tin như ở trên, chỉ gửi file word thôi"*). Trước đây `build_messages`
    # dựng 2 tin nhắn dài liệt kê từng tin + khối "sản lượng 5 chủ đề / lý do thiếu" — đọc
    # trên điện thoại rất nặng, mà toàn bộ nội dung đó đã có sẵn trong file rồi.
    # ⚠️ `build_messages` và `read_gaps` từ đây KHÔNG CÒN ĐƯỢC GỌI (bản `--morning` dùng hàm
    # khác — `build_morning_messages`). Cố ý giữ lại để bật lại trong một dòng nếu Huy đổi ý;
    # đừng tưởng chúng đang chạy mà đi sửa, và cũng đừng xoá `logs/scan-gaps.json` vì tưởng
    # hết chỗ dùng — email/web vẫn đọc file đó.
    msgs = []
    caption = (f"{tag}📰 Điểm Tin {generated_at}"
               + (f" — {total} tin mới" if total else " — không có tin mới so với bản trước"))

    # FILE THỨ HAI — tin bị loại dù đúng 5 chủ đề (chỉ thị Huy 28/07/2026).
    loai_path, loai_loi = dung_file_loai()
    files = []
    if loai_path:
        files.append((loai_path, f"{tag}🚫 Tin bị loại {generated_at} — kèm lý do"))
    elif loai_loi:
        print(f"::warning::[loai] {loai_loi}", file=sys.stderr)

    if dry:
        print(f"=== DRY_RUN — {len(msgs)} message, {total} tin, docx={docx} ===")
        print(f"caption: {caption}")
        print(f"file tin bị loại: {loai_path or '(không có)'}"
              + (f" — lỗi: {loai_loi}" if loai_loi else ""))
        return 0

    rc = send_all(token, chats, msgs, docx, caption, files)

    # Dựng file phụ hỏng thì báo CHAT CHỦ một dòng — Huy thấy ngay trên điện thoại thay vì
    # phải vào tab Actions đọc `::warning::`. Chỉ chat chủ, không gửi người đọc bản tin.
    if loai_loi and chats:
        call(token, "sendMessage", {
            "chat_id": os.environ.get("TELEGRAM_OWNER_CHAT", "").strip() or chats[0],
            "text": f"⚠️ Không dựng được file Word TIN BỊ LOẠI cho {generated_at}: {loai_loi}",
            "disable_web_page_preview": True,
        })
    return rc


if __name__ == "__main__":
    sys.exit(main())
