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

- Community **4**: 19 nodes — representative: `project.json` (project-management/project.json)
- Community **5**: 14 nodes — representative: `.codemapper_cache.json` (.codemapper_cache.json)
- Community **7**: 12 nodes — representative: `persona.md` (artifacts/persona.md)
- Community **20**: 12 nodes — representative: `stakeholder-map.md` (artifacts/stakeholder-map.md)
- Community **0**: 12 nodes — representative: `challenge.md` (docs/challenge.md)
- Community **14**: 11 nodes — representative: `challenge_it.md` (docs/challenge_it.md)
- Community **21**: 10 nodes — representative: `personas.md` (artifacts/personas.md)
- Community **15**: 10 nodes — representative: `Epics & Tasks` (docs/tasks-draft.md)
- Community **2**: 8 nodes — representative: `settings.json` (.claude/settings.json)
- Community **16**: 8 nodes — representative: `SKILL.md` (.agents/skills/analytical-siting-evaluator/SKILL.md)

## Quality Signals

Dead code / dead files: **1** nodes flagged
Top stale docstrings: `download_datasets.py`
Top complexity: `download_file()` (7)

## Suggested queries
- `explore("settings.json architecture")`
- `explore("how does settings.json relate to $schema")`
- `god_nodes(stale_only=True)` — files with outdated docstrings
- `god_nodes(dead_only=True)` — dead-code candidates
