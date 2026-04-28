# Task: Enrich task references in task_details.json (includes schema migration)

**Date:** 2026-04-20
**Goal:** Parse the 748 plain-string references in `task_details.json` into structured reference objects matching the schema used by `process_details.json`, resolve each one against authoritative bibliographic sources, and migrate both the schema and the data in one coordinated pass. Update the regeneration script and every derived file that consumes task references.

This is **Phase C** of the citation-enrichment workstream. It depends on Phase B (process references) having completed and the resolver module `outputs/resolve_citations.py` being stable. Do not begin this pass until the process pass is reviewed and approved.

See also: `.status/citation_enrichment_thinking_2026-04-20.md` (strategy), `task_citation_enrich_processes_instructions.md` (Phase B), `citation_gaps_*.md` (gaps log).

---

## Context

`task_details.json` is a flat JSON array of 103 task objects. Each task has two reference arrays: `key_references` and `recent_references`. Today they are **lists of plain strings** in APA-ish format. Example:

```
"Lang, P. J., Bradley, M. M., & Cuthbert, B. N. (1997). *International Affective Picture System (IAPS): Technical Manual and Affective Ratings*. NIMH Center for the Study of Emotion and Attention."
```

Totals: 103 tasks, 748 references, 0 objects, 13 references that already mention a DOI explicitly.

Two problems to solve in one pass:

1. **Schema migration.** Convert each string to the structured reference object used by `process_details.json` (see §Schema notes below).
2. **Enrichment.** Fill in DOI / OpenAlex ID / PMID, verify the DOI resolves, set source/confidence/verified_on.

These are coupled: the resolver needs something to work with, and the cleanest input is already-parsed fields. So the pass order is: **parse → resolve → merge → validate**.

---

## What specifically needs to happen

### Phase 1: Confirm dependencies

- Read `.status/citation_enrichment_thinking_2026-04-20.md` in full.
- Confirm `outputs/resolve_citations.py` exists and was used successfully in the process pass. Run the module's built-in self-test (you should have added one during Phase B) to confirm CrossRef / OpenAlex / Europe PMC / Semantic Scholar are still reachable.
- Read `.status/session_2026-04-20_citation_enrich_processes.md` for any lessons learned (e.g., if CrossRef was flaky, adjust the timeout).

### Phase 2: Write a citation-string parser

Create `outputs/parse_citation_string.py`. Target: ~200 lines. It exposes:

```python
@dataclass
class ParsedCitation:
    authors: str                # e.g. "Lang, P. J., Bradley, M. M., & Cuthbert, B. N."
    year: int | None
    title: str
    venue: str | None
    venue_type: str             # journal | book | book_chapter | report | proceedings | other
    volume: str | None
    issue: str | None
    pages: str | None
    doi: str | None             # if the string already contains a DOI

def parse(citation_string: str) -> ParsedCitation:
    ...
```

Parser behavior — APA-ish format:

1. **Find the year.** First `(YYYY)` or `(YYYY[a-z])` pattern. Extract the integer. If no parenthesized year, try a trailing ` YYYY.` pattern. If neither, year is `None`.
2. **Split on year.** Everything before the year is the authors string; everything after (before the next period) is the title.
3. **Title handling.** Strip markdown italics (`*...*`, `_..._`) around the title. A title ending in `.` terminates; a title ending in `?` or `!` also terminates.
4. **Venue detection.** After the title, the next chunk is the venue. If it's italicized (`*Journal Name*`), `venue_type = journal` and the rest (`volume(issue), pages` or `volume, pages`) follows standard APA. If it starts with "In " and then a title-case phrase, `venue_type = book_chapter` and the venue is the book title. If the remainder is a publisher (e.g., "Oxford University Press"), `venue_type = book`. If none of the above match cleanly, `venue_type = other` and keep the raw remainder as `venue`.
5. **Volume / issue / pages.** Regex: `(\d+)\((\d+)\),\s*(\d+[\-\u2013]\d+)` for `volume(issue), pages`. Or `(\d+),\s*(\d+[\-\u2013]\d+)` for `volume, pages`. En-dash and hyphen both accepted.
6. **DOI detection.** Regex: `\b10\.\d{4,9}/\S+\b`. Strip trailing punctuation.

**Write a test fixture** at `outputs/parse_citation_string_tests.py` with ~20 hand-picked strings covering: journal article, book, book chapter with "In ... (Eds.)", technical manual, tech report, pre-prints, and at least one string that will not parse cleanly (to confirm graceful degradation).

Run the tests before using the parser on real data. If any fail, fix the parser; do not lower the test bar.

### Phase 3: Dry-run the parser on all 748 strings

Write `outputs/parse_task_references_dryrun.py`. It:

1. Reads `task_details.json` via the Read tool.
2. For each reference string in every task, calls the parser.
3. Classifies: `{clean_journal, clean_book, clean_chapter, clean_report, malformed, has_doi_already}`.
4. Writes a table to `outputs/parse_dryrun_report.md` with counts and, for each category, up to 5 examples.

Read the dry-run report. If malformed exceeds **5%** (~37 refs), **stop and improve the parser** before continuing. Malformed here means "the parser returned mostly empty fields". Some hand-rolled refs (user-provided books, classics) will legitimately have sparse fields — that is fine. But if "Wechsler, D. (1997). *WMS-III*. Pearson." comes out with `authors=""`, that's a parser bug.

### Phase 4: Resolve each parsed reference

Write `outputs/enrich_task_references.py`. For each reference:

1. Run the parser to get `ParsedCitation`.
2. Call `resolve_reference(citation_string, venue, year, cache_dir)` from the resolver module (which was tuned during Phase B). Reuse the cache — many task references are likely duplicates of process references (e.g., foundational papers cited by both).
3. Merge the resolver result with the parser result. **Resolver fields take precedence** where they disagree, except for the original `citation_string`, which is always preserved verbatim.
4. Build the final reference object with the target schema (see §Schema notes).

### Phase 5: Apply the migration to task_details.json

1. Read `task_details.json` via the Read tool, write a copy to `outputs/task_details.working.json`.
2. For each task, replace `key_references: [str, ...]` with `key_references: [object, ...]` (same for `recent_references`).
3. **Sanity checks before saving:**
   - Count of references per task is unchanged.
   - Every original citation_string appears (byte-for-byte) somewhere in the new array's `citation_string` fields.
   - All 103 tasks present; no `hedtsk_id` changed.
4. Write the result to `outputs/task_details.enriched.json`.
5. Use the Write tool to copy it back to the authoritative `H:\Research\TaskResearch\Claude-research\task_details.json`.

### Phase 6: Update the regeneration script

`outputs/regenerate_derived_files.py` consumes `task_details.json`. It likely reads `key_references` / `recent_references` either not at all or only to display a count. After the migration:

- Audit the script for any code that assumes references are strings.
- Update as needed; keep the change small.
- Re-run the script.
- Verify `task_names.json`, `process_task_index.json`, `process_task_crossref.md`, and `file_inventory.md` still regenerate without errors.

### Phase 7: Update file_inventory and criteria

- Edit `file_inventory.json`: update the description of `task_details.json` to reflect the new reference schema.
- Edit `tasks_criteria.md` §References section (if present) to mention the structured reference schema. If the file has no explicit references section, do **not** add one in this pass — the user's preference is not to over-engineer.

### Phase 8: Validation

- Read the updated `task_details.json` via the Read tool.
- Confirm: 103 tasks; each reference is an object with at minimum `authors`, `year`, `citation_string`, `source`, `confidence`; all original citation strings preserved.
- Spot-check 10 random references for DOI resolvability.
- Cross-check 5 references that appear in both `process_details.json` and `task_details.json` (use citation_string match). The resolved DOI should agree across both files. If not, investigate.

### Phase 9: Extend the gaps document

Open `.status/citation_gaps_2026-04-20.md` (renamed during Phase B). Append a dated section for this pass covering:

- Every task reference that came back `source="unresolved"`.
- Every task reference where `confidence="low"` was accepted.
- Task definitions that seem misaligned with the resolved literature (e.g., the top CrossRef hit for the Wechsler digit-span reference suggests a different edition of the manual than the one cited).
- **Potential missing tasks** the literature surfaced: paradigms that appeared in the top-N CrossRef/OpenAlex hits for the concept or process linked to a task, but which are not in the catalog as their own task entry.
- **Potential missing processes** surfaced the same way.

### Phase 10: Write session report

Write `.status/session_2026-04-20_citation_enrich_tasks.md` documenting:

- Parser accuracy on the 748 strings (clean / malformed / has-doi breakdown).
- Resolver success rate by source and confidence.
- Schema migration stats (references before/after, file size before/after).
- Changes to `regenerate_derived_files.py`.
- Any citation_string that produced a resolver mismatch (e.g., wrong year, wrong journal, probable typo in the source).
- A list of follow-ups for human review.

---

## CRITICAL: File access rules — virtiofs stale snapshot issue

Same rules as Phase B. Use Read/Write/Edit tools on the Windows workspace path. Use bash only against `outputs/`. After any Write to the workspace, verify with the Read tool, not bash.

---

## Schema notes

### Target reference object (final, both files)

```json
{
  "authors": "Lang, P. J., Bradley, M. M., & Cuthbert, B. N.",
  "year": 1997,
  "title": "International Affective Picture System (IAPS): Technical Manual and Affective Ratings",
  "venue": "NIMH Center for the Study of Emotion and Attention",
  "venue_type": "report",
  "journal": null,
  "volume": null,
  "issue": null,
  "pages": null,
  "doi": null,
  "openalex_id": "https://openalex.org/W...",
  "pmid": null,
  "citation_string": "Lang, P. J., Bradley, M. M., & Cuthbert, B. N. (1997). *International Affective Picture System (IAPS): Technical Manual and Affective Ratings*. NIMH Center for the Study of Emotion and Attention.",
  "source": "openalex",
  "confidence": "medium",
  "verified_on": "2026-04-20"
}
```

