---
name: "oracle-synthesize"
description: "Synthesize a new Observation from retained PHIs/OBSs via a reflect query — presents output for curation, then retains the confirmed result as OBS-NNN."
argument-hint: "Optional: override the default synthesis query"
user-invocable: true
---

# Oracle Synthesize

Run a reflect query against the oracle bank to extract cross-entry patterns, curate the output, and retain it as a new Observation (OBS-NNN).

Use this for **periodic synthesis cycles** — generating a new observation from what's already in the corpus. For impromptu insights you want to integrate, use `/oracle-observe` instead.

## Arguments

```
$ARGUMENTS
```

If `$ARGUMENTS` is provided, use it as the reflect query. Otherwise use the default:

> *"What patterns define how I make decisions? Cite specific PHI and OBS IDs (e.g., PHI-001, OBS-001) in your response to ground the synthesis."*

## Execution

### Step 1 — Check daemon and pending operations

Run:
```bash
curl -s http://localhost:9077/v1/default/banks/oracle/stats
```

If `pending_operations > 0`, stop and tell the user:
> **Daemon has pending operations — reflect may be incomplete. Wait for `pending_operations: 0` before synthesizing.**

### Step 2 — Determine next OBS-NNN ID

Run:
```bash
curl -s http://localhost:9077/v1/default/banks/oracle/documents
```

Parse the response for any `id` matching `OBS-\d+`. Find the highest number. Next ID is that number + 1, zero-padded to 3 digits. If none exist, start at `OBS-001`.

### Step 3 — Recall + synthesis subagent

Synthesis used to be a daemon-side `/reflect` call (paid API). It now
runs as `/recall` (retrieval) + a Sonnet subagent dispatched from this
session (subscription tokens). See
`.claude/.decisions/CDR-subscription-llm-routing.md`.

**Important:** `$ARGUMENTS` may contain shell-special characters
(apostrophes, backticks, `$`). Do **not** embed it in any bash command
line — the harness substitutes the text into the script body before
bash parses it, so shell escaping does not protect you.

**Step 3a — write the query to a file via the `Write` tool** (not via
shell). Target path: `/tmp/oracle_synthesize_query.txt`. If `$ARGUMENTS`
is non-empty, write its contents. Otherwise write the default query:

> What patterns define how I make decisions? Cite specific PHI and OBS IDs (e.g., PHI-001, OBS-001) in your response to ground the synthesis.

**Step 3b — recall a wide spread of corpus entries** for the subagent:

```bash
python3 -c "
import json, urllib.request
q = open('/tmp/oracle_synthesize_query.txt').read().rstrip('\n')
payload = {'query': q, 'budget': 'high', 'max_tokens': 8192}
req = urllib.request.Request(
    'http://localhost:9077/v1/default/banks/oracle/memories/recall',
    data=json.dumps(payload).encode(),
    headers={'Content-Type': 'application/json'},
    method='POST'
)
with urllib.request.urlopen(req, timeout=60) as resp:
    d = json.loads(resp.read())
    slim = []
    for r in d.get('results', [])[:20]:
        item = {k: r.get(k) for k in ('text', 'type', 'document_id', 'mentioned_at', 'metadata') if r.get(k) is not None}
        slim.append(item)
    print(json.dumps(slim))
" > /tmp/oracle_synthesize_recall.json
```

If the recall result is empty:
> **Recall returned no entries — bank may have insufficient content. Do not retain.**

**Step 3c — dispatch a synthesis subagent** via the `Agent` tool with:

- `subagent_type`: `general-purpose`
- `model`: `sonnet`
- `description`: `Oracle synthesis (cross-corpus pattern)`
- `prompt`: a self-contained brief built from the template below.
  Read `/tmp/oracle_synthesize_query.txt` (the query) and
  `/tmp/oracle_synthesize_recall.json` (the corpus sample) into the
  prompt body inline.

Synthesis brief template:

```
You are running a periodic synthesis cycle for the Decision Oracle. The
oracle models Colin's cross-project decision-making philosophies and
patterns. Its bank holds PHIs (philosophies — held opinions) and OBSs
(observed patterns) extracted from prior sessions.

This is not a decision-point query. The output will be retained as a new
Observation (OBS-NNN) in the bank itself, so it must be a distilled
pattern statement, not an answer.

Synthesis query:
{QUERY}

Corpus sample (top 20 entries by relevance, JSON):
{RESULTS_JSON}

Write a markdown OBS body that:
- distills a *cross-entry pattern* — a recurring instinct, constraint,
  or tradeoff visible across multiple entries — not a summary of one
  entry;
- cites at least 2 specific PHI-NNN / OBS-NNN identifiers in the body
  text. Use `document_id` for `experience`-type entries; for
  `observation`-type entries the IDs are usually embedded in the body
  (e.g., "PHI-005 principle…"). Do not invent IDs;
- is suitable for direct retention (no preamble, no meta-commentary, no
  trailing orientation block);
- stays under ~200 words;
- if the corpus sample is too thin or off-topic to support a real
  synthesis, say so plainly in one sentence and stop — do not pad.
```

### Step 4 — Present for curation

Show the subagent's synthesized output verbatim and ask:

> **Review this synthesized Observation before retention:**
>
> {subagent output}
>
> Edit as needed. The curated version will be retained as {OBS-NNN}.

Wait for the user's response. Accept edits. Do not proceed until the user confirms the curated text.

### Step 5 — Extract citations

Parse the curated text for PHI/OBS identifiers using pattern `(PHI|OBS)-\d{3}`. These populate `metadata.derived_from`.

If fewer than 2 identifiers are found, warn:
> **Fewer than 2 PHI/OBS citations found — `derived_from` will be sparse. Proceed anyway?**

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
