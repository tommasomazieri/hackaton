"""
ENERGY PRICE — Locational Marginal Price (LMP)
===============================================
Theory
------
Energy price is the largest single OpEx driver for a data center, accounting for
50–70 % of total operating cost over a 15-year asset life. At 50 MW load and
8,760 operating hours per year, a 10 €/MWh price difference equals ≈ €4.4 M/year
in electricity costs — the dominant variable across siting candidates.

The Locational Marginal Price (LMP) at a transmission bus is the shadow price of
the nodal power balance constraint in the Optimal Power Flow (OPF) solution. It
decomposes into three components:

    LMP_n = λ_gen + λ_loss(n) + λ_congestion(n)

  1. λ_gen:         system-wide marginal generation cost (€/MWh)
  2. λ_loss(n):     incremental I²R losses at node n (can be positive or negative)
  3. λ_congestion(n): premium/discount caused by binding transmission constraints

LMP is therefore the most precise available signal for wholesale electricity cost
at a specific grid location — it captures both fuel/carbon market conditions and
physical grid constraints (congestion rents, line losses).

MVP Implementation
------------------
Annual mean LMP from the PyPSA OPF simulation, computed as:

    energy_price_eur_mwh(n) = mean(marginal_price(n, t), t = 1 … 8760)

Source: PyPSA `n.buses_t.marginal_price` (shape: 8760 × n_buses).

Annual averaging over 8,760 hourly snapshots is a stable proxy. It smooths
short-term price spikes (e.g., gas-price events, calm-wind periods) while
preserving the structural cross-node differentials driven by persistent congestion
and regional fuel-mix differences — the signals that matter for long-horizon
siting decisions.

Diagnostic columns also exported (lmp_p05, lmp_p95, lmp_spread_p95p5) for use in
battery storage sizing and congestion analysis in downstream modules.

Limitation: The simulation year reflects a historical weather/demand year, not
current forward market prices. ETS carbon price trajectory and fuel price shocks
after the simulation cutoff are not captured. Annual-average LMP from a PyPSA
simulation year can diverge from real day-ahead market averages by 10–20 %,
mainly driven by gas price assumptions.

Future Implementation
---------------------
Step 1 — ENTSO-E day-ahead market prices (real market, not simulation).
Library: entsoe-py. Query DocumentType.PRICE_DAY_AHEAD per bidding zone for
trailing 365 calendar days. Each zone returns 8,760 hourly prices in €/MWh.
Map bidding zones to PyPSA buses via spatial join (ENTSO-E bidding zone GeoJSON
available at transparency.entsoe.eu/api?documentType=A09).
Aggregates per bus: mean, P05, P50, P95, spread(P95−P05).
Freshness: 24 h TTL. Fallback: cached parquet if API unavailable.

Step 2 — Carbon credit cost adder (EU ETS).
Add carbon_cost_eur_mwh from 01_carbon_emissions (future impl) to the raw LMP:

    all_in_price_eur_mwh(n) = energy_price_eur_mwh(n) + carbon_cost_eur_mwh(n)

This is the true all-in electricity cost for a DC with no carbon coverage:
ETS-obligated generation cost + wholesale energy. At ETS €70/tCO₂ and
CI 350 gCO₂/kWh, adds ≈ €24.5/MWh to nominal LMP — material for low-LMP nodes.
New column: all_in_price_eur_mwh. Use this as primary cost signal in 02_compute.

Step 3 — PPA discount signal.
Fraction of hours with LMP ≤ 0 at each node = renewable curtailment fraction.
High curtailment → generator desperate for revenue → PPA discount negotiable.

    ppa_discount_proxy(n) = P(LMP_n ≤ 0)

New column: ppa_discount_proxy [0–1]. Higher = better PPA opportunity.

Step 4 — Battery arbitrage value.

    arbitrage_eur_mwh(n) = lmp_p95(n) − lmp_p05(n)

Proxy for revenue available to a co-located BESS doing peak-shaving / trading.
DCs with on-site storage can reduce effective energy cost by buying at P05 hours
and avoiding P95 hours. New column: arbitrage_eur_mwh.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from _utils import setup_logger, get_paths, get_pypsa_network, ensure_dirs

log = setup_logger("02_energy")


def run():
    paths = get_paths()
    ensure_dirs()

    log.info("Loading PyPSA network...")
    n = get_pypsa_network()

    if n.buses_t.marginal_price.empty:
        raise ValueError(
            "n.buses_t.marginal_price is empty — the network was not solved with OPF.\n"
            "Re-run the Snakemake workflow with optimization enabled.\n"
            "Check that 'solving' is not skipped in your snakemake config."
        )

    n_buses = len(n.buses)
    n_snapshots = len(n.snapshots)
    log.info(f"Network: {n_buses} buses, {n_snapshots} snapshots")

    mp = n.buses_t.marginal_price  # DataFrame: (snapshots × buses)

    energy_price = mp.mean(axis=0).rename("energy_price_eur_mwh")
    lmp_p05 = mp.quantile(0.05).rename("lmp_p05")
    lmp_p95 = mp.quantile(0.95).rename("lmp_p95")
    lmp_spread = (lmp_p95 - lmp_p05).rename("lmp_spread_p95p5")

    result = pd.concat([energy_price, lmp_p05, lmp_p95, lmp_spread], axis=1)
    result.index.name = "node_id"
    result = result.reset_index()

    # Join static metadata from n.buses
    bus_meta = (
        n.buses[["country", "x", "y"]]
        .copy()
        .rename_axis("node_id")
        .reset_index()
    )
    result = result.merge(bus_meta, on="node_id", how="left")

    n_missing_lmp = result["energy_price_eur_mwh"].isna().sum()
    if n_missing_lmp > 0:
        log.warning(f"{n_missing_lmp} buses have NaN marginal_price — check OPF coverage")

    log.info(
        f"LMP range: {result['energy_price_eur_mwh'].min():.1f} – "
        f"{result['energy_price_eur_mwh'].max():.1f} €/MWh"
    )
    log.info(f"EU mean LMP: {result['energy_price_eur_mwh'].mean():.1f} €/MWh")

    out_path = os.path.join(paths["data_raw"], "energy_price.parquet")
    result.to_parquet(out_path, index=False)
    log.info(f"Saved → {out_path}  ({len(result)} rows)")


if __name__ == "__main__":
    run()
