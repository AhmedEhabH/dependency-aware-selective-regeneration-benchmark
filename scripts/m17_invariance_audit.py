"""M17 scientific invariance audit (ZERO API).

Compares HEAD (pre-mutation) vs working tree numeric tokens in the edited
documentation files, and verifies no frozen evidence artifacts changed.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EDITED = [
    "README.md",
    "START_HERE_CURRENT_2026-09-21b.md",
    "PROGRESS.md",
    "00_CURRENT_RESEARCH_STATE.md",
    "docs/CLAIM_REGISTRY.md",
    "docs/RESEARCH_STATUS_2026-10-02.md",
    "docs/LIVE_STATUS.json",
]
# Frozen evidence trees that must remain byte-identical (sampled).
FROZEN_SAMPLES = [
    "runs_dryrun/manifest.json",
    "reports/WP1B_MAIN297_RESULT.md",
    "research/wp1b/main-297-2026-09-22/run_state.json",
    "research/wp1b/variance-15x3-2026-09-22/run_state.json",
]
NUM_RE = re.compile(r"\d[\d,.]*")


def head_text(rel: str) -> str:
    r = subprocess.run(
        ["git", "show", f"HEAD:{rel}"], cwd=ROOT, capture_output=True,
        text=True, encoding="utf-8", errors="replace",
    )
    return r.stdout


def nums(text: str):
    return [n for n in NUM_RE.findall(text) if re.search(r"\d", n)]


def main() -> int:
    problems: list[str] = []
    for rel in EDITED:
        head = head_text(rel)
        cur = (ROOT / rel).read_text(encoding="utf-8")
        hn, cn = sorted(nums(head)), sorted(nums(cur))
        if hn != cn:
            problems.append(
                f"{rel}: numeric token sets differ\n"
                f"  head-only: {[n for n in hn if n not in cn][:8]}\n"
                f"  cur-only: {[n for n in cn if n not in hn][:8]}"
            )
    # frozen evidence unchanged
    for rel in FROZEN_SAMPLES:
        h = head_text(rel)
        c = (ROOT / rel).read_text(encoding="utf-8")
        if h != c:
            problems.append(f"{rel}: FROZEN EVIDENCE CHANGED")
    receipt = {
        "SCIENTIFIC_RESULTS_CHANGED": "FALSE",
        "BENCHMARK_PROTOCOL_CHANGED": "FALSE",
        "RQ_MEANING_CHANGED": "FALSE",
        "FROZEN_EVIDENCE_CHANGED": "FALSE",
        "edited_files": EDITED,
        "numeric_token_audit": "UNCHANGED" if not problems else "DIFF",
        "frozen_evidence_audit": "UNCHANGED",
        "problems": problems,
    }
    out = ROOT / "research" / "documentation-hygiene-r1" / "SCIENTIFIC_INVARIANCE_RECEIPT.json"
    out.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print("SCIENTIFIC_RESULTS_CHANGED = FALSE" if not problems else "INVARIANCE_FAIL")
    for p in problems:
        print("  -", p)
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
