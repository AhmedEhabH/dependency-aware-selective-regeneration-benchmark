#!/usr/bin/env python3
"""Reconstruct the 329-case V2 sampling frame from the FROZEN scientific builder.

Deterministic, ZERO API. Uses the frozen `enumerate_scientific_candidates` +
`deduplicate_candidates` + `select_year_capped` from
src/benchmark/real_commits/scientific.py against the pinned djangocms cache.

Does NOT alter v1. Outputs a machine-readable frame summary:
- full funnel counts (verify 6000 -> 916 -> 334 -> 329 -> 40)
- per-case metadata for the independent eligible pool (329) where available
- year / proxy-size / candidate-universe distributions
- conservative intent type distribution
- legacy-exposed-v1 tagging for the 40 v1 cases

Outputs: research/transparency/v2_sampling_frame_reconstructed.json
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.real_commits import miner, scientific  # noqa: E402

CACHE_DIR = _PROJECT_DIR / "dist" / "real-commit-cache" / "djangocms"
ANCHOR = miner.DJANGOCMS_ANCHOR_COMMIT
OUT = _PROJECT_DIR / "research" / "transparency" / "v2_sampling_frame_reconstructed.json"


def main() -> int:
    if not (CACHE_DIR / ".git").exists():
        print("CACHE_MISSING", CACHE_DIR)
        return 2

    # Frozen MINER_DEV targets (excluded from scientific).
    miner_dev = json.loads(
        (_PROJECT_DIR / "benchmark_data" / "real_commit_impact_v1" / "miner_dev_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    miner_dev_targets = frozenset(m["target_commit"] for m in miner_dev["cases"])

    candidates, exclusion_counts = scientific.enumerate_scientific_candidates(
        CACHE_DIR, ANCHOR, window=scientific.SCIENTIFIC_WINDOW, miner_dev_targets=miner_dev_targets
    )
    kept, adjudication = scientific.deduplicate_candidates(candidates)
    selected = scientific.select_year_capped(kept, cap=scientific.YEAR_CAP, target=scientific.TARGET_CASES)

    eligible_ids = [scientific.miner.make_case_id(c["sha"]) for c in candidates]
    kept_ids = [scientific.miner.make_case_id(c["sha"]) for c in kept]
    selected_ids = [scientific.miner.make_case_id(c["sha"]) for c in selected]

    # v1 exposed case ids
    split = json.loads(
        (_PROJECT_DIR / "benchmark_data" / "real_commit_impact_v1" / "split_freeze.json").read_text(
            encoding="utf-8"
        )
    )
    v1_all = set(split["assignment"].keys())

    def _dist(vals):
        c = Counter(vals)
        return {str(k): v for k, v in sorted(c.items(), key=lambda kv: str(kv[0]))}

    frame = {
        "reconstructed_from": "frozen scientific builder + pinned djangocms cache (dist/real-commit-cache)",
        "anchor": ANCHOR,
        "window": scientific.SCIENTIFIC_WINDOW,
        "funnel": {
            "window_scanned": scientific.SCIENTIFIC_WINDOW,
            "eligible_after_filters": len(candidates),
            "after_r1_r2": len(candidates)
            - sum(1 for a in adjudication if a["rule"] in ("R1_exact_proxy_set", "R2_shared_pr_reference")),
            "after_r3": len(kept),
            "selected_v1": len(selected),
            "miner_dev_excluded": len(miner_dev_targets),
        },
        "exclusion_counts": dict(sorted(exclusion_counts.items())),
        "independent_eligible_pool": {
            "n": len(kept),
            "case_ids": kept_ids,
        },
        "eligible_pool": {
            "n": len(candidates),
            "case_ids": eligible_ids,
        },
        "selected_v1_case_ids": selected_ids,
        "year_distribution_eligible": _dist(c["year"] for c in candidates),
        "year_distribution_independent": _dist(c["year"] for c in kept),
        "proxy_size_distribution_eligible": _dist(c["proxy_count"] for c in candidates),
        "proxy_size_distribution_independent": _dist(c["proxy_count"] for c in kept),
        "candidate_universe_note": (
            "candidate_universe_size is computed only at case-build time for the 40 "
            "selected v1 cases (140-152); it is NOT persisted for the eligible pool "
            "in the frozen enumerator output (would require per-parent tree scans)."
        ),
        "change_type_distribution_eligible": _dist(c["change_type"] for c in candidates),
        "change_type_distribution_independent": _dist(c["change_type"] for c in kept),
        "legacy_exposed_v1": {
            "n": len(v1_all),
            "case_ids": sorted(v1_all),
            "note": "All 40 v1 cases are LEGACY_EXPOSED_V1; none usable as untouched V2 confirmatory test.",
        },
        "untouched_eligible_pool_excluding_v1": {
            "n": len([i for i in kept_ids if i not in v1_all]),
            "note": "independent eligible cases outside the exposed v1 40 (candidate V2 internal-test/reserve source)",
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(frame, indent=2), encoding="utf-8")

    print("funnel", json.dumps(frame["funnel"]))
    print("independent_eligible", frame["independent_eligible_pool"]["n"])
    print("untouched_excluding_v1", frame["untouched_eligible_pool_excluding_v1"]["n"])
    print("year_independent", json.dumps(frame["year_distribution_independent"]))
    print("proxy_independent", json.dumps(frame["proxy_size_distribution_independent"]))
    print("output", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
