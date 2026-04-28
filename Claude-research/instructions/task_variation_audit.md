# Task Variation Audit (Current State)

Date: 2026-04-21
Author: Claude Sonnet
Supersedes: .status_2/variation_audit.md

## Purpose

A KEEP/DROP audit of every variation currently in task_details.json, written against the active criteria in tasks_criteria.md. This is a post-audit verification: the original 1086 → 779 reduction has already been applied; this pass confirms the survivors and flags any that should still be removed.

## Criteria

The active criteria are defined in tasks_criteria.md. This audit applies them as-is; it does not restate them. The 12 active DROP codes are: MEAS, ANAL, DESG, STIM, POPL, IDIF, TRAN, PHAR, SCOR, ALIA, MOTI, DUAL. EMOT is retired (§5.1). The four §5 resolutions are honored: §5.4 dual-task uniformly DROP; §5.5 confidence-rating uniformly DROP except Confidence-Accuracy Paradigm in Heartbeat Detection; §5.6 computerized only KEEP if sensory/motor modality changes; §5.1 all emotional variants KEEP.

## Summary

- Total variations audited: 779
- KEEP: 772
- DROP (newly flagged): 7
- Tasks with all variations confirmed: 97
- Tasks with at least one new DROP: 6 (Attention Network Task, Face Processing Task, Visual Search Task, Digit Symbol Substitution Task, Remote Associates Task, Weapons Identification Task)
- Note: Clinical Screening ANT (ANT) is also to be added to the ANT `aliases` array in task_details.json

---

## Per-task tables

### 1. Affective Picture Viewing Task (`hedtsk_affective_picture_viewing`)

Variations: 1

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Category-Specific Selection | KEEP | — | Restricts stimuli to specific emotional categories (e.g., fear, disgust), creating category-structured event blocks distinct from mixed viewing |

---

### 2. Affective Priming Task (`hedtsk_affective_priming`)

Variations: 7

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Evaluative Decision (Good/Bad) | KEEP | — | Participant makes explicit valence judgment; changes response task from standard LDT |
| 2 | Pronunciation/Naming | KEEP | — | Vocal naming response instead of evaluative judgment; different output modality and response event |
| 3 | Subliminal Priming | KEEP | — | Prime below conscious threshold; changes stimulus timing structure and awareness conditions |
| 4 | Picture-Word Priming | KEEP | — | Visual picture prime instead of word; different stimulus type with distinct semantic processing |
| 5 | Face-Face Priming | KEEP | — | Social/facial stimuli as both prime and target; structurally distinct from word-prime paradigm |
| 6 | Cross-Modal Affective Priming | KEEP | — | Auditory prime + visual target; cross-modal structure creates distinct event types |
| 7 | Masked vs. Unmasked Priming | KEEP | — | Systematic masking manipulation changes prime visibility and conscious access to prime |

---

### 3. Anti-Saccade Task (`hedtsk_anti_saccade`)

Variations: 9

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard Anti-Saccade | KEEP | — | Canonical paradigm: participant inhibits reflexive saccade and redirects gaze to mirror location |
| 2 | Prosaccade (Control Condition) | KEEP | — | Opposite stimulus-response mapping (look toward cue); different response requirement from anti-saccade |
| 3 | Interleaved Pro/Anti-Saccade | KEEP | — | Mixed trial types require on-trial task-set switching; distinct from blocked presentation |
| 4 | Blocked Pro/Anti-Saccade | KEEP | — | Separate blocks of pro- and anti-saccade trials; different cognitive context from interleaved |
| 5 | Gap vs. Overlap Conditions | KEEP | — | Fixation offset timing changes saccade initiation dynamics and error rates |
| 6 | Delayed Anti-Saccade | KEEP | — | Memory-guided response after delay period; adds working memory component |
| 7 | Emotional Anti-Saccade | KEEP | — | Emotional stimuli as saccade targets; retained per §5.1 (EMOT retired) |
| 8 | Memory-Guided Anti-Saccade | KEEP | — | Target location must be retained in memory before response; distinct memory demand |
| 9 | Double-Step Anti-Saccade | KEEP | — | Two-step target displacement requires online motor reprogramming |

---

### 4. Artificial Grammar Learning Task (`hedtsk_artificial_grammar_learning`)

Variations: 7

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard AGL (Reber) | KEEP | — | Canonical implicit grammar learning: exposure to strings, then grammaticality judgment |
| 2 | Transfer Version | KEEP | — | Novel surface elements at test; isolates abstract rule knowledge from surface memorization |
| 3 | Chunk Strength Control | KEEP | — | Stimuli equated for associative chunk strength; controls for alternative explanation |
| 4 | Production Task | KEEP | — | Participant generates grammatical strings rather than judging them; different output requirement |
| 5 | Sequential AGL | KEEP | — | Motor/spatial sequential learning of grammar; different modality and response type |
| 6 | Hierarchical AGL | KEEP | — | Nested recursive grammar; structurally distinct grammar type requiring different parsing |
| 7 | Cross-Modal AGL | KEEP | — | Stimulus modality change (visual→auditory or vice versa) at test; cross-modal transfer paradigm |

---

### 5. Attention Network Task (`hedtsk_attention_network`)

Variations: 7

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard ANT (Fan et al., 2002) | KEEP | — | Canonical ANT with three cue types and flanker congruency; measures alerting, orienting, executive |
| 2 | ANT-I (Callejas et al.) | KEEP | — | Revised cue design with interaction effects measure; different trial structure and network scoring |
| 3 | ANT-R (Revised) | KEEP | — | Revised version with separate conflict and inhibition measures; different trial protocol |
| 4 | Lateralized ANT (LANT) | KEEP | — | Stimuli presented laterally to test hemispheric contributions; different spatial arrangement |
| 5 | Child ANT | KEEP | — | Fish stimuli, simplified flanker; procedure genuinely adapted for children per §5.3 |
| 6 | ANT with Emotional Stimuli | KEEP | — | Emotional flanker content; retained per §5.1 (EMOT retired) |
| 7 | Clinical Screening ANT | DROP | ALIA | Synonym for the Attention Network Task, not a distinct variation; to be added to ANT aliases array |

---

### 6. Auditory Masking Task (`hedtsk_auditory_masking`)

Variations: 10

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Simultaneous masking | KEEP | — | Masker and target overlap in time; fundamental temporal configuration of masking |
| 2 | Forward masking | KEEP | — | Masker precedes target; different temporal relationship produces distinct masking mechanism |
| 3 | Backward masking | KEEP | — | Masker follows target; different temporal order from forward masking |
| 4 | Energetic masking (peripheral) | KEEP | — | Peripheral auditory overlap; mechanistically distinct from informational masking |
| 5 | Informational masking (central) | KEEP | — | Central/cognitive masking mechanism; different stimulus and processing demands |
| 6 | Comodulation masking release (CMR) | KEEP | — | Comodulated flanking bands release target from masking; unique stimulus configuration |
| 7 | Speech-in-noise | KEEP | — | Speech target in noise background; distinct task with different linguistic processing demands |
| 8 | Tone-in-noise detection | KEEP | — | Pure tone detection in wideband noise; different target type from speech or complex stimuli |
| 9 | Modulation masking | KEEP | — | Masking of temporal amplitude modulation; different perceptual dimension |
| 10 | Spatial release from masking | KEEP | — | Spatial separation of target and masker; binaural processing distinguishes it from monaural variants |

---

### 7. Autobiographical Memory Task (`hedtsk_autobiographical_memory`)

Variations: 6

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Cue-Word Task (Galton-Crovitz) | KEEP | — | Single word cues; participant freely generates memories in response |
| 2 | Autobiographical Memory Test (Williams & Broadbent) | KEEP | — | Cued recall with specificity scoring and suicidal ideation variant; named standardized instrument |
| 3 | Autobiographical Memory Interview (Kopelman) | KEEP | — | Structured interview with childhood, early adult, and recent life sections; different retrieval protocol |
| 4 | Sentence-Cue Variant | KEEP | — | Sentence-length cues instead of single words; richer cueing structure |
| 5 | Odor-Cued Autobiographical Memory | KEEP | — | Olfactory cues evoke memories; different sensory modality and involuntary retrieval characteristics |
| 6 | Future Episodic Simulation | KEEP | — | Participant imagines future events instead of recalling past; different cognitive operation (projection vs. retrieval) |

---

### 8. Balloon Analog Risk Task (`hedtsk_balloon_analog_risk`)

Variations: 7

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard BART (30 balloons) | KEEP | — | Canonical BART: pump balloon for accumulating reward, risk of explosion |
| 2 | BART-Y (Youth Version) | KEEP | — | Modified pumping interface and simplified feedback for youth; procedure adapted per §5.3 |
| 3 | Variable Explosion Probability | KEEP | — | Explicitly communicated explosion probabilities; changes decision-making structure |
| 4 | High-Stakes vs. Low-Stakes | KEEP | — | Reward magnitude manipulation changes risk-reward trade-off context |
| 5 | Social Context BART | KEEP | — | Observer or peer performance information present; changes social decision-making context |
| 6 | Automatic BART | KEEP | — | Balloon pumps automatically; removes active pumping decision, isolates risk tolerance |
| 7 | BART with Loss Domain | KEEP | — | Losses instead of gains; loss framing changes motivational structure of decisions |

---

### 9. Biological Motion Perception Task (`hedtsk_biological_motion_perception`)

Variations: 11

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Intact Biological Motion | KEEP | — | Standard point-light walker; canonical biological motion stimulus |
| 2 | Scrambled Displays | KEEP | — | Spatially scrambled dots preserve local motion but destroy global form; control condition with different percept |
| 3 | Inverted Displays | KEEP | — | Walker inverted; disrupts configural processing while preserving motion signals |
| 4 | Reversed (Backward) Motion | KEEP | — | Temporal reversal disrupts action identity while preserving form |
| 5 | Action Recognition | KEEP | — | Participant identifies specific action (running, kicking); classification task beyond detection |
| 6 | Detection in Noise | KEEP | — | Walker embedded in noise dots; detection task with varying signal-to-noise |
| 7 | Gender/Identity Discrimination | KEEP | — | Discrimination of walker gender or identity; different judgment dimension |
| 8 | Emotion from Body Motion | KEEP | — | Emotional state judged from body kinematics; different recognition task |
| 9 | Partial/Occluded Displays | KEEP | — | Subset of dots visible; tests perceptual completion of biological motion |
| 10 | Comparison with Mechanical Motion | KEEP | — | Mechanical motion control alongside biological; category discrimination task |
| 11 | Facing Direction Discrimination | KEEP | — | Ambiguous facing direction judgment; different perceptual task |

---

### 10. Body Ownership Illusion Task (`hedtsk_body_ownership_illusion`)

Variations: 8

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Classic Rubber Hand Illusion | KEEP | — | Synchronous brush strokes on rubber hand and hidden real hand; canonical embodiment paradigm |
| 2 | Full Body Illusion (Body Swap) | KEEP | — | Full-body camera-to-HMD setup creates whole-body ownership; different from hand-only paradigm |
| 3 | Virtual Hand / Virtual Body Illusion | KEEP | — | Virtual avatar hand in VR; different sensory integration conditions |
| 4 | Enfacement Illusion | KEEP | — | Synchronous touch to face and rubber face; different body part and social dimension |
| 5 | Somatosensory Rubber Hand Illusion | KEEP | — | Tactile stimulation without visual component; isolates tactile-proprioceptive integration |
| 6 | Kinesthetic Mirror Illusion | KEEP | — | Proprioceptive/kinesthetic basis without visual rubber hand; different sensory modality |
| 7 | Threat Response Paradigm | KEEP | — | Threatening stimulus applied to rubber hand; measures embodiment via threat response |
| 8 | Incongruent Object Control | KEEP | — | Non-hand object used instead of rubber hand; tests specificity of body-form requirement |

---

### 11. Cambridge Face Memory Task (`hedtsk_cambridge_face_memory`)

Variations: 6

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | CFMT-Original | KEEP | — | Canonical 72-item CFMT with novel face learning phases |
| 2 | CFMT-Australian (CFMT+) | KEEP | — | Australian race face set; assesses own-race advantage with matched procedure |
| 3 | CFMT-Cars | KEEP | — | Cars instead of faces; object recognition control condition with same task structure |
| 4 | CFMT-Inverted | KEEP | — | Inverted face stimuli; disrupts configural processing; distinct task demand |
| 5 | Cambridge Face Perception Test (CFPT) | KEEP | — | Morph-ordering perception task instead of recognition; different participant operation |
| 6 | Short-Form CFMT | KEEP | — | Abbreviated item set for screening; recognized published short-form instrument |

---

### 12. Causal Learning Task (`hedtsk_causal_learning`)

