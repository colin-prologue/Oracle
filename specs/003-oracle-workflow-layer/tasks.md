# Tasks: Decision Oracle Workflow Layer Migration

**Input**: Design documents from `/specs/003-oracle-workflow-layer/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/
**Tests**: Included because the spec defines acceptance tests and deprecation gates before old paths may be removed.
**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the migration inventory and shared test scaffolding.

- [X] T001 Create initial migration matrix from `specs/003-oracle-workflow-layer/contracts/migration-matrix.md` in `specs/003-oracle-workflow-layer/migration-matrix.md`
- [X] T002 [P] Add query audit fixture data for native, empty, rejected, failure, and compat-shim outcomes in `tests/fixtures/oracle_workflow/query_audit_entries.json`
- [X] T003 [P] Add capture state fixture data for proposed, approved, retained, file-written, file-write-failed, and retain-failed states in `tests/fixtures/oracle_workflow/capture_states.json`
- [X] T004 [P] Add compatibility inventory fixture data covering required legacy paths in `tests/fixtures/oracle_workflow/migration_matrix.json`
- [X] T005 [P] Create Oracle workflow test module skeleton in `tests/test_oracle_workflow_layer.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define reusable helpers and contracts that every user story depends on.

**CRITICAL**: No user story work can begin until this phase is complete.

- [X] T006 Add canonical Oracle query audit record builder and validation helpers in `scripts/mcp_server.py`
- [X] T007 Add canonical Oracle query audit fixture assertions in `tests/test_oracle_workflow_layer.py`
- [X] T008 Add relevance-gate outcome helper for relevant, empty, irrelevant, and failure states in `scripts/mcp_server.py`
- [X] T009 Add duplicate-safe Hindsight-root path helper tests for query logs and PHI/OBS markdown paths in `tests/test_mcp_server.py`
- [X] T010 Update query log review helper to read the canonical audit shape while remaining compatible with existing log keys in `scripts/review_oracle_queries.py`
- [X] T011 Populate `specs/003-oracle-workflow-layer/migration-matrix.md` with all required initial inventory targets from `specs/003-oracle-workflow-layer/contracts/migration-matrix.md`

**Checkpoint**: Shared workflow helpers, audit schema, and migration inventory exist; user story implementation can begin.

---

## Phase 3: User Story 1 - Query Prior Decision Memory at Decision Points (Priority: P1) MVP

**Goal**: Oracle decision queries use base Hindsight recall and apply the relevance gate before recommendations.

**Independent Test**: Trigger an Oracle-required decision prompt and verify that the workflow uses Hindsight recall rather than standalone Oracle runtime logic.

### Tests for User Story 1

- [X] T012 [P] [US1] Add native query test proving `hindsight_oracle_query` uses Hindsight recall and returns the relevance-gate envelope in `tests/test_oracle_workflow_layer.py`
- [X] T013 [P] [US1] Add skill-contract test proving `.claude/skills/oracle/SKILL.md` instructs agents to query Hindsight before decision recommendations in `tests/test_oracle_workflow_layer.py`

### Implementation for User Story 1

- [X] T014 [US1] Refine `hindsight_oracle_query` to use the canonical relevance-gate outcome helper in `scripts/mcp_server.py`
- [X] T015 [US1] Update `/oracle` skill instructions to name base Hindsight recall as the required substrate in `.claude/skills/oracle/SKILL.md`
- [X] T016 [US1] Update user-facing Oracle decision-point documentation in `README.md`

**Checkpoint**: User Story 1 is independently testable through MCP unit tests and `/oracle` skill review.

---

## Phase 4: User Story 2 - Preserve Exact Empty Signal for Irrelevant Results (Priority: P1)

**Goal**: Empty and irrelevant recall outcomes return the exact Oracle empty signal without weak-match synthesis.

**Independent Test**: Run a query with no genuine PHI/OBS match and verify the exact response text.

### Tests for User Story 2

