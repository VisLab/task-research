# Project Reorganisation Plan

**Date:** 2026-04-23  
**Status:** DRAFT — awaiting user approval before any moves

---

## Proposed directory structure

All paths are relative to the workspace root.

```
<workspace-root>/
│
├── CLAUDE.md                        project conventions for Claude sessions
├── process_details.json             canonical process catalog (172 processes)
├── task_details.json                canonical task catalog (103 tasks)
├── file_inventory.md                project file inventory
├── process_criteria.md              process inclusion criteria
├── task_criteria.md                 task inclusion criteria
│
├── instructions/                    plans and task instruction documents
│   ├── literature_search_plan_2026-04-21.md
│   ├── cleanup_plan_2026-04-23.md   (this file, once moved)
│   ├── handoff_process_criteria_audit.md
│   ├── pdf_naming_thinking_2026-04-21.md
│   ├── citation_enrichment_thinking_2026-04-20.md
│   ├── landmark_refs_2026-04-22.md          authoritative landmark list
│   ├── landmark_refs_proposed_2026-04-22.md
│   ├── landmark_refs_first_review_gemini-manual.md
│   ├── landmark_refs_second_pass_thinking_2026-04-22.md
│   ├── phase1_instructions_thinking_2026-04-21.md
│   ├── phase2_instructions_thinking_2026-04-22.md
│   ├── phase3_instructions_thinking_2026-04-23.md
│   ├── task_citation_enrich_processes_instructions.md
│   ├── task_citation_enrich_tasks_instructions.md
│   ├── task_consolidate_process_files_instructions.md
│   ├── task_literature_search_phase1_instructions.md
│   ├── task_literature_search_phase2_instructions.md
│   ├── task_literature_search_phase3_instructions.md
│   ├── task_rename_hedtsk_ids_instructions.md
│   ├── task_variation_audit.md
│   ├── task_variation_audit_instructions.md
│   ├── task_variation_audit_thinking_2026-04-21.md
│   └── task_variation_audit_thinking_2026-04-21_sonnet.md
│
├── .status/                         decision notes and session reports ONLY
│   ├── candidates_index_<date>.md   Phase 3 review entry point
│   ├── citation_enrichment_blocked_2026-04-20.md
│   ├── citation_enrichment_blocked_2026-04-22.md
│   ├── citation_gaps_2026-04-20.md
│   ├── citation_gaps_initial_2026-04-20.md
│   ├── false_positive_corrections_2026-04-20.md
│   ├── hedtsk_id_rename_2026-04-19.md
│   ├── malformed_refs_2026-04-23.md
│   ├── malformed_refs_verification_2026-04-23.md
│   ├── process_audit_2026-04-18.md
│   ├── process_details_repair_2026-04-23.md
│   ├── reference_triage_2026-04-22.md
│   ├── script_fix_manual_skip_2026-04-20.md
│   └── session_YYYY-MM-DD_*.md      (all session reports)
│
├── code/                            all Python source files
│   ├── .apikeys                     project-wide API key store (git-ignored)
│   └── literature_search/
│       ├── clients/
│       │   ├── __init__.py
│       │   ├── crossref.py
│       │   ├── europepmc.py
│       │   ├── openalex.py
│       │   ├── semanticscholar.py
│       │   └── unpaywall.py
│       ├── identity.py              library modules
│       ├── cache.py
│       ├── triage_rules.py
│       ├── normalize.py
│       ├── search_queries.py
│       ├── rank_and_select.py
│       ├── present_candidates.py
│       ├── README.md
│       ├── resolve_landmarks.py     runnable scripts
│       ├── triage_existing_refs.py
│       ├── apply_drops.py
│       ├── patch_malformed.py
│       ├── phase1_validate.py
│       ├── phase3_search.py
│       └── test_identity.py
│
├── outputs/                         outputs from running scripts
│   ├── cache/                       API response cache (git-ignored)
│   │   ├── crossref/<YYYY-MM-DD>/
│   │   ├── openalex/<YYYY-MM-DD>/
│   │   ├── europepmc/<YYYY-MM-DD>/
│   │   ├── semanticscholar/<YYYY-MM-DD>/
│   │   └── unpaywall/<YYYY-MM-DD>/
│   ├── phase2/                      Phase 2 script outputs
│   │   └── landmark_refs.json       resolved landmark DOIs
│   └── phase3/                      Phase 3 script outputs
│       └── candidates/
│           └── <item_id>.md
│
└── .scratch/                        temporary work files (disposable)
    └── (Claude's working files — never commit, safe to delete)
```

**Out of scope:** The Phase A/B legacy scripts (`outputs/enrich_citations_host_script.py`,
`outputs/add_url_field.py`, `outputs/citation_cache/`, etc.) are from the citation-enrichment
workstream. They will be reorganised in a separate session.

---

## Files to move from `.status/` → `instructions/`

