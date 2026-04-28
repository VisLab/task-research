# Alias generation plan for HED process catalog
**Date:** 2026-04-26  
**Author:** session notes (for Opus)  
**Task:** Propose aliases for ~160 processes that currently have none

---

## Context you need to understand first

The HED (Hierarchical Event Descriptor) project maintains a catalog of
~172 cognitive processes (`process_details.json`). Each process has a
canonical `process_name` and an `aliases` list. These aliases are not
decorative — they are load-bearing in a literature search pipeline that
runs systematic PubMed-equivalent queries for every process.

**You are being asked to propose aliases.** The human domain expert will
review and approve before anything is written to the data file. Your job
is to produce a well-reasoned candidate list, not a final one.

---

## How aliases are used in the search pipeline

Understanding this is essential to generating useful aliases rather than
plausible-sounding ones.

### 1. Semantic Scholar sub-queries (Stage A)
Each alias becomes a **separate HTTP search query** to the S2 API. Multi-word
aliases are quoted (`"inhibitory control"`) so S2 treats them as phrases.
Single-word aliases are sent bare, which means they match any paper
containing that word — far too broad to be useful.

Consequence: aliases with only one word are nearly useless for S2 and add
API call overhead. Prefer multi-word phrases. An alias like `"learning"` for
`Reinforcement learning` would be harmful. `"reward learning"` would be fine.

### 2. OpenAlex and EuropePMC phrase filter (Stage A)
All phrases (primary name + all aliases) are OR-joined in a single
`title_and_abstract` search filter. No extra API calls per alias for these
sources — adding aliases here is essentially free.

### 3. Phrase gate (post-retrieval hard filter)
After retrieval, every candidate paper is checked: does the paper's title,
abstract, or TLDR contain at least one of the process's phrases as a
verbatim substring? Papers that match **none** are dropped entirely.
Historical landmark papers are exempt.

This is the most consequential use of aliases. If a major paper uses
"inhibitory control" throughout but never writes "response inhibition",
it is silently excluded from that process's candidate pool — permanently,
unless the alias is added. The phrase gate has no fallback.

### 4. Relevance scoring
Score = (number of phrase hits in title+abstract+TLDR) / (total phrases).
More aliases means more opportunities to score, but weak aliases dilute the
denominator. This effect is secondary compared to the phrase gate.

---

## What makes a good alias

### Include
- **Established synonyms actually used in peer-reviewed titles and abstracts.**
  The test is: would a search on PubMed or Google Scholar for this exact
  phrase, in quotes, return a substantial body of relevant literature?
- **Multi-word phrases.** They are specific enough to be meaningful for both
  S2 queries and phrase gating. Single words are almost always too broad.
- **Terms used interchangeably by a significant portion of the field.**
  Not just occasionally or in one lab's usage — broadly enough that papers
  using only the alias term would be missed without it.
- **Historical terms that dominated older literature** if the canonical name
  is a more recent coinage. Example: if a process was called X for decades
  before being renamed Y, papers from that era won't contain Y.

### Exclude
- **Terms that are related but not synonymous.** "Cognitive control" is not
  a synonym for "Response inhibition" — it's the parent category. Adding it
  as an alias would admit papers about any executive function.
- **Terms that refer to a subtype, not the whole construct.** "Stop-signal
  inhibition" is a subtype of response inhibition (tied to one paradigm),
  not a synonym for the construct.
- **Task or paradigm names.** The stop-signal task, the n-back, the Stroop
  — these belong in the task catalog, not as process aliases.
- **Abbreviations.** RL (reinforcement learning), WM (working memory),
  ToM (theory of mind) — too ambiguous as standalone strings, and the
  phrase gate does substring matching, so "WM" would match "FMRI" or
  "swim".
- **Neuroimaging or neural correlates.** "Prefrontal cortex activation" is
  not an alias for "executive function".
- **Terms that are the canonical name of another HED process.** See the
  category listing below — if a related term is already its own process
  entry, it must not be an alias for a neighboring process. This would make
  the phrase gate pass papers about the wrong process. E.g.,
  "interference control" has its own entry and must not appear as an alias
  for "response inhibition".
- **Lay or informal language.** "Willpower" is not an alias for
  "self-regulation" in the context of peer-reviewed literature search.
- **Single-word terms unless exceptionally specific.** Essentially never
  warranted.

### The scope test
Ask: "Is this term used to refer to the *same construct* as the canonical
name, or to a *related but distinct* construct?" Only synonyms pass.
When in doubt, omit — a missed alias hurts recall; a wrong alias introduces
noise that is harder to diagnose.

