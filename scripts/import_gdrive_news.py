#!/usr/bin/env python3
"""
Import news from Google Drive ban-tin-chien-luoc JSON files.
Searches for files from the last 2 days (VN time), downloads, deduplicates, and saves to /tmp/new_items.json.

Requires:
  - GOOGLE_DRIVE_FOLDER_ID: Folder ID on Drive
  - GDRIVE_API_KEY: API key for Google Drive API (or service account JSON as base64)
  - TZ: Set to Asia/Ho_Chi_Minh for correct date handling
"""

import os
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import sys

try:
    from google.auth.transport.requests import Request
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
except ImportError as e:
    print(f"ERROR: Missing Google libraries: {e}")
    print("Run: pip install google-auth google-auth-oauthlib google-api-python-client")
    sys.exit(1)

# Get folder ID from env
FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
API_KEY = os.getenv("GDRIVE_API_KEY")

if not FOLDER_ID:
    print("ERROR: GOOGLE_DRIVE_FOLDER_ID not set")
    sys.exit(1)

# Set timezone to VN
os.environ["TZ"] = "Asia/Ho_Chi_Minh"

def get_vn_dates():
    """Get today and yesterday dates in VN timezone (YYYY-MM-DD format)."""
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    return [today, yesterday]

def build_drive_service():
    """Build Google Drive API service."""
    try:
        # Try using API key (simplest, but read-only)
        if API_KEY and API_KEY.startswith("AIza"):
            return build("drive", "v3", developerKey=API_KEY)

        # Try service account JSON from env (base64 encoded)
        if API_KEY and not API_KEY.startswith("AIza"):
            import base64
            try:
                sa_json = json.loads(base64.b64decode(API_KEY))
                creds = Credentials.from_service_account_info(sa_json, scopes=["https://www.googleapis.com/auth/drive.readonly"])
                return build("drive", "v3", credentials=creds)
            except Exception as e:
                print(f"WARN: Service account decode failed ({e}), falling back to API key")
                return build("drive", "v3", developerKey=API_KEY)
    except Exception as e:
        print(f"ERROR: Cannot build Drive service: {e}")
        sys.exit(1)

def download_file(service, file_id):
    """Download file content from Drive as JSON."""
    try:
        request = service.files().get_media(fileId=file_id)
        content = request.execute()
        return json.loads(content.decode("utf-8"))
    except Exception as e:
        print(f"WARN: Failed to download {file_id}: {e}")
        return None

def search_news_files(service, folder_id, dates):
    """Search for ban-tin-chien-luoc files from last 2 days in VN TZ."""
    file_pattern_prefix = "ban-tin-chien-luoc-"
    results = []

    for date_str in dates:
        try:
            # Search for files matching the pattern
            query = f"'{folder_id}' in parents and trashed=false and name contains '{file_pattern_prefix}{date_str}'"
            files = service.files().list(
                q=query,
                spaces="drive",
                fields="files(id, name, modifiedTime, mimeType)",
                pageSize=10
            ).execute().get("files", [])

            for file in files:
                if file["mimeType"] == "application/json":
                    results.append({
                        "id": file["id"],
                        "name": file["name"],
                        "date_str": date_str,
                        "modified": file.get("modifiedTime")
                    })
                    print(f"Found: {file['name']} (modified: {file.get('modifiedTime')})")
        except Exception as e:
            print(f"WARN: Search for {date_str} failed: {e}")

    return results

def extract_edition_time(filename):
    """Extract edition time from filename (e.g., 2026-07-21-2000 -> 20:00)."""
    # Pattern: ban-tin-chien-luoc-YYYY-MM-DD-HHMM-ICT.json
    parts = filename.replace(".json", "").split("-")
    if len(parts) >= 5:
        hhmm = parts[-2]  # -2 because last is "ICT"
        if len(hhmm) == 4 and hhmm.isdigit():
            return f"{hhmm[0:2]}:{hhmm[2:4]}"
    return "unknown"

