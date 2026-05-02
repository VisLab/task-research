#!/usr/bin/env python3
"""
add_task_alias_expansions_2026-04-28.py — Add the spelled-out form of
each task's abbreviation alias as a sibling alias in task_details.json.

Why
---
Task aliases like "FER", "SST", "PRL" are short single-token abbreviations
that the rank_and_select._phrase_list filter drops (≤4 chars, single
token) to avoid the false-positive class of bug surfaced by FER on
hedtsk_facial_emotion_recognition. Without those aliases driving
retrieval, a paper that says only "stop-signal paradigm" but doesn't
include the canonical "Stop-Signal Task" verbatim is missed by the
phrase gate.

Adding the spelled-out forms as multi-word aliases gives the phrase
gate something specific to match on, and the abbreviation alias remains
in the data as documentation (just no longer load-bearing).

For some abbreviations the expansion is genuinely missing (e.g.
"Pavlovian-Instrumental Transfer" for PIT, "Probabilistic Reversal
Learning" for PRL). For others it's the canonical-without-"Task" form
which catches papers that say "Iowa Gambling" or "Stop-Signal" without
the "Task" suffix.

Behaviour
---------
- Idempotent. Each addition is skipped if the exact string is already
  in the task's alias list (or is the canonical name).
- Substring containment is NOT counted as a duplicate: the phrase gate
  matches phrases as verbatim substrings of paper text, so adding
  "Stop-Signal" alongside the canonical "Stop-Signal Task" is a real
  recall benefit.
- Dry run by default. Pass --write to actually modify task_details.json.
- Stages output to .scratch/ first, verifies JSON, then copies to root
  (per CLAUDE.md core-data-files handling rules).

Usage
-----
    # Dry run (default)
    python code/data_management/add_task_alias_expansions_2026-04-28.py

    # Write
    python code/data_management/add_task_alias_expansions_2026-04-28.py --write
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Additions. Keys are hedtsk_id; values are lists of new alias strings.
# Each entry is a multi-word phrase (so it survives the phrase-gate filter)
# that the literature commonly uses.
#
# Curated against the task_alias_abbreviations_2026-04-28.md reference.
# Cases where the expansion was already present (in canonical or another
# alias) are not listed here.
# ---------------------------------------------------------------------------
ADDITIONS: dict[str, list[str]] = {
    "hedtsk_anti_saccade": ["Anti-Saccade"],
    "hedtsk_artificial_grammar_learning": ["Artificial Grammar Learning"],
    "hedtsk_balloon_analog_risk": ["Balloon Analog Risk"],
    "hedtsk_cambridge_face_memory": ["Cambridge Face Memory"],
    "hedtsk_continuous_performance": ["Continuous Performance"],
    "hedtsk_delayed_match_to_sample": ["Delayed Match-to-Sample"],
    "hedtsk_dictator_game": [],  # already has "Dictator Game"
    "hedtsk_digit_span": ["Digit Span"],
    "hedtsk_digit_symbol_substitution": ["Digit Symbol Substitution"],
    "hedtsk_facial_emotion_recognition": ["Facial Emotion Recognition"],
    "hedtsk_finger_tapping": ["Finger Tapping"],
    "hedtsk_go_no_go": ["Go/No-Go"],
    "hedtsk_implicit_association": ["Implicit Association"],
    # PIT expansion is genuinely missing (canonical is "Instrumental
    # Conditioning Task"; PIT specifically refers to Pavlovian-Instrumental
    # Transfer, a related but distinct paradigm).
    "hedtsk_instrumental_conditioning": ["Pavlovian-Instrumental Transfer"],
    "hedtsk_iowa_gambling": ["Iowa Gambling"],
    "hedtsk_lexical_decision": ["Lexical Decision"],
    "hedtsk_mental_rotation": ["Mental Rotation"],
    "hedtsk_mirror_tracing": ["Mirror Tracing"],
    "hedtsk_mismatch_negativity": ["Mismatch Negativity"],
    "hedtsk_mnemonic_similarity": ["Mnemonic Similarity"],
    "hedtsk_monetary_incentive_delay": ["Monetary Incentive Delay"],
    "hedtsk_multi_armed_bandit": ["Multi-Armed Bandit"],
    "hedtsk_multiple_object_tracking": ["Multiple Object Tracking"],
    "hedtsk_operation_span": ["Operation Span"],
    "hedtsk_paired_associates_learning": ["Paired Associates Learning"],
    "hedtsk_psychological_refractory_period": ["Psychological Refractory Period"],
    "hedtsk_psychomotor_vigilance": ["Psychomotor Vigilance"],
    # PRL is genuinely missing (canonical is "Reversal Learning Task";
    # PRL specifically refers to the probabilistic variant).
    "hedtsk_reversal_learning": ["Probabilistic Reversal Learning"],
    "hedtsk_reading_the_mind_in_the_eyes": ["Reading the Mind in the Eyes Test"],
    "hedtsk_remote_associates": [],  # already has "Remote Associates Test"
    "hedtsk_serial_reaction_time": ["Serial Reaction Time"],
    "hedtsk_social_incentive_delay": ["Social Incentive Delay"],
    "hedtsk_stop_signal": ["Stop-Signal", "Stop Signal"],
    "hedtsk_sustained_attention_to_response": ["Sustained Attention to Response"],
    "hedtsk_tower_of_london": ["Tower of London"],
    "hedtsk_trail_making": [],   # already has "Trail Making Test"
    "hedtsk_trust_game": [],     # already has "Trust Game"
    "hedtsk_ultimatum_game": [], # already has "Ultimatum Game"
}


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

def apply_additions(tasks: list[dict]) -> tuple[list[dict], list[str]]:
    """Mutate `tasks` in place. Return (tasks, log_lines)."""
    log: list[str] = []
    by_id = {t.get("hedtsk_id"): t for t in tasks}
    for task_id, new_aliases in ADDITIONS.items():
        if not new_aliases:
            continue
        task = by_id.get(task_id)
        if task is None:
            log.append(f"  [skip] {task_id} not found in task_details.json")
            continue
        existing = task.setdefault("aliases", [])
        canonical = task.get("canonical_name", "")
        added: list[str] = []
        skipped: list[str] = []
        for new_alias in new_aliases:
            # Exact-match dedup against alias list and canonical.
            if new_alias in existing or new_alias == canonical:
                skipped.append(new_alias)
                continue
            existing.append(new_alias)
            added.append(new_alias)
        if added:
            log.append(f"  [add]  {task_id}: {', '.join(repr(a) for a in added)}")
        if skipped:
            log.append(f"  [skip] {task_id}: {', '.join(repr(a) for a in skipped)} already present")
    return tasks, log


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workspace", default=".",
                   help="Workspace root (default: cwd)")
    p.add_argument("--write", action="store_true",
                   help="Write changes to task_details.json (default: dry run)")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    ws = Path(args.workspace).resolve()
    src = ws / "task_details.json"
    scratch = ws / ".scratch"
    scratch.mkdir(exist_ok=True)
    staged = scratch / "task_details_with_alias_expansions.json"

    if not src.exists():
        print(f"ERROR: not found: {src}", file=sys.stderr)
        return 1

    with src.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        print("ERROR: task_details.json is not a top-level array.", file=sys.stderr)
        return 2

    n_tasks_before = len(data)
    data, log_lines = apply_additions(data)
    n_tasks_after = len(data)
    if n_tasks_before != n_tasks_after:
        print(f"ERROR: task count changed: {n_tasks_before} -> {n_tasks_after}", file=sys.stderr)
        return 3

    # Stage to .scratch/.
    staged_text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    staged.write_text(staged_text, encoding="utf-8")

    # Verify staged JSON parses.
    with staged.open("r", encoding="utf-8") as f:
        verified = json.load(f)
    assert len(verified) == n_tasks_before, "staged file has wrong task count"

    # Report.
    n_targets = len(ADDITIONS)
    n_actual_targets = sum(1 for v in ADDITIONS.values() if v)
    n_proposed = sum(len(v) for v in ADDITIONS.values())
    print(f"Source:   {src}")
    print(f"Staged:   {staged}")
    print(f"Tasks:    {n_tasks_before} (unchanged)")
    print(f"Targets:  {n_actual_targets} tasks (out of {n_targets} keys; rest already covered)")
    print(f"Proposed additions: {n_proposed} alias strings (some may dedup)")
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
