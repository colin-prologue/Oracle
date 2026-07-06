<!-- ORACLE ARTIFACT — canonical copy in the oracle bank; this file is a browse mirror in the Hindsight repo. Observed evidence, not a held philosophy. -->

**Status:** active

## OBS-029 — Silent restart-defeat of an in-memory session cap (Switchboard #28)
**Relationship:** supports PHI-002 (halt-state-guard corollary, ex-PHI-046 — merged 2026-07-06)

Switchboard, 2026-07-05. The autonomous worker fleet's session-cap parking kept both the per-issue session counter and the "parked" set in process memory (scheduler in-memory dicts). A pool restart re-zeroed both, so a previously parked-at-cap issue was silently re-dispatched with a fresh full budget — no error, no log line, the cap just reset. The failure was invisible precisely because nothing broke; the guard simply stopped guarding at the moment of churn.

Concrete stakes: two dispatchable tickets (#10, #20) were already parked-at-cap when the "can we restart the pool?" question arose, so restarting would have re-run exactly the work the cap had halted.

Fix: move the park marker into the tracker as a durable `status:parked` label (the system of record for issues), so the park decision is re-derived from the tracker on every poll and survives restart; the in-memory set was demoted to counter-reset bookkeeping. AgDR-008 superseded AgDR-002's explicitly-accepted "in-memory park" weakness.

Tail: a Codex review then caught that the label-*write-failure* path re-introduced the same class — the issue was recorded parked in-memory before the durable write, so on write failure the next poll unparked and re-dispatched (an unbounded same-process loop). Hardened by writing the durable marker before trusting the in-memory record, and halting dispatch entirely when the marker cannot be written (unprovisioned label).