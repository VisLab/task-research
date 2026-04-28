#!/usr/bin/env python3
"""
migrate_references.py — One-time schema migration: flatten reference arrays
and assign roles.

For each process and task:
  - Merges fundamental_references + recent_references (processes) or
    key_references + recent_references (tasks) into a single `references` list.
  - Adds a `roles` field (list) to every reference:
      ["historical"]  — reference matches the curated landmark list for this item
      ["unknown"]     — everything else; curators assign the real role in Phase 5
  - Removes the old array fields from the item.
  - Deduplicates on DOI first, then citation_string, when both arrays share a ref.

Protection contract:
  - References with "historical" in roles must not be removed by downstream
    scripts without an explicit --force-drop-historical flag. This script marks
    them; enforcement is in each downstream script.

Usage (run from workspace root):
    python code/literature_search/migrate_references.py --dry-run
    python code/literature_search/migrate_references.py --write

Options:
    --workspace PATH   workspace root (default: current directory)
    --landmark-refs    path to landmark_refs.json (relative to workspace)
    --write            write output to process_details.json / task_details.json
    --dry-run          (default) print summary only; write to .scratch/
"""

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path


# ---------------------------------------------------------------------------
# Author extraction helpers
# ---------------------------------------------------------------------------

def _normalise(s: str) -> str:
    """Lowercase, strip diacritics, keep only a-z and hyphen.

    Handles: Näätänen→naatanen, Güth→guth, Goldman-Rakic→goldman-rakic.
    """
    nfkd = unicodedata.normalize("NFKD", s)
    ascii_only = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"[^a-z\-]", "", ascii_only.lower())


def _family_from_authors(authors_str: str) -> str:
    """Extract first author family name from structured 'Family, G. I.' string."""
    if not authors_str:
        return ""
    first = authors_str.split(",")[0].strip()
    return _normalise(first)


def _family_from_citation(citation_str: str) -> str:
    """Extract first author family name from 'Author (year) ...' citation string."""
    if not citation_str:
        return ""
    # Match name including hyphens: Goldman-Rakic, Baron-Cohen, van Ede
    m = re.match(r"([A-Za-z\u00C0-\u024F][A-Za-z\u00C0-\u024F'\-]+)", citation_str.strip())
    return _normalise(m.group(1)) if m else ""


def _ref_family(ref: dict) -> str:
    """Best-effort first-author family name from a reference dict."""
    family = _family_from_authors(ref.get("authors") or "")
    if not family:
        family = _family_from_citation(ref.get("citation_string") or "")
    return family


# ---------------------------------------------------------------------------
# Landmark matching
# ---------------------------------------------------------------------------

def build_landmark_lookup(landmark_refs_path: Path) -> set[tuple[str, str, str]]:
    """Return set of (owner_id, author_family_lower, year_str) from landmark_refs.json.

    Used for Rule a2 matching: (owner, author, year) uniquely identifies almost
    all landmarks even without a DOI.
    """
    data = json.loads(landmark_refs_path.read_text(encoding="utf-8"))
    entries = data.get("entries", data) if isinstance(data, dict) else data
    lookup: set[tuple[str, str, str]] = set()
    for e in entries:
        owner  = e.get("id", "")
        family = _normalise(e.get("first_author_family") or "")
        year   = str(e.get("year") or "")
        if owner and family and year:
            lookup.add((owner, family, year))
    return lookup


def is_landmark(owner_id: str, ref: dict, lookup: set) -> bool:
    """Return True if this reference matches a landmark entry for owner_id."""
    family = _ref_family(ref)
    year   = str(ref.get("year") or "")
    return (owner_id, family, year) in lookup


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def _ref_key(ref: dict) -> str:
    """Stable dedup key: prefer doi, fall back to normalised citation_string."""
    doi = (ref.get("doi") or "").lower().strip()
    if doi:
        return f"doi:{doi}"
    cs = (ref.get("citation_string") or "").strip().lower()
    # Collapse whitespace for tolerance
    cs = re.sub(r"\s+", " ", cs)
    return f"cs:{cs}"


def merge_ref_arrays(*arrays: list[dict]) -> list[dict]:
    """Concatenate arrays, dropping duplicates by doi/citation_string.

    First occurrence wins; later duplicates are silently dropped.
    """
    seen: set[str] = set()
    result: list[dict] = []
    for arr in arrays:
        for ref in (arr or []):
            key = _ref_key(ref)
            if key not in seen:
                seen.add(key)
                result.append(ref)
    return result


# ---------------------------------------------------------------------------
# Per-item migration
# ---------------------------------------------------------------------------

