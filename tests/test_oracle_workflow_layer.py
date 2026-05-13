"""Tests for the Decision Oracle workflow-layer migration.

These tests start as contract/fixture checks and expand by user story as the
workflow-layer implementation lands.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures" / "oracle_workflow"


def load_workflow_fixture(name: str) -> dict:
    return json.loads((FIXTURES / f"{name}.json").read_text())


def test_oracle_workflow_fixtures_exist():
    assert (FIXTURES / "query_audit_entries.json").exists()
    assert (FIXTURES / "capture_states.json").exists()
    assert (FIXTURES / "migration_matrix.json").exists()


def test_query_audit_fixtures_validate_against_canonical_shape(mcp_mod):
    fixtures = load_workflow_fixture("query_audit_entries")

    for name, fixture in fixtures.items():
        entry = mcp_mod.build_oracle_query_audit_entry(
            client=fixture["client"],
            question=fixture["question"],
            workflow_source=fixture["workflow_source"],
            recall_substrate=fixture["recall_substrate"],
            outcome=fixture["outcome"],
            retrieved_ids=fixture["retrieved_ids"],
            accepted_ids=fixture["accepted_ids"],
            rejected_ids=fixture["rejected_ids"],
            rejection_reasons=fixture["rejection_reasons"],
            result_count=fixture["result_count"],
            error=fixture.get("error"),
            timestamp="2026-05-04T12:00:00+00:00",
        )

        assert mcp_mod.validate_oracle_query_audit_entry(entry) is True, name
        assert entry["timestamp"] == "2026-05-04T12:00:00+00:00"
        assert entry["retrieved_ids"] == fixture["retrieved_ids"]
        assert entry["accepted_ids"] == fixture["accepted_ids"]
        assert entry["rejected_ids"] == fixture["rejected_ids"]
        assert "candidate_bodies" not in entry


def test_query_audit_validation_rejects_unknown_outcome(mcp_mod):
    entry = mcp_mod.build_oracle_query_audit_entry(
        client="claude-code",
        question="q",
        workflow_source="native",
        outcome="empty",
        retrieved_ids=[],
        accepted_ids=[],
        rejected_ids=[],
        rejection_reasons={},
        result_count=0,
        timestamp="2026-05-04T12:00:00+00:00",
    )
    entry["outcome"] = "maybe"

    with pytest.raises(ValueError, match="outcome"):
        mcp_mod.validate_oracle_query_audit_entry(entry)


def test_relevance_gate_outcome_classifies_results(mcp_mod):
    results = [
        {"document_id": "PHI-015", "text": "Uniform audit shapes matter."},
        {"text": "OBS-011 Edge cases can hide core flow."},
    ]

    relevant = mcp_mod.oracle_relevance_gate_outcome(
        results,
        accepted_ids=["PHI-015"],
        rejection_reasons={"OBS-011": "Spec-shape concern, not audit schema."},
    )
    assert relevant["outcome"] == "relevant"
    assert relevant["retrieved_ids"] == ["OBS-011", "PHI-015"]
    assert relevant["accepted_ids"] == ["PHI-015"]
    assert relevant["rejected_ids"] == ["OBS-011"]

    empty = mcp_mod.oracle_relevance_gate_outcome([])
    assert empty["outcome"] == "empty"
    assert empty["result_count"] == 0

    irrelevant = mcp_mod.oracle_relevance_gate_outcome(
        results,
        accepted_ids=[],
        rejection_reasons={
            "PHI-015": "Audit uniformity is not material.",
            "OBS-011": "Spec-shape concern is not material.",
        },
    )
    assert irrelevant["outcome"] == "irrelevant"
    assert irrelevant["rejected_ids"] == ["OBS-011", "PHI-015"]

    failure = mcp_mod.oracle_relevance_gate_outcome([], error="daemon unavailable")
    assert failure["outcome"] == "failure"
    assert failure["error"] == "daemon unavailable"


def test_review_helper_normalizes_canonical_and_legacy_entries():
    from scripts import review_oracle_queries

    canonical = load_workflow_fixture("query_audit_entries")["native_irrelevant"]
    normalized = review_oracle_queries.normalize_query_entry(canonical)
    assert normalized["timestamp"] == "?"
    assert normalized["outcome"] == "irrelevant"
    assert normalized["source"] == "native"
    assert normalized["ids"] == []
    assert normalized["rejected_ids"] == ["PHI-001"]

    legacy = {
        "timestamp": "2026-05-04T12:00:00+00:00",
        "client": "codex-mcp",
        "question": "q",
        "answer": "a",
        "recall_data": {
            "result_count": 1,
            "empty": False,
            "available_ids": ["PHI-015"],
        },
    }
    normalized = review_oracle_queries.normalize_query_entry(legacy)
    assert normalized["timestamp"] == "2026-05-04T12:00:00+00:00"
    assert normalized["outcome"] == "relevant"
    assert normalized["ids"] == ["PHI-015"]


def test_hindsight_oracle_query_returns_relevance_gate_envelope(
    mcp_mod, mock_daemon, monkeypatch, tmp_path
):
    monkeypatch.setenv("HINDSIGHT_ROOT", str(tmp_path))
    from conftest import load_fixture

    fixture = load_fixture("recall")
    mock_daemon["respond"](
        fixture,
        url="/v1/default/banks/oracle/memories/recall",
        method="POST",
    )

    result = mcp_mod.hindsight_oracle_query(
        bank="oracle",
        question="Should this use Hindsight recall?",
    )

    payload = json.loads(result)
    assert "RELEVANCE GATE" in payload["instructions"]
    assert payload["recall_substrate"] == "hindsight:oracle"
    assert payload["gate"]["outcome"] == "relevant"
    assert payload["gate"]["result_count"] == len(payload["results"])
    assert payload["gate"]["retrieved_ids"]

    request_body = json.loads(mock_daemon["last_request"]()["body"])
    assert request_body["query"] == "Should this use Hindsight recall?"

    log_path = next((tmp_path / ".decisions" / "queries").glob("*.jsonl"))
    entry = json.loads(log_path.read_text())
    assert entry["workflow_source"] == "native"
    assert entry["outcome"] == "relevant"
    assert entry["retrieved_ids"] == payload["gate"]["retrieved_ids"]
    assert entry["accepted_ids"] == payload["gate"]["accepted_ids"]


def test_oracle_skill_contract_queries_hindsight_before_recommendations():
    skill = (ROOT / ".claude" / "skills" / "oracle" / "SKILL.md").read_text()

    assert "base Hindsight recall" in skill
    assert "mcp__hindsight__hindsight_recall" in skill
    assert "RELEVANCE GATE" in skill
    assert "The oracle has no entries relevant to that question." in skill


def test_hindsight_oracle_query_empty_recall_returns_exact_signal_and_audits_empty(
    mcp_mod, mock_daemon, monkeypatch, tmp_path
):
    monkeypatch.setenv("HINDSIGHT_ROOT", str(tmp_path))
    mock_daemon["respond"](
        {"results": []},
        url="/v1/default/banks/oracle/memories/recall",
        method="POST",
    )

    result = mcp_mod.hindsight_oracle_query(
        bank="oracle",
        question="Should we use an unrelated payment vendor?",
    )

    assert result == "The oracle has no entries relevant to that question."
    log_path = next((tmp_path / ".decisions" / "queries").glob("*.jsonl"))
    entry = json.loads(log_path.read_text().strip())
    assert entry["outcome"] == "empty"
    assert entry["result_count"] == 0
    assert entry["retrieved_ids"] == []
    assert entry["accepted_ids"] == []
    assert entry["rejected_ids"] == []
    assert "error" not in entry


def test_irrelevant_gate_response_returns_exact_empty_signal(mcp_mod):
    gate = mcp_mod.oracle_relevance_gate_outcome(
        [{"document_id": "PHI-015", "text": "Uniform audit shapes matter."}],
        accepted_ids=[],
        rejection_reasons={"PHI-015": "Not material to the decision."},
    )

    assert gate["outcome"] == "irrelevant"
    assert mcp_mod.oracle_response_for_relevance_gate(gate) == (
        "The oracle has no entries relevant to that question."
    )


def test_oracle_skill_forbids_near_miss_summaries_on_empty():
    skill = (ROOT / ".claude" / "skills" / "oracle" / "SKILL.md").read_text()

    assert "Do not summarize what was retrieved." in skill
    assert "Do not list near-misses." in skill
    assert "The oracle has no entries relevant to that question." in skill


def test_synthesis_envelope_reports_available_ids_and_missing_identifier_markers(mcp_mod):
    results = [
        {
            "text": "Pattern without a citeable identifier.",
            "type": "observation",
            "mentioned_at": "2026-05-04T12:00:00+00:00",
        },
        {
            "text": "PHI-015 says audit shapes should stay uniform.",
            "type": "observation",
        },
        {
            "text": "Captured philosophy.",
            "type": "experience",
            "document_id": "PHI-003",
        },
    ]

    envelope = mcp_mod.oracle_synthesis_envelope(
        question="How should synthesis cite memories?",
        results=results,
        bank="oracle",
    )

    assert envelope["available_ids"] == ["PHI-003", "PHI-015"]
    assert envelope["missing_identifier_markers"] == [
        {
            "index": 0,
            "marker": "MISSING-ORACLE-ID-1",
            "type": "observation",
            "mentioned_at": "2026-05-04T12:00:00+00:00",
        }
    ]
    assert envelope["gate"]["retrieved_ids"] == ["PHI-003", "PHI-015"]


def test_oracle_skill_contract_requires_tensions_and_inference_separation():
    skill = (ROOT / ".claude" / "skills" / "oracle" / "SKILL.md").read_text()

    assert "surfaces tensions or counter-evidence" in skill
    assert "before stating a recommendation" in skill
    assert "distinguishes cited Oracle memory from current-session inference" in skill


def test_missing_identifier_marker_for_relevant_memory_without_document_id(mcp_mod):
    envelope = mcp_mod.oracle_synthesis_envelope(
        question="What should happen when a relevant memory lacks an ID?",
        results=[{"text": "Relevant but uncited memory.", "type": "observation"}],
        bank="oracle",
    )

    assert envelope["available_ids"] == []
    assert envelope["missing_identifier_markers"][0]["marker"] == "MISSING-ORACLE-ID-1"


def test_capture_audit_fixtures_validate_against_canonical_shape(mcp_mod):
    fixtures = load_workflow_fixture("capture_states")

    for name, fixture in fixtures.items():
        entry = mcp_mod.build_oracle_capture_audit_entry(
            client=fixture["client"],
            workflow_source=fixture["workflow_source"],
            candidate_type=fixture["candidate_type"],
            document_id=fixture["document_id"],
            state=fixture["state"],
            bank_status=fixture.get("bank_status", "not-retained"),
            markdown_status=fixture.get("markdown_status", "not-written"),
            timestamp="2026-05-04T12:00:00+00:00",
        )

        assert mcp_mod.validate_oracle_capture_audit_entry(entry) is True, name
        assert entry["timestamp"] == "2026-05-04T12:00:00+00:00"


def test_oracle_debate_requires_bank_first_markdown_retry_without_duplicate_retain():
    skill = (ROOT / ".claude" / "skills" / "oracle-debate" / "SKILL.md").read_text()

    retain_index = skill.index("mcp__hindsight__hindsight_retain_phi")
    write_index = skill.index("Write the canonical PHI file")
    assert retain_index < write_index
    assert "If retain fails, do not create the canonical markdown file" in skill
    assert "report partial success" in skill
    assert "retry or regenerate the markdown without duplicating the retained bank entry" in skill
    assert "record capture audit state" in skill


def test_oracle_preclear_requires_bank_first_markdown_retry_without_duplicate_retain():
    skill = (ROOT / ".claude" / "skills" / "oracle-preclear" / "SKILL.md").read_text()

    retain_index = skill.index("mcp__hindsight__hindsight_retain_phi")
    write_index = skill.index("Then write the derivative file")
    assert retain_index < write_index
    assert "If retain fails, do not create the canonical markdown file" in skill
    assert "report partial success" in skill
    assert "retry or regenerate the markdown without duplicating the retained bank entry" in skill


def test_oracle_observe_requires_explicit_approval_and_retain_first_contract():
    skill = (ROOT / ".claude" / "skills" / "oracle-observe" / "SKILL.md").read_text()

    assert "Wait for explicit confirmation. Never auto-retain." in skill
    assert "If retain fails, do not create the canonical markdown file" in skill
    assert "source metadata" in skill
    assert "${HINDSIGHT_ROOT:-$HOME/Developer/Hindsight}" in skill


def test_oracle_preclear_limits_candidates_and_does_not_retain_unapproved():
    skill = (ROOT / ".claude" / "skills" / "oracle-preclear" / "SKILL.md").read_text()

    assert "0–3 items" in skill
    assert "If nothing qualifies" in skill
    assert "Do not retain unapproved candidates." in skill
    assert "no filler" in skill.lower()


def test_hindsight_log_query_writes_canonical_gate_outcomes(mcp_mod, tmp_path, monkeypatch):
    monkeypatch.setenv("HINDSIGHT_ROOT", str(tmp_path))
    fixtures = load_workflow_fixture("query_audit_entries")

    for fixture in (
        fixtures["native_relevant"],
        fixtures["native_irrelevant"],
        fixtures["native_failure"],
    ):
        recall_data = {
            "workflow_source": fixture["workflow_source"],
            "recall_substrate": fixture["recall_substrate"],
            "outcome": fixture["outcome"],
            "retrieved_ids": fixture["retrieved_ids"],
            "accepted_ids": fixture["accepted_ids"],
            "rejected_ids": fixture["rejected_ids"],
            "rejection_reasons": fixture["rejection_reasons"],
            "result_count": fixture["result_count"],
            **({"error": fixture["error"]} if "error" in fixture else {}),
        }
        mcp_mod.hindsight_log_query(
            client=fixture["client"],
            question=fixture["question"],
            answer="",
            recall_data=recall_data,
        )

    log_path = next((tmp_path / ".decisions" / "queries").glob("*.jsonl"))
    entries = [json.loads(line) for line in log_path.read_text().splitlines()]
    assert [entry["outcome"] for entry in entries] == [
        "relevant",
        "irrelevant",
        "failure",
    ]
    assert entries[1]["rejected_ids"] == ["PHI-001"]
    assert entries[2]["error"] == "daemon unavailable"


def test_query_audit_omits_rejected_candidate_bodies(mcp_mod, tmp_path, monkeypatch):
    monkeypatch.setenv("HINDSIGHT_ROOT", str(tmp_path))

    mcp_mod.hindsight_log_query(
        client="claude-code",
        question="q",
        answer="",
        recall_data={
            "workflow_source": "native",
            "outcome": "irrelevant",
            "retrieved_ids": ["PHI-015"],
            "accepted_ids": [],
            "rejected_ids": ["PHI-015"],
            "rejection_reasons": {"PHI-015": "Not relevant."},
            "candidate_bodies": {"PHI-015": "full rejected text"},
            "result_count": 1,
        },
    )

    log_path = next((tmp_path / ".decisions" / "queries").glob("*.jsonl"))
    entry = json.loads(log_path.read_text())
    assert "candidate_bodies" not in entry


def test_compatibility_source_marker_is_written_to_query_audit(
    mcp_mod, tmp_path, monkeypatch
):
    monkeypatch.setenv("HINDSIGHT_ROOT", str(tmp_path))
    fixture = load_workflow_fixture("query_audit_entries")["compat_relevant"]

    mcp_mod.hindsight_log_query(
        client=fixture["client"],
        question=fixture["question"],
        answer="",
        recall_data={
            "workflow_source": fixture["workflow_source"],
            "recall_substrate": fixture["recall_substrate"],
            "outcome": fixture["outcome"],
            "retrieved_ids": fixture["retrieved_ids"],
            "accepted_ids": fixture["accepted_ids"],
            "rejected_ids": fixture["rejected_ids"],
            "rejection_reasons": fixture["rejection_reasons"],
            "result_count": fixture["result_count"],
        },
    )

    log_path = next((tmp_path / ".decisions" / "queries").glob("*.jsonl"))
    entry = json.loads(log_path.read_text())
    assert entry["workflow_source"] == "compat-shim"


def test_hindsight_oracle_query_logs_failure_attempt(
    mcp_mod, mock_daemon, monkeypatch, tmp_path
):
    monkeypatch.setenv("HINDSIGHT_ROOT", str(tmp_path))
    mock_daemon["respond"](
        {},
        url="/v1/default/banks/oracle/memories/recall",
        method="POST",
        status=500,
    )

    result = mcp_mod.hindsight_oracle_query(
        bank="oracle",
        question="Should failure attempts be auditable?",
    )

    assert result.startswith("Oracle unavailable")
    log_path = next((tmp_path / ".decisions" / "queries").glob("*.jsonl"))
    entry = json.loads(log_path.read_text())
    assert entry["outcome"] == "failure"
    assert entry["workflow_source"] == "native"
    assert "error" in entry


def test_migration_matrix_covers_required_initial_inventory_targets():
    fixture = load_workflow_fixture("migration_matrix")
    matrix = (
        ROOT / "specs" / "003-oracle-workflow-layer" / "migration-matrix.md"
    ).read_text()

    for target in fixture["required_targets"]:
        assert target in matrix


def test_exact_response_shape_is_limited_to_named_active_consumers():
    matrix = (
        ROOT / "specs" / "003-oracle-workflow-layer" / "migration-matrix.md"
    ).read_text()
    compat_server = (ROOT / "mcp" / "oracle-query" / "server.py").read_text()

    assert (
        "| `mcp/oracle-query/server.py` | mcp |" in matrix
        and "| true |" in matrix
        and "Codex Oracle connector" in matrix
    )
    assert "EXACT_SHAPE_COMPATIBILITY = True" in compat_server
    assert "compat-shim" in compat_server


def test_standalone_oracle_query_removal_gate_remains_blocked():
    matrix = (
        ROOT / "specs" / "003-oracle-workflow-layer" / "migration-matrix.md"
    ).read_text()

    assert "Native query acceptance tests:" in matrix
    assert "Native capture acceptance tests:" in matrix
    assert "Pre-clear candidate tests:" in matrix
    assert "Explicit user approval for removal:" in matrix
    assert "Manual dogfood session with no blocking regressions:" in matrix
    assert "pending" in matrix
