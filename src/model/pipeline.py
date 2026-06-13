"""
MODEL PIPELINE — orchestrator
==============================
Thin wrapper that strings 01 → 02 → 03 together.

Usage:
    from src.model.pipeline import run

    results, metadata = run(dc_capacity_mw=100, dc_surface_m2=50_000)
    # results["pareto"]   — normalised scores (feeds rank.rank_by_weights)
    # results["gross"]    — raw scores
    # results["detail"]   — raw inputs + cost split (popup view)
    # metadata            — x / y / country for surviving nodes

Surface units:
    dc_surface_m2  — always in square metres.
    Pass km2 as:   dc_surface_m2=your_value * 1e6
"""
from __future__ import annotations

import pandas as pd

from src.model import load_filter, compute, rank


def run(
    dc_capacity_mw: float,
    dc_surface_m2: float,
    grid_path: str | None = None,
    allowed_countries: list[str] | None = None,
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """
    Args:
        dc_capacity_mw    DC power demand in MW (hard filter + congestion model).
        dc_surface_m2     DC footprint in m² (land cost scaling).
        grid_path         Override path to grid_nodes.parquet (optional).
        allowed_countries ISO2 whitelist — only these countries are considered.
                          None / empty ⇒ no country filter (all countries).

    Returns:
        (results_dict, metadata_df)
        results_dict keys: "gross", "detail", "pareto", "metadata"
    """
    scores, metadata = load_filter.run(
        dc_capacity_mw=dc_capacity_mw,
        dc_surface_m2=dc_surface_m2,
        grid_path=grid_path,
        allowed_countries=allowed_countries,
    )
    # No surviving nodes (capacity + country gates too strict). Skip compute/rank
    # (which can't normalise an empty frame) and return empty tables — the API
    # turns this into a clean 400.
    if scores.empty:
        empty = {"gross": scores, "detail": scores, "pareto": scores, "metadata": metadata}
        return empty, metadata
    scores = compute.run(
        df=scores,
        dc_capacity_mw=dc_capacity_mw,
        dc_surface_m2=dc_surface_m2,
    )
    results = rank.run(df=scores, metadata=metadata)
    return results, metadata
