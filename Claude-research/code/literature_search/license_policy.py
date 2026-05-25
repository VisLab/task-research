"""
license_policy.py — Licence normalisation and redistribution policy.

Three concerns in one module:

1.  Map raw licence strings from OpenAlex / Unpaywall / Semantic Scholar
    responses into a small SPDX-style vocabulary
    (``normalise_license``).
2.  Decide whether a given (normalised) licence permits redistribution
    — i.e., whether a Markdown derived from a PDF under that licence
    can land in the committed ``HED-Markdown-public/`` directory
    (``is_publishable``, ``PUBLISHABLE_LICENSES``).
3.  Surface unknown licence strings encountered during enrichment so a
    human can review and decide whether to extend the alias table
    (``classify_strings`` returns the unknown bucket separately).

Pure functions; no I/O.  This is the only module that owns the
licence vocabulary and the publishability predicate — change the
policy here, re-derive ``is_publishable`` flags downstream.

Policy as of 2026-05-19 (see .status/plan_2026-05-19_rec1_v2.md §10
decision 8):

  PUBLISHABLE_LICENSES = {cc-by, cc-by-sa, cc0, public-domain}

  CC-BY-NC family is deliberately excluded by default.  The boundary
  between "non-commercial use" and "open redistribution" is contested,
  so any inclusion of CC-BY-NC content requires a per-case override
  recorded in .status/license_overrides.md.
"""

from __future__ import annotations

import re
from typing import Iterable


__all__ = [
    "KNOWN_LICENSES",
    "PUBLISHABLE_LICENSES",
    "normalise_license",
    "is_publishable",
    "is_intentionally_unknown",
    "classify_strings",
]


# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------

#: The full set of normalised licence values.  ``unknown`` is the
#: sentinel for "we could not classify the raw string" — distinct from
#: ``proprietary`` ("the bytes are © the publisher, no redistribution").
#:
#: ``mit`` is included because OpenAlex / Semantic Scholar occasionally
#: emit it for papers (rare, but real — some F1000 / Wellcome Open
#: Research workflows; sometimes for code/data repositories associated
#: with a paper).  Permitted in ``PUBLISHABLE_LICENSES`` because the
#: MIT licence permits redistribution with attribution + licence-text
#: preservation, which is the same obligation CC-BY imposes (decision
#: 2026-05-23; see ``.status/decision_2026-05-23_mit_publishable.md``).
KNOWN_LICENSES: frozenset[str] = frozenset({
    "cc-by",
    "cc-by-sa",
    "cc-by-nc",
    "cc-by-nc-sa",
    "cc-by-nd",
    "cc-by-nc-nd",
    "cc0",
    "public-domain",
    "mit",
    "proprietary",
    "unknown",
})


#: Licences whose terms permit re-hosting derived artifacts (e.g. a
#: PDF->Markdown conversion) on a public GitHub repository.
#:
#: CC-BY-NC family is **not** included; HED's downstream uses are
#: not unambiguously non-commercial, and the contested boundary is
#: not worth automating away.  Override per-case if and when it
#: matters (see .status/license_overrides.md).
#:
#: ``mit`` IS included as of 2026-05-23.  The MIT licence permits
#: redistribution with copyright-notice + licence-text preservation;
#: the publish step must include both alongside the Markdown.  This
#: is the same attribution mechanism CC-BY needs, so no new policy
#: machinery is required.  See
#: ``.status/decision_2026-05-23_mit_publishable.md``.
PUBLISHABLE_LICENSES: frozenset[str] = frozenset({
    "cc-by",
    "cc-by-sa",
    "cc0",
    "public-domain",
    "mit",
})


# ---------------------------------------------------------------------------
# Aliases — raw strings observed in API responses -> normalised values
# ---------------------------------------------------------------------------

# Hand-maintained mapping for strings whose normalisation isn't obvious
# from the pattern alone.  Add entries here when ``classify_strings``
# reports an unknown that should clearly be classifiable.
_EXPLICIT_ALIASES: dict[str, str] = {
    # Public domain forms
    "pd":              "public-domain",
    "publicdomain":    "public-domain",
    "public domain":   "public-domain",
    # CC0 forms
    "cc-zero":         "cc0",
    "cc-0":            "cc0",
    # No alias entries are needed for CC-BY-* with the separators stripped
    # (e.g. ``"ccby"``, ``"ccbyncnd"``); ``_CC_NO_SEPARATOR_RE`` below
    # reinserts the hyphens during preprocessing, so the canonical
    # hyphenated form is recovered before any alias lookup runs.
    # Publisher-specific tags that OpenAlex / Unpaywall sometimes emit.
    # These mean "the publisher chose to make this article free to read,
    # under their own terms" — i.e. bronze OA equivalent.  Not
    # redistributable by default.
    "publisher-specific-oa":  "proprietary",
    "publisher-specific":     "proprietary",
    "acs-specific-tdm":       "proprietary",
    "elsevier-specific-oa":   "proprietary",
    # Unpaywall's "other-oa" means "OA but with an open licence we
    # didn't recognise" — safest to leave as unknown for human review.
    "other-oa": "unknown",
}


