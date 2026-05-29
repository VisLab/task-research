#!/usr/bin/env python3
"""
acquire_markdown.py — Auto-acquisition orchestrator for Markdown.

For each reference in scope, derives a Markdown rendering of the paper
and files it under ``HED-Markdown-{public,private}/``.  Two paths:

  1. **PMC BioC fast path.**  When ``ref["ids"]["pmcid"]`` is set,
     fetch the structured BioC JSON from PMC's BioC REST endpoint
     (via ``clients/pmc.py:lookup_by_pmcid``) and render Markdown
     directly from it (via ``vendored/opencite/pmc_convert.py:
     bioc_to_markdown``).  Cheap (in-process, no ML), preferred when
     available.

  2. **marker-pdf PDF fallback.**  When no PMC BioC is available and
     the ref carries a successful ``local_artifacts.pdf.path`` (placed
     by ``acquire_pdf.py``), convert that PDF to Markdown via
     ``convert.convert_pdf`` (marker-pdf, ML, heavyweight).

Licence handling — per the plan v2 §4 D5 amendment locked
2026-05-28:

  *  BioC path  : prefer ``documents[0].infons["license"]``; fall back
                  to the ``pmc``-classified entry of ``pdf_locations[]``;
                  finally ``"unknown"``.  The PMC copy ships the
                  authoritative licence; the discovery layer's stamp is
                  the secondary source.
  *  PDF path   : inherit ``ref.local_artifacts.pdf.license``.  A
                  derivative artifact does not change the licence on
                  the underlying bytes.

  The licence stamp drives ``license_policy.is_publishable`` which in
  turn routes the file to ``HED-Markdown-public/`` (publishable) or
  ``HED-Markdown-private/`` (everything else) via
  ``core.artifact_dir(..., is_publishable=...)``.  The directory is a
  cache of the catalog's ``is_publishable`` field, not a second source
  of truth.

Image handling deferred (plan v2 §13, locked 2026-05-27): both
converters reference images by filename only; the bytes are not
fetched.  The produced Markdown will carry unresolved image links until
the §13 follow-up PR ships.

Three modes for scope, mirroring ``acquire_pdf.py``:

  ``--mode poc``     Walk the three D-E3 POC DOIs declared in
                     :data:`acquire.POC_REF_DOIS`.
  ``--mode single``  Walk references owned by the comma-separated
                     IDs given in ``--ids``.
  ``--mode full``    Walk every reference in both catalog files.

Default behaviour is **dry-run**: prints the planned action for each
ref without touching the network, the disk, or the catalog.  Pass
``--write`` to actually fetch, render, save, and persist.

``--bioc-only`` (DQ-9, locked 2026-05-28): restrict the run to the
PMC BioC fast path.  Refs without ``ids.pmcid`` are skipped (not
counted as failures — they're out of scope for the run).  Refs with
a PMCID whose BioC lookup fails are recorded as failures (the PMC
route was tried).

Idempotency, ``--force``, ``--retry-failed`` match ``acquire_pdf.py``.

Usage (run from the workspace root, ``Claude-research/``)::

    # Dry-run on the three POC refs:
    python code/literature_search/acquire/acquire_markdown.py --mode poc

    # Wet-run on the POC trio:
    python code/literature_search/acquire/acquire_markdown.py \\
        --mode poc --write

    # Only the PMC fast path (skips refs without a pmcid):
    python code/literature_search/acquire/acquire_markdown.py \\
        --mode full --bioc-only --write

Exit codes:
    0 — clean (dry-run, or wet-run completed)
    1 — data issue (catalog parse / count mismatch)
    2 — file not found
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

# Make sibling modules importable when invoked as a script.
_HERE = Path(__file__).resolve().parent          # …/acquire
_PARENT = _HERE.parent                            # …/literature_search
for p in (_HERE, _PARENT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

# Local package imports.
from __init__ import POC_REF_DOIS  # noqa: E402

from core import (  # noqa: E402
    artifact_dir,
    canonical_artifact_filename,
    has_recorded_failure,
    iter_refs,
    record_failure,
    record_success,
    resolve_cache_dir,
    should_skip,
)
from priority import classify_url  # noqa: E402

# Sibling-module imports (live in literature_search/).
from clients.pmc import lookup_by_pmcid  # noqa: E402
from convert import convert_pdf  # noqa: E402
from license_policy import is_publishable, normalise_license  # noqa: E402
from vendored.opencite.pmc_convert import bioc_to_markdown  # noqa: E402


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Per-attempt result
# ---------------------------------------------------------------------------

@dataclass
class AttemptResult:
    """Outcome of trying to acquire one ref's Markdown.

    ``kind`` discriminates five shapes:

      ``"success"``           A Markdown landed on disk; ``dest_path``,
                              ``source_url``, ``source_type``,
                              ``converter``, ``license_norm``, and
                              ``is_publishable_flag`` are populated.
      ``"failure"``           No Markdown landed.  ``tried`` lists the
                              routes attempted; ``reason`` is a
                              human-readable summary.
      ``"would_walk"``        Dry-run only: ``plan`` describes the path
                              the wet-run would attempt.
      ``"skipped_no_pmcid"``  ``--bioc-only`` mode encountered a ref
                              without a PMCID.  Not a failure; the ref
                              is out of scope for the run.
    """
    kind: str
    # success
    dest_path: Path | None = None
    source_url: str = ""
    source_type: str = ""
    converter: str = ""
    license_norm: str = "unknown"
    is_publishable_flag: bool = False
    # failure
    tried: list[str] | None = None
    reason: str = ""
    # would_walk (dry-run)
    plan: str = ""


# ---------------------------------------------------------------------------
# Catalog I/O (staged-write convention, mirrors acquire_pdf.py)
# ---------------------------------------------------------------------------

def _load_catalog(workspace: Path) -> tuple[dict, list, Path, Path]:
    p_path = workspace / "process_details.json"
    t_path = workspace / "task_details.json"
    for path in (p_path, t_path):
        if not path.exists():
            raise FileNotFoundError(path)
    with p_path.open("r", encoding="utf-8") as f:
        processes = json.load(f)
    with t_path.open("r", encoding="utf-8") as f:
        tasks = json.load(f)
    return processes, tasks, p_path, t_path


def _save_catalog(
    processes: dict,
    tasks: list,
    p_path: Path,
    t_path: Path,
    *,
    workspace: Path,
) -> None:
    """Stage to ``.scratch/acquire_markdown/`` then copy into place.

    Same convention as ``acquire_pdf.py`` and the wider catalog-writing
    pattern (per CLAUDE.md "Core data files — handling rules").  The
    staged copy is left on disk after the run for diff/inspection.
    """
    scratch = workspace / ".scratch" / "acquire_markdown"
    scratch.mkdir(parents=True, exist_ok=True)
    staged_p = scratch / p_path.name
    staged_t = scratch / t_path.name
    with staged_p.open("w", encoding="utf-8") as f:
        json.dump(processes, f, indent=2, ensure_ascii=False)
        f.write("\n")
    with staged_t.open("w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)
        f.write("\n")
    shutil.copyfile(staged_p, p_path)
    shutil.copyfile(staged_t, t_path)


# ---------------------------------------------------------------------------
# Licence sourcing for the BioC path
# ---------------------------------------------------------------------------

def _license_for_bioc(bioc: dict, ref: dict) -> str:
    """Return the normalised licence stamp for a BioC-derived Markdown.

    Priority (locked 2026-05-28, plan v2 §4 D5 amendment):

      1. BioC document ``infons["license"]`` — authoritative; ships
         from PMC itself rather than from the discovery layer.
      2. The ``pmc``-classified entry of ``ref["pdf_locations"]`` —
         OpenAlex / Unpaywall / S2's read of the PMC copy.
      3. ``"unknown"`` — neither source carried a licence.

    ``normalise_license`` is applied to whichever raw value wins.
    """
    docs = bioc.get("documents") or []
    if docs and isinstance(docs[0], dict):
        infons = docs[0].get("infons") or {}
        raw = infons.get("license")
        if isinstance(raw, str) and raw.strip():
            return normalise_license(raw)

    for loc in ref.get("pdf_locations") or []:
        if not isinstance(loc, dict):
            continue
        if classify_url(loc.get("url")) != "pmc":
            continue
        raw = loc.get("license")
        if isinstance(raw, str) and raw.strip():
            return normalise_license(raw)

    return "unknown"


def _pmc_landing_url(bioc: dict, fallback_pmcid: str) -> str:
    """Compose the canonical PMC landing URL for ``source_url``.

    Prefers the BioC client's ``_pmcid`` annotation (canonical form)
    over the input string.  The landing URL is what a human-reviewing
    maintainer would click; the BioC REST endpoint is internal
    infrastructure and less useful in the catalog.
    """
    pmcid = bioc.get("_pmcid") or fallback_pmcid or ""
    pmcid = pmcid.strip()
    if not pmcid:
        return ""
    return f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/"


# ---------------------------------------------------------------------------
# Mockable callables (production defaults wired to the real modules)
# ---------------------------------------------------------------------------

LookupFn = Callable[[str, Path], "dict | None"]
BiocFn   = Callable[[dict], str]
ConvertFn = Callable[[str], str]


# ---------------------------------------------------------------------------
# Per-ref attempt
# ---------------------------------------------------------------------------

def _file_markdown(
    *,
    ref: dict,
    repo_root: Path,
    md_text: str,
    source_url: str,
    source_type: str,
    converter: str,
    license_norm: str,
) -> AttemptResult:
    """Write ``md_text`` to disk and return a success ``AttemptResult``.

    Routes to ``HED-Markdown-public/`` or ``HED-Markdown-private/``
    based on ``is_publishable(license_norm)`` (plan v2 §4 D5
    amendment).  Filename is canonical per ``identity.build_pdf_filename``
    with a ``.md`` extension so the PDF and Markdown for the same
    paper collate together.
    """
    is_pub = is_publishable(license_norm)
    dest_dir = artifact_dir(repo_root, "markdown", is_publishable=is_pub)
    dest_dir.mkdir(parents=True, exist_ok=True)
    filename = canonical_artifact_filename(ref, "markdown")
    dest_path = dest_dir / filename
    dest_path.write_text(md_text, encoding="utf-8")
    return AttemptResult(
        kind="success",
        dest_path=dest_path,
        source_url=source_url,
        source_type=source_type,
        converter=converter,
        license_norm=license_norm,
        is_publishable_flag=is_pub,
    )


def attempt_one_ref(
    ref: dict,
    *,
    repo_root: Path,
    write: bool,
    bioc_only: bool,
    cache_dir: Path,
    lookup_fn: LookupFn = lookup_by_pmcid,
    bioc_fn: BiocFn = bioc_to_markdown,
    convert_fn: ConvertFn = convert_pdf,
) -> AttemptResult:
    """Top-level per-ref entry point.

    Wet-run logic (locked 2026-05-28; see DQ-9 + plan v2 §4 D5
    amendment):

      1.  If ``ids.pmcid`` is set: call ``lookup_fn``.  On a non-empty
          BioC document, render to Markdown via ``bioc_fn``, file
          under ``HED-Markdown-public/`` or ``HED-Markdown-private/``
          per the BioC licence (or the PMC ``pdf_locations`` entry as
          fallback), and return success.
      2.  If ``--bioc-only`` and the BioC route did not succeed:
          *  PMCID missing -> ``skipped_no_pmcid`` (not a failure)
          *  PMC lookup failed -> ``failure`` with ``tried=["pmc_bioc"]``
      3.  Else fall through to the PDF fallback: if
          ``local_artifacts.pdf.path`` is a non-empty string, convert
          the on-disk PDF via ``convert_fn`` and file the Markdown.
          Licence inherits from ``local_artifacts.pdf.license``.
      4.  If neither route is usable, record failure with whatever
          ``tried`` list was accumulated (``[]`` if no PMCID and no
          PDF; ``["pmc_bioc"]`` if PMC was attempted but failed).

    Dry-run (``write=False``) returns a ``would_walk`` result without
    touching the network or the disk.
    """
    ids = ref.get("ids") or {}
    pmcid_raw = ids.get("pmcid")
    pdf_block = (ref.get("local_artifacts") or {}).get("pdf") or {}
    pdf_path_str = pdf_block.get("path")

    has_pmcid = isinstance(pmcid_raw, str) and bool(pmcid_raw.strip())
    has_pdf   = isinstance(pdf_path_str, str) and bool(pdf_path_str.strip())

    # ---- Dry-run: describe the wet-run plan without acting.
    if not write:
        return AttemptResult(kind="would_walk",
                             plan=_dry_run_plan(has_pmcid, has_pdf, bioc_only))

    tried: list[str] = []
    notes: list[str] = []

    # ---- Step 1: PMC BioC fast path.
    if has_pmcid:
        bioc = lookup_fn(pmcid_raw, cache_dir)
        if bioc and isinstance(bioc, dict) and bioc.get("documents"):
            try:
                md_text = bioc_fn(bioc["documents"][0])
            except Exception as exc:  # defensive — converter is in-process
                tried.append("pmc_bioc")
                notes.append(f"pmc_bioc: render raised {type(exc).__name__}: {exc}")
            else:
                license_norm = _license_for_bioc(bioc, ref)
                source_url = _pmc_landing_url(bioc, pmcid_raw)
                return _file_markdown(
                    ref=ref, repo_root=repo_root, md_text=md_text,
                    source_url=source_url,
                    source_type="auto_pmc_bioc",
                    converter="pmc_bioc",
                    license_norm=license_norm,
                )
        else:
            tried.append("pmc_bioc")
            notes.append("pmc_bioc: no BioC document available "
                         "(not in PMC OA subset, or transient error)")

    # ---- Step 2: --bioc-only short-circuit.
    if bioc_only:
        if not has_pmcid:
            return AttemptResult(kind="skipped_no_pmcid")
        # PMC was attempted and failed; do not fall through.
        return AttemptResult(
            kind="failure",
            tried=tried or ["pmc_bioc"],
            reason="; ".join(notes) if notes else "pmc_bioc unavailable",
        )

    # ---- Step 3: PDF fallback.
    if has_pdf:
        pdf_full_path = repo_root / pdf_path_str
        tried.append("marker-pdf")
        try:
            md_text = convert_fn(str(pdf_full_path))
        except ImportError as exc:
            # marker-pdf not installed.  Record as a per-ref failure
            # so the maintainer sees the gap in the catalog; remaining
            # PDF-fallback refs in the run will fail the same way.
            notes.append(f"marker-pdf: not installed ({exc})")
            return AttemptResult(
                kind="failure", tried=tried, reason="; ".join(notes),
            )
        except FileNotFoundError as exc:
            notes.append(f"marker-pdf: PDF missing on disk ({exc})")
            return AttemptResult(
                kind="failure", tried=tried, reason="; ".join(notes),
            )
        except Exception as exc:  # defensive — covers marker runtime errors
            notes.append(f"marker-pdf: {type(exc).__name__}: {exc}")
            return AttemptResult(
                kind="failure", tried=tried, reason="; ".join(notes),
            )

        # Markdown derived from a PDF inherits the PDF's licence stamp.
        license_norm = normalise_license(pdf_block.get("license"))
        source_url = pdf_block.get("source_url") or ""
        return _file_markdown(
            ref=ref, repo_root=repo_root, md_text=md_text,
            source_url=source_url,
            source_type="auto_markdown_from_pdf",
            converter="marker-pdf",
            license_norm=license_norm,
        )

    # ---- Step 4: nothing to try.
    reason = "; ".join(notes) if notes else "no PMC and no on-disk PDF"
    return AttemptResult(kind="failure", tried=tried, reason=reason)


def _dry_run_plan(has_pmcid: bool, has_pdf: bool, bioc_only: bool) -> str:
    """One-line description of the wet-run plan for ``attempt_one_ref``."""
    if has_pmcid and bioc_only:
        return "would try: pmc_bioc"
    if has_pmcid and has_pdf:
        return "would try: pmc_bioc -> marker-pdf (PDF on disk)"
    if has_pmcid:
        return "would try: pmc_bioc (no PDF on disk for fallback)"
    if bioc_only:
        return "would skip: no pmcid (bioc-only mode)"
    if has_pdf:
        return "would try: marker-pdf (no pmcid)"
    return "would record failure: no PMC and no on-disk PDF"


# ---------------------------------------------------------------------------
# CLI driver
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode", choices=["poc", "single", "full"], required=True,
                   help="poc=D-E3 POC DOIs, single=--ids, full=every ref.")
    p.add_argument("--ids", default="",
                   help="Comma-separated owner IDs for --mode single.")
    p.add_argument("--workspace", default=".",
                   help="Workspace root (Claude-research/).  Default: cwd.")
    p.add_argument("--cache-dir", default="<auto>",
                   help="PMC BioC cache root.  Resolves via "
                        "--cache-dir > $HED_CACHE_DIR > <workspace>/outputs/cache.")
    p.add_argument("--write", action="store_true",
                   help="Fetch BioC, run converters, save Markdown, "
                        "persist catalog.  Default is dry-run (plan only).")
    p.add_argument("--force", action="store_true",
                   help="Re-acquire refs with an existing successful Markdown.")
    p.add_argument("--retry-failed", action="store_true",
                   help="Include refs with a recorded failure record.  "
                        "Default skips them to keep re-runs fast.")
    p.add_argument("--bioc-only", action="store_true",
                   help="Restrict to the PMC BioC fast path.  Refs without "
                        "ids.pmcid are skipped (not failure-recorded); refs "
                        "whose BioC lookup fails are recorded as failures.")
    p.add_argument("--limit", type=int, default=0,
                   help="Cap on number of refs processed (0 = no cap).")
    p.add_argument("--verbose", "-v", action="store_true")
    return p.parse_args(argv)


def main(
    argv: list[str] | None = None,
    *,
    lookup_fn: LookupFn | None = None,
    bioc_fn: BiocFn | None = None,
    convert_fn: ConvertFn | None = None,
) -> int:
    """CLI entry point.

    The three ``*_fn`` kwargs are programmatic injection points for
    tests; production callers omit them and the real
    ``lookup_by_pmcid`` / ``bioc_to_markdown`` / ``convert_pdf`` are
    used.  Captured here (not as ``attempt_one_ref`` defaults) because
    Python evaluates default args at definition time, making it
    impossible for tests to swap them otherwise.
    """
    args = _parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    lookup_callable: LookupFn = lookup_fn if lookup_fn is not None else lookup_by_pmcid
    bioc_callable:   BiocFn   = bioc_fn   if bioc_fn   is not None else bioc_to_markdown
    convert_callable: ConvertFn = convert_fn if convert_fn is not None else convert_pdf

    ws = Path(args.workspace).resolve()
    repo_root = ws.parent
    cache_dir = resolve_cache_dir(args.cache_dir, ws)

    logger.info("workspace : %s", ws)
    logger.info("repo_root : %s", repo_root)
    logger.info("cache_dir : %s", cache_dir)
    logger.info("mode      : %s  write=%s  bioc-only=%s  "
                "force=%s  retry-failed=%s",
                args.mode, args.write, args.bioc_only,
                args.force, args.retry_failed)

    try:
        processes, tasks, p_path, t_path = _load_catalog(ws)
    except FileNotFoundError as exc:
        logger.error("catalog file missing: %s", exc)
        return 2

    ids = [i.strip() for i in args.ids.split(",") if i.strip()]

    # Counters.
    n_in_scope = 0
    n_skipped_done = 0
    n_skipped_prior_failure = 0
    n_skipped_no_pmcid = 0
    n_success = 0
    n_failure = 0
    n_dryrun = 0
    n_capped = 0

    for owner_id, ref_idx, ref in iter_refs(
        processes, tasks,
        mode=args.mode, ids=ids, poc_dois=POC_REF_DOIS,
    ):
        n_in_scope += 1

        if should_skip(ref, "markdown", force=args.force):
            n_skipped_done += 1
            continue
        if (has_recorded_failure(ref, "markdown")
                and not args.retry_failed and not args.force):
            n_skipped_prior_failure += 1
            continue
        if args.limit and (n_success + n_failure + n_dryrun) >= args.limit:
            n_capped += 1
            continue

        outcome = attempt_one_ref(
            ref,
            repo_root=repo_root,
            write=args.write,
            bioc_only=args.bioc_only,
            cache_dir=cache_dir,
            lookup_fn=lookup_callable,
            bioc_fn=bioc_callable,
            convert_fn=convert_callable,
        )

        label = f"[{owner_id}#{ref_idx}]"

        if outcome.kind == "would_walk":
            n_dryrun += 1
            print(f"  {label} {outcome.plan}")

        elif outcome.kind == "skipped_no_pmcid":
            n_skipped_no_pmcid += 1
            print(f"  {label} SKIP no pmcid (bioc-only mode)")

        elif outcome.kind == "success":
            n_success += 1
            assert outcome.dest_path is not None
            rel_path = f"{outcome.dest_path.parent.name}/{outcome.dest_path.name}"
            record_success(
                ref, "markdown",
                path=rel_path,
                source_url=outcome.source_url,
                source_type=outcome.source_type,
                license=outcome.license_norm,
                converter=outcome.converter,
                is_publishable=outcome.is_publishable_flag,
            )
            print(f"  {label} OK  saved {outcome.dest_path.parent.name}/"
                  f"{outcome.dest_path.name} "
                  f"(converter={outcome.converter}, "
                  f"licence={outcome.license_norm}, "
                  f"publishable={outcome.is_publishable_flag})")

        elif outcome.kind == "failure":
            n_failure += 1
            tried = outcome.tried or []
            record_failure(ref, "markdown", tried=tried, reason=outcome.reason)
            print(f"  {label} FAIL tried={tried}  reason={outcome.reason}")

        else:  # pragma: no cover - defensive
            logger.error("unknown attempt outcome kind: %r", outcome.kind)

    # ---- Summary
    print()
    print("Acquisition summary:")
    print(f"  in scope                  : {n_in_scope}")
    print(f"  skipped (already done)    : {n_skipped_done}")
    print(f"  skipped (prior failure)   : {n_skipped_prior_failure}")
    if args.bioc_only:
        print(f"  skipped (no pmcid)        : {n_skipped_no_pmcid}")
    if not args.write:
        print(f"  dry-run plans             : {n_dryrun}")
    else:
        print(f"  acquired (Markdown saved) : {n_success}")
        print(f"  failed (recorded)         : {n_failure}")
    if n_capped:
        print(f"  skipped (--limit cap)     : {n_capped}")

    # ---- Persist
    if args.write:
        _save_catalog(processes, tasks, p_path, t_path, workspace=ws)
        print()
        print(f"wrote: {p_path.name}")
        print(f"wrote: {t_path.name}")
    else:
        print()
        print("dry-run complete; pass --write to fetch + render + save + persist.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "AttemptResult",
    "attempt_one_ref",
    "main",
]
