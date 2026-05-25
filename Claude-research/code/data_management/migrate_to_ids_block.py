#!/usr/bin/env python3
"""
migrate_to_ids_block.py — One-shot migration of reference shape.

Schema change of 2026-05-19 (see .status/plan_2026-05-19_rec1_v2.md):

  Before:
    {
      ...,
      "doi": "10.xxxx/yyy",
      "openalex_id": null,
      "pmid": null,
      "url": "https://doi.org/10.xxxx/yyy",
      "roles": ["historical"]
    }

  After:
    {
      ...,
      "ids": {
        "doi": "10.xxxx/yyy",
        "openalex_id": null,
        "pmid": null,
        "pmcid": null,
        "s2_id": null,
        "arxiv_id": null
      },
      "url": "https://doi.org/10.xxxx/yyy",
      "pub_id": null,
      "oa_status": "unknown",
      "roles": ["historical"]
    }

Three changes per reference:

1. Flat ID fields (`doi`, `openalex_id`, `pmid`) move into a nested
   `ids` block, joined by three new always-present null fields
   (`pmcid`, `s2_id`, `arxiv_id`).
2. `url` and `pub_id` stay at the top level (they're not external
   identifiers — `url` is a location, `pub_id` is the content-
   addressed cross-repo key).  `pub_id` is added as `null` if absent.
3. `oa_status` is added with value `"unknown"` if not already set.

The script is **dry-run by default**.  Pass `--write` to actually
overwrite the source files.  Even with `--write`, it stages output
to `.scratch/migrate_to_ids_block/` first, validates that counts
and round-trip parsing are clean, and only then overwrites the
canonical files.

Run from the workspace root (Claude-research/):

    python code/data_management/migrate_to_ids_block.py             # dry-run
    python code/data_management/migrate_to_ids_block.py --diff       # dry-run + show diff
    python code/data_management/migrate_to_ids_block.py --write     # actually persist

Exit codes:
    0 — success (dry-run clean, or wet-run completed)
    1 — data issue (count mismatch, parse error, validation fail)
    2 — file not found
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections.abc import Iterable
from pathlib import Path


# ---------------------------------------------------------------------------
# Field handling
# ---------------------------------------------------------------------------

# Identifier fields that move from top-level into the nested ids block.
# The ids block ALWAYS has all six keys after migration, with null for
# missing values.  This uniform shape simplifies code reading the block.
_FLAT_ID_FIELDS = ("doi", "openalex_id", "pmid")
_NEW_ID_FIELDS  = ("pmcid", "s2_id", "arxiv_id")
_ALL_ID_FIELDS  = _FLAT_ID_FIELDS + _NEW_ID_FIELDS

# Field ordering for the migrated reference.  We preserve any existing
# key order then insert `ids`/`url`/`pub_id`/`oa_status` in a deterministic
# position so the resulting JSON is diff-friendly.
_PREFERRED_ORDER = (
    # bibliographic core
    "title", "authors", "year",
    "journal", "venue", "venue_type",
    "volume", "issue", "pages",
    # identity block (new)
    "ids",
    "url",
    "pub_id",
    "oa_status",
    # provenance and editorial
    "citation_string",
    "source", "confidence", "verified_on",
    # role vocabulary (required by schema)
    "roles",
)


def _normalise_id(val: object) -> str | None:
    """Coerce a raw ID field value to either a non-empty string or None."""
    if isinstance(val, str):
        s = val.strip()
        return s if s else None
    return None


def migrate_reference(ref: dict) -> dict:
    """Return a new reference dict with the post-2026-05-19 shape.

    Idempotent: if `ref` already carries an `ids` block, the values are
    preserved verbatim (no clobbering, no surprise nulls overwriting
    real data).  The function returns a new dict; the input is not
    mutated.
    """
    out: dict = {}

    # Build the ids block, preferring existing `ids` content over flat fields.
    existing_ids = ref.get("ids") if isinstance(ref.get("ids"), dict) else {}
    ids_block: dict[str, str | None] = {}
    for field in _ALL_ID_FIELDS:
        # New shape wins if it carries a value; otherwise look at the flat
        # field; otherwise None.
        nested_val = _normalise_id(existing_ids.get(field))
        if nested_val is not None:
            ids_block[field] = nested_val
        elif field in _FLAT_ID_FIELDS:
            ids_block[field] = _normalise_id(ref.get(field))
        else:
            ids_block[field] = None

    # Copy non-ID fields, dropping the flat ID fields and any existing
    # `ids` block (we just rebuilt it).
    for key, val in ref.items():
        if key in _FLAT_ID_FIELDS or key == "ids":
            continue
        if key in ("pub_id", "oa_status", "url"):
            # Handled explicitly below so they land in the preferred order.
            continue
        out[key] = val

    # Now place the special fields in the preferred order.
    final: dict = {}
    placed: set[str] = set()

    # Preserve any existing keys in their original order until we hit
    # a position where the new block belongs; insert there.
    for key in _PREFERRED_ORDER:
        if key == "ids":
            final["ids"] = ids_block
            placed.add("ids")
            continue
        if key == "url":
            url_val = ref.get("url")
            final["url"] = url_val if isinstance(url_val, str) and url_val else None
            placed.add("url")
            continue
        if key == "pub_id":
            pub_val = ref.get("pub_id")
            final["pub_id"] = pub_val if isinstance(pub_val, str) and pub_val else None
            placed.add("pub_id")
            continue
        if key == "oa_status":
            status_val = ref.get("oa_status")
            if isinstance(status_val, str) and status_val:
                final["oa_status"] = status_val
            else:
                final["oa_status"] = "unknown"
            placed.add("oa_status")
            continue
        if key in out:
            final[key] = out[key]
            placed.add(key)

    # Any leftover keys we didn't anticipate (custom fields, etc.) get
    # appended at the end so nothing is lost.
    for key, val in out.items():
        if key not in placed:
            final[key] = val

    return final


def migrate_processes(data: dict) -> tuple[dict, int]:
    """Migrate all references in a process_details.json payload.

    Returns (new_data, n_refs_migrated).
    """
    new_data = dict(data)
    new_processes = []
    n_refs = 0
    for proc in data.get("processes", []):
        new_proc = dict(proc)
        if "references" in new_proc and new_proc["references"] is not None:
            new_refs = [migrate_reference(r) for r in new_proc["references"]]
            new_proc["references"] = new_refs
            n_refs += len(new_refs)
        new_processes.append(new_proc)
    new_data["processes"] = new_processes
    return new_data, n_refs


def migrate_tasks(data: list) -> tuple[list, int]:
    """Migrate all references in a task_details.json payload.

    task_details.json is a bare array of task objects; references live
    on each one.
    """
    new_data: list = []
    n_refs = 0
    for task in data:
        new_task = dict(task)
        if "references" in new_task and new_task["references"] is not None:
            new_refs = [migrate_reference(r) for r in new_task["references"]]
            new_task["references"] = new_refs
            n_refs += len(new_refs)
        new_data.append(new_task)
    return new_data, n_refs


# ---------------------------------------------------------------------------
# Diff / round-trip verification
# ---------------------------------------------------------------------------

def collect_all_refs(data: object) -> list[dict]:
    """Flatten every reference in a catalog payload into a single list."""
    refs: list[dict] = []
    if isinstance(data, dict) and "processes" in data:
        for p in data["processes"]:
            refs.extend(p.get("references") or [])
    elif isinstance(data, list):
        for t in data:
            refs.extend(t.get("references") or [])
    return refs


def compare_refs_pre_post(
    pre_refs: list[dict],
    post_refs: list[dict],
) -> list[str]:
    """Verify no data was lost during migration.

    For every pre-migration reference, the corresponding post-migration
    reference must:
      - carry the same DOI / PMID / OpenAlex ID (now under `ids`)
      - preserve every non-ID field unchanged

    Returns a list of problem descriptions; empty list means clean.
    """
    problems: list[str] = []
    if len(pre_refs) != len(post_refs):
        problems.append(
            f"reference count changed: {len(pre_refs)} → {len(post_refs)}"
        )
        return problems

    for i, (pre, post) in enumerate(zip(pre_refs, post_refs)):
        # ID fields must round-trip exactly.
        for fld in _FLAT_ID_FIELDS:
            pre_val = _normalise_id(pre.get(fld))
            post_val = _normalise_id((post.get("ids") or {}).get(fld))
            if pre_val != post_val:
                problems.append(
                    f"ref[{i}] {fld}: {pre_val!r} → {post_val!r}"
                )

        # Non-ID fields must be preserved verbatim.
        skip = set(_FLAT_ID_FIELDS) | {"ids", "pub_id", "oa_status"}
        for key, val in pre.items():
            if key in skip:
                continue
            if post.get(key) != val:
                problems.append(
                    f"ref[{i}] {key}: value changed during migration"
                )

    return problems


# ---------------------------------------------------------------------------
# Diff display (for --diff)
# ---------------------------------------------------------------------------

def show_first_diff(pre_refs: list[dict], post_refs: list[dict]) -> str:
    """Pretty-print the first pre/post pair for human review."""
    if not pre_refs or not post_refs:
        return "(no references to show)"
    pre = json.dumps(pre_refs[0], indent=2, ensure_ascii=False)
    post = json.dumps(post_refs[0], indent=2, ensure_ascii=False)
    return f"--- BEFORE (first ref) ---\n{pre}\n\n--- AFTER (first ref) ---\n{post}"


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--workspace",
        default=".",
        help="Workspace root (default: current directory).",
    )
    p.add_argument(
        "--processes",
        default="process_details.json",
        help="Catalog file relative to workspace.",
    )
    p.add_argument(
        "--tasks",
        default="task_details.json",
        help="Task file relative to workspace.",
    )
    p.add_argument(
        "--scratch-dir",
        default=".scratch/migrate_to_ids_block",
        help="Where to stage migrated output before final write.",
    )
    p.add_argument(
        "--write",
        action="store_true",
        help="Overwrite the source files with migrated output. "
             "Default is dry-run.",
    )
    p.add_argument(
        "--diff",
        action="store_true",
        help="Print BEFORE/AFTER for the first reference in each file.",
    )
    return p.parse_args()


def write_staged(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")


def main() -> int:
    args = parse_args()
    ws = Path(args.workspace).resolve()
    src_proc = ws / args.processes
    src_tasks = ws / args.tasks
    scratch = ws / args.scratch_dir

    for src in (src_proc, src_tasks):
        if not src.exists():
            print(f"ERROR: not found: {src}", file=sys.stderr)
            return 2

    # ---- Load
    with src_proc.open("r", encoding="utf-8") as f:
        proc_pre = json.load(f)
    with src_tasks.open("r", encoding="utf-8") as f:
        tasks_pre = json.load(f)

    # ---- Migrate
    proc_post, n_proc_refs = migrate_processes(proc_pre)
    tasks_post, n_task_refs = migrate_tasks(tasks_pre)

    # ---- Verify
    pre_refs  = collect_all_refs(proc_pre) + collect_all_refs(tasks_pre)
    post_refs = collect_all_refs(proc_post) + collect_all_refs(tasks_post)

    print(f"references seen:")
    print(f"  in {src_proc.name}:  {n_proc_refs}")
    print(f"  in {src_tasks.name}: {n_task_refs}")
    print(f"  total: {len(pre_refs)} → {len(post_refs)}")

    problems = compare_refs_pre_post(pre_refs, post_refs)
    if problems:
        print(f"\nFAIL: {len(problems)} problem(s) detected:", file=sys.stderr)
        for p in problems[:20]:
            print(f"  - {p}", file=sys.stderr)
        if len(problems) > 20:
            print(f"  ... and {len(problems) - 20} more", file=sys.stderr)
        return 1
    print("verification: ok (every pre ref round-trips to a post ref)")

    # ---- Stage to .scratch
    staged_proc  = scratch / src_proc.name
    staged_tasks = scratch / src_tasks.name
    write_staged(staged_proc, proc_post)
    write_staged(staged_tasks, tasks_post)
    print(f"staged: {staged_proc.relative_to(ws)}")
    print(f"staged: {staged_tasks.relative_to(ws)}")

    # ---- Optional: show a diff for human review
    if args.diff:
        print()
        print("=" * 72)
        print(f"DIFF — {src_proc.name}")
        print("=" * 72)
        print(show_first_diff(
            collect_all_refs(proc_pre),
            collect_all_refs(proc_post),
        ))
        print()
        print("=" * 72)
        print(f"DIFF — {src_tasks.name}")
        print("=" * 72)
        print(show_first_diff(
            collect_all_refs(tasks_pre),
            collect_all_refs(tasks_post),
        ))

    # ---- Persist (only with --write)
    if args.write:
        shutil.copyfile(staged_proc,  src_proc)
        shutil.copyfile(staged_tasks, src_tasks)
        print()
        print(f"wrote: {src_proc.relative_to(ws)}")
        print(f"wrote: {src_tasks.relative_to(ws)}")
    else:
        print()
        print("dry-run complete; pass --write to overwrite the catalog files.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
