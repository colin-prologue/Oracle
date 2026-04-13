## CDR-003 — Hindsight plugin user config lives at ~/.hindsight/claude-code.json

**Date:** 2026-04-09
**Project:** Hindsight / Decision Oracle
**Domain:** tooling
**Session:** Initial Hindsight install and oracle setup

### Decision
User config overrides for the hindsight-memory plugin must be placed at
~/.hindsight/claude-code.json, not ~/.claude/plugins/data/hindsight/...

### Context
Attempted to disable autoRecall/autoRetain by writing to
~/.claude/plugins/data/hindsight/hindsight-memory/settings.json (the path used
by other Claude Code plugin systems). The config was silently ignored — hooks
kept firing. Reading config.py revealed the loading order: plugin defaults →
~/.hindsight/claude-code.json → env vars. The plugins/data/ path is never read.

### Constraints That Applied
- Plugin loading order is undocumented; had to read source to find it
- Silence on invalid config path makes this easy to get wrong

### Confidence
High — confirmed by reading config.py load_config() directly.

### Revisit Trigger
If hindsight-memory plugin adds support for reading from Claude Code's standard
plugin data directory.
