"""
fetch.py — Plain HTTP byte fetcher with per-host throttling.

The auto-acquisition orchestrator walks ``pdf_locations[]`` and fetches
each URL until something responds with PDF bytes.  None of those URLs
go through the OpenAlex / Unpaywall / S2 clients (D-E5: PR-E never
re-calls the discovery clients); they go through this module, which
is just ``requests.get`` with three pieces of bookkeeping the rest of
PR-E expects:

  1. Per-host throttle — one ``dict[host] -> last_call`` mirroring the
     pattern in ``clients/pmc.py``.  Default is one request per second
     per host, which is conservative enough for any publisher CDN or
     repository we hit in practice.  Tests pass ``host_throttle_sec=0``.
  2. Content-type sniff — the caller decides what to do with the body
     based on ``content_type`` (the orchestrator only saves bytes when
     it sees ``application/pdf``).
  3. Size cap — body reads stop at ``max_bytes`` so a misconfigured
     URL that streams forever can't fill the disk.

The function returns a :class:`FetchResult` for both success and
recoverable failure (HTTP error status, oversized body).  Network-
level exceptions — DNS failure, connection refused, timeout, TLS
error — surface as a ``FetchResult`` with ``error`` set, ``status=0``,
and an empty body.  Callers therefore never need to catch
``requests.RequestException`` themselves.

This module is reused by PR-E session 3 (Markdown orchestrator) for
PMC image-bytes fetching and any other raw byte fetches that don't
warrant a dedicated client.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Mapping
from urllib.parse import urlparse

try:
    import requests
except ImportError as _exc:  # pragma: no cover - environment misconfig
    raise ImportError("'requests' is required: pip install requests") from _exc


logger = logging.getLogger(__name__)


# Module-level per-host throttle state.  Same pattern as
# ``clients/pmc.py:_last_call``: a monotonic-clock timestamp of the
# last call to each host.  ``reset_throttle()`` is exposed for tests.
_last_call: dict[str, float] = {}


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class FetchResult:
    """Outcome of one :func:`fetch_bytes` call.

    ``status`` is the HTTP status code (0 if the request never
    completed).  ``url`` is the final URL after redirects (the original
    URL on error).  ``content_type`` is the lower-cased value of the
    Content-Type response header (without parameters like
    ``"; charset=utf-8"``).  ``body`` is the response bytes, capped at
    ``max_bytes`` — empty on error or oversize.  ``error`` is a short
    human-readable summary when the request never produced a usable
    response (network exception or size guard); None on every HTTP
    response, even 5xx.
    """
    status: int
    url: str
    content_type: str
    body: bytes
    error: str | None = None
    headers: Mapping[str, str] = field(default_factory=dict)

    def is_pdf(self) -> bool:
        """True if the response advertises a PDF body.

        Convenience for the orchestrator's content-type sniff.  Matches
        the ``application/pdf`` media type only; some publishers send
        ``application/octet-stream`` for PDFs, but treating that as PDF
        is a footgun (it also covers zip files, tarballs, etc.), so we
        require the explicit type.
        """
        return self.content_type.startswith("application/pdf")


# ---------------------------------------------------------------------------
# Throttle
# ---------------------------------------------------------------------------

def _host_of(url: str) -> str:
    """Lower-case host component of ``url``; ``""`` if unparseable."""
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def _throttle(host: str, gap_sec: float) -> None:
    """Sleep just enough that ``host``'s next call is ``gap_sec`` apart.

    Skipped when ``gap_sec <= 0`` so tests can disable throttling
    cheaply by passing zero (rather than monkey-patching ``time.sleep``).
    """
    if gap_sec <= 0 or not host:
        return
    now = time.monotonic()
    gap = now - _last_call.get(host, 0.0)
    if gap < gap_sec:
        time.sleep(gap_sec - gap)
    _last_call[host] = time.monotonic()


def reset_throttle() -> None:
    """Clear per-host call timestamps.  Tests call this between cases."""
    _last_call.clear()


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------

# Default cap: 50 MiB.  A typical journal PDF is 1–5 MiB; a large
# methodology paper with full-resolution figures runs 10–30 MiB.  The
# cap exists to prevent a misconfigured URL from streaming
# indefinitely; legitimate PDFs of unusual size simply fail the fetch
# (the orchestrator records it and moves on).
DEFAULT_MAX_BYTES: int = 50 * 1024 * 1024

DEFAULT_TIMEOUT: float = 30.0

DEFAULT_HOST_THROTTLE_SEC: float = 1.0

# A polite-but-honest User-Agent so server logs know who is calling.
# Crossref, PMC, etc. ask requesters to identify themselves in the UA;
# this string carries the contact email so admins can reach us if our
# traffic ever looks like abuse.
DEFAULT_USER_AGENT = (
    "hed-acquire/1.0 (https://github.com/hed-standard; mailto:hedannotation@gmail.com)"
)


def fetch_bytes(
    url: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    max_bytes: int = DEFAULT_MAX_BYTES,
    host_throttle_sec: float = DEFAULT_HOST_THROTTLE_SEC,
    allow_redirects: bool = True,
    user_agent: str = DEFAULT_USER_AGENT,
    extra_headers: Mapping[str, str] | None = None,
    session: "requests.Session | None" = None,
) -> FetchResult:
    """GET ``url`` and return a :class:`FetchResult`.

    Caps body reads at ``max_bytes``; if the response exceeds that, the
    returned result has ``error`` set and ``body`` empty.  Network
    exceptions are caught and surfaced as ``error`` likewise — callers
    do not need to wrap this in try/except.

    ``host_throttle_sec`` enforces a minimum gap between successive
    calls to the same host (lower-cased netloc).  Tests can disable
    throttling by passing ``0``.

    Pass ``session`` to share a :class:`requests.Session` across many
    fetches (connection-pooling for the same host).  When omitted, a
    fresh ``requests.get`` call is used.
    """
    if not isinstance(url, str) or not url.strip():
        return FetchResult(status=0, url=url or "", content_type="", body=b"",
                           error="empty or non-string url")

    host = _host_of(url)
    _throttle(host, host_throttle_sec)

    headers = {"User-Agent": user_agent}
    # Hint to publishers that we'd like a PDF if their server does
    # content negotiation.  Many CDNs ignore this; the ones that don't
    # (notably some DOI redirects) return a more useful response.
    headers.setdefault("Accept", "application/pdf, */*;q=0.8")
    if extra_headers:
        headers.update(extra_headers)

    try:
        get = session.get if session is not None else requests.get
        resp = get(
            url,
            headers=headers,
            timeout=timeout,
            allow_redirects=allow_redirects,
            stream=True,
        )
    except requests.RequestException as exc:
        logger.info("fetch network error %s: %s", url, exc)
        return FetchResult(status=0, url=url, content_type="", body=b"",
                           error=f"{type(exc).__name__}: {exc}")

    # Pull the headers we need before we start draining the stream.
    raw_ctype = resp.headers.get("Content-Type", "") or ""
    # Strip any parameters (e.g. "; charset=utf-8") and lower-case.
    content_type = raw_ctype.split(";", 1)[0].strip().lower()
    final_url = resp.url or url
    status = resp.status_code

    # Stream the body so we can stop early at max_bytes without
    # buffering the entire response.  iter_content(chunk_size=None)
    # respects the server's framing; we pick 64KiB chunks explicitly
    # for predictable progress.
    buf = bytearray()
    oversize = False
    try:
        for chunk in resp.iter_content(chunk_size=65_536):
            if not chunk:
                continue
            buf.extend(chunk)
            if len(buf) > max_bytes:
                oversize = True
                break
    except requests.RequestException as exc:
        logger.info("fetch stream error %s: %s", url, exc)
        try:
            resp.close()
        finally:
            pass
        return FetchResult(status=status, url=final_url, content_type=content_type,
                           body=b"", error=f"{type(exc).__name__}: {exc}",
                           headers=dict(resp.headers))

    headers_out = dict(resp.headers)
    resp.close()

    if oversize:
        return FetchResult(
            status=status, url=final_url, content_type=content_type,
            body=b"",
            error=f"body exceeds max_bytes={max_bytes}",
            headers=headers_out,
        )

    return FetchResult(
        status=status,
        url=final_url,
        content_type=content_type,
        body=bytes(buf),
        error=None,
        headers=headers_out,
    )
