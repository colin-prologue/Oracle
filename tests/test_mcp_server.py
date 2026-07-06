"""Tests for hindsight MCP server tool implementations.

Daemon-shape fixtures are recorded under `tests/fixtures/daemon/` from a real
running daemon. Tests against those fixtures verify that the tool handles the
real response shape, not a hand-crafted mock that can drift silently.
"""
import json
import urllib.error

import pytest

from conftest import load_fixture


# ---------------------------------------------------------------------------
# Module load
# ---------------------------------------------------------------------------


def test_server_module_imports(mcp_mod):
    assert mcp_mod.DAEMON_URL == "http://localhost:9077"
    assert mcp_mod.mcp.name == "hindsight"


# ---------------------------------------------------------------------------
# hindsight_stats
# ---------------------------------------------------------------------------


def test_hindsight_stats_returns_real_daemon_shape(mcp_mod, mock_daemon):
    """Tool returns the daemon body verbatim — verified against recorded shape."""
    fixture = load_fixture("stats")
    mock_daemon["respond"](
        fixture, url="/v1/default/banks/oracle/stats", method="GET",
    )
    result = mcp_mod.hindsight_stats(bank="oracle")
    assert result == fixture
    # Pin the real-daemon contract: these keys must be present.
    for key in ("bank_id", "total_nodes", "total_documents", "total_observations"):
        assert key in result, f"daemon contract regression: missing {key!r}"


def test_hindsight_stats_surfaces_http_error(mcp_mod, mock_daemon):
    mock_daemon["respond"](
        {}, url="/v1/default/banks/oracle/stats", method="GET", status=503,
    )
    with pytest.raises(urllib.error.HTTPError):
        mcp_mod.hindsight_stats(bank="oracle")


# ---------------------------------------------------------------------------
# hindsight_list_documents
# ---------------------------------------------------------------------------


def test_hindsight_list_documents_returns_real_daemon_shape(mcp_mod, mock_daemon):
    fixture = load_fixture("documents")
    mock_daemon["respond"](
        fixture, url="/v1/default/banks/oracle/documents?limit=200&offset=0", method="GET",
    )
    result = mcp_mod.hindsight_list_documents(bank="oracle")
    assert len(result) == len(fixture["items"])
    # Real items carry these keys; assert them so a daemon shape change shows up.
    item = result[0]
    for key in ("id", "bank_id", "document_metadata", "created_at"):
        assert key in item, f"daemon contract regression: missing {key!r}"


def test_hindsight_list_documents_with_prefix_filters_client_side(mcp_mod, mock_daemon):
    fixture = load_fixture("documents")
    mock_daemon["respond"](
        fixture, url="/v1/default/banks/oracle/documents?limit=200&offset=0", method="GET",
    )
    result = mcp_mod.hindsight_list_documents(bank="oracle", prefix="PHI-")
    assert all(d["id"].startswith("PHI-") for d in result)
    # Fixture has at least one PHI- and at least one non-PHI item.
    assert len(result) >= 1
    assert len(result) < len(fixture["items"])


def test_hindsight_list_documents_handles_missing_items_key(mcp_mod, mock_daemon):
    """Daemon shape change protection: tool returns [] not raises KeyError.

    Tradeoff (PHI-014 tension): silently returning [] hides daemon-shape regressions.
    Today the tool prefers tolerance; if the daemon ever reshapes /documents, the
    contract-shape assertion in `test_hindsight_list_documents_returns_real_daemon_shape`
    is the canary — not this test.
    """
    mock_daemon["respond"](
        {}, url="/v1/default/banks/oracle/documents?limit=200&offset=0", method="GET",
    )
    assert mcp_mod.hindsight_list_documents(bank="oracle") == []


def test_hindsight_list_documents_paginates_past_first_page(mcp_mod, mock_daemon):
    """Daemon pages at `limit` per response; the tool must follow offset to total.

    Regression: the daemon's default page size is 100 and the tool used to
    issue a single unparameterized GET, silently truncating a 102-document
    bank to 100.
    """
    page1 = [{"id": f"DOC-{i:03d}"} for i in range(200)]
    page2 = [{"id": f"DOC-{i:03d}"} for i in range(200, 250)]
    mock_daemon["respond"](
        {"items": page1, "total": 250, "limit": 200, "offset": 0},
        url="/v1/default/banks/oracle/documents?limit=200&offset=0", method="GET",
    )
    mock_daemon["respond"](
        {"items": page2, "total": 250, "limit": 200, "offset": 200},
        url="/v1/default/banks/oracle/documents?limit=200&offset=200", method="GET",
    )
    result = mcp_mod.hindsight_list_documents(bank="oracle")
    assert len(result) == 250
    assert result[0]["id"] == "DOC-000"
    assert result[-1]["id"] == "DOC-249"


