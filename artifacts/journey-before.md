# AS-IS Customer Journey: EU Data Center Site Research

**Persona:** Jordan — Infrastructure Strategy Analyst / DC Investment Analyst / Head of DC Development  
**Trigger:** Investment mandate issued — leadership commits to EU expansion at X MW by a defined deadline  
**End state:** IC / board presentation delivered; recommendation approved or returned for revision  

---

## The Cost of Today

| Metric | Range | Basis |
|---|---|---|
| Analysis phase (mandate → IC deck) | **15–35 calendar days** | 4–12 weeks full pre-feasibility per industry benchmark [^21]; desk-research-to-presentation phase is the inner 15–35 days |
| Analyst hours consumed | **80–120 hours** | Sum of stage estimates below; at €600–€850/day |
| In-house analyst cost | **€18,000–€30,000** | €600–€850/day blended rate × 30–35 days [^1][^2][^3][^4] |
| External consultant alternative | **€40,000–€120,000** | Feasibility study benchmarks $20k–$500k [^6]; TDD mid-market $75k–$500k [^7]; Arcadis 4-DC German contract implies ~€80k–€240k/engagement [^8] |
| Ember carbon data age at analysis start | **1–3 months** | Ember publishes with ~1 month lag (EU), up to 3 months for some regions [^20] |
| ENTSO-E wholesale price age at IC presentation | **2–4 weeks** | Near real-time source, but 2–4 weeks old by deck submission date |
| Financial decision risk | **€50M–€1.7B over asset life** | EU wholesale spread: €72/MWh Nordic vs. Italy (2024) [^10][^11]; 100 MW DC annual electricity cost $41M–$131M depending on location [^13]; energy = 40–67% of DC opex [^16][^17] |
| Cost of each scenario re-run | **+1–2 analyst days** | Full manual rebuild required; at €600–€850/day = +€600–€1,700 per scenario |

---

## Journey Map

```
MANDATE ──► S1 Brief ──► S2 Energy Data ──► S3 Carbon Data ──► S4 Grid Scoping
                                                                        │
                                                                        ▼
IC Meeting ◄── S9 ◄── S8 Deck Prep ◄── S7 Scoring ◄── S6 Supply Mix ◄── S5 Stitch & Longlist
```

---

## Stage 1 — Mandate & Brief

**Time:** 0.5–1 day | **Tools:** Email, meeting notes  
**Emotional state:** 😤 Energized — but scope is underspecified

Jordan receives the directive: place X MW in Europe by a deadline. The MW is fixed by business demand. The carbon ceiling is often stated qualitatively ("we need to be green") with no gCO₂/kWh number attached. Prior analysis from previous deals is rarely reusable — different geography, different assumptions.

**Pain:**
- Carbon constraint undefined — must be clarified through back-and-forth before analysis starts
- No structured intake format — scope is inferred, creating downstream rework when assumptions differ
- Starting from zero every time — no institutional memory, no reusable template

---

## Stage 2 — Energy Price Data Sourcing

**Time:** 1–2 days | **Tools:** ENTSO-E Transparency Platform, Excel  
**Emotional state:** 😑 Mechanical and tedious

Jordan navigates to the ENTSO-E Transparency Platform and downloads day-ahead wholesale price data. ENTSO-E organises data by **bidding zone** — approximately 30 zones across the EU [^18]. Critically, most EU countries comprise a single bidding zone: Germany, Poland, France, the Netherlands, Belgium, and Spain are each one zone [^18][^19]. This means the platform provides one country-wide average price for the markets where most EU DC development happens. A DC in Brandenburg pays the same published price as one in Bavaria. Sub-national nodal price variation — the signal that actually matters for regional siting — is not publicly available on ENTSO-E [^19].

**Pain:**
- Most major EU markets = one bidding zone = one country-wide average price [^18][^19]
- Sub-national nodal price variation (the relevant signal for siting) not publicly available [^19]
- Up to 20+ individual country/zone downloads required — no unified bulk EU export
- Format inconsistencies across zones require manual cleaning
- Static snapshot — no forward curve, no trend

