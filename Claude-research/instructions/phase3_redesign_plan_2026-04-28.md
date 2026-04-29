# Phase 3 redesign — JSON pipeline, tier classification, species filter, separated extract/render

**Date:** 2026-04-28
**Status:** Implementation complete; pending POC rerun and human-review session.
**Replaces:** the per-item markdown emitter previously in `present_candidates.py`.

This document describes the redesigned Phase 3 deliverable: how the
literature search produces machine-readable candidates, how the picked
tier is extracted into a reviewer-friendly form, and how a markdown view
is rendered on demand. It is the canonical reference for how the three
new scripts fit together.

The original Phase 3 plan
(`instructions/literature_search_plan_2026-04-21.md` §8.3) is still the
authority on the **search** itself — query construction, scoring, Stage A
and Stage B mechanics. Where this document and the original disagree on
output format, role assignment, or human-review workflow, this document
wins.

---

## 1. Why the redesign

Three concrete problems with the old per-item markdown:

1. **Manual review at scale was infeasible.** Each item had ~50 candidates
   in a free-form markdown with KEEP/DROP checkboxes; 275 items times 50
   decisions is a multi-week task no reviewer would finish.
2. **The presentation was confusing.** Two parallel ranked tables ("Top"
   and "Recent") overlapped heavily — the same paper appeared with
   different row IDs (`3P` and `1R`) and the reviewer had to mentally
   deduplicate. The `P`/`R` suffix system was unobvious.
3. **No species filter and opaque scores.** Rodent and non-human-primate
   studies competed with human work for picked-tier slots. Composite
   scores were close (0.93 vs 0.71) with no breakdown shown, so the
   reviewer couldn't tell *why* one paper outranked another.

The remedies are independent and additive: separate the
machine-deliverable from the human-readable form; filter species before
ranking; render with badges and on-demand detail; pre-populate review
state so the reviewer's default action is "do nothing."

---

## 2. Architecture: three independent steps

Each step has a single responsibility. Each can be re-run alone.

| Step | Script | Inputs | Output | Re-run when |
|---|---|---|---|---|
| 1. Search | `code/literature_search/phase3_search.py` | catalog + cache + APIs | `outputs/phase3/candidates/<item>.json` | aliases changed, sources changed, time passed |
| 2. Extract | `code/literature_search/phase3_extract_review.py` | candidates JSON (+ existing review JSON) | `outputs/phase3/review/<item>.json` | scoring tuned, picked-tier rules tuned, threshold changed |
| 3. Render | `code/literature_search/phase3_render.py` | candidates + review | `outputs/phase3/rendered/<item>.md` | want a fresh view, format changed |

