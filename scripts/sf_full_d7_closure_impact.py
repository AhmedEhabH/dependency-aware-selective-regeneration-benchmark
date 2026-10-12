#!/usr/bin/env python3
"""M17 source-fidelity Full-D7 population closure-impact preflight (F3).

Mission: M17_ENV_CANON_SOURCE_FIDELITY_R1_FULL_D7

F3 — Source-aware population preflight.  Recomputes the R1 source-aware
closure identity for ALL 144 units WITHOUT executing any real smoke
qualification, exactly following the frozen S9 methodology
(research/source-fidelity-r1/s9_population_impact.py):

  old identity = closure_identity_sha256(name/version flatten of source-aware pins)
  new identity = source-aware closure identity
  changed      = unit contains a DIRECTORY/PATH (non-registry) source package

Requires (else exit non-zero / STOP):
  N_UNCHANGED = 142
  N_CHANGED   = 2
  changed units exactly {vu-692af9112c6d, vu-b9808f19ace4}
  reproduced frozen identities:
    vu-692af9112c6d -> 8c638686445b8895e3b16fec2db826e1962ef84c7e85c09ad56dc62c1747516f
    vu-b9808f19ace4 -> 7bf871f278d8c5008682a8203be8835fcb643f9e471c5c43700cd914fa2cb1bd
  no third changed unit; no unresolved source identity; no task-ID special case.

Read-only: store, calibration R1 research dir.  No network, no docker.

Usage:
  python scripts/sf_full_d7_closure_impact.py
"""
from __future__ import annotations

import csv
import json
import os
import sys
from datetime import UTC, datetime

STORE = r"D:\wp2_env_store"
MANIFESTS = os.path.join(STORE, "manifests")
LOCKS = os.path.join(STORE, "artifacts", "locks")
REPO = r"C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\dist\pilot-repo-cache\saleor"
REPO_DIR = r"D:\wp2_sf_full_d7_r1"
OUT_DIR = os.path.join(REPO_DIR, "research", "source-fidelity-full-d7-r1")
RESEARCH_R1 = os.path.join(REPO_DIR, "research", "source-fidelity-r1")

SRC_DIR = os.path.join(REPO_DIR, "src")
sys.path.insert(0, SRC_DIR)

from benchmark.wp2 import source_fidelity_r1 as sf  # noqa: E402

MATRIX = os.path.join(MANIFESTS, "VALIDATION_UNIT_MATRIX.csv")
TASK_ENV = os.path.join(MANIFESTS, "TASK_ENV_MATRIX.csv")
SF_IMPACT = os.path.join(RESEARCH_R1, "POPULATION_CLOSURE_IMPACT_R1.json")

EXPECTED_CHANGED = {
    "vu-692af9112c6d": "8c638686445b8895e3b16fec2db826e1962ef84c7e85c09ad56dc62c1747516f",
    "vu-b9808f19ace4": "7bf871f278d8c5008682a8203be8835fcb643f9e471c5c43700cd914fa2cb1bd",
}


