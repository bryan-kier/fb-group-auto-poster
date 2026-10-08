"""Command-line entry point. For the browser UI, run `python app.py` instead."""

import threading

import store
from poster import Poster


def confirm(kind, message):
    input(f"\n  {message}\n  >>> Press ENTER to continue: ")


def main():
    print("\n  What would you like to post?")
    print("  Paste your Facebook link or type your message.")
    content = input("  >>> Post content: ").strip()
    if not content:
        print("  Nothing to post.")
        return

    print("\n  Add new target groups? Enter URLs one per line, ENTER on an empty line to finish.")
    lines = []
    while True:
        line = input("  Group URL: ").strip()
        if not line:
            break
        lines.append(line)
    if lines:
        result = store.add_groups_from_text("\n".join(lines))
        print(f"  Added {len(result['added'])}, skipped {len(result['duplicates'])} duplicates, "
              f"{len(result['invalid'])} invalid.")

    Poster(
        settings=store.load_settings(),
        content=content,
        log=lambda msg: print(f"[*] {msg}"),
        confirm=confirm,
        stop_event=threading.Event(),
        on_progress=lambda done, total: None,
    ).run()


if __name__ == "__main__":
    main()
