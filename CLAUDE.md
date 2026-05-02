# CLAUDE.md — Project conventions for Claude sessions

This file sits at the repository root (`task-research/CLAUDE.md`). It is
read at the start of every Claude session working on the HED (Hierarchical
Event Descriptor) cognitive process catalog. It describes the repository
layout, file placement rules, path conventions, and the quirks of the
Windows/Cowork sandbox environment.

For setup and how-to-run instructions, see the top-level `README.md`.

---

## What this project is

A structured catalog of ~172 cognitive processes and ~103 experimental tasks,
stored in `Claude-research/process_details.json` and
`Claude-research/task_details.json`. The long-term goal is a
systematically-searched reference list for each item, backed by a
`publications.json` store and a local Zotero library.

Active workstream: **literature search** (Phases 1–9). See
`Claude-research/instructions/literature_search_plan_2026-04-21.md` for the
full plan.

---

## Repository layout

The repository has two levels.

`task-research/` is the git root: this is where `pyproject.toml`, `.venv/`,
`.vscode/`, the top-level `README.md`, this `CLAUDE.md`, and the gitignored
`.status/` (session reports) live.

`Claude-research/` is the **catalog workspace** — where the catalog JSON
files, code, schemas, instructions, and script outputs live. All Python
scripts are run with `Claude-research/` as the current working directory;
they refer to it as the "workspace root." Paths in this file are
workspace-relative (i.e., relative to `Claude-research/`) unless explicitly
noted otherwise.

```
task-research/                       <- git root
│
├── README.md                        setup + how-to-run
├── CLAUDE.md                        this file (project conventions)
├── pyproject.toml                   Python project metadata + dependencies
├── .gitignore, .gitattributes
├── .venv/                           virtual environment (gitignored)
├── .vscode/                         workspace settings + schema mappings
├── .status/                         decision notes + session reports (gitignored)
│
├── Claude-research/                 <- catalog workspace ("workspace root")
│   ├── process_details.json         172 processes — DO NOT OVERWRITE without diff check
│   ├── task_details.json            103 tasks     — DO NOT OVERWRITE without diff check
│   ├── file_inventory.json          authoritative file inventory
│   ├── file_inventory.md            (regenerated)
│   ├── process_criteria.md
│   ├── tasks_criteria.md
│   ├── process_task_index.json      (derived)
│   ├── process_task_crossref.md     (derived)
│   ├── task_names.json              (derived)
│   │
│   ├── code/                        all Python source files
│   │   ├── .apikeys                 API key store (gitignored, never log)
│   │   ├── literature_search/       Phase 1–9 modules + clients/
│   │   ├── data_management/         catalog generation, validation, fixes
│   │   └── citation_enrichment/     legacy Phase A/B (historical)
│   │
│   ├── schemas/                     JSON Schemas (draft-07)
│   │   ├── process_details.schema.json
│   │   └── task_details.schema.json
│   │
│   ├── instructions/                plans and task instructions
│   │
│   ├── outputs/                     script outputs
│   │   ├── aliases/                 alias-generation deliverables
│   │   ├── cache/                   API response cache (date-stamped, immutable)
│   │   │   └── <source>/<YYYY-MM-DD>/<hash>.json
│   │   └── phase3/candidates/       per-item Phase 3 markdowns
│   │
│   └── .scratch/                    temporary work files (gitignored)
│
├── HED-PDFs/                        Phase 7 target (PDFs)
├── Zotero-HED/                      vendored Zotero profile (not project source)
└── GoogleSearches/                  saved web-search reference docs
```

---

## File placement rules

| What | Where |
|---|---|
| Literature search library modules and scripts | `code/literature_search/` |
| API client modules | `code/literature_search/clients/` |
| Citation enrichment scripts (Phase A/B) | `code/citation_enrichment/` |
| Catalog generation / one-off fix scripts | `code/data_management/` |
| Plans, task instructions, design thinking | `instructions/` |
| Session reports (`session_YYYY-MM-DD_*.md`) | `.status/` |
| Decision notes, error records, patch logs | `.status/` |
| API response cache | `outputs/cache/<source>/<date>/` |
| Phase 2 script outputs | `outputs/phase2/` |
| Phase 3 candidate markdown files | `outputs/phase3/candidates/` |
| Temporary scripts, work files, diffs | `.scratch/` |
| API keys | `code/.apikeys` |

