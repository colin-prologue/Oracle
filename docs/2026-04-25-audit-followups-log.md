# Audit Followups Log — 2026-04-25

Branch: `005-audit-followups`
Plan: `docs/superpowers/plans/2026-04-25-audit-followups.md`

## Task C — Branch Hygiene

### C1 — Audit

`git fetch --prune origin` cleaned up three already-deleted remotes: `origin/002-oracle-pattern-modeling`, `origin/003-oracle-vocabulary-alignment`, `origin/004-readme`. None of these were local.

Surviving branches:

| Branch | Local | Remote | Merged into main? | Verdict |
|---|---|---|---|---|
| `001-oracle-hook-skills` | yes | yes | yes | delete-both |
| `005-audit-followups` | yes (current) | yes | yes (no diff yet) | keep — active feature |
| `main` | yes | yes | n/a | keep |

### C2 — Local deletions

- `001-oracle-hook-skills` — ✓ deleted (was at `5811898`, merged)

### C3 — Remote deletions

- `origin/001-oracle-hook-skills` — ✓ deleted on remote
- `origin/002-oracle-pattern-modeling`, `origin/003-oracle-vocabulary-alignment`, `origin/004-readme` — already pruned by `git fetch --prune` (deleted on origin previously)

### Verdict

1 local + 1 remote branch removed by this task; 3 stale remote refs already pruned. Final state: `main`, `005-audit-followups` (local + remote).


## Task A — Bank Legacy Cleanup

### A1 — DELETE endpoint verification

- WRITE result: `200 success=True`
- DELETE result: `200 {"success":true,"document_id":"DELETE_PROBE_001","memory_units_deleted":0}`
- GET-after-delete: `404`
- Verdict: endpoint usable; idempotent

### A2 — Candidate inventory

| ID | type | date | len | title |
|---|---|---|---|---|
| `08b56c2d-...` | session-log | 2026-04-21 | 763 | (no heading) |
| `db0c6031-...` | session-log | 2026-04-21 | 1421 | (no heading) |
| `3879f855-...` | session-log | 2026-04-21 | 1890 | (no heading) |
| `681ecce2-...` | session-log | 2026-04-18 | 987 | (no heading) |
| `63d3dca1-...` | session-log | 2026-04-18 | 964 | (no heading) |
| `36f3f9e5-...` | session-log | 2026-04-14 | 707 | (no heading) |
| `d00566fc-...` | session-log | 2026-04-14 | 1014 | (no heading) |
| `CDR-007` | cdr | 2026-04-14 | 2824 | Two-skill observation capture |
| `CDR-006` | cdr | 2026-04-13 | 2352 | Oracle bank retain strategy |
| `CDR-005` | cdr | 2026-04-13 | 3014 | Daemon lifecycle to LaunchAgent |
| `cli_put_20260412_205253` | (none) | (none) | 2478 | CDR-004 — Haiku TPM contention |
| `cli_put_20260410_010327` | (none) | (none) | 2642 | ADR-001 — key-based LLM provider |
| `cli_put_20260409_230320` | (none) | (none) | 1125 | CDR-003 — plugin config location |
| `cli_put_20260409_225328` | (none) | (none) | 1677 | CDR-002 — macOS CPU-forcing flags |
| `cli_put_20260409_225306` | (none) | (none) | 1793 | CDR-001 — key-based LLM provider |
| `cli_put_20260409_224102` | (none) | (none) | 4 | (4 chars, junk) |

Plan assumed UUID records were autoRetain detritus; actual content shows they are session-logs. Plan assumed `cli_put_*` were test artifacts; actual content shows 5 are substantive CDR/ADR records and only 1 is junk. Re-classified accordingly before oracle query.

### A3 — Classification (oracle-mediated)

Auto-rule: `cli_put_20260409_224102` (4 chars) → **delete** (no content).

