#!/usr/bin/env python3
"""
enrich_task_citations_host_script.py  -  Phase C: task citation enricher.

Self-contained: inlines the APA parser and the resolver.  Shared cache
with Phase B (citation_cache/) so duplicate references cost nothing extra.

Usage (run from workspace root on Windows host):
    python outputs\enrich_task_citations_host_script.py --dry-run
    python outputs\enrich_task_citations_host_script.py --write-back

--dry-run   Parse-only stats; no network, no file writes.
--write-back  Write enriched data back to task_details.json (creates backup).

Dependency:  pip install requests
"""

import argparse, datetime, hashlib, json, re, sys, time, unicodedata
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    print("ERROR: requests not installed.  Run: pip install requests")
    sys.exit(1)

TODAY          = datetime.date.today().isoformat()
USER_AGENT     = "hed-task/1.0 (mailto:hedannotation@gmail.com)"
MAILTO         = "hedannotation@gmail.com"
RATE_LIMIT_SEC = 0.2
_last_call: dict = {}

BIOMED_TOKENS = frozenset([
    "neuroimage","j neurosci","neuron","nature neuroscience","nat neurosci",
    "pnas","plos","biol psychiatry","cereb cortex","hippocampus","brain",
    "psychol rev","jama","lancet","cognition","science","nature","cell",
])

# ===========================================================================
# Inline APA parser  (keep in sync with outputs/parse_citation_string.py)
# ===========================================================================

@dataclass
class ParsedCitation:
    authors:       str   = ""
    year:          Optional[int] = None
    title:         str   = ""
    venue:         Optional[str] = None
    venue_type:    str   = "other"
    volume:        Optional[str] = None
    issue:         Optional[str] = None
    pages:         Optional[str] = None
    doi:           Optional[str] = None
    parse_quality: str   = "malformed"

_P_YEAR_RE      = re.compile(r'\((\d{4}[a-z]?)\)')
_P_YEAR_SLASH   = re.compile(r'\((\d{4})/\d{4}[a-z]?\)')
_P_DOI_RE       = re.compile(r'\b(10\.\d{4,9}/[^\s,\])\'"]+)')
_P_COMPOUND     = re.compile(r'\s*\[(?:Updated|Note|See also|cf\.?)[^\]]*\]', re.IGNORECASE)
_P_VOL_ISS_PP   = re.compile(r'(\d+)\((\d+)\)[.,]?\s*([\d\w]+\s*[\-\u2013\u2014]\s*[\d\w]+)')
_P_VOL_PP       = re.compile(r'(\d+)[.,]\s*([\d\w]+\s*[\-\u2013\u2014]\s*[\d\w]+)')
_P_VOL_ISS      = re.compile(r'^(\d+)\((\d+)\)')
_P_VOL          = re.compile(r'^(\d+)\b')
_P_PP_PAGES     = re.compile(r'\(pp\.\s*([\d\w]+\s*[\-\u2013\u2014]\s*[\d\w]+)\)')
_P_REPORT       = re.compile(
    r'\b(manual|report|technical|handbook|guide|bulletin|monograph|'
    r'unpublished|dissertation|thesis|working paper)\b', re.IGNORECASE)
_P_PUBLISHER    = re.compile(
    r'\b(press|publishers?|publishing|university|association|institute|'
    r'foundation|society|academic|elsevier|springer|wiley|oxford|cambridge|'
    r'guilford|erlbaum|routledge|taylor|mcgraw|pearson|sage|apa|aps)\b', re.IGNORECASE)
_P_JOURNAL_SEP  = re.compile(r'([.?!])[\u2018\u2019\u201c\u201d"\']?\s+(?=\*)')


def _p_clean_pages(raw):
    return re.sub(r'\s*([\-\u2013\u2014])\s*', r'\1', raw.strip())

def _p_extract_italic(text):
    m = re.search(r'\*(.+?)\*', text)
    return (m.group(1).strip(), text[m.end():]) if m else ("", text)

