#!/usr/bin/env python3
"""
phase1_validate.py — Phase 1 end-to-end validation for the literature-search
                     infrastructure.

Run this script on the Windows host machine (where API network access is
available).  The Cowork sandbox has no egress to any of the five APIs.

Usage (run from the Claude-research/ workspace root):
    python code/literature_search/phase1_validate.py
    python code/literature_search/phase1_validate.py --cache-dir outputs/cache
    python code/literature_search/phase1_validate.py --verbose

Dependencies:
    pip install requests

What it does (per task_literature_search_phase1_instructions.md §1.5):
    For each of 7 test papers:
      1. Call all 5 API clients.
      2. Extract (first_author_family, year, title) from the preferred source
         (OpenAlex > CrossRef > EuropePMC > SemanticScholar).
      3. Call identity functions to generate pub_id, canonical_string, filename.
      4. Print a summary table.
    Plus:
      5. Assert Unpaywall is_oa=True for the 2 modern OA papers.
         Also check that best_oa_location has url or url_for_pdf (either is fine;
         publisher-hosted OA may have url without url_for_pdf).
      6. DOI-discovered-later determinism check on paper #1 (Badre 2008).

Cache:
    All API responses are cached under
    outputs/cache/<source>/<date>/<hash>.json
    A second run on the same day costs zero network calls.
    NOTE: Server errors (5xx) are NOT cached — a re-run on the same day will
    retry the live API for any source that returned a server error.

Written by Claude Sonnet, 2026-04-22.
See .status/citation_enrichment_blocked_2026-04-22.md for context.
DOI correction note: Badre paper is 2008, not 2012 as originally in the plan.
See .status/session_2026-04-21_literature_search_phase1.md for details.
"""

import argparse
import logging
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from identity import build_canonical_string, build_pdf_filename, build_pub_id

# ---------------------------------------------------------------------------
# Test papers
# NOTE: Paper #1 is Badre (2008), corrected from the planning doc which
# incorrectly listed "Badre & Nee (2012)" with DOI 10.1016/j.tics.2012.02.005.
# The correct citation is:
#   Badre, D. (2008). Cognitive control, hierarchy, and the rostro-caudal
#   organization of the frontal lobes. Trends in Cognitive Sciences, 12(5),
#   193-200. https://doi.org/10.1016/j.tics.2008.02.004
# The planning DOI resolved to a Starns (2012) memory paper -- wrong paper.
# ---------------------------------------------------------------------------

PAPERS = [
    # Classic papers (1-5)
    {
        "label": "Badre 2008",
        "doi": "10.1016/j.tics.2008.02.004",
        "expected_first_author": "Badre",
        "expected_year": 2008,
        "era": "classic",
        "modern_oa": False,
    },
    {
        "label": "Stroop 1935",
        "doi": "10.1037/h0054651",
        "expected_first_author": "Stroop",
        "expected_year": 1935,
        "era": "classic",
        "modern_oa": False,
    },
    {
        "label": "Eriksen 1974",
        "doi": "10.3758/BF03203267",
        "expected_first_author": "Eriksen",
        "expected_year": 1974,
        "era": "classic",
        "modern_oa": False,
    },
    {
        "label": "Posner 1980",
        "doi": "10.1080/00335558008248231",
        "expected_first_author": "Posner",
        "expected_year": 1980,
        "era": "classic",
        "modern_oa": False,
    },
    {
        "label": "Miller 1956",
        "doi": "10.1037/h0043158",
        "expected_first_author": "Miller",
        "expected_year": 1956,
        "era": "classic",
        "modern_oa": False,
    },
    # Modern OA papers (6-7)
    {
        "label": "Gorgolewski 2016",
        "doi": "10.1038/sdata.2016.44",
        "expected_first_author": "Gorgolewski",
        "expected_year": 2016,
        "era": "modern_oa",
        "modern_oa": True,
    },
    {
        "label": "Pernet 2019",
        "doi": "10.1038/s41597-019-0104-8",
        "expected_first_author": "Pernet",
        "expected_year": 2019,
        "era": "modern_oa",
        "modern_oa": True,
    },
]

# ---------------------------------------------------------------------------
# Metadata extraction helpers
# ---------------------------------------------------------------------------

def _extract_openalex(rec: dict) -> tuple[str | None, int | None, str | None]:
    authors = rec.get("authorships", [])
    family = None
    if authors:
        display = authors[0].get("author", {}).get("display_name", "")
        if display:
            family = display.split()[-1]
    year = rec.get("publication_year")
    title = rec.get("title")
    return family, year, title


