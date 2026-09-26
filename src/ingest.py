"""
LIVE INGEST — builds data/grid_nodes.parquet from public sources
=================================================================
Every source is fetched over HTTP and cached under data/live/ with a TTL. A
failed refresh falls back to the last good copy (marked "stale"), so the table
never regresses to nothing. `build()` joins the sources into the exact schema
src/model/01_load_filter.py reads. Methodology per column: docs/methodology.md.

    python -m src.ingest              # refresh expired sources, rebuild the table
    python -m src.ingest --force      # ignore TTLs, refetch everything
    python -m src.ingest --selfcheck  # offline asserts on the transform logic
"""
from __future__ import annotations

import argparse
import io
import json
import logging
import os
import threading
import time
import warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from src.data_normalization._utils import ISO3_TO_ISO2, minmax_norm

ROOT = Path(__file__).resolve().parents[1]
GRID_PATH = ROOT / "data" / "grid_nodes.parquet"
LIVE = ROOT / "data" / "live"
STATE_PATH = LIVE / "sources.json"
MIX_PATH = LIVE / "country_mix.json"

log = logging.getLogger("ingest")
HTTP = requests.Session()
HTTP.headers["User-Agent"] = "dc-siting-tool/1.0 (research prototype)"

HOUR, DAY = 3600, 86400

COUNTRIES = set(ISO3_TO_ISO2.values())            # EU27 + NO, ISO alpha-2
NUTS_TO_ISO = {"EL": "GR"}                        # NUTS writes Greece as EL
# Not on the continental synchronous grid / no coupled day-ahead market:
# French overseas, Ceuta, Melilla, Canaries, Azores, Madeira, Svalbard.
OFFSHORE_NUTS = ("FRY", "ES63", "ES64", "ES70", "PT20", "PT30", "NO0B")

# --- original pipeline constants (10_pypsa_fallback.py) ---------------------
HOURS_IN_YEAR = 8_760
CAPACITY_FACTOR = 0.35
LOAD_CV = 0.20

# --- sources -------------------------------------------------------------------
GISCO_NUTS = ("https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/"
              "NUTS_RG_20M_2021_4326.geojson")
OWID_CSV = "https://owid-public.owid.io/data/energy/owid-energy-data.csv"
EUROSTAT_LAND = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/apri_lprc"
EC_PRICE = "https://api.energy-charts.info/price"
ZONE_GEOJSON = ("https://raw.githubusercontent.com/EnergieID/entsoe-py/master/"
                "entsoe/geo/geojson/{}.geojson")
OVERPASS = "https://overpass-api.de/api/interpreter"
PEERINGDB = "https://www.peeringdb.com/api"

# Energy-Charts licenses these zones CC BY 4.0 (Bundesnetzagentur | SMARD.de);
# every other zone is "for private and internal use only" (api.energy-charts.info).
EC_CC_BY = {"AT", "BE", "CH", "CZ", "DE-LU", "DE-AT-LU", "DK1", "DK2", "FR", "HU",
            "IT-North", "NL", "NO2", "PL", "SE4", "SI"}
# Countries split into several bidding zones → entsoe-py polygon file per zone.
MULTI_ZONE = {
    "DK1": "DK_1", "DK2": "DK_2",
    "IT-North": "IT_NORD", "IT-Centre-North": "IT_CNOR", "IT-Centre-South": "IT_CSUD",
    "IT-South": "IT_SUD", "IT-Calabria": "IT_CALA", "IT-Sicily": "IT_SICI",
    "IT-Sardinia": "IT_SARD",
    "NO1": "NO_1", "NO2": "NO_2", "NO3": "NO_3", "NO4": "NO_4", "NO5": "NO_5",
    "SE1": "SE_1", "SE2": "SE_2", "SE3": "SE_3", "SE4": "SE_4",
}
MULTI_ZONE_COUNTRIES = {"DK", "IT", "NO", "SE"}
SINGLE_ZONE = {"DE": "DE-LU", "LU": "DE-LU", "IE": "IE(SEM)"}  # else zone == country

