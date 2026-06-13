"""
NODE GEOMETRY — NUTS3 Centroids as Grid Node Proxies
=====================================================
Theory
------
The atomic spatial unit for scoring is a grid node — a point in geographic space
with associated electricity grid and land characteristics. Ideally these are PyPSA
bus locations (physical HV substations). Without a solved PyPSA network we use
NUTS3 administrative centroids as node proxies.

NUTS3 regions are the finest administrative division available EU-wide from
Eurostat. Each NUTS3 centroid approximates the centre of mass of its territory.
This is a coarser representation than individual substations but still provides
sub-national resolution sufficient for DC siting recommendations.

x, y centroid coordinates are the only required geometry: they drive the NUTS2
spatial join for land price assignment in 08_cleanup.py.

Source (primary): PyPSA `n.buses` — actual substation locations, one row per bus.
Source (fallback): Eurostat GISCO NUTS3 polygon centroids (this script).

MVP Implementation
------------------
1. If PYPSA_NETWORK_PATH is set: use n.buses[['x','y','country']] directly.
2. Else: fetch NUTS3 polygons from Eurostat GISCO API, compute centroids, filter
   to EU27+NO, export node_id=NUTS_ID, x=lon, y=lat, country=NUTS_ID[:2].

No polygon geometry stored — not needed for any downstream operation.

Future Implementation
---------------------
[Empty — to be filled in dedicated planning session]

Real implementation: use PyPSA-Eur `resources/regions_onshore.geojson` (Voronoi
catchment areas from solved full-resolution network) for true substation-level
node geometry and accurate catchment area computation.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import io
import requests
import geopandas as gpd
import pandas as pd
from _utils import setup_logger, get_paths, ensure_dirs, EU_COUNTRIES_ISO2

log = setup_logger("07_geometry")

GISCO_URL = (
    "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/"
    "NUTS_RG_20M_2021_4326.geojson"
)


def _from_pypsa() -> pd.DataFrame | None:
    """Try to load node list from PyPSA network. Returns None if unavailable."""
    try:
        from _utils import get_pypsa_network
        n = get_pypsa_network()
        buses = n.buses[["x", "y", "country"]].copy().reset_index()
        buses = buses.rename(columns={"Bus": "node_id", "index": "node_id"})
        if "node_id" not in buses.columns:
            buses = buses.reset_index().rename(columns={"index": "node_id"})
        buses = buses[buses["country"].isin(EU_COUNTRIES_ISO2)]
        log.info(f"PyPSA nodes: {len(buses)} buses")
        return buses[["node_id", "x", "y", "country"]]
    except Exception as exc:
        log.warning(f"PyPSA unavailable ({exc}) — falling back to NUTS3 centroids")
        return None


def _from_gisco() -> pd.DataFrame:
    """Fetch NUTS3 polygons from Eurostat GISCO, compute centroids."""
    log.info("Fetching NUTS3 polygons from Eurostat GISCO…")
    resp = requests.get(GISCO_URL, timeout=120)
    resp.raise_for_status()
    gdf = gpd.read_file(io.BytesIO(resp.content))

    # NUTS3 = 5-char codes
    nuts3 = gdf[gdf["LEVL_CODE"] == 3].copy()
    nuts3 = nuts3[nuts3["CNTR_CODE"].isin(EU_COUNTRIES_ISO2)]
    nuts3 = nuts3.to_crs("EPSG:4326")

    centroids = nuts3.geometry.centroid
    result = pd.DataFrame({
        "node_id": nuts3["NUTS_ID"].values,
        "x": centroids.x.values,
        "y": centroids.y.values,
        "country": nuts3["CNTR_CODE"].values,
    })
    log.info(f"NUTS3 nodes: {len(result)} regions, {result['country'].nunique()} countries")
    return result


def run():
    paths = get_paths()
    ensure_dirs()

    nodes = _from_pypsa()
    if nodes is None:
        nodes = _from_gisco()

    assert nodes["node_id"].is_unique, "Duplicate node_id values"
    assert "x" in nodes.columns and "y" in nodes.columns
    assert nodes["x"].notna().all() and nodes["y"].notna().all()

    out_path = os.path.join(paths["data_raw"], "node_geometry.parquet")
    nodes.to_parquet(out_path, index=False)
    log.info(f"Saved → {out_path}  ({len(nodes)} rows)")


if __name__ == "__main__":
    run()
