"""
BUILD TABLE — Final Dataset Assembly
======================================
Imports all processed parquet files from data/processed/, merges them on node_id,
and writes the final analysis-ready dataset to data/grid_nodes.parquet.

Output schema:

  Metadata columns (not scored):
    node_id             str       Bus/NUTS3 node id
    x                   float     Centroid longitude (EPSG:4326)
    y                   float     Centroid latitude  (EPSG:4326)
    country             str       ISO alpha-2

  Scoring columns (raw values):
    energy_price_eur_mwh    float   Annual mean LMP (€/MWh) — PyPSA
    land_price_eur_ha       float   Avg of last 10 annual values (€/ha) — Eurostat
    carbon_intensity_elec   float   National carbon intensity (gCO₂/kWh) — OWID
    connectivity_score      float   Composite grid+fiber connectivity 0–1
    congestion_frac         float   Fraction of hours >80% loading (0–1) — PyPSA
    consumption_mean_mw     float   Mean hourly load at node (MW) — PyPSA
    consumption_std_mw      float   Std dev hourly load at node (MW) — PyPSA
    capacity_mw             float   Total installed generation capacity (MW) — PyPSA

All scoring columns may be NaN where the upstream source is unavailable
(PyPSA-dependent columns are NaN if no network file was provided).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from _utils import setup_logger, get_paths

log = setup_logger("09_build")

METADATA_COLS = ["node_id", "x", "y", "country"]
SCORING_COLS = [
    "energy_price_eur_mwh",
    "land_price_eur_ha",
    "carbon_intensity_elec",
    "connectivity_score",
    "congestion_frac",
    "consumption_mean_mw",
    "consumption_std_mw",
    "capacity_mw",
]


def _load_processed(paths: dict, name: str, key: str = "node_id") -> pd.DataFrame | None:
    """Load a processed parquet; return None with warning if missing."""
    fpath = os.path.join(paths["data_processed"], f"{name}.parquet")
    if not os.path.exists(fpath):
        log.warning(f"{name}.parquet not in data/processed/ — column(s) will be NaN")
        return None
    return pd.read_parquet(fpath)


def _run_fallbacks(paths: dict) -> None:
    """Auto-run fallback + cleanup if PyPSA-dependent processed files are missing."""
    pypsa_files = ["energy_price", "congestion", "capacity"]
    missing = [
        f for f in pypsa_files
        if not os.path.exists(os.path.join(paths["data_processed"], f"{f}.parquet"))
    ]
    if missing:
        log.info(f"Missing processed files {missing} — running 10_pypsa_fallback.py")
        import importlib.util, pathlib
        here = pathlib.Path(__file__).parent
        for script in ("10_pypsa_fallback", "08_cleanup"):
            spec = importlib.util.spec_from_file_location(script, here / f"{script}.py")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.run()


def run():
    paths = get_paths()
    out_path = os.path.join(paths["data"], "grid_nodes.parquet")

    _run_fallbacks(paths)

    # -----------------------------------------------------------------------
    # 1. Spine: node geometry (GeoDataFrame)
    # -----------------------------------------------------------------------
    geom = _load_processed(paths, "node_geometry")
    if geom is None:
        raise FileNotFoundError(
            "node_geometry.parquet is missing from data/processed/.\n"
            "Run 07_node_geometry.py and 08_cleanup.py first."
        )
    result = geom.copy()
    log.info(f"Spine: {len(result)} nodes")

    # -----------------------------------------------------------------------
    # 2. Energy price
    # -----------------------------------------------------------------------
    ep = _load_processed(paths, "energy_price")
    if ep is not None:
        result = result.merge(
            ep[["node_id", "energy_price_eur_mwh"]],
            on="node_id", how="left",
        )
        log.info(f"energy_price joined: {result['energy_price_eur_mwh'].notna().sum()} nodes with values")
    else:
        result["energy_price_eur_mwh"] = float("nan")

    # -----------------------------------------------------------------------
    # 3. Carbon emissions (country-level join)
    # -----------------------------------------------------------------------
    carbon = _load_processed(paths, "carbon_emissions")
    if carbon is not None:
        result = result.merge(
            carbon[["country", "carbon_intensity_elec"]],
            on="country", how="left",
        )
        log.info(f"carbon joined: {result['carbon_intensity_elec'].notna().sum()} nodes with values")
    else:
        result["carbon_intensity_elec"] = float("nan")

    # -----------------------------------------------------------------------
    # 4. Land price (already node-level from 08_cleanup.py)
    # -----------------------------------------------------------------------
    land = _load_processed(paths, "land_price")
    if land is not None and "land_price_eur_ha" in land.columns:
        result = result.merge(
            land[["node_id", "land_price_eur_ha"]],
            on="node_id", how="left",
        )
        log.info(f"land_price joined: {result['land_price_eur_ha'].notna().sum()} nodes with values")
    else:
        result["land_price_eur_ha"] = float("nan")

    # -----------------------------------------------------------------------
    # 5. Infrastructure access
    # -----------------------------------------------------------------------
    ia = _load_processed(paths, "infrastructure_access")
    if ia is not None:
        ia_cols = ["node_id", "connectivity_score", "grid_access_score",
                   "fiber_connectivity_score", "infra_data_quality",
                   "dist_to_hv_substation_km", "ixp_count_50km",
                   "dist_to_nearest_ixp_km"]
        ia_cols = [c for c in ia_cols if c in ia.columns]
        result = result.merge(ia[ia_cols], on="node_id", how="left")
        log.info(f"connectivity joined: {result['connectivity_score'].notna().sum()} nodes with values")
    else:
        result["connectivity_score"] = float("nan")

    # -----------------------------------------------------------------------
    # 6. Congestion + consumption stats
    # -----------------------------------------------------------------------
    cong = _load_processed(paths, "congestion")
    if cong is not None:
        cong_cols = ["node_id", "congestion_frac",
                     "consumption_mean_mw", "consumption_std_mw"]
        cong_cols = [c for c in cong_cols if c in cong.columns]
        result = result.merge(cong[cong_cols], on="node_id", how="left")
        log.info(f"congestion joined: {result['congestion_frac'].notna().sum()} nodes with values")
    else:
        for col in ["congestion_frac", "consumption_mean_mw", "consumption_std_mw"]:
            result[col] = float("nan")

    # -----------------------------------------------------------------------
    # 7. Capacity (total installed generation capacity)
    # -----------------------------------------------------------------------
    cap = _load_processed(paths, "capacity")
    if cap is not None:
        result = result.merge(
            cap[["node_id", "capacity_mw"]],
            on="node_id", how="left",
        )
        log.info(f"capacity joined: {result['capacity_mw'].notna().sum()} nodes with values")
    else:
        result["capacity_mw"] = float("nan")

    # -----------------------------------------------------------------------
    # 8. Final validation
    # -----------------------------------------------------------------------
    assert result["node_id"].is_unique, "Duplicate node_id in final table"
    assert result["node_id"].notna().all(), "NaN node_id in final table"
    assert "x" in result.columns and "y" in result.columns, "x, y missing"

    n_rows = len(result)
    n_countries = result["country"].nunique()
    log.info(f"\nFinal table: {n_rows} rows, {n_countries} countries")

    # NaN summary for scoring columns
    nan_summary = result[SCORING_COLS].isnull().mean().round(3)
    log.info(f"NaN fractions per scoring column:\n{nan_summary.to_string()}")

    # -----------------------------------------------------------------------
    # 9. Column order: metadata first, then scoring, then diagnostics
    # -----------------------------------------------------------------------
    diag_cols = [
        c for c in result.columns
        if c not in METADATA_COLS + SCORING_COLS
    ]
    final_cols = METADATA_COLS + SCORING_COLS + diag_cols
    final_cols = [c for c in final_cols if c in result.columns]
    result = result[final_cols]

    result.to_parquet(out_path, index=False)
    size_mb = os.path.getsize(out_path) / 1e6
    log.info(f"Saved → {out_path}  ({n_rows} rows, {size_mb:.1f} MB)")


if __name__ == "__main__":
    run()
