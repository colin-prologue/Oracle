## CDR-004 — Haiku 10k TPM limit causes retain/reflect contention

**Date:** 2026-04-13
**Project:** Hindsight / Decision Oracle
**Domain:** tooling, infrastructure
**Session:** Phase 1 validation and oracle testing

### Decision
Accept Haiku rate limit contention as a known limitation; mitigate via
retainEveryNTurns=10 and user awareness. Do not switch models yet.

### Context
After restarting the daemon with a backlogged retain task (52,301 token batch
split into ~10k sub-batches), running a reflect query caused the CLI to spin
indefinitely. Both operations compete for Haiku's 10,000 output tokens per
minute org-level rate limit. Retain hit 429 errors mid-extraction; reflect
entered the retry loop immediately on submission and never completed.

This condition occurs when:
1. Daemon restarts with pending retain tasks in the queue (backlog from
   interrupted session or rate-limit-aborted extraction)
2. A reflect query is issued while background retain is still processing
3. Long sessions generate large retain batches that exhaust the TPM budget

### Options Considered
- **Switch to Sonnet for retain/reflect** — higher rate limits. Rejected at
  this stage: 5x cost increase; normal usage (short sessions, no backlog)
  unlikely to hit contention. Revisit if contention becomes frequent.
- **Accept and mitigate (chosen)** — retainEveryNTurns bumped to 10 (from 5)
  to halve extraction frequency. User should check pending_operations=0 before
  running reflect. Practical workaround is sufficient for solo developer usage.
- **Disable background retain entirely** — defeats the purpose of the oracle.
  Rejected.

### Constraints That Applied
- Haiku org-level limit: 10,000 output tokens per minute
- Long setup sessions produce disproportionately large retain batches
- Solo developer: cost sensitivity favors staying on Haiku

### Confidence
High — condition reproduced; root cause confirmed via daemon logs (429 errors
during batch_retain, concurrent reflect retry loop).

### Revisit Trigger
- If contention occurs in normal (non-setup) sessions with retainEveryNTurns=10
- If Anthropic raises Haiku TPM limits
- If oracle reflect latency becomes unacceptable for Phase 2 /oracle skill usage

### Workaround
Before running reflect or /oracle queries, verify no pending operations:
  curl -s http://localhost:9077/v1/default/banks/oracle/stats | \
    python3 -c "import json,sys; d=json.load(sys.stdin); print(d['pending_operations'])"
Expected output: 0