| File | Reason |
|---|---|
| `literature_search_plan_2026-04-21.md` | primary plan |
| `cleanup_plan_2026-04-23.md` | this file |
| `handoff_process_criteria_audit.md` | instruction |
| `pdf_naming_thinking_2026-04-21.md` | design thinking |
| `citation_enrichment_thinking_2026-04-20.md` | design thinking |
| `landmark_refs_2026-04-22.md` | authoritative reference list |
| `landmark_refs_proposed_2026-04-22.md` | reference data |
| `landmark_refs_first_review_gemini-manual.md` | reference data |
| `landmark_refs_second_pass_thinking_2026-04-22.md` | design thinking |
| `phase1_instructions_thinking_2026-04-21.md` | design thinking |
| `phase2_instructions_thinking_2026-04-22.md` | design thinking |
| `phase3_instructions_thinking_2026-04-23.md` | design thinking |
| `task_citation_enrich_processes_instructions.md` | task instruction |
| `task_citation_enrich_tasks_instructions.md` | task instruction |
| `task_consolidate_process_files_instructions.md` | task instruction |
| `task_literature_search_phase1_instructions.md` | task instruction |
| `task_literature_search_phase2_instructions.md` | task instruction |
| `task_literature_search_phase3_instructions.md` | task instruction |
| `task_rename_hedtsk_ids_instructions.md` | task instruction |
| `task_variation_audit.md` | task instruction |
| `task_variation_audit_instructions.md` | task instruction |
| `task_variation_audit_thinking_2026-04-21.md` | design thinking |
| `task_variation_audit_thinking_2026-04-21_sonnet.md` | design thinking |

## Files to move from `outputs/literature_search/` → `code/literature_search/`

All `.py` files and the `clients/` subdirectory (see structure above).

## Files to move/rename

| From | To | Notes |
|---|---|---|
| `outputs/literature_search/.apikeys` | `code/.apikeys` | move, keep contents |
| `outputs/literature_search/cache/` | `outputs/cache/` | rename one level up |
| `outputs/literature_search/candidates/` | `outputs/phase3/candidates/` | rename |
| `scratch/` (current) | `.scratch/` | rename with dot prefix |

Note: `outputs/literature_search/landmark_refs.json` is now obsolete. The landmark
concept has been replaced by `roles: ["historical"]` in the reference arrays of
`process_details.json` and `task_details.json`. Phase 3 reads historical refs
directly from those files. The old JSON can be deleted.

## Files to delete

| File | Reason |
|---|---|
| `outputs/literature_search/malformed_refs_2026-04-23.md` | duplicate; canonical in `.status/` |
| `outputs/literature_search/reference_triage_2026-04-22.md` | duplicate; canonical in `.status/` |
| `outputs/literature_search/candidates/.gitkeep` | unnecessary placeholder |
| `outputs/literature_search/_inputs/` | sandbox staging area; no longer needed |
| `outputs/literature_search/_outputs/` | confirmed applied; repair complete |

---

## Path updates required in scripts

All scripts use paths relative to `--workspace` (default: current directory).
No absolute paths anywhere in defaults.

`phase3_search.py` — **DONE**:
- `--workspace .`
- `--cache-dir outputs/cache`
- `--output-dir outputs/phase3/candidates`
- `--apikeys code/.apikeys`
- Historical refs loaded directly from `process_details.json` / `task_details.json`
  (no longer reads a separate landmark file)

`resolve_landmarks.py` — no longer needed as a Phase 3 prerequisite.
The landmark concept is now encoded as `roles: ["historical"]` in the reference
arrays. If reference DOI enrichment is desired for existing refs, that is a
separate workstream (reference enrichment script, TBD).

---

## Execution order

**Completed (steps 1–6, 8):**
- ✓ 1. Created `instructions/`; moved 23 files from `.status/`
- ✓ 2. Created `code/literature_search/`; copied all `.py` files and `clients/`
- ✓ 3. Moved `.apikeys` → `code/.apikeys`
- ✓ 4. Renamed `scratch/` → `.scratch/`
- ✓ 5. Created `outputs/phase2/`, `outputs/phase3/candidates/`
- ✓ 6. Copied `outputs/literature_search/cache/` → `outputs/cache/`
- ✓ 8. Updated `phase3_search.py`: new paths, historical refs from JSON, no
       workspace root hardcoded
- ✓ Reference schema migration: unified `references` array with `roles` field

**Remaining:**

7. Delete staging dirs and obsolete files from `outputs/literature_search/`:
   - `_inputs/`
   - `_outputs/`
   - `candidates/.gitkeep`
   - `malformed_refs_2026-04-23.md` (duplicate of `.status/` copy)
   - `reference_triage_2026-04-22.md` (duplicate of `.status/` copy)
   - `landmark_refs.json` (superseded by `roles: ["historical"]` in JSON)

8. Verify all imports compile from `code/literature_search/`

9. Delete `outputs/literature_search/` once empty

10. Run POC: `python code/literature_search/phase3_search.py --mode poc --write`
