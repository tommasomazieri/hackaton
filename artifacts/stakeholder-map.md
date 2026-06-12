# Stakeholder Map — DC Siting Intelligence Tool

---

## Adoption Path

The sale runs through Jordan. There is no direct vendor-to-buyer path.

```
  [VENDOR] → convince Jordan first
                    │
                    Jordan pitches tool to CEO + CFO
                    │           │
                    CEO         CFO
                    (approves)  (co-approves + validates financial output)
                         │
                    Tool purchased → Jordan uses it
                         │
                    Tool output reviewed by:
                    ESG Officer · Infra PM · Legal
                         │
                    Output informs decision cleared by:
                    IC Partner · Board / LP
```

**Jordan is the gate.** If Jordan is not convinced, no pitch reaches CEO or CFO. Jordan must be won first — on time saving, output quality, and explainability — before they will champion the tool upward.

---

## Influence / Interest Grid

```
  INFLUENCE
     5 │  Board/LP      │  IC Partner
       │                │  CEO
     4 │                │  CFO · Jordan
       │                │
     3 │  ESG Officer   │
       │  Legal         │
     2 │                │  Infra PM
       │                │
     1 └────────────────┴──────────────
                LOW          HIGH
                          INTEREST
```

| Quadrant           | Stakeholders                              |
|--------------------|-------------------------------------------|
| **Manage Closely** | Jordan · CFO                              |
| **Keep Satisfied** | CEO · IC Partner · Board / LP             |
| **Keep Informed**  | ESG Officer · Infrastructure PM           |
| **Monitor**        | Legal / Regulatory Counsel                |

---

## Layer 1 — Main (Adoption Triad)

The three people who determine whether the tool gets bought and used.

---

### SH-001 — Jordan
**Sales role:** Champion — must be convinced first; pitches to CEO and CFO
**Quadrant:** Manage Closely (Influence 4 / Interest 5)

**Role:** Head of DC Development / Infrastructure Strategy Analyst / DC Investment Analyst. Owns the analysis. Presents directly to CEO. The tool adoption path runs entirely through Jordan — no Jordan buy-in, no sale.

**Needs from the tool:** Ranked EU zones with per-dimension scores, zone-level carbon data, supply mix (grid/PPA/on-site), and energy cost differential — in one structured output the CEO can act on and the CFO can plug into their model. No reformatting. Re-runnable instantly.

**Why Jordan must be won first:** Jordan runs the analysis. If the tool does not save them hours and produce IC-ready output, they will not advocate upward. CEO and CFO trust Jordan's recommendation of the tool — not a vendor pitch. Jordan is the credibility bridge.

**Approval trigger:** Tool returns ≥3 ranked sites in <30s citing auditable sources (PyPSA-Eur, Ember, OSM). One output serves both CEO narrative and CFO cost delta without extra work. Jordan can walk into the CEO meeting knowing CFO has already seen consistent numbers from the same output.

**Block trigger:** Carbon data country-averaged — cannot answer ESG Officer's zone-level questions. Output requires manual reformatting before the meeting. Jordan cannot explain the scoring methodology if the CEO asks. Too slow or brittle under IC deadline pressure.

---

### SH-002 — CEO / C-Suite
**Sales role:** Buyer — approves purchase after Jordan pitches; approves the siting decision the tool informs
**Quadrant:** Keep Satisfied (Influence 5 / Interest 3)

**Role:** Chief Executive Officer / Chief Strategy Officer / VP Infrastructure. Decision maker. Jordan presents to them — both the tool pitch and the eventual DC siting recommendation. Does not run the tool. Approves the budget.

**How Jordan pitches to them:** Jordan demos the output in <30s. The pitch is a capability investment: faster pre-feasibility, defensible IC memos, no more waiting weeks for a consultant. CEO approves when the time saving is obvious and Jordan + CFO are already aligned on the figures.

**Needs from the siting decision:** Clear winner with plain rationale. Carbon compliance as gCO₂/kWh vs. stated RE100 / net-zero target. Cost advantage in €, not rank. Top risk bounded as a range. Jordan and CFO walk in already aligned.

