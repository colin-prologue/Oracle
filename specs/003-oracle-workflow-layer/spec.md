# Feature Specification: Decision Oracle Workflow Layer Migration

**Feature Branch**: `003-oracle-workflow-layer`  
**Created**: 2026-05-04  
**Status**: Draft  
**Input**: User description: "Define the migration of the Decision Oracle from a separate Oracle-specific MCP/runtime path into a workflow layer built on top of base Hindsight primitives. Preserve Oracle semantics and rituals while removing duplicated runtime/server logic. Use Hindsight recall, retain, and query logging as the substrate. Define acceptance criteria, migration risks, compatibility requirements, audit requirements, and a phased roadmap suitable for later /speckit.plan and /speckit.tasks work."

## Oracle Inputs Applied

The migration direction is informed by relevant prior Oracle entries:

- **PHI-003**: Prefer conscious capture over automatic retention in memory systems; preserve explicit approval for durable Oracle entries.
- **PHI-005**: Reduce activation energy by automating extraction, not execution; pre-clear should propose capture candidates while the user decides what becomes canonical.
- **PHI-016**: Before specifying follow-on work, check whether manual usage has invalidated prior assumptions; migration must preserve explicit audit and acceptance gates before old paths are removed.
- **OBS: Uniform audit-trail principle**: Prefer one main path for auditable decisions over fast-path exceptions; Oracle query attempts should produce one consistent audit record shape whether results are relevant, empty, or failed.

## Clarifications

### Session 2026-05-04

- Q: What should be the deprecation gate for removing the standalone `oracle-query` MCP path? -> A: Acceptance tests pass, explicit user approval is received, and one manual dogfood session completes with no blocking regressions.
- Q: What should Oracle query audit logs store when the query or candidates may include sensitive/project-local content? -> A: Store full query text, identifiers/outcomes, and rejection reasons; do not store full rejected candidate text by default.
- Q: If PHI/OBS capture only partially persists, what recovery rule should the migrated workflow require? -> A: Retain to Hindsight first, then write markdown; if markdown persistence fails, report partial success and require retry or regeneration without duplicate retain.
- Q: What compatibility level should legacy Oracle query paths provide during the migration? -> A: Preserve Oracle semantics for all legacy paths; preserve exact old response shape only for named active consumers in the migration matrix.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Query Prior Decision Memory at Decision Points (Priority: P1)

Before making an architectural, technology, workflow, or tradeoff decision, the agent retrieves relevant prior PHIs/OBSs through the base Hindsight recall path and applies the Oracle relevance gate before answering.

**Why this priority**: This is the core user-facing value of the Decision Oracle. The migration is not successful unless agents still consult prior decision memory at the moment a decision is being shaped.

**Independent Test**: Can be tested by triggering an Oracle-required decision prompt and verifying that the workflow uses Hindsight recall rather than an Oracle-specific MCP/server runtime, then applies the relevance gate before synthesis.

**Acceptance Scenarios**:

1. **Given** an agent is about to recommend an architecture, technology, workflow, or tradeoff choice, **When** the Oracle workflow is invoked, **Then** it queries Hindsight for prior PHI/OBS material before presenting a recommendation.
2. **Given** Hindsight returns candidate memories, **When** the workflow evaluates them, **Then** it filters by genuine subject-matter relevance rather than keyword overlap.
3. **Given** relevant memories exist, **When** the workflow answers the decision question, **Then** it cites PHI/OBS identifiers and separates prior-memory evidence from the agent's current reasoning.

---

### User Story 2 - Preserve Exact Empty Signal for Irrelevant Results (Priority: P1)

When no retrieved memory is genuinely relevant, the agent returns the exact Oracle empty signal and does not synthesize from weak matches.

**Why this priority**: The Oracle is useful partly because it can say "nothing relevant" without laundering weak recall into false authority. Preserving that semantic is required before removing the standalone path.

**Independent Test**: Can be tested with a query known to have no matching PHI/OBS entries and verifying the response is exactly `The oracle has no entries relevant to that question.`

