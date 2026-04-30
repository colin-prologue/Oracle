# Hindsight MCP Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace inline `python3 -c "import json, urllib.request..."` HTTP heredocs across 5 oracle skills with a typed Python MCP server, eliminating two over-broad shell-allowlist entries and `/tmp` cross-session collision risk.

**Architecture:** Python MCP server using FastMCP, stdio transport, registered at user-level so oracle skills work cross-project. Server is a thin adapter — skills call `mcp__hindsight__*` typed tools, server translates to existing daemon HTTP at `localhost:9077`. Daemon API unchanged.

**Tech Stack:** Python 3.14, `mcp` SDK (FastMCP), `urllib.request` (stdlib HTTP), `pytest` for tests, daemon HTTP at `localhost:9077`.

**Spec:** `docs/superpowers/specs/2026-04-30-hindsight-mcp-server-design.md`

---

## File structure

**Create:**
- `scripts/mcp_server.py` — MCP server with 7 tools (single file; small enough to keep one-purpose)
- `tests/test_mcp_server.py` — pytest unit tests (mocks daemon HTTP)
- `tests/conftest.py` — shared fixtures (mock urllib.request.urlopen)

**Modify:**
- `.claude/skills/oracle/SKILL.md` — replace daemon python3 heredocs with MCP tool calls; remove `/tmp/oracle_q.txt` staging (typed args)
- `.claude/skills/oracle-debate/SKILL.md` — replace retain heredoc with `hindsight_retain_phi`
- `.claude/skills/oracle-observe/SKILL.md` — replace 2 heredocs with MCP calls; remove `/tmp/oracle_observation.txt` staging
- `.claude/skills/oracle-preclear/SKILL.md` — replace 4 heredocs with MCP calls; preserve write-ordering invariant
- `.claude/skills/oracle-synthesize/SKILL.md` — replace heredocs with MCP calls; remove `/tmp/oracle_synthesize_*` staging
- `~/.claude.json` (user-level) — register hindsight MCP server (NOT in Hindsight repo — see spec deferral #4)
- `~/.claude/settings.json` (user-level) — remove 2 bash patterns, add 7 MCP tool grants

**Delete (post-migration):**
- `scripts/log_oracle_query.py` — superseded by `hindsight_log_query` MCP tool

**Decision records (separate landing):**
- `.claude/.decisions/ADR-mcp-server-integration.md`
- `.claude/.decisions/CDR-mcp-tool-taxonomy.md`
- `.decisions/log/LOG-mcp-server-migration.md` (or wherever LOG records live; check repo convention)

---

## Phase 1 — MCP server foundation

### Task 1: Verify MCP Python SDK availability

**Files:** none (environment verification)

- [ ] **Step 1.1: Check current Python version**

```bash
python3 --version
```
Expected: `Python 3.14.x` (or compatible). If older, install Python 3.14 via pyenv or system package.

- [ ] **Step 1.2: Verify `uvx` is available** (for ephemeral dependency runs)

```bash
which uvx
```
Expected: a path. If missing, install: `brew install uv` or `pip install uv`.

- [ ] **Step 1.3: Verify `mcp` Python SDK installable**

```bash
uvx --from mcp mcp --version 2>&1 | head -5
```
Expected: a version string (or installs on first run, takes ~30 seconds). If install fails, debug uvx config.

- [ ] **Step 1.4: Test FastMCP import in a throwaway script**

```bash
uvx --from mcp python3 -c "from mcp.server.fastmcp import FastMCP; print(FastMCP.__module__)"
```
Expected: `mcp.server.fastmcp`. Confirms FastMCP is the installable framework path.

No commit (this task is environment verification only).

---

### Task 2: Create empty MCP server scaffold

**Files:**
- Create: `scripts/mcp_server.py`

- [ ] **Step 2.1: Write minimal FastMCP scaffold**

Create `scripts/mcp_server.py` with this exact content:

```python
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
```

- [ ] **Step 2.2: Verify syntax**

```bash
python3 -c "import ast; ast.parse(open('scripts/mcp_server.py').read())"
```
Expected: no output (parse succeeded).

- [ ] **Step 2.3: Smoke-test stdio handshake**

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' | uvx --from mcp python3 scripts/mcp_server.py
```
Expected: a JSON-RPC `initialize` response on stdout (single line). The server starts, handles one request, then waits for more. **You will need to Ctrl-C to exit** — that's expected for stdio servers.

- [ ] **Step 2.4: Commit**

```bash
git add scripts/mcp_server.py
git commit -m "feat(mcp): add empty hindsight MCP server scaffold"
```

---

### Task 3: Set up pytest infrastructure

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/test_mcp_server.py`

- [ ] **Step 3.1: Verify pytest is available**

```bash
uvx pytest --version
```
Expected: a version string.

- [ ] **Step 3.2: Create conftest.py with urllib.request mock fixture**

Create `tests/conftest.py`:

```python
"""Shared test fixtures for hindsight MCP server tests."""
import io
import json
from unittest.mock import patch

import pytest


@pytest.fixture
def mock_daemon():
    """Mock urllib.request.urlopen calls to the hindsight daemon.

    Yields a function `respond(payload_dict)` that registers the next response.
    Test bodies call respond() before invoking the MCP tool, then assert on the
    captured request via the returned 'last_request' callable.
    """
    captured = {"url": None, "method": None, "headers": {}, "body": None}
    next_response = {"data": None}

    class MockResponse:
        def __init__(self, body_bytes: bytes):
            self._body = body_bytes

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return self._body

    def fake_urlopen(req, *, timeout=None):
        captured["url"] = req.full_url
        captured["method"] = req.get_method()
        captured["headers"] = dict(req.headers)
        captured["body"] = req.data.decode() if req.data else None
        body = json.dumps(next_response["data"]).encode()
        return MockResponse(body)

    def respond(payload):
        next_response["data"] = payload

    def last_request():
        return dict(captured)

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        yield {"respond": respond, "last_request": last_request}
```

- [ ] **Step 3.3: Create test file with one smoke test**

Create `tests/test_mcp_server.py`:

```python
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
```

- [ ] **Step 3.4: Run the smoke test**

```bash
uvx --from mcp --with pytest pytest tests/test_mcp_server.py::test_server_module_imports -v
```
Expected: PASS.

- [ ] **Step 3.5: Commit**

```bash
git add tests/conftest.py tests/test_mcp_server.py
git commit -m "test(mcp): add pytest infra with daemon-HTTP mock fixture"
```

---

## Phase 2 — Read-only tools

### Task 4: `hindsight_stats` tool

**Files:**
- Modify: `scripts/mcp_server.py` — append tool
- Modify: `tests/test_mcp_server.py` — append test

- [ ] **Step 4.1: Write failing test**

Append to `tests/test_mcp_server.py`:

```python
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
```

- [ ] **Step 4.2: Run test, verify failure**

```bash
uvx --from mcp --with pytest pytest tests/test_mcp_server.py::test_hindsight_stats_calls_daemon_and_returns_response -v
```
Expected: FAIL — `AttributeError: module 'scripts.mcp_server' has no attribute 'hindsight_stats'`.

- [ ] **Step 4.3: Implement the tool**

In `scripts/mcp_server.py`, add after the `DAEMON_URL` line:

```python
import json
import urllib.request


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
```

- [ ] **Step 4.4: Run test, verify pass**

```bash
uvx --from mcp --with pytest pytest tests/test_mcp_server.py::test_hindsight_stats_calls_daemon_and_returns_response -v
```
Expected: PASS.

- [ ] **Step 4.5: Commit**

```bash
git add scripts/mcp_server.py tests/test_mcp_server.py
git commit -m "feat(mcp): add hindsight_stats tool"
```

---

### Task 5: `hindsight_list_documents` tool

**Files:**
- Modify: `scripts/mcp_server.py`
- Modify: `tests/test_mcp_server.py`

- [ ] **Step 5.1: Write failing test**

Append to `tests/test_mcp_server.py`:

```python
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
```

- [ ] **Step 5.2: Run tests, verify failure**

```bash
uvx --from mcp --with pytest pytest tests/test_mcp_server.py -k list_documents -v
```
Expected: FAIL — `AttributeError: ... has no attribute 'hindsight_list_documents'`.

- [ ] **Step 5.3: Implement the tool**

Append to `scripts/mcp_server.py`:

```python
@mcp.tool()
def hindsight_list_documents(bank: str, prefix: str | None = None) -> list[dict]:
    """List documents in the bank. If prefix is given (e.g., "PHI-"), filter client-side."""
    body = _get(f"/v1/default/banks/{bank}/documents")
    items = body.get("items", [])
    if prefix:
        items = [d for d in items if d.get("id", "").startswith(prefix)]
    return items
```

- [ ] **Step 5.4: Run tests, verify pass**

```bash
uvx --from mcp --with pytest pytest tests/test_mcp_server.py -k list_documents -v
```
Expected: 2 PASSED.

- [ ] **Step 5.5: Commit**

```bash
git add scripts/mcp_server.py tests/test_mcp_server.py
git commit -m "feat(mcp): add hindsight_list_documents tool with prefix filter"
```

---

### Task 6: Slim shape projection (pure function)

**Files:**
- Modify: `scripts/mcp_server.py`
- Modify: `tests/test_mcp_server.py`

- [ ] **Step 6.1: Write failing test for the slim projector**

Append to `tests/test_mcp_server.py`:

```python
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
```

- [ ] **Step 6.2: Run test, verify failure**

```bash
uvx --from mcp --with pytest pytest tests/test_mcp_server.py::test_slim_projection_keeps_required_fields_drops_others -v
```
Expected: FAIL — `AttributeError: ... no attribute '_project_slim'`.

- [ ] **Step 6.3: Implement the projector**

Append to `scripts/mcp_server.py`:

```python
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
```

- [ ] **Step 6.4: Run test, verify pass**

```bash
uvx --from mcp --with pytest pytest tests/test_mcp_server.py::test_slim_projection_keeps_required_fields_drops_others -v
```
Expected: PASS.

- [ ] **Step 6.5: Commit**

```bash
git add scripts/mcp_server.py tests/test_mcp_server.py
git commit -m "feat(mcp): add _project_slim projector for recall results"
```

---

### Task 7: `hindsight_recall` tool with slim default + verbose flag

**Files:**
- Modify: `scripts/mcp_server.py`
- Modify: `tests/test_mcp_server.py`

- [ ] **Step 7.1: Write failing tests**

Append to `tests/test_mcp_server.py`:

```python
def test_hindsight_recall_default_slim(mock_daemon):
    sys.path.insert(0, ".")
    if "scripts.mcp_server" in sys.modules:
        del sys.modules["scripts.mcp_server"]
    mod = importlib.import_module("scripts.mcp_server")

    mock_daemon["respond"]({"results": [
        {"text": "t1", "type": "experience", "document_id": "PHI-001",
         "mentioned_at": "2026-04-25T01:00:00+00:00", "metadata": {"d": "x"}, "score": 0.9},
        {"text": "t2", "type": "observation", "document_id": None,
         "mentioned_at": "2026-04-21T22:00:00+00:00", "metadata": None, "score": 0.8},
    ]})
    result = mod.hindsight_recall(bank="oracle", query="test query")

    req = mock_daemon["last_request"]()
    assert req["url"] == "http://localhost:9077/v1/default/banks/oracle/memories/recall"
    assert req["method"] == "POST"
    body = json.loads(req["body"])
    assert body["query"] == "test query"
    assert body["budget"] == "mid"
    assert body["max_tokens"] == 4096

    assert "score" not in result[0]
    assert result[0]["document_id"] == "PHI-001"
    assert "metadata" not in result[1]


def test_hindsight_recall_verbose_returns_full_response(mock_daemon):
    sys.path.insert(0, ".")
    if "scripts.mcp_server" in sys.modules:
        del sys.modules["scripts.mcp_server"]
    mod = importlib.import_module("scripts.mcp_server")

    raw = {"results": [{"text": "t1", "type": "experience", "score": 0.9}], "meta": "anything"}
    mock_daemon["respond"](raw)
    result = mod.hindsight_recall(bank="oracle", query="q", verbose=True)
    assert result == raw


def test_hindsight_recall_top_n_truncates(mock_daemon):
    sys.path.insert(0, ".")
    if "scripts.mcp_server" in sys.modules:
        del sys.modules["scripts.mcp_server"]
    mod = importlib.import_module("scripts.mcp_server")

    mock_daemon["respond"]({"results": [
        {"text": f"t{i}", "type": "experience", "mentioned_at": "2026-04-25T01:00:00+00:00"}
        for i in range(20)
    ]})
    result = mod.hindsight_recall(bank="oracle", query="q", top_n=5)
    assert len(result) == 5


def test_hindsight_recall_passes_budget_and_max_tokens(mock_daemon):
    sys.path.insert(0, ".")
    if "scripts.mcp_server" in sys.modules:
        del sys.modules["scripts.mcp_server"]
    mod = importlib.import_module("scripts.mcp_server")

    mock_daemon["respond"]({"results": []})
    mod.hindsight_recall(bank="oracle", query="q", budget="high", max_tokens=8192)
    body = json.loads(mock_daemon["last_request"]()["body"])
    assert body["budget"] == "high"
    assert body["max_tokens"] == 8192
```

Add `import json` at the top of the test file if not already imported.

- [ ] **Step 7.2: Run tests, verify failure**

```bash
uvx --from mcp --with pytest pytest tests/test_mcp_server.py -k recall -v
```
Expected: FAIL — `AttributeError: ... no attribute 'hindsight_recall'`.

- [ ] **Step 7.3: Implement the tool**

Append to `scripts/mcp_server.py`:

```python
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
```

- [ ] **Step 7.4: Run tests, verify pass**

```bash
uvx --from mcp --with pytest pytest tests/test_mcp_server.py -k recall -v
```
Expected: 4 PASSED.

- [ ] **Step 7.5: Commit**

```bash
git add scripts/mcp_server.py tests/test_mcp_server.py
git commit -m "feat(mcp): add hindsight_recall with slim default and verbose flag"
```

---

## Phase 3 — Write tools

### Task 8: `hindsight_retain_phi` tool

**Files:**
- Modify: `scripts/mcp_server.py`
- Modify: `tests/test_mcp_server.py`

- [ ] **Step 8.1: Write failing test**

Append to `tests/test_mcp_server.py`:

```python
def test_hindsight_retain_phi_maps_context_and_metadata(mock_daemon):
    sys.path.insert(0, ".")
    if "scripts.mcp_server" in sys.modules:
        del sys.modules["scripts.mcp_server"]
    mod = importlib.import_module("scripts.mcp_server")

    mock_daemon["respond"]({"document_id": "PHI-020", "mentioned_at": "2026-04-30T03:30:00+00:00"})
    result = mod.hindsight_retain_phi(
        bank="oracle",
        document_id="PHI-020",
        content="## PHI-020 — Test\n\nphilosophy body",
        derived_from="OBS-001",
        metadata={"domain": "architecture", "source": "oracle-debate"},
    )

    req = mock_daemon["last_request"]()
    assert req["url"] == "http://localhost:9077/v1/default/banks/oracle/memories"
    assert req["method"] == "POST"
    body = json.loads(req["body"])
    item = body["items"][0]
    assert item["context"] == "philosophy"
    assert item["document_id"] == "PHI-020"
    assert item["content"] == "## PHI-020 — Test\n\nphilosophy body"
    assert item["metadata"]["domain"] == "architecture"
    assert item["metadata"]["derived_from"] == "OBS-001"
    assert result["document_id"] == "PHI-020"


def test_hindsight_retain_phi_omits_derived_from_when_absent(mock_daemon):
    sys.path.insert(0, ".")
    if "scripts.mcp_server" in sys.modules:
        del sys.modules["scripts.mcp_server"]
    mod = importlib.import_module("scripts.mcp_server")

    mock_daemon["respond"]({"document_id": "PHI-021"})
    mod.hindsight_retain_phi(
        bank="oracle",
        document_id="PHI-021",
        content="body",
        metadata={"domain": "process"},
    )

    body = json.loads(mock_daemon["last_request"]()["body"])
    item = body["items"][0]
    assert "derived_from" not in item["metadata"]
```

- [ ] **Step 8.2: Run tests, verify failure**

```bash
uvx --from mcp --with pytest pytest tests/test_mcp_server.py -k retain_phi -v
```
Expected: FAIL — `AttributeError: ... no attribute 'hindsight_retain_phi'`.

- [ ] **Step 8.3: Implement the tool**

Append to `scripts/mcp_server.py`:

```python
def _retain(bank: str, *, context: str, content: str, document_id: str | None,
            derived_from: str | None, metadata: dict | None) -> dict:
    """Build the retain payload and POST to daemon.

    `context` is daemon-required: 'philosophy' | 'observation' | 'session-log'.
    Derived from tool name in callers, never user-controllable.
    """
    md = dict(metadata or {})
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
```

- [ ] **Step 8.4: Run tests, verify pass**

```bash
uvx --from mcp --with pytest pytest tests/test_mcp_server.py -k retain_phi -v
```
Expected: 2 PASSED.

- [ ] **Step 8.5: Commit**

```bash
git add scripts/mcp_server.py tests/test_mcp_server.py
git commit -m "feat(mcp): add hindsight_retain_phi tool with context='philosophy' mapping"
```

---

### Task 9: `hindsight_retain_obs` tool

**Files:**
- Modify: `scripts/mcp_server.py`
- Modify: `tests/test_mcp_server.py`

- [ ] **Step 9.1: Write failing test**

Append to `tests/test_mcp_server.py`:

```python
def test_hindsight_retain_obs_maps_context_observation(mock_daemon):
    sys.path.insert(0, ".")
    if "scripts.mcp_server" in sys.modules:
        del sys.modules["scripts.mcp_server"]
    mod = importlib.import_module("scripts.mcp_server")

    mock_daemon["respond"]({"document_id": "OBS-013"})
    mod.hindsight_retain_obs(
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
```

- [ ] **Step 9.2: Run test, verify failure**

```bash
uvx --from mcp --with pytest pytest tests/test_mcp_server.py -k retain_obs -v
```
Expected: FAIL — `AttributeError: ... no attribute 'hindsight_retain_obs'`.

- [ ] **Step 9.3: Implement the tool**

Append to `scripts/mcp_server.py`:

```python
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
```

- [ ] **Step 9.4: Run test, verify pass**

```bash
uvx --from mcp --with pytest pytest tests/test_mcp_server.py -k retain_obs -v
```
Expected: PASS.

- [ ] **Step 9.5: Commit**

```bash
git add scripts/mcp_server.py tests/test_mcp_server.py
git commit -m "feat(mcp): add hindsight_retain_obs tool with context='observation' mapping"
```

---

### Task 10: `hindsight_retain_session_log` tool

**Files:**
- Modify: `scripts/mcp_server.py`
- Modify: `tests/test_mcp_server.py`

- [ ] **Step 10.1: Write failing test**

Append to `tests/test_mcp_server.py`:

```python
def test_hindsight_retain_session_log_no_document_id(mock_daemon):
    sys.path.insert(0, ".")
    if "scripts.mcp_server" in sys.modules:
        del sys.modules["scripts.mcp_server"]
    mod = importlib.import_module("scripts.mcp_server")

    mock_daemon["respond"]({"document_id": "SESSION-2026-04-30-123"})
    mod.hindsight_retain_session_log(
        bank="oracle",
        content="session summary text",
        metadata={"project": "Hindsight"},
    )

    body = json.loads(mock_daemon["last_request"]()["body"])
    item = body["items"][0]
    assert item["context"] == "session-log"
    assert "document_id" not in item  # daemon assigns
    assert item["metadata"]["project"] == "Hindsight"
```

- [ ] **Step 10.2: Run test, verify failure**

```bash
uvx --from mcp --with pytest pytest tests/test_mcp_server.py -k retain_session_log -v
```
Expected: FAIL — `AttributeError: ... no attribute 'hindsight_retain_session_log'`.

- [ ] **Step 10.3: Implement the tool**

Append to `scripts/mcp_server.py`:

```python
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
```

- [ ] **Step 10.4: Run test, verify pass**

```bash
uvx --from mcp --with pytest pytest tests/test_mcp_server.py -k retain_session_log -v
```
Expected: PASS.

- [ ] **Step 10.5: Commit**

```bash
git add scripts/mcp_server.py tests/test_mcp_server.py
git commit -m "feat(mcp): add hindsight_retain_session_log tool"
```

---

## Phase 4 — Special tool

### Task 11: `hindsight_log_query` tool with `$HINDSIGHT_ROOT` anchor

**Files:**
- Modify: `scripts/mcp_server.py`
- Modify: `tests/test_mcp_server.py`

This tool does NOT call the daemon — it appends a JSONL line to `${HINDSIGHT_ROOT}/.decisions/queries/YYYY-MM.jsonl`. The path-anchor invariant (PHI-006 lesson) is enforced inside the tool: resolve against `$HINDSIGHT_ROOT` env var, fall back to `$HOME/Developer/Hindsight`, never `os.getcwd()`.

- [ ] **Step 11.1: Write failing tests**

Append to `tests/test_mcp_server.py`:

```python
import os
import tempfile


def test_hindsight_log_query_writes_to_hindsight_root(tmp_path, monkeypatch):
    sys.path.insert(0, ".")
    if "scripts.mcp_server" in sys.modules:
        del sys.modules["scripts.mcp_server"]
    mod = importlib.import_module("scripts.mcp_server")

    monkeypatch.setenv("HINDSIGHT_ROOT", str(tmp_path))
    monkeypatch.chdir("/tmp")  # CWD is somewhere else — tool must NOT use it

    result = mod.hindsight_log_query(
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


def test_hindsight_log_query_falls_back_to_home_when_env_unset(tmp_path, monkeypatch):
    sys.path.insert(0, ".")
    if "scripts.mcp_server" in sys.modules:
        del sys.modules["scripts.mcp_server"]
    mod = importlib.import_module("scripts.mcp_server")

    fake_home = tmp_path / "fakehome"
    fake_home.mkdir()
    monkeypatch.delenv("HINDSIGHT_ROOT", raising=False)
    monkeypatch.setenv("HOME", str(fake_home))

    mod.hindsight_log_query(
        client="cli",
        question="q",
        answer="a",
        recall_data={},
    )

    expected = fake_home / "Developer" / "Hindsight" / ".decisions" / "queries"
    assert expected.exists()


def test_hindsight_log_query_never_uses_cwd(tmp_path, monkeypatch):
    """Critical invariant: PHI-006 lesson. CWD must not influence write path."""
    sys.path.insert(0, ".")
    if "scripts.mcp_server" in sys.modules:
        del sys.modules["scripts.mcp_server"]
    mod = importlib.import_module("scripts.mcp_server")

    consumer_project = tmp_path / "TravelPlanner"
    consumer_project.mkdir()
    hindsight = tmp_path / "Hindsight"
    hindsight.mkdir()
    monkeypatch.setenv("HINDSIGHT_ROOT", str(hindsight))
    monkeypatch.chdir(consumer_project)  # if tool uses cwd, it lands here

    mod.hindsight_log_query(client="x", question="q", answer="a", recall_data={})

    # The consumer project must remain untouched.
    assert not (consumer_project / ".decisions").exists()
    assert (hindsight / ".decisions" / "queries").exists()
```

- [ ] **Step 11.2: Run tests, verify failure**

```bash
uvx --from mcp --with pytest pytest tests/test_mcp_server.py -k log_query -v
```
Expected: 3 FAIL — `AttributeError: ... no attribute 'hindsight_log_query'`.

- [ ] **Step 11.3: Implement the tool**

Append to `scripts/mcp_server.py`:

```python
import datetime
import os
from pathlib import Path


def _hindsight_root() -> Path:
    """Resolve HINDSIGHT_ROOT, falling back to ~/Developer/Hindsight.

    NEVER use os.getcwd() — PHI-006 was the bug where artifacts landed
    in consumer project trees because path resolution fell through to CWD.
    """
    env = os.environ.get("HINDSIGHT_ROOT")
    if env:
        return Path(env)
    return Path(os.environ["HOME"]) / "Developer" / "Hindsight"


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
    queries_dir = _hindsight_root() / ".decisions" / "queries"
    queries_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now(datetime.timezone.utc)
    log_path = queries_dir / f"{now.year:04d}-{now.month:02d}.jsonl"
    entry = {
        "timestamp": now.isoformat(),
        "client": client,
        "question": question,
        "answer": answer,
        "recall_data": recall_data,
    }
    with log_path.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    return {"logged_path": str(log_path)}
```

- [ ] **Step 11.4: Run tests, verify pass**

```bash
uvx --from mcp --with pytest pytest tests/test_mcp_server.py -k log_query -v
```
Expected: 3 PASSED. The third test (CWD invariant) is the load-bearing one — if it ever fails, PHI-006 has reopened.

- [ ] **Step 11.5: Commit**

```bash
git add scripts/mcp_server.py tests/test_mcp_server.py
git commit -m "feat(mcp): add hindsight_log_query with HINDSIGHT_ROOT path anchor (PHI-006 invariant)"
```

---

## Phase 5 — End-to-end verification

### Task 12: Manual smoke test against real daemon

**Files:** none (verification only)

Confirm the MCP server actually talks to the running daemon. Catches integration issues the unit tests can't (real network, real daemon response shapes, real bank state).

- [ ] **Step 12.1: Confirm daemon is running**

```bash
curl -s http://localhost:9077/v1/default/banks/oracle/stats
```
Expected: a JSON response with at least `node_count`. If the daemon isn't up, start it:

```bash
HINDSIGHT_API_EMBEDDINGS_LOCAL_FORCE_CPU=1 HINDSIGHT_API_RERANKER_LOCAL_FORCE_CPU=1 uvx hindsight-embed daemon start
```

- [ ] **Step 12.2: Manually invoke `hindsight_stats` via the server**

Use the MCP inspector or a manual stdio session. Quick approach with `mcp` CLI if available:

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"hindsight_stats","arguments":{"bank":"oracle"}}}' | uvx --from mcp python3 scripts/mcp_server.py 2>/dev/null | head -5
```
Expected: JSON-RPC response with the stats payload. If the request hangs, the server is waiting for the `initialize` handshake first — use the inspector instead.

- [ ] **Step 12.3: Manually invoke `hindsight_recall`**

Same pattern, with a real query. Verify:
- Response contains `results` (slim shape)
- No `score` field in result items
- `top_n` defaults to 10

- [ ] **Step 12.4: Verify `hindsight_log_query` writes to correct path**

```bash
HINDSIGHT_ROOT=/tmp/test-hindsight python3 -c "
import sys; sys.path.insert(0, '.')
from scripts.mcp_server import hindsight_log_query
print(hindsight_log_query('test-client', 'q', 'a', {}))
"
ls /tmp/test-hindsight/.decisions/queries/
```
Expected: log file exists, no `.decisions` created in CWD.

Cleanup: `rm -rf /tmp/test-hindsight`.

- [ ] **Step 12.5: Document any deviations**

If real daemon responses differ from the mock fixtures (extra fields, different shapes), note them in a `LOG-mcp-server-smoke.md` deferred to the LOG record in Task 24.

No commit (verification only).

---

## Phase 6 — Skill migration (one skill per task)

Each skill rewrite preserves the skill's frontmatter and step structure, replacing only the daemon-call mechanics. Critical invariants preserved per skill are called out at the top of each task.

### Task 13: Rewrite `oracle` skill

**Files:**
- Modify: `.claude/skills/oracle/SKILL.md`

**Invariant preserved:** subagent dispatch via `Agent` tool; synthesis brief format unchanged; logging via `hindsight_log_query` MCP tool replaces `log_oracle_query.py` script.

- [ ] **Step 13.1: Read current skill body**

```bash
cat .claude/skills/oracle/SKILL.md
```
Expected: 166 lines per current state. Keep frontmatter (lines 1-6) verbatim.

- [ ] **Step 13.2: Rewrite skill body — replace section "Execution"**

In `.claude/skills/oracle/SKILL.md`, replace the entire `## Execution` section (lines 26-154 currently) with:

