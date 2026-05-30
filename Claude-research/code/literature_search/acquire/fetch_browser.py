"""
fetch_browser.py — Playwright-based byte fetcher for WAF'd repositories.

PR-F (plan v2 §14) introduces a second fetcher alongside
:mod:`fetch`.  ``fetch_via_browser`` mirrors the
``fetch.fetch_bytes`` contract (same :class:`fetch.FetchResult`
shape; same notion of error / status / content_type / body) but
reaches the bytes through a headless Chromium so the WAF
challenges on hosts like Columbia Academic Commons resolve before
the download.

Why a separate module:

  * The Playwright import is deferred to call time.  Callers
    without the ``[browser]`` extra installed (``pip install -e
    .[browser]`` plus ``playwright install chromium``) never see
    an ``ImportError`` at import time — they see a clean
    ``FetchResult`` with ``error="playwright not installed: ..."``
    when (and only when) they call the fetcher.
  * The Playwright surface area used here is narrow on purpose
    (``page.goto``, ``page.wait_for_load_state``,
    ``page.evaluate``, ``context.request.get``).  Keeping it in one
    module makes the mocked-test surface obvious.

Caller contract:

  ``fetch_via_browser(url, ...) -> FetchResult`` returns a
  :class:`fetch.FetchResult` for every outcome, success or
  failure.  Network / timeout / Playwright failures land as
  ``error="<category>: <detail>"`` with ``status=0`` and an
  empty body, exactly the way :func:`fetch.fetch_bytes` surfaces
  ``requests`` exceptions.  HTTP status codes (4xx / 5xx) on the
  download response surface as ``error="download status <N>"``
  with the actual status preserved.

AC-specific behaviour:

  When the landing-page URL is on ``academiccommons.columbia.edu``,
  the fetcher pulls the direct PDF URL from the rendered DOM's
  ``<meta name="citation_pdf_url">`` tag.  If that tag is absent,
  it falls back to ``<landing>/download``.  Both routes match the
  reference implementation in ``.status/ac_with_playwright.py``.
  Other hosts can also be passed; the meta-tag extraction is
  generic (it works on any host whose landing page advertises
  ``citation_pdf_url``).

Testing:

  Production callers leave ``playwright_factory`` as the default;
  tests inject a stub factory whose chain
  (``factory() -> p -> browser -> context -> page``) returns
  controllable values.  See ``test_fetch_browser.py``.
"""

from __future__ import annotations

import logging
import re
from typing import Callable, ContextManager, Mapping
from urllib.parse import urlparse

