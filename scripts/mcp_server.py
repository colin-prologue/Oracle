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


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
