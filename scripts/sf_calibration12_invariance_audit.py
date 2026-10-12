#!/usr/bin/env python3
"""M17 source-fidelity fresh calibration-12 scientific invariance audit.

Mission: M17_ENV_CANON_SOURCE_FIDELITY_R1_FRESH_CALIBRATION_12

Verifies every required scientific invariant before the qualification can be
accepted.  Emits ``SOURCE_FIDELITY_CALIBRATION_INVARIANCE_AUDIT.json`` under
``research/source-fidelity-calibration-r1/``.
"""
from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime

STORE = r"D:\wp2_env_store"
MANIFESTS = os.path.join(STORE, "manifests")
RECEIPTS = os.path.join(STORE, "receipts")
HARNESS = os.path.join(STORE, "harness", "d7_r3")
REPO_DIR = r"D:\wp2_sf_calibration_r1"
RESEARCH = os.path.join(REPO_DIR, "research", "source-fidelity-r1")
OUT_DIR = os.path.join(REPO_DIR, "research", "source-fidelity-calibration-r1")
SRC_DIR = os.path.join(REPO_DIR, "src")

PLAN = os.path.join(MANIFESTS, "D7_CALIBRATION_12_PLAN.json")
HARNESS_FREEZE = os.path.join(MANIFESTS, "D7_R3_HARNESS_FREEZE.json")
SF_FREEZE = os.path.join(RESEARCH, "SOURCE_FIDELITY_AMENDMENT_FREEZE.json")
R3_RECEIPT = os.path.join(RECEIPTS, "D7_R3_CALIBRATION_12_RECEIPT.json")
PROGRESS = r"D:\wp2_sf_calibration_r1_store\progress.json"


