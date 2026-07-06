<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-043 — Data-shaped extension points over callback-shaped ones in pure cores

**Date:** 2026-07-04
**Domain:** architecture
**Source Project:** rts-proto (the philosophy itself is cross-project)
**Source:** Ratifying the sim-events decision — a proposed callback sink on the deterministic sim reducer was replaced by an optional out-array before implementation.

### Philosophy
In deterministic or pure cores (reducers, sim steps, transaction appliers), extension points should be data-shaped, not callback-shaped: an optional out-array/event log the core fills, never a callback the core invokes. A callback executes caller code mid-mutation and is an impurity vector held shut only by convention; data cannot run code, so the reentrancy/purity hazard is eliminated structurally rather than policed.

### Why I Hold This
rts-proto's sim-events decision (2026-07-03) originally proposed `step(state, commands, sink)` with a callback sink. The callback would have required a standing rule — "sink implementations must not observe or mutate state mid-step" — that every future consumer had to remember. Replacing it with `step(state, commands, events?: SimEvent[])` deleted the rule instead of enforcing it: an array cannot execute anything. The same repo made the identical move twice more (fixed-point newtype over "fenced floats" discipline; import allowlist over review-enforced render/sim boundary), and each time the convention-free variant cost nothing in ergonomics.

### Evidence
- rts-proto `docs/decisions/sim-events.md`, ratified 2026-07-03: out-array over callback sink; Gate 6 verified events changed no golden hashes (supports)

### Where It Applies
Any pure/deterministic execution core that needs to report richer output than its return value: game sim reducers, event-sourced aggregates, compiler passes emitting diagnostics, migration appliers emitting audit records, state machines emitting transitions.

### Known Tensions
Callbacks allow streaming/early-abort semantics an out-array cannot express; when the consumer genuinely needs to react mid-execution (backpressure, cancellation), a data-shaped point is insufficient and the purity cost must be weighed openly.

### Open to Revision When
A real case shows the out-array's buffer-everything semantics causing measurable memory or latency harm that a disciplined callback would avoid, or the language/runtime gains effect-typing that makes callback purity machine-checkable.
