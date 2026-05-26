"""
Vendored from opencite (https://github.com/neuromechanist/opencite),
commit ``3e784ddd067b75e73fd0c69e02e82142be1afe11``, file
``src/opencite/models.py``.  MIT licence retained.  See
``task-research/NOTICE.md`` at the repo root.

Local modifications: slimmed from upstream's full models.py to the
three definitions our pipeline actually uses — the ``IDType`` enum,
the ``IDSet`` dataclass, and the ``PDFLocation`` dataclass.
Upstream's ``Author``, ``Source``, ``Paper``, ``SearchResult``,
``CitationResult`` and ``parse_identifier`` are not included here:
our catalogue formats author / venue / paper concepts differently
(see ``schemas/{process_details,task_details}.schema.json``), and
``parse_identifier`` is split out into a sibling ``url_parsers.py``
to keep models / parsers separable.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class IDType(Enum):
    """Identifier types for academic papers."""

    DOI = "doi"
    PMID = "pmid"
    PMCID = "pmcid"
    OPENALEX = "openalex"
    S2 = "s2"
    ARXIV = "arxiv"


@dataclass(frozen=True)
class IDSet:
    """All known identifiers for a single paper.

    Immutable so it can be used for dedup lookups.
    """

    doi: str = ""
    pmid: str = ""
    pmcid: str = ""
    openalex_id: str = ""
    s2_id: str = ""
    arxiv_id: str = ""

    def has_any(self) -> bool:
        return bool(
            self.doi
            or self.pmid
            or self.pmcid
            or self.openalex_id
            or self.s2_id
            or self.arxiv_id
        )

    def best_lookup_id(self) -> tuple[IDType, str]:
        """Return the most useful ID for cross-API lookup.

        Priority: DOI > PMID > PMCID > S2 > OpenAlex > ArXiv.
        """
        if self.doi:
            return (IDType.DOI, self.doi)
        if self.pmid:
            return (IDType.PMID, self.pmid)
        if self.pmcid:
            return (IDType.PMCID, self.pmcid)
        if self.s2_id:
            return (IDType.S2, self.s2_id)
        if self.openalex_id:
            return (IDType.OPENALEX, self.openalex_id)
        if self.arxiv_id:
            return (IDType.ARXIV, self.arxiv_id)
        raise ValueError("No identifier available")

    def merge(self, other: IDSet) -> IDSet:
        """Create a new IDSet with the union of both sets' identifiers."""
        return IDSet(
            doi=self.doi or other.doi,
            pmid=self.pmid or other.pmid,
            pmcid=self.pmcid or other.pmcid,
            openalex_id=self.openalex_id or other.openalex_id,
            s2_id=self.s2_id or other.s2_id,
            arxiv_id=self.arxiv_id or other.arxiv_id,
        )


@dataclass
class PDFLocation:
    """A known location where a PDF can be retrieved."""

    url: str
    source: str  # "openalex", "s2", "pmc", "doi"
    version: str = ""  # "publishedVersion", "acceptedVersion", "submittedVersion"
    is_oa: bool = False
    license: str = ""
