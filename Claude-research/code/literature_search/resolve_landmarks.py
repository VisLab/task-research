"""
resolve_landmarks.py — Sub-phase 2.1: parse landmark_refs_2026-04-22.md,
resolve each entry via CrossRef + OpenAlex, and write landmark_refs.json.

Usage:
    python resolve_landmarks.py \\
        --md-file  _inputs/landmark_refs.md \\
        --cache-dir cache \\
        --output   landmark_refs.json

Network calls are cached: a rerun on the same day costs zero extra calls.
When network is blocked (sandbox), all entries receive resolution_status
"not_found" but the JSON is still written with correct pub_ids derived
from the MD metadata — sufficient for the Phase 2 triage.
"""

import argparse
import json
import logging
import re
import sys
from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# Infrastructure imports (siblings in outputs/literature_search/)
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent))
from identity import build_pub_id
from clients import crossref as crossref_client
from clients import openalex as openalex_client

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

TODAY = date.today().isoformat()

# ---------------------------------------------------------------------------
# MD parser
# ---------------------------------------------------------------------------

def _first_author_family(citation: str) -> str:
    """Extract first-author family name from a citation string like
    'Eriksen & Eriksen (1974)' or 'Botvinick, Braver, ... & Cohen (2001)'."""
    # Remove bracket annotations like [book_chapter_exception]
    s = re.sub(r"\[.*?\]", "", citation).strip()
    # Remove year-in-parentheses and everything after
    s = re.sub(r"\s*\(\d{4}\).*$", "", s).strip()
    # If comma-separated list, take first token
    if "," in s:
        s = s.split(",")[0].strip()
    elif " & " in s:
        s = s.split(" & ")[0].strip()
    elif " et al" in s.lower():
        s = re.split(r" et al", s, flags=re.IGNORECASE)[0].strip()
    return s


def _extract_year(citation: str) -> int | None:
    m = re.search(r"\((\d{4})\)", citation)
    return int(m.group(1)) if m else None


def _extract_title(title_venue: str) -> str | None:
    """Return quoted title if present, else None."""
    m = re.match(r'"([^"]+)"', title_venue.strip())
    return m.group(1) if m else None


def _first_five_words(title: str) -> str:
    words = title.split()
    return " ".join(words[:5])


def parse_landmark_md(md_text: str) -> list[dict]:
    """Return a list of entry dicts from the landmark MD tables."""
    entries = []
    for line in md_text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        # Skip separator rows
        if re.match(r"^\|[\s\-|]+\|$", line):
            continue
        cells = [c.strip() for c in line.split("|")]
        cells = [c for c in cells if c]
        if len(cells) < 4:
            continue
        id_val = cells[0].strip()
        if not (id_val.startswith("hed_") or id_val.startswith("hedtsk_")):
            continue
        kind = "task" if id_val.startswith("hedtsk_") else "process"
        citation = cells[1].strip()
        title_venue = cells[2].strip()
        conf = cells[3].strip()
        if conf not in ("H", "M", "L"):
            continue  # header row

        family = _first_author_family(citation)
        year = _extract_year(citation)
        title = _extract_title(title_venue)
        title_missing = title is None

        if title_missing:
            print(f"WARNING: {id_val}: title_missing_in_md (citation: {citation!r})",
                  file=sys.stderr)
            title = family  # fallback

        entries.append({
            "id": id_val,
            "kind": kind,
            "citation": citation,
            "first_author_family": family,
            "year": year,
            "md_title": title,
            "title_missing": title_missing,
            "confidence": conf,
            "book_chapter_exception": "[book_chapter_exception]" in citation,
        })
    return entries


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------

