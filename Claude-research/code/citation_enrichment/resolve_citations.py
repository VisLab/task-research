#!/usr/bin/env python3
"""
resolve_citations.py

Reusable citation resolver for the HED task/process catalog.

Exposes one public function:

    resolve_reference(citation_string, journal, year, cache_dir, session)
        -> ResolvedReference

Lookup order:
    1. File cache (cache_dir/<hash>.json)
    2. CrossRef  /works?query.bibliographic=...
    3. OpenAlex  /works?search=...
    4. Europe PMC /search  (biomed refs only)
    5. Semantic Scholar /paper/search  (last resort)
    6. source="unresolved", confidence="none"

Pre-1900 refs are short-circuited to source="historical", confidence="low".

Dependencies: requests, standard library only. No pyalex, no crossrefapi.

Part of citation-enrichment workstream, Phase B (process references).
See .status/task_citation_enrich_processes_instructions.md for full spec.
"""

import hashlib
import json
import re
import time
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TODAY = "2026-04-20"
USER_AGENT = "hed-task/1.0 (mailto:hedannotation@gmail.com)"
MAILTO = "hedannotation@gmail.com"
RATE_LIMIT_SEC = 0.2   # minimum gap between calls to the same host

# Tokens that indicate a reference is biomedical enough to try Europe PMC.
# Matched case-insensitively against the full citation_string + journal.
BIOMED_TOKENS = frozenset([
    "neuroimage", "j neurosci", "neuron", "nature neuroscience",
    "nat neurosci", "pnas", "plos", "biol psychiatry", "cereb cortex",
    "hippocampus", "brain", "psychol rev", "jama", "lancet", "pmc",
])

# Per-host monotonic timestamp of last outgoing request (for rate limiting)
_last_call: dict[str, float] = {}


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------

@dataclass
class ResolvedReference:
    """Structured output of a citation resolution attempt."""
    authors: Optional[str] = None
    year: Optional[int] = None
    title: Optional[str] = None
    venue: Optional[str] = None
    # one of: journal | book | book_chapter | proceedings | report | preprint | other
    venue_type: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    openalex_id: Optional[str] = None
    pmid: Optional[str] = None
    # one of: crossref | openalex | europepmc | semanticscholar | unresolved | historical
    source: str = "unresolved"
    # one of: high | medium | low | none
    confidence: str = "none"
    verified_on: Optional[str] = None


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _normalize(s: str) -> str:
    """Lowercase + NFKD unicode normalization."""
    return unicodedata.normalize("NFKD", s.lower())


def _strip_md(s: str) -> str:
    """Remove basic markdown formatting characters."""
    return re.sub(r"[*_`\[\]]", " ", s)


def _stable_key(citation_string: str, journal: Optional[str], year: Optional[int]) -> str:
    return json.dumps([citation_string, journal, year], sort_keys=True)


def _cache_path(cache_dir: Path, key: str) -> Path:
    h = hashlib.sha256(key.encode()).hexdigest()[:20]
    return cache_dir / f"{h}.json"


def _extract_surnames(citation_string: str) -> list[str]:
    """
    Extract author surnames from a citation string like
    "Smith & Jones (2020) *Journal* 10:1-20".

    Strategy: take everything before the first '(' (the year marker),
    split on comma / & / 'and', take the first multi-character token
    from each chunk that isn't an initial (single letter + optional '.').
    """
    before_year = re.split(r"\(", citation_string)[0]
    before_year = _strip_md(before_year)

    parts = re.split(r"[,&]|\band\b", before_year, flags=re.IGNORECASE)
    surnames: list[str] = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        for word in part.split():
            word = word.rstrip(".,;:")
            if re.match(r"^[A-Za-z]\.?$", word):
                continue  # skip initials
            if len(word) > 1:
                surnames.append(_normalize(word))
                break
    return surnames


def _author_match(citation_string: str, api_authors: list[dict]) -> bool:
    """
    Return True if at least one surname extracted from citation_string
    matches at least one family name in api_authors (case-insensitive,
    unicode-normalized, substring-tolerant for hyphenated names).

    api_authors is a list of dicts; we look at keys 'family' or 'name'.
    """
    surnames = _extract_surnames(citation_string)
    if not surnames:
        return True  # No surnames extracted — be permissive
    api_families = [
        _normalize(a.get("family") or a.get("name") or "")
        for a in api_authors
    ]
    api_families = [f for f in api_families if f]
    if not api_families:
        return True  # No author data in API — be permissive
    for s in surnames:
        for f in api_families:
            if s in f or f in s:
                return True
    return False


def _is_biomed(citation_string: str, journal: Optional[str]) -> bool:
    haystack = _normalize((citation_string or "") + " " + (journal or ""))
    return any(token in haystack for token in BIOMED_TOKENS)


# ---------------------------------------------------------------------------
# Crossref type → venue_type mapping
# ---------------------------------------------------------------------------

_CROSSREF_TYPE_MAP = {
    "journal-article":    "journal",
    "book":               "book",
    "book-chapter":       "book_chapter",
    "monograph":          "book",
    "edited-book":        "book",
    "reference-entry":    "book_chapter",
    "proceedings-article":"proceedings",
    "report":             "report",
    "posted-content":     "preprint",
    "dissertation":       "other",
}