def parse_citation(citation_string):
    r = ParsedCitation()
    s = _P_COMPOUND.sub('', citation_string).strip()
    doi_m = _P_DOI_RE.search(citation_string)
    if doi_m:
        r.doi = doi_m.group(1).rstrip('.')
    year_m = _P_YEAR_RE.search(s) or _P_YEAR_SLASH.search(s)
    if not year_m:
        return r
    try:
        r.year = int(year_m.group(1)[:4])
    except ValueError:
        return r
    r.authors = s[:year_m.start()].strip()
    rest = re.sub(r'^[\.\s]+', '', s[year_m.end():].strip())
    if not rest:
        return r
    if rest.startswith('*'):
        title, after = _p_extract_italic(rest)
        r.title = title
        after = after.strip().lstrip('.').strip()
        r.venue_type = "report" if _P_REPORT.search(citation_string) else "book"
        if after:
            r.venue = after.rstrip('.').strip() or None
    else:
        chap_m = re.search(r'\.\s+In\s+', rest, re.IGNORECASE)
        jour_m = _P_JOURNAL_SEP.search(rest)
        if chap_m and (jour_m is None or chap_m.start() <= jour_m.start()):
            r.title = rest[:chap_m.start()].strip()
            after_in = rest[chap_m.end():].strip()
            r.venue, _ = _p_extract_italic(after_in)
            r.venue_type = "book_chapter"
            pp = _P_PP_PAGES.search(after_in)
            if pp:
                r.pages = _p_clean_pages(pp.group(1))
        elif jour_m:
            tc = jour_m.group(1)
            r.title = rest[:jour_m.start() + (1 if tc in ('?', '!') else 0)].strip()
            after_sep = rest[jour_m.end():]
            r.venue, after_j = _p_extract_italic(after_sep)
            r.venue_type = "journal"
            vol_rest = after_j.strip().lstrip(',').strip()
            m = _P_VOL_ISS_PP.match(vol_rest)
            if m:
                r.volume, r.issue, r.pages = m.group(1), m.group(2), _p_clean_pages(m.group(3))
            else:
                m = _P_VOL_ISS.match(vol_rest)
                if m:
                    r.volume, r.issue = m.group(1), m.group(2)
                else:
                    m = _P_VOL_PP.match(vol_rest)
                    if m:
                        r.volume, r.pages = m.group(1), _p_clean_pages(m.group(2))
                    else:
                        m = _P_VOL.match(vol_rest)
                        if m:
                            r.volume = m.group(1)
        else:
            parts = re.split(r'\.\s+(?=[A-Z])', rest, maxsplit=1)
            r.title = parts[0].rstrip('.').strip()
            if len(parts) > 1:
                tail = parts[1].rstrip('.').strip()
                if _P_PUBLISHER.search(tail) or _P_REPORT.search(tail):
                    r.venue_type = "report" if _P_REPORT.search(citation_string) else "book"
                    r.venue = tail
                else:
                    r.venue_type, r.venue = "other", tail or None
            else:
                r.venue_type = "other"
    if not r.title or not r.year:
        r.parse_quality = "malformed"
    elif r.doi:
        r.parse_quality = "has_doi"
    elif r.venue_type == "journal":
        r.parse_quality = "clean_journal"
    elif r.venue_type == "book":
        r.parse_quality = "clean_book"
    elif r.venue_type == "book_chapter":
        r.parse_quality = "clean_chapter"
    elif r.venue_type == "report":
        r.parse_quality = "clean_report"
    else:
        r.parse_quality = "clean_journal" if r.venue else "malformed"
    return r

# ===========================================================================
# Resolver (identical logic to Phase B enrich_citations_host_script.py)
# ===========================================================================

@dataclass
class ResolvedReference:
    authors:     Optional[str] = None
    year:        Optional[int] = None
    title:       Optional[str] = None
    venue:       Optional[str] = None
    venue_type:  Optional[str] = None
    volume:      Optional[str] = None
    issue:       Optional[str] = None
    pages:       Optional[str] = None
    doi:         Optional[str] = None
    openalex_id: Optional[str] = None
    pmid:        Optional[str] = None
    url:         Optional[str] = None
    source:      str = "unresolved"
    confidence:  str = "none"
    verified_on: Optional[str] = None

_CR_TYPE = {"journal-article":"journal","book":"book","book-chapter":"book_chapter",
            "monograph":"book","edited-book":"book","proceedings-article":"proceedings",
            "report":"report","posted-content":"preprint","dissertation":"other"}
_OA_TYPE = {"journal-article":"journal","article":"journal","book":"book",
            "book-chapter":"book_chapter","proceedings-article":"proceedings",
            "report":"report","preprint":"preprint","dissertation":"other","dataset":"other"}

