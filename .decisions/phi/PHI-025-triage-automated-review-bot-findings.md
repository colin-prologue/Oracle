<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-025 — Triage Automated Review-Bot Findings Before Acting

**Date:** 2026-06-07
**Domain:** process
**Source Project:** mini-fax
**Source:** Two PR review bot (chatgpt-codex) comments on mini-fax PR #6 — both substantive, both addressable inline, both pointed to admitted-TODO stubs that PR 4 missed. User explicitly framed the triage rule: "If substance and an easy fix, go ahead. If architectural implications or uncertain, ask."

### Philosophy
Automated code-review findings vary widely in substance. Before either implementing or dismissing a bot-surfaced finding, triage into: (a) substance + easy fix → implement, (b) substance + architectural implications → stop and ask the user, (c) style/preference → dismiss with one-line rationale. Treat each finding as an independent claim about a real architectural gap until proven otherwise.

### Why I Hold This
The default of "implement everything the bot says" rewards bot noise and erodes signal/cost ratio over time. The default of "ignore the bot" misses real admitted-stub gaps that human review missed (PR 4's printer_state hardcoded "Ok" with a "PR 4 sources real state" TODO that PR 4 never filled — a bot caught it). Both extremes are bad; the triage rule turns variable-quality input into proportional output. Substance is recognizable by concrete tells: the finding cites an admitted-TODO comment, an unwired contract field, a missing rejection-path in NVS, an existing enum value not wired into an existing code path.

### Where It Applies
Any project with automated review bots in the PR pipeline (Codex, Sonar, Snyk, security scanners, LLM-based reviewers). Also applies to manual reviewer comments where the agent is acting as the implementer. The triage shape transfers cleanly across CI tooling.

### Known Tensions
For bots that produce mostly noise, the triage cost approaches "read every comment carefully" which itself becomes burdensome — a tax that may not be worth paying for a low-signal bot. The instinct can leak into excessive deference: when the bot flags a real bug AND a style preference, the agent may implement both and call it "addressing the comment." Watch for: did the diff change behavior or just appearance? When uncertain about the architectural-implications cutoff, defer to the user.

### Open to Revision When
- A bot with consistently high signal-to-noise ratio emerges where "implement all" becomes the right default.
- A bot whose findings are reliably style-preference-only — at which point "dismiss all with rationale" becomes acceptable.
- The user's stated preference for triage shifts (e.g., "I want every bot suggestion implemented automatically").
