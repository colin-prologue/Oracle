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

Call `mcp__hindsight__hindsight_stats(bank="oracle")`. If `pending_operations > 0`, stop and tell the user:

> **Daemon has pending operations — synthesis may be incomplete. Wait for `pending_operations: 0` before synthesizing.**

If the call errors with daemon-unavailable, surface the start command and stop.

### Step 2 — Determine next OBS-NNN ID

Call `mcp__hindsight__hindsight_list_documents(bank="oracle", prefix="OBS-")`. Highest `id` numeric suffix + 1, zero-padded. Start at `OBS-001` if none.

### Step 3 — Recall + synthesis subagent

Synthesis runs as MCP recall + Sonnet subagent dispatch (subscription tokens). See `.claude/.decisions/CDR-subscription-llm-routing.md`.

**Step 3a — Determine the query.** If `$ARGUMENTS` is non-empty, use it. Otherwise use the default:

> What patterns define how I make decisions? Cite specific PHI and OBS IDs (e.g., PHI-001, OBS-001) in your response to ground the synthesis.

**Step 3b — Recall a wide spread of corpus entries** via `mcp__hindsight__hindsight_recall`:

- `bank`: `"oracle"`
- `query`: the query text from 3a (typed string arg — no `/tmp` staging needed)
- `budget`: `"high"` (synthesize uses higher budget than other recall callers)
- `max_tokens`: `8192`
- `top_n`: `20`

The result is the slim top-20 — pass directly to step 3c as `{RESULTS_JSON}`.

If the result is empty:
> **Recall returned no entries — bank may have insufficient content. Do not retain.**

**Step 3c — Dispatch a synthesis subagent** via the `Agent` tool with:

- `subagent_type`: `general-purpose`
- `model`: `sonnet`
- `description`: `Oracle synthesis (cross-corpus pattern)`
- `prompt`: build the brief below, inlining the query and the slim recall result as JSON.

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
- names tensions, counter-evidence, or limits in the corpus before
  stating the synthesized pattern when the sample points in more than
  one direction;
- distinguishes cited Oracle memory from current-session inference;
- if a relevant memory lacks a PHI/OBS identifier, mark the citation gap
  explicitly rather than inventing an ID;
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

After explicit user confirmation in step 6, call `mcp__hindsight__hindsight_retain_obs`:

- `bank`: `"oracle"`
- `document_id`: e.g., `"OBS-013"` (from step 2)
- `content`: the curated text from step 4
- `derived_from`: comma-separated PHI/OBS IDs extracted in step 5
- `metadata`:
  ```json
  {
    "type": "observation",
    "date": "<YYYY-MM-DD today>",
    "query": "<the synthesis query>"
  }
  ```

### Step 8 — Confirm completion

Report:
- `{OBS-NNN}` retained to oracle bank
- `derived_from`: {IDs}
- Suggested next step: `/oracle "Summarize {OBS-NNN}"` to verify recall
