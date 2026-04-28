#!/usr/bin/env python3
"""
Validate process_details.json structural integrity.

Two layers of checking:

1. **Shape** — types, required keys, enums, id patterns. Defined
   declaratively in `schemas/process_details.schema.json` (JSON Schema
   draft-07) so the same shape applies in editor-time validation
   (VS Code) and in this script. Requires the `jsonschema` package.

2. **Cross-checks** — referential integrity (`category_id` resolves to
   a defined category), header-vs-actual counts, ID uniqueness, alias
   name uniqueness within a process, `task_count` consistency. These
   span multiple parts of the document and don't fit JSON Schema
   cleanly, so they live in Python here.

Plus byte-level checks (no null bytes, no trailing junk past the
closing brace) that are language-independent.

Run from the workspace root:

    python code/data_management/validate_catalog.py

Returns 0 if clean, 1 on any data issue, 2 if the file isn't where
expected, 3 if the schema can't be loaded or `jsonschema` isn't
installed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Byte-level
# ---------------------------------------------------------------------------


def check_byte_level(path: Path) -> list[str]:
    """No null bytes; file must end at a closing brace (optionally + newline)."""
    errors: list[str] = []
    raw = path.read_bytes()

    null_count = raw.count(b"\x00")
    if null_count:
        errors.append(f"file contains {null_count} null byte(s)")

    # rstrip strips ASCII whitespace only, not null bytes — so this catches
    # trailing junk including null sequences past the closing brace.
    stripped = raw.rstrip()
    if not stripped.endswith(b"}"):
        tail = raw[-30:].decode("utf-8", errors="replace")
        errors.append(
            f"file does not end at a closing brace; last 30 chars: {tail!r}"
        )

    return errors


# ---------------------------------------------------------------------------
# Schema validation (delegated to jsonschema)
# ---------------------------------------------------------------------------


def load_schema(schema_path: Path) -> dict:
    with schema_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def check_schema(data: dict, schema: dict) -> list[str]:
    """Run JSON Schema validation, returning a flat list of error messages."""
    try:
        from jsonschema import Draft7Validator
    except ImportError as e:
        raise SystemExit(
            "ERROR: the `jsonschema` package is required.\n"
            "Install it with: pip install jsonschema"
        ) from e

    validator = Draft7Validator(schema)
    errors = []
    for err in validator.iter_errors(data):
        path = "/".join(str(p) for p in err.absolute_path) or "<root>"
        errors.append(f"{path}: {err.message}")
    return errors


# ---------------------------------------------------------------------------
# Cross-checks (things the schema can't express)
# ---------------------------------------------------------------------------


def check_header_counts(data: dict) -> list[str]:
    errors: list[str] = []
    n_cats = len(data.get("categories", []))
    n_procs = len(data.get("processes", []))
    if data.get("total_categories") != n_cats:
        errors.append(
            f"total_categories header ({data.get('total_categories')}) "
            f"!= actual ({n_cats})"
        )
    if data.get("total_processes") != n_procs:
        errors.append(
            f"total_processes header ({data.get('total_processes')}) "
            f"!= actual ({n_procs})"
        )
    return errors


def check_category_uniqueness(data: dict) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for i, c in enumerate(data.get("categories", [])):
        cid = c.get("category_id")
        if cid in seen:
            errors.append(f"categories[{i}]: duplicate category_id {cid!r}")
        if cid is not None:
            seen.add(cid)
    return errors


def check_process_cross_refs(data: dict) -> list[str]:
    """Process IDs/names unique; category_id resolves; alias names unique
    within a process; task_count matches."""
    errors: list[str] = []
    procs = data.get("processes", [])
    valid_cat_ids = {
        c["category_id"]
        for c in data.get("categories", [])
        if "category_id" in c
    }

    seen_ids: set[str] = set()
    seen_names: set[str] = set()
    actual_cat_counts: dict[str, int] = {}

    for i, p in enumerate(procs):
        ctx = f"processes[{i}] {p.get('process_name', '?')!r}"

        pid = p.get("process_id")
        if pid in seen_ids:
            errors.append(f"{ctx}: duplicate process_id {pid!r}")
        if pid is not None:
            seen_ids.add(pid)

        pname = p.get("process_name")
        if pname in seen_names:
            errors.append(f"{ctx}: duplicate process_name {pname!r}")
        if pname is not None:
            seen_names.add(pname)

        cid = p.get("category_id")
        if cid is not None:
            if cid not in valid_cat_ids:
                errors.append(
                    f"{ctx}: category_id {cid!r} not defined in categories"
                )
            else:
                actual_cat_counts[cid] = actual_cat_counts.get(cid, 0) + 1

        # Alias name uniqueness within this process.
        seen_alias_names: set[str] = set()
        for j, a in enumerate(p.get("aliases", []) or []):
            name = a.get("name") if isinstance(a, dict) else None
            if name is None:
                continue
            if name in seen_alias_names:
                errors.append(f"{ctx} aliases[{j}]: duplicate alias name {name!r}")
            seen_alias_names.add(name)

        # tasks/task_count consistency. tasks[] is derived from
        # task_details.json; mismatch usually means sync is overdue.
        if "tasks" in p and "task_count" in p:
            if p["task_count"] != len(p["tasks"]):
                errors.append(
                    f"{ctx}: task_count ({p['task_count']}) != "
                    f"len(tasks) ({len(p['tasks'])}) — "
                    f"run sync_process_details_tasks.py"
                )

    # Per-category declared count vs. actual.
    for c in data.get("categories", []):
        cid = c.get("category_id")
        declared = c.get("process_count")
        actual = actual_cat_counts.get(cid, 0)
        if declared != actual:
            errors.append(
                f"category {cid!r}: process_count ({declared}) != actual ({actual})"
            )

    return errors


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--workspace",
        default=".",
        help="Workspace root (default: current directory)",
    )
    p.add_argument(
        "--file",
        default="process_details.json",
        help="Catalog file relative to workspace (default: process_details.json)",
    )
    p.add_argument(
        "--schema",
        default="schemas/process_details.schema.json",
        help="JSON Schema file relative to workspace.",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    ws = Path(args.workspace).resolve()
    src = ws / args.file
    schema_path = ws / args.schema

    if not src.exists():
        print(f"ERROR: not found: {src}", file=sys.stderr)
        return 2
    if not schema_path.exists():
        print(f"ERROR: schema not found: {schema_path}", file=sys.stderr)
        return 3

    errors: list[str] = []

    # 1. Byte-level
    errors.extend(check_byte_level(src))

    # 2. Parse JSON
    try:
        with src.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"FAIL: {src.name} does not parse as JSON", file=sys.stderr)
        print(
            f"  {e.msg} at line {e.lineno}, column {e.colno} (char {e.pos})",
            file=sys.stderr,
        )
        for msg in errors:
            print(f"  - {msg}", file=sys.stderr)
        return 1

    # 3. Schema (shape, types, enums)
    schema = load_schema(schema_path)
    errors.extend(check_schema(data, schema))

    # 4. Cross-checks
    errors.extend(check_header_counts(data))
    errors.extend(check_category_uniqueness(data))
    errors.extend(check_process_cross_refs(data))

    if errors:
        plural = "s" if len(errors) > 1 else ""
        print(f"FAIL: {src.name} ({len(errors)} issue{plural}):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    n_cats = len(data["categories"])
    n_procs = len(data["processes"])
    procs_with_aliases = sum(1 for p in data["processes"] if p.get("aliases"))
    n_aliases = sum(len(p.get("aliases", [])) for p in data["processes"])
    n_refs = sum(len(p.get("references", [])) for p in data["processes"])

    print(f"OK: {src.name}")
    print(f"  schema:     {schema_path.name}")
    print(f"  categories: {n_cats}")
    print(f"  processes:  {n_procs}")
    print(f"  aliases:    {n_aliases} across {procs_with_aliases} processes")
    print(f"  references: {n_refs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
