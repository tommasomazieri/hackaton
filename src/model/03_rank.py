"""
RANK — Stage 3
==============
Takes the 4-score DataFrame from 02_compute and produces in-memory tables:

  _RESULTS["gross"]    raw scores as-is (indexed by node_id)
  _RESULTS["detail"]   gross + every raw input & cost sub-component (popup view)
  _RESULTS["pareto"]   each score max-normalised to [0, 1]  (higher = worse)

There is no aggregate/balance table.  Ranking is computed on demand from the
pareto table via `rank_by_weights()` — a weighted average of the normalised
scores, with caller-supplied weights (default 1/n per column).

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


def rank_by_weights(weights: dict[str, float] | None = None, top_n: int = 10) -> pd.Index:
    """Rank nodes by a weighted average of the normalised pareto scores.

    Args:
        weights  per-column weights keyed by SCORE_COLS. Keys outside SCORE_COLS
                 are ignored; missing keys count as 0. Empty / all-zero falls
                 back to equal weights (1/n). Weights are normalised to sum 1.0.
        top_n    number of best nodes to return.

    Returns:
        Ordered node_id Index (best first). No score is returned — the aggregate
        is never exposed.
    """
    pareto = _RESULTS.get("pareto")
    if pareto is None:
        raise RuntimeError("Pareto table not built — call run() first")

    w = pd.Series(weights or {}, dtype=float).reindex(SCORE_COLS).fillna(0.0)
    if w.sum() <= 0:
        w[:] = 1.0 / len(SCORE_COLS)
    w = w / w.sum()

    score = (pareto[SCORE_COLS] * w).sum(axis=1)
    return score.sort_values().head(top_n).index


def run(df: pd.DataFrame, metadata: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """
    Args:
        df        scores_df from 02_compute.run(), indexed by node_id.
        metadata  metadata_df from 01_load_filter.run(), indexed by node_id.
                  Stored on _RESULTS["metadata"] for caller convenience.

    Returns:
        _RESULTS dict with keys "gross", "detail", "pareto", "metadata".
    """
    present_scores = [c for c in SCORE_COLS if c in df.columns]
    missing = set(SCORE_COLS) - set(present_scores)
    if missing:
        log.warning(f"Score columns missing, will be NaN: {missing}")
        for col in missing:
            df = df.copy()
            df[col] = np.nan

    # -------------------------------------------------------------------------
    # 1. Gross table — raw scores, no transformation (raw & ranked views use this)
    # -------------------------------------------------------------------------
    _RESULTS["gross"] = df[SCORE_COLS].copy()
    log.info(f"Gross table stored: {len(_RESULTS['gross'])} nodes")

    # Detail table — every column 02_compute produced (raw inputs + cost split).
    # Feeds the map popup; never sliced to SCORE_COLS.
    _RESULTS["detail"] = df.copy()
    log.info(f"Detail table stored: {len(_RESULTS['detail'])} nodes, "
             f"columns={list(_RESULTS['detail'].columns)}")

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
    # 3. Metadata pass-through (kept separate, aligned with surviving nodes)
    # -------------------------------------------------------------------------
    _RESULTS["metadata"] = metadata.loc[df.index]

    return _RESULTS
