# DC Siting Intelligence — To-Be Architecture

## Context

The MVP is a 3-stage pipeline (`load_filter → compute → rank`) reading a pre-built `grid_nodes.parquet`. It works. It also has specific, citable correctness problems documented below. This file covers:

1. MVP audit — what's wrong and why
2. To-be model architecture — hardened scoring pipeline
3. CNN satellite land analysis layer — post-ranking land acquisition support
4. Runtime data pipeline — replacing offline parquet with live fetching

---

## 1. MVP Audit

### Stage 1 — `01_load_filter.py`

**Hard gate uses nameplate capacity, not headroom.**
`capacity_mw >= dc_capacity_mw` checks the sum of `p_nom` (installed nameplate). A 500 MW nameplate node in a congested zone may have 0 MW of actual connectable headroom. Gate should be on `headroom_mw_p05`.

**Negative LMP clipping destroys signal.**
Negative day-ahead prices flag excess-renewable periods — exactly what a green DC co-location strategy targets. Clipping to 0 removes this advantage signal entirely.

---

### Stage 2 — `02_compute.py`

**Gaussian consumption model is wrong.**
`congestion_alpha` models nodal load as N(mean, std²) and shifts the mean by DC demand. Real grid consumption is bimodal (day/night cycle), seasonally heteroskedastic, and highly autocorrelated. A Gaussian underestimates peak-hour tail risk — the exact scenario where congestion matters most.

**DC load modeled as mean shift.**
HPC data centers draw >95% of nameplate load continuously (24/7). This creates a new consumption floor, not a perturbation to a Gaussian mean.

**National carbon intensity, not nodal.**
`carbon_intensity_elec` is a country-level annual average from OWID. A bus in northern Germany adjacent to offshore wind has a marginal unit at ~20 gCO₂/kWh; the national average is ~400 gCO₂/kWh. Needs hourly nodal marginal carbon via PyPSA network flow tracing.

**LMP spread data exists but is unused.**
`lmp_p05`, `lmp_p95`, `lmp_spread_p95p5` are in the parquet but dropped. A node with mean 50 €/MWh and spread 100 €/MWh has enormous hedging cost vs one at 10 €/MWh spread — critical input for battery storage sizing.

**Land price is an agricultural proxy.**
Eurostat `apri_lprc` is arable land. Industrial/brownfield prices diverge 5–20× from agricultural — making `total_cost_eur` unreliable as an absolute number.

**Connectivity score passed through unvalidated.**
OSM data has documented quality gaps in EE, LV, LT, BG, RO, HR, SI, SK, HU (flagged in `infra_data_quality`). Nodes in these countries get penalized unfairly with no flag to the caller.

---

### Stage 3 — `03_rank.py`

**Max normalization is outlier-sensitive.**
`/ max` across all nodes means one outlier pulls the entire distribution toward 0. Should cap at P95 per dimension before normalizing.

**"Pareto" table is mislabeled.**
It is max-normalized, not a true Pareto-optimal set. No dominance relationship is computed. A node strictly better than another on all 4 dimensions is not identified.

**Equal weighting across dimensions.**
No user preference vector accepted. A CFO-driven query weights `total_cost_eur` at 60%; a sustainability officer weights `dc_carbon_tco2_yr` at 60%.

**L2 norm ignores dominance.**
Node A `[0.3, 0.3, 0.3, 0.3]` beats node B `[0.1, 0.1, 0.1, 0.9]` by balance score, but B strictly dominates on 3 of 4 dimensions and should rank higher.

**No uncertainty quantification.**
All scores are point estimates. OSM-sparse nodes, interpolated land prices, and missing PyPSA values are treated with identical confidence.

---

## 2. To-Be Model Architecture

### Stage 0 — Query Intake *(new)*

Input schema:
```json
{
  "dc_capacity_mw": 50,
  "dc_surface_m2": 40000,
  "priority_weights": {
    "cost": 0.4,
    "carbon": 0.3,
    "congestion": 0.2,
    "latency": 0.1
  }
}
```

- Validate weights sum to 1.0; apply equal defaults if absent.
- Resolve data freshness: live fetch vs. cache (see §4).

---

### Stage 1 — Load & Filter *(hardened)*

- Gate on `headroom_mw_p05 >= dc_capacity_mw` instead of `capacity_mw`.
- Soft filter: tag OSM-sparse countries `low_confidence=True` — do not drop, propagate flag downstream.
- Preserve negative LMPs as-is; add `has_negative_lmp: bool` as a feature.
- Pass `infra_data_quality` through to Stage 3 for uncertainty bands.

