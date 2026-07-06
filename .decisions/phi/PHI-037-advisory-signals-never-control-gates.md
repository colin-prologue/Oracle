<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-037 — Advisory signals must never become control gates

**Date:** 2026-06-15
**Domain:** architecture
**Source Project:** Switchboard
**Source:** The "quota is advisory, never a claim gate" invariant in HDR-011.

### Philosophy
A status signal derived from a stale-prone or eventually-consistent source may inform humans and tune soft behavior (backoff, alerts, prioritization), but must never be promoted to a hard control gate. When the source is shared and the signal goes stale, a gate converts a transient condition into a system-wide wedge that outlives the condition itself.

### Why I Hold This
A soft signal degrades gracefully — a stale value just means a slightly-late alert or a too-long backoff. The same value behind a hard gate degrades catastrophically: it blocks work, and because the signal is stale it keeps blocking after the real condition has cleared. The danger compounds when the gated resource is shared, because every consumer wedges at once and none survives to clear the stale signal.

### Evidence
- OBS-021 — HDR-011: Switchboard holds quota strictly advisory; a quota-gated `sb claim` plus a stale signal would lock the whole fleet past the throttle's reset (supports).

### Where It Applies
Anywhere a derived or observed signal is tempting to reuse as a control: health checks gating traffic, quota/rate signals gating admission, feature flags driven by eventually-consistent config, cache-freshness gating reads. The signal can shape soft behavior; the hard gate needs an authoritative, fresh source.

### Known Tensions
Sometimes the advisory signal is the only signal available and the failure it warns of is worse than a wedge — e.g. admission control that must shed load to avoid collapse. There, gating on an imperfect signal is the lesser evil; the mitigation is a fail-open default and an aggressive staleness TTL, not promoting the signal to authoritative.

### Open to Revision When
The signal source becomes authoritative and synchronously fresh (not eventually-consistent), or a fail-open gate with a bounded staleness window provably cannot wedge — at which point gating is safe.
