# Task: Literature Search — Phase 3 systematic per-item search

**Original date:** 2026-04-23  
**Last updated:** 2026-04-23 (post-reorganisation)  
**Status:** Infrastructure complete. POC run pending.

---

## What Phase 3 is

For each of the 172 processes and 103 tasks, query OpenAlex, Europe PMC, and
Semantic Scholar; deduplicate across sources; score each candidate with the
composite ranking from the parent plan §6; and emit one per-item candidate
markdown for human review.

Phase 3 does **not** mutate `process_details.json` or `task_details.json` —
it produces candidate files only. Mutation happens in Phase 8 after Phase 5
human review.

Parent plan: `instructions/literature_search_plan_2026-04-21.md`.  
Session reports: `.status/session_2026-04-21_literature_search_phase1.md`,
`.status/session_2026-04-22_literature_search_phase2.md`,
`.status/session_2026-04-23_reorganisation_and_schema.md`.

---

## What is already built (do not rebuild)

All Phase 3 infrastructure was written and verified on 2026-04-23.
All scripts live in `code/literature_search/` (not `outputs/`).

| File | Purpose |
|---|---|
| `code/literature_search/identity.py` | `build_pub_id`, `build_canonical_string`, `build_pdf_filename` |
| `code/literature_search/cache.py` | `cache_get_or_fetch` — date-stamped disk cache |
| `code/literature_search/triage_rules.py` | `classify_venue`, `publisher_tier_from_doi`, venue/publisher allowlists |
| `code/literature_search/normalize.py` | `Candidate` dataclass; `normalize_openalex/europepmc/s2` |
| `code/literature_search/search_queries.py` | `ItemQueryPlan`; `build_plans_from_json`; `POC_ITEM_IDS` |
| `code/literature_search/rank_and_select.py` | `dedup_candidates`; `composite_score`; `select_candidates` |
| `code/literature_search/present_candidates.py` | `write_item_markdown`; `write_index` |
| `code/literature_search/phase3_search.py` | **Host entrypoint** — the script the user runs |
| `code/literature_search/clients/openalex.py` | `lookup_by_doi`; `search_works` |
| `code/literature_search/clients/europepmc.py` | `lookup_by_doi`; `lookup_by_pmid`; `search` |
| `code/literature_search/clients/semanticscholar.py` | `lookup_by_doi`; `search` |
| `code/literature_search/clients/crossref.py` | `lookup_by_doi`; `lookup_by_query` |
| `code/literature_search/clients/unpaywall.py` | `lookup_by_doi` |
| `code/literature_search/migrate_references.py` | One-time schema migration (already applied) |

---

## Current data state

**`process_details.json`** (172 processes) and **`task_details.json`** (103 tasks)
have been migrated to a unified reference schema (2026-04-23):

```json
"references": [
  {
    "citation_string": "Stroop (1935) ...",
    "roles": ["historical"],
    "doi": "10.1037/h0054651",
    "authors": "Stroop, J. R.",
    "title": "Studies of interference in serial verbal reactions.",
    "year": 1935,
    "venue": "Journal of Experimental Psychology"
  }
]
```

Role vocabulary: `historical | review | experiment | dataset | other | unknown`.  
Historical references are **locked** (127 total: 61 in processes, 66 in tasks).
All other existing references have `roles: ["unknown"]` pending Phase 5 review.

The old `fundamental_references`, `recent_references`, and `key_references`
arrays no longer exist.

---

## Sandbox constraint

The Cowork Linux sandbox has no network egress. Phase 3 must be run on the
Windows host where API access is available. The script is designed for this:

```
python code/literature_search/phase3_search.py --mode poc --write
```

---

## How Phase 3 scoring uses existing references

Phase 3 does **not** use a separate landmark file. Instead, `phase3_search.py`
loads `process_details.json` and `task_details.json` directly and reads
references with `roles: ["historical"]` for each item. These get a +0.30
scoring bonus in the composite score and are pinned in the foundational slot
of the candidate markdown.

Scoring formula (plan §6, weights locked):
```
0.35 × citation_percentile   (OpenAlex field-normalized)
0.20 × venue_tier_score       (flagship=1.0, mainstream=0.7, specialty=0.4, unknown=0.3)
0.15 × publisher_tier_score   (Tier A=1.0, Tier B=0.6, Tier C/None=0.0)
0.15 × recency_score          (triangular peak at today−5, zero at today−20)
0.10 × query_relevance        (word overlap of process/task name with title+abstract)
0.05 × review_bonus           (is_review or is_meta_analysis)
+0.30 × historical_bonus      (reference matches a historical ref for this item)
```

