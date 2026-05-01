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

### Mock-vs-real-daemon shape divergence — CLOSED 2026-05-01

Original concern: mock fixtures used hand-crafted shapes (`{node_count, observation_count}`) that didn't match the real daemon. Tools returned body verbatim, so tests passed circularly.

**Resolution (post-merge-review pass):** Recorded one real response per endpoint into `tests/fixtures/daemon/{stats,documents,recall}.json` from a live daemon. Tests assert tool behavior against the recorded shapes via a `load_fixture()` helper in `tests/conftest.py`. Contract-shape pins added: `test_hindsight_stats_returns_real_daemon_shape` requires `bank_id, total_nodes, total_documents, total_observations`; `test_hindsight_list_documents_returns_real_daemon_shape` requires `id, bank_id, document_metadata, created_at`; `test_slim_projection_against_real_recall_shape` asserts the projection drops *all* daemon-internal keys, not just the two cited in the original docstring.

Concrete divergences the original mocks would have hidden:
- `documents.items[*]` has no `type` field — taxonomy lives under `document_metadata`. The original `test_hindsight_list_documents_no_prefix` mock invented a `type` key.
- `recall.results[*]` carries 13 keys (`chunk_id, context, document_id, entities, id, mentioned_at, metadata, occurred_end, occurred_start, source_fact_ids, tags, text, type`), not the 7 in the mock. Original `_project_slim` docstring claimed it drops `score, rank` — actually drops 8+ fields.
- `recall.results[*].metadata` is `{}` for entries with no metadata, not absent. Slim projector keeps it. Acceptable.

**Route-pinning made mandatory** (same pass): `mock_daemon.respond()` now requires `url=` and `method=` kwargs and asserts on every call. Previously 8 of 23 tests pinned routes; now all 24 do. Closes the route-drift hole where a tool could be silently re-routed without test failure.

Reference: PHI-007 (shared spec for multi-dialect contract drift) governed the call to fix-now rather than defer; oracle query 2026-05-01.

### T20 — end-to-end skill smoke (DONE — 2026-05-01)

Run in a fresh post-restart session against the registered hindsight MCP server.

1. `/oracle "What patterns govern my permission allowlist decisions?"` — ✅ recall + Sonnet synthesis subagent + `mcp__hindsight__hindsight_log_query` wrote to `${HINDSIGHT_ROOT}/.decisions/queries/2026-05.jsonl` (PHI-006 anchor invariant holds)
2. `/oracle-debate "Test PHI for smoke verification — delete after"` — ✅ `mcp__hindsight__hindsight_retain_phi` succeeded (PHI-020), then file written to absolute `$HINDSIGHT_ROOT` path, then file deleted; bank entry tagged `smoke_test: T20-step2` in metadata for later prune
3. `/oracle-observe "Smoke-test observation — delete after"` — ✅ `mcp__hindsight__hindsight_retain_obs` succeeded (OBS-013); zero `/tmp/oracle_*` files created this session (pre-existing files dated 2026-04-29 21:51–21:54 are pre-migration); bank entry tagged `smoke_test: T20-step3`
4. `/oracle-synthesize` — ✅ stats + list + high-budget recall (top_n=20) via MCP; zero `/tmp/oracle_synthesize_*` files; subagent dispatch and retention deliberately skipped (no MCP delete tool — retaining a synthesis OBS would pollute the bank)
5. `/oracle-preclear` — ✅ stats + list + recall + `mcp__hindsight__hindsight_retain_session_log` succeeded; correctly identified no PHI/OBS candidates qualify (smoke session has no new cross-project signal)

Cleanup follow-ups (manual, no MCP delete path):
- Bank entries `PHI-020` and `OBS-013` are tagged `smoke_test` in metadata — prune via daemon admin path or leave until next bank GC.
- 5 stale `/tmp/oracle_*.{txt,json}` files from pre-migration shell-staging path can be `rm`'d at convenience.

### T21 — MCP grant auto-promotion (1st checkpoint clean — 2026-05-01)

Diff `~/.claude/settings.json` against the `.bak.20260430-214420` backup after a few sessions and confirm whether any `mcp__hindsight__*` entries were auto-re-added by the OBS-012 mechanism. Initial diff (immediately post-edit) showed only the 9 intended changes (2 removed + 7 added).

**Re-check after T20 smoke session (2026-05-01)** — `diff <(jq -S . ~/.claude/settings.json.bak.20260430-214420) <(jq -S . ~/.claude/settings.json)` still shows the same 9 lines and nothing else. No auto-promotion drift, no restored bash patterns, no surprise additions. Caveat: only one additional session of MCP usage has elapsed; this covers the migration session itself plus the heaviest single-session use (all 7 tools exercised), but a longer-horizon re-check is still useful — re-run this command in 2–3 weeks to catch slow drift.

## Rollback runbook

1. `git revert b8a1a04..0c96459` (or rebase the migration commits off the branch)
2. Restore `~/.claude/settings.json` from `~/.claude/settings.json.bak.20260430-214420`
3. `claude mcp remove hindsight --scope user`
4. Confirm: `claude mcp list` no longer shows `hindsight`; `~/.claude/settings.json` `permissions.allow` shows the two restored bash patterns and no `mcp__hindsight__*` entries

## Open follow-ups

- T20 done 2026-05-01. T21 first checkpoint clean as of 2026-05-01; long-horizon re-check (2–3 weeks of use) still recommended to catch slow drift.
- **Bank cleanup**: PHI-020 and OBS-013 smoke artifacts persist in the oracle bank (no MCP delete tool exists); both are tagged `smoke_test: T20-stepN` in metadata. Decide whether to add a delete-by-id MCP tool or leave smoke artifacts for the next consolidation/GC pass.
- **MCP grant auto-promotion behavior**: the chosen policy (auto-approve all 7) makes promotion benign today, but future tools landing as `ask`-class would be vulnerable. Worth checking again after a few sessions of use.
- ~~**Mock fixtures divergence from real `/stats` shape**~~: closed 2026-05-01 — recorded fixtures + contract-shape pins + mandatory route-pinning. See "Mock-vs-real-daemon shape divergence" section above.
- **Two-transport hybrid in `oracle-preclear`**: MCP calls and bash filesystem ops coexist under one parallel-execution step. Stable today (filesystem isn't a daemon resource) but reads as leftover migration. Consider an explicit boundary annotation in the skill or factor the bash filesystem ops into a separate sub-step.
- **Defensive `return []` on missing daemon keys**: `hindsight_list_documents` and `hindsight_recall` swallow malformed responses. PHI-014 tension noted in test docstrings. Today the contract-shape tests are the canary; if a daemon shape change isn't covered by a contract assertion, the tolerance hides it. Revisit if a regression slips through.
