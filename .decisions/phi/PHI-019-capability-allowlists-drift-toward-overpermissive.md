<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-019 — Capability allowlists drift toward over-permissive baselines unless pruned proactively

**Date:** 2026-04-30
**Domain:** infrastructure
**Source Project:** Claude-Root
**Source:** Audit of `.claude/settings.local.json` during a Claude Code session — 99-entry allowlist had degraded with 4 wide wildcards (`Bash(git *)`, `Bash(curl *)`, `Bash(python3 *)`, `Bash(uv pip *)`), ~26 stale entries from a removed feature (009 memory server), one-shot rename commands, and a redundant plaintext credential.

### Philosophy
Capability allowlists drift toward over-permissive baselines unless pruned proactively. Each grant is reactive (unblock work now); removal is invisible (no signal an entry is stale). Treat one-shot permission approvals as candidates for cleanup, not permanent grants — schedule periodic audits the same way you schedule dependency upgrades.

### Why I Hold This
A 99-entry allowlist had degraded into a near-permissive baseline despite originally being scoped per-command. Wide wildcards entered "just this once" to unblock real work and stayed forever. Stale entries from a removed feature survived ~5 days past the feature itself. A redundant plaintext credential lived alongside keyring auth that already worked. Nobody re-evaluated whether the original scope still matched the original intent — and during the very session that performed the cleanup, an auto-allowlist mechanism silently re-introduced `Bash(curl *)`, demonstrating that prune work has a half-life unless paired with deny rules or disabled auto-grant paths.

### Where It Applies
- Claude Code permission allowlists (`.claude/settings*.json`)
- Browser extension permissions (granted at install, never reviewed)
- sudoers files and `/etc/sudoers.d/`
- CI runner allowlists, GitHub Actions step permissions
- IAM policies grown via console clicks
- MCP / plugin trust lists
- AWS resource policies, Kubernetes RBAC role accretion
- Firewall allow-rules accumulated over years
- Any system with manual grants and no scheduled deny-side audit

### Known Tensions
- Pruning too aggressively creates friction — every removed entry becomes a future prompt the user must re-approve
- Auto-allowlist behaviors actively undo pruning unless paired with explicit deny rules or the auto-grant path is disabled
- "Reactive grant + proactive removal" is structurally asymmetric — cost of pruning falls on the same human who has to re-approve later, with no immediate visible gain
- Periodic audits get deprioritized because the system "is working" — drift is silent until exploited

### Open to Revision When
- Deny rules become first-class and override allow at runtime, making accidental over-grants self-correcting
- Permission systems gain expiration / freshness metadata so stale grants surface automatically
- Auto-allowlist mechanisms learn to scope-narrow on grant rather than scope-broaden
- Tooling emerges that flags allowlist entries unused in N days as removal candidates
