---
name: oracle-triage
description: Review the miner's drafted candidates in the oracle inbox — walk each one through keep/edit/skip, promote approved drafts to real PHI/OBS records via the capture skills, and clean up. Invoked via /oracle-triage after the weekly miner runs.
---

# Triage the Capture Inbox

The weekly miner (`scripts/weekly_mine.sh`) drafts candidates into
`$ORACLE_ROOT/inbox/` (gitignored — private, possibly containing project
context that must not reach the shared repo). Nothing leaves the inbox
without explicit approval here.

Resolve `ORACLE_ROOT` (env var; default `~/team-oracle`).

## Execution

1. **List** `$ORACLE_ROOT/inbox/*.md`, oldest first. If empty, say so and stop.
   If any draft is older than ~3 weeks, flag it: a backlog here means triage
   cadence is failing — better to skip aggressively than accumulate.

2. **For each draft**, present a tight summary — proposed type, one-paragraph
   gist, miner's confidence — and ask one question: **keep / edit / skip?**
   Keep the whole pass to minutes, not a review session.

3. **On keep or edit:**
   - Confirm confidential specifics are stripped (this is the last gate before
     shared visibility — re-check even though the miner was instructed).
   - Route by type: run the `/oracle-debate` flow for PHI candidates (admission
     test still applies), `/oracle-observe` for OBS candidates (≥2 instances
     still applies — a draft that can't meet it stays in the inbox or dies).
   - Delete the draft file once its record PR exists.

4. **On skip:** delete the draft. No graveyard — the transcripts remain the
   archive if something ever needs re-mining.

5. **Close with a count:** kept N, skipped M, inbox empty/remaining.
