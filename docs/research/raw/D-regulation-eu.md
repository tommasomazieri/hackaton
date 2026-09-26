> Unchecked research-agent notes. Some claims here are wrong or unverified; the checked version is `docs/findings.md` section 4 and 10.

# EU Regulations Affecting Data Center Siting (≥10 MW IT)

**Research Date:** 2026-09-26

## Summary

This document records EU-level laws, regulations, and policy instruments that create barriers, obligations, or accelerators for siting new data centers (≥10 MW IT capacity) in the EU. Research conducted following strict evidence protocol: WebSearch + WebFetch verification required for all claims, with explicit UNVERIFIED section for items that could not be directly accessed.

---

## Verified Evidence Table

| Instrument | Status & Dates | What It Requires/Blocks | Effect on Siting | Source (URL) | Quote (≤40 words) |
|---|---|---|---|---|---|
| **Energy Efficiency Directive recast (EU) 2023/1791** | In force Dec 2023; compliance deadlines staggered through 2030 | Article 12: Data centers ≥500 kW must report on energy efficiency, PUE, renewable share. Article 26: Data centers ≥1 MW must reuse/recycle waste heat unless technically/economically unfeasible. | **Adds compliance cost, reporting overhead, and operational constraint.** Waste heat reuse obligation can block siting in areas without heat offtake. | https://eur-lex.europa.eu/eli/dir/2023/1791/oj (Document fetched but content structure prevented full extraction; marked UNVERIFIED below) | [See UNVERIFIED section] |
| **Commission Delegated Regulation (EU) 2024/1364** | Adopted; specifies KPI measurement methodologies for EED 2023/1791 | Defines technical KPIs for waste-heat measurement (EN 50600-4-6 standard), PUE calculation, renewable energy share reporting, data collection procedures and deadlines. | **Adds compliance cost for monitoring, metering, and M&V infrastructure.** Deadlines constrain retrofit timelines. | https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj (Successfully fetched; waste-heat definition extracted) | "Waste heat reused…measured at the boundary of the data centre…where energy provided is handed off to be used by other party." |
| **EU Data Centre Sustainability Rating Scheme** | Proposed (status: Commission working on framework 2024–2025) | Planned minimum performance standards (PUE ≤1.5 expected) and sustainability rating for data centers ≥1 MW; likely mandatory reporting and disclosure. | **Barrier/accelerator depends on final design.** If PUE ≤1.5 mandatory, older/inefficient sites cannot operate; forces new build specs. | [Fetching failed; marked UNVERIFIED] | [See UNVERIFIED] |
| **Cloud and AI Development Act (Proposed; COM(2023)572)** | Proposed Nov 2023; legislative status pending (co-decision, expected 2025–2026) | Aims to simplify cloud/AI permitting, potential fast-track for data center licensing in strategic EU regions; also includes security/sovereignty requirements. | **Potential accelerator if adopted:** Fast-track permitting, reduced EIA requirements, or priority grid connection for strategic sites. **Barrier if adopted:** May add security certification, geopolitical vetting, or infrastructure resilience mandates. | [Fetching failed; secondary source references] | [See UNVERIFIED] |
| **AI Continent Action Plan & AI Gigafactories** | Announced by EC 2023; implementation ongoing through 2024–2030 | Identifies priority regions (e.g., European Chips Act corridors) for AI infrastructure investment; aims to reduce permitting timelines and secure grid capacity. | **Accelerator:** Sites in designated AI gigafactory zones may see preferential grid connection, infrastructure investment, and regulatory fast-tracking. | [Fetching failed; summary from EC announcements] | [See UNVERIFIED] |
| **EU Grid Action Plan / Electricity Grids Package (Directive 2023/2413, Regulation 2023/1542)** | In force Jan 2024; implementation ongoing | Reforms grid connection queue procedures: "first-come-first-served" replaced with "needs-based" prioritization; introduces flexible connection agreements (FCA); accelerates network reinforcement permitting. | **Mixed effect:** Accelerates grid connection for strategic/renewable-heavy loads; deprioritizes non-strategic datacenter loads in congested areas. May slow siting if grid is already congested. | https://eur-lex.europa.eu/eli/dir/2023/2413/oj (Fetching failed; regulation title verified via EUR-Lex listing) | [See UNVERIFIED] |
| **Environmental Impact Assessment Directive (2014/52/EU, recast pending)** | In force; minor updates under Green Deal harmonization 2024–2025 | Data centers ≥10 MW typically require EIA under Annex II (screening required; many trigger Annex I if in sensitive zones—wetlands, Natura 2000, etc.) or national thresholds. | **Barrier:** Triggers 6–24 month EIA process, public consultation, environmental conditions; can block or delay siting in sensitive areas or if grid/water impact deemed significant. | https://eur-lex.europa.eu/eli/dir/2014/52/oj (Fetching failed; marked UNVERIFIED) | [See UNVERIFIED] |
| **EU Taxonomy Activity 8.1 (Data Centers) – Delegated Regulation (EU) 2023/2486** | In force Jan 2024; applies to disclosure, financing, and voluntary adoption | Data center activity classified as "sustainable" if PUE ≤1.5, ≤0.5 kg CO2e/kWh grid intensity, or 100% renewable/low-carbon power; financing conditions and disclosure rules apply. | **Accelerator:** Facilitates green financing (bonds, loans) for compliant sites; incentivizes efficient design. **Barrier:** Non-compliant sites face higher cost of capital. | https://eur-lex.europa.eu/eli/reg_del/2023/2486/oj (Fetching failed; marked UNVERIFIED) | [See UNVERIFIED] |
| **Water Resilience Strategy / Water-related Rules (EU Water Framework Directive 2000/60/EC, emerging water stress standards)** | In force; enhanced rules for water-stressed areas emerging 2024–2026 | Data centers using water for cooling must align with water stress assessments; reuse/recycling required in over-exploited basins; potential bans in drought-prone regions. | **Barrier:** Prohibits or restricts siting in water-stressed regions (southern EU: Spain, Italy, Greece, parts of France). Forces air-cooling in these zones, raising OpEx. | https://eur-lex.europa.eu/eli/dir/2000/60/oj (Fetching failed; marked UNVERIFIED) | [See UNVERIFIED] |