def test_hindsight_list_documents_prefix_filters_across_all_pages(mcp_mod, mock_daemon):
    """The prefix filter must apply over the COMPLETE set, not just page one.

    Regression: OBS-001/OBS-002 sat past row 100 and were missed by the filter.
    """
    page1 = [{"id": f"PHI-{i:03d}"} for i in range(200)]
    page2 = [{"id": "OBS-001"}, {"id": "OBS-002"}]
    mock_daemon["respond"](
        {"items": page1, "total": 202, "limit": 200, "offset": 0},
        url="/v1/default/banks/oracle/documents?limit=200&offset=0", method="GET",
    )
    mock_daemon["respond"](
        {"items": page2, "total": 202, "limit": 200, "offset": 200},
        url="/v1/default/banks/oracle/documents?limit=200&offset=200", method="GET",
    )
    result = mcp_mod.hindsight_list_documents(bank="oracle", prefix="OBS-")
    assert [d["id"] for d in result] == ["OBS-001", "OBS-002"]


def test_hindsight_list_documents_warns_when_daemon_caps_response(mcp_mod, mock_daemon, capsys):
    """If the daemon stops serving pages before `total`, warn on stderr.

    Silent truncation is the bug this tool had; if the daemon ever reintroduces
    it server-side (short page + no more items), the caller must be told.
    """
    page1 = [{"id": f"DOC-{i:03d}"} for i in range(80)]
    mock_daemon["respond"](
        {"items": page1, "total": 150, "limit": 200, "offset": 0},
        url="/v1/default/banks/oracle/documents?limit=200&offset=0", method="GET",
    )
    mock_daemon["respond"](
        {"items": [], "total": 150, "limit": 200, "offset": 80},
        url="/v1/default/banks/oracle/documents?limit=200&offset=80", method="GET",
    )
    result = mcp_mod.hindsight_list_documents(bank="oracle")
    assert len(result) == 80
    err = capsys.readouterr().err
    assert "total=150" in err
    assert "80" in err
    assert "incomplete" in err


# ---------------------------------------------------------------------------
# _project_slim
# ---------------------------------------------------------------------------


def test_slim_projection_against_real_recall_shape(mcp_mod):
    """Slim projection must drop every field the real daemon returns except
    {text, type, document_id, mentioned_at, metadata}.
    """
    fixture = load_fixture("recall")
    slim = mcp_mod._project_slim(fixture["results"])
    allowed_keys = {"text", "type", "document_id", "mentioned_at", "metadata"}
    for entry in slim:
        extra = set(entry.keys()) - allowed_keys
        assert not extra, f"slim projection leaked daemon-internal keys: {extra}"
        # Required-field present-ness — the slim shape Claude consumes.
        assert "text" in entry
        assert "type" in entry


def test_slim_projection_drops_none_valued_fields(mcp_mod):
    raw = [
        {
            "text": "t",
            "type": "experience",
            "document_id": "PHI-001",
            "mentioned_at": "2026-04-25T01:00:00+00:00",
            "metadata": {"d": "x"},
            "score": 0.9,
            "rank": 0,
        },
        {
            "text": "t2",
            "type": "observation",
            "document_id": None,
            "mentioned_at": "2026-04-21T22:00:00+00:00",
            "metadata": None,
            "score": 0.8,
        },
    ]
    slim = mcp_mod._project_slim(raw)
    assert "document_id" not in slim[1]
    assert "metadata" not in slim[1]
    assert "score" not in slim[0]


# ---------------------------------------------------------------------------
# hindsight_recall
# ---------------------------------------------------------------------------


RECALL_URL = "/v1/default/banks/oracle/memories/recall"


