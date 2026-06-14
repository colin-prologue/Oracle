# OBS→PHI Graduation Lifecycle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Revision note (2026-06-12):** v2, revised after fresh-session adversarial review.
> Material changes from v1: graduation thresholds demoted from executable machinery to
> CDR guidance (review finding: counters calibrated against nothing at n=26 usable log
> entries, and `accepted_ids` ≈ wholesale retrieval — not a load-bearing-ness signal);
> usage signal redefined as "OBS ID cited in the logged answer text"; lifecycle terminal
> state added via mirror Status lines; `source_project` added to all three OBS retain
> paths; day-one candidates (OBS-011, OBS-004) handled explicitly; DECISION_ORACLE.md
> update added (v1 would have created the exact doc drift OBS-003 warns about);
> dead Task 7 (`unidentified_count` plumbing) dropped.

**Goal:** Sharpen the PHI/OBS distinction into a graduation lifecycle — OBS are dated evidence, PHIs are debated commitments, and evidence graduates to commitment based on three signals: **requests** (retrieval recurrence), **usage** (cited in a logged oracle answer), and **confirmation** (cross-project recurrence + explicit user ratification at debate).

**Architecture:** Prompt-only changes to the oracle skills plus one decision record, one backfill script, and one new mirror directory. No new tooling beyond the `relationship` metadata field `oracle-observe` already uses. Promotion is never automatic — `/oracle-synthesize` *proposes* graduation candidates by eyeballing `scripts/review_oracle_queries.py` output and mirror Status lines; `/oracle-debate` remains the only path that mints a PHI. Lifecycle status lives in the disk mirror (the bank is append-only; the mirror is canonical for *status*, the bank for *content* — this carve-out is recorded in the CDR).

**Tech Stack:** Markdown skill prompts, Hindsight MCP tools, Python 3 (one backfill script), daemon HTTP API at `localhost:9077`.

