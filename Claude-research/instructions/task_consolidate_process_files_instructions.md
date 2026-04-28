# Task: Consolidate process_reference.md and process_categories.md into process_details.json

**Date:** 2026-04-19  
**Goal:** Eliminate `process_reference.md` and `process_categories.md` as separate files. All their information should live in `process_details.json`, which is already the authoritative source of truth. After this task, those two markdown files should be deleted (or moved to an `original/` archive directory).

---

## Context

You are working on the HED (Hierarchical Event Descriptor) open-source project's cognitive process catalog. The workspace is at `H:\Research\TaskResearch\Claude-research\`.

The project currently maintains three files with overlapping process information:

1. **`process_details.json`** — The authoritative JSON catalog. 172 processes across 19 categories. Already contains: per-process definitions, citations, category placement, aliases, task links; and per-category scope, out_of_scope, issues, history, process_count. This is the single source of truth.

2. **`process_reference.md`** — A human-readable markdown file with 172 process entries organized by category. Each entry has: definition, fundamental references, recent references. This was the original source; `process_details.json` was extracted from it. It is now redundant — everything in it should already be in the JSON.

3. **`process_categories.md`** — A markdown editorial companion with scope, out_of_scope, history, and issues for each of the 19 categories. This too is now redundant — `process_details.json` already has category-level fields for these.

The problem is that these files have drifted apart through multiple editing sessions. Some edits were made to the JSON but not the markdown, and vice versa. The goal is to reconcile any differences (using the JSON as primary but checking whether the markdown has content the JSON is missing), absorb anything missing into the JSON, and then remove the markdown files.

## What specifically needs to happen

### Phase 1: Reconcile category-level content

Compare each of the 19 categories between `process_categories.md` and `process_details.json`. The JSON categories have these fields: `category_id`, `name`, `scope`, `out_of_scope`, `issues`, `history`, `process_count`. However, **not all categories have all optional fields**:

- 12 categories are **missing `history`** in the JSON (they have no history to record, or it was never added). Check whether `process_categories.md` has history text for any of these and add it if substantive.
- 3 categories are **missing `out_of_scope`** in the JSON: Auditory and Pre-Attentive Deviance Processing, Perceptual Decision-Making (Evidence Accumulation), Spatial Cognition and Navigation. Check whether `process_categories.md` has out_of_scope text for these (it may not — some categories genuinely have nothing notable to exclude).

For every category, verify that the `scope`, `out_of_scope`, `issues`, and `history` text in the JSON matches or subsumes what's in `process_categories.md`. Where the markdown has richer or more current text, update the JSON. Where the JSON is more current (due to recent edits), keep the JSON version.

### Phase 2: Reconcile process-level content

Compare every process definition between `process_reference.md` and `process_details.json`. For each of the 172 processes, check:

1. **Definition text** — Does the definition in the JSON match the one in the markdown? If they differ, determine which is more current/better and use that one. (The JSON was updated more recently in most cases.)

2. **References** — Does the JSON have all the references listed in the markdown? The JSON stores references as objects with `title`, `journal`, `year`, `citation_string`. The markdown has them as formatted strings. Check that no reference was lost.

3. **Category placement** — Verify the process appears under the same category heading in the markdown as its `category_id` indicates in the JSON.

There are 172 processes, so this needs to be done programmatically. Write a script that:
- Parses `process_reference.md` to extract per-process definitions and reference strings
- Compares them against `process_details.json`
- Reports any differences

### Phase 3: Absorb and update

Apply any fixes found in Phase 1 and Phase 2 to `process_details.json`. Then:

1. **Add missing optional fields** — If a category has `out_of_scope` or `history` content in the markdown that's absent from the JSON, add it.
2. **Fix any definition mismatches** — If a definition in the markdown is better/more current, update the JSON.
3. **Fix any missing references** — If the markdown has references the JSON doesn't, add them.

### Phase 4: Update references to eliminated files

After the JSON is complete, update other files that reference the eliminated markdown files:

- **`process_criteria.md`** — References `process_categories.md` and `process_reference.md` throughout. Update these references to point to `process_details.json` instead. Update the description of the file ecosystem.
- **`file_inventory.md`** — Remove entries for the two markdown files; update the description of `process_details.json` to note it is now the sole source for all process and category information.
- **`tasks_criteria.md`** — Check for any references to the eliminated files.

### Phase 5: Delete or archive the markdown files

Move `process_reference.md` and `process_categories.md` to the `original/` directory (as `original/process_reference_pre_consolidation_2026-04-19.md` and `original/process_categories_pre_consolidation_2026-04-19.md`). This preserves them for historical reference without cluttering the active file set.

### Phase 6: Regenerate derived files and verify

Regenerate:
- `task_names.json`
- `process_task_index.json`  
- `process_task_crossref.md`

Run a comprehensive verification:
- All 172 processes present with non-empty definitions
- All 19 category counts match actual process counts
- All category fields populated (scope required; out_of_scope, history, issues present where substantive)
- No stale references to `process_reference.md` or `process_categories.md` in any active file
- JSON is valid and well-formed

