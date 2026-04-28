# Task: Literature Search — Phase 2 triage of existing references

**Date:** 2026-04-22
**Goal:** Triage every reference currently in `process_details.json` and
`task_details.json` against mechanical keep/drop/review rules, with the
landmark override list as unconditional keeps. Produce one human-review
artifact (`.status/reference_triage_<date>.md`) the user reviews before
Phase 3. Phase 2 **does not mutate** `process_details.json` or
`task_details.json` — the review artifact is the deliverable, and
deletions happen in a later gated session after sign-off.

This is **Phase 2** of the literature-search workstream. Parent plan:
`.status/literature_search_plan_2026-04-21.md`. Phase 1 (infrastructure +
primitives) is complete — see
`.status/session_2026-04-21_literature_search_phase1.md`. Phases 3–9 are
separate Sonnet sessions and are not part of this task.

---

## Context

You are working on the HED (Hierarchical Event Descriptor) cognitive
process catalog. Workspace root: `H:\Research\TaskResearch\Claude-research\`.

`process_details.json` holds ≈172 processes in 19 categories; each
process carries `fundamental_references[]` and `recent_references[]`
arrays. `task_details.json` holds ≈103 tasks with an analogous
reference array shape. Total reference objects: ≈1,150. The reference
shape is:

```json
{
  "title": "...",
  "journal": "...",
  "year": 2004,
  "citation_string": "Bouton (2004) *Learning & Memory* 11:485–494",
  "authors": "Bouton, M. E.",
  "venue": "Learning & Memory",
  "venue_type": "journal",      // "journal" | "book_chapter" | "report" | null
  "volume": "11", "issue": "...", "pages": "485–494",
  "doi": "10.1101/lm.78804",    // may be null
  "openalex_id": null, "pmid": null, "url": null,
  "source": "crossref",         // provenance of the enrichment
  "confidence": "high",         // "high" | "medium" | "low" | "none"
  "verified_on": "2026-04-20"
}
```

The parent plan §1 documents why the current set is unsatisfactory:
too many test manuals, textbook chapters, and low-quality venues. Phase
2 makes the first pass at that cleanup.

Before coding, **read these documents in full**:

1. `.status/literature_search_plan_2026-04-21.md` §8 Phase 2, §5
   (publisher/venue filter), §7.3 (landmark override list). These are
   authoritative for the triage rules.
2. `.status/landmark_refs_2026-04-22.md` — the sign-off landmark list.
   Phase 2 will consume this via the JSON produced in sub-phase 2.1.
3. `.status/session_2026-04-21_literature_search_phase1.md` —
   infrastructure you will reuse. Pay attention to the note that
   Semantic Scholar returns `year=1992` for Stroop 1935 (Internet
   Archive digitization year); we trust OpenAlex/CrossRef for year, not
   S2.
4. `outputs/literature_search/README.md` and the module docstrings in
   `identity.py`, `cache.py`, and `clients/*.py` — do not reimplement
   primitives.

If any of these contradict this instructions doc, **stop and write a
dated decision note to `.status/`** rather than resolving the
contradiction on your own.

---

## What specifically needs to happen

### Sub-phase 2.1: Resolve landmark DOIs → `landmark_refs.json`

The clean landmark MD is the source of truth but it is not
machine-readable. Build a small script that parses it, resolves each
entry's DOI, verifies cross-source agreement, and writes the JSON Phase
2 triage will consume.

Create `outputs/literature_search/resolve_landmarks.py`. Target ~120
lines. Standard library + `requests`. Reuses `cache.cache_get_or_fetch`
and the CrossRef and OpenAlex clients from Phase 1.

Behavior:

1. Parse `.status/landmark_refs_2026-04-22.md`. Two tables matter:
   - §1.1 through §1.19 (process landmarks, keyed by `process_id`).
   - §2 (task landmarks, keyed by `task_id`).
   For each row extract `id`, `citation` (e.g. `"Eriksen & Eriksen
   (1974)"`), `title_and_venue` (the full italicized title-and-venue
   cell), `confidence` (`H`/`M`/`L`).
2. Extract a clean `(first_author_family, year, title)` tuple from each
   row using the same token logic as `identity.build_canonical_string`.
   - First author family: first capitalized surname before `&`, `et al.`,
     or the year parenthesis.
   - Year: the 4-digit integer inside parentheses.
   - Title: the quoted portion before the first `*venue*` span. If the
     row uses `*venue*` with no quoted title (some task rows do), use
     the authors' surname as a fallback title fragment and emit a
     `title_missing_in_md` warning to stderr.
3. For each entry, call CrossRef with a search query (via a new
   `lookup_by_query` function added to `clients/crossref.py` — see
   below; or, if you prefer, a standalone helper in
   `resolve_landmarks.py` that uses the same throttle/retry pattern).
   Query: `author: <family>, title: <first 5 title words>`,
   `filter=from-pub-date:<year>,until-pub-date:<year>`. Take the top-1
   result. Confirm first-author surname and year match exactly.
4. Cross-verify with OpenAlex via `clients/openalex.py.lookup_by_doi`
   on the CrossRef-returned DOI. If OpenAlex year differs from CrossRef
   year, emit a warning and keep the CrossRef value (CrossRef is
   authoritative for DOI metadata).
5. Mint each entry's `pub_id` via
   `identity.build_pub_id(first_author_family, year, title)` using the
   canonicalized title from CrossRef (not the MD title — the MD may
   truncate or abbreviate).
6. Write `outputs/literature_search/landmark_refs.json` with the schema
   from Appendix C of `landmark_refs_2026-04-22.md`. Additionally record
   the pub_id and a `resolution_status` field
   (`"resolved"` | `"ambiguous"` | `"not_found"`).

**Extending the CrossRef client.** If you add a new method, keep it
small and put it in `clients/crossref.py`. Proposed signature:

```python
def lookup_by_query(
    cache_dir: Path,
    author_family: str,
    title_terms: str,          # e.g. "effects of noise letters"
    year: int,
    email: str = "hedannotation@gmail.com",
) -> dict | None:
    """Query CrossRef by author + title terms + year. Return the top
    result's normalized metadata dict or None if no match. Uses
    cache_get_or_fetch under the hood; cache key is
    'crossref_query|<author>|<title_terms>|<year>'."""
```

Cache this by the composite key — the same query on the same day must
cost zero network calls on rerun.

**Output sanity test.** The script prints a summary table:

```
Landmark resolution — 2026-04-22

n total: <count>
n resolved (cross-source agreement): <count>
n ambiguous (one source unsure): <count>
n not found: <count>

Warnings:
  - hedtsk_foo_bar: title_missing_in_md
  - hed_baz: openalex year 1996 != crossref year 1995; kept crossref
```

Ambiguous and not-found entries are **not** silently dropped — they go
into the JSON with `resolution_status: "ambiguous"` / `"not_found"` and
`doi: null`. Phase 2 triage treats them as landmarks anyway (the
landmark status is an editorial decision, not contingent on CrossRef
agreeing). An explicit `"ambiguous"` entry is a flag for the user to
chase separately, not grounds to skip a keep.

**Do not** require 100% resolution before proceeding. Some old papers
(e.g. pre-1950, pre-DOI) will come back `not_found`; this is expected
and documented in Phase 1's session report.

### Sub-phase 2.2: Build the triage allowlists and denylists

Create `outputs/literature_search/triage_rules.py`. Target ~150 lines,
standard library only. This module encodes the decisions from plan
§5.1, §5.2, §5.3. Do **not** embed these lists in the triage script
directly — they live here so they are reviewable as data and easy to
revise.

Structure:

```python
PUBLISHER_TIERS = {
    # Plan §5.1
    "10.1016": "A",    # Elsevier
    "10.1007": "A",    # Springer Nature
    "10.1038": "A",    # Nature publishing
    "10.1002": "A",    # Wiley
    "10.1037": "A",    # APA
    "10.1523": "A",    # SfN
    "10.1073": "A",    # PNAS
    "10.1126": "A",    # AAAS
    "10.1093": "A",    # OUP
    "10.1017": "A",    # Cambridge
    "10.1146": "A",    # Annual Reviews
    "10.1177": "B",    # SAGE
    "10.1080": "B",    # Taylor & Francis
    "10.1371": "B",    # PLOS
    "10.3389": "B",    # Frontiers (with journal-level caveat)
    "10.1101": "B",    # bioRxiv (preprint caveat)
    "10.3758": "B",    # Psychonomic
}

VENUE_TIERS = {
    "flagship": { ...set of canonical venue strings... },
    "mainstream": { ... },
    "specialty": { ... },
    "low_or_excluded": { ... },   # start empty; populate from what we find
}

# Regexes that mark a reference as a test manual or handbook, not a paper.
TEST_MANUAL_PATTERNS = [
    r"\bmanual\b",
    r"\bhandbook\b",
    r"WAIS(-[IVX]+)?\b",
    r"WMS(-[IVX]+)?\b",
    r"Delis-Kaplan",
    r"IAPS\b",                 # stimuli set, cited as a normative report
    r"KDEF\b",
    r"Raven'?s? Progressive Matrices\s+Manual",
]

# Technical report default: drop, unless NIMH or DARPA and highly-cited.
# Phase 2 can't check citation counts without hitting OpenAlex for each;
# the conservative rule is to mark any "report" entry REVIEW (not DROP)
# so the user can override.

LANDMARK_IDS = set()   # filled at runtime from landmark_refs.json
```

Two helpers live here:

```python
def classify_venue(venue_str: str | None) -> str:
    """Return 'flagship' | 'mainstream' | 'specialty' | 'low_or_excluded'
    | 'unknown'. Matching is case-insensitive, trimmed, with common
    punctuation removed. The underlying comparison uses a preprocessed
    set built from VENUE_TIERS at import time."""

def publisher_tier_from_doi(doi: str | None) -> str | None:
    """Return 'A' | 'B' | 'C' | None based on DOI prefix."""
```

**Venue-allowlist bootstrap strategy.** The plan lists ~30 venues by
name. Do not hand-enter all possible spellings. Instead, the test at
the end of this sub-phase **reads every unique `venue` value from
`process_details.json` and `task_details.json`**, then prints a table
of (venue_string → `classify_venue` output). Review the table by hand
before moving to sub-phase 2.3; expect 5-15 "unknown" venues that are
actually flagship or mainstream journals under a different spelling
(e.g. `"Journal of Experimental Psychology: General"` vs.
`"J Exp Psychol Gen"`). Add the aliases to `VENUE_TIERS` before
proceeding. This is the right place to spend 30 minutes rather than in
the triage itself.

### Sub-phase 2.3: Build `triage_existing_refs.py`

Create `outputs/literature_search/triage_existing_refs.py`. Target
~250 lines. This is the main Phase 2 script.

What it does, end to end:

1. Load `process_details.json` and `task_details.json` via the **Read
   tool** pattern (see the virtiofs rules section below). The script
   reads from disk once at start, never writes back.
2. Load `outputs/literature_search/landmark_refs.json`.
3. Build a set of landmark `(owner_id, citation_key)` pairs where
   `owner_id` is the process_id or task_id and `citation_key` is the
   pub_id minted in sub-phase 2.1. For each existing reference in the
   two JSON files, compute its pub_id via
   `identity.build_pub_id(first_author_family, year, title)` using the
   reference's existing fields (first author parsed from `authors`).
4. For every (owner_id, array_name, index, ref) tuple, assign a triage
   decision by applying these rules **in order** (first match wins):

   a. **KEEP — landmark override.** If
      `(owner_id, pub_id) in landmark_set`, decision = KEEP with
      reason = `landmark_override`.

   b. **DROP — test manual / handbook.** If any `TEST_MANUAL_PATTERNS`
      regex matches `venue`, `journal`, `citation_string`, or `title`,
      decision = DROP with reason = `test_manual`.

   c. **DROP — year too old, not a landmark.** If `year is not None and
      year < 1960` AND not a landmark, decision = DROP with reason =
      `pre_1960_non_landmark`. (This implements plan §8 Phase 2
      rule 2c.)

   d. **REVIEW — technical report.** If `venue_type == "report"`,
      decision = REVIEW with reason = `technical_report_needs_citation_check`.

   e. **KEEP — flagship or mainstream venue.** If
      `classify_venue(venue)` ∈ {`"flagship"`, `"mainstream"`},
      decision = KEEP with reason = `venue_in_allowlist_<tier>`.

   f. **KEEP — Tier A or B publisher.** If DOI is present and
      `publisher_tier_from_doi(doi)` ∈ {`"A"`, `"B"`}, decision = KEEP
      with reason = `publisher_tier_<A|B>`.

   g. **REVIEW — book chapter, not landmark.** If
      `venue_type == "book_chapter"` and not a landmark, decision =
      REVIEW with reason = `book_chapter_non_landmark`.

   h. **REVIEW — unresolved / unknown venue.** If `confidence == "none"`
      or `classify_venue == "unknown"`, decision = REVIEW with reason
      = `unknown_venue`.

   i. **Default.** REVIEW with reason = `default_needs_review`.

   Note the deliberate asymmetry: we REVIEW rather than DROP most
   uncertain cases. The triage is a draft for the user to accept or
   override; false drops are worse than false reviews.

5. Produce `.status/reference_triage_<today>.md`. See sub-phase 2.4 for
   the exact format.

6. Print a one-screen summary to stdout:

   ```
   Phase 2 triage — <date>
   processes scanned: 172
   tasks scanned: 103
   references scanned: <total>
   decisions:
     KEEP (landmark):   <n>
     KEEP (allowlist):  <n>
     KEEP (publisher):  <n>
     DROP (manual):     <n>
     DROP (pre_1960):   <n>
     REVIEW (report):   <n>
     REVIEW (chapter):  <n>
     REVIEW (unknown):  <n>
     REVIEW (default):  <n>
   landmark coverage: <n_with_landmark_present> / <n_process_landmarks_in_json>
   ```

   The `landmark coverage` line is a sanity check: each process_id in
   `landmark_refs.json` should appear in the triage output with at
   least one KEEP (landmark) decision, unless the existing JSON does
   not yet contain that landmark paper. Print a warning for any
   landmark id that has zero references matching its pub_id in the
   existing data — those are slots Phase 3 will need to fill.

**Determinism.** A rerun on the same day, against the same input
files, must produce byte-identical output Markdown. Sort by
`(owner_id, array_name, index)` everywhere. Do not use set ordering or
dict-key ordering for any externally visible output.

**No network calls in this sub-phase.** All DOIs, years, and venues
come from the already-enriched JSON files. The only network work in
Phase 2 is sub-phase 2.1 (landmark DOI resolution).

### Sub-phase 2.4: The review artifact format

Write `.status/reference_triage_<YYYY-MM-DD>.md` with exactly this
shape:

```markdown
# Reference triage — <date>

Source: process_details.json, task_details.json (snapshot of <date>).
Landmark override list: outputs/literature_search/landmark_refs.json
(<n> entries).

Total references: <n>
  KEEP:   <n_keep>
  DROP:   <n_drop>
  REVIEW: <n_review>

## How to review

This file is the Phase 2 deliverable. Nothing in the JSON files has
changed yet. For each DROP row, review the reason column; uncheck the
box if you want the reference retained. For each REVIEW row, tick
KEEP or DROP. Do **not** edit the KEEP rows unless the reason looks
wrong. A follow-up session (not this one) will apply the approved
drops after your sign-off.

## 1. Proposed drops

| # | owner_id | array | idx | citation | venue | year | reason | status |
|---|---|---|---|---|---|---|---|---|
| 1 | hed_extinction | fundamental_references | 0 | Pavlov (1927) *Conditioned Reflexes* | (book) | 1927 | pre_1960_non_landmark | [ ] DROP |
| 2 | ... |

(one row per drop, sorted by owner_id then array then idx)

## 2. Items flagged for review

| # | owner_id | array | idx | citation | venue | year | reason | keep? |
|---|---|---|---|---|---|---|---|---|
| 1 | hed_foo | recent_references | 2 | Smith (2015) *Unknown Venue* 1:1-5 | Unknown Venue | 2015 | unknown_venue | [ ] KEEP [ ] DROP |
| ...

## 3. Confirmed keeps (for audit)

| # | owner_id | array | idx | citation | venue | year | reason |
|---|---|---|---|---|---|---|---|
| 1 | hed_response_conflict | fundamental_references | 0 | Eriksen & Eriksen (1974) *Percept Psychophys* | Perception & Psychophysics | 1974 | landmark_override |
| ...
```

The three sections are independently sortable. Section 3 is long;
that's fine — the user scans it rather than reads it line by line.

Table rows use GitHub-flavored Markdown and must not wrap inside cells
(escape or truncate long citation strings to ≤ 90 chars). Truncation
uses `…` as the last character and preserves the publication year.

### Sub-phase 2.5: Landmark gap report

After the main triage, write a second section in the review file:

```markdown
## 4. Landmark gaps

Landmark papers from landmark_refs.json whose pub_id does not appear
anywhere in the current process_details.json / task_details.json.
These are slots Phase 3 will need to fill with the systematic search.

| owner_id | kind | landmark citation | pub_id |
|---|---|---|---|
| hed_selective_attention | process | Posner (1980) | pub_xxxxxxxx |
| ...
```

This is mechanical: iterate the landmark JSON, for each entry check
whether its pub_id appears in any reference's computed pub_id across
the two JSON files. If not, it's a gap. Expected gap count: maybe 30-60
(the landmark list is more ambitious than the current curation).

### Sub-phase 2.6: Write the Phase 2 session report

Write `.status/session_2026-04-22_literature_search_phase2.md`. Include:

- What was built (file list with line counts).
- Landmark resolution summary (from sub-phase 2.1).
- Venue-allowlist decisions made during sub-phase 2.2 (the 5–15
  "unknown" venues you resolved by hand, and what tier they went to).
- Headline triage counts by decision and reason.
- Any surprises: references that matched multiple rules, references
  with garbage `authors` fields that broke pub_id minting (use
  `"Unknown"` family and flag in the report — do not fail hard).
- Landmark gap count and a short list (top 10) of the most surprising
  gaps.
- Any plan deviations with rationale.
- List of follow-ups for Phase 3.

---

## CRITICAL: File access rules — virtiofs stale snapshot issue

**The bash sandbox sees a stale, potentially corrupted snapshot of
mounted workspace files.** This has bitten every prior session. Rules:

1. **ALWAYS use the Read tool** (with Windows paths like
   `H:\Research\TaskResearch\Claude-research\process_details.json`) to
   read `process_details.json`, `task_details.json`, and any file under
   `.status/`. Do NOT use bash `cat`, `head`, `tail`, or Python
   `open()` on mounted paths.
2. **ALWAYS use the Write tool** to write files under `.status/`.
3. **Ok to use bash** within `outputs/literature_search/` — that's the
   Cowork-session temp area and is not subject to the stale-snapshot
   issue. Your scripts live there; their input JSON must still come
   from the Read tool or from an in-script copy you first made into
   `outputs/literature_search/` via a Read → Write round-trip.
4. **If a JSON parse error occurs in bash** on a workspace file, it is
   almost certainly the stale snapshot (trailing null bytes). Read the
   file via the Read tool instead.

Phase 2 **does not modify** any workspace JSON (`process_details.json`,
`task_details.json`). You will create files under
`outputs/literature_search/` (bash-safe) and `.status/` (use Write
tool).

**Recommended loader pattern** — to avoid running scripts against stale
mounted JSON:

```python
# In your triage script, accept the JSON via a path argument, not by
# hard-coding the mounted Windows path. Then from the Sonnet session
# you:
# 1) Read tool → load process_details.json into memory
# 2) Write tool → write it to outputs/literature_search/_inputs/process_details.json
# 3) Run: python triage_existing_refs.py --input _inputs/process_details.json ...
# Step 3 uses bash and reads only from the bash-safe outputs tree.
```

The `_inputs/` subdirectory is added to `.gitignore`-style scope; don't
commit its contents. These are transient copies.

---

## File inventory

### Files you will create

Under `H:\Research\TaskResearch\Claude-research\outputs\literature_search\`:

- `resolve_landmarks.py` — sub-phase 2.1 entrypoint.
- `triage_rules.py` — publisher/venue allowlists and classifiers.
- `triage_existing_refs.py` — main Phase 2 script.
- `landmark_refs.json` — resolved landmark list (output of 2.1).
- `_inputs/process_details.json` — transient copy used by bash (optional but recommended).
- `_inputs/task_details.json` — transient copy used by bash (optional but recommended).
- (extend) `clients/crossref.py` — add `lookup_by_query` if you choose the in-client route; or skip if you put the helper inside `resolve_landmarks.py`.

Under `H:\Research\TaskResearch\Claude-research\.status\`:

- `reference_triage_<today>.md` — the human-review deliverable.
- `session_2026-04-22_literature_search_phase2.md` — session report.

### Files for reference (do not modify)

- `.status/literature_search_plan_2026-04-21.md` — parent plan.
- `.status/landmark_refs_2026-04-22.md` — sign-off landmark list.
- `.status/landmark_refs_proposed_2026-04-22.md` — review record (useful if a landmark parse is ambiguous and you need context).
- `.status/session_2026-04-21_literature_search_phase1.md` — Phase 1 session report.
- `outputs/literature_search/identity.py` — pub_id, canonical_string, PDF filename.
- `outputs/literature_search/cache.py` — `cache_get_or_fetch`.
- `outputs/literature_search/clients/{crossref,openalex,europepmc,semanticscholar,unpaywall}.py` — thin API clients.

### Files you will NOT modify in Phase 2

- `process_details.json` — Phase 8 mutates this after human review.
- `task_details.json` — same.
- `publications.json` — does not exist yet; created in Phase 6.
- Any file under `OpenAlex/`.
- Any Zotero preference, plugin, or SQLite database.

---

## Working conventions

- **Clean, flat Python.** Reuse Phase 1 primitives; do not rebuild
  them. Import from sibling modules (`from cache import
  cache_get_or_fetch` etc., matching the Phase 1 style).
- **Standard library + `requests` only.** No `pyalex`, no `pandas`, no
  `click`, no `rich`. Plain `argparse`, plain `json`, plain `logging`.
- **Triage rules live in `triage_rules.py`.** Do not inline venue
  strings or regexes in the main script.
- **Deterministic output.** Sort every externally visible collection
  by a stable key. A rerun on the same day produces byte-identical
  review Markdown.
- **No emojis** in code or markdown unless the user asks.
- **Cache everything networky.** Sub-phase 2.1 should cost zero
  network calls on rerun.
- **One stopping point.** After the review file and session report are
  written, stop. Do **not** start Phase 3.

---

## What is explicitly NOT part of Phase 2

These are tracked separately and are forbidden in this session:

1. **Mutating `process_details.json` or `task_details.json`.** The
   user-gated follow-up session applies approved drops. Your output is
   read-only for this phase.
2. **Systematic search** for new candidate references. Phase 3 does
   that.
3. **Ranking** or composite scoring of references. Phase 2 classifies;
   Phase 3 ranks.
4. **Any OpenAlex search endpoint.** Phase 2 uses only DOI lookup
   (CrossRef and OpenAlex, in sub-phase 2.1). No
   `/works?search=...`, no `/works?filter=title.search:...`.
5. **PDF acquisition or Zotero interaction.** Phase 6 and 7 handle
   those.
6. **Deciding borderline venues on your own.** When the venue
   allowlist returns `unknown`, the reference goes to REVIEW, not to
   the allowlist. If you would like to propose adding a venue to
   flagship/mainstream/specialty, write that as a recommendation in
   the session report's follow-up list — do not silently expand the
   list mid-triage.

If you find yourself about to do any of the above, stop and write a
dated decision note in `.status/` explaining why, then ask for
confirmation.

---

## Success criteria

Phase 2 is done when:

1. `python outputs/literature_search/resolve_landmarks.py` runs to
   completion and produces `outputs/literature_search/landmark_refs.json`
   with a `resolution_status` field set on every entry. Print-summary
   counts of resolved/ambiguous/not_found match expectations (most
   should be resolved; a handful of pre-1960 titles may come back
   ambiguous).
2. A rerun of `resolve_landmarks.py` on the same day makes zero
   network calls (verified by running with network disabled or by
   checking the cache date directory's mtime).
3. `python outputs/literature_search/triage_existing_refs.py` runs
   without errors and produces `.status/reference_triage_<today>.md`
   with sections 1–4 populated.
4. A rerun of the triage script produces byte-identical output
   Markdown (`diff` returns empty).
5. `.status/session_2026-04-22_literature_search_phase2.md` exists and
   documents the run, including landmark resolution summary, venue
   aliases resolved by hand, triage counts, and landmark gap list.
6. **No changes** to `process_details.json` or `task_details.json`.
   Verify this with `git diff` (or equivalent) at the end of the
   session.

At that point, Phase 2 hands off to the user for review. Phase 3
(systematic search per process and per task) is a separate Sonnet
session gated on the user's acceptance of the triage.

---

## Questions to raise with the user if they come up during execution

Do not silently decide these — ask:

- If `resolve_landmarks.py` reports more than ~10% `ambiguous` or
  `not_found` entries — that means the MD parser or CrossRef query is
  under-tuned, not that the literature is sparse.
- If the triage reports a KEEP (landmark) count that disagrees with
  the landmark JSON's entry count by more than ~5 — either the pub_id
  minting is unstable across the two paths (identity issue to debug in
  Phase 1 code, not here) or the existing JSON has landmark papers
  under surprisingly different citation strings than the landmark MD.
- If >100 references fall into REVIEW/`default_needs_review` — the
  rule chain has a gap and you should propose a new rule rather than
  burying 100 items in the default bucket.
- If a reference has so little metadata (`authors == null`, `title
  == ""`) that you cannot mint a pub_id — report it, skip it with a
  `pub_id: null, triage: "malformed_reference"` row, and list it
  explicitly in the session report. Do not silently drop malformed
  entries.
- If you discover a new structural issue in `process_details.json` or
  `task_details.json` (duplicate references, missing required fields,
  schema mismatches) — report it and stop before continuing with the
  triage. Schema fixes are a separate workstream.

Open §12 items from the parent plan (venue tier review, 14 unresolved
historical refs, dual-cited refs with different resolution status) may
surface during Phase 2 triage but are not blocking. Note them in the
session report's follow-ups; they are the subject of Phase 3 / Phase 5
review.
