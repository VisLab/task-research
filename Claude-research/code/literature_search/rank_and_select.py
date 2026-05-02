"""
rank_and_select.py — Deduplication, composite scoring, candidate selection.

Implements the scoring formula from instructions/search_strategy_decisions_2026-04-24.md §8.
Weights are NOT to be changed without explicit user approval.

v3 changes (all authorised per design doc §8.4):
  - W_CITATION / W_VENUE / W_PUBLISHER / W_RECENCY / W_RELEVANCE / W_REVIEW
    weights updated.
  - Citation component is now a blend of total and influential citation counts.
  - Relevance score is phrase-count over title + abstract + TLDR (not word overlap).
  - phrase_gate() added: post-retrieval TLDR-aware topicality filter.
  - select_citation_seeds() added: Stage B seed selection.
  - _influence_intent_bump() added: per-edge Stage B boost.

Imports:
    from rank_and_select import (
        dedup_candidates, composite_score, select_candidates,
        phrase_gate, select_citation_seeds,
    )
"""

import math
import re
from dataclasses import replace

from normalize import Candidate
from search_queries import ItemQueryPlan
from triage_rules import classify_venue, publisher_tier_from_doi


# ---------------------------------------------------------------------------
# §8.1 score weights (locked — do not modify without user sign-off)
# ---------------------------------------------------------------------------
W_CITATION           = 0.25
W_VENUE              = 0.20
W_PUBLISHER          = 0.10
W_RECENCY            = 0.15
W_RELEVANCE          = 0.25
W_REVIEW             = 0.05
# Sum of base weights == 1.00

W_INFLUENCE_INTENT   = 0.05   # per strong Stage-B edge; capped at INFLUENCE_INTENT_CAP
INFLUENCE_INTENT_CAP = 3      # maximum edges counted toward the bump
LM_BONUS             = 0.30   # landmark bonus for historical pub_ids

VENUE_SCORES     = {"flagship": 1.0, "mainstream": 0.7, "specialty": 0.4,
                    "low_or_excluded": 0.0, "unknown": 0.3}
PUBLISHER_SCORES = {"A": 1.0, "B": 0.6, "C": 0.0, None: 0.0}


# ---------------------------------------------------------------------------
# Tokenisation (shared by phrase gate and relevance scorer)
# ---------------------------------------------------------------------------

_STOP_WORDS = frozenset(["", "the", "a", "an", "of", "and", "in", "to", "for",
                          "with", "on", "at", "by", "from", "as"])


def _tokenize(text: str) -> set[str]:
    return set(re.split(r"[^a-z0-9]+", text.lower())) - _STOP_WORDS


# ---------------------------------------------------------------------------
# Phrase list extraction
# ---------------------------------------------------------------------------

def _alias_text(a) -> str:
    """Extract a plain string from an alias regardless of whether it is a str
    (task aliases) or a dict with a 'name' key (process aliases)."""
    if isinstance(a, str):
        return a
    if isinstance(a, dict):
        return a.get("name") or ""
    return ""


# Single-token aliases at or below this character length are dropped from
# the phrase list. They tokenize as standalone "words" in the phrase gate
# and as substring matches in the relevance scorer, and short tokens are
# almost always abbreviations that collide with unrelated literature. For
# example, "FER" (Facial Emotion Recognition) tokenizes against any paper
# that abbreviates FERONIA receptor kinase as "FER", or that mentions
# "Fer-1" (ferrostatin-1), and contaminates the picked tier with plant
# biology and ferroptosis papers. Same risk for "FC", "PD", "DG", "RAT",
# "SST", and dozens of similar 2-3 letter task acronyms.
#
# Multi-word aliases ("Ekman Faces Task") and longer single-word aliases
# ("Mentalizing", "Vigilance", "OSPAN") are unaffected.
#
# 2026-04-28: cutoff set to 4. Diagnosed via hedtsk_facial_emotion_recognition
# returning 35+ plant-biology papers in the picked tier under the "FER" alias.
_MIN_SINGLE_TOKEN_ALIAS_LEN = 4


def _phrase_list(item: ItemQueryPlan) -> list[str]:
    """Return the primary name plus all alias strings safe for the phrase
    gate and relevance scorer.

    Aliases that are single-token AND ≤ 4 characters are dropped (see
    `_MIN_SINGLE_TOKEN_ALIAS_LEN`). Multi-word aliases and longer
    single-token aliases pass through unchanged. The primary name is
    always included regardless of length.
    """
    phrases: list[str] = [item.primary_name]
    for a in (item.aliases or []):
        s = _alias_text(a).strip()
        if not s:
            continue
        if " " not in s and len(s) <= _MIN_SINGLE_TOKEN_ALIAS_LEN:
            # Suspected short abbreviation — skip.
            continue
        phrases.append(s)
    return phrases


