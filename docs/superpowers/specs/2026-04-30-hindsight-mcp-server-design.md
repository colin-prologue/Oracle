# Hindsight MCP Server — Design Spec

**Date:** 2026-04-30
**Status:** Draft, awaiting user review before plan
**Owning repo:** `~/Developer/Hindsight`
**Workstream origin:** `~/.workstream/oracle-skills-permission-scope.md`

## Problem

The five oracle skills (`oracle`, `oracle-debate`, `oracle-observe`, `oracle-preclear`, `oracle-synthesize`) call the hindsight daemon at `http://localhost:9077` via inline `python3 -c "import json, urllib.request..."` blocks executed through Claude Code's Bash tool.

A user-level allowlist entry — `Bash(python3 -c "import json, urllib.request*)` — keeps these silent across all projects. Under prompt injection, that entry is functionally equivalent to `Bash(python3 *)`: any tool result, MCP response, or file content that drives Claude to construct a `python3 -c "import json, urllib.request; ..."` payload can do arbitrary I/O, including credential exfiltration to localhost or relays.

A companion entry — `Bash(curl * localhost:9077*)` — is narrower (substring-anchored on the daemon URL) but inherits the same drift dynamics PHI-019 warns about.

A third issue surfaced live during design: skills stage scratch files at fixed `/tmp/oracle_*.txt` paths, causing cross-session collisions when multiple Claude sessions run concurrently.

## Goal

Replace the shell-allowlist surface with a typed, bounded MCP server that adapts the existing daemon HTTP API into a Claude-Code-native tool layer. Land the security fix without introducing the drift dynamics the original allowlist suffered from.

## Non-goals

- Daemon HTTP API changes (unchanged contract)
- Hooks (PreCompact, SessionStart, SessionEnd, UserPromptSubmit) — invoked by the Claude Code harness directly, not via the user-prompt-driven Bash tool path. They run their commands (e.g., `python3 scripts/precompact_oracle_nudge.py` in `.claude/settings.json`) outside the permission-prompt gate, so the user-level Bash allowlist does not apply to them
- Localhost trust assumption — daemon listens unauthenticated on `localhost:9077`; any local process can hit it. Separate threat model.
- Bank-write authorization beyond what the harness offers — single-user personal tool; bank pollution is git-tracked (`.decisions/phi/`) and recoverable via `git revert`. The original injection-defense framing was over-design for the actual threat model.

## Architecture

Three layers, single responsibility each:

```
Claude Code session
  └── Oracle skills (5)        — no inline python3 -c HTTP blocks
      │ MCP tool calls
      ▼
  hindsight MCP server         — in repo, registered via .mcp.json
      │ HTTP (localhost:9077, unchanged)
      ▼
  hindsight daemon             — existing endpoints, no API changes
```

The MCP server is the Claude-facing contract. The daemon HTTP API is the underlying transport. Other (non-Claude) consumers (terminal, scripts, future agents) continue to hit the daemon directly via curl/HTTP.

**First-run UX note:** project-scope `.mcp.json` registration requires a one-time user approval per Claude Code project before the server connects. This is a known Claude Code behavior, not a design choice. After first approval, subsequent sessions auto-load the server without prompting.

## Tool surface (7 tools)

| Tool | Args | Returns |
|---|---|---|
| `hindsight_stats` | `bank: string` | raw daemon stats response |
| `hindsight_list_documents` | `bank: string`, `prefix?: string` (filters by `document_id` prefix, e.g., `"PHI-"` or `"OBS-"`) | array of `{document_id, type, mentioned_at, metadata?}` (raw) |
| `hindsight_recall` | `bank: string`, `query: string`, `budget?: "low"\|"mid"\|"high"`, `max_tokens?: int`, `top_n?: int = 10`, `verbose?: bool = false` | **slim shape** by default: array of `{text, type, document_id, mentioned_at, metadata?}`. With `verbose: true`, raw daemon response with scores. |
| `hindsight_retain_phi` | `bank: string`, `document_id: string`, `content: string`, `derived_from?: string`, `metadata?: object` | daemon retain response (shape not normalized — skills do not currently parse return value) |
| `hindsight_retain_obs` | `bank: string`, `document_id: string`, `content: string`, `derived_from?: string`, `metadata?: object` | daemon retain response (same as above) |
| `hindsight_retain_session_log` | `bank: string`, `content: string`, `metadata?: object` (no document_id — daemon assigns) | daemon retain response |
| `hindsight_log_query` | `client: string`, `question: string`, `answer: string`, `recall_data: object` | `{logged_path}` |