MIX_COLS = {
    "coal": "coal_share_elec", "gas": "gas_share_elec", "oil": "oil_share_elec",
    "nuclear": "nuclear_share_elec", "hydro": "hydro_share_elec",
    "wind": "wind_share_elec", "solar": "solar_share_elec",
    "bioenergy": "biofuel_share_elec",
    "other_renewables": "other_renewables_share_elec_exc_biofuel",
}

SOURCES = {  # provenance shown at /api/sources
    "nodes": ("Node locations (NUTS 2021 level-3 centroids)", "Eurostat GISCO", GISCO_NUTS,
              "https://ec.europa.eu/eurostat/web/gisco/geodata/administrative-units"),
    "owid": ("Carbon intensity, demand, generation, supply mix", "Our World in Data energy dataset",
             OWID_CSV, "https://github.com/owid/energy-data"),
    "land": ("Farmland price, EUR/ha (NUTS 2)", "Eurostat apri_lprc", EUROSTAT_LAND,
             "https://ec.europa.eu/eurostat/about-us/policies/copyright"),
    "zones": ("Bidding-zone shapes (DK, IT, NO, SE)", "entsoe-py (MIT)",
              ZONE_GEOJSON.format("…"), "https://github.com/EnergieID/entsoe-py"),
    "price": ("Day-ahead price, trailing 365 days", "Energy-Charts (Fraunhofer ISE)", EC_PRICE,
              "https://api.energy-charts.info"),
    "substations": ("HV substations ≥110 kV", "OpenStreetMap via Overpass (ODbL)", OVERPASS,
                    "https://www.openstreetmap.org/copyright"),
    "ixps": ("Facilities hosting an internet exchange", "PeeringDB", PEERINGDB,
             "https://www.peeringdb.com/aup"),
}
TTL = {"nodes": 365 * DAY, "owid": 7 * DAY, "land": 30 * DAY, "zones": 365 * DAY,
       "price": DAY, "substations": 30 * DAY, "ixps": 7 * DAY}


# =============================================================================
# Cache: one parquet per key under data/live/, state in data/live/sources.json
# =============================================================================
_state_lock = threading.Lock()
_build_lock = threading.Lock()
_fetches = 0  # bumped on every successful network fetch; 0 ⇒ nothing changed


def _read_state() -> dict:
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return {}


def _update_state(key: str, entry: dict) -> None:
    with _state_lock:
        state = _read_state()
        state[key] = entry
        LIVE.mkdir(parents=True, exist_ok=True)
        _atomic_write_text(STATE_PATH, json.dumps(state, indent=1))


