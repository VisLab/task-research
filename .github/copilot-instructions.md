# Task research developer instructions

> **Local environment**: If `.status/local-environment.md` exists in the repository root, read it first — it contains machine-specific shell, OS, and venv details (e.g. Windows/PowerShell vs Linux/bash) that override the generic commands shown here.

## Code style

- Google-style docstrings; use `Parameters:` not `Args:`
- Line length: 120 characters (configured in `pyproject.toml`)
- Markdown headers use sentence case: capitalize only the first word (and proper nouns/acronyms)
- When creating work summaries, place them in `.status/` at the repository root

## Project overview

This repository supports research into categorizing cognitive tasks and processes, with the goal of producing a curated crosswalk between task-level descriptions and standardized vocabularies. The primary application domain is HED (Hierarchical Event Descriptors) annotation of neuroimaging and behavioral datasets.

### Research goals

1. Identify and categorize the cognitive tasks and processes used in experimental neuroscience and psychology
2. Map tasks to established taxonomies: OpenAlex Topics, Cognitive Atlas concepts, and HED schema terms
3. Assess coverage gaps and produce human-reviewable reports to guide HED schema development

### Data sources

- **[OpenAlex](https://openalex.org/)**: Open bibliometric database with a four-level taxonomy (Domain → Field → Subfield → Topic) and legacy Concepts vocabulary. API access requires no key; passing an email uses the polite pool (~10 req/s).
- **[Cognitive Atlas](https://www.cognitiveatlas.org/)**: Community ontology of cognitive tasks and mental processes (tasks, concepts, conditions, and their relations).
- **Google searches**: Manual research notes in `GoogleSearches/` documenting task definitions, variations, and literature references.
- **Claude-research/**: AI-assisted structured analyses of tasks, concepts, and crosswalks.

### Repository layout

```
OpenAlex/               - OpenAlex pull scripts, raw data, normalized data, crosswalks
  pull_openalex.py      - Fetch taxonomy + concepts from the OpenAlex API
  normalize.py          - Reshape raw pulls into analysis-friendly JSON
  crosswalk.py          - Score and map HED core concepts → OpenAlex Topics
  outputs_tmp_sim.py    - Similarity output exploration (temporary)
  raw/                  - Immutable date-stamped API pulls (not tracked by git)
  normalized/           - Rebuilt from raw/ on demand
  crosswalks/           - Curated concept-to-topic mappings
  reports/              - Gap assessments and crosswalk statistics
GoogleSearches/         - Manual research notes per task or concept
Claude-research/        - AI-assisted structured analyses and inventories
  original/             - First-pass outputs from Claude
  original_2/           - Second-pass outputs
  original_3/           - Third-pass outputs
  outputs/              - Final curated outputs
.status/                - Work-in-progress notes, environment docs, thinking docs
```

## Key scripts

### `OpenAlex/pull_openalex.py`

Pulls the full OpenAlex taxonomy (domains, fields, subfields, topics) and legacy Concepts for psychology/neuroscience subtrees. Writes date-stamped JSON to `raw/` so pulls are immutable and diffable. Re-running on the same date overwrites that day's files; running on a later date creates new files alongside.

```powershell
# From H:\Research\TaskResearch\
python OpenAlex/pull_openalex.py --email hedannotation@gmail.com
```

### `OpenAlex/normalize.py`

Reshapes raw pulls into analysis-friendly structures. Reads `raw/current.json` to find the active date stamp.

```powershell
python OpenAlex/normalize.py
```

### `OpenAlex/crosswalk.py`

Scores and maps HED core concepts to OpenAlex Topics using name matching, keyword overlap, and Jaccard similarity. Writes candidate mappings to `crosswalks/`. Thresholds (`TOP_N`, `MIN_SCORE`) are tunable at the top of the file.

```powershell
python OpenAlex/crosswalk.py
```

## Development environment

### Setup

Activate the virtual environment before running any commands. See `.status/local-environment.md` for OS-specific activation syntax.

```powershell
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### Dependencies

- Python 3.10+ required
- Core: `requests>=2.28.0`
- Dev extras: `ruff`, `typos`, `mdformat`; install with `pip install -e ".[dev]"`

### Linting and formatting

```powershell
# Check for lint errors
ruff check OpenAlex/

# Check formatting
ruff format --check OpenAlex/

# Auto-fix lint + format
ruff check --fix OpenAlex/
ruff format OpenAlex/

# Spell check (see pyproject.toml [tool.typos] for exclusions)
typos
```

Ruff rules and line length (120) are configured in `pyproject.toml` under `[tool.ruff]`.

### Running tests

This repository currently uses ad hoc script execution rather than a formal test suite. Validate scripts by running them end-to-end and checking output files under `OpenAlex/normalized/`, `OpenAlex/crosswalks/`, and `OpenAlex/reports/`.

## Data conventions

- **Raw data is immutable.** Never modify files under `OpenAlex/raw/` directly. Re-pull to update.
- **`raw/current.json`** is the pointer to the active date stamp; downstream scripts use it to locate the latest pull without hardcoding dates.
- **Normalized and crosswalk files are rebuild targets** — they can always be regenerated from `raw/`. Treat them as derived artifacts.
- **Scores are approximate.** Crosswalk scoring (`crosswalk.py`) is deliberately simple and inspectable; all output is intended for human review before being promoted to curated mappings.
- **JSON files in `Claude-research/`** contain structured inventories (task details, concept details, process details) — treat these as authoritative catalogues that evolve with research.

## Common pitfalls to avoid

- Always activate the virtual environment before running Python/pip commands
- Check `.status/local-environment.md` for shell-specific command syntax (PowerShell vs bash)
- Do not modify files under `OpenAlex/raw/` — create a new dated pull instead
- `raw/current.json` must be updated after a new pull if you want downstream scripts to use the new data
- OpenAlex rate limits: stay in the polite pool by passing `--email`; do not parallelize requests aggressively
