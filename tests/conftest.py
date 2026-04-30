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
