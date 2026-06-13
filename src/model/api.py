from __future__ import annotations

import math
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.model.pipeline import run as pipeline_run

app = FastAPI(title="DC Siting API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.post("/run")
def run_pipeline(req: RunRequest) -> dict[str, Any]:
    global _results, _metadata
    results, metadata = pipeline_run(
        dc_capacity_mw=req.capacity_mw,
        dc_surface_m2=req.surface_m2,
    )
    n = len(results["balance"])
    if n == 0:
        raise HTTPException(status_code=400, detail="No nodes meet capacity constraint")
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
    if node_id not in _results["gross"].index:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found")
    gross_row = _results["gross"].loc[node_id]
    meta_row = _metadata.loc[node_id]
    return {
        "node_id": node_id,
        "country": meta_row["country"],
        "lat": meta_row["y"],
        "lng": meta_row["x"],
        "congestion_alpha": gross_row["congestion_alpha"],
        "carbon_tco2_yr": gross_row["dc_carbon_tco2_yr"],
        "total_cost_eur_yr": gross_row["total_cost_eur"],
        "connectivity_score": gross_row["connectivity_score"],
    }


@app.get("/results/raw")
def get_raw() -> list[dict[str, Any]]:
    _require_run()
    gross = _results["gross"].copy()
    gross = gross.join(_metadata[["country"]])
    return _df_to_records(gross)


@app.get("/results/pareto")
def get_pareto() -> list[dict[str, Any]]:
    _require_run()
    top10_ids = _results["balance"].head(10).index
    return _df_to_records(_results["pareto"].loc[top10_ids])


@app.get("/results/balance")
def get_balance() -> list[dict[str, Any]]:
    _require_run()
    balance = _results["balance"].head(10).copy()
    balance = balance.join(_metadata[["country"]])
    return _df_to_records(balance)
