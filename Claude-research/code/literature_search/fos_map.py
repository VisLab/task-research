"""
fos_map.py — Category → Semantic Scholar fieldsOfStudy map.

Translates this project's 19 category_id values into S2's fieldsOfStudy
vocabulary (broad discipline tags: Neuroscience, Psychology, Medicine, etc.).

Used in two places:
  - Stage A S2 query filter: ``fieldsOfStudy`` query param on /paper/search.
  - Stage B FoS-overlap filter: per-citing-paper topic check.

Design authority: instructions/search_strategy_decisions_2026-04-24.md §6.

Imports:
    from fos_map import fields_of_study_for_category, fields_of_study_set
"""

# ---------------------------------------------------------------------------
# 19-row map: category_id → comma-joined S2 fieldsOfStudy param string
# Rows copied verbatim from decisions doc §6.
# ---------------------------------------------------------------------------

_FOS_MAP: dict[str, str] = {
    "associative_learning_and_reinforcement":
        "Neuroscience,Psychology,Computer Science",
    "auditory_and_pre_attentive_deviance_processing":
        "Neuroscience,Psychology",
    "awareness_agency_and_metacognition":
        "Neuroscience,Psychology,Philosophy",
    "cognitive_flexibility_and_higher_order_executive_function":
        "Neuroscience,Psychology",
    "emotion_perception_and_regulation":
        "Neuroscience,Psychology,Medicine",
    "face_and_object_perception":
        "Neuroscience,Psychology,Computer Science",
    "implicit_and_statistical_learning":
        "Neuroscience,Psychology,Computer Science",
    "inhibitory_control_and_conflict_monitoring":
        "Neuroscience,Psychology,Medicine",
    "language_comprehension_and_production":
        "Neuroscience,Psychology,Linguistics",
    "long_term_memory":
        "Neuroscience,Psychology",
    "motor_preparation_timing_and_execution":
        "Neuroscience,Psychology,Biology",
    "perceptual_decision_making_evidence_accumulation":
        "Neuroscience,Psychology",
    "reasoning_and_problem_solving":
        "Neuroscience,Psychology,Philosophy,Computer Science",
    "reward_anticipation_and_motivation":
        "Neuroscience,Psychology,Medicine",
    "selective_and_sustained_attention":
        "Neuroscience,Psychology",
    "short_term_and_working_memory":
        "Neuroscience,Psychology",
    "social_cognition_and_strategic_social_choice":
        "Neuroscience,Psychology,Economics",
    "spatial_cognition_and_navigation":
        "Neuroscience,Psychology,Biology",
    "value_based_decision_making_under_risk_and_uncertainty":
        "Neuroscience,Psychology,Economics,Computer Science",
}

_FOS_DEFAULT = "Neuroscience,Psychology"


def fields_of_study_for_category(category_id: str | None) -> str:
    """Return the comma-joined S2 fieldsOfStudy param string for this category.

    Falls back to the default (Neuroscience,Psychology) for unknown or None
    category IDs.  The returned string is ready to pass as the ``fieldsOfStudy``
    query parameter to S2 /paper/search.

    Example:
        >>> fields_of_study_for_category("inhibitory_control_and_conflict_monitoring")
        'Neuroscience,Psychology,Medicine'
    """
    if not category_id:
        return _FOS_DEFAULT
    return _FOS_MAP.get(category_id, _FOS_DEFAULT)


def fields_of_study_set(category_id: str | None) -> set[str]:
    """Return a lowercase set of field names for this category.

    Used by Stage B's FoS-overlap filter: the citing paper's fieldsOfStudy
    must intersect this set.  Lowercase comparison is intentional.

    Example:
        >>> fields_of_study_set("reasoning_and_problem_solving")
        {'neuroscience', 'psychology', 'philosophy', 'computer science'}
    """
    fos_str = fields_of_study_for_category(category_id)
    return {f.strip().lower() for f in fos_str.split(",") if f.strip()}
