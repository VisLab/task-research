# Task — Phase 3 search revamp (Sonnet implementation)  v3

**Original date:** 2026-04-24
**Companion design doc:** `instructions/search_strategy_decisions_2026-04-24.md` (v3)
**Status:** Ready to implement **only after the user signs off on the
design doc.**  If the design doc is not signed off, stop and ask.

---

## 0. Orientation — read before editing

In this order:

1. `CLAUDE.md` — project conventions, sandbox path quirks, file-tool
   vs. bash-tool rules.
2. `instructions/search_strategy_decisions_2026-04-24.md` — all design
   decisions.  The authoritative spec for every change below.  If the
   code you are about to write contradicts that doc, stop and ask.
3. `instructions/literature_search_plan_2026-04-21.md` §6 (scoring)
   and §11.7 (pub_id) — current weights and identity rules.
4. `outputs/phase3/candidates/hed_response_inhibition.md` — the broken
   POC output you are fixing.
5. `code/literature_search/` — the modules you will touch.

Do not skip step 2.  Every change traces back to a numbered section
there.

---

## 1. Operating constraints

- **Workspace root** is always the project root.  Use relative paths
  in all new code.  No hardcoded Windows drive letters.
- **Windows vs. Linux sandbox.**  See `CLAUDE.md` "Windows / Cowork
  sandbox file access."  Summary: read with Read tool, write with
  Write/Edit, run with bash via Linux mount.  If bash can't import
  a just-edited file, rewrite via bash here-doc to refresh VirtioFS.
- **Do not mutate** `process_details.json` or `task_details.json`.
- **Cache behavior.**  Changed parameters → new cache keys → first
  run re-fetches.  Expected.  Do not manually invalidate old entries.
- **Scratch files.**  Temporary scripts and checks go in `.scratch/`.
  Clean up at end.
- **No network in sandbox.**  Prepare code in sandbox; user runs the
  POC on the Windows host.
- **Session report.**  Write
  `.status/session_2026-04-24_search_revamp.md` at end per
  `CLAUDE.md` conventions.

---

## 2. Implementation plan — one commit per numbered step

Steps 1–9 harden Stage A (preliminary screening).  Steps 10–12 add
Stage B and surface it in output.  Steps run in order; do not bundle.

Terminology note: the word "foundational" does **not** appear as a
Stage A pass name or a markdown section header anywhere.  The three
Stage A sub-queries are `all_years`, `recent`, `reviews`.  The
markdown section 1 is titled "Top candidates (score-ranked)."
"Foundational" survives only as one of five suggested-role hints in
the per-candidate detail block, and the human reviewer in Phase 5
may overwrite it.

### Step 1 — Add the category → fields-of-study map

**Create:** `code/literature_search/fos_map.py`

Unchanged from v2.  Copy all 19 rows of the table in decisions doc
§6 verbatim.  Expose two functions:

```python
def fields_of_study_for_category(category_id: str | None) -> str
def fields_of_study_set(category_id: str | None) -> set[str]
```

The first returns the comma-joined S2 query-param string.  The second
returns a lowercase set for use by Stage B's FoS-overlap filter.

**Test** (`.scratch/test_fos_map.py`):

- `fields_of_study_for_category("inhibitory_control_and_conflict_monitoring")`
  equals `"Neuroscience,Psychology,Medicine"`.
- `fields_of_study_for_category(None)` returns the default.
- `fields_of_study_set("reasoning_and_problem_solving")` equals
  `{"neuroscience", "psychology", "philosophy", "computer science"}`.
- Sanity loop: every `category_id` in `process_details.json` either
  appears in the map or falls back to the default.

### Step 2 — Wire category → FoS into `search_queries.py`, rename sub-queries

**Edit:** `code/literature_search/search_queries.py`

Changes:

1. Import `fields_of_study_for_category` from `fos_map`.
2. Rename all internal labels and keys from `foundational` to
   `all_years`.  This includes:
   - The pass dict keys (`plan.passes["all_years"]`, etc.).
   - Any docstring, comment, or log format string.
   - Any POC selection that referenced the old name.
   Keep `recent` and `reviews` as-is — they're already descriptive.
3. Extend `build_plans_from_json` to read `category_id` from each
   process record and thread it through.  Tasks resolve via their
   associated process(es); a task spanning multiple categories gets
   the union of those categories' field sets.
