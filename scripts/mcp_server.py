#!/usr/bin/env python3
"""Hindsight MCP server — adapts the local hindsight daemon HTTP API into typed MCP tools.

Replaces inline python3 -c HTTP heredocs in 5 oracle skills.
See: docs/superpowers/specs/2026-04-30-hindsight-mcp-server-design.md
"""
import json
import urllib.request

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


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
