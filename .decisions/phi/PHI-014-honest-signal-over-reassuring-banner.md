<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-014 — Honest-Signal Over Reassuring Banner at Human Checkpoints

**Date:** 2026-04-26
**Domain:** process / UX
**Source Project:** Claude-Root
**Source:** Spec 010 plan-gate re-review surfaced the dogfooding paradox that an affirmative "✓ all checks passed" banner may degrade rubber-stamping discipline more than no banner at all (LOG-013 captured the dissent + SC-008 kill-switch criterion).

### Philosophy
When surfacing automated-check results to a human gating decision, prefer neutral status phrasing in the no-findings path over affirmative iconography. With-findings paths are improved by inline surfacing of concrete issues; no-findings paths risk converting ambiguity into reassurance, accelerating rubber-stamping past the threshold the gate was designed to enforce.

### Why I Hold This
The signal a checkpoint sends is asymmetric. When a finding is present, the human gains information they couldn't have produced themselves — affirmative framing here is honest. When no finding is present, the human is being asked to read absence-of-evidence as evidence-of-absence. A green banner converts that ambiguity into a green light; an empty findings section forces the human to confront the ambiguity. Pre-checks that surface findings inline are strictly better than no pre-check; pre-checks that announce a clean result may be strictly worse than presenting no banner at all.

### Where It Applies
Any human-in-the-loop checkpoint that gates an irreversible or expensive action: BLOCKING orchestrator gates, CI status badges, code-review approval surfaces, security scan dashboards, deployment promotion screens. The principle scales with the cost of the action being gated and the cognitive overhead of the checkpoint.

### Known Tensions
- Operators sometimes legitimately need a "the system did its job" affirmation to trust the pipeline; total absence of feedback can erode trust in automation.
- Compliance contexts may require explicit attestation that a check ran, not just that it found nothing.
- A/B-testing the no-findings phrasing requires baseline data, which itself requires an initial choice. Both directions can become locked-in.

### Open to Revision When
Empirical measurement (e.g., rubber-stamp rate segmented by with-findings vs no-findings paths) shows the affirmative banner does not degrade attention, OR when an operator population credibly reports that absence of affirmation actively erodes their willingness to trust the pipeline at all.
