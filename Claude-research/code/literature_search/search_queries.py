"""
search_queries.py -- Per-item query plan builder for Phase 3 systematic search.

Reads process_details.json and task_details.json; returns one ItemQueryPlan per
process and per task.  No network calls -- pure data transformation.

Terminology (v3):
  Stage A has three sub-queries: all_years, recent, reviews.
  These are descriptive labels only; they do not predict the role a paper
  will be assigned.  Role labels appear at output time as advisory hints.

  The old foundational pass key was renamed to all_years in v3.  Any
  reference to foundational as a pass key or dict key is a bug.

Design authority: instructions/search_strategy_decisions_2026-04-24.md

Imports:
    from search_queries import build_plans_from_json, ItemQueryPlan
"""

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from fos_map import fields_of_study_for_category, fields_of_study_set


TODAY_YEAR: int = date.today().year
RECENT_YEAR_MIN: int = TODAY_YEAR - 8


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------

@dataclass
class ItemQueryPlan:
    item_id: str               # hed_* or hedtsk_*
    item_kind: str             # "process" or "task"
    primary_name: str
    aliases: list              # list[str] for tasks; list[dict] for processes
    description: str           # used for query_relevance scoring; also the
                               # canonical "definition" for processes / the
                               # `description` field for tasks
    openalex_topic_ids: list   # [] when crosswalk unavailable
    category_id: str | None    # primary category_id (None for multi-category tasks)
    fos_set: set               # pre-computed FoS set for Stage B filtering
    passes: dict               # "all_years" | "recent" | "reviews"
    # Identity-block extras propagated through to the candidates-JSON output
    # so each per-item file is self-contained (added 2026-04-28).
    short_definition: str | None = None     # tasks only
    inclusion_test: dict | None = None      # tasks only — {procedure, manipulation, measurement}


# ---------------------------------------------------------------------------
# Alias normalisation
# ---------------------------------------------------------------------------

def _alias_strings(aliases: list) -> list:
    """Return a flat list of alias strings regardless of input type.

    Task aliases are plain strings.
    Process aliases are dicts with a name key (and optional note).
    """
    result = []
    for a in aliases or []:
        if isinstance(a, str):
            s = a.strip()
            if s:
                result.append(s)
        elif isinstance(a, dict):
            s = (a.get("name") or "").strip()
            if s:
                result.append(s)
    return result


# ---------------------------------------------------------------------------
# Query construction helpers
# ---------------------------------------------------------------------------

def _phrases(name: str, aliases: list) -> list[str]:
    """Return the primary name plus all alias strings as a flat list.

    Used for OpenAlex phrase-filter and EuropePMC TITLE/ABSTRACT construction.
    """
    alias_strs = _alias_strings(aliases)
    return [name] + [a for a in alias_strs if a != name]


def _s2_queries(name: str, aliases: list) -> list[str]:
    """Return one query string per alias for Semantic Scholar.

    S2 does not reliably support boolean OR in /paper/search, so callers
    run one search per term and union the results.  Multi-word phrases are
    wrapped in double quotes so S2 treats them as phrases rather than
    independent token matches.
    """
    alias_strs = _alias_strings(aliases)
    out = []
    for t in [name] + [a for a in alias_strs if a != name]:
        if not t:
            continue
        out.append(f'"{t}"' if " " in t else t)
    return out


