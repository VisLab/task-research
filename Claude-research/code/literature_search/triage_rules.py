"""
triage_rules.py — Publisher/venue allowlists and triage classifiers.

All triage decisions about venue and publisher quality are encoded here
so they are reviewable as data and easy to revise, not scattered through
the triage script.

Source authority: literature_search_plan_2026-04-21.md §5.1, §5.2, §5.3.
"""

import re

# ---------------------------------------------------------------------------
# §5.1  DOI prefix → publisher tier
# ---------------------------------------------------------------------------

PUBLISHER_TIERS: dict[str, str] = {
    # Tier A — flagship publishers
    "10.1016": "A",   # Elsevier
    "10.1007": "A",   # Springer Nature
    "10.1038": "A",   # Nature publishing
    "10.1002": "A",   # Wiley
    "10.1037": "A",   # APA
    "10.1523": "A",   # Society for Neuroscience
    "10.1073": "A",   # PNAS
    "10.1126": "A",   # AAAS (Science)
    "10.1093": "A",   # Oxford University Press
    "10.1017": "A",   # Cambridge University Press
    "10.1146": "A",   # Annual Reviews
    # Tier B — mainstream, accepted with modest discount
    "10.1177": "B",   # SAGE
    "10.1080": "B",   # Taylor & Francis
    "10.1371": "B",   # PLOS
    "10.3389": "B",   # Frontiers (per-journal caveat)
    "10.1101": "B",   # bioRxiv (preprint caveat)
    "10.3758": "B",   # Psychonomic Society
    "10.1162": "B",   # MIT Press (Journal of Cognitive Neuroscience)
    "10.1167": "B",   # ARVO (Journal of Vision)
    "10.7554": "B",   # eLife Sciences
    "10.1152": "B",   # American Physiological Society
    "10.1111": "B",   # Wiley-Blackwell (Psychophysiology, etc.)
    "10.1068": "B",   # Pion / Sage (Perception)
}


# ---------------------------------------------------------------------------
# §5.2  Venue allowlist (canonical-preprocessed forms)
# ---------------------------------------------------------------------------

# Preprocessing: lowercase, strip all non-[a-z0-9 ], normalize "and" to space,
# collapse whitespace, strip leading "the ".
# Both sides of a comparison use _prep(); exact set membership then works
# regardless of punctuation, "and"/"&", or "The " prefix variations.

def _prep(v: str) -> str:
    v = v.lower()
    v = re.sub(r"[^a-z0-9 ]", " ", v)   # & : , . → space
    v = re.sub(r"\band\b", " ", v)       # "and" → space (same as &)
    v = re.sub(r"\s+", " ", v).strip()
    if v.startswith("the "):             # strip leading "the"
        v = v[4:]
    return v


# Build preprocessed lookup sets at import time.
def _mkset(items: set[str]) -> set[str]:
    return {_prep(s) for s in items}


