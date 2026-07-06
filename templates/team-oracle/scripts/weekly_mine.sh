#!/usr/bin/env bash
# Weekly capture miner. Scans the past week's local Claude Code transcripts and
# drafts AT MOST 3 candidate records into inbox/ for human triage.
#
# Extraction is automated; judgment is not. Nothing this script produces
# reaches the shared repo until /oracle-triage approves it.
#
# Schedule locally (this must run where the transcripts live — a cloud task
# cannot see them):
#   macOS/Linux cron:  0 9 * * MON  ORACLE_ROOT=$HOME/team-oracle $ORACLE_ROOT/scripts/weekly_mine.sh
#   Windows:           Task Scheduler -> git-bash.exe -c "..."
set -eu

ORACLE_ROOT="${ORACLE_ROOT:-$HOME/team-oracle}"
CLAUDE_PROJECTS="${CLAUDE_PROJECTS:-$HOME/.claude/projects}"
INBOX="$ORACLE_ROOT/inbox"
mkdir -p "$INBOX"

# Recent transcripts, newest first, capped so the prompt stays bounded.
transcripts=$(find "$CLAUDE_PROJECTS" -name '*.jsonl' -mtime -7 2>/dev/null \
  | head -20)

if [ -z "$transcripts" ]; then
  echo "team-oracle miner: no transcripts in the last 7 days; nothing to do."
  exit 0
fi

stamp=$(date +%Y-%m-%d)
claude -p "$(cat "$ORACLE_ROOT/scripts/mine_prompt.md")

Transcript files to scan (read selectively — recent user/assistant text, skip tool noise):
$transcripts

Write each candidate as a separate markdown file to $INBOX/${stamp}-candidate-N.md and print a one-line summary per candidate." \
  --allowedTools "Read,Write,Glob,Grep"

echo "team-oracle miner: done. Review with /oracle-triage in a session."
