"""
test_shortcuts.py — Unit tests for acquire/shortcuts.py.

Pure fixture-driven.  No filesystem, no network.
"""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from shortcuts import (  # noqa: E402
    _normalize_arxiv_id,
    _normalize_doi,
    synthesize_id_shortcuts,
)


def _ref(*, doi=None, arxiv_id=None, pmcid=None, pmid=None,
         openalex_id=None, s2_id=None):
    return {"ids": {
        "doi": doi, "arxiv_id": arxiv_id, "pmcid": pmcid,
        "pmid": pmid, "openalex_id": openalex_id, "s2_id": s2_id,
    }}


# ---------------------------------------------------------------------------
# ID normalizers
# ---------------------------------------------------------------------------

class TestNormalizeArxivId:

    def test_bare_modern(self):
        assert _normalize_arxiv_id("2104.12345") == "2104.12345"

    def test_bare_old_style(self):
        assert _normalize_arxiv_id("cs/0102003") == "cs/0102003"

    def test_arxiv_scheme_prefix(self):
        assert _normalize_arxiv_id("arxiv:2104.12345") == "2104.12345"
        assert _normalize_arxiv_id("ARXIV:2104.12345") == "2104.12345"

    def test_url_abs_form(self):
        assert _normalize_arxiv_id(
            "https://arxiv.org/abs/2104.12345"
        ) == "2104.12345"

    def test_url_pdf_form(self):
        # ``...pdf/<id>.pdf`` — extract id, drop .pdf.
        assert _normalize_arxiv_id(
            "https://arxiv.org/pdf/2104.12345.pdf"
        ) == "2104.12345"

    def test_empty(self):
        assert _normalize_arxiv_id("") is None
        assert _normalize_arxiv_id("   ") is None


class TestNormalizeDoi:

    def test_plain(self):
        assert _normalize_doi("10.1234/foo") == "10.1234/foo"

    def test_lowercases(self):
        assert _normalize_doi("10.1234/FOO") == "10.1234/foo"

    def test_strips_doi_url_prefix(self):
        for prefix in ("https://doi.org/", "http://doi.org/",
                       "https://dx.doi.org/", "doi:"):
            assert _normalize_doi(prefix + "10.1234/foo") == "10.1234/foo"

    def test_rejects_non_doi_strings(self):
        assert _normalize_doi("not-a-doi") is None
        assert _normalize_doi("10.1234") is None  # no slash
        assert _normalize_doi("") is None


# ---------------------------------------------------------------------------
# synthesize_id_shortcuts — per-id-class behaviour
# ---------------------------------------------------------------------------

class TestSynthesizeIdShortcuts:

    def test_empty_ref_returns_empty(self):
        assert synthesize_id_shortcuts(_ref()) == []

    def test_no_ids_block_returns_empty(self):
        assert synthesize_id_shortcuts({}) == []

    def test_arxiv_id_only(self):
        out = synthesize_id_shortcuts(_ref(arxiv_id="2104.12345"))
        assert len(out) == 1
        assert out[0]["url"] == "https://arxiv.org/pdf/2104.12345"
        assert out[0]["source"] == "synthesized:arxiv"
        assert out[0]["is_oa"] is True

    def test_pmcid_not_synthesized(self):
        # PR-H5 (2026-06-04): PMC PDFs are discovered via the OA
        # Web Service in acquire_pdf._plan_walk, not as a static
        # shortcut.  This module's contract excludes them.
        out = synthesize_id_shortcuts(_ref(pmcid="PMC1234567"))
        assert out == []

    def test_doi_non_biorxiv_yields_no_shortcut(self):
        # The doi.org content-negotiation fallback was retired
        # (2026-06-02): publishers ignore Accept: application/pdf.
        out = synthesize_id_shortcuts(_ref(doi="10.1016/j.foo.2020.01.001"))
        assert out == []

    def test_biorxiv_doi_yields_biorxiv_only(self):
        out = synthesize_id_shortcuts(_ref(doi="10.1101/2023.05.01.abc"))
        sources = [loc["source"] for loc in out]
        assert sources == ["synthesized:biorxiv"]
        assert out[0]["url"] == (
            "https://www.biorxiv.org/content/10.1101/2023.05.01.abc"
            "v1.full.pdf"
        )

    def test_arxiv_and_biorxiv_both(self):
        # A ref carrying both an arXiv id and a 10.1101/ DOI gets
        # both shortcuts.  (Unusual in practice, but the function
        # shouldn't drop one in favour of the other.)
        out = synthesize_id_shortcuts(_ref(
            arxiv_id="2104.12345",
            doi="10.1101/2023.05.01.abc",
        ))
        sources = [loc["source"] for loc in out]
        assert sources == ["synthesized:arxiv", "synthesized:biorxiv"]

    def test_arxiv_url_form_in_ids_block(self):
        out = synthesize_id_shortcuts(_ref(
            arxiv_id="https://arxiv.org/abs/2104.12345",
        ))
        assert out[0]["url"] == "https://arxiv.org/pdf/2104.12345"

    def test_no_mutation_of_ref(self):
        ref = _ref(doi="10.1234/foo")
        before = dict(ref["ids"])
        synthesize_id_shortcuts(ref)
        assert ref["ids"] == before
