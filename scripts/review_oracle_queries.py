"""Review recent oracle query log entries.

Reads .decisions/queries/*.jsonl, prints the last N entries in human-readable
form. No analytics, no aggregations — that's the dashboard trap. Real review
is reading the questions and judging whether the bank is being asked questions
it can actually answer.

Usage:
    python3 scripts/review_oracle_queries.py [N]   # default N=20
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def main() -> int:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20

    root = Path(os.environ.get("HINDSIGHT_ROOT", str(Path.home() / "Developer" / "Hindsight")))
    log_dir = root / ".decisions" / "queries"
    if not log_dir.exists():
        print(f"no log dir: {log_dir}")
        return 1

    files = sorted(log_dir.glob("*.jsonl"))
    if not files:
        print(f"no log files in {log_dir}")
        return 1

    entries: list[dict] = []
    for f in files:
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as exc:
                print(f"warning: bad line in {f}: {exc}", file=sys.stderr)

    entries = entries[-n:]
    if not entries:
        print("no entries yet")
        return 0

    for e in entries:
        empty_marker = " [EMPTY]" if e.get("empty") else ""
        client = e.get("client", "?")
        ids = e.get("cited_ids") or e.get("available_ids") or []
        ids_str = ", ".join(ids) if ids else "—"
        print(f"\n{e.get('ts', '?')}  ({client}){empty_marker}")
        print(f"  Q: {e.get('question', '')}")
        print(f"  results={e.get('result_count', 0)}  ids={ids_str}")
        if (answer := e.get("answer")) and not e.get("empty"):
            preview = answer.replace("\n", " ").strip()
            if len(preview) > 200:
                preview = preview[:200] + "..."
            print(f"  A: {preview}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