**Hours wasted on mechanical data wrangling:** ~8–16 hours

---

## Stage 3 — Carbon Intensity Data Sourcing

**Time:** 0.5–1 day | **Tools:** Ember Climate website, Excel  
**Emotional state:** 😤 Frustrated

Jordan navigates to Ember Climate and looks up grid carbon intensity per country. Ember updates its data twice monthly [^20] and publishes EU country figures with approximately a 1-month lag; some non-EU or data-sparse regions carry a 2–3 month lag [^20]. Data is available at country level only — no zone or NUTS2 granularity exists in Ember's published dataset [^20].

Jordan cannot determine which EU zones clear a specific gCO₂/kWh ceiling without manually filtering country averages. Sub-national variation is invisible: the wind-heavy north of Germany looks identical to the coal-heavy east.

**Pain:**
- Country-averaged only — a 200 gCO₂/kWh ceiling cannot be applied at zone level [^20]
- ~1 month publication lag for EU data; up to 3 months for some markets [^20]
- No bulk pull — each country is a manual lookup
- Zone-level variation (the thing that matters for siting) does not exist in this dataset [^20]

**Wasted decision quality:** Zone selection made on country averages that may mask the best or worst EU zones by 50–100 gCO₂/kWh or more.

---

## Stage 4 — Grid Infrastructure Scoping

**Time:** 1–2 days | **Tools:** Google Maps, OpenStreetMap, Excel  
**Emotional state:** 😬 Uncertain and uncomfortable

Jordan opens Google Maps and OSM and visually inspects candidate regions for substation presence and fiber coverage. Academic validation of the OSM power dataset confirms strong coverage of **high-voltage (220+ kV) transmission** infrastructure across Europe — circuit length correlation of ρ = 0.9980 against the ENTSO-E official inventory [^27]. However, this validation applies to the transmission backbone. The sub-transmission and distribution infrastructure relevant to an industrial grid connection for 50–200 MW — typically 110 kV or lower — is less systematically mapped in OSM [^27]. Substation markers show presence, not capacity, headroom, or available connection slots.

Grid connection queues across Europe reached 1,700+ GW by 2024 [^25], meaning available headroom at any given substation is genuinely opaque: there is no public dataset showing which connection slots are already committed.

**Pain:**
- OSM high-voltage transmission is well-mapped; sub-transmission connections for DCs are less so [^27]
- Substation markers show presence — capacity, headroom, and queue status are invisible
- Grid connection queues of 1,700+ GW across EU mean headroom data is dynamic and not public [^25]
- Typical grid connection reinforcement timelines: 5–10 years [^24]; 2-year authorization minimum under 2025 EU Grid Package [^26]
- Assessment is qualitative and non-defensible under IC scrutiny

**Risk:** Jordan flags a region as grid-suitable based on a map. It may have no available headroom within a 5-year horizon.

---

## Stage 5 — Manual Data Integration & Longlist

**Time:** 2–3 days | **Tools:** Excel / Google Sheets  
**Emotional state:** 😓 Overwhelmed

Jordan merges the three data tabs — ENTSO-E prices (one price per country for most markets), Ember carbon (country averages, 1–3 months stale), and OSM grid notes (presence-only) — into a master spreadsheet. The geographic levels don't align: energy and carbon data are at country level; grid observations are point-based. Jordan applies rough weights and scores 8–12 candidate countries or regions.

The longlist is built on fundamentally mismatched granularity. A data center going into a specific zone in Poland is scored on the average wholesale price of all of Poland.

**Pain:**
- No EU zone-level dataset exists — country data is forced onto zone-level decisions
- Manual merge is error-prone: stale tabs, copy-paste mistakes, unit mismatches
- Scoring is ad hoc — arbitrary weights, no audit trail
- Longlist gaps filled by prior knowledge and assumption

---

## Stage 6 — Supply Mix Analysis

**Time:** 3–5 days | **Tools:** Excel, PPA broker conversations, consultant reports  
**Emotional state:** 😤 Frustrated

