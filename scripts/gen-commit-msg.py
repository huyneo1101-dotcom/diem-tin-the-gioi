#!/usr/bin/env python3
"""Generate commit message based on tin counts in /tmp/new_items.json."""

import json
from pathlib import Path
from datetime import datetime

try:
    data = json.loads(Path("/tmp/new_items.json").read_text())
except FileNotFoundError:
    print("Nhap ban tin tu Google Drive (auto-sync)")
    exit(0)

world = len(data.get("worldNews", []))
us = len(data.get("usNews", []))
x = len(data.get("xNews", []))
dip_updates = len(data.get("dipEventUpdates", []))
new_dip = len(data.get("newDipEvents", []))

date_str = data.get("date", datetime.now().strftime("%d/%m"))

parts = [f"Nhap ban tin tu Drive {date_str}"]
tin_parts = []
if world:
    tin_parts.append(f"TG +{world}")
if us:
    tin_parts.append(f"My +{us}")
if x:
    tin_parts.append(f"X +{x}")

if tin_parts:
    parts.append(f": {', '.join(tin_parts)}")

if dip_updates:
    parts.append(f" + cap nhat {dip_updates} su kien")
if new_dip:
    parts.append(f" + {new_dip} su kien moi")

print("".join(parts))
