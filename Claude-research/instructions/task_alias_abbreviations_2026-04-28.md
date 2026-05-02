# Task alias abbreviations — reference

**Date:** 2026-04-28
**Purpose:** Document the short-form (acronym) aliases on tasks in
`task_details.json`, what they expand to, and why each one is or isn't
risky for the phrase-gate substring matcher.

The `rank_and_select._phrase_list` filter (`_MIN_SINGLE_TOKEN_ALIAS_LEN = 4`)
drops single-token aliases of 4 characters or fewer from the phrase gate
and the relevance scorer. This protects against the alias-collision class
of bug that surfaced for `FER` on `hedtsk_facial_emotion_recognition`
(plant biology, ferroptosis, and IVF papers contaminating the picked
tier). The filter is a defensive safety net; the data itself remains
unchanged unless explicitly cleaned.

The `Filtered` column below indicates whether each abbreviation is
currently dropped by the safety filter (single-token AND length ≤ 4).
The `Conflict risk` column flags unrelated literatures that use the same
acronym — these are what would have polluted the picked tier without the
filter.

---

## Two-letter abbreviations (filtered)

| Alias | Stands for | HED task | Conflict risk |
|---|---|---|---|
| `DG` | Dictator Game | `hedtsk_dictator_game` | "DG" = dentate gyrus (huge neuroscience literature on hippocampal subfields) |
| `DS` | Digit Span | `hedtsk_digit_span` | "DS" = Down syndrome (clinical), "DS" = drug-sensitive, generic shorthand in many fields |
| `FC` | Fear Conditioning | `hedtsk_pavlovian_fear_conditioning` | "FC" = functional connectivity (massive fMRI literature), "FC" = fold change (genomics) |
| `PD` | Prisoner's Dilemma | `hedtsk_prisoners_dilemma` | "PD" = Parkinson's disease (catches every Parkinson's paper) |
| `TG` | Trust Game | `hedtsk_trust_game` | "TG" = transgenic (mouse genetics, ubiquitous in molecular bio) |
| `UG` | Ultimatum Game | `hedtsk_ultimatum_game` | "UG" generic; less specific cross-talk |

## Three-letter abbreviations (filtered)

| Alias | Stands for | HED task | Conflict risk |
|---|---|---|---|
| `AGL` | Artificial Grammar Learning | `hedtsk_artificial_grammar_learning` | Less common as a non-task acronym; relatively safe but filtered for consistency |
| `ANT` | Attention Network Task | `hedtsk_attention_network` | "ant" = the insect; many biology/ecology papers tokenize "ant" |
| `AST` | Anti-Saccade Task | `hedtsk_anti_saccade` | "AST" = aspartate aminotransferase (liver enzyme; clinical chemistry) |
| `CPT` | Continuous Performance Task | `hedtsk_continuous_performance` | "CPT" = current procedural terminology (medical billing); some overlap |
| `DMS` | Delayed Match-to-Sample | `hedtsk_delayed_match_to_sample` | "DMS" = dimethyl sulfide (chemistry), document management system |
| `FER` | Facial Emotion Recognition | `hedtsk_facial_emotion_recognition` | **Removed from data 2026-04-28.** "FER" = FERONIA receptor kinase (plant biology), "Fer-1" = ferrostatin (cell death), FER1L4 (lncRNA) |
| `FTT` | Finger Tapping Task | `hedtsk_finger_tapping` | "FTT" = fault tolerance, fast tunnel test; less risky |
| `GNG` | Go/No-Go | `hedtsk_go_no_go` | Less common as a non-task acronym |
| `IAT` | Implicit Association Test | `hedtsk_implicit_association` | "IAT" = idiopathic anterior toxoplasmosis, intermittent abdominal twitching; minor overlap |
| `IGT` | Iowa Gambling Task | `hedtsk_iowa_gambling` | "IGT" = impaired glucose tolerance (diabetes literature) |
| `LDT` | Lexical Decision Task | `hedtsk_lexical_decision` | "LDT" = local distance test, low-density transit; minor |
| `MID` | Monetary Incentive Delay | `hedtsk_monetary_incentive_delay` | "mid" = generic English word; tokenizes against "midbrain" no, that tokenizes as "midbrain" — but "mid-life", "mid-line" split on hyphens to "mid" |
| `MAB` | Multi-Armed Bandit | `hedtsk_multi_armed_bandit` | "MAB" = monoclonal antibody (massive immunology literature); also "Mab" as part of drug names |
| `MMN` | Mismatch Negativity | `hedtsk_mismatch_negativity` | Generally specific to ERP literature; relatively safe |
| `MOT` | Multiple Object Tracking | `hedtsk_multiple_object_tracking` | "mot" generic in some contexts; less risk |
| `MRT` | Mental Rotation Task | `hedtsk_mental_rotation` | "MRT" = magnetic resonance tomography (medical imaging) |
| `MST` | Mnemonic Similarity Task | `hedtsk_mnemonic_similarity` | "MST" = minimum spanning tree (CS), median sleep time |
| `MTT` | Mirror Tracing Task | `hedtsk_mirror_tracing` | "MTT" = MTT assay (cell viability assay; widely used in molecular biology) |
| `PAL` | Paired Associates Learning | `hedtsk_paired_associates_learning` | "PAL" = phase-alternation line (TV standard), generic |
| `PIT` | Pavlovian-Instrumental Transfer | `hedtsk_instrumental_conditioning` | "pit" = English word; many false matches |
| `PLW` | Point-Light Walker | `hedtsk_biological_motion` (or similar) | Specific; relatively safe but filtered |
| `PRL` | Probabilistic Reversal Learning | `hedtsk_reversal_learning` | "PRL" = prolactin (endocrinology, every reproductive bio paper) |
| `PRP` | Psychological Refractory Period | `hedtsk_psychological_refractory_period` | "PRP" = platelet-rich plasma (clinical); PHP (variant) |
| `PSS` | Probabilistic Stimulus Selection | `hedtsk_probabilistic_selection` | "PSS" = perceived stress scale (psychology questionnaire — would actually overlap with relevant lit), other generics |
| `PST` | Probabilistic Selection Task | `hedtsk_probabilistic_selection` | "PST" = post (time abbreviation), various |
| `PVT` | Psychomotor Vigilance Task | `hedtsk_psychomotor_vigilance` | Generally specific to cog-neuro; relatively safe but short |
| `RAM` | Radial Arm Maze | `hedtsk_radial_arm_maze` | "RAM" = random access memory (huge CS hit), random; ambiguous; "ram" the animal |
| `RAT` | Remote Associates Task | `hedtsk_remote_associates` | **High-risk.** "rat" = the lab animal — every rodent paper |
| `RDK` | Random Dot Kinematogram | `hedtsk_random_dot_motion` | Generally specific; relatively safe but short |
| `RPM` | Raven's Progressive Matrices | `hedtsk_ravens_progressive_matrices` | "RPM" = revolutions per minute (physics, engineering, medicine) |
| `SID` | Social Incentive Delay | `hedtsk_social_incentive_delay` | "SID" = security ID, sudden infant death (variant of SIDS); generic |
| `SST` | Stop-Signal Task | `hedtsk_stop_signal` | "SST" = somatostatin (massive neuroscience hit on inhibitory interneurons), sea surface temperature |
| `TMT` | Trail Making Test | `hedtsk_trail_making` | "TMT" = trimethyltin (neurotoxin literature), trade marketing |
| `TOL` | Tower of London | `hedtsk_tower_of_london` | Generally specific to cog-neuro |
| `WPT` | Weather Prediction Task | `hedtsk_probabilistic_classification_learning` | Generally specific |

## Four-letter abbreviations (filtered)

| Alias | Stands for | HED task | Conflict risk |
|---|---|---|---|
| `BART` | Balloon Analog Risk Task | `hedtsk_balloon_analog_risk` | "BART" = Bay Area Rapid Transit, Bidirectional Auto-Regressive Transformer (NLP model), generally safe in cog-neuro |
| `CFMT` | Cambridge Face Memory Test | `hedtsk_cambridge_face_memory` | Specific; relatively safe but filtered |
| `CWIT` | Color-Word Interference Test | `hedtsk_stroop` (Stroop variant) | Specific; relatively safe but filtered |
| `DSST` | Digit Symbol Substitution Test | `hedtsk_digit_symbol_substitution` | Specific; relatively safe but filtered |
| `RMET` | Reading the Mind in the Eyes Test | `hedtsk_reading_the_mind_in_the_eyes` | Specific to social cognition literature |
| `SART` | Sustained Attention to Response Task | `hedtsk_sustained_attention_to_response` | Specific to attention literature; relatively safe but filtered |
| `SDMT` | Symbol Digit Modalities Test | `hedtsk_digit_symbol_substitution` | Specific; relatively safe but filtered |
| `SRTT` | Serial Reaction Time Task | `hedtsk_serial_reaction_time` | Specific; relatively safe but filtered |

## Aliases that pass the filter (5+ characters)

| Alias | Stands for | HED task | Notes |
|---|---|---|---|
| `Corsi` | (proper name) | `hedtsk_corsi_block_tapping` | Surname of the originator (Philip M. Corsi); 5 chars, passes |
| `OSPAN` | Operation Span | `hedtsk_operation_span` | 5 chars, specific |
| `RAVLT` | Rey Auditory Verbal Learning Test | `hedtsk_rey_auditory_verbal_learning` | 5 chars, specific clinical instrument |

---

## Notes on use

The filter applied at code level is a safety net. It does not modify
`task_details.json`. Aliases listed as "filtered" remain in the data and
will be visible to anyone reading `task_details.json` directly, which is
fine for documentation purposes.

If a specific abbreviation is judged worth keeping despite the filter
(e.g., the abbreviation is so dominantly used in its specific field that
filtering it has unacceptable recall cost), two paths:

1. **Lower the filter cutoff.** Edit
   `_MIN_SINGLE_TOKEN_ALIAS_LEN` in `code/literature_search/rank_and_select.py`.
   For example, `_MIN_SINGLE_TOKEN_ALIAS_LEN = 3` would let 4-character
   aliases through (BART, CFMT, etc.) but still drop 2-3 char ones.
2. **Replace the alias with a longer disambiguating form.** For example,
   replace `"FER"` with `"facial emotion recognition"` (multi-word, safe).
   This is the cleaner long-term fix and has been done for FER.

For abbreviations that are truly load-bearing for the search (i.e.,
their removal noticeably hurts recall), we'd want a different mechanism:
either case-sensitive token match (treat `FER` as different from `fer`)
or context-aware filtering (require the abbreviation to appear near the
expanded form). Neither is currently implemented; both would require
deeper changes to the phrase gate and the relevance scorer.

The current filter is conservative — it errs toward dropping potentially
useful aliases rather than admitting noise. Given the size of the
candidate pool returned by the search, missing a few legitimate
abbreviation matches is much cheaper than mixing rodent-only papers
into the picked tier of a human-cognition catalog.

---

## Cross-reference: process aliases (none filtered)

The process aliases added in the 2026-04-26 alias-generation pass were
deliberately chosen to avoid this class of bug. None are filtered:

- Single-word: `Pavlovian` (9 chars), `interoception` (13), `olfaction`
  (9), `reappraisal` (11), `self-referential` (16), `saccadic` (8),
  `Mentalizing` (11), `Vigilance` (9), `Gustation` (9), `Somatosensation`
  (14), `Memory Updating` (multi-word). All ≥ 5 chars when single-token.
- Multi-word phrases (e.g., `inhibitory control`, `task-unrelated thought`,
  `causal inference`) pass via the multi-word substring path, which is
  not affected by the length filter.

Process aliases are reviewed in `instructions/alias_generation_plan_2026-04-26.md`.
