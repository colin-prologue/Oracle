# Feature Specification: Message Worker Autonomous Execution

**Feature Branch**: `feat/002-message-worker-autonomous`  
**Created**: 2026-05-14  
**Status**: Draft  
**Input**: User description: "Feature 002 - message-worker autonomous Speckit pilot. Create the safe feature branch and kick off the autonomous process defined in docs/autonomous-speckit-runbook.md."

## Oracle Inputs Applied

The Hindsight oracle was queried before choosing how to handle the kickoff path and existing spec numbering overlap. It returned no relevant entries, so the specification uses the runbook as the controlling artifact and records the decision in `autonomous-ledger.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Start Autonomous Work Safely (Priority: P1)

As the project owner, I need the autonomous message-worker workstream to begin on an isolated branch with an explicit feature workspace so implementation can proceed without risking `main`.

**Why this priority**: Safe isolation is the precondition for the rest of the autonomous loop. Without it, later specification, planning, and implementation work could contaminate the default branch or become hard to roll back.

**Independent Test**: Can be tested by checking the active branch, `.specify/feature.json`, and the existence of `specs/002-message-worker/`.

**Acceptance Scenarios**:

1. **Given** the repository starts on `main`, **When** Feature 002 is kicked off, **Then** work occurs on `feat/002-message-worker-autonomous`.
2. **Given** Feature 002 is active, **When** downstream Speckit commands resolve the current feature, **Then** they use `specs/002-message-worker`.
3. **Given** kickoff decisions are made without live user input, **When** the stage completes, **Then** each material assumption is recorded in the autonomous ledger.

---

### User Story 2 - Process Autonomous Work Messages (Priority: P1)

As the operator of the autonomous workflow, I need a message worker that can accept queued work instructions and drive them through the required Speckit stages with durable progress tracking.

**Why this priority**: The feature is valuable only if work messages can be transformed into auditable progress through specify, review, plan, tasks, analyze, and implement stages.

**Independent Test**: Can be tested by submitting a representative work message and verifying that the worker records stage progress, artifacts, and completion state without relying on conversational memory alone.

**Acceptance Scenarios**:

1. **Given** a new autonomous work message exists, **When** the worker begins processing it, **Then** it records the message identity, active stage, and target feature workspace.
2. **Given** a stage produces an artifact or decision, **When** the worker advances, **Then** the artifact and ledger entry are persisted before the next stage begins.
3. **Given** a work message is already completed, **When** the worker sees it again, **Then** it does not duplicate durable artifacts or replay completed side effects.

---

### User Story 3 - Recover From Interrupted Runs (Priority: P2)

As the project owner, I need the worker to resume from durable state after interruption so autonomous execution is not coupled to a single Codex session.

**Why this priority**: Autonomous work loses trust if a compaction, crash, or local interruption leaves the system unable to determine what happened.

**Independent Test**: Can be tested by interrupting execution after a stage completes, restarting the worker, and verifying that it resumes from the next incomplete stage based on persisted artifacts.

**Acceptance Scenarios**:

1. **Given** the worker stops after a stage is persisted, **When** it restarts, **Then** it resumes from the next incomplete stage.
2. **Given** the worker stops before a stage is fully persisted, **When** it restarts, **Then** it treats the partial stage as incomplete and records the recovery action.
3. **Given** durable state and conversational state disagree, **When** the worker chooses a source of truth, **Then** it trusts repository artifacts and ledger records over transient summaries.

### Edge Cases

- The repository has uncommitted or untracked files at kickoff.
- Existing spec directories already use the requested feature number for other work.
- A work message is malformed, missing required fields, or names an unsupported stage.
- The worker is interrupted while writing an artifact or ledger entry.
- The Hindsight oracle returns no relevant guidance for a required decision.
- A security-critical ambiguity remains unresolved after the contrarian research gate.
- A downstream Speckit stage cannot run because a prerequisite artifact is missing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST keep autonomous Feature 002 work off `main` by using `feat/002-message-worker-autonomous`.
- **FR-002**: The system MUST resolve Feature 002 artifacts from `specs/002-message-worker`.
- **FR-003**: The system MUST maintain `specs/002-message-worker/autonomous-ledger.md` as the required decision ledger for the workstream.
- **FR-004**: The system MUST record each stage transition in durable project artifacts before advancing to the next stage.
- **FR-005**: The system MUST process each work message idempotently so completed messages are not replayed as new work.
- **FR-006**: The system MUST record enough state to resume processing after session interruption.
- **FR-007**: The system MUST prefer repository artifacts and ledger entries over returned worker summaries when determining completed work.
- **FR-008**: The system MUST run the contrarian research gate before resolving material ambiguities, design forks, or security-sensitive decisions.
- **FR-009**: The system MUST mark unresolved security-critical ambiguity for human sign-off instead of silently choosing an unsafe default.
- **FR-010**: The system MUST produce a final review packet containing the artifacts listed in the autonomous runbook.
- **FR-011**: The system MUST preserve existing Feature 002 Oracle artifacts and MUST NOT rename or overwrite unrelated spec directories.

### Key Entities *(include if feature involves data)*

- **Work Message**: A durable request for autonomous work, including identity, requested outcome, target feature context, and processing state.
- **Message Worker**: The executor that claims work messages, advances Speckit stages, records artifacts, and handles recovery.
- **Stage Record**: Durable evidence that a Speckit stage started, completed, failed, or requires sign-off.
- **Decision Ledger Entry**: A structured record of ambiguity, contrary perspective, evidence, recommendation, rejected alternatives, risk, confidence, and sign-off status.
- **Final Review Packet**: The end-of-feature bundle that summarizes generated artifacts, commits, tests, ledger entries, and pending approvals.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A fresh checkout can identify the active Feature 002 directory from `.specify/feature.json` without relying on conversational context.
- **SC-002**: Every completed stage has at least one corresponding durable artifact or ledger entry before the next stage begins.
- **SC-003**: Re-running the worker against an already completed work message produces no duplicate spec, ledger, or implementation artifacts.
- **SC-004**: After an interrupted run, the worker can resume from the next incomplete stage using only repository state.
- **SC-005**: The final review packet lists all pending human sign-off decisions, or explicitly states that none remain.

## Assumptions

- "Message worker" refers to an autonomous worker for durable work messages that drive the Speckit lifecycle, not a general chat UI or notification system.
- The runbook is authoritative for branch name, stage order, ledger path, and final review packet contents.
- Existing `specs/002-oracle-pattern-modeling` remains unrelated historical work and must be left intact.
- Downstream planning may choose the exact message storage format and worker runtime after applying the contrarian research gate.
