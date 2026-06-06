"""
landing_parser.py — Extract a PDF URL from publisher HTML (PR-H1).

When ``_attempt_walk`` fetches an OpenAlex / Unpaywall / S2-provided
URL and gets back ``text/html`` instead of ``application/pdf``, the
URL points at a publisher landing page rather than the PDF.  The
2026-06-01 wet-run showed ~825 candidate-level failures of this
shape — by a wide margin the dominant recovery angle.

Almost every published academic landing page carries the canonical
PDF URL in a meta tag for Google Scholar's benefit:

  <meta name="citation_pdf_url" content="https://...">

A smaller set (Frontiers, eLife, some PMC pages) uses:

  <link rel="alternate" type="application/pdf" href="https://...">

This module parses HTML and returns whichever signal appears first.
The caller is the orchestrator's ``_attempt_walk``, which fetches
the returned URL as a second-attempt candidate (logged as
``<original-source>+landing``).

Pure function.  No network, no I/O.  Tests in
``test_landing_parser.py``.

Why not parse with ``<a href="*.pdf">`` link-text heuristics:
publisher pages routinely include dozens of ``.pdf`` links
(supplements, figures, full-text downloads of unrelated articles in
the same issue, journal-front-matter PDFs).  The signal-to-noise
ratio of the meta tags is dramatically better.

Why not handle the response body as JSON / XML / other formats:
v1 deliberately scopes to HTML.  The APA PsycNet case
(``application/vnd.api+json``) is 8 candidates in the wet-run; a
dedicated parser for it can be added when we revisit (see PR-H
design doc §"What's deferred").
"""

from __future__ import annotations

import logging
from html.parser import HTMLParser
from urllib.parse import urljoin


logger = logging.getLogger(__name__)


class _PDFTagFinder(HTMLParser):
    """Walk a parsed HTML document; capture the first matching tag.

    Stops scanning after the first hit — calls to ``handle_starttag``
    after ``pdf_url`` is set are short-circuited.  HTMLParser doesn't
    expose a "stop parsing" hook, so the work-saving is per-tag, not
    document-wide; for realistic landing pages the meta tag is in
    ``<head>`` and the loop bails early in practice.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.pdf_url: str | None = None

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if self.pdf_url is not None:
            return

        # Build a lower-case attribute dict for case-insensitive name
        # lookup.  HTML attribute names are case-insensitive per spec;
        # publishers in practice use lowercase but the spec allows
        # capitalized forms.
        attr_map = {(k or "").lower(): (v or "") for k, v in attrs}

        if tag == "meta":
            if attr_map.get("name", "").strip().lower() == "citation_pdf_url":
                content = attr_map.get("content", "").strip()
                if content:
                    self.pdf_url = content
            return

        if tag == "link":
            rel = attr_map.get("rel", "").strip().lower()
            link_type = attr_map.get("type", "").strip().lower()
            if rel == "alternate" and link_type == "application/pdf":
                href = attr_map.get("href", "").strip()
                if href:
                    self.pdf_url = href


def _decode_html(html: bytes | str) -> str | None:
    """Decode ``html`` bytes to ``str``.  Returns None on hard failure.

    Most publisher HTML is utf-8; latin-1 is the standard fallback
    for stray bytes.  If both fail, we give up — the caller treats
    "can't parse" identically to "no PDF URL found".
    """
    if isinstance(html, str):
        return html
    try:
        return html.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return html.decode("latin-1")
        except UnicodeDecodeError:
            return None


def extract_pdf_url(html: bytes | str, base_url: str) -> str | None:
    """Return the first publisher-declared PDF URL in ``html``, absolute.

    Looks for, in order of appearance:

      1.  ``<meta name="citation_pdf_url" content="...">``
      2.  ``<link rel="alternate" type="application/pdf" href="...">``

    The returned URL is resolved against ``base_url`` so relative
    URLs become absolute.  Returns ``None`` when no signal is
    present or HTML parsing fails.

    Inputs:
      ``html``      The response body as ``bytes`` (typical) or
                    ``str`` (test convenience).  Empty / falsy
                    returns ``None`` immediately.
      ``base_url``  The URL the HTML was fetched from, used as the
                    base for ``urljoin`` resolution of relative
                    paths.  Pass an empty string if the URL was
                    already absolute and you have no base.
    """
    if not html:
        return None

    text = _decode_html(html)
    if text is None:
        return None

    finder = _PDFTagFinder()
    try:
        finder.feed(text)
    except Exception as exc:  # defensive — html.parser is forgiving
        logger.debug("landing-parser raised on %s: %r", base_url, exc)
        return None

    if not finder.pdf_url:
        return None

    return urljoin(base_url or "", finder.pdf_url)


__all__ = [
    "extract_pdf_url",
]
