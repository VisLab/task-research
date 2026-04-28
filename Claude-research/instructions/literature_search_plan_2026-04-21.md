# Literature Search — Comprehensive Plan (thinking doc)

**Date:** 2026-04-21  
**Author:** Claude Opus (planning pass)  
**Last updated:** 2026-04-23 (path and schema corrections after reorganisation)

> **Note for future sessions:** This document reflects the original plan with
> corrections applied. Where the original plan and actual implementation differ,
> the implementation wins. The canonical description of current infrastructure
> is `CLAUDE.md` and `instructions/task_literature_search_phase3_instructions.md`.
> All paths in this document are workspace-relative. Do not add absolute paths.

**Purpose:** Replace the current, unsatisfactory reference lists in
`process_details.json` and `task_details.json` with a systematically-searched,
quality-filtered literature corpus; build a versioned repository for publication
metadata; and set up a Zotero group library as the interactive front end.

Scope parameters confirmed with the user (2026-04-21):

- **Augment + prune existing.** Some of the existing references are fine, but
  test manuals (IAPS manual, WMS-III, RAVLT handbook, D-KEFS) and pre-1960
  classics with no clear pedagogical or empirical role should be dropped. The
  rest of the corpus comes from systematic search.
- **Deep corpus:** ~5 key + ~20 recent + a co-mentions section per item.
- **Full-text access via UTSA** (institutional subscriptions). Unpaywall
  supplies OA copies; paywalled papers are fetched via the campus proxy.
- **Zotero in a dedicated local profile** is the reference manager. A
  separate Zotero profile (its own data directory, plugins, SQLite,
  Better BibTeX DB) keeps the HED catalog entirely isolated from the
  user's day-to-day Zotero library. No zotero.org account, no cloud sync,
  no group library — everything stays on the user's machine (updated
  2026-04-21 per user decision). Sharing with the HED team happens
  through Git (`publications.json` is the system of record) plus optional
  BibTeX/JSON export, not through a Zotero group.

---

## 1. Why the current reference list is unsatisfactory

Read from `citation_gaps_2026-04-20.md`, `process_criteria.md §5`, and spot checks of
`task_details.json`:

1. **Too many historical references.** Pavlov (1927), Thorndike (1911),
   Sherrington (1906), von Békésy (1960), Rey (1941, French) and similar classics
   weigh down the arrays. They are resolver-unfriendly (no DOI), add little
   that a modern review does not cover, and skew the literature review toward the
   era rather than the current science.
2. **Test manuals cited as primary literature.** WMS-III (Wechsler 1997),
   IAPS Technical Manual (Lang et al. 1997), RAVLT handbook (Schmidt 1996),
   WAIS manual, D-KEFS manual. These are instrument documentation, not scientific
   claims, and they displace citations that describe how the instrument is used.
3. **Thin recent coverage.** `hed_extinction`, `hed_habit`, `hed_goal_directed_behavior`
   and other processes have a newest reference from the early 2010s. Meta-analyses
   and reviews from 2018–2025 are missing.
4. **Venue bias toward odd journals.** The enriched set includes a disproportionate
   number of specialty or open-access journals; flagship society journals
   (Psychological Review, Journal of Neuroscience, PNAS, NeuroImage, Nature
   Human Behaviour, Trends in Cognitive Sciences, Behavioral and Brain Sciences,
   Psychological Science) are under-represented.
5. **False positives from the automated resolver.** At least one missed by the
   auto-detector (Lang 1997 IAPS manual → Schupp 1997 paper) is still present in
   `task_details.json`, plus ~14 unresolved and 26 task-pass unresolved entries.
6. **No per-item process × task co-mentions.** A paper that describes the
   Flanker Task in an article whose abstract also discusses conflict monitoring
   is gold for the catalog — we have not searched for these explicitly.

Net: the reference arrays were never built by a systematic search. They were
seeded from LLM-authored draft content, lightly enriched by CrossRef lookup,
and patched by hand. We need a proper literature review.

---

## 2. Goal and success criteria

**Goal.** For each of the 172 processes and 103 tasks, produce a
systematically-searched reference list of roughly 5 foundational references,
20 recent/high-impact references, and a supporting set of papers that
co-mention the item and any linked item (process × task overlap). All
references live in a single canonical publications store, are tracked in a
Zotero group library with PDFs where we can acquire them, and are linked to
process_details.json / task_details.json by stable IDs.

**Success criteria.**

1. Every item (process or task) has at least one foundational reference and
   at least one recent review (published within the last 8 years) from a
   journal on the quality allowlist (§5).
2. ≥ 80% of the final reference set is from Elsevier, Springer Nature, Wiley,
   APA, SfN, PNAS, AAAS, Cambridge UP, Oxford UP, or Annual Reviews.
3. The proportion of pre-1990 references in the catalog falls from today's
   (estimated) ~15% to below 5%, with pre-1990 entries only surviving where
   they are genuine landmarks (e.g., Stroop 1935, Miller 1956, Sperling 1960,
   Posner 1980, Eriksen & Eriksen 1974, Rescorla & Wagner 1972).
4. Every (process, linked-task) pair has been co-searched; co-mention papers
   are recorded per pair.
5. For every resolved reference, we can produce either the abstract or, when
   UTSA subscriptions permit, the full-text PDF.
6. The canonical publications store, Zotero group library, and the two
   *_details.json files agree on every included reference.

---

## 3. Repository architecture

The current catalog stores references as nested objects inside
`process_details.json` and `task_details.json`. That worked while references
were few and each reference was only ever cited once, but it makes bookkeeping
hard (a paper cited by three processes appears three times; fixing a DOI
requires three edits). For the new corpus we promote publications to a
first-class table with their own identifiers, and make the `_details.json`
files hold only *references to* publications, not the publication payload.

### 3.1 Actual file layout (updated 2026-04-23)

```
<workspace-root>/
  publications.json               # (future Phase 6) canonical publication metadata
  publication_links.json          # (future Phase 6) many-to-many links
  process_details.json            # 172 processes — unified references array
  task_details.json               # 103 tasks — unified references array

  code/
    .apikeys                      # API key store (git-ignored)
    literature_search/            # Phase 1–9 scripts
      clients/                    # one module per API source
      identity.py                 # pub_id / canonical_string / PDF filename
      cache.py                    # cache_get_or_fetch
      triage_rules.py             # venue/publisher allowlists
      normalize.py                # Candidate dataclass + source normalisers
      search_queries.py           # ItemQueryPlan builder
      rank_and_select.py          # dedup, composite score, selection
      present_candidates.py       # markdown emitter
      phase3_search.py            # host entrypoint (run from workspace root)
      triage_existing_refs.py     # Phase 2 triage script
      migrate_references.py       # one-time schema migration (already applied)
      resolve_landmarks.py        # Phase 2 landmark resolution (no longer needed)
    citation_enrichment/          # Phase A/B enrichment scripts (historical)
    data_management/              # one-off catalog generation/fix scripts

  outputs/
    cache/                        # API response cache (git-ignored)
      <source>/<YYYY-MM-DD>/<hash>.json
    phase2/                       # Phase 2 outputs
    phase3/                       # Phase 3 outputs
      candidates/<item_id>.md

  instructions/                   # plans and task instructions
  .status/                        # session reports and decision notes only
  .scratch/                       # temporary work files (safe to delete)

  (PDFs live in a sibling directory outside the repo, not committed to git)
```

### 3.2 Current reference schema in `process_details.json` / `task_details.json`

> **Updated 2026-04-23.** The original plan described a separate
> `publications.json` store. In practice, Phases 1–3 operate on references
> embedded directly in `process_details.json` and `task_details.json`. The
> `publications.json` store is a Phase 6 deliverable.

Each process and task has a unified `references` array (the old
`fundamental_references`, `recent_references`, and `key_references` arrays
were merged into this on 2026-04-23). Each reference entry looks like:

```json
{
  "citation_string": "Stroop (1935) *Journal of Experimental Psychology* 28:643–662",
  "roles": ["historical"],
  "doi": "10.1037/h0054651",
  "authors": "Stroop, J. R.",
  "title": "Studies of interference in serial verbal reactions.",
  "year": 1935,
  "venue": "Journal of Experimental Psychology",
  "venue_type": "journal",
  "source": "crossref",
  "confidence": "high",
  "url": null,
  "verified_on": "2026-04-20"
}
```

**`roles`** is a list drawn from: `historical | review | experiment | dataset | other | unknown`.

- `historical` — curated landmark paper; **protected** — no script may remove
  it without an explicit `--force-drop-historical` flag.
- All other existing references start as `["unknown"]`; Phase 5 assigns
  the correct role.
- 127 historical refs were seeded from the curated landmark list (61 in
  processes, 66 in tasks).

The `publications.json` store (Phase 6) will be a separate file of fully
enriched, deduplicated publication records referenced by pub_id. Until
Phase 6 runs, references remain embedded in the `_details.json` files.

Points worth being explicit about:

