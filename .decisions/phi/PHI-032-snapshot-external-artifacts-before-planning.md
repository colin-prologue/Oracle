<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-032 — Snapshot external artifacts before planning

**Date:** 2026-06-12
**Domain:** process
**Source Project:** Hindsight (pattern observed in feature 012-design-alignment; graduated from OBS-004)
**Source:** OBS→PHI graduation lifecycle (CDR-obs-phi-graduation) — OBS-004 recurred in 4 logged oracle queries across two clients (claude-code, codex-mcp) and already carried its prescription verbatim.

### Philosophy
Spec claims about content living outside the repo are hypotheses until the artifact is pulled in and read; ingestion is the first real scoping pass — make it a pre-plan step, never a during-implementation discovery.

### Why I Hold This
External references (design files, vendor API docs, prototypes, reference implementations) are consistently under-read until snapshotted. The cost of a 15-minute ingestion at spec-close is far less than reconciling scope mid-implementation.

### Evidence
- OBS-004 — 012-design-alignment spec gate: extracting the external design zip revealed five renamed surfaces, an unmentioned decision/options-compare screen, and mechanical components the spec had called "UI/UX only," forcing an explicit scope fork pre-plan instead of silent drift (supports). Retrieved in 4 logged queries by two clients.

### Where It Applies
Any feature whose scope keys off an artifact outside the repo — design exports, vendor API docs, third-party prototypes, open-source references.

### Known Tensions
Heavy artifacts add repo weight, and the snapshot itself can go stale against the living artifact (OBS-003's convention-drift theme applied to data). Licensing may bar committing third-party content — "read in place and record findings in the spec" is the fallback that preserves the principle.

### Open to Revision When
Ingestions repeatedly confirm spec claims without surfacing mismatches (the step is pure overhead), or artifact churn makes snapshots misleading rather than grounding.