**Cost separation.** Re-running step 1 means hitting the APIs again
(~60–90 minutes cold for 275 items at S2's 1 rps). Re-running step 2
is seconds — it works on the JSON only. Re-running step 3 is also
seconds. So tuning the picked-tier criteria, score weights, or display
format does not force a re-fetch.

**State separation.** Step 1 writes a deterministic output that depends
only on the search config and the cached API responses. Step 2 reads
that and may also read prior human review state, replaying it on the
new candidates (rebase, §4). Step 3 reads both and produces a
read-only artifact.

---

## 3. File layout

Per item, three artifacts:

```
outputs/phase3/
  candidates/<item_id>.json   <- step 1 output. ALL candidates with tier set.
  review/<item_id>.json       <- step 2 output. Picked-tier decisions only.
  rendered/<item_id>.md       <- step 3 output. Human-readable view.
```

The candidates file is the canonical record. It contains every paper the
search retrieved, ranked once by composite score, with `tier ∈ {picked,
reserve, excluded}` set on each. Picked papers go to step 2; reserve
papers are available for promotion; excluded papers are kept for audit
(filtered for cause: non-human subjects, missing year+DOI, below
threshold).

The review file is the human-input layer. It is **never overwritten by
the search step**; only step 2 modifies it, and step 2 preserves prior
decisions via rebase.

The rendered markdown is a derived view. It can be regenerated at any
time from the other two and never carries authoritative state.

---

## 4. Candidates JSON shape

Schema id: `phase3_candidates_v1`. One file per item.

```json
{
  "schema_version": "phase3_candidates_v1",
  "generated": "2026-04-28T15:21:38",
  "item": {
    "kind": "process",
    "id": "hed_response_inhibition",
    "name": "Response inhibition",
    "definition": "Suppression of a prepotent or already-initiated response...",
    "category_id": "inhibitory_control_and_conflict_monitoring",
    "aliases": [
      {"name": "inhibitory control"},
      {"name": "response suppression",
       "note": "more common in motor-control and oculomotor literatures"}
    ]
  },
  "run": {
    "sources": ["openalex", "europepmc", "semanticscholar"],
    "passes":  ["all_years", "recent", "reviews"],
    "stage_b": {"seeds": 50, "raw": 942, "after_filters": 28, "merged": 28},
    "filters": {
      "species": "human_only_or_unknown",
      "publication_types_stage_a": ["JournalArticle", "Review", "Dataset", "MetaAnalysis"],
      "publication_types_stage_b": ["journalarticle", "review", "metaanalysis", "dataset"]
    },
    "tier_thresholds": {"n_picked": 30, "n_reserve": 30, "drop_unknown_species": false, "min_picked_score": null},
    "totals": {"deduped": 2763, "picked": 30, "reserve": 30, "excluded": 2703,
               "landmarks_found": 4, "landmarks_total": 4},
    "exclusion_reasons": {"non_human_subjects": 12, "below_reserve_cutoff": 2691, "no_year_no_doi": 0}
  },
  "candidates": [
    {
      "rank": 1,
      "tier": "picked",
      "auto_role": "key_review",
      "pub_id": "pub_a3b9f2c1",
      "doi": "10.1016/j.tics.2013.12.003",
      "url": "https://doi.org/10.1016/j.tics.2013.12.003",
      "openalex_id": null,
      "pmid": null,
      "first_author": "Aron",
      "authors_display": "Aron, A. R., Robbins, T. W., & Poldrack, R. A.",
      "year": 2014,
      "title": "Inhibition and the right inferior frontal cortex: one decade on.",
      "venue": "Trends in Cognitive Sciences",
      "venue_tier": "flagship",
      "publisher": null,
      "is_review": true,
      "is_meta_analysis": false,
      "human_subject": true,
      "species_evidence": ["mesh:Humans"],
      "citation_count": 1875,
      "influential_citation_count": 312,
      "fwci": null,
      "cited_by_percentile_year": null,
      "oa_status": null,
      "oa_url": null,
      "tldr": "It is proposed that the rIFC ...",
      "abstract": "...",
      "score": {
        "composite": 0.935,
        "breakdown": {
          "raw": {
            "citations": 0.78, "venue": 1.0, "publisher": 0.0,
            "recency": 0.65, "relevance": 0.92, "review": 1.0
          },
          "weighted": {
            "citations": 0.195, "venue": 0.20, "publisher": 0.0,
            "recency": 0.098, "relevance": 0.23, "review": 0.05
          },
          "stage_b_bump":  0.10,
          "landmark_bonus": 0.0
        }
      },
      "provenance": {
        "sources": ["semanticscholar", "semanticscholar_citations"],
        "stage_b_seed_pub_ids": ["pub_b1a2c3d4", "pub_e5f6a7b8"]
      },
      "mesh_terms": ["Humans", "Inhibition (Psychology)"]
    },
    ...
  ]
}
```

**What's surfaced and why:**

- `score.breakdown.raw` and `score.breakdown.weighted` together let you
  re-rank without re-fetching — multiply raw by new weights, sum, add
  the bumps.
- `species_evidence` is a list of strings explaining how the species
  classifier decided. Two sample values:
  `["mesh:Humans"]` (decisive positive),
  `["token:animal (rats)", "decision:mixed→human"]` (rats appeared but
  there was a human signal too, so kept as human-eligible).
- `auto_role` is one of `historical | key_review | recent_primary |
  foundational`. Methods is part of the role vocabulary but is never
  auto-assigned (heuristic detection is unreliable; reviewers can set
  `role_override` to "methods" by hand).
- `provenance.sources` shows which APIs returned the candidate.
  `stage_b_seed_pub_ids` shows which seed papers cited it (only
  populated for Stage B candidates).

---

## 5. Review JSON shape

Schema id: `phase3_review_v1`. One file per item. **Pre-populated by
step 2; edited by the reviewer; never touched by step 1.**

```json
{
  "schema_version": "phase3_review_v1",
  "item": { /* same identity block as the candidates file */ },
  "candidates_run_date": "2026-04-28T15:21:38",
  "extracted_on": "2026-04-28T15:30:12",
  "extraction": {"max_picked": null, "n_picked": 30},
  "decisions": [
    {
      "rank": 1,
      "label": "Aron 2014 — Inhibition and the right inferior frontal cortex one decade on (Trends in Cognitive Sciences, key_review, 1875×)",
      "doi": "10.1016/j.tics.2013.12.003",
      "pub_id": "pub_a3b9f2c1",
      "auto_role": "key_review",
      "score": { /* same breakdown as in candidates */ },
      "human_subject": true,
      "year": 2014,
      "venue": "Trends in Cognitive Sciences",
      "citation_count": 1875,
      "action": null,
      "role_override": null,
      "notes": null
    },
    ...30 entries
  ],
  "previously_decided": [
    {
      "label": "Verbruggen 2008 — Response inhibition in the stop-signal paradigm",
      "doi": "10.1016/j.tics.2008.07.005",
      "pub_id": "pub_b2c1d3e4",
      "year": 2008,
      "venue": "Trends in Cognitive Sciences",
      "action": "accept",
      "role_override": null,
      "notes": null,
      "current_tier": "reserve",
      "current_rank": 34,
      "rebase_note": "previously picked; now in 'reserve'. Phase 6 ignores non-picked entries; promote it back if you still want it included."
    }
  ]
}
```

**Decision values:**

| field | meaning |
|---|---|
| `action: null` | accept — use the auto pick. **This is the default for every row.** |
| `action: "accept"` | explicit accept. Same effect as null but recorded explicitly. |
| `action: "veto"` | drop this paper from Phase 6 even though the ranker picked it. |
| `action: "promote"` | only on rows the reviewer added — pull a reserve-tier paper into the picked set. |
| `role_override: <string>` | replace the auto_role for this paper. Used when the reviewer disagrees with the classification (e.g., "methods" instead of "recent_primary"). |
| `notes: <string>` | one-line free text. For audit. |

**Default-accept is intentional.** The reviewer's job is to scan the
table and intervene where the system is wrong, not to confirm every
auto pick. For a typical item the reviewer touches 0–3 rows.

The `previously_decided` block is the rebase audit trail (§4).

---

## 6. Rebase semantics on re-extract

When step 2 runs and a review file already exists, the existing decisions
are replayed against the new candidate set. Match key is DOI (lowered)
first, `pub_id` second.

| Prior state | New state | Result |
|---|---|---|
| accept on Aron 2014 | Aron 2014 still in picked tier | accept carried forward; rank field updated |
| veto on Foo 2019 | Foo 2019 still in picked tier | veto carried forward |
| accept on Bar 2010 | Bar 2010 now in reserve tier | moved to `previously_decided` with rebase_note |
| accept on Baz 2008 | Baz 2008 not in candidates at all | moved to `previously_decided` with rebase_note "no longer in current candidates" |
| no prior decision | new pick at rank 17 | row added to decisions with action=null |
| accept (in `previously_decided`) | back in picked tier | promoted to live decisions; accept carried forward |

The output is deterministic given (existing review state, new candidates).
Re-running step 2 with no candidates change is idempotent.

The reviewer's previous work is never silently dropped — at worst it
ends up in `previously_decided` where it remains visible. That section
is the audit trail.

---

## 7. Rendered markdown contract

Schema-free; for human eyes only.

Sections:

1. **Header.** Item name, definition, aliases, category. For tasks,
   short_definition and inclusion_test are also rendered.
2. **Run block.** A small table: generated date, sources, totals,
   landmarks found, exclusion counts.
3. **Picked.** Single sorted table by rank. Columns: `# | Year | First
   author | Venue | Cites | Badges | Auto role | Score | Decision | Title`.
   Badges: `H` historical, `R` review/meta-analysis, `N` recent_primary,
   `F` flagship venue.
4. **Picked detail blocks.** For each picked row, a `<details>` block
   collapsed by default containing the score breakdown table (raw +
   weighted per component, plus bumps), TLDR, and abstract.
5. **Reserve.** Collapsed `<details>` with a smaller table for the
   reserve tier. No detail blocks (those are for picked-tier rows where
   review effort is concentrated).
6. **Excluded.** Counts by reason. Optionally (with `--include-excluded`)
   a list of non-human exclusions for spot-checking the species filter.
7. **Previously decided.** Only present when the review file has a
   `previously_decided` block. Audit-only.

The `Decision` column shows the current review state for each picked
row: `accept` (default), `veto`, `promote`, etc., or `(no review)` when
no review file exists yet.

---

## 8. Implementation summary

Files added or modified:

| Path | Status | Purpose |
|---|---|---|
| `code/literature_search/normalize.py` | modified | `Candidate` dataclass extended with v4 fields: `composite_score`, `score_components`, `human_subject`, `species_evidence`, `tier`, `exclusion_reason`, `auto_role`. |
| `code/literature_search/rank_and_select.py` | modified | added `score_with_components()` (returns the full breakdown alongside the composite); added `assign_auto_role()`. `composite_score()` now delegates to the new function. |
| `code/literature_search/species.py` | new | classify a Candidate as human / non-human / unknown via MeSH terms first, title+abstract+TLDR keywords second. Pure functions. |
| `code/literature_search/tier_classify.py` | new | assigns `picked`/`reserve`/`excluded` plus `exclusion_reason`. Hard-excludes non-human and missing-id rows; otherwise top-N by score. |
| `code/literature_search/serialize_candidates.py` | new | writes the canonical JSON (schema `phase3_candidates_v1`). |
| `code/literature_search/search_queries.py` | modified | `ItemQueryPlan` now carries `short_definition` and `inclusion_test` so the JSON's identity block is self-contained for tasks. |
| `code/literature_search/phase3_search.py` | modified | wired to score with components, classify species, assign tiers, and write JSON. The legacy markdown emitter is no longer called. |
| `code/literature_search/phase3_extract_review.py` | new | extracts the picked tier into a review JSON skeleton, with rebase semantics against any existing review file. |
| `code/literature_search/phase3_render.py` | new | renders candidates + review into a per-item markdown view. |
| `code/literature_search/present_candidates.py` | retained | legacy markdown emitter; not called by the new pipeline but kept until the JSON path is fully validated. Will be removed in a follow-up. |

---

## 9. Running the new pipeline end to end

From `Claude-research/`, with the venv activated:

```powershell
# 1. Search (writes outputs/phase3/candidates/<item>.json)
python code/literature_search/phase3_search.py --mode poc --write

# 2. Extract review skeletons (writes outputs/phase3/review/<item>.json)
python code/literature_search/phase3_extract_review.py

# 3. Render markdown (writes outputs/phase3/rendered/<item>.md)
python code/literature_search/phase3_render.py
```

For a single item:

```powershell
python code/literature_search/phase3_search.py --mode single --ids hed_response_inhibition --write
python code/literature_search/phase3_extract_review.py --item hed_response_inhibition
python code/literature_search/phase3_render.py --item hed_response_inhibition
```

For a tighter picked-tier (smaller review burden):

```powershell
python code/literature_search/phase3_extract_review.py --max-picked 20
python code/literature_search/phase3_render.py
```

To audit the species filter:

```powershell
python code/literature_search/phase3_render.py --include-excluded
```

---

## 10. Migration from the old format

The previous output of `phase3_search.py` was per-item markdown at
`outputs/phase3/candidates/<item>.md`. Those files are now stale and
should be removed before the first run of the new pipeline so the
candidates directory contains only `.json` files:

```powershell
Remove-Item outputs\phase3\candidates\*.md -ErrorAction SilentlyContinue
```

The new pipeline writes `<item>.json` in the same directory; no
collision.

The cache is unchanged. Cached responses from prior runs are reused as
long as the cache key matches; the citations endpoint cache is now
keyed on the corrected `FIELDS_CITATIONS` string (no `tldr`), so a fresh
fetch happens automatically the first time the new code runs against
each seed paper.

---

## 11. What's not implemented yet

- **A click-to-veto UI.** The JSON-edit workflow is fine for the first
  pass. If the format proves stable and the reviewer wants speed, a
  small HTML+JS or Streamlit page that reads the review JSON, exposes
  click-to-veto, and saves back is a few hours of work. The JSON shape
  is the format; the UI is optional sugar.
- **Surfacing uncertain picks for explicit review.** The end goal of
  automated scoring is that the reviewer touches only papers where the
  ranker is uncertain (score within ±0.02 of cutoff, no abstract,
  borderline phrase match). Until we have a few items reviewed manually
  to calibrate, we can't say what "uncertain" looks like statistically.
  Plan to add a "review.uncertainty" flag to the review file once we
  have feedback from the first batch.
- **Cluster near-duplicates.** Same first author + same year +
  ≥80% title token overlap should be visually clustered in the
  rendered view to reduce reviewer effort. Current renderer treats
  each row independently. Worth doing if reviewer feedback says the
  picked tier has many near-twin entries (it did for response
  inhibition, e.g. multiple Pscherer/Sebastian/Verbruggen pairs).
- **Retire `present_candidates.py`.** Kept for now in case any
  downstream code still imports from it. Remove in a follow-up after
  the JSON path has been used at full scale.
- **JSON Schema files for `phase3_candidates_v1` and `phase3_review_v1`.**
  Useful for editor-time validation and for the validator pattern we
  set up for the catalog files. Add when the shapes have stabilized.

---

## 12. Decision provenance

Why this shape over alternatives:

- **One JSON file with all tiers, vs. separate picked/reserve/excluded
  files.** One file. The full record is useful as an audit trail; the
  Reserve and Excluded tiers are small relative to the size of each
  candidate dict (each candidate is dominated by its abstract and TLDR
  text). The cost of one larger file is low; the cost of multiple
  files is operational complexity (which file holds what?
  cross-references between files? rebase across files?).
- **Review file scoped to picked tier, vs. all candidates.** Picked
  only. The reviewer's job is to vet the auto-picks, not to consider
  every paper. A 2,700-row review file is the same usability problem
  as the old markdown.
- **Default-accept (action=null), vs. default-null-must-decide.**
  Default-accept. The whole point of the redesign is that scanning is
  enough most of the time; forcing a decision per row defeats the
  scaling story.
- **Match by DOI then pub_id, vs. just pub_id.** DOI is human-readable,
  globally stable, and citation-friendly. pub_id (an 8-hex-char hash) is
  the stable internal id but unreadable. Using DOI primarily means a
  reviewer reading the JSON can immediately see which paper a decision
  refers to.
- **Reserve tier collapsed in render, vs. shown by default.** Collapsed.
  The picked tier is what the reviewer scans; the reserve list is for
  the rare case where they want to promote a replacement. Showing it
  by default would clutter the page.
