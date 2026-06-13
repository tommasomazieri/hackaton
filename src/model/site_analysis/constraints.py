"""
CONSTRAINTS — environmental exclusion zones (European Environment Agency).
=========================================================================
Patches intersecting a protected area score 0 and are excluded outright.

Data (download once into data/eea/, EPSG:4326 GeoPackages):
  - Natura 2000  : https://www.eea.europa.eu/data-and-maps/data/natura-14/natura-2000-spatial-data
  - CDDA (national parks / nature reserves / nationally designated areas):
      https://www.eea.europa.eu/data-and-maps/data/nationally-designated-areas-national-cdda-17/cdda

Filenames are auto-detected by glob (any *.gpkg under data/eea/). If none are
present, the layer degrades gracefully to "no exclusions" with a warning, so the
rest of the pipeline still runs.

geopandas / rasterio imported lazily (optional CNN-stack deps).
"""
from __future__ import annotations

import glob
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
EEA_DIR = os.path.join(PROJECT_ROOT, "data", "eea")


def _gpkg_files() -> list[str]:
    return sorted(glob.glob(os.path.join(EEA_DIR, "*.gpkg")))


def load_protected(bbox: tuple) -> list:
    """Protected-area shapely geoms (lon/lat) intersecting bbox.

    bbox = (min_lon, min_lat, max_lon, max_lat). Returns [] if no EEA data present.
    """
    files = _gpkg_files()
    if not files:
        return []
    import geopandas as gpd
    from shapely.geometry import box

    aoi = box(*bbox)
    geoms = []
    for f in files:
        try:
            gdf = gpd.read_file(f, bbox=bbox)
        except Exception:
            gdf = gpd.read_file(f)
        if gdf.empty:
            continue
        if gdf.crs and gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(4326)
        for g in gdf.geometry:
            if g is not None and g.is_valid and g.intersects(aoi):
                geoms.append(g)
    return geoms


def is_excluded(geom, protected: list) -> bool:
    """True if `geom` (lon/lat shapely) intersects any protected area."""
    return any(geom.intersects(p) for p in protected)


def exclusion_mask(protected: list, transform, shape: tuple):
    """Rasterize protected areas onto the AOI grid -> bool (H, W) exclusion mask.

    Args:
        protected  shapely geoms in the SAME CRS as `transform`.
        transform  affine.Affine mapping (col,row)->CRS coords of the AOI raster.
        shape      (H, W).
    """
    import numpy as np
    if not protected:
        return np.zeros(shape, dtype=bool)
    from rasterio.features import rasterize

    burned = rasterize(
        ((g, 1) for g in protected),
        out_shape=shape,
        transform=transform,
        fill=0,
        all_touched=True,
        dtype="uint8",
    )
    return burned.astype(bool)
