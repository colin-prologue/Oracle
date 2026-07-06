<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-038 — Reuse existing independence before adding a dedicated independent step

**Date:** 2026-06-24
**Domain:** architecture
**Source Project:** Switchboard
**Source:** An adversarial leanness review of the Plan 3-C escalation design collapsed a proposed separate "tier-judge" into the existing verifier.

### Philosophy
When a requirement calls for independence or separation — a fresh-context reviewer, a different-model verifier, an isolated judge — first check whether a component already in the pipeline satisfies it, and fold the new concern into that step rather than spawning a second dedicated one. A second independent check of the same artifact at the same point is usually independence-for-its-own-sake: over-design.

### Why I Hold This
The discriminating test is "independent *from the author*, or merely independent *from another reviewer*?" Only the former is what such requirements actually demand. A reviewer that re-inspects an artifact the first reviewer already holds re-derives context for free and adds a dispatch, a protocol, and often a schema change — cost with no marginal independence. Pairs with PHI-030 (independence before autonomy): get the independence you need, but get it once.

### Evidence
- Switchboard Plan 3-C escalation review, 2026-06-24 (no OBS mirror retained): an adversarial leanness review collapsed a proposed separate "tier-judge" subagent into the existing verifier (already model≠author by construction), deleting a whole dispatch + protocol file + decision-schema bump with no loss of required independence (supports).

### Where It Applies
Verification lanes, code/design review gates, multi-agent QA, oversight/escalation layers — any pipeline carrying an independence, fresh-context, or separation-of-duties requirement.

### Known Tensions
When the two concerns genuinely need different contexts or would dilute each other's attention — mitigate by ordering (primary verdict first, secondary concern second) rather than splitting. When the existing component's independence is incidental rather than guaranteed by construction, it can't be relied on and a dedicated step is justified.

### Open to Revision When
Folding repeatedly degrades the primary check — attention dilution shows up as missed defects — making a dedicated second reviewer worth its cost.
