# PoC Task Draft — DC Siting Intelligence Map

**Deadline:** 24h  
**Goal:** Interactive EU map overlaying capacity / price / carbon / congestion to reveal best DC sites. Filter by specs → highlights zones. Click zone → supply mix + LCOE estimate.  
**Stack:** Python · FastAPI · Streamlit · PyDeck or Folium · Pydantic · pandas/geopandas  
**Output format:** Streamlit app (clean, judge-readable codebase) + FastAPI backend with domain separation

---

## Product Direction: Option 3 — Intelligence Map

Map IS the product. Options 1+2 are features within it:
- Filter panel (Option 1): input MW + carbon ceiling → dim bad zones, highlight good ones
- Site drill-down (Option 2): click zone → scores + supply mix + LCOE
- Export: site comparison table (CSV)

**Persona:** Alex, energy analyst at infrastructure fund. Mandate to find top EU markets for 80–150 MW DC. Presents to IC. Needs explorable map + boardroom-ready drill-down.

**Geographic granularity:** NUTS2 regions (~280 EU zones). Ember → country-level, pro-rated to NUTS2. PyPSA-Eur → zone approximation. OSM → substation density per NUTS2.

---

## Architecture

```
src/
  api/        FastAPI routes + Pydantic schemas
  core/       scoring engine + supply mix — pure Python, no I/O
  data/       loaders per source (Ember, PyPSA, OSM, geo)
  models/     domain models (Site, Score, SupplyMix, Query)
  services/   orchestration (query → score → mix → response)
  ui/         Streamlit app
tests/
  unit/       core scoring functions
  integration/ end-to-end query
data/         cached parquet + GeoJSON files
```

---

## Epics & Tasks

### Epic 1 — Project Scaffold (4 SP)

| ID | Task | SP | Model | Status |
|---|---|---|---|---|
| E1-T1 | Python project init: src layout, pyproject.toml, uv env, dev deps | 1 | haiku | backlog |
| E1-T2 | FastAPI skeleton: health endpoint, CORS, error handling | 1 | haiku | backlog |
| E1-T3 | Streamlit skeleton: calls FastAPI, placeholder map component | 1 | haiku | backlog |
| E1-T4 | Pydantic domain models: `SiteQuery`, `SiteScore`, `SupplyMix`, `SiteResult` | 1 | haiku | backlog |

---

### Epic 2 — Data Layer (15 SP)

> **Critical path.** Do data probes first 2 hours. PyPSA failure → activate fallback immediately.

| ID | Task | SP | Model | Status | Risk |
|---|---|---|---|---|---|
| E2-T1 | Ember: fetch EU country carbon intensity CSV, compute zone averages, cache as parquet | 2 | sonnet | backlog | Low |
| E2-T2 | PyPSA-Eur probe: download pre-solved network (Zenodo), extract nodal prices + headroom + curtailment by zone | 5 | sonnet | backlog | **HIGH** |
| E2-T3 | [FALLBACK] ENTSO-E / SMARD: wholesale price by country if PyPSA fails | 3 | sonnet | backlog | Contingency |
| E2-T4 | OSM: Overpass query for EU substation locations, compute density per NUTS2 | 3 | sonnet | backlog | Medium |
| E2-T5 | NUTS2 geoboundaries: download Eurostat shapefile, merge all sources into unified GeoDataFrame, cache as GeoParquet | 2 | sonnet | backlog | Low |
| E2-T6 | DC economics constants: PUE=1.4 default, annual power draw formula (IT load × PUE × 8760), LCOE skeleton | 1 | haiku | backlog | Low |

---

### Epic 3 — Scoring Engine (11 SP)

> Pure Python, no I/O. All functions unit-testable. Scores normalized [0–1], higher = better.

| ID | Task | SP | Model | Status |
|---|---|---|---|---|
| E3-T1 | Scoring schema: 4 dimensions, default weights, normalization rules, config-driven | 1 | haiku | backlog |
| E3-T2 | Cost score: map wholesale €/MWh → [0–1] inverted (cheaper = higher) | 2 | sonnet | backlog |
| E3-T3 | Carbon score: Ember gCO₂/kWh — hard filter on user ceiling, score remainder | 2 | sonnet | backlog |
| E3-T4 | Congestion score: PyPSA headroom / curtailment rate → inverted congestion proxy | 2 | sonnet | backlog |
| E3-T5 | Connectivity score: substation density + fiber proxy (OSM road/fiber data) | 2 | sonnet | backlog |
| E3-T6 | Composite ranker: weighted sum, apply all filters, return top-N NUTS2 zones with per-dimension breakdown | 2 | sonnet | backlog |

