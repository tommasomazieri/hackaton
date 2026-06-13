"""
OSM — grid, road and landuse layers for site scoring.
=====================================================
- Electricity grid: parsed from the project's cached
  data/osm_power_infrastructure.json (power lines, cables, substations). Way
  geometries are rebuilt from member-node refs (the dump has no inline geometry).
- Major roads + landuse: fetched live from the OSM Overpass API per AOI bbox and
  disk-cached, since the project ships no road/landuse dump.

Only core deps: shapely, pyproj, requests.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from functools import lru_cache

from shapely.geometry import LineString, Point, Polygon, shape  # noqa: F401
from shapely.ops import transform as shapely_transform

_HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
OSM_POWER_JSON = os.path.join(DATA_DIR, "osm_power_infrastructure.json")
CACHE_DIR = os.path.join(DATA_DIR, "site_analysis", "osm_cache")

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
GRID_POWER_VALUES = {"line", "cable", "minor_line", "substation"}
MAJOR_HIGHWAYS = ("motorway", "trunk", "primary")
# OSM landuse tag -> built-refinement code consumed by scoring.land_score_raster
LANDUSE_CODE = {"industrial": 1, "commercial": 2, "residential": 3, "retail": 2}


# ---------------------------------------------------------------------------
# Projection helper
# ---------------------------------------------------------------------------
def utm_epsg_for(lon: float, lat: float) -> int:
    zone = int((lon + 180) // 6) + 1
    return (32600 if lat >= 0 else 32700) + zone


def _to_utm_transformer(epsg: int):
    from pyproj import Transformer
    return Transformer.from_crs(4326, epsg, always_xy=True).transform


def nearest_distance_km(lon: float, lat: float, geoms: list, utm_epsg: int | None = None) -> float:
    """Min distance (km) from a lon/lat point to any geometry, computed in UTM."""
    if not geoms:
        return float("inf")
    epsg = utm_epsg or utm_epsg_for(lon, lat)
    tf = _to_utm_transformer(epsg)
    pt = shapely_transform(tf, Point(lon, lat))
    best = min(shapely_transform(tf, g).distance(pt) for g in geoms)
    return best / 1000.0


def project_geoms(geoms: list, utm_epsg: int) -> list:
    """Reproject lon/lat geoms to a UTM EPSG once (amortized over many patches)."""
    tf = _to_utm_transformer(utm_epsg)
    return [shapely_transform(tf, g) for g in geoms]


def min_distance_km_utm(utm_point, utm_geoms: list) -> float:
    """Min distance (km) from an already-UTM point to already-UTM geoms."""
    if not utm_geoms:
        return float("inf")
    return min(g.distance(utm_point) for g in utm_geoms) / 1000.0


# ---------------------------------------------------------------------------
# Grid layer from the cached power dump
# ---------------------------------------------------------------------------
def _node_lookup(elements: list) -> dict:
    return {e["id"]: (e["lon"], e["lat"]) for e in elements if e["type"] == "node"
            and "lon" in e and "lat" in e}


@lru_cache(maxsize=4)
def power_features(path: str | None = None) -> list:
    """Shapely geoms (lon/lat) for grid lines, cables and substations.

    Cached: the dump is large and identical across nodes, so load + parse once."""
    p = path or OSM_POWER_JSON
    with open(p, encoding="utf-8") as fh:
        elements = json.load(fh)["elements"]

    nodes = _node_lookup(elements)
    geoms = []
    for e in elements:
        power = e.get("tags", {}).get("power")
        if power not in GRID_POWER_VALUES:
            continue
        if e["type"] == "node":
            geoms.append(Point(e["lon"], e["lat"]))
        elif e["type"] == "way":
            coords = [nodes[n] for n in e.get("nodes", []) if n in nodes]
            if len(coords) < 2:
                continue
            closed = power == "substation" and coords[0] == coords[-1] and len(coords) >= 4
            geoms.append(Polygon(coords) if closed else LineString(coords))
    return geoms


# ---------------------------------------------------------------------------
# Live Overpass: roads + landuse, disk-cached per bbox
# ---------------------------------------------------------------------------
def _cache_path(kind: str, bbox: tuple) -> str:
    key = hashlib.md5(f"{kind}:{bbox}".encode()).hexdigest()[:16]
    return os.path.join(CACHE_DIR, f"{kind}_{key}.json")


# Overpass mirrors rejecting header-less requests return 406; a real User-Agent
# fixes it. Keep a couple of mirrors for resilience.
OVERPASS_MIRRORS = (
    OVERPASS_URL,
    "https://overpass.kumi.systems/api/interpreter",
)
_OVERPASS_HEADERS = {"User-Agent": "dc-hounds-siting/1.0 (hackathon; contact: ops@dchounds.example)"}


def _overpass(query: str, kind: str, bbox: tuple, max_age_s: int = 7 * 86400) -> dict:
    os.makedirs(CACHE_DIR, exist_ok=True)
    cp = _cache_path(kind, bbox)
    if os.path.exists(cp) and (time.time() - os.path.getmtime(cp)) < max_age_s:
        with open(cp, encoding="utf-8") as fh:
            return json.load(fh)
    import requests
    last = None
    for url in OVERPASS_MIRRORS:
        try:
            resp = requests.post(url, data={"data": query}, headers=_OVERPASS_HEADERS, timeout=180)
            resp.raise_for_status()
            payload = resp.json()
            break
        except Exception as exc:  # try the next mirror
            last = exc
    else:
        raise last
    with open(cp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh)
    return payload


def _bbox_str(bbox: tuple) -> str:
    # bbox = (min_lon, min_lat, max_lon, max_lat) -> Overpass wants S,W,N,E
    min_lon, min_lat, max_lon, max_lat = bbox
    return f"{min_lat},{min_lon},{max_lat},{max_lon}"


def roads(bbox: tuple) -> list:
    """Major-road LineStrings (motorway/trunk/primary) within bbox, via Overpass."""
    regex = "|".join(MAJOR_HIGHWAYS)
    q = (
        f"[out:json][timeout:120];"
        f'way["highway"~"^({regex})$"]({_bbox_str(bbox)});'
        f"out geom;"
    )
    data = _overpass(q, "roads", bbox)
    out = []
    for e in data.get("elements", []):
        geom = e.get("geometry")
        if geom and len(geom) >= 2:
            out.append(LineString([(g["lon"], g["lat"]) for g in geom]))
    return out


def landuse_polygons(bbox: tuple) -> list:
    """List of (Polygon, built_code) for industrial/commercial/residential landuse."""
    keys = "|".join(LANDUSE_CODE.keys())
    q = (
        f"[out:json][timeout:120];"
        f'(way["landuse"~"^({keys})$"]({_bbox_str(bbox)});'
        f'relation["landuse"~"^({keys})$"]({_bbox_str(bbox)}););'
        f"out geom;"
    )
    data = _overpass(q, "landuse", bbox)
    out = []
    for e in data.get("elements", []):
        geom = e.get("geometry")
        lu = e.get("tags", {}).get("landuse")
        code = LANDUSE_CODE.get(lu)
        if geom and code and len(geom) >= 3:
            ring = [(g["lon"], g["lat"]) for g in geom if "lon" in g]
            if len(ring) >= 3:
                out.append((Polygon(ring), code))
    return out
