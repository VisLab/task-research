# task-research

Purpose: a structured catalog of cognitive processes and experimental tasks
(`Claude-research/process_details.json`, `Claude-research/task_details.json`),
plus a literature pipeline that grounds each catalog item in publications and,
ultimately, in datasets - all in support of task models for HED (Hierarchical
Event Descriptor) annotation.
Not in scope: the public catalog site (that is `hed-task`) and the shared API
client/cache library (that is `hed-metadata-toolkit`).

## Commands

Test framework: pytest. Never convert the suite from one style to the other as
a side effect of other work.

Run from the repo root with the venv active (`.venv\Scripts\Activate.ps1` on
PowerShell, `source .venv/Scripts/activate` in git bash):

- Install dev env: `pip install -e ".[dev,test]"` plus an editable install of
  `hed-metadata-toolkit` from its own checkout (path is machine-specific; see
  `.status/local-environment.md`).
- Run tests: `python -m pytest -m "not network and not browser"`
- All tests including live-API and browser tests: `python -m pytest`
- Single test: `python -m pytest Claude-research/code/literature_search/test_normalize.py -q`
- Lint: `python -m ruff check Claude-research/code/`
- Format check: `python -m ruff format --check Claude-research/code/`
- Spell check: `typos` (exclusions in `pyproject.toml` under `[tool.typos]`)

Pipeline scripts run with `Claude-research/` as the current working directory
(the "workspace root") and take a `--workspace` argument defaulting to `.`:

```
python code/literature_search/phase3_search.py --mode poc --write
```

## Layout

- `Claude-research/` - the catalog workspace: catalog JSON, schemas, code,
  instructions, and script outputs. Scripts treat it as their working directory.
- `Claude-research/code/literature_search/` - literature pipeline modules and
  their tests (`test_*.py` beside the modules).
- `Claude-research/code/data_management/` - catalog generation, validation,
  and one-off fixes.
- `Claude-research/code/citation_enrichment/` - legacy, kept for reference;
  do not extend.
- `Claude-research/schemas/` - JSON Schemas (draft-07) for the catalog files.
- `Claude-research/outputs/` - script outputs only; never `.py` files here,
  never outputs under `code/`.
- `HED-PDFs/`, `HED-Markdown-*/`, `Zotero-HED/`, `GoogleSearches/` - acquired
  papers, their conversions, a vendored Zotero profile, and saved search
  references; data, not source.
- `.status/` - working notes. Gitignored; local to each machine.

## Conventions that differ from defaults

- **ASCII only** in prose, code, comments, and filenames: `-` not em or en
  dashes, `->` not arrows, `...` not an ellipsis character, straight quotes,
  no emoji. Exception: genuine data (author names, dataset titles, recorded
  API responses) keeps whatever characters it actually contains.
- Markdown headers in sentence case: capitalize the first word, proper nouns,
  and acronyms only.
- Filenames: lowercase, ASCII, no spaces; never two names differing only in case.
- Google-style docstrings with `Parameters:` rather than `Args:`; line length
  120 (`[tool.ruff]` in `pyproject.toml`).
- Relative paths only in committed files. Scripts derive every path from
  `--workspace`; no hardcoded absolute path or drive letter anywhere committed.

## Rules that are easy to get wrong

- `process_details.json` and `task_details.json` are the canonical catalog
  sources. Scripts never overwrite them silently: read the current version
  first, stage output in `.status/scratch/`, verify it parses and the item
  counts match, then write back only behind an explicit `--write` or
  `--write-back` flag. Dry-run is the default.
- Every reference in the catalogs carries a `roles` list drawn from:
  `historical`, `review`, `experiment`, `dataset`, `other`, `unknown`.
  A script must refuse to remove a reference whose roles include
  `historical` unless given an explicit override flag.
- API keys live in `Claude-research/code/.apikeys` (gitignored, `KEY=value`
  lines); environment variables take priority. Never log or print key values.
  `.env.example` documents the variables.
- The cache root resolves as `--cache-dir` arg -> `HED_CACHE_DIR` env var ->
  `outputs/cache/`. The on-disk cache convention is owned by
  `hed-metadata-toolkit`; never hardcode a cache path.
- Semantic Scholar caps search requests at 1/second whether or not a key is
  sent; the shared client enforces this. Do not "optimize" it away.

## Related repositories

- `hed-metadata-toolkit` - the shared base layer (API clients, cache, citation
  identity) this repo imports. Installed editable from its own checkout, not
  vendored here.
- `hed-task` - the public catalog site and, since 2026-09-19, the home of the
  catalog: task and process records are edited there by pull request. This
  repo's copies were imported once (`README.md`, "Hand-off to hed-task") and
  are not the authority; a bulk refresh would go through hed-task's
  `src/import_catalog.py`.
- `nemar-metadata` - sibling metadata-curation repo; NEMAR dataset citations
  are the intended grounding for this repo's references.

## Where the thinking lives

`.status/` is gitignored, so it exists only on the machine that wrote it and
never in a fresh clone or worktree.

- `.status/README.md` - the index. Read this first; it lists what is active.
- `.status/decisions.md` - why things are the way they are. Read before
  proposing structural changes. Append entries; never rewrite one.
- `.status/plans/*.md` - active plans. Check the `Status:` header and the
  `[ ]` / `[x]` markers before starting work.
- `.status/local-environment.md` - this machine's paths, interpreter, and
  quirks. Tool-agnostic. Never copy its contents into a committed file.
- IMPORTANT: do not read `.status/archive/` unless a file is named for you.
  Nothing new is created at the `.status/` root.

## Working agreements

- IMPORTANT: every file written to `.status/` opens with a `For humans:`
  summary - three or four sentences, at the very top: what the file is and
  what a person needs to take from it. The same applies to a long answer in a
  session: lead with the conclusion.
- IMPORTANT: temporary scripts, experiments, and one-off test files go in
  `.status/scratch/` - **never the repository root**. Delete them when the
  experiment ends; anything in `scratch/` may be deleted unread.
- IMPORTANT: never delete or rewrite a file under `.status/` without asking
  first. Appending is fine.
- For a change spanning more than three files, write a plan to
  `.status/plans/` and stop for review before editing.
- Label every command or diff proposed for the user to run (`Diagnostic A`,
  `Fix 1`, `Command 1`, ...) - one label per block, one expected result - and
  refer back by label.
- When you are guessing about an external API or data format, say so
  explicitly rather than assuming.
- Show evidence, not assertions: the command you ran and its actual output.
  For metadata work, include counts and a sample of records.
- Do not commit, push, or create branches unless asked.