- `pub_id` is a deterministic short identifier of the form
  `pub_<8-hex-char SHA-1>`. The hash is computed **only from metadata we
  can know without an external lookup** — first-author last name, year,
  and title — so discovering a DOI, PMID, or OpenAlex id *after* a record
  exists does not change the pub_id. Full rule in §11.7; the exact input
  is stored in the record as `canonical_string` (below) so the hash
  computation is auditable and re-runnable.
  Human-readable context (author, year, title) does **not** live in the
  pub_id itself — it lives in the PDF filename (§11.7) and in the
  record's structured fields. Cross-reference: strip the `pub_` prefix
  and you get the trailing `<hash8>` token of the PDF's filename.
- `canonical_string` is the exact input fed to SHA-1 to compute the
  pub_id. It is set **once**, at record creation, and never changes.
  Storing it alongside the hash turns "why does this paper have this
  pub_id?" from a guessing game into a one-line check. For dedup across
  sources, DOI match always wins over canonical-string match when both
  are available (DOI = same paper; canonical-string = same first-author
  /year/title-prefix, nearly always the same paper but not guaranteed).
- `doi` stored canonical (lowercased, no `https://doi.org/` prefix).
- `authors` is a structured list (family/given/sequence), not just a display
  string. Name matching for deduplication uses the structured form.
- `openalex_topics` keeps the routing info used to decide co-mentions.
- `quality.composite_score` is the ranking score (§6); stored so downstream
  tools can re-sort without recomputing.
- `zotero_key` is the 8-char Zotero item key; populated after `zotero_sync.py`
  uploads the item.
- `status` in `{"active", "rejected", "superseded"}` so a rejected candidate can
  be kept in the store for provenance but excluded from `publication_links`.

### 3.3 Link record schema

```json
{
  "pub_id": "pub_a3b9f2c1",
  "linked_to": {"type": "process", "id": "hed_proactive_control"},
  "role": "recent_review",
  "added_on": "2026-04-21",
  "curator": "claude-opus-planning",
  "relevance": 0.91,
  "notes": null
}
```

`role` values (closed vocabulary):

- `foundational` — one of the classics that established the construct or
  paradigm (e.g., Miller 1956 for working-memory span).
- `key_review` — a highly-cited recent review or meta-analysis.
- `recent_primary` — a primary empirical paper, typically from the last 8 years.
- `methods` — a paper whose main contribution is the method (e.g., drift-
  diffusion fitting toolbox, HDDM).
- `co_mention` — a paper that names both a process and a linked task in its
  title/abstract. A single publication can appear with role `co_mention` linked
  to a `(process_id, task_id)` pair in addition to other roles.
- `historical` — kept only for landmarks; capped by rule (max one per item,
  only when widely cited within the last 10 years).

`linked_to.type` in `{"process", "task", "co_mention"}`. For `co_mention` the
id is a pair: `{"process_id": "...", "task_id": "..."}`.

### 3.4 Why this architecture rather than nested-in-details?

- **Dedup.** A paper cited by three processes and two tasks appears once, not
  five times. A DOI fix happens in one place.
- **Auditability.** Every link has `curator`, `added_on`, `role`, `relevance`.
- **Reverse lookup is trivial.** "What processes is Duncan & Owen (2000) a
  reference for?" is one `jq` query away.
- **Zotero stays in sync without round-tripping through two nested JSONs.** The
  `zotero_sync.py` script looks at `publications.json` only.
- **Backwards compatibility.** `process_details.json` and `task_details.json`
  keep their reference arrays, but each element becomes a thin record:
  `{"pub_id": "...", "role": "..."}` plus any per-link notes. The human-readable
  `citation_string` can be regenerated on demand from the publication record.

Concretely, after migration, an item in `key_references` looks like:

```json
{"pub_id": "pub_a3b9f2c1", "role": "key_review"}
```

A small `render_references.py` utility expands these to the full APA strings
(or any other display format) for the Markdown-derived files.

---

## 4. Source ladder for literature discovery

Discovery means: "given a process or task, return a ranked list of candidate
publications." Validation means: "given a reference we already have, confirm
DOI / metadata." The two use different sources.

### 4.1 Discovery (primary)

1. **OpenAlex Works API** — the backbone. Already rate-limit-friendly and
   already scripted for the project (`OpenAlex/pull_openalex.py`). Reasons to
   put it first:
   - Topic-filtered queries via the existing crosswalk narrow the corpus by
     ~1000×, which makes the search tractable.
   - Returns `cited_by_count`, `counts_by_year`, `topics`, `abstract_inverted_index`,
     `oa_status`, `oa_url`, `referenced_works`, `related_works`. Everything we
     need for ranking and dedup.
   - Polite pool with `mailto=` = ~10 rps sustained.

2. **PubMed / Europe PMC** — the biomedical layer. Essential for paradigms
   that live in neuroimaging, neurophysiology, and clinical neuroscience, where
   MeSH indexing is the de facto search filter. We use it via:
   - E-utilities (`esearch`, `efetch`, `esummary`), JSON mode.
   - Europe PMC `/search` as a mirror with open-access link metadata.
   MeSH terms give us a second, independent signal that the paper is about the
   construct in question — particularly valuable for common words that
   OpenAlex's TF-IDF stumbles on (e.g., "control", "memory").

