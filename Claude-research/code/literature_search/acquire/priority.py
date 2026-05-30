"""
priority.py — Order pdf_locations[] entries for auto-acquisition.

Given a reference's ``pdf_locations[]`` array (populated by PR-D's
``enrich_pdf_locations.py``), return its entries in the priority order
named in plan v2 §3.4: PMC first, then preprint repositories, then
other OA copies (repositories, publisher OA pages), then DOI content
negotiation; never the bare PubMed landing page (not a direct PDF);
paywalled URLs are skipped unless the caller opts in.

PR-F (plan v2 §14, locked 2026-05-30) extends this module with the
machinery needed to drive a second fetcher:

  * A new ``"ac"`` host class for Columbia Academic Commons (WAF'd;
    needs the browser fetcher from :mod:`fetch_browser`).
  * :func:`fetcher_for` — collapses host class onto a fetcher choice
    (``"plain"`` vs ``"browser"``).  The orchestrator dispatches per
    candidate by calling this.
  * :func:`synthesize_candidates` — when a reference's
    ``pdf_locations[]`` carries an AC-managed DOI on the bare
    ``doi.org`` resolver (``doi.org/10.7916/...``) but no
    ``academiccommons.columbia.edu/doi/...`` entry, synthesise the
    direct AC landing URL as a candidate.  :func:`walk_locations`
    calls this before sorting.

Pure functions.  No network, no I/O.  Tests in ``test_priority.py``.

D-E5 (locked 2026-05-27): PR-E trusts ``pdf_locations[]`` as populated
by PR-D and never re-calls the discovery clients.  ``priority.py``
therefore takes the list as input and only sorts (and now augments)
it; it never refers to ``ids.pmcid`` or to any other field outside
the entry it is classifying.  Recovering a PMCID from a URL for the
BioC fast path is ``acquire_markdown.py``'s concern, not this
module's.
"""

from __future__ import annotations

import re
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

# Columbia Academic Commons — WAF'd OA repository.  Plain ``requests``
# calls see HTML; PDFs are reachable only through a real browser
# (Playwright).  Routed to :mod:`fetch_browser` by :func:`fetcher_for`.
_AC_HOST_SUBSTRING = "academiccommons.columbia.edu"


