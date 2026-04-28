"""
fixup_enriched.py  —  post-enrichment cleanup before write-back.

Three fixes applied to task_details.enriched.json (in-place):

  1. DOI recovery:   doi=null + url=https://doi.org/XYZ -> doi=XYZ
  2. HTML unescape:  venue / journal fields with &amp; etc.
  3. False positives: refs where resolved authors don't overlap with
                      citation_string authors -> re-extract from citation_string,
                      set source=needs_review, confidence=low, url=null, doi=null.

Run from workspace root:
    python outputs\fixup_enriched.py
"""
import html, json, re, unicodedata
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
ENRICHED   = SCRIPT_DIR / "task_details.enriched.json"

# -----------------------------------------------------------------------
# Helpers for false-positive detection  (same logic as inspect script)
# -----------------------------------------------------------------------

def _surnames_from(text):
    text = re.sub(r'\s*\[.*', '', text)
    parts = re.split(r"[,&.]|\bet al\b|\band\b", text, flags=re.IGNORECASE)
    result = []
    for p in parts:
        p = p.strip()
        if len(p) > 2 and not re.match(r'^[A-Z]\.?$', p):
            w = unicodedata.normalize("NFKD", p.lower())
            if w:
                result.append(w)
    return result

def _authors_overlap(cs_au, res_au):
    if not cs_au or not res_au:
        return True
    cs_sn = _surnames_from(cs_au)
    re_sn = _surnames_from(res_au)
    return any(s in r or r in s for s in cs_sn for r in re_sn)

# -----------------------------------------------------------------------
# Minimal re-parser for false-positive fallback  (extract from APA string)
# -----------------------------------------------------------------------

_YEAR_RE      = re.compile(r'\((\d{4}[a-z]?)\)')
_YEAR_SLASH   = re.compile(r'\((\d{4})/\d{4}[a-z]?\)')
_DOI_INLINE   = re.compile(r'\b(10\.\d{4,9}/[^\s,\])\'"]+)')
_COMPOUND     = re.compile(r'\s*\[(?:Updated|Note|See also|cf\.?)[^\]]*\]', re.IGNORECASE)
_CLOSING_Q    = '\u2018\u2019\u201c\u201d"\''
_JOURNAL_SEP  = re.compile(r'([.?!])[' + _CLOSING_Q + r']?\s+(?=\*)')
_REPORT_WORDS = re.compile(
    r'\b(manual|report|technical|handbook|guide|bulletin|monograph|'
    r'unpublished|dissertation|thesis|working paper)\b', re.IGNORECASE)

def _extract_italic(text):
    m = re.search(r'\*(.+?)\*', text)
    return (m.group(1).strip(), text[m.end():]) if m else ("", text)

def _parse_for_fallback(cs):
    """Return dict with authors/year/title/venue/venue_type extracted from cs."""
    s = _COMPOUND.sub('', cs).strip()
    doi_m = _DOI_INLINE.search(cs)
    doi   = doi_m.group(1).rstrip('.') if doi_m else None
    year_m = _YEAR_RE.search(s) or _YEAR_SLASH.search(s)
    if not year_m:
        return {"authors": "", "year": None, "title": cs[:120], "venue": None,
                "venue_type": "other", "doi": doi}
    year    = int(year_m.group(1)[:4])
    authors = s[:year_m.start()].strip()
    rest    = re.sub(r'^[\.\s]+', '', s[year_m.end():].strip())
    title, venue, venue_type = rest, None, "other"
    if rest.startswith('*'):
        t, after = _extract_italic(rest)
        title = t
        after = after.strip().lstrip('.').strip()
        venue_type = "report" if _REPORT_WORDS.search(cs) else "book"
        venue = after.rstrip('.').strip() or None
    else:
        chap_m = re.search(r'\.\s+In\s+', rest, re.IGNORECASE)
        jour_m = _JOURNAL_SEP.search(rest)
        if chap_m and (jour_m is None or chap_m.start() <= jour_m.start()):
            title = rest[:chap_m.start()].strip()
            after_in = rest[chap_m.end():].strip()
            bk, _ = _extract_italic(after_in)
            venue = bk or None
            venue_type = "book_chapter"
        elif jour_m:
            tc = jour_m.group(1)
            title = rest[:jour_m.start() + (1 if tc in ('?', '!') else 0)].strip()
            jname, _ = _extract_italic(rest[jour_m.end():])
            venue = jname or None
            venue_type = "journal"
        else:
            parts = re.split(r'\.\s+(?=[A-Z])', rest, maxsplit=1)
            title = parts[0].rstrip('.').strip()
            if len(parts) > 1:
                venue = parts[1].rstrip('.').strip() or None
    return {"authors": authors, "year": year, "title": title,
            "venue": venue, "venue_type": venue_type, "doi": doi}

# -----------------------------------------------------------------------
# Load
# -----------------------------------------------------------------------

with open(ENRICHED, encoding="utf-8") as fh:
    tasks = json.load(fh)

fix_doi = fix_html = fix_fp = 0

for task in tasks:
    for rk in ("key_references", "recent_references"):
        for ref in task.get(rk, []):
            if not isinstance(ref, dict):
                continue

            cs    = ref.get("citation_string", "")
            src   = ref.get("source", "")
            doi   = ref.get("doi")
            url   = ref.get("url") or ""
            res_au = ref.get("authors", "")

            cs_au_m = re.match(r'^([^(]+)\s*\(\d{4}', cs)
            cs_au   = cs_au_m.group(1).strip() if cs_au_m else ""

            # ---- Fix 1: false positives --------------------------------
            if (src not in ("unresolved", "historical", "needs_review")
                    and cs_au and res_au
                    and not _authors_overlap(cs_au, res_au)):
                fb = _parse_for_fallback(cs)
                ref["authors"]     = fb["authors"]
                ref["year"]        = fb["year"]
                ref["title"]       = fb["title"]
                ref["venue"]       = fb["venue"]
                ref["venue_type"]  = fb["venue_type"]
                ref["journal"]     = fb["venue"] if fb["venue_type"] == "journal" else None
                ref["volume"]      = None
                ref["issue"]       = None
                ref["pages"]       = None
                ref["doi"]         = fb["doi"]
                ref["openalex_id"] = None
                ref["pmid"]        = None
                ref["url"]         = None
                ref["source"]      = "needs_review"
                ref["confidence"]  = "low"
                fix_fp += 1
                continue   # skip other fixes for this ref

            # ---- Fix 2: recover doi from url ---------------------------
            if doi is None and url.startswith("https://doi.org/"):
                ref["doi"] = url.replace("https://doi.org/", "")
                fix_doi += 1

            # ---- Fix 3: unescape HTML entities in venue/journal --------
            for field in ("venue", "journal"):
                v = ref.get(field)
                if v and ("&amp;" in v or "&#" in v or "&lt;" in v or "&gt;" in v):
                    ref[field] = html.unescape(v)
                    fix_html += 1

print(f"False positives reverted  : {fix_fp}")
print(f"DOIs recovered from url   : {fix_doi}")
print(f"HTML entities unescaped   : {fix_html}")

with open(ENRICHED, "w", encoding="utf-8") as fh:
    json.dump(tasks, fh, ensure_ascii=False, indent=2)
print(f"\nWritten (fixed): {ENRICHED}")
