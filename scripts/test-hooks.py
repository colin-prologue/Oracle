#!/usr/bin/env python3
"""Hook-firing test harness.

Reads one or more settings.json files, enumerates configured hooks, runs each
hook against a synthesized stdin payload appropriate to its event/matcher, and
reports pass/fail per case. Closes the aspirational-convention-drift gap PHI-004
names: a hook documented but never validated in the workflow it claims to guard.

Optional sidecar `<settings>.assertions.json` declares expected outcomes per
case (event + matcher + command-substring → expect allow|deny + optional stdin
overrides). Without an assertion, "must exit 0" is the default expectation.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


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


def load_assertions(settings_path):
    """Sidecar `<settings>.assertions.json` lists expectations.

    Format: [{event, matcher, command_contains, expect, stdin_overrides?}, ...].
    Returns the list (possibly empty).
    """
    p = Path(str(settings_path).replace(".json", ".assertions.json"))
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError:
        return []


def match_assertion(assertions, event, matcher, command):
    for a in assertions:
        if a.get("event") != event:
            continue
        if a.get("matcher", "") != matcher:
            continue
        if a.get("command_contains", "") and a["command_contains"] not in command:
            continue
        return a
    return None


def classify_outcome(returncode, stdout):
    """Map a command-hook result to allow|deny.

    - exit != 0 → deny (host blocks the tool when a PreToolUse hook errors)
    - exit 0 with permissionDecision == "deny" in stdout JSON → deny
    - exit 0 with permissionDecision == "allow" → allow
    - exit 0 with no decision → allow
    """
    if returncode != 0:
        return "deny"
    out = stdout.strip()
    if not out:
        return "allow"
    try:
        obj = json.loads(out)
        decision = (obj.get("hookSpecificOutput") or {}).get("permissionDecision")
        if decision == "deny":
            return "deny"
        if decision == "allow":
            return "allow"
    except json.JSONDecodeError:
        pass
    return "allow"


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

        assertions = load_assertions(src)
        assertion = match_assertion(assertions, event, matcher, spec["command"])

        payload = synthesize_payload(event, matcher)
        if assertion and assertion.get("stdin_overrides"):
            for k, v in assertion["stdin_overrides"].items():
                if k == "tool_input" and isinstance(payload.get("tool_input"), dict):
                    payload["tool_input"].update(v)
                else:
                    payload[k] = v

        try:
            code, out, err = run_command_hook(spec, payload, timeout=spec.get("timeout", 10))
        except subprocess.TimeoutExpired:
            print(f"FAIL {label} — timeout")
            failures += 1
            continue

        outcome = classify_outcome(code, out)

        if assertion:
            expected = assertion.get("expect", "allow")
            if outcome == expected:
                print(f"PASS {label}  expect={expected}  got={outcome}")
            else:
                print(f"FAIL {label}  expect={expected}  got={outcome}\n  stdout: {out.strip()[:200]}")
                failures += 1
        else:
            if code == 0:
                print(f"PASS {label}  (no assertion, exit 0)")
            else:
                print(f"FAIL {label}  exit {code}\n  stderr: {err.strip()[:200]}")
                failures += 1

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
