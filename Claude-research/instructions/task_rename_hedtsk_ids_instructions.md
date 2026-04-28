# Task: Rename hedtsk IDs to match canonical names

**Date:** 2026-04-19  
**Priority:** Must-fix before further catalog work  
**Estimated scope:** 36 IDs to rename across 5 authoritative files + 3 derived files

---

## Problem

The `hedtsk_id` values in `task_details.json` were generated inconsistently. Some use abbreviations (e.g., `hedtsk_bart`, `hedtsk_wcst`, `hedtsk_igt`), some use partial names (e.g., `hedtsk_corsi_block` instead of `hedtsk_corsi_block_tapping`), and some use alternate names rather than the canonical name (e.g., `hedtsk_garden_path` for "Sentence Comprehension Task", `hedtsk_face_localizer` for "Face Processing Task"). 67 of 103 IDs are already correct; 36 need renaming.

The requirement is that `hedtsk_id` must be **mechanically derivable** from `canonical_name` using a fixed rule, so the two can be converted back and forth programmatically.

## The conversion rule

Given a `canonical_name`:

1. Strip the trailing ` Task` or ` Test` (exactly one word at the end).
2. Lowercase everything.
3. Replace apostrophes (`'`) with nothing (delete them).
4. Replace `/` with `_`.
5. Replace `-` with `_`.
6. Replace spaces with `_`.
7. Collapse any runs of multiple `_` into a single `_`.
8. Prefix with `hedtsk_`.

**Examples:**

| canonical_name | hedtsk_id |
|---|---|
| Wisconsin Card Sorting Task | `hedtsk_wisconsin_card_sorting` |
| Go/No-Go Task | `hedtsk_go_no_go` |
| Raven's Progressive Matrices Task | `hedtsk_ravens_progressive_matrices` |
| Effort-Based Decision-Making Task | `hedtsk_effort_based_decision_making` |
| Attention Network Task | `hedtsk_attention_network` |

## The 36 renames

| Current ID | Correct ID | Canonical name |
|---|---|---|
| `hedtsk_attention_network_test` | `hedtsk_attention_network` | Attention Network Task |
| `hedtsk_bart` | `hedtsk_balloon_analog_risk` | Balloon Analog Risk Task |
| `hedtsk_cfmt` | `hedtsk_cambridge_face_memory` | Cambridge Face Memory Task |
| `hedtsk_corsi_block` | `hedtsk_corsi_block_tapping` | Corsi Block-Tapping Task |
| `hedtsk_cpt` | `hedtsk_continuous_performance` | Continuous Performance Task |
| `hedtsk_dsst` | `hedtsk_digit_symbol_substitution` | Digit Symbol Substitution Task |
| `hedtsk_effort_decision` | `hedtsk_effort_based_decision_making` | Effort-Based Decision-Making Task |
| `hedtsk_face_localizer` | `hedtsk_face_processing` | Face Processing Task |
| `hedtsk_garden_path` | `hedtsk_sentence_comprehension` | Sentence Comprehension Task |
| `hedtsk_iat` | `hedtsk_implicit_association` | Implicit Association Task |
| `hedtsk_igt` | `hedtsk_iowa_gambling` | Iowa Gambling Task |
| `hedtsk_mid` | `hedtsk_monetary_incentive_delay` | Monetary Incentive Delay Task |
| `hedtsk_mmn` | `hedtsk_mismatch_negativity` | Mismatch Negativity Task |
| `hedtsk_mot` | `hedtsk_multiple_object_tracking` | Multiple Object Tracking Task |
| `hedtsk_mst` | `hedtsk_mnemonic_similarity` | Mnemonic Similarity Task |
| `hedtsk_old_new_recognition` | `hedtsk_old_new_recognition_memory` | Old/New Recognition Memory Task |
| `hedtsk_ospan` | `hedtsk_operation_span` | Operation Span Task |
| `hedtsk_paired_associates` | `hedtsk_paired_associates_learning` | Paired Associates Learning Task |
| `hedtsk_posner_cueing` | `hedtsk_posner_spatial_cueing` | Posner Spatial Cueing Task |
| `hedtsk_prp` | `hedtsk_psychological_refractory_period` | Psychological Refractory Period Task |
| `hedtsk_pss_frank` | `hedtsk_probabilistic_selection` | Probabilistic Selection Task |
| `hedtsk_pvt` | `hedtsk_psychomotor_vigilance` | Psychomotor Vigilance Task |
| `hedtsk_radial_arm_maze` | `hedtsk_virtual_radial_arm_maze` | Virtual Radial Arm Maze Task |
| `hedtsk_random_dot_motion` | `hedtsk_random_dot_kinematogram` | Random Dot Kinematogram Task |
| `hedtsk_rat` | `hedtsk_remote_associates` | Remote Associates Task |
| `hedtsk_ravens_matrices` | `hedtsk_ravens_progressive_matrices` | Raven's Progressive Matrices Task |
| `hedtsk_ravlt` | `hedtsk_rey_auditory_verbal_learning` | Rey Auditory Verbal Learning Task |
| `hedtsk_rmet` | `hedtsk_reading_the_mind_in_the_eyes` | Reading the Mind in the Eyes Task |
| `hedtsk_rsvp` | `hedtsk_rapid_serial_visual_presentation` | Rapid Serial Visual Presentation Task |
| `hedtsk_sart` | `hedtsk_sustained_attention_to_response` | Sustained Attention to Response Task |
| `hedtsk_sid` | `hedtsk_social_incentive_delay` | Social Incentive Delay Task |
| `hedtsk_srtt` | `hedtsk_serial_reaction_time` | Serial Reaction Time Task |
| `hedtsk_sternberg` | `hedtsk_sternberg_item_recognition` | Sternberg Item Recognition Task |
| `hedtsk_tmt` | `hedtsk_trail_making` | Trail Making Task |
| `hedtsk_ufov` | `hedtsk_useful_field_of_view` | Useful Field of View Task |
| `hedtsk_wcst` | `hedtsk_wisconsin_card_sorting` | Wisconsin Card Sorting Task |

