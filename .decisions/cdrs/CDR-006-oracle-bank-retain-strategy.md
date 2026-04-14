## CDR-006 — Oracle Bank Retain Strategy: Explicit Capture Only

**Date:** 2026-04-14
**Project:** Hindsight / Decision Oracle
**Domain:** tooling
**Session:** Phase 3 oracle pattern modeling — daemon startup and bank quality investigation

### Decision
Disable autoRetain; retain oracle bank content only on SessionEnd, PreCompact, and explicit /oracle-capture invocations.

### Context
During Phase 3 setup, the oracle bank pending_operations count grew continuously during active conversation because autoRetain fires every N turns, queuing every message exchange as a memory. This flooded the bank with conversation noise (516 nodes, 76 auto-observations from chat content rather than decisions), degraded reflect quality, and saturated the Haiku 10k TPM limit — blocking reflect queries that require pending_operations: 0. With multiple concurrent Claude sessions, the problem compounds: each session multiplies the retain queue.

### Options Considered
- **autoRetain: true, retainEveryNTurns=10** (prior default) — retains conversation content continuously; provides crash resilience but floods the bank with noise and saturates Haiku TPM during active sessions. Rejected.
- **autoRetain: true, retainEveryNTurns=50+** — reduces frequency but does not fix the fundamental signal/noise problem; still contends with reflect during active synthesis. Rejected.
- **autoRetain: false, retain on SessionEnd + PreCompact + explicit capture** (chosen) — bank accumulates only structured session summaries and deliberate CDR captures; reflect quality improves; TPM contention eliminated during active sessions.

### Constraints That Applied
- Haiku 10k TPM org-level rate limit creates direct contention between retain and reflect operations
- Multiple concurrent Claude sessions multiply queue load
- Decision oracle prioritizes reflect quality over completeness — a missed chat exchange is acceptable, a missed CDR is not
- PreCompact hook required to preserve content before /compact clears conversation context

### Confidence
High — root cause (autoRetain noise → TPM contention → reflect blocked) was directly observed; fix is minimal and reversible.

### Revisit Trigger
If session summaries prove insufficient for oracle recall quality, or if Haiku TPM limit increases significantly, reconsider selective autoRetain with project-scoped filtering.
