# DC Siting Intelligence — ML Forecasting Architecture

## Direction

The current scoring pipeline computes cost, carbon intensity, congestion, and headroom from static or annual-average proxies. The next phase replaces every placeholder forecast with ML-inferred values and expands the independent variable set to cover signals currently ignored.

---

## ML Tools for Forecasting Scoring Inputs

**Time-series models** (energy price, carbon intensity, congestion load):
- **Temporal Fusion Transformer (TFT)** — handles multi-horizon forecasts with mixed static/temporal covariates; fits LMP and carbon intensity jointly with calendar, weather, and grid topology features.
- **LightGBM / XGBoost on lagged features** — gradient-boosted trees on rolling statistics; robust baseline for headroom and congestion-fraction prediction where tabular structure dominates.

**Physics-informed / graph models** (power flow, congestion, headroom):
- **GridSFM (microsoft/gridsfm)** — AC-OPF foundation model; predicts bus voltages, branch flows, and congestion in milliseconds without running a full solver. Replaces PyPSA static snapshots for per-query inference.
- **Graph Neural Network (GNN) on PyPSA topology** — node embeddings encode grid neighborhood; used to propagate congestion signals from data-rich buses to data-sparse ones.

**Tabular regression** (land price, infrastructure score):
- **Random Forest / LightGBM** — trained on Eurostat NUTS3 industrial transaction data and OSM land-use features; replaces the agricultural-land proxy.

**Uncertainty quantification:**
- **Conformalized quantile regression** on any of the above — produces calibrated prediction intervals that feed directly into the `confidence` label per node.

---

## Expanded Independent Variables

Variables marked *(docstring)* are explicitly designed in `src/data_normalization/` Future Implementation sections. Variables marked *(new)* are not yet in any script.

**Energy / cost dimension** — `02_energy_price.py`

| Variable | Computation | Signal |
|---|---|---|
| `carbon_cost_eur_mwh` *(docstring)* | `CI_n × ETS_price / 1e6` | EU ETS obligation cost; adder to raw LMP for true all-in price |
| `ppa_discount_proxy` *(docstring)* | `P(LMP_n ≤ 0)` from ENTSO-E hourly prices | Renewable curtailment fraction → PPA discount negotiability |
| `arbitrage_eur_mwh` *(docstring)* | `lmp_p95 − lmp_p05` per bus | Revenue floor for co-located BESS doing peak-shaving |

**Carbon dimension** — `01_carbon_emissions.py`

| Variable | Computation | Signal |
|---|---|---|
| `CI_n(t)` nodal hourly *(docstring)* | Kirchhoff flow-tracing over PyPSA dispatch + IPCC EFs | Replaces national annual average; resolves 20–30% intra-country spread |

**Congestion / grid dimension** — `05_congestion.py`, `06_capacity.py`

| Variable | Source | Signal |
|---|---|---|
| `redispatch_intensity_gwh_per_gw` *(docstring)* | ENTSO-E 14.1.C trailing 12 months | Real TSO operational evidence of structural congestion |
| `tso_hosting_capacity_mw` *(docstring)* | TSO hosting capacity maps (NL, DE, IE) | Hard filter: published available capacity below DC demand → exclude |
| `firm_capacity_mw` *(docstring)* | `Σ dispatchable p_nom` (gas, nuclear, hydro) | Reliable backup signal; excludes weather-dependent nameplate |
| `renewable_fraction` *(docstring)* | `variable_capacity / total_capacity` | PPA opportunity and Scope 2 quality proxy |
| `storage_capacity_mwh` *(docstring)* | `Σ storage_units p_nom × max_hours` | Co-located BESS arbitrage feasibility |

**Connectivity / infrastructure dimension** — `04_infrastructure_access.py`

| Variable | Source | Signal |
|---|---|---|
| `dist_to_400kv_substation_km` *(docstring)* | ENTSO-E TYNDP GIS + GridKit | 400 kV required for hyperscale (>100 MW); separate from 220 kV signal |
| `ixp_member_count` *(docstring)* | PeeringDB REST API | Fiber provider competition at nearest IXP |
| `dist_to_cable_landing_km` *(docstring)* | TeleGeography submarine cable map | Sub-ms RTT to transatlantic routes for coastal nodes |
| `latency_to_nearest_ixp_ms` *(docstring)* | `dist_km × 0.005` (fiber: 5 µs/km, PeeringDB coords) | Computed latency; hard filter >10 ms excludes latency-sensitive workloads |
| `colocation_dcs_20km` *(docstring)* | OSM `building=data_center` via Overpass | Established DC corridor: fiber-dense, power-zoned, permitted |

**Land / geometry dimension** — `03_land_price.py`, `07_node_geometry.py`

| Variable | Source | Signal |
|---|---|---|
| `industrial_fraction` *(docstring)* | OSM `landuse=industrial` clipped to Voronoi polygon | Pre-zoned land; permitting risk near zero vs. greenfield |
| `node_area_km2` *(docstring)* | PyPSA-Eur `regions_onshore.geojson` Voronoi (EPSG:3035) | Replaces circular radius; land market depth input |
| `geometry_source` *(docstring)* | pypsa_voronoi / entso_voronoi / nuts3_centroid | Confidence tier; propagates to score uncertainty band |

**New signals not yet in any normalization script** *(new)*

| Variable | Source | Signal |
|---|---|---|
| ERA5 wind + solar capacity factor at node | Copernicus CDS hourly reanalysis | Direct PPA curtailment risk; cross-validates `ppa_discount_proxy` |
| Water availability index | EEA waterbase (river flow / aquifer stress) | Cooling feasibility: air vs. liquid vs. direct water |
| Seismic hazard index | EFEHR EU seismic hazard model | Infrastructure risk; affects insurance and civil engineering cost |
| Regulatory permitting speed (NUTS2) | EC Energy Communities tracker | Time-to-connect risk; high variance across member states |

---

## Limitations

GridSFM is trained on US topology — EU bus numbering and voltage levels require re-encoding via gridfm-datakit before inference is valid. TFT requires ≥2 years of hourly ENTSO-E data per bidding zone; Eastern European zones have documented gaps that force fallback to N-BEATS on shorter windows. GNN node embeddings transfer poorly to buses with fewer than 3 adjacent lines (island nodes, radial feeders), producing high-variance estimates that must be flagged. Land price models trained on Eurostat NUTS3 averages will overfit to Western European transaction density; EE/LV/LT/BG/RO nodes need held-out validation before deployment. Conformalized intervals assume exchangeability — valid for stationary historical periods, but distribution shift from grid topology changes (new lines, decommissioned plants) invalidates coverage guarantees until the model is retrained. All forecasting models require scheduled retraining cadence (monthly for price/carbon, quarterly for grid topology) to avoid stale predictions silently degrading scores.