### Phase 7: Write status report

Write `.status/session_2026-04-19_consolidation.md` documenting what was done, any differences found between the files, how they were resolved, and the final state.

---

## CRITICAL: File access rules — virtiofs stale snapshot issue

**The bash sandbox sees a stale, potentially corrupted snapshot of mounted workspace files.** This has caused repeated problems in prior sessions: files appear truncated, have trailing null bytes appended, or show stale content after edits.

**Mandatory rules:**

1. **ALWAYS use the Read tool** (with Windows paths like `H:\Research\TaskResearch\Claude-research\process_details.json`) to read files. Do NOT use bash `cat`, `head`, `tail`, or Python `open()` on the mounted path.

2. **ALWAYS use the Write or Edit tool** to write files back to the workspace. Do NOT write via bash or Python to the mounted path.

3. **If you must use bash for processing** (e.g., running a Python comparison script), first Read the file with the Read tool, then use the Write tool to save a copy to the outputs directory (`C:\Users\Robbi\AppData\Roaming\Claude\local-agent-mode-sessions\...\outputs\`). In bash, this copy is at `/sessions/.../mnt/outputs/` and is safe to read/write. Process the copy, then use the Write tool to put results back at the Windows workspace path.

4. **After any Write/Edit to a workspace file**, do NOT try to read it back via bash to verify — bash will still see the old content. Use the Read tool to verify.

5. **If a JSON parse error occurs in bash**, it is almost certainly the stale snapshot (trailing null bytes), not a real problem. Strip null bytes from the copy before processing.

The outputs directory is safe for bash I/O. The workspace mount (`/sessions/.../mnt/TaskResearch/`) is NOT safe for direct bash I/O.

---

## File inventory

### Files you will modify
- **`process_details.json`** — Absorb any missing content from the markdown files. Windows path: `H:\Research\TaskResearch\Claude-research\process_details.json`
- **`process_criteria.md`** — Update references to eliminated files. Windows path: `H:\Research\TaskResearch\Claude-research\process_criteria.md`
- **`file_inventory.md`** — Update file descriptions. Windows path: `H:\Research\TaskResearch\Claude-research\file_inventory.md`

### Files you will move/archive
- **`process_reference.md`** → `original/process_reference_pre_consolidation_2026-04-19.md`
- **`process_categories.md`** → `original/process_categories_pre_consolidation_2026-04-19.md`

### Files for reference (do not modify)
- **`task_details.json`** — Task catalog (103 tasks). Flat JSON array.
- **`tasks_criteria.md`** — Task-side criteria document.
- **`.status/`** — Session reports and decision logs.
- **`.status_2/`** — Older session reports.

### Derived files (regenerate, do not hand-edit)
- **`task_names.json`** — Keyed by hedtsk_id.
- **`process_task_index.json`** — Process → task reverse index.
- **`process_task_crossref.md`** — Human-readable cross-reference.

### Schema notes

`process_details.json` top-level structure:
```json
{
  "description": "...",
  "generated_on": "2026-04-18",
  "source_script": "...",
  "schema_version": "2026-04-18",
  "total_categories": 19,
  "total_processes": 172,
  "total_processes_used_by_tasks": 154,
  "total_tasks": 103,
  "categories": [ ... ],   // 19 category objects
  "processes": [ ... ]      // 172 process objects (flat array, NOT nested under categories)
}
```

Category object fields: `category_id`, `name`, `scope`, `out_of_scope` (optional), `issues`, `history` (optional), `process_count`.

Process object fields: `process_id`, `process_name`, `category_id`, `definition`, `aliases` (optional array of `{name, note}`), `fundamental_references[]`, `recent_references[]`, `tasks[]`, `task_count`.

Reference object fields: `title` (currently empty for most — 407 empty titles, do NOT attempt to fill these), `journal`, `year`, `citation_string`.

`task_details.json` is a flat JSON array of 103 task objects (NOT a dict with a `tasks` key). Each task has `hedtsk_id`, `canonical_name`, `hed_process_ids[]`, etc. **NOTE:** The hedtsk_ids are scheduled for a separate rename pass — do not rename them in this task.

---

## Working conventions

- Always write a session status report to `.status/` when done.
- The user's preference: clean, well-thought-out work. Don't over-engineer. Produce a summary of your thinking in markdown in the `.status/` directory.
- Be thorough in the comparison — the whole point is to ensure nothing is lost when the markdown files go away.
- If you find substantive differences between files (not just formatting), document each one in the status report with how you resolved it.

---

## Remaining items (NOT part of this task — do not attempt)

These are tracked separately and should not be addressed in this session:

1. **hedtsk_id rename** — 36 of 103 task IDs need renaming to match canonical names. Separate task with its own instructions.
2. **Update `process_list.md`** — Currently stale. May itself become a candidate for elimination once process_details.json is the sole source.
3. **Fill 407 empty reference titles** — Future-phase literature lookup.
