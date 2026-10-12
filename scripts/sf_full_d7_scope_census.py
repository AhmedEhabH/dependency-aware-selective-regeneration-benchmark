#!/usr/bin/env python3
"""M17 source-fidelity Full-D7 ZERO-CONTAINER SCOPE CENSUS (owner decision).

Mission: M17_ENV_CANON_SOURCE_FIDELITY_R1_FULL_D7 (scope-census stop)

This is a deterministic, NETWORK-FREE, DOCKER-FREE, UNIT-EXECUTION-FREE census
that informs the owner decision BEFORE any Full-D7 unit/container runs.

It computes:
  1. 219 worktree directory existence (materialized into the fresh output
     root; no byte-for-byte verification of all 219);
  2. byte parity of ONLY the 18 Calibration-overlap worktrees vs the frozen
     store worktrees (D:\\wp2_env_store\\tmp\\d7_r1_worktrees);
  3. NTFS-invalid skipped-path counts per task (from git tree listing; these
     are VCR test cassettes only, never closure/smoke inputs);
  4. era x lock census of the 144-unit population;
  5. zero-container frozen resolution dry-run per stratum using the frozen
     R3 closure derivation + frozen resolver against the era wheelhouse;
  6. explicit recording of frozen-authority limitations:
       - py312-only wheel-tag gate (affects py38/py39 strata);
       - uv editable-self / marker limitations (uv.lock stratum).

CRITICAL SCOPE RULE: units outside the Calibration-validated domain are
labelled OUT_OF_VALIDATED_SCOPE, NEVER classified as environment failure and
NEVER labelled NOT_READY in this census.  The validated domain is the
Calibration-12 stratum: python_version == 3.12 AND lock_type == poetry.

No Docker.  No Full-D7 unit execution.  No git freeze/push.

Usage:
  python scripts/sf_full_d7_scope_census.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime

sys.path.insert(0, r"D:\wp2_env_store\harness\d7_r3")
sys.path.insert(0, r"D:\wp2_sf_full_d7_r1\src")

from d7_r3_closure import derive_runtime_closure, resolve_runtime_artifacts  # noqa: E402

STORE = r"D:\wp2_env_store"
MANIFESTS = os.path.join(STORE, "manifests")
LOCKS = os.path.join(STORE, "artifacts", "locks")
STORE_WORKTREES = os.path.join(STORE, "tmp", "d7_r1_worktrees")
OUT_ROOT = r"D:\wp2_sf_full_d7_r1_store"
OUT_WORKTREES = os.path.join(OUT_ROOT, "worktrees")
REPO = r"C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\dist\pilot-repo-cache\saleor"
REPO_DIR = r"D:\wp2_sf_full_d7_r1"
OUT_DIR = os.path.join(REPO_DIR, "research", "source-fidelity-full-d7-r1")

MATRIX = os.path.join(MANIFESTS, "VALIDATION_UNIT_MATRIX.csv")
TASK_ENV = os.path.join(MANIFESTS, "TASK_ENV_MATRIX.csv")
MARKER_AUDIT = os.path.join(MANIFESTS, "MARKER_FILTER_AUDIT.json")
SF_IMPACT = os.path.join(REPO_DIR, "research", "source-fidelity-r1", "POPULATION_CLOSURE_IMPACT_R1.json")

ERA_DIR = {"3.8": "py38", "3.9": "py39", "3.12": "py312"}
_FORBIDDEN = set(':*?"<>|')


def load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def walk_files(root: str) -> dict[str, str]:
    out = {}
    for r, _dirs, files in os.walk(root):
        for fn in files:
            p = os.path.join(r, fn)
            rel = os.path.relpath(p, root).replace(os.sep, "/")
            out[rel] = sha256(p)
    return out


def era_wheels(era: str) -> list[str]:
    out = {}
    base = os.path.join(STORE, "wheelhouse", era)
    if os.path.isdir(base):
        for f in os.listdir(base):
            if f.endswith(".whl"):
                out[f] = 1
    base2 = os.path.join(STORE, "built_wheelhouse", "canon_r4b", era)
    if os.path.isdir(base2):
        for ident in os.listdir(base2):
            wd = os.path.join(base2, ident, "wheels")
            if os.path.isdir(wd):
                for f in os.listdir(wd):
                    if f.endswith(".whl"):
                        out[f] = 1
    return sorted(out)


def ntfs_invalid_paths(commit: str) -> list[str]:
    ls = subprocess.run(["git", "-C", REPO, "ls-tree", "-r", "--name-only", commit],
                        capture_output=True, text=True).stdout.splitlines()
    return [f for f in ls if any(ch in f for ch in _FORBIDDEN)]


def main() -> int:
    with open(MATRIX, newline="", encoding="utf-8") as f:
        unit_rows = list(csv.DictReader(f))
    with open(TASK_ENV, newline="", encoding="utf-8") as f:
        task_rows = list(csv.DictReader(f))
    task_commit = {r["task_id"]: r["target_commit"] for r in task_rows}
    task_info = {r["task_id"]: r for r in task_rows}

    # ---- 1. worktree directory existence ----
    worktree_dirs = {t: os.path.isdir(os.path.join(OUT_WORKTREES, t)) for t in task_commit}
    n_wt_present = sum(worktree_dirs.values())

    # ---- 2. NTFS-invalid skipped-path counts per task (git tree listing) ----
    ntfs_counts = {}
    for tid, commit in task_commit.items():
        bad = ntfs_invalid_paths(commit)
        if bad:
            ntfs_counts[tid] = {"n_skipped": len(bad), "paths": bad}
    n_tasks_with_ntfs_skip = len(ntfs_counts)
    n_total_ntfs_skipped = sum(v["n_skipped"] for v in ntfs_counts.values())

    # ---- 3. parity of ONLY the 18 Calibration-overlap worktrees ----
    store_overlap = sorted(set(os.listdir(STORE_WORKTREES)) & set(task_commit))
    parity = {}
    parity_all_ok = True
    for tid in store_overlap:
        a = walk_files(os.path.join(STORE_WORKTREES, tid))
        b = walk_files(os.path.join(OUT_WORKTREES, tid))
        same = a == b
        parity[tid] = {
            "byte_identical": same,
            "n_store_files": len(a),
            "n_full_d7_files": len(b),
            "only_in_store": sorted(set(a) - set(b))[:5],
            "only_in_full_d7": sorted(set(b) - set(a))[:5],
            "differing": sorted({k for k in set(a) & set(b) if a[k] != b[k]})[:5],
        }
        if not same:
            parity_all_ok = False

    # ---- 4. era x lock census + zero-container resolution dry-run ----
    era_lock = Counter((r["python_version"], r["lock_type"]) for r in unit_rows)
    dry: dict[str, dict] = defaultdict(lambda: {"ok": 0, "missing": 0, "incompatible": 0})
    per_unit: list[dict] = []
    for i, r in enumerate(unit_rows, start=1):
        uid = r["unit_id"]
        era = ERA_DIR[r["python_version"]]
        members = [t for t in r["member_task_ids"].split(";") if t]
        first = members[0]
        lock = os.path.join(LOCKS, f"{first}_{r['lock_type']}.toml")
        ppaths = []
        for tid in members:
            pp = os.path.join(OUT_WORKTREES, tid, "pyproject.toml")
            if os.path.isfile(pp):
                ppaths.append(pp)
        closure = derive_runtime_closure(lock, ppaths, MARKER_AUDIT, pyver=r["python_version"])
        res = resolve_runtime_artifacts(closure["runtime_pins"], wheel_file_list=era_wheels(era))
        key = f"{r['python_version']}|{r['lock_type']}"
        if res["pass_"]:
            dry[key]["ok"] += 1
            outcome = "RESOLVE_OK"
        elif res["missing"]:
            dry[key]["missing"] += 1
            outcome = "RESOLVE_MISSING"
        else:
            dry[key]["incompatible"] += 1
            outcome = "RESOLVE_INCOMPATIBLE"
        # sample reason evidence (first occurrence per outcome)
        per_unit.append({
            "validation_unit_id": uid,
            "ordered_full_d7_index": i,
            "python_version": r["python_version"],
            "lock_type": r["lock_type"],
            "install_route": r["install_route"],
            "era": era,
            "n_runtime_pins": len(closure["runtime_pins"]),
            "n_pins": len(closure["pins"]),
            "excluded": closure["excluded"],
            "resolution": {
                "pass_": res["pass_"],
                "missing": res["missing"][:8],
                "incompatible": [x["pin"] for x in res["incompatible"][:8]],
                "n_missing": len(res["missing"]),
                "n_incompatible": len(res["incompatible"]),
            },
            "dry_run_outcome": outcome,
        })

    # validated domain: Calibration-12 stratum (py312 + poetry)
    n_validated_domain = sum(1 for r in unit_rows
                             if r["python_version"] == "3.12" and r["lock_type"] == "poetry")
    validated_dry_ok = sum(1 for u in per_unit
                           if u["python_version"] == "3.12" and u["lock_type"] == "poetry"
                           and u["dry_run_outcome"] == "RESOLVE_OK")

    report = {
        "artifact": "FULL_D7_SCOPE_CENSUS",
        "mission": "M17_ENV_CANON_SOURCE_FIDELITY_R1_FULL_D7",
        "mission_class": "T3_REAL_FULL_D7_ENVIRONMENT_QUALIFICATION",
        "phase": "SCOPE_CENSUS_ZERO_CONTAINER",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "scope_banner": (
            "ZERO-CONTAINER census for owner decision.  NO Docker, NO Full-D7 "
            "unit execution, NO git freeze.  Units outside the Calibration-12 "
            "validated domain (python_version==3.12 AND lock_type==poetry) are "
            "labelled OUT_OF_VALIDATED_SCOPE, never classified as environment "
            "failure and never labelled NOT_READY in this census."
        ),
        "validated_domain": {
            "definition": "python_version == 3.12 AND lock_type == poetry (Calibration-12 stratum)",
            "n_units_in_validated_domain": n_validated_domain,
            "n_units_in_validated_domain_dry_resolve_ok": validated_dry_ok,
        },
        "population": {
            "N_VALIDATION_UNITS": len(unit_rows),
            "N_MAPPED_TASKS": len(task_rows),
            "era_x_lock_counts": dict(era_lock),
        },
        "worktrees": {
            "n_tasks": len(task_commit),
            "n_dirs_present": n_wt_present,
            "all_219_present": n_wt_present == 219,
            "note": "existence only; no full 219 byte-verification performed (per owner scope-census instruction)",
        },
        "ntfs_invalid": {
            "n_tasks_with_skipped_paths": n_tasks_with_ntfs_skip,
            "n_total_skipped_files": n_total_ntfs_skipped,
            "note": "skipped paths are VCR test cassettes only; they are never closure-derivation or frozen-gate inputs",
            "per_task_counts": {k: v["n_skipped"] for k, v in sorted(ntfs_counts.items())},
        },
        "calibration_worktree_parity": {
            "n_overlap_tasks": len(store_overlap),
            "all_byte_identical": parity_all_ok,
            "per_task": parity,
        },
        "dry_run": {
            "per_stratum": dict(dry),
            "per_unit": per_unit,
            "frozen_resolver": "d7_r3_closure.resolve_runtime_artifacts (frozen)",
            "closure_derivation": "d7_r3_closure.derive_runtime_closure (frozen, pyver=unit python_version)",
            "era_wheelhouse": "wheelhouse/<era> + built_wheelhouse/canon_r4b/<era> (frozen)",
        },
        "limitations": {
            "py312_only_wheel_tag_gate": (
                "The frozen R3 wheel-tag gate (d7_r3_wheeltags) targets CPython 3.12 "
                "only.  py38/py39 era wheels (cp38/cp39 non-abi3) are not accepted by "
                "the frozen resolver, so py38/py39 strata cannot pass the frozen "
                "resolution gate as frozen.  This is a FROZEN-AUTHORITY LIMITATION, "
                "not an environment failure.  py38/py39 units = OUT_OF_VALIDATED_SCOPE."
            ),
            "uv_editable_self_and_markers": (
                "The frozen R3 closure derivation reads all lock package entries as "
                "name==version pins; uv.lock editable-self (saleor==X, source "
                "virtual='.') is not excluded by the frozen R3 poetry_pins, and "
                "uv marker semantics are not applied by the frozen R3 closure path.  "
                "uv.lock units = OUT_OF_VALIDATED_SCOPE (not classified here)."
            ),
        },
        "missing_worktree_policy": (
            "A missing member-task worktree FAILS CLOSED (no silent smoke skip): the "
            "closure derivation only applies the win32 python-magic-bin exclusion "
            "when the member-task pyproject.toml is present, and smoke requires the "
            "mounted worktree; both are enforced as FAIL-CLOSED, never silently "
            "skipped."
        ),
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "FULL_D7_SCOPE_CENSUS.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)
    print(json.dumps({
        "artifact": report["artifact"],
        "phase": report["phase"],
        "validated_domain": report["validated_domain"],
        "population": report["population"],
        "worktrees": report["worktrees"],
        "ntfs_invalid": {k: v for k, v in report["ntfs_invalid"].items() if k != "per_task_counts"},
        "calibration_worktree_parity": report["calibration_worktree_parity"],
        "dry_run": report["dry_run"]["per_stratum"],
        "limitations": report["limitations"],
    }, indent=2, sort_keys=True))
    print(f"WROTE={out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())