def _norm(s): return unicodedata.normalize("NFKD", s.lower())
def _strip_md(s): return re.sub(r"[*_`\[\]]", " ", s)
def _stable_key(cs, journal, year): return json.dumps([cs, journal, year], sort_keys=True)
def _cache_path(cache_dir, key):
    h = hashlib.sha256(key.encode()).hexdigest()[:20]
    return cache_dir / f"{h}.json"

def _extract_surnames(cs):
    before = re.split(r"\(", cs)[0]
    before = _strip_md(before)
    parts = re.split(r"[,&]|\band\b", before, flags=re.IGNORECASE)
    surnames = []
    for part in parts:
        for word in part.strip().split():
            word = word.rstrip(".,;:")
            if re.match(r"^[A-Za-z]\.?$", word): continue
            if len(word) > 1:
                surnames.append(_norm(word)); break
    return surnames

def _author_match(cs, api_authors):
    surnames = _extract_surnames(cs)
    if not surnames: return True
    families = [_norm(a.get("family") or a.get("name") or "") for a in api_authors]
    families = [f for f in families if f]
    if not families: return True
    return any(s in f or f in s for s in surnames for f in families)

def _is_biomed(cs, journal):
    h = _norm((cs or "") + " " + (journal or ""))
    return any(t in h for t in BIOMED_TOKENS)

def _fmt_cr_authors(authors):
    parts = []
    for a in authors:
        fam = (a.get("family") or "").strip()
        giv = (a.get("given") or "").strip()
        if fam and giv:
            parts.append(f"{fam}, {' '.join(w[0]+'.' for w in giv.split() if w)}")
        elif fam:
            parts.append(fam)
    if not parts: return None
    if len(parts) == 1: return parts[0]
    return ", ".join(parts[:-1]) + ", & " + parts[-1]

def _fmt_oa_authors(authorships):
    parts = [((a.get("author") or {}).get("display_name") or "").strip()
             for a in authorships]
    parts = [p for p in parts if p]
    if not parts: return None
    if len(parts) == 1: return parts[0]
    return ", ".join(parts[:-1]) + ", & " + parts[-1]

def _get(url, params, host, session):
    now = time.monotonic()
    wait = RATE_LIMIT_SEC - (now - _last_call.get(host, 0.0))
    if wait > 0: time.sleep(wait)
    _last_call[host] = time.monotonic()
    for attempt, backoff in enumerate([1, 2, 4]):
        try:
            resp = session.get(url, params=params, timeout=12)
        except requests.RequestException:
            if attempt < 2: time.sleep(backoff); continue
            return None
        if resp.status_code in (429, 500, 502, 503, 504):
            if attempt < 2: time.sleep(backoff); continue
            return None
        if resp.status_code >= 400: return None
        return resp
    return None

def _verify_doi(doi, session):
    try:
        r = session.head(f"https://doi.org/{doi}", timeout=8, allow_redirects=True)
        return r.status_code < 400
    except requests.RequestException:
        return False

def _try_crossref(cs, year, session):
    params = {"query.bibliographic": cs, "rows": "3", "mailto": MAILTO}
    if year: params["filter"] = f"from-pub-date:{year},until-pub-date:{year}"
    resp = _get("https://api.crossref.org/works", params, "api.crossref.org", session)
    if not resp: return None
    try: items = resp.json().get("message", {}).get("items", [])
    except Exception: return None
    for item in items[:3]:
        parts = item.get("published", {}).get("date-parts", [[None]])
        iy = parts[0][0] if parts and parts[0] else None
        if year and iy != year: continue
        cr_authors = item.get("author", [])
        if cr_authors and not _author_match(cs, cr_authors): continue
        doi_val = item.get("DOI") or None
        titles = item.get("title", []); container = item.get("container-title", [])
        return ResolvedReference(
            authors=_fmt_cr_authors(cr_authors), year=iy,
            title=titles[0] if titles else None,
            venue=container[0] if container else None,
            venue_type=_CR_TYPE.get(item.get("type", ""), "other"),
            volume=item.get("volume") or None, issue=item.get("issue") or None,
            pages=item.get("page") or None, doi=doi_val,
            url=f"https://doi.org/{doi_val}" if doi_val else None,
            source="crossref", confidence="high", verified_on=TODAY)
    return None

