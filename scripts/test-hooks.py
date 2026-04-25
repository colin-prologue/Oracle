#!/usr/bin/env python3
"""Hook-firing test harness.

Reads one or more settings.json files, enumerates configured hooks, runs each
hook against a synthesized stdin payload appropriate to its event/matcher, and
reports pass/fail per case. Closes the aspirational-convention-drift gap PHI-004
names: a hook documented but never validated in the workflow it claims to guard.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


# Default stdin payloads per (event, matcher) — the harness synthesizes a plausible
# tool_input for each tool the matcher names. Add entries as new hooks appear.
DEFAULT_PAYLOADS = {
    ("PreToolUse", "Bash"): {"tool_name": "Bash", "tool_input": {"command": "ls"}},
    ("PreToolUse", "Write"): {"tool_name": "Write", "tool_input": {"file_path": "/tmp/x.txt", "content": "x"}},
    ("PreToolUse", "Edit"): {"tool_name": "Edit", "tool_input": {"file_path": "/tmp/x.txt", "old_string": "a", "new_string": "b"}},
    ("PostToolUse", "Bash"): {"tool_name": "Bash", "tool_input": {"command": "ls"}, "tool_response": {"success": True}},
    ("UserPromptSubmit", ""): {"prompt": "test prompt"},
    ("Stop", ""): {},
    ("SessionStart", ""): {},
    ("SessionEnd", ""): {},
    ("PreCompact", ""): {"trigger": "manual"},
}


def synthesize_payload(event, matcher):
    return DEFAULT_PAYLOADS.get((event, matcher), {"event": event, "matcher": matcher})


def run_command_hook(spec, payload, timeout=10):
    """Invoke a command-type hook with stdin = json.dumps(payload).

    Returns (returncode, stdout, stderr).
    """
    proc = subprocess.run(
        spec["command"],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        shell=True,
        timeout=timeout,
    )
    return proc.returncode, proc.stdout, proc.stderr


def load_settings(paths):
    for p in paths:
        p = Path(p).expanduser()
        if not p.exists():
            continue
        try:
            yield p, json.loads(p.read_text())
        except json.JSONDecodeError as e:
            print(f"WARN: skipping malformed settings at {p}: {e}", file=sys.stderr)


def enumerate_cases(settings_iter):
    cases = []
    for src, settings in settings_iter:
        hooks = settings.get("hooks") or {}
        for event, entries in hooks.items():
            for entry in entries:
                matcher = entry.get("matcher", "")
                for spec in entry.get("hooks", []):
                    cases.append((str(src), event, matcher, spec))
    return cases


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--settings", action="append", default=[], help="Path to a settings.json (repeatable)")
    args = ap.parse_args()

    if not args.settings:
        args.settings = [
            "~/.claude/settings.json",
            ".claude/settings.json",
        ]

    cases = enumerate_cases(load_settings(args.settings))
    if not cases:
        print("0 cases (no hooks found)")
        return 0

    print(f"{len(cases)} cases")
    failures = 0
    for src, event, matcher, spec in cases:
        label = f"{event}/{matcher or '*'} ({spec.get('type')})"
        if spec.get("type") != "command":
            print(f"SKIP {label} — non-command hooks (prompt/agent/http) not exercised")
            continue
        payload = synthesize_payload(event, matcher)
        try:
            code, out, err = run_command_hook(spec, payload, timeout=spec.get("timeout", 10))
        except subprocess.TimeoutExpired:
            print(f"FAIL {label} — timeout")
            failures += 1
            continue
        if code != 0:
            print(f"FAIL {label} — exit {code}\n  stderr: {err.strip()[:200]}")
            failures += 1
        else:
            print(f"PASS {label}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
