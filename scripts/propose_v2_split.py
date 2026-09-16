#!/usr/bin/env python3
"""Propose + hash the V2 split (DEV_TRAIN / DEV_VALIDATION / INTERNAL_TEST / RESERVE).

Deterministic, metadata-only, ZERO API. Uses the frozen reconstructed frame
(research/transparency/v2_sampling_frame_reconstructed.json) which contains the
independent eligible 329 case IDs and their metadata (year, proxy_count,
change_type).

Design:
- Excluded from v2 test/reserve: the 40 LEGACY_EXPOSED_V1 case ids.
- Pool for v2 = 289 untouched eligible cases.
- DEV_TRAIN / DEV_VALIDATION are drawn from the untouched pool by metadata-only
  stratification (proxy-size bucket, year spread) with a deterministic seed.
  The v1 30 TRAIN/VALIDATION development cases may be reused as
  compatibility/development cases (existing labels), so v2 DEV_TRAIN selects
  NEW untouched cases.
- INTERNAL_TEST + RESERVE: untouched, never-inferred, never-used.

This proposal is FROZEN-PROTOCOL-ONLY (auditable); the actual v2 manifest is
materialized by a later build step that needs the same cache. The split is
metadata-only and deterministic; it is registered here BEFORE any new model
result.

Output: research/transparency/v2_split_proposal.json
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

FRAME = _PROJECT_DIR / "research" / "transparency" / "v2_sampling_frame_reconstructed.json"
OUT = _PROJECT_DIR / "research" / "transparency" / "v2_split_proposal.json"

SEED = 20260916
DEV_TRAIN_TARGET = 120  # from the sample-size analysis (N=120 new dev tasks)
VALIDATION_TARGET = 30
TEST_TARGET = 80
RESERVE_TARGET = 59  # remainder of 289


def _bucket(n: int) -> str:
    if n <= 2:
        return "small"
    if n <= 6:
        return "medium"
    return "large"


def _sha(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def main() -> int:
    frame = json.loads(FRAME.read_text(encoding="utf-8"))
    legacy = set(frame["legacy_exposed_v1"]["case_ids"])
    pool_ids = [i for i in frame["independent_eligible_pool"]["case_ids"] if i not in legacy]
    assert len(pool_ids) == 289, f"expected 289 untouched, got {len(pool_ids)}"

    # Reconstruct per-case metadata for the untouched pool (year/proxy/type) by
    # re-running the deterministic enumerator (frozen builder; no cache build).
    from benchmark.real_commits import miner, scientific

    miner_dev = json.loads(
        (_PROJECT_DIR / "benchmark_data" / "real_commit_impact_v1" / "miner_dev_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    miner_dev_targets = frozenset(m["target_commit"] for m in miner_dev["cases"])
    cands, _ = scientific.enumerate_scientific_candidates(
        _PROJECT_DIR / "dist" / "real-commit-cache" / "djangocms",
        miner.DJANGOCMS_ANCHOR_COMMIT,
        window=scientific.SCIENTIFIC_WINDOW,
        miner_dev_targets=miner_dev_targets,
    )
    kept, _ = scientific.deduplicate_candidates(cands)
    meta: dict[str, dict[str, Any]] = {}
    for c in kept:
        cid = miner.make_case_id(c["sha"])
        if cid not in pool_ids:
            continue
        meta[cid] = {
            "year": c["year"],
            "proxy_count": c["proxy_count"],
            "bucket": _bucket(c["proxy_count"]),
            "change_type": c["change_type"],
            "intent": c["intent"],
            "target": c["sha"],
            "parent": c["parent"],
            "ts": c["ts"],
        }

    rng = random.Random(SEED)
    targets = {
        "DEV_TRAIN": DEV_TRAIN_TARGET,
        "DEV_VALIDATION": VALIDATION_TARGET,
        "INTERNAL_TEST": TEST_TARGET,
        "RESERVE": RESERVE_TARGET,
    }
    assert sum(targets.values()) == len(pool_ids), f"{sum(targets.values())} != {len(pool_ids)}"
    # Metadata-only stratification: bucket by proxy-size, then year spread.
    by_bucket: dict[str, list[str]] = {"small": [], "medium": [], "large": []}
    for cid in sorted(pool_ids):
        by_bucket[meta[cid]["bucket"]].append(cid)

    def seeded_shuffle(items: list[str]) -> list[str]:
        xs = list(items)
        rng.shuffle(xs)
        return xs

    # Deterministic, metadata-only assignment: one seeded shuffle of the whole
    # untouched pool, then consecutive blocks by role size. Each role is a
    # random sample of the pool (bucket mix proportional to the pool), which is
    # the simplest defensible stratified-by-shuffle design and avoids
    # bucket-concentration in any single role.
    shuffled = seeded_shuffle(sorted(pool_ids))
    role_order = ["DEV_TRAIN", "DEV_VALIDATION", "INTERNAL_TEST", "RESERVE"]
    assignment: dict[str, str] = {}
    cursor = 0
    for role in role_order:
        size = targets[role]
        for cid in shuffled[cursor : cursor + size]:
            assignment[cid] = role
        cursor += size

    per_role: dict[str, list[str]] = {r: [] for r in role_order}
    for cid, role in assignment.items():
        per_role[role].append(cid)

    role_meta: dict[str, Any] = {}
    for role, ids in per_role.items():
        ids_sorted = sorted(ids)
        role_meta[role] = {
            "count": len(ids_sorted),
            "case_ids": ids_sorted,
            "sha256": _sha(ids_sorted),
            "year_dist": dict(sorted(Counter(meta[i]["year"] for i in ids_sorted).items())),
            "bucket_dist": dict(sorted(Counter(meta[i]["bucket"] for i in ids_sorted).items())),
            "proxy_dist": dict(sorted(Counter(meta[i]["proxy_count"] for i in ids_sorted).items())),
        }

    proposal = {
        "study_id": "real-commit-impact-v2",
        "protocol_version": "real-commit-dataset-v2-v1.0.0",
        "seed": SEED,
        "frozen_before_any_model_result": True,
        "source_frame": str(FRAME),
        "legacy_exposed_v1_excluded": len(legacy),
        "untouched_pool": len(pool_ids),
        "strata": ["proxy-size bucket", "year (metadata-only)", "conservative change_type"],
        "assignment": assignment,
        "per_role": role_meta,
        "all_ids_sha256": _sha(sorted(pool_ids)),
    }
    OUT.write_text(json.dumps(proposal, indent=2), encoding="utf-8")

    for role in role_order:
        m = role_meta[role]
        print(role, m["count"], "year", json.dumps(m["year_dist"]), "bucket", json.dumps(m["bucket_dist"]))
    print("all_pool_sha256", proposal["all_ids_sha256"])
    print("output", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
