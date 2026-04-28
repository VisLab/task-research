#!/usr/bin/env python3
"""
extract_process_details_from_md.py

Phase 2 of the JSON-as-source-of-truth migration. Plan:
    ../.status/json_as_source_of_truth_plan_2026-04-17.md

Reads (authoritative as of the pre-flip state):
    ../process_reference.md     per-process definitions + citations + category grouping
    ../process_categories.md    per-category scope / out-of-scope / issues / history
    ../process_details.json     existing DERIVED file -- used for tasks[] reverse index
                                (OPTIONAL: skipped if missing or unparseable; tasks[]
                                 then emits empty, populated later by the Phase 4 sync
                                 script sync_process_details_tasks.py)

Writes:
    ../process_details.enriched.json    new enriched JSON (for review, not yet authoritative)
    ./phase2_extraction_report.md       report of what was parsed and what still needs work

This is a ONE-SHOT extraction. After Phase 3 (authority flip), process_details.json
becomes the authoritative hand-edited file; tasks[] / task_count stays derived via a
separate sync script, and forward generators emit the current markdown views.

Notes on citation extraction:
    The current house style in process_reference.md omits paper titles. Every extracted
    reference therefore has title = "". The `citation_string` field is populated with the
    source MD fragment verbatim. The subsequent literature pass (separate phase) will
    upgrade citations to Option B (APA-like full form) and fill in titles.

    Heuristic flags in the report identify references whose italicized run is likely a
    book title rather than a journal name (no `volume:pages` suffix after the italic).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent.resolve()
REPO_ROOT = SCRIPT_DIR.parent
PROCESS_REFERENCE = REPO_ROOT / "process_reference.md"
PROCESS_CATEGORIES = REPO_ROOT / "process_categories.md"
EXISTING_DETAILS = REPO_ROOT / "process_details.json"
OUT_JSON = REPO_ROOT / "process_details.enriched.json"
OUT_REPORT = SCRIPT_DIR / "phase2_extraction_report.md"


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class Reference:
    title: str
    journal: str
    year: Optional[int]
    citation_string: str


@dataclass
class ProcessEntry:
    process_id: str
    process_name: str
    category_id: str
    definition: str = ""
    fundamental_references: list = field(default_factory=list)
    recent_references: list = field(default_factory=list)
    notes: str = ""
    tasks: list = field(default_factory=list)
    task_count: int = 0


@dataclass
class CategoryEntry:
    category_id: str
    name: str
    scope: str = ""
    out_of_scope: str = ""
    issues: str = ""
    history: str = ""
    process_count: int = 0


# ---------------------------------------------------------------------------
# Slug
# ---------------------------------------------------------------------------

def slugify(name: str) -> str:
    """
    "Short-Term and Working Memory"  ->  "short_term_and_working_memory"
    "Perceptual Decision-Making (Evidence Accumulation)"
        ->  "perceptual_decision_making_evidence_accumulation"
    """
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


# ---------------------------------------------------------------------------
# Citation parsing
# ---------------------------------------------------------------------------

ITALIC_RE = re.compile(r"\*([^*]+)\*")
YEAR_RE = re.compile(r"\((\d{4})(?:[/-]\d{4})?\)")


def split_citations(line: str) -> list:
    """Split a citation paragraph by ';'. Returns stripped non-empty parts."""
    return [p.strip() for p in line.split(";") if p.strip()]


def parse_one_citation(raw: str) -> Reference:
    """
    Extract title / journal / year / citation_string from a single reference.

    title is always empty in Phase 2 (titles are absent from the source MD's
    compact house style; the literature pass fills them in). journal is the
    first italicized run, which is usually the journal but may be a book title
    when the reference is to a book or book chapter -- flagged in the report.
    """
    citation = raw.strip()
    # Strip trailing period only if it terminates the sentence cleanly
    if citation.endswith(".") and not citation.endswith("..."):
        citation = citation[:-1]
    year: Optional[int] = None
    m = YEAR_RE.search(citation)
    if m:
        year = int(m.group(1))
    journal = ""
    m = ITALIC_RE.search(citation)
    if m:
        journal = m.group(1).strip()
    return Reference(
        title="",
        journal=journal,
        year=year,
        citation_string=citation,
    )


def parse_citation_paragraph(line: str) -> list:
    return [parse_one_citation(s) for s in split_citations(line)]


# ---------------------------------------------------------------------------
# process_reference.md parser
# ---------------------------------------------------------------------------

HEAD2_RE = re.compile(r"^## (.+?)\s*$")
HEAD3_RE = re.compile(r"^### (.+?)\s+`([a-z0-9_]+)`(?:\s+(.*?))?\s*$")
DEFINITION_RE = re.compile(r"^\*\*Definition\.\*\*\s*(.*)$")
FUNDAMENTAL_RE = re.compile(r"^\*\*Fundamental\.\*\*\s*(.*)$")
RECENT_RE = re.compile(r"^\*\*Recent\.\*\*\s*(.*)$")
ITALIC_LINE_RE = re.compile(r"^_(.+)_\s*$")
PROCESSES_BLURB_RE = re.compile(r"^\d+\s+processes\.$")


def _header_trailer_to_note(trailer: str) -> str:
    """Convert e.g. '_(new 2026-04-15)_' to '(new 2026-04-15)'."""
    t = trailer.strip()
    if t.startswith("_") and t.endswith("_"):
        t = t[1:-1].strip()
    return t


def _italic_line_to_note(text: str) -> str:
    return text.strip()


def parse_process_reference(path: Path):
    """Return (categories_in_order: list[str], processes: list[ProcessEntry])."""
    categories_in_order: list = []
    processes: list = []
    current_category: Optional[str] = None
    current: Optional[ProcessEntry] = None

    def flush():
        nonlocal current
        if current is not None:
            processes.append(current)
            current = None

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()

        m = HEAD2_RE.match(line)
        if m:
            flush()
            current_category = m.group(1).strip()
            categories_in_order.append(current_category)
            continue

        m = HEAD3_RE.match(line)
        if m:
            flush()
            process_name = m.group(1).strip()
            process_id = m.group(2).strip()
            trailer = (m.group(3) or "").strip()
            notes = _header_trailer_to_note(trailer) if trailer else ""
            category_id = slugify(current_category) if current_category else ""
            current = ProcessEntry(
                process_id=process_id,
                process_name=process_name,
                category_id=category_id,
                notes=notes,
            )
            continue

        if current is None:
            continue

        m = DEFINITION_RE.match(line)
        if m:
            current.definition = m.group(1).strip()
            continue

        m = FUNDAMENTAL_RE.match(line)
        if m:
            current.fundamental_references = parse_citation_paragraph(m.group(1).strip())
            continue

        m = RECENT_RE.match(line)
        if m:
            current.recent_references = parse_citation_paragraph(m.group(1).strip())
            continue

        # Italic-only line: either the per-category "_N processes._" blurb
        # (skip) or an editorial trailer for the current process (append to
        # notes).
        m = ITALIC_LINE_RE.match(line)
        if m:
            text = m.group(1).strip()
            if PROCESSES_BLURB_RE.match(text):
                continue
            new_note = _italic_line_to_note(text)
            if current.notes and new_note:
                current.notes = f"{current.notes} {new_note}".strip()
            else:
                current.notes = new_note
            continue

    flush()
    return categories_in_order, processes


# ---------------------------------------------------------------------------
# process_categories.md parser
# ---------------------------------------------------------------------------

CATEGORY_HEAD_RE = re.compile(r"^## (.+?)(?:\s+\((\d+)\))?\s*$")
CATEGORY_FIELD_RE = re.compile(
    r"^\*\*(Scope|Out of scope|Issues|History)\.\*\*\s*(.*)$"
)
FIELD_MAP = {
    "Scope": "scope",
    "Out of scope": "out_of_scope",
    "Issues": "issues",
    "History": "history",
}


def parse_process_categories(path: Path) -> list:
    entries: list = []
    current: Optional[CategoryEntry] = None

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()

        m = CATEGORY_HEAD_RE.match(line)
        if m:
            name = m.group(1).strip()
            # Stop when we hit the terminal "Cross-cutting issues" section
            if name.lower().startswith("cross-cutting"):
                if current is not None:
                    entries.append(current)
                    current = None
                break
            if current is not None:
                entries.append(current)
            count_str = m.group(2)
            current = CategoryEntry(
                category_id=slugify(name),
                name=name,
                process_count=int(count_str) if count_str else 0,
            )
            continue

        if current is None:
            continue

        fm = CATEGORY_FIELD_RE.match(line)
        if fm:
            setattr(current, FIELD_MAP[fm.group(1)], fm.group(2).strip())

    if current is not None:
        entries.append(current)
    return entries


# ---------------------------------------------------------------------------
# Existing tasks[] loader
# ---------------------------------------------------------------------------

def load_existing_tasks(path: Path) -> dict:
    """
    Load the per-process tasks[] reverse index from the existing derived
    process_details.json. Returns an empty dict (and prints a notice) if the
    file is missing or cannot be parsed -- in that case, the enriched JSON is
    emitted with empty tasks[] on every process, and the Phase 4 sync script
    (sync_process_details_tasks.py) is expected to fill them in from the
    authoritative task_details.json later.
    """
    if not path.exists():
        print(f"NOTE: {path} not found -- emitting empty tasks[] fields. "
              f"Populate via sync_process_details_tasks.py (Phase 4).")
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"NOTE: {path} could not be parsed ({e}). "
              f"Emitting empty tasks[] fields; populate via "
              f"sync_process_details_tasks.py (Phase 4).")
        return {}
    out = {}
    for p in data.get("processes", []):
        out[p["process_id"]] = {
            "tasks": p.get("tasks", []),
            "task_count": p.get("task_count", 0),
        }
    return out


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------

def ref_to_dict(r: Reference) -> dict:
    return {
        "title": r.title,
        "journal": r.journal,
        "year": r.year,
        "citation_string": r.citation_string,
    }


def proc_to_dict(p: ProcessEntry) -> dict:
    d = {
        "process_id": p.process_id,
        "process_name": p.process_name,
        "category_id": p.category_id,
        "definition": p.definition,
        "fundamental_references": [ref_to_dict(r) for r in p.fundamental_references],
        "recent_references": [ref_to_dict(r) for r in p.recent_references],
    }
    if p.notes:
        d["notes"] = p.notes
    d["tasks"] = p.tasks
    d["task_count"] = p.task_count
    return d


def cat_to_dict(c: CategoryEntry) -> dict:
    d = {
        "category_id": c.category_id,
        "name": c.name,
        "scope": c.scope,
    }
    if c.out_of_scope:
        d["out_of_scope"] = c.out_of_scope
    if c.issues:
        d["issues"] = c.issues
    if c.history:
        d["history"] = c.history
    d["process_count"] = c.process_count
    return d


def build_enriched_json(
    categories: list,
    processes: list,
) -> dict:
    total_processes_used = sum(1 for p in processes if p.task_count > 0)
    # Unique tasks referenced (a task may link to multiple processes)
    unique_tasks = set()
    for p in processes:
        for t in p.tasks:
            unique_tasks.add(t.get("hedtsk_id"))
    return {
        "description": (
            "Enriched process catalog. AUTHORITATIVE for per-process definitions, "
            "citations, category placement, and editorial notes, and for per-category "
            "scope / out-of-scope / issues / history. The `tasks[]` and `task_count` "
            "fields inside each process are derived from task_details.json by a separate "
            "sync script (sync_process_details_tasks.py) and should not be hand-edited."
        ),
        "generated_on": date.today().isoformat(),
        "source_script": "outputs/extract_process_details_from_md.py",
        "schema_version": "2026-04-18",
        "total_categories": len(categories),
        "total_processes": len(processes),
        "total_processes_used_by_tasks": total_processes_used,
        "total_tasks": len(unique_tasks),
        "categories": [cat_to_dict(c) for c in categories],
        "processes": [proc_to_dict(p) for p in processes],
    }


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

# Flags a citation where the italicized run has no volume/pages/issue suffix
# immediately after, suggesting it is a book title rather than a journal.
VOL_PAGES_RE = re.compile(r"\s*(?:\d+\s*\(\d+\))?\s*\d+\s*[:,]\s*\d")


def is_probably_book(citation: str) -> bool:
    m = ITALIC_RE.search(citation)
    if not m:
        return False
    tail = citation[m.end():]
    # A journal citation usually has a volume:page pattern after the italic,
    # optionally prefixed by an issue number in parens. If none, assume book.
    return not VOL_PAGES_RE.match(tail)


def build_report(
    enriched: dict,
    categories: list,
    processes: list,
) -> str:
    lines = []
    lines.append("# Phase 2 extraction report")
    lines.append("")
    lines.append(f"**Date:** {date.today().isoformat()}")
    lines.append(
        "**Script:** `outputs/extract_process_details_from_md.py`"
    )
    lines.append(
        "**Output JSON:** `process_details.enriched.json` (at repo root — for review)"
    )
    lines.append("")

    lines.append("## Counts")
    lines.append("")
    lines.append(f"- Categories: {enriched['total_categories']}")
    lines.append(f"- Processes: {enriched['total_processes']}")
    lines.append(
        f"- Processes linked to at least one task: "
        f"{enriched['total_processes_used_by_tasks']}"
    )
    lines.append(f"- Unique tasks referenced: {enriched['total_tasks']}")
    lines.append("")

    lines.append("## Process-to-category distribution")
    lines.append("")
    cat_counts: dict = {}
    for p in processes:
        cat_counts[p.category_id] = cat_counts.get(p.category_id, 0) + 1
    for c in categories:
        md_count = c.process_count
        derived = cat_counts.get(c.category_id, 0)
        mismatch = "" if md_count == derived else f" — MISMATCH (MD: {md_count})"
        lines.append(
            f"- **{c.name}** (`{c.category_id}`): {derived}{mismatch}"
        )
    lines.append("")

    # Reference counts
    total_refs = 0
    for p in processes:
        total_refs += len(p.fundamental_references) + len(p.recent_references)

    lines.append("## References — summary")
    lines.append("")
    lines.append(f"- Total references extracted: {total_refs}")
    lines.append(
        f"- References with empty `title`: {total_refs} — every one, as expected "
        f"(source MD's compact house style omits titles). Literature pass will fill."
    )
    lines.append("")

    # Book-like flagged references
    lines.append(
        "## References where italicized run is likely a book (not journal)"
    )
    lines.append("")
    lines.append(
        "Heuristic: no `volume:pages` pattern follows the italicized run. These will "
        "need manual review during the literature pass — the `journal` field may hold "
        "a book title that belongs in `title`."
    )
    lines.append("")

    flagged = []
    for p in processes:
        for bucket_name, refs in (
            ("fundamental", p.fundamental_references),
            ("recent", p.recent_references),
        ):
            for r in refs:
                if is_probably_book(r.citation_string):
                    flagged.append((p.process_id, bucket_name, r.citation_string))
    lines.append(f"**Total flagged:** {len(flagged)}")
    lines.append("")
    for process_id, bucket, cs in flagged[:40]:
        lines.append(f"- `{process_id}` ({bucket}): {cs}")
    if len(flagged) > 40:
        lines.append(f"- ... and {len(flagged) - 40} more (see JSON).")
    lines.append("")

    # Notes field
    lines.append("## Processes with non-empty `notes`")
    lines.append("")
    with_notes = [p for p in processes if p.notes]
    lines.append(f"**Total:** {len(with_notes)}")
    lines.append("")
    for p in with_notes:
        lines.append(f"- `{p.process_id}`: {p.notes}")
    lines.append("")

    # Processes without tasks
    no_tasks = [p for p in processes if p.task_count == 0]
    lines.append("## Processes with no linked tasks (pre-provisioned rows)")
    lines.append("")
    lines.append(
        f"**Total:** {len(no_tasks)} "
        f"(catalog documentation expects ~22 pre-provisioned rows)."
    )
    lines.append("")
    for p in no_tasks:
        lines.append(f"- `{p.process_id}` ({p.process_name})")
    lines.append("")

    # Spot-check definitions
    lines.append("## Spot checks")
    lines.append("")
    lines.append(
        "Run `diff <(python3 -c 'import json; d=json.load(open(\"process_details.enriched.json\")); "
        "print(next(p[\"definition\"] for p in d[\"processes\"] if p[\"process_id\"]==\"hed_working_memory_updating\"))') "
        "<(grep -A 1 '^### Working memory updating' process_reference.md | tail -1 | "
        "sed -E 's/\\*\\*Definition\\.\\*\\* //')` "
        "to confirm no definition drift."
    )
    lines.append("")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    categories_in_order, processes = parse_process_reference(PROCESS_REFERENCE)
    categories = parse_process_categories(PROCESS_CATEGORIES)
    existing_tasks = load_existing_tasks(EXISTING_DETAILS)

    # Attach tasks[] / task_count from the existing derived JSON
    for p in processes:
        info = existing_tasks.get(p.process_id)
        if info:
            p.tasks = info["tasks"]
            p.task_count = info["task_count"]

    # Sanity: ordering of category names must match between the two MD sources
    ref_cats = categories_in_order
    cat_names = [c.name for c in categories]
    if ref_cats != cat_names:
        print("WARNING: category ordering differs between process_reference.md "
              "and process_categories.md")
        print("  process_reference.md order:", ref_cats)
        print("  process_categories.md order:", cat_names)

    # Fix per-category process_count to match the derived number
    cat_counts: dict = {}
    for p in processes:
        cat_counts[p.category_id] = cat_counts.get(p.category_id, 0) + 1
    for c in categories:
        c.process_count = cat_counts.get(c.category_id, 0)

    enriched = build_enriched_json(categories, processes)

    OUT_JSON.write_text(
        json.dumps(enriched, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    report = build_report(enriched, categories, processes)
    OUT_REPORT.write_text(report, encoding="utf-8")

    # Terse stdout summary
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_REPORT}")
    print(
        f"Categories: {enriched['total_categories']} | "
        f"Processes: {enriched['total_processes']} | "
        f"Used by tasks: {enriched['total_processes_used_by_tasks']} | "
        f"Unique tasks: {enriched['total_tasks']}"
    )


if __name__ == "__main__":
    main()
