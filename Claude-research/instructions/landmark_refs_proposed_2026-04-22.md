# Proposed landmark reference list — for review

**Date:** 2026-04-22
**Purpose:** Expanded hand-curated list of foundational citations per process
/ task id, per §7.3 of `literature_search_plan_2026-04-21.md`. This is the
draft to be reviewed before Phase 2 triage runs. After sign-off, this file
will be serialized to `outputs/literature_search/landmark_refs.json` for
programmatic use.

Total entries in this draft: **172** (80 processes × 1 landmark each; 92
tasks × 1 landmark each). A number of processes (~92) have no entry by
design — see §4.

---

## 1. Criteria applied

An entry earns landmark status if it meets at least one:

1. **Origin paper** — the work that named the construct or introduced the task.
2. **Canonical modern review** — the integrative review textbooks cite.
3. **Method-defining paper** — the paper that introduced the analytical /
   computational framework now inseparable from the construct.

Explicitly excluded (per user rules 2026-04-22):
- Test manuals (WAIS, WMS, IAPS normative ratings).
- Citation-count-based inclusion.
- Processes where no clear landmark exists (see §4 — left blank by design).
- **General textbooks and book chapters.** Dedicated monographs on
  tightly-related concepts are eligible in principle, but none in this
  draft are retained on that basis (the one borderline case, O'Keefe &
  Nadel 1978, was replaced with a journal alternative). §5 records the
  13 book/chapter substitutions made.

Where I had to choose between "the original 1950s paper" and "the modern
integrative review," I prefer the review when the original is either a
dissertation, a pre-DOI report, or a textbook chapter. Where the original
is a genuinely flagship-journal paper (Stroop 1935, Sperling 1960,
Sternberg 1966), the original wins.

Confidence is flagged per entry: **[H]** high (well-known canonical),
**[M]** medium (good candidate but the field has alternatives), **[L]** low
(my best guess; please verify or replace).

---

## 2. Process landmarks

### 2.1 Associative Learning and Reinforcement

| process_id | Citation | Title and venue | Confidence |
|---|---|---|---|
| hed_associative_learning | Rescorla (1988) | "Behavioral studies of Pavlovian conditioning." *Annu Rev Neurosci* 11:329–352 | H |
| hed_extinction | Bouton (2004) | "Context and behavioral processes in extinction." *Learn Mem* 11:485–494 | H |
| hed_goal_directed_behavior | Dickinson (1985) | "Actions and habits: the development of behavioural autonomy." *Philos Trans R Soc Lond B* 308:67–78 | H |
| hed_habit | Graybiel (2008) | "Habits, rituals, and the evaluative brain." *Annu Rev Neurosci* 31:359–387 | H |
| hed_instrumental_conditioning | Balleine & O'Doherty (2010) | "Human and rodent homologies in action control: corticostriatal determinants of goal-directed and habitual action." *Neuropsychopharmacology* 35:48–69 | H |
| hed_model_based_learning | Daw, Gershman, Seymour, Dayan & Dolan (2011) | "Model-based influences on humans' choices and striatal prediction errors." *Neuron* 69:1204–1215 | H |
| hed_model_free_learning | Daw, Niv & Dayan (2005) | "Uncertainty-based competition between prefrontal and dorsolateral striatal systems for behavioral control." *Nat Neurosci* 8:1704–1711 | H |
| hed_pavlovian_conditioning | Rescorla (1988) | "Pavlovian conditioning: it's not what you think it is." *Am Psychol* 43:151–160 | H |
| hed_reinforcement_learning | Sutton (1988) | "Learning to predict by the methods of temporal differences." *Mach Learn* 3:9–44 | H |
| hed_reversal_learning | Izquierdo, Brigman, Radke, Rudebeck & Holmes (2017) | "The neural basis of reversal learning: an updated perspective." *Neuroscience* 345:12–26 | M |
| hed_reward_prediction_error | Schultz, Dayan & Montague (1997) | "A neural substrate of prediction and reward." *Science* 275:1593–1599 | H |
| hed_value_learning | Rangel, Camerer & Montague (2008) | "A framework for studying the neurobiology of value-based decision-making." *Nat Rev Neurosci* 9:545–556 | H |

### 2.2 Auditory and Pre-Attentive Deviance Processing

| process_id | Citation | Title and venue | Confidence |
|---|---|---|---|
| hed_acoustic_processing | Fletcher (1940) | "Auditory patterns." *Rev Mod Phys* 12:47–65 | H |
| hed_auditory_tone_discrimination | Näätänen, Paavilainen, Rinne & Alho (2007) | "The mismatch negativity (MMN) in basic research of central auditory processing: a review." *Clin Neurophysiol* 118:2544–2590 | H |
| hed_pitch_perception | Oxenham (2018) | "How we hear: the perception and neural coding of sound." *Annu Rev Psychol* 69:27–50 | M |

### 2.3 Awareness, Agency, and Metacognition

| process_id | Citation | Title and venue | Confidence |
|---|---|---|---|
| hed_perceptual_awareness | Dehaene & Changeux (2011) | "Experimental and theoretical approaches to conscious processing." *Neuron* 70:200–227 | H |
| hed_body_ownership | Botvinick & Cohen (1998) | "Rubber hands 'feel' touch that eyes see." *Nature* 391:756 | H |
| hed_sense_of_agency | Haggard, Clark & Kalogeras (2002) | "Voluntary action and conscious awareness." *Nat Neurosci* 5:382–385 | H |
| hed_feeling_of_knowing | Koriat (1993) | "How do we know that we know? The accessibility model of the feeling of knowing." *Psychol Rev* 100:609–639 | H |
| hed_judgment_of_learning | Nelson & Dunlosky (1991) | "When people's judgments of learning (JOLs) are extremely accurate at predicting subsequent recall: the 'delayed-JOL effect'." *Psychol Sci* 2:267–270 | H |
| hed_metacognitive_monitoring | Fleming & Lau (2014) | "How to measure metacognition." *Front Hum Neurosci* 8:443 | H |
| hed_metacognitive_control | Koriat & Goldsmith (1996) | "Monitoring and control processes in the strategic regulation of memory accuracy." *Psychol Rev* 103:490–517 | H |
| hed_mind_wandering | Smallwood & Schooler (2015) | "The science of mind wandering: empirically navigating the stream of consciousness." *Annu Rev Psychol* 66:487–518 | H |
| hed_masking | Enns & Di Lollo (2000) | "What's new in visual masking?" *Trends Cogn Sci* 4:345–352 | H |
| hed_interoceptive_awareness | Critchley, Wiens, Rotshtein, Öhman & Dolan (2004) | "Neural systems supporting interoceptive awareness." *Nat Neurosci* 7:189–195 | H |
| hed_self_monitoring | Nelson & Narens (1990) | "Metamemory: a theoretical framework and new findings." *Psychol Learn Motiv* 26:125–173 | H |
| hed_self_referential_processing | Northoff et al. (2006) | "Self-referential processing in our brain—a meta-analysis of imaging studies on the self." *NeuroImage* 31:440–457 | H |

### 2.4 Cognitive Control Strategy and Flexibility

| process_id | Citation | Title and venue | Confidence |
|---|---|---|---|
| hed_goal_maintenance | Miller & Cohen (2001) | "An integrative theory of prefrontal cortex function." *Annu Rev Neurosci* 24:167–202 | H |
| hed_set_shifting | Monsell (2003) | "Task switching." *Trends Cogn Sci* 7:134–140 | H |

