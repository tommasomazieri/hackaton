"""
RANK — Stage 3
==============
Takes the 4-score DataFrame from 02_compute and produces three in-memory tables:

  _RESULTS["gross"]    raw scores as-is (indexed by node_id)
  _RESULTS["pareto"]   each score max-normalised to [0, 1]  (higher = worse)
  _RESULTS["balance"]  pareto table + balance_score = L2 norm of the 4 scores,
                       sorted ascending (rank 0 = best overall node)

All tables are indexed by node_id.  Metadata (x/y/country) is never merged in
here — callers join on index.
"""
import os
import sys

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
sys.path.insert(0, os.path.join(_PROJECT_ROOT, "src", "data_normalization"))
from _utils import setup_logger  # noqa: E402

log = setup_logger("03_rank")

SCORE_COLS = [
    "congestion_alpha",
    "dc_carbon_tco2_yr",
    "total_cost_eur",
    "connectivity_score",
]

# Module-level cache — both tables persist in RAM across calls within the same process
_RESULTS: dict[str, pd.DataFrame] = {}


def _max_normalise(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Divide each column by its max; zero-max columns become 0."""
    out = df.copy()
    for col in cols:
        mx = out[col].max(skipna=True)
        if mx and mx > 0:
            out[col] = out[col] / mx
        else:
            out[col] = 0.0
    return out


def run(df: pd.DataFrame, metadata: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """
    Args:
        df        scores_df from 02_compute.run(), indexed by node_id.
        metadata  metadata_df from 01_load_filter.run(), indexed by node_id.
                  Stored on _RESULTS["metadata"] for caller convenience.

    Returns:
        _RESULTS dict with keys "gross", "pareto", "balance", "metadata".
    """
    present_scores = [c for c in SCORE_COLS if c in df.columns]
    missing = set(SCORE_COLS) - set(present_scores)
    if missing:
        log.warning(f"Score columns missing, will be NaN: {missing}")
        for col in missing:
            df = df.copy()
            df[col] = np.nan

    # -------------------------------------------------------------------------
    # 1. Gross table — raw scores, no transformation
    # -------------------------------------------------------------------------
    _RESULTS["gross"] = df[SCORE_COLS].copy()
    log.info(f"Gross table stored: {len(_RESULTS['gross'])} nodes")

    # -------------------------------------------------------------------------
    # 2. Pareto (max-normalised) table
    # -------------------------------------------------------------------------
    pareto = _max_normalise(df[SCORE_COLS], SCORE_COLS)
    _RESULTS["pareto"] = pareto
    log.info(
        "Pareto table stored. Score ranges: "
        + ", ".join(f"{c}=[{pareto[c].min():.3f},{pareto[c].max():.3f}]" for c in SCORE_COLS)
    )

    # -------------------------------------------------------------------------
    # 3. Balance score — L2 norm in normalised 4-D space
    #    sqrt(Σ score_i²) ∈ [0, 2] (max = sqrt(4) when all scores = 1)
    #    Lower = better balanced across all dimensions.
    # -------------------------------------------------------------------------
    balance = pareto.copy()
    balance["balance_score"] = np.sqrt(
        (balance[SCORE_COLS].to_numpy() ** 2).sum(axis=1)
    )
    balance = balance.sort_values("balance_score")
    _RESULTS["balance"] = balance
    log.info(
        f"Balance table stored. Top node: {balance.index[0]}  "
        f"score={balance['balance_score'].iloc[0]:.4f}"
    )

    # -------------------------------------------------------------------------
    # 4. Metadata pass-through (kept separate, aligned with surviving nodes)
    # -------------------------------------------------------------------------
    _RESULTS["metadata"] = metadata.loc[df.index]

    return _RESULTS
