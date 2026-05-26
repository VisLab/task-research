"""
convert.py — PDF -> Markdown conversion via marker-pdf.

Thin wrapper around `marker-pdf <https://github.com/VikParuchuri/marker>`_
exposing the single function the rest of the literature-search
pipeline calls: ``convert_pdf(pdf_path) -> str``.

Why marker-pdf and not markitdown / pdfminer:
    markitdown does fast, lightweight text extraction but relies on
    PyPDF / pdfminer text grabbing, which loses structure on most
    academic papers — equations, multi-column layouts, tables,
    figures with embedded captions.  marker-pdf uses layout-aware
    ML models to preserve those structures.  For HED's use case
    (~824 reference PDFs converting to publishable Markdown), the
    quality difference is the difference between "usable artifact"
    and "needs manual fix-up on every conversion".

Runtime characteristics worth knowing:
    First-run model download is several GB into ``~/.cache/marker``;
    subsequent runs reuse the cache.  GPU acceleration is detected
    and used automatically if available; CPU fallback works but is
    much slower (~30 s per page on CPU vs ~2 s on a typical GPU).

    The wrapper does **not** cache the marker converter object
    across calls.  For one-off conversions this is fine; for batch
    conversion (PR-E's acquisition orchestrator), the orchestrator
    should build a single ``PdfConverter`` and reuse it — see the
    note in ``_load_converter()`` below.

If marker-pdf changes its API:
    The version pinned in ``pyproject.toml``'s ``[pdf]`` extra
    dictates the API shape this wrapper targets.  When upgrading
    marker-pdf, run ``test_convert.py`` — the smoke test catches
    API drift.  This is the only file in the pipeline that imports
    marker directly; everything else goes through ``convert_pdf``.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def convert_pdf(
    pdf_path: str | Path,
    output_path: str | Path | None = None,
) -> str:
    """Convert a PDF file to Markdown using marker-pdf.

    Args:
        pdf_path: Path to the source PDF.
        output_path: If provided, also write the Markdown to this file
            as UTF-8 alongside returning it.

    Returns:
        The Markdown text.

    Raises:
        FileNotFoundError: pdf_path does not exist.
        ImportError: marker-pdf is not installed.  Install with
            ``pip install -e ".[pdf]"`` from the repo root.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    converter = _load_converter()

    logger.info("converting %s with marker-pdf", pdf_path)
    rendered = converter(str(pdf_path))
    md_text = _text_from_rendered(rendered)

    if output_path is not None:
        out = Path(output_path)
        out.write_text(md_text, encoding="utf-8")
        logger.info("Markdown written to %s", out)

    return md_text


# ---------------------------------------------------------------------------
# Internal — kept private so the public surface stays one function.
# ---------------------------------------------------------------------------

def _load_converter():
    """Instantiate marker-pdf's PdfConverter, loading or downloading models.

    Re-instantiated on every call.  For one-off conversions this is
    fine — marker caches the model weights on disk, so subsequent
    instantiations are fast (the disk-to-RAM load still happens, but
    no network).  For batch conversion in PR-E, the orchestrator
    should build a converter once and reuse it; that optimisation is
    deferred until it actually matters.
    """
    try:
        from marker.converters.pdf import PdfConverter
        from marker.models import create_model_dict
    except ImportError as exc:
        raise ImportError(
            "marker-pdf is required for PDF conversion.  Install with: "
            'pip install -e ".[pdf]"'
        ) from exc

    return PdfConverter(artifact_dict=create_model_dict())


def _text_from_rendered(rendered) -> str:
    """Extract the Markdown string from marker-pdf's rendered output.

    marker-pdf returns a Pydantic-shaped object whose attribute / call
    layout has shifted between minor versions.  We try the documented
    entry point first, then fall back to direct attribute access.
    Both paths are exercised by the smoke test in
    ``test_convert.py``.
    """
    # Preferred: the documented helper.
    try:
        from marker.output import text_from_rendered
    except ImportError:
        text_from_rendered = None

    if text_from_rendered is not None:
        result = text_from_rendered(rendered)
        # text_from_rendered returns (text, ext, images) in current
        # versions; older versions returned text directly.  Handle
        # both.
        if isinstance(result, tuple):
            return result[0]
        return result

    # Fallback: attribute access on the rendered object.
    for attr in ("markdown", "text", "content"):
        val = getattr(rendered, attr, None)
        if isinstance(val, str):
            return val

    raise RuntimeError(
        "Could not extract Markdown from marker-pdf rendered output; "
        "marker-pdf may have changed its public API.  Inspect the "
        "rendered object and update _text_from_rendered."
    )
