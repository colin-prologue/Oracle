<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-015 — Protocol Uniformity Over Fast-Path Latency in Audit-Trail Systems

**Date:** 2026-04-26
**Domain:** architecture
**Source Project:** Claude-Root
**Source:** Spec 010 plan-gate re-review C-5 resolution: chose to fold `.run/abort` sentinel detection into `run-decide-next.sh` rather than retain it as a fast-path orchestrator check. The trade was a small per-stage latency cost for a single uniform invariant in the verdict-receipt audit substrate.

### Philosophy
When a routing or decision protocol has a "fast-path" exception alongside the main decision path (e.g., a sentinel file checked between normal decisions, or a cache hit short-circuiting the validation chain), prefer folding the exception into the main path — even at modest latency cost. Two paths means the audit substrate carries two rules; one path means readers, tools, and tests confront the same invariant for every decision. Latency overhead per decision is almost always negligible compared to the cost of debugging an asymmetric audit record three months later, when the fast-path's data shape no longer matches the main path's.

### Why I Hold This
Audit substrates outlive the systems they record. A protocol with N decision-paths produces N decision-shapes in the durable log; consumers of that log (people, dashboards, replays, validators) must understand all N. Each fast-path is a future cognitive tax and a future drift risk — the slow path evolves, the fast path is forgotten, and the audit record diverges silently. The "saved 200ms" intuition that motivates fast-paths is almost always a local optimization that buys nothing the user can perceive while spending a global property (uniformity) the future maintainer urgently needs.

### Where It Applies
Routing protocols, cache/origin lookups feeding decisions, sentinel-file pre-checks, feature-flag fast-paths around expensive validation, "trust the in-memory copy" shortcuts in distributed systems. The principle is strongest where the decisions are recorded for later inspection — orchestrators, schedulers, gating workflows, audit logs, ledger systems.

### Known Tensions
- Genuine latency-sensitive paths (sub-ms decision loops, tight-loop hot paths) cannot absorb a full validation chain per call; uniformity is a luxury the budget doesn't allow.
- Some fast-paths exist precisely because the slow path is unsafe to invoke under certain conditions (e.g., during shutdown or initialization). Folding them in requires the slow path to handle those conditions, which is itself a uniformity violation.
- Diagnostic paths (tracing, profiling) sometimes need to bypass the main protocol to avoid recursive instrumentation; the bypass is a feature, not a defect.

### Open to Revision When
Profiling shows the latency cost is no longer modest (e.g., the per-decision overhead bites a user-perceptible budget), OR when the audit substrate is genuinely write-only (no consumer reads the records) so the uniformity property buys nothing, OR when the "fast-path" is in fact a different decision concern that conflating into the main path would muddle rather than unify.
