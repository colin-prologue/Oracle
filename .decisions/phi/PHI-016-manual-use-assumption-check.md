<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-016 — Manual-Use Assumption Check

**Date:** 2026-04-30
**Domain:** process
**Source Project:** TravelPlanner
**Source:** Pre-/speckit.specify reshape of feature 002 (Trip Workspace) revealed five new working assumptions that no review gate or audit had caught — they only became visible once the predecessor features (001, 009, 012) were in actual hands-on use. Captured as a workflow rule in `.claude/rules/workflow.md` § Manual-Use Assumption Check (post-015 retrospective, 2026-04-30).

### Philosophy
Before specifying the next feature whose predecessor is in real use, check whether manual usage of the predecessor has invalidated any prior-feature assumptions. Changes noted during these user reviews should then trigger an audit pass to update artifacts, plans, and ensure prior code does not conflict with the new findings.

### Why I Hold This
Review panels see what is in scope at panel-time; they cannot replicate the feedback channel of real hands-on use. Silent assumption aging between specify-implement cycles is the failure mode this rule prevents. The reconciliation that follows the manual-use check is the audit's role — it propagates invalidations into prior artifacts so the new spec is written against current reality, not stale claims.

### Where It Applies
Any iterative product development where prior features inform the next feature's scope. Strongest fit: spec-kit-style pipelines, design-then-build cycles, MVP-then-iterate workflows, anywhere the next backlog item is shaped by what the last shipped item revealed.

### Known Tensions
For features with no real users yet (or only the implementer using them), there is no manual-use feedback channel — the check produces nothing useful. The rule's value scales with usage diversity and time-in-use. Also: an assumption-check that triggers an audit pass adds non-trivial latency before the next /speckit.specify; on small projects with rapid iteration, the cost may exceed the drift it prevents.

### Open to Revision When
- Continuous feedback channels (telemetry, automated user-flow recording, AI-summarized usage logs) become precise enough to surface assumption invalidations passively, eliminating the need for a deliberate human checkpoint.
- A unified specify-and-implement workflow makes assumption-status part of the spec data model so it is checked structurally on every gate run, not as a separate manual step.
