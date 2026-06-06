#!/usr/bin/env python3
"""
enrich_no_doi.py — Title-based DOI lookup for refs missing a DOI (PR-H3).

PR-D's ``enrich_pdf_locations.py`` requires a DOI to look up pdf_locations.
After the 2026-06-02 wet-run, 153 refs in the catalog still have
``ids.doi is None`` and therefore no pdf_locations.  They show up in
``analyze_failures.py`` as the ``[] :: no candidate locations`` bucket
(156 there, slightly different because of retry-failed dynamics).

This script queries OpenAlex by title+year, scores each candidate by
(title-similarity, year-proximity, first-author-surname match),
auto-stamps ``ids.doi`` and ``ids.openalex_id`` on HIGH-confidence
matches, and writes a markdown report listing MED-confidence
candidates for human review.

Conservative bias: a wrong DOI silently corrupts the catalog, so the
HIGH threshold is set so that title and author both have to match
strongly with year off by ≤1.  MED never auto-stamps; the maintainer
copies the candidate into the ref by hand from the report.

Pipeline (this is step 1 of 3 for end-to-end recovery):

  1.  Run THIS script with ``--write``.  Catalog gets new ``ids.doi``
      stamps for HIGH-confidence matches.
  2.  Re-run ``enrich_pdf_locations.py`` so PR-D populates
      ``pdf_locations`` for the newly-DOI'd refs.
  3.  Re-run ``acquire_pdf.py --mode full --write --retry-failed`` so
      PR-E attempts acquisition for those refs.

Usage (run from the workspace root, ``Claude-research/``)::

    # Dry-run: compute matches, write report, no catalog changes.
    python code/literature_search/enrich_no_doi.py

    # Wet-run: same, plus auto-stamp HIGH-confidence DOIs.
    python code/literature_search/enrich_no_doi.py --write

Outputs (under ``--output-dir``, default ``outputs/analysis/``)::

    enrich_no_doi_<YYYY-MM-DD>.md       human-readable report
    enrich_no_doi_<YYYY-MM-DD>.json     full per-ref outcomes

Exit codes:
    0 — clean
    1 — data issue (no no-DOI refs found, or catalog parse error)
    2 — catalog file missing
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import shutil
import sys
import time
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator

try:
    import requests
except ImportError:  # pragma: no cover - environment misconfig
    raise ImportError("'requests' is required: pip install requests")

# Local imports.  Catalog handling and cache helpers already live in the
# package; we reuse them rather than duplicate.
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from cache import cache_get_or_fetch  # noqa: E402


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Author parsing
# ---------------------------------------------------------------------------

# Common stop-words to drop from a title before similarity scoring.
# Kept short on purpose — large stop-word lists tend to hurt more than
# they help on short academic titles.
_TITLE_STOPWORDS: frozenset[str] = frozenset({
    "a", "an", "and", "as", "at", "by", "for", "from", "in", "of",
    "on", "or", "the", "to", "with",
})


def parse_surnames(authors: str) -> list[str]:
    """Extract surnames from an APA-style authors string.

    Input shapes encountered in the catalog:

      ``Shanks, D. R.``
      ``Staddon, J. E. R., & Cerutti, D. T.``
      ``Smith, A., Jones, B., & Brown, C.``

    The function splits on ``&`` (Oxford-style), then on ``;``, then
    takes the substring before the first comma in each piece as the
    surname.  Lowercased so callers can compare without re-normalising.
    Returns an empty list if ``authors`` is empty or unparseable.
    """
    if not authors or not isinstance(authors, str):
        return []
    surnames: list[str] = []
    # Split on " & " first; APA convention.
    pieces = re.split(r"\s*&\s*|\s*;\s*", authors)
    for piece in pieces:
        piece = piece.strip()
        if not piece:
            continue
        # Surname is everything before the first comma.
        head = piece.split(",", 1)[0].strip()
        if head:
            surnames.append(head.lower())
    return surnames


# ---------------------------------------------------------------------------
# Title normalisation + similarity
# ---------------------------------------------------------------------------

def _ascii_fold(text: str) -> str:
    """Strip diacritics to ASCII (so naïve == naive for matching)."""
    return "".join(
        c for c in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(c)
    )


def normalize_title(title: str) -> set[str]:
    """Return the bag of normalized content-words in ``title``.

    Steps: ascii-fold, lowercase, strip everything but ``[a-z0-9 ]``,
    drop stop-words and length-1 tokens.  Used by
    :func:`title_similarity`.

    Stop-words are dropped because they swamp short titles ("Learning"
    matches "the learning" 0.5 instead of 1.0 if "the" is kept).
    Length-1 tokens (single letters from author initials accidentally
    landing in a title etc.) are dropped for the same reason.
    """
    if not title:
        return set()
    s = _ascii_fold(title).lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    words = {w for w in s.split() if len(w) > 1 and w not in _TITLE_STOPWORDS}
    return words


def title_similarity(a: str, b: str) -> float:
    """Jaccard similarity on normalized title-word sets.

    Returns 0.0 if either title is empty after normalisation.  Jaccard
    is symmetric and easy to interpret: 1.0 means identical content
    words, 0.0 means no overlap.  Good enough for academic titles
    where word reuse is high and word order is reasonably stable.
    """
    sa = normalize_title(a)
    sb = normalize_title(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

# Confidence tiers — tuned conservatively.  See module docstring for
# rationale.  Tuning point: if HIGH proves too strict in practice the
# maintainer can drop ``high_title`` to 0.85 and re-run.
@dataclass(frozen=True)
class Thresholds:
    high_title: float = 0.90
    high_year_delta: int = 1
    high_require_author: bool = True
    med_title: float = 0.70
    med_year_delta: int = 2


DEFAULT_THRESHOLDS = Thresholds()


@dataclass
class Score:
    title_sim: float
    year_delta: int | None      # absolute; None if either year missing
    author_match: bool
    tier: str                   # "high", "med", "low"


def year_delta(ref_year: int | None, cand_year: int | None) -> int | None:
    if ref_year is None or cand_year is None:
        return None
    try:
        return abs(int(ref_year) - int(cand_year))
    except (TypeError, ValueError):
        return None


def score_candidate(
    ref_title: str,
    ref_year: int | None,
    ref_surnames: list[str],
    cand_title: str,
    cand_year: int | None,
    cand_surnames: list[str],
    *,
    thresholds: Thresholds = DEFAULT_THRESHOLDS,
) -> Score:
    """Score one candidate match against the ref's metadata.

    Returns a :class:`Score` carrying the three component values and
    the tier classification.
    """
    title_sim = title_similarity(ref_title, cand_title)
    delta = year_delta(ref_year, cand_year)
    ref_set = {s for s in ref_surnames if s}
    cand_set = {s for s in cand_surnames if s}
    author_match = bool(ref_set & cand_set)

    # Decide tier.
    if (title_sim >= thresholds.high_title
            and delta is not None
            and delta <= thresholds.high_year_delta
            and (author_match or not thresholds.high_require_author)):
        tier = "high"
    elif (title_sim >= thresholds.med_title
          and (
              (delta is not None and delta <= thresholds.med_year_delta)
              or author_match
          )):
        tier = "med"
    else:
        tier = "low"

    return Score(title_sim=title_sim, year_delta=delta,
                 author_match=author_match, tier=tier)


# ---------------------------------------------------------------------------
# OpenAlex title search
# ---------------------------------------------------------------------------

_OPENALEX_BASE = "https://api.openalex.org/works"
_RATE_SEC = 0.1  # OpenAlex polite-pool limit is 10 req/s
_last_call: dict[str, float] = {}


def _throttle(host: str = "api.openalex.org") -> None:
    now = time.monotonic()
    gap = now - _last_call.get(host, 0.0)
    if gap < _RATE_SEC:
        time.sleep(_RATE_SEC - gap)
    _last_call[host] = time.monotonic()


def _read_apikeys_mailto() -> str:
    """Read OPENALEX_MAILTO from env or code/.apikeys."""
    val = os.environ.get("OPENALEX_MAILTO", "").strip()
    if val:
        return val
    apikeys = _HERE / ".apikeys"
    if apikeys.exists():
        for line in apikeys.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("OPENALEX_MAILTO="):
                return line.split("=", 1)[1].strip()
    return "hedannotation@gmail.com"  # CLAUDE.md default


def _build_query_key(title: str, year: int | None) -> str:
    """Stable cache key for a (title, year) lookup."""
    norm = " ".join(sorted(normalize_title(title)))
    return f"{norm}::{year}"


def _do_openalex_search(
    title: str,
    year: int | None,
    *,
    mailto: str,
    per_page: int = 10,
) -> dict | None:
    """Live OpenAlex API call.  Returns parsed JSON or None on error.

    Filters on publication_year ±1 of ``year`` when ``year`` is known;
    when ``year`` is None the year filter is omitted entirely.  Title
    is passed as the free-text ``search`` parameter.
    """
    _throttle()
    params: dict[str, str] = {
        "search": title,
        "per_page": str(per_page),
        "mailto": mailto,
    }
    if isinstance(year, int):
        params["filter"] = f"publication_year:{year - 1}-{year + 1}"
    try:
        resp = requests.get(_OPENALEX_BASE, params=params, timeout=20)
    except requests.RequestException as exc:
        logger.info("openalex network error for title=%r year=%r: %s",
                    title[:60], year, exc)
        return None
    if resp.status_code != 200:
        logger.info("openalex HTTP %d for title=%r year=%r",
                    resp.status_code, title[:60], year)
        return None
    try:
        return resp.json()
    except ValueError as exc:
        logger.info("openalex JSON parse error: %s", exc)
        return None


def search_openalex(
    title: str,
    year: int | None,
    *,
    cache_dir: Path,
    mailto: str,
    fetch_fn: Callable[[str, int | None], dict | None] | None = None,
) -> list[dict]:
    """Search OpenAlex by title (±1y window if year known).

    Returns a list of candidate work-dicts (the ``results`` array
    of the OpenAlex Works response).  Cached on (title, year);
    successive runs hit the cache.

    ``fetch_fn`` is injectable for tests so the network isn't touched.
    """
    if not title or not title.strip():
        return []

    def _fetch_live() -> dict | None:
        if fetch_fn is not None:
            return fetch_fn(title, year)
        return _do_openalex_search(title, year, mailto=mailto)

    cached = cache_get_or_fetch(
        cache_dir=cache_dir,
        source="openalex_title_search",
        key=_build_query_key(title, year),
        fetch=_fetch_live,
        stable=False,
        max_age_days=30,
    )
    if not cached:
        return []
    return cached.get("results") or []


# ---------------------------------------------------------------------------
# Candidate extraction from OpenAlex response
# ---------------------------------------------------------------------------

def _strip_doi_prefix(doi_raw: str) -> str:
    """Strip the ``https://doi.org/`` prefix OpenAlex prepends."""
    s = (doi_raw or "").strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/",
                   "https://dx.doi.org/", "doi:"):
        if s.startswith(prefix):
            return s[len(prefix):]
    return s


