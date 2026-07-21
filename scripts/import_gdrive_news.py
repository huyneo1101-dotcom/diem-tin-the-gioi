#!/usr/bin/env python3
"""
Import news from Google Drive ban-tin-chien-luoc JSON files.

Tìm MỌI file ban-tin-chien-luoc-YYYY-MM-DD-HHMM-ICT.json trong khung 2 ngày
(hôm nay + hôm qua, giờ VN), tải hết, GỘP thành MỘT batch duy nhất (dedupe theo
URL, ưu tiên ấn bản mới nhất), rồi ghi ra /tmp/new_items.json cho add_news.py.

Requires:
  - GOOGLE_DRIVE_FOLDER_ID: Folder ID on Drive
  - GDRIVE_API_KEY: API key for Google Drive API (or service account JSON as base64)
"""

import os
import time
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
import sys

try:
    from googleapiclient.discovery import build
    from google.oauth2.service_account import Credentials
except ImportError as e:
    print(f"ERROR: Missing Google libraries: {e}")
    print("Run: pip install google-auth google-auth-oauthlib google-api-python-client")
    sys.exit(1)

FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
API_KEY = os.getenv("GDRIVE_API_KEY")

# Giờ VN — phải gọi tzset() thì datetime.now() mới thực sự đổi múi giờ trên Linux
os.environ["TZ"] = "Asia/Ho_Chi_Minh"
try:
    time.tzset()
except AttributeError:  # Windows
    pass

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = "/tmp/new_items.json"

NEWS_SECTIONS = ("worldNews", "usNews")
EVENT_UPDATE_SECTIONS = ("exerciseUpdates", "dipEventUpdates")

_log_lines = []


def log(msg: str) -> None:
    """In ra stdout (cho Action log) VÀ gom lại để ghi vào logs/gdrive-<ngày>.log."""
    print(msg)
    _log_lines.append(msg)


def flush_log(status: str) -> None:
    """Ghi log ngày + cập nhật cờ pipeline 'drive-import' trong logs/state.json.

    Cờ nằm RIÊNG khỏi DATA.generatedAt: generatedAt là ngày bản tin hiển thị trên web,
    không phải cờ "pipeline nào đã chạy" (xem scripts/state.py).
    """
    today = datetime.now().strftime("%Y-%m-%d")
    hhmm = datetime.now().strftime("%H:%M")
    log_path = REPO_ROOT / "logs" / f"gdrive-{today}.log"
    detail = " | ".join(_log_lines)
    try:
        log_path.parent.mkdir(exist_ok=True)
        header = "" if log_path.exists() else f"# Log nhap ban tin tu Google Drive - {today} (gio VN)\n"
        with log_path.open("a", encoding="utf-8") as f:
            f.write(f"{header}[{hhmm} VN] {status} (GitHub Action) {detail}\n")
    except Exception as e:  # log không được thì cũng đừng làm hỏng job
        print(f"WARN: khong ghi duoc log: {e}")
    try:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import state

        state.STATE_PATH = REPO_ROOT / "logs" / "state.json"
        state.record("drive-import", status, detail[:300])
    except Exception as e:
        print(f"WARN: khong cap nhat duoc state.json: {e}")


def get_vn_dates():
    """Hôm nay + hôm qua theo giờ VN (YYYY-MM-DD)."""
    now = datetime.now()
    return [now.strftime("%Y-%m-%d"), (now - timedelta(days=1)).strftime("%Y-%m-%d")]


def build_drive_service():
    if not API_KEY:
        print("ERROR: GDRIVE_API_KEY not set")
        sys.exit(1)
    try:
        if API_KEY.startswith("AIza"):
            return build("drive", "v3", developerKey=API_KEY)
        # Service account JSON dạng base64
        import base64

        try:
            sa_json = json.loads(base64.b64decode(API_KEY))
            creds = Credentials.from_service_account_info(
                sa_json, scopes=["https://www.googleapis.com/auth/drive.readonly"]
            )
            return build("drive", "v3", credentials=creds)
        except Exception as e:
            print(f"WARN: Service account decode failed ({e}), falling back to API key")
            return build("drive", "v3", developerKey=API_KEY)
    except Exception as e:
        print(f"ERROR: Cannot build Drive service: {e}")
        sys.exit(1)


def download_file(service, file_id):
    try:
        content = service.files().get_media(fileId=file_id).execute()
        return json.loads(content.decode("utf-8"))
    except Exception as e:
        log(f"WARN: tai/parse that bai {file_id}: {e}")
        return None


def search_news_files(service, folder_id, dates):
    """Tìm TẤT CẢ file ban-tin-chien-luoc của các ngày trong khung (không lọc bớt)."""
    results = []
    for date_str in dates:
        try:
            query = (
                f"'{folder_id}' in parents and trashed=false "
                f"and name contains 'ban-tin-chien-luoc-{date_str}'"
            )
            files = (
                service.files()
                .list(q=query, spaces="drive", fields="files(id, name, modifiedTime, mimeType)", pageSize=25)
                .execute()
                .get("files", [])
            )
            for f in files:
                if f["name"].endswith(".json"):
                    results.append(
                        {"id": f["id"], "name": f["name"], "date_str": date_str, "modified": f.get("modifiedTime")}
                    )
        except Exception as e:
            log(f"WARN: tim file ngay {date_str} loi: {e}")
    return results


def edition_key(f):
    """Khoá sắp xếp ấn bản: (ngày, giờ phát hành trong tên file). Mới nhất = lớn nhất."""
    m = re.search(r"(\d{4}-\d{2}-\d{2})-(\d{4})", f["name"])
    if m:
        return (m.group(1), m.group(2))
    return (f["date_str"], "0000")


