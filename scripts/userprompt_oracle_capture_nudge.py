#!/usr/bin/env python3
"""UserPromptSubmit hook: nudge /oracle-debate or /oracle-observe on capture intent.

Fires on every user message but only emits a nudge when the message contains
declarative oracle-capture intent. Vocabulary is intentionally narrow to avoid
colliding with CLAUDE.md auto-memory's generic "remember" semantics:

- auto-memory handles cross-conversation persistence (user facts, preferences,
  feedback) — fires on plain "remember"
- this nudge handles cross-project philosophies / observations (PHIs / OBSs) —
  only fires when the user explicitly signals capture-as-philosophy intent

Output is `additionalContext` (loaded into Claude's context as a system
reminder); Claude decides whether to surface and act on it.
"""

from __future__ import annotations

import json
import re
import sys

# Patterns for declarative oracle-capture intent. Each must signal that the
# user wants something *captured* — not just referenced or recalled.
PATTERNS = [
    r"\bworth (?:recording|keeping|capturing|noting)(?:\s+as)?\b",
    r"\bshould (?:be|become|capture)\s+(?:a\s+|an\s+)?(?:PHI|OBS|philosophy|observation)\b",
    r"\bmake (?:this|that|it)\s+(?:a\s+|an\s+)?(?:PHI|OBS|philosophy|observation)\b",
    r"\b(?:this|that)\s+(?:is|sounds like|feels like|seems like)\s+(?:a\s+|an\s+)?(?:philosophy|principle|pattern|observation)\s+worth\b",
    r"\blet'?s capture (?:this|that)\b",
    r"\bcapture (?:this|that)\s+(?:decision|insight|pattern|philosophy|observation)\b",
    r"\b(?:save|track|record) (?:this|that)\s+as\s+(?:a\s+|an\s+)?(?:PHI|OBS|philosophy|observation|principle|pattern)\b",
]
COMPILED = [re.compile(p, re.IGNORECASE) for p in PATTERNS]

NUDGE = (
    "The user's last message signals oracle-capture intent ({matched!r}). "
    "Consider recommending they capture it now via:\n"
    "- `/oracle-debate \"[brief description]\"` — for cross-project philosophies (PHIs)\n"
    "- `/oracle-observe \"[insight]\"` — for impromptu observations (OBSs)\n"
    "\n"
    "Don't auto-invoke. Let the user confirm. If the content is session-specific "
    "or about the user themselves (preferences, role) rather than a cross-project "
    "decision pattern, the auto-memory system handles it without oracle involvement — "
    "in that case, skip the recommendation."
)


def extract_prompt(data: dict) -> str:
    """Best-effort extraction of the user's prompt text. Tries common keys."""
    for key in ("prompt", "user_message", "message", "content", "user_prompt"):
        value = data.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0  # fail-safe: don't break user prompts on bad input

    prompt = extract_prompt(data)
    if not prompt:
        return 0

    matched: str | None = None
    for pattern in COMPILED:
        m = pattern.search(prompt)
        if m:
            matched = m.group(0)
            break

    if not matched:
        return 0

    print(json.dumps({"additionalContext": NUDGE.format(matched=matched)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
