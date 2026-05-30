"""
test_fetch_browser.py — Tests for acquire/fetch_browser.py.

No real browser is launched.  Every test injects a stub
``playwright_factory`` whose chain
(``factory() -> p -> browser -> context -> page``) returns
controllable values, so the failure-mode taxonomy and the
URL-extraction logic can be asserted without Chromium running.

Three concentric layers:

  TestACFallback              Pure helper: AC landing URL → /download.
  TestExcTag                  Pure helper: exception class name → tag.
  TestFetchViaBrowser         Happy paths and the full failure-shape
                              taxonomy, all via injected stub factory.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

# Make ``fetch_browser.py`` importable when pytest runs the file
# directly.  Matches the convention used by test_fetch.py /
# test_priority.py.
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

import fetch_browser as FB  # noqa: E402  module under test


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------

class TestACFallback:

    def test_landing_url_gets_download_suffix(self) -> None:
        url = "https://academiccommons.columbia.edu/doi/10.7916/d8rv0nsn"
        assert FB._ac_fallback_url(url) == \
            "https://academiccommons.columbia.edu/doi/10.7916/d8rv0nsn/download"

    def test_landing_url_trailing_slash_tolerated(self) -> None:
        url = "https://academiccommons.columbia.edu/doi/10.7916/abc123/"
        assert FB._ac_fallback_url(url) == \
            "https://academiccommons.columbia.edu/doi/10.7916/abc123/download"

    def test_non_ac_url_returns_none(self) -> None:
        # Non-AC repository URLs have no fallback; the caller surfaces
        # "no pdf url found" rather than fabricating a download path.
        assert FB._ac_fallback_url("https://hdl.handle.net/2066/99614") is None
        assert FB._ac_fallback_url("https://doi.org/10.7916/d8rv0nsn") is None

    def test_ac_url_with_extra_path_returns_none(self) -> None:
        # Anything beyond ``/doi/<AC-DOI>[/]`` is rejected — we do not
        # invent fallbacks for URL shapes we did not validate.
        url = "https://academiccommons.columbia.edu/doi/10.7916/d8rv0nsn/extra"
        assert FB._ac_fallback_url(url) is None

    def test_non_string_input(self) -> None:
        assert FB._ac_fallback_url(None) is None  # type: ignore[arg-type]
        assert FB._ac_fallback_url(123) is None   # type: ignore[arg-type]


class TestExcTag:

    def test_timeout_class_tagged_playwright_timeout(self) -> None:
        class TimeoutError(Exception):  # noqa: N818
            pass
        assert FB._exc_tag(TimeoutError("x")) == "playwright_timeout"

    def test_non_timeout_class_uses_class_name(self) -> None:
        class ConnectError(Exception):
            pass
        assert FB._exc_tag(ConnectError("x")) == "ConnectError"


# ---------------------------------------------------------------------------
# Stub Playwright surface
# ---------------------------------------------------------------------------

class _StubResponse:
    """Stands in for a Playwright ``APIResponse``.

    Implements only the surface :func:`fetch_via_browser` actually
    touches: ``status``, ``ok``, ``headers``, ``body()``.  ``body_exc``
    lets a test inject an exception out of ``body()`` to exercise
    the body-read failure branch.
    """

    def __init__(
        self,
        *,
        status: int = 200,
        headers: dict[str, str] | None = None,
        body: bytes | bytearray | object = b"",
        body_exc: Exception | None = None,
    ) -> None:
        self.status = status
        self.headers = headers or {}
        self._body = body
        self._body_exc = body_exc

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300

    def body(self) -> Any:
        if self._body_exc is not None:
            raise self._body_exc
        return self._body


class _StubRequest:
    """Stub of ``BrowserContext.request``.

    ``response`` is the response handed back by ``.get(url, ...)``.
    ``get_exc`` lets a test raise out of ``.get`` (timeout, network
    error).  ``last_get`` records the call site for the dispatch
    assertions.
    """

    def __init__(self, response: _StubResponse | None = None,
                 get_exc: Exception | None = None) -> None:
        self._response = response or _StubResponse()
        self._get_exc = get_exc
        self.last_get: dict[str, Any] | None = None

    def get(self, url: str, **kwargs: Any) -> _StubResponse:
        self.last_get = {"url": url, **kwargs}
        if self._get_exc is not None:
            raise self._get_exc
        return self._response


class _StubPage:
    """Stub of a Playwright ``Page``.

    ``meta_url`` is the value returned by ``evaluate`` (i.e. what
    the meta-tag scrape would have found).  ``goto_exc`` /
    ``evaluate_exc`` inject errors out of the matching method.
    """

    def __init__(
        self,
        *,
        meta_url: str | None = None,
        goto_exc: Exception | None = None,
        wait_exc: Exception | None = None,
        evaluate_exc: Exception | None = None,
    ) -> None:
        self._meta_url = meta_url
        self._goto_exc = goto_exc
        self._wait_exc = wait_exc
        self._evaluate_exc = evaluate_exc
        self.goto_calls: list[dict[str, Any]] = []
        self.wait_calls: list[dict[str, Any]] = []
        self.evaluate_calls: list[Any] = []

    def goto(self, url: str, **kwargs: Any) -> None:
        self.goto_calls.append({"url": url, **kwargs})
        if self._goto_exc is not None:
            raise self._goto_exc

    def wait_for_load_state(self, state: str, **kwargs: Any) -> None:
        self.wait_calls.append({"state": state, **kwargs})
        if self._wait_exc is not None:
            raise self._wait_exc

    def evaluate(self, js: str) -> Any:
        self.evaluate_calls.append(js)
        if self._evaluate_exc is not None:
            raise self._evaluate_exc
        return self._meta_url


class _StubContext:
    """Stub of a Playwright ``BrowserContext``.

    Holds the ``request`` stub and the page returned by ``new_page``.
    """

    def __init__(self, page: _StubPage, request: _StubRequest,
                 user_agent: str | None = None) -> None:
        self._page = page
        self.request = request
        self.user_agent = user_agent

    def new_page(self) -> _StubPage:
        return self._page


class _StubBrowser:
    """Stub of a Playwright ``Browser``.

    ``new_context`` accepts ``user_agent`` (captured for assertion).
    ``close`` is recorded so tests can verify lifecycle hygiene.
    """

    def __init__(self, context: _StubContext) -> None:
        self._context = context
        self.closed = False
        self.last_context_kwargs: dict[str, Any] = {}

    def new_context(self, **kwargs: Any) -> _StubContext:
        self.last_context_kwargs = kwargs
        # Pass the user_agent through so the test can read it from the
        # context as well.
        if "user_agent" in kwargs:
            self._context.user_agent = kwargs["user_agent"]
        return self._context

    def close(self) -> None:
        self.closed = True


class _StubChromium:

    def __init__(self, browser: _StubBrowser, launch_exc: Exception | None = None) -> None:
        self._browser = browser
        self._launch_exc = launch_exc
        self.last_launch_kwargs: dict[str, Any] = {}

    def launch(self, **kwargs: Any) -> _StubBrowser:
        self.last_launch_kwargs = kwargs
        if self._launch_exc is not None:
            raise self._launch_exc
        return self._browser


class _StubPW:

    def __init__(self, chromium: _StubChromium) -> None:
        self.chromium = chromium


class _StubFactoryCM:
    """Context manager whose ``__enter__`` returns the stub PW."""

    def __init__(self, pw: _StubPW) -> None:
        self._pw = pw
        self.entered = False
        self.exited = False

    def __enter__(self) -> _StubPW:
        self.entered = True
        return self._pw

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.exited = True


def _build_factory(
    *,
    meta_url: str | None = None,
    response: _StubResponse | None = None,
    goto_exc: Exception | None = None,
    wait_exc: Exception | None = None,
    evaluate_exc: Exception | None = None,
    get_exc: Exception | None = None,
    launch_exc: Exception | None = None,
) -> tuple[Any, dict[str, Any]]:
    """Assemble a stub factory + a handle dict for assertions.

    The handle dict is populated with references to the page, browser,
    context, etc. so tests can read what was called.
    """
    page = _StubPage(meta_url=meta_url, goto_exc=goto_exc,
                     wait_exc=wait_exc, evaluate_exc=evaluate_exc)
    request = _StubRequest(response=response, get_exc=get_exc)
    context = _StubContext(page=page, request=request)
    browser = _StubBrowser(context=context)
    chromium = _StubChromium(browser=browser, launch_exc=launch_exc)
    pw = _StubPW(chromium=chromium)
    cm = _StubFactoryCM(pw=pw)

    def factory() -> _StubFactoryCM:
        return cm

    handle = {
        "page": page, "request": request, "context": context,
        "browser": browser, "chromium": chromium, "cm": cm,
    }
    return factory, handle


# ---------------------------------------------------------------------------
# Happy paths
# ---------------------------------------------------------------------------

LANDING_URL = "https://academiccommons.columbia.edu/doi/10.7916/d8rv0nsn"
META_PDF_URL = "https://academiccommons.columbia.edu/downloads/abc.pdf"
PDF_BYTES = b"%PDF-1.7\n%fake body\n"


class TestFetchViaBrowserSuccess:

    def test_meta_tag_url_used_when_present(self) -> None:
        factory, h = _build_factory(
            meta_url=META_PDF_URL,
            response=_StubResponse(status=200,
                                   headers={"content-type": "application/pdf"},
                                   body=PDF_BYTES),
        )
        r = FB.fetch_via_browser(LANDING_URL, playwright_factory=factory)

        assert r.error is None
        assert r.status == 200
        assert r.url == META_PDF_URL
        assert r.content_type == "application/pdf"
        assert r.body == PDF_BYTES
        assert r.is_pdf() is True
        # Lifecycle: landing page navigated, network-idle wait, browser closed.
        assert h["page"].goto_calls[0]["url"] == LANDING_URL
        assert h["page"].wait_calls[0]["state"] == FB.DEFAULT_WAIT_UNTIL
        assert h["browser"].closed is True
        # Download routed through the trusted context, not bare requests.
        assert h["request"].last_get is not None
        assert h["request"].last_get["url"] == META_PDF_URL

    def test_meta_missing_falls_back_to_ac_download_url(self) -> None:
        factory, h = _build_factory(
            meta_url=None,
            response=_StubResponse(status=200,
                                   headers={"content-type": "application/pdf"},
                                   body=PDF_BYTES),
        )
        r = FB.fetch_via_browser(LANDING_URL, playwright_factory=factory)

        assert r.error is None
        assert r.url == f"{LANDING_URL}/download"
        assert r.body == PDF_BYTES
        assert h["request"].last_get["url"] == f"{LANDING_URL}/download"

    def test_user_agent_passes_through_to_context(self) -> None:
        factory, h = _build_factory(
            meta_url=META_PDF_URL,
            response=_StubResponse(headers={"content-type": "application/pdf"},
                                   body=PDF_BYTES),
        )
        custom_ua = "hed-test/1.0"
        FB.fetch_via_browser(LANDING_URL,
                             playwright_factory=factory, user_agent=custom_ua)
        assert h["browser"].last_context_kwargs.get("user_agent") == custom_ua

    def test_timeout_seconds_converted_to_milliseconds(self) -> None:
        factory, h = _build_factory(
            meta_url=META_PDF_URL,
            response=_StubResponse(headers={"content-type": "application/pdf"},
                                   body=PDF_BYTES),
        )
        FB.fetch_via_browser(LANDING_URL, playwright_factory=factory, timeout=5.0)
        # Playwright expects ms; the wrapper multiplies by 1000.
        assert h["page"].goto_calls[0]["timeout"] == 5000
        assert h["page"].wait_calls[0]["timeout"] == 5000
        assert h["request"].last_get["timeout"] == 5000

    def test_non_pdf_content_type_still_returns_body(self) -> None:
        # Mirrors fetch_bytes: the wrapper does not enforce PDF here;
        # the orchestrator's is_pdf() sniff decides whether to keep
        # the bytes.
        factory, _ = _build_factory(
            meta_url=META_PDF_URL,
            response=_StubResponse(status=200,
                                   headers={"content-type": "text/html"},
                                   body=b"<html>not a pdf</html>"),
        )
        r = FB.fetch_via_browser(LANDING_URL, playwright_factory=factory)

        assert r.error is None
        assert r.status == 200
        assert r.content_type == "text/html"
        assert r.body == b"<html>not a pdf</html>"
        assert r.is_pdf() is False

    def test_content_type_parameters_stripped_and_lowercased(self) -> None:
        factory, _ = _build_factory(
            meta_url=META_PDF_URL,
            response=_StubResponse(
                status=200,
                headers={"Content-Type": "Application/PDF; charset=binary"},
                body=PDF_BYTES,
            ),
        )
        r = FB.fetch_via_browser(LANDING_URL, playwright_factory=factory)
        assert r.content_type == "application/pdf"
        assert r.is_pdf() is True


# ---------------------------------------------------------------------------
# Failure shapes
# ---------------------------------------------------------------------------

class _StubTimeoutError(Exception):
    """Stand-in for ``playwright.sync_api.TimeoutError`` — class name
    contains ``"Timeout"`` so :func:`fetch_browser._exc_tag` maps it to
    ``"playwright_timeout"`` exactly as it would the real class.
    """


class TestFetchViaBrowserFailures:

    def test_empty_url_short_circuits(self) -> None:
        # No factory call needed; the URL check fires first.
        r = FB.fetch_via_browser("   ")
        assert r.status == 0
        assert r.error == "empty or non-string url"

    def test_non_string_url_short_circuits(self) -> None:
        r = FB.fetch_via_browser(None)  # type: ignore[arg-type]
        assert r.status == 0
        assert r.error == "empty or non-string url"

    def test_factory_raises_returns_factory_tagged_error(self) -> None:
        def bad_factory() -> Any:
            raise RuntimeError("playwright not initialised")

        r = FB.fetch_via_browser(LANDING_URL, playwright_factory=bad_factory)
        assert r.status == 0
        assert r.error == "RuntimeError: factory"

    def test_navigation_timeout_tagged_playwright_timeout(self) -> None:
        factory, _ = _build_factory(
            goto_exc=_StubTimeoutError("Timeout 30000ms exceeded"),
        )
        r = FB.fetch_via_browser(LANDING_URL, playwright_factory=factory)
        assert r.status == 0
        assert r.error == "playwright_timeout: navigation"

    def test_navigation_non_timeout_uses_class_name(self) -> None:
        class ConnectError(Exception):
            pass
        factory, _ = _build_factory(goto_exc=ConnectError("dns"))
        r = FB.fetch_via_browser(LANDING_URL, playwright_factory=factory)
        assert r.error == "ConnectError: navigation"

    def test_wait_for_load_state_timeout(self) -> None:
        factory, _ = _build_factory(
            wait_exc=_StubTimeoutError("networkidle timed out"),
        )
        r = FB.fetch_via_browser(LANDING_URL, playwright_factory=factory)
        assert r.error == "playwright_timeout: navigation"

    def test_evaluate_raises(self) -> None:
        class EvalError(Exception):
            pass
        factory, _ = _build_factory(evaluate_exc=EvalError("page crashed"))
        r = FB.fetch_via_browser(LANDING_URL, playwright_factory=factory)
        assert r.error == "EvalError: evaluate"

    def test_no_meta_no_fallback_url(self) -> None:
        # Non-AC landing URL + no meta tag → no fallback synthesised.
        factory, _ = _build_factory(meta_url=None)
        r = FB.fetch_via_browser("https://hdl.handle.net/2066/99614",
                                 playwright_factory=factory)
        assert r.status == 0
        assert r.error == "no pdf url found"

    def test_download_timeout_tagged_playwright_timeout(self) -> None:
        factory, _ = _build_factory(
            meta_url=META_PDF_URL,
            get_exc=_StubTimeoutError("APIRequest timed out"),
        )
        r = FB.fetch_via_browser(LANDING_URL, playwright_factory=factory)
        assert r.url == META_PDF_URL  # tracked to the PDF URL, not landing
        assert r.error == "playwright_timeout: download"

    def test_download_status_non_2xx_returns_download_status_error(self) -> None:
        factory, _ = _build_factory(
            meta_url=META_PDF_URL,
            response=_StubResponse(status=403,
                                   headers={"content-type": "text/html"},
                                   body=b"forbidden"),
        )
        r = FB.fetch_via_browser(LANDING_URL, playwright_factory=factory)
        assert r.status == 403
        assert r.error == "download status 403"
        assert r.body == b""

    def test_body_raises_returns_body_tagged_error(self) -> None:
        class StreamReset(Exception):
            pass
        factory, _ = _build_factory(
            meta_url=META_PDF_URL,
            response=_StubResponse(status=200,
                                   headers={"content-type": "application/pdf"},
                                   body_exc=StreamReset("connection reset")),
        )
        r = FB.fetch_via_browser(LANDING_URL, playwright_factory=factory)
        assert r.status == 200
        assert r.error == "StreamReset: body"
        assert r.body == b""

    def test_body_oversize_returns_max_bytes_error(self) -> None:
        big = b"\x00" * 5000
        factory, _ = _build_factory(
            meta_url=META_PDF_URL,
            response=_StubResponse(status=200,
                                   headers={"content-type": "application/pdf"},
                                   body=big),
        )
        r = FB.fetch_via_browser(LANDING_URL,
                                 playwright_factory=factory, max_bytes=2048)
        assert r.status == 200
        assert r.error == "body exceeds max_bytes=2048"
        assert r.body == b""

    def test_body_non_bytes_rejected(self) -> None:
        # Defensive: the stub for some reason returned a str.  We do
        # not silently encode; surface a clear error.
        factory, _ = _build_factory(
            meta_url=META_PDF_URL,
            response=_StubResponse(status=200,
                                   headers={"content-type": "application/pdf"},
                                   body="this is a string"),  # type: ignore[arg-type]
        )
        r = FB.fetch_via_browser(LANDING_URL, playwright_factory=factory)
        assert r.error == "body is not bytes"

    def test_browser_close_called_even_on_failure(self) -> None:
        factory, h = _build_factory(
            goto_exc=_StubTimeoutError("nav timeout"),
        )
        FB.fetch_via_browser(LANDING_URL, playwright_factory=factory)
        assert h["browser"].closed is True


# ---------------------------------------------------------------------------
# Default factory (ImportError path)
# ---------------------------------------------------------------------------

def test_import_error_when_playwright_not_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force the deferred Playwright import to fail; expect a clean
    FetchResult with ``error`` populated.

    We block both the package and its ``sync_api`` submodule so that
    Python's import machinery raises ``ImportError`` for either path.
    """
    monkeypatch.setitem(sys.modules, "playwright", None)
    monkeypatch.setitem(sys.modules, "playwright.sync_api", None)

    r = FB.fetch_via_browser(LANDING_URL)

    assert r.status == 0
    assert r.error is not None
    assert "playwright not installed" in r.error