def get_existing_urls():
    """Mọi sourceUrl/url đã có trong index.html — để không nhập lại tin cũ."""
    index_path = REPO_ROOT / "index.html"
    if not index_path.exists():
        return set()
    try:
        content = index_path.read_text(encoding="utf-8")
        return set(re.findall(r'"(?:sourceUrl|url)":"([^"]+)"', content))
    except Exception as e:
        log(f"WARN: khong doc duoc URL cu: {e}")
        return set()


def merge_batches(batches, existing_urls, window):
    """Gộp nhiều file bản tin thành MỘT batch.

    batches: list các dict bản tin, đã sắp MỚI NHẤT TRƯỚC (bản mới thắng khi trùng URL).
    window: set các ngày (YYYY-MM-DD) được phép — item ngoài khung bị đẩy sang rejectedNews
            thay vì để add_news.py chặn cả lô.
    """
    out = {
        "date": max(window),
        "worldNews": [],
        "usNews": [],
        "xNews": [],
        "exerciseUpdates": [],
        "dipEventUpdates": [],
        "newDipEvents": [],
        "rejectedNews": [],
    }
    seen = set(existing_urls)  # URL đã dùng: trong index.html hoặc đã nhận ở lô này
    stats = {"trung": 0, "ngoai_khung": 0, "thieu_url": 0}

    def take(item, url_field):
        """True nếu item hợp lệ & chưa trùng → nhận. Ngược lại ghi lý do."""
        url = item.get(url_field)
        if not url:
            stats["thieu_url"] += 1
            return False
        if url in seen:
            stats["trung"] += 1
            return False
        if item.get("date") not in window:
            stats["ngoai_khung"] += 1
            out["rejectedNews"].append(
                {**item, "sourceUrl": url, "reason": f"ngoài khung 2 ngày ({item.get('date')})"}
            )
            seen.add(url)
            return False
        seen.add(url)
        return True

    updates_by_name = {k: {} for k in EVENT_UPDATE_SECTIONS}
    new_events_by_name = {}

    for batch in batches:
        for section in NEWS_SECTIONS:
            for item in batch.get(section, []):
                if take(item, "sourceUrl"):
                    out[section].append(item)

        for item in batch.get("xNews", []):
            if take(item, "url"):
                out["xNews"].append(item)

        # Cập nhật sự kiện: gộp theo tên, item dedupe theo sourceUrl
        for section in EVENT_UPDATE_SECTIONS:
            for upd in batch.get(section, []):
                name = upd.get("name")
                if not name:
                    continue
                items = [it for it in upd.get("items", []) if take(it, "sourceUrl")]
                if items:
                    updates_by_name[section].setdefault(name, []).extend(items)

        # Sự kiện ngoại giao mới: dedupe theo tên (bản mới nhất thắng)
        for ev in batch.get("newDipEvents", []):
            name = ev.get("name")
            if not name or name in new_events_by_name:
                continue
            items = [it for it in ev.get("items", []) if take(it, "sourceUrl")]
            if items:
                new_events_by_name[name] = {**ev, "items": items}

        # Tin bị loại sẵn trong file nguồn
        out["rejectedNews"].extend(batch.get("rejectedNews", []))

    for section in EVENT_UPDATE_SECTIONS:
        out[section] = [{"name": n, "items": items} for n, items in updates_by_name[section].items()]
    out["newDipEvents"] = list(new_events_by_name.values())

    return out, stats


def main():
    if not FOLDER_ID:
        print("ERROR: GOOGLE_DRIVE_FOLDER_ID not set")
        sys.exit(1)

    vn_dates = get_vn_dates()
    window = set(vn_dates)
    service = build_drive_service()

    files = search_news_files(service, FOLDER_ID, vn_dates)
    if not files:
        log(f"khong tim thay file ban-tin-chien-luoc nao cho {', '.join(vn_dates)}")
        flush_log("SKIP")
        return 0

    # Mới nhất trước — khi trùng URL thì bản mới thắng, và tin mới nằm đầu danh sách
    files.sort(key=edition_key, reverse=True)
    log(f"tim thay {len(files)} file: {', '.join(f['name'] for f in files)}")

    existing_urls = get_existing_urls()
    batches = [b for b in (download_file(service, f["id"]) for f in files) if b]
    if not batches:
        log("tai duoc 0 file hop le")
        flush_log("FAIL")
        return 0

    merged, stats = merge_batches(batches, existing_urls, window)

    total = len(merged["worldNews"]) + len(merged["usNews"]) + len(merged["xNews"])
    ev_items = sum(len(u["items"]) for s in EVENT_UPDATE_SECTIONS for u in merged[s])
    ev_items += sum(len(e["items"]) for e in merged["newDipEvents"])

    if total == 0 and ev_items == 0:
        log(
            f"khong co tin moi (trung {stats['trung']}, ngoai khung {stats['ngoai_khung']}, "
            f"thieu url {stats['thieu_url']})"
        )
        Path(OUTPUT_PATH).unlink(missing_ok=True)
        flush_log("SKIP")
        return 0

    Path(OUTPUT_PATH).write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    log(
        f"nhan TG+{len(merged['worldNews'])} My+{len(merged['usNews'])} X+{len(merged['xNews'])}, "
        f"{ev_items} item su kien ({len(merged['newDipEvents'])} su kien moi); "
        f"loai: trung {stats['trung']}, ngoai khung {stats['ngoai_khung']}, thieu url {stats['thieu_url']}"
    )
    flush_log("DONE")
    return total


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(1)
    except Exception as e:
        import traceback

        traceback.print_exc()
        log(f"loi: {e}")
        flush_log("FAIL")
        sys.exit(1)