# Regex to strip a trailing version number like " 4.0", "-4.0", "v4", "/4.0".
# A separator (-, whitespace, /, or _) is REQUIRED before the version digits,
# so that names with a literal trailing digit ("cc0") aren't mistaken for
# versioned forms ("cc-by-4.0").
_VERSION_SUFFIX_RE = re.compile(r"[-\s/_]v?\d+(?:\.\d+)*$")


# Regex to recognise CC licence codes with the separators stripped (e.g.
# ``"ccbyncnd"``).  Some upstream API sources emit licence strings in this
# concatenated form.  The match groups split it back into canonical
# hyphenated form: cc-by[-nc][-sa|-nd].
#
# Structure: ``cc`` + required ``by`` + optional ``nc`` + optional ``sa``
# or ``nd`` (mutually exclusive, since ``sa`` and ``nd`` don't co-occur in
# the CC vocabulary).  This matches all six valid no-separator forms:
# ccby, ccbysa, ccbync, ccbynd, ccbyncsa, ccbyncnd.
_CC_NO_SEPARATOR_RE = re.compile(r"^cc(by)(nc)?(sa|nd)?$")


def normalise_license(raw: object) -> str:
    """Map a raw licence string to one of ``KNOWN_LICENSES``.

    Pipeline (in order):
      1.  None / non-string / empty / "null" / "none" -> ``"unknown"``.
      2.  Lowercase, strip outer whitespace.
      3.  Drop any annotation after the first comma (e.g.
          ``"publisher-specific, author manuscript"`` ->
          ``"publisher-specific"``).  Commas don't appear in valid
          licence identifiers, so this is safe.
      4.  Collapse runs of whitespace/underscore to a single hyphen;
          collapse repeated hyphens; strip leading/trailing hyphens.
      5.  Reinsert hyphens between glued CC tokens via
          ``_CC_NO_SEPARATOR_RE`` (e.g. ``"ccbyncnd"`` -> ``"cc-by-nc-nd"``).
      6.  Check ``_EXPLICIT_ALIASES`` BEFORE version stripping — this
          catches cases like ``"cc-0"`` whose trailing ``-0`` would
          otherwise be mistaken for a version suffix.
      7.  Strip trailing version suffixes (e.g. ``"cc-by 4.0"`` ->
          ``"cc-by"``).
      8.  Check ``_EXPLICIT_ALIASES`` again — catches cases like
          ``"publisher-specific-oa 4.0"`` -> ``"publisher-specific-oa"``
          -> ``"proprietary"``.
      9.  If the result is in ``KNOWN_LICENSES``, return it; otherwise
          ``"unknown"``.

    Examples:
        >>> normalise_license("cc-by")
        'cc-by'
        >>> normalise_license("CC-BY 4.0")
        'cc-by'
        >>> normalise_license("CC-BY-NC-ND-4.0")
        'cc-by-nc-nd'
        >>> normalise_license("CCBYNCND")
        'cc-by-nc-nd'
        >>> normalise_license("publisher-specific, author manuscript")
        'proprietary'
        >>> normalise_license("cc0")
        'cc0'
        >>> normalise_license("cc-0")
        'cc0'
        >>> normalise_license("MIT")
        'mit'
        >>> normalise_license(None)
        'unknown'
        >>> normalise_license("")
        'unknown'
    """
    if not isinstance(raw, str):
        return "unknown"
    s = raw.strip().lower()
    if not s or s in {"null", "none", "n/a", "na"}:
        return "unknown"

    # Drop everything after the first comma; commas mark annotation,
    # not part of the identifier.
    if "," in s:
        s = s.split(",", 1)[0].strip()
        if not s:
            return "unknown"

    # Normalise separators: whitespace and underscores become hyphens.
    s = re.sub(r"[\s_]+", "-", s)
    # Collapse repeated hyphens.
    s = re.sub(r"-+", "-", s).strip("-")

    # Check explicit aliases BEFORE version stripping so things like
    # "cc-0" (where the trailing "-0" looks like a version suffix) get
    # caught.
    if s in _EXPLICIT_ALIASES:
        return _EXPLICIT_ALIASES[s]

    # Strip a trailing version suffix (e.g. "cc-by-4.0" -> "cc-by",
    # "ccby 4.0" -> "ccby-4.0" -> "ccby").
    s_no_version = _VERSION_SUFFIX_RE.sub("", s).strip("-")
    if s_no_version:
        s = s_no_version

    # If the (now version-stripped) string is a glued CC licence code
    # (e.g. "ccbync"), split it back into canonical hyphenated form.
    # Doing this AFTER version stripping handles "ccby 4.0" -> "ccby"
    # -> "cc-by"; doing it earlier would miss that case because the
    # anchored regex can't match while a "-4.0" suffix is still
    # attached.
    m = _CC_NO_SEPARATOR_RE.match(s)
    if m:
        s = "cc-" + "-".join(g for g in m.groups() if g)

    # Check aliases AGAIN after stripping — covers e.g.
    # "publisher-specific-oa 4.0" -> "publisher-specific-oa" -> "proprietary".
    if s in _EXPLICIT_ALIASES:
        return _EXPLICIT_ALIASES[s]
    if s in KNOWN_LICENSES:
        return s
    return "unknown"