def _atomic_write_text(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    _replace(tmp, path)


def _replace(src: Path, dst: Path) -> None:
    # Windows refuses os.replace while a reader holds dst open; readers are brief.
    for attempt in range(20):
        try:
            os.replace(src, dst)
            return
        except PermissionError:
            if attempt == 19:
                raise
            time.sleep(0.25)


def cached(key: str, fetch, force: bool = False) -> pd.DataFrame:
    """Fresh cache → cached copy. Expired → fetch; if that fails, the stale copy."""
    global _fetches
    ttl = TTL[key.split("/")[0]]
    path = LIVE / f"{key}.parquet"
    entry = _read_state().get(key, {})
    if path.exists() and not force and time.time() - entry.get("fetched_ts", 0) < ttl:
        return pd.read_parquet(path)
    try:
        df = fetch()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        df.to_parquet(tmp, index=False)
        _replace(tmp, path)
        _fetches += 1
        _update_state(key, {"fetched_ts": time.time(), "status": "fresh", "rows": len(df)})
        return df
    except Exception as exc:
        err = f"{type(exc).__name__}: {exc}"[:300]
        if not path.exists():
            _update_state(key, {**entry, "status": "failed", "error": err})
            raise
        log.warning(f"{key}: refresh failed, serving stale copy ({err})")
        _update_state(key, {**entry, "status": "stale", "error": err})
        return pd.read_parquet(path)


# =============================================================================
# Fetchers
# =============================================================================
def fetch_nodes() -> pd.DataFrame:
    import geopandas as gpd
    r = HTTP.get(GISCO_NUTS, timeout=120)
    r.raise_for_status()
    gdf = gpd.read_file(io.BytesIO(r.content))
    gdf = gdf[gdf["LEVL_CODE"] == 3].copy()
    gdf["country"] = gdf["CNTR_CODE"].replace(NUTS_TO_ISO)
    gdf = gdf[gdf["country"].isin(COUNTRIES) & ~gdf["NUTS_ID"].str.startswith(OFFSHORE_NUTS)]
    with warnings.catch_warnings():  # geographic centroid, as in the original pipeline
        warnings.simplefilter("ignore")
        c = gdf.geometry.centroid
    return pd.DataFrame({"node_id": gdf["NUTS_ID"].to_numpy(), "x": c.x.to_numpy(),
                         "y": c.y.to_numpy(), "country": gdf["country"].to_numpy(),
                         "name": gdf["NAME_LATN"].to_numpy()})  # display only, not in the grid


def fetch_owid() -> pd.DataFrame:
    r = HTTP.get(OWID_CSV, timeout=120)
    r.raise_for_status()
    cols = ["iso_code", "year", "carbon_intensity_elec", "electricity_demand",
            "electricity_generation", *MIX_COLS.values()]
    df = pd.read_csv(io.BytesIO(r.content), usecols=cols)
    df = df[df["iso_code"].isin(ISO3_TO_ISO2) & (df["year"] >= 2010)]
    return df.assign(country=df["iso_code"].map(ISO3_TO_ISO2)).drop(columns="iso_code")


def jsonstat_frame(doc: dict) -> pd.DataFrame:
    """Decode a JSON-stat 2.0 dataset into long format (one column per dimension + value)."""
    ids, sizes = doc["id"], doc["size"]
    labels = []
    for d in ids:
        index = doc["dimension"][d]["category"]["index"]
        labels.append(list(index) if isinstance(index, list)
                      else [k for k, _ in sorted(index.items(), key=lambda kv: kv[1])])
    strides = [int(np.prod(sizes[i + 1:])) for i in range(len(sizes))]
    values = doc["value"]
    items = values.items() if isinstance(values, dict) else enumerate(values)
    rows = []
    for flat, v in items:
        if v is None:
            continue
        flat = int(flat)
        rec = {d: lab[(flat // st) % sz] for d, lab, st, sz in zip(ids, labels, strides, sizes)}
        rec["value"] = float(v)
        rows.append(rec)
    return pd.DataFrame(rows)


def fetch_land() -> pd.DataFrame:
    r = HTTP.get(EUROSTAT_LAND, params={"format": "JSON", "lang": "EN", "unit": "EUR_HA"},
                 timeout=120)
    r.raise_for_status()
    df = jsonstat_frame(r.json())
    df = df[df["geo"].str.fullmatch(r"[A-Z]{2}\d{2}")]
    df["year"] = df["time"].astype(int)
    return df[["geo", "agriprod", "year", "value"]].reset_index(drop=True)


def fetch_zone_shapes() -> pd.DataFrame:
    from shapely.geometry import shape
    from shapely.ops import unary_union
    rows = []
    for zone, fname in MULTI_ZONE.items():
        r = HTTP.get(ZONE_GEOJSON.format(fname), timeout=60)
        r.raise_for_status()
        geom = unary_union([shape(f["geometry"]) for f in r.json()["features"]])
        rows.append({"zone": zone, "country": zone[:2], "wkt": geom.wkt})
    return pd.DataFrame(rows)


_ec_lock = threading.Lock()
_ec_last = 0.0


def fetch_price(zone: str) -> pd.DataFrame:
    """Trailing-365-day day-ahead price stats for one bidding zone.
    Energy-Charts allows 2 requests/min (burst 2), so calls are spaced ≥31 s."""
    global _ec_last
    end = pd.Timestamp.now(tz="UTC").normalize()
    start = end - pd.Timedelta(days=365)
    params = {"bzn": zone, "start": start.strftime("%Y-%m-%d"), "end": end.strftime("%Y-%m-%d")}
    for _ in range(3):
        with _ec_lock:
            wait = _ec_last + 31 - time.time()
            if wait > 0:
                time.sleep(wait)
            _ec_last = time.time()
        r = HTTP.get(EC_PRICE, params=params, timeout=120)
        if r.status_code == 429:
            time.sleep(60)
            continue
        r.raise_for_status()
        d = r.json()
        s = pd.Series(d["price"], index=pd.to_datetime(d["unix_seconds"], unit="s"), dtype=float)
        hourly = s.resample("1h").mean().dropna()  # 15-min and hourly MTUs weigh the same
        if len(hourly) < 24 * 30:
            raise ValueError(f"only {len(hourly)} hourly prices for {zone}")
        return pd.DataFrame([{
            "zone": zone, "mean": hourly.mean(), "p05": hourly.quantile(0.05),
            "p95": hourly.quantile(0.95), "hours": len(hourly),
            "from": str(hourly.index.min().date()), "to": str(hourly.index.max().date()),
            "license": "CC BY 4.0" if zone in EC_CC_BY else "private and internal use only",
        }])
    raise RuntimeError(f"Energy-Charts rate limit persisted for {zone}")


def _max_voltage(v: str) -> float | None:
    vals = [float(p) for p in str(v).split(";") if p.strip().isdigit()]
    return max(vals) if vals else None


def fetch_substations(cc: str) -> pd.DataFrame:
    # Only substations with a ≥6-digit voltage tag (≥100 kV) come back; ≥110 kV kept below.
    q = (f'[out:json][timeout:600];area["ISO3166-1"="{cc}"][admin_level=2]->.a;'
         f'(nwr["power"="substation"]["voltage"~"[0-9]{{6}}"](area.a););out center tags;')
    for attempt in range(3):
        r = HTTP.post(OVERPASS, data={"data": q}, timeout=700)
        if r.status_code in (429, 504) and attempt < 2:
            time.sleep(30 * (attempt + 1))
            continue
        r.raise_for_status()
        break
    rows = []
    for el in r.json()["elements"]:
        pos = el if el["type"] == "node" else el.get("center", {})
        v = _max_voltage(el.get("tags", {}).get("voltage", ""))
        if "lat" in pos and v is not None and v >= 110_000:
            rows.append({"lat": pos["lat"], "lon": pos["lon"], "kv": v / 1000})
    if not rows:
        raise ValueError(f"no HV substations returned for {cc}")
    return pd.DataFrame(rows)


def fetch_ixps() -> pd.DataFrame:
    ixfac = HTTP.get(f"{PEERINGDB}/ixfac", params={"fields": "fac_id"}, timeout=60)
    ixfac.raise_for_status()
    fac_ids = {r["fac_id"] for r in ixfac.json()["data"]}
    fac = HTTP.get(f"{PEERINGDB}/fac", params={"fields": "id,latitude,longitude,status"},
                   timeout=60)
    fac.raise_for_status()
    rows = [{"lat": f["latitude"], "lon": f["longitude"]} for f in fac.json()["data"]
            if f["id"] in fac_ids and f.get("status") == "ok"
            and f.get("latitude") is not None and f.get("longitude") is not None
            and 34 <= f["latitude"] <= 72 and -25 <= f["longitude"] <= 45]  # Europe
    return pd.DataFrame(rows)


# =============================================================================
# Transforms (same formulas as the original data_normalization scripts)
# =============================================================================
def country_stats(owid: pd.DataFrame) -> pd.DataFrame:
    """Per-country carbon intensity (last reported year) and last non-null demand/generation."""
    owid = owid.sort_values("year")
    carbon = (owid.dropna(subset=["carbon_intensity_elec"]).groupby("country").last()
              [["carbon_intensity_elec", "year"]].rename(columns={"year": "carbon_year"}))
    energy = owid.groupby("country")[["electricity_demand", "electricity_generation"]].last()
    return carbon.join(energy, how="outer")


def grid_stats(stats: pd.DataFrame, n_nodes: pd.Series) -> pd.DataFrame:
    """OWID → per-node capacity / consumption / congestion (10_pypsa_fallback formulas)."""
    gen, dem = stats["electricity_generation"], stats["electricity_demand"]
    n = n_nodes.reindex(stats.index)
    out = pd.DataFrame(index=stats.index)
    out["capacity_mw"] = gen * 1e6 / HOURS_IN_YEAR / CAPACITY_FACTOR / n
    out["consumption_mean_mw"] = dem * 1e6 / HOURS_IN_YEAR / n
    out["consumption_std_mw"] = out["consumption_mean_mw"] * LOAD_CV
    out["congestion_frac"] = ((dem / gen).fillna(1.0) * 0.5 - 0.3).clip(lower=0.0, upper=0.95)
    return out


def country_mix(owid: pd.DataFrame) -> dict:
    owid = owid.sort_values("year")
    out = {}
    for cc, g in owid.dropna(subset=["coal_share_elec"]).groupby("country"):
        row = g.iloc[-1]
        out[cc] = {"year": int(row["year"]),
                   **{k: round(float(row[c]), 2) if pd.notna(row[c]) else None
                      for k, c in MIX_COLS.items()}}
    return out


def land_by_nuts2(land: pd.DataFrame) -> pd.Series:
    """Mean of the last 10 annual values per NUTS2; each year averages the land types."""
    per_year = land.groupby(["geo", "year"])["value"].mean().reset_index()
    last10 = per_year.sort_values("year").groupby("geo").tail(10)
    s = last10.groupby("geo")["value"].mean()
    return s[s.between(0, 1_000_000)]


def assign_land(nodes: pd.DataFrame, nuts2_price: pd.Series) -> pd.Series:
    """NUTS2 match → country average → nearest node with a value (08_cleanup order)."""
    from scipy.spatial import KDTree
    iso = pd.Series(nuts2_price.index.str[:2], index=nuts2_price.index).replace(NUTS_TO_ISO)
    country_avg = nuts2_price.groupby(iso.to_numpy()).mean()
    price = nodes["node_id"].str[:4].map(nuts2_price)
    price = price.fillna(nodes["country"].map(country_avg))
    known = price.notna().to_numpy()
    if known.any() and not known.all():
        tree = KDTree(nodes.loc[known, ["x", "y"]].to_numpy())
        _, idx = tree.query(nodes.loc[~known, ["x", "y"]].to_numpy(), k=1)
        price[~known] = price[known].to_numpy()[idx]
    return price


def assign_zones(nodes: pd.DataFrame, shapes: pd.DataFrame) -> pd.Series:
    """Bidding zone per node: country code, or point-in-polygon for split countries."""
    from shapely import wkt
    from shapely.geometry import Point
    zone = nodes["country"].map(lambda c: SINGLE_ZONE.get(c, c)).astype(object)
    geoms = [(r.zone, r.country, wkt.loads(r.wkt)) for r in shapes.itertuples()]
    for i in nodes.index[nodes["country"].isin(MULTI_ZONE_COUNTRIES)]:
        pt = Point(nodes.at[i, "x"], nodes.at[i, "y"])
        cands = [(z, g) for z, c, g in geoms if c == nodes.at[i, "country"]]
        hit = next((z for z, g in cands if g.contains(pt)), None)
        zone[i] = hit or min(cands, key=lambda zg: zg[1].distance(pt))[0]  # coastal centroid
    return zone


def connectivity(nodes: pd.DataFrame, subs: pd.DataFrame, ixps: pd.DataFrame) -> pd.DataFrame:
    """04_infrastructure_access formula: 0.5·grid + 0.5·fiber, lower = better."""
    from pyproj import Transformer
    from scipy.spatial import KDTree
    tr = Transformer.from_crs("EPSG:4326", "EPSG:3035", always_xy=True)

    def xy(lon, lat):
        return np.column_stack(tr.transform(np.asarray(lon), np.asarray(lat)))

    nxy = xy(nodes["x"], nodes["y"])
    d_sub = KDTree(xy(subs["lon"], subs["lat"])).query(nxy, k=1)[0] / 1000
    ix_tree = KDTree(xy(ixps["lon"], ixps["lat"]))
    n_ix = np.array([len(i) for i in ix_tree.query_ball_point(nxy, r=50_000)], dtype=float)
    d_ix = ix_tree.query(nxy, k=1)[0] / 1000

    out = pd.DataFrame({"dist_to_hv_substation_km": d_sub, "ixp_count_50km": n_ix.astype(int),
                        "dist_to_nearest_ixp_km": d_ix}, index=nodes.index)
    out["grid_access_score"] = minmax_norm(out["dist_to_hv_substation_km"])
    out["fiber_connectivity_score"] = (0.6 * (1.0 - minmax_norm(pd.Series(n_ix, index=nodes.index)))
                                       + 0.4 * minmax_norm(out["dist_to_nearest_ixp_km"]))
    out["connectivity_score"] = 0.5 * out["grid_access_score"] + 0.5 * out["fiber_connectivity_score"]
    return out


# =============================================================================
# Build
# =============================================================================
MODEL_COLS = ["energy_price_eur_mwh", "land_price_eur_ha", "carbon_intensity_elec",
              "connectivity_score", "congestion_frac", "consumption_mean_mw",
              "consumption_std_mw", "capacity_mw"]


def _try(key: str, fetch, force: bool) -> pd.DataFrame | None:
    try:
        return cached(key, fetch, force)
    except Exception as exc:
        log.error(f"{key}: unavailable ({exc})")
        return None


def build(force: bool = False) -> bool:
    """Refresh expired sources and rebuild grid_nodes.parquet. Returns True if rebuilt."""
    global _fetches
    with _build_lock:
        _fetches = 0
        _update_meta(building=True)
        try:
            return _build(force)
        finally:
            _update_meta(building=False)


def _build(force: bool) -> bool:
    nodes = cached("nodes", fetch_nodes, force)
    owid = cached("owid", fetch_owid, force)
    land = cached("land", fetch_land, force)
    shapes = cached("zones", fetch_zone_shapes, force)
    ixps = cached("ixps", fetch_ixps, force)

    zone = assign_zones(nodes, shapes)
    # Energy-Charts and Overpass are separate hosts: fetch both slow loops in parallel.
    with ThreadPoolExecutor(2) as ex:
        f_price = ex.submit(lambda: {z: _try(f"price/{z}", lambda z=z: fetch_price(z), force)
                                     for z in sorted(zone.unique())})
        f_subs = ex.submit(lambda: {cc: _try(f"substations/{cc}",
                                             lambda cc=cc: fetch_substations(cc), force)
                                    for cc in sorted(COUNTRIES)})
        prices, subs = f_price.result(), f_subs.result()

    if _fetches == 0 and GRID_PATH.exists() and not force:
        return False  # every source served from a fresh cache: table is current

    df = nodes.copy()
    df["price_zone"] = zone
    zone_price = {z: p["mean"].iloc[0] for z, p in prices.items() if p is not None}
    df["energy_price_eur_mwh"] = df["price_zone"].map(zone_price)
    df["land_price_eur_ha"] = assign_land(df, land_by_nuts2(land))
    stats = country_stats(owid)
    df["carbon_intensity_elec"] = df["country"].map(stats["carbon_intensity_elec"])

    # Range checks from 08_cleanup: out-of-range values are treated as missing.
    df.loc[~df["carbon_intensity_elec"].between(0, 2000), "carbon_intensity_elec"] = np.nan
    df.loc[~df["energy_price_eur_mwh"].between(-50, 5000), "energy_price_eur_mwh"] = np.nan

    # A node missing a model input would score NaN, which the ranking treats as 0
    # (best). Drop it instead, and say why.
    reasons = {
        "energy_price_eur_mwh": lambda r: f"no day-ahead price for zone {r.price_zone}",
        "carbon_intensity_elec": lambda r: "no carbon-intensity data for country",
    }
    excluded = []
    for col, why in reasons.items():
        miss = df[col].isna()
        excluded += [{"node_id": r.node_id, "country": r.country, "reason": why(r)}
                     for r in df[miss].itertuples()]
        df = df[~miss]

    n_nodes = df["country"].value_counts()
    df = df.join(grid_stats(stats, n_nodes), on="country")

    sub_frames = [s for s in subs.values() if s is not None]
    conn = connectivity(df, pd.concat(sub_frames, ignore_index=True), ixps)
    df = df.join(conn)
    missing_subs = {cc for cc, s in subs.items() if s is None}
    df["infra_data_quality"] = np.where(df["country"].isin(missing_subs),
                                        "no_substation_data", "ok")

    bad = df[MODEL_COLS].isna().any(axis=1)
    excluded += [{"node_id": r.node_id, "country": r.country, "reason": "incomplete inputs"}
                 for r in df[bad].itertuples()]
    df = df[~bad]

    cols = ["node_id", "x", "y", "country", *MODEL_COLS, "grid_access_score",
            "fiber_connectivity_score", "infra_data_quality", "dist_to_hv_substation_km",
            "ixp_count_50km", "dist_to_nearest_ixp_km", "price_zone"]
    out = df[cols].reset_index(drop=True)
    assert out["node_id"].is_unique and len(out) > 0

    tmp = GRID_PATH.with_name(GRID_PATH.name + ".tmp")
    out.to_parquet(tmp, index=False)
    _replace(tmp, GRID_PATH)
    _atomic_write_text(MIX_PATH, json.dumps(country_mix(owid)))
    _update_meta(built_ts=time.time(), n_nodes=len(out), excluded=excluded)
    log.info(f"grid_nodes.parquet rebuilt: {len(out)} nodes, {len(excluded)} excluded")
    return True


def _update_meta(**kw) -> None:
    with _state_lock:
        state = _read_state()
        state["_build"] = {**state.get("_build", {}), **kw}
        LIVE.mkdir(parents=True, exist_ok=True)
        _atomic_write_text(STATE_PATH, json.dumps(state, indent=1))


def status() -> dict:
    """Provenance for /api/sources: one entry per source, with sub-keys rolled up."""
    state = _read_state()
    build_meta = state.pop("_build", {})
    sources = []
    for key, (what, provider, url, terms) in SOURCES.items():
        entries = {k: v for k, v in state.items() if k == key or k.startswith(key + "/")}
        parts = [{"key": k.split("/", 1)[1], **v} for k, v in entries.items() if "/" in k]
        head = entries.get(key, {})
        stamps = [e.get("fetched_ts") for e in ([head] if head else parts) if e.get("fetched_ts")]
        states = [e.get("status") for e in ([head] if head else parts)]
        item = {
            "key": key, "what": what, "provider": provider, "url": url, "terms": terms,
            "ttl_hours": TTL[key] / HOUR,
            "fetched_at": min(stamps) if stamps else None,
            "status": ("failed" if "failed" in states else "stale" if "stale" in states
                       else "fresh" if states else "pending"),
        }
        if head.get("error"):
            item["error"] = head["error"]
        if key == "price":
            for p in parts:
                p["license"] = "CC BY 4.0" if p["key"] in EC_CC_BY else "private and internal use only"
        if parts:
            item["parts"] = sorted(parts, key=lambda p: p["key"])
        sources.append(item)
    return {"built_at": build_meta.get("built_ts"), "building": build_meta.get("building", False),
            "n_nodes": build_meta.get("n_nodes"), "excluded": build_meta.get("excluded", []),
            "sources": sources}


def load_mix() -> dict:
    try:
        return json.loads(MIX_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return {}


def start_background(interval_s: float = HOUR) -> None:
    """Rebuild on a timer; each pass only refetches sources whose TTL expired."""
    def loop():
        while True:
            try:
                build()
            except Exception:
                log.exception("ingest pass failed; previous table stays in service")
            time.sleep(interval_s)
    threading.Thread(target=loop, name="ingest", daemon=True).start()


# =============================================================================
# Self-check (offline)
# =============================================================================
def selfcheck() -> None:
    doc = {"id": ["a", "b"], "size": [2, 3],
           "dimension": {"a": {"category": {"index": {"x": 0, "y": 1}}},
                         "b": {"category": {"index": ["p", "q", "r"]}}},
           "value": {"0": 1, "5": 6}}
    f = jsonstat_frame(doc)
    assert f.to_dict("records") == [{"a": "x", "b": "p", "value": 1.0},
                                    {"a": "y", "b": "r", "value": 6.0}], f

    assert _max_voltage("220000;65000;20000") == 220000 and _max_voltage("medium") is None

    land = pd.DataFrame({"geo": ["DE11"] * 12 + ["EL30"], "agriprod": ["ARA"] * 12 + ["ARA"],
                         "year": list(range(2010, 2022)) + [2020],
                         "value": [0.0, 0.0] + [10.0] * 10 + [5.0]})
    s = land_by_nuts2(land)
    assert s["DE11"] == 10.0, s  # only the last 10 years count
    nodes = pd.DataFrame({"node_id": ["DE111", "EL301", "EL999", "FI1B1"],
                          "country": ["DE", "GR", "GR", "FI"],
                          "x": [9.0, 23.7, 22.0, 25.0], "y": [48.7, 38.0, 39.0, 60.2]})
    p = assign_land(nodes, s)
    assert list(p) == [10.0, 5.0, 5.0, 10.0], list(p)  # direct, direct, country avg, nearest

    stats = pd.DataFrame({"electricity_generation": [8.76], "electricity_demand": [8.76]},
                         index=["XX"])
    g = grid_stats(stats, pd.Series({"XX": 2}))
    assert abs(g.at["XX", "capacity_mw"] - 1e6 / 0.35 / 2 / 1000) < 1e-6
    assert abs(g.at["XX", "congestion_frac"] - 0.2) < 1e-12

    nodes = pd.DataFrame({"x": [4.9, 10.0, 25.0], "y": [52.4, 50.0, 65.0]})
    subs = pd.DataFrame({"lon": [4.9, 10.1], "lat": [52.4, 50.0]})
    ixps = pd.DataFrame({"lon": [4.9, 4.95, 10.0], "lat": [52.4, 52.35, 50.0]})
    c = connectivity(nodes, subs, ixps)
    assert c["connectivity_score"].between(0, 1).all()
    assert c["connectivity_score"].idxmin() == 0 and c["connectivity_score"].idxmax() == 2
    assert list(c["ixp_count_50km"]) == [2, 1, 0]
    print("ingest selfcheck: ok")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="[%(name)s] %(message)s")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--force", action="store_true", help="ignore TTLs")
    ap.add_argument("--selfcheck", action="store_true", help="run offline asserts and exit")
    args = ap.parse_args()
    if args.selfcheck:
        selfcheck()
    else:
        build(force=args.force)