**Motivating findings (from 2026-06-12 oracle quality review, corrected by fresh-session re-verification):**
- OBS-003/011/016 contain prescriptions ("should...", reviewer smells, design commitments) — proto-PHIs in OBS clothing.
- PHIs drifted 1.5KB→4KB as case-study narrative accumulated inside normative claims.
- Half of existing OBS (8 of 16) are same-session PHI appendices via `derived_from`; 5 are standalone; 2 are CDR-era. The evidence layer is real but entangled with capture-time PHIs.
- No promotion path exists: `/oracle-synthesize` only mints more OBS; evidence never graduates.
- PHIs are mirrored to disk; OBS exist only in postgres. (Justification for the mirror is DECISION_ORACLE.md's browsable-derivative-files decision, *not* PHI-009 — PHI-009 governs write ordering once two stores exist; it does not mandate a second store.)
- **Day-one graduation candidates already exist:** scanning the real query logs shows OBS-011 (cited/accepted in 5 queries) and OBS-004 (3–4) — both flagged as proto-PHIs in the quality review. The lifecycle's first act is triaging them, not waiting for signal to accumulate.

**Known tensions (named per the oracle's own discipline):**
- **PHI-029 (medium before capability):** the oracle's felt gap is organic usage — most logged queries are self-referential (about the oracle/Hindsight itself). This plan scales lifecycle capability anyway. Mitigation: everything here is prompt-only and piggybacks on rituals that already run (preclear); nothing new must be habitually visited. If usage doesn't materialize, the kill criterion fires.
- **PHI-005 (activation energy / review fatigue):** the prescription split can double approval items per preclear candidate. Accepted cost; if preclear sessions start getting skipped, that is kill-criterion evidence.

**Explicit non-goals (lean check):**
- No retroactive rewrite of existing PHI-001..030 or OBS-001..016 content.
- No bank topology changes (session-log separation is a separate decision).
- No automated promotion — every graduation passes through `/oracle-debate` with the user.
- No new MCP tools, daemon changes, or log-schema changes.
- No threshold-counting machinery. Thresholds live in the CDR as *guidance* for a human-judgment step. Revisit if query volume grows ~5x and gate discipline improves (i.e., `accepted_ids` stops equaling `retrieved_ids` wholesale).

**Kill criterion (pre-committed):** Re-evaluate after +10 new OBS or 3 months, whichever first. Collapse PHI/OBS into one record type with a maturity field (and amend the CDR) if any of:
(a) ≥3 of the next 5 OBS contain prescriptive language despite the admission test;
(b) graduation candidates exist (per the synthesize triage) but zero `/oracle-debate` promotions have happened — the lifecycle is being ignored;
(c) preclear capture rate visibly drops because the split-and-classify ceremony is too heavy.

---

### Task 1: Record the decision (CDR)

**Files:**
- Create: `.claude/.decisions/CDR-obs-phi-graduation.md`

- [ ] **Step 1: Write the CDR**

```markdown
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
```

- [ ] **Step 2: Verify file placement**

Run: `ls /Users/colindwan/Developer/Hindsight/.claude/.decisions/CDR-obs-phi-graduation.md`
Expected: file exists.

- [ ] **Step 3: Commit**

```bash
git add .claude/.decisions/CDR-obs-phi-graduation.md
git commit -m "docs(decisions): record OBS->PHI graduation lifecycle CDR"
```

---

### Task 2: OBS admission test in oracle-preclear

**Files:**
- Modify: `.claude/skills/oracle-preclear/SKILL.md` (Step 3 classification block; Step 4 OBS retain block)

- [ ] **Step 1: Replace the classification block**

Find (verbatim, `oracle-preclear/SKILL.md:70-73`):

```markdown
For each candidate, classify as:
- **PHI** — a prescriptive held opinion ("prefer X over Y when Z")
- **OBS** — a descriptive pattern or observation
```

Replace with:

```markdown
For each candidate, classify as:
- **PHI** — a prescriptive held opinion ("prefer X over Y when Z")
- **OBS** — a descriptive pattern or observation

**OBS admission test** (apply before presenting an OBS candidate):
*"Did this actually happen — is it dated, countable, and citable?"* An OBS
must cite at least one dated instance (project + date + what occurred). If
the candidate cannot, it is not an OBS — drop it or reframe it.

**Prescription check:** if an OBS candidate contains prescriptive language
("should", "must", "prefer", "always/never do X"), it has a PHI candidate
inside it. Split it: present the evidence as the OBS, and present the
prescription as a separate PHI candidate (or note it as a future
/oracle-debate if the user declines the PHI now). Do not retain prescriptions
inside OBS bodies.

**Relationship tagging:** every OBS candidate that relates to an existing
PHI must name the relationship: `supports PHI-NNN`, `tension-with PHI-NNN`,
or `standalone`. Tension evidence is as valuable as support — do not
suppress it.
```

- [ ] **Step 2: Add relationship + source_project metadata to the OBS retain call**

Find (verbatim, in Step 4's OBS candidates block):

```markdown
- `metadata`:
  ```json
  {
    "type": "observation",
    "date": "<YYYY-MM-DD today>",
    "source": "oracle-preclear"
  }
  ```
```

Replace with:

```markdown
- `metadata`:
  ```json
  {
    "type": "observation",
    "date": "<YYYY-MM-DD today>",
    "source": "oracle-preclear",
    "source_project": "<from step 1>",
    "relationship": "<supports PHI-NNN | tension-with PHI-NNN | standalone>"
  }
  ```
```

- [ ] **Step 3: Add OBS mirror write to Step 4**

Find (verbatim): `Increment the OBS counter before the next OBS candidate.`

Replace with (indented block uses 4-space code style to avoid fence nesting):

```markdown
**Then write the derivative OBS file** to
`${HINDSIGHT_ROOT:-$HOME/Developer/Hindsight}/.decisions/obs/OBS-{NNN}-{slug}.md`
— same bank-first ordering and failure states as PHI files
(`bank-retained/file-write-failed`, `file-written`). First line banner
(mirrors the PHI banner wording):

    <!-- ORACLE ARTIFACT — canonical copy in the oracle bank; this file is a browse mirror in the Hindsight repo. Observed evidence, not a held philosophy. -->

Then a status line, then the retained content:

    **Status:** active

    ## OBS-{NNN} — {title}
    **Relationship:** {supports PHI-NNN | tension-with PHI-NNN | standalone}

    {retained OBS body verbatim}

The `**Status:**` line is the lifecycle terminal-state record (`active` /
`graduated → PHI-NNN` / `declined YYYY-MM-DD`). The bank cannot update
documents in place, so the mirror is canonical for status only; the bank
stays canonical for content.

Increment the OBS counter before the next OBS candidate.
```

- [ ] **Step 4: Verify edits are internally consistent**

Run: `grep -c "relationship" /Users/colindwan/Developer/Hindsight/.claude/skills/oracle-preclear/SKILL.md`
Expected: ≥3 occurrences.

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/oracle-preclear/SKILL.md
git commit -m "feat(oracle-preclear): OBS admission test, prescription split, relationship metadata, disk mirror"
```

---

### Task 3: Same admission test in oracle-observe (+ source_project)

**Files:**
- Modify: `.claude/skills/oracle-observe/SKILL.md` (Step 5 curation, Step 7 retain metadata + mirror)

- [ ] **Step 1: Add admission + prescription check to Step 5 (curation)**

Find (verbatim, `oracle-observe/SKILL.md:79-81`):

```markdown
### Step 5 — Curate the observation text

Present the user's original observation and ask if they want to refine it before retention:
```

Replace with:

```markdown
### Step 5 — Curate the observation text

Apply the **OBS admission test** first: *"Did this actually happen — is it
dated, countable, and citable?"* If the observation cites no dated instance,
ask the user for one before proceeding (project + date + what occurred).

Apply the **prescription check**: if the text contains prescriptive language
("should", "must", "prefer", "always/never"), tell the user the prescription
belongs in a PHI and offer to route it to `/oracle-debate` after retaining
the descriptive remainder as the OBS. Do not retain prescriptions inside OBS
bodies.

Present the user's original observation and ask if they want to refine it before retention:
```

- [ ] **Step 2: Add source_project to Step 7 retain metadata**

Find (verbatim, in Step 7's metadata block):

```markdown
  {
    "type": "observation",
    "date": "<YYYY-MM-DD today>",
    "relationship": "<new | extends OBS-NNN | contradicts PHI-NNN>",
    "source": "manual"
  }
```

Replace with:

```markdown
  {
    "type": "observation",
    "date": "<YYYY-MM-DD today>",
    "relationship": "<new | extends OBS-NNN | contradicts PHI-NNN>",
    "source": "manual",
    "source_project": "<git remote slug or basename of cwd>"
  }
```

- [ ] **Step 3: Add OBS mirror write after Step 7 retain success**

Find (verbatim, `oracle-observe/SKILL.md:132`):

```markdown
When retain succeeds, record capture audit state `retained`.
```

Replace with:

```markdown
When retain succeeds, record capture audit state `retained`, then write the
derivative file to
`${HINDSIGHT_ROOT:-$HOME/Developer/Hindsight}/.decisions/obs/OBS-{NNN}-{slug}.md`
with the standard OBS banner and `**Status:** active` line (see
oracle-preclear Step 4 for the exact format) and record `file-written`
(or `bank-retained/file-write-failed` on failure).
```

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/oracle-observe/SKILL.md
git commit -m "feat(oracle-observe): OBS admission test, prescription routing, source_project, disk mirror"
```

---

### Task 4: PHI slimming + evidence links in oracle-debate and oracle-preclear

**Files:**
- Modify: `.claude/skills/oracle-preclear/SKILL.md:134` (PHI file template)
- Modify: `.claude/skills/oracle-debate/SKILL.md:72` (PHI template — anchor differs: NO trailing period)

- [ ] **Step 1a: Update the PHI template in oracle-preclear**

Find (verbatim — note trailing period inside braces, line 134):

```markdown
### Why I Hold This
{The experience or repeated pattern that grounded this position.}
```

Replace with:

```markdown
### Why I Hold This
{The experience or repeated pattern that grounded this position — 2-4
sentences. Detailed case studies do NOT go here: capture them as OBS records
and cite them in Evidence below.}

### Evidence
{Bulleted OBS-NNN citations, one line each: `- OBS-NNN — {one-line summary}
(supports)`. If no OBS exists yet for the grounding incident, create one in
the same session and cite it. Tension evidence is listed here too, marked
`(tension)`.}
```

- [ ] **Step 1b: Update the PHI template in oracle-debate**

Find (verbatim — note NO trailing period, line 72):

```markdown
{The experience or repeated pattern that grounded this position}
```

Replace with:

```markdown
{The experience or repeated pattern that grounded this position — 2-4
sentences. Detailed case studies do NOT go here: capture them as OBS records
and cite them in Evidence below.}

### Evidence
{Bulleted OBS-NNN citations, one line each: `- OBS-NNN — {one-line summary}
(supports)`. If no OBS exists yet for the grounding incident, create one in
the same session and cite it. Tension evidence is listed here too, marked
`(tension)`.}
```

(Verify surrounding context in oracle-debate before applying — the template
section heading there may differ from preclear's; the replacement must land
inside the PHI template, immediately after its "Why I Hold This" heading.)

- [ ] **Step 2: Add a length guard to both skills' PHI sections**

Immediately before the PHI template block in each file, insert:

```markdown
Target PHI body ≤ ~2KB. A PHI is a normative claim with its commitment
structure (tensions, revision triggers) — not an incident report. If the
draft exceeds ~2KB, move narrative into an OBS and cite it under Evidence.
```

- [ ] **Step 3: Verify both files updated**

Run: `grep -l "### Evidence" /Users/colindwan/Developer/Hindsight/.claude/skills/oracle-preclear/SKILL.md /Users/colindwan/Developer/Hindsight/.claude/skills/oracle-debate/SKILL.md`
Expected: both paths printed.

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/oracle-preclear/SKILL.md .claude/skills/oracle-debate/SKILL.md
git commit -m "feat(oracle): slim PHI template, add Evidence section linking OBS"
```

---

### Task 5: Graduation triage in oracle-synthesize (judgment step, no counters)

**Files:**
- Modify: `.claude/skills/oracle-synthesize/SKILL.md` (insert Step 2b between Step 2 and Step 3; Step 4 curation note; Step 7 metadata)

- [ ] **Step 1: Insert the graduation triage step**

After the Step 2 section (`### Step 2 — Determine next OBS-NNN ID`) and before `### Step 3`, insert:

```markdown
### Step 2b — Graduation triage (OBS→PHI candidates)

Before synthesizing new observations, check whether existing evidence has
earned commitment status. This is a judgment step, not a counting step.

1. Run `python3 scripts/review_oracle_queries.py` (or read
   `.decisions/queries/*.jsonl` directly) and note which OBS IDs recur in
   `retrieved_ids` (requests signal) and which appear *in the answer text*
   of logged queries (usage signal — stricter than `accepted_ids`, which
   tracks retrieval wholesale).
2. Read the `**Status:**` lines in `.decisions/obs/*.md`. Skip any OBS not
   `active` (already `graduated` or `declined`).
3. For each active OBS showing requests or usage signal, check
   **confirmation**: a second dated instance from a different
   `source_project` (metadata or body), or prior user interest.

For each candidate, present:

> **Graduation candidate: OBS-NNN** — requests: {seen in N queries},
> usage: {cited in N answers}, confirmation: {yes — projects A, B / not yet}
> Distilled prescription: "{the normative claim hiding in this evidence}"
> Promote with: `/oracle-debate "{distilled prescription}"`

Promotion is the user's call — never mint a PHI here. Record the outcome in
the OBS mirror's `**Status:**` line: `graduated → PHI-NNN` after a
successful debate, or `declined YYYY-MM-DD` if the user passes (declined OBS
are not re-proposed; the user can flip the line back to `active` to
reconsider). If no candidates, say "No graduation candidates" and continue.
```

- [ ] **Step 2: Admit synthesized OBS form in Step 4 curation**

In Step 4 (`Present for curation`), after the line `Edit as needed. The curated version will be retained as {OBS-NNN}.`, add:

```markdown
Admission check for synthesized OBS: the body must cite ≥2 corpus instances
by ID (its dated instances are those citations — admissible form 2 in
CDR-obs-phi-graduation). It must remain descriptive: if the synthesis
produced prescriptive language, that prescription is a graduation candidate
for Step 2b / /oracle-debate, not OBS content.
```

- [ ] **Step 3: Add source_project to Step 7 retain metadata**

Find (verbatim, in Step 7's metadata block):

```markdown
  {
    "type": "observation",
    "date": "<YYYY-MM-DD today>",
    "query": "<the synthesis query>"
  }
```

Replace with:

```markdown
  {
    "type": "observation",
    "date": "<YYYY-MM-DD today>",
    "query": "<the synthesis query>",
    "source": "oracle-synthesize",
    "source_project": "<git remote slug or basename of cwd>"
  }
```

- [ ] **Step 4: Surface tension evidence in the synthesis brief**

In the Step 3c synthesis brief template, after the line `- names tensions, counter-evidence, or limits in the corpus before`/`...one direction;`, add:

```
- if any retained OBS carries `relationship: tension-with PHI-NNN`, check
  that PHI's "Open to Revision When" clause and state whether the
  accumulated tension evidence meets it;
```

- [ ] **Step 5: Day-one triage (one-time, part of rollout)**

Run `/oracle-synthesize` once after Tasks 1–6 land. Expected: Step 2b
proposes **OBS-011** (edge-cases-as-deferral-bucket — cited in ~5 logged
queries, prescription already identified: "every edge case that rewrites
cleanly as an FR is a deferred FR — promote it") and likely **OBS-004**.
Decide promote/decline for each; record Status lines accordingly. This is
the lifecycle's first real exercise and validates the whole loop.

- [ ] **Step 6: Commit**

```bash
git add .claude/skills/oracle-synthesize/SKILL.md
git commit -m "feat(oracle-synthesize): graduation triage step proposing OBS->PHI promotions"
```

---

### Task 6: OBS disk mirror backfill + architecture doc update

**Files:**
- Create: `scripts/backfill_obs_mirror.py`
- Create: `.decisions/obs/` (16 mirrored files)
- Modify: `.claude/.decisions/DECISION_ORACLE.md` (Layer 2 section — currently says "no canonical file is written to disk"; leaving it would create exactly the aspirational-convention drift OBS-003 documents)

- [ ] **Step 1: Write the backfill script**

```python
#!/usr/bin/env python3
"""One-off: mirror existing OBS bank documents to .decisions/obs/.

Bank is source of truth for content; the mirror is a browse derivative and
carries the lifecycle Status line (bank is append-only). Safe to re-run:
skips existing files.
"""
import json
import pathlib
import re
import urllib.request

DAEMON = "http://localhost:9077"
ROOT = pathlib.Path(__file__).resolve().parent.parent
OBS_DIR = ROOT / ".decisions" / "obs"
BANNER = ("<!-- ORACLE ARTIFACT — canonical copy in the oracle bank; this "
          "file is a browse mirror in the Hindsight repo. Observed evidence, "
          "not a held philosophy. -->\n\n**Status:** active\n\n")


def get(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)


def slug_from(text, doc_id):
    first = next((l for l in text.splitlines() if l.strip()), doc_id)
    first = re.sub(r"^#+\s*", "", first)
    first = re.sub(rf"^{doc_id}\s*[—-]\s*", "", first).strip()
    s = re.sub(r"[^a-z0-9]+", "-", first.lower()).strip("-")
    return s[:60] or "untitled"


def main():
    OBS_DIR.mkdir(parents=True, exist_ok=True)
    docs = get(f"{DAEMON}/v1/default/banks/oracle/documents")
    items = docs if isinstance(docs, list) else docs.get("items") or docs.get("result") or []
    total = docs.get("total") if isinstance(docs, dict) else len(items)
    if total and total > len(items):
        raise SystemExit(f"pagination needed: total={total} > page={len(items)}; "
                         "add a paging loop before re-running")
    obs_ids = sorted(d["id"] for d in items if str(d.get("id", "")).startswith("OBS-"))
    for doc_id in obs_ids:
        d = get(f"{DAEMON}/v1/default/banks/oracle/documents/{doc_id}")
        text = d.get("original_text") or d.get("text") or ""
        if not text:
            print(f"SKIP {doc_id}: no text in daemon response")
            continue
        path = OBS_DIR / f"{doc_id}-{slug_from(text, doc_id)}.md"
        if path.exists():
            print(f"EXISTS {path.name}")
            continue
        path.write_text(BANNER + text.rstrip() + "\n")
        print(f"WROTE {path.name}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it**

Run: `python3 scripts/backfill_obs_mirror.py`
Expected: 16 `WROTE OBS-...md` lines (OBS-001..016).

- [ ] **Step 3: Verify mirror contents**

Run: `ls /Users/colindwan/Developer/Hindsight/.decisions/obs/ | wc -l` and spot-read one file.
Expected: count matches bank OBS count; banner on line 1; `**Status:** active` present.

- [ ] **Step 4: Update DECISION_ORACLE.md Layer 2**

Find (verbatim, in the `### Layer 2 — Observation (OBS-NNN)` section):

```markdown
OBSs are retained to the oracle bank only; no canonical file is written to disk. The bank is
the source of truth.
```

Replace with:

```markdown
OBSs are retained to the oracle bank first (canonical for content), then
mirrored to `${HINDSIGHT_ROOT}/.decisions/obs/OBS-{NNN}-{slug}.md` as a
browse derivative — same contract as PHI files. The mirror additionally
carries the lifecycle `**Status:**` line (`active` / `graduated → PHI-NNN` /
`declined YYYY-MM-DD`), for which the mirror is canonical because the bank
is append-only. See CDR-obs-phi-graduation.md.
```

Also add `obs/` alongside `phi/` in the doc's File Structure listing if present.

- [ ] **Step 5: Commit**

```bash
git add scripts/backfill_obs_mirror.py .decisions/obs/ .claude/.decisions/DECISION_ORACLE.md
git commit -m "feat(decisions): mirror OBS records to .decisions/obs/ with backfill script and doc update"
```

---

### Task 7: End-to-end verification

**Files:** none (verification only)

- [ ] **Step 1: Dry-run the preclear classification on a synthetic candidate**

Manually walk oracle-preclear Step 3 with the text: "Audits reliably catch
scope creep in fix-prefixed commits, so you should always split scope into
separate commits." Expected behavior per the new prompt: split into OBS
(the audit observation, dated instance required) + PHI candidate
(the commit-splitting prescription).

- [ ] **Step 2: Verify anchors all applied**

Run: `grep -l "OBS admission test" .claude/skills/oracle-preclear/SKILL.md .claude/skills/oracle-observe/SKILL.md && grep -l "### Evidence" .claude/skills/oracle-preclear/SKILL.md .claude/skills/oracle-debate/SKILL.md && grep -l "Graduation triage" .claude/skills/oracle-synthesize/SKILL.md`
Expected: all five paths printed.

- [ ] **Step 3: Probe retention symmetry**

Run: `ls .decisions/phi | head -3 && ls .decisions/obs | head -3`
Expected: both mirrors populated.

- [ ] **Step 4: First triage run (= Task 5 Step 5)**

Run `/oracle-synthesize`; confirm Step 2b proposes OBS-011/OBS-004 and that
the decisions land in mirror Status lines. **Caution:** any `/oracle` probe
queries run during verification append real log lines — note them as probes
in the session, since the triage signal reads these logs.

- [ ] **Step 5: Final commit if any stragglers**

```bash
git status --short
git add -A && git commit -m "chore(oracle): graduation lifecycle verification artifacts"
```
