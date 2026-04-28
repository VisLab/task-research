# Task Selection and Variation Criteria

**Date:** 2026-04-18 (updated)  
**Purpose:** Reference document specifying how the 103-task HED catalog was scoped, how tasks were selected, and the rules for classifying variations vs. aliases vs. non-variations.

---

## 1. Task Selection Criteria

### What counts as a task in this catalog?

A **task** is a structured experimental paradigm that:

1. **Produces event-based data.** The paradigm generates a sequence of discrete, time-stamped events (stimulus presentations, participant responses, feedback) that can be annotated with HED tags.

2. **Has a specific, reproducible procedure.** A researcher reading the task description could implement it. Generic categories like "memory task" or "attention task" are not tasks — they are domains.

3. **Is widely used in cognitive/behavioral neuroscience.** The paradigm appears across multiple labs, has a recognized name, and is cited in the literature as a standard method.

4. **Engages identifiable cognitive processes.** The task is designed to isolate or measure specific cognitive, perceptual, motor, or affective processes.

### What is excluded?

- **Self-report instruments**: Personality inventories, mood questionnaires, symptom checklists (e.g., BDI, STAI). These do not produce event-structured data.
- **Clinical screening tools**: Instruments designed for diagnostic classification rather than experimental measurement (e.g., MMSE as a screening tool, though components like digit span are included as standalone tasks).
- **Broad task categories**: "Working memory task" as a generic label. The catalog includes specific instantiations (N-Back, Operation Span, Change Detection, etc.).
- **One-off experimental designs**: Paradigms used in a single study without broader adoption.
- **Neurological examinations**: Reflex testing, cranial nerve exams, etc.

### The 103-task scope

The catalog targets approximately 100 canonical tasks spanning the major domains of cognitive and behavioral neuroscience: attention, memory, executive function, language, perception, motor control, emotion, social cognition, decision-making, and learning. The number 103 is not a hard constraint — it reflects the current state of consolidation from the Cognitive Atlas plus gap-filling. Tasks may be added or removed as the catalog matures.

---

## 2. Naming Conventions

Each task has a **canonical_name** (the standard reference name) and zero or more **aliases** (alternative names used in the literature).

### Canonical name rules

- Use the most widely recognized name in the literature
- Include "Task" as a suffix (e.g., "Stroop Color-Word Task", not just "Stroop")
- For named paradigms, the standard abbreviation goes in the `aliases` array, not in the canonical name (e.g., canonical name "Cambridge Face Memory Task", alias "CFMT")
- Prefer the specific paradigm name over the generic process name when both exist (e.g., "Eriksen Flanker Task" not "Response Conflict Task")

### Alias rules

An **alias** is an alternative name for the same task. Aliases are:

- Abbreviations (e.g., "AGL" for Artificial Grammar Learning Task)
- Eponymous names (e.g., "Galton-Crovitz Task" for the cue-word variant of Autobiographical Memory Task)
- Common shortened forms (e.g., "Antisaccade" for Anti-Saccade Task)
- Instrument-specific names (e.g., "IAPS Viewing" for Affective Picture Viewing Task)

Aliases are **not** variations. An alias refers to the same procedure with a different name. A variation refers to a different procedure under the same task umbrella.

### Identifier formats

Every term in the catalog is typed by its identifier prefix, so any ID encountered anywhere in the documents is unambiguously classifiable:

