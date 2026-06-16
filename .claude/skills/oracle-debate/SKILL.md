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

Target PHI body ≤ ~2KB. A PHI is a normative claim with its commitment
structure (tensions, revision triggers) — not an incident report. If the
draft exceeds ~2KB, move narrative into an OBS and cite it under Evidence.

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
{The experience or repeated pattern that grounded this position — 2-4
sentences. Detailed case studies do NOT go here: capture them as OBS records
and cite them in Evidence below.}

### Evidence
{Bulleted OBS-NNN citations, one line each: `- OBS-NNN — {one-line summary}
(supports)`. If no OBS exists yet for the grounding incident, create one in
the same session and cite it. Tension evidence is listed here too, marked
`(tension)`.}

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

Once confirmed in step 3, call the `mcp__hindsight__hindsight_retain_phi` tool:

- `bank`: `"oracle"`
- `document_id`: e.g., `"PHI-020"` (computed in step 1)
- `content`: the full confirmed PHI markdown, **starting at the `## PHI-NNN ...` heading — NOT including the `<!-- ORACLE ARTIFACT -->` banner**. The banner is filesystem-only; embedding it in the bank adds retrieval noise.
- `derived_from`: any related PHI/OBS IDs cited in the debate, comma-separated; or omit if none
- `metadata`:
  ```json
  {
    "type": "philosophy",
    "domain": "<from the PHI domain field>",
    "date": "<YYYY-MM-DD today>",
    "source": "oracle-debate",
    "source_project": "<from step 1>"
  }
  ```

**Collision handling.** `PHI-{NNN}` was computed back in step 1; another capture may have claimed it during the debate. Immediately before retaining, re-run `hindsight_list_documents(bank="oracle", prefix="PHI-")` and recompute the next free ID. The retain tool now refuses an existing ID rather than silently overwriting — if it returns `document_id ... already exists`, a concurrent session took it: bump to the next free ID, update the filename slug to match, and retry. Pass `allow_overwrite=True` *only* to deliberately correct an existing record in place, never to resolve a collision.

If the tool errors with a daemon connection failure:
- Surface: **Oracle unavailable** — see daemon start instructions in `/oracle` skill
- Record capture audit state `retain-failed`
- Stop. If retain fails, do not create the canonical markdown file. The user can retry after the daemon is available.

**Do NOT proceed to step 5 until step 4 has succeeded.** This preserves the retain-bank-first ordering.

### Step 5 — Write the canonical PHI file

Derive the filename slug from the title: lowercase, spaces → hyphens, strip punctuation.

Write using the **Write tool** with an absolute path — never `$(pwd)`, never a relative path:

```
${HINDSIGHT_ROOT:-$HOME/Developer/Hindsight}/.decisions/phi/PHI-{NNN}-{slug}.md
```

If the resolved path does not point at the Hindsight repo, stop and surface the error. The file is a browsable derivative of the bank record — the bank retain in Step 4 is the canonical store.

If the bank retain succeeded but this markdown write fails, report partial success and retry or regenerate the markdown without duplicating the retained bank entry. Record capture audit state `bank-retained/file-write-failed`. When the file write succeeds, record capture audit state `file-written`.

For each transition, record capture audit state using the canonical Oracle capture audit shape: `approved`, `retained`, `bank-retained/file-write-failed`, `file-written`, or `retain-failed`.

### Step 6 — Confirm completion

Report:
- PHI file written to `$HINDSIGHT_ROOT/.decisions/phi/PHI-{NNN}-{slug}.md`
- Retained to oracle bank (or note if retain failed)
- Suggested follow-up (run from the Hindsight repo): `git add .decisions/phi/ && git commit -m 'Add PHI-{NNN}: {title}'`
