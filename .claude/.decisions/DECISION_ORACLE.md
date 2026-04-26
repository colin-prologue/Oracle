# Decision Oracle — Architecture & Implementation Guide

## What This Is

The Decision Oracle is a persistent memory layer that models Colin's historical decision-making
patterns and surfaces them automatically during development sessions. It is not a chat log or
a document store — it is a reasoning system that learns *how* decisions get made, not just
*what* was decided.

The oracle is built on **Hindsight** (MIT-licensed, open source) and stores two types of artifacts:

| Artifact | ID | What it is |
|---|---|---|
| **Philosophy** | PHI-NNN | A cross-project held opinion — prescriptive, debatable, not project-scoped |
| **Observation** | OBS-NNN | A synthesized pattern noticed across decisions — descriptive |

Session logs feed both layers over time. The oracle does not store project-specific ADRs or
decisions — those belong in each project's own Knowledge Base (e.g. Claude-Root's `.specify/memory/`).

---

## Core Concept

The oracle models *meta-reasoning* — how Colin tends to decide, not what was decided in any
single project. The separation is strict:

| Layer | System | Question answered | Examples |
|---|---|---|---|
| **Oracle** | Hindsight bank | "How do I tend to decide?" | PHI: "persistence layers must outlive consumers" |
| **KB** | Project memory | "What did we decide here?" | ADR: "chose FastMCP for this project" |

A project decision that would change your default approach across all future projects → PHI.
A project decision that's ground truth for this project only → ADR in the KB.

Every SpecKit spec elaboration involves decisions. The oracle closes the loop:

- **Before elaboration** — auto-recall surfaces relevant PHIs and OBSs into Claude's context
- **During elaboration** — `/oracle [question]` queries the oracle at explicit decision points
- **Session end** — `/oracle-debate` or `/oracle-observe` if a new meta-pattern emerged
- **Over time** — `/oracle-synthesize` synthesizes OBS-NNN from accumulated PHIs and session logs

---

## Technology Stack

### Hindsight (Primary Layer)

**Repo:** https://github.com/vectorize-io/hindsight
**License:** MIT

Hindsight organizes memory into four networks:

| Network | Purpose | Oracle Use |
|---|---|---|
| **World** | Objective facts | Cross-project constraints, non-negotiables |
| **Experiences** | Agent interactions | Session outcomes, rejected approaches |
| **Observations** | Auto-synthesized patterns | Decision style model, recurring tradeoffs |
| **Mental Models** | Living documents | Decision Constitution |

The three operations are:

- `retain` — store a new memory (PHI/OBS capture calls this)
- `recall` — semantic + keyword + graph + temporal search (auto-injected before every prompt)
- `reflect` — synthesize across memories to answer a question (oracle query calls this)

### Claude Code Integration

Hindsight ships a native Claude Code plugin that wires into Claude Code's hook system.
It is **not an MCP server** — it runs Python scripts on hook events.

| Hook Event | Script | Purpose |
|---|---|---|
| `SessionStart` | `session_start.py` | Health check |
| `UserPromptSubmit` | `recall.py` | **Auto-recall** — inject relevant PHIs/OBSs before every prompt |
| `Stop` | `retain.py` | **Auto-retain** — extract transcript, POST to Hindsight (async) |
| `SessionEnd` | `session_end.py` | Cleanup |

Auto-recall and auto-retain are handled entirely by the plugin.

### What Is NOT Needed

**Graphiti** (Zep) — not required. Hindsight's Observation layer covers decision pattern
modeling with less infrastructure overhead.

**Serena** — not part of the oracle stack. It is for LSP-backed code navigation within a
single project session, not cross-session memory.

---

## Installation

### Prerequisites

- `uvx` (via `pip install uv`) for the Hindsight daemon
- An Anthropic API key (key-based, not `claude-code` — see PHI-001)

### Step 1 — Run the Hindsight Daemon

```bash
HINDSIGHT_API_EMBEDDINGS_LOCAL_FORCE_CPU=1 \
HINDSIGHT_API_RERANKER_LOCAL_FORCE_CPU=1 \
uvx hindsight-embed daemon start
```

CPU flags are required on macOS Apple Silicon (PHI-001 / ADR-002 in oracle setup history).
The daemon runs on `http://localhost:9077` and is managed as a macOS LaunchAgent
(`com.hindsight.daemon`) — it must outlive individual sessions (PHI-002).

### Step 2 — Install the Claude Code Plugin

```bash
claude plugin marketplace add vectorize-io/hindsight
claude plugin install hindsight-memory
```

Then register the hooks:

```bash
/hindsight:setup
```

### Step 3 — Configure the Plugin

Create `~/.hindsight/claude-code.json` (not `~/.claude/plugins/data/...` — that path is ignored):

