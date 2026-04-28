"""
apply_drops.py — Read the signed-off triage file, extract all DROP
decisions, and remove those references from process_details.json and
task_details.json.

Usage:
    python3 apply_drops.py \
        --triage   reference_triage_2026-04-22.md \
        --processes _inputs/process_details.json \
        --tasks     _inputs/task_details.json \
        --out-processes _outputs/process_details.json \
        --out-tasks     _outputs/task_details.json

The script is non-destructive: it writes to --out-* paths and never
touches the input files.  The caller (Write tool) copies the outputs
back to the workspace originals.
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path


# ---------------------------------------------------------------------------
# Parse triage file → set of (owner_id, array_name, pos) to drop
# ---------------------------------------------------------------------------

def parse_drops(triage_path: Path) -> set[tuple[str, str, int]]:
    """Return the set of (owner_id, array_name, pos) for every DROP row
    in sections 1 and 2 of the triage Markdown table.

    Table column order (both sections):
      # | HED concept | ref list | title | citation | venue | year | reason | status | pos
      0    1             2          3       4          5       6      7        8        9
    """
    drops: set[tuple[str, str, int]] = set()
    text = triage_path.read_text(encoding="utf-8")

    # Only scan sections 1 and 2 (stop at ## 3.)
    m = re.search(r"^## 1\.", text, re.MULTILINE)
    m3 = re.search(r"^## 3\.", text, re.MULTILINE)
    if not m:
        raise ValueError("Could not find '## 1.' in triage file")
    end = m3.start() if m3 else len(text)
    scope = text[m.start():end]

    for line in scope.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")]
        cells = [c for c in cells if c]  # drop empty edge cells
        if len(cells) < 10:
            continue
        # Skip header rows and separator rows
        if cells[0] == "#" or re.match(r"^-+$", cells[0]):
            continue
        owner_id   = cells[1]
        array_name = cells[2]
        status     = cells[8]
        pos_str    = cells[9]
        if status.strip() != "DROP":
            continue
        try:
            pos = int(pos_str)
        except ValueError:
            print(f"WARNING: could not parse pos {pos_str!r} for {owner_id} {array_name}",
                  file=sys.stderr)
            continue
        drops.add((owner_id, array_name, pos))

    return drops


# ---------------------------------------------------------------------------
# Apply drops
# ---------------------------------------------------------------------------

def apply_to_processes(data: dict, drops: set[tuple[str, str, int]]) -> tuple[dict, int]:
    """Remove flagged references from process_details.json structure.
    Returns (modified_data, n_removed)."""
    # Group drops by (process_id, array_name)
    drop_map: dict[tuple[str, str], set[int]] = defaultdict(set)
    for owner_id, array_name, pos in drops:
        if not owner_id.startswith("hedtsk_"):
            drop_map[(owner_id, array_name)].add(pos)

    n_removed = 0
    for proc in data.get("processes", []):
        pid = proc.get("process_id", "")
        for arr_name in ("fundamental_references", "recent_references"):
            positions_to_drop = drop_map.get((pid, arr_name), set())
            if not positions_to_drop:
                continue
            original = proc.get(arr_name, [])
            kept = [ref for i, ref in enumerate(original)
                    if i not in positions_to_drop]
            n_dropped = len(original) - len(kept)
            if n_dropped != len(positions_to_drop):
                print(
                    f"WARNING: {pid}/{arr_name}: expected to drop "
                    f"{len(positions_to_drop)} but dropped {n_dropped}",
                    file=sys.stderr,
                )
            proc[arr_name] = kept
            n_removed += n_dropped
    return data, n_removed


def apply_to_tasks(data: list, drops: set[tuple[str, str, int]]) -> tuple[list, int]:
    """Remove flagged references from task_details.json structure.
    Returns (modified_data, n_removed)."""
    drop_map: dict[tuple[str, str], set[int]] = defaultdict(set)
    for owner_id, array_name, pos in drops:
        if owner_id.startswith("hedtsk_"):
            drop_map[(owner_id, array_name)].add(pos)

    n_removed = 0
    for task in data:
        tid = task.get("hedtsk_id", "")
        for arr_name in ("key_references", "recent_references"):
            positions_to_drop = drop_map.get((tid, arr_name), set())
            if not positions_to_drop:
                continue
            original = task.get(arr_name, [])
            kept = [ref for i, ref in enumerate(original)
                    if i not in positions_to_drop]
            n_dropped = len(original) - len(kept)
            if n_dropped != len(positions_to_drop):
                print(
                    f"WARNING: {tid}/{arr_name}: expected to drop "
                    f"{len(positions_to_drop)} but dropped {n_dropped}",
                    file=sys.stderr,
                )
            task[arr_name] = kept
            n_removed += n_dropped
    return data, n_removed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="Apply triage DROP decisions to JSON files")
    ap.add_argument("--triage",        required=True)
    ap.add_argument("--processes",     required=True)
    ap.add_argument("--tasks",         required=True)
    ap.add_argument("--out-processes", required=True)
    ap.add_argument("--out-tasks",     required=True)
    args = ap.parse_args()

    script_dir = Path(__file__).parent

    def resolve(p: str) -> Path:
        path = Path(p)
        return path if path.is_absolute() else script_dir / path

    triage_path   = resolve(args.triage)
    proc_in       = resolve(args.processes)
    task_in       = resolve(args.tasks)
    proc_out      = resolve(args.out_processes)
    task_out      = resolve(args.out_tasks)

    proc_out.parent.mkdir(parents=True, exist_ok=True)
    task_out.parent.mkdir(parents=True, exist_ok=True)

    # Parse drops
    print("Parsing triage file …")
    drops = parse_drops(triage_path)
    print(f"  DROP decisions parsed: {len(drops)}")

    process_drops = sum(1 for (o, a, p) in drops if not o.startswith("hedtsk_"))
    task_drops    = sum(1 for (o, a, p) in drops if o.startswith("hedtsk_"))
    print(f"  Process drops: {process_drops}  Task drops: {task_drops}")

    # Load JSON
    print("Loading process_details.json …")
    proc_data = json.loads(proc_in.read_text(encoding="utf-8"))

    print("Loading task_details.json …")
    task_data = json.loads(task_in.read_text(encoding="utf-8"))

    # Apply
    print("Applying drops to processes …")
    proc_data, n_proc = apply_to_processes(proc_data, drops)
    print(f"  Removed: {n_proc}")

    print("Applying drops to tasks …")
    task_data, n_task = apply_to_tasks(task_data, drops)
    print(f"  Removed: {n_task}")

    total = n_proc + n_task
    if total != len(drops):
        print(f"WARNING: expected {len(drops)} total removals, got {total}", file=sys.stderr)
    else:
        print(f"Total removed: {total} ✓  (matches drop count)")

    # Write outputs
    print(f"Writing {proc_out} …")
    proc_out.write_text(
        json.dumps(proc_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Writing {task_out} …")
    task_out.write_text(
        json.dumps(task_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("Done.")


if __name__ == "__main__":
    main()