4. In `_build_passes`, replace the module-level
   `S2_DEFAULT_FIELDS_OF_STUDY` with a per-item `fields_of_study`
   argument from `fos_map`.  Remove the constant.
5. `all_years` S2 sub-query: add `min_citation_count=20`.
6. All S2 sub-queries: add `publication_types` —
   `"JournalArticle,Review"` on `all_years`, `"JournalArticle"` on
   `recent`, `"Review"` on `reviews`.

Do not change the query-string construction here — that's Step 3 and
Step 6.

**Test** (`.scratch/test_query_plan.py`):

- `plan.passes["all_years"]["semanticscholar"]["fields_of_study"]`
  for `hed_response_inhibition` equals
  `"Neuroscience,Psychology,Medicine"`.
- For `hed_model_based_learning` equals
  `"Neuroscience,Psychology,Computer Science"`.
- `min_citation_count == 20` on `all_years` S2; absent elsewhere.
- `publication_types == "JournalArticle,Review"` on `all_years`,
  `"JournalArticle"` on `recent`, `"Review"` on `reviews`.
- No dict key named `foundational` anywhere in the resulting plan
  structure.

### Step 3 — Phrase-aware OpenAlex query with journal-article filter

**Edit:** `code/literature_search/clients/openalex.py`

Changes to `search_works`:

- Replace top-level `search=<query>` with
  `filter=title_and_abstract.search:"<phrase>"` for single phrase,
  OR-joined with pipe (`|`) for multiple.
- Add type filter.  `all_years` and `recent`: `filter=type:article|review`.
  `reviews`: `filter=type:review`.  Compose with phrase filter via
  comma (OpenAlex filter AND).
- Accept `phrases: list[str]` argument; keep backward compat with
  `query` string.
- Cache key includes phrases (sorted, pipe-joined) and type filter.

**Test** (`.scratch/test_openalex_filter.py`):

- For phrases `["response inhibition", "inhibitory control"]`,
  sub-query=`all_years`, assert final `filter` contains both:
    - `title_and_abstract.search:"response inhibition"|title_and_abstract.search:"inhibitory control"`
    - `type:article|review`
- For sub-query=`reviews`, assert `type:review`.

### Step 4 — TITLE/ABSTRACT-qualified EuropePMC query with PUB_TYPE

**Edit:** `code/literature_search/clients/europepmc.py`

Changes:

- Given `phrases`, build `(TITLE:"<p>" OR ABSTRACT:"<p>")` per phrase;
  OR-join the blocks.
- AND with `PUB_TYPE:"research-article"` on `all_years` and `recent`;
  `PUB_TYPE:"review-article"` on `reviews`.
- AND with existing date filter on `recent`.

Cache key includes phrases + pub_type; invalidates old entries.

**Test** (`.scratch/test_europepmc_filter.py`): assert constructed
query string character-for-character for all three sub-queries.

### Step 5 — S2 client: `minCitationCount`, `publicationTypes`, richer `fields`

**Edit:** `code/literature_search/clients/semanticscholar.py`

In `search`, accept:

- `min_citation_count: int | None = None` → `minCitationCount` param.
- `publication_types: str | None = None` → `publicationTypes` param.

Update the default `fields` string to include the v3 additions:

    FIELDS_SEARCH = (
        "title,abstract,tldr,year,authors,venue,"
        "publicationTypes,fieldsOfStudy,"
        "citationCount,influentialCitationCount,"
        "externalIds,openAccessPdf,paperId"
    )

Add both new params + the fields string to the cache key.

Update `phase3_search.run_item` (S2 branch) to forward
`min_citation_count` and `publication_types` from the pass spec.

**Test** (`.scratch/test_s2_params.py`):

- Build `search(..., min_citation_count=20,
  publication_types="JournalArticle,Review")`; confirm both appear
  in the resolved `params` dict.
- Confirm the `fields` param string contains `tldr` and
  `influentialCitationCount`.

### Step 6 — S2 query = quoted phrase

**Edit:** `code/literature_search/search_queries.py`

Change `_s2_queries`:

    def _s2_queries(name: str, aliases: list) -> list[str]:
        out = []
        for t in [name] + _flatten_aliases(aliases):
            if not t:
                continue
            out.append(f'"{t}"' if " " in t else t)
        return out

