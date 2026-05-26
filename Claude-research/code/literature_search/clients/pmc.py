"""
clients/pmc.py — PMC BioC REST API client.

One entry point:
  lookup_by_pmcid(pmcid, cache_dir)  — fetch a BioC JSON document
                                       for a PMC Open Access article.

Fresh sync implementation written to match this project's client
family (sibling of ``crossref.py``); not vendored from opencite
because opencite's PMC client is async and importing async code into
this otherwise-synchronous pipeline is brittle.  See
``.status/plan_2026-05-19_rec1_v2.md`` §3.5 for the rationale.

The PMC BioC OA endpoint:

  GET https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_json/<PMCID>/unicode

No auth.  NCBI's general 3 req/s policy applies.

Return semantics match the rest of the client family:

  None  → network/5xx error; caller will NOT cache.
  {}    → 404 / PMCID not in OA subset; caller WILL cache as miss.
  {...} → success; caller WILL cache.

The returned dict (on success) is the parsed BioC collection — a
dict with ``documents``, ``source``, ``date``, ``infons``.  Callers
who want Markdown should pass ``documents[0]`` to
``vendored.opencite.bioc_to_markdown``.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

try:
    import requests
except ImportError:
    raise ImportError("'requests' is required: pip install requests")

from cache import cache_get_or_fetch


logger = logging.getLogger(__name__)

_BASE = "https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_json"
_RATE_SEC = 0.34  # ~3 req/s per NCBI policy
_last_call: dict[str, float] = {}


def _throttle(host: str) -> None:
    now = time.monotonic()
    gap = now - _last_call.get(host, 0.0)
    if gap < _RATE_SEC:
        time.sleep(_RATE_SEC - gap)
    _last_call[host] = time.monotonic()


def _normalise_pmcid(pmcid: str) -> str:
    """Normalise ``"PMC123456"`` / ``"123456"`` / ``" pmc 123456 "`` to ``"PMC123456"``.

    Empty / non-string / unparseable input returns an empty string —
    the caller short-circuits to a cache miss before any network call.
    """
    if not isinstance(pmcid, str):
        return ""
    s = pmcid.strip().upper()
    if not s:
        return ""
    if s.startswith("PMC"):
        rest = s[3:].strip()
        return f"PMC{rest}" if rest.isdigit() else ""
    if s.isdigit():
        return f"PMC{s}"
    return ""


def _get(url: str, headers: dict | None = None) -> dict | None:
    host = "ncbi.nlm.nih.gov"
    for attempt in range(3):
        _throttle(host)
        try:
            resp = requests.get(url, headers=headers, timeout=15)
        except requests.RequestException as exc:
            logger.warning("pmc network error (attempt %d): %s", attempt + 1, exc)
            if attempt < 2:
                time.sleep(2)
                continue
            return None

        status = resp.status_code
        if status == 200:
            # NCBI's BioC endpoint signals "PMCID not in OA subset" by
            # returning HTTP 200 with a text/html error page
            # (body starts "[Error] : No result can be found. <BR>...").
            # Treat that as a cacheable miss, not a parse error.
            ctype = resp.headers.get("content-type", "").lower()
            if "json" not in ctype:
                logger.info(
                    "pmc 200 non-json content-type=%r for %s (treating as not-in-OA)",
                    ctype, url,
                )
                return {}
            try:
                return resp.json()
            except ValueError as exc:
                # JSON content-type but unparseable -> transient error,
                # do NOT cache (return None so caller retries next session).
                logger.warning("pmc 200 json but invalid JSON for %s: %s", url, exc)
                return None
        if status == 404:
            return {}
        if status == 429:
            logger.warning("pmc 429 rate-limit; waiting 2 s")
            time.sleep(2)
            continue
        if status >= 500:
            logger.warning("pmc %d server error; waiting 2 s", status)
            time.sleep(2)
            continue
        logger.info("pmc %d for %s", status, url)
        return {}
    return None


def lookup_by_pmcid(
    pmcid: str,
    cache_dir: Path,
    email: str = "hedannotation@gmail.com",
) -> dict | None:
    """Return the PMC BioC document for ``pmcid``, or ``None`` if not found / error.

    The returned dict is the parsed BioC collection; useful sub-keys
    are ``documents`` (list of articles), ``source``, ``date``.
    Pass ``documents[0]`` to ``vendored.opencite.bioc_to_markdown``
    for a Markdown conversion.
    """
    canonical = _normalise_pmcid(pmcid)
    if not canonical:
        logger.info("source=pmc pmcid=%r status=invalid", pmcid)
        return None

    url = f"{_BASE}/{canonical}/unicode"
    headers = {"User-Agent": f"hed-task/1.0 (mailto:{email})"}

    def _fetch() -> dict | None:
        data = _get(url, headers=headers)
        if data is None:
            return None
        # Empty list / empty dict / falsy → not in OA subset; cache as miss.
        if not data:
            return {}
        # PMC sometimes returns a list wrapping the collection.
        if isinstance(data, list):
            if not data:
                return {}
            data = data[0]
        if not isinstance(data, dict):
            return {}
        return data

    cached = cache_get_or_fetch(
        cache_dir=cache_dir,
        source="pmc_bioc",
        key=canonical,
        fetch=_fetch,
        stable=True,  # BioC for a published article is stable.
    )

    if not cached:
        logger.info("source=pmc pmcid=%s status=not_found", canonical)
        return None

    cached["_source"] = "pmc_bioc"
    cached["_pmcid"] = canonical

    logger.info("source=pmc pmcid=%s status=200", canonical)
    return cached
