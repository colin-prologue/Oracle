<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-040 — Failure classification is a recovery-policy selector

**Date:** 2026-07-03
**Domain:** process
**Source Project:** Switchboard
**Source:** Designing cap-hit post-mortems and re-dispatch policy for an autonomous worker fleet; issue #10 presented a compound failure (permission wall + under-scoped ticket) the same night the taxonomy was drafted.

### Philosophy
Classify failures by what they discredit, and let each root select its own recovery policy. A failure event can carry multiple simultaneous roots — classify each separately rather than collapsing to one headline cause.

### Why I Hold This
A capability-wall root (permission, dependency, quota) discredits nothing about the approach: fix the wall, re-dispatch with full context. An unproductive-path root (thrash) discredits the actor's model: re-dispatch fresh with a facts-only brief excluding prior conclusions. A scope-overflow root discredits the task shape: don't retry — split. When roots are compound, the most restrictive applicable policy governs: removing a wall does not validate the approach it was blocking. Retry systems that treat all failures identically either propagate ruts or burn budget on unwinnable shapes.

### Evidence
- OBS-024 — Switchboard workers' verification contract was unsatisfiable under the permission allowlist; issue #10 was simultaneously wall-blocked AND under-scoped, so fixing the allowlist alone still left a doomed retry (supports)

### Where It Applies
Any bounded-retry system: agent orchestrators, CI retry policies, incident response runbooks, job queues with backoff, human escalation paths. Anywhere "it failed, run it again" is a policy decision.

### Known Tensions
Classification cost: cheap mechanical classes (denials) are free, but thrash-vs-overflow needs interpretation — sometimes a fresh reviewer session. Self-report bias: the failed actor classifying its own failure will misreport ruts as complexity; mechanical signals must be able to override.

### Open to Revision When
If facts-only briefs empirically propagate ruts anyway (the brief itself anchors the next attempt), or if uniform-retry systems with high enough caps outperform classified recovery on cost, the policy-selector layer is overhead.