```json
{
  "hindsightApiUrl": "http://localhost:9077",
  "bankId": "oracle",
  "bankMission": "Model Colin's cross-project decision-making philosophies and patterns. Surface PHIs and OBSs relevant to current decisions. Do not store project-specific decisions — those belong in each project's knowledge base.",
  "retainMission": "Extract cross-project philosophies, recurring patterns, and meta-reasoning about how decisions get made. Ignore project-specific implementation choices.",
  "dynamicBankId": false,
  "autoRecall": true,
  "autoRetain": false
}
```

`autoRetain: false` is intentional — retain only on SessionEnd, PreCompact, and explicit
`/oracle-debate` or `/oracle-observe` invocations (PHI-003).

### Step 4 — Configure Bank Directives

```python
from hindsight_client import Hindsight

client = Hindsight(base_url="http://localhost:9077")

client.update_bank_config(
    bank_id="oracle",
    reflect_mission="""
        Model Colin's cross-project decision-making philosophies and observed patterns.
        Surface PHIs and OBSs relevant to the current decision point.
        Flag when a proposed decision contradicts an established PHI.
        Do not surface project-specific ADRs — those belong in project KBs.
    """,
    observations_mission="""
        Synthesize recurring patterns in Colin's decision-making across projects and sessions.
        Identify consistent philosophies, non-negotiables, and tradeoffs accepted across contexts.
        Build a living model of decision style — not a log of individual decisions.
    """,
)
```

---

## Artifact Layers

### Layer 1 — Philosophy (PHI-NNN)

A cross-project held opinion that should govern future decisions. Prescriptive but debatable —
not a hard rule. A PHI belongs in the oracle only if it would apply regardless of which project
you're working on.

**Schema:**

```markdown
## PHI-{NNN} — {title}

**Date:** {YYYY-MM-DD}
**Domain:** {architecture, tooling, process, infrastructure}
**Source:** {what experience prompted this philosophy}

### Philosophy
{One or two sentences: the held opinion, phrased as a disposition not a rule}

### Why I Hold This
{The experience or repeated pattern that grounded this position}

### Where It Applies
{Cross-project context — when does this philosophy apply}

### Known Tensions
{What situations create legitimate pressure against this philosophy}

### Open to Revision When
{What would change your mind}
```

**Capture:** `/oracle-debate "[description]"` or, at session end, `/oracle-preclear`. Both retain to the oracle bank first (canonical), then write the file to `${HINDSIGHT_ROOT:-$HOME/Developer/Hindsight}/.decisions/phi/PHI-{NNN}-{slug}.md`. **The file always lives in the Hindsight repo — never in the consumer project's working tree**, because a PHI is cross-project by definition and putting it in a consumer project conflates oracle artifacts with local project rules. Each file opens with an `ORACLE ARTIFACT` banner so it self-identifies if ever read from an unexpected path.

**Filter:** Ask "Would this change my default in a new project with no prior context?" If yes → PHI.
If it's ground truth for this project only → ADR in the project KB.

### Layer 2 — Observation (OBS-NNN)

A synthesized pattern extracted from accumulated PHIs and session logs. Descriptive, not prescriptive.
OBSs are generated by `/oracle-synthesize` (periodic corpus synthesis) or `/oracle-observe`
(impromptu mid-session insight with fit-check reflect).

OBSs are retained to the oracle bank only; no canonical file is written to disk. The bank is
the source of truth.

### Layer 3 — Session Log

A lightweight end-of-session summary retained manually via the Session End Protocol in `CLAUDE.md`.
Session logs feed the Observation layer over time — Hindsight synthesizes patterns from them.

---

## Oracle Skills

| Skill | Purpose |
|---|---|
| `/oracle "[question]"` | Query oracle at a decision point — runs reflect on the oracle bank |
| `/oracle-debate "[philosophy]"` | Draft, debate, and retain a PHI — semi-manual by design |
| `/oracle-observe "[insight]"` | Capture impromptu observation with fit-check reflect; retains as OBS-NNN |
| `/oracle-synthesize` | Periodic synthesis: reflect across corpus, curate, retain as OBS-NNN |
| `/oracle-preclear` | End-of-session scan: proposes PHI/OBS candidates for approval, retains, writes session summary. Only retention path when using `/clear` |

---

## File Structure

```
.decisions/
  phi/
    PHI-001-background-services-must-be-stateless.md
    PHI-002-persistence-layers-outlive-consumers.md
    PHI-003-prefer-conscious-capture-over-automatic-retention.md
    ...
  DECISION_ORACLE.md          ← this file
  DECISION_CONSTITUTION.md    ← bank mission/directives in human-readable form

.claude/skills/
  oracle/           ← /oracle query skill
  oracle-debate/    ← /oracle-debate PHI capture skill
  oracle-observe/   ← /oracle-observe OBS capture skill
  oracle-synthesize/ ← /oracle-synthesize periodic synthesis skill
```