# ---------------------------------------------------------------------------
# Component helpers
# ---------------------------------------------------------------------------

def _log_norm(count: int) -> float:
    """Map a citation count to [0, 1] via log scale.

    Ceiling at 1000 citations (log_norm(1000) == 1.0).
    Papers with zero citations score 0.0.
    """
    if count <= 0:
        return 0.0
    return math.log1p(count) / math.log1p(1000)


def _citation_component(cand: Candidate) -> float:
    """Blended citation score: 0.4 × log_norm(total) + 0.6 × log_norm(influential).

    Influential weighted more because it is the sharper signal.  Total retained
    as a backstop for papers S2's classifier has not yet tagged.
    """
    total = _log_norm(cand.citation_count or 0)
    infl  = _log_norm(cand.influential_citation_count or 0)
    return 0.4 * total + 0.6 * infl


def _recency_score(cand: Candidate, today_year: int) -> float:
    """Triangular function: 0 at today-20, peak 1.0 at today-5, 0 above today."""
    year = cand.year
    if year is None:
        return 0.0
    peak       = today_year - 5
    zero_below = today_year - 20
    if year >= today_year:
        return 0.5  # treat future-stamped records as neutral
    if year <= zero_below:
        return 0.0
    if year <= peak:
        return (year - zero_below) / (peak - zero_below)
    return 1.0 - (year - peak) / (today_year - peak)


def _relevance_score(cand: Candidate, item: ItemQueryPlan) -> float:
    """Phrase-count relevance in [0, 1].

    Counts how many of the item's phrases (primary name + aliases) appear in
    the concatenation of the candidate's title, abstract, and TLDR.  A phrase
    matches if the whole multi-word string is present as a substring (case
    insensitive) for multi-word phrases, or if the single token is present in
    the tokenized text for single-word terms.

    Returns hits / total_phrases, or 0.0 if there are no phrases.
    """
    phrases = _phrase_list(item)
    if not phrases:
        return 0.0
    text = (
        (cand.title or "") + " " +
        (cand.abstract or "") + " " +
        (cand.tldr or "")
    ).lower()
    hits = 0
    for phrase in phrases:
        p = phrase.lower().strip()
        if not p:
            continue
        if " " in p:
            if p in text:
                hits += 1
        else:
            if p in _tokenize(text):
                hits += 1
    return hits / len(phrases)


def _venue_score(cand: Candidate) -> float:
    return VENUE_SCORES[classify_venue(cand.venue)]


def _publisher_score(cand: Candidate) -> float:
    return PUBLISHER_SCORES[publisher_tier_from_doi(cand.doi)]


def _review_bonus(cand: Candidate) -> float:
    return 1.0 if (cand.is_review or cand.is_meta_analysis) else 0.0


# ---------------------------------------------------------------------------
# Stage B influence-and-intent bump
# ---------------------------------------------------------------------------

_STRONG_INTENTS = {"background", "methodology", "extension"}


def _influence_intent_bump(cand: Candidate) -> float:
    """Additional score for Stage-B candidates with strong citation edges.

    Iterates over ``cand.stage_b_edges``.  An edge is strong if
    ``is_influential == True`` or if its ``intents`` set intersects
    {background, methodology, extension}.

    Bump = W_INFLUENCE_INTENT × min(strong_edge_count, INFLUENCE_INTENT_CAP).
    Returns 0.0 for Stage-A-only candidates (empty edge list).
    """
    strong = 0
    for edge in cand.stage_b_edges:
        if edge.get("is_influential"):
            strong += 1
            continue
        intents = {str(i).lower() for i in (edge.get("intents") or [])}
        if intents & _STRONG_INTENTS:
            strong += 1
    return W_INFLUENCE_INTENT * min(strong, INFLUENCE_INTENT_CAP)


# ---------------------------------------------------------------------------
# Composite score (public)
# ---------------------------------------------------------------------------

