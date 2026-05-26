"""
Vendored slice of opencite (https://github.com/neuromechanist/opencite).

Public surface re-exported here so callers can write::

    from vendored.opencite import PDFLocation, parse_identifier

instead of pointing at each module individually.  See ``README.md``
in this directory for which files are vendored and the refresh
policy; see ``NOTICE.md`` at the repo root for the MIT licence
attribution this vendoring requires.

Pinned to opencite commit ``3e784ddd06`` (2026-05-06).

Note: PDF -> Markdown conversion is *not* part of this vendored
slice.  We use marker-pdf instead of opencite's markitdown / mistral
path; the wrapper lives at
``Claude-research/code/literature_search/convert.py`` as our own
code, not vendored.  See the PR-B section of the v2 plan for the
rationale.
"""

from __future__ import annotations

# Data models
from .models import IDSet, IDType, PDFLocation
# URL / identifier parsing
from .url_parsers import parse_identifier
# BioC JSON -> Markdown converter (the real value-add from opencite)
from .pmc_convert import bioc_to_markdown, extract_figure_files, extract_metadata


__all__ = [
    "IDSet",
    "IDType",
    "PDFLocation",
    "parse_identifier",
    "bioc_to_markdown",
    "extract_figure_files",
    "extract_metadata",
]
