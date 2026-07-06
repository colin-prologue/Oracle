---
name: oracle
description: Query the team decision oracle at a decision point. Use BEFORE recommending an architectural approach, choosing between technologies, or evaluating a tradeoff — even unprompted. Empty results are a valid signal, not a failure. Invoked explicitly via /oracle "[question]".
---

# Oracle Query (file-based)

Answer a decision question from the team's PHI/OBS record corpus. Retrieval is
an index scan — no daemon, no embeddings.

Resolve `ORACLE_ROOT` (env var; default `~/team-oracle`). If the directory is
missing, tell the user to clone the oracle repo and stop.

## Arguments

`$ARGUMENTS` is the decision question. If empty, ask: "What decision are you facing?"

## Execution

1. **Load the index.** Prefer the remote tip so answers reflect teammates'
   latest merges: `git -C $ORACLE_ROOT show origin/main:INDEX.md`; fall back to
   the local file if that fails. Note which revision it came from — step 3 must
   read records from the same one. (Skip loading if a `<team-oracle-index>`
   block is already in context from the SessionStart hook; its `rev` attribute
   names the revision.)

2. **Pick candidates.** From the index, select up to 8 record IDs whose hooks
   plausibly bear on the question. Judge from the hook lines only — do not open
   every file. If nothing plausibly relates, go straight to the empty answer in
   step 4.

3. **Read the candidate files from the same revision as the index.** When the
   index came from `origin/main`, the working tree may be behind and lack a
   freshly merged record file — resolve each ID's path and content at that
   revision:

   ```
   git -C $ORACLE_ROOT ls-tree -r --name-only origin/main records/ | grep <ID>
   git -C $ORACLE_ROOT show origin/main:<path>
   ```

   When the index came from the local file — or a record is missing at the
   remote revision — read from `$ORACLE_ROOT/records/{phi,obs}/` instead.

4. **Relevance gate, then synthesize.** Re-judge each opened record against the
   question's actual subject matter, not surface keywords. If none survives,
   reply exactly:

   > The oracle has no entries relevant to that question.

   Otherwise write a direct markdown answer that:
   - leads with the answer, not the reasoning;
   - cites PHI-NNN / OBS-NNN identifiers, noting each PHI's status —
     a `contested` or `proposed` PHI is signal, not settled policy;
   - surfaces tensions or counter-evidence among the records before the
     recommendation;
   - distinguishes cited records from current-session inference;
   - says plainly when evidence is thin;
   - stays under ~250 words unless the question genuinely needs more.

5. **Log the query.** Append one JSON line to
   `$ORACLE_ROOT/queries/YYYY-MM.<username>.jsonl` (create if absent;
   `<username>` from `$USER`):

   ```json
   {"timestamp": "<ISO8601>", "user": "<username>", "question": "...",
    "answer": "<full markdown answer>",
    "retrieved_ids": ["opened records"], "accepted_ids": ["cited"],
    "rejected_ids": ["opened but gated out"], "outcome": "relevant | empty"}
   ```

   Logging is best-effort — if the write fails, still deliver the answer.
   These logs are the usage signal that drives OBS→PHI graduation; include
   them in your next record PR so they reach the shared repo.

6. **Append a capture prompt:**

   > If this surfaced a decision worth recording, capture it with `/oracle-debate` (opinion) or `/oracle-observe` (pattern).
