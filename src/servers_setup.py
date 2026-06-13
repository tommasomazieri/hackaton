"""
servers_setup.py — launch the DC Hounds stack from scratch.
=========================================================
Frees the API + frontend ports (kills anything still bound to them), then starts
both servers fresh in the SAME Python interpreter you run this with — so the API
always has the installed CNN stack (tensorflow / odc-stac / rasterio / …):

  - FastAPI backend : uvicorn src.model.api:app   -> http://127.0.0.1:8000
  - Static frontend : http.server (src/frontend)  -> http://127.0.0.1:5500

Usage:
    python src/servers_setup.py
    python src/servers_setup.py --no-browser     # don't auto-open the tab

Ctrl+C stops both servers.
"""
from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
import webbrowser

# Windows consoles default to cp1252 and choke on non-ASCII prints — force UTF-8.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

API_PORT = 8000
WEB_PORT = 3000   # matches src/main.py

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
FRONTEND_DIR = os.path.join(HERE, "frontend")


# ---------------------------------------------------------------------------
# Port freeing — kill whatever is already listening so we always start clean
# ---------------------------------------------------------------------------
def _free_port(port: int) -> None:
    pids: set[str] = set()
    if os.name == "nt":
        out = subprocess.run(["netstat", "-ano", "-p", "tcp"],
                             capture_output=True, text=True).stdout
        for line in out.splitlines():
            parts = line.split()
            # TCP  <local>  <remote>  <state>  <pid>
            if len(parts) >= 5 and parts[0] == "TCP" and parts[1].endswith(f":{port}") and parts[-1].isdigit():
                pids.add(parts[-1])
        for pid in pids:
            subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
            print(f"  - freed :{port} (killed PID {pid})")
    else:
        out = subprocess.run(["sh", "-c", f"lsof -ti tcp:{port} || true"],
                             capture_output=True, text=True).stdout
        for pid in out.split():
            subprocess.run(["kill", "-9", pid], capture_output=True)
            print(f"  - freed :{port} (killed PID {pid})")
    if not pids:
        print(f"  - :{port} already free")


def _wait_port(port: int, timeout: float = 40.0) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return True
        time.sleep(0.4)
    return False


def main() -> None:
    ap = argparse.ArgumentParser(description="Launch DC Hounds backend + frontend from scratch")
    ap.add_argument("--no-browser", action="store_true", help="don't auto-open the browser tab")
    ap.add_argument("--api-port", type=int, default=API_PORT)
    ap.add_argument("--web-port", type=int, default=WEB_PORT)
    args = ap.parse_args()

    print("Freeing ports...")
    _free_port(args.api_port)
    _free_port(args.web_port)

    env = os.environ.copy()
    env["PYTHONPATH"] = ROOT + os.pathsep + env.get("PYTHONPATH", "")
    env["TF_CPP_MIN_LOG_LEVEL"] = "3"          # quiet TensorFlow startup spam

    print(f"Starting API   on :{args.api_port}  (uvicorn src.model.api:app)")
    api = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.model.api:app",
         "--host", "127.0.0.1", "--port", str(args.api_port)],
        cwd=ROOT, env=env,
    )

    print(f"Starting WEB   on :{args.web_port}  (serving {FRONTEND_DIR})")
    web = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(args.web_port), "--directory", FRONTEND_DIR],
        cwd=ROOT, env=env,
    )

    url = f"http://127.0.0.1:{args.web_port}/index.html"
    if _wait_port(args.api_port):
        print(f"API ready. Frontend -> {url}")
    else:
        print("WARNING: API did not answer in time — check the log above for import errors.")

    if not args.no_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    print("\nBoth servers running. Press Ctrl+C to stop.\n")
    try:
        while True:
            if api.poll() is not None:
                print("API process exited — shutting down.")
                break
            if web.poll() is not None:
                print("Frontend process exited — shutting down.")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping…")
    finally:
        for p in (web, api):
            if p.poll() is None:
                p.terminate()
        for p in (web, api):
            try:
                p.wait(timeout=5)
            except Exception:
                p.kill()


if __name__ == "__main__":
    main()
