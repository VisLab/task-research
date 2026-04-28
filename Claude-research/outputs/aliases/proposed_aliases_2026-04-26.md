# Proposed process aliases — for review
**Date:** 2026-04-26
**Plan:** `instructions/alias_generation_plan_2026-04-26.md`
**Author:** Claude (Opus)

This file proposes aliases for the ~160 processes that currently have no
aliases. **Nothing has been written to `process_details.json`.** This is a
candidate list for human review.

For each process I list the canonical definition, then either a proposed
alias or an explicit "no aliases proposed" with reasoning. Total proposed
new aliases: **52**, well under the plan's ceiling of ~150.

The criterion for accepting an alias is **substring specificity**, not word
count: would the string match the right papers as a verbatim substring in
the phrase gate, without admitting too many unrelated papers? Single-word
aliases (e.g., `"Pavlovian"`, `"reappraisal"`, `"interoception"`) pass this
test when the term is highly domain-specific. Multi-word aliases are
preferred for terms that would otherwise be ambiguous (e.g., `"memory
encoding"` rather than bare `"encoding"`). Hyphenation variants are listed
separately when both forms appear commonly in titles
(e.g., `"task switching"` and `"task-switching"`), because the phrase gate
does verbatim substring matching.

I tried to err toward fewer rather than more aliases, on the principle that
a missed alias hurts recall but a wrong alias introduces noise that's harder
to diagnose. Where I was uncertain, I marked **(flag)**.

---

## associative_learning_and_reinforcement

**Associative learning**
definition: Learning of co-occurrence relations between stimuli or between stimuli and responses.
- no aliases proposed
  reason: canonical name dominates the literature; no widely used multi-word synonym in titles/abstracts.

**Extinction**
definition: Decrease in a previously reinforced response when reinforcement is withheld; a form of new inhibitory learning rather than erasure.
- alias: "extinction learning"
  reason: many titles (especially in fear-conditioning and rodent literatures) use "extinction learning" instead of bare "extinction". Bare "extinction" is also too lexically ambiguous (species extinction, ecology, etc.) to leave the canonical name as the only phrase, but the canonical is what it is — adding the longer form catches papers that only use the longer form.

**Goal-directed behavior**
definition: Behavior that is sensitive to current outcome value, characteristic of action–outcome learning.
- alias: "goal-directed action"
  reason: routinely used interchangeably in the instrumental learning literature (Dickinson, Balleine, etc.); some papers use only "goal-directed action".

**Habit**
definition: Behavior that is insensitive to the current value of its outcome, characteristic of stimulus–response learning.
- alias: "habit learning"
  reason: some titles use "habit learning" rather than "habit" alone; also disambiguates from non-cognitive uses of "habit" (lifestyle, etc.). Bare "habit" is high-frequency lay vocabulary so titles using only "habit" without context probably aren't relevant anyway — the alias targets the technical literature.

**Instrumental conditioning** *(already has alias)*
- existing aliases: ["Operant conditioning"]
- no new aliases proposed.

**Model-based learning**
definition: Reinforcement learning that uses an internal model of the environment's transition and reward structure to plan.
- alias: "model-based reinforcement learning"
  reason: full form often used in titles (e.g., Daw et al.); shorter "model-based learning" by itself is sometimes paired only with the full form in abstracts.

**Model-free learning**
definition: Reinforcement learning from cached value estimates updated by prediction errors, without an explicit model of the environment.
- alias: "model-free reinforcement learning"
  reason: same rationale as model-based.

**Pavlovian conditioning**
definition: Learning that a neutral stimulus predicts a biologically significant outcome, leading to conditioned responding.
- alias: "classical conditioning"
  reason: classical and Pavlovian are used interchangeably across the field; older literature is dominated by "classical conditioning".
- alias: "Pavlovian"
  reason: highly specific term — almost any paper containing "Pavlovian" is about Pavlovian conditioning or related paradigms. Catches titles like "Pavlovian-instrumental transfer", "Pavlovian fear conditioning" (with intervening words), and "Pavlovian responses" that wouldn't match canonical "Pavlovian conditioning" verbatim.

**Policy learning**
definition: Direct learning of a mapping from states to actions without necessarily estimating values.
- no aliases proposed
  reason: no widely used multi-word synonym; "policy gradient learning" is a method, not a synonym.

**Reinforcement learning**
definition: Learning to select actions that maximize cumulative reward through experience with reward prediction errors.
- no aliases proposed
  reason: term is dominant. "Reward learning" is used loosely but is broader (includes Pavlovian); risk of admitting the wrong scope.

**Reversal learning**
definition: Relearning after contingencies between stimuli (or responses) and outcomes are switched.
- no aliases proposed
  reason: term is dominant; "discrimination reversal" refers to a paradigm.

**Reward prediction error**
definition: Signed difference between received and expected reward, instantiated by phasic midbrain dopamine firing.
- no aliases proposed
  reason: term is dominant. "Prediction error" alone is too broad (sensory PE, semantic PE, etc.); "RPE" is an abbreviation (excluded by plan).

**Value learning**
definition: Acquisition of the expected value of stimuli, actions, or states from experience with outcomes.
- no aliases proposed
  reason: closely related terms ("reward learning", "value updating") are either broader or refer to a sub-aspect.

