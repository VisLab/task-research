"""
triage_existing_refs.py — Sub-phase 2.3: triage every reference in
process_details.json and task_details.json against keep/drop/review rules.

Produces:
  - <output>  (review artifact Markdown, default: reference_triage_<date>.md)
  - stdout: one-screen summary

Does NOT modify process_details.json or task_details.json.
Makes ZERO network calls.

Usage:
    python triage_existing_refs.py \\
        --processes _inputs/process_details.json \\
        --tasks     _inputs/task_details.json \\
        --landmark  landmark_refs.json \\
        --output    reference_triage_2026-04-22.md

A rerun on the same day with the same inputs produces byte-identical output.
"""

import argparse
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from identity import build_pub_id
from triage_rules import (
    classify_venue,
    publisher_tier_from_doi,
    matches_test_manual,
    LANDMARK_IDS,
)

TODAY = date.today().isoformat()

# ---------------------------------------------------------------------------
# First-author extraction from the JSON `authors` field
# ---------------------------------------------------------------------------

def _first_author_family(authors_str: str | None) -> str | None:
    """Extract first-author family name from strings like
    'Rescorla, R. A., & Wagner, A. R.' or
    'SCHUPP, H. T., CUTHBERT, B. N., ...'"""
    if not authors_str:
        return None
    s = authors_str.split(",")[0].strip()
    s = s.rstrip(".,;:").strip()
    return s if s else None


def _family_lc(family: str | None) -> str:
    """Canonical lowercase form of a family name for secondary matching."""
    if not family:
        return ""
    import unicodedata
    nfkd = unicodedata.normalize("NFKD", family.lower())
    return re.sub(r"[^a-z]", "", "".join(c for c in nfkd
                                         if unicodedata.combining(c) == 0))


# ---------------------------------------------------------------------------
# Triage rule engine (rules applied in order; first match wins)
# ---------------------------------------------------------------------------

def triage_ref(
    owner_id: str,
    array_name: str,
    idx: int,
    ref: dict,
    landmark_set: set[tuple[str, str]],
    landmark_secondary: set[tuple[str, str, int]],
) -> dict:
    """Apply the rule chain and return a triage decision dict."""

    family = _first_author_family(ref.get("authors"))
    year = ref.get("year")
    title = ref.get("title")
    venue = ref.get("venue") or ref.get("journal") or ""
    venue_type = ref.get("venue_type")
    doi = ref.get("doi")
    confidence = ref.get("confidence", "none")
    citation_string = ref.get("citation_string", "")

    # Compute pub_id for this reference
    if family or title:
        try:
            pub_id = build_pub_id(family, year, title)
        except Exception:
            pub_id = None
    else:
        pub_id = None

    # --- Rule a: KEEP — landmark override (primary: pub_id match) ---
    if pub_id and (owner_id, pub_id) in landmark_set:
        return _decision("KEEP", "landmark_override", owner_id, array_name,
                         idx, ref, pub_id, citation_string, venue, year)

    # --- Rule a2: KEEP — landmark override (secondary: author+year match) ---
    # Used for landmark entries whose title was missing in the MD, which means
    # the landmark pub_id was computed from the author surname fallback and
    # does not match the pub_id computed from the JSON title.
    flc = _family_lc(family)
    if flc and year is not None and (owner_id, flc, year) in landmark_secondary:
        return _decision("KEEP", "landmark_override",
                         owner_id, array_name, idx, ref, pub_id,
                         citation_string, venue, year)

    # --- Rule b: DROP — test manual / handbook ---
    if matches_test_manual(ref):
        return _decision("DROP", "test_manual", owner_id, array_name,
                         idx, ref, pub_id, citation_string, venue, year)

    # --- Rule c: DROP — year < 1960, not a landmark ---
    if year is not None and year < 1960:
        return _decision("DROP", "pre_1960_non_landmark", owner_id, array_name,
                         idx, ref, pub_id, citation_string, venue, year)

    # --- Rule d: REVIEW — technical report ---
    if venue_type == "report":
        return _decision("REVIEW", "technical_report_needs_citation_check",
                         owner_id, array_name, idx, ref, pub_id,
                         citation_string, venue, year)

    # --- Rule e: KEEP — flagship or mainstream venue ---
    venue_tier = classify_venue(venue)
    if venue_tier in ("flagship", "mainstream"):
        return _decision("KEEP", f"venue_in_allowlist_{venue_tier}",
                         owner_id, array_name, idx, ref, pub_id,
                         citation_string, venue, year)

    # --- Rule f: KEEP — Tier A or B publisher ---
    pub_tier = publisher_tier_from_doi(doi)
    if pub_tier in ("A", "B"):
        return _decision("KEEP", f"publisher_tier_{pub_tier}",
                         owner_id, array_name, idx, ref, pub_id,
                         citation_string, venue, year)

    # --- Rule g: REVIEW — book chapter, not landmark ---
    if venue_type == "book_chapter":
        return _decision("REVIEW", "book_chapter_non_landmark",
                         owner_id, array_name, idx, ref, pub_id,
                         citation_string, venue, year)

    # --- Rule h: REVIEW — unresolved / unknown venue ---
    if confidence == "none" or venue_tier == "unknown":
        return _decision("REVIEW", "unknown_venue",
                         owner_id, array_name, idx, ref, pub_id,
                         citation_string, venue, year)

    # --- Rule i: default REVIEW ---
    return _decision("REVIEW", "default_needs_review",
                     owner_id, array_name, idx, ref, pub_id,
                     citation_string, venue, year)