Variations: 8

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Allergy Prediction Task | KEEP | — | Canonical food-allergy prediction: participant judges cause-effect contingencies |
| 2 | Blocking Paradigm | KEEP | — | Pre-training on one cue blocks learning about second cue; distinct compound conditioning procedure |
| 3 | Outcome Density Manipulation | KEEP | — | Systematically varies base rate of outcomes; changes the statistical environment |
| 4 | Trial-by-Trial Prediction | KEEP | — | Participant predicts on each trial before feedback; different response requirement from summary judgment |
| 5 | Summary vs. Sequential Presentation | KEEP | — | Summary table vs. trial-by-trial presentation; changes information format and cognitive demand |
| 6 | Multi-Cause (Relative Validity) | KEEP | — | Multiple competing cues; relative validity procedure changes causal inference structure |
| 7 | Causal Direction Manipulation | KEEP | — | Manipulates whether participant judges cause→effect or effect→cause; different reasoning direction |
| 8 | Backward Blocking / Retrospective Revaluation | KEEP | — | Post-training devaluation of compound changes prior learning; distinct temporal structure |

---

### 13. Change Detection Task (`hedtsk_change_detection`)

Variations: 7

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard Color Change Detection | KEEP | — | Canonical flicker paradigm: colored squares change across blank; whole/partial report |
| 2 | Single-Probe Change Detection | KEEP | — | Post-array probe tests one item; different response structure from whole-display report |
| 3 | Orientation Change Detection | KEEP | — | Orientation feature instead of color; different perceptual dimension |
| 4 | Conjunction Change Detection | KEEP | — | Conjunctions of features can change; higher-order binding demand |
| 5 | Change Detection with Filtering | KEEP | — | Some items task-relevant, others to be ignored; adds selective attention demand |
| 6 | Continuous Report / Precision Task | KEEP | — | Participant reports exact remembered value on continuous wheel; different response format |
| 7 | Sequential Presentation | KEEP | — | Items presented serially before test; different encoding structure |

---

### 14. Contextual Cueing Task (`hedtsk_contextual_cueing`)

Variations: 6

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard Visual Search CC | KEEP | — | Canonical: repeated spatial configurations implicitly facilitate target detection |
| 2 | Configuration-Based vs. Association-Based CC | KEEP | — | Separates global configuration from local target-distractor association; different learning conditions |
| 3 | Semantic Contextual Cueing | KEEP | — | Semantic scene content instead of arbitrary array; different memory system engaged |
| 4 | Cross-Modal Contextual Cueing | KEEP | — | Auditory context cues visual search; cross-modal learning paradigm |
| 5 | Dynamic Contextual Cueing | KEEP | — | Moving-element arrays instead of static; different perceptual and memory demands |
| 6 | Transfer of Contextual Cueing | KEEP | — | Tests whether learned context transfers to new target locations; different probe phase |

---

### 15. Continuous Performance Task (`hedtsk_continuous_performance`)

Variations: 8

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | X-CPT (Simple) | KEEP | — | Respond to single target letter; canonical simple vigilance paradigm |
| 2 | AX-CPT (Context Processing) | KEEP | — | Context-dependent target requires tracking A→X sequence; different working memory demand |
| 3 | Identical Pairs CPT (IP-CPT) | KEEP | — | Respond when consecutive stimuli match; different stimulus-response rule |
| 4 | Gradual-Onset CPT (gradCPT) | KEEP | — | Stimuli gradually transition instead of discrete flashes; different perceptual and decision dynamics |
| 5 | Auditory CPT | KEEP | — | Auditory stimulus stream instead of visual; different sensory modality |
| 6 | Conners' CPT-3 | KEEP | — | Standardized commercial CPT with letter stimuli and specific timing; named published instrument |
| 7 | TOVA (Test of Variables of Attention) | KEEP | — | Geometric stimuli, fixed ISI; distinct named instrument with different timing parameters |
| 8 | CPT with Emotional Distractors | KEEP | — | Emotional stimuli as distractors; retained per §5.1 (EMOT retired) |

---

### 16. Corsi Block-Tapping Task (`hedtsk_corsi_block_tapping`)

Variations: 7

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Forward Corsi Span | KEEP | — | Reproduce tapped sequence in same order; canonical visuospatial span |
| 2 | Backward Corsi Span | KEEP | — | Reproduce sequence in reverse order; requires mental transformation |
| 3 | Computerized (eCorsi) | KEEP | — | Screen-based tapping vs. physical blocks; per §5.6 changes spatial/motor demands |
| 4 | Supra-Span Corsi | KEEP | — | Sequences exceed span; repeated learning-to-criterion procedure |
| 5 | Walking Corsi (large-scale) | KEEP | — | Full-body locomotion to large floor locations; different motor modality from finger tapping |
| 6 | Sequential vs. Simultaneous Presentation | KEEP | — | All blocks illuminated at once vs. sequentially; changes encoding demands |
| 7 | Crossed/Uncrossed Paths | KEEP | — | Spatial crossing of sequence paths tests motor programming constraints |

---

### 17. Delay Discounting Task (`hedtsk_delay_discounting`)

Variations: 10

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Adjusting-Amount Method | KEEP | — | Adjusts smaller-sooner amount until indifferent; adaptive titration procedure |
| 2 | Adjusting-Delay Method | KEEP | — | Adjusts delay until indifferent; different dimension titrated |
| 3 | 5-Trial Adjusting Delay | KEEP | — | Rapid 5-trial protocol; distinct abbreviated titration method |
| 4 | Fixed-Choice Discrete Trials | KEEP | — | Fixed set of choices without adaptation; different decision structure |
| 5 | Magnitude Manipulation | KEEP | — | Systematically varies reward magnitude; tests magnitude effect on discounting |
| 6 | Real vs. Hypothetical Rewards | KEEP | — | Real monetary payoff vs. hypothetical; changes incentive structure and motivation |
| 7 | Experiential Discounting Task | KEEP | — | Delays experienced in real time; different temporal structure from verbal/hypothetical |
| 8 | Gain vs. Loss Framing | KEEP | — | Loss domain discounting; different valence changes decision context |
| 9 | Probabilistic Discounting | KEEP | — | Reward probability instead of delay; tests probability rather than temporal discounting |
| 10 | Cross-Commodity Discounting | KEEP | — | Non-monetary rewards (food, drugs); different commodity changes motivational basis |

---

### 18. Delayed Match-to-Sample Task (`hedtsk_delayed_match_to_sample`)

Variations: 7

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard DMTS | KEEP | — | Canonical: sample presented, delay, then match from array |
| 2 | Variable Delay DMTS | KEEP | — | Systematically varies delay length; tests forgetting function |
| 3 | Multi-Choice DMTS | KEEP | — | More than two choices at test; increases decision complexity |
| 4 | DMTS with Distraction During Delay | KEEP | — | Interfering stimuli during retention interval; changes delay period structure |
| 5 | Spatial DMTS | KEEP | — | Location rather than identity must be matched; different memory dimension |
| 6 | DMTS with Object Complexity Manipulation | KEEP | — | Varies object complexity; tests encoding difficulty directly |
| 7 | Delayed Non-Match-to-Sample (DNMS) | KEEP | — | Respond to non-matching item; opposite stimulus-response mapping |

---

### 19. Dictator Game Task (`hedtsk_dictator_game`)

Variations: 9

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard Dictator Game | KEEP | — | Canonical: unilateral allocation from fixed endowment to anonymous recipient |
| 2 | Take Game | KEEP | — | Dictator can take from recipient; different action space |
| 3 | Give-or-Take Game | KEEP | — | Both giving and taking possible; combined action space |
| 4 | Double Dictator | KEEP | — | Both players act as dictators simultaneously; distinct social structure |
| 5 | Earned vs. Windfall Endowment | KEEP | — | Endowment earned through effort vs. given randomly; changes perceived legitimacy |
| 6 | Audience/Observation Effects | KEEP | — | Observer present or aware of allocation; changes social context |
| 7 | N-Person Dictator | KEEP | — | Multiple recipients; changes social structure and distribution decision |
| 8 | Charitable Giving Dictator | KEEP | — | Recipient is charity; different social/moral framing |
| 9 | Exit Option | KEEP | — | Option to leave game rather than allocate; adds outside option to choice set |

---

### 20. Digit Span Task (`hedtsk_digit_span`)

Variations: 11

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Forward Digit Span | KEEP | — | Reproduce digits in order; canonical phonological span measure |
| 2 | Backward Digit Span | KEEP | — | Reproduce in reverse; requires mental transformation |
| 3 | Digit Span Sequencing (WAIS-IV) | KEEP | — | Reorder digits from smallest to largest; different transformation requirement |
| 4 | Letter-Number Sequencing | KEEP | — | Alternating letters and numbers reordered separately; dual sequencing demand |
| 5 | Auditory vs. Visual Presentation | KEEP | — | Visual digit presentation vs. auditory; different input modality |
| 6 | Adaptive Staircase Versions | KEEP | — | Adaptive difficulty tracking; different trial-generation procedure |
| 7 | Spatial Digit Span | KEEP | — | Digits at spatial locations; adds spatial component |
| 8 | Running Digit Span | KEEP | — | Recall last N digits of unknown-length list; different task structure |
| 9 | Grouped/Chunked Presentation | KEEP | — | Digits presented in groups; tests chunking facilitation |
| 10 | Matrix Span | KEEP | — | Spatial matrix locations instead of digits; different stimulus type |
| 11 | Supra-Span Lists | KEEP | — | Lists exceed span; tests learning over trials |

---

### 21. Digit Symbol Substitution Task (`hedtsk_digit_symbol_substitution`)

Variations: 6

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | DSST (Digit-to-Symbol; WAIS) | KEEP | — | Canonical DSST: given digit, write corresponding symbol; pencil-and-paper version |
| 2 | SDMT (Symbol-to-Digit; Smith) | KEEP | — | Given symbol, write digit; reverse lookup direction |
| 3 | Oral SDMT | KEEP | — | Verbal response instead of written; different output modality |
| 4 | Computerized DSST/SDMT | KEEP | — | Button pressing vs. handwriting; per §5.6, changes fine motor skill |
| 5 | Incidental Learning Recall | DROP | MEAS | Recall test appended after the coding task ends; not part of the DSST itself; pure measurement add-on |
| 6 | Paired-Associate Variant | KEEP | — | Symbol-digit pairs studied as paired associates; different explicit learning structure |

---

### 22. Directed Forgetting Task (`hedtsk_directed_forgetting`)

Variations: 7

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Item-Method Directed Forgetting | KEEP | — | Forget cue follows each item; individual item suppression |
| 2 | List-Method Directed Forgetting | KEEP | — | Forget cue follows entire first list; list-level suppression |
| 3 | Recognition vs. Recall Test | KEEP | — | Different retrieval test changes what type of access is measured |
| 4 | Directed Forgetting with Source Memory | KEEP | — | Retrieval includes source judgment; adds contextual memory component |
| 5 | Emotional Directed Forgetting | KEEP | — | Emotional to-be-forgotten material; retained per §5.1 (EMOT retired) |
| 6 | Directed Forgetting of Actions (SPT) | KEEP | — | Subject-performed tasks as to-be-forgotten items; different encoding modality |
| 7 | Cumulative Directed Forgetting | KEEP | — | Multiple forget cues accumulate across list; different suppression structure |

---

### 23. Dot-Probe Task (`hedtsk_dot_probe`)

Variations: 6

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard Face Dot-Probe | KEEP | — | Canonical: face pair followed by probe; measures attentional bias to faces |
| 2 | Word Dot-Probe | KEEP | — | Word stimuli instead of faces; different stimulus type |
| 3 | Pictorial Dot-Probe | KEEP | — | Scene/object pictures; different stimulus class |
| 4 | Detection vs. Classification Probe | KEEP | — | Probe identity discrimination vs. simple detection; different response task |
| 5 | Subliminal/Masked Dot-Probe | KEEP | — | Primes below threshold; changes conscious awareness of cue |
| 6 | Positive Dot-Probe | KEEP | — | Positive stimuli as cues; different emotional valence of attention capture stimuli |

---

### 24. Effort-Based Decision-Making Task (`hedtsk_effort_based_decision_making`)

Variations: 7

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | EEfRT (Physical Effort) | KEEP | — | Canonical effort-reward task: grips vs. reward levels |
| 2 | Cognitive Effort Discounting | KEEP | — | Cognitive task difficulty vs. reward; different effort type |
| 3 | Grip-Force Effort Task | KEEP | — | Graded grip force as effort measure; different motor requirement |
| 4 | Effort Discounting Titration | KEEP | — | Adaptive titration of effort-reward indifference points; different method |
| 5 | Progressive Ratio Task | KEEP | — | Escalating effort requirement for each reward; different effort schedule |
| 6 | Demand Selection Task | KEEP | — | Freely choose between high/low demand tasks; choice behavior reveals effort avoidance |
| 7 | Apple-Gathering Task | KEEP | — | Virtual navigation effort for rewards; different effort modality (locomotion) |

---

### 25. Emotion Regulation Task (`hedtsk_emotion_regulation`)