**Acceptance Scenarios**:

1. **Given** Hindsight returns zero candidate memories, **When** the relevance gate runs, **Then** the workflow returns exactly `The oracle has no entries relevant to that question.`
2. **Given** Hindsight returns keyword-adjacent but substantively irrelevant memories, **When** the relevance gate runs, **Then** the workflow returns exactly `The oracle has no entries relevant to that question.`
3. **Given** the empty signal is returned, **When** the query attempt is audited, **Then** the audit record distinguishes a valid empty-result miss from a system failure.

---

### User Story 3 - Synthesize Relevant Memories with Tensions First (Priority: P1)

When relevant PHIs/OBSs exist, the agent synthesizes a concise answer that cites identifiers, surfaces tensions or counter-evidence, and only then recommends a direction.

**Why this priority**: Oracle answers must preserve decision nuance, not simply retrieve memory. Tensions and counter-evidence keep prior philosophy from becoming unexamined dogma.

**Independent Test**: Can be tested by querying a decision topic with multiple relevant entries and verifying the response format includes identifiers, tensions, and a concise recommendation.

**Acceptance Scenarios**:

1. **Given** relevant PHI/OBS memories support more than one consideration, **When** the workflow synthesizes an answer, **Then** it names the tension before making a recommendation.
2. **Given** the workflow cites prior memory, **When** the answer is produced, **Then** every cited prior-memory claim includes a PHI/OBS identifier or an explicit missing-identifier marker.
3. **Given** the workflow must add current reasoning beyond retrieved memories, **When** it answers, **Then** it clearly distinguishes inference from cited Oracle memory.

---

### User Story 4 - Deliberately Capture Durable PHIs/OBSs (Priority: P2)

When a new durable philosophy or observation emerges, the user can deliberately capture it into the canonical Oracle bank and markdown decision files through a Hindsight retain-backed workflow.

**Why this priority**: Migration cannot reduce the quality or intentionality of the Oracle bank. Durable capture must remain explicit, canonical, and easy enough to use.

**Independent Test**: Can be tested by drafting a new PHI/OBS candidate, approving it, and verifying both Hindsight retention and canonical markdown file creation/update.

**Acceptance Scenarios**:

1. **Given** a new durable philosophy emerges during work, **When** the user invokes Oracle capture, **Then** the workflow drafts a PHI candidate with context, applicability, limits, and source links for user review.
2. **Given** a new durable observation emerges during work, **When** the user invokes Oracle capture, **Then** the workflow drafts an OBS candidate with evidence, date, source context, and relationship to existing PHIs when applicable.
3. **Given** the user approves a candidate, **When** capture completes, **Then** the entry is retained through base Hindsight before the canonical Oracle markdown file is written or linked in the Hindsight repository.
4. **Given** the user rejects or edits a candidate, **When** the workflow continues, **Then** no durable memory is retained until explicit approval is received.

---

### User Story 5 - Propose Pre-Clear Capture Candidates (Priority: P2)

Before context loss, compaction, or session clearing, the workflow proposes high-signal capture candidates for approval rather than requiring the user to articulate them from scratch.

**Why this priority**: This preserves the proven pre-clear ritual while reducing the activation energy of capture. The workflow should automate extraction, not approval.

**Independent Test**: Can be tested by running the pre-clear workflow after a session with decisions and verifying it proposes concise PHI/OBS candidates without retaining them automatically.

**Acceptance Scenarios**:

1. **Given** a session contains durable decisions, repeated reasoning patterns, or notable observations, **When** pre-clear runs, **Then** it proposes a short list of candidate PHIs/OBSs with source snippets and rationale.
2. **Given** no high-signal candidates exist, **When** pre-clear runs, **Then** it says no capture candidates were found and does not create filler entries.
3. **Given** the user approves one or more candidates, **When** capture proceeds, **Then** the same deliberate capture path from User Story 4 is used.
4. **Given** the user takes no action before context loss, **When** the session ends, **Then** unapproved candidates are not retained as canonical Oracle entries.

