# Search strategy decisions — 2026-04-24  (v3)

**Status:** Draft for user sign-off.  No code changes have been made.
**Input:** `instructions/search_strategy_opus_session.md`
**Companion instruction file (written after sign-off):** `instructions/task_search_revamp_sonnet_2026-04-24.md`
**POC artifact examined:** `outputs/phase3/candidates/hed_response_inhibition.md`

---

## 0. What changed from v2 to v3

v2 answered the user's first round of feedback (remove landmark
fallback, add citation expansion, add journal-article filter, clarify
workflow).  v3 responds to a second round:

1. **"Foundational" is gone from Stage A vocabulary.**  Stage A is now
   "preliminary screening."  Its three sub-queries are labeled
   descriptively (`all-years`, `recent`, `reviews`), not by the role
   we expect the results to play.  Role labels appear only at output
   time as a reviewer hint and are clearly advisory.
2. **No premature trimming before Stage C.**  The full phrase-gated
   Stage A pool flows through to Stage C.  Stage B no longer "cuts"
   the pool — it only selects a **seed set** (K = 50) to drive its
   own S2 citation queries; every Stage A candidate survives to the
   merge regardless of whether it was a seed.
3. **Richer S2 signals.**  Stage A now requests the `tldr` and
   `influentialCitationCount` fields.  Stage B's citations endpoint
   also requests `intents` and `isInfluential` on each citation edge.
4. **TLDR participates in the phrase gate and the markdown.**  Gate
   text = title + abstract + TLDR (broader net for topicality).
   Detail block renders both TLDR and the first 400 chars of abstract
   on separate lines — TLDR for quick skim, abstract for author
   framing.
5. **Citation-quality signal is now blended.**  Composite score's
   citation component is 0.4 × log_norm(citationCount) + 0.6 ×
   log_norm(influentialCitationCount).  Influential weighted more
   because it is sharper; total retained as a backstop for papers
   S2's classifier has not tagged.
6. **New ranking term for Stage B intent and influence.**
   W_INFLUENCE_INTENT = +0.05 per seed-to-candidate edge with
   `isInfluential=true` or intent ∈ {background, methodology,
   extension}, capped at 3 edges.  Applies only to candidates reached
   via Stage B.

Everything else from v2 (three-layer phrase defense, per-category
fieldsOfStudy map, journal-article-only filter, minCitationCount=20,
no landmark fallback, no backward citations yet) carries over.

---

## 1. Simplified workflow (read this first)

```
 STAGE A — PRELIMINARY SCREENING  ->  full phrase-gated pool per item
 ──────────────────────────────────
 Three sub-queries per item (descriptive, not role-bearing):
   all-years  |  recent (year >= today-8)  |  reviews

 Each sub-query hits three sources in fixed order (commutative):

    1) OpenAlex    filter=title_and_abstract.search:"<phrase>"
                   type:article|review       (reviews: type:review)
    2) EuropePMC   (TITLE:"<p>" OR ABSTRACT:"<p>")
                   PUB_TYPE:"research-article"
                                              (reviews: "review-article")
    3) S2          query="<phrase>"
                   publicationTypes=JournalArticle[,Review]
                   fieldsOfStudy=<per-category>
                   minCitationCount=20        (all-years only)
                   fields=...,tldr,influentialCitationCount

 Dedup across sources on pub_id.
 Phrase gate (drop candidates whose title+abstract+TLDR contains
 no item phrase; historicals exempt).
 The entire post-gate pool carries forward to Stage C.
                         |
                         +----> select top 50 by
                         |      influentialCitationCount
                         |      (exclude historicals; require S2 paperId)
                         |
                         v
 STAGE B — S2 CITATION EXPANSION
 ────────────────────────────────
 For each of the 50 seeds:
    GET /paper/{paperId}/citations
        ?fields=...,tldr,intents,isInfluential
        &limit=1000
 Filter each citing paper:
    - publicationType in {JournalArticle, Review, MetaAnalysis}
    - fieldsOfStudy overlaps per-category set
    - phrase gate against title+abstract+TLDR
 Record per-edge intent and isInfluential flags for Stage C.
 Normalize -> merge into Stage A pool (dedup on pub_id).
                         |
                         v
 STAGE C — RANK & EMIT
 ──────────────────────
 Composite score over merged pool, with:
    - blended citation component (0.4 total + 0.6 influential)
    - W_INFLUENCE_INTENT per strong Stage-B edge (cap 3)
    - +0.30 landmark bonus for historical pub_ids
 Emit per-item markdown with sections:
    1) Top candidates (score-ranked)
    2) Recent candidates (year >= today-8)
    3) All deduplicated candidates (audit tail)
 Detail block shows TLDR and first 400 chars of abstract.
 Log (do not rescue) any historical landmark missing from the pool.
```

