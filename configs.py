from os import path
from json import load
import typing

import os

SOCIAL_MAPS = {
    "facebook": {
        "login": "https://www.facebook.com/login",
        "filename": "facebook-cookies.json",
    }
}

# Robust path detection
PROJECT_ROOT = path.dirname(path.abspath(__file__))

def ensure_dirs():
    """Ensure required directories exist for a fresh setup."""
    sessions_dir = path.join(PROJECT_ROOT, "sessions")
    if not path.exists(sessions_dir):
        os.makedirs(sessions_dir)
        print(f"[*] Created missing directory: {sessions_dir}")


import shutil

def get_sources_list() -> typing.List:
    # 1. Look for private list in sessions (ignored by git)
    private_path = path.join(PROJECT_ROOT, "sessions", "groups.json")
    # 2. Look for legacy groups.json in root (also ignored)
    legacy_path = path.join(PROJECT_ROOT, "groups.json")
    # 3. Reference example
    example_path = path.join(PROJECT_ROOT, "groups.example.json")

    # Auto-initialize if completely empty
    if not path.exists(private_path) and not path.exists(legacy_path):
        ensure_dirs()
        shutil.copy(example_path, private_path)
        print(f"[*] Initialized your private group list at: {private_path}")
        print("[!] Edit that file to add your actual target groups.")

    target_path = private_path if path.exists(private_path) else legacy_path
    
    with open(target_path, "r") as sources_file:
        return load(sources_file)
