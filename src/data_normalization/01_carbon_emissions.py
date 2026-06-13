"""
CARBON INTENSITY
================
Theory
------
Carbon intensity (gCO₂/kWh) is the primary sustainability constraint for data
center siting. DC operators bound by the EU Taxonomy for Sustainable Finance,
internal Scope 2 commitments, or RE100/PPA targets must verify that the grid at
the chosen location meets their carbon budget. Grid carbon intensity is the
weighted average of emission factors across all generation technologies dispatched
in a given period, including cross-border imports:

    CI = Σ(E_i × EF_i) / Σ(E_i)

where E_i is generation from source i (MWh) and EF_i its lifecycle emission factor
(gCO₂/kWh): coal ≈ 950, gas ≈ 400, solar ≈ 30, nuclear ≈ 12, wind ≈ 15.

Why it matters for siting:
  - Hard constraint: if CI_node > operator's carbon_max, the site is ineligible
    regardless of cost or grid capacity.
  - OpEx driver: lower CI → lower Scope 2 emissions → lower EU ETS exposure and
    lower green bond financing costs (−50 to −150 bps for <100 gCO₂/kWh sites,
    EU Taxonomy aligned).

MVP Implementation
------------------
Assign the OWID/Ember national average carbon intensity to every PyPSA node in
that country. This is the direct spatial mapping approach (Approach 1 in
docs/data.md §6A):

    CI_node(n) = CI_national(country(n))

Source: OWID full energy dataset (owid-energy-data.csv), column
`carbon_intensity_elec`, last available year per ISO 3166-1 alpha-3 country code.

All nodes in the same country receive the same value. This is a valid first-order
approximation: at the national level, Ember/OWID is the most accurate and freely
available time series for EU27 + Norway.

Limitation: ignores within-country grid heterogeneity. North Germany (wind-surplus)
has substantially lower CI than south Germany (coal-dependent) — intra-national
variation of 20–30% documented in docs/data.md §6A. For national-level screening
(Filter 1 in the hierarchical approach) this is sufficient.

Future Implementation
---------------------
[Empty — to be filled in dedicated planning session]

Real implementation: PyPSA Carbon Flow Tracking (docs/data.md §3B.3). For each
bus n and simulation hour t, solve the linear system:

    CI_n(t) = [Σ G_g,n(t)·EF_g + Σ F_mn(t)·CI_m(t)] / [Σ G_g,n + Σ F_mn]

where F_mn(t) = max(0, P_mn(t)) is the import flow from neighbor m. This gives
true consumption-based Scope 2 carbon intensity at hourly nodal resolution,
accounting for cross-border electricity flows.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from _utils import setup_logger, get_paths, ISO3_TO_ISO2, EU_COUNTRIES_ISO3, ensure_dirs

log = setup_logger("01_carbon")


def run():
    paths = get_paths()
    ensure_dirs()

    owid_path = paths["owid_csv"]
    if not os.path.exists(owid_path):
        raise FileNotFoundError(
            f"OWID energy CSV not found at '{owid_path}'.\n"
            "Download from https://ourworldindata.org/energy and place at data/owid-energy-data.csv"
        )

    log.info("Loading OWID energy CSV...")
    df = pd.read_csv(
        owid_path,
        usecols=["country", "year", "iso_code", "carbon_intensity_elec"],
    )

    # Keep only EU27 + Norway; drop rows missing carbon data
    df = df[df["iso_code"].isin(EU_COUNTRIES_ISO3)].dropna(
        subset=["carbon_intensity_elec"]
    )

    # Last available year per country
    df = (
        df.sort_values("year")
        .groupby("iso_code", as_index=False)
        .last()[["iso_code", "year", "carbon_intensity_elec"]]
        .rename(columns={"iso_code": "iso3", "year": "source_year"})
    )

    df["country"] = df["iso3"].map(ISO3_TO_ISO2)

    missing = df[df["country"].isna()]
    if not missing.empty:
        log.warning(f"No alpha-2 mapping for: {missing['iso3'].tolist()}")
    df = df.dropna(subset=["country"])

    log.info(
        f"Carbon data for {len(df)} countries: {sorted(df['country'].tolist())}"
    )
    log.info(
        f"Range: {df['carbon_intensity_elec'].min():.1f} – "
        f"{df['carbon_intensity_elec'].max():.1f} gCO₂/kWh"
    )

    # Output is country-level. Per-node join (country → each bus) is done in
    # 08_cleanup.py once the full node list with country codes is available.
    out = df[["country", "carbon_intensity_elec", "source_year"]].reset_index(
        drop=True
    )

    out_path = os.path.join(paths["data_raw"], "carbon_emissions.parquet")
    out.to_parquet(out_path, index=False)
    log.info(f"Saved → {out_path}  ({len(out)} rows)")


if __name__ == "__main__":
    run()
