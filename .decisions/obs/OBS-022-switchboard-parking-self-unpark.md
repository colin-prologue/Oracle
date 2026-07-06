<!-- ORACLE ARTIFACT — canonical copy in the oracle bank; this file is a browse mirror in the Hindsight repo. Observed evidence, not a held philosophy. -->

**Status:** active

## OBS-022 — Switchboard parking self-unpark incident
**Relationship:** supports PHI-039

On 2026-07-02 in Switchboard, the session-cap parking extension released an issue's claim and posted a notification comment, using "issue updatedAt changed" as the unpark-on-human-touch signal — but the comment itself bumped updatedAt, so the next poll unparked the issue, reset the session counter, and resumed dispatching: an unbounded 3-sessions → park → comment → unpark spend loop, the exact failure the cap existed to prevent. The bug survived 110 passing tests because the FakeTracker test double did not model GitHub's comment→updatedAt echo; an independent fresh-context conformance auditor caught it (finding #1, BLOCKER) by reasoning against the real API's behavior rather than the fake's. Fixed by re-fetching the issue after posting the comment and storing the post-comment updatedAt as the park marker; the FakeTracker was updated to mimic the echo as a regression guard. Validated live the same day: issue colin-prologue/Switchboard#8 parked at cap 1/1, received exactly one comment, and stayed parked through subsequent poll ticks.
