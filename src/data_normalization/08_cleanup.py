"""
CLEANUP — Validation, Spatial Join, and Processed Dataset Export
=================================================================
This script:
  1. Loads all raw parquet files from data/raw/
  2. Performs the NUTS2 spatial join to assign land_price_eur_ha to each node
  3. Validates all scoring columns for schema correctness and value ranges
  4. Saves cleaned tables to data/processed/

No normalization happens here — raw values are preserved.
The final assembly into grid_nodes.parquet is performed by 09_build_table.py.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from _utils import setup_logger, get_paths, ensure_dirs

log = setup_logger("08_cleanup")


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _check_range(df: pd.DataFrame, col: str, lo: float, hi: float,
                 action: str = "nan") -> pd.DataFrame:
    """Check a column against [lo, hi]. action: 'nan', 'clamp', 'warn'."""
    if col not in df.columns:
        return df
    mask = df[col].notna() & ~df[col].between(lo, hi)
    n_bad = mask.sum()
    if n_bad > 0:
        log.warning(f"{col}: {n_bad} values outside [{lo}, {hi}]")
        if action == "nan":
            df.loc[mask, col] = np.nan
        elif action == "clamp":
            df[col] = df[col].clip(lower=lo, upper=hi)
    return df


def _log_nan_frac(df: pd.DataFrame, label: str) -> None:
    nans = df.isnull().mean().round(3)
    non_zero = nans[nans > 0]
    if non_zero.empty:
        log.info(f"{label}: no NaN values")
    else:
        log.info(f"{label} NaN fractions:\n{non_zero.to_string()}")


# ---------------------------------------------------------------------------
# Land price spatial join
# ---------------------------------------------------------------------------

def _assign_land_price(
    nodes: pd.DataFrame,
    land_df: pd.DataFrame,
) -> pd.Series:
    """
    Assign land_price_eur_ha to each node.

    Strategy A (direct): if node_id looks like a NUTS code (e.g. 'DE254'),
    derive NUTS2 = node_id[:4] and look up directly — no spatial join needed.
    This applies when nodes come from GISCO NUTS3 centroids.

    Strategy B (spatial): for PyPSA bus IDs, fetch NUTS3 polygons from GISCO
    and do a point-in-polygon join.

    Fallback for unmatched nodes: country-level average land price.
    """
    import re
    import io
    import requests

    price_lookup = land_df.set_index("nuts2_code")["land_price_eur_ha"].to_dict()
    country_avg = (
        land_df.assign(country=land_df["nuts2_code"].str[:2])
        .groupby("country")["land_price_eur_ha"]
        .mean()
        .to_dict()
    )

    NUTS_PATTERN = re.compile(r"^[A-Z]{2}\d{2,3}$")

    # Strategy A: direct NUTS code lookup
    if nodes["node_id"].str.match(NUTS_PATTERN).mean() > 0.8:
        log.info("Land price: direct NUTS code lookup (node_id = NUTS3 code)")
        prices = {}
        n_nuts2 = n_country = n_missing = 0
        for _, row in nodes.iterrows():
            nid = row["node_id"]
            nuts2 = nid[:4] if len(nid) >= 4 else nid
            if nuts2 in price_lookup:
                prices[nid] = price_lookup[nuts2]
                n_nuts2 += 1
            elif row["country"] in country_avg:
                prices[nid] = country_avg[row["country"]]
                n_country += 1
            else:
                prices[nid] = float("nan")
                n_missing += 1
        log.info(
            f"Land price: {n_nuts2} NUTS2 matches, "
            f"{n_country} country-avg fallbacks, {n_missing} missing"
        )
        return pd.Series(prices, name="land_price_eur_ha")

    # Strategy B: spatial join via GISCO NUTS3 polygons
    log.info("Land price: spatial join via Eurostat GISCO NUTS3 polygons…")
    GISCO_URL = (
        "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/"
        "NUTS_RG_20M_2021_4326.geojson"
    )
    resp = requests.get(GISCO_URL, timeout=120)
    resp.raise_for_status()
    nuts_gdf = gpd.read_file(io.BytesIO(resp.content))
    nuts3_gdf = nuts_gdf[nuts_gdf["LEVL_CODE"] == 3][["NUTS_ID", "geometry"]].copy()
    nuts3_gdf["nuts2_code"] = nuts3_gdf["NUTS_ID"].str[:4]
    nuts3_gdf = nuts3_gdf.to_crs("EPSG:4326")

    node_pts = gpd.GeoDataFrame(
        nodes[["node_id", "country"]].copy(),
        geometry=gpd.points_from_xy(nodes["x"], nodes["y"]),
        crs="EPSG:4326",
    )
    joined = gpd.sjoin(node_pts, nuts3_gdf[["nuts2_code", "geometry"]],
                       how="left", predicate="within")

    prices = {}
    n_nuts2 = n_country = n_missing = 0
    for node_id, group in joined.groupby("node_id"):
        nuts2_vals = group["nuts2_code"].dropna()
        country = group["country"].iloc[0]
        nuts2 = nuts2_vals.iloc[0] if len(nuts2_vals) > 0 else None
        if nuts2 and nuts2 in price_lookup:
            prices[node_id] = price_lookup[nuts2]
            n_nuts2 += 1
        elif country in country_avg:
            prices[node_id] = country_avg[country]
            n_country += 1
        else:
            prices[node_id] = float("nan")
            n_missing += 1

    log.info(
        f"Land price: {n_nuts2} NUTS2 matches, "
        f"{n_country} country-avg fallbacks, {n_missing} missing"
    )
    return pd.Series(prices, name="land_price_eur_ha")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run():
    paths = get_paths()
    ensure_dirs()

    raw = paths["data_raw"]
    proc = paths["data_processed"]

    # -----------------------------------------------------------------------
    # 1. Node geometry (master key)
    # -----------------------------------------------------------------------
    geom_path = os.path.join(raw, "node_geometry.parquet")
    if not os.path.exists(geom_path):
        raise FileNotFoundError(
            f"Node geometry missing at '{geom_path}'.\n"
            "Run 07_node_geometry.py first."
        )
    nodes = pd.read_parquet(geom_path)
    log.info(f"Master node list: {len(nodes)} nodes")

    assert nodes["node_id"].is_unique, "Duplicate node_id in node_geometry!"
    assert "x" in nodes.columns and "y" in nodes.columns, \
        "x, y centroid columns missing from node_geometry"

    nodes.to_parquet(os.path.join(proc, "node_geometry.parquet"), index=False)
    _log_nan_frac(nodes, "node_geometry")

    # -----------------------------------------------------------------------
    # 2. Carbon emissions
    # -----------------------------------------------------------------------
    carbon_path = os.path.join(raw, "carbon_emissions.parquet")
    if os.path.exists(carbon_path):
        carbon = pd.read_parquet(carbon_path)
        carbon = _check_range(carbon, "carbon_intensity_elec", 0, 2000, action="nan")
        _log_nan_frac(carbon, "carbon_emissions")
        carbon.to_parquet(os.path.join(proc, "carbon_emissions.parquet"), index=False)
        log.info(f"carbon_emissions processed: {len(carbon)} rows")
    else:
        log.warning(f"carbon_emissions.parquet not found — skipping")

    # -----------------------------------------------------------------------
    # 3. Energy price
    # -----------------------------------------------------------------------
    ep_path = os.path.join(raw, "energy_price.parquet")
    if os.path.exists(ep_path):
        ep = pd.read_parquet(ep_path)
        ep = _check_range(ep, "energy_price_eur_mwh", -50, 5000, action="nan")
        _log_nan_frac(ep, "energy_price")
        ep.to_parquet(os.path.join(proc, "energy_price.parquet"), index=False)
        log.info(f"energy_price processed: {len(ep)} rows")
    else:
        log.warning("energy_price.parquet not found — skipping (PyPSA required)")

    # -----------------------------------------------------------------------
    # 4. Land price — fetch NUTS2 table and do spatial join to nodes
    # -----------------------------------------------------------------------
    lp_path = os.path.join(raw, "land_price.parquet")

    if os.path.exists(lp_path):
        land_df = pd.read_parquet(lp_path)
        land_df = _check_range(land_df, "land_price_eur_ha", 0, 1_000_000, action="nan")

        land_series = _assign_land_price(nodes, land_df)
        # Attach land price to node list for the processed output
        nodes_land = nodes[["node_id", "x", "y", "country"]].copy()
        nodes_land["land_price_eur_ha"] = nodes_land["node_id"].map(land_series)

        n_nan = nodes_land["land_price_eur_ha"].isna().sum()
        if n_nan > 0:
            from scipy.spatial import KDTree
            known = nodes_land["land_price_eur_ha"].notna()
            unknown = ~known
            if known.any():
                tree = KDTree(nodes_land.loc[known, ["x", "y"]].to_numpy())
                _, idx = tree.query(nodes_land.loc[unknown, ["x", "y"]].to_numpy(), k=1)
                nodes_land.loc[unknown, "land_price_eur_ha"] = (
                    nodes_land.loc[known, "land_price_eur_ha"].iloc[idx].values
                )
                log.info(f"KNN-imputed {n_nan} missing land prices from nearest non-NaN node")

        nodes_land.to_parquet(
            os.path.join(proc, "land_price.parquet"), index=False
        )
        _log_nan_frac(nodes_land, "land_price (node-level)")
        log.info(f"land_price processed: {len(nodes_land)} rows")
    else:
        log.warning("land_price.parquet not found — run 03_land_price.py first")

    # -----------------------------------------------------------------------
    # 5. Infrastructure access
    # -----------------------------------------------------------------------
    ia_path = os.path.join(raw, "infrastructure_access.parquet")
    if os.path.exists(ia_path):
        ia = pd.read_parquet(ia_path)
        ia = _check_range(ia, "connectivity_score", 0.0, 1.0, action="clamp")
        ia = _check_range(ia, "grid_access_score", 0.0, 1.0, action="clamp")
        ia = _check_range(ia, "fiber_connectivity_score", 0.0, 1.0, action="clamp")
        _log_nan_frac(ia, "infrastructure_access")
        ia.to_parquet(os.path.join(proc, "infrastructure_access.parquet"), index=False)
        log.info(f"infrastructure_access processed: {len(ia)} rows")
    else:
        log.warning("infrastructure_access.parquet not found — skipping")

    # -----------------------------------------------------------------------
    # 6. Congestion + consumption stats
    # -----------------------------------------------------------------------
    cong_path = os.path.join(raw, "congestion.parquet")
    if os.path.exists(cong_path):
        cong = pd.read_parquet(cong_path)
        cong = _check_range(cong, "congestion_frac", 0.0, 1.0, action="clamp")
        for col in ["consumption_mean_mw", "consumption_std_mw"]:
            cong = _check_range(cong, col, 0.0, 1e7, action="nan")
        _log_nan_frac(cong, "congestion")
        cong.to_parquet(os.path.join(proc, "congestion.parquet"), index=False)
        log.info(f"congestion processed: {len(cong)} rows")
    else:
        log.warning("congestion.parquet not found — skipping (PyPSA required)")

    # -----------------------------------------------------------------------
    # 7. Capacity (total installed generation capacity per node)
    # -----------------------------------------------------------------------
    cap_path = os.path.join(raw, "capacity.parquet")
    if os.path.exists(cap_path):
        cap = pd.read_parquet(cap_path)
        cap = _check_range(cap, "capacity_mw", 0.0, 1e7, action="nan")
        _log_nan_frac(cap, "capacity")
        cap.to_parquet(os.path.join(proc, "capacity.parquet"), index=False)
        log.info(f"capacity processed: {len(cap)} rows")
    else:
        log.warning("capacity.parquet not found — skipping (PyPSA required)")

    log.info("Cleanup complete. Processed tables in data/processed/")


if __name__ == "__main__":
    run()
