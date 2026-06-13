from __future__ import annotations

import math
import os
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.model import rank, site_stage
from src.model.pipeline import run as pipeline_run

rank_by_weights = rank.rank_by_weights
SCORE_COLS = rank.SCORE_COLS

app = FastAPI(title="DC Siting API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stage-4 (CNN) writes per-node JSON + rendered PNGs here. Serve the PNGs at
# /site-images/<node_id>.png so the report can <img>-load them directly.
SITE_IMG_DIR = (
    site_stage.OUT_DIR if site_stage is not None
    else os.path.join(os.path.dirname(__file__), "..", "..", "data", "site_analysis")
)
os.makedirs(SITE_IMG_DIR, exist_ok=True)
app.mount("/site-images", StaticFiles(directory=SITE_IMG_DIR), name="site-images")

_results: dict[str, pd.DataFrame] | None = None
_metadata: pd.DataFrame | None = None


def _require_run() -> None:
    if _results is None:
        raise HTTPException(status_code=503, detail="No results cached — call POST /run first")


def _df_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    records = []
    for node_id, row in df.iterrows():
        rec = {"node_id": node_id}
        for k, v in row.items():
            rec[k] = None if (isinstance(v, float) and math.isnan(v)) else v
        records.append(rec)
    return records


class RunRequest(BaseModel):
    capacity_mw: float
    surface_m2: float
    countries: list[str] | None = None


class RankRequest(BaseModel):
    weights: dict[str, float] | None = None


class ReportImagesRequest(BaseModel):
    weights: dict[str, float] | None = None     # rank the same way the table does
    node_ids: list[str] | None = None           # or pass explicit ids
    top_n: int = 10
    aoi_km: float = 10.0


@app.post("/run")
def run_pipeline(req: RunRequest) -> dict[str, Any]:
    global _results, _metadata
    results, metadata = pipeline_run(
        dc_capacity_mw=req.capacity_mw,
        dc_surface_m2=req.surface_m2,
        allowed_countries=req.countries,
    )
    n = len(results["gross"])
    if n == 0:
        raise HTTPException(
            status_code=400,
            detail="No nodes meet the capacity and country constraints",
        )
    _results = results
    _metadata = metadata
    return {"status": "ok", "n_nodes": n}


@app.get("/nodes")
def get_nodes() -> list[dict[str, Any]]:
    _require_run()
    records = []
    for node_id, row in _metadata.iterrows():
        records.append({
            "node_id": node_id,
            "lat": row["y"],
            "lng": row["x"],
            "country": row["country"],
        })
    return records


@app.get("/nodes/{node_id}")
def get_node(node_id: str) -> dict[str, Any]:
    _require_run()
    if node_id not in _results["detail"].index:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found")
    meta_row = _metadata.loc[node_id]
    rec: dict[str, Any] = {
        "node_id": node_id,
        "country": meta_row["country"],
        "lat": meta_row["y"],
        "lng": meta_row["x"],
    }
    for k, v in _results["detail"].loc[node_id].items():
        rec[k] = None if (isinstance(v, float) and math.isnan(v)) else v
    return rec


@app.get("/results/raw")
def get_raw() -> list[dict[str, Any]]:
    _require_run()
    gross = _results["gross"].copy()
    gross = gross.join(_metadata[["country"]])
    return _df_to_records(gross)


@app.get("/results/detail")
def get_detail() -> list[dict[str, Any]]:
    """Full per-node breakdown (raw inputs + cost split + size proxy) for the popup."""
    _require_run()
    detail = _results["detail"].copy()
    meta_cols = [c for c in ["country", "area_km2", "radius_km"] if c in _metadata.columns]
    detail = detail.join(_metadata[meta_cols])
    return _df_to_records(detail)


@app.post("/results/ranked")
def get_ranked(req: RankRequest) -> list[dict[str, Any]]:
    """Top-10 nodes ranked by a weighted average of the normalised pareto scores.

    Returns raw (formatted-ready) score rows in best-first order. The weighted
    score itself is never returned — there is no aggregate column.
    """
    _require_run()

    weights = req.weights or {}
    unknown = set(weights) - set(SCORE_COLS)
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unknown weight keys: {sorted(unknown)}")
    if any(v < 0 for v in weights.values()):
        raise HTTPException(status_code=400, detail="Weights must be non-negative")
    if sum(weights.values()) > 1.0 + 1e-6:
        raise HTTPException(status_code=400, detail="Weights must sum to at most 1.0")

    idx = rank_by_weights(weights, top_n=10)
    gross = _results["gross"].loc[idx].join(_metadata[["country"]])
    return _df_to_records(gross)


@app.post("/report/site-images")
def post_report_images(req: ReportImagesRequest) -> list[dict[str, Any]]:
    """Lazy, cached CNN site imagery for the report. Computed only when called
    (report open), once per node — cached PNGs/JSON are reused on later calls.

    Returns one record per node, in rank order:
        { node_id, status, image_url, buildable_area_ha, dominant_buildable_class }
    `image_url` is None when the CNN produced no image (deps absent, no buildable
    land, or an error) — the frontend then shows a placeholder.
    """
    _require_run()
    if site_stage is None:
        from src.model import site_stage_error
        raise HTTPException(
            status_code=503,
            detail=f"Site-analysis stage unavailable: {site_stage_error}",
        )

    if req.node_ids:
        ids = req.node_ids
    else:
        weights = req.weights or {}
        unknown = set(weights) - set(SCORE_COLS)
        if unknown:
            raise HTTPException(status_code=400, detail=f"Unknown weight keys: {sorted(unknown)}")
        ids = list(rank_by_weights(weights, top_n=req.top_n))

    results = site_stage.run(ids, size_km=req.aoi_km, write=True, cache=True)

    out: list[dict[str, Any]] = []
    for res in results:
        img = res.get("image")
        out.append({
            "node_id": res.get("node_id"),
            "status": res.get("status", "error"),
            "image_url": f"/site-images/{img}" if img else None,
            "buildable_area_ha": res.get("buildable_area_ha"),
            "dominant_buildable_class": res.get("dominant_buildable_class"),
        })
    return out
