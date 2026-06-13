"""
LOAD & FILTER — Stage 1
=======================
Loads data/grid_nodes.parquet, splits metadata from scores, clips negative
prices to zero, then hard-gates nodes whose installed capacity is below the
requested DC demand.

Node size proxy (area / radius)
-------------------------------
In a more developed version of this proof of concept, each node's physical size
could be inferred precisely from the land areas (substation service territory /
catchment polygons) that belong to it. Gathering and attributing that geometry
is slow, so for this MVP we take a shortcut: every node is assigned an area
equal to 1/n of its country's total land area, where n is the number of nodes
in that country. The node is then treated as a circle, so we derive a radius
from that area (radius_km = sqrt(area_km2 / pi)). Both `area_km2` and
`radius_km` are emitted as node metadata. These are deliberately coarse MVP
assumptions, not real footprints.

Returns:
    scores_df   pd.DataFrame  — scoring columns, indexed by node_id
    metadata_df pd.DataFrame  — x / y / country / area_km2 / radius_km, by node_id
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

# Total land area (km²) per ISO-3166 alpha-2 country code. Used only for the MVP
# node-size proxy (see module docstring): area_km2 = country_area / n_country_nodes.
COUNTRY_AREA_KM2 = {
    "AT": 83879, "BE": 30528, "BG": 110879, "CY": 9251, "CZ": 78867,
    "DE": 357022, "DK": 43094, "EE": 45227, "ES": 505992, "FI": 338424,
    "FR": 551695, "HR": 56594, "HU": 93028, "IE": 70273, "IT": 301340,
    "LT": 65300, "LU": 2586, "LV": 64589, "MT": 316, "NL": 41543,
    "NO": 385207, "PL": 312696, "PT": 92090, "RO": 238397, "SE": 450295,
    "SI": 20273, "SK": 49035,
}


def run(
    dc_capacity_mw: float,
    dc_surface_m2: float,
    grid_path: str | None = None,
    allowed_countries: list[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Args:
        dc_capacity_mw    Required generation headroom (MW) — hard filter threshold.
        dc_surface_m2     DC footprint in square metres (use km2 * 1e6 to convert).
        grid_path         Override default data/grid_nodes.parquet path.
        allowed_countries ISO2 whitelist — hard gate on node country. None / empty
                          ⇒ no country filter (all countries pass).

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
    # Node size proxy (MVP shortcut — see module docstring).
    # area_km2  = country land area / number of nodes in that country
    # radius_km = sqrt(area_km2 / pi)  (node treated as a circle)
    # Computed on the full set so size is a stable physical property, not query-
    # dependent; carried through the capacity gate via the metadata slice below.
    # -------------------------------------------------------------------------
    node_counts = metadata["country"].map(metadata["country"].value_counts())
    country_area = metadata["country"].map(COUNTRY_AREA_KM2)
    n_unknown = country_area.isna().sum()
    if n_unknown:
        log.warning(f"No country area for {n_unknown} node(s) — area_km2 left NaN")
    metadata["area_km2"] = country_area / node_counts
    metadata["radius_km"] = np.sqrt(metadata["area_km2"] / np.pi)

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

    # -------------------------------------------------------------------------
    # Hard gate: country whitelist (optional). Empty / None ⇒ no filter.
    # -------------------------------------------------------------------------
    if allowed_countries:
        allowed = set(allowed_countries)
        keep = metadata.index[metadata["country"].isin(allowed)]
        scores = scores.loc[scores.index.intersection(keep)]
        metadata = metadata.loc[scores.index]
        log.info(f"Country filter {sorted(allowed)}: → {len(scores)} nodes")

    return scores, metadata
