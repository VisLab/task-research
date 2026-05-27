"""
core.py — Shared helpers for the auto-acquisition orchestrator.

Pure dict manipulation, a cache-dir resolver, and a small set of
filing helpers.  No network.  The success/failure recorders mutate
the in-memory ref dict; persisting to ``process_details.json`` /
``task_details.json`` is the orchestrator CLI's responsibility, not
this module's.

What's in here:

  resolve_cache_dir            Reuse the convention from enrich_pdf_locations.py
                               (per .status/cache_convention.md §3).
  iter_refs                    Walk the catalog in scope, yielding
                               ``(owner_id, ref_index, ref)``.
  should_skip                  Idempotency: is this ref's artifact already on disk?
  has_recorded_failure         Did we previously record a failure for this kind?
  record_success               Mutate ref to record a successful acquisition.
  record_failure               Mutate ref to record a failed attempt (path: null
                               plus diagnostic fields, per D-E2 locked 2026-05-27).
  artifact_dir                 ``repo_root / "HED-PDFs"`` or
                               ``repo_root / "HED-Markdown-private"`` for ``kind``.
  canonical_artifact_filename  Bare filename per ``identity.build_pdf_filename``
                               (D-E6 locked 2026-05-27); ``.md`` extension for
                               Markdown.

The success/failure recorders implement the schema shape locked in
``.status/pr_e_execution_2026-05-26.md`` §3.5 / D-E2: a single
``local_artifacts.{kind}`` object whose ``path`` is either a non-null
string (successful acquisition) or null (failure record carrying
``last_attempt``, ``attempts``, ``tried``, ``reason`` for the
maintainer to triage).  ``record_success`` and ``record_failure`` are
symmetric: each drops the *other* shape's keys when it stamps its
own shape, so the slot never carries a hybrid record across mode
transitions.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Literal

# ``identity.build_pdf_filename`` lives one directory up.  Add the
# parent to sys.path on import so ``canonical_artifact_filename`` can
# call it; matches the local-import convention used by sibling scripts
# in ``code/literature_search/``.
_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from identity import build_pdf_filename  # noqa: E402


# Two kinds of artifact land separately in the catalog; the helpers
# below are kind-agnostic — they take the literal "pdf" or "markdown"
# as a parameter rather than splitting into pdf-specific and
# markdown-specific functions.
ArtifactKind = Literal["pdf", "markdown"]


# ---------------------------------------------------------------------------
# Cache directory resolution (mirrors enrich_pdf_locations.py /
# .status/cache_convention.md §3)
# ---------------------------------------------------------------------------

def resolve_cache_dir(arg_value: str, workspace: Path) -> Path:
    """Resolve the cache root: ``--cache-dir`` > ``$HED_CACHE_DIR`` >
    ``<workspace>/outputs/cache``.

    Mirrors the helper in ``enrich_pdf_locations.py`` exactly so the
    two scripts read from the same cache on disk.  Kept here as a
    copy rather than imported because PR-E does not want a hard
    dependency on the enrichment module.
    """
    if arg_value and arg_value != "<auto>":
        p = Path(arg_value)
        return p if p.is_absolute() else workspace / p
    env_val = os.environ.get("HED_CACHE_DIR")
    if env_val:
        return Path(env_val)
    return workspace / "outputs" / "cache"


# ---------------------------------------------------------------------------
# Catalog walk
# ---------------------------------------------------------------------------

def iter_refs(
    processes: dict,
    tasks: list,
    mode: str,
    ids: list[str] | None = None,
    poc_dois: tuple[str, ...] | None = None,
) -> Iterable[tuple[str, int, dict]]:
    """Walk references in scope, yielding ``(owner_id, ref_index, ref)``.

    ``mode`` is one of:

      ``"full"``    every reference in both catalog files
      ``"single"``  references whose owner ID is in ``ids``
                    (process_id for processes, hedtsk_id for tasks)
      ``"poc"``     references whose ``ids.doi`` is in ``poc_dois``;
                    used by PR-E to walk the three DOIs locked in D-E3.

    The ``poc`` mode in PR-E is intentionally distinct from the
    process-id-based POC mode used by ``enrich_pdf_locations.py`` and
    ``enrich_ids.py``: PR-E exercises specific *references*, not
    whole processes.
    """
    if mode not in ("full", "single", "poc"):
        raise ValueError(f"unknown mode: {mode!r}")

    procs = (processes or {}).get("processes", []) or []
    items: list[tuple[str, dict]] = []
    for p in procs:
        items.append((p.get("process_id", "") or "", p))
    for t in tasks or []:
        items.append((t.get("hedtsk_id", "") or "", t))

    wanted_ids = set(ids or [])
    wanted_dois = {(d or "").lower().strip() for d in (poc_dois or [])}

    for owner_id, item in items:
        if mode == "single" and owner_id not in wanted_ids:
            continue
        for idx, ref in enumerate(item.get("references") or []):
            if mode == "poc":
                doi = ((ref.get("ids") or {}).get("doi") or "").lower().strip()
                if doi not in wanted_dois:
                    continue
            yield owner_id, idx, ref


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------

def should_skip(ref: dict, kind: ArtifactKind, force: bool = False) -> bool:
    """Return True if this ref already has a successful ``kind`` artifact.

    "Success" means ``local_artifacts[kind].path`` is a non-empty
    string.  A failure record (``path: null`` accompanied by
    ``last_attempt``) does NOT count as success; ``should_skip``
    returns False so the orchestrator can retry such refs.

    ``force=True`` always returns False — the caller is explicitly
    asking to re-acquire.
    """
    if force:
        return False
    la = (ref.get("local_artifacts") or {}).get(kind) or {}
    path = la.get("path")
    return isinstance(path, str) and bool(path.strip())


def has_recorded_failure(ref: dict, kind: ArtifactKind) -> bool:
    """Return True if this ref carries a previous failure record for ``kind``.

    Used by the orchestrator's ``--retry-failed`` mode to scope which
    refs to retry.
    """
    la = (ref.get("local_artifacts") or {}).get(kind) or {}
    return la.get("path") is None and la.get("last_attempt") is not None


# ---------------------------------------------------------------------------
# Record success and failure
# ---------------------------------------------------------------------------

def _utcnow_iso() -> str:
    """UTC timestamp in ISO 8601, seconds precision, trailing ``Z``."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# Keys written exclusively by ``record_failure``.  ``record_success``
