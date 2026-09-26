# DC Hound — Findings

As of 2026-09-26. Every verified claim comes from a page that was actually opened on that date; raw notes are in `docs/research/raw/`. Claims that could not be verified are listed in section 10 and are not used anywhere else.

## Summary

1. **European data-center sites are won on deliverable grid power by a known date, and on regulatory permission.** Cost, land and fibre come after (section 3).
2. **The person who screens sites is not the person who decides.** A site-selection analyst recommends; finance, the investment committee, the board and lenders approve. The approvers only ever see the export (sections 1, 2).
3. **Regulation is a hard filter that DC Hound never modelled.** Examples:
   - Amsterdam halted new large data centers in June 2025.
   - Germany accepts 10–15% of data-center grid applications.
   - Denmark paused all new grid connections from March to June 2026.
   - Ireland now requires each new data center to bring its own generation and new renewables.
   - Finland's data-center electricity tax went from 0.05 to 2.24 c/kWh in July 2026.

   Section 4 lists what applies where.
4. **In the hackathon data, the only thing that varied between sites inside a country was farmland price.** Congestion, carbon, power price and capacity were one national value, and connectivity was the same number for all of Europe. The ranking was effectively "pick a country, then its cheapest farmland" (section 7).
5. **The market gap is real but narrow.** The dedicated siting software found (Enverus, LandGate, Paces, Nira, Transect) is US-focused, the market databases list existing facilities, and advisors sell bespoke work. No pan-European, grid-aware screen for the analyst was found (section 5).

## 1. Who builds and who decides