```markdown
## Execution

1. **Check that `$ARGUMENTS` is not empty.** If empty, ask: "What decision are you facing?" before proceeding.

2. **Retrieve relevant memories from the oracle bank.** Call the `mcp__hindsight__hindsight_recall` tool:

   - `bank`: `"oracle"`
   - `query`: the user's question (`$ARGUMENTS`) — passed as a typed string arg, no shell escaping needed
   - `budget`: `"mid"` (default)
   - `max_tokens`: `4096` (default)
   - `top_n`: `10` (default)

   The tool returns the slim shape — already projected to `{text, type, document_id, mentioned_at, metadata}`. No further trimming needed in step 3.

   If the tool errors with a connection failure to the daemon:
   > **Oracle unavailable** — start the daemon with:
   > ```
   > HINDSIGHT_API_EMBEDDINGS_LOCAL_FORCE_CPU=1 HINDSIGHT_API_RERANKER_LOCAL_FORCE_CPU=1 uvx hindsight-embed daemon start
   > ```
   Do not proceed.

3. **Inspect results.** If the returned list is empty, tell the user "The oracle has no entries relevant to that question." Do not dispatch a subagent. Stop here. Otherwise, the list is already top-10 slim — pass directly to step 4 as `{RESULTS_JSON}`.

4. **Dispatch a synthesis subagent.** Use the `Agent` tool with these parameters:

   - `subagent_type`: `general-purpose`
   - `model`: `sonnet`
   - `description`: `Oracle synthesis`
   - `prompt`: a self-contained brief built from the template below.

   Synthesis brief template (substitute `{QUESTION}` and `{RESULTS_JSON}` — the latter inlined as JSON string):

   ```
   You are synthesizing an answer for the Decision Oracle. The oracle
   models Colin's cross-project decision-making philosophies and patterns.
   Its bank holds PHIs (philosophies — held opinions) and OBSs (observed
   patterns) extracted from prior sessions.

   Decision question:
   {QUESTION}

   Retrieved memories from the oracle bank (most relevant first):
   {RESULTS_JSON}

   RELEVANCE GATE — apply this BEFORE writing anything else:
   Read each retrieved entry against the decision question. If none is
   genuinely relevant (i.e., addresses the question's actual subject
   matter, not just sharing surface keywords or topic-adjacent themes),
   respond with EXACTLY this single line and nothing else:

   The oracle has no entries relevant to that question.

   Do not soften, qualify, or pad. Do not summarize what was retrieved.
   Do not list near-misses. Returning empty is the correct answer when
   the bank holds no signal — empty results are a valid, accepted outcome.

   If at least one entry is genuinely relevant, proceed to synthesis.

   Write a direct markdown answer to the decision question that:
   - cites specific PHI-NNN / OBS-NNN identifiers where relevant —
     `document_id` carries them for `experience`-type entries, but
     `observation`-type entries usually leave `document_id` null and embed
     the IDs in the body text (e.g., "PHI-001 philosophy…"). Extract from
     either source; do not invent IDs;
   - leads with the answer, not the reasoning;
   - surfaces tensions or counter-evidence in the retrieved memories
     before stating a recommendation;
   - flags when the bank's evidence is thin or off-topic — say so plainly
     rather than padding;
   - stays under ~250 words unless the question genuinely needs more.

   Do not include preamble, meta-commentary about the synthesis process,
   restatements of the question, or trailing orientation/next-step blocks.
   Output only the markdown answer.
   ```

5. **Render the subagent's response directly to the user.**

6. **Log the query** via `mcp__hindsight__hindsight_log_query`:

   - `client`: `"claude-code"`
   - `question`: `$ARGUMENTS` (typed string arg, no shell escaping)
   - `answer`: the subagent's full response text
   - `recall_data`: the recall result from step 2

   The MCP tool resolves `${HINDSIGHT_ROOT}/.decisions/queries/YYYY-MM.jsonl` internally — no path argument needed.

7. **Append a capture prompt** at the end:

   > If this query surfaced a decision worth recording, capture it with `/oracle-debate "[brief description]"`.
```

