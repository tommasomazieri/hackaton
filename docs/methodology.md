# Methodology: how each input is built

`src/ingest.py` builds `data/grid_nodes.parquet`, the table the model (`src/model/`) scores. Every source is fetched live, cached under `data/live/` with a TTL, and reused marked "stale" if a refresh fails. `GET /api/sources` shows what was fetched when, and under which terms.

## Current implementation

| Column | Source | Method | Refresh |
|---|---|---|---|
| `node_id, x, y, country` | Eurostat GISCO NUTS 2021 (20M) | Level-3 regions of EU27 + NO. Geographic centroid. `EL` is renamed `GR`. Regions off the continental grid are excluded: FRY, ES63, ES64, ES70, PT20, PT30, NO0B. | 365 d |
| `energy_price_eur_mwh` | Energy-Charts `/price` | Mean of hourly day-ahead prices over the trailing 365 days, per bidding zone. 15-min prices are averaged to hourly first. Each node gets its zone's price: DE and LU map to DE-LU; DK, IT, NO and SE are split by point-in-polygon against the entsoe-py zone shapes (nearest zone if a coastal centroid falls outside). | 24 h |
| `carbon_intensity_elec` | OWID energy dataset | National value for the last reported year (unchanged formula). | 7 d |
| `capacity_mw, consumption_mean_mw, consumption_std_mw, congestion_frac` | OWID energy dataset | Unchanged fallback formulas: `capacity = gen_TWh·1e6/8760/0.35/n_nodes`, `consumption_mean = demand_TWh·1e6/8760/n_nodes`, `std = 0.2·mean`, `congestion = clip(0.5·demand/gen − 0.3, 0, 0.95)`. | 7 d |
| `land_price_eur_ha` | Eurostat `apri_lprc` (unit EUR_HA) | Per NUTS2 and year, average the land types (ARA, ARAIB, ARAXIB, J0000), then take the mean of the last 10 years. Assign by `node_id[:4]`, falling back to the country average, then to the nearest node that has a value. | 30 d |
| `connectivity_score, grid_access_score, fiber_connectivity_score` | OSM via Overpass (HV substations); PeeringDB (IX facilities) | Unchanged formula, computed in EPSG:3035: `grid = minmax(dist_to_hv_substation_km)`, `fiber = 0.6·(1 − minmax(ixp_count_50km)) + 0.4·minmax(dist_to_nearest_ixp_km)`, `connectivity = 0.5·grid + 0.5·fiber` (lower = better). | 30 d / 7 d |
| `infra_data_quality` | derived | `no_substation_data` when a country's Overpass fetch has never succeeded, else `ok`. | per build |
| `dist_*`, `ixp_count_50km`, `price_zone` | derived | Diagnostics shown in the node detail view. | per build |

The model code is untouched.

### What changed from the hackathon build, and why

- **The data is live, where before it was hardcoded or constant.** Prices were a hardcoded 2023 table. Connectivity was a constant 0.5 for every node, because the EU-wide OSM fetch had never run.
- **Greece is included.** NUTS codes Greece `EL`, the country filter expected `GR`, and every Greek node was silently dropped.
- **Overseas regions are excluded.** They sit on separate grids and price zones.
- **Nodes with a missing model input are excluded**, not left as NaN. The ranking sums weighted normalised scores with `skipna`, so a NaN would count as 0, which is the *best* score. Excluded nodes and the reason for each are listed at `/api/sources`.
- **IX locations come from PeeringDB** (facilities hosting at least one internet exchange) rather than OSM `telecom=exchange`. This is the upgrade path the original script named in its "Future Implementation, Step 2a".
- **Substations must carry a voltage tag ≥110 kV.** The original also counted untagged substations as HV, and most of those are distribution-level.

### Known limits (not fixed here: algorithm scope)

- Congestion, capacity and consumption are national figures divided evenly across nodes. They are a proxy, not deliverable MW. See `docs/research/dc-siting-decision-process.md`: deliverable power by date is the factor the industry ranks first.
- Farmland price is a proxy for industrial land (see the land section below).
- Carbon intensity is national.
- **Price licensing.** Energy-Charts publishes 16 zones under CC BY 4.0 (AT, BE, CH, CZ, DE-LU, DE-AT-LU, DK1, DK2, FR, HU, IT-North, NL, NO2, PL, SE4, SI). The rest are "for private and internal use only". Any commercial use needs a licence from the exchanges (EPEX SPOT, Nord Pool).

## Background and roadmap

