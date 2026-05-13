# Quickstart: Decision Oracle Workflow Layer Migration

This quickstart is a manual verification and dogfood script for the migrated Oracle workflow layer. It is intended for use after implementation tasks are complete.

## 1. Confirm Active Feature

```bash
.specify/scripts/bash/check-prerequisites.sh --json --paths-only
```

Expected: `FEATURE_DIR` resolves to `specs/003-oracle-workflow-layer`.

## 2. Start or Verify Hindsight Daemon Substrate

This checks the Hindsight HTTP daemon, not the MCP adapter. In Codex, sandboxed
localhost probes may fail even when the daemon is healthy; if that happens,
confirm whether something is listening on port 9077 and rerun the health check
with approved localhost access.

```bash
curl -s http://localhost:9077/health
```

If unavailable, start the daemon using the repository's documented local setup.

Expected healthy response:

```json
{"status":"healthy","database":"connected"}
```

## 3. Verify MCP Adapter and Workflow Tests

This checks the stdio MCP adapter and Oracle workflow-layer contracts. MCP is
not normally verified with `curl` in this repository.

```bash
uvx --from mcp --with pytest pytest tests/test_mcp_server.py tests/test_oracle_workflow_layer.py
```

Expected: MCP adapter tests and Oracle workflow-layer tests pass.

## 4. Native Query Dogfood: Relevant Result

Ask a decision question that should retrieve known PHI/OBS material.

Expected:

- Hindsight recall is used through the MCP/workflow path.
- The response includes the relevance-gate instruction or native workflow equivalent.
- The final answer cites PHI/OBS IDs where available.
- Tensions or counter-evidence appear before the recommendation.
- A query audit entry is written with source marker and accepted IDs.

## 5. Native Query Dogfood: Empty or Irrelevant Result

Ask a decision question known not to match Oracle memory.

Expected exact Oracle answer:

```text
The oracle has no entries relevant to that question.
```

Expected audit behavior:

- Outcome is `empty` or `irrelevant`.
- The attempt is not logged as a system failure.

## 6. Audit Privacy Check

Run a query that retrieves weak but rejected candidates.

Expected:

- Audit record stores full query text.
- Audit record stores identifiers/outcomes/rejection reasons.
- Audit record does not store full rejected candidate bodies by default.

## 7. Capture: Bank-First Success

Approve a test PHI/OBS candidate using the migrated capture workflow.

Expected:

- Explicit approval is required before retain/write.
- Hindsight retain happens before markdown persistence.
- Canonical markdown is written under the Hindsight repository, not caller `cwd`.
- Capture audit distinguishes bank-retained/file-written success.

Clean up test PHI/OBS entries after verification if the candidate was synthetic.

## 8. Capture: Markdown Failure Recovery

Simulate or force a markdown write failure after Hindsight retain.

Expected:

- Workflow reports partial success.
- Retry/regeneration does not create a duplicate retained bank entry.
- Capture audit records bank-retained/file-write failure.

## 9. Compatibility Shim Check

Invoke each legacy path listed in the migration matrix.

Expected:

- Oracle semantics are preserved.
- Exact legacy response shape is preserved only for rows with named active consumers requiring it.
- Audit entries use the canonical record shape and include compatibility source markers.
- Migration notes exist for shape changes.

## 10. Standalone `oracle-query` Deprecation Record

Before the standalone `mcp/oracle-query` path was removed, the workflow
confirmed:

- native query tests pass;
- native capture tests pass;
- pre-clear tests pass;
- compatibility matrix is complete;
- explicit user approval is recorded;
- one manual dogfood session completed with no blocking regressions.

## 11. Suggested Next Command

After this plan is accepted:

```text
/speckit.tasks
```

## Verification Log

### 2026-05-07 Implementation Verification

- Full Python suite:
  `uvx --from mcp --with pytest pytest`
  - Result: 58 passed in 1.43s.
- Query log compatibility review:
  `python3 scripts/review_oracle_queries.py 5`
  - Result: reviewer read recent legacy query entries and rendered normalized
    `legacy` source/outcome/ID fields without errors.
- Daemon substrate health check:
  `curl -s http://localhost:9077/health`
  - Sandboxed result: failed with exit code 7.
  - Follow-up evidence: `lsof -nP -iTCP:9077 -sTCP:LISTEN` showed a Python
    process listening on `127.0.0.1:9077`; approved `curl -sS
    http://localhost:9077/health` returned
    `{"status":"healthy","database":"connected"}`.
  - Interpretation: sandboxed localhost access failed; the Hindsight daemon was
    healthy outside the sandbox.
- Dogfood outcome:
  - Manual MCP/workflow dogfood was pending at the time of this check; daemon
    health was no longer the blocker.
  - Later 2026-05-13 checks completed native dogfood and unblocked standalone
    removal.

### 2026-05-10 Compatibility Dogfood

- Dogfood query:
  `/oracle "Before I remove the standalone oracle-query MCP server, what gates should I require and what risks should I check?"`
- Result:
  - Oracle returned relevant prior memories and synthesized a gate-oriented
    recommendation.
  - Query audit log contains canonical fields with `workflow_source:
    "compat-shim"`, `outcome: "relevant"`, retrieved IDs, accepted IDs, rejected
    IDs, and rejection reasons.
- Remaining gate at the time:
  - Native replacement dogfood and explicit user approval were still required
    before removing `mcp/oracle-query`.

### 2026-05-13 Active Consumer Audit and Native Audit Remediation

- Local/repo consumer audit:
  - Initial audit found Codex config registering standalone
    `mcp/oracle-query/server.py` in `/Users/colindwan/.codex/config.toml`.
  - Follow-up local migration changed Codex config to register native
    `scripts/mcp_server.py` as the `hindsight` MCP server and updated
    `/Users/colindwan/.codex/AGENTS.md` to call `hindsight_oracle_query`.
  - Claude active settings use native `mcp__hindsight__*` tools and do not
    point at standalone `mcp/oracle-query`.
  - Fresh-session Codex dogfood confirmed the migrated config uses native
    Hindsight audit logging.
- Native dogfood remediation:
  - Before remediation, the native non-empty `hindsight_oracle_query` branch
    returned the native envelope but wrote a legacy-shaped query audit entry.
  - The native branch now logs the canonical gate payload with
    `workflow_source: "native"` and `recall_substrate: "hindsight:oracle"`.
  - Regression coverage asserts that relevant native query results write
    canonical native audit fields.
- Dogfood query:
  `Before retiring standalone oracle-query, what native Hindsight workflow evidence should we require?`
- Result:
  - Native replacement dogfood retrieved PHI evidence through Hindsight and
    wrote a canonical `native` query audit entry on 2026-05-13.
  - Fresh-session Codex dogfood for the new-project Oracle DB access question
    wrote `workflow_source: "native"` at
    `2026-05-13T18:51:32.244864+00:00`.
  - The most recent `compat-shim` entry remains
    `2026-05-13T18:46:35.217579+00:00`, before the migrated fresh-session
    dogfood.
  - Standalone `mcp/oracle-query` removal was then approved by user request to
    continue with the cleanup PR on 2026-05-13.

### 2026-05-13 Standalone Cleanup

- User approval:
  - Explicit approval was recorded by the request to continue with the cleanup
    PR on 2026-05-13.
- Removal:
  - Standalone `mcp/oracle-query` files were removed after native tests,
    migrated Codex config, and fresh-session native dogfood passed.
- Current state:
  - Oracle query behavior uses native Hindsight MCP workflow helpers.
  - Historical `compat-shim` audit entries remain reviewable, but no active
    local config requires the exact legacy response shape.
