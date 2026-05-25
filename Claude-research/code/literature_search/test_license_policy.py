"""
Unit tests for license_policy.

Pure-function tests; no I/O.  Run from the workspace root:

    pytest code/literature_search/test_license_policy.py -v

Or from the repo root via the project venv:

    pytest Claude-research/code/literature_search/test_license_policy.py -v

These tests pin the normalisation behaviour and the publishability
policy.  Changes to ``PUBLISHABLE_LICENSES`` or ``_EXPLICIT_ALIASES``
in license_policy.py should be accompanied by test updates here, so
the policy is auditable from the test suite.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make the sibling modules importable without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest

from license_policy import (
    KNOWN_LICENSES,
    PUBLISHABLE_LICENSES,
    classify_strings,
    is_intentionally_unknown,
    is_publishable,
    normalise_license,
)


# ---------------------------------------------------------------------------
# Basic mapping
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw, expected",
    [
        # Direct hits
        ("cc-by",        "cc-by"),
        ("cc-by-sa",     "cc-by-sa"),
        ("cc-by-nc",     "cc-by-nc"),
        ("cc-by-nc-sa",  "cc-by-nc-sa"),
        ("cc-by-nd",     "cc-by-nd"),
        ("cc-by-nc-nd",  "cc-by-nc-nd"),
        ("cc0",          "cc0"),
        ("public-domain", "public-domain"),
        ("proprietary",   "proprietary"),
        ("unknown",       "unknown"),
        # Case-insensitive
        ("CC-BY",        "cc-by"),
        ("Cc-By-NC",     "cc-by-nc"),
        ("CC0",          "cc0"),
        # Whitespace as separator
        ("cc by",        "cc-by"),
        ("CC BY",        "cc-by"),
        ("cc  by",       "cc-by"),
        ("public domain", "public-domain"),
        # Underscore as separator
        ("cc_by",        "cc-by"),
        ("cc_by_nc_nd",  "cc-by-nc-nd"),
        # Repeated hyphens collapse
        ("cc--by",       "cc-by"),
        ("cc---by",      "cc-by"),
    ],
)
def test_normalise_basic(raw: str, expected: str) -> None:
    assert normalise_license(raw) == expected


# ---------------------------------------------------------------------------
# Version-suffix stripping
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw, expected",
    [
        # CC family with versions
        ("cc-by-4.0",       "cc-by"),
        ("cc-by 4.0",       "cc-by"),
        ("CC-BY 4.0",       "cc-by"),
        ("cc-by-3.0",       "cc-by"),
        ("cc-by-1.0",       "cc-by"),
        ("CC-BY-NC-ND-4.0", "cc-by-nc-nd"),
        ("cc-by-nc-nd 4.0", "cc-by-nc-nd"),
        ("cc-by-sa-4.0",    "cc-by-sa"),
        # Two-component versions
        ("cc-by-v4",        "cc-by"),
        ("cc-by-v4.0",      "cc-by"),
        # No version, just hyphens
        ("cc-by",           "cc-by"),
        ("cc-by-nc",        "cc-by-nc"),
    ],
)
def test_normalise_version_suffix(raw: str, expected: str) -> None:
    assert normalise_license(raw) == expected


# ---------------------------------------------------------------------------
# Explicit aliases (publisher-specific tags, abbreviations)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw, expected",
    [
        # Public-domain aliases
        ("pd",                 "public-domain"),
        ("PD",                 "public-domain"),
        ("publicdomain",       "public-domain"),
        # CC0 aliases
        ("cc-zero",            "cc0"),
        ("CC-ZERO",            "cc0"),
        ("cc-0",               "cc0"),
        # Publisher-specific tags → proprietary
        ("publisher-specific-oa",  "proprietary"),
        ("publisher-specific",     "proprietary"),
        ("acs-specific-tdm",       "proprietary"),
        ("elsevier-specific-oa",   "proprietary"),
        # Unpaywall's catch-all → unknown (deliberate)
        ("other-oa",               "unknown"),
    ],
)
def test_normalise_explicit_aliases(raw: str, expected: str) -> None:
    assert normalise_license(raw) == expected


# ---------------------------------------------------------------------------
# Falsy / missing / unrecognised
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw",
    [
        None,
        "",
        "   ",
        "null",
        "NULL",
        "none",
        "N/A",
        "n/a",
        "na",
        "random nonsense",
        "some-fake-licence-string",
        12345,                # non-string
        [],                   # non-string
        {"x": 1},             # non-string
    ],
)
def test_normalise_unknown_or_missing(raw: object) -> None:
    assert normalise_license(raw) == "unknown"


# ---------------------------------------------------------------------------
# Predicate
# ---------------------------------------------------------------------------

def test_publishable_allowlist() -> None:
    """The publishable set is exactly the five allowlist members."""
    assert PUBLISHABLE_LICENSES == frozenset({
        "cc-by", "cc-by-sa", "cc0", "public-domain", "mit"
    })


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("cc-by",         True),
        ("cc-by-sa",      True),
        ("cc0",           True),
        ("public-domain", True),
        ("mit",            True),
        ("MIT",            True),
        # CC-BY-NC family deliberately excluded (per D8)
        ("cc-by-nc",       False),
        ("cc-by-nc-sa",    False),
        ("cc-by-nd",       False),
        ("cc-by-nc-nd",    False),
        # Proprietary / unknown
        ("proprietary",    False),
        ("unknown",        False),
        # Versioned forms still publish via normalisation
        ("CC-BY 4.0",      True),
        ("cc-by-4.0",      True),
        # Missing / non-string
        (None,             False),
        ("",               False),
        (12345,            False),
    ],
)
def test_is_publishable(raw: object, expected: bool) -> None:
    assert is_publishable(raw) is expected


# ---------------------------------------------------------------------------
# Bulk classification
# ---------------------------------------------------------------------------

def test_classify_strings_buckets_correctly() -> None:
    result = classify_strings([
        "cc-by",
        "CC-BY 4.0",
        "cc-by-nc",
        "publisher-specific-oa",
        "x-fake",
        None,
        "",
        "cc0",
        "cc-by",          # duplicate; should not appear twice in the bucket
    ])
    assert "cc-by" in result
    # Duplicate exact-match input is deduplicated within its bucket.
    assert result["cc-by"].count("cc-by") == 1
    # Case-variant ends up in the same bucket but is recorded separately.
    assert "CC-BY 4.0" in result["cc-by"]
    assert "cc-by-nc" in result["cc-by-nc"]
    assert "publisher-specific-oa" in result["proprietary"]
    assert "x-fake" in result["unknown"]


def test_classify_strings_handles_non_strings() -> None:
    """Non-string inputs map to ``unknown`` and are recorded as their repr."""
    result = classify_strings([12345, None, ["nested"]])
    assert "unknown" in result
    assert "12345" in result["unknown"]
    assert "None" in result["unknown"]


# ---------------------------------------------------------------------------
# CC no-separator preprocessing
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw, expected",
    [
        ("ccby",       "cc-by"),
        ("CCBY",       "cc-by"),         # case-insensitive
        ("ccbysa",     "cc-by-sa"),
        ("ccbync",     "cc-by-nc"),
        ("ccbynd",     "cc-by-nd"),
        ("ccbyncsa",   "cc-by-nc-sa"),
        ("ccbyncnd",   "cc-by-nc-nd"),
        ("CCBYNCND",   "cc-by-nc-nd"),
        # The regex still works in combination with a version suffix.
        ("ccby 4.0",   "cc-by"),
        # Non-matches survive — these don't shortcut the alias / KNOWN
        # path, so they should still bucket as unknown.
        ("cc",         "unknown"),       # "by" is required
        ("ccsa",       "unknown"),       # "by" must come first
        ("xxby",       "unknown"),       # only "cc" prefix matches
    ],
)
def test_normalise_cc_no_separator(raw: str, expected: str) -> None:
    assert normalise_license(raw) == expected


# ---------------------------------------------------------------------------
# Comma-annotation strip
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw, expected",
    [
        # The motivating case from a real enrichment run.
        ("publisher-specific, author manuscript",  "proprietary"),
        # Other plausible compound forms.
        ("publisher-specific, published version",  "proprietary"),
        ("cc-by, version 4.0",                     "cc-by"),
        ("cc-by-nc, submitted version",            "cc-by-nc"),
        # Edge: only a comma is left after preprocessing.
        (", just an annotation",                   "unknown"),
        # Trailing comma without an annotation.
        ("cc-by,",                                 "cc-by"),
    ],
)
def test_normalise_comma_annotation_strip(raw: str, expected: str) -> None:
    assert normalise_license(raw) == expected


# ---------------------------------------------------------------------------
# MIT licence
# ---------------------------------------------------------------------------

def test_mit_known_and_publishable() -> None:
    """MIT is tracked as a distinct licence and is publishable.

    Decision 2026-05-23: MIT permits redistribution with attribution
    + licence-text preservation, same obligation as CC-BY.  See
    ``.status/decision_2026-05-23_mit_publishable.md``.
    """
    assert "mit" in KNOWN_LICENSES
    assert "mit" in PUBLISHABLE_LICENSES
    assert normalise_license("MIT") == "mit"
    assert normalise_license("mit") == "mit"
    assert is_publishable("MIT") is True


# ---------------------------------------------------------------------------
# Intentional-unknown predicate
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw, expected",
    [
        # Strings explicitly aliased to "unknown" → True.
        ("other-oa",     True),
        ("OTHER-OA",     True),         # case-insensitive
        ("other_oa",     True),         # underscore separator
        ("other-oa 4.0", True),         # tolerated version suffix
        # Strings that bucket as unknown via the fallthrough → False.
        ("x-fake",       False),
        ("",             False),
        (None,           False),
        ("null",         False),
        (12345,          False),
        # Strings classified as something else entirely → False.
        ("cc-by",                  False),
        ("publisher-specific-oa",  False),  # aliased to "proprietary", not "unknown"
        ("proprietary",            False),
    ],
)
def test_is_intentionally_unknown(raw: object, expected: bool) -> None:
    assert is_intentionally_unknown(raw) is expected


def test_intentional_unknowns_actually_bucket_as_unknown() -> None:
    """Sanity: every intentional-unknown raw string normalises to 'unknown'."""
    for raw in ("other-oa", "OTHER-OA", "other_oa", "other-oa 4.0"):
        assert normalise_license(raw) == "unknown"


# ---------------------------------------------------------------------------
# Round-trip invariants
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("known", sorted(KNOWN_LICENSES))
def test_known_licences_are_self_normalising(known: str) -> None:
    """Every member of KNOWN_LICENSES survives normalise_license unchanged."""
    assert normalise_license(known) == known


def test_publishable_subset_of_known() -> None:
    assert PUBLISHABLE_LICENSES.issubset(KNOWN_LICENSES)
