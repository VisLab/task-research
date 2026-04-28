# Phase 2 instructions — thinking summary

**Date:** 2026-04-22
**Companion to:** `.status/task_literature_search_phase2_instructions.md`
**Context:** Phase 1 is complete and validated
(`.status/session_2026-04-21_literature_search_phase1.md`); the
landmark list is finalized (`.status/landmark_refs_2026-04-22.md`);
user asked for the clean MD plus a draft of Phase 2 instructions.

This note explains the design choices inside the instructions doc —
the ones that are easy to miss in the mechanical rule text.

## 1. What Phase 2 is for (and isn't)

Phase 2 is a triage of existing references, not an enrichment pass and
not a search pass. The parent plan §8 Phase 2 is clear on this: the
deliverable is a human-review Markdown, and nothing in the workspace
JSON changes until the user signs off. I kept that framing literally
— the script's success criterion #6 is `git diff` empty for
`process_details.json` and `task_details.json`.

The reason matters. Every prior pass that mutated these JSON files
left us with a reference set the user doesn't fully trust (see plan
§1 — the list "is not acceptable for our quality bar"). Phase 2 earns
trust by being read-only with a human gate. If we collapse the
mutation into Phase 2 to save a session, we lose the gate. The
explicit read-only discipline is the feature.

## 2. Why sub-phase 2.1 (landmark DOI resolution) is in Phase 2 and not Phase 1

This was the biggest structural decision. I considered three options:

- **(a)** Put DOI resolution inside Phase 1 — "Phase 1b" style — since
  the landmarks list is finalized.
- **(b)** Leave it to Phase 3 as part of the search infrastructure.
- **(c)** Put it at the top of Phase 2 (the choice I made).

(a) is tempting because it mentally groups all "infrastructure
plumbing" in one place. It fails because Phase 1 is already signed
off and executed — re-opening it to add a new script risks regressions
in the identity primitives and test file. Surgical scope preservation
matters more than grouping aesthetics.

(b) fails the other way: Phase 3 needs the JSON to run at all (the
systematic search uses landmarks as seed DOIs to measure co-citation
around). If Phase 2 triage doesn't produce the JSON, Phase 3 has an
extra bootstrap step.

(c) is right: Phase 2 is the first consumer of the landmark JSON, and
the resolution script is small (~120 lines) and shares exactly the
clients Phase 1 built. Putting it at the top of Phase 2 keeps the
read-only discipline of §1 above — the resolver doesn't touch
`process_details.json` — while giving the main triage a machine-
readable input.

## 3. Why rule order matters, and how I chose it

The triage rules in sub-phase 2.3 are ordered first-match-wins, not
evaluated as a scoring function. This is a deliberate choice against
the parent plan §6 composite-score mechanism. §6 applies to **Phase 3
ranking** of candidate papers from search results; it does **not**
apply to Phase 2 triage of existing references. Conflating the two is
the mistake I want to prevent.

The ordering:

1. Landmark override first — nothing should ever drop a landmark
   paper. The rule earns its position by being non-negotiable.
2. Test manual drop second — these never become landmarks, are cheap
   to detect via regex, and shouldn't be gated behind venue checks.