---

### Stage 2 — Compute *(enriched)*

**Congestion:** Replace Gaussian model with `congestion_frac` directly (already computed in `05_congestion.py`). Derive `connection_queue_risk` category:

| `congestion_frac` | Risk |
|---|---|
| < 0.05 | GREEN — connect today |
| 0.05 – 0.25 | AMBER — reinforcement likely |
| > 0.25 | RED — 5–10 year queue |

(Thresholds per `docs/independent-variables.md §3c`.)

**Carbon:** Add `marginal_carbon_intensity` via PyPSA network flow tracing (or GridSFM inference). Keep national average as labelled fallback with `carbon_source: "national_avg"` flag.

**Cost (hedged):**
```
energy_cost_mean = lmp_mean × dc_capacity_mw × 8760
energy_cost_p95  = lmp_p95  × dc_capacity_mw × 8760
cost_at_risk     = energy_cost_p95 - energy_cost_mean
```

**Land:** Flag `land_price_source: "agricultural_proxy"`. For top-N nodes, trigger commercial real estate lookup (CoStar/JLL API or OSM land-use polygon extraction) to refine.

**PPA signal:** Add `ppa_opportunity_score` = fraction of adjacent generator capacity from wind + solar. Proxy for Power Purchase Agreement negotiability.

---

### Stage 3 — Rank *(proper)*

**Quantile normalization:** Cap each dimension at P95, clip outliers, normalize to [0, 1].

**User-weighted composite:**
```
weighted_score = Σ (weight_i × norm_score_i)
```
using client priority vector from Stage 0.

**True Pareto front:** Compute strict dominance across all 4 score dimensions. Output `pareto_rank` column: `0` = Pareto-optimal (not dominated by any other node), `1` = dominated by exactly 1 node, etc. Present top-3 from Pareto front as primary recommendations.

**Uncertainty bands:** Propagate `infra_data_quality` and `low_confidence` flags into a `confidence` label per node: `HIGH` / `MEDIUM` / `LOW`.

**Enriched output columns:**
```
node_id, country, x, y,
weighted_score, pareto_rank, confidence,
connection_queue_risk, ppa_opportunity_score,
cost_at_risk, carbon_source, land_price_source
```

---

## 3. CNN Satellite Land Analysis Layer

> **STATUS — IMPLEMENTED (Stage 4).** Realized in `src/model/04_site_analysis.py` +
> the `src/model/site_analysis/` package, using the **pretrained Google Dynamic
> World CNN** (`google/dynamicworld` TF SavedModel, local inference) instead of the
> MobileNet/CORINE design sketched below. Imagery + DEM are fetched on-the-go from
> Microsoft Planetary Computer; the DW `built` class is refined into industrial/
> commercial/residential via OSM landuse; environmental exclusions use EEA Natura
> 2000 + CDDA. Scoring follows the client spec
> (`final = 0.35·land + 0.25·grid + 0.15·road + 0.10·slope + 0.15·area`) and the
> output is the bounding box + largest inscribed circle per node. Exposed via
> `POST /site-analysis`. The original sketch below is retained for context.

After ranking, the model has `(lat, lon)` for top-N nodes. The CNN layer answers: *"What does the actual buildable land around this node look like, and where exactly should the client acquire land?"*

### Input

- `(lat, lon)` of top-N nodes from Stage 3.
- Radius: configurable, default 5 km.
- Image: **Sentinel-2 L2A** at 10 m resolution, RGB + NIR bands. Fetched via Copernicus Data Space Ecosystem API or Google Earth Engine Python client.

### Model

- **Task:** Semantic segmentation — classify each 10 m² pixel into land-use class.
- **Backbone:** MobileNetV3-Small or EfficientNet-B0 (~3 M parameters). Fast CPU inference.
- **Decoder:** U-Net style upsampling with skip connections.
- **Training data:** Sentinel-2 tiles + CORINE Land Cover 2018 labels (EU-wide, freely available from EEA). Pre-trained weights: SentinelHub `eo-learn` land cover model.

### Output Classes

| # | Class | DC Suitability |
|---|---|---|
| 1 | Industrial / brownfield | **Ideal** — existing permits, grid-proximate |
| 2 | Greenfield / agricultural | **Buildable** — new permits needed |
| 3 | Existing built-up / commercial | Possible — high acquisition cost |
| 4 | Water bodies | Excluded |
| 5 | Forest / protected area | Likely restricted — check Natura 2000 |
| 6 | Urban residential | Excluded |
| 7 | Infrastructure (roads, substations) | Informative — proximity signal |

