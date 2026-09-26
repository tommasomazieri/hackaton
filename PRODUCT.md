# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

**Primary: the site-selection / site-acquisition analyst or manager** at a data-center developer, a neocloud, or an advisory firm working for one. They run the site screen (market → shortlist) under time pressure. They are expert and numerate, open the tool many times per project, and need a shortlist they can defend. This comes from desk research (`docs/research/dc-siting-decision-process.md`) and has not yet been validated with real users.

**Secondary: the approvers.** Finance (TCO), the investment committee, the board and lenders. They never open the tool; they read its export. The export must stand alone: why each site ranks where it does, and what data each number rests on.

**Who will actually open it right now is unknown** (confirmed by the owner): the team itself, possibly investors, possibly prospective customers. Treat every first visit as cold. It must make sense within seconds to someone who has never seen it, without talking down to a domain expert.

## Product Purpose

DC Hound screens every candidate grid node in Europe for a data center of a given size and footprint. It returns a ranked shortlist scored on grid congestion, carbon, cost and connectivity, with the weighting under the user's control. For each shortlisted node it can analyse satellite imagery to find buildable land nearby. Success means an analyst goes from "which countries?" to a defensible, exportable shortlist in minutes rather than weeks of consultant work.

## Positioning

A pan-European, grid-aware site screen built for the analyst, where every number traces back to a named public source with its licence and freshness. The fetched sources show competitors are either US-centric (Enverus, LandGate, Paces), market-intelligence databases on existing facilities (DC Byte, datacenterHawk), or bespoke advisory work (CBRE, JLL, Cushman & Wakefield). The CNN buildable-land check on satellite imagery sits in the same flow as the grid screen.

## Operating Context

- Industry decision funnel: market thesis → **site screen (DC Hound's job)** → land, grid application, permits → recommendation and final investment decision (lease, financing, EPC, permits, interconnection and board approval together).
- What the industry ranks first in 2026 is deliverable megawatts by a date, then time to revenue over cost, then connectivity, permits, water and land. Sources are in the research doc.
- The export (PDF) is how results leave the tool and reach approvers.
- Hackathon origin: the Invertix data-center siting challenge, June 2026. The project is now part of the owner's portfolio and is meant to work for real, not as a demo.

## Capabilities and Constraints

- Inputs: capacity (MW), footprint (m²), optional country whitelist, and weights on the four scored metrics.
- Outputs: every surviving node ranked, with raw values, cost split (energy vs land), consumption stats, and the country generation mix (coal, gas, oil, nuclear, hydro, wind, solar, bioenergy, other renewables).
- Per-node buildable-land analysis (Sentinel-2 plus a Dynamic World CNN). The first run per node takes tens of seconds; after that it is cached.
- Data is fetched live from public sources with a TTL cache: Eurostat GISCO, OWID, Eurostat land prices, Energy-Charts day-ahead prices, OSM Overpass substations and PeeringDB. Provenance, freshness and licence are exposed at `/api/sources`.
- Europe only. At least 3 ranked sites in under 30 s. Scoring must stay explainable (no black-box ML in ranking).
- **Stated limits that the UI must never oversell:**
  - "Congestion" is a proxy, not deliverable MW by date.
  - There is no connection-queue, transformer-lead-time or permitting-risk input.
  - Land price is agricultural land, not industrial.
  - Day-ahead prices for 16 zones are CC BY 4.0; the rest are private-use only, so a commercial launch needs an exchange data licence.
- The model/algorithm side is out of scope for UI work: the UI presents it and does not change it.

## Brand Commitments

- Name: **DC Hound** (singular; confirmed).
- Feel volunteered by the owner: a precision instrument. Dense, quiet and numbers-first, with the map as the hero.
- Anti-references volunteered by the owner: generic SaaS dashboards, and crypto or neon dark mode.

## Evidence on Hand

- Research: `docs/research/dc-siting-decision-process.md`, with raw notes in `docs/research/raw/`.
- Methodology and data lineage: `docs/methodology.md`.
- Cached site analyses with satellite renders: `data/site_analysis/*.json|png` (131 nodes).
- Absent, and not to be fabricated: customers, testimonials, pricing, usage numbers, accuracy benchmarks, partnerships.

## Product Principles

1. **Power first.** The industry screens on power before anything else, so grid factors lead and are labelled honestly (proxy where proxy).
2. **Every number is traceable.** Source, date and licence are one step away from any figure, both in the UI and in the export.
3. **The export is the product for the people who decide.** It must stand alone for someone who never saw the tool.
4. **The analyst is in control.** Weights, country filters and the ranking stay visible and editable; no hidden defaults decide the answer.
5. **Cold visitors get it immediately.** The first screen shows a real ranked result, not an empty form.
