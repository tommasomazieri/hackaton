"""
MODEL PIPELINE — orchestrator
==============================
Thin wrapper that strings 01 → 02 → 03 together.

Usage:
    from src.model.pipeline import run

    results, metadata = run(dc_capacity_mw=100, dc_surface_m2=50_000)
    # results["balance"]  — ranked table (best first)
    # results["pareto"]   — normalised scores
    # results["gross"]    — raw scores
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
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """
    Args:
        dc_capacity_mw  DC power demand in MW (hard filter + congestion model).
        dc_surface_m2   DC footprint in m² (land cost scaling).
        grid_path       Override path to grid_nodes.parquet (optional).

    Returns:
        (results_dict, metadata_df)
        results_dict keys: "gross", "pareto", "balance", "metadata"
    """
    scores, metadata = load_filter.run(
        dc_capacity_mw=dc_capacity_mw,
        dc_surface_m2=dc_surface_m2,
        grid_path=grid_path,
    )
    scores = compute.run(
        df=scores,
        dc_capacity_mw=dc_capacity_mw,
        dc_surface_m2=dc_surface_m2,
    )
    results = rank.run(df=scores, metadata=metadata)
    return results, metadata
