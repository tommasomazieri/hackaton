"""
DC Siting — single server: JSON API + static frontend.

    python -m src.server            # http://127.0.0.1:8000
    python -m src.server --port 9000 --no-ingest

Stateless: every /api/query carries its own inputs and returns the full ranked
table, so there is nothing to "run first" and no cross-user state.
"""
from __future__ import annotations

import argparse
import json
import logging
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src import ingest
from src.model import pipeline, rank, site_stage

log = logging.getLogger("server")
ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "src" / "frontend"
SITE_DIR = Path(site_stage.OUT_DIR) if site_stage else ROOT / "data" / "site_analysis"
SCORE_COLS = rank.SCORE_COLS

# rank.rank_by_weights reads a module-global table that pipeline.run overwrites,
# so run + rank must happen as one critical section.
# ponytail: global lock, one query at a time (~100 ms each); fine for a team tool.
_model_lock = threading.Lock()
_cnn_slots = threading.Semaphore(3)  # parallel CNN runs share one GPU
# ~3.8 km → ~388 px composite, under the Dynamic World model's 399 px window:
# one inference per node instead of 2x2 tiling (same AOI the old report used).
AOI_KM = 3.8
_node_locks: dict[str, threading.Lock] = {}
_node_locks_guard = threading.Lock()

ENABLE_INGEST = True


@asynccontextmanager
async def lifespan(_: FastAPI):
    if ENABLE_INGEST:
        ingest.start_background()
    yield


app = FastAPI(title="DC Siting", lifespan=lifespan)
app.add_middleware(GZipMiddleware, minimum_size=2_000)


class Query(BaseModel):
    capacity_mw: float = Field(gt=0, le=10_000)
    surface_m2: float = Field(gt=0, le=100_000_000)
    countries: list[str] | None = None
    weights: dict[str, float] | None = None


def _region_names() -> pd.Series:
    """NUTS 3 region names from the ingest cache; empty if the cache predates them."""
    try:
        return pd.read_parquet(ingest.LIVE / "nodes.parquet",
                               columns=["node_id", "name"]).set_index("node_id")["name"]
    except Exception:
        return pd.Series(dtype=object)


def _records(df: pd.DataFrame) -> list[dict[str, Any]]:
    return json.loads(df.to_json(orient="records"))  # NaN/NA → null, numpy → native


@app.post("/api/query")
def query(q: Query) -> dict[str, Any]:
    weights = q.weights or {}
    unknown = set(weights) - set(SCORE_COLS)
    if unknown:
        raise HTTPException(400, f"Unknown weight keys: {sorted(unknown)}")
    if any(v < 0 for v in weights.values()):
        raise HTTPException(400, "Weights must be non-negative")
    if not ingest.GRID_PATH.exists():
        raise HTTPException(503, "Node table is still being built; retry in a few minutes")

    with _model_lock:
        results, meta = pipeline.run(
            dc_capacity_mw=q.capacity_mw,
            dc_surface_m2=q.surface_m2,
            allowed_countries=[c.upper() for c in q.countries] if q.countries else None,
        )
        if results["gross"].empty:
            raise HTTPException(400, "No node meets the capacity and country constraints")
        order = rank.rank_by_weights(weights, top_n=len(results["pareto"]))
        detail = results["detail"].loc[order]
        norm = results["pareto"].loc[order, SCORE_COLS].add_prefix("norm_")
        meta = meta.loc[order]

    table = pd.concat([meta.rename(columns={"y": "lat", "x": "lng"}), detail, norm], axis=1)
    table.insert(0, "rank", range(1, len(table) + 1))
    table.insert(1, "name", table.index.map(_region_names()))
    status = ingest.status()
    return {
        "nodes": _records(table.reset_index()),
        "mix": ingest.load_mix(),
        "data_built_at": status["built_at"],
    }


@app.get("/api/sources")
def sources() -> dict[str, Any]:
    return ingest.status()


def _node_lock(node_id: str) -> threading.Lock:
    with _node_locks_guard:
        return _node_locks.setdefault(node_id, threading.Lock())


@app.get("/api/sites/{node_id}")
def site(node_id: str) -> dict[str, Any]:
    """Buildable-land analysis for one node (Sentinel-2 + Dynamic World CNN).
    First call per node runs the CNN (tens of seconds); later calls read the cache."""
    if site_stage is None:
        from src.model import site_stage_error
        raise HTTPException(503, f"Site analysis unavailable: {site_stage_error}")
    grid = pd.read_parquet(ingest.GRID_PATH, columns=["node_id", "x", "y"]).set_index("node_id")
    if node_id not in grid.index:
        raise HTTPException(404, f"Unknown node '{node_id}'")

    path = SITE_DIR / f"{node_id}.json"
    with _node_lock(node_id):
        if path.exists():
            res = json.loads(path.read_text(encoding="utf-8"))
        else:
            with _cnn_slots:
                try:
                    res = site_stage.analyze_node(node_id, float(grid.at[node_id, "y"]),
                                                  float(grid.at[node_id, "x"]), size_km=AOI_KM)
                except Exception as exc:
                    log.exception(f"site analysis failed for {node_id}")
                    raise HTTPException(502, f"Site analysis failed: {exc}") from exc
            if res.get("status") in ("ok", "no_buildable_land"):
                SITE_DIR.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(res, indent=2), encoding="utf-8")
    img = res.get("image")
    res["image_url"] = f"/site-images/{img}" if img and (SITE_DIR / img).exists() else None
    return res


SITE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/site-images", StaticFiles(directory=SITE_DIR), name="site-images")
app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO, format="[%(name)s] %(message)s")
    ap = argparse.ArgumentParser(description="DC Siting server")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--no-ingest", action="store_true", help="skip background data refresh")
    args = ap.parse_args()
    ENABLE_INGEST = not args.no_ingest
    uvicorn.run(app, host=args.host, port=args.port)