### 2.5 Emotion and Affect

| process_id | Citation | Title and venue | Confidence |
|---|---|---|---|
| hed_cognitive_reappraisal | Ochsner & Gross (2005) | "The cognitive control of emotion." *Trends Cogn Sci* 9:242–249 | H |
| hed_emotion_recognition | Ekman & Friesen (1971) | "Constants across cultures in the face and emotion." *J Pers Soc Psychol* 17:124–129 | H |
| hed_emotion_regulation | Gross (1998) | "The emerging field of emotion regulation: an integrative review." *Rev Gen Psychol* 2:271–299 | H |
| hed_expressive_suppression | Gross (2002) | "Emotion regulation: affective, cognitive, and social consequences." *Psychophysiology* 39:281–291 | H |
| hed_affective_priming | Fazio, Sanbonmatsu, Powell & Kardes (1986) | "On the automatic activation of attitudes." *J Pers Soc Psychol* 50:229–238 | H |

### 2.6 Face, Object, and Scene Perception

| process_id | Citation | Title and venue | Confidence |
|---|---|---|---|
| hed_biological_motion_perception | Johansson (1973) | "Visual perception of biological motion and a model for its analysis." *Percept Psychophys* 14:201–211 | H |
| hed_face_identity_recognition | Bruce & Young (1986) | "Understanding face recognition." *Br J Psychol* 77:305–327 | H |
| hed_face_perception | Kanwisher, McDermott & Chun (1997) | "The fusiform face area: a module in human extrastriate cortex specialized for face perception." *J Neurosci* 17:4302–4311 | H |
| hed_visual_form_recognition | Riesenhuber & Poggio (1999) | "Hierarchical models of object recognition in cortex." *Nat Neurosci* 2:1019–1025 | H |
| hed_visual_object_recognition | Logothetis & Sheinberg (1996) | "Visual object recognition." *Annu Rev Neurosci* 19:577–621 | H |
| hed_pattern_recognition | Biederman (1987) | "Recognition-by-components: a theory of human image understanding." *Psychol Rev* 94:115–147 | H |
| hed_motion_perception | Newsome & Paré (1988) | "A selective impairment of motion perception following lesions of the middle temporal visual area (MT) of the macaque monkey." *J Neurosci* 8:2201–2211 | H |
| hed_visual_perception | Hubel & Wiesel (1962) | "Receptive fields, binocular interaction and functional architecture in the cat's visual cortex." *J Physiol* 160:106–154 | H |

### 2.7 Implicit Learning and Procedural Memory

| process_id | Citation | Title and venue | Confidence |
|---|---|---|---|
| hed_implicit_memory | Schacter (1987) | "Implicit memory: history and current status." *J Exp Psychol Learn Mem Cogn* 13:501–518 | H |
| hed_procedural_memory | Squire (1992) | "Memory and the hippocampus: a synthesis from findings with rats, monkeys, and humans." *Psychol Rev* 99:195–231 | H |

### 2.8 Executive Control and Inhibition

| process_id | Citation | Title and venue | Confidence |
|---|---|---|---|
| hed_conflict_monitoring | Botvinick, Braver, Barch, Carter & Cohen (2001) | "Conflict monitoring and cognitive control." *Psychol Rev* 108:624–652 | H |
| hed_error_detection | Gehring, Goss, Coles, Meyer & Donchin (1993) | "A neural system for error detection and compensation." *Psychol Sci* 4:385–390 | H |
| hed_executive_attention | Posner & Petersen (1990) | "The attention system of the human brain." *Annu Rev Neurosci* 13:25–42 | H |
| hed_interference_control | MacLeod (1991) | "Half a century of research on the Stroop effect: an integrative review." *Psychol Bull* 109:163–203 | H |
| hed_proactive_control | Braver (2012) | "The variable nature of cognitive control: a dual mechanisms framework." *Trends Cogn Sci* 16:106–113 | H |
| hed_reactive_control | Braver (2012) | "The variable nature of cognitive control: a dual mechanisms framework." *Trends Cogn Sci* 16:106–113 | H |
| hed_response_conflict | Eriksen & Eriksen (1974) | "Effects of noise letters upon the identification of a target letter in a nonsearch task." *Percept Psychophys* 16:143–149 | H |
| hed_response_inhibition | Logan & Cowan (1984) | "On the ability to inhibit thought and action: a theory of an act of control." *Psychol Rev* 91:295–327 | H |

### 2.9 Language and Reading

| process_id | Citation | Title and venue | Confidence |
|---|---|---|---|
| hed_discourse_processing | Kintsch (1988) | "The role of knowledge in discourse comprehension: a construction-integration model." *Psychol Rev* 95:163–182 | H |
| hed_language_comprehension | Kutas & Hillyard (1980) | "Reading senseless sentences: brain potentials reflect semantic incongruity." *Science* 207:203–205 | H |
| hed_lexical_access | Marslen-Wilson (1987) | "Functional parallelism in spoken word-recognition." *Cognition* 25:71–102 | H |
| hed_naming | Levelt, Roelofs & Meyer (1999) | "A theory of lexical access in speech production." *Behav Brain Sci* 22:1–38 | H |
| hed_phonological_awareness | Bradley & Bryant (1983) | "Categorizing sounds and learning to read—a causal connection." *Nature* 301:419–421 | H |
| hed_reading | Rayner (1998) | "Eye movements in reading and information processing: 20 years of research." *Psychol Bull* 124:372–422 | H |
| hed_semantic_processing | Binder, Desai, Graves & Conant (2009) | "Where is the semantic system? A critical review and meta-analysis of 120 functional neuroimaging studies." *Cereb Cortex* 19:2767–2796 | H |
| hed_sentence_comprehension | Just & Carpenter (1980) | "A theory of reading: from eye fixations to comprehension." *Psychol Rev* 87:329–354 | H |
| hed_speech_perception | Liberman, Cooper, Shankweiler & Studdert-Kennedy (1967) | "Perception of the speech code." *Psychol Rev* 74:431–461 | H |
| hed_word_recognition | Coltheart, Rastle, Perry, Langdon & Ziegler (2001) | "DRC: a dual route cascaded model of visual word recognition and reading aloud." *Psychol Rev* 108:204–256 | M |

### 2.10 Long-Term Memory: Encoding, Consolidation, and Retrieval

