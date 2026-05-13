#!/usr/bin/env python3
"""Hindsight MCP server — adapts the local hindsight daemon HTTP API into typed MCP tools.

Replaces inline python3 -c HTTP heredocs in 5 oracle skills.
See: docs/superpowers/specs/2026-04-30-hindsight-mcp-server-design.md
"""
import datetime
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("hindsight")

DAEMON_URL = "http://localhost:9077"
ID_PATTERN = re.compile(r"\b(?:PHI|OBS)-\d{3,}\b")
ORACLE_EMPTY_SIGNAL = "The oracle has no entries relevant to that question."
ORACLE_QUERY_OUTCOMES = {"relevant", "empty", "irrelevant", "failure"}
ORACLE_CAPTURE_STATES = {
    "proposed",
    "approved",
    "rejected",
    "retained",
    "file-written",
    "bank-retained/file-write-failed",
    "retain-failed",
}
ORACLE_BANK_STATUSES = {"not-retained", "retained", "retain-failed"}
ORACLE_MARKDOWN_STATUSES = {"not-written", "written", "write-failed"}
RELEVANCE_GATE = (
    "RELEVANCE GATE — read each entry against the user's question. If none "
    "is genuinely relevant (i.e., addresses the question's actual subject "
    "matter, not just sharing surface keywords or topic-adjacent themes), "
    "tell the user EXACTLY: 'The oracle has no entries relevant to that "
    "question.' with no padding, summary, or near-miss listing. Empty is a "
    "valid, accepted outcome. If at least one entry is genuinely relevant, "
    "synthesize a direct answer that cites PHI-NNN / OBS-NNN identifiers "
    "(extracted from document_id or embedded in entry text), leads with the "
    "answer not the reasoning, and surfaces tensions or counter-evidence "
    "before recommendations."
)


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


def hindsight_artifact_path(*parts: str) -> Path:
    """Resolve a Hindsight-owned artifact path beneath the canonical root."""
    return _hindsight_root().joinpath(*parts)


def oracle_markdown_path(document_id: str) -> Path:
    """Return the canonical PHI/OBS markdown path anchored to HINDSIGHT_ROOT."""
    match = ID_PATTERN.fullmatch(document_id)
    if not match:
        raise ValueError("document_id must be a PHI-NNN or OBS-NNN identifier")
    folder = document_id.split("-", 1)[0].lower()
    return hindsight_artifact_path(".decisions", folder, f"{document_id}.md")


def _utc_timestamp() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _dedupe_ids(ids: list[str] | tuple[str, ...] | None) -> list[str]:
    out: list[str] = []
    for item in ids or []:
        if item not in out:
            out.append(item)
    return out


def oracle_relevance_gate_outcome(
    results: list[dict],
    *,
    accepted_ids: list[str] | None = None,
    rejection_reasons: dict | None = None,
    error: str | None = None,
) -> dict:
    """Classify recall results after the strict Oracle relevance gate."""
    retrieved_ids = _available_ids(results)
    accepted = sorted(_dedupe_ids(accepted_ids))
    reasons = dict(rejection_reasons or {})

    if error:
        outcome = "failure"
        rejected: list[str] = []
    elif not results:
        outcome = "empty"
        rejected = []
    elif accepted:
        outcome = "relevant"
        rejected = [doc_id for doc_id in retrieved_ids if doc_id not in accepted]
    else:
        outcome = "irrelevant"
        rejected = list(retrieved_ids)

    return {
        "outcome": outcome,
        "retrieved_ids": retrieved_ids,
        "accepted_ids": accepted,
        "rejected_ids": rejected,
        "rejection_reasons": {
            doc_id: reasons[doc_id] for doc_id in rejected if doc_id in reasons
        },
        "result_count": len(results),
        **({"error": error} if error else {}),
    }


def oracle_response_for_relevance_gate(gate: dict) -> str | None:
    """Return the fixed Oracle response for terminal non-synthesis outcomes."""
    outcome = gate.get("outcome")
    if outcome in {"empty", "irrelevant"}:
        return ORACLE_EMPTY_SIGNAL
    if outcome == "failure":
        error = gate.get("error", "unknown error")
        return f"Oracle unavailable — {error}"
    return None


