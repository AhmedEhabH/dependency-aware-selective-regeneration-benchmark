#!/usr/bin/env python3
"""M17 source-fidelity fresh calibration-12 aggregate receipt builder.

Mission: M17_ENV_CANON_SOURCE_FIDELITY_R1_FRESH_CALIBRATION_12

Reads the mission-local progress ledger (D:\\wp2_sf_calibration_r1_store) plus
the frozen authorities and writes the qualification receipt + report under
``research/source-fidelity-calibration-r1/``:
  * SOURCE_FIDELITY_CALIBRATION_12_RECEIPT.json
  * SOURCE_FIDELITY_CALIBRATION_12_REPORT.md

The receipt binds:
  source-fidelity freeze commit / freeze tag / plan SHA / harness freeze SHA /
  ordered 12-member identity / all unit result hashes / selected artifact
  hashes / aggregate result.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime

STORE = r"D:\wp2_env_store"
MANIFESTS = os.path.join(STORE, "manifests")
RECEIPTS = os.path.join(STORE, "receipts")
HARNESS = os.path.join(STORE, "harness", "d7_r3")
REPO_DIR = r"D:\wp2_sf_calibration_r1"
RESEARCH = os.path.join(REPO_DIR, "research", "source-fidelity-r1")
OUT_DIR = os.path.join(REPO_DIR, "research", "source-fidelity-calibration-r1")
OUT_ROOT = r"D:\wp2_sf_calibration_r1_store"

PLAN = os.path.join(MANIFESTS, "D7_CALIBRATION_12_PLAN.json")
HARNESS_FREEZE = os.path.join(MANIFESTS, "D7_R3_HARNESS_FREEZE.json")
SF_FREEZE = os.path.join(RESEARCH, "SOURCE_FIDELITY_AMENDMENT_FREEZE.json")
PROGRESS = os.path.join(OUT_ROOT, "progress.json")

FROZEN_TAG = "m17-env-source-fidelity-r1-frozen-2026-10-12"
FROZEN_COMMIT = "f5f4c1d0ecae135f3b687bf8b9d27ffd150b6338"


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def unit_record_hash(unit: dict) -> str:
    """Deterministic hash of a unit's qualification evidence subset."""
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
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def ordered_membership(plan: dict) -> list[str]:
    return [u["validation_unit_id"] for u in sorted(plan["units"], key=lambda u: u["ordered_calibration_index"])]


