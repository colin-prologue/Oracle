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

## Canonical locations

OBS captures retain to the oracle bank first. Any markdown mirror or later
filesystem artifact must be anchored under
`${HINDSIGHT_ROOT:-$HOME/Developer/Hindsight}` and treated as derivative of
the bank record, never as a project-local source of truth.

## Arguments

```
$ARGUMENTS
```

If `$ARGUMENTS` is empty, ask: "What observation do you want to capture?"

## Execution

### Step 1 — Check daemon

Call `mcp__hindsight__hindsight_stats(bank="oracle")`. If the call errors with a connection failure, surface: **Oracle unavailable** — see daemon start instructions in `/oracle` skill. Do not proceed.

If the response includes `pending_operations > 0`, warn the user but do not block — fit-check recall is lower stakes than synthesis. Proceed with caution noted.

### Step 2 — Determine next OBS-NNN ID

Call `mcp__hindsight__hindsight_list_documents(bank="oracle", prefix="OBS-")`. Find the highest `id` (numeric suffix). Next ID = highest + 1, zero-padded to 3 digits. If none exist, start at `OBS-001`.

### Step 3 — Run fit-check via MCP recall

Call `mcp__hindsight__hindsight_recall`:
- `bank`: `"oracle"`
- `query`: the observation text (`$ARGUMENTS`) — passed as a typed string arg, no shell escaping or `/tmp` staging needed
- `budget`: `"mid"` (default)
- `top_n`: `10` (default)

The result is the slim shape — top 10 entries with `text`, `type`, `document_id`, `mentioned_at`, `metadata`. Use this for step 4's fit narrative.

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

Apply the **OBS admission test** first: *"Did this actually happen — is it
dated, countable, and citable?"* If the observation cites no dated instance,
ask the user for one before proceeding (project + date + what occurred).

Apply the **prescription check**: if the text contains prescriptive language
("should", "must", "prefer", "always/never"), tell the user the prescription
belongs in a PHI and offer to route it to `/oracle-debate` after retaining
the descriptive remainder as the OBS. Do not retain prescriptions inside OBS
bodies.

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

After explicit user confirmation in step 6, call `mcp__hindsight__hindsight_retain_obs`:

- `bank`: `"oracle"`
- `document_id`: e.g., `"OBS-013"` (computed in step 2)
- `content`: the curated text from step 5
- `derived_from`: comma-separated list of related PHI/OBS IDs from the user's confirmation; omit if standalone
- `metadata`:
  ```json
  {
    "type": "observation",
    "date": "<YYYY-MM-DD today>",
    "relationship": "<new | extends OBS-NNN | contradicts PHI-NNN>",
    "source": "manual",
    "source_project": "<git remote slug or basename of cwd>"
  }
  ```

**Collision handling.** `OBS-{NNN}` was computed back in step 2; another capture may have claimed it since. Immediately before retaining, re-run `hindsight_list_documents(bank="oracle", prefix="OBS-")` and recompute the next free ID. The retain tool now refuses an existing ID rather than silently overwriting — if it returns `document_id ... already exists`, a concurrent session took it: bump to the next free ID, update the filename slug to match, and retry. Pass `allow_overwrite=True` *only* to deliberately correct an existing record in place, never to resolve a collision.

If retain fails for any other reason, do not create the canonical markdown file. Record capture
audit state `retain-failed` and surface the daemon or retain error to the
user. The metadata above is source metadata and must travel with the retained
bank entry when retry succeeds.

When retain succeeds, record capture audit state `retained`, then write the
derivative file to
`${HINDSIGHT_ROOT:-$HOME/Developer/Hindsight}/.decisions/obs/OBS-{NNN}-{slug}.md`
with the standard OBS banner and `**Status:** active` line (see
oracle-preclear Step 4 for the exact format) and record `file-written`
(or `bank-retained/file-write-failed` on failure).

### Step 8 — Confirm completion

Report:
- `{OBS-NNN}` retained to oracle bank (`source: manual`)
- `derived_from`: {IDs or "none — standalone"}
- `relationship`: {new / extends / contradicts}
- Suggested follow-up: `/oracle "Summarize {OBS-NNN}"` to verify recall
