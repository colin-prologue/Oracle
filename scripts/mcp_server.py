#!/usr/bin/env python3
"""Hindsight MCP server — adapts the local hindsight daemon HTTP API into typed MCP tools.

Replaces inline python3 -c HTTP heredocs in 5 oracle skills.
See: docs/superpowers/specs/2026-04-30-hindsight-mcp-server-design.md
"""
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("hindsight")

DAEMON_URL = "http://localhost:9077"


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
