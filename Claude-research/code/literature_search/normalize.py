"""
normalize.py — Candidate dataclass and per-source normalization functions.

Each source (OpenAlex, Europe PMC, Semantic Scholar) returns a different JSON
shape.  This module converts each to a uniform Candidate record.  No network
calls; pure data transformation.

v3 additions to Candidate:
    tldr                   — S2 TLDR text (None for OpenAlex/EuropePMC records)
    s2_paper_id            — S2 paperId string; required for Stage B seed selection
    stage_b_edges          — list of citation-edge dicts from Stage B orchestration

v4 additions (2026-04-28, JSON-pipeline refactor):
    composite_score        — final composite from rank_and_select.composite_score
    score_components       — per-component dict (citations/venue/recency/...)
    human_subject          — True/False/None classification for species filter
    tier                   — "picked" | "reserve" | "excluded"
    exclusion_reason       — string code when tier == "excluded"; None otherwise
    auto_role              — assigned role from the ranker ("foundational",
                              "key_review", "recent_primary", "methods",
                              "historical", or None)

Imports:
    from normalize import Candidate, normalize_openalex, normalize_europepmc, normalize_s2
"""

import re
from dataclasses import dataclass, field

from identity import build_pub_id


# ---------------------------------------------------------------------------
# Candidate dataclass
# ---------------------------------------------------------------------------

@dataclass
class Candidate:
    pub_id: str
    doi: str | None
    openalex_id: str | None
    pmid: str | None
    title: str
    first_author_family: str | None
    last_author_family: str | None        # best-effort; None when not extractable
    authors_display: str                  # "Badre, D., & Nee, D. E."
    year: int | None
    venue: str | None
    publisher: str | None
    abstract: str | None                  # reconstructed or raw; capped at 2000 chars
    is_review: bool
    is_meta_analysis: bool
    citation_count: int | None
    fwci: float | None                    # OpenAlex field-weighted citation impact
    cited_by_percentile_year: float | None  # OpenAlex min-percentile (0-100)
    influential_citation_count: int | None  # Semantic Scholar
    oa_status: str | None
    oa_url: str | None
    # v3 additions
    tldr: str | None = None               # S2 TLDR text; None for non-S2 records
    s2_paper_id: str | None = None        # S2 paperId; required for Stage B seeds
    mesh_terms: list[str] = field(default_factory=list)
    openalex_topics: list[dict] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    raw_per_source: dict = field(default_factory=dict)
    stage_b_edges: list[dict] = field(default_factory=list)
    # Each edge dict: {seed_pub_id: str, intents: list[str], is_influential: bool}
    # v4 additions (JSON-pipeline refactor; populated post-ranking)
    composite_score: float | None = None
    score_components: dict = field(default_factory=dict)
    human_subject: bool | None = None     # None == not yet classified or unknown
    species_evidence: list[str] = field(default_factory=list)  # for audit
    tier: str | None = None               # "picked" | "reserve" | "excluded"
    exclusion_reason: str | None = None
    auto_role: str | None = None


# ---------------------------------------------------------------------------
# Abstract reconstruction
# ---------------------------------------------------------------------------

def reconstruct_abstract(inverted_index: dict | None) -> str | None:
    """Reconstruct readable text from OpenAlex abstract_inverted_index.

    Format: {word: [position_int, ...]}. Positions are 0-based.
    Returns None when the index is absent or empty.
    Caps output at 2000 characters.
    """
    if not inverted_index:
        return None
    max_pos = 0
    for positions in inverted_index.values():
        if positions:
            max_pos = max(max_pos, max(positions))

    words = [""] * (max_pos + 1)
    for word, positions in inverted_index.items():
        for pos in positions:
            if 0 <= pos <= max_pos:
                words[pos] = word

    text = " ".join(w for w in words if w)
    return text[:2000] if text else None


# ---------------------------------------------------------------------------
# Author helpers
# ---------------------------------------------------------------------------

def _authors_display(names: list[str]) -> str:
    """Format a name list as a brief display string."""
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]}, & {names[1]}"
    return f"{names[0]} et al."


def _clean_doi(doi_raw: str | None) -> str | None:
    if not doi_raw:
        return None
    doi = doi_raw.lower().strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
    return doi or None


# ---------------------------------------------------------------------------
# OpenAlex normalization
# ---------------------------------------------------------------------------

