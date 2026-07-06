<!-- ORACLE ARTIFACT — canonical copy in the oracle bank; this file is a browse mirror in the Hindsight repo. Observed evidence, not a held philosophy. -->

**Status:** active

## OBS-023 — Test doubles inherit their author's blind spots
**Relationship:** supports PHI-030; paired with OBS-026 (same author-blind-spot finding, game-simulation domain — graduation candidate pair)

Test doubles inherit their author's blind spots. On 2026-07-02 in Switchboard, the FakeTracker written by the same process that wrote the scheduler omitted GitHub's comment→updatedAt side effect — the same misconception that produced the parking self-unpark bug (OBS-022) — so the integration suite certified the misconception rather than the behavior: 110 tests green around a BLOCKER-severity defect. The gap was closed only by a verifier with independent knowledge of the real system (a fresh-context conformance auditor citing live GitHub API semantics), after which the fake was corrected to encode the newly-learned behavior as a regression guard. Evidence that "tests pass" is weak assurance precisely where the implementation and its test fixtures share one model of the external world; independent verification must bring its own model of the external dependency, not reuse the implementer's.