The sections below are the theory and "future implementation" notes from the original pipeline scripts (`src/data_normalization/0*.py`, removed in favour of `src/ingest.py`), kept verbatim. Where a section's "MVP Implementation" differs from the table above, the table is current.

### `07_node_geometry.py`

```text
NODE GEOMETRY — NUTS3 Centroids as Grid Node Proxies
=====================================================
Theory
------
The atomic spatial unit for scoring is a grid node — a point in geographic space
with associated electricity grid and land characteristics. Ideally these are PyPSA
bus locations (physical HV substations). Without a solved PyPSA network we use
NUTS3 administrative centroids as node proxies.

NUTS3 regions are the finest administrative division available EU-wide from
Eurostat. Each NUTS3 centroid approximates the centre of mass of its territory.
This is a coarser representation than individual substations but still provides
sub-national resolution sufficient for DC siting recommendations.

x, y centroid coordinates are the only required geometry: they drive the NUTS2
spatial join for land price assignment in 08_cleanup.py.

Source (primary): PyPSA `n.buses` — actual substation locations, one row per bus.
Source (fallback): Eurostat GISCO NUTS3 polygon centroids (this script).

MVP Implementation
------------------
1. If PYPSA_NETWORK_PATH is set: use n.buses[['x','y','country']] directly.
2. Else: fetch NUTS3 polygons from Eurostat GISCO API, compute centroids, filter
   to EU27+NO, export node_id=NUTS_ID, x=lon, y=lat, country=NUTS_ID[:2].

No polygon geometry stored — not needed for any downstream operation.

Future Implementation
---------------------
Step 1 — True substation geometry from PyPSA-Eur Voronoi catchments.
Source: PyPSA-Eur resources/regions_onshore.geojson — Voronoi polygons from the
solved full-resolution network, one polygon per bus, covering EU landmass with
no gaps or overlaps. This is the actual electrical service territory of each node.

Load and reproject to equal-area CRS for accurate area computation:
    regions    = gpd.read_file('resources/regions_onshore.geojson')
    regions_ea = regions.to_crs('EPSG:3035')        # ETRS89-LAEA equal-area
    area_km2   = regions_ea.geometry.area / 1e6
    centroid   = regions_ea.geometry.centroid       # then back-project to WGS84

New columns exported: node_id, x, y, country, area_km2, geometry (WKT polygon).
area_km2 propagates to 03_land_price.py (land market depth) and replaces the
circular radius approximation in dc_surface_ha estimation in 02_compute.py.

Step 2 — High-resolution Voronoi from ENTSO-E TYNDP substations.
Use ENTSO-E TYNDP substation coordinates (lat/lon per physical substation) as
Voronoi seed points instead of PyPSA bus approximations. Compute tessellation
via scipy.spatial.Voronoi, clip to national borders (Natural Earth polygons).
Yields ~3,000 nodes EU-wide vs PyPSA-Eur's ~500 simplified buses — much finer
spatial resolution for land-use, infrastructure, and area scoring.

Step 3 — Geometry source quality flag.
Tag each node with geometry_source:
    "pypsa_voronoi"  — best; from solved PyPSA-Eur network
    "entso_voronoi"  — high; from TYNDP substations + clipped Voronoi
    "nuts3_centroid" — fallback; current MVP, point only, no area
Downstream modules use geometry_source to propagate confidence level.
```

### `01_carbon_emissions.py`

```text
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
Step 1 — Hourly nodal carbon intensity via PyPSA carbon flow tracing.
For each bus n and simulation hour t, distribute carbon causally through the
network using Kirchhoff's power flow:

    CI_n(t) = [Σ_{g ∈ gen(n)} P_g(t)·EF_g  +  Σ_{m: F_mn>0} F_mn(t)·CI_m(t)]
              ──────────────────────────────────────────────────────────────────
              [Σ_{g ∈ gen(n)} P_g(t)  +  Σ_{m: F_mn>0} F_mn(t)]

where F_mn(t) = max(0, P_mn(t)) is the net import from neighbor m and EF_g is
the lifecycle emission factor of generator g (gCO₂/kWh).
Source: n.generators_t.p (dispatch), n.lines_t.p0 (flows), IPCC lifecycle EFs.

Result: CI_n(t) — hourly, consumption-based Scope 2 carbon intensity at nodal
resolution. Collapse to annual P50 for siting score; retain hourly series for
Scope 2 reporting and PPA matching.

Step 2 — ENTSO-E Transparency Platform as live alternative to PyPSA.
Library: entsoe-py (pip install entsoe-py). Pull actual generation-per-technology
(16.1.B&C) and cross-border flows (12.1.G) per bidding zone for the trailing 12
calendar months. Compute consumption-based CI via the same flow-tracing equations,
aggregated at bidding-zone granularity. Map bidding zones to PyPSA buses via
spatial join on ENTSO-E bidding zone GeoJSON.
Freshness: 24 h TTL (ENTSO-E updates D+1).

Step 3 — EU ETS carbon cost adder.
Multiply CI_n by the current EU ETS allowance price (€/tCO₂) to produce:

    carbon_cost_eur_mwh(n) = CI_n [gCO₂/kWh] × ETS_price [€/tCO₂] / 1e6

At ETS = €70/tCO₂ and CI = 350 gCO₂/kWh: carbon cost ≈ €24.5/MWh — a material
fraction of total energy cost. Source: EEX EUA spot price via REST API or
ember-climate.org ETS price series.
New column: carbon_cost_eur_mwh. Propagates to 02_energy_price all-in cost.
```