def build_oracle_query_audit_entry(
    *,
    client: str,
    question: str,
    workflow_source: str,
    outcome: str,
    retrieved_ids: list[str] | None,
    accepted_ids: list[str] | None,
    rejected_ids: list[str] | None,
    rejection_reasons: dict | None,
    result_count: int,
    recall_substrate: str = "hindsight:oracle",
    answer: str = "",
    error: str | None = None,
    timestamp: str | None = None,
) -> dict:
    """Build the uniform Oracle query audit shape used by native and shim paths."""
    entry = {
        "timestamp": timestamp or _utc_timestamp(),
        "client": client,
        "workflow_source": workflow_source,
        "question": question,
        "answer": answer,
        "recall_substrate": recall_substrate,
        "retrieved_ids": _dedupe_ids(retrieved_ids),
        "accepted_ids": _dedupe_ids(accepted_ids),
        "rejected_ids": _dedupe_ids(rejected_ids),
        "rejection_reasons": dict(rejection_reasons or {}),
        "result_count": result_count,
        "outcome": outcome,
    }
    if error:
        entry["error"] = error
    validate_oracle_query_audit_entry(entry)
    return entry


def validate_oracle_query_audit_entry(entry: dict) -> bool:
    """Validate the canonical Oracle query audit shape."""
    required = {
        "timestamp": str,
        "client": str,
        "workflow_source": str,
        "question": str,
        "answer": str,
        "recall_substrate": str,
        "retrieved_ids": list,
        "accepted_ids": list,
        "rejected_ids": list,
        "rejection_reasons": dict,
        "result_count": int,
        "outcome": str,
    }
    for key, expected_type in required.items():
        if key not in entry:
            raise ValueError(f"missing audit field: {key}")
        if not isinstance(entry[key], expected_type):
            raise ValueError(f"audit field {key} must be {expected_type.__name__}")
    if entry["outcome"] not in ORACLE_QUERY_OUTCOMES:
        raise ValueError(f"unknown oracle query outcome: {entry['outcome']}")
    if entry["outcome"] == "failure" and "error" not in entry:
        raise ValueError("failure audit entries must include error")
    if "candidate_bodies" in entry:
        raise ValueError("candidate_bodies must not be written to query audit logs")
    return True


def build_oracle_capture_audit_entry(
    *,
    client: str,
    workflow_source: str,
    candidate_type: str,
    document_id: str,
    state: str,
    bank_status: str = "not-retained",
    markdown_status: str = "not-written",
    timestamp: str | None = None,
    error: str | None = None,
) -> dict:
    """Build the uniform Oracle capture audit shape."""
    entry = {
        "timestamp": timestamp or _utc_timestamp(),
        "client": client,
        "workflow_source": workflow_source,
        "candidate_type": candidate_type,
        "document_id": document_id,
        "state": state,
        "bank_status": bank_status,
        "markdown_status": markdown_status,
    }
    if error:
        entry["error"] = error
    validate_oracle_capture_audit_entry(entry)
    return entry


def validate_oracle_capture_audit_entry(entry: dict) -> bool:
    """Validate the canonical Oracle capture audit shape."""
    required = {
        "timestamp": str,
        "client": str,
        "workflow_source": str,
        "candidate_type": str,
        "document_id": str,
        "state": str,
        "bank_status": str,
        "markdown_status": str,
    }
    for key, expected_type in required.items():
        if key not in entry:
            raise ValueError(f"missing capture audit field: {key}")
        if not isinstance(entry[key], expected_type):
            raise ValueError(
                f"capture audit field {key} must be {expected_type.__name__}"
            )
    if entry["candidate_type"] not in {"PHI", "OBS"}:
        raise ValueError("candidate_type must be PHI or OBS")
    if entry["state"] not in ORACLE_CAPTURE_STATES:
        raise ValueError(f"unknown capture audit state: {entry['state']}")
    if entry["bank_status"] not in ORACLE_BANK_STATUSES:
        raise ValueError(f"unknown bank_status: {entry['bank_status']}")
    if entry["markdown_status"] not in ORACLE_MARKDOWN_STATUSES:
        raise ValueError(f"unknown markdown_status: {entry['markdown_status']}")
    if entry["state"] == "retain-failed" and entry["markdown_status"] != "not-written":
        raise ValueError("retain-failed entries must not have markdown written")
    return True


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
    queries_dir = hindsight_artifact_path(".decisions", "queries")
    queries_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now(datetime.timezone.utc)
    log_path = queries_dir / f"{now.year:04d}-{now.month:02d}.jsonl"
    if "outcome" in recall_data:
        entry = build_oracle_query_audit_entry(
            timestamp=now.isoformat(),
            client=client,
            question=question,
            answer=answer,
            workflow_source=recall_data.get("workflow_source", "native"),
            recall_substrate=recall_data.get("recall_substrate", "hindsight:oracle"),
            outcome=recall_data["outcome"],
            retrieved_ids=recall_data.get("retrieved_ids", []),
            accepted_ids=recall_data.get("accepted_ids", []),
            rejected_ids=recall_data.get("rejected_ids", []),
            rejection_reasons=recall_data.get("rejection_reasons", {}),
            result_count=recall_data.get("result_count", 0),
            error=recall_data.get("error"),
        )
    else:
        result_count = recall_data.get("result_count", 0)
        retrieved_ids = (
            recall_data.get("available_ids")
            or _available_ids(recall_data.get("results", []))
        )
        outcome = "empty" if recall_data.get("empty") else "relevant"
        entry = build_oracle_query_audit_entry(
            timestamp=now.isoformat(),
            client=client,
            question=question,
            answer=answer,
            workflow_source=recall_data.get("workflow_source", "legacy"),
            recall_substrate=recall_data.get("recall_substrate", "hindsight:oracle"),
            outcome=outcome,
            retrieved_ids=retrieved_ids,
            accepted_ids=retrieved_ids if outcome == "relevant" else [],
            rejected_ids=[],
            rejection_reasons={},
            result_count=result_count,
        )
    with log_path.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    return {"logged_path": str(log_path)}


