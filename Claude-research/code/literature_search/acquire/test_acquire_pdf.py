"""
test_acquire_pdf.py — Unit + integration tests for acquire/acquire_pdf.py.

All tests inject a fake ``fetch_fn`` so the network is never touched.
Filesystem writes go to ``tmp_path`` fixtures so no real catalog or
HED-PDFs/ directory is mutated.

Three concentric layers:

  TestSourceTypeStamp        Pure helper: composition of source_type
                             from ``pdf_locations`` entry's ``source``.
  TestAttemptWalk            One-ref walk semantics: success on first
                             try, walk past HTML/HTTP errors, total
                             failure shape, empty candidates per
                             PRE-E2-Q1.
  TestAttemptOneRefDryRun    Wet/dry-run split.
  TestMainIntegration        End-to-end: synthetic catalog files in
                             ``tmp_path``, ``main(argv, fetch_fn=…)``
                             drives a POC dry-run and a wet-run.  Covers
                             the catalog round-trip, idempotency, and
                             the failure-record path.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Sequence

import pytest

# Make ``acquire/`` and its parent (``literature_search/``) importable
# when pytest runs the file directly.  Matches the convention used by
# test_priority.py / test_core.py / test_fetch.py.
_HERE = Path(__file__).resolve().parent
_PARENT = _HERE.parent
for p in (_HERE, _PARENT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import acquire_pdf as M  # noqa: E402  module under test
from fetch import FetchResult  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PDF_BYTES = b"%PDF-1.7\n%fake pdf body\n"


def _loc(url: str, *, source: str = "openalex",
         version: str = "publishedVersion", license: str = "cc-by",
         is_oa: bool = True) -> dict:
    """Build a synthetic ``pdf_locations[]`` entry."""
    return {"url": url, "source": source, "version": version,
            "license": license, "is_oa": is_oa}


def _ref(*locs: dict, doi: str | None = None) -> dict:
    """Build a minimal ref with the catalog shape acquire_pdf reads.

    Default ``doi=None`` so synthesize_id_shortcuts (PR-H2) does NOT
    inject a ``synthesized:doi`` candidate.  Tests that want to
    exercise DOI-based behaviour pass ``doi=<some-doi>`` explicitly.
    """
    return {
        "authors": "Smith, J., & Jones, K.",
        "year": 2008,
        "title": "Synthetic test paper",
        "ids": {"doi": doi},
        "pdf_locations": list(locs),
    }


def _queue_fetch(*results: FetchResult):
    """Return a fake ``fetch_fn`` that serves ``results`` in order."""
    pending = list(results)
    calls: list[dict] = []

    def fake(url: str, **kwargs) -> FetchResult:
        calls.append({"url": url, **kwargs})
        if not pending:
            raise AssertionError(f"fetch called more times than queued ({url})")
        return pending.pop(0)

    fake.calls = calls  # type: ignore[attr-defined]
    return fake


def _pdf_response(url: str = "https://example.com/x.pdf") -> FetchResult:
    return FetchResult(status=200, url=url, content_type="application/pdf",
                       body=PDF_BYTES, error=None, headers={})


def _html_response(url: str = "https://example.com/landing") -> FetchResult:
    return FetchResult(status=200, url=url, content_type="text/html",
                       body=b"<html>landing</html>", error=None, headers={})


def _network_error(url: str = "https://example.com/x") -> FetchResult:
    return FetchResult(status=0, url=url, content_type="", body=b"",
                       error="ConnectionError: DNS failure", headers={})


def _http_404(url: str = "https://example.com/x") -> FetchResult:
    return FetchResult(status=404, url=url, content_type="text/plain",
                       body=b"not found", error=None, headers={})


# ---------------------------------------------------------------------------
# _source_type_for
# ---------------------------------------------------------------------------

class TestSourceTypeStamp:

    def test_single_source(self) -> None:
        assert M._source_type_for("openalex") == "auto_openalex"

    def test_comma_joined_sources_preserved(self) -> None:
        # PR-D's merge can union two sources for the same URL into a
        # comma-joined string; we keep the full string so the catalog
        # records the full provenance.
        assert M._source_type_for("openalex,unpaywall") == "auto_openalex,unpaywall"

    def test_empty_string_falls_back_to_unknown(self) -> None:
        assert M._source_type_for("") == "auto_unknown"
        assert M._source_type_for("   ") == "auto_unknown"


# ---------------------------------------------------------------------------
# _attempt_walk
# ---------------------------------------------------------------------------

class TestAttemptWalk:

    def test_first_candidate_success(self, tmp_path: Path) -> None:
        ref = _ref(_loc("https://example.com/a.pdf", source="openalex"))
        cands = M._plan_walk(ref, allow_paywalled=False)
        fake = _queue_fetch(_pdf_response("https://example.com/a-final.pdf"))

        result = M._attempt_walk(
            ref, cands, repo_root=tmp_path, fetch_fn=fake,
            timeout=5, max_bytes=1024, host_throttle_sec=0,
        )

        assert result.kind == "success"
        assert result.source_tag == "openalex"
        assert result.license_norm == "cc-by"
        assert result.source_url == "https://example.com/a-final.pdf"
        assert result.dest_path is not None
        assert result.dest_path.exists()
        assert result.dest_path.read_bytes() == PDF_BYTES
        # Lands under HED-PDFs/, filename canonical per identity.py.
        assert result.dest_path.parent == tmp_path / "HED-PDFs"
        assert result.dest_path.name.startswith("Smith_2008_SyntheticTestPaper_")
        assert result.dest_path.name.endswith(".pdf")

    def test_walks_past_html_to_pdf(self, tmp_path: Path) -> None:
        # First candidate returns an HTML landing page; second is the
        # actual PDF.  Walk should stop at the second.
        ref = _ref(
            _loc("https://landing.example.com/abs", source="openalex"),
            _loc("https://repo.example.com/file.pdf", source="unpaywall"),
        )
        cands = M._plan_walk(ref, allow_paywalled=False)
        fake = _queue_fetch(_html_response(), _pdf_response())

        result = M._attempt_walk(
            ref, cands, repo_root=tmp_path, fetch_fn=fake,
            timeout=5, max_bytes=1024, host_throttle_sec=0,
        )

        assert result.kind == "success"
        assert result.source_tag == "unpaywall"
        assert len(fake.calls) == 2

    def test_walks_past_http_404(self, tmp_path: Path) -> None:
        ref = _ref(
            _loc("https://gone.example.com/x.pdf", source="openalex"),
            _loc("https://there.example.com/x.pdf", source="unpaywall"),
        )
        cands = M._plan_walk(ref, allow_paywalled=False)
        fake = _queue_fetch(_http_404(), _pdf_response())
        result = M._attempt_walk(
            ref, cands, repo_root=tmp_path, fetch_fn=fake,
            timeout=5, max_bytes=1024, host_throttle_sec=0,
        )
        assert result.kind == "success"

    def test_walks_past_network_error(self, tmp_path: Path) -> None:
        ref = _ref(
            _loc("https://dns.example.com/x.pdf", source="openalex"),
            _loc("https://there.example.com/x.pdf", source="unpaywall"),
        )
        cands = M._plan_walk(ref, allow_paywalled=False)
        fake = _queue_fetch(_network_error(), _pdf_response())
        result = M._attempt_walk(
            ref, cands, repo_root=tmp_path, fetch_fn=fake,
            timeout=5, max_bytes=1024, host_throttle_sec=0,
        )
        assert result.kind == "success"

    def test_all_candidates_fail(self, tmp_path: Path) -> None:
        ref = _ref(
            _loc("https://a.example.com/x", source="openalex"),
            _loc("https://b.example.com/x", source="unpaywall"),
        )
        cands = M._plan_walk(ref, allow_paywalled=False)
        fake = _queue_fetch(_html_response(), _html_response())
        result = M._attempt_walk(
            ref, cands, repo_root=tmp_path, fetch_fn=fake,
            timeout=5, max_bytes=1024, host_throttle_sec=0,
        )
        assert result.kind == "failure"
        assert result.tried == ["openalex", "unpaywall"]
        # The reason concatenates a per-source diagnostic.
        assert "openalex" in result.reason
        assert "unpaywall" in result.reason
        assert "not PDF" in result.reason
        # No PDF was written.
        pdfs = list((tmp_path / "HED-PDFs").glob("*")) if (tmp_path / "HED-PDFs").exists() else []
        assert pdfs == []

    def test_empty_candidates_records_no_candidate_locations(self,
                                                             tmp_path: Path) -> None:
        # PRE-E2-Q1 (resolved 2026-05-27): record failure for refs whose
        # pdf_locations is empty/all-paywalled, so the maintainer sees a
        # complete inventory of "still needs manual".
        result = M._attempt_walk(
            {"pdf_locations": []}, [],
            repo_root=tmp_path,
            fetch_fn=_queue_fetch(),
            timeout=5, max_bytes=1024, host_throttle_sec=0,
        )
        assert result.kind == "failure"
        assert result.tried == []
        assert result.reason == "no candidate locations"

    def test_stops_at_first_success(self, tmp_path: Path) -> None:
        # Confirm the walk does NOT keep going after the first PDF.
        ref = _ref(
            _loc("https://a.example.com/x.pdf", source="openalex"),
            _loc("https://b.example.com/x.pdf", source="unpaywall"),
        )
        cands = M._plan_walk(ref, allow_paywalled=False)
        fake = _queue_fetch(_pdf_response("https://a.example.com/x.pdf"))
        # Only one fetch queued; if walk continued past the first PDF
        # the test would fail with "fetch called more times than queued".
        result = M._attempt_walk(
            ref, cands, repo_root=tmp_path, fetch_fn=fake,
            timeout=5, max_bytes=1024, host_throttle_sec=0,
        )
        assert result.kind == "success"
        assert len(fake.calls) == 1

    def test_license_normalised_through_record(self, tmp_path: Path) -> None:
        # license_policy.normalise_license maps "CC-BY 4.0" -> "cc-by".
        ref = _ref(_loc("https://example.com/x.pdf",
                        source="openalex", license="CC-BY 4.0"))
        cands = M._plan_walk(ref, allow_paywalled=False)
        fake = _queue_fetch(_pdf_response())
        result = M._attempt_walk(
            ref, cands, repo_root=tmp_path, fetch_fn=fake,
            timeout=5, max_bytes=1024, host_throttle_sec=0,
        )
        assert result.license_norm == "cc-by"


# ---------------------------------------------------------------------------
# attempt_one_ref dry-run/wet-run split
# ---------------------------------------------------------------------------

class TestAttemptOneRefDryRun:

    def test_dry_run_returns_would_walk_without_fetching(self, tmp_path: Path) -> None:
        ref = _ref(_loc("https://example.com/x.pdf"))
        fake = _queue_fetch()  # would error if called
        result = M.attempt_one_ref(
            ref, repo_root=tmp_path, write=False, allow_paywalled=False,
            fetch_fn=fake, timeout=5, max_bytes=1024, host_throttle_sec=0,
        )
        assert result.kind == "would_walk"
        assert result.candidates is not None
        assert len(result.candidates) == 1
        assert fake.calls == []
        # No HED-PDFs/ created.
        assert not (tmp_path / "HED-PDFs").exists()

    def test_dry_run_empty_pdf_locations_still_returns_would_walk(self,
                                                                 tmp_path: Path) -> None:
        ref = _ref()  # no locations
        fake = _queue_fetch()
        result = M.attempt_one_ref(
            ref, repo_root=tmp_path, write=False, allow_paywalled=False,
            fetch_fn=fake, timeout=5, max_bytes=1024, host_throttle_sec=0,
        )
        # Dry-run reports the empty walk; the failure-record path only
        # fires on wet-run.
        assert result.kind == "would_walk"
        assert result.candidates == []

    def test_wet_run_with_pdf_writes_file_and_returns_success(self,
                                                              tmp_path: Path) -> None:
        ref = _ref(_loc("https://example.com/x.pdf"))
        fake = _queue_fetch(_pdf_response())
        result = M.attempt_one_ref(
            ref, repo_root=tmp_path, write=True, allow_paywalled=False,
            fetch_fn=fake, timeout=5, max_bytes=1024, host_throttle_sec=0,
        )
        assert result.kind == "success"
        assert result.dest_path is not None and result.dest_path.exists()


# ---------------------------------------------------------------------------
# End-to-end via main()
# ---------------------------------------------------------------------------

# Canonical POC DOIs declared in acquire/__init__.py.  Tests use these
# directly rather than re-importing to avoid coupling fixture data to
# the package's import path.
POC_FLEMING = "10.3389/fnhum.2014.00443"
POC_SALAMONE = "10.1007/s00213-006-0668-9"
POC_DAW      = "10.1038/nn1560"


def _make_workspace(tmp_path: Path,
                    processes: list[dict],
                    tasks: list[dict]) -> Path:
    """Materialise a synthetic workspace with the two catalog files.

    The workspace sits under ``tmp_path/Claude-research`` so that the
    parent (``tmp_path``) becomes the synthetic repo root and
    ``HED-PDFs/`` lands as a sibling — same layout as the real repo.
    """
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
        # Synthetic catalog with one Fleming-shaped ref matching the
        # POC DOI; main() in dry-run mode should leave catalog untouched.
        ws = _make_workspace(
            tmp_path,
            processes=[{
                "process_id": "hed_test",
                "references": [_ref(_loc("https://example.com/x.pdf"),
                                    doi=POC_FLEMING)],
            }],
            tasks=[],
        )
        rc = M.main(["--mode", "poc", "--workspace", str(ws),
                     "--host-throttle-sec", "0"],
                    fetch_fn=_queue_fetch())  # empty: must not be called
        assert rc == 0
        procs, _ = _read_catalog(ws)
        ref = procs["processes"][0]["references"][0]
        assert "local_artifacts" not in ref
        # No HED-PDFs/ was created.
        assert not (tmp_path / "HED-PDFs").exists()
        out = capsys.readouterr().out
        assert "1 candidate(s)" in out
        assert "dry-run complete" in out

    def test_poc_wet_run_saves_pdf_and_stamps_success(self,
                                                      tmp_path: Path,
                                                      capsys) -> None:
        ws = _make_workspace(
            tmp_path,
            processes=[{
                "process_id": "hed_test",
                "references": [_ref(_loc("https://example.com/x.pdf"),
                                    doi=POC_FLEMING)],
            }],
            tasks=[],
        )
        rc = M.main(
            ["--mode", "poc", "--workspace", str(ws), "--write",
             "--host-throttle-sec", "0"],
            fetch_fn=_queue_fetch(_pdf_response()),
        )
        assert rc == 0
        # PDF on disk.
        pdfs = list((tmp_path / "HED-PDFs").glob("*.pdf"))
        assert len(pdfs) == 1
        # Catalog stamped.
        procs, _ = _read_catalog(ws)
        la = procs["processes"][0]["references"][0]["local_artifacts"]["pdf"]
        assert la["path"].startswith("HED-PDFs/")
        assert la["source_type"] == "auto_openalex"
        assert la["license"] == "cc-by"
        assert la["acquired_via"] == "auto"
        assert la["is_publishable"] is True

    def test_wet_run_records_failure_for_empty_locations(self,
                                                        tmp_path: Path) -> None:
        # Daw-shaped ref: pdf_locations empty -> failure record per
        # PRE-E2-Q1.  POC_DAW is a 10.1038/ DOI so no preprint-prefix
        # shortcut fires; the walk has zero candidates.
        ws = _make_workspace(
            tmp_path,
            processes=[{
                "process_id": "hed_test",
                "references": [_ref(doi=POC_DAW)],
            }],
            tasks=[],
        )
        rc = M.main(
            ["--mode", "poc", "--workspace", str(ws), "--write",
             "--host-throttle-sec", "0"],
            fetch_fn=_queue_fetch(),
        )
        assert rc == 0
        procs, _ = _read_catalog(ws)
        la = procs["processes"][0]["references"][0]["local_artifacts"]["pdf"]
        assert la["path"] is None
        assert la["attempts"] == 1
        assert la["tried"] == []
        assert la["reason"] == "no candidate locations"
        assert "last_attempt" in la
        # Success-only keys are absent (record_failure symmetry).
        for key in ("source_url", "source_type", "license", "acquired_on"):
            assert key not in la

    def test_wet_run_is_idempotent_on_re_run(self, tmp_path: Path) -> None:
        # First run: success.  Second run with the same args (no
        # --force, no --retry-failed): ref is skipped, nothing changes.
        ws = _make_workspace(
            tmp_path,
            processes=[{
                "process_id": "hed_test",
                "references": [_ref(_loc("https://example.com/x.pdf"),
                                    doi=POC_FLEMING)],
            }],
            tasks=[],
        )
        # Run 1
        M.main(["--mode", "poc", "--workspace", str(ws), "--write",
                "--host-throttle-sec", "0"],
               fetch_fn=_queue_fetch(_pdf_response()))
        before, _ = _read_catalog(ws)
        # Run 2 — fetch queue is empty; if walk fires the test fails.
        rc = M.main(["--mode", "poc", "--workspace", str(ws), "--write",
                     "--host-throttle-sec", "0"],
                    fetch_fn=_queue_fetch())
        assert rc == 0
        after, _ = _read_catalog(ws)
        assert before == after

    def test_wet_run_skips_refs_with_prior_failure_by_default(self,
                                                              tmp_path: Path) -> None:
        # Stage a ref that already has a failure record; default flags
        # must skip it (no fetch, no change).
        ref = _ref(_loc("https://example.com/x.pdf"), doi=POC_FLEMING)
        ref["local_artifacts"] = {"pdf": {
            "path": None,
            "last_attempt": "2026-05-01T00:00:00Z",
            "attempts": 1,
            "tried": ["openalex"],
            "reason": "earlier attempt",
        }}
        ws = _make_workspace(
            tmp_path,
            processes=[{"process_id": "hed_test", "references": [ref]}],
            tasks=[],
        )
        before, _ = _read_catalog(ws)
        rc = M.main(["--mode", "poc", "--workspace", str(ws), "--write",
                     "--host-throttle-sec", "0"],
                    fetch_fn=_queue_fetch())  # empty: must not be called
        assert rc == 0
        after, _ = _read_catalog(ws)
        assert before == after

    def test_retry_failed_flag_re_attempts_failures(self, tmp_path: Path) -> None:
        # Same setup, but --retry-failed makes the orchestrator try
        # again.  This time we supply a successful fetch.
        ref = _ref(_loc("https://example.com/x.pdf"), doi=POC_FLEMING)
        ref["local_artifacts"] = {"pdf": {
            "path": None,
            "last_attempt": "2026-05-01T00:00:00Z",
            "attempts": 2,
            "tried": ["openalex"],
            "reason": "earlier attempt",
        }}
        ws = _make_workspace(
            tmp_path,
            processes=[{"process_id": "hed_test", "references": [ref]}],
            tasks=[],
        )
        rc = M.main(["--mode", "poc", "--workspace", str(ws),
                     "--write", "--retry-failed",
                     "--host-throttle-sec", "0"],
                    fetch_fn=_queue_fetch(_pdf_response()))
        assert rc == 0
        procs, _ = _read_catalog(ws)
        la = procs["processes"][0]["references"][0]["local_artifacts"]["pdf"]
        assert la["path"].startswith("HED-PDFs/")
        # Failure-only keys were cleared on transition to success.
        for k in ("last_attempt", "attempts", "tried", "reason"):
            assert k not in la

    def test_force_flag_re_acquires_successful_refs(self, tmp_path: Path) -> None:
        # Pre-existing success entry; --force re-acquires.
        ref = _ref(_loc("https://example.com/x.pdf"), doi=POC_FLEMING)
        ref["local_artifacts"] = {"pdf": {
            "path": "HED-PDFs/stale.pdf",
            "source_url": "https://stale.example.com/",
            "source_type": "auto_openalex",
            "license": "cc-by",
            "acquired_on": "2025-12-01T00:00:00Z",
            "acquired_via": "auto",
        }}
        ws = _make_workspace(
            tmp_path,
            processes=[{"process_id": "hed_test", "references": [ref]}],
            tasks=[],
        )
        rc = M.main(["--mode", "poc", "--workspace", str(ws),
                     "--write", "--force",
                     "--host-throttle-sec", "0"],
                    fetch_fn=_queue_fetch(_pdf_response("https://new.example.com/x.pdf")))
        assert rc == 0
        procs, _ = _read_catalog(ws)
        la = procs["processes"][0]["references"][0]["local_artifacts"]["pdf"]
        # acquired_on is preserved (per record_success); other fields refresh.
        assert la["acquired_on"] == "2025-12-01T00:00:00Z"
        assert la["source_url"] == "https://new.example.com/x.pdf"

    def test_returns_2_when_catalog_missing(self, tmp_path: Path) -> None:
        ws = tmp_path / "missing-workspace"
        ws.mkdir()
        rc = M.main(["--mode", "poc", "--workspace", str(ws)],
                    fetch_fn=_queue_fetch())
        assert rc == 2


# ---------------------------------------------------------------------------
# PR-F: per-candidate fetcher dispatch
# ---------------------------------------------------------------------------

# AC landing URL used by these tests.  Real-world value would carry an
# AC DOI under 10.7916/.  priority.classify_url returns "ac" for any
# academiccommons.columbia.edu URL, regardless of DOI.
AC_LANDING_URL = "https://academiccommons.columbia.edu/doi/10.7916/d8rv0nsn"

# AC-managed DOI on the bare resolver — triggers
# priority.synthesize_candidates to add an AC landing URL behind it.
AC_DOI_RESOLVER_URL = "https://doi.org/10.7916/d8rv0nsn"


def _queue_two_fetchers(
    plain_results: list[FetchResult] | None = None,
    browser_results: list[FetchResult] | None = None,
) -> tuple[object, object]:
    """Build a pair of fake fetchers; each records the URLs it received.

    Each fake serves its queued ``FetchResult`` list in order.  Asking
    for more responses than were queued raises so a test that routes
    a call to the wrong fetcher fails loudly rather than silently.
    """
    plain_pending = list(plain_results or [])
    browser_pending = list(browser_results or [])

    plain_calls: list[dict] = []
    browser_calls: list[dict] = []

    def fake_plain(url: str, **kwargs) -> FetchResult:
        plain_calls.append({"url": url, **kwargs})
        if not plain_pending:
            raise AssertionError(f"plain fetcher called unexpectedly ({url})")
        return plain_pending.pop(0)

    def fake_browser(url: str, **kwargs) -> FetchResult:
        browser_calls.append({"url": url, **kwargs})
        if not browser_pending:
            raise AssertionError(f"browser fetcher called unexpectedly ({url})")
        return browser_pending.pop(0)

    fake_plain.calls = plain_calls            # type: ignore[attr-defined]
    fake_browser.calls = browser_calls        # type: ignore[attr-defined]
    return fake_plain, fake_browser


class TestDispatch:
    """Per-candidate fetcher routing via :func:`priority.fetcher_for`.

    Plain (non-AC) candidates must route to ``fetch_fn``; AC candidates
    must route to ``browser_fetch_fn``.  Each test injects both
    fetchers explicitly and asserts the call list on each.
    """

    def test_plain_candidate_uses_fetch_fn_only(self, tmp_path: Path) -> None:
        ref = _ref(_loc("https://example.com/a.pdf", source="openalex"))
        cands = M._plan_walk(ref, allow_paywalled=False)
        plain, browser = _queue_two_fetchers(
            plain_results=[_pdf_response("https://example.com/a.pdf")],
        )

        result = M._attempt_walk(
            ref, cands, repo_root=tmp_path,
            fetch_fn=plain, browser_fetch_fn=browser,
            timeout=5, max_bytes=1024, host_throttle_sec=0,
        )

        assert result.kind == "success"
        assert len(plain.calls) == 1                 # type: ignore[attr-defined]
        assert len(browser.calls) == 0               # type: ignore[attr-defined]

    def test_ac_candidate_uses_browser_fetch_fn_only(self, tmp_path: Path) -> None:
        ref = _ref(_loc(AC_LANDING_URL, source="openalex"))
        cands = M._plan_walk(ref, allow_paywalled=False)
        plain, browser = _queue_two_fetchers(
            browser_results=[_pdf_response(AC_LANDING_URL)],
        )

        result = M._attempt_walk(
            ref, cands, repo_root=tmp_path,
            fetch_fn=plain, browser_fetch_fn=browser,
            timeout=5, max_bytes=1024, host_throttle_sec=0,
        )

        assert result.kind == "success"
        assert len(browser.calls) == 1               # type: ignore[attr-defined]
        assert len(plain.calls) == 0                 # type: ignore[attr-defined]
        # The browser fetcher does NOT receive host_throttle_sec —
        # Playwright's launch cost is its own implicit throttle.
        assert "host_throttle_sec" not in browser.calls[0]  # type: ignore[attr-defined]

    def test_synthesised_ac_entry_routes_to_browser(self, tmp_path: Path) -> None:
        # Input: a bare doi.org/10.7916/<id> resolver URL only.
        # priority.synthesize_candidates appends an AC landing URL
        # behind it; the AC entry sorts ahead of the doi.org entry by
        # tier, so the browser fetcher is tried first.
        ref = _ref(_loc(AC_DOI_RESOLVER_URL, source="openalex"))
        cands = M._plan_walk(ref, allow_paywalled=False)
        plain, browser = _queue_two_fetchers(
            browser_results=[_pdf_response(AC_LANDING_URL)],
        )

        result = M._attempt_walk(
            ref, cands, repo_root=tmp_path,
            fetch_fn=plain, browser_fetch_fn=browser,
            timeout=5, max_bytes=1024, host_throttle_sec=0,
        )

        assert result.kind == "success"
        assert result.source_tag == "synthesized:ac"
        assert len(browser.calls) == 1               # type: ignore[attr-defined]
        # The doi.org fallback was not tried — the browser route
        # succeeded first.
        assert len(plain.calls) == 0                 # type: ignore[attr-defined]

    def test_mixed_walk_dispatches_per_candidate(self, tmp_path: Path) -> None:
        # PMC PDF URL fails (HTML), then AC succeeds via browser.
        # Verifies the dispatch picks the right fetcher per candidate,
        # not per ref.  PMC URLs route plain (PR-H5 reverted PR-H4's
        # browser routing); AC URLs route to browser.
        ref = _ref(
            _loc("https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1/pdf/foo.pdf",
                 source="pmc"),
            _loc(AC_LANDING_URL, source="openalex"),
        )
        cands = M._plan_walk(ref, allow_paywalled=False)
        plain, browser = _queue_two_fetchers(
            plain_results=[_html_response()],
            browser_results=[_pdf_response(AC_LANDING_URL)],
        )

        result = M._attempt_walk(
            ref, cands, repo_root=tmp_path,
            fetch_fn=plain, browser_fetch_fn=browser,
            timeout=5, max_bytes=1024, host_throttle_sec=0,
        )

        assert result.kind == "success"
        assert result.source_tag == "openalex"
        assert len(plain.calls) == 1                 # type: ignore[attr-defined]
        assert len(browser.calls) == 1               # type: ignore[attr-defined]
        # Order: PMC tried first (plain), then AC (browser).
        assert plain.calls[0]["url"].startswith("https://www.ncbi.nlm.nih.gov/")  # type: ignore[attr-defined]
        assert browser.calls[0]["url"] == AC_LANDING_URL                          # type: ignore[attr-defined]

    def test_browser_fetcher_failure_recorded_with_tried(self, tmp_path: Path) -> None:
        # Browser returns a non-PDF response → walk continues.  Here
        # there is no fallback candidate, so the result is a failure
        # with "synthesized:ac" on the tried list.
        ref = _ref(_loc(AC_LANDING_URL, source="openalex"))
        cands = M._plan_walk(ref, allow_paywalled=False)
        plain, browser = _queue_two_fetchers(
            browser_results=[_html_response(AC_LANDING_URL)],
        )

        result = M._attempt_walk(
            ref, cands, repo_root=tmp_path,
            fetch_fn=plain, browser_fetch_fn=browser,
            timeout=5, max_bytes=1024, host_throttle_sec=0,
        )

        assert result.kind == "failure"
        assert result.tried == ["openalex"]
        assert "not PDF" in result.reason

    def test_main_threads_browser_fetch_fn(self, tmp_path: Path) -> None:
        # End-to-end via main(): a synthetic catalog with one AC ref
        # gets acquired through the injected browser fetcher; the
        # plain fetcher is never called.
        ref = _ref(_loc(AC_LANDING_URL, source="openalex"), doi=POC_FLEMING)
        ws = _make_workspace(
            tmp_path,
            processes=[{"process_id": "hed_test", "references": [ref]}],
            tasks=[],
        )
        plain, browser = _queue_two_fetchers(
            browser_results=[_pdf_response(AC_LANDING_URL)],
        )

        rc = M.main(
            ["--mode", "poc", "--workspace", str(ws), "--write",
             "--host-throttle-sec", "0"],
            fetch_fn=plain, browser_fetch_fn=browser,
        )

        assert rc == 0
        assert len(browser.calls) == 1               # type: ignore[attr-defined]
        assert len(plain.calls) == 0                 # type: ignore[attr-defined]
        procs, _ = _read_catalog(ws)
        la = procs["processes"][0]["references"][0]["local_artifacts"]["pdf"]
        assert la["path"].startswith("HED-PDFs/")
        assert la["source_type"] == "auto_openalex"


# ---------------------------------------------------------------------------
# PR-H1 — Landing-page PDF extraction
# ---------------------------------------------------------------------------

def _html_with_citation_pdf_url(pdf_url: str,
                                page_url: str = "https://landing.example.com/abs") -> FetchResult:
    """An HTML landing page advertising a citation_pdf_url meta tag."""
    body = (
        '<html><head>'
        f'<meta name="citation_pdf_url" content="{pdf_url}">'
        '</head><body>landing</body></html>'
    ).encode("utf-8")
    return FetchResult(status=200, url=page_url, content_type="text/html",
                       body=body, error=None, headers={})


class TestLandingExtraction:
    """PR-H1: when a candidate returns text/html, look for citation_pdf_url."""

    def test_landing_extracts_and_fetches_pdf(self, tmp_path: Path) -> None:
        ref = _ref(_loc("https://landing.example.com/abs",
                        source="openalex"))
        cands = M._plan_walk(ref, allow_paywalled=False)
        fake = _queue_fetch(
            _html_with_citation_pdf_url(
                "https://cdn.example.com/file.pdf",
                page_url="https://landing.example.com/abs",
            ),
            _pdf_response("https://cdn.example.com/file.pdf"),
        )

        result = M._attempt_walk(
            ref, cands, repo_root=tmp_path, fetch_fn=fake,
            timeout=5, max_bytes=1024, host_throttle_sec=0,
        )

        assert result.kind == "success"
        # Source tag carries the +landing provenance suffix.
        assert result.source_tag == "openalex+landing"
        # Two fetches: the landing GET and the PDF GET.
        assert len(fake.calls) == 2
        assert fake.calls[0]["url"] == "https://landing.example.com/abs"
        assert fake.calls[1]["url"] == "https://cdn.example.com/file.pdf"

    def test_landing_with_no_meta_tag_falls_through(self,
                                                    tmp_path: Path) -> None:
        # HTML body with no citation_pdf_url: extraction returns None
        # and no secondary fetch is made; walk continues to next candidate.
        ref = _ref(
            _loc("https://landing.example.com/abs", source="openalex"),
            _loc("https://repo.example.com/file.pdf", source="unpaywall"),
        )
        cands = M._plan_walk(ref, allow_paywalled=False)
        # The default _html_response body has no meta tag.
        fake = _queue_fetch(_html_response(), _pdf_response())
        result = M._attempt_walk(
            ref, cands, repo_root=tmp_path, fetch_fn=fake,
            timeout=5, max_bytes=1024, host_throttle_sec=0,
        )
        # Should land on the second candidate, not via +landing.
        assert result.kind == "success"
        assert result.source_tag == "unpaywall"
        assert len(fake.calls) == 2

    def test_landing_extraction_secondary_also_html_fails(self,
                                                          tmp_path: Path) -> None:
        # Primary HTML has a citation_pdf_url; secondary fetch returns
        # HTML (not a PDF).  Record both failures in the reason and
        # fall through to the next candidate.
        ref = _ref(
            _loc("https://landing.example.com/abs", source="openalex"),
        )
        cands = M._plan_walk(ref, allow_paywalled=False)
        fake = _queue_fetch(
            _html_with_citation_pdf_url("https://cdn.example.com/file.pdf"),
            _html_response("https://cdn.example.com/file.pdf"),
        )
        result = M._attempt_walk(
            ref, cands, repo_root=tmp_path, fetch_fn=fake,
            timeout=5, max_bytes=1024, host_throttle_sec=0,
        )
        assert result.kind == "failure"
        # tried records both the original tag and the +landing extension.
        assert "openalex" in result.tried
        assert "openalex+landing" in result.tried
        # Reason has the +landing failure note.
        assert "openalex+landing" in result.reason

    def test_pmc_oa_success_via_plain_fetcher(self, tmp_path: Path) -> None:
        # PR-H5: _plan_walk synthesizes a pmc_oa candidate from the
        # OA Web Service.  The URL is on ftp.ncbi.nlm.nih.gov (or
        # similar plain-HTTP host); the plain fetcher walks it.
        ref = {
            "ids": {"pmcid": "PMC4097944", "doi": None, "arxiv_id": None,
                    "pmid": None, "openalex_id": None, "s2_id": None},
            "pdf_locations": [],
        }
        oa_url = ("https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_pdf/"
                  "08/56/fnhum-08-00443.pdf")
        cands = M._plan_walk(
            ref, allow_paywalled=False, cache_dir=tmp_path,
            oa_lookup_fn=lambda pmcid, cd: oa_url,
        )
        assert len(cands) == 1
        assert cands[0]["source"] == "pmc_oa"
        assert cands[0]["url"] == oa_url

        plain, browser = _queue_two_fetchers(
            plain_results=[_pdf_response(oa_url)],
        )
        result = M._attempt_walk(
            ref, cands, repo_root=tmp_path,
            fetch_fn=plain, browser_fetch_fn=browser,
            timeout=5, max_bytes=1024, host_throttle_sec=0,
        )
        assert result.kind == "success"
        assert result.source_tag == "pmc_oa"
        assert len(plain.calls) == 1                  # type: ignore[attr-defined]
        assert len(browser.calls) == 0                # type: ignore[attr-defined]

    def test_landing_extraction_accepts_magic_bytes(self,
                                                    tmp_path: Path) -> None:
        # The extracted URL serves a PDF with octet-stream Content-Type;
        # PR-H2's magic-byte check should recover it.
        ref = _ref(_loc("https://landing.example.com/abs", source="openalex"))
        cands = M._plan_walk(ref, allow_paywalled=False)
        octet_pdf = FetchResult(
            status=200, url="https://cdn.example.com/file.pdf",
            content_type="application/octet-stream",
            body=PDF_BYTES, error=None, headers={},
        )
        fake = _queue_fetch(
            _html_with_citation_pdf_url("https://cdn.example.com/file.pdf"),
            octet_pdf,
        )
        result = M._attempt_walk(
            ref, cands, repo_root=tmp_path, fetch_fn=fake,
            timeout=5, max_bytes=1024, host_throttle_sec=0,
        )
        assert result.kind == "success"
        assert result.source_tag == "openalex+landing"


# ---------------------------------------------------------------------------
# PR-H2 — Shortcut URL synthesis in _plan_walk
# ---------------------------------------------------------------------------

class TestPlanWalkShortcuts:
    """PR-H2: _plan_walk combines pdf_locations with ID-derived shortcuts.

    Note: ``synthesized:pmc`` and ``synthesized:doi`` were retired on
    2026-06-02 (see ``.status/session_2026-06-02_pmc_shortcut.md``)
    after the wet-run showed 0 ref-level recoveries from either.
    Only ``synthesized:arxiv`` and ``synthesized:biorxiv`` remain.
    """

    def test_arxiv_id_appends_arxiv_pdf_url(self) -> None:
        ref = {
            "ids": {"arxiv_id": "2104.12345", "doi": None,
                    "pmcid": None, "pmid": None,
                    "openalex_id": None, "s2_id": None},
            "pdf_locations": [],
        }
        cands = M._plan_walk(ref, allow_paywalled=False)
        urls = [c["url"] for c in cands]
        assert "https://arxiv.org/pdf/2104.12345" in urls

    def test_biorxiv_doi_appends_full_pdf_url(self) -> None:
        ref = {
            "ids": {"doi": "10.1101/2024.01.01.000001", "arxiv_id": None,
                    "pmcid": None, "pmid": None,
                    "openalex_id": None, "s2_id": None},
            "pdf_locations": [],
        }
        cands = M._plan_walk(ref, allow_paywalled=False)
        urls = [c["url"] for c in cands]
        assert any("biorxiv.org/content" in u and "full.pdf" in u for u in urls)

    def test_non_biorxiv_doi_no_shortcut(self) -> None:
        # 2026-06-02: the doi.org fallback was retired.  A plain DOI
        # ref with no preprint signal yields zero shortcuts.
        ref = {
            "ids": {"doi": "10.1234/foo", "arxiv_id": None,
                    "pmcid": None, "pmid": None,
                    "openalex_id": None, "s2_id": None},
            "pdf_locations": [_loc("https://repo.example.com/file.pdf",
                                   source="openalex")],
        }
        cands = M._plan_walk(ref, allow_paywalled=False)
        urls = [c["url"] for c in cands]
        assert urls == ["https://repo.example.com/file.pdf"]

    def test_pmcid_no_static_shortcut(self) -> None:
        # PR-H5: synthesize_id_shortcuts no longer emits a PMC
        # candidate.  The OA Web Service handles that (see
        # TestPlanWalkPMCOA below).
        ref = {
            "ids": {"pmcid": "PMC9999999", "doi": None, "arxiv_id": None,
                    "pmid": None, "openalex_id": None, "s2_id": None},
            "pdf_locations": [_loc("https://repo.example.com/file.pdf",
                                   source="openalex")],
        }
        cands = M._plan_walk(ref, allow_paywalled=False)
        urls = [c["url"] for c in cands]
        assert urls == ["https://repo.example.com/file.pdf"]


class TestPlanWalkPMCOA:
    """PR-H5: _plan_walk calls clients.pmc.lookup_oa_pdf_url for
    refs with ids.pmcid and a non-None cache_dir.  The OA hit is
    appended as a ``pmc_oa`` candidate; OA misses produce no
    candidate.
    """

    def test_oa_hit_appended_as_candidate(self, tmp_path: Path) -> None:
        ref = {
            "ids": {"pmcid": "PMC4097944", "doi": None, "arxiv_id": None,
                    "pmid": None, "openalex_id": None, "s2_id": None},
            "pdf_locations": [],
        }
        # Stub OA lookup returns a known-good URL.
        cands = M._plan_walk(
            ref, allow_paywalled=False, cache_dir=tmp_path,
            oa_lookup_fn=lambda pmcid, cd: (
                "https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_pdf/"
                "08/56/fnhum-08-00443.pdf"
            ),
        )
        sources = [c.get("source") for c in cands]
        assert "pmc_oa" in sources
        oa = next(c for c in cands if c["source"] == "pmc_oa")
        assert oa["url"].endswith("/fnhum-08-00443.pdf")
        assert oa["is_oa"] is True

    def test_oa_miss_yields_no_candidate(self, tmp_path: Path) -> None:
        ref = {
            "ids": {"pmcid": "PMC4598943", "doi": None, "arxiv_id": None,
                    "pmid": None, "openalex_id": None, "s2_id": None},
            "pdf_locations": [_loc("https://repo.example.com/file.pdf",
                                   source="openalex")],
        }
        cands = M._plan_walk(
            ref, allow_paywalled=False, cache_dir=tmp_path,
            oa_lookup_fn=lambda pmcid, cd: None,
        )
        sources = [c.get("source") for c in cands]
        assert "pmc_oa" not in sources

    def test_no_cache_dir_skips_oa_lookup(self) -> None:
        # Tests without cache infrastructure pass cache_dir=None and
        # the OA lookup is skipped entirely (no stub needed).
        called = []
        def stub(pmcid, cd):
            called.append(pmcid)
            return "https://example.com/x.pdf"
        ref = {
            "ids": {"pmcid": "PMC4097944", "doi": None, "arxiv_id": None,
                    "pmid": None, "openalex_id": None, "s2_id": None},
            "pdf_locations": [],
        }
        cands = M._plan_walk(
            ref, allow_paywalled=False, cache_dir=None, oa_lookup_fn=stub,
        )
        assert called == []
        assert cands == []  # no cataloged URL, no synth, no OA

    def test_no_pmcid_skips_oa_lookup(self, tmp_path: Path) -> None:
        called = []
        def stub(pmcid, cd):
            called.append(pmcid)
            return "https://example.com/x.pdf"
        ref = {
            "ids": {"pmcid": None, "doi": None, "arxiv_id": None,
                    "pmid": None, "openalex_id": None, "s2_id": None},
            "pdf_locations": [],
        }
        M._plan_walk(
            ref, allow_paywalled=False, cache_dir=tmp_path, oa_lookup_fn=stub,
        )
        assert called == []

    def test_oa_url_already_cataloged_deduped(self, tmp_path: Path) -> None:
        # If PR-D's enrichment somehow already produced the same OA
        # URL, the synthesized:pmc_oa candidate is dropped so we
        # don't walk it twice.
        oa_url = ("https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_pdf/"
                  "08/56/fnhum-08-00443.pdf")
        ref = {
            "ids": {"pmcid": "PMC4097944", "doi": None, "arxiv_id": None,
                    "pmid": None, "openalex_id": None, "s2_id": None},
            "pdf_locations": [_loc(oa_url, source="openalex")],
        }
        cands = M._plan_walk(
            ref, allow_paywalled=False, cache_dir=tmp_path,
            oa_lookup_fn=lambda pmcid, cd: oa_url,
        )
        urls = [c["url"] for c in cands]
        assert urls.count(oa_url) == 1
        sources = [c.get("source") for c in cands]
        # The kept entry is the cataloged one (openalex), not the
        # synthesized:pmc_oa.
        assert "pmc_oa" not in sources

    def test_no_ids_no_shortcuts(self) -> None:
        ref = {
            "ids": {"doi": None, "arxiv_id": None, "pmcid": None,
                    "pmid": None, "openalex_id": None, "s2_id": None},
            "pdf_locations": [_loc("https://repo.example.com/file.pdf",
                                   source="openalex")],
        }
        cands = M._plan_walk(ref, allow_paywalled=False)
        urls = [c["url"] for c in cands]
        assert urls == ["https://repo.example.com/file.pdf"]
