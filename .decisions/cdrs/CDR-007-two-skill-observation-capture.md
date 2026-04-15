## CDR-007 — Two-skill observation capture: oracle-synthesize and oracle-observe

**Date:** 2026-04-14
**Project:** Hindsight / Decision Oracle
**Domain:** tooling
**Session:** Phase 3 oracle pattern modeling — observation capture workflow design

### Decision
Split observation capture into two separate skills (`/oracle-synthesize` and `/oracle-observe`) rather than a single skill with optional modes or flags.

### Context
The oracle needed a workflow for capturing Observations (OBS-NNN) to the bank. Two distinct use cases emerged: (1) periodic synthesis cycles that run a fixed reflect query against the full CDR corpus to extract patterns, and (2) impromptu insights the developer notices mid-session that need to be integrated against existing entries. The question was whether to handle both in one skill with a `--manual` flag or argument-based mode switch, or as two separate skills.

### Options Considered
- **Single skill with optional argument** — if `$ARGUMENTS` provided, skip reflect and use as observation content directly; otherwise run the synthesis reflect query. Cheaper (one file), but conflates two fundamentally different input directions (corpus → observation vs. observation → corpus).
- **Two separate skills (chosen)** — `oracle-synthesize` for corpus-driven synthesis, `oracle-observe` for manual insight integration with fit-check reflect. Cleaner separation; each skill has a single clear invocation model and a distinct reflect query purpose.
- **Extend oracle-capture** — add `--type observation` mode to the existing CDR capture skill. Cheapest change, but oracle-capture is CDR-specific and mixing capture types would muddy its purpose.

### Constraints That Applied
- The retain shape for OBS-NNN is identical whether content came from reflect or from the developer's head — same `context: "observation"`, same `derived_from`, same ID sequencing. This reduced the structural pressure to split.
- The reflect queries are meaningfully different: oracle-synthesize asks "what patterns exist in the corpus?" (budget: `high`); oracle-observe asks "where does this new insight fit?" (budget: `mid`). Different purposes, different payloads.
- Hindsight `PATCH /documents/{id}` only updates tags, not content — "extending" an existing OBS requires creating a new successor entry, which oracle-observe handles explicitly.

### Confidence
High — the two invocation models are used differently in practice (periodic synthesis vs. ad hoc capture) and the reflect query designs are distinct enough that cramming them into one skill would require branching logic that reads as two skills anyway.

### Revisit Trigger
If a third observation capture pattern emerges (e.g., bulk import from external notes), reconsider whether a unified observation skill with explicit `--mode` flags is cleaner than a growing family of oracle-* skills.