---

### User Story 6 - Audit Oracle Query Attempts and Misses (Priority: P2)

Every Oracle query attempt, including empty-result misses and compatibility-shim calls, remains auditable so the user can evaluate bank usefulness and coverage gaps.

**Why this priority**: Audit logs are how the user judges whether the bank is helping, where recall is missing, and whether compatibility paths are still in use.

**Independent Test**: Can be tested by executing relevant, empty, and failed Oracle queries and verifying each produces a uniform audit entry with outcome, source path, and gate result.

**Acceptance Scenarios**:

1. **Given** an Oracle query returns relevant memories, **When** the workflow completes, **Then** the audit log records the query, retrieved identifiers, accepted identifiers, rejected candidates if available, result type, and workflow source.
2. **Given** an Oracle query returns no genuinely relevant memories, **When** the empty signal is returned, **Then** the audit log records the attempt as an empty-result miss, not an error.
3. **Given** a compatibility shim handles an old Oracle command, **When** the query completes, **Then** the audit log marks the compatibility source while using the same canonical audit record shape.
4. **Given** the Hindsight substrate is unavailable, **When** the query fails, **Then** the audit log records a failure entry when possible and the user receives an actionable error.

---

### User Story 7 - Migrate Existing Oracle Workflows Safely (Priority: P3)

Existing Oracle workflows either continue to work through compatibility shims or have explicit migration notes, replacement acceptance criteria, and removal criteria before old paths are removed.

**Why this priority**: The standalone Oracle path can only be deprecated after replacement behavior is proven. Compatibility gives users and tooling time to move without silent breakage.

**Independent Test**: Can be tested by running each known legacy command or MCP path against a migration matrix and verifying it either delegates to the new workflow or has an approved retirement note.

**Acceptance Scenarios**:

1. **Given** a legacy Oracle command is still documented as supported, **When** the user invokes it, **Then** it delegates to the Hindsight-backed workflow and emits a deprecation note only if migration guidance exists.
2. **Given** a legacy behavior is proposed for removal, **When** removal is reviewed, **Then** the spec or migration note identifies the replacement behavior, acceptance tests, audit impact, and rollback path.
3. **Given** all replacement acceptance tests pass, explicit user approval is received, and one manual dogfood session completes with no blocking regressions, **When** deprecation criteria are reviewed, **Then** the standalone oracle-query MCP path may be removed.

### Edge Cases

