#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gom ứng viên tin từ các KÊNH TELEGRAM công khai — lớp [TG], bổ sung cho harvest.py.

Dùng:  python3 scripts/telegram_harvest.py                # in ứng viên theo 5 chủ đề
       python3 scripts/telegram_harvest.py --all          # in cả bài KHÔNG khớp chủ đề
       python3 scripts/telegram_harvest.py --probe        # chỉ dò kênh sống/chết
       python3 scripts/telegram_harvest.py --json /tmp/tg.json

CÁCH LẤY: bản xem trước web `https://t.me/s/<kênh>` — HTML tĩnh, 20 bài gần nhất, KHÔNG
cần API key, KHÔNG cần đăng nhập, KHÔNG cần số điện thoại. Chỉ đọc nội dung mà chính kênh
đã công khai cho web.

⚠️ GIỚI HẠN ĐÃ ĐO THẬT (27/07/2026) — đọc trước khi thêm kênh:
  1. Kênh TẮT xem trước web thì đường này KHÔNG lấy được. Dò 48 kênh thì 35 hỏng, trong đó
     có đúng những kênh OSINT quốc phòng lớn nhất: @sentdefender (OSINTdefender),
     @militarylandnet (MilitaryLand.net). Chúng CÓ THẬT nhưng chặn web preview.
     → Muốn đọc nhóm này phải đi đường MTProto (Telethon, cần đăng nhập tài khoản).
  2. Phân biệt "kênh không tồn tại" với "kênh tắt preview": mở `https://t.me/<kênh>` (không
     có /s/) rồi xem `og:title` — ra "Telegram: Contact @x" là KHÔNG TỒN TẠI, ra tên thật
     là CÓ THẬT mà tắt preview. `--probe` in sẵn cột này.
  3. Preview có thể đứng ở quá khứ dù kênh vẫn sống: @osinttechnical chỉ trả bài tới
     27/06/2022. Vì vậy `--probe` in tuổi bài mới nhất — kênh nào quá cũ thì bỏ khỏi bảng.

