<!-- ORACLE ARTIFACT — canonical copy in the oracle bank; this file is a browse mirror in the Hindsight repo. Observed evidence, not a held philosophy. -->

**Status:** active

## OBS-031 — Reconcile a ratified model against running code; route findings patch-vs-ticket by live-break
**Relationship:** supports PHI-016

Switchboard, 2026-07-05. After a design session ratified a new lifecycle/transition model (durable park + fail-review routing + reused `drafting` for remediation), an explicit audit of the whiteboard model against the *running* code on current `main` (post-#28) surfaced four contradictions between the aspirational design and reality:

1. a phantom `in-progress` state nothing writes yet (feature unbuilt) — enforcing it would break the live worker flow;
2. a `status:blocked` label the orchestrator ignores entirely, gating instead on native `blocked_by` dependencies (the label is cosmetic);
3. cap-hit routes to `parked` today vs. the newly-ratified cap→`fail-review`;
4. additive parking labels (issue carries two status labels) vs. the new single-status assumption the board relies on.

Each contradiction was triaged patch-vs-ticket by a single discriminating test: **does the gap break something live today?** Live break → immediate patch; latent / no live consumer → ticket carrying an explicit "reconciliation with current reality" section. All four were latent (no live consumer breaks now), so all four routed to tickets — preventing implementers from building against the whiteboard rather than the running system. This both instantiates PHI-016 (Manual-Use Assumption Check) in a fresh domain (orchestrator/state-machine design rather than feature use) and adds a distilled rule for triaging what the assumption-audit surfaces.