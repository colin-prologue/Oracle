<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-002 — Persistence layers must outlive their consumers

**Date:** 2026-04-13
**Domain:** infrastructure, architecture
**Source Project:** hindsight
**Source:** CDR-005 — daemon lifecycle moved to macOS LaunchAgent

### Philosophy
Never tie the lifecycle of a storage or memory system to the session or process that uses it. A persistence layer that starts and stops with its consumer accumulates stale state, loses work on interruption, and compounds problems across restarts.

### Why I Hold This
The Hindsight plugin's session-scoped daemon model caused stale retain tasks to accumulate whenever a session ended before retain completed. On restart, these tasks compounded with the new session's batch, saturating the Haiku API rate limit and blocking reflect queries. The root cause wasn't the rate limit — it was that a memory system designed to persist across time was being managed as if it were a session artifact.

### Where It Applies
Any system where writes outlast the session that triggers them: memory servers, queues, embedded databases, log collectors. If the data is meant to survive a session, the process managing it should too. LaunchAgent, systemd, or equivalent — pick the right lifecycle manager for the platform.

### Known Tensions
Session-scoped startup is simpler to set up and easier to reason about during development. Persistent daemons require more upfront config and platform-specific lifecycle tooling (launchd, systemd, Docker). The added setup cost is real but one-time; the stale-state problem compounds indefinitely.

### Open to Revision When
The storage system has native crash recovery and task durability guarantees that make mid-session interruption safe — e.g., if the daemon's task queue became durable and self-healing across restarts without manual lifecycle management.
