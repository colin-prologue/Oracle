---
name: "oracle-capture"
description: "Capture a confirmed decision as a CDR — drafts the record from session context, confirms with the user, then retains to the oracle bank and writes to .decisions/cdrs/."
argument-hint: "Brief description of the decision (e.g. 'Chose X over Y because Z')"
user-invocable: true
---

# Oracle Capture — CDR

Capture a confirmed decision as a Coding Decision Record (CDR). This is semi-manual by design: you draft the CDR from session context, review it with the user, and only retain it after explicit confirmation.

## Arguments

```
$ARGUMENTS
```

If `$ARGUMENTS` is empty, ask: "What decision should I capture?"

## Execution

### Step 1 — Determine the next CDR number

Run:
```bash
ls /Users/colindwan/Developer/Hindsight/.decisions/cdrs/ | grep -E '^CDR-[0-9]+' | sort | tail -1
```

Extract the number from the last filename (e.g., `CDR-004-...` → `4`). The next CDR number is `N+1`, zero-padded to 3 digits (e.g., `005`).

If the directory is empty or no CDR files exist, start at `001`.

### Step 2 — Draft the CDR

Using the decision described in `$ARGUMENTS` and context from the current session, draft a CDR in this exact schema:

```markdown
## CDR-{NNN} — {title}

**Date:** {YYYY-MM-DD}
**Project:** Hindsight / Decision Oracle
**Domain:** {e.g. agent-orchestration, tooling, unreal-integration, infrastructure}
**Session:** {brief reference to current task or spec, e.g. "Phase 2 oracle hook skills"}

### Decision
{One sentence: what was decided}

### Context
{What problem or constraint prompted this decision}

### Options Considered
- **{Option A}** — {why considered; why rejected or not}
- **{Option B}** — {why considered; why rejected or not}
- **{Chosen option}** — {why selected}

### Constraints That Applied
{Tech constraints, time pressure, team capability, prior commitments that limited choices}

### Confidence
{High / Medium / Low} — {one sentence rationale}

### Revisit Trigger
{What would prompt revisiting this decision, e.g. "If X changes" or "When Y becomes available"}
```

Fill every field using:
- The decision description from `$ARGUMENTS`
- Session context (what was just built or discussed)
- Explicit statements about rejected options if available
- Reasonable inference where context is missing (note inferred fields)

### Step 3 — Present for review

Show the drafted CDR to the user and ask:

> **Review this CDR before I retain it:**
>
> {CDR content}
>
> Confirm to retain, or provide corrections.

Wait for the user's response. If they request edits, revise and present again. Do not retain until the user explicitly confirms.

### Step 4 — Retain to oracle bank

Once confirmed, run:

```bash
python3 -c "
import json, urllib.request, datetime

cdr = '''FULL_CDR_CONTENT_HERE'''

domain = 'CDR_DOMAIN_HERE'
cdr_id = 'CDR_ID_HERE'
confidence = 'CDR_CONFIDENCE_HERE'
today = datetime.date.today().isoformat()

payload = {
    'items': [{
        'content': cdr,
        'context': 'coding-decision-record',
        'document_id': cdr_id,
        'metadata': {
            'type': 'cdr',
            'project': 'hindsight-decision-oracle',
            'domain': domain,
            'date': today,
            'confidence': confidence
        }
    }]
}

req = urllib.request.Request(
    'http://localhost:9077/v1/default/banks/oracle/memories',
    data=json.dumps(payload).encode(),
    headers={'Content-Type': 'application/json'},
    method='POST'
)
with urllib.request.urlopen(req, timeout=30) as resp:
    result = json.loads(resp.read())
    print(json.dumps(result, indent=2))
"
```

Replace:
- `FULL_CDR_CONTENT_HERE` — the full confirmed CDR markdown (escape backslashes and triple-quotes)
- `CDR_DOMAIN_HERE` — the domain field from the CDR (e.g., `tooling`)
- `CDR_ID_HERE` — e.g., `CDR-005`
- `CDR_CONFIDENCE_HERE` — `High`, `Medium`, or `Low`

If the retain call fails with a connection error:
- Note: **Oracle unavailable** — see daemon start instructions in `/oracle` skill
- Still write the CDR file in Step 5 (don't lose the capture)

If the retain call returns a non-200 status, show the error and ask the user whether to proceed with file write only.

### Step 5 — Write the canonical CDR file

Derive the filename slug from the CDR title: lowercase, spaces → hyphens, strip punctuation.

Write the confirmed CDR to:
```
.decisions/cdrs/CDR-{NNN}-{slug}.md
```

### Step 6 — Confirm completion

Report to the user:
- CDR file written to `.decisions/cdrs/CDR-{NNN}-{slug}.md`
- Retained to oracle bank (or note if retain failed)
- Suggested follow-up: "Commit the CDR file with `git add .decisions/cdrs/ && git commit -m 'Add CDR-{NNN}: {title}'`"
