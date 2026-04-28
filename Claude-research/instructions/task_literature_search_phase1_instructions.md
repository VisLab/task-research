# Task: Literature Search — Phase 1 infrastructure

**Date:** 2026-04-21
**Goal:** Build the primitive layer for the literature search workstream: the
`identity` module (pub_id, canonical_string, PDF filename generators), five
thin API clients for bibliographic lookup, a deterministic cache layer, and a
Phase-1 validation script that resolves five known papers end-to-end and
reports the generated pub_ids and PDF filename shapes. Prove the primitives
work before any real literature search runs.

This is **Phase 1** of the literature-search workstream. Parent plan:
`.status/literature_search_plan_2026-04-21.md`. Phase 0 was planning
(the plan itself and `pdf_naming_thinking_2026-04-21.md`). Phases 2–9 are
separate Sonnet sessions and are not part of this task.

---

## Context

You are working on the HED (Hierarchical Event Descriptor) cognitive process
catalog. The workspace root is `H:\Research\TaskResearch\Claude-research\`.

The current reference set in `process_details.json` and `task_details.json`
is not acceptable for our quality bar (too many historical refs and test
manuals, too few flagship-journal papers, no systematic co-mention search).
The literature-search workstream rebuilds the reference corpus via
systematic discovery through OpenAlex / PubMed / Semantic Scholar, routed
through the OpenAlex Topic crosswalk in `H:\Research\TaskResearch\OpenAlex\`,
filtered by a publisher/venue quality allowlist, and curated into a new
first-class `publications.json` store with Zotero as the GUI frontend.

**Your job in Phase 1 is not to do any of that search work.** Your job is to
build the pure-function and client primitives that the later phases rely on,
and prove they work on five known papers. Nothing you write in Phase 1
touches `process_details.json`, `task_details.json`, or any Zotero instance.

Before coding, **read these three documents in full**:

1. `.status/literature_search_plan_2026-04-21.md` — the parent plan. The
   relevant sections for Phase 1 are §3.2 (publication record schema), §4
   (source ladder), §8 Phase 1, and §11.7 (PDF filename and canonical-string
   rules).
2. `.status/pdf_naming_thinking_2026-04-21.md` — the decisions doc for the
   pub_id / canonical_string / PDF filename design. Section 5 in particular
   is the authoritative algorithm.
3. `OpenAlex/README.md` and `OpenAlex/pull_openalex.py` — reference
   implementation for OpenAlex polite-pool conventions, argparse patterns,
   and idempotent caching. Copy patterns, don't import.

If any of these contradict this instructions doc, **stop and write a dated
decision note to `.status/` rather than resolving the contradiction on your
own.**

---

## What specifically needs to happen

### Sub-phase 1.1: Confirm environment and network

Before writing any code:

1. Confirm egress to each API host from the sandbox (if running in Cowork)
   or from the host machine (if running host-side):
   ```
   curl -I --max-time 5 https://api.crossref.org/works?rows=1
   curl -I --max-time 5 "https://api.openalex.org/works?per-page=1"
   curl -I --max-time 5 "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=test&format=json&pageSize=1"
   curl -I --max-time 5 "https://api.semanticscholar.org/graph/v1/paper/search?query=test&limit=1"
   curl -I --max-time 5 "https://api.unpaywall.org/v2/10.1038/nature12373?email=hedannotation@gmail.com"
   ```
   Expected: HTTP 200 from each.
2. If **any** host returns a connection error, stop and follow the
   host-script fallback pattern from
   `task_citation_enrich_processes_instructions.md` (the "Network access
   check" section there). Do not attempt to work around blocked hosts in
   any other way.

### Sub-phase 1.2: Build `identity.py`

Create `outputs/literature_search/identity.py`. Target: ~200 lines of flat
Python, no classes beyond one or two dataclasses. Standard library only (no
`requests`, no external packages). This module is imported by every other
module in the workstream and must be correct and well-tested.

It exposes three pure functions:

```python
def build_canonical_string(
    first_author_family: str | None,
    year: int | None,
    title: str | None,
) -> str:
    """Returns the <=100-char ASCII alphanumeric string used as SHA-1
    input for the pub_id and for the filename's trailing hash.
    Algorithm is §11.7 step 4 of the plan."""
    ...

