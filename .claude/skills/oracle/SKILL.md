---
name: "oracle"
description: "Query the Decision Oracle — calls Hindsight reflect to surface relevant prior decisions, patterns, and constraints at a decision point."
argument-hint: "Your decision question"
user-invocable: true
---

# Oracle Query

Query the Decision Oracle using Hindsight's `reflect` API. This synthesizes prior CDRs, ADRs, session logs, and the Decision Constitution into a direct answer to your decision question.

## Arguments

```
$ARGUMENTS
```

If `$ARGUMENTS` is empty, ask the user: "What decision are you facing?"

## Execution

1. **Check that `$ARGUMENTS` is not empty.** If empty, ask for the question before proceeding.

2. **Call the oracle.** Run this Bash command:

```bash
curl -s -X POST "http://localhost:9077/v1/default/banks/oracle/reflect" \
  -H "Content-Type: application/json" \
  -d "{\"query\": $(echo "$ARGUMENTS" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read().strip()))'), \"budget\": \"medium\"}"
```

If the curl command fails with a connection error:
- Surface this message: **Oracle unavailable** — start the daemon with:
  ```
  HINDSIGHT_API_EMBEDDINGS_LOCAL_FORCE_CPU=1 HINDSIGHT_API_RERANKER_LOCAL_FORCE_CPU=1 uvx hindsight-embed daemon start
  ```
- Do not proceed further.

3. **Parse the response.** The response JSON has a `text` field containing the oracle's markdown answer.
   - If `text` is present and non-empty: render it directly to the user.
   - If the response is a non-200 status or `text` is absent: show the raw response and note that the oracle returned no result.

4. **Append a capture prompt** at the end of your response:

> If this query surfaced a decision worth recording, capture it with `/oracle-capture "[brief description]"`.

## Notes

- The oracle answers from retained CDRs, ADRs, session logs, and the Decision Constitution mental model.
- If the bank is empty or has no relevant content, the oracle will say so — this is correct behavior, not an error.
- Budget is set to `medium` for decision-point queries (gives better synthesis than `low`, avoids `high` latency).