- Hindsight recall returns many loosely related entries; the relevance gate must reject weak matches and preserve the exact empty signal if none are genuinely relevant.
- Hindsight recall returns entries without PHI/OBS identifiers; synthesis may use them only with an explicit missing-identifier marker and the audit log must record the metadata gap.
- Query logging fails after recall succeeds; the workflow must surface the audit failure and avoid pretending the attempt is fully auditable.
- Capture writes to Hindsight succeed but markdown file persistence fails; the workflow must report partial success, include recovery instructions, and support retry or regeneration without duplicate retention.
- Hindsight retain fails before markdown persistence begins; the workflow must report capture failure and must not create a canonical markdown file for an unretained entry.
- Pre-clear proposes sensitive, temporary, or project-local content; the workflow must require user approval and must not retain unapproved candidates.
- Legacy MCP consumers expect the old response shape; compatibility shims must preserve exact legacy response shape only for named active consumers in the migration matrix, otherwise semantic compatibility plus migration notes is sufficient.
- Multiple Oracle banks or namespaces exist; this spec assumes the canonical Oracle bank remains the source of truth unless later planning identifies an approved compatibility boundary.
- The agent is offline or the base Hindsight daemon is unavailable; query and capture workflows must fail clearly without inventing Oracle guidance.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Oracle workflow MUST use base Hindsight primitives for recall, retain, and query logging; it MUST NOT introduce a second memory system.
- **FR-002**: The Oracle workflow MUST preserve the relevance gate instruction: only genuinely relevant PHI/OBS material may be synthesized.
- **FR-003**: When no genuinely relevant memory exists, the workflow MUST return exactly `The oracle has no entries relevant to that question.` with no additional summary, near-miss listing, or fallback recommendation in the Oracle answer.
- **FR-004**: When relevant memories exist, the workflow MUST cite PHI/OBS identifiers in the synthesized answer whenever identifiers are available.
- **FR-005**: When relevant memories conflict or imply tradeoffs, the workflow MUST surface tensions or counter-evidence before recommendations.
- **FR-006**: The workflow MUST distinguish cited Oracle memory from current-session inference.
- **FR-007**: The workflow MUST support deliberate PHI capture into the canonical Oracle bank and markdown files.
- **FR-008**: The workflow MUST support deliberate OBS capture into the canonical Oracle bank and markdown files.
- **FR-009**: Capture workflows MUST require explicit user approval before retaining durable Oracle entries or updating canonical markdown files.
- **FR-010**: Pre-clear/session-end workflows MUST propose high-signal capture candidates when present, but MUST NOT retain candidates automatically.
- **FR-011**: Oracle query attempts MUST be logged using a uniform audit record shape across native workflow calls, compatibility-shim calls, empty-result misses, and failures where logging is possible.
- **FR-012**: Audit records MUST include at minimum timestamp, query text, workflow source, recall substrate, retrieved candidate identifiers when available, accepted identifiers, relevance-gate result, rejection reasons, final outcome, and error details when applicable.
- **FR-013**: Audit records MUST NOT store full rejected candidate text by default; verbose rejected-candidate content may be captured only through an explicit diagnostic mode or later approved capture workflow.
- **FR-014**: PHI/OBS capture workflows MUST retain to Hindsight before writing canonical markdown files.
- **FR-015**: If Hindsight retain succeeds but markdown persistence fails, the workflow MUST report partial success and support retry or regeneration without creating a duplicate retained entry.
- **FR-016**: If Hindsight retain fails, the workflow MUST NOT create a canonical markdown file for the unretained entry.
- **FR-017**: Compatibility shims MUST preserve Oracle semantics for existing Oracle workflows that remain supported during migration.
- **FR-018**: Compatibility shims MUST preserve exact legacy response shape only for migration-matrix entries with named active consumers that require the old shape.
- **FR-019**: Every legacy Oracle path MUST be represented in a migration matrix with one of these statuses: delegated, replaced, retired, or blocked.
- **FR-020**: A legacy Oracle path MUST NOT be removed until replacement acceptance tests exist and pass, or until an explicit retirement note documents why the behavior is no longer supported.
- **FR-021**: The standalone oracle-query MCP path MUST have documented deprecation criteria before removal.
- **FR-022**: Migration documentation MUST identify user-visible command changes, compatibility behavior, audit impacts, rollback strategy, and known unsupported cases.
- **FR-023**: The new workflow MUST keep canonical PHI/OBS markdown files anchored in the Hindsight repository.
- **FR-024**: The migration MUST NOT redesign Hindsight storage, ranking, embeddings, daemon lifecycle, or bank schema.
- **FR-025**: The migration MUST NOT optimize or rewrite unrelated Spec Kit, Superpowers, or hook infrastructure except where needed to integrate Oracle workflow instructions.

### Compatibility Requirements

- **CR-001**: Existing user-facing Oracle query commands must continue to produce equivalent user-facing semantics through a shim until they are explicitly retired.
- **CR-002**: Existing Oracle capture commands must either delegate to the new deliberate capture workflow or provide a documented migration note before deprecation.
- **CR-003**: Existing pre-clear/session-end capture rituals must continue to propose candidates before context loss, with explicit approval required for retention.
- **CR-004**: Existing consumers of the oracle-query MCP response must receive exact legacy response shape only when the migration matrix identifies them as active consumers that require it; all other legacy paths may use semantic compatibility with migration notes.
- **CR-005**: Compatibility shims must write the same audit record shape as native workflow calls, with an additional source marker identifying the shim.
- **CR-006**: Legacy documentation must point to the new workflow once the replacement is available, while preserving rollback instructions until standalone removal is complete.

