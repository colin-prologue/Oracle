<!-- ORACLE ARTIFACT — canonical copy in the oracle bank; this file is a browse mirror in the Hindsight repo. Observed evidence, not a held philosophy. -->

**Status:** active

## OBS-030 — A bare failure→ready transition is a bug; encode the diagnostic as a required state
**Relationship:** supports PHI-040

Switchboard, 2026-07-05. While designing the autonomous fleet's failure-recovery transition graph, a direct `failure → todo` (ready) edge was identified as a latent defect: returning capped or failed work to the dispatchable state without attaching its diagnosis just re-runs the same failure (thrash repeats thrash; scope overflow re-overflows).

Ratified model (applying PHI-040's classify-by-what-it-discredits): every cap-hit routes through a **mandatory `fail-review` diagnostic state** — a fresh independent verifier, the post-failure twin of pre-dispatch triage. It classifies the failure per the taxonomy and routes by class: `blockage`/`quota` (approach sound, wall artificial) → `todo` **carrying a distilled re-entry brief** so the next worker resumes from furthest-state, not scratch; `iteration` (thrash, model suspect) → `drafting` for a facts-only re-dispatch; `complexity` (scope overflow) → split into re-triaged children. Remediated tickets re-enter through `drafting`+`triage` (revise + re-verify), not a straight bounce.

Key move: making the diagnostic a *required state* rather than leaving recovery as an unguarded label flip renders the naive `failure→ready` bounce structurally unrepresentable — the same "make the wrong path impossible rather than rely on discipline" instinct Colin favors for data-shaped extension points. Recursive validation: the fail-review feature (#20) itself cap-hit as honest scope overflow, and its own taxonomy classified it as SPLIT — the auto-diagnoser could not yet diagnose itself, arguing for its priority.