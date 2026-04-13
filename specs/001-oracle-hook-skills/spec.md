# Feature Specification: Decision Oracle Phase 2 — Hook Skills

**Feature Branch**: `001-oracle-hook-skills`
**Created**: 2026-04-12
**Status**: Draft

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Oracle Query at Decision Points (Priority: P1)

During spec elaboration or implementation planning, the developer invokes `/oracle` with a decision question. The oracle queries the Hindsight bank using `reflect` and returns a synthesis of relevant prior decisions, patterns, and constraints — all in context, without leaving the Claude Code session.

**Why this priority**: The core value of the oracle is surfacing historical decisions at the moment they are needed. Without this, accumulated CDRs and ADRs are unsearchable during active work.

**Independent Test**: Can be tested by running `/oracle "Should we use X or Y?"` and confirming the oracle returns a structured response drawing from retained CDRs/ADRs. Delivers immediate decision support value as a standalone capability.

**Acceptance Scenarios**:

1. **Given** the Hindsight daemon is running and the oracle bank has retained CDRs/ADRs, **When** the developer runs `/oracle "What patterns do I use for agent coordination?"`, **Then** the oracle returns a response that references relevant retained decisions, names any contradictions with current direction, and surfaces the constraints that drove prior choices.
2. **Given** the oracle bank is empty or unreachable, **When** `/oracle` is invoked, **Then** the system surfaces a clear error message without crashing the session.
3. **Given** a vague or broad query, **When** `/oracle` is invoked, **Then** the oracle still returns a useful response based on whatever relevant context it can find, rather than refusing to answer.

---

### User Story 2 — CDR Capture After a Confirmed Decision (Priority: P1)

After a decision is confirmed during spec elaboration or implementation, the developer invokes `/oracle-capture` with a brief description. Claude drafts a full CDR in the standard schema, presents it for review, and — on confirmation — retains it to the Hindsight oracle bank and writes the canonical file to `.decisions/cdrs/`.

**Why this priority**: CDR quality depends on capturing decisions immediately after they are made, while context is fresh. Manual logging after the fact loses nuance about rejected options and constraints.

**Independent Test**: Can be tested by running `/oracle-capture "Chose X over Y because Z"` and confirming a CDR file appears in `.decisions/cdrs/` and is retrievable via `/oracle`. Delivers full capture-to-retrieval loop as a standalone capability.

**Acceptance Scenarios**:

1. **Given** a decision was just made in the session, **When** the developer runs `/oracle-capture "Chose Hindsight over Graphiti for oracle layer"`, **Then** Claude drafts a CDR using the standard schema (decision, context, options considered, constraints, confidence, revisit trigger), presents it for confirmation, and proceeds only after approval.
2. **Given** the developer confirms the drafted CDR, **When** capture proceeds, **Then** the CDR is retained to the oracle bank via the Hindsight API and written to `.decisions/cdrs/CDR-{next-id}.md` with correct sequential numbering.
3. **Given** the developer rejects the draft or requests edits, **When** feedback is provided, **Then** Claude revises the CDR and presents it again before retaining.

---

### User Story 3 — Oracle Integration Points in SpecKit Workflow (Priority: P2)

The SpecKit specify workflow prompts for oracle queries at natural decision points during spec elaboration, and the approval workflow invokes oracle capture after decisions are confirmed. The developer does not need to remember to query or capture — the workflow surfaces the prompts.

**Why this priority**: Without integration, the oracle depends on the developer remembering to invoke it. Integration makes the workflow self-reinforcing.

**Independent Test**: Can be tested by running `/speckit.specify` on a new feature and verifying that oracle query prompts appear at decision points. Independently valuable even if `/oracle` and `/oracle-capture` are not yet customized.

**Acceptance Scenarios**:

1. **Given** the developer runs `/speckit.specify` on a new feature, **When** the spec elaboration reaches architectural or tech-selection decision points, **Then** the workflow prompts the developer to run `/oracle` with a suggested question before committing to a requirement.
2. **Given** the spec elaboration is complete and the developer is about to approve, **When** the approval step runs, **Then** the workflow reminds the developer to capture any confirmed decisions via `/oracle-capture`.

---

### User Story 4 — Session End Protocol (Priority: P3)