def migrate_process(proc: dict, landmark_lookup: set) -> dict:
    """Return a new process dict with the merged references schema."""
    owner_id = proc["process_id"]
    fund = proc.pop("fundamental_references", []) or []
    rec  = proc.pop("recent_references", []) or []
    refs = merge_ref_arrays(fund, rec)

    for ref in refs:
        if is_landmark(owner_id, ref, landmark_lookup):
            ref["roles"] = ["historical"]
        else:
            ref["roles"] = ["unknown"]

    proc["references"] = refs
    return proc


def migrate_task(task: dict, landmark_lookup: set) -> dict:
    """Return a new task dict with the merged references schema."""
    owner_id = task["hedtsk_id"]
    key_refs = task.pop("key_references", []) or []
    rec_refs = task.pop("recent_references", []) or []
    refs = merge_ref_arrays(key_refs, rec_refs)

    for ref in refs:
        if is_landmark(owner_id, ref, landmark_lookup):
            ref["roles"] = ["historical"]
        else:
            ref["roles"] = ["unknown"]

    task["references"] = refs
    return task


# ---------------------------------------------------------------------------
# Summary helpers
# ---------------------------------------------------------------------------

def summarise(label: str, items: list[dict], id_field: str) -> None:
    total_refs = 0
    historical = 0
    unknown    = 0
    for item in items:
        for ref in item.get("references", []):
            roles = ref.get("roles", [])
            total_refs += 1
            if "historical" in roles:
                historical += 1
            else:
                unknown += 1
    print(f"  {label}: {len(items)} items, {total_refs} refs "
          f"({historical} historical, {unknown} unknown)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="Migrate reference arrays to unified schema.")
    ap.add_argument("--workspace",     default=".",
                    help="Workspace root (default: current directory)")
    ap.add_argument("--landmark-refs", default="outputs/literature_search/landmark_refs.json",
                    help="Path to landmark_refs.json (relative to workspace)")
    ap.add_argument("--write",         action="store_true",
                    help="Write output to process_details.json / task_details.json")
    ap.add_argument("--dry-run",       action="store_true",
                    help="(default) Print summary; write only to .scratch/")
    args = ap.parse_args()

    ws = Path(args.workspace)
    landmark_path = ws / args.landmark_refs
    pd_path       = ws / "process_details.json"
    td_path       = ws / "task_details.json"
    scratch       = ws / ".scratch"
    scratch.mkdir(exist_ok=True)

    # Load
    landmark_lookup = build_landmark_lookup(landmark_path)
    print(f"Landmark lookup entries: {len(landmark_lookup)}")

    pd_data = json.loads(pd_path.read_text(encoding="utf-8"))
    td_data = json.loads(td_path.read_text(encoding="utf-8"))

    processes = pd_data.get("processes", [])
    tasks     = td_data if isinstance(td_data, list) else td_data.get("tasks", [])

    # Migrate
    migrated_procs = [migrate_process(p, landmark_lookup) for p in processes]
    migrated_tasks = [migrate_task(t, landmark_lookup)    for t in tasks]

    pd_data["processes"] = migrated_procs
    if isinstance(td_data, list):
        td_data = migrated_tasks
    else:
        td_data["tasks"] = migrated_tasks

    # Summary
    print("\nMigration summary:")
    summarise("process_details", migrated_procs, "process_id")
    summarise("task_details",    migrated_tasks,  "hedtsk_id")

    # Spot-check: how many got historical?
    hist_procs = [(p["process_id"], r.get("citation_string","")[:60])
                  for p in migrated_procs
                  for r in p.get("references", [])
                  if "historical" in r.get("roles", [])]
    print(f"\n  Historical references found: {len(hist_procs)}")
    for pid, cs in hist_procs[:10]:
        print(f"    {pid}: {cs}")
    if len(hist_procs) > 10:
        print(f"    ... and {len(hist_procs) - 10} more")

    # Validate JSON round-trip
    pd_json = json.dumps(pd_data, ensure_ascii=False, indent=2)
    td_json = json.dumps(td_data, ensure_ascii=False, indent=2)
    json.loads(pd_json)   # raises if invalid
    json.loads(td_json)

    # Always write to .scratch/ for inspection
    scratch_pd = scratch / "process_details_migrated.json"
    scratch_td = scratch / "task_details_migrated.json"
    scratch_pd.write_text(pd_json, encoding="utf-8")
    scratch_td.write_text(td_json, encoding="utf-8")
    print(f"\nStaged to:")
    print(f"  {scratch_pd}")
    print(f"  {scratch_td}")

    if args.write:
        pd_path.write_text(pd_json, encoding="utf-8")
        td_path.write_text(td_json, encoding="utf-8")
        print("\nWritten to workspace root. Migration complete.")
    else:
        print("\nDry-run: workspace root files NOT changed. Pass --write to apply.")


if __name__ == "__main__":
    main()
