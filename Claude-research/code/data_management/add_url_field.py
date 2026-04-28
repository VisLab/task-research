#!/usr/bin/env python3
"""
add_url_field.py

One-shot patch: add a `url` field to every reference object in
process_details.json.  No network calls — URL is synthesised from
existing doi / pmid / openalex_id fields, with two specific manual
overrides for entries whose URLs were supplied by the user.

Field priority:
  1. Known manual URL (O'Keefe & Nadel, Braver DMCC)
  2. https://doi.org/<doi>          if doi is set
  3. https://pubmed.ncbi.nlm.nih.gov/<pmid>/  if pmid is set (and no doi)
  4. openalex_id                    if it starts with "https://" (and no doi/pmid)
  5. null

Field is inserted after `pmid` in each object so the order reads:
  ..., doi, openalex_id, pmid, url, source, confidence, verified_on

Run from the workspace root:
    python outputs\\add_url_field.py
    python outputs\\add_url_field.py --workspace "H:\\Research\\TaskResearch\\Claude-research"
    python outputs\\add_url_field.py --dry-run   # report counts, don't write

Written by Claude Sonnet, 2026-04-20.
"""

import argparse
import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Specific manual URLs keyed on citation_string
# ---------------------------------------------------------------------------

MANUAL_URLS: dict[str, str] = {
    "O'Keefe & Nadel (1978) *The Hippocampus as a Cognitive Map*":
        "https://repository.arizona.edu/handle/10150/620894",
    "Braver et al. (2021) *Journal of Cognitive Neuroscience* doi:10.1162/jocn_a_01768":
        "https://pmc.ncbi.nlm.nih.gov/articles/PMC10069323/",
}

# Desired field order for a reference object.
FIELD_ORDER = [
    "title", "journal", "year", "citation_string",
    "authors", "venue", "venue_type",
    "volume", "issue", "pages",
    "doi", "openalex_id", "pmid", "url",
    "source", "confidence", "verified_on",
]


def _synthesise_url(ref: dict) -> str | None:
    cs = ref.get("citation_string", "")

    # Manual override takes precedence.
    if cs in MANUAL_URLS:
        return MANUAL_URLS[cs]

    doi = ref.get("doi") or None
    if doi:
        return f"https://doi.org/{doi}"

    pmid = ref.get("pmid") or None
    if pmid:
        return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

    oa_id = ref.get("openalex_id") or None
    if oa_id and str(oa_id).startswith("https://"):
        return oa_id

    return None


def _reorder(ref: dict) -> dict:
    """Return a new dict with fields in FIELD_ORDER; any extras appended at end."""
    ordered: dict = {}
    for field in FIELD_ORDER:
        if field in ref:
            ordered[field] = ref[field]
    for field in ref:
        if field not in ordered:
            ordered[field] = ref[field]
    return ordered


def patch_refs(refs: list[dict]) -> tuple[list[dict], int, int]:
    """Add url field to every ref. Returns (patched_list, added_count, manual_count)."""
    patched = []
    added = 0
    manual = 0
    for ref in refs:
        if "url" in ref:
            # Already has the field (idempotent re-run): just ensure correct order.
            patched.append(_reorder(ref))
            continue
        url = _synthesise_url(ref)
        ref = dict(ref)
        ref["url"] = url
        patched.append(_reorder(ref))
        added += 1
        cs = ref.get("citation_string", "")
        if cs in MANUAL_URLS:
            manual += 1
    return patched, added, manual


def main():
    parser = argparse.ArgumentParser(
        description="Add url field to all process_details.json reference objects.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--workspace", type=Path, default=None,
        help="Path to Claude-research workspace root (default: parent of outputs/)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Report counts without writing.",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).parent.resolve()
    workspace  = args.workspace or script_dir.parent
    path       = workspace / "process_details.json"

    if not path.exists():
        print(f"ERROR: {path} not found.")
        raise SystemExit(1)

    data = json.loads(path.read_text(encoding="utf-8"))
    processes = data.get("processes", [])

    total_refs = 0
    total_added = 0
    total_manual = 0
    doi_count = 0
    pmid_count = 0
    oa_count = 0
    null_count = 0

    for process in processes:
        for ref_key in ("fundamental_references", "recent_references"):
            refs = process.get(ref_key, [])
            patched, added, manual = patch_refs(refs)
            process[ref_key] = patched
            total_refs  += len(patched)
            total_added += added
            total_manual += manual
            for ref in patched:
                u = ref.get("url")
                if u is None:
                    null_count += 1
                elif "doi.org" in u:
                    doi_count += 1
                elif "pubmed" in u or "europepmc" in u:
                    pmid_count += 1
                else:
                    oa_count += 1

    print(f"References processed : {total_refs}")
    print(f"  url field added    : {total_added}  (0 = already present, idempotent re-run)")
    print(f"  manual URL applied : {total_manual}")
    print()
    print("URL breakdown:")
    print(f"  doi.org URL        : {doi_count}")
    print(f"  pubmed/europepmc   : {pmid_count}")
    print(f"  other (OA/repo)    : {oa_count}")
    print(f"  null (no source)   : {null_count}")

    if args.dry_run:
        print()
        print("Dry run — not writing.")
        return

    out = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    path.write_text(out, encoding="utf-8")
    print()
    print(f"Written: {path}")


if __name__ == "__main__":
    main()
