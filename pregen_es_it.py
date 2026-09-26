"""
Pre-generate CNN site imagery for EVERY Spain (ES) + Italy (IT) grid node, so a
presentation report exports instantly from cache. Parallel (threads overlap the
slow Sentinel-2 / Overpass fetches; the single GPU CNN session is thread-safe),
resumable (skips nodes already cached), fault-tolerant (Overpass failures now
degrade to "no roads/landuse" instead of killing the node).

Usage:
    .venv/Scripts/python.exe pregen_es_it.py            # ES + IT
    .venv/Scripts/python.exe pregen_es_it.py --workers 8
"""
from __future__ import annotations

import argparse
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd

from src.model import site_stage as ss

AOI_KM = 3.8  # matches the report's AOI_KM (single-inference, fastest path)

_print_lock = threading.Lock()


def _log(msg: str) -> None:
    with _print_lock:
        print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def node_ids_for(countries: list[str]) -> list[str]:
    df = pd.read_parquet("data/grid_nodes.parquet")
    cc = {c.lower(): c for c in df.columns}
    nid, ctry = df[cc["node_id"]], df[cc["country"]]
    return list(nid[ctry.isin(countries)])


def worker(node_id: str, lat: float, lon: float) -> tuple[str, str]:
    jp = os.path.join(ss.OUT_DIR, f"{node_id}.json")
    pp = os.path.join(ss.OUT_DIR, f"{node_id}.png")
    if os.path.exists(jp) and os.path.exists(pp):
        return node_id, "cached"
    last = None
    for attempt in range(3):  # transient network: retry a couple of times
        try:
            res = ss.analyze_node(node_id, lat, lon, size_km=AOI_KM)
            status = res.get("status")
            if status in ("ok", "no_buildable_land"):
                with open(jp, "w", encoding="utf-8") as fh:
                    json.dump(res, fh, indent=2)
                return node_id, status + ("/img" if res.get("image") else "/noimg")
            return node_id, f"status={status}"
        except Exception as exc:
            last = exc
            time.sleep(2 * (attempt + 1))
    return node_id, f"ERROR {last}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--countries", default="ES,IT")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    countries = [c.strip().upper() for c in args.countries.split(",")]
    ids = node_ids_for(countries)
    coords = ss.load_node_coords(ids)
    os.makedirs(ss.OUT_DIR, exist_ok=True)

    done = sum(
        1 for n in ids
        if os.path.exists(os.path.join(ss.OUT_DIR, f"{n}.json"))
        and os.path.exists(os.path.join(ss.OUT_DIR, f"{n}.png"))
    )
    _log(f"{countries}: {len(ids)} nodes, {done} already cached, "
         f"{len(ids) - done} to do, {args.workers} workers")

    counts: dict[str, int] = {}
    completed = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {
            ex.submit(worker, n, float(coords.loc[n, "y"]), float(coords.loc[n, "x"])): n
            for n in ids
        }
        for fut in as_completed(futs):
            node_id, outcome = fut.result()
            tag = outcome.split()[0]
            counts[tag] = counts.get(tag, 0) + 1
            completed += 1
            _log(f"[{completed}/{len(ids)}] {node_id}: {outcome}")

    img_ok = sum(
        1 for n in ids if os.path.exists(os.path.join(ss.OUT_DIR, f"{n}.png"))
    )
    _log(f"DONE in {time.time() - t0:.0f}s — outcomes={counts}")
    _log(f"PNG coverage: {img_ok}/{len(ids)} nodes have a site image")


if __name__ == "__main__":
    main()