VENUE_TIERS: dict[str, set[str]] = {
    # ---- FLAGSHIP ----
    "flagship": {
        # APA society journals
        "Psychological Review",
        "Psychological Science",
        "Psychological Bulletin",
        "Journal of Experimental Psychology: General",
        "Journal of Experimental Psychology: Human Perception and Performance",
        "Journal of Experimental Psychology: Learning, Memory, and Cognition",
        "Journal of Experimental Psychology: Applied",
        # Old undifferentiated APA journal name (pre-1975)
        "Journal of Experimental Psychology",
        # Old split name (APA 1975–1982)
        "Journal of Experimental Psychology: Human Learning and Memory",
        # BBS
        "Behavioral and Brain Sciences",
        # Trends
        "Trends in Cognitive Sciences",
        "Trends in Neurosciences",
        # Nature group
        "Nature",
        "Nature Neuroscience",
        "Nature Human Behaviour",
        "Nature Reviews Neuroscience",
        "Nature Reviews Neurology",
        "Nature Communications",
        "Nature Methods",
        "Nature Protocols",
        "Scientific Reports",
        # Science / AAAS
        "Science",
        "Science Advances",
        # PNAS
        "Proceedings of the National Academy of Sciences",
        "Proceedings of the National Academy of Sciences of the United States of America",
        "PNAS",
        # Cell Press
        "Cell",
        "Current Biology",
        # Neuroscience
        "NeuroImage",
        "Neuron",
        "Journal of Neuroscience",
        "The Journal of Neuroscience",
        "Cerebral Cortex",
        "Brain",
        # Cognitive & clinical
        "Cognition",
        "Cognitive Psychology",
        # Annual Reviews
        "Annual Review of Psychology",
        "Annual Review of Neuroscience",
        "Annual Review of Vision Science",
        # Vision / perception
        "Journal of Vision",
        "Attention, Perception, & Psychophysics",
        "Perception & Psychophysics",   # older name
        # eLife
        "eLife",
        # Lancet
        "The Lancet",
        "Lancet",
        # PLoS Biology
        "PLoS Biology",
        "PLOS Biology",
    },

    # ---- MAINSTREAM ----
    "mainstream": {
        # Psychophysiology / body of work
        "Psychophysiology",
        # Neuroimaging
        "Human Brain Mapping",
        # Clinical neuropsychology adjacent
        "Neuropsychologia",
        "Cortex",
        # Cognitive neuroscience
        "Journal of Cognitive Neuroscience",
        # Memory
        "Memory & Cognition",
        # Psychonomic
        "Psychonomic Bulletin & Review",
        "Behavior Research Methods",
        "Behavior Research Methods, Instruments, & Computers",
        # Language
        "Brain and Language",
        # SCAN
        "Social Cognitive and Affective Neuroscience",
        # Emotion
        "Cognition & Emotion",
        # Neuropsychopharmacology
        "Neuropsychopharmacology",
        # Other mainstream
        "Current Directions in Psychological Science",
        "Perspectives on Psychological Science",
        # Journal of Personality and Social Psychology
        "Journal of Personality and Social Psychology",
        # Review journals
        "Review of General Psychology",
        "Psychological Medicine",
        "Quarterly Journal of Experimental Psychology",
        # Biological
        "Biological Psychiatry",
        "Biological Psychology",
        "Behavioural Brain Research",
        # Cognitive neuroscience / methods
        "Cognitive Neuropsychology",
        "Brain and Cognition",
        "Experimental Brain Research",
        # Development
        "Child Development",
        "Developmental Cognitive Neuroscience",
        # Affective / CABN
        "Cognitive, Affective, & Behavioral Neuroscience",
        # Clinical science
        "Clinical Psychological Science",
        # Translational / molecular
        "Molecular Psychiatry",
        "Translational Psychiatry",
        # PLOS
        "PLoS ONE",
        "PLOS ONE",
        "PLOS Computational Biology",
        "PLoS Computational Biology",
        # Other
        "Psychological Research",
        "Psychopharmacology",
        "Sleep",
        "Visual Cognition",
        "Neuropsychology Review",
        "Neuroscience & Biobehavioral Reviews",
        "Neuroscience and Biobehavioral Reviews",
        # Personality & social
        "Personality and Social Psychology Bulletin",
    },

    # ---- SPECIALTY ----
    "specialty": {
        "Journal of Experimental Child Psychology",
        "Consciousness and Cognition",
        "Emotion",
        "Neuropsychology",
        "Journal of Abnormal Psychology",
        "Journal of Abnormal and Social Psychology",
        "Journal of Applied Psychology",
        "Learning & Memory",
        "Learning and Motivation",
        "Journal of Memory and Language",
        "Acta Psychologica",
        "Vision Research",
        "Spatial Vision",
        "British Journal of Psychology",
        "Canadian Journal of Psychology",
        "Canadian Psychologist",
        "American Psychologist",
        "American Journal of Psychology",
        "Journal of Verbal Learning and Verbal Behavior",
        "Journal of General Psychology",
        "Journal of Consulting Psychology",
        "Journal of Educational Psychology",
        "Journal of Neurology, Neurosurgery, and Psychiatry",
        "Journal of Child Psychology and Psychiatry",
        "Journal of the Acoustical Society of America",
        "Psychomotor Skills",
        "Perceptual and Motor Skills",
        "Journal of Cognitive Psychology",
        "Cognitive Science",
        "Topics in Cognitive Science",
        "Cognitive Brain Research",
        "Brain Research",
        "Brain Research Reviews",
        "Reviews of Modern Physics",
        "Clinical Neurophysiology",
        "International Journal of Psychophysiology",
        "Journal of Physiology",
        "Journal of Neurophysiology",
        "European Journal of Neuroscience",
        "Hippocampus",
        "Neuroscience",
        "Journal of Experimental Analysis of Behavior",
        "Journal of the Experimental Analysis of Behavior",
        "Learning and Motivation",
        "Games and Economic Behavior",
        "Journal of Economic Literature",
        "Journal of Economic Behavior and Organization",
        "Econometrica",
        "Games Econ Behav",
        "Psychology and Aging",
        "Schizophrenia Bulletin",
        "Neuropsychological Rehabilitation",
        "Philosophical Transactions of the Royal Society B",
        "Philosophical Transactions of the Royal Society of London B",
        "Philosophical Transactions of the Royal Society of London. Series B",
        "Philosophical Transactions of the Royal Society B: Biological Sciences",
        "Philosophical Transactions of the Royal Society of London. B, Biological Sciences",
        "Philosophical Transactions of the Royal Society of London. Series B: Biological Sciences",
        "Philosophical Transactions of the Royal Society of London. Series B, Biological Sciences",
        "Machine Learning",
        "Journal of Experimental Psychology: Animal Behavior Processes",
        "Psychology of Learning and Motivation",
        "Journal of Personality",
        "Psychological Assessment",
        "Journal of Psychiatry and Neuroscience",
        "JAMA Psychiatry",
        # Clinical neuropsychology
        "Archives of Clinical Neuropsychology",
        "Journal of Clinical and Experimental Neuropsychology",
        "Journal of Neuropsychology",
        "Clinical Neuropsychologist",
        "Applied Neuropsychology",
        "Applied Neuropsychology: Adult",
        "Neuropsychological Rehabilitation",
        "Neuropsychology Review",
        # Aging / gerontology
        "Aging, Neuropsychology, and Cognition",
        "Gerontology",
        "Journals of Gerontology Series A",
        "Journals of Gerontology Series B",
        # Animal learning
        "Animal Learning & Behavior",
        # Applied / cognitive
        "Applied Cognitive Psychology",
        # Behavioural therapy
        "Behaviour Research and Therapy",
        # Behavioral neuroscience
        "Behavioral Neuroscience",
        "Behavioural Brain Research",
        "Brain and Behavior",
        # Bilingualism
        "Bilingualism: Language and Cognition",
        # EEG
        "Electroencephalography and Clinical Neurophysiology",
        # European assessment
        "European Journal of Psychological Assessment",
        "European Journal of Personality",
        "European Journal of Social Psychology",
        # Frontiers (Tier B publisher; listed here for completeness)
        "Frontiers in Aging Neuroscience",
        "Frontiers in Behavioral Neuroscience",
        "Frontiers in Human Neuroscience",
        "Frontiers in Neuroscience",
        "Frontiers in Psychology",
        "Frontiers in Systems Neuroscience",
        # Motor
        "Journal of Motor Behavior",
        # Language / speech
        "Journal of Speech, Language, and Hearing Research",
        "Language and Cognitive Processes",
        "Language, Cognition and Neuroscience",
        # Math psychology
        "Journal of Mathematical Psychology",
        # Memory standalone journal
        "Memory",
        # Metacognition
        "Metacognition and Learning",
        # Molecular
        "Molecular Autism",
        # Methods
        "Journal of Neuroscience Methods",
        # Motivation
        "Motivation and Emotion",
        # Neurological
        "Archives of Neurology",
        "Multiple Sclerosis Journal",
        # Neurobiology of language
        "Neurobiology of Language",
        # Neuropharmacology
        "Neuropharmacology",
        # Neurorehabilitation
        "Neurorehabilitation and Neural Repair",
        # International neuropsychological
        "Journal of the International Neuropsychological Society",
        # Physiological
        "Physiological Reviews",
        # Clinical psychology
        "Clinical Psychology Review",
        "Depression and Anxiety",
        # Psychometrics
        "Psychometrika",
        "Psychological Inquiry",
        "Psychological Monographs",
        "Psychological Reports",
        # Scandinavian
        "Scandinavian Journal of Psychology",
        # Social / personality
        "Social and Personality Psychology Compass",
        # Systematic reviews
        "Systematic Reviews",
        # Thinking / timing
        "Thinking & Reasoning",
        "Timing & Time Perception",
        # Cognitive neuropsychiatry
        "Cognitive Neuropsychiatry",
        # Current opinion journals
        "Current Opinion in Behavioral Sciences",
        "Current Opinion in Neurobiology",
        "Current Opinion in Neurology",
        "Current Opinion in Psychology",
        # IEEE
        "IEEE Transactions on Neural Networks",
        "IEEE Transactions on Neural Networks and Learning Systems",
        # Intelligence
        "Intelligence",
        # International developmental
        "International Journal of Developmental Neuroscience",
        # Data
        "Data in Brief",
        # Open access
        "F1000Research",
        # Experimental economics
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
    },

    # ---- LOW OR EXCLUDED ----
    "low_or_excluded": {
        # Beall-listed or known-quality-concern journals go here as discovered.
        # Also test manuals (caught by TEST_MANUAL_PATTERNS before venue check).
    },
}