⚠️ TELEGRAM LÀ RADAR, KHÔNG PHẢI NGUỒN NẠP THẲNG — cùng vai với [GNEWS] trong harvest.py:
kênh Telegram là mạng xã hội, không nằm trong thang xác minh nguồn của CLAUDE.md. Agent
PHẢI truy về bài gốc (thông cáo chính thức / wire / báo chuyên ngành) rồi mới nạp, và
`sourceUrl` TUYỆT ĐỐI không được là link t.me. Script đã trích sẵn mọi URL ngoài mà bài
Telegram dẫn tới (cột `links`) để đỡ công truy ngược.
Riêng kênh của truyền thông nhà nước độc tài (TASS, Sputnik, Rybar…): theo CLAUDE.md chỉ
dùng cho phát ngôn CỦA CHÍNH HỌ, không làm nguồn cho sự kiện tranh chấp/thương vong —
bảng nguồn đánh dấu cột "hạng" là `nhanuoc` cho nhóm này.
"""
import argparse
import concurrent.futures as cf
import datetime
import html as htmlmod
import json
import os
import pathlib
import re
import subprocess
import sys
import zoneinfo

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import topics  # noqa: E402
import tap_tran  # noqa: E402
from topics import match_topic  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
VN = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
CHANNELS_DOC = ROOT / "docs" / "telegram-channels.md"
PER_TOPIC_CAP = 15
# Số ký tự đầu bài dùng để khớp chủ đề — xấp xỉ độ dài một tiêu đề báo (xem chú thích
# ở chỗ gọi match_topic). Nới số này lên là kéo nhiễu về, siết xuống là bỏ sót bài mà
# kênh viết lối "dẫn nhập rồi mới vào tin".
HEAD_CHARS = 200


def curl(url: str, timeout: int = 25) -> str:
    p = subprocess.run(
        ["curl", "-sL", "--compressed", "--max-time", str(timeout), "-A", UA, url],
        capture_output=True)
    return p.stdout.decode("utf-8", "replace")


def channels_from_doc():
    """Đọc bảng kênh trong docs/telegram-channels.md -> [(handle, mô tả, hạng)].

    Đọc từ file tài liệu thay vì hardcode: thêm/bớt kênh chỉ sửa một chỗ, và bảng đó cũng
    là thứ Huy đọc được — cùng cách harvest.py đọc bảng RSS trong CLAUDE.md.
    """
    if not CHANNELS_DOC.is_file():
        print(f"Chưa có {CHANNELS_DOC} — tạo file đó rồi chạy lại.", file=sys.stderr)
        return []
    out, seen = [], set()
    for line in CHANNELS_DOC.read_text(encoding="utf-8").split("\n"):
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or not cells[0].startswith("@"):
            continue
        handle = cells[0].lstrip("@").strip("`")
        if handle in seen:
            continue
        seen.add(handle)
        hang = cells[2] if len(cells) > 2 else ""
        out.append((handle, cells[1], hang))
    return out


def parse_channel(handle: str):
    """Trả (trang_thai, ten_kenh, [bài]). Mỗi bài: {ngay, gio, text, url, links}."""
    body = curl(f"https://t.me/s/{handle}")
    title_m = re.search(r'<meta property="og:title" content="([^"]*)"', body)
    title = htmlmod.unescape(title_m.group(1)) if title_m else ""

    # Không có khối message nào -> kênh tắt preview hoặc không tồn tại. Phân biệt bằng
    # og:title của trang KHÔNG có /s/ (xem docstring, giới hạn #2).
    if "tgme_widget_message_text" not in body:
        probe = curl(f"https://t.me/{handle}")
        t2 = re.search(r'<meta property="og:title" content="([^"]*)"', probe)
        name2 = htmlmod.unescape(t2.group(1)) if t2 else ""
        if name2.startswith("Telegram: Contact"):
            return "KHONG-TON-TAI", name2, []
        return "TAT-PREVIEW", name2, []

    posts = []
    # Mỗi bài: khối bắt đầu bằng data-post="<kênh>/<id>", trong đó có text và <time datetime>.
    for block in body.split('class="tgme_widget_message ')[1:]:
        post_m = re.search(r'data-post="([^"]+)"', block)
        time_m = re.search(r'<time datetime="([^"]+)"', block)
        text_m = re.search(
            r'class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', block, re.S)
        if not (post_m and time_m):
            continue
        raw = text_m.group(1) if text_m else ""
        # Link ngoài mà bài dẫn tới -> đường truy về bài gốc cho agent.
        links = [htmlmod.unescape(u) for u in re.findall(r'href="(https?://[^"]+)"', raw)
                 if "t.me/" not in u and "telegram.me" not in u]
        text = re.sub(r"<br\s*/?>", " ", raw)
        text = htmlmod.unescape(re.sub(r"<[^>]+>", "", text))
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            continue
        dt = datetime.datetime.fromisoformat(time_m.group(1).replace("Z", "+00:00"))
        dt_vn = dt.astimezone(VN)
        posts.append({
            "ngay": dt_vn.date().isoformat(),
            "gio": dt_vn.strftime("%H:%M"),
            "text": text,
            "url": f"https://t.me/{post_m.group(1)}",
            "links": links,
        })
    return "OK", title, posts


def parse_channel_mtproto(client, handle: str, days: int):
    """Như parse_channel nhưng qua MTProto — đọc được cả kênh TẮT xem trước web.

    Chỉ gọi API ĐỌC lịch sử kênh công khai; không gửi, không join, không đọc chat riêng.
    """
    import datetime as _dt
    from telethon.errors import (ChannelPrivateError, UsernameInvalidError,
                                 UsernameNotOccupiedError, FloodWaitError)

    moc = _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(days=days + 1)
    try:
        ent = client.get_entity(handle)
    except (UsernameInvalidError, UsernameNotOccupiedError, ValueError):
        return "KHONG-TON-TAI", "", []
    except ChannelPrivateError:
        return "RIENG-TU", "", []
    except FloodWaitError as e:
        # Telegram bắt chờ — KHÔNG lách bằng cách thử lại ngay; báo ra để người chạy biết.
        return f"FLOOD-WAIT-{e.seconds}s", "", []
    except Exception as e:
        return f"LOI({type(e).__name__})", "", []

    posts = []
    try:
        for m in client.iter_messages(ent, limit=80):
            if m.date < moc:
                break
            text = (m.message or "").strip()
            if not text:
                continue
            text = re.sub(r"\s+", " ", text)
            links = []
            for ent_off in (m.entities or []):
                u = getattr(ent_off, "url", None)
                if u and "t.me/" not in u:
                    links.append(u)
            links += [u for u in re.findall(r"https?://\S+", text)
                      if "t.me/" not in u and u not in links]
            dt_vn = m.date.astimezone(VN)
            posts.append({
                "ngay": dt_vn.date().isoformat(),
                "gio": dt_vn.strftime("%H:%M"),
                "text": text,
                "url": f"https://t.me/{handle}/{m.id}",
                "links": links[:5],
            })
    except FloodWaitError as e:
        return f"FLOOD-WAIT-{e.seconds}s", getattr(ent, "title", ""), posts
    except Exception as e:
        return f"LOI({type(e).__name__})", getattr(ent, "title", ""), posts
    return "OK", getattr(ent, "title", "") or handle, posts


def mtproto_client():
    """Dựng client Telethon từ biến môi trường. Thiếu gì thì nói rõ thiếu gì rồi trả None."""
    api_id = os.environ.get("TG_API_ID", "").strip()
    api_hash = os.environ.get("TG_API_HASH", "").strip()
    session = os.environ.get("TG_SESSION", "").strip()
    thieu = [n for n, v in (("TG_API_ID", api_id), ("TG_API_HASH", api_hash),
                            ("TG_SESSION", session)) if not v]
    if thieu:
        print(f"Thiếu biến môi trường: {', '.join(thieu)}. Tạo bằng "
              "`python3 scripts/telegram_login.py` (Huy tự chạy).", file=sys.stderr)
        return None
    try:
        from telethon.sync import TelegramClient
        from telethon.sessions import StringSession
    except ImportError:
        print("Thiếu telethon. Cài: python3 -m pip install telethon", file=sys.stderr)
        return None
    c = TelegramClient(StringSession(session), int(api_id), api_hash,
                       device_model="Diem Tin harvest", system_version="macOS")
    c.connect()
    if not c.is_user_authorized():
        print("Session không còn hiệu lực (bị chấm dứt ở Telegram?) — chạy lại "
              "telegram_login.py.", file=sys.stderr)
        return None
    return c


def probe(channels):
    print(f"Dò {len(channels)} kênh...\n", file=sys.stderr)
    now = datetime.datetime.now(VN)
    rows = []
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        for (handle, mota, hang), (st, title, posts) in zip(
                channels, ex.map(lambda c: parse_channel(c[0]), channels)):
            tuoi = ""
            if posts:
                newest = max(p["ngay"] + " " + p["gio"] for p in posts)
                d = datetime.datetime.strptime(newest, "%Y-%m-%d %H:%M").replace(tzinfo=VN)
                tuoi = f"{(now - d).total_seconds() / 3600:.1f}h"
            rows.append((handle, st, len(posts), tuoi, title or mota))
    print(f"{'KÊNH':<26}{'TRẠNG THÁI':<16}{'BÀI':>4}  {'MỚI NHẤT':>9}  TÊN")
    for h, st, n, tuoi, title in rows:
        print(f"@{h:<25}{st:<16}{n:>4}  {tuoi:>9}  {title[:40]}")
    print("\nTAT-PREVIEW = kênh có thật nhưng chặn xem trước web → cần đường MTProto.")
    print("KHONG-TON-TAI = sai tên hoặc kênh riêng tư.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true", help="chỉ dò kênh sống/chết")
    ap.add_argument("--all", action="store_true", help="in cả bài không khớp chủ đề nào")
    ap.add_argument("--days", type=int, default=1, help="lùi bao nhiêu ngày (mặc định 1)")
    ap.add_argument("--mtproto", action="store_true",
                    help="đọc qua tài khoản Telegram (Telethon) — với được cả kênh TẮT "
                         "xem trước web; cần TG_API_ID/TG_API_HASH/TG_SESSION")
    ap.add_argument("--json", metavar="PATH", help="ghi kết quả ra JSON")
    args = ap.parse_args()

    channels = channels_from_doc()
    if not channels:
        return 1
    if args.probe:
        probe(channels)
        return 0

    today = datetime.datetime.now(VN).date()
    window = {(today - datetime.timedelta(days=i)).isoformat() for i in range(args.days + 1)}
    print(f"Khung ngày: {min(window)} .. {max(window)} (giờ VN) · {len(channels)} kênh",
          file=sys.stderr)

    # Bơm từ khoá cuộc tập trận đang chạy TRƯỚC vòng `match_topic` (05/08/2026) — bảng chủ đề
    # 05 rỗng mặc định, không bơm thì lớp Telegram không bao giờ xếp được bài nào vào đó.
    # Đây là lý do lời gọi phải nằm ở CẢ HAI script quét, không chỉ `harvest.py`: hai lớp quét
    # độc lập, mỗi lớp nạp `topics` trong tiến trình của riêng nó.
    try:
        _dang = tap_tran.dang_dien_ra(tap_tran.doc_exercises(), today.isoformat())
        _keys = [k for e in _dang for k in tap_tran.tu_khoa(e)]
        topics.nap_tu_khoa_tap_tran(_keys)
        print(f"🎖️  Tập trận đang bám: {tap_tran.tom_tat(_dang)}", file=sys.stderr)
    except Exception as e:                                     # pragma: no cover
        print(f"⚠️  không nạp được cuộc tập trận đang chạy ({e}) — chủ đề tập trận sẽ trống",
              file=sys.stderr)

    client = None
    if args.mtproto:
        client = mtproto_client()
        if client is None:
            print("→ Không dùng được MTProto, lùi về đường xem trước web.", file=sys.stderr)

    if client is not None:
        # TUẦN TỰ, không đa luồng: MTProto tính giới hạn theo tài khoản, bắn song song là
        # ăn FloodWait và có thể bị khoá tạm phiên — đúng thứ không được để xảy ra với
        # tài khoản Telegram thật của Huy.
        print(f"[MTProto] đọc {len(channels)} kênh (tuần tự)...", file=sys.stderr)
        ket_qua = [(c, parse_channel_mtproto(client, c[0], args.days)) for c in channels]
        client.disconnect()
    else:
        with cf.ThreadPoolExecutor(max_workers=8) as ex:
            ket_qua = list(zip(channels, ex.map(lambda c: parse_channel(c[0]), channels)))

    hits, hong = [], []
    for (handle, mota, hang), (st, title, posts) in ket_qua:
        if st != "OK":
            hong.append((handle, st))
            continue
        for p in posts:
            if p["ngay"] not in window:
                continue
            # Khớp chủ đề trên PHẦN ĐẦU bài, không phải cả bài. Bài Telegram dài
            # (digest, nhiều đoạn) nên khớp toàn văn kéo về rất nhiều tin lệch chủ đề:
            # chạy thử 27/07 gán tin Triều Tiên hạt nhân và hợp kim Trung Quốc vào
            # "CNQS Mỹ" chỉ vì cuối bài có chữ Pentagon/US. `harvest.py` khớp trên
            # TIÊU ĐỀ, nên cắt về độ dài tương đương mới cùng một chuẩn.
            topic = match_topic(p["text"][:HEAD_CHARS], "both")
            if not topic and not args.all:
                continue
            hits.append({
                "lop": "TG", "chu_de": topic or "(không khớp chủ đề)",
                "ngay": p["ngay"], "gio": p["gio"],
                "kenh": f"@{handle}", "hang": hang,
                "tieu_de": p["text"][:220],
                "url": p["url"], "links": p["links"],
            })

    by_topic = {}
    for h in hits:
        by_topic.setdefault(h["chu_de"], []).append(h)

    print(f"\n=== ỨNG VIÊN TỪ TELEGRAM — {len(hits)} bài trong khung ngày ===")
    order = ["Nội bộ Mỹ", "Úc & Biển Đông", "CNQS Mỹ", "Mỹ – Mali", topics.CHU_DE_TAP_TRAN]
    if args.all:
        order.append("(không khớp chủ đề)")
    for topic in order:
        lst = sorted(by_topic.get(topic, []), key=lambda x: (x["ngay"], x["gio"]), reverse=True)
        print(f"\n-- {topic} ({len(lst)} bài) --")
        if not lst:
            print("   (không có)")
        for h in lst[:PER_TOPIC_CAP]:
            hang = f" ⚠️{h['hang']}" if h["hang"] in ("nhanuoc", "tonghop-vi") else ""
            if h["hang"] == "tonghop-vi" and not h["links"]:
                hang += " (KHÔNG dẫn nguồn — phải WebSearch tìm bài gốc, không ra thì BỎ)"
            print(f"   [TG][{h['ngay']} {h['gio']}] {h['kenh']}{hang}: {h['tieu_de'][:150]}")
            print(f"        post: {h['url']}")
            for u in h["links"][:3]:
                print(f"        link dẫn: {u[:120]}")

    if hong:
        print(f"\n⚠️  {len(hong)} kênh không đọc được: "
              + ", ".join(f"@{h}({s})" for h, s in hong))
    print("\n⚠️  [TG] LÀ RADAR — link t.me KHÔNG được nạp vào `sourceUrl`. Phải truy về bài gốc")
    print("    (dùng cột 'link dẫn' nếu có, hoặc WebSearch theo nội dung) rồi mới nạp.")
    print("⚠️  Kênh đánh dấu ⚠️nhanuoc: chỉ dùng cho phát ngôn CỦA CHÍNH HỌ (CLAUDE.md).")
    print("⚠️  Kênh ⚠️tonghop-vi (@quantin, @tra_da_via_he): tin đã DỊCH, không kèm link gốc và")
    print("    nhiều bài lấy từ nguồn Nga. Bắt buộc WebSearch ra bài gốc tiếng Anh rồi nạp theo")
    print("    bài đó (đổi cả tiêu đề lẫn URL, số liệu lấy theo gốc); không ra gốc thì BỎ.")
    print("⚠️  GIỜ ĐĂNG TRÊN KÊNH ≠ NGÀY SỰ KIỆN — kênh hay đăng lại tin cũ. Neo `date` theo")
    print("    ngày sự kiện trong bài gốc, ngoài khung thì BỎ.")

    if args.json:
        pathlib.Path(args.json).write_text(
            json.dumps(hits, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nĐã ghi {len(hits)} ứng viên ra {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