### `02_energy_price.py`

```text
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
```

### `03_land_price.py`

```text
LAND PRICE — Agricultural Land Transaction Prices (Eurostat apri_lprc)
=======================================================================
Theory
------
Land acquisition cost is a meaningful CapEx component for data center development,
typically 5–15 % of total project cost depending on site footprint and location.
A hyperscale DC (100+ MW) requires 20–100 ha of buildable land; site cost at
€20,000–€80,000/ha in rural EU regions adds €4 M–€8 M to project CapEx.

Agricultural land price (€/ha) is used as a DC siting proxy for three reasons:

  1. It is the only freely available EU-wide sub-national land price time series
     with consistent methodology, available at NUTS2 granularity via Eurostat
     dataset `apri_lprc` (Agricultural Land Prices and Rents).

  2. Farmland prices are driven by the same structural factors as industrial and
     commercial land prices: regional GDP per capita, infrastructure quality
     (proximity to highways, rail, fiber), development pressure, and urban
     proximity. A NUTS2 region with high farmland prices almost universally also
     has high industrial/commercial land prices.

  3. The Eurostat dataset records actual land transaction prices, not assessed or
     tax values — it reflects true market-clearing land costs in each region.

The "last 10 trades" rule applied here: average of the last 10 non-NaN annual
Eurostat observations per NUTS2 region. Each annual observation in `apri_lprc`
aggregates hundreds or thousands of individual agricultural land sales within the
NUTS2 region during that calendar year, so this equals averaging 10 annual market
clearing prices — a stable, low-volatility signal.

NUTS2 is the finest administrative level at which Eurostat consistently publishes
land transaction data. NUTS3 is available for some countries (Germany, France)
but not EU-wide. We use NUTS2 and assign the NUTS2 value to every PyPSA bus
whose centroid falls within that NUTS2 polygon (spatial join in 08_cleanup.py).

MVP Implementation
------------------
1. Fetch `apri_lprc` via the `eurostat` Python package (or REST API fallback).
2. Filter to unit=EUR_HA (price per hectare in euros) and landuse=AG (agricultural
   land, total arable + permanent grassland combined).
3. For each NUTS2 region: average of the last 10 non-NaN annual values.
4. Output NUTS2-level table. Spatial join to PyPSA nodes is in 08_cleanup.py.

Limitation: Farmland price ≠ industrial/DC land price. Urban NUTS2 regions
(Amsterdam, Frankfurt, Paris metropolitan) have scarce agricultural land and the
`apri_lprc` prices there are priced differently from commercial buildable land.
Rural regions near urban corridors may be underpriced in this proxy. This is a
first-order approximation suitable for macro-level regional screening.

Future Implementation
---------------------
Step 1 — Correct node area from Voronoi catchment polygons (not radius).
MVP cost computation uses a user-supplied dc_surface_m2 (DC footprint). But for
regional land cost estimation, the "area belonging to each node" must be derived
from the actual grid topology, not a circular radius approximation.

Source: PyPSA-Eur resources/regions_onshore.geojson — Voronoi catchment polygons,
one polygon per PyPSA bus, tiling the EU landmass with no overlap. Each polygon
is the geographic territory electrically served by that bus.

Computation (reproject to equal-area CRS for accurate area):
    regions = gpd.read_file('resources/regions_onshore.geojson')
    regions_ea = regions.to_crs('EPSG:3035')   # ETRS89-LAEA equal-area
    area_km2(n) = regions_ea.geometry.area / 1e6

New column: node_area_km2 (exported from 07_node_geometry, consumed here).
Land market depth signal (not DC land cost):
    land_cost_potential_eur(n) = land_price_eur_ha(n) × node_area_km2(n) × 100
Large cheap polygons signal better siting environments than small expensive ones.

Step 2 — Industrial land fraction via OSM land-use polygons.
For each node's Voronoi polygon, clip to OSM landuse=industrial polygons via
Overpass API: [out:json]; (way[landuse=industrial](bbox); relation[...]);
Compute: industrial_area_km2(n), industrial_fraction(n).
Nodes with industrial_fraction > 0.05 are in established industrial zones —
land is already zoned, permitted, and serviced. Price premium applies but
permitting risk is near zero. New column: industrial_fraction.

Step 3 — Commercial real estate APIs (requires license).
CoStar API or JLL Data & Analytics: industrial/logistics land price per NUTS3.
Use as direct replacement for apri_lprc when a license is available. Granularity:
municipality or cadastral parcel. License cost: ~€15,000–€40,000/year.
Fallback (free): HM Land Registry (UK), Kadaster (NL), German Bodenrichtwert
(WMS service) where national open registries are available.
```

