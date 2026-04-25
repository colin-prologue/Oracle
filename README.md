# Hindsight — Decision Oracle

A local, persistent memory layer that monitors decision-making across all active projects and surfaces recurring patterns of judgment before you repeat a mistake or reinvent a tradeoff you've already worked through.

---

## What This Is

Most developer knowledge systems store *what was decided*. This stores *how decisions get made* — the recurring philosophies, instincts, and patterns that apply regardless of which project you're in.

The oracle is not a journal, a chat log, or a project ADR store. It is a reasoning system that accumulates your decision-making style over time and surfaces it at the moment you need it.

Two artifacts live here:

| Artifact | ID | What it is |
|---|---|---|
| **Philosophy** | PHI-NNN | A cross-project held opinion — prescriptive, debatable, not project-scoped |
| **Observation** | OBS-NNN | A synthesized pattern extracted from accumulated PHIs and session logs — descriptive |

The strict separation: **project-specific decisions stay in each project's own knowledge base.** ADRs and implementation choices belong there. The oracle only holds what would change your default approach in a brand new project with no prior context.

If the answer to "Would this apply to any project I work on?" is yes → PHI. If no → ADR in the project KB.

---

## Why It Exists

You work across multiple projects simultaneously. Lessons learned under pressure in one project often fail to surface when a similar decision comes up six weeks later in a different context. By the time you recognize the pattern, you've already committed to an approach.

The oracle closes that loop:

- **Before a decision** — auto-recall injects relevant PHIs and OBSs into your Claude session context
- **At a decision point** — `/oracle "[question]"` runs a targeted reflect query to surface applicable patterns
- **When a new pattern emerges** — `/oracle-debate` or `/oracle-observe` captures it before the session ends
- **Periodically** — `/oracle-synthesize` synthesizes new OBSs from accumulated session logs and PHIs

---

## How It Works

The oracle is built on [Hindsight](https://github.com/vectorize-io/hindsight), a local memory daemon that provides semantic recall and synthesis across retained memories. It integrates with Claude Code via the native plugin hook system — not an MCP server.

```
Session starts
  → plugin auto-recalls relevant PHIs/OBSs into context

During session
  → /oracle [question]     query at explicit decision points
  → /oracle-debate         capture a new philosophy (PHI)
  → /oracle-observe        capture an impromptu observation (OBS)

Session ends
  → manual session summary retained to oracle bank
  → /oracle-synthesize     periodic synthesis (run occasionally, not every session)
```

Retention is deliberate. `autoRetain` is disabled — the bank fills with noise faster than reflection can surface patterns when every exchange is retained automatically. Every entry in the oracle earned its place.

---

## Setup

### Prerequisites

- `uv` installed (`pip install uv`)
- An Anthropic API key (key-based; not `claude-code` session auth — see PHI-001)

### 1. Start the daemon

```bash
HINDSIGHT_API_EMBEDDINGS_LOCAL_FORCE_CPU=1 \
HINDSIGHT_API_RERANKER_LOCAL_FORCE_CPU=1 \
uvx hindsight-embed daemon start
```

The daemon runs on `http://localhost:9077`. It is managed as a macOS LaunchAgent (`com.hindsight.daemon`) so it outlives individual sessions — the oracle bank must survive session interruption (PHI-002).

### 2. Install the Claude Code plugin

```bash
claude plugin marketplace add vectorize-io/hindsight
claude plugin install hindsight-memory
/hindsight:setup
```

### 3. Configure the plugin

`~/.hindsight/claude-code.json`:

```json
{
  "hindsightApiUrl": "http://localhost:9077",
  "bankId": "oracle",
  "bankMission": "Model cross-project decision-making philosophies and patterns. Surface PHIs and OBSs relevant to current decisions. Do not store project-specific decisions — those belong in each project's knowledge base.",
  "retainMission": "Extract cross-project philosophies, recurring patterns, and meta-reasoning about how decisions get made. Ignore project-specific implementation choices.",
  "dynamicBankId": false,
  "autoRecall": true,
  "autoRetain": false
}
```

---

## Daily Usage

### Query the oracle at a decision point

```
/oracle "Should I wire this as a daemon or a session-scoped process?"
```

Runs a `reflect` query across the oracle bank and surfaces applicable PHIs and OBSs.

### Capture a new philosophy

```
/oracle-debate "Persistence layers must outlive their consumers"
```

Drafts a PHI from session context, debates it with you, then retains on confirmation. Files written to `.decisions/phi/`. The debate step is not optional — philosophies that don't survive challenge aren't worth retaining.

### Capture an impromptu observation

```
/oracle-observe "Every time we pick autoRetain, signal quality degrades within two weeks"
```

Runs a fit-check reflect first (to find related PHIs/OBSs), then retains the observation as OBS-NNN.

### Periodic synthesis

```
/oracle-synthesize
```

Reflect across the full corpus to surface patterns not yet captured as OBSs. Run occasionally — after a dense decision period, or when starting a new project phase. Not every session.

### End-of-session protocol

At session end, retain a 3–5 sentence summary covering what was decided, what was rejected and why, and anything that would have been useful to know at the start. Full protocol in `CLAUDE.md`.

---

## File Structure

```
.decisions/
  phi/
    PHI-001-background-services-must-be-stateless.md
    PHI-002-persistence-layers-outlive-consumers.md
    PHI-003-prefer-conscious-capture-over-automatic-retention.md
    ...
  DECISION_ORACLE.md          ← architecture & implementation guide
  DECISION_CONSTITUTION.md    ← bank mission/directives in human-readable form

.claude/skills/
  oracle/                     ← /oracle query skill
  oracle-debate/              ← /oracle-debate PHI capture skill
  oracle-observe/             ← /oracle-observe OBS capture skill
  oracle-synthesize/          ← /oracle-synthesize periodic synthesis skill
```

PHI files are committed to this repo — git history is the auditable record. Hindsight is not the source of truth; it is the query interface.

---

## Governing Philosophies

**PHI-001 — Background services must be stateless and session-independent**
Daemons must authenticate via durable, key-based credentials — not via the calling session's active auth context.

**PHI-002 — Persistence layers must outlive their consumers**
Never tie the lifecycle of a storage or memory system to the session or process that uses it.

**PHI-003 — Prefer conscious capture over automatic retention**
Only retain what you consciously choose to retain. Automatic high-frequency retention degrades signal quality.

Full philosophy rationale in `.decisions/phi/`.

---

## What This Is Not

- **Not a project ADR store** — project-specific decisions belong in each project's own knowledge base
- **Not a chat log** — session logs are inputs, not the artifact; OBSs and PHIs are
- **Not a passive journal** — capture is deliberate; the oracle only holds decisions that earned entry
- **Not a replacement for thinking** — it surfaces patterns; judgment still happens in the session

---

## Roadmap

- **Phase 4** — External hosting so cloud Claude sessions (claude.ai) can reach the oracle
- **Phase 5** — ~~SpecKit integration~~ *(removed — covered by existing CLI hook events; no special integration needed)*
- **Phase 6** — Multi-user bank evaluation for team contexts

Current status and completed phases: `.decisions/DECISION_ORACLE.md`.
