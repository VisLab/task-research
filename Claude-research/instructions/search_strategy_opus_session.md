# Search strategy design — Opus planning session

**Created:** 2026-04-24  
**Purpose:** Input document for an Opus session to design a production-quality
per-item literature search strategy before running Phase 3 on all 275 items.  
**Context file:** `CLAUDE.md` (read first), `instructions/literature_search_plan_2026-04-21.md`

---

## What has been built and tested (do not rebuild)

The Phase 3 pipeline is running. Infrastructure is complete:

| Layer | Status |
|---|---|
| Cache (`cache.py`) | Working — date-stamped, immutable, SHA-1 keyed |
| Normalization (`normalize.py`) | Working — OpenAlex, EuropePMC, S2 → `Candidate` dataclass |
| Deduplication (`rank_and_select.py`) | Working — DOI-first merge, pub_id fallback |
| Scoring (`rank_and_select.py`) | Working but weights need review (see below) |
| Query plan builder (`search_queries.py`) | Working but naive (see problems) |
| Candidate markdown writer (`present_candidates.py`) | Working |
| Landmark supplementary lookup (`phase3_search.py`) | Working — explicit DOI fetch for historical refs missed by text search |
| S2 `fieldsOfStudy` filter | Just added — `"Neuroscience,Psychology"` default |

Three API clients are working: OpenAlex (`search_works`, `lookup_by_doi`),
EuropePMC (`search`, `lookup_by_doi`, `lookup_by_pmid`),
Semantic Scholar (`search`, `lookup_by_doi`).

A POC run on 3 items completed successfully (279s cold, ~30s warm).

---

## Problems observed in POC that motivate this session

### Problem 1 — Off-topic contamination via S2 (partially fixed)

**Root cause:** S2's `/paper/search` without a `fieldsOfStudy` filter returns papers
from all domains. For items with short names containing common biology terms
(e.g. "Response inhibition"), cancer biology papers (CDK4/6 inhibitors, PARP
inhibitors) and COVID papers appeared in the candidate pool and were picked
because their citation counts and venue tiers overwhelmed the low relevance weight.

**Partial fix applied:** Added `fieldsOfStudy=Neuroscience,Psychology` to all S2
queries. This eliminates most off-topic contamination but raises a design question:
some items in the catalog span Neuroscience AND Computer Science (e.g.
`hed_model_based_learning`) or Neuroscience AND Medicine (e.g. addiction, anxiety
processes). A single global `fieldsOfStudy` value may be wrong for ~30–40 items.

**Open question for Opus:** Should `fields_of_study` be per-item (set in the JSON
catalog) or per-category (set by process/task category), and what is the right
vocabulary? The catalog has 172 processes across ~20 categories.

### Problem 2 — Text search misses foundational papers that predate modern vocabulary

**Root cause:** Many foundational papers (pre-1995) were written before the field
settled on current terminology. Their titles don't contain the item's primary name.
Examples:
- Logan & Cowan (1984): "On the ability to inhibit **thought and action**" — no "response inhibition" in title
- Stroop (1935): 1935 paper, not indexed with searchable abstract in modern APIs

**Fix applied:** Supplementary DOI lookup after text search; historical refs with
DOIs are explicitly fetched if not found by text search.

**Remaining gap:** Historical refs without DOIs (rare after the data fix, but possible)
and foundational papers that were never stored as historical refs but should be
primary retrieval targets. The text search is the only path for the second group.

### Problem 3 — Current S2 usage is shallow

We use `/paper/search` with `limit=100`. The S2 API has capabilities we are not using:

**`/paper/search/bulk`**  
- Boolean query against title+abstract (not just relevance matching)
- Cursor-based pagination — no 1000-result cap
- Supports `sort=citationCount` for citation-sorted retrieval
- Supports `publicationTypes` filter (Review, JournalArticle, etc.)
- Better suited for systematic search than `/paper/search`

**Citation network endpoints**  
- `/paper/{id}/citations` — forward citations (papers that cite a landmark)
- `/paper/{id}/references` — backward citations (what a landmark cites)
- For well-chosen seed papers, forward citation retrieval is arguably the most
  reliable way to find relevant literature: every paper that cites Logan & Cowan
  (1984) is, by definition, engaging with response inhibition research

**`/paper/batch`** (POST)  
- Fetch up to 500 papers by DOI/PMID/S2ID in one request
- Useful for enriching candidates already found via other sources

**`minCitationCount`** filter  
- Available on `/paper/search` — can set a floor to reduce noise in foundational pass

**SPECTER 2.0 embeddings** (`embedding` field)  
- Semantic similarity vectors; could be used to rank candidates by proximity to
  the centroid of the landmark paper embeddings

### Problem 4 — Current scoring weights are misbalanced

The locked scoring formula:
```
0.35 × citation_percentile
0.20 × venue_tier
0.15 × publisher_tier
0.15 × recency
0.10 × query_relevance    ← too low
0.05 × review_bonus
+0.30 × historical_bonus
```

