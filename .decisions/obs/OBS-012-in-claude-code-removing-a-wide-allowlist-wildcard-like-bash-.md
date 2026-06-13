<!-- ORACLE ARTIFACT — canonical copy in the oracle bank; this file is a browse mirror in the Hindsight repo. Observed evidence, not a held philosophy. -->

**Status:** active

In Claude Code, removing a wide allowlist wildcard like `Bash(curl *)` from `.claude/settings.local.json` can be silently re-introduced mid-session by an auto-allowlist mechanism that grants previously-approved patterns on subsequent matching invocations. Cleanup work on capability allowlists has a half-life unless paired with explicit deny rules or the auto-grant path is disabled.

Observed live on 2026-04-30 in a Claude-Root session: during a deliberate allowlist prune that dropped `Bash(curl *)` in favor of three host-scoped curl entries (`raw.githubusercontent.com`, `api.github.com`, HEAD-only `https://*`), `Bash(curl *)` was silently re-added by an external linter or auto-grant mechanism before the session ended. The re-addition was flagged in a system-reminder as "intentional," meaning the harness did not surface it as adversarial — only that the file had been modified out-of-band.

This is the empirical evidence behind PHI-019's "Known Tensions" section: the asymmetry between reactive grants (immediate) and proactive removal (invisible) is not just a maintenance gap — it is actively undone by tooling. Implication: pruning capability allowlists in any system with auto-grant behavior must be paired with either (a) deny rules that override allow, (b) disabling the auto-grant path, or (c) a higher-frequency audit cadence than the auto-grant restoration cycle. Without one of those, the cleanup is performative.
