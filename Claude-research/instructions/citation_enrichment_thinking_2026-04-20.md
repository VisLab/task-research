# Citation Enrichment — Strategy and Thinking

**Date:** 2026-04-20
**Purpose:** Summary of how I (Claude Opus) thought through the citation-enrichment problem for the HED task and process catalog, and the rationale for the plan split into two execution passes (processes first, tasks second).

This document is the "thinking" counterpart to the two instruction files in the same directory:
- `task_citation_enrich_processes_instructions.md` — Phase B (process references)
- `task_citation_enrich_tasks_instructions.md` — Phase C (task references, includes schema migration)
- `citation_gaps_initial_2026-04-20.md` — Initial gaps observations, to be extended by sonnet

---

## 1. Starting state of the catalog (2026-04-20)

Concrete numbers, read from the two authoritative JSON files:

| File | Entries | Reference count | Notable issues |
|---|---:|---:|---|
| `process_details.json` | 172 processes, 19 categories | **404** references (objects) | **All 404 `title` fields are empty.** `journal`, `year`, `citation_string` are populated. No DOIs anywhere. |
| `task_details.json` | 103 tasks | **748** references (plain strings) | Well-formed APA-ish citation strings, often with italicized journal name, often with page ranges. Only ~13 mention a DOI explicitly. |

Two different schemas. Two different problems:

- **Processes** — already structured; we need to *fill* missing fields (title, authors, DOI) without changing the outer shape of the array.
- **Tasks** — still strings; we need to *parse* them into structured records and only then fill in DOIs. This is a schema migration on top of the enrichment.

This asymmetry is the main reason the plan splits into two sonnet sessions.

---

## 2. What "definitive citations with complete information" means

The target reference record (same schema for both files at the end):

```json
{
  "authors": "Rescorla, R. A., & Wagner, A. R.",
  "year": 1972,
  "title": "A theory of Pavlovian conditioning: Variations in the effectiveness of reinforcement and nonreinforcement",
  "venue": "Classical Conditioning II: Current Research and Theory",
  "venue_type": "book_chapter",
  "volume": null,
  "issue": null,
  "pages": "64–99",
  "doi": null,
  "openalex_id": "https://openalex.org/W...",
  "pmid": null,
  "url": null,
  "citation_string": "Rescorla & Wagner (1972) in *Classical Conditioning II*",
  "source": "crossref",
  "confidence": "high",
  "verified_on": "2026-04-20"
}
```

Decisions embedded in this schema:

1. **Keep `citation_string`**. It is the one human-readable field that is always present; useful as a last-resort display when structured fields are incomplete (e.g., old books with no DOI).
2. **`venue` (not `journal`)**. Books, proceedings, and technical reports don't have journals. `venue_type` (`journal` / `book` / `book_chapter` / `proceedings` / `report` / `preprint` / `other`) disambiguates.
3. **`source` + `confidence` + `verified_on`**. These are provenance. They are the difference between "I filled this in by LLM-guess" (low) and "I round-tripped through CrossRef on 2026-04-20 and the DOI resolves" (high). The user explicitly asked about correcting existing citations — without provenance we cannot tell generated from verified.
4. **`openalex_id` alongside `doi`**. OpenAlex IDs resolve for works that have no DOI (especially older books and grey literature). Keeping both future-proofs the catalog.
5. **No `authors_parsed` field** (list of structured names). Tempting, but overbuilt for our use case; APA-style string is enough and avoids name-parsing ambiguity.

---

## 3. Source selection

### Sources the user named

| Source | API | Rate limit | DOI/Metadata quality | Coverage for cog-sci | Verdict |
|---|---|---|---|---|---|
| **OpenAlex** | `api.openalex.org/works` | ~10 req/s polite pool, `mailto=`. Already set up in `OpenAlex/works/fetch_works.py`. | Excellent. Has DOI, year, venue, inverted-index abstract, cited_by_count. | Very broad — includes psychology, neuroscience, cognitive science. | **Primary lookup source.** |
| **PubMed / Europe PMC** | `www.ebi.ac.uk/europepmc/webservices/rest/search` (JSON) | ~10 req/s, no key needed. | Excellent for biomedical. Has PMID, DOI, abstract, MeSH. | Strong for neuroimaging, neurology, clinical. Weaker for cognitive psychology proper. | **Secondary, biomed-heavy refs.** |
| **OpenCitations** | `opencitations.net/index/api/v2` | Unauthenticated, rate-limited. | Good for citation edges; metadata is DOI-keyed only. | Depends on COCI/PubMedCitations, which lag. | **Not used for primary lookup.** Optional for downstream citation graph work. |
| **Semantic Scholar** | `api.semanticscholar.org/graph/v1` | 1 req/s for both unauthenticated and free-tier key callers. (Earlier copy of this row claimed 100 req/s with a free key; corrected 2026-04-28.) | Strong — has tldr, abstract, authors, venue. | Very broad. | **Tertiary fallback** when OpenAlex and Europe PMC both miss. |
| **Google Scholar** | None. Scraping is ToS-banned. | N/A | The most comprehensive, including grey literature and books. | Would be best if we could use it. | **Manual fallback only**, user-driven, not automated. |

