#!/usr/bin/env python3
"""Materialize RealCommitImpactDataset-v2 case bundles from the frozen split proposal.

Deterministic, ZERO API. Builds public (parent-only) + hidden (observed proxy)
bundles for the V2 DEV_TRAIN + DEV_VALIDATION cases selected by
research/transparency/v2_split_proposal.json, using the frozen scientific
builder + miner.build_case against the pinned djangocms cache.

Does NOT alter v1. Does NOT touch INTERNAL_TEST / RESERVE / LEGACY_EXPOSED_V1.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.real_commits import miner, scientific  # noqa: E402

CACHE_DIR = _PROJECT_DIR / "dist" / "real-commit-cache" / "djangocms"
ANCHOR = miner.DJANGOCMS_ANCHOR_COMMIT
SPLIT = _PROJECT_DIR / "research" / "transparency" / "v2_split_proposal.json"
OUTPUT_DIR = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_v2"
CREATED_UTC = "2026-09-16T00:00:00+00:00"


def main() -> int:
    proposal = json.loads(SPLIT.read_text(encoding="utf-8"))
    assignment = proposal["assignment"]
    dev_roles = ("DEV_TRAIN", "DEV_VALIDATION")
    dev_ids = [cid for cid, role in assignment.items() if role in dev_roles]
    dev_ids.sort()
    print("V2 dev cases to build:", len(dev_ids))

    miner_dev = json.loads(
        (_PROJECT_DIR / "benchmark_data" / "real_commit_impact_v1" / "miner_dev_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    miner_dev_targets = frozenset(m["target_commit"] for m in miner_dev["cases"])

    candidates, _ = scientific.enumerate_scientific_candidates(
        CACHE_DIR, ANCHOR, window=scientific.SCIENTIFIC_WINDOW, miner_dev_targets=miner_dev_targets
    )
    kept, _ = scientific.deduplicate_candidates(candidates)
    by_cid = {miner.make_case_id(c["sha"]): c for c in kept}

    missing = [cid for cid in dev_ids if cid not in by_cid]
    if missing:
        print("MISSING_CASES", missing)
        return 2

    scientific_dir = OUTPUT_DIR / "scientific"
    scientific_dir.mkdir(parents=True, exist_ok=True)

    built = 0
    for cid in dev_ids:
        c = by_cid[cid]
        miner.build_case(
            cache_dir=CACHE_DIR,
            case_id=cid,
            target=c["sha"],
            parent=c["parent"],
            name_status=c["status"],
            eligibility=c["eligibility"],
            output_dir=scientific_dir,
            created_utc=CREATED_UTC,
            partition_role="SCIENTIFIC",
            split=assignment[cid],
        )
        built += 1

    records = []
    for cid in dev_ids:
        manifest = json.loads(
            (scientific_dir / cid / "case_manifest.json").read_text(encoding="utf-8")
        )
        records.append(manifest["record"])

    v2_manifest: dict[str, Any] = {
        "schema_version": "v1",
        "dataset_version": "v2",
        "repository": "djangocms",
        "anchor_commit": ANCHOR,
        "window": scientific.SCIENTIFIC_WINDOW,
        "split_proposal_source": str(SPLIT),
        "split_seed": proposal["seed"],
        "created_utc": CREATED_UTC,
        "roles_built": list(dev_roles),
        "legacy_exposed_v1_excluded": True,
        "case_ids": dev_ids,
        "cases": records,
    }
    v2_manifest["canonical_manifest_sha256"] = scientific.compute_canonical_dataset_manifest_hash(v2_manifest)
    manifest_path = OUTPUT_DIR / "v2_development_manifest.json"
    manifest_path.write_text(scientific.canonical_json(v2_manifest), encoding="utf-8")

    split_freeze = {
        "schema_version": "v1",
        "seed": proposal["seed"],
        "roles_built": list(dev_roles),
        "assignment": {cid: assignment[cid] for cid in dev_ids},
        "source_proposal": str(SPLIT),
        "note": "INTERNAL_TEST + RESERVE never materialized/inferred; LEGACY_EXPOSED_V1 excluded",
    }
    split_freeze["canonical_split_freeze_sha256"] = scientific.sha256_json(split_freeze)
    (OUTPUT_DIR / "split_freeze_v2_development.json").write_text(
        scientific.canonical_json(split_freeze), encoding="utf-8"
    )

    print("built_cases", built)
    print("manifest_sha256", v2_manifest["canonical_manifest_sha256"][:16])
    print("output", OUTPUT_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
