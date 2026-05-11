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


def normalize_query_entry(entry: dict) -> dict:
    """Normalize canonical and legacy query log entries for review output."""
    recall_data = entry.get("recall_data") or {}
    outcome = entry.get("outcome")
    if not outcome:
        outcome = "empty" if recall_data.get("empty") else "relevant"

    ids = (
        entry.get("accepted_ids")
        or entry.get("cited_ids")
        or entry.get("available_ids")
        or recall_data.get("cited_ids")
        or recall_data.get("available_ids")
        or []
    )
    rejected_ids = entry.get("rejected_ids") or recall_data.get("rejected_ids") or []
    rejection_reasons = (
        entry.get("rejection_reasons")
        or recall_data.get("rejection_reasons")
        or {}
    )

    return {
        "timestamp": entry.get("timestamp") or entry.get("ts") or "?",
        "client": entry.get("client", "?"),
        "source": entry.get("workflow_source") or entry.get("source") or "legacy",
        "outcome": outcome,
        "question": entry.get("question", ""),
        "answer": entry.get("answer", ""),
        "result_count": entry.get("result_count", recall_data.get("result_count", 0)),
        "ids": ids,
        "rejected_ids": rejected_ids,
        "rejection_reasons": rejection_reasons,
    }


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
        normalized = normalize_query_entry(e)
        empty_marker = " [EMPTY]" if normalized["outcome"] == "empty" else ""
        ids_str = ", ".join(normalized["ids"]) if normalized["ids"] else "—"
        rejected_str = (
            ", ".join(normalized["rejected_ids"])
            if normalized["rejected_ids"]
            else "—"
        )
        print(
            f"\n{normalized['timestamp']}  ({normalized['client']}; "
            f"{normalized['source']}; {normalized['outcome']}){empty_marker}"
        )
        print(f"  Q: {normalized['question']}")
        print(
            f"  results={normalized['result_count']}  ids={ids_str}  "
            f"rejected={rejected_str}"
        )
        if normalized["rejection_reasons"]:
            for doc_id, reason in normalized["rejection_reasons"].items():
                print(f"  reject {doc_id}: {reason}")
        if (answer := normalized["answer"]) and normalized["outcome"] != "empty":
            preview = answer.replace("\n", " ").strip()
            if len(preview) > 200:
                preview = preview[:200] + "..."
            print(f"  A: {preview}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
