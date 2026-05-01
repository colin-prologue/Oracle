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


def test_hindsight_list_documents_no_prefix(mock_daemon):
    sys.path.insert(0, ".")
    if "scripts.mcp_server" in sys.modules:
        del sys.modules["scripts.mcp_server"]
    mod = importlib.import_module("scripts.mcp_server")

    mock_daemon["respond"]({"items": [
        {"id": "PHI-001", "type": "philosophy"},
        {"id": "OBS-002", "type": "observation"},
    ]})
    result = mod.hindsight_list_documents(bank="oracle")

    req = mock_daemon["last_request"]()
    assert req["url"] == "http://localhost:9077/v1/default/banks/oracle/documents"
    assert len(result) == 2


def test_hindsight_list_documents_with_prefix_filters_client_side(mock_daemon):
    sys.path.insert(0, ".")
    if "scripts.mcp_server" in sys.modules:
        del sys.modules["scripts.mcp_server"]
    mod = importlib.import_module("scripts.mcp_server")

    mock_daemon["respond"]({"items": [
        {"id": "PHI-001", "type": "philosophy"},
        {"id": "OBS-002", "type": "observation"},
        {"id": "PHI-003", "type": "philosophy"},
    ]})
    result = mod.hindsight_list_documents(bank="oracle", prefix="PHI-")
    assert all(d["id"].startswith("PHI-") for d in result)
    assert len(result) == 2


def test_slim_projection_keeps_required_fields_drops_others():
    sys.path.insert(0, ".")
    if "scripts.mcp_server" in sys.modules:
        del sys.modules["scripts.mcp_server"]
    mod = importlib.import_module("scripts.mcp_server")

    raw_results = [
        {
            "text": "philosophy text",
            "type": "experience",
            "document_id": "PHI-001",
            "mentioned_at": "2026-04-25T01:00:00+00:00",
            "metadata": {"domain": "architecture"},
            "score": 0.91,
            "rank": 0,
        },
        {
            "text": "observation text",
            "type": "observation",
            "document_id": None,
            "mentioned_at": "2026-04-21T22:00:00+00:00",
            "metadata": None,
            "score": 0.84,
            "rank": 1,
        },
    ]

    slim = mod._project_slim(raw_results)
    assert slim == [
        {
            "text": "philosophy text",
            "type": "experience",
            "document_id": "PHI-001",
            "mentioned_at": "2026-04-25T01:00:00+00:00",
            "metadata": {"domain": "architecture"},
        },
        {
            "text": "observation text",
            "type": "observation",
            "mentioned_at": "2026-04-21T22:00:00+00:00",
        },
    ]