### Schema decisions

- **Recall slim-by-default with `verbose` escape valve.** The MCP server is the Claude-facing contract; optimizing the default shape for that audience is appropriate. Daemon HTTP API stays raw — non-MCP consumers get the full shape via direct curl.
- **`retain_phi` and `retain_obs` have identical schemas but stay separate tools.** Split-by-side-effect granularity preserves intent in the audit log and makes future per-tool gating possible without schema changes, even though the current permission policy auto-approves all 7.
- **`hindsight_log_query` doesn't touch the daemon.** It writes to `${HINDSIGHT_ROOT}/.decisions/queries/YYYY-MM.jsonl` (resolved against `$HINDSIGHT_ROOT`, **never** `$(pwd)`). This is the same path-anchor lesson PHI-006 captured: writing oracle artifacts via CWD lands them in consumer project trees. The MCP server must enforce `$HINDSIGHT_ROOT` resolution; if `$HINDSIGHT_ROOT` is unset, fall back to `$HOME/Developer/Hindsight`. This is the only place the MCP server reaches into the repo's `.decisions/` directory.
- **Daemon `context` field mapping.** The daemon's retain payload requires a `context` field with values `'philosophy'` / `'observation'` / `'session-log'`. The MCP server derives `context` from the tool name (no explicit arg needed) — `hindsight_retain_phi` → `'philosophy'`, etc. This keeps the MCP schema clean and prevents callers from passing a mismatched type.

## Permission policy

**All 7 MCP tools auto-approved at user level** (`~/.claude/settings.json`).

Rationale:
- Single-user personal tool; bank pollution = git-tracked, recoverable via `git revert`.
- Every existing oracle code path already includes in-skill content confirmation before retain fires (`/oracle-debate` debate loop, `/oracle-observe` confirm step, `/oracle-preclear` candidate approval). The harness prompt would ask "approve hindsight_retain_phi?" — showing tool name and args, not semantic content. Ceremony without information.
- PHI-019's drift warning is about *bash* allowlists where grants are over-permissive by construction (`Bash(python3 *)` allows any python). MCP tool grants are narrowly scoped by typed schema; there is no wider pattern to drift toward.

**Safety nets that remain:**
- In-skill content confirmation in all 5 skills (already present)
- Git tracking of `.decisions/phi/` and `.decisions/queries/` (revertible)
- Periodic allowlist audit ritual per PHI-019 (applies more strongly to bash grants we still keep around)

## Skill migration

| Skill | Today (replaced) | After (MCP) |
|---|---|---|
| `oracle` | `python3 -c` (build payload) → `curl /recall` → `python3 -c` (log) | `hindsight_recall` → `Agent` (synthesis) → `hindsight_log_query` |
| `oracle-preclear` | `curl /stats`, `curl /documents`, 4× `python3 -c` HTTP heredocs | `hindsight_stats`, `hindsight_list_documents`, `hindsight_recall`, `hindsight_retain_phi`, `hindsight_retain_obs`, `hindsight_retain_session_log` |
| `oracle-observe` | `curl /stats`, `curl /documents`, `python3 -c` (recall + retain) | `hindsight_stats`, `hindsight_list_documents`, `hindsight_recall`, `hindsight_retain_obs` |
| `oracle-debate` | `python3 -c` (retain) | `hindsight_retain_phi` |
| `oracle-synthesize` | `curl /stats`, `curl /documents`, `python3 -c` (recall + retain) | `hindsight_stats`, `hindsight_list_documents`, `hindsight_recall`, `hindsight_retain_obs` |

**What disappears across all 5 skills:**
- All inline `python3 -c "import json, urllib.request..."` heredocs for daemon HTTP
- All `curl http://localhost:9077/...` calls
- All `/tmp/oracle_*.txt` and `/tmp/oracle_*.json` scratch files (cross-session collision risk eliminated)
- The Write→Read→stage-to-/tmp dance in skill prologues

