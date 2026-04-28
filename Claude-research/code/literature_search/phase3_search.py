#!/usr/bin/env python3
"""
phase3_search.py — Phase 3 systematic per-item literature search.

Run from the workspace root on the Windows host (not in the Cowork sandbox).

Usage:
    python code/literature_search/phase3_search.py --mode poc --write
    python code/literature_search/phase3_search.py --mode single --ids hed_response_inhibition --write

Dependencies: pip install requests

Pipeline:
    Stage A  all_years / recent / reviews sub-queries
          -> dedup -> phrase gate -> Stage A pool
    Stage B  S2 citation expansion from top-50 seeds by influentialCitationCount
          -> type/FoS/phrase filters -> merge into Stage A pool
    Stage C  composite score over merged pool -> select -> write markdown
"""

import argparse
import json
import logging
import os
import re
import sys
import time
import unicodedata
from datetime import date
from pathlib import Path

try:
    import requests  # noqa: F401
except ImportError:
    print("ERROR: 'requests' is not installed.  Run:  pip install requests")
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).parent))

from fos_map import fields_of_study_set
from identity import build_pub_id
from search_queries import build_plans_from_json, filter_plans_by_ids, POC_ITEM_IDS, ItemQueryPlan
from normalize import Candidate, normalize_openalex, normalize_europepmc, normalize_s2
from rank_and_select import (
    dedup_candidates, select_candidates,
    phrase_gate, select_citation_seeds,
)
from present_candidates import write_item_markdown, write_index

from clients.openalex import search_works, lookup_by_doi as oa_lookup
from clients.europepmc import search as epmc_search, lookup_by_doi as epmc_lookup
from clients.semanticscholar import (
    search as s2_search,
    lookup_by_doi as s2_lookup,
    fetch_citations,
)

TODAY      = date.today().isoformat()
TODAY_YEAR = date.today().year

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("phase3")


def load_api_key(env_var: str, apikeys_path: Path | None = None) -> str | None:
    val = os.environ.get(env_var)
    if val:
        return val.strip()
    if apikeys_path and apikeys_path.exists():
        for line in apikeys_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(f"{env_var}=") and not line.startswith("#"):
                return line.split("=", 1)[1].strip()
    return None


def _normalise_family(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s)
    ascii_only = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"[^a-z\-]", "", ascii_only.lower())


def _first_family(ref: dict) -> str | None:
    authors = ref.get("authors") or ""
    if authors:
        family = _normalise_family(authors.split(",")[0].strip())
        return family or None
    cs = ref.get("citation_string") or ""
    if cs:
        m = re.match(r"([A-Za-z\u00C0-\u024F][A-Za-z\u00C0-\u024F'\-]+)", cs)
        return _normalise_family(m.group(1)) if m else None
    return None


def load_historical_refs(process_path: Path, task_path: Path) -> dict[str, list[dict]]:
    """Return {item_id: [ref_dict]} for all references with role 'historical'."""
    result: dict[str, list[dict]] = {}

    def _enrich_and_collect(item_id: str, refs: list[dict]) -> None:
        hist = []
        for ref in refs:
            if "historical" not in ref.get("roles", []):
                continue
            r = dict(ref)
            r["pub_id"] = build_pub_id(_first_family(r), r.get("year"), r.get("title"))
            r.setdefault("citation", r.get("citation_string", "?"))
            hist.append(r)
        if hist:
            result[item_id] = hist

    pd_data = json.loads(process_path.read_text(encoding="utf-8"))
    for proc in pd_data.get("processes", []):
        _enrich_and_collect(proc["process_id"], proc.get("references", []))

    td_data = json.loads(task_path.read_text(encoding="utf-8"))
    tasks = td_data if isinstance(td_data, list) else td_data.get("tasks", [])
    for task in tasks:
        _enrich_and_collect(task["hedtsk_id"], task.get("references", []))

    return result


