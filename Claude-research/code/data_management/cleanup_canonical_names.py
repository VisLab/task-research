#!/usr/bin/env python3
"""
cleanup_canonical_names.py

Removes parentheticals and spaced slashes from canonical_name fields in
task_details.json. Also cleans aliases that contain parentheticals.

This is a text-based processor (regex on lines) — it doesn't need to parse
the full JSON, so it works even on a truncated file.

Changes made:
  1. canonical_name: "X (Y)" → "X"
  2. canonical_name: "A / B Task" → "A Task"  (spaced slash)
  3. Aliases like "X (Y)" → "X" (if the parenthetical abbreviation is
     already a separate alias entry)

Does NOT touch:
  - Unspaced "/" (Go/No-Go, Old/New, etc.) — these are compound terms
  - Any field other than canonical_name and aliases
"""

import re
import sys
import json
from pathlib import Path

SLASH_FIXES = {
    "Face Processing / FFA Localizer Task": "Face Processing Task",
    "False Belief / Theory of Mind Task": "False Belief Task",
    "Instrumental / Operant Conditioning Task": "Instrumental Conditioning Task",
    "Sentence Comprehension / Garden-Path Task": "Sentence Comprehension Task",
    "Task Switching / Set Shifting Task": "Task Switching Task",
}


def clean_canonical_name(name: str) -> tuple[str, list[str]]:
    """Return (cleaned_name, list_of_removed_parts)."""
    removed = []

    # Step 1: Hardcoded spaced-slash fixes (only 5 cases, each needs specific logic)
    if name in SLASH_FIXES:
        name = SLASH_FIXES[name]

    # Step 2: Remove parentheticals
    # "Balloon Analog Risk Task (BART)" → "Balloon Analog Risk Task"
    paren_match = re.search(r'\s*\(([^)]+)\)\s*$', name)
    if paren_match:
        paren_content = paren_match.group(1).strip()
        name = name[:paren_match.start()].strip()
        # Split on " / " within parenthetical (e.g., "DSST / SDMT")
        parts = [p.strip() for p in paren_content.split(' / ')]
        removed.extend(parts)

    return name, removed


def clean_alias(alias: str) -> str:
    """Remove parentheticals from an alias string.
    "Attention Network Test (ANT)" → "Attention Network Test"
    """
    cleaned = re.sub(r'\s*\([^)]+\)\s*$', '', alias).strip()
    return cleaned


def process_file(input_path: str, output_path: str):
    """Process task_details.json line by line."""

    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse as JSON for precise manipulation
    try:
        tasks = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"ERROR: Could not parse JSON: {e}", file=sys.stderr)
        print("Falling back to regex-based processing...", file=sys.stderr)
        process_file_regex(input_path, output_path)
        return

    changes_log = []

    for task in tasks:
        old_name = task.get('canonical_name', '')
        new_name, removed = clean_canonical_name(old_name)

        if new_name != old_name:
            changes_log.append(f"  canonical_name: '{old_name}' → '{new_name}'")
            task['canonical_name'] = new_name

        # Clean aliases that contain parentheticals
        aliases = task.get('aliases', [])
        new_aliases = []
        alias_changes = []
        for alias in aliases:
            cleaned = clean_alias(alias)
            if cleaned != alias:
                alias_changes.append(f"    alias: '{alias}' → '{cleaned}'")
            new_aliases.append(cleaned)

        # Deduplicate aliases (case-sensitive)
        seen = set()
        deduped = []
        for a in new_aliases:
            if a not in seen:
                seen.add(a)
                deduped.append(a)

        if deduped != aliases:
            task['aliases'] = deduped
            for ac in alias_changes:
                changes_log.append(ac)
            if len(deduped) != len(new_aliases):
                changes_log.append(f"    (removed {len(new_aliases) - len(deduped)} duplicate alias(es))")

    # Write output
    output = json.dumps(tasks, indent=2, ensure_ascii=False) + '\n'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output)

    print(f"Processed {len(tasks)} tasks")
    print(f"Changes made: {len(changes_log)}")
    for line in changes_log:
        print(line)
    print(f"\nOutput written to: {output_path}")


def process_file_regex(input_path: str, output_path: str):
    """Fallback: regex-based processing for truncated JSON files."""
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    output_lines = []
    changes = 0

    for line in lines:
        # Match canonical_name lines
        m = re.match(r'^(\s*"canonical_name":\s*")(.+?)(",?\s*)$', line)
        if m:
            prefix, name, suffix = m.group(1), m.group(2), m.group(3)
            new_name, _ = clean_canonical_name(name)
            if new_name != name:
                line = f'{prefix}{new_name}{suffix}\n'
                changes += 1

        # Match alias lines (within aliases array)
        # These look like:  "Some Alias (ABC)",
        m = re.match(r'^(\s*")(.+?\s*\([^)]+\))(",?\s*)$', line)
        if m:
            prefix, alias, suffix = m.group(1), m.group(2), m.group(3)
            cleaned = clean_alias(alias)
            if cleaned != alias:
                line = f'{prefix}{cleaned}{suffix}\n'
                changes += 1

        output_lines.append(line)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)

    print(f"Regex fallback: {changes} line-level changes")
    print(f"Output written to: {output_path}")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python cleanup_canonical_names.py <input.json> <output.json>")
        sys.exit(1)

    process_file(sys.argv[1], sys.argv[2])
