#!/usr/bin/env python3
"""Materialize djangoCMS V2 INTERNAL_TEST case bundles (frozen, ZERO API).

Authorized 2026-09-17 by Ahmed: open ONLY djangoCMS V2 INTERNAL_TEST (80
tasks) under the frozen V2 confirmatory protocol. This script builds the case
bundles deterministically from the pinned djangocms cache using the SAME frozen
builder as the 150 DEV bundles (scripts/build_v2_development_cases.py), but
for the INTERNAL_TEST role only. It NEVER touches RESERVE, Saleor INTERNAL_TEST,
or Saleor RESERVE.

The bundles contain the frozen public (parent-only) + hidden (observed proxy)
artifacts exactly as built by miner.build_case; this is the authorized opening
of the frozen INTERNAL_TEST data for the confirmatory run. No model call is
made here.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.real_commits import miner, scientific  # noqa: E402

CACHE_DIR = _PROJECT_DIR / "dist" / "real-commit-cache" / "djangocms"
ANCHOR = miner.DJANGOCMS_ANCHOR_COMMIT
SPLIT = _PROJECT_DIR / "research" / "transparency" / "v2_split_proposal.json"
OUTPUT_DIR = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_v2"
CREATED_UTC = "2026-09-17T00:00:00+00:00"


def main() -> int:
    proposal = json.loads(SPLIT.read_text(encoding="utf-8"))
    assignment = proposal["assignment"]
    internal_ids = [cid for cid, role in assignment.items() if role == "INTERNAL_TEST"]
    internal_ids.sort()
    print("INTERNAL_TEST cases to build:", len(internal_ids))
    if len(internal_ids) != 80:
        print("EXPECTED_80_GOT", len(internal_ids))
        return 2

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

    missing = [cid for cid in internal_ids if cid not in by_cid]
    if missing:
        print("MISSING_CASES", missing)
        return 2

    scientific_dir = OUTPUT_DIR / "scientific"
    scientific_dir.mkdir(parents=True, exist_ok=True)

    built = 0
    for cid in internal_ids:
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
    for cid in internal_ids:
        manifest = json.loads(
            (scientific_dir / cid / "case_manifest.json").read_text(encoding="utf-8")
        )
        records.append(manifest["record"])

    manifest: dict[str, object] = {
        "schema_version": "v1",
        "dataset_version": "v2",
        "repository": "djangocms",
        "anchor_commit": ANCHOR,
        "window": scientific.SCIENTIFIC_WINDOW,
        "split_proposal_source": str(SPLIT),
        "split_seed": proposal["seed"],
        "created_utc": CREATED_UTC,
        "roles_built": ["INTERNAL_TEST"],
        "legacy_exposed_v1_excluded": True,
        "authorization": "Ahmed explicit 2026-09-17: djangoCMS V2 INTERNAL_TEST only; RESERVE + Saleor sealed",
        "case_ids": internal_ids,
        "cases": records,
    }
    manifest["canonical_manifest_sha256"] = scientific.compute_canonical_dataset_manifest_hash(manifest)
    manifest_path = OUTPUT_DIR / "v2_internal_test_manifest.json"
    manifest_path.write_text(scientific.canonical_json(manifest), encoding="utf-8")

    print("built_cases", built)
    print("manifest_sha256", manifest["canonical_manifest_sha256"][:16])
    print("output", scientific_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