3. Pre-1960 non-landmark drop third — an escape hatch for the landmark
   rule. Anything from the 1920s-1950s either has landmark status
   (Stroop 1935, Rescorla-Wagner equivalents, Pavlov 1927 if the
   user wanted it kept — he didn't) or is chaff that Phase 3 would
   find modern replacements for. This was tempting to soften to
   REVIEW, but the catalog has a real pathology of citing pre-1960
   textbooks as "fundamental references" when the field actually
   relies on a 1980s-1990s integrative paper instead. DROP here forces
   Phase 3 to propose a modern replacement.
4. Technical report → REVIEW. Can't check citation counts in Phase 2
   (that's a Phase 3 concern), so conservative: user reviews rather
   than we silently drop.
5. Flagship/mainstream venue KEEP. This is the cheapest strong signal.
6. Tier A/B publisher KEEP — the DOI-prefix check is a narrower signal
   than the venue allowlist and catches flagship publishers whose
   venues we haven't yet added to the allowlist.
7. Book chapter non-landmark → REVIEW, not DROP. This was the most
   subtle call. The hard rule from the landmark MD is "no book
   chapters." But many processes have legitimate
   foundational-in-the-sense-of-historical book chapter citations
   (Atkinson & Shiffrin 1968; Baddeley & Hitch 1974 pre-1992; Tulving
   1972). For Phase 2 we REVIEW these so the user decides whether the
   modern journal equivalent is already present or needs to be added
   by Phase 3. We don't unilaterally drop a reference that a catalog
   maintainer may have chosen deliberately.
8. Unknown venue / unresolved → REVIEW.
9. Default → REVIEW.

The asymmetry is intentional: the only rules that DROP are (b) and
(c). Everything uncertain becomes REVIEW. A false drop costs the user
a reference they wanted to keep; a false review costs them 30 seconds
of ticking a KEEP box. The cost asymmetry is large.

## 4. Why pub_id is the right primary key for matching landmarks to existing refs

The naïve match is "compare DOIs." It fails: many existing references
have `doi: null` (pre-DOI papers, unresolved by the earlier citation
enrichment). The landmark list has DOIs only after sub-phase 2.1
resolves them — and some landmarks will come back with
`resolution_status: "not_found"`.

pub_id is the right key because it is content-derived (first-author
family + year + canonicalized title) and does not depend on DOI
availability. A landmark that has `doi: null` in `landmark_refs.json`
can still match an existing reference that also has `doi: null`, as
long as both share first author, year, and near-identical title. This
is the DOI-discovered-later invariant from plan §11.7, validated
already in Phase 1.

The edge case I want Sonnet to handle carefully: existing references
with garbage `authors` fields. I documented this in the Questions to
Raise section — mint pub_id with `"Unknown"` family, flag in the
session report, and do not silently drop. "Mint and flag" preserves
data; "skip" loses it.

## 5. Why triage_rules.py is a separate module, not inline

I've seen this go wrong before in the catalog work. When venue lists
and classifier logic are inlined into the main script, the only way to
review the rule set is to read the whole script — and the user ends up
re-deriving what's in the list from the diff rather than being able to
look at one file that is "just the rules."

Splitting `triage_rules.py` out means:

- The rule set is reviewable as data.
- When sub-phase 2.2 prints the "unknown venues" table, the user's
  edit lands in one file, not scattered across classification logic.
- Sub-phase 2.2's 30-minute hand-review of venue aliases is a
  first-class step with a first-class output.

The 30-minute hand-review is the most important investment in the
triage. Classification lives and dies on whether the venue allowlist
matches the actual venue strings in the JSON. If "J Exp Psychol Gen"
is not aliased to the same flagship tier as "Journal of Experimental
Psychology: General", every JEP:Gen reference becomes REVIEW and the
review file balloons.

## 6. Why the review file has four sections (not three)

Plan §8 Phase 2 says "three tables" — keep, drop, review. I added a
fourth: the landmark gap report (sub-phase 2.5). Reason: the user's
primary concern with the current reference set is under-coverage of
canonical papers (plan §1). Surfacing landmark papers that are
**missing** from the existing data — not just triaging what is there
— lets Phase 3 seed the systematic search with the high-value targets
first.

This is free work in Phase 2 because the pub_id set is already
computed for the main triage. We just invert the lookup: for each
landmark pub_id, ask "does it appear in any reference's computed
pub_id?" The expected gap count (30-60) is where Phase 3's coverage
work gets concrete.

## 7. The virtiofs rule and the _inputs/ pattern

The stale-snapshot issue has bitten every session that tried to run
Python scripts against mounted JSON via `bash`. The instructions
encode the fix: the triage script accepts the JSON path as an
argument, and Sonnet is expected to Read → Write the JSON into
`outputs/literature_search/_inputs/` before running the script from
bash. The `_inputs/` copy is transient per-session.

This adds a few minutes to the Sonnet session but prevents the
"JSON parse error at byte N, looks like null bytes" class of failure
that has cost multiple hours in prior sessions. The sharpest phrasing
is: "the bash sandbox cannot be trusted to read workspace JSON; always
round-trip via the file tools first."

## 8. What I considered and rejected

**Making Phase 2 apply the drops.** Rejected per §1. The human-review
gate is the feature.

**Running CrossRef lookups on every reference to backfill missing
DOIs during triage.** Rejected because (a) it would 10× the runtime of
Phase 2 with ~1,150 lookups for a subset of value, (b) the DOI is not
a triage signal for most decisions (venue_type and venue name are), and
(c) the enrichment is a Phase 3 concern — Phase 3 is going to be
calling OpenAlex on every reference anyway as part of the search.

**Collapsing `landmark_refs.json` production into `landmark_refs.md`
by making Sonnet hand-format JSON.** Rejected — every hand-formatted
JSON file in this project has had schema drift, and the CrossRef
verification step is valuable (it catches cases where the MD's
citation string disagrees with CrossRef's author list, which has
happened before). The resolver script earns its 120 lines.

**Adding Tier C (= "low") drop rules based on DOI prefix.** Rejected
because Tier C is defined as "not on the allowlist" (plan §5.1), i.e.
a `None` return from `publisher_tier_from_doi`. The rule chain already
routes those to the venue classifier and then to REVIEW — no separate
Tier C drop rule is needed. Adding one would double-count.

**Using the full composite score from plan §6 as the triage signal.**
Rejected as explained in §3 above. §6 is for Phase 3 candidate
ranking, not Phase 2 existing-reference triage.

## 9. Open questions I am deferring to the user or to Sonnet

These are the instructions doc's "Questions to raise" section. Listed
here too because they represent real uncertainty, not just
boilerplate:

- What if the venue allowlist bootstrapping finds more than ~15 unknown
  venues? Either my mental model of the catalog is wrong or the data is
  messier than expected. Sonnet should stop at ~15 unknowns and ask
  before proceeding.
- What if `resolve_landmarks.py` ambiguity rate is over 10%? The
  CrossRef query tuning is wrong. Fixable by narrower title-term
  filtering or adding Europe PMC as a cross-check for older papers.
- What if the pub_id minting finds identity collisions — two different
  references in different processes with the same pub_id? This is
  possible for deliberately-shared references (e.g., Eriksen 1974 cited
  by both `hed_response_conflict` and `hedtsk_eriksen_flanker`). These
  are legitimate reuses, not bugs. The triage output should preserve
  both with separate rows, not collapse them.

## 10. Expected outputs when Phase 2 runs

Rough sizing estimates for the user's planning:

- Landmark resolution: ~90-100 landmarks × 1 CrossRef call + 1
  OpenAlex verification = ~200 network calls, all cached thereafter.
  Wall time: ~60 seconds.
- Triage: zero network calls. Local computation over ~1,150 references.
  Wall time: ~5 seconds for everything including file write.
- Review file: 100-200 KB of Markdown. Readable in one scroll.

The user's review time after Sonnet hands off: 30-60 minutes if the
REVIEW bucket is under 200 entries; could be 2-3 hours if it balloons.
The fourth question in §9 above exists specifically to surface if
REVIEW ballooning would be bad — Sonnet should stop and ask rather
than hand back a 3-hour review task.

## 11. What comes after Phase 2

Once the user ticks KEEP/DROP and signs off:

1. A small "apply_triage.py" session (≤ 1 Sonnet pass) rewrites the
   reference arrays with the approved drops removed. This is the
   first session that mutates `process_details.json` and
   `task_details.json` in this workstream. The backup-before-rewrite
   discipline applies.
2. Phase 3 (systematic search per process and per task) runs against
   the cleaned catalog. The landmark gap list from sub-phase 2.5 seeds
   Phase 3's per-item candidate lists.

Neither of those belongs in Phase 2.