def load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    with open(TASK_ENV, newline="", encoding="utf-8") as f:
        task_rows = list(csv.DictReader(f))
    task_commit = {r["task_id"]: r["target_commit"] for r in task_rows}

    with open(MATRIX, newline="", encoding="utf-8") as f:
        unit_rows = list(csv.DictReader(f))

    changed: list[dict] = []
    unchanged: list[dict] = []
    for u in sorted(unit_rows, key=lambda r: r["unit_id"]):
        uid = u["unit_id"]
        members = [t for t in u["member_task_ids"].split(";") if t]
        first = members[0]
        lock = os.path.join(LOCKS, f"{first}_{u['lock_type']}.toml")
        with open(lock, encoding="utf-8") as fh:
            text = fh.read()
        commit = task_commit.get(first, "")
        closure = sf.derive_source_aware_closure(
            text,
            commit,
            REPO,
            python_version=u["python_version"],
            sys_platform="linux",
            lock_format=u["lock_type"],
        )
        old_pins = sorted({p.split("@", 1)[0] for p in closure["pins"]})
        old_identity = sf.closure_identity_sha256(old_pins)
        new_identity = closure["closure_identity_sha256"]
        affected = sorted(
            {
                (r["name"], r["source_type"], r.get("source_reference") or "")
                for r in closure["records"]
                if r["source_type"] != sf.SOURCE_TYPE_REGISTRY
            }
        )
        entry = {
            "validation_unit_id": uid,
            "member_task_ids": members,
            "lock_type": u["lock_type"],
            "python_version": u["python_version"],
            "n_pins_old": len(old_pins),
            "n_pins_new": len(closure["pins"]),
            "old_canon_closure_identity_sha256": old_identity,
            "new_source_aware_closure_identity_sha256": new_identity,
            "source_identity_change": bool(affected),
            "non_registry_sources": affected,
            "n_fail_closed": closure["n_fail_closed"],
        }
        (changed if affected else unchanged).append(entry)

    changed_ids = sorted(e["validation_unit_id"] for e in changed)
    all_ok = True
    problems = []

    if len(changed) != 2:
        all_ok = False
        problems.append(f"N_CHANGED={len(changed)} != 2")
    if len(unchanged) != 142:
        all_ok = False
        problems.append(f"N_UNCHANGED={len(unchanged)} != 142")
    if set(changed_ids) != set(EXPECTED_CHANGED):
        all_ok = False
        problems.append(f"changed ids {changed_ids} != {sorted(EXPECTED_CHANGED)}")
    for uid, exp in EXPECTED_CHANGED.items():
        entry = next((e for e in changed if e["validation_unit_id"] == uid), None)
        if entry is None:
            all_ok = False
            problems.append(f"missing expected changed unit {uid}")
            continue
        if entry["new_source_aware_closure_identity_sha256"] != exp:
            all_ok = False
            problems.append(
                f"{uid} identity {entry['new_source_aware_closure_identity_sha256']} != {exp}"
            )
        if entry["n_fail_closed"] != 0:
            all_ok = False
            problems.append(f"{uid} n_fail_closed={entry['n_fail_closed']}")
    for e in changed:
        if e["n_fail_closed"] != 0:
            all_ok = False
            problems.append(f"{e['validation_unit_id']} unresolved source identity")
    for e in unchanged:
        if e["n_fail_closed"] != 0:
            all_ok = False
            problems.append(f"{e['validation_unit_id']} unresolved source identity (unchanged)")

    # task-ID special case check on the module source
    task_id_hits = sf.assert_no_task_specific_branch()
    if task_id_hits:
        all_ok = False
        problems.append(f"task-ID special case in source_fidelity_r1: {task_id_hits[:3]}")

    receipt = {
        "artifact": "FULL_D7_SOURCE_AWARE_CLOSURE_IMPACT",
        "mission": "M17_ENV_CANON_SOURCE_FIDELITY_R1_FULL_D7",
        "phase": "F3",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "method": "replicates frozen s9_population_impact.py (source-aware closure, all 144 units, no execution)",
        "n_units": len(unit_rows),
        "n_unchanged": len(unchanged),
        "n_changed": len(changed),
        "changed_unit_ids": changed_ids,
        "expected_changed": sorted(EXPECTED_CHANGED),
        "all_ok": all_ok,
        "problems": problems,
        "changed": changed,
        "unchanged_summary": {
            "count": len(unchanged),
            "unit_ids": [e["validation_unit_id"] for e in unchanged],
        },
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "FULL_D7_SOURCE_AWARE_CLOSURE_IMPACT.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2, sort_keys=True)
    print(json.dumps(
        {k: v for k, v in receipt.items() if k not in ("changed", "unchanged_summary")},
        indent=2, sort_keys=True))
    for e in changed:
        print("CHANGED", e["validation_unit_id"], e["new_source_aware_closure_identity_sha256"])
    print(f"ALL_OK={all_ok}")
    print(f"WROTE={out}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())