### Output per Node

```
buildable_area_ha       float   sum of class 1 + 2 pixels → hectares
land_suitability_score  float   brownfield(1.0) > greenfield(0.7) > commercial(0.4) > rest(0)
buildable_patch         GeoJSON minimum bounding rectangle of largest contiguous buildable area
```

### Map Overlay

- Extend `graphify-out/graph.html` (Leaflet/Mapbox).
- Per node: colored polygon drawn over the largest buildable patch.
- Popup: `{ buildable_area_ha, land_suitability_score, dominant_class }`.
- Export: GeoJSON with all patches for downstream GIS / land acquisition workflow.

**Runtime:** ~2–5 s/node on CPU, ~0.5 s on GPU. Top-5 nodes → 10–25 s total. Within the 30 s SLA.

---

## 4. Runtime Data Pipeline

**Current:** 9 normalization scripts run offline, produce `grid_nodes.parquet` as a static artifact. No freshness guarantee.

**Target:** Async runtime fetcher invoked per query, with tiered caching.

### Fetcher Architecture

```
QueryHandler
  └── DataOrchestrator (async, parallel)
        ├── GridFetcher       → PyPSA-Eur network (.nc) or GridSFM inference
        ├── CarbonFetcher     → ENTSO-E Transparency Platform / Electricity Maps API
        ├── PriceFetcher      → ENTSO-E day-ahead prices via entsoe-py
        ├── LandFetcher       → Eurostat REST apri_lprc + OSM land-use polygons
        ├── InfraFetcher      → OSM Overpass API + PeeringDB IXP API
        └── CacheLayer        → Redis L2 + in-process cachetools.TTLCache L1
```

### Per-Source Freshness

| Source | Current | Runtime Target | Cache TTL |
|---|---|---|---|
| PyPSA grid topology | `.nc` offline file | Zenodo bundle + disk cache | 30 days |
| ENTSO-E day-ahead prices | Annual mean from PyPSA OPF | `entsoe-py` last 365 d per bidding zone | 24 h |
| ENTSO-E carbon flow | National annual (OWID) | `entsoe-py` + network flow tracing per bus | 24 h |
| Eurostat land price | `apri_lprc` REST (already live) | Same, batched at startup | 7 days |
| OSM substations / IXPs | Overpass + `.gpkg` cache | Overpass API + `.gpkg` cache | 7 days |
| GridSFM OPF inference | Not used | `microsoft/gridsfm` on HuggingFace for top-N | per-query |

### Cache Layers

- **L1 (in-process):** `cachetools.TTLCache` — same-session repeated queries hit memory.
- **L2 (disk):** Parquet files with metadata sidecar `{fetched_at, source_version}` — the existing parquet structure is reused as a cache format, not discarded.
- **L3 (cold):** Full re-fetch from upstream APIs on cache miss or TTL expiry.

### Graceful Degradation

- ENTSO-E unavailable → fall back to L2 cached parquet, log staleness age in API response.
- Overpass unavailable → use cached `.gpkg`.
- PyPSA network path not set → raise `DataUnavailableError` with user-facing message (not a silent NaN).

---

## 5. Future Implementation — Normalization File Stubs

Each `src/data_normalization/0N_*.py` has an empty `Future Implementation` docstring section. Concrete designs:

| File | Future implementation |
|---|---|
| `01_carbon_emissions.py` | PyPSA carbon flow tracing (Kirchhoff equations) assigns hourly marginal carbon per bus; ENTSO-E as fallback |
| `02_energy_price.py` | `entsoe-py`: pull last 365 d day-ahead prices per bidding zone, spatial-join bidding zone polygons to PyPSA bus coordinates |
| `03_land_price.py` | CoStar/JLL API for industrial land price per NUTS3; OSM `landuse=industrial` polygon extraction as fallback |
| `04_infrastructure_access.py` | PeeringDB REST API for IXP database; ENTSO-E GIS layers (TYNDP) for HV substation locations |
| `05_congestion.py` | N-1 contingency simulation: remove each adjacent line one at a time, re-solve DC OPF, measure worst-case flow increase |
| `06_capacity.py` | Firm capacity = `p_nom × capacity_factor` or P10 annual generation from time-resolved dispatch (not nameplate sum) |
| `06_headroom.py` | DC sensitivity analysis: inject ΔP test load at each bus, re-solve DC power flow, measure Δflow on adjacent lines — true headroom rather than bottleneck proxy |
| `07_node_geometry.py` | PyPSA-Eur Voronoi catchments from `regions_onshore.geojson` for true substation service area boundaries |
