# Feature Specification: Oracle Pattern Modeling

**Feature Branch**: `002-oracle-pattern-modeling`
**Created**: 2026-04-13
**Status**: Draft

## User Scenarios & Testing *(mandatory)*

### User Story 1 - First Synthesized Observation (Priority: P1)

A developer with 5 CDRs and 1 ADR retained in the oracle bank triggers a reflect query to produce the first synthesized Observation — a cross-CDR pattern statement that describes how architectural decisions have been made so far. The developer reviews the output, curates it if needed, and confirms it as a valid Observation in the oracle bank.

**Why this priority**: Without a validated Observation, the oracle can recall individual decisions but cannot answer "what patterns define how I make architecture decisions?" — the core value of Phase 3. Everything else depends on this working first.

**Independent Test**: Can be tested in isolation by running a reflect query against the oracle bank and verifying that the response references specific CDRs and states a coherent pattern — without any changes to the constitution or cadence tooling.

**Acceptance Scenarios**:

1. **Given** 5 CDRs are retained in the oracle bank, **When** the developer runs a reflect query asking "what patterns define how I make architecture decisions?", **Then** the oracle returns a synthesized response that cites at least 2 specific CDRs and names at least one recurring preference.

2. **Given** the oracle returns a synthesized Observation, **When** the developer reviews it for accuracy, **Then** they can either confirm it as-is or edit it before retaining it as a curated Observation in the bank.

3. **Given** the oracle returns vague or inaccurate output, **When** the developer identifies the issue, **Then** they have a clear path to curate the Observation before committing it to the bank.

---

### User Story 2 - Decision Constitution Updated (Priority: P2)

After reviewing the synthesized Observations, the developer updates the Decision Constitution — the oracle's living Mental Model document — to reflect the recurring preferences and non-negotiables that the Observations surfaced. The constitution becomes an accurate model of actual decision style, not just a template.

**Why this priority**: The constitution is only useful if it reflects observed patterns. Updating it based on real Observations closes the loop between raw decisions and the oracle's behavioral model.

**Independent Test**: Can be tested independently by comparing the constitution before and after: it should reference at least one Observation-derived pattern that wasn't in the original draft.

**Acceptance Scenarios**:

1. **Given** a curated Observation exists in the oracle bank, **When** the developer reads the Observation and the current constitution, **Then** they can identify at least one gap — a pattern the Observation surfaced that the constitution does not yet capture.

2. **Given** a gap is identified, **When** the developer updates the constitution, **Then** the updated version contains a section or principle that corresponds directly to a named Observation.

3. **Given** the constitution is updated, **When** the oracle is queried about architecture preferences, **Then** its reflect output is consistent with the updated constitution.

---

### User Story 3 - Observation Drift Review Cadence (Priority: P3)

The developer defines a lightweight, repeatable check — a specific `/oracle` query — that can be run periodically to detect whether the Observation layer has drifted from actual decisions being made. The cadence is simple enough to run at the start or end of any working session without ceremony.

**Why this priority**: Without a check, the Observation layer silently degrades as new decisions accumulate without being synthesized. The cadence is the maintenance mechanism that keeps the oracle honest over time.

**Independent Test**: Can be validated independently by running the designated cadence query and verifying it returns a response that can be compared against recent CDRs to spot inconsistencies.

**Acceptance Scenarios**:

1. **Given** a periodic review query is defined, **When** the developer runs it after several new CDRs have been added, **Then** the response either confirms the Observations are still consistent with recent decisions, or surfaces a pattern shift worth re-synthesizing.

2. **Given** the cadence query is run, **When** a drift is detected (the Observation contradicts a recent CDR), **Then** the developer knows to trigger a new reflect cycle and curate an updated Observation.

3. **Given** no drift is detected, **When** the query returns consistent results, **Then** the developer can proceed with confidence that the oracle's behavioral model is still accurate.

---

### Edge Cases

- What happens when the oracle has too few CDRs to synthesize a meaningful pattern? (Phase 3 assumes 5 CDRs exist — if the bank is empty or sparse, the reflect query should return a clear "insufficient data" signal, not a hallucinated pattern.)
- How does the developer distinguish a genuinely new pattern from noise in a single outlier CDR?
- What if the constitution update contradicts an existing principle rather than extending it?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The oracle MUST accept a reflect query phrased as "what patterns define how I make architecture decisions?" and return a synthesized response within the same session.
- **FR-002**: The reflect response MUST cite at least 2 specific CDR identifiers in its output, grounding the synthesis in retained decisions rather than general reasoning.
- **FR-003**: The developer MUST be able to curate the reflect output — editing the synthesized text before retaining it — without losing the source citations.
- **FR-004**: The Decision Constitution MUST be updatable as a Mental Model within the oracle bank, not only as a file on disk.
- **FR-005**: A designated cadence query MUST be defined and documented such that any session can execute it without requiring new configuration.
- **FR-006**: The cadence query response MUST be comparable against recent CDRs — structured or phrased such that inconsistencies between Observations and recent decisions are evident.

### Key Entities

- **Observation**: A synthesized pattern statement produced by `reflect`, grounded in multiple CDRs. May be curated by the developer before retention.
- **Decision Constitution**: The oracle's living Mental Model document describing Colin's architectural preferences and non-negotiables. Updated based on Observations.
- **Cadence Query**: A specific, reusable `/oracle` invocation used periodically to check for Observation drift.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The oracle can answer "what patterns define how I make architecture decisions?" with a response that cites specific CDRs — verifiable by inspecting the output against the CDR list.
- **SC-002**: At least one new principle or preference derived from Observations is present in the updated Decision Constitution that was not in the Phase 1 draft.
- **SC-003**: A cadence query is defined and can be executed in under 30 seconds with no session setup beyond the daemon running.
- **SC-004**: Running the cadence query after adding 3 new CDRs produces a response that can be meaningfully compared to the existing Observations without manual cross-referencing.

## Assumptions

- The Hindsight daemon is running and accessible at `http://localhost:9077` before any reflect or retain operations are attempted.
- 5 CDRs (CDR-001 through CDR-005) and 1 ADR (ADR-001) are already retained in the oracle bank from Phases 1 and 2.
- The Decision Constitution exists as a retained Mental Model in the oracle bank (not only as a file on disk).
- Curation of Observations is done manually — no automated approval workflow is in scope for Phase 3.
- The review cadence is not automated or scheduled; it is a defined query the developer chooses to run, not a daemon task.
