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
| files | .codemapper_cache.json | 0 |  |  |  |
| .mcp.json | .mcp.json | 0 |  |  |  |
| codemapper2 | .mcp.json | 0 |  |  |  |

## Communities

- Community **4**: 16 nodes — representative: `project.json` (project-management/project.json)
- Community **0**: 12 nodes — representative: `challenge.md` (docs/challenge.md)
- Community **2**: 8 nodes — representative: `settings.json` (.claude/settings.json)
- Community **1**: 7 nodes — representative: `CLAUDE.md` (CLAUDE.md)
- Community **5**: 5 nodes — representative: `.codemapper_cache.json` (.codemapper_cache.json)
- Community **6**: 5 nodes — representative: `kanban.json` (project-management/kanban.json)
- Community **3**: 4 nodes — representative: `.mcp.json` (.mcp.json)
- Community **7**: 3 nodes — representative: `wip_limits` (project-management/project.json)
- Community **8**: 2 nodes — representative: `open-pm.sh` (project-management/open-pm.sh)
- Community **9**: 1 nodes — representative: `backlog.json` (project-management/backlog.json)

## Quality Signals

Dead code / dead files: **0** nodes flagged

## Suggested queries
- `explore("settings.json architecture")`
- `explore("how does settings.json relate to $schema")`
- `god_nodes(stale_only=True)` — files with outdated docstrings
- `god_nodes(dead_only=True)` — dead-code candidates
