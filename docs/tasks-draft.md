# PoC Task Draft — DC Siting Intelligence Map

**Deadline:** 24h  
**Goal:** Interactive EU map overlaying capacity / price / carbon / congestion to reveal best DC sites. Filter by specs → highlights zones. Click zone → supply mix + LCOE estimate + optimized site recommendation.  
**Stack:** Python · FastAPI · Streamlit · Folium · Pydantic · pandas/geopandas · scipy.optimize · scikit-learn · transformers (GridSFM inference)  
**Output:** Streamlit app (judge-readable codebase) + FastAPI backend with domain separation

---

## Product Direction: Option 3 — Intelligence Map

Map IS the product. Options 1+2 are features within it:
- **Primary inputs (user sets these first):**
  - Required capacity: MW (fixed by market demand)
  - Building size: land footprint in m² (or ha) — determines land cost and availability filter
- Filter panel: carbon ceiling (hard constraint) + priority weights across scoring dimensions
- Optimization solver: given MW + land size + constraints → find optimal zone
- Site drill-down: click zone → scores + supply mix + LCOE + land cost estimate at specified inputs
- Export: site comparison table (CSV)

**Scoring dimensions (5, not 4):**
1. Energy cost (wholesale EUR/MWh)
2. Carbon intensity (gCO₂/kWh — hard ceiling filter)
3. Grid congestion / headroom
4. Connectivity (substation density + fiber)
5. **Land cost / availability** (EUR/m² by NUTS2, plot availability proxy) ← NEW

**Persona — User:** Jordan, DC infrastructure decision-maker (see `artifacts/persona.md`).  
**Persona — Buyer:** IC / CFO approving the site selection decision. Needs CFO-legible output, supply mix cost breakdown, carbon compliance evidence, land cost summary.

**Geographic granularity:** NUTS2 regions (~280 EU zones). Ember → country-level, pro-rated to NUTS2. PyPSA-Eur → zone approximation. OSM → substation density per NUTS2.

---

## Decision Engine — Dual Signal + Confluence

Three independent signals, one recommendation:

| Signal | Method | Output |
|---|---|---|
| A — Rule-based | Weighted 5-dimension composite score | Ranked list + per-dim breakdown |
| B — NPV model | DCF: capex (construction $/MW + land) + opex (energy + land) vs revenue → NPV per site | NPV estimate (EUR) |
| C — ML layer | Random Forest classifier (good/neutral/bad) + regression (predicted NPV). Trained on synthetic data: perturb NUTS2 features → score → label → noise → fit | class + confidence % |

**Confluence logic:**
- A + B + C agree positive → `STRONG SIGNAL — proceed`
- A + C agree, B diverges → `CAUTION — financial model shows risk`
- A + B agree, C diverges → `CAUTION — ML detects pattern anomaly`
- Majority negative → `ADVISE AGAINST`

**SiteResult output fields:** `signal_strength`, `rule_score`, `npv_estimate_eur`, `ml_class`, `ml_confidence`, `supply_mix`, `lcoe`, `narrative`

---

## Architecture

```
src/
  api/        FastAPI routes + Pydantic schemas
  core/
    scoring/  5-dimension scoring engine — pure Python, no I/O
    npv/      DCF model — capex, opex, revenue, NPV per site
    ml/       RF classifier + regression — train on synthetic, predict on live data
    signal/   confluence logic — combine A+B+C → signal_strength + reasoning
    supply/   supply mix optimizer + LCOE
  data/       loaders per source (Ember, PyPSA, OSM, geo, land)
  models/     domain models (SiteQuery, SiteScore, NPVResult, MLPrediction, SiteResult)
  services/   orchestration (query → score → NPV → ML → confluence → mix → response)
  ui/         Streamlit app
tests/
  unit/       core scoring functions + optimizer
  integration/ end-to-end query
data/         cached parquet + GeoJSON files
```

---

## Epics & Tasks

### Epic E0 — Desirability & Viability (12 SP) ← DO FIRST

