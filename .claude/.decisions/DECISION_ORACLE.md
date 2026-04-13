# Decision Oracle — Architecture & SpecKit Implementation Guide

## What This Is

The Decision Oracle is a persistent memory layer that models Colin's historical decision-making
patterns and surfaces them automatically during development sessions. It is not a chat log or
a document store — it is a reasoning system that learns *how* decisions get made, not just
*what* was decided.

The oracle is built on **Hindsight** (MIT-licensed, open source) and extends it with three
structured capture layers: ADRs (Architecture Decision Records), CDRs (Coding Decision Records),
and Session Logs. These layers feed the oracle's memory banks and are queryable during spec
elaboration, code review, or implementation planning.

---

## Core Concept

Every SpecKit spec elaboration involves decisions. The oracle closes the loop:

- **Before elaboration** — auto-recall surfaces relevant prior decisions into Claude's context
- **During elaboration** — `/oracle [question]` queries the oracle at explicit decision points
- **After approval** — CDR capture records the confirmed decision as a structured entry
- **Over time** — Hindsight's Observation layer synthesizes patterns across entries,
  building a living model of Colin's decision style that improves with each session

The oracle does not replace SpecKit's reasoning. It grounds it in project-specific history.

---

## Technology Stack

### Hindsight (Primary Layer)

**Repo:** https://github.com/vectorize-io/hindsight
**License:** MIT

Hindsight organizes memory into four networks:

| Network | Purpose | Oracle Use |
|---|---|---|
| **World** | Objective facts | Project constraints, tech stack, non-negotiables |
| **Experiences** | Agent interactions | Session outcomes, rejected approaches, debugging results |
| **Observations** | Auto-synthesized patterns | Decision style model, recurring tradeoffs |
| **Mental Models** | Living documents | Decision Constitution, domain playbooks |

The three operations are:

- `retain` — store a new memory (CDR/ADR capture calls this)
- `recall` — semantic + keyword + graph + temporal search (auto-injected before every prompt)
- `reflect` — synthesize across memories to answer a question (oracle query calls this)

### Claude Code Integration

Hindsight ships a native Claude Code plugin (`hindsight-integrations/claude-code`) that wires
into Claude Code's hook system. It is **not an MCP server** — it is a plugin that runs Python
scripts on hook events.

| Hook Event | Script | Purpose |
|---|---|---|
| `SessionStart` | `session_start.py` | Health check — verify Hindsight is reachable |
| `UserPromptSubmit` | `recall.py` | **Auto-recall** — query oracle bank, inject as invisible context |
| `Stop` | `retain.py` | **Auto-retain** — extract transcript, POST to Hindsight (async) |
| `SessionEnd` | `session_end.py` | Cleanup — stop auto-managed daemon if started |

Auto-recall and auto-retain are handled entirely by the plugin. No custom hook code is needed
for these operations.

### What Is NOT Needed

