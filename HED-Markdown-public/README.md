# HED-Markdown-public

This directory holds **redistributable** Markdown derivatives of
publications referenced from the HED catalog.  Files here are
committed to the public repository.

## What lands here

Only Markdown files whose `license` field in
`Claude-research/process_details.json` /
`Claude-research/task_details.json` is in the project's allowlist
of redistributable licences:

  `cc-by`, `cc-by-sa`, `cc0`, `public-domain`

(The allowlist is defined in
`Claude-research/code/literature_search/license_policy.py` as
`PUBLISHABLE_LICENSES`.  Anything else is excluded by policy.)

A Markdown lands here *only* via the explicit "publish" step —
never as a side-effect of acquisition or conversion.  Acquisition
always writes first to `HED-Markdown-private/` (which is
gitignored).  The publish step re-checks the licence at promotion
time and refuses to copy non-publishable files.

## What does NOT land here

- PDFs — those live in `HED-PDFs/` (gitignored, always private).
- Markdown derived from a paywalled publisher PDF, even when the
  same paper has an OA preprint with a redistributable licence
  elsewhere.  The licence travels with the *bytes*, not with the
  *paper* — see `.status/plan_2026-05-19_rec1_v2.md` §1.
- Markdown derived from publisher-TDM-token URLs (Elsevier, Wiley,
  Springer).  Those tokens explicitly forbid redistribution.
- CC-BY-NC family content by default.  HED is non-commercial in
  spirit, but the boundary is contested; CC-BY-NC overrides are
  per-decision and recorded in `.status/license_overrides.md`.

## How files get here

There is no automated "everything OA goes public" sweep.  Each file
arrives via an explicit human action: the `publish_markdown.py`
command (PR-E, future) copies a file from `HED-Markdown-private/`
here only after:

1. Confirming the source `pdf_locations[]` entry has a licence in
   `PUBLISHABLE_LICENSES`.
2. Confirming the `local_artifacts.markdown.license` reflects that
   same licence (i.e. the conversion didn't accidentally derive from
   the wrong source).
3. Recording the promotion in the catalog and writing a session note.

## File naming

Same convention as `HED-PDFs/`:

```
<LastName>_<Year>_<CamelCaseTitle>_<hash8>.md
```

The `<hash8>` is the same one used in `pub_id` (the first 8 hex chars
of SHA-1 over canonical metadata; see
`Claude-research/code/literature_search/identity.py`), so the
filename and the `pub_id` are mechanically linked.
