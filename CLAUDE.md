# Hindsight / Decision Oracle

## Project Context

This repo is the Decision Oracle — a persistent memory layer built on Hindsight that models Colin's historical decision-making patterns and surfaces them during development sessions.

Key documents:
- **Architecture & implementation guide**: `.claude/.decisions/DECISION_ORACLE.md`
- **Philosophies**: `.decisions/phi/` (PHI-NNN — cross-project held opinions)

## Oracle Skills

- `/oracle "[question]"` — Query the oracle at a decision point. Calls Hindsight `reflect` on the `oracle` bank.
- `/oracle-debate "[philosophy]"` — Draft, debate, and retain a PHI to the oracle bank and `.decisions/phi/`.
- `/oracle-observe "[insight]"` — Capture an impromptu observation with fit-check reflect; retains as OBS-NNN.
- `/oracle-synthesize` — Periodic synthesis: reflect across the corpus, curate, retain as OBS-NNN.

Daemon runs on `http://localhost:9077` (claude-code profile). Start with:
```
HINDSIGHT_API_EMBEDDINGS_LOCAL_FORCE_CPU=1 HINDSIGHT_API_RERANKER_LOCAL_FORCE_CPU=1 uvx hindsight-embed daemon start
```

## Session End Protocol

At the end of every session, before closing:

1. **Write a session summary** (3–5 sentences):
   - What was decided, built, or resolved
   - Any rejected approaches and why
   - Anything that would have been useful to know at the start

2. **Retain it** via Bash:
   ```bash
   python3 -c "
   import json, urllib.request, datetime

   summary = '''YOUR SESSION SUMMARY HERE'''

   payload = {
       'items': [{
           'content': summary,
           'context': 'session-log',
           'metadata': {
               'type': 'session-log',
               'project': 'hindsight-decision-oracle',
               'date': datetime.date.today().isoformat()
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
       print(json.loads(resp.read()))
   "
   ```

3. **Check for new patterns**: If a new cross-project philosophy or observation emerged this session, run `/oracle-debate` or `/oracle-observe` before closing. Skip if nothing meta-level surfaced.

Session logs feed the Observation layer — Hindsight synthesizes patterns from them automatically over time.

## Active Technologies
- Python 3.14 (scripts) — no new runtime + Hindsight daemon (http://localhost:9077), hindsight-embed (uvx), Anthropic API (claude-haiku-3) (002-oracle-pattern-modeling)
- Hindsight oracle bank (postgresql via daemon) + `.decisions/` markdown files (002-oracle-pattern-modeling)

## Recent Changes
- 002-oracle-pattern-modeling: Added Python 3.14 (scripts) — no new runtime + Hindsight daemon (http://localhost:9077), hindsight-embed (uvx), Anthropic API (claude-haiku-3)