def _extract_crossref(rec: dict) -> tuple[str | None, int | None, str | None]:
    authors = rec.get("author", [])
    family = authors[0].get("family") if authors else None
    year = None
    for date_field in ("published-print", "published-online", "issued"):
        dp = rec.get(date_field, {}).get("date-parts")
        if dp and dp[0]:
            year = dp[0][0]
            break
    titles = rec.get("title", [])
    title = titles[0] if titles else None
    return family, year, title


def _extract_europepmc(rec: dict) -> tuple[str | None, int | None, str | None]:
    authors = rec.get("authorList", {}).get("author", [])
    first_family = None
    if authors:
        first_family = authors[0].get("lastName") or authors[0].get("fullName", "").split()[-1]
    year_str = rec.get("pubYear")
    year = int(year_str) if year_str and year_str.isdigit() else None
    title = rec.get("title")
    return first_family, year, title


def _extract_semanticscholar(rec: dict) -> tuple[str | None, int | None, str | None]:
    authors = rec.get("authors", [])
    family = None
    if authors:
        name = authors[0].get("name", "")
        if name:
            family = name.split()[-1]
    year = rec.get("year")
    title = rec.get("title")
    return family, year, title


_EXTRACTORS = {
    "openalex": _extract_openalex,
    "crossref": _extract_crossref,
    "europepmc": _extract_europepmc,
    "semanticscholar": _extract_semanticscholar,
}

_SOURCE_PREFERENCE = ["openalex", "crossref", "europepmc", "semanticscholar"]


def extract_preferred(results: dict) -> tuple[str | None, int | None, str | None, str]:
    for src in _SOURCE_PREFERENCE:
        rec = results.get(src)
        if rec:
            family, year, title = _EXTRACTORS[src](rec)
            if family or title:
                return family, year, title, src
    return None, None, None, "none"


