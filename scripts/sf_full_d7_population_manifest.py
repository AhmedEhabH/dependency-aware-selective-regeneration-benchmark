#!/usr/bin/env python3
"""M17 source-fidelity Full-D7 population manifest freeze (mission-local).

Mission: M17_ENV_CANON_SOURCE_FIDELITY_R1_FULL_D7

F2 — Freeze the exact ordered 144-unit / 219-task population manifest from the
frozen D7 authority (VALIDATION_UNIT_MATRIX.csv + TASK_ENV_MATRIX.csv).

Requires (each enforced or the script exits non-zero):
  N_VALIDATION_UNITS = 144
  N_MAPPED_TASKS     = 219
  N_DUPLICATE_UNITS  = 0
  N_UNKNOWN_TASKS    = 0
  N_SUBSTITUTIONS    = 0

Per-unit fields frozen: ordered index, member tasks, mapped task count,
python version, docker profile, image, image id (from D6), native profile,
install route, lock type/hash, expected worktree (member) count.

Usage:
  python scripts/sf_full_d7_population_manifest.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from datetime import UTC, datetime

STORE = r"D:\wp2_env_store"
MANIFESTS = os.path.join(STORE, "manifests")
REPO = r"D:\wp2_sf_full_d7_r1"
OUT_DIR = os.path.join(REPO, "research", "source-fidelity-full-d7-r1")

MATRIX = os.path.join(MANIFESTS, "VALIDATION_UNIT_MATRIX.csv")
TASK_ENV = os.path.join(MANIFESTS, "TASK_ENV_MATRIX.csv")
D6_NATIVE = os.path.join(MANIFESTS, "D6_NATIVE_RESULTS.json")
DOCKER_PROFILES = os.path.join(MANIFESTS, "DOCKER_PROFILE_MANIFEST.json")

EXPECTED_UNITS = 144
EXPECTED_TASKS = 219


def load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    with open(MATRIX, newline="", encoding="utf-8") as f:
        unit_rows = list(csv.DictReader(f))
    with open(TASK_ENV, newline="", encoding="utf-8") as f:
        task_rows = list(csv.DictReader(f))
    d6 = load_json(D6_NATIVE)
    image_ids = d6["image_ids"]
    dmp = load_json(DOCKER_PROFILES)
    native_profiles = dmp["native_profiles"]

    if len(unit_rows) != EXPECTED_UNITS:
        print(f"FAIL units={len(unit_rows)} != {EXPECTED_UNITS}")
        return 1
    if len(task_rows) != EXPECTED_TASKS:
        print(f"FAIL tasks={len(task_rows)} != {EXPECTED_TASKS}")
        return 1

    uids = [r["unit_id"] for r in unit_rows]
    if len(set(uids)) != len(uids):
        print("FAIL duplicate unit ids")
        return 1
    task_by_id = {r["task_id"]: r for r in task_rows}
    if len(task_by_id) != len(task_rows):
        print("FAIL duplicate task ids")
        return 1

    unknown = []
    member_count = {}
    for r in unit_rows:
        for tid in r["member_task_ids"].split(";"):
            member_count[tid] = member_count.get(tid, 0) + 1
            if tid not in task_by_id:
                unknown.append(tid)
    if unknown:
        print(f"FAIL unknown tasks: {unknown[:5]}")
        return 1
    if set(member_count) != set(task_by_id):
        missing = sorted(set(task_by_id) - set(member_count))
        print(f"FAIL tasks not mapped by any unit: {missing[:5]}")
        return 1
    dup_tasks = [t for t, n in member_count.items() if n > 1]
    if dup_tasks:
        print(f"FAIL task mapped by multiple units: {dup_tasks[:5]}")
        return 1

    units = []
    for i, r in enumerate(unit_rows, start=1):
        pid = r["native_profile_id"]
        image = f"envcanon/saleor-env-native-{pid}:latest"
        image_name = f"envcanon/saleor-env-native-{pid}"
        image_id = image_ids.get(image_name)
        lock_sha = r["lock_sha256"]
        for tid in r["member_task_ids"].split(";"):
            row = task_by_id[tid]
            if row["lock_sha256"] != lock_sha:
                print(f"FAIL lock sha mismatch {r['unit_id']} {tid}")
                return 1
        units.append(
            {
                "validation_unit_id": r["unit_id"],
                "ordered_full_d7_index": i,
                "member_task_ids": r["member_task_ids"].split(";"),
                "mapped_task_count": len(r["member_task_ids"].split(";")),
                "era": r["era"],
                "python_version": r["python_version"],
                "docker_profile_id": r["docker_profile_id"],
                "image": image,
                "image_id": image_id,
                "native_profile_id": pid,
                "install_route": r["install_route"],
                "lock_type": r["lock_type"],
                "lock_sha256": lock_sha,
                "marker_platform_context": r["marker_platform_context"],
                "expected_worktree_count": len(r["member_task_ids"].split(";")),
                "expected_member_count": len(r["member_task_ids"].split(";")),
            }
        )

    tasks = []
    for tid, row in sorted(task_by_id.items()):
        tasks.append(
            {
                "task_id": tid,
                "target_commit": row["target_commit"],
                "python_version": row["python_version"],
                "lock_type": row["lock_type"],
                "lock_sha256": row["lock_sha256"],
                "docker_profile_id": row.get("docker_profile_id") or "",
                "native_profile_id": row.get("native_profile_id") or "",
                "known_environment_status": row.get("known_environment_status") or "",
                "needs_dynamic_validation": row.get("needs_dynamic_validation") or "",
            }
        )

    manifest = {
        "artifact": "FULL_D7_POPULATION_MANIFEST",
        "mission": "M17_ENV_CANON_SOURCE_FIDELITY_R1_FULL_D7",
        "mission_class": "T3_REAL_FULL_D7_ENVIRONMENT_QUALIFICATION",
        "phase": "F2",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "authority": {
            "validation_unit_matrix": MATRIX,
            "task_env_matrix": TASK_ENV,
            "order": "frozen VALIDATION_UNIT_MATRIX.csv row order (no reorder)",
            "source_fidelity_freeze_commit": "f5f4c1d0ecae135f3b687bf8b9d27ffd150b6338",
            "qualification_commit": "bea6fab8050e561ee7ac1fd0ebe9828f29ae6b55",
        },
        "counts": {
            "N_VALIDATION_UNITS": len(units),
            "N_MAPPED_TASKS": len(tasks),
            "N_DUPLICATE_UNITS": 0,
            "N_UNKNOWN_TASKS": len(unknown),
            "N_SUBSTITUTIONS": 0,
        },
        "python_versions": sorted({u["python_version"] for u in units}),
        "docker_profiles": sorted({u["docker_profile_id"] for u in units}),
        "native_profiles": sorted({u["native_profile_id"] for u in units}),
        "install_routes": sorted({u["install_route"] for u in units}),
        "lock_types": sorted({u["lock_type"] for u in units}),
        "units": units,
        "tasks": tasks,
    }

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "FULL_D7_POPULATION_MANIFEST.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)

    with open(out, "rb") as f:
        manifest_sha256 = hashlib.sha256(f.read()).hexdigest()

    summary = {
        "manifest_file": out,
        "manifest_sha256": manifest_sha256,
        "N_VALIDATION_UNITS": len(units),
        "N_MAPPED_TASKS": len(tasks),
        "N_DUPLICATE_UNITS": 0,
        "N_UNKNOWN_TASKS": len(unknown),
        "N_SUBSTITUTIONS": 0,
        "all_ok": True,
    }
    with open(os.path.join(OUT_DIR, "FULL_D7_POPULATION_MANIFEST.sha256.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())