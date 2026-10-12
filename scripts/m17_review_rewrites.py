import csv
import sys

sys.stdout.reconfigure(encoding="utf-8")

with open(
    r"research/documentation-hygiene-r1/DOCUMENTATION_PROVENANCE_CENSUS.csv",
    encoding="utf-8",
    newline="",
) as fh:
    rows = list(csv.DictReader(fh))
for r in rows:
    if r["action"] == "REWRITE_RESEARCHER_CENTRIC":
        print(
            f"{r['path']}:{r['line']} [{r['matched_term']}] {r['context_excerpt']}"
        )