Variations: 9

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Reinterpretation/Reappraisal | KEEP | — | Participant cognitively reframes stimulus meaning; changes cognitive strategy instructions |
| 2 | Distancing/Detachment | KEEP | — | Third-person perspective taking; distinct cognitive strategy |
| 3 | Distraction/Attentional Deployment | KEEP | — | Attention redirected away from stimulus; different regulatory mechanism |
| 4 | Expressive Suppression | KEEP | — | Inhibit visible emotional response; behavioral output regulation |
| 5 | Acceptance/Mindful Awareness | KEEP | — | Non-judgmental observation; different regulatory stance |
| 6 | Situation Selection/Modification | KEEP | — | Choice between stimuli or contexts; different task structure with decision component |
| 7 | Up-Regulation | KEEP | — | Amplify rather than down-regulate emotional response; opposite regulatory direction |
| 8 | Regulation of Positive vs. Negative Emotions | KEEP | — | Valence manipulation changes emotional context of regulation |
| 9 | Implicit Emotion Regulation | KEEP | — | No explicit instruction to regulate; tests implicit regulatory processes |

---

### 26. Emotional Stroop Task (`hedtsk_emotional_stroop`)

Variations: 6

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Threat-Related Emotional Stroop | KEEP | — | Threat words produce interference; canonical emotional Stroop design |
| 2 | Disorder-Specific Variants | KEEP | — | Stimulus set tailored to specific disorder (e.g., spider phobia words); different content domain |
| 3 | Positive vs. Negative Emotional Stroop | KEEP | — | Positive stimuli alongside negative; tests valence symmetry of interference |
| 4 | Pictorial Emotional Stroop | KEEP | — | Emotional pictures instead of words; different stimulus modality |
| 5 | Subliminal Emotional Stroop | KEEP | — | Masked words below awareness; changes conscious access to emotional stimuli |
| 6 | Face-Word Emotional Stroop | KEEP | — | Emotional faces paired with color words; cross-domain emotional conflict |

---

### 27. Eriksen Flanker Task (`hedtsk_eriksen_flanker`)

Variations: 7

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Arrow Flanker (Standard) | KEEP | — | Canonical flanker: central arrow surrounded by congruent/incongruent arrows |
| 2 | Letter Flanker | KEEP | — | Letter stimuli instead of arrows; different S-R mapping and stimulus class |
| 3 | Color Flanker | KEEP | — | Color response with flanking distractors; different response dimension |
| 4 | Emotional Flanker | KEEP | — | Emotional face flankers; retained per §5.1 (EMOT retired) |
| 5 | Numerical Flanker | KEEP | — | Number stimuli with magnitude response; different S-R domain |
| 6 | Proportion-Congruent Flanker | KEEP | — | Varies ratio of congruent to incongruent trials; changes conflict adaptation context per §5.2 |
| 7 | Combined Flanker + Go/No-Go | KEEP | — | Integrated flanker-GNG design; targets response inhibition under conflict |

---

### 28. Face Processing Task (`hedtsk_face_processing`)

Variations: 9

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Faces vs. Objects Block Design | KEEP | — | Localizer with objects as contrast; category-selective activation paradigm |
| 2 | Faces vs. Scrambled Faces | KEEP | — | Scrambled faces as control; tests configural vs. feature processing |
| 3 | Faces vs. Houses | KEEP | — | Houses as non-face object category; standard FFA localizer contrast |
| 4 | Dynamic Face Localizer | KEEP | — | Moving/dynamic faces; different temporal and motion processing demands |
| 5 | Upright vs. Inverted Faces | KEEP | — | Face inversion disrupts configural processing; different perceptual experience |
| 6 | Identity Adaptation | KEEP | — | Adaptation paradigm with identity pairs; different temporal structure |
| 7 | Face Parts (Eyes, Mouth) | KEEP | — | Isolated face regions; participant views different spatial configuration |
| 8 | Familiar vs. Unfamiliar Faces | KEEP | — | Familiarity manipulation changes recognition demand |
| 9 | One-Back or Two-Back Task During Viewing | **DROP** | DUAL | Concurrent n-back added as active task to maintain attention during face localizer; §5.4 dual-task add-on |

---

### 29. Facial Emotion Recognition Task (`hedtsk_facial_emotion_recognition`)

Variations: 8

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Static Ekman Faces (6 basic emotions) | KEEP | — | Canonical categorical recognition with posed expressions |
| 2 | Morphed Intensity | KEEP | — | Continuous emotion intensity gradient; participant categorizes or rates on morph scale |
| 3 | Dynamic Expressions | KEEP | — | Temporally unfolding expressions; different stimulus type with motion information |
| 4 | Microexpression Detection | KEEP | — | Very brief (~40 ms) expressions; different detection difficulty and timing |
| 5 | Emotion-in-Context | KEEP | — | Body or scene context accompanies face; changes integration demands |
| 6 | Expression Matching | KEEP | — | Match-to-sample format; different response structure from labeling |
| 7 | Compound Expressions | KEEP | — | Blended or simultaneous multi-emotion displays; different stimulus category |
| 8 | Dimensional Ratings | KEEP | — | Continuous valence/arousal ratings instead of categorical labels; different response type and scale |

---

### 30. False Belief Task (`hedtsk_false_belief`)

Variations: 11

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Sally-Anne / Change-of-Location | KEEP | — | Classic change-of-location false belief; canonical ToM paradigm |
| 2 | Unexpected Contents (Smarties/Crayon Box) | KEEP | — | Container with unexpected content; different scenario structure |
| 3 | Second-Order False Belief | KEEP | — | Belief about another's belief; higher-order recursive ToM |
| 4 | Diverse Beliefs Task | KEEP | — | Two agents with different beliefs about same object; tests belief diversity understanding |
| 5 | Implicit False Belief (Looking Time) | KEEP | — | Looking time measure of anticipation; no verbal response required |
| 6 | Anticipatory Looking | KEEP | — | Eye-tracking where agent will look; different response modality |
| 7 | Animated Triangles (Heider-Simmel) | KEEP | — | Geometric shapes with attributed mental states; different stimulus and attribution task |
| 8 | Cartoon/Story Vignette Tasks | KEEP | — | Story-based false belief; different presentation format |
| 9 | Belief-Desire Reasoning | KEEP | — | Combines belief and desire attribution; more complex ToM reasoning |
| 10 | Adult False Belief with Reaction Time | KEEP | — | RT version for adults; measures implicit processing speed alongside accuracy |
| 11 | Competitive False Belief (Deception) | KEEP | — | Strategic deception context; tests belief reasoning under competitive motivation |

---

### 31. Feeling-of-Knowing Task (`hedtsk_feeling_of_knowing`)

Variations: 5

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Episodic Feeling-of-Knowing | KEEP | — | FOK for episodic memories; unrecalled episode-specific items |
| 2 | Semantic / General-Knowledge Feeling-of-Knowing | KEEP | — | FOK for semantic facts; different memory system |
| 3 | Cue-Only vs. Cue-Target Paradigm | KEEP | — | Study with or without target; tests whether target exposure affects FOK accuracy |
| 4 | Tip-of-the-Tongue Variant | KEEP | — | TOT state as extreme FOK; different phenomenology and partial information access |
| 5 | Feeling-of-Knowing with Feedback | KEEP | — | Accuracy feedback after recognition test; tests calibration learning |

---

### 32. Finger Tapping Task (`hedtsk_finger_tapping`)

Variations: 7

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Self-Paced Tapping | KEEP | — | Participant taps at preferred rate; measures preferred motor tempo |
| 2 | Auditorily-Paced Tapping | KEEP | — | Synchronize to auditory metronome; different sensorimotor integration |
| 3 | Visually-Paced Tapping | KEEP | — | Synchronize to visual metronome; different sensory modality for pacing |
| 4 | Unimanual vs. Bimanual | KEEP | — | One vs. two hands; bimanual coordination introduces interlimb constraints |
| 5 | Sequential Multi-Finger | KEEP | — | Specific finger sequence rather than single finger; different motor programming |
| 6 | Complex Rhythmic Patterns | KEEP | — | Non-isochronous rhythm; changes temporal structure of tapping |
| 7 | Continuation Paradigm | KEEP | — | External pacing withdrawn mid-task; isolates internal vs. externally guided timing |

---

### 33. Free Recall Task (`hedtsk_free_recall`)

Variations: 8

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Immediate Free Recall (IFR) | KEEP | — | Recall tested immediately after list; canonical free recall |
| 2 | Delayed Free Recall (DFR) | KEEP | — | Filled delay before recall; tests long-term retention |
| 3 | Continual Distractor Free Recall (CDFR) | KEEP | — | Distractors between each item and at end; eliminates recency via distractor |
| 4 | Final Free Recall | KEEP | — | Recall all lists at end of session; tests long-term retention and inter-list organization |
| 5 | Categorized Free Recall | KEEP | — | Semantically categorized lists; tests organizational clustering |
| 6 | Repeated Free Recall | KEEP | — | Same list recalled multiple times; tests learning across trials |
| 7 | Directed Forgetting in Free Recall | KEEP | — | Forget instructions after list learning; suppression measured in free recall |
| 8 | Externalized Free Recall | KEEP | — | Participants report all retrievals including partial/uncertain; different response protocol |

---

### 34. Go/No-Go Task (`hedtsk_go_no_go`)

Variations: 9

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard Go/No-Go | KEEP | — | Canonical: respond to go, withhold to no-go; measures response inhibition |
| 2 | Emotional Go/No-Go | KEEP | — | Emotional stimuli as go/no-go signals; retained per §5.1 (EMOT retired) |
| 3 | Reward/Punishment Go/No-Go | KEEP | — | Monetary outcomes for correct responses; motivation manipulation changes decision context |
| 4 | Probabilistic Go/No-Go | KEEP | — | Probabilistic rather than deterministic stimulus-response rules; different learning structure |
| 5 | Cued Go/No-Go | KEEP | — | Preparatory cue precedes imperative signal; different temporal structure |
| 6 | Flanked Go/No-Go | KEEP | — | Go/no-go signal surrounded by flanking distractors; adds conflict component |
| 7 | Reversal Go/No-Go | KEEP | — | Go/no-go assignments reverse mid-task; tests reversal of inhibitory mappings |
| 8 | Saccadic Go/No-Go | KEEP | — | Eye movement response instead of button press; different response effector |
| 9 | Multi-Stimulus Go/No-Go | KEEP | — | Multiple stimulus categories with different go/no-go rules; more complex rule set |

---

### 35. Heartbeat Detection Task (`hedtsk_heartbeat_detection`)

Variations: 5

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Heartbeat Counting (Schandry) | KEEP | — | Count heartbeats over interval; canonical interoception measure |
| 2 | Heartbeat Discrimination (Whitehead) | KEEP | — | Judge whether tone is synchronous with heartbeat; different detection task |
| 3 | Confidence-Accuracy Paradigm | KEEP | — | Sole confidence-rating exception per §5.5; Garfinkel et al. (2015) interoception model |
| 4 | Interoceptive Attention Manipulation | KEEP | — | Instructions to attend to vs. distract from heartbeat; changes attentional focus |
| 5 | Respiratory Interoception Variant | KEEP | — | Respiratory signals instead of cardiac; different physiological channel |

---

### 36. Imitation-Inhibition Task (`hedtsk_imitation_inhibition`)

Variations: 8

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Classic Finger-Lift Paradigm (Brass et al.) | KEEP | — | Canonical: respond to number cue, observe incongruent finger lift |
| 2 | Kinematic Paradigm (Kilner Task) | KEEP | — | Perform arm movement while observing congruent/incongruent arm; different motor effector |
| 3 | Hand Open/Close Variant | KEEP | — | Open/close hand in response to/despite observed hand action |
| 4 | Animacy Manipulation | KEEP | — | Animate vs. inanimate observed movement; tests social specificity of imitation |
| 5 | Goal-Directed Imitation Variant | KEEP | — | Imitate goal vs. means; tests level of imitative representation |
| 6 | Vocal Stimulus-Response Compatibility | KEEP | — | Vocal response to observed action; different response modality |
| 7 | Controlled Imitation Task (Reverse) | KEEP | — | Instructed to imitate or not; tests explicit voluntary control |
| 8 | Counter-Imitation Training | KEEP | — | Training to suppress imitation; tests plasticity of imitative tendencies |

---

### 37. Implicit Association Task (`hedtsk_implicit_association`)

Variations: 9

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Race IAT | KEEP | — | Canonical IAT measuring race-valence associations |
| 2 | Gender-Science IAT | KEEP | — | Gender-career associations; different conceptual domain |
| 3 | Self-Esteem IAT | KEEP | — | Self-related vs. other category; different self-referential structure |
| 4 | Single-Category IAT (SC-IAT) | KEEP | — | One target category instead of two; different design structure |
| 5 | Brief IAT (BIAT) | KEEP | — | Shorter version with different block structure; distinct published instrument |
| 6 | Go/No-Go Association Task (GNAT) | KEEP | — | Detection response instead of categorization; different response structure |
| 7 | Recoding-Free IAT (IAT-RF) | KEEP | — | Response keys don't change across blocks; removes recoding confound |
| 8 | Personalized IAT (P-IAT) | KEEP | — | Self-relevant exemplars; different stimulus set and personal relevance |
| 9 | Developmental / Child IAT | KEEP | — | Picture-based categories for children; procedure adapted per §5.3 |

---

