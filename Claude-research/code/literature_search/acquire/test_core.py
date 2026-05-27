"""
test_core.py — Unit tests for acquire/core.py.

Pure fixture-driven.  No filesystem, no network.  Covers iter_refs
(catalog walk), should_skip / has_recorded_failure (idempotency
predicates), and record_success / record_failure (mutation
behaviour).

`resolve_cache_dir` is a one-line copy of the enrich_pdf_locations.py
helper and is covered (with the same logic) by that module's
exercise; not duplicated here.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make ``core.py`` importable when pytest runs the file directly.
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from core import (  # noqa: E402
    has_recorded_failure,
    iter_refs,
    record_failure,
    record_success,
    should_skip,
)


# ---------------------------------------------------------------------------
# Catalog fixtures (paper-shaped; not real data)
# ---------------------------------------------------------------------------

def _ref(doi: str | None) -> dict:
    """Build a reference dict with a populated ids block."""
    return {"ids": {
        "doi": doi, "openalex_id": None, "pmid": None,
        "pmcid": None, "s2_id": None, "arxiv_id": None,
    }}


def _processes(*pairs: tuple[str, list[dict]]) -> dict:
    """Build a processes catalog: each pair is (process_id, [refs])."""
    return {"processes": [
        {"process_id": pid, "references": refs} for pid, refs in pairs
    ]}


def _tasks(*pairs: tuple[str, list[dict]]) -> list:
    """Build a tasks catalog: each pair is (hedtsk_id, [refs])."""
    return [{"hedtsk_id": tid, "references": refs} for tid, refs in pairs]


# ---------------------------------------------------------------------------
# iter_refs
# ---------------------------------------------------------------------------

class TestIterRefs:

    def test_full_mode_yields_every_ref(self) -> None:
        procs = _processes(
            ("hed_p1", [_ref("10.x/1"), _ref("10.x/2")]),
            ("hed_p2", [_ref("10.x/3")]),
        )
        tasks = _tasks(("hedtsk_t1", [_ref("10.x/4")]))
        got = list(iter_refs(procs, tasks, mode="full"))
        assert [(o, i) for o, i, _ in got] == [
            ("hed_p1", 0), ("hed_p1", 1), ("hed_p2", 0), ("hedtsk_t1", 0),
        ]

    def test_single_mode_filters_by_owner_id(self) -> None:
        procs = _processes(
            ("hed_p1", [_ref("10.x/1")]),
            ("hed_p2", [_ref("10.x/2")]),
        )
        tasks = _tasks(("hedtsk_t1", [_ref("10.x/3")]))
        got = list(iter_refs(procs, tasks, mode="single", ids=["hed_p2", "hedtsk_t1"]))
        owners = [o for o, _, _ in got]
        assert owners == ["hed_p2", "hedtsk_t1"]

    def test_poc_mode_filters_by_doi(self) -> None:
        procs = _processes(
            ("hed_p1", [_ref("10.x/keep"), _ref("10.x/drop")]),
            ("hed_p2", [_ref("10.x/keep2")]),
        )
        tasks = _tasks(("hedtsk_t1", [_ref("10.x/drop2")]))
        got = list(iter_refs(
            procs, tasks, mode="poc",
            poc_dois=("10.x/keep", "10.x/keep2"),
        ))
        dois = [(r["ids"] or {}).get("doi") for _, _, r in got]
        assert sorted(dois) == ["10.x/keep", "10.x/keep2"]

    def test_poc_mode_case_insensitive(self) -> None:
        # DOIs are case-folded on both sides of the comparison.
        procs = _processes(("hed_p1", [_ref("10.X/UPPER")]))
        got = list(iter_refs(procs, [], mode="poc", poc_dois=("10.x/upper",)))
        assert len(got) == 1

    def test_unknown_mode_raises(self) -> None:
        try:
            list(iter_refs({"processes": []}, [], mode="bogus"))
        except ValueError as exc:
            assert "bogus" in str(exc)
        else:
            raise AssertionError("expected ValueError")

    def test_empty_catalogs(self) -> None:
        assert list(iter_refs({}, [], mode="full")) == []
        assert list(iter_refs({"processes": []}, [], mode="full")) == []


# ---------------------------------------------------------------------------
# Idempotency predicates
# ---------------------------------------------------------------------------

class TestShouldSkip:

    def test_skip_when_artifact_path_set(self) -> None:
        ref = {"local_artifacts": {"pdf": {"path": "HED-PDFs/Foo.pdf"}}}
        assert should_skip(ref, "pdf") is True

    def test_dont_skip_when_no_local_artifacts(self) -> None:
        assert should_skip({}, "pdf") is False
        assert should_skip({"local_artifacts": {}}, "pdf") is False

    def test_dont_skip_on_failure_record(self) -> None:
        ref = {"local_artifacts": {"pdf": {
            "path": None, "last_attempt": "2026-01-01T00:00:00Z", "attempts": 1,
        }}}
        assert should_skip(ref, "pdf") is False

    def test_dont_skip_on_empty_path_string(self) -> None:
        ref = {"local_artifacts": {"pdf": {"path": "  "}}}
        assert should_skip(ref, "pdf") is False

    def test_force_overrides(self) -> None:
        ref = {"local_artifacts": {"pdf": {"path": "HED-PDFs/Foo.pdf"}}}
        assert should_skip(ref, "pdf", force=True) is False

    def test_kind_isolation(self) -> None:
        # pdf set, markdown unset: only the relevant kind is checked.
        ref = {"local_artifacts": {"pdf": {"path": "HED-PDFs/Foo.pdf"}}}
        assert should_skip(ref, "pdf") is True
        assert should_skip(ref, "markdown") is False


class TestHasRecordedFailure:

    def test_true_on_failure_record(self) -> None:
        ref = {"local_artifacts": {"pdf": {
            "path": None, "last_attempt": "2026-01-01T00:00:00Z",
        }}}
        assert has_recorded_failure(ref, "pdf") is True

    def test_false_on_success_record(self) -> None:
        ref = {"local_artifacts": {"pdf": {"path": "HED-PDFs/Foo.pdf"}}}
        assert has_recorded_failure(ref, "pdf") is False

    def test_false_when_block_absent(self) -> None:
        assert has_recorded_failure({}, "pdf") is False


# ---------------------------------------------------------------------------
# Record success
# ---------------------------------------------------------------------------

class TestRecordSuccess:

    def test_writes_all_fields(self) -> None:
        ref: dict = {}
        record_success(
            ref, "pdf",
            path="HED-PDFs/Smith_2008_X_abcd1234.pdf",
            source_url="https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1/",
            source_type="pmc",
            license="cc-by",
            when="2026-05-27T12:00:00Z",
        )
        pdf = ref["local_artifacts"]["pdf"]
        assert pdf["path"]         == "HED-PDFs/Smith_2008_X_abcd1234.pdf"
        assert pdf["source_url"]   == "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1/"
        assert pdf["source_type"]  == "pmc"
        assert pdf["license"]      == "cc-by"
        assert pdf["acquired_on"]  == "2026-05-27T12:00:00Z"
        assert pdf["acquired_via"] == "auto"
        assert "converter" not in pdf

    def test_writes_converter_when_provided(self) -> None:
        ref: dict = {}
        record_success(
            ref, "markdown",
            path="x.md", source_url="x", source_type="pmc_bioc",
            license="cc-by", converter="pmc_bioc",
            when="2026-05-27T12:00:00Z",
        )
        assert ref["local_artifacts"]["markdown"]["converter"] == "pmc_bioc"

    def test_preserves_existing_acquired_on(self) -> None:
        ref = {"local_artifacts": {"pdf": {"acquired_on": "2020-01-01T00:00:00Z"}}}
        record_success(
            ref, "pdf",
            path="x.pdf", source_url="x", source_type="pmc", license="cc-by",
            when="2026-05-27T12:00:00Z",
        )
        # Original timestamp survived; new write happened.
        assert ref["local_artifacts"]["pdf"]["acquired_on"] == "2020-01-01T00:00:00Z"
        assert ref["local_artifacts"]["pdf"]["path"]        == "x.pdf"

    def test_clears_failure_fields(self) -> None:
        ref = {"local_artifacts": {"pdf": {
            "path": None,
            "last_attempt": "2026-01-01T00:00:00Z",
            "attempts":     3,
            "tried":        ["pmc", "openalex"],
            "reason":       "all sources returned non-OA",
        }}}
        record_success(
            ref, "pdf",
            path="HED-PDFs/Foo.pdf", source_url="x", source_type="pmc",
            license="cc-by", when="2026-05-27T12:00:00Z",
        )
        pdf = ref["local_artifacts"]["pdf"]
        assert pdf["path"] == "HED-PDFs/Foo.pdf"
        assert "last_attempt" not in pdf
        assert "attempts"     not in pdf
        assert "tried"        not in pdf
        assert "reason"       not in pdf


# ---------------------------------------------------------------------------
# Record failure
# ---------------------------------------------------------------------------

class TestRecordFailure:

    def test_first_failure_writes_attempts_one(self) -> None:
        ref: dict = {}
        record_failure(
            ref, "pdf",
            tried=["pmc", "openalex"],
            reason="all sources returned non-OA",
            when="2026-05-27T12:00:00Z",
        )
        pdf = ref["local_artifacts"]["pdf"]
        assert pdf["path"]         is None
        assert pdf["last_attempt"] == "2026-05-27T12:00:00Z"
        assert pdf["attempts"]     == 1
        assert pdf["tried"]        == ["pmc", "openalex"]
        assert pdf["reason"]       == "all sources returned non-OA"

    def test_subsequent_failure_increments_attempts(self) -> None:
        ref = {"local_artifacts": {"pdf": {
            "path": None,
            "last_attempt": "2026-01-01T00:00:00Z",
            "attempts": 2,
            "tried":    ["pmc"],
            "reason":   "earlier reason",
        }}}
        record_failure(
            ref, "pdf",
            tried=["pmc", "unpaywall"],
            reason="still failing",
            when="2026-05-27T12:00:00Z",
        )
        pdf = ref["local_artifacts"]["pdf"]
        assert pdf["attempts"]     == 3
        assert pdf["last_attempt"] == "2026-05-27T12:00:00Z"
        assert pdf["tried"]        == ["pmc", "unpaywall"]
        assert pdf["reason"]       == "still failing"

    def test_kind_isolation(self) -> None:
        # Recording a markdown failure does not touch the pdf block.
        ref = {"local_artifacts": {"pdf": {"path": "HED-PDFs/Foo.pdf"}}}
        record_failure(
            ref, "markdown",
            tried=["pmc_bioc"], reason="not in OA subset",
            when="2026-05-27T12:00:00Z",
        )
        assert ref["local_artifacts"]["pdf"]["path"] == "HED-PDFs/Foo.pdf"
        assert ref["local_artifacts"]["markdown"]["path"] is None