For each shortlisted region, Jordan researches PPA availability and rates. **PPA pricing is structurally non-public.** Pexapark's market analysis states: *"Price transparency in the PPA market is low due to a comparatively low number of transactions, the bilateral nature of PPAs and lack of disclosure of transacted prices"* [^14]. LevelTen Energy, which built a platform specifically to address this gap, describes the traditional process as one where *"price offers [are] typically shared directly between buyers and sellers during weeks-long RFP processes that can result in outdated prices by the time they are completed"* [^15].

Jordan builds the grid/PPA/on-site blended LCOE model in Excel, from scratch, as done on every previous deal. There is no reusable template. If the load estimate changes by even 10 MW, the model must be rebuilt.

**Pain:**
- PPA prices are bilateral and confidential — "price transparency... is low" [^14]; broker access required [^15]
- Curtailment zone intelligence is informal and stale — zone-level discount cannot be priced with confidence
- Model rebuilt from scratch every deal — no institutional memory
- Cannot tell the CFO "the PPA discount at this zone is X€/MWh" — can only flag that an opportunity may exist [^14][^15]
- Any change to MW or carbon ceiling requires full manual rebuild

**Hours wasted on a repeat rebuild:** ~24–40 hours per deal, every deal.

---

## Stage 7 — Site Shortlisting & Scoring

**Time:** 2–3 days | **Tools:** Excel, PowerPoint  
**Emotional state:** 😰 Anxious

Jordan selects 3–5 final sites, applies dimension weights, and ranks them. The methodology is ad hoc — weights chosen based on experience, not a published standard. There is no audit trail. If the IC asks "why does Poland rank above Finland?" the answer relies on Jordan's judgment, not a reproducible algorithm.

Meanwhile: the financial stakes of getting this wrong are substantial. The 2024 EU wholesale electricity price spread between the cheapest and most expensive major markets was **€72–73/MWh** — Nordic at €36/MWh vs. Italy/Ireland at €108–109/MWh [^10][^11]. For a 100 MW DC, CNBC quantified this as the difference between $41M and $131M in annual electricity costs [^13] — a $90M/year differential that compounds to **$1.8B over a 20-year asset life**. Energy accounts for 40–67% of DC operating costs [^16][^17]. Jordan is scoring sites that differ by €1B in lifetime energy cost, using a manual Excel model with arbitrary weights.

**Pain:**
- Scoring weights are arbitrary and not defensible under scrutiny
- No audit trail: weight changes and their effect on ranking are invisible
- Any input change restarts the scoring from scratch
- The financial stakes are €100M–€1.7B scale [^10][^11][^13] — the tool's accuracy matters enormously

---

## Stage 8 — IC / Board Presentation Preparation

**Time:** 2–3 days | **Tools:** PowerPoint, Excel, Word  
**Emotional state:** 😩 Exhausted and deadline-pressured

Jordan builds two separate documents from the same analysis: a technical deck for the CEO and a financial cost delta summary for the CFO. These must be reconciled manually. By the time the deck is ready, the ENTSO-E prices used in the model are 2–4 weeks old. The Ember carbon data was published 1–3 months ago [^20]. The formatting and charting work takes as long as the analysis itself.

In-house, a senior infrastructure analyst running this process costs €600–€850/day [^1][^2][^3] — for a 30–35 day engagement: **€18,000–€30,000** in analyst time alone [^1][^2][^4]. If Jordan's firm engages a specialist DC advisor instead, the engagement cost is **€40,000–€120,000** [^6][^7][^8][^9] — and the output is a static PDF that cannot be re-run.

**Pain:**
- Two deliverables from one analysis — version mismatch risk at IC if numbers drift between documents
- Narrative written from scratch — no structure inherited from the scoring output
- ENTSO-E prices 2–4 weeks old; Ember carbon 1–3 months stale [^20]
- Consultant alternative: €40k–€120k, one-time, non-re-runnable [^6][^7][^8]
- Cannot re-run if IC asks for a different scenario in the meeting

**Cost of formatting work:** ~16–24 analyst hours producing documents, not analysis.

---

## Stage 9 — IC Meeting & Follow-up