Three hard ordering constraints: (a) within Stage A, sub-queries and
sources can run in any order since results are unioned; (b) Stage A
must complete before Stage B; (c) Stage C runs only on the merged
Stage A + Stage B pool.

---

## 2. Diagnosis — what the POC actually showed

Unchanged from v2.  Four concrete failure modes in
`outputs/phase3/candidates/hed_response_inhibition.md`:

### 2.1 Contamination is NOT only from Semantic Scholar

16 cancer-biology / COVID-19 / drug-delivery papers appear in the
top-100 audit tail (Goel 2017 CDK4/6, Litchfield 2021 checkpoint
inhibitors, Kim 2020 PARP, Shin 2020 SARS-CoV-2, etc.).  Several came
from OpenAlex and EuropePMC, not only S2.  Root cause: the query
`"Response inhibition"` is a two-token phrase; every engine's default
full-text search matches it as `response AND inhibition`, which
cancer papers routinely satisfy.

### 2.2 The relevance signal is almost useless

`rank_and_select._relevance_score` is token-overlap.  For
`hed_response_inhibition`, any paper containing both "response" and
"inhibition" scores 1.0 — including the cancer papers.  The 0.10
relevance weight has no discriminating power because the signal is
broken, not under-weighted.

### 2.3 Book chapters and non-research outputs leak through

Phase 3 currently accepts every publication type the sources return.
Several OpenAlex entries are `book-chapter`; some EuropePMC rows are
editorial commentary tagged `review-article`.  No explicit
journal-article gate anywhere.

### 2.4 The candidate pool is too narrow

Text search alone misses high-quality on-topic papers that don't use
the exact phrase in title or abstract.  The fix is Stage B — citation
expansion from high-influential Stage A papers — which uses the
citation graph as a semantic-neighborhood signal that text search
cannot provide.

---

## 3. Stage A parameters per source

Three sub-queries per item; three sources per sub-query.  Applied
verbatim by `search_queries._build_passes`.

### 3.1 OpenAlex

| Sub-query | Request form | Year filter | Type filter | Sort | Per-page |
|---|---|---|---|---|---|
| all-years | `filter=title_and_abstract.search:"<p>"...&filter=type:article|review` | — | yes | cited_by_count:desc | 100 |
| recent | same + `filter=from_publication_date:<Y-01-01>` | today−8 | yes | cited_by_count:desc | 100 |
| reviews | same + `filter=type:review` | — | `type:review` only | cited_by_count:desc | 50 |

Multi-alias items: OR the phrase filters with pipe (`|`) inside one
`filter` parameter value.  OpenAlex's `type` vocabulary: `article`
(research + review), `review`, `book-chapter`, `editorial`, etc.
Book chapters, editorials, errata, datasets, and preprint-only
records are excluded.

### 3.2 EuropePMC

| Sub-query | Query block | Year filter | Type filter | Per-page |
|---|---|---|---|---|
| all-years | `(TITLE:"<p>" OR ABSTRACT:"<p>")` OR-joined | — | `AND PUB_TYPE:"research-article"` | 100 |
| recent | same | `AND FIRST_PDATE:[Y-01-01 TO *]` | same | 100 |
| reviews | same | — | `AND PUB_TYPE:"review-article"` | 50 |

### 3.3 Semantic Scholar (`/paper/search`)

| Sub-query | Query form | Year | `publicationTypes` | `minCitationCount` | `fieldsOfStudy` | limit |
|---|---|---|---|---|---|---|
| all-years | one call per alias, quoted phrase | — | `JournalArticle,Review` | 20 | per-category (§6) | 100 |
| recent | same | `Y-` (today−8) | `JournalArticle` | — | per-category | 100 |
| reviews | same | — | `Review` | — | per-category | 50 |

**`fields` parameter** (new in v3):

    title, abstract, tldr, year, authors, venue,
    publicationTypes, fieldsOfStudy,
    citationCount, influentialCitationCount,
    externalIds, openAccessPdf, paperId

