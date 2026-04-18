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
- `/oracle-preclear` — **Run before `/clear`**. Scans the conversation, proposes PHI/OBS candidates for rapid approval, retains approved ones, writes session summary. No argument needed.

Daemon runs on `http://localhost:9077` (claude-code profile). Start with:
```
HINDSIGHT_API_EMBEDDINGS_LOCAL_FORCE_CPU=1 HINDSIGHT_API_RERANKER_LOCAL_FORCE_CPU=1 uvx hindsight-embed daemon start
```

## Session End Protocol

**Before `/clear` or closing**, run:

```
/oracle-preclear
```

This scans the current conversation, proposes PHI/OBS candidates for rapid yes/skip approval, retains approved ones, and writes the session summary — all without requiring you to prompt it. `/clear` does not trigger PreCompact, so this is the only retention path.

Use `/oracle-debate "[philosophy]"` or `/oracle-observe "[insight]"` mid-session if something surfaces that you want to capture immediately rather than waiting for pre-clear.

## Active Technologies
- Python 3.14 (scripts) — no new runtime + Hindsight daemon (http://localhost:9077), hindsight-embed (uvx), Anthropic API (claude-haiku-3) (002-oracle-pattern-modeling)
- Hindsight oracle bank (postgresql via daemon) + `.decisions/` markdown files (002-oracle-pattern-modeling)

## Recent Changes
- 002-oracle-pattern-modeling: Added Python 3.14 (scripts) — no new runtime + Hindsight daemon (http://localhost:9077), hindsight-embed (uvx), Anthropic API (claude-haiku-3)
