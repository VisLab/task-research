"""
shortcuts.py — Synthesize ID-derived PDF candidate URLs (PR-H2).

PR-D's ``enrich_pdf_locations.py`` populates ``ref["pdf_locations"]``
by calling OpenAlex / Unpaywall / Semantic Scholar.  Two classes of
candidate URL can be constructed without an API call as long as the
relevant identifier is on the ref:

  arXiv         arxiv.org/pdf/<arxiv_id>             from ids.arxiv_id
  bioRxiv       biorxiv.org/content/<doi>v1.full.pdf
                                                     from ids.doi (10.1101/)

PMC PDFs are handled in :func:`acquire_pdf._plan_walk` by calling
the PMC OA Web Service (:func:`clients.pmc.lookup_oa_pdf_url`).
The OA service is the principled way to discover PMC PDF URLs for
OA-subset articles; non-OA-subset articles cannot be downloaded
programmatically regardless of approach.  See
``.status/session_2026-06-04_pmc_oa.md`` for the design.

These shortcuts are appended to whatever PR-D produced.  The
orchestrator's :func:`acquire_pdf._plan_walk` calls
:func:`synthesize_id_shortcuts`, dedupes the result against existing
``pdf_locations`` URLs, and passes the combined list to
:func:`priority.walk_locations` so the same filter/sort/dispatch
pipeline applies uniformly to cataloged and synthesized candidates.

Why a separate module from :mod:`priority`:
  *  :func:`priority.synthesize_candidates` synthesizes from
     ``pdf_locations`` itself (AC URL discovery from a doi.org
     resolver entry).
  *  This module synthesizes from ``ref.ids`` — a different input
     contract.  Splitting the two keeps each function focused.

Note on medRxiv: refs with DOI prefix ``10.1101/`` could be either
bioRxiv or medRxiv.  We synthesize only the bioRxiv URL in v1
because (a) bioRxiv is the majority server for that prefix in
practice and (b) reliably distinguishing the two requires venue
metadata we don't always have on the ref.  A medRxiv-routed ref
gets stamped as a per-candidate failure when the bioRxiv URL 404s;
the diagnostic note makes the issue visible.  v2 can add medRxiv
when we know it's worth the extra fetch budget.

History:

  *  ``synthesized:pmc`` (bare ``/pdf/`` URL) tried 2026-06-01;
     dropped 2026-06-02 after 87 attempts → 0 recoveries.  PMC's
     late-2024 viewer redirects that URL to a SPA viewer page.
  *  ``synthesized:pmc`` (viewer landing URL with anchor-scan or
     Playwright) tried 2026-06-03; dropped 2026-06-04 after 0
     recoveries.  PMC's SPA gates plain HTTP behind reCAPTCHA and
     the PDF download URL requires browser-mediated session that
     Playwright's ``context.request.get`` can't supply.
  *  ``synthesized:doi`` — ``doi.org/<doi>`` with
     ``Accept: application/pdf`` content negotiation was dropped
     2026-06-02 (~66 attempts → 0 recoveries; publishers ignore
     the Accept header).
  *  PMC PDFs in scope for OA-subset articles only — handled
     via ``clients.pmc.lookup_oa_pdf_url`` (PR-H5, 2026-06-04).
     The OA Web Service is XML-based and not captcha-gated.

Pure functions.  No network, no I/O.
"""

from __future__ import annotations

from typing import Any


# Canonical URL templates.  Kept as module-level constants so they
# appear together for easy maintenance.

_ARXIV_PDF_TMPL    = "https://arxiv.org/pdf/{arxiv_id}"
_BIORXIV_PDF_TMPL  = "https://www.biorxiv.org/content/{doi}v1.full.pdf"

_BIORXIV_DOI_PREFIX = "10.1101/"


