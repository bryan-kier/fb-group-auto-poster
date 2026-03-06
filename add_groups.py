"""
add_groups.py — Utility to add Facebook groups to your target list.

Usage:
    python add_groups.py

Paste Facebook group URLs (one per line).
Press ENTER on an empty line when done.

Supported formats:
    https://www.facebook.com/groups/groupname
    https://www.facebook.com/groups/1234567890
    https://facebook.com/groups/groupname/
    facebook.com/groups/groupname
"""

import json
import re
import os
from os import path
from configs import PROJECT_ROOT, ensure_dirs

GROUPS_PATH = path.join(PROJECT_ROOT, "sessions", "groups.json")


def parse_group_url(url: str) -> dict | None:
    """Extract the group username/ID from a Facebook group URL."""
    url = url.strip().rstrip("/")

    # Match: facebook.com/groups/<slug_or_id>
    match = re.search(r"facebook\.com/groups/([^/?#\s]+)", url, re.IGNORECASE)
    if match:
        username = match.group(1)
        return {
            "name": username,   # Use slug as name; edit manually if needed
            "username": username,
            "status": "straight"
        }

    return None


def load_existing() -> list:
    if path.exists(GROUPS_PATH):
        with open(GROUPS_PATH, "r") as f:
            return json.load(f)
    return []


def save_groups(groups: list):
    ensure_dirs()
    with open(GROUPS_PATH, "w") as f:
        json.dump(groups, f, indent=2)


def main():
    print("\n" + "="*55)
    print("  📋 Facebook Group Manager")
    print("  Paste group URLs below, one per line.")
    print("  Press ENTER on an empty line when done.")
    print("="*55 + "\n")

    existing = load_existing()
    existing_usernames = {g["username"] for g in existing}

    raw_lines = []
    while True:
        line = input("  URL: ").strip()
        if not line:
            break
        raw_lines.append(line)

    added = []
    skipped_dups = []
    invalid = []

    for line in raw_lines:
        parsed = parse_group_url(line)
        if not parsed:
            invalid.append(line)
        elif parsed["username"] in existing_usernames:
            skipped_dups.append(parsed["username"])
        else:
            existing.append(parsed)
            existing_usernames.add(parsed["username"])
            added.append(parsed["username"])

    save_groups(existing)

    print("\n" + "="*55)
    print(f"  ✅ Added:        {len(added)} group(s)")
    if added:
        for u in added:
            print(f"     + {u}")
    if skipped_dups:
        print(f"  ⏭  Duplicates:  {len(skipped_dups)} skipped")
    if invalid:
        print(f"  ❌ Invalid URLs: {len(invalid)} skipped")
        for u in invalid:
            print(f"     - {u}")
    print(f"\n  📁 Total groups in list: {len(existing)}")
    print(f"  Saved to: {GROUPS_PATH}")
    print("="*55 + "\n")


if __name__ == "__main__":
    main()
