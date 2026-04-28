# Task: Enrich process references in process_details.json

**Date:** 2026-04-20
**Goal:** Resolve each of the 404 reference objects in `process_details.json` against authoritative bibliographic sources, fill in the empty `title` fields and add DOIs/IDs where they exist, and preserve the original `citation_string` for human display. Produce a session report and extend `citation_gaps_initial_2026-04-20.md` with any unresolved references.

This is **Phase B** of the citation-enrichment workstream. See `.status/citation_enrichment_thinking_2026-04-20.md` for strategy, source selection rationale, and the target reference schema. Phase A was planning (this document and its sibling). Phase C (task references) is a separate sonnet session and is tracked in `task_citation_enrich_tasks_instructions.md`.

---

## Context

You are working on the HED (Hierarchical Event Descriptor) cognitive process catalog. The workspace root is `H:\Research\TaskResearch\Claude-research\`. The authoritative process data is in `process_details.json`: 172 processes across 19 categories, with two reference arrays per process (`fundamental_references`, `recent_references`).

Current state:

- **404 reference objects total.** Every one has an empty `title` field.
- `journal`, `year`, and `citation_string` are populated; no DOIs anywhere.
- Processes with 0 refs: 0. Processes with <2 refs: 0. Coverage is complete at the ref-count level; quality is the issue.

Task outcome: every reference object gains structured fields (`authors`, `title`, `venue`, `venue_type`, `doi`, `openalex_id`, `pmid` where applicable, `source`, `confidence`, `verified_on`). The original fields (`journal`, `year`, `citation_string`) are preserved.

---

## What specifically needs to happen

### Phase 1: Read the strategy doc and decide on schema

Read `.status/citation_enrichment_thinking_2026-04-20.md` in full. The target reference schema is defined in §2 of that file. **Do not deviate from that schema without writing a dated decision note to `.status/`.**

If you find a reason to add or remove a field from the schema during execution, stop, write the decision note, and ask for confirmation before continuing.

### Phase 2: Build the resolver module

Create `outputs/resolve_citations.py`. Target: ~300 lines of flat Python, no classes beyond a couple of dataclasses. Depends only on `requests` and the standard library.

The module exposes one function:

```python
def resolve_reference(
    citation_string: str,
    journal: str | None,
    year: int | None,
    cache_dir: Path,
) -> ResolvedReference:
    ...
```

Internally it tries, in order:

1. **Cache check.** Compute a stable hash of the input triple (citation_string, journal, year). If `cache_dir/<hash>.json` exists, load and return.
2. **CrossRef** — `https://api.crossref.org/works?query.bibliographic=<citation_string>&filter=from-pub-date:<year>,until-pub-date:<year>&rows=3`. Include `User-Agent: hed-task/1.0 (mailto:hedannotation@gmail.com)` and `mailto=hedannotation@gmail.com`. Accept the top hit if (a) year matches exactly, and (b) at least one surname from the citation_string matches at least one author's family name in the hit (case-insensitive). Confidence = `high`.
3. **OpenAlex Works** — `https://api.openalex.org/works?search=<citation_string, stripped of punctuation>&filter=publication_year:<year>&per-page=3&mailto=hedannotation@gmail.com`. Same acceptance rule. Confidence = `high` if DOI present, `medium` otherwise.
4. **Europe PMC** — `https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=<citation_string>+AND+PUB_YEAR:<year>&format=json&resultType=core&pageSize=3`. Only consult if CrossRef and OpenAlex both missed **and** the journal or citation_string contains a biomedical token (see stop-list below). Confidence = `medium`.
5. **Semantic Scholar** — `https://api.semanticscholar.org/graph/v1/paper/search?query=<citation_string>&year=<year>&limit=3&fields=externalIds,title,authors,venue,year`. Last resort; accept only with author + year match. Confidence = `low`.
6. Otherwise return `source="unresolved"`, `confidence="none"`, leaving structured fields blank but `citation_string` intact.

**Biomedical token list** (for Europe PMC gating):
`NeuroImage, J Neurosci, Neuron, Nature Neuroscience, Nat Neurosci, PNAS, PLoS, Biol Psychiatry, Cereb Cortex, Hippocampus, Brain, Psychol Rev, JAMA, Lancet, PMC`.

Rate limiting: 0.2 s sleep between calls to the same host. Retry on 429/5xx with backoff (1, 2, 4 s; give up after three attempts). Do not retry on 4xx.

**Verification:** For every DOI returned by any source, issue a HEAD request to `https://doi.org/<doi>`. Reject DOIs that don't resolve (non-2xx/3xx). This catches typos and malformed DOIs.

