"""
Vendored from opencite (https://github.com/neuromechanist/opencite),
commit ``3e784ddd067b75e73fd0c69e02e82142be1afe11``, file
``src/opencite/models.py`` (the ``parse_identifier`` function only).
MIT licence retained.  See ``task-research/NOTICE.md`` at the repo
root.

Local modifications: extracted from upstream's ``models.py`` into
this standalone module so URL / identifier parsing is separable
from data-model code.  The function body is unchanged.
"""

from __future__ import annotations

import re

from .models import IDType


def parse_identifier(raw: str) -> tuple[IDType, str]:
    """Auto-detect identifier type from a raw string.

    Formats:
        10.xxx/yyy              -> DOI
        pmid:12345              -> PMID
        pmc:PMC12345            -> PMCID
        PMC12345                -> PMCID
        arxiv:2106.15928        -> ArXiv
        2106.15928[vN]          -> ArXiv (bare new-style ID)
        cs.LG/0101001           -> ArXiv (bare old-style ID)
        https://arxiv.org/abs/… -> ArXiv (URL)
        https://arxiv.org/pdf/… -> ArXiv (URL)
        https://www.biorxiv.org/content/… -> DOI extracted from URL
        https://www.medrxiv.org/content/… -> DOI extracted from URL
        W1234567890             -> OpenAlex
        40-char hex             -> S2 paper ID
    """
    s = raw.strip()

    # --- arXiv / bioRxiv URL detection (must come before DOI pattern) ---

    # arXiv URLs: https://arxiv.org/abs/2106.15928[v2]
    #             https://arxiv.org/pdf/2106.15928[v2]
    #             https://arxiv.org/html/2106.15928[v2]
    arxiv_url_match = re.match(
        r"https?://(?:ar[xX]iv\.org|export\.arxiv\.org)/(?:abs|pdf|html|e-print)/"
        r"([0-9]{4}\.[0-9]{4,5}(?:v\d+)?|[a-zA-Z.-]+/\d+(?:v\d+)?)",
        s,
    )
    if arxiv_url_match:
        arxiv_id = arxiv_url_match.group(1)
        # Strip version suffix for canonical ID
        arxiv_id = re.sub(r"v\d+$", "", arxiv_id)
        return (IDType.ARXIV, arxiv_id)

    # bioRxiv/medRxiv URLs: extract DOI from URL path
    # e.g. https://www.biorxiv.org/content/10.1101/2021.01.01.425001v2
    biorxiv_url_match = re.match(
        r"https?://www\.(?:bio|med)rxiv\.org/content/(10\.\d{4,}/\S+?)(?:v\d+)?(?:\.full(?:\.pdf)?)?$",
        s,
    )
    if biorxiv_url_match:
        return (IDType.DOI, biorxiv_url_match.group(1))

    # --- Explicit prefixes ---
    lower = s.lower()
    if lower.startswith("pmid:"):
        return (IDType.PMID, s[5:])
    if lower.startswith("pmc:"):
        val = s[4:]
        if not val.upper().startswith("PMC"):
            val = f"PMC{val}"
        return (IDType.PMCID, val)
    if lower.startswith("arxiv:"):
        # Strip optional version: arXiv:2106.15928v2 -> 2106.15928
        arxiv_id = re.sub(r"v\d+$", "", s[6:])
        return (IDType.ARXIV, arxiv_id)
    if lower.startswith("doi:"):
        return (IDType.DOI, s[4:])

    # --- PMC ID without prefix ---
    if s.upper().startswith("PMC") and s[3:].isdigit():
        return (IDType.PMCID, s.upper())

    # --- DOI pattern ---
    if re.match(r"^10\.\d{4,}/", s):
        return (IDType.DOI, s)

    # --- OpenAlex ID ---
    if re.match(r"^W\d+$", s):
        return (IDType.OPENALEX, s)

    # --- S2 40-char hex ---
    if re.match(r"^[0-9a-f]{40}$", s):
        return (IDType.S2, s)

    # --- Bare arXiv ID (new format): YYMM.NNNNN[vN] ---
    # Must be checked before bare-digits fallback
    if re.match(r"^\d{4}\.\d{4,5}(?:v\d+)?$", s):
        arxiv_id = re.sub(r"v\d+$", "", s)
        return (IDType.ARXIV, arxiv_id)

    # --- Bare arXiv ID (old format): area.subarea/YYMMNNN[vN] ---
    if re.match(r"^[a-zA-Z-]+(?:\.[A-Z]{2})?/\d{7}(?:v\d+)?$", s):
        arxiv_id = re.sub(r"v\d+$", "", s)
        return (IDType.ARXIV, arxiv_id)

    # --- Bare digits -> assume PMID ---
    if s.isdigit():
        return (IDType.PMID, s)

    raise ValueError(f"Cannot determine identifier type for: {raw}")
