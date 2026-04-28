"""
_patch_triage_rules.py — DEPRECATED one-off patch.

This script appended additional specialty journal names to the SPECIALTY
list in `triage_rules.py`. The patch was applied; the additional entries
are now part of the committed `triage_rules.py`. This file is retained
only as a record of what was added.

Do not run. Re-running would either fail (anchor already replaced) or
duplicate entries.

If a similar future patch is ever needed, prefer editing `triage_rules.py`
directly rather than via an ANCHOR-based string replacement.
"""

import argparse
from pathlib import Path


ANCHOR = '        "Experimental Economics",\n    },'

ADDITIONS = '''\
        "Experimental Economics",
        # Additional specialty journals
        "Journal of Applied Physiology",
        "Journal of Behavior Therapy and Experimental Psychiatry",
        "Journal of Clinical Psychopharmacology",
        "The Neuroscientist",
        "European Neuropsychopharmacology",
        "Dementia and Geriatric Cognitive Disorders",
        "Research in Autism Spectrum Disorders",
        "Autism",
        # Proceedings of Royal Society B variants
        "Proceedings of the Royal Society of London. Series B. Biological Sciences",
        "Proceedings of the Royal Society B",
        "Proceedings of the Royal Society of London. Series B",
        # QJEP section variants
        "Quarterly Journal of Experimental Psychology Section A",
        "Quarterly Journal of Experimental Psychology Section B",
        # Gerontology full-name variants
        "Journals of Gerontology Series A: Biological Sciences and Medical Sciences",
        "Journals of Gerontology Series B: Psychological Sciences and Social Sciences",
        # Bilingual journal name
        "Canadian Journal of Psychology / Revue canadienne de psychologie",
        # Additional clinical/biological
        "Annals of the New York Academy of Sciences",
        "Journal of the Neurological Sciences",
        "Journal of Child Language",
        "Journal of Communication Disorders",
        "Journal of Economic Psychology",
    },'''


def main() -> int:
    ap = argparse.ArgumentParser(description="DEPRECATED one-off patch (already applied).")
    ap.add_argument("--workspace", default=".",
                    help="Workspace root (default: current directory)")
    args = ap.parse_args()

    path = Path(args.workspace).resolve() / "code" / "literature_search" / "triage_rules.py"
    src = path.read_text(encoding="utf-8")

    if ANCHOR in src:
        new_src = src.replace(ANCHOR, ADDITIONS, 1)
        path.write_text(new_src, encoding="utf-8")
        print("Patch applied.")
        return 0

    print("ERROR: anchor not found (patch is presumably already applied).")
    print("This script is retained only as a record. Do not re-run.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