### `04_infrastructure_access.py`

```text
CONNECTIVITY SCORE — Grid Infrastructure + Fiber/Internet Access (Merged)
=========================================================================
Theory
------
Data center siting requires two distinct connectivity layers to be viable:

  1. GRID INFRASTRUCTURE ACCESS
     A DC drawing >10 MW must connect at ≥110 kV (EU NC DCC Regulation 2016/1388).
     Connection CapEx = €0.5–1.2 M/km for a 110 kV aerial line + €1–3 M substation
     bay works. Beyond ~10 km from the nearest HV substation, grid connection cost
     dominates project economics. This is a hard binary constraint disguised as a
     continuous variable: sites >20 km from any HV substation are typically non-viable.

  2. FIBER / INTERNET CONNECTIVITY
     Low-latency (<10 ms RTT) fiber to an Internet Exchange Point (IXP) or PoP is
     a hard technical requirement. DC tenants requiring <4 ms to financial exchanges
     or cloud on-ramps can only be served at fiber-rich sites. Fiber leasing cost
     (dark fiber IRU or lit service) grows with distance from the nearest IXP and
     falls with the number of competing providers within reach.

Composite Score Architecture
-----------------------------
Two sub-scores are computed independently and merged 50/50:

    grid_access_score        = norm(dist_to_hv_substation_km)         [0–1]
    fiber_connectivity_score = 0.6 × (1 − norm(ixp_count_50km))
                             + 0.4 × norm(dist_to_nearest_ixp_km)     [0–1]

    connectivity_score = 0.5 × grid_access_score
                       + 0.5 × fiber_connectivity_score               [0–1]

DIRECTION: lower score = better site (closer to HV substation, more IXPs,
closer to nearest IXP). Consistent with energy_price, land_price, carbon_intensity
where lower = preferable. Score 0 = ideal connectivity; score 1 = worst connectivity.

Equal weighting (50/50) between grid and fiber reflects that both are hard
constraints: a DC that can't connect to the grid OR can't get fiber is non-viable,
regardless of how good the other dimension is.

Sub-signals
-----------
dist_to_hv_substation_km — OSM `power=substation` (voltage ≥ 110 kV). Direct
  CapEx driver. OSM has near-complete coverage for transmission-level substations.

ixp_count_50km — OSM `telecom=exchange` within 50 km. Proxies fiber provider
  count and dark fiber market competitiveness. 50 km = practical fiber leasing
  radius in EU metro areas. (No dedicated OSM fiber tag exists — see
  docs/independent-variables.md §2.)

dist_to_nearest_ixp_km — Distance to closest `telecom=exchange`. Sanity check:
  catches fiber-desert nodes where ixp_count_50km = 0 but nearest IXP is at 51 km.

OSM Data Coverage Note
----------------------
`telecom=exchange` coverage is sparse in Eastern EU. Nodes in EE, LV, LT, BG, RO,
HR, SI, SK, HU get `infra_data_quality='sparse'` — their fiber sub-score may be
systematically understated. Grid sub-score is reliable EU-wide.

MVP Implementation
------------------
Two sub-scores (grid, fiber), each min-max normalized across all EU nodes,
merged 50/50 into connectivity_score [0–1].

Future Implementation
---------------------
Step 1 — Grid layer: ENTSO-E TYNDP GIS dataset + GridKit.
Replace OSM power=substation with:
  a) ENTSO-E Ten-Year Network Development Plan (TYNDP) substation GIS layer —
     authoritative, TSO-reported, available as GeoJSON/KML from entsoe.eu.
     Covers all ≥110 kV substations EU-wide with voltage level, operator, capacity.
  b) GridKit (github.com/bdollma/gridkit) — topologically consistent HV network
     derived from OSM with automatic error correction. Better than raw OSM for
     substation identification in complex urban areas.
New fields: substation_voltage_kv (from TYNDP); dist_to_220kv_substation_km and
dist_to_400kv_substation_km as separate signals — 400 kV preferred for
hyperscale (>100 MW) DCs.

Step 2 — Fiber layer: PeeringDB + TeleGeography.
  a) PeeringDB REST API (peeringdb.com/api/ixlan) — authoritative IXP database,
     open and free. Returns IXP name, city, lat/lon, member count, policy.
     Replace OSM telecom=exchange with PeeringDB geometries.
     New field: ixp_member_count (proxy for fiber provider competition).
  b) TeleGeography Submarine Cable Map — cable landing stations as ultra-low-
     latency fiber anchors. Coastal nodes near landings get <1 ms RTT to
     transatlantic routes. New field: dist_to_cable_landing_km.
  c) AMS-IX, DE-CIX, LINX public PoP lists — major IXP remote PoPs beyond HQ.

Step 3 — Latency estimation.
    latency_to_nearest_ixp_ms(n) ≈ dist_to_nearest_ixp_km(n) × 0.005
    (fiber propagation: ~5 µs/km ≈ 200 km/ms)
Hard filter: nodes where latency_to_nearest_ixp_ms > 10 are ineligible for
latency-sensitive workloads. New column: latency_to_nearest_ixp_ms.

Step 4 — Existing DC proximity.
Fetch OSM building=data_center + man_made=data_center tags via Overpass.
Count existing DCs within 20 km: colocation_dcs_20km(n).
High count → established DC corridor → fiber-dense, power-zoned environment.
New column: colocation_dcs_20km.
```

