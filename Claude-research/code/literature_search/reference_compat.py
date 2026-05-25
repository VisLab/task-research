"""
reference_compat.py — Accessors for the unified-reference shape.

Every reference in process_details.json and task_details.json carries a
nested ``ids`` block (DOI / PMID / PMCID / OpenAlex / S2 / ArXiv).
This module provides small accessor helpers so call sites don't reach
into the dict structure directly:

    >>> from reference_compat import ref_doi, ref_pmid, ref_pmcid
    >>> ref_doi(reference)              # str | None
    '10.xxxx/yyy'

Why accessors instead of inlining ``ref["ids"]["doi"]`` everywhere:

1.  **Single point of change** if the schema moves again.  Today the
    DOI lives at ``ref["ids"]["doi"]``; before the 2026-05-19 schema
    migration it lived at ``ref["doi"]``.  A future schema bump would
    only touch this file.

2.  **Backward compatibility during migration.**  Each accessor reads
    the new (nested) shape first and falls back to the old (flat) shape
    if the nested shape is absent.  This lets the migration script, the
    Phase 3 pipeline, and any callers run safely on data that's been
    partly migrated — the helper always returns the same value
    regardless of which shape the ref happens to be in.  Once the
    migration is finalised and committed (PR-C in the v2 plan), the
    fallback branch can be removed; the module's surface stays the
    same.

3.  **Empty-string vs. None normalisation.**  Some sources write ``""``
    for "not present"; others write ``null``.  Accessors normalise both
    to ``None`` so callers can write ``if doi: ...`` without surprises.

The functions return ``None`` (never an empty string) when the field
is not populated.  All accessors are pure functions of the input
dict — no I/O, no caching, no side effects.

The accessors here cover only **identifier** fields.  Bibliographic
fields (title, authors, year, etc.) remain at the top level of the
reference object and don't need indirection.
"""

from __future__ import annotations

from typing import Any


__all__ = [
    "ref_doi",
    "ref_pmid",
    "ref_pmcid",
    "ref_openalex_id",
    "ref_s2_id",
    "ref_arxiv_id",
    "ref_ids",
    "ref_pub_id",
    "ref_oa_status",
    "ref_url",
]


# ---------------------------------------------------------------------------
# Internal: read one ID field with new-shape-first, old-shape fallback
# ---------------------------------------------------------------------------

def _read_id(ref: dict[str, Any], field: str) -> str | None:
    """Return ``ref["ids"][field]`` if set, else ``ref[field]`` if set, else None.

    Empty strings normalise to None so callers can use truthiness checks.
    """
    if not isinstance(ref, dict):
        return None

    ids = ref.get("ids")
    if isinstance(ids, dict):
        val = ids.get(field)
        if isinstance(val, str) and val:
            return val
        # Nested shape exists but this field is null/empty — that's a
        # definitive "not set"; do NOT fall through to the flat shape.
        if "ids" in ref:
            return None

    # Pre-migration fallback: flat field at the top level.
    val = ref.get(field)
    if isinstance(val, str) and val:
        return val
    return None


# ---------------------------------------------------------------------------
# Per-ID accessors
# ---------------------------------------------------------------------------

def ref_doi(ref: dict[str, Any]) -> str | None:
    """Return the DOI (e.g. ``10.xxxx/yyy``), or None if not set."""
    return _read_id(ref, "doi")


def ref_pmid(ref: dict[str, Any]) -> str | None:
    """Return the PubMed ID (digits-only string), or None if not set."""
    return _read_id(ref, "pmid")


def ref_pmcid(ref: dict[str, Any]) -> str | None:
    """Return the PMC ID (e.g. ``PMC123456``), or None if not set."""
    return _read_id(ref, "pmcid")


def ref_openalex_id(ref: dict[str, Any]) -> str | None:
    """Return the OpenAlex Work ID (e.g. ``W2034567890`` or a full URL),
    or None if not set."""
    return _read_id(ref, "openalex_id")


def ref_s2_id(ref: dict[str, Any]) -> str | None:
    """Return the Semantic Scholar paperId (40-hex string), or None if not set."""
    return _read_id(ref, "s2_id")


def ref_arxiv_id(ref: dict[str, Any]) -> str | None:
    """Return the arXiv ID (e.g. ``2106.15928``), or None if not set."""
    return _read_id(ref, "arxiv_id")


# ---------------------------------------------------------------------------
# Aggregate accessors
# ---------------------------------------------------------------------------

def ref_ids(ref: dict[str, Any]) -> dict[str, str | None]:
    """Return all six identifier fields as a dict.  Missing values are None.

    Useful when the caller wants to enumerate or copy all identifiers at
    once (e.g., when constructing a query plan that's willing to use any
    available ID).
    """
    return {
        "doi":         ref_doi(ref),
        "openalex_id": ref_openalex_id(ref),
        "pmid":        ref_pmid(ref),
        "pmcid":       ref_pmcid(ref),
        "s2_id":       ref_s2_id(ref),
        "arxiv_id":    ref_arxiv_id(ref),
    }


def ref_pub_id(ref: dict[str, Any]) -> str | None:
    """Return the canonical pub_id (e.g. ``pub_abc12345``), or None.

    pub_id stays at the top level of the reference — it's not an
    external identifier, it's the content-addressed cross-repo key.
    """
    if not isinstance(ref, dict):
        return None
    val = ref.get("pub_id")
    if isinstance(val, str) and val:
        return val
    return None


def ref_oa_status(ref: dict[str, Any]) -> str:
    """Return the OA status enum value.  Defaults to ``"unknown"`` if absent
    or unset, so callers don't need to handle missing-field cases.

    Allowed values (post-migration): gold / hybrid / green / bronze /
    closed / diamond / unknown.  An unrecognised string is returned
    verbatim; the schema validator will catch it.
    """
    if not isinstance(ref, dict):
        return "unknown"
    val = ref.get("oa_status")
    if isinstance(val, str) and val:
        return val
    return "unknown"


def ref_url(ref: dict[str, Any]) -> str | None:
    """Return the canonical URL for the reference.

    ``url`` stays at the top level of the reference (it's a location,
    not an identifier).  Most refs synthesise it from the DOI; a small
    number carry a non-DOI URL directly.
    """
    if not isinstance(ref, dict):
        return None
    val = ref.get("url")
    if isinstance(val, str) and val:
        return val
    return None