| process_id | Citation | Title and venue | Confidence |
|---|---|---|---|
| hed_autobiographical_memory | Conway & Pleydell-Pearce (2000) | "The construction of autobiographical memories in the self-memory system." *Psychol Rev* 107:261–288 | H |
| hed_consolidation | McGaugh (2000) | "Memory—a century of consolidation." *Science* 287:248–251 | H |
| hed_declarative_memory | Squire (1992) | "Memory and the hippocampus: a synthesis from findings with rats, monkeys, and humans." *Psychol Rev* 99:195–231 | H |
| hed_directed_forgetting | Anderson & Green (2001) | "Suppressing unwanted memories by executive control." *Nature* 410:366–369 | H |
| hed_encoding | Craik & Lockhart (1972) | "Levels of processing: a framework for memory research." *J Verb Learn Verb Behav* 11:671–684 | H |
| hed_episodic_memory | Tulving (2002) | "Episodic memory: from mind to brain." *Annu Rev Psychol* 53:1–25 | H |
| hed_familiarity | Yonelinas (2002) | "The nature of recollection and familiarity: a review of 30 years of research." *J Mem Lang* 46:441–517 | H |
| hed_pattern_completion | Marr (1971) | "Simple memory: a theory for archicortex." *Phil Trans R Soc B* 262:23–81 | H |
| hed_pattern_separation | Yassa & Stark (2011) | "Pattern separation in the hippocampus." *Trends Neurosci* 34:515–525 | H |
| hed_prospective_memory | Einstein & McDaniel (1990) | "Normal aging and prospective memory." *J Exp Psychol Learn Mem Cogn* 16:717–726 | H |
| hed_recall | Tulving & Thomson (1973) | "Encoding specificity and retrieval processes in episodic memory." *Psychol Rev* 80:352–373 | H |
| hed_recognition | Mandler (1980) | "Recognizing: the judgment of previous occurrence." *Psychol Rev* 87:252–271 | H |
| hed_recollection | Yonelinas (2002) | "The nature of recollection and familiarity: a review of 30 years of research." *J Mem Lang* 46:441–517 | H |
| hed_reconsolidation | Nader, Schafe & LeDoux (2000) | "Fear memories require protein synthesis in the amygdala for reconsolidation after retrieval." *Nature* 406:722–726 | H |
| hed_retrieval | Tulving (2002) | "Episodic memory: from mind to brain." *Annu Rev Psychol* 53:1–25 | H |
| hed_semantic_memory | Collins & Loftus (1975) | "A spreading-activation theory of semantic processing." *Psychol Rev* 82:407–428 | H |
| hed_source_memory | Johnson, Hashtroudi & Lindsay (1993) | "Source monitoring." *Psychol Bull* 114:3–28 | H |

### 2.11 Motor Control and Action

| process_id | Citation | Title and venue | Confidence |
|---|---|---|---|
| hed_antisaccade | Hallett (1978) | "Primary and secondary saccades to goals defined by instructions." *Vision Res* 18:1279–1296 | H |
| hed_motor_planning | Wolpert, Ghahramani & Flanagan (2001) | "Perspectives and problems in motor learning." *Trends Cogn Sci* 5:487–494 | H |
| hed_motor_sequence_learning | Nissen & Bullemer (1987) | "Attentional requirements of learning: evidence from performance measures." *Cogn Psychol* 19:1–32 | H |
| hed_motor_timing | Ivry & Keele (1989) | "Timing functions of the cerebellum." *J Cogn Neurosci* 1:136–152 | H |
| hed_reaching | Georgopoulos, Kalaska, Caminiti & Massey (1982) | "On the relations between the direction of two-dimensional arm movements and cell discharge in primate motor cortex." *J Neurosci* 2:1527–1537 | H |
| hed_response_selection | Pashler (1994) | "Dual-task interference in simple tasks: data and theory." *Psychol Bull* 116:220–244 | H |
| hed_saccade | Munoz & Everling (2004) | "Look away: the anti-saccade task and the voluntary control of eye movement." *Nat Rev Neurosci* 5:218–228 | H |
| hed_visuomotor_adaptation | Shadmehr & Mussa-Ivaldi (1994) | "Adaptive representation of dynamics during learning of a motor task." *J Neurosci* 14:3208–3224 | H |

### 2.12 Perceptual Decision Making

| process_id | Citation | Title and venue | Confidence |
|---|---|---|---|
| hed_perceptual_decision_making | Ratcliff (1978) | "A theory of memory retrieval." *Psychol Rev* 85:59–108 | H |

### 2.13 Problem Solving and Reasoning

| process_id | Citation | Title and venue | Confidence |
|---|---|---|---|
| hed_analogical_reasoning | Gentner (1983) | "Structure-mapping: a theoretical framework for analogy." *Cogn Sci* 7:155–170 | H |
| hed_categorization | Nosofsky (1986) | "Attention, similarity, and the identification-categorization relationship." *J Exp Psychol Gen* 115:39–57 | H |
| hed_causal_reasoning | Cheng & Novick (1992) | "Covariation in natural causal induction." *Psychol Rev* 99:365–382 | H |
| hed_deductive_reasoning | Johnson-Laird & Byrne (2002) | "Conditionals: a theory of meaning, pragmatics, and inference." *Psychol Rev* 109:646–678 | H |
| hed_hypothesis_testing | Wason (1960) | "On the failure to eliminate hypotheses in a conceptual task." *Q J Exp Psychol* 12:129–140 | H |
| hed_inductive_reasoning | Osherson, Smith, Wilkie, López & Shafir (1990) | "Category-based induction." *Psychol Rev* 97:185–200 | H |
| hed_insight | Metcalfe & Wiebe (1987) | "Intuition in insight and noninsight problem solving." *Mem Cognit* 15:238–246 | H |
| hed_planning | Shallice (1982) | "Specific impairments of planning." *Phil Trans R Soc B* 298:199–209 | H |

### 2.14 Reward, Motivation, and Effort

| process_id | Citation | Title and venue | Confidence |
|---|---|---|---|
| hed_effort_allocation | Kool, McGuire, Rosen & Botvinick (2010) | "Decision making and the avoidance of cognitive demand." *J Exp Psychol Gen* 139:665–682 | H |
| hed_incentive_salience | Berridge & Robinson (1998) | "What is the role of dopamine in reward: hedonic impact, reward learning, or incentive salience?" *Brain Res Rev* 28:309–369 | H |
| hed_reward_anticipation | Knutson, Westdorp, Kaiser & Hommer (2000) | "FMRI visualization of brain activity during a monetary incentive delay task." *NeuroImage* 12:20–27 | H |
| hed_reward_consumption | Berridge, Robinson & Aldridge (2009) | "Dissecting components of reward: 'liking', 'wanting', and learning." *Curr Opin Pharmacol* 9:65–73 | M |

### 2.15 Selective and Sustained Attention

| process_id | Citation | Title and venue | Confidence |
|---|---|---|---|
| hed_alerting | Posner & Petersen (1990) | "The attention system of the human brain." *Annu Rev Neurosci* 13:25–42 | H |
| hed_attentional_capture | Folk, Remington & Johnston (1992) | "Involuntary covert orienting is contingent on attentional control settings." *J Exp Psychol Hum Percept Perform* 18:1030–1044 | H |
| hed_divided_attention | Pashler (1994) | "Dual-task interference in simple tasks: data and theory." *Psychol Bull* 116:220–244 | H |
| hed_feature_based_attention | Maunsell & Treue (2006) | "Feature-based attention in visual cortex." *Trends Neurosci* 29:317–322 | H |
| hed_object_based_attention | Duncan (1984) | "Selective attention and the organization of visual information." *J Exp Psychol Gen* 113:501–517 | H |
| hed_orienting | Posner (1980) | "Orienting of attention." *Q J Exp Psychol* 32:3–25 | H |
| hed_selective_attention | Cherry (1953) | "Some experiments on the recognition of speech, with one and with two ears." *J Acoust Soc Am* 25:975–979 | H |
| hed_spatial_attention | Posner (1980) | "Orienting of attention." *Q J Exp Psychol* 32:3–25 | H |
| hed_sustained_attention | Mackworth (1948) | "The breakdown of vigilance during prolonged visual search." *Q J Exp Psychol* 1:6–21 | H |
| hed_temporal_attention | Nobre & van Ede (2018) | "Anticipated moments: temporal structure in attention." *Nat Rev Neurosci* 19:34–48 | H |
| hed_attention_shifting | Monsell (2003) | "Task switching." *Trends Cogn Sci* 7:134–140 | M |

