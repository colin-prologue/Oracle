## CDR-002 — macOS requires CPU-forcing flags for hindsight-embed local models

**Date:** 2026-04-09
**Project:** Hindsight / Decision Oracle
**Domain:** tooling, infrastructure
**Session:** Initial Hindsight install and oracle setup

### Decision
Always set HINDSIGHT_API_EMBEDDINGS_LOCAL_FORCE_CPU=1 and
HINDSIGHT_API_RERANKER_LOCAL_FORCE_CPU=1 in the claude-code daemon profile.

### Context
Daemon crashed on startup after loading sentence-transformer models
(BAAI/bge-small-en-v1.5, cross-encoder/ms-marco-MiniLM-L-6-v2). Logs showed
"No device provided, using mps" — Apple Silicon GPU selected by default. Daemon
never reached "Application startup complete." The plugin sets these flags when
it auto-starts the daemon, but `uvx hindsight-embed daemon start` run manually
bypasses that injection. Fix: persist the flags in the profile so they apply
regardless of how the daemon is launched.

### Options Considered
- **Let daemon use MPS (default)** — no config needed. Rejected: startup crash
  on macOS 23.5.0 / Apple Silicon / Python 3.14. Multiprocessing resource
  tracker reports leaked semaphore on shutdown.
- **Force CPU via profile env vars (chosen)** — one-time config, applies on
  every start. Consistent with hindsight-embed's own macOS guidance (the plugin
  already does this internally).

### Constraints That Applied
- macOS Apple Silicon + Python 3.14 + sentence-transformers MPS incompatibility
- Daemon must be startable both by plugin hooks and manually

### Confidence
High — crash was reproducible; adding flags fixed it immediately.

### Revisit Trigger
Future hindsight-embed or PyTorch release resolving MPS compatibility on
macOS + Python 3.14.
