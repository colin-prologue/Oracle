# oracle-query MCP server

Exposes the Decision Oracle to MCP-aware clients (Codex desktop, Codex CLI,
others) as a single tool: `oracle_query(question)`. The tool calls the local
`hindsight-embed` daemon's recall endpoint and returns the top-K slim results
plus an inline relevance-gate instruction that the calling model reads when
synthesizing the answer.

This mirrors the discipline used by Claude Code's `/oracle` skill so behavior
stays consistent across clients: the model applies the gate ("if no entry is
genuinely relevant, return the empty signal verbatim"). Synthesis happens
client-side; the server is retrieval-only.

## Requirements

- `uv` ≥ 0.10 (resolves PEP 723 inline deps on first run; ~30 packages)
- `hindsight-embed` daemon running at `localhost:9077` with the `oracle` bank
  populated. Start with:
  ```
  HINDSIGHT_API_EMBEDDINGS_LOCAL_FORCE_CPU=1 \
  HINDSIGHT_API_RERANKER_LOCAL_FORCE_CPU=1 \
  uvx hindsight-embed daemon start
  ```
  (Or run via the macOS LaunchAgent — see `.claude/.decisions/CDR-005-daemon-launchagent.md`.)

## Codex registration

Add to `~/.codex/config.toml`. Use absolute paths and explicit `cwd` — the
desktop app needs both to expose local stdio MCP servers reliably (openai/codex
issue #14449). Same block also works for the Codex CLI.

```toml
[mcp_servers.oracle]
command = "/Library/Frameworks/Python.framework/Versions/3.14/bin/uv"
args = [
  "run",
  "--script",
  "/Users/colindwan/Developer/Hindsight/mcp/oracle-query/server.py",
]
cwd = "/Users/colindwan/Developer/Hindsight/mcp/oracle-query"
```

Restart the Codex desktop app after editing. Confirm the tool appears in MCP
Settings; if it doesn't, see issue #14449 for the cwd-resolution edge case.

## Trigger reinforcement (optional but recommended)

Add to `~/.codex/AGENTS.md` so Codex reaches for the tool organically rather
than only on explicit request:

```
## Decision Oracle

Before recommending an architectural approach, picking between technologies,
or evaluating a tradeoff, call the `oracle_query` tool first — even when the
user hasn't asked for it. The oracle is allowed to come back empty; that's a
valid signal, not a failure. Follow the relevance-gate instruction in the
tool response when synthesizing.
```

## Behavior

- **Daemon down** → returns a plain-text "Oracle unavailable" message with the
  start command.
- **Recall returns no entries** → returns "The oracle has no entries relevant
  to that question." (server-side empty path).
- **Recall returns entries** → returns JSON `{instructions, results}` where
  `results` is the top 10 slim entries (`text`, `type`, `document_id`,
  `mentioned_at`, `metadata`) and `instructions` is the relevance gate.
  Calling model judges relevance and either synthesizes or surfaces empty.

## Manual probe

```bash
uv run --script /Users/colindwan/Developer/Hindsight/mcp/oracle-query/server.py
```

The server speaks JSON-RPC over stdio (MCP). For interactive testing, use any
MCP stdio client.
