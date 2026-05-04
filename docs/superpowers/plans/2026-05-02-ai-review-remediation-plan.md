# 2026-05-02 — AI Review Remediation Plan

## Context

This plan captures findings from a targeted architecture/code-quality review focused on AI-generated inconsistencies, duplicate logic paths, false-positive tests, reinvented utilities, orphaned code paths, and overall maintainability.

Goal: execute this work on a dedicated branch and coordinate with Superpowers in small, reviewable increments.

---

## Findings Summary

1. **Duplicated MCP server implementations**
   - `scripts/mcp_server.py` and `mcp/oracle-query/server.py` both implement overlapping oracle/daemon recall behaviors with divergent stack choices (`urllib` sync vs `httpx` async), projection logic, and runtime semantics.
   - Risk: architectural drift, inconsistent behavior across clients, double maintenance burden.

2. **Inconsistent error handling around query logging**
   - `mcp/oracle-query/server.py::_log_query` swallows all errors by design.
   - `scripts/mcp_server.py::hindsight_log_query` propagates write errors.
   - Risk: unpredictable reliability model and difficult incident/debug behavior.

3. **Potential false-positive / environment-coupled harness tests**
   - `tests/test_hooks_harness.py` includes a case that shells out to `jq`.
   - Risk: tests pass/fail depending on machine image dependencies rather than harness correctness.

4. **Mixed test frameworks and fragmented test style**
   - MCP tests use `pytest`; hook harness tests use stdlib `unittest`.
   - Risk: duplicated fixture patterns, inconsistent developer workflow, and slower onboarding.

5. **Reinvented shared logic (projection + recall semantics)**
   - Similar “slim projection” and recall truncation behavior implemented in parallel.
   - Risk: subtle divergence bugs and uneven feature rollout.

6. **Potential orphaned migration state**
   - `mcp/oracle-query/server.py` appears to represent a newer path but lacks parity test depth compared to `scripts/mcp_server.py` tests.
   - Risk: partial migration uncertainty and unknown production authority.

---

## Execution Strategy (Superpowers Coordination)

### Phase 1 — Authority + Scope Lock

- [ ] Confirm canonical production entrypoint:
  - Option A: `scripts/mcp_server.py`
  - Option B: `mcp/oracle-query/server.py`
  - Option C: dual-entrypoint supported intentionally
- [ ] Record decision and rationale in docs.
- [ ] Define compatibility expectations for downstream clients.

**Deliverable:** authority decision doc + acceptance criteria for behavior parity.

### Phase 2 — Shared Core Extraction

- [ ] Extract shared daemon client + projection utility into a single module (e.g., `mcp/oracle-query/core.py` or `scripts/oracle_core.py`).
- [ ] Keep entrypoint-specific wiring thin (CLI/MCP registration only).
- [ ] Eliminate duplicated projection constants/logic.

**Deliverable:** one source of truth for recall request/response shaping.

### Phase 3 — Logging Contract Unification

- [ ] Define explicit logging contract:
  - Best-effort (never break tool call), or
  - Strict (propagate with explicit typed error behavior)
- [ ] Apply uniformly across all entrypoints.
- [ ] Add tests for log-write failure modes and expected behavior.

**Deliverable:** stable, documented reliability semantics.

### Phase 4 — Test Reliability Hardening

- [ ] Remove `jq` runtime dependency from harness tests.
- [ ] Replace with portable shell/Python snippets that are guaranteed in CI.
- [ ] Add focused tests for classification edge cases (`allow/deny`, malformed JSON, non-zero exits).

**Deliverable:** deterministic tests independent of host package set.

### Phase 5 — Test Architecture Standardization

- [ ] Decide single framework direction (recommended: `pytest` for all tests unless compelling reason not to).
- [ ] If standardizing, migrate hook harness tests from `unittest` to `pytest` incrementally.
- [ ] Preserve intent and existing coverage while simplifying fixtures/helpers.

**Deliverable:** consistent contributor experience and lower test maintenance cost.

### Phase 6 — Migration Completion / Deletion of Orphans