### One more source I'd add

**CrossRef** (`api.crossref.org/works`) — the authoritative DOI registry, free, unauthenticated, polite pool via `mailto=`. Strongest single source when we have a known author/year/title to validate, because CrossRef *is* the DOI source of truth. I put CrossRef *ahead of* OpenAlex for validation queries (author+year+title lookup to confirm DOI) and OpenAlex *ahead of* CrossRef for discovery (search by concept name, return top-N Works).

### Final lookup order (same for processes and tasks)

For each existing reference:

1. **CrossRef `/works` query** with `query.author=<surname>`, `query.bibliographic=<title-ish>`, `filter=from-pub-date:YYYY,until-pub-date:YYYY`. If top hit has matching surnames + year, accept its DOI + title + venue. Confidence = high.
2. **OpenAlex `/works` search** with `search=<citation string, stripped>`, `filter=publication_year:YYYY`. If top hit matches on surname + year, accept. Confidence = high/medium.
3. **Europe PMC `/search`** query — only for refs whose `journal` or `citation_string` looks biomedical (contains "Neuroimage", "J Neurosci", "PNAS", "Nat Neurosci", etc.). Accept PMID/DOI.
4. **Semantic Scholar `/paper/search`** — last automated resort.
5. Unresolved → flag in `citation_gaps_*.md`, leave original fields intact, set `source="unresolved"`, `confidence="none"`. Do not hallucinate DOIs.

### What we don't do

- Do not invent DOIs. A DOI we cannot independently verify (via `doi.org/<doi>` HEAD request returning 200) is not accepted.
- Do not rewrite the original `citation_string`. It stays as-is so we can always compare old ↔ new.
- Do not merge refs across processes/tasks even if they point to the same paper. Duplication across the two files is correct — a single paper may be both a fundamental reference for a process and a key reference for a task.

---

## 4. Rate limiting, caching, idempotence

Total work volume: ~1,150 references across the two files. Expected runtime at 0.3 s per lookup (with 2–3 API hops in the worst case): **~15–30 minutes** of wall clock, well within one sonnet session.