No additional S2 call cost; the request just asks for more per-paper
fields in the response.

Rationale for `minCitationCount=20`: a paper cited < 20 times over
any period is neither foundational nor a key review.  Applied only
to all-years because recent papers legitimately have low counts and
reviews are already typed.

Note: S2 `/paper/search` honors quoted phrases per the public FAQ
even though the web UI does not.  Sonnet smoke-tests this on one
item (§10).  If S2 does not honor them, the phrase gate in §7.2
recovers precision without another code change.

---

## 4. Journal-article-only hard filter

Every source above gets an explicit "research article or review" type
gate.  Excluded types:

- OpenAlex: `book`, `book-chapter`, `editorial`, `erratum`, `letter`,
  `paratext`, `report`, `standard`.  Kept: `article`, `review`.
- EuropePMC: everything except `PUB_TYPE:"research-article"` on the
  all-years and recent sub-queries, and except `PUB_TYPE:"review-article"`
  on the reviews sub-query.
- Semantic Scholar: `publicationTypes=JournalArticle,Review` (with
  `MetaAnalysis` implicit inside Review per S2 docs).  The rest of
  S2's type vocabulary (`Conference`, `Dataset`, `Editorial`,
  `LettersAndComments`, `News`, `Study`, `Book`, `BookSection`) is
  excluded.

Historical references from the catalog that happen to be books or
book chapters are preserved via `roles: ["historical"]` — they are
not retrieved by Stage A or Stage B, but they carry their landmark
bonus from the catalog directly.  The catalog remains the source of
truth for historical landmarks.

---

## 5. Stage B — Semantic Scholar citation expansion

### 5.1 Why it belongs in Phase 3

The landmark list used to pre-seed this project is rudimentary (some
entries came from Cognitive Atlas, others from an early OpenAlex
pass); it is not a gold-standard seed.  Relying on text search alone
will systematically miss on-topic papers whose titles and abstracts
do not carry the exact phrase.  Citation expansion is the standard
remedy.  Putting it inside Phase 3 gives the human KEEP/DROP review
in Phase 5 a richer pool up front, and avoids building a second
pipeline that duplicates Phase 3's scoring, dedup, and markdown
emission.

### 5.2 Seed selection

After Stage A's phrase-gated pool is assembled for an item:

1. Collect candidates that have a non-empty S2 paperId.
2. Exclude any historical pub_id — they are guaranteed via landmark
   bonus, and spending Stage B budget on them is wasted.
3. Sort by **`influentialCitationCount` descending**, not composite
   score.  Rationale: a seed's job is to be a citation-graph hub
   whose children are likely on-topic.  `influentialCitationCount`
   is S2's own measure of non-trivial citation; a paper with high
   total citations but low influential counts is a poor seed
   (widely-cited-in-passing).
4. Take the top **50 seeds**.  If fewer than 50 candidates have S2
   paperIds and are non-historical, take whatever there are.

### 5.3 Citation fetch

For each seed:

    GET https://api.semanticscholar.org/graph/v1/paper/{paperId}/citations
        ?fields=title,abstract,tldr,year,authors,venue,
                publicationTypes,fieldsOfStudy,
                citationCount,influentialCitationCount,
                externalIds,openAccessPdf,
                intents,isInfluential
        &limit=1000

`intents` is an array of classifier tags per citation edge
(`background`, `methodology`, `result`, `extension`, etc.).
`isInfluential` is S2's binary "this citation is not a mere mention"
flag.  Both are recorded per-edge and used as ranking inputs in
Stage C.

S2 does not accept a `sort` parameter on this endpoint; the client
sorts by `citationCount` desc after fetching.  One call per seed.

Rate: budget for 1 rps regardless of S2 key. **(Corrected 2026-04-28:**
this section previously claimed citation endpoints run at 10 rps with a
key. The user's actual S2 free-tier key does not raise the rate above
1 rps for any endpoint, so the runtime budget should assume 1 rps
throughout.) Full run: 275 items × 50 seeds × 1 call = 13,750 calls at
1 rps ≈ 230 minutes (≈ 3 hours 50 minutes). Cached per paperId; a
same-day repeat run is free.

### 5.4 Per-citation filtering

Each returned citing paper is filtered in this order (fail-fast):

1. **Publication type** — accept only `JournalArticle`, `Review`,
   `MetaAnalysis`.