def build_pub_id(
    first_author_family: str | None,
    year: int | None,
    title: str | None,
) -> str:
    """Returns 'pub_' + sha1(build_canonical_string(...))[:8]."""
    ...

def build_pdf_filename(
    first_author_family: str | None,
    year: int | None,
    title: str | None,
) -> str:
    """Returns '<LastName>_<Year>_<CamelCaseTitle>_<hash8>.pdf' per
    §11.7 steps 1–4 of the plan. Returns the filename only (no
    directory prefix)."""
    ...
```

**Implementation notes:**

- ASCII folding uses the standard library: `unicodedata.normalize('NFKD', s)`
  followed by stripping characters where `unicodedata.combining(c) != 0`.
- Neither function calls the other; `build_pub_id` and `build_pdf_filename`
  both call `build_canonical_string` (or a shared helper) for the hash.
- `build_pdf_filename` reuses `build_canonical_string`'s last-name and title
  normalization but **not** its output string (that's the hash input, not the
  filename). The filename's `<LastName>` is TitleCased whitespace-joined
  tokens (`Van Der Berg` → `VanDerBerg`). The filename's `<CamelCaseTitle>`
  preserves all-caps acronyms of length ≥ 2 and truncates at a token boundary
  ≤ 100 chars (never mid-word). The canonical string is always lowercased
  alphanumeric and truncated at exactly 100 chars (may cut mid-word — it's
  opaque).
- Year handling: `year=None` → canonical uses `"0000"`, filename uses
  `"nodate"`. Two different spellings on purpose (the plan says so).
- Empty-after-fold cases: canonical uses `"anonymous"` / `"untitled"`;
  filename uses `"Anonymous"` / `"UntitledNonLatin"`.

Colocate a **pytest-runnable** test file `outputs/literature_search/test_identity.py`
with the fixtures listed below. Use plain `assert` statements and
`pytest.mark.parametrize`. Do **not** use unittest. Do **not** add a
fixture-loading framework. All inputs are literals in the test file.

Required test cases (one parametrized test per function, each exercising
every row below):

| # | first_author_family | year | title | notes |
|---|---|---|---|---|
| 1 | "Badre" | 2012 | "Cognitive control, hierarchy, and the rostro-caudal organization of the frontal lobes" | baseline; canonical = `badre2012cognitivecontrolhierarchy...` |
| 2 | "Stroop" | 1935 | "Studies of interference in serial verbal reactions" | pre-DOI era |
| 3 | "Eriksen" | 1974 | "Effects of noise letters upon the identification of a target letter in a nonsearch task" | |
| 4 | "Posner" | 1980 | "Orienting of attention" | short title |
| 5 | "Miller" | 1956 | "The magical number seven, plus or minus two" | leading article "The" |
| 6 | "Schönberg" | 2009 | "A test of diacritics" | accented family name |
| 7 | "O'Keefe" | 1971 | "The hippocampus as a spatial map" | apostrophe in family name |
| 8 | "van der Berg" | 2020 | "Compound particle test" | compound particle |
| 9 | "de Fockert" | 2001 | "The role of working memory in visual selective attention" | |
| 10 | "Wagenmakers" | 2016 | "fMRI and EEG study of cognitive control: an ADHD cohort" | preserve `fMRI`, `EEG`, `ADHD` in filename |
| 11 | "Smith" | 2015 | "A" * 400 | very long title — hits both 100-char truncations |
| 12 | None | 2010 | "Anonymous report" | no first author → `anonymous` / `Anonymous` |
| 13 | "Brown" | None | "Undated paper" | no year → `0000` / `nodate` |
| 14 | "Li" | 2018 | "工作记忆" | non-Latin title folds empty → `untitled` / `UntitledNonLatin` |
| 15 | "Badre" | 2012 | "Cognitive control, hierarchy, and the rostro-caudal organization of the frontal lobes" | **identical to #1** — asserts determinism (DOI-discovered-later round trip simulated by calling with identical inputs twice; pub_id and filename must match byte-for-byte across two invocations) |

For each row, assert specific expected outputs where it's cheap to enumerate
(e.g., for row 1 the canonical string is
`badre2012cognitivecontrolhierarchyandtherostrocaudalorganizationofthefrontallobes`
and `build_pub_id(...)` returns `"pub_" + sha1(canonical).hexdigest()[:8]`).
Where the exact hash is not worth hand-computing, assert format properties
instead: length, prefix, character class, filename shape.

**Hash-collision handling is not required in Phase 1.** The 8-char hash is
sufficient for our catalog size; record a TODO comment at the one place
where it would matter (the function that writes a new pub_id into
`publications.json` — which you don't write in Phase 1 anyway).

### Sub-phase 1.3: Build the cache layer

Create `outputs/literature_search/cache.py`. ~80 lines.

One function:

```python
def cache_get_or_fetch(
    cache_dir: Path,
    source: str,               # "openalex" | "crossref" | "europepmc" | "semanticscholar" | "unpaywall"
    key: str,                  # e.g. the DOI, or the full URL
    fetch: Callable[[], dict],
    today: str | None = None,  # "YYYY-MM-DD"; defaults to date.today().isoformat()
) -> dict:
    """Returns the cached JSON for (source, key) on `today`. If absent,
    calls fetch() once and persists the response under
    cache_dir/<source>/<today>/<hash(key)>.json, then returns it."""
    ...