def test_hindsight_recall_default_slim_against_real_shape(mcp_mod, mock_daemon):
    """Real recall results carry 13 fields; slim must drop all but the 5 allowed."""
    fixture = load_fixture("recall")
    mock_daemon["respond"](fixture, url=RECALL_URL, method="POST")
    result = mcp_mod.hindsight_recall(bank="oracle", query="test query")

    body = json.loads(mock_daemon["last_request"]()["body"])
    assert body["query"] == "test query"
    assert body["budget"] == "mid"
    assert body["max_tokens"] == 4096

    allowed_keys = {"text", "type", "document_id", "mentioned_at", "metadata"}
    for entry in result:
        assert set(entry.keys()) <= allowed_keys


def test_hindsight_recall_verbose_returns_full_response(mcp_mod, mock_daemon):
    fixture = load_fixture("recall")
    mock_daemon["respond"](fixture, url=RECALL_URL, method="POST")
    result = mcp_mod.hindsight_recall(bank="oracle", query="q", verbose=True)
    assert result == fixture
    # Verbose path leaks daemon-internal keys deliberately — assert one is present.
    assert "trace" in result


def test_hindsight_recall_top_n_truncates(mcp_mod, mock_daemon):
    mock_daemon["respond"](
        {"results": [
            {"text": f"t{i}", "type": "experience", "mentioned_at": "2026-04-25T01:00:00+00:00"}
            for i in range(20)
        ]},
        url=RECALL_URL, method="POST",
    )
    result = mcp_mod.hindsight_recall(bank="oracle", query="q", top_n=5)
    assert len(result) == 5


def test_hindsight_recall_passes_budget_and_max_tokens(mcp_mod, mock_daemon):
    mock_daemon["respond"]({"results": []}, url=RECALL_URL, method="POST")
    mcp_mod.hindsight_recall(bank="oracle", query="q", budget="high", max_tokens=8192)
    body = json.loads(mock_daemon["last_request"]()["body"])
    assert body["budget"] == "high"
    assert body["max_tokens"] == 8192


def test_hindsight_recall_handles_missing_results_key(mcp_mod, mock_daemon):
    """Daemon shape change protection: missing 'results' yields [].

    Same PHI-014 tradeoff as list_documents — the contract test against the
    real recall shape is the canary, not this tolerance.
    """
    mock_daemon["respond"]({}, url=RECALL_URL, method="POST")
    assert mcp_mod.hindsight_recall(bank="oracle", query="q") == []


def test_hindsight_recall_surfaces_http_error(mcp_mod, mock_daemon):
    mock_daemon["respond"]({}, url=RECALL_URL, method="POST", status=500)
    with pytest.raises(urllib.error.HTTPError):
        mcp_mod.hindsight_recall(bank="oracle", query="q")


# ---------------------------------------------------------------------------
# hindsight_oracle_query
# ---------------------------------------------------------------------------


def test_hindsight_oracle_query_returns_gate_and_results(mcp_mod, mock_daemon, monkeypatch, tmp_path):
    monkeypatch.setenv("HINDSIGHT_ROOT", str(tmp_path))
    fixture = load_fixture("recall")
    mock_daemon["respond"](fixture, url=RECALL_URL, method="POST")
    result = mcp_mod.hindsight_oracle_query(bank="oracle", question="q")
    payload = json.loads(result)
    assert "RELEVANCE GATE" in payload["instructions"]
    assert isinstance(payload["results"], list)
    assert payload["results"]


def test_hindsight_oracle_query_handles_empty_question(mcp_mod):
    assert mcp_mod.hindsight_oracle_query(bank="oracle", question="   ") == "No question provided."


# ---------------------------------------------------------------------------
# hindsight_retain_phi / retain_obs / retain_session_log
# ---------------------------------------------------------------------------


RETAIN_URL = "/v1/default/banks/oracle/memories"


