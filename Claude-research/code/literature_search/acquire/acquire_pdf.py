#!/usr/bin/env python3
"""
acquire_pdf.py — Auto-acquisition orchestrator for PDFs.

For each reference in scope, walks ``ref["pdf_locations"]`` in
priority order (per :mod:`priority`), fetches each candidate URL
(via :mod:`fetch`), and saves the first response whose body sniffs as
``application/pdf`` to ``HED-PDFs/<canonical>.pdf``.  On success,
stamps ``ref["local_artifacts"]["pdf"]`` via :func:`core.record_success`;
on total failure (no candidate produced a PDF, or there were no
candidates at all) stamps it via :func:`core.record_failure`.

Three modes for scope, mirroring ``enrich_pdf_locations.py``:

  ``--mode poc``     Walk the three D-E3 POC DOIs declared in
                     :data:`acquire.POC_REF_DOIS`.
  ``--mode single``  Walk references owned by the comma-separated
                     IDs given in ``--ids``.
  ``--mode full``    Walk every reference in both catalog files.

Default behaviour is **dry-run**: prints the planned walk for each ref
without touching the network, the disk, or the catalog.  Pass
``--write`` to actually fetch, save, and persist.

Idempotency:

  Default                        skip refs with a successful prior
                                 acquisition (``should_skip``) and refs
                                 carrying a recorded failure
                                 (``has_recorded_failure``).
  ``--retry-failed``             include refs with a recorded failure.
  ``--force``                    include refs with a successful
                                 acquisition (re-acquires).

Per D-E5 (locked 2026-05-27), PR-E never re-calls OpenAlex / Unpaywall
/ Semantic Scholar.  Every URL fetched here comes from
``ref["pdf_locations"]`` as populated by PR-D's
``enrich_pdf_locations.py``.

Usage (run from the workspace root, ``Claude-research/``)::

    # Dry-run on the three POC refs:
    python code/literature_search/acquire/acquire_pdf.py --mode poc

    # Wet-run on a single process's refs:
    python code/literature_search/acquire/acquire_pdf.py \\
        --mode single --ids hed_response_inhibition --write

    # Full-catalog acquisition, retrying prior failures:
    python code/literature_search/acquire/acquire_pdf.py \\
        --mode full --retry-failed --write

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
from typing import Callable, Sequence

# Make sibling modules importable when invoked as a script.
_HERE = Path(__file__).resolve().parent          # …/acquire
_PARENT = _HERE.parent                            # …/literature_search
for p in (_HERE, _PARENT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

# Local package imports.
from __init__ import POC_REF_DOIS  # noqa: E402

from core import (  # noqa: E402
    ArtifactKind,
    artifact_dir,
    canonical_artifact_filename,
    has_recorded_failure,
    iter_refs,
    record_failure,
    record_success,
    should_skip,
)
from fetch import FetchResult, fetch_bytes  # noqa: E402
from priority import walk_locations  # noqa: E402

# Sibling-module imports (live in literature_search/).
from license_policy import is_publishable, normalise_license  # noqa: E402


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Per-attempt result
# ---------------------------------------------------------------------------

@dataclass
class AttemptResult:
    """Outcome of trying to acquire one ref's PDF.

    ``kind`` discriminates the three shapes:

      ``"success"``    A PDF landed on disk; ``dest_path``,
                       ``source_url``, ``source_tag`` and
                       ``license_norm`` are populated.
      ``"failure"``    No PDF landed.  ``tried`` lists the source tags
                       walked; ``reason`` is a human-readable summary.
      ``"would_walk"`` Dry-run only: ``candidates`` is the
                       priority-ordered list that *would* be tried.
    """
    kind: str
    candidates: list[dict] | None = None       # would_walk
    dest_path: Path | None = None              # success
    source_url: str = ""                       # success
    source_tag: str = ""                       # success (e.g. "openalex,unpaywall")
    license_norm: str = "unknown"              # success
    tried: list[str] | None = None             # failure
    reason: str = ""                           # failure


# ---------------------------------------------------------------------------
# Catalog I/O (staged-write convention, mirrors enrich_pdf_locations.py)
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
    """Stage to ``.scratch/acquire_pdf/`` then copy into place.

    Same convention as ``enrich_pdf_locations.py`` (per CLAUDE.md
    "Core data files — handling rules").  The staged copy is left on
    disk after the run for diff/inspection.
    """
    scratch = workspace / ".scratch" / "acquire_pdf"
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
# Single-ref attempt
# ---------------------------------------------------------------------------

# The fetch function is parameterised so tests can inject a fake.
# Production callers leave it as the default.
FetchFn = Callable[..., FetchResult]


def _plan_walk(ref: dict, *, allow_paywalled: bool) -> list[dict]:
    """Return the priority-ordered list of candidate locations for ``ref``.

    Wrapper around :func:`priority.walk_locations` so the dry-run
    output and the wet-run loop see the same list.
    """
    return walk_locations(ref.get("pdf_locations"), allow_paywalled=allow_paywalled)


def _attempt_walk(
    ref: dict,
    candidates: Sequence[dict],
    *,
    repo_root: Path,
    fetch_fn: FetchFn,
    timeout: float,
    max_bytes: int,
    host_throttle_sec: float,
) -> AttemptResult:
    """Walk ``candidates`` until one returns PDF bytes; save and return.

    On total exhaustion (or on an empty candidate list) returns a
    failure result with ``tried`` and ``reason`` populated for
    :func:`core.record_failure`.  Per PRE-E2-Q1 (resolved by maintainer
    2026-05-27 — record), an empty candidate list is a recorded
    failure with ``tried=[]`` and ``reason="no candidate locations"``.
    """
    if not candidates:
        return AttemptResult(kind="failure", tried=[], reason="no candidate locations")

    tried: list[str] = []
    notes: list[str] = []

    for loc in candidates:
        url = loc.get("url") or ""
        source_tag = loc.get("source") or "unknown"
        tried.append(source_tag)

        result = fetch_fn(
            url,
            timeout=timeout,
            max_bytes=max_bytes,
            host_throttle_sec=host_throttle_sec,
        )

        if result.error:
            notes.append(f"{source_tag}: {result.error}")
            continue
        if result.status != 200:
            notes.append(f"{source_tag}: HTTP {result.status}")
            continue
        if not result.is_pdf():
            notes.append(f"{source_tag}: not PDF ({result.content_type or 'no content-type'})")
            continue

        # Got PDF bytes.  Save to HED-PDFs/<canonical>.pdf.
        dest_dir = artifact_dir(repo_root, "pdf")
        dest_dir.mkdir(parents=True, exist_ok=True)
        filename = canonical_artifact_filename(ref, "pdf")
        dest_path = dest_dir / filename
        dest_path.write_bytes(result.body)

        return AttemptResult(
            kind="success",
            dest_path=dest_path,
            source_url=result.url or url,
            source_tag=source_tag,
            license_norm=normalise_license(loc.get("license")),
        )

    reason = "; ".join(notes) if notes else "all candidates exhausted"
    return AttemptResult(kind="failure", tried=tried, reason=reason)


def attempt_one_ref(
    ref: dict,
    *,
    repo_root: Path,
    write: bool,
    allow_paywalled: bool,
    fetch_fn: FetchFn = fetch_bytes,
    timeout: float = 30.0,
    max_bytes: int = 50 * 1024 * 1024,
    host_throttle_sec: float = 1.0,
) -> AttemptResult:
    """Top-level per-ref entry point.

    Dry-run (``write=False``) returns a ``"would_walk"`` result with
    the priority-ordered candidates; no network, no disk.

    Wet-run (``write=True``) calls :func:`_attempt_walk`.
    """
    candidates = _plan_walk(ref, allow_paywalled=allow_paywalled)
    if not write:
        return AttemptResult(kind="would_walk", candidates=list(candidates))
    return _attempt_walk(
        ref, candidates,
        repo_root=repo_root,
        fetch_fn=fetch_fn,
        timeout=timeout,
        max_bytes=max_bytes,
        host_throttle_sec=host_throttle_sec,
    )


# ---------------------------------------------------------------------------
# Source-type stamp
# ---------------------------------------------------------------------------

def _source_type_for(source_tag: str) -> str:
    """Compose the ``source_type`` value stored on the catalog entry.

    ``source_tag`` arrives from ``pdf_locations[i]["source"]`` and may
    be a single source name (``"openalex"``) or a comma-joined list
    when PR-D's merge unioned two sources for the same URL
    (``"openalex,unpaywall"``).  The full string is preserved with an
    ``"auto_"`` prefix so the catalog records both the route and the
    automation provenance.  The free-form schema description allows
    this exactly.
    """
    tag = (source_tag or "unknown").strip() or "unknown"
    return f"auto_{tag}"


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
    p.add_argument("--write", action="store_true",
                   help="Fetch bytes, save PDFs, persist catalog.  "
                        "Default is dry-run (print planned walk only).")
    p.add_argument("--force", action="store_true",
                   help="Re-acquire refs with an existing successful PDF.")
    p.add_argument("--retry-failed", action="store_true",
                   help="Include refs with a recorded failure record.  "
                        "Default skips them to keep re-runs fast.")
    p.add_argument("--allow-paywalled", action="store_true",
                   help="Pass through to walk_locations: include "
                        "candidates whose licence is 'proprietary'.")
    p.add_argument("--limit", type=int, default=0,
                   help="Cap on number of refs processed (0 = no cap).")
    p.add_argument("--timeout", type=float, default=30.0,
                   help="Per-request HTTP timeout in seconds.")
    p.add_argument("--max-bytes", type=int, default=50 * 1024 * 1024,
                   help="Max response body size in bytes.")
    p.add_argument("--host-throttle-sec", type=float, default=1.0,
                   help="Minimum gap between same-host requests.")
    p.add_argument("--verbose", "-v", action="store_true")
    return p.parse_args(argv)


def _format_candidate_line(loc: dict) -> str:
    """One-line summary for dry-run output."""
    src = (loc.get("source") or "unknown")[:24]
    ver = (loc.get("version") or "")[:18]
    lic = (loc.get("license") or "")[:14]
    return f"    - {src:<24} {ver:<18} {lic:<14} {loc.get('url')}"


def main(argv: list[str] | None = None, *, fetch_fn: FetchFn | None = None) -> int:
    """CLI entry point.

    ``fetch_fn`` is a programmatic injection point for tests; production
    callers omit it and the default :func:`fetch.fetch_bytes` is used.
    Captured here (not as an ``attempt_one_ref`` default) because
    Python evaluates default args at function-definition time, which
    makes monkey-patching ``fetch_bytes`` from a test impossible.
    """
    args = _parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    fetch_callable: FetchFn = fetch_fn if fetch_fn is not None else fetch_bytes

    ws = Path(args.workspace).resolve()
    repo_root = ws.parent
    logger.info("workspace : %s", ws)
    logger.info("repo_root : %s", repo_root)
    logger.info("mode      : %s  write=%s  force=%s  retry-failed=%s",
                args.mode, args.write, args.force, args.retry_failed)

    try:
        processes, tasks, p_path, t_path = _load_catalog(ws)
    except FileNotFoundError as exc:
        logger.error("catalog file missing: %s", exc)
        return 2

    ids = [i.strip() for i in args.ids.split(",") if i.strip()]

    # Counters
    n_in_scope = 0
    n_skipped_done = 0
    n_skipped_prior_failure = 0
    n_success = 0
    n_failure = 0
    n_dryrun = 0
    n_capped = 0

    for owner_id, ref_idx, ref in iter_refs(
        processes, tasks,
        mode=args.mode, ids=ids, poc_dois=POC_REF_DOIS,
    ):
        n_in_scope += 1

        if should_skip(ref, "pdf", force=args.force):
            n_skipped_done += 1
            continue
        if (has_recorded_failure(ref, "pdf")
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
            allow_paywalled=args.allow_paywalled,
            fetch_fn=fetch_callable,
            timeout=args.timeout,
            max_bytes=args.max_bytes,
            host_throttle_sec=args.host_throttle_sec,
        )

        label = f"[{owner_id}#{ref_idx}]"

        if outcome.kind == "would_walk":
            n_dryrun += 1
            cands = outcome.candidates or []
            print(f"  {label} {len(cands)} candidate(s):")
            for c in cands:
                print(_format_candidate_line(c))
            if not cands:
                print("    (would record failure: no candidate locations)")

        elif outcome.kind == "success":
            n_success += 1
            assert outcome.dest_path is not None
            rel_path = f"{outcome.dest_path.parent.name}/{outcome.dest_path.name}"
            record_success(
                ref, "pdf",
                path=rel_path,
                source_url=outcome.source_url,
                source_type=_source_type_for(outcome.source_tag),
                license=outcome.license_norm,
                is_publishable=is_publishable(outcome.license_norm),
            )
            print(f"  {label} OK  saved {outcome.dest_path.name} "
                  f"(src={outcome.source_tag}, licence={outcome.license_norm})")

        elif outcome.kind == "failure":
            n_failure += 1
            tried = outcome.tried or []
            record_failure(ref, "pdf", tried=tried, reason=outcome.reason)
            print(f"  {label} FAIL tried={tried}  reason={outcome.reason}")

        else:  # pragma: no cover - defensive
            logger.error("unknown attempt outcome kind: %r", outcome.kind)

    # ---- Summary
    print()
    print("Acquisition summary:")
    print(f"  in scope                 : {n_in_scope}")
    print(f"  skipped (already done)   : {n_skipped_done}")
    print(f"  skipped (prior failure)  : {n_skipped_prior_failure}")
    if not args.write:
        print(f"  dry-run candidates       : {n_dryrun}")
    else:
        print(f"  acquired (PDF saved)     : {n_success}")
        print(f"  failed (recorded)        : {n_failure}")
    if n_capped:
        print(f"  skipped (--limit cap)    : {n_capped}")

    # ---- Persist
    if args.write:
        _save_catalog(processes, tasks, p_path, t_path, workspace=ws)
        print()
        print(f"wrote: {p_path.name}")
        print(f"wrote: {t_path.name}")
    else:
        print()
        print("dry-run complete; pass --write to fetch + save + persist.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "AttemptResult",
    "attempt_one_ref",
    "main",
]
