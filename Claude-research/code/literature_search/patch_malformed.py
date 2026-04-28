"""
patch_malformed.py — Apply author/title/metadata corrections for the 15
formerly-malformed references in process_details.json.

DEPRECATED: This is a historical one-off script. The corrections it
defines were already applied to process_details.json. It also expects
the pre-2026-04-23 reference schema (separate `fundamental_references`
and `recent_references` arrays); the current schema has unified
`references` so this script will not match against current data.
Retained as a record of which references were patched and why.

Two entries (Lamme 2018, Schmidt 1996) are dropped entirely.
Thirteen locations (14 unique papers, Pavlov appearing twice) get
fields filled in.

Usage (if ever resurrected against historical data):
    python code/literature_search/patch_malformed.py --workspace .
"""

import argparse
import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Corrections table
# key: (process_id, array_name, match_year)  → dict of field overrides
# match_year is used to confirm we're touching the right entry at pos 0
# ---------------------------------------------------------------------------

# Entries to DROP entirely: (process_id, array_name, match_year)
DROPS = {
    ("hed_attentional_awareness", "recent_references",  2018),  # Lamme
    ("hed_verbal_memory",         "recent_references",  1996),  # Schmidt handbook
}

# Entries to patch: same key → dict of fields to set/overwrite
PATCHES = {
    # 1a Pavlov — hed_extinction
    ("hed_extinction", "fundamental_references", 1927): {
        "authors":    "Pavlov, I. P.",
        "title":      "Conditioned reflexes: an investigation of the physiological activity of the cerebral cortex.",
        "venue":      "Oxford University Press",
        "venue_type": "book",
        "source":     "historical",
        "confidence": "high",
        "citation_string": "Pavlov (1927) *Conditioned reflexes* Oxford University Press",
    },
    # 1b Pavlov — hed_pavlovian_conditioning
    ("hed_pavlovian_conditioning", "fundamental_references", 1927): {
        "authors":    "Pavlov, I. P.",
        "title":      "Conditioned reflexes: an investigation of the physiological activity of the cerebral cortex.",
        "venue":      "Oxford University Press",
        "venue_type": "book",
        "source":     "historical",
        "confidence": "high",
        "citation_string": "Pavlov (1927) *Conditioned reflexes* Oxford University Press",
    },
    # 2 von Békésy
    ("hed_auditory_perception", "fundamental_references", 1960): {
        "authors":    "von Békésy, G.",
        "title":      "Experiments in hearing",
        "venue":      "McGraw-Hill",
        "venue_type": "book",
        "source":     "historical",
        "confidence": "high",
        "citation_string": "von Békésy (1960) *Experiments in Hearing* McGraw-Hill",
    },
    # 3 Oxenham — wrong journal; correct to J Neurosci
    ("hed_pitch_perception", "recent_references", 2012): {
        "authors":    "Oxenham, A. J.",
        "title":      "Pitch perception",
        "journal":    "Journal of Neuroscience",
        "venue":      "Journal of Neuroscience",
        "venue_type": "journal",
        "volume":     "32",
        "issue":      "39",
        "pages":      "13335-13338",
        "doi":        "10.1523/JNEUROSCI.3815-12.2012",
        "source":     "crossref",
        "confidence": "high",
        "citation_string": "Oxenham (2012) *Journal of Neuroscience* 32:13335–13338",
    },
    # 5 Breitmeyer
    ("hed_masking", "fundamental_references", 1984): {
        "authors":    "Breitmeyer, B. G.",
        "title":      "Visual Masking: An Integrative Approach",
        "venue":      "Clarendon Press / Oxford University Press",
        "venue_type": "book",
        "source":     "historical",
        "confidence": "high",
        "citation_string": "Breitmeyer (1984) *Visual Masking: An Integrative Approach* Clarendon Press",
    },
    # 6 Baars
    ("hed_perceptual_awareness", "fundamental_references", 1988): {
        "authors":    "Baars, B. J.",
        "title":      "A Cognitive Theory of Consciousness",
        "venue":      "Cambridge University Press",
        "venue_type": "book",
        "source":     "historical",
        "confidence": "high",
        "citation_string": "Baars (1988) *A Cognitive Theory of Consciousness* Cambridge University Press",
    },
    # 7 Nigg — issue was 3, correct to 4; fix venue_type; add doi
    ("hed_interference_control", "recent_references", 2017): {
        "authors":    "Nigg, J. T.",
        "title":      "Annual Research Review: On the relations among self-regulation, self-control, executive functioning, effortful control, cognitive control, impulsivity, risk-taking, and inhibition for developmental psychopathology",
        "venue_type": "journal",
        "issue":      "4",
        "doi":        "10.1111/jcpp.12675",
        "source":     "crossref",
        "confidence": "high",
        "citation_string": "Nigg (2017) *Journal of Child Psychology and Psychiatry* 58:361–383",
    },
    # 8 Ferstl — issue was 6, correct to 5; fix venue_type; add doi
    ("hed_discourse_processing", "recent_references", 2008): {
        "authors":    "Ferstl, E. C., Neumann, J., Bogler, C., & von Cramon, D. Y.",
        "title":      "The extended language network: A meta-analysis of neuroimaging studies on text comprehension",
        "venue_type": "journal",
        "issue":      "5",
        "doi":        "10.1002/hbm.20422",
        "source":     "crossref",
        "confidence": "high",
        "citation_string": "Ferstl, Neumann, Bogler & von Cramon (2008) *Human Brain Mapping* 29:581–593",
    },
    # 9 Ebbinghaus — keep year 1885; use standard English title of translation
    ("hed_forgetting", "fundamental_references", 1885): {
        "authors":    "Ebbinghaus, H.",
        "title":      "Memory: A Contribution to Experimental Psychology",
        "venue":      "Dover Publications (1964 reprint of 1913 translation)",
        "venue_type": "book",
        "source":     "historical",
        "confidence": "high",
        "citation_string": "Ebbinghaus (1885/1964) *Memory: A Contribution to Experimental Psychology* Dover",
    },
    # 10 Rey
    ("hed_verbal_memory", "fundamental_references", 1958): {
        "authors":    "Rey, A.",
        "title":      "L'examen clinique en psychologie",
        "venue":      "Presses Universitaires de France",
        "venue_type": "book",
        "source":     "historical",
        "confidence": "high",
        "citation_string": "Rey (1958) *L'examen clinique en psychologie* Presses Universitaires de France",
    },
    # 12 Sherrington
    ("hed_proprioception", "fundamental_references", 1906): {
        "authors":    "Sherrington, C. S.",
        "title":      "The integrative action of the nervous system",
        "venue":      "Yale University Press",
        "venue_type": "book",
        "doi":        "10.1037/13798-000",
        "source":     "historical",
        "confidence": "high",
        "citation_string": "Sherrington (1906) *The Integrative Action of the Nervous System* Yale University Press",
    },
    # 13 Jeannerod
    ("hed_reaching", "fundamental_references", 1988): {
        "authors":    "Jeannerod, M.",
        "title":      "The neural and behavioural organization of goal-directed movements",
        "venue":      "Clarendon Press / Oxford University Press",
        "venue_type": "book",
        "source":     "historical",
        "confidence": "high",
        "citation_string": "Jeannerod (1988) *The Neural and Behavioural Organization of Goal-Directed Movements* Clarendon Press",
    },
    # 14 Mundy — issue was 5, correct to 6; fix venue_type; add doi
    ("hed_joint_attention", "recent_references", 2018): {
        "authors":    "Mundy, P.",
        "title":      "A review of joint attention and social-cognitive brain systems in typical development and autism spectrum disorder",
        "venue_type": "journal",
        "issue":      "6",
        "doi":        "10.1111/ejn.13720",
        "source":     "crossref",
        "confidence": "high",
        "citation_string": "Mundy (2018) *European Journal of Neuroscience* 47:497–514",
    },
}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workspace", default=".",
                    help="Workspace root (default: current directory)")
    ap.add_argument("--out", default=".scratch/process_details_patched.json",
                    help="Output path relative to workspace")
    args = ap.parse_args()

    ws = Path(args.workspace).resolve()
    src = ws / "process_details.json"
    out = ws / args.out

    data = json.loads(src.read_text(encoding="utf-8"))

    n_patched = 0
    n_dropped = 0

    for proc in data.get("processes", []):
        pid = proc.get("process_id", "")
        for arr_name in ("fundamental_references", "recent_references"):
            arr = proc.get(arr_name, [])
            if not arr:
                continue

            ref0 = arr[0]
            year = ref0.get("year")
            key  = (pid, arr_name, year)

            # DROP
            if key in DROPS:
                proc[arr_name] = arr[1:]   # remove index 0
                n_dropped += 1
                print(f"  DROPPED  {pid}/{arr_name}[0]  year={year}")
                continue

            # PATCH
            if key in PATCHES:
                for field, value in PATCHES[key].items():
                    arr[0][field] = value
                n_patched += 1
                print(f"  PATCHED  {pid}/{arr_name}[0]  year={year}")

    print(f"\nTotal patched: {n_patched}  dropped: {n_dropped}")
    expected_patch = len(PATCHES)
    expected_drop  = len(DROPS)
    if n_patched != expected_patch:
        print(f"  WARNING: expected {expected_patch} patches, got {n_patched}")
    if n_dropped != expected_drop:
        print(f"  WARNING: expected {expected_drop} drops, got {n_dropped}")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