def _extract_candidate_metadata(work: dict) -> dict:
    """Pull the fields we care about out of an OpenAlex work record."""
    doi = _strip_doi_prefix(work.get("doi") or "")
    openalex_url = work.get("id") or ""
    openalex_id = ""
    if openalex_url.startswith("https://openalex.org/"):
        openalex_id = openalex_url.split("/")[-1]
    surnames: list[str] = []
    for au in (work.get("authorships") or []):
        name = ((au or {}).get("author") or {}).get("display_name") or ""
        if not name:
            continue
        # OpenAlex display names are "First Last" or "First M. Last".
        last = name.strip().split()[-1].lower()
        if last:
            surnames.append(last)
    return {
        "doi": doi,
        "openalex_id": openalex_id,
        "title": work.get("title") or work.get("display_name") or "",
        "year": work.get("publication_year"),
        "surnames": surnames,
        "cited_by_count": work.get("cited_by_count") or 0,
    }


# ---------------------------------------------------------------------------
# Picking the best match
# ---------------------------------------------------------------------------

@dataclass
class Match:
    """The best match for a ref, with its score and tier."""
    ref_owner_id: str
    ref_idx: int
    ref_title: str
    ref_year: int | None
    ref_authors: str
    candidate: dict | None           # _extract_candidate_metadata shape
    score: Score | None              # None if no candidates found
    tier: str = "no_match"           # "high", "med", "low", "no_match"


