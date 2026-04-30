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


def test_hindsight_stats_calls_daemon_and_returns_response(mock_daemon):
    sys.path.insert(0, ".")
    if "scripts.mcp_server" in sys.modules:
        del sys.modules["scripts.mcp_server"]
    mod = importlib.import_module("scripts.mcp_server")

    mock_daemon["respond"]({"node_count": 42, "observation_count": 13})
    result = mod.hindsight_stats(bank="oracle")

    req = mock_daemon["last_request"]()
    assert req["url"] == "http://localhost:9077/v1/default/banks/oracle/stats"
    assert req["method"] == "GET"
    assert result == {"node_count": 42, "observation_count": 13}
