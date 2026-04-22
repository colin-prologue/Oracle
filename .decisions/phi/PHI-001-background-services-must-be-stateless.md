<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-001 — Background services must be stateless and session-independent

**Date:** 2026-04-09
**Domain:** infrastructure, tooling
**Source Project:** hindsight
**Source:** CDR-001 / ADR-001 — hindsight-embed daemon auth cascade failure

### Philosophy
Never tie a background service's auth or lifecycle to the session that invokes it. Daemons must authenticate via durable, key-based credentials — not via the calling session's active auth context.

### Why I Hold This
Manually setting the hindsight-embed daemon to use `claude-code` as its LLM provider caused cascading process spawns, macOS crash dialogs, and port-binding collisions. The daemon's LLM calls contended with the active Claude Code session's context because `claude-code` routes through the session-bound Agent SDK. The configure wizard deliberately excluded this option — bypassing it was the mistake.

### Where It Applies
Any time a background process, daemon, or long-running service needs to make LLM or API calls: it must use key-based, stateless credentials. This applies regardless of whether a session-bound shortcut exists that would avoid an extra key.

### Known Tensions
Session-bound auth shortcuts (like `claude-code` provider) are tempting for solo developers trying to minimize the number of API keys and accounts managed. The convenience is real — but the failure mode (nested auth loops, resource contention) is severe and hard to diagnose.

### Open to Revision When
A session-independent, headless auth mode exists for session-bound SDKs — e.g., if Anthropic releases a service-account mode for the Agent SDK that doesn't require an active CLI session.