**What stays:**
- Subagent dispatch via `Agent` tool in `/oracle` and `/oracle-synthesize` (CDR-subscription-llm-routing.md unaffected)
- All hooks (PreCompact, SessionStart, SessionEnd, UserPromptSubmit) — they invoke plugin scripts directly via fully-qualified python3 paths
- **Filesystem operations in skill bodies** — `Write` to `${HINDSIGHT_ROOT}/.decisions/phi/PHI-NNN-{slug}.md` (oracle-preclear, oracle-debate), `ls .decisions/phi/ | grep PHI- | sort | tail -1` for next-PHI ID enumeration (both), `git remote get-url origin` for source-project capture (both). None of these go through the daemon, none are migrated to MCP.
- **PHI banner stripping** — oracle-preclear and oracle-debate strip `<!-- ORACLE ARTIFACT -->` banner from bank content before retain (filesystem-only safeguard). MCP server is a pure relay; banner-strip stays in skill bodies.

**Critical preserved invariants:**

1. **Write-ordering in oracle-preclear and oracle-debate** — retain PHI to the bank **before** writing the canonical file (oracle-preclear SKILL.md line 19). A mid-run auto-compact that interrupts between bank-retain and file-write orphans only the regenerable file copy, never the canonical bank record. **MCP migration must preserve this ordering** — call `hindsight_retain_phi` first, then `Write` the canonical file. Implementation must not reorder for "simpler control flow."

2. **Path anchoring for canonical PHI files** — `Write` calls for `${HINDSIGHT_ROOT}/.decisions/phi/PHI-NNN-{slug}.md` must resolve against `$HINDSIGHT_ROOT` (or `$HOME/Developer/Hindsight` fallback), **never** `$(pwd)` and never a relative path. PHI-006 was this exact bug: a PHI file landed in a consumer project's tree because the resolver used CWD. Skill bodies already enforce this; MCP migration must not introduce a regression. The same anchor applies to `hindsight_log_query`'s write target (above).

**Error-handling pattern change:** today, skills catch `urllib.error.URLError` / curl connection errors and surface daemon-start instructions. With MCP, errors come back as MCP tool error responses. Skill bodies need to handle that error pattern instead — same user-facing message, different error-detection mechanism.

**Shell-escape mitigation pattern vanishes:** `/oracle`, `/oracle-observe`, and `/oracle-synthesize` currently use a two-step Write-then-Read dance (`Write` user input to `/tmp/oracle_*.txt`, then `python3 -c` reads it via `open()`) to avoid bash interpolation of shell-special characters in user input. With typed MCP args, this entire pattern is unnecessary — input goes straight from skill prompt to MCP tool arg. ~30 lines of skill-body machinery disappears across these three skills.

## Migration sequencing — atomic single commit

The landing commit includes:

1. New MCP server in `~/Developer/Hindsight/` (exact location deferred to plan time per Plan-time deferrals below — likely `mcp/` or `scripts/mcp_server.py`)
2. `.mcp.json` registration in repo root
3. All 5 SKILL.md rewrites
4. `~/.claude/settings.json` edits:
   - **Remove** `Bash(python3 -c "import json, urllib.request*)`
   - **Remove** `Bash(curl * localhost:9077*)`
   - **Add** 7 user-level grants for `mcp__hindsight__*` tools

Atomic because phased migration would leave the python3-c pattern in place during a soak window — exactly the drift dynamic PHI-019 warns about. Atomic is acceptable because failure mode is "oracle skills broken until user pulls" — a single-user personal tool, low blast radius.

**Rollback gap (worth naming):** `git revert` on the landing commit restores skill files and the MCP server, but does **not** restore `~/.claude/settings.json` (user-level, not repo-tracked). A revert leaves skills calling MCP tools that aren't registered (because `.mcp.json` reverts) AND leaves the old `Bash(python3 -c "import json, urllib.request*)` allowlist entry removed. Rollback procedure must be: (1) `git revert` the Hindsight commit, (2) manually restore the two removed allowlist entries in `~/.claude/settings.json`, (3) remove the 7 added `mcp__hindsight__*` allowlist entries. Document this as a runbook step in the LOG that lands with the migration.

## Risk register

### Risk 1 — Recall-becomes-write drift

`hindsight_recall` is auto-approved on the basis that current daemon behavior makes it a pure read of pre-existing index state. If the daemon later adds query-time logging, server-side reranking with LLM calls, or any side-effect-having middleware, "recall" silently becomes a write.

**Mitigation:** the auto-approve is conditional on recall remaining a pure read. Revisit on any daemon API change. Captured in this spec; ADR amendment required if behavior changes.