| Actor | What they do in siting | Source |
|---|---|---|
| Hyperscaler site-acquisition team (Microsoft: Senior Director Site Acquisition EMEA → Site Acquisition Director → Site Acquisition Managers) | "Lead cross functional teams to evaluate, select, negotiate and recommend leases for approval"; "Work with Finance reps to conduct Total Cost of Ownership (TCO) analysis"; aligns with "capacity planning, network, energy, security, engineering". | [Microsoft Site Acquisition Director, LinkedIn](https://uk.linkedin.com/jobs/view/site-acquisition-director-at-microsoft-4451066734) |
| Hyperscaler land acquisition (Microsoft) | A separate role for greenfield land: "Lead identification, evaluation, and acquisition of strategic land parcels across EMEA", including zoning, entitlement and government engagement. | [Microsoft Land Acquisition Manager, LinkedIn](https://uk.linkedin.com/jobs/view/land-acquisition-manager-at-microsoft-4460329634) |
| Neoclouds / AI infrastructure (Nebius, Verda) | Dedicated "Site Selection Manager" roles scoped to EMEA; smaller companies merge site selection with colocation leasing in one role. | [Nebius](https://nl.linkedin.com/jobs/view/site-selection-colocation-manager-%E2%80%93-data-centers-at-nebius-4437654837), [Verda](https://uk.linkedin.com/jobs/view/site-selection-manager-%E2%80%94-emea-at-verda-4424474092) |
| Developers / colocation (Equinix, Digital Realty, Vantage…) | "translate that demand into built facilities by acquiring land, managing entitlements, negotiating with utilities, and arranging financing." | [Global Data Center Hub](https://www.globaldatacenterhub.com/p/how-to-underwrite-the-hyperscale) |
| Investors and lenders (infra funds, REITs, sovereign wealth) | Capital enters at different phases. Lenders underwrite on tenant credit, lease cash flows and power certainty: "These deals are not getting financed without firm, real power-delivery dates" (Sean Farney, JLL). | Same; [Data Center Knowledge](https://www.datacenterknowledge.com/data-center-site-selection/power-availability-now-determines-where-data-centers-get-built) |
| Board | Power procurement is "a priority at board level"; board approval is one of the preconditions of the final investment decision. | [Osborne Clarke](https://www.osborneclarke.com/insights/how-investors-are-managing-risk-new-wave-european-data-centre-projects) |
| Advisors (CBRE, JLL, Cushman & Wakefield, Arup, Turner & Townsend, Knight Frank, Savills) | Run site selection and due diligence *for* all of the above. No public pricing; engagements are custom. | Section 5 |

Patterns seen in the postings:
- Big companies split **land acquisition** (greenfield, zoning, government) from **site selection / leasing** (existing buildings, lease negotiation). Smaller ones merge them.
- Site teams co-own decisions with **finance** (TCO) and **legal** (lease documents).
- **No posting names who gives the final approval.** The director "recommend[s] leases for approval" and nothing more.

## 2. How a site gets chosen

A site survives a funnel, and each gate has a different owner:

1. **Market thesis.** Which countries and metros. Demand-led (hyperscaler capacity planning) or supply-led (a developer scanning for power and zoning).
2. **Site screen.** A site-selection team scores candidate sites, power first; sites with no credible power pathway die here. **This is DC Hound's job.**
3. **Land control, grid application, permits.** Months to years; the grid is the longest step. Power commitments and long-lead equipment must be ordered years before construction ([DCK](https://www.datacenterknowledge.com/data-center-site-selection/grid-constraints-steer-dutch-data-centers-beyond-amsterdam)).
4. **Recommendation and final investment decision (FID).** It needs lease, financing, construction (EPC) contract, permits, interconnection agreement *and* board approval in place at the same time ([Global Data Center Hub](https://www.globaldatacenterhub.com/p/how-to-underwrite-the-hyperscale)).

Planning advice from JLL: map each phase to utility delivery dates and "stress-test 12-, 24-, and 36-month delay scenarios" ([DCK](https://www.datacenterknowledge.com/data-center-site-selection/power-availability-now-determines-where-data-centers-get-built)).

## 3. What decides a site in 2026

1. **Deliverable power, on a date.** "Site selection in 2026 is driven primarily by deliverable power. If developers cannot secure megawatts on a predictable timeline, incentives, land costs, and fiber connectivity become secondary." (Assad Noori, EMEA head of data centers, JLL). "Cost and delivery timeline are now co-equal with availability." ([DCK, 2026-09-21](https://www.datacenterknowledge.com/data-center-site-selection/grid-constraints-steer-dutch-data-centers-beyond-amsterdam))
2. **Time to revenue over price.** "There's more of a focus on time to revenue than cost." (Farney, JLL). "The most attractive market is not necessarily the one with the cheapest electricity." (Siddharth Muzumdar, DC Byte). ([DCK, 2026-09-09](https://www.datacenterknowledge.com/data-center-site-selection/power-availability-now-determines-where-data-centers-get-built))
3. **The search starts from power.** "The key shift is from asking, 'Where do we want to build?' to 'Where can we actually secure and deliver the power?'" (Muzumdar, same source).
4. **Grid acceptance is rare.** Germany: "Only around 10-15% of grid applications for data centres will be accepted." A planned maturity-based procedure (*Reifegradverfahren*) will favour projects with "land already secured, a robust technical concept and credible financing." ([Osborne Clarke, 2026-04-07](https://www.osborneclarke.com/insights/how-investors-are-managing-risk-new-wave-european-data-centre-projects))
5. **Equipment lead times.** Transformers "up to three years" (Noori, JLL); substation transformers "exceeding 160 weeks" ([Global Data Center Hub](https://www.globaldatacenterhub.com/p/how-to-underwrite-the-hyperscale)).
6. **Then** connectivity, permitting and zoning, water, flood risk, land.
7. **Where growth is going.** Linesight: FLAP-D (Frankfurt, London, Amsterdam, Paris, Dublin) growing about 16%; "Southern Europe and the Nordics… 30-55% over the next year" ([Linesight, 2025-07-07](https://www.linesight.com/en-us/insights/beyond-real-estate-navigating-the-complexities-of-data-centre-site-selection/)).

## 4. Regulatory barriers

DC Hound's model contains none of this. Every row was checked against the cited page on 2026-09-26. Claims from the research passes that failed that check, or could not be opened, are in section 10.

**The pattern.** Regulation now works mainly through the **grid-connection process**:
- a pause (Denmark);
- a low acceptance rate (Germany);
- conditions attached to a connection (Ireland);
- a queue far larger than the grid (Italy, Spain, Denmark);
- designated fast-track sites (France, Portugal).

Outright bans are local (Amsterdam, and Dutch hyperscale outside designated areas). Second come efficiency and waste-heat duties (Germany, EU), which favour sites near heat demand. Third come electricity-tax changes (Finland up, Sweden's break gone), which move the cost ranking.

### EU level: applies everywhere

| Rule | What it requires | Effect on siting | Source |
|---|---|---|---|
| Energy Efficiency Directive (EU) 2023/1791, Art. 26(6) | Data centres with a total rated energy input above 1 MW "utilise the waste heat or other waste heat recovery applications unless they can show that it is not technically or economically feasible". | Favours sites near heat off-takers (district heating, industry). A remote greenfield site has to argue infeasibility. | [EUR-Lex](https://eur-lex.europa.eu/eli/dir/2023/1791/oj) |
| EED Art. 12 and Delegated Regulation (EU) 2024/1364 | From 500 kW IT, yearly reporting of energy, PUE, water, renewable share and waste heat to the European database: first by 15 Sep 2024, then every 15 May. | A compliance cost, not a location filter yet. The data feeds the coming rating scheme. | [EUR-Lex](https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj), [Commission](https://energy.ec.europa.eu/topics/energy-efficiency/energy-efficiency-targets-directive-and-rules/energy-efficiency-directive/energy-performance-data-centres_en) |
| EU-wide rating scheme for data centres | The Commission took feedback on a draft regulation from 26 Mar to 23 Apr 2026. Its content (for example any minimum performance standard) was not verified. | Could become a filter on inefficient designs. Watch it. | [Commission](https://energy.ec.europa.eu/topics/energy-efficiency/energy-efficiency-targets-directive-and-rules/energy-efficiency-directive/energy-performance-data-centres_en) |
| Cloud and AI Development Act (CADA), part of the AI Continent Action Plan | Aims at "at least tripling the EU's data centre capacity within the next 5–7 years" and "simplifying and accelerating permitting and deployment of data centres". Legislative status was not verified. | A potential accelerator. Nothing binding verified. | [Commission](https://digital-strategy.ec.europa.eu/en/policies/cloud-and-ai-development-act) |

### By country

| Country | Rule or situation | Effect on siting | Source |
|---|---|---|---|
| Ireland | A de facto moratorium on new data-center connections (since 2021) was replaced by a new policy on 12 Dec 2025. It covers sites of 1 MVA and above; sites of 10 MVA and above ("almost every hyperscale and co-location data centre") carry the heaviest duties. A site must bring its own generation or storage, on site or nearby, matching its maximum import capacity and trading in the wholesale market. At least 80% of annual demand must come from *additional* renewables generating in Ireland (6-year glide path). Operators weigh whether the location is constrained. | Connection is possible again, but every site needs its own dispatchable generation and a credible new-renewables plan. Constrained locations (Dublin) are assessed case by case. | [CRU](https://www.cru.ie/about-us/news/the-cru-publishes-its-decision-on-new-electricity-connection-policy-for-data-centres/), [William Fry, 24 Jun 2026](https://www.williamfry.com/knowledge/irelands-data-centre-connections-back-online/) |
| Netherlands | National policy bars hyperscale (≥ 10 ha and 70 MW) from most of the country. Amsterdam halted new large data centers in June 2025. | A hard exclusion for hyperscale outside designated areas. | [DCK, 2026-09-21](https://www.datacenterknowledge.com/data-center-site-selection/grid-constraints-steer-dutch-data-centers-beyond-amsterdam) |
| Germany | Energy Efficiency Act (EnEfG) for data centers starting operation from 1 Jul 2026: PUE ≤ 1.2, and an energy reuse factor of ≥ 10%. The factor rises to 15% for data centers starting from 1 Jul 2027 and 20% after 1 Jul 2028, with exemptions such as an agreement with a nearby municipality or heat-network operator. Also 100% renewable electricity from 1 Jan 2027. Separately, only about 10–15% of data-center grid applications are accepted, and a maturity-based procedure is planned. | The grid is the main filter. The waste-heat target ties sites to heat demand, and the renewables rule adds PPA cost. | [White & Case](https://www.whitecase.com/insight-alert/data-center-requirements-under-new-german-energy-efficiency-act), [Osborne Clarke](https://www.osborneclarke.com/insights/how-investors-are-managing-risk-new-wave-european-data-centre-projects) |
| Denmark | Energinet paused all new grid-connection agreements on 2 Mar 2026, with about 60 GW queued against a national peak of about 7 GW. The pause was lifted on 3 Jun 2026 in favour of a new case-processing model with stricter requirements and maturity criteria. The regulator opened a review of that model on 8 Jun 2026. | New large loads face prioritisation rules that are still in flux. | [Plesner, 8 Jun 2026](https://plesner.com/en/news/energinets-grid-connection-pause-and-its-impact-what-do-project-owner), [Auxilium](https://www.auxinfra.com/blog/grid-connection-queue-denmark) |
| Sweden | The data-center electricity tax reduction was abolished from 1 Jul 2023; data centers now pay the general rate. | No tax advantage today, although older articles still describe one. | [Skatteverket via SDIA](https://knowledge.sdialliance.org/policies/sweden-abolishes-tax-incentives-for-data-centers) |
| Finland | From 1 Jul 2026, data-center electricity moves from tax category II (0.05 c/kWh) to the general category I (2.24 c/kWh), which is +2.19 c/kWh. | About +€22/MWh on running cost, which narrows Finland's cost advantage. | [Finnish Government, 23 Oct 2025](https://valtioneuvosto.fi/en/-/government-safeguards-finland-s-competitiveness-in-attracting-data-centre-investments) |
| Norway | Data Center Regulation in force from 1 Jan 2025: operators register with Nkom before starting operations, plus security and preparedness duties. | Compliance only, not a location filter. | [Haavind](https://haavind.no/en/regulation-of-data-centers-in-norway-focus-on-security-and-preparedness/) |
| France | RTE fast-track sites: Bosquel 1,000 MW, and Escaudain, Fouju, Dunkirk and Montereau at 700 MW each. RTE is quoted as offering "250 MW accessible in two years — permitting included — up to 1,000 MW in four years or less". A standard HV connection elsewhere takes 18–36 months, by a consultant's estimate. | A strong pull toward five named sites. | [GridReadiness](https://www.gridreadiness.com/blog/ai-data-center-france-grid-connection-rte-2026) (a consultancy blog; the RTE primary source was not opened) |
| Italy | Law Decree 21/2026, in force 21 Feb 2026: one authorisation covers data-center build and grid connection, with a 10-month statutory deadline. Terna held more than 50 GW of data-center connection requests from more than 300 projects in June 2025, up from 30 GW six months earlier. The Milan and Rome substations face a shortfall of about 150 MW by 2028. | Permitting is no longer the bottleneck; the grid is. | [Latham & Watkins](https://www.lw.com/en/insights/italy-passes-new-data-center-regulations), [Global Data Center Hub](https://www.globaldatacenterhub.com/p/italys-50-gigawatt-grid-queue-is) |
| Spain | Grid access for demand is "scarce and very competitive", and many applications are rejected. Transmission nodes can be reserved for demand-capacity tenders, where data centers "are not going to be the preferred option". On water: the data centers announced in Aragón up to Aug 2025 would need about 10 million m³ a year, roughly the irrigation for 2,200 ha, in a region with about 320 l/m² of rainfall. | Grid access and water are the filters, and water in Aragón is politically sensitive. | [WFW, Jun 2025](https://www.wfw.com/articles/data-centres-an-international-legal-and-regulatory-perspective-spotlight-on-spain/), [Urbequity](https://urbequity.com/en/data-centres-in-aragon/) |
| Portugal | National Data Center Plan, approved 19 Mar 2026: AICEP acts as the single contact point, licensing gets maximum deadlines, and pre-zoned land comes with planning, infrastructure and grid connections coordinated with REN. | An accelerator: pre-zoned sites. | [Portugal Global](https://portugalglobal.pt/en/news/2026/abril/portugal-approves-national-data-center-plan/) |
| Greece | Law 5069/2023 creates a dedicated regime with land uses and building requirements, and a notification duty for data centers of ≥ 200 kW IT serving third parties. | Clarity on land use, not a filter. | [WFW, Sep 2025](https://www.wfw.com/articles/data-centres-an-international-legal-and-regulatory-perspectivespotlight-on-greece/) |

**Not covered:** Belgium, Poland, Austria, Czechia, Romania, Hungary and the Baltics. The research found claims for some of these (section 10), but none was verified.

**What this means for DC Hound.** A per-country regulatory layer is feasible and mostly static. It would carry:
- hard exclusions (hyperscale in the Netherlands, Amsterdam);
- flags such as a connection pause, low acceptance, on-site generation required, or a waste-heat duty;
- cost adjustments (Finland's tax, Ireland's generation and renewables duties);
- boosts (the French fast-track sites, Portuguese pre-zoned land).

Each entry needs a date and a source, because the rules change within months: Denmark paused and reopened within one quarter.

## 5. Market and competitors

**Market size.** Europe data-center market USD 59.84 bn in 2025, forecast USD 148.82 bn by 2031. Colocation is USD 11.65 bn in 2025, forecast USD 46.51 bn by 2031 and 68% of 2025 construction investment; hyperscale self-build is the fastest-growing segment ([GlobeNewswire, 2026-09-11](https://www.globenewswire.com/news-release/2026/09/11/3360148/28124/en/europe-data-center-colocation-market-forecast-to-reach-usd-46-51-billion-by-2031-as-ai-and-cloud-demand-accelerate.html)). This is a market-research press release, so treat it as indicative.

**Capital.** KKR and Oak Hill committed nearly USD 2 bn to Global Technical Realty's European platform ([BusinessWire, 2026-01-07](https://secure.businesswire.com/news/home/20260107040486/en/KKR-and-Oak-Hill-Capital-Commit-Nearly-%242-Billion-to-Leading-European-Data-Center-Platform-Global-Technical-Realty)).

**Siting and grid software**

| Product | What it does | Geography | Source |
|---|---|---|---|
| Enverus Data Center Siting | Screens "156M land parcels", withdrawal capacity at "23,000+ interconnection points", price forecasts | US | [enverus.com](https://www.enverus.com/products/data-center-siting-solutions/) |
| LandGate | Offtake capacity data, parcel search by substation distance, land marketplace | US | [landgate.com](https://www.landgate.com/energy-markets/data-centers) |
| Paces | Siting heatmaps, power-flow studies, permitting; claims "5x faster" development | US | [paces.com](https://www.paces.com/data-center-developers) |
| Nira Energy | Transmission capacity and point-of-interconnection screening | US | [niraenergy.com](https://www.niraenergy.com/data-centers) |
| Transect | Environmental due diligence, permitting, community acceptance | US | [transect.com](https://www.transect.com/transect-environmental-due-diligence-for-data-center-siting) |

**Market-intelligence databases** (existing facilities, not site screening): DC Byte, Baxtel, datacenterHawk, 451 Research (S&P), Structure Research, TeleGeography. None publishes pricing.

**Advisors**: CBRE, JLL, Cushman & Wakefield ("real-time view of supply, demand, pricing and power availability"), Arup, Turner & Townsend, Knight Frank, Savills. All custom engagements, no public pricing ([C&W](https://www.cushmanwakefield.com/en/industries/data-centers); others in `raw/C-market-tools.md`).

**Public grid-capacity data that DC Hound could use:**
- The Dutch *capaciteitskaart* (Netbeheer Nederland), with congestion status per location, updated weekly.
- The German BNetzA grid-connection transparency reforms, still at draft stage.

**The gap:** no fetched source showed a pan-European, grid-aware site screen aimed at the site-selection analyst. Advisors fill it with bespoke work.

## 6. Who DC Hound is for

- **Primary user: the site-selection / site-acquisition analyst or manager** at a developer, neocloud or advisory firm. They run gate 2 of the funnel under time pressure, are numerate, and return to the tool many times per project. This is research-based and not yet validated with real users.
- **Secondary reader: the approvers** (finance, investment committee, board, lenders). They never open the tool; they read the export. The export must show why each site ranks where it does and what every number rests on. This is what the original "CFO-legible" requirement really means.
- **Who will actually open it now is unknown:** the team, possibly investors, possibly prospective customers. The first screen must make sense to someone arriving cold.

## 7. What DC Hound's model does not account for

**How much each metric varies between sites in the hackathon data** (1,127 nodes, 27 countries):

| Metric | Varies within a country? | Distinct values in all of Europe |
|---|---|---|
| Congestion | No: one value per country | 27 |
| Carbon intensity | No: one value per country | 27 |
| Power price | No: one value per country | 24 |
| Capacity | No: one value per country | 27 |
| Land price | Yes, in 21 of 27 countries | 139 |
| Connectivity | No: one value for all of Europe (0.5) | 1 |

So the four scored dimensions collapsed to "country" plus "farmland price". In the rebuilt data, connectivity is computed per node and power price varies across bidding zones inside Denmark, Italy, Norway and Sweden. Congestion, carbon and capacity are still national.

**Gaps against what the industry ranks first:**

1. **No deliverable-power-by-date input.** "Congestion" is a national demand/generation ratio, `clip(0.5·demand/generation − 0.3, 0, 0.95)`, and capacity is national generation spread evenly over nodes. That is a proxy, not megawatts available at a substation on a date.
2. **No regulatory layer.** Moratoria, zoning bans, connection-acceptance rates and national data-center laws (section 4) are not in the model, so it can rank first a site that cannot legally be built or connected.
3. **No connection-queue or equipment lead-time input.** These are the factors that decide time to revenue.
4. **Land price is agricultural land** (Eurostat `apri_lprc`), not industrial land. It understates cost in exactly the metros where data centers cluster (Amsterdam, Frankfurt, Paris).
5. **Carbon is the national average**, which ignores within-country differences (e.g. wind-surplus north Germany).
6. **Water, flood risk, climate and permitting risk** are not scored.
7. **Missing inputs used to rank as best.** The ranking is a max-normalised weighted sum that skips NaN, so a missing value counted as 0, the best possible score. The rebuilt data excludes such nodes and records the reason.

**Price data licensing.** Energy-Charts publishes 16 bidding zones under CC BY 4.0 (AT, BE, CH, CZ, DE-LU, DE-AT-LU, DK1, DK2, FR, HU, IT-North, NL, NO2, PL, SE4, SI). All the others are "for private and internal use only". ENTSO-E's free re-use list does not cover day-ahead prices either (per [entsoemcp.com/licensing](https://entsoemcp.com/licensing); the ENTSO-E list itself was not opened). A commercial launch needs an exchange data licence (EPEX SPOT, Nord Pool).

## 8. Data problems found in the app, and what was done

| Problem in the hackathon build | Effect | Status |
|---|---|---|
| "Live" data was read from cached demo files | Numbers never refreshed | Replaced by a live ingest with a disk cache, per-source refresh intervals, and stale-on-failure |
| Greece missing: Eurostat codes Greece `EL`, the pipeline expected `GR` | No Greek sites at all | Fixed |
| Overseas regions included (French overseas departments, Canaries, Ceuta, Melilla, Azores, Madeira, Svalbard) | Non-mainland sites ranked against mainland Europe | Excluded |
| Connectivity a constant 0.5 everywhere | One of four scores carried no information | Computed per node from HV substations (OpenStreetMap, ≥110 kV) and internet exchanges (PeeringDB) |
| Power prices hardcoded to 2023 | Stale costs | Trailing 12 months of day-ahead prices (Energy-Charts), refreshed daily |
| Ireland had no price: wrong bidding-zone code | Irish sites, including Dublin, would be dropped | Fixed (`IE(SEM)`) |
| Cyprus and Malta have no day-ahead price on Energy-Charts | Cannot be costed | Excluded, with the reason recorded |
| Missing values ranked as the best score | Nodes with gaps could top the list | Nodes with missing inputs are excluded, with reasons |
| Server kept one global result set between calls | Two users would overwrite each other | Stateless API: each query carries its own inputs |
| Substations tagged without voltage were counted | Distribution substations inflated access | A voltage tag of ≥110 kV is required |

Data lineage per column is in `docs/methodology.md`; source freshness and licence are served live at `/api/sources`.

## 9. Open questions (need interviews, not desk research)

- Who exactly approves a lease or build at a hyperscaler, and how investment committees at colocation developers are composed.
- What analysts use today for the screen (Excel, GIS, advisors' reports) and how long a screen takes.
- Whether they would pay per query or per seat, and how much.
- Which regulatory and grid-queue data they already buy or collect by hand.
- Whether the export format (PDF) matches what goes to the committee.

## 10. Unverified claims, not used anywhere above

- FLAP-D interconnection queues of "7–10 years" (no fetched quote).
- A Dutch waiting list of "over 3,600 MW" in the Randstad (no fetched quote).
- EU grid congestion costs of "EUR 4.3 billion" in 2024 (attributed to ACER via IEA/Ember; not opened).
- EMEA hyperscale pipeline of "742 MW under construction + 2,661 MW land-banked" (JLL, from a search result only).
- The scope of Cushman & Wakefield's market index: sources disagree (a 33-market "maturity index" vs a 107-market, 24-variable comparison). Neither was verified.
- Site-selection roles at Mapletree and QTS, and more Verda vacancies (search results only; login wall).
- Stage durations for the funnel (screening, land option, grid application, permitting).
- Uptime Institute 2026 survey rankings of location factors (preview only).
- Other tools named in startup lists (CivilGrid, Orennia, PVcase Prospect, "Kasa") (vendor pages not opened).

**Regulation: found wrong when checked**
- Sweden "97% electricity tax rebate for data centres, active in 2026". The source cited was a 2016 article about the 2017 cut. The reduction was abolished on 1 Jul 2023 (Skatteverket).
- Ireland "Dublin blocked until 2028". That comes from a 2022 EirGrid statement. The connection policy was replaced on 12 Dec 2025, and constrained locations are now assessed case by case.

**Regulation: not verified (source blocked, not opened, or search snippets only)**
- Netherlands: waits of up to 10 years for business connections (Liander); an Amsterdam halt "until 2035"; the list of municipalities where hyperscale is allowed.
- France: PINM fast-track status and a 50% electricity-tax cut for large sites under the 2026 simplification law; permitting cut "from 17 to 9 months"; 18 GW pre-allocated to about 80 projects.
- Belgium: Elia's proposed "data centre" capacity category and its cap.
- Norway: fines of up to 5% of turnover.
- Frankfurt: the zoning plan limiting new cloud and colocation buildings (source returned 403).
- Poland: grid-connection advance payment doubled to PLN 60/kW (March 2026 reform).
- Romania: ANRE orders raising the connection guarantee to 20% and a EUR 20,000/MW auction deposit.
- Austria: a 200 MW minimum for transmission-level connections under the new Electricity Act (the Freshfields page opened, but this line was not in it).
- Czechia and Hungary: no data-center rules found; Hungary's figures came from a market-research page.
- EU level: taxonomy criteria for data centres; environmental-impact-assessment thresholds; EU water rules forcing air cooling in the south; a "needs-based" connection queue in the grids package. The research pass could not open EUR-Lex for these and cited instrument numbers that were not checked, so none is used above.

## 11. Sources

Pages opened on 2026-09-26:
- [Microsoft, Site Acquisition Director (LinkedIn)](https://uk.linkedin.com/jobs/view/site-acquisition-director-at-microsoft-4451066734)
- [Microsoft, Land Acquisition Manager (LinkedIn)](https://uk.linkedin.com/jobs/view/land-acquisition-manager-at-microsoft-4460329634)
- [Nebius, Site Selection & Colocation Manager (LinkedIn)](https://nl.linkedin.com/jobs/view/site-selection-colocation-manager-%E2%80%93-data-centers-at-nebius-4437654837)
- [Verda, Site Selection Manager EMEA (LinkedIn)](https://uk.linkedin.com/jobs/view/site-selection-manager-%E2%80%94-emea-at-verda-4424474092)
- [Global Data Center Hub, How to underwrite the hyperscale](https://www.globaldatacenterhub.com/p/how-to-underwrite-the-hyperscale)
- [Data Center Knowledge, Power availability now determines where data centers get built](https://www.datacenterknowledge.com/data-center-site-selection/power-availability-now-determines-where-data-centers-get-built)
- [Data Center Knowledge, Grid constraints steer Dutch data centers beyond Amsterdam](https://www.datacenterknowledge.com/data-center-site-selection/grid-constraints-steer-dutch-data-centers-beyond-amsterdam)
- [Osborne Clarke, How investors are managing risk in the new wave of European data centre projects](https://www.osborneclarke.com/insights/how-investors-are-managing-risk-new-wave-european-data-centre-projects)
- [Linesight, Beyond real estate: data centre site selection](https://www.linesight.com/en-us/insights/beyond-real-estate-navigating-the-complexities-of-data-centre-site-selection/)
- [Delegated Regulation (EU) 2024/1364, EUR-Lex](https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj)
- [Cushman & Wakefield, Data centers](https://www.cushmanwakefield.com/en/industries/data-centers)
- [Enverus Data Center Siting](https://www.enverus.com/products/data-center-siting-solutions/)
- [LandGate](https://www.landgate.com/energy-markets/data-centers), [Paces](https://www.paces.com/data-center-developers), [Nira Energy](https://www.niraenergy.com/data-centers), [Transect](https://www.transect.com/transect-environmental-due-diligence-for-data-center-siting)
- [GlobeNewswire, Europe data center colocation market](https://www.globenewswire.com/news-release/2026/09/11/3360148/28124/en/europe-data-center-colocation-market-forecast-to-reach-usd-46-51-billion-by-2031-as-ai-and-cloud-demand-accelerate.html)
- [BusinessWire, KKR and Oak Hill commit to Global Technical Realty](https://secure.businesswire.com/news/home/20260107040486/en/KKR-and-Oak-Hill-Capital-Commit-Nearly-%242-Billion-to-Leading-European-Data-Center-Platform-Global-Technical-Realty)
- [Energy-Charts API (price licences)](https://api.energy-charts.info/)
- [entsoemcp.com, licensing](https://entsoemcp.com/licensing)
- [Energy Efficiency Directive (EU) 2023/1791, EUR-Lex](https://eur-lex.europa.eu/eli/dir/2023/1791/oj)
- [European Commission, Energy performance of data centres](https://energy.ec.europa.eu/topics/energy-efficiency/energy-efficiency-targets-directive-and-rules/energy-efficiency-directive/energy-performance-data-centres_en)
- [European Commission, Cloud and AI Development Act](https://digital-strategy.ec.europa.eu/en/policies/cloud-and-ai-development-act)
- [CRU, New electricity connection policy for data centres](https://www.cru.ie/about-us/news/the-cru-publishes-its-decision-on-new-electricity-connection-policy-for-data-centres/)
- [William Fry, Ireland's data centre connections: back online](https://www.williamfry.com/knowledge/irelands-data-centre-connections-back-online/)
- [White & Case, Data center requirements under the German Energy Efficiency Act](https://www.whitecase.com/insight-alert/data-center-requirements-under-new-german-energy-efficiency-act)
- [Plesner, Energinet's grid connection pause](https://plesner.com/en/news/energinets-grid-connection-pause-and-its-impact-what-do-project-owner)
- [Auxilium, Grid connection queues in Denmark](https://www.auxinfra.com/blog/grid-connection-queue-denmark)
- [SDIA, Sweden abolishes tax incentives for data centers](https://knowledge.sdialliance.org/policies/sweden-abolishes-tax-incentives-for-data-centers)
- [Finnish Government, Data centre electricity tax](https://valtioneuvosto.fi/en/-/government-safeguards-finland-s-competitiveness-in-attracting-data-centre-investments)
- [Haavind, Regulation of data centers in Norway](https://haavind.no/en/regulation-of-data-centers-in-norway-focus-on-security-and-preparedness/)
- [GridReadiness, France grid connection and RTE fast-track](https://www.gridreadiness.com/blog/ai-data-center-france-grid-connection-rte-2026)
- [Latham & Watkins, Italy passes new data center regulations](https://www.lw.com/en/insights/italy-passes-new-data-center-regulations)
- [Global Data Center Hub, Italy's 50-gigawatt grid queue](https://www.globaldatacenterhub.com/p/italys-50-gigawatt-grid-queue-is)
- [Watson Farley & Williams, Spain](https://www.wfw.com/articles/data-centres-an-international-legal-and-regulatory-perspective-spotlight-on-spain/) and [Greece](https://www.wfw.com/articles/data-centres-an-international-legal-and-regulatory-perspectivespotlight-on-greece/)
- [Urbequity, Data centres in Aragón](https://urbequity.com/en/data-centres-in-aragon/)
- [Portugal Global, National Data Center Plan](https://portugalglobal.pt/en/news/2026/abril/portugal-approves-national-data-center-plan/)

Raw research notes: `docs/research/raw/A-roles.md`, `B-process.md`, `C-market-tools.md`, `D-regulation-eu.md`, `E-regulation-northwest.md`, `F-regulation-south-east.md`. **D, E and F contain unverified and some wrong claims (section 10). This file is the checked version.**
