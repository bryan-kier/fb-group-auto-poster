# 🚀 fb-group-auto-poster

A high-performance automation suite for programmatic content distribution across Facebook groups. Built with **Python** and **Playwright** for reliability and human-like interaction.

---

## ✨ Core Capabilities

- **⚡️ Rapid Distribution**: Post content to hundreds of groups in a single session.
- **🛡️ Stealth Mode**: Randomized typing speeds, browsing breaks, and human-like delays to minimize detection.
- **🍪 Session Preservation**: Persistent cookie management to bypass constant logins.
- **📊 Activity Logging**: Real-time tracking of successful posts and automated cycle resets.
- **🎯 Precision Targeting**: Easily configurable group queues via JSON.

---

## 🛠 Setup Guide

### Step 1 — Install Python
Download and install [**Python 3.9+**](https://www.python.org/downloads/) if you don't have it already.

### Step 2 — Get the Code
**Option A: Using Git**
```bash
git clone https://github.com/bryan-kier/fb-group-auto-poster.git
cd fb-group-auto-poster
```
**Option B: No Git? Download ZIP**
Go to the repo page → click **Code** → **Download ZIP** → unzip it → open a terminal inside the folder.

### Step 3 — Install Dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### Step 4 — Add Your Target Groups
Open `sessions/groups.json` (auto-created on first run) and add your target Facebook groups:
```json
[
  {
    "name": "Group Name",
    "username": "group_slug_or_id",
    "status": "straight"
  }
]
```
- `straight` — Posts directly.
- `pending` — Submits for admin approval.

### Step 5 — Run It
```bash
python main.py
```
- **First run**: A browser window will open automatically. Log in to Facebook, wait for your feed to load, then press **ENTER** in the terminal. Your session is saved for future runs.
- **Every run after**: Just run the script and enter your post content when prompted. That's it.

---

## ⚙️ Advanced Options

| Setting | Default | What it does |
|---|---|---|
| `MIN_DELAY_BETWEEN_GROUPS` | 5s | Minimum pause between posts |
| `MAX_DELAY_BETWEEN_GROUPS` | 10s | Maximum pause between posts |
| `MIN_TYPING_DELAY` | 10ms | Minimum keystroke delay |
| `MAX_TYPING_DELAY` | 50ms | Maximum keystroke delay |
| `MAX_GROUPS_PER_SESSION` | 9999 | Max groups posted per run |
| `CREATE_SESSION` | `False` | Set to `True` to force re-login |

---

> **Note:** All private data (cookies, group lists, logs) is stored in `sessions/` which is Git-ignored and never uploaded.