- [ ] **Step 13.3: Update the "Notes" section**

Replace the existing "Notes" section with:

```markdown
## Notes

- The oracle answers from retained PHIs, OBSs, session logs, and the Decision Constitution mental model — whatever the recall tool surfaces semantically.
- If the bank is empty or has no relevant content, say so plainly. This is correct behavior, not an error.
- Synthesis runs on subscription tokens at Sonnet 4.6 via the Agent tool. The previous `/reflect` path used haiku-3 against the Anthropic API.
- All daemon HTTP calls are routed through `mcp__hindsight__*` MCP tools — no inline `python3 -c`, `curl`, or `/tmp` staging.
```

- [ ] **Step 13.4: Verify the file syntax (markdown structure)**

```bash
head -10 .claude/skills/oracle/SKILL.md
grep -c "^##" .claude/skills/oracle/SKILL.md
```
Expected: frontmatter intact, section headings present.

- [ ] **Step 13.5: Confirm no inline daemon HTTP heredocs remain**

```bash
grep -nE "python3 -c|curl.*localhost:9077|/tmp/oracle_" .claude/skills/oracle/SKILL.md
```
Expected: no matches.

- [ ] **Step 13.6: Commit**

```bash
git add .claude/skills/oracle/SKILL.md
git commit -m "refactor(oracle): replace daemon HTTP heredocs with MCP tool calls"
```

