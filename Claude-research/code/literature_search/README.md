# Literature Search — code/literature_search/

This directory contains the literature-search workstream code: API
clients, identity functions, the cache, and the per-phase scripts.

For setup and how-to-run-the-pipeline instructions, see the top-level
`README.md` at the repository root (`task-research/README.md`).

For the architectural plan that ties the phases together, see
`Claude-research/instructions/literature_search_plan_2026-04-21.md`.

---

## Directory layout (relative to workspace root, `Claude-research/`)

```
code/literature_search/
  identity.py            Pure functions: build_canonical_string, build_pub_id,
                         build_pdf_filename. No network, no I/O.
  test_identity.py       pytest-runnable tests: 15 fixture rows × 3 functions.
  cache.py               cache_get_or_fetch: date-stamped, idempotent disk cache.
  fos_map.py             Field-of-study mapping (OpenAlex / S2 categories).
  normalize.py           Reference normalization helpers.
  search_queries.py      Query builders for Phase 3 retrieval.
  rank_and_select.py     Phase 3 ranking and selection.
  present_candidates.py  Render Phase 3 candidates as markdown for review.
  triage_rules.py        Rule definitions for triaging existing references.
  triage_existing_refs.py  Phase 2 triage script.
  resolve_landmarks.py   Resolve historical landmarks from the curated list.
  apply_drops.py         Apply DROP marks from the human-review pass.

  phase1_validate.py     End-to-end Phase 1 validation (cache + identity).
  phase3_search.py       Phase 3 systematic search runner.

  migrate_references.py  ONE-OFF (already applied): unified-reference migration.
  patch_malformed.py     DEPRECATED one-off (already applied).
  _patch_triage_rules.py DEPRECATED one-off (already applied).

  clients/
    __init__.py
    openalex.py          OpenAlex Works API.
    crossref.py          CrossRef Works API.
    europepmc.py         Europe PMC search API.
    semanticscholar.py   Semantic Scholar Graph API.
    unpaywall.py         Unpaywall API.

  README.md              This file.
```

The cache lives at `outputs/cache/<source>/<YYYY-MM-DD>/<hash16>.json`,
not inside this directory. Cache is git-ignored.

---

## Running

All scripts are runnable from the workspace root (`Claude-research/`)
and accept `--workspace` (defaults to current directory). Examples:

```
# from Claude-research/
python code/literature_search/phase1_validate.py
python code/literature_search/phase3_search.py --mode poc --write
pytest code/literature_search/test_identity.py -v
```

A second run on the same day costs zero network calls (responses cached).

See the top-level README for full per-phase instructions.

---

## Design summary

### pub_id and canonical_string

Every publication has a stable identifier: `pub_<8-hex-chars>`, where
the 8 hex chars are the first 8 characters of SHA-1 over a deterministic
*canonical string* derived from metadata alone:

```
canonical = last_name_lc_az + year_4digit + title_lc_az0-9
canonical = canonical[:100]          (may cut mid-word)
pub_id    = "pub_" + sha1(canonical)[:8]
```

Because the hash is metadata-only (never based on DOI, PMID, or OpenAlex
id), discovering a DOI *after* a record is created does not change the
`pub_id`. This is the DOI-discovered-later invariant tested in
`phase1_validate.py`.

### PDF filename

```
<LastName>_<Year>_<CamelCaseTitle>_<hash8>.pdf
```

The `<hash8>` tail is the same 8 hex chars as `pub_id[-8:]`, so any PDF
in the sibling `HED-PDFs/` directory maps back to its catalog record by
a single substring search in `publications.json` (when that file
exists).

### Cache

Each API call is cached under
`outputs/cache/<source>/<YYYY-MM-DD>/<sha1_16hex>.json`. Caches are
immutable once written; a fresh date produces new files.

---

## What this directory does NOT do

- No PDF downloads (Phase 7).
- No Zotero interaction.
- No modifications to `publications.json` or `publication_links.json`
  (Phase 6, future).
- No write to `process_details.json` or `task_details.json` outside of
  the historical migration scripts noted above.