### 38. Instrumental Conditioning Task (`hedtsk_instrumental_conditioning`)

Variations: 11

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Fixed Ratio (FR) | KEEP | — | Reward after fixed number of responses; canonical ratio schedule |
| 2 | Variable Ratio (VR) | KEEP | — | Reward after variable number of responses; different reinforcement statistics |
| 3 | Fixed Interval (FI) | KEEP | — | First response after fixed time rewarded; different temporal reinforcement structure |
| 4 | Variable Interval (VI) | KEEP | — | Variable time intervals; different temporal unpredictability |
| 5 | Progressive Ratio | KEEP | — | Ratio requirement escalates; measures motivational breakpoint |
| 6 | Concurrent Choice | KEEP | — | Two simultaneously available schedules; choice behavior reveals preference |
| 7 | Two-Stage Decision Task (Daw) | KEEP | — | Two-step Markov decision; measures model-based vs. model-free learning |
| 8 | Devaluation Paradigm | KEEP | — | Outcome devaluation tests goal-directed vs. habitual control; different post-training procedure |
| 9 | Contingency Degradation | KEEP | — | Action-outcome contingency degraded; tests action sensitivity |
| 10 | Outcome-Specific Pavlovian-Instrumental Transfer (PIT) | KEEP | — | Pavlovian CS influences instrumental responding; different multi-phase design |
| 11 | Avoidance Learning | KEEP | — | Response prevents aversive outcome; different valence and contingency structure |

---

### 39. Intentional Binding Task (`hedtsk_intentional_binding`)

Variations: 7

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Libet Clock Method (Standard) | KEEP | — | Canonical: estimate action or tone time on rotating clock |
| 2 | Interval Estimation Method | KEEP | — | Estimate delay between action and outcome; different timing judgment task |
| 3 | Involuntary Action Control (TMS) | KEEP | — | TMS-induced involuntary movement instead of voluntary action; different action type |
| 4 | Outcome Probability Manipulation | KEEP | — | Vary probability that action produces tone; tests contingency on binding |
| 5 | Causal Belief Manipulation | KEEP | — | Instructions manipulate whether action causes outcome; tests belief on binding |
| 6 | Social Intentional Binding | KEEP | — | Another person performs action; tests social extension of binding |
| 7 | Outcome Valence Manipulation | KEEP | — | Aversive vs. pleasant outcomes; tests valence effect on temporal binding |

---

### 40. Iowa Gambling Task (`hedtsk_iowa_gambling`)

Variations: 6

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard IGT | KEEP | — | Canonical four-deck IGT with covert payoff structure |
| 2 | Soochow Gambling Task (SGT) | KEEP | — | Reversed long-run structure; tests frequency vs. magnitude sensitivity |
| 3 | Child Versions | KEEP | — | Simplified decks and stimuli for children; procedure adapted per §5.3 |
| 4 | Extended IGT (150–200 trials) | KEEP | — | Extended trial count; tests learning at longer timescales |
| 5 | IGT with Explicit Probabilities | KEEP | — | Payoff probabilities stated explicitly; changes information structure |
| 6 | Modified Payoff Variants | KEEP | — | Different win/loss schedules; tests sensitivity to schedule structure |

---

### 41. Judgment-of-Learning Task (`hedtsk_judgment_of_learning`)

Variations: 6

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Immediate Judgment-of-Learning | KEEP | — | JOL made immediately after study; foresight-based monitoring |
| 2 | Delayed Judgment-of-Learning | KEEP | — | JOL made after delay; improves accuracy via delayed-JOL effect |
| 3 | Aggregate vs. Item-by-Item Judgments | KEEP | — | Global confidence vs. per-item monitoring; different judgment granularity |
| 4 | Cue-Only vs. Cue-Target Delayed Judgment | KEEP | — | JOL prompted by cue alone vs. cue+target; tests forward vs. backward recall fluency |
| 5 | Self-Regulated Study Paradigm | KEEP | — | Participant allocates study time based on JOL; adds metacognitive control component |
| 6 | Pre-Study Judgment (Ease-of-Learning) | KEEP | — | Judgment made before study; different pre-learning prediction task |

---

### 42. Lexical Decision Task (`hedtsk_lexical_decision`)

Variations: 8

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard Visual LDT | KEEP | — | Canonical: word/nonword judgment to visually presented strings |
| 2 | Auditory LDT | KEEP | — | Auditory presentation; different sensory modality |
| 3 | Masked Priming LDT | KEEP | — | Brief masked prime before target; changes prime awareness |
| 4 | Cross-Modal LDT | KEEP | — | Prime in one modality, target in another; cross-modal priming structure |
| 5 | LDT with Different Nonword Types | KEEP | — | Pseudowords, random letter strings, pseudohomophones; nonword type changes task difficulty |
| 6 | Bilingual LDT | KEEP | — | Targets in two languages; different language switching demand |
| 7 | LDT Megastudies | KEEP | — | Large-scale normed stimulus sets enabling item-level analyses; different methodological scope |
| 8 | Go/No-Go LDT | KEEP | — | Respond to one word class, withhold to another; different response structure |

---

### 43. Mental Rotation Task (`hedtsk_mental_rotation`)

Variations: 7

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Shepard-Metzler 3D Block Figures | KEEP | — | Canonical 3D block figure rotation; depth and perspective rotation |
| 2 | 2D Shape Rotation | KEEP | — | Flat 2D figures; different stimulus complexity and dimensionality |
| 3 | Body Part Rotation (Hand Laterality) | KEEP | — | Hands judged as left/right; embodied rotation via motor imagery |
| 4 | Mirror vs. Identical Discrimination | KEEP | — | Distinguish mirrored from same-orientation figure; different judgment type |
| 5 | Embodied/Motor-Assisted Rotation | KEEP | — | Physical hand rotation accompanies mental rotation; different embodiment condition |
| 6 | Virtual Reality Mental Rotation | KEEP | — | Immersive VR environment; full-body spatial context changes processing |
| 7 | Egocentric vs. Allocentric Rotation | KEEP | — | Participant perspective vs. object-centered rotation; different reference frame |

---

### 44. Mirror Tracing Task (`hedtsk_mirror_tracing`)

Variations: 8

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Star Tracing (Standard) | KEEP | — | Canonical mirror tracing of star with visuomotor reversal |
| 2 | Circle/Diamond/Complex Shapes | KEEP | — | Different shape complexity and curvature demands |
| 3 | Computerized Mirror Tracing | KEEP | — | Screen/stylus instead of physical mirror/pencil; per §5.6, loses haptic edge feedback |
| 4 | Left-Right vs. Up-Down Reversal | KEEP | — | Different mirror axis changes visuomotor mapping |
| 5 | Rotation (Non-Mirror) Variants | KEEP | — | Rotation rather than mirror reversal; different visuomotor transformation |
| 6 | Prism Adaptation Analog | KEEP | — | Prismatic displacement of visual field; different mechanism from mirror reversal |
| 7 | Dual-Hand Mirror Tracing | KEEP | — | Both hands trace simultaneously with mirrored feedback; bimanual coordination variant |
| 8 | Mirror Tracing with Delay | KEEP | — | Delay between practice and test; tests retention of visuomotor adaptation |

---

### 45. Mismatch Negativity Task (`hedtsk_mismatch_negativity`)

Variations: 9

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Frequency MMN | KEEP | — | Frequency deviant in auditory stream; canonical MMN stimulus type |
| 2 | Duration MMN | KEEP | — | Duration deviant; different acoustic dimension |
| 3 | Intensity MMN | KEEP | — | Intensity deviant; tests loudness change detection |
| 4 | Location/Spatial MMN | KEEP | — | Spatial location change; different perceptual dimension |
| 5 | Complex Pattern MMN | KEEP | — | Pattern-level violation; higher-order regularity processing |
| 6 | Multi-Feature MMN (Optimum) | KEEP | — | Multiple deviants in single paradigm; different stimulus sequence |
| 7 | Phoneme/Speech MMN | KEEP | — | Phonemic contrast as deviant; linguistic processing |
| 8 | Visual MMN (vMMN) | KEEP | — | Visual change detection; different sensory modality |
| 9 | Roving Standard MMN | KEEP | — | Standard changes after each sequence; different stimulus history structure |

---

### 46. Mnemonic Similarity Task (`hedtsk_mnemonic_similarity`)

Variations: 7

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard Object MST | KEEP | — | Canonical everyday objects with lure pairs for pattern separation |
| 2 | Scene MST | KEEP | — | Scene stimuli instead of objects; different stimulus class |
| 3 | Continuous MST | KEEP | — | Study and test interleaved; different trial structure |
| 4 | Parametric Similarity Manipulation | KEEP | — | Graded lure similarity levels; tests pattern separation threshold |
| 5 | MST for Faces | KEEP | — | Face stimuli; different recognition domain |
| 6 | Spatial MST | KEEP | — | Location-based similarity; tests spatial pattern separation |
| 7 | Short-Delay vs. Long-Delay MST | KEEP | — | Retention interval manipulation tests forgetting of pattern separation |

---

### 47. Monetary Incentive Delay Task (`hedtsk_monetary_incentive_delay`)

Variations: 6

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard MID (Knutson) | KEEP | — | Canonical cue-anticipation-response structure with monetary reward/punishment |
| 2 | Graded Reward MID | KEEP | — | Multiple reward magnitude levels; tests reward sensitivity parametrically |
| 3 | MID with Social Rewards | KEEP | — | Social stimuli (faces) as rewards instead of money; different incentive type |
| 4 | MID with Drug Cues | KEEP | — | Drug-associated cues as incentive stimuli; different cue content |
| 5 | Passive MID | KEEP | — | No response required; isolates anticipatory processing from motor preparation |
| 6 | MID with Effort Component | KEEP | — | Effort required to obtain reward; adds effort-discounting to incentive structure |

---

### 48. Motor Sequence Learning Task (`hedtsk_motor_sequence_learning`)

Variations: 8

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Discrete Sequence Production (DSP) | KEEP | — | Canonical pre-learned sequence executed rapidly; measures chunking |
| 2 | Serial Reaction Time Task variant | KEEP | — | Implicit learning via RT advantages for repeating sequences |
| 3 | Finger Opposition Task | KEEP | — | Thumb-to-finger opposition sequences; different finger movement type |
| 4 | Bimanual Coordination | KEEP | — | Both hands performing sequences; interlimb coordination demands |
| 5 | Explicit vs. Implicit Sequence Learning | KEEP | — | Aware vs. unaware of sequence structure; different instruction and learning mechanism |
| 6 | Sequence Complexity Manipulation | KEEP | — | Varies sequence length and structure; tests learning as function of complexity |
| 7 | Transfer Tests | KEEP | — | Probe what was learned by testing with modified sequence; different test phase structure |
| 8 | Continuous Tracking + Sequence | KEEP | — | Sequence embedded in continuous tracking; tests incidental learning during ongoing task |

---

### 49. Multi-Armed Bandit Task (`hedtsk_multi_armed_bandit`)

Variations: 9

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Two-Armed Stationary Bandit | KEEP | — | Canonical two-option stationary reward structure; stable payoff distributions |
| 2 | Restless (Volatile) Bandit | KEEP | — | Reward probabilities drift over time; tests tracking of non-stationary environments |
| 3 | Contextual Bandit | KEEP | — | Context features predict optimal choice; adds feature-based learning |
| 4 | Horizon Task (Wilson et al.) | KEEP | — | Fixed horizon with exploration vs. exploitation trade-off manipulation |
| 5 | Four-Armed Bandit with Reversal | KEEP | — | Four arms with explicit reversal phase; tests reversal learning in bandit |
| 6 | Informative vs. Non-Informative Exploration | KEEP | — | Exploration choices yield differential information; changes exploration value |
| 7 | Social Bandit | KEEP | — | Observe another's choices; social learning component |
| 8 | Bandit with Effort Cost | KEEP | — | Effort cost added to choices; combines effort discounting with learning |
| 9 | Bandit with Partial Observability | KEEP | — | Outcomes sometimes hidden; different information structure |

---

### 50. Multiple Object Tracking Task (`hedtsk_multiple_object_tracking`)

Variations: 7

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard MOT | KEEP | — | Canonical: track subset of identical moving dots |
| 2 | Identity-MOT (MIT) | KEEP | — | Track identity features of moving objects; adds identity memory demand |
| 3 | 3D MOT (NeuroTracker) | KEEP | — | Three-dimensional display with depth; different spatial processing |
| 4 | MOT with Occlusion | KEEP | — | Objects temporarily hidden; requires inference of hidden trajectories |
| 5 | Probe-Based MOT | KEEP | — | Probe object after tracking to test spatial knowledge; different response method |
| 6 | Hierarchical MOT | KEEP | — | Nested groups of objects tracked at multiple levels; different attentional structure |
| 7 | Auditory MOT Analogs | KEEP | — | Tracking moving sounds; different sensory modality |

---

### 51. N-Back Task (`hedtsk_n_back`)