### Backward compatibility

- The `citation_string` field carries the original human-readable form. Anyone who used `ref_string` before the migration can use `ref["citation_string"]` now.
- `journal` is populated only for `venue_type = journal`. For books and reports, `venue` is populated and `journal` is null. This aligns with the process_details schema (where `journal` is populated because every process ref is currently a journal article; after enrichment the same field becomes conditional).

### Rules

- The 13 task references that already mention a DOI in the string: the parser extracts them, the resolver verifies them (HEAD request to `doi.org/<doi>`), and the source is recorded as the **first** automated source that confirms the DOI (usually CrossRef). If the DOI doesn't resolve, flag as a `confidence: low` with `doi: null` in the final record, keep the original DOI string in `citation_string`.

---

## Network access check (FIRST STEP)

Same as Phase B. Confirm egress to `api.crossref.org`, `api.openalex.org`, `www.ebi.ac.uk`, `api.semanticscholar.org`, and `doi.org`. If any is blocked, produce a host-side script following the `OpenAlex/pull_openalex.py` pattern.

---

## File inventory

### Files you will modify
- **`task_details.json`** — Schema migration (strings → objects) and enrichment.
- **`file_inventory.json`** — Description update.
- **`outputs/regenerate_derived_files.py`** — Audit and adjust for new reference shape.
- **`tasks_criteria.md`** — Only if it has a references section; add a brief note about the schema.

### Files you will create
- **`outputs/parse_citation_string.py`** — APA-ish string parser.
- **`outputs/parse_citation_string_tests.py`** — Unit tests.
- **`outputs/parse_task_references_dryrun.py`** — Dry-run analyzer.
- **`outputs/parse_dryrun_report.md`** — Dry-run output.
- **`outputs/enrich_task_references.py`** — Full enrichment driver.
- **`outputs/task_details.working.json`** and **`outputs/task_details.enriched.json`** — Intermediate artifacts.
- **`.status/session_2026-04-20_citation_enrich_tasks.md`** — Session report.

### Files for reference (do not modify)
- **`process_details.json`** — Already enriched in Phase B. Reference for the target schema.
- **`outputs/resolve_citations.py`** — Resolver from Phase B. Reuse as-is; do not modify.
- **`.status/citation_enrichment_thinking_2026-04-20.md`** — Strategy.
- **`Claude research-temp/task_concept_supplement_references_variations_models.md`** — 972-line supplement with additional tasks and APA refs. May contain cleaner versions of existing task refs. Use it as a cross-check for confidence-low resolutions: if the supplement has the same citation with more complete info, promote confidence.
- **`GoogleSearches/*.md`** — Rough AI-overview hints. Use as a backup sanity-check for paradigm names; do not extract citations from them.

### Derived files (regenerate after migration)
- **`task_names.json`**, **`process_task_index.json`**, **`process_task_crossref.md`**, **`file_inventory.md`**.

---

## Verification checklist (must all pass before declaring done)

- [ ] `outputs/resolve_citations.py` and `outputs/parse_citation_string.py` exist and are tested.
- [ ] Parser dry-run report shows <5% malformed.
- [ ] Every reference in `task_details.json` is an object (no strings remain).
- [ ] Every original `citation_string` appears verbatim in the new data.
- [ ] All 103 tasks present; no hedtsk_id changed.
- [ ] Reference counts per task unchanged.
- [ ] Derived files regenerate without error.
- [ ] Spot-check 10 DOIs resolve via `doi.org`.
- [ ] `citation_gaps_2026-04-20.md` has an appended task-pass section.
- [ ] `file_inventory.md` reflects the new schema.
- [ ] Session report written.

---

## Working conventions

- Same as Phase B.
- Pay extra attention to the schema migration step. A failed migration corrupts the entire task catalog; back up `task_details.json` to `original/task_details_pre_enrichment_2026-04-20.json` before writing the enriched version.
- If any validation step fails, stop, write a note to `.status/`, ask for confirmation before retrying. Do not auto-heal.

---

## Remaining items (NOT part of this task — do not attempt)

1. **Catalog expansion.** Any "missing task" or "missing process" found during the gaps review is recorded, not added. New entries are a separate decision.
2. **Paradigm extraction from abstracts.** Separate workstream (`OpenAlex/works/.status/works_step_proposal.md`).
3. **Citation graph analysis.** Who-cites-whom using OpenCitations. Future-phase.
4. **Process-ref / task-ref deduplication.** Not attempted here; keep duplicates on purpose.
