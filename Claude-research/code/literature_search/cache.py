"""
cache.py — Deterministic, immutable disk cache for API responses.

One public function: cache_get_or_fetch.

Two cache layouts, picked per-call via the `stable` flag:

  Date-stamped (default; for queries whose results change over time):
      <cache_dir>/<source>/<YYYY-MM-DD>/<sha1_16hex>.json
      A fresh date stamp creates a new subdirectory; re-running on a
      different day re-fetches. Use for search endpoints, where new
      papers appear daily and citation counts grow.

  Stable (for lookups whose results are essentially fixed):
      <cache_dir>/<source>/stable/<sha1_16hex>.json
      No date in the path. Once written, served indefinitely.
      Use for lookup-by-DOI calls (a paper's metadata, OA status, etc.
      is stable; daily re-fetching is wasteful). Pass `stable=True`
      from the caller.

Each cache file is self-describing:
    {"source": "...", "key": "...", "fetched_on": "...", "response": {...}}

The key and source are stored alongside the response so that a SHA-1
key collision is detectable on read (mismatch between the stored key and
the requested key).

Stable cache entries have no automatic expiry. To force a refresh of a
stable entry, delete the file (or the whole `<source>/stable/` directory).

This mirrors the raw/ convention in OpenAlex/pull_openalex.py.

Error semantics:
    fetch() returning None  → server/network error; do NOT write to disk so
                              the next run retries the live API.
    fetch() returning {}    → legitimate "not found" (e.g. 404); write to
                              disk to avoid pointless retries.
    fetch() returning {...} → success; write to disk.
"""

import hashlib
import json
import logging
from collections.abc import Callable
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)


def _cache_key_hex(key: str) -> str:
    """Return 16 hex characters of SHA-1 over the key string."""
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def cache_get_or_fetch(
    cache_dir: Path,
    source: str,
    key: str,
    fetch: Callable[[], dict | None],
    today: str | None = None,
    stable: bool = False,
) -> dict:
    """Return the cached JSON for (source, key).

    If absent, call fetch() once.  If fetch() returns a non-None value,
    persist it and return it.  If fetch() returns None (server/network
    error), do NOT persist — return {} so the caller gets a miss and the
    next run can retry the live API.

    Args:
        cache_dir: Root cache directory.
        source:    One of "openalex", "crossref", "europepmc",
                   "semanticscholar", "unpaywall".
        key:       Arbitrary string identifying the request (e.g. the DOI).
        fetch:     Zero-argument callable returning dict | None.
                   None signals a transient error (should not be cached).
                   {} signals a legitimate not-found (safe to cache).
        today:     "YYYY-MM-DD" override; defaults to date.today().isoformat().
                   Ignored when stable=True.
        stable:    When True, use the stable (no-date) cache layout under
                   <cache_dir>/<source>/stable/. Use this for lookups whose
                   results are essentially fixed (e.g. lookup_by_doi calls);
                   delete the file manually to force a refresh. Default
                   False keeps the date-stamped layout for search-style
                   calls whose results change over time.

    Returns:
        The response dict, or {} if not found / error.
    """
    if today is None:
        today = date.today().isoformat()

    cache_hex = _cache_key_hex(key)
    bucket = "stable" if stable else today
    cache_path = Path(cache_dir) / source / bucket / f"{cache_hex}.json"

    if cache_path.exists():
        try:
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            if data.get("source") != source or data.get("key") != key:
                logger.warning(
                    "Cache key collision or metadata mismatch for %s/%s "
                    "(stored key=%r, stored source=%r); treating as miss.",
                    source, cache_hex, data.get("key"), data.get("source"),
                )
                # Fall through to re-fetch.
            else:
                logger.debug("cache_hit source=%s key=%r", source, key)
                return data["response"]
        except (json.JSONDecodeError, KeyError) as exc:
            logger.warning("Corrupted cache file %s (%s); re-fetching.", cache_path, exc)

    # Cache miss: call the fetch callable.
    response = fetch()

    if response is None:
        # Transient error (network failure, 5xx after retries).
        # Do not write to disk — allow the next run to retry the live API.
        logger.debug("cache_skip source=%s key=%r (fetch returned None)", source, key)
        return {}

    # Write to disk (includes the {} "not found" case).
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": source,
        "key": key,
        "fetched_on": today,
        "response": response,
    }
    cache_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.debug("cache_write source=%s key=%r -> %s", source, key, cache_path)

    return response
