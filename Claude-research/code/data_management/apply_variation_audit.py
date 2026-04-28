#!/usr/bin/env python3
"""
apply_variation_audit.py

Applies the KEEP/DROP verdicts from .status/task_variation_audit.md to
task_details.json by removing all variations marked DROP, and applies any
alias additions specified in ALIAS_ADDITIONS below.

Strategy:
  1. Parse the audit file to extract (task_name → list of DROP variation names).
  2. Match audit task names to task_details.json canonical_names
     (normalized: lowercase, strip parentheticals, strip "task"/"test" suffix).
     Falls back to substring matching if exact normalized match fails.
  3. Remove DROP variations from each task's variations array.
  4. Apply alias additions: for each (hedtsk_id, alias) pair in ALIAS_ADDITIONS,
     add the alias to that task's aliases array if not already present.
  5. Write updated task_details.json (with backup).
  6. Print a detailed report.
"""

import json
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
REPO_ROOT = SCRIPT_DIR.parent

TASK_DETAILS = REPO_ROOT / "task_details.json"
AUDIT_FILE = REPO_ROOT / ".status" / "task_variation_audit.md"

# Variations dropped and simultaneously promoted to alias entries.
# Each entry: (hedtsk_id, alias_string_to_add)
# These are applied after the DROP pass.
ALIAS_ADDITIONS = [
    ("hedtsk_attention_network", "Clinical Screening ANT"),
]


def normalize_name(name):
    """Normalize a task name for fuzzy matching."""
    name = re.sub(r"\s*\([^)]*\)\s*", " ", name)   # strip parentheticals
    name = re.sub(r"\s+", " ", name.lower().strip()) # lowercase + collapse ws
    name = re.sub(r"\s+(task|test)$", "", name)      # strip trailing task/test
    return name


def parse_audit(audit_path):
    """
    Parse task_variation_audit.md and return:
      dict: audit_task_name → list of DROP variation names

    Handles both plain '| DROP |' and bold '| **DROP** |' in table rows.
    """
    text = audit_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # Task section headers: ### N. Canonical Name (`hedtsk_id`)
    task_header_re = re.compile(r"^###\s+\d+\.\s+(.+?)(?:\s+\(`hedtsk_[^`]+`\))?$")
    # DROP table rows — accept both '| DROP |' and '| **DROP** |'
    drop_row_re = re.compile(
        r"^\|\s*\d+\s*\|\s*(.+?)\s*\|\s*\*{0,2}DROP\*{0,2}\s*\|"
    )

    drops_by_task = {}
    current_task = None

    for line in lines:
        hm = task_header_re.match(line)
        if hm:
            current_task = hm.group(1).strip()
            drops_by_task.setdefault(current_task, [])
            continue

        if current_task:
            dm = drop_row_re.match(line)
            if dm:
                drops_by_task[current_task].append(dm.group(1).strip())

    return {k: v for k, v in drops_by_task.items() if v}


def build_match_map(audit_tasks, json_tasks):
    """
    Match audit task names to task_details.json canonical_names.
    Returns (dict: audit_task_name → hedtsk_id, list of unmatched names).
    """
    norm_to_id = {normalize_name(t["canonical_name"]): t["hedtsk_id"] for t in json_tasks}

    match_map = {}
    unmatched = []

    for audit_name in audit_tasks:
        norm = normalize_name(audit_name)
        if norm in norm_to_id:
            match_map[audit_name] = norm_to_id[norm]
        else:
            # Substring fallback
            found = next(
                (tid for jnorm, tid in norm_to_id.items()
                 if jnorm in norm or norm in jnorm),
                None,
            )
            if found:
                match_map[audit_name] = found
            else:
                unmatched.append(audit_name)

    return match_map, unmatched


def apply_drops(tasks, drops_by_task, match_map):
    """
    Remove DROP variations from tasks.
    Returns (report lines, total_removed, total_not_found).
    """
    id_to_idx = {t["hedtsk_id"]: i for i, t in enumerate(tasks)}
    report = []
    total_removed = 0
    total_not_found = 0

    for audit_name, drop_names in drops_by_task.items():
        if audit_name not in match_map:
            report.append(f"SKIP (no match): {audit_name}")
            continue

        task = tasks[id_to_idx[match_map[audit_name]]]
        existing = {v["name"] for v in task.get("variations", [])}
        removed   = [n for n in drop_names if n in existing]
        not_found = [n for n in drop_names if n not in existing]

        if removed:
            task["variations"] = [
                v for v in task["variations"] if v["name"] not in set(removed)
            ]

        total_removed   += len(removed)
        total_not_found += len(not_found)

        entry = (
            f"{task['canonical_name']} ({task['hedtsk_id']}): "
            f"{len(existing)} → {len(task.get('variations', []))}"
        )
        if removed:
            entry += f"  [dropped: {removed}]"
        if not_found:
            entry += f"  [NOT FOUND IN JSON: {not_found}]"
        report.append(entry)

    return report, total_removed, total_not_found


