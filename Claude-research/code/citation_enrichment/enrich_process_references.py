#!/usr/bin/env python3
"""
enrich_process_references.py

Driver for Phase B of the citation-enrichment workstream.

Loads process_details.json, calls resolve_reference() on every entry in
fundamental_references and recent_references, writes an enriched copy to
outputs/process_details.enriched.json, and prints a resolution summary.

Usage (from the workspace root or the outputs/ directory):
    python outputs/enrich_process_references.py
    python outputs/enrich_process_references.py --workspace "H:\\Research\\TaskResearch\\Claude-research"
    python outputs/enrich_process_references.py --write-back   # update process_details.json in place

Requires: resolve_citations.py in the same directory (outputs/).
Depends only on stdlib + requests.

IMPORTANT: This script reads process_details.json via the filesystem path
passed to --workspace (or inferred from the script's location). Do NOT edit
process_details.json while this script is running.
"""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

# Ensure resolve_citations is importable whether run from workspace root or outputs/
_SCRIPT_DIR = Path(__file__).parent.resolve()
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from resolve_citations import resolve_reference, ResolvedReference  # noqa: E402

import requests

USER_AGENT = "hed-task/1.0 (mailto:hedannotation@gmail.com)"
TODAY = "2026-04-20"

# Fields added by the resolver (never overwrite originals: journal, year, citation_string)
RESOLVER_FIELDS = (
    "authors", "title", "venue", "venue_type",
    "volume", "issue", "pages",
    "doi", "openalex_id", "pmid",
    "source", "confidence", "verified_on",
)


def enrich_ref(ref: dict, cache_dir: Path, session: requests.Session) -> dict:
    """
    Resolve citation and merge resolver fields into a copy of ref.
    Original fields (journal, year, citation_string) are always preserved.
    """
    citation_string = ref.get("citation_string", "")
    journal = ref.get("journal") or None
    year = ref.get("year") or None

    resolved = resolve_reference(citation_string, journal, year, cache_dir, session)
    r = asdict(resolved)

    enriched = dict(ref)  # copy original
    for field in RESOLVER_FIELDS:
        val = r.get(field)
        # Always write source/confidence/verified_on; for others only if non-None
        if field in ("source", "confidence", "verified_on"):
            enriched[field] = val
        elif val is not None:
            enriched[field] = val
        elif field not in enriched:
            enriched[field] = None
    return enriched


def count_refs(processes: list) -> int:
    return sum(
        len(p.get("fundamental_references", [])) + len(p.get("recent_references", []))
        for p in processes
    )


def main():
    parser = argparse.ArgumentParser(
        description="Enrich process_details.json references with CrossRef/OpenAlex/EuropePMC/S2."
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=None,
        help=(
            "Path to Claude-research workspace root "
            "(default: parent of the outputs/ directory where this script lives)"
        ),
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="Directory for per-lookup JSON cache files (default: outputs/citation_cache/)",
    )
    parser.add_argument(
        "--write-back",
        action="store_true",
        help="After enrichment, write process_details.enriched.json back to process_details.json",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load and report counts, then exit without making any API calls",
    )
    args = parser.parse_args()

    workspace  = args.workspace  or _SCRIPT_DIR.parent
    cache_dir  = args.cache_dir  or (_SCRIPT_DIR / "citation_cache")
    input_path = workspace / "process_details.json"
    working_path = _SCRIPT_DIR / "process_details.working.json"
    output_path  = _SCRIPT_DIR / "process_details.enriched.json"

    print("=" * 60)
    print("enrich_process_references.py")
    print("=" * 60)
    print(f"Workspace : {workspace}")
    print(f"Input     : {input_path}")
    print(f"Cache dir : {cache_dir}")
    print(f"Output    : {output_path}")
    if args.write_back:
        print(f"Write-back: yes — will update {input_path}")
    print()

    if not input_path.exists():
        print(f"ERROR: {input_path} not found. Pass --workspace to point at the correct root.")
        sys.exit(1)

    # Load
    print("Loading process_details.json ...", end=" ", flush=True)
    data = json.loads(input_path.read_text(encoding="utf-8"))
    processes = data.get("processes", [])
    total_refs = count_refs(processes)
    print(f"OK: {len(processes)} processes, {total_refs} references")

    if args.dry_run:
        print("\nDry run — exiting without resolving any references.")
        return

    # Write a working copy so we can inspect/compare before committing
    working_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Working copy: {working_path}")
    print()

    # Set up requests session
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    # Resolution counters
    conf_counts: dict[str, int] = {"high": 0, "medium": 0, "low": 0, "none": 0}
    src_counts:  dict[str, int] = {}
    done = 0
    unresolved_list: list[tuple[str, str]] = []  # (process_id, citation_string)

    try:
        for process in processes:
            pid = process["process_id"]
            for ref_key in ("fundamental_references", "recent_references"):
                refs = process.get(ref_key, [])
                for i, ref in enumerate(refs):
                    enriched = enrich_ref(ref, cache_dir, session)
                    refs[i] = enriched
                    done += 1

                    conf = enriched.get("confidence", "none")
                    conf_counts[conf] = conf_counts.get(conf, 0) + 1

                    src = enriched.get("source", "unresolved")
                    src_counts[src] = src_counts.get(src, 0) + 1

                    if src == "unresolved":
                        unresolved_list.append((pid, ref.get("citation_string", "")))

                    if done % 25 == 0 or done == total_refs:
                        cs = ref.get("citation_string", "")[:55]
                        print(f"  [{done:3d}/{total_refs}] {pid}: {cs}")
    finally:
        session.close()

    # Write enriched output
    print()
    output_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote: {output_path}")

    if args.write_back:
        input_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote back: {input_path}")

    # Summary
    resolved = conf_counts["high"] + conf_counts["medium"] + conf_counts["low"]
    unresolved = conf_counts["none"]
    pct = lambda n: f"{100 * n // total_refs}%" if total_refs else "0%"

    print()
    print("=" * 40)
    print("Resolution summary")
    print("=" * 40)
    print(f"Total refs   : {total_refs}")
    print(f"Resolved     : {resolved} ({pct(resolved)})")
    print(f"  high       : {conf_counts['high']}")
    print(f"  medium     : {conf_counts['medium']}")
    print(f"  low        : {conf_counts['low']}")
    print(f"Unresolved   : {unresolved} ({pct(unresolved)})")
    print()
    print("By source:")
    for src, count in sorted(src_counts.items(), key=lambda x: -x[1]):
        print(f"  {src:<22}: {count}")

    if unresolved_list:
        print()
        print(f"Unresolved references ({len(unresolved_list)}):")
        for pid, cs in unresolved_list:
            print(f"  [{pid}] {cs}")

    print()
    if not args.write_back:
        print(
            "To update process_details.json, re-run with --write-back, "
            "or copy process_details.enriched.json manually."
        )
    print("Done.")


if __name__ == "__main__":
    main()
