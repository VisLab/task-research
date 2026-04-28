"""
present_candidates.py — Per-item candidate markdown emitter + index writer.

Writes one markdown file per item to:
    <output_dir>/<item_id>.md

v3 changes:
  - Section 1 header renamed to "Top candidates (score-ranked)".
  - Detail block renders TLDR (when present) above abstract; omitted if absent.
  - Stage B expansion summary line added below "Sources queried".
  - Pass names updated to all_years / recent / reviews.

Imports:
    from present_candidates import write_item_markdown, write_index
"""

import re
from datetime import date
from pathlib import Path

from normalize import Candidate
from search_queries import ItemQueryPlan
from rank_and_select import composite_score


TODAY = date.today().isoformat()


def _trunc_title(title: str, max_chars: int = 90) -> str:
    if len(title) <= max_chars:
        return title
    cut = title[:max_chars].rsplit(" ", 1)[0]
    return cut + "\u2026"


def _first_sentences(text: str | None, max_chars: int = 400) -> str:
    if not text:
        return "(no abstract)"
    parts = re.split(r"\.\s+(?=[A-Z])", text.strip())
    result = ". ".join(parts[:3])
    if not result.endswith("."):
        result += "."
    return result[:max_chars]


def _doi_link(doi: str | None) -> str:
    if doi:
        return f"[{doi}](https://doi.org/{doi})"
    return "\u2014"


def _score_str(score: float) -> str:
    return f"{score:.3f}"


def _row(n: str, cand: Candidate, score: float, role: str) -> str:
    title_trunc = _trunc_title(cand.title)
    doi_cell    = _doi_link(cand.doi)
    first_auth  = cand.first_author_family or "?"
    year        = str(cand.year) if cand.year else "?"
    venue       = (cand.venue or "?")[:35]
    cites       = str(cand.citation_count) if cand.citation_count is not None else "?"
    return (
        f"| {n} | {doi_cell} | {first_auth} | {year} | {venue} | "
        f"{cites} | {_score_str(score)} | {role} | {title_trunc} |"
    )


_TABLE_HEADER = (
    "| # | DOI | First author | Year | Venue | Cites | Score | Suggested | Title |\n"
    "| - | --- | ------------ | ---- | ----- | ----- | ----- | --------- | ----- |"
)


def _detail_block(n: str, cand: Candidate) -> str:
    """Detail lines below each table row.

    Renders TLDR (when present) above abstract.  If cand.tldr is None or
    empty the TLDR line is omitted entirely (no placeholder text).
    """
    sources = ", ".join(cand.sources)
    lines = [
        f"\n- **({n})** `[ ] KEEP  [ ] DROP  role: ___________`  sources: {sources}",
    ]
    if cand.tldr:
        lines.append(f"  *TLDR:* {cand.tldr}")
    lines.append(f"  *Abstract:* {_first_sentences(cand.abstract)}")
    lines.append("")
    return "\n".join(lines)


def _suggest_role(cand: Candidate, today_year: int) -> str:
    """Advisory role hint for the human reviewer (Phase 5).

    Note: "foundational" here is a ROLE label for older primary papers, not a
    Stage A pass name.  The pass labels are all_years / recent / reviews.
    """
    if cand.is_review or cand.is_meta_analysis:
        return "key_review"
    if cand.year is not None and cand.year < today_year - 15:
        return "foundational"
    if cand.year is not None and cand.year >= today_year - 8:
        return "recent_primary"
    return "foundational"


def _build_section(
    header: str,
    candidates: list[Candidate],
    picked_ids: set[str],
    pick_suffix: str,
    item: ItemQueryPlan,
    today_year: int,
    landmark_pub_ids: set[str],
    display_limit: int = 25,
) -> str:
    lines = [f"## {header}", "", _TABLE_HEADER]
    details = []
    for i, cand in enumerate(candidates[:display_limit]):
        score  = composite_score(cand, item, today_year, landmark_pub_ids)
        suffix = pick_suffix if cand.pub_id in picked_ids else ""
        n      = f"{i + 1}{suffix}"
        role   = _suggest_role(cand, today_year)
        lines.append(_row(n, cand, score, role))
        details.append(_detail_block(n, cand))
    lines.append("")
    lines.extend(details)
    return "\n".join(lines)


def _build_landmark_section(
    landmark_entries: list[dict],
    all_candidates: list[Candidate],
) -> str:
    all_pub_ids = {c.pub_id for c in all_candidates}
    all_dois    = {c.doi for c in all_candidates if c.doi}
    lines = [
        "## 4. Landmark check", "",
        "| Landmark citation | Landmark pub_id | Found in candidates? |",
        "| --- | --- | --- |",
    ]
    for lm in landmark_entries:
        citation = lm.get("citation", "?")
        pub_id   = lm.get("pub_id", "?")
        doi      = lm.get("doi")
        found    = (pub_id in all_pub_ids) or (doi and doi.lower() in all_dois)
        status   = "YES" if found else "NOT FOUND \u2014 query may need broadening"
        lines.append(f"| {citation} | {pub_id} | {status} |")
    return "\n".join(lines)


