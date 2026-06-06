"""
test_analyze_failures.py — Unit tests for analyze_failures.py.

Pure fixture-driven.  No filesystem, no network.  Covers:

  - ``split_reason``                — handles compound reasons and
                                       semicolons inside parens.
  - ``normalize_reason_component``  — URL / byte / content-type-params
                                       / exception-message rules.
  - ``normalize_reason``            — compound join with ``" | "``.
  - ``reason_components``           — split + normalize each.
  - ``iter_failed_refs``            — yields only failure stamps; kind-isolated.
  - ``bucket_by_*``                 — counts and ref-id grouping.
  - ``format_markdown_report``      — three tables present, limit
                                       respected, empty input handled.
  - ``format_json_sidecar``         — structure shape.

End-to-end CLI behaviour (``main``) is exercised by the integration
test at the bottom (writes to a tmp dir).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from analyze_failures import (  # noqa: E402
    Bucket,
    Failure,
    bucket_by_pattern,
    bucket_by_reason_component,
    bucket_by_tried,
    format_json_sidecar,
    format_markdown_report,
    iter_failed_refs,
    main as analyze_failures_main,
    normalize_reason,
    normalize_reason_component,
    reason_components,
    split_reason,
)


# ---------------------------------------------------------------------------
# Catalog fixtures
# ---------------------------------------------------------------------------

def _ref_failure(doi: str | None, tried: list[str], reason: str) -> dict:
    return {
        "ids": {
            "doi": doi, "openalex_id": None, "pmid": None,
            "pmcid": None, "s2_id": None, "arxiv_id": None,
        },
        "local_artifacts": {
            "pdf": {
                "path": None,
                "last_attempt": "2026-06-01T10:00:00Z",
                "attempts": 1,
                "tried": list(tried),
                "reason": reason,
            },
        },
    }


def _ref_success(doi: str) -> dict:
    return {
        "ids": {"doi": doi},
        "local_artifacts": {
            "pdf": {
                "path": "HED-PDFs/foo.pdf",
                "source_url": "https://example.com",
                "source_type": "auto_openalex",
                "license": "cc-by",
                "acquired_on": "2026-06-01T10:00:00Z",
                "acquired_via": "auto",
            },
        },
    }


def _ref_no_artifacts(doi: str) -> dict:
    return {"ids": {"doi": doi}}


def _catalog(*refs: dict) -> tuple[dict, list]:
    procs = {"processes": [{"process_id": "hed_p1", "references": list(refs)}]}
    tasks: list = []
    return procs, tasks


# ---------------------------------------------------------------------------
# split_reason
# ---------------------------------------------------------------------------

class TestSplitReason:

    def test_plain_single(self) -> None:
        assert split_reason("no candidate locations") == ["no candidate locations"]

    def test_simple_compound(self) -> None:
        assert split_reason("openalex: HTTP 403; unpaywall: not PDF") == [
            "openalex: HTTP 403",
            "unpaywall: not PDF",
        ]

    def test_semicolon_inside_parens_is_preserved(self) -> None:
        assert split_reason("openalex: not PDF (text/html; charset=utf-8)") == [
            "openalex: not PDF (text/html; charset=utf-8)"
        ]

    def test_mixed_inside_and_outside_parens(self) -> None:
        assert split_reason(
            "openalex: not PDF (text/html; charset=utf-8); unpaywall: HTTP 403"
        ) == [
            "openalex: not PDF (text/html; charset=utf-8)",
            "unpaywall: HTTP 403",
        ]

    def test_empty(self) -> None:
        assert split_reason("") == []

    def test_only_whitespace(self) -> None:
        assert split_reason("   ") == []

    def test_trailing_semicolon_dropped(self) -> None:
        assert split_reason("a; b;") == ["a", "b"]

    def test_doubled_separator_dropped(self) -> None:
        assert split_reason("a;;b") == ["a", "b"]


# ---------------------------------------------------------------------------
# normalize_reason_component
# ---------------------------------------------------------------------------

class TestNormalizeReasonComponent:

    def test_lowercases(self) -> None:
        assert normalize_reason_component("HTTP 403") == "http 403"

    def test_strips_url(self) -> None:
        out = normalize_reason_component(
            "openalex: redirect to https://example.com/landing.html"
        )
        assert "<url>" in out
        assert "example.com" not in out

    def test_url_inside_parens_does_not_swallow_close(self) -> None:
        out = normalize_reason_component(
            "openalex: forwarded (target https://x.com/p) and stopped"
        )
        # The URL regex must not eat the trailing ')' — without that
        # safeguard the rest of the message would be lost.
        assert "<url>" in out
        assert "and stopped" in out

    def test_byte_count_collapsed(self) -> None:
        out = normalize_reason_component(
            "openalex: body exceeds max_bytes=52428800"
        )
        assert "=<n>" in out
        assert "52428800" not in out

    def test_short_numbers_not_collapsed(self) -> None:
        # 3 digits (HTTP status) must not match the bytes-regex.
        out = normalize_reason_component("openalex: HTTP 403")
        assert "403" in out

    def test_content_type_params_stripped(self) -> None:
        out = normalize_reason_component(
            "openalex: not PDF (text/html; charset=utf-8)"
        )
        assert "(text/html)" in out
        assert "charset" not in out

    def test_content_type_no_params_preserved(self) -> None:
        assert (
            normalize_reason_component("openalex: not PDF (text/html)")
            == "openalex: not pdf (text/html)"
        )

    def test_exception_message_collapsed(self) -> None:
        out = normalize_reason_component(
            "openalex: ConnectionError: connection refused on port 443"
        )
        assert "connectionerror" in out
        assert "port" not in out
        assert "refused" not in out

    def test_dotted_exception_name_collapsed(self) -> None:
        # ``\b`` matches between ``.`` and a word char, so qualified
        # exception names like ``requests.exceptions.ConnectionError``
        # still bucket cleanly on the type name.
        out = normalize_reason_component(
            "openalex: requests.exceptions.ConnectionError: refused"
        )
        # The exception regex matches the leaf type name; the prefix
        # remains in the string.  Either way "refused" must be gone.
        assert "refused" not in out
        assert "connectionerror" in out

    def test_empty(self) -> None:
        assert normalize_reason_component("") == ""
        assert normalize_reason_component("   ") == ""

    def test_runs_of_whitespace_collapsed(self) -> None:
        assert normalize_reason_component("a    b") == "a b"


# ---------------------------------------------------------------------------
# normalize_reason (compound)
# ---------------------------------------------------------------------------

class TestNormalizeReason:

    def test_compound_joins_with_pipe(self) -> None:
        assert (
            normalize_reason("openalex: HTTP 403; unpaywall: not PDF (text/html)")
            == "openalex: http 403 | unpaywall: not pdf (text/html)"
        )

    def test_compound_with_inside_paren_semicolon(self) -> None:
        assert (
            normalize_reason(
                "openalex: not PDF (text/html; charset=utf-8); unpaywall: HTTP 403"
            )
            == "openalex: not pdf (text/html) | unpaywall: http 403"
        )

    def test_single_component(self) -> None:
        assert normalize_reason("no candidate locations") == "no candidate locations"

    def test_empty(self) -> None:
        assert normalize_reason("") == ""


# ---------------------------------------------------------------------------
# reason_components
# ---------------------------------------------------------------------------

class TestReasonComponents:

    def test_splits_and_normalizes_each(self) -> None:
        assert reason_components(
            "openalex: HTTP 403; unpaywall: not PDF (text/html; charset=utf-8)"
        ) == [
            "openalex: http 403",
            "unpaywall: not pdf (text/html)",
        ]

    def test_empty(self) -> None:
        assert reason_components("") == []


# ---------------------------------------------------------------------------
# iter_failed_refs
# ---------------------------------------------------------------------------

class TestIterFailedRefs:

    def test_yields_failure_refs_only(self) -> None:
        procs, tasks = _catalog(
            _ref_failure("10.x/a", ["openalex"], "openalex: HTTP 403"),
            _ref_success("10.x/b"),
            _ref_no_artifacts("10.x/c"),
        )
        out = list(iter_failed_refs(procs, tasks, "pdf"))
        assert len(out) == 1
        assert out[0].doi == "10.x/a"

    def test_extracts_tried_as_tuple(self) -> None:
        procs, tasks = _catalog(
            _ref_failure("10.x/a", ["openalex", "unpaywall"], "some reason"),
        )
        f = next(iter_failed_refs(procs, tasks, "pdf"))
        assert f.tried == ("openalex", "unpaywall")
        assert isinstance(f.tried, tuple)

    def test_empty_tried_for_no_candidates(self) -> None:
        procs, tasks = _catalog(
            _ref_failure("10.x/a", [], "no candidate locations"),
        )
        f = next(iter_failed_refs(procs, tasks, "pdf"))
        assert f.tried == ()

    def test_walks_processes_and_tasks(self) -> None:
        procs = {"processes": [
            {"process_id": "p1", "references": [
                _ref_failure("10.x/p", ["openalex"], "x"),
            ]},
        ]}
        tasks = [
            {"hedtsk_id": "t1", "references": [
                _ref_failure("10.x/t", ["openalex"], "x"),
            ]},
        ]
        out = [(f.owner_id, f.ref_idx) for f in iter_failed_refs(procs, tasks, "pdf")]
        assert out == [("p1", 0), ("t1", 0)]

    def test_kind_isolated(self) -> None:
        # PDF success + Markdown failure on the same ref.
        ref = {
            "ids": {"doi": "10.x/a"},
            "local_artifacts": {
                "pdf": {"path": "HED-PDFs/foo.pdf"},
                "markdown": {
                    "path": None,
                    "reason": "pmc_bioc unavailable",
                    "tried": ["pmc_bioc"],
                    "last_attempt": "2026-06-01T10:00:00Z",
                    "attempts": 1,
                },
            },
        }
        procs = {"processes": [{"process_id": "p1", "references": [ref]}]}
        assert list(iter_failed_refs(procs, [], "pdf")) == []
        out_md = list(iter_failed_refs(procs, [], "markdown"))
        assert len(out_md) == 1
        assert out_md[0].tried == ("pmc_bioc",)

    def test_no_doi_ok(self) -> None:
        ref = _ref_failure(None, [], "no candidate locations")
        procs = {"processes": [{"process_id": "p1", "references": [ref]}]}
        f = next(iter_failed_refs(procs, [], "pdf"))
        assert f.doi == ""

    def test_skips_path_null_without_reason(self) -> None:
        # A block with path=None but no 'reason' key is not a real
        # failure stamp — could be a partial/legacy record.  Skip it.
        ref = {
            "ids": {"doi": "10.x/a"},
            "local_artifacts": {"pdf": {"path": None}},
        }
        procs = {"processes": [{"process_id": "p1", "references": [ref]}]}
        assert list(iter_failed_refs(procs, [], "pdf")) == []


# ---------------------------------------------------------------------------
# Bucketing
# ---------------------------------------------------------------------------

def _f(doi: str, tried: list[str], reason_raw: str) -> Failure:
    return Failure(
        owner_id="owner",
        ref_idx=0,
        doi=doi,
        tried=tuple(tried),
        reason_raw=reason_raw,
        reason_normalized=normalize_reason(reason_raw),
        components=reason_components(reason_raw),
    )


class TestBucketByTried:

    def test_counts_and_groups(self) -> None:
        fs = [
            _f("10.x/1", ["openalex"], "X"),
            _f("10.x/2", ["openalex"], "Y"),
            _f("10.x/3", [], "Z"),
        ]
        out = bucket_by_tried(fs)
        assert out["[openalex]"].count == 2
        assert out["[]"].count == 1

    def test_sample_dois_capped(self) -> None:
        fs = [_f(f"10.x/{i}", ["openalex"], "X") for i in range(10)]
        out = bucket_by_tried(fs)
        assert len(out["[openalex]"].sample_dois) == 3


class TestBucketByReasonComponent:

    def test_compound_reason_counts_each_component(self) -> None:
        fs = [
            _f("10.x/1", ["openalex", "unpaywall"],
               "openalex: HTTP 403; unpaywall: not PDF (text/html)"),
            _f("10.x/2", ["openalex"], "openalex: HTTP 403"),
        ]
        out = bucket_by_reason_component(fs)
        assert out["openalex: http 403"].count == 2
        assert out["unpaywall: not pdf (text/html)"].count == 1

    def test_empty_reason_bucketed_as_sentinel(self) -> None:
        fs = [_f("10.x/1", ["openalex"], "")]
        out = bucket_by_reason_component(fs)
        assert out["(empty)"].count == 1


class TestBucketByPattern:

    def test_distinct_tried_sets_distinct_keys(self) -> None:
        fs = [
            _f("10.x/1", ["openalex"], "openalex: HTTP 403"),
            _f("10.x/2", ["openalex", "unpaywall"], "openalex: HTTP 403"),
        ]
        out = bucket_by_pattern(fs)
        # Same reason, different tried sets -> two buckets.
        assert len(out) == 2

    def test_same_pattern_buckets_together(self) -> None:
        fs = [
            _f("10.x/1", ["openalex"], "openalex: HTTP 403"),
            _f("10.x/2", ["openalex"], "openalex: HTTP 403"),
        ]
        out = bucket_by_pattern(fs)
        assert len(out) == 1
        bucket = next(iter(out.values()))
        assert bucket.count == 2


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------

class TestFormatMarkdownReport:

    def test_three_tables_present(self) -> None:
        fs = [_f("10.x/1", ["openalex"], "openalex: HTTP 403")]
        md = format_markdown_report(fs, "pdf", limit=10, when="2026-06-01")
        assert "## By `tried` set" in md
        assert "## By normalized reason component" in md
        assert "## By (tried, normalized reason) pattern" in md
        assert "Total failed refs: **1**" in md
        assert "2026-06-01" in md

    def test_limit_respected_with_overflow_row(self) -> None:
        fs = [
            _f(f"10.x/{i}", [f"src{i}"], f"src{i}: some-reason-{i}")
            for i in range(30)
        ]
        md = format_markdown_report(fs, "pdf", limit=5, when="2026-06-01")
        assert "25 more buckets" in md

    def test_no_overflow_row_when_below_limit(self) -> None:
        fs = [_f("10.x/1", ["openalex"], "openalex: HTTP 403")]
        md = format_markdown_report(fs, "pdf", limit=10, when="2026-06-01")
        assert "more buckets" not in md

    def test_empty_failures_handled(self) -> None:
        md = format_markdown_report([], "pdf", limit=10, when="2026-06-01")
        assert "Total failed refs: **0**" in md
        # Tables present but empty (only the header rows).
        assert "## By `tried` set" in md


class TestFormatJSONSidecar:

    def test_structure(self) -> None:
        fs = [_f("10.x/1", ["openalex"], "openalex: HTTP 403")]
        sidecar = json.loads(format_json_sidecar(fs, "pdf", when="2026-06-01"))
        assert sidecar["kind"] == "pdf"
        assert sidecar["when"] == "2026-06-01"
        assert sidecar["total"] == 1
        for key in ("by_tried", "by_component", "by_pattern"):
            assert key in sidecar
            assert sidecar[key][0]["count"] == 1
        # ref_ids carry the full list, sample_dois capped at 3.
        assert sidecar["by_tried"][0]["ref_ids"] == ["owner#0"]


# ---------------------------------------------------------------------------
# End-to-end CLI smoke test
# ---------------------------------------------------------------------------

class TestCLI:

    def test_writes_md_and_json(self, tmp_path: Path) -> None:
        """End-to-end: stage a minimal catalog, run main(), check files."""
        procs = {"processes": [{"process_id": "p1", "references": [
            _ref_failure("10.x/a", ["openalex"], "openalex: HTTP 403"),
            _ref_failure("10.x/b", [], "no candidate locations"),
            _ref_success("10.x/c"),
        ]}]}
        tasks: list = []
        (tmp_path / "process_details.json").write_text(
            json.dumps(procs), encoding="utf-8"
        )
        (tmp_path / "task_details.json").write_text(
            json.dumps(tasks), encoding="utf-8"
        )

        rc = analyze_failures_main([
            "--kind", "pdf",
            "--workspace", str(tmp_path),
            "--output-dir", "outputs/analysis",
        ])
        assert rc == 0

        out_dir = tmp_path / "outputs" / "analysis"
        md_files = list(out_dir.glob("failures_pdf_*.md"))
        json_files = list(out_dir.glob("failures_pdf_*.json"))
        assert len(md_files) == 1
        assert len(json_files) == 1

        sidecar = json.loads(json_files[0].read_text(encoding="utf-8"))
        assert sidecar["total"] == 2  # only failures, not the success ref

    def test_no_failures_exits_1(self, tmp_path: Path) -> None:
        procs = {"processes": [{"process_id": "p1", "references": [
            _ref_success("10.x/a"),
        ]}]}
        (tmp_path / "process_details.json").write_text(
            json.dumps(procs), encoding="utf-8"
        )
        (tmp_path / "task_details.json").write_text("[]", encoding="utf-8")

        rc = analyze_failures_main([
            "--kind", "pdf", "--workspace", str(tmp_path),
        ])
        assert rc == 1

    def test_missing_catalog_exits_2(self, tmp_path: Path) -> None:
        rc = analyze_failures_main([
            "--kind", "pdf", "--workspace", str(tmp_path),
        ])
        assert rc == 2
