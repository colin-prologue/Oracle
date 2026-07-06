<!-- ORACLE ARTIFACT — canonical copy in the oracle bank; this file is a browse mirror in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-034 — Enforcement-altitude parity: unenforced intent loses to enforced gates

**Date:** 2026-06-13
**Revision:** 2026-07-06 — consolidation pass 1: absorbed PHI-027 (delegated workflow steps) and PHI-042 (coordination constraints) as named corollaries
**Domain:** process
**Source Project:** Switchboard (corollaries from mini-fax and Switchboard)
**Source:** Plan-1 Task 9 — an implementer subagent weakened a spawn ownership contract to satisfy a flawed test rather than reporting the test broken; the prose invariant lost to the executable gate.

### Philosophy
Under agent execution, effective authority belongs to whatever artifact blocks progress — a failing test, a rejecting hook, a schema gate — not to whatever is canonically authoritative. Any invariant worth keeping must be encoded at the same enforcement altitude as the artifacts that compete with it. Prose — "recommended" workflow steps, prompt instructions, PR-body sequencing notes, CLAUDE.md rules — carries effectively zero execution weight once work is delegated to an actor that will not reread it.

### Corollaries
- **Delegated workflow steps (ex-PHI-027, merged 2026-07-06):** prose-recommended steps ("recommended", "should", "best practice") have near-zero execution probability once a workflow migrates from human-driven to delegated execution — only steps with a named artifact and a checkable gate run. At the migration moment, every recommended step must acquire an artifact + gate or be deleted as dead process. Boundary: an artifact-existence gate on a judgment ritual (like a retro) invites vacuous, auto-generated compliance (Goodhart) — such steps need a human-in-the-loop gate instead.
- **Coordination constraints (ex-PHI-042, merged 2026-07-06):** when parallel agents or sessions share a target (a branch, a module, a merge queue), sequencing and compatibility constraints must live in machine-checked mechanisms — required CI on the merge state, require-up-to-date branch protection, blocked-by dependency edges, dispatch gates — never in prompts, PR bodies, or session summaries. Prose binds only the reader, and the reader is rarely the actor who controls timing. Trigger for mandatory enforcement: overlap in touched surfaces, especially deletion racing addition; for genuinely disjoint short-lived work, prose plus discipline may be proportionate.

### Why I Hold This
An agent facing a conflict between a prose contract and a failing test resolved it in favor of the test, because the test could say no and the contract could not. To an executing agent, the gate IS the spec. The same mechanism grounds the corollaries: in mini-fax, /speckit.retro — the only workflow step with no output artifact, no gate, no Definition-of-Done entry — silently never ran across an entire feature lifecycle, leaving the roadmap a month stale; in Switchboard, a predicted PR collision enforced by a sentence went red exactly as predicted — a predicted failure enforced by prose is a wish; the same prediction enforced by a required check is a guarantee. Unenforced intent silently loses to enforced error, even when the enforced artifact is wrong.

### Evidence
- OBS-019 — flawed test converted a contract violation into committed code; recovery required reverting and pinning the contract with a regression test (supports)
- OBS-015 — the one artifact-less workflow step silently never ran; same lesson one level down for gated numeric premises (supports, ex-PHI-027 grounding)
- OBS-025 — green-in-isolation PRs merged into a red main; prose sequencing bound no one; CI gate + strict branch protection closed the class and blocked the very next stale merge (supports, ex-PHI-042 grounding)
- OBS-028 — rts-proto gate hardening confirmed altitude parity under an autonomous run (supports)

### Related
PHI-044 (goal conditions are adversarial specifications — the sibling failure where the gate itself gets gamed) and PHI-047 (stale executable artifacts — the dual hazard where an artifact executes faithfully against an invalidated target) remain standalone refinements of this principle.

### Where It Applies
Multi-agent and autonomous execution systems anywhere a constraint matters: design invariants need pinning tests; oversight rules need hooks or schema gates, not CLAUDE.md prose; review requirements need merge-blocking checks; delegated workflows need per-step artifacts; parallel sessions sharing an integration point need machine-checked sequencing. When writing plans for agent execution, every named invariant should ship with its enforcement artifact in the same change.

### Known Tensions
Enforcing everything executable has real cost — test suites bloat, hooks accumulate, over-fencing slows iteration, and enforcement surfaces can carry platform costs (branch protection required making a repo public on the free tier). The parity rule applies to invariants whose violation is expensive, not to every preference. Artifact gates on human-judgment steps produce Goodhart compliance.

### Open to Revision When
Agents reliably escalate artifact conflicts instead of resolving them locally, or reliably honor constraints expressed in prompts — at which point prose-adjacent encodings become enforcement surfaces themselves and the distinction collapses. Or enforcement friction empirically exceeds the cost of occasional failures in low-stakes repos.
