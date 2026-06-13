"""
CAPACITY — Total Installed Generation Capacity at Node (MW)
============================================================
Theory
------
Total installed generation capacity at a node (MW) quantifies how much power
the local grid zone can generate. It is the sum of all generators' nominal
capacity (p_nom) connected to that PyPSA bus, including conventional thermal,
renewables, and storage discharge capacity.

This metric answers: "how self-sufficient is this node?" A node with high local
generation capacity is more resilient to transmission constraints — it can
serve a new large load (like a DC) from local generation even when import lines
are congested. It also signals existing grid infrastructure: high-capacity nodes
already have large substations, transformers, and protection systems sized for
multi-hundred MW operation.

For a DC operator:
  - High capacity node → likely near large power plants or major renewable farms
    → lower energy delivery risk, potentially lower PPA negotiation cost
  - Low capacity node → depends on imports → congestion and headroom risk apply

Relationship to other metrics:
  - capacity_mw + congestion_frac together define the "grid quality" quadrant
  - High capacity + low congestion = best grid connectivity
  - Low capacity + high congestion = avoid

Source: PyPSA `n.generators.p_nom` and `n.storage_units.p_nom`, grouped by bus.

MVP Implementation
------------------
capacity_mw(n) = sum of p_nom of all generators and storage units at bus n:

    capacity_mw(n) = Σ_{g ∈ generators, g.bus == n} p_nom(g)
                   + Σ_{s ∈ storage_units, s.bus == n} p_nom(s)

p_nom is the installed (nameplate) capacity in MW from the PyPSA network object.
Buses with no attached generation: capacity_mw = 0.

Limitation: p_nom is installed capacity, not available capacity or firm capacity.
Renewable generators (wind, solar) have high p_nom but low capacity factor (~25%).
A 500 MW wind farm contributes 500 MW to this metric but only ~125 MW on average.
For DC siting, firm dispatchable capacity is more relevant. This is addressed in
the future implementation.

Future Implementation
---------------------
Step 1 — Firm capacity disaggregated by fuel type.
Rather than summing all p_nom (which conflates 500 MW nuclear with 500 MW wind),
compute fuel-type-aware firm capacity:

    firm_capacity_mw(n)     = Σ_{g: dispatchable} p_nom(g)         # gas, nuclear, hydro
    variable_capacity_mw(n) = Σ_{g: variable}     p_nom(g) × CF_g  # wind×0.25, solar×0.13

where CF_g = n.generators_t.p[g].mean() / p_nom(g) — actual annual capacity
factor from the solved dispatch. New columns: firm_capacity_mw,
variable_capacity_mw, renewable_fraction.
For DC siting: firm_capacity_mw drives dispatchable backup signal;
renewable_fraction drives PPA opportunity and Scope 2 carbon quality.

Step 2 — Time-resolved P10 generation (conservative firm capacity proxy).

    p10_annual_mw(n) = quantile(n.generators_t.p.T.groupby(bus).sum().T, 0.10)

P10 = generation available for 90 % of all hours — a robust floor for
continuous 24/7 load like a data center. New column: p10_generation_mw.

Step 3 — ENTSO-E installed capacity cross-validation.
Compare PyPSA p_nom per bus against ENTSO-E Installed Generation Capacity per
Production Type (14.1.A) at bidding-zone granularity. Flags nodes where PyPSA
significantly understates or overstates actual capacity (common in network
simplification). Freshness: annual. New diagnostic column: entso_capacity_mw.

Step 4 — Storage capacity signal.
    storage_capacity_mwh(n) = Σ_{s ∈ storage_units(n)} p_nom(s) × max_hours(s)
High storage → node can absorb surplus renewables and support DC battery
arbitrage strategy. New column: storage_capacity_mwh.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from _utils import setup_logger, get_paths, get_pypsa_network, ensure_dirs

log = setup_logger("06_capacity")


def run():
    paths = get_paths()
    ensure_dirs()

    log.info("Loading PyPSA network…")
    n = get_pypsa_network()

    log.info(f"Network: {len(n.buses)} buses, {len(n.generators)} generators, "
             f"{len(n.storage_units)} storage units")

    # Generator capacity per bus
    gen_cap = (
        n.generators.groupby("bus")["p_nom"].sum()
        if len(n.generators) > 0
        else pd.Series(dtype=float)
    )

    # Storage unit capacity per bus
    stor_cap = (
        n.storage_units.groupby("bus")["p_nom"].sum()
        if len(n.storage_units) > 0
        else pd.Series(dtype=float)
    )

    # Total capacity per bus — fill missing with 0
    total_cap = gen_cap.add(stor_cap, fill_value=0).reindex(
        n.buses.index, fill_value=0.0
    )

    result = pd.DataFrame({
        "node_id": total_cap.index,
        "capacity_mw": total_cap.values,
    })

    n_zero = (result["capacity_mw"] == 0).sum()
    if n_zero > 0:
        log.warning(f"{n_zero} buses have zero installed capacity (no generators attached)")

    log.info(
        f"capacity_mw — mean: {result['capacity_mw'].mean():.1f} MW, "
        f"median: {result['capacity_mw'].median():.1f} MW, "
        f"max: {result['capacity_mw'].max():.1f} MW"
    )

    out_path = os.path.join(paths["data_raw"], "capacity.parquet")
    result.to_parquet(out_path, index=False)
    log.info(f"Saved → {out_path}  ({len(result)} rows)")


if __name__ == "__main__":
    run()