```

Layout of the cache on disk:

```
outputs/literature_search/cache/
  openalex/2026-04-21/<16-hex-char-sha1>.json
  crossref/2026-04-21/<16-hex-char-sha1>.json
  europepmc/2026-04-21/<16-hex-char-sha1>.json
  semanticscholar/2026-04-21/<16-hex-char-sha1>.json
  unpaywall/2026-04-21/<16-hex-char-sha1>.json
```

Each cache file also contains its own key (so a hash collision is detectable
by mismatch on read). Shape on disk:

```json
{"source": "openalex", "key": "...", "fetched_on": "2026-04-21", "response": {...}}
```

No expiry logic; caches are immutable once written. A fresh date stamp means
a new directory tree. This mirrors the `raw/` convention in
`H:\Research\TaskResearch\OpenAlex\`.

### Sub-phase 1.4: Build the five API clients

Create `outputs/literature_search/clients/` with one file per source:

```
clients/
  __init__.py
  openalex.py
  crossref.py
  europepmc.py
  semanticscholar.py
  unpaywall.py
```

Each client is ~80–120 lines, standard library + `requests`. Each exposes:

```python
def lookup_by_doi(doi: str, cache_dir: Path, email: str = "hedannotation@gmail.com") -> dict | None:
    """Return the source's normalized metadata dict for this DOI, or None
    if not found / error. Uses cache_get_or_fetch under the hood."""
    ...
```

(Europe PMC additionally exposes `lookup_by_pmid(pmid, ...)`. Unpaywall only
takes DOI.)

Per-client URL templates, to keep this doc self-contained:

- **OpenAlex**: `https://api.openalex.org/works/doi:{doi}?mailto={email}`
- **CrossRef**: `https://api.crossref.org/works/{doi}` with header
  `User-Agent: hed-task/1.0 (mailto:{email})`
- **Europe PMC**:
  `https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:{doi}&format=json&resultType=core&pageSize=1`
- **Semantic Scholar**:
  `https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=externalIds,title,authors,year,venue,abstract,openAccessPdf,isOpenAccess,citationCount`