Variations: 8

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Verbal N-Back | KEEP | — | Letters or words; phonological working memory |
| 2 | Spatial N-Back | KEEP | — | Locations instead of letters; visuospatial working memory |
| 3 | Emotional N-Back | KEEP | — | Emotional stimuli; retained per §5.1 (EMOT retired) |
| 4 | Dual N-Back | KEEP | — | Simultaneous visual and auditory streams; recognized named paradigm (Jaeggi et al., 2008) |
| 5 | Fractal/Object N-Back | KEEP | — | Complex visual objects; different stimulus type |
| 6 | Adaptive N-Back | KEEP | — | N-level adjusts with performance; changes task difficulty trajectory |
| 7 | N-Back with Lures | KEEP | — | Near-miss stimuli create high interference; changes task demand |
| 8 | Auditory N-Back | KEEP | — | Auditory tones or words; different sensory modality |

---

### 52. Navon Task (`hedtsk_navon`)

Variations: 11

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard Navon (Blocked) | KEEP | — | Canonical blocked global/local judgment of hierarchical figures |
| 2 | Mixed/Cued Navon | KEEP | — | Trial-by-trial cue indicates level; task-switching demand added |
| 3 | Divided Attention Navon | KEEP | — | Respond to both levels simultaneously; different attentional demand |
| 4 | Consistent vs. Inconsistent Stimuli | KEEP | — | Local and global levels same vs. different; conflict manipulation |
| 5 | Sparse vs. Dense Local Elements | KEEP | — | Number of local elements varies; tests density effect on global processing |
| 6 | Emotional Navon | KEEP | — | Emotional faces at global/local level; retained per §5.1 (EMOT retired) |
| 7 | Auditory Navon Analogs | KEEP | — | Hierarchical auditory stimuli; different sensory modality |
| 8 | Navon with Priming | KEEP | — | Preceding prime influences level processing; temporal context manipulation |
| 9 | Lateralized Presentation | KEEP | — | Stimuli presented to one visual field; tests hemispheric contributions |
| 10 | Navon Figures with Shapes | KEEP | — | Non-letter shapes at global/local level; different stimulus class |
| 11 | Temporal Precedence (Brief Exposure) | KEEP | — | Brief exposure tests which level is processed first |

---

### 53. Oddball Task (`hedtsk_oddball`)

Variations: 9

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Two-Stimulus Auditory Oddball | KEEP | — | Canonical: standard + deviant tones; P300 or MMN elicitation |
| 2 | Three-Stimulus Novelty Oddball | KEEP | — | Novel distractors added to standard+deviant; different stimulus structure |
| 3 | Visual Oddball | KEEP | — | Visual stimuli; different sensory modality |
| 4 | Passive Oddball | KEEP | — | No response required; isolates automatic change detection |
| 5 | Active Counting vs. Button-Press Response | KEEP | — | Silent count vs. button press; different response modality |
| 6 | Duration Deviance Oddball | KEEP | — | Duration-based deviant; different acoustic dimension from frequency |
| 7 | Cross-Modal Oddball | KEEP | — | Deviant crosses sensory modality; different cross-modal attention |
| 8 | Emotional Oddball | KEEP | — | Emotional stimuli as deviants; retained per §5.1 (EMOT retired) |
| 9 | Roving Paradigm | KEEP | — | Standard changes after each presentation; different stimulus history structure |

---

### 54. Old/New Recognition Memory Task (`hedtsk_old_new_recognition_memory`)

Variations: 7

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard Old/New | KEEP | — | Canonical yes/no recognition judgment |
| 2 | Remember-Know (R/K) | KEEP | — | Participant distinguishes recollection from familiarity; different response scale |
| 3 | Source Memory | KEEP | — | Identify source context of recognized item; adds contextual retrieval judgment |
| 4 | Associative Recognition | KEEP | — | Judge intact vs. rearranged pairs; tests associative vs. item memory |
| 5 | Forced-Choice Recognition | KEEP | — | Select target from foil array; different response structure |
| 6 | Continuous Recognition | KEEP | — | Study and test interleaved in ongoing stream; different trial structure |
| 7 | DRM (Deese-Roediger-McDermott) False Memory Variant | KEEP | — | Semantically related lures elicit false recognition; distinct false memory paradigm |

---

### 55. Operation Span Task (`hedtsk_operation_span`)

Variations: 6

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Automated OSPAN (AOSPAN) | KEEP | — | Canonical computerized OSPAN with math distractor |
| 2 | Reading Span (RSPAN) | KEEP | — | Sentence comprehension distractor; different processing demand |
| 3 | Symmetry Span (SYMSPAN) | KEEP | — | Spatial symmetry judgment distractor; visuospatial storage component |
| 4 | Counting Span | KEEP | — | Counting shapes distractor; different processing requirement |
| 5 | Shortened OSPAN | KEEP | — | Abbreviated protocol; recognized efficient version for time-limited settings |
| 6 | Adaptive OSPAN | KEEP | — | Adaptive set sizes based on performance; different difficulty trajectory |

---

### 56. Paired Associates Learning Task (`hedtsk_paired_associates_learning`)

Variations: 9

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Verbal Paired Associates (Cued Recall) | KEEP | — | Canonical word-word pairs with cued recall test |
| 2 | Face-Name Paired Associates | KEEP | — | Face-name binding; social memory domain |
| 3 | Object-Location Pairs | KEEP | — | Object-location binding; spatial memory component |
| 4 | CANTAB PAL | KEEP | — | Touchscreen object-location paradigm; named computerized instrument |
| 5 | Arbitrary vs. Semantically Related Pairs | KEEP | — | Relatedness manipulation changes encoding strategy |
| 6 | Cross-Modal Paired Associates | KEEP | — | Pairs span sensory modalities; cross-modal binding demand |
| 7 | Multi-Trial Learning Curves | KEEP | — | Repeated study-test cycles; tests learning rate over trials |
| 8 | Retroactive/Proactive Interference Variants | KEEP | — | Competing pairs introduced; tests interference in associative memory |
| 9 | Incidental vs. Intentional Encoding | KEEP | — | Encoding goal manipulation; tests depth and intentionality of encoding |

---

### 57. Pavlovian Fear Conditioning Task (`hedtsk_pavlovian_fear_conditioning`)

Variations: 12

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Delay Conditioning | KEEP | — | CS and US overlap; canonical associative fear learning |
| 2 | Trace Conditioning | KEEP | — | Trace interval between CS offset and US onset; different temporal structure |
| 3 | Contextual Conditioning | KEEP | — | Context (environment) as CS; different stimulus type |
| 4 | Differential Conditioning (CS+/CS−) | KEEP | — | Two CSs with different US contingencies; adds discrimination demand |
| 5 | Extinction Training | KEEP | — | CS presented without US; tests extinction learning |
| 6 | Extinction Recall | KEEP | — | Test of extinguished fear after delay; different memory phase |
| 7 | Renewal (Context Change) | KEEP | — | Extinguished CS tested in new context; tests context-specificity of extinction |
| 8 | Reinstatement | KEEP | — | Unsignaled US presentations revive extinguished fear; different recovery procedure |
| 9 | Reconsolidation Paradigm | KEEP | — | Reactivation + interference during reconsolidation; different intervention timing |
| 10 | Generalization Gradient | KEEP | — | CS-similar stimuli tested; measures perceptual generalization |
| 11 | Instructed vs. Uninstructed | KEEP | — | Verbal instruction about CS-US relationship; tests instructed vs. experiential fear |
| 12 | Compound CS Conditioning | KEEP | — | CS compound with multiple elements; different stimulus structure |

---

### 58. Phonological Awareness Task (`hedtsk_phonological_awareness`)

Variations: 11

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Rhyme Detection | KEEP | — | Participant judges whether words rhyme; canonical phonological awareness task |
| 2 | Rhyme Oddity | KEEP | — | Identify non-rhyming word in set; different task structure from detection |
| 3 | Rhyme Production | KEEP | — | Generate rhyming words; different output requirement |
| 4 | Onset Detection | KEEP | — | Judge initial consonant; different phonological unit (onset) |
| 5 | Phoneme Deletion | KEEP | — | Delete specified phoneme and report result; manipulation task |
| 6 | Phoneme Substitution | KEEP | — | Replace phoneme in word; different manipulation operation |
| 7 | Phoneme Segmentation | KEEP | — | Segment word into constituent phonemes; decomposition task |
| 8 | Blending | KEEP | — | Combine phonemes to form word; synthesis operation |
| 9 | Spoonerisms | KEEP | — | Transpose onset phonemes of two words; complex transposition manipulation |
| 10 | Alliteration Detection | KEEP | — | Detect shared onset consonant; different phonological judgment |
| 11 | Syllable Awareness Tasks | KEEP | — | Syllable-level operations instead of phoneme-level; different linguistic unit |

---

### 59. Picture Naming Task (`hedtsk_picture_naming`)

Variations: 9

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard Single-Object Naming | KEEP | — | Canonical overt naming to pictured objects |
| 2 | Blocked-Cyclic Naming | KEEP | — | Same items repeat in blocked cycles; cumulative interference paradigm |
| 3 | Continuous Naming | KEEP | — | Rapid successive naming; tests sustained lexical access |
| 4 | Picture-Word Interference (PWI) | KEEP | — | Distractor word accompanies picture; lexical competition paradigm |
| 5 | Delayed Naming | KEEP | — | Delay between picture onset and response signal; isolates planning from execution |
| 6 | Object + Action Naming | KEEP | — | Name actions as well as objects; different grammatical category |
| 7 | Bilingual Picture Naming | KEEP | — | Language cue specifies response language; language control demand |
| 8 | Tip-of-the-Tongue (TOT) Paradigm | KEEP | — | Naming under word-finding difficulty conditions; different metacognitive state |
| 9 | Naming with Phonological/Semantic Cues | KEEP | — | Partial cues provided after TOT; different cueing structure |

---

### 60. Posner Spatial Cueing Task (`hedtsk_posner_spatial_cueing`)

Variations: 11

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Exogenous (Peripheral) Cueing | KEEP | — | Peripheral onset cue drives automatic orienting; canonical exogenous attention |
| 2 | Endogenous (Central) Cueing | KEEP | — | Central arrow cue drives voluntary orienting; different mechanism |
| 3 | Valid, Invalid, and Neutral Cue Conditions | KEEP | — | Three cue validity conditions test benefit and cost of orienting |
| 4 | Inhibition of Return (IOR) Paradigm | KEEP | — | Long SOA reverses validity benefit; distinct temporal structure |
| 5 | Gap vs. Overlap Conditions | KEEP | — | Fixation offset before/during cue changes alerting |
| 6 | Double-Cue Paradigm | KEEP | — | Both locations cued simultaneously; tests alerting without orienting |
| 7 | Predictive vs. Non-Predictive Cues | KEEP | — | Cue validity changes attentional weight given to cue |
| 8 | Feature-Based Cueing | KEEP | — | Feature rather than location cued; tests feature-based attention |
| 9 | Object-Based Cueing | KEEP | — | Object defines cued location; tests object-based attention |
| 10 | Cross-Modal Cueing | KEEP | — | Auditory or tactile cue precedes visual target; cross-modal orienting |
| 11 | Detection vs. Discrimination Targets | KEEP | — | Simple detection vs. identity discrimination; different response task |

---

### 61. Prisoner's Dilemma Task (`hedtsk_prisoners_dilemma`)

Variations: 12

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Single-Shot (One-Round) PD | KEEP | — | Canonical one-round anonymous PD; no reputation effects |
| 2 | Iterated PD (Repeated Games) | KEEP | — | Multiple rounds with same partner; reputation and strategy accumulate |
| 3 | Sequential PD | KEEP | — | One player acts before observing other's choice; different temporal structure |
| 4 | Multiplayer/Public Goods Version | KEEP | — | More than two players; group dilemma structure |
| 5 | PD with Communication | KEEP | — | Players communicate before deciding; cheap talk changes decision context |
| 6 | PD with Punishment Option | KEEP | — | Third-party punishment available; adds enforcement mechanism |
| 7 | PD with Varying Payoff Matrices | KEEP | — | Different temptation/sucker payoffs; tests sensitivity to game parameters |
| 8 | PD against Computer Opponents | KEEP | — | Computer opponent instead of human; per §5.6 structural change (deterministic vs. human partner) |
| 9 | PD with Reputation Information | KEEP | — | Partner's past cooperation history visible; changes social information available |
| 10 | Continuous PD | KEEP | — | Continuous contribution instead of binary; different action space |
| 11 | Asymmetric Prisoner's Dilemma | KEEP | — | Different payoff structures for each player; breaks symmetry of standard PD |
| 12 | Optional Prisoner's Dilemma | KEEP | — | Third option to not participate; changes strategic choice set |

---

### 62. Probabilistic Classification Learning Task (`hedtsk_probabilistic_classification_learning`)