**Time:** 0.5 days (meeting) + 1–3 days (follow-up)  
**Tools:** PowerPoint, Excel, Email  
**Emotional state:** 😟 Defensive and stressed

Jordan presents to the investment committee. The data holds together until someone asks: "What is the grid headroom in that Polish zone?" or "What if we size this at 200 MW instead of 100?" Both questions require offline work. Jordan acknowledges gaps in real time.

The IC may defer the decision pending follow-up, costing another 1–3 days and potentially a second meeting. If a fundamentally different scenario is requested, the analysis restarts from Stage 2. EU grid congestion costs alone reached **€4.3 billion in 2024** [^28] — IC committees know grid headroom is a real business risk, and Jordan has no data to answer the question quantitatively.

**Pain:**
- No live re-run capability — what-if scenarios take days, not seconds
- Grid headroom questions cannot be answered with confidence [^24][^25][^26]
- PPA opportunity flagged but not priced — IC cannot commit on a flag alone [^14][^15]
- Credibility risk: if data is challenged and Jordan cannot defend it in the room, the recommendation loses authority
- Full restart risk: new MW target or carbon ceiling → back to S2

**Worst-case outcome:** IC defers. Jordan rebuilds. Second meeting in 2 weeks. Analysis is now 6 weeks old.

---

## What This Costs, Summed

| Stage | Hours | Primary waste |
|---|---|---|
| S1 Brief | 4–8 | Scope ambiguity, no intake format |
| S2 Energy data | 8–16 | 20+ zone downloads, 1 price per country for most of EU [^18][^19] |
| S3 Carbon data | 4–8 | Manual transcription, country-level only, 1–3 month lag [^20] |
| S4 Grid scoping | 8–16 | No headroom data, 1,700 GW EU queue invisible [^25] |
| S5 Integration | 16–24 | Manual merge, geographic mismatch |
| S6 Supply mix | 24–40 | Full rebuild every deal; PPA pricing structurally non-public [^14][^15] |
| S7 Scoring | 16–24 | Arbitrary weights; stakes are €100M–€1.7B [^10][^11][^13] |
| S8 Deck prep | 16–24 | Two documents, reconciliation, manual narrative; €18k–€30k in analyst cost [^1][^2][^3] |
| S9 IC + follow-up | 8–24 | No live re-run; grid headroom unanswerable [^24][^25] |
| **Total** | **80–120 hrs** | **15–35 day analysis cycle; 4–12 weeks full pre-feasibility [^21]** |

**The structural problem isn't effort — it's fragmentation.** The data exists. The analysis is sound. But it lives across 5 tools, 20+ sources, and two separate documents that must be reconciled by hand, every deal, from scratch. The financial decision it informs is worth €100M–€1.7B over the asset life [^10][^11][^13]. The tool replacing this process doesn't need to be perfect — it needs to be one query.

---

## Sources

[^1]: Stafiz (2025). *Daily Rates in Consulting*. €600–€900/day for expertise/infrastructure consultants. https://stafiz.com/en/daily-rates-in-consulting

[^2]: Consultancy.eu (2025). *Consulting Industry Fees & Rates*. €800–€1,000/day blended rate; mid-tier firms $150k–$220k annual revenue per consultant. https://www.consultancy.eu/consulting-industry/fees-rates

[^3]: Metrics.biz (2025). *IT Consultant Day Rates 2025*. €600–€900/day for infrastructure roles in Europe; 19.4–25% increase since 2020. https://www.metrics.biz/en/blog-post/daily-rates-2025-for-it-consultants-remain-high.html

[^4]: Breagh Recruitment (2026). *Data Centre Salaries Europe 2026*. DC project management €85k–€130k/yr; senior leadership €150k–€210k. Day-rate equivalent: €510–€720. https://breaghrecruitment.com/data-centre-salaries-europe-2026

[^5]: Wall Street Oasis (forum, 2024). *Infrastructure PE Europe Analyst Salary*. Major infra PE firms (Ardian, GIP, Antin): €75k–€80k base + 50–80% bonus; fully-loaded €120k–€180k/yr → €480–€720/day. https://www.wallstreetoasis.com/forum/private-equity/infrastructure-pe-europe-analyst-salary

