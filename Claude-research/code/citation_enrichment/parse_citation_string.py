"""
parse_citation_string.py - APA-ish citation string parser for the HED task catalog.
(Canonical source: outputs/parse_citation_string.py in workspace)

Exposes one public function:
    parse(citation_string: str) -> ParsedCitation

ParsedCitation fields: authors, year, title, venue, venue_type,
                       volume, issue, pages, doi, parse_quality

parse_quality values:
    "clean_journal"  - journal article, all major fields found
    "clean_book"     - stand-alone book
    "clean_chapter"  - book chapter (In *Book*)
    "clean_report"   - technical report or manual
    "has_doi"        - DOI found in string (any type)
    "malformed"      - year or title could not be extracted

Design: graceful degradation — never raises, always returns something.
        [Updated: ...] and similar compound annotations are stripped first.
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional

@dataclass
class ParsedCitation:
    authors:       str            = ""
    year:          Optional[int]  = None
    title:         str            = ""
    venue:         Optional[str]  = None
    venue_type:    str            = "other"   # journal|book|book_chapter|report|other
    volume:        Optional[str]  = None
    issue:         Optional[str]  = None
    pages:         Optional[str]  = None
    doi:           Optional[str]  = None
    parse_quality: str            = "malformed"

_YEAR_RE       = re.compile(r'\((\d{4}[a-z]?)\)')
# Slash reprint year: (1969/1868) — capture the first (reprint) year.
_YEAR_SLASH_RE = re.compile(r'\((\d{4})/\d{4}[a-z]?\)')
_DOI_RE        = re.compile(r'\b(10\.\d{4,9}/[^\s,\])\'"]+)')
_COMPOUND_RE   = re.compile(r'\s*\[(?:Updated|Note|See also|cf\.?)[^\]]*\]', re.IGNORECASE)
_VOL_ISS_PAGES = re.compile(r'(\d+)\((\d+)\)[.,]?\s*([\d\w]+\s*[\-\u2013\u2014]\s*[\d\w]+)')
_VOL_PAGES     = re.compile(r'(\d+)[.,]\s*([\d\w]+\s*[\-\u2013\u2014]\s*[\d\w]+)')
_VOL_ISS_ONLY  = re.compile(r'^(\d+)\((\d+)\)')
_VOL_ONLY      = re.compile(r'^(\d+)\b')
_PP_PAGES      = re.compile(r'\(pp\.\s*([\d\w]+\s*[\-\u2013\u2014]\s*[\d\w]+)\)')
_REPORT_WORDS  = re.compile(
    r'\b(manual|report|technical|handbook|guide|bulletin|monograph|'
    r'unpublished|dissertation|thesis|working paper)\b', re.IGNORECASE)
_PUBLISHER_WORDS = re.compile(
    r'\b(press|publishers?|publishing|university|association|institute|'
    r'foundation|society|academic|elsevier|springer|wiley|oxford|cambridge|'
    r'guilford|erlbaum|routledge|taylor|mcgraw|pearson|sage|apa|aps)\b', re.IGNORECASE)

# Separator between title and journal name.
# Handles: ". *J*"  "? *J*"  '." *J*'  '.\u201d *J*'  (period or ? or ! then
# optional closing quote then whitespace then opening asterisk of journal name).
_CLOSING_QUOTES = '\u2018\u2019\u201c\u201d"\''
_JOURNAL_SEP = re.compile(r'([.?!])[' + _CLOSING_QUOTES + r']?\s+(?=\*)')


def _clean_pages(raw: str) -> str:
    return re.sub(r'\s*([\-\u2013\u2014])\s*', r'\1', raw.strip())


def _extract_italicised(text: str) -> tuple:
    """Return (content_of_first_*...*_span, text_after_closing_star)."""
    m = re.search(r'\*(.+?)\*', text)
    if m:
        return m.group(1).strip(), text[m.end():]
    return "", text


def parse(citation_string: str) -> ParsedCitation:
    """Parse an APA-ish citation string. Never raises."""
    result = ParsedCitation()

    # Strip compound annotations, then extract DOI from the original.
    s = _COMPOUND_RE.sub('', citation_string).strip()
    doi_m = _DOI_RE.search(citation_string)
    if doi_m:
        result.doi = doi_m.group(1).rstrip('.')

    # Find year: standard (YYYY) first, then slash-reprint (YYYY/YYYY).
    year_m = _YEAR_RE.search(s)
    if not year_m:
        year_m = _YEAR_SLASH_RE.search(s)
    if not year_m:
        result.parse_quality = "malformed"
        return result

    try:
        result.year = int(year_m.group(1)[:4])
    except ValueError:
        result.parse_quality = "malformed"
        return result

    # Authors: trailing '.' is the last initial — do NOT strip it.
    result.authors = s[:year_m.start()].strip()

    rest = s[year_m.end():].strip()
    rest = re.sub(r'^[\.\s]+', '', rest)   # strip leading ". "

    if not rest:
        result.parse_quality = "malformed"
        return result

    if rest.startswith('*'):
        # Italicised title -> stand-alone book or report.
        title_text, after_title = _extract_italicised(rest)
        result.title = title_text
        after_title = after_title.strip().lstrip('.').strip()
        result.venue_type = "report" if _REPORT_WORDS.search(citation_string) else "book"
        if after_title:
            result.venue = after_title.rstrip('.').strip() or None
    else:
        chapter_m = re.search(r'\.\s+In\s+', rest, re.IGNORECASE)
        journal_m = _JOURNAL_SEP.search(rest)

        if chapter_m and (journal_m is None or chapter_m.start() <= journal_m.start()):
            # Book chapter
            result.title = rest[:chapter_m.start()].strip()
            after_in = rest[chapter_m.end():].strip()
            book_name, _tail = _extract_italicised(after_in)
            result.venue = book_name or None
            result.venue_type = "book_chapter"
            pp_m = _PP_PAGES.search(after_in)
            if pp_m:
                result.pages = _clean_pages(pp_m.group(1))

        elif journal_m:
            # Journal article: include '?' or '!' in the title but not '.'.
            term_char = journal_m.group(1)
            end_of_title = journal_m.start() + (1 if term_char in ('?', '!') else 0)
            result.title = rest[:end_of_title].strip()
            # Journal section starts right at the opening *.
            after_sep = rest[journal_m.end():]
            journal_name, after_journal = _extract_italicised(after_sep)
            result.venue = journal_name or None
            result.venue_type = "journal"
            vol_rest = after_journal.strip().lstrip(',').strip()

            m = _VOL_ISS_PAGES.match(vol_rest)
            if m:
                result.volume = m.group(1)
                result.issue  = m.group(2)
                result.pages  = _clean_pages(m.group(3))
            else:
                m = _VOL_ISS_ONLY.match(vol_rest)
                if m:
                    result.volume = m.group(1)
                    result.issue  = m.group(2)
                else:
                    m = _VOL_PAGES.match(vol_rest)
                    if m:
                        result.volume = m.group(1)
                        result.pages  = _clean_pages(m.group(2))
                    else:
                        m = _VOL_ONLY.match(vol_rest)
                        if m:
                            result.volume = m.group(1)
        else:
            # No venue marker — treat as bare book/other.
            parts = re.split(r'\.\s+(?=[A-Z])', rest, maxsplit=1)
            result.title = parts[0].rstrip('.').strip()
            if len(parts) > 1:
                tail = parts[1].rstrip('.').strip()
                if _PUBLISHER_WORDS.search(tail) or _REPORT_WORDS.search(tail):
                    result.venue_type = "report" if _REPORT_WORDS.search(citation_string) else "book"
                    result.venue = tail
                else:
                    result.venue_type = "other"
                    result.venue = tail or None
            else:
                result.venue_type = "other"

    if not result.title or not result.year:
        result.parse_quality = "malformed"
    elif result.doi:
        result.parse_quality = "has_doi"
    elif result.venue_type == "journal":
        result.parse_quality = "clean_journal"
    elif result.venue_type == "book":
        result.parse_quality = "clean_book"
    elif result.venue_type == "book_chapter":
        result.parse_quality = "clean_chapter"
    elif result.venue_type == "report":
        result.parse_quality = "clean_report"
    else:
        result.parse_quality = "clean_journal" if result.venue else "malformed"

    return result