### 2.16 Short-Term and Working Memory

| process_id | Citation | Title and venue | Confidence |
|---|---|---|---|
| hed_active_maintenance | Goldman-Rakic (1995) | "Cellular basis of working memory." *Neuron* 14:477–485 | H |
| hed_chunking | Miller (1956) | "The magical number seven, plus or minus two: some limits on our capacity for processing information." *Psychol Rev* 63:81–97 | H |
| hed_manipulation | Baddeley (2003) | "Working memory: looking back and looking forward." *Nat Rev Neurosci* 4:829–839 | H |
| hed_rehearsal | Baddeley, Thomson & Buchanan (1975) | "Word length and the structure of short-term memory." *J Verb Learn Verb Behav* 14:575–589 | H |
| hed_spatial_working_memory | Smith & Jonides (1999) | "Storage and executive processes in the frontal lobes." *Science* 283:1657–1661 | H |
| hed_visual_working_memory | Luck & Vogel (1997) | "The capacity of visual working memory for features and conjunctions." *Nature* 390:279–281 | H |
| hed_working_memory | Baddeley (1992) | "Working memory." *Science* 255:556–559 | H |
| hed_working_memory_updating | Miyake, Friedman, Emerson, Witzki, Howerter & Wager (2000) | "The unity and diversity of executive functions and their contributions to complex 'frontal lobe' tasks: a latent variable analysis." *Cogn Psychol* 41:49–100 | H |

### 2.17 Social Cognition

| process_id | Citation | Title and venue | Confidence |
|---|---|---|---|
| hed_cooperation | Fehr & Fischbacher (2003) | "The nature of human altruism." *Nature* 425:785–791 | H |
| hed_imitation | Meltzoff & Moore (1977) | "Imitation of facial and manual gestures by human neonates." *Science* 198:75–78 | H |
| hed_joint_attention | Mundy & Newell (2007) | "Attention, joint attention, and social cognition." *Curr Dir Psychol Sci* 16:269–274 | H |
| hed_perspective_taking | Premack & Woodruff (1978) | "Does the chimpanzee have a theory of mind?" *Behav Brain Sci* 1:515–526 | H |
| hed_social_decision_making | Rilling & Sanfey (2011) | "The neuroscience of social decision-making." *Annu Rev Psychol* 62:23–48 | H |
| hed_social_perception | Adolphs (2003) | "Cognitive neuroscience of human social behaviour." *Nat Rev Neurosci* 4:165–178 | H |
| hed_stereotyping | Devine (1989) | "Stereotypes and prejudice: their automatic and controlled components." *J Pers Soc Psychol* 56:5–18 | H |

### 2.18 Spatial Cognition

| process_id | Citation | Title and venue | Confidence |
|---|---|---|---|
| hed_mental_rotation | Shepard & Metzler (1971) | "Mental rotation of three-dimensional objects." *Science* 171:701–703 | H |
| hed_spatial_memory | Moser, Kropff & Moser (2008) | "Place cells, grid cells, and the brain's spatial representation system." *Annu Rev Neurosci* 31:69–89 | H |

### 2.19 Value-based Decision Making, Risk, and Reward Processing

| process_id | Citation | Title and venue | Confidence |
|---|---|---|---|
| hed_delay_discounting | Ainslie (1975) | "Specious reward: a behavioral theory of impulsiveness and impulse control." *Psychol Bull* 82:463–496 | H |
| hed_intertemporal_choice | Frederick, Loewenstein & O'Donoghue (2002) | "Time discounting and time preference: a critical review." *J Econ Lit* 40:351–401 | H |
| hed_probability_judgment | Tversky & Kahneman (1974) | "Judgment under uncertainty: heuristics and biases." *Science* 185:1124–1131 | H |
| hed_risk_processing | Kahneman & Tversky (1979) | "Prospect theory: an analysis of decision under risk." *Econometrica* 47:263–292 | H |
| hed_valuation | Rangel, Camerer & Montague (2008) | "A framework for studying the neurobiology of value-based decision making." *Nat Rev Neurosci* 9:545–556 | H |
| hed_value_based_decision_making | Rangel, Camerer & Montague (2008) | "A framework for studying the neurobiology of value-based decision making." *Nat Rev Neurosci* 9:545–556 | M |

---

## 3. Task landmarks

Organized alphabetically by task id for easier review.