- **Task IDs** have the form `hedtsk_<slug>` (e.g., `hedtsk_eriksen_flanker`, `hedtsk_change_detection`, `hedtsk_balloon_analog_risk`). The slug is mechanically derived from the `canonical_name` by stripping the trailing word "Task" or "Test", lowercasing, removing apostrophes, replacing `/`, `-`, and spaces with `_`, collapsing runs of `_`, and prepending `hedtsk_`. It is therefore a stable, deterministic identifier once the canonical name is fixed. The `hedtsk_` prefix is mandatory.
- **Process IDs** have the form `hed_<slug>` (e.g., `hed_response_inhibition`, `hed_visual_working_memory`). The `hed_` prefix is mandatory. The `hed_` prefix is this catalog's working prefix and is not a claim about HED-schema membership (see `.status_2/criteria_review_2026-04-17.md` §2.5).
- **Canonical names** for tasks always end in the word `Task` or `Test`. `Task` is the default. The canonical name contains no parenthetical abbreviations and no spaced slashes — abbreviations and alternative names go in `aliases`. Examples: "Balloon Analog Risk Task" with alias "BART"; "False Belief Task" with alias "Theory of Mind Task".
- **Process names** are sentence case (first word capitalized, remainder lowercase except proper nouns).

A reader who sees `hedtsk_balloon_analog_risk` knows it is a task; `hed_response_inhibition` is a process; `BART` is a human-readable abbreviation not an ID. Any cross-reference between the two axes (task-to-process, or process-to-task) must preserve these prefixes verbatim.

---

## 3. The Inclusion Test

Each task has a three-part **inclusion_test** that defines the boundary of the task:

### Structure

```json
{
  "procedure": "What the participant does — the observable sequence of events",
  "manipulation": "What the experimenter varies — the independent variables",
  "measurement": "What is recorded — the dependent variables and signals"
}
```

### How to use the inclusion test

A specific experiment is an instance of a given task if and only if:

1. Its procedure matches the **procedure** field (the participant performs the described sequence of actions)
2. It manipulates at least one variable from the **manipulation** field
3. It records at least one measure from the **measurement** field

The procedure field is the most important. Two experiments with different manipulations or measurements but the same procedure are instances of the same task. Two experiments with different procedures are different tasks, even if they target the same cognitive construct.

---

## 4. Variation Criteria

### What is a variation?

A **variation** is a named version of a task that changes **what the participant experiences or does** such that the event structure in the recorded data would differ. The key test:

> If you compared the event logs from the standard version and the variation, would there be structural differences in the types of events, their temporal organization, or the participant's required responses?

### Examples of genuine variations

- **Different response modalities**: Verbal naming vs. button press (Picture Naming Task)
- **Different stimulus configurations**: Simultaneous masking vs. forward masking vs. backward masking (Auditory Masking Task)
- **Different cognitive demands**: 1-choice vs. 2-choice vs. go/no-go versions of the same paradigm
- **Different task structures**: Blocked vs. interleaved conditions when this changes what the participant must track (e.g., interleaved pro/anti-saccade trials require task-set switching)
- **Additional participant actions**: Production version of AGL (participant generates strings, not just judges them)
- **Different stimulus-response mappings**: Prosaccade vs. antisaccade (same cue, opposite required response)
- **Named sub-paradigms**: Sally-Anne, Smarties Task, Animated Triangles as distinct False Belief implementations

### What is NOT a variation? (12 active DROP categories + 1 retired)

The following do **not** count as task variations because they do not change what the participant experiences or does (EMOT was retired 2026-04-17; see §5.1):

