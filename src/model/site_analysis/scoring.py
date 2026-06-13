"""
SCORING — Dynamic World classes -> data-center suitability scores.
===================================================================
Pure functions (numpy only, no heavy deps) so the whole score spec is unit
testable without TensorFlow / STAC / rasterio in the environment.

Implements the exact score system the client specified:

  land  (0.35) :  per-pixel from the DW land-cover class, with the single DW
                  `built` class refined into industrial / commercial / residential
                  via OSM landuse polygons.
  grid  (0.25) :  distance to nearest electricity grid feature (OSM power).
  road  (0.15) :  distance to nearest major road (OSM highway motorway/trunk/primary).
  slope (0.10) :  terrain slope in degrees, from a DEM.
  area  (0.15) :  size of the buildable patch in hectares (rewards big sites).

  final_score = 0.35*land + 0.25*grid + 0.15*road + 0.10*slope + 0.15*area
"""
from __future__ import annotations

import numpy as np

# ---------------------------------------------------------------------------
# Dynamic World output classes, in model index order (0..8).
# Source: google/dynamicworld single_image_runner.ipynb.
# ---------------------------------------------------------------------------
DW_CLASSES = [
    "water",              # 0
    "trees",              # 1
    "grass",              # 2
    "flooded_vegetation",  # 3
    "crops",              # 4
    "shrub_and_scrub",    # 5
    "built",              # 6
    "bare",               # 7
    "snow_and_ice",       # 8
]
N_CLASSES = len(DW_CLASSES)
BUILT_CLASS = 6  # the only class refined further via OSM landuse

# ---------------------------------------------------------------------------
# Per-class land score (client spec). The `built` entry is a placeholder of 0.0;
# real built pixels are overridden per-pixel from OSM landuse (see below).
#
# Assumptions flagged for the client (no exact row in the spec table):
#   - shrub_and_scrub -> 0.70 (treated like Grassland: low, clearable vegetation)
#   - built with no OSM landuse tag -> 0.0 (assume residential/mixed, exclude)
# Both are single-number knobs, trivial to retune.
# ---------------------------------------------------------------------------
LAND_SCORE_BY_CLASS = np.array([
    0.00,   # 0 water               -> Acqua
    0.00,   # 1 trees               -> Foresta
    0.70,   # 2 grass               -> Grassland
    0.00,   # 3 flooded_vegetation  -> Wetland
    0.75,   # 4 crops               -> Greenfield agricolo
    0.70,   # 5 shrub_and_scrub     -> (assumption) ~Grassland
    0.00,   # 6 built               -> placeholder, refined via OSM landuse
    0.95,   # 7 bare                -> Bare ground
    0.00,   # 8 snow_and_ice        -> Ghiaccio
], dtype=np.float32)

# OSM landuse tag on a `built` pixel -> client land score.
BUILT_LANDUSE_SCORE = {
    "industrial": 1.00,   # Industriale
    "commercial": 0.40,   # Commerciale
    "residential": 0.00,  # Residenziale
}
BUILT_DEFAULT_SCORE = 0.00  # built pixel with no landuse tag -> excluded


def land_score_raster(
    class_raster: np.ndarray,
    built_landuse_raster: np.ndarray | None = None,
) -> np.ndarray:
    """Map a DW class raster to a per-pixel land score in [0, 1].

    Args:
        class_raster          (H, W) int array of DW class indices 0..8.
        built_landuse_raster  optional (H, W) int array, only meaningful where
                              class_raster == BUILT_CLASS. Encodes OSM landuse:
                                0 = none/untagged, 1 = industrial,
                                2 = commercial,   3 = residential.
                              If None, every built pixel gets BUILT_DEFAULT_SCORE.

    Returns:
        (H, W) float32 land-score raster.
    """
    cls = np.asarray(class_raster)
    out = LAND_SCORE_BY_CLASS[cls].astype(np.float32)

    built = cls == BUILT_CLASS
    if not built.any():
        return out

    if built_landuse_raster is None:
        out[built] = BUILT_DEFAULT_SCORE
        return out

    lu = np.asarray(built_landuse_raster)
    code_to_score = {
        0: BUILT_DEFAULT_SCORE,
        1: BUILT_LANDUSE_SCORE["industrial"],
        2: BUILT_LANDUSE_SCORE["commercial"],
        3: BUILT_LANDUSE_SCORE["residential"],
    }
    for code, score in code_to_score.items():
        out[built & (lu == code)] = score
    return out


# ---------------------------------------------------------------------------
# Distance / slope / area component scores (client spec, with >range fallbacks).
# ---------------------------------------------------------------------------
def grid_score(dist_km: float) -> float:
    """Electricity grid proximity. Spec: <1->1.0, 1-3->0.8, 3-5->0.5. >5 extrapolated 0.2."""
    if dist_km < 1:
        return 1.0
    if dist_km < 3:
        return 0.8
    if dist_km < 5:
        return 0.5
    return 0.2


def road_score(dist_km: float) -> float:
    """Major-road proximity. Spec: <1->1.0, 1-5->0.8, 5-10->0.5. >10 extrapolated 0.2."""
    if dist_km < 1:
        return 1.0
    if dist_km < 5:
        return 0.8
    if dist_km < 10:
        return 0.5
    return 0.2


def slope_score(slope_deg: float) -> float:
    """Terrain slope. Spec: <3->1.0, 3-5->0.9, 5-10->0.6, 10-15->0.2, >15->0."""
    if slope_deg < 3:
        return 1.0
    if slope_deg < 5:
        return 0.9
    if slope_deg < 10:
        return 0.6
    if slope_deg < 15:
        return 0.2
    return 0.0


# Area score: piecewise-linear through the client anchor points, capped at 1.2.
_AREA_ANCHORS_HA = np.array([0.0, 20.0, 50.0, 100.0, 200.0])
_AREA_ANCHORS_SCORE = np.array([0.0, 0.40, 0.70, 1.00, 1.20])


def area_score(patch_area_ha: float) -> float:
    """Reward large buildable patches. Anchors: 20ha=0.4, 50=0.7, 100=1.0, 200=1.2 (cap)."""
    a = max(0.0, float(patch_area_ha))
    return float(np.interp(a, _AREA_ANCHORS_HA, _AREA_ANCHORS_SCORE))


# ---------------------------------------------------------------------------
# Final weighted score.
# ---------------------------------------------------------------------------
WEIGHTS = {"land": 0.35, "grid": 0.25, "road": 0.15, "slope": 0.10, "area": 0.15}


def final_score(land: float, grid: float, road: float, slope: float, area: float) -> float:
    """Weighted composite. Note: area can reach 1.2, so the max is slightly >1."""
    return (
        WEIGHTS["land"] * land
        + WEIGHTS["grid"] * grid
        + WEIGHTS["road"] * road
        + WEIGHTS["slope"] * slope
        + WEIGHTS["area"] * area
    )


def score_components(
    land: float, grid_dist_km: float, road_dist_km: float,
    slope_deg: float, patch_area_ha: float,
) -> dict[str, float]:
    """Build the full per-patch score breakdown (component scores + final)."""
    g = grid_score(grid_dist_km)
    r = road_score(road_dist_km)
    s = slope_score(slope_deg)
    a = area_score(patch_area_ha)
    return {
        "land_score": round(float(land), 4),
        "grid_score": g,
        "road_score": r,
        "slope_score": s,
        "area_score": round(a, 4),
        "final_score": round(final_score(land, g, r, s, a), 4),
    }
