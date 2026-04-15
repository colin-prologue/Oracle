---
name: "oracle-synthesize"
description: "Synthesize a new Observation from retained CDRs/ADRs via a reflect query — presents output for curation, then retains the confirmed result as OBS-NNN."
argument-hint: "Optional: override the default synthesis query"
user-invocable: true
---

# Oracle Synthesize

Run a reflect query against the oracle bank to extract cross-CDR patterns, curate the output, and retain it as a new Observation (OBS-NNN).

Use this for **periodic synthesis cycles** — generating a new observation from what's already in the corpus. For impromptu insights you want to integrate, use `/oracle-observe` instead.

## Arguments

```
$ARGUMENTS
```

If `$ARGUMENTS` is provided, use it as the reflect query. Otherwise use the default:

> *"What patterns define how I make architecture decisions? Cite specific CDR IDs (e.g., CDR-001) in your response to ground the synthesis."*

## Execution

### Step 1 — Check daemon and pending operations

Run:
```bash
curl -s http://localhost:9077/v1/default/banks/oracle/stats
```

If `pending_operations > 0`, stop and tell the user:
> **Daemon has pending operations — reflect may be incomplete. Wait for `pending_operations: 0` before synthesizing (CDR-004).**

### Step 2 — Determine next OBS-NNN ID

Run:
```bash
curl -s http://localhost:9077/v1/default/banks/oracle/documents
```

Parse the response for any `id` matching `OBS-\d+`. Find the highest number. Next ID is that number + 1, zero-padded to 3 digits. If none exist, start at `OBS-001`.

### Step 3 — Run reflect query

POST to reflect:
```bash
python3 -c "
import json, urllib.request

query = 'QUERY_HERE'

payload = {'query': query, 'budget': 'high'}
req = urllib.request.Request(
    'http://localhost:9077/v1/default/banks/oracle/reflect',
    data=json.dumps(payload).encode(),
    headers={'Content-Type': 'application/json'},
    method='POST'
)
with urllib.request.urlopen(req, timeout=120) as resp:
    result = json.loads(resp.read())
    print(result.get('response', result))
"
```

Replace `QUERY_HERE` with the query from Step 1.

If the reflect returns empty or times out:
> **Reflect returned no output — bank may have insufficient CDRs or daemon is under load. Do not retain.**

### Step 4 — Present for curation

Show the raw reflect output and ask:

> **Review this synthesized Observation before retention:**
>
> {reflect output}
>
> Edit as needed. The curated version will be retained as {OBS-NNN}.

Wait for the user's response. Accept edits. Do not proceed until the user confirms the curated text.

### Step 5 — Extract citations

Parse the curated text for CDR/ADR/OBS identifiers using pattern `(CDR|ADR|OBS)-\d{3}`. These populate `metadata.derived_from`.

If fewer than 2 CDR/ADR identifiers are found, warn:
> **Fewer than 2 CDR/ADR citations found — `derived_from` will be sparse. Proceed anyway?**

Require explicit confirmation before continuing.

### Step 6 — Confirm retention

Show the user:

> **Confirm retention of {OBS-NNN}:**
>
> **Content**: {curated text}
> **derived_from**: {extracted IDs}
> **document_id**: {OBS-NNN}
>
> Retain to oracle bank?

Wait for explicit confirmation. Do not retain without it.

### Step 7 — Retain to oracle bank

```bash
python3 -c "
import json, urllib.request, datetime

content = '''CURATED_CONTENT_HERE'''
obs_id = 'OBS_ID_HERE'
derived_from = DERIVED_FROM_LIST_HERE
query = 'QUERY_HERE'

payload = {
    'items': [{
        'content': content,
        'context': 'observation',
        'document_id': obs_id,
        'metadata': {
            'type': 'observation',
            'project': 'hindsight-decision-oracle',
            'date': datetime.date.today().isoformat(),
            'derived_from': ', '.join(derived_from),
            'query': query
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

Replace placeholders with confirmed values.

### Step 8 — Confirm completion

Report:
- `{OBS-NNN}` retained to oracle bank
- `derived_from`: {IDs}
- Suggested next step: `/oracle "Summarize {OBS-NNN}"` to verify recall
