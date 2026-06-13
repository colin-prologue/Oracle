# CDR — OBS→PHI Graduation Lifecycle

**Date:** 2026-06-12
**Status:** Accepted
**Context:** 2026-06-12 oracle quality review found bidirectional blur between
PHIs and OBSs: OBS-003/011/016 carry prescriptions (proto-PHIs); PHIs carry
growing case-study narrative (1.5KB→4KB drift); half of existing OBS are
same-session PHI appendices; no path exists for evidence to become commitment.
A fresh-session adversarial review of the v1 plan corrected the signal design
(see plan revision note).

## Decision

PHI and OBS are not two document types — they are two stages of one lifecycle:

- **OBS = evidence.** Strictly descriptive. Admission test: *"Did this
  actually happen — is it dated, countable, and citable?"* Two admissible
  forms: (1) a dated instance (project + date + what occurred); (2) a
  synthesized pattern citing ≥2 corpus instances by ID (the citations are its
  dated instances). An OBS containing prescriptive language ("should",
  "must", "prefer X") has a PHI candidate inside it — the prescription is
  extracted and routed to /oracle-debate; the evidence stays.
- **PHI = commitment.** Strictly normative, debated before retention, carries
  Known Tensions and Open to Revision When. Case studies live in linked OBS,
  not in the PHI body. Target body ≤ ~2KB.
- **Graduation signals** (guidance for a human-judgment triage in
  /oracle-synthesize — NOT executable thresholds; calibration data does not
  exist yet at current query volume):
  1. **Requests** — the OBS keeps coming back in recall for real queries
     (`retrieved_ids` in .decisions/queries/*.jsonl).
  2. **Usage** — the OBS ID appears in the *answer text* of a logged oracle
     query (it did load-bearing work in a synthesis). This is deliberately
     stricter than `accepted_ids`, which empirically tracks retrieval
     wholesale.
  3. **Confirmation** — a second dated instance from a different
     `source_project`, or explicit user ratification.
- **Promotion:** /oracle-synthesize proposes candidates during its triage
  step; /oracle-debate is the only minting path. Never automatic.
- **Terminal state:** lifecycle status lives in the disk mirror
  (`.decisions/obs/OBS-NNN-*.md`, `**Status:**` line: `active` /
  `graduated → PHI-NNN` / `declined YYYY-MM-DD`). The bank is append-only,
  so the mirror is canonical for status; the bank stays canonical for
  content. Triage skips non-active OBS.
- **Tension path:** an OBS retained with `relationship: tension-with PHI-NNN`
  counts against that PHI; /oracle-synthesize surfaces accumulated tension
  evidence against the PHI's "Open to Revision When" clause.
- **Mirror symmetry:** OBS get a disk mirror at `.decisions/obs/` as
  browsable derivatives (same rationale as `.decisions/phi/` in
  DECISION_ORACLE.md), with the same bank-first write ordering (OBS-006
  lesson).
- **Metadata:** all three OBS retain paths (preclear, observe, synthesize)
  set `source_project`. Confirmation is forward-only for legacy OBS — 15 of
  16 lack `source_project` and the bank cannot update documents in place.

## Rejected alternatives

- **Collapse to one record type with maturity field** — rejected for now
  because the commitment structure (debate, tensions, revision clauses) is
  what makes PHIs safe to advise from; kept as the pre-committed fallback
  (see kill criterion in the plan).
- **Executable graduation thresholds (usage ≥2, requests ≥3 counters)** —
  rejected after adversarial review: at ~26 usable log entries the counters
  are calibrated against nothing, `accepted_ids` ≈ `retrieved_ids` wholesale
  ~two-thirds of the time, logs contain duplicate questions and malformed
  IDs, and verification probes contaminate counts. Eyeball triage over
  `scripts/review_oracle_queries.py` output captures the value at this n.
- **Evidence-link tooling / link database** — rejected at n=16 OBS as
  premature elaboration; `relationship` metadata + derived_from is enough.

## Known tensions

- PHI-029: this scales capability on a system whose gap is usage/medium.
  Mitigated by prompt-only changes riding existing rituals; kill criterion
  covers the miss.
- PHI-005: prescription-splitting adds approval ceremony to preclear.
  Accepted; monitored via kill criterion (c).
- Synthesize-minted OBS are cross-entry distillations, not incident reports —
  admissible under form (2). Note: once prescriptions are split out of new
  OBS, descriptive residue may rarely clear the relevance gate, so
  *requests* may be the livest signal for a while. Acceptable: graduation
  also flows from confirmation, and the triage is judgment, not counting.

## Kill criterion

See plan header. Pre-committed: prescriptive leakage in new OBS, ignored
candidates, or dropped capture rate ⇒ collapse the two types and amend this
CDR.