At the end of every session, the developer is prompted to write a brief session summary and retain it to the oracle bank. This feeds the Observation layer over time.

**Why this priority**: Session logs are the lowest-signal input but compound significantly over time. Without a protocol, they are never captured.

**Independent Test**: Can be tested by following the session-end protocol manually and confirming the summary appears in oracle recall results in the next session.

**Acceptance Scenarios**:

1. **Given** a session is wrapping up, **When** the developer follows the session-end protocol, **Then** a 3–5 sentence summary is retained to the oracle bank as a session-log type entry.

---

### Edge Cases

- What happens when the Hindsight daemon is not running when `/oracle` or `/oracle-capture` is invoked? The skill must surface a clear, actionable error (e.g., "daemon not running — start with `uvx hindsight-embed daemon start`") rather than a cryptic failure.
- What if the CDR sequential numbering produces a collision? The capture skill must check existing files before assigning a number.
- What if the oracle bank returns no results for a query? The skill should acknowledge this explicitly rather than hallucinating a response.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `/oracle` skill MUST call Hindsight's `reflect` API on the `oracle` bank with the developer's query and return the synthesized response inline in the Claude Code session.
- **FR-002**: The `/oracle` skill MUST surface a clear error message if the Hindsight daemon is unreachable (connection refused, timeout, non-200 response).
- **FR-003**: The `/oracle-capture` skill MUST draft a CDR in the standard schema (decision, context, options considered, constraints, confidence, revisit trigger) using context from the current session before presenting it for review.
- **FR-004**: The `/oracle-capture` skill MUST await explicit developer confirmation before retaining to the oracle bank or writing to disk.
- **FR-005**: The `/oracle-capture` skill MUST assign the next sequential CDR number by scanning existing files in `.decisions/cdrs/`.
- **FR-006**: The `/oracle-capture` skill MUST retain the CDR to the oracle bank via the Hindsight `retain` API with metadata including type, project, domain, date, and confidence.
- **FR-007**: The `/oracle-capture` skill MUST write the canonical CDR file to `.decisions/cdrs/CDR-{NNN}-{slug}.md`.
- **FR-008**: The SpecKit specify skill MUST prompt the developer to invoke `/oracle` at least once at an architectural or technology decision point during elaboration.
- **FR-009**: The SpecKit specify skill MUST remind the developer to invoke `/oracle-capture` for confirmed decisions at the end of elaboration.
- **FR-010**: The project CLAUDE.md MUST include a Session End Protocol section that describes the 3-step process for writing and retaining a session summary.

### Key Entities

- **Oracle Query**: A developer-provided question submitted to Hindsight's `reflect` API; returns a synthesis of relevant prior decisions.
- **CDR (Coding Decision Record)**: A structured markdown document capturing a confirmed decision, its context, the options considered, constraints, confidence level, and revisit trigger.
- **Hindsight Bank**: The `oracle` bank in the running Hindsight daemon, containing retained CDRs, ADRs, session logs, and the Decision Constitution mental model.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The developer can invoke `/oracle` and receive a response grounded in oracle bank content within the same Claude Code session, without any additional setup.
- **SC-002**: The developer can invoke `/oracle-capture` and have a confirmed CDR written to `.decisions/cdrs/` and retrievable via future `/oracle` queries, within a single interaction.
- **SC-003**: Running `/speckit.specify` on a new feature produces at least one oracle query prompt and one capture reminder, without requiring the developer to remember to invoke them.
- **SC-004**: The session-end protocol is documented in CLAUDE.md and produces a retained session log that surfaces in oracle recall results in a subsequent session.

## Assumptions

- The Hindsight daemon is running locally on `http://localhost:8888` (the configured default).
- The oracle bank (`bank_id="oracle"`) has already been configured with its mission, directives, and Decision Constitution (Phase 1 complete).
- Both skills are implemented as Claude Code custom skills (SKILL.md files), not MCP tools or external scripts.
- The Hindsight `reflect` API is called via `curl` or Python from within the skill prompt; skills do not require a dedicated Python script file.
- CDR capture is semi-manual by design — the developer must explicitly invoke `/oracle-capture`; it is never triggered automatically.
- The SpecKit specify workflow is extended by editing the skill's SKILL.md prompt, not by modifying `.specify/extensions.yml` hooks (which are reserved for git operations).
