<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-035 — Escalation calibrated to decision substance, not action category

**Date:** 2026-06-13
**Domain:** process
**Source Project:** Switchboard
**Source:** Plan-1 retro — agent prompted for approval of a fast-forward, local, reversible, fully-verified merge with nothing contestable in it; Colin flagged both failure modes and the rule was codified as Switchboard HDR-010.

### Philosophy
Interrupting a human for approval must be justified by decision substance, never by action category or workflow ceremony. Over-asking is a failure mode symmetric with over-proceeding: empty prompts train rubber-stamping, which degrades the signal value of the gates that matter.

### Why I Hold This
A workflow skill hard-gated a merge that had no contestable content (fast-forward, local, reversible, 84 tests + two-stage reviews already passed). The audit showed only publish and destroy genuinely needed the human. Interrupt-worthiness turned out to be computable from fields every decision record already carries — confidence × blast radius × reversibility — so the binary ask/proceed choice was a false dichotomy.

### Evidence
- Switchboard HDR-010 (2026-06-13) — merge-approval retro; substance-tiered rule codified with feedback amendment requiring independent tier judgment (supports; project decision record)

### Where It Applies
Any agent-human collaboration with autonomy: orchestrators, worker skills, CI auto-merge policies, approval workflows. Three tiers: (1) interrupt-blocking — hard-escalation domains (security, prod, secrets, frozen contracts), evidence ties research cannot break, low confidence with cross-cutting blast radius, changes to the oversight contract itself, publish/destroy; (2) flag-async — contestable but reversible: record the decision, notify, proceed; interruption without idling; (3) record-silent — high confidence, local blast, reversible; batched at the gate profile.

### Known Tensions
Tier placement initially depends on agent self-assessed confidence — the component most likely to be miscalibrated. Mitigation is structural: self-assessment is bootstrap mode only; once the system can host it, tier judgment moves to an independent fresh-context agent (PHI-030 extended to the escalation judgment itself). Gate verdict history tunes thresholds: overturned silent records raise the bar, waved-through interrupts lower it.

### Open to Revision When
Evidence that humans prefer ceremony prompts as engagement touchpoints despite the rubber-stamping cost; or verdict-history calibration proves too slow/noisy to converge, making fixed action-category rules cheaper than tier computation.
