# Vendored opencite slice

This directory holds a small slice of code copied from the
[opencite](https://github.com/neuromechanist/opencite) project,
vendored under the terms of opencite's MIT licence.  See
`task-research/NOTICE.md` (at the repo root) for the licence text
and the copyright notice that the MIT licence requires us to
preserve.

## Why vendor

`plan_2026-05-19_rec1_v2.md` §3 evaluates opencite as a Python
dependency and chose vendoring for three reasons: (1) we only need
~400 lines of opencite, not the whole package; (2) opencite's
upstream priority-order for PDF acquisition differs from what HED
needs (see plan §3.4); (3) some of opencite's network code is
async, and we want all our network code to be sync + cache-aware so
it composes with the rest of the literature-search pipeline.

## What is and isn't here

Vendored, unchanged from upstream apart from the attribution header
on each file:

- `models.py` — only the `PDFLocation` and `IDSet` dataclasses
  (plus the `IDType` enum they reference).  We dropped opencite's
  `Paper`, `Author`, `Source`, `SearchResult`, and `CitationResult`
  — our own catalogue formats those concepts differently.
- `url_parsers.py` — the `parse_identifier` function, extracted
  from upstream `models.py`.
- `pmc_convert.py` — BioC JSON → Markdown converter.  This is the
  substantive contribution from opencite — 260 lines of section /
  figure / table / reference handling specific to NCBI's BioC
  schema, well-tested upstream, unrelated to PDF extraction.

NOT vendored:

- `clients/pmc.py` — upstream is async; we wrote a fresh sync
  client at `Claude-research/code/literature_search/clients/pmc.py`
  against the same PMC BioC REST endpoint.
- `convert.py` — opencite's PDF → Markdown wrapper uses markitdown
  (or markit-mistral).  We use [marker-pdf](https://github.com/VikParuchuri/marker)
  instead — meaningfully better quality on academic papers.  Our
  wrapper lives at
  `Claude-research/code/literature_search/convert.py` as our own
  code.  Same `convert_pdf(pdf_path) -> str` interface a future PR-E
  acquisition orchestrator can call.
- Everything else in opencite — `search.py`, `dedup.py`, `pdf.py`,
  `cli.py`, the rest of `clients/`, the formatters — out of scope.

## Refresh policy

Vendored code is NOT regenerated automatically.  To refresh:

1. Update your local opencite clone, note the new commit hash.
2. Read each vendored file alongside upstream and diff.
3. Apply any upstream improvements that make sense for us.
4. Update the per-file attribution header with the new commit hash.
5. Update `NOTICE.md` at the repo root.
6. Write a session note in `.status/` describing what changed and
   why.

Refresh is a deliberate maintainer action, not a CI task.

## Currently pinned to

opencite commit `3e784ddd067b75e73fd0c69e02e82142be1afe11`
(2026-05-06).
