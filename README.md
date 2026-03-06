# 🚀 fb-group-auto-post

A high-performance automation suite for programmatic content distribution across Facebook groups. Built with **Python** and **Playwright** for reliability and human-like interaction.

---

## ✨ Core Capabilities

- **⚡️ Rapid Distribution**: Post content to hundreds of groups in a single session.
- **🛡️ Stealth Mode**: Randomized typing speeds, browsing breaks, and human-like delays to minimize detection.
- **🍪 Session Preservation**: Persistent cookie management to bypass constant logins and 2FA.
- **📊 Activity Logging**: Real-time tracking of successful posts and automated cycle resets.
- **� Precision Targeting**: Easily configurable group queues via JSON.

---

## 🛠 Installation

### 1. Requirements
Ensure you have [**Python 3.9+**](https://www.python.org/downloads/) installed on your system.

### 2. Setup Dependencies
```bash
# Install the core library and dependencies
pip install -r requirements.txt

# Download the required browser engine
playwright install chromium
```

---

## 🚦 Getting Started

### 1. Launch the Engine
Simply run the main script:
```bash
python main.py
```

### 2. First-Time Onboarding
The tool is designed for **Zero-Friction**:
- **Login**: If no session is found, it will automatically open a browser for you to log in. Once you're in, hit **ENTER** in your terminal to save your cookies.
- **Group List**: If you haven't set up your groups, it will automatically create `sessions/groups.json` using the template. Just add your target group IDs to that file.

---

## ⚙️ Configuration

### 🛡 User Data Isolation
- **Private Data**: Everything stored in the `sessions/` directory (cookies, real group lists, logs) is **ignored by Git** and will never be pushed to your repository.
- **Manual Account Switch**: If you ever want to re-login or switch accounts, set `CREATE_SESSION = True` in `main.py` temporarily.

### 📊 Operational Safety (`main.py`)
Fine-tune the "humanity" of the bot:
- `MIN_DELAY_BETWEEN_GROUPS`: Minimum rest interval between groups.
- `MIN_TYPING_DELAY`: Variance in keystroke speed.
- `MAX_GROUPS_PER_SESSION`: Daily safety cap.