(Only multi-word phrases are quoted.)

**Smoke test** (user runs on Windows host):

    python code/literature_search/phase3_search.py --mode single \
      --ids hed_response_inhibition --passes all_years \
      --sources semanticscholar --write

Compare S2 result count to the prior cache entry.  Record in session
report.  If the quoted query returns near-zero results, revert this
step and rely on the phrase gate alone.

### Step 7 — Extend `Candidate`, normalization, and the phrase-count relevance score

**Edit:** `code/literature_search/normalize.py`

Extend the `Candidate` dataclass with:

- `tldr: str | None = None`
- `influential_citation_count: int | None = None`
- `s2_paper_id: str | None = None`
- `stage_b_edges: list[dict] = field(default_factory=list)`  where
  each edge-dict has keys `seed_pub_id`, `intents` (list[str] or
  []), `is_influential` (bool).

Update `normalize_s2_paper` (and the OpenAlex/EuropePMC normalizers
for backward compat — TLDR is S2-only, so others set `tldr=None`).
S2 paperId goes into `s2_paper_id`.  Influential count goes into
`influential_citation_count` (int, or None if missing).

**Edit:** `code/literature_search/rank_and_select.py`

Add `_phrase_list(item)` returning primary name + flat alias strings.

Replace `_relevance_score`:

    def _relevance_score(cand: Candidate, item: ItemQueryPlan) -> float:
        phrases = _phrase_list(item)
        if not phrases:
            return 0.0
        text = ((cand.title or "") + " " +
                (cand.abstract or "") + " " +
                (cand.tldr or "")).lower()
        hits = 0
        for phrase in phrases:
            p = phrase.lower().strip()
            if not p:
                continue
            if " " in p:
                if p in text:
                    hits += 1
            else:
                if _tokenize(text) & {p}:
                    hits += 1
        return hits / len(phrases)

Keep `_tokenize` and `_STOP_WORDS` unchanged.

**Test** (`.scratch/test_relevance.py`):

- Candidate with title "CDK4/6 inhibition triggers anti-tumor
  immunity", abstract containing "response" and "inhibition"
  separately, no TLDR.  Item = `hed_response_inhibition`.
  Assert score 0.0.
- Candidate with title "Cortical suppression during stopping" (no
  phrase), abstract empty, TLDR "This paper examines response
  inhibition using stop-signal tasks."  Same item.  Assert score
  1.0.  (Demonstrates the TLDR rescue.)
- Candidate with title "Response inhibition in the stop-signal
  paradigm"; assert score 1.0.

### Step 8 — Post-retrieval phrase gate (TLDR-aware)

**Edit:** `code/literature_search/rank_and_select.py`

Add:

    def phrase_gate(
        candidates: list[Candidate],
        item: ItemQueryPlan,
        historical_pub_ids: set[str],
        historical_dois: set[str],
    ) -> list[Candidate]:
        phrases = [p.lower().strip() for p in _phrase_list(item) if p]
        kept = []
        for c in candidates:
            if c.pub_id in historical_pub_ids:
                kept.append(c); continue
            if c.doi and c.doi.lower() in historical_dois:
                kept.append(c); continue
            text = ((c.title or "") + " " +
                    (c.abstract or "") + " " +
                    (c.tldr or "")).lower()
            matched = False
            for p in phrases:
                if " " in p and p in text:
                    matched = True; break
                if " " not in p and p in _tokenize(text):
                    matched = True; break
            if matched:
                kept.append(c)
        return kept

Wire into `phase3_search.run_item` right after `dedup_candidates`.
Used by Stage B (Step 11) too.

**Test** (`.scratch/test_phrase_gate.py`): synthetic test with 4
candidates — on-topic-via-title, on-topic-via-TLDR-only,
off-topic-all, historical — assert first three survive and the
second confirms TLDR rescue.

### Step 9 — Scoring: blended citation, new weights, influence-intent bump

**Edit:** `code/literature_search/rank_and_select.py`

Replace top-of-file weight constants:

    W_CITATION           = 0.25
    W_VENUE              = 0.20
    W_PUBLISHER          = 0.10
    W_RECENCY            = 0.15
    W_RELEVANCE          = 0.25
    W_REVIEW             = 0.05
    # Sum == 1.00
    W_INFLUENCE_INTENT   = 0.05   # per strong Stage-B edge, cap 3
    INFLUENCE_INTENT_CAP = 3
    LM_BONUS             = 0.30