# strips these when stamping a success so an entry never carries a
# hybrid record.
_FAILURE_KEYS: tuple[str, ...] = ("last_attempt", "attempts", "tried", "reason")

# Keys written by ``record_success`` (in addition to ``path``).
# ``record_failure`` strips these when stamping a failure so the slot
# reflects the current attempt's state cleanly — without this, a
# ``--force`` re-acquisition that fails would leave a stale
# ``source_url`` / ``license`` from the prior successful run.
_SUCCESS_KEYS: tuple[str, ...] = (
    "source_url", "source_type", "license",
    "acquired_on", "acquired_via", "converter", "is_publishable",
)


def record_success(
    ref: dict,
    kind: ArtifactKind,
    *,
    path: str,
    source_url: str,
    source_type: str,
    license: str,
    acquired_via: str = "auto",
    converter: str | None = None,
    is_publishable: bool | None = None,
    when: str | None = None,
) -> None:
    """Mutate ``ref`` to record a successful artifact acquisition.

    Replaces any prior failure-record fields for this kind so the
    record reflects a clean success (no stale ``last_attempt`` /
    ``attempts`` left behind).

    Preserves ``acquired_on`` if the slot already has one — a re-run
    that lands the same artifact does not change the original
    acquisition timestamp.  Pass ``when`` (ISO 8601 string) to
    override the timestamp deterministically — useful for tests.

    ``is_publishable`` is an optional cache of
    ``license_policy.is_publishable(license)``.  Stamped onto the
    block only when provided so this module stays free of a
    ``license_policy`` dependency; the orchestrator computes it and
    passes it in.  Per the schema description, downstream consumers
    must recompute rather than trust a stale stored value.
    """
    la = ref.setdefault("local_artifacts", {})
    block: dict = la.setdefault(kind, {})

    block["path"] = path
    block["source_url"] = source_url
    block["source_type"] = source_type
    block["license"] = license
    block["acquired_on"] = block.get("acquired_on") or (when or _utcnow_iso())
    block["acquired_via"] = acquired_via
    if converter is not None:
        block["converter"] = converter
    if is_publishable is not None:
        block["is_publishable"] = bool(is_publishable)

    # Drop failure diagnostic fields if they linger from a prior
    # attempt.  Keeping them would confuse downstream readers.
    for key in _FAILURE_KEYS:
        block.pop(key, None)