[^6]: Aninver Development Partners (2025). *Cost of a Feasibility Study*. Range: $20,000–$500,000 for professional external feasibility studies. DC pre-feasibility sits in mid-range. https://aninver.com/blog/cost-of-a-feasibility-study

[^7]: Datarooms.org (2025). *Due Diligence Cost Benchmarks*. Technical due diligence mid-market: $75,000–$500,000; operational assessment workstream: $20,000–$80,000. https://datarooms.org/vdr-blog/due-diligence-costs/

[^8]: Arcadis (November 2025). *Arcadis Announces Four New Data Center Wins in Germany*. Combined value €8M for 4 Frankfurt/Berlin hyperscale DC projects covering TDD, permitting, construction monitoring. Implied per-engagement: €80k–€240k. https://www.arcadis.com/en/news/global/2025/arcadis-announces-four-new-data-center-wins-in-germany

[^9]: Caroola (2025). *Rates & Pay for Renewable Energy Engineers & Consultants*. Senior infrastructure consultants £390–£420/day; specialist ceiling £1,000+/day. https://caroola.com/resources/sector-advice/rates-pay-renewable-energy-engineers-consultants/

[^10]: AleaSoft (2025). *Analysis Year 2024: European Electricity Market Prices*. Nordic average: €36.06/MWh; Italy (IPEX): €108.52/MWh; spread: €72.46/MWh. "Yearly prices in 2024 were the lowest since 2021 in all markets analysed." https://aleasoft.com/fall-european-market-prices-2024-renewable-energy-gas/

[^11]: FfE — Forschungsstelle für Energiewirtschaft (2024). *European Day-Ahead Electricity Prices in 2024*. Sweden: €36/MWh; Ireland: €109/MWh; spread: €73/MWh. "The electricity price in Sweden was less than half the European average." https://www.ffe.de/en/publications/european-day-ahead-electricity-prices-in-2024/

[^12]: IEA (June 2025). *Electricity Mid-Year Update 2025: Prices & Trends in Wholesale Markets*. Nordic prices ~$40/MWh H1 2025; EU average ~$95/MWh; UK ~$115/MWh. https://www.iea.org/reports/electricity-mid-year-update-2025/prices-trends-in-wholesale-markets-differ-across-regions

[^13]: CNBC (May 2026). *Europe's AI Data Center Energy and Electricity Costs*. Annual electricity cost for 100 MW DC: $41M (cheap market) to $131M (expensive market). $88.97/MWh Germany, $44.19/MWh France, $111.65/MWh UK. https://www.cnbc.com/2026/05/18/europe-ai-energy-electricity-costs-data-centers-china-us.html

[^14]: Pexapark (2026). *PPA Price and PPA Value Are Not the Same: Why PPA Prices Diverge from Value in Renewable Markets*. "Price transparency in the PPA market is low due to a comparatively low number of transactions, the bilateral nature of PPAs and lack of disclosure of transacted prices, alongside the wide array of deal structures and non-standard PPA contracts." https://pexapark.com/blog/ppa-price-and-ppa-value-are-not-the-same-part-2-why-ppa-prices-diverge-from-value-in-renewable-markets/

[^15]: LevelTen Energy / Solar Power World (2022). *LevelTen Energy Launches Web Platform for PPA Pricing Transparency*. "Traditionally, there are roadblocks to obtaining PPA pricing, with price offers typically shared directly between buyers and sellers during weeks-long RFP processes that can result in outdated prices by the time they are completed." https://www.solarpowerworldonline.com/2022/08/levelten-energy-launches-web-platform-for-ppa-pricing-transparency/

[^16]: Epoch AI (2026). *One-Gigawatt AI Data Center Cost Breakdown*. Electricity = $0.6B of $0.9B annual OpEx (67%) for 1 GW AI DC. https://epoch.ai/data-insights/ai-datacenter-cost-breakdown

