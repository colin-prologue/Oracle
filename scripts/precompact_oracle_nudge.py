#!/usr/bin/env python3
"""PreCompact hook: nudge user to run /oracle-preclear before auto-compaction.

Registered in .claude/settings.json with matcher "auto" so this only fires
when the harness is about to auto-compact (context near limit), not on
user-typed /compact or /clear. Blocks the auto-compaction with a reason
the user sees, so retention happens before context is mutated.

This catches the slow-context-drift case. Manual /clear is still
unhookable — relies on the existing CLAUDE.md Session End Protocol.
"""

from __future__ import annotations

import json
import sys


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # If we can't parse the input, don't block compaction.
        return 0

    used = data.get("context_used")
    remaining = data.get("tokens_remaining")

    budget_line = ""
    if used is not None and remaining is not None:
        budget_line = f" (context: {used} used / {remaining} remaining)"

    reason = (
        f"Auto-compaction is about to fire{budget_line}. To preserve session "
        "insights in the oracle bank, run `/oracle-preclear` first. After "
        "that, choose:\n"
        "  - `/compact` — continue the same session with summarized context\n"
        "  - `/clear` — start fresh\n"
        "If you don't care about preserving insights this session, type "
        "`/compact` to bypass this nudge."
    )

    print(json.dumps({"decision": "block", "reason": reason}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
