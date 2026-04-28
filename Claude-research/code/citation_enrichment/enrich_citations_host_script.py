#!/usr/bin/env python3
"""
enrich_citations_host_script.py

Self-contained citation enricher for the HED process catalog.
Run this on the Windows host machine when the Cowork sandbox has no
network egress to the citation APIs.

Usage:
    python outputs\\enrich_citations_host_script.py
    python outputs\\enrich_citations_host_script.py --workspace "H:\\Research\\TaskResearch\\Claude-research"
    python outputs\\enrich_citations_host_script.py --write-back
    python outputs\\enrich_citations_host_script.py --dry-run

Dependencies: requests (pip install requests). Standard library for everything else.

What it does:
    1. Loads process_details.json from the workspace root.
    2. For each of the 404 references in fundamental_references /
       recent_references, calls the citation resolver.
    3. Resolver tries, in order:
         a. File cache  (outputs/citation_cache/<hash>.json)
         b. CrossRef    api.crossref.org/works
         c. OpenAlex    api.openalex.org/works
         d. Europe PMC  www.ebi.ac.uk/europepmc  (biomed refs only)
         e. Semantic Scholar  api.semanticscholar.org/graph/v1
       Accepts top hit when: year matches exactly AND at least one
       author surname from the citation_string matches an API author.
    4. Verifies every DOI via HEAD to https://doi.org/<doi>.
    5. Writes outputs/process_details.enriched.json.
    6. If --write-back is set (or you confirm the prompt), copies the
       enriched file to process_details.json.
    7. Prints a resolution summary.

Idempotent: a second run costs $0 and < 5 s (all cache hits).

Manual entries: references with source='manual' are skipped entirely and
preserved unchanged.  Their stale cache files (if any) are deleted on the
first pass so the old false-positive result cannot contaminate future runs.

Written by Claude Sonnet, 2026-04-20.
See .status/citation_enrichment_blocked_2026-04-20.md for context.
See .status/false_positive_corrections_2026-04-20.md for the 4 manual fixes.
"""

import argparse
import datetime
import hashlib
import json
import re
import sys
import time
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    print("ERROR: 'requests' is not installed. Run:  pip install requests")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TODAY = datetime.date.today().isoformat()
USER_AGENT = "hed-task/1.0 (mailto:hedannotation@gmail.com)"
MAILTO = "hedannotation@gmail.com"
RATE_LIMIT_SEC = 0.2  # minimum gap between calls to the same host

BIOMED_TOKENS = frozenset([
    "neuroimage", "j neurosci", "neuron", "nature neuroscience",
    "nat neurosci", "pnas", "plos", "biol psychiatry", "cereb cortex",
    "hippocampus", "brain", "psychol rev", "jama", "lancet", "pmc",
])

_last_call: dict[str, float] = {}

# Fields we add; we never overwrite these originals: journal, year, citation_string
RESOLVER_FIELDS = (
    "authors", "title", "venue", "venue_type",
    "volume", "issue", "pages",
    "doi", "openalex_id", "pmid", "url",
    "source", "confidence", "verified_on",
)

# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------

@dataclass
class ResolvedReference:
    authors:      Optional[str] = None
    year:         Optional[int] = None
    title:        Optional[str] = None
    venue:        Optional[str] = None
    venue_type:   Optional[str] = None
    volume:       Optional[str] = None
    issue:        Optional[str] = None
    pages:        Optional[str] = None
    doi:          Optional[str] = None
    openalex_id:  Optional[str] = None
    pmid:         Optional[str] = None
    url:          Optional[str] = None
    source:       str = "unresolved"
    confidence:   str = "none"
    verified_on:  Optional[str] = None


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _normalize(s: str) -> str:
    return unicodedata.normalize("NFKD", s.lower())


def _strip_md(s: str) -> str:
    return re.sub(r"[*_`\[\]]", " ", s)


def _stable_key(citation_string: str, journal: Optional[str], year: Optional[int]) -> str:
    return json.dumps([citation_string, journal, year], sort_keys=True)