def _run_stage_b(
    stage_a_pool: list[Candidate],
    item: ItemQueryPlan,
    cache_dir: Path,
    s2_api_key: str | None,
    hist_pub_ids: set[str],
    hist_dois: set[str],
) -> dict:
    """Expand the Stage A pool via S2 forward citation chains.

    For each of the top-50 Stage A seeds (ranked by influentialCitationCount),
    fetches up to 1000 citing papers from S2, filters by publication type,
    fields of study, and the shared phrase gate, then merges survivors into
    the Stage A pool on pub_id.

    Returns a dict with Stage B statistics and a _merged_pool key.
    """
    seeds = select_citation_seeds(stage_a_pool, hist_pub_ids, top_k=50)
    n_seeds = len(seeds)

    if not seeds:
        return {
            "_merged_pool": stage_a_pool,
            "n_seeds": 0, "n_raw": 0, "n_after_type_fos": 0,
            "n_after_gate": 0, "n_merged": 0, "n_bumped_nonzero": 0,
        }

    item_fos = item.fos_set

    citing_by_paperid: dict[str, dict] = {}
    edges_by_paperid:  dict[str, list[dict]] = {}
    n_raw_total = 0

    for seed in seeds:
        cit_results = fetch_citations(
            paper_id=seed.s2_paper_id,
            cache_dir=cache_dir,
            limit=1000,
            api_key=s2_api_key,
        )
        n_raw_total += len(cit_results)
        for result in cit_results:
            citing_paper = result.get("citingPaper") or {}
            pid = citing_paper.get("paperId") or ""
            if not pid:
                continue
            edge = {
                "seed_pub_id":    seed.pub_id,
                "intents":        result.get("intents") or [],
                "is_influential": bool(result.get("isInfluential")),
            }
            if pid not in citing_by_paperid:
                citing_by_paperid[pid] = citing_paper
                edges_by_paperid[pid] = []
            edges_by_paperid[pid].append(edge)

    _ACCEPTED_TYPES = {"journalarticle", "review", "metaanalysis"}
    type_fos_kept: list[tuple] = []

    for pid, paper in citing_by_paperid.items():
        pub_types = {pt.lower().replace(" ", "") for pt in (paper.get("publicationTypes") or [])}
        if not pub_types.intersection(_ACCEPTED_TYPES):
            continue
        paper_fos = {f.lower() for f in (paper.get("fieldsOfStudy") or [])}
        if paper_fos and not paper_fos.intersection(item_fos):
            continue
        year = paper.get("year")
        if year is not None and (year < 1950 or year > TODAY_YEAR):
            continue
        type_fos_kept.append((pid, paper, edges_by_paperid[pid]))

    n_after_type_fos = len(type_fos_kept)

    b_candidates: list[Candidate] = []
    for pid, paper, edges in type_fos_kept:
        c = normalize_s2(paper)
        if not c:
            continue
        c.stage_b_edges.extend(edges)
        c.sources = ["semanticscholar_citations"]
        b_candidates.append(c)

    b_candidates = phrase_gate(b_candidates, item, hist_pub_ids, hist_dois)
    n_after_gate = len(b_candidates)

    a_by_pub_id: dict[str, Candidate] = {c.pub_id: c for c in stage_a_pool}
    n_merged = 0

    for b_cand in b_candidates:
        existing = a_by_pub_id.get(b_cand.pub_id)
        if existing is not None:
            if "semanticscholar_citations" not in existing.sources:
                existing.sources.append("semanticscholar_citations")
            existing.stage_b_edges.extend(b_cand.stage_b_edges)
        else:
            a_by_pub_id[b_cand.pub_id] = b_cand
            n_merged += 1

    merged_pool = list(a_by_pub_id.values())

    _STRONG = {"background", "methodology", "extension"}
    n_bumped_nonzero = sum(
        1 for c in merged_pool
        if any(
            e.get("is_influential") or
            {str(i).lower() for i in (e.get("intents") or [])}.intersection(_STRONG)
            for e in c.stage_b_edges
        )
    )

    logger.info(
        "[stage_b] seeds=%d raw=%d after_type_fos=%d after_gate=%d "
        "merged=%d bumped_nonzero=%d",
        n_seeds, n_raw_total, n_after_type_fos, n_after_gate, n_merged, n_bumped_nonzero,
    )

    return {
        "_merged_pool":     merged_pool,
        "n_seeds":          n_seeds,
        "n_raw":            n_raw_total,
        "n_after_type_fos": n_after_type_fos,
        "n_after_gate":     n_after_gate,
        "n_merged":         n_merged,
        "n_bumped_nonzero": n_bumped_nonzero,
    }