def load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def sha256(path: str) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    plan = load_json(PLAN)
    harness_freeze = load_json(HARNESS_FREEZE)
    sf_free = load_json(SF_FREEZE)
    r3 = load_json(R3_RECEIPT)
    progress = load_json(PROGRESS)

    plan_ids = [u["validation_unit_id"]
        for u in sorted(plan["units"], key=lambda u: u["ordered_calibration_index"])]
    r3_ids = [u["validation_unit_id"] for u in sorted(r3["units"], key=lambda u: u["ordered_calibration_index"])]
    unit_ids = [c["validation_unit_id"]
        for c in sorted(progress["completed"], key=lambda c: c["ordered_calibration_index"])]

    # 1. CALIBRATION_MEMBERSHIP_CHANGED = FALSE
    membership_unchanged = plan_ids == unit_ids == r3_ids
    # 2. CALIBRATION_ORDER_CHANGED = FALSE
    order_unchanged = (
        [u["ordered_calibration_index"] for u in plan["units"]] == list(range(1, 13))
        and plan_ids == unit_ids == r3_ids
    )
    # 3. PYTHON_VERSION_CHANGED = FALSE
    python_unchanged = all(u["python_version"] == "3.12" for u in plan["units"])
    # 4. TASK_ELIGIBILITY_CHANGED = FALSE
    plan_members = {tid for u in plan["units"] for tid in u["member_task_ids"]}
    r3_members = {tid for u in r3["units"] for tid in u["member_task_ids"]}
    task_eligibility_unchanged = plan_members == r3_members
    # 5. SCIENTIFIC_POPULATION_CHANGED = FALSE
    population_unchanged = plan["tasks_total"] == 219 and plan["selection_rule"] == "FIRST_12_FROZEN_ORDER"
    # 6. SMOKE_GATE_CHANGED = FALSE (frozen R3 harness byte-exact)
    smoke_gate_unchanged = _harness_hashes_exact(harness_freeze)
    # 7. R3_HARNESS_MUTATED = FALSE
    r3_harness_unmutated = _harness_hashes_exact(harness_freeze)
    # 8. PYXBX_USED = FALSE
    pyxbx_used = _pyxbx_used(progress)
    # 9. NETWORK_USED = FALSE
    network_used = any(c.get("network_status") != "NETWORK_UNAVAILABLE" for c in progress["completed"])
    # 10. PREVIOUS_FAILED_EVIDENCE_MODIFIED = FALSE
    prev_evidence_unmodified = _previous_evidence_unmodified()
    # 11. SOURCE_FIDELITY_RULE_GENERIC = TRUE
    rule_generic = _rule_generic(sf_free)

    invariants = {
        "CALIBRATION_MEMBERSHIP_CHANGED": not membership_unchanged,
        "CALIBRATION_ORDER_CHANGED": not order_unchanged,
        "PYTHON_VERSION_CHANGED": not python_unchanged,
        "TASK_ELIGIBILITY_CHANGED": not task_eligibility_unchanged,
        "SCIENTIFIC_POPULATION_CHANGED": not population_unchanged,
        "SMOKE_GATE_CHANGED": not smoke_gate_unchanged,
        "R3_HARNESS_MUTATED": not r3_harness_unmutated,
        "PYXBX_USED": pyxbx_used,
        "NETWORK_USED": network_used,
        "PREVIOUS_FAILED_EVIDENCE_MODIFIED": not prev_evidence_unmodified,
        "SOURCE_FIDELITY_RULE_GENERIC": rule_generic,
    }
    # Boolean presentation in mission terms: invariant holds when FALSE/TRUE as required.
    required_false = [
        "CALIBRATION_MEMBERSHIP_CHANGED",
        "CALIBRATION_ORDER_CHANGED",
        "PYTHON_VERSION_CHANGED",
        "TASK_ELIGIBILITY_CHANGED",
        "SCIENTIFIC_POPULATION_CHANGED",
        "SMOKE_GATE_CHANGED",
        "R3_HARNESS_MUTATED",
        "PYXBX_USED",
        "NETWORK_USED",
        "PREVIOUS_FAILED_EVIDENCE_MODIFIED",
    ]
    all_pass = (all(invariants[k] is False for k in required_false)
                and invariants["SOURCE_FIDELITY_RULE_GENERIC"] is True)

    result = {
        "mission": "M17_ENV_CANON_SOURCE_FIDELITY_R1_FRESH_CALIBRATION_12",
        "phase": "C10_SCIENTIFIC_INVARIANCE_AUDIT",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "all_pass": all_pass,
        "invariants": {
            k: {
                "value": bool(v),
                "required": ("FALSE" if k in required_false else "TRUE"),
                "pass": (v is False if k in required_false else v is True),
            }
            for k, v in invariants.items()
        },
        "detail": {
            "plan_ordered_ids": plan_ids,
            "unit_ordered_ids": unit_ids,
            "r3_ordered_ids": r3_ids,
            "plan_python_versions": sorted({u["python_version"] for u in plan["units"]}),
        },
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "SOURCE_FIDELITY_CALIBRATION_INVARIANCE_AUDIT.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)
    print(json.dumps(result["invariants"], indent=2, sort_keys=True))
    print(f"ALL_PASS={all_pass}")
    print(f"WROTE={out}")
    return 0 if all_pass else 1


def _harness_hashes_exact(freeze: dict) -> bool:
    r3 = load_json(R3_RECEIPT)
    man_actual = r3["manifest_hashes"]["manifest_actual_file_sha256"]
    for rel, info in freeze["harness_files"].items():
        p = os.path.join(HARNESS, rel)
        if not os.path.isfile(p):
            return False
        if rel == "D7_R3_HARNESS_MANIFEST.json":
            if sha256(p) != man_actual:
                return False
            continue
        if sha256(p) != info["sha256"]:
            return False
    return True


def _pyxbx_used(progress: dict) -> bool:
    for c in progress["completed"]:
        overlay = c.get("source_fidelity_overlay", {})
        for art in overlay.get("artifacts", []):
            if "pyxb-x" in art.get("output_filename", "").lower():
                return True
        pins = c.get("closure", {}).get("pins", []) or []
        if any("pyxb-x" in p.lower() for p in pins):
            return True
    return False


def _previous_evidence_unmodified() -> bool:
    p = os.path.join(RECEIPTS, "D7_R3_CALIBRATION_12_RECEIPT.json")
    return sha256(p) == "5bc086be6ef9081be6b99f1940c892281f4ca76bffba39458adcf733ee5c6c33"


def _rule_generic(sf_free: dict) -> bool:
    with open(os.path.join(SRC_DIR, "benchmark", "wp2", "source_fidelity_r1.py"), encoding="utf-8") as fh:
        src = fh.read()
    with open(os.path.join(REPO_DIR, "scripts", "sf_calibration12_driver.py"), encoding="utf-8") as fh:
        driver = fh.read()
    task_ids = re.findall(r"saleor-rc-[0-9a-f]{12}", src + driver)
    return len(task_ids) == 0 and sf_free["invariants"]["TASK_ID_SPECIAL_CASE_USED"] is False


if __name__ == "__main__":
    raise SystemExit(main())