def _cache_path(cache_dir: Path, key: str) -> Path:
    h = hashlib.sha256(key.encode()).hexdigest()[:20]
    return cache_dir / f"{h}.json"


def _extract_surnames(citation_string: str) -> list[str]:
    """
    Pull author surnames from a citation_string like
    "Smith & Jones (2020) *Journal Name* 10:1–20".

    Takes text before the first '(', splits on , & 'and',
    picks the first word per chunk that isn't a bare initial.
    """
    before_year = re.split(r"\(", citation_string)[0]
    before_year = _strip_md(before_year)
    parts = re.split(r"[,&]|\band\b", before_year, flags=re.IGNORECASE)
    surnames: list[str] = []
    for part in parts:
        for word in part.strip().split():
            word = word.rstrip(".,;:")
            if re.match(r"^[A-Za-z]\.?$", word):
                continue   # skip bare initial
            if len(word) > 1:
                surnames.append(_normalize(word))
                break
    return surnames


def _author_match(citation_string: str, api_authors: list[dict]) -> bool:
    surnames = _extract_surnames(citation_string)
    if not surnames:
        return True   # can't extract — be permissive
    families = [
        _normalize(a.get("family") or a.get("name") or "")
        for a in api_authors
    ]
    families = [f for f in families if f]
    if not families:
        return True   # no author data — be permissive
    return any(s in f or f in s for s in surnames for f in families)


def _is_biomed(citation_string: str, journal: Optional[str]) -> bool:
    h = _normalize((citation_string or "") + " " + (journal or ""))
    return any(t in h for t in BIOMED_TOKENS)


# ---------------------------------------------------------------------------
# Type maps
# ---------------------------------------------------------------------------

_CR_TYPE = {
    "journal-article":     "journal",
    "book":                "book",
    "book-chapter":        "book_chapter",
    "monograph":           "book",
    "edited-book":         "book",
    "reference-entry":     "book_chapter",
    "proceedings-article": "proceedings",
    "report":              "report",
    "posted-content":      "preprint",
    "dissertation":        "other",
}

_OA_TYPE = {
    "journal-article":     "journal",
    "article":             "journal",
    "book":                "book",
    "book-chapter":        "book_chapter",
    "proceedings-article": "proceedings",
    "report":              "report",
    "preprint":            "preprint",
    "dissertation":        "other",
    "dataset":             "other",
}


# ---------------------------------------------------------------------------
# Author formatting
# ---------------------------------------------------------------------------

def _fmt_crossref_authors(authors: list[dict]) -> Optional[str]:
    parts = []
    for a in authors:
        family = (a.get("family") or "").strip()
        given  = (a.get("given")  or "").strip()
        if family and given:
            initials = " ".join(f"{w[0]}." for w in given.split() if w)
            parts.append(f"{family}, {initials}")
        elif family:
            parts.append(family)
    if not parts:
        return None
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + ", & " + parts[-1]


def _fmt_openalex_authors(authorships: list[dict]) -> Optional[str]:
    parts = []
    for a in authorships:
        name = ((a.get("author") or {}).get("display_name") or a.get("display_name") or "").strip()
        if name:
            parts.append(name)
    if not parts:
        return None
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + ", & " + parts[-1]


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------

def _get(url: str, params: dict, host: str, session: requests.Session) -> Optional[requests.Response]:
    now = time.monotonic()
    wait = RATE_LIMIT_SEC - (now - _last_call.get(host, 0.0))
    if wait > 0:
        time.sleep(wait)
    _last_call[host] = time.monotonic()

    for attempt, backoff in enumerate([1, 2, 4]):
        try:
            resp = session.get(url, params=params, timeout=12)
        except requests.RequestException:
            if attempt < 2:
                time.sleep(backoff)
                continue
            return None

        if resp.status_code in (429, 500, 502, 503, 504):
            if attempt < 2:
                time.sleep(backoff)
                continue
            return None

        if resp.status_code >= 400:
            return None   # 4xx other than 429: no retry

        return resp

    return None