---

### Epic 4 — Supply Mix Engine (7 SP)

> Answers: "For this site, what blend of grid / PPA / on-site gives lowest LCOE at target carbon?"

| ID | Task | SP | Model | Status |
|---|---|---|---|---|
| E4-T1 | LCOE model: compute blended €/MWh for a given grid%/PPA%/on-site% mix at a site | 2 | sonnet | backlog |
| E4-T2 | PPA opportunity flag: high curtailment → PPA discount = `curtailment_rate × 0.35`, flag zones | 2 | sonnet | backlog |
| E4-T3 | Supply mix optimizer: given zone data, output optimal % breakdown + estimated annual cost at user's MW | 3 | sonnet | backlog |

**LCOE formula (simplified):**  
`blended_€/MWh = (grid_pct × spot_price) + (ppa_pct × ppa_rate) + (onsite_pct × onsite_lcoe)`  
Annual power cost = `blended × IT_load_MW × PUE × 8760`

---

### Epic 5 — Map & UI (12 SP)

| ID | Task | SP | Model | Status |
|---|---|---|---|---|
| E5-T1 | NUTS2 choropleth map: render composite score as fill color, tooltip with zone name + top score | 3 | sonnet | backlog |
| E5-T2 | Layer toggle: switch overlay between cost / carbon / congestion / connectivity / composite | 2 | sonnet | backlog |
| E5-T3 | Filter panel: input IT load (MW), carbon ceiling (gCO₂/kWh), priority weight slider → re-score + re-render | 2 | sonnet | backlog |
| E5-T4 | Site drill-down panel: click zone → scores table, supply mix bar chart, LCOE estimate, plain-language blurb | 3 | sonnet | backlog |
| E5-T5 | Narrative generator: Claude API call, generate CFO-legible 3-sentence explanation per site using real score data | 2 | sonnet | backlog |

---

### Epic 6 — Integration & Demo (6 SP)

| ID | Task | SP | Model | Status |
|---|---|---|---|---|
| E6-T1 | Unit tests: scoring engine pure functions (cost/carbon/congestion/connectivity/composite) | 2 | haiku | backlog |
| E6-T2 | E2E integration test: 3 canned queries, assert ≥3 results, correct ranking direction, <30s | 2 | haiku | backlog |
| E6-T3 | Demo scenarios: cost-first (Poland/Balkans), carbon-first (Nordics/France), balanced (Iberia) — hardcoded drill-downs if dynamic is slow | 1 | haiku | backlog |
| E6-T4 | README: architecture diagram (ASCII), data sources, run instructions, PoC limitations | 1 | haiku | backlog |

---

## Total SP: 55

| Epic | SP | Priority |
|---|---|---|
| E1 Scaffold | 4 | Must |
| E2 Data Layer | 15 | Must (PyPSA or fallback) |
| E3 Scoring Engine | 11 | Must |
| E4 Supply Mix | 7 | Must |
| E5 Map & UI | 12 | Must |
| E6 Integration | 6 | Must |

---

## 24h Critical Path

```
Hour 00–02  E1 scaffold + E2-T1 (Ember) + E2-T2 probe (PyPSA) — parallel
Hour 02–04  E2-T4 (OSM) + E2-T5 (NUTS2 merge) — decision: PyPSA or fallback
Hour 04–08  E3 scoring engine (all 6 tasks, some parallel)
Hour 08–12  E4 supply mix + E2-T6 economics
Hour 12–18  E5 map + UI (choropleth → filter → drill-down)
Hour 18–21  E5-T5 narrative + E6 integration tests
Hour 21–23  E6-T3 demo scenarios + polish
Hour 23–24  E6-T4 README + final smoke test
```

**Biggest risk:** E2-T2 (PyPSA-Eur). If pre-solved network download + parsing takes >2h, cut to fallback (E2-T3) immediately. Do not debug PyPSA past hour 2.

**Stretch (cut if behind):**
- Real-time re-scoring on slider change (use cached batch instead)
- CSV export
- Google Alphaearth layer (API-gated, likely inaccessible)
- IEA layer (reference only, integrate as static text in drill-down)

---

## Open Decisions

- [ ] PPA rate model: `spot × (1 - curtailment_discount)` or use published indicative rates by country?
- [ ] Map library: PyDeck (Mapbox token needed) vs Folium (no token, simpler) — Folium safer for 24h
- [ ] Deploy: Streamlit Cloud (free, needs GitHub push) or local demo only?
- [ ] Export: in-scope for PoC or cut?
