# LOG-mcp-server-migration — Hindsight MCP server lands

**Date:** 2026-04-30 → 2026-05-01
**Branch:** `spec/mcp-server-design`
**ADR:** `ADR-mcp-server-integration.md`
**CDR:** `CDR-mcp-tool-taxonomy.md`
**Spec:** `docs/superpowers/specs/2026-04-30-hindsight-mcp-server-design.md`
**Plan:** `docs/superpowers/plans/2026-04-30-hindsight-mcp-server.md`

## Files added

- `scripts/mcp_server.py` — FastMCP stdio server, 7 tools (stats, list_documents, recall, retain_phi, retain_obs, retain_session_log, log_query)
- `tests/test_mcp_server.py` — 16 unit tests; `tests/conftest.py` provides `mock_daemon` fixture monkey-patching `urllib.request.urlopen`
- `.claude/.decisions/ADR-mcp-server-integration.md`
- `.claude/.decisions/CDR-mcp-tool-taxonomy.md`
- `.claude/.decisions/LOG-mcp-server-migration.md` (this file)

## Files modified

- 5 skills under `.claude/skills/oracle*/SKILL.md` — heredocs replaced with MCP tool calls
- `.claude/.decisions/DECISION_ORACLE.md` — query/answer log entry updated to reference MCP tool

## Files deleted

- `scripts/log_oracle_query.py` — superseded by `mcp__hindsight__hindsight_log_query`

## User-level changes (not repo-tracked)

### `~/.claude.json`

Added stdio server registration via `claude mcp add hindsight --scope user -- uvx --from mcp python3 /Users/colindwan/Developer/Hindsight/scripts/mcp_server.py`. **Deviation from plan:** plan specified `python3 PATH` directly; bare system `python3` lacks the `mcp` package, so the runtime command uses `uvx --from mcp python3` instead. `claude mcp list` confirms `hindsight: ✓ Connected`.

### `~/.claude/settings.json`

Backup: `~/.claude/settings.json.bak.20260430-214420`.

Diff applied to `permissions.allow`:

**Removed:**
- `Bash(curl * localhost:9077*)`
- `Bash(python3 -c "import json, urllib.request*)`

**Added (7 entries):**
- `mcp__hindsight__hindsight_stats`
- `mcp__hindsight__hindsight_list_documents`
- `mcp__hindsight__hindsight_recall`
- `mcp__hindsight__hindsight_retain_phi`
- `mcp__hindsight__hindsight_retain_obs`
- `mcp__hindsight__hindsight_retain_session_log`
- `mcp__hindsight__hindsight_log_query`

## Smoke / verification

### T12 — server vs real daemon (via stdio MCP client harness, this session)

- `hindsight_stats(bank="oracle")` returns full daemon payload (`bank_id`, `total_nodes=421`, `total_documents=39`, etc.)
- `hindsight_recall(bank="oracle", query="path anchor invariant", top_n=3)` returns slim-shape entries (no `score`, no `rank`); 3 items as requested
- `hindsight_log_query(client="test-client", question="q", answer="a", recall_data={})` writes to `${HINDSIGHT_ROOT}/.decisions/queries/YYYY-MM.jsonl`; consumer-project CWD remains untouched (PHI-006 invariant verified)

### Mock-vs-real-daemon shape divergence (note for future tests)

Real daemon `/stats` shape: `{bank_id, total_nodes, total_links, total_documents, nodes_by_fact_type, links_by_link_type, links_by_fact_type, links_breakdown, pending_operations, failed_operations, last_consolidated_at, pending_consolidation, total_observations}`.

Mock fixtures used `{node_count, observation_count}`. Tools return body verbatim, so mocks pass; the divergence is mock-only and does not affect runtime correctness, but the simpler mock shape is misleading if used as documentation. Consider widening mock fixtures to mirror real shape if regression tests start asserting on stat fields.

Real `/recall` returns `metadata: {}` for entries without metadata; the slim projector keeps `metadata` because `{} is not None`. Acceptable today (empty dict ≠ noise) but a future stricter projector could drop empty containers too.

### T20 — end-to-end skill smoke (DEFERRED)

Requires Claude Code restart to pick up the MCP registration; cannot be performed from inside the live session that registered it. Run in a fresh session:

1. `/oracle "What patterns govern my permission allowlist decisions?"` — verify recall + synthesis + log
2. `/oracle-debate "Test PHI for smoke verification — delete after"` — verify retain bank-first, file write second, delete after
3. `/oracle-observe "Smoke-test observation — delete after"` — verify no `/tmp/oracle_*` files, delete after
4. `/oracle-synthesize` — verify no `/tmp/oracle_synthesize_*` files, delete after
5. `/oracle-preclear` — verify multi-step retain ordering

### T21 — MCP grant auto-promotion (DEFERRED)

Diff `~/.claude/settings.json` against the `.bak.20260430-214420` backup after a few sessions and confirm whether any `mcp__hindsight__*` entries were auto-re-added by the OBS-012 mechanism. Initial diff (immediately post-edit) shows only the 9 intended changes (2 removed + 7 added).

## Rollback runbook

1. `git revert b8a1a04..0c96459` (or rebase the migration commits off the branch)
2. Restore `~/.claude/settings.json` from `~/.claude/settings.json.bak.20260430-214420`
3. `claude mcp remove hindsight --scope user`
4. Confirm: `claude mcp list` no longer shows `hindsight`; `~/.claude/settings.json` `permissions.allow` shows the two restored bash patterns and no `mcp__hindsight__*` entries

## Open follow-ups

- **T20 + T21 must run in a fresh CC session** before this branch is considered fully verified.
- **MCP grant auto-promotion behavior**: the chosen policy (auto-approve all 7) makes promotion benign today, but future tools landing as `ask`-class would be vulnerable. Worth checking again after a few sessions of use.
- **Mock fixtures divergence from real `/stats` shape**: not load-bearing now, but adopt closer-to-real shape if stats fields gain tests.
