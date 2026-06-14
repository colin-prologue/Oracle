<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-033 — Workspace isolation before concurrent sessions

**Date:** 2026-06-12
**Domain:** process
**Source Project:** Oracle
**Source:** A spawned secondary session operated in the same Hindsight checkout as the primary oracle session — merged a PR, advanced main, removed a worktree — and avoided conflict only by accident.

### Philosophy
Concurrent agent sessions require workspace isolation (a dedicated worktree) by default. A shared working tree is owned by one primary session; secondary sessions may write to it only through surfaces designed for concurrent access (append-only daemon-mediated logs, clean-gated operations).

### Why I Hold This
Shared-tree safety that depends on the accidental shape of the writes is not safety. When two sessions overlap in one checkout, the failure mode is silent — one session changes git state under the other's feet, and neither errors. Isolation, like verification (PHI-030), is a precondition you provision before granting concurrency, not after the first collision.

### Evidence
- OBS-018 — two concurrent sessions shared the Hindsight checkout on 2026-06-12; safe only by structural luck (supports)
- OBS-014 — pre-dispatch state snapshot for delegated-action auditing: same instinct, observable state before concurrent/delegated mutation (supports)

### Where It Applies
Any multi-session or multi-agent workflow touching a shared repo: spawned background tasks, parallel subagents, scheduled jobs, CI bots running alongside interactive sessions.

### Known Tensions
Worktree provisioning has real overhead for tiny read-only tasks; forcing isolation on pure readers is ceremony. Some shared state (daemon-mediated query logs) is intentionally tree-global and concurrency-safe by design — the rule targets git mutations, not all writes.

### Open to Revision When
Session tooling makes shared-tree concurrency safe by construction (e.g., automatic per-session worktrees, or git-level session locking), at which point the manual isolation discipline becomes redundant.
