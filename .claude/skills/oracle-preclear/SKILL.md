---
name: "oracle-preclear"
description: "Scan the current conversation for oracle-worthy content before /clear — proposes PHI/OBS candidates for rapid approval, retains approved ones, writes session summary. Run this instead of going straight to /clear."
user-invocable: true
---

# Oracle Pre-Clear

Scan the current conversation and extract oracle-worthy content before running `/clear`. No argument needed — Claude reads the conversation context itself, proposes candidates, handles rapid approval, retains approved ones, then writes and retains the session summary.

**This is the only retention path when using `/clear`. PreCompact does not fire on `/clear`, only on `/compact`.**

## Execution

### Step 1 — Check daemon and gather orientation data

Run all of these in parallel:

```bash
curl -s http://localhost:9077/v1/default/banks/oracle/stats
```

```bash
curl -s http://localhost:9077/v1/default/banks/oracle/documents | python3 -c "
import json, sys, re
docs = json.load(sys.stdin)['items']
obs_ids = sorted([d['id'] for d in docs if re.match(r'OBS-\d+', d['id'])])
print('OBS IDs:', obs_ids)
"
```

```bash
ls "$(pwd)/.decisions/phi/" 2>/dev/null | grep -E '^PHI-[0-9]+' | sort | tail -1
```

```bash
git remote get-url origin 2>/dev/null | sed 's/.*\///' | sed 's/\.git$//' || basename "$(pwd)"
```

If daemon is unreachable, stop:

> **Oracle unavailable** — start with:
> ```
> HINDSIGHT_API_EMBEDDINGS_LOCAL_FORCE_CPU=1 HINDSIGHT_API_RERANKER_LOCAL_FORCE_CPU=1 uvx hindsight-embed daemon start
> ```

Compute from results:
- **Next OBS-NNN**: highest OBS-NNN number + 1, zero-padded to 3 digits. Start at 001 if none.
- **Next PHI-NNN**: extract number from last PHI filename (e.g. `PHI-003-...` → 3), add 1, zero-pad. Start at 001 if none.
- **Project name**: from git remote slug or directory name.

### Step 2 — Orient on existing corpus

Run a low-budget reflect to know what's already captured, so candidates don't duplicate:

```bash
python3 -c "
import json, urllib.request

payload = {'query': 'List all PHI and OBS principles currently captured in the oracle bank. One line per entry with its ID.', 'budget': 'low'}
req = urllib.request.Request(
    'http://localhost:9077/v1/default/banks/oracle/reflect',
    data=json.dumps(payload).encode(),
    headers={'Content-Type': 'application/json'},
    method='POST'
)
with urllib.request.urlopen(req, timeout=60) as resp:
    print(json.loads(resp.read()).get('response', ''))
"
```

### Step 3 — Scan conversation and propose candidates

Without prompting the user, review the current conversation. Identify **0–3 items** that meet ALL of:

- **Cross-project** — applies beyond this specific project or task
- **Not already captured** — new ground relative to the corpus summary from Step 2
- **Genuinely distilled** — a recurring instinct, a constraint surfaced, a tradeoff accepted, or a pattern noticed across multiple decisions in this session

For each candidate, classify as:
- **PHI** — a prescriptive held opinion ("prefer X over Y when Z")
- **OBS** — a descriptive pattern or observation

If nothing qualifies, say so clearly and skip to Step 5.

Present each candidate one at a time:

---
**Candidate {N} of {total}** [{PHI / OBS}] — Confidence: {high / medium / low}

> {1–3 sentence description of the pattern, written as the principle itself — not as "I noticed that..."}

**y** to retain as-is | **s** to skip | or paste edited text to retain with edits

---

Wait for user response before presenting the next candidate.

### Step 4 — Retain approved candidates

Process each approved candidate immediately after approval.

**For PHI candidates:**

Derive a filename slug from the title (lowercase, spaces to hyphens, strip punctuation).

Write the canonical PHI file to `.decisions/phi/PHI-{NNN}-{slug}.md`:

```markdown
## PHI-{NNN} — {title}

**Date:** {YYYY-MM-DD}
**Domain:** {architecture / tooling / process / infrastructure}
**Source:** {what pattern in this session prompted this}

### Philosophy
{Held opinion in 1–2 sentences. Phrased as a disposition, not a rule.}

### Why I Hold This
{The experience or repeated pattern that grounded this position.}

### Where It Applies
{Cross-project context — when does this philosophy kick in.}

### Known Tensions
{What situations create legitimate pressure against this philosophy.}

### Open to Revision When
{What would change your mind.}
```

Then retain to oracle bank:

```bash
python3 -c "
import json, urllib.request, datetime

phi = '''PHI_CONTENT_HERE'''
phi_id = 'PHI_ID_HERE'
domain = 'DOMAIN_HERE'

payload = {
    'items': [{
        'content': phi,
        'context': 'philosophy',
        'document_id': phi_id,
        'metadata': {
            'type': 'philosophy',
            'domain': domain,
            'date': datetime.date.today().isoformat(),
            'source': 'oracle-preclear'
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

Increment the PHI counter before the next PHI candidate in this session.

**For OBS candidates:**

Retain to oracle bank:

```bash
python3 -c "
import json, urllib.request, datetime

content = '''OBS_CONTENT_HERE'''
obs_id = 'OBS_ID_HERE'
derived_from = DERIVED_FROM_LIST_HERE  # list of related PHI/OBS IDs, or []

payload = {
    'items': [{
        'content': content,
        'context': 'observation',
        'document_id': obs_id,
        'metadata': {
            'type': 'observation',
            'date': datetime.date.today().isoformat(),
            'derived_from': ', '.join(derived_from) if derived_from else '',
            'source': 'oracle-preclear'
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

Increment the OBS counter before the next OBS candidate in this session.

### Step 5 — Generate and retain session summary

Without prompting the user, write a 3–5 sentence session summary from the current conversation:
- What was decided, built, or resolved
- Any rejected approaches and why
- Anything that would have been useful to know at the start of the session

Retain it:

```bash
python3 -c "
import json, urllib.request, datetime

summary = '''SESSION_SUMMARY_HERE'''
project = 'PROJECT_NAME_HERE'

payload = {
    'items': [{
        'content': summary,
        'context': 'session-log',
        'metadata': {
            'type': 'session-log',
            'project': project,
            'date': datetime.date.today().isoformat()
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
    print(json.loads(resp.read()))
"
```

Show the summary to the user before retaining so they can see what was captured.

### Step 6 — Confirm

Report:
- Any PHI/OBS retained (IDs and one-line description each)
- Session log retained
- Then say: **Oracle bank updated. Safe to `/clear`.**
