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
from triage_rules import classify_venue


# Stable exclusion reason codes. The serializer copies these into the JSON
# output verbatim; downstream tools may filter on them.
EXCL_NON_HUMAN     = "non_human_subjects"
EXCL_UNKNOWN_SPEC  = "unknown_species"
EXCL_NO_YEAR_NO_DOI = "no_year_no_doi"
EXCL_BELOW_THRESHOLD = "below_score_threshold"
EXCL_BELOW_RESERVE   = "below_reserve_cutoff"
EXCL_CONFERENCE      = "conference_or_proceedings"
EXCL_PREPRINT        = "preprint"
EXCL_LOW_VENUE       = "low_quality_venue"
EXCL_PUBLISHER       = "excluded_publisher"


# Publication-type tokens that mark a candidate as a conference/proceedings
# paper rather than a journal article. Match is case-insensitive substring;
# any hit excludes the candidate, even when JournalArticle is also present
# (S2 frequently double-tags hybrid venues like LNCS or Procedia).
_CONFERENCE_PATTERNS: tuple[str, ...] = (
    "conference",
    "proceedings-article",
    "proceedingsarticle",
    "proceedings article",
    "meeting-abstract",
    "meeting abstract",
    "meetingabstract",
)

# Venue-string fallback for conferences when the type tag is missing.
# S2 frequently tags ICLR/NeurIPS/ICML/AAAI papers as JournalArticle,
# so the type filter alone misses them. These substrings are matched
# case-insensitively against the candidate's venue.
#
# Patterns are conservative — they don't appear in legitimate journal
# names (so e.g. "Proceedings of the National Academy of Sciences" is
# untouched, but "Proceedings of the IEEE/CVF Conference on..." is caught).
# Add to this list when an ML/cog-sci conference proceeding leaks through.
_CONFERENCE_VENUE_PATTERNS: tuple[str, ...] = (
    "conference on",
    "workshop on",
    "international conference",
    "annual conference",
    "annual workshop",
    "international workshop",
    "advances in neural information processing systems",  # NeurIPS proceedings
    "ieee/cvf",                                            # CVPR/ICCV/WACV
    "ieee international conference",
    "acm international conference",
    "acm conference on",
    "acm symposium on",
    "european conference on",
    "asian conference on",
    "uist proceedings",                                    # ACM UIST
    "chi conference",                                      # ACM CHI
    "neurips proceedings",
    "icml proceedings",
    "iclr proceedings",
)

# Publication-type tokens that mark a candidate as a preprint. Different
# sources use different vocabularies for "this hasn't been peer-reviewed
# in a journal yet"; we match all of them.
_PREPRINT_TYPE_PATTERNS: tuple[str, ...] = (
    "preprint",
    "posted-content",
    "postedcontent",
    "posted content",
)

# Venue substrings that identify a preprint server even when the type tag
# is missing or wrong (S2 sometimes labels arXiv papers as JournalArticle).
# Case-insensitive substring match.
_PREPRINT_VENUE_PATTERNS: tuple[str, ...] = (
    "arxiv",
    "biorxiv",
    "medrxiv",
    "psyarxiv",
    "chemrxiv",
    "research square",
    "researchsquare",
    "ssrn",
    "preprints.org",
    "osf preprints",
)


def _is_conference_or_proceedings(c) -> bool:
    """True if any signal flags this candidate as a conference / proceedings
    paper.

    Two signals, either is sufficient:
      1. publication_types contains a conference-flavored tag.
      2. The venue string contains a conference-suggestive substring (used
         when sources fail to tag, which S2 does for ML conferences).
    """
    # Signal 1: type tags
    for pt in (c.publication_types or []):
        ptl = pt.lower()
        for pattern in _CONFERENCE_PATTERNS:
            if pattern in ptl:
                return True

    # Signal 2: venue string
    venue = (c.venue or "").lower()
    if venue:
        for pattern in _CONFERENCE_VENUE_PATTERNS:
            if pattern in venue:
                return True
    return False


