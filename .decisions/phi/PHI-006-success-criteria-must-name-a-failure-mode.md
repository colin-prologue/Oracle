<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-006 — Success criteria must name a failure mode

**Date:** 2026-04-21
**Domain:** process
**Source Project:** travel
**Source:** Spec-gate /speckit.review on feature 012-design-alignment flagged SC-001/SC-003 as "vibes not criteria" because their signal was a trusted reviewer's verbal reaction; revised to observable pass/fail per step and a per-surface rubric against the design snapshot.

### Philosophy

A success criterion must name a failure mode. If the criterion cannot fail under honest evaluation — because its signal is a trusted reviewer's verbal reaction, a qualitative impression, or any measure whose absence is easier than its presence — it is not a criterion, it is a wish. Replace with observable pass/fail checks, rubric items checked against an artifact, or measurable regressions before accepting the criterion into scope.

### Why I Hold This

Spec 012's original SC-001 required the primary user "not comment on unfinished UI" and SC-003 required them to "describe the app as polished." The primary user is a family member in a trust-rich relationship; social-desirability bias makes both criteria trivially passable while the feature could still miss its goal. The revision to observable completion + a per-surface rubric against the design snapshot turned two vibes into two checks that can visibly fail.

### Where It Applies

Any artifact that encodes acceptance gates: spec success criteria, Definition of Done, PR checklists, deploy readiness checklists, incident postmortem exit criteria, research conclusions. Applies most strongly where the evaluator is trusted or motivated to pass the check.

### Known Tensions

Qualitative signals (primary-user delight, team morale, code "feel") are real and sometimes matter more than any rubric. The PHI does not forbid capturing them — it forbids treating them as gates. Capture as supplementary, non-gating signals alongside the falsifiable checks.

Rubrics can also fail by being too granular (checklist theater) or too shallow (pass-everyone). The fix for both is keeping the rubric tight, snapshot-anchored, and dimensional (typography, spacing, color, behavior) rather than feature-by-feature.

### Open to Revision When

A criterion proves falsifiable in practice despite being phrased qualitatively (e.g., a trusted reviewer with a track record of blocking bad work); or a rubric fails to catch a regression a vibes-check would have. Either would suggest the distinction is weaker than this PHI claims.