- **Unpaywall**: `https://api.unpaywall.org/v2/{doi}?email={email}`

**Common conventions:**

- 0.2 s sleep between consecutive calls to the same host.
- Retry once on HTTP 429 with a 2 s wait; retry once on 5xx with a 2 s wait.
  Give up (return None + log) on further errors.
- Do not retry on 4xx.
- Log each call as one line: `source=openalex doi=... status=200 cached=False`.
- All clients return `None` on missing/unresolvable — not an exception. The
  validation script decides what to do with `None`.

**Normalized output**: each client returns its source's JSON with three
convenience keys added, if computable:

```python
{
  "_source": "openalex",
  "_doi": "10.1016/j.tics.2012.02.005",
  "_fetched_on": "2026-04-21",
  ... raw response fields ...
}
```

**Do not** try to merge across sources in Phase 1. The merger belongs to
Phase 3 and has its own decisions. Phase 1 just fetches and caches.

### Sub-phase 1.5: Build the validation script

Create `outputs/literature_search/phase1_validate.py`. ~150 lines. Standard
library + `requests`.

It does exactly this, for each of the seven test papers below:

1. Call each of the five clients with the paper's DOI.
2. Extract a canonical `(first_author_family, year, title)` tuple. Preferred
   source for these fields is OpenAlex; fall back to CrossRef; then Europe
   PMC; then Semantic Scholar.
3. Call `identity.build_pub_id(...)`, `identity.build_canonical_string(...)`,
   and `identity.build_pdf_filename(...)` on the tuple.
4. Print a row in a summary table.

