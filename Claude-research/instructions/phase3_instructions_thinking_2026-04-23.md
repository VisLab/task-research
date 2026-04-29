# Phase 3 instructions — thinking summary

**Date:** 2026-04-23
**Companion to:** `.status/task_literature_search_phase3_instructions.md`
**Context:** Phase 1 primitives and Phase 2 triage are both complete
and validated (see `.status/session_2026-04-21_literature_search_phase1.md`
and `.status/session_2026-04-22_literature_search_phase2.md`). The
landmark list is resolved in `outputs/literature_search/landmark_refs.json`.
User asked for the Phase 3 instruction doc; this note explains the
design choices embedded in it.

The user is also mid-way through patching 15 malformed existing
references (`malformed_refs_2026-04-23.md`) — that work is independent
of Phase 3 but confirms the broader theme: the existing reference set
is the raw material Phase 3 ranks against, and anything Phase 3
produces will be evaluated on top of a cleaner base than Phase 2 had
to work with.

## 1. What Phase 3 is for (and what it isn't)

Phase 3 is the discovery and ranking layer. It produces a menu. The
parent plan describes nine total phases; Phase 3 is the most
expensive in terms of API budget and wall time, but it is
deliberately *not* the decision phase. Selection — the moment the
catalog's references actually change — happens in Phase 5 (human
review of the candidate markdown) and Phase 8 (JSON mutation).

I pushed hard against collapsing the scope. The sandbox session for
Phase 3 could technically write `publications.json`, stage Zotero
items, or auto-apply the top-25 to `process_details.json`. All
rejected. Every prior phase that tried to do two things at once cost
us a subsequent session to unwind the overlap. Phase 3's job is to
produce 275 markdown files and stop. The instructions doc's "What is
explicitly NOT part of Phase 3" section is nine bullets long for a
reason.

The asymmetry that matters: Phase 3 is a **write-heavy but
workspace-JSON read-only** phase. It writes hundreds of new markdown
files, thousands of new cache entries, and one session report — but
does not touch `process_details.json`, `task_details.json`,
`publications.json`, or anything under Zotero. Any diff against the
existing workspace JSON in the session report is a bug.

## 2. Why search goes on discovery clients and not validator clients

OpenAlex, Europe PMC, and Semantic Scholar are the three discovery
sources. CrossRef and Unpaywall are validators: CrossRef answers
"given a DOI, is this a real record and what's the exact metadata?";
Unpaywall answers "given a DOI, where's the OA PDF?". Neither is
designed as a discovery endpoint, and the source ladder in plan §4
treats them as cross-checks.

I considered adding `search` to CrossRef because CrossRef's
`/works?query=` endpoint works and would give us a fourth source for
redundancy. Rejected on two grounds:

- CrossRef search is relevance-ranked by a metric we can't tune and
  that historically under-surfaces high-impact papers on general
  queries. A fourth source would increase recall, but the marginal
  recall over OpenAlex+EuropePMC+S2 on the same query is empirically
  low, and the cost is a fourth pagination loop per item per pass.
- Phase 2 added `lookup_by_query` to CrossRef for landmark
  resolution — a targeted-citation use, not a discovery use. Keeping
  that function the only query-ish entry point on CrossRef preserves
  the mental model: CrossRef is for "resolve this one thing."

If a future phase finds real gaps that OpenAlex+EuropePMC+S2 miss,
adding CrossRef discovery is a clean delta. Not now.

## 3. Why three passes (foundational / recent / reviews) instead of one big query

A single giant query per item "find everything about response
inhibition" would produce the right superset but the wrong ranking.
OpenAlex's `sort=cited_by_count:desc` biases hard toward old,
heavily-cited papers; within the top 100 results for a well-studied
process, the last decade's work can be completely absent. Conversely,
restricting to `year >= today-8` and sorting by citations surfaces
modern high-impact papers but drops the canonical foundational ones.

The three-pass strategy is the cheapest way to guarantee both ends
of the distribution make it into the candidate pool before ranking:

- **Foundational pass** (no year filter, sort by cites) — the
  classical canon, including anything from before 1990 that is still
  relevant.
- **Recent pass** (year ≥ today-8, sort by cites) — the current
  literature. Eight years is roughly one methodological generation in
  neuroimaging and cognitive neuroscience.
- **Reviews pass** (review type filter, no year filter) — reviews
  serve a distinct role for Phase 5 (curator orientation), and
  surfacing them separately guarantees the ranker has at least a
  handful of review candidates to pin via the selection rule.

The three passes overlap substantially. Dedup in `rank_and_select.py`
collapses them into one pool per item, and the composite score
applies once. The "pass" concept is about query-time recall, not
about scoring or display.

I briefly considered a fourth pass for "methods" (papers primarily
about paradigm design). Rejected — paradigm-construction papers are
already surfaced by the foundational pass (they tend to be old and
highly cited). The curator's role-labeling affordance in Phase 5
handles the downstream distinction.

## 4. Per-source alias handling: why OpenAlex and EuropePMC get one OR-query but Semantic Scholar gets N queries

This is a pragmatism call, not a philosophy call. OpenAlex's `search`
parameter and Europe PMC's query DSL both support boolean `OR`
reliably — one query with `("<name>" OR "<alias1>" OR "<alias2>")`
works and returns a union. Semantic Scholar's `/graph/v1/paper/search`
supports free-text query only; boolean operators within the query
string are treated as literals or are silently ignored depending on
the day. The empirical behavior has changed multiple times since
2023.

The defensive approach is to run S2 once per alias and union the
results post-hoc. This increases S2 call count roughly 2-4× per
item. **Correction (2026-04-28):** earlier passes of this thinking
doc assumed a free-tier S2 API key lifted the search rate limit
from 1 rps to 100 rps. That is not correct — free-tier keys leave
the search-endpoint rate at 1 rps. So budget for 1 rps regardless
of whether a key is set. The sub-phase 3.1 question on key
acquisition still matters (it gives S2 visibility into the caller
and is required for some auth-scoped endpoints), but it does NOT
move the wall-clock estimate.

Capping the per-item S2 union at 100 candidates post-merge is
important. Without a cap, a process with four aliases each pulling
100 results would contribute 400 S2 candidates before dedup; with
overlap across sources and passes that spikes the total candidate
pool per item to ~600, which trashes the scoring pass's runtime for
no recall benefit.

## 5. Why the POC is a hard gate before the full run

The plan §15 recommends running on 3–5 items before the full 275.
The instructions doc makes this mandatory, not recommended. Three
reasons:

- **API budget.** A full-run mistake costs ~5,000 calls. A POC
  mistake costs ~60 calls. The ratio is large enough that the
  asymmetry of regret favors the POC gate even when the pipeline
  looks fine on code review.
- **Ranker visibility.** The composite score is specified in plan §6
  but has never actually been run on real data. Sub-phase 3.4 is the
  first time it meets reality. POC is where we find out that some
  weight is not pulling its weight (pun intended) before we bake 275
  markdown files.
- **Curator feedback loop.** The user's job in Phase 5 is to sanity
  check 25 candidates per item × 275 items = ~7000 candidate rows.
  If the markdown presentation is wrong — abstract truncation, table
  columns, missing landmark flagging — that's 7000 rows of wrong
  before anyone notices. POC gives the user three markdown files
  before committing to 275.

The three POC items were chosen deliberately:

- `hed_response_inhibition` — the "everything works" case. Mature
  literature, unambiguous landmarks, multiple linked tasks, covers
  the OpenAlex topic filter path.
- `hedtsk_stroop_color_word` — a task (not a process). Exercises the
  task-side of the builder and the alias-union logic (multiple
  common names).
- `hed_model_based_learning` — a modern-skewed process where the
  recency pass has to carry more weight. Also tests the RL / comp-
  psychiatry venue mix, which stresses `classify_venue` more than
  standard cognitive-neuroscience venues.

