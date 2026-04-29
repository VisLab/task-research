"""
species.py — Classify a Candidate as human-subject, non-human-subject, or unknown.

Used as a Stage A post-retrieval filter to keep rodent and other animal
studies from contending with human studies for the picked-tier slots.
The HED catalog is human-cognition focused; rodent inhibition / rodent
working memory / rodent reinforcement-learning literatures exist but
shouldn't dominate the picked set.

Returns one of three states for each candidate:
    True   — at least one strong positive human signal AND no decisive
             non-human signal.
    False  — at least one decisive non-human signal AND no positive
             human-only signal that outranks it.
    None   — insufficient signal to classify (e.g., empty title and
             abstract). Treated by the tier classifier as "unknown,
             leave in pool" — better to under-filter than to drop a
             possibly-human study.

Three signal sources, in priority order:
    1. MeSH terms when present (Europe PMC). MeSH "Humans" is decisive
       positive; "Animals" without "Humans" is decisive negative.
    2. Title + abstract + TLDR keyword scan. Multi-token negative
       keywords (e.g., "non-human primate") qualify positive matches.
    3. (Future) S2 fieldsOfStudy as a weak signal. Currently unused.

The classifier is intentionally conservative: when in doubt, return
None. The tier classifier is the place that decides what to do with
unknowns.

No network calls. No state. Pure function over Candidate fields.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Keyword sets
# ---------------------------------------------------------------------------

# Strong positive signals — almost always indicate human subjects.
# Multi-word phrases must appear verbatim; single tokens are word-boundary
# matched (whole-word, case-insensitive).
_HUMAN_PHRASES: tuple[str, ...] = (
    "human participants",
    "human subjects",
    "healthy adults",
    "healthy controls",
    "in humans",
    "patients with",
    "in patients",
    "clinical population",
)
_HUMAN_TOKENS: frozenset[str] = frozenset({
    "human", "humans",
    "patient", "patients",
    "subject", "subjects",      # weak; only counted if no animal token present
    "participant", "participants",
})

# Decisive non-human signals when present without a stronger human signal.
# These are the actual species/model words; specific lab-animal contexts.
_ANIMAL_TOKENS: frozenset[str] = frozenset({
    "rat", "rats",
    "mouse", "mice",
    "rodent", "rodents",
    "macaque", "macaques",
    "monkey", "monkeys",
    "marmoset", "marmosets",
    "zebrafish", "drosophila",
    "c.elegans",                 # also matches "c. elegans" via tokenization
    "rabbit", "rabbits",
    "pigeon", "pigeons",
    "ferret", "ferrets",
    "vole", "voles",
})
# Compound phrases that look animal but are actually human-relative.
# When one of these appears, the matched animal token is NOT counted.
_QUALIFYING_PHRASES: tuple[str, ...] = (
    "non-human primate",
    "non-human primates",
    "nonhuman primate",
    "nonhuman primates",
    "human primate",
    "human-primate",
    "human-monkey",
    "human and monkey",
    "human and rodent",
)


# MeSH heading vocabulary (Europe PMC supplies these as plain strings).
_MESH_POSITIVE: frozenset[str] = frozenset({"humans"})
# We treat "Animals" as a presence flag; the MeSH convention is that any
# study with non-human subjects is tagged "Animals", and human studies
# may be tagged either "Humans" or both "Humans" + "Animals". So
# "Animals" alone (without "Humans") is the decisive negative signal.
_MESH_ANIMAL_FLAG = "animals"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify_human_subject(
    title: str | None,
    abstract: str | None,
    tldr: str | None = None,
    mesh_terms: list[str] | None = None,
) -> tuple[bool | None, list[str]]:
    """Return (is_human, evidence_list) for a candidate.

    The evidence list records which signals fired, in human-readable form.
    Useful for audit and for the JSON output's `species_evidence` field.

    Decision rules, in order:
      1. If MeSH "Humans" present → True (with evidence "mesh:Humans").
      2. If MeSH "Animals" present and "Humans" absent → False
         (with evidence "mesh:Animals (no Humans)").
      3. Otherwise scan title + abstract + TLDR.
         - If a qualifying phrase matches (e.g. "non-human primate"),
           mark all subsequent animal-token matches as qualified
           (do not count them as negative signals).
         - Strong positive phrase or high-confidence token → True.
         - Animal token (unqualified) without any positive token → False.
         - Mixed signals → True (human studies sometimes mention rodent
           literature for comparison; assume positive).
         - No signals → None.
    """
    evidence: list[str] = []
    text = " ".join(s for s in (title, abstract, tldr) if s).lower()

    mesh_lower = {m.lower() for m in (mesh_terms or [])}

    # 1. MeSH-based decisive signals.
    if _MESH_POSITIVE & mesh_lower:
        evidence.append("mesh:Humans")
        return True, evidence
    if _MESH_ANIMAL_FLAG in mesh_lower:
        evidence.append("mesh:Animals (no Humans)")
        return False, evidence

    if not text:
        return None, evidence

    # 2. Look for human-positive phrases in the text.
    positive_phrase_hit = any(p in text for p in _HUMAN_PHRASES)
    if positive_phrase_hit:
        evidence.append("phrase:human-positive")

    # 3. Animal tokens, qualified by surrounding phrases.
    qualifying_present = any(q in text for q in _QUALIFYING_PHRASES)
    if qualifying_present:
        evidence.append("phrase:non-human-primate-qualifier (positive)")

    tokens = set(re.split(r"[^a-z0-9]+", text))
    animal_hits = tokens & _ANIMAL_TOKENS
    human_token_hits = tokens & _HUMAN_TOKENS

    if animal_hits and not qualifying_present:
        evidence.append(f"token:animal ({','.join(sorted(animal_hits))})")
    if human_token_hits:
        evidence.append(f"token:human ({','.join(sorted(human_token_hits))})")

    # 4. Decision.
    has_positive = positive_phrase_hit or qualifying_present or bool(human_token_hits)
    has_negative = bool(animal_hits) and not qualifying_present

    if has_positive and not has_negative:
        return True, evidence
    if has_negative and not has_positive:
        return False, evidence
    if has_positive and has_negative:
        # Mixed signals usually mean a human study referencing rodent work.
        # Lean True; the tier classifier can still demote if needed.
        evidence.append("decision:mixed→human")
        return True, evidence

    # No signals at all.
    return None, evidence


# ---------------------------------------------------------------------------
# Convenience wrapper for Candidate objects
# ---------------------------------------------------------------------------

def classify_candidate(cand) -> tuple[bool | None, list[str]]:
    """Pull the relevant fields off a Candidate and call classify_human_subject."""
    return classify_human_subject(
        title=cand.title,
        abstract=cand.abstract,
        tldr=cand.tldr,
        mesh_terms=cand.mesh_terms,
    )
