## CDR-005 — Daemon lifecycle moved to macOS LaunchAgent

**Date:** 2026-04-13
**Project:** Hindsight / Decision Oracle
**Domain:** infrastructure, tooling
**Session:** Phase 2 oracle hook skills — post-implementation validation

### Decision
Manage the Hindsight daemon as a macOS LaunchAgent (`com.hindsight.daemon`) rather
than relying on the Hindsight plugin to start/stop it per Claude Code session.

### Context
CDR-004 documented a known rate-limit contention issue where retain workers exhaust
Haiku's 10k TPM budget, blocking reflect queries. The mitigation (retainEveryNTurns=10)
proved insufficient. Root cause analysis revealed the deeper problem: the plugin-managed
daemon lifecycle creates stale tasks whenever a session ends before retain completes.
These stale tasks are recovered on the next daemon start, compounding with the new
session's retain batch and saturating the Haiku API.

The session-scoped daemon model is architecturally wrong for a memory system — memory
should outlive sessions, and so should the process that manages it.

### Options Considered
- **Accept and mitigate further (CDR-004 approach)** — bump retainEveryNTurns higher,
  document workaround. Rejected: doesn't fix stale task accumulation; contention still
  occurs after long or interrupted sessions. Treats symptom, not cause.
- **LaunchAgent (chosen)** — daemon starts at login via launchd, runs continuously,
  survives session open/close. Plugin hooks still fire for recall/retain; only lifecycle
  management moves out of plugin scope. `stop_daemon` in the plugin checks
  `started_by_plugin` state and no-ops if not set — no conflict.
- **Docker with persistent volume** — the DECISION_ORACLE.md recommended this for
  production. Rejected at this stage: adds Docker dependency for a solo developer
  setup; LaunchAgent achieves the same persistence with less overhead.

### Constraints That Applied
- `stop_daemon` in the plugin only stops if `started_by_plugin` is in daemon state —
  LaunchAgent-started daemons never set this flag, so SessionEnd is a safe no-op
- `SessionStart` checks if daemon is already running and skips pre-start — no conflict
- `HINDSIGHT_EMBED_DAEMON_IDLE_TIMEOUT=0` must be set in profile env to prevent
  the daemon from self-terminating due to inactivity (default is 300s)
- uvx path must be absolute in plist (`/Library/Frameworks/Python.framework/...`)
  because launchd does not inherit shell PATH

### Confidence
High — confirmed via `launchctl list | grep hindsight` (PID present), daemon health
check passing, plugin SessionEnd skip verified via source code reading.

### Revisit Trigger
- If the user moves to a new machine (LaunchAgent must be re-created manually)
- If `uvx` path changes after Python upgrade
- If Hindsight plugin adds explicit `manageDaemon: false` config option (could
  replace the LaunchAgent approach with a cleaner flag)
- If Docker becomes part of the dev environment for other reasons (revert to
  Docker volume approach from DECISION_ORACLE.md)