| Code | Category | Description | Examples |
|------|----------|-------------|----------|
| **MEAS** | Measurement modality | Adding or changing recording equipment | "with fMRI," "with EEG," "with eye-tracking," "with SCR/startle probe," "with MEG," "with TMS recording" |
| **ANAL** | Analysis method | Post-hoc data analysis technique | Computational modeling, DDM, ROC analysis, Gratton effect analysis, process dissociation, clustering analysis, strategy analysis, locus-of-slack logic, reverse correlation |
| **DESG** | Design/parameter choice | Experimenter decisions about trial structure | Blocked vs. event-related design, varying ISI/SOA (as generic sweep), parametric difficulty, variable set size (as parameter sweep), speed-accuracy tradeoff instructions |
| **STIM** | Stimulus substitution | Swapping one stimulus set for an equivalent one | IAPS→OASIS/NAPS, race-specific face sets with identical procedures, alternative word lists, translated stimuli |
| **POPL** | Population/clinical use | Testing a different population | "in amnesia," "for children" (unless procedure changes), "clinical screening," "developmental version," "in schizophrenia," cross-cultural comparison |
| **IDIF** | Individual differences | Using a task as a correlational measure | "as individual differences measure," correlational studies |
| **TRAN** | Training/intervention | Using repeated task exposure as an intervention | Bias modification training, working memory training, practice/training interventions, memory specificity training |
| **PHAR** | Pharmacological challenge | Administering drugs during the task | "under pharmacological challenge," medication on/off designs |
| **SCOR** | Scoring method | How performance is quantified | Partial-credit scoring, B-minus-A derived scores, B/A ratio, trial-level bias scores |
| **ALIA** | Alias/redundant | Restates the canonical task or duplicates another variation | "Standard X" that merely restates the canonical definition, near-duplicate entries from dual-source generation |
| **MOTI** | Motivation/reward add-on | Adding incentives without changing task structure | "Rewarded X," reward modulation, mood induction before task |
| **DUAL** | Dual-task add-on | Adding a concurrent secondary task | Articulatory suppression, working memory load, concurrent secondary task (unless it creates a recognized named paradigm) |
| **EMOT** | Emotional stimulus swap — **RETIRED 2026-04-17** | ~~Replacing neutral stimuli with emotional ones~~ | This category was retired by user decision on 2026-04-17. All attested Emotional-X paradigms are now kept as variations under their parent tasks. No emotional variations are dropped on EMOT grounds. See §5.1 for the resolution. |

### Applying the criteria consistently

The DROP categories are applied uniformly across all 103 tasks. If "with fMRI" is dropped for one task, it must be dropped for all tasks. If "in children" is dropped when only stimuli change for age-appropriateness, it must be dropped everywhere that applies.

The one exception is when a modification creates a **recognized named paradigm** with its own literature. For example, the Emotional Stroop Task is kept as a separate top-level task entry because it has a distinct, established identity in the literature. Note that the EMOT category was retired entirely on 2026-04-17 (see §5.1) — all attested Emotional-X paradigms are now kept as variations, whether or not they have independent literatures.

---

## 5. Borderline Cases and Policy Questions

These areas required explicit policy decisions. §5.1 was resolved on 2026-04-17; the remaining five are open. The variation audit (`.status_2/variation_audit.md`, applied 2026-04-18) applied the default rules listed below:

### 5.1 Emotional variants — RESOLVED 2026-04-17

**Decision:** The EMOT DROP category was retired on 2026-04-17. All attested Emotional-X paradigms are kept as variations under their parent tasks. No emotional variations are promoted to top-level tasks (decided 2026-04-18).

**What this means in practice:** The following emotional variations are kept as variations (not top-level tasks): Emotional Anti-Saccade, ANT with Emotional Stimuli, CPT with Emotional Distractors, Emotional Directed Forgetting, Emotional Flanker, Emotional Navon, Emotional Oddball, Emotional Simon Task, Emotional Go/No-Go, Emotional N-Back, Emotional TNT, Emotion-Induced Blindness, Emotional Attentional Blink. The Emotional Stroop Task, Emotion Regulation Task, and Facial Emotion Recognition Task remain top-level tasks (they were always independent entries, not promoted from variations).

**Rationale:** Emotional content does change what the participant experiences, and these are attested paradigms in the literature. Keeping them as variations rather than promoting them avoids proliferating task entries for every stimulus-domain cross.

### 5.2 Proportion-congruent manipulations

**Current rule:** KEPT for Flanker, Stroop, and Simon tasks because proportion-congruent manipulations change the cognitive control context substantially (participants adjust their strategies based on conflict frequency).

**Open question:** Could be argued as a design choice (DESG) since it's an experimenter-controlled parameter.

### 5.3 Child/developmental versions

