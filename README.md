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
Ensure you have **Python 3.9+** installed on your system.

### 2. Setup Dependencies
```bash
# Install the core library and dependencies
pip install -r requirements.txt

# Download the required browser engine
playwright install chromium
```

---

## 🚦 Getting Started

### Initial Session (Login)
Before running automation, you must capture a valid browser session.
1. Open `main.py`.
2. Locate `CREATE_SESSION = False` and change it to `True`.
3. Run the script:
   ```bash
   python main.py
   ```
4. A browser window will open. Log in to your account manually and wait for the feed to load.
5. Return to the terminal and press **ENTER**. Your session is now saved in `sessions/facebook-cookies.json`.

### Automation Mode
Once the session is saved, toggle the setting back:
1. Set `CREATE_SESSION = False` in `main.py`.
2. Run `python main.py`.
3. Enter your message or link when prompted.

---

## ⚙️ Configuration

### 🛡 Zero-Friction & Privacy-First
This tool is designed for **public sharing with private data**. 
- On the first run, the script creates a `sessions/` folder (which is ignored by Git).
- It automatically copies `groups.example.json` to `sessions/groups.json`.
- **Your Work**: Just edit `sessions/groups.json` with your real target list. It will persist locally and will **never** be pushed to GitHub.

### 📊 Operational Safety (`main.py`)
Fine-tune the "humanity" of the bot:
- `MIN_DELAY_BETWEEN_GROUPS`: Minimum rest interval between groups.
- `MIN_TYPING_DELAY`: Variance in keystroke speed.
- `MAX_GROUPS_PER_SESSION`: Daily safety cap.

---

## ⚠️ Disclaimer
This tool is for educational and personal efficiency purposes only. Automating social media platforms carries risks of account restriction. Use responsibly and stay within platform guidelines.

---

**Developed by Bryan Kier**  
*Efficiency through automation.*

