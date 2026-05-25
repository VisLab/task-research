#!/usr/bin/env python3
"""
record_artifact.py — Manual artifact recording for the HED catalog.

When you've downloaded a PDF (or built a Markdown) by hand — typically
through your university library or a manual download — this script
copies the file into the canonical location and records its
provenance in the catalog.

Two subcommands:

    record_artifact.py pdf       — record a PDF acquisition
    record_artifact.py markdown  — record a Markdown acquisition

Each subcommand requires:

    --file <path>          source file on your disk
    --license <spdx>       SPDX-style licence string (see
                           license_policy.normalise_license).
                           Required so the publishability flag can
                           be computed; pass "proprietary" for
                           publisher PDFs from a TDM/library route,
                           "cc-by" / "cc-by-nc-nd" / etc. for OA.

And one identifier (used to locate which catalog reference(s) to
update):

    --doi <doi>            DOI of the publication (most common)
    --pub-id <pub_id>      content-addressed publication ID
    --pmid <pmid>          PubMed ID

Optional:

    --source-url <url>     where the file came from (kept verbatim)
    --source-type <name>   short tag identifying the route.  Defaults:
                             pdf → "manual_library"
                             markdown → "manual_conversion"
    --converter <name>     for markdown only: pmc_bioc / markitdown /
                           mistral / manual.  Defaults to "manual".
    --force                overwrite an existing local_artifacts entry
                           or destination file
    --workspace <path>     workspace root (Claude-research/).  Defaults
                           to the current directory.
    --dry-run              do everything except copy the file and write
                           the catalog back

The PDF goes to ``<repo-root>/HED-PDFs/`` (gitignored).  The Markdown
goes to ``<repo-root>/HED-Markdown-private/`` (gitignored).  The
canonical filename is computed via
``identity.build_pdf_filename(first_author_family, year, title)`` so
PDF and Markdown for the same paper share a stem.

Multi-reference updates: if the publication is referenced by more
than one process or task (common for landmark papers), every
matching reference is updated with the same ``local_artifacts``
block in a single run.

Example::

    # PDF you downloaded through your university library:
    python code/literature_search/record_artifact.py pdf \\
        --doi 10.1016/j.neuron.2015.09.028 \\
        --file ~/Downloads/Dunsmoor_Neuron_2015.pdf \\
        --source-url 'https://www.sciencedirect.com/science/article/pii/S0896627315008454' \\
        --source-type manual_library \\
        --license proprietary

    # Markdown you converted from an OA preprint:
    python code/literature_search/record_artifact.py markdown \\
        --doi 10.1016/j.neuron.2015.09.028 \\
        --file ~/Downloads/Dunsmoor_Neuron_2015.md \\
        --source-url 'https://www.biorxiv.org/content/10.1101/2015.09.XX.YYYYYYv1' \\
        --source-type manual_conversion \\
        --license cc-by-nc-nd

Exit codes:
    0 — success (or dry-run clean)
    1 — usage error / file not found / no matching reference / would-overwrite
    2 — internal error (catalog parse failure, etc.)
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import date
from pathlib import Path
from typing import Iterable

# Allow running both as "python code/literature_search/record_artifact.py"
# from the workspace root and as a module-style invocation.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from identity import build_pdf_filename  # noqa: E402
from license_policy import is_publishable, normalise_license  # noqa: E402
from reference_compat import ref_doi, ref_pmid, ref_pub_id  # noqa: E402


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def _resolve_workspace(arg: str) -> Path:
    """Workspace root (Claude-research/)."""
    return Path(arg).resolve()


def _repo_root(workspace: Path) -> Path:
    """Repository root — the parent of the workspace."""
    return workspace.parent


def _artifact_dir(repo_root: Path, kind: str) -> Path:
    if kind == "pdf":
        return repo_root / "HED-PDFs"
    if kind == "markdown":
        return repo_root / "HED-Markdown-private"
    raise ValueError(f"unknown artifact kind: {kind!r}")


def _artifact_suffix(kind: str) -> str:
    return {"pdf": ".pdf", "markdown": ".md"}[kind]


# ---------------------------------------------------------------------------
# Catalog I/O
# ---------------------------------------------------------------------------

def _load_catalog(workspace: Path) -> tuple[dict, list, Path, Path]:
    """Load both process_details.json and task_details.json."""
    p_path = workspace / "process_details.json"
    t_path = workspace / "task_details.json"
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
) -> None:
    """Atomic-ish write: stage to a sibling tmp file, then rename."""
    for data, path in ((processes, p_path), (tasks, t_path)):
        tmp = path.with_suffix(path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        tmp.replace(path)


# ---------------------------------------------------------------------------
# Reference lookup
# ---------------------------------------------------------------------------

def _iter_all_refs(
    processes: dict,
    tasks: list,
) -> Iterable[tuple[str, dict]]:
    """Yield ``(owner_id, reference)`` for every reference in the catalog."""
    for p in processes.get("processes", []):
        owner = p.get("process_id", "")
        for r in p.get("references") or []:
            yield owner, r
    for t in tasks:
        owner = t.get("hedtsk_id", "")
        for r in t.get("references") or []:
            yield owner, r


def _matches(
    ref: dict,
    *,
    doi: str | None = None,
    pub_id: str | None = None,
    pmid: str | None = None,
) -> bool:
    """True if the reference matches any of the provided identifiers."""
    if doi:
        rd = (ref_doi(ref) or "").lower().strip()
        if rd == doi.lower().strip():
            return True
    if pub_id:
        if ref_pub_id(ref) == pub_id:
            return True
    if pmid:
        if (ref_pmid(ref) or "").strip() == pmid.strip():
            return True
    return False


def _find_matching_refs(
    processes: dict,
    tasks: list,
    *,
    doi: str | None,
    pub_id: str | None,
    pmid: str | None,
) -> list[tuple[str, dict]]:
    """Return every (owner_id, reference) matching any identifier given."""
    return [
        (owner, r)
        for owner, r in _iter_all_refs(processes, tasks)
        if _matches(r, doi=doi, pub_id=pub_id, pmid=pmid)
    ]


# ---------------------------------------------------------------------------
# Canonical filename
# ---------------------------------------------------------------------------

def _canonical_stem(ref: dict) -> str:
    """Derive the canonical filename stem from a reference.

    Uses identity.build_pdf_filename and strips the trailing extension
    so the same stem can be used for both PDF and Markdown.
    """
    family = _first_author_family(ref.get("authors"))
    year   = ref.get("year")
    title  = ref.get("title")
    fname  = build_pdf_filename(family, year, title)
    # build_pdf_filename emits "<stem>.pdf"; drop the suffix.
    if fname.lower().endswith(".pdf"):
        fname = fname[:-4]
    return fname


def _first_author_family(authors_str: str | None) -> str | None:
    """Extract first-author family name from the catalog's ``authors`` string.

    Mirrors the helper in triage_existing_refs.py; kept local so this
    script is self-contained.
    """
    if not authors_str:
        return None
    s = authors_str.split(",")[0].strip().rstrip(".,;:").strip()
    return s or None


# ---------------------------------------------------------------------------
# local_artifacts construction
# ---------------------------------------------------------------------------

def _build_artifact_entry(
    *,
    kind: str,
    rel_path: str,
    source_url: str | None,
    source_type: str,
    license_raw: str,
    converter: str | None,
) -> dict:
    """Construct a local_artifact_entry dict for the catalog."""
    norm = normalise_license(license_raw)
    entry: dict = {
        "path":           rel_path,
        "source_url":     source_url,
        "source_type":    source_type,
        "license":        norm,
        "acquired_on":    date.today().isoformat(),
        "acquired_via":   "manual",
        "is_publishable": is_publishable(norm),
    }
    if kind == "markdown":
        entry["converter"] = converter or "manual"
    return entry


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="record_artifact",
        description="Record a manually-acquired PDF or Markdown against the HED catalog.",
    )
    sub = p.add_subparsers(dest="kind", required=True)

    def _add_common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--file", required=True,
                        help="Source file on your disk to be copied into the canonical location.")
        sp.add_argument("--license", required=True,
                        help="SPDX-style licence (cc-by, cc-by-nc-nd, proprietary, cc0, ...). "
                             "Use 'proprietary' for publisher PDFs obtained via library/TDM routes. "
                             "See license_policy.normalise_license.")
        sp.add_argument("--doi", help="DOI of the publication.")
        sp.add_argument("--pub-id", help="pub_id of the publication (if known).")
        sp.add_argument("--pmid", help="PubMed ID of the publication.")
        sp.add_argument("--source-url",
                        help="URL the file came from (kept verbatim for provenance).")
        sp.add_argument("--source-type", default=None,
                        help="Short tag identifying the acquisition route. "
                             "Defaults: pdf→manual_library, markdown→manual_conversion.")
        sp.add_argument("--workspace", default=".",
                        help="Workspace root (Claude-research/). Default: current directory.")
        sp.add_argument("--force", action="store_true",
                        help="Overwrite an existing local_artifacts entry or destination file.")
        sp.add_argument("--dry-run", action="store_true",
                        help="Do everything except copy the file and write the catalog back.")

    pdf = sub.add_parser("pdf", help="Record a PDF acquisition.")
    _add_common(pdf)

    md = sub.add_parser("markdown", help="Record a Markdown acquisition.")
    _add_common(md)
    md.add_argument("--converter", default=None,
                    help="Which converter produced the Markdown (pmc_bioc / markitdown / "
                         "mistral / manual). Default: manual.")
    return p


def _validate_identifiers(args: argparse.Namespace) -> None:
    if not (args.doi or args.pub_id or args.pmid):
        raise SystemExit(
            "ERROR: must supply at least one identifier "
            "(--doi, --pub-id, or --pmid)."
        )


def _default_source_type(kind: str) -> str:
    return {"pdf": "manual_library", "markdown": "manual_conversion"}[kind]


def main(argv: list[str] | None = None) -> int:
    args = _make_parser().parse_args(argv)
    kind = args.kind  # "pdf" or "markdown"

    _validate_identifiers(args)

    src = Path(args.file).expanduser()
    if not src.exists():
        print(f"ERROR: source file not found: {src}", file=sys.stderr)
        return 1
    if not src.is_file():
        print(f"ERROR: source is not a regular file: {src}", file=sys.stderr)
        return 1

    workspace = _resolve_workspace(args.workspace)
    repo_root = _repo_root(workspace)
    art_dir   = _artifact_dir(repo_root, kind)

    # Ensure target directory exists; mkdir is cheap and idempotent.
    art_dir.mkdir(parents=True, exist_ok=True)

    # ---- Load catalog
    try:
        processes, tasks, p_path, t_path = _load_catalog(workspace)
    except FileNotFoundError as e:
        print(f"ERROR: catalog file missing: {e}", file=sys.stderr)
        return 2

    # ---- Find matching references
    matches = _find_matching_refs(
        processes, tasks,
        doi=args.doi, pub_id=args.pub_id, pmid=args.pmid,
    )
    if not matches:
        print(
            "ERROR: no references match the supplied identifier(s). "
            f"doi={args.doi!r} pub_id={args.pub_id!r} pmid={args.pmid!r}",
            file=sys.stderr,
        )
        return 1

    # ---- Compute canonical filename from the first matching reference.
    # All matches refer to the same publication, so any reference works;
    # using the first one keeps the result deterministic.
    stem = _canonical_stem(matches[0][1])
    dest_path = art_dir / f"{stem}{_artifact_suffix(kind)}"
    rel_path  = f"{art_dir.name}/{dest_path.name}"

    # ---- Existence check: refuse to overwrite without --force.
    if dest_path.exists() and not args.force:
        print(
            f"ERROR: destination already exists: {dest_path}\n"
            "       Pass --force to overwrite, or delete the existing file first.",
            file=sys.stderr,
        )
        return 1

    # ---- Pre-existing artifact entry check.
    for owner, ref in matches:
        existing = (ref.get("local_artifacts") or {}).get(kind)
        if existing and not args.force:
            print(
                f"ERROR: {owner} reference already has a {kind} "
                f"artifact entry (path={existing.get('path')!r}).\n"
                "       Pass --force to overwrite.",
                file=sys.stderr,
            )
            return 1

    # ---- Build the entry once; apply to every match.
    source_type = args.source_type or _default_source_type(kind)
    entry = _build_artifact_entry(
        kind=kind,
        rel_path=rel_path,
        source_url=args.source_url,
        source_type=source_type,
        license_raw=args.license,
        converter=getattr(args, "converter", None),
    )

    # ---- Report what will happen
    print(f"Plan: record {kind} for {len(matches)} reference(s)")
    print(f"  identifier: doi={args.doi!r} pub_id={args.pub_id!r} pmid={args.pmid!r}")
    for owner, _ in matches:
        print(f"    - {owner}")
    print(f"  source:    {src}")
    print(f"  dest:      {dest_path}")
    print(f"  licence:   {args.license!r} -> normalised: {entry['license']!r}")
    print(f"  publishable: {entry['is_publishable']}")
    print(f"  source_type: {entry['source_type']!r}")
    if kind == "markdown":
        print(f"  converter:   {entry['converter']!r}")

    if args.dry_run:
        print("\ndry-run complete; no files copied, catalog unchanged.")
        return 0

    # ---- Copy the file.
    shutil.copy2(src, dest_path)
    print(f"\ncopied: {dest_path}")

    # ---- Update every matching reference.
    for _, ref in matches:
        ref.setdefault("local_artifacts", {})[kind] = entry

    # ---- Write catalog back.
    _save_catalog(processes, tasks, p_path, t_path)
    print(f"wrote: {p_path.name}")
    print(f"wrote: {t_path.name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
