"""Reads and writes everything under sessions/: settings, groups, posted log, cookies."""

import json
import re
from os import path, remove

from configs import PROJECT_ROOT, SOCIAL_MAPS, ensure_dirs

SESSIONS_DIR = path.join(PROJECT_ROOT, "sessions")
SETTINGS_PATH = path.join(SESSIONS_DIR, "settings.json")
GROUPS_PATH = path.join(SESSIONS_DIR, "groups.json")
POSTED_LOG_PATH = path.join(SESSIONS_DIR, "posted_log.json")
COOKIE_PATH = path.join(SESSIONS_DIR, SOCIAL_MAPS["facebook"]["filename"])

DEFAULT_SETTINGS = {
    "min_delay_between_groups": 60,     # seconds
    "max_delay_between_groups": 180,
    "min_typing_delay": 10,             # ms per keystroke
    "max_typing_delay": 50,
    "max_groups_per_session": 9999,
    "browsing_break_every": 10,         # 0 disables
    "intro_chance": 50,                 # % of posts that get a random intro
    "intros": [
        "Check this out!",
        "Sharing this here 🏡",
        "For anyone looking 👇",
    ],
    "composer_texts": [
        "Write something...",
        "Isulat ang isang bagay",
        "What's on your mind",
    ],
}

_NUMERIC = {
    "min_delay_between_groups": (0, 3600),
    "max_delay_between_groups": (0, 3600),
    "min_typing_delay": (0, 2000),
    "max_typing_delay": (0, 2000),
    "max_groups_per_session": (1, 100000),
    "browsing_break_every": (0, 1000),
    "intro_chance": (0, 100),
}


def _read_json(file_path, default):
    if not path.exists(file_path):
        return default
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def _write_json(file_path, data):
    ensure_dirs()
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)


# --- settings ---------------------------------------------------------------

def sanitize_settings(raw: dict) -> dict:
    out = dict(DEFAULT_SETTINGS)
    for key, (lo, hi) in _NUMERIC.items():
        try:
            out[key] = max(lo, min(hi, int(float(raw.get(key, out[key])))))
        except (TypeError, ValueError):
            pass
    for lo_key, hi_key in (
        ("min_delay_between_groups", "max_delay_between_groups"),
        ("min_typing_delay", "max_typing_delay"),
    ):
        if out[lo_key] > out[hi_key]:
            out[lo_key], out[hi_key] = out[hi_key], out[lo_key]
    for key in ("intros", "composer_texts"):
        value = raw.get(key)
        if isinstance(value, list):
            cleaned = [str(v).replace('"', "").strip() for v in value]
            out[key] = [v for v in cleaned if v]
    if not out["composer_texts"]:
        out["composer_texts"] = list(DEFAULT_SETTINGS["composer_texts"])
    return out


def load_settings() -> dict:
    return sanitize_settings(_read_json(SETTINGS_PATH, {}))


def save_settings(raw: dict) -> dict:
    settings = sanitize_settings(raw)
    _write_json(SETTINGS_PATH, settings)
    return settings


# --- groups -----------------------------------------------------------------

def parse_group_url(url: str):
    match = re.search(r"facebook\.com/groups/([^/?#\s]+)", url.strip(), re.IGNORECASE)
    return match.group(1) if match else None


def load_groups() -> list:
    groups = _read_json(GROUPS_PATH, None)
    if groups is None:
        groups = _read_json(path.join(PROJECT_ROOT, "groups.json"), [])
    return groups if isinstance(groups, list) else []


def save_groups(groups: list) -> list:
    seen, cleaned = set(), []
    for g in groups:
        username = str(g.get("username", "")).strip()
        if not username or username in seen:
            continue
        seen.add(username)
        status = g.get("status") if g.get("status") in ("straight", "pending") else "straight"
        cleaned.append({
            "name": str(g.get("name") or username).strip(),
            "username": username,
            "status": status,
        })
    _write_json(GROUPS_PATH, cleaned)
    return cleaned


def add_groups_from_text(text: str) -> dict:
    """Parse pasted URLs (one per line) and append new groups."""
    groups = load_groups()
    known = {g["username"] for g in groups}
    added, duplicates, invalid = [], [], []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        username = parse_group_url(line)
        if not username:
            invalid.append(line)
        elif username in known:
            duplicates.append(username)
        else:
            known.add(username)
            groups.append({"name": username, "username": username, "status": "straight"})
            added.append(username)
    save_groups(groups)
    return {"added": added, "duplicates": duplicates, "invalid": invalid}


# --- posted log / session ---------------------------------------------------

def load_posted_log() -> dict:
    data = _read_json(POSTED_LOG_PATH, {})
    return data if isinstance(data, dict) else {}


def save_posted_log(data: dict):
    _write_json(POSTED_LOG_PATH, data)


def has_session() -> bool:
    return path.exists(COOKIE_PATH)


def delete_session():
    if path.exists(COOKIE_PATH):
        remove(COOKIE_PATH)