> Validates WHO we're building for and WHY they'll pay. Required before any code. Feeds pitch deck directly.

| ID | Task | SP | Model | Status |
|---|---|---|---|---|
| TASK-001 | Define personas — user (Alex) and buyer (IC/CFO) | 2 | sonnet | backlog |
| TASK-002 | Customer journey map — before (current pain) | 2 | sonnet | backlog |
| TASK-003 | Customer journey map — after (with tool) | 2 | sonnet | backlog |
| TASK-004 | Jobs-to-be-done framework (3–5 JTBD statements) | 1 | sonnet | backlog |
| TASK-005 | Market viability analysis — TAM/SAM/SOM and pricing model | 3 | sonnet | backlog |
| TASK-006 | Pitch narrative and value proposition statement | 2 | sonnet | backlog |

---

### Epic E1 — Project Scaffold (4 SP)

| ID | Task | SP | Model | Status |
|---|---|---|---|---|
| TASK-007 | Python project init: src layout, pyproject.toml, uv env, dev deps | 1 | haiku | backlog |
| TASK-008 | FastAPI skeleton: health endpoint, CORS, error handling | 1 | haiku | backlog |
| TASK-009 | Streamlit skeleton: calls FastAPI, placeholder map component | 1 | haiku | backlog |
| TASK-010 | Pydantic domain models: SiteQuery (capacity_mw, building_footprint_m2, carbon_ceiling, weights), SiteScore (5 dims + composite), SupplyMix, SiteResult | 1 | haiku | backlog |

---

### Epic E2 — Data Layer (16 SP)

> Critical path. PyPSA failure → try GridSFM-Open → ENTSO-E fallback. Time-box each: 2h max per attempt.

| ID | Task | SP | Model | Status | Risk |
|---|---|---|---|---|---|
| TASK-011 | Ember: fetch EU carbon intensity CSV, compute zone averages, cache parquet | 2 | sonnet | backlog | Low |
| TASK-012 | PyPSA-Eur probe: download pre-solved network, extract nodal prices + headroom per zone | 5 | sonnet | backlog | **HIGH** |
| TASK-012b | **GridSFM-Open probe**: load microsoft/GridSFM-Open from HuggingFace, construct EU grid topology input (from OSM + ENTSO-E), run inference → branch flows + congestion + headroom per zone. If EU topology construction fails, use US topology as proxy for model validation only. | 5 | sonnet | backlog | **HIGH** |
| TASK-013 | [FALLBACK] ENTSO-E/SMARD wholesale prices by country — activate if both PyPSA and GridSFM fail | 3 | sonnet | backlog | Contingency |
| TASK-014 | OSM: Overpass query EU substations, compute density per NUTS2 | 3 | sonnet | backlog | Medium |
| TASK-015 | NUTS2 geoboundaries: download Eurostat shapefile, merge all sources into master GeoDataFrame | 2 | sonnet | backlog | Low |
| TASK-016 | DC economics constants: PUE=1.4, annual power draw formula, LCOE skeleton | 1 | haiku | backlog | Low |
| TASK-016b | Land cost data: source EU land price estimates by NUTS2 (Eurostat / ESPON / proxy from property indices), cache as parquet | 2 | sonnet | backlog | Medium |

---

### Epic E3 — Rule-Based Scoring Engine (13 SP)

> Pure Python, no I/O. All functions unit-testable. Scores [0–1] higher=better. Signal A of the dual-signal system.

| ID | Task | SP | Model | Status |
|---|---|---|---|---|
| TASK-017 | Scoring schema: 5 dimensions, default weights, normalization config | 1 | haiku | backlog |
| TASK-018 | Cost score: wholesale EUR/MWh → [0,1] inverted | 2 | sonnet | backlog |
| TASK-019 | Carbon score: hard filter on user ceiling, score remainder | 2 | sonnet | backlog |
| TASK-020 | Congestion score: PyPSA headroom/curtailment proxy inverted | 2 | sonnet | backlog |
| TASK-021 | Connectivity score: substation density + fiber proxy | 2 | sonnet | backlog |
| TASK-021b | Land score: EUR/m² → [0,1] inverted; hard filter zones where footprint unavailable | 2 | sonnet | backlog |
| TASK-022 | Composite ranker: weighted sum, apply hard filters, return top-N with per-dim breakdown | 2 | sonnet | backlog |