**Author-surname match logic:** Extract surnames from the `citation_string` by taking everything before the first `(` (year marker), split on `,`, `&`, `and`, take the word(s) before any initials. Compare against each `family` name in the API response's author list, case-insensitive, unicode-normalized. One match is sufficient.

**Do not** import anything exotic. No pyalex, no crossrefapi, no requests-cache. Plain `requests` and `json`.

### Phase 3: Apply the resolver to every process reference

Write `outputs/enrich_process_references.py`. It:

1. Uses the **Read tool** (not bash `open()`) to load `process_details.json` — virtiofs stale-snapshot rules apply, see §CRITICAL below.
2. Copies to `outputs/process_details.working.json`.
3. For each process, for each reference in `fundamental_references` and `recent_references`, calls `resolve_reference(...)` and merges the result into the reference object (preserving `journal`, `year`, `citation_string`).
4. Writes the enriched file to `outputs/process_details.enriched.json`.
5. Prints a summary: total references, resolved (high/medium/low), unresolved, per-confidence counts.

Then, using the Write tool, copy `outputs/process_details.enriched.json` to `H:\Research\TaskResearch\Claude-research\process_details.json` (the authoritative location).

### Phase 4: Verification

After applying the enrichment:

- Use the **Read tool** to re-load `process_details.json` from the workspace and verify no data was lost (all 172 processes present, all reference arrays intact, all original fields preserved).
- Confirm the header fields (`total_processes`, `total_categories`) are unchanged.
- Spot-check 10 random references: does the new `title` sound right for the `journal`/`year`/`citation_string`? Does `https://doi.org/<doi>` resolve in a HEAD request from the resolver cache?
- Regenerate derived files via `outputs/regenerate_derived_files.py`. Confirm `task_names.json`, `process_task_index.json`, `process_task_crossref.md`, and `file_inventory.md` are still valid JSON/markdown.

### Phase 5: Update file inventory

Edit `file_inventory.json`: update the description of `process_details.json` to mention the enriched reference schema and the 2026-04-20 enrichment date. Run `outputs/regenerate_derived_files.py` to regenerate `file_inventory.md`.

### Phase 6: Extend the gaps document

Open `.status/citation_gaps_initial_2026-04-20.md`. Append a dated section listing:

- Every reference that came back `source="unresolved"` — process name, citation_string, what was tried, what failed.
- Every reference where the resolver accepted a match at `confidence="low"` — these need human review.
- Any **process whose definition looks thin or mismatched** relative to what the literature surfaced (e.g., the top CrossRef hit for the citation had a title that suggested a different construct than the process definition).
- Any **potential missing processes** the literature lookup surfaced: constructs that appeared prominently in the retrieved papers but have no corresponding process in the catalog.

Rename the file to `.status/citation_gaps_2026-04-20.md` (drop the `_initial_` marker) once you are done writing to it.

### Phase 7: Write session report

Write `.status/session_2026-04-20_citation_enrich_processes.md` documenting:

- How many references were resolved, at what confidence, from which source.
- Any corrections you found (e.g., wrong year, wrong journal — compare old citation_string against resolved record).
- The Levy & Glimcher (2012) ref specifically — verify the manual correction noted in `process_criteria.md` §5 against CrossRef.
- Any changes to the plan as executed (with rationale).
- A list of follow-ups for the task pass.

---

## CRITICAL: File access rules — virtiofs stale snapshot issue

**The bash sandbox sees a stale, potentially corrupted snapshot of mounted workspace files.** This has bitten every prior session. Rules:

