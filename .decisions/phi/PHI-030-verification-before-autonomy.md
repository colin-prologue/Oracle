<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-030 — Verification before autonomy

**Date:** 2026-06-11
**Domain:** architecture
**Source Project:** AgentChat (agent-team)
**Source:** Guiding-principles interview chose a developer agent as the next role (pure throughput); the immediate counter-finding was that a dev teammate without a QA/review leg makes the owner the full-time reviewer. Written into the agent-team constitution as "the ordering constraint" so it survives enthusiasm.

### Philosophy
No agent executes autonomously on a task type until independent verification — something other than the owner — exists for that task type. Granting execution autonomy without a verification leg doesn't remove the human bottleneck; it relocates it downstream, converting the owner from executor into full-time reviewer. Verification can be another agent, an automated gate, or a test harness — but its existence is the precondition for moving any autonomy ratchet past draft-mode, and the constraint should be written where enthusiasm can't erode it.

### Why I Hold This
Multi-agent failure research (UC Berkeley MAST taxonomy) attributes a large share of failures to verification gaps, and "tester approves without testing" is a recognized failure mode. In agent-team's design session, the pull toward shipping a developer role first was strong precisely because throughput is the visible win — the review burden it creates is invisible until it arrives. Owner-review of agent decision records (AgDRs) shrinks the owner's load to judgment calls but is still owner-verification; it deliberately does not satisfy this constraint.

### Where It Applies
Any system delegating execution to agents or automation: agent teams, CI auto-merge policies, autonomous workflow runners, scheduled jobs that mutate state. Kicks in whenever an autonomy level is about to increase — the question is "what, other than me, checks this?" before "what can it do?"

### Known Tensions
- Verification roles produce no visible output of their own, so they always lose prioritization fights against capability roles unless the constraint is pre-committed in writing.
- For low-stakes, easily-reversible task types, mandatory independent verification can be over-engineering; the constraint is about *autonomous execution*, not about drafts or proposals.

### Open to Revision When
- Evidence that owner-review at a gate (e.g., AgDR verdicts) scales sustainably for some task types, making independent verification unnecessary there.
- A task type proves so reliably reversible that post-hoc audit beats pre-merge verification on total cost.
