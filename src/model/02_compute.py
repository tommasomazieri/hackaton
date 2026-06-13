"""
COMPUTE SCORES — Stage 2
========================
Transforms raw grid-node metrics into four comparable risk/cost scores:

  congestion_alpha   float  P(hourly consumption > node capacity | DC load added)
  dc_carbon_tco2_yr  float  Tonnes CO₂/yr emitted by the DC at this node
  total_cost_eur     float  Annualised OpEx (energy) + CapEx/CoE (land) in €/yr
  connectivity_score float  Passed through unchanged (already [0-1], lower=better)

It ALSO keeps every intermediate / raw column it touches (consumption mean & std,
prices, carbon intensity, capacity) plus the two cost sub-components
(energy_cost_eur, land_cost_eur) so the map popup can show a full breakdown.
Nothing is dropped — downstream ranking slices SCORE_COLS itself.
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import norm

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
sys.path.insert(0, os.path.join(_PROJECT_ROOT, "src", "data_normalization"))
from _utils import setup_logger  # noqa: E402

log = setup_logger("02_compute")

HOURS_IN_YEAR: int = 8_760
COST_OF_EQUITY: float = 0.08

# Score columns used by the ranking stage (exactly 4). Everything else this
# stage produces or passes through is detail for the popup — nothing is dropped.
SCORE_COLS = [
    "congestion_alpha",
    "dc_carbon_tco2_yr",
    "total_cost_eur",
    "connectivity_score",
]


def run(
    df: pd.DataFrame,
    dc_capacity_mw: float,
    dc_surface_m2: float,
) -> pd.DataFrame:
    """
    Args:
        df              scores_df from 01_load_filter.run(), indexed by node_id.
        dc_capacity_mw  DC power demand in MW.
        dc_surface_m2   DC footprint in m² (converted to ha internally).

    Returns:
        DataFrame indexed by node_id with exactly SCORE_COLS columns.
    """
    df = df.copy()
    dc_surface_ha = dc_surface_m2 / 10_000.0

    # -------------------------------------------------------------------------
    # 1. Congestion alpha
    #    Model node consumption as N(mean, std²). Shift mean up by DC demand.
    #    alpha = P(X > capacity_mw) under the shifted distribution.
    # -------------------------------------------------------------------------
    if all(c in df.columns for c in ["consumption_mean_mw", "consumption_std_mw", "capacity_mw"]):
        shifted_mean = df["consumption_mean_mw"] + dc_capacity_mw
        # clip std to tiny epsilon so z-score never explodes on zero-variance nodes
        std = df["consumption_std_mw"].clip(lower=1e-6)
        z = (df["capacity_mw"] - shifted_mean) / std
        # norm.cdf operates element-wise on a numpy array — fully vectorised
        df["congestion_alpha"] = 1.0 - norm.cdf(z.to_numpy())
        log.info(
            f"congestion_alpha: mean={df['congestion_alpha'].mean():.3f}, "
            f"max={df['congestion_alpha'].max():.3f}"
        )
    else:
        log.warning("congestion columns missing — congestion_alpha set to NaN")
        df["congestion_alpha"] = np.nan

    # -------------------------------------------------------------------------
    # 2. DC carbon footprint
    #    dc_capacity_mw [MW] × 8760 h = MWh/yr × 1000 kWh/MWh × gCO₂/kWh ÷ 1e6 = tCO₂/yr
    #    Simplifies to: dc_capacity_mw × HOURS × carbon_intensity / 1000
    # -------------------------------------------------------------------------
    if "carbon_intensity_elec" in df.columns:
        df["dc_carbon_tco2_yr"] = (
            dc_capacity_mw * HOURS_IN_YEAR * df["carbon_intensity_elec"] / 1_000.0
        )
        log.info(
            f"dc_carbon_tco2_yr: mean={df['dc_carbon_tco2_yr'].mean():.0f} tCO₂/yr"
        )
    else:
        log.warning("carbon_intensity_elec missing — dc_carbon_tco2_yr set to NaN")
        df["dc_carbon_tco2_yr"] = np.nan

    # -------------------------------------------------------------------------
    # 3. Cost voice  (single composite annual cost)
    #    Energy: OpEx    = energy_price [€/MWh] × capacity [MW] × hours [h/yr]
    #    Land:   CapEx/CoE = land_price [€/ha] × surface [ha] ÷ cost_of_equity
    # -------------------------------------------------------------------------
    if "energy_price_eur_mwh" in df.columns:
        df["energy_cost_eur"] = df["energy_price_eur_mwh"] * dc_capacity_mw * HOURS_IN_YEAR
    else:
        log.warning("energy_price_eur_mwh missing — energy cost contribution is NaN")
        df["energy_cost_eur"] = np.nan

    if "land_price_eur_ha" in df.columns:
        df["land_cost_eur"] = df["land_price_eur_ha"] * dc_surface_ha / COST_OF_EQUITY
    else:
        log.warning("land_price_eur_ha missing — land cost contribution is NaN")
        df["land_cost_eur"] = np.nan

    df["total_cost_eur"] = df["energy_cost_eur"] + df["land_cost_eur"]
    log.info(f"total_cost_eur: mean={df['total_cost_eur'].mean():.0f} €/yr")

    # -------------------------------------------------------------------------
    # 4. Keep every column (raw inputs + both cost sub-components stay for the
    #    popup breakdown). Cast integer-valued €/tonne columns for clean display.
    # -------------------------------------------------------------------------
    for col in ("dc_carbon_tco2_yr", "total_cost_eur", "energy_cost_eur", "land_cost_eur"):
        if col in df.columns:
            df[col] = df[col].round().astype("Int32")

    log.info(
        f"Output: {len(df)} nodes, columns={list(df.columns)}"
    )
    return df