The seven papers (these are the ground truth — the doc's answer key).
The first five span the pre-DOI era through 2012 and test the APIs on
classic, heavily-indexed work. The last two are modern open-access papers
directly relevant to HED (both extend BIDS, the neuroimaging metadata
standard HED is part of). They exist specifically to exercise paths the
older papers don't: Unpaywall's OA-positive response shape, rich CrossRef
metadata (ORCID, funders, structured authorship), Semantic Scholar's
populated citation/externalIds response, and non-Elsevier / non-APA
publisher DOIs (Nature/Scientific Data).

| # | era | paper | DOI |
|---|---|---|---|
| 1 | classic | Badre & Nee (2012), *Cognitive control, hierarchy, and the rostro-caudal organization of the frontal lobes*, TiCS | `10.1016/j.tics.2012.02.005` |
| 2 | classic | Stroop (1935), *Studies of interference in serial verbal reactions*, JEP | `10.1037/h0054651` |
| 3 | classic | Eriksen & Eriksen (1974), *Effects of noise letters...* , Perception & Psychophysics | `10.3758/BF03203267` |
| 4 | classic | Posner (1980), *Orienting of attention*, Quarterly Journal of Experimental Psychology | `10.1080/00335558008248231` |
| 5 | classic | Miller (1956), *The magical number seven, plus or minus two*, Psychological Review | `10.1037/h0043158` |
| 6 | modern OA | Gorgolewski et al. (2016), *The brain imaging data structure, a format for organizing and describing outputs of neuroimaging experiments*, Scientific Data | `10.1038/sdata.2016.44` |
| 7 | modern OA | Pernet et al. (2019), *EEG-BIDS, an extension to the brain imaging data structure for electroencephalography*, Scientific Data | `10.1038/s41597-019-0104-8` |

For the modern OA papers, **additionally assert** that Unpaywall returns
`is_oa: true` with a populated `best_oa_location.url_for_pdf` — if either
comes back null for these two, the client is probably broken rather than
the paper being closed-access.

(Note: DOIs are listed above in their canonical lowercase form; verify them
against CrossRef or DOI.org if any look suspect before running the full
pipeline — a typo in this list wastes runtime. The two modern DOIs in
particular should be spot-checked, as they were recalled from memory when
this doc was written.)

Expected output:

```
Phase 1 validation — 7 papers (5 classic + 2 modern OA)

pub_id          canonical_string (first 60 chars)    pdf_filename
pub_xxxxxxxx    badre2012cognitivecontrolhierarchy... Badre_2012_...a3b9f2c1.pdf
pub_yyyyyyyy    stroop1935studiesofinterferenceins... Stroop_1935_...yyyyyyyy.pdf
...
pub_zzzzzzzz    gorgolewski2016thebrainimagingdata... Gorgolewski_2016_...zzzzzzzz.pdf
pub_wwwwwwww    pernet2019eegbidsanextensiontoth... Pernet_2019_...wwwwwwww.pdf

Cross-source DOI agreement:
  Badre 2012:       openalex + crossref + s2 agree on first_author=Badre, year=2012, title matches
  Stroop 1935:      ...
  Gorgolewski 2016: openalex + crossref + europepmc + s2 agree; unpaywall is_oa=True
  Pernet 2019:      openalex + crossref + europepmc + s2 agree; unpaywall is_oa=True

Warnings: (if any source returned a different year or different first author,
           list here with both values)
```

**Determinism test**: after the main table, re-run the pipeline on the first
paper (Badre 2012) but without populating the DOI field in the intermediate
data (simulate "DOI unknown at ingest"). Confirm the pub_id is identical to
the DOI-populated run. This is the DOI-discovered-later invariant from
§11.7 of the plan.

### Sub-phase 1.6: Write the Phase 1 session report

Write `.status/session_2026-04-21_literature_search_phase1.md`. Include:

- What was built (file list with line counts).
- The final validation-script output table.
- Whether all five cross-source DOI agreements passed.
- Any surprises: API quirks (OpenAlex rate limits triggered, Semantic Scholar
  returning nulls, CrossRef DOI that 404'd, Unpaywall missing entries),
  character-folding edge cases, etc.
- The DOI-discovered-later round-trip result.
- Any plan deviations with rationale.
- List of follow-ups for Phase 2.

---

## CRITICAL: File access rules — virtiofs stale snapshot issue

**The bash sandbox sees a stale, potentially corrupted snapshot of mounted
workspace files.** This has bitten every prior session. Rules:

1. **ALWAYS use the Read tool** (with Windows paths like
   `H:\Research\TaskResearch\Claude-research\process_details.json`) to read
   files from the workspace mount. Do NOT use bash `cat`, `head`, `tail`,
   or Python `open()` on mounted paths.
2. **ALWAYS use the Write or Edit tool** to write files back to the
   workspace.
3. **Ok to use bash** within `outputs/` — that's the Cowork-session temp
   area and is not subject to the stale-snapshot issue.
4. **If a JSON parse error occurs in bash** on a workspace file, it is
   almost certainly the stale snapshot (trailing null bytes). Read the file
   via the Read tool instead.

Phase 1 does not modify any workspace JSON. You will create files under
`outputs/literature_search/` (bash-safe) and `.status/` (use Write tool).

---

## File inventory

### Files you will create

Under `H:\Research\TaskResearch\Claude-research\outputs\literature_search\`:

- `identity.py` — three pure functions + one shared helper.
- `test_identity.py` — parametrized tests; 15 fixture rows × 3 functions.
- `cache.py` — one function + small helpers.
- `clients/__init__.py` — empty.
- `clients/openalex.py`
- `clients/crossref.py`
- `clients/europepmc.py`
- `clients/semanticscholar.py`
- `clients/unpaywall.py`
- `phase1_validate.py` — entrypoint.
- `README.md` — one-page orientation for the directory.

Under `H:\Research\TaskResearch\Claude-research\.status\`:

- `session_2026-04-21_literature_search_phase1.md` — session report.

### Files for reference (do not modify)

- `.status/literature_search_plan_2026-04-21.md` — parent plan.
- `.status/pdf_naming_thinking_2026-04-21.md` — decisions doc.
- `.status/task_citation_enrich_processes_instructions.md` — prior
  Sonnet instruction style; copy conventions.
- `OpenAlex/pull_openalex.py` — reference for idempotent cache + argparse +
  polite-pool patterns.
- `outputs/resolve_citations.py` (from Phase B) — reference for retry and
  rate-limit patterns in a similar domain. **Do not import**; copy ideas
  only. That module uses *search* endpoints; Phase 1 uses only *lookup by
  DOI/PMID* endpoints.

### Files you will NOT modify in Phase 1

- `process_details.json`
- `task_details.json`
- `publications.json` (does not exist yet; created in Phase 6)
- `publication_links.json` (does not exist yet; created in Phase 6)
- Anything in `OpenAlex/`
- Any Zotero preference, plugin, or SQLite database

---

## Working conventions

- **Clean, flat Python.** No abstract base classes. No dependency injection
  frameworks. One module per responsibility. Each file ≤ 200 lines ideally;
  hard cap 300.
- **Standard library + `requests` only.** No `pyalex`, no `crossrefapi`, no
  `requests-cache`, no `pydantic`, no `click`, no `rich`. Plain `argparse`,
  plain `json`, plain `logging`.
- **Cache everything**. A rerun should cost zero network calls.
- **No emojis** in code or markdown unless the user asks.
- **One commit-equivalent at the end**: after `phase1_validate.py` works,
  write the session report and stop. Do not start Phase 2.

---

## What is explicitly NOT part of Phase 1

These are tracked separately and are forbidden in this session:

1. **Literature searching.** No calls to OpenAlex `/works?search=...` or
   similar search endpoints. Phase 1 is DOI-lookup only.
2. **Ranking.** No quality score, no composite scoring, no venue tier table.
3. **Zotero interaction.** No `pyzotero`, no HTTP call to
   `http://localhost:23119/api/`, no reading of any Zotero file.
4. **Modifying `process_details.json` or `task_details.json`.** Phase 8 does
   that; not now.
5. **Creating `publications.json` or `publication_links.json`.** Phase 6
   does that; not now.
6. **PDF acquisition.** No actual download of any PDF. Phase 7 does that;
   Phase 1 only computes filenames.
7. **Network egress to hosts other than the five listed APIs.** If anything
   else is needed, stop and ask.

If you find yourself about to do any of the above, stop and write a dated
decision note in `.status/` explaining why, then ask for confirmation.

---

## Success criteria

Phase 1 is done when:

1. `pytest outputs/literature_search/test_identity.py -q` passes all 45
   test cases (15 fixtures × 3 functions) on a clean checkout.
2. `python outputs/literature_search/phase1_validate.py` prints the summary
   table and the DOI-discovered-later invariant check both pass.
3. The cache tree under `outputs/literature_search/cache/` contains one
   `.json` file per (source, DOI) tuple for the 5 papers — 25 files,
   roughly.
4. `.status/session_2026-04-21_literature_search_phase1.md` exists and
   documents the run.

At that point, Phase 1 hands off to the user for review. Phase 2 (triage of
existing references) is a separate Sonnet session gated on that review.

---

## Questions to raise with the user if they come up during execution

Do not silently decide these — ask:

- If any of the 5 validation DOIs returns 404 from all five sources (likely
  indicates my DOI was wrong in this doc).
- If the canonical string for a real paper exceeds 100 chars and the
  truncation lands in the middle of what would have been an important
  disambiguator (e.g., the title has a version/edition suffix past char
  100).
- If a required API host is unreachable from your environment and the
  host-script fallback would require changes to the existing
  `OpenAlex/pull_openalex.py` pattern.
- If a client returns data that doesn't fit the "normalized dict with _source,
  _doi, _fetched_on" shape (e.g., Europe PMC returns a result list rather
  than a single paper).

Open §12 items from the parent plan (landmark list, venue tier review, 14
unresolved historical refs, dual-cited refs with different resolution
status) do NOT affect Phase 1 and should not be raised here. They'll be
handled before Phase 3.
