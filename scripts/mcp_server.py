#!/usr/bin/env python3
"""Hindsight MCP server — adapts the local hindsight daemon HTTP API into typed MCP tools.

Replaces inline python3 -c HTTP heredocs in 5 oracle skills.
See: docs/superpowers/specs/2026-04-30-hindsight-mcp-server-design.md
"""
import datetime
import json
import os
import urllib.request
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("hindsight")

DAEMON_URL = "http://localhost:9077"


def _get(path: str) -> dict:
    """Issue GET to daemon, return parsed JSON body."""
    req = urllib.request.Request(f"{DAEMON_URL}{path}", method="GET")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def _post(path: str, payload: dict, timeout: int = 30) -> dict:
    """Issue POST with JSON body, return parsed JSON response."""
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{DAEMON_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


@mcp.tool()
def hindsight_stats(bank: str) -> dict:
    """Return daemon stats for the given bank (e.g., node_count, observation_count)."""
    return _get(f"/v1/default/banks/{bank}/stats")


@mcp.tool()
def hindsight_list_documents(bank: str, prefix: str | None = None) -> list[dict]:
    """List documents in the bank. If prefix is given (e.g., "PHI-"), filter client-side."""
    body = _get(f"/v1/default/banks/{bank}/documents")
    items = body.get("items", [])
    if prefix:
        items = [d for d in items if d.get("id", "").startswith(prefix)]
    return items


@mcp.tool()
def hindsight_recall(
    bank: str,
    query: str,
    budget: str = "mid",
    max_tokens: int = 4096,
    top_n: int = 10,
    verbose: bool = False,
) -> list[dict] | dict:
    """Retrieve relevant memories from the bank.

    Returns slim shape {text, type, document_id, mentioned_at, metadata} by default;
    top_n entries (default 10). Set verbose=True to get the raw daemon response
    including scores and rank metadata.

    The default-slim shape matches what the oracle skills' synthesis subagents
    consume — see CDR-subscription-llm-routing.md.
    """
    payload = {"query": query, "budget": budget, "max_tokens": max_tokens}
    body = _post(f"/v1/default/banks/{bank}/memories/recall", payload, timeout=60)
    if verbose:
        return body
    results = body.get("results", [])[:top_n]
    return _project_slim(results)


def _project_slim(results: list[dict]) -> list[dict]:
    """Project recall results to Claude-optimized shape: {text, type, document_id, mentioned_at, metadata}.

    Drops: score, rank, any other internal-ranking fields.
    Drops keys whose values are None (slim doesn't include null fields).
    """
    SLIM_KEYS = ("text", "type", "document_id", "mentioned_at", "metadata")
    out = []
    for r in results:
        item = {k: r.get(k) for k in SLIM_KEYS if r.get(k) is not None}
        out.append(item)
    return out


def _retain(bank: str, *, context: str, content: str, document_id: str | None,
            derived_from: str | None, metadata: dict | None) -> dict:
    """Build the retain payload and POST to daemon.

    `context` is daemon-required: 'philosophy' | 'observation' | 'session-log'.
    Derived from tool name in callers, never user-controllable.

    Contract: `derived_from` is a typed kwarg only. Passing `derived_from`
    inside `metadata` is rejected — it would create silent precedence ambiguity
    if both were set. Callers must use the kwarg.
    """
    md = dict(metadata or {})
    if "derived_from" in md:
        raise ValueError(
            "derived_from must be passed as a kwarg, not inside metadata"
        )
    if derived_from:
        md["derived_from"] = derived_from
    item: dict = {"content": content, "context": context, "metadata": md}
    if document_id is not None:
        item["document_id"] = document_id
    payload = {"items": [item]}
    return _post(f"/v1/default/banks/{bank}/memories", payload)


@mcp.tool()
def hindsight_retain_phi(
    bank: str,
    document_id: str,
    content: str,
    derived_from: str | None = None,
    metadata: dict | None = None,
) -> dict:
    """Retain a Philosophy (PHI) record to the bank.

    The MCP server hard-codes context='philosophy' — the caller cannot pass
    a mismatched type. document_id (e.g., "PHI-020") is required. Returns
    the daemon response.

    Note: caller is responsible for stripping the `<!-- ORACLE ARTIFACT -->`
    banner from `content` before passing — the banner is a filesystem-only
    safeguard and adds retrieval noise if embedded in the bank.
    """
    return _retain(
        bank,
        context="philosophy",
        content=content,
        document_id=document_id,
        derived_from=derived_from,
        metadata=metadata,
    )


@mcp.tool()
def hindsight_retain_obs(
    bank: str,
    document_id: str,
    content: str,
    derived_from: str | None = None,
    metadata: dict | None = None,
) -> dict:
    """Retain an Observation (OBS) record to the bank.

    Hard-codes context='observation'. document_id required (e.g., "OBS-013").
    Use `derived_from` to cite related PHI/OBS IDs.
    """
    return _retain(
        bank,
        context="observation",
        content=content,
        document_id=document_id,
        derived_from=derived_from,
        metadata=metadata,
    )


@mcp.tool()
def hindsight_retain_session_log(
    bank: str,
    content: str,
    metadata: dict | None = None,
) -> dict:
    """Retain a session-log record to the bank.

    Hard-codes context='session-log'. No document_id arg — daemon assigns.
    High-frequency, system-driven (PreCompact/SessionEnd code paths).
    """
    return _retain(
        bank,
        context="session-log",
        content=content,
        document_id=None,
        derived_from=None,
        metadata=metadata,
    )


def _hindsight_root() -> Path:
    """Resolve HINDSIGHT_ROOT, falling back to ~/Developer/Hindsight.

    NEVER use os.getcwd() — PHI-006 was the bug where artifacts landed
    in consumer project trees because path resolution fell through to CWD.
    """
    env = os.environ.get("HINDSIGHT_ROOT")
    if env:
        return Path(env)
    return Path(os.environ["HOME"]) / "Developer" / "Hindsight"


@mcp.tool()
def hindsight_log_query(
    client: str,
    question: str,
    answer: str,
    recall_data: dict,
) -> dict:
    """Append a query log line to ${HINDSIGHT_ROOT}/.decisions/queries/YYYY-MM.jsonl.

    Path is anchored to HINDSIGHT_ROOT (or ~/Developer/Hindsight fallback) —
    NEVER to CWD. PHI-006 was the bug this anchor prevents.
    """
    queries_dir = _hindsight_root() / ".decisions" / "queries"
    queries_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now(datetime.timezone.utc)
    log_path = queries_dir / f"{now.year:04d}-{now.month:02d}.jsonl"
    entry = {
        "timestamp": now.isoformat(),
        "client": client,
        "question": question,
        "answer": answer,
        "recall_data": recall_data,
    }
    with log_path.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    return {"logged_path": str(log_path)}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
