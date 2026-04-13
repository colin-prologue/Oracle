## CDR-001 — Hindsight daemon must use key-based LLM provider

**Date:** 2026-04-09
**Project:** Hindsight / Decision Oracle
**Domain:** tooling, infrastructure
**Session:** Initial Hindsight install and oracle setup

### Decision
Use `anthropic` as the LLM provider for hindsight-embed, not `claude-code`.

### Context
The configure wizard omits `claude-code` from its interactive menu. It was set
manually to avoid needing an additional API key (consistent with solo-developer
preference for minimizing external accounts). This caused cascading Python
process spawns, macOS crash dialogs, and port-binding collisions on :9077.

### Options Considered
- **`claude-code`** — no separate API key; uses existing Claude auth. Attempted
  specifically because it avoids an extra account. Rejected: the provider routes
  LLM calls through the Claude Agent SDK, which is session-bound. Running it
  inside an active Claude Code session creates nested SDK auth loops and resource
  contention. The wizard omits it deliberately — bypassing that was the mistake.
- **`openai`** — stateless, well-tested. Not chosen: requires a separate key.
- **`anthropic` (chosen)** — stateless, key-based. Anthropic key already exists
  for Claude subscription; this is not an "extra account," just surfacing an
  already-held credential for daemon use.

### Constraints That Applied
- Solo developer preference: minimize external service accounts
- Daemon must be stateless and session-independent
- Anthropic key already available via Claude subscription

### Confidence
High — root cause confirmed by reading claude_code_llm.py. Cascade reproduced
twice before fix identified.

### Revisit Trigger
If Anthropic releases a headless/service-account mode for the Agent SDK that
doesn't require an active CLI session.
