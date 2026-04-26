<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-012 — Preserve Manual Ritual Discipline When Automating Sequential Workflows

**Date:** 2026-04-25
**Domain:** process
**Source Project:** Claude-Root
**Source:** During spec 010-autonomous-workflow Q2 clarification on subagent execution context, user explicitly chose subagent-per-stage on the grounds that they already manually `/clear` between phases to prevent cross-phase decision pollution. Their manual ritual was the deciding evidence for the orchestrator architecture.

### Philosophy
When automating a sequential workflow, preserve the discipline of any manual ritual the human already performs between steps. If the human invented a reset between phases, that's evidence the cross-step pollution they're guarding against is a real cost — automate the ritual, do not bypass it.

### Why I Hold This
The human's manual reset between phases is itself a designed control: it prevents prior-phase reasoning from biasing the next phase's choices. An automation that re-introduces cross-phase carryover regresses a discipline the human deliberately built. Independent decision frames in sequential pipelines are a feature, not friction.

### Where It Applies
Any time you are automating a workflow a human currently runs by hand: spec→plan→implement pipelines, code review (read code → form opinion → then check tests, not the reverse), incident response runbooks, interview loops, deployment promotion stages, any workflow with explicit phase boundaries. Anywhere humans naturally pause and reset between steps.

### Known Tensions
The ritual may be incidental rather than principled — humans sometimes invent practices for reasons they cannot articulate, and not every habit is load-bearing. Preserving the ritual costs tokens, latency, or complexity; in cost-sensitive automation that may not be acceptable. If the ritual exists only because the manual tools were inadequate (e.g., the human had no way to scope context), automating with better tools may make the ritual obsolete.

### Open to Revision When
The human articulates that their manual ritual was a workaround for a tool limitation now eliminated, OR repeated automated runs with carryover demonstrably produce equally good or better outcomes than runs with reset, OR the cost of preserving the reset (tokens, latency, complexity) clearly exceeds the value of independent decision frames in a specific domain.
