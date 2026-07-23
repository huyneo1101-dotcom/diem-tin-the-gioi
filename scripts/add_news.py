#!/usr/bin/env python3
"""Chèn tin mới vào DATA trong index.html mà không cần đọc toàn bộ file.

Dùng: python3 scripts/add_news.py new_items.json
Hoặc: python3 scripts/add_news.py --recent-titles [N]
      In ra N tiêu đề gần nhất (mặc định 20) của worldNews + usNews + xNews +
      item của exercises/dipEvents, để nhúng vào prompt các agent quét nhằm
      tránh report lại tin/sự kiện đã có. Không ghi file, chỉ đọc.
Hoặc: python3 scripts/add_news.py --baomoi-pending
      In các bài "đã lưu" Báo Mới (baomoi-saved.json) CHƯA có trong DATA, để giao
      agent viết summary + significance rồi nạp lại qua section `baomoiNews`.

new_items.json:
{
  "date": "YYYY-MM-DD",
  "worldNews": [ {...}, ... ],
  "usNews": [ {...}, ... ],
  "baomoiNews": [ {...}, ... ],
  "xNews": [ {...}, ... ],
  "exerciseUpdates": [ {"name": "<tên đúng exercise đã có trong DATA>", "items": [ {...}, ... ]} ],
  "dipEventUpdates": [ {"name": "<tên đúng dipEvent đã có trong DATA>", "items": [ {...}, ... ]} ],
  "newDipEvents": [ {"name","status","dates","location","scale","summary","items":[{...}]}, ... ]
}

- newDipEvents: TẠO sự kiện ngoại giao MỚI trong dipEvents (vd ký kết song
  phương, thượng đỉnh, thăm cấp cao). Bị CHẶN nếu tên trùng/giống sự kiện đã
  có (Jaccard>=0.6) -> khi đó dùng dipEventUpdates. status: ongoing/recent/
  upcoming. Mỗi sự kiện phải có >=1 item (nguồn chứng minh), item bị kiểm tra
  ngày + link như tin thường.

- baomoiNews: bài "đã lưu" Báo Mới sau khi agent viết summary + significance. Chèn
  vào chung DATA.worldNews, gắn cờ `_baomoi` để web hiện nhãn 📌 Đã lưu. Áp ĐÚNG
  khung ngày như tin thường — chỉ bài đăng trong 24h gần nhất mới được lên web.

Guardrail tự động (chặn = raise lỗi, phải sửa JSON rồi chạy lại; cảnh báo = in ra):
- CHẶN: thiếu field, category sai, sourceUrl/url không hợp lệ, date ngoài khung
  (cũ hơn MAX_AGE_DAYS ngày so với "date" của batch, hoặc ở tương lai),
  URL rác (live-blog / trang chủ), URL trùng nhau trong batch, URL đã có sẵn
  trong DATA, ID bài X vô lý (bịa), tên exercise/dipEvent không khớp.
- CẢNH BÁO: sourceName lạ (ngoài danh sách nguồn đã biết), tiêu đề trùng gần
  giống tin đã có, phần nào chưa đủ chỉ tiêu số lượng.
"""
import collections
import datetime
import json
import pathlib
import re
import sys
import urllib.parse

NEWS_REQUIRED_FIELDS = {"date", "category", "title", "summary", "sourceName", "sourceUrl", "significance"}
VALID_CATEGORIES = {"Kinh tế", "Chính trị", "Công nghệ quân sự", "Ngoại giao"}
MIN_PER_CATEGORY = 2
FLOOR_DAY = 15  # SÀN CỨNG TỔNG NGÀY (sáng+tối): worldNews ≥ 15 VÀ usNews ≥ 15 (chỉ thị người dùng 23/07/2026)
MAX_AGE_DAYS = 1  # CHỈ nhận 2 ngày gần nhất (hôm nay + hôm qua); cũ hơn -> chặn

# Mục "Bị loại" KHÔNG giới hạn tổng số — chỉ giới hạn lượng thêm MỖI LẦN QUÉT, để một lô
# ứng viên Báo Mới (~80 bài/lần) không nhấn chìm loại tin giá trị hơn: tin ĐÚNG GU mà agent
# phải loại vì ngày/nghi trùng — đó mới là thứ người dùng cần rà để 👍 cứu.
REJECTED_PER_RUN = 20          # tổng thêm mỗi lần quét
BAOMOI_REJECT_PER_RUN = 10     # trong đó, phần ứng viên chuyên mục Báo Mới
# Tự dọn mục Bị loại: bỏ mục đã NẰM TRONG MỤC quá 2 ngày (tính theo `addedAt` — ngày được
# đưa vào, KHÔNG phải ngày đăng bài; tin "vừa rơi khỏi khung 3-7 ngày" vẫn vào được).
# Web giữ snapshot riêng cho tin đã 👍 kéo vào Bài mới (dt.promotedSnap) nên dọn không mất tin đã cứu.
REJECTED_KEEP_DAYS = 1
REJECT_CATEGORY_ORDER = {"Công nghệ quân sự": 0, "Ngoại giao": 1, "Kinh tế": 2, "Chính trị": 3}