_OPENALEX_TYPE_MAP = {
    "journal-article":    "journal",
    "article":            "journal",
    "book":               "book",
    "book-chapter":       "book_chapter",
    "proceedings-article":"proceedings",
    "report":             "report",
    "preprint":           "preprint",
    "dissertation":       "other",
    "dataset":            "other",
}


def _crossref_venue_type(cr_type: str) -> str:
    return _CROSSREF_TYPE_MAP.get(cr_type, "other")


def _openalex_venue_type(oa_type: str) -> str:
    return _OPENALEX_TYPE_MAP.get(oa_type, "other")


# ---------------------------------------------------------------------------
# Author formatting helpers
# ---------------------------------------------------------------------------

def _fmt_authors_crossref(cr_authors: list[dict]) -> str:
    parts = []
    for a in cr_authors:
        family = (a.get("family") or "").strip()
        given  = (a.get("given")  or "").strip()
        if family and given:
            initials = " ".join(f"{w[0]}." for w in given.split() if w)
            parts.append(f"{family}, {initials}")
        elif family:
            parts.append(family)
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + ", & " + parts[-1]


def _fmt_authors_openalex(authorships: list[dict]) -> str:
    parts = []
    for a in authorships:
        name = (a.get("author") or {}).get("display_name") or a.get("display_name") or ""
        name = name.strip()
        if name:
            parts.append(name)
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + ", & " + parts[-1]


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------

def _get(
    url: str,
    params: dict,
    host: str,
    session: requests.Session,
) -> Optional[requests.Response]:
    """
    Rate-limited GET with retry on 429 / 5xx.
    Returns None on any unrecoverable failure.
    """
    # Rate limiting
    now = time.monotonic()
    elapsed = now - _last_call.get(host, 0.0)
    if elapsed < RATE_LIMIT_SEC:
        time.sleep(RATE_LIMIT_SEC - elapsed)
    _last_call[host] = time.monotonic()

    backoffs = [1, 2, 4]
    for attempt, backoff in enumerate(backoffs):
        try:
            resp = session.get(url, params=params, timeout=12)
        except requests.RequestException:
            if attempt < len(backoffs) - 1:
                time.sleep(backoff)
            else:
                return None
            continue

        if resp.status_code in (429, 500, 502, 503, 504):
            if attempt < len(backoffs) - 1:
                time.sleep(backoff)
            else:
                return None
            continue

        if resp.status_code >= 400:
            return None  # 4xx other than 429: no retry

        return resp

    return None


# ---------------------------------------------------------------------------
# DOI verification
# ---------------------------------------------------------------------------

def _verify_doi(doi: str, session: requests.Session) -> bool:
    """HEAD request to https://doi.org/<doi>; accept 2xx or 3xx."""
    try:
        resp = session.head(
            f"https://doi.org/{doi}",
            timeout=8,
            allow_redirects=True,
        )
        return resp.status_code < 400
    except requests.RequestException:
        return False


# ---------------------------------------------------------------------------
# Per-source lookup functions
# ---------------------------------------------------------------------------

def _try_crossref(
    citation_string: str,
    year: Optional[int],
    session: requests.Session,
) -> Optional[ResolvedReference]:
    params: dict = {
        "query.bibliographic": citation_string,
        "rows": "3",
        "mailto": MAILTO,
    }
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
        # Year check
        pub_parts = item.get("published", {}).get("date-parts", [[None]])
        item_year = pub_parts[0][0] if pub_parts and pub_parts[0] else None
        if year and item_year != year:
            continue

        cr_authors = item.get("author", [])
        if cr_authors and not _author_match(citation_string, cr_authors):
            continue

        title_list = item.get("title", [])
        title = title_list[0] if title_list else None
        container = item.get("container-title", [])
        venue = container[0] if container else None
        venue_type = _crossref_venue_type(item.get("type", ""))
        doi = item.get("DOI") or None

        return ResolvedReference(
            authors=_fmt_authors_crossref(cr_authors) or None,
            year=item_year,
            title=title,
            venue=venue,
            venue_type=venue_type,
            volume=item.get("volume") or None,
            issue=item.get("issue") or None,
            pages=item.get("page") or None,
            doi=doi,
            source="crossref",
            confidence="high",
            verified_on=TODAY,
        )
    return None


