# Persona: DC Infrastructure Decision-Maker

> Composite of: infrastructure strategy analyst (hyperscaler), investment analyst (infra fund), head of DC development (colo operator). Common thread: all are accountable for finding where to put capacity to serve a known market demand.

---

## Profile

**Archetype name:** Jordan  
**Role titles (any of):** Infrastructure Strategy Analyst · DC Investment Analyst · Head of Data Center Development  
**Organization types:** Hyperscaler / large tech · Infrastructure fund · Colocation operator / DC developer  
**Seniority:** Mid-to-senior individual contributor or team lead. Owns the analysis, presents to exec.  
**Geography:** EU-focused mandate or global with EU expansion on the roadmap  
**Team size:** 2–8 people. No dedicated internal tooling team.

---

## The Core Problem

Jordan's organization has **a known compute demand to serve** — a market commitment, a fund thesis, a colo pipeline. The question is not *whether* to build but **where in Europe** to build to meet that demand most efficiently.

The capacity requirement (MW) is fixed by the business. Everything else — cost, carbon, grid reliability — is optimized within that constraint.

---

## Primary Goal

> "I need to place X MW of capacity in Europe. Tell me which region gives me the best combination of energy cost, carbon profile, and grid reliability — and show me why."

- Capacity is the **primary input** (non-negotiable, set by business demand)
- Cost is the **primary optimization target** (hits P&L or fund returns directly)
- Carbon is a **hard constraint** (RE100 / ESG policy / investor mandate sets ceiling)
- Grid reliability / connectivity is a **risk filter** (eliminates unstable or isolated zones)

---

## Secondary Goals

- Build a defensible recommendation to present to IC / CTO / board
- Understand supply mix options (grid vs PPA vs on-site) and their cost implications
- Identify PPA opportunities where curtailment creates discount
- Have output that a CFO can read without a technical briefing

---

## Current Pain (Before Tool)

- Assembles data manually: ENTSO-E prices in one tab, Ember carbon in another, OSM maps in a third
- No unified EU view — has to stitch country-level data and guess at regional variation
- Supply mix analysis done in Excel, rebuilt from scratch each deal
- Carbon data is stale or country-averaged — no zone-level granularity
- Presenting to IC takes days of formatting; the underlying analysis is a spreadsheet
- No way to quickly re-run for a different MW or carbon ceiling

---

## Frustrations

- "I know Poland is cheap but I don't know if the grid can handle 150 MW without congestion"
- "Our ESG team says we need <200 gCO₂/kWh — I have no idea which EU zones qualify"
- "Every time the load estimate changes I have to redo the whole analysis"
- "The IC wants to compare 3 sites side by side and I'm copying numbers between slides"

---

## Tools Used Today

- Excel / Google Sheets (primary analysis)
- ENTSO-E Transparency Platform (manual data pulls)
- Ember Climate website (country carbon intensity)
- Google Maps + OSM (qualitative substation/fiber check)
- PowerPoint (presentation)
- Occasional consultant report (expensive, static, not re-runnable)

---

## Decision Criteria for Buying This Tool

| Factor | Weight |
|---|---|
| Saves significant manual analysis time | High |
| Output is boardroom-ready without reformatting | High |
| Carbon data is current and zone-level (not country average) | High |
| Can re-run instantly for different MW / carbon scenarios | High |
| Shows supply mix and LCOE, not just site ranking | Medium |
| Trusted data sources (PyPSA, Ember, OSM) | Medium |
| Per-query pricing (no annual commitment) | Medium |

---

## Buyer (who approves the purchase)

**Title:** Investment Committee member · CTO · CFO · Head of Real Estate  
**What they care about:** Is the recommendation defensible? What's the energy cost? Are we carbon-compliant?  
**What they read:** The CFO-legible 3-sentence narrative + the supply mix cost breakdown. Not the choropleth.

---

## Key Quote

> "I need to place 100 MW somewhere in Europe by Q3. Give me the top 3 zones with the numbers, show me the power cost and carbon, and tell me if there's a PPA angle. I'll take it to IC on Friday."
