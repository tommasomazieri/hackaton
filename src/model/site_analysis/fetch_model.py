"""
FETCH_MODEL — vendor the pretrained Google Dynamic World SavedModel.
====================================================================
Sparse-clones google/dynamicworld (Apache-2.0) into vendor/dynamicworld/ so the
`model/forward` TensorFlow SavedModel is available for local inference.

Idempotent: if the SavedModel is already present, does nothing.

    python src/model/site_analysis/fetch_model.py
"""
from __future__ import annotations

import os
import subprocess
import sys

REPO_URL = "https://github.com/google/dynamicworld.git"
_HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
VENDOR_DIR = os.path.join(PROJECT_ROOT, "vendor", "dynamicworld")
FORWARD_DIR = os.path.join(VENDOR_DIR, "model", "forward")


def _run(cmd: list[str], cwd: str | None = None) -> None:
    print("  $", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def fetch() -> str:
    """Ensure the forward SavedModel exists locally; return its directory."""
    if os.path.isdir(FORWARD_DIR) and os.listdir(FORWARD_DIR):
        print(f"[fetch_model] already present: {FORWARD_DIR}")
        return FORWARD_DIR

    os.makedirs(os.path.dirname(VENDOR_DIR), exist_ok=True)

    if not os.path.isdir(os.path.join(VENDOR_DIR, ".git")):
        print(f"[fetch_model] sparse-cloning {REPO_URL}")
        _run(["git", "clone", "--depth", "1", "--filter=blob:none",
              "--sparse", REPO_URL, VENDOR_DIR])
        _run(["git", "sparse-checkout", "set", "model"], cwd=VENDOR_DIR)
    else:
        _run(["git", "sparse-checkout", "set", "model"], cwd=VENDOR_DIR)

    if not (os.path.isdir(FORWARD_DIR) and os.listdir(FORWARD_DIR)):
        raise RuntimeError(
            f"clone finished but {FORWARD_DIR} is empty — check the repo layout"
        )
    print(f"[fetch_model] ready: {FORWARD_DIR}")
    return FORWARD_DIR


if __name__ == "__main__":
    try:
        fetch()
    except subprocess.CalledProcessError as exc:
        print(f"[fetch_model] git failed: {exc}", file=sys.stderr)
        sys.exit(1)
