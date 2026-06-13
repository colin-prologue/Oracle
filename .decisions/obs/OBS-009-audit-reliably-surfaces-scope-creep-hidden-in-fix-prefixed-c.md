<!-- ORACLE ARTIFACT — canonical copy in the oracle bank; this file is a browse mirror in the Hindsight repo. Observed evidence, not a held philosophy. -->

**Status:** active

## OBS-009 — Audit reliably surfaces scope creep hidden in fix-prefixed commits

When a commit prefixed `fix:` ships new functionality alongside the bug fix, an audit run reliably surfaces the scope creep — typically as a missing task entry, a missing decision-record row, or an unmarked regression-checklist row. Two distinct authoring intents live in one diff and the audit sees both even when the commit message names only one.

Useful as a pre-commit signal: if you're tempted to expand scope mid-fix, either rename the commit prefix (`feat:` / `feat+fix:`) or split the work into separate commits — otherwise the audit forces the bookkeeping after the fact.

**Observed in:** TravelPlanner feature 012-design-alignment, commit 858a188 (`fix(012): manual test fixes`) added tag editing UI to CardEditor, which the post-commit audit flagged as MEDIUM finding F-2 (missing tasks.md entry, missing design-decisions row).
