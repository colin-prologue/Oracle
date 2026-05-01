# CDR-mcp-tool-taxonomy — Hindsight MCP Tool Surface

**Date:** 2026-04-30
**Status:** Accepted
**ADR:** `ADR-mcp-server-integration.md`

## Tool inventory

Seven tools, organized by side-effect:

| Tool | Effect | Risk class |
|---|---|---|
| `hindsight_stats` | Read daemon stats | read-of-pre-existing-state |
| `hindsight_list_documents` | Read document list (with optional prefix filter) | read-of-pre-existing-state |
| `hindsight_recall` | Read corpus via embedding search; returns slim shape by default | read-of-pre-existing-state |
| `hindsight_retain_phi` | Write PHI to canonical bank | append-to-canonical-bank |
| `hindsight_retain_obs` | Write OBS to canonical bank | append-to-canonical-bank |
| `hindsight_retain_session_log` | Write session log to canonical bank (no document_id) | append-to-canonical-bank |
| `hindsight_log_query` | Append to `${HINDSIGHT_ROOT}/.decisions/queries/YYYY-MM.jsonl` | append-to-canonical-bank |

## Schema decisions

- **`recall` slim-by-default with `verbose` escape valve.** MCP server is the Claude-facing contract; optimizing the default shape for that audience is appropriate. Daemon HTTP API stays raw.
- **`retain_phi` and `retain_obs` schemas identical, tools separate.** Split-by-side-effect granularity preserves intent in audit logs and enables future per-tool gating without schema changes.
- **`context` field auto-mapped from tool name.** `retain_phi` → `'philosophy'`, `retain_obs` → `'observation'`, `retain_session_log` → `'session-log'`. Caller cannot pass mismatched type.
- **`hindsight_log_query` does NOT touch the daemon.** Resolves `${HINDSIGHT_ROOT}/.decisions/queries/YYYY-MM.jsonl` internally. Path anchor via `_hindsight_root()` — never `os.getcwd()` (PHI-006 invariant).

## Permission policy

All 7 tools auto-approved at user level. Single-user personal tool; bank pollution is git-tracked and recoverable. In-skill content confirmation in all 5 skills already gates retains.