def _decision(decision: str, reason: str, owner_id: str, array_name: str,
              idx: int, ref: dict, pub_id: str | None,
              citation_string: str, venue: str, year: int | None) -> dict:
    return {
        "decision": decision,
        "reason": reason,
        "owner_id": owner_id,
        "array_name": array_name,
        "idx": idx,
        "pub_id": pub_id,
        "citation": citation_string,
        "title": (ref.get("title") or "") if ref else "",
        "venue": venue,
        "year": year,
    }


# ---------------------------------------------------------------------------
# Helpers for iterating (owner_id, array_name, idx, ref) tuples
# ---------------------------------------------------------------------------

def iter_process_refs(processes: list[dict]):
    for proc in processes:
        owner_id = proc.get("process_id", "")
        for arr_name in ("fundamental_references", "recent_references"):
            for idx, ref in enumerate(proc.get(arr_name, [])):
                yield owner_id, arr_name, idx, ref


def iter_task_refs(tasks: list[dict]):
    for task in tasks:
        owner_id = task.get("hedtsk_id", "")
        for arr_name in ("key_references", "recent_references"):
            for idx, ref in enumerate(task.get(arr_name, [])):
                yield owner_id, arr_name, idx, ref


# ---------------------------------------------------------------------------
# Markdown table helpers
# ---------------------------------------------------------------------------

_MAX_CELL = 90


def _trunc(s: str, max_len: int = _MAX_CELL) -> str:
    if len(s) <= max_len:
        return s
    year_m = re.search(r"\d{4}", s)
    year_str = f" [{year_m.group()}]" if year_m else ""
    cutoff = max_len - len(year_str) - 1
    return s[:cutoff].rstrip() + "\u2026" + year_str


def _row(*cells: str) -> str:
    return "| " + " | ".join(cells) + " |"


