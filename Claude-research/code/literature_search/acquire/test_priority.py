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

from priority import (  # noqa: E402
    classify_url,
    fetcher_for,
    priority_key,
    synthesize_candidates,
    walk_locations,
)


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

    def test_academic_commons(self) -> None:
        # PR-F: AC needs its own tag so the orchestrator can route
        # to the browser fetcher.
        assert classify_url("https://academiccommons.columbia.edu/doi/10.7916/d8rv0nsn") == "ac"
        assert classify_url("https://academiccommons.columbia.edu/doi/10.7916/d8rv0nsn/download") == "ac"

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

    def test_ac_outranks_doi(self) -> None:
        # PR-F: synthesized AC URLs must beat the bare doi.org resolver
        # so the browser fetcher gets a shot before content negotiation.
        ac = priority_key(loc("https://academiccommons.columbia.edu/doi/10.7916/x"))
        doi = priority_key(loc("https://doi.org/10.7916/x"))
        assert ac < doi

    def test_ac_same_tier_as_other(self) -> None:
        # AC sorts at the repository tier; stable-sort lets curators
        # control which repository goes first via input order.
        ac = priority_key(loc("https://academiccommons.columbia.edu/doi/10.7916/x"))
        other = priority_key(loc("https://hdl.handle.net/x/y"))
        assert ac[0] == other[0]


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


# ---------------------------------------------------------------------------
# synthesize_candidates  (PR-F)
# ---------------------------------------------------------------------------

# AC DOI shared across these tests.  The 10.7916/ prefix is registered
# exclusively to Columbia University Libraries — see priority.py
# _AC_DOI_RESOLVER_RE.
_AC_DOI = "10.7916/d8rv0nsn"
_AC_DOI_URL = f"https://doi.org/{_AC_DOI}"
_AC_LANDING_URL = f"https://academiccommons.columbia.edu/doi/{_AC_DOI}"


class TestSynthesizeCandidates:

    def test_empty_input(self) -> None:
        assert synthesize_candidates(None) == []
        assert synthesize_candidates([]) == []

    def test_no_ac_doi_no_synthesis(self) -> None:
        locs = [loc("https://doi.org/10.1038/nn1560")]
        out = synthesize_candidates(locs)
        assert out == locs
        # Returns a fresh list, not the input itself.
        assert out is not locs

    def test_ac_doi_synthesises_landing_url(self) -> None:
        locs = [loc(_AC_DOI_URL, source="openalex", license="cc-by")]
        out = synthesize_candidates(locs)

        assert len(out) == 2
        synthetic = out[1]
        assert synthetic["url"] == _AC_LANDING_URL
        assert synthetic["source"] == "synthesized:ac"
        assert synthetic["license"] == "cc-by"
        assert synthetic["is_oa"] is True

    def test_existing_ac_entry_blocks_synthesis(self) -> None:
        # If we already have an AC URL (in any shape) the synthesis
        # step does nothing.  Avoids redundant browser calls.
        locs = [
            loc(_AC_DOI_URL),
            loc(f"{_AC_LANDING_URL}/download", source="manual"),
        ]
        out = synthesize_candidates(locs)
        assert len(out) == 2
        assert all("synthesized" not in (loc_.get("source") or "") for loc_ in out)

    def test_inherits_version_and_license_from_source_doi_entry(self) -> None:
        locs = [
            loc(_AC_DOI_URL,
                source="unpaywall",
                version="acceptedManuscript",
                license="cc-by-nc-nd",
                is_oa=True),
        ]
        out = synthesize_candidates(locs)
        synthetic = out[-1]
        assert synthetic["version"] == "acceptedManuscript"
        assert synthetic["license"] == "cc-by-nc-nd"

    def test_only_one_synthesis_per_ref(self) -> None:
        # Two AC DOIs (unusual) → at most one synthesis.
        other_ac_doi_url = "https://doi.org/10.7916/abc123"
        locs = [
            loc(_AC_DOI_URL),
            loc(other_ac_doi_url),
        ]
        out = synthesize_candidates(locs)
        synthetics = [x for x in out if x.get("source") == "synthesized:ac"]
        assert len(synthetics) == 1

    def test_non_ac_doi_with_7916_lookalike_not_synthesised(self) -> None:
        # 10.7916/ is the AC prefix; nothing else should trigger
        # synthesis even if the URL shape rhymes.
        locs = [
            loc("https://doi.org/10.7916abc"),                # missing slash
            loc("https://doi.org/10.7917/x"),                  # wrong prefix
            loc("https://doi.org/10.7916/x?ref=y"),           # query rejected
            loc("https://doi.org/10.7916/x/extra"),           # extra path rejected
        ]
        out = synthesize_candidates(locs)
        assert out == locs
        assert all(loc_.get("source") != "synthesized:ac" for loc_ in out)

    def test_dx_doi_org_subdomain_synthesises(self) -> None:
        # Historical dx.doi.org subdomain is still in some catalog rows.
        locs = [loc(f"https://dx.doi.org/{_AC_DOI}")]
        out = synthesize_candidates(locs)
        assert any(loc_.get("source") == "synthesized:ac" for loc_ in out)

    def test_non_dict_entries_ignored(self) -> None:
        # Defensive: corrupt pdf_locations entries should not crash.
        # synthesize_candidates preserves input order and identity, so
        # the non-dict element passes through unchanged — filter for
        # dicts before reading .source on the result.
        locs = ["not a dict", loc(_AC_DOI_URL)]  # type: ignore[list-item]
        out = synthesize_candidates(locs)
        synthetics = [
            x for x in out
            if isinstance(x, dict) and x.get("source") == "synthesized:ac"
        ]
        assert len(synthetics) == 1

    def test_input_not_mutated(self) -> None:
        locs = [loc(_AC_DOI_URL)]
        original_length = len(locs)
        synthesize_candidates(locs)
        assert len(locs) == original_length


