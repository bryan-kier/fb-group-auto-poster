from playwright.sync_api import sync_playwright
from configs import *
from datetime import datetime
from os import path
import json
import time
import random
import re
import os

# Safety settings
MIN_DELAY_BETWEEN_GROUPS = 5     # minimum seconds between posts
MAX_DELAY_BETWEEN_GROUPS = 10    # maximum seconds between posts
MIN_TYPING_DELAY = 10            # min ms delay between keystrokes
MAX_TYPING_DELAY = 50            # max ms delay between keystrokes
MAX_GROUPS_PER_SESSION = 9999    # process all groups

# Global post content - set at runtime
POST_CONTENT = ""


class FacebookGroupSpam:
    CREATE_SESSION = False

    def __init__(self) -> None:
        ensure_dirs()
        p = sync_playwright().start()
        self.browser = p.chromium.launch(headless=False)
        self.context = self.browser.new_context(no_viewport=True)
        self.page = self.context.new_page()

        cookie_path = path.join(PROJECT_ROOT, "sessions", SOCIAL_MAPS["facebook"]["filename"])

        # Auto-detect login: If no cookie exists, or user forces it via CREATE_SESSION
        if not path.exists(cookie_path) or self.CREATE_SESSION:
            self.generate_cookie()
        else:
            self.load_cookie()
            self.post_to_groups()
        self.page.close()
        self.context.close()

    def human_delay(self, min_ms=500, max_ms=1000):
        """Random short delay to simulate human behaviour"""
        time.sleep(random.uniform(min_ms / 1000, max_ms / 1000))

    def human_browsing_break(self):
        """Visit a random Facebook page to simulate human browsing between posts"""
        random_pages = [
            "https://www.facebook.com",
            "https://www.facebook.com/marketplace",
            "https://www.facebook.com/watch",
            "https://www.facebook.com/groups/feed",
            "https://www.facebook.com/gaming",
            "https://www.facebook.com/news",
        ]
        page = random.choice(random_pages)
        print(f"\t[*] Taking a human break, browsing Facebook...")
        self.page.goto(page, wait_until="domcontentloaded")

        scrolls = random.randint(2, 4)
        for _ in range(scrolls):
            scroll_amount = random.randint(300, 800)
            self.page.mouse.wheel(0, scroll_amount)
            time.sleep(random.uniform(1.0, 2.5))

        if random.random() > 0.5:
            self.page.mouse.wheel(0, -random.randint(100, 400))
            time.sleep(random.uniform(0.5, 1.5))

        total_break = random.uniform(15, 30)
        remaining = max(0, total_break - (scrolls * 2))
        time.sleep(remaining)
        print(f"\t[*] Break done, back to posting...")

    def get_post_content(self):
        """Slightly vary post content each time to avoid spam detection"""
        intros = [
            "",
            "",
            "",
            "Check this out!\n\n",
            "Sharing this here 🏡\n\n",
            "For anyone looking 👇\n\n",
        ]
        intro = random.choice(intros)
        return f"{intro}{POST_CONTENT}"

    def post_to_groups(self):
        global POST_CONTENT
        groups = get_sources_list()
        posted_log_path = f"{PROJECT_ROOT}/sessions/posted_log.json"

        # Load existing posted log
        if os.path.exists(posted_log_path):
            with open(posted_log_path, "r") as f:
                posted_log = json.load(f)
        else:
            posted_log = {}

        # Separate unposted vs already posted groups
        unposted = [g for g in groups if g['username'] not in posted_log]
        already_posted = [g for g in groups if g['username'] in posted_log]

        # If all groups have been posted to, reset and exit cleanly
        if not unposted:
            print("\n" + "="*50)
            print(f"  ✅ All {len(groups)} groups posted! Cycle complete.")
            print("  Log has been reset. Run the script again for your next post.")
            print("="*50)
            posted_log = {}
            with open(posted_log_path, "w") as f:
                json.dump(posted_log, f)
            exit()

        # Always prioritize unposted groups, shuffle within each bucket
        random.shuffle(unposted)
        random.shuffle(already_posted)
        ordered_groups = unposted + already_posted

        total_unposted_start = len(unposted)
        print(f"[*] {total_unposted_start} unposted groups remaining out of {len(groups)} total\n")

        posted_count = 0

        for group in ordered_groups:
            if posted_count >= MAX_GROUPS_PER_SESSION:
                print(f"[*] Reached max groups per session ({MAX_GROUPS_PER_SESSION}). Stopping.")
                print(f"[*] Run the script again to continue with remaining groups.")
                break

            print(f"[*] Trying to post: {group['name']}")
            try:
                self.human_delay(300, 800)

                self.page.goto(
                    f"https://facebook.com/groups/{group['username']}",
                    wait_until="domcontentloaded"
                )

                self.human_delay(1000, 2000)

                self.page.wait_for_selector(
                    '//span[contains(text(), "Write something...") or contains(text(), "Isulat ang isang bagay") or contains(text(), "What\'s on your mind")]',
                    timeout=15_000
                ).click()

                self.human_delay(300, 700)

                content = self.get_post_content()
                text_box = self.page.wait_for_selector(
                    "//div[@role='dialog']//div[@contenteditable='true']"
                )
                for char in content:
                    text_box.type(char, delay=random.uniform(
                        MIN_TYPING_DELAY, MAX_TYPING_DELAY
                    ))

                self.human_delay(1500, 2500)

                self.page.wait_for_selector(
                    "//div[@role='dialog']//div[@aria-label='Post']"
                ).click()

                # Wait for dialog to disappear (confirms post was submitted)
                try:
                    self.page.wait_for_selector(
                        "//div[@role='dialog']",
                        state="hidden",
                        timeout=15_000
                    )
                    print(f"\t[+] Dialog closed - post submitted!")
                except:
                    print(f"\t[!] Dialog didn't close - post may have failed")

                self.page.wait_for_timeout(1_000)
                print(f"\t[+] Post successfully submitted!")

                # Log this group as posted with timestamp
                posted_log[group['username']] = {
                    "name": group['name'],
                    "posted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                with open(posted_log_path, "w") as f:
                    json.dump(posted_log, f, indent=2)

                posted_count += 1
                remaining = total_unposted_start - posted_count
                print(f"\t[+] Posted! ({posted_count}/{total_unposted_start}) | {remaining} groups left this session")

            except Exception as e:
                error_msg = str(e)
                print(f"\t[-] Error: {error_msg}")

                # If page crashed or timed out, create a fresh page to recover
                if "crashed" in error_msg.lower() or "timeout" in error_msg.lower():
                    print(f"\t[*] Recovering, creating fresh page...")
                    try:
                        self.page.close()
                    except:
                        pass
                    self.page = self.context.new_page()
                    time.sleep(3)

            # Random delay + human browsing break between groups
            if posted_count < min(len(ordered_groups), MAX_GROUPS_PER_SESSION):
                if posted_count > 0 and posted_count % 10 == 0:
                    self.human_browsing_break()
                else:
                    wait = random.uniform(MIN_DELAY_BETWEEN_GROUPS, MAX_DELAY_BETWEEN_GROUPS)
                    print(f"\t[*] Waiting {int(wait)} seconds before next group...")
                    time.sleep(wait)

        print(f"\n[*] Done! Posted to {posted_count} groups this session.")
        print(f"[*] Total posted so far: {len(posted_log)}/{len(groups)} groups")

        # If all groups completed in this session, reset log for next cycle
        if len(posted_log) >= len(groups):
            print("\n" + "="*50)
            print(f"  ✅ All {len(groups)} groups posted! Cycle complete.")
            print("  Log has been reset. Run the script again for your next post.")
            print("="*50)
            with open(posted_log_path, "w") as f:
                json.dump({}, f)

    def generate_cookie(self) -> None:
        print("[*] Opening Facebook login page...")
        self.page.goto(SOCIAL_MAPS["facebook"]["login"], wait_until="domcontentloaded")
        self.page.wait_for_timeout(3_000)
        print("\n" + "="*50)
        print("  Facebook is open in Chrome.")
        print("  1. Log in with your Facebook account")
        print("  2. Wait until you can see your feed")
        print("  3. Come back here and press ENTER")
        print("="*50)
        input("  >>> Press ENTER after you have logged in: ")
        print("[*] Saving session cookies...")
        with open(f"{PROJECT_ROOT}/sessions/{SOCIAL_MAPS['facebook']['filename']}", "w") as f:
            json.dump(self.page.context.cookies(), f)
        print("[+] Cookie saved successfully!")
        print("[+] Continuing to post setup...")
        self.load_cookie()
        self.post_to_groups()

    def load_cookie(self) -> None:
        global POST_CONTENT
        file_path = f"{PROJECT_ROOT}/sessions/{SOCIAL_MAPS['facebook']['filename']}"
        if not path.exists(file_path):
            print("[-] Not found facebook.json")
            print("[-] Generate using `generate_cookie()`")
            exit()

        print("[*] Loading Facebook session, please wait...")

        self.page.goto("https://www.facebook.com", wait_until="domcontentloaded")
        self.page.wait_for_timeout(1_500)

        with open(file_path, "r") as f:
            cookies = json.loads(f.read())
            self.context.add_cookies(cookies)

        self.page.reload(wait_until="domcontentloaded")
        self.page.wait_for_timeout(2_000)

        try:
            self.page.wait_for_selector("//div[@role='feed']", timeout=30_000)
            print("[+] Successfully logged in!")
        except:
            try:
                self.page.wait_for_selector("//div[@aria-label='Facebook']", timeout=10_000)
                print("[+] Successfully logged in!")
            except:
                print("[-] Login failed or took too long, please regenerate cookie")
                exit()

        # Give user time to manually switch accounts if needed
        print("\n" + "="*50)
        print("  You can now switch accounts in the Chrome window.")
        print("  e.g. switch to your Page or another profile.")
        print("  When you're ready, enter your post content below.")
        print("="*50)

        # Step 1: Ask for post content
        print("\n  What would you like to post?")
        print("  Paste your Facebook link or type your message.")
        POST_CONTENT = input("  >>> Post content: ").strip()

        # Step 2: Optionally add new target groups
        print("\n" + "="*50)
        print("  Do you want to add new target groups?")
        print("  Enter group URLs one per line.")
        print("  Press ENTER on an empty line to skip or finish.")
        print("="*50)

        groups_path = path.join(PROJECT_ROOT, "sessions", "groups.json")
        existing = []
        if path.exists(groups_path):
            with open(groups_path, "r") as f:
                existing = json.load(f)
        existing_usernames = {g["username"] for g in existing}

        added_count = 0
        while True:
            url = input("  Group URL (or ENTER to continue): ").strip()
            if not url:
                break
            match = re.search(r"facebook\.com/groups/([^/?#\s]+)", url, re.IGNORECASE)
            if match:
                username = match.group(1)
                if username not in existing_usernames:
                    existing.append({"name": username, "username": username, "status": "straight"})
                    existing_usernames.add(username)
                    added_count += 1
                    print(f"  [+] Added: {username}")
                else:
                    print(f"  [~] Already in list: {username}")
            else:
                print(f"  [!] Not a valid Facebook group URL, skipped.")

        if added_count > 0:
            with open(groups_path, "w") as f:
                json.dump(existing, f, indent=2)
            print(f"\n  [✓] {added_count} new group(s) saved. Total: {len(existing)} groups.")

        print(f"\n[+] Content set! Starting in 3 seconds...")
        time.sleep(3)


if __name__ == "__main__":
    FacebookGroupSpam()