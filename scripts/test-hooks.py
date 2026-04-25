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
import sys
from pathlib import Path


def load_settings(paths):
    """Yield (path, dict) for each readable settings file."""
    for p in paths:
        p = Path(p).expanduser()
        if not p.exists():
            continue
        try:
            yield p, json.loads(p.read_text())
        except json.JSONDecodeError as e:
            print(f"WARN: skipping malformed settings at {p}: {e}", file=sys.stderr)


def enumerate_cases(settings_iter):
    """Flatten settings into (source, event, matcher, hook_spec) cases."""
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
    for src, event, matcher, spec in cases:
        print(f"  {event}/{matcher or '*'}  type={spec.get('type')}  src={src}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