def get_existing_urls():
    """Extract all existing URLs from index.html to prevent duplicates."""
    index_path = Path("index.html")
    if not index_path.exists():
        return set()

    try:
        content = index_path.read_text()
        # Simple grep for sourceUrl
        import re
        urls = set(re.findall(r'"sourceUrl":"([^"]+)"', content))
        return urls
    except Exception as e:
        print(f"WARN: Could not read existing URLs: {e}")
        return set()

def process_and_save_batch(batch_data, existing_urls, output_path="/tmp/new_items.json"):
    """Process batch, deduplicate, and save to output."""
    if not batch_data:
        return None

    processed = {
        "date": batch_data.get("date", datetime.now().strftime("%Y-%m-%d")),
        "worldNews": [],
        "usNews": [],
        "xNews": [],
        "dipEventUpdates": [],
        "newDipEvents": [],
        "exerciseUpdates": [],
        "rejectedNews": []
    }

    # Process world news
    for item in batch_data.get("worldNews", []):
        if item.get("sourceUrl") not in existing_urls:
            processed["worldNews"].append(item)
        else:
            processed["rejectedNews"].append({**item, "reason": "URL trùng"})

    # Process US news
    for item in batch_data.get("usNews", []):
        if item.get("sourceUrl") not in existing_urls:
            processed["usNews"].append(item)
        else:
            processed["rejectedNews"].append({**item, "reason": "URL trùng"})

    # Process X news (if present)
    for item in batch_data.get("xNews", []):
        if item.get("url") not in existing_urls:
            processed["xNews"].append(item)

    # Pass through other sections (dipEventUpdates, newDipEvents, exerciseUpdates)
    processed["dipEventUpdates"] = batch_data.get("dipEventUpdates", [])
    processed["newDipEvents"] = batch_data.get("newDipEvents", [])
    processed["exerciseUpdates"] = batch_data.get("exerciseUpdates", [])
    processed["rejectedNews"].extend(batch_data.get("rejectedNews", []))

    # Save to output
    Path(output_path).write_text(json.dumps(processed, ensure_ascii=False, indent=2))

    # Log summary
    total = len(processed["worldNews"]) + len(processed["usNews"]) + len(processed["xNews"])
    print(f"✓ Processed: {len(processed['worldNews'])} world + {len(processed['usNews'])} US + {len(processed['xNews'])} X news")
    if processed["rejectedNews"]:
        print(f"  Loại: {len(processed['rejectedNews'])} tin")

    return total

def main():
    print("=" * 60)
    print("Import news from Google Drive")
    print("=" * 60)

    # Get VN dates
    vn_dates = get_vn_dates()
    print(f"Searching for files from: {', '.join(vn_dates)}")

    # Build Drive service
    print("Connecting to Google Drive...")
    service = build_drive_service()

    # Search for files
    files = search_news_files(service, FOLDER_ID, vn_dates)

    if not files:
        print("No news files found on Drive.")
        return 0

    # Get existing URLs
    existing_urls = get_existing_urls()
    print(f"Existing URLs to avoid: {len(existing_urls)}")

    # Download and process files
    # Prefer newer editions (evening > morning for same date)
    files_by_date = {}
    for f in files:
        date = f["date_str"]
        edition_time = extract_edition_time(f["name"])

        if date not in files_by_date or edition_time > files_by_date[date]["time"]:
            files_by_date[date] = {**f, "time": edition_time}

    total_new = 0
    for date_str, file_info in sorted(files_by_date.items(), reverse=True):
        print(f"\nProcessing: {file_info['name']} ({file_info['time']})")
        batch = download_file(service, file_info["id"])

        if batch:
            count = process_and_save_batch(batch, existing_urls)
            if count:
                total_new += count

    print("\n" + "=" * 60)
    if total_new > 0:
        print(f"✓ Total new items: {total_new}")
        print(f"Saved to: /tmp/new_items.json")
    else:
        print("No new items to import.")
    print("=" * 60)

    return total_new

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