If these three pass, the rest is likely to work. If any of them
produces surprising output, the POC session pays for itself.

## 6. Why the ranking weights are locked at the plan §6 values

The composite score is:

```
  0.35 * citation_percentile
+ 0.20 * venue_tier
+ 0.15 * publisher_tier
+ 0.15 * recency
+ 0.10 * query_relevance
+ 0.05 * review_bonus
+ 0.30 * landmark_bonus (additive)
```

These weights were chosen in plan §6 after explicit discussion. The
instructions doc forbids tuning them during Phase 3 for the same
reason Phase 2 forbade applying drops: the value of the design is
in the discipline of not re-opening the spec every session.

If the POC exposes a ranking that looks wrong — say, a specialty-
venue paper with high citations outranking a flagship review — the
instruction is to flag it in the session report and ask, not to edit
the weight and rerun. Silent weight drift across sessions is the
failure mode I'm most trying to prevent. The weights are the
contract between Phase 3 and Phase 5.

(The one exception, and it is explicit in the instructions: in the
foundational-slot selection, recency is neutralized to 0.5 rather
than computed. This is a plan §6 rule, not a tuning — it prevents
the foundational selection from double-counting recency, which is
separately privileged in the recent-slot selection.)

## 7. Why candidates/ lives in outputs/ but the index lives in .status/

275 markdown files dropped into `.status/` would swamp the 40-ish
decision notes and session reports that already live there. The
`.status/` convention in this project is "things the user consults
to understand state," not "the bulk data of a phase." Per-item
candidate files are bulk data; they belong in `outputs/`.

The top-level index, on the other hand, is the single document the
user opens to start the Phase 5 review. It earns a place in
`.status/` as a state marker — "here's the pointer into 275 files'
worth of review material, dated so the next session can tell which
index is current."

I considered having the index auto-generate in
`outputs/literature_search/candidates/index.md`. Rejected because the
index is per-run (dated), whereas the per-item files are
addressable-forever (by `<item_id>`). Keeping the index dated and
outside the candidates directory makes the "which run am I looking
at?" question explicit.

## 8. Why Europe PMC, not a separate NCBI E-utilities client

Europe PMC mirrors the PubMed index plus adds OA metadata, and
returns a clean JSON response without the XML/JSON switch that
NCBI E-utilities imposes (`esearch` → `esummary` → `efetch`
pipeline). Adding a separate `pubmed.py` client doubles the Phase 3
surface area for negligible recall gain — Europe PMC claims >99%
PubMed coverage, and the only papers that are uniquely in PubMed
are a long tail of non-English, non-OA, mid-20th-century clinical
papers that are unlikely to be Phase 3 candidates anyway.

The instructions doc leaves the door open: if POC reveals genuine
PubMed-only gaps on specific items, adding a `pubmed.py` client is
a follow-up session, not a Phase 3 deliverable.

## 9. Why 25 picked per item with 100 emitted

Phase 5 is the bottleneck. If the curator has to review 100
candidates per item, the total review load is ~28,000 rows, which
is a month of full-time work. 25 candidates per item is ~7,000
rows, which is a week of part-time work. 5 foundational + 20
recent = 25 is the breakpoint that falls out of the sums.

But the ranker is imperfect. Emitting only the 25 picked would hide
from the curator exactly the cases where the ranker got it wrong.
Emitting the full deduplicated pool (up to 100) lets the curator
scan past the cutoff in the cases that matter — a paper that
"feels foundational" but scored below the top 5 — without adding
much cognitive load because the markdown sections are ordered and
the picked rows are flagged.

The 100 cap on emitted candidates is there to bound the markdown
file size. Beyond 100, the signal-to-noise ratio of the audit tail
collapses.

## 10. Why the diversity rule is per-item, not global

