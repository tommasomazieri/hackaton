"""
CONNECTIVITY SCORE — Grid Infrastructure + Fiber/Internet Access (Merged)
=========================================================================
Theory
------
Data center siting requires two distinct connectivity layers to be viable:

  1. GRID INFRASTRUCTURE ACCESS
     A DC drawing >10 MW must connect at ≥110 kV (EU NC DCC Regulation 2016/1388).
     Connection CapEx = €0.5–1.2 M/km for a 110 kV aerial line + €1–3 M substation
     bay works. Beyond ~10 km from the nearest HV substation, grid connection cost
     dominates project economics. This is a hard binary constraint disguised as a
     continuous variable: sites >20 km from any HV substation are typically non-viable.

  2. FIBER / INTERNET CONNECTIVITY
     Low-latency (<10 ms RTT) fiber to an Internet Exchange Point (IXP) or PoP is
     a hard technical requirement. DC tenants requiring <4 ms to financial exchanges
     or cloud on-ramps can only be served at fiber-rich sites. Fiber leasing cost
     (dark fiber IRU or lit service) grows with distance from the nearest IXP and
     falls with the number of competing providers within reach.

Composite Score Architecture
-----------------------------
Two sub-scores are computed independently and merged 50/50:

    grid_access_score        = norm(dist_to_hv_substation_km)         [0–1]
    fiber_connectivity_score = 0.6 × (1 − norm(ixp_count_50km))
                             + 0.4 × norm(dist_to_nearest_ixp_km)     [0–1]

    connectivity_score = 0.5 × grid_access_score
                       + 0.5 × fiber_connectivity_score               [0–1]

DIRECTION: lower score = better site (closer to HV substation, more IXPs,
closer to nearest IXP). Consistent with energy_price, land_price, carbon_intensity
where lower = preferable. Score 0 = ideal connectivity; score 1 = worst connectivity.

Equal weighting (50/50) between grid and fiber reflects that both are hard
constraints: a DC that can't connect to the grid OR can't get fiber is non-viable,
regardless of how good the other dimension is.

Sub-signals
-----------
dist_to_hv_substation_km — OSM `power=substation` (voltage ≥ 110 kV). Direct
  CapEx driver. OSM has near-complete coverage for transmission-level substations.

ixp_count_50km — OSM `telecom=exchange` within 50 km. Proxies fiber provider
  count and dark fiber market competitiveness. 50 km = practical fiber leasing
  radius in EU metro areas. (No dedicated OSM fiber tag exists — see
  docs/independent-variables.md §2.)

dist_to_nearest_ixp_km — Distance to closest `telecom=exchange`. Sanity check:
  catches fiber-desert nodes where ixp_count_50km = 0 but nearest IXP is at 51 km.

OSM Data Coverage Note
----------------------
`telecom=exchange` coverage is sparse in Eastern EU. Nodes in EE, LV, LT, BG, RO,
HR, SI, SK, HU get `infra_data_quality='sparse'` — their fiber sub-score may be
systematically understated. Grid sub-score is reliable EU-wide.

MVP Implementation
------------------
Two sub-scores (grid, fiber), each min-max normalized across all EU nodes,
merged 50/50 into connectivity_score [0–1].

Future Implementation
---------------------
[Empty — to be filled in dedicated planning session]

Real implementation:
  Grid: TSO GIS layers (ENTSO-E) or GridKit dataset (more complete than OSM)
  Fiber: PeeringDB IXP database + TeleGeography submarine/terrestrial cable maps
         + national dark fiber registry APIs (AMS-IX, DE-CIX, LINX public PoP lists)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import warnings
import numpy as np
import pandas as pd
from _utils import (
    setup_logger,
    get_paths,
    minmax_norm,
    EU_COUNTRIES_ISO2,
    OSM_SPARSE_COUNTRIES,
    ensure_dirs,
)

log = setup_logger("04_infra")

OSM_CACHE_FILE = None  # set at runtime from get_paths()

# ---------------------------------------------------------------------------
# OSM loading helpers
# ---------------------------------------------------------------------------

def _parse_osm_elements(elements: list) -> tuple[list, list]:
    """
    Split raw OSM elements into substations and IXP/telecom exchange points.

    Returns:
        substations: list of (lat, lon) tuples for HV substations (≥110 kV)
        exchanges:   list of (lat, lon) tuples for telecom=exchange nodes
    """
    substations = []
    exchanges = []

    for el in elements:
        tags = el.get("tags", {})
        eltype = el.get("type")

        # Determine coordinate
        if eltype == "node":
            lat = el.get("lat")
            lon = el.get("lon")
        elif eltype == "way":
            center = el.get("center", {})
            lat = center.get("lat")
            lon = center.get("lon")
        else:
            continue

        if lat is None or lon is None:
            continue

        power = tags.get("power", "")
        telecom = tags.get("telecom", "")

        # HV substation filter: voltage ≥ 110,000 V
        if power == "substation":
            voltage_str = tags.get("voltage", "")
            max_v = _max_voltage(voltage_str)
            if max_v is None or max_v >= 110_000:
                # Include if voltage missing (assume HV) or confirmed ≥110 kV
                substations.append((lat, lon))

        # Telecom exchange / IXP
        if telecom == "exchange":
            exchanges.append((lat, lon))

    return substations, exchanges


def _max_voltage(voltage_str: str) -> float | None:
    """Parse a semicolon-separated voltage string and return the maximum value."""
    if not voltage_str:
        return None
    try:
        vals = [float(v) for v in voltage_str.split(";") if v.strip().isdigit()]
        return max(vals) if vals else None
    except (ValueError, AttributeError):
        return None


def _load_from_json(json_path: str) -> tuple[list, list]:
    log.info(f"Loading OSM data from {json_path}…")
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    elements = data.get("elements", [])
    subs, exch = _parse_osm_elements(elements)
    log.info(f"  → {len(subs)} HV substations, {len(exch)} telecom exchanges")
    return subs, exch


def _load_from_cache_or_fetch(cache_path: str) -> tuple[list, list]:
    """Load EU-wide OSM data: from gpkg cache if present, else fetch via osmnx."""
    import geopandas as gpd

    if os.path.exists(cache_path):
        log.info(f"Loading OSM cache from {cache_path}…")
        try:
            subs_gdf = gpd.read_file(cache_path, layer="substations")
            exch_gdf = gpd.read_file(cache_path, layer="exchanges")
            subs = list(zip(subs_gdf.geometry.y, subs_gdf.geometry.x))
            exch = list(zip(exch_gdf.geometry.y, exch_gdf.geometry.x))
            log.info(f"  → {len(subs)} substations, {len(exch)} exchanges from cache")
            return subs, exch
        except Exception as exc:
            log.warning(f"Cache read failed ({exc}); re-fetching…")

    log.info("Fetching EU-wide OSM data via osmnx (this may take 20–40 min)…")
    try:
        import osmnx as ox
    except ImportError:
        raise ImportError(
            "osmnx is not installed. Run: pip install osmnx\n"
            "Or set OSM_DATA_PATH to a pre-downloaded OSM GeoJSON."
        )

    all_subs = []
    all_exch = []

    countries = list(EU_COUNTRIES_ISO2)
    for i, country_iso2 in enumerate(countries, 1):
        log.info(f"  [{i}/{len(countries)}] Fetching {country_iso2}…")
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                subs_gdf = ox.features_from_place(
                    f"{country_iso2}",
                    tags={"power": "substation"},
                )
                exch_gdf = ox.features_from_place(
                    f"{country_iso2}",
                    tags={"telecom": "exchange"},
                )

            # Get centroid coordinates
            for geom in subs_gdf.geometry:
                centroid = geom.centroid
                all_subs.append((centroid.y, centroid.x))

            for geom in exch_gdf.geometry:
                centroid = geom.centroid
                all_exch.append((centroid.y, centroid.x))

        except Exception as exc:
            log.warning(f"  Failed for {country_iso2}: {exc}")

    log.info(f"Fetch complete: {len(all_subs)} substations, {len(all_exch)} exchanges")

    # Save to cache
    try:
        from shapely.geometry import Point

        if all_subs:
            subs_gdf = gpd.GeoDataFrame(
                geometry=[Point(lon, lat) for lat, lon in all_subs],
                crs="EPSG:4326",
            )
            subs_gdf.to_file(cache_path, layer="substations", driver="GPKG")

        if all_exch:
            exch_gdf = gpd.GeoDataFrame(
                geometry=[Point(lon, lat) for lat, lon in all_exch],
                crs="EPSG:4326",
            )
            exch_gdf.to_file(cache_path, layer="exchanges", driver="GPKG")

        log.info(f"OSM cache saved → {cache_path}")
    except Exception as exc:
        log.warning(f"Could not save OSM cache: {exc}")

    return all_subs, all_exch


# ---------------------------------------------------------------------------
# Spatial distance computation
# ---------------------------------------------------------------------------

def _to_epsg3035(latlon_list: list) -> np.ndarray:
    """Convert [(lat, lon), …] to EPSG:3035 (meters). Returns (N, 2) array."""
    from pyproj import Transformer

    if not latlon_list:
        return np.empty((0, 2))

    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3035", always_xy=True)
    lons = [p[1] for p in latlon_list]
    lats = [p[0] for p in latlon_list]
    xs, ys = transformer.transform(lons, lats)
    return np.column_stack([xs, ys])


def _compute_signals(
    node_xy3035: np.ndarray,  # (N_nodes, 2) in EPSG:3035 metres
    sub_xy3035: np.ndarray,   # (N_subs, 2)
    exch_xy3035: np.ndarray,  # (N_exch, 2)
    radius_m: float = 50_000,  # 50 km in metres
) -> pd.DataFrame:
    """Compute three distance/count signals for each node."""
    from scipy.spatial import KDTree

    n = len(node_xy3035)

    # Sub-signal 1: distance to nearest HV substation (km)
    if len(sub_xy3035) > 0:
        tree_subs = KDTree(sub_xy3035)
        dist_sub_m, _ = tree_subs.query(node_xy3035, k=1)
        dist_sub_km = dist_sub_m / 1000.0
    else:
        log.warning("No HV substations available — dist_to_hv_substation_km set to NaN")
        dist_sub_km = np.full(n, np.nan)

    # Sub-signal 2: IXP count within 50 km
    # Sub-signal 3: distance to nearest IXP (km)
    if len(exch_xy3035) > 0:
        tree_exch = KDTree(exch_xy3035)
        ixp_indices = tree_exch.query_ball_point(node_xy3035, r=radius_m)
        ixp_count = np.array([len(idx) for idx in ixp_indices])
        dist_ixp_m, _ = tree_exch.query(node_xy3035, k=1)
        dist_ixp_km = dist_ixp_m / 1000.0
    else:
        log.warning("No telecom exchanges available — IXP signals set to NaN")
        ixp_count = np.zeros(n, dtype=int)
        dist_ixp_km = np.full(n, np.nan)

    return pd.DataFrame({
        "dist_to_hv_substation_km": dist_sub_km,
        "ixp_count_50km": ixp_count,
        "dist_to_nearest_ixp_km": dist_ixp_km,
    })


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run():
    paths = get_paths()
    ensure_dirs()

    # --- Load node centroids from 07_node_geometry output ---
    node_geom_path = os.path.join(paths["data_raw"], "node_geometry.parquet")
    if not os.path.exists(node_geom_path):
        raise FileNotFoundError(
            f"Node geometry not found at '{node_geom_path}'.\n"
            "Run 07_node_geometry.py first."
        )
    import geopandas as gpd

    nodes = gpd.read_parquet(node_geom_path)[["node_id", "x", "y", "country"]]
    log.info(f"Nodes loaded: {len(nodes)} bus centroids")

    # --- Load OSM data ---
    osm_env = os.environ.get("OSM_DATA_PATH", "")
    cache_path = os.path.join(paths["data_raw"], "osm_eu_cache.gpkg")

    if osm_env and os.path.exists(osm_env):
        log.info(f"Using OSM data from OSM_DATA_PATH: {osm_env}")
        if osm_env.endswith(".json"):
            substations, exchanges = _load_from_json(osm_env)
        else:
            substations, exchanges = _load_from_cache_or_fetch(osm_env)
    elif os.path.exists(cache_path):
        substations, exchanges = _load_from_cache_or_fetch(cache_path)
    elif os.path.exists(paths["osm_json"]):
        log.warning(
            f"Using Luxembourg-only OSM data from {paths['osm_json']}.\n"
            "  For EU-wide results, set OSM_DATA_PATH to a full EU OSM extract,\n"
            "  or delete data/osm_power_infrastructure.json to trigger EU fetch."
        )
        substations, exchanges = _load_from_json(paths["osm_json"])
    else:
        substations, exchanges = _load_from_cache_or_fetch(cache_path)

    # --- Project to EPSG:3035 for metre-based distance ---
    log.info("Projecting to EPSG:3035…")
    node_latlon = list(zip(nodes["y"].values, nodes["x"].values))
    node_xy = _to_epsg3035(node_latlon)
    sub_xy = _to_epsg3035(substations)
    exch_xy = _to_epsg3035(exchanges)

    # --- Compute signals ---
    log.info("Computing distance signals…")
    signals = _compute_signals(node_xy, sub_xy, exch_xy)

    # --- Two sub-scores, then merge 50/50 ---
    norm_dist_sub = minmax_norm(signals["dist_to_hv_substation_km"])
    norm_ixp_count = minmax_norm(signals["ixp_count_50km"].astype(float))
    norm_dist_ixp = minmax_norm(signals["dist_to_nearest_ixp_km"])

    # Lower = better (closer to substation, more IXPs nearby, closer to IXP)
    grid_access_score = norm_dist_sub                             # lower dist → lower score → better
    fiber_connectivity_score = 0.6 * (1.0 - norm_ixp_count) + 0.4 * norm_dist_ixp  # fewer/farther IXPs → higher score → worse
    connectivity_score = 0.5 * grid_access_score + 0.5 * fiber_connectivity_score

    # --- Assemble output ---
    result = nodes[["node_id", "country"]].copy().reset_index(drop=True)
    result["dist_to_hv_substation_km"] = signals["dist_to_hv_substation_km"].values
    result["ixp_count_50km"] = signals["ixp_count_50km"].values.astype(int)
    result["dist_to_nearest_ixp_km"] = signals["dist_to_nearest_ixp_km"].values
    result["grid_access_score"] = grid_access_score.values
    result["fiber_connectivity_score"] = fiber_connectivity_score.values
    result["connectivity_score"] = connectivity_score.values

    # Data quality flag for OSM-sparse countries
    result["infra_data_quality"] = result["country"].apply(
        lambda c: "sparse" if c in OSM_SPARSE_COUNTRIES else "ok"
    )

    n_sparse = (result["infra_data_quality"] == "sparse").sum()
    if n_sparse > 0:
        log.warning(
            f"{n_sparse} nodes flagged infra_data_quality='sparse' "
            f"(countries: {OSM_SPARSE_COUNTRIES & set(result['country'].unique())})"
        )

    log.info(
        f"connectivity_score range: "
        f"{result['connectivity_score'].min():.3f} – "
        f"{result['connectivity_score'].max():.3f}  "
        f"(grid_access: {result['grid_access_score'].mean():.3f} avg, "
        f"fiber: {result['fiber_connectivity_score'].mean():.3f} avg)"
    )

    out_path = os.path.join(paths["data_raw"], "infrastructure_access.parquet")
    result.to_parquet(out_path, index=False)
    log.info(f"Saved → {out_path}  ({len(result)} rows)")


if __name__ == "__main__":
    run()
