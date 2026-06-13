"""
IMAGERY — on-the-go Sentinel-2 + DEM fetch from Microsoft Planetary Computer.
=============================================================================
Free, no-auth STAC access to:
  - sentinel-2-l2a  : 9 bands (B2..B12) -> Dynamic World input
  - cop-dem-glo-30  : Copernicus DEM, for slope

Per node we build a ~10 km AOI, fetch a low-cloud median composite on a 10 m UTM
grid, and return numpy arrays aligned by a single affine transform. The whole
heavy stack (pystac-client, planetary-computer, odc-stac, rioxarray, rasterio)
is imported lazily.

NOTE on scale: DW's log normalization expects Sentinel-2 surface-reflectance on
the 0-10000 DN scale (as on Earth Engine / Planetary Computer), so band DNs are
passed through unscaled. Post-2022 baselines carry a -1000 BOA offset that we
re-add here to keep older and newer scenes comparable.
"""
from __future__ import annotations

import numpy as np

from src.model.site_analysis.dw_model import S2_BANDS

STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
S2_COLLECTION = "sentinel-2-l2a"
DEM_COLLECTION = "cop-dem-glo-30"
RES_M = 10.0
BOA_OFFSET = 1000  # re-add the post-baseline-4.0 BOA_ADD_OFFSET (-1000) to align scenes


def aoi_bbox(lat: float, lon: float, size_km: float = 10.0) -> tuple:
    """Square AOI around (lat, lon). Returns (min_lon, min_lat, max_lon, max_lat)."""
    half = size_km / 2.0
    dlat = half / 111.32
    dlon = half / (111.32 * max(0.05, np.cos(np.radians(lat))))
    return (lon - dlon, lat - dlat, lon + dlon, lat + dlat)


def utm_epsg_for(lon: float, lat: float) -> int:
    zone = int((lon + 180) // 6) + 1
    return (32600 if lat >= 0 else 32700) + zone


def _search_s2(bbox, max_cloud, date_range):
    import planetary_computer as pc
    from pystac_client import Client

    cat = Client.open(STAC_URL, modifier=pc.sign_inplace)
    search = cat.search(
        collections=[S2_COLLECTION],
        bbox=bbox,
        datetime=date_range,
        query={"eo:cloud_cover": {"lt": max_cloud}},
    )
    return list(search.items())


def fetch_composite(
    bbox: tuple,
    date_range: str = "2023-05-01/2023-09-30",
    max_cloud: int = 20,
) -> dict:
    """Median Sentinel-2 composite + slope on a shared 10 m UTM grid.

    Returns dict:
        bands      (H, W, 9) float32 reflectance DN, band order = S2_BANDS
        slope_deg  (H, W) float32 terrain slope in degrees
        transform  affine.Affine (col,row)->UTM metres
        crs_epsg   int (UTM zone EPSG)
        bbox       echoed lon/lat bbox
    """
    import odc.stac

    epsg = utm_epsg_for((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)

    items = _search_s2(bbox, max_cloud, date_range)
    if not items:
        items = _search_s2(bbox, 60, date_range)
    if not items:
        raise RuntimeError(f"No Sentinel-2 scenes for bbox={bbox} cloud<60%")

    ds = odc.stac.load(
        items, bands=S2_BANDS, bbox=bbox, crs=f"EPSG:{epsg}",
        resolution=RES_M, chunks={}, groupby="solar_day",
    )
    med = ds.median(dim="time", skipna=True)
    band_stack = np.stack(
        [med[b].values.astype(np.float32) + BOA_OFFSET for b in S2_BANDS], axis=-1
    )
    band_stack = np.clip(band_stack, 0, None)

    transform = med.odc.geobox.affine
    slope = _fetch_slope(bbox, epsg, med.odc.geobox)

    return {
        "bands": band_stack,
        "slope_deg": slope,
        "transform": transform,
        "crs_epsg": epsg,
        "bbox": bbox,
    }


def _fetch_slope(bbox, epsg, geobox) -> np.ndarray:
    """Copernicus DEM -> slope in degrees, resampled onto the S2 geobox."""
    import odc.stac
    import planetary_computer as pc
    from pystac_client import Client

    cat = Client.open(STAC_URL, modifier=pc.sign_inplace)
    items = list(cat.search(collections=[DEM_COLLECTION], bbox=bbox).items())
    if not items:
        return np.zeros(geobox.shape, dtype=np.float32)

    dem = odc.stac.load(items, bbox=bbox, like=geobox, chunks={})
    var = "data" if "data" in dem else list(dem.data_vars)[0]
    elev = dem[var]
    if "time" in elev.dims:
        elev = elev.isel(time=0)
    z = elev.values.astype(np.float32)

    dzdy, dzdx = np.gradient(z, RES_M, RES_M)
    return np.degrees(np.arctan(np.hypot(dzdx, dzdy))).astype(np.float32)


def pix_to_lonlat_fn(transform, crs_epsg: int):
    """Build a (col,row)->(lon,lat) callable from an affine transform + UTM EPSG."""
    from pyproj import Transformer

    to_wgs = Transformer.from_crs(crs_epsg, 4326, always_xy=True).transform

    def _f(col: float, row: float) -> tuple:
        x, y = transform * (col + 0.5, row + 0.5)  # pixel center
        lon, lat = to_wgs(x, y)
        return float(lon), float(lat)

    return _f


def utm_transform_for(transform, crs_epsg: int):
    """Return (transform, crs_epsg) — protected-area rasterization happens in UTM."""
    return transform, crs_epsg
