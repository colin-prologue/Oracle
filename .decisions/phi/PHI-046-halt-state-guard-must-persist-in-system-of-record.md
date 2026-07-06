<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-046 — A halt-state guard must persist in the system of record

**Date:** 2026-07-05
**Domain:** architecture
**Source Project:** Switchboard
**Source:** in-memory session-cap park re-granted the full cap on pool restart (#28); durable tracker-label fix

### Philosophy
A safety checkpoint whose purpose is to *halt* work — a session cap, a park, a kill-switch, a dedup marker, a circuit breaker — must persist its state in the durable system of record, not in process memory. Keeping halt-state in memory means a restart re-grants the full budget with no error: the guard quietly stops guarding exactly when the process churns.

### Why I Hold This
The failure mode is silent, which is what makes it dangerous — nothing throws, no log fires, the counter simply resets. A guard exists to stop something expensive or unsafe, and an in-memory guard's blind spot is the one event most likely to happen under load or failure: a restart. Persisting the state where the work is tracked lets the guard be *re-derived* every cycle rather than *remembered*.

### Evidence
- OBS-029 — Switchboard #28: in-memory session-cap park re-granted the full cap to already-parked issues on pool restart; fixed by a durable tracker label; the write-failure path re-introduced the same class until the durable write preceded the in-memory record. (supports)

### Where It Applies
Any orchestrator, scheduler, rate-limiter, watchdog, or pipeline with caps/quotas/locks/parks/dedup that must survive process churn — autonomous agent fleets, cron-restarted daemons, anything horizontally restarted or redeployed. The bar rises with the cost of the halted action (money, irreversible effects, duplicate work).

### Known Tensions
Durable writes add latency and a dependency on the system of record; for cheap, easily-reversible, or purely-advisory guards the in-memory version is fine. There is also a write-echo hazard — an automated writer to the monitored channel can trip its own trigger (see PHI-039) — so persistence must be paired with correct re-baselining.

### Open to Revision When
Restarts become impossible or fully state-preserving (durable-execution runtimes that checkpoint memory transparently), or the halted action is cheap enough that a re-granted budget on restart costs nothing.