**Never** put `.py` files in `outputs/`. **Never** put outputs in `code/`.
**Never** put plans or instructions in `.status/` — that directory is for
after-the-fact records only.

---

## Reference schema (as of 2026-04-23)

Each process and task has a unified `references` array (replacing the old
`fundamental_references`/`recent_references` split). Every reference carries
a `roles` list drawn from this vocabulary:

```
historical   — curated landmark paper; protected, cannot be removed by scripts
review       — review article or meta-analysis
experiment   — primary empirical paper
dataset      — normative dataset or data paper
other        — book chapter, manual, etc.
unknown      — not yet classified (default for all non-historical refs)
```

Historical references were seeded from the curated landmark list on 2026-04-23.
All other existing references are currently `["unknown"]`; Phase 5 (human
review) assigns the correct roles. Scripts must refuse to remove a reference
whose `roles` contains `"historical"` without an explicit override flag.

---

## Path conventions

**Always use relative paths** in plans, instructions, and as default argument
values in scripts. The workspace root must not appear as a hardcoded absolute
Windows path (e.g., `C:\Users\name\Projects\my-repo`) anywhere in committed
files. This keeps the project portable to GitHub and other machines.

Runnable scripts accept a `--workspace` argument (default: current working
directory) and derive all paths from it:

```python
ws        = Path(args.workspace)
cache_dir = ws / args.cache_dir          # e.g. ws / "outputs/cache"
output    = ws / args.output_dir         # e.g. ws / "outputs/phase3/candidates"
```

When referencing files in documentation, use workspace-relative paths:
- Correct: `outputs/phase3/candidates/hed_response_inhibition.md`
- Wrong:   `<drive>:\<absolute>\<path>\outputs\...`

The `--workspace` default in scripts can be `"."` (current directory), which
works correctly when the script is run from the workspace root.

---

## Windows / Cowork sandbox file access

**Critical:** The Cowork Linux sandbox has two ways to read files, and they
do not always agree.

### Read tool (Windows native API)
- Always shows the current, correct file contents.
- Use for: reading `process_details.json`, `task_details.json`, any `.json`
  or `.md` in the workspace, any file just written by Write or Edit tool.

### Bash (`mcp__workspace__bash`)
- Reads files via a VirtioFS mount that may show a **stale cached snapshot**
  of files written by the Write or Edit tools.
- Use bash for: running Python scripts, arithmetic, counting lines, `diff`,
  `cp`, `wc`. Do NOT use bash `cat` to read workspace files for logic.
- If a bash Python import fails on a file you just edited with the Edit tool,
  rewrite the complete file via bash `cat > file << 'EOF' ... EOF` to force
  a cache refresh.

### Write vs Edit tool
- **Write tool**: creates or fully rewrites a file. Immediately visible to
  subsequent bash calls.
- **Edit tool**: makes a targeted diff-style change. May NOT be immediately
  visible to bash (stale snapshot). Prefer Write for new files; use Edit for
  small changes to existing files that bash does not need to read immediately.

### Rule of thumb
```
Read  workspace files  →  Read tool (Windows path)
Write workspace files  →  Write or Edit tool (Windows path)
Run code / system ops  →  bash (Linux path via mount)
Temporary work         →  bash writes to .scratch/ (immediately visible)
```

### Path translation
The workspace root maps to the Linux mount as:
```
<workspace-root>/  →  /sessions/<session-id>/mnt/<project-folder>/
```
The session ID and project folder name change between sessions. Use
`mcp__cowork__request_cowork_directory` if the exact mount path is needed.
For temporary files, write to `.scratch/` via the Windows Write tool or via
bash at the mount path.

---

## Session reporting

Every session that writes, moves, or deletes files must produce a session
report. Place it in `.status/` (which lives at the repository root,
`task-research/.status/`, *not* under `Claude-research/`; gitignored).
From the catalog workspace this is `../.status/`. Use a dated filename:

