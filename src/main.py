"""DC Siting Intelligence — single-command launcher.

Starts the FastAPI model server (uvicorn) and a static file server for the
frontend, then opens the web app in the default browser. Ctrl-C stops both.

Usage:
    python main.py
"""
from __future__ import annotations

import atexit
import signal
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

def _find_project_root() -> Path:
    """Walk up from this file to the dir that holds src/frontend + src/model."""
    here = Path(__file__).resolve()
    for cand in [here.parent, *here.parents]:
        if (cand / "src" / "frontend").is_dir() and (cand / "src" / "model" / "api.py").is_file():
            return cand
    # fallback: assume this file lives directly under the project root
    return here.parent


ROOT = _find_project_root()
FRONTEND_DIR = ROOT / "src" / "frontend"

API_HOST = "127.0.0.1"
API_PORT = 8000
WEB_PORT = 3000

_procs: list[subprocess.Popen] = []


def _start_api() -> subprocess.Popen:
    """Launch uvicorn serving src.model.api:app from the project root."""
    cmd = [
        sys.executable, "-m", "uvicorn",
        "src.model.api:app",
        "--host", API_HOST,
        "--port", str(API_PORT),
    ]
    return subprocess.Popen(cmd, cwd=str(ROOT))


def _start_web() -> subprocess.Popen:
    """Launch a static HTTP server with the frontend directory as root."""
    cmd = [
        sys.executable, "-m", "http.server", str(WEB_PORT),
        "--bind", "127.0.0.1",
        "--directory", str(FRONTEND_DIR),
    ]
    return subprocess.Popen(cmd, cwd=str(ROOT))


def _shutdown(*_args) -> None:
    for p in _procs:
        if p.poll() is None:
            p.terminate()
    for p in _procs:
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            p.kill()


def _check_deps() -> None:
    """Fail loudly if the API server's deps are missing in this interpreter."""
    import importlib.util
    missing = [m for m in ("fastapi", "uvicorn") if importlib.util.find_spec(m) is None]
    if missing:
        sys.exit(
            f"[main] Missing modules in {sys.executable}: {', '.join(missing)}\n"
            f"       Install with:\n"
            f'       "{sys.executable}" -m pip install fastapi "uvicorn[standard]"'
        )


def _check_ports() -> None:
    """Fail loudly if a target port is already bound."""
    import socket
    for name, port in (("API", API_PORT), ("web", WEB_PORT)):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex((API_HOST, port)) == 0:
                sys.exit(
                    f"[main] Port {port} ({name}) is already in use.\n"
                    f"       A previous run is probably still alive. Free it with PowerShell:\n"
                    f"       Get-NetTCPConnection -LocalPort {port} -State Listen | "
                    f"%{{ Stop-Process -Id $_.OwningProcess -Force }}"
                )


def main() -> None:
    if not FRONTEND_DIR.exists():
        sys.exit(f"Frontend directory not found: {FRONTEND_DIR}")
    _check_deps()
    _check_ports()

    print(f"[main] Starting API server  -> http://{API_HOST}:{API_PORT}")
    _procs.append(_start_api())

    print(f"[main] Starting web server  -> http://127.0.0.1:{WEB_PORT}")
    _procs.append(_start_web())

    atexit.register(_shutdown)
    signal.signal(signal.SIGINT, lambda *a: (_shutdown(), sys.exit(0)))

    # give servers a moment to bind before opening the browser
    def _open_browser() -> None:
        time.sleep(1.5)
        url = f"http://127.0.0.1:{WEB_PORT}/index.html"
        print(f"[main] Opening {url}")
        webbrowser.open(url)

    threading.Thread(target=_open_browser, daemon=True).start()

    print("[main] Press Ctrl-C to stop both servers.")
    try:
        while True:
            for p in _procs:
                if p.poll() is not None:
                    print("[main] A server process exited — shutting down.")
                    _shutdown()
                    return
            time.sleep(0.5)
    except KeyboardInterrupt:
        _shutdown()


if __name__ == "__main__":
    main()
