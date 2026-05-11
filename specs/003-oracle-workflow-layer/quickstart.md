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

## 10. Standalone `oracle-query` Deprecation Gate

Before removing or disabling `mcp/oracle-query`, confirm:

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
  - Manual MCP/workflow dogfood is still pending; daemon health is no longer the
    blocker.
  - Standalone `mcp/oracle-query` removal remains blocked.

### 2026-05-10 Compatibility Dogfood

- Dogfood query:
  `/oracle "Before I remove the standalone oracle-query MCP server, what gates should I require and what risks should I check?"`
- Result:
  - Oracle returned relevant prior memories and synthesized a gate-oriented
    recommendation.
  - Query audit log contains canonical fields with `workflow_source:
    "compat-shim"`, `outcome: "relevant"`, retrieved IDs, accepted IDs, rejected
    IDs, and rejection reasons.
- Remaining gate:
  - Native replacement dogfood and explicit user approval are still required
    before removing `mcp/oracle-query`.
