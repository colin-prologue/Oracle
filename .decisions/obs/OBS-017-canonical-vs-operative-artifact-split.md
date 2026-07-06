<!-- ORACLE ARTIFACT — canonical copy in the oracle bank; this file is a browse mirror in the Hindsight repo. Observed evidence, not a held philosophy. -->

**Status:** active

## OBS-017 — Canonical vs. operative artifact split
**Relationship:** supports PHI-010 (dogfood-separation corollary, ex-PHI-022 — merged 2026-07-06)

When a runtime loads from a deploy location distinct from the version-controlled source (canonical vs. operative copies), edits flow to the canonical copy — where review and history live — while the operative copy silently lags, so the review pipeline validates files the runtime never reads. Staleness emits no signal: the loader runs the stale copy without error. Dated instance: 2026-06-12, Oracle project — 4 of 5 oracle skill prompts loaded from ~/.claude/skills/ lagged the repo's PR-#20-reviewed .claude/skills/ sources; resolved by symlinking the load path to the source.