Variations: 7

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard Weather Prediction (4 cues, binary outcome) | KEEP | — | Canonical probabilistic categorization with cue combinations |
| 2 | Deterministic Version | KEEP | — | Cues perfectly predict outcome; removes probabilistic uncertainty |
| 3 | Varying Probability Levels | KEEP | — | Cue-outcome reliability systematically manipulated; different learning statistics |
| 4 | Information-Integration Category Learning | KEEP | — | Categories defined by integration of dimensions; different decision rule |
| 5 | Rule-Based Category Learning (comparison) | KEEP | — | Explicit rule applicable; contrasts implicit vs. explicit learning systems |
| 6 | Feedback vs. Observation Learning | KEEP | — | Active feedback vs. observational learning; different learning mechanism |
| 7 | Transfer Test Variants | KEEP | — | Probe generalization with novel cue combinations; different test phase |

---

### 63. Probabilistic Selection Task (`hedtsk_probabilistic_selection`)

Variations: 5

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard PST (3 Stimulus Pairs) | KEEP | — | Canonical Frank et al. learn-then-test with choose/avoid pairs |
| 2 | Extended Training Versions | KEEP | — | More training trials; tests asymptotic learning |
| 3 | 4-Pair Version | KEEP | — | Additional stimulus pairs; larger choice set |
| 4 | Gain-Only and Loss-Only Variants | KEEP | — | Separate gain vs. loss feedback conditions; isolates approach vs. avoidance learning |
| 5 | PST with Volatility | KEEP | — | Contingencies shift over time; tests learning in non-stationary environment |

---

### 64. Prospective Memory Task (`hedtsk_prospective_memory`)

Variations: 6

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Event-Based PM (Focal Cue) | KEEP | — | PM cue is focal target of ongoing task; different resource demand from non-focal |
| 2 | Event-Based PM (Non-Focal Cue) | KEEP | — | PM cue is non-focal; requires additional monitoring attention |
| 3 | Time-Based PM | KEEP | — | Time check required at specified interval; different PM cue type |
| 4 | Activity-Based PM | KEEP | — | PM intention linked to completing an activity; different cue type |
| 5 | Multiple-Intention PM | KEEP | — | Several PM intentions simultaneously maintained; different load |
| 6 | Naturalistic PM | KEEP | — | Real-world task context instead of lab; different ecological setting |

---

### 65. Psychological Refractory Period Task (`hedtsk_psychological_refractory_period`)

Variations: 6

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard Auditory-Visual PRP | KEEP | — | Canonical PRP: auditory then visual stimulus with variable SOA |
| 2 | Visual-Visual PRP | KEEP | — | Both stimuli visual; tests modality effects on bottleneck |
| 3 | Variable SOA Design | KEEP | — | Multiple SOAs parametrically varied; standard PRP SOA manipulation |
| 4 | PRP with Practice | KEEP | — | Extended practice changes PRP magnitude; tests dual-task automatization |
| 5 | PRP with Ideomotor-Compatible Tasks | KEEP | — | Ideomotor-compatible S-R mappings eliminate bottleneck; tests structural bottleneck theory |
| 6 | Triple-Task PRP | KEEP | — | Three concurrent tasks; extends bottleneck theory to three tasks |

---

### 66. Psychomotor Vigilance Task (`hedtsk_psychomotor_vigilance`)

Variations: 4

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard 10-Minute PVT | KEEP | — | Canonical 10-min RT task with variable ISI |
| 2 | Brief PVT (PVT-B) | KEEP | — | 3-min version; recognized published abbreviated instrument |
| 3 | Palm PVT / Mobile PVT | KEEP | — | Handheld or mobile device; different motor and environmental context |
| 4 | Auditory PVT | KEEP | — | Auditory tone instead of visual stimulus; different sensory modality |

---

### 67. Random Dot Kinematogram Task (`hedtsk_random_dot_kinematogram`)

Variations: 4

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Two-Alternative Forced Choice (Standard) | KEEP | — | Canonical 2AFC motion direction discrimination |
| 2 | Free Response vs. Interrogation Protocol | KEEP | — | Self-paced vs. fixed-duration decision; different temporal control |
| 3 | Pulse Paradigm | KEEP | — | Brief coherence pulses instead of sustained motion; different stimulus structure |
| 4 | Multi-Alternative Motion Discrimination | KEEP | — | More than two motion directions; higher-order discrimination |

---

### 68. Rapid Serial Visual Presentation Task (`hedtsk_rapid_serial_visual_presentation`)

Variations: 13

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Dual-Target Attentional Blink | KEEP | — | Canonical AB: T2 missed when presented shortly after T1 |
| 2 | Single-Target RSVP | KEEP | — | Detect or identify one target in stream; no AB protocol |
| 3 | Emotion-Induced Blindness | KEEP | — | Emotional T1 causes blindness to T2; retained per §5.1 (EMOT retired) |
| 4 | Rapid Scene Categorization | KEEP | — | Categorize natural scenes at rapid presentation rates; different stimulus class |
| 5 | RSVP Image Triage (BCI) | KEEP | — | Brain-computer interface using RSVP for rapid image tagging; different application and response structure |
| 6 | Triple-RSVP (Multiple Streams) | KEEP | — | Three simultaneous streams; different attentional load structure |
| 7 | Whole-Report RSVP | KEEP | — | Report all items seen; different response requirement |
| 8 | RSVP with Task Switch | KEEP | — | Task changes within or between streams; adds switching demand |
| 9 | Detection vs. Identification | KEEP | — | Detect presence vs. identify identity; different judgment type |
| 10 | Three-Target Variant | KEEP | — | Three targets in stream; extends AB to three-target scenario |
| 11 | Cross-Modal Attentional Blink | KEEP | — | T1 and T2 in different modalities; tests cross-modal attentional resources |
| 12 | Emotional Attentional Blink | KEEP | — | Emotional T2; retained per §5.1 (EMOT retired) |
| 13 | Spatial Two-Stream RSVP | KEEP | — | Two streams at different spatial locations; tests spatial attention in RSVP |

---

### 69. Raven's Progressive Matrices Task (`hedtsk_ravens_progressive_matrices`)

Variations: 8

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard Progressive Matrices (SPM) | KEEP | — | Canonical general ability measure |
| 2 | Advanced Progressive Matrices (APM) | KEEP | — | Harder item set for higher ability; different item difficulty range |
| 3 | Colored Progressive Matrices (CPM) | KEEP | — | Colored figures, simpler items for children/elderly; different stimulus format |
| 4 | Computerized Adaptive Version | KEEP | — | Per §5.6: adaptive algorithm changes which items presented; procedural change beyond interface |
| 5 | Matrix Reasoning (WAIS subtest) | KEEP | — | Standardized 26-item version with WAIS norms; named published instrument |
| 6 | Sandia Matrices | KEEP | — | Open-source item set with verified psychometrics; distinct published test |
| 7 | Time-Limited vs. Untimed Administration | KEEP | — | Time pressure changes response strategy and performance profile |
| 8 | Shortened Versions (15-Item) | KEEP | — | Abbreviated protocols validated for efficiency; recognized published short form |

---

### 70. Reading the Mind in the Eyes Task (`hedtsk_reading_the_mind_in_the_eyes`)

Variations: 5

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | RMET Revised (36 items) | KEEP | — | Canonical Baron-Cohen RMET with 36-item set |
| 2 | RMET Short Form (15–18 items) | KEEP | — | Abbreviated form; recognized efficient version |
| 3 | RMET Child Version | KEEP | — | Simplified vocabulary and reduced items for children; adapted per §5.3 |
| 4 | Dynamic Eyes Task | KEEP | — | Moving eyes instead of static photographs; different stimulus type |
| 5 | Full-Face vs. Eyes-Only | KEEP | — | Full face context vs. isolated eyes region; different stimulus scope |

---

### 71. Remember/Know Task (`hedtsk_remember_know`)

Variations: 4

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard Remember/Know | KEEP | — | Canonical R/K: recollection vs. familiarity distinction |
| 2 | Remember/Know/Guess (RKG) | KEEP | — | Third Guess category added; different response scale |
| 3 | Remember/Know with Source Memory | KEEP | — | Source judgment added to R/K; adds contextual memory component |
| 4 | Associative Remember/Know | KEEP | — | R/K for associative pairs; tests recollection of binding |

---

### 72. Remote Associates Task (`hedtsk_remote_associates`)

Variations: 6

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard RAT (Mednick) | KEEP | — | Canonical three-word compound remote associate task |
| 2 | Compound RAT (CRAT) | KEEP | — | Compound word solutions instead of single words; different solution structure |
| 3 | Insight vs. Analytic Solutions | DROP | ANAL | Solution-type categorization is an analytical distinction applied to RAT performance, not a recognized procedural variation of the paradigm |
| 4 | Timed vs. Untimed RAT | KEEP | — | Time pressure changes solving strategy |
| 5 | RAT with Hint/Priming | KEEP | — | Semantic prime precedes problem; changes solution accessibility |
| 6 | Warmth Ratings | DROP | MEAS | Adds a subjective closeness-to-solution rating to the base RAT; measurement add-on, not a recognized variation of the paradigm |

---

### 73. Reversal Learning Task (`hedtsk_reversal_learning`)

Variations: 6

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Deterministic Reversal | KEEP | — | Contingency fully reverses; canonical reversal learning |
| 2 | Probabilistic Reversal | KEEP | — | Stochastic contingency reversal; different uncertainty structure |
| 3 | Serial Reversal | KEEP | — | Multiple reversals in sequence; tests reversal learning rate |
| 4 | Stimulus-Outcome vs. Action-Outcome Reversal | KEEP | — | Reversal of stimulus or action contingency; different associative structure |
| 5 | Multi-Dimensional Reversal | KEEP | — | Reversal involves change in relevant stimulus dimension; more complex |
| 6 | Reward vs. Punishment Reversal | KEEP | — | Valence manipulation changes learning signal |

---

### 74. Rey Auditory Verbal Learning Task (`hedtsk_rey_auditory_verbal_learning`)

Variations: 5

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard RAVLT (List A × 5 + List B + Recall + Delayed Recall) | KEEP | — | Canonical multi-trial verbal learning with interference and delayed recall |
| 2 | Recognition Trial | KEEP | — | Target list embedded in foil words for recognition test; different retrieval task |
| 3 | Shortened RAVLT | KEEP | — | Fewer study trials; recognized abbreviated protocol |
| 4 | Proactive Interference Paradigm | KEEP | — | List B interference on List A recall; tests proactive interference effects |
| 5 | Cued Recall Addition | KEEP | — | Category cues added to recall phase; tests cueing benefit on verbal learning |

---

### 75. Self-Paced Reading Task (`hedtsk_self_paced_reading`)

Variations: 6

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Non-Cumulative (Moving Window) | KEEP | — | Canonical word-by-word presentation without previous words visible |
| 2 | Cumulative Self-Paced Reading | KEEP | — | Words accumulate on screen; different visual context during reading |
| 3 | Phrase-by-Phrase Presentation | KEEP | — | Phrases instead of words; different chunking of presentation |
| 4 | Maze Task | KEEP | — | Word-by-word forced choice between correct and anomalous continuation; different response structure |
| 5 | Cross-Modal Self-Paced Listening | KEEP | — | Auditory presentation instead of visual; different sensory modality |
| 6 | Passage-Level Self-Paced Reading | KEEP | — | Full passages instead of sentences; different text-level processing |

---

### 76. Self-Referential Encoding Task (`hedtsk_self_referential_encoding`)

Variations: 6

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard Trait Adjective Encoding | KEEP | — | Canonical: judge whether adjective describes self; incidental encoding |
| 2 | Positive/Negative Valence Split | KEEP | — | Valence-matched sets tested separately; tests self-relevance by valence |
| 3 | Close vs. Distant Other-Reference | KEEP | — | Encoding with reference to close vs. distant others; tests reference specificity |
| 4 | Incidental vs. Intentional Encoding | KEEP | — | Explicit memory instruction vs. incidental; changes encoding goal |
| 5 | Endorsement-Only (No Memory Test) | KEEP | — | Task without memory test phase; tests self-referential processing in isolation |
| 6 | Source Memory for Self-Encoded Items | KEEP | — | Retrieval includes source judgment for self vs. other items; adds source component |

---

### 77. Semantic Priming Task (`hedtsk_semantic_priming`)

Variations: 12

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Short SOA (< 250 ms) | KEEP | — | Brief prime-target interval; automatic spreading activation |
| 2 | Long SOA (> 500 ms) | KEEP | — | Long interval; strategic processing contributes |
| 3 | Masked Priming | KEEP | — | Prime below awareness; unconscious semantic activation |
| 4 | Relatedness Proportion Manipulation | KEEP | — | Varies proportion of related pairs; changes strategic context |
| 5 | Semantic Relation Types | KEEP | — | Taxonomic vs. thematic vs. associative relations; different prime-target relationships |
| 6 | Mediated Priming | KEEP | — | Prime activates mediator that activates target; tests spread of activation |
| 7 | Cross-Modal Priming | KEEP | — | Auditory prime + visual target; cross-modal semantic activation |
| 8 | Sentence Context Priming | KEEP | — | Sentence prime instead of single word; higher-level context |
| 9 | Picture-Word Priming | KEEP | — | Picture prime for word target; conceptual rather than lexical priming |
| 10 | Morphological Priming | KEEP | — | Morphologically related prime; tests morphological representation |
| 11 | Phonological Priming | KEEP | — | Phonologically similar prime; tests phonological overlap effects |
| 12 | Orthographic Priming | KEEP | — | Orthographically similar prime; tests spelling overlap effects |