Replace the citation component of `composite_score`:

    def _citation_component(cand: Candidate) -> float:
        total = _log_norm(cand.citation_count or 0)
        infl  = _log_norm(cand.influential_citation_count or 0)
        return 0.4 * total + 0.6 * infl

Add the influence-intent bump.  New helper:

    _STRONG_INTENTS = {"background", "methodology", "extension"}

    def _influence_intent_bump(cand: Candidate) -> float:
        strong = 0
        for edge in cand.stage_b_edges:
            if edge.get("is_influential"):
                strong += 1; continue
            intents = {str(i).lower() for i in (edge.get("intents") or [])}
            if intents & _STRONG_INTENTS:
                strong += 1
        return W_INFLUENCE_INTENT * min(strong, INFLUENCE_INTENT_CAP)

Include the bump in the composite:

    score = (W_CITATION   * _citation_component(c) +
             W_VENUE      * _venue_score(c) +
             W_PUBLISHER  * _publisher_score(c) +
             W_RECENCY    * _recency_score(c, today_year) +
             W_RELEVANCE  * _relevance_score(c, item) +
             W_REVIEW     * _review_bonus(c))
    score += _influence_intent_bump(c)
    if c.pub_id in historical_pub_ids:
        score += LM_BONUS
    return score

Update the module docstring to cite design doc §8 as the authority.

**Test** (`.scratch/test_scoring.py`):

- Candidate with only `citation_count=100` (no `influential_citation_count`):
  citation component equals `0.4 * log_norm(100) + 0.6 * log_norm(0)`.
- Candidate with `citation_count=100, influential_citation_count=30`:
  citation component equals `0.4 * log_norm(100) + 0.6 * log_norm(30)`.
- Candidate with `stage_b_edges=[{is_influential: True}, {intents: ["background"]}]`:
  bump equals `2 * 0.05 = 0.10`.
- Candidate with five influential edges: bump equals `3 * 0.05 = 0.15` (capped).
- Candidate with zero edges: bump equals 0.0.

### Step 10 — S2 citations fetch function

**Edit:** `code/literature_search/clients/semanticscholar.py`

Add:

    FIELDS_CITATIONS = (
        "title,abstract,tldr,year,authors,venue,"
        "publicationTypes,fieldsOfStudy,"
        "citationCount,influentialCitationCount,"
        "externalIds,openAccessPdf,paperId,"
        "intents,isInfluential"
    )

    def fetch_citations(
        paper_id: str,
        limit: int = 1000,
        cache_dir: Path | None = None,
        fields: str = FIELDS_CITATIONS,
    ) -> list[dict]:
        """GET /paper/{paperId}/citations.  Returns a list of result
        dicts as returned by S2; each has top-level keys `intents`
        (list[str]), `isInfluential` (bool), and `citingPaper` (dict).
        Client code is responsible for flattening.  Empty list on
        404 or HTTP error (log and continue)."""
        ...

Details:

- URL: `/paper/{paper_id}/citations`.
- Params: `fields=<fields>&limit=<limit>`.  No sort parameter (S2
  does not support it here).
- Cache path:
  `outputs/cache/semanticscholar/YYYY-MM-DD/cit_<hash>.json`, hash =
  sha1(`f"{paper_id}|{limit}|{fields}"`).
- Error handling: 404 → WARNING log, return `[]`.  429 → respect
  Retry-After.  5xx → retry once with backoff, then ERROR log and
  return `[]`.

Also add `fetch_references` (same shape, `/paper/{id}/references`,
returning results with `citedPaper` field).  Unwired but symmetric.

**Test** (`.scratch/test_s2_citations.py`): with a recorded fixture,
assert `fetch_citations` parses a typical response and that `[]` is
returned for 404 without raising.

### Step 11 — Stage B orchestration (citation expansion)

**Edit:** `code/literature_search/rank_and_select.py`