def run_item(
    item: ItemQueryPlan,
    cache_dir: Path,
    s2_api_key: str | None,
    sources: list[str],
    passes: list[str],
    hist_pub_ids: set[str],
    hist_dois: set[str],
) -> tuple[list[Candidate], dict]:
    """Run Stage A queries, phrase gate, and Stage B expansion for one item.

    Returns (merged_pool, stage_b_stats).
    """
    raw_candidates: list[Candidate] = []

    for pass_name, pass_spec in item.passes.items():
        if pass_name not in passes:
            continue

        if "openalex" in sources:
            spec = pass_spec["openalex"]
            results = search_works(
                cache_dir=cache_dir,
                phrases=spec.get("phrases"),
                topic_ids=spec.get("topic_ids"),
                year_min=spec.get("year_min"),
                year_max=spec.get("year_max"),
                pub_type=spec.get("pub_type"),
                max_results=spec.get("max_results", 100),
            )
            for r in results:
                c = normalize_openalex(r)
                if c:
                    raw_candidates.append(c)
            logger.info("[%s] pass=%s openalex raw=%d", item.item_id, pass_name, len(results))

        if "europepmc" in sources:
            spec = pass_spec["europepmc"]
            results = epmc_search(
                cache_dir=cache_dir,
                phrases=spec.get("phrases"),
                year_min=spec.get("year_min"),
                year_max=spec.get("year_max"),
                pub_type=spec.get("pub_type"),
                max_results=spec.get("max_results", 100),
            )
            for r in results:
                c = normalize_europepmc(r)
                if c:
                    raw_candidates.append(c)
            logger.info("[%s] pass=%s europepmc raw=%d", item.item_id, pass_name, len(results))

        if "semanticscholar" in sources:
            spec = pass_spec["semanticscholar"]
            s2_queries: list[str] = spec.get("queries", [item.primary_name])
            s2_all: list[dict] = []
            for q in s2_queries:
                results = s2_search(
                    cache_dir=cache_dir,
                    query=q,
                    year_min=spec.get("year_min"),
                    year_max=spec.get("year_max"),
                    max_results=spec.get("max_results", 100),
                    api_key=s2_api_key,
                    fields_of_study=spec.get("fields_of_study"),
                    min_citation_count=spec.get("min_citation_count"),
                    publication_types=spec.get("publication_types"),
                )
                s2_all.extend(results)
            s2_cap = spec.get("max_results", 100)
            for r in s2_all[:s2_cap]:
                c = normalize_s2(r)
                if c:
                    raw_candidates.append(c)
            logger.info(
                "[%s] pass=%s semanticscholar raw=%d (across %d queries)",
                item.item_id, pass_name, min(len(s2_all), s2_cap), len(s2_queries),
            )

    stage_a_pool = dedup_candidates(raw_candidates)
    logger.info(
        "[%s] stage_a pre-dedup=%d post-dedup=%d",
        item.item_id, len(raw_candidates), len(stage_a_pool),
    )

    stage_a_pool = phrase_gate(stage_a_pool, item, hist_pub_ids, hist_dois)
    logger.info("[%s] stage_a post-gate=%d", item.item_id, len(stage_a_pool))

    stage_b_stats = _run_stage_b(
        stage_a_pool=stage_a_pool,
        item=item,
        cache_dir=cache_dir,
        s2_api_key=s2_api_key,
        hist_pub_ids=hist_pub_ids,
        hist_dois=hist_dois,
    )
    merged_pool = stage_b_stats.pop("_merged_pool")
    return merged_pool, stage_b_stats