def pick_best(
    ref: dict,
    cand_works: list[dict],
    *,
    thresholds: Thresholds = DEFAULT_THRESHOLDS,
) -> tuple[dict | None, Score | None]:
    """Score every candidate; return the highest-scoring (with score).

    "Highest" is by: tier first (high > med > low), then title
    similarity, then cited_by_count (more-cited = more canonical).
    Returns (None, None) when ``cand_works`` is empty.
    """
    ref_title = ref.get("title") or ""
    ref_year = ref.get("year")
    ref_surnames = parse_surnames(ref.get("authors") or "")

    scored: list[tuple[Score, dict, dict]] = []  # (score, extracted, raw)
    for w in cand_works:
        cm = _extract_candidate_metadata(w)
        s = score_candidate(
            ref_title=ref_title,
            ref_year=ref_year,
            ref_surnames=ref_surnames,
            cand_title=cm["title"],
            cand_year=cm["year"],
            cand_surnames=cm["surnames"],
            thresholds=thresholds,
        )
        # Skip candidates without a DOI — we can't stamp anything useful.
        if not cm["doi"]:
            continue
        scored.append((s, cm, w))

    if not scored:
        return None, None

    tier_rank = {"high": 0, "med": 1, "low": 2}

    def sort_key(item: tuple[Score, dict, dict]) -> tuple:
        s, cm, _ = item
        return (tier_rank[s.tier], -s.title_sim, -cm["cited_by_count"])

    scored.sort(key=sort_key)
    best_score, best_meta, _ = scored[0]
    return best_meta, best_score