# Precomputed sets for O(1) classification
_FLAGSHIP_SET: set[str] = _mkset(VENUE_TIERS["flagship"])
_MAINSTREAM_SET: set[str] = _mkset(VENUE_TIERS["mainstream"])
_SPECIALTY_SET: set[str] = _mkset(VENUE_TIERS["specialty"])
_LOW_EXCLUDED_SET: set[str] = _mkset(VENUE_TIERS["low_or_excluded"])


# ---------------------------------------------------------------------------
# §5.3  Explicit exclusion patterns (test manuals, handbooks)
# ---------------------------------------------------------------------------

TEST_MANUAL_PATTERNS: list[re.Pattern] = [
    re.compile(r"\bmanual\b", re.IGNORECASE),
    re.compile(r"\bhandbook\b", re.IGNORECASE),
    re.compile(r"\bWAIS(-[IVX]+)?\b", re.IGNORECASE),
    re.compile(r"\bWMS(-[IVX]+)?\b", re.IGNORECASE),
    re.compile(r"\bD-KEFS\b", re.IGNORECASE),
    re.compile(r"\bDelis.Kaplan\b", re.IGNORECASE),
    re.compile(r"\bIAPS\b"),                          # International Affective Picture System
    re.compile(r"\bKDEF\b"),
    re.compile(r"Raven'?s?\s+Progressive\s+Matrices\s+Manual", re.IGNORECASE),
    re.compile(r"\bRAVLT\b"),                         # Rey Auditory Verbal Learning Test
]

