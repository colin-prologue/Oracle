# 2026-05-03 — Hindsight-Only Migration Exploration (Branch Notes)

Branch: `feat/hindsight-only-migration-exploration`

## Objective

Explore and prototype de-duping by implementing Oracle-mode behavior directly in the base hindsight MCP server, reducing architectural split while preserving Oracle semantics.

## What Changed in This Branch

1. Added an Oracle-mode tool to the base server:
   - `hindsight_oracle_query(bank, question, budget, max_tokens, top_n)`
   - Reuses `hindsight_recall(...)` for retrieval and slim projection.
   - Returns Oracle-style JSON envelope (`instructions` + `results`) with relevance gate contract.
   - Returns exact no-input and no-relevant-entry strings for behavior parity.

2. Added helper for Oracle-style ID extraction:
   - `_available_ids(results)` extracts IDs from `document_id` and PHI/OBS patterns in result text.

3. Added tests for Oracle-mode behavior on base MCP:
   - Response envelope + relevance-gate existence.
   - Empty question guard behavior.

## Why This Supports Hindsight-Only

- The Oracle path's unique value is primarily **policy/contract semantics**, not a separate data backend.
- Implementing Oracle mode as a tool in the base server demonstrates that Oracle can be modeled as an opinionated interface layered on the existing hindsight core.

## Open Questions to Resolve Before Full Migration

1. Should `hindsight_oracle_query` be the canonical tool name, or should we preserve `oracle_query` for client compatibility?
2. Should query logging in Oracle mode be strict or best-effort? (Current code path logs through `hindsight_log_query`, which is strict.)
3. Do we need a compatibility shim in `mcp/oracle-query/server.py` during transition, or can clients swap endpoints in one cutover?
4. Is there any operational requirement (deployment/SLO/ownership) that still forces a dual-service topology?
5. Should Oracle relevance-gate text be configurable via env/config to reduce hard-coded policy drift?

## Recommended Next Step

- Add a thin compatibility shim (or alias tool) so existing Oracle clients can migrate without immediate breaking changes, then complete parity tests and retire duplicate runtime logic.