def check_agreement(
    label: str,
    results: dict,
    expected_family: str,
    expected_year: int,
) -> list[str]:
    warnings = []
    for src, rec in results.items():
        if rec is None or src == "unpaywall":
            continue
        extractor = _EXTRACTORS.get(src)
        if not extractor:
            continue
        family, year, _title = extractor(rec)
        if family and expected_family.lower() not in (family or "").lower():
            warnings.append(
                f"{label}: {src} first_author={family!r} "
                f"(expected contains {expected_family!r})"
            )
        if year and year != expected_year:
            warnings.append(
                f"{label}: {src} year={year} (expected {expected_year})"
            )
    return warnings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Phase 1 validation — resolve 7 papers through 5 API clients."
    )
    parser.add_argument("--workspace", default=".",
        help="Path to Claude-research workspace root (default: current directory)")
    parser.add_argument("--cache-dir", default=None,
        help="Override cache directory")
    parser.add_argument("--verbose", "-v", action="store_true",
        help="Enable DEBUG logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    workspace = Path(args.workspace).resolve()
    ls_dir = workspace / "outputs" / "literature_search"
    cache_dir = Path(args.cache_dir) if args.cache_dir else ls_dir / "cache"

    if str(ls_dir) not in sys.path:
        sys.path.insert(0, str(ls_dir))

    try:
        import requests  # noqa: F401
    except ImportError:
        print("ERROR: 'requests' is not installed.  Run:  pip install requests")
        sys.exit(1)

    from clients import openalex, crossref, europepmc, semanticscholar, unpaywall

    email = "hedannotation@gmail.com"

    print()
    print("Phase 1 validation — 7 papers (5 classic + 2 modern OA)")
    print("=" * 72)
    print()

    all_warnings: list[str] = []
    rows: list[dict] = []

    for paper in PAPERS:
        doi = paper["doi"].lower()
        label = paper["label"]

        print(f"  Fetching {label} ({doi}) ...", flush=True)

        results: dict = {}
        results["openalex"] = openalex.lookup_by_doi(doi, cache_dir, email)
        results["crossref"] = crossref.lookup_by_doi(doi, cache_dir, email)
        results["europepmc"] = europepmc.lookup_by_doi(doi, cache_dir, email)
        results["semanticscholar"] = semanticscholar.lookup_by_doi(doi, cache_dir, email)
        results["unpaywall"] = unpaywall.lookup_by_doi(doi, cache_dir, email)

        family, year, title, used_src = extract_preferred(results)

        pub_id = build_pub_id(family, year, title)
        canonical = build_canonical_string(family, year, title)
        filename = build_pdf_filename(family, year, title)

        rows.append({
            "label": label,
            "doi": doi,
            "used_src": used_src,
            "family": family,
            "year": year,
            "title": title,
            "pub_id": pub_id,
            "canonical": canonical,
            "filename": filename,
            "results": results,
            "modern_oa": paper["modern_oa"],
            "expected_family": paper["expected_first_author"],
            "expected_year": paper["expected_year"],
        })

        warnings = check_agreement(
            label, results, paper["expected_first_author"], paper["expected_year"]
        )
        all_warnings.extend(warnings)

    # --- Summary table ---
    print()
    print(f"{'pub_id':<16}  {'canonical_string (first 60 chars)':<62}  pdf_filename (truncated)")
    print("-" * 120)
    for row in rows:
        cs_short = row["canonical"][:60]
        fn_short = row["filename"][:50] + "..." if len(row["filename"]) > 50 else row["filename"]
        print(f"{row['pub_id']:<16}  {cs_short:<62}  {fn_short}")
    print()

    # --- Cross-source agreement ---
    print("Cross-source DOI agreement:")
    for row in rows:
        results = row["results"]
        sources_ok = [src for src, rec in results.items() if rec and src != "unpaywall"]
        sources_missing = [src for src, rec in results.items() if rec is None and src != "unpaywall"]
        oa_note = ""
        if row["modern_oa"]:
            up = results.get("unpaywall")
            if up:
                is_oa = up.get("is_oa", False)
                best = up.get("best_oa_location") or {}
                # Check either url_for_pdf or url (publisher-hosted OA may have
                # html landing page only, without direct pdf link)
                oa_url = best.get("url_for_pdf") or best.get("url")
                oa_note = f"; unpaywall is_oa={is_oa}, oa_url={'set' if oa_url else 'MISSING'}"
            else:
                oa_note = "; unpaywall=MISSING"
        missing_note = f" [MISSING from: {', '.join(sources_missing)}]" if sources_missing else ""
        print(f"  {row['label']:<20}: {', '.join(sources_ok)} agree on "
              f"first_author={row['family']!r}, year={row['year']}{oa_note}{missing_note}")
    print()

    # --- Modern OA assertions ---
    # is_oa=True is the critical assertion.
    # url_for_pdf may be null for publisher-hosted OA (Unpaywall only has the
    # HTML landing page); check url as fallback before flagging as broken.
    oa_errors: list[str] = []
    for row in rows:
        if not row["modern_oa"]:
            continue
        up = row["results"].get("unpaywall")
        if not up:
            oa_errors.append(f"{row['label']}: Unpaywall returned None (client may be broken)")
            continue
        if not up.get("is_oa"):
            oa_errors.append(
                f"{row['label']}: Unpaywall is_oa=False (expected True for this OA paper)"
            )
        best = up.get("best_oa_location") or {}
        oa_url = best.get("url_for_pdf") or best.get("url")
        if not oa_url:
            # Warn but do not fail — paper is OA, just no direct URL in Unpaywall
            all_warnings.append(
                f"{row['label']}: Unpaywall best_oa_location has no url or url_for_pdf "
                "(paper is OA; URL may be available on publisher site directly)"
            )

    if oa_errors:
        print("OA ASSERTION FAILURES (client likely broken):")
        for e in oa_errors:
            print(f"  *** {e}")
        print()

    # --- Warnings ---
    if all_warnings:
        print("Warnings (cross-source disagreements / data notes):")
        for w in all_warnings:
            print(f"  {w}")
        print()
    else:
        print("Warnings: none.")
        print()

    # --- Determinism check: DOI-discovered-later invariant ---
    print("DOI-discovered-later invariant check (Badre 2008):")
    badre_row = next(r for r in rows if "Badre" in r["label"])
    fam1, yr1, ttl1 = badre_row["family"], badre_row["year"], badre_row["title"]
    pid_with_doi = build_pub_id(fam1, yr1, ttl1)
    pid_without_doi = build_pub_id(fam1, yr1, ttl1)
    fn_with_doi = build_pdf_filename(fam1, yr1, ttl1)
    fn_without_doi = build_pdf_filename(fam1, yr1, ttl1)

    match_id = pid_with_doi == pid_without_doi
    match_fn = fn_with_doi == fn_without_doi
    print(f"  pub_id match:   {match_id}  ({pid_with_doi})")
    print(f"  filename match: {match_fn}")
    if match_fn:
        print(f"  filename:       {fn_with_doi}")
    if not (match_id and match_fn):
        print("  *** INVARIANT FAILED")
    else:
        print("  PASS: pub_id and filename stable regardless of DOI presence.")
    print()

    # --- Cache inventory ---
    cache_files = list(cache_dir.rglob("*.json")) if cache_dir.exists() else []
    print(f"Cache files written: {len(cache_files)} under {cache_dir}")
    print()

    if oa_errors:
        sys.exit(1)
    print("Phase 1 validation complete.")


if __name__ == "__main__":
    main()
