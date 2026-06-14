<!-- ORACLE ARTIFACT — canonical copy in the oracle bank; this file is a browse mirror in the Hindsight repo. Observed evidence, not a held philosophy. -->

**Status:** active

## OBS-018 — Concurrent sessions shared a checkout; safe by structural luck
**Relationship:** standalone

On 2026-06-12, two concurrent Claude Code sessions shared the Hindsight main checkout: the secondary session merged PR #20, advanced main via ff-only pull, removed a worktree, and appended to the query JSONL while the primary session held untracked in-flight files. No conflict occurred — but only because every shared write surface was incidentally overlap-tolerant (daemon-mediated append-only log, untracked files invisible to ff-merge, clean-status gate before worktree removal). The spawned-session flow did not provision isolation; safety was structural luck.
