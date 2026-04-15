---
name: "oracle-debate"
description: "Capture a Philosophy (PHI) — drafts a held opinion from session context, debates it with the user, then retains to the oracle bank and writes to .decisions/phi/."
argument-hint: "Brief description of the philosophy (e.g. 'Prefer X over Y when Z')"
user-invocable: true
---

# Oracle Debate — PHI

Capture a cross-project Philosophy (PHI-NNN). Philosophies are strong opinions about how to approach decisions — prescriptive but open to debate, not hard rules. This is semi-manual by design: draft from session context, debate with the user, retain only after explicit confirmation.

## Arguments

```
$ARGUMENTS
```

If `$ARGUMENTS` is empty, ask: "What philosophy do you want to capture?"

## Execution

### Step 1 — Determine the next PHI number

Run:
```bash
ls /Users/colindwan/Developer/Hindsight/.decisions/phi/ | grep -E '^PHI-[0-9]+' | sort | tail -1
```

Extract the number from the last filename (e.g., `PHI-002-...` → `2`). Next PHI number is `N+1`, zero-padded to 3 digits (e.g., `003`).

If the directory is empty or no PHI files exist, start at `001`.

### Step 2 — Draft the Philosophy

Using `$ARGUMENTS` and session context, draft a PHI in this schema:

```markdown
## PHI-{NNN} — {title}

**Date:** {YYYY-MM-DD}
**Domain:** {e.g. architecture, tooling, process, infrastructure}
**Source:** {what experience or pattern prompted this philosophy}

### Philosophy
{One or two sentences: the held opinion, phrased as a disposition not a rule}

### Why I Hold This
{The experience or repeated pattern that grounded this position}

### Where It Applies
{Cross-project context — when does this philosophy apply}

### Known Tensions
{What situations create legitimate pressure against this philosophy}

### Open to Revision When
{What would change your mind}
```

Fill every field. The philosophy statement should be generalizable — not tied to a specific project's implementation details.

### Step 3 — Present for debate

Show the drafted PHI and ask:

> **Review this Philosophy before I retain it:**
>
> {PHI content}
>
> Push back, refine, or confirm.

Wait for the user's response. This is the debate step — the user may challenge the framing, scope, or wording. Revise and present again if needed. Do not retain until explicitly confirmed.

### Step 4 — Retain to oracle bank

Once confirmed, run:

```bash
python3 -c "
import json, urllib.request, datetime

phi = '''FULL_PHI_CONTENT_HERE'''

domain = 'PHI_DOMAIN_HERE'
phi_id = 'PHI_ID_HERE'
today = datetime.date.today().isoformat()

payload = {
    'items': [{
        'content': phi,
        'context': 'philosophy',
        'document_id': phi_id,
        'metadata': {
            'type': 'philosophy',
            'domain': domain,
            'date': today
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
- `FULL_PHI_CONTENT_HERE` — full confirmed PHI markdown (escape backslashes and triple-quotes)
- `PHI_DOMAIN_HERE` — domain field from the PHI (e.g., `architecture`)
- `PHI_ID_HERE` — e.g., `PHI-004`

If the retain call fails with a connection error:
- Note: **Oracle unavailable** — see daemon start instructions in `/oracle` skill
- Still write the PHI file in Step 5 (don't lose the capture)

### Step 5 — Write the canonical PHI file

Derive the filename slug from the title: lowercase, spaces → hyphens, strip punctuation.

Write to:
```
.decisions/phi/PHI-{NNN}-{slug}.md
```

### Step 6 — Confirm completion

Report:
- PHI file written to `.decisions/phi/PHI-{NNN}-{slug}.md`
- Retained to oracle bank (or note if retain failed)
- Suggested follow-up: `git add .decisions/phi/ && git commit -m 'Add PHI-{NNN}: {title}'`
