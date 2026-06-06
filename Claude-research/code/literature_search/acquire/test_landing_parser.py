"""
test_landing_parser.py — Unit tests for acquire/landing_parser.py.

Pure fixture-driven.  No filesystem, no network.
"""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from landing_parser import extract_pdf_url  # noqa: E402


# ---------------------------------------------------------------------------
# citation_pdf_url meta tag
# ---------------------------------------------------------------------------

class TestCitationPdfUrl:

    def test_simple_absolute(self):
        html = (
            "<html><head>"
            '<meta name="citation_pdf_url" content="https://pub.example/a.pdf">'
            "</head></html>"
        )
        assert extract_pdf_url(html, "https://pub.example/article/123") == (
            "https://pub.example/a.pdf"
        )

    def test_relative_resolved_against_base(self):
        html = (
            '<meta name="citation_pdf_url" content="/article/123.pdf">'
        )
        assert extract_pdf_url(html, "https://pub.example/landing/article/123") == (
            "https://pub.example/article/123.pdf"
        )

    def test_protocol_relative_resolved(self):
        html = (
            '<meta name="citation_pdf_url" content="//cdn.example/a.pdf">'
        )
        # urljoin respects scheme of the base.
        assert extract_pdf_url(html, "https://pub.example/x") == (
            "https://cdn.example/a.pdf"
        )

    def test_case_insensitive_name(self):
        html = '<META Name="Citation_PDF_URL" Content="https://x/y.pdf">'
        assert extract_pdf_url(html, "https://x") == "https://x/y.pdf"

    def test_empty_content_returns_none(self):
        html = '<meta name="citation_pdf_url" content="">'
        assert extract_pdf_url(html, "https://x") is None

    def test_missing_content_attr_returns_none(self):
        html = '<meta name="citation_pdf_url">'
        assert extract_pdf_url(html, "https://x") is None

    def test_first_meta_wins(self):
        html = (
            '<meta name="citation_pdf_url" content="https://x/first.pdf">'
            '<meta name="citation_pdf_url" content="https://x/second.pdf">'
        )
        assert extract_pdf_url(html, "https://x") == "https://x/first.pdf"


# ---------------------------------------------------------------------------
# <link rel="alternate" type="application/pdf">
# ---------------------------------------------------------------------------

class TestLinkAlternate:

    def test_link_rel_alternate(self):
        html = (
            '<link rel="alternate" type="application/pdf" '
            'href="https://x/y.pdf">'
        )
        assert extract_pdf_url(html, "https://x") == "https://x/y.pdf"

    def test_link_relative_href_resolved(self):
        html = '<link rel="alternate" type="application/pdf" href="full.pdf">'
        assert extract_pdf_url(html, "https://x/articles/123/") == (
            "https://x/articles/123/full.pdf"
        )

    def test_link_case_insensitive_attrs(self):
        html = (
            '<LINK REL="Alternate" TYPE="Application/PDF" '
            'HREF="https://x/y.pdf">'
        )
        assert extract_pdf_url(html, "https://x") == "https://x/y.pdf"

    def test_link_wrong_rel_ignored(self):
        html = (
            '<link rel="canonical" type="application/pdf" '
            'href="https://x/y.pdf">'
        )
        assert extract_pdf_url(html, "https://x") is None

    def test_link_wrong_type_ignored(self):
        html = (
            '<link rel="alternate" type="text/html" href="https://x/y.html">'
        )
        assert extract_pdf_url(html, "https://x") is None


# ---------------------------------------------------------------------------
# Precedence and document-order behaviour
# ---------------------------------------------------------------------------

