"""
test_priority.py — Unit tests for acquire/priority.py.

Pure fixture-driven.  No filesystem, no network.  Covers URL host
classification, the priority-key tuple, and the full ``walk_locations``
contract.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make ``priority.py`` importable when pytest runs the file directly.
# Matches the convention used elsewhere in code/literature_search/.
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from priority import classify_url, priority_key, walk_locations  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def loc(
    url: str,
    *,
    source: str = "openalex",
    version: str | None = None,
    is_oa: bool | None = True,
    license: str | None = "unknown",
) -> dict:
    """Build a pdf_locations[] entry with sensible defaults."""
    return {
        "url":     url,
        "source":  source,
        "version": version,
        "is_oa":   is_oa,
        "license": license,
    }


# ---------------------------------------------------------------------------
# classify_url
# ---------------------------------------------------------------------------

class TestClassifyURL:

    def test_pmc_hosts(self) -> None:
        assert classify_url("https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4097944/") == "pmc"
        assert classify_url("https://pmc.ncbi.nlm.nih.gov/articles/PMC4097944/") == "pmc"
        assert classify_url("https://europepmc.org/articles/pmc4097944?pdf=render") == "pmc"

    def test_preprint_hosts(self) -> None:
        assert classify_url("https://www.biorxiv.org/content/10.1101/abc.v1.full.pdf") == "biorxiv"
        assert classify_url("https://www.medrxiv.org/content/10.1101/xyz.v2.full.pdf") == "medrxiv"
        assert classify_url("https://arxiv.org/abs/2104.12345") == "arxiv"
        assert classify_url("https://arxiv.org/pdf/2104.12345.pdf") == "arxiv"

    def test_pubmed_landing(self) -> None:
        # PubMed abstract pages are never direct PDFs.
        assert classify_url("https://pubmed.ncbi.nlm.nih.gov/25076880") == "pubmed_landing"

    def test_doi_resolver(self) -> None:
        assert classify_url("https://doi.org/10.1038/nn1560") == "doi"
        assert classify_url("https://dx.doi.org/10.1038/nn1560") == "doi"

    def test_repository_other(self) -> None:
        assert classify_url("https://hdl.handle.net/2066/99614") == "other"
        assert classify_url("https://discovery.ucl.ac.uk/7319/") == "other"
        assert classify_url("https://www.frontiersin.org/articles/10.3389/fpsyg.2011.00255/pdf") == "other"
        assert classify_url("http://citeseerx.ist.psu.edu/viewdoc/...") == "other"

    def test_empty_and_invalid(self) -> None:
        assert classify_url("") == "other"
        assert classify_url(None) == "other"  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# priority_key
# ---------------------------------------------------------------------------

class TestPriorityKey:

    def test_pmc_outranks_other(self) -> None:
        pmc = priority_key(loc("https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1/"))
        other = priority_key(loc("https://hdl.handle.net/x/y"))
        assert pmc < other

    def test_preprint_outranks_other(self) -> None:
        bio = priority_key(loc("https://www.biorxiv.org/content/10.1101/x.full.pdf"))
        other = priority_key(loc("https://hdl.handle.net/x/y"))
        assert bio < other

    def test_other_outranks_doi(self) -> None:
        other = priority_key(loc("https://hdl.handle.net/x/y"))
        doi = priority_key(loc("https://doi.org/10.1038/nn1560"))
        assert other < doi

    def test_version_tiebreaker_within_tier(self) -> None:
        # Same host class ("other"); publishedVersion should sort before submittedVersion.
        published = priority_key(loc("https://repo.uni.edu/p.pdf", version="publishedVersion"))
        submitted = priority_key(loc("https://repo.uni.edu/q.pdf", version="submittedVersion"))
        assert published < submitted

    def test_is_oa_penalty(self) -> None:
        # Same host + same version; is_oa=True should sort before is_oa=False.
        oa = priority_key(loc("https://repo.uni.edu/p.pdf", is_oa=True))
        non_oa = priority_key(loc("https://repo.uni.edu/q.pdf", is_oa=False))
        assert oa < non_oa


# ---------------------------------------------------------------------------
# walk_locations
# ---------------------------------------------------------------------------

class TestWalkLocations:

    def test_pmc_before_publisher_repository(self) -> None:
        locs = [
            loc("https://www.frontiersin.org/articles/10.3389/fnhum.2014.00443/pdf"),
            loc("https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4097944/", license="cc-by"),
        ]
        out = walk_locations(locs)
        assert classify_url(out[0]["url"]) == "pmc"
        assert classify_url(out[1]["url"]) == "other"

    def test_preprint_before_repository(self) -> None:
        locs = [
            loc("https://hdl.handle.net/2066/99614"),
            loc("https://www.biorxiv.org/content/10.1101/abc.full.pdf"),
        ]
        out = walk_locations(locs)
        assert classify_url(out[0]["url"]) == "biorxiv"
        assert classify_url(out[1]["url"]) == "other"

    def test_doi_is_last(self) -> None:
        locs = [
            loc("https://doi.org/10.1038/nn1560"),
            loc("https://hdl.handle.net/2066/99614"),
            loc("https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1/"),
        ]
        out = walk_locations(locs)
        urls = [r["url"] for r in out]
        assert urls[0] == "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1/"
        assert urls[1] == "https://hdl.handle.net/2066/99614"
        assert urls[2] == "https://doi.org/10.1038/nn1560"

    def test_pubmed_landing_dropped(self) -> None:
        locs = [loc("https://pubmed.ncbi.nlm.nih.gov/25076880")]
        assert walk_locations(locs) == []

    def test_paywalled_dropped_by_default(self) -> None:
        locs = [
            loc("https://www.elsevier.com/article", license="proprietary"),
            loc("https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1/", license="cc-by"),
        ]
        out = walk_locations(locs)
        assert len(out) == 1
        assert classify_url(out[0]["url"]) == "pmc"

    def test_paywalled_included_when_allow_flag_set(self) -> None:
        locs = [loc("https://www.elsevier.com/article", license="proprietary")]
        out = walk_locations(locs, allow_paywalled=True)
        assert len(out) == 1
        assert out[0]["url"] == "https://www.elsevier.com/article"

    def test_missing_or_empty_url_dropped(self) -> None:
        locs = [
            {"url": "",   "source": "openalex", "version": None, "is_oa": True,  "license": "unknown"},
            {"url": None, "source": "openalex", "version": None, "is_oa": True,  "license": "unknown"},
            loc("https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1/"),
        ]
        out = walk_locations(locs)
        assert len(out) == 1
        assert classify_url(out[0]["url"]) == "pmc"

    def test_non_dict_entry_skipped(self) -> None:
        # Defensive: a corrupt pdf_locations[] containing a non-dict
        # element should not crash; just skip it.
        locs = [
            "not a dict",                                                  # type: ignore[list-item]
            loc("https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1/"),
        ]
        out = walk_locations(locs)
        assert len(out) == 1

    def test_stable_order_within_same_tier(self) -> None:
        # Equal priority keys: input order is preserved.
        locs = [
            loc("https://www.ncbi.nlm.nih.gov/pmc/articles/PMC_FIRST/"),
            loc("https://www.ncbi.nlm.nih.gov/pmc/articles/PMC_SECOND/"),
        ]
        out = walk_locations(locs)
        assert out[0]["url"].endswith("PMC_FIRST/")
        assert out[1]["url"].endswith("PMC_SECOND/")

    def test_version_tiebreaker_in_walk(self) -> None:
        locs = [
            loc("https://repo.uni.edu/p1.pdf", version="submittedVersion"),
            loc("https://repo.uni.edu/p2.pdf", version="publishedVersion"),
        ]
        out = walk_locations(locs)
        assert out[0]["version"] == "publishedVersion"
        assert out[1]["version"] == "submittedVersion"

    def test_empty_input(self) -> None:
        assert walk_locations([]) == []
        assert walk_locations(None) == []

    def test_returns_original_entries(self) -> None:
        # walk_locations preserves entry identity (no copy).  Callers
        # that need to mutate should copy explicitly.
        entry = loc("https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1/")
        out = walk_locations([entry])
        assert out[0] is entry