# ---------------------------------------------------------------------------
# Build the review Markdown
# ------------------
def build_triage_md(
    rows: list[dict],
    landmark_entries: list[dict],
    process_count: int,
    task_count: int,
    today: str,
) -> str:
    rows = sorted(rows, key=lambda r: (r["owner_id"], r["array_name"], r["idx"]))

    drops   = [r for r in rows if r["decision"] == "DROP"]
    reviews = [r for r in rows if r["decision"] == "REVIEW"]
    keeps   = [r for r in rows if r["decision"] == "KEEP"]

    n_total  = len(rows)
    n_keep   = len(keeps)
    n_drop   = len(drops)
    n_review = len(reviews)

    lines = []
    lines.append(f"# Reference triage \u2014 {today}")
    lines.append("")
    lines.append(f"Source: process_details.json, task_details.json (snapshot of {today}).")
    lines.append("Landmark override list: outputs/literature_search/landmark_refs.json")
    lines.append(f"({len(landmark_entries)} entries).")
    lines.append("")
    lines.append(f"Total references: {n_total}")
    lines.append(f"  KEEP:   {n_keep}")
    lines.append(f"  DROP:   {n_drop}")
    lines.append(f"  REVIEW: {n_review}")
    lines.append("")

    intro = """**What this file is:** Every reference currently attached to a HED process or task has been sorted by rule into one of three buckets. Your job is to check the two smaller buckets (Sections 1 and 2) and add your sign-off before anything is changed.

| Bucket | Count | What to do |
|--------|-------|------------|
| **KEEP** | {n_keep} | Nothing needed. Listed in Section 3 for audit only. |
| **DROP (proposed)** | {n_drop} | Scan Section 1. Write `KEEP` in the status column for any row you want to retain. |
| **REVIEW** | {n_review} | Work through Section 2. Replace `DECIDE` with `KEEP` or `DROP` for every row. |

**Nothing in the JSON data files has been changed yet.** All edits wait until you sign off.

---

## Column guide

| Column | Meaning |
|--------|---------|
| **HED concept** | The process or task this reference belongs to. IDs starting with `hed_` are processes (e.g. `hed_interference_control`); IDs starting with `hedtsk_` are tasks (e.g. `hedtsk_stroop_color_word`). |
| **ref list** | Which list the reference lives in: `fundamental_references` = foundational papers; `recent_references` = supporting/recent papers; `key_references` = primary task references. |
| **title** | The full article title from the database. |
| **citation** | The formatted citation string (may be truncated). |
| **venue** | Journal or book name. |
| **year** | Publication year. |
| **reason** | Why this row is in this section — see codes below. |
| **pos** | Position index within the reference list (0 = first). Used by the follow-up script to identify which entry to act on; you can ignore it. |

**Reason codes:**

| Code | Meaning |
|------|---------|
| `landmark_override` | Designated landmark for this concept — always kept regardless of other rules. |
| `venue_in_allowlist_flagship` | Published in a top-tier journal (Nature, Neuron, Psychological Review, PNAS, etc.). |
| `venue_in_allowlist_mainstream` | Published in a solid mainstream journal (Psychophysiology, Neuropsychologia, Brain and Cognition, etc.). |
| `publisher_tier_A` | DOI prefix is a Tier-A publisher (Elsevier, Springer, APA, Oxford UP, etc.) and venue was not in the named allowlist. |
| `publisher_tier_B` | DOI prefix is a Tier-B publisher (PLOS, Frontiers, Psychonomic Society, etc.). |
| `test_manual` | Citation or title contains "manual", "handbook", WAIS, IAPS, etc. — almost certainly a test kit or edited-volume entry, not a primary research article. |
| `pre_1960_non_landmark` | Published before 1960 and not a designated landmark for this concept. |
| `book_chapter_non_landmark` | Identified as a book chapter and not a designated landmark. |
| `unknown_venue` | Venue not in the allowlist and publisher could not be identified from the DOI. |
| `default_needs_review` | Did not match any automatic keep or drop rule. |
| `technical_report_needs_citation_check` | Appears to be a technical report — verify the citation is complete. |

---

## How to edit

**Section 1 — Proposed drops:** The `status` column shows `DROP`. If you want to *keep* a row instead, change `DROP` to `KEEP`.

**Section 2 — Items for review:** The `status` column shows `DECIDE`. Replace `DECIDE` with `KEEP` or `DROP` for every row.

**Section 3 — Confirmed keeps:** Read-only audit. Scan if you like; edit only if a reason looks wrong.
"""
    lines.append(intro.format(n_keep=n_keep, n_drop=n_drop, n_review=n_review))

    # --- Section 1: Proposed drops ---
    lines.append("## 1. Proposed drops")
    lines.append("")
    lines.append("The script proposes dropping these references. The `status` column says `DROP`.")
    lines.append("If you disagree, change `DROP` to `KEEP` in that cell.")
    lines.append("")
    lines.append(_row("#", "HED concept", "ref list", "title", "citation", "venue", "year", "reason", "status", "pos"))
    lines.append(_row("---","---","---","---","---","---","---","---","---","---"))
    for n, r in enumerate(drops, 1):
        lines.append(_row(
            str(n),
            r["owner_id"],
            r["array_name"],
            _trunc(r.get("title") or "", 80),
            _trunc(r["citation"] or r.get("pub_id") or "(no citation)"),
            _trunc(r["venue"] or "(none)", 45),
            str(r["year"] or ""),
            r["reason"],
            "DROP",
            str(r["idx"]),
        ))
    lines.append("")

    # --- Section 2: Items flagged for review ---
    lines.append("## 2. Items flagged for review")
    lines.append("")
    lines.append("Replace `DECIDE` in the `status` column with `KEEP` or `DROP` for each row.")
    lines.append("")
    lines.append(_row("#", "HED concept", "ref list", "title", "citation", "venue", "year", "reason", "status", "pos"))
    lines.append(_row("---","---","---","---","---","---","---","---","---","---"))
    for n, r in enumerate(reviews, 1):
        lines.append(_row(
            str(n),
            r["owner_id"],
            r["array_name"],
            _trunc(r.get("title") or "", 80),
            _trunc(r["citation"] or r.get("pub_id") or "(no citation)"),
            _trunc(r["venue"] or "(none)", 45),
            str(r["year"] or ""),
            r["reason"],
            "DECIDE",
            str(r["idx"]),
        ))
    lines.append("")

    # --- Section 3: Confirmed keeps ---
    lines.append("## 3. Confirmed keeps (for audit)")
    lines.append("")
    lines.append(_row("#", "HED concept", "ref list", "title", "citation", "venue", "year", "reason"))
    lines.append(_row("---","---","---","---","---","---","---","---"))
    for n, r in enumerate(keeps, 1):
        lines.append(_row(
            str(n),
            r["owner_id"],
            r["array_name"],
            _trunc(r.get("title") or "", 80),
            _trunc(r["citation"] or r.get("pub_id") or "(no citation)"),
            _trunc(r["venue"] or "(none)", 45),
            str(r["year"] or ""),
            r["reason"],
        ))
    lines.append("")

    return "\n".join(lines)