1. **ALWAYS use the Read tool** (with Windows paths like `H:\Research\TaskResearch\Claude-research\process_details.json`) to read files. Do NOT use bash `cat`, `head`, `tail`, or Python `open()` on the mounted path.
2. **ALWAYS use the Write or Edit tool** to write files back to the workspace.
3. **If you must use bash for processing**, Read the file with the Read tool, Write a copy to the outputs directory (`C:\Users\Robbi\AppData\Roaming\Claude\local-agent-mode-sessions\...\outputs\`), process the copy in bash, then Write the result back to the workspace path.
4. **After any Write/Edit to a workspace file**, do NOT try to read it back via bash to verify — use the Read tool.
5. **If a JSON parse error occurs in bash**, it is almost certainly the stale snapshot (trailing null bytes), not a real problem. Strip null bytes from the copy.

The outputs directory is safe for bash I/O. The workspace mount is NOT safe for direct bash I/O.

---

## Network access check (FIRST STEP)

Before writing any resolver code, confirm egress to each API host. In bash:

```
curl -I --max-time 5 https://api.crossref.org/works?rows=1
curl -I --max-time 5 "https://api.openalex.org/works?per-page=1"
curl -I --max-time 5 "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=test&format=json&pageSize=1"
curl -I --max-time 5 "https://api.semanticscholar.org/graph/v1/paper/search?query=test&limit=1"
```

Expected: HTTP 200 from each.

**If any host returns a connection error**, do not attempt to work around it. Stop, write a note to `.status/citation_enrichment_blocked_<date>.md` describing which hosts are blocked, and produce a **standalone Python script** (`outputs/enrich_citations_host_script.py`) the user can run on the host machine. Follow the pattern of `OpenAlex/pull_openalex.py`: argparse-driven, `requests`-based, writes cached JSON to a timestamped directory.

---

## File inventory

### Files you will modify
- **`process_details.json`** — Reference enrichment; outer shape unchanged. Windows path: `H:\Research\TaskResearch\Claude-research\process_details.json`
- **`file_inventory.json`** — Update description of `process_details.json` to note 2026-04-20 enrichment.

### Files you will create
- **`outputs/resolve_citations.py`** — Reusable resolver (also used by the task pass).
- **`outputs/enrich_process_references.py`** — Driver script for this pass.
- **`outputs/citation_cache/*.json`** — One file per unique lookup, for idempotence.
- **`.status/session_2026-04-20_citation_enrich_processes.md`** — Session report.
- **`.status/citation_gaps_2026-04-20.md`** — Renamed from `citation_gaps_initial_2026-04-20.md` after extension.

### Files for reference (do not modify)
- **`task_details.json`** — Task catalog. Do not touch in this pass.
- **`process_criteria.md`** — Process-side criteria, §5 on references. Confirm your enrichment is consistent with the standards there.
- **`.status/citation_enrichment_thinking_2026-04-20.md`** — Strategy, schema, source order.
- **`OpenAlex/works/fetch_works.py`** — Reference implementation for OpenAlex polite-pool conventions. Copy patterns, don't import.
- **`OpenAlex/pull_openalex.py`** — Reference for host-side script pattern if API access is blocked.

### Derived files (regenerated, do not hand-edit)
- **`task_names.json`**, **`process_task_index.json`**, **`process_task_crossref.md`**, **`file_inventory.md`** — run `outputs/regenerate_derived_files.py`.

---

## Schema notes

Target reference object (after enrichment):

```json
{
  "authors": "Rescorla, R. A., & Wagner, A. R.",
  "year": 1972,
  "title": "A theory of Pavlovian conditioning: ...",
  "venue": "Classical Conditioning II: Current Research and Theory",
  "venue_type": "book_chapter",
  "journal": "Classical Conditioning II",
  "volume": null,
  "issue": null,
  "pages": "64–99",
  "doi": null,
  "openalex_id": "https://openalex.org/W...",
  "pmid": null,
  "citation_string": "Rescorla & Wagner (1972) in *Classical Conditioning II*",
  "source": "openalex",
  "confidence": "high",
  "verified_on": "2026-04-20"
}
```

Rules:

- **Preserve** `journal`, `year`, `citation_string`. These are the user-visible fields and their removal would break anyone reading the JSON today.
- **Add** all other fields. Null is acceptable for fields that don't apply (e.g., `volume` for a book).
- **`venue_type`** must be one of: `journal`, `book`, `book_chapter`, `proceedings`, `report`, `preprint`, `other`. Infer from CrossRef `type` or OpenAlex `type`.
- **`source`** must be one of: `crossref`, `openalex`, `europepmc`, `semanticscholar`, `unresolved`, `historical`.
- **`confidence`** must be one of: `high`, `medium`, `low`, `none`.
- **`verified_on`** is the ISO date the DOI HEAD check succeeded (or the resolution happened for no-DOI refs).

---

## Working conventions

- Clean, readable code. Flat functions, no abstract base classes. One module per responsibility.
- Cache everything. A rerun should cost $0 and be idempotent.
- No emojis in code or markdown unless the user asks.
- Always write a session report to `.status/` when done.
- If you find substantive differences between the original citation_string and the resolved metadata (e.g., the year was wrong, the journal was wrong), document each one in the session report with the correction applied.

---

## Remaining items (NOT part of this task — do not attempt)

These are tracked separately and should not be addressed in this session:

1. **Task reference enrichment + schema migration** — Phase C. See `task_citation_enrich_tasks_instructions.md`. Do not start until the process pass is reviewed.
2. **Paradigm extraction from OpenAlex abstracts** — Separate workstream (`OpenAlex/works/.status/works_step_proposal.md`).
3. **New process discovery** — Only flag in the gaps document; do not add new process rows.
4. **Criteria document updates** — `process_criteria.md` §7.12 can be marked RESOLVED as part of the session report, but do not restructure §5 or other sections.
