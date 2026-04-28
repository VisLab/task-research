"""
fix_process_html_entities.py  —  decode &amp; etc. in process_details.json venue/journal fields.

Run from workspace root:
    python outputs\fix_process_html_entities.py
"""
import html, json
from pathlib import Path

WORKSPACE    = Path(__file__).parent.parent
PROCESS_FILE = WORKSPACE / "process_details.json"

with open(PROCESS_FILE, encoding="utf-8") as fh:
    data = json.load(fh)

fixed = 0
for process in data.get("processes", []):
    for ref_key in ("fundamental_references", "recent_references"):
        for ref in process.get(ref_key, []):
            for field in ("venue", "journal"):
                v = ref.get(field)
                if v and ("&amp;" in v or "&#" in v or "&lt;" in v or "&gt;" in v):
                    ref[field] = html.unescape(v)
                    fixed += 1

print(f"Fields unescaped: {fixed}")

with open(PROCESS_FILE, "w", encoding="utf-8") as fh:
    json.dump(data, fh, ensure_ascii=False, indent=2)
print(f"Written: {PROCESS_FILE}")
