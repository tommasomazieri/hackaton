"""Shared utilities for the data_normalization pipeline."""
import os
import logging
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Country code lookup — ISO 3166-1 alpha-3 (OWID) → alpha-2 (PyPSA / NUTS)
# Covers EU27 + Norway
# ---------------------------------------------------------------------------
ISO3_TO_ISO2 = {
    "AUT": "AT", "BEL": "BE", "BGR": "BG", "HRV": "HR",
    "CYP": "CY", "CZE": "CZ", "DNK": "DK", "EST": "EE",
    "FIN": "FI", "FRA": "FR", "DEU": "DE", "GRC": "GR",
    "HUN": "HU", "IRL": "IE", "ITA": "IT", "LVA": "LV",
    "LTU": "LT", "LUX": "LU", "MLT": "MT", "NLD": "NL",
    "POL": "PL", "PRT": "PT", "ROU": "RO", "SVK": "SK",
    "SVN": "SI", "ESP": "ES", "SWE": "SE", "NOR": "NO",
}

EU_COUNTRIES_ISO3 = set(ISO3_TO_ISO2.keys())
EU_COUNTRIES_ISO2 = set(ISO3_TO_ISO2.values())

# Countries with known sparse OSM telecom tagging — flag for downstream QA
OSM_SPARSE_COUNTRIES = {"EE", "LV", "LT", "BG", "RO", "HR", "SI", "SK", "HU"}


def minmax_norm(series: pd.Series) -> pd.Series:
    """Min-max normalize a Series to [0, 1]. NaN values are propagated."""
    mn = series.min()
    mx = series.max()
    if mx == mn:
        return pd.Series(np.zeros(len(series)), index=series.index)
    return (series - mn) / (mx - mn)


def get_paths() -> dict:
    """Return absolute paths for all project data resources."""
    here = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(here, "..", ".."))
    data_dir = os.path.join(project_root, "data")
    return {
        "project_root": project_root,
        "data": data_dir,
        "data_raw": os.path.join(data_dir, "raw"),
        "data_processed": os.path.join(data_dir, "processed"),
        "nuts3_geojson": os.path.join(data_dir, "nuts3_all_features.json"),
        "owid_csv": os.path.join(data_dir, "owid-energy-data.csv"),
        "osm_json": os.path.join(data_dir, "osm_power_infrastructure.json"),
        "regions_onshore": os.environ.get(
            "REGIONS_ONSHORE_PATH",
            os.path.join(project_root, "resources", "regions_onshore.geojson"),
        ),
    }


def ensure_dirs() -> None:
    """Create data/raw and data/processed directories if absent."""
    paths = get_paths()
    os.makedirs(paths["data_raw"], exist_ok=True)
    os.makedirs(paths["data_processed"], exist_ok=True)


def get_pypsa_network():
    """
    Load a PyPSA Network from PYPSA_NETWORK_PATH environment variable.

    Raises FileNotFoundError with full instructions if the path is not set
    or the file does not exist.
    """
    import pypsa  # imported here so scripts that don't need it don't hard-depend on it

    path = os.environ.get("PYPSA_NETWORK_PATH", "")
    if not path or not os.path.exists(path):
        raise FileNotFoundError(
            f"PyPSA network not found at '{path}'.\n\n"
            "To generate it:\n"
            "  1. Clone pypsa-eur:\n"
            "       git clone https://github.com/PyPSA/pypsa-eur\n"
            "  2. Set full substation resolution in config/config.default.yaml:\n"
            "       scenario:\n"
            "         clusters: [all]   # all EU substations, no clustering\n"
            "  3. Run Snakemake:\n"
            "       snakemake results/networks/base_s_all_elec_.nc --cores 8\n"
            "  4. Export the path:\n"
            "       export PYPSA_NETWORK_PATH=/path/to/base_s_all_elec_.nc\n\n"
            "Zenodo pre-built bundle (includes regions_onshore.geojson):\n"
            "  https://zenodo.org/records/13756400\n"
            "Then also set:\n"
            "  export REGIONS_ONSHORE_PATH=/path/to/resources/regions_onshore.geojson"
        )
    return pypsa.Network(path)


def get_regions_onshore():
    """
    Load the PyPSA Voronoi regions GeoDataFrame from REGIONS_ONSHORE_PATH.

    Schema: name (bus id), x (lon), y (lat), country (ISO alpha-2), geometry (Polygon).
    """
    import geopandas as gpd

    paths = get_paths()
    path = paths["regions_onshore"]
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"regions_onshore.geojson not found at '{path}'.\n\n"
            "Download the PyPSA-Eur Zenodo bundle:\n"
            "  https://zenodo.org/records/13756400\n"
            "Extract and set:\n"
            "  export REGIONS_ONSHORE_PATH=/path/to/resources/regions_onshore.geojson\n\n"
            "Or generate via Snakemake 'base_network' rule in pypsa-eur."
        )
    return gpd.read_file(path)


def setup_logger(name: str) -> logging.Logger:
    """Return a logger with format: [name][LEVEL] message."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(f"[{name}][%(levelname)s] %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
