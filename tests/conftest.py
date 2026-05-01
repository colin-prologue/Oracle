"""Shared test fixtures for hindsight MCP server tests."""
import importlib
import io
import json
import sys
import urllib.error
from unittest.mock import patch

import pytest


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
      - respond(payload, *, url=None, method=None, status=200) — register the
        next response. If url/method are given, the mock asserts the actual
        request matches; if not, it accepts any. status >= 400 raises HTTPError.
      - last_request() — capture of the most recent call (url, method, body).
    """
    captured = {"url": None, "method": None, "headers": {}, "body": None}
    next_response = {"payload": None, "url": None, "method": None, "status": 200}

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

        expect_url = next_response["url"]
        if expect_url is not None and not req.full_url.endswith(expect_url):
            raise AssertionError(
                f"unexpected URL: got {req.full_url!r}, expected suffix {expect_url!r}"
            )
        expect_method = next_response["method"]
        if expect_method is not None and req.get_method() != expect_method:
            raise AssertionError(
                f"unexpected method: got {req.get_method()!r}, expected {expect_method!r}"
            )

        status = next_response["status"]
        if status >= 400:
            raise urllib.error.HTTPError(
                req.full_url, status, "mock daemon error", {}, io.BytesIO(b"")
            )

        body = json.dumps(next_response["payload"]).encode()
        return MockResponse(body)

    def respond(payload, *, url=None, method=None, status=200):
        next_response["payload"] = payload
        next_response["url"] = url
        next_response["method"] = method
        next_response["status"] = status

    def last_request():
        return dict(captured)

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        yield {"respond": respond, "last_request": last_request}