def _available_ids(results: list[dict]) -> list[str]:
    ids = set()
    for item in results:
        doc_id = item.get("document_id")
        if doc_id:
            ids.add(doc_id)
        ids.update(ID_PATTERN.findall(item.get("text", "")))
    return sorted(ids)


def oracle_synthesis_envelope(question: str, results: list[dict], bank: str) -> dict:
    """Build the Oracle synthesis envelope consumed by decision-point agents."""
    missing = []
    missing_count = 1
    for index, item in enumerate(results):
        has_id = bool(item.get("document_id")) or bool(
            ID_PATTERN.findall(item.get("text", ""))
        )
        if has_id:
            continue
        marker = {
            "index": index,
            "marker": f"MISSING-ORACLE-ID-{missing_count}",
            "type": item.get("type", "unknown"),
        }
        if item.get("mentioned_at"):
            marker["mentioned_at"] = item["mentioned_at"]
        missing.append(marker)
        missing_count += 1

    gate = oracle_relevance_gate_outcome(
        results,
        accepted_ids=_available_ids(results),
    )
    return {
        "instructions": RELEVANCE_GATE,
        "recall_substrate": f"hindsight:{bank}",
        "question": question,
        "gate": gate,
        "available_ids": _available_ids(results),
        "missing_identifier_markers": missing,
        "results": results,
    }


@mcp.tool()
def hindsight_oracle_query(
    bank: str,
    question: str,
    budget: str = "mid",
    max_tokens: int = 4096,
    top_n: int = 10,
) -> str:
    """Oracle-mode query on top of hindsight recall.

    Uses the same recall stack as `hindsight_recall`, but returns an opinionated
    JSON envelope with a relevance-gate instruction for synthesis clients.
    """
    if not question or not question.strip():
        return "No question provided."

    try:
        slim = hindsight_recall(
            bank=bank,
            query=question,
            budget=budget,
            max_tokens=max_tokens,
            top_n=top_n,
            verbose=False,
        )
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        gate = oracle_relevance_gate_outcome([], error=str(exc))
        hindsight_log_query(
            client="codex-mcp",
            question=question,
            answer=oracle_response_for_relevance_gate(gate) or "",
            recall_data={
                **gate,
                "workflow_source": "native",
                "recall_substrate": f"hindsight:{bank}",
            },
        )
        return oracle_response_for_relevance_gate(gate) or "Oracle unavailable"
    if not slim:
        gate = oracle_relevance_gate_outcome([])
        hindsight_log_query(
            client="codex-mcp",
            question=question,
            answer=ORACLE_EMPTY_SIGNAL,
            recall_data={
                **gate,
                "workflow_source": "native",
                "recall_substrate": f"hindsight:{bank}",
            },
        )
        return oracle_response_for_relevance_gate(gate)

    envelope = oracle_synthesis_envelope(question=question, results=slim, bank=bank)
    hindsight_log_query(
        client="codex-mcp",
        question=question,
        answer="",
        recall_data={
            **envelope["gate"],
            "workflow_source": "native",
            "recall_substrate": f"hindsight:{bank}",
        },
    )
    return json.dumps(
        envelope,
        ensure_ascii=False,
        indent=2,
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
