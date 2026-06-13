"""
LOAD & FILTER — Stage 1
=======================
Loads data/grid_nodes.parquet, splits metadata from scores, clips negative
prices to zero, then hard-gates nodes whose installed capacity is below the
requested DC demand.

Returns:
    scores_df   pd.DataFrame  — scoring columns, indexed by node_id
    metadata_df pd.DataFrame  — x / y / country,  indexed by node_id
"""
import os
import sys

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
sys.path.insert(0, os.path.join(_PROJECT_ROOT, "src", "data_normalization"))
from _utils import setup_logger  # noqa: E402

log = setup_logger("01_load_filter")

METADATA_COLS = ["x", "y", "country"]  # node_id becomes the index
_DEFAULT_PATH = os.path.join(_PROJECT_ROOT, "data", "grid_nodes.parquet")

# Columns that must be clipped to [0, ∞) — prices cannot be negative for scoring
_CLIP_LOWER_ZERO = ["energy_price_eur_mwh", "land_price_eur_ha"]


def run(
    dc_capacity_mw: float,
    dc_surface_m2: float,
    grid_path: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Args:
        dc_capacity_mw  Required generation headroom (MW) — hard filter threshold.
        dc_surface_m2   DC footprint in square metres (use km2 * 1e6 to convert).
        grid_path       Override default data/grid_nodes.parquet path.

    Returns:
        (scores_df, metadata_df) — both indexed by node_id.
        capacity_mw is kept in scores_df; script 02_compute.py uses it for the
        congestion z-score and drops it there.
    """
    path = grid_path or _DEFAULT_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"grid_nodes.parquet not found at '{path}'.\n"
            "Run src/data_normalization/09_build_table.py first."
        )

    raw = pd.read_parquet(path)
    n_total = len(raw)
    log.info(f"Loaded {n_total} nodes from {path}")

    # -------------------------------------------------------------------------
    # Split metadata from scoring columns
    # -------------------------------------------------------------------------
    metadata = raw[["node_id"] + METADATA_COLS].set_index("node_id")
    scores = raw.drop(columns=METADATA_COLS).set_index("node_id")

    # -------------------------------------------------------------------------
    # Clip negative prices to zero
    # -------------------------------------------------------------------------
    for col in _CLIP_LOWER_ZERO:
        if col in scores.columns:
            neg_count = (scores[col] < 0).sum()
            if neg_count:
                log.info(f"  {col}: clipped {neg_count} negative value(s) to 0")
            scores[col] = scores[col].clip(lower=0)

    # -------------------------------------------------------------------------
    # Hard gate: capacity_mw must be >= dc_capacity_mw
    # NaN capacity rows are dropped (no data = cannot guarantee headroom)
    # -------------------------------------------------------------------------
    if "capacity_mw" not in scores.columns:
        log.warning("capacity_mw column missing — no hard gate applied")
    else:
        mask = scores["capacity_mw"].notna() & (scores["capacity_mw"] >= dc_capacity_mw)
        scores = scores.loc[mask]
        metadata = metadata.loc[scores.index]
        n_kept = len(scores)
        log.info(
            f"Hard gate ({dc_capacity_mw} MW): {n_total} → {n_kept} nodes "
            f"({n_total - n_kept} discarded)"
        )

    return scores, metadata
