# CDR — Routing Oracle LLM Calls Through CC Subscription

**Status:** Investigation complete — design proposed
**Branch:** `008-subscription-llm-routing`
**Date:** 2026-04-25

## Problem

Oracle skills today call the hindsight-embed daemon's `/reflect` endpoint. The
daemon performs both retrieval and LLM synthesis; synthesis runs against the
Anthropic API using a personal API key, billed per-token outside the user's
Claude Code subscription.

We want reflect synthesis to consume CC subscription tokens when the call
originates from an active CC session, so day-to-day oracle use stops drawing
on paid API credit.

## Hard Constraint (from prior burn — PHI-001)

Background services must be stateless and session-independent. A previous
attempt routed daemon-side synthesis through the calling session's Agent SDK
(`claude-code` provider) and produced cascading process spawns, macOS crash
dialogs, and port-binding collisions. **Hindsight upstream has since
deliberately excluded the `claude-code` provider option from the
configuration wizard as a safeguard** (corroborated in oracle bank).

Implication: no design that mutates the daemon's LLM provider is acceptable.

## Verified Facts

| Question | Answer | Evidence |
|---|---|---|
| Does the daemon expose a retrieval-only endpoint? | **Yes** — `POST /v1/default/banks/{bank_id}/memories/recall` returns chunks + entities by semantic similarity with no LLM call. | OpenAPI schema at `localhost:9077/openapi.json`; live-probed with sample query. |
| Are there any non-interactive `/reflect` callers? | **None.** The only `/reflect` callers in this repo are the four oracle skills (`oracle`, `oracle-debate`, `oracle-observe`, `oracle-synthesize`, plus a fit-check call in `oracle-preclear`). The `UserPromptSubmit` hook calls `/recall` (already retrieval-only); the `Stop` hook calls `/retain` (write path). No cron entries. | `rg -n reflect` across `.claude/skills/`; `~/.claude/settings.json` hook commands; `crontab -l`. |
| Do any skills use `response_schema` / structured output from reflect? | **No.** All call sites consume the markdown `text` field. Parity is straightforward. | `rg response_schema` returns no skill hits. |
| Is the daemon's API-key path safely revertable? | **Daemon untouched in this design.** API key remains in `~/.hindsight/profiles/claude-code.env` (`HINDSIGHT_API_LLM_PROVIDER=anthropic`, `HINDSIGHT_API_LLM_API_KEY=sk-ant-…`). `/reflect` continues to work for any external caller. Rollback = revert skill files. | Inspected `~/.hindsight/profiles/claude-code.env`; launchd plist shows `-p claude-code` profile; no daemon mutation in proposed design. |

## Proposed Design

**Each oracle skill calls `/recall` for retrieval, then dispatches a synthesis
subagent pinned to Sonnet via the `Agent` tool's `model: "sonnet"` parameter.**

- Daemon: unchanged.
- Skills: replace the curl payload from `{"query": ..., "budget": ...}` →
  `/reflect` with `{"query": ..., "limit": N, "include": {...}}` →
  `/recall`. Pass the recall results plus a self-contained synthesis prompt
  to a subagent via the `Agent` tool with `subagent_type: "general-purpose"`,
  `model: "sonnet"`. Subagent returns the synthesized markdown; skill
  renders it.
- Synthesis runs on subscription tokens at Sonnet 4.6 quality (vs. daemon's
  current haiku-3).

## PHI-001 Alignment

PHI-001 governs background services. The design respects it:

- **Daemon stays session-independent.** It still uses its API key for any
  external `/reflect` caller and never reaches into a session's auth.
- **The new LLM call lives entirely inside the calling session.** Subagent
  dispatch is a child of the session — same auth context as the parent —
  not a background service contending with it. No nested SDK loops, no
  daemon-side calls back into the session.
- The two auth contexts (daemon's API key, session's subscription) remain
  disjoint. This is *more* PHI-001-aligned than the status quo, where the
  daemon was at least handling auth on the user's behalf for an in-session
  trigger.

**Candidate synthesis input (defer):** this work surfaces a possible
complement to PHI-001 — "auth-context ownership symmetry: daemons own API
keys for autonomous work, sessions own subscription tokens for ephemeral
work; neither side crosses the boundary." One instance only; per
resist-premature-generalization rule, do not articulate as a new PHI yet.
A future `/oracle-synthesize` pass should pick this up if a second
instance appears.

## Weakest Point

**Subagents have cold context — every synthesis call resends the recall
results and the synthesis prompt.** For typical oracle queries that's a
few thousand input tokens at Sonnet rates per call. Cheap in absolute
terms but worth measuring after the first skill is converted; if average
input tokens balloon (e.g., when `oracle-synthesize` retrieves 30+ chunks),
re-evaluate whether the budget warrants downshifting to Haiku for that one
skill.

A second-order concern: since each skill writes its own subagent brief,
prompt drift across the four skills is now a maintenance surface. We hold
off on extracting a shared synthesis prompt until the second skill is
converted (avoiding premature DRY).

## Other Considerations

- `oracle-preclear` runs a low-budget reflect to dedupe candidates against
  what's already captured. With `/recall` this becomes a similarity check on
  the candidate text; arguably *better* fit than reflect for that use case.
- `oracle-synthesize` is the heaviest reflect user (the "synthesize a new
  observation across the corpus" path). This is where the model upgrade
  matters most — and where the subscription-token cost shows up most.
- We will likely want a small shared synthesis prompt under
  `.claude/skills/_shared/oracle-synthesis.md` so the four skills don't
  drift on phrasing. (Defer until at least two skills are converted; resist
  premature DRY.)

## Implementation Sketch

1. Convert `.claude/skills/oracle/SKILL.md` first (smallest, most-used) —
   `/reflect` → `/recall` + Sonnet subagent synthesis. Validate output
   against current behavior on 2–3 representative questions.
2. Convert `oracle-preclear` (fit-check use case — lower bar).
3. Convert `oracle-observe` (also fit-check).
4. Convert `oracle-synthesize` (heaviest; prompt parity matters most here).
5. Once two skills share near-identical synthesis text, evaluate extracting
   to `.claude/skills/_shared/oracle-synthesis.md`.
6. No daemon changes. No env-var changes. No launchd reload.

## Rollback

Revert the skill files. Daemon's `/reflect` path is intact and functional
on `main` and continues to be served by the running daemon throughout —
nothing to restart, no credential to restore.

## Decision Log

- 2026-04-25 — Draft created.
- 2026-04-25 — Investigation closed all four open questions. Design
  simplified: daemon stays untouched, only skills change. Original
  framing's "dual-path drift trap" risk is moot because no non-interactive
  `/reflect` callers exist.
