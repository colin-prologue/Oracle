"""Tests for hindsight MCP server tool implementations."""
import importlib
import sys


def test_server_module_imports():
    # Avoid re-import if already loaded.
    if "scripts.mcp_server" in sys.modules:
        del sys.modules["scripts.mcp_server"]
    sys.path.insert(0, ".")
    mod = importlib.import_module("scripts.mcp_server")
    assert mod.DAEMON_URL == "http://localhost:9077"
    assert mod.mcp.name == "hindsight"
