# Stakeholder Map — DC Siting Intelligence Tool

## Influence / Interest Grid

```
INFLUENCE
   5 │ Board/LP          │ IC Partner
     │ Legal/Compliance  │ CFO/CIO
     │                   │ Head of DC Dev
   3 │                   │ ESG Officer
     │                   │
   1 │                   │ Infrastructure PM
     └───────────────────┴──────────────────
              LOW            HIGH
                          INTEREST
```

Formal quadrant placement:

| Quadrant           | Stakeholders                                      |
|--------------------|---------------------------------------------------|
| **Manage Closely** | IC Partner · CFO/CIO · Head of DC Development    |
| **Keep Satisfied** | Board/LP · Legal/Compliance                       |
| **Keep Informed**  | ESG Officer · Infrastructure PM                  |
| **Monitor**        | *(none at current scope)*                         |

---

## Stakeholder Profiles

### SH-001 — IC Partner
**Quadrant:** Manage Closely (Influence 5 / Interest 4)

**Role:** Ultimate deal approver on Investment Committee. Signs capital allocation for new DC builds. Reads deal memos — not dashboards.

**Needs from DC siting:** IRR-accretive site selection with quantified downside. Carbon narrative for LP reporting. Proof the team ran a rigorous, repeatable process — not consultant intuition. Fast enough to not lose competitive deals.

**Approval trigger:** NPV positive with sensitivity bounds. Carbon intensity below LP mandate ceiling. Site ranked #1 vs peer regions on cost-adjusted basis. Supply mix hedges long-term energy price exposure.

**Block trigger:** Unquantified regulatory or grid-connection risk. Carbon liability in jurisdiction. Black-box methodology with no defensible reasoning. Competitor already locked preferred site.

---

### SH-002 — CFO / CIO
**Quadrant:** Manage Closely (Influence 4 / Interest 5)

**Role:** Owns capital budget and major capex sign-off. Also owns the OpEx envelope for energy — the largest operating line in a DC. May be same person or joint sign-off depending on firm structure.

**Needs from DC siting:** Precise LCOE per site with sensitivity range. Grid vs PPA vs on-site mix that reduces energy price volatility. Capex by region benchmarked against market. Annual cost delta between top 3 sites in a CFO-legible table.

**Approval trigger:** NPV positive within budget envelope. Blended LCOE competitive vs market benchmark. PPA option available to hedge spot exposure. Sensitivity shows NPV survives +20% energy cost shock.

**Block trigger:** Energy cost assumptions unsourced. No PPA pathway for volatile markets. Capex estimate too wide. OpEx blowout risk from grid congestion not quantified.

---

### SH-003 — Head of DC Development *(Jordan's manager)*
**Quadrant:** Manage Closely (Influence 4 / Interest 5)

**Role:** Accountable for pre-feasibility process quality and IC deck credibility. Owns the siting mandate top-down. Must present to IC and field teams simultaneously — technical and commercial credibility both required.

**Needs from DC siting:** Defensible shortlist of ≥3 sites with per-dimension scores they can interrogate. Supply mix per site. Tool fast enough to iterate during IC prep. Audit trail for IC Q&A without rebuilding the analysis.

**Approval trigger:** Tool returns ranked sites in <30s with explainable scores. Supply mix cites real data. Output is IC-presentable without manual reformatting. Jordan's team operates it independently.

**Block trigger:** Data reliability concerns (are Ember/PyPSA numbers current?). Tool too complex under time pressure. No methodology section for IC Q&A. Results change unpredictably between runs.

---

### SH-004 — ESG Officer
**Quadrant:** Keep Informed (Influence 3 / Interest 5)

**Role:** Owns Scope 2 carbon commitments, LP ESG reporting, and RE100/SBTi targets. Reviews major infrastructure decisions for carbon exposure. Growing veto power as LP mandates tighten.

**Needs from DC siting:** Auditable carbon intensity per site (gCO₂/kWh). Clear PPA / Guarantee of Origin pathway to net-zero Scope 2. Curtailment-zone PPA opportunity flagged — generator additionality story matters for Scope 2 claims.

**Approval trigger:** Site carbon intensity below LP mandate ceiling. PPA with Guarantee of Origin available in-region. Supply mix shows credible path to 100% renewable matching. Carbon data source cited and methodology documented.

