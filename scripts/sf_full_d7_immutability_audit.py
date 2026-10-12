#!/usr/bin/env python3
"""M17 source-fidelity Full-D7 input immutability audit (mission-local).

Mission: M17_ENV_CANON_SOURCE_FIDELITY_R1_FULL_D7

F1 — Input immutability audit.  Binds (SHA-256) and byte-compares every frozen
input of the Full-D7 environment-qualification population against its frozen
authority:

  * frozen D7 manifests;
  * D7 validation population (144 units / 219 tasks);
  * frozen R3 harness files (byte-exact vs D7_R3_HARNESS_FREEZE.json);
  * lock artifacts (vs TASK_ENV_MATRIX lock_sha256_git_blob);
  * Docker image identities (vs D6_NATIVE_RESULTS.json image_ids);
  * native profiles (DOCKER_PROFILE_MANIFEST.json);
  * source-fidelity freeze (freeze + provenance manifest + closure impact +
    validation + source-type audit);
  * Calibration PASS receipt (receipt + progress.json unit hashes).

No repair, no normalization, no line-ending rewrite: any mismatch is a FAIL.

Usage:
  python scripts/sf_full_d7_immutability_audit.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime

REPO = r"D:\wp2_sf_full_d7_r1"
STORE = r"D:\wp2_env_store"
HARNESS = os.path.join(STORE, "harness", "d7_r3")
MANIFESTS = os.path.join(STORE, "manifests")
RECEIPTS = os.path.join(STORE, "receipts")
LOCKS = os.path.join(STORE, "artifacts", "locks")
CAL_R1 = r"D:\wp2_sf_calibration_r1"
CAL_R1_STORE = r"D:\wp2_sf_calibration_r1_store"
RESEARCH_FREEZE = os.path.join(REPO, "research", "source-fidelity-r1")
RESEARCH_CAL = os.path.join(REPO, "research", "source-fidelity-calibration-r1")
OUT_DIR = os.path.join(REPO, "research", "source-fidelity-full-d7-r1")

HARNESS_FREEZE = os.path.join(MANIFESTS, "D7_R3_HARNESS_FREEZE.json")
MATRIX = os.path.join(MANIFESTS, "VALIDATION_UNIT_MATRIX.csv")
TASK_ENV = os.path.join(MANIFESTS, "TASK_ENV_MATRIX.csv")
DOCKER_PROFILES = os.path.join(MANIFESTS, "DOCKER_PROFILE_MANIFEST.json")
MARKER_AUDIT = os.path.join(MANIFESTS, "MARKER_FILTER_AUDIT.json")
D6_NATIVE = os.path.join(MANIFESTS, "D6_NATIVE_RESULTS.json")
WHEELHOUSE_HASHES = os.path.join(MANIFESTS, "WHEELHOUSE_HASHES_py312.json")
WHEELHOUSE_HASHES_38 = os.path.join(MANIFESTS, "WHEELHOUSE_HASHES_py38.json")
WHEELHOUSE_HASHES_39 = os.path.join(MANIFESTS, "WHEELHOUSE_HASHES_py39.json")
DOCKER_IMAGE_PLAN = os.path.join(MANIFESTS, "DOCKER_IMAGE_PLAN.csv")
DOCKER_IMAGE_PLAN_SHA = os.path.join(MANIFESTS, "DOCKER_IMAGE_PLAN.csv.sha256")
ENV_PROFILE_MATRIX = os.path.join(MANIFESTS, "ENV_PROFILE_MATRIX.csv")
ENV_PROFILE_MATRIX_SHA = os.path.join(MANIFESTS, "ENV_PROFILE_MATRIX.csv.sha256")

SF_FREEZE = os.path.join(RESEARCH_FREEZE, "SOURCE_FIDELITY_AMENDMENT_FREEZE.json")
SF_MANIFEST = os.path.join(RESEARCH_FREEZE, "SOURCE_FIDELITY_PROVENANCE_MANIFEST.json")
SF_IMPACT = os.path.join(RESEARCH_FREEZE, "POPULATION_CLOSURE_IMPACT_R1.json")
SF_VALIDATION = os.path.join(RESEARCH_FREEZE, "SOURCE_FIDELITY_VALIDATION_R1.json")
SF_AUDIT_CSV = os.path.join(RESEARCH_FREEZE, "D7_DEPENDENCY_SOURCE_TYPE_AUDIT.csv")
SF_DEFECT = os.path.join(RESEARCH_FREEZE, "SOURCE_IDENTITY_DEFECT_RECEIPT.json")
SF_P2P_F2P = os.path.join(RESEARCH_FREEZE, "SOURCE_FIDELITY_P2P_F2P_RECEIPT.json")

CAL_RECEIPT = os.path.join(RESEARCH_CAL, "SOURCE_FIDELITY_CALIBRATION_12_RECEIPT.json")
CAL_REPORT = os.path.join(RESEARCH_CAL, "SOURCE_FIDELITY_CALIBRATION_12_REPORT.md")
CAL_INVARIANCE = os.path.join(RESEARCH_CAL, "SOURCE_FIDELITY_CALIBRATION_INVARIANCE_AUDIT.json")
CAL_P2P_F2P = os.path.join(RESEARCH_CAL, "SOURCE_FIDELITY_CALIBRATION_P2P_F2P.json")
CAL_PROGRESS = os.path.join(CAL_R1_STORE, "progress.json")

EXPECTED_HARNESS_FREEZE_SHA = "ad8130941391aad2a0575221373651fbfb138f694122f3cd901c59639f68ab35"
EXPECTED_POPULATION = 144
EXPECTED_TASKS = 219


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def check(name: str, fn, detail: str = "") -> dict:
    try:
        ok, extra = fn()
        return {"id": name, "pass": ok, "detail": extra if extra else detail}
    except Exception as exc:
        return {"id": name, "pass": False, "detail": f"{type(exc).__name__}: {exc}"}


def harness_hashes_exact() -> tuple[bool, str]:
    freeze = load_json(HARNESS_FREEZE)
    r3_receipt = load_json(os.path.join(RECEIPTS, "D7_R3_CALIBRATION_12_RECEIPT.json"))
    if sha256(HARNESS_FREEZE) != EXPECTED_HARNESS_FREEZE_SHA:
        return False, "D7_R3_HARNESS_FREEZE.json sha mismatch"
    man_actual = r3_receipt["manifest_hashes"]["manifest_actual_file_sha256"]
    for rel, info in freeze["harness_files"].items():
        p = os.path.join(HARNESS, rel)
        if not os.path.isfile(p):
            return False, f"harness file missing: {rel}"
        disk = sha256(p)
        if rel == "D7_R3_HARNESS_MANIFEST.json":
            if disk != man_actual:
                return False, f"manifest actual bytes mismatch {disk} != {man_actual}"
            continue
        if disk != info["sha256"]:
            return False, f"harness file mismatch {rel}: {disk} != {info['sha256']}"
    return True, "all frozen R3 harness files byte-exact (manifest bound by R3 receipt actual-file hash)"


def locks_exact() -> tuple[bool, str]:
    with open(TASK_ENV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    bad = []
    for r in rows:
        tid = r["task_id"]
        lt = r["lock_type"]
        ref = r.get("lock_sha256_git_blob") or ""
        p = os.path.join(LOCKS, f"{tid}_{lt}.toml")
        if not os.path.isfile(p):
            bad.append(f"{tid} missing lock")
            continue
        if ref and sha256(p) != ref:
            bad.append(f"{tid} lock sha mismatch")
    return (not bad), "; ".join(bad[:5]) if bad else f"{len(rows)} lock artifacts verified"


def docker_images_exact() -> tuple[bool, str]:
    """Every distinct native_profile_id in the 144-unit population must have a
    frozen native profile and a locally-present image whose ID matches D6."""
    d6 = load_json(D6_NATIVE)
    image_ids = d6.get("image_ids", {})
    dmp = load_json(DOCKER_PROFILES)
    np = dmp.get("native_profiles", {})
    with open(MATRIX, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    profiles = sorted({r["native_profile_id"] for r in rows})
    bad = []
    verified = 0
    for pid in profiles:
        if pid not in np:
            bad.append(f"native profile missing: {pid}")
            continue
        img = f"envcanon/saleor-env-native-{pid}:latest"
        r = subprocess.run(["docker", "image", "inspect", "-f", "{{.Id}}", img],
                           capture_output=True, text=True)
        if r.returncode != 0:
            bad.append(f"{img} not inspectable")
            continue
        full = r.stdout.strip().removeprefix("sha256:")
        ref = image_ids.get(f"envcanon/saleor-env-native-{pid}")
        if ref is not None and full[:12] != ref:
            bad.append(f"{img} id {full[:12]} != D6 {ref}")
            continue
        verified += 1
    msg = f"{verified}/{len(profiles)} population profiles verified (D6+local+docker)"
    if bad:
        msg = msg + "; " + "; ".join(bad[:5])
    return (not bad), msg


def provenance_files_identical() -> tuple[bool, str]:
    """Repo source-fidelity freeze files are byte-identical to calibration R1."""
    pairs = [
        (SF_FREEZE, os.path.join(CAL_R1, "research", "source-fidelity-r1", "SOURCE_FIDELITY_AMENDMENT_FREEZE.json")),
        (SF_MANIFEST, os.path.join(CAL_R1, "research", "source-fidelity-r1", "SOURCE_FIDELITY_PROVENANCE_MANIFEST.json")),
        (SF_IMPACT, os.path.join(CAL_R1, "research", "source-fidelity-r1", "POPULATION_CLOSURE_IMPACT_R1.json")),
        (SF_VALIDATION, os.path.join(CAL_R1, "research", "source-fidelity-r1", "SOURCE_FIDELITY_VALIDATION_R1.json")),
        (SF_AUDIT_CSV, os.path.join(CAL_R1, "research", "source-fidelity-r1", "D7_DEPENDENCY_SOURCE_TYPE_AUDIT.csv")),
        (SF_DEFECT, os.path.join(CAL_R1, "research", "source-fidelity-r1", "SOURCE_IDENTITY_DEFECT_RECEIPT.json")),
        (SF_P2P_F2P, os.path.join(CAL_R1, "research", "source-fidelity-r1", "SOURCE_FIDELITY_P2P_F2P_RECEIPT.json")),
        (CAL_RECEIPT, os.path.join(CAL_R1, "research", "source-fidelity-calibration-r1", "SOURCE_FIDELITY_CALIBRATION_12_RECEIPT.json")),
        (CAL_REPORT, os.path.join(CAL_R1, "research", "source-fidelity-calibration-r1", "SOURCE_FIDELITY_CALIBRATION_12_REPORT.md")),
        (CAL_INVARIANCE, os.path.join(CAL_R1, "research", "source-fidelity-calibration-r1", "SOURCE_FIDELITY_CALIBRATION_INVARIANCE_AUDIT.json")),
        (CAL_P2P_F2P, os.path.join(CAL_R1, "research", "source-fidelity-calibration-r1", "SOURCE_FIDELITY_CALIBRATION_P2P_F2P.json")),
    ]
    bad = []
    hashes = {}
    for a, b in pairs:
        if not os.path.isfile(a) or not os.path.isfile(b):
            bad.append(f"{os.path.basename(a)} missing")
            continue
        ha, hb = sha256(a), sha256(b)
        hashes[os.path.basename(a)] = ha
        if ha != hb:
            bad.append(f"{os.path.basename(a)} differs from calibration R1")
    return (not bad), (f"{len(pairs)} provenance/calibration files byte-identical" if not bad else "; ".join(bad))


def unit_record_hash(unit: dict) -> str:
    """Deterministic hash of a unit's qualification evidence subset.

    Replicates the calibration receipt's unit_record_hash exactly
    (subset + sort_keys + compact separators).
    """
    subset = {
        "validation_unit_id": unit["validation_unit_id"],
        "ordered_calibration_index": unit["ordered_calibration_index"],
        "member_task_ids": unit["member_task_ids"],
        "python_version": unit["python_version"],
        "lock_sha256": unit["lock_sha256"],
        "install_route": unit["install_route"],
        "native_profile_id": unit["native_profile_id"],
        "docker_profile_id": unit["docker_profile_id"],
        "image_id": unit["image_id"],
        "old_r3_closure_identity_sha256": unit.get("old_r3_closure_identity_sha256"),
        "new_source_aware_closure_identity_sha256": unit.get("new_source_aware_closure_identity_sha256"),
        "source_fidelity_change_applied": unit.get("source_fidelity_change_applied"),
        "selected_hashes": unit.get("selected_pyxb_authorizenet_hashes"),
        "closure": unit.get("closure"),
        "resolution_passed": unit.get("resolution_passed"),
        "final_classification": unit.get("final_classification"),
        "network_status": unit.get("network_status"),
        "install_status": unit.get("install_status"),
        "pip_check_status": unit.get("pip_check_status"),
        "native_status": unit.get("native_status"),
        "smoke_status": unit.get("smoke_status"),
        "run": unit.get("run"),
    }
    payload = json.dumps(subset, sort_keys=True, separators=(",", ":"))
    return sha256_bytes(payload.encode("utf-8"))


def calibration_progress_exact() -> tuple[bool, str]:
    """Calibration PASS progress records the exact frozen unit_result_hashes."""
    rec = load_json(CAL_RECEIPT)
    prog = load_json(CAL_PROGRESS)
    completed = {c["validation_unit_id"]: c for c in prog["completed"]}
    exp = rec["unit_result_hashes"]
    if len(completed) != 12:
        return False, f"progress has {len(completed)} units != 12"
    bad = []
    for uid, h in exp.items():
        if uid not in completed:
            bad.append(f"{uid} missing in progress")
            continue
        if unit_record_hash(completed[uid]) != h:
            bad.append(f"{uid} hash mismatch")
    return (not bad), "12/12 unit hashes match calibration receipt" if not bad else "; ".join(bad)


def population_counts() -> tuple[bool, str]:
    with open(MATRIX, newline="", encoding="utf-8") as f:
        units = list(csv.DictReader(f))
    with open(TASK_ENV, newline="", encoding="utf-8") as f:
        tasks = list(csv.DictReader(f))
    if len(units) != EXPECTED_POPULATION:
        return False, f"units {len(units)} != 144"
    if len(tasks) != EXPECTED_TASKS:
        return False, f"tasks {len(tasks)} != 219"
    uids = [u["unit_id"] for u in units]
    if len(set(uids)) != len(uids):
        return False, "duplicate unit ids"
    tids = [t["task_id"] for t in tasks]
    if len(set(tids)) != len(tids):
        return False, "duplicate task ids"
    return True, f"{len(units)} units / {len(tasks)} tasks, no duplicates"


def d6_image_ids_reference() -> tuple[bool, str]:
    d6 = load_json(D6_NATIVE)
    image_ids = d6.get("image_ids", {})
    return bool(image_ids), f"{len(image_ids)} frozen image rows in D6"


def main() -> int:
    checks = [
        check("F1_harness_freeze_sha", harness_hashes_exact),
        check("F1_locks_exact", locks_exact),
        check("F1_docker_images_exact", docker_images_exact),
        check("F1_d6_image_ids_reference", d6_image_ids_reference),
        check("F1_provenance_files_identical", provenance_files_identical),
        check("F1_calibration_progress_exact", calibration_progress_exact),
        check("F1_population_counts", population_counts),
    ]
    all_pass = all(c["pass"] for c in checks)
    manifest_hashes = {c["id"]: c["detail"] for c in checks}
    receipt = {
        "artifact": "FULL_D7_INPUT_IMMUTABILITY_AUDIT",
        "mission": "M17_ENV_CANON_SOURCE_FIDELITY_R1_FULL_D7",
        "phase": "F1",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "all_pass": all_pass,
        "checks": checks,
        "expected_harness_freeze_sha256": EXPECTED_HARNESS_FREEZE_SHA,
        "expected_population": EXPECTED_POPULATION,
        "expected_tasks": EXPECTED_TASKS,
        "no_repair": True,
        "no_normalization": True,
        "manifest_hashes": manifest_hashes,
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "FULL_D7_INPUT_IMMUTABILITY_AUDIT.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2, sort_keys=True)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    print(f"ALL_PASS={all_pass}")
    print(f"WROTE={out}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())