def _location(
    *,
    url: str,
    source: str,
    is_oa: bool | None = True,
    license: str | None = None,
    version: str | None = None,
) -> dict[str, Any]:
    """Build a ``pdf_locations``-shaped dict for a synthesized candidate.

    Mirrors the shape used by ``enrich_pdf_locations.py`` and
    ``priority.synthesize_candidates``: ``url``, ``source``,
    ``version``, ``is_oa``, ``license``.  Sources for synthesized
    entries use the ``synthesized:<kind>`` prefix so successful
    acquisitions stamp a recognizable provenance on
    ``local_artifacts.pdf.source_type`` (e.g. ``auto_synthesized:arxiv``).
    """
    return {
        "url": url,
        "source": source,
        "version": version,
        "is_oa": is_oa,
        "license": license,
    }


def _normalize_arxiv_id(raw: str) -> str | None:
    """Return a bare arXiv ID (e.g. ``2104.12345`` or ``cs/0102003``).

    Accepts the bare form, the ``arxiv:`` URL form, and a full
    ``arxiv.org/abs/...`` URL.  Returns None if nothing recognizable.
    """
    s = (raw or "").strip()
    if not s:
        return None
    # ``arxiv:`` URL scheme used by some metadata sources.
    if s.lower().startswith("arxiv:"):
        s = s[len("arxiv:"):].strip()
    # ``arxiv.org/abs/<id>`` or ``arxiv.org/pdf/<id>`` URL form.
    lower = s.lower()
    for marker in ("/abs/", "/pdf/"):
        idx = lower.find(marker)
        if idx >= 0:
            s = s[idx + len(marker):]
            break
    # Strip any trailing ``.pdf`` and version suffix (``v1``, ``v2``...).
    if s.lower().endswith(".pdf"):
        s = s[:-4]
    return s or None


def _normalize_doi(raw: str) -> str | None:
    """Return a DOI in lowercased, prefix-stripped canonical form.

    Strips an optional ``https://doi.org/`` (or ``http://...``)
    prefix; returns None if the result doesn't look like a DOI
    (must contain ``/`` after a ``10.`` prefix).
    """
    s = (raw or "").strip().lower()
    if not s:
        return None
    for prefix in ("https://doi.org/", "http://doi.org/",
                   "https://dx.doi.org/", "http://dx.doi.org/",
                   "doi:"):
        if s.startswith(prefix):
            s = s[len(prefix):]
            break
    if not s.startswith("10.") or "/" not in s:
        return None
    return s


def synthesize_id_shortcuts(ref: dict) -> list[dict[str, Any]]:
    """Return a list of synthesized PDF candidate locations for ``ref``.

    Walks ``ref.ids`` and produces:

      *  ``arxiv``    if ``ids.arxiv_id`` is set
      *  ``biorxiv``  if ``ids.doi`` starts with ``10.1101/``

    All entries carry ``source = "synthesized:<kind>"`` so the
    catalog stamp on a successful acquisition records the route.
    Returns a fresh list (possibly empty).  No mutation of ``ref``.

    Note: PMC is intentionally NOT handled here.  PR-H5 (2026-06-04)
    routes PMC discovery through the OA Web Service in
    ``acquire_pdf._plan_walk`` instead — that returns the canonical
    OA PDF URL when the article is in the OA subset.
    """
    ids = ref.get("ids") or {}
    out: list[dict[str, Any]] = []

    arxiv_id = _normalize_arxiv_id(ids.get("arxiv_id") or "")
    if arxiv_id:
        out.append(_location(
            url=_ARXIV_PDF_TMPL.format(arxiv_id=arxiv_id),
            source="synthesized:arxiv",
        ))

    doi = _normalize_doi(ids.get("doi") or "")
    if doi and doi.startswith(_BIORXIV_DOI_PREFIX):
        out.append(_location(
            url=_BIORXIV_PDF_TMPL.format(doi=doi),
            source="synthesized:biorxiv",
        ))

    return out


__all__ = [
    "synthesize_id_shortcuts",
]
