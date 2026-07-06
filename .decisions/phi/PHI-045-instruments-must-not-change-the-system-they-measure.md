<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-045 — Instruments must not change the system they measure

**Date:** 2026-07-05
**Domain:** architecture
**Source Project:** rts-proto
**Source:** Gate 7 balance-harness design: the deterministic sim had no outcome variance (seed inert), and the cheapest path was to add RNG draws inside the sim — which would have moved every committed golden and changed game feel as a side effect of building a measurement tool.

### Philosophy
Measurement instruments (harnesses, benchmarks, analytics, telemetry) must not alter the system they measure. When the instrument needs a property the subject lacks — variance, hooks, observability — supply it in the instrument's own layer; when an instrument finding implicates the subject itself, route it to the subject's design queue as a first-class decision, never patch the subject as a side effect of tooling and never work around it inside the tool.

### Why I Hold This
A change that moves the subject's committed contracts (goldens, behavior, feel) to serve the instrument is a design decision smuggled in as infrastructure — it bypasses the review altitude design changes deserve. The reverse failure (tool-side workarounds hiding subject defects) silently corrupts every future measurement. rts-proto's balance harness got its variance from seeded setup jitter in the harness layer, and when it surfaced a real sim fairness defect (57%/84% side split), the defect became a design-debt issue with its own decision record, not a harness correction.

### Evidence
- OBS-027 — rts-proto balance harness: variance in sampling layer, sim untouched, bias finding routed to design queue; era prior art (BW/C&C/WC3/AoE2) only ever added in-sim randomness as game design (supports)

### Where It Applies
Benchmark suites, load/perf harnesses, balance/simulation testing, analytics instrumentation, observability hooks in pure cores — anywhere a measurement layer sits on a system with its own correctness contracts.

### Known Tensions
Sometimes the subject genuinely lacks a property the measurement needs and the instrument layer cannot fake it (e.g., observability requires a real hook). Then the subject change should go through the subject's own design process — the philosophy prices the path, it doesn't forbid the change.

### Open to Revision When
An instrument-layer substitute (like setup jitter) repeatedly produces conclusions that in-subject variance later invalidates — evidence the substitution measured the wrong thing.
