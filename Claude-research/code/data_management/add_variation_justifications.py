#!/usr/bin/env python3
"""
add_variation_justifications.py

Reads the KEEP reasons from .status/task_variation_audit.md and adds them
as a 'justification' field to each matching variation object in task_details.json.

Only KEEP rows are processed. DROP rows are skipped — those variations will
be removed by apply_variation_audit.py, so they do not need justifications.

If a variation already has a 'justification' field it is overwritten, making
this script safe to re-run.

USAGE
-----
    python3 outputs/add_variation_justifications.py

Expected output:
    772 justifications added (one per surviving variation)
    0 audit KEEP entries with no matching variation in task_details.json
    0 task_details.json variations with no matching audit KEEP entry
      (the latter group are the 7 DROPs, which is expected)
"""

import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
REPO_ROOT  = SCRIPT_DIR.parent

TASK_DETAILS = REPO_ROOT / "task_details.json"
AUDIT_FILE   = REPO_ROOT / ".status" / "task_variation_audit.md"


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_audit(audit_path: Path) -> dict[str, dict[str, str]]:
    """
    Parse the audit markdown and return:
        {hedtsk_id: {variation_name: justification_text}}

    Only KEEP rows are included. DROP rows are silently skipped.
    """
    text = audit_path.read_bytes().rstrip(b"\x00").decode("utf-8", errors="replace")

    # Match section headers: ### N. Task Name (`hedtsk_id`)
    header_re = re.compile(r"^###\s+\d+\.\s+.+?\s+\(`(hedtsk_[^`]+)`\)")

    result: dict[str, dict[str, str]] = {}
    current_id: str | None = None

    for line in text.splitlines():
        # New task section?
        hm = header_re.match(line)
        if hm:
            current_id = hm.group(1)
            result.setdefault(current_id, {})
            continue

        if current_id is None or not line.startswith("|"):
            continue

        # Split pipe-delimited table row into columns.
        # cols[0] = '' (before first |), cols[-1] = '' (after last |)
        cols = [c.strip() for c in line.split("|")]
        if len(cols) < 6:
            continue

        # Skip the header row (| # | Variation | …) and separator row (|---|…)
        if cols[1] in ("#", "") or cols[1].startswith("-"):
            continue

        verdict = cols[3].strip("*").strip()   # handles both KEEP and **DROP**
        if verdict != "KEEP":
            continue

        var_name = cols[2]
        # Reason is column 5; join any extra columns in case '|' appeared in text
        reason = " | ".join(c for c in cols[5:-1] if c).strip()

        if var_name and reason:
            result[current_id][var_name] = reason

    return result


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

def apply_justifications(
    tasks: list[dict],
    audit: dict[str, dict[str, str]],
) -> tuple[int, list[str], list[str]]:
    """
    Add 'justification' field to each variation whose name appears as a
    KEEP entry in the audit for that task.

    Returns:
        (total_added, unmatched_audit_entries, json_vars_without_audit_entry)
    """
    id_to_task = {t["hedtsk_id"]: t for t in tasks}

    total_added = 0
    unmatched_audit: list[str] = []      # audit KEEP names not found in JSON
    no_audit_entry: list[str] = []       # JSON variation names with no audit KEEP entry

    for hedtsk_id, keep_map in audit.items():
        task = id_to_task.get(hedtsk_id)
        if task is None:
            for vname in keep_map:
                unmatched_audit.append(f"{hedtsk_id} / {vname}")
            continue

        # Build a case-insensitive lookup for variation name → variation dict
        # (exact match preferred; fallback to casefold)
        var_by_name: dict[str, dict] = {v["name"]: v for v in task.get("variations", [])}
        var_by_cf:   dict[str, dict] = {v["name"].casefold(): v for v in task.get("variations", [])}

        for audit_name, justification in keep_map.items():
            var = var_by_name.get(audit_name) or var_by_cf.get(audit_name.casefold())
            if var is None:
                unmatched_audit.append(f"{hedtsk_id} / {audit_name!r}")
            else:
                var["justification"] = justification
                total_added += 1

    # Find JSON variations with no audit KEEP entry (expected: the 7 DROPs)
    for task in tasks:
        keep_map = audit.get(task["hedtsk_id"], {})
        for var in task.get("variations", []):
            if var["name"] not in keep_map:
                no_audit_entry.append(f"{task['hedtsk_id']} / {var['name']!r}")

    return total_added, unmatched_audit, no_audit_entry


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=== Add Variation Justifications ===\n")

    # Load
    raw   = TASK_DETAILS.read_bytes().rstrip(b"\x00")
    tasks = json.loads(raw)
    total_vars = sum(len(t.get("variations", [])) for t in tasks)
    print(f"Loaded {len(tasks)} tasks, {total_vars} variations from task_details.json")

    # Parse audit
    audit = parse_audit(AUDIT_FILE)
    total_keep = sum(len(v) for v in audit.values())
    print(f"Parsed audit: {len(audit)} tasks, {total_keep} KEEP entries")

    # Apply
    total_added, unmatched_audit, no_audit_entry = apply_justifications(tasks, audit)

    # Report
    print(f"\n--- Results ---")
    print(f"Justifications added : {total_added}")

    if unmatched_audit:
        print(f"\nWARNING — audit KEEP entries with no matching variation in JSON ({len(unmatched_audit)}):")
        for entry in unmatched_audit:
            print(f"  {entry}")
    else:
        print("OK: all audit KEEP entries matched a variation in task_details.json")

    if no_audit_entry:
        print(f"\nVariations in JSON with no audit KEEP entry ({len(no_audit_entry)}) — expected to be the DROP list:")
        for entry in no_audit_entry:
            print(f"  {entry}")
    else:
        print("OK: every JSON variation has an audit KEEP entry")

    # Sanity: expected 772 KEEPs (779 total - 7 DROPs)
    expected_keep = 772
    if total_added != expected_keep:
        print(
            f"\nWARNING: added {total_added} justifications but expected {expected_keep}. "
            "Investigate before treating output as final."
        )
        sys.exit(1)
    else:
        print(f"\nOK: exactly {total_added} justifications added (expected {expected_keep})")

    # Write backup then updated file
    backup = TASK_DETAILS.with_suffix(".pre_justifications_backup.json")
    backup.write_bytes(raw)
    print(f"Backup written: {backup.name}")

    TASK_DETAILS.write_text(
        json.dumps(tasks, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Updated task_details.json written")


if __name__ == "__main__":
    main()
