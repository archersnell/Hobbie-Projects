"""
Persists seen alert IDs so restarts do not resend duplicate notifications.
"""

import json
import os
from datetime import datetime, timedelta


STATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
SEEN_ITEMS_PATH = os.path.join(STATE_DIR, "seen_items.json")
MAX_ITEM_AGE_DAYS = 30


# Reads the seen-items log from disk.
def load_seen_items() -> dict:
    if not os.path.exists(SEEN_ITEMS_PATH):
        return {}

    try:
        with open(SEEN_ITEMS_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[state] Could not read seen-items log: {exc}")
        return {}


# Writes the seen-items log to disk.
def save_seen_items(seen_items: dict) -> None:
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(SEEN_ITEMS_PATH, "w") as f:
        json.dump(seen_items, f, indent=2)


# Removes old seen-item IDs to keep the log small.
def prune_seen_items(seen_items: dict) -> dict:
    cutoff = datetime.now() - timedelta(days=MAX_ITEM_AGE_DAYS)
    pruned = {}

    for item_id, timestamp in seen_items.items():
        try:
            if datetime.fromisoformat(timestamp) >= cutoff:
                pruned[item_id] = timestamp
        except (TypeError, ValueError):
            continue

    return pruned


# Returns True if an alert ID has already been handled.
def has_seen_item(item_id: str) -> bool:
    return item_id in load_seen_items()


# Marks an alert ID as handled and persists it.
def mark_item_seen(item_id: str) -> None:
    seen_items = prune_seen_items(load_seen_items())
    seen_items[item_id] = datetime.now().isoformat(timespec="seconds")
    save_seen_items(seen_items)