# ---------------------------------------------------------------------------
# Catalog walk
# ---------------------------------------------------------------------------

def iter_no_doi_refs(processes: dict, tasks: list) -> Iterator[tuple[str, int, dict]]:
    """Yield (owner_id, ref_idx, ref) for every ref with no DOI."""
    items: list[tuple[str, dict]] = []
    for p in (processes or {}).get("processes") or []:
        items.append((p.get("process_id") or "", p))
    for t in tasks or []:
        items.append((t.get("hedtsk_id") or "", t))
    for owner_id, item in items:
        for idx, ref in enumerate(item.get("references") or []):
            doi = ((ref.get("ids") or {}).get("doi") or "").strip()
            if doi:
                continue
            yield owner_id, idx, ref


# ---------------------------------------------------------------------------
# Catalog I/O (staged write convention from CLAUDE.md)
# ---------------------------------------------------------------------------

def _load_catalog(workspace: Path) -> tuple[dict, list, Path, Path]:
    p_path = workspace / "process_details.json"
    t_path = workspace / "task_details.json"
    for path in (p_path, t_path):
        if not path.exists():
            raise FileNotFoundError(path)
    with p_path.open("r", encoding="utf-8") as f:
        processes = json.load(f)
    with t_path.open("r", encoding="utf-8") as f:
        tasks = json.load(f)
    return processes, tasks, p_path, t_path