| task_id | Citation | Venue | Confidence |
|---|---|---|---|
| hedtsk_affective_priming | Fazio, Sanbonmatsu, Powell & Kardes (1986) | *J Pers Soc Psychol* 50:229–238 | H |
| hedtsk_anti_saccade | Hallett (1978) | *Vision Res* 18:1279–1296 | H |
| hedtsk_artificial_grammar_learning | Reber (1967) | *J Verb Learn Verb Behav* 6:855–863 | H |
| hedtsk_attention_network | Fan, McCandliss, Sommer, Raz & Posner (2002) | *J Cogn Neurosci* 14:340–347 | H |
| hedtsk_autobiographical_memory | Levine, Svoboda, Hay, Winocur & Moscovitch (2002) | *Psychol Aging* 17:677–689 | H |
| hedtsk_balloon_analog_risk | Lejuez et al. (2002) | *J Exp Psychol Appl* 8:75–84 | H |
| hedtsk_biological_motion_perception | Johansson (1973) | *Percept Psychophys* 14:201–211 | H |
| hedtsk_body_ownership_illusion | Botvinick & Cohen (1998) | *Nature* 391:756 | H |
| hedtsk_cambridge_face_memory | Duchaine & Nakayama (2006) | *Neuropsychologia* 44:576–585 | H |
| hedtsk_causal_learning | Shanks (1985) "Forward and backward blocking in human contingency judgement" | *Q J Exp Psychol B* 37:1–21 | M |
| hedtsk_change_detection | Rensink, O'Regan & Clark (1997) | *Psychol Sci* 8:368–373 | H |
| hedtsk_continuous_performance | Rosvold, Mirsky, Sarason, Bransome & Beck (1956) | *J Consult Psychol* 20:343–350 | H |
| hedtsk_contextual_cueing | Chun & Jiang (1998) | *Cogn Psychol* 36:28–71 | H |
| hedtsk_delay_discounting | Kirby & Maraković (1996) | *Psychon Bull Rev* 3:100–104 | H |
| hedtsk_delayed_match_to_sample | Mishkin & Delacour (1975) | *J Exp Psychol Anim Behav Process* 1:326–334 | H |
| hedtsk_dictator_game | Forsythe, Horowitz, Savin & Sefton (1994) | *Games Econ Behav* 6:347–369 | H |
| hedtsk_digit_span | Miller (1956) | *Psychol Rev* 63:81–97 | M |
| hedtsk_directed_forgetting | Anderson & Green (2001) | *Nature* 410:366–369 | H |
| hedtsk_dot_probe | MacLeod, Mathews & Tata (1986) | *J Abnorm Psychol* 95:15–20 | H |
| hedtsk_effort_based_decision_making | Kool, McGuire, Rosen & Botvinick (2010) | *J Exp Psychol Gen* 139:665–682 | H |
| hedtsk_emotional_stroop | Williams, Mathews & MacLeod (1996) | *Psychol Bull* 120:3–24 | H |
| hedtsk_emotion_regulation | Ochsner, Bunge, Gross & Gabrieli (2002) | *J Cogn Neurosci* 14:1215–1229 | H |
| hedtsk_eriksen_flanker | Eriksen & Eriksen (1974) | *Percept Psychophys* 16:143–149 | H |
| hedtsk_face_processing | Tong, Nakayama, Moscovitch, Weinrib & Kanwisher (2000) | *Neuron* 21:753–759 | M |
| hedtsk_facial_emotion_recognition | Ekman (1992) | "An argument for basic emotions." *Cognition & Emotion* 6:169–200 | H |
| hedtsk_false_belief | Wimmer & Perner (1983) | *Cognition* 13:103–128 | H |
| hedtsk_feeling_of_knowing | Hart (1965) | *J Educ Psychol* 56:208–216 | H |
| hedtsk_free_recall | Murdock (1962) | *J Exp Psychol* 64:482–488 | H |
| hedtsk_go_no_go | Garavan, Ross & Stein (1999) | *Proc Natl Acad Sci USA* 96:8301–8306 | H |
| hedtsk_heartbeat_detection | Schandry (1981) | *Psychophysiology* 18:483–488 | H |
| hedtsk_imitation_inhibition | Brass, Bekkering & Prinz (2001) | *Acta Psychol* 106:3–22 | H |
| hedtsk_implicit_association | Greenwald, McGhee & Schwartz (1998) | *J Pers Soc Psychol* 74:1464–1480 | H |
| hedtsk_instrumental_conditioning | O'Doherty, Dayan, Schultz, Deichmann, Friston & Dolan (2004) | *Science* 304:452–454 | H |
| hedtsk_intentional_binding | Haggard, Clark & Kalogeras (2002) | *Nat Neurosci* 5:382–385 | H |
| hedtsk_iowa_gambling | Bechara, Damasio, Damasio & Anderson (1994) | *Cognition* 50:7–15 | H |
| hedtsk_judgment_of_learning | Nelson & Dunlosky (1991) | *Psychol Sci* 2:267–270 | H |
| hedtsk_lexical_decision | Meyer & Schvaneveldt (1971) | *J Exp Psychol* 90:227–234 | H |
| hedtsk_mental_rotation | Shepard & Metzler (1971) | *Science* 171:701–703 | H |
| hedtsk_mirror_tracing | Scoville & Milner (1957) "Loss of recent memory after bilateral hippocampal lesions" | *J Neurol Neurosurg Psychiatry* 20:11–21 | H |
| hedtsk_mismatch_negativity | Näätänen, Gaillard & Mäntysalo (1978) | *Acta Psychol* 42:313–329 | H |
| hedtsk_mnemonic_similarity | Kirwan & Stark (2007) | *Learn Mem* 14:625–633 | H |
| hedtsk_monetary_incentive_delay | Knutson, Westdorp, Kaiser & Hommer (2000) | *NeuroImage* 12:20–27 | H |
| hedtsk_motor_sequence_learning | Karni et al. (1995) | *Nature* 377:155–158 | H |
| hedtsk_multi_armed_bandit | Daw, O'Doherty, Dayan, Seymour & Dolan (2006) | *Nature* 441:876–879 | H |
| hedtsk_multiple_object_tracking | Pylyshyn & Storm (1988) | *Spat Vis* 3:179–197 | H |
| hedtsk_n_back | Owen, McMillan, Laird & Bullmore (2005) | *Hum Brain Mapp* 25:46–59 | H |
| hedtsk_navon | Navon (1977) | *Cogn Psychol* 9:353–383 | H |
| hedtsk_oddball | Sutton, Braren, Zubin & John (1965) | *Science* 150:1187–1188 | H |
| hedtsk_old_new_recognition_memory | Rugg & Curran (2007) | *Trends Cogn Sci* 11:251–257 | M |
| hedtsk_operation_span | Turner & Engle (1989) | *J Mem Lang* 28:127–154 | H |
| hedtsk_paired_associates_learning | Postman & Underwood (1973) | *Mem Cognit* 1:19–40 | L |
| hedtsk_pavlovian_fear_conditioning | LaBar, Gatenby, Gore, LeDoux & Phelps (1998) | *Neuron* 20:937–945 | H |
| hedtsk_phonological_awareness | Bradley & Bryant (1983) | *Nature* 301:419–421 | H |
| hedtsk_picture_naming | Snodgrass & Vanderwart (1980) | *J Exp Psychol Hum Learn Mem* 6:174–215 | H |
| hedtsk_posner_spatial_cueing | Posner (1980) | *Q J Exp Psychol* 32:3–25 | H |
| hedtsk_prisoners_dilemma | Axelrod & Hamilton (1981) "The evolution of cooperation" | *Science* 211:1390–1396 | H |
| hedtsk_probabilistic_classification_learning | Knowlton, Squire & Gluck (1994) | *Learn Mem* 1:106–120 | H |
| hedtsk_probabilistic_selection | Frank, Seeberger & O'Reilly (2004) | *Science* 306:1940–1943 | H |
| hedtsk_prospective_memory | Einstein & McDaniel (1990) | *J Exp Psychol Learn Mem Cogn* 16:717–726 | H |
| hedtsk_psychological_refractory_period | Pashler (1994) | *Psychol Bull* 116:220–244 | H |
| hedtsk_psychomotor_vigilance | Dinges & Powell (1985) | *Behav Res Methods Instrum Comput* 17:652–655 | H |
| hedtsk_random_dot_kinematogram | Newsome & Paré (1988) | *J Neurosci* 8:2201–2211 | H |
| hedtsk_rapid_serial_visual_presentation | Raymond, Shapiro & Arnell (1992) | *J Exp Psychol Hum Percept Perform* 18:849–860 | H |
| hedtsk_ravens_progressive_matrices | Carpenter, Just & Shell (1990) | *Psychol Rev* 97:404–431 | H |
| hedtsk_reading_the_mind_in_the_eyes | Baron-Cohen, Wheelwright, Hill, Raste & Plumb (2001) | *J Child Psychol Psychiatry* 42:241–251 | H |
| hedtsk_remember_know | Tulving (1985) | *Can Psychol* 26:1–12 | H |
| hedtsk_remote_associates | Mednick (1962) | *Psychol Rev* 69:220–232 | H |
| hedtsk_reversal_learning | Murray, O'Doherty & Schoenbaum (2007) | *Nat Rev Neurosci* 8:148–159 | H |
| hedtsk_self_paced_reading | Just, Carpenter & Woolley (1982) | *J Exp Psychol Gen* 111:228–238 | H |
| hedtsk_self_referential_encoding | Rogers, Kuiper & Kirker (1977) | *J Pers Soc Psychol* 35:677–688 | H |
| hedtsk_semantic_priming | Neely (1977) | *J Exp Psychol Gen* 106:226–254 | H |
| hedtsk_sentence_comprehension | Caplan & Waters (1999) | *Behav Brain Sci* 22:77–126 | M |
| hedtsk_serial_reaction_time | Nissen & Bullemer (1987) | *Cogn Psychol* 19:1–32 | H |
| hedtsk_simon | Simon & Rudell (1967) | *J Appl Psychol* 51:300–304 | H |
| hedtsk_social_incentive_delay | Spreckelmeyer et al. (2009) | *Soc Cogn Affect Neurosci* 4:158–165 | H |
| hedtsk_source_memory | Johnson & Raye (1981) | "Reality monitoring." *Psychol Rev* 88:67–85 | H |
| hedtsk_sternberg_item_recognition | Sternberg (1966) | *Science* 153:652–654 | H |
| hedtsk_stop_signal | Logan, Cowan & Davis (1984) | *J Exp Psychol Hum Percept Perform* 10:276–291 | H |
| hedtsk_stroop_color_word | Stroop (1935) | *J Exp Psychol* 18:643–662 | H |
| hedtsk_sustained_attention_to_response | Robertson, Manly, Andrade, Baddeley & Yiend (1997) | *Neuropsychologia* 35:747–758 | H |
| hedtsk_task_switching | Rogers & Monsell (1995) | *J Exp Psychol Gen* 124:207–231 | H |
| hedtsk_think_no_think | Anderson & Green (2001) | *Nature* 410:366–369 | H |
| hedtsk_tower_of_london | Shallice (1982) | *Phil Trans R Soc B* 298:199–209 | H |
| hedtsk_trail_making | Reitan (1958) | *Percept Mot Skills* 8:271–276 | H |
| hedtsk_trust_game | Berg, Dickhaut & McCabe (1995) | *Games Econ Behav* 10:122–142 | H |
| hedtsk_two_stage_decision | Daw, Gershman, Seymour, Dayan & Dolan (2011) | *Neuron* 69:1204–1215 | H |
| hedtsk_ultimatum_game | Güth, Schmittberger & Schwarze (1982) | *J Econ Behav Organ* 3:367–388 | H |
| hedtsk_verb_generation | Petersen, Fox, Posner, Mintun & Raichle (1988) | *Nature* 331:585–589 | H |
| hedtsk_virtual_morris_water_maze | Morris (1981) | *Learn Motiv* 12:239–260 | H |
| hedtsk_virtual_radial_arm_maze | Olton & Samuelson (1976) | *J Exp Psychol Anim Behav Process* 2:97–116 | H |
| hedtsk_visual_masking | Breitmeyer & Öğmen (2000) | *Percept Psychophys* 62:1572–1595 | H |
| hedtsk_visual_search | Treisman & Gelade (1980) | *Cogn Psychol* 12:97–136 | H |
| hedtsk_wason_selection | Wason (1968) | *Q J Exp Psychol* 20:273–281 | H |
| hedtsk_weapons_identification | Payne (2001) | *J Pers Soc Psychol* 81:181–192 | H |
| hedtsk_wisconsin_card_sorting | Berg (1948) | *J Gen Psychol* 39:15–22 | H |

