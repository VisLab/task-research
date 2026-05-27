"""
acquire — Auto-acquisition orchestrator for PDFs and Markdowns.

PR-E (auto-acquisition pipeline) lives in this package.  Two CLIs sit
on top of a shared core:

    acquire_pdf.py        Walk pdf_locations[] in priority order, fetch the
                          first OA PDF that responds with application/pdf,
                          stamp licence, file under HED-PDFs/.
                          (PR-E session 2 — not yet written.)

    acquire_markdown.py   For each ref, try PMC BioC first (if ids.pmcid set),
                          else convert an existing PDF via marker-pdf.  File
                          publishable Markdown under HED-Markdown-public/,
                          everything else under HED-Markdown-private/.
                          (PR-E session 3 — not yet written.)

Both lean on:

    core.py               Catalog walk, idempotency, success/failure recording.
    priority.py           Pure ordering of pdf_locations[] entries.

POC reference set (D-E3, locked 2026-05-27 — see
`.status/pr_e_execution_2026-05-26.md` §11):

    Fleming & Lau 2014   gold OA + PMC + CC-BY (PMC-BioC fast path)
    Salamone et al. 2007 green OA, no PMC      (repository walk)
    Daw et al. 2005      closed                (failure-record path)

Identified by DOI; PR-E's POC list is distinct from the process-id-
based POC used by enrich_*.py.  See D-E3 rationale.
"""

# POC reference DOIs — these three exercise the three operationally
# distinct paths through priority.py and core.py.  Lower-cased and
# stripped to match cache keys.
POC_REF_DOIS: tuple[str, ...] = (
    "10.3389/fnhum.2014.00443",   # Fleming & Lau 2014  (gold, PMC4097944, cc-by)
    "10.1007/s00213-006-0668-9",  # Salamone et al. 2007 (green, no PMC)
    "10.1038/nn1560",             # Daw, Niv & Dayan 2005 (closed, no PMC)
)
