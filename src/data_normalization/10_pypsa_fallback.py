"""
PYPSA FALLBACK — public data substitutes for PyPSA-dependent columns
=====================================================================
Populates the three PyPSA-dependent columns using publicly available data
when a solved PyPSA network is not available.

  capacity_mw          ← OWID electricity_generation (TWh) ÷ capacity_factor
  consumption_mean_mw  ← OWID electricity_demand (TWh) → mean MW per node
  consumption_std_mw   ← consumption_mean × 0.20 (typical EU load CV)
  congestion_frac      ← heuristic from demand/generation ratio
  energy_price_eur_mwh ← static 2023 ENTSO-E annual average wholesale prices

Writes directly to data/processed/ (clean values, no cleanup needed).

Run:
    python src/data_normalization/10_pypsa_fallback.py
Then:
    python src/data_normalization/09_build_table.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
from _utils import setup_logger, get_paths, ensure_dirs, ISO3_TO_ISO2

log = setup_logger("10_pypsa_fallback")

HOURS_IN_YEAR = 8_760
CAPACITY_FACTOR = 0.35   # EU generation-weighted average capacity factor
LOAD_CV = 0.20           # coefficient of variation for hourly EU national load

# 2023 annual average day-ahead wholesale electricity prices (€/MWh)
# Source: ENTSO-E Market Report 2023 / Ember European Wholesale Electricity Prices
PRICES_2023: dict[str, float] = {
    "AT": 96.8,  "BE": 97.3,  "BG": 101.2, "HR": 105.4, "CY": 180.0,
    "CZ": 95.1,  "DK": 88.4,  "EE": 89.0,  "FI": 57.6,  "FR": 98.6,
    "DE": 95.2,  "GR": 129.5, "HU": 96.2,  "IE": 103.7, "IT": 128.3,
    "LV": 88.5,  "LT": 88.2,  "LU": 97.3,  "MT": 180.0, "NL": 97.3,
    "PL": 95.4,  "PT": 99.7,  "RO": 98.5,  "SK": 95.3,  "SI": 105.2,
    "ES": 99.4,  "SE": 67.5,  "NO": 73.1,
}


def _owid_stats(owid_path: str) -> pd.DataFrame:
    """
    Load OWID energy CSV and return last non-NaN year per EU country with:
      iso2, electricity_demand_twh, electricity_generation_twh
    """
    cols = ["iso_code", "year", "electricity_demand", "electricity_generation"]
    df = pd.read_csv(owid_path, usecols=cols)

    # keep only EU+NO iso3 codes
    df = df[df["iso_code"].isin(ISO3_TO_ISO2.keys())].copy()
    df["iso2"] = df["iso_code"].map(ISO3_TO_ISO2)

    # last non-NaN year for each country (demand and generation)
    df = df.sort_values("year")
    result = (
        df.groupby("iso2")[["electricity_demand", "electricity_generation"]]
        .last()
        .dropna(how="all")
        .reset_index()
    )
    result.columns = ["country", "electricity_demand_twh", "electricity_generation_twh"]
    log.info(f"OWID stats loaded: {len(result)} countries")
    return result


def run():
    paths = get_paths()
    ensure_dirs()

    # -----------------------------------------------------------------------
    # Load node geometry (need x, y, country, and node count per country)
    # -----------------------------------------------------------------------
    geom_path = os.path.join(paths["data_processed"], "node_geometry.parquet")
    if not os.path.exists(geom_path):
        raise FileNotFoundError(
            f"node_geometry.parquet not found at '{geom_path}'.\n"
            "Run 07_node_geometry.py and 08_cleanup.py first."
        )
    nodes = pd.read_parquet(geom_path)
    n_nodes_per_country = nodes.groupby("country")["node_id"].count().rename("n_nodes")
    log.info(f"Nodes loaded: {len(nodes)} across {nodes['country'].nunique()} countries")

    # -----------------------------------------------------------------------
    # Load OWID stats
    # -----------------------------------------------------------------------
    owid_stats = _owid_stats(paths["owid_csv"])
    owid_stats = owid_stats.join(n_nodes_per_country, on="country")

    # -----------------------------------------------------------------------
    # Compute country-level metrics
    # -----------------------------------------------------------------------

    # capacity: installed generation = mean_generation / capacity_factor
    # mean_generation_mw = twh * 1e6 / hours
    owid_stats["cap_country_mw"] = (
        owid_stats["electricity_generation_twh"] * 1e6 / HOURS_IN_YEAR / CAPACITY_FACTOR
    )
    # consumption mean/std at country level
    owid_stats["cons_mean_country_mw"] = (
        owid_stats["electricity_demand_twh"] * 1e6 / HOURS_IN_YEAR
    )
    owid_stats["cons_std_country_mw"] = owid_stats["cons_mean_country_mw"] * LOAD_CV

    # congestion proxy: demand/generation ratio signals grid stress
    # demand > generation → net importer → higher stress
    ratio = (
        owid_stats["electricity_demand_twh"] / owid_stats["electricity_generation_twh"]
    ).fillna(1.0)
    owid_stats["congestion_country"] = (ratio * 0.5 - 0.3).clip(lower=0.0, upper=0.95)

    # per-node = country total / n_nodes (equal distribution within country)
    owid_stats["capacity_mw"] = owid_stats["cap_country_mw"] / owid_stats["n_nodes"]
    owid_stats["consumption_mean_mw"] = (
        owid_stats["cons_mean_country_mw"] / owid_stats["n_nodes"]
    )
    owid_stats["consumption_std_mw"] = (
        owid_stats["cons_std_country_mw"] / owid_stats["n_nodes"]
    )
    owid_stats["congestion_frac"] = owid_stats["congestion_country"]
    owid_stats["energy_price_eur_mwh"] = owid_stats["country"].map(PRICES_2023)

    log.info(
        "Country-level summary (sample):\n"
        + owid_stats[["country", "capacity_mw", "consumption_mean_mw",
                       "congestion_frac", "energy_price_eur_mwh"]].head(8).to_string(index=False)
    )

    # -----------------------------------------------------------------------
    # Expand to node level by joining on country
    # -----------------------------------------------------------------------
    node_df = nodes[["node_id", "country"]].merge(
        owid_stats[["country", "capacity_mw", "consumption_mean_mw",
                    "consumption_std_mw", "congestion_frac", "energy_price_eur_mwh"]],
        on="country",
        how="left",
    )

    n_nan = node_df[["capacity_mw", "consumption_mean_mw", "energy_price_eur_mwh"]].isna().any(axis=1).sum()
    if n_nan:
        log.warning(f"{n_nan} nodes have NaN after country join (missing OWID/price data)")

    # -----------------------------------------------------------------------
    # Write to data/processed/ (same schema as the PyPSA scripts)
    # -----------------------------------------------------------------------
    proc = paths["data_processed"]

    # capacity.parquet
    cap = node_df[["node_id", "capacity_mw"]].copy()
    cap.to_parquet(os.path.join(proc, "capacity.parquet"), index=False)
    log.info(f"capacity.parquet → {len(cap)} rows  (mean {cap['capacity_mw'].mean():.0f} MW/node)")

    # congestion.parquet
    cong = node_df[["node_id", "congestion_frac", "consumption_mean_mw", "consumption_std_mw"]].copy()
    cong.to_parquet(os.path.join(proc, "congestion.parquet"), index=False)
    log.info(
        f"congestion.parquet → {len(cong)} rows  "
        f"(mean congestion_frac={cong['congestion_frac'].mean():.3f})"
    )

    # energy_price.parquet — include lmp_* columns for schema compat with 09_build_table
    ep = node_df[["node_id", "energy_price_eur_mwh"]].copy()
    ep["lmp_p05"] = ep["energy_price_eur_mwh"]
    ep["lmp_p95"] = ep["energy_price_eur_mwh"]
    ep["lmp_spread_p95p5"] = 0.0
    ep.to_parquet(os.path.join(proc, "energy_price.parquet"), index=False)
    log.info(
        f"energy_price.parquet → {len(ep)} rows  "
        f"(mean {ep['energy_price_eur_mwh'].mean():.1f} €/MWh)"
    )

    # infrastructure_access.parquet — neutral fallback (0.5) when OSM data unavailable
    ia_path = os.path.join(proc, "infrastructure_access.parquet")
    if not os.path.exists(ia_path):
        ia = nodes[["node_id", "country"]].copy()
        ia["connectivity_score"] = 0.5
        ia["grid_access_score"] = 0.5
        ia["fiber_connectivity_score"] = 0.5
        ia["infra_data_quality"] = "fallback"
        ia.to_parquet(ia_path, index=False)
        log.info("infrastructure_access.parquet → neutral 0.5 fallback (run 04_infrastructure_access.py for real values)")

    log.info(
        "\nAll PyPSA-fallback parquets written.\n"
        "Next: python src/data_normalization/09_build_table.py"
    )


if __name__ == "__main__":
    run()
