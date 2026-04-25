---
name: "oracle-observe"
description: "Capture an impromptu observation — runs a fit-check reflect to find related OBS/PHI entries, then retains the insight as a new OBS-NNN with cross-references."
argument-hint: "The observation to capture (e.g. 'I always reach for X when Y')"
user-invocable: true
---

# Oracle Observe

Capture an impromptu insight or pattern you've noticed — not derived from running a full synthesis cycle. Runs a fit-check reflect to find what's related in the corpus, then retains the observation as a new OBS-NNN with cross-references to related entries.

Use this for **ad hoc capture** of insights noticed mid-session. For periodic synthesis from the full corpus, use `/oracle-synthesize` instead.

Note: the Hindsight API does not support updating document content in place. "Extending" an existing observation means creating a new OBS-NNN that cites the predecessor in `derived_from` — the original entry is preserved.

## Arguments

```
$ARGUMENTS
```

If `$ARGUMENTS` is empty, ask: "What observation do you want to capture?"

## Execution

### Step 1 — Check daemon

Run:
```bash
curl -s http://localhost:9077/v1/default/banks/oracle/stats
```

If the daemon is unreachable, stop and surface the start command from `/oracle` skill. Do not proceed without daemon connectivity.

If `pending_operations > 0`, warn the user but do not block — fit-check reflect is lower stakes than synthesis. Proceed with caution noted.

### Step 2 — Determine next OBS-NNN ID

Run:
```bash
curl -s http://localhost:9077/v1/default/banks/oracle/documents
```

Parse for `id` matching `OBS-\d+`. Find the highest. Next ID = highest + 1, zero-padded to 3 digits. If none exist, start at `OBS-001`.

### Step 3 — Run fit-check via recall

Use the observation text as a recall query to surface related entries.
This used to call `/reflect` (paid-API LLM synthesis); it's now `/recall`
(retrieval-only) — the parent skill assistant interprets the chunks
directly in Step 4, so no subagent dispatch is needed.

**Important:** `$ARGUMENTS` may contain shell-special characters
(apostrophes, backticks, `$`). Do **not** embed it in any bash command
line — the harness substitutes the text into the script body before
bash parses it, so shell escaping does not protect you.

**Step 3a — write the observation to a file via the `Write` tool**
(not via shell). Target path: `/tmp/oracle_observation.txt`. Write only
the `$ARGUMENTS` text as the file contents.

**Step 3b — run the recall, reading the observation from that file:**

```bash
python3 -c "
import json, urllib.request
q = open('/tmp/oracle_observation.txt').read().rstrip('\n')
payload = {'query': q, 'budget': 'mid', 'max_tokens': 4096}
req = urllib.request.Request(
    'http://localhost:9077/v1/default/banks/oracle/memories/recall',
    data=json.dumps(payload).encode(),
    headers={'Content-Type': 'application/json'},
    method='POST'
)
with urllib.request.urlopen(req, timeout=60) as resp:
    d = json.loads(resp.read())
    for r in d.get('results', [])[:10]:
        doc = r.get('document_id') or '-'
        kind = r.get('type', '?')
        text = (r.get('text') or '').replace('\n', ' ')[:300]
        print(f'{doc} ({kind}): {text}')
"
```

### Step 4 — Present fit analysis

Read the recall results from Step 3 and write a short narrative the user
can act on. You (the calling skill assistant) produce this fit-analysis
text directly — no subagent dispatch — citing specific PHI-NNN / OBS-NNN
identifiers from the recall output (use `document_id` when present;
otherwise extract IDs embedded in the body text).

Show the user:

> **Fit analysis for your observation:**
>
> *Your observation*: {$ARGUMENTS}
>
> *Related entries found*:
> {your fit narrative — 2–4 sentences citing specific IDs and naming the
> relationship: reinforces / extends / contradicts / supersedes /
> orthogonal}
>
> **How should this be retained?**
> - **New standalone OBS-{NNN}** — this is new ground not covered by existing entries
> - **Successor to an existing OBS** — this extends or refines an existing observation (cite which one; it will appear in `derived_from`)
> - **Discard** — the corpus already captures this adequately

Wait for the user's decision.

### Step 5 — Curate the observation text

Present the user's original observation and ask if they want to refine it before retention:

> **Observation text to retain:**
>
> {$ARGUMENTS}
>
> Edit if needed, or confirm as-is.

Accept any edits. Do not proceed until confirmed.

### Step 6 — Confirm retention

Assemble `derived_from`:
- Any related OBS/PHI IDs the user confirmed from the fit analysis
- If this is a successor, include the predecessor OBS ID

Show:

> **Confirm retention of {OBS-NNN}:**
>
> **Content**: {curated text}
> **derived_from**: {IDs, or empty if standalone}
> **relationship**: {new / extends OBS-NNN / contradicts PHI-NNN}
>
> Retain to oracle bank?

Wait for explicit confirmation. Never auto-retain.

### Step 7 — Retain to oracle bank

```bash
python3 -c "
import json, urllib.request, datetime

content = '''CURATED_CONTENT_HERE'''
obs_id = 'OBS_ID_HERE'
derived_from = DERIVED_FROM_LIST_HERE
relationship = 'RELATIONSHIP_HERE'

payload = {
    'items': [{
        'content': content,
        'context': 'observation',
        'document_id': obs_id,
        'metadata': {
            'type': 'observation',
            'date': datetime.date.today().isoformat(),
            'derived_from': ', '.join(derived_from) if derived_from else '',
            'relationship': relationship,
            'source': 'manual'
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
    print(json.dumps(json.loads(resp.read()), indent=2))
"
```

Replace placeholders with confirmed values. `derived_from` may be an empty list `[]` for standalone observations.

### Step 8 — Confirm completion

Report:
- `{OBS-NNN}` retained to oracle bank (`source: manual`)
- `derived_from`: {IDs or "none — standalone"}
- `relationship`: {new / extends / contradicts}
- Suggested follow-up: `/oracle "Summarize {OBS-NNN}"` to verify recall