def record_failure(
    ref: dict,
    kind: ArtifactKind,
    *,
    tried: list[str],
    reason: str,
    when: str | None = None,
) -> None:
    """Mutate ``ref`` to record a failed acquisition attempt for ``kind``.

    D-E2 (locked 2026-05-27): a failure is a ``local_artifacts[kind]``
    entry with ``path: null`` plus diagnostic fields.

    ``attempts`` increments across re-runs so the maintainer can spot
    refs that keep failing.  ``tried`` is the list of sources visited
    on the latest attempt (overwritten — callers wanting the full
    history can derive it from session reports).

    Pass ``when`` (ISO 8601 string) to override the timestamp
    deterministically — useful for tests.

    Symmetric with :func:`record_success`: drops any success-only keys
    (``source_url`` / ``license`` / ``acquired_on`` / ``acquired_via``
    / ``converter`` / ``is_publishable``) that may linger from a prior
    successful acquisition, so a forced re-acquire that ends in failure
    leaves the slot in a clean failure shape.
    """
    la = ref.setdefault("local_artifacts", {})
    block: dict = la.setdefault(kind, {})

    prior_attempts = block.get("attempts") or 0
    block["path"] = None
    block["last_attempt"] = when or _utcnow_iso()
    block["attempts"] = prior_attempts + 1
    block["tried"] = list(tried)
    block["reason"] = reason

    # Drop success-only keys so a transition success -> failure
    # produces a clean failure record (mirrors record_success).
    for key in _SUCCESS_KEYS:
        block.pop(key, None)


# ---------------------------------------------------------------------------
# Artifact filing
# ---------------------------------------------------------------------------

# Per plan v2 §4 D5 (decided 2026-05-19) and §3.4: PDFs land in
# ``HED-PDFs/``; Markdowns land in ``HED-Markdown-private/`` on
# acquisition.  A separate ``publish_markdown`` step (deferred follow-
# up) moves licence-compliant Markdowns into ``HED-Markdown-public/``.
# Auto-acquisition therefore only ever writes into the private dir
# for Markdown.
_ARTIFACT_DIRS: dict[ArtifactKind, str] = {
    "pdf":      "HED-PDFs",
    "markdown": "HED-Markdown-private",
}


def artifact_dir(repo_root: Path, kind: ArtifactKind) -> Path:
    """Return the directory under ``repo_root`` where ``kind`` lands.

    Does not create the directory; callers should
    ``mkdir(parents=True, exist_ok=True)`` before writing.

    Raises ``ValueError`` for unknown kinds (the caller is hitting an
    unimplemented code path, not a runtime data issue).
    """
    if kind not in _ARTIFACT_DIRS:
        raise ValueError(f"unknown artifact kind: {kind!r}")
    return Path(repo_root) / _ARTIFACT_DIRS[kind]


def _first_author_family(authors_str: str | None) -> str | None:
    """Extract the first-author family name from the catalog ``authors`` string.

    Mirrors the same-named helper in ``record_artifact.py`` so the
    acquire package is self-contained; if a third caller appears the
    two should be consolidated into ``identity.py``.
    """
    if not authors_str:
        return None
    s = authors_str.split(",")[0].strip().rstrip(".,;:").strip()
    return s or None


def canonical_artifact_filename(ref: dict, kind: ArtifactKind) -> str:
    """Return the canonical bare filename (no directory) for ``ref``.

    Delegates to :func:`identity.build_pdf_filename` and swaps the
    extension to ``.md`` for Markdown so the PDF and Markdown for the
    same paper share a stem (and therefore sort together in any
    directory listing) — D-E6 locked 2026-05-27.

    ``ref`` must expose the standard catalog fields ``authors``,
    ``year`` and ``title``.  Missing fields are tolerated (the
    underlying helpers substitute ``Anonymous`` / ``nodate`` /
    ``UntitledNonLatin`` for absent inputs).
    """
    family = _first_author_family(ref.get("authors"))
    year   = ref.get("year")
    title  = ref.get("title")
    fname  = build_pdf_filename(family, year, title)
    if kind == "pdf":
        return fname
    if kind == "markdown":
        # build_pdf_filename always emits a ``.pdf`` suffix; replace
        # only that final segment to keep the rest of the name intact.
        return fname[:-4] + ".md" if fname.lower().endswith(".pdf") else fname + ".md"
    raise ValueError(f"unknown artifact kind: {kind!r}")
