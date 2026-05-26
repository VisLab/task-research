"""
Smoke test for convert.py — the marker-pdf wrapper.

Two tests:

  test_convert_pdf_import_error_message
      -> if marker-pdf is not installed, our wrapper raises an
         ImportError with a useful install hint.  Light, no network.
         Runs by default.

  test_convert_pdf_roundtrip (marked 'slow')
      -> actual round-trip of a small PDF through marker-pdf,
         asserting our marker text survives.  Heavy: marker-pdf
         downloads ~5 GB of ML model weights on first run into
         ``~/.cache/marker``; first invocation can take minutes
         even on fast networks.  Subsequent runs reuse the cache.
         Opt-in only.

Default test run:

    pytest code/literature_search/test_convert.py -v

Including the heavy round-trip:

    pip install -e ".[pdf]"
    pytest code/literature_search/test_convert.py -v -m slow

If you do not have marker-pdf installed, the round-trip test is
skipped automatically (pytest.importorskip) so the file's default
collection stays clean.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make sibling modules importable without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parent))


# ---------------------------------------------------------------------------
# 1.  Import-error message (no marker-pdf needed)
# ---------------------------------------------------------------------------

def test_convert_pdf_import_error_message(monkeypatch, tmp_path: Path) -> None:
    """When marker-pdf is missing, our wrapper raises a helpful ImportError.

    Simulates a missing marker-pdf install by blocking the marker
    package in ``sys.modules`` and then calling ``convert_pdf`` on
    a tiny stub file.  The wrapper's ImportError message should
    contain the install hint.

    This test is lightweight and runs by default — it does not need
    marker-pdf to be installed.
    """
    # Build a stub file so the wrapper's existence check passes.
    pdf_path = tmp_path / "stub.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF\n")

    # Block marker imports.  We replace the marker package in sys.modules
    # with None, which makes ``from marker.X import Y`` raise ImportError.
    monkeypatch.setitem(sys.modules, "marker", None)
    monkeypatch.setitem(sys.modules, "marker.converters", None)
    monkeypatch.setitem(sys.modules, "marker.converters.pdf", None)
    monkeypatch.setitem(sys.modules, "marker.models", None)

    from convert import convert_pdf

    with pytest.raises(ImportError) as exc_info:
        convert_pdf(pdf_path)

    msg = str(exc_info.value)
    assert "marker-pdf" in msg, f"expected 'marker-pdf' in ImportError, got: {msg}"
    assert "pip install" in msg, f"expected install hint in ImportError, got: {msg}"


# ---------------------------------------------------------------------------
# 2.  PDF -> Markdown round-trip (slow; opt-in)
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_convert_pdf_roundtrip(tmp_path: Path) -> None:
    """Run a tiny PDF through the marker-pdf wrapper end-to-end.

    Skipped if marker-pdf isn't installed (use ``pip install -e
    ".[pdf]"`` from the repo root).  Heavy: first run downloads
    model weights to ``~/.cache/marker``.  Subsequent runs reuse the
    cache and finish in seconds.

    Fixture: a hand-rolled minimal PDF containing the literal text
    ``Hello PR-B`` in Helvetica.  If marker-pdf cannot extract that
    string from a valid minimal PDF, either our fixture is wrong or
    marker-pdf has regressed; either is worth investigating before
    PR-E builds on top of this wrapper.
    """
    pytest.importorskip(
        "marker", reason='install with: pip install -e ".[pdf]"'
    )

    from convert import convert_pdf

    # Hand-rolled minimal PDF.  Valid PDF 1.4 with a single page
    # containing the string 'Hello PR-B' in Helvetica.  ~700 bytes.
    pdf_bytes = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]"
        b"/Resources<</Font<</F1 5 0 R>>>>/Contents 4 0 R>>endobj\n"
        b"4 0 obj<</Length 56>>stream\n"
        b"BT /F1 24 Tf 100 700 Td (Hello PR-B) Tj ET\n"
        b"endstream endobj\n"
        b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
        b"xref\n0 6\n"
        b"0000000000 65535 f\n"
        b"0000000009 00000 n\n"
        b"0000000052 00000 n\n"
        b"0000000098 00000 n\n"
        b"0000000189 00000 n\n"
        b"0000000295 00000 n\n"
        b"trailer<</Size 6/Root 1 0 R>>\n"
        b"startxref\n358\n%%EOF\n"
    )
    pdf_path = tmp_path / "smoke.pdf"
    pdf_path.write_bytes(pdf_bytes)

    md = convert_pdf(pdf_path)
    assert isinstance(md, str)
    assert "Hello PR-B" in md, (
        f"Marker text missing from output (first 200 chars): {md[:200]!r}.  "
        "Either marker-pdf cannot OCR this minimal fixture, or its API has "
        "shifted.  If the latter, update _text_from_rendered in convert.py."
    )
