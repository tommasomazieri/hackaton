# Jobs-To-Be-Done: DC Siting Intelligence Tool

**Personas:** Jordan (user), CFO / IC Member (buyer), CEO (decision-maker)  
**Grounded in:** AS-IS journey stages S1–S9

---

## Why JTBD over features

Jordan does not need "a dashboard." Jordan needs to stop losing 2–3 days to ENTSO-E country downloads that mask the zone-level variation where the DC will actually sit. The CFO does not need "a score." The CFO needs the number that goes into the DCF model on Friday. The CEO does not need a 80-page report — he needs one ranked winner he can say yes to.

These four jobs describe what each person is actually trying to make progress on.

---

## JTBD-001 — Jordan · Functional
### Screen Europe in one query instead of 20+ country downloads

> **When** I need to screen EU locations against a specific MW load and gCO₂/kWh ceiling, and today I face 1–2 days on ENTSO-E pulling 20+ country files plus a half-day on Ember — all producing country averages that mask the zone-level variation where the DC will actually sit —  
> **I want** a single query that applies the carbon ceiling as a hard filter at zone level and ranks EU NUTS2 zones by energy cost, grid headroom, and connectivity in one unified output —  
> **so I can** produce a defensible shortlist in hours instead of weeks, without stitching mismatched country-level datasets in Excel.

**Validates:** cost · carbon · congestion · connectivity  
**Pain anchor:** 8–24 hours of mechanical data wrangling (S2+S3); country-level granularity on decisions worth €100M–€1.7B over asset life.

---

## JTBD-002 — Jordan · Emotional
### Walk into IC with a defensible methodology, not gut-feel Excel

> **When** I have built a site ranking with manually assigned weights and no audit trail, and I am about to present to an investment committee who may challenge the data source, recency, or scoring methodology —  
> **I want** every score to cite a traceable source (PyPSA-Eur, Ember, OSM) with a published weighting methodology and a per-dimension breakdown showing exactly why Site A ranks above Site B —  
> **so I can** walk in with genuine confidence, defend the recommendation under live challenge, and not have it sent back for rework.

**Validates:** cost · carbon · congestion · connectivity · land  
**Pain anchor:** IC deferral adds 1–3 analyst days (€600–€1,700) and a 2-week delay; worst case restarts full analysis from S2.

---

## JTBD-003 — CFO / IC Member · Financial
### Turn the PPA flag into a €/MWh number for the DCF model

> **When** Jordan's analysis flags that a zone has high PPA curtailment opportunity but cannot quantify the discount — PPA prices are bilateral and structurally non-public — so a flag appears in the deck with no number I can model —  
> **I want** the PPA discount expressed as €/MWh at each flagged zone relative to day-ahead spot, and the NPV of that discount over the contract term at our target MW —  
> **so I can** quantify the financial value of the PPA-opportunity site over the grid-heavy alternative, plug the delta into our DCF model, and give the CEO a financially grounded recommendation — not a flag the committee cannot act on.

**Validates:** cost (supply mix / LCOE output)  
**Pain anchor:** PPA price transparency structurally low (Pexapark 2026); LevelTen Energy built an entire commercial platform to address this exact gap. Without zone-level LCOE, IC cannot distinguish a 15% discount from a marginal one.

---

## JTBD-004 — CEO · Social / Decision
### Receive one ranked winner — not a spreadsheet with the answer on page 62

> **When** my team brings me an EU expansion analysis that is a spreadsheet with trade-offs buried in an appendix, two versions of the numbers that Jordan and the CFO are not yet aligned on, and no clear winner —  
> **I want** one ranked recommendation with a plain carbon compliance story and a financial delta I can read in five minutes —  
> **so I can** make the go/no-go call without needing to understand grid physics, walk into the board with a defensible strategic rationale, and know that Jordan and the CFO are citing the same numbers.

**Validates:** carbon · cost  
**Pain anchor:** Current alternative — 80-page consultant report (€40k–€120k, one-time, non-re-runnable) or a misaligned CEO deck + CFO Excel with version-mismatch risk. CEO quote: *"I don't need to understand the grid. I need to know which country we're going into and whether we'll be able to say we're running on clean energy."*

---

## Summary

| JTBD | Persona | Type | Journey stages | Dimensions |
|---|---|---|---|---|
| 001 | Jordan | Functional | S2 · S3 · S5 | cost · carbon · congestion · connectivity |
| 002 | Jordan | Emotional | S7 · S8 · S9 | all five |
| 003 | CFO / IC | Financial | S6 · S8 · S9 | cost (LCOE / supply mix) |
| 004 | CEO | Social / Decision | S8 · S9 | carbon · cost |

**Three non-negotiable product implications:**

1. **Carbon hard filter at zone level, not country average.** JTBD-001 fails if the filter runs on country-level Ember data — Jordan's shortlist silently includes coal-heavy zones in a nominally "green" country.
2. **LCOE and supply mix as first-class outputs, not tooltips.** JTBD-003 fails if the PPA discount is flagged but not priced. The CFO cannot use a flag — only a number plugs into a DCF model.
3. **Single output that CEO and CFO read from the same source.** JTBD-004 fails if Jordan produces two separate documents that must be manually reconciled — the CEO approves when Jordan and CFO walk in already aligned.