---

## auditory_and_pre_attentive_deviance_processing

**Acoustic processing**
definition: Low-level analysis of sound, including frequency, intensity, and temporal structure.
- no aliases proposed
  reason: closely-related sibling "auditory perception" already covers most candidate synonyms; risk of admitting overlapping papers.

**Auditory perception**
definition: Perception of sound, including pitch, timbre, loudness, and spatial location.
- no aliases proposed
  reason: dominant term; "audition" alone is single word; "hearing" is too broad and too lay.

**Auditory tone discrimination**
definition: Judgment of whether two tones differ in pitch, intensity, or duration.
- alias: "tone discrimination"
  reason: many papers use "tone discrimination" without the "auditory" prefix; substantial body of literature would otherwise be missed by phrase gate.

**Pitch perception**
definition: Perception of the highness or lowness of a sound, related to fundamental frequency.
- alias: "pitch processing"
  reason: used interchangeably in psychoacoustics and music cognition.

---

## awareness_agency_and_metacognition

**Attentional awareness**
definition: Awareness of the current focus and content of attention.
- no aliases proposed
  reason: relatively recent technical term; no established synonym in titles.

**Body ownership**
definition: The experience that a body or body-part belongs to the self...
- no aliases proposed
  reason: dominant term in this literature (rubber-hand illusion line of work). "Embodiment" is broader.

**Feeling of knowing**
definition: Judgment that information currently not retrievable would be recognized if presented.
- no aliases proposed
  reason: dominant term. "FOK" is an abbreviation.

**Interoceptive awareness**
definition: Conscious perception of internal bodily signals such as heartbeat, respiration, and visceral state...
- alias: "interoception"
  reason: highly domain-specific term; parallels existing aliases for sibling perceptual modalities (`Gustation` for Gustatory perception, `Somatosensation` for Somatosensory perception). Covers slightly more than "awareness" alone (also includes mechanism), but the field uses the two largely interchangeably.

**Judgment of learning**
definition: Prediction of future memory performance made during or after encoding.
- no aliases proposed
  reason: dominant term. "JOL" is an abbreviation.

**Masking**
definition: Reduction in visibility or detectability of a target stimulus by a temporally or spatially adjacent masker.
- no aliases proposed
  reason: subtypes ("backward masking", "visual masking") would narrow rather than synonymize; canonical single-word name is dominant.

**Metacognitive control**
definition: Regulation of cognition based on metacognitive monitoring...
- no aliases proposed
  reason: term is dominant; "metamemory control" is restricted to memory metacognition.

**Metacognitive monitoring**
definition: Second-order evaluation of ongoing first-order cognition...
- no aliases proposed
  reason: dominant term.

**Mind wandering**
definition: Task-unrelated thought that arises during an ongoing task.
- alias: "task-unrelated thought"
  reason: Smallwood & Schooler and successors use this as the primary technical synonym in titles/abstracts.
- alias: "mind-wandering"
  reason: hyphenated form is at least as common in titles as the unhyphenated canonical; phrase gate does verbatim substring matching, so both forms need to be present.

**Perceptual awareness**
definition: Conscious access to perceptual content.
- alias: "conscious perception"
  reason: "conscious perception" is widely used in the consciousness literature interchangeably with perceptual awareness.

**Self-monitoring**
definition: Ongoing evaluation of one's own performance against task goals and expected outcomes.
- no aliases proposed
  reason: closely related "performance monitoring" is broader (includes monitoring of others) — risk of admitting parent-construct papers.

**Self-referential processing**
definition: Processing of information in relation to the self...
- alias: "self-referential"
  reason: papers using "self-referential cognition" or "self-referential encoding" wouldn't match canonical "self-referential processing" verbatim. The bare adjective "self-referential" is highly specific to this construct and adds little noise.

**Sense of agency**
definition: The experience of being the cause of one's own actions and their sensory consequences...
- no aliases proposed
  reason: dominant term. "Agency judgment" is a measure; "feeling of agency" is sometimes used but the canonical dominates.

---

## cognitive_flexibility_and_higher_order_executive_function

**Goal maintenance**
definition: Active holding of task goals, rules, or sub-goals in a form that biases ongoing processing.
- no aliases proposed
  reason: term is dominant; "goal shielding" (Goschke et al.) is a related but distinct construct.

**Set shifting** *(already has alias)*
- existing aliases: ["Cognitive flexibility"]
- **proposed addition: "task switching"**
  reason: dominant experimental-paradigm term in the literature (Monsell, Rogers & Monsell, Meiran). The plan explicitly flagged this gap.
- **proposed addition: "task-switching"**
  reason: hyphenated variant is widely used (especially in titles); phrase gate uses verbatim substring matching so both forms need to be present.

**Strategy use**
definition: Selection and implementation of a cognitive procedure chosen to improve performance on a task.
- no aliases proposed
  reason: "strategy selection" is one phase of strategy use; "strategic processing" is broader.

---

## emotion_perception_and_regulation

**Affective priming**
definition: Facilitation or interference in evaluating a target by a valence-related prime.
- alias: "evaluative priming"
  reason: term used interchangeably; some traditions (e.g., Fazio) prefer "evaluative priming".