---

### 78. Sentence Comprehension Task (`hedtsk_sentence_comprehension`)

Variations: 7

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Self-Paced Reading (Word-by-Word) | KEEP | — | Canonical sentence processing paradigm with reading time measure |
| 2 | Eye-Tracking Reading | KEEP | — | Natural reading with eye-tracking; different response modality and richer time course |
| 3 | Main Verb/Reduced Relative Ambiguity | KEEP | — | Syntactic ambiguity at main verb/relative clause; canonical garden path structure |
| 4 | PP-Attachment Ambiguity | KEEP | — | Prepositional phrase attachment ambiguity; different syntactic decision point |
| 5 | NP/S Ambiguity | KEEP | — | Noun phrase vs. sentence ambiguity; different structural ambiguity type |
| 6 | Temporarily Ambiguous vs. Unambiguous Controls | KEEP | — | Matched unambiguous controls; tests processing cost of ambiguity |
| 7 | Speed-Accuracy Tradeoff (SAT) Studies | KEEP | — | Response deadline method; different temporal measurement approach |

---

### 79. Serial Reaction Time Task (`hedtsk_serial_reaction_time`)

Variations: 7

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Deterministic SRTT | KEEP | — | Fixed repeating sequence; canonical implicit sequence learning |
| 2 | Probabilistic SRTT | KEEP | — | High-probability sequence structure; tests learning under uncertainty |
| 3 | Alternating Serial Reaction Time (ASRT) | KEEP | — | Alternating random and patterned elements; tests learning of alternating structure |
| 4 | SRTT with Awareness Assessment | KEEP | — | Explicit sequence knowledge probed after implicit learning; adds awareness component |
| 5 | Second-Order Conditional (SOC) Sequences | KEEP | — | Each response depends on two preceding; different sequence order |
| 6 | Arm-Reaching/Foot-Stepping SRTT | KEEP | — | Full-limb movements instead of finger presses; different motor effector |
| 7 | Cross-Modal SRTT | KEEP | — | Auditory sequence instead of visual; different sensory modality |

---

### 80. Simon Task (`hedtsk_simon`)

Variations: 10

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Visual Simon Task (Standard) | KEEP | — | Canonical: respond to color/shape despite irrelevant spatial position |
| 2 | Auditory Simon Task | KEEP | — | Auditory stimulus location as irrelevant dimension; different sensory modality |
| 3 | Vertical Simon Task | KEEP | — | Vertical rather than horizontal spatial dimension; different axis of conflict |
| 4 | Simon Task with Accessory Stimuli | KEEP | — | Non-response-relevant accessory stimulus added; tests alerting-compatibility interaction |
| 5 | Reversed Simon Task | KEEP | — | Stimulus-response mapping reversed; opposite compatibility mapping |
| 6 | Joint Simon Task | KEEP | — | Two participants share one Simon task; tests social simulation of co-actor's response |
| 7 | Hybrid Simon-Flanker Task | KEEP | — | Integrates flanker conflict with Simon conflict; combined interference paradigm |
| 8 | Emotional Simon Task | KEEP | — | Emotional content as irrelevant dimension; retained per §5.1 (EMOT retired) |
| 9 | Mouse-Tracking Simon | KEEP | — | Continuous mouse trajectory as response; different response modality |
| 10 | Simon with Proportion-Congruent Manipulation | KEEP | — | Varies conflict frequency; adaptation context manipulation per §5.2 |

---

### 81. Social Incentive Delay Task (`hedtsk_social_incentive_delay`)

Variations: 5

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard SID (Smiling Face Reward) | KEEP | — | Canonical SID with face as social incentive |
| 2 | SID with Personalized Social Stimuli | KEEP | — | Stimuli customized to individual's social network; different stimulus content |
| 3 | SID vs. MID within-Subjects | KEEP | — | Both social and monetary incentives in same session; direct contrast paradigm |
| 4 | SID with Graded Social Reward | KEEP | — | Multiple social reward magnitudes; tests social reward sensitivity |
| 5 | SID with Real Social Interaction | KEEP | — | Actual social partner rather than photograph; different social context |

---

### 82. Source Memory Task (`hedtsk_source_memory`)

Variations: 8

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Voice Source Monitoring | KEEP | — | Speaker identity as source attribute; canonical source monitoring |
| 2 | Spatial Source Monitoring | KEEP | — | Location as source attribute; different source dimension |
| 3 | Temporal Source Monitoring | KEEP | — | Time of occurrence as source; different temporal memory dimension |
| 4 | Reality Monitoring | KEEP | — | Internal vs. external origin judgment; distinct reality monitoring paradigm |
| 5 | Internal Source Monitoring | KEEP | — | Self-generated vs. experimenter-presented items; different internal/external distinction |
| 6 | Modality Source Monitoring | KEEP | — | Auditory vs. visual presentation as source; different sensory source |
| 7 | Encoding Task Source Monitoring | KEEP | — | Which encoding task was used as source; different procedural context |
| 8 | Multi-Source (3+ Sources) | KEEP | — | Three or more source attributes; higher discrimination demand |

---

### 83. Sternberg Item Recognition Task (`hedtsk_sternberg_item_recognition`)

Variations: 5

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Visual Sternberg | KEEP | — | Canonical memory set presented visually; recognition probe after delay |
| 2 | Auditory Sternberg | KEEP | — | Auditory memory set; different sensory modality |
| 3 | Cross-Modal Sternberg | KEEP | — | Study in one modality, test in another; cross-modal recognition |
| 4 | Sternberg with Irrelevant Items | KEEP | — | Distractors added during retention; tests interference resistance |
| 5 | Recent-Probes Sternberg | KEEP | — | Probes match previous trials; tests proactive interference |

---

### 84. Stop-Signal Task (`hedtsk_stop_signal`)

Variations: 8

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard SST with Staircase SSD | KEEP | — | Canonical adaptive stop-signal delay tracking |
| 2 | Fixed SSD Procedure | KEEP | — | Non-adaptive fixed delays; different trial structure |
| 3 | Stop-Change Task | KEEP | — | Stop signal replaced by change signal; different inhibition-and-substitute |
| 4 | Selective Stop-Signal | KEEP | — | Stop signal applies to one response type only; selective inhibition |
| 5 | Proactive vs. Reactive Inhibition Manipulation | KEEP | — | Pre-signal preparatory inhibition vs. post-signal reactive; different inhibition timing |
| 6 | Stop-Signal in Reaching/Saccade Tasks | KEEP | — | Arm reaching or eye movement response; different motor effector |
| 7 | Context-Dependent Stop-Signal | KEEP | — | Stop signal context varies; tests context-sensitive inhibition |
| 8 | Conditional Stop-Signal | KEEP | — | Inhibit only under specific conditions; conditional stopping logic |

---

### 85. Stroop Color-Word Task (`hedtsk_stroop_color_word`)

Variations: 12

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Classic Color-Word Stroop | KEEP | — | Canonical color naming of congruent/incongruent color words |
| 2 | Manual (Button-Press) Stroop | KEEP | — | Button press instead of vocal response; different response modality |
| 3 | Vocal Response Stroop | KEEP | — | Vocal naming; distinct from manual version |
| 4 | Counting Stroop | KEEP | — | Count number of words instead of naming color; different task dimension |
| 5 | Spatial Stroop | KEEP | — | Spatial word/location conflict; different conflict dimension |
| 6 | Numerical Stroop | KEEP | — | Number magnitude vs. physical size conflict; different domain |
| 7 | Reverse Stroop | KEEP | — | Name the word rather than the color; reversed task demand |
| 8 | Proportion-Congruent Manipulation | KEEP | — | Conflict frequency variation; adaptation context per §5.2 |
| 9 | Face-Word Stroop | KEEP | — | Face emotion vs. color word conflict; different stimulus domain |
| 10 | Color-Shape Stroop | KEEP | — | Color word/shape conflict instead of ink color; different conflict structure |
| 11 | Priming Stroop | KEEP | — | Prime precedes Stroop item; temporal context manipulation |
| 12 | Negative Priming Stroop | KEEP | — | Previously ignored item becomes target; tests ignored repetition effect |

---

### 86. Sustained Attention to Response Task (`hedtsk_sustained_attention_to_response`)

Variations: 8

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard SART (Fixed Sequence) | KEEP | — | Canonical: respond to digits except 3; fixed pseudo-random sequence |
| 2 | Random SART | KEEP | — | Random digit order; removes sequential predictability |
| 3 | SART with Thought Probes | KEEP | — | Mind-wandering probes inserted; adds metacognitive reporting |
| 4 | Perceptual SART | KEEP | — | Perceptual variants (lines, shapes); different stimulus type |
| 5 | Sustained Attention Task with Response Switching | KEEP | — | Response switches during task; adds rule-change demand |
| 6 | SART with Multiple Targets | KEEP | — | Multiple no-go digits instead of one; different inhibition load |
| 7 | Sustained Attention with Clock Task | KEEP | — | Clock face rather than digit sequence; different stimulus format |
| 8 | Child-Adapted SART | KEEP | — | Modified timing and stimuli for children; adapted per §5.3 |

---

### 87. Task Switching Task (`hedtsk_task_switching`)

Variations: 10

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Cued Task-Switching | KEEP | — | Canonical cue specifies task each trial |
| 2 | Alternating Runs (AABB) | KEEP | — | Predictable alternation without explicit cue; different task structure |
| 3 | Voluntary Task Switching | KEEP | — | Participant chooses task; measures voluntary switching rates |
| 4 | Mixing Cost Paradigm | KEEP | — | Compares mixed-block to pure-block performance; different block structure |
| 5 | Cue-Stimulus Interval (CSI) Manipulation | KEEP | — | Varies preparation time; tests proactive preparation |
| 6 | Response-Stimulus Interval (RSI) Manipulation | KEEP | — | Varies post-response interval; tests backward inhibition decay |
| 7 | Task Switching with N>2 Tasks | KEEP | — | Three or more tasks; different reconfiguration demands |
| 8 | Univalent vs. Bivalent Stimuli | KEEP | — | Stimuli compatible with one vs. both tasks; different interference structure |
| 9 | Predictable vs. Random Task Sequences | KEEP | — | Known vs. unknown switch sequence; tests preparation strategies |
| 10 | Task Switching with Conflict | KEEP | — | Bivalent stimuli with competing responses; combined switching and conflict |

---

### 88. Think/No-Think Task (`hedtsk_think_no_think`)

Variations: 6

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard Think/No-Think (TNT) | KEEP | — | Canonical Anderson & Green: cue-directed recall suppression |
| 2 | Independent Probe Test | KEEP | — | Test with novel cues not seen in TNT phase; isolates suppression from retrieval practice |
| 3 | TNT with Intrusion Reporting | KEEP | — | Participant signals intrusions during no-think; adds metacognitive monitoring report |
| 4 | Emotional TNT | KEEP | — | Emotional paired associates; retained per §5.1 (EMOT retired) |
| 5 | TNT with Thought Substitution | KEEP | — | Replace suppressed thought with substitute; different suppression strategy |
| 6 | Dose-Response TNT | KEEP | — | Varies number of suppression repetitions; tests suppression as function of dose |

---

### 89. Tower of London Task (`hedtsk_tower_of_london`)

Variations: 6

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard Tower of London (3 pegs, 3 balls) | KEEP | — | Canonical Shallice ToL: rearrange colored balls across pegs |
| 2 | Tower of Hanoi | KEEP | — | Different rule structure (disk size constraint); distinct classic puzzle |
| 3 | Tower of London – Drexel (TOL-DX) | KEEP | — | Standardized 10-item version with normative data; published clinical instrument |
| 4 | Tower of London – Freiburg (TOL-F) | KEEP | — | Computer version with different item set and constraints |
| 5 | Computerized vs. Physical Versions | KEEP | — | Per §5.6: grasping 3D beads vs. drag-and-drop changes motor activity |
| 6 | Tower with Time Pressure | KEEP | — | Response deadline imposed; changes planning strategy |

---

### 90. Trail Making Task (`hedtsk_trail_making`)

Variations: 6

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | TMT-A (Number Sequencing) | KEEP | — | Canonical: connect numbers in order; processing speed measure |
| 2 | TMT-B (Number-Letter Alternation) | KEEP | — | Alternating numbers and letters; adds cognitive flexibility demand |
| 3 | Oral Trail Making Test | KEEP | — | Verbal response instead of pencil tracing; different response modality |
| 4 | Color Trails Test | KEEP | — | Color-coded circles instead of letters; tests same construct in different format |
| 5 | Comprehensive Trail Making Test (CTMT) | KEEP | — | Extended standardized version with additional subtests; named published instrument |
| 6 | D-KEFS Trail Making | KEEP | — | Delis-Kaplan version with additional conditions; named published instrument |

---

### 91. Trust Game Task (`hedtsk_trust_game`)

