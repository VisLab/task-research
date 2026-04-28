# Handoff prompt: Process criteria document and audit

Copy everything below the line into a new session.

---

## Context

You are working on the HED (Hierarchical Event Descriptor) open-source project's cognitive process catalog. The project maintains parallel catalogs of **tasks** (experimental paradigms) and **processes** (cognitive constructs those tasks engage). Over several sessions we built, cleaned, and audited the task side — producing `tasks_criteria.md` (the rules document) and `task_details.json` (103 tasks, 779 variations after audit). Now it's time to do the same for the process side.

## What exists

The workspace is at `H:\Research\TaskResearch\Claude-research\`. Key process files:

### Authoritative
- **`process_details.json`** — The enriched, authoritative process catalog. 176 processes across 19 categories. Top-level has metadata fields, then a `categories` array (each with category_id, name, scope, out_of_scope, issues, history, process_count — but NO nested processes), then a flat `processes` array. Each process has: process_id (`hed_<slug>`), process_name, category_id, definition, fundamental_references[], recent_references[], tasks[], task_count. Reference objects have title (currently ALL empty — 407 empty titles), journal, year, citation_string. **NOTE:** bash in the sandbox may see a stale virtiofs snapshot of this file. If you need to run Python against it, read it via the Windows Read tool and Write it to the outputs directory first.
- **`process_reference.md`** — Human-readable reference for all 176 processes: definition, fundamental citations, recent citations, organized by category. 1509 lines.
- **`process_categories.md`** — Editorial companion: scope, out-of-scope, issues, and history for each of the 19 categories. 215 lines.

### Derived
- **`process_task_index.json`** — Reverse index: 154 processes that link to at least one task.
- **`process_task_crossref.md`** — Human-readable cross-reference: 103 tasks → their linked processes.
- **`process_list.md`** — Older flat list, predates the enriched JSON. May be slightly stale.

### Reference documents
- **`tasks_criteria.md`** — The completed task-side criteria document. Use this as the structural model for `process_criteria.md`. It covers: what counts as a task, what's excluded, naming conventions, identifier formats, the inclusion test, variation criteria (with DROP categories), and resolved/open policy questions. Read this file first.
- **`file_inventory.md`** — Documents all files, their roles, and schemas.
- **`.status/session_2026-04-18_audit_and_cleanup.md`** — Status report from the task audit session.
- **`.status_2/`** — Contains prior session status reports, decision logs, reframe notes. Key files: `reframe.md`, `decisions_log.md`, `umbrella_decisions.md`, `side_findings_resolutions.md`, `criteria_review_2026-04-17.md`.

### Known issues in the process data
1. **Instrumental ≡ Operant conditioning:** Two separate entries (`hed_instrumental_conditioning`, `hed_operant_conditioning`) that are synonyms. Should collapse to one.
2. **Working memory umbrella:** `hed_working_memory` exists alongside component rows (verbal WM, visual WM, spatial WM, etc.). Policy question whether the umbrella should be kept.
3. **22 processes with no task links** (task_count = 0). Some may be legitimate (processes not yet covered by the 103 tasks), others may signal problems.
4. **407 empty title fields** in references. This is a known future-phase item — do not attempt to fill these.
5. **`process_details.json` has a stale virtiofs snapshot in bash.** The file was edited earlier this session (Levy & Glimcher citation fix). To run Python against it, copy via Read→Write to the outputs directory.

## Your two deliverables

### 1. `process_criteria.md` — Write first

Create `process_criteria.md` in the repo root, modeled on `tasks_criteria.md` but for processes. It should cover:

- **§1 Process selection criteria:** What counts as a process in this catalog? What's excluded? (Umbrella constructs, traits, stimulus properties, task-level parameters, emotional states, specific emotions.) Draw on decisions already documented in `process_categories.md`, `.status_2/reframe.md`, `.status_2/umbrella_decisions.md`, `.status_2/decisions_log.md`, and `.status_2/side_findings_resolutions.md`.
- **§2 Naming conventions:** Process IDs (`hed_<slug>`), process names (sentence case), how synonyms are handled (one canonical, others point to it or merge).
- **§3 Definition standards:** What makes a good process definition. Every process must have one. One-sentence minimum.
- **§4 Category rules:** The 19 categories, their purpose, the scope/out-of-scope/issues structure. How to decide where a process goes when it could fit two categories.
- **§5 Reference standards:** What fundamental vs. recent references mean. Current state (407 empty titles). Quality expectations.
- **§6 Task linkage rules:** How processes link to tasks. A process links to a task if the task's inclusion test engages that process. The link is via `hedtsk_<slug>` IDs.
- **§7 Known issues and policy questions:** Consolidate all open issues from `process_categories.md` issues fields, `.status_2/umbrella_decisions.md`, and the known issues listed above. For each, state the issue, the current state, and whether it's resolved or open.

**Important:** Read the existing documents first. Do not invent criteria — extract and codify what's already been decided. Where decisions haven't been made, state the open question clearly. The document should be a reference that someone can use to evaluate whether a process entry is correct.

### 2. Audit `process_details.json` against the criteria — Do second

After writing `process_criteria.md`, audit every process in `process_details.json` against the criteria you just wrote. Check:

- Does every process have a non-empty definition?
- Does every process_id follow `hed_<slug>` format?
- Is every process_name sentence case?
- Is every process assigned to exactly one category, and does that category exist?
- Are there duplicate or near-duplicate processes? (Instrumental/Operant is known; are there others?)
- Are there entries that violate the exclusion criteria? (Umbrella constructs that shouldn't be process rows, traits, stimulus properties, emotions-as-states, task-level parameters.)
- Are the 22 unlinked processes (task_count=0) legitimate or problematic?
- Are category process_counts accurate?
- Do the category scope fields accurately describe what's in them?

Produce an audit report as `.status/process_audit_2026-04-18.md` with findings organized by category, a summary of issues found, and recommended actions (with severity: fix-now vs. future-phase vs. policy-decision-needed).

## Working conventions

- Write a session status report to `.status/` when done.
- The bash sandbox is Linux; file paths differ from Windows paths. The mapping: `H:\Research\TaskResearch\` → `/sessions/eloquent-friendly-galileo/mnt/TaskResearch/`. But beware the virtiofs stale-snapshot issue described above.
- Do not modify `process_details.json` in this session — this is a criteria-writing and audit session, not a fix session. Modifications come in a follow-up session after the audit is reviewed.
- Do not attempt to fill the 407 empty reference titles. That's a separate future task.
- Be thorough and honest. If something looks wrong, say so. Do not smooth over problems.
