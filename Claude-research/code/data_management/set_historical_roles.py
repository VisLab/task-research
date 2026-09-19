#!/usr/bin/env python3
"""
set_historical_roles.py

One-shot patch: restore the key-versus-recent distinction into the `roles` field.

The April 2026 export of the catalog (the copy hed-task imported) kept two reference
lists per task (`key_references`, `recent_references`) and per process
(`fundamental_references`, `recent_references`). The unified `references` list that
replaced them carries a `roles` field meant to hold that kind of distinction, but the
migration left almost every reference at `["unknown"]`. This script marks a reference
`historical` when the same task or process listed it as a key or fundamental reference
in the April export, so the public site can keep its "Key references" and "Fundamental
references" headings from the data alone.

Matching is by DOI (case-insensitive) within the same task or process, then by exact
`citation_string`, then, for April references that have no DOI (books, pre-DOI papers),
by first surname plus year. `unknown` is dropped from a reference's roles when
`historical` is added; any other existing role is kept.

Run from the workspace root. Dry run is the default; it reports counts and lists the
April key references that found no counterpart, and writes nothing.

    python code/data_management/set_historical_roles.py \\
        --april-tasks <path>/task_details.json --april-processes <path>/process_details.json
    python code/data_management/set_historical_roles.py --april-tasks ... --april-processes ... --write

With --write, the new catalogs are staged in .status/scratch/ first, checked to parse
with unchanged item counts, then written back. Run validate_tasks.py and
validate_catalog.py afterwards. Line endings follow the existing file.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def _doi(ref: dict) -> str:
    ids = ref.get("ids") or {}
    return (ids.get("doi") or ref.get("doi") or "").strip().lower()


_YEAR = re.compile(r"\b(1[6-9]\d\d|20\d\d)\b")
_LEAD = re.compile(r"^[^A-Za-z\u00C0-\u024F]*([A-Za-z\u00C0-\u024F][A-Za-z\u00C0-\u024F'\-]*)")


def _loose(citation: str) -> str:
    """(first surname, year) from a citation string, for references without a DOI.

    Books and old papers carry no DOI and their citation strings were reformatted
    between the two exports ("Pavlov (1927) *Conditioned Reflexes*" against the APA
    form), so the exact string does not match. The first surname plus the year does.
    """
    lead = _LEAD.match(citation)
    year = _YEAR.search(citation)
    if not lead or not year:
        return ""
    return f"{lead.group(1).lower()}|{year.group(1)}"


def _key(ref: dict) -> tuple[str, str, str]:
    """A matching key: (doi, citation_string, loose surname-year). Parts may be empty."""
    cite = (ref.get("citation_string") or "").strip()
    return _doi(ref), cite, _loose(cite)


def _matches(ref: dict, keys: set[tuple[str, str, str]]) -> bool:
    """DOI first; then exact citation string; then surname-year, only against old
    references that have no DOI of their own."""
    doi, cite, loose = _key(ref)
    if doi and any(k[0] == doi for k in keys):
        return True
    if cite and any(k[1] == cite for k in keys):
        return True
    return bool(loose) and any(k[2] == loose and not k[0] for k in keys)


def _apply(
    records: list[dict], april_by_id: dict[str, dict], id_field: str, old_fields: tuple[str, ...], label: str
) -> dict:
    stats = {"marked": 0, "already": 0, "unmatched_old": [], "records_without_april": 0}
    for rec in records:
        april = april_by_id.get(rec[id_field])
        if april is None:
            stats["records_without_april"] += 1
            continue
        old_keys = {_key(r) for f in old_fields for r in april.get(f, [])}
        matched_keys: set[tuple[str, str]] = set()
        for ref in rec.get("references", []):
            if _matches(ref, old_keys):
                matched_keys.add(_key(ref))
                roles = list(ref.get("roles") or [])
                if "historical" in roles:
                    stats["already"] += 1
                    continue
                roles = [r for r in roles if r != "unknown"] + ["historical"]
                ref["roles"] = roles
                stats["marked"] += 1
        for k in old_keys:
            hit = (
                (k[0] and any(m[0] == k[0] for m in matched_keys))
                or (k[1] and any(m[1] == k[1] for m in matched_keys))
                or (k[2] and not k[0] and any(m[2] == k[2] for m in matched_keys))
            )
            if not hit:
                stats["unmatched_old"].append((rec[id_field], k[1][:90] or k[0]))
    print(f"{label}: marked historical {stats['marked']}, already historical {stats['already']}, ")
    print(
        f"  records with no April counterpart {stats['records_without_april']}, April key refs unmatched {len(stats['unmatched_old'])}"
    )
    for rid, what in stats["unmatched_old"][:40]:
        print(f"    unmatched: {rid} | {what}")
    if len(stats["unmatched_old"]) > 40:
        print(f"    ... {len(stats['unmatched_old']) - 40} more")
    return stats


def _read(path: Path) -> tuple[object, str]:
    raw = path.read_bytes()
    newline = "\r\n" if b"\r\n" in raw else "\n"
    return json.loads(raw.decode("utf-8")), newline


def _dump(data: object, newline: str) -> str:
    text = json.dumps(data, indent=2, ensure_ascii=False)
    if newline == "\r\n":
        text = text.replace("\n", "\r\n")
    return text + newline


def _stage_and_write(data: object, target: Path, scratch: Path, newline: str, count_before: int, count_of) -> None:
    scratch.mkdir(parents=True, exist_ok=True)
    staged = scratch / target.name
    staged.write_bytes(_dump(data, newline).encode("utf-8"))
    reparsed = json.loads(staged.read_bytes().decode("utf-8"))
    count_after = count_of(reparsed)
    if count_after != count_before:
        sys.exit(f"refusing to write {target.name}: item count changed {count_before} -> {count_after}")
    target.write_bytes(staged.read_bytes())
    print(f"wrote {target} ({count_after} items; staged copy at {staged})")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace", type=Path, default=Path("."), help="catalog workspace root (default: .)")
    ap.add_argument(
        "--april-tasks", type=Path, required=True, help="April export of task_details.json (has key_references)"
    )
    ap.add_argument(
        "--april-processes",
        type=Path,
        required=True,
        help="April export of process_details.json (has fundamental_references)",
    )
    ap.add_argument("--write", action="store_true", help="write the catalogs back (default: dry run)")
    args = ap.parse_args()

    ws = args.workspace
    tasks_path, procs_path = ws / "task_details.json", ws / "process_details.json"
    tasks, t_nl = _read(tasks_path)
    procs, p_nl = _read(procs_path)
    april_tasks, _ = _read(args.april_tasks)
    april_procs, _ = _read(args.april_processes)

    april_t_by_id = {t["hedtsk_id"]: t for t in april_tasks}
    april_p_by_id = {p["process_id"]: p for p in april_procs["processes"]}

    _apply(tasks, april_t_by_id, "hedtsk_id", ("key_references",), "tasks")
    _apply(procs["processes"], april_p_by_id, "process_id", ("fundamental_references",), "processes")

    if not args.write:
        print("dry run: nothing written (pass --write to apply)")
        return 0

    scratch = ws.parent / ".status" / "scratch" / "set_historical_roles"
    _stage_and_write(tasks, tasks_path, scratch, t_nl, len(tasks), len)
    _stage_and_write(procs, procs_path, scratch, p_nl, len(procs["processes"]), lambda d: len(d["processes"]))
    print("now run: python code/data_management/validate_tasks.py && python code/data_management/validate_catalog.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