---

### Task 14: Rewrite `oracle-debate` skill

**Files:**
- Modify: `.claude/skills/oracle-debate/SKILL.md`

**Invariants preserved:**
- Write-ordering: retain to bank BEFORE writing canonical file (mid-run interruption orphans only the regenerable file)
- Path anchoring: canonical file `Write` resolves against `$HINDSIGHT_ROOT`, never `$(pwd)`
- Banner stripping: bank `content` excludes `<!-- ORACLE ARTIFACT -->` (filesystem-only marker)

- [ ] **Step 14.1: Read current skill body**

```bash
cat .claude/skills/oracle-debate/SKILL.md
```
Expected: ~170 lines. Keep frontmatter (lines 1-6) verbatim.

- [ ] **Step 14.2: Rewrite step 4 (retain) to use MCP tool**

In `.claude/skills/oracle-debate/SKILL.md`, replace the `### Step 4 — Retain to oracle bank` section (which currently contains a `python3 -c` heredoc) with:

```markdown
### Step 4 — Retain to oracle bank

Once confirmed in step 3, call the `mcp__hindsight__hindsight_retain_phi` tool:

- `bank`: `"oracle"`
- `document_id`: e.g., `"PHI-020"` (computed in step 1)
- `content`: the full confirmed PHI markdown, **starting at the `## PHI-NNN ...` heading — NOT including the `<!-- ORACLE ARTIFACT -->` banner**. The banner is filesystem-only; embedding it in the bank adds retrieval noise.
- `derived_from`: any related PHI/OBS IDs cited in the debate, comma-separated; or omit if none
- `metadata`:
  ```json
  {
    "type": "philosophy",
    "domain": "<from the PHI domain field>",
    "date": "<YYYY-MM-DD today>",
    "source": "oracle-debate",
    "source_project": "<from step 1>"
  }
  ```

