# PDF naming and storage — thinking summary

**Date:** 2026-04-21
**Context:** Follow-up to `literature_search_plan_2026-04-21.md`. The user
rejected the earlier `<pub_id>.pdf` filename scheme and specified a
human-readable pattern instead: `name_year_title_id.pdf`. This note
records the design decisions and the one open question.

## The user's requirement, in their words

> I want something like name_year_title_id.pdf — name is the first author
> last name, year is the year of publication, title is the article title
> with no internal spaces or punctuation and with each word capitalized,
> id is the id we are using (some hash maybe). it could be the hash of
> the rest of it. My concern is that when I look at the pdfs I should
> know what they are.

The driver is **recognition at a glance**. When the user opens
`H:\Research\TaskResearch\HED-PDFs\` in Explorer, every filename should
tell them what the paper is without any lookup. The earlier scheme
(`pub_2012_badre_dopa_tics.pdf`) failed that test — `dopa_tics` only
reads as "dopamine, TICS" once you know the convention.

## The scheme

```
<year>\<LastName>_<Year>_<CamelCaseTitle>_<hash8>.pdf
```

Under `H:\Research\TaskResearch\HED-PDFs\`, so full example:

```
H:\Research\TaskResearch\HED-PDFs\2012\Badre_2012_CognitiveControlHierarchyAndTheRostroCaudalOrganizationOfTheFrontalLobes_a3b9f2c1.pdf
```

Full field-construction rules are in the plan, §11.7. The interesting
parts of the design are below.

## Design decisions and why

### 1. PDFs go in a sibling directory, not inside the repo or the Zotero profile

Three candidates were considered:

| Location | Verdict |
|:---|:---|
| Inside the Git repo (`Claude-research/pdfs/`) | No. PDFs are large, often redistribution-restricted, and don't belong in version control. Git-ignoring them still clutters the working tree. |
| Inside the Zotero profile (`Zotero-HED/storage/`) | No. Zotero's default layout is `storage/<8-char-key>/<original-filename>.pdf`, which couples the path to Zotero's internal item keys and makes the PDFs unusable without Zotero. |
| Sibling directory (`HED-PDFs/`) | **Yes.** Decoupled from both version control and Zotero. Any tool can read the tree; Zotero references the files via linked-file attachments. |

The sibling directory also gives us a single place to point Zotero's
"Linked Attachment Base Directory" at, which makes the attachment paths
Zotero stores *relative* rather than absolute — portable if the tree
ever moves.

### 2. Year folders, not publisher folders

One level of `<year>\` bucketing keeps directories browsable (< ~500
files per folder for any realistic year). Publisher folders were
rejected: DOIs drift between publishers after imprint mergers (Elsevier
→ Cell Press within Elsevier, Nature → Springer Nature, etc.), and the
publisher is not a stable organizing key.

### 3. Filename starts with author + year

Explorer sorts alphabetically by default. Starting with `<LastName>_`
gives a free per-year index by author. Starting with `<year>_` would
duplicate the folder name. Starting with `<hash>_` would be unreadable.

### 4. CamelCaseTitle, not spaced or kebab-cased

The user explicitly asked for this. The reasons it works:

- Windows filesystems are case-insensitive but case-preserving, so the
  case just aids reading.
- Removing internal spaces sidesteps shell-quoting and copy-paste
  issues across tools.
- Removing punctuation sidesteps the "what's allowed in a Windows
  filename" question (`:` and `?` are illegal; most others are legal
  but awkward).

Edge rules worth noting in the plan and the implementation:
- ASCII-fold first (Schönberg → Schonberg), so non-Latin diacritics don't
  break file ops.
- Preserve all-caps tokens if length ≥ 2 (keep `fMRI`, `EEG`, `IAPS`,
  `ADHD` intact rather than flattening to `Fmri`, `Eeg`, `Iaps`, `Adhd`).
- Truncate at ≤ 100 chars on a token boundary — no ellipsis, no
  mid-word cuts.

### 5. The id: an 8-hex-char hash of a metadata-only canonical string

The user's wording — "id is the id we are using (some hash maybe). it
could be the hash of the rest of it" — left two options:

**Option A:** keep the semantic pub_id `pub_2012_badre_dopa_tics` and
put it in the filename. Problem: two semantic slugs (the filename's
author/year/title and the pub_id's author/year/topic/venue) overlap
heavily and can drift.

**Option B:** shrink pub_id to `pub_<hash8>`. Use the same 8 hex chars
as the filename's trailing id; semantic metadata lives in exactly one
place (the filename plus the record's structured fields).

**User confirmed Option B, and refined the hash derivation.** My first
draft used a priority cascade `DOI → PMID → metadata`. The user
correctly rejected that: a paper ingested without a DOI would get a
metadata-derived hash, and if we later discovered the DOI the pub_id
would change — cascading to the PDF filename, the Zotero marker, every
`publication_links.json` row, and every reference in the
`_details.json` files. That's the exact failure mode "deterministic"
should prevent.

**Final rule: the hash is computed from metadata alone, always.** The
canonical string is:

```
last_name_lowercased_alphanumeric
+ year_as_4_digits (or "0000" if unknown)
+ title_lowercased_alphanumeric
truncated to 100 chars total
```

Example (Badre 2012):

```
badre2012cognitivecontrolhierarchyandtherostrocaudalorganizationofthefrontallobes
```

→ `pub_id = "pub_" + sha1(canonical).hexdigest()[:8]`

Discovering a DOI later does not change any of these inputs, so the
pub_id is stable for the entire lifecycle of the record. The canonical
string is stored in the record as `canonical_string` so the hash is
auditable ("why does this record have this pub_id?" = one-line check).

**DOI is the dedup key, not the identity key.** When we ingest a new
record, we first try to match against existing records by DOI. DOI
match → reuse the existing pub_id regardless of any metadata drift.
Canonical-string match is a fallback only when neither record has a
DOI.

**Collision math.** 8 hex chars = 32 bits. For ~5000 papers the
birthday-paradox collision probability is < 10⁻⁵. The ingester
explicitly checks for collisions at write time and bumps both
colliding records to 10 hex chars — rare enough that we don't
prematurely optimize for it.

**Correction policy.** If a curator corrects a title or author name
after ingestion, the `title` / `authors` fields are updated but
`canonical_string` and `pub_id` are **not**. Only if the correction is
large enough to make the old pub_id misleading do we mint a new record;
the old pub_id is retained in a `superseded_by` field for provenance.
This is a deliberate manual step, never automatic.

### 6. The hash is deterministic — same paper, same id, any run

Priority order for the input to SHA-1:

1. DOI (lowercased, no URL prefix).
2. PMID prefixed with `pmid:` to separate the namespace from DOI
   collisions.
3. Canonical metadata: `family_lc + "|" + str(year) + "|" + normalized_title`.

This makes the pipeline re-runnable without fear of re-minting pub_ids.
Running the ingest script twice yields identical files, identical
pub_ids, and identical Zotero linked-file paths.

## What this affects elsewhere in the plan

- **§3.2 publication record schema** — `pub_id` redefined; `local_pdf_path`
  example updated.
- **§11.3 PDF storage** — rewritten to point at `HED-PDFs\<year>\`.
- **§11.7 PDF filename scheme (new)** — full rules, edge cases, and
  implementation guardrails.
- **§12 open decisions** — item 4c records the pub_id redesign as the
  one remaining confirmation question.
- **Appendix B.3** — adds the step "Set Zotero's Linked Attachment Base
  Directory to `H:\Research\TaskResearch\HED-PDFs\`".
- **Appendix B.4** — `.zotero_env` gets `HED_PDFS_DIR`.
- **Appendix C** — captures the PDF and pub_id decisions.

Phase 7 (full-text acquisition) was updated to call
`build_pdf_filename(record)` rather than assemble a path inline — one
pure function, one source of truth for the filename format.

## Resolved open questions

- `pub_id = pub_<hash8>` — **confirmed 2026-04-21.**
- Hash input = metadata-only canonical string (not DOI-prioritized) —
  **confirmed 2026-04-21**, with the explicit property that discovering
  a DOI after record creation does not change the pub_id.
- `canonical_string` added as a stored field on the publication record
  — **confirmed 2026-04-21**.

No open questions specific to PDF naming or pub_id remain. The list in
§12 of the main plan still carries the non-PDF open items (landmark list
expansion, venue tier review, triage policy for historical refs).

## What I deliberately did not do

- Did not start implementing `identity.py` (`build_canonical_string`,
  `build_pub_id`, `build_pdf_filename`). The plan is a planning
  document; code waits for the overall execution phase.
- Did not touch `process_details.json` or `task_details.json`.
- Did not create `HED-PDFs\` on disk — that's a one-line setup step
  for the user (or a setup script once we start execution).
- Did not propose an automated renamer for the existing PDF-free
  catalog; there is nothing to rename yet.