def apply_alias_additions(tasks, alias_additions):
    """
    For each (hedtsk_id, alias) pair, add alias to that task's aliases list
    if it is not already present.
    Returns a list of report lines.
    """
    id_to_task = {t["hedtsk_id"]: t for t in tasks}
    report = []

    for hedtsk_id, alias in alias_additions:
        if hedtsk_id not in id_to_task:
            report.append(f"ALIAS SKIP (task not found): {hedtsk_id}")
            continue

        task = id_to_task[hedtsk_id]
        aliases = task.setdefault("aliases", [])

        if alias in aliases:
            report.append(
                f"ALIAS already present: '{alias}' in {task['canonical_name']}"
            )
        else:
            aliases.append(alias)
            report.append(
                f"ALIAS added: '{alias}' → {task['canonical_name']} ({hedtsk_id})"
            )

    return report


def main():
    print("=== Variation Audit Application ===\n")

    tasks = json.loads(TASK_DETAILS.read_text(encoding="utf-8"))
    print(f"Loaded {len(tasks)} tasks from task_details.json")

    total_vars_before = sum(len(t.get("variations", [])) for t in tasks)
    print(f"Total variations before: {total_vars_before}")

    # --- Parse audit ---
    drops_by_task = parse_audit(AUDIT_FILE)
    total_drops = sum(len(v) for v in drops_by_task.values())
    print(f"Parsed audit: {len(drops_by_task)} tasks with DROPs, {total_drops} total DROP verdicts")

    # --- Match task names ---
    match_map, unmatched = build_match_map(drops_by_task, tasks)
    print(f"Matched {len(match_map)} audit task names to JSON tasks")
    if unmatched:
        print(f"UNMATCHED audit task names: {unmatched}")
        print("Aborting — resolve unmatched names before applying.")
        return

    # --- Apply drops ---
    drop_report, total_removed, total_not_found = apply_drops(
        tasks, drops_by_task, match_map
    )

    total_vars_after = sum(len(t.get("variations", [])) for t in tasks)

    print(f"\n--- Drop results ---")
    print(f"Variations removed : {total_removed}")
    print(f"Names not in JSON  : {total_not_found}")
    print(f"Total variations   : {total_vars_before} → {total_vars_after}")
    print(f"\n--- Per-task detail ---")
    for line in drop_report:
        print(f"  {line}")

    # --- Apply alias additions ---
    print(f"\n--- Alias additions ---")
    alias_report = apply_alias_additions(tasks, ALIAS_ADDITIONS)
    for line in alias_report:
        print(f"  {line}")

    # --- Sanity checks ---
    print(f"\n--- Sanity checks ---")
    expected_removed = 7
    if total_removed != expected_removed:
        print(
            f"WARNING: removed {total_removed} variations but expected {expected_removed}. "
            "Investigate before treating output as authoritative."
        )
    else:
        print(f"OK: removed exactly {total_removed} variations (expected {expected_removed})")

    if total_not_found > 0:
        print(
            f"WARNING: {total_not_found} DROP variation name(s) were not found in "
            "task_details.json — they may have already been removed."
        )

    expected_aliases = len(ALIAS_ADDITIONS)
    aliases_added = sum(1 for l in alias_report if l.startswith("ALIAS added"))
    print(
        f"OK: {aliases_added}/{expected_aliases} alias addition(s) applied"
        if aliases_added == expected_aliases
        else f"WARNING: only {aliases_added}/{expected_aliases} alias addition(s) applied"
    )

    # --- Write output ---
    backup = TASK_DETAILS.with_suffix(".pre_2026_04_21_audit_backup.json")
    backup.write_text(TASK_DETAILS.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"\nBackup written: {backup.name}")

    TASK_DETAILS.write_text(
        json.dumps(tasks, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"Updated task_details.json written "
        f"({total_vars_after} variations, {aliases_added} alias(es) added)"
    )


if __name__ == "__main__":
    main()