### Audit Requirements

- **AR-001**: Query audit logs must preserve empty-result misses as first-class outcomes.
- **AR-002**: Query audit logs must preserve relevance-gate rejections separately from recall failures.
- **AR-003**: Capture audit logs must distinguish proposed, approved, rejected, retained, and partially failed states.
- **AR-004**: Audit entries must be inspectable from repository-local files or base Hindsight query logs without requiring the deprecated Oracle-specific runtime.
- **AR-005**: The audit format must be stable enough for later trend review of useful hits, empty misses, compatibility-shim usage, and coverage gaps.
- **AR-006**: Query audit logs must preserve full query text by default, but must record rejected candidates by identifier and rejection reason rather than by full candidate body.
- **AR-007**: Capture audit logs must distinguish bank-retained/file-written success, bank-retained/file-write failure, and retain failure before file creation.

### Deprecation Criteria for Standalone `oracle-query` MCP Path

- **DC-001**: Native Hindsight-backed Oracle query workflow passes acceptance tests for relevant, irrelevant, empty, and failed recall scenarios.
- **DC-002**: Native Hindsight-backed capture workflow passes acceptance tests for PHI capture, OBS capture, rejection, bank-first write ordering, and partial-failure recovery.
- **DC-003**: Pre-clear candidate proposal workflow passes acceptance tests for sessions with candidates and sessions without candidates.
- **DC-004**: Compatibility matrix covers every documented legacy Oracle command, hook, skill, and MCP path, including named active consumers that require exact legacy response shape.
- **DC-005**: Compatibility shims produce uniform audit records and expose source markers.
- **DC-006**: Migration notes document replacement commands, user-visible behavior changes, rollback instructions, and removal timing.
- **DC-007**: No active acceptance test depends on Oracle-specific server logic except compatibility tests that intentionally validate shim behavior.
- **DC-008**: The user has approved removal or explicit retirement of any legacy behavior that will not be carried forward.
- **DC-009**: At least one manual dogfood session has exercised the replacement Oracle workflows with no blocking regressions before standalone `oracle-query` MCP removal.

### Key Entities *(include if feature involves data)*

- **Oracle Workflow Layer**: The skills, commands, hooks, instructions, and rituals that implement Oracle behavior over base Hindsight primitives.
- **Hindsight Recall Result**: Candidate prior memory returned from the base Hindsight substrate for relevance-gate evaluation.
- **Relevance Gate Result**: The workflow's judgment that retrieved memories are genuinely relevant, irrelevant, empty, or unavailable.
- **PHI**: A durable philosophy entry in the canonical Oracle bank and markdown files.
- **OBS**: A durable observation entry in the canonical Oracle bank and markdown files.
- **Capture Candidate**: A pre-retention PHI/OBS proposal extracted from session context for user approval.
- **Oracle Query Audit Entry**: A durable record of a query attempt, including hits, misses, gate decisions, workflow source, and failures.
- **Compatibility Shim**: A legacy command, hook, skill, or MCP adapter that delegates to the new workflow while preserving user-facing behavior during migration.
- **Migration Matrix**: A repository document that tracks each old Oracle path, replacement status, compatibility plan, tests, and deprecation decision.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of Oracle query acceptance tests use base Hindsight recall rather than Oracle-specific server recall.
- **SC-002**: Empty or irrelevant recall scenarios return exactly `The oracle has no entries relevant to that question.` in every tested native and compatibility path.
- **SC-003**: Relevant-memory query scenarios cite PHI/OBS identifiers in 100% of cases where identifiers are present in retrieved metadata or content.
- **SC-004**: Query audit tests cover relevant hits, empty misses, relevance-gate rejections, compatibility-shim calls, substrate failures, and default omission of full rejected-candidate bodies.
- **SC-005**: Capture tests verify that no PHI/OBS is retained or written canonically without explicit user approval, and that markdown persistence never precedes Hindsight retain.
- **SC-006**: Pre-clear tests verify that candidate extraction occurs before approval and that unapproved candidates are not retained.
- **SC-007**: The migration matrix accounts for every documented Oracle command, hook, skill, standalone MCP path, and named active consumer requiring exact legacy response shape before deprecation begins.
- **SC-008**: Standalone `oracle-query` MCP removal is blocked until all deprecation criteria in this spec are satisfied, including explicit user approval and one manual dogfood session with no blocking regressions, or explicitly retired by the user.

