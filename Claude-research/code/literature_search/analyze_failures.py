#!/usr/bin/env python3
"""
analyze_failures.py — Bucket acquisition failures by failure mode.

Reads ``process_details.json`` + ``task_details.json``, walks every
reference's ``local_artifacts[kind]`` block, and produces a
three-table report for refs whose stamp is a failure record (per
D-E2, locked 2026-05-27: ``path: null`` plus ``reason`` /
``last_attempt`` / ``attempts`` / ``tried``).

The three tables, in increasing granularity:

  1.  **By ``tried`` set** — coarse cut.  Which route combinations got
      walked.  E.g. "245 refs walked just openalex".
  2.  **By normalized reason component** — compound reasons (joined by
      the orchestrator with ``"; "``) are split, each component
      normalized, and counted independently.  This is the
      *candidate-level* cut: the same orchestrator-level grep
      counts we got from the wet-run log, now properly attributed.
  3.  **By ``(tried, normalized_reason)`` pattern** — finest cut, sorted
      by count desc.  Top rows are the design input for recovery
      passes (PR-H et seq.).

``normalize_reason`` strips:

  *  URLs (``https?://...``)            → ``<url>``
  *  Byte counts (``=52428800``)       → ``=<n>``
  *  Content-type parameters           → strip everything after ``;``
                                          inside ``(...)``, keep the
                                          media-type base
  *  Exception messages                → keep ``<type>error`` or
                                          ``<type>exception`` (lowercased),
                                          drop the message body

…so that superficially-different failures bucket together when they
describe the same underlying failure mode.

Usage (run from the workspace root, ``Claude-research/``)::

    python code/literature_search/analyze_failures.py --kind pdf
    python code/literature_search/analyze_failures.py --kind markdown --limit 50

Outputs (under ``--output-dir`` workspace-relative, default
``outputs/analysis``)::

    failures_<kind>_<YYYY-MM-DD>.md
    failures_<kind>_<YYYY-MM-DD>.json

The JSON sidecar carries the full ref-ID list per bucket so a
follow-up recovery script can ingest a specific bucket without
re-parsing the catalog.

Exit codes:
    0 — clean
    1 — no failures found for ``--kind``
    2 — catalog file missing
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, Literal


ArtifactKind = Literal["pdf", "markdown"]

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Reason normalization
# ---------------------------------------------------------------------------

# Match a URL.  Stops at whitespace or closing paren so a URL inside a
# parenthesised note doesn't swallow the closing punctuation.
_URL_RE = re.compile(r"https?://[^\s)]+")

# Match a numeric value of 4+ digits after ``=`` (with optional space).
# Catches ``max_bytes=52428800`` but not ``HTTP 403`` or ``attempts=5``.
_BYTES_AFTER_EQ_RE = re.compile(r"=\s*\d{4,}")

# Match a parenthesised content-type with parameters: keep group 1 (the
# bare media type), drop everything after the first ``;``.
_CT_PARAMS_RE = re.compile(r"\(([^;)]+);\s*[^)]+\)")

# Match an exception name followed by ``:`` and a message body.  After
# normalize_reason_component() lowercases the string, exception type
# names look like ``connectionerror`` or ``timeoutexception``.  The
# message body (anything up to the next ``;`` or ``|``) is dropped so
# different message texts for the same exception type bucket together.
_EXC_RE = re.compile(r"\b([a-z][a-z_.]*(?:error|exception))\s*:\s*[^;|]+")


def split_reason(reason: str) -> list[str]:
    """Split a compound failure reason on ``;`` *outside* parens.

    The orchestrator joins per-candidate notes with ``"; "``, but
    content-type parameters in ``not PDF (text/html; charset=utf-8)``
    also contain semicolons.  Plain ``.split(";")`` would mangle the
    latter; this respects parenthesis depth.

    Returns a list of stripped components, empty if ``reason`` is
    empty or whitespace.
    """
    parts: list[str] = []
    depth = 0
    cur: list[str] = []
    for ch in reason:
        if ch == "(":
            depth += 1
            cur.append(ch)
        elif ch == ")":
            depth = max(0, depth - 1)
            cur.append(ch)
        elif ch == ";" and depth == 0:
            piece = "".join(cur).strip()
            if piece:
                parts.append(piece)
            cur = []
        else:
            cur.append(ch)
    tail = "".join(cur).strip()
    if tail:
        parts.append(tail)
    return parts


def normalize_reason_component(component: str) -> str:
    """Normalize one piece of a (possibly compound) reason string.

    Steps (order matters):

      1. Lowercase + strip.
      2. Replace URLs with ``<url>``.
      3. Replace ``=<long-number>`` with ``=<n>``.
      4. Strip parameters from parenthesised content types.
      5. Collapse exception messages: keep just the exception type name.
      6. Collapse runs of whitespace.

    Returns the empty string for empty input.
    """
    s = component.strip().lower()
    if not s:
        return ""
    s = _URL_RE.sub("<url>", s)
    s = _BYTES_AFTER_EQ_RE.sub("=<n>", s)
    s = _CT_PARAMS_RE.sub(r"(\1)", s)
    s = _EXC_RE.sub(r"\1", s)
    return re.sub(r"\s+", " ", s).strip()


def normalize_reason(reason: str) -> str:
    """Normalize a full (possibly compound) reason string.

    Components are split with :func:`split_reason`, each normalized
    with :func:`normalize_reason_component`, and rejoined with ``" | "``
    so the ``(tried, reason)`` bucket key is stable across whatever
    order the orchestrator happened to walk candidates in.
    """
    parts = [normalize_reason_component(p) for p in split_reason(reason)]
    parts = [p for p in parts if p]
    return " | ".join(parts)


def reason_components(reason: str) -> list[str]:
    """Return the normalized components of a reason string.

    Each component is independently normalized; ordering is preserved
    so the caller can correlate components with the candidate-walk
    order if they care.  Used by the by-component bucket (table 2).
    """
    return [normalize_reason_component(p) for p in split_reason(reason) if p.strip()]


# ---------------------------------------------------------------------------
# Failure extraction
# ---------------------------------------------------------------------------

@dataclass
class Failure:
    """One ref's failure record, with normalized reason fields.

    ``tried`` is frozen to a tuple so it can be used as a dict key.
    ``reason_raw`` is preserved verbatim for the JSON sidecar (a
    consumer wanting to do its own normalization should not have to
    re-read the catalog).
    """
    owner_id: str           # process_id or hedtsk_id
    ref_idx: int            # position within the owner's references list
    doi: str                # may be "" for no-DOI refs
    tried: tuple[str, ...]
    reason_raw: str
    reason_normalized: str
    components: list[str]


def _ref_doi(ref: dict) -> str:
    return ((ref.get("ids") or {}).get("doi") or "").strip().lower()


def _is_failure(block: dict | None) -> bool:
    """Return True iff ``block`` is a failure stamp per D-E2.

    Success stamp:  ``path`` is a non-empty string.
    Failure stamp:  ``path`` is None (or absent) AND ``reason`` is set.
    Absent:         block is None / missing reason.
    """
    if not isinstance(block, dict):
        return False
    path = block.get("path")
    if isinstance(path, str) and path.strip():
        return False
    return "reason" in block


def iter_failed_refs(
    processes: dict,
    tasks: list,
    kind: ArtifactKind,
) -> Iterator[Failure]:
    """Yield a :class:`Failure` for every ref with a failure stamp on ``kind``.

    Walks both catalog files in the same order as
    ``acquire.core.iter_refs(mode="full")`` so report ordering is
    reproducible.  Refs with a success stamp or no stamp at all are
    skipped.
    """
    items: list[tuple[str, dict]] = []
    for p in (processes or {}).get("processes") or []:
        items.append((p.get("process_id") or "", p))
    for t in tasks or []:
        items.append((t.get("hedtsk_id") or "", t))

    for owner_id, item in items:
        for idx, ref in enumerate(item.get("references") or []):
            la = (ref.get("local_artifacts") or {}).get(kind)
            if not _is_failure(la):
                continue
            assert la is not None  # narrowing for type checkers
            tried_list = la.get("tried")
            tried = tuple(tried_list) if isinstance(tried_list, list) else ()
            reason_raw = la.get("reason") or ""
            yield Failure(
                owner_id=owner_id,
                ref_idx=idx,
                doi=_ref_doi(ref),
                tried=tried,
                reason_raw=reason_raw,
                reason_normalized=normalize_reason(reason_raw),
                components=reason_components(reason_raw),
            )


# ---------------------------------------------------------------------------
# Bucketing
# ---------------------------------------------------------------------------

@dataclass
class Bucket:
    """One bucket of failures sharing a key.

    ``ref_ids`` are ``"<owner_id>#<ref_idx>"`` strings — the same
    format the acquire orchestrators use in per-ref log lines, so a
    bucket's contents can be grepped in the wet-run log directly.

    ``sample_dois`` is capped at 3; the JSON sidecar carries the
    full ref-ID list if a caller needs to enumerate all refs in a
    bucket.
    """
    key: str
    count: int = 0
    ref_ids: list[str] = field(default_factory=list)
    sample_dois: list[str] = field(default_factory=list)


def _ref_id(f: Failure) -> str:
    return f"{f.owner_id}#{f.ref_idx}"


def _format_tried(tried: tuple[str, ...]) -> str:
    """Stable string form of a ``tried`` tuple, including empty."""
    return "[" + ", ".join(tried) + "]" if tried else "[]"


def _add_to_bucket(b: Bucket, f: Failure, *, sample_cap: int = 3) -> None:
    b.count += 1
    b.ref_ids.append(_ref_id(f))
    if f.doi and f.doi not in b.sample_dois and len(b.sample_dois) < sample_cap:
        b.sample_dois.append(f.doi)


def bucket_by_tried(failures: Iterable[Failure]) -> dict[str, Bucket]:
    """Group failures by ``tuple(tried)``.

    Empty tried -> ``"[]"``.  Order of insertion is preserved (so
    the report's ordering is deterministic even before the
    count-sort).
    """
    out: "OrderedDict[str, Bucket]" = OrderedDict()
    for f in failures:
        key = _format_tried(f.tried)
        b = out.setdefault(key, Bucket(key=key))
        _add_to_bucket(b, f)
    return dict(out)


def bucket_by_reason_component(failures: Iterable[Failure]) -> dict[str, Bucket]:
    """Group failures by each normalized reason component.

    A failure with two components contributes one count to each of
    the two buckets — this is the candidate-level cut.  ``ref_ids``
    in each bucket may therefore contain duplicates if the same ref
    triggered the same component twice (it shouldn't, in practice,
    because each candidate produces one note).
    """
    out: "OrderedDict[str, Bucket]" = OrderedDict()
    for f in failures:
        if not f.components:
            # Reasons that fail to split (empty reason, whitespace
            # only) get bucketed as an explicit sentinel rather than
            # silently dropped — they're worth seeing in the report.
            b = out.setdefault("(empty)", Bucket(key="(empty)"))
            _add_to_bucket(b, f)
            continue
        for comp in f.components:
            b = out.setdefault(comp, Bucket(key=comp))
            _add_to_bucket(b, f)
    return dict(out)


def bucket_by_pattern(failures: Iterable[Failure]) -> dict[str, Bucket]:
    """Group failures by ``(tried, normalized_reason)`` pattern.

    The finest cut.  Bucket key has shape
    ``"<tried-set> :: <normalized-reason>"``.
    """
    out: "OrderedDict[str, Bucket]" = OrderedDict()
    for f in failures:
        tried_part = _format_tried(f.tried)
        reason_part = f.reason_normalized or "(empty)"
        key = f"{tried_part} :: {reason_part}"
        b = out.setdefault(key, Bucket(key=key))
        _add_to_bucket(b, f)
    return dict(out)


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------

def _sorted_buckets(buckets: dict[str, Bucket]) -> list[Bucket]:
    """Sort buckets by count desc, then key asc for stable ordering."""
    return sorted(buckets.values(), key=lambda b: (-b.count, b.key))


def _samples_cell(b: Bucket) -> str:
    return ", ".join(b.sample_dois) if b.sample_dois else "—"


def format_markdown_report(
    failures: list[Failure],
    kind: ArtifactKind,
    *,
    limit: int = 25,
    when: str | None = None,
) -> str:
    """Compose the three-table Markdown report.

    ``limit`` caps the rows in each table (top-N); the JSON sidecar
    always carries the full bucket list.  ``when`` overrides the
    default date stamp (useful in tests for determinism).
    """
    when = when or _utc_today()
    total = len(failures)

    by_tried = _sorted_buckets(bucket_by_tried(failures))
    by_comp = _sorted_buckets(bucket_by_reason_component(failures))
    by_pattern = _sorted_buckets(bucket_by_pattern(failures))

    lines: list[str] = []
    lines.append(f"# Acquisition failures — {kind} ({when})")
    lines.append("")
    lines.append(f"Total failed refs: **{total}**.")
    lines.append("")
    lines.append(
        "Buckets are sorted by count desc.  See the JSON sidecar for "
        "full ref-ID lists per bucket."
    )
    lines.append("")

    # --- Table 1
    lines.append("## By `tried` set")
    lines.append("")
    lines.append("Coarse cut: which route combinations got walked.")
    lines.append("")
    lines.append("| Count | Tried | Sample DOIs |")
    lines.append("|---:|---|---|")
    for b in by_tried[:limit]:
        lines.append(f"| {b.count} | `{b.key}` | {_samples_cell(b)} |")
    if len(by_tried) > limit:
        lines.append(f"| … | _{len(by_tried) - limit} more buckets_ | |")
    lines.append("")

    # --- Table 2
    lines.append("## By normalized reason component")
    lines.append("")
    lines.append(
        "Compound reasons split on `;`; each component counted "
        "independently.  This is the candidate-level cut."
    )
    lines.append("")
    lines.append("| Count | Reason component | Sample DOIs |")
    lines.append("|---:|---|---|")
    for b in by_comp[:limit]:
        lines.append(f"| {b.count} | `{b.key}` | {_samples_cell(b)} |")
    if len(by_comp) > limit:
        lines.append(f"| … | _{len(by_comp) - limit} more buckets_ | |")
    lines.append("")

    # --- Table 3
    lines.append("## By (tried, normalized reason) pattern")
    lines.append("")
    lines.append(
        "Finest cut.  Top rows are the design input for recovery passes."
    )
    lines.append("")
    lines.append("| Count | Pattern | Sample DOIs |")
    lines.append("|---:|---|---|")
    for b in by_pattern[:limit]:
        lines.append(f"| {b.count} | `{b.key}` | {_samples_cell(b)} |")
    if len(by_pattern) > limit:
        lines.append(f"| … | _{len(by_pattern) - limit} more buckets_ | |")
    lines.append("")

    return "\n".join(lines)


def _serialize_bucket(b: Bucket) -> dict:
    return {
        "key": b.key,
        "count": b.count,
        "sample_dois": b.sample_dois,
        "ref_ids": b.ref_ids,
    }


def format_json_sidecar(
    failures: list[Failure],
    kind: ArtifactKind,
    *,
    when: str | None = None,
) -> str:
    """Return a JSON string carrying every bucket with full ref-ID lists.

    Layout::

        {
          "kind": "pdf",
          "when": "2026-06-01",
          "total": 780,
          "by_tried":     [ {key, count, sample_dois, ref_ids}, … ],
          "by_component": [ … ],
          "by_pattern":   [ … ]
        }
    """
    when = when or _utc_today()
    payload = {
        "kind": kind,
        "when": when,
        "total": len(failures),
        "by_tried": [
            _serialize_bucket(b) for b in _sorted_buckets(bucket_by_tried(failures))
        ],
        "by_component": [
            _serialize_bucket(b)
            for b in _sorted_buckets(bucket_by_reason_component(failures))
        ],
        "by_pattern": [
            _serialize_bucket(b)
            for b in _sorted_buckets(bucket_by_pattern(failures))
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# CLI driver
# ---------------------------------------------------------------------------

def _utc_today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _load_catalog(workspace: Path) -> tuple[dict, list]:
    p_path = workspace / "process_details.json"
    t_path = workspace / "task_details.json"
    missing = [str(p) for p in (p_path, t_path) if not p.exists()]
    if missing:
        raise FileNotFoundError("catalog file(s) missing: " + ", ".join(missing))
    with p_path.open("r", encoding="utf-8") as f:
        processes = json.load(f)
    with t_path.open("r", encoding="utf-8") as f:
        tasks = json.load(f)
    return processes, tasks


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--kind",
        choices=["pdf", "markdown"],
        required=True,
        help="Artifact kind to analyze.",
    )
    p.add_argument(
        "--workspace",
        default=".",
        help="Workspace root (Claude-research/).  Default: cwd.",
    )
    p.add_argument(
        "--output-dir",
        default="outputs/analysis",
        help="Workspace-relative output directory for the .md and .json.",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=25,
        help="Cap on rows printed per table in the Markdown report. "
             "Default: 25.  JSON sidecar carries the full lists.",
    )
    p.add_argument(
        "--stdout",
        action="store_true",
        help="Print the Markdown report to stdout and skip file writes.",
    )
    p.add_argument("--verbose", "-v", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    args = _parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    ws = Path(args.workspace).resolve()
    logger.info("workspace : %s", ws)
    logger.info("kind      : %s", args.kind)

    try:
        processes, tasks = _load_catalog(ws)
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return 2

    failures = list(iter_failed_refs(processes, tasks, args.kind))
    if not failures:
        logger.error(
            "No failure stamps found for kind=%s.  Nothing to analyze.",
            args.kind,
        )
        return 1

    md = format_markdown_report(failures, args.kind, limit=args.limit)

    if args.stdout:
        sys.stdout.write(md)
        return 0

    out_dir = ws / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    today = _utc_today()
    md_path = out_dir / f"failures_{args.kind}_{today}.md"
    json_path = out_dir / f"failures_{args.kind}_{today}.json"

    md_path.write_text(md, encoding="utf-8")
    json_path.write_text(
        format_json_sidecar(failures, args.kind),
        encoding="utf-8",
    )

    print(f"wrote: {md_path}")
    print(f"wrote: {json_path}")
    print(f"  ({len(failures)} failure refs analyzed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ArtifactKind",
    "Bucket",
    "Failure",
    "bucket_by_pattern",
    "bucket_by_reason_component",
    "bucket_by_tried",
    "format_json_sidecar",
    "format_markdown_report",
    "iter_failed_refs",
    "main",
    "normalize_reason",
    "normalize_reason_component",
    "reason_components",
    "split_reason",
]