**Block trigger:** Site above threshold with no viable PPA alternative. Greenwashing risk — PPA supplier in different bidding zone, no physical additionality. Carbon data stale or unsourced.

---

### SH-005 — Board / LP
**Quadrant:** Keep Satisfied (Influence 5 / Interest 2)

**Role:** Board members and Limited Partners providing capital. Shape mandate constraints (carbon ceiling, geography, return hurdle) that filter the decision space upstream. Receive quarterly reporting, not deal dashboards.

**Needs from DC siting:** Confirmation the deal fits fund mandate: IRR above hurdle, carbon within LP ceiling, geography in scope. One-paragraph narrative for board memo. Not interested in methodology — outcome confidence only.

**Approval trigger:** Deal hits IRR hurdle. Carbon within LP ESG covenant. Site in approved geography. IC Partner already endorsed.

**Block trigger:** Carbon exposure violating LP ESG covenant. Jurisdiction outside approved geographies. Deal speed too slow — LP optionality window closes. Regulatory risk not surfaced at memo stage.

---

### SH-006 — Infrastructure PM
**Quadrant:** Keep Informed (Influence 2 / Interest 5)

**Role:** Executes the build once site is selected. Focused on delivery risk: grid connection timelines, substation capacity, land title, planning probability. Highly interested in operational data; low organizational influence over siting decision.

**Needs from DC siting:** Substation density and grid connection capacity per site. Fiber availability for backhaul. Land parcel availability at required footprint. Realistic grid connection lead times — not averages, actual bottleneck data.

**Approval trigger:** OSM substation count confirms HV capacity within 5km. Land footprint achievable in zone. Connectivity score above threshold. Congestion risk flagged with mitigation options.

**Block trigger:** Grid connection timeline >24 months not reflected in score. Substation density high but single-point-of-failure topology. Land availability from sparse data — real parcel not confirmed.

---

### SH-007 — Legal / Compliance
**Quadrant:** Keep Satisfied (Influence 4 / Interest 2)

**Role:** Reviews regulatory exposure in target jurisdictions: planning law, grid connection contracts, PPA enforceability, data residency for DC operations. Can escalate risk opinions to IC and delay or block transactions.

**Needs from DC siting:** Jurisdiction-level regulatory flag per shortlisted site. PPA structure compatible with local law. Data residency / sovereignty requirements. Grid connection commitment type — formally reserved vs indicative score.

**Approval trigger:** No active permitting moratorium in jurisdiction. PPA counterparty creditworthy, contract enforceable locally. Grid connection formally committed. Data residency requirements met.

**Block trigger:** Jurisdictions with active grid connection moratoriums (e.g., Ireland 2022-era constraints). PPA structure unenforceable locally. Carbon offset claims not audit-ready. Unresolved GDPR / data sovereignty exposure in DC operating model.

---

## Narrative: Pitch Implications

The stakeholder map reveals three things that should shape pitch framing:

**1. The IC Partner is the gatekeeper, but the CFO/Head of DC Dev are the daily users.**
Our pitch must clear IC Partner scrutiny (methodology rigor, NPV defensibility, LP carbon narrative) while being genuinely useful to the people who run the analysis (Head of DC Dev, Jordan). These are different audiences — the pitch deck speaks to IC; the demo speaks to Jordan's team.

**2. Board/LP and Legal operate as constraint-setters, not evaluators.**
They don't evaluate site quality — they set the envelope (carbon ceiling, geography, return hurdle, regulatory clean). The tool should surface compliance with those constraints early in results (carbon ceiling pass/fail, jurisdiction flag) so these stakeholders are satisfied without needing to engage with methodology.

**3. ESG Officer and Infrastructure PM are high-interest validators — win them and they become internal champions.**
ESG Officer needs to trust the carbon data provenance (Ember citation, Guarantee of Origin pathway). Infrastructure PM needs to trust the connectivity scores reflect real substation data. Winning both converts them from reviewers to advocates who pre-clear objections before IC.

**Key insight for product:** The tool's explainability requirement — citing Ember, PyPSA/GridSFM, and OSM data sources per dimension — is not just a technical constraint. It is the primary mechanism by which Board/LP mandates are confirmed, Legal risk flags are surfaced, and ESG claims are made audit-ready. Explainability IS the stakeholder management layer.
