# DC Siting Intelligence Tool — User Personas

## Decision Structure

```
CEO  ←─── makes the go/no-go
 │
 ├── Jordan  (technical advisor — our direct user, runs the tool)
 └── CFO     (financial advisor — pulled in by Jordan, advises CEO on cost case)
```

The tool is used by Jordan. Its output is not a final presentation — it is structured narrative material. Jordan and the CFO each take the parts relevant to them and walk into the CEO meeting already aligned, because both read from the same source. The CEO hears one coherent story, not two advisors who coordinated overnight.

---

## Jordan — Technical Advisor & Our Direct User

**Composite of:** Infrastructure Strategy Analyst · DC Investment Analyst · Head of DC Development

Jordan is the CEO's technical point of contact on site selection. The mandate: take a known MW requirement, a carbon ceiling, and a cost priority — and return a ranked shortlist the CEO can act on and the CFO can stress-test financially.

The tool collapses weeks of fragmented manual work into one query. The output is structured so the technical story (ranked sites, grid headroom, carbon compliance, supply mix) and the financial story (energy cost delta, PPA discount, carbon cost gap) live in the same document. Jordan doesn't need to rebuild for the CFO. The CFO doesn't need to ask Jordan to reformat. The narrative assembles itself.

**Jordan's quote:**
> "I need to place 100 MW somewhere in Europe by Q3. Give me the top 3 zones — the technical case, the carbon numbers, and the cost delta between options. I want to walk into the CEO meeting with the CFO already on board because they've seen the same figures."

### Goals
- Screen 10+ EU countries in hours, not weeks
- Produce output the CFO can read without Jordan present to interpret it
- Give the CEO a recommendation where the technical and financial case are already aligned
- Identify PPA opportunities in high-curtailment zones
- Re-run instantly when load or carbon constraint changes

### What Makes Jordan Buy
| Factor | Weight |
|---|---|
| Saves hours of manual analysis | High |
| Output structured so CFO and Jordan build the same narrative without coordinating | High |
| Zone-level carbon data, not country average | High |
| Instant re-run for different MW / carbon scenarios | High |
| Energy cost differential per site, not just ranking | Medium |
| Citable sources (PyPSA-Eur, Ember, OSM) | Medium |
| Per-query pricing, no annual lock-in | Medium |

---

## CEO / C-Suite — The Decision Maker

**Composite of:** CEO · Chief Strategy Officer · VP Infrastructure

The CEO is the person Jordan is ultimately working for. They receive technical input from Jordan and financial input from the CFO — and they make the call.

They don't read the analysis. They receive a coherent narrative: which site, why technically, what it costs versus the alternatives, whether ESG commitments are met. That narrative is not built in the CEO meeting — it's built beforehand, by Jordan and the CFO working from the same tool output.

What the CEO needs from our tool — indirectly, via Jordan and CFO — is output that is already structured as a story: a clear winner, a plain rationale, quantified trade-offs, bounded risks. Not raw data. Not a ranked table with footnotes. Prose and numbers that connect.

**CEO's quote:**
> "I don't need to understand the grid. When Jordan and the CFO walk in already aligned — same site, same numbers, same carbon story — that's when I can make the call."

### What They Need the Narrative to Cover
- Which site and why — one sentence, not a trade-off list
- Carbon compliance stated as a number vs. the stated policy target
- Cost advantage of the chosen site over alternatives — in €, not in rank
- Top risk per site, bounded: not "congestion risk" but "±X €/MWh opex range"

### What Makes Them Approve
- Jordan and CFO present with the same figures — no reconciliation needed in the room
- ESG story is citable — gCO₂/kWh vs. RE100 target, explicitly
- Financial case is expressed as a decision delta, not a full project model
- Risk is surfaced with a number, not a colour

---

## CFO — Financial Advisor to the CEO

**Composite of:** CFO · Investment Committee Member · Head of Real Estate Finance

The CFO is pulled in by Jordan, not a direct user of the tool. Their role is to advise the CEO on whether the financial case for the recommended site holds. They already have the financial model — capex, opex, depreciation, financing. What they are missing is the one input our tool provides: **the energy cost differential between candidate sites**.

All else equal — same DC, same MW, same build — which location is cheaper to run over 20 years, and by how much? That is the only question we answer. We do not replace the financial model. We give the CFO the delta they plug into it.

They will ask: if we choose Site A over Site B, what does that decision cost or save in energy over the asset life? They want the PPA discount expressed as €/MWh, not flagged as an opportunity. They want carbon cost exposure as a € per year delta between sites, not a gCO₂/kWh number they have to convert themselves. They want congestion risk as an opex variance range, not a traffic-light label.

**CFO's quote:**
> "I have the build cost. I don't need you to model the whole project. Tell me: if we go to Site A instead of Site B, what does that decision cost or save us in energy over 20 years? Give me the delta. I'll plug it into the model."

### Key Differential KPIs (what the tool must surface)
| KPI | What we provide |
|---|---|
| Energy cost differential | €/MWh delta between sites × annual MWh = annual € savings/cost |
| NPV of location choice | PV of energy cost difference over asset life (15–25 yr, given discount rate) |
| PPA discount vs. spot | Curtailment-zone PPA price minus day-ahead spot — quantified in €/MWh |
| Carbon cost delta | (intensity_A − intensity_B) × EU ETS price × annual MWh = €/yr exposure gap |
| Congestion opex variance | Grid congestion risk as ±€/MWh range — not high/medium/low |

> **Scope boundary:** We provide differential figures above a standard DC baseline. Total project NPV, construction cost, financing, and depreciation are the CFO's model — not ours.

### What Makes Them Approve
- Location choice expressed as a € value, not just a rank
- PPA discount quantified and sourced, not flagged
- Carbon delta in €/yr — pluggable directly into the model
- Congestion risk as a number they can stress-test
- Output explicitly scoped as additive differential — no total cost claimed

---

## Persona Summary Table

| | Jordan | CEO | CFO |
|---|---|---|---|
| **Org role** | Technical advisor + direct user | Decision maker | Financial advisor to CEO |
| **Relationship to tool** | Runs it | Reads Jordan's output | Pulled in by Jordan — reads cost delta |
| **Reads** | Full scored output + supply mix | Ranked winner + ESG narrative + CFO sign-off | Energy cost differential + NPV of location choice |
| **Blocked by** | Fragmented data sources, no zone-level intelligence, no re-run | Jordan and CFO not aligned on same numbers | Unpriced PPA, congestion risk not quantified |
| **Pays for** | Time saved on analysis | Decision confidence, board defensibility | Financial defensibility of location choice |
| **Key metric** | Hours saved per site screen | gCO₂/kWh vs. policy target, strategic fit | €/MWh delta, NPV of Site A vs B, €/yr carbon cost gap |
