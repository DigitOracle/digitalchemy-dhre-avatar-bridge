import time
import shutil
import subprocess
import os
import traceback
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WATCH_DIR = "C:/Users/kwils/Downloads"
WATCH_FILE = "index.html"
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DEST_FILE = os.path.join(PROJECT_DIR, "index.html")
RESTART_DELAY = 3


class DeployHandler(FileSystemEventHandler):
    def on_created(self, event):
        self._handle(event)

    def on_modified(self, event):
        self._handle(event)

    def _handle(self, event):
        try:
            if event.is_directory:
                return
            if os.path.basename(event.src_path) != WATCH_FILE:
                return

            src = event.src_path
            print(f"\n[deploy] Detected {src}")

            # Brief pause to let the file finish writing
            time.sleep(1)

            print(f"[deploy] Copying to {DEST_FILE}")
            shutil.copy2(src, DEST_FILE)

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
                        break
                else:
                    print("[deploy] Deployed successfully.")
                    print(result.stdout)
            else:
                print("[deploy] Deployment failed:")
                print(result.stderr or result.stdout)
        except Exception:
            print("[deploy] Error in handler:")
            traceback.print_exc()


def run_watcher():
    """Start the observer. Returns only when it stops."""
    print(f"[deploy] Watching {WATCH_DIR} for {WATCH_FILE} ...")
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
