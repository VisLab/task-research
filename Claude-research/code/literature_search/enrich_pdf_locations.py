#!/usr/bin/env python3
"""
enrich_pdf_locations.py — Populate ``pdf_locations[]`` and ``oa_status``
on every reference that carries a DOI.

For each catalog reference, this script:

1.  Looks up the DOI via the three cached clients we already have
    — OpenAlex, Unpaywall, Semantic Scholar.  Cache layout follows
    ``.status/cache_convention.md``: ``--cache-dir`` arg → ``$HED_CACHE_DIR``
    env var → ``outputs/cache/``.  Lookups are ``stable=True`` so a
    DOI's response is fetched once and served indefinitely.
2.  Extracts each response's "where can the PDF be obtained" hints into
    ``PDFLocation``-shaped dicts (mirrors opencite's shape).
3.  Three-way merge across the responses: deduplicates by canonicalised
    URL; on duplicate, keeps the first non-empty licence / version seen,
    and unions the ``is_oa`` flag (any True wins).
4.  Sets ``ref["oa_status"]`` from OpenAlex's ``open_access.oa_status``
    (preferred — wider vocabulary that includes diamond) and falls back
    to Unpaywall's ``oa_status`` then to ``"unknown"``.
5.  Normalises every per-location ``license`` string through
    ``license_policy.normalise_license`` so downstream consumers see
    SPDX-style values.  Tracks any string that mapped to ``"unknown"``
    and prints the bucket at the end for human review.

The script is **dry-run by default**: it loads everything, computes the
new ``pdf_locations[]``, prints a summary, and exits without writing.
Pass ``--write`` to persist the changes back into
``process_details.json`` / ``task_details.json``.  Staged output goes
to ``.scratch/enrich_pdf_locations/`` before being copied into place.

Idempotent: re-running on already-enriched data produces the same
result (the cached client responses are stable; the merge is
deterministic).

Usage (run from the workspace root, Claude-research/)::

    # Dry-run on the 3-item POC set
    python code/literature_search/enrich_pdf_locations.py --mode poc

    # Specific items
    python code/literature_search/enrich_pdf_locations.py \\
        --mode single --ids hed_response_inhibition

    # Full catalog, write changes
    python code/literature_search/enrich_pdf_locations.py --mode full --write

Exit codes:
    0 — clean (dry-run completed, or wet-run wrote successfully)
    1 — data issue (parse failure, count mismatch)
    2 — file not found
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable

# Allow direct invocation (python code/literature_search/enrich_pdf_locations.py)
# and ensure sibling modules (clients/, identity, etc.) are importable.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from license_policy import (  # noqa: E402
    classify_strings,
    is_intentionally_unknown,
    normalise_license,
)
from reference_compat import ref_doi  # noqa: E402

from clients.openalex import lookup_by_doi as oa_lookup  # noqa: E402
from clients.unpaywall import lookup_by_doi as up_lookup  # noqa: E402
from clients.semanticscholar import lookup_by_doi as s2_lookup  # noqa: E402


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Cache directory resolution (per .status/cache_convention.md §3)
# ---------------------------------------------------------------------------

def resolve_cache_dir(arg_value: str, workspace: Path) -> Path:
    """Resolve the cache root.

    Priority (highest to lowest):
      1.  ``--cache-dir`` argument (if explicit, i.e. not the default
          sentinel).
      2.  ``$HED_CACHE_DIR`` environment variable.
      3.  ``<workspace>/outputs/cache`` (per-repo default).
    """
    if arg_value and arg_value != "<auto>":
        # Explicit override.  Treat as absolute if it looks absolute,
        # otherwise resolve relative to the workspace.
        p = Path(arg_value)
        return p if p.is_absolute() else workspace / p
    env_val = os.environ.get("HED_CACHE_DIR")
    if env_val:
        return Path(env_val)
    return workspace / "outputs" / "cache"


# ---------------------------------------------------------------------------
# Per-source PDF-location extraction
# ---------------------------------------------------------------------------

def _normalise_url(url: str | None) -> str:
    """Light URL canonicalisation for dedup: strip whitespace, lowercase host."""
    if not isinstance(url, str):
        return ""
    s = url.strip()
    # Lowercase only the scheme://host part to keep DOI casing intact in path.
    if "://" in s:
        scheme, rest = s.split("://", 1)
        if "/" in rest:
            host, path = rest.split("/", 1)
            return f"{scheme.lower()}://{host.lower()}/{path}"
        return f"{scheme.lower()}://{rest.lower()}"
    return s


def _make_location(
    *,
    url: str | None,
    source: str,
    version: str | None,
    is_oa: bool | None,
    license_raw: str | None,
) -> dict | None:
    """Build a PDFLocation-shaped dict, or None if url is missing."""
    if not url or not isinstance(url, str) or not url.strip():
        return None
    return {
        "url":     url.strip(),
        "source":  source,
        "version": version if isinstance(version, str) and version else None,
        "is_oa":   bool(is_oa) if is_oa is not None else None,
        "license": normalise_license(license_raw),
    }


def extract_openalex_locations(resp: dict | None) -> tuple[list[dict], str, list[str]]:
    """Return (locations, oa_status, raw_license_strings).

    ``raw_license_strings`` are the licence strings as they appeared in
    the response, captured for later classification.
    """
    if not resp:
        return [], "", []
    raw_licenses: list[str] = []
    locations: list[dict] = []

    oa_block = resp.get("open_access") or {}
    oa_status_raw = oa_block.get("oa_status") or ""

    # Walk every location in the Work response.
    for loc in resp.get("locations") or []:
        if not isinstance(loc, dict):
            continue
        url = loc.get("pdf_url") or loc.get("url_for_pdf") or loc.get("landing_page_url")
        lic = loc.get("license")
        if lic is not None:
            raw_licenses.append(lic if isinstance(lic, str) else repr(lic))
        entry = _make_location(
            url=url,
            source="openalex",
            version=loc.get("version"),
            is_oa=loc.get("is_oa"),
            license_raw=lic,
        )
        if entry:
            locations.append(entry)

    return locations, oa_status_raw, raw_licenses


def extract_unpaywall_locations(resp: dict | None) -> tuple[list[dict], str, list[str]]:
    if not resp:
        return [], "", []
    raw_licenses: list[str] = []
    locations: list[dict] = []

    oa_status_raw = resp.get("oa_status") or ""

    for loc in resp.get("oa_locations") or []:
        if not isinstance(loc, dict):
            continue
        url = loc.get("url_for_pdf") or loc.get("url")
        lic = loc.get("license")
        if lic is not None:
            raw_licenses.append(lic if isinstance(lic, str) else repr(lic))
        entry = _make_location(
            url=url,
            source="unpaywall",
            version=loc.get("version"),
            is_oa=True,                              # Unpaywall only lists OA copies
            license_raw=lic,
        )
        if entry:
            locations.append(entry)

    return locations, oa_status_raw, raw_licenses


def extract_s2_locations(resp: dict | None) -> tuple[list[dict], list[str]]:
    if not resp:
        return [], []
    raw_licenses: list[str] = []
    locations: list[dict] = []

    pdf = resp.get("openAccessPdf") or {}
    if isinstance(pdf, dict) and pdf.get("url"):
        lic = pdf.get("license")
        if lic is not None:
            raw_licenses.append(lic if isinstance(lic, str) else repr(lic))
        entry = _make_location(
            url=pdf.get("url"),
            source="s2",
            version=pdf.get("status"),               # S2's analogue of "version"
            is_oa=resp.get("isOpenAccess"),
            license_raw=lic,
        )
        if entry:
            locations.append(entry)

    return locations, raw_licenses


# ---------------------------------------------------------------------------
# Three-way merge
# ---------------------------------------------------------------------------

_KNOWN_OA_STATUSES = {"gold", "hybrid", "green", "bronze", "closed", "diamond", "unknown"}


def _pick_oa_status(openalex_val: str, unpaywall_val: str) -> str:
    """Choose oa_status: prefer OpenAlex (richer vocabulary), fall back to Unpaywall."""
    def _clean(v: str) -> str:
        s = (v or "").strip().lower()
        return s if s in _KNOWN_OA_STATUSES else ""
    return _clean(openalex_val) or _clean(unpaywall_val) or "unknown"


def merge_locations(*chunks: list[dict]) -> list[dict]:
    """Deduplicate per-source location lists by canonicalised URL.

    On duplicate URL, keep the first non-empty value for ``license`` and
    ``version``; combine ``is_oa`` with OR semantics; preserve the first
    seen ``source`` (but extend it with the duplicate's source for
    provenance — comma-joined).
    """
    merged: dict[str, dict] = {}
    for chunk in chunks:
        for loc in chunk:
            url_key = _normalise_url(loc["url"])
            if not url_key:
                continue
            if url_key in merged:
                existing = merged[url_key]
                # Extend source attribution (e.g. "openalex" → "openalex,unpaywall")
                src_set = {*existing["source"].split(","), loc["source"]}
                existing["source"] = ",".join(sorted(s for s in src_set if s))
                # Prefer first non-empty / non-"unknown" license.
                if existing["license"] in ("unknown", "", None) and loc["license"]:
                    existing["license"] = loc["license"]
                if not existing["version"] and loc["version"]:
                    existing["version"] = loc["version"]
                if loc["is_oa"] is True:
                    existing["is_oa"] = True
            else:
                merged[url_key] = dict(loc)
    return list(merged.values())


# ---------------------------------------------------------------------------
# Enrichment driver
# ---------------------------------------------------------------------------

def enrich_one_reference(
    ref: dict,
    cache_dir: Path,
    email: str,
) -> tuple[bool, list[str]]:
    """Update ``ref`` in place with ``pdf_locations`` and ``oa_status``.

    Returns ``(changed, raw_license_strings_seen)``.
    """
    doi = ref_doi(ref)
    if not doi:
        return False, []

    oa_resp = oa_lookup(doi, cache_dir, email)
    up_resp = up_lookup(doi, cache_dir, email)
    s2_resp = s2_lookup(doi, cache_dir, email)

    oa_locs, oa_status_oa, oa_raw_lic = extract_openalex_locations(oa_resp)
    up_locs, oa_status_up, up_raw_lic = extract_unpaywall_locations(up_resp)
    s2_locs, s2_raw_lic                = extract_s2_locations(s2_resp)

    locations = merge_locations(oa_locs, up_locs, s2_locs)
    oa_status = _pick_oa_status(oa_status_oa, oa_status_up)

    raw_licenses = [*oa_raw_lic, *up_raw_lic, *s2_raw_lic]

    changed = False
    if ref.get("pdf_locations") != locations:
        ref["pdf_locations"] = locations
        changed = True
    if ref.get("oa_status") != oa_status:
        ref["oa_status"] = oa_status
        changed = True

    return changed, raw_licenses


# ---------------------------------------------------------------------------
# Item-level traversal (mirrors phase3_search.py's --mode poc / single / full)
# ---------------------------------------------------------------------------

# POC item IDs are reused from the search_queries module for consistency.
try:
    from search_queries import POC_ITEM_IDS as _SQ_POC
except Exception:
    _SQ_POC = ("hed_response_inhibition", "hed_working_memory_updating", "hedtsk_stroop_color_word")

POC_ITEM_IDS: tuple[str, ...] = tuple(_SQ_POC)


def _iter_items(
    processes: dict,
    tasks: list,
    mode: str,
    ids: list[str],
) -> Iterable[tuple[str, dict]]:
    """Yield (owner_id, item_dict) for items in scope."""
    procs = processes.get("processes", [])
    all_items: list[tuple[str, dict]] = []
    for p in procs:
        all_items.append((p.get("process_id", ""), p))
    for t in tasks:
        all_items.append((t.get("hedtsk_id", ""), t))

    if mode == "full":
        yield from all_items
    elif mode == "poc":
        wanted = set(POC_ITEM_IDS)
        for oid, item in all_items:
            if oid in wanted:
                yield oid, item
    elif mode == "single":
        wanted = set(ids)
        for oid, item in all_items:
            if oid in wanted:
                yield oid, item
    else:
        raise ValueError(f"unknown mode: {mode!r}")


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode", choices=["poc", "single", "full"], required=True,
                   help="poc=3 sample items, single=--ids, full=every item.")
    p.add_argument("--ids", default="",
                   help="Comma-separated owner IDs for --mode single.")
    p.add_argument("--workspace", default=".",
                   help="Workspace root (Claude-research/). Default: cwd.")
    p.add_argument("--cache-dir", default="<auto>",
                   help="Cache root. Default: $HED_CACHE_DIR or "
                        "<workspace>/outputs/cache.")
    p.add_argument("--email", default="hedannotation@gmail.com",
                   help="Polite-pool email for Crossref/OpenAlex/Unpaywall.")
    p.add_argument("--write", action="store_true",
                   help="Persist changes to process_details.json and task_details.json.")
    p.add_argument("--limit", type=int, default=0,
                   help="Cap the number of references processed (0 = no cap). "
                        "Useful for incremental dry-runs of --mode full.")
    p.add_argument("--verbose", "-v", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    ws = Path(args.workspace).resolve()
    cache_dir = resolve_cache_dir(args.cache_dir, ws)
    cache_dir.mkdir(parents=True, exist_ok=True)
    logger.info("workspace : %s", ws)
    logger.info("cache_dir : %s", cache_dir)

    p_path = ws / "process_details.json"
    t_path = ws / "task_details.json"
    for path in (p_path, t_path):
        if not path.exists():
            logger.error("not found: %s", path)
            return 2

    with p_path.open("r", encoding="utf-8") as f:
        processes = json.load(f)
    with t_path.open("r", encoding="utf-8") as f:
        tasks = json.load(f)

    ids = [i.strip() for i in args.ids.split(",") if i.strip()]
    items_iter = list(_iter_items(processes, tasks, args.mode, ids))
    logger.info("items in scope (%s): %d", args.mode, len(items_iter))

    # Walk every reference inside the in-scope items.
    n_refs_seen      = 0
    n_refs_with_doi  = 0
    n_refs_changed   = 0
    n_locations_total = 0
    oa_status_counter: Counter[str] = Counter()
    all_raw_licenses: list[str] = []

    for owner_id, item in items_iter:
        for ref in item.get("references") or []:
            n_refs_seen += 1
            if not ref_doi(ref):
                continue
            n_refs_with_doi += 1
            if args.limit and n_refs_with_doi > args.limit:
                break
            changed, raw_lic = enrich_one_reference(ref, cache_dir, args.email)
            all_raw_licenses.extend(raw_lic)
            if changed:
                n_refs_changed += 1
            n_locations_total += len(ref.get("pdf_locations") or [])
            oa_status_counter[ref.get("oa_status") or "unknown"] += 1
        if args.limit and n_refs_with_doi > args.limit:
            break

    # ---- Summary
    print()
    print("Enrichment summary:")
    print(f"  references seen            : {n_refs_seen}")
    print(f"  with DOI (processed)       : {n_refs_with_doi}")
    print(f"  changed (vs prior state)   : {n_refs_changed}")
    print(f"  total pdf_locations stored : {n_locations_total}")
    print(f"  oa_status distribution     :")
    for status, n in oa_status_counter.most_common():
        print(f"    {status:10s}  {n}")

    # ---- Licence-normaliser review report
    print()
    license_buckets = classify_strings(all_raw_licenses)
    print("Licence normalisation (raw → bucket counts):")
    for bucket, raws in sorted(license_buckets.items()):
        print(f"  {bucket:18s}  {len(raws):4d}   examples: "
              + ", ".join(raws[:3]))
    if "unknown" in license_buckets:
        # Split the unknown bucket: strings that are intentionally aliased
        # to "unknown" (e.g. Unpaywall's ``other-oa``) are documented
        # decisions and do not need human review.  Only the truly
        # unclassified strings should be flagged.
        intentional   = [r for r in license_buckets["unknown"]
                         if is_intentionally_unknown(r)]
        needs_review  = [r for r in license_buckets["unknown"]
                         if not is_intentionally_unknown(r)]
        if intentional:
            print()
            print(f"  {len(intentional)} raw string(s) intentionally classified as 'unknown' "
                  f"(no action needed):")
            for raw in intentional:
                print(f"    {raw!r}")
        if needs_review:
            print()
            print(f"NOTE: {len(needs_review)} distinct raw licence string(s) need review.")
            print("      Add an alias to code/literature_search/license_policy.py:_EXPLICIT_ALIASES")
            print("      and re-run.  Strings:")
            for raw in needs_review:
                print(f"        {raw!r}")

    # ---- Persist (only with --write)
    if args.write:
        scratch = ws / ".scratch" / "enrich_pdf_locations"
        scratch.mkdir(parents=True, exist_ok=True)
        staged_p = scratch / p_path.name
        staged_t = scratch / t_path.name
        with staged_p.open("w", encoding="utf-8") as f:
            json.dump(processes, f, indent=2, ensure_ascii=False)
            f.write("\n")
        with staged_t.open("w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)
            f.write("\n")
        shutil.copyfile(staged_p, p_path)
        shutil.copyfile(staged_t, t_path)
        print()
        print(f"wrote: {p_path.name}")
        print(f"wrote: {t_path.name}")
    else:
        print()
        print("dry-run complete; pass --write to persist changes.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