- [ ] If one server is canonical, mark the other deprecated then remove after parity achieved.
- [ ] If dual servers remain intentional, explicitly document capability split and ownership.
- [ ] Add parity tests (or contract tests) for whichever path was previously under-tested.

**Deliverable:** no ambiguous or orphaned runtime path.

---

## Proposed Branching + PR Sequence

1. `chore/oracle-authority-decision`
2. `refactor/oracle-shared-core`
3. `refactor/oracle-logging-contract`
4. `test/harness-portability-hardening`
5. `test/framework-standardization`
6. `chore/orphan-path-resolution`

Keep each PR scoped to one phase to reduce review overhead and rollback complexity.

---

## Definition of Done

- No duplicated oracle recall/projection logic across maintained entrypoints.
- Logging behavior is explicit, consistent, and tested.
- Harness tests are environment-stable and dependency-light.
- Test framework strategy is codified and applied.
- Runtime architecture has one clearly documented authority path (or intentional split).

---

## Superpowers Coordination Notes

- Assign one owner per phase with explicit reviewer.
- Use “decision checkpoints” between phases to avoid speculative refactors.
- Require before/after behavior snapshots for recall outputs and logging behavior.
- Prefer contract tests over implementation-detail assertions where possible.


---

## Additional Analysis — Base Hindsight MCP vs Oracle MCP

### Overlap Inventory

Both services currently wrap the same local hindsight daemon and share a substantial core concern set:

- Daemon recall endpoint usage (`/v1/default/banks/{bank}/memories/recall` equivalent behavior).
- Recall query payload defaults (`budget`, `max_tokens`) and top-N truncation patterns.
- Slim projection behavior focused on `{text, type, document_id, mentioned_at, metadata}`.
- Bank-rooted query logging under `${HINDSIGHT_ROOT}/.decisions/queries/*.jsonl`.
- Identical domain framing: PHI/OBS retrieval for decision support.

This overlap strongly suggests architectural duplication rather than intentional capability partitioning.

### What Is Special About the Oracle MCP

The Oracle MCP path introduces opinionated product semantics not present in the base hindsight MCP toolset:

1. **Relevance-gate instruction contract**
   - Oracle returns an explicit instruction block that governs synthesis behavior (including strict “no relevant entries” response behavior).
   - This is a policy layer on top of raw memory recall, not a new data-access primitive.

2. **User-facing single-tool abstraction (`oracle_query`)**
   - Oracle intentionally narrows the surface area for clients that only need decision-oriented recall.
   - Base hindsight MCP exposes broader, lower-level administrative and retention tools.

3. **Query log schema tuned for MCP-client constraints**
   - Oracle logs `available_ids` because client-side synthesis/citations are not returned to server.
   - This is an adaptation detail, not necessarily a separate service requirement.

### Can They Be Collapsed Into One Service?

**Short answer: yes, likely.**

A single MCP service can expose both:
- a **core hindsight tool family** (stats/list/retain/verbose recall), and
- an **oracle opinionated facade** (relevance gate + constrained output contract).

Recommended unification model:

- Keep one daemon client implementation and one projection/logging core.
- Implement `oracle_query` as a thin adapter over shared recall utility.
- Preserve specialized Oracle semantics via tool-level policy (prompt contract), not separate process/runtime.
- Optionally namespace tools (`hindsight_*` and `oracle_*`) inside one FastMCP server.

### Conditions Where Split Services Might Still Be Justified

Retain split only if there is a concrete, documented requirement such as:
- Different auth/network boundaries,
- Different SLOs or deployment topology,
- Distinct ownership/release cadence that cannot be coordinated,
- Hard isolation of experimental Oracle policy behavior.

Absent one of those constraints, split services are mostly maintenance overhead.

### Updated Recommendation

- Treat Oracle as an **opinionated mode** of the base hindsight MCP, not a standalone backend.
- Collapse shared logic immediately (Phase 2), then decide whether runtime merger is done in the same PR stream or as a follow-up once parity tests pass.
- Extend Phase 1 authority decision with explicit answer to: “single process with dual tool families vs two processes.”
