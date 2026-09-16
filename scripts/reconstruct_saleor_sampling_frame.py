#!/usr/bin/env python3
"""Reconstruct the Saleor Stage-2 sampling frame (zero scientific calls).

Generalizes the frozen djangoCMS scientific builder to Saleor by overriding
ONLY the repository-specific constant `miner.PRODUCTION_ROOTS` (("cms",
"menus") -> ("saleor",)) at import. This is a config adapter, NOT a rule
change: eligibility, leakage barrier, dedup (R1/R2/R3), selection and split
rules are unchanged.

Anchor: the pinned snapshot HEAD 2c48391b652c26ce4f27a53d6532d4c873306af0
(matches benchmark_data/repository_profiles/saleor.yaml version 3.23.0).

Outputs:
- research/transparency/saleor_sampling_frame_reconstructed.json
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.real_commits import miner, scientific  # noqa: E402

# Config adapter (repo identity only; rules unchanged).
miner.PRODUCTION_ROOTS = ("saleor",)

CACHE_DIR = _PROJECT_DIR / "dist" / "pilot-repo-cache" / "saleor"
ANCHOR = "2c48391b652c26ce4f27a53d6532d4c873306af0"
WINDOW = scientific.SCIENTIFIC_WINDOW  # 6000, same as djangoCMS
OUT = _PROJECT_DIR / "research" / "transparency" / "saleor_sampling_frame_reconstructed.json"


def main() -> int:
    if not (CACHE_DIR / ".git").exists():
        print("SALEOR_CACHE_MISSING", CACHE_DIR)
        return 2
    shallow = (
        _PROJECT_DIR / "dist" / "pilot-repo-cache" / "saleor"
    )
    import subprocess

    is_shallow = subprocess.run(
        ["git", "-C", str(shallow), "rev-parse", "--is-shallow-repository"],
        capture_output=True, text=True,
    ).stdout.strip()
    if is_shallow != "false":
        print("SALEOR_CACHE_STILL_SHALLOW")
        return 2

    candidates, exclusion_counts = scientific.enumerate_scientific_candidates(
        CACHE_DIR, ANCHOR, window=WINDOW, miner_dev_targets=frozenset()
    )
    kept, adjudication = scientific.deduplicate_candidates(candidates)

    def _dist(vals):
        c = Counter(vals)
        return {str(k): v for k, v in sorted(c.items(), key=lambda kv: str(kv[0]))}

    frame: dict[str, Any] = {
        "repo": "saleor",
        "anchor": ANCHOR,
        "window": WINDOW,
        "adapter": "miner.PRODUCTION_ROOTS=('saleor',); rules unchanged",
        "funnel": {
            "window_scanned": WINDOW,
            "eligible_after_filters": len(candidates),
            "after_r1_r2": len(candidates)
            - sum(1 for a in adjudication if a["rule"] in ("R1_exact_proxy_set", "R2_shared_pr_reference")),
            "after_r3": len(kept),
        },
        "exclusion_counts": dict(sorted(exclusion_counts.items())),
        "independent_eligible_pool": {"n": len(kept), "case_ids": [miner.make_case_id(c["sha"]) for c in kept]},
        "year_distribution_eligible": _dist(c["year"] for c in candidates),
        "year_distribution_independent": _dist(c["year"] for c in kept),
        "proxy_size_distribution_eligible": _dist(c["proxy_count"] for c in candidates),
        "proxy_size_distribution_independent": _dist(c["proxy_count"] for c in kept),
        "change_type_distribution_independent": _dist(c["change_type"] for c in kept),
        "note": "ZERO scientific LLM calls; data-construction only.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(frame, indent=2), encoding="utf-8")

    print("funnel", json.dumps(frame["funnel"]))
    print("independent_eligible", len(kept))
    print("years", json.dumps(frame["year_distribution_independent"]))
    print("proxy", json.dumps(frame["proxy_size_distribution_independent"]))
    print("output", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