**Graphiti** (Zep) is not required. It provides a temporal knowledge graph useful for
relational queries across entities, but Hindsight's Observation layer covers the decision
pattern modeling use case with less infrastructure overhead. Add Graphiti later only if
explicit graph traversal queries become necessary (e.g. "show all decisions influenced by
constraint X").

**Serena** is not part of the oracle stack. It is a separate tool for LSP-backed code
navigation and token optimization within a single project session. It does not help with
cross-session memory.

---

## Installation

### Prerequisites

- Docker (recommended) or `uvx` (via `pip install uv`) for the Hindsight server
- An LLM API key (Anthropic, OpenAI, Gemini, Groq, or Ollama for local)

### Step 1 — Run the Hindsight Server

**Docker (recommended — persistent volume ensures memory survives restarts):**

```bash
export ANTHROPIC_API_KEY=sk-ant-xxx

docker run --rm -it --pull always \
  -p 8888:8888 \
  -p 9999:9999 \
  -e HINDSIGHT_API_LLM_PROVIDER=anthropic \
  -e HINDSIGHT_API_LLM_API_KEY=$ANTHROPIC_API_KEY \
  -v $HOME/.hindsight-oracle:/home/hindsight/.pg0 \
  ghcr.io/vectorize-io/hindsight:latest

# API: http://localhost:8888
# UI:  http://localhost:9999
```

The volume mount at `$HOME/.hindsight-oracle` is critical — this is what persists memory
across container restarts. Without it, every restart is a cold start.

**Alternative — local daemon (auto-managed by plugin via uvx):**

Skip the Docker step. The plugin will start and stop `hindsight-embed` automatically using
`uvx`. Requires an LLM API key set in the environment.

### Step 2 — Install the Claude Code Plugin

```bash
claude plugin marketplace add vectorize-io/hindsight
claude plugin install hindsight-memory
```

Then register the hooks (one-time setup):

```bash
/hindsight:setup
```

Restart Claude Code. You should see `[Hindsight]` log lines on the next session start.

### Step 3 — Configure the Plugin

Create `~/.hindsight/claude-code.json`:

```json
{
  "hindsightApiUrl": "http://localhost:8888",
  "bankId": "oracle",
  "bankMission": "Model Colin's architectural and coding decision patterns at Prologue Games. Prioritize tradeoffs between shipping velocity and technical debt. Surface relevant prior decisions when asked about architecture, library selection, agent orchestration, and tooling adoption.",
  "retainMission": "Extract architectural decisions, library choices, approach tradeoffs, rejected options, and the constraints that drove each decision. Capture the reasoning behind decisions, not just the outcomes.",
  "dynamicBankId": false,
  "autoRecall": true,
  "autoRetain": true,
  "retainEveryNTurns": 5,
  "debug": false
}
```

### Step 4 — Configure Bank Directives (One-Time Python Setup)

The bank's directives and reflect mission shape every oracle query. Run once after the
server is up:

```python
from hindsight_client import Hindsight

client = Hindsight(base_url="http://localhost:8888")

client.update_bank_config(
    bank_id="oracle",
    reflect_mission="""
        Model Colin's architectural and coding decision patterns at Prologue Games.
        Prioritize tradeoffs between shipping velocity and technical debt.
        Surface relevant prior decisions when asked about architecture, library
        selection, agent orchestration, and tooling adoption. Favor decisions that
        reflect spec-driven development principles and SpecKit methodology.
        Flag when a proposed decision contradicts established patterns.
    """,
    observations_mission="""
        Synthesize recurring patterns in Colin's decision-making across sessions.
        Identify consistent preferences, non-negotiables, and tradeoffs accepted under
        pressure vs. deliberate design choices. Build a living model of decision style.
    """,
)

client.create_mental_model(
    bank_id="oracle",
    name="Decision Constitution",
    description="""
        Colin's non-negotiables and recurring preferences:
        - Never recommend approaches explicitly rejected in past CDRs
        - Always surface the constraint that drove a prior decision, not just the outcome
        - Distinguish between decisions made under time pressure vs. deliberate design
        - Treat Unreal Engine constraints as a hard context layer for all game code decisions
        - Disposition: direct, pattern-aware, skeptical of novelty without clear justification
    """
)
```

---

## Capture Layers

### Layer 1 — CDR (Coding Decision Record)

Captures implementation-level decisions: library choices, pattern selections, approach
tradeoffs within a single feature or task.

**Schema:**

```markdown
## CDR-{id} — {title}

**Date:** {YYYY-MM-DD}
**Project:** {project name}
**Domain:** {e.g. agent-orchestration, unreal-integration, tooling}
**Session:** {spec or task reference}

### Decision
{What was decided, one sentence}

### Context
{What problem or constraint prompted this decision}

### Options Considered
- **{Option A}** — {why considered, why rejected}
- **{Option B}** — {why considered, why rejected}
- **{Chosen option}** — {why selected}

### Constraints That Applied
{Tech constraints, time pressure, team capability, prior commitments}

### Confidence
{High / Medium / Low} — {rationale}

### Revisit Trigger
{What would prompt revisiting this decision}
```

**Capture (semi-manual):**

CDR capture is intentionally semi-manual. After confirming a decision, prompt Claude to
capture it:

```
/oracle-capture [brief description of the decision]
```

Claude will draft the CDR in the schema above, confirm with you, then call:

```python
client.retain(
    bank_id="oracle",
    content=cdr_markdown,
    metadata={
        "type": "cdr",
        "project": "prologue-games",
        "domain": domain,
        "date": today,
        "confidence": confidence,
    }
)
```

The file is also written to `.decisions/cdrs/CDR-{id}.md` in the repo.

### Layer 2 — ADR (Architecture Decision Record)

Captures system-level decisions: structural choices, cross-cutting patterns, technology
bets that affect multiple features or the long-term codebase shape.

ADRs follow the same schema as CDRs but carry additional fields:

```markdown
### Scope
{Component / System / Cross-cutting}

### Affected Systems
{List of systems or components impacted}

### Reversibility
{Reversible with low cost / Reversible with high cost / Effectively irreversible}

### Status
{Proposed / Accepted / Superseded by ADR-{id}}
```

ADRs are stored as flat markdown files in `.decisions/adrs/` in the repo. The file is
the source of truth; Hindsight is the retrieval layer.

### Layer 3 — Session Log

A lightweight end-of-session summary. The plugin auto-retains conversation transcripts
via the `Stop` hook — session logs are a structured supplement for decisions and
outcomes not fully captured in the transcript.

The CLAUDE.md session-end protocol handles this:

```markdown
## Session End Protocol

At the end of every session, before closing:
1. Write a 3-5 sentence summary of what was decided, built, or resolved
2. Note any rejected approaches and why
3. Retain via: client.retain(bank_id="oracle", content=summary, metadata={"type": "session-log", ...})
```

Session logs feed the Observation layer over time — Hindsight synthesizes patterns from
them automatically.

---

## Hook Design

The plugin handles auto-recall and auto-retain. The remaining oracle-specific workflows
are triggered manually or via SpecKit integration.

### Auto-Recall (Plugin-Managed)

Fires automatically on every `UserPromptSubmit`. No configuration needed beyond the
plugin settings in `~/.hindsight/claude-code.json`. Relevant prior decisions from the
oracle bank are injected as invisible context before Claude sees your prompt.

### Oracle Query — `/oracle`

For explicit decision-point queries during spec elaboration:

```
/oracle "Should we use a message queue or direct RPC for the agent coordinator?"
```

This calls `reflect` on the oracle bank. Add this as a CLAUDE.md instruction or a
custom skill once SpecKit is installed.

Underlying call:
```python
client.reflect(bank_id="oracle", query=question)
```

### CDR Capture — `/oracle-capture`

Fires after a spec decision is confirmed. Semi-manual by design — fully automatic capture
risks low-quality entries. The slash command prompts for structured input:

```
/oracle-capture "Chose Hindsight over Graphiti for oracle layer"
```

Claude drafts the CDR in the schema above, awaits confirmation, then retains it.

### SpecKit Integration (Post-Install)

After SpecKit is installed, wire the oracle into the spec elaboration workflow:

- **Pre-elaboration:** auto-recall is already active via the plugin
- **Decision points:** add `/oracle` invocation to the SpecKit elaboration prompt
- **Post-approval:** add `/oracle-capture` invocation to the spec approval workflow

The specific hook points will depend on SpecKit's extension API.

---

## Querying the Oracle

### Explicit oracle query (reflect)
```
/oracle "What patterns do I use for multi-agent coordination?"
```

### Recall a specific prior decision
```python
client.recall(bank_id="oracle", query="Redis caching rejection")
```

### List mental models
```python
client.list_mental_models(bank_id="oracle")
```

### Refresh the Decision Constitution
```python
client.create_mental_model(
    bank_id="oracle",
    name="Prologue Architecture Principles",
    description="Synthesize my recurring architectural preferences and non-negotiables"
)
```

---

## File Structure

```
.decisions/
  adrs/
    ADR-001-agent-orchestration-pattern.md
    ADR-002-mcp-server-hosting.md
    ...
  cdrs/
    CDR-001-speckit-memory-layer.md
    CDR-002-hindsight-vs-graphiti.md
    ...
  logs/
    2026-04-09-session.md
    ...
  DECISION_ORACLE.md          ← this file
  DECISION_CONSTITUTION.md    ← bank mission/directives in human-readable form
```

The `.decisions/` folder is committed to the repo. Hindsight is the retrieval and
synthesis layer on top of it — the files are the canonical record, Hindsight is what
makes them queryable at speed.

---

## Roadmap

### Phase 1 — Foundation
- [ ] Hindsight running locally with persistent Docker volume
- [ ] Claude Code plugin installed and hooks registered (`/hindsight:setup`)
- [ ] Bank configured with initial Decision Constitution (`update_bank_config`)
- [ ] First 5 CDRs captured manually to seed the oracle

### Phase 2 — Hook Integration ✓ Complete (2026-04-12)
- [x] `/oracle` slash command wired as a custom Claude Code skill (`.claude/skills/oracle/SKILL.md`)
- [x] `/oracle-capture` slash command wired for CDR capture (`.claude/skills/oracle-capture/SKILL.md`)
- [x] SpecKit elaboration prompt updated to invoke `/oracle` at decision points (step 5a)
- [x] SpecKit approval workflow updated to invoke `/oracle-capture` (step 8 reminder)
- [x] Session end protocol in `CLAUDE.md`

### Phase 3 — Pattern Modeling
- [ ] First mental models created from accumulated CDRs/ADRs
- [ ] Observation layer reviewed and curated
- [ ] Decision Constitution updated based on synthesized patterns

### Phase 4 — External Hosting *(future — build toward)*
- [ ] Expose oracle over a stable public URL so Claude.ai cloud sessions can reach it
- [ ] Evaluate hosting options: Hindsight Cloud vs. self-hosted VPS vs. Fly.io/Railway
- [ ] Migrate local PostgreSQL data to the hosted instance without losing CDR/ADR history
- [ ] Secure the endpoint (API key auth or IP allowlist) — oracle contains architectural patterns worth protecting
- [ ] Update `~/.hindsight/claude-code.json` `hindsightApiUrl` to point to remote instance
- [ ] Retire the LaunchAgent once the remote instance is stable (or keep it as a local fallback)

> **Why**: Local daemon means oracle is only available from this machine and only in Claude Code CLI.
> Moving to an external host unlocks oracle access from claude.ai, mobile, and any future context
> where decisions need to be surfaced. The data model doesn't change — only the hosting boundary.
>
> **Prerequisite**: Enough CDRs/ADRs accumulated (Phase 3 complete) to make the oracle worth
> exposing. Don't migrate an empty bank.

### Phase 5 — Team Extension *(future)*
- [ ] Evaluate multi-user bank setup for Prologue team decisions
- [ ] Consider Hindsight Cloud for shared access without self-hosting overhead

---

## Key Decisions Already Made

**Hindsight over Graphiti for oracle layer** — Hindsight's Observation and Mental Model
layers cover the decision pattern modeling use case. Graphiti's relational graph queries
are not needed at this stage and would add infrastructure complexity without clear benefit.

**Hindsight over Serena for memory** — Serena's memory is project-scoped and codebase-
focused. The oracle needs to be person-scoped and decision-focused. These are different
tools solving different problems and are not in conflict.

**Plugin over MCP for Claude Code integration** — Hindsight integrates as a Claude Code
plugin using native hook events, not as an MCP server. Auto-recall and auto-retain are
handled by the plugin; the oracle is a bank configuration, not a separate service.

**CDR capture is semi-manual by design** — fully automatic capture risks low-quality
entries. The `/oracle-capture` command prompts for structured input rather than auto-
generating CDRs from session transcripts. Quality of oracle reasoning depends on quality
of input.

**Files as canonical record, Hindsight as retrieval** — ADRs and CDRs live as committed
markdown files. Hindsight is not the source of truth, it is the query interface. This
avoids lock-in and keeps decisions auditable in git history.
