# Implementation Plan: Decision Oracle Workflow Layer Migration

**Branch**: `003-oracle-workflow-layer` | **Date**: 2026-05-04 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/003-oracle-workflow-layer/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Migrate the Decision Oracle from a standalone Oracle-specific MCP/runtime path into a workflow layer over base Hindsight primitives. The implementation keeps Oracle semantics intact: strict relevance gate, exact empty signal, PHI/OBS citation, tensions before recommendations, deliberate capture, pre-clear candidate extraction, and auditable query attempts. The technical approach is to make the existing Hindsight MCP/workflow surface the primary path, route legacy Oracle query behavior through compatibility adapters, standardize audit records, preserve bank-first capture ordering, and document deprecation gates for removing `mcp/oracle-query`.

## Technical Context

**Language/Version**: Python 3.11+ for existing MCP/scripts; Markdown for skills, specs, and migration docs  
**Primary Dependencies**: Existing `mcp.server.fastmcp.FastMCP`, `httpx`, Python standard library HTTP/JSON/path tooling, Hindsight daemon HTTP API at `localhost:9077`  
**Storage**: Hindsight oracle bank for operational recall/retain; repository-local `.decisions/phi/` and `.decisions/queries/YYYY-MM.jsonl` for durable review/audit mirrors  
**Testing**: Existing `pytest` tests in `tests/test_mcp_server.py`, hook harness tests, fixture-backed daemon-shape tests, plus new acceptance tests for Oracle workflow semantics and compatibility paths  
**Target Platform**: Local macOS development environment with Hindsight daemon managed outside the agent session; cross-client callers include Claude Code skills and Codex MCP usage  
**Project Type**: Local tooling / MCP adapter / agent workflow skills  
**Performance Goals**: Preserve current interactive Oracle behavior; query path should remain suitable for decision-time use and avoid additional runtime layers beyond Hindsight recall plus client-side synthesis  
**Constraints**: Do not redesign Hindsight storage, ranking, embeddings, daemon lifecycle, or bank schema; do not introduce a second memory system; preserve exact empty signal; retain PHI/OBS to bank before markdown write; audit all query attempts using one record shape  
**Scale/Scope**: Single-user personal Decision Oracle; migration covers documented Oracle commands, hooks, skills, standalone `mcp/oracle-query`, audit files, canonical markdown locations, and named active consumers requiring exact legacy response shape

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The repository constitution is still the uncustomized Spec Kit template, so there are no ratified project-specific gates to enforce. Planning therefore applies the feature spec's own non-negotiable constraints as the effective gates:

- **Memory substrate gate**: PASS. Plan uses base Hindsight recall, retain, and query logging; no second memory system is introduced.
- **Oracle semantics gate**: PASS. Plan preserves relevance gate, exact empty signal, citation requirements, tensions-first synthesis, and inference separation.
- **Conscious capture gate**: PASS. Capture remains user-approved; pre-clear extracts candidates but does not retain them automatically.
- **Audit uniformity gate**: PASS. Native and compatibility paths share a canonical audit record shape with source markers.
- **Bank-first capture gate**: PASS. Plan requires Hindsight retain before canonical markdown persistence and defines partial-failure recovery.
- **Compatibility/deprecation gate**: PASS. Legacy paths are inventoried in a migration matrix; exact response shape is preserved only for named active consumers; removal requires acceptance tests, explicit user approval, and one clean dogfood session.

## Project Structure

### Documentation (this feature)

```text
specs/003-oracle-workflow-layer/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── oracle-workflow.md
│   └── migration-matrix.md
├── checklists/
│   └── requirements.md
└── spec.md
```

### Source Code (repository root)

```text
scripts/
├── mcp_server.py                  # Primary Hindsight MCP/workflow adapter
├── review_oracle_queries.py       # Query audit review helper
├── precompact_oracle_nudge.py     # Existing pre-clear/context-loss hook helper
└── userprompt_oracle_capture_nudge.py

mcp/
└── oracle-query/
    ├── server.py                  # Standalone Oracle-specific MCP path to deprecate or shim
    └── README.md

.claude/
└── skills/
    ├── oracle/
    ├── oracle-debate/
    ├── oracle-observe/
    ├── oracle-preclear/
    └── oracle-synthesize/

.decisions/
├── phi/                           # Canonical PHI markdown mirror
└── queries/                       # Canonical Oracle query audit JSONL files

tests/
├── test_mcp_server.py             # MCP/workflow unit and contract tests
├── test_hooks_harness.py          # Hook behavior tests
└── fixtures/daemon/               # Recorded daemon-shape fixtures
```

**Structure Decision**: This is an in-place migration of local tooling. New work should prefer `scripts/mcp_server.py`, `.claude/skills/oracle*`, `.decisions/`, and tests under `tests/`. The standalone `mcp/oracle-query` path remains only as a compatibility/deprecation target unless the migration matrix identifies an active consumer that requires exact legacy response shape.

## Complexity Tracking

No constitution violations or complexity exceptions are required. The added migration matrix and workflow contract are documentation/test scaffolding for deprecation safety, not new runtime architecture.

## Phase 0: Research

See [research.md](./research.md). Research resolves the planning decisions around primary workflow boundary, compatibility semantics, audit record shape, bank-first capture, path anchoring, and deprecation gates.

## Phase 1: Design & Contracts

See [data-model.md](./data-model.md) for entities, validation rules, and state transitions.

Contracts:

- [oracle-workflow.md](./contracts/oracle-workflow.md): native Oracle workflow behavior and audit/capture contracts.
- [migration-matrix.md](./contracts/migration-matrix.md): required inventory schema for legacy paths and active consumers.

See [quickstart.md](./quickstart.md) for manual verification and dogfood flow.

## Post-Design Constitution Check

- **Memory substrate gate**: PASS. Design keeps Hindsight as the only recall/retain substrate.
- **Oracle semantics gate**: PASS. Contracts encode relevance gate, exact empty signal, citation behavior, and synthesis requirements.
- **Conscious capture gate**: PASS. Data model distinguishes proposed, approved, rejected, retained, and partial-failure states.
- **Audit uniformity gate**: PASS. Contract requires one audit record shape for native and shimmed query attempts.
- **Bank-first capture gate**: PASS. Data model and contract require retain-before-markdown and duplicate-safe retry/regeneration.
- **Compatibility/deprecation gate**: PASS. Migration matrix contract blocks removal until inventory, tests, user approval, and dogfood criteria are satisfied.
