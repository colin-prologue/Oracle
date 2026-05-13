# Migration Matrix: Decision Oracle Workflow Layer

| legacy_path | owner | current_behavior | replacement_behavior | status | active_consumers | exact_shape_required | acceptance_tests | audit_impact | migration_notes | rollback_notes |
|---|---|---|---|---|---|---|---|---|---|---|
| `.claude/skills/oracle/SKILL.md` | skill | Queries Oracle memory at decision points and logs query attempts. | Delegate to base Hindsight recall and canonical query logging. | delegated | Claude Code `/oracle` users | false | US1, US2, US3, US6 | Native query audit with `claude-skill` source. | Update skill wording and README usage. | Restore previous skill file from git. |
| `.claude/skills/oracle-debate/SKILL.md` | skill | Drafts and retains PHI entries after user debate/approval. | Use bank-first capture workflow and capture audit states. | delegated | Claude Code `/oracle-debate` users | false | US4 | Capture audit states for approval/retain/file write. | Update capture instructions. | Restore previous skill file from git. |
| `.claude/skills/oracle-observe/SKILL.md` | skill | Captures OBS entries after fit-check and approval. | Use bank-first capture workflow and capture audit states. | delegated | Claude Code `/oracle-observe` users | false | US4 | Capture audit states for approval/retain/file write. | Update capture instructions. | Restore previous skill file from git. |
| `.claude/skills/oracle-preclear/SKILL.md` | skill | Proposes and captures pre-clear PHI/OBS candidates. | Keep proposal-first ritual; use bank-first capture workflow and capture audit states. | delegated | Claude Code `/oracle-preclear` users | false | US4, US5 | Capture audit states for proposed/approved/rejected/retained outcomes. | Update pre-clear instructions. | Restore previous skill file from git. |
| `.claude/skills/oracle-synthesize/SKILL.md` | skill | Synthesizes OBS entries from Oracle memory. | Reuse citation/tension conventions from native Oracle workflow. | delegated | Claude Code `/oracle-synthesize` users | false | US3 | Native/capture audit as applicable. | Update synthesis instructions. | Restore previous skill file from git. |
| `scripts/mcp_server.py` | mcp | Primary Hindsight MCP adapter with recall, retain, and query logging tools. | Own canonical Oracle workflow helpers and audit record shape. | replaced | Claude Code skills, Codex MCP | false | US1-US6 | Writes canonical query and capture audit records. | Prefer this as native workflow path. | Restore previous script from git. |
| `scripts/review_oracle_queries.py` | script | Reads existing query logs and prints recent entries. | Read canonical audit shape while remaining backward-compatible with old keys. | replaced | Maintainers | false | US6 | Displays canonical audit fields. | Document supported old/new fields in code. | Restore previous script from git. |
| `scripts/precompact_oracle_nudge.py` | hook | Nudges user before compaction/context loss. | Point at proposal-first pre-clear behavior. | delegated | Claude hook harness | false | US5 | No direct audit writes. | Update copy only. | Restore previous script from git. |
| `scripts/userprompt_oracle_capture_nudge.py` | hook | Nudges user around capture opportunities. | Preserve deliberate approval language. | delegated | Claude hook harness | false | US5 | No direct audit writes. | Update copy only. | Restore previous script from git. |
| `.decisions/queries/*.jsonl` | audit | Stores existing Oracle query logs with mixed legacy keys. | Continue as canonical query audit location with stable shape. | replaced | Maintainers | false | US6 | Canonical query audit records. | Review compatibility with old log review helper. | Existing logs remain; no rollback needed. |
| `.decisions/phi/*.md` | docs | Human-readable PHI mirror committed to repo. | Remain Hindsight-root anchored canonical markdown mirror. | replaced | Maintainers | false | US4 | Capture audit records file-write outcomes. | Ensure capture skills never use caller `cwd`. | Restore affected PHI files from git. |
| `README.md` | docs | Documents Oracle architecture and daily usage. | Describe workflow-layer migration and native Hindsight substrate. | replaced | Users/maintainers | false | US1, US7 | No direct audit writes. | Update after behavior changes. | Restore previous README from git. |
| `CLAUDE.md` | docs | Agent-facing Oracle usage and project context. | Describe updated active tech and workflow-layer behavior. | replaced | Claude Code sessions | false | US7 | No direct audit writes. | Update after behavior changes. | Restore previous CLAUDE.md from git. |

## Deprecation Gate Status

- Native query acceptance tests: pass (`uvx --from mcp --with pytest pytest`, 2026-05-07)
- Native capture acceptance tests: pass (`uvx --from mcp --with pytest pytest`, 2026-05-07)
- Pre-clear candidate tests: pass (`uvx --from mcp --with pytest pytest`, 2026-05-07)
- Matrix completeness: pass (`tests/test_oracle_workflow_layer.py`)
- Exact-shape active consumers: no active local config reference found after
  Codex config migration and fresh-session native dogfood on 2026-05-13
- Compatibility audit source markers: pass (`compat-shim` canonical audit shape)
- Migration notes and rollback instructions: pass (`README.md`, `CLAUDE.md`)
- Explicit user approval for removal: pass (recorded by user request to continue with the cleanup PR on 2026-05-13)
- Active consumer audit: pass; `/Users/colindwan/.codex/config.toml`
  now registers native `scripts/mcp_server.py`, fresh-session Codex dogfood
  logged `workflow_source: "native"`, and no new `compat-shim` entry was
  created by the successful query
- Manual dogfood session with no blocking regressions: pass; compatibility
  `oracle-query` dogfood logged canonical `compat-shim` audit on 2026-05-10,
  native replacement dogfood logged canonical `native` audit on 2026-05-13,
  and migrated Codex fresh-session dogfood logged canonical `native` audit at
  2026-05-13T18:51:32.244864+00:00
- Removal action: performed; standalone `mcp/oracle-query` files removed after
  tests, user approval, and fresh-session native dogfood passed
