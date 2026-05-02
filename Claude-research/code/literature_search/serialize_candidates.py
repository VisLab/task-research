"""
serialize_candidates.py — Write Phase 3 candidates to canonical JSON.

This is the *only* place where a Candidate becomes JSON. The downstream
review-extract and markdown-render steps both read this format; nothing
else writes it.

Schema version: phase3_candidates_v1 (see schemas/phase3_candidates.schema.json
when that file lands).

The JSON is structured around three blocks:
    item   — the catalog identity for this row (process or task), including
             definition + aliases so the file is self-contained.
    run    — provenance for the search run (date, sources, filters, totals,
             tier thresholds).
    candidates — every retained candidate, ranked, with tier, role, score
             breakdown, and provenance per candidate.

Public entry points:
    write_candidates_json(item, candidates, run_metadata, output_dir)
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from normalize import Candidate
from search_queries import ItemQueryPlan
from triage_rules import classify_venue


SCHEMA_VERSION = "phase3_candidates_v1"


# ---------------------------------------------------------------------------
# Item identity block — duplicated into both candidates and review files
# so each is self-contained.
# ---------------------------------------------------------------------------

def build_item_block(item: ItemQueryPlan) -> dict:
    """Return the `item` block of the candidates JSON.

    Pulls identity fields directly off the ItemQueryPlan. The block is
    duplicated into the review JSON too so each per-item file is
    self-contained.

    For processes, `description` carries the catalog `definition`.
    For tasks, `description` carries the catalog `description`, and
    `short_definition` and `inclusion_test` are also populated.
    """
    block: dict = {
        "kind": item.item_kind,                # "process" | "task"
        "id": item.item_id,
        "name": item.primary_name,
        "aliases": list(item.aliases or []),
    }
    if item.category_id:
        block["category_id"] = item.category_id

    if item.item_kind == "process":
        if item.description:
            # `description` on the plan == `definition` in the catalog
            # for processes.
            block["definition"] = item.description
    else:  # task
        if item.short_definition:
            block["short_definition"] = item.short_definition
        if item.description:
            block["description"] = item.description
        if item.inclusion_test:
            block["inclusion_test"] = dict(item.inclusion_test)

    return block


# ---------------------------------------------------------------------------
# Per-candidate serialization
# ---------------------------------------------------------------------------

def _candidate_to_json(c: Candidate, rank: int) -> dict:
    """Serialize one Candidate to its JSON representation."""
    out: dict = {
        "rank": rank,
        "tier": c.tier,
        "auto_role": c.auto_role,
        "pub_id": c.pub_id,
        "doi": c.doi,
        "url": f"https://doi.org/{c.doi}" if c.doi else None,
        "openalex_id": c.openalex_id,
        "pmid": c.pmid,
        "first_author": c.first_author_family,
        "authors_display": c.authors_display,
        "year": c.year,
        "title": c.title,
        "venue": c.venue,
        "venue_tier": classify_venue(c.venue),
        "publisher": c.publisher,
        "publication_types": list(c.publication_types),
        "is_review": c.is_review,
        "is_meta_analysis": c.is_meta_analysis,
        "human_subject": c.human_subject,
        "species_evidence": list(c.species_evidence),
        "citation_count": c.citation_count,
        "influential_citation_count": c.influential_citation_count,
        "fwci": c.fwci,
        "cited_by_percentile_year": c.cited_by_percentile_year,
        "oa_status": c.oa_status,
        "oa_url": c.oa_url,
        "tldr": c.tldr,
        "abstract": c.abstract,
        "score": {
            "composite": c.composite_score,
            "breakdown": dict(c.score_components),
        },
        "provenance": {
            "sources": list(c.sources),
            "stage_b_seed_pub_ids": [
                e.get("seed_pub_id")
                for e in c.stage_b_edges
                if e.get("seed_pub_id")
            ],
        },
    }
    if c.tier == "excluded":
        out["exclusion_reason"] = c.exclusion_reason
    if c.mesh_terms:
        out["mesh_terms"] = list(c.mesh_terms)
    return out


# ---------------------------------------------------------------------------
# Top-level write
# ---------------------------------------------------------------------------

def build_candidates_json(
    item: ItemQueryPlan,
    candidates: list[Candidate],
    run_metadata: dict,
) -> dict:
    """Assemble the full candidates JSON for one item.

    Args:
        item: the ItemQueryPlan for this process or task.
        candidates: every candidate retained after dedup, in any order.
            They will be sorted here by composite_score descending; rank
            assignment matches the sort.
        run_metadata: provenance dict carrying:
            sources: list[str] — which APIs were queried
            passes: list[str] — which passes ran
            stage_b: dict — seeds/raw/after_filters counts
            filters: dict — species, publication_types, etc.
            tier_thresholds: dict — n_picked, n_reserve, min_picked_score
            totals: dict — deduped, picked, reserve, excluded counts
            exclusion_reasons: dict — counts by reason
    """
    ranked = sorted(
        candidates,
        key=lambda c: (c.composite_score is None, -(c.composite_score or 0.0)),
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "generated": datetime.now().isoformat(timespec="seconds"),
        "item": build_item_block(item),
        "run": run_metadata,
        "candidates": [_candidate_to_json(c, rank=i + 1) for i, c in enumerate(ranked)],
    }


def write_candidates_json(
    item: ItemQueryPlan,
    candidates: list[Candidate],
    run_metadata: dict,
    output_dir: Path,
) -> Path:
    """Write the canonical candidates JSON for one item.

    Output path: ``<output_dir>/<item_id>.json``. The directory is created
    if it does not exist.

    Returns the path written. The file is overwritten on each call.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{item.item_id}.json"

    payload = build_candidates_json(item, candidates, run_metadata)

    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")

    return path