Citation + venue together = 0.55. Relevance = 0.10. A high-impact off-topic paper
can outscore a relevant lower-impact paper even after the `fieldsOfStudy` fix,
because the filter only helps with S2 results; OpenAlex and EuropePMC still have
no equivalent domain filter for general search.

The `fieldsOfStudy` fix addresses the S2 contribution; whether weights need
changing depends on how bad the OpenAlex/EuropePMC contamination remains after
the fix. This should be evaluated in the second POC run.

---

## Available API capabilities (summary for design)

### Semantic Scholar

| Endpoint | Best for | Pagination | Rate limit |
|---|---|---|---|
| `/paper/search` | Quick relevance search | offset (max 1000 total) | 1 rps |
| `/paper/search/bulk` | Systematic/boolean search | cursor (unlimited) | 1 rps |
| `/paper/{id}/citations` | Forward citation chaining | offset | 10 rps |
| `/paper/{id}/references` | Backward citation chaining | offset | 10 rps |
| `/paper/batch` (POST) | Enrichment by known ID | single call, up to 500 | 1 rps |

Key filters available on search endpoints:
- `fieldsOfStudy`: domain restriction (Neuroscience, Psychology, Medicine, ...)
- `year`: range filter "YYYY-YYYY", "YYYY-", "-YYYY"
- `publicationTypes`: Review, JournalArticle, CaseReport, ...
- `minCitationCount`: floor on citations (useful for foundational pass)
- `openAccessPDF`: restrict to OA papers

Key fields for our use:
- `paperId, externalIds, title, abstract, authors, year, venue`
- `citationCount, influentialCitationCount`
- `isOpenAccess, openAccessPdf`
- `tldr` (1-sentence AI summary)
- `publicationTypes`
- `fieldsOfStudy, s2FieldsOfStudy`
- `embedding` (SPECTER 2.0 — 768-dim vector)

Retry pattern from S2's own examples (from `s2-folks` repo):
```python
HTTPAdapter(max_retries=Retry(
    total=6, backoff_factor=2.0, backoff_jitter=0.5,
    respect_retry_after_header=True,
    status_forcelist=[429, 502, 503, 504],
    allowed_methods={'GET', 'POST'}
))
```
Current client does NOT use this pattern; it has manual retries.

### OpenAlex

| Endpoint | Best for |
|---|---|
| `GET /works?search=<q>` | Full-text relevance search |
| `GET /works?filter=...` | Filtered retrieval (topic, type, date, OA) |
| Cursor pagination | Up to 200/page, unlimited depth |

Key filters:
- `topics.id:<id>` — topic-based filtering (requires crosswalk, currently absent)
- `type:review` — review-type papers
- `from_publication_date`, `to_publication_date`
- `cited_by_count:>N` — citation floor
- `open_access.is_oa:true` — OA filter

