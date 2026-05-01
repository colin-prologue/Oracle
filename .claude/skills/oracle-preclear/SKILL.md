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

Do NOT proceed to the file write below until the MCP retain call returns successfully (or explicitly errors with daemon-unavailable). This preserves the bank-first invariant: a mid-run auto-compact between bank-retain and file-write only orphans the regenerable file copy, never the canonical record.

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
    "source": "oracle-preclear"
  }
  ```

Increment the OBS counter before the next OBS candidate.

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