The `.decisions/phi/` folder is committed to **this** (Hindsight) repo. The oracle bank is source of truth; the files are browsable derivatives. Oracle skills resolve the PHI directory via `${HINDSIGHT_ROOT:-$HOME/Developer/Hindsight}/.decisions/phi/` so invocations from other projects still land files here, not in the caller's tree.

---

## Roadmap

### Phase 1 — Foundation ✓ Complete
- [x] Hindsight daemon running locally via uvx + LaunchAgent
- [x] Claude Code plugin installed and hooks registered
- [x] Bank configured with initial Decision Constitution
- [x] First PHIs seeded from setup experience

### Phase 2 — Hook Integration ✓ Complete (2026-04-12)
- [x] `/oracle` skill wired (`.claude/skills/oracle/SKILL.md`)
- [x] `/oracle-debate` skill wired for PHI capture (`.claude/skills/oracle-debate/SKILL.md`)
- [x] Session end protocol in `CLAUDE.md`

### Phase 3 — Pattern Modeling ✓ Complete (2026-04-14)
- [x] `/oracle-synthesize` skill written — synthesizes OBS-NNN from reflect query
- [x] `/oracle-observe` skill written — captures impromptu observations via fit-check reflect
- [x] First Observation created and curated: OBS-001 retained to oracle bank
- [x] Decision Constitution updated and written to disk at `.claude/.decisions/DECISION_CONSTITUTION.md`
- [x] Cadence query pair validated; SC-003 <30s target not met (~50s at `mid` budget with mature corpus — acceptable for non-interactive use)

### Phase 3b — Vocabulary Alignment ✓ Complete (2026-04-15)
- [x] Replaced CDR artifact type with PHI (Philosophy) — cross-project held opinions, debatable
- [x] Clarified oracle scope: meta-patterns only, no project-specific ADRs
- [x] Renamed `/oracle-capture` → `/oracle-debate`
- [x] Removed `.decisions/adrs/` and `.decisions/cdrs/` — oracle has `.decisions/phi/` only
- [x] Updated all skills to use PHI/OBS vocabulary

### Phase 4 — External Hosting *(out of scope — CLI-only by decision)*

Oracle is scoped to Claude Code CLI sessions only. Desktop app (chat, cowork, code) and
cloud/mobile sessions are explicitly excluded.

**Why:** CLI hook events (`UserPromptSubmit`, `Stop`, `SessionEnd`) provide automatic,
reliable recall/retain without any instruction-based workarounds. Desktop MCP integration
requires instruction-driven recall — a weaker, less reliable substitute. The oracle's
value comes from consistent, automatic pattern capture; partial coverage degrades that.

**Revisit when:** Claude Desktop exposes lifecycle hooks equivalent to Claude Code's
`UserPromptSubmit` / `Stop` events that MCP servers can subscribe to. Until then,
CLI-only is the right scope.

### Phase 5 — SpecKit Integration *(removed)*

Removed 2026-04-25. The original plan was to wire oracle hooks into SpecKit's
extension surface so prior PHIs would surface automatically at spec/plan/implement
decision points. That bridge is solved elsewhere — oracle and SpecKit interoperate
via the existing CLI hook events (`UserPromptSubmit` recall, `Stop`/`SessionEnd`
retain) which fire during SpecKit commands the same as any other interaction. No
SpecKit-specific integration is needed.

SpecKit remains a development tool used in this repo; nothing about that changes.

### Phase 6 — Team Extension *(future)*
- [ ] Evaluate multi-user bank setup
- [ ] Consider Hindsight Cloud for shared access without self-hosting overhead

### Phase 7 — Organic Invocation & Cross-Tool Query *(in progress, 2026-04-25)*

Goal: make oracle queries fire organically at decision moments, and extend query access to Codex sessions. Capture (debate/observe/synthesize/preclear) stays explicit per PHI-003 — this phase only touches the read path.