## Migration Risks

- **Risk 1 - Semantic Drift**: Replacing the standalone path could weaken the exact empty signal or relevance gate. Mitigation: acceptance tests must cover weak-match rejection and exact empty output.
- **Risk 2 - Audit Fragmentation**: Native and shimmed calls could emit different audit shapes. Mitigation: require one uniform audit record shape with source markers.
- **Risk 3 - Capture Noise**: Pre-clear automation could become automatic retention. Mitigation: preserve explicit approval and distinguish proposed versus retained states.
- **Risk 4 - Compatibility Blind Spots**: Some legacy command or MCP consumer may be missed. Mitigation: require a migration matrix before removal work.
- **Risk 5 - Partial Persistence**: Hindsight retain and markdown persistence may diverge. Mitigation: require bank-first write ordering, partial-success reporting, and retry or regeneration without duplicate retention.
- **Risk 6 - Overreach Into Hindsight Core**: The migration could expand into storage, ranking, or daemon redesign. Mitigation: keep those areas out of scope unless a later spec explicitly changes scope.
- **Risk 7 - Weak Identifier Hygiene**: Retrieved memories may lack identifiers, weakening citation quality. Mitigation: audit missing identifiers and allow synthesis only with explicit missing-identifier markers.

## Phased Roadmap

### Phase 0 - Inventory and Baseline

- Create the migration matrix for existing Oracle commands, hooks, skills, instructions, MCP paths, audit files, and canonical markdown locations.
- Record current user-facing semantics for query, empty signal, synthesis, capture, pre-clear, and audit behavior.
- Identify acceptance tests that must pass before old paths can be changed.

### Phase 1 - Native Workflow Layer

- Define the Hindsight-backed Oracle query workflow with relevance gate, exact empty signal, synthesis format, and audit entry requirements.
- Define the deliberate capture workflow for PHI/OBS entries.
- Define the pre-clear candidate proposal ritual.
- Keep the standalone Oracle MCP path available during this phase.

### Phase 2 - Compatibility Shims

- Route supported legacy commands and MCP-facing paths through the new workflow layer.
- Preserve legacy response shapes where required or document adapter behavior.
- Add audit source markers for shimmed calls.
- Update user-facing documentation to prefer the workflow layer.

### Phase 3 - Acceptance and Coverage Review

- Run native and compatibility acceptance tests for query, empty signal, synthesis, capture, pre-clear, audit, and failure scenarios.
- Review audit logs for compatibility-shim usage and empty-result misses.
- Close migration matrix gaps or mark legacy behavior as explicitly retired.

### Phase 4 - Deprecation Decision

- Compare implementation status against deprecation criteria DC-001 through DC-009.
- If criteria are met, remove or disable the standalone oracle-query MCP path.
- If criteria are not met, keep compatibility shims active and document remaining blockers.

## Assumptions

- The canonical Oracle bank already exists in Hindsight and remains the source of truth for PHI/OBS recall and retain operations.
- Canonical PHI/OBS markdown files continue to live in the Hindsight repository under existing decision-memory conventions.
- "Oracle" after migration refers to workflow semantics, not a separate memory substrate.
- The standalone oracle-query MCP path may remain temporarily for compatibility, but it should not own new behavior after the workflow layer is accepted.
- Later `/speckit.plan` work will choose concrete file paths, command names, test harnesses, and shim implementation details.
- The user prefers preserving high-signal conscious capture over comprehensive automatic retention.
