# Who decides where a European data center gets built

Research date: 2026-09-26. Every claim below carries a source that was fetched and read on that date. Raw notes from the three research streams are in `raw/` (A: roles, B: process, C: market and tools); anything they assert that is not repeated here was not verified and should not be quoted.

## Short answer

Nobody "picks a site" in one act. A site survives a funnel, and different people own different gates:

1. **Market thesis** (weeks 1–8). Demand side (hyperscaler capacity planning) or supply side (developer scanning markets for power and zoning).
2. **Site screen** (weeks 4–16). A site-selection or site-acquisition team screens candidate sites against a multi-criteria matrix, power first. Sites with no credible power pathway die here.
3. **Land control, grid application, permits** (months 3–24+). Grid is the longest pole.
4. **Recommendation and approval.** The site team *recommends*; approval sits above them (named only as "for approval" in job postings) and ends in a **Final Investment Decision** that needs lease, financing, EPC contract, permits, interconnection agreement *and board approval* in place at the same time.

The person who runs the screen is not the person who pulls the trigger. The screener's output has to survive being handed to finance, lenders and a board.

## Who does what (verified)

| Actor | What they do in siting | Source |
|---|---|---|
| Hyperscaler site-acquisition team (Microsoft: Senior Director Site Acquisition EMEA → Site Acquisition Director → Site Acquisition Managers) | "develop high quality metro strategies based on market expertise, with time to market and cost efficiencies being core"; "Lead cross functional teams to evaluate, select, negotiate and recommend leases for approval"; "Work with Finance reps to conduct Total Cost of Ownership (TCO) lease or build options"; coordinates with "capacity planning, network, energy, security, engineering". Pay band £100k–£200k. | [LinkedIn, Microsoft Site Acquisition Director, London, fetched 2026-09-26](https://uk.linkedin.com/jobs/view/site-acquisition-director-at-microsoft-4451066734) |
| Neocloud / AI-infra site selection (Nebius, Verda) | Dedicated "Site Selection Manager" roles scoped to EMEA; smaller orgs merge selection and colocation leasing into one role. | [raw/A-roles.md](raw/A-roles.md) (LinkedIn postings, 2026-08/09) |
| Developers (Equinix, Digital Realty, Vantage…) | "translate that demand into built facilities by acquiring land, managing entitlements, negotiating with utilities, and arranging financing." | [Global Data Center Hub, 2026-05-16](https://www.globaldatacenterhub.com/p/how-to-underwrite-the-hyperscale) |
| Investors (infra funds, REITs, sovereign wealth) | Capital enters at different phases; lenders underwrite on tenant credit, lease cash flows and power certainty. "These deals are not getting financed without firm, real power-delivery dates" (Sean Farney, JLL). | Same; [DCK, 2026-09-09](https://www.datacenterknowledge.com/data-center-site-selection/power-availability-now-determines-where-data-centers-get-built) |
| Board | Power procurement "a priority at board level"; board approval is one of the FID preconditions. | [Osborne Clarke, 2026-04-07](https://www.osborneclarke.com/insights/how-investors-are-managing-risk-new-wave-european-data-centre-projects); Global Data Center Hub |
| Advisors (CBRE, JLL, Cushman & Wakefield, Arup, Linesight, Knight Frank, Savills, Turner & Townsend) | Run site selection and due diligence *for* the above. C&W: "real-time view of supply, demand, pricing and power availability"; their market comparison scores 107 markets on 24 weighted variables. Pricing not public. | [C&W data centers page, fetched 2026-09-26](https://www.cushmanwakefield.com/en/industries/data-centers); [raw/C-market-tools.md](raw/C-market-tools.md) |

**Still unverified:** the name of the body that approves a hyperscaler lease or build (the posting says only "for approval"), and how investment committees at colocation developers are composed. No public source found; this needs interviews.

## What decides the site (verified, ranked)

1. **Deliverable power, on a date.** "Site selection in 2026 is driven primarily by deliverable power. If developers cannot secure megawatts on a predictable timeline, incentives, land costs, and fiber connectivity become secondary." (Assad Noori, EMEA head of data centers, JLL). "Cost and delivery timeline are now co-equal with availability." [DCK, 2026-09-21](https://www.datacenterknowledge.com/data-center-site-selection/grid-constraints-steer-dutch-data-centers-beyond-amsterdam)
2. **Time to revenue over price.** "There's more of a focus on time to revenue than cost." (Farney, JLL). "The most attractive market is not necessarily the one with the cheapest electricity." (Siddharth Muzumdar, DC Byte). Plans should "stress-test 12-, 24-, and 36-month delay scenarios." [DCK, 2026-09-09](https://www.datacenterknowledge.com/data-center-site-selection/power-availability-now-determines-where-data-centers-get-built)
3. **The search now starts from power.** "The key shift is from asking, 'Where do we want to build?' to 'Where can we actually secure and deliver the power?'" (Muzumdar). Same source.
4. **Grid acceptance is rare.** Germany: "Only around 10-15% of grid applications for data centres will be accepted." The planned *Reifegradverfahren* will prioritise projects with "land already secured, a robust technical concept and credible financing." [Osborne Clarke, 2026-04-07](https://www.osborneclarke.com/insights/how-investors-are-managing-risk-new-wave-european-data-centre-projects)
5. **Equipment lead time.** Transformers "up to three years" (Noori, JLL); substation transformers "exceeding 160 weeks" (Global Data Center Hub).
6. **Then** connectivity, permitting and zoning, water, flood risk, land. Amsterdam halted new large data centers in June 2025; Dutch national policy bars hyperscale (≥10 ha and 70 MW) from most of the country. [DCK, 2026-09-21](https://www.datacenterknowledge.com/data-center-site-selection/grid-constraints-steer-dutch-data-centers-beyond-amsterdam). Linesight: FLAP-D growing ~16%, "Southern Europe and the Nordics… 30-55% over the next year." [Linesight, 2025-07-07](https://www.linesight.com/en-us/insights/beyond-real-estate-navigating-the-complexities-of-data-centre-site-selection/)

**Regulation that touches every EU site ≥500 kW IT.** Operators must report energy, PUE, water, renewable share and waste-heat KPIs to the EU database every year (first by 15 Sep 2024, then every 15 May). [Delegated Regulation (EU) 2024/1364, EUR-Lex](https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj)

## Who else sells into this workflow (verified)

- **Enverus Data Center Siting**: targets developers, industrial load developers and investors. "filter 156M land parcels", withdrawal capacity at "23,000+ interconnection points", "Forecast electricity prices across scenarios". It is US-centric (LMP nodes, US parcels). [enverus.com, fetched 2026-09-26](https://www.enverus.com/products/data-center-siting-solutions/)
- **LandGate, Paces, Nira Energy, Transect**: US-focused siting platforms (per raw/C). **DC Byte, DatacenterHawk, Baxtel, 451 Research, Structure Research, TeleGeography**: market-intelligence databases on facilities rather than site screening. Pricing is not public for any of them.
- The European gap: no fetched source showed a pan-European, grid-aware *site screen* aimed at the site-selection analyst. Advisors fill that gap with bespoke work.

## What this means for the product

**Primary user: the site-selection / site-acquisition analyst or manager**, at a developer, a neocloud, or an advisory firm working for one. They run phase 2 (market → shortlist) under time pressure and need a defensible shortlist quickly. They are expert and numerate, and they will open the tool many times per project.

**Secondary reader: whoever approves.** That means finance (TCO), the investment committee, the board and lenders. They never touch the tool. They read its export, and the export must show *why* each site ranks where it does and what the numbers rest on. This is the real meaning of the existing "CFO-legible" constraint.

**Honest gaps in the current model** (algo is out of scope for this pass; recorded so they are not oversold):
- The model scores *congestion* (a proxy), not *deliverable MW by date*, which is the factor the industry ranks first. The UI must label it as a proxy.
- There is no connection-queue, transformer-lead-time or permitting-risk input.
- Day-ahead prices come from power exchanges. Energy-Charts licenses 16 zones CC BY 4.0 and restricts the rest to private use; ENTSO-E's free re-use list does not include day-ahead prices either (per [entsoemcp.com/licensing](https://entsoemcp.com/licensing), which cites ENTSO-E's list of 18 Oct 2023; the list PDF itself was not fetched). A commercial launch needs an exchange data licence (EPEX / Nord Pool).