### Risk 2 — MCP server as privileged proxy

Tool-level grants only constrain the *Claude → MCP* boundary. The MCP server itself can do anything to the daemon (full HTTP API access). `recall`'s read-only-ness must be enforced *inside the MCP server*, not just trusted from the daemon.

**Mitigation:** each MCP tool implementation calls only its narrow daemon endpoint. No generic passthrough tool ships. Each new tool requires an ADR amendment naming its risk class.

### Risk 3 — Daemon endpoint additions

If the daemon adds a new endpoint (delete, admin, reindex), the MCP server doesn't auto-expose it, but a future maintainer might add a tool for it without re-running this risk analysis.

**Mitigation:** documented rule — each new MCP tool requires an ADR amendment naming its risk class, not just the precedent of existing tools. Risk classes used by this spec: *read-of-pre-existing-state* (auto-approve safe), *append-to-canonical-bank* (auto-approve only if write boundary is well-defined and recoverable), *side-effect-having-middleware* (always re-evaluate). New tools that don't fit one of these need a class definition added.

## Plan-time deferrals

The following decisions are explicitly deferred to writing-plans + `mcp-server-dev:build-mcp-server`:

1. **MCP transport** — stdio vs HTTP vs SSE
2. **Server runtime** — Python (matches daemon stack, official `mcp` Python SDK + FastMCP confirmed available) vs Node
3. **Server home in repo** — `mcp/` vs `scripts/mcp_server.py` vs plugin distribution path
4. **`.mcp.json` distribution** — checked into Hindsight repo for auto-registration vs user-level `~/.claude/mcp_servers/`
5. **`hindsight_log_query` boundary** — implement as daemon endpoint (cleaner architecture, couples log writing to daemon) or as a script the MCP server invokes (simpler, matches today's `log_oracle_query.py`)

## Plan-time verifications

These are facts that need confirmation during implementation, not design decisions:

1. **MCP grant auto-promotion behavior** — Claude Code documentation does not specify whether MCP tool grants face the same auto-allowlist promotion mechanism that OBS-012 documented for `Bash(curl *)`. Vendor-policy precondition check (PHI-017): test by approving `mcp__hindsight__retain_phi` once via prompt, then check whether it appears as a permanent allowlist entry. Forward-compatibility check only — current policy auto-approves all 7 tools, so promotion is benign today.

2. **Synthesis subagent prompt compatibility with slim recall shape** — `/oracle` and `/oracle-synthesize` dispatch Sonnet subagents (per CDR-subscription-llm-routing.md) and feed them the recall result as JSON in the prompt body. Today's subagent prompts assume the verbose daemon shape with scores. After MCP migration, recall returns the slim shape by default. Plan-time check: review the synthesis brief templates in both skills and confirm they reference only fields present in the slim shape (`text`, `type`, `document_id`, `mentioned_at`, `metadata`), not `score` or rank metadata. If they reference verbose-only fields, either pass `verbose: true` from the skill or update the brief.

## Decision-record artifacts to land

- **ADR** — "Hindsight ships an MCP server as the integration boundary for Claude-Code-driven oracle skills"
- **CDR** — Tool taxonomy, slim-by-default recall, `hindsight_log_query` boundary choice (after plan-time decision)
- **LOG** — Migration execution record (skill edits, allowlist diff, verification steps)
- **PHI candidate** — "Permission integrations for typed protocols (MCP) avoid the drift dynamics PHI-019 describes for bash allowlists" — generalization with the C decision as concrete grounding

## References

- **Workstream doc:** `~/.workstream/oracle-skills-permission-scope.md` (B-vs-C debate, retraction of D, full session history)
- **Subscription-LLM routing:** `.claude/.decisions/CDR-subscription-llm-routing.md` (synthesis subagent dispatch, unchanged)
- **Decision oracle architecture:** `.claude/.decisions/DECISION_ORACLE.md`
- **PHI-019** — Capability allowlists drift toward over-permissive baselines (motivates choosing C over B)
- **OBS-012** — Live evidence of auto-allowlist re-introduction during prune (motivates the C decision; informs the auto-approve-MCP rationale by demonstrating bash-allowlist drift specifically)
- **PHI-007** — Extract shared spec, not shared implementation (informs slim-at-MCP boundary choice)
- **PHI-001** — Stateless, independent system design (preserved: daemon stays the state-holder, MCP server is a thin adapter)
