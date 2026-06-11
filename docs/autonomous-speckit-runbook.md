# Autonomous Speckit Runbook (Zero-Input Mode)

## Purpose

Define how Speckit/Codex executes a full feature lifecycle with zero live user
input, while preserving auditability and assumption challenge quality.

This runbook is feature-agnostic. Substitute the active feature's number and
slug (written `<NNN>-<slug>` below) wherever a path or branch name appears.

---

## Mode Name + Invocation

Canonical mode name: **CAP** (Contrarian Autopilot).

Per-run, suffix the mode with the active feature number — e.g. `CAP-002` pins a
run to Feature 002. The concise label is easier to reference in commits, logs,
and reports.

Suggested shorthand in notes/commits:
- `CAP-<NNN>` (canonical, e.g. `CAP-002`)
- `Cap-<NNN>` (accepted human-readable variant; normalize to `CAP-<NNN>` in files)

### Slash command status

There is no guaranteed built-in single slash command that runs the entire loop
end-to-end autonomously. Treat this mode as an **orchestration policy** over
existing commands:

1. `/speckit.specify`
2. `/speckit.review`
3. `/speckit.plan`
4. `/speckit.tasks`
5. `/speckit.analyze`
6. `/speckit.implement`
7. `/speckit.codereview`
8. `/speckit.audit`

If you want one-entry invocation, create a local wrapper command (for example
`/speckit.autopilot`) that calls the sequence above and enforces this runbook.

---

## Kickoff (Safe-by-default)

Use this exact startup sequence before running the autonomous loop:

1. Ensure your working tree is clean on `main`.
2. Create a dedicated feature branch:
   - `feat/<NNN>-<slug>-autonomous`
3. Run `/speckit.specify` for the feature.
4. Continue through `/speckit.review` → `/speckit.plan` → `/speckit.tasks`
   → `/speckit.analyze` → `/speckit.implement` → `/speckit.codereview`
   → `/speckit.audit`.

### Branching policy

- **Do not run autonomous implementation on `main`.**
- **Assume `/speckit.specify` does not create branches for you.** Treat branch
  creation as a required manual pre-step.
- Commit after each stage (or logical slice) so rollback is trivial.
- Push branch snapshots regularly to avoid local-only history loss.

---

## Root Cause Analysis: Why autonomous runs stop early

1. **Stage-complete vs feature-complete ambiguity**
   - Prior runs treated completion of documents as completion of feature delivery.
2. **No autonomous re-entry rule**
   - The loop lacked a mandatory "loop again until done criteria are met" control.
3. **No hard blocker escalation format**
   - Human-required decisions were not surfaced as explicit blocking questions.

### Corrective controls (mandatory)

- Add a formal **Done Contract** (below).
- Add a **Re-entry Loop Rule** that auto-runs additional implementation slices.
- Add a **Blocker Escalation Contract** for human-required decisions.

---

## Done Contract (feature-complete, not stage-complete)

A run is complete only when all are true:

1. All tasks in `tasks.md` are checked complete.
2. Required automated tests are implemented and passing.
3. Manual test checklist is executed and logged (when applicable).
4. `/speckit.codereview` findings are resolved or waived with rationale.
5. `/speckit.audit` passes with no unresolved high-severity mismatches.
6. Ledger has no unresolved blocking decisions.

If any item is false, the run is **not complete** and must continue autonomously.

---

## Re-entry Loop Rule (self-improving autonomous cycle)

After every `/speckit.audit`:

1. Read unresolved tasks, review findings, and audit gaps.
2. Generate next smallest executable slice (prefer 1–3 tasks).
3. Execute `/speckit.implement` for that slice.
4. Execute `/speckit.codereview`.
5. Execute `/speckit.audit`.
6. Repeat until Done Contract is satisfied.

This is the control that prevents premature stopping.

---

## Mandatory Step: Contrarian Research Gate

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

If uncertainty remains high and the issue is security-critical, trigger blocker
escalation and continue all non-blocked work.

---

## Blocker Escalation Contract (clear human questions)

Only escalate when work is truly blocked by a human decision. Each blocker must
be logged and raised in this exact format:

- **Blocker ID**
- **Decision needed** (one sentence)
- **Why blocked** (what task cannot proceed)
- **Option A** (recommended) + impact
- **Option B** (contrary) + impact
- **Default if no response by date** (explicit date in UTC)
- **Latest safe point reached** (commit hash + artifact)

If no answer by the deadline, the run proceeds using the default and logs that
choice in the ledger.

---

## Decision Ledger Contract

Maintain a per-feature decision ledger at:

- `specs/<NNN>-<slug>/autonomous-ledger.md`

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

- Do not ask the user questions during normal execution.
- Resolve ambiguities via the Contrarian Research Gate.
- Use Blocker Escalation Contract only for true hard blockers.

---

## Final Review Packet (feature-complete handoff)

Provide:

1. Updated `spec.md`
2. Review findings + resolutions
3. `plan.md`
4. `tasks.md` (all checked)
5. Analysis report
6. Implementation summary + commits
7. Automated and manual test results
8. `autonomous-ledger.md`
9. Any blocker escalations and final dispositions

---

## Reporting format (must include Recommended Next Steps)

Every status summary (intermediate and final) must include:

1. Completed in this slice
2. Remaining blockers/risks
3. **Recommended Next Steps** (ordered, actionable, and mapped to task IDs)

Recommended Next Steps should be a short ordered list with command-or-task precision
(e.g., `T003: implement /send route handler`, `run npm test`, `run /speckit.audit`).
