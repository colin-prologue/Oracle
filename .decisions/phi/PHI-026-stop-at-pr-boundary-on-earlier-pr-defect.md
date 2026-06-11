<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-026 — Stop at the PR Boundary When Verification Surfaces an Earlier-PR Defect

**Date:** 2026-06-07
**Domain:** process
**Source Project:** mini-fax
**Source:** mini-fax PR #6 T055 verification surfaced that PR 1's `firmware/platformio.ini` had no flash-encryption build flags wired — a build-system gap from an earlier PR's scope. The PR 4 goal-prompt explicitly listed "Discovery of a bug in PR 1/2/3 surfaced by T053/T054/T055 verification — STOP and report — don't silently fix it in PR 4" as a hard-escalation trigger. The escalation produced LOG-024 (FR-022 flash-encryption deferred v1) with user-authorized Option A path, instead of an inline patch that would have expanded PR 4 scope.

### Philosophy
When late-stage verification (acceptance test, audit, codereview gate, or invariant check) surfaces a defect whose origin lies in an earlier PR's scope, stop and report at the boundary — do not silently fix in the current PR. The current PR should escalate to the user with three structured options: (a) inline-fix and expand current PR scope explicitly, (b) accept-as-deferred-risk via a decision record (ADR/LOG) and proceed, (c) kick to a separate cleanup PR. Default to (b) when the deferral has clear closure conditions and the inline fix would meaningfully expand current PR scope.

### Why I Hold This
Silent fixes by the agent hide three things that future readers need: (1) the defect's origin (no record that an earlier PR shipped incomplete), (2) the scope-creep that defeats the current PR's reviewability (auditors expecting "PR 4 wires US3" find "PR 4 also retroactively closes FR-022 efuse burn"), and (3) the user's decision authority over whether to accept the deferral. The PR boundary is also the natural place to surface vendor-policy / earlier-decision-record drift that would otherwise compound silently. The hard-escalation rule trades a small cost (one user prompt + one decision record) for a large gain (provenance of the defect + audit clarity + user authority preserved). Validated when mini-fax T055 found a multi-day fix that did NOT belong in PR 4 — the stop-and-report path produced LOG-024 with explicit closure conditions, whereas a silent inline fix would have stretched PR 4 by days and obscured the earlier-PR origin.

### Where It Applies
Any multi-PR feature where late-stage gates verify invariants that earlier PRs were supposed to establish. Common shapes: build-system gates (encryption, signing, partition layout), security gates (auth coverage, secret hygiene), contract gates (HMAC test vectors, schema versions), and integration gates. Applies equally in goal-mode (autonomous) and human-driven implementation. Also applies to spec-kit `/speckit.codereview` and `/speckit.audit` results — both surface earlier-decision drift that should escalate, not silently rebase.

### Known Tensions
Trivial fixes (single-character typos, obvious off-by-ones with no architectural implication) can legitimately ride the current PR without escalation — the rule's force depends on the defect's scope. Distinguishing "trivial" from "earlier-PR scope" is judgment; when in doubt, escalate. Also tension with goal-mode looping limits: the escalation costs user turns the goal cannot self-budget, so a goal-prompt's success criterion must allow partial-completion deferrals or the goal becomes structurally unsatisfiable when an earlier-PR defect surfaces. Resolved by making the success criterion authorize user-driven exceptions (Option A path).

### Open to Revision When
- A user explicitly authorizes "silently roll up earlier-PR defects into the current PR without asking" — at which point the default flips and the agent stops escalating.
- A multi-PR feature ships under tight deadline pressure where stop-and-ask cost exceeds the silent-fix-now cost — at which point the rule may be situationally suspended with explicit acknowledgement.
- Project context shifts to a culture where PR boundaries are loose and review is post-hoc — at which point the boundary's value as escalation surface diminishes.