# Reuse the same FetchResult dataclass so callers can swap fetchers
# without a type translation step.
from fetch import FetchResult


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Browser-fetcher timeouts are configured in seconds (mirroring
# :func:`fetch.fetch_bytes`); Playwright internally takes
# milliseconds, so the wrapper multiplies on the way in.
DEFAULT_TIMEOUT: float = 30.0

# Same cap as :data:`fetch.DEFAULT_MAX_BYTES`; documented there.
DEFAULT_MAX_BYTES: int = 50 * 1024 * 1024

# Match :data:`fetch.DEFAULT_USER_AGENT` so server logs see the
# same caller identity regardless of which fetcher made the call.
DEFAULT_USER_AGENT: str = (
    "hed-acquire/1.0 (https://github.com/hed-standard; mailto:hedannotation@gmail.com)"
)

# Playwright's standard "load-state-finished" wait strategy.  AC's
# WAF challenge resolves once the page goes quiet on the network;
# ``networkidle`` is the documented Playwright idiom for that.
DEFAULT_WAIT_UNTIL: str = "networkidle"

# JS run inside the page to extract the canonical PDF URL.  Many
# repositories — not only AC — advertise the direct PDF via the
# ``citation_pdf_url`` meta tag, so this works as a generic
# meta-tag scraper.
_CITATION_PDF_URL_JS: str = (
    "() => { "
    "const m = document.querySelector('meta[name=\"citation_pdf_url\"]'); "
    "if (m && m.content) return m.content; "
    "return null; "
    "}"
)

# Recognise an AC landing URL so we can synthesise a ``/download``
# fallback when the meta tag is missing.  AC URLs route by DOI:
# ``https://academiccommons.columbia.edu/doi/<AC-DOI>``.  Trailing
# slash optional, no further segments after the DOI.
_AC_LANDING_RE: re.Pattern[str] = re.compile(
    r"^https?://academiccommons\.columbia\.edu/doi/(10\.7916/[^/?#]+)/?$",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ac_fallback_url(landing_url: str) -> str | None:
    """If ``landing_url`` is an AC landing-page URL, return the
    ``/download`` route; otherwise None.

    The fallback is the documented AC alternative when a paper's
    landing page lacks a ``citation_pdf_url`` meta tag (rare but
    happens for older deposits).  Anything outside the AC host gets
    no fallback — callers that need a non-AC fallback can pass it
    in once we know the shape it should take.
    """
    if not isinstance(landing_url, str):
        return None
    m = _AC_LANDING_RE.match(landing_url.strip())
    if not m:
        return None
    ac_doi = m.group(1)
    return f"https://academiccommons.columbia.edu/doi/{ac_doi}/download"


def _exc_tag(exc: BaseException) -> str:
    """Compose an error tag for a Playwright exception.

    Playwright's ``TimeoutError`` lives at ``playwright.sync_api.
    TimeoutError`` — but importing it at module scope would defeat
    the deferred-import contract.  Instead we look at the class
    name: any exception whose name contains ``"timeout"`` (case-
    insensitive) gets the ``playwright_timeout`` tag.  Everything
    else gets the exception's class name, matching the convention
    used by :func:`fetch.fetch_bytes` for ``requests`` exceptions.
    """
    name = type(exc).__name__
    if "timeout" in name.lower():
        return "playwright_timeout"
    return name


def _parse_content_type(headers: Mapping[str, str] | None) -> str:
    """Return the lower-cased content-type, parameters stripped."""
    if not headers:
        return ""
    raw = headers.get("content-type") or headers.get("Content-Type") or ""
    return raw.split(";", 1)[0].strip().lower()


def _is_blank_url(url: object) -> bool:
    return not isinstance(url, str) or not url.strip()


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

# A no-arg callable returning a Playwright context manager.  Default
# (production) is ``sync_playwright``; tests pass a stub.
PlaywrightFactory = Callable[[], ContextManager]


def fetch_via_browser(
    url: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    max_bytes: int = DEFAULT_MAX_BYTES,
    user_agent: str = DEFAULT_USER_AGENT,
    wait_until: str = DEFAULT_WAIT_UNTIL,
    playwright_factory: PlaywrightFactory | None = None,
) -> FetchResult:
    """Navigate ``url`` in a headless browser; download the PDF.

    Mirrors :func:`fetch.fetch_bytes` semantics: every outcome
    (success, network failure, timeout, missing meta tag, oversize
    body, non-200 download status) returns a :class:`FetchResult`.

    ``playwright_factory`` is the injection seam used by tests.
    When ``None``, the function imports ``sync_playwright`` lazily;
    if the import fails the function returns a ``FetchResult`` with
    ``error="playwright not installed: <detail>"``.

    Stage-by-stage error tagging keeps failure diagnosis clear:

      * ``"playwright not installed: ..."``         — import failed
      * ``"<ExcClass>: factory"``                   — factory() raised
      * ``"playwright_timeout: navigation"``        — page.goto / wait_for_load_state
      * ``"<ExcClass>: navigation"``                — non-timeout navigation error
      * ``"<ExcClass>: evaluate"``                  — page.evaluate raised
      * ``"no pdf url found"``                      — no meta tag, no fallback
      * ``"playwright_timeout: download"``          — context.request.get timed out
      * ``"<ExcClass>: download"``                  — non-timeout download error
      * ``"<ExcClass>: body"``                      — response.body() raised
      * ``"body exceeds max_bytes=<N>"``            — oversize
      * ``"download status <N>"``                   — non-2xx HTTP on the download

    On success the returned ``FetchResult.url`` is the final PDF
    URL (the meta-tag value or the fallback), not the original
    landing URL — same convention as :func:`fetch.fetch_bytes`'s
    redirect handling.
    """
    if _is_blank_url(url):
        return FetchResult(status=0, url=url or "", content_type="", body=b"",
                           error="empty or non-string url")

    # ---- Deferred Playwright import.
    if playwright_factory is None:
        try:
            from playwright.sync_api import sync_playwright  # noqa: WPS433
        except ImportError as exc:
            return FetchResult(status=0, url=url, content_type="", body=b"",
                               error=f"playwright not installed: {exc}")
        playwright_factory = sync_playwright

    timeout_ms = int(timeout * 1000)

    try:
        factory_ctx = playwright_factory()
    except Exception as exc:                          # noqa: BLE001 - intentional
        logger.info("fetch_via_browser factory error %s: %s", url, exc)
        return FetchResult(status=0, url=url, content_type="", body=b"",
                           error=f"{type(exc).__name__}: factory")

    try:
        with factory_ctx as p:
            browser = p.chromium.launch(headless=True)
            try:
                context = browser.new_context(user_agent=user_agent)
                page = context.new_page()

                # ---- Stage 1: navigate landing page (and wait for WAF / JS).
                try:
                    page.goto(url, timeout=timeout_ms)
                    page.wait_for_load_state(wait_until, timeout=timeout_ms)
                except Exception as exc:              # noqa: BLE001
                    logger.info("navigation error %s: %s", url, exc)
                    return FetchResult(status=0, url=url, content_type="",
                                       body=b"",
                                       error=f"{_exc_tag(exc)}: navigation")

                # ---- Stage 2: locate the direct PDF URL.
                try:
                    pdf_url = page.evaluate(_CITATION_PDF_URL_JS)
                except Exception as exc:              # noqa: BLE001
                    logger.info("evaluate error %s: %s", url, exc)
                    return FetchResult(status=0, url=url, content_type="",
                                       body=b"",
                                       error=f"{type(exc).__name__}: evaluate")

                if not isinstance(pdf_url, str) or not pdf_url.strip():
                    pdf_url = _ac_fallback_url(url)

                if not pdf_url:
                    return FetchResult(status=0, url=url, content_type="",
                                       body=b"", error="no pdf url found")

                # ---- Stage 3: download via the trusted browser context.
                try:
                    resp = context.request.get(pdf_url, timeout=timeout_ms)
                except Exception as exc:              # noqa: BLE001
                    logger.info("download error %s: %s", pdf_url, exc)
                    return FetchResult(status=0, url=pdf_url, content_type="",
                                       body=b"",
                                       error=f"{_exc_tag(exc)}: download")

                status = getattr(resp, "status", 0) or 0
                headers = dict(getattr(resp, "headers", {}) or {})
                content_type = _parse_content_type(headers)

                ok = getattr(resp, "ok", None)
                if ok is None:
                    ok = 200 <= status < 300
                if not ok:
                    return FetchResult(status=status, url=pdf_url,
                                       content_type=content_type, body=b"",
                                       error=f"download status {status}",
                                       headers=headers)

                try:
                    body = resp.body()
                except Exception as exc:              # noqa: BLE001
                    logger.info("body() error %s: %s", pdf_url, exc)
                    return FetchResult(status=status, url=pdf_url,
                                       content_type=content_type, body=b"",
                                       error=f"{type(exc).__name__}: body",
                                       headers=headers)

                if not isinstance(body, (bytes, bytearray)):
                    return FetchResult(status=status, url=pdf_url,
                                       content_type=content_type, body=b"",
                                       error="body is not bytes",
                                       headers=headers)
                body = bytes(body)

                if len(body) > max_bytes:
                    return FetchResult(status=status, url=pdf_url,
                                       content_type=content_type, body=b"",
                                       error=f"body exceeds max_bytes={max_bytes}",
                                       headers=headers)

                return FetchResult(status=status, url=pdf_url,
                                   content_type=content_type, body=body,
                                   error=None, headers=headers)
            finally:
                # ``browser.close()`` is harmless if launch failed
                # because we'd have raised before reaching this block;
                # if launch succeeded we always want it closed.
                try:
                    browser.close()
                except Exception:                     # noqa: BLE001
                    logger.debug("browser.close() raised; ignored", exc_info=True)
    except Exception as exc:                          # noqa: BLE001 - intentional
        # Anything that escapes the inner try / with — context-manager
        # exit failure, launch failure, etc. — surfaces as an opaque
        # FetchResult-shaped error rather than propagating.
        logger.info("fetch_via_browser unexpected error %s: %s", url, exc)
        return FetchResult(status=0, url=url, content_type="", body=b"",
                           error=f"{type(exc).__name__}: {exc}")


__all__ = [
    "DEFAULT_MAX_BYTES",
    "DEFAULT_TIMEOUT",
    "DEFAULT_USER_AGENT",
    "DEFAULT_WAIT_UNTIL",
    "PlaywrightFactory",
    "fetch_via_browser",
]
