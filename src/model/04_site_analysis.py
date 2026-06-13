"""
SITE ANALYSIS — Stage 4 (post-Pareto followup)
===============================================
Runs on the top-N ranked nodes from 03_rank. For each node:

  1. Build a ~10 km AOI around (lat, lon).
  2. Fetch a Sentinel-2 median composite + Copernicus DEM slope (Planetary Computer).
  3. Classify land cover with the pretrained Google Dynamic World CNN.
  4. Refine the DW `built` class into industrial/commercial/residential via OSM landuse.
  5. Score land + grid distance + road distance + slope + patch area per the client spec.
  6. Exclude patches inside EEA Natura 2000 / CDDA protected areas.
  7. Pick the best patch and return its bounding box + largest inscribed circle
     (where + how big a DC pad fits).

Outputs:
  data/site_analysis/<node_id>.json     per-node result + score breakdown
  graphify-out/site_analysis.geojson    bbox + inscribed circle per node (map overlay)

CLI:
  python src/model/04_site_analysis.py --nodes DE254,FR123
  python src/model/04_site_analysis.py --top 5
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src", "data_normalization"))

from _utils import setup_logger  # noqa: E402
from src.model.site_analysis import (  # noqa: E402
    constraints, dw_model, geometry, imagery, osm, scoring,
)

log = setup_logger("04_site_analysis")

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
GRID_PARQUET = os.path.join(DATA_DIR, "grid_nodes.parquet")
OUT_DIR = os.path.join(DATA_DIR, "site_analysis")
GEOJSON_OUT = os.path.join(PROJECT_ROOT, "graphify-out", "site_analysis.geojson")

# Cap how many candidate patches we fully score per node (largest-first).
MAX_PATCHES_SCORED = 8
DEFAULT_AOI_KM = 10.0

# Projected power-grid geoms per UTM EPSG — same grid reused across nodes in a zone.
_GRID_UTM_CACHE: dict[int, list] = {}


def _grid_utm_for(epsg: int) -> list:
    if epsg not in _GRID_UTM_CACHE:
        _GRID_UTM_CACHE[epsg] = osm.project_geoms(osm.power_features(), epsg)
    return _GRID_UTM_CACHE[epsg]


# ---------------------------------------------------------------------------
# Node lat/lon lookup
# ---------------------------------------------------------------------------
def load_node_coords(node_ids: list[str] | None = None) -> pd.DataFrame:
    """Return DataFrame indexed by node_id with x (lon), y (lat), country."""
    df = pd.read_parquet(GRID_PARQUET, columns=None)
    cols = {c.lower(): c for c in df.columns}
    x, y = cols.get("x"), cols.get("y")
    if x is None or y is None:
        raise RuntimeError("grid_nodes.parquet lacks x/y columns")

    keep = [x, y] + ([cols["country"]] if "country" in cols else [])
    out = df[keep].copy()
    out.columns = ["x", "y"] + (["country"] if "country" in cols else [])
    # node_id is a column (string ids like 'DE254'); the parquet index is positional.
    out.index = df[cols["node_id"]] if "node_id" in cols else df.index
    out.index.name = "node_id"

    if node_ids:
        missing = [n for n in node_ids if n not in out.index]
        if missing:
            raise KeyError(f"node_ids not found: {missing}")
        out = out.loc[node_ids]
    return out


def _rasterize_landuse(landuse, transform, crs_epsg, shape):
    """Rasterize OSM landuse (Polygon, code) lon/lat pairs onto the UTM AOI grid."""
    if not landuse:
        return None
    from rasterio.features import rasterize
    polys, codes = zip(*landuse)
    utm_polys = osm.project_geoms(list(polys), crs_epsg)
    return rasterize(
        ((g, c) for g, c in zip(utm_polys, codes)),
        out_shape=shape, transform=transform, fill=0, all_touched=True, dtype="int16",
    )


# ---------------------------------------------------------------------------
# Per-node analysis
# ---------------------------------------------------------------------------
def analyze_node(
    node_id: str, lat: float, lon: float,
    size_km: float = DEFAULT_AOI_KM,
    date_range: str = "2023-05-01/2023-09-30",
    render_image: bool = True,
) -> dict:
    log.info(f"[{node_id}] AOI {size_km} km @ ({lat:.4f},{lon:.4f})")
    bbox = imagery.aoi_bbox(lat, lon, size_km)

    comp = imagery.fetch_composite(bbox, date_range=date_range)
    bands, slope_deg = comp["bands"], comp["slope_deg"]
    transform, epsg = comp["transform"], comp["crs_epsg"]
    H, W = bands.shape[:2]
    log.info(f"[{node_id}] composite {H}x{W} px, UTM EPSG:{epsg}")

    class_raster = dw_model.predict(bands)

    landuse = osm.landuse_polygons(bbox)
    built_lu = _rasterize_landuse(landuse, transform, epsg, (H, W))
    land = scoring.land_score_raster(class_raster, built_lu)

    protected = constraints.load_protected(bbox)
    excluded = constraints.exclusion_mask(
        osm.project_geoms(protected, epsg) if protected else [], transform, (H, W)
    )

    pix_to_lonlat = imagery.pix_to_lonlat_fn(transform, epsg)
    patches = geometry.extract_patches(land, excluded, pix_to_lonlat, min_area_ha=1.0)
    if not patches:
        return {"node_id": node_id, "lat": lat, "lon": lon,
                "status": "no_buildable_land", "patches_found": 0}

    # Pre-project grid + road geoms to UTM once. The grid is global + identical
    # across nodes, so cache its projection per UTM zone (reused by same-zone nodes).
    grid_utm = _grid_utm_for(epsg)
    road_utm = osm.project_geoms(osm.roads(bbox), epsg)

    from shapely.geometry import Point
    best = None
    for p in patches[:MAX_PATCHES_SCORED]:
        cx, cy = transform * (p.center_rc[1] + 0.5, p.center_rc[0] + 0.5)
        center_utm = Point(cx, cy)
        grid_km = osm.min_distance_km_utm(center_utm, grid_utm)
        road_km = osm.min_distance_km_utm(center_utm, road_utm)
        slope_at = float(slope_deg[p.center_rc])
        comps = scoring.score_components(p.mean_land_score, grid_km, road_km, slope_at, p.area_ha)
        cand = {
            "patch": p, "grid_dist_km": round(grid_km, 3), "road_dist_km": round(road_km, 3),
            "slope_deg": round(slope_at, 2), **comps,
        }
        if best is None or cand["final_score"] > best["final_score"]:
            best = cand

    p = best["patch"]
    dominant_cls = scoring.DW_CLASSES[int(np.bincount(
        class_raster[geometry.buildable_mask(land, excluded)].ravel(), minlength=scoring.N_CLASSES
    ).argmax())]
    buildable_ha = round(float(geometry.buildable_mask(land, excluded).sum()) * geometry.PIXEL_AREA_HA, 2)

    res = {
        "node_id": node_id, "lat": lat, "lon": lon, "status": "ok",
        "patches_found": len(patches),
        "buildable_area_ha": buildable_ha,
        "dominant_buildable_class": dominant_cls,
        "chosen_patch": {
            "area_ha": p.area_ha,
            "bbox_lonlat": list(p.bbox_lonlat),
            "inscribed_circle": {
                "center_lonlat": list(p.center_lonlat),
                "radius_m": p.radius_m,
            },
        },
        "scores": {
            "land_score": best["land_score"], "grid_score": best["grid_score"],
            "road_score": best["road_score"], "slope_score": best["slope_score"],
            "area_score": best["area_score"], "final_score": best["final_score"],
        },
        "inputs": {
            "grid_dist_km": best["grid_dist_km"], "road_dist_km": best["road_dist_km"],
            "slope_deg": best["slope_deg"], "aoi_km": size_km,
        },
    }

    # Render the "where to build" picture: true-colour S2 + chosen-patch overlay.
    if render_image:
        try:
            os.makedirs(OUT_DIR, exist_ok=True)
            png_path = os.path.join(OUT_DIR, f"{node_id}.png")
            render_site_png(bands, transform, epsg, res, png_path)
            res["image"] = f"{node_id}.png"
        except Exception as exc:  # imaging is best-effort, never sink the result
            log.warning(f"[{node_id}] image render failed: {exc}")

    return res


# ---------------------------------------------------------------------------
# Site image — true-colour Sentinel-2 composite with the chosen patch overlaid
# ---------------------------------------------------------------------------
def _lonlat_to_rc(lon: float, lat: float, transform, epsg: int) -> tuple[float, float]:
    """(lon, lat) -> (col, row) pixel coords on the UTM AOI grid."""
    from pyproj import Transformer
    to_utm = Transformer.from_crs(4326, epsg, always_xy=True).transform
    x, y = to_utm(lon, lat)
    col, row = ~transform * (x, y)
    return col, row


def render_site_png(bands, transform, epsg: int, result: dict, out_path: str) -> None:
    """Save an RGB PNG of the AOI (B4/B3/B2) with the chosen patch bbox + inscribed
    circle drawn on top. Pixel resolution is RES_M (10 m), so radius_m / RES_M
    gives the circle radius in pixels."""
    from PIL import Image, ImageDraw

    rgb = bands[..., [2, 1, 0]].astype("float32")  # B4 (R), B3 (G), B2 (B)
    lo = float(np.percentile(rgb, 2))
    hi = float(np.percentile(rgb, 98))
    if hi <= lo:
        hi = lo + 1.0
    arr = np.clip((rgb - lo) / (hi - lo), 0.0, 1.0)
    img = Image.fromarray((arr * 255).astype("uint8"), mode="RGB")

    cp = result.get("chosen_patch")
    if cp:
        draw = ImageDraw.Draw(img)
        min_lon, min_lat, max_lon, max_lat = cp["bbox_lonlat"]
        c0, r0 = _lonlat_to_rc(min_lon, max_lat, transform, epsg)  # top-left pixel
        c1, r1 = _lonlat_to_rc(max_lon, min_lat, transform, epsg)  # bottom-right pixel
        draw.rectangle([min(c0, c1), min(r0, r1), max(c0, c1), max(r0, r1)],
                       outline=(245, 158, 11), width=3)
        circ = cp["inscribed_circle"]
        clon, clat = circ["center_lonlat"]
        cc, cr = _lonlat_to_rc(clon, clat, transform, epsg)
        rad_px = float(circ["radius_m"]) / imagery.RES_M
        draw.ellipse([cc - rad_px, cr - rad_px, cc + rad_px, cr + rad_px],
                     outline=(251, 191, 36), width=3)

    img.thumbnail((640, 640))  # keep PNGs light so the report/print stays fast
    img.save(out_path)


# ---------------------------------------------------------------------------
# GeoJSON assembly
# ---------------------------------------------------------------------------
def _features_for(result: dict) -> list[dict]:
    if result.get("status") != "ok":
        return []
    cp = result["chosen_patch"]
    min_lon, min_lat, max_lon, max_lat = cp["bbox_lonlat"]
    bbox_ring = [[min_lon, min_lat], [max_lon, min_lat], [max_lon, max_lat],
                 [min_lon, max_lat], [min_lon, min_lat]]
    circle = cp["inscribed_circle"]
    ring = geometry.circle_polygon_lonlat(tuple(circle["center_lonlat"]), circle["radius_m"])
    props = {"node_id": result["node_id"], **result["scores"],
             "buildable_area_ha": result["buildable_area_ha"],
             "dominant_buildable_class": result["dominant_buildable_class"]}
    return [
        {"type": "Feature", "properties": {**props, "kind": "bbox"},
         "geometry": {"type": "Polygon", "coordinates": [bbox_ring]}},
        {"type": "Feature", "properties": {**props, "kind": "inscribed_circle",
                                           "radius_m": circle["radius_m"]},
         "geometry": {"type": "Polygon", "coordinates": [ring]}},
    ]


def run(node_ids: list[str], size_km: float = DEFAULT_AOI_KM,
        date_range: str = "2023-05-01/2023-09-30", write: bool = True,
        cache: bool = True, render_image: bool = True) -> list[dict]:
    """Analyse `node_ids`. With `cache=True`, nodes that already have a cached
    `<id>.json` are loaded from disk instead of re-running the CNN — so the heavy
    stage runs at most once per node. Coordinates are only read on a cache miss."""
    os.makedirs(OUT_DIR, exist_ok=True)

    results, features = [], []
    coords = None  # lazily loaded only when a node actually needs computing
    for node_id in node_ids:
        json_path = os.path.join(OUT_DIR, f"{node_id}.json")
        if cache and os.path.exists(json_path):
            with open(json_path, encoding="utf-8") as fh:
                res = json.load(fh)
            if res.get("image") and not os.path.exists(os.path.join(OUT_DIR, res["image"])):
                res.pop("image", None)  # cached json but image was cleaned up
        else:
            if coords is None:
                coords = load_node_coords(node_ids)
            row = coords.loc[node_id]
            try:
                res = analyze_node(node_id, float(row["y"]), float(row["x"]),
                                   size_km=size_km, date_range=date_range,
                                   render_image=render_image)
            except Exception as exc:  # one bad node must not sink the batch
                log.error(f"[{node_id}] failed: {exc}")
                res = {"node_id": node_id, "status": "error", "error": str(exc)}
            if write and res.get("status") in ("ok", "no_buildable_land"):
                with open(json_path, "w", encoding="utf-8") as fh:
                    json.dump(res, fh, indent=2)
        results.append(res)
        features.extend(_features_for(res))

    if write:
        os.makedirs(os.path.dirname(GEOJSON_OUT), exist_ok=True)
        with open(GEOJSON_OUT, "w", encoding="utf-8") as fh:
            json.dump({"type": "FeatureCollection", "features": features}, fh, indent=2)
        log.info(f"Wrote {GEOJSON_OUT} ({len(features)} features)")
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _resolve_top(n: int) -> list[str]:
    """Top-N node_ids from the in-memory rank results, if a pipeline run is cached."""
    from src.model import rank
    pareto = rank._RESULTS.get("pareto")
    if pareto is None:
        raise SystemExit("--top requires a cached pipeline run; pass --nodes instead "
                         "or call via the API after POST /run.")
    return list(rank.rank_by_weights({}, top_n=n))


def main() -> None:
    ap = argparse.ArgumentParser(description="Post-Pareto DW site analysis")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--nodes", help="comma-separated node_ids")
    g.add_argument("--top", type=int, help="top-N from cached ranking")
    ap.add_argument("--aoi-km", type=float, default=DEFAULT_AOI_KM)
    ap.add_argument("--dates", default="2023-05-01/2023-09-30")
    args = ap.parse_args()

    node_ids = args.nodes.split(",") if args.nodes else _resolve_top(args.top)
    results = run(node_ids, size_km=args.aoi_km, date_range=args.dates)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
