<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-029 — Medium before capability

**Date:** 2026-06-11
**Domain:** process
**Source Project:** AgentChat (agent-team)
**Source:** First-principles reassessment of the agent-team project: weeks of capability-building (roles, memory, specs) while agents existed only inside summoned desk sessions; the interview's pivotal finding was "the threads don't exist yet — the team is currently manual code sessions," reframing the chat surface from convenience to constitutive.

### Philosophy
For any system whose value depends on habitual interaction — agent teams, dashboards, knowledge bases, memory systems — the always-reachable, low-ceremony access medium is constitutive, not a convenience feature. Until the system persists in a channel you reach without setup ritual, it isn't in use; it's demoware. Build and prove the medium before scaling the system's capability, because capability built without a medium accumulates unused.

### Why I Hold This
The agent-team project had a working PM with persistent memory, a proven spec-execute-evaluate loop, and a roadmap of further roles — yet actual usage was zero outside deliberate desk sessions, because engaging an agent required opening the right folder with the right boot cue. The 2026-06-10 reassessment chose a thread-first build order (over factory-first and foundations-first) specifically because the felt gap was the medium's nonexistence, not missing capability.

### Where It Applies
Any owner-facing system intended for ongoing use: AI teammates/assistants, status dashboards, personal knowledge bases, decision oracles, monitoring views. Kicks in at prioritization time — when choosing between adding capability and reducing the ceremony of reaching the system, reduce the ceremony first until the habit exists.

### Known Tensions
- Foundations-first instinct: building surfaces before proving core loops risks polishing access to a system that doesn't work yet. (Resolved in agent-team by proving the core loop *first* at small scale, then prioritizing the medium.)
- Related to but distinct from PHI-005 (reduce activation energy by automating extraction): PHI-005 lowers friction inside a workflow step; this governs build *order* — presence infrastructure before capability scaling.

### Open to Revision When
- A system with no low-ceremony medium nonetheless sustains daily use (would show capability pull can outweigh access friction).
- Building the medium first repeatedly produces well-attended channels around systems too immature to be useful, burning trust in the channel itself.