Oracle query: see [Oracle Queries](#oracle-queries) section. Per-record verdicts:

| ID | verdict | reason |
|---|---|---|
| `CDR-005` | keep | Implementation detail beyond PHI-002 (LaunchAgent specifics, idle config) |
| `CDR-006` | keep | Implementation detail beyond PHI-003 (TPM contention, pending_operations) |
| `CDR-007` | keep | Two-skill split decision; no PHI counterpart |
| `cli_put_20260412_205253` (CDR-004) | keep | Haiku TPM constraint, not covered by any PHI |
| `cli_put_20260410_010327` (ADR-001) | **delete** | Duplicate of CDR-001 |
| `cli_put_20260409_230320` (CDR-003) | keep | Plugin config location knowledge |
| `cli_put_20260409_225328` (CDR-002) | keep | macOS MPS / Python 3.14 platform constraint |
| `cli_put_20260409_225306` (CDR-001) | keep | Validates PHI-001 empirically |
| All 7 UUID session-logs | **delete** | Signal/noise per PHI-003; reflect contamination; alternative is sample preservation but oracle judges no current value |
| `cli_put_20260409_224102` (4 chars) | **delete** | Auto-rule (junk) |

Total: 9 deletions, 7 kept (legacy by intent), 7 PHIs + 5 OBSs untouched.

### A4 — Deletion results

- Pre-deletion total: 28 docs
- Post-deletion total: 19 docs
- Memory units pruned: 43 (sessions had 5–8 each; cli_put_* deletions removed 0 since they were never extracted)
- All 9 deletions returned HTTP 200; no failures.
- Surviving IDs: PHI-001..007, OBS-001..005, CDR-005/006/007, cli_put_20260409_225306 (CDR-001), cli_put_20260409_225328 (CDR-002), cli_put_20260409_230320 (CDR-003), cli_put_20260412_205253 (CDR-004) — 19 records, all PHI/OBS or kept-by-oracle-judgment legacy CDRs.

## Task B — Hook-Firing Test Harness

### B1 — Scaffold

- Created `scripts/test-hooks.py` and `tests/test_hooks_harness.py` (stdlib `unittest` — pytest is not a project dep).
- First test: empty settings → 0 cases. PASSes.

### B2 — Synthesize payloads + run command hooks

- Default payloads keyed on `(event, matcher)` for PreToolUse Bash/Write/Edit, PostToolUse Bash, and stub payloads for UserPromptSubmit/Stop/Session*/PreCompact.
- Non-command hook types (prompt/agent/http) → SKIP.
- Sentinel-file test confirms `cat > /tmp/...` hook receives the synthesized JSON.

### B3 — Assertion-driven allow/deny + real-config smoke run

- Sidecar `<settings>.assertions.json` declares `{event, matcher, command_contains, expect, stdin_overrides}` per case.
- `classify_outcome` maps stdout `permissionDecision` and exit code to `allow`/`deny`.
- Created `~/.claude/settings.assertions.json` with one entry asserting the block-main-commit hook allows `ls`.

Smoke run: `python3 scripts/test-hooks.py --settings ~/.claude/settings.json`

```
6 cases
PASS PreToolUse/Bash (command)  expect=allow  got=allow
PASS UserPromptSubmit/* (command)  (no assertion, exit 0)
PASS Stop/* (command)  (no assertion, exit 0)
PASS SessionStart/* (command)  (no assertion, exit 0)
PASS SessionEnd/* (command)  (no assertion, exit 0)
PASS PreCompact/* (command)  (no assertion, exit 0)
```

Verdict: 6/6 PASS. The block-main-commit hook correctly allows non-git commands. All 5 hindsight-memory python hooks tolerate the harness's stub payloads without erroring — useful resilience signal.

Limitation logged: `match_assertion` returns the FIRST match. To exercise both the deny-on-main case and the escape-hatch case for the same hook, the harness would need either multi-match support or repeated invocations with different `stdin_overrides`. Marked YAGNI — single allow-case assertion already closes the PHI-004 loop for the new commit hook (existence + minimal payload sanity). Deny-case validation is exercised by unit tests, not the real-config sidecar.

## Oracle Queries

### Q1 — Bank cleanup (CDR + session-log fates)

**Asked at:** Task A3, 2026-04-25.
**Question summary:** For each pre-rename CDR/ADR record (some stored as `CDR-NNN`, some as `cli_put_*`) and each UUID-named session-log, recommend keep or delete given existing PHI-001..007 and OBS-001..005 in the bank.

**Oracle recommendation (verbatim, abridged):**

> GROUP A — keep CDR-005/006/007 (implementation details extending PHI-002/003), keep CDR-001/002/003/004 (cli_put_* substantive), delete cli_put_20260410_010327 (ADR-001 duplicate of CDR-001).
>
> GROUP B (session logs) — DELETE ALL. Signal/noise per PHI-003; competes with PHI/OBS during reflect; "Archive, Don't Retain" — preserve in separate bank with disabled reflect indexing if retrospective tracing needed, not active oracle bank.

**Action taken:** Accepted recommendation in full. 1 ADR-1 duplicate + 7 session logs deleted; 7 substantive CDRs preserved. Plus 1 auto-rule deletion (4-char junk). Total: 9 deletions.

## Final Summary

- **Task C (branch hygiene):** 1 local + 1 remote branch removed (`001-oracle-hook-skills`); 3 stale remote refs auto-pruned by `git fetch --prune`. Final state: `main`, `005-audit-followups` only.
- **Task A (bank cleanup):** 28 → 19 docs. Deleted 9 records (7 session-logs + 1 ADR-001 duplicate + 1 4-char junk), 43 memory units pruned. Kept 7 PHIs, 5 OBSs, and 7 legacy CDR records (CDR-005/006/007 + 4 cli_put_*-stored CDRs) on oracle's recommendation that each captures unique implementation knowledge not subsumed by current PHIs.
- **Task B (hook-firing harness):** Shipped `scripts/test-hooks.py`, `tests/test_hooks_harness.py`, `scripts/README.md`, `~/.claude/settings.assertions.json`. Real-config smoke run shows 6/6 PASS across all configured hooks (block-main-commit + 5 hindsight-memory hooks). Closes PHI-004's aspirational-drift gap for the new commit hook.

### Commits on this branch

```
fdc60e7 feat(hooks): allow/deny assertions + smoke run against real config
f92045d feat(hooks): execute command-type hooks with synthesized payloads
9b88dc8 feat(hooks): scaffold hook-firing test harness
64cea09 chore(oracle): prune legacy bank records (CDR/UUID/cli_put detritus)
711e65f chore(branches): clean up merged feature branches + seed audit-followups log
```

### Outstanding / out-of-scope

- Multi-case matching in the harness (`match_assertion` returns first match) — YAGNI; revisit if multiple cases per (event, matcher) become a real need.
- Non-command hook execution (prompt/agent/http) — none currently configured; harness reports SKIP correctly.
- `~/.claude/settings.assertions.json` lives at user-global path, not in the Hindsight repo. Consider moving to a versioned location if you want assertions to travel with the project; currently it's a personal config artifact.

### Oracle queries

1. CDR + session-log fates (logged above) — verdict accepted in full.
