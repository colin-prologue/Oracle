<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

**Status:** merged → PHI-030 2026-07-06

## PHI-041 — Evidence before self-report: read order preserves reviewer independence

**Date:** 2026-07-03
**Domain:** process
**Source Project:** Switchboard
**Source:** Designing the park-time fail-review verifier (fresh session dissecting capped worker sessions); the anti-anchoring protocol emerged while deciding what evidence the reviewer receives and in what order.

### Philosophy
When a fresh reviewer dissects another actor's failure, sequence the evidence: mechanics first, self-report last, disagreements surfaced. The reviewer forms its classification from objective signals and ground-truth records before reading the failed actor's own account, then reconciles — reporting both verdicts when they differ.

### Why I Hold This
Reading the self-report first buys anchored agreement, not independence: you pay for a fresh perspective and receive the rut's self-justification with a second signature. A failed actor plausibly misclassifies its own rut (thrash self-reported as complexity or blockage). The self-report informs; mechanical signals decide ties. Precedent within the same project: issue #10's failure class was diagnosed correctly from transcript mechanics alone (denial strings, retry loops), with no worker testimony needed.

### Evidence
- OBS-024 — permission-wall diagnosis derived from transcript mechanics alone; worker self-context unnecessary and potentially misleading (supports)
- OBS-023 / test-doubles blind-spot line — independent verification must bring its own model rather than reuse the author's (supports, sibling concern)

### Where It Applies
Post-mortem reviewers over agent sessions, incident review after on-call self-reports, code review of self-described PRs, audit of delegated actions, LLM-judge pipelines evaluating LLM outputs. Anywhere the evaluated party authored an account of its own performance.

### Known Tensions
Cost: reading raw evidence first is slower than starting from the summary. For mechanically unambiguous failures the ordering is moot — the discipline only earns its overhead where interpretation matters. Extreme form (never read self-reports) discards genuinely useful pointers.

### Open to Revision When
If evidence-first reviewers empirically converge on the same verdicts as summary-first reviewers at materially lower cost, the ordering is ceremony; or if self-reports become schema-constrained to facts-only such that anchoring content no longer exists in them.
