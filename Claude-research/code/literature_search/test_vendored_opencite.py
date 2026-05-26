"""
Smoke tests for the vendored opencite slice and the fresh PMC client.

Three tests, each covering one of the three pieces PR-B ships in
the vendored slice (plus the new sync PMC client that exercises the
BioC converter end-to-end):

  test_pdf_location_instantiation
      -> the PDFLocation dataclass loads, fields default sensibly.

  test_parse_biorxiv_url (and the extra-cases test)
      -> the parse_identifier function recognises the URL forms our
         literature-search pipeline cares about and extracts the
         right identifier.

  test_pmc_bioc_fetch_pmc7327471 (marked 'network')
      -> the fresh sync clients/pmc.py + the vendored bioc_to_markdown
         work end-to-end against the live PMC BioC API.
         PMC7327471 (Wu et al. 2020, "Genome composition and divergence
         of the novel coronavirus", CC-BY) replaces plan §9 PR-B's
         PMC2486527, which is not in the PMC OA subset.

PDF -> Markdown conversion (via marker-pdf) is tested separately in
``test_convert.py`` because (a) marker-pdf is our own wrapper, not
vendored code, and (b) the marker test is heavy (downloads ~5 GB of
ML model weights on first run) and benefits from its own dedicated
opt-in marker.

Run from the workspace root (Claude-research/):

    pytest code/literature_search/test_vendored_opencite.py -v

To skip the live-network test (offline / CI without internet):

    pytest code/literature_search/test_vendored_opencite.py -v -m "not network"
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make sibling modules importable without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from vendored.opencite import (  # noqa: E402
    IDType,
    PDFLocation,
    bioc_to_markdown,
    parse_identifier,
)


# ---------------------------------------------------------------------------
# 1.  PDFLocation dataclass
# ---------------------------------------------------------------------------

def test_pdf_location_instantiation() -> None:
    """PDFLocation loads, required field works, optionals default sensibly."""
    loc = PDFLocation(url="https://example.org/paper.pdf", source="openalex")
    assert loc.url == "https://example.org/paper.pdf"
    assert loc.source == "openalex"
    assert loc.version == ""
    assert loc.is_oa is False
    assert loc.license == ""

    # Full instantiation with all fields.
    loc_full = PDFLocation(
        url="https://www.biorxiv.org/content/10.1101/2021.01.01.425001v2.full.pdf",
        source="biorxiv",
        version="submittedVersion",
        is_oa=True,
        license="cc-by-nc-nd",
    )
    assert loc_full.is_oa is True
    assert loc_full.license == "cc-by-nc-nd"


# ---------------------------------------------------------------------------
# 2.  parse_identifier — bioRxiv URL and a few extra cases
# ---------------------------------------------------------------------------

def test_parse_biorxiv_url() -> None:
    """parse_identifier extracts the DOI from a bioRxiv content URL."""
    url = "https://www.biorxiv.org/content/10.1101/2021.01.01.425001v2"
    id_type, value = parse_identifier(url)
    assert id_type is IDType.DOI
    assert value == "10.1101/2021.01.01.425001"


def test_parse_identifier_extra_smoke_cases() -> None:
    """A few extra cases to exercise different code paths in parse_identifier.

    Not exhaustive — opencite has its own test suite — but enough to catch
    a refresh that breaks one of the recognisers.
    """
    cases: list[tuple[str, IDType, str]] = [
        ("10.1038/nature12373",                        IDType.DOI, "10.1038/nature12373"),
        ("PMC2486527",                                 IDType.PMCID, "PMC2486527"),
        ("pmid:12345678",                              IDType.PMID, "12345678"),
        ("arxiv:2106.15928",                           IDType.ARXIV, "2106.15928"),
        ("2106.15928v3",                               IDType.ARXIV, "2106.15928"),
        ("W2034567890",                                IDType.OPENALEX, "W2034567890"),
        ("https://arxiv.org/abs/2106.15928v2",         IDType.ARXIV, "2106.15928"),
    ]
    for raw, expected_type, expected_value in cases:
        got_type, got_value = parse_identifier(raw)
        assert got_type is expected_type, f"{raw!r}: type {got_type} != {expected_type}"
        assert got_value == expected_value, f"{raw!r}: value {got_value!r} != {expected_value!r}"


# ---------------------------------------------------------------------------
# 3.  PMC BioC fetch + bioc_to_markdown (live network)
# ---------------------------------------------------------------------------

@pytest.mark.network
def test_pmc_bioc_fetch_pmc7327471(tmp_path: Path) -> None:
    """Fetch a known-good PMCID end-to-end.

    Uses the fresh sync clients/pmc.py we wrote in this PR and then
    passes the first document through the vendored bioc_to_markdown
    converter.  Asserts both layers produce non-trivial output.

    Skipped automatically with ``-m 'not network'``.
    """
    # Import here so the module-level import doesn't fire if the test
    # collection runs without the ``network`` marker enabled.
    from clients.pmc import lookup_by_pmcid

    cache_dir = tmp_path / "cache"
    result = lookup_by_pmcid("PMC7327471", cache_dir)

    assert result is not None, "PMC client returned None — network error?"
    assert isinstance(result, dict)
    assert result.get("_pmcid") == "PMC7327471"

    documents = result.get("documents")
    assert isinstance(documents, list) and documents, \
        "BioC response missing 'documents' list"

    md = bioc_to_markdown(documents[0])
    assert isinstance(md, str)
    # A real article's Markdown should be well over 500 chars and contain
    # at least one section heading.
    assert len(md) > 500, f"Suspiciously short Markdown: {len(md)} chars"
    assert "## " in md or "# " in md, "No Markdown headings in converted output"