---

## 4. Processes deliberately left without a landmark entry

These are cases where no single paper stands out as the canonical origin or
review — usually because the process is either too umbrella (e.g.,
"visual_perception") or too mechanical (e.g., "response_execution") for a
single reference to do the job. The triage's keep/drop rules will handle
these via the venue allowlist, not the landmark override.

**Explicitly unlisted by design** (~88 processes after the second-pass
additions in §9): all perception submodalities that aren't
face/motion/biological and weren't added in the second pass
(auditory_perception, depth_perception, gustatory_perception,
olfactory_perception, somatosensory_perception), umbrella motor processes
(action_initiation, fine_motor_control, grasping, motor_memory,
motor_preparation, proprioception, response_execution,
vocal_motor_control), language-production umbrellas that overlap with the
listed entries (language_production, phonological_encoding,
speech_production, syntactic_parsing, semantic_knowledge,
verbal_fluency — the latter's landmark is in the Benton test manual,
explicitly excluded), umbrella reasoning processes without a clear origin
(mathematical_reasoning, means_ends_analysis, subgoaling),
approach/avoidance motivation (usually cited to Gray's textbook, excluded),
social cognition umbrellas (competition, reciprocity,
in_group_out_group_processing, self_other_distinction), all executive-
control umbrellas already covered by more specific entries
(attentional_awareness, conflict_monitoring is covered,
error_correction — no distinct origin separate from error_detection), all
decision umbrellas covered by §2.19 entries, self_monitoring (see §9 — the
Gemini pass proposed Snyder 1974 but that's the wrong construct;
performance-monitoring candidate flagged for user decision),
choice_commitment (unclear construct), value_learning has the
Rangel/Camerer/Montague review but it's already listed under
value_based_decision_making.

**Filled in the second pass (see §9):** hed_visual_perception
(Hubel & Wiesel 1962), hed_acoustic_processing (Fletcher 1940),
hed_inductive_reasoning (Osherson et al. 1990).

I expect you'll want to add ~5–10 of these back. I left them out rather
than populate with a weak choice; easier to add than to argue against.

---

## 5. Book and book-chapter substitutions (rule applied 2026-04-22)

Per the user's rule (2026-04-22): general textbooks, monographs, and book
chapters are excluded from landmark status. Dedicated monographs on
tightly-related concepts are the only books eligible; none in this list
are retained on that basis (the one borderline case, O'Keefe & Nadel 1978
as a monograph on the cognitive-map theory of hippocampal spatial memory,
has a strong journal review alternative and was replaced).

The substitutions applied in §2 and §3 above:

| Id | Original (excluded) | Replacement (journal) |
|---|---|---|
| hed_associative_learning | Rescorla & Wagner (1972) book chapter | Rescorla (1988) *Annu Rev Neurosci* 11:329–352 |
| hed_reinforcement_learning | Sutton & Barto textbook | Sutton (1988) *Mach Learn* 3:9–44 (TD learning) |
| hed_feeling_of_knowing | Nelson & Narens (1990) book-series chapter | Koriat (1993) *Psychol Rev* 100:609–639 |
| hed_metacognitive_monitoring | Nelson & Narens (1990) book-series chapter | Fleming & Lau (2014) *Front Hum Neurosci* 8:443 |
| hed_metacognitive_control | Nelson & Narens (1990) book-series chapter | Koriat & Goldsmith (1996) *Psychol Rev* 103:490–517 |
| hed_deductive_reasoning | Johnson-Laird (1983) *Mental Models* book | Johnson-Laird & Byrne (2002) *Psychol Rev* 109:646–678 |
| hed_selective_attention | Broadbent (1958) book | Cherry (1953) *J Acoust Soc Am* 25:975–979 |
| hed_working_memory | Baddeley & Hitch (1974) book chapter | Baddeley (1992) *Science* 255:556–559 |
| hed_joint_attention | Tomasello (1995) book chapter | Mundy & Newell (2007) *Curr Dir Psychol Sci* 16:269–274 |
| hed_spatial_memory | O'Keefe & Nadel (1978) monograph | Moser, Kropff & Moser (2008) *Annu Rev Neurosci* 31:69–89 |
| hed_delay_discounting | Mazur (1987) book chapter | Ainslie (1975) *Psychol Bull* 82:463–496 |
| hedtsk_mirror_tracing | Milner (1962) book chapter (French) | Scoville & Milner (1957) *J Neurol Neurosurg Psychiatry* 20:11–21 (HM paper) |
| hedtsk_prisoners_dilemma | Rapoport & Chammah (1965) book | Axelrod & Hamilton (1981) *Science* 211:1390–1396 |
| hedtsk_causal_learning | Shanks & Dickinson (1987) book-series chapter | Shanks (1985) *Q J Exp Psychol B* 37:1–21 |

### One case worth flagging explicitly

**hed_associative_learning / Rescorla & Wagner (1972).** The rule excludes
the literal origin paper of the Rescorla–Wagner model — the most
important conditioning theory of the 20th century — because it appeared as
a book chapter. The replacement (Rescorla 1988 *Annu Rev Neurosci*) is
Rescorla's own comprehensive journal review covering the RW framework and
successor work; it is a strong proxy but is not the original model paper.
If the HED team wants the RW model itself in the landmark set as a
one-off exception to the rule, say so and I'll add it back with a
`book_chapter_exception: true` flag in the JSON schema. Otherwise the
Rescorla 1988 review stands.

A similar flag exists for Kamin (1968) "blocking" — also a book chapter;
I didn't include it above because blocking wasn't one of the landmarks in
my draft, but if you want it we have the same decision to make.

### Carved-out exceptions retained (user decisions 2026-04-22)

These book/chapter entries are kept in the landmark list despite the
general exclusion rule. Each will carry a `book_chapter_exception: true`
flag in the JSON so the exception is traceable:

| Id | Entry | Reason |
|---|---|---|
| hed_self_monitoring | Nelson & Narens (1990) "Metamemory: a theoretical framework and new findings" *Psychol Learn Motiv* 26:125–173 | The seminal model of metacognition (object-level / meta-level framework); the theoretical foundation for performance monitoring as a whole. Book-chapter venue is incidental. User decision 2026-04-22. |

The user may also want to revisit three earlier Nelson & Narens (1990)
substitutions for consistency (hed_feeling_of_knowing,
hed_metacognitive_monitoring, hed_metacognitive_control — all
substituted with journal alternatives in §5). If the same rationale
applies there, Nelson & Narens (1990) could be the landmark for all
four processes. Flag if that's the intent; otherwise the current
substitutions stand and Nelson & Narens is used only for
hed_self_monitoring.

---

## 6. Entries I'm least confident about

Flagged **[M]** or **[L]** above. Summary list for focused review.
Updated 2026-04-22 after the second-pass Gemini review (§9):

- hed_pitch_perception (Oxenham 2018) — review is recent; the field has competing reviews.
- hed_word_recognition (Coltheart et al. 2001) — DRC model is the modern computational landmark; origin might be a Forster or Morton paper.
- hed_reward_consumption (Berridge, Robinson & Aldridge 2009) — the "liking vs. wanting" distinction is strong but the specific 2009 paper may not be the best pick.
- hed_cooperation — Fehr & Fischbacher (2003) *Nature* is strong; kept [H].
- hed_value_based_decision_making (Rangel, Camerer & Montague 2008) — same citation as hed_valuation; consider whether one of the two should be dropped.
- hedtsk_face_processing (Tong et al. 2000) — conflicts with the Kanwisher 1997 FFA paper under hed_face_perception; please choose which should be where.
- hedtsk_causal_learning (Shanks 1985) — journal paper now; still [M] because the field has several candidate origins.
- hedtsk_old_new_recognition_memory (Rugg & Curran 2007) — integrative ERP review; origin of the paradigm itself predates it.
- hedtsk_paired_associates_learning (Postman & Underwood 1973) — weak. The paradigm has many origins; please suggest if you have a preferred one.
- hedtsk_digit_span (Miller 1956) — added in second pass. Same citation as hed_chunking. The origin of the digit-span paradigm itself is Jacobs (1887) *Mind* 12:75–79 (pre-journal-era era, effectively); Conway, Kane, Bunting, Hambrick, Wilhelm & Engle (2005) *Psychon Bull Rev* 12:769–786 is a stronger modern review if you prefer.

**Resolved by the second pass (no longer [M] or [L]):**
hed_pattern_recognition (now Biederman 1987 [H]),
hed_expressive_suppression (now Gross 2002 [H]),
hed_response_selection (now Pashler 1994 [H]),
hed_working_memory_updating (now Miyake et al. 2000 [H]),
hedtsk_source_memory (now Johnson & Raye 1981 [H]),
hedtsk_facial_emotion_recognition (now Ekman 1992 [H]).

---

## 7. Questions for you

1. **Rescorla & Wagner (1972) exception.** The book-chapter exclusion cost
   us the literal origin of the Rescorla–Wagner model. The replacement
   (Rescorla 1988 *Annu Rev Neurosci* review) is a strong proxy but is not
   the original model paper. Do you want a narrow, explicit exception for
   this one entry? Same question applies to Kamin (1968) "blocking" and
   Baddeley & Hitch (1974) working-memory model if either matters to
   your curation.

2. **Processes left blank** (§4). ~92 of 172 processes have no landmark
   entry. Is that too few? The plan's §7.3 rule is "a paper that **must**
   be included" — if a construct has no single must-include paper, I'd
   rather leave it blank than pad. But if you want fuller coverage I'll
   iterate.

3. **Dual-citation overlap.** Some tasks and processes point to the same
   paper (Eriksen & Eriksen 1974 appears under hed_response_conflict and
   hedtsk_eriksen_flanker; Posner 1980 appears under hed_orienting,
   hed_spatial_attention, and hedtsk_posner_spatial_cueing; Daw 2011
   under hed_model_based_learning and hedtsk_two_stage_decision). That's
   by design — the landmark list maps id → DOI, and the same DOI is
   allowed to cover multiple ids. Phase 6 dedupes at the publication-
   record level. Flag if you want this structured differently.

4. **Test-manual exclusion.** I dropped WAIS-based tasks (digit_span,
   digit_symbol_substitution), IAPS for affective_picture_viewing, KDEF
   for facial_emotion_recognition. That means those tasks have no
   landmark. If you want to allow test-manual entries with a flag, I'll
   add them back.

5. **Confidence levels.** §6 lists ~13 entries I'm least sure of. If any
   of these matter strategically (e.g., you know your domain will want a
   specific paper), flag them and I'll swap before we serialize.

---

## 8. Next step after review

After your sign-off:

1. Generate DOIs for every entry (via CrossRef title+author+year lookup, batched; ~170 lookups, ~5 minutes with rate limiting).
2. Serialize to `outputs/literature_search/landmark_refs.json` with schema:
   ```json
   {
     "schema_version": "2026-04-22",
     "generated_on": "YYYY-MM-DD",
     "entries": [
       {"id": "hed_response_conflict", "doi": "10.3758/BF03203267",
        "citation": "Eriksen & Eriksen (1974)", "confidence": "H"},
       ...
     ]
   }
   ```
3. Resolve open item §12.2 in the main plan (mark as "confirmed with the
   curated list in `.status/landmark_refs_proposed_2026-04-22.md`").
4. Proceed to drafting Phase 2 instructions for Sonnet.

---

## 9. Second-pass review log (2026-04-22)

The user ran the draft through a second manual review with AI assistance
(`landmark_refs_first_review_gemini-manual.md`). This section records
what was accepted, modified, or rejected from that review and why. All
downstream tooling should read the current tables in §2 and §3 as
authoritative; this log is for traceability.

### 9.1 Accepted with no modification

Five process swaps that correctly filled or strengthened [M]/[L] entries:

| id | Before | After | Why accepted |
|---|---|---|---|
| hed_pattern_recognition | Treisman & Gelade (1980) FIT [M] | Biederman (1987) RBC [H] | Biederman's RBC is genuinely the canonical object-recognition origin paper; FIT is better placed under visual_search and hed_pattern_recognition was double-booking it. |
| hed_response_selection | Welford (1952) [M] | Pashler (1994) [H] | Pashler's bottleneck theory is the modern canonical frame; Welford was my placeholder. Creates intentional overlap with hed_divided_attention and hedtsk_psychological_refractory_period (allowed, see §7 Q3). |
| hed_expressive_suppression | Gross (1998) [M] | Gross (2002) [H] | The 2002 *Psychophysiology* paper is the specific suppression-vs-reappraisal comparison that defines the construct; the 1998 paper is for the broader regulation umbrella. |
| hed_working_memory_updating | Morris & Jones (1990) [M] | Miyake et al. (2000) [H] | Miyake et al. established "updating" as a distinct executive-function construct. I had flagged this swap as pending in §6 of the original draft. |
| hedtsk_source_memory | Johnson, Hashtroudi & Lindsay (1993) [M] | Johnson & Raye (1981) [H] | The 1981 paper is the origin of reality-monitoring theory; the 1993 paper is the review that followed. I had flagged this swap as pending in §6. |

Plus one task-level accepted swap:

| hedtsk_facial_emotion_recognition | Ekman & Friesen (1971) [M] | Ekman (1992) [H] | Ekman's 1992 basic-emotions theoretical paper is a better functional origin for the face-emotion paradigm than the 1971 cross-cultural empirical paper (which is already used for hed_emotion_recognition). |

### 9.2 Accepted with a modified citation

Three cases where the Gemini pass proposed filling a previously-blank
process but with a weaker citation; I accepted the decision to fill but
substituted a stronger paper:

| id | Gemini proposal | Used instead | Why changed |
|---|---|---|---|
| hed_visual_perception | Livingstone & Hubel (1988) *Science* "Segregation of form, color, movement, and depth" | **Hubel & Wiesel (1962)** *J Physiol* "Receptive fields, binocular interaction and functional architecture in the cat's visual cortex" | Hubel & Wiesel 1962 is the origin paper for cortical visual processing and is what the HED catalog itself cites as the fundamental reference. Livingstone & Hubel 1988 is more specific (magno/parvo pathways) — narrower than the process definition. |
| hed_acoustic_processing | Tanner & Swets (1954) *Psychol Rev* "A decision-making theory of **visual** detection" | **Fletcher (1940)** *Rev Mod Phys* "Auditory patterns" | The Tanner & Swets paper is the SDT foundation paper but is explicitly about *visual* detection. Using a visual-detection paper as the landmark for acoustic processing is incongruous. Fletcher 1940 is a flagship-journal psychoacoustics origin paper (critical bands) and is what the HED catalog itself cites. |
| hed_inductive_reasoning | Osherson et al. (1990) *Psychol Rev* | **Osherson, Smith, Wilkie, López & Shafir (1990)** *Psychol Rev* (full author list) | Same paper; expanded the et al. for consistency with the rest of §2. |

### 9.3 Accepted with a confidence downgrade

| id | Gemini proposal | Accepted at | Why |
|---|---|---|---|
| hedtsk_digit_span | Miller (1956) [new entry] | Miller (1956) [M] | Miller is already doing duty for hed_chunking and the magical-number paper is not really a digit-span origin — Jacobs (1887) *Mind* is the task origin but is pre-DOI and effectively unindexable. Conway, Kane, Bunting, Hambrick, Wilhelm & Engle (2005) *Psychon Bull Rev* 12:769–786 is a stronger modern review and is a candidate replacement if you prefer. Listed at [M] to keep this decision visible. |

### 9.4 Rejected

Three proposals I did not incorporate, with reasons:

| id | Gemini proposal | Why rejected |
|---|---|---|
| hed_associative_learning | Swap Rescorla (1988) *Annu Rev Neurosci* "Behavioral studies of Pavlovian conditioning" → Rescorla (1988) *Am Psychol* "Pavlovian conditioning: it's not what you think it is" | The *Am Psychol* paper is already the landmark for **hed_pavlovian_conditioning** — the two Rescorla 1988 reviews complement each other, one for the general associative-learning construct and one for the Pavlovian-specific framing. Collapsing them would lose that distinction. |
| hed_motor_control | New entry: Fitts (1954) *J Exp Psychol* | **hed_motor_control does not exist as a process_id in the HED catalog.** The motor processes are `hed_motor_memory`, `hed_motor_planning`, `hed_motor_preparation`, `hed_motor_sequence_learning`, `hed_motor_timing`. Fitts 1954 is an excellent paper but has no landmark slot to fill here. If you want Fitts' Law represented, the natural attachment is `hed_motor_planning` or `hed_motor_preparation` — say so and I'll add it. |
| hed_self_monitoring | New entry: Snyder (1974) *J Pers Soc Psychol* "Self-monitoring of expressive behavior" | **Wrong construct.** Snyder's "self-monitoring" is a social/personality-psychology trait (monitoring one's expressive behavior for social appropriateness). The HED catalog's `hed_self_monitoring` is defined as *"Ongoing evaluation of one's own performance against task goals and expected outcomes"* — performance/metacognitive monitoring. Resolved 2026-04-22 by user decision to carve out a book-chapter exception and use **Nelson & Narens (1990)** *Psychol Learn Motiv* 26:125–173, the seminal object-level / meta-level metamemory framework; see §5 "Carved-out exceptions retained." |

### 9.5 Net effect on the draft

- Four processes moved from §4 (left blank) into §2: `hed_visual_perception` (→ §2.6), `hed_acoustic_processing` (→ §2.2), `hed_inductive_reasoning` (→ §2.13), `hed_self_monitoring` (→ §2.3 — carved-out book-chapter exception, see §5).
- One task added: `hedtsk_digit_span`.
- Six entries upgraded in confidence or strengthened by swap (see §9.1).
- Header counts are now slightly off ("172" in §1 header); a final count should be done before JSON serialization — easier to do that in the serializer than to hand-edit the header now.

---

## 10. New question from the second-pass review

6. **hed_self_monitoring.** ~~The Gemini pass proposed Snyder (1974)...~~
   **Resolved 2026-04-22.** User decision: carve out a book-chapter
   exception and use Nelson & Narens (1990) "Metamemory: a theoretical
   framework and new findings" *Psychol Learn Motiv* 26:125–173 — the
   seminal object-level / meta-level metamemory framework, which is the
   theoretical foundation for the performance-monitoring literature as a
   whole. See §2.3 for the entry and §5 "Carved-out exceptions retained"
   for the `book_chapter_exception: true` flag. Open follow-up question
   for the user: whether to extend this exception to the three other
   Nelson & Narens (1990) substitutions in §5 (hed_feeling_of_knowing,
   hed_metacognitive_monitoring, hed_metacognitive_control) for
   consistency.
