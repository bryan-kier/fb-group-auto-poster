"""Posting engine. Frontend-agnostic: the CLI and the web UI both drive this class.

The caller supplies:
    log(msg)             - receives progress lines
    confirm(kind, msg)   - blocks until the user acknowledges (kind: "login" | "start" | "close")
    on_progress(done, total)
    stop_event           - threading.Event; set it to abort cleanly
"""

import json
import random
import time
from datetime import datetime

from playwright.sync_api import sync_playwright

import store
from configs import SOCIAL_MAPS, ensure_dirs

BREAK_PAGES = [
    "https://www.facebook.com",
    "https://www.facebook.com/marketplace",
    "https://www.facebook.com/watch",
    "https://www.facebook.com/groups/feed",
    "https://www.facebook.com/gaming",
    "https://www.facebook.com/news",
    "https://www.facebook.com/events",
    "https://www.facebook.com/friends",
    "https://www.facebook.com/reels",
    "https://www.facebook.com/memories",
    "https://www.facebook.com/saved",
    "https://www.facebook.com/groups/?ref=bookmarks",
]


class StopRequested(Exception):
    pass


class Poster:
    def __init__(self, settings, content, log, confirm, stop_event, on_progress=None, force_login=False):
        self.s = settings
        self.content = content
        self.log = log
        self.confirm = confirm
        self.stop = stop_event
        self.on_progress = on_progress or (lambda done, total: None)
        self.force_login = force_login
        self.page = None
        self.context = None

    # --- helpers ------------------------------------------------------------

    def _check_stop(self):
        if self.stop.is_set():
            raise StopRequested()

    def _sleep(self, seconds):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            self._check_stop()
            time.sleep(min(0.25, max(0, end - time.monotonic())))

    def human_delay(self, min_ms=500, max_ms=1000):
        self._sleep(random.uniform(min_ms / 1000, max_ms / 1000))

    def build_content(self):
        intros = self.s["intros"]
        if intros and random.randint(1, 100) <= self.s["intro_chance"]:
            return f"{random.choice(intros)}\n\n{self.content}"
        return self.content

    def human_browsing_break(self):
        self.log("Taking a human break, browsing Facebook...")
        self.page.goto(random.choice(BREAK_PAGES), wait_until="domcontentloaded")
        scrolls = random.randint(4, 8)
        for _ in range(scrolls):
            self.page.mouse.wheel(0, random.randint(400, 1200))
            self._sleep(random.uniform(1.5, 3.5))
        if random.random() > 0.5:
            self.page.mouse.wheel(0, -random.randint(200, 600))
            self._sleep(random.uniform(1.0, 2.5))
        self._sleep(max(0, random.uniform(25, 45) - scrolls * 2))
        self.log("Break done, back to posting...")

    # --- session ------------------------------------------------------------

    def generate_cookie(self):
        self.log("Opening Facebook login page...")
        self.page.goto(SOCIAL_MAPS["facebook"]["login"], wait_until="domcontentloaded")
        self.confirm("login", "Log in to Facebook in the browser window, wait for your feed, then continue.")
        self._check_stop()
        with open(store.COOKIE_PATH, "w") as f:
            json.dump(self.context.cookies(), f)
        self.log("Session saved.")

    def load_cookie(self):
        self.log("Loading Facebook session...")
        self.page.goto("https://www.facebook.com", wait_until="domcontentloaded")
        self.page.wait_for_timeout(1_500)
        with open(store.COOKIE_PATH, "r") as f:
            self.context.add_cookies(json.load(f))
        self.page.reload(wait_until="domcontentloaded")
        self.page.wait_for_timeout(2_000)
        for selector, timeout in (("//div[@role='feed']", 30_000), ("//div[@aria-label='Facebook']", 10_000)):
            try:
                self.page.wait_for_selector(selector, timeout=timeout)
                self.log("Logged in.")
                return
            except Exception:
                self._check_stop()
        raise RuntimeError("Login failed or took too long. Reset the session and log in again.")

    # --- main flow ----------------------------------------------------------

    def run(self):
        ensure_dirs()
        pw = sync_playwright().start()
        browser = None
        try:
            browser = pw.chromium.launch(headless=False)
            self.context = browser.new_context(no_viewport=True)
            self.page = self.context.new_page()

            if self.force_login or not store.has_session():
                self.generate_cookie()
            self.load_cookie()

            self.confirm("start", "Logged in. Switch to another account or Page now if needed, then start posting.")
            self._check_stop()
            self.post_to_groups()
        except StopRequested:
            self.log("Stopped.")
        finally:
            try:
                if self.page and not self.page.is_closed():
                    self.confirm("close", "Done. The browser stays open until you close it here.")
            except StopRequested:
                pass
            except Exception:
                pass
            for closable in (self.context, browser):
                try:
                    closable.close()
                except Exception:
                    pass
            pw.stop()

    def post_to_groups(self):
        s = self.s
        groups = store.load_groups()
        posted_log = store.load_posted_log()

        unposted = [g for g in groups if g["username"] not in posted_log]
        already = [g for g in groups if g["username"] in posted_log]

        if not groups:
            self.log("No groups configured. Add some in the Groups tab.")
            return
        if not unposted:
            self.log(f"All {len(groups)} groups already posted. Cycle complete, history reset.")
            store.save_posted_log({})
            return

        random.shuffle(unposted)
        random.shuffle(already)
        ordered = unposted + already
        total = min(len(unposted), s["max_groups_per_session"])
        self.log(f"{len(unposted)} unposted groups remaining out of {len(groups)} total.")
        self.on_progress(0, total)

        posted_count = 0
        composer_xpath = "//span[" + " or ".join(
            f'contains(text(), "{t}")' for t in s["composer_texts"]
        ) + "]"

        for group in ordered:
            if posted_count >= s["max_groups_per_session"]:
                self.log(f"Reached max groups per session ({s['max_groups_per_session']}).")
                break
            self._check_stop()
            self.log(f"Posting to: {group['name']}")
            try:
                self.human_delay(300, 800)
                self.page.goto(f"https://facebook.com/groups/{group['username']}", wait_until="domcontentloaded")
                self.human_delay(1000, 2000)
                self.page.wait_for_selector(composer_xpath, timeout=15_000).click()
                self.human_delay(300, 700)

                text_box = self.page.wait_for_selector("//div[@role='dialog']//div[@contenteditable='true']")
                for char in self.build_content():
                    self._check_stop()
                    text_box.type(char, delay=random.uniform(s["min_typing_delay"], s["max_typing_delay"]))
                self._sleep(1)  # let video/link preview render
                self.human_delay(1500, 2500)

                self.page.wait_for_selector("//div[@role='dialog']//div[@aria-label='Post']").click()
                try:
                    self.page.wait_for_selector("//div[@role='dialog']", state="hidden", timeout=15_000)
                except Exception:
                    self.log("  Dialog didn't close, post may have failed.")
                self.page.wait_for_timeout(1_000)

                posted_log[group["username"]] = {
                    "name": group["name"],
                    "posted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                store.save_posted_log(posted_log)
                posted_count += 1
                self.on_progress(posted_count, total)
                self.log(f"  Posted ({posted_count}/{total})")

            except StopRequested:
                raise
            except Exception as e:
                msg = str(e).splitlines()[0] if str(e) else type(e).__name__
                self.log(f"  Error: {msg}")
                if "crashed" in msg.lower() or "timeout" in msg.lower():
                    self.log("  Recovering, opening a fresh page...")
                    try:
                        self.page.close()
                    except Exception:
                        pass
                    self.page = self.context.new_page()
                    self._sleep(3)

            if posted_count < min(len(ordered), s["max_groups_per_session"]):
                every = s["browsing_break_every"]
                if every and posted_count > 0 and posted_count % every == 0:
                    self.human_browsing_break()
                else:
                    wait = random.uniform(s["min_delay_between_groups"], s["max_delay_between_groups"])
                    self.log(f"  Waiting {int(wait)}s before next group...")
                    self._sleep(wait)

        self.log(f"Done. Posted to {posted_count} groups this session.")
        if len(posted_log) >= len(groups):
            self.log("All groups posted. Cycle complete, history reset.")
            store.save_posted_log({})
