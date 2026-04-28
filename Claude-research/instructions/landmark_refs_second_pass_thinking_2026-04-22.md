# Second-pass landmark review — thinking summary

**Date:** 2026-04-22
**Context:** Companion to `landmark_refs_first_review_gemini-manual.md`
(user's manual pass with Gemini assistance) and the updated
`landmark_refs_proposed_2026-04-22.md` (now contains §9 with the review
log). This note explains the accept/modify/reject calls.

## Overall read on the Gemini pass

Good catch rate on the obvious upgrades. All five of the "swap this [M]
or [L] entry for something stronger" proposals were ones I had either
flagged myself in §6 or would have flagged on a second read:

- Biederman 1987 for pattern_recognition (I had T&G 1980 which was
  double-booked with visual_search — embarrassing).
- Pashler 1994 for response_selection (I had Welford as a placeholder
  and said so in §6).
- Gross 2002 for expressive_suppression (I had Gross 1998 and flagged
  the duplicate in §6).
- Miyake 2000 for working_memory_updating (explicitly named in my §6).
- Johnson & Raye 1981 for source_memory (explicitly named in my §6).
- Ekman 1992 for facial_emotion_recognition (I flagged the Ekman 1971
  duplicate in §6).

These were all straightforward accepts. Six upgrades in one pass —
worth doing manual reviews.

## Where I diverged

Three proposals I didn't accept as-stated, and one I accepted but with
a different citation. These are the interesting cases.

### hed_visual_perception: Hubel & Wiesel 1962 > Livingstone & Hubel 1988

Both are real, both are *Science* / *J Physiol* flagship journal papers,
both are Hubel. The 1988 paper is a beautiful integrative piece on
parallel visual pathways (magno/parvo). The 1962 paper is the origin
paper for receptive fields and columnar organization in V1.

Why 1962 over 1988: the HED catalog's own `fundamental_references` entry
for `hed_visual_perception` cites Hubel & Wiesel 1962. If the HED team's
own curation went with 1962, landmarks shouldn't silently override that
without strong reason. 1988 is narrower than the process definition
("Perception of visual information; includes form, motion, depth, color,
and spatial layout") — 1962 covers the general machinery of cortical
visual processing that subsequent parallel-pathway work built on.

This is a judgment call; if the user prefers 1988 I'll swap. But 1962
is the stronger default.

### hed_acoustic_processing: Fletcher 1940 > Tanner & Swets 1954

This one was an error on Gemini's part that I almost missed. The
proposal was:

> Tanner & Swets (1954) "A decision-making theory of **visual**
> detection" *Psychol Rev* 61:401–409 — for hed_acoustic_processing

The paper is real; the problem is its title. Tanner & Swets 1954 is
foundational for Signal Detection Theory, and the authors were part of
the Michigan auditory lab, but the 1954 paper's examples are *visual*
detection. Using a paper titled "...visual detection" as the landmark
for "acoustic processing" would look sloppy to anyone who opened the
PDF.

What should go there: Fletcher 1940 *Rev Mod Phys* "Auditory patterns"
is a flagship-journal psychoacoustics paper (introduced the critical-
band concept) and — here's the tell — is the citation HED itself uses
as the `fundamental_references` entry for this process. That's a
strong signal that the HED team already considered and converged on
this choice.

Lesson for subsequent AI review passes: when the tool proposes a paper
whose *title* doesn't match the process it's being assigned to, that's
a red flag to re-examine the proposal even if the paper is individually
strong.

### hed_motor_control: does not exist in the catalog

Gemini proposed Fitts 1954 for a new entry called `hed_motor_control`.
Fitts 1954 is excellent, but `hed_motor_control` is not in the HED
process list. The motor processes are motor_memory, motor_planning,
motor_preparation, motor_sequence_learning, motor_timing. There's no
umbrella "motor_control" id to attach Fitts to.

I caught this by grepping process_details.json. If the user wants Fitts
represented, the natural attachment is `hed_motor_planning` or
`hed_motor_preparation`. I flagged this explicitly in §9.4 so they can
decide.

Lesson: always verify a proposed id against the source-of-truth file.
LLMs confidently hallucinate id names that sound plausible for a
catalog they've inferred from context.

### hed_self_monitoring: construct-mismatch

Gemini proposed Snyder 1974 *J Pers Soc Psychol* "Self-monitoring of
expressive behavior." Snyder's self-monitoring is a social/personality
trait — the degree to which people monitor and adjust their expressive
behavior based on social cues. Think of extroverts who adapt their
self-presentation in different contexts.

HED's `hed_self_monitoring` definition is:
> "Ongoing evaluation of one's own performance against task goals and
> expected outcomes."

That's *performance monitoring*. Different construct entirely. Snyder's
construct belongs in a social-cognition or personality framework, not
in HED's cognitive-process taxonomy.

The right paper for HED's construct is something like:
- Ridderinkhof, Ullsperger, Crone & Nieuwenhuis (2004) *Science*
  306:443–447 — the performance-monitoring review.
- Or a Nelson-style metamemory paper (excluded as book chapters).
- Or leave blank and let `hed_metacognitive_monitoring` (Fleming & Lau
  2014) and `hed_error_detection` (Gehring 1993) cover it implicitly.

I left this blank and raised it as §10 Q6 for the user to resolve.

Lesson: when a proposed landmark paper and the process definition use
the same word but the word has a different technical meaning in two
subfields, the AI is at risk of false-friend substitution. The mitigation
is to quote the process definition back and check that the paper's
construct matches.

### hed_associative_learning: subtle duplicate

Gemini proposed swapping Rescorla (1988) *Annu Rev Neurosci* →
Rescorla (1988) *Am Psychol*. Both are real. The problem is the
*Am Psychol* paper is already the landmark for
**hed_pavlovian_conditioning** in my draft. Swapping would collapse two
distinct landmark entries into one citation, losing the intentional
distinction between:

- hed_associative_learning → Rescorla 1988 ARN (behavioral/integrative)
- hed_pavlovian_conditioning → Rescorla 1988 AmPsych (theoretical frame)

The two papers complement each other. Keeping them distinct is
deliberate. Rejected the swap.

Lesson: when a second pass proposes a "better" citation, check that the
new citation isn't already in use for a related entry.

## What this tells us about the review workflow

The user's workflow — draft with one model, review with another, apply
deltas — caught six real issues I missed in the initial pass. At the
same time, three of the ten Gemini proposals were wrong in specific,
hard-to-spot ways: wrong construct (self_monitoring), nonexistent id
(motor_control), cross-process duplicate (associative_learning), and
title mismatch (acoustic_processing). That's a 60/40 signal-to-noise
ratio on the review, which is good but not something to rubber-stamp.

Concretely: when applying an AI-assisted review to a curation task:

1. Grep the source-of-truth file to verify every id mentioned actually
   exists.
2. Check that the proposed paper's *title* is consistent with the
   process construct (the Tanner & Swets case).
3. Check that the proposed paper isn't already assigned to an adjacent
   process (the Rescorla case).
4. Compare the paper's construct to the HED definition (the Snyder
   case), not just the process name.

I applied all four checks by hand during the incorporation. For future
passes it would be easy to script (1) and (3) as a sanity check.

## State of the landmark list after this pass

Six upgrades, three new fills, one reject (self_monitoring flagged for
user decision), one rejected-as-duplicate, one rejected-as-phantom-id.

Still to do:

- User decision on §7 Qs 1–5 (original) and §10 Q6 (new: self_monitoring).
- After sign-off: batch CrossRef DOI lookup, serialize to
  `outputs/literature_search/landmark_refs.json`, mark §12 item #2
  resolved in the main plan.
- Then draft Phase 2 instructions for Sonnet.
