#!/usr/bin/env bash
# One-time per-user setup: symlink oracle skills into ~/.claude/skills (symlinks,
# not copies — copies drift) and print the hook snippet for user settings.
set -eu

ORACLE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_SRC="$ORACLE_ROOT/.claude/skills"

if [ ! -d "$SKILLS_SRC" ]; then
  echo "ERROR: $SKILLS_SRC not found."
  echo "This looks like the un-extracted template. Activate it first:"
  echo "  mv dot-claude .claude && mv CLAUDE.template.md CLAUDE.md"
  exit 1
fi
SKILLS_DST="$HOME/.claude/skills"
mkdir -p "$SKILLS_DST"

for d in "$SKILLS_SRC"/*/; do
  name=$(basename "$d")
  target="$SKILLS_DST/$name"
  if [ -e "$target" ] && [ ! -L "$target" ]; then
    echo "SKIP $name: $target exists and is not a symlink — resolve manually."
    continue
  fi
  ln -sfn "$d" "$target"
  echo "linked $name -> $target"
done

cat <<EOF

Add to your shell profile:
  export ORACLE_ROOT="$ORACLE_ROOT"

Add to ~/.claude/settings.json (user level, so every project gets the index):
{
  "hooks": {
    "SessionStart": [
      { "hooks": [ { "type": "command",
        "command": "ORACLE_ROOT=$ORACLE_ROOT bash $ORACLE_ROOT/scripts/hooks/session_start_oracle.sh" } ] }
    ]
  }
}

Optional weekly capture miner (see header of scripts/weekly_mine.sh for
scheduling; it must run locally, where your transcripts live).
EOF
