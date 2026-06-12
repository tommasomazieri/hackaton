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
| GridFM (Microsoft Research) | Foundation model initiative for electric grid physics — umbrella project | https://microsoft.com/en-us/research/project/gridfm |
| GridSFM (Microsoft Research) | AC-OPF foundation model: predicts bus voltages, branch flows, congestion, headroom in milliseconds. GridSFM-Open (~15M params) open source. Replaces/augments PyPSA static snapshots for congestion scoring. Risk: existing dataset is US-focused; EU topology construction needed. | HuggingFace: microsoft/gridsfm · GitHub: microsoft/GridSFM |
| gridfm-datakit | Python lib for generating synthetic power flow / OPF datasets. Can generate E3c ML training data for our RF classifier. | github.com/gridfm/gridfm-datakit |

## Dev Commands

<!-- fill in once stack is decided -->

## Important

- No committing `.env` or API keys
- `docs/challenge.md` is the canonical problem definition — update it if scope changes
- All site scoring logic must be explainable (no black-box ML for MVP)