def resolve_entry(entry: dict, cache_dir: Path) -> dict:
    """Attempt CrossRef + OpenAlex lookup; return enriched dict."""
    family = entry["first_author_family"]
    year = entry["year"]
    title = entry["md_title"]
    title_terms = _first_five_words(title) if title else ""

    doi = None
    cr_title = None
    resolution_status = "not_found"
    warnings = []

    # --- CrossRef query ---
    if year is not None:
        try:
            cr = crossref_client.lookup_by_query(
                cache_dir=cache_dir,
                author_family=family,
                title_terms=title_terms,
                year=year,
            )
        except Exception as exc:
            logger.warning("crossref error for %s: %s", entry["id"], exc)
            cr = None

        if cr:
            doi = (cr.get("DOI") or "").lower().strip() or None
            title_list = cr.get("title", [])
            cr_title = title_list[0] if title_list else None
            resolution_status = "ambiguous"

            # --- OpenAlex cross-check ---
            if doi:
                try:
                    oa = openalex_client.lookup_by_doi(doi, cache_dir=cache_dir)
                except Exception as exc:
                    logger.warning("openalex error for %s: %s", entry["id"], exc)
                    oa = None

                if oa:
                    oa_year = None
                    pub_date = oa.get("publication_year")
                    if pub_date:
                        oa_year = int(pub_date)
                    if oa_year and oa_year != year:
                        warnings.append(
                            f"{entry['id']}: openalex year {oa_year} != "
                            f"crossref year {year}; kept crossref"
                        )
                    resolution_status = "resolved"

    # pub_id: prefer CrossRef-normalised title; fall back to MD title
    canonical_title = cr_title if cr_title else title
    pub_id = build_pub_id(family, year, canonical_title)

    return {
        "id": entry["id"],
        "kind": entry["kind"],
        "citation": entry["citation"],
        "first_author_family": family,
        "year": year,
        "title": canonical_title,
        "venue": entry.get("md_title", ""),   # MD display title (may include venue)
        "doi": doi,
        "confidence": entry["confidence"],
        "book_chapter_exception": entry["book_chapter_exception"],
        "title_missing_in_md": entry["title_missing"],
        "pub_id": pub_id,
        "resolution_status": resolution_status,
        "_warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="Resolve landmark references")
    ap.add_argument("--md-file", default="_inputs/landmark_refs.md",
                    help="Path to landmark_refs_2026-04-22.md")
    ap.add_argument("--cache-dir", default="cache",
                    help="Cache directory (relative to this script or absolute)")
    ap.add_argument("--output", default="landmark_refs.json",
                    help="Output JSON file")
    args = ap.parse_args()

    script_dir = Path(__file__).parent
    md_path = Path(args.md_file) if Path(args.md_file).is_absolute() \
        else script_dir / args.md_file
    cache_dir = Path(args.cache_dir) if Path(args.cache_dir).is_absolute() \
        else script_dir / args.cache_dir
    output_path = Path(args.output) if Path(args.output).is_absolute() \
        else script_dir / args.output

    md_text = md_path.read_text(encoding="utf-8")
    entries = parse_landmark_md(md_text)

    resolved = []
    all_warnings = []
    n_resolved = n_ambiguous = n_not_found = 0

    for entry in entries:
        result = resolve_entry(entry, cache_dir)
        all_warnings.extend(result.pop("_warnings", []))
        resolved.append(result)
        s = result["resolution_status"]
        if s == "resolved":
            n_resolved += 1
        elif s == "ambiguous":
            n_ambiguous += 1
        else:
            n_not_found += 1

    output = {
        "schema_version": "2026-04-22",
        "generated_on": TODAY,
        "entries": resolved,
    }
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2),
                           encoding="utf-8")

    # --- Summary ---
    print(f"\nLandmark resolution — {TODAY}")
    print()
    print(f"n total:                          {len(resolved)}")
    print(f"n resolved (cross-source agree):  {n_resolved}")
    print(f"n ambiguous (one source unsure):  {n_ambiguous}")
    print(f"n not found:                      {n_not_found}")
    if all_warnings:
        print("\nWarnings:")
        for w in all_warnings:
            print(f"  - {w}")
    else:
        print("\nNo warnings.")
    print(f"\nWrote {output_path}")


if __name__ == "__main__":
    main()