**Approval trigger:** Jordan demo shows IC-presentable output in <30s. Speed advantage vs. consultant process is explicit. CFO has already seen the cost-differential section and is aligned. ESG narrative is citable against the stated target.

**Block trigger:** Output looks like a dashboard they won't read. Jordan and CFO present different figures. No clear winner surfaced — trade-offs buried. Carbon compliance stated as a colour, not a number.

---

### SH-003 — CFO
**Sales role:** Buyer — co-approves purchase with CEO; validates financial output from the tool
**Quadrant:** Manage Closely (Influence 4 / Interest 4)

**Role:** Chief Financial Officer / IC Member / Head of Real Estate Finance. Pulled in by Jordan — not a direct user. Advises CEO on whether the financial case holds. Co-approves the purchase when Jordan shows the cost-differential output is directly pluggable into their model.

**How Jordan pitches to them:** Jordan shows the cost-differential section: "this is what you currently ask me to calculate manually — now it's in every query, already in the format you plug into the model." CFO approves when the numbers are pluggable and correctly scoped as differential only.

**Needs from the siting decision:** Energy cost differential in €/MWh annualised at target MW. NPV of location choice over 15–25 yr. PPA discount vs. day-ahead spot in €/MWh — quantified, not flagged. Carbon cost delta as €/yr. Congestion risk as ±€/MWh opex variance range.

**Approval trigger:** Location choice expressed as a € value over asset life. PPA discount quantified and sourced. Carbon delta in €/yr, pluggable directly. Output explicitly scoped as additive differential — no total cost claimed. Figures consistent with Jordan's narrative.

**Block trigger:** PPA flagged but not priced. Congestion risk labelled, not numbered. Tool did not eliminate the coordination step — CFO still has to call Jordan to get the number they need.

---

## Layer 2 — Peripheral (Output Validators)

These stakeholders do not approve the tool purchase. They review specific dimensions of the tool's output after purchase and can block the siting decision if their dimension is not satisfied. Win them as internal validators — they pre-clear objections before IC.

---

### SH-004 — ESG Officer
**Sales role:** Output validator — reviews carbon output; growing veto power on siting decision
**Quadrant:** Keep Informed (Influence 3 / Interest 5)

**Role:** Owns Scope 2 carbon commitments, LP ESG reporting, RE100/SBTi targets. Does not approve the tool purchase. Can block the siting decision if carbon claims are not audit-ready for LP reporting.

**Needs from the siting output:** Carbon intensity per site in gCO₂/kWh — Ember, datestamped, zone-level not country-average. PPA / Guarantee of Origin pathway for Scope 2 matching. Curtailment-zone PPA with physical additionality argument. Audit trail for LP carbon reporting.

**Approval trigger:** Carbon below LP mandate ceiling. Ember data cited with date. Zone-level granularity. PPA with Guarantee of Origin in-region. Supply mix shows credible 100% renewable matching with additionality.

**Block trigger:** PPA in different bidding zone — greenwashing risk. Carbon data country-averaged and not audit-ready. No citation trail in output.

---

### SH-005 — Infrastructure PM
**Sales role:** Output validator — executes against tool output; flags if connectivity / substation data is unreliable
**Quadrant:** Keep Informed (Influence 2 / Interest 4)

**Role:** Executes the build post-decision. Focused on delivery risk: grid connection timelines, substation capacity, land title, planning probability. No influence over purchase or siting decision.

**Needs from the siting output:** Substation density and HV grid connection capacity near shortlisted sites. Fiber backhaul availability. Land parcel availability at required footprint. Realistic grid connection timelines by region.

**Approval trigger:** OSM substation data reflects actual HV capacity. Connectivity distinguishes fiber-dense from greenfield. Congestion score flags single-point-of-failure topology. Land availability tied to footprint input.

**Block trigger:** Tool scores zone high but TSO grid connection backlog is 24+ months. Substation density from OSM outdated. Land availability is a regional proxy — actual parcel not confirmed.

---

### SH-006 — Legal / Regulatory Counsel
**Sales role:** Output validator — reviews jurisdiction flags; can escalate risk opinion to IC
**Quadrant:** Monitor (Influence 3 / Interest 2)

**Role:** Reviews regulatory exposure in target jurisdictions: DC permitting law, grid connection contracts, PPA enforceability, data residency. Can delay or block siting decisions through formal risk opinion to IC.

