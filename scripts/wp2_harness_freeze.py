#!/usr/bin/env python3
"""WP-2 harness V2 freeze manifest (C1) - ZERO API.

Frozen before the large rerun (Mission 07 §4 / amendment D): captures the
harness source content-hashes, era/service image digests, test-patch rule hash,
and substrate identity so that final V2 results never mix semantic harness
versions. No required provenance field may be None (amendment D).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

from benchmark.wp2.era_resolver import ERA_TABLE  # noqa: E402
from benchmark.wp2.oracle_semantics_v2 import (  # noqa: E402
    SEMANTICS_V2_VERSION,
    TEST_PATH_RULE_SHA256,
)
from benchmark.wp2.provenance_schema_v2 import ORACLE_HARNESS_SCHEMA_VERSION  # noqa: E402

OUT = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23" / "harness_v2_freeze_2026-09-23.json"

HARNESS_FILES = (
    "src/benchmark/wp2/oracle_semantics_v2.py",
    "src/benchmark/wp2/provenance_schema_v2.py",
    "src/benchmark/wp2/era_resolver.py",
    "src/benchmark/wp2/linux_adapter.py",
    "src/benchmark/wp2/dev_split_v2.py",
    "src/benchmark/wp2/census_metadata_v2.py",
    "src/benchmark/wp2/p2p_inventory_v1.py",
    "src/benchmark/wp2/oracle_confirmation.py",
    "scripts/wp2_linux_dryrun.py",
)


def blob_sha256(relpath: str) -> str:
    p = PROJECT / relpath
    if not p.exists():
        return "MISSING"
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    classifier_bundle = "\n".join(
        f"{relpath}:{blob_sha256(relpath)}" for relpath in HARNESS_FILES
    )
    classifier_bundle_sha256 = hashlib.sha256(classifier_bundle.encode()).hexdigest()
    era_digests = {spec.era_key: spec.image_digest for spec in ERA_TABLE.values()}
    era_images = {spec.era_key: spec.base_image for spec in ERA_TABLE.values()}

    manifest = {
        "artifact": "wp2_harness_v2_freeze",
        "date": "2026-09-23",
        "semantics_version": SEMANTICS_V2_VERSION,
        "provenance_schema": ORACLE_HARNESS_SCHEMA_VERSION,
        "harness_version": "wp2-linux-harness-v2-2026-09-23",
        "test_patch_rule_sha256": TEST_PATH_RULE_SHA256,
        "classifier_bundle_sha256": classifier_bundle_sha256,
        "harness_files": {rel: blob_sha256(rel) for rel in HARNESS_FILES},
        "era_images": era_images,
        "era_image_digests": era_digests,
        "service_images": {
            "postgres": "postgres:15-alpine",
            "postgres_digest": "sha256:f7d23353e1b15400d22ebe31189f4d314b87a4c129cc400c8c2d8d4ca127bf81",
            "redis": "redis:7-alpine",
            "redis_digest": "sha256:858f009f9709ce576febc734aa78b8f6d624b82571f9ddb6bda4377c833b3499",
        },
        "substrate": "WSL-local Docker Engine (Ubuntu-24.04, docker 29.1.3)",
        "no_provenance_field_none": True,
        "status": "FROZEN",
    }
    for spec in ERA_TABLE.values():
        if not spec.image_digest.startswith("sha256:"):
            raise SystemExit(f"era {spec.era_key} missing immutable digest")
    OUT.write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
    print("classifier_bundle_sha256:", classifier_bundle_sha256)
    print("test_patch_rule_sha256:", TEST_PATH_RULE_SHA256)
    print("wrote", OUT.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
