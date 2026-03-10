import time
import shutil
import subprocess
import os
import re
import glob
import traceback
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WATCH_DIR = "C:/Users/kwils/Downloads"
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_FILE = os.path.join(PROJECT_DIR, "index.html")
RESTART_DELAY = 3
POLL_INTERVAL = 10

# Pattern for existing slide video files: slide{N}-*-bg.mp4
SLIDE_RE = re.compile(r"^slide(\d+)-.*-bg\.mp4$")

# Lock to prevent watchdog and poller from deploying simultaneously
_deploy_lock = threading.Lock()


def next_slide_number():
    """Scan project root for slide*-*-bg.mp4 and return next N."""
    existing = glob.glob(os.path.join(PROJECT_DIR, "slide*-*-bg.mp4"))
    nums = []
    for f in existing:
        m = SLIDE_RE.match(os.path.basename(f))
        if m:
            nums.append(int(m.group(1)))
    return max(nums, default=0) + 1


def slugify(filename):
    """Turn a filename like '13477-248644896_medium.mp4' into a short slug."""
    name = os.path.splitext(filename)[0]
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:30].rstrip("-") or "video"


def update_video_src(old_src, new_src):
    """If index.html contains a <source src="old_src">, update it to new_src."""
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        html = f.read()
    if old_src and old_src in html:
        html = html.replace(old_src, new_src)
    elif new_src not in html:
        print(f"[deploy] Note: no existing <source src> found to update for {new_src}")
        return False
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    return True


def git_commit_and_push(filename):
    """git add -A, commit, and push."""
    msg = f"auto-deploy: {filename}"
    print(f"[deploy] Committing: {msg}")
    cmd = f'git add -A && git commit -m "{msg}" && git push'
    result = subprocess.run(
        cmd,
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        shell=True,
    )
    if result.returncode == 0:
        print(f"[deploy] Pushed successfully.")
        for line in result.stdout.splitlines():
            if "->" in line:
                print(f"[deploy] {line.strip()}")
    else:
        print("[deploy] Git push failed:")
        print(result.stderr or result.stdout)


def deploy_index(src):
    """Copy index.html from src to project root and git push."""
    with _deploy_lock:
        print(f"\n[deploy] Deploying index.html from {src}")
        time.sleep(1)
        shutil.copy2(src, INDEX_FILE)
        git_commit_and_push("index.html")


def deploy_mp4(src, basename):
    """Rename, copy, update HTML, and git push an mp4."""
    with _deploy_lock:
        n = next_slide_number()
        slug = slugify(basename)
        new_name = f"slide{n}-{slug}-bg.mp4"
        dest = os.path.join(PROJECT_DIR, new_name)

        print(f"[deploy] Renaming -> {new_name}")
        shutil.copy2(src, dest)

        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            html = f.read()
        src_matches = re.findall(r'<source\s+src="([^"]*\.mp4)"', html)
        if src_matches:
            old_src = src_matches[-1]
            print(f"[deploy] Updating index.html: {old_src} -> {new_name}")
            update_video_src(old_src, new_name)
        else:
            print(f"[deploy] No <source src=*.mp4> in index.html to update")

        git_commit_and_push(new_name)


class DeployHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self._handled = set()

    def on_created(self, event):
        self._handle(event)

    def on_modified(self, event):
        self._handle(event)

    def _handle(self, event):
        try:
            if event.is_directory:
                return

            basename = os.path.basename(event.src_path)
            lower = basename.lower()

            if basename == "index.html":
                print(f"\n[deploy] [watchdog] Detected index.html")
                deploy_index(event.src_path)
                return

            if lower.endswith(".mp4"):
                key = event.src_path
                if key in self._handled:
                    return
                self._handled.add(key)

                print(f"\n[deploy] [watchdog] Detected MP4: {basename}")
                time.sleep(2)
                deploy_mp4(event.src_path, basename)
                self._handled.discard(key)
                return

        except Exception:
            print("[deploy] Error in watchdog handler:")
            traceback.print_exc()


def poll_index_html(stop_event):
    """Every POLL_INTERVAL seconds, check if Downloads/index.html is newer than project index.html."""
    print(f"[deploy] [poller] Polling every {POLL_INTERVAL}s for index.html changes")
    downloads_index = os.path.join(WATCH_DIR, "index.html")

    while not stop_event.is_set():
        try:
            if os.path.exists(downloads_index):
                dl_mtime = os.path.getmtime(downloads_index)
                age = time.time() - dl_mtime
                should_deploy = False

                if os.path.exists(INDEX_FILE):
                    proj_mtime = os.path.getmtime(INDEX_FILE)
                    if dl_mtime > proj_mtime:
                        print(f"\n[deploy] [poller] Downloads/index.html is newer (dl={dl_mtime:.0f} > proj={proj_mtime:.0f})")
                        should_deploy = True
                    elif age <= 60:
                        print(f"\n[deploy] [poller] Downloads/index.html modified {age:.0f}s ago (within 60s window)")
                        should_deploy = True
                else:
                    print(f"\n[deploy] [poller] Downloads/index.html found, project missing - deploying")
                    should_deploy = True

                if should_deploy:
                    deploy_index(downloads_index)
        except Exception:
            print("[deploy] [poller] Error:")
            traceback.print_exc()

        stop_event.wait(POLL_INTERVAL)


def run_watcher():
    """Start watchdog observer + polling thread."""
    print(f"[deploy] Watching {WATCH_DIR} for index.html and *.mp4 ...")
    print(f"[deploy] Watchdog (events) + poller ({POLL_INTERVAL}s fallback)")

    stop_event = threading.Event()

    # Start polling thread
    poller = threading.Thread(target=poll_index_html, args=(stop_event,), daemon=True)
    poller.start()

    # Start watchdog
    handler = DeployHandler()
    observer = Observer()
    observer.schedule(handler, WATCH_DIR, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        raise
    finally:
        stop_event.set()
        observer.stop()
        observer.join()
        poller.join(timeout=5)


if __name__ == "__main__":
    print("[deploy] Starting watcher (auto-restart on crash) ...")
    print("[deploy] Press Ctrl+C to stop.\n")

    while True:
        try:
            run_watcher()
        except KeyboardInterrupt:
            print("\n[deploy] Stopped by user.")
            break
        except Exception:
            print("[deploy] Watcher crashed:")
            traceback.print_exc()
            print(f"[deploy] Restarting in {RESTART_DELAY}s ...\n")
            time.sleep(RESTART_DELAY)