# ---------------------------------------------------------------------------
# Predicates
# ---------------------------------------------------------------------------

def is_publishable(license: object) -> bool:
    """True if ``license`` permits redistribution of derived artifacts.

    Accepts either a raw string (will be normalised) or an already-
    normalised value.  Returns False for ``"unknown"``,
    ``"proprietary"``, the CC-BY-NC family, and anything else not in
    ``PUBLISHABLE_LICENSES``.

    Examples:
        >>> is_publishable("cc-by")
        True
        >>> is_publishable("CC-BY 4.0")
        True
        >>> is_publishable("cc-by-nc")
        False
        >>> is_publishable("proprietary")
        False
        >>> is_publishable(None)
        False
        >>> is_publishable("")
        False
    """
    return normalise_license(license) in PUBLISHABLE_LICENSES


def is_intentionally_unknown(raw: object) -> bool:
    """True if ``raw`` normalises to ``"unknown"`` via an explicit alias.

    Distinguishes two cases that both bucket as ``"unknown"``:

      - **Intentional**: the raw string is recognised but its meaning is
        "the licence is not identifiable" (e.g. Unpaywall's ``"other-oa"``
        which means "OA but with an unidentified licence").  These are
        documented decisions and should not appear in the
        enrichment-time review report.
      - **Unclassified**: the raw string was not recognised at all (e.g.
        a new publisher-specific tag we have not seen before).  These
        are the ones a human should review and potentially add to
        ``_EXPLICIT_ALIASES``.

    Empty strings, ``None``, ``"null"``, etc. return ``False`` — they
    are unclassified rather than intentional.

    Note: this function duplicates the preprocessing steps of
    ``normalise_license`` (comma-strip, lowercase, separator collapse,
    CC-token split, version-suffix strip) so that a raw string is
    checked against ``_EXPLICIT_ALIASES`` after the same transforms
    ``normalise_license`` applies.  If the preprocessing logic changes
    there, update it here too — the parallel-behaviour test in
    ``test_license_policy.py`` will fail otherwise.
    """
    if not isinstance(raw, str):
        return False
    s = raw.strip().lower()
    if not s or s in {"null", "none", "n/a", "na"}:
        return False
    if "," in s:
        s = s.split(",", 1)[0].strip()
        if not s:
            return False
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    if _EXPLICIT_ALIASES.get(s) == "unknown":
        return True
    s_no_version = _VERSION_SUFFIX_RE.sub("", s).strip("-")
    if s_no_version:
        s = s_no_version
    m = _CC_NO_SEPARATOR_RE.match(s)
    if m:
        s = "cc-" + "-".join(g for g in m.groups() if g)
    return _EXPLICIT_ALIASES.get(s) == "unknown"


# ---------------------------------------------------------------------------
# Bulk classification (for enrichment-time review)
# ---------------------------------------------------------------------------

def classify_strings(raws: Iterable[object]) -> dict[str, list[str]]:
    """Bucket a collection of raw licence strings by normalised value.

    Useful during enrichment runs: feed it every licence string seen in
    an API batch and inspect the ``"unknown"`` bucket for things worth
    adding to ``_EXPLICIT_ALIASES``.

    Returns a mapping ``{normalised_value: [unique_raw_strings_seen]}``.
    Each list of raw strings is sorted and de-duplicated.

    Example::

        classify_strings(["cc-by", "CC-BY 4.0", "publisher-specific-oa", "x"])
          -> {"cc-by": ["CC-BY 4.0", "cc-by"],
              "proprietary": ["publisher-specific-oa"],
              "unknown": ["x"]}
    """
    by_norm: dict[str, set[str]] = {}
    for r in raws:
        norm = normalise_license(r)
        # Record the raw input as-seen (preserve case for human review),
        # but only if it's a string — non-strings are recorded as their
        # repr to avoid dropping a signal silently.
        key = r if isinstance(r, str) else repr(r)
        by_norm.setdefault(norm, set()).add(key)
    return {k: sorted(v) for k, v in by_norm.items()}
