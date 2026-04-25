<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-008 — Cross-project artifacts live in their owning repo, not the consumer's tree

**Date:** 2026-04-25
**Domain:** architecture / process
**Source Project:** hindsight
**Source:** PHI-006 leaked into the Travel project's `.decisions/phi/` because oracle-preclear wrote canonical files via `$(pwd)`. Auto-compact during execution erased the "this is an oracle artifact" framing, leaving an unexplained file in a project that didn't own it. Fix: resolve the canonical path against the owning repo (`$HINDSIGHT_ROOT`), with a self-identifying banner on the file as a defense-in-depth measure.

### Philosophy
Cross-project artifacts must be canonically stored in their owning repository, never in a consumer project's tree. When an artifact's *meaning* applies beyond a single project (a held opinion, a cross-cutting convention, a shared decision), placing its file in the project that happens to surface it conflates the artifact with that project's local rules — and any auto-compact, copy, or path-resolution accident can amplify the confusion. The owning repo is canonical; consumer projects reference, not host.

### Why I Hold This
The PHI-leakage bug demonstrated this concretely: a PHI captured during work in Travel ended up in Travel's git tree. Because PHIs are explicitly cross-project (the definition of a PHI is "applies beyond this specific project"), placing one inside Travel was a category error. Once the file was committed, anyone reading Travel's tree could mistake it for a local Travel rule. Auto-compact during the failing oracle-preclear run made it worse: the in-context framing ("this is an oracle artifact") was lost, and the orphaned file remained.

### Where It Applies
Any artifact whose semantics outlive the project that surfaced it: shared decision records, cross-cutting conventions, philosophy logs, design tokens used by multiple consumers, schema definitions referenced by multiple services, runbook entries owned by an SRE team but invoked from app repos. The general rule: if the artifact's authority transcends the project, the artifact's home should too.

### Known Tensions
- Co-locating an artifact with the work that surfaced it has real ergonomics: less context-switching, easier provenance, simpler git workflows.
- Discovery: a developer reading the consumer project may not know to look in the owning repo. Mitigations: a self-identifying banner on the file (so even if it leaks it announces itself), a metadata field naming the owning repo, or symlinks at known paths.
- Multi-owner artifacts: when no single repo "owns" the artifact, this principle says nothing — but that's also a sign the artifact isn't yet well-scoped.

### Open to Revision When
- A first-class cross-project artifact registry exists at the platform level (e.g., a workspace-aware tool that resolves "the canonical philosophy bank" without filesystem assumptions). Then per-repo location matters less and indirection can replace centralization.
- The "owning repo" itself becomes a moving target (e.g., gets archived or split). At that point the artifacts need a new home, not a new principle.
