import time
import shutil
import subprocess
import os
import re
import glob
import traceback
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WATCH_DIR = "C:/Users/kwils/Downloads"
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_FILE = os.path.join(PROJECT_DIR, "index.html")
RESTART_DELAY = 3

# Pattern for existing slide video files: slide{N}-*-bg.mp4
SLIDE_RE = re.compile(r"^slide(\d+)-.*-bg\.mp4$")


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
    # Replace non-alphanumeric with hyphens, collapse, strip
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    # Truncate to something reasonable
    return slug[:30].rstrip("-") or "video"


def update_video_src(old_src, new_src):
    """If index.html contains a <source src="old_src">, update it to new_src."""
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        html = f.read()
    if old_src and old_src in html:
        html = html.replace(old_src, new_src)
    elif new_src not in html:
        # No existing video tag — nothing to replace
        print(f"[deploy] Note: no existing <source src> found to update for {new_src}")
        return False
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    return True


def deploy_prod():
    """Run vercel --prod and print the live URL."""
    print("[deploy] Running vercel --prod ...")
    result = subprocess.run(
        "vercel --prod --yes",
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        shell=True,
    )
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("https://") and "vercel.app" in line:
                print(f"[deploy] Live URL: {line}")
                return
        print("[deploy] Deployed successfully.")
        print(result.stdout)
    else:
        print("[deploy] Deployment failed:")
        print(result.stderr or result.stdout)


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

            # --- index.html handler ---
            if basename == "index.html":
                src = event.src_path
                print(f"\n[deploy] Detected {src}")
                time.sleep(1)
                print(f"[deploy] Copying to {INDEX_FILE}")
                shutil.copy2(src, INDEX_FILE)
                deploy_prod()
                return

            # --- .mp4 handler ---
            if lower.endswith(".mp4"):
                # Deduplicate rapid events for the same file
                key = event.src_path
                if key in self._handled:
                    return
                self._handled.add(key)

                src = event.src_path
                print(f"\n[deploy] Detected MP4: {src}")
                time.sleep(2)  # Let download finish

                n = next_slide_number()
                slug = slugify(basename)
                new_name = f"slide{n}-{slug}-bg.mp4"
                dest = os.path.join(PROJECT_DIR, new_name)

                print(f"[deploy] Renaming → {new_name}")
                shutil.copy2(src, dest)

                # Find the most recent existing video src in index.html to replace
                with open(INDEX_FILE, "r", encoding="utf-8") as f:
                    html = f.read()
                # Find all <source src="*.mp4"> references
                src_matches = re.findall(r'<source\s+src="([^"]*\.mp4)"', html)
                if src_matches:
                    old_src = src_matches[-1]  # replace the last one found
                    print(f"[deploy] Updating index.html: {old_src} → {new_name}")
                    update_video_src(old_src, new_name)
                else:
                    print(f"[deploy] No <source src=*.mp4> in index.html to update")

                deploy_prod()

                # Allow this file to be handled again if re-downloaded
                self._handled.discard(key)
                return

        except Exception:
            print("[deploy] Error in handler:")
            traceback.print_exc()


def run_watcher():
    """Start the observer. Returns only when it stops."""
    print(f"[deploy] Watching {WATCH_DIR} for index.html and *.mp4 ...")
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
        observer.stop()
        observer.join()


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
