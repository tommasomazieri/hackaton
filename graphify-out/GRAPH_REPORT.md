# Codebase Knowledge Graph Report

## God Nodes (most architecturally central files)

| label | source_file | degree | complexity | stale | dead |
|---|---|---|---|---|---|
| settings.json | .claude/settings.json | 0 |  |  |  |
| $schema | .claude/settings.json | 0 |  |  |  |
| permissions | .claude/settings.json | 0 |  |  |  |
| deny | .claude/settings.json | 0 |  |  |  |
| hooks | .claude/settings.json | 0 |  |  |  |
| PreToolUse | .claude/settings.json | 0 |  |  |  |
| SessionStart | .claude/settings.json | 0 |  |  |  |
| Stop | .claude/settings.json | 0 |  |  |  |
| .codemapper_cache.json | .codemapper_cache.json | 0 |  |  |  |
| version | .codemapper_cache.json | 0 |  |  |  |
| root | .codemapper_cache.json | 0 |  |  |  |
| mtimes | .codemapper_cache.json | 0 |  |  |  |
| src/main.py | .codemapper_cache.json | 0 |  |  |  |
| src/data_normalization/01_carbon_emissions.py | .codemapper_cache.json | 0 |  |  |  |
| src/data_normalization/02_energy_price.py | .codemapper_cache.json | 0 |  |  |  |

## Communities

- Community **17**: 33 nodes — representative: `data.md` (docs/data.md)
- Community **38**: 28 nodes — representative: `app.js` (src/frontend/app.js)
- Community **100**: 24 nodes — representative: `TO_BE_ARCHITECTURE.md` (src/model/TO_BE_ARCHITECTURE.md)
- Community **45**: 22 nodes — representative: `mtimes` (.codemapper_cache.json)
- Community **5**: 22 nodes — representative: `market_context` (artifacts/market-viability.json)
- Community **98**: 20 nodes — representative: `api.py` (src/model/api.py)
- Community **24**: 19 nodes — representative: `journey-before.json` (artifacts/journey-before.json)
- Community **4**: 19 nodes — representative: `project.json` (project-management/project.json)
- Community **33**: 19 nodes — representative: `04_infrastructure_access.py` (src/data_normalization/04_infrastructure_access.py)
- Community **18**: 18 nodes — representative: `01_carbon_emissions.py` (src/data_normalization/01_carbon_emissions.py)

## Quality Signals

Dead code / dead files: **15** nodes flagged
Top stale docstrings: `__init__.py`, `api.py`
Top complexity: `_normalise_long()` (26), `run()` (18), `run()` (14), `_load_from_cache_or_fetch()` (11), `_assign_land_price()` (11)

## Suggested queries
- `explore("settings.json architecture")`
- `explore("how does settings.json relate to $schema")`
- `god_nodes(stale_only=True)` — files with outdated docstrings
- `god_nodes(dead_only=True)` — dead-code candidates