def lookup_missing_landmarks(
    hist_refs: list[dict],
    existing_candidates: list[Candidate],
    cache_dir: Path,
    s2_api_key: str | None,
) -> list[Candidate]:
    """Fetch any historical reference not already in the candidate pool via DOI lookup."""
    existing_dois   = {c.doi for c in existing_candidates if c.doi}
    existing_pubids = {c.pub_id for c in existing_candidates}
    new_candidates: list[Candidate] = []

    for ref in hist_refs:
        doi = (ref.get("doi") or "").lower().strip()
        if not doi:
            continue
        if doi in existing_dois or ref.get("pub_id", "") in existing_pubids:
            continue

        logger.info("landmark supplementary lookup: doi=%s", doi)
        found_any = False

        raw_oa = oa_lookup(doi=doi, cache_dir=cache_dir)
        if raw_oa:
            c = normalize_openalex(raw_oa)
            if c:
                new_candidates.append(c)
                found_any = True

        raw_epmc = epmc_lookup(doi=doi, cache_dir=cache_dir)
        if raw_epmc:
            c = normalize_europepmc(raw_epmc)
            if c:
                new_candidates.append(c)
                found_any = True

        raw_s2 = s2_lookup(doi=doi, cache_dir=cache_dir)
        if raw_s2:
            c = normalize_s2(raw_s2)
            if c:
                new_candidates.append(c)
                found_any = True

        if not found_any:
            logger.warning("landmark doi=%s not found in any source", doi)

    return dedup_candidates(new_candidates) if new_candidates else []


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Phase 3 systematic per-item literature search (host runner)."
    )
    parser.add_argument("--mode", choices=["poc", "full", "single"], required=True)
    parser.add_argument("--ids", default="")
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--cache-dir", default="outputs/cache")
    parser.add_argument("--output-dir", default="outputs/phase3/candidates")
    parser.add_argument("--index", default="")
    parser.add_argument("--apikeys", default="code/.apikeys")
    parser.add_argument("--sources", default="openalex,europepmc,semanticscholar")
    parser.add_argument("--passes", default="all_years,recent,reviews",
                        help="Comma-separated passes to run (all_years, recent, reviews).")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--force-refresh", action="store_true")
    args = parser.parse_args()

    ws           = Path(args.workspace)
    cache_dir    = ws / args.cache_dir
    output_dir   = ws / args.output_dir
    apikeys_path = ws / args.apikeys
    index_path   = (
        Path(args.index) if args.index
        else ws / ".status" / f"candidates_index_{TODAY}.md"
    )
    process_path   = ws / "process_details.json"
    task_path      = ws / "task_details.json"
    crosswalk_path = ws / "outputs" / "phase2" / "openalex_crosswalk.json"

    s2_api_key = load_api_key("S2_API_KEY", apikeys_path)
    if s2_api_key:
        logger.info("Semantic Scholar API key loaded.")
    else:
        logger.info("No S2 API key — rate limited to 1 rps.")

    logger.info("Loading process_details.json and task_details.json ...")
    all_plans = build_plans_from_json(process_path, task_path, crosswalk_path)
    logger.info(
        "Loaded %d plans (%d processes + %d tasks).",
        len(all_plans),
        sum(1 for p in all_plans if p.item_kind == "process"),
        sum(1 for p in all_plans if p.item_kind == "task"),
    )

    logger.info("Loading historical references ...")
    historical_map = load_historical_refs(process_path, task_path)
    total_hist = sum(len(v) for v in historical_map.values())
    logger.info("Loaded %d historical references across %d items.", total_hist, len(historical_map))

    if args.mode == "poc":
        plans = filter_plans_by_ids(all_plans, POC_ITEM_IDS)
    elif args.mode == "single":
        ids = [i.strip() for i in args.ids.split(",") if i.strip()]
        plans = filter_plans_by_ids(all_plans, ids)
    else:
        plans = all_plans

    if not plans:
        logger.error("No matching items for mode=%s ids=%r", args.mode, args.ids)
        sys.exit(1)
    logger.info("Running %d items in mode=%s.", len(plans), args.mode)

    sources = [s.strip() for s in args.sources.split(",")]
    passes  = [p.strip() for p in args.passes.split(",")]

    t_start    = time.monotonic()
    index_rows: list[dict] = []

    for plan in plans:
        logger.info("--- Processing %s (%s) ---", plan.item_id, plan.primary_name)
        item_start = time.monotonic()

        hist_refs    = historical_map.get(plan.item_id, [])
        hist_pub_ids = {r["pub_id"] for r in hist_refs}
        hist_dois    = {(r.get("doi") or "").lower() for r in hist_refs if r.get("doi")}

        candidates, stage_b_stats = run_item(
            item=plan,
            cache_dir=cache_dir,
            s2_api_key=s2_api_key,
            sources=sources,
            passes=passes,
            hist_pub_ids=hist_pub_ids,
            hist_dois=hist_dois,
        )

        if not candidates:
            logger.warning("[%s] Zero candidates after dedup — check query.", plan.item_id)

        landmark_extras = lookup_missing_landmarks(
            hist_refs=hist_refs,
            existing_candidates=candidates,
            cache_dir=cache_dir,
            s2_api_key=s2_api_key,
        )
        if landmark_extras:
            logger.info("[%s] landmark lookup added %d candidate(s)",
                        plan.item_id, len(landmark_extras))
            candidates = dedup_candidates(candidates + landmark_extras)

        top_picks, recent_picks, all_sorted = select_candidates(
            candidates=candidates,
            item=plan,
            today_year=TODAY_YEAR,
            landmark_pub_ids=hist_pub_ids,
        )

        all_cand_pub_ids = {c.pub_id for c in all_sorted}
        all_cand_dois    = {c.doi   for c in all_sorted if c.doi}
        hist_hits = sum(
            1 for r in hist_refs
            if r["pub_id"] in all_cand_pub_ids
            or (r.get("doi") and r["doi"].lower() in all_cand_dois)
        )

        index_rows.append({
            "item_id":      plan.item_id,
            "kind":         plan.item_kind,
            "n_candidates": len(all_sorted),
            "n_picked":     len(top_picks) + len(recent_picks),
            "n_landmarks":  hist_hits,
            "n_lm_total":   len(hist_refs),
        })

        elapsed = time.monotonic() - item_start
        logger.info(
            "[%s] candidates=%d picked=%d hist_found=%d/%d "
            "stage_b_seeds=%d stage_b_merged=%d wall=%.1fs",
            plan.item_id, len(all_sorted), len(top_picks) + len(recent_picks),
            hist_hits, len(hist_refs),
            stage_b_stats.get("n_seeds", 0), stage_b_stats.get("n_merged", 0),
            elapsed,
        )

        if args.write:
            out_path = write_item_markdown(
                item=plan,
                found_picks=top_picks,
                recent_picks=recent_picks,
                all_sorted=all_sorted,
                landmark_entries=hist_refs,
                output_dir=output_dir,
                today_year=TODAY_YEAR,
                stage_b_n_seeds=stage_b_stats.get("n_seeds", 0),
                stage_b_n_kept=stage_b_stats.get("n_after_gate", 0),
            )
            logger.info("[%s] Written: %s", plan.item_id, out_path)
        else:
            logger.info("[%s] dry-run — pass --write to save.", plan.item_id)

    if args.write and index_rows:
        index_path.parent.mkdir(parents=True, exist_ok=True)
        write_index(index_path, index_rows, output_dir)
        logger.info("Index written: %s", index_path)

    wall = time.monotonic() - t_start
    print("\n" + "=" * 60)
    print(f"Phase 3 search complete — mode={args.mode}")
    print(f"  Items processed    : {len(plans)}")
    print(f"  Candidates (dedup) : {sum(r['n_candidates'] for r in index_rows)}")
    print(f"  Picked             : {sum(r['n_picked']     for r in index_rows)}")
    hist_found = sum(r['n_landmarks'] for r in index_rows)
    hist_total = sum(r['n_lm_total']  for r in index_rows)
    print(f"  Historical found   : {hist_found}/{hist_total}")
    print(f"  Wall time          : {wall:.1f}s")
    if not args.write:
        print("  NOTE: --write not set; no files written.")
    print("=" * 60)


if __name__ == "__main__":
    main()
