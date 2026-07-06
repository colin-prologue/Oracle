<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-036 — Observe metered resources out-of-band

**Date:** 2026-06-15
**Domain:** architecture
**Source Project:** Switchboard
**Source:** Designing the quota/liveness signal for a fleet of LLM workers on a shared subscription budget (HDR-011).

### Philosophy
The component that reports a resource's health or remaining capacity must not consume that resource. Observe metered or shared resources out-of-band — otherwise the monitor goes dark precisely when the exhaustion it exists to report arrives. The reporter must not be the thing that fails.

### Why I Hold This
A status signal whose producer draws on the very resource being constrained has a circular failure mode: when the resource is exhausted, the reporter cannot run, so the outage is silent exactly when it matters most. This is the observation-side sibling of an independence I already hold elsewhere — session-independent daemons (PHI-001) and independent verification of work (PHI-030). The fix is the same shape: move the observer off the constrained path.

### Evidence
- OBS-021 — HDR-011: a subscription LLM fleet's quota/liveness monitor must run outside the fleet, token-free and without shared auth, so a full cap or dead fleet is still reported (supports).

### Where It Applies
Any monitored system on a metered, shared, or exhaustible resource: LLM fleets on rate/usage budgets, connection-pool or quota dashboards, disk/memory watchdogs, heartbeat/liveness checks. Whenever a signal's job is to warn about resource exhaustion, the signal's producer must not depend on that resource.

### Known Tensions
Out-of-band observers add a second always-on component to run and maintain, and they often see a coarser, more reactive signal (e.g. a post-hoc error rather than a proactive gauge) than an in-band probe would. When the resource realistically never exhausts, in-band simplicity can win.

### Open to Revision When
The platform exposes a reliable in-band capacity gauge that remains queryable under exhaustion (e.g. a cap-aware endpoint that still answers when throttled), removing the circular dependency.
