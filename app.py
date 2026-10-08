"""Local web UI. Run `python app.py`, then open http://127.0.0.1:8765

Uses only the standard library and binds to localhost.
"""

import json
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from os import path

import store
from configs import PROJECT_ROOT
from poster import Poster, StopRequested

HOST, PORT = "127.0.0.1", 8765
INDEX_PATH = path.join(PROJECT_ROOT, "ui", "index.html")


class Job:
    """Single background posting run, shared with the HTTP handlers."""

    def __init__(self):
        self.lock = threading.Lock()
        self.status = "idle"            # idle | starting | waiting | running | stopping
        self.logs = []
        self.progress = {"done": 0, "total": 0}
        self.prompt = None              # {"kind": ..., "message": ...} while waiting on the user
        self._ack = threading.Event()
        self._stop = threading.Event()
        self._thread = None

    def log(self, msg):
        with self.lock:
            self.logs.append(msg)

    def _confirm(self, kind, message):
        with self.lock:
            self.prompt = {"kind": kind, "message": message}
            self.status = "waiting"
            self._ack.clear()
        while not self._ack.wait(0.25):
            if self._stop.is_set():
                break
        with self.lock:
            self.prompt = None
            if not self._stop.is_set():
                self.status = "running" if kind != "close" else self.status
        if self._stop.is_set() and kind != "close":
            raise StopRequested()

    def _on_progress(self, done, total):
        with self.lock:
            self.progress = {"done": done, "total": total}

    def start(self, content, force_login):
        with self.lock:
            if self._thread and self._thread.is_alive():
                return False
            self.status = "starting"
            self.logs = []
            self.progress = {"done": 0, "total": 0}
            self._stop.clear()
        poster = Poster(
            settings=store.load_settings(),
            content=content,
            log=self.log,
            confirm=self._confirm,
            stop_event=self._stop,
            on_progress=self._on_progress,
            force_login=force_login,
        )
        self._thread = threading.Thread(target=self._run, args=(poster,), daemon=True)
        self._thread.start()
        return True

    def _run(self, poster):
        try:
            poster.run()
        except Exception as e:
            self.log(f"Error: {e}")
        finally:
            with self.lock:
                self.status = "idle"
                self.prompt = None

    def acknowledge(self):
        self._ack.set()

    def stop(self):
        with self.lock:
            if self.status == "idle":
                return
            self.status = "stopping"
        self._stop.set()
        self._ack.set()

    def snapshot(self, since):
        with self.lock:
            return {
                "status": self.status,
                "prompt": self.prompt,
                "progress": self.progress,
                "log_offset": len(self.logs),
                "logs": self.logs[since:],
            }


job = Job()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    # --- plumbing -----------------------------------------------------------

    def _host_ok(self):
        host = (self.headers.get("Host") or "").split(":")[0]
        if host not in ("127.0.0.1", "localhost"):
            return False
        origin = self.headers.get("Origin")
        return origin is None or origin.split("://", 1)[-1].split(":")[0] in ("127.0.0.1", "localhost")

    def _send(self, code, body, content_type="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _body(self):
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length))
        except json.JSONDecodeError:
            return {}

    # --- routes -------------------------------------------------------------

    def do_GET(self):
        if not self._host_ok():
            return self._send(403, {"error": "forbidden"})
        route, _, query = self.path.partition("?")
        if route == "/":
            with open(INDEX_PATH, "rb") as f:
                return self._send(200, f.read(), "text/html; charset=utf-8")
        if route == "/api/state":
            since = 0
            for part in query.split("&"):
                if part.startswith("since="):
                    since = int(part[6:] or 0) if part[6:].isdigit() else 0
            snap = job.snapshot(since)
            snap["has_session"] = store.has_session()
            return self._send(200, snap)
        if route == "/api/settings":
            return self._send(200, {"settings": store.load_settings(), "defaults": store.DEFAULT_SETTINGS})
        if route == "/api/groups":
            return self._send(200, {"groups": store.load_groups(), "posted": store.load_posted_log()})
        self._send(404, {"error": "not found"})

    def do_POST(self):
        if not self._host_ok():
            return self._send(403, {"error": "forbidden"})
        body = self._body()
        route = self.path

        if route == "/api/run":
            content = str(body.get("content", "")).strip()
            if not content:
                return self._send(400, {"error": "Post content is empty."})
            if not store.load_groups():
                return self._send(400, {"error": "Add at least one group first."})
            if not job.start(content, bool(body.get("force_login"))):
                return self._send(409, {"error": "A run is already in progress."})
            return self._send(200, {"ok": True})
        if route == "/api/confirm":
            job.acknowledge()
            return self._send(200, {"ok": True})
        if route == "/api/stop":
            job.stop()
            return self._send(200, {"ok": True})
        if route == "/api/settings":
            return self._send(200, {"settings": store.save_settings(body)})
        if route == "/api/groups":
            groups = body.get("groups")
            if not isinstance(groups, list):
                return self._send(400, {"error": "groups must be a list"})
            return self._send(200, {"groups": store.save_groups(groups)})
        if route == "/api/groups/add":
            result = store.add_groups_from_text(str(body.get("text", "")))
            result["groups"] = store.load_groups()
            return self._send(200, result)
        if route == "/api/history/reset":
            store.save_posted_log({})
            return self._send(200, {"ok": True})
        if route == "/api/session/reset":
            store.delete_session()
            return self._send(200, {"ok": True})
        self._send(404, {"error": "not found"})


def open_browser(url):
    if not webbrowser.open(url) and sys.platform == "darwin":
        subprocess.run(["open", url], check=False)


def main():
    url = f"http://{HOST}:{PORT}"
    try:
        server = ThreadingHTTPServer((HOST, PORT), Handler)
    except OSError:
        print(f"Already running at {url}. Opening it in your browser.")
        open_browser(url)
        return
    print(f"fb-group-auto-poster UI running at {url}  (Ctrl+C to quit)")
    threading.Timer(0.5, open_browser, [url]).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        job.stop()
        print("\nBye.")


if __name__ == "__main__":
    main()
