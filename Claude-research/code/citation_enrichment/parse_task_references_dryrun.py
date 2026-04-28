"""
parse_task_references_dryrun.py

Phase C dry-run: parse all task reference strings in task_details.json and
report statistics without touching the file or making any network calls.

Run from the outputs/ directory:
    python parse_task_references_dryrun.py

Reads:  ../task_details.json
Writes: parse_dryrun_report.md  (in this directory)
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

# Locate files relative to this script.
SCRIPT_DIR   = Path(__file__).parent
TASK_FILE    = SCRIPT_DIR.parent / "task_details.json"
REPORT_FILE  = SCRIPT_DIR / "parse_dryrun_report.md"

# Import the parser from the same directory.
sys.path.insert(0, str(SCRIPT_DIR))
from parse_citation_string import parse

# -----------------------------------------------------------------------
# Load data
# -----------------------------------------------------------------------

with open(TASK_FILE, encoding="utf-8") as fh:
    tasks = json.load(fh)

print(f"Loaded {len(tasks)} tasks from {TASK_FILE.name}")

# -----------------------------------------------------------------------
# Parse every reference string
# -----------------------------------------------------------------------

CATEGORIES = ["clean_journal", "clean_book", "clean_chapter",
               "clean_report", "has_doi", "malformed"]

results_by_cat  = defaultdict(list)   # category -> list of (task_id, string, ParsedCitation)
all_strings     = []                  # (task_id, ref_key, string)

for task in tasks:
    tid = task.get("hedtsk_id", "?")
    for ref_key in ("key_references", "recent_references"):
        for ref in task.get(ref_key, []):
            if not isinstance(ref, str):
                print(f"WARNING: non-string ref in {tid}.{ref_key}, skipping.", file=sys.stderr)
                continue
            all_strings.append((tid, ref_key, ref))
            pc = parse(ref)
            results_by_cat[pc.parse_quality].append((tid, ref_key, ref, pc))

total = len(all_strings)
print(f"Parsed {total} reference strings.\n")

# -----------------------------------------------------------------------
# Build report
# -----------------------------------------------------------------------

lines = []
lines.append("# Citation String Parse Dry-Run Report")
lines.append("")
lines.append(f"**Task file:** `task_details.json`  ")
lines.append(f"**Tasks:** {len(tasks)}  ")
lines.append(f"**Total reference strings:** {total}")
lines.append("")
lines.append("## Summary")
lines.append("")
lines.append("| Category | Count | % |")
lines.append("|---|---|---|")

for cat in CATEGORIES:
    n = len(results_by_cat[cat])
    pct = 100.0 * n / total if total else 0
    lines.append(f"| {cat} | {n} | {pct:.1f}% |")

malformed_n = len(results_by_cat["malformed"])
malformed_pct = 100.0 * malformed_n / total if total else 0
threshold_ok = malformed_pct < 5.0
lines.append("")
lines.append(f"**Malformed rate: {malformed_pct:.1f}%** "
             f"({'OK - below 5% threshold' if threshold_ok else 'FAIL - exceeds 5% threshold; fix parser'})")

# -----------------------------------------------------------------------
# Examples per category (up to 5 each)
# -----------------------------------------------------------------------

lines.append("")
lines.append("## Examples by Category")
lines.append("")

for cat in CATEGORIES:
    rows = results_by_cat[cat]
    lines.append(f"### {cat} ({len(rows)} refs)")
    lines.append("")
    for (tid, rk, s, pc) in rows[:5]:
        short = s if len(s) <= 120 else s[:117] + "..."
        lines.append(f"- `{tid}` ({rk})  ")
        lines.append(f"  `{short}`  ")
        if cat not in ("has_doi", "malformed"):
            lines.append(
                f"  -> authors=`{pc.authors[:40] if pc.authors else ''}` | "
                f"year={pc.year} | venue=`{(pc.venue or '')[:40]}` | "
                f"vol={pc.volume} iss={pc.issue} pp={pc.pages}"
            )
        elif cat == "has_doi":
            lines.append(f"  -> doi=`{pc.doi}`")
        else:
            lines.append(f"  -> (year={pc.year}, title=`{pc.title[:50]}`)")
        lines.append("")
    if len(rows) > 5:
        lines.append(f"  *...and {len(rows)-5} more.*")
        lines.append("")

# -----------------------------------------------------------------------
# Full malformed list (to help diagnose parser gaps)
# -----------------------------------------------------------------------

if results_by_cat["malformed"]:
    lines.append("## All Malformed Strings")
    lines.append("")
    lines.append("| Task | Ref key | String (truncated) |")
    lines.append("|---|---|---|")
    for (tid, rk, s, pc) in results_by_cat["malformed"]:
        short = s[:100].replace("|", "\\|") if s else ""
        lines.append(f"| {tid} | {rk} | `{short}` |")
    lines.append("")

# -----------------------------------------------------------------------
# Write report
# -----------------------------------------------------------------------

report_text = "\n".join(lines)
with open(REPORT_FILE, "w", encoding="utf-8") as fh:
    fh.write(report_text)

print(f"Report written to: {REPORT_FILE}")
print()
print("Category breakdown:")
for cat in CATEGORIES:
    n = len(results_by_cat[cat])
    print(f"  {cat:20s}: {n:4d}  ({100.0*n/total:.1f}%)" if total else f"  {cat}: {n}")
print()
if not threshold_ok:
    print("ACTION REQUIRED: malformed rate exceeds 5%. Fix parse_citation_string.py before continuing.")
    sys.exit(1)
else:
    print("Malformed rate is within threshold. Ready for Phase 4 (enrichment).")
