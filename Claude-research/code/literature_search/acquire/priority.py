"""
priority.py — Order pdf_locations[] entries for auto-acquisition.

Given a reference's ``pdf_locations[]`` array (populated by PR-D's
``enrich_pdf_locations.py``), return its entries in the priority order
named in plan v2 §3.4: PMC first, then preprint repositories, then
other OA copies (repositories, publisher OA pages), then DOI content
negotiation; never the bare PubMed landing page (not a direct PDF);
paywalled URLs are skipped unless the caller opts in.

Pure functions.  No network, no I/O.  Tests in ``test_priority.py``.

D-E5 (locked 2026-05-27): PR-E trusts ``pdf_locations[]`` as populated
by PR-D and never re-calls the discovery clients.  ``priority.py``
therefore takes the list as input and only sorts it; it never refers
to ``ids.pmcid`` or to any other field outside the entry it is
classifying.  Recovering a PMCID from a URL for the BioC fast path is
``acquire_markdown.py``'s concern, not this module's.
"""

from __future__ import annotations

from typing import Sequence
from urllib.parse import urlparse


# ---------------------------------------------------------------------------
# Host classification
# ---------------------------------------------------------------------------

# Order within each list does not matter — substring tests are mutually
# exclusive at the host level.  We match on substrings (rather than
# strict host equality) because PMC has several historical hostnames
# in active use.
_PMC_SUBSTRINGS = (
    "ncbi.nlm.nih.gov/pmc/articles",
    "pmc.ncbi.nlm.nih.gov",
    "europepmc.org/articles",
)
_PUBMED_LANDING_SUBSTRING = "pubmed.ncbi.nlm.nih.gov"


def classify_url(url: str | None) -> str:
    """Return one of:

      ``"pmc"``             — a direct or near-direct PMC OA article URL
      ``"biorxiv"``         — bioRxiv content URL
      ``"medrxiv"``         — medRxiv content URL
      ``"arxiv"``           — arXiv abstract or PDF URL
      ``"doi"``             — doi.org resolver (use as content-negotiation last resort)
      ``"pubmed_landing"``  — PubMed abstract landing page (never a direct PDF)
      ``"other"``           — repository / publisher / unknown host

    Empty or non-string inputs return ``"other"``.
    """
    if not isinstance(url, str) or not url:
        return "other"
    lower = url.lower()

    for sub in _PMC_SUBSTRINGS:
        if sub in lower:
            return "pmc"

    # Preprint hosts are checked before the generic "other" bucket so
    # they get priority-2 treatment instead of priority-3.
    if "biorxiv.org" in lower:
        return "biorxiv"
    if "medrxiv.org" in lower:
        return "medrxiv"
    if "arxiv.org" in lower:
        return "arxiv"

    # The PubMed landing-page host is explicitly demoted because it
    # never serves a PDF — it serves an HTML abstract page.  Including
    # it in the walk wastes a fetch and a content-type check.
    if _PUBMED_LANDING_SUBSTRING in lower:
        return "pubmed_landing"

    # doi.org is a redirect-only resolver.  Following it may or may not
    # land on a PDF depending on the publisher's HTTP content
    # negotiation — useful as a last resort.
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        host = ""
    if host == "doi.org" or host.endswith(".doi.org"):
        return "doi"

    return "other"


# ---------------------------------------------------------------------------
# Priority key
# ---------------------------------------------------------------------------

# Lower priority_key tuples sort first.  Numbers chosen with gaps so
# future tiers can be inserted without renumbering.
_HOST_PRIORITY: dict[str, int] = {
    "pmc":            10,
    "biorxiv":        20,
    "medrxiv":        20,
    "arxiv":          20,
    "other":          30,   # repositories, publisher OA pages
    "doi":            40,   # content negotiation, last resort
    "pubmed_landing": 999,  # filtered out by walk_locations; this is defensive
}


def _version_rank(version: str | None) -> int:
    """Smaller is better.  publishedVersion > acceptedManuscript >
    submittedVersion > anything else.
    """
    v = (version or "").lower()
    if v == "publishedversion":
        return 0
    if v == "acceptedmanuscript":
        return 1
    if v == "submittedversion":
        return 2
    return 3


def priority_key(loc: dict) -> tuple[int, int, int]:
    """Return a sort tuple ``(host_priority, version_rank, is_oa_penalty)``.

    Used both as the sort key inside :func:`walk_locations` and as a
    standalone hook for callers that want to inspect ordering without
    sorting.
    """
    host_pri = _HOST_PRIORITY.get(classify_url(loc.get("url")), 50)
    ver_pri = _version_rank(loc.get("version"))
    # is_oa=True is preferred (penalty 0).  is_oa=False / None gets
    # penalty 1.  This is the weakest tiebreaker — most pdf_locations
    # entries have is_oa=True since PR-D populates them from OA sources.
    is_oa_penalty = 0 if loc.get("is_oa") is True else 1
    return (host_pri, ver_pri, is_oa_penalty)


# ---------------------------------------------------------------------------
# Walk
# ---------------------------------------------------------------------------

# Licences that are paywalled by definition.  Anything that
# license_policy.normalise_license maps to one of these is skipped by
# default; --allow-paywalled opts back in.  We do NOT skip "unknown"
# licences here — many real OA copies arrive without a parseable
# licence string, and skipping them would gut the green-OA case.
_PAYWALLED_LICENSES: frozenset[str] = frozenset({"proprietary"})


def walk_locations(
    pdf_locations: Sequence[dict] | None,
    *,
    allow_paywalled: bool = False,
) -> list[dict]:
    """Return the candidates from ``pdf_locations`` in walk order.

    Filters applied **before** sorting:

      * empty or non-string URL → drop
      * ``pubmed_landing`` host class → drop (never a direct PDF)
      * licence in :data:`_PAYWALLED_LICENSES` and ``allow_paywalled=False`` → drop

    Sort is stable, so entries with equal priority keys retain their
    input order — important for reproducibility when the caller's
    upstream merge (e.g. PR-D's ``merge_locations``) places duplicates
    deterministically.

    The returned list contains the original entry dicts unchanged
    (same identity, not copies).  Callers that need to mutate entries
    should copy first.
    """
    if not pdf_locations:
        return []

    candidates: list[dict] = []
    for loc in pdf_locations:
        if not isinstance(loc, dict):
            continue
        url = loc.get("url")
        if not isinstance(url, str) or not url.strip():
            continue
        if classify_url(url) == "pubmed_landing":
            continue
        if not allow_paywalled and loc.get("license") in _PAYWALLED_LICENSES:
            continue
        candidates.append(loc)

    return sorted(candidates, key=priority_key)
