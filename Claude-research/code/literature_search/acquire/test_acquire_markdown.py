"""
test_acquire_markdown.py — Unit + integration tests for acquire/acquire_markdown.py.

All tests inject fake ``lookup_fn`` / ``bioc_fn`` / ``convert_fn``
callables so neither the PMC BioC endpoint nor marker-pdf nor the
file system outside ``tmp_path`` is ever touched.  Catalog and
artifact writes go to ``tmp_path`` fixtures so no real
``HED-Markdown-{public,private}/`` directory is mutated.

Concentric layers, mirroring ``test_acquire_pdf.py``:

  TestLicenseForBioc        Pure helper: licence priority chain
                            (BioC infons -> pdf_locations pmc entry
                            -> "unknown").
  TestPmcLandingUrl         Pure helper: source_url composition.
  TestDryRunPlan            Pure helper: dry-run plan strings.
  TestAttemptOneRefDryRun   Wet/dry-run split: dry-run returns
                            would_walk without touching mocks.
  TestAttemptOneRefPmc      PMC fast path: BioC document -> Markdown
                            -> routed to public/private.
  TestAttemptOneRefPdf      PDF fallback: convert_pdf -> Markdown,
                            licence inherits.
  TestAttemptOneRefFailures Failure paths: tried lists, reason
                            composition, ImportError handling.
  TestAttemptOneRefBiocOnly --bioc-only semantics: skipped vs
                            failure for refs with/without pmcid.
  TestMainIntegration       End-to-end via main(): catalog round-trip,
                            idempotency, --force, --retry-failed,
                            --bioc-only, exit codes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable

import pytest

# Make ``acquire/`` and its parent (``literature_search/``) importable
# when pytest runs the file directly.  Matches the convention used by
# the other test files in this directory.
_HERE = Path(__file__).resolve().parent
_PARENT = _HERE.parent
for p in (_HERE, _PARENT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import acquire_markdown as M  # noqa: E402  module under test


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FAKE_MD_BIOC = "# Fake BioC Markdown\n\nA short rendered article.\n"
FAKE_MD_PDF  = "# Fake PDF-converted Markdown\n\nFrom marker-pdf.\n"


def _loc(url: str, *, source: str = "openalex",
         version: str = "publishedVersion", license: str = "cc-by",
         is_oa: bool = True) -> dict:
    """Build a synthetic ``pdf_locations[]`` entry."""
    return {"url": url, "source": source, "version": version,
            "license": license, "is_oa": is_oa}


def _ref(*locs: dict,
         doi: str = "10.x/test",
         pmcid: str | None = None,
         pdf_local: dict | None = None) -> dict:
    """Build a minimal ref with the catalog shape ``acquire_markdown`` reads.

    ``pdf_local`` populates ``local_artifacts.pdf`` when supplied —
    typically the output of a successful ``acquire_pdf.py`` run.
    """
    r: dict = {
        "authors": "Fleming, S. M., & Lau, H. C.",
        "year": 2014,
        "title": "How to measure metacognition",
        "ids": {"doi": doi, "pmcid": pmcid},
        "pdf_locations": list(locs),
    }
    if pdf_local is not None:
        r["local_artifacts"] = {"pdf": pdf_local}
    return r


def _bioc(*, license: str | None = "CC-BY",
          n_docs: int = 1,
          pmcid_annotation: str | None = "PMC4097944") -> dict:
    """Build a synthetic BioC collection dict.

    Mimics the shape returned by ``clients.pmc.lookup_by_pmcid``: a
    dict with ``documents`` plus the client-added ``_pmcid`` /
    ``_source`` annotations.  ``license=None`` produces a document
    whose ``infons`` carries no licence (so callers can exercise the
    fallback chain in ``_license_for_bioc``).
    """
    infons: dict = {"journal-title": "Frontiers in Human Neuroscience"}
    if license is not None:
        infons["license"] = license
    docs = [{"id": "test", "infons": infons,
             "passages": [{"infons": {"section_type": "TITLE",
                                       "type": "front"},
                           "text": "How to measure metacognition"}]}
            for _ in range(n_docs)]
    out: dict = {"documents": docs, "source": "PMC"}
    if pmcid_annotation is not None:
        out["_pmcid"]  = pmcid_annotation
        out["_source"] = "pmc_bioc"
    return out


def _queue(*items) -> "_Queue":
    """Mock callable that yields ``items`` in order; raises on overflow."""
    return _Queue(list(items))


class _Queue:
    def __init__(self, items: list):
        self.items = items
        self.calls: list[tuple] = []

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        if not self.items:
            raise AssertionError(
                f"mock called more times than queued (args={args!r})")
        item = self.items.pop(0)
        if isinstance(item, BaseException):
            raise item
        if callable(item):
            return item(*args, **kwargs)
        return item


def _empty_callable_must_not_run(*args, **kwargs):  # pragma: no cover - guard
    raise AssertionError(f"callable invoked unexpectedly: args={args!r}")


# ---------------------------------------------------------------------------
# _license_for_bioc
# ---------------------------------------------------------------------------

class TestLicenseForBioc:

    def test_uses_bioc_document_infons_first(self) -> None:
        bioc = _bioc(license="CC-BY 4.0")
        ref = _ref(_loc("https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4097944/",
                        source="pmc", license="cc-by-nc"))  # discovery says nc
        # BioC says cc-by; it wins.
        assert M._license_for_bioc(bioc, ref) == "cc-by"

    def test_falls_back_to_pmc_pdf_locations_entry(self) -> None:
        bioc = _bioc(license=None)  # no licence in BioC
        ref = _ref(
            _loc("https://example.com/random.pdf",
                 source="openalex", license="cc0"),  # not pmc-classified
            _loc("https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4097944/",
                 source="pmc", license="cc-by-sa"),
        )
        assert M._license_for_bioc(bioc, ref) == "cc-by-sa"

    def test_returns_unknown_when_neither_present(self) -> None:
        bioc = _bioc(license=None)
        ref = _ref(_loc("https://example.com/random.pdf",
                        source="openalex", license="cc0"))
        # No pmc-classified pdf_locations entry, no licence in BioC.
        assert M._license_for_bioc(bioc, ref) == "unknown"

    def test_normalises_raw_string(self) -> None:
        # "CC-BY-NC-ND 4.0" should normalise to canonical cc-by-nc-nd.
        bioc = _bioc(license="CC-BY-NC-ND 4.0")
        ref = _ref()
        assert M._license_for_bioc(bioc, ref) == "cc-by-nc-nd"

    def test_skips_empty_string_license_in_bioc(self) -> None:
        # An empty string isn't a real licence; fall through.
        bioc = _bioc(license="   ")
        ref = _ref(_loc("https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4097944/",
                        source="pmc", license="cc-by"))
        assert M._license_for_bioc(bioc, ref) == "cc-by"

    def test_no_documents_falls_back(self) -> None:
        bioc = {"documents": []}
        ref = _ref(_loc("https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4097944/",
                        source="pmc", license="cc-by"))
        assert M._license_for_bioc(bioc, ref) == "cc-by"


# ---------------------------------------------------------------------------
# _pmc_landing_url
# ---------------------------------------------------------------------------

class TestPmcLandingUrl:

    def test_uses_pmcid_annotation_when_present(self) -> None:
        bioc = {"_pmcid": "PMC4097944"}
        # Fallback would have been "PMC4097944" anyway, but verify
        # the annotation path is exercised.
        assert (M._pmc_landing_url(bioc, "pmc4097944")
                == "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4097944/")

    def test_falls_back_to_input_pmcid(self) -> None:
        bioc = {}
        assert (M._pmc_landing_url(bioc, "PMC4097944")
                == "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4097944/")

    def test_returns_empty_string_on_missing_input(self) -> None:
        assert M._pmc_landing_url({}, "") == ""
        assert M._pmc_landing_url({"_pmcid": "   "}, "") == ""


# ---------------------------------------------------------------------------
# _dry_run_plan
# ---------------------------------------------------------------------------

class TestDryRunPlan:

    def test_pmc_with_pdf_fallback(self) -> None:
        plan = M._dry_run_plan(has_pmcid=True, has_pdf=True, bioc_only=False)
        assert "pmc_bioc" in plan and "marker-pdf" in plan

    def test_pmc_only_no_pdf(self) -> None:
        plan = M._dry_run_plan(has_pmcid=True, has_pdf=False, bioc_only=False)
        assert "pmc_bioc" in plan and "marker-pdf" not in plan

    def test_pmc_bioc_only(self) -> None:
        plan = M._dry_run_plan(has_pmcid=True, has_pdf=True, bioc_only=True)
        assert "pmc_bioc" in plan and "marker-pdf" not in plan

    def test_no_pmcid_bioc_only_says_skip(self) -> None:
        plan = M._dry_run_plan(has_pmcid=False, has_pdf=True, bioc_only=True)
        assert "skip" in plan.lower()

    def test_no_pmcid_pdf_fallback_only(self) -> None:
        plan = M._dry_run_plan(has_pmcid=False, has_pdf=True, bioc_only=False)
        assert "marker-pdf" in plan and "pmc_bioc" not in plan

    def test_nothing_to_try(self) -> None:
        plan = M._dry_run_plan(has_pmcid=False, has_pdf=False, bioc_only=False)
        assert "failure" in plan.lower()


# ---------------------------------------------------------------------------
# attempt_one_ref dry-run
# ---------------------------------------------------------------------------

class TestAttemptOneRefDryRun:

    def test_dry_run_does_not_invoke_lookup_or_convert(self, tmp_path: Path) -> None:
        ref = _ref(pmcid="PMC4097944",
                   pdf_local={"path": "HED-PDFs/x.pdf"})
        result = M.attempt_one_ref(
            ref, repo_root=tmp_path, write=False, bioc_only=False,
            cache_dir=tmp_path / "cache",
            lookup_fn=_empty_callable_must_not_run,
            bioc_fn=_empty_callable_must_not_run,
            convert_fn=_empty_callable_must_not_run,
        )
        assert result.kind == "would_walk"
        assert "pmc_bioc" in result.plan

    def test_dry_run_no_pdf_no_pmcid_reports_failure_intention(self,
                                                                tmp_path: Path) -> None:
        ref = _ref()
        result = M.attempt_one_ref(
            ref, repo_root=tmp_path, write=False, bioc_only=False,
            cache_dir=tmp_path / "cache",
            lookup_fn=_empty_callable_must_not_run,
            bioc_fn=_empty_callable_must_not_run,
            convert_fn=_empty_callable_must_not_run,
        )
        assert result.kind == "would_walk"
        assert "failure" in result.plan.lower()


# ---------------------------------------------------------------------------
# attempt_one_ref — PMC happy path
# ---------------------------------------------------------------------------

class TestAttemptOneRefPmc:

    def test_pmc_success_writes_markdown_and_returns_success(self,
                                                              tmp_path: Path) -> None:
        ref = _ref(pmcid="PMC4097944")
        bioc = _bioc(license="CC-BY")

        result = M.attempt_one_ref(
            ref, repo_root=tmp_path, write=True, bioc_only=False,
            cache_dir=tmp_path / "cache",
            lookup_fn=_queue(bioc),
            bioc_fn=_queue(FAKE_MD_BIOC),
            convert_fn=_empty_callable_must_not_run,
        )

        assert result.kind == "success"
        assert result.converter == "pmc_bioc"
        assert result.source_type == "auto_pmc_bioc"
        assert result.license_norm == "cc-by"
        assert result.is_publishable_flag is True
        assert result.source_url == (
            "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4097944/")
        # Lands under HED-Markdown-public/ because cc-by is publishable.
        assert result.dest_path is not None
        assert result.dest_path.exists()
        assert result.dest_path.read_text(encoding="utf-8") == FAKE_MD_BIOC
        assert result.dest_path.parent == tmp_path / "HED-Markdown-public"
        # Filename mirrors the PDF canonical filename with .md.
        assert result.dest_path.name.startswith(
            "Fleming_2014_HowToMeasureMetacognition_")
        assert result.dest_path.name.endswith(".md")

    def test_pmc_unknown_license_lands_in_private(self, tmp_path: Path) -> None:
        # BioC has no licence; pdf_locations has none either.  Defaults
        # to "unknown" -> not publishable -> private.
        ref = _ref(pmcid="PMC4097944")
        bioc = _bioc(license=None)

        result = M.attempt_one_ref(
            ref, repo_root=tmp_path, write=True, bioc_only=False,
            cache_dir=tmp_path / "cache",
            lookup_fn=_queue(bioc),
            bioc_fn=_queue(FAKE_MD_BIOC),
            convert_fn=_empty_callable_must_not_run,
        )
        assert result.kind == "success"
        assert result.license_norm == "unknown"
        assert result.is_publishable_flag is False
        assert result.dest_path.parent == tmp_path / "HED-Markdown-private"

    def test_pmc_nc_license_lands_in_private(self, tmp_path: Path) -> None:
        # CC-BY-NC is NOT in PUBLISHABLE_LICENSES (decision 2026-05-19,
        # plan v2 §10 D8).
        ref = _ref(pmcid="PMC4097944")
        bioc = _bioc(license="CC-BY-NC")

        result = M.attempt_one_ref(
            ref, repo_root=tmp_path, write=True, bioc_only=False,
            cache_dir=tmp_path / "cache",
            lookup_fn=_queue(bioc),
            bioc_fn=_queue(FAKE_MD_BIOC),
            convert_fn=_empty_callable_must_not_run,
        )
        assert result.license_norm == "cc-by-nc"
        assert result.is_publishable_flag is False
        assert result.dest_path.parent == tmp_path / "HED-Markdown-private"

    def test_pmc_path_does_not_call_convert_fn(self, tmp_path: Path) -> None:
        # PMC success must short-circuit; the PDF fallback must not run
        # even if a PDF would otherwise be available.
        ref = _ref(
            pmcid="PMC4097944",
            pdf_local={"path": "HED-PDFs/x.pdf",
                       "license": "proprietary",
                       "source_url": "https://stale"},
        )
        bioc = _bioc(license="CC-BY")
        convert = _queue()  # empty: must not be called

        result = M.attempt_one_ref(
            ref, repo_root=tmp_path, write=True, bioc_only=False,
            cache_dir=tmp_path / "cache",
            lookup_fn=_queue(bioc),
            bioc_fn=_queue(FAKE_MD_BIOC),
            convert_fn=convert,
        )
        assert result.kind == "success"
        assert result.converter == "pmc_bioc"
        assert convert.calls == []


# ---------------------------------------------------------------------------
# attempt_one_ref — PDF fallback path
# ---------------------------------------------------------------------------

class TestAttemptOneRefPdf:

    def test_no_pmcid_with_pdf_runs_marker(self, tmp_path: Path) -> None:
        ref = _ref(pdf_local={
            "path":       "HED-PDFs/Foo.pdf",
            "source_url": "https://example.com/source.pdf",
            "license":    "cc-by",
        })
        # Make the PDF actually exist so convert_pdf wouldn't have raised
        # FileNotFoundError if it were called for real.  (The mock
        # doesn't care, but we keep the fixture realistic.)
        (tmp_path / "HED-PDFs").mkdir()
        (tmp_path / "HED-PDFs" / "Foo.pdf").write_bytes(b"%PDF-1.7\n")

        result = M.attempt_one_ref(
            ref, repo_root=tmp_path, write=True, bioc_only=False,
            cache_dir=tmp_path / "cache",
            lookup_fn=_empty_callable_must_not_run,
            bioc_fn=_empty_callable_must_not_run,
            convert_fn=_queue(FAKE_MD_PDF),
        )

        assert result.kind == "success"
        assert result.converter == "marker-pdf"
        assert result.source_type == "auto_markdown_from_pdf"
        assert result.license_norm == "cc-by"
        assert result.source_url == "https://example.com/source.pdf"
        assert result.dest_path is not None
        assert result.dest_path.exists()
        assert result.dest_path.read_text(encoding="utf-8") == FAKE_MD_PDF
        assert result.dest_path.parent == tmp_path / "HED-Markdown-public"

    def test_pdf_proprietary_lands_in_private(self, tmp_path: Path) -> None:
        ref = _ref(pdf_local={
            "path":       "HED-PDFs/Foo.pdf",
            "source_url": "https://example.com/source.pdf",
            "license":    "proprietary",
        })
        (tmp_path / "HED-PDFs").mkdir()
        (tmp_path / "HED-PDFs" / "Foo.pdf").write_bytes(b"%PDF-1.7\n")

        result = M.attempt_one_ref(
            ref, repo_root=tmp_path, write=True, bioc_only=False,
            cache_dir=tmp_path / "cache",
            lookup_fn=_empty_callable_must_not_run,
            bioc_fn=_empty_callable_must_not_run,
            convert_fn=_queue(FAKE_MD_PDF),
        )
        assert result.license_norm == "proprietary"
        assert result.is_publishable_flag is False
        assert result.dest_path.parent == tmp_path / "HED-Markdown-private"

    def test_pmc_failure_falls_through_to_pdf(self, tmp_path: Path) -> None:
        # PMCID set, but BioC lookup returns None (not in OA subset or
        # transient).  PDF on disk -> conversion happens.
        ref = _ref(
            pmcid="PMC9999999",
            pdf_local={"path": "HED-PDFs/Foo.pdf",
                       "source_url": "https://example.com/source.pdf",
                       "license": "cc-by"},
        )
        (tmp_path / "HED-PDFs").mkdir()
        (tmp_path / "HED-PDFs" / "Foo.pdf").write_bytes(b"%PDF-1.7\n")

        result = M.attempt_one_ref(
            ref, repo_root=tmp_path, write=True, bioc_only=False,
            cache_dir=tmp_path / "cache",
            lookup_fn=_queue(None),  # PMC unavailable
            bioc_fn=_empty_callable_must_not_run,
            convert_fn=_queue(FAKE_MD_PDF),
        )
        assert result.kind == "success"
        assert result.converter == "marker-pdf"

    def test_pdf_normalises_raw_license(self, tmp_path: Path) -> None:
        ref = _ref(pdf_local={"path": "HED-PDFs/Foo.pdf",
                              "license": "CC-BY 4.0"})
        (tmp_path / "HED-PDFs").mkdir()
        (tmp_path / "HED-PDFs" / "Foo.pdf").write_bytes(b"%PDF-1.7\n")

        result = M.attempt_one_ref(
            ref, repo_root=tmp_path, write=True, bioc_only=False,
            cache_dir=tmp_path / "cache",
            lookup_fn=_empty_callable_must_not_run,
            bioc_fn=_empty_callable_must_not_run,
            convert_fn=_queue(FAKE_MD_PDF),
        )
        assert result.license_norm == "cc-by"


# ---------------------------------------------------------------------------
# attempt_one_ref — Failures
# ---------------------------------------------------------------------------

class TestAttemptOneRefFailures:

    def test_no_pmc_no_pdf_records_clean_failure(self, tmp_path: Path) -> None:
        ref = _ref()
        result = M.attempt_one_ref(
            ref, repo_root=tmp_path, write=True, bioc_only=False,
            cache_dir=tmp_path / "cache",
            lookup_fn=_empty_callable_must_not_run,
            bioc_fn=_empty_callable_must_not_run,
            convert_fn=_empty_callable_must_not_run,
        )
        assert result.kind == "failure"
        assert result.tried == []
        assert result.reason == "no PMC and no on-disk PDF"

    def test_pmc_failure_no_pdf_records_pmc_tried(self, tmp_path: Path) -> None:
        ref = _ref(pmcid="PMC9999999")
        result = M.attempt_one_ref(
            ref, repo_root=tmp_path, write=True, bioc_only=False,
            cache_dir=tmp_path / "cache",
            lookup_fn=_queue(None),
            bioc_fn=_empty_callable_must_not_run,
            convert_fn=_empty_callable_must_not_run,
        )
        assert result.kind == "failure"
        assert result.tried == ["pmc_bioc"]
        assert "pmc_bioc" in result.reason

    def test_convert_pdf_import_error_records_failure(self, tmp_path: Path) -> None:
        # marker-pdf not installed: convert_fn raises ImportError.  The
        # ref-level handler records a failure; the run continues.
        ref = _ref(pdf_local={"path": "HED-PDFs/Foo.pdf", "license": "cc-by"})
        (tmp_path / "HED-PDFs").mkdir()
        (tmp_path / "HED-PDFs" / "Foo.pdf").write_bytes(b"%PDF-1.7\n")

        result = M.attempt_one_ref(
            ref, repo_root=tmp_path, write=True, bioc_only=False,
            cache_dir=tmp_path / "cache",
            lookup_fn=_empty_callable_must_not_run,
            bioc_fn=_empty_callable_must_not_run,
            convert_fn=_queue(ImportError("marker-pdf is required")),
        )
        assert result.kind == "failure"
        assert result.tried == ["marker-pdf"]
        assert "not installed" in result.reason

    def test_convert_pdf_runtime_error_records_failure(self, tmp_path: Path) -> None:
        ref = _ref(pdf_local={"path": "HED-PDFs/Foo.pdf", "license": "cc-by"})
        (tmp_path / "HED-PDFs").mkdir()
        (tmp_path / "HED-PDFs" / "Foo.pdf").write_bytes(b"%PDF-1.7\n")

        result = M.attempt_one_ref(
            ref, repo_root=tmp_path, write=True, bioc_only=False,
            cache_dir=tmp_path / "cache",
            lookup_fn=_empty_callable_must_not_run,
            bioc_fn=_empty_callable_must_not_run,
            convert_fn=_queue(RuntimeError("model crashed")),
        )
        assert result.kind == "failure"
        assert result.tried == ["marker-pdf"]
        assert "RuntimeError" in result.reason
        assert "model crashed" in result.reason

    def test_pmc_succeeds_but_bioc_to_markdown_raises(self, tmp_path: Path) -> None:
        # Defensive: a rendering bug should surface as a per-ref failure
        # rather than aborting the whole run.
        ref = _ref(pmcid="PMC4097944")
        result = M.attempt_one_ref(
            ref, repo_root=tmp_path, write=True, bioc_only=False,
            cache_dir=tmp_path / "cache",
            lookup_fn=_queue(_bioc(license="CC-BY")),
            bioc_fn=_queue(ValueError("malformed passage")),
            convert_fn=_empty_callable_must_not_run,
        )
        assert result.kind == "failure"
        assert "pmc_bioc" in result.tried
        assert "ValueError" in result.reason

    def test_pmc_failure_then_pdf_failure_records_both_in_tried(self,
                                                                  tmp_path: Path) -> None:
        # PMC tried + failed; PDF on disk + marker-pdf fails.  tried[]
        # should reflect both routes.
        ref = _ref(
            pmcid="PMC9999999",
            pdf_local={"path": "HED-PDFs/Foo.pdf", "license": "cc-by"},
        )
        (tmp_path / "HED-PDFs").mkdir()
        (tmp_path / "HED-PDFs" / "Foo.pdf").write_bytes(b"%PDF-1.7\n")

        result = M.attempt_one_ref(
            ref, repo_root=tmp_path, write=True, bioc_only=False,
            cache_dir=tmp_path / "cache",
            lookup_fn=_queue(None),
            bioc_fn=_empty_callable_must_not_run,
            convert_fn=_queue(ImportError("not installed")),
        )
        assert result.kind == "failure"
        assert result.tried == ["pmc_bioc", "marker-pdf"]


# ---------------------------------------------------------------------------
# attempt_one_ref — --bioc-only semantics
# ---------------------------------------------------------------------------

class TestAttemptOneRefBiocOnly:

    def test_bioc_only_skips_refs_without_pmcid(self, tmp_path: Path) -> None:
        ref = _ref(pdf_local={"path": "HED-PDFs/Foo.pdf", "license": "cc-by"})
        result = M.attempt_one_ref(
            ref, repo_root=tmp_path, write=True, bioc_only=True,
            cache_dir=tmp_path / "cache",
            lookup_fn=_empty_callable_must_not_run,
            bioc_fn=_empty_callable_must_not_run,
            convert_fn=_empty_callable_must_not_run,  # never reached
        )
        assert result.kind == "skipped_no_pmcid"

    def test_bioc_only_pmc_success(self, tmp_path: Path) -> None:
        ref = _ref(pmcid="PMC4097944")
        result = M.attempt_one_ref(
            ref, repo_root=tmp_path, write=True, bioc_only=True,
            cache_dir=tmp_path / "cache",
            lookup_fn=_queue(_bioc(license="CC-BY")),
            bioc_fn=_queue(FAKE_MD_BIOC),
            convert_fn=_empty_callable_must_not_run,
        )
        assert result.kind == "success"
        assert result.converter == "pmc_bioc"

    def test_bioc_only_pmc_failure_records_failure(self, tmp_path: Path) -> None:
        # In bioc-only mode, PMC failure does NOT fall through to PDF
        # even if a PDF is on disk.
        ref = _ref(
            pmcid="PMC9999999",
            pdf_local={"path": "HED-PDFs/Foo.pdf", "license": "cc-by"},
        )
        result = M.attempt_one_ref(
            ref, repo_root=tmp_path, write=True, bioc_only=True,
            cache_dir=tmp_path / "cache",
            lookup_fn=_queue(None),
            bioc_fn=_empty_callable_must_not_run,
            convert_fn=_empty_callable_must_not_run,  # must not be called
        )
        assert result.kind == "failure"
        assert result.tried == ["pmc_bioc"]


# ---------------------------------------------------------------------------
# End-to-end via main()
# ---------------------------------------------------------------------------

POC_FLEMING  = "10.3389/fnhum.2014.00443"
POC_SALAMONE = "10.1007/s00213-006-0668-9"
POC_DAW      = "10.1038/nn1560"


def _make_workspace(tmp_path: Path,
                    processes: list[dict],
                    tasks: list[dict]) -> Path:
    """Materialise a synthetic workspace with the two catalog files."""
    ws = tmp_path / "Claude-research"
    ws.mkdir(parents=True, exist_ok=True)
    (ws / "process_details.json").write_text(
        json.dumps({"processes": processes}, indent=2), encoding="utf-8")
    (ws / "task_details.json").write_text(
        json.dumps(tasks, indent=2), encoding="utf-8")
    return ws


def _read_catalog(ws: Path) -> tuple[dict, list]:
    procs = json.loads((ws / "process_details.json").read_text(encoding="utf-8"))
    tasks = json.loads((ws / "task_details.json").read_text(encoding="utf-8"))
    return procs, tasks


class TestMainIntegration:

    def test_poc_dry_run_does_not_modify_catalog(self,
                                                  tmp_path: Path,
                                                  capsys) -> None:
        ws = _make_workspace(
            tmp_path,
            processes=[{
                "process_id": "hed_test",
                "references": [_ref(pmcid="PMC4097944", doi=POC_FLEMING)],
            }],
            tasks=[],
        )
        rc = M.main(
            ["--mode", "poc", "--workspace", str(ws)],
            lookup_fn=_empty_callable_must_not_run,
            bioc_fn=_empty_callable_must_not_run,
            convert_fn=_empty_callable_must_not_run,
        )
        assert rc == 0
        procs, _ = _read_catalog(ws)
        ref = procs["processes"][0]["references"][0]
        assert "local_artifacts" not in ref
        out = capsys.readouterr().out
        assert "pmc_bioc" in out
        assert "dry-run complete" in out

    def test_poc_wet_run_pmc_success_stamps_catalog(self, tmp_path: Path) -> None:
        ws = _make_workspace(
            tmp_path,
            processes=[{
                "process_id": "hed_test",
                "references": [_ref(pmcid="PMC4097944", doi=POC_FLEMING)],
            }],
            tasks=[],
        )
        rc = M.main(
            ["--mode", "poc", "--workspace", str(ws), "--write"],
            lookup_fn=_queue(_bioc(license="CC-BY")),
            bioc_fn=_queue(FAKE_MD_BIOC),
            convert_fn=_empty_callable_must_not_run,
        )
        assert rc == 0
        # File on disk in HED-Markdown-public/.
        mds = list((tmp_path / "HED-Markdown-public").glob("*.md"))
        assert len(mds) == 1
        # Catalog stamped.
        procs, _ = _read_catalog(ws)
        la = procs["processes"][0]["references"][0]["local_artifacts"]["markdown"]
        assert la["path"].startswith("HED-Markdown-public/")
        assert la["source_type"] == "auto_pmc_bioc"
        assert la["converter"] == "pmc_bioc"
        assert la["license"] == "cc-by"
        assert la["is_publishable"] is True

    def test_poc_wet_run_no_pmc_no_pdf_records_failure(self,
                                                       tmp_path: Path) -> None:
        # Daw-shaped ref: no pmcid, no PDF -> failure.
        ws = _make_workspace(
            tmp_path,
            processes=[{
                "process_id": "hed_test",
                "references": [_ref(doi=POC_DAW)],
            }],
            tasks=[],
        )
        rc = M.main(
            ["--mode", "poc", "--workspace", str(ws), "--write"],
            lookup_fn=_empty_callable_must_not_run,
            bioc_fn=_empty_callable_must_not_run,
            convert_fn=_empty_callable_must_not_run,
        )
        assert rc == 0
        procs, _ = _read_catalog(ws)
        la = procs["processes"][0]["references"][0]["local_artifacts"]["markdown"]
        assert la["path"] is None
        assert la["attempts"] == 1
        assert la["tried"] == []
        assert la["reason"] == "no PMC and no on-disk PDF"
        # Success-only keys absent.
        for key in ("source_url", "source_type", "license",
                    "converter", "is_publishable", "acquired_on"):
            assert key not in la

    def test_wet_run_is_idempotent_on_re_run(self, tmp_path: Path) -> None:
        ws = _make_workspace(
            tmp_path,
            processes=[{
                "process_id": "hed_test",
                "references": [_ref(pmcid="PMC4097944", doi=POC_FLEMING)],
            }],
            tasks=[],
        )
        # Run 1: success.
        M.main(
            ["--mode", "poc", "--workspace", str(ws), "--write"],
            lookup_fn=_queue(_bioc(license="CC-BY")),
            bioc_fn=_queue(FAKE_MD_BIOC),
            convert_fn=_empty_callable_must_not_run,
        )
        before, _ = _read_catalog(ws)
        # Run 2: queues are empty; if PMC fires we crash.
        rc = M.main(
            ["--mode", "poc", "--workspace", str(ws), "--write"],
            lookup_fn=_empty_callable_must_not_run,
            bioc_fn=_empty_callable_must_not_run,
            convert_fn=_empty_callable_must_not_run,
        )
        assert rc == 0
        after, _ = _read_catalog(ws)
        assert before == after

    def test_wet_run_skips_prior_failure_by_default(self, tmp_path: Path) -> None:
        ref = _ref(pmcid="PMC4097944", doi=POC_FLEMING)
        ref["local_artifacts"] = {"markdown": {
            "path": None,
            "last_attempt": "2026-05-01T00:00:00Z",
            "attempts": 1,
            "tried":  ["pmc_bioc"],
            "reason": "earlier attempt",
        }}
        ws = _make_workspace(
            tmp_path,
            processes=[{"process_id": "hed_test", "references": [ref]}],
            tasks=[],
        )
        before, _ = _read_catalog(ws)
        rc = M.main(
            ["--mode", "poc", "--workspace", str(ws), "--write"],
            lookup_fn=_empty_callable_must_not_run,
            bioc_fn=_empty_callable_must_not_run,
            convert_fn=_empty_callable_must_not_run,
        )
        assert rc == 0
        after, _ = _read_catalog(ws)
        assert before == after

    def test_retry_failed_flag_re_attempts(self, tmp_path: Path) -> None:
        ref = _ref(pmcid="PMC4097944", doi=POC_FLEMING)
        ref["local_artifacts"] = {"markdown": {
            "path": None,
            "last_attempt": "2026-05-01T00:00:00Z",
            "attempts": 2,
            "tried":  ["pmc_bioc"],
            "reason": "earlier attempt",
        }}
        ws = _make_workspace(
            tmp_path,
            processes=[{"process_id": "hed_test", "references": [ref]}],
            tasks=[],
        )
        rc = M.main(
            ["--mode", "poc", "--workspace", str(ws),
             "--write", "--retry-failed"],
            lookup_fn=_queue(_bioc(license="CC-BY")),
            bioc_fn=_queue(FAKE_MD_BIOC),
            convert_fn=_empty_callable_must_not_run,
        )
        assert rc == 0
        procs, _ = _read_catalog(ws)
        la = procs["processes"][0]["references"][0]["local_artifacts"]["markdown"]
        assert la["path"].startswith("HED-Markdown-public/")
        # Failure-only keys were cleared on success.
        for k in ("last_attempt", "attempts", "tried", "reason"):
            assert k not in la

    def test_force_re_acquires_successful_ref(self, tmp_path: Path) -> None:
        ref = _ref(pmcid="PMC4097944", doi=POC_FLEMING)
        ref["local_artifacts"] = {"markdown": {
            "path":           "HED-Markdown-public/stale.md",
            "source_url":     "https://stale.example.com/",
            "source_type":    "auto_pmc_bioc",
            "license":        "cc-by",
            "acquired_on":    "2025-12-01T00:00:00Z",
            "acquired_via":   "auto",
            "converter":      "pmc_bioc",
            "is_publishable": True,
        }}
        ws = _make_workspace(
            tmp_path,
            processes=[{"process_id": "hed_test", "references": [ref]}],
            tasks=[],
        )
        rc = M.main(
            ["--mode", "poc", "--workspace", str(ws), "--write", "--force"],
            lookup_fn=_queue(_bioc(license="CC-BY")),
            bioc_fn=_queue(FAKE_MD_BIOC),
            convert_fn=_empty_callable_must_not_run,
        )
        assert rc == 0
        procs, _ = _read_catalog(ws)
        la = procs["processes"][0]["references"][0]["local_artifacts"]["markdown"]
        # Original acquired_on preserved per record_success.
        assert la["acquired_on"] == "2025-12-01T00:00:00Z"
        # New filename was written (the canonical one for this ref).
        assert la["path"].startswith("HED-Markdown-public/Fleming_2014_")

    def test_bioc_only_skip_does_not_stamp_failure(self, tmp_path: Path) -> None:
        # Two refs: one with pmcid, one without.  --bioc-only writes
        # Markdown for the first; the second is skipped silently
        # (no catalog change).
        ref_with_pmc = _ref(pmcid="PMC4097944", doi=POC_FLEMING)
        ref_without  = _ref(doi=POC_DAW)
        ws = _make_workspace(
            tmp_path,
            processes=[
                {"process_id": "hed_a", "references": [ref_with_pmc]},
                {"process_id": "hed_b", "references": [ref_without]},
            ],
            tasks=[],
        )
        rc = M.main(
            ["--mode", "poc", "--workspace", str(ws),
             "--write", "--bioc-only"],
            lookup_fn=_queue(_bioc(license="CC-BY")),
            bioc_fn=_queue(FAKE_MD_BIOC),
            convert_fn=_empty_callable_must_not_run,
        )
        assert rc == 0
        procs, _ = _read_catalog(ws)
        # Ref with PMCID: success stamp.
        la_a = procs["processes"][0]["references"][0]["local_artifacts"]["markdown"]
        assert la_a["path"].startswith("HED-Markdown-public/")
        # Ref without PMCID: untouched.
        assert "local_artifacts" not in procs["processes"][1]["references"][0]

    def test_returns_2_when_catalog_missing(self, tmp_path: Path) -> None:
        ws = tmp_path / "missing-workspace"
        ws.mkdir()
        rc = M.main(["--mode", "poc", "--workspace", str(ws)],
                    lookup_fn=_empty_callable_must_not_run,
                    bioc_fn=_empty_callable_must_not_run,
                    convert_fn=_empty_callable_must_not_run)
        assert rc == 2
