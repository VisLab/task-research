"""
tier_classify.py — Assign each ranked candidate a tier: picked / reserve / excluded.

Run after `composite_score` has been applied to every candidate and the
species classifier has set `human_subject` and `species_evidence` on each.

Inputs:
    ranked        — list[Candidate], sorted by composite_score descending.
    historical_pub_ids — landmarks; always go to picked (regardless of score).
    n_picked      — target picked-tier size (default 30).
    n_reserve     — target reserve-tier size below the picked cutoff
                     (default 30).
    drop_unknown_species — when True, candidates with human_subject == None
                           are sent to excluded with reason "unknown_species".
                           Default False (be conservative — keep them in pool).

Mutations:
    Sets each candidate's `tier` to one of "picked" | "reserve" | "excluded"
    and, when excluded, sets `exclusion_reason` to a stable string code.

Returns:
    A summary dict for logging:
      {"picked": N, "reserve": M, "excluded": K,
       "exclusion_reasons": {"non_human_subjects": ..., ...}}
"""

from __future__ import annotations

from collections import Counter

from normalize import Candidate


# Stable exclusion reason codes. The serializer copies these into the JSON
# output verbatim; downstream tools may filter on them.
EXCL_NON_HUMAN     = "non_human_subjects"
EXCL_UNKNOWN_SPEC  = "unknown_species"
EXCL_NO_YEAR_NO_DOI = "no_year_no_doi"
EXCL_BELOW_THRESHOLD = "below_score_threshold"
EXCL_BELOW_RESERVE   = "below_reserve_cutoff"


def assign_tiers(
    ranked: list[Candidate],
    historical_pub_ids: set[str],
    n_picked: int = 30,
    n_reserve: int = 30,
    drop_unknown_species: bool = False,
    min_picked_score: float | None = None,
) -> dict:
    """Mutate each candidate's `tier` and `exclusion_reason` in place.

    Args:
        min_picked_score: If set, candidates whose composite_score is below
            this floor are sent to excluded with reason "below_score_threshold"
            even if they would otherwise have made the picked-tier slot count.
            Useful for items with thin literature where picking 30 would
            include weak matches.
    """
    summary = {"picked": 0, "reserve": 0, "excluded": 0, "exclusion_reasons": Counter()}

    # Pass 1: hard exclusions independent of ranking position.
    for c in ranked:
        if c.year is None and not c.doi:
            c.tier = "excluded"
            c.exclusion_reason = EXCL_NO_YEAR_NO_DOI
            summary["exclusion_reasons"][EXCL_NO_YEAR_NO_DOI] += 1
            continue

        if c.human_subject is False:
            # Decisive non-human signal.
            c.tier = "excluded"
            c.exclusion_reason = EXCL_NON_HUMAN
            summary["exclusion_reasons"][EXCL_NON_HUMAN] += 1
            continue

        if drop_unknown_species and c.human_subject is None:
            c.tier = "excluded"
            c.exclusion_reason = EXCL_UNKNOWN_SPEC
            summary["exclusion_reasons"][EXCL_UNKNOWN_SPEC] += 1
            continue

        # Provisional: not yet assigned. Pass 2 handles picked/reserve.
        c.tier = None

    # Pass 2: assign picked/reserve to the still-unclassified ranked tail.
    # Historical landmarks go to picked unconditionally (provided they
    # weren't hard-excluded above, which would only happen for missing
    # year+DOI — landmarks should always have those).
    eligible = [c for c in ranked if c.tier is None]
    eligible.sort(key=lambda c: c.composite_score or 0.0, reverse=True)

    picked_count = 0
    reserve_count = 0
    for c in eligible:
        is_landmark = c.pub_id in historical_pub_ids

        if is_landmark and picked_count < n_picked:
            c.tier = "picked"
            picked_count += 1
            continue

        if (
            picked_count < n_picked
            and (min_picked_score is None or (c.composite_score or 0.0) >= min_picked_score)
        ):
            c.tier = "picked"
            picked_count += 1
            continue

        if (
            picked_count < n_picked
            and min_picked_score is not None
            and (c.composite_score or 0.0) < min_picked_score
        ):
            # Slot was available but score too low; this candidate falls
            # to reserve or excluded depending on whether reserve has space.
            if reserve_count < n_reserve:
                c.tier = "reserve"
                reserve_count += 1
            else:
                c.tier = "excluded"
                c.exclusion_reason = EXCL_BELOW_THRESHOLD
                summary["exclusion_reasons"][EXCL_BELOW_THRESHOLD] += 1
            continue

        if reserve_count < n_reserve:
            c.tier = "reserve"
            reserve_count += 1
            continue

        c.tier = "excluded"
        c.exclusion_reason = EXCL_BELOW_RESERVE
        summary["exclusion_reasons"][EXCL_BELOW_RESERVE] += 1

    summary["picked"]   = sum(1 for c in ranked if c.tier == "picked")
    summary["reserve"]  = sum(1 for c in ranked if c.tier == "reserve")
    summary["excluded"] = sum(1 for c in ranked if c.tier == "excluded")
    summary["exclusion_reasons"] = dict(summary["exclusion_reasons"])
    return summary