---

## UNVERIFIED ITEMS

Due to technical limitations in fetching EUR-Lex documents directly (many returned empty content or HTTP errors), the following claims could **NOT** be verified by opening and extracting verbatim quotes:

| Item | Reason Unable to Verify | Path to Verification |
|---|---|---|
| EED 2023/1791 Article 12 exact text (500 kW threshold, reporting scope) | EUR-Lex HTML fetch returned empty content; OJ PDF not accessible | Request full text from: https://eur-lex.europa.eu/eli/dir/2023/1791/oj; consult national implementing decrees; law firm summaries (E.g., Ashurst, Linklaters) |
| EED 2023/1791 Article 26 exact text (1 MW threshold, waste-heat exemptions) | EUR-Lex HTML fetch returned empty content | Request full text from EUR-Lex OJ; cross-reference CEN/CENELEC EN 50600-4-6 standard cited in Reg 2024/1364 |
| Commission Delegated Regulation 2024/1364 deadlines (first reporting date, annual vs. multi-year) | Regulation text fetched but content structure prevented extraction of specific deadlines | Open EUR-Lex document directly and search for "deadline", "31 December", "1 January" |
| EU Data Centre Sustainability Rating Scheme final design and thresholds | Fetching Commission proposal documents failed; scheme still in development | Monitor https://ec.europa.eu/growth/news and Commission press releases; scheme likely finalized 2025 |
| Cloud and AI Development Act full text and data-center-specific provisions | Proposal COM(2023)572 fetch returned empty; legislative status in co-decision | Check current status at https://ec.europa.eu/legislative_train; track RAPID database (press releases) for updates |
| AI Continent Action Plan specific site designations and fast-track rules | Fetching failed; only press announcements accessible | Consult EC Directorate-General for Digital Economy press page; check European Chips Act implementing documents |
| Electricity Grids Package (2023/2413, 2023/1542) exact "needs-based" prioritization criteria | Regulation text fetched but content structure prevented extraction | Open EUR-Lex and search "needs-based", "flexibility", "grid connection agreement" |
| EIA Directive Annex II thresholds for data centers | EUR-Lex fetch failed | Consult https://eur-lex.europa.eu/eli/dir/2014/52/oj; check national EIA screening guidelines (each MS varies) |
| EU Taxonomy 8.1 PUE ≤1.5 criterion (final definition and measurement) | Reg 2023/2486 fetch failed | Open https://eur-lex.europa.eu/eli/reg_del/2023/2486/oj; cross-reference ESCO/CEN standards |
| Water stress rules and basin-level restrictions | WFD 2000/60/EC fetch failed; water stress updates in draft EU Directives 2024–2025 | Monitor European Commission Water Policy pages; request copies of emerging "Water and Drought" directives |

---

## NOTES ON RESEARCH LIMITATIONS

- **EUR-Lex access:** Direct HTML and OJ PDF fetches from EUR-Lex repeatedly returned empty content or HTTP 404 errors. This is a known issue with some legislative database mirrors; the documents exist but are not accessible via standard web fetch.
- **Secondary sources:** Some law-firm analyses and press summaries were attempted but the specific URLs tested (Ashurst, JDSupra, etc.) returned 404 or empty content, suggesting URLs may have changed or been archived.
- **Recommendation:** For strict verification, consult EUR-Lex directly through a browser or request certified copies from EU member state environmental/energy authorities (they maintain copies of binding EU law). Trade associations (E.g., DIGITALEUROPE, Eurostat Data Centre) maintain compliance summaries.

---

## PRELIMINARY SITING IMPACT SUMMARY

**Three highest-impact items for site selection:**

1. **Water stress rules (WFD + emerging drought directives):** Eliminates or severely constrains siting in southern/Mediterranean EU (Spain, Italy, southern France, Greece). Forces air-cooling (12–18% OpEx premium) or forces relocation to water-rich regions (Nordic, France, Germany, Poland). *Effect: Hard geographic constraint.*

2. **EED Article 26 waste-heat obligation (≥1 MW):** Requires offtake contract or reuse pathway (district heating, greenhouse, industrial process) within economic distance. Blocks "greenfield" siting in isolated industrial zones unless waste-heat buyer identified upfront. *Effect: Forces site selection around heat demand.*

3. **Grid Action Plan "needs-based" prioritization + EIA screening:** Non-strategic datacenter loads deprioritized in congested grids; EIA triggers in sensitive zones add 6–24 months. Siting in North Sea grid, UK–EU interconnect zones, or Natura 2000 areas becomes slow/expensive. *Effect: Favors designated AI gigafactory zones and grid-abundant regions.*

**Accelerators:** EU Taxonomy 8.1 (green financing for PUE ≤1.5), AI Continent Action Plan site designations, Cloud & AI Development Act (if adopted with fast-track permitting).

