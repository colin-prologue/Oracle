---
description: "Task list for Oracle Pattern Modeling implementation"
---

# Tasks: Oracle Pattern Modeling

**Input**: Design documents from `/specs/002-oracle-pattern-modeling/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/oracle-synthesize.md, quickstart.md

**Organization**: Tasks grouped by user story for independent implementation and validation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Setup (Verification)

**Purpose**: Confirm daemon is running and the oracle bank contains the expected CDRs/ADR before any synthesis work begins.

- [ ] T001 Verify daemon is accessible: `curl -s http://localhost:9077/v1/default/banks/oracle/stats` — confirm `pending_operations: 0` before proceeding
- [ ] T002 Confirm CDR-001 through CDR-005 and ADR-001 are retained in oracle bank by running `/oracle "List the CDR and ADR identifiers you have retained."` and verifying all 6 are present

**Checkpoint**: Daemon confirmed running with expected CDR/ADR corpus — synthesis can proceed

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Determine next sequential OBS-* ID to prevent document_id collision.

**⚠️ CRITICAL**: Complete before Phase 3 — OBS-001 must be assigned correctly

- [ ] T003 Query oracle bank for any existing OBS-* memories to determine next sequential document_id: `curl -s http://localhost:9077/v1/default/banks/oracle/memories` — if none exist, next ID is OBS-001

**Checkpoint**: OBS-NNN assigned — Phase 3 synthesis can begin

---

## Phase 3: User Story 1 - First Synthesized Observation (Priority: P1) 🎯 MVP

**Goal**: Run a reflect query against the oracle bank, curate the output, and retain it as OBS-001 — a cross-CDR pattern Observation grounded in specific CDR citations.

**Independent Test**: Run `/oracle "What synthesized Observations are in the oracle bank?"` and verify OBS-001 is returned with at least 2 CDR IDs in its metadata.

### Implementation for User Story 1

- [ ] T004 [US1] Write `.claude/skills/oracle-synthesize/SKILL.md` implementing the full synthesis-curation-retain loop per the contract in `specs/002-oracle-pattern-modeling/contracts/oracle-synthesize.md` — include: reflect POST payload, curation presentation step, citation extraction regex (`CDR-\d{3}|ADR-\d{3}`), confirm step, and retain POST payload with `context: "observation"` and `metadata.derived_from`
- [ ] T005 [US1] Execute `/oracle-synthesize` (or run the reflect query manually via `curl -s -X POST http://localhost:9077/v1/default/banks/oracle/reflect -H 'Content-Type: application/json' -d '{"query":"What patterns define how I make architecture decisions? Cite specific CDR IDs (e.g., CDR-001) in your response to ground the synthesis.","budget":"high"}'`) — capture the raw reflect output
- [ ] T006 [US1] Curate the reflect output: verify it cites ≥2 CDR identifiers, edit for accuracy if needed, confirm the `derived_from` list matches citations in the text (FR-002, FR-003)
- [ ] T007 [US1] Retain curated Observation as OBS-001 via `POST http://localhost:9077/v1/default/banks/oracle/memories` with `context: "observation"`, `document_id: "OBS-001"`, `metadata.type: "observation"`, `metadata.derived_from: [<cited CDR IDs>]`, `metadata.query: "What patterns define how I make architecture decisions?"`, `metadata.date: <today ISO>`

**Checkpoint**: OBS-001 retained — independently testable via:
```bash
curl -s http://localhost:9077/v1/default/banks/oracle/documents/OBS-001 | python3 -c "import json,sys; d=json.load(sys.stdin); print('id:', d['id']); print('derived_from:', d['document_metadata'].get('derived_from')); print('type:', d['document_metadata'].get('type'))"
```
Verify: `id` is `OBS-001`, `type` is `observation`, `derived_from` contains ≥2 CDR/ADR IDs. Note: reflect does not surface document IDs — use the documents endpoint for this check.

---

## Phase 4: User Story 2 - Decision Constitution Updated (Priority: P2)

**Goal**: Update the Decision Constitution Mental Model in Hindsight to reflect at least one Observation-derived pattern not present in the Phase 1 draft. Keep file on disk in sync.

**Independent Test**: Compare the constitution before and after — the updated version must contain at least one principle that directly corresponds to a pattern named in OBS-001 and was absent from the Phase 1 draft (SC-002).

### Implementation for User Story 2

- [ ] T008 [US2] Query current constitution via `/oracle "What does the current Decision Constitution say about my architectural preferences?"` — note existing principles to identify gaps
- [ ] T009 [US2] Read OBS-001 content (from oracle recall or retained text) and identify ≥1 gap: a pattern OBS-001 surfaced that the current constitution does not capture
- [ ] T010 [US2] Draft updated constitution text: add a section or principle that corresponds directly to the OBS-001-derived pattern; if it supersedes an existing principle, add "Supersedes prior principle: [...]" notation
- [ ] T011 [US2] Retain updated constitution via `POST http://localhost:9077/v1/default/banks/oracle/mental_models` with `name: "Decision Constitution"` and full updated `description`; if POST returns a conflict, retrieve the existing model ID and use `PUT /v1/default/banks/oracle/mental_models/{id}` instead
- [ ] T012 [P] [US2] Update `.claude/.decisions/DECISION_CONSTITUTION.md` on disk to match the retained Mental Model (FR-004 requires both in sync)