[^17]: Network Installers (2026). *Data Center Operating Costs*. "Electricity accounts for 40% to 60% of total operational costs." https://thenetworkinstallers.com/blog/data-center-operating-costs/

[^18]: Synertics (2024). *Bidding Zones in European Electricity Markets*. ~30 bidding zones across EU; most countries = 1 zone (Germany, France, Poland, Netherlands, Belgium); exceptions: Italy 6 zones, Norway 5, Sweden 4, Denmark 2. https://synertics.io/blog/74/bidding-zones

[^19]: ENTSO-E Transparency Platform (2024). *Introduction Guide for New Users*. Data available at control area, bidding zone, and country levels. For most of the EU, bidding zone = country = one price for the entire national territory. https://transparencyplatform.zendesk.com/hc/en-us/articles/13772306625428-Introduction-guide-for-new-users

[^20]: Ember Climate (2025). *Monthly Electricity Data — Methodology*. "Ember's data is updated twice a month." EU country figures: ~1 month publication lag. US data: 3-month lag from EIA reporting. "In some cases, data is published on a monthly lag; recent months are estimated based on Ember's own generation forecasting model." https://ember-energy.org/data/monthly-electricity-data/

[^21]: Build.inc (2024). *Data Center Site Selection*. "Feasibility, site selection & business case typically take 4–12 weeks, though this can be longer for complex land acquisition or regulatory issues." AI-accelerated screening: "development teams using AI-native screening tools are shortlisting viable sites in days rather than weeks." https://build.inc/insights/data-center-site-selection

[^22]: Broadstaff Global (2024). *Data Center Construction Timeline*. Full DC development including utility coordination and regulatory review: 18–24 months typical. https://broadstaffglobal.com/data-center-construction-timeline

[^23]: Avisenlegal (2024). *How Long Does It Take to Develop a Data Center*. Planning/feasibility phase: 3–6 months; site selection including regulatory review: 6–12 months. https://www.avisenlegal.com/how-long-does-it-take-to-develop-a-data-center-a-step-by-step-timeline/

[^24]: Eurelectric (2024). *What Are Grid Connections and How Europe Can Fix the Queue*. "Typical project times for reinforcing the connection to the TSO exceed 5 to 10 years." https://www.eurelectric.org/in-detail/what-are-grid-connections-and-how-europe-can-fix-the-queue/

[^25]: Eurelectric (2025). *From Backlog to Breakthrough: Managing Connection Queues in Distribution Networks*. "Around 1,700 GW of renewable projects waiting across 16 European countries... more than 450,000 RES connection requests (+133% since 2021)." https://www.eurelectric.org/wp-content/uploads/2025/04/From-Backlog-to-Breakthrough-Managing-Connection-Queues-in-Distribution-Networks.cleaned.pdf

[^26]: European Commission (December 2025). *European Grids Package*. "2025 European Grids Package introduces EU-level time limits for authorisation procedures, set at two years with a possible one-year extension." https://energy.ec.europa.eu/document/download/62c46b3d-0df9-42a1-a5fe-c3c71ed5f18c_en

[^27]: Hörsch, J. et al. (2025). *Modelling the High-Voltage Grid Using Open Data for Europe and Beyond*. Nature Scientific Data / PMC. "OSM data coverage of the European high-voltage grid is high or even close to complete." Circuit length correlation vs ENTSO-E: ρ = 0.9980. Validation covers 220–750 kV; sub-transmission coverage is less systematised. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11830763/

[^28]: IEA (2025). *Overcoming Energy Constraints Is Key to Delivering on Europe's Data Centre Goals*. "High grid congestion costs — which reached EUR 4.3 billion in 2024 — are driving developers toward areas with greater available grid capacity." https://www.iea.org/commentaries/overcoming-energy-constraints-is-key-to-delivering-on-europe-s-data-centre-goals

[^29]: IEA (2023, updated 2024). *Electricity Grids and Secure Energy Transitions*. "At least 3,000 GW of renewable power projects, of which 1,500 GW are in advanced stages, waiting in grid connection queues globally." https://www.iea.org/reports/electricity-grids-and-secure-energy-transitions
