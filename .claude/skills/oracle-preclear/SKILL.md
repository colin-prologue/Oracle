---
name: "oracle-preclear"
description: "Scan the current conversation for oracle-worthy content before /clear — proposes PHI/OBS candidates for rapid approval, retains approved ones, writes session summary. Run this instead of going straight to /clear."
user-invocable: true
---

# Oracle Pre-Clear

Scan the current conversation and extract oracle-worthy content before running `/clear`. No argument needed — Claude reads the conversation context itself, proposes candidates, handles rapid approval, retains approved ones, then writes and retains the session summary.

**This is the only retention path when using `/clear`. PreCompact does not fire on `/clear`, only on `/compact`.**

## Canonical locations

PHIs are cross-project by definition, so canonical PHI files live in the Hindsight repo — **never** in the consumer project's working tree. Path resolution:

- `${HINDSIGHT_ROOT:-$HOME/Developer/Hindsight}/.decisions/phi/`

The oracle bank is the source of truth; the filesystem copy is a derivative. Retain to the bank **before** writing the file, so a mid-run auto-compact cannot orphan a file inside a project that does not own it.

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
HINDSIGHT_ROOT="${HINDSIGHT_ROOT:-$HOME/Developer/Hindsight}"
test -d "$HINDSIGHT_ROOT/.decisions/phi" && \
  ls "$HINDSIGHT_ROOT/.decisions/phi/" | grep -E '^PHI-[0-9]+' | sort | tail -1 || \
  echo "MISSING: $HINDSIGHT_ROOT/.decisions/phi"
```

```bash
git remote get-url origin 2>/dev/null | sed 's/.*\///' | sed 's/\.git$//' || basename "$(pwd)"
```

If daemon is unreachable, stop:

> **Oracle unavailable** — start with:
> ```
> HINDSIGHT_API_EMBEDDINGS_LOCAL_FORCE_CPU=1 HINDSIGHT_API_RERANKER_LOCAL_FORCE_CPU=1 uvx hindsight-embed daemon start
> ```

If the PHI listing returns `MISSING: ...`, stop:

> **Hindsight repo not found at `$HINDSIGHT_ROOT`.** Set `HINDSIGHT_ROOT` to the Hindsight repo path, or clone it to `~/Developer/Hindsight`. PHI files must live there, not in the current project.

Compute from results:
- **Next OBS-NNN**: highest OBS-NNN number + 1, zero-padded to 3 digits. Start at 001 if none.
- **Next PHI-NNN**: extract number from last PHI filename in Hindsight's `.decisions/phi/` (e.g. `PHI-003-...` → 3), add 1, zero-pad. Start at 001 if none.
- **Source project**: current project, from git remote slug or directory name. Recorded in the PHI metadata as its origin — the PHI itself applies cross-project.

### Step 2 — Orient on existing corpus via recall

Pull a representative sample of retained entries so Step 3 can dedupe
candidates against what's already captured. This used to call `/reflect`
(daemon-side LLM synthesis on the paid API). It's now a `/recall` call
(retrieval-only) — the raw entries are better dedup signal than a
reflected summary, and we save the synthesis token cost.

```bash
python3 -c "
import json, urllib.request
payload = {'query': 'philosophies and observed patterns retained in the oracle bank', 'budget': 'mid', 'max_tokens': 4096}
req = urllib.request.Request(
    'http://localhost:9077/v1/default/banks/oracle/memories/recall',
    data=json.dumps(payload).encode(),
    headers={'Content-Type': 'application/json'},
    method='POST'
)
with urllib.request.urlopen(req, timeout=60) as resp:
    d = json.loads(resp.read())
    for r in d.get('results', [])[:15]:
        doc = r.get('document_id') or '-'
        kind = r.get('type', '?')
        text = (r.get('text') or '').replace('\n', ' ')[:240]
        print(f'{doc} ({kind}): {text}')
"
```

Use the resulting list as context for Step 3 — when proposing candidates,
dedupe against entries that overlap on theme.

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

**Retain to oracle bank FIRST** (canonical store — if an auto-compact interrupts before the file write, the PHI is still safely captured).

The `phi` content for the bank **must not include the `<!-- ORACLE ARTIFACT -->` banner** — that banner is a filesystem-only safeguard and adds retrieval noise if embedded. Build the bank content starting at the `## PHI-{NNN}` heading; add the banner only when writing the file in the next step.

```bash
python3 -c "
import json, urllib.request, datetime

phi = '''PHI_CONTENT_HERE'''  # starts at '## PHI-NNN ...' — no banner
phi_id = 'PHI_ID_HERE'
domain = 'DOMAIN_HERE'
source_project = 'SOURCE_PROJECT_HERE'

payload = {
    'items': [{
        'content': phi,
        'context': 'philosophy',
        'document_id': phi_id,
        'metadata': {
            'type': 'philosophy',
            'domain': domain,
            'date': datetime.date.today().isoformat(),
            'source': 'oracle-preclear',
            'source_project': source_project
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

**Then write the derivative file** to `${HINDSIGHT_ROOT:-$HOME/Developer/Hindsight}/.decisions/phi/PHI-{NNN}-{slug}.md` — **never** to the current project's directory. The file is a convenience copy for browsing; the bank is source of truth.

The first line is a banner that self-identifies the file as an oracle artifact, so if the path is ever read from an unexpected location it cannot be mistaken for a local project rule:

```markdown
<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-{NNN} — {title}

**Date:** {YYYY-MM-DD}
**Domain:** {architecture / tooling / process / infrastructure}
**Source Project:** {project that surfaced this PHI — the philosophy itself is cross-project}
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

Use the Write tool with an **absolute path** built from `$HINDSIGHT_ROOT` (or `$HOME/Developer/Hindsight`) — not `$(pwd)` and not a relative path. If the path does not resolve to the Hindsight repo, stop and surface the error.

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