def write_item_markdown(
    item: ItemQueryPlan,
    found_picks: list[Candidate],
    recent_picks: list[Candidate],
    all_sorted: list[Candidate],
    landmark_entries: list[dict],
    output_dir: Path,
    today_year: int,
    stage_b_n_seeds: int = 0,
    stage_b_n_kept: int = 0,
) -> Path:
    """Write the per-item candidate markdown file. Returns the output path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{item.item_id}.md"

    landmark_pub_ids = {e.get("pub_id", "") for e in landmark_entries}
    found_ids  = {c.pub_id for c in found_picks}
    recent_ids = {c.pub_id for c in recent_picks}

    from rank_and_select import composite_score as _cs

    def fscore(c: Candidate) -> float:
        return _cs(c, item, today_year, landmark_pub_ids, neutralize_recency=True)

    found_display   = sorted(all_sorted, key=fscore, reverse=True)
    recent_year_min = today_year - 8
    recent_display  = sorted(
        [c for c in all_sorted if c.year is not None and c.year >= recent_year_min],
        key=lambda c: _cs(c, item, today_year, landmark_pub_ids),
        reverse=True,
    )

    alias_str = ", ".join(
        a if isinstance(a, str) else (a.get("name") or "")
        for a in item.aliases
    ) if item.aliases else "none"
    topic_str = (
        ", ".join(item.openalex_topic_ids) if item.openalex_topic_ids
        else "none (no crosswalk)"
    )
    n_total  = len(all_sorted)
    n_picked = len(found_picks) + len(recent_picks)

    lines: list[str] = [
        f"# Candidates \u2014 {item.item_id}", "",
        f"**Kind:** {item.item_kind}",
        f"**Primary name:** {item.primary_name}",
        f"**Aliases:** {alias_str}",
        f"**Generated:** {TODAY}",
        f"**Sources queried:** openalex, europepmc, semanticscholar",
        f"**Stage B expansion:** {stage_b_n_seeds} seeds, "
        f"{stage_b_n_kept} citing papers kept after filters",
        f"**Passes:** all_years, recent, reviews",
        f"**Topic filter:** {topic_str}",
        f"**Candidates (total after dedup):** {n_total}",
        f"**Picked (P=top slot, R=recent slot):** {n_picked}",
        "",
        "## How to review", "",
        "Each candidate has `[ ] KEEP` and `[ ] DROP` checkboxes and a `role:` field.",
        "Tick KEEP on every candidate you want in the final reference list.",
        "Leave blank to silently drop. The `Suggested` column is the ranker's best",
        "guess; overwrite `role:` if you disagree.",
        "Roles: `foundational | key_review | recent_primary | methods | historical`",
        "",
    ]

    # Section 1: Top candidates (score-ranked)
    lines.append(_build_section(
        header="1. Top candidates (score-ranked)",
        candidates=found_display,
        picked_ids=found_ids,
        pick_suffix="P",
        item=item,
        today_year=today_year,
        landmark_pub_ids=landmark_pub_ids,
        display_limit=25,
    ))

    # Section 2: Recent
    lines.append(_build_section(
        header=f"2. Recent candidates (top 25, year >= {recent_year_min})",
        candidates=recent_display,
        picked_ids=recent_ids,
        pick_suffix="R",
        item=item,
        today_year=today_year,
        landmark_pub_ids=landmark_pub_ids,
        display_limit=25,
    ))

    # Section 3: Audit tail
    lines.append("## 3. All deduplicated candidates (audit tail)")
    lines.append("")
    lines.append(_TABLE_HEADER)
    picked_all = found_ids | recent_ids
    for i, cand in enumerate(all_sorted[:100]):
        score  = _cs(cand, item, today_year, landmark_pub_ids)
        suffix = "*" if cand.pub_id in picked_all else ""
        n      = f"{i + 1}{suffix}"
        role   = _suggest_role(cand, today_year)
        lines.append(_row(n, cand, score, role))
    lines.append("")

    # Section 4: Landmark check
    lines.append(_build_landmark_section(landmark_entries, all_sorted))
    lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def write_index(
    index_path: Path,
    items: list[dict],
    candidates_dir: Path,
) -> None:
    lines = [
        f"# Candidate index \u2014 {TODAY}", "",
        "Generated by Phase 3 systematic search.",
        "172 processes + 103 tasks = 275 items expected.",
        "",
        "## Summary", "",
        "| # | item_id | kind | candidates | picked | landmark hits |",
        "| - | ------- | ---- | ---------- | ------ | ------------- |",
    ]
    for i, row in enumerate(items):
        lm_hits  = row.get("n_landmarks", 0)
        lm_total = row.get("n_lm_total", 0)
        lines.append(
            f"| {i + 1} | {row['item_id']} | {row['kind']} | "
            f"{row['n_candidates']} | {row['n_picked']} | {lm_hits}/{lm_total} |"
        )
    lines.append("")
    lines.append("## Files")
    lines.append("")
    for row in items:
        rel = candidates_dir / f"{row['item_id']}.md"
        lines.append(f"- [{row['item_id']}]({rel})")
    index_path.write_text("\n".join(lines), encoding="utf-8")
