# task-research

A structured catalog of cognitive **processes** and experimental **tasks** for
the HED (Hierarchical Event Descriptor) annotation framework, plus a
literature pipeline that grounds each catalog item in publications and
datasets.

The catalog and its code live in `Claude-research/`; supporting data
directories (`Zotero-HED/`, `HED-PDFs/`, `HED-Markdown-*/`, `GoogleSearches/`)
sit alongside it. Project conventions for AI-assisted sessions are in
`AGENTS.md` at the repository root.

---

## What this is

The catalog (`Claude-research/process_details.json` and
`Claude-research/task_details.json`) defines:

- **Cognitive processes**, organized into categories (e.g. *Response
  inhibition*, *Working memory updating*, *Pavlovian conditioning*).
- **Experimental tasks/paradigms** (e.g. *Stop-Signal Task*, *N-Back Task*,
  *Affective Picture Viewing*).
- The cross-reference between them, plus aliases, definitions, inclusion
  tests, variations, and references.

The literature pipeline (`Claude-research/code/literature_search/`) builds a
systematically-searched reference list for each catalog item using the
academic APIs (OpenAlex, CrossRef, Europe PMC, Semantic Scholar, Unpaywall)
and acquires open-access full text (PDF and Markdown) for analysis. The
shared API clients, cache, and citation-identity layer live in the sibling
[hed-metadata-toolkit](https://github.com/hed-standard/hed-metadata-toolkit)
package.

## Repository layout

```
task-research/                       <- repo root, .git lives here
|
|-- README.md                        this file
|-- AGENTS.md                        instructions for AI assistants
|-- CLAUDE.md                        imports AGENTS.md for Claude Code
|-- pyproject.toml                   Python project metadata + dependencies
|-- .gitignore, .gitattributes
|
|-- .venv/                           Python virtual environment (gitignored)
|-- .vscode/                         VS Code workspace settings
|
|-- Claude-research/                 active project workspace
|   |-- process_details.json         the cognitive-process catalog
|   |-- task_details.json            the experimental-task catalog
|   |-- file_inventory.json          authoritative file inventory
|   |-- process_criteria.md          process classification criteria
|   |-- tasks_criteria.md            task classification criteria
|   |-- process_task_index.json      (derived)
|   |-- process_task_crossref.md     (derived)
|   |-- task_names.json              (derived)
|   |
|   |-- code/
|   |   |-- .apikeys                 API keys (gitignored - never log)
|   |   |-- data_management/         catalog generation, validation, fixes
|   |   |-- literature_search/       search + acquisition pipeline
|   |   `-- citation_enrichment/     legacy; kept for reference
|   |
|   |-- schemas/                     JSON Schemas (draft-07)
|   `-- outputs/                     script outputs (never .py files)
|
|-- HED-PDFs/                        acquired PDFs
|-- HED-Markdown-private/            converted Markdown (not redistributable)
|-- HED-Markdown-public/             converted Markdown (publishable licenses)
|-- Zotero-HED/                      vendored Zotero profile (not project source)
`-- GoogleSearches/                  saved web-search reference docs
```

**Key convention.** The Python scripts in `Claude-research/code/` are run
from the `Claude-research/` directory (which they treat as the "workspace
root"). `cd Claude-research` in the integrated terminal before running them,
or pass `--workspace` where supported.

## One-time setup

Prerequisites: Python 3.10+, Git, and (recommended) VS Code with the
Microsoft Python extension.

From a PowerShell terminal at the repository root:

```powershell
# 1. Create the virtual environment (only once)
python -m venv .venv

# 2. Activate it
.venv\Scripts\Activate.ps1

# 3. Install the project (uses pyproject.toml)
pip install -e ".[dev,test]"

# 4. Install the shared toolkit from its own checkout (editable)
pip install -e <path-to-hed-metadata-toolkit>

# Optional: browser-based fetcher (Playwright + headless Chromium) for
# WAF-protected OA repositories. After the pip install, fetch Chromium:
pip install -e ".[browser]"
playwright install chromium

# Optional: PDF -> Markdown conversion (heavy; downloads model weights)
pip install -e ".[pdf]"
```

To verify the install:

```powershell
python -c "import requests, jsonschema; print('ok')"
```

## VS Code setup

Open the **`task-research/`** folder (not `Claude-research/`) - that is where
the venv, `.git`, and `.vscode/settings.json` live.

- `Ctrl+Shift+P` -> **Python: Select Interpreter** -> pick
  `.venv/Scripts/python.exe`.
- The JSON-schema wiring for the catalog files ships in
  `.vscode/settings.json`; editing either catalog file surfaces schema
  errors inline. To verify: change a reference's `"roles": ["unknown"]` to a
  typo, save, and expect a red squiggle. Undo to clean up.

## The catalog files

| File | What it holds |
|---|---|
| `process_details.json` | Cognitive processes in categories. Each has a `process_id` (`hed_<slug>`), `process_name`, `category_id`, `definition`, and optional `aliases`, `references`, `tasks`, `notes`. |
| `task_details.json` | Experimental tasks (top level is a bare array). Each has `hedtsk_id` (`hedtsk_<slug>`), `canonical_name`, string-array `aliases`, `short_definition`, `description`, `inclusion_test`, `variations`, `hed_process_ids`, `references`. |

Schema differences worth knowing:

- Process aliases are `{name, note?}` objects; task aliases are plain strings.
- Both files share the same reference shape, with the same `roles`
  vocabulary (`historical`, `review`, `experiment`, `dataset`, `other`,
  `unknown`). A reference whose roles include `historical` is protected:
  scripts refuse to remove it without an explicit override flag.

Editing rules (never overwrite silently; dry-run by default; validate after)
are in `AGENTS.md`.

## Validation

JSON Schemas catch shape errors in the editor; the Python validators add the
cross-checks schemas cannot express (count headers, ID uniqueness,
referential integrity):

```powershell
cd Claude-research
python code/data_management/validate_catalog.py   # process_details.json
python code/data_management/validate_tasks.py     # task_details.json
```

Exit codes: `0` clean, `1` data issue, `2` file or schema not found,
`3` jsonschema not installed. Run these after any hand-edit or scripted
write.

After editing either catalog file, regenerate the derived views:

```powershell
cd Claude-research
python code/data_management/regenerate_derived_files.py
```

## Hand-off to hed-task

Since 2026-09-19 the public catalog lives in `hed-task`
(https://github.com/hed-standard/hed-task, `data/task_details.json` and
`data/process_details.json`) and is edited there by pull request. This workspace
is the record of the citation search that produced the references, and the place
to run any further bulk literature work. Its two catalog files were imported into
hed-task on 2026-09-18; do not edit a task or process here expecting the site to
change.

If a bulk refresh from this workspace is ever wanted again, the path is:

1. Here: make sure every reference carries a real `roles` value. The site
   publishes `historical` references under "Key references" (tasks) and
   "Fundamental references" (processes) and everything else under "Further
   references". `code/data_management/set_historical_roles.py` restored the roles
   from the April export once (dry run by default, `--write` to apply); new
   references should get their role when they are added.
2. Here: `python code/data_management/validate_tasks.py` and
   `python code/data_management/validate_catalog.py` must pass.
3. In a hed-task checkout: `python src/import_catalog.py --source <path to this
   repo>/Claude-research --check`, then the same without `--check`. The import
   validates against `schemas/`, drops the fields that belong to the literature
   pipeline (`pdf_locations`, `local_artifacts`, `pub_id`) and `atlas_id` (hed-task
   keeps its own curated Atlas mapping), assigns `variation_id` to every variation,
   and writes hed-task's `data/`. It never writes back here.
4. In hed-task: `python src/generate_docs.py`, which validates the catalog again
   and regenerates the pages; then commit data and pages together.

Nothing in hed-task reads this repository at build time, so this workspace can stay
private and the site builds without it.

## Literature pipeline

### API keys

Keys live in `Claude-research/code/.apikeys` (gitignored), one `KEY=value`
per line; environment variables take priority. `.env.example` documents the
variables. **Never log key values.**

Note on Semantic Scholar: a free-tier `S2_API_KEY` does NOT raise the
search-endpoint rate limit - both keyed and unkeyed callers are capped at
1 request/second, and the shared client enforces that unconditionally.
Setting the key is still useful (caller visibility, auth-scoped endpoints).
Plan full search runs as multi-hour jobs; same-day re-runs are near-free
because the response cache is date-stamped.

### Infrastructure validation

```powershell
cd Claude-research
python code/literature_search/phase1_validate.py           # read-only
python code/literature_search/phase1_validate.py --verbose
```

### Systematic search

For each catalog item, retrieves candidates per alias from each enabled
source, expands by citation-walking from strong seeds, scores and ranks, and
writes one Markdown file per item under `outputs/phase3/candidates/` for
human KEEP/DROP review:

```powershell
cd Claude-research
python code/literature_search/phase3_search.py --mode poc            # dry run, 3 items
python code/literature_search/phase3_search.py --mode poc --write
python code/literature_search/phase3_search.py --mode full --write
python code/literature_search/phase3_search.py --mode single --ids hed_response_inhibition --write
```

Useful flags: `--sources`, `--passes`, `--cache-dir`, `--output-dir`,
`--apikeys`, `--force-refresh`. Dry-run is the default; `--write` writes.

### Full-text acquisition

`code/literature_search/acquire/` fetches open-access PDFs into `HED-PDFs/`
and Markdown into `HED-Markdown-public/` (publishable licenses) or
`HED-Markdown-private/` (everything else), driven by the license policy in
`code/literature_search/license_policy.py`. `enrich_pdf_locations.py`
resolves OA locations; `acquire_pdf.py` and `acquire_markdown.py` do the
fetching.

## Testing, linting, spell check

From the repository root with the venv active:

```powershell
python -m pytest -m "not network and not browser"   # offline test suite
python -m pytest                                    # everything, incl. live APIs
python -m ruff check Claude-research/code/
python -m ruff format --check Claude-research/code/
typos
```

Custom pytest markers (`network`, `slow`, `browser`) are declared in
`pyproject.toml`.

## Troubleshooting

- **"Schema not found" from a validator:** run from `Claude-research/`, or
  pass `--workspace` and `--schema` explicitly.
- **Scripts with stale defaults:** `triage_existing_refs.py` and
  `resolve_landmarks.py` have defaults pointing at an input layout that no
  longer exists; pass `--processes`, `--tasks`, `--landmark`, and `--output`
  explicitly.
- **Hardcoded-path scripts:** `regenerate_derived_files.py` and
  `apply_variation_audit.py` expect `Claude-research/` as the current
  working directory.
- **Deprecated one-offs:** scripts whose docstrings say DEPRECATED are
  historical record - their effects are already in the catalog. Do not run
  them.

## Files of note

- `AGENTS.md` - conventions, commands, and rules for assistants and humans.
- `Claude-research/file_inventory.json` - authoritative inventory of the
  workspace files with status (`current`, `historical`, `deprecated`,
  `generated`, `ignored`).
- `Claude-research/code/literature_search/README.md` - module-level overview
  of the search code.