2. **Fields of study** — the citing paper's `fieldsOfStudy` must
   intersect the item's per-category FoS set.  If S2 returns an
   empty `fieldsOfStudy`, keep and let the phrase gate decide.
3. **Phrase gate** — title + abstract + TLDR must contain at least
   one of the item's phrases (same check as Stage A, now extended
   to TLDR).
4. **Year sanity** — drop papers with `year < 1950` or
   `year > today` (defensive; usually metadata errors).

Intent and isInfluential are **not** used as filters — they are
recorded as per-edge metadata and fed into Stage C scoring.  Filter
hard-drops lose information; scoring preserves it.

Survivors are normalized and merged into the Stage A pool on pub_id.
A candidate from both Stage A and Stage B keeps its Stage A record
and extends `sources` with `"semanticscholar_citations"`.  Stage-B-
only candidates get `sources: ["semanticscholar_citations"]`.  The
per-edge metadata (`seed_pub_id`, `intents`, `isInfluential`) is
stored on the candidate record as a list of edge-dicts for Stage C
to consume.

### 5.5 What Stage B deliberately does NOT do

- No backward citations (`/paper/{paperId}/references`).  May be
  added later if gaps remain.
- No transitive (two-hop) expansion.
- No re-seed from Stage B output.
- No intent-based filtering — intent is a score input only.

---

## 6. Per-category `fieldsOfStudy` map

**What `fieldsOfStudy` (FoS) is.**  A Semantic Scholar taxonomy that
tags each paper with one or more broad disciplines from a controlled
vocabulary of ~20 values (Neuroscience, Psychology, Medicine,
Computer Science, Linguistics, Philosophy, Economics, Biology,
Chemistry, Physics, Engineering, Business, Geology, Geography,
History, Art, Political Science, Sociology, Materials Science,
Environmental Science, Mathematics).  S2 auto-assigns these tags
based on paper content.  FoS is distinct from OpenAlex's
`topics`/`concepts` (finer-grained, different vocabulary), from
EuropePMC's MeSH terms (medical subject headings), and from
publication types (`JournalArticle`, `Review`, etc., which describe
format, not subject).

The map below translates this project's 19 `category_id` values into
the FoS vocabulary.  It is consumed in two places:

- **Stage A S2 query filter.**  Passed as the `fieldsOfStudy` query
  param on `/paper/search`; S2 returns only papers tagged with at
  least one of the listed disciplines.  This is what keeps
  cancer-biology papers out of S2's slice of Stage A.
- **Stage B FoS-overlap filter.**  Each citing paper returned by
  `/paper/{id}/citations` carries its own `fieldsOfStudy` tags; we
  require the citing paper's tags to intersect the per-category set
  here.  Empty FoS on the citing paper passes through to the phrase
  gate rather than being dropped.

| `category_id` | `fields_of_study` |
|---|---|
| associative_learning_and_reinforcement | Neuroscience, Psychology, Computer Science |
| auditory_and_pre_attentive_deviance_processing | Neuroscience, Psychology |
| awareness_agency_and_metacognition | Neuroscience, Psychology, Philosophy |
| cognitive_flexibility_and_higher_order_executive_function | Neuroscience, Psychology |
| emotion_perception_and_regulation | Neuroscience, Psychology, Medicine |
| face_and_object_perception | Neuroscience, Psychology, Computer Science |
| implicit_and_statistical_learning | Neuroscience, Psychology, Computer Science |
| inhibitory_control_and_conflict_monitoring | Neuroscience, Psychology, Medicine |
| language_comprehension_and_production | Neuroscience, Psychology, Linguistics |
| long_term_memory | Neuroscience, Psychology |
| motor_preparation_timing_and_execution | Neuroscience, Psychology, Biology |
| perceptual_decision_making_evidence_accumulation | Neuroscience, Psychology |
| reasoning_and_problem_solving | Neuroscience, Psychology, Philosophy, Computer Science |
| reward_anticipation_and_motivation | Neuroscience, Psychology, Medicine |
| selective_and_sustained_attention | Neuroscience, Psychology |
| short_term_and_working_memory | Neuroscience, Psychology |
| social_cognition_and_strategic_social_choice | Neuroscience, Psychology, Economics |
| spatial_cognition_and_navigation | Neuroscience, Psychology, Biology |
| value_based_decision_making_under_risk_and_uncertainty | Neuroscience, Psychology, Economics, Computer Science |

