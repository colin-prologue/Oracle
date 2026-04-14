# Quickstart: Oracle Pattern Modeling

**Branch**: `002-oracle-pattern-modeling` | **Date**: 2026-04-13

## Prerequisites

The Hindsight daemon must be running before any oracle operations:

```bash
HINDSIGHT_API_EMBEDDINGS_LOCAL_FORCE_CPU=1 HINDSIGHT_API_RERANKER_LOCAL_FORCE_CPU=1 uvx hindsight-embed daemon start
```

Verify no pending operations before running reflect (CDR-004 mitigation):

```bash
curl -s http://localhost:9077/v1/default/banks/oracle/stats | \
  python3 -c "import json,sys; d=json.load(sys.stdin); print('pending:', d['pending_operations'])"
# Expected: pending: 0
```

---

## User Story 1 — First Synthesized Observation

### Step 1: Synthesize

```
/oracle-synthesize
```

The skill runs a reflect query against CDR-001 through CDR-005 and ADR-001, presents the synthesized pattern text, and waits for your curation before retaining as OBS-001.

**Acceptance check (SC-001)**: The output should cite at least 2 CDR IDs (e.g., CDR-001, CDR-003) and name at least one recurring preference (e.g., "lean toward tooling that minimizes account proliferation").

---

## User Story 2 — Update the Decision Constitution

After OBS-001 is retained, identify at least one gap between the Observation and the current constitution, then update the Mental Model in Hindsight.

### Step 1: Query the current constitution

```
/oracle "What does the current Decision Constitution say about my architectural preferences?"
```

### Step 2: Identify the gap

Compare the Observation (what patterns you actually follow) against the constitution (what it says about your preferences). Look for patterns the Observation surfaced that the constitution doesn't capture.

### Step 3: Update the Mental Model

Run this Python snippet (replace the description with the updated constitution text):

```python
python3 -c "
import json, urllib.request

updated_constitution = '''
[PASTE UPDATED CONSTITUTION TEXT HERE]
'''

payload = {
    'name': 'Decision Constitution',
    'description': updated_constitution.strip()
}

req = urllib.request.Request(
    'http://localhost:9077/v1/default/banks/oracle/mental_models',
    data=json.dumps(payload).encode(),
    headers={'Content-Type': 'application/json'},
    method='POST'
)
with urllib.request.urlopen(req, timeout=30) as resp:
    print(json.loads(resp.read()))
"
```

Also update the file on disk:

```
.claude/.decisions/DECISION_CONSTITUTION.md
```

**Acceptance check (SC-002)**: The updated constitution contains at least one principle that corresponds to a pattern named in OBS-001 and was not in the Phase 1 draft.

---

## User Story 3 — Observation Drift Review Cadence

### Defined Cadence Query

Run these two `/oracle` calls in sequence at the start or end of any session where new CDRs were added:

**Query 1 — Summarize current Observations:**
```
/oracle "Summarize the current synthesized Observations in the oracle bank."
```

**Query 2 — Check for drift:**
```
/oracle "Compare the current Observations against the most recently retained CDRs. Flag any pattern shifts or contradictions."
```

**When to run**: After adding 2+ new CDRs, or at the start of any architecture-heavy session.

**Acceptance check (SC-003)**: Both queries complete within 30 seconds of daemon start with no additional setup.

**Acceptance check (SC-004)**: After adding 3 new CDRs, Query 2 produces output that references specific CDR IDs and either confirms consistency or names a specific tension.

### If Drift Is Detected

1. Run `/oracle-synthesize` to produce a new Observation (OBS-002, etc.)
2. Curate and retain
3. Update the Decision Constitution Mental Model if the drift represents a genuine preference shift

### If No Drift

Proceed with confidence. Document "no drift detected" in the session log if desired.

---

## Edge Case Handling

**Too few CDRs**: If the bank has fewer than 3 CDRs, `/oracle-synthesize` will likely return a "insufficient data" signal. Do not curate or retain a partial synthesis — add more CDRs first.

**Single outlier CDR**: If one CDR seems to contradict the Observation, the cadence query will flag it. Check whether it represents a genuine new pattern or a context-specific exception. Only update the constitution if it's a pattern, not an exception.

**Constitution contradiction**: If an update contradicts an existing principle rather than extending it, note the supersession explicitly in the updated constitution text: "Supersedes prior principle: [...]".