X_REQUIRED_FIELDS = {"date", "handle", "name", "title", "summary", "significance", "url"}
EVENT_ITEM_REQUIRED_FIELDS = {"date", "title", "summary", "sourceName", "sourceUrl"}

# Tạo sự kiện ngoại giao MỚI (newDipEvents) — cho phép từ 11/07/2026, có rào chắn chống trùng
VALID_EVENT_STATUS = {"ongoing", "recent", "upcoming"}
NEW_EVENT_REQUIRED_FIELDS = {"name", "status", "dates", "location", "scale", "summary", "items"}

# Nguồn đã biết (chỉ để CẢNH BÁO nếu gặp nguồn lạ, không chặn — nguồn mới hợp lệ vẫn xuất hiện)
KNOWN_SOURCES = {
    # Báo chí
    "Defense News", "Naval News", "Breaking Defense", "Defense One", "SpaceNews", "Task & Purpose",
    "Al Jazeera", "Al Arabiya", "The Straits Times", "The Moscow Times", "South China Morning Post",
    "Politico", "Axios", "The Hindu", "Africanews", "CNBC", "Fortune",
    "VnEconomy", "VnExpress", "Tuổi Trẻ", "Thanh Niên", "Dân Trí", "Báo Mới", "Thế giới & Việt Nam",
    "Reuters", "Kyiv Post", "The Kyiv Independent", "Korea Times", "ANTARA News", "CGTN",
    # Wire + báo chí quốc tế (bổ sung 11/07 từ bộ nguồn chuẩn báo cáo)
    "Associated Press", "AP", "Agence France-Presse", "AFP", "Bloomberg", "Financial Times",
    "Wall Street Journal", "The Economist", "Nikkei Asia", "BBC", "Deutsche Welle", "France 24",
    "The Japan Times", "The Korea Herald", "USNI News", "C4ISRNet", "Army Recognition", "Oryx",
    "The Diplomat", "Foreign Policy", "Foreign Affairs",
    # Nguồn dữ liệu (tầng 2)
    "OECD", "WTO", "BIS", "UNCTAD", "IEA", "SIPRI", "IISS", "Janes",
    # Viện nghiên cứu (tầng 3)
    "CSIS", "RAND", "RUSI", "Chatham House", "CSET", "Brookings", "Carnegie Endowment", "CFR",
    "CNAS", "Atlantic Council", "Lowy Institute", "ASPI", "ISEAS", "RSIS", "ORF", "MERICS",
    "Jamestown Foundation", "ECFR", "Stimson Center", "Hudson Institute",
    # Tổ chức/cơ quan chính thức bổ sung (tầng 1)
    "EEAS", "ASEAN", "Hội đồng Bảo an Liên Hợp Quốc", "DARPA", "CISA", "NIST", "ENISA", "NATO DIANA",
    "Thông tấn xã Việt Nam", "Nhân Dân", "Quân đội Nhân dân",
    # Nguồn chính phủ/chính thức (primary — ưu tiên cao)
    "NATO", "Liên Hợp Quốc", "United Nations", "EU", "Hội đồng châu Âu", "IMF",
    "Nhà Trắng", "The White House", "Bộ Quốc phòng Mỹ", "U.S. Department of Defense",
    "Bộ Ngoại giao Mỹ", "U.S. Department of State", "CENTCOM", "Lực lượng Không gian Mỹ",
    "Fed", "Federal Reserve", "Bộ Quốc phòng Anh", "Chính phủ Anh", "Phủ Tổng thống Ukraine",
    "World Bank", "Ngân hàng Thế giới", "Royal Navy", "Bộ Ngoại giao Nhật Bản",
    "Chính phủ Việt Nam", "Báo Chính phủ", "Bộ Ngoại giao Việt Nam",
    # Truyền thông nhà nước (chỉ dùng cho phát ngôn của chính họ — xem CLAUDE.md)
    "Xinhua", "TASS",
}

# Pattern URL rác: trang live-blog / tổng hợp liên tục (không phải bài viết cố định)
URL_BLOCK_PATTERNS = [
    re.compile(r"/live(?:[-/]|$)", re.I),
    re.compile(r"live-updates", re.I),
    re.compile(r"live-blog|liveblog", re.I),
    re.compile(r"live-news", re.I),
]