### Target quantity
0–3 aliases per process is the right range. Most well-named processes need
0–1. A few genuinely contested naming situations might warrant 2–3. Proposing
5+ for any single process should be a flag that the criteria are being applied
too loosely.

---

## Format in process_details.json

Aliases are stored as a list of dicts:

```json
"aliases": [
  {"name": "inhibitory control"},
  {"name": "response suppression", "note": "used especially in older motor control literature"}
]
```

The `note` field is optional. Use it when the alias is restricted to a
specific subfield, time period, or usage context that might help a future
reviewer understand why it was included.

---

## Current state — processes by category

160 of 172 processes currently have no aliases. The `--` marker below means
no alias; existing aliases are shown after `→`.

### associative_learning_and_reinforcement (13 processes, 12 no alias)
```
-- Associative learning
-- Extinction
-- Goal-directed behavior
-- Habit
   Instrumental conditioning  →  ['Operant conditioning']
-- Model-based learning
-- Model-free learning
-- Pavlovian conditioning
-- Policy learning
-- Reinforcement learning
-- Reversal learning
-- Reward prediction error
-- Value learning
```

### auditory_and_pre_attentive_deviance_processing (4 processes, 4 no alias)
```
-- Acoustic processing
-- Auditory perception
-- Auditory tone discrimination
-- Pitch perception
```

### awareness_agency_and_metacognition (13 processes, 13 no alias)
```
-- Attentional awareness
-- Body ownership
-- Feeling of knowing
-- Interoceptive awareness
-- Judgment of learning
-- Masking
-- Metacognitive control
-- Metacognitive monitoring
-- Mind wandering
-- Perceptual awareness
-- Self-monitoring
-- Self-referential processing
-- Sense of agency
```

### cognitive_flexibility_and_higher_order_executive_function (3 processes, 2 no alias)
```
-- Goal maintenance
   Set shifting  →  ['Cognitive flexibility']   ← NOTE: missing "task switching"
-- Strategy use
```

### emotion_perception_and_regulation (5 processes, 4 no alias)
```
-- Affective priming
-- Cognitive reappraisal
   Emotion recognition  →  ['Emotion perception']
-- Emotion regulation
-- Expressive suppression
```

### face_and_object_perception (12 processes, 10 no alias)
```
-- Biological motion perception
-- Depth perception
-- Face identity recognition
-- Face perception
   Gustatory perception  →  ['Gustation']
-- Motion perception
-- Olfactory perception
-- Pattern recognition
   Somatosensory perception  →  ['Somatosensation']
-- Visual form recognition
-- Visual object recognition
-- Visual perception
```

### implicit_and_statistical_learning (2 processes, 2 no alias)
```
-- Implicit memory
-- Procedural memory
```

### inhibitory_control_and_conflict_monitoring (9 processes, 9 no alias)
```
-- Conflict monitoring
-- Error correction
-- Error detection
-- Executive attention
-- Interference control
-- Proactive control
-- Reactive control
-- Response conflict
-- Response inhibition
```
**Note for this category:** These processes are closely related and their
boundaries matter a great deal. Be especially careful not to propose an alias
for one process that is the canonical name of a sibling process in this
category. E.g., "inhibitory control" could be an alias for Response inhibition,
but "interference control" cannot — it is its own entry.

### language_comprehension_and_production (16 processes, 15 no alias)
```
-- Discourse processing
-- Language comprehension
-- Language production
-- Lexical access
-- Naming
-- Phonological awareness
-- Phonological encoding
-- Reading
-- Semantic knowledge
-- Semantic processing
-- Sentence comprehension
-- Speech perception
-- Speech production
-- Syntactic parsing
-- Verbal fluency
   Word recognition  →  ['Visual word recognition']
```

### long_term_memory (21 processes, 21 no alias)
```
-- Autobiographical memory
-- Consolidation
-- Declarative memory
-- Directed forgetting
-- Encoding
-- Episodic memory
-- Familiarity
-- Forgetting
-- Pattern completion
-- Pattern separation
-- Proactive interference
-- Prospective memory
-- Recall
-- Recognition
-- Recollection
-- Reconsolidation
-- Retrieval
-- Retroactive interference
-- Semantic memory
-- Source memory
-- Verbal memory
```
**Note for this category:** Many of these are generic single words (Encoding,
Recall, Retrieval, Recognition, Forgetting). Single-word canonical names do
not need single-word aliases — the phrase gate is already loose for these.
Only add an alias if there is a well-established multi-word synonym (e.g.,
"source monitoring" for Source memory; "temporal context memory" would be too
narrow). Aliases that are subsets (e.g., "free recall" as alias for Recall)
should be avoided unless the subset term is so dominant that the general term
is rarely used.