The diversity rule ("no single first-or-last author appears on more
than 3 picked candidates for this item") is scoped to a single
item's selection because literature clustering happens at the
sub-field level, not the corpus level. For a process like
`hed_working_memory`, one author's contribution can dominate the
citation graph (Baddeley has 25+ high-cite papers on the topic);
without the cap, the picked list for that item could be 12 Baddeley
papers and 13 others.

Scoping globally (e.g., "no author appears more than 3 times across
all 275 items' picks") would be philosophically cleaner but
operationally wrong. A neuroscientist who works across cognitive
control, attention, and executive function *should* show up in the
picked set for each of those processes — they are the right author
for each. Capping globally would silently suppress legitimate
multi-process contributions.

## 11. Why we reuse `triage_rules` primitives rather than re-deriving

`triage_rules.py` already encodes PUBLISHER_TIERS, VENUE_TIERS, and
the `classify_venue` + `publisher_tier_from_doi` functions. Phase 3
needs exactly the same classification logic to score candidates.
Duplicating it — even with "just a few tweaks for the Phase 3 use
case" — would fork two copies of a taxonomy that has to stay
synchronized as the catalog grows.

The import pattern from `rank_and_select.py`:

```python
from triage_rules import (
    classify_venue,
    publisher_tier_from_doi,
)
```

If Phase 3 finds a venue string that's missing from the allowlist,
the instruction is to add it to `triage_rules.py`, not to maintain a
second allowlist in `rank_and_select.py`. This preserves the Phase 2
property that the user can review "the rules" in one file.

The side benefit: Phase 2's venue allowlist has been hand-curated to
~135 venues across flagship/mainstream/specialty. Phase 3 inherits
all of that work for free.

## 12. The host-script pattern (session 4 of using it)

Phase 3 is the fourth session in this workstream to use the host-
script pattern, after Phase 1, Phase 2, and the enrich-citations
pass. The pattern is: Sonnet writes a self-contained Python
entrypoint; the user runs it on the Windows host; Sonnet reviews
the output logs and writes a session report.

Why this is worth the friction: the Cowork sandbox has no network
egress, and the workspace is on a Windows host with Python + real
internet. Every phase of this workstream hits external APIs. The
alternative to the host-script pattern would be manual
copy-paste-and-run, which loses the automation and the cache
benefits. Putting the automation in a Python script the user runs
manually, once, is the cleanest compromise between "Sonnet does
everything" and "user runs everything."

The instruction doc's key reminder: the Sonnet session stops *after*
producing the three POC markdown files, not after producing all
275. The user runs the full search themselves, with the code Sonnet
wrote. The session report gets updated after the user reports back
with the full-run summary.

## 13. The virtiofs stale-snapshot discipline

This has bitten every session. The bash sandbox sees a potentially
stale snapshot of mounted workspace files — specifically,
`process_details.json` and files under `outputs/` that were written
by the Write tool can show up in bash as either truncated or with
trailing null bytes. The Read tool uses the native Windows handle
and always sees the current file.

Rules encoded in the instructions:

- Use the Read tool for any workspace JSON or markdown.
- Use the Write/Edit tools for any mutation to workspace files.
- Use bash only for *running* Python (after it has been written via
  Write tool).
- The `_inputs/` transient directory pattern from Phase 2 carries
  forward: if a script needs to read JSON during in-sandbox
  development, Read-copy it to `outputs/literature_search/_inputs/`
  first.
- The host script itself (`phase3_search.py`) runs on Windows, so
  normal `open()` works there — the stale-snapshot rule is sandbox-
  only.

This is boilerplate but omitting it has cost multi-hour debugging
sessions twice in this project. Worth restating in every phase's
instructions.

## 14. What I considered and rejected

**Running the search in-sandbox via a proxy or tunnel.** Rejected —
against the sandbox's network policy, not worth the time to plumb.
Host-script pattern wins.

**Pre-merging candidates into `publications.json` during Phase 3.**
Rejected for the same reason Phase 2 didn't apply drops: the human
review gate is the feature. `publications.json` is a Phase 6 concern.

**Storing candidate files as JSON instead of markdown.** Rejected —
the review is a human activity, and markdown renders in the user's
editor and in GitHub. JSON would require a second render step to be
reviewable, and we gain no structure that the markdown format
doesn't already carry (the tables and checkboxes are structured
enough).

**Adding an ML-based relevance score.** Rejected — the plan §6
query_relevance is a word-overlap score at weight 0.10. A
transformer embedding would improve relevance but at the cost of a
model dependency, a GPU, an inference server, and a non-
deterministic scoring pass. The 0.10 weight means even a perfect
relevance signal wouldn't move rankings by much. Not worth the
complexity.

**Paging OpenAlex beyond 4 pages.** Rejected — cited_by_count-sorted
results beyond the top 200 per query are rarely Phase 3 candidates.
The pagination cap keeps the API budget bounded.

**Using Semantic Scholar's `/paper/search/bulk`.** Rejected —
different rate-limit semantics, requires a partner agreement, and
the graph API's vanilla `/paper/search` is sufficient for our scale.

## 15. Open questions I am deferring

These are flagged in the instructions doc for Sonnet to ask before
running:

- **OpenAlex topic crosswalk availability.** Sub-phase 3.1 asks
  Sonnet to probe `H:\Research\TaskResearch\OpenAlex\` for the
  crosswalk file. If present, topic-filtered queries are used; if
  not, text-only queries still work but with lower precision. Either
  is correct — the question is which path the full run takes.
- **API keys for Semantic Scholar and PubMed/NCBI.** **Corrected
  2026-04-28:** earlier copy here said the keys reduce wall time
  from ~60–90 minutes to ~10. That was wrong — a free-tier S2 key
  does NOT lift the search-endpoint rate limit, and Phase 3 does
  not currently use NCBI (Europe PMC is used instead). Set the
  S2 key for visibility/auth-scoped endpoints, but expect ~60–90
  minutes for the full run regardless.
- **Whether to include the three proposed POC items, or swap.** The
  POC choices are opinionated; the user may prefer different items
  (e.g., a process with known sparse literature to stress the
  low-candidate case).
- **Whether the composite-score output needs a separate "explain"
  column.** Current plan is to emit one `Score: 0.72` value per
  candidate. If the user wants a breakdown (`citation=0.85
  venue=1.0 publisher=0.6 recency=0.4 qrel=0.5 review=0.0 lm=0.0`)
  the markdown gets wider and the file sizes grow ~20%. Worth
  asking before committing to either.

## 16. Expected outputs and sizing

- Per-item candidate markdown: ~15–30 KB each × 275 items ≈ 5 MB
  total under `outputs/literature_search/candidates/`.
- Cache size after full run: ~5,000 API responses × ~20 KB average
  JSON = ~100 MB under `outputs/literature_search/cache/`. Git-
  ignored per Phase 1 convention.
- Index file: ~30 KB.
- Session report: ~10 KB.
- API calls per full run: ~5,000 total (three passes × three
  sources × 275 items, with pagination ~1.5× on average).
- Wall time: ~60–90 minutes cold, regardless of S2 key (S2 caps at
  1 rps either way — the key is not a free-tier accelerator).
  Same-day re-runs are near-instant due to the cache.
- POC wall time: ~2 minutes warm, ~5 minutes cold.

## 17. What comes after Phase 3

Once the user has reviewed the three POC files and approved:

1. User runs `phase3_search.py --mode full --write`. Wall time
   ~10–90 minutes. 275 candidate markdown files produced.
2. Phase 4 (co-mention search) runs a separate pass over the
   (process × task) cross-product, using the same clients and cache
   but with different query construction. Phase 4 is not in Phase
   3's scope.
3. Phase 5 (human review) is the curator going through the 275
   candidate markdown files and ticking KEEP/DROP/role. Unblocks
   Phases 6–8.

Phase 3 does not touch any of that. Its one job is to produce the
menu.
