<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

**Status:** merged → PHI-034 2026-07-06

## PHI-042 — Coordination constraints live in enforcement surfaces, not communication surfaces

**Date:** 2026-07-03
**Domain:** process
**Source Project:** Switchboard (the philosophy itself is cross-project)
**Source:** Parallel-session PR collision — a sequencing constraint written into a spawned task's prompt and a session summary bound no one; the merge went red exactly as predicted.

### Philosophy
When parallel agents or sessions share a target (a branch, a module, a merge queue), encode sequencing and compatibility constraints as machine-checked mechanisms — required CI on the merge state, require-up-to-date branch protection, blocked-by dependency edges, dispatch gates — not as prose in prompts, PR bodies, or summaries. Prose binds only the reader, and the reader is rarely the actor who controls timing.

### Why I Hold This
I predicted the exact failure ("merge #23 before the follow-up sessions open theirs") and enforced it with a sentence; the sentence was read by an agent that could not wait and skimmed past by the human who controlled timing. A predicted failure enforced by prose is a wish; the same prediction enforced by a required check is a guarantee. This generalizes the earlier Gate-B lesson (governance gates require automated enforcement) from human gates to agent-coordination constraints.

### Evidence
- OBS-025 — green-in-isolation PRs #23/#24 merged into a red main; prose sequencing bound no one; CI gate + strict branch protection closed the class and blocked the very next stale merge (supports)
- OBS-023 — test-doubles blind spot: shared mental models between artifacts don't verify each other; independent enforcement is required (supports)

### Where It Applies
Any multi-agent or multi-session workflow with a shared integration point: parallel PR streams, spawned background tasks touching overlapping modules, orchestrator worker fleets, cron/routine agents sharing state. The moment work is delegated to an actor that won't reread the conversation, constraints must move into the machinery it cannot bypass.

### Known Tensions
Enforcement surfaces cost setup and add friction (sequential merges, update-branch churn, plan-tier walls — branch protection required making the repo public on the free tier). For genuinely disjoint short-lived work, prose plus discipline may be proportionate; the trigger for mandatory enforcement is overlap in touched surfaces, especially deletion racing addition.

### Open to Revision When
If agent harnesses gain reliable constraint-honoring (e.g., spawned tasks that genuinely block on a dependency expressed in the prompt), prose-adjacent encodings become enforcement surfaces themselves and the distinction collapses. Or if enforcement friction empirically exceeds the cost of occasional red mains in low-stakes repos.