### `05_congestion.py`

```text
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
```

### `06_capacity.py`

```text
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
```

### `08_cleanup.py`

```text
CLEANUP — Validation, Spatial Join, and Processed Dataset Export
=================================================================
This script:
  1. Loads all raw parquet files from data/raw/
  2. Performs the NUTS2 spatial join to assign land_price_eur_ha to each node
  3. Validates all scoring columns for schema correctness and value ranges
  4. Saves cleaned tables to data/processed/

No normalization happens here — raw values are preserved.
The final assembly into grid_nodes.parquet is performed by 09_build_table.py.
```

### `10_pypsa_fallback.py`

```text
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
```

### `09_build_table.py`

```text
BUILD TABLE — Final Dataset Assembly
======================================
Imports all processed parquet files from data/processed/, merges them on node_id,
and writes the final analysis-ready dataset to data/grid_nodes.parquet.

Output schema:

  Metadata columns (not scored):
    node_id             str       Bus/NUTS3 node id
    x                   float     Centroid longitude (EPSG:4326)
    y                   float     Centroid latitude  (EPSG:4326)
    country             str       ISO alpha-2

  Scoring columns (raw values):
    energy_price_eur_mwh    float   Annual mean LMP (€/MWh) — PyPSA
    land_price_eur_ha       float   Avg of last 10 annual values (€/ha) — Eurostat
    carbon_intensity_elec   float   National carbon intensity (gCO₂/kWh) — OWID
    connectivity_score      float   Composite grid+fiber connectivity 0–1
    congestion_frac         float   Fraction of hours >80% loading (0–1) — PyPSA
    consumption_mean_mw     float   Mean hourly load at node (MW) — PyPSA
    consumption_std_mw      float   Std dev hourly load at node (MW) — PyPSA
    capacity_mw             float   Total installed generation capacity (MW) — PyPSA

All scoring columns may be NaN where the upstream source is unavailable
(PyPSA-dependent columns are NaN if no network file was provided).
```

### `download_network.py`

```text
DOWNLOAD NETWORK — Zenodo PyPSA-Eur pre-built bundle
=====================================================
Downloads bundle.tar.xz from Zenodo record 13756400 (~85 MB), extracts it,
finds .nc network files, and checks whether OPF results are present.

Run from project root:
    python src/data_normalization/download_network.py

After running, set the env var printed at the end, then run:
    python src/data_normalization/02_energy_price.py   # if OPF present
    python src/data_normalization/05_congestion.py     # if OPF present
    python src/data_normalization/06_capacity.py
    python src/data_normalization/08_cleanup.py
    python src/data_normalization/09_build_table.py

If OPF results are NOT present in the bundle, run the fallback instead:
    python src/data_normalization/10_pypsa_fallback.py
```
