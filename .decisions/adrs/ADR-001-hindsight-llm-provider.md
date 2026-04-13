## ADR-001 — Hindsight daemon must use a key-based LLM provider

**Date:** 2026-04-09
**Project:** Hindsight / Decision Oracle
**Domain:** tooling, infrastructure
**Session:** Initial Hindsight install and oracle setup

### Decision
Use `anthropic` (key-based) as the LLM provider for the `hindsight-embed` daemon, not `claude-code`.

### Context
During initial setup, the `hindsight-embed configure` wizard was run interactively but did not present `claude-code` as an option. The provider was manually set to `claude-code` in the profile `.env`, bypassing the wizard's safeguard. This caused cascading Python process spawning, macOS crash dialogs, and port-binding collisions on `localhost:9077` across multiple sessions.

### Options Considered

- **`claude-code` provider** — routes LLM calls through the Claude Agent SDK, which authenticates via the active `claude auth login` session. No separate API key needed. *Rejected:* the daemon is a background process that must be stateless and independent. Running it inside an active Claude Code session creates nested SDK auth loops — the daemon's LLM calls contend with the active session's context, causing cascade failures. The configure wizard deliberately excluded this provider from interactive setup for this reason.

- **`openai` provider** — stateless, key-based, well-tested by plugin authors. *Not chosen:* requires a separate OpenAI key; Anthropic key already available.

- **`anthropic` provider (chosen)** — stateless, key-based, consistent with existing Anthropic credentials. Daemon operates independently of any Claude Code session. No auth contention possible.

### Constraints That Applied
- No separate OpenAI API key; Anthropic key available
- Must not require active Claude Code session to function
- Daemon must survive session restarts without reconfiguration

### Confidence
High — root cause was confirmed by reading `claude_code_llm.py` and `llm_wrapper.py` source. The cascade was reproduced twice before the fix was identified.

### Revisit Trigger
If Anthropic releases a headless/service-account mode for the Agent SDK that doesn't require an active CLI session, `claude-code` could be reconsidered. Until then, key-based providers only.

### Scope
Cross-cutting — affects all Hindsight daemon operations (retain, recall, temporal extraction, consolidation)

### Affected Systems
- `hindsight-embed` daemon (`~/.hindsight/profiles/claude-code.env`)
- All hook scripts (recall.py, retain.py) that depend on the daemon being available

### Reversibility
Reversible with low cost — switching providers is a 1-line change in the profile `.env`

### Status
Accepted
