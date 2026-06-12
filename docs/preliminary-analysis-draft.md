> [!WARNING]
> **DRAFT — NOT ACCEPTED**
> This document is a preliminary synthesis of E0 artifacts. It is **not foundational, not imperative, and must not be used as a basis for implementation decisions** until explicitly reviewed and accepted by the team. Content may be incomplete, incorrect, or superseded.

---

# Preliminary Analysis — DC Siting Intelligence Tool

## Who Buys, Who Uses, What Kills the Deal

- **Jordan** = the one user. Adoption path runs through them. If tool doesn't save hours + produce IC-ready output, no sale.
- **CFO** = co-buyer. Needs only **differentials** (€/MWh, NPV delta, PPA discount vs. spot). Never total cost — that's their model's job.
- **CEO** = approves when Jordan + CFO walk in aligned with same numbers. No grid physics. Plain rationale, clear winner.
- **IC Partner** = mandate-setter with veto. Blocks on: undocumented methodology, inconsistent Jordan/CFO numbers, competitor transacted during delay.

**Hard blockers** (any one kills adoption):
- Carbon data country-averaged — ESG Officer blocks siting decision
- PPA flagged but not priced — CFO can't act
- Slow or not re-runnable — breaks the "Friday CEO meeting" use case
- Output requires reformatting before CEO meeting

---

## Quantified Pain = Pitch Numbers

| Pain | Number |
|---|---|
| Current process cost | €18k–€30k in-house; €40–120k external per deal |
| Decision risk (wrong site energy cost) | €50M–€1.7B over 20yr for 50–200 MW |
| EU wholesale spread | €72/MWh Nordic vs Italy — masks real location value |
| Re-run cost | 1–2 analyst days (€600–€850/day) per scenario change |
| Grid queue context | 1,700+ GW queued, 5–10yr connection timelines |

---

## Granularity — Two Independent Axes

Granularity is not one thing. Spatial and temporal are separate concerns and must be declared explicitly for every data layer.

### Spatial Granularity

| Level | Zones | Verdict |
|---|---|---|
| Country | ~27 | Too coarse — exact pain Jordan has today |
| NUTS2 | ~240 | Previously assumed correct — **under review** |
| **NUTS3** | ~1,100 | **Preferred target** — actual siting decision happens at this scale (e.g. "Munich metro" vs "rural Upper Bavaria") |

**NUTS3 is the correct spatial target.** NUTS2 zones are too large to distinguish intra-region energy price, carbon, or grid headroom differentials that actually determine which site wins.

**Constraint:** Several upstream sources (Eurostat energy stats, Ember country pro-rating) only publish at NUTS2 or country level. Those layers require interpolation downward to NUTS3 — document this explicitly in every affected data layer; do not silently promote country data to NUTS3 precision.

### Temporal Granularity

Each data source has its own cadence. Mixing them without declaring resolution is a silent error source.

| Source | Cadence | Lag |
|---|---|---|
| Ember | Monthly / annual | 1–3 months |
| PyPSA-Eur | Hourly (8,760h/yr pre-solved) | Snapshot vintage |
| ENTSO-E | Hourly day-ahead prices | ~1 day |
| OSM | Static snapshot | Unknown drift |
| AlphaEarth | Annual (2017–2024) | ~1 year |

**Rule:** every zone score must be stamped with the spatial resolution AND the temporal resolution of its weakest input. A score built on annual Ember data is not an hourly score — even if PyPSA contributed hourly congestion data.

---

## Data Design Insights

**Critical architecture constraint:** 3-tier screening required — national filter → nodal validation → micro-siting for top 5 only. Running AlphaEarth/PyPSA across all EU NUTS3 in real-time is infeasible.

- **Ember**: national average only — flags ±10–30% local variance; acceptable for compliance reporting, must caveat explicitly; interpolate to NUTS3 with documented uncertainty
- **PyPSA-Eur**: the congestion/headroom signal — hourly nodal simulation expensive; pre-solve and cache, don't run live
- **OSM**: static snapshot; HV substation presence ≠ available capacity; useful for connectivity proxy
- **GridSFM**: parallel probe to PyPSA — EU topology construction is the risk, not the model itself
- **AlphaEarth**: 64-dim embeddings at 10m / annual — micro-siting layer only (land suitability, terrain, cooling proximity); not a primary scoring dimension; access via `GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL` on Earth Engine (free, CC-BY 4.0) or `gs://alphaearth_foundations` on GCS
- **Scope 2 honesty**: national intensity acceptable for LP reporting; product must flag ±15% local variance or ESG Officer blocks the siting decision

---

## Dev Critical Path

**Unblock order — nothing else moves without these:**

1. `TASK-007` — Python project init (scaffolds everything)
2. `TASK-012` PyPSA probe **and** `TASK-013` GridSFM probe — run parallel, 2h time-box each. If both fail → `TASK-014` ENTSO-E fallback. Single biggest technical risk.
3. `TASK-016` — NUTS3 GeoDataFrame master merge (all scoring depends on this)
4. `TASK-019` — scoring schema config (gates all 5 dimension tasks)

**Max parallelism available:**
- `TASK-008` + `TASK-009` (FastAPI + Streamlit skeletons) — start immediately alongside data work
- `TASK-011` + `TASK-012/013` (Ember + grid data) — two independent data tracks
- `TASK-015` + `TASK-017` + `TASK-018` (OSM + economics constants + land cost) — all parallel after project init
- `TASK-020–024` (5 dimension scores) — fully parallel once NUTS3 merge done

---

## Solution Design Hints

1. **Cache everything pre-query.** NUTS3 master dataset computed once, stored as GeoParquet. Query latency must come from scoring (milliseconds), not data fetch (minutes).

2. **NUTS3 is the right spatial granularity.** Country averages are the exact pain Jordan has today. NUTS3 + PyPSA nodal mapping = the differentiator. Where upstream data is only NUTS2/country, interpolate and flag uncertainty explicitly — never silently promote resolution.

3. **Single output, two readers.** The JSON `SiteResult` must carry both the CEO-legible narrative AND the CFO-pluggable €/MWh differential in the same object. Jordan does zero reformatting.

4. **Triple-signal (A+B+C → STRONG/CAUTION/AGAINST)** is the IC-defense mechanism. Jordan can say "all three methods agree" under live challenge. Must be citable, not decorative.

5. **PyPSA/GridSFM failure is not a failure mode — it's expected.** Design the ENTSO-E fallback from day 1 so congestion scoring degrades gracefully.

6. **Demo scenarios (TASK-044) are insurance, not an afterthought.** If PyPSA takes 45s during a live demo, the hardcoded Polish/Nordic/Iberian scenarios are what judges see.

**Recommended start sequence:** `TASK-007` (init) → parallel `TASK-008/009/011/012/013` → merge + scoring.