def _is_preprint(c) -> bool:
    """True if the candidate is a preprint, by any of three signals.

    1. publication_types contains a preprint-flavored tag.
    2. DOI uses the arXiv canonical prefix `10.48550/arxiv`.
    3. Venue string contains a known preprint-server name.
    """
    for pt in (c.publication_types or []):
        ptl = pt.lower()
        for pattern in _PREPRINT_TYPE_PATTERNS:
            if pattern in ptl:
                return True

    doi = (c.doi or "").lower()
    if doi.startswith("10.48550/arxiv"):
        return True

    venue = (c.venue or "").lower()
    if not venue:
        return False
    for pattern in _PREPRINT_VENUE_PATTERNS:
        if pattern in venue:
            return True
    return False


def _is_low_quality_venue(c) -> bool:
    """True if the venue is in the curated low/excluded tier
    (predatory, mill, retracted-heavy, or otherwise off-strategy).
    'unknown' venues are NOT excluded — too many legitimate journals
    aren't in the curated list, so unknown is treated as neutral."""
    return classify_venue(c.venue) == "low_or_excluded"


# DOI prefixes for publishers we want to exclude wholesale, regardless of
# venue or topic. Keep this list short and well-justified — each entry
# rejects every paper from that publisher across the whole catalog.
#
# 2026-04-28: MDPI, Bentham, OMICS added at user request. Each prefix is
# exclusive to its publisher, so the match is unambiguous (no journal at
# a different publisher uses the same DOI prefix).
_EXCLUDED_DOI_PREFIXES: tuple[str, ...] = (
    "10.3390/",   # MDPI    (Sensors, Brain Sciences, IJMS, Behavioral Sciences, ...)
    "10.2174/",   # Bentham (Bentham Science / Bentham Open)
    "10.4172/",   # OMICS   (OMICS Publishing Group / OMICS International)
)

# Publisher-string fallback for records that lack a DOI but have a publisher
# name. Matched as case-insensitive substring against c.publisher.
#
# Each entry must be specific enough to avoid false positives. Plain "omics"
# is unsafe (catches "genomics"/"proteomics"/etc. in venue strings or in
# legitimate journals that happen to have "omics" in their publisher name);
# we match the longer "omics publishing" / "omics international" instead.
_EXCLUDED_PUBLISHER_NAMES: tuple[str, ...] = (
    "mdpi",
    "bentham science",
    "bentham open",
    "omics publishing",
    "omics international",
)


def _is_excluded_publisher(c) -> bool:
    """True if the candidate's publisher is on the exclusion list.

    Two signals, either is sufficient:
      1. DOI starts with a publisher's exclusive DOI prefix.
      2. Publisher string contains the publisher's name (case-insensitive).
    """
    doi = (c.doi or "").lower()
    for prefix in _EXCLUDED_DOI_PREFIXES:
        if doi.startswith(prefix):
            return True
    publisher = (c.publisher or "").lower()
    if publisher:
        for name in _EXCLUDED_PUBLISHER_NAMES:
            if name in publisher:
                return True
    return False


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

        if _is_conference_or_proceedings(c):
            # Even if the paper is also tagged JournalArticle, any
            # conference/proceedings tag excludes it. The HED catalog is
            # journal-and-review focused.
            c.tier = "excluded"
            c.exclusion_reason = EXCL_CONFERENCE
            summary["exclusion_reasons"][EXCL_CONFERENCE] += 1
            continue

        if _is_preprint(c):
            # arXiv, bioRxiv, etc. — kept out of the picked tier; reviewers
            # can promote one back from reserve if a particular preprint
            # is genuinely the canonical reference for an item.
            c.tier = "excluded"
            c.exclusion_reason = EXCL_PREPRINT
            summary["exclusion_reasons"][EXCL_PREPRINT] += 1
            continue

        if _is_low_quality_venue(c):
            c.tier = "excluded"
            c.exclusion_reason = EXCL_LOW_VENUE
            summary["exclusion_reasons"][EXCL_LOW_VENUE] += 1
            continue

        if _is_excluded_publisher(c):
            c.tier = "excluded"
            c.exclusion_reason = EXCL_PUBLISHER
            summary["exclusion_reasons"][EXCL_PUBLISHER] += 1
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