OpenAlex also has a concepts/topics taxonomy that was pulled to `H:\Research\OpenAlex\`.
The crosswalk file (`outputs/phase2/openalex_crosswalk.json`) does not currently
exist, so all OpenAlex queries run in text-only mode. Building this crosswalk is
a separate Phase 2 deliverable.

### EuropePMC

Lucene query syntax, `sort=CITED desc`, `resultType=core`. Good for MeSH-filtered
review retrieval. Generally weaker at full-text search than OpenAlex/S2 for
cognitive science because its focus is biomedical literature.

---

## Specific design questions for the Opus session

### Q1 — Citation chaining: should it be a Phase 3 pass or a separate phase?

**Option A:** Add citation chaining as a 4th pass inside Phase 3. For each item,
after the text search passes, collect the S2 paper IDs of all historical refs found
in the candidate pool and fetch their forward citations. Merge with text search
results before scoring.

Pros: single pipeline, historical refs anchor the citation set  
Cons: adds ~100–500 API calls per item; Phase 3 runtime grows significantly;
citation sets from popular landmarks can be enormous (Logan & Cowan: 2500 papers)

**Option B:** Keep Phase 3 as text-only search; add citation chaining as Phase 4
(currently described as "co-mention search"). This matches the existing plan structure.

Pros: separation of concerns; Phase 3 stays fast and reproducible  
Cons: landmark papers only appear via DOI lookup (already implemented), not via
citation context

**Recommendation needed:** Is forward citation from landmarks a Phase 3 pass or
Phase 4?

### Q2 — `/paper/search` vs `/paper/search/bulk` for S2

`/paper/search/bulk` supports boolean queries (AND/OR) against title+abstract
and cursor pagination with no hard limit. For items like `hed_response_inhibition`
the boolean query `"response inhibition" OR "inhibitory control" OR "stop-signal"`
would be more precise than separate per-alias calls.

However, the bulk endpoint does NOT support `minCitationCount` or sorting by
citation count (only by `publicationDate` or relevance). The regular `/paper/search`
supports `minCitationCount` and is sorted by relevance.

**Recommendation needed:** Which endpoint for which pass? Possible strategy:
- Foundational pass: `/paper/search` with `minCitationCount=50`, sorted by relevance
- Recent pass: `/paper/search/bulk` with boolean query, sorted by publicationDate
- Reviews pass: `/paper/search` with `publicationTypes=Review`

### Q3 — `fieldsOfStudy` — global default vs per-item vs per-category

Current: `"Neuroscience,Psychology"` applied globally to all 275 items.

Categories in the catalog that likely need different values:
- Addiction, Anxiety, Depression, PTSD processes → add `"Medicine"`
- Model-based learning, Reinforcement learning → add `"Computer Science"`
- Language processes → may need `"Linguistics"` (though coverage is poor in S2)

Options:
- **Global default + category overrides** stored in `search_queries.py` as a dict keyed on `category_id`
- **Per-item override** stored in `process_details.json` / `task_details.json` as a `s2_fields_of_study` field
- **Compute from existing catalog metadata** using the category_id already on each item

Recommendation needed: where should this configuration live?

### Q4 — Scoring weights: should `W_RELEVANCE` increase?

The `fieldsOfStudy` fix eliminates most S2 contamination. But OpenAlex and EuropePMC
have no equivalent domain filter. If OpenAlex still contributes off-topic papers,
the weight imbalance (0.55 citation+venue vs 0.10 relevance) will remain a problem.

Evaluate after the second POC run. If off-topic papers persist in OpenAlex/EuropePMC
picks, recommend a weight rebalance.

Candidate rebalance:
```
W_CITATION:   0.35 → 0.25
W_VENUE:      0.20 → 0.20  (unchanged)
W_PUBLISHER:  0.15 → 0.10
W_RECENCY:    0.15 → 0.15  (unchanged)
W_RELEVANCE:  0.10 → 0.25
W_REVIEW:     0.05 → 0.05  (unchanged)
```
Total: 1.00 ✓. This requires explicit user sign-off before implementation.

### Q5 — EuropePMC: keep or reduce?

EuropePMC is the weakest of the three sources for cognitive neuroscience. Its
strengths are: MeSH terms (useful for review filtering), PMID coverage, and
European institutional coverage. Its weaknesses are: Lucene query fragility,
limited abstract indexing for older papers, biomedical focus.

Question: should EuropePMC be dropped from the foundational pass and kept only
for the reviews pass (where `PUB_TYPE:review` with MeSH is genuinely useful)?
This would reduce API calls by ~33% and reduce contamination from biomedical
papers that don't belong in a cognitive science catalog.

### Q6 — `minCitationCount` floor for foundational pass

Adding `minCitationCount=20` to S2 foundational pass would eliminate papers with
fewer than 20 citations, reducing noise without significant recall loss for
foundational literature. Does this make sense? What threshold?

---

## Constraints the strategy must respect

- **Idempotency:** re-running on the same day must cost zero API calls (cache hit)
- **Rate limits:** S2 without key: 1 rps for search endpoints. Full run of 275 items
  with 3 passes × 3 sources × up to 3 alias queries = potentially 2,475 S2 calls
  at 1 rps = ~41 minutes just for S2. With S2 key: 1 rps for search (key helps
  for GET /paper/* endpoints but NOT for /paper/search per S2 docs)
- **Reproducibility:** all API calls go through the date-stamped cache; re-runs
  on a different day re-fetch (by design). This is acceptable.
- **No mutation of process_details.json or task_details.json in Phase 3**
- **Weights locked without explicit user sign-off**
- **No Google Scholar scraping (manual only)**

---

## What the Opus session should produce

A written design decision covering each of Q1–Q6 above, plus:

1. A revised pass structure for S2 (which endpoints, which parameters per pass)
2. A `fieldsOfStudy` assignment strategy (global default + override mechanism)
3. A recommendation on whether citation chaining belongs in Phase 3 or Phase 4
4. A recommendation on weight rebalancing (or confirmation that the `fieldsOfStudy`
   fix is sufficient)
5. A recommendation on EuropePMC scope reduction
6. Any other improvements identified from reading the S2 API docs

The output should be precise enough to drive code changes without further ambiguity.
Place the output in `instructions/search_strategy_decisions_<date>.md`.

---

## Files to read before the Opus session

```
CLAUDE.md                                           project conventions
instructions/literature_search_plan_2026-04-21.md  full plan (§6 scoring, §11.7 identity)
instructions/task_literature_search_phase3_instructions.md
code/literature_search/search_queries.py            current query plan builder
code/literature_search/rank_and_select.py           scoring formula
code/literature_search/clients/semanticscholar.py   current S2 client
code/literature_search/phase3_search.py             orchestrator
H:\Research\SemanticScholar\docs\                   S2 best practices (user notes)
H:\Research\SemanticScholar\s2-folks\               S2 official API examples
H:\Research\OpenAlex\                               OpenAlex taxonomy + pull script
outputs/phase3/candidates/hed_response_inhibition.md   POC result — has contamination
outputs/phase3/candidates/hedtsk_stroop_color_word.md  POC result — clean
outputs/phase3/candidates/hed_model_based_learning.md  POC result — mostly clean
.status/session_2026-04-24_phase3_preflight.md      bug log from this session
```
