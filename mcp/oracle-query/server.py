# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "mcp>=1.0",
#   "httpx>=0.27",
# ]
# ///
"""MCP server exposing the Decision Oracle to MCP clients (Codex desktop/CLI, etc.).

Wraps the local hindsight-embed daemon's recall endpoint as a single tool,
`oracle_query`. Returns top-K slim results plus an inline relevance-gate
instruction the calling model reads when interpreting the results.

Synthesis happens client-side (the calling model reads the JSON and answers
the user). Mirrors the relevance discipline used by the Claude Code /oracle
skill so behavior is consistent across clients.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

DAEMON_URL = "http://localhost:9077/v1/default/banks/oracle/memories/recall"
TOP_K = 10
TIMEOUT_SECONDS = 30.0
ID_PATTERN = re.compile(r"\b(?:PHI|OBS)-\d{3,}\b")

RELEVANCE_GATE = (
    "RELEVANCE GATE — read each entry against the user's question. If none "
    "is genuinely relevant (i.e., addresses the question's actual subject "
    "matter, not just sharing surface keywords or topic-adjacent themes), "
    "tell the user EXACTLY: 'The oracle has no entries relevant to that "
    "question.' with no padding, summary, or near-miss listing. Empty is a "
    "valid, accepted outcome. If at least one entry is genuinely relevant, "
    "synthesize a direct answer that cites PHI-NNN / OBS-NNN identifiers "
    "(extracted from document_id or embedded in entry text), leads with the "
    "answer not the reasoning, and surfaces tensions or counter-evidence "
    "before recommendations."
)

mcp = FastMCP("oracle")


def _log_query(question: str, results: list[dict[str, Any]], empty: bool) -> None:
    """Append a query entry to the canonical queries log.

    Codex doesn't pass the synthesized answer back to this server, so the
    MCP schema differs from the CC skill schema: we log `available_ids` (PHI/OBS
    IDs in the returned results) instead of `cited_ids` (IDs in the answer).
    Failures are swallowed — logging must not break the tool call.
    """
    try:
        root = Path(os.environ.get("HINDSIGHT_ROOT", str(Path.home() / "Developer" / "Hindsight")))
        log_dir = root / ".decisions" / "queries"
        log_dir.mkdir(parents=True, exist_ok=True)

        available: set[str] = set()
        for item in results:
            doc_id = item.get("document_id")
            if doc_id:
                available.add(doc_id)
            available.update(ID_PATTERN.findall(item.get("text", "")))

        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "client": "codex-mcp",
            "question": question,
            "result_count": len(results),
            "empty": empty,
            "available_ids": sorted(available),
        }
        month = datetime.now(timezone.utc).strftime("%Y-%m")
        log_file = log_dir / f"{month}.jsonl"
        with log_file.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001 — logging must never break tool execution
        pass


@mcp.tool()
async def oracle_query(question: str) -> str:
    """Use BEFORE recommending an architectural approach, choosing between technologies, evaluating a tradeoff, or when the user proposes a design — queries Colin's cross-project Decision Oracle (PHIs/OBSs from prior sessions) and returns relevant prior philosophies. Empty results are a valid signal, not a failure. The returned JSON includes a relevance-gate instruction; follow it when synthesizing the answer.

    Args:
        question: The decision question to query the oracle with.

    Returns:
        JSON string with `instructions` (relevance gate) and `results` (top-K
        slim entries: text, type, document_id, mentioned_at, metadata). If the
        bank has no entries or the daemon is unreachable, returns a plain
        message instead of JSON.
    """
    if not question or not question.strip():
        return "No question provided."

    payload = {"query": question, "budget": "mid", "max_tokens": 4096}
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.post(DAEMON_URL, json=payload)
        response.raise_for_status()
    except httpx.ConnectError:
        return (
            "Oracle unavailable: hindsight-embed daemon not running at "
            "localhost:9077. Start it with: "
            "HINDSIGHT_API_EMBEDDINGS_LOCAL_FORCE_CPU=1 "
            "HINDSIGHT_API_RERANKER_LOCAL_FORCE_CPU=1 "
            "uvx hindsight-embed daemon start"
        )
    except httpx.HTTPError as exc:
        return f"Oracle daemon error: {exc}"

    data = response.json()
    raw_results = data.get("results", [])[:TOP_K]
    slim: list[dict[str, Any]] = []
    for item in raw_results:
        entry = {
            k: item.get(k)
            for k in ("text", "type", "document_id", "mentioned_at", "metadata")
            if item.get(k) is not None
        }
        slim.append(entry)

    if not slim:
        _log_query(question, [], empty=True)
        return "The oracle has no entries relevant to that question."

    _log_query(question, slim, empty=False)
    return json.dumps(
        {"instructions": RELEVANCE_GATE, "results": slim},
        ensure_ascii=False,
        indent=2,
    )


if __name__ == "__main__":
    mcp.run()
