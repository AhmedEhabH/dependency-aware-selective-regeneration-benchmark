#!/usr/bin/env python3
"""M17_D7_R4_FULL144_ARTIFACT_RECOVERY_SUCCESSOR — Gate 2: full 144-unit static artifact closure.

Deterministic, offline, ZERO-Docker evaluation.  For every frozen Full144 unit it
computes the exact effective artifact inputs that execution would use
(base era merged wheelhouse names + source-fidelity overlay wheels + R4-E
recovery overlay wheels selected evidence-driven from the ACTUAL runtime pins),
then resolves every runtime pin with the qualified wheel-compatibility engine.
No scientific Docker workload is executed.

Terminal evidence (fail-closed):
  N_UNITS=144 N_RESOLVABLE=144 N_MISSING=0 N_INCOMPATIBLE=0
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCRIPT = Path(__file__).resolve()
PROJECT = SCRIPT.parents[1]
SRC = PROJECT / "src"
SCRIPTS = PROJECT / "scripts"

SUCCESSOR_ROOT = Path(
    r"D:\WP2\runs\r4-full-d7-144-artifact-recovery-successor-2026-10-15"
)
REPO_EVIDENCE = PROJECT / "research" / "env-canon-r4" / "R4_FULL144_ARTIFACT_CLOSURE_144.json"
E1_PLAN = PROJECT / "research" / "env-canon-r4" / "R4_E1_PYLINT_RECOVERY_PLAN.json"
E2_RECEIPT = PROJECT / "research" / "env-canon-r4" / "R4_E2_PYLINT_ACQUISITION_RECEIPT.json"
E3_RECEIPT = PROJECT / "research" / "env-canon-r4" / "R4_E3_AFFECTED_REVALIDATION_RECEIPT.json"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SystemExit(f"FAIL_CLOSED missing authority: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"FAIL_CLOSED authority not an object: {path}")
    return data


def _frozen_recovery_identities() -> set[tuple[str, str]]:
    e1 = _read_json(E1_PLAN)
    return {tuple(x) for x in e1.get("exact_ordered_recovery_identities", [])}


def _load_execution() -> tuple[Any, Any, Any]:
    for p in (SRC, SCRIPTS):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    import r4_behavioral_calibration_n12_r2 as r2  # type: ignore[import-untyped]

    from benchmark.wp2.full144 import driver, population

    return driver, population, r2


def evaluate_unit(r2: Any, uid: str, unit: dict[str, Any], pins: list[str]) -> dict[str, Any]:
    era = unit["wheelhouse_era"]
    sf_inputs = r2.source_fidelity_overlay_inputs(uid) if uid in r2.SOURCE_FIDELITY_UNITS else []
    recovery_inputs = r2.recovery_overlay_inputs_for_pins(pins, era)
    recovery = recovery_inputs[0] if recovery_inputs else None

    base = r2.build_merged_wheelhouse(era)
    base_names = sorted(p.name for p in base.glob("*.whl"))
    overlay_filenames = [a["output_filename"] for a in sf_inputs]
    recovery_versions: list[str] = []
    if recovery:
        overlay_filenames.append(recovery["filename"])
        recovery_versions.append(recovery["version"])
    overlay_set = set(overlay_filenames)
    wheel_names = sorted(n for n in base_names if n not in overlay_set) + sorted(overlay_set)

    res = r2._resolve_pin_wheels(pins, era, wheel_names=wheel_names)
    return {
        "validation_unit_id": uid,
        "python_version": unit["python_version"],
        "lock_type": unit["lock_type"],
        "install_route": unit["install_route"],
        "wheelhouse_era": era,
        "runtime_pins_count": len(pins),
        "resolved_wheels_count": len(res.get("resolved", {})),
        "missing": res.get("missing", []),
        "incompatible": res.get("incompatible", []),
        "resolvable": not (res.get("missing") or res.get("incompatible")),
        "source_fidelity_overlay_count": len(sf_inputs),
        "recovery_overlay": {
            "package": recovery["package"],
            "version": recovery["version"],
            "filename": recovery["filename"],
            "sha256": recovery["sha256"],
            "manifest_sha256": recovery["manifest_sha256"],
        }
        if recovery
        else None,
        "recovery_overlay_versions": recovery_versions,
        "source_fidelity_filenames": overlay_filenames[: len(sf_inputs)],
    }


def evaluate(run_root: Path) -> dict[str, Any]:
    os.environ["R4_FULL144_RUN_ROOT"] = str(run_root)
    driver, population, r2 = _load_execution()

    pop = population.validate_population()
    uids = population.ordered_unit_ids()
    orders = {u: i + 1 for i, u in enumerate(uids)}
    driver.configure_runner()

    plan = driver.full144_plan()
    by_uid = {u["validation_unit_id"]: u for u in plan["calibration_units"]}

    frozen_recovery = _frozen_recovery_identities()

    per_unit: list[dict[str, Any]] = []
    recovery_versions: dict[str, int] = {}
    recovery_artifacts: dict[tuple[str, str, str], str] = {}
    n_recovery_units = 0
    n_resolvable = 0
    missing_total: list[str] = []
    incompatible_total: list[dict[str, Any]] = []

    for uid in uids:
        unit = by_uid[uid]
        pins_info = r2.runtime_pins(uid)
        row = evaluate_unit(r2, uid, unit, pins_info["runtime_pins"])
        row["calibration_index"] = orders[uid]
        missing_total.extend(row["missing"])
        incompatible_total.extend(row["incompatible"])
        if not row["resolvable"]:
            raise SystemExit(
                f"FAIL_CLOSED unit unresolved {uid}: "
                f"missing={row['missing']} incompatible={row['incompatible']}"
            )
        n_resolvable += 1
        rec = row["recovery_overlay"]
        if rec is not None:
            n_recovery_units += 1
            key = (rec["package"], rec["version"], rec["filename"])
            if key in recovery_artifacts and recovery_artifacts[key] != rec["sha256"]:
                raise SystemExit(f"FAIL_CLOSED conflicting recovery artifact hash for {key}")
            recovery_artifacts[key] = rec["sha256"]
            recovery_versions[rec["version"]] = recovery_versions.get(rec["version"], 0) + 1
            if (rec["package"], rec["version"]) not in frozen_recovery:
                raise SystemExit(
                    f"FAIL_CLOSED recovery artifact outside frozen R4-E authority: {rec}"
                )
        per_unit.append(row)

    n_units = len(uids)
    if n_units != 144:
        raise SystemExit(f"FAIL_CLOSED N_UNITS={n_units} != 144")

    payload: dict[str, Any] = {
        "schema_version": "env-canon-r4/full144-artifact-recovery/static-closure/1.0",
        "mission_id": "M17_D7_R4_FULL144_ARTIFACT_RECOVERY_SUCCESSOR",
        "verdict": "PASS_FULL144_STATIC_ARTIFACT_CLOSURE",
        "N_UNITS": n_units,
        "N_RESOLVABLE": n_resolvable,
        "N_MISSING": len(missing_total),
        "N_INCOMPATIBLE": len(incompatible_total),
        "units_consuming_recovery": n_recovery_units,
        "recovered_versions_consumed": recovery_versions,
        "recovery_artifacts_used": [
            {"package": p, "version": v, "filename": f, "sha256": h}
            for (p, v, f), h in sorted(recovery_artifacts.items())
        ],
        "zero_recovery_outside_frozen_authority": True,
        "docker_workloads_executed": 0,
        "network_policy": "--network=none; no pull/build/download/acquire",
        "population_identity": pop["population_identity"],
        "ordered_membership_hash": pop["ordered_membership_hash"],
        "population_strata": pop["strata"],
        "recovery_authority_hashes": {
            "e1_plan": _sha256_file(E1_PLAN),
            "e2_receipt": _sha256_file(E2_RECEIPT),
            "e3_receipt": _sha256_file(E3_RECEIPT),
        },
        "execution_code_hashes": {
            "runner": _sha256_file(SCRIPTS / "r4_behavioral_calibration_n12_r2.py"),
            "driver": _sha256_file(SRC / "benchmark" / "wp2" / "full144" / "driver.py"),
            "population": _sha256_file(SRC / "benchmark" / "wp2" / "full144" / "population.py"),
            "closure_script": _sha256_file(SCRIPT),
        },
        "ordered_membership": uids,
        "per_unit": per_unit,
        "frozen_utc": datetime.now(UTC).isoformat(),
    }
    return payload


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Full144 static artifact closure gate")
    ap.add_argument("--run-root", type=Path, default=SUCCESSOR_ROOT)
    ap.add_argument("--repo-evidence", type=Path, default=REPO_EVIDENCE)
    args = ap.parse_args(argv)

    run_root: Path = args.run_root
    run_root.mkdir(parents=True, exist_ok=True)
    freeze_dir = run_root / "freeze"
    freeze_dir.mkdir(parents=True, exist_ok=True)

    payload = evaluate(run_root)

    freeze_copy = freeze_dir / "FULL144_STATIC_ARTIFACT_CLOSURE.json"
    for target in (freeze_copy, args.repo_evidence):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(
        f"N_UNITS = {payload['N_UNITS']}\n"
        f"N_RESOLVABLE = {payload['N_RESOLVABLE']}\n"
        f"N_MISSING = {payload['N_MISSING']}\n"
        f"N_INCOMPATIBLE = {payload['N_INCOMPATIBLE']}\n"
        f"UNITS_CONSUMING_RECOVERY = {payload['units_consuming_recovery']}\n"
        f"RECOVERED_VERSIONS_CONSUMED = {json.dumps(payload['recovered_versions_consumed'], sort_keys=True)}\n"
        f"RECOVERY_ARTIFACTS_USED = {len(payload['recovery_artifacts_used'])}\n"
        f"VERDICT = {payload['verdict']}\n"
        f"EVIDENCE = {args.repo_evidence}\n"
        f"FREEZE_COPY = {freeze_copy}\n"
    )
    if payload["N_RESOLVABLE"] != 144 or payload["N_MISSING"] or payload["N_INCOMPATIBLE"]:
        return 1
    print("FULL144_STATIC_ARTIFACT_CLOSURE_PASS_144_144")
    return 0


if __name__ == "__main__":
    sys.exit(main())
