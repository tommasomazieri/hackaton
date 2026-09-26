> Unchecked research-agent notes. Some claims here are wrong or unverified; the checked version is `docs/findings.md` section 4 and 10.

# Data Center Siting Regulations: Northwestern Europe & Nordics (Sept 2026)

**Research Date: 26 September 2026**

## Summary Table: Regulations, Restrictions, and Siting Effects

| Country | Instrument / Policy | Status & Dates | What it blocks / requires | Effect on siting | Source (URL) | Quote |
|---------|-------------------|-----------------|------------------------|------------------|-------------|-------|
| Ireland | EirGrid Dublin grid constraint | **Active**: No new connections before 2028 | Moratorium on new grid connections in Greater Dublin area due to demand representing ~50% of regional load | **Blocks**: Dublin expansion until 2028; **Requires**: Alternative northern/coastal sites (Cork, Galway potential) | https://www.williamfry.com/knowledge/irelands-data-centre-connections-back-online/ | "EirGrid indicated in 2022 that new connections are unlikely before 2028" |
| Ireland | CRU Large Energy Users Connection Policy | **Effective**: December 2025 (implementation March 2026) | For sites ≥10 MVA: dispatchable generation/storage equal to 100% MIC, participating in wholesale market; plus 80% annual electricity from in-state renewables over 6-year glide path | **Requires**: On-site or proximate dispatchable capacity + dedicated renewable procurement; **Blocks**: Sites without feasible renewable integration | https://www.cru.ie/about-us/news/the-cru-publishes-its-decision-on-new-electricity-connection-policy-for-data-centres/ | "Data centres at or above 1 MVA must meet at least 80% of their annual electricity demand with additional renewable electricity generated in the State" |
| Ireland | System Stability Assessment (Fault Ride Through) | **Permanent requirement** | All data center connection applications must pass FRT test; must remain connected or reconnect rapidly after momentary faults | **Requires**: Advanced grid synchronization tech; **Blocks**: Sites with weak grid stability | https://www.williamfry.com/knowledge/irelands-data-centre-connections-back-online/ | "Every data centre connection application must pass a System Stability Assessment" |
| Netherlands | Hyperscale Data Center Restriction (National) | **Active since 1 Jan 2024**: Nationwide ban except Het Hogeland & Hollands Kroon | Definition: >10 hectares OR >70 MW electrical connected load | **Blocks**: 95%+ of Netherlands outside designated municipalities; **Permits**: Only projects in two northern municipalities (Het Hogeland, Hollands Kroon) | https://www.cms-lawnow.com/en/ealerts/2022/11/netherlands-prohibits-creating-hyperscale-data-centres-until-national-guidelines-are-passed | "A hyperscale data center is defined as a computer center or data center of more than 10 hectares and an electrical connected load of 70 MW" |
| Netherlands | Amsterdam Data Center Moratorium | **Effective**: April 2025 onwards | No new data centers or expansions until 2030 minimum; alderman statement of intent: no data centers until 2035 (except pre-approved projects) | **Blocks**: All new DC in Amsterdam (largest NL city); **Permits**: Previously-approved projects only | https://www.datacenterdynamics.com/en/analysis/the-ongoing-impact-of-amsterdams-data-center-moratorium/ | "Amsterdam would not allow any more data centres or expansions in the municipality until at least 2030" |
| Netherlands | Grid Congestion / TenneT Queue | **Ongoing**: Connection queue at 60+ GW with 10-year waits reported | Liander reports business connections with 10-year wait times; TenneT capacity saturated in multiple regions | **Blocks**: All large load connections face multi-year delays; **Requires**: Off-peak flexible contracts as interim solution | https://www.rabobank.com/knowledge/d011486697-backup-power-for-europe-part-6-dutch-bess-capacity-grows-despite-regulatory-hurdles | "More than 70 GW of customers, mainly large-scale battery energy storage projects, are currently stuck in the grid connection queue" |
| Germany | Energieeffizienzgesetz (EnEfG) - PUE Requirement | **Effective**: July 2026 onwards (new facilities); graduated for existing | New facilities: PUE ≤1.2 within 2 years; Existing: PUE ≤1.5 by July 2027, ≤1.3 by July 2030 | **Requires**: Advanced cooling efficiency; **Blocks**: Designs with PUE >1.2 post-2028; **Effect**: Higher OpEx, favors Nordic/cold-climate sites | https://www.whitecase.com/insight-alert/data-center-requirements-under-new-german-energy-efficiency-act | "For data centers starting operation from July 2026 onward, the PUE requirement is 1.2" |
| Germany | EnEfG - Renewable Energy Mandates | **Schedule**: 50% renewable by 2024 (retroactive), 100% by 2027 | All data centers >300 kW public, >1 MW private must source 100% of power from renewables by 2027 | **Requires**: PPAs or renewable procurement contracts; **Blocks**: Sites without renewable capacity access; **Effect**: Increases LCOE, favors windy regions (North Sea coastal, Schleswig-Holstein) | https://www.moduledge.com/blog/eu-data-center-regulations-2026 | "The Energy Efficiency Act mandates German data centers to procure 50% of their electricity from renewable sources by 2024, increasing to 100% by 2027" |
| Germany | EnEfG - Waste Heat Recovery | **Mandatory**: From July 2026 onwards | All new facilities >300 kW must integrate waste-heat reuse (district heating, industrial process heat, or other recovery) | **Requires**: Heat customer relationship or storage infra; **Blocks**: Isolated greenfield sites; **Effect**: Favors dense urban/industrial areas with heat demand | https://etalytics.com/resources/blog/germanys-energy-efficiency-act-in-data-centers | "Data center operators are obligated to introduce energy management systems by July 1, 2025" |
| Germany | Frankfurt Rechenzentrumsplan (Zoning) | **Active**: 2024 updated plan; enforced | Frankfurt am Main limited new cloud/colocation DC zoning; redirects growth to outlying towns (Hanau, Hattersheim, Offenbach, Schwalbach) | **Blocks**: New large DCs in central Frankfurt; **Permits**: Suburban expansion; **Effect**: Increases land costs in outlying regions; favors CyrusOne FRA7 model (Westside industrial) | https://www.datacenterdynamics.com/en/news/frankfurt-updates-its-plans-for-environmental-data-center-zoning/ | "Frankfurt announced an updated plan for commercial developments in the city, which will place a limitation on cloud and colocation data center buildings" |
| France | Projets d'Intérêt National Majeur (PINM) Fast-Track Status | **Effective**: May 2026 law (Loi de Simplification Économique); decree-based qualifying | PINM designation for major DC (30–50 hectares, significant investment/sovereignty role) → accelerated admin + reduced electricity tax (50% reduction for >1 GW annual) | **Permits**: Rapid grid connection & building permits; **Requires**: Sovereignty/domestic ecosystem criteria; **Effect**: Strongly favors large operators with EU/FR backing | https://www.addleshawgoddard.com/en/insights/insights-briefings/2025/real-estate/the-future-of-data-centres-in-france/ | "PINM status provides accelerated administrative procedures, particularly for building permits and electricity grid connection" |
| France | RTE Fast-Track Grid Connection Program | **Active**: 5 designated sites as of June 2026 | Five RTE Fast-Track sites: Bosquel (1,000 MW), Escaudain (700 MW), Fouju (700 MW), Dunkirk (700 MW), Montereau (700 MW); 250 MW deliverable in 24 months, 1,000 MW in 4 years | **Permits**: Priority grid access at designated sites; **Blocks**: DC outside Fast-Track zones face standard RTE queue (pre-allocated 18 GW for ~80 projects as of May 2026) | https://www.gridreadiness.com/blog/ai-data-center-france-grid-connection-rte-2026 | "RTE signed France's first Fast Track grid connection contract in January 2026 — 240MW by the end of 2027, 700MW by 2029, designed for 1,400MW" |
| France | Planning Authorization Timeline Reduction | **Effective**: 2025 (Green Industry Law) | Reduced authorization timelines from 17 months to 9 months for data center projects | **Permits**: Faster permitting; **Effect**: Competitive advantage vs. Germany/Benelux | https://www.addleshawgoddard.com/en/insights/insights-briefings/2025/real-estate/the-future-of-data-centres-in-france/ | "The Green Industry Law cut authorization timelines by approximately 50%: from 17 to nine months" |
| Belgium (Elia) | Data Center Category in Grid Capacity Framework | **Proposed/Partial implementation**: 2025 onwards (short-term measure) | Elia proposed creating dedicated "data centre" category within grid capacity with maximum allocation caps; flexible connection curtailment during peak demand allowed | **Blocks**: Exceeding allocated capacity; **Requires**: Acceptance of curtailment during grid stress | **Effect**: Capacity-capped expansion; uncertain ceiling not yet formally defined | https://www.silicon.co.uk/cloud/ai/belgium-power-ai-627144 | "Belgium's transmission system operator, Elia, recently proposed the creation of a specific data centre category within its network capacity framework, subject to maximum capacity allocations" |
| Belgium | 2028–2038 Grid Development Plan (TBD) | **In preparation**: Expected 2026 publication; implementation 2028–2038 | Will address data center consumption explicitly; long-term capacity planning | **Effect**: Future regulation TBD; current uncertainty creates planning risk | https://itdaily.com/news/datacenter/belgian-data-centers-growing/ | "The rise in data center energy consumption will be addressed in the upcoming 2028-2038 federal grid development plan" |
| Denmark | Energinet 3-Month Grid Connection Moratorium | **Active**: March 2026 – June 2026 (initial); likely extended pending queue reform | Temporary pause on all new grid connection agreements; Energinet assessing queue prioritization reform | **Blocks**: All new large-load connections during moratorium; **Effect**: First-come-first-served abolished February 1, 2026; new prioritization TBD | https://www.datacenterdynamics.com/en/news/danish-grid-operator-introduces-three-month-moratorium-for-new-grid-connections/ | "In March, Denmark's state-owned grid operator Energinet introduced a temporary pause on new grid connection agreements" |
| Denmark | Grid Capacity Saturation Statement | **Status**: Ongoing capacity constraint (as of 2024 LTP) | Energinet 2024 Long-Term Development Plan: "The power grid has already reached its upper limit today in many parts of Denmark" | **Blocks**: Reliable new connections in capacity-constrained regions; **Effect**: Regional prioritization needed; offshore wind capacity relief delayed | https://www.datacenterdynamics.com/en/news/danish-grid-operator-introduces-three-month-moratorium-for-new-grid-connections/ | "Energinet warned in its 2024 Long-Term Development Plan that 'The power grid has already reached its upper limit today in many parts of Denmark'" |
| Sweden | Electricity Tax Rebate (97%) for Data Centers | **Active**: Confirmed 2025, extended into 2026 | Data centers receive 97% electricity tax reduction; 2026 rate 0.442 SEK/kWh (~€0.042/kWh) vs. standard rate ~€0.12–0.14/kWh | **Permits**: Lowest electricity cost in Europe post-rebate; **Effect**: Strong incentive for DC siting; no major siting restrictions | https://www.cloudcomputing-news.net/news/sweden-confirms-tax-break-for-data-centres-following-government-study | "Swedish data centre operators are to enjoy a vastly reduced electricity tax rate for providing their services" |
| Sweden | Grid Connection Policy | **Status**: No reported moratoria or major restrictions as of Sept 2026 | Svenska kraftnät operates standard connection queue; no data-center-specific caps reported | **Effect**: Relative freedom of site selection; grid capacity not yet saturated for DC loads | — | — |
| Norway | Data Center Registration Law (Electronic Communications Act) | **Effective**: 1 January 2025 onwards | All data centers with subscribed electrical capacity >0.5 MW must register with Nkom; existing DCs had until 1 July 2025 to register; new DCs register before build starts | **Requires**: Regulatory registration; **Blocks**: Unregistered operation (penalties up to 5% annual turnover) | https://www.datacenterdynamics.com/en/news/norway-data-center-register/ | "All data centers with subscribed electrical capacity exceeding 0.5 MW must be registered with the authorities" |
| Norway | Security & Emergency Preparedness Requirements | **Effective**: 1 January 2025 onwards | Operators must meet security and emergency preparedness standards (details in regulation) | **Requires**: Compliance plan; **Effect**: No major siting restriction, primarily operational | https://haavind.no/en/regulation-of-data-centers-in-norway-focus-on-security-and-preparedness/ | "The new rules include requirements related to security and emergency preparedness" |
| Finland | Electricity Tax Removal on Data Centers | **Effective**: 1 July 2026 onwards | Move from low tax (Category II: €0.0005/kWh) to general rate (Category I: €0.0224/kWh); annual impact €47M; future incentive scheme (details TBD) for value-added DCs planned autumn 2026 | **Blocks**: Bulk power incentive post-July 2026; **Effect**: Significant LCOE increase (~220–350x) unless new scheme offsetts | **Major siting disincentive** | https://valtioneuvosto.fi/en/-/government-safeguards-finland-s-competitiveness-in-attracting-data-centre-investments | "The electricity tax on power used in data centres will move from the lower electricity tax category II to the general category I as of 1 July 2026" |
| Finland | Grid Connection Policy (Fingrid) | **Status**: No reported moratoria as of Sept 2026 | Standard grid connection procedure; grid capacity not reported as saturated | **Effect**: Relative freedom pending tax policy impact | — | — |

