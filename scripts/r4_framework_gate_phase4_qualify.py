#!/usr/bin/env python3
"""M17_D7_R4_FRAMEWORK_GATE_PHASE4_REPAIR - minimal real offline qualification.

Runs exactly ONE Full144 validation unit (default: the historical Unit63,
``vu-2483fd026a5e``) through the REPAIRED Phase-4 runner in a dedicated
non-scientific Phase-4 qualification root, using existing local images/artifacts
only (``--network=none``, no pull/build/download, no scientific evidence import).

This is a narrow harness over the FROZEN qualified runner machinery
(``scripts/r4_behavioral_calibration_n12_r2.py``).  It does NOT modify any
runner/driver/provider semantics: it only binds the runner to a single-unit
Full144 plan + a fresh qualification run root, then runs the behavioural unit
path (install / pip check / native / import / pytest smoke + classification).

Phase-4 repair qualification assertions (acceptance gate P4):
  A. no ``python manage.py check`` gate is executed by the container script;
  B. the per-worktree manage marker is recorded explicitly as
     ``NOT_APPLICABLE_SYNTHETIC_GATE_REMOVED`` (never a fake MANAGE_RC_=0);
  C. Unit63 qualifies PASS iff all remaining mandatory gates pass.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
SRC = PROJECT / "src"
SCRIPTS = PROJECT / "scripts"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import r4_behavioral_calibration_n12_r2 as r2  # noqa: E402

DEFAULT_UNIT = "vu-2483fd026a5e"  # historical Unit63 (saleor-rc-2a59d31fc839)
REMOVED_STATE = "NOT_APPLICABLE_SYNTHETIC_GATE_REMOVED"


def census_unit(uid: str) -> dict[str, Any]:
    census = json.loads((PROJECT / "research" / "env-canon-r4"
                         / "R4_I6_CORRECTED_ZERO_CONTAINER_CENSUS_144.json").read_text(encoding="utf-8"))
    units = census["units"]
    if not isinstance(units, list):
        raise SystemExit("census units is not a list")
    for u in units:
        if not isinstance(u, dict):
            continue
        if u.get("validation_unit_id") == uid:
            return u
    raise SystemExit(f"unknown validation unit {uid}")


def bind_single_unit(uid: str, run_root: Path) -> None:
    """Bind the frozen runner to one Full144 unit + a fresh qualification root."""
    u = census_unit(uid)
    unit_plan: dict[str, Any] = {
        "validation_unit_id": u["validation_unit_id"],
        "member_task_ids": list(u["member_tasks"]),
        "docker_profile_id": u["docker_profile_id"],
        "native_profile_id": u["native_profile_id"],
        "python_version": u["python_version"],
        "lock_type": u["lock_type"],
        "install_route": u["install_route"],
        "wheelhouse_era": u["wheelhouse_era"],
    }
    plan = {
        "schema_version": "env-canon-r4-full144/1.0",
        "calibration_units": [unit_plan],
        "population": {"n_validation_units": 1, "n_mapped_tasks": 1},
        "source_population_identity_sha256": "ce51d2ec0eb28f6b720fbab13a852618e2de0f0a1111a3cc19dc64b1d19defac",
    }
    r2.FROZEN_UNIT_ORDER = (uid,)  # type: ignore[assignment]
    r2.RUN_ROOT = run_root
    r2.EXPECTED_RUN_ROOT = run_root
    r2.EXPECTED_RUN_ROOT_STR = str(run_root)
    r2.FREEZE_DIR = run_root / "freeze"
    r2.UNITS_DIR = run_root / "units"
    r2.LOGS_DIR = run_root / "logs"
    r2.PROGRESS_DIR = run_root / "progress"
    r2.MATERIALIZED_DIR = run_root / "materialized"
    r2.RECEIPTS_DIR = run_root / "receipts"
    r2.PROGRESS_JSON = r2.PROGRESS_DIR / "progress.json"
    r2.load_plan = lambda: plan
    for d in (r2.FREEZE_DIR, r2.UNITS_DIR, r2.LOGS_DIR, r2.PROGRESS_DIR,
              r2.MATERIALIZED_DIR, r2.RECEIPTS_DIR):
        d.mkdir(parents=True, exist_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="R4 framework-gate Phase-4 single-unit real qualification")
    ap.add_argument("--unit-id", default=DEFAULT_UNIT, help="Full144 validation_unit_id")
    ap.add_argument("--run-root", required=True, type=Path, help="fresh non-scientific Phase-4 qualification root")
    args = ap.parse_args()

    if args.run_root.exists() and any(args.run_root.iterdir()):
        print(f"FAIL_CLOSED run root must be fresh/empty: {args.run_root}")
        return 1

    bind_single_unit(args.unit_id, args.run_root)
    try:
        runner = r2.UnitRunner()
        record = runner.run_unit(1)
    except r2.CalibrationFailClosedError as exc:
        print(f"FAIL_CLOSED {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        print(f"UNEXPECTED_FAILURE {exc!r}", file=sys.stderr)
        return 2

    run = record.get("run", {})
    smoke = run.get("smoke", {}) or {}
    manage_gate = run.get("manage_gate", {}) or {}

    gate_removed_assertions = {
        "no_manage_smoke_key": all(not k.startswith("manage_") for k in smoke),
        "manage_gate_state_is_explicit": all(v == REMOVED_STATE for v in manage_gate.values()),
    }
    container_script = r2.container_script(args.unit_id, len(record.get("member_task_ids", [])), [], {})
    gate_removed_assertions["container_never_runs_manage_check"] = "python manage.py check" not in container_script
    gate_removed_assertions["no_fake_manage_success"] = "MANAGE_RC_$(basename $wt)=0" not in container_script

    summary = {
        "schema_version": "env-canon-r4/framework-gate-phase4/qualification/1.0",
        "mission_id": "M17_D7_R4_FRAMEWORK_GATE_PHASE4_REPAIR_AND_REFREEZE",
        "validation_unit_id": record["validation_unit_id"],
        "calibration_index": record["calibration_index"],
        "result": record["result"],
        "classification": record["classification"],
        "network_status": run.get("network_status"),
        "install_rc": run.get("install_rc"),
        "pipcheck_rc": run.get("pipcheck_rc"),
        "native_failures": run.get("native_failures"),
        "smoke": smoke,
        "manage_gate": manage_gate,
        "gate_removed_assertions": gate_removed_assertions,
        "execution_image_ref": record["execution_image_ref"],
        "immutable_image_id": record["immutable_image_id"],
        "elapsed_seconds": record["elapsed_seconds"],
        "qualification_root": str(args.run_root),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))

    if record["result"] != "PASS":
        print(f"QUALIFICATION_FAIL {record['validation_unit_id']} -> {record['classification']}")
        return 1
    if not all(gate_removed_assertions.values()):
        print(f"QUALIFICATION_FAIL gate-removed assertions not all satisfied: {gate_removed_assertions}")
        return 1
    print(f"QUALIFICATION_PASS {record['validation_unit_id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
