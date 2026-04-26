"""Append a query/answer entry to the oracle queries log.

Used by the Claude Code /oracle skill (step 6). The MCP server has its own
logging path inline. Two writers, two implementations — Rule of Three says
don't extract a shared helper for two sites.

Reads question, answer, and recall response from files (avoids shell-escape
issues with arbitrary user input). Writes one JSON line per invocation to
$HINDSIGHT_ROOT/.decisions/queries/YYYY-MM.jsonl.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

EMPTY_ANSWER = "The oracle has no entries relevant to that question."
ID_PATTERN = re.compile(r"\b(?:PHI|OBS)-\d{3,}\b")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", required=True, help="claude-code | codex-mcp | other")
    parser.add_argument("--question-file", required=True, type=Path)
    parser.add_argument("--answer-file", required=True, type=Path)
    parser.add_argument("--recall-file", required=True, type=Path)
    args = parser.parse_args()

    root = Path(os.environ.get("HINDSIGHT_ROOT", str(Path.home() / "Developer" / "Hindsight")))
    log_dir = root / ".decisions" / "queries"
    log_dir.mkdir(parents=True, exist_ok=True)

    question = args.question_file.read_text(encoding="utf-8").rstrip("\n")
    answer = args.answer_file.read_text(encoding="utf-8").rstrip("\n")
    recall = json.loads(args.recall_file.read_text(encoding="utf-8")) if args.recall_file.exists() else {}
    results = recall.get("results", [])

    empty = len(results) == 0 or answer.strip() == EMPTY_ANSWER
    cited = sorted(set(ID_PATTERN.findall(answer)))

    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "client": args.client,
        "project": os.getcwd(),
        "question": question,
        "result_count": len(results),
        "empty": empty,
        "cited_ids": cited,
        "answer": answer,
    }

    month = datetime.now(timezone.utc).strftime("%Y-%m")
    log_file = log_dir / f"{month}.jsonl"
    with log_file.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"logged: {log_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