Add seed-selection helper:

    def select_citation_seeds(
        candidates: list[Candidate],
        historical_pub_ids: set[str],
        top_k: int = 50,
    ) -> list[Candidate]:
        """Top-K by influential citation count, excluding historicals
        and candidates without an S2 paperId."""
        pool = [
            c for c in candidates
            if c.pub_id not in historical_pub_ids
            and c.s2_paper_id
        ]
        pool.sort(
            key=lambda c: c.influential_citation_count or 0,
            reverse=True,
        )
        return pool[:top_k]

**Edit:** `code/literature_search/phase3_search.py`

Extend `run_item`.  After Stage A's `phrase_gate` completes, and
before composite scoring:

1. **Select seeds:**
   `seeds = select_citation_seeds(stage_a_pool, historical_pub_ids,
   top_k=50)`.
2. **Fetch citations per seed:**
   For each seed, call `semanticscholar.fetch_citations(seed.s2_paper_id,
   limit=1000)`.  Accumulate into a dict keyed by citing paperId with
   a list of seed-edges per citing paper.  Each edge records
   `{seed_pub_id: seed.pub_id, intents: result["intents"],
   is_influential: result["isInfluential"]}`.  The citing paper
   payload (`result["citingPaper"]`) is the S2 paper dict.
3. **Normalize and pre-filter each unique citing paper:**
   - Skip if `publicationTypes` does not intersect
     `{"JournalArticle", "Review", "MetaAnalysis"}`.
   - Let `item_fos = fields_of_study_set(item.category_id)`.  If the
     citing paper has a non-empty `fieldsOfStudy`, skip if the
     lowercased set does not intersect `item_fos`.  Empty
     `fieldsOfStudy` passes through to the phrase gate.
   - Skip if `year < 1950` or `year > today_year()`.
   - Convert to `Candidate` via `normalize_s2_paper` (adapt if the
     citation response shape differs).  Attach the edge list.
4. **Phrase gate** (same function as Stage A) against the normalized
   Stage B candidates.
5. **Merge into Stage A pool** on pub_id.  If a candidate already
   exists in the pool, extend its `sources` with
   `"semanticscholar_citations"` and merge its `stage_b_edges` list.
   If it is new, mark
   `sources=["semanticscholar_citations"]`.
6. **Log sanity:**
   `INFO item=<id> stage_b_seeds=<n_seeds> stage_b_raw=<n_total_results>
   stage_b_after_type_fos=<n> stage_b_after_gate=<n>
   stage_b_merged=<n> stage_b_bumped_nonzero=<n>`.

After merge, run composite scoring over the merged pool.

**Test** (`.scratch/test_stage_b.py`):

- Unit test `select_citation_seeds`: given synthetic candidates
  including one historical and one with no `s2_paper_id`, assert both
  are excluded and top_k=50 is honored.
- Unit test the per-citation filter helper with four synthetic
  citing-paper results: one JournalArticle on-topic with
  `isInfluential=true` (kept, bump 0.05); one BookChapter (dropped);
  one JournalArticle with disjoint FoS (dropped); one JournalArticle
  with empty FoS and on-topic abstract (kept via gate, no bump
  unless intent marks it).
- Integration: merge a mock Stage A pool of 5 with a mock Stage B
  pool of 10, one overlap.  Assert merged size = 14, the overlap
  candidate has both sources listed and merged edges.

### Step 12 — Markdown rendering (TLDR + abstract, renamed sections)

**Edit:** `code/literature_search/present_candidates.py`

Changes:

1. Section 1 header: `"Top candidates (score-ranked)"` — remove
   "Foundational."
2. Per-candidate detail block:

       - **(1)** `[ ] KEEP  [ ] DROP  role: ___________`  sources: ...
         *TLDR:* <cand.tldr>
         *Abstract:* <first 400 chars of cand.abstract>

   If `cand.tldr` is missing/empty, omit the TLDR line entirely (no
   placeholder).  If `cand.abstract` is missing, show
   `*Abstract:* (no abstract)`.
3. Stage B provenance: detail block's `sources: ...` line already
   concatenates the list — no change needed; it will naturally show
   `sources: semanticscholar_citations` for Stage-B-only candidates
   and e.g. `sources: openalex, semanticscholar_citations` for merged.
4. Top-of-markdown Stage B line (below "Sources queried"):

       **Stage B expansion:** N seeds, M citing papers kept after filters

   Thread N and M into `write_item_markdown` as new keyword args
   defaulting to 0.

