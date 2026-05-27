#!/usr/bin/env python3
"""
enrich_ids.py — Fill the ``ids`` block on every reference that has a DOI.

For each reference with ``ref.ids.doi`` set, this script reads PR-D's
already-cached OpenAlex and Semantic Scholar responses for that DOI and
fills any null slot in ``ref.ids`` (``openalex_id``, ``pmid``, ``pmcid``,
``s2_id``, ``arxiv_id``) with the corresponding identifier from the
response.

Pure cache-read pass.  No new network calls in the common case: PR-D
left every DOI's response on disk under ``<cache_root>/<source>/stable/``
per ``.status/cache_convention.md``.  If a cached response is absent
(a DOI PR-D didn't process) the underlying ``lookup_by_doi`` clients
hit the live API once, exactly as PR-D would have.

Source-priority rules (see
``.status/id_enrichment_execution_2026-05-27.md`` §3):

  openalex_id   OpenAlex ``id`` field (strip prefix)
  pmid          OpenAlex ``ids.pmid`` first, S2 ``externalIds.PubMed`` fallback
  pmcid         OpenAlex ``ids.pmcid`` first, S2 ``externalIds.PubMedCentral`` fallback
                (normalised to ``PMC<digits>``)
  s2_id         S2 ``paperId``
  arxiv_id      S2 ``externalIds.ArXiv``

A pre-existing non-null value in ``ref.ids`` is NEVER overwritten — if a
candidate disagrees, the conflict is logged for human review and the
existing value is kept.

Dry-run by default.  ``--write`` stages through
``.scratch/enrich_ids/`` before atomically copying back to
``process_details.json`` and ``task_details.json``.

Usage (run from the workspace root, ``Claude-research/``)::

    # 3 POC items
    python code/literature_search/enrich_ids.py --mode poc

    # Single item
    python code/literature_search/enrich_ids.py --mode single \\
        --ids hed_response_inhibition

    # Full catalog, persist
    python code/literature_search/enrich_ids.py --mode full --write

Exit codes:
    0  clean (dry-run completed, or wet-run wrote successfully)
    1  data issue (parse failure, validation failure)
    2  file not found
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable

# Allow direct invocation: ``python code/literature_search/enrich_ids.py``.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from reference_compat import ref_doi  # noqa: E402

from clients.openalex import lookup_by_doi as oa_lookup  # noqa: E402
from clients.semanticscholar import lookup_by_doi as s2_lookup  # noqa: E402


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Cache-directory resolution (per .status/cache_convention.md §3)
# ---------------------------------------------------------------------------

def resolve_cache_dir(arg_value: str, workspace: Path) -> Path:
    """Resolve the cache root: arg > $HED_CACHE_DIR > <workspace>/outputs/cache."""
    if arg_value and arg_value != "<auto>":
        p = Path(arg_value)
        return p if p.is_absolute() else workspace / p
    env_val = os.environ.get("HED_CACHE_DIR")
    if env_val:
        return Path(env_val)
    return workspace / "outputs" / "cache"


# ---------------------------------------------------------------------------
# Identifier extraction
# ---------------------------------------------------------------------------

# OpenAlex prefixes its IDs as URLs.  These regexes pull the bare ID out
# of the URL form; they also tolerate already-stripped values (a bare
# "W2003876547" passes through unchanged because the prefix is optional).
_RE_OPENALEX = re.compile(r"^(?:https?://openalex\.org/)?(W\d+)$", re.I)
_RE_PMID     = re.compile(r"^(?:https?://(?:www\.)?(?:pubmed\.)?ncbi\.nlm\.nih\.gov/(?:pubmed/)?)?(\d+)$", re.I)
_RE_PMCID    = re.compile(r"^(?:https?://(?:www\.)?(?:pmc\.)?ncbi\.nlm\.nih\.gov/pmc/articles/)?(?:PMC)?(\d+)/?$", re.I)


def _strip_prefix(value: object, pattern: re.Pattern[str]) -> str | None:
    """Strip a known URL prefix from an identifier, returning the bare ID."""
    if not isinstance(value, str) or not value.strip():
        return None
    m = pattern.match(value.strip())
    return m.group(1) if m else None


def _normalise_pmcid(value: object) -> str | None:
    """Return ``PMC<digits>`` form.  Accepts bare digits or already-prefixed."""
    bare = _strip_prefix(value, _RE_PMCID)
    return f"PMC{bare}" if bare else None


def extract_ids_from_openalex(resp: dict | None) -> dict[str, str]:
    """Pull openalex_id, pmid, pmcid out of an OpenAlex Work response.

    Missing or unparseable values are simply absent from the returned
    dict — never present-but-null.  Callers should treat a missing key
    as "no candidate from this source."
    """
    if not isinstance(resp, dict) or not resp:
        return {}
    out: dict[str, str] = {}

    # Top-level id is the OpenAlex Work URL.  ids.openalex is the same.
    oa_id = _strip_prefix(resp.get("id"), _RE_OPENALEX)
    if not oa_id:
        oa_id = _strip_prefix((resp.get("ids") or {}).get("openalex"), _RE_OPENALEX)
    if oa_id:
        out["openalex_id"] = oa_id

    ids_block = resp.get("ids") or {}
    pmid = _strip_prefix(ids_block.get("pmid"), _RE_PMID)
    if pmid:
        out["pmid"] = pmid

    pmcid = _normalise_pmcid(ids_block.get("pmcid"))
    if pmcid:
        out["pmcid"] = pmcid

    return out


def extract_ids_from_s2(resp: dict | None) -> dict[str, str]:
    """Pull s2_id, pmid, pmcid, arxiv_id out of an S2 Paper response."""
    if not isinstance(resp, dict) or not resp:
        return {}
    out: dict[str, str] = {}

    paper_id = resp.get("paperId")
    if isinstance(paper_id, str) and paper_id.strip():
        out["s2_id"] = paper_id.strip()

    ext = resp.get("externalIds") or {}
    pmid_raw = ext.get("PubMed")
    if isinstance(pmid_raw, str) and pmid_raw.strip().isdigit():
        out["pmid"] = pmid_raw.strip()

    pmcid = _normalise_pmcid(ext.get("PubMedCentral"))
    if pmcid:
        out["pmcid"] = pmcid

    arxiv = ext.get("ArXiv")
    if isinstance(arxiv, str) and arxiv.strip():
        out["arxiv_id"] = arxiv.strip()

    return out


# ---------------------------------------------------------------------------
# Merge + apply
# ---------------------------------------------------------------------------

def merge_id_sets(oa: dict[str, str], s2: dict[str, str]) -> dict[str, str]:
    """Combine OpenAlex and S2 candidate IDs.

    OpenAlex wins for ``pmid`` and ``pmcid`` when both carry a value;
    S2 fills the slots OpenAlex doesn't surface (``s2_id``,
    ``arxiv_id``).
    """
    merged = dict(s2)        # start from S2 so OA can overwrite shared keys
    merged.update(oa)        # OpenAlex slots win on conflict
    # Ensure S2-only keys survive even though OA wrote nothing for them
    for k in ("s2_id", "arxiv_id"):
        if k in s2 and k not in merged:
            merged[k] = s2[k]
    return merged


# A conflict is (slot, existing_value_in_ref, candidate_value_from_apis).
Conflict = tuple[str, str, str]


def apply_to_ref(ref: dict, candidates: dict[str, str]) -> tuple[int, list[Conflict]]:
    """Write candidate IDs into ``ref['ids']`` without overwriting non-null slots.

    Returns ``(n_filled, conflicts)``:
      - ``n_filled``: number of previously-null slots set to a non-null
        candidate.
      - ``conflicts``: list of slots where ``ref['ids']`` already has a
        non-null value that disagrees with the candidate.  Returned for
        the driver to log; ``ref`` is unchanged for those slots.
    """
    ids = ref.setdefault("ids", {})
    n_filled = 0
    conflicts: list[Conflict] = []

    for slot, cand in candidates.items():
        if not cand:
            continue
        existing = ids.get(slot)
        if existing in (None, "", []):
            ids[slot] = cand
            n_filled += 1
            continue
        if existing != cand:
            conflicts.append((slot, str(existing), cand))
        # equal values: silently no-op (idempotent)

    return n_filled, conflicts


# ---------------------------------------------------------------------------
# Per-reference enrichment
# ---------------------------------------------------------------------------

def enrich_one_reference(
    ref: dict,
    cache_dir: Path,
    email: str,
) -> tuple[int, list[Conflict], bool]:
    """Enrich one reference's ``ids`` block.

    Returns ``(n_filled, conflicts, had_doi)``.  ``had_doi=False`` means
    the ref was skipped because it has no DOI to look up.
    """
    doi = ref_doi(ref)
    if not doi:
        return 0, [], False

    oa_resp = oa_lookup(doi, cache_dir, email)
    s2_resp = s2_lookup(doi, cache_dir, email)

    oa_ids = extract_ids_from_openalex(oa_resp)
    s2_ids = extract_ids_from_s2(s2_resp)
    merged = merge_id_sets(oa_ids, s2_ids)

    n_filled, conflicts = apply_to_ref(ref, merged)
    return n_filled, conflicts, True


# ---------------------------------------------------------------------------
# Item-level traversal (mirrors enrich_pdf_locations.py)
# ---------------------------------------------------------------------------

try:
    from search_queries import POC_ITEM_IDS as _SQ_POC
except Exception:
    _SQ_POC = ("hed_response_inhibition", "hed_working_memory_updating",
               "hedtsk_stroop_color_word")

POC_ITEM_IDS: tuple[str, ...] = tuple(_SQ_POC)


def _iter_items(
    processes: dict,
    tasks: list,
    mode: str,
    ids: list[str],
) -> Iterable[tuple[str, dict]]:
    procs = processes.get("processes", [])
    all_items: list[tuple[str, dict]] = []
    for p in procs:
        all_items.append((p.get("process_id", ""), p))
    for t in tasks:
        all_items.append((t.get("hedtsk_id", ""), t))

    if mode == "full":
        yield from all_items
    elif mode == "poc":
        wanted = set(POC_ITEM_IDS)
        for oid, item in all_items:
            if oid in wanted:
                yield oid, item
    elif mode == "single":
        wanted = set(ids)
        for oid, item in all_items:
            if oid in wanted:
                yield oid, item
    else:
        raise ValueError(f"unknown mode: {mode!r}")


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode", choices=["poc", "single", "full"], required=True,
                   help="poc=3 sample items, single=--ids, full=every item.")
    p.add_argument("--ids", default="",
                   help="Comma-separated owner IDs for --mode single.")
    p.add_argument("--workspace", default=".",
                   help="Workspace root (Claude-research/). Default: cwd.")
    p.add_argument("--cache-dir", default="<auto>",
                   help="Cache root. Default: $HED_CACHE_DIR or "
                        "<workspace>/outputs/cache.")
    p.add_argument("--email", default="hedannotation@gmail.com",
                   help="Polite-pool email for OpenAlex.")
    p.add_argument("--write", action="store_true",
                   help="Persist changes to process_details.json and task_details.json.")
    p.add_argument("--limit", type=int, default=0,
                   help="Cap the number of references processed (0 = no cap).")
    p.add_argument("--verbose", "-v", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    ws = Path(args.workspace).resolve()
    cache_dir = resolve_cache_dir(args.cache_dir, ws)
    cache_dir.mkdir(parents=True, exist_ok=True)
    logger.info("workspace : %s", ws)
    logger.info("cache_dir : %s", cache_dir)

    p_path = ws / "process_details.json"
    t_path = ws / "task_details.json"
    for path in (p_path, t_path):
        if not path.exists():
            logger.error("not found: %s", path)
            return 2

    with p_path.open("r", encoding="utf-8") as f:
        processes = json.load(f)
    with t_path.open("r", encoding="utf-8") as f:
        tasks = json.load(f)

    ids_arg = [i.strip() for i in args.ids.split(",") if i.strip()]
    items_iter = list(_iter_items(processes, tasks, args.mode, ids_arg))
    logger.info("items in scope (%s): %d", args.mode, len(items_iter))

    n_refs_seen      = 0
    n_refs_with_doi  = 0
    fills_per_slot: Counter[str] = Counter()
    all_conflicts: list[tuple[str, str, Conflict]] = []  # (owner_id, doi, conflict)

    for owner_id, item in items_iter:
        for ref in item.get("references") or []:
            n_refs_seen += 1
            if args.limit and n_refs_with_doi >= args.limit:
                break
            n_filled, conflicts, had_doi = enrich_one_reference(
                ref, cache_dir, args.email,
            )
            if not had_doi:
                continue
            n_refs_with_doi += 1

            # Count per-slot fills by inspecting what's now set vs what
            # apply_to_ref reported.  We get n_filled total back but the
            # per-slot breakdown is recoverable by re-comparing — cheaper
            # to track at apply time, but a tiny re-walk is fine here.
            # Instead, track by inspecting the candidate dict's keys at
            # the time of fill: re-do the lookup is wasteful, so we
            # accept that n_filled is total-only at the summary level
            # and report per-slot using a second pass below if needed.
            #
            # Pragmatic compromise: re-run the extract on the now-filled
            # ref's ids block to count populated slots vs the pre-call
            # state.  Simpler: just count current non-null ids slots.
            for slot in ("openalex_id", "pmid", "pmcid", "s2_id", "arxiv_id"):
                if (ref.get("ids") or {}).get(slot):
                    fills_per_slot[slot + "_present"] += 1

            for c in conflicts:
                doi = ref_doi(ref) or "<no-doi>"
                all_conflicts.append((owner_id, doi, c))

        if args.limit and n_refs_with_doi >= args.limit:
            break

    # ---- Summary
    print()
    print("ID enrichment summary:")
    print(f"  references seen           : {n_refs_seen}")
    print(f"  with DOI (processed)      : {n_refs_with_doi}")
    print(f"  conflicts (existing!=cand): {len(all_conflicts)}")
    print()
    print("  ids.<slot> non-null counts (post-enrichment):")
    for slot in ("openalex_id", "pmid", "pmcid", "s2_id", "arxiv_id"):
        print(f"    {slot:14s}  {fills_per_slot.get(slot + '_present', 0)}")

    if all_conflicts:
        print()
        print(f"Conflicts ({len(all_conflicts)}) — existing value KEPT; "
              f"candidate logged for review:")
        for owner_id, doi, (slot, existing, cand) in all_conflicts[:20]:
            print(f"  [{owner_id}] doi={doi}  {slot}: existing={existing!r}  "
                  f"candidate={cand!r}")
        if len(all_conflicts) > 20:
            print(f"  ... and {len(all_conflicts) - 20} more")

    # ---- Persist (only with --write)
    if args.write:
        scratch = ws / ".scratch" / "enrich_ids"
        scratch.mkdir(parents=True, exist_ok=True)
        staged_p = scratch / p_path.name
        staged_t = scratch / t_path.name

        with staged_p.open("w", encoding="utf-8") as f:
            json.dump(processes, f, indent=2, ensure_ascii=False)
            f.write("\n")
        with staged_t.open("w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)
            f.write("\n")

        # Round-trip parse check before clobbering the originals.
        with staged_p.open("r", encoding="utf-8") as f:
            _check_p = json.load(f)
        with staged_t.open("r", encoding="utf-8") as f:
            _check_t = json.load(f)
        if not isinstance(_check_p, dict) or "processes" not in _check_p:
            logger.error("staged process_details.json failed structural check")
            return 1
        if not isinstance(_check_t, list):
            logger.error("staged task_details.json failed structural check")
            return 1

        shutil.copyfile(staged_p, p_path)
        shutil.copyfile(staged_t, t_path)
        print()
        print(f"wrote: {p_path.name}")
        print(f"wrote: {t_path.name}")
    else:
        print()
        print("dry-run complete; pass --write to persist changes.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
