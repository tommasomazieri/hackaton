"""
GEOMETRY — extract buildable patches and the placement footprint.
=================================================================
From a per-pixel land-score raster, find contiguous buildable patches, and for
each compute:
  - area in hectares,
  - bounding box,
  - the largest inscribed circle (where + how big a DC pad fits) via the
    Euclidean distance transform.

Pure numpy + scipy.ndimage (both already core deps). Pixel <-> world coordinate
conversion is injected as a callable so this module needs no rasterio/pyproj.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np
from scipy import ndimage

PIXEL_SIZE_M = 10.0          # Sentinel-2 / Dynamic World native resolution
PIXEL_AREA_HA = (PIXEL_SIZE_M ** 2) / 1e4   # 100 m^2 -> 0.01 ha

# A pixel is buildable if its land score clears this floor (land==0 classes excluded).
BUILDABLE_MIN_LAND = 1e-6

# (col, row) in array space -> (lon, lat). Identity default keeps the module testable.
PixToLonLat = Callable[[float, float], tuple[float, float]]


def _identity_pix_to_lonlat(col: float, row: float) -> tuple[float, float]:
    return float(col), float(row)


@dataclass
class Patch:
    label: int
    area_ha: float
    pixel_count: int
    mean_land_score: float
    # inscribed circle (placement footprint)
    center_rc: tuple[int, int]          # (row, col) in array space
    center_lonlat: tuple[float, float]
    radius_m: float
    # bounding box in array space (min_row, min_col, max_row, max_col), inclusive
    bbox_rc: tuple[int, int, int, int]
    bbox_lonlat: tuple[float, float, float, float] = field(default=(0, 0, 0, 0))  # (min_lon,min_lat,max_lon,max_lat)


def buildable_mask(
    land_score: np.ndarray,
    excluded: np.ndarray | None = None,
) -> np.ndarray:
    """Boolean mask of pixels eligible to build on.

    Args:
        land_score  (H, W) per-pixel land score.
        excluded    optional (H, W) bool mask of environmentally excluded pixels
                    (Natura 2000 / CDDA). Excluded pixels are never buildable.
    """
    mask = np.asarray(land_score) > BUILDABLE_MIN_LAND
    if excluded is not None:
        mask = mask & ~np.asarray(excluded, dtype=bool)
    return mask


def _inscribed_circle(patch_mask: np.ndarray) -> tuple[tuple[int, int], float]:
    """Center (row, col) and radius in metres of the largest circle inside the patch."""
    dt = ndimage.distance_transform_edt(patch_mask)  # distance in pixels to edge
    flat = int(np.argmax(dt))
    row, col = np.unravel_index(flat, dt.shape)
    radius_m = float(dt[row, col]) * PIXEL_SIZE_M
    return (int(row), int(col)), radius_m


def extract_patches(
    land_score: np.ndarray,
    excluded: np.ndarray | None = None,
    pix_to_lonlat: PixToLonLat | None = None,
    min_area_ha: float = 1.0,
) -> list[Patch]:
    """Find buildable patches and characterise each.

    Args:
        land_score     (H, W) per-pixel land score raster.
        excluded       optional (H, W) bool environmental-exclusion mask.
        pix_to_lonlat  (col,row)->(lon,lat). Defaults to identity (array space).
        min_area_ha    drop patches smaller than this (noise speckle).

    Returns:
        list of Patch, largest-area first.
    """
    to_lonlat = pix_to_lonlat or _identity_pix_to_lonlat
    score = np.asarray(land_score, dtype=np.float32)
    mask = buildable_mask(score, excluded)

    # 8-connectivity so diagonally touching buildable pixels form one patch.
    structure = np.ones((3, 3), dtype=int)
    labels, n = ndimage.label(mask, structure=structure)
    if n == 0:
        return []

    patches: list[Patch] = []
    for lab in range(1, n + 1):
        pm = labels == lab
        count = int(pm.sum())
        area_ha = count * PIXEL_AREA_HA
        if area_ha < min_area_ha:
            continue

        rows, cols = np.where(pm)
        min_r, max_r = int(rows.min()), int(rows.max())
        min_c, max_c = int(cols.min()), int(cols.max())

        (cr, cc), radius_m = _inscribed_circle(pm)
        center_lonlat = to_lonlat(cc, cr)

        lon0, lat0 = to_lonlat(min_c, min_r)
        lon1, lat1 = to_lonlat(max_c, max_r)
        bbox_lonlat = (min(lon0, lon1), min(lat0, lat1), max(lon0, lon1), max(lat0, lat1))

        patches.append(Patch(
            label=lab,
            area_ha=round(area_ha, 3),
            pixel_count=count,
            mean_land_score=round(float(score[pm].mean()), 4),
            center_rc=(cr, cc),
            center_lonlat=(round(center_lonlat[0], 6), round(center_lonlat[1], 6)),
            radius_m=round(radius_m, 1),
            bbox_rc=(min_r, min_c, max_r, max_c),
            bbox_lonlat=tuple(round(v, 6) for v in bbox_lonlat),
        ))

    patches.sort(key=lambda p: p.area_ha, reverse=True)
    return patches


def circle_polygon_lonlat(
    center_lonlat: tuple[float, float], radius_m: float, n: int = 48,
) -> list[list[float]]:
    """Approximate the inscribed circle as a lon/lat polygon ring (for GeoJSON).

    Uses a local equirectangular metres-per-degree approximation — fine at the
    few-km scale of a single DC footprint.
    """
    lon, lat = center_lonlat
    m_per_deg_lat = 111_320.0
    m_per_deg_lon = max(1.0, 111_320.0 * np.cos(np.radians(lat)))
    ring = []
    for k in range(n + 1):
        theta = 2 * np.pi * k / n
        dlon = (radius_m * np.cos(theta)) / m_per_deg_lon
        dlat = (radius_m * np.sin(theta)) / m_per_deg_lat
        ring.append([round(lon + dlon, 6), round(lat + dlat, 6)])
    return ring