def _verify_doi(doi: str, session: requests.Session) -> bool:
    try:
        r = session.head(f"https://doi.org/{doi}", timeout=8, allow_redirects=True)
        return r.status_code < 400
    except requests.RequestException:
        return False


# ---------------------------------------------------------------------------
# Per-source lookups
# ---------------------------------------------------------------------------

def _try_crossref(cs: str, year: Optional[int], session: requests.Session) -> Optional[ResolvedReference]:
    params: dict = {"query.bibliographic": cs, "rows": "3", "mailto": MAILTO}
    if year:
        params["filter"] = f"from-pub-date:{year},until-pub-date:{year}"

    resp = _get("https://api.crossref.org/works", params, "api.crossref.org", session)
    if not resp:
        return None

    try:
        items = resp.json().get("message", {}).get("items", [])
    except Exception:
        return None

    for item in items[:3]:
        parts = item.get("published", {}).get("date-parts", [[None]])
        item_year = parts[0][0] if parts and parts[0] else None
        if year and item_year != year:
            continue

        cr_authors = item.get("author", [])
        if cr_authors and not _author_match(cs, cr_authors):
            continue

        titles = item.get("title", [])
        container = item.get("container-title", [])

        doi_val = item.get("DOI") or None
        return ResolvedReference(
            authors=_fmt_crossref_authors(cr_authors),
            year=item_year,
            title=titles[0] if titles else None,
            venue=container[0] if container else None,
            venue_type=_CR_TYPE.get(item.get("type", ""), "other"),
            volume=item.get("volume") or None,
            issue=item.get("issue") or None,
            pages=item.get("page") or None,
            doi=doi_val,
            url=f"https://doi.org/{doi_val}" if doi_val else None,
            source="crossref",
            confidence="high",
            verified_on=TODAY,
        )
    return None


def _try_openalex(cs: str, year: Optional[int], session: requests.Session) -> Optional[ResolvedReference]:
    stripped = re.sub(r"\s+", " ", _strip_md(cs)).strip()
    params: dict = {"search": stripped, "per-page": "3", "mailto": MAILTO}
    if year:
        params["filter"] = f"publication_year:{year}"

    resp = _get("https://api.openalex.org/works", params, "api.openalex.org", session)
    if not resp:
        return None

    try:
        results = resp.json().get("results", [])
    except Exception:
        return None

    for item in results[:3]:
        item_year = item.get("publication_year")
        if year and item_year != year:
            continue

        authorships = item.get("authorships", [])
        api_authors = [
            {"family": ((a.get("author") or {}).get("display_name") or "").rsplit(" ", 1)[-1]}
            for a in authorships
        ]
        if api_authors and not _author_match(cs, api_authors):
            continue

        raw_doi = item.get("doi") or ""
        doi = raw_doi.replace("https://doi.org/", "").strip() or None
        loc = item.get("primary_location") or {}
        src_info = loc.get("source") or {}

        # Prefer open-access full-text URL; fall back to landing page or DOI resolver.
        oa_url = (item.get("open_access") or {}).get("oa_url") or None
        landing = item.get("landing_page_url") or None
        url = oa_url or (f"https://doi.org/{doi}" if doi else landing)

        return ResolvedReference(
            authors=_fmt_openalex_authors(authorships),
            year=item_year,
            title=item.get("display_name") or item.get("title"),
            venue=src_info.get("display_name") or None,
            venue_type=_OA_TYPE.get(item.get("type", ""), "other"),
            doi=doi,
            openalex_id=item.get("id") or None,
            url=url,
            source="openalex",
            confidence="high" if doi else "medium",
            verified_on=TODAY,
        )
    return None