- [X] T017 [P] [US2] Add empty recall test asserting exact `The oracle has no entries relevant to that question.` output in `tests/test_oracle_workflow_layer.py`
- [X] T018 [P] [US2] Add weak-match rejection test asserting irrelevant candidates produce the exact empty signal in `tests/test_oracle_workflow_layer.py`
- [X] T019 [P] [US2] Add empty-result audit test asserting empty misses are not logged as failures in `tests/test_oracle_workflow_layer.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement empty and irrelevant outcome handling through the canonical relevance-gate helper in `scripts/mcp_server.py`
- [X] T021 [US2] Update `/oracle` skill empty-result instructions to forbid near-miss summaries in `.claude/skills/oracle/SKILL.md`
- [X] T022 [US2] Update standalone compatibility notes for exact empty signal behavior in `mcp/oracle-query/README.md`

**Checkpoint**: User Story 2 returns the exact empty signal across native workflow tests.

---

## Phase 5: User Story 3 - Synthesize Relevant Memories with Tensions First (Priority: P1)

**Goal**: Relevant Oracle answers cite PHI/OBS identifiers, surface tensions first, and separate memory from inference.

**Independent Test**: Query a topic with multiple relevant entries and verify citation, tension, and inference-separation instructions.

### Tests for User Story 3

- [X] T023 [P] [US3] Add synthesis-envelope test for PHI/OBS identifier extraction and available ID reporting in `tests/test_oracle_workflow_layer.py`
- [X] T024 [P] [US3] Add skill-contract test for tensions-before-recommendations wording in `.claude/skills/oracle/SKILL.md` via `tests/test_oracle_workflow_layer.py`
- [X] T025 [P] [US3] Add missing-identifier marker test for relevant memories without `document_id` in `tests/test_oracle_workflow_layer.py`

### Implementation for User Story 3

- [X] T026 [US3] Extend Oracle query envelope with available IDs and missing-identifier indicators in `scripts/mcp_server.py`
- [X] T027 [US3] Update synthesis prompt instructions for tensions, citations, and inference separation in `.claude/skills/oracle/SKILL.md`
- [X] T028 [US3] Update periodic synthesis instructions to use the same citation and tension conventions in `.claude/skills/oracle-synthesize/SKILL.md`

**Checkpoint**: User Story 3 can be validated by unit tests and prompt-contract inspection.

---

## Phase 6: User Story 4 - Deliberately Capture Durable PHIs/OBSs (Priority: P2)

**Goal**: Approved PHI/OBS captures retain to Hindsight before writing canonical markdown and recover cleanly from partial persistence.

**Independent Test**: Draft, approve, retain, and mirror a PHI/OBS candidate; verify explicit approval and bank-first ordering.

### Tests for User Story 4

- [X] T029 [P] [US4] Add retain-before-markdown ordering test for PHI capture instructions in `.claude/skills/oracle-debate/SKILL.md` using `tests/test_oracle_workflow_layer.py`
- [X] T030 [P] [US4] Add retain-before-markdown ordering test for pre-clear PHI capture instructions in `.claude/skills/oracle-preclear/SKILL.md` using `tests/test_oracle_workflow_layer.py`
- [X] T031 [P] [US4] Add partial markdown failure recovery contract test in `tests/test_oracle_workflow_layer.py`
- [X] T032 [P] [US4] Add retain failure prevents markdown creation contract test in `tests/test_oracle_workflow_layer.py`

### Implementation for User Story 4

- [X] T033 [US4] Update `/oracle-debate` capture instructions with explicit bank-first ordering, duplicate-safe markdown retry behavior, and `${HINDSIGHT_ROOT:-$HOME/Developer/Hindsight}` markdown path anchoring in `.claude/skills/oracle-debate/SKILL.md`
- [X] T034 [US4] Update `/oracle-observe` capture instructions with explicit approval, retain-first behavior, source metadata requirements, and `${HINDSIGHT_ROOT:-$HOME/Developer/Hindsight}` markdown path anchoring in `.claude/skills/oracle-observe/SKILL.md`
- [X] T035 [US4] Update `/oracle-preclear` PHI/OBS capture instructions with partial-success behavior, retry/regeneration behavior, and `${HINDSIGHT_ROOT:-$HOME/Developer/Hindsight}` markdown path anchoring in `.claude/skills/oracle-preclear/SKILL.md`
- [X] T036 [US4] Add capture audit helper for proposed, approved, rejected, retained, bank-retained/file-write-failed, and retain-failed states in `scripts/mcp_server.py`
- [X] T037 [US4] Update `/oracle-debate`, `/oracle-observe`, and `/oracle-preclear` to record capture audit states through the capture audit helper in `.claude/skills/oracle*/SKILL.md`

**Checkpoint**: User Story 4 has contract tests for approval, bank-first ordering, and partial persistence recovery.

---

## Phase 7: User Story 5 - Propose Pre-Clear Capture Candidates (Priority: P2)

**Goal**: Pre-clear extracts high-signal candidates before context loss without automatically retaining unapproved material.

**Independent Test**: Run pre-clear after sessions with and without candidates; verify 0-3 proposals and no unapproved retention.

### Tests for User Story 5

- [X] T038 [P] [US5] Add pre-clear candidate limit and no-filler contract test for `.claude/skills/oracle-preclear/SKILL.md` in `tests/test_oracle_workflow_layer.py`
- [X] T039 [P] [US5] Add hook nudge test ensuring context-loss capture remains proposal-based in `tests/test_hooks_harness.py`

### Implementation for User Story 5

- [X] T040 [US5] Update `/oracle-preclear` to explicitly present 0-3 candidates and avoid retaining skipped candidates in `.claude/skills/oracle-preclear/SKILL.md`
- [X] T041 [US5] Update precompact nudge copy to point at proposal-first pre-clear behavior in `scripts/precompact_oracle_nudge.py`
- [X] T042 [US5] Update user prompt capture nudge copy to preserve deliberate approval language in `scripts/userprompt_oracle_capture_nudge.py`

**Checkpoint**: User Story 5 preserves pre-clear ritual value without automatic durable retention.

---

## Phase 8: User Story 6 - Audit Oracle Query Attempts and Misses (Priority: P2)

**Goal**: Every Oracle query attempt writes a uniform audit entry for hits, misses, rejected candidates, failures, and compatibility shim calls.

**Independent Test**: Execute relevant, empty, rejected, failed, and compatibility query paths and inspect canonical audit entries.

### Tests for User Story 6

- [X] T043 [P] [US6] Add canonical audit record tests for relevant, empty, irrelevant, and failure outcomes in `tests/test_oracle_workflow_layer.py`
- [X] T044 [P] [US6] Add audit privacy test proving rejected candidate bodies are omitted by default in `tests/test_oracle_workflow_layer.py`
- [X] T045 [P] [US6] Add compatibility source marker audit test in `tests/test_oracle_workflow_layer.py`

### Implementation for User Story 6

- [X] T046 [US6] Update `/oracle` query logging instructions to pass accepted IDs, rejected IDs, rejection reasons, and outcome into `mcp__hindsight__hindsight_log_query` in `.claude/skills/oracle/SKILL.md`
- [X] T047 [US6] Update `hindsight_log_query` to write the canonical audit record shape with source markers and caller-provided gate results in `scripts/mcp_server.py`
- [X] T048 [US6] Update `hindsight_oracle_query` to log empty, irrelevant, relevant, and failure attempts through the canonical audit path in `scripts/mcp_server.py`
- [X] T049 [US6] Update query review output to display canonical outcome, source marker, accepted IDs, rejected IDs, and rejection reasons in `scripts/review_oracle_queries.py`
- [X] T050 [US6] Update Oracle query logging instructions in `.claude/skills/oracle/SKILL.md`

**Checkpoint**: User Story 6 provides auditable native query attempts and query review support.

---

## Phase 9: User Story 7 - Migrate Existing Oracle Workflows Safely (Priority: P3)

**Goal**: Legacy Oracle paths are delegated, replaced, retired, or blocked with explicit tests, migration notes, and removal gates.

**Independent Test**: Run each migration matrix row against its listed acceptance tests and verify standalone `oracle-query` cannot be removed before gates pass.

### Tests for User Story 7

- [X] T051 [P] [US7] Add migration matrix completeness test for all required initial inventory targets in `tests/test_oracle_workflow_layer.py`
- [X] T052 [P] [US7] Add consumer-based exact response shape test for named active consumers in `tests/test_oracle_workflow_layer.py`
- [X] T053 [P] [US7] Add standalone `mcp/oracle-query` deprecation gate test requiring acceptance tests, user approval, and dogfood evidence in `tests/test_oracle_workflow_layer.py`

### Implementation for User Story 7

- [X] T054 [US7] Complete active-consumer and exact-shape decisions for every row in `specs/003-oracle-workflow-layer/migration-matrix.md`
- [X] T055 [US7] Convert or document `mcp/oracle-query/server.py` as a compatibility shim over the native workflow in `mcp/oracle-query/server.py`
- [X] T056 [US7] Update standalone Oracle MCP migration and rollback notes in `mcp/oracle-query/README.md`
- [X] T057 [US7] Update repository-wide Oracle architecture and usage documentation in `README.md`
- [X] T058 [US7] Update agent-facing Oracle instructions and recent technology context in `CLAUDE.md`

**Checkpoint**: User Story 7 blocks unsafe removal and documents the compatibility/deprecation path.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Final verification, dogfood evidence, and cleanup across the migration.

- [X] T059 [P] Run full Python test suite and record results in `specs/003-oracle-workflow-layer/quickstart.md`
- [X] T060 [P] Run quickstart manual verification and record dogfood outcome in `specs/003-oracle-workflow-layer/quickstart.md`
- [X] T061 [P] Review recent Oracle query logs for canonical shape compatibility using `scripts/review_oracle_queries.py`
- [X] T062 Update deprecation gate status and user approval placeholder in `specs/003-oracle-workflow-layer/migration-matrix.md`
- [X] T063 Remove or disable standalone `mcp/oracle-query` only if all deprecation gates in `specs/003-oracle-workflow-layer/migration-matrix.md` pass and user approval is recorded

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion; blocks all user stories.
- **P1 User Stories (Phases 3-5)**: Depend on Foundational completion. US1 is the MVP; US2 and US3 can proceed after US1 test scaffolding clarifies the native query path.
- **P2 User Stories (Phases 6-8)**: Depend on Foundational completion. US4 and US5 can proceed in parallel; US6 depends on the canonical audit helper from Phase 2 and should integrate outputs from US1-US3.
- **P3 User Story (Phase 9)**: Depends on migration matrix setup and should wait until native workflow behavior is stable enough to define compatibility rows accurately.
- **Polish (Phase 10)**: Depends on selected user stories and deprecation gate status.

### User Story Dependencies

- **US1 (P1)**: No dependency after Foundation; establishes native recall workflow.
- **US2 (P1)**: Depends on US1 helper path but independently validates empty/irrelevant outcomes.
- **US3 (P1)**: Depends on US1 helper path but independently validates synthesis envelope and prompt contract.
- **US4 (P2)**: Independent after Foundation; validates deliberate capture and bank-first persistence.
- **US5 (P2)**: Depends on US4 capture workflow contract for approved candidates.
- **US6 (P2)**: Depends on Foundational audit helper and integrates query outcomes from US1-US3.
- **US7 (P3)**: Depends on US1-US6 behavior contracts to classify legacy paths safely.

### Within Each User Story

- Tests are listed before implementation and should fail before implementation begins.
- Prompt-contract tests should be updated before skill rewrites.
- Canonical helper changes in `scripts/mcp_server.py` should precede updates to legacy compatibility paths.
- Documentation updates should follow behavior changes within each story.

### Parallel Opportunities

- Setup fixtures T002-T005 can run in parallel.
- User-story test tasks marked `[P]` can run in parallel within each story.
- US4 and US5 can proceed in parallel after Foundation if the capture contract is stable.
- Documentation tasks in US7 can run in parallel after the migration matrix is complete.
- Polish verification tasks T057-T059 can run in parallel.

---

## Parallel Example: User Story 6

```text
Task: "Add canonical audit record tests for relevant, empty, irrelevant, and failure outcomes in tests/test_oracle_workflow_layer.py"
Task: "Add audit privacy test proving rejected candidate bodies are omitted by default in tests/test_oracle_workflow_layer.py"
Task: "Add compatibility source marker audit test in tests/test_oracle_workflow_layer.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Stop and validate native Oracle decision queries use base Hindsight recall and preserve the relevance-gate envelope.

### Incremental Delivery

1. Deliver P1 query semantics: US1, US2, US3.
2. Deliver P2 capture/pre-clear/audit semantics: US4, US5, US6.
3. Deliver P3 compatibility/deprecation safety: US7.
4. Run quickstart and dogfood before any standalone `oracle-query` removal.

### Deprecation Safety

Do not remove or disable `mcp/oracle-query` until `specs/003-oracle-workflow-layer/migration-matrix.md` records passing acceptance tests, explicit user approval, and one manual dogfood session with no blocking regressions.