- **Cache each successful lookup** under `H:\Research\TaskResearch\Claude-research\outputs\citation_cache\` as `<doi-slug-or-hash>.json`. On re-run, a cache hit is a no-op.
- **Polite headers everywhere.** `User-Agent: hed-task/1.0 (mailto:hedannotation@gmail.com)` + `mailto=` query param where supported.
- **No retries on 4xx**. 4xx means the query was bad; log it and move on.
- **Exponential backoff on 429/5xx** — 1 s, 2 s, 4 s, then give up.

Network egress: the workspace may not have `api.crossref.org`, `www.ebi.ac.uk`, or `api.semanticscholar.org` on the allowlist. The instructions file tells sonnet to check this first and, if blocked, to generate a standalone Python script the user can run on the host machine (mirroring the `pull_openalex.py` pattern already in the OpenAlex work).

---

## 5. Why split into two sonnet sessions

Tried one session; doesn't fit cleanly:

- The **process** pass is primarily a "fill empty fields" exercise. The outer shape of the JSON doesn't change (the `fundamental_references`/`recent_references` arrays stay, new fields are added inside each reference object). The risk of breaking existing machinery is low.
- The **task** pass requires *parsing strings into objects*, which is a schema change. Every file that consumes `task_details.json` (`regenerate_derived_files.py`, the process_task_crossref derivation) needs to be re-checked. Higher risk; benefits from a dedicated session with its own verification plan.

Splitting also means the user can approve the process result before investing in the task migration — if the enrichment quality is bad for processes (hallucinated DOIs, false positives on author match), we can stop cheap rather than after 748 tasks are scrambled.

Order: **processes first, tasks second.** If the resolver infrastructure needs tuning, we tune it on the 404-ref corpus, not the 748-ref one.

---

## 6. What I won't do in these plans

- No "citation quality score". That is a future-phase research question in its own right.
- No cross-check between process refs and task refs for shared DOIs. Possibly useful later (e.g., "paper X is cited by 7 processes and 4 tasks — flag for review"), but not now.
- No automated update of `process_criteria.md` or `tasks_criteria.md` based on the enrichment. Those documents describe the *criteria*, not the *data*.
- No paradigm extraction from OpenAlex abstracts. That is what the existing `OpenAlex/works/.status/works_step_proposal.md` design is for, and it is a separate workstream (orphan-task finding), not citation enrichment of already-listed refs.

---

## 7. Relationship to prior work

- **`OpenAlex/` directory** (2026-04-14): Already has `pull_openalex.py` (taxonomy), crosswalks from concepts to Topics, a POC Works pull for 5 orphans, and a gap assessment in `OpenAlex/reports/coverage_assessment.md`. The citation-enrichment plans **reuse** the OpenAlex polite-pool conventions and the Works inverted-index abstract helper, but do not modify the crosswalks.
- **`GoogleSearches/` directory**: ~30 `.md` files with rough AI-overview text and URLs. Not a structured citation source; treat as **hints** for sonnet when an automated lookup fails (e.g., to confirm a paradigm name), not as a citation source.
- **`Claude research-temp/task_concept_supplement_references_variations_models.md`**: 972-line supplement written earlier with additional tasks (#51–75+) and APA-style references. This file is **probably a goldmine** — many task references in `task_details.json` may already be drawn from it, but it may contain fuller / better-formatted refs. Sonnet should spot-check it during the task pass.

---

## 8. Gaps and policy questions identified while planning

(Also written to `citation_gaps_initial_2026-04-20.md` in this directory; sonnet extends that file during execution.)

Immediate observations:

1. **Books have no DOIs.** Wechsler (1997), Baddeley (1986), Pavlov (1927), Thorndike (1911), Lang et al. (1997) technical manual — these are book/manual refs, expect many unresolved-by-DOI outcomes. Planned behavior: OpenAlex often has a Work record for books (e.g., `W2802...` for "Working Memory"); accept an OpenAlex ID even without a DOI.
2. **Several refs have journal-only format** in process_details.json (e.g., `"Rescorla & Wagner (1972) in *Classical Conditioning II*"`). These are book chapters, not journal articles. Plan needs to detect and label `venue_type: book_chapter`.
3. **Single-author et-al. citations** (`"Balleine & O'Doherty (2010)"` — only two authors shown, but the paper has more). CrossRef returns the full author list; after enrichment, the `authors` field will be longer than what the current `citation_string` shows. That's fine; `citation_string` is preserved.
4. **Pre-1950 refs with no clean metadata record** (Pavlov 1927, Thorndike 1911). Expected to be unresolved. Mark as `source="historical"`, `confidence="low"`, keep original fields. Do not invent DOIs.
5. **The Levy & Glimcher (2012) correction noted in `process_criteria.md` §5** — journal was corrected manually on 2026-04-18. Sonnet should re-verify this against CrossRef to make sure the fix holds.
6. **Potential catalog gaps surfaced indirectly.** Lookup queries that return zero hits across all sources may indicate the process/task description doesn't match the literature's terminology — a surface-form issue that the gaps document should capture (category D in `OpenAlex/reports/coverage_assessment.md`).

---

## 9. What sonnet produces at the end

After both passes complete, expected artifacts:

- Updated `process_details.json` with structured, DOI-bearing references (where resolvable).
- Updated `task_details.json` with references migrated from strings to objects, structured and DOI-bearing.
- `outputs/citation_cache/` — raw API responses keyed by DOI / OpenAlex ID for provenance.
- `outputs/resolve_citations.py` — the resolver script (kept, not deleted, so the user can re-run).
- `.status/session_YYYY-MM-DD_citation_enrich_processes.md` and `.status/session_YYYY-MM-DD_citation_enrich_tasks.md` — session reports.
- `.status/citation_gaps_YYYY-MM-DD.md` — the final gaps document, expanded from the initial file.
- An updated `file_inventory.json` / `file_inventory.md` reflecting the enriched JSON schema.

After these artifacts land, the "2026-04-19 known issue 7.12 — empty reference titles (407 entries)" item in `process_criteria.md` is closed.