def _build_passes(
    name: str,
    aliases: list,
    topic_ids: list,
    fields_of_study: str,
) -> dict:
    """Construct the three pass specifications (all_years, recent, reviews).

    No key named foundational appears anywhere in the returned structure.

    Args:
        name:             Primary item name.
        aliases:          Alias list (str for tasks; dicts for processes).
        topic_ids:        OpenAlex topic IDs (may be empty).
        fields_of_study:  Comma-joined S2 fieldsOfStudy string for this item.
    """
    phrase_list = _phrases(name, aliases)
    s2_qs = _s2_queries(name, aliases)
    topic_ids_arg = topic_ids or None

    return {
        # No year filter -- collects classical canon and high-cite papers of any era.
        # S2: minCitationCount=20 applied (a paper cited < 20 times is unlikely
        # to be foundational or a key review over any time horizon).
        "all_years": {
            "openalex": {
                "phrases": phrase_list, "topic_ids": topic_ids_arg,
                "year_min": None, "year_max": None,
                "pub_type": "article_review", "max_results": 100,
            },
            "europepmc": {
                "phrases": phrase_list, "year_min": None, "year_max": None,
                "pub_type": "research_article", "max_results": 100,
            },
            "semanticscholar": {
                "queries": s2_qs, "year_min": None, "year_max": None,
                "max_results": 100,
                "fields_of_study": fields_of_study,
                "min_citation_count": 20,
                "publication_types": "JournalArticle,Review,Dataset",
            },
        },
        # Last 8 years -- surfaces recent work under-weighted by all_years pass.
        # S2: no minCitationCount (recent papers legitimately have low counts).
        "recent": {
            "openalex": {
                "phrases": phrase_list, "topic_ids": topic_ids_arg,
                "year_min": RECENT_YEAR_MIN, "year_max": None,
                "pub_type": "article_review", "max_results": 100,
            },
            "europepmc": {
                "phrases": phrase_list, "year_min": RECENT_YEAR_MIN, "year_max": None,
                "pub_type": "research_article", "max_results": 100,
            },
            "semanticscholar": {
                "queries": s2_qs, "year_min": RECENT_YEAR_MIN, "year_max": None,
                "max_results": 100,
                "fields_of_study": fields_of_study,
                "min_citation_count": None,
                "publication_types": "JournalArticle,Dataset",
            },
        },
        # Review-type filter -- guarantees reviews appear for the selection rule.
        "reviews": {
            "openalex": {
                "phrases": phrase_list, "topic_ids": topic_ids_arg,
                "year_min": None, "year_max": None,
                "pub_type": "review", "max_results": 100,
            },
            "europepmc": {
                "phrases": phrase_list, "year_min": None, "year_max": None,
                "pub_type": "review_article", "max_results": 100,
            },
            "semanticscholar": {
                "queries": s2_qs, "year_min": None, "year_max": None,
                "max_results": 100,
                "fields_of_study": fields_of_study,
                "min_citation_count": None,
                "publication_types": "Review",
            },
        },
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def build_plans_from_json(process_details_path, task_details_path,
                          openalex_crosswalk_path=None):
    """Build one ItemQueryPlan for every process and every task.

    Args:
        process_details_path: Path to process_details.json.
        task_details_path:    Path to task_details.json.
        openalex_crosswalk_path: Optional path to {item_id: [topic_id]} JSON.

    Returns:
        List of ItemQueryPlan (processes first, then tasks).
    """
    crosswalk = {}
    if openalex_crosswalk_path and Path(openalex_crosswalk_path).exists():
        try:
            crosswalk = json.loads(
                Path(openalex_crosswalk_path).read_text(encoding="utf-8"))
        except Exception:
            crosswalk = {}

    plans = []

    # --- Processes ---
    p_data = json.loads(Path(process_details_path).read_text(encoding="utf-8"))

    # Build a map from process_id -> category_id for task resolution below.
    proc_category_map: dict[str, str | None] = {}
    for proc in p_data.get("processes", []):
        proc_category_map[proc["process_id"]] = proc.get("category_id")

    for proc in p_data.get("processes", []):
        item_id = proc["process_id"]
        name = proc["process_name"]
        aliases = proc.get("aliases") or []
        description = proc.get("definition") or ""
        topic_ids = crosswalk.get(item_id, [])
        cat_id = proc.get("category_id")
        fos_str = fields_of_study_for_category(cat_id)
        fos = fields_of_study_set(cat_id)

        plans.append(ItemQueryPlan(
            item_id=item_id, item_kind="process",
            primary_name=name, aliases=aliases,
            description=description, openalex_topic_ids=topic_ids,
            category_id=cat_id,
            fos_set=fos,
            passes=_build_passes(name, aliases, topic_ids, fos_str),
        ))

    # --- Tasks ---
    t_data = json.loads(Path(task_details_path).read_text(encoding="utf-8"))
    tasks = t_data if isinstance(t_data, list) else t_data.get("tasks", [])
    for task in tasks:
        item_id = task["hedtsk_id"]
        name = task["canonical_name"]
        aliases = task.get("aliases") or []
        description = task.get("description") or task.get("short_definition") or ""
        topic_ids = crosswalk.get(item_id, [])

        # Resolve FoS from associated processes; union across all linked processes.
        proc_ids: list[str] = task.get("hed_process_ids") or []
        fos: set[str] = set()
        for pid in proc_ids:
            cat = proc_category_map.get(pid)
            fos |= fields_of_study_set(cat)
        if not fos:
            fos = fields_of_study_set(None)
        fos_str = ",".join(sorted(fos))

        # Store primary category_id from the first associated process with a known category.
        primary_cat: str | None = None
        for pid in proc_ids:
            cat = proc_category_map.get(pid)
            if cat:
                primary_cat = cat
                break

        plans.append(ItemQueryPlan(
            item_id=item_id, item_kind="task",
            primary_name=name, aliases=aliases,
            description=description, openalex_topic_ids=topic_ids,
            category_id=primary_cat,
            fos_set=fos,
            passes=_build_passes(name, aliases, topic_ids, fos_str),
            short_definition=task.get("short_definition"),
            inclusion_test=task.get("inclusion_test"),
        ))

    return plans


def filter_plans_by_ids(plans, item_ids):
    """Return plans matching the given item_ids (order preserved)."""
    id_set = set(item_ids)
    return [p for p in plans if p.item_id in id_set]


# ---------------------------------------------------------------------------
# POC item IDs
# ---------------------------------------------------------------------------

POC_ITEM_IDS = [
    "hed_response_inhibition",   # well-studied process, classic landmarks
    "hedtsk_stroop_color_word",  # task with multiple aliases, MacLeod 1991
    "hed_model_based_learning",  # modern-skewed, RL / comp-psychiatry venues
]
