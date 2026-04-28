# Task variation audit — thinking and decision document

**Date:** 2026-04-21
**Author:** Claude Opus
**Purpose:** Reasoning behind the new task variation audit pass and the Opus-vs-Sonnet handoff decision.

---

## What is "stale" about the old audit?

The old audit at `.status_2/variation_audit.md` was written 2026-04-16 and revised 2026-04-17. It analyzed the **pre-audit** state of `task_details.json` (1086 variations) and recommended 300 DROPs. It is no longer "current" for three independent reasons:

1. **Its DROP recommendations were applied.** Per `.status/session_2026-04-18_audit_and_cleanup.md`, `outputs/apply_variation_audit.py` removed 300 of ~300 DROP-classified variations on 2026-04-18 (16 name-mismatch survivors were cleaned up by `outputs/fix_remaining.py`). The old audit's KEEP/DROP table therefore describes a state that no longer exists in the JSON — the DROPPED rows are gone.

2. **Three follow-on refinement rounds happened after the audit was written, and are not reflected in it:**
   - 4 computerized variations dropped under the refined §5.6 rule (Computerized RAVLT, Digital TMT, Computerized UFOV, Computerized WCST-CV).
   - 2 confidence-rating add-ons dropped under the resolved §5.5 rule (Confidence-Rated Recognition, R/K with Confidence Ratings).
   - 1 dual-task survivor dropped under the resolved §5.4 rule (Concurrent Cognitive Load on Affective Picture Viewing).
   - Net result: 786 → 779 variations between the audit and the current JSON.

3. **The criteria document has been brought up to date but the audit hasn't.** `tasks_criteria.md` has resolved §§5.1, 5.4, 5.5, 5.6 and retired the EMOT category. The old audit's preamble still talks about the EMOT reversal as a "policy update"; it would benefit from being rewritten against the settled criteria rather than maintained as a delta narrative.

So the old audit has served its purpose. What we need now is a **post-audit verification document** — a fresh KEEP/DROP pass over the 779 variations that currently exist, written against the current criteria, that either confirms each surviving variation belongs in the catalog or flags it for further DROP.

## Confirmed current state (verified 2026-04-21)

- `task_details.json`: 103 tasks, 779 variations.
  - Verified by Grep on `"name":` (which appears only inside variation objects in this schema): 779 matches.
  - Verified by Grep on `"hedtsk_id":`: 103 matches.
  - Spot-checked Affective Picture Viewing Task (1 variation; matches expected post-audit state of 2 minus the 2026-04-18 dual-task drop = 1).
  - Spot-checked Biological Motion Perception (11 variations; matches the audit's "After: 11").
- `tasks_criteria.md`: 12 active DROP categories + 1 retired (EMOT), all five §5 borderline cases now resolved.
- The four §5 resolutions (5.4 dual-task, 5.5 confidence, 5.6 computerized, plus the EMOT reversal) constitute the policy delta from the original audit.

## What the new audit should produce

A document at `.status/task_variation_audit.md` that:

1. Lists every one of the 779 current variations, organized by task in the same order as `task_names.json`.
2. For each variation: gives a verdict (KEEP or DROP), and if DROP, the category code (one of the 12 active codes) and a one-line reason.
3. The expected default is KEEP for almost all variations — the original audit's DROPs are already out of the file. The new audit's main work is to confirm this and to surface anything that looks suspect under the now-settled criteria.
4. Includes a header that explicitly references `tasks_criteria.md` as the active criteria source rather than restating the criteria.
5. Includes summary statistics: per-task counts, total KEEP, total DROP (if any), and any DROP-by-category breakdown.
6. Calls out any task that gained variations not present in the old audit (these are most likely to need fresh judgment).

## Opus vs. Sonnet — handoff decision

**Decision: Hand off to Sonnet with detailed instructions.**

This is the same pattern used for the citation enrichment (Phase B, Phase C) and the process file consolidation. The reasons it fits here too:

- **Volume.** 779 variations to read, classify, and write a one-line verdict for. Even at 30 seconds per variation that is ~6 hours of focused work — too much for a single Opus session and a poor use of Opus tokens for what is mostly mechanical pattern matching against a settled rule set.
- **Criteria are written down and stable.** `tasks_criteria.md` §4 lists the 12 DROP codes with examples. §§5.1–5.6 resolve the borderline policies. There is no remaining ambiguity that requires Opus-level judgment for the bulk of cases.
- **A working template exists.** The old `.status_2/variation_audit.md` shows the expected output format (per-task tables with #, name, verdict, code, reason). Sonnet can follow the same structure.
- **Validation is cheap.** A new audit can be cross-checked against the old audit by comparing the surviving (KEEP) variations — they should mostly match, with explainable deltas in the four resolved §5 areas.
- **Opus stays in the loop.** When Sonnet returns the audit, Opus reviews it, runs spot-checks, decides whether any flagged borderline cases need a policy decision from the user, and only then escalates.

Where Opus IS adding value (this document):

- Identifying the three reasons the old audit is stale.
- Specifying the post-audit verification framing (rather than starting Sonnet on a blind reclassification, which would waste effort confirming DROPs that are already gone).
- Listing the four policy resolutions Sonnet must apply consistently.
- Specifying the file-access discipline that has burned previous sessions.

The instructions document is `.status/task_variation_audit_instructions.md`. The actual audit deliverable Sonnet will produce is `.status/task_variation_audit.md`.

## Edge cases worth flagging for Sonnet

These are areas where the verdict requires reading the variation description carefully, not just the name. Sonnet should be told to slow down on these:

1. **Variations whose name suggests a measurement modality but whose description shows a procedure change.** For example, a variation named "X with EEG" that turns out to specify a different stimulus stream designed for EEG decoding may be a genuine procedure change, not a MEAS add-on.

2. **Computerized/digital variations that survived §5.6.** Six variations are explicitly kept (eCorsi, Computerized DSST, Computerized Mirror Tracing, Computerized Adaptive Raven's, Computerized Tower of London, PD against Computer Opponents). These should re-emerge as KEEP. Any other "Computerized X" should be re-examined under the §5.6 rule (sensory or motor modality change required).

3. **Emotional-X variations.** All emotional variations are KEEP under the retired EMOT rule. There should be no DROP with code EMOT in the new audit.

4. **Confidence-rating variations.** The only confidence-rating KEEP is the Confidence-Accuracy Paradigm under Heartbeat Detection Task (per §5.5). Any other surviving confidence-rating variation should be flagged.

5. **Dual-task variations.** All dual-task add-ons should be DROP (DUAL) under the resolved §5.4. There should be no DUAL survivors.

6. **Variations that look like duplicates of the parent task.** "Standard X", "Classic X", and similar are ALIA candidates.

## What happens after Sonnet returns the audit

1. Opus reads the new `task_variation_audit.md`.
2. Opus runs a quick consistency check: any DROP at all? Any DROP without an active code? Any task with variations not present in the old audit's KEEP list?
3. Opus identifies anything that needs a user decision (likely a small number of borderline calls).
4. If the audit confirms the current state cleanly, the audit becomes the new active document and `.status_2/variation_audit.md` is marked superseded in `file_inventory.json`.
5. If the audit surfaces additional DROPs the user accepts, `outputs/apply_variation_audit.py` (already written, idempotent on already-clean data) is rerun against the new audit.
