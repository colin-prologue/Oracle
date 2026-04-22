---
name: "oracle-debate"
description: "Capture a Philosophy (PHI) — drafts a held opinion from session context, debates it with the user, then retains to the oracle bank and writes the canonical file to Hindsight's .decisions/phi/."
argument-hint: "Brief description of the philosophy (e.g. 'Prefer X over Y when Z')"
user-invocable: true
---

# Oracle Debate — PHI

Capture a cross-project Philosophy (PHI-NNN). Philosophies are strong opinions about how to approach decisions — prescriptive but open to debate, not hard rules. This is semi-manual by design: draft from session context, debate with the user, retain only after explicit confirmation.

## Canonical locations

PHIs are cross-project by definition, so canonical PHI files live in the Hindsight repo — **never** in the consumer project's working tree. Path resolution:

- `${HINDSIGHT_ROOT:-$HOME/Developer/Hindsight}/.decisions/phi/`

The oracle bank is source of truth; the filesystem copy is a derivative. The retain step runs **before** the file write so an interruption cannot orphan a file in a project that does not own it.

## Arguments

```
$ARGUMENTS
```

If `$ARGUMENTS` is empty, ask: "What philosophy do you want to capture?"

## Execution

### Step 1 — Determine the next PHI number

Run:
```bash
HINDSIGHT_ROOT="${HINDSIGHT_ROOT:-$HOME/Developer/Hindsight}"
test -d "$HINDSIGHT_ROOT/.decisions/phi" && \
  ls "$HINDSIGHT_ROOT/.decisions/phi/" | grep -E '^PHI-[0-9]+' | sort | tail -1 || \
  echo "MISSING: $HINDSIGHT_ROOT/.decisions/phi"
```

If the output starts with `MISSING:`, stop:

> **Hindsight repo not found at `$HINDSIGHT_ROOT`.** Set `HINDSIGHT_ROOT` to the Hindsight repo path, or clone it to `~/Developer/Hindsight`. PHI files must live there, not in the current project.

Extract the number from the last filename (e.g., `PHI-002-...` → `2`). Next PHI number is `N+1`, zero-padded to 3 digits (e.g., `003`).

If the directory is empty or no PHI files exist, start at `001`.

Also capture the **source project** (the project that surfaced this PHI — the philosophy itself is cross-project):

```bash
git remote get-url origin 2>/dev/null | sed 's/.*\///' | sed 's/\.git$//' || basename "$(pwd)"
```

### Step 2 — Draft the Philosophy

Using `$ARGUMENTS` and session context, draft a PHI in this schema:

```markdown
<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-{NNN} — {title}

**Date:** {YYYY-MM-DD}
**Domain:** {e.g. architecture, tooling, process, infrastructure}
**Source Project:** {project that surfaced this PHI — the philosophy itself is cross-project}
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

Once confirmed, run the retain below.

The bank `phi` content **must not include the `<!-- ORACLE ARTIFACT -->` banner** — that banner is a filesystem-only safeguard and adds retrieval noise if embedded. Build the bank payload starting at the `## PHI-{NNN}` heading; add the banner only when writing the file in Step 5.

```bash
python3 -c "
import json, urllib.request, datetime

phi = '''FULL_PHI_CONTENT_HERE'''  # starts at '## PHI-NNN ...' — no banner

domain = 'PHI_DOMAIN_HERE'
phi_id = 'PHI_ID_HERE'
source_project = 'SOURCE_PROJECT_HERE'
today = datetime.date.today().isoformat()

payload = {
    'items': [{
        'content': phi,
        'context': 'philosophy',
        'document_id': phi_id,
        'metadata': {
            'type': 'philosophy',
            'domain': domain,
            'date': today,
            'source': 'oracle-debate',
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
    result = json.loads(resp.read())
    print(json.dumps(result, indent=2))
"
```

Replace:
- `FULL_PHI_CONTENT_HERE` — full confirmed PHI markdown (escape backslashes and triple-quotes)
- `PHI_DOMAIN_HERE` — domain field from the PHI (e.g., `architecture`)
- `PHI_ID_HERE` — e.g., `PHI-004`
- `SOURCE_PROJECT_HERE` — the project captured in Step 1

If the retain call fails with a connection error:
- Note: **Oracle unavailable** — see daemon start instructions in `/oracle` skill
- Still write the PHI file in Step 5 (don't lose the capture)

### Step 5 — Write the canonical PHI file

Derive the filename slug from the title: lowercase, spaces → hyphens, strip punctuation.

Write using the **Write tool** with an absolute path — never `$(pwd)`, never a relative path:

```
${HINDSIGHT_ROOT:-$HOME/Developer/Hindsight}/.decisions/phi/PHI-{NNN}-{slug}.md
```

If the resolved path does not point at the Hindsight repo, stop and surface the error. The file is a browsable derivative of the bank record — the bank retain in Step 4 is the canonical store.

### Step 6 — Confirm completion

Report:
- PHI file written to `$HINDSIGHT_ROOT/.decisions/phi/PHI-{NNN}-{slug}.md`
- Retained to oracle bank (or note if retain failed)
- Suggested follow-up (run from the Hindsight repo): `git add .decisions/phi/ && git commit -m 'Add PHI-{NNN}: {title}'`