```
.status/session_YYYY-MM-DD_<short-topic>.md
```

Minimum content: what was done, what files changed, what decisions were made,
what is left for the next session.

Also write a thinking/design summary to `.status/` for any non-trivial
design decision, using the same date convention. These complement the session
report and explain the *why* behind choices.

---

## API keys

Keys live in `code/.apikeys` (one `KEY=value` line per key, git-ignored).
Environment variables take priority over the file. Scripts read them with:

```python
import os
key = os.environ.get("S2_API_KEY") or _read_apikeys_file("S2_API_KEY")
```

Current keys in use:
- `S2_API_KEY` — Semantic Scholar. Note: a free-tier key does NOT lift the
  search-endpoint rate limit; both keyed and unkeyed callers are capped at
  1 request/second. The key is still worth setting because it can help
  with auth-scoped endpoints and gives Semantic Scholar visibility into
  who is calling. The S2 client at `code/literature_search/clients/
  semanticscholar.py` enforces the 1 rps limit unconditionally.
- `NCBI_API_KEY` — NCBI E-utilities (Phase 3 uses Europe PMC instead, so
  this is not currently used by Phase 3 scripts)
- `OPENALEX_MAILTO` — polite-pool email for both Crossref and OpenAlex.
  Default `hedannotation@gmail.com`. Same value used across all HED
  metadata repos. Sent as `mailto=` URL parameter on every Crossref /
  OpenAlex call to opt into the polite pool (faster, more reliable
  rate limits; free, no signup beyond providing the address).

Never log or print key values. Never hardcode them in source files.

---

## Cache convention (cross-repo)

`.status/cache_convention.md` defines the on-disk cache layout shared
across all HED metadata repositories (this repo, `openneuro-metadata`,
and any future ones). When writing a new client module or script that
hits Crossref / OpenAlex / Europe PMC / Semantic Scholar / Unpaywall,
read that file before deciding where cache files go. In one line: the
cache root is resolved as `--cache-dir` arg → `$HED_CACHE_DIR` env var
→ `outputs/cache/`. Hard-coded cache paths in committed code are
forbidden.

---

## Core data files — handling rules

`process_details.json` and `task_details.json` are the canonical catalog
sources. Before any script writes to them:

1. Read the current version with the Read tool.
2. Stage the output in `.scratch/` and verify it parses as valid JSON.
3. Verify process/task counts match expectations.
4. Copy to root only after verification.
5. Write a dated decision note to `.status/` describing what changed and why.

Scripts must never silently overwrite these files. Use explicit `--write`
or `--write-back` flags; dry-run should be the default.

---

## .scratch/ usage

`.scratch/` is the designated dump for:
- Temporary Python scripts written for one-off checks
- Intermediate JSON files produced during multi-step data fixes
- Diff outputs, exploratory queries, test fixtures

**Rules:**
- Claude should write all temporary files here, not in `outputs/` or `code/`.
- Contents are disposable — never depend on a `.scratch/` file persisting
  between sessions.
- Do not commit `.scratch/` contents to git.
- Claude should not accumulate files in `.scratch/` across sessions; clean
  it up at the end of a session or at the start of the next one.

---

## Literature search workstream — quick reference

| Phase | Script | Output |
|---|---|---|
| 1 — Infrastructure | `code/literature_search/phase1_validate.py` | cache smoke-test |
| 2 — Triage existing refs | `code/literature_search/triage_existing_refs.py` | `.status/reference_triage_*.md` |
| 3 — Systematic search | `code/literature_search/phase3_search.py` | `outputs/phase3/candidates/*.md` |
| 5 — Human review | (manual) | KEEP/DROP marks in candidate files |
| 6 — publications.json | (future) | `publications.json`, `publication_links.json` |
| 7 — PDF acquisition | (future) | PDFs in sibling directory |
| 8 — JSON merge | (future) | updates to `process_details.json` |

Run scripts from the workspace root:
```
python code/literature_search/phase3_search.py --mode poc --write
```
