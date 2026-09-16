#!/usr/bin/env python3
"""Build Saleor Stage-2 case bundles + split freeze (ZERO scientific model calls).

Uses the frozen M4A miner/build_case machinery with the Saleor config adapter
(miner.PRODUCTION_ROOTS = ("saleor",)) — no rule change. Builds DEVELOPMENT
bundles first; TEST and RESERVE are metadata-only manifests (scientific
outcomes are never exposed to method-development code).

For every bundle:
- parent commit pinned; visible intent; candidate universe; production-file
  rules; hidden observed-change proxy stored separately; graph-capability
  metadata; history-capability metadata; SHA-256.

Outputs:
- benchmark_data/real_commit_impact_saleor/ (scientific/<case_id>/ bundles)
- benchmark_data/real_commit_impact_saleor/saleor_development_manifest.json
- benchmark_data/real_commit_impact_saleor/split_freeze_saleor.json
- reports/SALEOR_CASE_BUNDLE_BUILD_REPORT.md
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.real_commits import miner, scientific  # noqa: E402

CACHE_DIR = _PROJECT_DIR / "dist" / "pilot-repo-cache" / "saleor"
ANCHOR = "2c48391b652c26ce4f27a53d6532d4c873306af0"
META = _PROJECT_DIR / "research" / "transparency" / "saleor_candidate_metadata.json"
SPLIT = _PROJECT_DIR / "research" / "transparency" / "saleor_split_proposal.json"
OUTPUT_DIR = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor"
CREATED_UTC = "2026-09-17T00:00:00+00:00"


def _sha(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def main() -> int:
    miner.PRODUCTION_ROOTS = ("saleor",)
    meta = json.loads(META.read_text(encoding="utf-8"))
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    assignment = {
        cid: role
        for role, per in split["per_role"].items()
        for cid in per["case_ids"]
    }
    # Rebuild eligibility objects (enumerate is expensive; the metadata file has
    # eligibility already — but build_case needs the full eligibility dict).
    # We stored eligibility; reconstruct the exact structure build_case expects.
    dev_roles = ("DEV_TRAIN", "DEV_VALIDATION")
    dev_ids = sorted(cid for cid, role in assignment.items() if role in dev_roles)
    print("Saleor DEVELOPMENT cases to build:", len(dev_ids))

    scientific_dir = OUTPUT_DIR / "scientific"
    scientific_dir.mkdir(parents=True, exist_ok=True)
    built = 0
    skipped = []
    for cid in dev_ids:
        c = meta.get(cid)
        if not c:
            skipped.append(cid)
            continue
        # Reconstruct eligibility payload with the fields build_case needs.
        elig = c["eligibility"]
        if not elig.get("proxy_paths"):
            skipped.append(cid)
            continue
        try:
            miner.build_case(
                cache_dir=CACHE_DIR,
                case_id=cid,
                target=c["sha"],
                parent=c["parent"],
                name_status=c["status"],
                eligibility=elig,
                output_dir=scientific_dir,
                created_utc=CREATED_UTC,
                partition_role="SCIENTIFIC",
                split=assignment[cid],
            )
            built += 1
        except Exception as exc:
            skipped.append(f"{cid}: {type(exc).__name__} {str(exc)[:80]}")

    # Development manifest
    records = []
    for cid in dev_ids:
        mpath = scientific_dir / cid / "case_manifest.json"
        if mpath.is_file():
            records.append(json.loads(mpath.read_text(encoding="utf-8"))["record"])
    dev_manifest: dict[str, Any] = {
        "schema_version": "v1",
        "dataset_version": "saleor-v1",
        "repository": "saleor",
        "anchor_commit": ANCHOR,
        "window": scientific.SCIENTIFIC_WINDOW,
        "roles_built": list(dev_roles),
        "case_ids": dev_ids,
        "cases": records,
        "config_adapter": "miner.PRODUCTION_ROOTS=('saleor',); rules unchanged",
    }
    dev_manifest["canonical_manifest_sha256"] = scientific.compute_canonical_dataset_manifest_hash(dev_manifest)
    (OUTPUT_DIR / "saleor_development_manifest.json").write_text(
        scientific.canonical_json(dev_manifest), encoding="utf-8"
    )

    # Split freeze (metadata-only; TEST/RESERVE not materialized, not inferred)
    split_freeze = {
        "schema_version": "v1",
        "seed": split["seed"],
        "roles": list(split["roles"]),
        "assignment": assignment,
        "per_role_sha256": {r: split["per_role"][r]["sha256"] for r in split["roles"]},
        "all_pool_sha256": split["all_pool_sha256"],
        "materialized_development": built,
        "note": "INTERNAL_TEST + RESERVE metadata-only; never materialized/inferred tonight.",
    }
    split_freeze["canonical_split_freeze_sha256"] = scientific.sha256_json(split_freeze)
    (OUTPUT_DIR / "split_freeze_saleor.json").write_text(scientific.canonical_json(split_freeze), encoding="utf-8")

    print("built", built, "skipped", len(skipped))
    print("manifest_sha256", dev_manifest["canonical_manifest_sha256"][:16])
    print("output", OUTPUT_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
