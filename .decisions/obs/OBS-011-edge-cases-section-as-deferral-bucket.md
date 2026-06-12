<!-- ORACLE ARTIFACT — canonical copy in the oracle bank; this file is a browse mirror in the Hindsight repo. Observed evidence, not a held philosophy. -->

**Status:** active

## OBS-011 — Edge Cases Section as Deferral Bucket

**Date:** 2026-04-26
**Source:** Spec 010 (autonomous-workflow) review — Phase A reviewers (delivery-reviewer, devils-advocate) found that 5 of the 8 listed Edge Cases were not edge cases at all, but core control-flow questions the orchestrator must answer on every run (what happens when no spec exists yet, what happens on stage failure, what happens during simultaneous clarifications, etc.). They were promoted to FR-021..028 in revision.

### Pattern
Edge Cases sections in specs sometimes function as deferral buckets rather than enumerations. When every "edge case" listed is actually core control flow that the system must answer on every run, the section is being used to defer decisions, not to surface them.

### Reviewer-Detectable Smell
Every Edge Case bullet promotes cleanly to a Functional Requirement under challenge. If a reviewer can take any line item from the section and rewrite it as "FR-NNN: System MUST ..." without losing meaning or adding scope, that line item was a deferred FR, not an edge case.

### True Edge Cases vs Deferred FRs
- **True edge case**: A condition that is rare, recoverable, or out-of-scope-but-worth-noting. Example: "if disk fills mid-write, the run aborts and the partial log is retained."
- **Deferred FR**: A condition that occurs on every run or every meaningful run, and the system''s behavior under that condition is part of the contract. Example: "if the stage fails, the orchestrator decides whether to retry, halt, or escalate." That is not an edge case — that is the spec.

### Why This Matters
A spec that defers core control flow to an Edge Cases section will pass shallow review (the bullets exist) and fail at plan time (the implementer has to invent the answers). It also masks the spec''s true complexity from gatekeepers — "only 8 FRs" looks small, but "8 FRs + 8 deferred FRs in Edge Cases" is what the implementer actually has to build.

### Related
PHI-013 (architectural model where the coordinator must answer ''what happens if subagent X does Y'' for every Y, every run — those answers belong in FRs, not edge cases)
