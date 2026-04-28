# Phase 1 Sonnet instructions — thinking summary

**Date:** 2026-04-21
**Context:** Follow-up to `literature_search_plan_2026-04-21.md` and
`pdf_naming_thinking_2026-04-21.md`. The user selected Path A (write a
detailed Sonnet execution spec for Phase 1 infrastructure). This note
records why the instructions doc is shaped the way it is.

## The problem

The parent plan is ~30 KB of architecture and design. Handing that to a
Sonnet session unmodified is the classic mistake — Sonnet needs a
*bounded* task description with explicit success criteria, not the whole
design. But strip it down too far and Sonnet reinvents decisions we
already made (DOI-priority vs. metadata-only hash, nested paths vs. year
folders, etc.) with no awareness of the prior work.

The instructions doc's job is to be the bridge: bounded scope, explicit
success criteria, clear pointers back to the plan for the "why".

## Scope choice: primitives + validation, nothing else

Phase 1 is **infrastructure only**. Five concrete deliverables:

1. `identity.py` — pure functions (`build_canonical_string`,
   `build_pub_id`, `build_pdf_filename`).
2. `test_identity.py` — 15 fixtures × 3 functions = 45 assertions.
3. `cache.py` — one function (`cache_get_or_fetch`) plus helpers.
4. Five thin API clients (`clients/<source>.py`).
5. `phase1_validate.py` — prove the primitives work end-to-end on 5
   known papers with known DOIs.

No searching, no ranking, no Zotero, no PDF download, no schema writes.
Those are later phases with their own decisions.

The reason I drew the scope line here rather than at "also do the first
search" is: the primitives are easy to test in isolation (45 pytest
assertions) and any bugs in them cascade to every later phase. Catching
them before the first real search is cheap; catching them after means
re-running search + re-minting pub_ids.

## The 15-row fixture table — why these rows

The table in sub-phase 1.2 is the heart of the doc. Each row exercises
a specific edge case:

- Row 1 (Badre 2012) — baseline happy path; canonical is hand-computable.
- Rows 2–5 (Stroop, Eriksen, Posner, Miller) — pre-DOI era papers, short
  titles, leading articles. Covers "does the folding rule work on old
  papers".
- Row 6 (Schönberg) — accented family name. Catches missing
  `unicodedata.normalize('NFKD', ...)`.
