<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-039 — Re-baseline after self-authored writes to a monitored channel

**Date:** 2026-07-02
**Domain:** architecture
**Source Project:** Switchboard
**Source:** Conformance audit of the Symphony-derived orchestrator found the parking extension's unpark signal (issue `updatedAt` change = "human touched it") was triggered by the parking notification comment itself, converting a spend cap into an unbounded dispatch/comment loop.

### Philosophy
When an automated remediation writes to the same channel it monitors for external intervention, it must re-baseline its trigger signal to the post-write state. Prefer capturing the after-action state as the new marker over filtering by actor or timestamp heuristics — actor filters break under shared identities, and timestamp heuristics race.

### Why I Hold This
A watchdog whose own output is indistinguishable from the human input it waits for self-defeats into exactly the loop it exists to prevent. The failure is invisible in unit tests because test fakes rarely model the side effect (the fake tracker didn't bump `updatedAt` on comment); it only surfaces against the real system's write-echo behavior. The fix is structural, not heuristic: read back the state after your own write and treat that as the baseline.

### Evidence
- OBS-022 — Switchboard parking self-unpark incident, 2026-07-02 (supports)

### Where It Applies
Any reconcile/watchdog loop that both observes and mutates a shared resource: bots that comment on issues/PRs and use "was it updated" as an intervention signal; alerting systems posting to logs they tail; Kubernetes-style controllers reacting to resourceVersion bumps from their own status patches; queue consumers that re-enqueue with metadata they also key retries on.

### Known Tensions
Re-baselining can mask a genuinely concurrent human action that lands in the same window as the self-write (read-back swallows their update). Shared-identity environments make the cheap alternative (filter by actor) unavailable; where distinct identities exist, actor filtering is a legitimate complement.

### Open to Revision When
If monitored channels routinely expose reliable causality metadata (e.g., event provenance IDs linking a change to its author operation), filtering by provenance would be strictly better than re-baselining and this philosophy should weaken to "prefer provenance filtering, fall back to re-baseline".