**In sequence:**
- [x] Rewrite `/oracle` skill `description` as a trigger condition (when to use, not what it does); add reinforcing one-liner in CLAUDE.md *(commit `de6e18c`)*
- [x] Add a relevance gate to the synthesis subagent prompt so it returns "no relevant entries" rather than padding answers from weakly-related hits *(originally planned daemon-side; hindsight-embed exposes neither per-result similarity scores nor a min_score request param, so the gate moved to the LLM-judged synthesis layer instead — see future-exploration item below for the daemon-side variant)*
- [x] Build an MCP `oracle_query` server wrapping the daemon's recall endpoint; tool description carries the same broad trigger phrasing as the CC `/oracle` skill, and the JSON response embeds the relevance-gate instruction the calling model applies. Lives at `mcp/oracle-query/server.py` (PEP 723 inline-deps Python script run via `uv`). Verified end-to-end via MCP stdio client probe — tool listing, off-topic query, and on-topic query all return well-formed responses. *(Registration in `~/.codex/config.toml` and `~/.codex/AGENTS.md` is a manual step — block documented in `mcp/oracle-query/README.md`. Codex desktop needs absolute paths + explicit `cwd` per openai/codex issue #14449.)*

**Future exploration (not yet scoped):**
- [x] **Context-threshold preclear nudge (auto-compact case)** — `PreCompact` hook with matcher `"auto"` blocks auto-compaction with a reason directing the user to run `/oracle-preclear` first, then choose `/compact` or `/clear`. Lives at `scripts/precompact_oracle_nudge.py`, registered in `.claude/settings.json`. Hook investigation confirmed `PreCompact` is the only event with token-budget data (`context_used`, `tokens_remaining`) — no early-warning threshold mechanism exists in other hook events. Manual `/clear` case remains unhookable (no hook fires before `/clear` executes); CLAUDE.md Session End Protocol stays the documentation-side mitigation. Manual `/compact` is intentionally not hooked — explicit user invocation is a deliberate choice not to second-guess.
- [x] **Keyword-triggered capture nudge** — `UserPromptSubmit` hook (`scripts/userprompt_oracle_capture_nudge.py`) pattern-matches the user's prompt against a deliberately narrow vocabulary of declarative oracle-capture intent ("worth capturing", "should be a PHI", "make this a philosophy", etc.) and emits `additionalContext` recommending `/oracle-debate` or `/oracle-observe`. Vocabulary intentionally excludes generic "remember" to avoid colliding with CLAUDE.md auto-memory's cross-conversation persistence path; nudge text also tells Claude to skip the recommendation when content is session-specific or user-personal (auto-memory's domain). Calibration depends on real session usage — narrow vocabulary errs toward false negatives over false positives per PHI-005 noise tension.
- [ ] **Daemon-side similarity floor (local fork of `hindsight-embed`)** — the synthesis-side LLM gate (shipped above) is approximate; a true similarity floor requires per-result `score` in the recall response and a `min_score` request param, neither of which `hindsight-embed` exposes today. Solo-user scope means the path is a local fork of `hindsight-embed` (point `uvx` at the fork, manage rebases on upstream releases) — not an upstream PR. Decision trigger: ship the LLM gate, gather data via the query/answer log, then evaluate whether numeric-threshold rigor justifies fork-maintenance overhead.
- [x] **Query/answer log** — JSONL append on every `/oracle` invocation (CC) and every `oracle_query` call (MCP) to `.decisions/queries/YYYY-MM.jsonl`. Empty-result queries logged too (their absence would defeat calibration). CC schema includes the synthesized answer + cited IDs; MCP schema captures available IDs (Codex-side synthesis isn't visible to the server). Two writers, two implementations — Rule of Three says don't extract a shared helper for two sites. CC delegates to `scripts/log_oracle_query.py` (avoids 30 lines of Python in skill markdown); MCP appends inline. Review via `scripts/review_oracle_queries.py [N]`. *Review ritual itself remains manual — no auto-promotion of findings into OBSes (PHI-003 / Pattern 9 autoRetain failure mode).*

---

## Key Architectural Decisions

**Oracle stores meta-patterns only, not project decisions** — Project-specific ADRs and LOGs
belong in each project's KB. The oracle's value comes from cross-project pattern recognition;
polluting it with project-specific decisions degrades reflect quality. Filter: "Would this
change my default in a new project?" If yes → PHI. If no → ADR in the KB.

**PHI not CDR** — "Coding Decision Record" implied a project artifact. "Philosophy" captures
what the oracle actually stores: cross-project held opinions, open to debate, not hard rules.

**Observation over Automation** — Oracle-observe and oracle-debate are manual invocations, not
automated hooks. Pattern recognition requires judgment. Hooks can surface reminders; invocation
stays deliberate (PHI-003).

**Hindsight over Graphiti** — Hindsight's Observation and Mental Model layers cover decision
pattern modeling. Graphiti's relational graph queries are not needed at this stage.

**Plugin over MCP** — Hindsight integrates as a Claude Code plugin using native hook events,
not as an MCP server. Auto-recall and auto-retain are handled by the plugin.

**Files as canonical record, Hindsight as retrieval** — PHI files are committed to the repo.
Hindsight is not the source of truth, it is the query interface. Avoids lock-in, keeps
decisions auditable in git history.