## Files that must be updated

### Authoritative files (source of truth — must be edited directly)

1. **`task_details.json`** — Each task's `hedtsk_id` field. This is the primary file. 103 task entries, 36 need their `hedtsk_id` changed.

2. **`process_details.json`** — Every process has a `tasks` array containing `{"hedtsk_id": "...", "canonical_name": "..."}` objects. There are ~486 hedtsk references across 172 processes. Each old ID must be replaced with the new one wherever it appears.

3. **`tasks_criteria.md`** — 2 hedtsk references (examples in the criteria text). Check and update if they reference any of the 36 renamed IDs.

4. **`process_criteria.md`** — 1 hedtsk reference. Check and update if needed.

5. **`file_inventory.md`** — 7 hedtsk references. Check and update if needed.

### Derived files (regenerated — do NOT edit by hand)

These are regenerated from `task_details.json` and `process_details.json`:

6. **`task_names.json`** — Keyed by hedtsk_id. Regenerate after renaming.
7. **`process_task_index.json`** — Values are hedtsk_id arrays. Regenerate after renaming.
8. **`process_task_crossref.md`** — Contains hedtsk_ids in section headers. Regenerate after renaming.

### Historical/status files (DO NOT EDIT)

The `.status/` and `.status_2/` directories and `history.md` contain hedtsk references in historical context. **Do not update these.** They document what was true at the time they were written.

## Recommended approach

### Step 1: Build the rename map

Write a Python script that reads `task_details.json`, applies the conversion rule to every `canonical_name`, and produces a dictionary mapping old IDs to new IDs. Verify it produces exactly the 36 renames listed above (and that the other 67 are already correct).

### Step 2: Rename in task_details.json

For each task entry, replace `hedtsk_id` with the computed value. Use the **Edit tool** (Read/Edit, not bash) to make these changes. Write a verification script to confirm all 103 IDs now match their canonical names.

### Step 3: Rename in process_details.json

Every process's `tasks` array contains `hedtsk_id` values. Apply the rename map to all of them. There are ~486 references. This can be done with a script that reads the JSON, applies the map, and writes it back — but **use the Read tool to read the file and the Write tool to write it back**. Do NOT read or write via bash (see critical warning below).

### Step 4: Check and update criteria/inventory files

Grep `tasks_criteria.md`, `process_criteria.md`, and `file_inventory.md` for any of the 36 old IDs and replace them.

### Step 5: Regenerate derived files

Regenerate `task_names.json`, `process_task_index.json`, and `process_task_crossref.md` from the updated authoritative files. The regeneration logic already exists in `outputs/regenerate_derived_files.py` but may need adaptation since `task_details.json` is a flat array (not a dict with a `tasks` key).

### Step 6: Verify

Run a comprehensive verification:
- All 103 hedtsk_ids match the conversion rule applied to their canonical_name
- All hedtsk_ids in process_details.json tasks arrays exist in task_details.json
- No old IDs remain in any authoritative file
- All category counts still match
- Derived files are consistent

### Step 7: Write status report

Write a summary to `.status/` documenting what was done.

---

## CRITICAL: File access warning — virtiofs stale snapshot issue

**The bash sandbox sees a stale, potentially truncated snapshot of mounted files.** This is a known virtiofs issue that has bitten us repeatedly in prior sessions. Specifically:

- Files read via bash (at `/sessions/.../mnt/TaskResearch/Claude-research/`) may be **truncated** or have **trailing null bytes** appended.
- Files written via bash to the mount may not flush correctly.
- The Windows-side file (accessed via the Read/Write/Edit tools at `H:\Research\TaskResearch\Claude-research\`) is always authoritative and correct.

**Rules:**

1. **Always use the Read tool** (with Windows paths like `H:\Research\TaskResearch\Claude-research\task_details.json`) to read files, not bash `cat` or Python `open()`.
2. **Always use the Write or Edit tool** to write files back, not bash redirection or Python file I/O to the mounted path.
3. **If you must use bash** (e.g., for JSON processing with Python), copy the file from the mount to the outputs directory first, strip trailing null bytes, process it there, then use the Write tool to put the result back at the Windows path.
4. **Never trust** a JSON parse error from bash — it's probably the stale snapshot, not a real problem with the file.

The outputs directory (`/sessions/.../mnt/outputs/`) is safe for bash read/write — it's the mounted workspace files that have the stale snapshot problem.

---

## Remaining items (separate future phases)

These are not part of this rename task but should not be lost:

1. **Sync `process_reference.md`** with `process_details.json` — verify all 172 definitions agree between the two files.
2. **Update `process_list.md`** — currently stale; needs to reflect all removals (operant conditioning, maintenance, logical reasoning, cognitive flexibility) and count changes down to 172.
3. **Fill 407 empty reference titles** in `process_details.json` — future-phase literature lookup.