def test_hindsight_retain_phi_maps_context_and_metadata(mcp_mod, mock_daemon):
    mock_daemon["respond"]({"items": []}, url=f"{DOCS_URL}?limit=200&offset=0", method="GET")
    mock_daemon["respond"](
        {"document_id": "PHI-020", "mentioned_at": "2026-04-30T03:30:00+00:00"},
        url=RETAIN_URL, method="POST",
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
    mock_daemon["respond"]({"items": []}, url=f"{DOCS_URL}?limit=200&offset=0", method="GET")
    mock_daemon["respond"](
        {"document_id": "PHI-021"}, url=RETAIN_URL, method="POST",
    )
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
    mock_daemon["respond"](
        {"document_id": "PHI-099"}, url=RETAIN_URL, method="POST",
    )
    with pytest.raises(ValueError, match="derived_from"):
        mcp_mod.hindsight_retain_phi(
            bank="oracle",
            document_id="PHI-099",
            content="body",
            metadata={"derived_from": "OBS-001", "domain": "x"},
        )


def test_retain_rejects_derived_from_in_metadata_even_without_kwarg(mcp_mod, mock_daemon):
    """The rejection is unconditional — not just a precedence-conflict check."""
    mock_daemon["respond"](
        {"document_id": "OBS-099"}, url=RETAIN_URL, method="POST",
    )
    with pytest.raises(ValueError, match="derived_from"):
        mcp_mod.hindsight_retain_obs(
            bank="oracle",
            document_id="OBS-099",
            content="body",
            metadata={"derived_from": "PHI-001"},
        )


def test_hindsight_retain_obs_maps_context_observation(mcp_mod, mock_daemon):
    mock_daemon["respond"]({"items": []}, url=f"{DOCS_URL}?limit=200&offset=0", method="GET")
    mock_daemon["respond"](
        {"document_id": "OBS-013"}, url=RETAIN_URL, method="POST",
    )
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
    mock_daemon["respond"](
        {"document_id": "SESSION-2026-04-30-123"}, url=RETAIN_URL, method="POST",
    )
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
    mock_daemon["respond"](
        {"items": []}, url=f"{DOCS_URL}?limit=200&offset=0", method="GET",  # collision-check finds nothing
    )
    mock_daemon["respond"](
        {}, url=RETAIN_URL, method="POST", status=400,
    )
    with pytest.raises(urllib.error.HTTPError):
        mcp_mod.hindsight_retain_phi(
            bank="oracle", document_id="PHI-099", content="x"
        )


# ---------------------------------------------------------------------------
# hindsight_delete_document — destructive, bank-only, by id
# ---------------------------------------------------------------------------


def test_delete_document_issues_delete_to_id_route(mcp_mod, mock_daemon):
    mock_daemon["respond"](
        {"document_id": "OBS-099", "deleted": True},
        url="/v1/default/banks/oracle/documents/OBS-099", method="DELETE",
    )
    result = mcp_mod.hindsight_delete_document(bank="oracle", document_id="OBS-099")

    req = mock_daemon["last_request"]()
    assert req["method"] == "DELETE"
    assert req["url"].endswith("/v1/default/banks/oracle/documents/OBS-099")
    assert result["deleted"] is True


def test_delete_document_handles_empty_204_body(mcp_mod, mock_daemon):
    """Daemon may answer a delete with 204/no body — tool returns a useful dict."""
    mock_daemon["respond"](
        None,  # empty body
        url="/v1/default/banks/oracle/documents/OBS-099", method="DELETE",
    )
    result = mcp_mod.hindsight_delete_document(bank="oracle", document_id="OBS-099")
    assert result == {"document_id": "OBS-099", "deleted": True}


def test_delete_document_surfaces_http_error(mcp_mod, mock_daemon):
    mock_daemon["respond"](
        {}, url="/v1/default/banks/oracle/documents/NOPE-001",
        method="DELETE", status=404,
    )
    with pytest.raises(urllib.error.HTTPError):
        mcp_mod.hindsight_delete_document(bank="oracle", document_id="NOPE-001")


# ---------------------------------------------------------------------------
# collision guard — retain must not silently overwrite an existing document_id
# (the daemon upserts by id; without this guard a duplicate id is data loss)
# ---------------------------------------------------------------------------


DOCS_URL = "/v1/default/banks/oracle/documents"


def test_retain_phi_rejects_existing_document_id(mcp_mod, mock_daemon):
    """A PHI whose id already exists is refused — no overwrite POST is sent."""
    mock_daemon["respond"](
        {"items": [{"id": "PHI-033"}, {"id": "PHI-034"}]},
        url=f"{DOCS_URL}?limit=200&offset=0", method="GET",
    )
    with pytest.raises(ValueError, match="already exists"):
        mcp_mod.hindsight_retain_phi(
            bank="oracle", document_id="PHI-033", content="body",
        )
    # the guard's GET is the last call — no POST escaped
    assert mock_daemon["last_request"]()["method"] == "GET"


def test_retain_obs_rejects_existing_document_id(mcp_mod, mock_daemon):
    mock_daemon["respond"](
        {"items": [{"id": "OBS-018"}]}, url=f"{DOCS_URL}?limit=200&offset=0", method="GET",
    )
    with pytest.raises(ValueError, match="already exists"):
        mcp_mod.hindsight_retain_obs(
            bank="oracle", document_id="OBS-018", content="body",
        )
    assert mock_daemon["last_request"]()["method"] == "GET"


def test_retain_phi_proceeds_when_id_is_new(mcp_mod, mock_daemon):
    """A genuinely new id passes the guard and is retained."""
    mock_daemon["respond"](
        {"items": [{"id": "PHI-034"}]}, url=f"{DOCS_URL}?limit=200&offset=0", method="GET",
    )
    mock_daemon["respond"](
        {"document_id": "PHI-035"}, url=RETAIN_URL, method="POST",
    )
    result = mcp_mod.hindsight_retain_phi(
        bank="oracle", document_id="PHI-035", content="body",
    )
    assert result["document_id"] == "PHI-035"
    assert mock_daemon["last_request"]()["method"] == "POST"


def test_retain_collision_guard_sees_ids_beyond_first_page(mcp_mod, mock_daemon):
    """The guard must check the COMPLETE document list, not the first page.

    Regression companion to the list_documents truncation bug: an existing id
    sitting past row 100 (e.g. OBS-001 in a 102-doc bank) used to pass the
    guard and get silently overwritten by the daemon's upsert.
    """
    page1 = [{"id": f"PHI-{i:03d}"} for i in range(200)]
    mock_daemon["respond"](
        {"items": page1, "total": 201, "limit": 200, "offset": 0},
        url=f"{DOCS_URL}?limit=200&offset=0", method="GET",
    )
    mock_daemon["respond"](
        {"items": [{"id": "OBS-001"}], "total": 201, "limit": 200, "offset": 200},
        url=f"{DOCS_URL}?limit=200&offset=200", method="GET",
    )
    with pytest.raises(ValueError, match="already exists"):
        mcp_mod.hindsight_retain_obs(
            bank="oracle", document_id="OBS-001", content="body",
        )
    # the guard's paging GETs are the only calls — no POST escaped
    assert mock_daemon["last_request"]()["method"] == "GET"


def test_retain_phi_allow_overwrite_skips_guard_and_updates(mcp_mod, mock_daemon):
    """allow_overwrite=True is the explicit, intentional update path.

    No collision-check GET is made — the caller has asserted intent to replace.
    """
    mock_daemon["respond"](
        {"document_id": "PHI-033"}, url=RETAIN_URL, method="POST",
    )
    result = mcp_mod.hindsight_retain_phi(
        bank="oracle", document_id="PHI-033", content="corrected body",
        allow_overwrite=True,
    )
    assert result["document_id"] == "PHI-033"
    # only one call happened, and it was the POST (no guard GET)
    assert mock_daemon["last_request"]()["method"] == "POST"


# ---------------------------------------------------------------------------
# hindsight_log_query — file-write tool, no daemon
# ---------------------------------------------------------------------------


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


def test_hindsight_artifact_path_anchors_queries_and_markdown_to_hindsight_root(
    mcp_mod, tmp_path, monkeypatch
):
    consumer_project = tmp_path / "TravelPlanner"
    consumer_project.mkdir()
    hindsight = tmp_path / "Hindsight"
    hindsight.mkdir()
    monkeypatch.setenv("HINDSIGHT_ROOT", str(hindsight))
    monkeypatch.chdir(consumer_project)

    assert mcp_mod.hindsight_artifact_path(".decisions", "queries") == (
        hindsight / ".decisions" / "queries"
    )
    assert mcp_mod.oracle_markdown_path("PHI-015") == (
        hindsight / ".decisions" / "phi" / "PHI-015.md"
    )
    assert mcp_mod.oracle_markdown_path("OBS-011") == (
        hindsight / ".decisions" / "obs" / "OBS-011.md"
    )
    assert not (consumer_project / ".decisions").exists()