def _try_openalex(cs, year, session):
    stripped = re.sub(r"\s+", " ", _strip_md(cs)).strip()
    params = {"search": stripped, "per-page": "3", "mailto": MAILTO}
    if year: params["filter"] = f"publication_year:{year}"
    resp = _get("https://api.openalex.org/works", params, "api.openalex.org", session)
    if not resp: return None
    try: results = resp.json().get("results", [])
    except Exception: return None
    for item in results[:3]:
        iy = item.get("publication_year")
        if year and iy != year: continue
        authorships = item.get("authorships", [])
        api_authors = [{"family": ((a.get("author") or {}).get("display_name") or "").rsplit(" ", 1)[-1]}
                       for a in authorships]
        if api_authors and not _author_match(cs, api_authors): continue
        raw_doi = item.get("doi") or ""
        doi = raw_doi.replace("https://doi.org/", "").strip() or None
        loc = item.get("primary_location") or {}
        src_info = loc.get("source") or {}
        oa_url = (item.get("open_access") or {}).get("oa_url") or None
        landing = item.get("landing_page_url") or None
        url = oa_url or (f"https://doi.org/{doi}" if doi else landing)
        return ResolvedReference(
            authors=_fmt_oa_authors(authorships), year=iy,
            title=item.get("display_name") or item.get("title"),
            venue=src_info.get("display_name") or None,
            venue_type=_OA_TYPE.get(item.get("type", ""), "other"),
            doi=doi, openalex_id=item.get("id") or None, url=url,
            source="openalex", confidence="high" if doi else "medium", verified_on=TODAY)
    return None

def _try_europepmc(cs, year, journal, session):
    if not _is_biomed(cs, journal): return None
    q = cs if not year else f"{cs} AND PUB_YEAR:{year}"
    resp = _get("https://www.ebi.ac.uk/europepmc/webservices/rest/search",
                {"query": q, "format": "json", "resultType": "core", "pageSize": "3"},
                "www.ebi.ac.uk", session)
    if not resp: return None
    try: results = resp.json().get("resultList", {}).get("result", [])
    except Exception: return None
    for item in results[:3]:
        raw_year = item.get("pubYear")
        iy = int(raw_year) if raw_year and str(raw_year).isdigit() else None
        if year and iy != year: continue
        al = item.get("authorList", {}).get("author", [])
        api_authors = [{"family": a.get("lastName", "")} for a in al]
        if api_authors and not _author_match(cs, api_authors): continue
        authors_str = "; ".join(f"{a.get('lastName','')}, {a.get('initials','')}".strip(", ")
                                for a in al if a.get("lastName")) or None
        pmid_val = str(item.get("pmid")) if item.get("pmid") else None
        doi_val  = item.get("doi") or None
        url = (f"https://europepmc.org/article/MED/{pmid_val}" if pmid_val
               else (f"https://doi.org/{doi_val}" if doi_val else None))
        return ResolvedReference(
            authors=authors_str, year=iy,
            title=item.get("title") or None, venue=item.get("journalTitle") or None,
            venue_type="journal" if item.get("journalTitle") else "other",
            doi=doi_val, pmid=pmid_val, url=url,
            source="europepmc", confidence="medium", verified_on=TODAY)
    return None

def _try_semanticscholar(cs, year, session):
    stripped = re.sub(r"\s+", " ", _strip_md(cs)).strip()
    params = {"query": stripped, "limit": "3",
              "fields": "externalIds,title,authors,venue,year"}
    if year: params["year"] = str(year)
    resp = _get("https://api.semanticscholar.org/graph/v1/paper/search",
                params, "api.semanticscholar.org", session)
    if not resp: return None
    try: results = resp.json().get("data", [])
    except Exception: return None
    for item in results[:3]:
        iy = item.get("year")
        if year and iy != year: continue
        ss_authors = item.get("authors", [])
        api_authors = [{"family": a.get("name", "").rsplit(" ", 1)[-1]}
                       for a in ss_authors if a.get("name")]
        if api_authors and not _author_match(cs, api_authors): continue
        ext = item.get("externalIds") or {}
        doi = ext.get("DOI") or None
        pmid = str(ext.get("PubMed")) if ext.get("PubMed") else None
        url = (item.get("url") or (f"https://doi.org/{doi}" if doi else None)
               or (f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None))
        return ResolvedReference(
            authors=", ".join(a.get("name","") for a in ss_authors) or None,
            year=iy, title=item.get("title") or None, venue=item.get("venue") or None,
            venue_type="journal", doi=doi, pmid=pmid, url=url,
            source="semanticscholar", confidence="low", verified_on=TODAY)
    return None

