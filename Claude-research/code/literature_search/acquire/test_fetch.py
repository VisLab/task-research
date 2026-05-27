"""
test_fetch.py — Tests for acquire/fetch.py.

No network: every test injects a fake ``Session`` (via the ``session=``
parameter on :func:`fetch.fetch_bytes`) whose ``.get`` returns a
controllable response object.  This keeps the test surface obvious and
avoids monkey-patching ``requests`` at module scope.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable
from unittest.mock import patch

import pytest
import requests

# Make ``fetch.py`` importable when pytest is invoked from the repo
# root.  Matches the convention used in test_priority.py / test_core.py.
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

import fetch as F  # noqa: E402  the module under test


# ---------------------------------------------------------------------------
# Fake response + session
# ---------------------------------------------------------------------------

class FakeResp:
    """Minimal stand-in for a ``requests.Response``.

    Only implements the surface :func:`fetch.fetch_bytes` actually
    touches: ``status_code``, ``headers``, ``url``, ``iter_content``,
    ``close``.  Body is yielded in 64 KiB chunks by default, matching
    the production code's chunk size — keeps streaming-edge tests
    realistic.
    """

    def __init__(
        self,
        *,
        status: int = 200,
        headers: dict[str, str] | None = None,
        body: bytes = b"",
        url: str = "https://example.com/x",
        stream_error: Exception | None = None,
        chunk_size: int = 65_536,
    ) -> None:
        self.status_code = status
        self.headers = headers or {}
        self._body = body
        self.url = url
        self._stream_error = stream_error
        self._chunk_size = chunk_size
        self.closed = False

    def iter_content(self, chunk_size: int = 65_536) -> Iterable[bytes]:
        if self._stream_error is not None:
            raise self._stream_error
        if not self._body:
            return
        step = self._chunk_size if self._chunk_size else chunk_size
        for i in range(0, len(self._body), step):
            yield self._body[i : i + step]

    def close(self) -> None:
        self.closed = True


class FakeSession:
    """Captures the most recent get-call args; returns a queued response.

    Supply either a single ``FakeResp`` (re-used for every call) or an
    iterable of responses to be served in order.
    """

    def __init__(
        self,
        response: FakeResp | None = None,
        responses: Iterable[FakeResp] | None = None,
        raise_exc: Exception | None = None,
    ) -> None:
        if responses is not None:
            self._responses = list(responses)
        elif response is not None:
            self._responses = [response]
        else:
            self._responses = []
        self._raise_exc = raise_exc
        self.calls: list[dict] = []

    def get(self, url, **kwargs):
        self.calls.append({"url": url, **kwargs})
        if self._raise_exc is not None:
            raise self._raise_exc
        if not self._responses:
            raise AssertionError("FakeSession.get called more times than queued responses")
        if len(self._responses) == 1:
            return self._responses[0]
        return self._responses.pop(0)


@pytest.fixture(autouse=True)
def _clean_throttle():
    """Each test starts with no per-host throttle state."""
    F.reset_throttle()
    yield
    F.reset_throttle()


# ---------------------------------------------------------------------------
# Happy paths
# ---------------------------------------------------------------------------

def test_successful_pdf_fetch_populates_all_fields():
    body = b"%PDF-1.7\n%fake\n"
    resp = FakeResp(
        status=200,
        headers={"Content-Type": "application/pdf"},
        body=body,
        url="https://example.com/final.pdf",
    )
    sess = FakeSession(response=resp)

    r = F.fetch_bytes("https://example.com/x", session=sess, host_throttle_sec=0)

    assert r.status == 200
    assert r.url == "https://example.com/final.pdf"
    assert r.content_type == "application/pdf"
    assert r.body == body
    assert r.error is None
    assert r.is_pdf() is True


def test_content_type_strips_parameters_and_lowercases():
    resp = FakeResp(
        headers={"Content-Type": "Application/PDF; charset=binary"},
        body=b"%PDF-1.4",
    )
    r = F.fetch_bytes("https://example.com/x",
                      session=FakeSession(response=resp), host_throttle_sec=0)
    assert r.content_type == "application/pdf"
    assert r.is_pdf() is True


def test_is_pdf_false_for_html_response():
    resp = FakeResp(headers={"Content-Type": "text/html; charset=utf-8"},
                    body=b"<html>landing page</html>")
    r = F.fetch_bytes("https://example.com/x",
                      session=FakeSession(response=resp), host_throttle_sec=0)
    assert r.is_pdf() is False
    # HTML body is still returned so the caller can log it.
    assert r.body == b"<html>landing page</html>"


def test_is_pdf_false_for_octet_stream():
    # application/octet-stream is also used for zip files etc.; we
    # require the explicit PDF media type to avoid false positives.
    resp = FakeResp(headers={"Content-Type": "application/octet-stream"},
                    body=b"%PDF-1.4 maybe")
    r = F.fetch_bytes("https://example.com/x",
                      session=FakeSession(response=resp), host_throttle_sec=0)
    assert r.is_pdf() is False


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------

def test_network_exception_surfaces_as_error_with_status_zero():
    sess = FakeSession(raise_exc=requests.ConnectionError("DNS failure"))
    r = F.fetch_bytes("https://example.com/x", session=sess, host_throttle_sec=0)
    assert r.status == 0
    assert r.body == b""
    assert r.error is not None
    assert "ConnectionError" in r.error
    assert "DNS failure" in r.error


def test_timeout_exception_surfaces_as_error():
    sess = FakeSession(raise_exc=requests.Timeout("read timed out"))
    r = F.fetch_bytes("https://example.com/x", session=sess, host_throttle_sec=0)
    assert r.status == 0
    assert "Timeout" in (r.error or "")


def test_http_error_status_is_returned_normally():
    # 404 / 500 etc. are domain-level concerns, not errors at this
    # layer; the orchestrator decides whether to retry.
    resp = FakeResp(status=404,
                    headers={"Content-Type": "text/plain"},
                    body=b"not found")
    r = F.fetch_bytes("https://example.com/x",
                      session=FakeSession(response=resp), host_throttle_sec=0)
    assert r.status == 404
    assert r.error is None
    assert r.body == b"not found"


def test_stream_exception_mid_body_returns_error():
    resp = FakeResp(
        status=200,
        headers={"Content-Type": "application/pdf"},
        body=b"x",  # body is irrelevant; the stream error fires first
        stream_error=requests.ConnectionError("connection reset mid-stream"),
    )
    r = F.fetch_bytes("https://example.com/x",
                      session=FakeSession(response=resp), host_throttle_sec=0)
    # Status header came back fine, but the body couldn't be drained.
    assert r.status == 200
    assert r.body == b""
    assert "ConnectionError" in (r.error or "")


def test_oversize_body_aborts_with_error_and_empty_body():
    body = b"\x00" * 4096
    resp = FakeResp(status=200,
                    headers={"Content-Type": "application/pdf"},
                    body=body, chunk_size=1024)
    r = F.fetch_bytes(
        "https://example.com/x",
        session=FakeSession(response=resp),
        host_throttle_sec=0,
        max_bytes=2048,
    )
    assert r.status == 200
    assert r.body == b""
    assert r.error is not None
    assert "max_bytes" in r.error


def test_empty_url_short_circuits_without_calling_session():
    sess = FakeSession()
    r = F.fetch_bytes("   ", session=sess, host_throttle_sec=0)
    assert r.status == 0
    assert r.error == "empty or non-string url"
    assert sess.calls == []


def test_non_string_url_short_circuits():
    sess = FakeSession()
    r = F.fetch_bytes(None, session=sess, host_throttle_sec=0)  # type: ignore[arg-type]
    assert r.status == 0
    assert r.error == "empty or non-string url"


# ---------------------------------------------------------------------------
# Headers and request shape
# ---------------------------------------------------------------------------

def test_user_agent_default_includes_contact_email():
    # Tests the constant rather than the over-the-wire request because
    # the FakeSession captures headers in its call log.
    assert "mailto:" in F.DEFAULT_USER_AGENT
    assert "hed-acquire" in F.DEFAULT_USER_AGENT


def test_extra_headers_merge_with_defaults():
    resp = FakeResp(headers={"Content-Type": "application/pdf"}, body=b"%PDF")
    sess = FakeSession(response=resp)
    F.fetch_bytes(
        "https://example.com/x",
        session=sess,
        host_throttle_sec=0,
        extra_headers={"Authorization": "Bearer tok", "X-Custom": "v"},
    )
    sent = sess.calls[0]["headers"]
    assert sent["User-Agent"] == F.DEFAULT_USER_AGENT
    assert sent["Authorization"] == "Bearer tok"
    assert sent["X-Custom"] == "v"
    # Default Accept header still present
    assert "application/pdf" in sent["Accept"]


def test_request_uses_streaming_and_redirects():
    resp = FakeResp(headers={"Content-Type": "application/pdf"}, body=b"%PDF")
    sess = FakeSession(response=resp)
    F.fetch_bytes("https://example.com/x", session=sess, host_throttle_sec=0)
    call = sess.calls[0]
    assert call["stream"] is True
    assert call["allow_redirects"] is True


# ---------------------------------------------------------------------------
# Throttle
# ---------------------------------------------------------------------------

def test_throttle_sleeps_on_same_host_within_window():
    resp = FakeResp(headers={"Content-Type": "application/pdf"}, body=b"")
    sess = FakeSession(responses=[resp, resp])

    with patch.object(F.time, "sleep") as fake_sleep, \
         patch.object(F.time, "monotonic", side_effect=[10.0, 10.0, 10.2, 10.7, 10.7]):
        # Call 1: throttle sees no prior state -> no sleep; records t=10.0
        # Call 2: monotonic=10.2; gap=0.2; throttle_sec=1.0 -> sleeps 0.8
        F.fetch_bytes("https://example.com/a", session=sess, host_throttle_sec=1.0)
        F.fetch_bytes("https://example.com/b", session=sess, host_throttle_sec=1.0)

    assert fake_sleep.call_count == 1
    # The sleep amount should be close to (1.0 - gap).
    assert fake_sleep.call_args.args[0] == pytest.approx(0.8, abs=0.01)


def test_throttle_does_not_sleep_when_gap_already_elapsed():
    resp = FakeResp(headers={"Content-Type": "application/pdf"}, body=b"")
    sess = FakeSession(responses=[resp, resp])

    with patch.object(F.time, "sleep") as fake_sleep, \
         patch.object(F.time, "monotonic", side_effect=[10.0, 10.0, 12.0, 12.0, 12.0]):
        F.fetch_bytes("https://example.com/a", session=sess, host_throttle_sec=1.0)
        F.fetch_bytes("https://example.com/b", session=sess, host_throttle_sec=1.0)

    assert fake_sleep.call_count == 0


def test_throttle_per_host_independent():
    resp = FakeResp(headers={"Content-Type": "application/pdf"}, body=b"")
    sess = FakeSession(responses=[resp, resp])

    # Two calls to different hosts -> no inter-host throttling.
    with patch.object(F.time, "sleep") as fake_sleep, \
         patch.object(F.time, "monotonic",
                      side_effect=[10.0, 10.0, 10.1, 10.1, 10.1]):
        F.fetch_bytes("https://a.example.com/x", session=sess, host_throttle_sec=1.0)
        F.fetch_bytes("https://b.example.com/x", session=sess, host_throttle_sec=1.0)

    assert fake_sleep.call_count == 0


def test_throttle_skipped_when_threshold_is_zero():
    resp = FakeResp(headers={"Content-Type": "application/pdf"}, body=b"")
    sess = FakeSession(responses=[resp, resp, resp])

    with patch.object(F.time, "sleep") as fake_sleep:
        for _ in range(3):
            F.fetch_bytes("https://example.com/x", session=sess, host_throttle_sec=0)

    fake_sleep.assert_not_called()


def test_reset_throttle_clears_state():
    # Make a call with a non-zero threshold so _throttle actually
    # records a timestamp.  host_throttle_sec=0 short-circuits the
    # whole function (the intended fast-path for tests that don't
    # care about throttle bookkeeping), so use a small positive
    # value here and patch sleep so the test stays fast.
    resp = FakeResp(headers={"Content-Type": "application/pdf"}, body=b"")
    with patch.object(F.time, "sleep"):
        F.fetch_bytes("https://example.com/x",
                      session=FakeSession(response=resp),
                      host_throttle_sec=0.01)
    assert F._last_call  # populated
    F.reset_throttle()
    assert F._last_call == {}