- Row 7 (O'Keefe) — apostrophe in family name. Catches regex over-matching.
- Row 8 (van der Berg) — compound particle. Catches splitting on spaces
  for LastName TitleCasing.
- Row 9 (de Fockert) — similar compound; also a more common name pattern.
- Row 10 (Wagenmakers, fMRI/EEG/ADHD) — explicit acronym preservation
  test. If the filename comes out `Fmri`, `Eeg`, `Adhd`, the rule in
  §11.7 is broken.
- Row 11 (400-char title) — hits both truncations: the canonical string
  cuts at 100 chars opaque, the filename cuts at 100 chars on a token
  boundary. They **should give different visible truncation points**.
- Rows 12–14 — the three "empty after fold" cases (no author, no year,
  non-Latin title). Spellings for canonical vs filename differ by
  design (`anonymous` vs `Anonymous`, `0000` vs `nodate`) — the
  assertions catch accidental normalization drift.
- Row 15 — **the determinism check.** Same inputs as row 1 but a
  separate invocation. Must produce byte-for-byte identical outputs.
  This is the DOI-discovered-later invariant translated to a
  unit-testable form.

If Sonnet's implementation passes all 15 rows for all 3 functions, I'm
confident the primitives are correct.

## Seven validation papers — why these seven

Originally five, all pre-2012. The user flagged the gap: no modern
papers means the validation run never exercises the code paths that
only fire on recent DOIs (Unpaywall OA hit, populated ORCID/funder
metadata, rich Semantic Scholar response). Added two modern OA papers.
Final set:

- **Badre 2012** — flagship Trends in Cognitive Sciences paper; heavily
  indexed across all 5 APIs. If this doesn't round-trip, something is
  wrong with the client code, not the paper.
- **Stroop 1935** — pre-DOI era. DOI exists now (`10.1037/h0054651`) but
  indexing is inconsistent. Exercises "what do the APIs do with
  genuinely old papers".
- **Eriksen & Eriksen 1974** — published in Perception & Psychophysics;
  Springer DOI. Confirms non-Elsevier publisher path works.
- **Posner 1980** — Taylor & Francis DOI. Different publisher again.
- **Miller 1956** — Psychological Review. APA publisher. Covers the fourth
  major publisher we'll hit in practice.
- **Gorgolewski et al. 2016** — BIDS paper, *Scientific Data* 3:160044.
  Modern OA. Directly relevant to HED (HED extends BIDS). Tests:
  Unpaywall returns `is_oa=True` with a populated OA URL (which every
  prior paper fails to exercise), many-author metadata structure,
  Scientific Data DOI prefix, rich post-2015 CrossRef registration.
- **Pernet et al. 2019** — EEG-BIDS, *Scientific Data* 6:103. Modern OA,
  directly in HED's electrophysiology domain. Tests the post-2018
  CrossRef schema (ORCID, funders, checklist fields) that the 2016
  paper may still be missing.

The modern-OA additions have one extra assertion attached (Unpaywall
`is_oa=True` with a populated `best_oa_location.url_for_pdf`) — this
makes them dedicated canaries for the OA path. The five historical
papers don't assert on Unpaywall at all; most will return null and
that's the correct behavior.

Seven papers is still small enough that the full cross-source trace
fits in the session report, and it gives us publisher coverage across
Elsevier, APA, Springer 1974-imprint, Taylor & Francis, and two
Nature/Scientific Data DOIs — a realistic spread.

## Why the cache layer is in Phase 1

The cache isn't Phase 1's **goal** — but every later phase needs it, and
writing it without a real caller leads to premature abstraction. Phase
1's validation script is a real caller with 5 × 5 = 25 distinct cache
keys. That's enough to shake out the hash-collision detection, the
date-bucketed layout, and the "what happens on second run" behavior.

## What I deliberately left out

- **No normalization/merge across sources.** That's Phase 3 and has its
  own design decisions (field precedence, conflict resolution, what to
  do when CrossRef says one year and OpenAlex says another). Phase 1
  returns raw source JSON with three underscore-prefixed convenience
  keys and that's it.
- **No ranking.** No venue tier lookup, no quality score, no composite.
- **No PDF acquisition.** `build_pdf_filename` returns a string; nothing
  downloads anything. The filename is proof-of-concept only.
- **No `pub_id` uniqueness check against an existing store.** There is
  no existing `publications.json` yet. A TODO comment in the relevant
  place, no more.
- **No hash-collision widening logic.** The plan allows bumping from 8
  to 10 hex chars on collision, but Phase 1 has 5 papers and the math
  says collision probability is astronomical. Phase 6 revisits.
- **No argparse beyond a simple `--cache-dir`.** The script is called
  once by the validator, not composed into a larger CLI. If a later
  session wants to break these into a CLI, it can.

## Stylistic choices

- **Plain `assert` + `pytest.mark.parametrize`** — not `unittest`.
  Matches the style of `outputs/resolve_citations.py` from the prior
  enrichment phase. Keeps fixtures local, readable in one screen.
- **Stdlib + `requests` only** — explicitly no `pyalex`,
  `crossrefapi`, `requests-cache`, `pydantic`, `click`, `rich`. The
  user has stated a preference against over-engineering. For a ~600-LOC
  workstream, those libs add more reading burden than they save code.
- **Normalized return shape with three underscore keys** (`_source`,
  `_doi`, `_fetched_on`) — lightweight convention, not a class. The
  merger in Phase 3 will adopt whatever structured form makes sense
  there; Phase 1 keeps source JSON essentially intact.
- **One line per API call log**, not JSON-structured logging. Phase 1
  is read by a human in the session report, not ingested by log
  analysis.

## Questions Phase 1 might surface

The doc's "Questions to raise" section lists four classes of
interrupt-worthy findings:

1. A DOI from my paper list is wrong. I verified against my memory; if
   wrong, the fix is one character in the table.
2. A real paper's canonical string truncates in a way that loses a
   disambiguator (e.g., a "second edition" suffix past char 100). If
   this happens, §11.7 rules may need to change. Flag it, don't silently
   pick a different truncation.
3. A required API host is unreachable and the workaround would require
   a new pattern. Use the host-script fallback pattern, or stop.
4. An API returns a shape that doesn't fit the normalized dict
   convention. The likely offender is Europe PMC which returns a result
   list for search-style queries; the instructions specify DOI
   lookup, which *should* return a single paper, but if it comes back
   as a list the client needs to handle it.

I flagged these so Sonnet doesn't invent answers for them.

## What happens after Phase 1

The doc explicitly stops at "write session report". No Phase 2. The
user reviews the primitives, the validation output, and the session
report, then decides whether to:

- Proceed to Phase 2 (triage of existing refs against OpenAlex Topic
  crosswalk).
- Resolve §12 open items in the parent plan (landmark seed size, venue
  tier review, 14 unresolved historical refs, dual-cited refs) before
  any further execution.
- Or revise the Phase 1 primitives if something came out wrong.

The review gate between phases is deliberate. It's the way we catch
early design drift before it cascades.
