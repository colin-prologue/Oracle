# Autonomous Speckit Runbook (Zero-Input Mode)

## Purpose

Define how Speckit/Codex can execute a full feature lifecycle with zero live user
input, while preserving auditability and assumption challenge quality.

Pilot scope: **Feature 002 — message-worker**.

---

## Kickoff (Safe-by-default)

Use this exact startup sequence before running the autonomous loop:

1. Ensure your working tree is clean on `main`.
2. Create a dedicated feature branch:
   - `feat/002-message-worker-autonomous`
3. Run `/speckit.specify` for Feature 002.
4. Continue through `/speckit.review` → `/speckit.plan` → `/speckit.tasks`
   → `/speckit.analyze` → `/speckit.implement`.

### Branching policy

- **Do not run autonomous implementation on `main`.**
- **Assume `/speckit.specify` does not create branches for you.** Treat branch
  creation as a required manual pre-step.
- Commit after each stage (or logical slice) so rollback is trivial.
- Push branch snapshots regularly to avoid local-only history loss.

---

## Workflow Stages

1. Specify
2. Review
3. Plan
4. Tasks
5. Analyze
6. Implement

Each stage must append decisions to the feature decision ledger before advancing.

---

## New Mandatory Step: Contrarian Research Gate

When an ambiguity, open question, or design fork appears, do **not** immediately
pick the default path.

Run this gate first:

1. **State the baseline assumption** (what we currently think is true).
2. **Generate at least one contrary perspective** that could invalidate it.
3. **Research both sides** using available project artifacts and any needed
   external primary sources.
4. **Stress-test consequences** of being wrong on each path (security,
   reliability, operability, scope risk).
5. **Choose a recommendation** with explicit rationale.
6. **Log the decision** (including rejected alternative) before proceeding.

If uncertainty remains high and the issue is security-critical, halt and mark for
human sign-off in the final review packet.

---

## Decision Ledger Contract

For feature 002, maintain:

- `specs/002-message-worker/autonomous-ledger.md`

Each entry includes:

- Timestamp (UTC)
- Stage
- Decision ID
- Question or ambiguity
- Baseline assumption
- Contrary perspective
- Evidence reviewed
- Recommendation
- Rejected alternative(s)
- Risk if wrong
- Confidence (High/Medium/Low)
- Requires human sign-off (Yes/No)

No stage transition is allowed unless required ledger fields are present.

---

## Non-Interactive Policy

- Do not ask the user questions during execution.
- Resolve ambiguities via the Contrarian Research Gate.
- Record unresolved/unsafe items for final approval packet.

---

## Final Review Packet (end of feature 002)

Provide:

1. Updated `spec.md`
2. Review findings + resolutions
3. `plan.md`
4. `tasks.md`
5. Analysis report
6. Implementation summary + commits
7. Test results
8. `autonomous-ledger.md`
9. Pending sign-off decisions
