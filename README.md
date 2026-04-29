# task-research

A structured catalog of cognitive **processes** and experimental **tasks** for
the HED (Hierarchical Event Descriptor) annotation framework, plus a
literature-search pipeline that builds a curated reference list for each
catalog item.

The catalog itself lives in `Claude-research/`; supporting directories
(`Zotero-HED/`, `HED-PDFs/`, `GoogleSearches/`) sit alongside it.

---

## Table of contents

1. [What this is](#what-this-is)
2. [Repository layout](#repository-layout)
3. [One-time setup](#one-time-setup)
4. [VS Code setup](#vs-code-setup)
5. [The catalog files](#the-catalog-files)
6. [Editor-time validation (JSON Schemas)](#editor-time-validation-json-schemas)
7. [Running the validators from the terminal](#running-the-validators-from-the-terminal)
8. [Regenerating derived files](#regenerating-derived-files)
9. [Literature-search pipeline](#literature-search-pipeline)
   - [API keys](#api-keys)
   - [Phase 1 — infrastructure validation](#phase-1--infrastructure-validation)
   - [Phase 2 — triage existing references](#phase-2--triage-existing-references)
   - [Phase 3 — systematic search](#phase-3--systematic-search-semantic-scholar-openalex-europe-pmc)
   - [Phase 5 — human review](#phase-5--human-review-manual)
   - [Phases 6–8 — future](#phases-68--future-not-yet-implemented)
10. [Cookbook (common operations)](#cookbook-common-operations)
11. [Troubleshooting & known issues](#troubleshooting--known-issues)
12. [Files of note](#files-of-note)

---

## What this is

The catalog (`Claude-research/process_details.json` and
`Claude-research/task_details.json`) defines:

- **172 cognitive processes** across 19 categories (e.g. *Response inhibition*,
  *Working memory updating*, *Pavlovian conditioning*).
- **103 experimental tasks/paradigms** (e.g. *Stop-Signal Task*, *N-Back Task*,
  *Affective Picture Viewing*).
- The cross-reference between them, plus aliases, definitions, inclusion
  tests, variations, and references.

The literature-search pipeline (`Claude-research/code/literature_search/`)
builds a systematically-searched reference list for each catalog item using
five academic APIs: OpenAlex, CrossRef, Europe PMC, Semantic Scholar, and
Unpaywall.

For project-internal conventions (file placement, reference schema, the
sandbox quirk with VirtioFS, etc.), see `CLAUDE.md` (next to this file at
the repository root).

---

## Repository layout

```
task-research/                       <- repo root, .git lives here
│
├── README.md                        this file
├── CLAUDE.md                        project conventions for Claude sessions
├── pyproject.toml                   Python project metadata + dependencies
├── .gitignore, .gitattributes
│
├── .venv/                           Python virtual environment (gitignored)
├── .vscode/                         VS Code workspace settings
├── .status/                         session reports + decision notes (gitignored)
│
├── Claude-research/                 active project workspace
│   ├── process_details.json         172 cognitive processes
│   ├── task_details.json            103 experimental tasks
│   ├── file_inventory.json          authoritative file inventory
│   ├── file_inventory.md            (regenerated from .json)
│   ├── process_criteria.md          process classification criteria
│   ├── tasks_criteria.md            task classification criteria
│   ├── process_task_index.json      (derived)
│   ├── process_task_crossref.md     (derived)
│   ├── task_names.json              (derived)
│   │
│   ├── code/                        all Python source
│   │   ├── .apikeys                 API keys (gitignored — never log)
│   │   ├── data_management/         catalog generation, validation, fixes
│   │   ├── literature_search/       Phase 1–9 pipeline + clients/
│   │   └── citation_enrichment/     legacy Phase A/B (historical)
│   │
│   ├── schemas/                     JSON Schemas (draft-07)
│   │   ├── process_details.schema.json
│   │   └── task_details.schema.json
│   │
│   ├── instructions/                plans, task instructions, thinking docs
│   │
│   └── outputs/                     script outputs
│       ├── aliases/                 alias-generation deliverables
│       ├── cache/                   API response cache (date-stamped, immutable)
│       └── phase3/candidates/       Phase 3 candidate markdowns (for review)
│
├── HED-PDFs/                        downloaded PDFs (Phase 7 target; empty initially)
├── Zotero-HED/                      vendored Zotero browser profile (large; not project source)
└── GoogleSearches/                  saved web-search reference docs
```

**Key convention.** The Python scripts in `Claude-research/code/` are designed
to be run from the `Claude-research/` directory (which they treat as the
"workspace root"). When VS Code opens `task-research/` as the workspace,
you'll need to `cd Claude-research` in the integrated terminal before
running them, or pass `--workspace Claude-research` where supported.

---

## One-time setup

### Prerequisites

- Python 3.10 or newer
- Git
- Visual Studio Code (recommended) with the official Microsoft Python extension

### Steps

From a PowerShell terminal at the repository root (`task-research/`):

```powershell
# 1. Create the virtual environment (only once)
python -m venv .venv

# 2. Activate it
.venv\Scripts\Activate.ps1

# 3. Install the project (uses pyproject.toml)
pip install -e .

# Optional: dev tools (ruff, typos, mdformat) and test tools (pytest, coverage)
pip install -e ".[dev,test]"
```

The runtime dependencies (`requests`, `jsonschema`) are declared in
`pyproject.toml` and pulled in by `pip install -e .`.

To verify the install:

```powershell
python -c "import requests, jsonschema; print('ok')"
```

---

## VS Code setup

Open the **`task-research/`** folder in VS Code (not `Claude-research/`),
because that's where the venv, `.git`, and `.vscode/settings.json` live.

### Select the Python interpreter

`Ctrl+Shift+P` → **Python: Select Interpreter** → pick the one under
`.venv/Scripts/python.exe`. After this, opening a new integrated terminal
auto-activates the venv.

### Wire up the JSON Schemas

The `.vscode/settings.json` should contain (paths relative to the workspace
root, which is `task-research/`):

```json
{
  "json.schemas": [
    {
      "fileMatch": ["**/process_details.json"],
      "url": "./Claude-research/schemas/process_details.schema.json"
    },
    {
      "fileMatch": ["**/task_details.json"],
      "url": "./Claude-research/schemas/task_details.schema.json"
    }
  ]
}
```

The `**/` glob lets the schema apply regardless of which directory you open
the JSON file from. To verify it's working: open
`Claude-research/process_details.json`, find any reference's `"roles": ["unknown"]`,
change it to `"roles": ["unknwn"]` (typo), save. You should see a red
squiggle within a second flagging that the value isn't in the allowed enum.
Undo to clean up.

### Open the integrated terminal

`` Ctrl+` `` opens a terminal that auto-activates the venv. From here, all
of the operations below run cleanly.

---

## The catalog files

The two source-of-truth files live at `Claude-research/`:

| File | What it holds |
|---|---|
| `process_details.json` | 172 cognitive processes, organized into 19 categories. Each has a `process_id` (`hed_<slug>`), a `process_name`, a `category_id`, a `definition`, and optional `aliases`, `references`, `tasks`, `notes`. |
| `task_details.json` | 103 experimental tasks. Top-level is a bare array. Each task has `hedtsk_id` (`hedtsk_<slug>`), `canonical_name`, string-array `aliases`, `short_definition`, `description`, `inclusion_test`, `variations`, `hed_process_ids`, and `references`. |

**Schema differences worth knowing:**

- Process aliases are `{name, note?}` objects.
- Task aliases are plain strings.
- Both files share the same reference shape, with the same `roles` vocabulary
  (`historical`, `review`, `experiment`, `dataset`, `other`, `unknown`).

The full reference schema and editing rules are in `CLAUDE.md` (at the
repository root) under "Reference schema" and "Core data files — handling
rules."

---

## Editor-time validation (JSON Schemas)

With the schema setup above wired in, VS Code highlights schema violations
the moment you save:

- Missing required key (`name`, `process_id`, etc.) → red squiggle.
- Invalid `roles` value (typo'd enum) → red squiggle.
- Wrong type (string where integer expected) → red squiggle.
- Extra key on `aliases[]` or `variations[]` items → red squiggle (those
  shapes have `additionalProperties: false`).

What schema validation does **not** catch:

- Cross-references (`category_id` resolves to a defined category, etc.)
- Header-vs-actual count mismatch (`total_processes` ≠ `len(processes)`)
- Duplicate `process_id` or `process_name`
- `task_count` ≠ `len(tasks)`

For those, run the Python validators below.

---

## Running the validators from the terminal

From `Claude-research/` (the integrated terminal in VS Code with the venv
active):

```powershell
cd Claude-research

# Validate process_details.json (schema + cross-checks)
python code/data_management/validate_catalog.py

# Validate task_details.json (schema + cross-checks)
python code/data_management/validate_tasks.py
```

Each prints an `OK:` summary block on success, or a list of issues on
failure. Exit codes:

- `0` — clean
- `1` — data issue (parse error, schema violation, or cross-check failure)
- `2` — file or schema not found
- `3` — `jsonschema` package not installed

Run these whenever you've hand-edited either catalog file (or after a
script makes a write).

---

## Regenerating derived files

After hand-editing `process_details.json` or `task_details.json`, the
derived files (`task_names.json`, `process_task_index.json`,
`process_task_crossref.md`, and the per-process `tasks[]` field inside
`process_details.json`) become stale. To regenerate:

```powershell
cd Claude-research
python code/data_management/regenerate_derived_files.py
```

The script reads only the authoritative files and `file_inventory.json`,
and writes the four derived files in place. It does **not** modify
`process_details.json` or `task_details.json` directly except for the
derived `tasks[]` field (per the comment at the top of `process_details.json`).

`file_inventory.md` is also regenerated from `file_inventory.json` by this
script.

---

## Literature-search pipeline

The pipeline runs in numbered phases. Phases 1–3 are implemented; Phase 5
is manual review; Phases 6–8 are future work.

### API keys

Keys live in `Claude-research/code/.apikeys` (gitignored). One per line:

```
S2_API_KEY=...
NCBI_API_KEY=...
```

**Note on the Semantic Scholar key:** a free-tier `S2_API_KEY` does NOT
raise the search-endpoint rate limit — both keyed and unkeyed callers are
capped at 1 request/second. Setting the key is still useful (Semantic
Scholar gets visibility into who is calling, and certain auth-scoped
endpoints require it), but don't expect it to speed up Phase 3. The S2
client at `code/literature_search/clients/semanticscholar.py` enforces
1 rps unconditionally. Request a key from
https://www.semanticscholar.org/product/api .

Environment variables take priority over the file. **Never log key values.**

### Phase 1 — infrastructure validation

Confirms all five API clients work, the cache is idempotent, and the
`pub_id` identity functions are deterministic.

```powershell
cd Claude-research
python code/literature_search/phase1_validate.py

# Useful flags
python code/literature_search/phase1_validate.py --verbose
python code/literature_search/phase1_validate.py --cache-dir outputs/cache
```

Read-only — no `--write` flag, doesn't modify any catalog file. A second
run on the same day costs zero network calls because the cache is
date-stamped.

To run the identity unit tests:

```powershell
pytest code/literature_search/test_identity.py -v
# Expected: 45 passed
```

### Phase 2 — triage existing references

Applies a set of triage rules (specialty journals, generic-too-broad
patterns, malformed-entry detectors) to the existing references in the
catalog and writes a Markdown review artifact. Read-only.

```powershell
cd Claude-research

python code/literature_search/triage_existing_refs.py `
  --processes process_details.json `
  --tasks task_details.json `
  --landmark instructions/landmark_refs_2026-04-22.md `
  --output ../.status/reference_triage_2026-04-26.md
```

(The script's built-in defaults expect an older `_inputs/` layout; pass the
arguments explicitly as shown. See *Troubleshooting* below.)

After human review of the produced markdown — KEEP/DROP marks added in
place — apply the drops:

```powershell
python code/literature_search/apply_drops.py `
  --triage ../.status/reference_triage_2026-04-26.md `
  --processes process_details.json `
  --tasks task_details.json `
  --out-processes .scratch/process_details_post_drops.json `
  --out-tasks .scratch/task_details_post_drops.json
```

This writes to `.scratch/` first (non-destructive). Diff-check, then copy
into place if satisfied. The script refuses to drop references whose
`roles` includes `historical` without an explicit override flag.

### Phase 3 — systematic search (Semantic Scholar, OpenAlex, Europe PMC)

The headline phase. For each catalog item:

- Stage A retrieves candidates from each enabled source using per-alias
  Semantic Scholar sub-queries plus OpenAlex / Europe PMC phrase filters.
- Stage B expands by walking citations from highly relevant seeds via S2.
- Stage C scores and ranks candidates with a composite of relevance,
  citation count, recency, and influence.

Output is one Markdown file per item under `outputs/phase3/candidates/`,
ready for human KEEP/DROP review.

```powershell
cd Claude-research

# Dry run on the proof-of-concept item set (3 items)
python code/literature_search/phase3_search.py --mode poc

# Same, but actually write the candidate markdowns
python code/literature_search/phase3_search.py --mode poc --write

# Full run across the entire catalog (slower; respects cache)
python code/literature_search/phase3_search.py --mode full --write

# Single item or a comma-separated list
python code/literature_search/phase3_search.py --mode single --ids hed_response_inhibition --write
python code/literature_search/phase3_search.py --mode single --ids hed_response_inhibition,hedtsk_stroop_color_word --write
```

**Useful flags:**

- `--write` — actually write output (default is dry-run)
- `--cache-dir outputs/cache` — override cache location (default is fine)
- `--output-dir outputs/phase3/candidates` — override output location
- `--apikeys code/.apikeys` — override key file
- `--sources openalex,europepmc,semanticscholar` — restrict sources
- `--passes all_years,recent,reviews` — restrict query passes
- `--force-refresh` — bust the cache for this run

A second run on the same day costs zero network calls (cache hits).

The current `outputs/phase3/candidates/` files were generated against the
old, mostly-empty alias set; expect them to change once you re-run Phase 3
against the new alias-augmented `process_details.json`.

### Phase 5 — human review (manual)

Open each file in `outputs/phase3/candidates/` and add KEEP/DROP marks
inline. The `apply_drops.py` script (above) consumes the marked-up files
to update the catalog.

### Phases 6–8 — future, not yet implemented

| Phase | Goal | Output |
|---|---|---|
| 6 | Build `publications.json` and `publication_links.json` | the unified publication store |
| 7 | Acquire PDFs (Unpaywall + manual) | `HED-PDFs/<LastName>_<Year>_<Title>_<hash8>.pdf` |
| 8 | Merge into the catalog | updates to `process_details.json` and `task_details.json` |

The PDF naming and the `pub_id` ↔ filename invariant are documented in
`Claude-research/instructions/pdf_naming_thinking_2026-04-21.md`.

---

## Cookbook (common operations)

### Add an alias to a process

1. Edit `Claude-research/process_details.json` directly. The schema will
   flag any structural mistake as you type.
2. Run `python code/data_management/validate_catalog.py` to confirm.
3. Run `python code/data_management/regenerate_derived_files.py` if the
   change affects derived views.
4. Commit.

### Add a new task

1. Edit `Claude-research/task_details.json` directly. Required fields:
   `hedtsk_id`, `canonical_name`, `short_definition`, `description`,
   `inclusion_test` (with all three sub-keys), `hed_process_ids`.
2. `python code/data_management/validate_tasks.py` to confirm.
3. `python code/data_management/regenerate_derived_files.py` to update the
   reverse index in `process_details.json` and the `task_names.json` /
   `process_task_crossref.md` derived files.
4. Commit.

### Update aliases at scale (batch)

Write a one-off script in `code/data_management/` modeled on
`add_aliases_2026-04-26.py` (idempotent, dry-run by default, stages to
`.scratch/`, writes only with `--write`). Run validator after.

### Re-run Phase 3 after alias updates

```powershell
cd Claude-research
python code/literature_search/phase3_search.py --mode full --write
```

This will re-query every catalog item. Hits the cache for any sub-query
that was issued today; otherwise re-fetches.

### Inspect what's in the cache

```powershell
ls outputs\cache\semanticscholar -Recurse | Measure-Object -Property Length -Sum
```

---

## Troubleshooting & known issues

### "Schema not found" when running a validator

The validator looks for the schema relative to the workspace root. Either
run from `Claude-research/`, or pass `--workspace Claude-research` and
`--schema schemas/process_details.schema.json` explicitly.

### `jsonschema` not installed

```powershell
.venv\Scripts\Activate.ps1
pip install jsonschema
```

### `triage_existing_refs.py` and `resolve_landmarks.py` look for `_inputs/`

These scripts have stale defaults pointing at an `_inputs/` directory that
no longer exists. Pass the actual paths explicitly when running:

```powershell
python code/literature_search/triage_existing_refs.py `
  --processes process_details.json `
  --tasks task_details.json `
  --landmark instructions/landmark_refs_2026-04-22.md `
  --output ../.status/reference_triage_<DATE>.md
```

### Several scripts in `code/data_management/` have hardcoded paths

`regenerate_derived_files.py` and `apply_variation_audit.py` use hardcoded
constants for input paths rather than argparse. They expect to be run with
`Claude-research/` as the current working directory:

```powershell
cd Claude-research
python code/data_management/regenerate_derived_files.py
```

### Scripts marked DEPRECATED

The following are historical one-offs whose effects are already in the
catalog. Don't run them:

- `code/literature_search/migrate_references.py` — unified the
  pre-2026-04-23 reference-schema split. Already applied.
- `code/literature_search/patch_malformed.py` — corrected 13 malformed
  refs. Already applied; will not match the current unified-references
  schema.
- `code/literature_search/_patch_triage_rules.py` — added specialty
  journals to triage_rules.py. Already applied.
- `code/data_management/extract_process_details_from_md.py` — superseded
  by direct JSON authoring.
- `code/data_management/regen_temp.py` — temporary helper.

These are kept as historical record; their docstrings note "DEPRECATED".

### Bash mount stale snapshots (Cowork sandbox only)

If running inside the Cowork sandbox, the bash-side VirtioFS mount may
show a stale snapshot of files just edited via the Edit tool. Either use
the Read tool (Windows-side) for verification, or rewrite via bash to
force a cache refresh. Not relevant in VS Code.

---

## Files of note

- `CLAUDE.md` (at the repository root, next to this README) — project
  conventions, schema rules, sandbox quirks. Read this when in doubt
  about where a file should live.
- `Claude-research/file_inventory.json` — authoritative inventory of all
  files in `Claude-research/` with status (`current`, `historical`,
  `deprecated`, `generated`, `ignored`).
- `Claude-research/instructions/literature_search_plan_2026-04-21.md` —
  the architectural plan for the literature-search workstream.
- `Claude-research/code/literature_search/README.md` — module-level
  overview of the search code (identity functions, cache layout, design
  notes).
- `.status/` (parent level, gitignored) — session reports, decision notes,
  and historical thinking documents. Filenames follow
  `session_YYYY-MM-DD_<topic>.md` and `decision_YYYY-MM-DD_<topic>.md`.