def resolve_reference(citation_string, venue, year, cache_dir, session):
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = _stable_key(citation_string, venue, year)
    cpath = _cache_path(cache_dir, key)
    if cpath.exists():
        try:
            return ResolvedReference(**json.loads(cpath.read_text(encoding="utf-8")))
        except Exception:
            pass
    if year and year < 1900:
        result = ResolvedReference(year=year, source="historical",
                                   confidence="low", verified_on=TODAY)
        cpath.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2), encoding="utf-8")
        return result
    result = _try_crossref(citation_string, year, session)
    if result is None: result = _try_openalex(citation_string, year, session)
    if result is None: result = _try_europepmc(citation_string, year, venue, session)
    if result is None: result = _try_semanticscholar(citation_string, year, session)
    if result is not None and result.doi:
        if not _verify_doi(result.doi, session):
            result.doi = None
    if result is None:
        result = ResolvedReference(year=year, source="unresolved",
                                   confidence="none", verified_on=TODAY)
    if result.url is None:
        if result.doi: result.url = f"https://doi.org/{result.doi}"
        elif result.pmid: result.url = f"https://pubmed.ncbi.nlm.nih.gov/{result.pmid}/"
    cpath.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2), encoding="utf-8")
    return result

# ===========================================================================
# Build target reference object
# ===========================================================================

FIELD_ORDER = [
    "authors", "year", "title", "venue", "venue_type", "journal",
    "volume", "issue", "pages", "doi", "openalex_id", "pmid",
    "citation_string", "url", "source", "confidence", "verified_on",
]

def build_ref_object(citation_string, parsed, resolved):
    """Merge ParsedCitation + ResolvedReference into the target schema dict.

    Resolver fields take precedence over parser fields.
    citation_string is always preserved verbatim.
    journal is populated only when venue_type == 'journal'.
    """
    venue_type = resolved.venue_type or parsed.venue_type or "other"
    venue      = resolved.venue or parsed.venue
    title      = resolved.title or parsed.title or ""
    authors    = resolved.authors or parsed.authors or ""
    year       = resolved.year or parsed.year
    volume     = resolved.volume or parsed.volume
    issue      = resolved.issue or parsed.issue
    pages      = resolved.pages or parsed.pages
    doi        = resolved.doi or parsed.doi

    ref = {
        "authors":         authors,
        "year":            year,
        "title":           title,
        "venue":           venue,
        "venue_type":      venue_type,
        "journal":         venue if venue_type == "journal" else None,
        "volume":          volume,
        "issue":           issue,
        "pages":           pages,
        "doi":             doi,
        "openalex_id":     resolved.openalex_id,
        "pmid":            resolved.pmid,
        "citation_string": citation_string,
        "url":             resolved.url,
        "source":          resolved.source,
        "confidence":      resolved.confidence,
        "verified_on":     resolved.verified_on,
    }
    return {k: ref[k] for k in FIELD_ORDER if k in ref}

# ===========================================================================
# Main
# ===========================================================================

