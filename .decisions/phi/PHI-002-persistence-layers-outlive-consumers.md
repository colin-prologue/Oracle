<!-- ORACLE ARTIFACT — canonical copy in the oracle bank; this file is a browse mirror in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-002 — Persistence layers must outlive their consumers

**Date:** 2026-04-13
**Revision:** 2026-07-06 — consolidation pass 1: absorbed PHI-009 (write durable store first) and PHI-046 (halt-state guards persist) as named corollaries
**Domain:** infrastructure, architecture
**Source Project:** hindsight (corollaries from hindsight and Switchboard)
**Source:** CDR-005 — daemon lifecycle moved to macOS LaunchAgent

### Philosophy
Never tie the lifecycle of a storage or memory system to the session or process that uses it. A persistence layer that starts and stops with its consumer accumulates stale state, loses work on interruption, and compounds problems across restarts.

### Corollaries
- **Write to the durable store first; the other copy is a derivative (ex-PHI-009, merged 2026-07-06):** when writing the same datum to two stores with asymmetric durability or recovery semantics (memory bank + filesystem mirror, database + log file, cloud upload + local artifact, event publish + audit trail), retain to the more durable store first and treat the other as a derivative. A mid-process interruption can then only orphan the recoverable copy, never the canonical record — the order of writes encodes which store is the source of truth. The default instinct ("do the cheap local write first") inverts the source-of-truth relationship exactly when the next step fails. Boundaries: "durable" is relative to context (a local SQLite file may beat an unreliable network store); a derivative that can't be regenerated cheaply is actually co-canonical and needs transactions/two-phase commit/idempotent retry instead; ordering is moot when a coordinator guarantees atomicity.
- **Halt-state guards persist in the system of record (ex-PHI-046, merged 2026-07-06):** a safety checkpoint whose purpose is to halt work — a session cap, a park, a kill-switch, a dedup marker, a circuit breaker — must persist its state in the durable system of record, not in process memory. In-memory halt-state means a restart re-grants the full budget with no error: nothing throws, no log fires, the counter simply resets, and the guard quietly stops guarding exactly when the process churns. Persist the state where the work is tracked so the guard is re-derived every cycle rather than remembered — and per the write-ordering corollary above, the durable write must precede the in-memory record, or the write-failure path re-introduces the same class. Boundaries: cheap, easily-reversible, or purely-advisory guards can stay in memory; persistence must be paired with correct re-baselining to avoid the write-echo hazard (PHI-039).

### Why I Hold This
The Hindsight plugin's session-scoped daemon model caused stale retain tasks to accumulate whenever a session ended before retain completed. On restart, these tasks compounded with the new session's batch, saturating the Haiku API rate limit and blocking reflect queries. The root cause wasn't the rate limit — it was that a memory system designed to persist across time was being managed as if it were a session artifact. The corollaries are the same asymmetry one level down: durable state is only durable if it is written first (oracle-preclear originally wrote the file before the bank, so an interruption could orphan the file with the bank never knowing) and only guards if it survives restarts (Switchboard's in-memory session cap re-granted parked budgets on every pool restart).

### Evidence
- CDR-005 — daemon lifecycle moved to LaunchAgent after session-scoped stale-task pileup (founding incident)
- OBS-006 / OBS-007 — bank-vs-file divergences from loose store-to-store coupling; oracle-preclear reordered bank-first so interruptions orphan only the regenerable mirror (supports, ex-PHI-009 grounding)
- OBS-029 — Switchboard #28: in-memory session-cap park re-granted the full cap on pool restart; fixed by a durable tracker label, and the class recurred until the durable write preceded the in-memory record (supports, ex-PHI-046 grounding)

### Where It Applies
Any system where writes or state outlast the session that triggers them: memory servers, queues, embedded databases, log collectors — pick the platform's lifecycle manager (LaunchAgent, systemd, Docker). The write-ordering corollary applies wherever one datum lands in two stores with asymmetric durability. The guard corollary applies to any orchestrator, scheduler, rate-limiter, watchdog, or pipeline with caps/quotas/locks/parks/dedup that must survive process churn; the bar rises with the cost of the halted action.

### Known Tensions
Session-scoped startup is simpler to set up; persistent daemons need platform-specific lifecycle tooling — a real but one-time cost against a compounding stale-state problem. Durable writes add latency and a dependency on the system of record. Write ordering matters most when interruptions are realistic and recovery is asymmetric; for cheap idempotent operations it may not matter.

### Open to Revision When
The storage system gains native crash recovery and task durability that make mid-session interruption safe. The two stores are joined by a transaction or coordinator guaranteeing atomicity. Restarts become fully state-preserving (durable-execution runtimes that checkpoint memory transparently), or the halted action becomes cheap enough that a re-granted budget costs nothing. A "derivative" turns out to be non-regenerable — reclassify it as co-canonical before applying the ordering rule.