**Needs from the siting output:** Jurisdiction-level regulatory flag per shortlisted site. PPA structure locally enforceable. Data residency / sovereignty requirements per country. Grid connection commitment type — formally reserved vs. indicative.

**Approval trigger:** No active permitting moratorium or grid freeze in shortlisted zones. PPA structure locally enforceable. Data residency requirements identified. Carbon claims audit-ready.

**Block trigger:** Active grid connection moratoriums in shortlisted zones. PPA structure unenforceable locally. Tool implies regulatory clean without flagging jurisdiction-specific constraints.

---

## Layer 3 — Institutional / Macro (Constraint-Setters)

Never interact with the tool. Set the envelope — carbon ceiling, geography scope, return hurdle, ESG covenants — that Jordan's output must satisfy. The tool's hard filters enforce their constraints automatically. They check for compliance with their mandate, not site quality.

---

### SH-007 — Investment Committee / IC Partner
**Sales role:** Mandate-setter — defines analytical rigour standard Jordan's output must clear; never sees the tool
**Quadrant:** Keep Satisfied (Influence 5 / Interest 2)

**Role:** Formal capital approval body. In PE/infrastructure fund: IC Partner who chairs deal approval. In corporate: exec committee equivalent. Reads Jordan's IC memo — produced using the tool. Sets the bar.

**Needs from the decision:** IRR-accretive site selection with quantified downside. Methodology reproducible and citable. Carbon consistent with LP mandate. Deal timeline competitive — not lost to competitors during analysis.

**Approval trigger:** NPV of location choice positive with sensitivity range. Carbon within LP ceiling, cited. Jordan and CFO memo sections consistent — same figures. Methodology defensible under IC questioning.

**Block trigger:** Methodology undocumented. Carbon exposure not quantified vs. LP mandate. Jordan and CFO inconsistent. Competitor transacted during analysis delay.

---

### SH-008 — Board / LP
**Sales role:** Constraint-setter — their ESG covenants and geography mandates define what the tool's hard filters must enforce
**Quadrant:** Keep Satisfied (Influence 5 / Interest 1)

**Role:** Board members and Limited Partners. Set the mandate constraints the entire decision must satisfy: carbon ceiling, geography scope, minimum return hurdle, ESG covenants. Never interact with the tool. Shape the filter Jordan must satisfy.

**Needs from the decision:** Confirmation deal satisfies fund mandate: IRR above hurdle, carbon within LP ESG covenant, geography within approved scope. One-paragraph board memo. ESG compliance documented for LP audit trail.

**Approval trigger:** Return hurdle met. Carbon within LP ESG covenant — documented with source. Geography in scope. IC endorsed. Board memo is one clear paragraph.

**Block trigger:** Carbon breach of LP ESG covenant. Geography outside approved scope. Material risk not disclosed early — surfaces as a surprise at board level.

---

## Pitch Implications

**The sale is a two-step relay, not a direct pitch.**
Convince Jordan that the tool saves them hours and produces IC-ready output. Jordan then sells it upward. CEO approves on capability + speed advantage. CFO approves on financial output quality. Neither CEO nor CFO will evaluate the tool on their own — they rely on Jordan's endorsement.

**The tool must serve two masters simultaneously.**
Jordan uses one query. CEO reads the ranked winner and ESG story. CFO reads the cost differential and NPV delta. If the output structure forces Jordan to reformat for either audience — the sale fails. The tool's value prop is the unified output, not the analysis.

**Peripheral validators are pre-clearance infrastructure.**
ESG Officer, Infra PM, and Legal do not buy — but they can block the siting decision downstream. Win them by making their dimension explicit, cited, and auditable in every output. ESG gets Ember datestamped zone-level data. Infra PM gets substation and connectivity with source. Legal gets jurisdiction flags. They become advocates, not reviewers.

**Institutional stakeholders set the hard filter, not the analysis.**
Board/LP and IC never see the tool. Their constraints — carbon ceiling, geography, return hurdle — must be enforced automatically by the tool's hard filters. When Jordan's output lands on the IC desk, it must already be compliant with the mandate. The tool's explainability layer is what makes that demonstrable.