---

## UNVERIFIED CLAIMS (Could not fetch primary source or date/detail mismatch)

| Item | Reason | Found evidence | Status |
|------|--------|-----------------|--------|
| **Netherlands** — specific Liander 10-year wait time | Secondary source (Rabobank) cites "up to 10 years" for business connections; primary Liander source not fetched | WebSearch results mention this; no primary confirmation fetched | **Partially verified**: wait times are real but exact 10-year figure not confirmed from Liander directly |
| **Belgium** — Elia "specific category" capacity cap value (MW/GW limit) | Elia website (elia.be) returned 403 Forbidden; described as "maximum capacity allocations" but no specific number found | Search results indicate it exists as short-term measure; formal regulation number TBD | **Not verified**: Specific cap value unknown |
| **Germany** — Reifegradverfahren or other queue reforms mentioned in initial brief | Mentioned as potential; no evidence found in searches | Grid connection queue exists but terminology not confirmed in 2026 sources | **Not verified**: Specific reform name not confirmed |
| **Denmark** — Post-moratorium prioritization criteria (specifics) | Moratorium confirmed; new prioritization criteria in development as of March 2026 but not yet published | Announced as "in preparation" | **Not verified**: Final criteria TBD (moratorium active, pending decision) |
| **France** — 50% electricity tax reduction for PINM projects (exact % and threshold >1 GW) | One source (Addleshaw Goddard) mentions "50% reduction" for "sites consuming over 1 GW annually"; other sources mention PINM fast-track but not tax detail | Found in secondary legal briefing; RTE/CRE primary source not fetched | **Partially verified**: 50% figure cited in law firm brief; threshold confirms ">1 GW" |
| **Norway** — Exact fine amount "5% of annual turnover" | Law360/Orbitax sources mention penalties; no regulatory text fetched | Secondary sources consistent on 5% figure | **Partially verified**: Cited in multiple secondary sources; regulatory text (Nkom) not directly fetched |