def _try_europepmc(cs: str, year: Optional[int], journal: Optional[str],
                   session: requests.Session) -> Optional[ResolvedReference]:
    if not _is_biomed(cs, journal):
        return None
    query = cs if not year else f"{cs} AND PUB_YEAR:{year}"
    resp = _get(
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
        {"query": query, "format": "json", "resultType": "core", "pageSize": "3"},
        "www.ebi.ac.uk",
        session,
    )
    if not resp:
        return None

    try:
        results = resp.json().get("resultList", {}).get("result", [])
    except Exception:
        return None

    for item in results[:3]:
        raw_year = item.get("pubYear")
        item_year = int(raw_year) if raw_year and str(raw_year).isdigit() else None
        if year and item_year != year:
            continue

        al = item.get("authorList", {}).get("author", [])
        api_authors = [{"family": a.get("lastName", "")} for a in al]
        if api_authors and not _author_match(cs, api_authors):
            continue

        authors_str = None
        if al:
            parts = [f"{a.get('lastName', '')}, {a.get('initials', '')}".strip(", ") for a in al]
            authors_str = "; ".join(p for p in parts if p) or None

        pmid_val = str(item.get("pmid")) if item.get("pmid") else None
        doi_val  = item.get("doi") or None
        url = (
            f"https://europepmc.org/article/MED/{pmid_val}" if pmid_val
            else (f"https://doi.org/{doi_val}" if doi_val else None)
        )
        return ResolvedReference(
            authors=authors_str,
            year=item_year,
            title=item.get("title") or None,
            venue=item.get("journalTitle") or None,
            venue_type="journal" if item.get("journalTitle") else "other",
            doi=doi_val,
            pmid=pmid_val,
            url=url,
            source="europepmc",
            confidence="medium",
            verified_on=TODAY,
        )
    return None


def _try_semanticscholar(cs: str, year: Optional[int],
                         session: requests.Session) -> Optional[ResolvedReference]:
    stripped = re.sub(r"\s+", " ", _strip_md(cs)).strip()
    params: dict = {"query": stripped, "limit": "3",
                    "fields": "externalIds,title,authors,venue,year"}
    if year:
        params["year"] = str(year)

    resp = _get(
        "https://api.semanticscholar.org/graph/v1/paper/search",
        params,
        "api.semanticscholar.org",
        session,
    )
    if not resp:
        return None

    try:
        results = resp.json().get("data", [])
    except Exception:
        return None

    for item in results[:3]:
        item_year = item.get("year")
        if year and item_year != year:
            continue

        ss_authors = item.get("authors", [])
        api_authors = [
            {"family": a.get("name", "").rsplit(" ", 1)[-1]}
            for a in ss_authors if a.get("name")
        ]
        if api_authors and not _author_match(cs, api_authors):
            continue

        ext = item.get("externalIds") or {}
        doi = ext.get("DOI") or None
        pmid = str(ext.get("PubMed")) if ext.get("PubMed") else None
        authors_str = ", ".join(a.get("name", "") for a in ss_authors) or None
        url = (
            item.get("url")
            or (f"https://doi.org/{doi}" if doi else None)
            or (f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None)
        )

        return ResolvedReference(
            authors=authors_str,
            year=item_year,
            title=item.get("title") or None,
            venue=item.get("venue") or None,
            venue_type="journal",  # S2 type field is unreliable
            doi=doi,
            pmid=pmid,
            url=url,
            source="semanticscholar",
            confidence="low",
            verified_on=TODAY,
        )
    return None


# ---------------------------------------------------------------------------
# Core resolver
# ---------------------------------------------------------------------------

