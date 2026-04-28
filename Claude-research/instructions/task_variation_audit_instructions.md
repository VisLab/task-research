# Task: Re-audit task variations against the current criteria

**Date:** 2026-04-21
**Goal:** Produce a current, comprehensive KEEP/DROP audit of every variation that exists in `task_details.json` today (779 variations across 103 tasks), written against the now-settled criteria in `tasks_criteria.md`. The result lives at `.status/task_variation_audit.md` and supersedes `.status_2/variation_audit.md`.

This is a **post-audit verification pass**, not a fresh classification. The original 2026-04-16 audit was already applied to the JSON: 300 variations were dropped on 2026-04-18, plus 7 more in the §5 follow-on rounds (4 computerized, 2 confidence-rating, 1 dual-task). The variations that exist today are the ones that survived all those passes. Your job is to confirm each one belongs and to surface anything that does not.

See also: `.status/task_variation_audit_thinking_2026-04-21.md` (Opus's analysis of why the old audit is stale and the framing for this pass).

---

## Context

`task_details.json` is a flat JSON array of 103 task objects. Each task has a `variations` array. Each variation is an object with two fields:

```json
{
  "name": "Sally-Anne Task",
  "description": "Classic change-of-location false belief paradigm: Sally hides a marble, Anne moves it, where will Sally look?"
}
```

There are 779 such variation objects in total. They were curated through the original audit + the §5 follow-on drops, so the prior expectation is that almost all of them are KEEP. The new audit's value lies in:

1. Producing one document that catalogs the current state, organized to match `task_names.json` ordering.
2. Cross-checking each variation against the now-settled criteria.
3. Flagging anything that looks suspect — especially in the four areas where policy has changed since the original audit was written.

---

## What specifically needs to happen

### Phase 1: Confirm starting state

- Read `.status/task_variation_audit_thinking_2026-04-21.md` for the framing of this pass.
- Read `tasks_criteria.md` in full. §4 lists the 12 active DROP codes; §§5.1–5.6 are the resolved borderline policies you must apply uniformly.
- Read `.status_2/variation_audit.md` for the working format. **Do not** copy its structure verbatim — that document tracked DROPs only; the new audit lists every current variation. But the per-task table format (#, name, verdict, code, reason) is a good template.
- Read `.status/session_2026-04-18_audit_and_cleanup.md` items 5–8 to understand the four §5 resolutions that happened after the original audit.

### Phase 2: Extract the current variations

Write a single-file Python script `outputs/extract_current_variations.py` that:

1. Loads `task_details.json` (use the working copy approach in §File access rules, never bash directly on the workspace mount).
2. For each task, in the order they appear in the JSON, emits: `hedtsk_id`, `canonical_name`, and the list of `(name, description)` pairs from `variations`.
3. Writes the result to `outputs/current_variations.json` as a structured dump.
4. Also prints a per-task variation count and a grand total. The grand total must be 779. If it is not, stop and re-read `.status/task_variation_audit_thinking_2026-04-21.md`'s "Confirmed current state" section before continuing.

Verify: 103 tasks, 779 variations, totals match.

### Phase 3: Build the audit document

Write `.status/task_variation_audit.md`. Structure:

```markdown
# Task Variation Audit (Current State)

Date: 2026-04-21
Author: <your name>
Supersedes: .status_2/variation_audit.md

## Purpose

A KEEP/DROP audit of every variation currently in task_details.json, written against the active criteria in tasks_criteria.md. This is a post-audit verification: the original 1086 → 779 reduction has already been applied; this pass confirms the survivors and flags any that should still be removed.

## Criteria

The active criteria are defined in tasks_criteria.md. This audit applies them as-is; it does not restate them. The 12 active DROP codes are: MEAS, ANAL, DESG, STIM, POPL, IDIF, TRAN, PHAR, SCOR, ALIA, MOTI, DUAL. EMOT is retired (§5.1). The four §5 resolutions are honored (§5.4 dual-task uniformly DROP, §5.5 confidence-rating uniformly DROP except Confidence-Accuracy Paradigm in Heartbeat Detection, §5.6 computerized only KEEP if sensory/motor modality changes).

## Summary

- Total variations audited: 779
- KEEP: <count>
- DROP (newly flagged): <count>
- Tasks with all variations confirmed: <count>
- Tasks with at least one new DROP: <count>

## Per-task tables

[One section per task, in task_names.json order, see template below]

## DROPs by category (newly flagged only)

| Code | Count | Examples (task — variation) |
|------|-------|-----------------------------|
| ... | ... | ... |

## Items for user review

[List any variation where the verdict required a judgment call you do not feel confident making alone.]
```

For each task, the section format is:

```markdown
### NN. <Canonical Name> (`hedtsk_id`)

Variations: <count>

| # | Variation | Verdict | Code | Reason |
|---|-----------|---------|------|--------|
| 1 | <name> | KEEP | — | <one-line justification, e.g. "Distinct procedure: participant generates strings instead of judging them"> |
| 2 | <name> | DROP | <code> | <one-line reason that ties to the code> |
```

For KEEP rows, the reason should describe what makes the variation a genuine procedural / experiential change (the positive criterion in `tasks_criteria.md` §4). Do not write "no reason to drop" — write the affirmative reason it qualifies. Reasons can be short (10–20 words is fine).

For DROP rows, the reason cites the DROP code from `tasks_criteria.md` §4 and applies the test for that code. Example: `MEAS — pure recording add-on with no procedural change`.

### Phase 4: Apply the four §5 policy rules carefully

For each of the following areas, your audit must produce results consistent with the resolved policies. If you find a survivor that violates a resolved policy, it should be DROP in your new audit (and surfaced in the "Items for user review" section since the original audit pass already missed it):

- **§5.1 EMOT (retired):** No DROP entry should ever have code `EMOT`. All Emotional-X variations are KEEP. Expect ~13 such variations across the catalog.
- **§5.4 DUAL (uniformly DROP):** If you find any surviving dual-task variation (concurrent secondary task that is not itself a recognized named paradigm), it is DROP code `DUAL`. The original audit already removed all known DUAL survivors as of 2026-04-18 — none should remain.
- **§5.5 Confidence ratings:** Only one confidence-related variation is KEEP: `Confidence-Accuracy Paradigm` under Heartbeat Detection Task. Any other variation that adds a confidence/subjective rating to an otherwise-unchanged base task is DROP code `MEAS`.
- **§5.6 Computerized/digital:** Six computerized variations are KEEP under the modality-change rule (eCorsi, Computerized DSST, Computerized Mirror Tracing, Computerized Adaptive Raven's, Computerized Tower of London, PD against Computer Opponents). Any other "Computerized X" must change the participant's sensory or motor modality to be KEEP; otherwise DROP code `DESG` (or `MEAS` if it's an automated-scoring add-on).

### Phase 5: Edge case handling

Slow down on these patterns. They tripped up the original audit and may still hide:

1. **Names that suggest a modality but descriptions that show a procedure change.** Read the description, not just the name. A variation called "X with fMRI" is usually MEAS, but if its description specifies a different stimulus stream or response window designed for fMRI timing, that may be a procedural change (DESG borderline — flag for review).

2. **Aliases of the canonical task.** A variation called "Standard X", "Classic X", or "X (basic)" that restates the canonical procedure is `ALIA`.

3. **Aliases of another variation in the same task.** Catch these by reading all variations in a task before judging individual ones. The original audit caught many of these in Biological Motion Perception, False Belief, Navon, and Visual Search. There should be few left.

4. **Aliases of a different top-level task.** A variation that is itself a top-level task elsewhere in the catalog (e.g., "Emotional Stroop" appearing as a variation under standard Stroop, when it is a separate top-level task) is `ALIA`.

5. **Population/clinical use of a procedurally unchanged task.** "X in amnesia", "X for children" → `POPL`, unless the variation description shows the actual procedure was modified (different stimulus pacing, simplified response set, etc.).

When in doubt, prefer KEEP and flag the variation in "Items for user review" with a one-paragraph note explaining the ambiguity. Do not silently DROP borderline cases.

### Phase 6: Self-consistency checks before declaring done

Run these checks against your draft `.status/task_variation_audit.md`:

- [ ] All 103 tasks present in the same order as `task_names.json`.
- [ ] Sum of "Variations: <count>" lines equals 779.
- [ ] Every row has a verdict (KEEP or DROP), no blanks.
- [ ] No DROP row has code `EMOT`.
- [ ] No DROP row uses a code outside the 12 active codes (MEAS, ANAL, DESG, STIM, POPL, IDIF, TRAN, PHAR, SCOR, ALIA, MOTI, DUAL).
- [ ] No DROP row whose reason is empty or generic ("redundant", "duplicate") without specifying *which* it duplicates.
- [ ] Summary section's KEEP + DROP equals 779.
- [ ] DROPs-by-category table totals match the count of DROP rows.
- [ ] Heartbeat Detection Task includes `Confidence-Accuracy Paradigm` as KEEP.
- [ ] All 13 (or however many remain) Emotional-X variations are KEEP.

### Phase 7: Write a session report

Write `.status/session_2026-04-21_variation_audit.md`:

- Total counts.
- Number of new DROP flags (expected: small, possibly zero).
- List of variations sent to "Items for user review" with a brief rationale for each.
- Any task whose variations seem to need a substantive description rewrite (separate from the audit but worth noting).
- Any inconsistency found between the audit's expected post-state and the actual JSON state (could indicate the JSON drifted since 2026-04-18).

---

## CRITICAL: File access rules — virtiofs stale snapshot issue

The bash sandbox sees a stale, potentially corrupted snapshot of the mounted Windows workspace. Files appear truncated, get trailing null bytes, or show stale content after edits. This has burned multiple prior sessions.

**Mandatory rules:**

1. **Always use the Read tool** (with Windows paths like `H:\Research\TaskResearch\Claude-research\task_details.json`) to read files in the workspace. Do **NOT** use bash `cat`, `head`, `tail`, or Python `open()` against `/sessions/.../mnt/Claude-research/...`.

2. **Always use the Write or Edit tool** to write files back to the workspace. Do **NOT** write via bash.

3. **For processing in bash:** Read the file with the Read tool, then use the Write tool to save a copy under `outputs/` (which maps to `/sessions/.../mnt/outputs/` and is safe for bash I/O). Process the copy in bash. Use the Write tool to put final results back at the workspace path.

4. **After any Write/Edit to the workspace,** verify with the Read tool, never bash. Bash will still see the old content.

5. **JSON parse errors in bash** are almost always trailing null bytes from the stale mount, not real syntax errors. Strip null bytes from the working copy.

6. **`task_details.json` is large (~20,000 lines).** When reading it through the Read tool, prefer reading the file in full once and saving a working copy to `outputs/task_details_working.json`, then operating on the working copy from bash. Do not Read the workspace file repeatedly — each call hits the same stale-snapshot risk if subsequent writes have happened.

---

## File inventory

### Files you will read (do not modify)
- **`task_details.json`** — Source of the 779 variations. Windows path: `H:\Research\TaskResearch\Claude-research\task_details.json`.
- **`tasks_criteria.md`** — Active criteria. Windows path: `H:\Research\TaskResearch\Claude-research\tasks_criteria.md`.
- **`task_names.json`** — Use for canonical task ordering. Windows path: `H:\Research\TaskResearch\Claude-research\task_names.json`.
- **`.status_2/variation_audit.md`** — Old audit, for format reference and historical comparison.
- **`.status/session_2026-04-18_audit_and_cleanup.md`** — Documents the four §5 resolutions and confirms the post-audit state of 779.
- **`.status/task_variation_audit_thinking_2026-04-21.md`** — Opus's framing for this pass.

### Files you will create
- **`outputs/extract_current_variations.py`** — Extraction script (Phase 2).
- **`outputs/current_variations.json`** — Structured dump of all 779 variations (Phase 2).
- **`.status/task_variation_audit.md`** — The new audit (Phases 3–6). **This is the primary deliverable.**
- **`.status/session_2026-04-21_variation_audit.md`** — Session report (Phase 7).

### Files you will not touch
- `task_details.json` — Read-only for this pass. Application of any new DROPs is a separate, follow-up task that requires user approval before invoking `outputs/apply_variation_audit.py`.
- `tasks_criteria.md` — Read-only.
- Any other file in the project.

---

## Working conventions

- The user's standing preference: clean, well-thought-out work. Do not over-engineer. Produce a thinking summary in `.status/` documenting your reasoning if any non-obvious decisions came up during the pass.
- Defer to KEEP when in doubt. The cost of a wrongly-flagged DROP is higher than the cost of a borderline KEEP, because DROP causes data removal once `apply_variation_audit.py` runs.
- Surface every borderline call in "Items for user review" rather than silently deciding it.
- The grand total (779) is a hard invariant. If your extraction script disagrees, stop and investigate before drafting the audit.

---

## Verification checklist (must all pass before declaring done)

- [ ] `outputs/extract_current_variations.py` runs cleanly and reports 103 tasks, 779 variations.
- [ ] `outputs/current_variations.json` exists and is well-formed JSON.
- [ ] `.status/task_variation_audit.md` exists and follows the per-task table format.
- [ ] All 103 tasks are present, in `task_names.json` order.
- [ ] Per-task variation counts in the audit equal those in `outputs/current_variations.json`.
- [ ] No DROP row uses the retired EMOT code.
- [ ] All four §5 policies are applied uniformly (DUAL DROP, confidence ratings DROP except CAP, computerized KEEP only when modality changes, no EMOT DROPs).
- [ ] Every borderline judgment is surfaced in "Items for user review" rather than silently chosen.
- [ ] Session report written.
- [ ] No edits made to `task_details.json` or any other authoritative file.

---

## Out of scope (do not attempt)

1. **Applying any new DROPs to `task_details.json`.** That requires user approval and a separate run of `outputs/apply_variation_audit.py`.
2. **Rewriting variation descriptions.** If a description seems weak, note it in the session report; don't fix it here.
3. **Adding new variations.** This pass audits what exists; it does not propose additions.
4. **Promoting variations to top-level tasks.** Decision deferred (see `tasks_criteria.md` §5.1).
5. **Editing `tasks_criteria.md`.** The criteria are the input to this audit, not its output.
