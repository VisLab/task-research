#!/usr/bin/env python3
"""
phase3_extract_review.py — Extract the picked tier from a candidates JSON
and produce a review skeleton, with rebase semantics against any existing
review file.

Inputs (per item):
    outputs/phase3/candidates/<item_id>.json   (always; written by phase3_search.py)
    outputs/phase3/review/<item_id>.json       (optional; preserved if present)

Output:
    outputs/phase3/review/<item_id>.json

Each output file contains:
    item               — duplicated catalog identity block (so the review
                          file is self-contained without the candidates file)
    candidates_run_date — from the candidates file's `generated` timestamp
    extracted_on        — when this extract step ran
    decisions[]         — one entry per picked-tier candidate, in rank order.
                          Pre-filled with action=null (= default-accept).
                          For each entry: rank, label, doi, pub_id, auto_role,
                          score (composite + breakdown), human_subject,
                          action, role_override, notes.
    previously_decided[] — only present after a rebase. Decisions whose
                          target is no longer in the picked tier are demoted
                          here so the audit trail isn't lost.

Rebase rules (when an existing review file is present):
  - Match prior decisions to current candidates by DOI first, pub_id second.
  - Surviving picks carry forward action/role_override/notes verbatim.
    Their `rank` field is updated to wherever they are in the new ranking.
  - Picks that no longer exist in the current candidates JSON, or that
    have moved out of the picked tier, are moved to `previously_decided`
    with a `rebase_note` explaining what happened.
  - New picks (in current picked tier but no prior decision) come in with
    action=null.

Usage:
    python code/literature_search/phase3_extract_review.py
    python code/literature_search/phase3_extract_review.py --item hed_response_inhibition
    python code/literature_search/phase3_extract_review.py --max-picked 20

Default behavior is to extract every candidates file in the candidates
directory. Use --item to scope to one. Default writes; pass --dry-run to
preview without writing.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


SCHEMA_VERSION = "phase3_review_v1"


# ---------------------------------------------------------------------------
# Label rendering — what the reviewer sees in `decisions[i].label`
# ---------------------------------------------------------------------------

def _format_citations(n: int | None) -> str:
    if n is None:
        return ""
    if n >= 1000:
        return f"{n//1000}k×"
    return f"{n}×"


def _venue_short(venue: str | None) -> str:
    if not venue:
        return "?"
    # Trim long journal names to a recognizable abbreviation, keeping
    # readability over precision (this is for human eyes only).
    venue = venue.strip()
    if len(venue) > 35:
        return venue[:32] + "…"
    return venue


def build_label(c: dict) -> str:
    """Return a human-readable one-line label for a picked candidate.

    Format: "FirstAuthor YEAR — Title... (Venue, role, NNN×)"
    """
    first = c.get("first_author") or "?"
    year  = c.get("year") or "????"
    title = (c.get("title") or "").strip()
    if len(title) > 80:
        title = title[:77] + "…"
    venue = _venue_short(c.get("venue"))
    role  = c.get("auto_role") or "?"
    cites = _format_citations(c.get("citation_count"))

    badges_parts: list[str] = [venue, role]
    if cites:
        badges_parts.append(cites)
    badges = ", ".join(p for p in badges_parts if p)

    return f"{first} {year} — {title} ({badges})"


# ---------------------------------------------------------------------------
# Decision-row construction
# ---------------------------------------------------------------------------

def build_decision_row(c: dict) -> dict:
    """Pre-populated decision row for one picked candidate."""
    return {
        "rank":          c.get("rank"),
        "label":         build_label(c),
        "doi":           c.get("doi"),
        "pub_id":        c.get("pub_id"),
        "auto_role":     c.get("auto_role"),
        "score":         c.get("score"),     # full breakdown carried forward
        "human_subject": c.get("human_subject"),
        "year":          c.get("year"),
        "venue":         c.get("venue"),
        "citation_count": c.get("citation_count"),
        # Decision fields — null by default (= accept the auto pick).
        "action":         None,
        "role_override":  None,
        "notes":          None,
    }


# ---------------------------------------------------------------------------
# Rebase
# ---------------------------------------------------------------------------

def _decision_key(entry: dict) -> str | None:
    """Return the matching key for a decision row.

    DOI first (lowercased, stripped), pub_id as fallback. Returns None if
    neither is available — those rows can't be rebased and will be
    treated as orphans.
    """
    doi = (entry.get("doi") or "").lower().strip()
    if doi:
        return f"doi:{doi}"
    pub_id = entry.get("pub_id")
    if pub_id:
        return f"pub:{pub_id}"
    return None


def _is_human_decision(entry: dict) -> bool:
    """A decision is 'human' if any of action / role_override / notes is set."""
    return bool(
        entry.get("action") is not None
        or entry.get("role_override") is not None
        or entry.get("notes")
    )


def rebase_decisions(
    new_picked: list[dict],
    prior_review: dict | None,
    current_candidates_by_key: dict[str, dict],
) -> tuple[list[dict], list[dict]]:
    """Apply rebase semantics; return (decisions, previously_decided).

    `new_picked` is the list of fresh decision rows built from the current
    picked tier. `prior_review` is the previous review JSON (or None on
    first extract). `current_candidates_by_key` is a lookup over ALL
    candidates in the current candidates JSON (any tier), keyed by
    `_decision_key`.

    For each prior decision:
      - If target is in new_picked AND the decision had user-set fields:
        carry the user fields forward into the matching new row.
      - Else if target is still in candidates but in a different tier
        (reserve / excluded): move to previously_decided with a note.
      - Else: target is gone entirely; move to previously_decided with a
        "no longer in candidates" note.
    """
    decisions = list(new_picked)  # mutable copy
    previously_decided: list[dict] = []

    if not prior_review:
        return decisions, previously_decided

    # Build a lookup over the new picked rows for fast carry-forward.
    new_by_key: dict[str, dict] = {}
    for row in decisions:
        k = _decision_key(row)
        if k:
            new_by_key[k] = row

    for prior in prior_review.get("decisions", []):
        if not _is_human_decision(prior):
            # No user input on this row; nothing to preserve.
            continue
        key = _decision_key(prior)
        if not key:
            previously_decided.append({
                **prior,
                "rebase_note": "could not match (no DOI or pub_id)",
                "current_tier": None,
            })
            continue

        # Survivor in picked tier: carry user fields forward.
        if key in new_by_key:
            target = new_by_key[key]
            target["action"]        = prior.get("action")
            target["role_override"] = prior.get("role_override")
            target["notes"]         = prior.get("notes")
            continue

        # Still in candidates but in a different tier?
        existing = current_candidates_by_key.get(key)
        if existing is not None:
            current_tier = existing.get("tier")
            previously_decided.append({
                **{k: v for k, v in prior.items() if k != "score"},
                "current_tier":  current_tier,
                "current_rank":  existing.get("rank"),
                "rebase_note": (
                    f"previously picked; now in {current_tier!r}. "
                    "Phase 6 ignores non-picked entries; promote it back "
                    "if you still want it included."
                ),
            })
            continue

        # Gone entirely.
        previously_decided.append({
            **{k: v for k, v in prior.items() if k != "score"},
            "current_tier":  None,
            "current_rank":  None,
            "rebase_note": (
                "no longer in current candidates (filter, query, or source "
                "no longer returns it)."
            ),
        })

    # Also rebase any prior previously_decided entries — drop ones that
    # have come back into picked (rare but possible) and otherwise carry
    # them forward.
    for prior_orphan in (prior_review.get("previously_decided", []) or []):
        key = _decision_key(prior_orphan)
        if not key:
            continue
        if key in new_by_key:
            # The orphan came back into picked. Promote its preserved
            # decision into the live decisions list.
            target = new_by_key[key]
            target["action"]        = prior_orphan.get("action")
            target["role_override"] = prior_orphan.get("role_override")
            target["notes"]         = prior_orphan.get("notes")
            continue
        previously_decided.append(prior_orphan)

    return decisions, previously_decided


# ---------------------------------------------------------------------------
# Per-item processing
# ---------------------------------------------------------------------------

def extract_one(
    candidates_path: Path,
    review_dir: Path,
    write: bool,
    max_picked: int | None,
) -> tuple[Path, dict]:
    """Extract review skeleton from one candidates JSON.

    Returns (output_path, summary_dict).
    """
    with candidates_path.open("r", encoding="utf-8") as f:
        cand_doc = json.load(f)

    item = cand_doc.get("item") or {}
    item_id = item.get("id")
    if not item_id:
        raise ValueError(f"candidates file {candidates_path} missing item.id")

    all_candidates = cand_doc.get("candidates") or []
    picked = [c for c in all_candidates if c.get("tier") == "picked"]

    # Optional cap below the run's natural picked-tier size.
    if max_picked is not None and len(picked) > max_picked:
        picked = picked[:max_picked]

    new_decisions = [build_decision_row(c) for c in picked]

    # Build candidate lookup for rebase.
    by_key: dict[str, dict] = {}
    for c in all_candidates:
        k = _decision_key(c)
        if k:
            by_key[k] = c

    # Read prior review file if present.
    review_dir = Path(review_dir)
    review_path = review_dir / f"{item_id}.json"
    prior_review: dict | None = None
    if review_path.exists():
        try:
            with review_path.open("r", encoding="utf-8") as f:
                prior_review = json.load(f)
        except json.JSONDecodeError as exc:
            print(
                f"WARN: existing review file {review_path} does not parse: {exc}; "
                f"starting from a fresh skeleton.",
                file=sys.stderr,
            )
            prior_review = None

    decisions, previously_decided = rebase_decisions(
        new_decisions, prior_review, by_key,
    )

    review_doc: dict = {
        "schema_version":      SCHEMA_VERSION,
        "item":                item,
        "candidates_run_date": cand_doc.get("generated"),
        "extracted_on":        datetime.now().isoformat(timespec="seconds"),
        "extraction": {
            "max_picked": max_picked,
            "n_picked":   len(decisions),
        },
        "decisions":           decisions,
    }
    if previously_decided:
        review_doc["previously_decided"] = previously_decided

    summary = {
        "item_id":             item_id,
        "n_decisions":         len(decisions),
        "n_previously_decided": len(previously_decided),
        "n_carried_forward":   sum(
            1 for d in decisions
            if d.get("action") is not None
            or d.get("role_override") is not None
            or d.get("notes")
        ),
    }

    if write:
        review_dir.mkdir(parents=True, exist_ok=True)
        with review_path.open("w", encoding="utf-8", newline="\n") as f:
            json.dump(review_doc, f, ensure_ascii=False, indent=2)
            f.write("\n")

    return review_path, summary


# ---------------------------------------------------------------------------
# CLI driver
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workspace", default=".",
                    help="Workspace root (default: cwd)")
    ap.add_argument("--candidates-dir", default="outputs/phase3/candidates",
                    help="Where the candidates JSONs live (relative to workspace).")
    ap.add_argument("--review-dir", default="outputs/phase3/review",
                    help="Where to write review JSONs (relative to workspace).")
    ap.add_argument("--item", default="",
                    help="Single item_id to process; default is all candidates files.")
    ap.add_argument("--max-picked", type=int, default=None,
                    help="Override the n_picked from the candidates run. "
                         "If set, only the top N picked candidates appear "
                         "in the review file.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print summary but do not write review files.")
    args = ap.parse_args()

    ws = Path(args.workspace).resolve()
    cand_dir = ws / args.candidates_dir
    rev_dir  = ws / args.review_dir

    if not cand_dir.exists():
        print(f"ERROR: candidates dir not found: {cand_dir}", file=sys.stderr)
        return 2

    if args.item:
        cand_files = [cand_dir / f"{args.item}.json"]
    else:
        cand_files = sorted(cand_dir.glob("*.json"))
        if not cand_files:
            print(f"ERROR: no candidates files in {cand_dir}", file=sys.stderr)
            return 2

    write = not args.dry_run
    print(f"Extracting review skeletons for {len(cand_files)} item(s).")
    print(f"  candidates dir : {cand_dir}")
    print(f"  review dir     : {rev_dir}")
    print(f"  max_picked     : {args.max_picked!r}")
    print(f"  write          : {write}")
    print()

    total_decisions = 0
    total_carried   = 0
    total_orphans   = 0
    for cf in cand_files:
        if not cf.exists():
            print(f"  MISSING: {cf}")
            continue
        try:
            out_path, summary = extract_one(
                cf, rev_dir, write=write, max_picked=args.max_picked,
            )
        except (ValueError, KeyError) as exc:
            print(f"  ERROR processing {cf.name}: {exc}", file=sys.stderr)
            continue
        total_decisions += summary["n_decisions"]
        total_carried   += summary["n_carried_forward"]
        total_orphans   += summary["n_previously_decided"]
        print(
            f"  {summary['item_id']:40s}  "
            f"decisions={summary['n_decisions']:3d}  "
            f"carried_forward={summary['n_carried_forward']:3d}  "
            f"previously_decided={summary['n_previously_decided']:3d}"
        )

    print()
    print(f"Total decisions: {total_decisions}")
    print(f"Total carried forward from prior review: {total_carried}")
    print(f"Total previously_decided (orphaned): {total_orphans}")
    if not write:
        print("DRY RUN — no files written. Re-run without --dry-run to write.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