3. **Semantic Scholar Graph API** — the citation graph. Used for:
   - "Papers that cite this key reference" (forward citations).
   - "Highly-influential citations" (S2's `isInfluential` flag) for
     ranking.
   - `tldr` field for quick relevance triage.
   - Venue normalization (S2 has cleaner venue strings than CrossRef).
   Rate-limited; we request a free API key to go from 1 rps to 100 rps.

### 4.2 Validation (secondary)

4. **CrossRef** — DOI authority. Used only to:
   - Validate that a DOI we have resolves.
   - Disambiguate the publisher from the DOI prefix.
   - Look up journal-level metadata (ISSN, full title, society publisher).
   - Detect retractions via `crossmark` and `update-to`.

5. **Unpaywall** — open-access routing. Per-DOI lookup of whether a free
   version exists and where.

### 4.3 Manual fallback

6. **Google Scholar** — ToS forbids automated scraping. Used only as a
   human-in-the-loop fallback: when a specific process or task has weak yield
   from automated sources, the plan emits a list of Scholar URLs the user opens
   in a browser and imports into Zotero via the browser connector. Output is
   captured via `zotero_sync.py` pull from the group library; no scraping from
   our code.

### 4.4 What each source contributes to a publication record

| Field | Primary source | Backup | Notes |
|---|---|---|---|
| doi | OpenAlex | CrossRef | canonicalize (lowercase, strip prefix) |
| pmid | PubMed | OpenAlex | |
| openalex_id | OpenAlex | — | |
| title, authors, venue | OpenAlex | CrossRef | OpenAlex author list is already normalized |
| abstract | OpenAlex (inverted index) | PubMed | reconstruct abstract text from inverted index |
| is_review | S2 + MeSH "Review" | OpenAlex `type` | |
| is_meta_analysis | MeSH "Meta-Analysis" | S2 | |
| citation_count | OpenAlex | S2 | |
| oa_status, oa_url | OpenAlex | Unpaywall | |
| mesh_terms | PubMed | — | biomed only |
| influential_citations | S2 | — | used in ranking |
| publisher | CrossRef (prefix map) | — | drives venue_tier |

Rule: when sources disagree on a scalar field, the primary wins but the
secondary value is retained under `sources[*].value_when_differ`. This is the
provenance pattern used by Phase B — do not quietly overwrite.

---

## 5. Publisher and venue quality filter

The user asked specifically for Elsevier, Springer, and flagship society
journals. We implement that as a two-dimensional filter: publisher tier
(from DOI prefix) and venue tier (from a curated journal list). Candidates
that fail both fall into a low-priority bucket but are not deleted — a paper
from, e.g., *eLife* or *Cognition* is worth including even if it doesn't fall
cleanly into the user's three named publishers.

### 5.1 DOI prefix → publisher tier

Tier A (flagship publishers, kept without penalty):

| Prefix | Publisher |
|---|---|
| 10.1016 | Elsevier (Cognition, Cortex, NeuroImage, Neuron, Neuropsychologia, Current Biology, Cognitive Psychology, Brain and Language, Trends in Cognitive Sciences, Trends in Neurosciences) |
| 10.1007 | Springer Nature (Psychonomic Bulletin & Review, Memory & Cognition, Behavior Research Methods, Attention Perception & Psychophysics) |
| 10.1038 | Nature publishing (Nature Neuroscience, Nature Human Behaviour, Scientific Reports, Nature Communications, Nature Reviews Neuroscience) |
| 10.1002 | Wiley (Psychophysiology, Hippocampus, Human Brain Mapping, Topics in Cognitive Science) |
| 10.1037 | American Psychological Association (Psych Review, Psych Science, JEP series, Neuropsychology) |
| 10.1523 | Society for Neuroscience (Journal of Neuroscience) |
| 10.1073 | PNAS |
| 10.1126 | AAAS (Science, Science Advances) |
| 10.1093 | Oxford University Press (Cerebral Cortex, SCAN, Brain, Schizophrenia Bulletin) |
| 10.1017 | Cambridge University Press (Behavioral and Brain Sciences, Development and Psychopathology) |
| 10.1146 | Annual Reviews (ARP, ARN, Annual Review of Vision Science) |

Tier B (mainstream, accepted with modest discount):

| Prefix | Publisher |
|---|---|
| 10.1177 | SAGE (Psychological Science, Perspectives on Psych Science) |
| 10.1080 | Taylor & Francis (Memory, Cognition and Emotion) |
| 10.1371 | PLOS (PLOS ONE — careful, low bar; PLOS Biology fine) |
| 10.3389 | Frontiers (flagged by journal; exclude Frontiers in Psychology OA dumping ground by default; allow Frontiers in Human Neuroscience by journal-level rule) |
| 10.1101 | bioRxiv (preprint — keep only when there is no peer-reviewed version and the paper is highly-cited) |
| 10.3758 | Psychonomic (overlap with 10.1007; some older Psychon refs use 10.3758) |

Tier C (not on the allowlist): default exclusion with a wildcard escape — if
a paper is highly cited (> 95th percentile in field by `citations_per_year`),
it is accepted regardless of publisher.

### 5.2 Venue allowlist

In addition to the publisher tier, a curated allowlist of journal names (stored
in `code/literature_search/triage_rules.py` as `VENUE_TIERS`) tags each
candidate with its venue tier:

- `flagship` — Psych Review, Psych Science, Psych Bulletin, JEP:General, JEP:HPP,
  JEP:LMC, Behavioral and Brain Sciences, Trends in Cognitive Sciences, Trends
  in Neurosciences, Nature, Nature Neuroscience, Nature Human Behaviour, Science,
  PNAS, NeuroImage, Neuron, Current Biology, Journal of Neuroscience, Cerebral
  Cortex, Cognition, Cognitive Psychology, Annual Review of Psychology, Annual
  Review of Neuroscience, eLife, Journal of Vision, Attention Perception &
  Psychophysics.
- `mainstream` — Psychophysiology, Human Brain Mapping, Neuropsychologia,
  Cortex, Journal of Cognitive Neuroscience, Memory & Cognition, Psychonomic
  Bulletin & Review, Behavior Research Methods, Brain & Language, SCAN,
  Cognition & Emotion.
- `specialty` — Journal of Experimental Child Psychology, Consciousness and
  Cognition, Emotion, Neuropsychology, etc.
- `low_or_excluded` — predatory, Beall-listed, or journals with known quality
  concerns. Also miscellaneous "open access" dumps where quality is not
  controlled.

Both the publisher tier and the venue tier feed `quality.venue_tier` for
ranking. Highly-cited papers in specialty journals can still win their tier's
composite-score ranking.

### 5.3 Explicit exclusions

- Non-peer-reviewed: test manuals (Wechsler, Delis-Kaplan, Schmidt's RAVLT
  handbook), technical reports with no DOI and no citing academic review,
  conference abstracts (unless the abstract is the primary citable output for
  a very recent result), preprint-only when a published version exists.
- Retracted papers: detected via CrossRef `update-to.type == "retraction"` or
  PubMed retraction notices. Retracted items go into publications.json with
  `status="rejected"` and a retraction note; no `publication_links` for them.
- Predatory journals: a small curated stop-list.

---

## 6. Ranking and selection

A composite score per (candidate, process-or-task) pair. Recorded on the
candidate record so review is auditable.

```
composite_score =
    0.35 * citation_percentile_in_field            # OpenAlex topic-normalized
  + 0.20 * venue_tier_score                        # 1.0 flagship, 0.7 mainstream, 0.4 specialty, 0.0 excluded
  + 0.15 * publisher_tier_score                    # 1.0 Tier A, 0.6 Tier B, 0.0 Tier C
  + 0.15 * recency_score                           # triangular: peak at 5 y ago, 0 at >20 y
  + 0.10 * query_relevance                         # BM25-like overlap of process/task name with title+abstract
  + 0.05 * is_review_or_meta_bonus                 # reviews and meta-analyses preferred for recent slots
  + co_mention_bonus                               # +0.20 flat if paper mentions both linked process and task
  + historical_landmark_bonus                      # +0.30 for items on the curated landmark list (Stroop 1935 etc.)
```

Selection rules per item:

- `foundational`: top-5 by composite_score with recency_score ignored. Must
  include at least one paper older than 15 years where a true landmark exists.
  Seeded by a hand-curated landmark list (§7.3) that always wins its slot if
  present.
- `recent_primary` and `key_review`: top-20 by composite_score, restricted to
  publication year ≥ (current_year − 8). At least 3 must be reviews or
  meta-analyses; at least 1 must be a methods paper if any exist in the top-50.
- `co_mention`: top-10 by composite_score per (process, linked-task) pair.
- Diversity rule: no single author appears as first or last author on more
  than 3 of the final selections for a given item. This blocks the failure
  mode where one prolific lab dominates.

Selection is a hard decision the user reviews. The plan emits a Markdown
file per item (§8 phase 4) with 50 candidates shown, each with a one-line
summary, the composite_score, and a thumbs-up/down column for the user to
mark. The merged pick list drives the final JSON write.

---

## 7. Process × task co-mention strategy

The user specifically called out co-mention papers as especially valuable. Our
strategy:

### 7.1 Which pairs do we search?

Not all (process, task) pairs — only those that are already linked in
`task_details.json` (`hed_process_ids`). For each task, we iterate its linked
processes. That is roughly 103 tasks × ~5 linked processes each ≈ 500 pairs.
Plus the reverse (process-centric) view, which is the same 500 pairs ordered
differently.

### 7.2 Query construction

For a pair `(process_name, task_name)`:

1. **OpenAlex Works**: `search="<process_name>" AND search="<task_name>"` plus
   filter by the Topics in the process's crosswalk entry. Sort by
   `cited_by_count:desc`, cap 50.
2. **PubMed**: `"<process_name>"[tiab] AND "<task_name>"[tiab]` plus
   `"last 10 years"[dp]`.
3. **Semantic Scholar**: free-text search of the concatenated names; take
   top-20 by influential-citation count.

For task_name we expand using `aliases` from `task_details.json` (e.g.,
"Eriksen Flanker Task" + "Flanker Task"). For process_name we expand using the
`aliases` from `process_details.json` (e.g., "Perspective taking" + "Theory of
mind" + "Mentalizing").

### 7.3 Historical references (formerly "landmark override list")

> **Updated 2026-04-23.** The separate `landmark_refs.json` file has been
> superseded. Landmark/historical status is now encoded directly in the
> `references` array of each process and task as `"roles": ["historical"]`.

References with `"historical"` in their roles list are the curated landmark
papers that must be included regardless of score. They receive a +0.30 bonus
in the composite score and are pinned to the top of the foundational slot.
No script may remove a historical reference without an explicit override flag.

As of 2026-04-23: 127 historical references are set (61 in processes, 66 in
tasks) covering the landmark papers originally curated in
`instructions/landmark_refs_2026-04-22.md`. The human-readable list of
landmark citations remains in that file for reference.

`phase3_search.py` reads historical references directly from
`process_details.json` and `task_details.json` — no separate file required.

---

## 8. Execution phases (for sonnet handoff)

Each phase has clear deliverables, cache semantics, and a human-review gate
where appropriate. The plan assumes the sandbox cannot reach external APIs
(this has been true in every prior session) and therefore leans on host-side
scripts run from the workspace root. The template for the host-script pattern
is `code/citation_enrichment/enrich_citations_host_script.py`.

### Phase 1 — Infrastructure and dry runs (COMPLETE)

> All Phase 1 infrastructure was built on 2026-04-22. Scripts live in
> `code/literature_search/` and `code/literature_search/clients/`.
> Cache lives in `outputs/cache/<source>/<date>/`.

1. Create `code/literature_search/` and the five client modules:
   `clients/openalex.py`, `clients/europepmc.py`, `clients/semanticscholar.py`,
   `clients/crossref.py`, `clients/unpaywall.py`. Each uses `requests`, caches
   under `outputs/cache/<source>/<date>/<hash>.json`. Unit tests at the
   module level.
2. Zotero local-library setup in a dedicated profile (user action):
   - Install Zotero 7 desktop (no account required) if not already
     installed.
   - Create a new Zotero profile named `hed-research` with its own data
     directory (e.g., `H:\Research\TaskResearch\Zotero-HED\`) — see
     Appendix B for the step-by-step.
   - Launch Zotero with the new profile. Install the Better BibTeX
     plugin inside this profile (plugins are per-profile).
   - Enable the local HTTP API: Preferences → Advanced → Config Editor,
     set `extensions.zotero.httpServer.enabled = true` and
     `extensions.zotero.httpServer.localAPI.enabled = true`.
   - (Optional) Configure Better BibTeX auto-export to a known path
     inside the profile data directory
     (e.g., `H:\Research\TaskResearch\Zotero-HED\zotero_export.json`)
     as the offline fallback channel.
   - On first connect, `zotero_sync.py` writes a "HED Catalog (do not
     delete)" marker item so subsequent runs can verify they are
     targeting the right library.
   Write `zotero_sync.py` using `pyzotero` in local mode (`local=True`,
   empty api_key). Verify round-trip by creating one test item, reading it
   back, updating it, deleting it.
3. Write `publications.json` schema + validator (`publications_schema.json`
   JSON-schema file + `validate_publications.py`). Populate with 5 seed
   publications to smoke-test.
4. Write `publication_links.json` schema + validator.
5. Host-side runner scaffolding: `code/literature_search/phase3_search.py`
   following the `enrich_citations_host_script.py` pattern — single-file,
   stdlib + requests, argparse-driven, dry-run by default.

Deliverable: infrastructure works end-to-end for one seed process
(`hed_response_inhibition` is a good candidate — well-studied, clean
terminology, many tasks).

### Phase 2 — Triage existing references (COMPLETE)

> Completed 2026-04-22. Session report: `.status/session_2026-04-22_literature_search_phase2.md`.
> Triage output: `.status/reference_triage_2026-04-22.md`.

Outcome:
- 974 references kept, 48 mechanically dropped, 115 sent to human review.
- Human review resolved and dropped the 115 review items.
- Reference schema then migrated (2026-04-23) to a unified `references` array
  with `roles` field — see `CLAUDE.md` §"Reference schema" and
  `.status/session_2026-04-23_reorganisation_and_schema.md`.
- Historical landmark refs (127) seeded with `roles: ["historical"]` (protected).
- All remaining refs carry `roles: ["unknown"]` pending Phase 5 assignment.

Deliverable achieved: reduced reference set with chaff removed; historical refs
locked; all others marked unknown for Phase 5 curation.

### Phase 3 — Systematic search per process and per task (INFRASTRUCTURE COMPLETE)

> Infrastructure built 2026-04-23. POC run is the next step.
> See `instructions/task_literature_search_phase3_instructions.md` for
> the full current-state guide.

For each of the 172 processes and 103 tasks:

1. Build queries against OpenAlex, Europe PMC, and Semantic Scholar (three
   passes per item: foundational, recent, reviews). Cache raw results under
   `outputs/cache/`.
2. Deduplicate candidates across sources by DOI (primary) and pub_id
   (author+year+title hash, fallback).
3. Score each candidate with the composite formula (§6).
4. Emit per-item candidate files to `outputs/phase3/candidates/<item_id>.md`.
5. Emit top-level index to `.status/candidates_index_<date>.md`.

Run command (from workspace root):
```
python code/literature_search/phase3_search.py --mode poc --write   # POC first
python code/literature_search/phase3_search.py --mode full --write  # then full
```

Budget: ~5,000 API calls. ~10 min with S2 key, ~60–90 min without.

### Phase 4 — Co-mention search (≈ 1 session)

Iterate all (process, linked-task) pairs from `task_details.json`. Run the
queries in §7.2. Cache, dedupe, rank. Emit
`.status/candidates_comention_<process_id>_<task_id>_<date>.md`.

### Phase 5 — Human review and selection (asynchronous)

The user reviews the candidate Markdown files per item. For each, marks
KEEP / DROP / ADJUST-role on each candidate. This is the critical curation
step — we do not write to `publications.json` or Zotero until this review
happens.

To keep the review tractable, the Markdown format is tight:

```markdown
### hed_response_inhibition — candidate #1
- **DOI:** 10.1016/j.tics.2011.02.001
- **Title:** "The role of the lateral frontal cortex in...
- **Authors:** Aron, A. R., et al.
- **Venue:** Trends in Cognitive Sciences, 2011 (cited 3,412)
- **Score:** 0.93 (Tier A, flagship, recent, review)
- **Suggested role:** key_review
- [ ] KEEP  [ ] DROP  [ ] role: ___________
- Abstract: *...first 3 sentences...*
```

The user ticks boxes directly in the file.

### Phase 6 — Populate Zotero and publications.json (≈ 1 session)

Once review is complete for a batch of items:

1. For every approved candidate, upsert into `publications.json`. Deduplicate
   by DOI / pub_id.
2. Create/update corresponding Zotero items via `pyzotero`. File into the
   matching collection (by process category or task category), tag with role
   and tier.
3. Write `publication_links.json` rows linking each pub_id to the
   `(process|task|co_mention)` target with its role.
4. Update `zotero_mapping.json` with the Zotero keys returned from the upsert.

### Phase 7 — Full-text acquisition via UTSA + Unpaywall (rolling)

For each publication in `publications.json` without `local_pdf_path`:

1. Consult Unpaywall's `oa_url` or OpenAlex's `oa_url`. If present and
   reachable, download to the path returned by
   `build_pdf_filename(record)`, i.e.
   `H:\Research\TaskResearch\HED-PDFs\<year>\<LastName>_<Year>_<CamelCaseTitle>_<hash8>.pdf`
   (§11.7). Create the year folder if it does not exist.
2. If not, attempt the UTSA library proxy (`rowdylink.utsa.edu` style URL
   — the exact form goes in `utsa_pdf_fetcher.py`). Where the publisher
   requires an interactive login, the script logs the paper to a "manual
   fetch" queue and the user completes the download via browser + Zotero
   connector; the next sync picks up the PDF and moves/renames it into
   the canonical path.
3. Add the PDF to the matching Zotero item as a **linked-file** attachment
   (not a stored copy). Because the profile has its Linked Attachment
   Base Directory set to `H:\Research\TaskResearch\HED-PDFs\` (§B.3.3),
   Zotero stores the path relatively and the attachment stays valid on
   any machine that mounts the same sibling tree.
4. Log coverage: what fraction of papers have full text; what publishers are
   consistently blocked.

The OCR / full-text indexing pass (if ever needed) is out of scope.

### Phase 8 — Merge into authoritative JSON (≈ 1 session)

1. Back up `process_details.json` → `original/process_details_pre_litsearch_<date>.json`.
2. Same for `task_details.json`.
3. Rewrite the reference arrays to thin records: `{"pub_id": "...", "role": "..."}`.
4. Update `file_inventory.json` and the regeneration script
   (`outputs/regenerate_derived_files.py`) to (a) know about
   `publications.json` as an upstream input and (b) render references by
   expanding pub_ids against that file.
5. Re-run regeneration; verify all derived files.
6. Write a session report.

### Phase 9 — Quality audit (≈ 1 session)

1. Sample 20 items across processes and tasks; spot-check the final reference
   list for a domain expert sanity check.
2. Compute distributions:
   - Publisher tier A vs. B vs. C share.
   - Year histogram.
   - Venue histogram.
   - Citation-count percentile within field.
   - Co-mention coverage (what fraction of linked pairs have ≥ 1 co-mention).
3. Flag any item where the curated list fell below target (e.g., < 5 key or
   < 10 recent) so we can go back for more.
4. Close out `process_criteria.md §7.12` and any successor items referring to
   the old reference quality.

---

## 9. Risks and mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Sandbox has no network access to APIs | High (known) | All executable work runs via host-side Python scripts (same pattern as `enrich_citations_host_script.py`). Sandbox runs drafting, review, and merge steps. |
| API rate limits (PubMed unauthenticated, S2 unauthenticated) | Medium | Register for free API keys. Implement per-host throttling + exponential backoff. Cache aggressively (every response keyed by query hash, date-stamped). |
| Google Scholar ToS violation from automation | High if we try | We do not scrape it. Manual-only via browser + Zotero connector. |
| Virtiofs stale snapshot (bash sees stale data) | High (known) | Continue the Phase B/C rule: Read/Write/Edit for workspace paths; bash only for `outputs/` and `literature_cache/`. |
| Paywalled PDFs we cannot acquire even via UTSA | Medium | Record as "abstract-only" in publications.json. Keep the Zotero item; flag for later human-fetch. Do not block the pipeline. |
| Predatory journals sneaking in | Low-medium | Venue allowlist + DOAJ lookup + MDPI/Frontiers-per-journal rules catch most; human review is the final filter. |
| OpenAlex topic crosswalk quality is uneven | Known | Already in coverage_assessment.md. For concepts with "weak" top-1 score we fall back to category-level routing. |
| False positives from author-name matches | Known | Already seen in Phase B (Rescorla, Indefrey, Skinner) and Phase C (Lang). Use stricter matching (2-surname overlap when > 2 authors; first + last surname match; DOI-first dedup before any name match). |
| Reference arrays grow unwieldy (25+ per item × 275 items = thousands) | Medium | Publication table dedups across items; the growth lives in `publications.json` (manageable) while each `_details.json` item only stores pub_ids. |
| User preference for "clean, not over-engineered" vs. this plan's scope | Real | Keep scripts < 200 LOC each; flat functions; no class hierarchies beyond a couple of dataclasses. The architecture is segmented by responsibility (one client per source) rather than abstracted. |

---

## 10. What this plan explicitly does NOT do

- It does not scrape Google Scholar.
- It does not auto-update the final reference lists. Every pick passes a
  human-review gate (Phase 5).
- It does not attempt to compute a "citation quality score" beyond the
  composite ranking described in §6. That is a separate, bigger question.
- It does not try to mine paradigm names from abstracts. That is
  `OpenAlex/works/.status/works_step_proposal.md`, a related but separate
  workstream (orphan task finding).
- It does not introduce any new naming conventions for processes or tasks;
  those stay stable.
- It does not modify `tasks_criteria.md` or `process_criteria.md` except to
  (a) add a short pointer to the new reference schema and (b) close the
  known-issue §7.12 in `process_criteria.md`.

---

## 11. Zotero: design details (local-only, dedicated profile)

> **Path note (2026-04-23):** Sections §11 and the PDF appendix contain
> absolute paths for the Zotero data directory and the HED-PDFs folder.
> These paths are intentionally local to the user's machine and are NOT
> committed to the repository. They should be configured in `code/.apikeys`
> or as environment variables, not hardcoded in any script. When referencing
> these directories in scripts, use a `--zotero-dir` or `--pdfs-dir` argument
> with no default, or read the path from `code/.apikeys`.

*(Revised 2026-04-21 — group library replaced with a local personal
library; further revised same day — personal library lives in a dedicated
Zotero profile, fully isolated from the user's normal Zotero profile.)*

### 11.0 Why a dedicated profile (and not just a new library)

Zotero allows exactly one personal library per profile (the built-in
"My Library"). Group libraries can be added alongside, but we've ruled
those out because they require a zotero.org account. So the only way to
get a fully separate personal library for the HED catalog is to run a
**second Zotero profile** with its own data directory.

This is the Firefox-style profile mechanism Zotero inherited from its
Mozilla platform: each profile has an independent `zotero.sqlite`,
`storage/` directory, plugin set, preferences, and Better BibTeX
database. Switching profiles switches *everything*; items, collections,
tags, and PDFs cannot leak between profiles. That isolation is exactly
what the user asked for.

Practical consequences of the profile approach:

- The HED Zotero profile has its own plugin installs (Better BibTeX must
  be installed once per profile).
- The local HTTP API (§11.2) is served by whichever profile is currently
  running. As long as the user launches Zotero with the HED profile when
  doing HED work, `zotero_sync.py` naturally targets the right library
  and cannot pollute the personal one.
- By default Zotero allows only one running instance. To run both
  profiles at once, use `--no-remote` when launching the second
  instance. For most workflows it's simpler to close one and open the
  other as needed.

### 11.1 Library structure

- **Profile name:** `hed-research` (suggested; user can rename).
- **Profile data directory:** suggested
  `H:\Research\TaskResearch\Zotero-HED\` — outside the Git repo so that
  PDFs, the SQLite, and the `storage/` directory stay local and are not
  inadvertently committed. The path is recorded in
  `outputs/literature_search/.zotero_env` (git-ignored) as
  `ZOTERO_PROFILE_DIR=...`.
- **Library:** the profile's single personal library ("My Library"). No
  zotero.org sync; no group library; no cloud copy.
- **Top-level collections** (mirrors what we would have had in a group):
  - `Processes/<CategoryName>` — 19 collections, matching
    `process_details.json`'s category list.
  - `Tasks/<CategoryName>` — task-side collections.
  - `Co-mention/<process_id>__<task_id>` — lazily created per pair when the
    first co-mention paper is curated in.
  - `_Landmarks` — the hand-curated classics list.
- **Tags:** `role:foundational`, `role:key_review`, `role:recent_primary`,
  `role:methods`, `role:co_mention`, `role:historical`, `venue:flagship`,
  `venue:mainstream`, `review`, `meta-analysis`, `has-pdf`, `needs-review`.
- **Relations:** Zotero item relations used optionally to link papers that
  cite each other (from S2 influential-citation data). Phase 7+ enhancement.

### 11.2 Keys and sync

`publications.json` is the system of record in Git. Zotero is the interactive
front end. Sync flows both directions.

- **Identifiers.** Each publication carries our `pub_id` slug plus, once the
  item is created in Zotero, its 8-char Zotero item key. Zotero dedupes on
  DOI when adding items, so the DOI is the de-facto join key.
- **Preferred sync channel — local HTTP API.** Zotero 7 exposes
  `http://localhost:23119/api/` when the desktop app is running and
  `extensions.zotero.httpServer.enabled` is true (default) with
  `extensions.zotero.httpServer.localAPI.enabled` set to true. `pyzotero`
  supports this mode:

  ```python
  from pyzotero import zotero
  zot = zotero.Zotero(library_id=0, library_type='user', api_key='', local=True)
  ```

  `library_id=0` plus `local=True` targets the running desktop's personal
  library — which, under the dedicated-profile setup in §11.0, is the HED
  catalog library and only the HED catalog library. `zotero_sync.py`
  guards against mis-targeting by checking a profile-marker item on
  connect: the first time the script runs against a library it writes a
  hidden "HED Catalog (do not delete)" item with a known UUID; subsequent
  runs refuse to operate on a library that does not contain that marker.
  No API key required; no network traffic leaves the machine.

- **Fallback sync channel — Better BibTeX auto-export.** Better BibTeX can
  auto-export the whole library (or named collections) to a JSON file on
  every change. When the desktop app is not running, or when we want a
  reproducible offline artifact, `zotero_sync.py` reads that exported JSON
  and reconciles against `publications.json`. Better BibTeX also supplies
  stable citation keys we can store alongside `pub_id` for external tools
  (LaTeX, Pandoc, etc.).

- **Conflict rule.** `publications.json` in Git is authoritative for
  metadata. Zotero-side edits to a shared field (title, venue, authors) are
  surfaced in a `.status/zotero_drift_<date>.md` report and not auto-merged;
  the user resolves drift by hand or by re-export.

- **Direction.** Authoring happens in the sandbox against
  `publications.json`. On sync, `zotero_sync.py`:
  1. Push new or updated publications into Zotero (via local API).
  2. Pull any Zotero-only additions (items the user saved via the browser
     connector that are not yet in `publications.json`) and stage them as
     proposed additions under `.status/zotero_new_items_<date>.md` for user
     review.

### 11.3 PDF storage (location and linking)

PDFs live **outside** both the Git repo and the Zotero profile, in a
dedicated sibling directory:

```
H:\Research\TaskResearch\HED-PDFs\
  <year>\<LastName>_<Year>_<CamelCaseTitle>_<hash8>.pdf
```

Examples:

```
H:\Research\TaskResearch\HED-PDFs\2012\Badre_2012_CognitiveControlHierarchyAndTheRostroCaudalOrganizationOfTheFrontalLobes_a3b9f2c1.pdf
H:\Research\TaskResearch\HED-PDFs\1935\Stroop_1935_StudiesOfInterferenceInSerialVerbalReactions_7f10b4d2.pdf
H:\Research\TaskResearch\HED-PDFs\1997\Lang_1997_InternationalAffectivePictureSystemIAPSTechnicalManual_c7a2e55f.pdf
```

The filename is deliberately human-readable so a glance at the directory
tells you what each PDF is — author, year, title, with a short hash at the
end to disambiguate and to tie each file to its `pub_id` in the catalog.
Full filename rules (ASCII folding, title casing, truncation, edge cases)
are in §11.7.

Rationale for this layout:

- **Outside the Git repo.** PDFs are large, often redistribution-restricted
  under publisher licenses, and change rarely; they don't belong in version
  control. A sibling directory keeps them close without polluting Git.
- **Outside the Zotero profile.** Zotero 7's default "stored" attachments
  live under `storage/` in the profile directory. That path is opaque
  (`storage/ABCD1234/original-pdf-name.pdf`), couples file organization to
  Zotero's internal item keys, and makes the PDFs hard to use without
  Zotero. A separately-rooted directory keeps the PDFs usable by any tool
  (a plain PDF reader, a full-text indexer, a future non-Zotero workflow).
- **Year-bucketed, name-first filenames.** One level of year bucketing
  keeps any single directory below ~500 files even for a prolific year.
  The filename starts with author and year so the year folder plus an
  alphabetical directory listing is effectively an index by author. The
  trailing `<hash8>` is the last 8 chars of the publication's `pub_id`,
  so cross-referencing the PDF to the catalog is one substring lookup in
  `publications.json`. No publisher subfolders: DOIs drift between
  imprints after mergers, and publisher is not a stable organizing key.

Zotero items reference these PDFs as **linked file** attachments, not copies.
Consequences:

- No duplication (one PDF on disk, one link in Zotero).
- No Zotero storage quota concerns (there is no cloud storage under this
  plan anyway).
- Zotero's own PDF reader, annotation, and full-text search still work on
  linked files.
- Moving the PDF root breaks Zotero's links. Mitigations: (a) configure
  Zotero's "Linked Attachment Base Directory" to
  `H:\Research\TaskResearch\HED-PDFs\` (Appendix B.3) so Zotero stores
  *relative* paths and the tree is portable; (b) `zotero_sync.py` offers a
  `--rewrite-pdf-paths --old <dir> --new <dir>` option for the rare case
  when relative paths are not enough.

For UTSA-acquired PDFs, the acquisition flow (Phase 7) writes straight to
`H:\Research\TaskResearch\HED-PDFs\<year>\<pub_id>.pdf` and then adds a
linked-file attachment to the matching Zotero item on the next sync. The
full naming rules (including no-DOI and preprint edge cases) are in §11.7.

### 11.4 Sharing the catalog with the HED team (no group library)

Since the library is local, sharing happens through Git + exports:

- **Primary share artifact:** `publications.json` in the repo. Any team
  member with repo access has the full reference metadata.
- **Secondary share artifact:** a periodic BibTeX dump, generated by
  `zotero_sync.py --export-bibtex`. Committed to the repo (or released as a
  GitHub release asset). Team members can import the BibTeX into their own
  Zotero, Mendeley, Papers, or LaTeX bibliography.
- **PDFs are not shared by default.** They stay on the curator's machine and
  are acquired individually by team members via UTSA access.

If the catalog later needs true multi-curator editing, migrating from a
personal local library to a group library is a one-time, low-risk move —
Zotero supports drag-and-drop between libraries and our pub_id/DOI keys make
re-syncing deterministic.

### 11.5 Why still use Zotero at all

- **GUI for candidate review.** The Phase 5 candidate lists are long;
  browsing them in Zotero (with abstract preview, tags, saved searches) is
  markedly faster than scrolling a Markdown file.
- **PDF annotation.** Zotero 7 ships a native PDF reader with highlights,
  notes, and tags. Notes stick to the item in `publications.json` via the
  sync.
- **Browser connector.** The one-click save flow from a publisher page,
  PubMed, or Google Scholar. This is the piece that closes the Google
  Scholar loophole without scraping.
- **DOI / PMID lookup.** Paste a DOI or PMID into Zotero and it pulls
  structured metadata. Useful when a user-supplied reference doesn't go
  through the automated resolver.
- **No vendor lock-in.** Everything exportable as BibTeX, RIS, or CSL-JSON
  at any time.

### 11.6 Downsides to be honest about

- **Zotero must be running with the HED profile** for the local HTTP API
  to target the HED catalog. If the user has their personal profile
  running instead, the marker-item guard (§11.2) prevents the sync
  script from doing anything destructive — it errors out cleanly. When
  Zotero isn't running at all, `zotero_sync.py` falls back to the Better
  BibTeX export-file path or degrades to a read-only dry run.
- **Only one profile runs at a time by default.** Switching between the
  user's personal Zotero and the HED profile means closing one and
  opening the other, or launching the second with `--no-remote`.
- **SQLite-direct reads are off-limits while Zotero is running** (the DB is
  locked). We do not read the SQLite directly; we go through the HTTP API
  or the export file.
- **Single-user editing.** Two people cannot edit the local library
  simultaneously. The Git-based workflow on `publications.json` covers
  multi-contributor work; the Zotero library is the sole curator's workspace.
- **Plugins are per-profile.** Better BibTeX, the Zotero Connector's
  browser integration, and any other plugins must be installed once in
  the HED profile. This is cheap, but easy to forget on first setup.

### 11.7 PDF filename scheme (detailed rules)

Goal: when the curator opens `H:\Research\TaskResearch\HED-PDFs\` in
Explorer, each PDF's filename should tell them author, year, topic, and
carry a stable back-reference to the catalog — without any lookup.

**Pattern:**

```
<LastName>_<Year>_<CamelCaseTitle>_<hash8>.pdf
```

**Field construction (each step is deterministic):**

1. **`<LastName>`** — first author's family name, drawn from the
   structured `authors[0].family` field of the publication record.
   - Apply NFKD Unicode normalization, then strip combining marks
     (ASCII fold): `Schönberg` → `Schonberg`, `Müller` → `Muller`.
   - Split on whitespace; TitleCase each token; remove every character
     that is not `[A-Za-z0-9]`; concatenate. This preserves particle
     structure while producing a Windows-safe token:
     `O'Keefe` → `OKeefe`, `van der Berg` → `VanDerBerg`,
     `de Fockert` → `DeFockert`, `Wagner` → `Wagner`.
   - If `authors` is empty (extremely rare, should prompt a manual
     review), use `Anonymous`.

2. **`<Year>`** — 4-digit publication year from the record's `year`
   field. If unknown, emit `nodate`.

3. **`<CamelCaseTitle>`** — from the record's `title`:
   - ASCII-fold as above (diacritics → ASCII).
   - Split on any non-alphanumeric character (colons, commas, slashes,
     spaces, hyphens, parentheses, periods — all become token
     boundaries).
   - For each token: if the token is already all-uppercase *and* length
     ≥ 2, keep as-is (preserves acronyms: `fMRI`, `EEG`, `ADHD`, `IAPS`,
     `TMS`); otherwise TitleCase (first letter upper, rest lower).
   - Concatenate tokens.
   - **Truncate** at the largest prefix that stays ≤ 100 characters and
     ends on a token boundary (so the filename does not end mid-word).
     100 is chosen so the total filename (with path prefix) stays well
     under Windows' default 260-character path limit and leaves the
     directory browsable.

4. **`<hash8>`** — 8 hex characters of SHA-1 over a deterministic
   **canonical string** built from metadata alone. The canonical string
   is independent of whether we know a DOI, PMID, or OpenAlex id for
   this paper; discovering any of those identifiers *later* populates
   their fields but does not alter the hash. The algorithm:

   1. `last`  = `authors[0].family`, ASCII-folded, lowercased, with all
      non-`[a-z]` characters removed.
      Examples: `Badre` → `badre`, `O'Keefe` → `okeefe`,
      `van der Berg` → `vanderberg`, `Schönberg` → `schonberg`.
      If no first author is available, use `anonymous`.
   2. `yr`    = the 4-digit year as a zero-padded string, e.g. `2012`.
      If the year is unknown, use `0000`.
   3. `title` = the title ASCII-folded, lowercased, with all
      non-`[a-z0-9]` characters removed. If the result is empty
      (e.g., non-Latin-script title that folds to nothing), use
      `untitled`.
   4. Concatenate with no separators: `s = last + yr + title`.
   5. Truncate: `s = s[:100]` (at most 100 characters total).
   6. Hash: `hash8 = sha1(s.encode("utf-8")).hexdigest()[:8]`.

   The final canonical string `s` is stored in the record as
   `canonical_string` (§3.2) so the hash is reproducible from the
   record alone.

   Example (Badre 2012):
   ```
   last  = "badre"
   yr    = "2012"
   title = "cognitivecontrolhierarchyandtherostrocaudalorganizationofthefrontallobes"
   s     = "badre2012cognitivecontrolhierarchyandtherostrocaudalorganizationofthefrontallobes"
          (length 82 — no truncation needed)
   hash8 = sha1(s).hexdigest()[:8]    # illustrative: "a3b9f2c1"
   ```

   **`hash8` is the tail of `pub_id`.** The PDF filename's trailing
   `_<hash8>.pdf` is always the same 8 hex characters as
   `pub_id[-8:]`. That coupling is the only link the curator needs to
   jump between a PDF in Explorer and its record in `publications.json`.

   **Dedup rule (stated once, to avoid confusion with hashing).** When
   the ingester sees a new record, it first checks DOI match against
   existing records; DOI match → reuse existing pub_id. Only if DOI
   is not available on either side does the canonical-string match
   come into play. The hash is an *identity* mechanism under metadata
   drift, not the primary *dedup* mechanism across sources.

**Putting it together (example):**

- First author: David Badre
- Year: 2012
- Title: *"Cognitive control, hierarchy, and the rostro-caudal
  organization of the frontal lobes"*
- Canonical string (stored in the record):
  `badre2012cognitivecontrolhierarchyandtherostrocaudalorganizationofthefrontallobes`
- SHA-1 prefix of that string (illustrative): `a3b9f2c1`

→ `pub_id` = `pub_a3b9f2c1`
→ File at
  `H:\Research\TaskResearch\HED-PDFs\2012\Badre_2012_CognitiveControlHierarchyAndTheRostroCaudalOrganizationOfTheFrontalLobes_a3b9f2c1.pdf`

Note that the DOI (`10.1016/j.tics.2012.02.005`) was not used to compute
either the hash or the filename. If we had ingested this paper from
Europe PMC with just the PMID, the pub_id would still be `pub_a3b9f2c1`;
populating the DOI later is a no-op for the id.

**Edge cases (all deterministic):**

| Case | Filename / hash behavior |
|:---|:---|
| No first author | Canonical string uses `anonymous` as the last-name token; filename's `<LastName>` also becomes `Anonymous`. Flagged for manual review. |
| No year | Canonical string uses `0000`; filename's `<Year>` token becomes `nodate` and the file is placed in `HED-PDFs\undated\`. (Two different spellings, same underlying "unknown year" — the hash uses `0000` for determinism; the filename uses `nodate` for legibility.) |
| Title is empty / non-Latin-script that folds to nothing | Canonical string uses `untitled`; filename uses `UntitledNonLatin`. Flagged. |
| Title > 100 chars after folding | Hash input is truncated to exactly 100 chars (may cut mid-word; the hash is opaque so that's fine). Filename's `<CamelCaseTitle>` is truncated at a token boundary ≤ 100 chars (for readability). The two truncations are independent. |
| Preprint followed by published version-of-record | Two separate records, two separate canonical strings (titles usually differ slightly between preprint and VoR; even when identical, the year often differs) → two pub_ids → two filenames. `publication_links.json` records the `preprint_of` / `vor_of` relationship. |
| Two sources returning slightly different titles for the same paper | Dedup by DOI first (§ dedup rule above). Only if neither source has a DOI do we fall back to canonical-string match; in that case the ingester commits one title as canonical, stores it as `canonical_string`, and the hash is derived from that choice — auditable via the stored field. |
| Title with leading article ("The", "A", "An") | Kept verbatim in the canonical string (`theiowagamblingtask...`) and TitleCased in the filename (`TheIowaGamblingTask...`). We do not attempt librarian-style leading-article rewriting. |
| Curator corrects the title after ingestion | The `title` and `authors` fields are updated; the `canonical_string` and `pub_id` are **not**. If a correction is large enough that the old pub_id is misleading, the record is re-minted (new pub_id, new filename) and the old pub_id is kept in a `superseded_by` field for provenance. This is a deliberate manual step, not an automatic one. |

**Why this scheme (and why the hash input is metadata-only):**

- **Human readability first.** The earlier pre-review scheme used
  `<pub_id>.pdf` with a semantic pub_id (`pub_2012_badre_dopa_tics`).
  That was terse but cryptic — `dopa_tics` reads as "dopamine TICS" only
  after you know the convention. A full author/year/title filename
  removes the convention.
- **One source of semantic truth.** Semantic metadata lives in the
  filename and in the publication record's structured fields. The
  pub_id carries only the hash, so there is no slug-vs-filename drift.
- **Identity is stable against identifier discovery.** Because the hash
  is computed from `last + year + title`, not from DOI/PMID/OpenAlex,
  ingesting a paper before we know its DOI — and then discovering the
  DOI later — does not change its pub_id. All existing filenames, Zotero
  marker entries, and `publication_links.json` rows remain valid.
- **Auditable.** `canonical_string` is stored in the record. Any time
  the question "why does this record have this pub_id?" comes up, the
  answer is a one-line check: recompute `sha1(canonical_string)[:8]`.
- **Collision-safe at our scale.** 8 hex chars = 32 bits. For a catalog
  of ~5000 papers the birthday-paradox collision probability is < 10⁻⁵.
  The ingester checks for collisions at write time and bumps to 10 hex
  chars for the rare pair that collides (both the bumped record and the
  prior record).

**Implementation note.** Two pure functions live in
`code/literature_search/identity.py`:

- `build_canonical_string(record) -> str` — returns the ≤100-char hash
  input described above.
- `build_pub_id(record) -> str` — returns `"pub_" + sha1(canonical_string)[:8]`.
- `build_pdf_filename(record) -> str` — returns the full
  `<LastName>_<Year>_<CamelCaseTitle>_<hash8>.pdf` filename (without
  the directory prefix).

Each is a pure function and re-runnable. They are unit-tested against
a fixture set that covers: accented names, compound particles
(`van der Berg`, `de Fockert`), all-caps acronyms in titles, long
titles exceeding the 100-char budget, no-DOI papers, no-year papers,
leading-article titles, and — critically — the **DOI-discovered-later**
round-trip: a record minted without a DOI must produce the same pub_id
and the same filename after the DOI field is populated. Every other
script that touches pub_ids, canonical strings, or PDF paths calls
these three functions; no ad-hoc formatting anywhere else.

---

## 12. Open decisions to confirm with the user

1. ~~Group library name and initial sharing list.~~ **Resolved 2026-04-21:**
   local personal library only; no group library.
2. Whether to expand the landmark list (§7.3) beyond the ~40 starter entries
   before running — or to seed it with ~40 and grow it as we go.
3. The venue tier table (§5.2) needs a pass from the HED team for any
   discipline-specific flagships we may have missed (e.g., Schizophrenia
   Bulletin for the clinical-adjacent items; Cognition for mainstream cog
   psych).
4. ~~PDF storage location.~~ **Resolved 2026-04-21:** PDFs live in a
   sibling directory `H:\Research\TaskResearch\HED-PDFs\<year>\`, outside
   both the Git repo and the Zotero profile; Zotero uses linked-file
   attachments with a base directory set to that root. No Zotero cloud
   upload and no storage quota.
4b. ~~PDF filename scheme.~~ **Resolved 2026-04-21 (§11.7):** human-readable
    `<LastName>_<Year>_<CamelCaseTitle>_<hash8>.pdf`. The 8-hex-char hash
    is also the tail of `pub_id` so the PDF always maps back to its catalog
    record by a substring lookup.
4c. ~~pub_id redesign.~~ **Resolved 2026-04-21:** `pub_id = pub_<hash8>`
    where `<hash8>` is the first 8 hex chars of SHA-1 over a
    metadata-only canonical string (lastname+year+title, ≤100 chars,
    lowercase, alphanumeric-only). The canonical string is stored in
    the record as `canonical_string` so the hash input is auditable
    and re-computable. Discovering a DOI later does not change the
    pub_id. Full rule in §11.7 step 4.
5. What to do about the ~14 Phase B unresolved historical refs: drop them as
   part of Phase 2 triage, or keep with a `source="historical"` flag?
6. What to do about references cited by both processes and tasks that
   currently have different resolution status (Balleine & O'Doherty 2010,
   Haber & Knutson 2010 in §4 of `citation_gaps_2026-04-20.md`): fix in
   Phase 2 triage, before the systematic search runs.

---

## 13. Relationship to prior work

- **OpenAlex crosswalk** (`H:\Research\TaskResearch\OpenAlex\`) is reused as
  the routing layer. No new crosswalk. No changes to `crosswalks/` files.
- **`resolve_citations.py`** (from Phase B) remains the citation validator.
  We do not re-implement DOI-resolution logic in the new clients.
- **`enrich_citations_host_script.py`** is the template for the new
  `run_host.py`: single-file, stdlib + requests, argparse-driven, writes
  cached JSON.
- **`parse_citation_string.py`** (from Phase C) handles any legacy string
  references we choose to migrate; in the new publications-table model we
  don't need it for new entries.
- **`GoogleSearches/*.md`** continues to be a hint store, not a citation
  source.
- **`works/.status/works_step_proposal.md`**: paradigm extraction from
  abstracts. Adjacent but separate — we can run the two workstreams in
  parallel; the literature search gives us verified references and
  publications.json, the works proposal gives us candidate paradigm names.

---

## 14. Net estimate of effort and timeline

Rough estimate, assuming sandbox network access remains blocked and each
phase has its own sonnet session:

| Phase | Effort | Gated by |
|---|---|---|
| 1. Infrastructure | 1 session (Opus planning + Sonnet execution) | Zotero group creation (user) |
| 2. Triage existing | 1 session + user review | User review gate |
| 3. Per-item search | 2 sessions | API access (host-run) |
| 4. Co-mention search | 1 session | API access (host-run) |
| 5. Candidate review | Asynchronous, weeks | User |
| 6. Zotero + publications.json populate | 1 session per batch | Phase 5 sign-off |
| 7. PDF acquisition (rolling) | Ongoing | UTSA access; manual fetches |
| 8. Merge into authoritative JSON | 1 session | Phase 6 complete |
| 9. Quality audit | 1 session | Phase 8 complete |

Total: roughly 8–10 working sessions plus the user's review cycle. The review
gate at Phase 5 is the clock-limiting item.

---

## 15. What I recommend we do next

1. Confirm the §12 open decisions with the user.
2. Start with a **very narrow proof-of-concept**: run the whole pipeline
   (Phases 1 → 8) for one process (`hed_response_inhibition`) plus its 3–4
   linked tasks. This validates the infrastructure, surfaces integration
   issues with Zotero, and gives the user a worked example to react to.
3. Based on the POC, adjust the plan — especially §6 ranking weights and
   §5.2 venue allowlist — before rolling out to the full 275 items.
4. Only then proceed to the full-catalog search.

I would rather invest two weeks in a POC and have reviewers say "this is
what we want, just do the rest" than invest two months in the full catalog
and have reviewers say "we want different weights / publishers / roles".

---

## Appendix A — Known reference-quality failures to fix in Phase 2 triage

From `citation_gaps_2026-04-20.md`:

- IAPS Technical Manual (Lang et al. 1997) in
  `hedtsk_affective_picture_viewing` — false positive from Phase C still
  present; the current resolved record points to Schupp et al. 1997 (a
  different paper). Clear `doi/title/authors/url`, set
  `source="needs_review"`, then drop during Phase 2 triage (test manual).
- Pavlov (1927), Thorndike (1911), Sherrington (1906), von Békésy (1960),
  Rey (1941, French), Breitmeyer (1984), Baars (1988), Jeannerod (1988):
  candidates for triage drop. Replace with modern reviews of the same
  construct.
- Balleine & O'Doherty (2010) cross-file inconsistency: fix the DOI in
  `hedtsk_instrumental_conditioning` to match the one already manually
  corrected in process_details.json (`10.1038/npp.2009.131`).
- Haber & Knutson (2010) in `hedtsk_instrumental_conditioning` (status:
  unresolved): resolve via DOI `10.1038/npp.2010.129`.

These are easy wins that Phase 2 can knock out first, before we turn on the
systematic search.

---

## Appendix B — Suggested Zotero local-only setup steps for the user

### B.1 Install Zotero (once)

1. Install Zotero 7 desktop (https://www.zotero.org/download/). No
   account is needed. Do not sign in if prompted.

### B.2 Create a dedicated profile for the HED catalog

A separate Zotero profile guarantees the HED library cannot collide with
the user's normal Zotero library. Everything in the HED profile — items,
collections, tags, plugins, preferences — lives in its own profile
folder, and the **data directory** (the actual `zotero.sqlite` library
plus the `storage/` folder) is pointed at a separate path inside that
same tree. Both have to be set explicitly: Zotero keeps them as
independent preferences, and by default a new profile still reads the
old default data directory at `%USERPROFILE%\Zotero\`, which is why a
fresh profile often looks like it contains your personal library.

**Step 1 — Create the profile (sets only the profile folder):**

1. Close any running Zotero instance.
2. Launch the Zotero profile manager:
   - **Windows:** open a Command Prompt (or PowerShell), then run
     `"C:\Program Files\Zotero\zotero.exe" -P`
     (adjust the path if Zotero is installed elsewhere).
   - **macOS:** `/Applications/Zotero.app/Contents/MacOS/zotero -P`
   - **Linux:** `zotero -P`
3. In the profile manager, click **Create Profile…**, name it
   `hed-research`, and **choose a custom folder** for the profile's
   folder. Suggested path:
   `H:\Research\TaskResearch\Zotero-HED\profile\` (outside the Git
   repo). This folder holds `prefs.js`, extensions, session state — it
   does **not** yet contain your library.
4. Select `hed-research` and click **Start Zotero**. Expect the
   library to look like your personal library at this point — the data
   directory has not been moved yet.

**Step 2 — Move the data directory (this is what actually gives you an
empty library):**

5. In the `hed-research` Zotero, open **Edit → Settings (Preferences) →
   Advanced → Files and Folders → Data Directory Location**.
6. Select **Custom**, set it to
   `H:\Research\TaskResearch\Zotero-HED\data\` (or any empty folder
   outside `%USERPROFILE%\Zotero\`), and confirm.
7. Zotero asks to restart; restart it. On restart, Zotero sees an empty
   data directory and creates a fresh `zotero.sqlite` + `storage/`
   there. The library pane is now empty — this confirms you are no
   longer sharing data with your personal profile.

**Step 3 — Verify (takes 30 seconds):**

8. **Help → About Zotero** → scroll to the bottom. Confirm both:
   - Profile directory:
     `H:\Research\TaskResearch\Zotero-HED\profile\...`
   - Data directory: `H:\Research\TaskResearch\Zotero-HED\data\`
   If either still points at an AppData or `%USERPROFILE%\Zotero\`
   path, repeat the step that targets the wrong one.

**Step 4 — Make the profile easy to relaunch:**

9. (Recommended) Create a Windows shortcut that always launches this
   profile:
   - Target: `"C:\Program Files\Zotero\zotero.exe" -P hed-research`
   - (Add `-no-remote` to the target if you want to run this profile
     *alongside* your normal Zotero simultaneously.)
   Name it "Zotero (HED)" and keep it next to your normal Zotero icon.

**Why the two-step profile / data-directory split exists at all.**
Zotero treats the profile (preferences, extensions) as separate from
the library (data directory) so that, for example, a single profile can
be pointed at different libraries over time, or two profiles can share
a library if you want. For our purposes that's a footgun — it's easy
to create a new profile and assume you have a new library when you
don't. Setting the data directory explicitly is the step that actually
isolates the HED catalog.

### B.3 Configure the HED profile

With the `hed-research` profile running:

1. Install the Better BibTeX plugin
   (https://retorque.re/zotero-better-bibtex/). Plugins are per-profile,
   so this installs only in the HED profile.
2. Edit → Preferences → Advanced → Config Editor. Confirm / set:
   - `extensions.zotero.httpServer.enabled = true`
   - `extensions.zotero.httpServer.localAPI.enabled = true`
   (You can verify by visiting `http://localhost:23119/api/` in a
   browser while this Zotero is running — you should get a JSON
   response, not a 404. The profile name is not visible through the
   API, but the marker item planted by `zotero_sync.py` will confirm
   you are talking to the right library.)
3. Set the **Linked Attachment Base Directory** to the PDF root so
   Zotero stores linked-file paths *relative* to it and the tree is
   portable across machines:
   - Edit → Preferences → Advanced → Files and Folders → **Linked
     Attachment Base Directory** → set to
     `H:\Research\TaskResearch\HED-PDFs\`.
   - Create the directory first if it does not exist.
   - This makes Zotero record each PDF as e.g.
     `attachments:2012\Badre_2012_...a3b9f2c1.pdf` rather than a hard-
     coded absolute path.
4. Create the top-level collections listed in §11.1 (`Processes/`,
   `Tasks/`, `Co-mention/`, `_Landmarks`). The category sub-collections
   under `Processes/` and `Tasks/` are created automatically on first
   sync.
5. (Optional but recommended) Configure Better BibTeX auto-export:
   - Right-click the library root → Export Library.
   - Format: `Better CSL JSON`.
   - Keep updated: Yes.
   - Destination:
     `H:\Research\TaskResearch\Zotero-HED\zotero_export.json`.
   This file is git-ignored and lives alongside the profile folder; it
   exists only as the offline fallback sync channel.

### B.4 Record the profile and data-directory locations

Create `outputs/literature_search/.zotero_env` (git-ignored) with:

```
ZOTERO_PROFILE_NAME=hed-research
ZOTERO_PROFILE_DIR=H:\Research\TaskResearch\Zotero-HED\profile
ZOTERO_DATA_DIR=H:\Research\TaskResearch\Zotero-HED\data
ZOTERO_LOCAL_API=http://localhost:23119/api/
ZOTERO_BBT_EXPORT=H:\Research\TaskResearch\Zotero-HED\zotero_export.json
HED_PDFS_DIR=H:\Research\TaskResearch\HED-PDFs
```

No API key, no cloud account, no `ZOTERO_API_KEY` needed.
`ZOTERO_PROFILE_DIR` and `ZOTERO_DATA_DIR` must match the two paths
shown in **Help → About Zotero** under the `hed-research` profile.
`HED_PDFS_DIR` must match the "Linked Attachment Base Directory" you
configured in §B.3.3.

### B.5 First sanity check

With the HED profile running, run:

```
python outputs/literature_search/zotero_sync.py --check
```

Expected output:

1. `local API reachable on port 23119` ✓
2. `Better BibTeX export file found and parseable` ✓
3. `HED catalog marker item found` (or, on first run, `Marker item
   created`) ✓
4. A one-line summary of item count and collection count.

If Zotero is running with the wrong profile, step 3 fails safely — the
script detects the missing marker and exits without writing anything.

---

## Appendix C — Summary of decisions captured from the user

- Augment + prune, not wholesale replace: drop test manuals and ancient
  refs without clear landmark status; keep the rest.
- Deep corpus: ~5 key + ~20 recent + co-mentions per item.
- Institutional full-text access via UTSA; use Unpaywall + proxy.
- Zotero **in a dedicated local profile** (`hed-research`, data directory
  outside the Git repo) is the reference manager — no zotero.org account,
  no cloud sync, no group library, and fully isolated from the user's
  normal Zotero profile. Sharing with the HED team happens through Git
  (`publications.json`) and optional BibTeX exports.
- **PDFs live outside both the repo and the Zotero profile**, in a
  sibling directory `H:\Research\TaskResearch\HED-PDFs\<year>\`. Zotero
  references them as linked-file attachments, with the profile's "Linked
  Attachment Base Directory" set to the PDF root so paths stay portable.
- **PDF filenames are human-readable**:
  `<LastName>_<Year>_<CamelCaseTitle>_<hash8>.pdf`, where `<hash8>` is the
  same 8-hex-char SHA-1 tail that forms `pub_id` (`pub_<hash8>`) in the
  catalog. Full rules in §11.7.
- **`pub_id` = `pub_<hash8>`**, where `<hash8>` is the first 8 hex chars
  of SHA-1 over a metadata-only canonical string
  (`lastname + year + title`, lowercased to `[a-z0-9]`, truncated at
  100 chars). The canonical string is stored in the record as
  `canonical_string`. Discovering a DOI after record creation does not
  change the pub_id. Full rule in §11.7 step 4.

These shape every section above; any future change to these should update
this document's Scope block at the top.