def main():
    ap = argparse.ArgumentParser(description="Enrich task_details.json references (Phase C).")
    ap.add_argument("--workspace", default=None,
                    help="Path to workspace root (default: parent of this script's directory)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Parse only; no network calls, no file writes.")
    ap.add_argument("--write-back", action="store_true",
                    help="Write enriched data back to task_details.json (with backup).")
    args = ap.parse_args()

    script_dir  = Path(__file__).parent
    workspace   = Path(args.workspace) if args.workspace else script_dir.parent
    task_file   = workspace / "task_details.json"
    cache_dir   = script_dir / "citation_cache"   # shared with Phase B
    backup_dir  = workspace / "original"
    output_file = script_dir / "task_details.enriched.json"

    print(f"Loading {task_file} ...")
    with open(task_file, encoding="utf-8") as fh:
        tasks = json.load(fh)
    print(f"  {len(tasks)} tasks loaded.")

    all_refs = []
    for ti, task in enumerate(tasks):
        for ref_key in ("key_references", "recent_references"):
            for ri, ref in enumerate(task.get(ref_key, [])):
                if isinstance(ref, str):
                    all_refs.append((ti, ref_key, ri, ref))

    print(f"  {len(all_refs)} reference strings found.\n")

    parse_cats = Counter()
    parsed_map = {}
    for (ti, rk, ri, s) in all_refs:
        pc = parse_citation(s)
        parse_cats[pc.parse_quality] += 1
        parsed_map[(ti, rk, ri)] = pc

    total = len(all_refs)
    print("Parse statistics:")
    for cat, n in sorted(parse_cats.items(), key=lambda x: -x[1]):
        print(f"  {cat:20s}: {n:4d}  ({100*n/total:.1f}%)")
    print()

    malformed_n = parse_cats["malformed"]
    if malformed_n / total > 0.05:
        print(f"WARNING: malformed rate {100*malformed_n/total:.1f}% exceeds 5% threshold.")
        sys.exit(1)

    if args.dry_run:
        print("--dry-run: stopping here (no network calls, no writes).")
        return

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    print("Resolving references (this may take several minutes) ...")
    print("  Cache shared with Phase B — many hits expected.\n")

    resolved_map = {}
    stats = Counter()
    n_done = 0

    for (ti, rk, ri, s) in all_refs:
        pc = parsed_map[(ti, rk, ri)]
        resolved = resolve_reference(s, pc.venue, pc.year, cache_dir, session)
        resolved_map[(ti, rk, ri)] = resolved
        stats[resolved.source] += 1
        n_done += 1
        if n_done % 50 == 0:
            print(f"  {n_done}/{total} resolved ...")

    print(f"\nResolution complete ({total} refs).")
    print("By source:")
    for src, n in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"  {src:20s}: {n}")
    print()

    errors = []
    for (ti, rk, ri, s) in all_refs:
        obj = build_ref_object(s, parsed_map[(ti, rk, ri)], resolved_map[(ti, rk, ri)])
        if obj["citation_string"] != s:
            errors.append(f"citation_string mismatch at task[{ti}].{rk}[{ri}]")
    if errors:
        print("SANITY FAIL: citation_string preservation errors:")
        for e in errors[:10]: print(f"  {e}")
        sys.exit(1)

    enriched_tasks = [dict(task) for task in tasks]
    for (ti, rk, ri, s) in all_refs:
        obj = build_ref_object(s, parsed_map[(ti, rk, ri)], resolved_map[(ti, rk, ri)])
        enriched_tasks[ti][rk][ri] = obj

    for ti, (orig, enr) in enumerate(zip(tasks, enriched_tasks)):
        for rk in ("key_references", "recent_references"):
            orig_n = len(orig.get(rk, []))
            enr_n  = len(enr.get(rk, []))
            if orig_n != enr_n:
                errors.append(f"ref count changed: task[{ti}].{rk} {orig_n}->{enr_n}")
        if orig.get("hedtsk_id") != enr.get("hedtsk_id"):
            errors.append(f"hedtsk_id changed at index {ti}")
    if errors:
        print("SANITY FAIL:")
        for e in errors[:10]: print(f"  {e}")
        sys.exit(1)

    print("Sanity checks passed.")

    enriched_json = json.dumps(enriched_tasks, ensure_ascii=False, indent=2)
    output_file.write_text(enriched_json, encoding="utf-8")
    print(f"Written: {output_file}")

    if args.write_back:
        backup_dir.mkdir(exist_ok=True)
        backup_file = backup_dir / f"task_details_pre_enrichment_{TODAY}.json"
        if not backup_file.exists():
            backup_file.write_text(task_file.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"Backup: {backup_file}")
        task_file.write_text(enriched_json, encoding="utf-8")
        print(f"Written back: {task_file}")
    else:
        print()
        print("Review outputs/task_details.enriched.json, then re-run with --write-back.")

    n_resolved = sum(1 for (ti, rk, ri, s) in all_refs
                     if resolved_map[(ti, rk, ri)].source not in ("unresolved", "historical"))
    n_with_doi = sum(1 for (ti, rk, ri, s) in all_refs
                     if resolved_map[(ti, rk, ri)].doi)
    print()
    print("=" * 50)
    print(f"Total references : {total}")
    print(f"Resolved         : {n_resolved} ({100*n_resolved/total:.1f}%)")
    print(f"With DOI         : {n_with_doi} ({100*n_with_doi/total:.1f}%)")
    print(f"Unresolved       : {stats['unresolved']}")
    print("=" * 50)


if __name__ == "__main__":
    main()