def resolve_reference(
    citation_string: str,
    journal: Optional[str],
    year: Optional[int],
    cache_dir: Path,
    session: requests.Session,
) -> ResolvedReference:
    """
    Resolve one citation. Caches result in cache_dir/<hash>.json.
    Lookup order: cache → CrossRef → OpenAlex → Europe PMC → S2 → unresolved.
    Pre-1900 refs: shortcut to historical/low.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = _stable_key(citation_string, journal, year)
    cpath = _cache_path(cache_dir, key)

    if cpath.exists():
        try:
            return ResolvedReference(**json.loads(cpath.read_text(encoding="utf-8")))
        except Exception:
            pass

    # Historical shortcut
    if year and year < 1900:
        result = ResolvedReference(year=year, source="historical",
                                   confidence="low", verified_on=TODAY)
        cpath.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2),
                         encoding="utf-8")
        return result

    result: Optional[ResolvedReference] = None
    result = _try_crossref(citation_string, year, session)
    if result is None:
        result = _try_openalex(citation_string, year, session)
    if result is None:
        result = _try_europepmc(citation_string, year, journal, session)
    if result is None:
        result = _try_semanticscholar(citation_string, year, session)

    # DOI verification
    if result is not None and result.doi:
        if not _verify_doi(result.doi, session):
            result.doi = None

    if result is None:
        result = ResolvedReference(year=year, source="unresolved",
                                   confidence="none", verified_on=TODAY)

    # URL fallback: if no source-specific URL was set, synthesize from doi or pmid.
    if result.url is None:
        if result.doi:
            result.url = f"https://doi.org/{result.doi}"
        elif result.pmid:
            result.url = f"https://pubmed.ncbi.nlm.nih.gov/{result.pmid}/"

    cpath.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2),
                     encoding="utf-8")
    return result


# ---------------------------------------------------------------------------
# Reference enrichment
# ---------------------------------------------------------------------------

def enrich_ref(ref: dict, cache_dir: Path, session: requests.Session) -> dict:
    """Merge resolver output into ref, preserving original fields.

    Entries with source='manual' are returned unchanged — they represent
    human-verified corrections that must not be overwritten by API lookups.
    Any stale cache file for that citation key is also deleted, so a future
    run won't re-import the old false-positive result into a different entry
    that shares the same citation_string/journal/year triple.
    """
    if ref.get("source") == "manual":
        # Delete stale cache entry if present so it can't contaminate future runs.
        key = _stable_key(
            ref.get("citation_string", ""),
            ref.get("journal") or None,
            ref.get("year") or None,
        )
        cpath = _cache_path(cache_dir, key)
        if cpath.exists():
            try:
                cpath.unlink()
            except OSError:
                pass  # not critical
        return ref

    resolved = resolve_reference(
        ref.get("citation_string", ""),
        ref.get("journal") or None,
        ref.get("year") or None,
        cache_dir,
        session,
    )
    r = asdict(resolved)
    enriched = dict(ref)
    for field in RESOLVER_FIELDS:
        val = r.get(field)
        if field in ("source", "confidence", "verified_on"):
            enriched[field] = val
        elif val is not None:
            enriched[field] = val
        elif field not in enriched:
            enriched[field] = None
    return enriched


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Enrich process_details.json citation references using CrossRef / "
            "OpenAlex / Europe PMC / Semantic Scholar.\n\n"
            "Run from the workspace root (H:\\Research\\TaskResearch\\Claude-research) "
            "or pass --workspace explicitly."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=None,
        help="Path to Claude-research workspace root (default: parent of outputs/)",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="Cache directory for per-lookup JSON files (default: outputs/citation_cache/)",
    )
    parser.add_argument(
        "--write-back",
        action="store_true",
        help="Automatically write enriched JSON back to process_details.json (skip prompt)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load, report counts, then exit without resolving",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).parent.resolve()
    workspace  = args.workspace  or script_dir.parent
    cache_dir  = args.cache_dir  or (script_dir / "citation_cache")
    input_path = workspace / "process_details.json"
    output_path = script_dir / "process_details.enriched.json"

    print("=" * 64)
    print("HED Citation Enricher — process_details.json")
    print("=" * 64)
    print(f"Workspace  : {workspace}")
    print(f"Input      : {input_path}")
    print(f"Cache dir  : {cache_dir}")
    print(f"Output     : {output_path}")
    print()

    if not input_path.exists():
        print(f"ERROR: {input_path} not found.")
        print("Pass --workspace to point at the Claude-research directory.")
        sys.exit(1)

    # Load
    raw = input_path.read_text(encoding="utf-8")
    data = json.loads(raw)
    processes = data.get("processes", [])
    total_refs = sum(
        len(p.get("fundamental_references", [])) + len(p.get("recent_references", []))
        for p in processes
    )
    print(f"Loaded {len(processes)} processes, {total_refs} references.")
    print()

    if args.dry_run:
        print("Dry run — exiting without resolving.")
        return

    # Session
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    # Counters
    conf_counts: dict[str, int] = {"high": 0, "medium": 0, "low": 0, "none": 0}
    src_counts:  dict[str, int] = {}
    done = 0
    skipped_manual = 0
    unresolved_list: list[tuple[str, str]] = []

    print("Resolving references (this takes ~15–30 min for 404 refs on first run)...")
    print("Entries with source='manual' are preserved unchanged.")
    print()

    try:
        for process in processes:
            pid = process["process_id"]
            for ref_key in ("fundamental_references", "recent_references"):
                refs = process.get(ref_key, [])
                for i, ref in enumerate(refs):
                    enriched = enrich_ref(ref, cache_dir, session)
                    refs[i] = enriched
                    done += 1

                    src = enriched.get("source", "unresolved")
                    src_counts[src] = src_counts.get(src, 0) + 1

                    if src == "manual":
                        skipped_manual += 1
                        # Don't fold manual into conf_counts — they're already correct.
                        if done % 20 == 0 or done == total_refs:
                            cs_short = ref.get("citation_string", "")[:55]
                            print(f"  [{done:3d}/{total_refs}] {cs_short} [MANUAL — preserved]")
                        continue

                    conf = enriched.get("confidence", "none")
                    conf_counts[conf] = conf_counts.get(conf, 0) + 1

                    if src == "unresolved":
                        unresolved_list.append((pid, ref.get("citation_string", "")))

                    if done % 20 == 0 or done == total_refs:
                        cs_short = ref.get("citation_string", "")[:55]
                        flag = " [UNRESOLVED]" if src == "unresolved" else f" [{conf}]"
                        print(f"  [{done:3d}/{total_refs}] {cs_short}{flag}")
    except KeyboardInterrupt:
        print("\nInterrupted — partial results will be written.")
    finally:
        session.close()

    # Write enriched output
    enriched_text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    output_path.write_text(enriched_text, encoding="utf-8")
    print()
    print(f"Wrote: {output_path}")

    # Summary
    # manual entries are excluded from auto-resolution counts
    auto_total = total_refs - skipped_manual
    resolved = conf_counts["high"] + conf_counts["medium"] + conf_counts["low"]
    pct = lambda n, d=auto_total: f"{100 * n // d}%" if d else "N/A"

    print()
    print("=" * 50)
    print("Resolution summary")
    print("=" * 50)
    print(f"Total refs:          {total_refs}")
    if skipped_manual:
        print(f"  manual (skipped):  {skipped_manual}  (human-verified, not re-queried)")
        print(f"  auto-resolved:     {auto_total}")
    print(f"Resolved (auto):     {resolved} ({pct(resolved)})")
    print(f"  high confidence:   {conf_counts['high']}")
    print(f"  medium:            {conf_counts['medium']}")
    print(f"  low:               {conf_counts['low']}")
    print(f"Unresolved:          {conf_counts['none']} ({pct(conf_counts['none'])})")
    print()
    print("By source:")
    for src, count in sorted(src_counts.items(), key=lambda x: -x[1]):
        print(f"  {src:<24}: {count}")

    if unresolved_list:
        print()
        print(f"Unresolved ({len(unresolved_list)}):")
        for pid, cs in unresolved_list:
            print(f"  [{pid}]  {cs}")

    # Write-back decision
    print()
    do_write_back = args.write_back
    if not do_write_back:
        try:
            ans = input(f"Write enriched data back to {input_path}? [y/N] ").strip().lower()
            do_write_back = ans in ("y", "yes")
        except EOFError:
            pass

    if do_write_back:
        input_path.write_text(enriched_text, encoding="utf-8")
        print(f"Updated: {input_path}")
        print()
        print("Next steps:")
        print("  1. Return to Cowork session and run Phase 4 verification.")
        print("  2. That session will re-read the updated JSON, spot-check 10 refs,")
        print("     and regenerate derived files via outputs/regenerate_derived_files.py.")
    else:
        print(f"Skipped write-back. Enriched file is at:")
        print(f"  {output_path}")
        print()
        print("When ready, copy it to process_details.json, then run Phase 4.")

    print()
    print("Done.")


if __name__ == "__main__":
    main()
