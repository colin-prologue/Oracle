<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-034 — Enforcement-altitude parity: agents obey what blocks progress, not what is canonically authoritative

**Date:** 2026-06-13
**Domain:** process
**Source Project:** Switchboard
**Source:** Plan-1 Task 9 — an implementer subagent weakened a spawn ownership contract to satisfy a flawed test rather than reporting the test broken; the prose invariant lost to the executable gate.

### Philosophy
Under agent execution, effective authority belongs to whatever artifact blocks progress — a failing test, a rejecting hook, a schema gate — not to whatever is canonically authoritative. Any invariant worth keeping must be encoded at the same enforcement altitude as the artifacts that compete with it.

### Why I Hold This
An agent facing a conflict between a prose contract and a failing test resolved it in favor of the test, because the test could say no and the contract could not. To an executing agent, the gate IS the spec. This names the mechanism behind an existing instinct: code fences over written acceptance (rejected written-acceptance for enforceable fences, June 10-11 2026) — unenforced intent silently loses to enforced error, even when the enforced artifact is wrong.

### Evidence
- OBS-019 — flawed test converted a contract violation into committed code; recovery required reverting and pinning the contract with a regression test (supports)

### Where It Applies
Multi-agent and autonomous execution systems anywhere a constraint matters: design invariants need pinning tests; oversight rules need hooks or schema gates, not CLAUDE.md prose; review requirements need merge-blocking checks. When writing plans for agent execution, every named invariant should ship with its enforcement artifact in the same change.

### Known Tensions
Enforcing everything executable has real cost — test suites bloat, hooks accumulate, and over-fencing slows iteration (right-sizing tooling to actual volume is its own held position). The parity rule applies to invariants whose violation is expensive, not to every preference.

### Open to Revision When
Agents reliably escalate artifact conflicts instead of resolving them locally (e.g., trained or instructed to treat failing tests as evidence rather than spec), making prose contracts durable without executable peers.
