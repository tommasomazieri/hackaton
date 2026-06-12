# Jobs-To-Be-Done: DC Siting Intelligence Tool

**Personas:** Jordan (user), CFO / IC Member (buyer), CEO (decision-maker)  
**Grounded in:** AS-IS journey stages S1–S9

---

## What this tool actually does — and does not do

**This is a differential, comparative analysis. Not an absolute cost model.**

Every data center in Europe has roughly the same steel, concrete, server hardware, and cooling capex. What differs by location is: the energy price at that zone, the carbon intensity of that grid, the congestion headroom, the connectivity density, the land cost. Those spot-specific variables are what we score.

The output is a ranked comparison: *"Site A beats Site B because its energy price is €28/MWh lower, its carbon intensity is 60 gCO₂/kWh cleaner, and its grid congestion risk is lower."*

We do not model total build cost. We do not model total operating cost. We output the **delta** — the location-specific variables that change by site. The CFO already has a financial model. They need us to fill in the location-specific inputs, not replace their model.

---

## JTBD-001 — Jordan · Functional
### Compare EU zones on the variables that actually differ by location

> **When** I need to compare EU locations against each other on the site-specific variables — energy price, carbon intensity, grid headroom, connectivity — and today I face 1–2 days on ENTSO-E plus a half-day on Ember producing country averages that mask the zone-level differentials that determine which site is actually better —  
> **I want** a single query that pulls the spot-specific value for each dimension at each EU NUTS2 zone and ranks zones by how they compare against each other —  
> **so I can** see which zones are comparatively better or worse on the variables that vary by location, in hours instead of weeks.

**Validates:** cost · carbon · congestion · connectivity  
**Pain anchor:** Country-level averages mask zone differentials worth up to €72/MWh energy price spread and 50–100 gCO₂/kWh carbon spread across EU — the entire signal is lost before analysis starts.

---

## JTBD-002 — Jordan · Emotional
### Back the ranking with spot-specific differentials, not judgment

> **When** I have manually ranked sites with arbitrary weights and no audit trail, and I must present to an investment committee who may ask why Site A ranks above Site B —  
> **I want** every ranking position backed by the actual spot-specific differential that drove it: "Site A ranks above Site B because its energy price is €28/MWh lower and its carbon intensity is 60 gCO₂/kWh cleaner" — citing traceable sources (PyPSA-Eur, Ember, OSM) —  
> **so I can** defend the ranking under live IC challenge with numbers, not judgment, and not have the recommendation sent back for rework.

**Validates:** cost · carbon · congestion · connectivity · land  
**Pain anchor:** IC deferral adds 1–3 analyst days (€600–€1,700) and a 2-week delay; worst case restarts full analysis from S2.

---

## JTBD-003 — CFO / IC Member · Financial
### Give me the location-specific deltas to plug into our model

> **When** Jordan gives me a ranked shortlist but I need to know what choosing Site A over Site B is actually worth — the energy price differential, the carbon cost differential, the PPA discount at this zone versus day-ahead spot —  
> **I want** spot-specific differentials expressed as €/MWh per site: energy price gap versus EU average, PPA discount at this zone, carbon intensity gap between top candidates — all stated at our target MW —  
> **so I can** quantify the financial value of choosing one location over another from the site-specific variables alone, plug the deltas into our existing DCF model, and give the CEO a grounded recommendation. We already have the build cost. We need what changes by location.

**Validates:** cost (LCOE / supply mix differentials)  
**Pain anchor:** CFO quote: *"I have the build cost. Tell me: if we go to Site A instead of Site B, what does that decision cost or save us in energy over 20 years? Give me the delta."* PPA discount structurally non-public (Pexapark 2026) — without zone-level differential, IC cannot act on a flag.

---

## JTBD-004 — CEO · Social / Decision
### One ranked winner — which location wins on the variables that differ

> **When** my team brings me a site comparison where trade-offs are buried in an appendix and there is no clear winner —  
> **I want** one ranked recommendation that states plainly how the top site differs from the alternatives — cheaper energy, cleaner grid, less congestion risk — without requiring me to understand grid physics —  
> **so I can** make the go/no-go call on which location wins on the site-specific variables, walk into the board with a defensible trade-off rationale, and know that Jordan and the CFO are citing the same differential numbers.

**Validates:** carbon · cost  
**Pain anchor:** Current alternative — 80-page consultant report (€40k–€120k, static) or misaligned CEO deck + CFO Excel. CEO quote: *"I don't need to understand the grid. I need to know which country we're going into and whether we'll be able to say we're running on clean energy."*

---

## Summary

| JTBD | Persona | Type | Journey stages | Dimensions |
|---|---|---|---|---|
| 001 | Jordan | Functional | S2 · S3 · S5 | cost · carbon · congestion · connectivity |
| 002 | Jordan | Emotional | S7 · S8 · S9 | all five |
| 003 | CFO / IC | Financial | S6 · S8 · S9 | cost (LCOE differentials) |
| 004 | CEO | Social / Decision | S8 · S9 | carbon · cost |

**Three non-negotiable product implications — all differential:**

1. **Every score is a relative position, not an absolute value.** A cost score of 0.9 means "cheapest energy in EU relative to other zones" — not "costs €X to operate." The output is always comparative.
2. **LCOE output is a delta, not a total.** We output the energy cost differential between the top-ranked zone and the alternatives at the user's target MW. The CFO plugs that delta into their model — we do not replace their model.
3. **Single shared output for CEO and CFO.** JTBD-004 fails if Jordan produces two separate documents that drift apart. One tool output, one set of differential numbers, two people walk into the room aligned.
