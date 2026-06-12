# Challenge: Data-Center Siting & Power (Invertix)

## Problem Statement

AI is driving a wave of new data centers across Europe and globally. The binding constraint is no longer land or hardware — it is **electricity**: availability, price, carbon intensity, and grid headroom. Siting decisions are currently made by expensive consultants or internal teams with patchy, siloed data. The process is slow, opaque, and inaccessible to smaller players.

## Business Framing — What We're Building

We are building a **SaaS siting intelligence tool** that replaces the consultant.

A client — a DC developer, hyperscaler, or energy investor — inputs their requirements. The tool returns ranked candidate sites across Europe with quantified trade-off explanations and a recommended power supply mix. They pay per query or via subscription.

This is not a one-off analysis. It is a product other people pay to use.

## Target Users & Jobs-to-be-Done

| User | Job |
|---|---|
| DC developer | Pre-feasibility screening across 10+ EU countries in hours, not weeks |
| Hyperscaler expansion team | Identify regions with grid headroom + low carbon before committing to land |
| Energy/infrastructure fund | Score a portfolio of candidate sites consistently and quickly |

**Core query the tool answers:**
> "Show me the top EU locations for a 50 MW data center with carbon intensity below 200 gCO₂/kWh — explain the trade-offs and give me the cheapest power supply mix for each."

## Core Trade-offs the Tool Resolves

| Dimension | Tension |
|---|---|
| Cost vs Carbon | Cheap coal-heavy grids vs expensive but green regions |
| Grid headroom vs Congestion | Unconstrained periphery vs overloaded hubs near demand |
| PPA availability vs On-site capex | Cheap wind/solar PPAs where curtailment is high vs on-site gen where grid is weak |
| Connectivity | Fiber-dense urban areas vs greenfield sites with power but no backhaul |

## Power Supply Mix — Key Concepts

Data centers have three ways to source electricity. Our tool recommends the optimal blend per site:

| Option | What it is | Best when |
|---|---|---|
| **Grid** | Buy at spot / day-ahead wholesale market | Grid is already cheap and low-carbon (Nordics, France nuclear) |
| **PPA** | Long-term contract (10–25 yr) direct with a renewable generator at a fixed €/MWh | High renewable curtailment zones — generator discounts rate for revenue certainty |
| **On-site generation** | Build own solar, battery, or backup generator on the DC plot | Grid is unreliable, very expensive, or site is remote |

**PPA in detail:** A Power Purchase Agreement is a bilateral contract between the DC operator (buyer/offtaker) and a wind or solar farm (generator). The DC commits to buy X MWh at a fixed price for the contract term. Electrons still flow through the public grid — the PPA is a financial layer on top. In practice: generator sells to grid at spot, DC buys from grid at spot, and the fixed/spot price difference is settled financially (a Contract for Difference). The DC gets price certainty + renewable energy certificates (Guarantees of Origin) to support carbon claims.

**Why PPAs are cheap in curtailment zones:** In regions where wind/solar generation exceeds local grid capacity (e.g., Scottish Highlands, western Ireland, Iberian interior), generators are sometimes forced to switch off despite producing free-fuel electricity. A DC willing to sign a long-term offtake agreement removes that risk for the generator — who then offers a below-market rate. Our tool identifies these zones as high-PPA-opportunity.

## Product Scope — Hackathon MVP

A web app or AI agent that:

1. Takes structured user inputs (DC size, carbon budget, cost priority, optional region filter)
2. Queries and scores EU locations across cost, carbon, congestion, and connectivity dimensions
3. Returns a ranked shortlist of sites with per-dimension scores and narrative explanation
4. Recommends a power supply mix (grid / PPA / on-site generation) per top site

## Key Input → Output Contract

**Inputs:**
- Target load (MW)
- Max carbon intensity (gCO₂/kWh) — hard constraint or weighted preference
- Cost priority (low / balanced / carbon-first)
- Region preference (optional — e.g., "Nordics only")

**Outputs:**
- Ranked list of ≥3 EU candidate sites
- Per-site scores: electricity cost, carbon intensity, grid congestion risk, connectivity
- Recommended supply mix per site: % grid, % PPA, % on-site generation
- Plain-language explanation of why each site ranks as it does

## Data & Tools Available

| Source | What it provides |
|---|---|
| **PyPSA-Eur** | European grid topology, power flows, nodal prices, grid headroom |
| **Ember** | Hourly/daily carbon intensity time series by country and zone |
| **OpenStreetMap** | Fiber infrastructure, substation locations, accessibility |
| **IEA Energy & AI** | Data center demand projections, policy context |
| **Google Alphaearth** | Satellite imagery for physical site suitability (land, cooling, proximity) |

## Success Criteria

- Given valid inputs, system returns ≥3 ranked EU locations within 30 seconds
- Each result includes a score breakdown and supply mix recommendation
- A non-expert (e.g., a CFO, not a grid engineer) can understand and act on the output
- Trade-off explanations reference real data, not placeholders

## Out of Scope

- Permitting, planning law, physical construction details
- Non-EU markets (stretch goal only if time allows)
- Real-time grid telemetry / live dispatch data
- Financial modeling beyond levelized cost of electricity (LCOE) approximations