# ---------------------------------------------------------------------------
# fetcher_for  (PR-F)
# ---------------------------------------------------------------------------

class TestFetcherFor:

    def test_ac_routes_to_browser(self) -> None:
        assert fetcher_for(loc(_AC_LANDING_URL)) == "browser"

    def test_pmc_routes_to_plain(self) -> None:
        assert fetcher_for(loc("https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1/")) == "plain"

    def test_publisher_routes_to_plain(self) -> None:
        assert fetcher_for(loc("https://www.frontiersin.org/x.pdf")) == "plain"

    def test_doi_resolver_routes_to_plain(self) -> None:
        # Bare doi.org needs content negotiation, not a browser.
        assert fetcher_for(loc("https://doi.org/10.1038/nn1560")) == "plain"

    def test_preprint_routes_to_plain(self) -> None:
        assert fetcher_for(loc("https://arxiv.org/pdf/2104.12345.pdf")) == "plain"

    def test_synthesised_ac_entry_routes_to_browser(self) -> None:
        # End-to-end check: walk_locations -> synthesize -> fetcher_for
        # all line up.
        locs = [loc(_AC_DOI_URL)]
        out = walk_locations(locs)
        # The bare doi.org entry stays in the walk; the synthesised AC
        # entry routes to the browser.
        synthetic = [x for x in out if x.get("source") == "synthesized:ac"]
        assert len(synthetic) == 1
        assert fetcher_for(synthetic[0]) == "browser"

    def test_non_dict_routes_to_plain(self) -> None:
        assert fetcher_for("not a dict") == "plain"  # type: ignore[arg-type]
        assert fetcher_for({}) == "plain"


# ---------------------------------------------------------------------------
# walk_locations integration with synthesis  (PR-F)
# ---------------------------------------------------------------------------

class TestWalkLocationsWithSynthesis:

    def test_ac_doi_synthesises_and_ranks_before_bare_doi(self) -> None:
        # The original input has only the bare doi.org entry.  After
        # synthesis + sort, the AC landing URL must come ahead of the
        # doi.org resolver — the bar PR-F's plan v2 §14 sets.
        locs = [loc(_AC_DOI_URL)]
        out = walk_locations(locs)
        urls = [x["url"] for x in out]
        assert urls == [_AC_LANDING_URL, _AC_DOI_URL]

    def test_ac_synthesis_loses_to_pmc(self) -> None:
        # AC sits at the repository tier; PMC still wins overall.
        locs = [
            loc(_AC_DOI_URL),
            loc("https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1/"),
        ]
        out = walk_locations(locs)
        assert classify_url(out[0]["url"]) == "pmc"

    def test_no_synthesis_when_existing_ac_url_already_in_locations(self) -> None:
        # Existing AC landing URL + AC-managed DOI → synthesise nothing.
        locs = [
            loc(_AC_DOI_URL),
            loc(_AC_LANDING_URL, source="openalex"),
        ]
        out = walk_locations(locs)
        # Both original entries make it through; no synthesised entry added.
        urls = [x["url"] for x in out]
        assert sorted(urls) == sorted([_AC_DOI_URL, _AC_LANDING_URL])
