<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-007 — Shared spec, not shared implementation, for cross-dialect duplication

**Date:** 2026-04-21
**Domain:** architecture
**Source Project:** claude-root
**Source:** ADR-055 refactor (`memory-server/speckit_memory/index.py`) — three filter-predicate sites across Python closures and LanceDB SQL WHERE. Option B (force one dialect to subsume the other) would have destroyed SQL push-down; Option A (shared FilterSpec dict + two builders) preserved both optimizations and eliminated drift.

### Philosophy
When the same logical predicate lives in two execution dialects, extract the shared *spec* rather than the shared *implementation*. One declarative data structure consumed by N dialect-specific builders eliminates drift by construction while preserving each path's native optimizations.

### Why I Hold This
Rule-of-Three duplicates tempt you toward DRY-at-any-cost. The cheap win — "just filter in Python, skip the SQL" — often costs a push-down optimization that matters at scale. The non-obvious move is to recognize that the duplication isn't really in the *implementation* (closures vs. WHERE clauses are fundamentally different); it's in the *surface* (which fields, which semantics). Sharing the surface as a declarative spec, and letting each dialect build its own matcher from that spec, dedupes the part that actually drifts (new filter field → one edit) without compromising either runtime.

### Where It Applies
- Python predicate + SQL WHERE over the same table
- Client-side validator + server-side validator of the same payload
- ORM filter + raw SQL query against the same model
- Frontend form logic + backend API schema
- CLI flag parser + config-file parser for the same option set
- Mock fixture + production data generator for the same entity

Any time two code paths must agree on a *contract* but execute in different runtimes or dialects, the extract-the-spec pattern applies.

### Known Tensions
- If one of the dialects needs behavior the spec can't express (e.g., a fuzzy-match operator that only the Python side supports), the spec must either grow a capability flag — at which point the spec becomes its own complexity center — or the dialect diverges. Re-examine whether a spec is still earning its keep when this starts happening.
- For two sites only, a shared spec may be over-engineering. The Rule of Three is the threshold for a reason.
- Very small specs (one or two fields) can be noise: callers pass a 2-key dict to get one comparison back. The refactor has to eliminate real drift cost, not just line count.

### Open to Revision When
- A production incident traces to a bug in a spec-derived builder that a hand-written dialect-specific implementation wouldn't have had (the spec abstracted away a dialect-specific quirk).
- The spec accumulates so many capability flags that the builders become spec-interpreters rather than predicates — at that point the spec IS the implementation, just poorly.
- A single unified dialect becomes available (e.g., a query language that compiles to both Python and SQL), making the spec layer redundant.
