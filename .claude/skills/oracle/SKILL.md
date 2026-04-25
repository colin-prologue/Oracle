---
name: "oracle"
description: "Use BEFORE recommending an architectural approach, choosing between technologies, evaluating a tradeoff, or when the user proposes a design — queries Colin's cross-project Decision Oracle (PHIs/OBSs from prior sessions) and synthesizes a direct answer with cited prior philosophies. Empty results are a valid signal, not a failure. Also invoked explicitly via /oracle \"[question]\"."
argument-hint: "Your decision question"
user-invocable: true
---

# Oracle Query

Query the Decision Oracle. This retrieves relevant PHIs, OBSs, and session
memories from the oracle bank, then synthesizes a direct answer to your
decision question using a Sonnet subagent (subscription tokens, not API).

Architecture note: synthesis happens in-session via subagent dispatch rather
than via the daemon's `/reflect` endpoint. The daemon is retrieval-only for
this skill. See `.claude/.decisions/CDR-subscription-llm-routing.md`.

## Arguments

```
$ARGUMENTS
```

If `$ARGUMENTS` is empty, ask the user: "What decision are you facing?"

## Execution

1. **Check that `$ARGUMENTS` is not empty.** If empty, ask for the question
   before proceeding.

2. **Retrieve relevant memories from the oracle bank.**

   **Important:** the user's question (`$ARGUMENTS`) may contain shell-
   special characters (apostrophes, backticks, `$`). Do **not** embed
   `$ARGUMENTS` in any bash command line, including inside double-quoted
   strings, heredoc bodies, or `-c` arguments — the harness substitutes
   the text into the script body before bash parses it, so shell escaping
   does not protect you. Use this two-step pattern instead:

   **Step 2a — write the question to a file via the `Write` tool** (not
   via shell). Target path: `/tmp/oracle_q.txt`. Write only the
   `$ARGUMENTS` text as the file contents.

   **Step 2b — run the recall, reading the question from that file:**

```bash
python3 -c 'import json; q=open("/tmp/oracle_q.txt").read().rstrip("\n"); print(json.dumps({"query": q, "budget": "mid", "max_tokens": 4096}))' > /tmp/oracle_payload.json
curl -s -X POST "http://localhost:9077/v1/default/banks/oracle/memories/recall" \
  -H "Content-Type: application/json" \
  -d @/tmp/oracle_payload.json
```

   If the curl command fails with a connection error:
   - Surface this message: **Oracle unavailable** — start the daemon with:
     ```
     HINDSIGHT_API_EMBEDDINGS_LOCAL_FORCE_CPU=1 HINDSIGHT_API_RERANKER_LOCAL_FORCE_CPU=1 uvx hindsight-embed daemon start
     ```
   - Do not proceed further.

3. **Inspect and trim `results`.** The response has a `results` array; each
   item has `text`, `type` (`observation` | `experience`), `document_id`
   (e.g. `PHI-005`, `OBS-003`), `mentioned_at`, and optional `metadata`.
   Recall returns rank-ordered by relevance.

   - If `results` is empty: tell the user "The oracle has no entries
     relevant to that question." Do not dispatch a subagent. Stop here.
   - Otherwise, take the top 10 results (or fewer if the array is shorter)
     and project each to the slim shape `{text, type, document_id,
     mentioned_at, metadata}`, dropping null fields. This is the
     `{RESULTS_JSON}` value passed to the synthesis subagent in step 4.

4. **Dispatch a synthesis subagent.** Use the `Agent` tool with these
   parameters:

   - `subagent_type`: `general-purpose`
   - `model`: `sonnet`
   - `description`: `Oracle synthesis`
   - `prompt`: a self-contained brief built from the template below.

   Synthesis brief template (substitute `{QUESTION}` and `{RESULTS_JSON}`):

   ```
   You are synthesizing an answer for the Decision Oracle. The oracle
   models Colin's cross-project decision-making philosophies and patterns.
   Its bank holds PHIs (philosophies — held opinions) and OBSs (observed
   patterns) extracted from prior sessions.

   Decision question:
   {QUESTION}

   Retrieved memories from the oracle bank (most relevant first):
   {RESULTS_JSON}

   Write a direct markdown answer to the decision question that:
   - cites specific PHI-NNN / OBS-NNN identifiers where relevant —
     `document_id` carries them for `experience`-type entries, but
     `observation`-type entries usually leave `document_id` null and embed
     the IDs in the body text (e.g., "PHI-001 philosophy…"). Extract from
     either source; do not invent IDs;
   - leads with the answer, not the reasoning;
   - surfaces tensions or counter-evidence in the retrieved memories
     before stating a recommendation;
   - flags when the bank's evidence is thin or off-topic — say so plainly
     rather than padding;
   - stays under ~250 words unless the question genuinely needs more.

   Do not include preamble, meta-commentary about the synthesis process,
   restatements of the question, or trailing orientation/next-step blocks.
   Output only the markdown answer.
   ```

   Pass the slim top-10 results from step 3 inline as JSON for
   `{RESULTS_JSON}`.

5. **Render the subagent's response directly to the user.**

6. **Append a capture prompt** at the end:

   > If this query surfaced a decision worth recording, capture it with
   > `/oracle-debate "[brief description]"`.

## Notes

- The oracle answers from retained PHIs, OBSs, session logs, and the
  Decision Constitution mental model — whatever `/recall` surfaces
  semantically.
- If the bank is empty or has no relevant content, say so plainly. This
  is correct behavior, not an error.
- Synthesis runs on subscription tokens at Sonnet 4.6. The previous
  `/reflect` path used haiku-3 against the Anthropic API; we accept a
  modest token-cost increase for subscription-vs-API routing.
