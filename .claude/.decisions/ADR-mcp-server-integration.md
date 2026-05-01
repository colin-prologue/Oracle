# ADR-mcp-server-integration — Hindsight MCP Server as Oracle Skill Integration Boundary

**Date:** 2026-04-30
**Status:** Accepted
**Spec:** `docs/superpowers/specs/2026-04-30-hindsight-mcp-server-design.md`

## Context

Five oracle skills called the local hindsight daemon at `localhost:9077` via inline `python3 -c "import json, urllib.request..."` heredocs through Claude Code's Bash tool. A user-level allowlist entry — `Bash(python3 -c "import json, urllib.request*)` — kept these silent across projects but was functionally equivalent to `Bash(python3 *)` under prompt injection.

PHI-019 (capability allowlists drift toward over-permissive baselines) and OBS-012 (live evidence of auto-allowlist re-introduction) made the bash-allowlist surface a structural drift target.

## Decision

Hindsight ships a Python MCP server (`scripts/mcp_server.py`) using FastMCP over stdio. Five oracle skills are migrated to call typed `mcp__hindsight__*` tools instead of inline HTTP heredocs. The two over-broad bash allowlist entries are removed; seven narrow MCP tool grants replace them at user level.

## Risk Classes Used

- **read-of-pre-existing-state** (auto-approve safe): `hindsight_stats`, `hindsight_list_documents`, `hindsight_recall`
- **append-to-canonical-bank** (auto-approve only if write boundary is well-defined and recoverable): `hindsight_retain_phi`, `hindsight_retain_obs`, `hindsight_retain_session_log`, `hindsight_log_query`

New tools require an ADR amendment naming risk class.

## References

- PHI-019 (capability allowlists drift)
- OBS-012 (auto-allowlist re-introduction evidence)
- PHI-001 (stateless system design — daemon stays the state-holder)
- PHI-006 (path resolution must anchor against owning repo, not CWD — preserved by `_hindsight_root()` in MCP server)
- PHI-007 (extract shared spec, not implementation — slim shape lives at MCP boundary)
- CDR-subscription-llm-routing (synthesis subagent dispatch unaffected)