def composite_score(
    cand: Candidate,
    item: ItemQueryPlan,
    today_year: int,
    landmark_pub_ids: set[str],
    neutralize_recency: bool = False,
) -> float:
    """Compute composite score per design doc §8.

    Args:
        landmark_pub_ids:  Set of pub_ids that receive the +0.30 landmark bonus.
        neutralize_recency: When True, fix recency component at 0.5 (used for
            the top-candidates slot selection so old landmark papers are not
            penalised by the recency term).

    Equivalent to score_with_components(...)["composite"]; retained as the
    shorter call site when components aren't needed.
    """
    return score_with_components(
        cand, item, today_year, landmark_pub_ids, neutralize_recency,
    )["composite"]


def score_with_components(
    cand: Candidate,
    item: ItemQueryPlan,
    today_year: int,
    landmark_pub_ids: set[str],
    neutralize_recency: bool = False,
) -> dict:
    """Compute the composite score AND surface every contributing component.

    Returns a dict shaped like::

        {
          "composite": 0.935,
          "components": {
              "citations":         0.78,   # raw component (before W_*)
              "venue":             1.0,
              "publisher":         0.6,
              "recency":           0.4,
              "relevance":         0.92,
              "review":            1.0,
          },
          "weighted": {
              "citations":         W_CITATION   * 0.78,
              "venue":             W_VENUE      * 1.0,
              ...
          },
          "stage_b_bump":          0.10,    # already weighted (additive)
          "landmark_bonus":        0.0,     # 0 or LM_BONUS
          "neutralize_recency":    False,
        }

    The downstream JSON serializer stores both the raw components (so we
    can re-score under different weights without re-fetching) and the
    weighted values (so a reader can see at a glance which weighted term
    dominated). Sum of `weighted` + `stage_b_bump` + `landmark_bonus`
    equals `composite`.
    """
    citations = _citation_component(cand)
    venue     = _venue_score(cand)
    publisher = _publisher_score(cand)
    recency   = 0.5 if neutralize_recency else _recency_score(cand, today_year)
    relevance = _relevance_score(cand, item)
    review    = _review_bonus(cand)

    weighted = {
        "citations":  W_CITATION   * citations,
        "venue":      W_VENUE      * venue,
        "publisher":  W_PUBLISHER  * publisher,
        "recency":    W_RECENCY    * recency,
        "relevance":  W_RELEVANCE  * relevance,
        "review":     W_REVIEW     * review,
    }
    stage_b_bump = _influence_intent_bump(cand)
    landmark_bonus = LM_BONUS if cand.pub_id in landmark_pub_ids else 0.0

    composite = sum(weighted.values()) + stage_b_bump + landmark_bonus

    return {
        "composite": composite,
        "components": {
            "citations":  citations,
            "venue":      venue,
            "publisher":  publisher,
            "recency":    recency,
            "relevance":  relevance,
            "review":     review,
        },
        "weighted": weighted,
        "stage_b_bump":      stage_b_bump,
        "landmark_bonus":    landmark_bonus,
        "neutralize_recency": neutralize_recency,
    }


# ---------------------------------------------------------------------------
# Post-retrieval phrase gate
# ---------------------------------------------------------------------------

def phrase_gate(
    candidates: list[Candidate],
    item: ItemQueryPlan,
    historical_pub_ids: set[str],
    historical_dois: set[str],
) -> list[Candidate]:
    """Drop candidates whose title + abstract + TLDR contain no item phrase.

    Historical landmarks (by pub_id or DOI) are always exempt and pass
    through regardless of phrase matching.  This prevents the gate from
    accidentally removing a landmark paper whose vocabulary predates the
    modern phrase (e.g. Logan & Cowan 1984).

    The gate is applied to both Stage A and Stage B candidates.
    """
    phrases = [p.lower().strip() for p in _phrase_list(item) if p]
    kept: list[Candidate] = []

    for c in candidates:
        # Always keep historical landmarks.
        if c.pub_id in historical_pub_ids:
            kept.append(c)
            continue
        if c.doi and c.doi.lower() in historical_dois:
            kept.append(c)
            continue

        text = (
            (c.title or "") + " " +
            (c.abstract or "") + " " +
            (c.tldr or "")
        ).lower()

        matched = False
        for p in phrases:
            if not p:
                continue
            if " " in p and p in text:
                matched = True
                break
            if " " not in p and p in _tokenize(text):
                matched = True
                break

        if matched:
            kept.append(c)

    return kept


# ---------------------------------------------------------------------------
# Auto-role assignment
# ---------------------------------------------------------------------------

