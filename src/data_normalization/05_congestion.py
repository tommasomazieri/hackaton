"""
CONGESTION — Grid Line Loading Fraction + Node Consumption Statistics
======================================================================
Theory
------
Grid congestion measures how often a node's adjacent transmission lines are
near-saturated. It is the primary proxy for **connection queue risk** — the
probability that connecting a new large load at this node will require structural
grid reinforcement and face a multi-year queue at the TSO.

The load rate (loading fraction) of a transmission line at time t is:

    LoadRate(l, t) = |P(l, t)| / S_nom(l)

where P(l, t) is the active power flow on line l (MW) and S_nom(l) is its thermal
capacity (MVA, approximately equal to MW for EU HV lines at unity power factor).

When LoadRate > 0.80 (80 % of thermal capacity), TSOs apply operational redispatch
and typically refuse new connection applications at adjacent nodes. This 80 %
threshold is the standard N-1 operational margin: the line must retain 20 %
headroom to absorb flow rerouting following the loss of a neighboring line.

Real-world connection queue evidence (docs/independent-variables.md §3c):
  - Netherlands: zero hosting capacity at multiple substations (Mar 2026)
  - Denmark: new HV connections paused (60 GW queued vs 7.3 GW peak, Mar 2026)
  - Germany: 270 GW in connection queue, 717 applications (Q3 2025)
  - Ireland: >100 MW requires 80 % new renewable generation on-site (EirGrid 2026)

A DC connecting to a node with congestion_frac > 0.25 (lines >80 % loaded for
>25 % of the year) faces a realistic 5–10 year connection queue.

Node consumption statistics (mean, median, quartiles of hourly consumption in MW)
characterise the load profile at the node. A node with high median consumption
is a load centre — it has existing grid infrastructure sized for large loads,
meaning a DC can co-locate without triggering disproportionate grid upgrades.
These stats also inform sizing: a DC at 50 MW in a node with median 10 MW
consumption is a dominant load and will attract TSO scrutiny; the same DC in a
500 MW median node is incremental.

Source: `n.loads_t.p_set` (time-varying load demand at each bus, MW).

MVP Implementation
------------------
congestion_frac(n) = fraction of 8,760 annual simulation hours during which
any adjacent line of bus n exceeds 80 % of its nominal thermal capacity:

    adj(n) = {l : bus0(l) == n OR bus1(l) == n}

    congestion_frac(n) = mean_t [ max_{l ∈ adj(n)} (LoadRate(l, t) > 0.80) ]

consumption stats(n) = mean and std of hourly sum of all loads attached to bus n:
    consumption_mean_mw, consumption_std_mw

Source: PyPSA `n.lines_t.p0`, `n.lines.s_nom`, `n.loads`, `n.loads_t.p_set`.

Buses with no adjacent AC lines: congestion_frac = NaN.
Buses with no attached loads: consumption stats = 0.

Future Implementation
---------------------
Step 1 — ENTSO-E observed redispatch volumes.
Query ENTSO-E Transparency Platform DocumentType.REDISPATCH (14.1.C) per TSO
zone for trailing 12 months. High redispatch volume = persistent structural
congestion validated by actual TSO operational data, independent of simulation.

    redispatch_intensity(n) = annual_redispatch_gwh(zone(n)) / zone_peak_load_gw(n)

New column: redispatch_intensity_gwh_per_gw. Cross-validates PyPSA congestion_frac
with real market evidence. Freshness: 30-day TTL.

Step 2 — GridSFM real-time congestion inference.
Use microsoft/gridsfm (HuggingFace) to predict line loadings at each bus in
milliseconds from network topology and load features — no full OPF solve needed.
Apply as a fast screening layer: run GridSFM for all nodes, flag suspected
congestion hotspots, then run full PyPSA lopf only for the top-50 candidates.
Reduces full OPF runtime from ~hours to ~minutes for candidate-set evaluation.

Step 3 — Connection queue proxy from TSO hosting capacity maps.
Several TSOs publish digital hosting capacity maps (NL: Netbeheer Nederland,
DE: various DSOs, IE: EirGrid). Scrape or API-fetch available capacity per
substation. Map to nearest PyPSA bus.
New column: tso_hosting_capacity_mw (NaN where not published).
Hard filter: if tso_hosting_capacity_mw < dc_capacity_mw and not NaN →
exclude node regardless of congestion_frac.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
from _utils import setup_logger, get_paths, get_pypsa_network, ensure_dirs

log = setup_logger("05_congestion")

CONGESTION_THRESHOLD = 0.80  # 80 % of thermal capacity


def run():
    paths = get_paths()
    ensure_dirs()

    log.info("Loading PyPSA network…")
    n = get_pypsa_network()

    if n.lines_t.p0.empty:
        raise ValueError(
            "n.lines_t.p0 is empty — power flow results not available.\n"
            "The network must be solved with OPF before running this script."
        )

    log.info(f"Network: {len(n.buses)} buses, {len(n.lines)} lines, "
             f"{len(n.snapshots)} snapshots")

    # Normalised loading: |P(t)| / S_nom  →  shape (snapshots, lines)
    loading = n.lines_t.p0.abs().div(n.lines.s_nom, axis=1)

    # Pre-build consumption series per bus (sum of loads at that bus, per snapshot)
    # n.loads has column 'bus'; n.loads_t.p_set columns = load indices
    log.info("Building per-bus consumption time series from n.loads_t.p_set…")
    bus_consumption: dict[str, pd.Series] = {}
    zero_series = pd.Series(0.0, index=n.snapshots)

    if not n.loads_t.p_set.empty:
        for bus in n.buses.index:
            bus_load_idx = n.loads[n.loads.bus == bus].index.intersection(
                n.loads_t.p_set.columns
            )
            if len(bus_load_idx) > 0:
                bus_consumption[bus] = n.loads_t.p_set[bus_load_idx].sum(axis=1)
            else:
                bus_consumption[bus] = zero_series
    else:
        # Static loads: use p_set from n.loads directly (scalar per load)
        for bus in n.buses.index:
            bus_loads = n.loads[n.loads.bus == bus]
            total = float(bus_loads["p_set"].sum()) if len(bus_loads) > 0 else 0.0
            bus_consumption[bus] = pd.Series(total, index=n.snapshots)

    records = []
    n_no_adj = 0

    for bus in n.buses.index:
        adj = n.lines[
            (n.lines.bus0 == bus) | (n.lines.bus1 == bus)
        ].index

        if len(adj) == 0:
            n_no_adj += 1
            cong_frac = float("nan")
        else:
            over_threshold = (loading[adj] > CONGESTION_THRESHOLD).any(axis=1)
            cong_frac = float(over_threshold.mean())

        cons = bus_consumption[bus]
        records.append({
            "node_id": bus,
            "congestion_frac": cong_frac,
            "consumption_mean_mw": float(cons.mean()),
            "consumption_std_mw": float(cons.std()),
        })

    if n_no_adj > 0:
        log.warning(
            f"{n_no_adj} buses have no adjacent AC lines → congestion_frac = NaN"
        )

    result = pd.DataFrame(records)

    valid_cong = result["congestion_frac"].dropna()
    log.info(
        f"congestion_frac — mean: {valid_cong.mean():.3f}, "
        f"max: {valid_cong.max():.3f}, "
        f"fraction >0.25: {(valid_cong > 0.25).mean():.2%}"
    )
    log.info(
        f"consumption_mean_mw — mean: {result['consumption_mean_mw'].mean():.1f} MW, "
        f"avg std: {result['consumption_std_mw'].mean():.1f} MW"
    )

    out_path = os.path.join(paths["data_raw"], "congestion.parquet")
    result.to_parquet(out_path, index=False)
    log.info(f"Saved → {out_path}  ({len(result)} rows)")


if __name__ == "__main__":
    run()
