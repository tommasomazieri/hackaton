"""Shared helpers: country codes, min-max normalisation, logger (used by src/ingest.py and src/model/)."""
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


def minmax_norm(series: pd.Series) -> pd.Series:
    """Min-max normalize a Series to [0, 1]. NaN values are propagated."""
    mn = series.min()
    mx = series.max()
    if mx == mn:
        return pd.Series(np.zeros(len(series)), index=series.index)
    return (series - mn) / (mx - mn)


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