def assign_auto_role(cand: Candidate, today_year: int, landmark_pub_ids: set[str]) -> str:
    """Assign a coarse role label to a candidate.

    The role is a hint to the reviewer ("here's why the ranker thinks this
    is in the list"), not a filter. The reviewer can override it via the
    review file's `role_override` field.

    Decision order (first match wins):
      historical      — pub_id is in the curated historical landmark set.
      key_review      — is_review or is_meta_analysis is true.
      recent_primary  — year is within the last 8 years.
      foundational    — anything else (typically older primary research).

    The "methods" role exists in the role vocabulary but is not auto-assigned
    here; methods papers are hard to detect heuristically. Reviewers can set
    role_override = "methods" by hand.
    """
    if cand.pub_id in landmark_pub_ids:
        return "historical"
    if cand.is_review or cand.is_meta_analysis:
        return "key_review"
    if cand.year is not None and cand.year >= today_year - 8:
        return "recent_primary"
    return "foundational"


# ---------------------------------------------------------------------------
# Stage B seed selection
# ---------------------------------------------------------------------------

def select_citation_seeds(
    candidates: list[Candidate],
    historical_pub_ids: set[str],
    top_k: int = 50,
) -> list[Candidate]:
    """Select the top-K Stage A candidates to use as Stage B citation seeds.

    Seeds are ranked by ``influential_citation_count`` (descending).  A paper
    with high total citations but low influential counts is a poor seed because
    it is widely-cited-in-passing; influential count reflects non-trivial
    citation by the S2 classifier.

    Exclusions:
      - Historical landmarks: their Stage B budget is wasted; they are
        guaranteed via the landmark bonus.
      - Candidates without an s2_paper_id: we cannot call the citations
        endpoint without a paperId.
    """
    pool = [
        c for c in candidates
        if c.pub_id not in historical_pub_ids
        and c.s2_paper_id
    ]
    pool.sort(
        key=lambda c: c.influential_citation_count or 0,
        reverse=True,
    )
    return pool[:top_k]


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def dedup_candidates(candidates: list[Candidate]) -> list[Candidate]:
    """Deduplicate candidates across sources.

    Priority: DOI match > pub_id match (derived from author+year+title).
    When two records share a DOI, merge them preferring OpenAlex for most
    fields, EuropePMC for mesh/pmid, Semantic Scholar for S2-specific fields.
    Drop records with neither DOI nor year (likely database artifacts).
    """
    by_doi: dict[str, list[Candidate]] = {}
    no_doi: list[Candidate] = []

    for cand in candidates:
        if cand.doi:
            by_doi.setdefault(cand.doi.lower(), []).append(cand)
        else:
            no_doi.append(cand)

    merged: list[Candidate] = [_merge(g) for g in by_doi.values()]

    by_pub_id: dict[str, list[Candidate]] = {}
    for cand in no_doi:
        by_pub_id.setdefault(cand.pub_id, []).append(cand)
    merged += [_merge(g) for g in by_pub_id.values()]

    # Drop candidates that have no year AND no doi — likely artifacts.
    merged = [c for c in merged if not (c.year is None and c.doi is None)]
    return merged