**Cognitive reappraisal**
definition: Reinterpretation of an emotional stimulus to change its affective impact.
- alias: "reappraisal"
  reason: dominant short form in the emotion-regulation literature; many Gross-tradition papers use only "reappraisal" in titles. Specific enough that substring-matching risk is low — outside emotion regulation, the term mostly appears in legal/financial contexts (real-estate reappraisal, asset reappraisal) which won't be in the candidate retrieval pool.

**Emotion recognition** *(already has alias)*
- existing aliases: ["Emotion perception"]
- no new aliases proposed.

**Emotion regulation**
definition: Processes by which individuals influence which emotions they have, when, and how they experience and express them.
- no aliases proposed
  reason: term is dominant (Gross's framework). "Affect regulation" is occasional but broader.

**Expressive suppression**
definition: Inhibition of outward behavioral expression of emotion.
- no aliases proposed
  reason: term is the canonical Gross-tradition name; "emotion suppression" is too broad and conflates with other regulation strategies.

---

## face_and_object_perception

**Biological motion perception**
definition: Recognition of animate motion from sparse kinematic cues, such as point-light displays.
- alias: "biological motion"
  note: common 2-word shorthand in titles even when the paper is about perception of biological motion.
  reason: many titles drop "perception" and just say "biological motion" (e.g., "Biological motion in the visual cortex"). Without this alias the phrase gate would silently drop those papers.

**Depth perception**
definition: Perception of distance and three-dimensional structure from monocular and binocular cues.
- no aliases proposed
  reason: "stereopsis" is single word and refers to one mechanism (binocular). Canonical is dominant.

**Face identity recognition**
definition: Identification of an individual from face-specific features.
- alias: "face recognition"
  reason: "face recognition" is the dominant historical term in the field (Bruce & Young 1986; classic literature). Without this alias a major fraction of the relevant literature would be missed by the phrase gate.
  **(flag — slight overlap risk with sibling "Face perception"; in practice "face recognition" almost always refers to identity recognition in cog-neuro contexts, but a small fraction of papers may be admitted into the wrong pool.)**

**Face perception**
definition: Recognition and processing of faces as a specialized perceptual category; N170-sensitive, FFA-dependent.
- alias: "face processing"
  reason: very widely used as a near-synonym; many papers titled "face processing" address face perception specifically.

**Gustatory perception** *(already has alias)*
- existing aliases: ["Gustation"]

**Motion perception**
definition: Detection and interpretation of moving stimuli; includes global motion and optic flow.
- no aliases proposed
  reason: "visual motion processing" is a candidate but overlaps with sibling "Visual perception"; canonical is dominant.

**Olfactory perception**
definition: Perception of odor via the olfactory system.
- alias: "olfaction"
  reason: parallels existing aliases for sibling processes (`Gustation` for Gustatory perception, `Somatosensation` for Somatosensory perception). Highly specific term — not a substring of unrelated common words.

**Pattern recognition**
definition: Categorization of sensory input according to its structure.
- no aliases proposed
  reason: term has heavy use outside cognitive science (machine learning, signal processing) — adding even multi-word aliases would risk admitting non-cognitive papers.

**Somatosensory perception** *(already has alias)*
- existing aliases: ["Somatosensation"]

**Visual form recognition**
definition: Assignment of visual input to a shape category prior to semantic identification.
- alias: "shape recognition"
  reason: "shape recognition" is a more common 2-word title phrase; "form recognition" alone rarely appears without "visual".

**Visual object recognition**
definition: Identification of objects from visual input, invariant over viewpoint, size, and lighting.
- alias: "object recognition"
  reason: dominant short form in titles (DiCarlo, Riesenhuber, etc.); "visual object recognition" is the canonical but most papers say "object recognition" alone.

**Visual perception**
definition: Perception of visual information; includes form, motion, depth, color, and spatial layout.
- no aliases proposed
  reason: most candidates ("vision", "visual processing") are either too broad or substring-match too widely; canonical is dominant.

---

## implicit_and_statistical_learning

**Implicit memory**
definition: Memory expressed without conscious recollection, measurable by priming, skill learning, and conditioning.
- no aliases proposed
  reason: "nondeclarative memory" is broader (includes procedural memory, a sibling). Canonical is dominant in the implicit-memory literature.

**Procedural memory**
definition: Non-declarative memory for skills and procedures...
- no aliases proposed
  reason: "procedural learning" is the acquisition counterpart, not strictly a synonym. Canonical is dominant.

---

## inhibitory_control_and_conflict_monitoring

*(this category is sensitive — sibling boundaries matter)*

**Conflict monitoring**
definition: Detection of co-activation of incompatible response tendencies...
- no aliases proposed
  reason: term is dominant (Botvinick et al. line of work). "Conflict detection" is a candidate but risks overlap with sibling "Error detection".

**Error correction**
definition: Adjustment of behavior following an error, including post-error slowing and improvement on subsequent trials.
- no aliases proposed
  reason: "post-error adjustment" is closely related but typically refers to behavioral signatures rather than the process. Canonical is dominant.

**Error detection**
definition: Recognition that a response was incorrect, indexed by the error-related negativity (ERN) and by error awareness.
- no aliases proposed
  reason: "error monitoring" is broader and would admit Conflict-monitoring/Self-monitoring papers — risk of overlap.

**Executive attention**
definition: Resolution of conflict among thoughts, feelings, and responses; one of Posner's three attentional networks.
- no aliases proposed
  reason: "attentional control" is a tempting candidate but is a parent construct (broader). Risk of admitting general-EF papers.

**Interference control**
definition: Resistance to interference from task-irrelevant stimuli or competing response representations...
- alias: "interference resolution"
  reason: used as a synonym in the Bunge/Aron/Friedman lines of research.

**Proactive control**
definition: Sustained, anticipatory maintenance of task goals that biases processing in preparation for an expected demand.
- no aliases proposed
  reason: technical term (Braver's dual mechanisms framework); no established synonym.

**Reactive control**
definition: Transient, stimulus-triggered engagement of control after interference or conflict is detected.
- no aliases proposed
  reason: same — paired technical term to proactive control.

**Response conflict**
definition: Competing activation of two or more response representations on a single trial...
- no aliases proposed
  reason: term is dominant; "stimulus-response conflict" is a paradigm-specific variant.

**Response inhibition**
definition: Suppression of a prepotent or already-initiated response when it becomes inappropriate, indexed behaviorally by stop-signal reaction time or commission errors.
- alias: "inhibitory control"
  reason: explicitly endorsed in the plan. The category-level term "inhibitory control" is also broadly used as a near-synonym for response inhibition in motor/SSRT literature.
  **(flag — slight breadth concern: some papers using "inhibitory control" may be discussing the broader executive umbrella, but in practice most cog-neuro response-inhibition papers use the two terms interchangeably.)**
- alias: "response suppression"
  note: more common in motor-control and oculomotor literatures.
  reason: classic synonym, especially in older motor-inhibition work.

---

## language_comprehension_and_production

**Discourse processing**
definition: Integration of sentences into coherent representations of extended text or conversation.
- no aliases proposed
  reason: "discourse comprehension" is closely related but emphasizes comprehension specifically; canonical "discourse processing" is broader and dominant.

**Language comprehension**
definition: Extraction of meaning from linguistic input (spoken, written, or signed).
- no aliases proposed
  reason: candidates ("language understanding") are informal; sibling processes (Sentence comprehension, Discourse processing) cover the more common subordinate phrases.

**Language production**
definition: Generation of spoken, written, or signed linguistic output, from message to articulation.
- no aliases proposed
  reason: dominant term; "speaking" is too broad.

**Lexical access**
definition: Retrieval of word-level representations (form and meaning) from memory.
- alias: "lexical retrieval"
  reason: used interchangeably in psycholinguistics; some papers use "lexical retrieval" as primary term.

**Naming**
definition: Production of a word label for a presented stimulus (e.g., picture naming).
- no aliases proposed
  reason: "picture naming" is a paradigm; bare "naming" is generic but is the canonical name.

**Phonological awareness**
definition: Explicit awareness of the sound structure of spoken words (onsets, rimes, phonemes).
- no aliases proposed
  reason: dominant term in reading/literacy literature.

**Phonological encoding**
definition: Assembly of phonological representations during language production.
- no aliases proposed
  reason: technical term (Levelt model); no established synonym.

**Reading**
definition: Visual processing of written text, integrating orthography, phonology, and meaning.
- no aliases proposed
  reason: canonical is single-word and dominant; "reading comprehension" is a sub-aspect/skill.

**Semantic knowledge**
definition: Long-term store of facts, concepts, and word meanings.
- no aliases proposed
  reason: closely related "conceptual knowledge" is broader (extends beyond linguistic meaning); risk of scope creep.

**Semantic processing**
definition: Access and integration of word and phrase meaning, indexed by the N400.
- no aliases proposed
  reason: dominant term; "semantic access" is a sub-step of semantic processing.

**Sentence comprehension**
definition: Integration of lexical, syntactic, and semantic information to derive sentence meaning.
- alias: "sentence processing"
  reason: standard psycholinguistic term, often used interchangeably with sentence comprehension; some papers use only "sentence processing" in titles.

**Speech perception**
definition: Extraction of linguistic content from the acoustic speech signal...
- no aliases proposed
  reason: dominant term; "speech recognition" overlaps too heavily with the engineering/ASR literature.

**Speech production**
definition: Planning and articulation of spoken output...
- no aliases proposed
  reason: dominant term; sibling processes (Phonological encoding, Vocal-motor control) cover finer-grained aspects.

**Syntactic parsing**
definition: Assignment of hierarchical grammatical structure to a linguistic input.
- alias: "syntactic processing"
  reason: many psycholinguistic papers use "syntactic processing" rather than "parsing"; ERP/fMRI titles especially.

**Verbal fluency**
definition: Rapid generation of words under a semantic or phonemic constraint.
- no aliases proposed
  reason: dominant term in the assessment literature.

**Word recognition** *(already has alias)*
- existing aliases: ["Visual word recognition"]

---

## long_term_memory

*(per plan note: many of these are generic single words; aliases should be added only where a multi-word synonym is dominant)*

**Autobiographical memory**
definition: Memory for personally experienced events across the lifespan...
- no aliases proposed
  reason: dominant term.

**Consolidation**
definition: Post-encoding stabilization of memory traces, dependent on time and often on sleep...
- alias: "memory consolidation"
  reason: bare "consolidation" is heavily polysemous (immunology, finance, business); "memory consolidation" is the dominant title form in the relevant literature.

**Declarative memory**
definition: Consciously accessible memory for facts and events; encompasses semantic and episodic memory.
- alias: "explicit memory"
  reason: widely used as a synonym (e.g., Squire). Some papers use only "explicit memory" without "declarative".

**Directed forgetting**
definition: Reduced memory for items that have been cued to be forgotten, relative to items cued to be remembered.
- no aliases proposed
  reason: dominant term; specific paradigm.

**Encoding**
definition: Processes by which perceptual input is transformed into a memory representation at acquisition.
- alias: "memory encoding"
  reason: bare "encoding" is heavily polysemous (neural encoding, character encoding, protein encoding). "Memory encoding" disambiguates and is widely used in cognitive-neuroscience titles.

**Episodic memory**
definition: Memory for specific events located in a particular place and time...
- no aliases proposed
  reason: dominant term (Tulving's coinage).

**Familiarity**
definition: Sense that a stimulus has been encountered before, in the absence of retrieval of contextual detail.
- no aliases proposed
  reason: canonical is single-word. Multi-word candidates ("familiarity-based recognition") are subordinate.

**Forgetting**
definition: Loss of accessibility of previously encoded information, due to decay, interference, or retrieval failure.
- no aliases proposed
  reason: canonical is single-word. "Memory loss" implies pathology.

**Pattern completion**
definition: Retrieval of a complete memory from a partial or degraded cue; CA3 function.
- no aliases proposed
  reason: dominant technical term.

**Pattern separation**
definition: Transformation of similar input patterns into distinct, non-overlapping memory representations; dentate gyrus function.
- no aliases proposed
  reason: dominant technical term.

**Proactive interference**
definition: Disruption of new learning by previously learned material.
- no aliases proposed
  reason: dominant term.

**Prospective memory**
definition: Memory for intentions to act at a future time or on a future event.
- no aliases proposed
  reason: dominant term.

**Recall**
definition: Retrieval of items without an external cue provided at test (free or cued recall).
- no aliases proposed
  reason: per plan, subset terms ("free recall", "cued recall") should not be aliases since the canonical covers both.

**Recognition**
definition: Judgment that a test item has been previously encountered; supported by familiarity and recollection.
- alias: "recognition memory"
  reason: bare "recognition" is heavily polysemous (face recognition, pattern recognition, speech recognition, object recognition). "Recognition memory" disambiguates and is the standard title form.

**Recollection**
definition: Retrieval of contextual detail about a prior event, including source information.
- no aliases proposed
  reason: canonical is single-word but reasonably specific in cognitive contexts.

**Reconsolidation**
definition: Destabilization and re-stabilization of a memory upon retrieval...
- alias: "memory reconsolidation"
  reason: bare "reconsolidation" is also used in non-memory contexts (debt reconsolidation, etc., though rarer); "memory reconsolidation" is standard in titles.

**Retrieval**
definition: Reactivation of a stored memory representation; dissociable into cue-driven and strategic retrieval.
- alias: "memory retrieval"
  reason: bare "retrieval" is heavily polysemous (information retrieval, data retrieval). "Memory retrieval" disambiguates.

**Retroactive interference**
definition: Disruption of older memories by newly learned material.
- no aliases proposed
  reason: dominant term.

**Semantic memory**
definition: Long-term store of general knowledge about the world...
- no aliases proposed
  reason: dominant term (Tulving's coinage).

**Source memory**
definition: Memory for the contextual origin of information (e.g., who said it, where it was seen).
- alias: "source monitoring"
  note: Johnson, Hashtroudi & Lindsay (1993) tradition.
  reason: "source monitoring" is the dominant title form in much of the source-memory literature; without it the source-monitoring framework's papers may be missed.

**Verbal memory**
definition: Memory for linguistic material (words, sentences), tested via word lists, story recall, and RAVLT.
- no aliases proposed
  reason: dominant term in clinical neuropsychology.

---

## motor_preparation_timing_and_execution

**Action initiation**
definition: Triggering of an action after planning is complete.
- no aliases proposed
  reason: technical term; no established synonym.

**Antisaccade**
definition: Voluntary eye movement away from a peripheral stimulus, requiring inhibition of a prepotent saccade.
- alias: "anti-saccade"
  reason: hyphenated form is at least as common as the unhyphenated form in titles; the phrase gate does verbatim substring matching, so both spellings need to be present.

**Fine motor control**
definition: Precise control of small-amplitude movements, typically of the hand and fingers.
- no aliases proposed
  reason: "fine motor skill" emphasizes skill rather than control; subtle but distinct.

**Grasping**
definition: Shaping and closure of the hand around an object.
- no aliases proposed
  reason: canonical is single-word; "reach-to-grasp" is a paradigm.

**Motor memory**
definition: Long-term retention of motor skills and procedures.
- no aliases proposed
  reason: closely related "motor learning" is the acquisition counterpart and would admit non-memory papers — risk of scope creep.

**Motor planning**
definition: Specification of movement parameters before execution.
- alias: "movement planning"
  reason: used interchangeably; some titles use only "movement planning".

**Motor preparation**
definition: Neural readiness state preceding movement, indexed by the readiness potential and LRP.
- alias: "movement preparation"
  reason: same rationale.

**Motor sequence learning**
definition: Acquisition of a skilled sequence of movements through repetition.
- no aliases proposed
  reason: candidates ("sequence learning" alone, "motor skill learning") are either broader or differ in scope.

**Motor timing**
definition: Production or estimation of temporal intervals in motor output.
- no aliases proposed
  reason: dominant term; "timing" alone is too broad.

**Proprioception**
definition: Perception of body position and movement from muscle, tendon, and joint receptors.
- no aliases proposed
  reason: canonical is single-word and highly specific; no common multi-word synonym.

**Reaching**
definition: Goal-directed arm movement toward a spatial target.
- no aliases proposed
  reason: canonical is single-word.

**Response execution**
definition: Overt production of a selected response in accordance with task demands.
- alias: "movement execution"
  reason: used in motor-control literature as a near-synonym (especially when the "response" is a movement rather than a key press).

**Response selection**
definition: Choice of an action from a set of alternatives.
- alias: "action selection"
  reason: dominant term in basal-ganglia and motor-control literature; "response selection" is more cognitive-psychology, "action selection" is more neuroscience — papers in either tradition often use only one.

**Saccade**
definition: Rapid ballistic eye movement between points of fixation.
- alias: "saccadic"
  reason: morphological variant — papers titled or described with "saccadic eye movement", "saccadic latency", "saccadic adaptation" do not contain "saccade" as a verbatim substring. Single word, highly specific to oculomotor literature.

**Visuomotor adaptation**
definition: Recalibration of movement in response to perturbations of the mapping between vision and action.
- alias: "sensorimotor adaptation"
  reason: used as a near-synonym, especially for prism-adaptation and force-field studies.

**Vocal-motor control**
definition: Control of the articulators for speech production and vocalization.
- alias: "speech motor control"
  reason: dominant term in the speech-motor literature; "vocal-motor control" is a less common phrasing.

---

## perceptual_decision_making_evidence_accumulation

**Perceptual decision making**
definition: Integration of noisy sensory evidence toward a decision criterion...
- no aliases proposed
  reason: dominant term.

---

## reasoning_and_problem_solving

**Analogical reasoning**
definition: Mapping of relational structure from a source domain to a target domain.
- no aliases proposed
  reason: dominant term; "relational reasoning" is broader.

**Categorization**
definition: Assignment of instances to categories according to their features.
- no aliases proposed
  reason: canonical is single-word but standard. "Category learning" is the acquisition counterpart.

**Causal reasoning**
definition: Inference about cause–effect relations from observation and intervention.
- alias: "causal inference"
  reason: used interchangeably in the cognitive-psychology literature; some papers use "causal inference" as the primary term.
  **(flag — small risk of admitting statistical-methods papers that use "causal inference" in the Pearl/Rubin sense; these are usually distinguishable by context, but worth knowing.)**

**Deductive reasoning** *(already has alias)*
- existing aliases: ["Logical reasoning"]

**Hypothesis testing**
definition: Generation and evaluation of alternative explanations against evidence.
- no aliases proposed
  reason: dominant term; ambiguous with statistical hypothesis testing but the canonical already has that issue.

**Inductive reasoning**
definition: Inference from specific instances to general principles; probabilistic rather than necessary.
- no aliases proposed
  reason: dominant term; "induction" alone is too broad.

**Insight**
definition: Sudden restructuring of a problem representation yielding a solution that was previously unavailable...
- no aliases proposed
  reason: canonical is single-word and dominant in insight-problem-solving literature. Adding "insight problem solving" as a longer phrase would still gate against papers using only "insight".

**Mathematical reasoning**
definition: Manipulation of numerical and algebraic quantities and relations.
- no aliases proposed
  reason: "mathematical cognition" is broader (includes numerical perception); "numerical reasoning" is narrower.

**Means-ends analysis**
definition: Iterative problem-solving strategy in which the distance between the current state and the goal state is reduced...
- no aliases proposed
  reason: dominant technical term (Newell & Simon).

**Planning**
definition: Mental formulation of a sequence of actions toward a goal before execution.
- no aliases proposed
  reason: canonical is single-word; multi-word candidates ("action planning", "cognitive planning") are either narrower or non-standard.

**Subgoaling**
definition: Decomposition of a goal into an ordered sequence of subgoals...
- no aliases proposed
  reason: technical term; no established synonym.

---

## reward_anticipation_and_motivation

**Approach motivation**
definition: Tendency to engage with stimuli associated with positive outcomes.
- no aliases proposed
  reason: "behavioral approach" is closely related but emphasizes behavior rather than the motivational state.

**Avoidance motivation**
definition: Tendency to disengage from stimuli associated with negative outcomes.
- no aliases proposed
  reason: same — "behavioral avoidance" is closely related but distinct.

**Effort allocation**
definition: Decision to expend physical or cognitive effort as a function of expected reward and cost.
- no aliases proposed
  reason: "effort-based decision making" is closely related but conflicts with the sibling category Value-Based Decision-Making.

**Incentive salience**
definition: "Wanting" attributed to reward-predictive cues, distinct from "liking."
- no aliases proposed
  reason: technical term (Berridge); no established synonym.

**Reward anticipation**
definition: Affective and neural response to cues predicting upcoming reward.
- no aliases proposed
  reason: dominant term.

**Reward consumption**
definition: Affective and neural response to receipt of reward.
- no aliases proposed
  reason: candidates ("reward receipt", "hedonic response") are either rare or refer to subaspects (hedonic = "liking" specifically).

---

## selective_and_sustained_attention

**Alerting**
definition: Achieving and maintaining a state of readiness to respond, whether tonic or phasic; one of Posner's three attentional networks.
- no aliases proposed
  reason: technical term tied to Posner's tradition.

**Attention shifting**
definition: Reorienting of attention from one location, feature, or object to another...
- no aliases proposed
  reason: candidates ("shifting attention", "attentional shifting") are word-order variants — the phrase gate does substring matching, so "attention shift" / "attentional shift" / "attention shifting" all match the canonical "Attention shifting" only partially. **Worth verifying empirically whether the phrase gate handles these as substrings.**

**Attentional capture**
definition: Involuntary shift of attention to a salient stimulus...
- no aliases proposed
  reason: dominant term.

**Divided attention**
definition: Concurrent processing of two or more streams of information...
- no aliases proposed
  reason: "dual-task performance" is paradigm-specific.

**Feature-based attention**
definition: Selection of a specific visual feature...
- no aliases proposed
  reason: dominant term.

**Object-based attention**
definition: Selection of an object as a unit of attention...
- no aliases proposed
  reason: dominant term.

**Orienting**
definition: Selection of information from sensory input, typically in space...
- no aliases proposed
  reason: technical term in Posner's tradition; canonical is single-word.

**Selective attention**
definition: Prioritized processing of a task-relevant subset of stimuli...
- no aliases proposed
  reason: dominant term.

**Spatial attention**
definition: Selection of a location in space for preferential sensory processing...
- no aliases proposed
  reason: dominant term.

**Sustained attention** *(already has alias)*
- existing aliases: ["Vigilance"]

**Temporal attention**
definition: Selection of a point in time for preferential processing...
- no aliases proposed
  reason: dominant term.

---

## short_term_and_working_memory

**Active maintenance** *(already has alias)*
- existing aliases: ["Maintenance"]
- **(flag — see end note about whether "Maintenance" is too generic.)**

**Chunking**
definition: Binding of multiple items into a single unit in memory to expand effective capacity.
- no aliases proposed
  reason: canonical is single-word and specific in memory contexts.

**Manipulation**
definition: Transformation of information held in working memory...
- no aliases proposed
  reason: bare "manipulation" is highly polysemous; longer phrases ("WM manipulation", "working memory manipulation") are uncommon as standalone titles. Would be a useful target for the WM-related candidate pool to be combined with category-level filtering rather than aliases.

**Rehearsal**
definition: Covert repetition of material to refresh its representation in short-term memory...
- no aliases proposed
  reason: canonical is single-word; "articulatory rehearsal" is a subtype.

**Spatial working memory**
definition: Short-term storage of spatial locations and spatial relations.
- no aliases proposed
  reason: dominant term.

**Verbal working memory**
definition: Short-term storage of phonological/verbal information, historically "phonological loop"...
- alias: "phonological loop"
  note: Baddeley working memory model; the definition itself flags this synonym.
  reason: a substantial body of working-memory papers uses "phonological loop" as the primary term.

**Visual working memory**
definition: Short-term storage and manipulation of visual information; capacity limited to ~3–4 items.
- no aliases proposed
  reason: "visuospatial sketchpad" is the Baddeley term but encompasses both visual and spatial — risks scope mismatch with the sibling Spatial working memory.

**Working memory**
definition: System for the short-term maintenance, updating, and manipulation of task-relevant information...
- no aliases proposed
  reason: dominant term.

**Working memory updating** *(already has aliases)*
- existing aliases: ["Updating", "Updating (WM)"]
- **(flag — see end note about whether these existing aliases work in practice.)**

---

## social_cognition_and_strategic_social_choice

**Competition**
definition: Action in conflict with another agent's interests for a contested resource.
- no aliases proposed
  reason: bare "competition" is too generic across contexts (economic competition, competitive games, etc.) — adding it as alias would not help; canonical word will already gate the same papers (and the same noise).

**Cooperation**
definition: Coordinated action among agents for mutual benefit, often at individual cost.
- no aliases proposed
  reason: same reasoning as Competition.

**Imitation**
definition: Reproduction of observed actions or behaviors.
- no aliases proposed
  reason: canonical is single-word and standard in the social-cognition literature.

**In-group/out-group processing**
definition: Differential processing of members of one's own group versus other groups.
- alias: "intergroup processing"
  reason: more compact title form widely used in social-cognitive neuroscience; the slash in the canonical name may not appear in titles.

**Joint attention**
definition: Coordinated focus by two or more agents on the same object or event...
- no aliases proposed
  reason: dominant term.

**Perspective taking** *(already has aliases)*
- existing aliases: ["Mentalizing", "Theory of mind"]

**Reciprocity**
definition: Contingent positive or negative responses to another's prior behavior.
- no aliases proposed
  reason: bare "reciprocity" is too polysemous (legal, biological, etc.); dominant in social/economic-game papers.

**Self-other distinction**
definition: Discrimination between self-generated and other-generated states or actions.
- no aliases proposed
  reason: candidates ("self-other discrimination") differ minimally from canonical.

**Social decision making**
definition: Choice involving other agents and their preferences, often in strategic settings.
- no aliases proposed
  reason: "social choice" overlaps with the economics term (voting, aggregation); risk of admitting wrong-domain papers.

**Social perception**
definition: Visual perception of socially relevant stimuli, including faces, bodies, and actions.
- no aliases proposed
  reason: dominant term.

**Stereotyping**
definition: Attribution of attributes to individuals based on social category membership.
- no aliases proposed
  reason: canonical is single-word but very specific to social cognition.

---

## spatial_cognition_and_navigation

**Mental rotation**
definition: Imagined rotation of a 2D or 3D figure to compare with another figure...
- no aliases proposed
  reason: dominant term (Shepard & Metzler tradition).

**Spatial memory**
definition: Memory for the arrangement and location of objects and environments.
- no aliases proposed
  reason: dominant term; "allocentric memory" is a subtype.

---

## value_based_decision_making_under_risk_and_uncertainty

**Choice commitment**
definition: The act of locking in a selected option once accumulated evidence or value crosses a decision boundary...
- no aliases proposed
  reason: relatively recent technical term; no established synonym.

**Delay discounting**
definition: Devaluation of a reward as a function of the delay to its receipt, typically hyperbolic.
- alias: "temporal discounting"
  reason: used interchangeably; some traditions prefer "temporal discounting".

**Intertemporal choice**
definition: Choice among options that differ in timing of outcomes...
- alias: "intertemporal decision making"
  reason: used as the longer form in many titles.

**Probability judgment**
definition: Estimation of likelihoods of events, often deviating from normative Bayes.
- alias: "probability estimation"
  reason: used as a near-synonym; particularly in the calibration and judgment-under-uncertainty literature.

**Risk processing** *(already has alias)*
- existing aliases: ["Risky decision making"]

**Valuation**
definition: Assignment of a subjective value to a prospective option...
- no aliases proposed
  reason: bare "valuation" is single-word and polysemous (asset valuation, etc.); "subjective valuation" is sometimes used but the canonical is dominant. Worth flagging — heavy non-cognitive overlap.

**Value-based decision making**
definition: Choice among options that differ in subjective value, computed across attributes.
- alias: "value-based choice"
  reason: shorter title form widely used, especially in computational neuroscience.

---

# Concerns about *existing* aliases (per plan request)

A few existing aliases in the catalog look problematic given how the phrase
gate works (verbatim substring matching against title + abstract + TLDR).
Worth a separate review pass:

1. **Set shifting** has only `["Cognitive flexibility"]`. Should add
   `"task switching"` — the dominant experimental-paradigm term in the
   literature (Monsell, Rogers & Monsell, Meiran). The plan flagged this.

2. **Working memory updating** has `["Updating", "Updating (WM)"]`.
   - `"Updating"` substring-matches a huge variety of unrelated text
     ("updating priors", "updating estimates", "updating parameters",
     etc., across many fields). The substring is too generic, regardless
     of word count, to be a clean alias.
   - `"Updating (WM)"` is unlikely to ever match — papers don't typically
     write `(WM)` inline in their abstracts. Effectively a dead alias.
   - Suggested replacements: `"working memory updating"` (catches papers
     using the longer form without "updating" alone admitting noise) and
     possibly `"WM updating"` if you want to admit papers that only use
     the abbreviated form.

3. **Active maintenance** has `["Maintenance"]`. Same substring-specificity
   concern as `"Updating"`: bare `"maintenance"` matches building
   maintenance, system maintenance, etc. Consider replacing with
   `"working memory maintenance"` or removing.

4. **Sustained attention** has `["Vigilance"]`. Single-word but
   substring-specific — `"vigilance"` is largely confined to the
   sustained-attention literature in cog-neuro contexts. Probably OK.

5. **Gustatory perception** has `["Gustation"]`, **Somatosensory perception**
   has `["Somatosensation"]`. Highly substring-specific; good aliases.
   My proposed `"olfaction"` for Olfactory perception parallels these.

# Summary

| Category | New aliases proposed |
|---|---|
| associative_learning_and_reinforcement | 7 |
| auditory_and_pre_attentive_deviance_processing | 2 |
| awareness_agency_and_metacognition | 5 |
| cognitive_flexibility_and_higher_order_executive_function | 2 (additions to existing) |
| emotion_perception_and_regulation | 2 |
| face_and_object_perception | 6 |
| implicit_and_statistical_learning | 0 |
| inhibitory_control_and_conflict_monitoring | 3 |
| language_comprehension_and_production | 3 |
| long_term_memory | 7 |
| motor_preparation_timing_and_execution | 8 |
| perceptual_decision_making_evidence_accumulation | 0 |
| reasoning_and_problem_solving | 1 |
| reward_anticipation_and_motivation | 0 |
| selective_and_sustained_attention | 0 |
| short_term_and_working_memory | 1 |
| social_cognition_and_strategic_social_choice | 1 |
| spatial_cognition_and_navigation | 0 |
| value_based_decision_making_under_risk_and_uncertainty | 4 |
| **Total** | **52** |

Plus 4 existing aliases recommended for review.
