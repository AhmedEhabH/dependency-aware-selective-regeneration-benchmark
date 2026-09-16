#!/usr/bin/env python3
"""Propose + hash the Saleor metadata-only split (Stage-2 ready-to-run).

Deterministic, metadata-only, ZERO API. Uses the reconstructed frame
(research/transparency/saleor_sampling_frame_reconstructed.json) which contains
the 1316 independent eligible case IDs and per-case year/proxy metadata.

Design (mirrors the djangoCMS V2 split):
- DEV_TRAIN 120, DEV_VALIDATION 30, INTERNAL_TEST 80, RESERVE = remainder.
- One seeded shuffle of the full pool, then consecutive blocks by role size.
- Frozen BEFORE any Saleor model result. INTERNAL_TEST/RESERVE untouched.

Output: research/transparency/saleor_split_proposal.json
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

from benchmark.real_commits import miner, scientific  # noqa: E402

FRAME = _PROJECT_DIR / "research" / "transparency" / "saleor_sampling_frame_reconstructed.json"
OUT = _PROJECT_DIR / "research" / "transparency" / "saleor_split_proposal.json"
CACHE_DIR = _PROJECT_DIR / "dist" / "pilot-repo-cache" / "saleor"
ANCHOR = "2c48391b652c26ce4f27a53d6532d4c873306af0"

SEED = 20260916
TARGETS = {"DEV_TRAIN": 120, "DEV_VALIDATION": 30, "INTERNAL_TEST": 80}
ROLE_ORDER = ["DEV_TRAIN", "DEV_VALIDATION", "INTERNAL_TEST", "RESERVE"]


def _sha(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _bucket(n: int) -> str:
    if n <= 2:
        return "small"
    if n <= 6:
        return "medium"
    return "large"


def main() -> int:
    frame = json.loads(FRAME.read_text(encoding="utf-8"))
    pool_ids = frame["independent_eligible_pool"]["case_ids"]
    pool = len(pool_ids)
    reserve = pool - sum(TARGETS.values())
    targets = {**TARGETS, "RESERVE": reserve}

    # Reconstruct per-case metadata (year/proxy) with the Saleor adapter.
    miner.PRODUCTION_ROOTS = ("saleor",)
    cands, _ = scientific.enumerate_scientific_candidates(
        CACHE_DIR, ANCHOR, window=scientific.SCIENTIFIC_WINDOW, miner_dev_targets=frozenset()
    )
    kept, _ = scientific.deduplicate_candidates(cands)
    meta = {}
    for c in kept:
        cid = miner.make_case_id(c["sha"])
        if cid not in set(pool_ids):
            continue
        meta[cid] = {
            "year": c["year"],
            "proxy_count": c["proxy_count"],
            "bucket": _bucket(c["proxy_count"]),
            "change_type": c["change_type"],
        }

    rng = random.Random(SEED)
    shuffled = list(pool_ids)
    rng.shuffle(shuffled)
    assignment: dict[str, str] = {}
    cursor = 0
    for role in ROLE_ORDER:
        for cid in shuffled[cursor : cursor + targets[role]]:
            assignment[cid] = role
        cursor += targets[role]

    per_role = {}
    for role in ROLE_ORDER:
        ids = sorted(c for c, r in assignment.items() if r == role)
        per_role[role] = {
            "count": len(ids),
            "case_ids": ids,
            "sha256": _sha(ids),
            "year_dist": dict(sorted(Counter(meta[i]["year"] for i in ids).items())),
            "bucket_dist": dict(sorted(Counter(meta[i]["bucket"] for i in ids).items())),
        }

    proposal = {
        "study_id": "saleor-stage2-v1",
        "protocol_version": "saleor-real-commit-v1",
        "seed": SEED,
        "anchor": ANCHOR,
        "frozen_before_any_model_result": True,
        "independent_eligible_pool": pool,
        "roles": ROLE_ORDER,
        "per_role": per_role,
        "all_pool_sha256": _sha(sorted(pool_ids)),
    }
    OUT.write_text(json.dumps(proposal, indent=2), encoding="utf-8")
    for role in ROLE_ORDER:
        m = per_role[role]
        print(role, m["count"], "years", json.dumps(m["year_dist"]))
    print("all_pool_sha256", proposal["all_pool_sha256"])
    print("output", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