def _merge(group: list[Candidate]) -> Candidate:
    """Merge a list of Candidate records for the same paper into one."""
    if len(group) == 1:
        return group[0]

    oa_rec  = next((c for c in group if "openalex"       in c.sources), None)
    epm_rec = next((c for c in group if "europepmc"      in c.sources), None)
    s2_rec  = next((c for c in group if "semanticscholar" in c.sources
                    or "semanticscholar_citations" in c.sources), None)

    base = oa_rec or epm_rec or s2_rec or group[0]

    # Prefer EuropePMC for pmid and mesh_terms.
    pmid       = (epm_rec and epm_rec.pmid)       or base.pmid
    mesh_terms = (epm_rec and epm_rec.mesh_terms) or base.mesh_terms

    # Prefer S2 for influential_citation_count, tldr, s2_paper_id.
    inf_cites   = (s2_rec and s2_rec.influential_citation_count) or base.influential_citation_count
    tldr        = (s2_rec and s2_rec.tldr)         or base.tldr
    s2_paper_id = (s2_rec and s2_rec.s2_paper_id)  or base.s2_paper_id

    # Prefer OpenAlex for OA info.
    oa_status = (oa_rec and oa_rec.oa_status) or base.oa_status
    oa_url    = (oa_rec and oa_rec.oa_url)    or base.oa_url

    # Union source lists.
    all_sources: list[str] = []
    for c in group:
        for s in c.sources:
            if s not in all_sources:
                all_sources.append(s)

    # Union stage_b_edges lists.
    all_edges: list[dict] = []
    seen_edges: set[str] = set()
    for c in group:
        for edge in c.stage_b_edges:
            key = edge.get("seed_pub_id", "") + "|" + str(edge.get("is_influential"))
            if key not in seen_edges:
                all_edges.append(edge)
                seen_edges.add(key)

    # Union publication_types across sources. Different sources use different
    # vocabularies (OpenAlex's "journal-article" vs S2's "JournalArticle" vs
    # EPMC's "research-article") — keep them all so the conference/proceedings
    # filter can fire on any source's tag.
    all_pub_types: list[str] = []
    seen_pub_types: set[str] = set()
    for c in group:
        for pt in (c.publication_types or []):
            key = pt.lower()
            if key not in seen_pub_types:
                all_pub_types.append(pt)
                seen_pub_types.add(key)

    raw_merged: dict = {}
    for c in group:
        raw_merged.update(c.raw_per_source)

    return replace(
        base,
        pmid=pmid,
        mesh_terms=mesh_terms or [],
        influential_citation_count=inf_cites,
        tldr=tldr,
        s2_paper_id=s2_paper_id,
        oa_status=oa_status,
        oa_url=oa_url,
        sources=all_sources,
        raw_per_source=raw_merged,
        stage_b_edges=all_edges,
        publication_types=all_pub_types,
    )


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------

def _try_add(
    cand: Candidate,
    picks: list[Candidate],
    author_count: dict[str, int],
    max_per_author: int = 3,
) -> bool:
    """Add cand to picks if diversity rule allows. Returns True if added."""
    key = (cand.first_author_family or "").lower().strip()
    if key and author_count.get(key, 0) >= max_per_author:
        return False
    picks.append(cand)
    if key:
        author_count[key] = author_count.get(key, 0) + 1
    return True


def select_candidates(
    candidates: list[Candidate],
    item: ItemQueryPlan,
    today_year: int,
    landmark_pub_ids: set[str],
) -> tuple[list[Candidate], list[Candidate], list[Candidate]]:
    """Select top and recent picks; return all sorted by composite score.

    Returns:
        (top_picks, recent_picks, all_sorted)

        top_picks:    up to 5 candidates (landmarks pinned first),
            scored with recency neutralized so old papers are not penalised.
        recent_picks: up to 20 candidates with year >= today-8, >=3 reviews.
        all_sorted:   all deduplicated candidates sorted by composite score desc.

    Diversity rule (shared across both pick lists):
        No single first_author_family appears more than 3 times in the
        combined picked set (25 candidates total).
    """
    def fscore(c: Candidate) -> float:
        return composite_score(c, item, today_year, landmark_pub_ids, neutralize_recency=True)

    def rscore(c: Candidate) -> float:
        return composite_score(c, item, today_year, landmark_pub_ids)

    all_sorted = sorted(candidates, key=rscore, reverse=True)

    # Shared author diversity tracker across both slot types.
    author_count: dict[str, int] = {}

    # --- Top picks (up to 5): landmarks pinned, rest by fscore ---
    landmarks    = [c for c in all_sorted if c.pub_id in landmark_pub_ids]
    non_landmark = sorted(
        [c for c in all_sorted if c.pub_id not in landmark_pub_ids],
        key=fscore, reverse=True,
    )

    top_picks: list[Candidate] = []
    for c in landmarks:
        _try_add(c, top_picks, author_count)
    for c in non_landmark:
        if len(top_picks) >= 5:
            break
        _try_add(c, top_picks, author_count)

    # --- Recent picks (up to 20): year >= today-8, >=3 reviews ---
    recent_year_min = today_year - 8
    recent_pool = [c for c in all_sorted if c.year is not None and c.year >= recent_year_min]

    recent_picks: list[Candidate] = []
    review_count = 0
    for c in recent_pool:
        if len(recent_picks) >= 20:
            break
        added = _try_add(c, recent_picks, author_count)
        
    if review_count < 3:
        already_picked = set(id(c) for c in top_picks + recent_picks)
        review_backfill = [
            c for c in all_sorted
            if (c.is_review or c.is_meta_analysis) and id(c) not in already_picked
        ]
        for c in review_backfill:
            if review_count >= 3:
                break
            added = _try_add(c, recent_picks, author_count)
            if added:
                review_count += 1

    return top_picks, recent_picks, all_sorted
