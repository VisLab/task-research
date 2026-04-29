#!/usr/bin/env python3
"""
phase3_render.py — Render a per-item markdown view from candidates and review JSON.

Inputs (per item):
    outputs/phase3/candidates/<item_id>.json   (always required)
    outputs/phase3/review/<item_id>.json       (optional; decisions overlaid when present)

Output:
    outputs/phase3/rendered/<item_id>.md

Design choices:
  - Single ranked list for the picked tier. No P/R suffix, no parallel
    "top" vs "recent" sections. Rank comes straight from composite_score.
  - Badges (★ review, ★ recent, citation tier, venue tier) instead of
    bare numeric scores so a reader can scan in seconds.
  - Score breakdown and abstract live in `<details>` blocks below the
    table — expand on demand, hidden by default.
  - The `Decision` column shows the current review state for each picked
    row (`accept`, `veto`, `promote`, `…`). When no review file exists
    it shows `(no review yet)`.
  - The reserve tier is summarized in a collapsed table; the excluded
    tier is summarized by reason count only (full list is in the
    candidates JSON for anyone who wants it).

Usage:
    python code/literature_search/phase3_render.py
    python code/literature_search/phase3_render.py --item hed_response_inhibition
    python code/literature_search/phase3_render.py --include-excluded
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Small render helpers
# ---------------------------------------------------------------------------

def _trunc(s: str | None, n: int) -> str:
    if not s:
        return ""
    s = s.strip()
    if len(s) <= n:
        return s
    return s[: n - 1].rstrip() + "…"


def _venue_short(v: str | None, n: int = 28) -> str:
    return _trunc(v, n)


def _format_cites(n: int | None) -> str:
    if n is None:
        return "—"
    if n >= 1000:
        return f"{n//1000}k"
    return str(n)


def _doi_link(doi: str | None) -> str:
    if not doi:
        return "—"
    return f"[{doi}](https://doi.org/{doi})"


def _badges(c: dict) -> str:
    """Compact star/letter badges for the row.

    Each badge tells the reader something without forcing them to
    interpret a numeric score:
        R   — review or meta-analysis
        N   — recent (year >= 2018ish; we use the auto_role recent_primary)
        H   — historical landmark (auto_role == "historical")
        F   — flagship venue (venue_tier == "flagship")
    """
    bits: list[str] = []
    if c.get("auto_role") == "historical":
        bits.append("H")
    if c.get("is_review") or c.get("is_meta_analysis"):
        bits.append("R")
    if c.get("auto_role") == "recent_primary":
        bits.append("N")
    if c.get("venue_tier") == "flagship":
        bits.append("F")
    return "".join(bits) or "·"


# ---------------------------------------------------------------------------
# Decision lookup
# ---------------------------------------------------------------------------

def build_decision_lookup(review_doc: dict | None) -> dict[str, dict]:
    """Map (DOI lower / pub_id) → decision dict for fast row-level lookup."""
    out: dict[str, dict] = {}
    if not review_doc:
        return out
    for d in review_doc.get("decisions", []) or []:
        if d.get("doi"):
            out[f"doi:{d['doi'].lower()}"] = d
        if d.get("pub_id"):
            out[f"pub:{d['pub_id']}"] = d
    return out


def _lookup_decision(c: dict, lookup: dict[str, dict]) -> dict | None:
    if c.get("doi"):
        d = lookup.get(f"doi:{c['doi'].lower()}")
        if d:
            return d
    if c.get("pub_id"):
        return lookup.get(f"pub:{c['pub_id']}")
    return None


def _decision_label(d: dict | None) -> str:
    if d is None:
        return "(no review)"
    a = d.get("action")
    if a is None:
        return "accept"
    return str(a)


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------

def render_header(cand_doc: dict) -> str:
    item = cand_doc.get("item") or {}
    out: list[str] = []
    kind = item.get("kind", "?")
    name = item.get("name", "?")
    out.append(f"# {name}  ·  {kind}")
    out.append("")

    # Definition / description (process vs task)
    definition = item.get("definition") or item.get("description")
    if definition:
        out.append(definition)
        out.append("")
    if item.get("short_definition") and item.get("short_definition") != definition:
        out.append(f"_Short definition._ {item['short_definition']}")
        out.append("")
    if item.get("inclusion_test"):
        it = item["inclusion_test"]
        out.append(f"_Inclusion test._")
        for k in ("procedure", "manipulation", "measurement"):
            if it.get(k):
                out.append(f"- **{k.capitalize()}.** {it[k]}")
        out.append("")

    # Aliases
    aliases = item.get("aliases") or []
    if aliases:
        names = []
        for a in aliases:
            if isinstance(a, str):
                names.append(a)
            elif isinstance(a, dict):
                names.append(a.get("name") or "")
        names = [n for n in names if n]
        if names:
            out.append(f"**Aliases.** {', '.join(names)}")
            out.append("")

    if item.get("category_id"):
        out.append(f"**Category.** `{item['category_id']}`")
        out.append("")

    out.append("---")
    out.append("")
    return "\n".join(out)


def render_run_block(cand_doc: dict) -> str:
    run = cand_doc.get("run") or {}
    totals = run.get("totals") or {}
    excl = run.get("exclusion_reasons") or {}

    rows: list[tuple[str, str]] = [
        ("Generated", cand_doc.get("generated", "?")),
        ("Sources", ", ".join(run.get("sources") or [])),
        ("Passes", ", ".join(run.get("passes") or [])),
        ("Picked / Reserve / Excluded",
         f"{totals.get('picked', '?')} / {totals.get('reserve', '?')} / {totals.get('excluded', '?')}"),
        ("Total candidates (post-dedup)", str(totals.get("deduped", "?"))),
        ("Historical landmarks found",
         f"{totals.get('landmarks_found', '?')} / {totals.get('landmarks_total', '?')}"),
    ]
    if excl.get("non_human_subjects"):
        rows.append(("Excluded for non-human subjects", str(excl["non_human_subjects"])))

    out = ["## Run", ""]
    out.append("| | |")
    out.append("|---|---|")
    for k, v in rows:
        out.append(f"| {k} | {v} |")
    out.append("")
    return "\n".join(out)


def _badges_legend() -> str:
    return (
        "Badges: **H** historical landmark · **R** review or meta-analysis · "
        "**N** recent primary · **F** flagship venue."
    )


def render_picked_section(cand_doc: dict, decisions_by_key: dict[str, dict]) -> str:
    picked = [c for c in (cand_doc.get("candidates") or []) if c.get("tier") == "picked"]
    if not picked:
        return "## Picked (0)\n\n_No picked-tier candidates._\n"

    out = [f"## Picked ({len(picked)})", ""]
    out.append(_badges_legend())
    out.append("")

    # The scan-friendly table.
    out.append("| # | Year | First author | Venue | Cites | Badges | Auto role | Score | Decision | Title |")
    out.append("| - | ---- | ------------ | ----- | ----- | ------ | --------- | ----- | -------- | ----- |")
    for c in picked:
        d = _lookup_decision(c, decisions_by_key)
        score = c.get("score") or {}
        composite = score.get("composite")
        composite_str = f"{composite:.2f}" if composite is not None else "?"
        out.append(
            f"| {c.get('rank', '?')} "
            f"| {c.get('year') or '—'} "
            f"| {c.get('first_author') or '—'} "
            f"| {_venue_short(c.get('venue'))} "
            f"| {_format_cites(c.get('citation_count'))} "
            f"| {_badges(c)} "
            f"| {c.get('auto_role') or '—'} "
            f"| {composite_str} "
            f"| {_decision_label(d)} "
            f"| {_trunc(c.get('title'), 70)} |"
        )
    out.append("")

    # Per-row detail blocks (collapsed).
    out.append("### Picked — score breakdown and abstract per row")
    out.append("")
    for c in picked:
        score = c.get("score") or {}
        composite = score.get("composite")
        composite_str = f"{composite:.3f}" if composite is not None else "?"
        breakdown = score.get("breakdown") or {}
        weighted = breakdown.get("weighted") or {}
        raw = breakdown.get("raw") or {}
        stage_b = breakdown.get("stage_b_bump", 0.0)
        landmark = breakdown.get("landmark_bonus", 0.0)

        title = c.get("title") or ""
        first = c.get("first_author") or "?"
        year = c.get("year") or "?"
        rank = c.get("rank", "?")
        out.append(
            f"<details><summary><strong>{rank}.</strong> {first} {year} — "
            f"{_trunc(title, 100)} (score {composite_str})</summary>"
        )
        out.append("")
        out.append(f"DOI: {_doi_link(c.get('doi'))}")
        out.append("")
        out.append(f"Venue: {c.get('venue') or '—'}")
        out.append("")
        if c.get("species_evidence"):
            out.append(f"Species evidence: {', '.join(c.get('species_evidence') or [])}")
            out.append("")

        out.append("Score breakdown:")
        out.append("")
        out.append("| component | raw | weighted |")
        out.append("|---|---|---|")
        for comp_name in ("citations", "venue", "publisher", "recency", "relevance", "review"):
            r = raw.get(comp_name)
            w = weighted.get(comp_name)
            r_str = f"{r:.3f}" if r is not None else "—"
            w_str = f"{w:.3f}" if w is not None else "—"
            out.append(f"| {comp_name} | {r_str} | {w_str} |")
        if stage_b:
            out.append(f"| stage_b_bump | — | {stage_b:.3f} |")
        if landmark:
            out.append(f"| landmark_bonus | — | {landmark:.3f} |")
        out.append(f"| **composite** | — | **{composite_str}** |")
        out.append("")

        if c.get("tldr"):
            out.append(f"_TLDR._ {c['tldr']}")
            out.append("")
        if c.get("abstract"):
            out.append(f"_Abstract._ {_trunc(c['abstract'], 800)}")
            out.append("")
        out.append("</details>")
        out.append("")

    return "\n".join(out)


def render_reserve_section(cand_doc: dict) -> str:
    reserve = [c for c in (cand_doc.get("candidates") or []) if c.get("tier") == "reserve"]
    if not reserve:
        return ""

    out = [f"## Reserve ({len(reserve)})", ""]
    out.append("Available for promotion via the review file. Collapsed by default.")
    out.append("")
    out.append("<details><summary>Show reserve list</summary>")
    out.append("")
    out.append("| # | Year | First author | Venue | Cites | Auto role | Score | Title |")
    out.append("| - | ---- | ------------ | ----- | ----- | --------- | ----- | ----- |")
    for c in reserve:
        score = c.get("score") or {}
        composite = score.get("composite")
        composite_str = f"{composite:.2f}" if composite is not None else "?"
        out.append(
            f"| {c.get('rank', '?')} "
            f"| {c.get('year') or '—'} "
            f"| {c.get('first_author') or '—'} "
            f"| {_venue_short(c.get('venue'))} "
            f"| {_format_cites(c.get('citation_count'))} "
            f"| {c.get('auto_role') or '—'} "
            f"| {composite_str} "
            f"| {_trunc(c.get('title'), 70)} |"
        )
    out.append("")
    out.append("</details>")
    out.append("")
    return "\n".join(out)


def render_excluded_summary(cand_doc: dict, include_full: bool = False) -> str:
    excluded = [c for c in (cand_doc.get("candidates") or []) if c.get("tier") == "excluded"]
    if not excluded:
        return ""

    # Group by reason.
    by_reason: dict[str, int] = {}
    for c in excluded:
        r = c.get("exclusion_reason") or "unknown"
        by_reason[r] = by_reason.get(r, 0) + 1

    out = [f"## Excluded ({len(excluded)})", ""]
    out.append("Counts by exclusion reason. Full list is in the candidates JSON.")
    out.append("")
    out.append("| Reason | Count |")
    out.append("| ------ | ----- |")
    for reason, n in sorted(by_reason.items(), key=lambda kv: kv[1], reverse=True):
        out.append(f"| {reason} | {n} |")
    out.append("")

    if include_full:
        # Just show the non_human_subjects ones — those are the most useful
        # to spot-check (did the species filter make sensible decisions?).
        non_human = [c for c in excluded if c.get("exclusion_reason") == "non_human_subjects"]
        if non_human:
            out.append(f"### Non-human exclusions ({len(non_human)})")
            out.append("")
            out.append("| # | Year | First author | Title | Species evidence |")
            out.append("| - | ---- | ------------ | ----- | ---------------- |")
            for c in non_human:
                ev = ", ".join(c.get("species_evidence") or [])
                out.append(
                    f"| {c.get('rank', '?')} "
                    f"| {c.get('year') or '—'} "
                    f"| {c.get('first_author') or '—'} "
                    f"| {_trunc(c.get('title'), 70)} "
                    f"| {ev or '—'} |"
                )
            out.append("")

    return "\n".join(out)


def render_review_orphans(review_doc: dict | None) -> str:
    if not review_doc:
        return ""
    orphans = review_doc.get("previously_decided") or []
    if not orphans:
        return ""

    out = ["## Previously decided (audit only)", ""]
    out.append(
        "Decisions you'd previously recorded that no longer apply to the "
        "current picked tier. Phase 6 ignores these. Promote any of them "
        "back from reserve via the review file if needed."
    )
    out.append("")
    out.append("| Year | First author | Venue | Prior action | Current tier | Note |")
    out.append("| ---- | ------------ | ----- | ------------ | ------------ | ---- |")
    for o in orphans:
        out.append(
            f"| {o.get('year', '—')} "
            f"| — "
            f"| {_venue_short(o.get('venue'), 24)} "
            f"| {o.get('action') or '—'} "
            f"| {o.get('current_tier') or '—'} "
            f"| {_trunc(o.get('rebase_note'), 60)} |"
        )
    out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Top-level render
# ---------------------------------------------------------------------------

def render_item(
    cand_doc: dict,
    review_doc: dict | None,
    include_excluded_full: bool = False,
) -> str:
    decisions_lookup = build_decision_lookup(review_doc)
    parts: list[str] = []
    parts.append(render_header(cand_doc))
    parts.append(render_run_block(cand_doc))
    parts.append(render_picked_section(cand_doc, decisions_lookup))
    parts.append(render_reserve_section(cand_doc))
    parts.append(render_excluded_summary(cand_doc, include_full=include_excluded_full))
    parts.append(render_review_orphans(review_doc))
    return "\n".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workspace", default=".")
    ap.add_argument("--candidates-dir", default="outputs/phase3/candidates")
    ap.add_argument("--review-dir",     default="outputs/phase3/review")
    ap.add_argument("--rendered-dir",   default="outputs/phase3/rendered")
    ap.add_argument("--item", default="",
                    help="Single item_id; default is all candidates files.")
    ap.add_argument("--include-excluded", action="store_true",
                    help="Also list non-human exclusions in the rendered output "
                         "(for auditing the species filter).")
    ap.add_argument("--dry-run", action="store_true",
                    help="Render but do not write files.")
    args = ap.parse_args()

    ws = Path(args.workspace).resolve()
    cand_dir = ws / args.candidates_dir
    rev_dir  = ws / args.review_dir
    out_dir  = ws / args.rendered_dir

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
    print(f"Rendering markdown for {len(cand_files)} item(s).")
    print(f"  candidates dir : {cand_dir}")
    print(f"  review dir     : {rev_dir}")
    print(f"  rendered dir   : {out_dir}")
    print(f"  write          : {write}")
    print()

    out_dir.mkdir(parents=True, exist_ok=True)

    for cf in cand_files:
        if not cf.exists():
            print(f"  MISSING: {cf}")
            continue
        try:
            with cf.open("r", encoding="utf-8") as f:
                cand_doc = json.load(f)
        except json.JSONDecodeError as exc:
            print(f"  ERROR parsing {cf.name}: {exc}", file=sys.stderr)
            continue

        item_id = (cand_doc.get("item") or {}).get("id")
        if not item_id:
            print(f"  ERROR: {cf.name} missing item.id", file=sys.stderr)
            continue

        review_path = rev_dir / f"{item_id}.json"
        review_doc: dict | None = None
        if review_path.exists():
            try:
                with review_path.open("r", encoding="utf-8") as f:
                    review_doc = json.load(f)
            except json.JSONDecodeError as exc:
                print(f"  WARN: review file {review_path} does not parse: {exc}",
                      file=sys.stderr)

        md_text = render_item(
            cand_doc, review_doc,
            include_excluded_full=args.include_excluded,
        )

        if write:
            out_path = out_dir / f"{item_id}.md"
            with out_path.open("w", encoding="utf-8", newline="\n") as f:
                f.write(md_text)
                if not md_text.endswith("\n"):
                    f.write("\n")
            print(f"  {item_id:40s}  rendered -> {out_path}")
        else:
            print(f"  {item_id:40s}  (dry-run, {len(md_text)} chars)")

    if not write:
        print()
        print("DRY RUN — no files written. Re-run without --dry-run to write.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
