# Contract: Migration Matrix

The migration matrix was the required inventory before standalone
`oracle-query` removal. It may be implemented as Markdown, CSV, JSON, or YAML
during `/speckit.tasks`, but it must preserve the fields and rules below.

## Required Fields

| Field | Required | Description |
|---|---:|---|
| `legacy_path` | yes | Command, skill, hook, script, MCP server, README section, or config entry being migrated. |
| `owner` | yes | Owning area: `skill`, `hook`, `mcp`, `script`, `docs`, `settings`, or `test`. |
| `current_behavior` | yes | Current user-visible behavior and response semantics. |
| `replacement_behavior` | yes | New workflow behavior or explicit retirement rationale. |
| `status` | yes | One of `delegated`, `replaced`, `retired`, or `blocked`. |
| `active_consumers` | yes | Named active consumers, or `none`. |
| `exact_shape_required` | yes | Boolean. True only when a named active consumer requires legacy response shape. |
| `acceptance_tests` | yes | Tests that must pass for this row. |
| `audit_impact` | yes | How the path writes canonical audit records after migration. |
| `migration_notes` | yes | User-visible docs or command guidance. |
| `rollback_notes` | yes | How to restore prior behavior if migration fails. |

## Required Initial Inventory Targets Before Deprecation

- `.claude/skills/oracle/SKILL.md`
- `.claude/skills/oracle-debate/SKILL.md`
- `.claude/skills/oracle-observe/SKILL.md`
- `.claude/skills/oracle-preclear/SKILL.md`
- `.claude/skills/oracle-synthesize/SKILL.md`
- `scripts/mcp_server.py`
- `mcp/oracle-query/server.py`
- `mcp/oracle-query/README.md`
- `scripts/review_oracle_queries.py`
- `scripts/precompact_oracle_nudge.py`
- `scripts/userprompt_oracle_capture_nudge.py`
- `.decisions/queries/*.jsonl`
- `.decisions/phi/*.md`
- `README.md`
- `CLAUDE.md`

## Status Rules

- `delegated`: legacy path remains callable and delegates to the native workflow.
- `replaced`: legacy path has a direct replacement and old path no longer owns behavior.
- `retired`: legacy behavior is explicitly not carried forward, with user-approved rationale.
- `blocked`: migration cannot proceed until listed blocker is resolved.

## Removal Gate

Standalone `mcp/oracle-query` removal was blocked until:

- native query acceptance tests pass;
- native capture acceptance tests pass;
- pre-clear candidate tests pass;
- the migration matrix covers every documented legacy path;
- exact response shape is preserved for every named active consumer that requires it;
- compatibility shims write canonical audit records with source markers;
- migration notes and rollback instructions exist;
- explicit user approval is recorded;
- one manual dogfood session completes with no blocking regressions.