def classify_url(url: str | None) -> str:
    """Return one of:

      ``"pmc"``             — a direct or near-direct PMC OA article URL
      ``"biorxiv"``         — bioRxiv content URL
      ``"medrxiv"``         — medRxiv content URL
      ``"arxiv"``           — arXiv abstract or PDF URL
      ``"ac"``              — Columbia Academic Commons (WAF; browser fetcher)
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

    # AC needs its own tag so the orchestrator can route to the
    # browser fetcher.  Priority-wise AC sorts at the same tier as
    # other repositories — see _HOST_PRIORITY.
    if _AC_HOST_SUBSTRING in lower:
        return "ac"

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
# future tiers can be inserted without renumbering.  ``"ac"`` shares
# the repository tier with ``"other"`` (both 30): the synthesised AC
# landing URL beats the bare ``doi.org`` resolver (40) by tier alone,
# which is the only ordering constraint PR-F's plan v2 §14 imposes.
_HOST_PRIORITY: dict[str, int] = {
    "pmc":            10,
    "biorxiv":        20,
    "medrxiv":        20,
    "arxiv":          20,
    "ac":             30,
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
# AC URL synthesis (PR-F)
# ---------------------------------------------------------------------------

# AC-managed DOIs start with the ``10.7916/`` prefix (registered
# exclusively to Columbia University Libraries per the DOI Foundation
# registry).  This pattern matches the bare ``doi.org/10.7916/...``
# resolver URL we expect to find in ``pdf_locations[]`` for any AC-
# deposited paper — that URL is what OpenAlex and Unpaywall hand us,
# never the direct AC landing URL.
#
# Trailing slash optional.  Query / fragment NOT permitted: we only
# synthesise from a clean DOI resolver URL.  Extra path segments
# (e.g. doi.org/10.7916/x/extra) are rejected — same defence as the
# AC landing-URL regex in :mod:`fetch_browser`.
_AC_DOI_RESOLVER_RE: re.Pattern[str] = re.compile(
    r"^https?://(dx\.)?doi\.org/(10\.7916/[^/?#]+)/?$",
    re.IGNORECASE,
)


def synthesize_candidates(pdf_locations: Sequence[dict] | None) -> list[dict]:
    """Return ``pdf_locations`` plus any fetcher-layer-synthesised entries.

    Today this synthesises exactly one shape: when a reference's
    ``pdf_locations[]`` carries an AC-managed DOI on the bare
    ``doi.org`` resolver (``doi.org/10.7916/...``) **and** no
    ``academiccommons.columbia.edu/doi/...`` entry is already present,
    append a synthetic candidate pointing at the AC landing URL.  The
    browser fetcher (:mod:`fetch_browser`) then extracts the direct
    PDF URL from the rendered DOM.

    The synthesised entry carries:

      ``url``     ``https://academiccommons.columbia.edu/doi/<AC-DOI>``
      ``source``  ``"synthesized:ac"``  (preserves provenance on
                  successful acquisition stamps)
      ``version`` inherited from the source ``doi.org`` entry
      ``is_oa``   inherited (defaults to ``True`` if absent)
      ``license`` inherited from the source ``doi.org`` entry

    Returns a new list; the input is not mutated.  When there is no
    synthesis to do, returns ``list(pdf_locations)`` unchanged (still a
    fresh list so the caller can mutate without affecting the input).
    """
    if not pdf_locations:
        return []

    out: list[dict] = list(pdf_locations)

    # If an AC entry is already present (in any shape), do nothing —
    # the existing entry classifies as ``"ac"`` and routes to the
    # browser fetcher via :func:`fetcher_for`.
    for loc in pdf_locations:
        if (isinstance(loc, dict)
                and isinstance(loc.get("url"), str)
                and _AC_HOST_SUBSTRING in loc["url"].lower()):
            return out

    # Otherwise: look for an AC-managed DOI on doi.org and synthesise.
    # Only one synthesis per ref — multiple AC DOIs on the same paper
    # would be unusual and adding more than one wastes browser calls.
    for loc in pdf_locations:
        if not isinstance(loc, dict):
            continue
        url = loc.get("url")
        if not isinstance(url, str):
            continue
        m = _AC_DOI_RESOLVER_RE.match(url.strip())
        if not m:
            continue
        ac_doi = m.group(2)
        out.append({
            "url":     f"https://academiccommons.columbia.edu/doi/{ac_doi}",
            "source":  "synthesized:ac",
            "version": loc.get("version"),
            "is_oa":   loc.get("is_oa", True),
            "license": loc.get("license"),
        })
        break

    return out


# ---------------------------------------------------------------------------
# Fetcher dispatch (PR-F)
# ---------------------------------------------------------------------------

def fetcher_for(loc: dict) -> str:
    """Return ``"browser"`` for hosts that require the Playwright
    fetcher, ``"plain"`` for everything else.

    The orchestrator calls this per candidate to pick between
    :func:`fetch.fetch_bytes` and :func:`fetch_browser.fetch_via_browser`.
    Today only the ``"ac"`` host class needs the browser fetcher;
    future WAF'd repositories get added here as they surface.

    Non-dict input or missing URL → ``"plain"`` (the plain fetcher
    handles the empty-URL short-circuit itself).
    """
    if not isinstance(loc, dict):
        return "plain"
    if classify_url(loc.get("url")) == "ac":
        return "browser"
    return "plain"


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

    PR-F: :func:`synthesize_candidates` runs first so any AC-shaped
    synthetic entry enters the same sort and filter pipeline as the
    original entries.

    Filters applied **before** sorting:

      * empty or non-string URL → drop
      * ``pubmed_landing`` host class → drop (never a direct PDF)
      * licence in :data:`_PAYWALLED_LICENSES` and ``allow_paywalled=False`` → drop

    Sort is stable, so entries with equal priority keys retain their
    input order — important for reproducibility when the caller's
    upstream merge (e.g. PR-D's ``merge_locations``) places duplicates
    deterministically.  Synthesised candidates are appended to the
    end of the input list and therefore tie-break *after* original
    entries at the same priority tier.

    The returned list contains the original entry dicts unchanged
    (same identity, not copies).  Synthesised entries are fresh dicts.
    Callers that need to mutate entries should copy first.
    """
    if not pdf_locations:
        return []

    augmented = synthesize_candidates(pdf_locations)

    candidates: list[dict] = []
    for loc in augmented:
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
