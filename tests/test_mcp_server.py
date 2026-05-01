"""Tests for hindsight MCP server tool implementations."""
import json
import urllib.error

import pytest


def test_server_module_imports(mcp_mod):
    assert mcp_mod.DAEMON_URL == "http://localhost:9077"
    assert mcp_mod.mcp.name == "hindsight"


def test_hindsight_stats_calls_daemon_and_returns_response(mcp_mod, mock_daemon):
    mock_daemon["respond"](
        {"node_count": 42, "observation_count": 13},
        url="/v1/default/banks/oracle/stats",
        method="GET",
    )
    result = mcp_mod.hindsight_stats(bank="oracle")
    assert result == {"node_count": 42, "observation_count": 13}


def test_hindsight_stats_surfaces_http_error(mcp_mod, mock_daemon):
    mock_daemon["respond"]({}, status=503)
    with pytest.raises(urllib.error.HTTPError):
        mcp_mod.hindsight_stats(bank="oracle")


def test_hindsight_list_documents_no_prefix(mcp_mod, mock_daemon):
    mock_daemon["respond"](
        {"items": [
            {"id": "PHI-001", "type": "philosophy"},
            {"id": "OBS-002", "type": "observation"},
        ]},
        url="/v1/default/banks/oracle/documents",
        method="GET",
    )
    result = mcp_mod.hindsight_list_documents(bank="oracle")
    assert len(result) == 2


def test_hindsight_list_documents_with_prefix_filters_client_side(mcp_mod, mock_daemon):
    mock_daemon["respond"]({"items": [
        {"id": "PHI-001", "type": "philosophy"},
        {"id": "OBS-002", "type": "observation"},
        {"id": "PHI-003", "type": "philosophy"},
    ]})
    result = mcp_mod.hindsight_list_documents(bank="oracle", prefix="PHI-")
    assert all(d["id"].startswith("PHI-") for d in result)
    assert len(result) == 2


def test_hindsight_list_documents_handles_missing_items_key(mcp_mod, mock_daemon):
    """Daemon shape change protection: tool returns [] not raises KeyError."""
    mock_daemon["respond"]({})
    assert mcp_mod.hindsight_list_documents(bank="oracle") == []


def test_slim_projection_keeps_required_fields_drops_others(mcp_mod):
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

    slim = mcp_mod._project_slim(raw_results)
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


def test_hindsight_recall_default_slim(mcp_mod, mock_daemon):
    mock_daemon["respond"](
        {"results": [
            {"text": "t1", "type": "experience", "document_id": "PHI-001",
             "mentioned_at": "2026-04-25T01:00:00+00:00", "metadata": {"d": "x"}, "score": 0.9},
            {"text": "t2", "type": "observation", "document_id": None,
             "mentioned_at": "2026-04-21T22:00:00+00:00", "metadata": None, "score": 0.8},
        ]},
        url="/v1/default/banks/oracle/memories/recall",
        method="POST",
    )
    result = mcp_mod.hindsight_recall(bank="oracle", query="test query")

    body = json.loads(mock_daemon["last_request"]()["body"])
    assert body["query"] == "test query"
    assert body["budget"] == "mid"
    assert body["max_tokens"] == 4096

    assert "score" not in result[0]
    assert result[0]["document_id"] == "PHI-001"
    assert "metadata" not in result[1]


def test_hindsight_recall_verbose_returns_full_response(mcp_mod, mock_daemon):
    raw = {"results": [{"text": "t1", "type": "experience", "score": 0.9}], "meta": "anything"}
    mock_daemon["respond"](raw)
    result = mcp_mod.hindsight_recall(bank="oracle", query="q", verbose=True)
    assert result == raw


def test_hindsight_recall_top_n_truncates(mcp_mod, mock_daemon):
    mock_daemon["respond"]({"results": [
        {"text": f"t{i}", "type": "experience", "mentioned_at": "2026-04-25T01:00:00+00:00"}
        for i in range(20)
    ]})
    result = mcp_mod.hindsight_recall(bank="oracle", query="q", top_n=5)
    assert len(result) == 5


def test_hindsight_recall_passes_budget_and_max_tokens(mcp_mod, mock_daemon):
    mock_daemon["respond"]({"results": []})
    mcp_mod.hindsight_recall(bank="oracle", query="q", budget="high", max_tokens=8192)
    body = json.loads(mock_daemon["last_request"]()["body"])
    assert body["budget"] == "high"
    assert body["max_tokens"] == 8192


def test_hindsight_recall_handles_missing_results_key(mcp_mod, mock_daemon):
    """Daemon shape change protection: missing 'results' yields []."""
    mock_daemon["respond"]({})
    assert mcp_mod.hindsight_recall(bank="oracle", query="q") == []


def test_hindsight_recall_surfaces_http_error(mcp_mod, mock_daemon):
    mock_daemon["respond"]({}, status=500)
    with pytest.raises(urllib.error.HTTPError):
        mcp_mod.hindsight_recall(bank="oracle", query="q")


def test_hindsight_retain_phi_maps_context_and_metadata(mcp_mod, mock_daemon):
    mock_daemon["respond"](
        {"document_id": "PHI-020", "mentioned_at": "2026-04-30T03:30:00+00:00"},
        url="/v1/default/banks/oracle/memories",
        method="POST",
    )
    result = mcp_mod.hindsight_retain_phi(
        bank="oracle",
        document_id="PHI-020",
        content="## PHI-020 — Test\n\nphilosophy body",
        derived_from="OBS-001",
        metadata={"domain": "architecture", "source": "oracle-debate"},
    )

    body = json.loads(mock_daemon["last_request"]()["body"])
    item = body["items"][0]
    assert item["context"] == "philosophy"
    assert item["document_id"] == "PHI-020"
    assert item["content"] == "## PHI-020 — Test\n\nphilosophy body"
    assert item["metadata"]["domain"] == "architecture"
    assert item["metadata"]["derived_from"] == "OBS-001"
    assert result["document_id"] == "PHI-020"