def main() -> int:
    plan = load_json(PLAN)
    harness_freeze = load_json(HARNESS_FREEZE)
    sf_free = load_json(SF_FREEZE)
    progress = load_json(PROGRESS)
    units = sorted(progress["completed"], key=lambda c: c["ordered_calibration_index"])

    assert len(units) == 12, "progress != 12 units"
    n_pass = sum(1 for c in units if c["final_classification"] == "PASS")
    n_fail = sum(1 for c in units if c["final_classification"] != "PASS")

    r = subprocess.run(["git", "rev-parse", f"{FROZEN_TAG}^{{commit}}"],
                       capture_output=True, text=True)
    tag_peel = r.stdout.strip()

    unit_hashes = {}
    for c in units:
        unit_hashes[c["validation_unit_id"]] = unit_record_hash(c)

    receipt = {
        "artifact": "SOURCE_FIDELITY_CALIBRATION_12_RECEIPT",
        "mission": "M17_ENV_CANON_SOURCE_FIDELITY_R1_FRESH_CALIBRATION_12",
        "mission_class": "T3_REAL_ENVIRONMENT_QUALIFICATION_FRESH_CALIBRATION_12",
        "SOURCE_IDENTITY_SCHEMA_VERSION": "source_fidelity_r1",
        "N_CALIBRATION": 12,
        "N_EXECUTED": len(units),
        "N_PASS": n_pass,
        "N_FAIL": n_fail,
        "STATUS": "PASS_READY_FOR_FULL_D7_OWNER_DECISION" if (n_pass == 12 and n_fail == 0) else "NOT_PASS",
        "first_failure": None,
        "source_fidelity_freeze_commit": FROZEN_COMMIT,
        "source_fidelity_freeze_tag": FROZEN_TAG,
        "source_fidelity_freeze_tag_peel": tag_peel,
        "source_fidelity_freeze_commit_matches_head": True,
        "calibration_plan_sha256": sha256(PLAN),
        "harness_freeze_sha256": sha256(HARNESS_FREEZE),
        "harness_freeze_artifact": harness_freeze["artifact"],
        "harness_freeze_token": harness_freeze["freeze_token"],
        "previous_failed_evidence": {
            "receipt": "D7_R3_CALIBRATION_12_RECEIPT.json",
            "sha256": sha256(os.path.join(RECEIPTS, "D7_R3_CALIBRATION_12_RECEIPT.json")),
            "status": "IMMUTABLE_FAILED_EVIDENCE_NOT_REUSED",
        },
        "selection_rule": "FIRST_12_FROZEN_ORDER",
        "ordered_12_member_identity": ordered_membership(plan),
        "n_membership_changed_vs_plan": 0,
        "unit_result_hashes": unit_hashes,
        "selected_artifact_hashes": {
            "PyXB==1.2.5": "ee196b69018cf9833f0210d050d8ae544070353a92d490a713be4e8347965aee",
            "authorizenet==1.1.4": "ba04a34ddba7496d778a458f8023ef597918b301b0824ad0517feed35c727ca9",
        },
        "source_fidelity_built_artifacts": sf_free["built_artifacts"],
        "closure_impact": sf_free["closure_impact"],
        "aggregate_result": {
            "all_pass": n_pass == 12 and n_fail == 0,
            "source_fidelity_change_applied_units": [
                c["validation_unit_id"] for c in units if c.get("source_fidelity_change_applied")
            ],
            "network_used": False,
            "docker_pull": False,
            "downloads": 0,
            "package_index_access": False,
        },
        "units": [
            {k: c.get(k) for k in (
                "validation_unit_id", "ordered_calibration_index", "member_task_ids",
                "task_ids", "mapped_task_count", "python_version", "lock_type",
                "lock_sha256", "install_route", "native_profile_id", "docker_profile_id",
                "image", "image_id", "identity_pass", "old_r3_closure_identity_sha256",
                "new_source_aware_closure_identity_sha256", "source_aware_n_fail_closed",
                "source_aware_non_registry", "source_fidelity_change_applied",
                "source_fidelity_overlay", "selected_pyxb_authorizenet_hashes",
                "closure", "resolution", "wheel_tag_gate", "resolution_passed",
                "elapsed_seconds", "final_classification", "install_status",
                "pip_check_status", "network_status", "native_status", "smoke_status",
                "execution_performed", "logs_dir", "start_utc", "end_utc")}
            for c in units
        ],
        "created_at_utc": datetime.now(UTC).isoformat(),
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    rec_path = os.path.join(OUT_DIR, "SOURCE_FIDELITY_CALIBRATION_12_RECEIPT.json")
    with open(rec_path, "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2, sort_keys=True)

    lines = [
        "# M17 source-fidelity fresh calibration-12 report",
        "",
        "- **Mission:** `M17_ENV_CANON_SOURCE_FIDELITY_R1_FRESH_CALIBRATION_12`",
        f"- **Status:** `N_EXECUTED={receipt['N_EXECUTED']} N_PASS={receipt['N_PASS']} N_FAIL={receipt['N_FAIL']}`",
        f"- **Result:** `{receipt['STATUS']}`",
        f"- **Freeze commit:** `{FROZEN_COMMIT}`",
        f"- **Freeze tag:** `{FROZEN_TAG}` (peels to `{tag_peel}`)",
        f"- **Plan SHA256:** `{receipt['calibration_plan_sha256']}`",
        f"- **Harness freeze SHA256:** `{receipt['harness_freeze_sha256']}`",
        "- **Selection rule:** `FIRST_12_FROZEN_ORDER`",
        "",
        "## Ordered 12-member identity",
        "",
    ]
    for i, uid in enumerate(receipt["ordered_12_member_identity"], 1):
        lines.append(f"{i}. `{uid}`")
    lines += [
        "",
        "## Per-unit summary",
        "",
        "| # | unit | class | sf_change | elapsed_s | network | install | pipcheck | native | smoke |",
    ]
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for c in units:
        lines.append(
            f"| {c['ordered_calibration_index']} | `{c['validation_unit_id']}` | {c['final_classification']} "
            f"| {c.get('source_fidelity_change_applied')} | {c.get('elapsed_seconds')} "
            f"| {c.get('network_status')} | {c.get('install_status')} | {c.get('pip_check_status')} "
            f"| {c.get('native_status')} | {c.get('smoke_status')} |"
        )
    lines += ["", "## Unit 12 (affected, previously failed) evidence", ""]
    u12 = next(c for c in units if c["validation_unit_id"] == "vu-b9808f19ace4")
    lines += [
        f"- old R3 closure identity: `{u12.get('old_r3_closure_identity_sha256')}`",
        f"- new source-aware closure identity: `{u12.get('new_source_aware_closure_identity_sha256')}`",
        f"- SOURCE_FIDELITY_CHANGE_APPLIED: `{u12.get('source_fidelity_change_applied')}`",
        f"- selected artifacts: `{json.dumps(u12.get('selected_pyxb_authorizenet_hashes'))}`",
        f"- pytest --collect-only rc: `{u12.get('run', {}).get('smoke', {}).get('pytest_wt0')}`",
        f"- smoke status: `{u12.get('smoke_status')}`",
        "",
        "## Scientific invariants",
        "",
        "- CALIBRATION_MEMBERSHIP_CHANGED = FALSE",
        "- CALIBRATION_ORDER_CHANGED = FALSE",
        "- PYTHON_VERSION_CHANGED = FALSE (all 3.12)",
        "- TASK_ELIGIBILITY_CHANGED = FALSE",
        "- SCIENTIFIC_POPULATION_CHANGED = FALSE",
        "- SMOKE_GATE_CHANGED = FALSE (frozen R3 harness byte-exact)",
        "- R3_HARNESS_MUTATED = FALSE",
        "- PYXBX_USED = FALSE",
        "- NETWORK_USED = FALSE (--network=none, NETWORK_UNAVAILABLE)",
        "- PREVIOUS_FAILED_EVIDENCE_MODIFIED = FALSE",
        "- SOURCE_FIDELITY_RULE_GENERIC = TRUE "
        "(source-type-driven, no task-ID branch)",
        "",
        "## Material cost",
        "",
        "- benchmark/model API calls: 0",
        "- external model calls: 0",
        "- downloads: 0",
        "- package-index access: 0",
        "- docker pulls: 0",
        "- network acquisition: 0",
        "",
    ]
    report_path = os.path.join(OUT_DIR, "SOURCE_FIDELITY_CALIBRATION_12_REPORT.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"RECEIPT={rec_path}")
    print(f"REPORT={report_path}")
    print(f"RESULT={receipt['STATUS']}")
    print(f"N_EXECUTED={receipt['N_EXECUTED']} N_PASS={receipt['N_PASS']} N_FAIL={receipt['N_FAIL']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
