# Hindsight / Decision Oracle

## Project Context

This repo is the Decision Oracle — a persistent memory layer built on Hindsight that models Colin's historical decision-making patterns and surfaces them during development sessions.

Key documents:
- **Architecture & implementation guide**: `.claude/.decisions/DECISION_ORACLE.md`
- **Philosophies**: `.decisions/phi/` (PHI-NNN — cross-project held opinions). **Canonical location is this Hindsight repo**, resolved via `${HINDSIGHT_ROOT:-$HOME/Developer/Hindsight}/.decisions/phi/`. Oracle skills write here regardless of the session's working directory — PHI files must never land in a consumer project's tree.

## Oracle Skills

- `/oracle "[question]"` — Query the oracle at a decision point. Uses base Hindsight recall on the `oracle` bank, applies the Oracle relevance gate, and logs canonical query audit records.
- `/oracle-debate "[philosophy]"` — Draft, debate, and retain a PHI to the oracle bank and Hindsight's `.decisions/phi/`.
- `/oracle-observe "[insight]"` — Capture an impromptu observation with fit-check reflect; retains as OBS-NNN.
- `/oracle-synthesize` — Periodic synthesis: reflect across the corpus, curate, retain as OBS-NNN.
- `/oracle-preclear` — **Run before `/clear`**. Scans the conversation, proposes PHI/OBS candidates for rapid approval, retains approved ones, writes session summary. No argument needed.

**When to query organically:** Before recommending an architectural approach, picking between technologies, or evaluating a tradeoff, invoke `/oracle` first — even unprompted. The oracle is allowed to come back empty; that's a valid signal, not a failure.

The former standalone `mcp/oracle-query` compatibility server has been retired.
Use native Hindsight MCP tools for Oracle recall, capture, and query logging.

Daemon runs on `http://localhost:9077` (claude-code profile). Start with:
```
HINDSIGHT_API_EMBEDDINGS_LOCAL_FORCE_CPU=1 HINDSIGHT_API_RERANKER_LOCAL_FORCE_CPU=1 uvx hindsight-embed daemon start
```

## Session End Protocol

**Before `/clear` or closing**, run:

```
/oracle-preclear
```

This scans the current conversation, proposes PHI/OBS candidates for rapid yes/skip approval, retains approved ones, and writes the session summary — all without requiring you to prompt it. `/clear` does not trigger PreCompact, so this is the only retention path for that case. (Auto-compaction is now intercepted by the `PreCompact` hook in `.claude/settings.json`, which blocks auto-compact and surfaces the same nudge.)

Use `/oracle-debate "[philosophy]"` or `/oracle-observe "[insight]"` mid-session if something surfaces that you want to capture immediately rather than waiting for pre-clear.

## Active Technologies
- Python 3.14 (scripts) — no new runtime + Hindsight daemon (http://localhost:9077), hindsight-embed (uvx), Anthropic API (claude-haiku-3) (002-oracle-pattern-modeling)
- Hindsight oracle bank (postgresql via daemon) + `.decisions/` markdown files (002-oracle-pattern-modeling)
- Python 3.11+ for existing MCP/scripts; Markdown for skills, specs, and migration docs + Existing `mcp.server.fastmcp.FastMCP`, `httpx`, Python standard library HTTP/JSON/path tooling, Hindsight daemon HTTP API at `localhost:9077` (003-oracle-workflow-layer)
- Hindsight oracle bank for operational recall/retain; repository-local `.decisions/phi/` and `.decisions/queries/YYYY-MM.jsonl` for durable review/audit mirrors (003-oracle-workflow-layer)
- Oracle workflow layer over base Hindsight primitives; standalone `mcp/oracle-query` retired after deprecation gates passed (003-oracle-workflow-layer)

## Recent Changes
- 002-oracle-pattern-modeling: Added Python 3.14 (scripts) — no new runtime + Hindsight daemon (http://localhost:9077), hindsight-embed (uvx), Anthropic API (claude-haiku-3)
