---
name: "oracle"
description: "Use BEFORE recommending an architectural approach, choosing between technologies, evaluating a tradeoff, or when the user proposes a design — queries Colin's cross-project Decision Oracle (PHIs/OBSs from prior sessions) and synthesizes a direct answer with cited prior philosophies. Empty results are a valid signal, not a failure. Also invoked explicitly via /oracle \"[question]\"."
argument-hint: "Your decision question"
user-invocable: true
---

# Oracle Query

Query the Decision Oracle. This retrieves relevant PHIs, OBSs, and session
memories from the oracle bank through base Hindsight recall, then synthesizes
a direct answer to your decision question using a Sonnet subagent
(subscription tokens, not API).

Architecture note: synthesis happens in-session via subagent dispatch rather
than via the daemon's `/reflect` endpoint. The daemon is retrieval-only for
this skill. See `.claude/.decisions/CDR-subscription-llm-routing.md`.

## Arguments

```
$ARGUMENTS
```

If `$ARGUMENTS` is empty, ask the user: "What decision are you facing?"

## Execution

1. **Check that `$ARGUMENTS` is not empty.** If empty, ask: "What decision are you facing?" before proceeding.

2. **Retrieve relevant memories from the oracle bank through base Hindsight recall.** Call the `mcp__hindsight__hindsight_recall` tool:

   - `bank`: `"oracle"`
   - `query`: the user's question (`$ARGUMENTS`) — passed as a typed string arg, no shell escaping needed
   - `budget`: `"mid"` (default)
   - `max_tokens`: `4096` (default)
   - `top_n`: `10` (default)

   The tool returns the slim shape — already projected to `{text, type, document_id, mentioned_at, metadata}`. No further trimming needed in step 3.

   If the tool errors with a connection failure to the daemon:
   > **Oracle unavailable** — start the daemon with:
   > ```
   > HINDSIGHT_API_EMBEDDINGS_LOCAL_FORCE_CPU=1 HINDSIGHT_API_RERANKER_LOCAL_FORCE_CPU=1 uvx hindsight-embed daemon start
   > ```
   Do not proceed.

3. **Inspect results.** If the returned list is empty, tell the user "The oracle has no entries relevant to that question." Do not dispatch a subagent. Stop here. Otherwise, the list is already top-10 slim — pass directly to step 4 as `{RESULTS_JSON}`.

4. **Dispatch a synthesis subagent.** Use the `Agent` tool with these parameters:

   - `subagent_type`: `general-purpose`
   - `model`: `sonnet`
   - `description`: `Oracle synthesis`
   - `prompt`: a self-contained brief built from the template below.

   Synthesis brief template (substitute `{QUESTION}` and `{RESULTS_JSON}` — the latter inlined as JSON string):

   ```
   You are synthesizing an answer for the Decision Oracle. The oracle
   models Colin's cross-project decision-making philosophies and patterns.
   Its bank holds PHIs (philosophies — held opinions) and OBSs (observed
   patterns) extracted from prior sessions.

   Decision question:
   {QUESTION}

   Retrieved memories from the oracle bank (most relevant first):
   {RESULTS_JSON}

   RELEVANCE GATE — apply this BEFORE writing anything else:
   Read each retrieved entry against the decision question. If none is
   genuinely relevant (i.e., addresses the question's actual subject
   matter, not just sharing surface keywords or topic-adjacent themes),
   respond with EXACTLY this single line and nothing else:

   The oracle has no entries relevant to that question.

   Do not soften, qualify, or pad. Do not summarize what was retrieved.
   Do not list near-misses. Returning empty is the correct answer when
   the bank holds no signal — empty results are a valid, accepted outcome.

   If at least one entry is genuinely relevant, proceed to synthesis.

   Write a direct markdown answer to the decision question that:
   - cites specific PHI-NNN / OBS-NNN identifiers where relevant —
     `document_id` carries them for `experience`-type entries, but
     `observation`-type entries usually leave `document_id` null and embed
     the IDs in the body text (e.g., "PHI-001 philosophy…"). Extract from
     either source; do not invent IDs;
   - leads with the answer, not the reasoning;
   - surfaces tensions or counter-evidence in the retrieved memories
     before stating a recommendation;
   - distinguishes cited Oracle memory from current-session inference;
   - if a relevant memory lacks a PHI/OBS identifier, cite it with an
     explicit missing-identifier marker rather than inventing an ID;
   - flags when the bank's evidence is thin or off-topic — say so plainly
     rather than padding;
   - stays under ~250 words unless the question genuinely needs more.

   Do not include preamble, meta-commentary about the synthesis process,
   restatements of the question, or trailing orientation/next-step blocks.
   Output only the markdown answer.
   ```

5. **Render the subagent's response directly to the user.**

6. **Log the query** via `mcp__hindsight__hindsight_log_query`:

   - `client`: `"claude-code"`
   - `question`: `$ARGUMENTS` (typed string arg, no shell escaping)
   - `answer`: the subagent's full response text
   - `recall_data`: a canonical relevance-gate audit object:
     ```json
     {
       "workflow_source": "claude-skill",
       "recall_substrate": "hindsight:oracle",
       "outcome": "relevant | empty | irrelevant | failure",
       "retrieved_ids": ["bank document ids, derived per the rule below"],
       "accepted_ids": ["the subset of retrieved_ids that passed the relevance gate"],
       "rejected_ids": ["the subset of retrieved_ids rejected by the relevance gate"],
       "rejection_reasons": {"<id from rejected_ids>": "short reason"},
       "result_count": 0
     }
     ```

   **ID derivation rule.** Every id in `retrieved_ids`, `accepted_ids`,
   `rejected_ids`, and the keys of `rejection_reasons` is a bank document
   id that `hindsight_list_documents` can resolve. Build `retrieved_ids`
   mechanically from the step-2 recall results:

   1. For each result, take its `document_id` field copied
      character-for-character — `PHI-NNN`/`OBS-NNN` for retained entries,
      a raw UUID for session-log documents. A UUID is the correct id for
      a session-log hit; log it as-is.
   2. When `document_id` is null, use the `PHI-NNN`/`OBS-NNN` identifier
      embedded in the entry's text if one is present. A result with
      neither contributes no id (it still counts toward `result_count`).
   3. List each document id once, in first-retrieval order, even when
      several memory units came from the same document.
   4. Set `result_count` to the length of the step-2 results list itself,
      counting every memory unit including repeats of the same document —
      10 results hitting 9 distinct documents log `result_count: 10`
      alongside 9 `retrieved_ids`.

   `accepted_ids` and `rejected_ids` partition `retrieved_ids` using the
   same verbatim strings — when the synthesis answer describes an entry
   without naming an identifier, match it back to its recall result by
   content and log the id the rule above derived for that result
   (its `document_id`, or the text-embedded id when `document_id` is
   null).

   The MCP tool resolves `${HINDSIGHT_ROOT}/.decisions/queries/YYYY-MM.jsonl` internally — no path argument needed.

7. **Append a capture prompt** at the end:

   > If this query surfaced a decision worth recording, capture it with `/oracle-debate "[brief description]"`.

## Notes

- The oracle answers from retained PHIs, OBSs, session logs, and the Decision Constitution mental model — whatever the recall tool surfaces semantically.
- If the bank is empty or has no relevant content, say so plainly. This is correct behavior, not an error.
- Synthesis runs on subscription tokens at Sonnet 4.6 via the Agent tool. The previous `/reflect` path used haiku-3 against the Anthropic API.
- All daemon HTTP calls are routed through `mcp__hindsight__*` MCP tools — no inline `python3 -c`, `curl`, or `/tmp` staging.
