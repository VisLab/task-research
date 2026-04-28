#!/usr/bin/env python3
"""
Validate task_details.json structural integrity.

Mirrors validate_catalog.py but for the task catalog. The shape check
is delegated to schemas/task_details.schema.json (JSON Schema draft-07);
this script adds byte-level checks and a small set of cross-checks
that JSON Schema can't express.

Cross-checks performed:
  - hedtsk_id uniqueness across all tasks
  - canonical_name uniqueness across all tasks
  - hed_process_ids resolve to actual processes in process_details.json
    (skipped if process_details.json is unreadable; reported as a warning)

Run from the workspace root:

    python code/data_management/validate_tasks.py

Returns 0 if clean, 1 on any data issue, 2 if a file isn't found,
3 if `jsonschema` isn't installed.
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
    """No null bytes; file ends at a closing bracket (top-level is an array)."""
    errors: list[str] = []
    raw = path.read_bytes()

    null_count = raw.count(b"\x00")
    if null_count:
        errors.append(f"file contains {null_count} null byte(s)")

    stripped = raw.rstrip()
    if not stripped.endswith(b"]"):
        tail = raw[-30:].decode("utf-8", errors="replace")
        errors.append(
            f"file does not end at a closing bracket; last 30 chars: {tail!r}"
        )

    return errors


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------


def check_schema(data, schema: dict) -> list[str]:
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
# Cross-checks
# ---------------------------------------------------------------------------


def check_uniqueness(tasks: list) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    seen_names: set[str] = set()
    for i, t in enumerate(tasks):
        ctx = f"tasks[{i}] {t.get('canonical_name', '?')!r}"
        tid = t.get("hedtsk_id")
        if tid in seen_ids:
            errors.append(f"{ctx}: duplicate hedtsk_id {tid!r}")
        if tid is not None:
            seen_ids.add(tid)
        name = t.get("canonical_name")
        if name in seen_names:
            errors.append(f"{ctx}: duplicate canonical_name {name!r}")
        if name is not None:
            seen_names.add(name)
    return errors


def check_process_id_refs(tasks: list, process_ids: set[str] | None) -> list[str]:
    """Each hed_process_ids entry should resolve to a defined process."""
    if process_ids is None:
        return []
    errors: list[str] = []
    for i, t in enumerate(tasks):
        ctx = f"tasks[{i}] {t.get('canonical_name', '?')!r}"
        for j, pid in enumerate(t.get("hed_process_ids", []) or []):
            if pid not in process_ids:
                errors.append(
                    f"{ctx} hed_process_ids[{j}]: {pid!r} not in process_details.json"
                )
    return errors


def load_process_ids(path: Path) -> set[str] | None:
    """Return the set of process_id values from process_details.json,
    or None if the file is missing or unreadable. Don't fail this script
    just because process_details.json has its own issues — that's a
    separate concern."""
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
    return {
        p["process_id"]
        for p in data.get("processes", [])
        if isinstance(p, dict) and "process_id" in p
    }


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workspace", default=".", help="Workspace root (default: cwd)")
    p.add_argument(
        "--file",
        default="task_details.json",
        help="Catalog file relative to workspace.",
    )
    p.add_argument(
        "--schema",
        default="schemas/task_details.schema.json",
        help="JSON Schema file relative to workspace.",
    )
    p.add_argument(
        "--processes",
        default="process_details.json",
        help=(
            "process_details.json path for hed_process_ids cross-check "
            "(skipped if unreadable)."
        ),
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    ws = Path(args.workspace).resolve()
    src = ws / args.file
    schema_path = ws / args.schema
    processes_path = ws / args.processes

    if not src.exists():
        print(f"ERROR: not found: {src}", file=sys.stderr)
        return 2
    if not schema_path.exists():
        print(f"ERROR: schema not found: {schema_path}", file=sys.stderr)
        return 2

    errors: list[str] = []

    # 1. Byte-level
    errors.extend(check_byte_level(src))

    # 2. Parse
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

    # 3. Schema
    with schema_path.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    errors.extend(check_schema(data, schema))

    # 4. Cross-checks (only if data is the expected list shape).
    if isinstance(data, list):
        errors.extend(check_uniqueness(data))
        process_ids = load_process_ids(processes_path)
        errors.extend(check_process_id_refs(data, process_ids))
        process_ref_skipped = process_ids is None
    else:
        process_ref_skipped = True

    if errors:
        plural = "s" if len(errors) > 1 else ""
        print(f"FAIL: {src.name} ({len(errors)} issue{plural}):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    n_tasks = len(data) if isinstance(data, list) else 0
    n_refs = (
        sum(len(t.get("references", [])) for t in data)
        if isinstance(data, list)
        else 0
    )

    print(f"OK: {src.name}")
    print(f"  schema:     {schema_path.name}")
    print(f"  tasks:      {n_tasks}")
    print(f"  references: {n_refs}")
    if process_ref_skipped:
        print(
            "  note: hed_process_ids cross-check skipped "
            "(process_details.json missing or unreadable)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