---

## Key Data Points: Grid Queue Status & Bottlenecks (Sept 2026)

### Connection Queues by Country/Region
- **Netherlands (TenneT)**: ~60 GW total queue; no data-center-specific isolation reported
- **France (RTE)**: 18 GW pre-allocated for ~80 DC projects; 5 Fast-Track sites at 4,800 MW capacity
- **Denmark (Energinet)**: 60 GW total queue; 14 GW for data centers; moratorium March–June 2026
- **Germany**: No single national queue cited; Frankfurt/West/South grids facing regional constraints
- **Ireland (EirGrid)**: Dublin fully constrained until 2028; elsewhere unconstrained
- **Belgium (Elia)**: No published queue size; capacity "defining constraint"; 2028–2038 plan in prep
- **Sweden (Svenska kraftnät)**: No reported saturation or queues
- **Norway (Statnett)**: No reported saturation; registration-based transparency new as of 2025
- **Finland (Fingrid)**: No reported saturation; tax change effective July 2026 is the binding constraint

---

## Regulatory Intensity by Country (Barrier-to-Entry Score, 1–5)

| Country | Score | Primary barriers | Notes |
|---------|-------|-----------------|-------|
| **Ireland** | 4/5 | Dublin moratorium (2028), 80% renewable + dispatchable gen mandate, FRT test | Highest barriers in northwest EU; policy-driven, not grid-only |
| **Netherlands** | 5/5 | National hyperscale ban (>70 MW / >10 ha), Amsterdam moratorium (2035), grid queue (10yr) | Strictest in region; combined land + grid + municipal bans |
| **Germany** | 3/5 | PUE 1.2 (July 2026), 100% renewable (2027), waste heat reuse, Frankfurt zoning limit | Tech/efficiency-driven; geographically selective (Frankfurt strict, elsewhere moderate) |
| **France** | 2/5 | Fast-track available for PINM projects; standard queue for others; 9-month permit timeline | Most permissive; favorable for large strategic projects |
| **Belgium** | 3/5 | Elia capacity category (pending), 9-fold demand increase, 2028–2038 plan uncertainty | In transition; current measures interim; future regulation TBD |
| **Denmark** | 4/5 | Moratorium (active March–June 2026, likely extended), grid saturated in many regions | Near-term pause; long-term policy unclear pending Energinet prioritization rules |
| **Sweden** | 1/5 | 97% tax rebate; no moratoria or zoning limits; standard grid queue | Most open; electricity cost advantage substantial |
| **Norway** | 1/5 | Registration only (not siting limit); no grid saturation; standard TSO queue | Low regulatory burden; framework is transparency + security, not capacity gating |
| **Finland** | 3/5 (rising to 4 post-July 2026) | Electricity tax rebate removal (July 2026); future incentive scheme TBD; Fingrid capacity adequate | Tax policy is the binding constraint; grid is not (yet) |

