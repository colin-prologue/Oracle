<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-028 — Decide-Async With Steelman Records, Review-Bound at the Merge Gate

**Date:** 2026-06-11
**Domain:** process
**Source Project:** mini-fax
**Source:** ADR-043 (Agent Decision Records) design + first full lifecycle: 15 AGDRs captured, batch-reviewed, two overturned as cheap pre-implementation replans.

### Philosophy
When delegating work to an agent, let it decide-and-proceed on pivotal judgment calls — those that foreclose alternatives, are expensive to reverse, resolve spec ambiguity by interpretation, or commit money/scope/schedule — provided each call produces a record that steelmans the rejected option and states blast radius (what builds on the decision + unwind cost). Review is fully async during the run but BINDING at the PR-merge gate: no merge with unreviewed records. Hard-escalation domains (security invariants, production deploys, secret material, frozen contracts) remain excluded — a record is never a license to proceed there.

### Why I Hold This
The PR-boundary placement makes overturning cheap: an on-branch overturn is a replan, a post-merge overturn is archaeology. The steelman requirement counters self-justification — an agent forced to write the rejected option's strongest honest case cannot produce a pure rationalization. The blast-radius field is what makes async review survivable: a late overturn starts from the record's own unwind notes. First exercise validated the shape: a retroactive batch surfaced a genuine spec defect (a 3.3x-inflated cost premise two FULL review panels had computed with), and both overturns executed before implementation locked anything in. A record's own revision conditions also fired correctly at the next gate and were honored rather than relitigated.

### Where It Applies
Any agent-delegated workflow with a merge/release boundary: feature implementation runs, autonomous goal-prompt sessions, spec/plan drafting, ops automation with change-review. Pairs with PHI-026 (same boundary, inverse case: stop-and-report for defects originating in earlier scope; proceed-with-record for forward judgment calls).

### Known Tensions
The pivotal test is self-administered — an agent that misjudges "routine" never writes the record; the only backstops are code-review checklists and human diff review. Review burden concentrates at PR gates and invites rubber-stamping; neutral status phrasing and small batch sizes (pivotal-only capture) are the mitigations. Records written by the decider always skew toward the decision; the steelman shrinks but does not eliminate this.

### Open to Revision When
If batch reviews at the gate show systematic rubber-stamping (verdicts tracking recommendations near-100% over many batches), the async model is laundering rather than governing — revert pivotal classes to pre-approval. If chain depth between gates grows so long that overturns regularly cascade beyond one PR's scope, insert intermediate checkpoints (the rejected circuit-breaker-cap option becomes right).