5. The suggested-role heuristic in `_suggest_role` still emits
   `foundational | key_review | recent_primary | methods | historical`
   as advisory labels in the Suggested column.  Do not rename those —
   they are advisory hints for the human reviewer and match the
   project's role vocabulary per `CLAUDE.md`.

**Test**: round-trip a minimal write with one Stage-B-only
candidate and one Stage-A-only candidate; visually verify the TLDR
line appears only when present and section 1 header reads "Top
candidates (score-ranked)."

---

## 3. POC rerun procedure

After steps 1–12 are merged and their scratch tests pass:

1. On the Windows host:

       python code/literature_search/phase3_search.py \
         --mode poc --write

2. Examine `outputs/phase3/candidates/hed_response_inhibition.md`,
   `hedtsk_stroop_color_word.md`, `hed_model_based_learning.md`.

3. Compare to pre-revamp versions (original mtimes; if overwritten,
   refer to copies reviewed on 2026-04-24 cited in the design doc).

4. Check each acceptance criterion in §4.

---

## 4. Acceptance criteria

Map to decisions doc §10.  Report PASS/FAIL per item in session report.

1. **Contamination gone.**  `hed_response_inhibition.md`: zero
   cancer-biology, zero COVID-19, zero drug-delivery papers in
   sections 1 (top 25), 2 (top 25), and 3 (top 50).
2. **Non-journal outputs gone.**  Zero `book-chapter`, `editorial`,
   `letter`, `erratum`, `dataset` entries in any section of the
   three POC markdowns.
3. **Stage B observable.**  `hed_response_inhibition.md` has ≥ 50
   candidates with `semanticscholar_citations` in `sources`.
4. **TLDR rendered.**  ≥ 20 candidates across the three POC outputs
   have a `TLDR:` line above their `Abstract:`.  Candidates without
   TLDR omit the line (no filler).
5. **Bump observable.**  Sanity diagnostic logged by `run_item`
   reports `stage_b_bumped_nonzero ≥ 5` for `hed_response_inhibition`.
6. **Historical landmarks present.**  MacLeod 1991, Daw 2011, Logan
   & Cowan 1984 each `YES` in their landmark-check tables.  A `NO`
   is a regression to investigate — **do not patch**.
7. **Negative-control stability.**  Stroop and model-based POCs
   retain ≥ 20/25 of their pre-revamp top-25 picks in section 1.
8. **S2 phrase-syntax check.**  Session report states whether the
   smoke test found quoted ≠ unquoted behavior.
9. **Call-budget sanity.**  `fetch_citations` called ≤ 50 times per
   item; ≤ 150 total across the 3 POC items.
10. **Schema drift.**  Checksums of `process_details.json` and
    `task_details.json` before/after the run match.
11. **Unit tests.**  All `.scratch/test_*.py` pass.
12. **No `foundational` pass label.**  Grep `code/literature_search/`
    for `foundational` — any hit must be inside
    `present_candidates._suggest_role` (the advisory label
    vocabulary), a docstring that explains v3 terminology, or a
    reference to the v2→v3 rename.  No pass/key/variable still uses
    the old name.

If any criterion fails, stop, write the session report describing
what failed.  Do not silently patch over failures.

---

## 5. Session report template

Write to `.status/session_2026-04-24_search_revamp.md`:

- **What was done** — 12 steps with PASS/FAIL.
- **Files changed** — list.
- **POC acceptance check** — one line per §4 criterion.
- **API observations** — S2 quoted-phrase behavior, OpenAlex phrase
  filter call count, EuropePMC result-count delta, cache
  invalidation cost, Stage B seed-to-kept yield ratio per item,
  distribution of bump values (count of edges per candidate).
- **Decisions deferred** — judgment calls where the evidence was
  ambiguous.
- **Left for next session** — stubs, TODOs, unresolved edges.

---

## 6. Guardrails

- No new clients.
- No `/paper/search/bulk` yet.
- Do not increase the per-alias search count beyond one call per
  alias in Stage A.
- `fetch_references` exists (Step 10) but stays unwired in this task.
- Do not alter the dedup algorithm or `pub_id` function.
- Do not change any file outside `code/literature_search/`,
  `.scratch/`, `.status/`.  `instructions/` and JSON catalog files
  are read-only.
- Do not silently widen acceptance criteria.
