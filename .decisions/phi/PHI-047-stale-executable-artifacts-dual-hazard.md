<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-047 — Stale executable artifacts are the dual hazard of delegation-by-artifact

**Date:** 2026-07-05
**Revision:** 2026-07-06 — cross-references repointed: PHI-027 merged into PHI-034 (consolidation pass 1)
**Domain:** process
**Source Project:** mini-fax
**Source:** 002 group-board pivot — a pre-staged implementation goal-prompt survived the pivot pointing at the old model; its invalidation warning had to move from a branch-local resume doc to the roadmap issue.

### Philosophy
A pre-staged, autonomously-executable artifact (goal-prompt, kickoff ticket, runbook) is only as safe as it is fresh. The very property that makes artifacts reliable for delegation — a delegate runs them faithfully without rereading upstream context — is what makes a *stale* one dangerous: it executes at high fidelity against an invalidated target. So a model/spec pivot must invalidate or re-point **every downstream executable artifact**, not just the specs; and any "this is stale" warning must live at the altitude where the executor looks (the launch ticket), never only in a branch-local doc.

### Why I Hold This
PHI-034's delegated-workflow corollary (ex-PHI-027) established that named artifacts + gates are what actually get executed under delegation; prose has near-zero execution probability. This is the dual: after a locked model pivot, a pre-staged `/goal` implementation prompt still described the OLD model and would have built the wrong thing — faithfully. The invalidation was first captured only in a branch-local resume doc; the gap surfaced only when Colin asked whether the next step was in a git issue. The fix put a stop-warning at the top of the roadmap ticket (the PR-1 issue) — the altitude an implementer actually reads.

### Evidence
- PHI-034 (delegated-workflow corollary, ex-PHI-027) — artifacts (not prose) govern delegated execution; this PHI is its dual for *stale* artifacts (supports).
- PHI-034 — enforcement-altitude parity; the invalidation warning must sit at the executor's altitude (supports).
- Grounding instance: mini-fax 002, 2026-07-05 — stale implementation goal-prompt survived the group-board pivot; warning relocated from the branch resume doc to GitHub issue #9. (OBS candidate surfaced this session but declined; incident retained here + in the session log.)

### Where It Applies
Any delegated/automated setup with pre-staged launch artifacts — agent orchestration (Switchboard goal strings on issue bodies, rts-proto), spec-kit goal-prompts, CI/migration runbooks, saved automation prompts.

### Known Tensions
Auditing every artifact on every edit is ceremony — the trigger is a *pivot* (model/contract change), not routine edits. And a "check freshness" reminder is itself prose (near-zero execution per PHI-034's delegated-workflow corollary) unless mechanized: a lint diffing the launch artifact against the current spec, or a freshness stamp the launcher gates on.

### Open to Revision When
Launchers reliably reread upstream context before firing (instruction-following improves enough that stale artifacts get caught at run time), or a mechanical freshness check (artifact ↔ spec drift lint / staleness stamp) makes the manual pivot-audit redundant.
