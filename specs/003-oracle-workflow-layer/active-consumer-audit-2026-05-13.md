# Active Oracle MCP Consumer Audit: 2026-05-13

## Summary

The standalone `mcp/oracle-query` path was found as an active Codex
compatibility path during the audit. Follow-up local remediation migrated Codex
configuration to the native Hindsight MCP server. The native Hindsight workflow
is healthy, and fresh-session Codex dogfood confirms successful native audit
logging. Standalone removal was later approved and performed.

## Consumer Inventory

| Consumer | Config path | Uses `mcp/oracle-query`? | Needs exact shape? | Replacement path | Removal blocker |
|---|---|---:|---:|---|---|
| Codex desktop | `/Users/colindwan/.codex/config.toml` | no after local migration | no after local migration | native Hindsight MCP Oracle workflow | none |
| Codex CLI | `/Users/colindwan/.codex/config.toml` | no after local migration | no after local migration | native Hindsight MCP Oracle workflow | none |
| Claude Code skills | `/Users/colindwan/.claude/settings.json`, repo `.claude/skills/oracle*` | no | no | `mcp__hindsight__*` tools | none found locally |
| Repo documentation/tests | `specs/003-oracle-workflow-layer/*`, `tests/test_oracle_workflow_layer.py` | references only | no active exact-shape need found | native Hindsight workflow helpers | none |
| Query audit logs | `.decisions/queries/2026-05.jsonl` | historical evidence of use | no active exact-shape need found | canonical native audit records | none |

## Checks Performed

- Searched repository, `~/.codex`, and `~/.claude` for:
  `oracle-query`, `oracle_query`, `mcp/oracle-query`, `mcp_servers.oracle`,
  and `server.py` paths under `mcp/oracle-query`.
- Reviewed recent query audit logs with `scripts/review_oracle_queries.py 50`.
- Confirmed Hindsight daemon health with `curl -sS http://localhost:9077/health`.
- Ran MCP adapter and Oracle workflow tests with
  `uvx --from mcp --with pytest pytest`.
- Dogfooded native `hindsight_oracle_query` for a relevant Oracle question.
- Migrated `/Users/colindwan/.codex/config.toml` from
  `mcp/oracle-query/server.py` to native `scripts/mcp_server.py`.
- Migrated `/Users/colindwan/.codex/AGENTS.md` from `oracle_query` to
  `hindsight_oracle_query`.
- Validated the migrated Codex TOML parses and the configured native MCP
  command imports the `hindsight` server.
- Confirmed fresh-session Codex dogfood wrote
  `workflow_source: "native"` for the new-project Oracle DB access question at
  `2026-05-13T18:51:32.244864+00:00`.
- Confirmed the most recent `compat-shim` entry was older, at
  `2026-05-13T18:46:35.217579+00:00`, before the migrated fresh-session
  dogfood.

## Remediation

The audit found one native replacement issue: the relevant-result branch of
`hindsight_oracle_query` returned the native synthesis envelope but logged a
legacy-shaped audit payload. That made dogfood evidence look like
`workflow_source: "legacy"` even though the native workflow was used.

The fix changes the relevant-result native branch to log the same canonical
gate payload returned in the response, including `workflow_source: "native"`
and `recall_substrate: "hindsight:oracle"`. Regression coverage now asserts
the native relevant-result path writes canonical native audit fields.

## Decision

Explicit removal approval was recorded by the request to continue with the
cleanup PR on 2026-05-13. The standalone `mcp/oracle-query` files were removed
after native workflow tests, migrated Codex config, and fresh-session dogfood
passed.