Default for unknown category: `"Neuroscience, Psychology"`.  Tasks
inherit the field list of the category their `process_refs` point
to; when a task spans multiple categories, union the field lists.

---

## 7. Three-layer phrase defense

### 7.1 Phrase-aware query construction

See §3.  Every multi-word phrase is quoted at the source; single
tokens are left bare (quoting a single token is a no-op in some
engines and degrades recall in others).

### 7.2 Post-retrieval phrase gate

Applied after dedup, before ranking.  Text window includes the TLDR:

    def phrase_gate(cand, item_phrases, historical_pub_ids,
                    historical_dois):
        if cand.pub_id in historical_pub_ids:
            return True
        if cand.doi and cand.doi.lower() in historical_dois:
            return True
        text = ((cand.title or "") + " " +
                (cand.abstract or "") + " " +
                (cand.tldr or "")).lower()
        for p in item_phrases:
            pl = p.lower().strip()
            if " " in pl and pl in text:
                return True
            if " " not in pl and pl in tokenize(text):
                return True
        return False

Historical landmarks are always exempt.  The gate applies equally to
Stage A and Stage B candidates.

### 7.3 Improved relevance score

Phrase-count score (unchanged from v2), now also computed over the
TLDR-extended text:

    rel = (# item phrases present in title+abstract+TLDR)
         / (# item phrases)

Bounded in [0, 1], zero for off-topic papers, scales with alias
diversity.

---

## 8. Scoring changes

### 8.1 Weight table

Contingent on §7 and §8.2 being implemented together.

| Component | v2 | v3 | Rationale |
|---|---|---|---|
| W_CITATION | 0.25 | 0.25 | Now blended; see §8.2 |
| W_VENUE | 0.20 | 0.20 | Unchanged |
| W_PUBLISHER | 0.10 | 0.10 | Unchanged |
| W_RECENCY | 0.15 | 0.15 | Unchanged |
| W_RELEVANCE | 0.25 | 0.25 | Unchanged; now over title+abstract+TLDR |
| W_REVIEW | 0.05 | 0.05 | Unchanged |
| Sum | 1.00 | 1.00 |  |
| W_INFLUENCE_INTENT | — | +0.05/edge, cap 3 | Stage-B-only bump |
| LM_BONUS | +0.30 | +0.30 | Unchanged |

The W_INFLUENCE_INTENT term sits outside the base weight sum because
it applies only to Stage-B-sourced candidates and is bounded (max
0.15 total per candidate).  A candidate reached by multiple strong
seed edges accumulates more bump, up to the cap.

### 8.2 Citation component blend

Old:

    citation_component = log_norm(citationCount)

New:

    citation_component = 0.4 * log_norm(citationCount)
                       + 0.6 * log_norm(influentialCitationCount)

Log-norm is the existing `_log_norm` helper in `rank_and_select.py`
(no change to normalization behavior).  Influential weighted more
because it is the sharper signal — S2's classifier has specifically
identified these as non-trivial citations.  Total retained as a
backstop because S2's classifier has incomplete coverage
(influential counts are missing or zero for many otherwise
well-cited papers).

### 8.3 Stage-B influence-and-intent bump

For each Stage-B-sourced candidate, iterate over its edge list
(seeds that cited it).  For each edge:

- If `edge.isInfluential == true`, it counts as a strong edge.
- Else if `edge.intents ∩ {"background", "methodology", "extension"}
  != ∅`, it counts as a strong edge.
- Otherwise it counts as a weak edge.

Bump = `0.05 × min(strong_edge_count, 3)`.  Added to composite
score after the base weighted sum, before the landmark bonus.

The cap protects against hub papers that happen to be cited by many
seeds.  0.05 is roughly 1/3 of the recency weight — meaningful but
not dominant.

### 8.4 Sign-off requirement

§8.1 weight changes, §8.2 blend, and §8.3 bump all require explicit
user sign-off per the existing rule in
`literature_search_plan_2026-04-21.md`.

---

## 9. Brief answers to the original Q1–Q6

1. **Citation chaining.**  In Phase 3 as Stage B (§5).  Forward only;
   backward deferred.
2. **S2 endpoint choice.**  Keep `/paper/search` for Stage A.  Add
   `/paper/{id}/citations` for Stage B.  `/paper/search/bulk` stays
   deferred.
3. **`fieldsOfStudy` scope.**  Per-category (§6).
4. **Scoring weights.**  Rebalanced in §8 (needs sign-off).  New
   blended citation component and Stage-B bump.
5. **Europe PMC scope.**  Keep, narrow query to TITLE/ABSTRACT,
   apply journal-article filter.
6. **`minCitationCount` floor.**  Apply 20 to S2 all-years sub-query
   only.

---

## 10. Acceptance criteria for the Sonnet session

1. **Contamination gone.**  POC rerun on `hed_response_inhibition`
   has zero cancer-biology, COVID-19, or drug-delivery papers in the
   top-25 of section 1, top-25 of section 2, and top-50 of section 3.
2. **Non-journal outputs gone.**  Zero `book-chapter`, `editorial`,
   `letter`, `erratum`, `dataset` entries in any section of the three
   POC markdowns.
3. **Stage B observable.**  `hed_response_inhibition.md` has at
   least 50 candidates whose `sources` includes
   `"semanticscholar_citations"`.
4. **TLDR rendered.**  At least 20 candidates in any POC output have
   a `TLDR:` line above their `Abstract:` line.  Candidates without
   a TLDR omit the TLDR line (no "(no TLDR)" filler).
5. **Influence-intent bump observable.**  A sanity diagnostic
   (logged at the end of `run_item`) reports the number of
   candidates with `bump > 0` and their median bump.  At least 5
   Stage-B candidates have a non-zero bump.
6. **Historical landmarks present.**  MacLeod 1991 (Stroop), Daw
   2011 (model-based), Logan & Cowan 1984 (response inhibition)
   each appear with `YES` in the landmark check.  A `NO` is a
   regression, not a case to patch.
7. **Negative-control stability.**  Stroop and model-based POCs
   retain ≥ 20/25 of their pre-revamp top-25 picks in section 1.
8. **S2 phrase-syntax check.**  Session report states whether the
   quoted-phrase smoke test (Sonnet step 6) showed quoted ≠ unquoted.
9. **Call-budget sanity.**  Stage B called `fetch_citations` ≤ 50
   times per item; ≤ 150 total new S2 citation calls across the 3
   POC items.
10. **Schema drift.**  Checksums of `process_details.json` and
    `task_details.json` before/after the run match.

---

## 11. Out of scope (still)

- OpenAlex topic crosswalk (Phase 2 deliverable).
- S2 embedding-based ranking (SPECTER 2.0); Phase 4+.
- `/paper/search/bulk` adoption (deferred).
- Backward citation expansion (may add later if forward alone leaves
  gaps).
- Transitive (two-hop) citation expansion.
- Any mutation of `process_details.json` or `task_details.json`.

---

## 12. Files the Sonnet session will touch

- `code/literature_search/search_queries.py`  — per-category FoS,
  phrase list, pass parameters, sub-query labels renamed.
- `code/literature_search/fos_map.py`  — **new**.  Category→fields.
- `code/literature_search/clients/openalex.py`  — phrase-aware
  filter, journal-article type filter.
- `code/literature_search/clients/europepmc.py`  — TITLE/ABSTRACT
  phrase, journal-article PUB_TYPE filter.
- `code/literature_search/clients/semanticscholar.py`  — pass
  `minCitationCount`, `publicationTypes`; extended fields list with
  `tldr`, `influentialCitationCount`; **new** `fetch_citations`
  function with `intents` and `isInfluential` in its fields list;
  **new** `fetch_references` (unwired, symmetric).
- `code/literature_search/normalize.py`  — extend `Candidate` with
  `tldr`, `influential_citation_count`, `s2_paper_id`, and a
  `stage_b_edges: list[dict]` field.
- `code/literature_search/rank_and_select.py`  — new weights, blended
  citation component, phrase-gate-with-TLDR, relevance-score-with-
  TLDR, phrase gate function, seed selection helper, influence-intent
  bump helper.
- `code/literature_search/phase3_search.py`  — wire phrase gate,
  Stage B orchestration, sanity logging.
- `code/literature_search/present_candidates.py`  — section header
  rename, TLDR rendering above abstract in detail block.
- `instructions/task_search_revamp_sonnet_2026-04-24.md`  — companion
  instruction file.
- `.status/session_2026-04-24_search_strategy_design.md`  — thinking
  summary; append v3 iteration log.

POC candidate markdown files in `outputs/phase3/candidates/` are
regenerated; no manual edits to those files.