---

## API keys

Keys are read from environment variables (priority) or `code/.apikeys`:
```
S2_API_KEY=<key>      Semantic Scholar: 1 rps without, 100 rps with
NCBI_API_KEY=<key>    Not used by Phase 3 (Europe PMC is used instead)
```

Without an S2 key: POC takes ~5 min cold, full run ~60–90 min.  
With an S2 key: full run ~10 min.

OpenAlex and Europe PMC require no key; polite-pool access via
`mailto=hedannotation@gmail.com` is already configured.

---

## OpenAlex topic crosswalk

The crosswalk file (`outputs/phase2/openalex_crosswalk.json`) is checked at
startup but is optional. If absent, all queries run in text-only mode — no
topic filter. This is acceptable; topic filtering is an optimization, not a
correctness requirement. The file does not currently exist; text-only mode
will be used.

---

## POC items

Three items chosen to test the full pipeline:

1. `hed_response_inhibition` — well-studied process, clear historical refs
   (Logan & Cowan 1984; Aron, Robbins & Poldrack 2014).
2. `hedtsk_stroop_color_word` — task with multiple aliases; tests OR-query
   construction and alias union.
3. `hed_model_based_learning` — modern-skewed (Daw et al. 2011); tests the
   recency pass and RL/comp-psychiatry venue mix.

---

## Running Phase 3

All commands run from the workspace root.

### POC (< 5 min cold, ~2 min warm)
```
python code/literature_search/phase3_search.py --mode poc --write
```

Outputs:
- `outputs/phase3/candidates/hed_response_inhibition.md`
- `outputs/phase3/candidates/hedtsk_stroop_color_word.md`
- `outputs/phase3/candidates/hed_model_based_learning.md`
- `.status/candidates_index_<today>.md`

### POC verification checklist
1. Three candidate markdown files produced.
2. Historical references appear in Section 1 (Foundational) with bonus score.
3. At least 3 reviews appear in Section 2 (Recent).
4. No single author appears >3 times across picked slots.
5. Zero API calls on a second run (idempotency — warm cache).
6. Composite scores look sensible (flagship journals outrank specialty with
   comparable citation counts).

### Re-running a single item
```
python code/literature_search/phase3_search.py --mode single --ids hed_response_inhibition --write
```

### Full run (all 275 items)
Only after POC is approved:
```
python code/literature_search/phase3_search.py --mode full --write
```
Expected wall time: ~10 min with S2 key, ~60–90 min without.

---

## Default argument values (phase3_search.py)

```
--workspace    .                              (current directory = workspace root)
--cache-dir    outputs/cache
--output-dir   outputs/phase3/candidates
--apikeys      code/.apikeys
--index        .status/candidates_index_<today>.md
--sources      openalex,europepmc,semanticscholar
--passes       foundational,recent,reviews
--write        (not set by default — dry-run)
```

---

## What comes after Phase 3

1. User reviews three POC candidate files; approves or requests adjustments.
2. Run `--mode full` to generate all 275 candidate files.
3. **Phase 4 (co-mention search):** Separate session. Reuses same clients and
   scoring. Queries are (process × task) pairs, not per-item.
4. **Phase 5 (human review):** Open `.status/candidates_index_<date>.md`.
   Tick KEEP/DROP and assign `role:` for each candidate.
5. **Phase 6 (publications.json):** Converts KEEPs into the canonical
   publications store.

---

## What is explicitly NOT part of Phase 3

- Co-mention search (Phase 4)
- Candidate selection / KEEP-DROP (Phase 5)
- `publications.json` creation (Phase 6)
- Zotero interaction (Phase 6)
- PDF acquisition (Phase 7)
- Mutating `process_details.json` or `task_details.json` (Phase 8)
- Google Scholar scraping (manual only, always)
- Tuning ranking weights without user sign-off

---

## CRITICAL: file access rules

See `CLAUDE.md` §"Windows / Cowork sandbox file access" for the full rules.
Summary:

- Read workspace JSON files → **Read tool** (not bash `cat`)
- Write workspace files → **Write or Edit tool**
- Run scripts → **bash** (Linux mount path)
- Temporary files → **`.scratch/`**
- If an Edit-tool change is invisible to bash → rewrite the full file via bash
  `cat > file << 'EOF' ... EOF`
