<!-- ORACLE ARTIFACT — canonical copy in the oracle bank; this file is a browse mirror in the Hindsight repo. Observed evidence, not a held philosophy. -->

**Status:** active

## OBS-024 — Verification contract unsatisfiable under the executor's permission envelope; 120 green tests never saw it
**Relationship:** supports PHI-034

On 2026-07-02 (Switchboard), the worker fleet's core verification contract — "every acceptance criterion is checkable by a command the agent runs" — was unsatisfiable in production: the permission allowlist admitted only `git`/`gh`, so every pytest invocation died on non-interactive denial. Issue #10 burned 11 of 20 turns retrying denied test-command variants; #11 hit the same wall across three sessions. Notably, 120 unit tests were green throughout — every test tier stopped at a component boundary (fake CLI, fake tracker), and none included the executor's real capability envelope, so the intent-level contract had no test anywhere. The contract lived in methodology prose; the allowlist was the executable gate, and the gate won (PHI-034). Diagnosis came from transcript mechanics alone (denial strings, retry loops). Fix: pin the verifying commands into the allowlist and state them in the worker prompt; validated same night when #11's next worker ran pytest and shipped PR #17 in two sessions. Compound-failure note: #10 was simultaneously wall-blocked and under-scoped — clearing the wall alone still left a doomed retry (grounds PHI-040).
