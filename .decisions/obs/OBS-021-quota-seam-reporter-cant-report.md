<!-- ORACLE ARTIFACT — canonical copy in the oracle bank; this file is a browse mirror in the Hindsight repo. Observed evidence, not a held philosophy. -->

**Status:** active

## OBS-021 — Switchboard's quota seam: the reporter that's down can't report (HDR-011)
**Relationship:** supports PHI-036, supports PHI-037

On 2026-06-15, designing Switchboard's status digest (M0 Plan 2, HDR-011), the quota seam exposed a circular failure. The obvious design had each worker session write `.switchboard/quota.json` when it caught a rate-limit signal — but under a hard usage cap the throttled session cannot run inference to record the outage, so the reporter is the thing that is down. Because the subscription budget is shared (HDR-009), a cap cascades to the whole fleet simultaneously, so no worker survives to report it.

Verified the same day against Anthropic docs: there is no API for subscription (Pro/Max / Claude Code) 5-hour-rolling-window or weekly usage — the Usage/Cost and Rate-Limits Admin APIs cover org API billing only. So there is no proactive capacity gauge to poll token-free; the only token-free signals are a reactive 429-on-next-dispatch and (optionally) Claude Code OTEL token counters cross-referenced against published caps.

Resolution chosen in HDR-011: rate-limit detection moves to a deterministic PostToolUse hook (token-free, fires even when the session has no tokens left to reason), and quota + liveness are surfaced by an external monitor — a cron'd `sb status --emit` / `sb notify` that reads only local `.switchboard/` files and makes no model or API calls — so it survives the fleet being capped or dead. The same external observer also covers silent session death (spec §11 #3); one out-of-band process solves both. Because the monitor makes no model/API calls, it sidesteps the PHI-001 auth-coupling hazard rather than tripping it.

A second, consumption-side constraint from the same decision: quota state is held strictly advisory and never gates `sb claim`. A shared throttle is simultaneous across the fleet, so a quota-gated claim plus a stale signal would lock every worker out and keep them locked past the throttle's reset — converting a transient condition into a system-wide wedge.
