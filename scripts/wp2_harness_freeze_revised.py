#!/usr/bin/env python3
"""WP-2 harness V2 REVISED freeze (C1-PERF-V2) - ZERO API.

Revised freeze after C1-PERF-V2: includes the finalized MAIN sweep runner and
the modified dry-run runner (uv dependency-cache volume + test-only PostgreSQL
durability settings), plus all relevant imported harness files. The original
freeze (harness_v2_freeze_2026-09-23.json) is preserved as superseded.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
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

OUT = (
    PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23"
    / "harness_v2_freeze_2026-09-23_REVISED.json"
)

HARNESS_FILES = (
    "src/benchmark/wp2/oracle_semantics_v2.py",
    "src/benchmark/wp2/provenance_schema_v2.py",
    "src/benchmark/wp2/era_resolver.py",
    "src/benchmark/wp2/linux_adapter.py",
    "src/benchmark/wp2/dev_split_v2.py",
    "src/benchmark/wp2/census_metadata_v2.py",
    "src/benchmark/wp2/p2p_inventory_v1.py",
    "src/benchmark/wp2/oracle_confirmation.py",
    "src/benchmark/wp2/environment_manager.py",
    "scripts/wp2_linux_dryrun.py",
    "scripts/wp2_linux_main_sweep.py",
    "scripts/wp2_linux_dev_sweep.py",
    "scripts/wp2_linux_main_orchestrator.py",
)


def blob_sha256(relpath: str) -> str:
    p = PROJECT / relpath
    if not p.exists():
        return "MISSING"
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    git_head = subprocess.run(
        ["git", "-C", str(PROJECT), "rev-parse", "HEAD"],
        capture_output=True, text=True, encoding="utf-8", check=False,
    ).stdout.strip()
    dirty = subprocess.run(
        ["git", "-C", str(PROJECT), "status", "--porcelain"],
        capture_output=True, text=True, encoding="utf-8", check=False,
    ).stdout.strip()
    bundle = "\n".join(f"{relpath}:{blob_sha256(relpath)}" for relpath in HARNESS_FILES)
    bundle_sha = hashlib.sha256(bundle.encode()).hexdigest()

    manifest = {
        "artifact": "wp2_harness_v2_freeze_REVISED",
        "date": "2026-09-23",
        "revision": "C1-PERF-V2",
        "supersedes": "harness_v2_freeze_2026-09-23.json (preserved)",
        "semantics_version": SEMANTICS_V2_VERSION,
        "provenance_schema": ORACLE_HARNESS_SCHEMA_VERSION,
        "harness_version": "wp2-linux-harness-v2-2026-09-23",
        "git_head": git_head,
        "git_dirty": bool(dirty),
        "test_patch_rule_sha256": TEST_PATH_RULE_SHA256,
        "classifier_bundle_sha256": bundle_sha,
        "harness_files": {rel: blob_sha256(rel) for rel in HARNESS_FILES},
        "era_images": {spec.era_key: spec.base_image for spec in ERA_TABLE.values()},
        "era_image_digests": {spec.era_key: spec.image_digest for spec in ERA_TABLE.values()},
        "service_images": {
            "postgres": "postgres:15-alpine",
            "postgres_digest": "sha256:f7d23353e1b15400d22ebe31189f4d314b87a4c129cc400c8c2d8d4ca127bf81",
            "redis": "redis:7-alpine",
            "redis_digest": "sha256:858f009f9709ce576febc734aa78b8f6d624b82571f9ddb6bda4377c833b3499",
        },
        "python_versions": {spec.era_key: spec.python_version for spec in ERA_TABLE.values()},
        "installers": {spec.era_key: spec.installer_version for spec in ERA_TABLE.values()},
        "postgres_test_settings": {
            "fsync": "off",
            "synchronous_commit": "off",
            "full_page_writes": "off",
            "note": "disposable per-(task,state) test databases only; recorded per amendment D/C1-PERF-V2",
        },
        "uv_cache_policy": {
            "volume": "wp2-uv-cache",
            "policy": (
                "persistent uv dependency-cache volume mounted into task "
                "containers; same resolved wheels (no version drift), no "
                "silent dependency fallback"
            ),
        },
        "execution": {"workers": 1, "early_exit": "DISABLED", "stability": "3 target + 3 parent runs"},
        "filesystem_identity": "WSL Ubuntu-24.04 ext4 (/opt/wp2_v2); historical checkouts NOT NTFS-backed",
        "b3_equivalence": {
            "status": "PASS 5/5",
            "median_speedup": 1.52,
            "weighted_speedup": 1.52,
            "max_speedup": 2.13,
            "task_results": "baseline vs optimized classifications MATCH on all 5 frozen B3 tasks",
        },
        "eta_before_after": {
            "C2_before_hours": [27.0, 62.0],
            "C2_typical_before_hours": 46.0,
            "C2_after_hours": [9.0, 37.0],
            "C2_typical_after_hours": 20.0,
            "C4_after_hours": [5.0, 19.0],
            "C4_typical_after_hours": 10.0,
        },
        "no_provenance_field_none": True,
        "provenance_note": (
            "C2 MAIN 220 records record classifier_bundle_sha256=b11374fe "
            "(the original pre-optimization freeze hash hardcoded by the C2 "
            "runner). The bundle actually executed at C2 run time (era-key "
            "fix + uv-cache/PostgreSQL optimization, 5/5 B3-equivalence PASS) "
            "is captured by the revised freeze. The classifier-semantics "
            "files (oracle_semantics_v2.py, oracle_confirmation.py, "
            "provenance_schema_v2.py) are byte-identical across freeze "
            "revisions, so no semantic harness versions are mixed. "
            "C4's 4 existing records recorded b5074bff (the freeze current "
            "when they ran); this manifest's current bundle hash reflects the "
            "orchestration-only orchestrator fix. A runner-hardcoded bundle "
            "hash is self-referential and is a KNOWN provenance-hardening "
            "item to resolve when the C4 persistence change is adopted "
            "(record the freeze-manifest hash, not a runner hardcode)."
        ),
        "status": "FROZEN",
    }
    OUT.write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
    print("classifier_bundle_sha256:", bundle_sha)
    print("git_head:", git_head, "dirty:", bool(dirty))
    print("wrote", OUT.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
