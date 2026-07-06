#!/usr/bin/env bash
# SessionStart hook: sync the oracle clone (throttled) and inject INDEX.md
# into session context. Registered user-level so every project gets it.
# Must never block a session: all failures degrade to "inject what we have".
set -u

ORACLE_ROOT="${ORACLE_ROOT:-$HOME/team-oracle}"
STAMP="$ORACLE_ROOT/.oracle-sync-stamp"
SYNC_INTERVAL_SECS=14400  # 4h; records change slowly

[ -d "$ORACLE_ROOT/.git" ] || exit 0  # no clone, no oracle — stay silent

# Throttled fetch with a hard timeout so a hung VPN can't stall session start.
now=$(date +%s)
last=0
[ -f "$STAMP" ] && last=$(cat "$STAMP" 2>/dev/null || echo 0)
if [ $((now - last)) -ge "$SYNC_INTERVAL_SECS" ]; then
  if command -v timeout >/dev/null 2>&1; then
    timeout 10 git -C "$ORACLE_ROOT" fetch --quiet origin main 2>/dev/null
  else
    git -C "$ORACLE_ROOT" fetch --quiet origin main 2>/dev/null &
    fpid=$!; ( sleep 10 && kill "$fpid" 2>/dev/null ) & wpid=$!
    wait "$fpid" 2>/dev/null; kill "$wpid" 2>/dev/null
  fi
  echo "$now" > "$STAMP"
fi

# Read the index from the remote tip so retrieval reflects the freshest state
# regardless of local working-tree drift; fall back to the local file.
index=$(git -C "$ORACLE_ROOT" show origin/main:INDEX.md 2>/dev/null) \
  || index=$(cat "$ORACLE_ROOT/INDEX.md" 2>/dev/null) \
  || exit 0

behind=$(git -C "$ORACLE_ROOT" rev-list --count HEAD..origin/main 2>/dev/null || echo 0)

cat <<EOF
<team-oracle-index root="$ORACLE_ROOT" behind="$behind">
Team decision oracle index (one line per record). Before recommending an
architectural approach, technology choice, or tradeoff, consult it with
/oracle "[question]". Records live under $ORACLE_ROOT/records/.

$index
</team-oracle-index>
EOF