def _try_openalex(
    citation_string: str,
    year: Optional[int],
    session: requests.Session,
) -> Optional[ResolvedReference]:
    stripped = re.sub(r"\s+", " ", _strip_md(citation_string)).strip()
    params: dict = {
        "search": stripped,
        "per-page": "3",
        "mailto": MAILTO,
    }
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
        # Build a family-name list for matching
        api_authors = [
            {"family": (a.get("author") or {}).get("display_name", "").rsplit(" ", 1)[-1]}
            for a in authorships
        ]
        if api_authors and not _author_match(citation_string, api_authors):
            continue

        title = item.get("display_name") or item.get("title")
        loc = item.get("primary_location") or {}
        src = loc.get("source") or {}
        venue = src.get("display_name") or None
        venue_type = _openalex_venue_type(item.get("type", ""))

        raw_doi = item.get("doi") or ""
        doi = raw_doi.replace("https://doi.org/", "").strip() or None
        openalex_id = item.get("id") or None

        confidence = "high" if doi else "medium"

        return ResolvedReference(
            authors=_fmt_authors_openalex(authorships) or None,
            year=item_year,
            title=title,
            venue=venue,
            venue_type=venue_type,
            doi=doi,
            openalex_id=openalex_id,
            source="openalex",
            confidence=confidence,
            verified_on=TODAY,
        )
    return None


def _try_europepmc(
    citation_string: str,
    year: Optional[int],
    journal: Optional[str],
    session: requests.Session,
) -> Optional[ResolvedReference]:
    if not _is_biomed(citation_string, journal):
        return None

    query = citation_string
    if year:
        query = f"{query} AND PUB_YEAR:{year}"

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

        author_list = item.get("authorList", {}).get("author", [])
        api_authors = [{"family": a.get("lastName", "")} for a in author_list]
        if api_authors and not _author_match(citation_string, api_authors):
            continue

        title = item.get("title") or None
        venue = item.get("journalTitle") or None
        venue_type = "journal" if venue else "other"
        doi = item.get("doi") or None
        pmid = str(item.get("pmid")) if item.get("pmid") else None

        authors_str = None
        if author_list:
            parts = [
                f"{a.get('lastName', '')}, {a.get('initials', '')}".strip(", ")
                for a in author_list
            ]
            authors_str = "; ".join(p for p in parts if p) or None

        return ResolvedReference(
            authors=authors_str,
            year=item_year,
            title=title,
            venue=venue,
            venue_type=venue_type,
            doi=doi,
            pmid=pmid,
            source="europepmc",
            confidence="medium",
            verified_on=TODAY,
        )
    return None


def _try_semanticscholar(
    citation_string: str,
    year: Optional[int],
    session: requests.Session,
) -> Optional[ResolvedReference]:
    stripped = re.sub(r"\s+", " ", _strip_md(citation_string)).strip()
    params: dict = {
        "query": stripped,
        "limit": "3",
        "fields": "externalIds,title,authors,venue,year",
    }
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
        if api_authors and not _author_match(citation_string, api_authors):
            continue

        title = item.get("title") or None
        venue = item.get("venue") or None
        ext = item.get("externalIds") or {}
        doi = ext.get("DOI") or None
        pmid = str(ext.get("PubMed")) if ext.get("PubMed") else None
        authors_str = ", ".join(a.get("name", "") for a in ss_authors) or None

        return ResolvedReference(
            authors=authors_str,
            year=item_year,
            title=title,
            venue=venue,
            venue_type="journal",  # Semantic Scholar does not reliably report type
            doi=doi,
            pmid=pmid,
            source="semanticscholar",
            confidence="low",
            verified_on=TODAY,
        )
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def resolve_reference(
    citation_string: str,
    journal: Optional[str],
    year: Optional[int],
    cache_dir: Path,
    session: Optional[requests.Session] = None,
) -> ResolvedReference:
    """
    Resolve a citation string to a structured ResolvedReference.

    Lookup order: cache → CrossRef → OpenAlex → Europe PMC → Semantic Scholar.
    On failure at all sources: source="unresolved", confidence="none".
    On year < 1900: source="historical", confidence="low" (no API call).

    All successful resolutions are cached in cache_dir as <hash>.json.
    A second call with the same inputs is a no-op (reads from cache).

    If no session is passed, a temporary one is created with the correct
    User-Agent header and closed before returning.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = _stable_key(citation_string, journal, year)
    cpath = _cache_path(cache_dir, key)

    # Cache hit
    if cpath.exists():
        try:
            return ResolvedReference(**json.loads(cpath.read_text(encoding="utf-8")))
        except Exception:
            pass  # Corrupt cache entry — re-resolve

    # Historical shortcut (pre-1900)
    if year and year < 1900:
        result = ResolvedReference(
            year=year,
            source="historical",
            confidence="low",
            verified_on=TODAY,
        )
        cpath.write_text(
            json.dumps(asdict(result), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return result

    own_session = session is None
    if own_session:
        session = requests.Session()
        session.headers["User-Agent"] = USER_AGENT

    try:
        result: Optional[ResolvedReference] = None

        result = _try_crossref(citation_string, year, session)

        if result is None:
            result = _try_openalex(citation_string, year, session)

        if result is None:
            result = _try_europepmc(citation_string, year, journal, session)

        if result is None:
            result = _try_semanticscholar(citation_string, year, session)

        # DOI verification — reject DOIs that don't resolve
        if result is not None and result.doi:
            if not _verify_doi(result.doi, session):
                result.doi = None

        if result is None:
            result = ResolvedReference(
                year=year,
                source="unresolved",
                confidence="none",
                verified_on=TODAY,
            )

        cpath.write_text(
            json.dumps(asdict(result), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return result

    finally:
        if own_session:
            session.close()
