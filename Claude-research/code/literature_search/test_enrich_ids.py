"""
test_enrich_ids.py — Unit tests for enrich_ids.py.

Pure fixture-driven.  No filesystem, no network.  Covers the four
extract/merge/apply primitives.  The driver `main()` is not tested
here because its only non-trivial logic is JSON I/O against the
catalog files (covered by the dry-run/wet-run sequence in the
execution plan).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make the sibling enrich_ids module importable when pytest runs from
# anywhere under the repo.
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from enrich_ids import (  # noqa: E402
    apply_to_ref,
    extract_ids_from_openalex,
    extract_ids_from_s2,
    merge_id_sets,
)


# ---------------------------------------------------------------------------
# Fixtures (paper-shaped, not necessarily real)
# ---------------------------------------------------------------------------

OPENALEX_FULL = {
    "id":  "https://openalex.org/W2003876547",
    "doi": "https://doi.org/10.3389/fnhum.2014.00443",
    "ids": {
        "openalex": "https://openalex.org/W2003876547",
        "doi":      "https://doi.org/10.3389/fnhum.2014.00443",
        "pmid":     "https://pubmed.ncbi.nlm.nih.gov/25076880",
        "pmcid":    "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4097944",
    },
}

OPENALEX_NO_PMCID = {
    "id":  "https://openalex.org/W17225164",
    "ids": {"pmid": "https://pubmed.ncbi.nlm.nih.gov/17225164"},
}

OPENALEX_BARE = {
    "id": "https://openalex.org/W123",
    # no ids block
}

S2_FULL = {
    "paperId": "fedcba9876543210",
    "externalIds": {
        "DOI":           "10.3389/fnhum.2014.00443",
        "PubMed":        "25076880",
        "PubMedCentral": "4097944",           # bare digits — must be PMC-prefixed
        "ArXiv":         "1234.5678",
        "MAG":           "2003876547",
    },
}

S2_PREFIXED_PMCID = {
    "paperId": "p1",
    "externalIds": {"PubMedCentral": "PMC1234567"},
}

S2_MINIMAL = {
    "paperId": "p2",
    "externalIds": {},
}


# ---------------------------------------------------------------------------
# extract_ids_from_openalex
# ---------------------------------------------------------------------------

def test_extract_openalex_ids_full() -> None:
    got = extract_ids_from_openalex(OPENALEX_FULL)
    assert got == {
        "openalex_id": "W2003876547",
        "pmid":        "25076880",
        "pmcid":       "PMC4097944",
    }


def test_extract_openalex_ids_partial() -> None:
    got = extract_ids_from_openalex(OPENALEX_NO_PMCID)
    assert got == {
        "openalex_id": "W17225164",
        "pmid":        "17225164",
    }


def test_extract_openalex_ids_minimal() -> None:
    got = extract_ids_from_openalex(OPENALEX_BARE)
    assert got == {"openalex_id": "W123"}


def test_extract_openalex_ids_empty_or_none() -> None:
    assert extract_ids_from_openalex(None) == {}
    assert extract_ids_from_openalex({}) == {}


# ---------------------------------------------------------------------------
# extract_ids_from_s2
# ---------------------------------------------------------------------------

def test_extract_s2_ids_full() -> None:
    got = extract_ids_from_s2(S2_FULL)
    assert got == {
        "s2_id":    "fedcba9876543210",
        "pmid":     "25076880",
        "pmcid":    "PMC4097944",    # PMC-prefixed
        "arxiv_id": "1234.5678",
    }


def test_extract_s2_ids_already_prefixed_pmcid() -> None:
    got = extract_ids_from_s2(S2_PREFIXED_PMCID)
    assert got == {"s2_id": "p1", "pmcid": "PMC1234567"}


def test_extract_s2_ids_minimal() -> None:
    got = extract_ids_from_s2(S2_MINIMAL)
    assert got == {"s2_id": "p2"}


def test_extract_s2_ids_empty_or_none() -> None:
    assert extract_ids_from_s2(None) == {}
    assert extract_ids_from_s2({}) == {}


# ---------------------------------------------------------------------------
# merge_id_sets
# ---------------------------------------------------------------------------

def test_merge_openalex_wins_pmid_pmcid() -> None:
    oa = {"openalex_id": "W1", "pmid": "111", "pmcid": "PMC222"}
    s2 = {"s2_id": "p1", "pmid": "999", "pmcid": "PMC888", "arxiv_id": "1.2"}
    got = merge_id_sets(oa, s2)
    assert got == {
        "openalex_id": "W1",
        "pmid":        "111",      # OA wins
        "pmcid":       "PMC222",   # OA wins
        "s2_id":       "p1",
        "arxiv_id":    "1.2",
    }


def test_merge_s2_fills_when_openalex_silent() -> None:
    oa = {"openalex_id": "W1", "pmid": "111"}            # no pmcid
    s2 = {"s2_id": "p1", "pmcid": "PMC222", "arxiv_id": "1.2"}
    got = merge_id_sets(oa, s2)
    assert got["pmcid"] == "PMC222"
    assert got["arxiv_id"] == "1.2"
    assert got["openalex_id"] == "W1"
    assert got["pmid"] == "111"


# ---------------------------------------------------------------------------
# apply_to_ref
# ---------------------------------------------------------------------------

def _empty_ids_ref() -> dict:
    return {"ids": {
        "doi": "10.x/y", "openalex_id": None, "pmid": None,
        "pmcid": None, "s2_id": None, "arxiv_id": None,
    }}


def test_apply_fills_all_null_slots() -> None:
    ref = _empty_ids_ref()
    cands = {"openalex_id": "W1", "pmid": "111", "pmcid": "PMC222",
             "s2_id": "p1", "arxiv_id": "1.2"}
    n_filled, conflicts = apply_to_ref(ref, cands)
    assert n_filled == 5
    assert conflicts == []
    assert ref["ids"]["openalex_id"] == "W1"
    assert ref["ids"]["pmcid"] == "PMC222"


def test_apply_never_overwrites_existing() -> None:
    ref = _empty_ids_ref()
    ref["ids"]["pmid"] = "preexisting"
    cands = {"openalex_id": "W1", "pmid": "fresh", "pmcid": "PMC222"}
    n_filled, conflicts = apply_to_ref(ref, cands)
    assert ref["ids"]["pmid"] == "preexisting"   # untouched
    assert ref["ids"]["openalex_id"] == "W1"     # null slot filled
    assert ref["ids"]["pmcid"] == "PMC222"
    assert n_filled == 2
    assert conflicts == [("pmid", "preexisting", "fresh")]


def test_apply_idempotent_on_already_filled_ref() -> None:
    ref = _empty_ids_ref()
    ref["ids"].update({
        "openalex_id": "W1", "pmid": "111", "pmcid": "PMC222",
        "s2_id": "p1", "arxiv_id": "1.2",
    })
    cands = {"openalex_id": "W1", "pmid": "111", "pmcid": "PMC222",
             "s2_id": "p1", "arxiv_id": "1.2"}
    n_filled, conflicts = apply_to_ref(ref, cands)
    assert n_filled == 0
    assert conflicts == []
    # Ref is unchanged.
    assert ref["ids"]["openalex_id"] == "W1"


def test_apply_creates_ids_block_if_missing() -> None:
    # Defensive: a ref with no ids block at all (shouldn't happen post-PR-A,
    # but the schema doesn't strictly require ids to exist).
    ref = {}
    n_filled, conflicts = apply_to_ref(ref, {"openalex_id": "W1"})
    assert n_filled == 1
    assert ref["ids"]["openalex_id"] == "W1"
    assert conflicts == []