Variations: 7

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard Two-Stage Trust Game | KEEP | — | Canonical Berg et al.: investor sends, trustee returns |
| 2 | One-Shot vs. Repeated | KEEP | — | Single vs. multiple rounds; repeated play enables reputation building |
| 3 | Multiplier Variation | KEEP | — | Different multiplication factors; changes investment incentive |
| 4 | Trust Game with Reputation | KEEP | — | Trustee reputation history visible; changes available social information |
| 5 | Partner Selection Trust Game | KEEP | — | Participant selects partner before trust game; adds partner choice |
| 6 | Anonymous vs. Face-to-Face | KEEP | — | Social identification manipulation changes accountability |
| 7 | Social Identity Manipulation | KEEP | — | In-group vs. out-group trustee; tests trust as function of group membership |

---

### 92. Two-Stage Decision Task (`hedtsk_two_stage_decision`)

Variations: 5

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard Daw et al. (2011) Version | KEEP | — | Canonical two-step Markov decision task; measures model-based vs. model-free |
| 2 | Shortened/Simplified Versions | KEEP | — | Fewer trials or simplified state structure; recognized efficient version |
| 3 | Enhanced Model-Based Version | KEEP | — | Design features that enhance model-based learning; different incentive structure |
| 4 | Devaluation Manipulation | KEEP | — | Reward devalued after training; tests habitual vs. goal-directed control |
| 5 | Two-Stage with Instructed Knowledge | KEEP | — | Transition structure explicitly taught; tests instructed vs. learned model |

---

### 93. Ultimatum Game Task (`hedtsk_ultimatum_game`)

Variations: 9

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard Ultimatum | KEEP | — | Canonical: proposer offers split, responder accepts/rejects |
| 2 | Strategy Method | KEEP | — | Responder states acceptance threshold for all possible offers; different elicitation |
| 3 | Multi-Round Ultimatum | KEEP | — | Repeated rounds; tests learning and adaptation |
| 4 | Third-Party Punishment | KEEP | — | Observer can punish unfair proposer; adds external enforcement |
| 5 | Proposer Competition | KEEP | — | Multiple proposers compete for responder; changes market structure |
| 6 | Asymmetric Information | KEEP | — | Responder does not know pie size; different information structure |
| 7 | Stake Variation | KEEP | — | Systematically varies total pie size; tests stake sensitivity |
| 8 | Anonymous vs. Identified Partners | KEEP | — | Social identification changes accountability |
| 9 | Ultimatum with Earned vs. Windfall Endowment | KEEP | — | Endowment from effort vs. luck; changes perceived legitimacy |

---

### 94. Useful Field of View Task (`hedtsk_useful_field_of_view`)

Variations: 4

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Subtest 1: Central Processing Speed | KEEP | — | Central target discrimination; measures processing speed component |
| 2 | Subtest 2: Divided Attention | KEEP | — | Central + peripheral target; divided attention component |
| 3 | Subtest 3: Selective Attention | KEEP | — | Peripheral target with distractors; selective attention component |
| 4 | UFOV with Varying Eccentricities | KEEP | — | Peripheral target at different distances; tests eccentricity function |

---

### 95. Verb Generation Task (`hedtsk_verb_generation`)

Variations: 6

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard Overt Verb Generation | KEEP | — | Canonical Petersen et al.: say verb aloud in response to noun |
| 2 | Covert Verb Generation | KEEP | — | Internal silent generation; different response mode |
| 3 | High vs. Low Selection Demand | KEEP | — | Dominant vs. non-dominant verb associations; tests selection difficulty |
| 4 | Verb Generation with Practice | KEEP | — | Repeated generation reduces demand; tests automatization |
| 5 | Noun Generation (Reverse) | KEEP | — | Generate noun to verb cue; reversed direction |
| 6 | Written Verb Generation | KEEP | — | Written response instead of vocal; different response modality |

---

### 96. Verbal Fluency Task (`hedtsk_verbal_fluency`)

Variations: 6

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Phonemic / Letter Fluency (FAS) | KEEP | — | Generate words by initial letter; canonical phonemic fluency |
| 2 | Semantic / Category Fluency | KEEP | — | Generate words from category; different retrieval strategy and structure |
| 3 | Action / Verb Fluency | KEEP | — | Generate verbs/actions; different grammatical category |
| 4 | Switching Fluency | KEEP | — | Alternate between two categories; adds cognitive flexibility demand |
| 5 | Design Fluency | KEEP | — | Draw novel designs instead of words; different modality |
| 6 | Excluded-Letter Fluency | KEEP | — | Generate words avoiding a letter; adds constraint that changes retrieval strategy |

---

### 97. Virtual Morris Water Maze Task (`hedtsk_virtual_morris_water_maze`)

Variations: 9

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Hidden Platform (Allocentric) | KEEP | — | Canonical allocentric navigation to hidden platform using distal cues |
| 2 | Visible Platform (Cue-Based) | KEEP | — | Platform marked visibly; cue-based navigation without spatial learning |
| 3 | Probe Trials | KEEP | — | Platform removed; tests memory for trained location |
| 4 | Reversal | KEEP | — | Platform moved to opposite quadrant; tests behavioral flexibility |
| 5 | Dual-Solution Design | KEEP | — | Landmark and allocentric routes both available; tests strategy preference |
| 6 | Virtual Star Maze | KEEP | — | Star-shaped corridors in VR; different maze geometry |
| 7 | Path Integration Tasks | KEEP | — | Navigation without visual landmarks; dead reckoning demand |
| 8 | Large-Scale Virtual Cities | KEEP | — | City-scale environment; different scale and complexity |
| 9 | Boundary-Based vs. Landmark-Based Navigation | KEEP | — | Systematically varies cue type; tests geometric vs. landmark navigation |

---

### 98. Virtual Radial Arm Maze Task (`hedtsk_virtual_radial_arm_maze`)

Variations: 9

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard 8-Arm Radial Maze | KEEP | — | Canonical 8-arm maze with bait at end of each arm |
| 2 | Partially Baited Maze (4 of 8) | KEEP | — | Only subset of arms baited; tests working memory for visited arms |
| 3 | 12-Arm or 16-Arm Versions | KEEP | — | Increased arm number; higher memory load |
| 4 | Virtual Reality (Immersive VR) | KEEP | — | Head-mounted display VR; full immersive spatial navigation |
| 5 | Desktop Virtual Maze | KEEP | — | Screen-based navigation; different motor control |
| 6 | Maze with Landmarks | KEEP | — | Salient landmarks aid navigation; tests landmark use |
| 7 | Cue-Removed Conditions | KEEP | — | Landmarks removed mid-experiment; tests spatial memory without cues |
| 8 | Delay Variants | KEEP | — | Delay between choices tests retention |
| 9 | Probabilistic Reward Maze | KEEP | — | Arms probabilistically rather than deterministically rewarded |

---

### 99. Visual Masking Task (`hedtsk_visual_masking`)

Variations: 10

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard Metacontrast Masking | KEEP | — | Canonical metacontrast: annular mask suppresses disc |
| 2 | Phosphene Detection at Threshold | KEEP | — | TMS-evoked phosphenes measured at perceptual threshold |
| 3 | TMS-Evoked Phosphene Detection | KEEP | — | Visual cortex stimulation produces phosphene; different masking mechanism |
| 4 | Object Substitution Masking | KEEP | — | Four-dot surround mask replaces object representation; different mechanism |
| 5 | Pattern Masking at Threshold | KEEP | — | Pattern mask overlapping in space and time; different mask type |
| 6 | Continuous Flash Suppression Threshold | KEEP | — | Monocular suppression by rapidly alternating masks; binocular suppression paradigm |
| 7 | Rhythmic Entrainment + Detection | KEEP | — | Rhythmic stimulation before target; tests oscillatory effects on detection |
| 8 | Masked Priming Variant | KEEP | — | Masked prime before target; tests subliminal priming via masking |
| 9 | Backward Masking with Attentional Manipulation | KEEP | — | Attention directed during masking; tests attentional modulation of masking |
| 10 | Auditory Backward Masking | KEEP | — | Auditory masking paradigm; different sensory modality |

---

### 100. Visual Search Task (`hedtsk_visual_search`)

Variations: 12

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Feature Search (Pop-Out) | KEEP | — | Canonical preattentive pop-out; target defined by single feature |
| 2 | Conjunction Search | KEEP | — | Target defined by conjunction of features; requires serial search |
| 3 | Spatial Configuration Search | KEEP | — | Learned spatial configuration guides search; contextual cueing component |
| 4 | Efficient vs. Inefficient Search | **DROP** | ANAL | Post-hoc categorization by search slope (ms/item); no distinct experimental procedure |
| 5 | Absent Trials and Target-Present/Absent Ratio | KEEP | — | Systematically varies target presence probability; changes decision criteria |
| 6 | Multiple-Target Search (Foraging) | KEEP | — | Multiple targets per display; foraging paradigm with different decision structure |
| 7 | Real-World/Naturalistic Search | KEEP | — | Natural scenes as search arrays; different stimulus class and recognition demands |
| 8 | Guided Search Variants | KEEP | — | Top-down feature guidance provides target template; changes attentional control |
| 9 | Additional-Singleton Paradigm | KEEP | — | Color singleton distractor captures attention; distinct capture paradigm |
| 10 | Preview Search | KEEP | — | Subset of items previewed before search display; different temporal structure |
| 11 | Adaptive Choice Visual Search | KEEP | — | Participant chooses between search types; tests cost-benefit of different strategies |
| 12 | Hybrid Search (Visual + Memory) | KEEP | — | Memory set held while visual search proceeds; combined memory-search paradigm |

---

### 101. Wason Selection Task (`hedtsk_wason_selection`)

Variations: 8

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Abstract Wason Task (Standard) | KEEP | — | Canonical abstract conditional reasoning; select cards to test rule |
| 2 | Thematic/Concrete Versions | KEEP | — | Concrete familiar content; tests facilitation of abstract reasoning |
| 3 | Social Contract Versions | KEEP | — | Cheater-detection framing; different evolutionary content domain |
| 4 | Precaution Rules | KEEP | — | Safety precaution framing; different pragmatic rule type |
| 5 | Deontic vs. Indicative Rules | KEEP | — | Permission/obligation vs. descriptive conditional; different rule semantics |
| 6 | Negated Rules | KEEP | — | Negation in conditional changes logical structure |
| 7 | Probabilistic Selection Task | KEEP | — | Probabilistic card selection instead of binary; different decision format |
| 8 | Wason 2-4-6 Task (Related) | KEEP | — | Hypothesis-testing number sequence task; related reasoning paradigm |

---

### 102. Weapons Identification Task (`hedtsk_weapons_identification`)

Variations: 3

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard Weapons Identification (Payne, 2001) | DROP | ALIA | Minor alias for the canonical task; restates the core procedure without adding a distinct variation |
| 2 | First-Person Shooter Task (Correll et al., 2002) | KEEP | — | Video-game format shooter task; different motor response and scenario structure |
| 3 | Weapons Task in Virtual Reality | KEEP | — | Immersive VR environment; full-body spatial and motor engagement |

---

### 103. Wisconsin Card Sorting Task (`hedtsk_wisconsin_card_sorting`)

Variations: 7

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | Standard WCST (128 Cards) | KEEP | — | Canonical 128-card version with shifting sorting rules |
| 2 | Short Form WCST (64 Cards) | KEEP | — | 64-card abbreviated version; recognized efficient form |
| 3 | Modified WCST with Explicit Cues | KEEP | — | Explicit cues about sorting dimension; tests rule use vs. rule discovery |
| 4 | Berg Card Sorting Test | KEEP | — | Simplified precursor with fewer cards and dimensions; named related instrument |
| 5 | Intra-/Extra-Dimensional Set Shifting (IED) | KEEP | — | CANTAB analog with distinct dimension-shifting structure; different stimuli and shift types |
| 6 | Reversal-Only WCST | KEEP | — | Only reversal phase; isolates reversal from acquisition |
| 7 | Probabilistic WCST | KEEP | — | Sorting feedback probabilistic rather than deterministic; different uncertainty structure |

---

## DROPs by category (newly flagged only)

| Code | Count | Examples (task — variation) |
|------|-------|-----------------------------|
| MEAS | 2 | Digit Symbol Substitution Task — Incidental Learning Recall; Remote Associates Task — Warmth Ratings |
| ANAL | 2 | Visual Search Task — Efficient vs. Inefficient Search; Remote Associates Task — Insight vs. Analytic Solutions |
| ALIA | 2 | Weapons Identification Task — Standard Weapons Identification (Payne, 2001); Attention Network Task — Clinical Screening ANT (also add to ANT aliases) |
| DUAL | 1 | Face Processing Task — One-Back or Two-Back Task During Viewing |

Total newly flagged DROPs: 7

---

## Items for user review

All items resolved. No open review items remain.

All five flagged items were resolved by user decision on 2026-04-21 and are reflected in the per-task tables and DROPs-by-category table above. Clinical Screening ANT (Attention Network Task) is DROP(ALIA) and is also to be added to the ANT `aliases` array in task_details.json.
