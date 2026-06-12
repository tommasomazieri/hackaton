# DC Siting Intelligence Tool — Hackathon

SaaS tool that recommends optimal European data center locations given compute load, carbon budget, and cost priority. Clients pay per query. See `docs/challenge.md` for full problem framing.

## Project Layout

```
docs/           challenge framing + architecture decisions
challenges/     original hackathon PDF
src/            application code (TBD)
data/           cached/processed data assets
```

## Key Constraints

- MVP must return ≥3 ranked EU sites with trade-off explanation + supply mix in <30s
- Output must be readable by a non-engineer (CFO-legible)
- Europe only for hackathon scope

## Data Sources

| Source | What | Access |
|---|---|---|
| PyPSA-Eur | Grid topology, nodal prices, headroom | Python library |
| Ember | Carbon intensity time series | CSV/API |
| OpenStreetMap | Fiber, substations | osmnx / Overpass API |
| IEA Energy & AI | Demand projections | Reference only |

## Dev Commands

<!-- fill in once stack is decided -->

## Important

- No committing `.env` or API keys
- `docs/challenge.md` is the canonical problem definition — update it if scope changes
- All site scoring logic must be explainable (no black-box ML for MVP)
