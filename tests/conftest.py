"""Shared test fixtures for hindsight MCP server tests."""
import importlib
import io
import json
import sys
import urllib.error
from pathlib import Path
from unittest.mock import patch

import pytest

FIXTURES = Path(__file__).parent / "fixtures" / "daemon"


def load_fixture(name: str) -> dict:
    """Load a recorded daemon response fixture (e.g., 'stats', 'documents', 'recall').

    Fixtures are recorded once from the running daemon — see LOG-mcp-server-migration.md.
    Tests assert against this real shape so daemon contract drift surfaces as a test
    failure rather than a silently-passing mock.
    """
    return json.loads((FIXTURES / f"{name}.json").read_text())


@pytest.fixture
def mcp_mod():
    """Load a fresh `scripts.mcp_server` module for each test.

    Re-imports so module-level state from prior tests doesn't leak.
    """
    sys.path.insert(0, ".")
    if "scripts.mcp_server" in sys.modules:
        del sys.modules["scripts.mcp_server"]
    return importlib.import_module("scripts.mcp_server")


@pytest.fixture
def mock_daemon():
    """Mock urllib.request.urlopen calls to the hindsight daemon.

    Yields a dict with two callables:
      - respond(payload, *, url, method, status=200) — enqueue the next response.
        Call once per expected daemon round-trip, in order; responses are served
        FIFO. url and method are REQUIRED; the mock asserts the actual request
        matches. status >= 400 raises HTTPError.
      - last_request() — capture of the most recent call (url, method, body).

    Mandatory route-pinning prevents tools from silently being routed to the
    wrong endpoint while still passing tests. The FIFO queue lets one tool make
    multiple daemon calls (e.g. a collision-check GET before a retain POST).
    """
    captured = {"url": None, "method": None, "headers": {}, "body": None}
    queue: list[dict] = []

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

        if not queue:
            raise AssertionError(
                f"unexpected daemon call with no response enqueued: "
                f"{req.get_method()} {req.full_url}"
            )
        expected = queue.pop(0)

        if not req.full_url.endswith(expected["url"]):
            raise AssertionError(
                f"unexpected URL: got {req.full_url!r}, expected suffix {expected['url']!r}"
            )
        if req.get_method() != expected["method"]:
            raise AssertionError(
                f"unexpected method: got {req.get_method()!r}, expected {expected['method']!r}"
            )

        if expected["status"] >= 400:
            raise urllib.error.HTTPError(
                req.full_url, expected["status"], "mock daemon error", {}, io.BytesIO(b"")
            )

        body = json.dumps(expected["payload"]).encode()
        return MockResponse(body)

    def respond(payload, *, url, method, status=200):
        queue.append({"payload": payload, "url": url, "method": method, "status": status})

    def last_request():
        return dict(captured)

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        yield {"respond": respond, "last_request": last_request}
