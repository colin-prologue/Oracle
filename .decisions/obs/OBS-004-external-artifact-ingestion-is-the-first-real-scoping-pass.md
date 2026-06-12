<!-- ORACLE ARTIFACT — canonical copy in the oracle bank; this file is a browse mirror in the Hindsight repo. Observed evidence, not a held philosophy. -->

**Status:** active

## OBS-004 — External artifact ingestion is the first real scoping pass

When a feature's scope depends on content that lives outside the repo (design files, vendor API docs, a prototype in a third-party tool, an open-source reference implementation), the spec's claims about what that artifact contains are hypotheses until the artifact is pulled in-repo and read. The ingestion itself reveals surface mismatches, implied behavioral components, and dependencies the spec author did not anticipate.

Observed during feature 012-design-alignment spec gate: the spec described six in-scope surfaces sourced from an external claude.ai design artifact. Extracting the artifact zip into the repo revealed five surfaces with different names (constitution wizard instead of editor, workspace instead of trip-detail + card-grid split), a previously unmentioned decision/options-compare screen, and mechanical components (scoring function, zoom-out trigger, wizard state machine) the spec had explicitly called "UI/UX only." The ingestion triggered a forced scope fork (narrow vs wide vs narrow-plus-tokens) that would otherwise have emerged mid-implementation as silent scope drift.

Practical consequence: make snapshotting and reading the external artifact a pre-plan step, not a during-plan step. The cost of a 15-minute ingestion at spec-close is far less than the cost of reconciling scope during implementation. Related to but distinct from OBS-003: OBS-003 is about internal convention docs outliving their implementation; OBS-004 is about external artifacts being under-read until they are snapshotted.

Cross-project where any work keys off an external reference.
