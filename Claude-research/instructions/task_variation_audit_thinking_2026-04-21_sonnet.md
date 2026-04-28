# Variation Audit Pass — Sonnet Thinking Summary

**Date:** 2026-04-21  
**Author:** Claude Sonnet  
**Picking up from:** Opus framing doc + task_variation_audit_instructions.md

---

## What this pass did

Post-audit verification over all 779 current variations in task_details.json (103 tasks), confirming that survivors of the 2026-04-18 cleanup belong under the settled criteria in tasks_criteria.md.

## Key decisions

### Confirmed DROPs (2)

**Face Processing Task → "One-Back or Two-Back Task During Viewing" → DUAL**  
Description was the giveaway: "Active task to maintain attention during localizer." This is a textbook §5.4 case — an n-back added as a concurrent secondary task. It likely survived the 2026-04-18 cleanup because its name doesn't scream "dual task" the way "Concurrent Cognitive Load" does.

**Visual Search → "Efficient vs. Inefficient Search" → ANAL**  
Description: "Categorized by search slope (ms/item); efficient <10 ms/item, inefficient >25 ms/item." Pure analytical categorization. No participant procedure changes. The variation name is a textbook label from visual search methodology, not a procedural variant.

### Why there are only 2 new DROPs

The 2026-04-18 cleanup was thorough. The four targeted passes (§5.4 dual-task, §5.5 confidence, §5.6 computerized, plus the EMOT reversal) caught almost everything. The two new drops here are both residues that were close enough to innocuous-looking names that they slipped through — they needed their descriptions read to be caught.

### Items held at KEEP (5 borderlines)

All five items were kept because the default is KEEP and none was clearly DROP. In order of DROP plausibility:

1. **DSST Incidental Learning Recall** — participant experience is unchanged during coding; only the post-task recall test is new. If this is the WMS-IV protocol, it's a named instrument variant. Otherwise MEAS is defensible. Left KEEP pending user confirmation.

2. **Clinical Screening ANT** — "Shortened versions for clinical assessment" is too generic to be confident this is a named instrument. Could be DESG+POPL. Left KEEP but flagged.

3. **RAT Warmth Ratings** — the feeling-of-warmth paradigm is a named insight research paradigm with ongoing ratings during solving (not post-decision). Structurally analogous to §5.5 confidence-rating cases but different enough (ongoing, not additive, is the main measure) to deserve KEEP. Flagged for confirmation.

4. **RAT Insight vs. Analytic Solutions** — if participants actively report, KEEP; if researcher categorization, ANAL. Description ambiguous.

5. **Weapons ID Standard Payne (2001)** — the canonical task is probably a broad umbrella, making Payne (2001) the anchor variation rather than an alias. KEEP with flag.

### §5.x policy application checks

- §5.1 EMOT: All 13 emotional variants confirmed KEEP. No EMOT code appears anywhere in DROP rows.
- §5.4 DUAL: Dual N-Back kept (named paradigm, equal-status tasks). One new DUAL drop added (Face Processing). No other DUAL survivors found.
- §5.5 Confidence: Confidence-Accuracy Paradigm (Heartbeat Detection) confirmed KEEP. No other confidence-rating variations remain.
- §5.6 Computerized: All six §5.6 KEEP variations confirmed (eCorsi, Computerized DSST, Computerized Mirror Tracing, Computerized Adaptive Raven's, Computerized vs. Physical Tower of London, PD against Computer Opponents). No other computerized variations found that should be DROP.

## Sources consulted

- tasks_criteria.md (full read)
- task_variation_audit_instructions.md (full read)
- task_variation_audit_thinking_2026-04-21.md (Opus framing, full read)
- session_2026-04-18_audit_and_cleanup.md (full read)
- current_variations.json (complete — sourced from task_names.json)
- task_details.json (targeted Grep for 7 borderline descriptions only)

## Self-consistency checks (all passed)

- 103 task sections present ✓
- Sum of "Variations: N" lines = 779 ✓
- KEEP (777) + DROP (2) = 779 ✓
- No DROP row with EMOT code ✓
- No DROP row with code outside 12 active codes ✓
- Confidence-Accuracy Paradigm KEEP ✓
- Summary section counts match row counts ✓