# LANDMARK_IDS is a set of (owner_id, pub_id) pairs loaded at runtime.
LANDMARK_IDS: set[tuple[str, str]] = set()


# ---------------------------------------------------------------------------
# Public classifiers
# ---------------------------------------------------------------------------

def classify_venue(venue_str: str | None) -> str:
    """Return 'flagship' | 'mainstream' | 'specialty' | 'low_or_excluded' | 'unknown'.

    Comparison is case-insensitive, punctuation-insensitive, 'and'/'&'-
    insensitive, and strips a leading 'The ' article.
    """
    if not venue_str:
        return "unknown"
    v = _prep(venue_str)
    if v in _FLAGSHIP_SET:
        return "flagship"
    if v in _MAINSTREAM_SET:
        return "mainstream"
    if v in _SPECIALTY_SET:
        return "specialty"
    if v in _LOW_EXCLUDED_SET:
        return "low_or_excluded"
    return "unknown"


def publisher_tier_from_doi(doi: str | None) -> str | None:
    """Return 'A' | 'B' | 'C' | None based on the DOI prefix.

    A DOI like '10.1016/j.neuroimage.2004.12.015' has prefix '10.1016'.
    Returns None if doi is absent or prefix not in PUBLISHER_TIERS.
    Returns 'C' for any prefix not in the map (default exclusion).
    """
    if not doi:
        return None
    doi = doi.lower().strip()
    # Strip URL prefix first, then extract the registrant component (10.XXXX)
    if doi.startswith("https://doi.org/"):
        doi = doi[len("https://doi.org/"):]
    elif doi.startswith("http://doi.org/"):
        doi = doi[len("http://doi.org/"):]
    prefix = doi.split("/")[0] if "/" in doi else doi
    tier = PUBLISHER_TIERS.get(prefix)
    return tier if tier is not None else "C"


def matches_test_manual(ref: dict) -> bool:
    """Return True if any TEST_MANUAL_PATTERNS matches venue, journal,
    citation_string, or title of the reference."""
    fields = [
        ref.get("venue") or "",
        ref.get("journal") or "",
        ref.get("citation_string") or "",
        ref.get("title") or "",
    ]
    combined = " ".join(fields)
    return any(p.search(combined) for p in TEST_MANUAL_PATTERNS)


# ---------------------------------------------------------------------------
# Bootstrap helper — print venue classification table for all venues in data
# ---------------------------------------------------------------------------

def print_venue_check(process_refs: list[dict], task_refs: list[dict]) -> None:
    """Print a sorted table of (venue_string → tier) for every unique venue
    found in the reference objects.  Used during sub-phase 2.2 to verify
    allowlist coverage before running the full triage.
    """
    venues: set[str] = set()
    for ref in process_refs + task_refs:
        v = ref.get("venue")
        if v:
            venues.add(v)

    print(f"{'Venue':<65}  {'Tier'}")
    print("-" * 75)
    for v in sorted(venues, key=str.lower):
        tier = classify_venue(v)
        marker = "  <-- REVIEW" if tier == "unknown" else ""
        print(f"{v:<65}  {tier}{marker}")


if __name__ == "__main__":
    # Bootstrap mode: print venue check for _inputs/ JSON files.
    import json, sys
    from pathlib import Path
    script_dir = Path(__file__).parent
    p_path = script_dir / "_inputs" / "process_details.json"
    t_path = script_dir / "_inputs" / "task_details.json"
    p_data = json.loads(p_path.read_text(encoding="utf-8"))
    t_data = json.loads(t_path.read_text(encoding="utf-8"))
    p_refs = [ref for proc in p_data.get("processes", [])
              for arr in ("fundamental_references", "recent_references")
              for ref in proc.get(arr, [])]
    t_refs = [ref for task in t_data
              for arr in ("key_references", "recent_references")
              for ref in task.get(arr, [])]
    print_venue_check(p_refs, t_refs)