---

### Epic E3b — NPV Model (8 SP)

> Signal B. DCF on site investment. Inputs: capacity MW, footprint m², zone energy/land data. Output: NPV estimate in EUR.

**Formula skeleton:**
```
capex = construction_cost_per_mw × capacity_mw + land_price_per_m2 × footprint_m2
annual_opex = blended_energy_cost × capacity_mw × PUE × 8760 + land_lease
annual_revenue = capacity_mw × utilization_rate × rack_rate_eur_per_mw_year
npv = sum((annual_revenue - annual_opex) / (1+r)^t for t in 1..horizon) - capex
```

| ID | Task | SP | Model | Status |
|---|---|---|---|---|
| TASK-023a | NPV model constants: construction $/MW by EU region, discount rate, horizon, utilization defaults | 1 | haiku | backlog |
| TASK-023b | DCF engine: compute NPV per NUTS2 zone given capacity + footprint + zone data | 3 | sonnet | backlog |
| TASK-023c | NPV sensitivity: vary energy cost ±20%, land cost ±20% → NPV range (for IC presentation) | 2 | sonnet | backlog |
| TASK-023d | NPV ranker: normalize NPV across zones → [0,1] score, return top-N | 2 | sonnet | backlog |

---

### Epic E3c — ML Signal Layer (10 SP)

> Signal C. Random Forest classifier (good/neutral/bad) + regression (predicted NPV). Trained on synthetic data via gridfm-datakit. Provides independent second opinion.
>
> ⚠️ **Explainability constraint:** RF must expose feature importances + SHAP values per prediction. No black-box output — every signal must show WHY. This satisfies pitch deck defensibility and the original "no black-box ML" constraint.

| ID | Task | SP | Model | Status |
|---|---|---|---|---|
| TASK-023e | Synthetic training data: use `gridfm-datakit` (PF/OPF perturbation pipeline) + NUTS2 feature augmentation to generate labeled training set. Label = scoring rule output + NPV. | 3 | sonnet | backlog |
| TASK-023f | RF classifier: train on synthetic data, predict {good/neutral/bad} + confidence %; expose feature importances + SHAP values per prediction | 3 | sonnet | backlog |
| TASK-023g | NPV regression: train on synthetic data, predict NPV per zone; expose top feature contributions | 2 | sonnet | backlog |
| TASK-023h | Signal confluence: combine rule score (A) + NPV model (B) + ML class (C) → signal_strength {STRONG/CAUTION/AGAINST} + human-readable reasoning string citing divergent features | 2 | sonnet | backlog |

---

### Epic E4 — Supply Mix Engine (7 SP)

> Answers: "For this site, what blend of grid / PPA / on-site gives lowest LCOE at target carbon?"

| ID | Task | SP | Model | Status |
|---|---|---|---|---|
| TASK-024 | LCOE model: blended EUR/MWh for grid/PPA/on-site mix at a site | 2 | sonnet | backlog |
| TASK-025 | PPA opportunity flag: high curtailment → PPA discount, flag zones | 2 | sonnet | backlog |
| TASK-026 | Supply mix optimizer: optimal % breakdown + estimated annual cost at user MW | 3 | sonnet | backlog |

**LCOE formula:**  
`blended_EUR/MWh = (grid_pct × spot_price) + (ppa_pct × ppa_rate) + (onsite_pct × onsite_lcoe)`  
Annual cost = `blended × IT_load_MW × PUE × 8760`

---

### Epic E5 — Map & UI (12 SP)