**Checkpoint**: Constitution updated in both Hindsight and on disk — verify via `/oracle "What does the current Decision Constitution say?"`

---

## Phase 5: User Story 3 - Observation Drift Review Cadence (Priority: P3)

**Goal**: Validate the defined cadence query pair (from `quickstart.md`) executes correctly in under 30s and produces output comparable against recent CDRs.

**Independent Test**: Run both cadence queries and confirm: (a) both complete in <30s with daemon running and no additional setup, (b) Query 2 output references specific CDR IDs (SC-003, SC-004).

### Implementation for User Story 3

- [ ] T013 [US3] Execute cadence Query 1 via `/oracle "Summarize the current synthesized Observations in the oracle bank."` — record whether OBS-001 is cited and the response time
- [ ] T014 [US3] Execute cadence Query 2 via `/oracle "Compare the current Observations against the most recently retained CDRs. Flag any pattern shifts or contradictions."` — verify the response references specific CDR IDs and produces a comparison statement
- [ ] T015 [US3] Confirm both queries complete within 30s (SC-003) and that Query 2 output can be read against the CDR list without manual cross-referencing (SC-004); if quickstart.md has inaccuracies from actual behavior, note them for the Polish phase

**Checkpoint**: Cadence query defined and validated — drift detection is operational

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Sync docs to reality, close Phase 3 roadmap, run session end protocol.

- [ ] T016 [P] Update `specs/002-oracle-pattern-modeling/quickstart.md` with any corrections from actual execution (e.g., actual reflect response time, adjusted query phrasing if output differed)
- [ ] T017 Update `.claude/.decisions/DECISION_ORACLE.md` to check off Phase 3 roadmap items: `/oracle-synthesize` skill created, OBS-001 retained, constitution updated
- [ ] T018 Run session end protocol: write 3–5 sentence session summary and retain to oracle bank via `POST http://localhost:9077/v1/default/banks/oracle/memories` with `context: "session-log"`, `metadata.type: "session-log"`, `metadata.date: <today>`
- [ ] T019 [P] Capture any unrecorded decisions from this session via `/oracle-capture` (e.g., decisions about curation workflow, constitution structure choices, or cadence query phrasing)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (daemon must be confirmed running)
- **US1 (Phase 3)**: Depends on Phase 2 (OBS-* ID assigned) — **BLOCKS US2**
- **US2 (Phase 4)**: Depends on US1 (OBS-001 must be retained to update constitution against it)
- **US3 (Phase 5)**: Independent of US1 and US2 — can run after Phase 1/2 if cadence query validation doesn't require OBS-001
- **Polish (Phase 6)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational only — no story dependencies
- **US2 (P2)**: Depends on US1 — constitution update is driven by OBS-001 content
- **US3 (P3)**: Independent — cadence queries work against whatever is in the bank

### Within User Story 1

- T004 (write skill) can run in parallel with T005 (first reflect run) — different artifacts
- T006 (curate) depends on T005 output
- T007 (retain) depends on T006 curated content

### Parallel Opportunities

- T004 and T005 within US1 can run in parallel (skill authoring vs. reflect execution)
- T012 (file update) and T011 (Mental Model retain) within US2 can run after T010
- T016 and T019 in Polish phase are independent of each other
- US3 (T013–T015) can run in parallel with US2 once US1 is done

---

## Parallel Example: User Story 1

```
# Run in parallel once Phase 2 is complete:
Task T004: Write .claude/skills/oracle-synthesize/SKILL.md
Task T005: Execute reflect query against oracle bank

# Sequentially after T005:
Task T006: Curate reflect output
Task T007: Retain as OBS-001
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Verify daemon and corpus
2. Complete Phase 2: Confirm OBS-* ID
3. Complete Phase 3: US1 — write skill, synthesize, curate, retain OBS-001
4. **STOP and VALIDATE**: `curl -s http://localhost:9077/v1/default/banks/oracle/documents/OBS-001` returns the document with `type: observation` and ≥2 entries in `derived_from`
5. Ship US1 — oracle can now answer "what patterns define my decisions?"

### Incremental Delivery

1. Setup + Foundational → corpus confirmed, ID assigned
2. US1 → OBS-001 retained, pattern synthesis working
3. US2 → constitution updated to reflect observed patterns
4. US3 → drift detection operational
5. Polish → docs accurate, session closed cleanly

---

## Notes

- No new infrastructure or runtime — all work is skill authoring (SKILL.md) + manual oracle operations
- Daemon constraint: avoid concurrent retain+reflect (CDR-004) — run ops sequentially
- Reflect budget must be `high` for pattern synthesis (skill contract invariant)
- Never auto-retain an Observation — explicit curation + confirmation required (skill invariant)
- The cadence query is not a scheduled task — it's a documented query the developer runs manually
