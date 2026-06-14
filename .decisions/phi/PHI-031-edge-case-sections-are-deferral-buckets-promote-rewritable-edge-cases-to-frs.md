<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-031 — Edge-case sections are deferral buckets; promote rewritable edge cases to FRs

**Date:** 2026-06-12
**Domain:** process
**Source Project:** Hindsight (pattern observed in Spec 010 review; graduated from OBS-011)
**Source:** First exercise of the OBS→PHI graduation lifecycle (CDR-obs-phi-graduation) — OBS-011 showed the strongest requests signal in the query logs (retrieved in 5 logged queries) and was flagged as a proto-PHI in the 2026-06-12 oracle quality review.

### Philosophy
Treat a spec's Edge Cases section as a deferral bucket under suspicion: any "edge case" that rewrites cleanly as a functional requirement is a deferred FR — promote it before the spec closes.

### Why I Hold This
Spec reviews keep finding core control-flow questions (what happens when no spec exists yet, what happens on stage failure, what happens during simultaneous clarifications) parked as "edge cases." Deferring them hides scope that resurfaces mid-implementation as silent drift.

### Evidence
- OBS-011 — Spec 010 (autonomous-workflow) review: 5 of 8 listed Edge Cases were core control-flow questions, promoted to FR-021..028 in revision (supports). Retrieved in 5 logged oracle queries.

### Where It Applies
Any spec-driven workflow with an Edge Cases (or similar deferral) section — at spec gates and reviews, before implementation begins.

### Known Tensions
Genuinely rare conditions do belong in an edge-case list; blanket promotion bloats FR counts and slows spec closure (PHI-005 activation-energy pressure). The rewrite test — "does it state cleanly as an FR?" — is the filter, not wholesale promotion. Confirmation evidence is currently single-project (Spec 010 reviews); this graduated on requests signal plus explicit ratification.

### Open to Revision When
Promoted edge-FRs routinely turn out to be dead requirements (never exercised in implementation), or the rewrite test starts promoting noise that reviewers strike back out.