**Current rule:** KEPT when the procedure is genuinely simplified or uses different stimuli that change the task. DROPPED when only stimuli are swapped for age-appropriateness without changing the procedure.

**Currently kept child/developmental variations (5):** Child ANT (fish stimuli, simplified flanker), Developmental / Child IAT (picture-based categories), Iowa Gambling Task Child Versions (simplified decks), RMET Child Version (reduced item set, simplified vocabulary), Child-Adapted SART (modified timing and stimuli).

**Open question:** Should there be a uniform rule for all child versions?

### 5.4 Dual-task add-ons — RESOLVED 2026-04-18

**Rule:** Uniformly DROPPED. Adding a concurrent secondary task (working memory load, articulatory suppression, etc.) is a design choice (DUAL), not a task variation, regardless of how widely used the combination is. No exceptions for "well-established" dual-task pairings — popularity does not change the structural argument.

**Applied:** All DUAL-coded entries were removed in the original audit. The one borderline survivor from that pass — Concurrent Cognitive Load (Affective Picture Viewing Task) — was dropped 2026-04-18 for consistency.

### 5.5 Confidence ratings / subjective reports — RESOLVED 2026-04-18

**Rule:** Adding a confidence rating or subjective report to an otherwise unchanged task is a measurement add-on (MEAS), not a variation. The fact that it adds a participant response to the event stream is not sufficient — by that logic any bolted-on scale would create a variation. Confidence-rating add-ons are uniformly DROPPED.

**Exception:** A confidence-related variation is kept only when the confidence judgment defines a recognized named paradigm whose construct of interest *is* the metacognitive correspondence, not the base task's performance. The sole current example is the Confidence-Accuracy Paradigm (Heartbeat Detection Task), where Garfinkel et al. (2015) defined a three-dimensional model of interoception in which confidence-accuracy correspondence is one of the core measured dimensions.

**Dropped in the original audit (6):** AGL with Confidence Ratings, ROC Analysis (Old/New Recognition), Confidence Judgment Version (Random Dot Kinematogram), ROC Analysis (Remember/Know), Backward Masking with Confidence Ratings (Visual Masking), Source Confidence Ratings (Source Memory). **Dropped 2026-04-18 (2):** Confidence-Rated Recognition (Old/New Recognition), Remember/Know with Confidence Ratings (Remember/Know). These two had initially survived the audit but were dropped for consistency — adding a graded scale to old/new or R/K judgments is the same kind of add-on as the six already dropped.

### 5.6 Computerized vs. manual versions — RESOLVED 2026-04-18

**Rule (refined 2026-04-18):** A computerized version is a genuine variation only if it changes the sensory modality or motor activity the participant uses. Manipulating physical objects vs. clicking on a screen qualifies. Handwriting vs. key-pressing qualifies. Stylus-on-tablet vs. pencil-on-paper does not (same motor modality). Automated scoring or administration software alone is never a variation (that is MEAS or DESG).

**Kept computerized/digital variations (6):** Computerized (eCorsi) — physical block tapping → screen tapping changes spatial/motor demands; Computerized DSST/SDMT — handwriting → button pressing is a different fine motor skill; Computerized Mirror Tracing — loss of haptic edge feedback from physical template; Computerized Adaptive Version (Raven's) — adaptive algorithm changes which items are presented, a procedural change beyond interface; Computerized vs. Physical Versions (Tower of London) — grasping/placing 3D beads → drag-and-drop; PD against Computer Opponents (Prisoner's Dilemma) — not an interface change but a structural one: deterministic program opponent vs. human.

**Dropped 2026-04-18 (4):** Computerized RAVLT (digital administration with automatic scoring — MEAS/DESG), Digital TMT/dTMT (stylus on tablet vs. pencil on paper — same motor modality; kinematic recording is MEAS), Computerized UFOV (UFOV is inherently screen-based; this is commercial software with automated staircase — DESG), Computerized WCST/WCST-CV (digital version with automated scoring — DESG).