def _save_catalog(
    processes: dict,
    tasks: list,
    p_path: Path,
    t_path: Path,
    *,
    workspace: Path,
) -> None:
    """Stage to .scratch/enrich_no_doi/ then copy into place."""
    scratch = workspace / ".scratch" / "enrich_no_doi"
    scratch.mkdir(parents=True, exist_ok=True)
    staged_p = scratch / p_path.name
    staged_t = scratch / t_path.name
    with staged_p.open("w", encoding="utf-8") as f:
        json.dump(processes, f, indent=2, ensure_ascii=False)
        f.write("\n")
    with staged_t.open("w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)
        f.write("\n")
    shutil.copyfile(staged_p, p_path)
    shutil.copyfile(staged_t, t_path)


# ---------------------------------------------------------------------------
# Report writers
# ---------------------------------------------------------------------------

def _utc_today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def format_markdown_report(matches: list[Match], *, write_mode: bool) -> str:
    """Human-readable summary grouped by tier."""
    by_tier: dict[str, list[Match]] = {"high": [], "med": [], "low": [], "no_match": []}
    for m in matches:
        by_tier[m.tier].append(m)

    lines: list[str] = []
    lines.append(f"# enrich_no_doi — {_utc_today()}")
    lines.append("")
    lines.append(f"Total refs walked: **{len(matches)}**.")
    lines.append("")
    lines.append("| Tier | Count | Auto-action |")
    lines.append("|---|---:|---|")
    lines.append(f"| HIGH (auto-stamp candidate)        | {len(by_tier['high'])} "
                 f"| {'Stamped' if write_mode else 'WOULD stamp (rerun with --write)'} |")
    lines.append(f"| MED  (human review needed)         | {len(by_tier['med'])} "
                 f"| Listed below for manual review |")
    lines.append(f"| LOW  (weak match, skipped)         | {len(by_tier['low'])} "
                 f"| Not stamped |")
    lines.append(f"| no_match (no candidates returned)  | {len(by_tier['no_match'])} "
                 f"| Genuine gap — title not in OpenAlex |")
    lines.append("")

    for tier_label, header in [
        ("high", "## HIGH-confidence matches"),
        ("med", "## MED-confidence matches (REVIEW BEFORE STAMPING)"),
        ("low", "## LOW-confidence (not stamped)"),
        ("no_match", "## No candidates"),
    ]:
        bucket = by_tier[tier_label]
        if not bucket:
            continue
        lines.append(header)
        lines.append("")
        lines.append("| Ref | Year | Title | Best candidate DOI | Title sim | Year Δ | Author? |")
        lines.append("|---|---:|---|---|---:|---:|:---:|")
        for m in bucket:
            ref_id = f"`{m.ref_owner_id}#{m.ref_idx}`"
            title = (m.ref_title or "")[:60]
            if m.candidate is None:
                lines.append(
                    f"| {ref_id} | {m.ref_year or '?'} | {title} | — | — | — | — |"
                )
            else:
                doi = m.candidate.get("doi") or "—"
                ts = f"{m.score.title_sim:.2f}" if m.score else "—"
                yd = (str(m.score.year_delta) if m.score and m.score.year_delta is not None
                      else "—")
                am = "✓" if (m.score and m.score.author_match) else "—"
                lines.append(
                    f"| {ref_id} | {m.ref_year or '?'} | {title} "
                    f"| `{doi}` | {ts} | {yd} | {am} |"
                )
        lines.append("")

    return "\n".join(lines)


def format_json_sidecar(matches: list[Match]) -> str:
    out: list[dict] = []
    for m in matches:
        cand = None
        if m.candidate is not None:
            cand = {k: v for k, v in m.candidate.items() if k != "surnames"}
        score = None
        if m.score is not None:
            score = {
                "title_sim": m.score.title_sim,
                "year_delta": m.score.year_delta,
                "author_match": m.score.author_match,
                "tier": m.score.tier,
            }
        out.append({
            "ref_owner_id": m.ref_owner_id,
            "ref_idx": m.ref_idx,
            "ref_title": m.ref_title,
            "ref_year": m.ref_year,
            "ref_authors": m.ref_authors,
            "candidate": cand,
            "score": score,
            "tier": m.tier,
        })
    return json.dumps({"when": _utc_today(), "matches": out},
                      indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_enrich(
    processes: dict,
    tasks: list,
    *,
    cache_dir: Path,
    mailto: str,
    limit: int = 0,
    thresholds: Thresholds = DEFAULT_THRESHOLDS,
    fetch_fn: Callable[[str, int | None], dict | None] | None = None,
) -> list[Match]:
    """Walk every no-DOI ref, query OpenAlex, score, return matches.

    Does NOT mutate the catalog.  The caller decides whether to apply
    HIGH matches based on write mode.
    """
    matches: list[Match] = []
    for n, (owner_id, idx, ref) in enumerate(iter_no_doi_refs(processes, tasks)):
        if limit and n >= limit:
            break

        ref_title = ref.get("title") or ""
        ref_year = ref.get("year")

        cand_works = search_openalex(
            ref_title, ref_year,
            cache_dir=cache_dir,
            mailto=mailto,
            fetch_fn=fetch_fn,
        )

        best, score = pick_best(ref, cand_works, thresholds=thresholds)
        if best is None:
            tier = "no_match"
        else:
            tier = score.tier

        matches.append(Match(
            ref_owner_id=owner_id,
            ref_idx=idx,
            ref_title=ref_title,
            ref_year=ref_year,
            ref_authors=ref.get("authors") or "",
            candidate=best,
            score=score,
            tier=tier,
        ))

        logger.info("[%s#%d] tier=%s title=%r%s",
                    owner_id, idx, tier, ref_title[:60],
                    f" -> doi={best['doi']}" if best else "")
    return matches


def apply_high_matches(
    matches: list[Match],
    processes: dict,
    tasks: list,
) -> int:
    """Stamp ``ids.doi`` and ``ids.openalex_id`` on HIGH matches.

    Returns the number of refs updated.  Mutates the catalog dicts.
    """
    # Index for fast lookup by (owner_id, idx).
    by_owner: dict[str, list[dict]] = {}
    for p in (processes or {}).get("processes") or []:
        by_owner[p.get("process_id") or ""] = p.get("references") or []
    for t in tasks or []:
        by_owner[t.get("hedtsk_id") or ""] = t.get("references") or []

    updated = 0
    for m in matches:
        if m.tier != "high" or m.candidate is None:
            continue
        refs = by_owner.get(m.ref_owner_id, [])
        if m.ref_idx >= len(refs):
            logger.warning("ref index out of range: %s#%d",
                           m.ref_owner_id, m.ref_idx)
            continue
        ref = refs[m.ref_idx]
        ids = ref.setdefault("ids", {})
        ids["doi"] = m.candidate["doi"]
        if m.candidate.get("openalex_id"):
            ids["openalex_id"] = m.candidate["openalex_id"]
        updated += 1
    return updated


# ---------------------------------------------------------------------------
# CLI driver
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workspace", default=".",
                   help="Workspace root (Claude-research/).  Default: cwd.")
    p.add_argument("--cache-dir", default="<auto>",
                   help="Cache root.  Resolves via --cache-dir > "
                        "$HED_CACHE_DIR > <workspace>/outputs/cache.")
    p.add_argument("--output-dir", default="outputs/analysis",
                   help="Workspace-relative output for report + JSON sidecar.")
    p.add_argument("--write", action="store_true",
                   help="Auto-stamp ids.doi on HIGH-confidence matches.  "
                        "Default is dry-run (compute matches, write report, "
                        "leave catalog unchanged).")
    p.add_argument("--limit", type=int, default=0,
                   help="Cap on number of no-DOI refs processed (0 = no cap).")
    p.add_argument("--mailto", default="",
                   help="Override the mailto string sent to OpenAlex.")
    p.add_argument("--verbose", "-v", action="store_true")
    return p.parse_args(argv)


def _resolve_cache_dir(arg_value: str, workspace: Path) -> Path:
    if arg_value and arg_value != "<auto>":
        p = Path(arg_value)
        return p if p.is_absolute() else workspace / p
    env_val = os.environ.get("HED_CACHE_DIR")
    if env_val:
        return Path(env_val)
    return workspace / "outputs" / "cache"


def main(
    argv: list[str] | None = None,
    *,
    fetch_fn: Callable[[str, int | None], dict | None] | None = None,
) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    ws = Path(args.workspace).resolve()
    cache_dir = _resolve_cache_dir(args.cache_dir, ws)
    mailto = args.mailto or _read_apikeys_mailto()

    logger.info("workspace : %s", ws)
    logger.info("cache_dir : %s", cache_dir)
    logger.info("mailto    : %s", mailto)
    logger.info("write     : %s", args.write)

    try:
        processes, tasks, p_path, t_path = _load_catalog(ws)
    except FileNotFoundError as exc:
        logger.error("catalog file missing: %s", exc)
        return 2

    matches = run_enrich(
        processes, tasks,
        cache_dir=cache_dir,
        mailto=mailto,
        limit=args.limit,
        fetch_fn=fetch_fn,
    )

    if not matches:
        logger.warning("No no-DOI refs found.  Nothing to do.")
        return 1

    md = format_markdown_report(matches, write_mode=args.write)
    js = format_json_sidecar(matches)

    out_dir = ws / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    today = _utc_today()
    md_path = out_dir / f"enrich_no_doi_{today}.md"
    json_path = out_dir / f"enrich_no_doi_{today}.json"
    md_path.write_text(md, encoding="utf-8")
    json_path.write_text(js, encoding="utf-8")

    tier_counts: dict[str, int] = {"high": 0, "med": 0, "low": 0, "no_match": 0}
    for m in matches:
        tier_counts[m.tier] = tier_counts.get(m.tier, 0) + 1

    print()
    print("Enrichment summary:")
    print(f"  no-DOI refs walked : {len(matches)}")
    print(f"  HIGH-confidence    : {tier_counts['high']}")
    print(f"  MED-confidence     : {tier_counts['med']}")
    print(f"  LOW-confidence     : {tier_counts['low']}")
    print(f"  no_match           : {tier_counts['no_match']}")

    if args.write and tier_counts["high"]:
        updated = apply_high_matches(matches, processes, tasks)
        _save_catalog(processes, tasks, p_path, t_path, workspace=ws)
        print()
        print(f"Stamped ids.doi on {updated} refs.")
        print(f"wrote: {p_path.name}")
        print(f"wrote: {t_path.name}")
    elif tier_counts["high"]:
        print()
        print("Dry-run: rerun with --write to stamp the HIGH matches.")

    print()
    print(f"Report   : {md_path}")
    print(f"JSON     : {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "DEFAULT_THRESHOLDS",
    "Match",
    "Score",
    "Thresholds",
    "apply_high_matches",
    "format_json_sidecar",
    "format_markdown_report",
    "iter_no_doi_refs",
    "main",
    "normalize_title",
    "parse_surnames",
    "pick_best",
    "run_enrich",
    "score_candidate",
    "search_openalex",
    "title_similarity",
    "year_delta",
]