def build_gap_section(
    landmark_entries: list[dict],
    all_pub_ids_by_owner: dict[str, set[str]],
    landmark_secondary: set[tuple[str, str, int]],
) -> str:
    """Section 4: landmark papers not appearing in the current JSON data."""
    gaps = []
    for e in landmark_entries:
        oid = e.get("id", "")
        pid = e.get("pub_id")
        family_lc = _family_lc(e.get("first_author_family", ""))
        yr = e.get("year")
        owner_pids = all_pub_ids_by_owner.get(oid, set())
        # Primary match: pub_id in owner's reference set
        primary_hit = pid and pid in owner_pids
        # Secondary match: (owner_id, author_lc, year) matched in secondary set
        secondary_hit = (oid, family_lc, yr) in landmark_secondary and \
                        any(True for (o, a, y) in landmark_secondary
                            if o == oid and a == family_lc and y == yr)
        if not primary_hit and not secondary_hit:
            gaps.append(e)

    lines = []
    lines.append("## 4. Landmark gaps")
    lines.append("")
    lines.append(
        "Landmark papers from landmark_refs.json whose pub_id does not appear "
        "anywhere in the current process_details.json / task_details.json. "
        "These are slots Phase 3 will need to fill with the systematic search."
    )
    lines.append("")
    lines.append(_row("owner_id", "kind", "landmark citation", "pub_id"))
    lines.append(_row("---", "---", "---", "---"))
    for e in sorted(gaps, key=lambda x: (x["id"], x.get("citation", ""))):
        lines.append(_row(
            e["id"], e["kind"],
            _trunc(e.get("citation", ""), 60),
            e.get("pub_id") or "(unresolved)",
        ))
    lines.append("")
    lines.append(f"Total gaps: {len(gaps)} / {len(landmark_entries)} landmark entries")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="Triage existing references")
    ap.add_argument("--processes", default="_inputs/process_details.json")
    ap.add_argument("--tasks",     default="_inputs/task_details.json")
    ap.add_argument("--landmark",  default="landmark_refs.json")
    ap.add_argument("--output",    default=f"reference_triage_{TODAY}.md")
    args = ap.parse_args()

    script_dir = Path(__file__).parent

    def _resolve(p: str) -> Path:
        path = Path(p)
        return path if path.is_absolute() else script_dir / path

    proc_path = _resolve(args.processes)
    task_path = _resolve(args.tasks)
    lm_path   = _resolve(args.landmark)
    out_path  = _resolve(args.output)

    # --- Load data ---
    p_data    = json.loads(proc_path.read_text(encoding="utf-8"))
    processes = p_data.get("processes", [])

    t_data = json.loads(task_path.read_text(encoding="utf-8"))
    tasks  = t_data if isinstance(t_data, list) else t_data.get("tasks", [])

    lm_data          = json.loads(lm_path.read_text(encoding="utf-8"))
    landmark_entries = lm_data.get("entries", [])

    # --- Build landmark sets ---
    # Primary: (owner_id, pub_id) — works when title is known and matches
    landmark_set: set[tuple[str, str]] = set()
    # Secondary: (owner_id, author_family_lc, year) — fallback for
    # entries whose title was missing in the MD (pub_id computed from
    # author-surname fallback won't match the JSON's actual title)
    landmark_secondary: set[tuple[str, str, int]] = set()

    for e in landmark_entries:
        pid = e.get("pub_id")
        oid = e.get("id")
        if pid and oid:
            landmark_set.add((oid, pid))
        # Always populate secondary (author+year) to catch title mismatches
        family_lc = _family_lc(e.get("first_author_family", ""))
        yr        = e.get("year")
        if oid and family_lc and yr is not None:
            landmark_secondary.add((oid, family_lc, yr))

    LANDMARK_IDS.update(landmark_set)

    # --- Triage ---
    rows: list[dict] = []
    malformed: list[dict] = []

    for owner_id, arr_name, idx, ref in iter_process_refs(processes):
        family = _first_author_family(ref.get("authors"))
        title  = ref.get("title")
        if not family and not title:
            malformed.append({"owner_id": owner_id, "arr": arr_name,
                               "idx": idx, "ref": ref})
            continue
        row = triage_ref(owner_id, arr_name, idx, ref,
                         landmark_set, landmark_secondary)
        rows.append(row)

    for owner_id, arr_name, idx, ref in iter_task_refs(tasks):
        family = _first_author_family(ref.get("authors"))
        title  = ref.get("title")
        if not family and not title:
            malformed.append({"owner_id": owner_id, "arr": arr_name,
                               "idx": idx, "ref": ref})
            continue
        row = triage_ref(owner_id, arr_name, idx, ref,
                         landmark_set, landmark_secondary)
        rows.append(row)

    if malformed:
        print(f"\nWARNING: {len(malformed)} malformed references "
              f"(no authors AND no title):", file=sys.stderr)
        for m in malformed[:10]:
            print(f"  {m['owner_id']} {m['arr']}[{m['idx']}]", file=sys.stderr)

    # --- Build per-owner pub_id sets for gap check ---
    all_pub_ids_by_owner: dict[str, set[str]] = {}
    for r in rows:
        oid = r["owner_id"]
        pid = r.get("pub_id")
        if pid:
            all_pub_ids_by_owner.setdefault(oid, set()).add(pid)

    # --- Build Markdown ---
    md_body     = build_triage_md(rows, landmark_entries, len(processes),
                                  len(tasks), TODAY)
    gap_section = build_gap_section(landmark_entries, all_pub_ids_by_owner,
                                    landmark_secondary)
    full_md = md_body + gap_section

    out_path.write_text(full_md, encoding="utf-8")

    # --- Counters ---
    decision_reason = Counter((r["decision"], r["reason"]) for r in rows)

    landmark_keep_owners = {r["owner_id"] for r in rows
                            if r["decision"] == "KEEP"
                            and r["reason"] == "landmark_override"}
    landmark_owner_set = {e["id"] for e in landmark_entries}
    missing_coverage   = landmark_owner_set - landmark_keep_owners

    total_keep   = sum(v for (d,_),v in decision_reason.items() if d=="KEEP")
    total_drop   = sum(v for (d,_),v in decision_reason.items() if d=="DROP")
    total_review = sum(v for (d,_),v in decision_reason.items() if d=="REVIEW")

    print(f"\nPhase 2 triage \u2014 {TODAY}")
    print(f"processes scanned:   {len(processes)}")
    print(f"tasks scanned:       {len(tasks)}")
    print(f"references scanned:  {len(rows) + len(malformed)}")
    if malformed:
        print(f"  malformed (skipped): {len(malformed)}")
    print("decisions:")
    print(f"  KEEP  (landmark_override):             {decision_reason.get(('KEEP','landmark_override'),0)}")
    print(f"  KEEP  (venue flagship):                {decision_reason.get(('KEEP','venue_in_allowlist_flagship'),0)}")
    print(f"  KEEP  (venue mainstream):              {decision_reason.get(('KEEP','venue_in_allowlist_mainstream'),0)}")
    print(f"  KEEP  (publisher Tier A):              {decision_reason.get(('KEEP','publisher_tier_A'),0)}")
    print(f"  KEEP  (publisher Tier B):              {decision_reason.get(('KEEP','publisher_tier_B'),0)}")
    print(f"  KEEP  total:                           {total_keep}")
    print(f"  DROP  (test_manual):                   {decision_reason.get(('DROP','test_manual'),0)}")
    print(f"  DROP  (pre_1960_non_landmark):         {decision_reason.get(('DROP','pre_1960_non_landmark'),0)}")
    print(f"  DROP  total:                           {total_drop}")
    print(f"  REVIEW (report):                       {decision_reason.get(('REVIEW','technical_report_needs_citation_check'),0)}")
    print(f"  REVIEW (book_chapter):                 {decision_reason.get(('REVIEW','book_chapter_non_landmark'),0)}")
    print(f"  REVIEW (unknown_venue):                {decision_reason.get(('REVIEW','unknown_venue'),0)}")
    print(f"  REVIEW (default):                      {decision_reason.get(('REVIEW','default_needs_review'),0)}")
    print(f"  REVIEW total:                          {total_review}")
    print(f"landmark coverage: {len(landmark_keep_owners)} / {len(landmark_owner_set)} "
          f"owner_ids have >= 1 KEEP(landmark)")
    if missing_coverage:
        sample = sorted(missing_coverage)[:8]
        print(f"  (owners with no landmark match in data — {len(missing_coverage)} total): "
              + ", ".join(sample)
              + (" ..." if len(missing_coverage) > 8 else ""))
    rev_default = decision_reason.get(("REVIEW", "default_needs_review"), 0)
    if rev_default > 100:
        print(f"\nFLAG: {rev_default} in default_needs_review (>100); "
              "consider a new rule.", file=sys.stderr)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
