---
name: oracle-debate
description: Capture a team Philosophy (PHI) — drafts a held opinion from session context, debates it with the user, writes the record on a branch, and opens a PR whose review is the adoption gate. Invoked via /oracle-debate "[philosophy]".
---

# Capture a Philosophy (PHI)

Resolve `ORACLE_ROOT` (env var; default `~/team-oracle`). All writes go there —
never into the current project's tree.

## Arguments

`$ARGUMENTS` describes the philosophy. If empty, draft from what this session
surfaced and say so.

## Execution

1. **Admission test first.** Ask: would this change the team's default on a NEW
   project with no prior context? If no, it belongs in the current project's
   ADRs — say so and stop.

2. **Fit check.** Load `INDEX.md` (prefer `git show origin/main:INDEX.md`).
   If an existing PHI already covers this, propose amending its Status/Tensions
   via PR instead of drafting a duplicate. If a related PHI conflicts, plan to
   cite it under Known Tensions — opposing `contested` PHIs may coexist.

3. **Allocate the ID.** Next number = max PHI-NNN across local
   `records/phi/` and `origin/main:INDEX.md`, +1. A collision with a
   concurrent PR surfaces as an INDEX.md merge conflict — renumber then.

4. **Draft** using `records/_templates/phi-template.md`, `Status: proposed`,
   sponsor = the user. Keep the Philosophy section to a disposition, not a rule.

5. **Debate.** Present the draft and argue against it before the user does:
   name the weakest point, the strongest counter-scenario, and what evidence
   would kill it. Revise until the user confirms. If they abandon it, stop —
   no artifacts.

6. **Write and propose.** On a new branch in `$ORACLE_ROOT`:
   - write `records/phi/PHI-{NNN}-{slug}.md`
   - add its line to `INDEX.md` under Philosophies
   - commit, push, open a PR titled `PHI-{NNN}: {title}`. The PR body carries
     the Philosophy section verbatim plus the strongest objection from the
     debate, so the reviewer engages the substance.

7. **Explain the gate:** approval + merge flips Status to `adopted` (reviewer
   edits the line in the same PR, or a follow-up commit does); a reviewer who
   disagrees but agrees it's worth keeping merges it as `contested` with their
   position added under Known Tensions.
