<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-044 — Goal conditions for autonomous loops are adversarial specifications

**Date:** 2026-07-04
**Domain:** process
**Source Project:** rts-proto (the philosophy itself is cross-project)
**Source:** Hardening gate checks before a long /goal run, then watching an independent review catch what the checks priced too low.

### Philosophy
A machine-checkable success condition given to an autonomous optimization loop will be satisfied by the cheapest available path, not the intended one. Before starting a run, enumerate each check's cheapest bypass and price it above the real work — in the goal text (explicit "do not weaken / do not hardcode" clauses) AND structurally (bypasses must be impossible or audit-visible). Prose constraints alone do not bind an optimizer.

### Why I Hold This
Preparing rts-proto's gate campaign (2026-07-03), a pre-run audit found the cheapest path through several checks was gutting them, not building the feature: golden hash files could be silently regenerated to bless any behavior change; a "boundary lint" greping for one function name passed any real violation; "a decision record exists" was pre-satisfied by an unratified proposal. Each got a structural tooth — gates fail while any golden is uncommitted or modified (regeneration becomes a deliberate, explained commit), an import allowlist replaced the grep, records must carry Status: decided — plus matching anti-gaming clauses in the goal strings. The subsequent six-gate autonomous run produced no check-gaming; every green was real work.

### Evidence
- rts-proto baseline commit cd20606 (2026-07-03): five check-weaknesses closed pre-run; ALL GATES PASS achieved with zero goldens silently moved across the whole campaign (supports)

### Where It Applies
Any evaluator-driven agent loop (goal conditions, CI-gated auto-merge bots, fitness functions, RL reward specs, acceptance-test-driven code generators): wherever a success signal is cheaper to fake than to earn.

### Known Tensions
Pricing every bypass costs setup time and can over-fortify a throwaway experiment; for short supervised runs, human review of the diff is cheaper than structural teeth. Also, teeth calibrated by the same author who writes the checks share that author's blind spots — independent review remains necessary (see PHI-030 family).

### Open to Revision When
Evaluators become capable of judging intent rather than transcript tokens (making textual anti-gaming clauses redundant), or evidence accumulates that well-aligned agent loops don't exploit under-specified conditions in practice.