class TestOrdering:

    def test_meta_before_link_wins_when_both_present(self):
        html = (
            '<meta name="citation_pdf_url" content="https://x/meta.pdf">'
            '<link rel="alternate" type="application/pdf" '
            'href="https://x/link.pdf">'
        )
        assert extract_pdf_url(html, "https://x") == "https://x/meta.pdf"

    def test_link_before_meta_wins_when_both_present(self):
        # We take whichever appears first in document order.
        html = (
            '<link rel="alternate" type="application/pdf" '
            'href="https://x/link.pdf">'
            '<meta name="citation_pdf_url" content="https://x/meta.pdf">'
        )
        assert extract_pdf_url(html, "https://x") == "https://x/link.pdf"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:

    def test_no_pdf_signal_returns_none(self):
        html = "<html><head><title>No PDF here</title></head></html>"
        assert extract_pdf_url(html, "https://x") is None

    def test_empty_bytes_returns_none(self):
        assert extract_pdf_url(b"", "https://x") is None

    def test_empty_str_returns_none(self):
        assert extract_pdf_url("", "https://x") is None

    def test_none_returns_none(self):
        # The function is typed as bytes | str, but a defensive call
        # with a falsy non-string should still bail cleanly.
        assert extract_pdf_url(None, "https://x") is None  # type: ignore[arg-type]

    def test_utf8_bytes_handled(self):
        html = (
            '<meta name="citation_pdf_url" content="https://x/article-α.pdf">'
        ).encode("utf-8")
        assert extract_pdf_url(html, "https://x") == (
            "https://x/article-α.pdf"
        )

    def test_latin1_fallback_on_decode_error(self):
        # A byte that's not valid utf-8 in the document body: parser
        # should not blow up — fallback decoder takes over.
        html = (
            b'<meta name="citation_pdf_url" content="https://x/y.pdf">'
            b'<p>nasty byte \xff here</p>'
        )
        assert extract_pdf_url(html, "https://x") == "https://x/y.pdf"

    def test_malformed_html_doesnt_crash(self):
        # Wildly broken HTML — html.parser is forgiving; we should
        # either find the tag or return None, never raise.
        html = (
            "<html><head><<meta name=\"citation_pdf_url\""
            " content=\"https://x/y.pdf\"></head></html"
        )
        # Best-effort: the parser may still find the meta tag.  Either
        # outcome is acceptable; what matters is no exception escapes.
        result = extract_pdf_url(html, "https://x")
        assert result is None or result == "https://x/y.pdf"

    def test_no_base_url_keeps_absolute(self):
        html = (
            '<meta name="citation_pdf_url" content="https://x/y.pdf">'
        )
        assert extract_pdf_url(html, "") == "https://x/y.pdf"

    def test_no_base_url_relative_input_yields_relative_output(self):
        # urljoin("", "/foo.pdf") returns "/foo.pdf".  This documents
        # the contract — callers that want an absolute URL must pass
        # a base.  Acceptable behaviour because the orchestrator
        # always passes ``result.url`` as the base.
        html = '<meta name="citation_pdf_url" content="/foo.pdf">'
        assert extract_pdf_url(html, "") == "/foo.pdf"


# ---------------------------------------------------------------------------
# Realistic publisher-shape fixtures
# ---------------------------------------------------------------------------

# Trimmed to the relevant tags.  Real pages have hundreds of lines of
# additional markup that we don't reproduce here.

ELSEVIER_FIXTURE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>An article</title>
    <meta name="citation_doi" content="10.1016/j.example.2024.01.001">
    <meta name="citation_pdf_url" content="https://www.sciencedirect.com/science/article/pii/S0000000000000001/pdfft?md5=abc&pid=1-s2.0.pdf">
    <meta name="citation_journal_title" content="Example Journal">
</head>
<body></body>
</html>
"""

APA_FIXTURE = """
<html>
<head>
    <meta name="citation_pdf_url" content="https://psycnet.apa.org/fulltext/2024-12345-001.pdf">
</head>
</html>
"""

NATURE_FIXTURE = """
<html>
<head>
    <meta name="dc.format" content="text/html">
    <meta name="citation_pdf_url" content="https://www.nature.com/articles/s41586-024-00001-1.pdf">
</head>
</html>
"""

ELIFE_FIXTURE = """
<html>
<head>
    <link rel="alternate" type="application/pdf" href="https://cdn.elifesciences.org/articles/12345/elife-12345-v2.pdf">
</head>
</html>
"""


class TestRealisticFixtures:

    def test_elsevier(self):
        assert extract_pdf_url(ELSEVIER_FIXTURE, "https://www.sciencedirect.com/science/article/pii/X") == (
            "https://www.sciencedirect.com/science/article/pii/"
            "S0000000000000001/pdfft?md5=abc&pid=1-s2.0.pdf"
        )

    def test_apa(self):
        assert extract_pdf_url(APA_FIXTURE, "https://psycnet.apa.org/doiLanding") == (
            "https://psycnet.apa.org/fulltext/2024-12345-001.pdf"
        )

    def test_nature(self):
        assert extract_pdf_url(NATURE_FIXTURE, "https://www.nature.com/articles/X") == (
            "https://www.nature.com/articles/s41586-024-00001-1.pdf"
        )

    def test_elife(self):
        assert extract_pdf_url(ELIFE_FIXTURE, "https://elifesciences.org/articles/12345") == (
            "https://cdn.elifesciences.org/articles/12345/elife-12345-v2.pdf"
        )