def normalize_openalex(raw: dict) -> "Candidate | None":
    """Normalize an OpenAlex Works record.  Returns None if title is missing."""
    title = (raw.get("title") or "").strip()
    if not title:
        return None

    doi = _clean_doi(raw.get("doi"))
    openalex_id = raw.get("id")

    # Authors
    authorships = raw.get("authorships") or []
    display_names: list[str] = []
    first_author_family: str | None = None
    last_author_family: str | None = None

    for auth in authorships:
        name = (auth.get("author") or {}).get("display_name", "")
        pos = auth.get("author_position", "")
        parts = name.split()
        family = parts[-1] if parts else ""
        if pos == "first" and first_author_family is None:
            first_author_family = family or None
        if family:
            last_author_family = family
        display_names.append(name)

    authors_display = _authors_display(display_names)
    year = raw.get("publication_year")

    # Venue / publisher
    primary_loc = raw.get("primary_location") or {}
    source = primary_loc.get("source") or {}
    venue = source.get("display_name") or None
    publisher = (
        source.get("host_organization_name")
        or source.get("publisher")
        or None
    )

    # Abstract
    abstract = reconstruct_abstract(raw.get("abstract_inverted_index"))

    # Type flags
    work_type = (raw.get("type") or "").lower()
    is_review = "review" in work_type
    is_meta_analysis = "meta" in work_type

    # Citations
    citation_count = raw.get("cited_by_count")
    fwci = raw.get("fwci")

    # Percentile: OpenAlex {"min": 95, "max": 100} → store min (0-100 percentile)
    pctile_obj = raw.get("cited_by_percentile_year")
    cited_by_percentile_year: float | None = None
    if isinstance(pctile_obj, dict):
        cited_by_percentile_year = float(pctile_obj.get("min", 0))
    elif isinstance(pctile_obj, (int, float)):
        cited_by_percentile_year = float(pctile_obj)

    # OA
    oa = raw.get("open_access") or {}
    oa_status = oa.get("oa_status")
    oa_url = oa.get("oa_url")

    # MeSH (OpenAlex exposes this via mesh field)
    mesh_terms = [
        m.get("descriptor_name", "") for m in (raw.get("mesh") or [])
        if m.get("descriptor_name")
    ]

    openalex_topics = raw.get("topics") or []

    pub_id = build_pub_id(first_author_family, year, title)

    return Candidate(
        pub_id=pub_id,
        doi=doi,
        openalex_id=openalex_id,
        pmid=None,
        title=title,
        first_author_family=first_author_family,
        last_author_family=last_author_family,
        authors_display=authors_display,
        year=year,
        venue=venue,
        publisher=publisher,
        abstract=abstract,
        is_review=is_review,
        is_meta_analysis=is_meta_analysis,
        citation_count=citation_count,
        fwci=fwci,
        cited_by_percentile_year=cited_by_percentile_year,
        influential_citation_count=None,
        oa_status=oa_status,
        oa_url=oa_url,
        tldr=None,          # OpenAlex does not provide TLDR
        s2_paper_id=None,   # OpenAlex does not provide S2 paperId
        mesh_terms=mesh_terms,
        openalex_topics=openalex_topics,
        sources=["openalex"],
        raw_per_source={"openalex": raw},
    )


# ---------------------------------------------------------------------------
# Europe PMC normalization
# ---------------------------------------------------------------------------

def normalize_europepmc(raw: dict) -> "Candidate | None":
    """Normalize a Europe PMC core record.  Returns None if title is missing."""
    title = (raw.get("title") or "").strip()
    if not title:
        return None

    doi = _clean_doi(raw.get("doi"))
    pmid = str(raw.get("pmid") or "").strip() or None

    # Authors
    author_list = (raw.get("authorList") or {}).get("author") or []
    if isinstance(author_list, dict):
        author_list = [author_list]
    display_names: list[str] = []
    first_author_family: str | None = None
    last_author_family: str | None = None

    for a in author_list:
        family = (a.get("lastName") or a.get("collectiveName") or "").strip()
        given = (a.get("firstName") or a.get("initials") or "").strip()
        if family and first_author_family is None:
            first_author_family = family
        if family:
            last_author_family = family
        if given:
            display_names.append(f"{family}, {given[0]}.")
        elif family:
            display_names.append(family)

    authors_display = _authors_display(display_names)

    year_str = raw.get("pubYear") or ""
    year = int(year_str) if year_str.isdigit() else None

    # Venue / publisher
    ji = raw.get("journalInfo") or {}
    journal = ji.get("journal") or {}
    venue = journal.get("title") or journal.get("medlineAbbreviation") or None
    publisher = journal.get("publisher") or None

    # Abstract
    abstract_raw = raw.get("abstractText")
    abstract = str(abstract_raw)[:2000] if abstract_raw else None

    # Publication types
    pt_obj = raw.get("pubTypeList") or {}
    pub_types = pt_obj.get("pubType") or []
    if isinstance(pub_types, str):
        pub_types = [pub_types]
    pt_lower = [pt.lower() for pt in pub_types]
    is_review = any("review" in pt for pt in pt_lower)
    is_meta_analysis = any("meta-analysis" in pt for pt in pt_lower)

    citation_count = raw.get("citedByCount")

    oa_status = "open" if raw.get("isOpenAccess") == "Y" else None
    oa_url: str | None = None
    full_text_list = (raw.get("fullTextUrlList") or {}).get("fullTextUrl") or []
    if isinstance(full_text_list, dict):
        full_text_list = [full_text_list]
    for url_obj in full_text_list:
        if isinstance(url_obj, dict) and url_obj.get("availabilityCode") == "OA":
            oa_url = url_obj.get("url")
            break

    # MeSH
    mh_list = (raw.get("meshHeadingList") or {}).get("meshHeading") or []
    if isinstance(mh_list, dict):
        mh_list = [mh_list]
    mesh_terms = [
        m.get("descriptorName", "") for m in mh_list
        if isinstance(m, dict) and m.get("descriptorName")
    ]

    pub_id = build_pub_id(first_author_family, year, title)

    return Candidate(
        pub_id=pub_id,
        doi=doi,
        openalex_id=None,
        pmid=pmid,
        title=title,
        first_author_family=first_author_family,
        last_author_family=last_author_family,
        authors_display=authors_display,
        year=year,
        venue=venue,
        publisher=publisher,
        abstract=abstract,
        is_review=is_review,
        is_meta_analysis=is_meta_analysis,
        citation_count=citation_count,
        fwci=None,
        cited_by_percentile_year=None,
        influential_citation_count=None,
        oa_status=oa_status,
        oa_url=oa_url,
        tldr=None,          # EuropePMC does not provide TLDR
        s2_paper_id=None,   # EuropePMC does not provide S2 paperId
        mesh_terms=mesh_terms,
        openalex_topics=[],
        sources=["europepmc"],
        raw_per_source={"europepmc": raw},
    )


