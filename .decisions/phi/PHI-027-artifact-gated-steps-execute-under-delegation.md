<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-027 — Artifact-Gated Steps Are the Only Steps That Execute Under Delegation

**Date:** 2026-06-11
**Domain:** process
**Source Project:** mini-fax
**Source:** Root-causing why /speckit.retro never ran for a completed feature; design session for ADR-043 (Agent Decision Records).

### Philosophy
Prose-recommended workflow steps ("recommended", "should", "best practice") have effectively zero execution probability once a workflow migrates from human-driven to delegated execution — only steps with a named artifact and a checkable gate run. When delegating a workflow, every recommended step must either acquire an artifact + gate or be deleted as dead process.

### Why I Hold This
In mini-fax, /speckit.retro was the only workflow step with no output artifact, no gate, and no Definition-of-Done entry — and it silently never ran across an entire feature lifecycle, leaving roadmap.md a month stale with real contradictions. Every step that DID run (audit, crossref check, builds, test-plan evidence) ran because a goal-prompt success criterion named a verifiable artifact for it. The one "recommended" step that made it into the success criteria executed; the one that didn't, didn't. Inclusion was luck, not system.

### Where It Applies
Any workflow being handed to an agent or automation: spec-kit lifecycles, CI/CD process docs, runbooks, review cadences, retro/postmortem rituals. The migration moment — human-driven to delegated — is when every "(recommended)" annotation must be re-litigated into an artifact + gate or removed.

### Known Tensions
Gating everything invites ceremony and vacuous compliance — an artifact requirement on a judgment ritual (like a retro) can produce auto-generated reflection that LOOKS done (Goodhart). Steps whose value is human judgment need a human-in-the-loop gate, not just an artifact-existence gate.

### Open to Revision When
If agents reliably execute prose intent without artifact anchors (instruction-following improves enough that "recommended" carries execution weight), or if a lighter mechanism (e.g., workflow linting that diffs delegation prompts against the canonical step list) catches omissions without per-step gates.
