#!/usr/bin/env python3
"""
Add new process aliases to process_details.json.

Source: outputs/aliases/proposed_aliases_2026-04-26.md (reviewed and approved
by the user on 2026-04-26).

Workflow per CLAUDE.md:
  1. Read process_details.json with the Read-equivalent (Python json.load).
  2. Stage modified copy in .scratch/.
  3. Verify JSON validity, process count, and that every targeted process
     was found and updated.
  4. Only with --write does the staged copy replace the canonical file.
  5. A decision note is written to .status/.

Usage:
    # Dry run (default) — writes only to .scratch/, prints summary.
    python code/data_management/add_aliases_2026-04-26.py

    # Write back to process_details.json.
    python code/data_management/add_aliases_2026-04-26.py --write
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Aliases to add. Keys are exact `process_name` strings. Values are lists of
# alias dicts (each with "name" and optional "note"). New aliases are appended
# to any existing aliases list; existing aliases are not modified.
# ---------------------------------------------------------------------------
NEW_ALIASES: dict[str, list[dict]] = {
    # associative_learning_and_reinforcement (7 aliases)
    "Extinction": [{"name": "extinction learning"}],
    "Goal-directed behavior": [{"name": "goal-directed action"}],
    "Habit": [{"name": "habit learning"}],
    "Model-based learning": [{"name": "model-based reinforcement learning"}],
    "Model-free learning": [{"name": "model-free reinforcement learning"}],
    "Pavlovian conditioning": [
        {"name": "classical conditioning"},
        {"name": "Pavlovian"},
    ],

    # auditory_and_pre_attentive_deviance_processing (2)
    "Auditory tone discrimination": [{"name": "tone discrimination"}],
    "Pitch perception": [{"name": "pitch processing"}],

    # awareness_agency_and_metacognition (5)
    "Interoceptive awareness": [{"name": "interoception"}],
    "Mind wandering": [
        {"name": "task-unrelated thought"},
        {"name": "mind-wandering"},
    ],
    "Perceptual awareness": [{"name": "conscious perception"}],
    "Self-referential processing": [{"name": "self-referential"}],

    # cognitive_flexibility_and_higher_order_executive_function (2 added to
    # existing aliases on Set shifting)
    "Set shifting": [
        {"name": "task switching"},
        {"name": "task-switching"},
    ],

    # emotion_perception_and_regulation (2)
    "Affective priming": [{"name": "evaluative priming"}],
    "Cognitive reappraisal": [{"name": "reappraisal"}],

    # face_and_object_perception (6)
    "Biological motion perception": [
        {
            "name": "biological motion",
            "note": "common shorthand in titles even when the paper is about perception of biological motion",
        },
    ],
    "Face identity recognition": [{"name": "face recognition"}],
    "Face perception": [{"name": "face processing"}],
    "Olfactory perception": [{"name": "olfaction"}],
    "Visual form recognition": [{"name": "shape recognition"}],
    "Visual object recognition": [{"name": "object recognition"}],

    # inhibitory_control_and_conflict_monitoring (3)
    "Interference control": [{"name": "interference resolution"}],
    "Response inhibition": [
        {"name": "inhibitory control"},
        {
            "name": "response suppression",
            "note": "more common in motor-control and oculomotor literatures",
        },
    ],

    # language_comprehension_and_production (3)
    "Lexical access": [{"name": "lexical retrieval"}],
    "Sentence comprehension": [{"name": "sentence processing"}],
    "Syntactic parsing": [{"name": "syntactic processing"}],

    # long_term_memory (7)
    "Consolidation": [{"name": "memory consolidation"}],
    "Declarative memory": [{"name": "explicit memory"}],
    "Encoding": [{"name": "memory encoding"}],
    "Recognition": [{"name": "recognition memory"}],
    "Reconsolidation": [{"name": "memory reconsolidation"}],
    "Retrieval": [{"name": "memory retrieval"}],
    "Source memory": [
        {
            "name": "source monitoring",
            "note": "Johnson, Hashtroudi & Lindsay (1993) tradition",
        },
    ],

    # motor_preparation_timing_and_execution (8)
    "Antisaccade": [{"name": "anti-saccade"}],
    "Motor planning": [{"name": "movement planning"}],
    "Motor preparation": [{"name": "movement preparation"}],
    "Response execution": [{"name": "movement execution"}],
    "Response selection": [{"name": "action selection"}],
    "Saccade": [{"name": "saccadic"}],
    "Visuomotor adaptation": [{"name": "sensorimotor adaptation"}],
    "Vocal-motor control": [{"name": "speech motor control"}],

    # reasoning_and_problem_solving (1)
    "Causal reasoning": [{"name": "causal inference"}],

    # short_term_and_working_memory (1)
    "Verbal working memory": [
        {
            "name": "phonological loop",
            "note": "Baddeley working memory model",
        },
    ],

    # social_cognition_and_strategic_social_choice (1)
    "In-group/out-group processing": [{"name": "intergroup processing"}],

    # value_based_decision_making_under_risk_and_uncertainty (4)
    "Delay discounting": [{"name": "temporal discounting"}],
    "Intertemporal choice": [{"name": "intertemporal decision making"}],
    "Probability judgment": [{"name": "probability estimation"}],
    "Value-based decision making": [{"name": "value-based choice"}],
}

EXPECTED_TOTAL_ALIASES = sum(len(v) for v in NEW_ALIASES.values())  # 52
EXPECTED_PROCESSES_TOUCHED = len(NEW_ALIASES)  # 48


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--workspace",
        default=".",
        help="Workspace root (default: current directory)",
    )
    p.add_argument(
        "--write",
        action="store_true",
        help="Write changes back to process_details.json (default: dry run)",
    )
    return p.parse_args()


def apply_aliases(processes: list[dict]) -> tuple[list[dict], list[str], list[str]]:
    """Return (modified_processes, applied_log, missing_processes).

    `applied_log` contains one human-readable line per added alias.
    `missing_processes` contains any keys in NEW_ALIASES not found in the data.
    """
    applied: list[str] = []
    found: set[str] = set()

    # Build name → process index for fast lookup.
    name_to_proc = {p["process_name"]: p for p in processes}

    for target_name, new_aliases in NEW_ALIASES.items():
        proc = name_to_proc.get(target_name)
        if proc is None:
            continue
        found.add(target_name)
        existing = proc.get("aliases", [])
        existing_names = {a["name"] for a in existing}
        added_to_this = []
        for alias in new_aliases:
            if alias["name"] in existing_names:
                applied.append(
                    f"  [skip] {target_name} already has alias '{alias['name']}'"
                )
                continue
            existing.append(alias)
            added_to_this.append(alias["name"])
        if added_to_this:
            applied.append(
                f"  [add]  {target_name}: {', '.join(repr(a) for a in added_to_this)}"
            )
        proc["aliases"] = existing

    missing = [name for name in NEW_ALIASES if name not in found]
    return processes, applied, missing


def main() -> int:
    args = parse_args()
    ws = Path(args.workspace).resolve()
    src = ws / "process_details.json"
    scratch_dir = ws / ".scratch"
    scratch_dir.mkdir(exist_ok=True)
    staged = scratch_dir / "process_details_with_new_aliases.json"

    if not src.exists():
        print(f"ERROR: not found: {src}", file=sys.stderr)
        return 1

    with src.open("r", encoding="utf-8") as f:
        data = json.load(f)

    original_total = data.get("total_processes")
    original_count = len(data["processes"])
    if original_total != original_count:
        print(
            f"WARN: header total_processes ({original_total}) != "
            f"len(processes) ({original_count})",
            file=sys.stderr,
        )

    # Apply.
    data["processes"], log_lines, missing = apply_aliases(data["processes"])

    # Sanity checks.
    new_count = len(data["processes"])
    if new_count != original_count:
        print(
            f"ERROR: process count changed: {original_count} -> {new_count}",
            file=sys.stderr,
        )
        return 2
    if missing:
        print(
            f"ERROR: {len(missing)} process names not found in catalog:",
            file=sys.stderr,
        )
        for m in missing:
            print(f"  - {m!r}", file=sys.stderr)
        return 3

    # Stage to .scratch/ first.
    staged_text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    staged.write_text(staged_text, encoding="utf-8")

    # Verify staged JSON parses.
    with staged.open("r", encoding="utf-8") as f:
        verified = json.load(f)
    assert len(verified["processes"]) == original_count, (
        "staged file has wrong process count"
    )

    # Report.
    print(f"Source:   {src}")
    print(f"Staged:   {staged}")
    print(f"Processes: {original_count} (unchanged)")
    print(f"Targets:   {EXPECTED_PROCESSES_TOUCHED} processes")
    print(f"Aliases to add: {EXPECTED_TOTAL_ALIASES}")
    print()
    for line in log_lines:
        print(line)
    print()

    if args.write:
        src.write_text(staged_text, encoding="utf-8")
        print(f"WROTE: {src}")
    else:
        print("Dry run only. Re-run with --write to apply.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