# ---------------------------------------------------------------------------
# Semantic Scholar normalization
# ---------------------------------------------------------------------------

def normalize_s2(raw: dict) -> "Candidate | None":
    """Normalize a Semantic Scholar paper record.  Returns None if title is missing.

    In v3, TLDR text is stored in ``cand.tldr`` rather than used as an abstract
    fallback.  The abstract field carries only the paper's true abstract.
    ``s2_paper_id`` captures S2's ``paperId`` for Stage B seed selection.
    """
    title = (raw.get("title") or "").strip()
    if not title:
        return None

    ext = raw.get("externalIds") or {}
    doi = _clean_doi(ext.get("DOI"))
    pmid = str(ext.get("PubMed") or "").strip() or None

    # Authors: S2 gives full name strings; extract family as last word.
    authors = raw.get("authors") or []
    display_names: list[str] = []
    first_author_family: str | None = None
    last_author_family: str | None = None

    for a in authors:
        name = (a.get("name") or "").strip()
        parts = name.split()
        family = parts[-1] if parts else ""
        if family and first_author_family is None:
            first_author_family = family
        if family:
            last_author_family = family
        if len(parts) > 1:
            initial = parts[0][0] + "."
            display_names.append(f"{family}, {initial}")
        elif family:
            display_names.append(family)

    authors_display = _authors_display(display_names)

    year = raw.get("year")
    venue = raw.get("venue") or None

    # Abstract: true abstract only (not TLDR fallback in v3).
    abstract: str | None = raw.get("abstract")
    if abstract:
        abstract = str(abstract)[:2000]

    # TLDR: stored separately so the phrase gate and markdown can use it.
    tldr_raw = raw.get("tldr") or {}
    tldr: str | None = None
    if isinstance(tldr_raw, dict):
        tldr = tldr_raw.get("text") or None
    elif isinstance(tldr_raw, str):
        tldr = tldr_raw or None

    # S2 paperId — required for Stage B seed selection.
    s2_paper_id: str | None = raw.get("paperId") or None

    # Publication types

    pub_types = raw.get("publicationTypes") or []
    pt_lower = [pt.lower() for pt in pub_types]
    is_review = "review" in pt_lower
    is_meta_analysis = any("meta" in pt for pt in pt_lower)

    citation_count = raw.get("citationCount")
    influential_citation_count = raw.get("influentialCitationCount")

    oa_status = "open" if raw.get("isOpenAccess") else None
    oa_pdf = raw.get("openAccessPdf") or {}
    oa_url = oa_pdf.get("url") if isinstance(oa_pdf, dict) else None

    pub_id = build_pub_id(first_author_family, year, title)

    return Candidate(
        pub_id=pub_id,
        doi=doi,
        openalex_id=None,
        pmid=pmid,
        title=title,
        first_author_family=first_author_family,
        last_author_family=last_author_family,
        authors_display=authors_display,
        year=year,
        venue=venue,
        publisher=None,
        abstract=abstract,
        is_review=is_review,
        is_meta_analysis=is_meta_analysis,
        citation_count=citation_count,
        fwci=None,
        cited_by_percentile_year=None,
        influential_citation_count=influential_citation_count,
        oa_status=oa_status,
        oa_url=oa_url,
        tldr=tldr,
        s2_paper_id=s2_paper_id,
        mesh_terms=[],
        openalex_topics=[],
        sources=["semanticscholar"],
        raw_per_source={"semanticscholar": raw},
    )