| ID | Task | SP | Model | Status |
|---|---|---|---|---|
| TASK-027 | NUTS2 choropleth map: composite score fill color, tooltip with zone name + signal_strength badge | 3 | sonnet | backlog |
| TASK-028 | Layer toggle: switch overlay between cost/carbon/congestion/connectivity/NPV/composite | 2 | sonnet | backlog |
| TASK-029 | Filter panel: capacity MW + footprint m² (primary inputs), carbon ceiling, priority weights → re-score + re-render | 2 | sonnet | backlog |
| TASK-030 | Site drill-down: click zone → signal badge (STRONG/CAUTION/AGAINST), scores table, NPV estimate + sensitivity, supply mix, LCOE, narrative | 3 | sonnet | backlog |
| TASK-031 | Narrative generator: Claude API (haiku), CFO-legible explanation including signal reasoning and NPV range | 2 | haiku | backlog |

---

### Epic E6 — Integration & Demo (6 SP)

| ID | Task | SP | Model | Status |
|---|---|---|---|---|
| TASK-032 | Unit tests: scoring engine, NPV model, ML predictions, confluence logic | 3 | haiku | backlog |
| TASK-033 | E2E integration test: 3 canned queries, assert ≥3 results, correct ranking, <30s | 2 | haiku | backlog |
| TASK-034 | Demo scenarios: cost-first (Poland/Balkans), carbon-first (Nordics), balanced (Iberia) | 1 | haiku | backlog |
| TASK-035 | README: ASCII architecture diagram, data sources, run instructions, PoC limits | 1 | haiku | backlog |

---

## Total: 98 SP

| Epic | SP | Priority |
|---|---|---|
| E0 Desirability & Viability | 12 | **CRITICAL — do first** |
| E1 Scaffold | 4 | Must |
| E2 Data Layer | 23 | Must (PyPSA → GridSFM → ENTSO-E fallback chain) |
| E3 Rule-Based Scoring | 13 | Must |
| E3b NPV Model | 8 | Must |
| E3c ML Signal Layer | 10 | Must |
| E4 Supply Mix | 7 | Must |
| E5 Map & UI | 12 | Must |
| E6 Integration | 7 | Must |

---

## 24h Critical Path

```
Hour 00–03  E0 desirability work (personas, journey maps, JTBD, viability) — parallel research
Hour 03–04  E1 scaffold + E2-T1 (Ember) + E2-T12 probe (PyPSA) + E2-T12b probe (GridSFM-Open) — parallel
Hour 04–06  E2-T4 (OSM) + E2-T5 (NUTS2 merge) — data decision point: which congestion source won?
Hour 06–11  E3 scoring engine (T1–T6) + E3b NPV model + E3c ML layer (synthetic data → train → confluence)
Hour 11–14  E4 supply mix + E2-T6 economics
Hour 14–19  E5 map + UI (choropleth → filter → drill-down)
Hour 19–21  E5-T5 narrative generator + E0-T6 pitch narrative
Hour 21–23  E6 integration tests + demo scenarios
Hour 23–24  E6-T4 README + final smoke test
```

**Risk 1:** E2-T12 (PyPSA) + E2-T12b (GridSFM EU topology). Both high. Time-box 2h each. If both fail → ENTSO-E fallback (E2-T13). At least one congestion source must land.  
**Risk 2:** GridSFM EU topology construction — existing GridSFM dataset is US-only. Need ENTSO-E or OSM-derived EU grid topology in PowerModels.jl format. May be too costly for 24h; if so, use GridSFM for pitch credibility + US proof-of-concept only.  
**Risk 3:** E3c ML layer. If synthetic data + RF training is too slow, drop ML signal; keep rule-based + NPV as dual signal (still strong pitch story).

---

## Open Decisions

- [ ] PPA rate model: `spot × (1 - curtailment_discount)` or published indicative rates by country?
- [ ] Map library: Folium (no token, safer for 24h) vs PyDeck (Mapbox token needed)
- [ ] Deploy: Streamlit Cloud (needs GitHub push) or local demo only?
- [ ] Optimizer objective: single-objective (min cost OR min carbon) or Pareto front?
- [ ] Export (CSV): in-scope for PoC or cut?