def find_data_span(html: str) -> tuple[int, int]:
    marker = "var DATA = "
    start = html.index(marker) + len(marker)
    depth = 0
    in_str = False
    esc = False
    i = start
    while i < len(html):
        c = html[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return start, i + 1
        i += 1
    raise ValueError("Không tìm thấy điểm kết thúc của var DATA")


def parse_date(s: str) -> datetime.date:
    return datetime.date.fromisoformat(s)


def check_date_window(date_str: str, ref: datetime.date, ctx: str) -> None:
    try:
        d = parse_date(date_str)
    except (ValueError, TypeError):
        raise ValueError(f"{ctx}: date không đúng định dạng YYYY-MM-DD: {date_str!r}")
    if d > ref:
        raise ValueError(f"{ctx}: date {date_str} ở TƯƠNG LAI so với ngày batch {ref} — nghi sai/bịa")
    if (ref - d).days > MAX_AGE_DAYS:
        raise ValueError(
            f"{ctx}: date {date_str} cũ hơn {MAX_AGE_DAYS} ngày so với batch {ref} — tin quá cũ, bỏ hoặc thay tin mới hơn"
        )


def check_url_quality(url: str, ctx: str) -> None:
    for pat in URL_BLOCK_PATTERNS:
        if pat.search(url):
            raise ValueError(f"{ctx}: URL có vẻ là trang live-blog/tổng hợp, không phải bài viết cố định: {url}")
    parsed = urllib.parse.urlparse(url)
    if parsed.path.strip("/") == "" and not parsed.query:
        raise ValueError(f"{ctx}: URL chỉ trỏ tới trang chủ, không phải bài viết cụ thể: {url}")


def check_x_id(url: str, ctx: str) -> None:
    m = re.search(r"/status/(\d+)", url)
    if not m:
        raise ValueError(f"{ctx}: url X không có dạng .../status/<id>: {url}")
    sid = m.group(1)
    if len(sid) < 15:
        raise ValueError(f"{ctx}: status ID X quá ngắn ({sid}) — nghi bịa (ID thật ~19 chữ số)")
    if re.search(r"0{5,}$", sid):
        raise ValueError(f"{ctx}: status ID X kết thúc bằng nhiều số 0 ({sid}) — nghi bịa")


def validate_news_items(items: list, label: str, ref: datetime.date) -> None:
    for idx, item in enumerate(items):
        ctx = f"{label}[{idx}]"
        missing = NEWS_REQUIRED_FIELDS - item.keys()
        if missing:
            raise ValueError(f"{ctx} thiếu field: {missing}")
        if item["category"] not in VALID_CATEGORIES:
            raise ValueError(f"{ctx} category không hợp lệ: {item['category']}")
        if not item["sourceUrl"].startswith("http"):
            raise ValueError(f"{ctx} sourceUrl không hợp lệ: {item['sourceUrl']}")
        check_date_window(item["date"], ref, ctx)
        check_url_quality(item["sourceUrl"], ctx)


def validate_x_items(items: list, ref: datetime.date) -> None:
    for idx, item in enumerate(items):
        ctx = f"xNews[{idx}]"
        missing = X_REQUIRED_FIELDS - item.keys()
        if missing:
            raise ValueError(f"{ctx} thiếu field: {missing}")
        if not item["url"].startswith("http"):
            raise ValueError(f"{ctx} url không hợp lệ: {item['url']}")
        check_date_window(item["date"], ref, ctx)
        check_x_id(item["url"], ctx)


def validate_event_updates(updates: list, label: str, ref: datetime.date) -> None:
    for u_idx, update in enumerate(updates):
        if "name" not in update or "items" not in update:
            raise ValueError(f"{label}[{u_idx}] cần có 'name' và 'items'")
        for idx, item in enumerate(update["items"]):
            ctx = f"{label}[{u_idx}].items[{idx}]"
            missing = EVENT_ITEM_REQUIRED_FIELDS - item.keys()
            if missing:
                raise ValueError(f"{ctx} thiếu field: {missing}")
            if not item["sourceUrl"].startswith("http"):
                raise ValueError(f"{ctx} sourceUrl không hợp lệ: {item['sourceUrl']}")
            check_date_window(item["date"], ref, ctx)
            check_url_quality(item["sourceUrl"], ctx)


def iter_new_urls(new_items: dict):
    for label in ("worldNews", "usNews", "baomoiNews"):
        for idx, it in enumerate(new_items.get(label, [])):
            yield f"{label}[{idx}]", it["sourceUrl"]
    for idx, it in enumerate(new_items.get("xNews", [])):
        yield f"xNews[{idx}]", it["url"]
    for label, key in (("exerciseUpdates", "exerciseUpdates"), ("dipEventUpdates", "dipEventUpdates")):
        for u_idx, upd in enumerate(new_items.get(key, [])):
            for idx, it in enumerate(upd["items"]):
                yield f"{label}[{u_idx}].items[{idx}]", it["sourceUrl"]
    for e_idx, ev in enumerate(new_items.get("newDipEvents", [])):
        for idx, it in enumerate(ev.get("items", [])):
            yield f"newDipEvents[{e_idx}].items[{idx}]", it["sourceUrl"]


def collect_existing_urls(data: dict) -> set:
    urls = set()
    for it in data.get("worldNews", []) + data.get("usNews", []):
        urls.add(it.get("sourceUrl"))
        # Tin đã ĐỔI NGUỒN từ Báo Mới sang nguồn gốc nước ngoài vẫn phải nhớ link Báo Mới cũ:
        # thiếu nó thì `--baomoi-pending` coi bài đó là "chưa nạp" và phiên sau nạp lại y hệt.
        if it.get("_baomoiUrl"):
            urls.add(it["_baomoiUrl"])
    for it in data.get("xNews", []):
        urls.add(it.get("url"))
    for ev in data.get("exercises", []) + data.get("dipEvents", []):
        for it in ev.get("items", []):
            urls.add(it.get("sourceUrl"))
    return urls


def check_duplicate_urls(new_items: dict, data: dict) -> None:
    existing = collect_existing_urls(data)
    seen = {}
    for ctx, url in iter_new_urls(new_items):
        if url in seen:
            raise ValueError(f"{ctx}: URL trùng với {seen[url]} trong cùng batch: {url}")
        seen[url] = ctx
        if url in existing:
            raise ValueError(f"{ctx}: URL đã có sẵn trong DATA (tin trùng): {url}")


def norm_tokens(title: str) -> set:
    return set(re.sub(r"[^\w\s]", " ", title.lower()).split())


def warn_similar_titles(new_items: dict, data: dict) -> None:
    existing = []
    for it in data.get("worldNews", []) + data.get("usNews", []):
        existing.append(it.get("title", ""))
    for it in data.get("xNews", []):
        existing.append(it.get("title", ""))
    existing_tokens = [(t, norm_tokens(t)) for t in existing if t]

    new_titles = []
    for label in ("worldNews", "usNews", "xNews"):
        for it in new_items.get(label, []):
            new_titles.append(it.get("title", ""))

    for nt in new_titles:
        nts = norm_tokens(nt)
        if not nts:
            continue
        for old, ots in existing_tokens:
            if not ots:
                continue
            jaccard = len(nts & ots) / len(nts | ots)
            if jaccard >= 0.6:
                print(f"  [CẢNH BÁO] tiêu đề nghi trùng (Jaccard {jaccard:.2f}):")
                print(f"      mới: {nt}")
                print(f"      cũ : {old}")
                break


def warn_unknown_sources(new_items: dict) -> None:
    unknown = set()
    for label in ("worldNews", "usNews"):
        for it in new_items.get(label, []):
            if it["sourceName"] not in KNOWN_SOURCES:
                unknown.add(it["sourceName"])
    for key in ("exerciseUpdates", "dipEventUpdates"):
        for upd in new_items.get(key, []):
            for it in upd["items"]:
                if it["sourceName"] not in KNOWN_SOURCES:
                    unknown.add(it["sourceName"])
    if unknown:
        print(f"  [CẢNH BÁO] nguồn lạ ngoài danh sách đã biết (kiểm tra lại độ tin cậy): {', '.join(sorted(unknown))}")


def validate_new_events(events: list, ref: datetime.date) -> None:
    for idx, ev in enumerate(events):
        ctx = f"newDipEvents[{idx}]"
        missing = NEW_EVENT_REQUIRED_FIELDS - ev.keys()
        if missing:
            raise ValueError(f"{ctx} thiếu field: {missing} (cần đủ để tạo sự kiện mới)")
        if ev["status"] not in VALID_EVENT_STATUS:
            raise ValueError(f"{ctx} status không hợp lệ: {ev['status']!r} (cần 1 trong {sorted(VALID_EVENT_STATUS)})")
        if not isinstance(ev["items"], list) or not ev["items"]:
            raise ValueError(f"{ctx} phải có ít nhất 1 item nguồn để chứng minh sự kiện có thật")
        for j, it in enumerate(ev["items"]):
            ictx = f"{ctx}.items[{j}]"
            miss = EVENT_ITEM_REQUIRED_FIELDS - it.keys()
            if miss:
                raise ValueError(f"{ictx} thiếu field: {miss}")
            if not it["sourceUrl"].startswith("http"):
                raise ValueError(f"{ictx} sourceUrl không hợp lệ: {it['sourceUrl']}")
            check_date_window(it["date"], ref, ictx)
            check_url_quality(it["sourceUrl"], ictx)


def check_new_event_names(new_events: list, existing_events: list) -> None:
    ex = [(e.get("name", ""), norm_tokens(e.get("name", ""))) for e in existing_events]
    for ev in new_events:
        nt = norm_tokens(ev["name"])
        if not nt:
            raise ValueError(f"newDipEvents: name rỗng/không hợp lệ")
        for oname, ot in ex:
            if not ot:
                continue
            jaccard = len(nt & ot) / len(nt | ot)
            if jaccard >= 0.6:
                raise ValueError(
                    f"newDipEvents: '{ev['name']}' trùng/giống sự kiện đã có '{oname}' (Jaccard {jaccard:.2f}) "
                    f"— dùng dipEventUpdates để cập nhật item vào sự kiện đó thay vì tạo mới"
                )


def apply_event_updates(existing_events: list, updates: list, label: str) -> int:
    by_name = {e["name"]: e for e in existing_events}
    added = 0
    for update in updates:
        name = update["name"]
        if name not in by_name:
            available = ", ".join(sorted(by_name.keys()))
            raise ValueError(f"{label}: không tìm thấy '{name}'. Tên hiện có: {available}")
        entry = by_name[name]
        entry["items"] = update["items"] + entry.get("items", [])
        added += len(update["items"])
    return added


def category_report(items: list, label: str) -> bool:
    counts = collections.Counter(item["category"] for item in items)
    ok = True
    print(f"  {label}: {len(items)} tin")
    for cat in sorted(VALID_CATEGORIES):
        n = counts.get(cat, 0)
        flag = "" if n >= MIN_PER_CATEGORY else "  <-- THIẾU (cần >= 2)"
        if n < MIN_PER_CATEGORY:
            ok = False
        print(f"    {cat}: {n}{flag}")
    return ok


def print_recent_titles(html_path: pathlib.Path, n: int) -> None:
    html = html_path.read_text(encoding="utf-8")
    start, end = find_data_span(html)
    data = json.loads(html[start:end])
    for label in ("worldNews", "usNews"):
        items = data.get(label, [])
        print(f"{label} ({min(n, len(items))} gần nhất):")
        for item in items[:n]:
            print(f"  [{item['date']}] {item['title']}")
    xitems = data.get("xNews", [])
    print(f"xNews ({min(n, len(xitems))} gần nhất):")
    for item in xitems[:n]:
        print(f"  [{item['date']}] {item['handle']}: {item['title']}")
    for label in ("exercises", "dipEvents"):
        print(f"{label} — item cập nhật gần nhất mỗi sự kiện:")
        for ev in data.get(label, []):
            recent = ev.get("items", [])[:3]
            titles = "; ".join(it["title"] for it in recent) or "(chưa có item)"
            print(f"  * {ev['name']} [{ev.get('status','?')}]: {titles}")


def _load_baomoi(path: pathlib.Path) -> tuple[list, int]:
    """Đọc file Báo Mới, LOẠI bài ngoài khung ngày. Trả (items trong khung, số bài quá cũ).

    Hai script sync đã lọc 24h theo timestamp rồi, nhưng nếu Action lỗi/không chạy thì file
    trong repo là bản CŨ — để agent nhìn thấy bài quá hạn là nó sẽ báo lên và guardrail chặn
    NGUYÊN LÔ, mất cả bản tin. Lọc ở đây để bài cũ không bao giờ tới tay agent.
    """
    try:
        items = json.loads(path.read_text(encoding="utf-8")).get("items", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return [], 0
    cutoff = datetime.date.today() - datetime.timedelta(days=MAX_AGE_DAYS)
    fresh = []
    for it in items:
        try:
            if parse_date(it.get("date", "")) >= cutoff:
                fresh.append(it)
        except ValueError:
            continue
    return fresh, len(items) - len(fresh)


def print_baomoi_pending(html_path: pathlib.Path, repo_root: pathlib.Path) -> None:
    """In bài Báo Mới CHƯA có trong DATA, tách 2 nhóm xử lý KHÁC NHAU.

    Cả 2 file đều do Action sync-baomoi sinh ra và chỉ có date/category/title/sourceName/
    sourceUrl/region — thiếu summary + significance (2 field guardrail bắt buộc), nên phải
    qua agent viết bổ sung. Cả 2 đã được lọc sẵn "đăng trong 24h" theo timestamp.

    - baomoi-saved.json  : bài NGƯỜI DÙNG tự bookmark -> lấy HẾT, không áp bộ lọc sở thích,
                           nạp qua section `baomoiNews` (web gắn nhãn 📌 Đã lưu).
    - baomoi-topics.json : KHO ỨNG VIÊN quét từ chuyên mục công khai -> CHỌN LỌC theo bộ lọc
                           sở thích, chỉ lấy vài bài tốt nhất, nạp qua `worldNews` như tin thường.
    """
    html = html_path.read_text(encoding="utf-8")
    start, end = find_data_span(html)
    data = json.loads(html[start:end])
    existing = collect_existing_urls(data)

    def fmt(it):
        return (
            f"  [{it.get('date','?')}] ({it.get('category','?')} · {it.get('region','') or 'không rõ'}) "
            f"{it.get('title','')}\n      {it.get('sourceName','')} — {it['sourceUrl']}"
        )

    saved, saved_old = _load_baomoi(repo_root / "baomoi-saved.json")
    pending = [it for it in saved if it.get("sourceUrl") and it["sourceUrl"] not in existing]
    old_note = f", bỏ {saved_old} bài đăng quá 24h" if saved_old else ""
    print(f"=== BÀI ĐÃ LƯU (lấy HẾT, không lọc sở thích) — {len(pending)}/{len(saved)} chưa nạp{old_note} ===")
    print("\n".join(fmt(it) for it in pending) or "  (không có bài mới)")

    topics, topics_old = _load_baomoi(repo_root / "baomoi-topics.json")
    cand = [it for it in topics if it.get("sourceUrl") and it["sourceUrl"] not in existing]
    old_note = f", bỏ {topics_old} bài đăng quá 24h" if topics_old else ""
    print(
        f"\n=== KHO ỨNG VIÊN theo chuyên mục (CHỌN LỌC, chỉ lấy bài tốt nhất) — "
        f"{len(cand)}/{len(topics)} chưa nạp{old_note} ==="
    )
    by_cat = collections.defaultdict(list)
    for it in cand:
        by_cat[it.get("category", "?")].append(it)
    for cat in sorted(by_cat):
        print(f"\n-- {cat} ({len(by_cat[cat])} bài) --")
        print("\n".join(fmt(it) for it in by_cat[cat]))
    if not cand:
        print("  (không có ứng viên — bỏ qua)")


def main() -> None:
    if len(sys.argv) >= 2 and sys.argv[1] == "--recent-titles":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        repo_root = pathlib.Path(__file__).resolve().parent.parent
        print_recent_titles(repo_root / "index.html", n)
        return

    if len(sys.argv) >= 2 and sys.argv[1] == "--baomoi-pending":
        repo_root = pathlib.Path(__file__).resolve().parent.parent
        print_baomoi_pending(repo_root / "index.html", repo_root)
        return

    if len(sys.argv) != 2:
        print(
            "Dùng: add_news.py <new_items.json>  |  add_news.py --recent-titles [N]"
            "  |  add_news.py --baomoi-pending",
            file=sys.stderr,
        )
        sys.exit(1)

    repo_root = pathlib.Path(__file__).resolve().parent.parent
    html_path = repo_root / "index.html"
    new_items = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))

    world_new = new_items.get("worldNews", [])
    us_new = new_items.get("usNews", [])
    baomoi_new = new_items.get("baomoiNews", [])
    x_new = new_items.get("xNews", [])
    exercise_updates = new_items.get("exerciseUpdates", [])
    dip_updates = new_items.get("dipEventUpdates", [])
    new_dip_events = new_items.get("newDipEvents", [])
    rejected_new = new_items.get("rejectedNews", [])
    date = new_items.get("date")

    if not date:
        raise ValueError("new_items.json thiếu 'date' (YYYY-MM-DD của batch) — cần để kiểm tra khung ngày")
    ref = parse_date(date)

    validate_news_items(world_new, "worldNews", ref)
    validate_news_items(us_new, "usNews", ref)
    # baomoiNews áp ĐÚNG khung ngày như tin thường (yêu cầu 22/07: bài Báo Mới chỉ lên web
    # nếu đăng trong 24h gần nhất) — baomoi_sync.py đã lọc sẵn theo timestamp, đây là chốt chặn.
    validate_news_items(baomoi_new, "baomoiNews", ref)
    validate_x_items(x_new, ref)
    validate_event_updates(exercise_updates, "exerciseUpdates", ref)
    validate_event_updates(dip_updates, "dipEventUpdates", ref)
    validate_new_events(new_dip_events, ref)

    html = html_path.read_text(encoding="utf-8")
    start, end = find_data_span(html)
    data = json.loads(html[start:end])

    # Chống trùng tên sự kiện ngoại giao mới với sự kiện đã có
    check_new_event_names(new_dip_events, data.get("dipEvents", []))

    # Cross-check với dữ liệu đang có (chặn URL trùng; cảnh báo tiêu đề gần giống)
    # Phải chạy TRƯỚC khi chèn để so với tin cũ, tránh tự trùng với tin vừa thêm.
    check_duplicate_urls(new_items, data)
    similar_warnings_data = {
        "worldNews": list(data.get("worldNews", [])),
        "usNews": list(data.get("usNews", [])),
        "xNews": list(data.get("xNews", [])),
    }

    # Tin Báo Mới vào chung luồng worldNews, giữ cờ _baomoi để web gắn nhãn 📌 Đã lưu
    # (và để loadBaomoi trong index.html nhận ra là đã xử lý, không trộn lại lần nữa).
    for it in baomoi_new:
        it["_baomoi"] = True
    # _addedDate = ngày ĐƯA LÊN (= batch date). Dùng để đếm SÀN TỔNG NGÀY: cả phiên sáng và tối
    # cùng ngày đều set date = hôm nay VN, nên đếm _addedDate == date gộp được tin của cả 2 phiên.
    # (web bỏ qua field này). Không dùng date đăng bài vì tin đăng hôm qua vẫn tính vào ngày đưa lên.
    for it in world_new + baomoi_new + us_new:
        it["_addedDate"] = date
    data["worldNews"] = world_new + baomoi_new + data.get("worldNews", [])
    data["usNews"] = us_new + data.get("usNews", [])
    data["xNews"] = x_new + data.get("xNews", [])

    exercise_items_added = apply_event_updates(data.get("exercises", []), exercise_updates, "exerciseUpdates")
    dip_items_added = apply_event_updates(data.get("dipEvents", []), dip_updates, "dipEventUpdates")

    # Tạo sự kiện ngoại giao MỚI (append vào cuối dipEvents)
    if new_dip_events:
        data["dipEvents"] = data.get("dipEvents", []) + new_dip_events

    # rejectedNews: tin bị loại khi quét — hiện ở mục "Bị loại" trên web để người dùng cứu (like)
    # hoặc xác nhận không thích (dislike). Không áp guardrail ngày/trùng-DATA (chúng là tin bị loại,
    # có thể cũ); chỉ cần title + sourceUrl, kèm 'reason'. Chống trùng trong rejectedNews + với tin live.
    # KHÔNG giới hạn tổng số, chỉ giới hạn số thêm MỖI LẦN QUÉT (xem 2 hằng số ở đầu file).
    live_urls = {i.get("sourceUrl", "") for i in data.get("worldNews", [])} | {
        i.get("sourceUrl", "") for i in data.get("usNews", [])
    }
    existing = data.get("rejectedNews", [])
    existing_urls = {i.get("sourceUrl", "") for i in existing}

    # (a) Ứng viên Báo Mới KHÔNG được chọn -> tự đổ vào mục Bị loại, không tốn token agent
    #     (dữ liệu đã đủ field sẵn trong baomoi-topics.json). Ưu tiên chủ đề người dùng thích.
    #     CHIA ĐỀU 4 chuyên mục (xoay vòng) thay vì lấy hết mục ưu tiên trước — kho ứng viên
    #     lệch nặng (vd 45 Kinh tế / 5 Ngoại giao) nên xếp theo độ ưu tiên sẽ ăn hết 10 slot
    #     bằng đúng 1 mục, người dùng không thấy được ứng viên của 3 mục còn lại.
    #     Vòng xoay đi theo thứ tự ưu tiên nên mục thích hơn vẫn được nhiều hơn: 3-3-2-2.
    cand_pool, _ = _load_baomoi(repo_root / "baomoi-topics.json")
    by_cat = collections.defaultdict(collections.deque)
    for it in sorted(cand_pool, key=lambda x: x.get("date", ""), reverse=True):  # mới nhất trước
        u = it.get("sourceUrl", "")
        if not it.get("title") or not u or u in live_urls or u in existing_urls:
            continue
        by_cat[it.get("category", "")].append(it)

    baomoi_rejects = []
    cats = sorted(by_cat, key=lambda c: REJECT_CATEGORY_ORDER.get(c, 9))
    while len(baomoi_rejects) < BAOMOI_REJECT_PER_RUN and any(by_cat[c] for c in cats):
        for c in cats:
            if len(baomoi_rejects) >= BAOMOI_REJECT_PER_RUN:
                break
            if not by_cat[c]:
                continue  # mục hết bài -> các mục khác lấp chỗ, vẫn đủ hạn mức
            it = by_cat[c].popleft()
            existing_urls.add(it["sourceUrl"])
            baomoi_rejects.append(
                {k: v for k, v in it.items() if k != "topic"}
                | {"reason": "Ứng viên Báo Mới không được chọn — 👍 để đưa vào bản tin", "addedAt": date}
            )

    # (b) Tin agent chủ động loại (sai ngày/không hợp gu) — GIÁ TRỊ HƠN nên được xếp trước và
    #     luôn còn ít nhất REJECTED_PER_RUN - BAOMOI_REJECT_PER_RUN slot.
    clean = []
    for it in rejected_new:
        if len(clean) >= REJECTED_PER_RUN - len(baomoi_rejects):
            break
        u = it.get("sourceUrl", "")
        if not it.get("title") or not u or u in live_urls or u in existing_urls:
            continue
        it.setdefault("reason", "")
        it["addedAt"] = date
        existing_urls.add(u)
        clean.append(it)

    # (c) Dọn mục cũ: bỏ mục đã nằm trong Bị loại quá REJECTED_KEEP_DAYS ngày. Mục cũ chưa có
    #     `addedAt` (từ trước khi thêm trường này) được đóng dấu ngày hôm nay để sống thêm 1 vòng,
    #     thay vì biến mất ngay lập tức.
    keep_from = ref - datetime.timedelta(days=REJECTED_KEEP_DAYS)
    kept_existing, pruned = [], 0
    for it in existing:
        stamp = it.get("addedAt")
        if not stamp:
            it["addedAt"] = date
            kept_existing.append(it)
            continue
        try:
            if parse_date(stamp) >= keep_from:
                kept_existing.append(it)
            else:
                pruned += 1
        except ValueError:
            it["addedAt"] = date
            kept_existing.append(it)

    rejected_added = len(clean) + len(baomoi_rejects)
    if rejected_added or pruned:
        data["rejectedNews"] = clean + baomoi_rejects + kept_existing

    # Chỉ đẩy generatedAt khi có nội dung BẢN TIN thật — lô chỉ có rejectedNews
    # (tin bị loại) KHÔNG được coi là "đã cập nhật bản tin" (tránh làm routine quét SKIP nhầm).
    content_added = bool(
        world_new or us_new or x_new or baomoi_new
        or exercise_items_added or dip_items_added or new_dip_events
    )
    if content_added:
        data["generatedAt"] = date
    if world_new or baomoi_new:
        data["worldGeneratedAt"] = date
    if us_new:
        data["usGeneratedAt"] = date
    if x_new:
        data["xGeneratedAt"] = date

    new_data_str = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    html_path.write_text(html[:start] + new_data_str + html[end:], encoding="utf-8")

    new_ev_note = f", +{len(new_dip_events)} SỰ KIỆN ngoại giao MỚI" if new_dip_events else ""
    rej_note = f", +{rejected_added} tin BỊ LOẠI (mục Bị loại)" if rejected_added else ""
    if pruned:
        rej_note += f" [-{pruned} mục cũ quá {REJECTED_KEEP_DAYS + 1} ngày]"
    bm_note = f", +{len(baomoi_new)} tin Báo Mới (📌 đã lưu)" if baomoi_new else ""
    print(
        f"OK: +{len(world_new)} tin Thế giới{bm_note}, +{len(us_new)} tin Mỹ, +{len(x_new)} tin X, "
        f"+{exercise_items_added} tin tập trận, +{dip_items_added} tin ngoại giao (sự kiện){new_ev_note}{rej_note}. generatedAt={date}"
    )
    for ev in new_dip_events:
        print(f"  [SỰ KIỆN MỚI] dipEvents += '{ev['name']}' ({ev['status']}, {len(ev['items'])} item)")
    # Cảnh báo (không chặn)
    warn_unknown_sources(new_items)
    warn_similar_titles(new_items, similar_warnings_data)
    print("Phân bổ category (batch vừa thêm):")
    world_ok = category_report(world_new, "worldNews") if world_new else True
    us_ok = category_report(us_new, "usNews") if us_new else True
    if not (world_ok and us_ok):
        print("=> Còn category thiếu tin (< 2). Nếu đã thử hết nguồn hợp lý, chấp nhận và nêu rõ trong tóm tắt cuối; nếu chưa, quét bổ sung rồi chạy lại script.")

    # ── SÀN CỨNG TỔNG NGÀY: worldNews ≥ FLOOR_DAY và usNews ≥ FLOOR_DAY tin ĐƯA LÊN trong ngày
    # (chỉ thị người dùng 23/07/2026 — tính cả 2 phiên sáng+tối). Đếm tin có _addedDate == ngày batch
    # trên DATA SAU khi chèn, nên gộp được phiên sáng và tăng dần qua từng vòng bổ sung. TÍN HIỆU,
    # KHÔNG chặn — việc lặp là của session điều phối (phiên tối phải kéo tổng ngày lên đủ FLOOR_DAY).
    w_cnt = sum(1 for it in data.get("worldNews", []) if it.get("_addedDate") == date)
    u_cnt = sum(1 for it in data.get("usNews", []) if it.get("_addedDate") == date)
    print(f"── SÀN CỨNG TỔNG NGÀY {date} (gộp cả sáng+tối, tăng dần qua từng vòng): "
          f"worldNews {w_cnt}/{FLOOR_DAY} · usNews {u_cnt}/{FLOOR_DAY}")
    if w_cnt < FLOOR_DAY or u_cnt < FLOOR_DAY:
        need = []
        if w_cnt < FLOOR_DAY:
            need.append(f"worldNews thiếu {FLOOR_DAY - w_cnt}")
        if u_cnt < FLOOR_DAY:
            need.append(f"usNews thiếu {FLOOR_DAY - u_cnt}")
        print(f"   ⚠️ CHƯA ĐẠT SÀN NGÀY ({', '.join(need)}). Phiên SÁNG: nhắm ~10/mục là đủ, để tối bù. "
              f"Phiên TỐI: CHƯA ĐỦ THÌ CHƯA DỪNG → giao thêm agent (nội bộ Mỹ mở toàn bộ = dư địa lớn nhất).")
    else:
        print("   ✅ ĐẠT SÀN NGÀY cả worldNews lẫn usNews.")
    if len(x_new) < 4:
        print(f"  xNews: {len(x_new)} tin  <-- THIẾU (mục tiêu 4-5)")
    if exercise_items_added < 1:
        print("  exercises: 0 tin cập nhật  <-- THIẾU (mục tiêu 1-2)")
    if dip_items_added < 1:
        print("  dipEvents: 0 tin cập nhật  <-- THIẾU (mục tiêu 1-2)")


if __name__ == "__main__":
    main()
