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

Call these MCP tools in parallel:

- `mcp__hindsight__hindsight_stats(bank="oracle")` — confirms daemon connectivity
- `mcp__hindsight__hindsight_list_documents(bank="oracle", prefix="OBS-")` — for next-OBS-NNN computation

Plus these filesystem operations (NOT migrated — they don't go through the daemon):

```bash
HINDSIGHT_ROOT="${HINDSIGHT_ROOT:-$HOME/Developer/Hindsight}"
test -d "$HINDSIGHT_ROOT/.decisions/phi" && \
  ls "$HINDSIGHT_ROOT/.decisions/phi/" | grep -E '^PHI-[0-9]+' | sort | tail -1 || \
  echo "MISSING: $HINDSIGHT_ROOT/.decisions/phi"
```

```bash
git remote get-url origin 2>/dev/null | sed 's/.*\///' | sed 's/\.git$//' || basename "$(pwd)"
```

If the MCP stats call errors with a connection failure: surface **Oracle unavailable** with daemon start instructions, stop.

If the PHI listing returns `MISSING:`: surface **Hindsight repo not found at `$HINDSIGHT_ROOT`**, stop.

Compute from results:
- **Next OBS-NNN**: highest OBS number from `list_documents` result + 1, zero-padded to 3 digits. Start at 001 if none.
- **Next PHI-NNN**: from the PHI filename listing.
- **Source project**: from git remote slug or directory name.

### Step 2 — Orient on existing corpus via MCP recall

Call `mcp__hindsight__hindsight_recall`:
- `bank`: `"oracle"`
- `query`: `"philosophies and observed patterns retained in the oracle bank"`
- `budget`: `"mid"`
- `top_n`: `15`

The result is the slim shape — top 15 corpus entries. Use as dedup signal for step 3.

### Step 3 — Scan conversation and propose candidates

Without prompting the user, review the current conversation. Identify **0–3 items** that meet ALL of:

- **Cross-project** — applies beyond this specific project or task
- **Not already captured** — new ground relative to the corpus summary from Step 2
- **Genuinely distilled** — a recurring instinct, a constraint surfaced, a tradeoff accepted, or a pattern noticed across multiple decisions in this session

For each candidate, classify as:
- **PHI** — a prescriptive held opinion ("prefer X over Y when Z")
- **OBS** — a descriptive pattern or observation

**OBS admission test** (apply before presenting an OBS candidate):
*"Did this actually happen — is it dated, countable, and citable?"* An OBS
must cite at least one dated instance (project + date + what occurred). If
the candidate cannot, it is not an OBS — drop it or reframe it.

**Prescription check:** if an OBS candidate contains prescriptive language
("should", "must", "prefer", "always/never do X"), it has a PHI candidate
inside it. Split it: present the evidence as the OBS, and present the
prescription as a separate PHI candidate (or note it as a future
/oracle-debate if the user declines the PHI now). Do not retain prescriptions
inside OBS bodies.

**Relationship tagging:** every OBS candidate that relates to an existing
PHI must name the relationship: `supports PHI-NNN`, `tension-with PHI-NNN`,
or `standalone`. Tension evidence is as valuable as support — do not
suppress it.

If nothing qualifies, say so clearly and skip to Step 5. Do not create no filler
candidates to satisfy the list. Do not retain unapproved candidates.

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

**Retain to oracle bank FIRST** via `mcp__hindsight__hindsight_retain_phi`:

- `bank`: `"oracle"`
- `document_id`: e.g., `"PHI-020"`
- `content`: PHI markdown **starting at `## PHI-NNN` heading** — NO `<!-- ORACLE ARTIFACT -->` banner (banner is filesystem-only)
- `metadata`:
  ```json
  {
    "type": "philosophy",
    "domain": "<from the PHI domain>",
    "date": "<YYYY-MM-DD today>",
    "source": "oracle-preclear",
    "source_project": "<from step 1>"
  }
  ```

Do NOT proceed to the file write below until the MCP retain call returns successfully. If retain fails, do not create the canonical markdown file. Record capture audit state `retain-failed` and leave the candidate unretained for retry. This preserves the bank-first invariant: a mid-run auto-compact between bank-retain and file-write only orphans the regenerable file copy, never the canonical record.

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

If the bank retain succeeded but this markdown write fails, report partial success and retry or regenerate the markdown without duplicating the retained bank entry. Record capture audit state `bank-retained/file-write-failed`. When the file write succeeds, record capture audit state `file-written`.

Increment the PHI counter before the next PHI candidate in this session.

**For OBS candidates:**

Call `mcp__hindsight__hindsight_retain_obs`:

- `bank`: `"oracle"`
- `document_id`: e.g., `"OBS-013"`
- `content`: the OBS body
- `derived_from`: comma-separated related PHI/OBS IDs, or omit if standalone
- `metadata`:
  ```json
  {
    "type": "observation",
    "date": "<YYYY-MM-DD today>",
    "source": "oracle-preclear",
    "source_project": "<from step 1>",
    "relationship": "<supports PHI-NNN | tension-with PHI-NNN | standalone>"
  }
  ```

**Then write the derivative OBS file** to
`${HINDSIGHT_ROOT:-$HOME/Developer/Hindsight}/.decisions/obs/OBS-{NNN}-{slug}.md`
— same bank-first ordering and failure states as PHI files
(`bank-retained/file-write-failed`, `file-written`). First line banner
(mirrors the PHI banner wording):

    <!-- ORACLE ARTIFACT — canonical copy in the oracle bank; this file is a browse mirror in the Hindsight repo. Observed evidence, not a held philosophy. -->

Then a status line, then the retained content:

    **Status:** active

    ## OBS-{NNN} — {title}
    **Relationship:** {supports PHI-NNN | tension-with PHI-NNN | standalone}

    {retained OBS body verbatim}

The `**Status:**` line is the lifecycle terminal-state record (`active` /
`graduated → PHI-NNN` / `declined YYYY-MM-DD`). The bank cannot update
documents in place, so the mirror is canonical for status only; the bank
stays canonical for content.

Increment the OBS counter before the next OBS candidate.

For each candidate transition, record capture audit state using the canonical Oracle capture audit shape: `proposed`, `approved`, `rejected`, `retained`, `bank-retained/file-write-failed`, `file-written`, or `retain-failed`.

### Step 5 — Generate and retain session summary

Without prompting the user, write a 3–5 sentence session summary from the current conversation:
- What was decided, built, or resolved
- Any rejected approaches and why
- Anything that would have been useful to know at the start of the session

Show the summary to the user before retaining so they can see what was captured.

Then call `mcp__hindsight__hindsight_retain_session_log`:

- `bank`: `"oracle"`
- `content`: the summary text
- `metadata`:
  ```json
  {
    "type": "session-log",
    "project": "<source project from step 1>",
    "date": "<YYYY-MM-DD today>"
  }
  ```

### Step 6 — Confirm

Report:
- Any PHI/OBS retained (IDs and one-line description each)
- Session log retained
- Then say: **Oracle bank updated. Safe to `/clear`.**
