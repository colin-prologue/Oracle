# Hindsight / Decision Oracle

## Project Context

This repo is the Decision Oracle — a persistent memory layer built on Hindsight that models Colin's historical decision-making patterns and surfaces them during development sessions.

Key documents:
- **Architecture & implementation guide**: `.claude/.decisions/DECISION_ORACLE.md`
- **Decision records**: `.decisions/cdrs/` (CDRs) and `.decisions/adrs/` (ADRs)

## Oracle Skills

- `/oracle "[question]"` — Query the oracle at a decision point. Calls Hindsight `reflect` on the `oracle` bank.
- `/oracle-capture "[decision]"` — Draft, review, and retain a CDR to the oracle bank and `.decisions/cdrs/`.

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

3. **Capture any unrecorded decisions**: If decisions were made this session that are not yet in a CDR, run `/oracle-capture "[description]"` before closing.

Session logs feed the Observation layer — Hindsight synthesizes patterns from them automatically over time.