def test_hindsight_retain_phi_omits_derived_from_when_absent(mcp_mod, mock_daemon):
    mock_daemon["respond"]({"document_id": "PHI-021"})
    mcp_mod.hindsight_retain_phi(
        bank="oracle",
        document_id="PHI-021",
        content="body",
        metadata={"domain": "process"},
    )

    body = json.loads(mock_daemon["last_request"]()["body"])
    item = body["items"][0]
    assert "derived_from" not in item["metadata"]


def test_retain_rejects_derived_from_inside_metadata(mcp_mod, mock_daemon):
    """Contract pin: derived_from is a kwarg-only parameter.

    Allowing it inside metadata creates silent precedence ambiguity if both
    are passed. Reject at the boundary instead.
    """
    mock_daemon["respond"]({"document_id": "PHI-099"})
    with pytest.raises(ValueError, match="derived_from"):
        mcp_mod.hindsight_retain_phi(
            bank="oracle",
            document_id="PHI-099",
            content="body",
            metadata={"derived_from": "OBS-001", "domain": "x"},
        )


def test_retain_rejects_derived_from_in_metadata_even_without_kwarg(mcp_mod, mock_daemon):
    """The rejection is unconditional — not just a precedence-conflict check."""
    mock_daemon["respond"]({"document_id": "OBS-099"})
    with pytest.raises(ValueError, match="derived_from"):
        mcp_mod.hindsight_retain_obs(
            bank="oracle",
            document_id="OBS-099",
            content="body",
            metadata={"derived_from": "PHI-001"},
        )


def test_hindsight_retain_obs_maps_context_observation(mcp_mod, mock_daemon):
    mock_daemon["respond"]({"document_id": "OBS-013"})
    mcp_mod.hindsight_retain_obs(
        bank="oracle",
        document_id="OBS-013",
        content="observation body",
        derived_from="PHI-007, PHI-019",
        metadata={"source": "manual"},
    )

    body = json.loads(mock_daemon["last_request"]()["body"])
    item = body["items"][0]
    assert item["context"] == "observation"
    assert item["document_id"] == "OBS-013"
    assert item["metadata"]["derived_from"] == "PHI-007, PHI-019"


def test_hindsight_retain_session_log_no_document_id(mcp_mod, mock_daemon):
    mock_daemon["respond"]({"document_id": "SESSION-2026-04-30-123"})
    mcp_mod.hindsight_retain_session_log(
        bank="oracle",
        content="session summary text",
        metadata={"project": "Hindsight"},
    )

    body = json.loads(mock_daemon["last_request"]()["body"])
    item = body["items"][0]
    assert item["context"] == "session-log"
    assert "document_id" not in item  # daemon assigns
    assert item["metadata"]["project"] == "Hindsight"


def test_hindsight_retain_surfaces_http_error(mcp_mod, mock_daemon):
    mock_daemon["respond"]({}, status=400)
    with pytest.raises(urllib.error.HTTPError):
        mcp_mod.hindsight_retain_phi(
            bank="oracle", document_id="PHI-099", content="x"
        )


def test_hindsight_log_query_writes_to_hindsight_root(mcp_mod, tmp_path, monkeypatch):
    monkeypatch.setenv("HINDSIGHT_ROOT", str(tmp_path))
    monkeypatch.chdir("/tmp")  # CWD is somewhere else — tool must NOT use it

    result = mcp_mod.hindsight_log_query(
        client="claude-code",
        question="what is X?",
        answer="X is Y",
        recall_data={"results": [{"document_id": "PHI-001"}]},
    )

    expected_dir = tmp_path / ".decisions" / "queries"
    assert expected_dir.exists()
    log_files = list(expected_dir.glob("*.jsonl"))
    assert len(log_files) == 1
    line = log_files[0].read_text().strip().splitlines()[-1]
    parsed = json.loads(line)
    assert parsed["client"] == "claude-code"
    assert parsed["question"] == "what is X?"
    assert parsed["answer"] == "X is Y"
    assert "timestamp" in parsed
    assert result["logged_path"] == str(log_files[0])


def test_hindsight_log_query_falls_back_to_home_when_env_unset(mcp_mod, tmp_path, monkeypatch):
    fake_home = tmp_path / "fakehome"
    fake_home.mkdir()
    monkeypatch.delenv("HINDSIGHT_ROOT", raising=False)
    monkeypatch.setenv("HOME", str(fake_home))

    mcp_mod.hindsight_log_query(
        client="cli",
        question="q",
        answer="a",
        recall_data={},
    )

    expected = fake_home / "Developer" / "Hindsight" / ".decisions" / "queries"
    assert expected.exists()


def test_hindsight_log_query_never_uses_cwd(mcp_mod, tmp_path, monkeypatch):
    """Critical invariant: PHI-006 lesson. CWD must not influence write path."""
    consumer_project = tmp_path / "TravelPlanner"
    consumer_project.mkdir()
    hindsight = tmp_path / "Hindsight"
    hindsight.mkdir()
    monkeypatch.setenv("HINDSIGHT_ROOT", str(hindsight))
    monkeypatch.chdir(consumer_project)  # if tool uses cwd, it lands here

    mcp_mod.hindsight_log_query(client="x", question="q", answer="a", recall_data={})

    # The consumer project must remain untouched.
    assert not (consumer_project / ".decisions").exists()
    assert (hindsight / ".decisions" / "queries").exists()