### motor_preparation_timing_and_execution (16 processes, 16 no alias)
```
-- Action initiation
-- Antisaccade
-- Fine motor control
-- Grasping
-- Motor memory
-- Motor planning
-- Motor preparation
-- Motor sequence learning
-- Motor timing
-- Proprioception
-- Reaching
-- Response execution
-- Response selection
-- Saccade
-- Visuomotor adaptation
-- Vocal-motor control
```

### perceptual_decision_making_evidence_accumulation (1 process, 1 no alias)
```
-- Perceptual decision making
```

### reasoning_and_problem_solving (11 processes, 10 no alias)
```
-- Analogical reasoning
-- Categorization
-- Causal reasoning
   Deductive reasoning  →  ['Logical reasoning']
-- Hypothesis testing
-- Inductive reasoning
-- Insight
-- Mathematical reasoning
-- Means-ends analysis
-- Planning
-- Subgoaling
```

### reward_anticipation_and_motivation (6 processes, 6 no alias)
```
-- Approach motivation
-- Avoidance motivation
-- Effort allocation
-- Incentive salience
-- Reward anticipation
-- Reward consumption
```

### selective_and_sustained_attention (11 processes, 10 no alias)
```
-- Alerting
-- Attention shifting
-- Attentional capture
-- Divided attention
-- Feature-based attention
-- Object-based attention
-- Orienting
-- Selective attention
-- Spatial attention
   Sustained attention  →  ['Vigilance']
-- Temporal attention
```

### short_term_and_working_memory (9 processes, 7 no alias)
```
   Active maintenance  →  ['Maintenance']
-- Chunking
-- Manipulation
-- Rehearsal
-- Spatial working memory
-- Verbal working memory
-- Visual working memory
-- Working memory
   Working memory updating  →  ['Updating', 'Updating (WM)']
```

### social_cognition_and_strategic_social_choice (11 processes, 10 no alias)
```
-- Competition
-- Cooperation
-- Imitation
-- In-group/out-group processing
-- Joint attention
   Perspective taking  →  ['Mentalizing', 'Theory of mind']
-- Reciprocity
-- Self-other distinction
-- Social decision making
-- Social perception
-- Stereotyping
```

### spatial_cognition_and_navigation (2 processes, 2 no alias)
```
-- Mental rotation
-- Spatial memory
```

### value_based_decision_making_under_risk_and_uncertainty (7 processes, 6 no alias)
```
-- Choice commitment
-- Delay discounting
-- Intertemporal choice
-- Probability judgment
   Risk processing  →  ['Risky decision making']
-- Valuation
-- Value-based decision making
```

---

## Suggested working method

Work through one category at a time. For each category, consider all the
processes together — this is important because sibling processes share
conceptual space and aliases for one must not overlap with canonical names
of others in the same category.

For each process, produce one of:
- **No aliases proposed** — the canonical name is the dominant term in the
  literature and no important synonyms are being missed. This is the right
  answer for many processes.
- **One or more alias proposals**, each with:
  - The proposed alias string
  - A one-sentence justification explaining why papers using this term
    would not otherwise be retrieved (or would be dropped by the phrase gate)
  - An optional note if the alias is subfield-specific

Flag any case where you are uncertain — the human reviewer needs to know
where your confidence is lower.

## Output format requested

Produce output category by category in this format:

```
### category_name

**ProcessName**
definition: <one-sentence definition of the construct>
- alias: "proposed alias string"
  reason: why this is needed
  note: (optional subfield qualifier)

**ProcessName2**
definition: <one-sentence definition of the construct>
- no aliases proposed
  reason: canonical name dominates the literature
```

Then at the end, flag any cases where you noticed a potential problem with
an *existing* alias (e.g., the existing alias for Set shifting appears to be
missing "task switching" as a third alias).

---

## What not to do

- Do not propose aliases just to have something to show. "No aliases" is
  often the correct answer.
- Do not propose aliases that are the canonical name of another process in
  the same category.
- Do not propose single-word aliases.
- Do not propose task names.
- Do not add speculative or subfield-specific jargon that only a narrow
  community uses.
- Do not produce a list so long it becomes impractical to review. The total
  number of proposed aliases across all 172 processes should probably be
  under 150.