If the tool errors with a daemon connection failure:
- Surface: **Oracle unavailable** — see daemon start instructions in `/oracle` skill
- **Still write the PHI file in step 5** (don't lose the capture). The bank-first invariant is best-effort: when the bank is genuinely unreachable, the file copy is the fallback record.

**Do NOT proceed to step 5 until step 4 has either succeeded OR explicitly fallen through with the daemon-unavailable message.** This preserves the retain-bank-first ordering.
```

- [ ] **Step 14.3: Verify step 5 (canonical file Write) is unchanged**

The canonical file write in step 5 still uses the `Write` tool against `${HINDSIGHT_ROOT:-$HOME/Developer/Hindsight}/.decisions/phi/PHI-NNN-{slug}.md`. **Do not modify that section** — it preserves the path-anchor invariant. Confirm:

```bash
grep -A 5 "### Step 5 — Write the canonical PHI file" .claude/skills/oracle-debate/SKILL.md
```
Expected: section exists, references `$HINDSIGHT_ROOT`, no relative paths.

- [ ] **Step 14.4: Confirm no inline daemon HTTP heredocs remain**

```bash
grep -nE "python3 -c|curl.*localhost:9077" .claude/skills/oracle-debate/SKILL.md
```
Expected: no matches.

- [ ] **Step 14.5: Commit**

```bash
git add .claude/skills/oracle-debate/SKILL.md
git commit -m "refactor(oracle-debate): replace retain heredoc with MCP tool, preserve invariants"
```

---

### Task 15: Rewrite `oracle-observe` skill

**Files:**
- Modify: `.claude/skills/oracle-observe/SKILL.md`

**Invariants preserved:**
- Step 7 retain still happens AFTER step 6 user confirmation (no auto-retain)
- The fit-check recall in step 3 still goes to the corpus, not just to the user

**What disappears:**
- `/tmp/oracle_observation.txt` staging — typed args remove the shell-escape concern
- Two `python3 -c` heredocs (recall + retain)
- One `curl` call (stats check)

- [ ] **Step 15.1: Read current skill body**

```bash
cat .claude/skills/oracle-observe/SKILL.md
```

- [ ] **Step 15.2: Rewrite step 1 (daemon check) to use MCP**

Replace the curl-based stats check with a call to `mcp__hindsight__hindsight_stats(bank="oracle")`. Replace error-handling: instead of `curl` connection-error message, handle MCP tool error response (the surfaced message stays the same).

```markdown
### Step 1 — Check daemon

Call `mcp__hindsight__hindsight_stats(bank="oracle")`. If the call errors with a connection failure, surface: **Oracle unavailable** — see daemon start instructions in `/oracle` skill. Do not proceed.

If the response includes `pending_operations > 0`, warn the user but do not block — fit-check recall is lower stakes than synthesis. Proceed with caution noted.
```

- [ ] **Step 15.3: Rewrite step 2 (next OBS-NNN) to use MCP**

Replace the curl + python parsing with a single MCP call:

```markdown
### Step 2 — Determine next OBS-NNN ID

Call `mcp__hindsight__hindsight_list_documents(bank="oracle", prefix="OBS-")`. Find the highest `id` (numeric suffix). Next ID = highest + 1, zero-padded to 3 digits. If none exist, start at `OBS-001`.
```

- [ ] **Step 15.4: Rewrite step 3 (fit-check recall) — REMOVE /tmp staging**

Replace the entire step 3 (currently a Write-then-Read-then-python3-c dance) with:

```markdown
### Step 3 — Run fit-check via MCP recall

Call `mcp__hindsight__hindsight_recall`:
- `bank`: `"oracle"`
- `query`: the observation text (`$ARGUMENTS`) — passed as a typed string arg, no shell escaping or `/tmp` staging needed
- `budget`: `"mid"` (default)
- `top_n`: `10` (default)

The result is the slim shape — top 10 entries with `text`, `type`, `document_id`, `mentioned_at`, `metadata`. Use this for step 4's fit narrative.
```

- [ ] **Step 15.5: Rewrite step 7 (retain) to use MCP tool**

Replace the `python3 -c` retain heredoc with:

```markdown
### Step 7 — Retain to oracle bank

After explicit user confirmation in step 6, call `mcp__hindsight__hindsight_retain_obs`:

- `bank`: `"oracle"`
- `document_id`: e.g., `"OBS-013"` (computed in step 2)
- `content`: the curated text from step 5
- `derived_from`: comma-separated list of related PHI/OBS IDs from the user's confirmation; omit if standalone
- `metadata`:
  ```json
  {
    "type": "observation",
    "date": "<YYYY-MM-DD today>",
    "relationship": "<new | extends OBS-NNN | contradicts PHI-NNN>",
    "source": "manual"
  }
  ```
```

- [ ] **Step 15.6: Confirm no inline daemon HTTP heredocs or /tmp staging remain**

```bash
grep -nE "python3 -c|curl.*localhost:9077|/tmp/oracle_" .claude/skills/oracle-observe/SKILL.md
```
Expected: no matches.

- [ ] **Step 15.7: Commit**

```bash
git add .claude/skills/oracle-observe/SKILL.md
git commit -m "refactor(oracle-observe): MCP tools, remove /tmp staging and shell-escape pattern"
```

---

### Task 16: Rewrite `oracle-preclear` skill

**Files:**
- Modify: `.claude/skills/oracle-preclear/SKILL.md`

**Invariants preserved (load-bearing):**
- **Write-ordering** (line 19 of current skill): retain to bank BEFORE writing PHI file. MCP migration must call `hindsight_retain_phi` then `Write`, never reverse.
- **Path anchoring**: PHI file `Write` resolves against `$HINDSIGHT_ROOT`, never `$(pwd)`.
- **Banner stripping**: bank `content` excludes the `<!-- ORACLE ARTIFACT -->` banner.

**What disappears:**
- 4 `python3 -c` heredocs (recall + 3 retain variants)
- 1 `curl` stats call
- 1 `curl + python3 -c` documents listing

**What stays:**
- `ls .decisions/phi/` for next-PHI ID enumeration (filesystem operation, not daemon)
- `git remote get-url origin` for source-project capture (filesystem operation)
- Write-tool calls for PHI file creation

- [ ] **Step 16.1: Read current skill body**

```bash
cat .claude/skills/oracle-preclear/SKILL.md
```
Expected: ~289 lines.

- [ ] **Step 16.2: Rewrite step 1 (daemon + orientation) — replace curl/python with MCP**

Replace the two parallel `curl` blocks (stats + documents) with two MCP tool calls:

```markdown
### Step 1 — Check daemon and gather orientation data

Call these MCP tools in parallel:

- `mcp__hindsight__hindsight_stats(bank="oracle")` — confirms daemon connectivity
- `mcp__hindsight__hindsight_list_documents(bank="oracle", prefix="OBS-")` — for next-OBS-NNN computation

Plus these filesystem operations (NOT migrated — they don't go through the daemon):

```bash
HINDSIGHT_ROOT="${HINDSIGHT_ROOT:-$HOME/Developer/Hindsight}"
test -d "$HINDSIGHT_ROOT/.decisions/phi" && \
  ls "$HINDSIGHT_ROOT/.decisions/phi/" | grep -E '^PHI-[0-9]+' | sort | tail -1 || \
  echo "MISSING: $HINDSIGHT_ROOT/.decisions/phi"
```

```bash
git remote get-url origin 2>/dev/null | sed 's/.*\///' | sed 's/\.git$//' || basename "$(pwd)"
```

If the MCP stats call errors with a connection failure: surface **Oracle unavailable** with daemon start instructions, stop.

If the PHI listing returns `MISSING:`: surface **Hindsight repo not found at `$HINDSIGHT_ROOT`**, stop.

Compute from results:
- **Next OBS-NNN**: highest OBS number from list_documents result + 1, zero-padded to 3 digits. Start at 001 if none.
- **Next PHI-NNN**: from the PHI filename listing.
- **Source project**: from git remote slug or directory name.
```

- [ ] **Step 16.3: Rewrite step 2 (orient via recall) to use MCP**

Replace the `python3 -c` recall block with:

```markdown
### Step 2 — Orient on existing corpus via MCP recall

Call `mcp__hindsight__hindsight_recall`:
- `bank`: `"oracle"`
- `query`: `"philosophies and observed patterns retained in the oracle bank"`
- `budget`: `"mid"`
- `top_n`: `15`

The result is the slim shape — top 15 corpus entries. Use as dedup signal for step 3.
```

- [ ] **Step 16.4: Rewrite step 4 PHI retain — preserve write-ordering**

Replace the `python3 -c` PHI retain heredoc with:

```markdown
**For PHI candidates:**

Derive a filename slug from the title (lowercase, spaces to hyphens, strip punctuation).

**Retain to oracle bank FIRST** via `mcp__hindsight__hindsight_retain_phi`:

- `bank`: `"oracle"`
- `document_id`: e.g., `"PHI-020"`
- `content`: PHI markdown **starting at `## PHI-NNN` heading** — NO `<!-- ORACLE ARTIFACT -->` banner (banner is filesystem-only)
- `metadata`:
  ```json
  {
    "type": "philosophy",
    "domain": "<from the PHI domain>",
    "date": "<YYYY-MM-DD today>",
    "source": "oracle-preclear",
    "source_project": "<from step 1>"
  }
  ```

Do NOT proceed to the file write below until the MCP retain call returns successfully (or explicitly errors with daemon-unavailable). This preserves the bank-first invariant: a mid-run auto-compact between bank-retain and file-write only orphans the regenerable file copy, never the canonical record.
```

Then the existing file-write section follows verbatim (the `Write` tool call against `${HINDSIGHT_ROOT}/.decisions/phi/PHI-NNN-{slug}.md` with banner-prefixed content). Confirm that section is unchanged:

```bash
grep -A 3 "Use the Write tool with an" .claude/skills/oracle-preclear/SKILL.md
```
Expected: still references `$HINDSIGHT_ROOT`, absolute path, no `$(pwd)`.

- [ ] **Step 16.5: Rewrite step 4 OBS retain to use MCP**

Replace the `python3 -c` OBS retain heredoc with:

```markdown
**For OBS candidates:**

Call `mcp__hindsight__hindsight_retain_obs`:

- `bank`: `"oracle"`
- `document_id`: e.g., `"OBS-013"`
- `content`: the OBS body
- `derived_from`: comma-separated related PHI/OBS IDs, or omit if standalone
- `metadata`:
  ```json
  {
    "type": "observation",
    "date": "<YYYY-MM-DD today>",
    "source": "oracle-preclear"
  }
  ```

Increment the OBS counter before the next OBS candidate.
```

- [ ] **Step 16.6: Rewrite step 5 (session summary retain) to use MCP**

Replace the `python3 -c` session retain heredoc with:

```markdown
### Step 5 — Generate and retain session summary

Without prompting the user, write a 3–5 sentence session summary from the current conversation:
- What was decided, built, or resolved
- Any rejected approaches and why
- Anything that would have been useful to know at the start of the session

Show the summary to the user before retaining so they can see what was captured.

Then call `mcp__hindsight__hindsight_retain_session_log`:

- `bank`: `"oracle"`
- `content`: the summary text
- `metadata`:
  ```json
  {
    "type": "session-log",
    "project": "<source project from step 1>",
    "date": "<YYYY-MM-DD today>"
  }
  ```
```

- [ ] **Step 16.7: Confirm no inline daemon HTTP heredocs remain**

```bash
grep -nE "python3 -c.*urllib|curl.*localhost:9077" .claude/skills/oracle-preclear/SKILL.md
```
Expected: no matches. (Filesystem `python3 -c` for parsing PHI listings is fine if any remain — only daemon-HTTP heredocs are the target.)

- [ ] **Step 16.8: Commit**

```bash
git add .claude/skills/oracle-preclear/SKILL.md
git commit -m "refactor(oracle-preclear): MCP tools for daemon I/O, preserve write-ordering invariant"
```

---

### Task 17: Rewrite `oracle-synthesize` skill

**Files:**
- Modify: `.claude/skills/oracle-synthesize/SKILL.md`

**Invariants preserved:**
- Subagent dispatch in step 3c (Sonnet synthesis subagent — CDR-subscription-llm-routing.md)
- User confirmation (step 6) before retain in step 7

**What disappears:**
- `/tmp/oracle_synthesize_query.txt` and `/tmp/oracle_synthesize_recall.json` staging
- 1 `curl` stats call
- 1 `curl` documents call
- 2 `python3 -c` heredocs (recall + retain)

- [ ] **Step 17.1: Read current skill body**

```bash
cat .claude/skills/oracle-synthesize/SKILL.md
```

- [ ] **Step 17.2: Rewrite step 1 (daemon check) to use MCP**

Replace the `curl /stats` block with:

```markdown
### Step 1 — Check daemon and pending operations

Call `mcp__hindsight__hindsight_stats(bank="oracle")`. If `pending_operations > 0`, stop and tell the user:

> **Daemon has pending operations — synthesis may be incomplete. Wait for `pending_operations: 0` before synthesizing.**

If the call errors with daemon-unavailable, surface the start command and stop.
```

- [ ] **Step 17.3: Rewrite step 2 (next OBS-NNN) to use MCP**

Replace the curl + python parse with:

```markdown
### Step 2 — Determine next OBS-NNN ID

Call `mcp__hindsight__hindsight_list_documents(bank="oracle", prefix="OBS-")`. Highest `id` numeric suffix + 1, zero-padded. Start at `OBS-001` if none.
```

- [ ] **Step 17.4: Rewrite step 3 (recall) — REMOVE /tmp staging**

Replace the entire step 3 (Write to /tmp + python3 -c recall) with:

```markdown
### Step 3 — Recall + synthesis subagent

Synthesis runs as MCP recall + Sonnet subagent dispatch (subscription tokens). See `.claude/.decisions/CDR-subscription-llm-routing.md`.

**Step 3a — Determine the query.** If `$ARGUMENTS` is non-empty, use it. Otherwise use the default:

> What patterns define how I make decisions? Cite specific PHI and OBS IDs (e.g., PHI-001, OBS-001) in your response to ground the synthesis.

**Step 3b — Recall a wide spread of corpus entries** via `mcp__hindsight__hindsight_recall`:

- `bank`: `"oracle"`
- `query`: the query text from 3a (typed string arg — no `/tmp` staging needed)
- `budget`: `"high"` (synthesize uses higher budget than other recall callers)
- `max_tokens`: `8192`
- `top_n`: `20`

The result is the slim top-20 — pass directly to step 3c as `{RESULTS_JSON}`.

If the result is empty:
> **Recall returned no entries — bank may have insufficient content. Do not retain.**

**Step 3c — Dispatch a synthesis subagent** via the `Agent` tool with:

- `subagent_type`: `general-purpose`
- `model`: `sonnet`
- `description`: `Oracle synthesis (cross-corpus pattern)`
- `prompt`: build the brief below, inlining the query and the slim recall result as JSON.

Synthesis brief template:

```
You are running a periodic synthesis cycle for the Decision Oracle. The
oracle models Colin's cross-project decision-making philosophies and
patterns. Its bank holds PHIs (philosophies — held opinions) and OBSs
(observed patterns) extracted from prior sessions.

This is not a decision-point query. The output will be retained as a new
Observation (OBS-NNN) in the bank itself, so it must be a distilled
pattern statement, not an answer.

Synthesis query:
{QUERY}

Corpus sample (top 20 entries by relevance, JSON):
{RESULTS_JSON}

Write a markdown OBS body that:
- distills a *cross-entry pattern* — a recurring instinct, constraint,
  or tradeoff visible across multiple entries — not a summary of one
  entry;
- cites at least 2 specific PHI-NNN / OBS-NNN identifiers in the body
  text. Use `document_id` for `experience`-type entries; for
  `observation`-type entries the IDs are usually embedded in the body
  (e.g., "PHI-005 principle…"). Do not invent IDs;
- is suitable for direct retention (no preamble, no meta-commentary, no
  trailing orientation block);
- stays under ~200 words;
- if the corpus sample is too thin or off-topic to support a real
  synthesis, say so plainly in one sentence and stop — do not pad.
```
```

- [ ] **Step 17.5: Rewrite step 7 (retain) to use MCP tool**

Replace the `python3 -c` retain heredoc with:

```markdown
### Step 7 — Retain to oracle bank

After explicit user confirmation in step 6, call `mcp__hindsight__hindsight_retain_obs`:

- `bank`: `"oracle"`
- `document_id`: e.g., `"OBS-013"` (from step 2)
- `content`: the curated text from step 4
- `derived_from`: comma-separated PHI/OBS IDs extracted in step 5
- `metadata`:
  ```json
  {
    "type": "observation",
    "date": "<YYYY-MM-DD today>",
    "query": "<the synthesis query>"
  }
  ```
```

- [ ] **Step 17.6: Confirm no inline daemon HTTP heredocs or /tmp staging remain**

```bash
grep -nE "python3 -c.*urllib|curl.*localhost:9077|/tmp/oracle_synthesize" .claude/skills/oracle-synthesize/SKILL.md
```
Expected: no matches.

- [ ] **Step 17.7: Commit**

```bash
git add .claude/skills/oracle-synthesize/SKILL.md
git commit -m "refactor(oracle-synthesize): MCP tools, remove /tmp staging"
```

---

## Phase 7 — Atomic landing

### Task 18: Add user-level MCP server registration

**Files:**
- Modify: `~/.claude.json` (user-level, NOT in repo)

**Why this is user-level, not repo-level:** oracle skills live in `~/.claude/skills/` and run in any project's working directory. Repo-scope `.mcp.json` would only register the server when Claude Code is opened in the Hindsight directory. User-level registration makes the MCP server available cross-project (matches the cross-project nature of the oracle).

- [ ] **Step 18.1: Inspect current ~/.claude.json structure**

```bash
test -f ~/.claude.json && python3 -c "import json; print(json.dumps(list(json.load(open(\"\$HOME/.claude.json\")).keys()), indent=2))" || echo "not found"
```
Expected: shows top-level keys, including (probably) an `mcpServers` block. If file doesn't exist, that's also fine — Claude Code creates it on first MCP add.

- [ ] **Step 18.2: Add the hindsight server entry**

Use the `claude mcp add` CLI (cleaner than hand-editing JSON):

```bash
claude mcp add hindsight --scope user --transport stdio -- python3 "$HOME/Developer/Hindsight/scripts/mcp_server.py"
```
Expected: confirmation that `hindsight` was added to user-scope config.

If `claude mcp add` is not available, hand-edit `~/.claude.json` to add:

```json
{
  "mcpServers": {
    "hindsight": {
      "command": "python3",
      "args": ["/Users/colindwan/Developer/Hindsight/scripts/mcp_server.py"]
    }
  }
}
```

- [ ] **Step 18.3: Verify the server is registered**

```bash
claude mcp list
```
Expected: shows `hindsight` in the list with the user scope.

- [ ] **Step 18.4: Test the server connects from Claude Code**

Open a fresh Claude Code session in any directory (e.g., `cd /tmp && claude`). Type:

```
/mcp
```
Expected: lists `hindsight` as connected, with 7 tools enumerated.

- [ ] **Step 18.5: No commit** — `~/.claude.json` is not repo-tracked. Document the change in the LOG record (Task 24).

---

### Task 19: Update user-level allowlist

**Files:**
- Modify: `~/.claude/settings.json` (user-level, NOT in repo)

- [ ] **Step 19.1: Back up current settings**

```bash
cp ~/.claude/settings.json ~/.claude/settings.json.bak.$(date +%Y%m%d-%H%M%S)
```

- [ ] **Step 19.2: Inspect the relevant entries**

```bash
python3 -c "
import json
s = json.load(open('$HOME/.claude/settings.json'))
allow = s.get('permissions', {}).get('allow', [])
for entry in allow:
    if 'python3' in entry or 'curl' in entry or 'mcp__hindsight' in entry:
        print(entry)
"
```
Expected to see (current state):
- `Bash(python3 -c "import json, urllib.request*)`
- `Bash(curl * localhost:9077*)`
And no `mcp__hindsight__*` entries yet.

- [ ] **Step 19.3: Apply the allowlist edits**

Edit `~/.claude/settings.json` directly. Find the `permissions.allow` array and:

**Remove these two entries:**
```json
"Bash(python3 -c \"import json, urllib.request*)",
"Bash(curl * localhost:9077*)"
```

**Add these seven entries:**
```json
"mcp__hindsight__hindsight_stats",
"mcp__hindsight__hindsight_list_documents",
"mcp__hindsight__hindsight_recall",
"mcp__hindsight__hindsight_retain_phi",
"mcp__hindsight__hindsight_retain_obs",
"mcp__hindsight__hindsight_retain_session_log",
"mcp__hindsight__hindsight_log_query"
```

- [ ] **Step 19.4: Validate JSON**

```bash
python3 -c "import json; json.load(open('$HOME/.claude/settings.json')); print('valid')"
```
Expected: `valid`. If invalid, restore from backup and re-apply manually.

- [ ] **Step 19.5: Verify the new state**

```bash
python3 -c "
import json
s = json.load(open('$HOME/.claude/settings.json'))
allow = s.get('permissions', {}).get('allow', [])
hindsight_grants = [e for e in allow if 'mcp__hindsight' in e]
old_bash = [e for e in allow if 'urllib.request' in e or 'localhost:9077' in e]
print(f'mcp__hindsight grants: {len(hindsight_grants)} (expected 7)')
print(f'old bash patterns remaining: {len(old_bash)} (expected 0)')
"
```
Expected: `7` and `0`.

- [ ] **Step 19.6: No commit** — user-level settings, not repo-tracked. Document in LOG (Task 24).

---

### Task 20: End-to-end smoke test all 5 skills

**Files:** none (verification only)

- [ ] **Step 20.1: Restart Claude Code** to pick up new MCP server registration

If Claude Code is running, exit and restart it.

- [ ] **Step 20.2: Verify MCP tools are auto-approved**

In a fresh session, invoke any oracle skill that calls a tool (e.g., `/oracle "test question"`). Confirm no permission prompt appears for `mcp__hindsight__hindsight_recall`. If a prompt appears, the allowlist edit (Task 19) didn't take effect — diagnose before proceeding.

- [ ] **Step 20.3: Test `/oracle` skill end-to-end**

```
/oracle "What patterns govern my permission allowlist decisions?"
```
Expected: skill calls `hindsight_recall`, dispatches synthesis subagent, renders answer, calls `hindsight_log_query` to record. Verify:

```bash
ls -la ~/Developer/Hindsight/.decisions/queries/$(date +%Y-%m).jsonl
tail -1 ~/Developer/Hindsight/.decisions/queries/$(date +%Y-%m).jsonl | python3 -c "import json,sys; print(json.loads(sys.stdin.read())['question'])"
```
Expected: log file appended with the question text.

- [ ] **Step 20.4: Test `/oracle-debate` skill end-to-end**

```
/oracle-debate "Test PHI for smoke verification — delete after"
```
Walk through the debate prompts. After confirmation, verify:
- A new `PHI-NNN` row appears via: `mcp__hindsight__hindsight_list_documents(bank="oracle", prefix="PHI-")` (or use the daemon directly)
- The corresponding file lands under `~/Developer/Hindsight/.decisions/phi/`
- File is NOT in any consumer project (`find ~/Developer -name "PHI-NNN-*.md" -not -path "*/Hindsight/*"` should return nothing)

After verification, manually delete the test PHI from the bank (use existing tooling or curl) and remove the file.

- [ ] **Step 20.5: Test `/oracle-observe` skill end-to-end**

```
/oracle-observe "Smoke-test observation — delete after"
```
Walk through prompts, verify retain succeeds, verify NO `/tmp/oracle_observation.txt` is created (`ls /tmp/oracle_*` should not show it).

Manually clean up the test OBS.

- [ ] **Step 20.6: Test `/oracle-synthesize` skill end-to-end**

```
/oracle-synthesize
```
Verify the recall→subagent→retain flow. Verify NO `/tmp/oracle_synthesize_*` files are created.

Manually clean up the test OBS.

- [ ] **Step 20.7: Test `/oracle-preclear` skill end-to-end**

```
/oracle-preclear
```
Verify the multi-step retain flow. Pay particular attention to the **bank-first ordering** — if you can simulate an interruption between bank-retain and file-write (e.g., by killing claude mid-step), verify only file copies are orphaned, never bank records without files.

- [ ] **Step 20.8: No commit** (verification only). Note any failures in LOG (Task 24).

---

### Task 21: Verification 1 — MCP grant auto-promotion behavior

**Files:** none (vendor-policy precondition check)

Per spec plan-time verification #1: confirm whether Claude Code's auto-allowlist mechanism applies to MCP tool grants the way it does to Bash patterns (OBS-012).

- [ ] **Step 21.1: Inspect current settings.json for any auto-added MCP entries**

```bash
diff ~/.claude/settings.json.bak.* ~/.claude/settings.json | head -40
```
Expected: only the 9 changes from Task 19 (2 removes + 7 adds). If any extra `mcp__hindsight__*` entries appeared, auto-promotion fired.

- [ ] **Step 21.2: Document the finding in LOG (Task 24)**

If auto-promotion did fire: note the entries it added. The chosen policy (auto-approve all 7) means promotion is benign today — no action required, but record for future reference.

If no auto-promotion: note that MCP grants appear to NOT face the OBS-012 mechanism. Forward-compat win.

---

## Phase 8 — Cleanup

### Task 22: Delete `scripts/log_oracle_query.py`

**Files:**
- Delete: `scripts/log_oracle_query.py`

- [ ] **Step 22.1: Verify nothing references the script**

```bash
grep -rn "log_oracle_query" ~/Developer/Hindsight/.claude/ ~/Developer/Hindsight/scripts/
```
Expected: only matches inside `scripts/log_oracle_query.py` itself, plus possibly the spec/plan docs (which document the deletion). If any SKILL.md still references it, that skill wasn't fully migrated — go back to its task.

- [ ] **Step 22.2: Delete the script**

```bash
git rm scripts/log_oracle_query.py
```

- [ ] **Step 22.3: Commit**

```bash
git commit -m "chore(mcp): remove scripts/log_oracle_query.py (superseded by hindsight_log_query)"
```

---

### Task 23: Land decision records (ADR + CDR + LOG)

**Files:**
- Create: `.claude/.decisions/ADR-mcp-server-integration.md`
- Create: `.claude/.decisions/CDR-mcp-tool-taxonomy.md`
- Create: `.decisions/log/LOG-mcp-server-migration.md` (verify exact LOG path with existing convention)

- [ ] **Step 23.1: Verify LOG path convention**

```bash
ls .decisions/ 2>/dev/null
ls .claude/.decisions/ 2>/dev/null | head -10
```
Determine where existing LOG files live (likely `.decisions/log/` or alongside ADRs). Use whichever matches.

- [ ] **Step 23.2: Write ADR**

Create `.claude/.decisions/ADR-mcp-server-integration.md`:

```markdown
# ADR-mcp-server-integration — Hindsight MCP Server as Oracle Skill Integration Boundary

**Date:** 2026-04-30
**Status:** Accepted
**Spec:** `docs/superpowers/specs/2026-04-30-hindsight-mcp-server-design.md`

## Context

Five oracle skills called the local hindsight daemon at `localhost:9077` via inline `python3 -c "import json, urllib.request..."` heredocs through Claude Code's Bash tool. A user-level allowlist entry — `Bash(python3 -c "import json, urllib.request*)` — kept these silent across projects but was functionally equivalent to `Bash(python3 *)` under prompt injection.

PHI-019 (capability allowlists drift toward over-permissive baselines) and OBS-012 (live evidence of auto-allowlist re-introduction) made the bash-allowlist surface a structural drift target.

## Decision

Hindsight ships a Python MCP server (`scripts/mcp_server.py`) using FastMCP over stdio. Five oracle skills are migrated to call typed `mcp__hindsight__*` tools instead of inline HTTP heredocs. The two over-broad bash allowlist entries are removed; seven narrow MCP tool grants replace them at user level.

## Risk Classes Used

- **read-of-pre-existing-state** (auto-approve safe): `hindsight_stats`, `hindsight_list_documents`, `hindsight_recall`
- **append-to-canonical-bank** (auto-approve only if write boundary is well-defined and recoverable): `hindsight_retain_phi`, `hindsight_retain_obs`, `hindsight_retain_session_log`, `hindsight_log_query`

New tools require an ADR amendment naming risk class.

## References

- PHI-019 (capability allowlists drift)
- OBS-012 (auto-allowlist re-introduction evidence)
- PHI-001 (stateless system design — daemon stays the state-holder)
- PHI-006 (path resolution must anchor against owning repo, not CWD — preserved by `_hindsight_root()` in MCP server)
- PHI-007 (extract shared spec, not implementation — slim shape lives at MCP boundary)
- CDR-subscription-llm-routing (synthesis subagent dispatch unaffected)
```

- [ ] **Step 23.3: Write CDR**

Create `.claude/.decisions/CDR-mcp-tool-taxonomy.md`:

```markdown
# CDR-mcp-tool-taxonomy — Hindsight MCP Tool Surface

**Date:** 2026-04-30
**Status:** Accepted
**ADR:** `ADR-mcp-server-integration.md`

## Tool inventory

Seven tools, organized by side-effect:

| Tool | Effect | Risk class |
|---|---|---|
| `hindsight_stats` | Read daemon stats | read-of-pre-existing-state |
| `hindsight_list_documents` | Read document list (with optional prefix filter) | read-of-pre-existing-state |
| `hindsight_recall` | Read corpus via embedding search; returns slim shape by default | read-of-pre-existing-state |
| `hindsight_retain_phi` | Write PHI to canonical bank | append-to-canonical-bank |
| `hindsight_retain_obs` | Write OBS to canonical bank | append-to-canonical-bank |
| `hindsight_retain_session_log` | Write session log to canonical bank (no document_id) | append-to-canonical-bank |
| `hindsight_log_query` | Append to `${HINDSIGHT_ROOT}/.decisions/queries/YYYY-MM.jsonl` | append-to-canonical-bank |

## Schema decisions

- **`recall` slim-by-default with `verbose` escape valve.** MCP server is the Claude-facing contract; optimizing the default shape for that audience is appropriate. Daemon HTTP API stays raw.
- **`retain_phi` and `retain_obs` schemas identical, tools separate.** Split-by-side-effect granularity preserves intent in audit logs and enables future per-tool gating without schema changes.
- **`context` field auto-mapped from tool name.** `retain_phi` → `'philosophy'`, `retain_obs` → `'observation'`, `retain_session_log` → `'session-log'`. Caller cannot pass mismatched type.
- **`hindsight_log_query` does NOT touch the daemon.** Resolves `${HINDSIGHT_ROOT}/.decisions/queries/YYYY-MM.jsonl` internally. Path anchor via `_hindsight_root()` — never `os.getcwd()` (PHI-006 invariant).

## Permission policy

All 7 tools auto-approved at user level. Single-user personal tool; bank pollution is git-tracked and recoverable. In-skill content confirmation in all 5 skills already gates retains.
```

- [ ] **Step 23.4: Write LOG (path per Step 23.1)**

Create the LOG file (path per existing convention) with content covering:
- Migration date and branch
- Files added/modified/deleted (full list)
- Allowlist diff applied to user-level `~/.claude/settings.json`
- MCP registration applied to `~/.claude.json`
- Smoke test results from Task 20
- Verification 1 outcome from Task 21
- Rollback runbook (`git revert`, plus manual restore of 2 bash allowlist entries + removal of 7 MCP grants)

- [ ] **Step 23.5: Commit decision records**

```bash
git add .claude/.decisions/ADR-mcp-server-integration.md .claude/.decisions/CDR-mcp-tool-taxonomy.md
# Plus the LOG path
git add <log-file-path>
git commit -m "docs(decisions): ADR + CDR + LOG for MCP server migration"
```

---

### Task 24: Open the PR

**Files:** none (PR creation)

- [ ] **Step 24.1: Push the branch**

```bash
git push -u origin spec/mcp-server-design
```

- [ ] **Step 24.2: Create the PR via gh**

```bash
gh pr create --title "feat: hindsight MCP server replaces inline daemon HTTP heredocs" --body "$(cat <<'EOF'
## Summary

- Adds `scripts/mcp_server.py` — Python MCP server (FastMCP, stdio) exposing 7 typed tools that adapt the existing daemon HTTP API
- Migrates 5 oracle skills to call `mcp__hindsight__*` tools instead of inline `python3 -c "import json, urllib.request..."` heredocs
- Eliminates `Bash(python3 -c "import json, urllib.request*")` and `Bash(curl * localhost:9077*)` user-level allowlist entries (manual edits, see LOG)
- Removes `/tmp/oracle_*.{txt,json}` cross-session collision risk by passing skill args as typed MCP arguments
- Deletes `scripts/log_oracle_query.py` (superseded by `hindsight_log_query` MCP tool)

## Spec

`docs/superpowers/specs/2026-04-30-hindsight-mcp-server-design.md`

## Test plan

- [ ] `pytest tests/test_mcp_server.py` passes (28+ tests covering all 7 tools, path-anchor invariant, slim shape projection)
- [ ] Manual smoke test of all 5 oracle skills end-to-end against running daemon
- [ ] `~/.claude/settings.json` allowlist diff verified: 2 bash patterns removed, 7 MCP grants added
- [ ] `~/.claude.json` MCP registration verified: `claude mcp list` shows `hindsight` server
- [ ] No `/tmp/oracle_*` files created during skill invocation
- [ ] PHI files written to `${HINDSIGHT_ROOT}/.decisions/phi/`, never to consumer project trees (PHI-006 invariant)
- [ ] Bank-first write ordering preserved in `oracle-preclear` and `oracle-debate` (retain MCP call before Write tool call)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```
Expected: PR URL returned. Open it in browser to verify rendered description.

---

## Self-review checklist

After all tasks, run this self-review:

- [ ] **Spec coverage:** every requirement in spec sections (Tool surface, Permission policy, Skill migration, Migration sequencing, Risk register, Critical preserved invariants) is addressed by at least one task above. Trace each spec section to its task(s):
  - Tool surface (7 tools) → Tasks 4–11
  - Permission policy → Task 19
  - Skill migration table → Tasks 13–17
  - Atomic migration → Tasks 18–22 land in one PR (Task 24)
  - Risk register entries 1, 2, 3 → enforced by code structure in Tasks 4–11; verified in Task 12
  - Plan-time verification 1 → Task 21
  - Plan-time verification 2 → already pre-flight verified during planning, no separate task needed
  - Critical preserved invariants (write-ordering, path anchoring) → Tasks 14, 16, 11

- [ ] **No placeholders:** zero "TBD", "TODO", "implement appropriate X", or "similar to Task N" references. All code shown inline.

- [ ] **Type consistency:** function names match across tasks (`hindsight_stats` not `hindsight_get_stats`; `_project_slim` not `_slim_project`; `_hindsight_root()` not `_resolve_root()`). Verify by grep:
  ```bash
  grep -nE "hindsight_(stats|list_documents|recall|retain_phi|retain_obs|retain_session_log|log_query)" docs/superpowers/plans/2026-04-30-hindsight-mcp-server.md | wc -l
  # Expected: many matches, all using consistent names
  ```
