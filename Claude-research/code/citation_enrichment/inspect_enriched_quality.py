"""
inspect_enriched_quality.py
Run from the workspace root on Windows:
    python outputs\inspect_enriched_quality.py

Reads task_details.enriched.json and reports:
  1. False positives — resolved authors don't overlap with citation_string authors
  2. Unresolved references
  3. HTML entities (&amp; etc.) in venue/journal fields
  4. doi=null but url has a doi.org link (verification-stripped DOIs)
  5. Overall statistics
"""
import json, re, unicodedata
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
ENRICHED   = SCRIPT_DIR / "task_details.enriched.json"

def surnames_from(text):
    """Extract lowercased surnames from an author string."""
    text = re.sub(r'\s*\[.*', '', text)   # strip [Updated: ...] etc.
    parts = re.split(r"[,&.]|\bet al\b|\band\b", text, flags=re.IGNORECASE)
    result = []
    for p in parts:
        p = p.strip()
        if len(p) > 2 and not re.match(r'^[A-Z]\.?$', p):
            w = unicodedata.normalize("NFKD", p.lower())
            if w:
                result.append(w)
    return result

def authors_overlap(cs_authors, res_authors):
    """Return True if any surname from cs_authors appears in res_authors."""
    if not cs_authors or not res_authors:
        return True   # can't compare; don't flag
    cs_sn = surnames_from(cs_authors)
    re_sn = surnames_from(res_authors)
    return any(s in r or r in s for s in cs_sn for r in re_sn)

with open(ENRICHED, encoding="utf-8") as fh:
    tasks = json.load(fh)

false_positives = []
unresolved      = []
html_entities   = []
doi_stripped    = []

total = 0
for task in tasks:
    tid = task.get("hedtsk_id", "?")
    for rk in ("key_references", "recent_references"):
        for ref in task.get(rk, []):
            if not isinstance(ref, dict):
                continue
            total += 1
            cs      = ref.get("citation_string", "")
            src     = ref.get("source", "")
            conf    = ref.get("confidence", "")
            res_au  = ref.get("authors", "")
            doi     = ref.get("doi")
            url     = ref.get("url", "")

            # Extract author portion of citation_string (before first '(YYYY)')
            cs_au_m = re.match(r'^([^(]+)\s*\(\d{4}', cs)
            cs_au   = cs_au_m.group(1).strip() if cs_au_m else ""

            # 1. False positives
            if src not in ("unresolved", "historical") and cs_au and res_au:
                if not authors_overlap(cs_au, res_au):
                    false_positives.append({
                        "task": tid, "ref_key": rk,
                        "cs_au": cs_au[:60], "res_au": res_au[:60],
                        "res_title": ref.get("title","")[:70],
                        "citation_string": cs[:90],
                    })

            # 2. Unresolved
            if src == "unresolved":
                unresolved.append({
                    "task": tid, "ref_key": rk, "citation_string": cs[:100],
                    "year": ref.get("year"),
                })

            # 3. HTML entities in venue/journal
            for field in ("venue", "journal"):
                v = ref.get(field) or ""
                if "&amp;" in v or "&#" in v or "&lt;" in v or "&gt;" in v:
                    html_entities.append({
                        "task": tid, "ref_key": rk, "field": field, "value": v,
                    })
                    break

            # 4. doi=null but url is a doi.org link (verification-stripped DOIs)
            if doi is None and url and url.startswith("https://doi.org/"):
                doi_stripped.append({
                    "task": tid, "ref_key": rk,
                    "inferred_doi": url.replace("https://doi.org/", ""),
                    "citation_string": cs[:80],
                })

# -----------------------------------------------------------------------
print("=" * 70)
print(f"Total references examined : {total}")
print(f"False positives detected  : {len(false_positives)}")
print(f"Unresolved                : {len(unresolved)}")
print(f"HTML entity venues        : {len(html_entities)}")
print(f"doi=null / url=doi.org    : {len(doi_stripped)}")
print("=" * 70)

if false_positives:
    print(f"\n--- FALSE POSITIVES ({len(false_positives)}) ---")
    for fp in false_positives:
        print(f"  [{fp['task']} / {fp['ref_key']}]")
        print(f"    CS  authors : {fp['cs_au']}")
        print(f"    RES authors : {fp['res_au']}")
        print(f"    RES title   : {fp['res_title']}")
        print(f"    CS          : {fp['citation_string']}")
        print()

if unresolved:
    print(f"\n--- UNRESOLVED ({len(unresolved)}) ---")
    for u in unresolved:
        print(f"  [{u['task']} / {u['ref_key']}]  year={u['year']}")
        print(f"    {u['citation_string']}")
        print()

if html_entities:
    print(f"\n--- HTML ENTITY VENUES ({len(html_entities)}) ---")
    for e in html_entities[:20]:
        print(f"  [{e['task']}] {e['field']} = {e['value']}")

if doi_stripped:
    print(f"\n--- DOI=NULL BUT URL IS DOI.ORG ({len(doi_stripped)}) ---")
    for d in doi_stripped[:20]:
        print(f"  doi: {d['inferred_doi']}")
        print(f"  cs : {d['citation_string']}")
        print()
