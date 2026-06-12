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
| src/data_ingestion/download_datasets.py | .codemapper_cache.json | 0 |  |  |  |
| files | .codemapper_cache.json | 0 |  |  |  |
| src/data_ingestion/download_datasets.py | .codemapper_cache.json | 0 |  |  |  |

## Communities

- Community **17**: 22 nodes — representative: `data.md` (docs/data.md)
- Community **24**: 19 nodes — representative: `journey-before.json` (artifacts/journey-before.json)
- Community **4**: 19 nodes — representative: `project.json` (project-management/project.json)
- Community **15**: 18 nodes — representative: `tasks-draft.md` (docs/tasks-draft.md)
- Community **20**: 16 nodes — representative: `stakeholder-map.md` (artifacts/stakeholder-map.md)
- Community **25**: 15 nodes — representative: `journey-before.md` (artifacts/journey-before.md)
- Community **5**: 14 nodes — representative: `.codemapper_cache.json` (.codemapper_cache.json)
- Community **21**: 13 nodes — representative: `personas.md` (artifacts/personas.md)
- Community **26**: 12 nodes — representative: `jtbd.md` (artifacts/jtbd.md)
- Community **7**: 12 nodes — representative: `persona.md` (artifacts/persona.md)

## Quality Signals

Dead code / dead files: **1** nodes flagged
Top stale docstrings: `download_datasets.py`
Top complexity: `download_file()` (7)

## Suggested queries
- `explore("settings.json architecture")`
- `explore("how does settings.json relate to $schema")`
- `god_nodes(stale_only=True)` — files with outdated docstrings
- `god_nodes(dead_only=True)` — dead-code candidates
