"""
core.py — Shared helpers for the auto-acquisition orchestrator.

Pure dict manipulation and a cache-dir resolver.  No network, no
filesystem writes (the success/failure recorders mutate the in-memory
ref dict; persisting to ``process_details.json`` / ``task_details.json``
is the orchestrator CLI's responsibility, not this module's).

Five things in here:

  resolve_cache_dir   Reuse the convention from enrich_pdf_locations.py
                      (per .status/cache_convention.md §3).
  iter_refs           Walk the catalog in scope, yielding
                      ``(owner_id, ref_index, ref)``.
  should_skip         Idempotency: is this ref's artifact already on disk?
  record_success      Mutate ref to record a successful acquisition.
  record_failure      Mutate ref to record a failed attempt (path: null
                      plus diagnostic fields, per D-E2 locked 2026-05-27).

The success/failure recorders implement the schema shape locked in
``.status/pr_e_execution_2026-05-26.md`` §3.5 / D-E2: a single
``local_artifacts.{kind}`` object whose ``path`` is either a non-null
string (successful acquisition) or null (failure record carrying
``last_attempt``, ``attempts``, ``tried``, ``reason`` for the
maintainer to triage).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Literal


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

    # Drop failure diagnostic fields if they linger from a prior
    # attempt.  Keeping them would confuse downstream readers.
    for key in ("last_attempt", "attempts", "tried", "reason"):
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
    """
    la = ref.setdefault("local_artifacts", {})
    block: dict = la.setdefault(kind, {})

    prior_attempts = block.get("attempts") or 0
    block["path"] = None
    block["last_attempt"] = when or _utcnow_iso()
    block["attempts"] = prior_attempts + 1
    block["tried"] = list(tried)
    block["reason"] = reason