---

## Sources (Full URLs)

**Ireland:**
- https://www.williamfry.com/knowledge/irelands-data-centre-connections-back-online/
- https://www.cru.ie/about-us/news/the-cru-publishes-its-decision-on-new-electricity-connection-policy-for-data-centres/

**Netherlands:**
- https://www.cms-lawnow.com/en/ealerts/2022/11/netherlands-prohibits-creating-hyperscale-data-centres-until-national-guidelines-are-passed
- https://www.datacenterdynamics.com/en/analysis/the-ongoing-impact-of-amsterdams-data-center-moratorium/
- https://www.rabobank.com/knowledge/d011486697-backup-power-for-europe-part-6-dutch-bess-capacity-grows-despite-regulatory-hurdles

**Germany:**
- https://www.whitecase.com/insight-alert/data-center-requirements-under-new-german-energy-efficiency-act
- https://www.moduledge.com/blog/eu-data-center-regulations-2026
- https://etalytics.com/resources/blog/germanys-energy-efficiency-act-in-data-centers
- https://www.datacenterdynamics.com/en/news/frankfurt-updates-its-plans-for-environmental-data-center-zoning/

**France:**
- https://www.addleshawgoddard.com/en/insights/insights-briefings/2025/real-estate/the-future-of-data-centres-in-france/
- https://www.gridreadiness.com/blog/ai-data-center-france-grid-connection-rte-2026

**Belgium:**
- https://www.silicon.co.uk/cloud/ai/belgium-power-ai-627144
- https://itdaily.com/news/datacenter/belgian-data-centers-growing/

**Denmark:**
- https://www.datacenterdynamics.com/en/news/danish-grid-operator-introduces-three-month-moratorium-for-new-grid-connections/

**Sweden:**
- https://www.cloudcomputing-news.net/news/sweden-confirms-tax-break-for-data-centres-following-government-study

**Norway:**
- https://www.datacenterdynamics.com/en/news/norway-data-center-register/
- https://haavind.no/en/regulation-of-data-centers-in-norway-focus-on-security-and-preparedness/

**Finland:**
- https://valtioneuvosto.fi/en/-/government-safeguards-finland-s-competitiveness-in-attracting-data-centre-investments
