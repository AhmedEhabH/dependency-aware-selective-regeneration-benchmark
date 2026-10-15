#!/usr/bin/env python3
"""R4 Poetry Closure Successor — bounded real behavioral qualification (S8).

Mission M17_D7_R4_POETRY_CLOSURE_SUCCESSOR_QUALIFICATION.

Uses a NEW run root (never reuses/overwrites old Full-D7 unit evidence) and the
qualified Attempt-6 runner with the SAME behavioral gates as the frozen
Full-D7 execution (runtime-clean binding, exact image immutable IDs, R4-C
materialization, exact local wheels, --network=none, pip check, frozen native
probes, import saleor, manage.py where applicable, pytest collection where
applicable, unchanged timeout semantics).

Mandatory known affected units (successor closure changed):
  vu-0d8ddec94417, vu-8228f26085f6, vu-3a7ebc8e23c7

Controls (justified by the changed semantic surface):
  - vu-e4998719ee01, vu-b68ee1b3ad18  previously-PASS LOCK_FRAGMENT controls
  - vu-117d7bd068d5  previously-PASS V2_EDITABLE_PLUS_LOCK_DEV control
    (the shared runner's runtime_pins projection was restructured, so a V2
     control proves the V2 path is behaviourally unchanged)

No download / no pull / no build / no scientific retry / no adaptation.
Run sequentially; on the first mandatory failure: persist evidence and STOP.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
SRC = PROJECT / "src"
SCRIPTS = PROJECT / "scripts"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import r4_behavioral_calibration_n12_r2 as r2  # noqa: E402

QUAL_ROOT = Path(r"D:\WP2\runs\r4-poetry-closure-successor-qualification-2026-10-14")
CENSUS = PROJECT / "research" / "env-canon-r4" / "R4_I6_CORRECTED_ZERO_CONTAINER_CENSUS_144.json"

QUAL_UNIT_ORDER = (
    "vu-0d8ddec94417",  # known affected (saleor-rc-36a9a14e8d12)
    "vu-8228f26085f6",  # known affected (saleor-rc-5477b7dd3867)
    "vu-3a7ebc8e23c7",  # known affected (saleor-rc-659af1b19239)
    "vu-e4998719ee01",  # control: previously-PASS LOCK_FRAGMENT
    "vu-b68ee1b3ad18",  # control: previously-PASS LOCK_FRAGMENT
    "vu-117d7bd068d5",  # control: previously-PASS V2_EDITABLE_PLUS_LOCK_DEV
)


def _read_json(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(f"missing artifact: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"not a JSON object: {path}")
    return data


def qual_plan() -> dict:
    census = _read_json(CENSUS)
    by_uid = {u["validation_unit_id"]: u for u in census["units"]}
    units: list[dict] = []
    for uid in QUAL_UNIT_ORDER:
        u = by_uid[uid]
        units.append(
            {
                "validation_unit_id": uid,
                "member_task_ids": u["member_tasks"],
                "docker_profile_id": u["docker_profile_id"],
                "native_profile_id": u["native_profile_id"],
                "python_version": u["python_version"],
                "lock_type": u["lock_type"],
                "install_route": u["install_route"],
                "wheelhouse_era": u["wheelhouse_era"],
            }
        )
    return {
        "schema_version": "env-canon-r4-qualification/1.0",
        "n_calibration": len(units),
        "calibration_units": units,
        "population": {"n_validation_units": 144, "n_mapped_tasks": 219},
        "source_population_identity_sha256": r2.EXPECTED_POPULATION_IDENTITY,
        "plan_sha256": "qualification-subset-plan",
        "required_categories": [],
        "uncovered_categories": [],
    }


def configure_runner() -> None:
    if QUAL_ROOT.exists():
        evidence = [
            p for p in QUAL_ROOT.rglob("*")
            if p.is_file() and p.name != ".gitkeep"
        ]
        if evidence:
            raise SystemExit(f"qualification root not fresh: {QUAL_ROOT} ({evidence})")
    r2.FROZEN_UNIT_ORDER = QUAL_UNIT_ORDER
    r2.RUN_ROOT = QUAL_ROOT
    r2.EXPECTED_RUN_ROOT = QUAL_ROOT
    r2.EXPECTED_RUN_ROOT_STR = str(QUAL_ROOT)
    r2.FREEZE_DIR = QUAL_ROOT / "freeze"
    r2.UNITS_DIR = QUAL_ROOT / "units"
    r2.LOGS_DIR = QUAL_ROOT / "logs"
    r2.PROGRESS_DIR = QUAL_ROOT / "progress"
    r2.MATERIALIZED_DIR = QUAL_ROOT / "materialized"
    r2.RECEIPTS_DIR = QUAL_ROOT / "receipts"
    r2.PROGRESS_JSON = r2.PROGRESS_DIR / "progress.json"
    r2.load_plan = qual_plan
    for d in (r2.FREEZE_DIR, r2.UNITS_DIR, r2.LOGS_DIR, r2.PROGRESS_DIR,
              r2.MATERIALIZED_DIR, r2.RECEIPTS_DIR):
        d.mkdir(parents=True, exist_ok=True)


def verify_images() -> list[dict]:
    plan = qual_plan()
    out: list[dict] = []
    for idx, unit in enumerate(plan["calibration_units"], start=1):
        info = r2.verify_execution_image_binding(
            unit["docker_profile_id"], unit["native_profile_id"], uid=unit["validation_unit_id"]
        )
        out.append(
            {
                "index": idx,
                "validation_unit_id": unit["validation_unit_id"],
                "execution_image_ref": info["execution_image_ref"],
                "immutable_image_id": info["immutable_image_id"],
                "verified": True,
            }
        )
    return out


def main() -> None:
    configure_runner()
    images = verify_images()
    print("IMAGE_BINDING_VERIFIED", len(images))

    results: list[dict] = []
    for idx in range(1, len(QUAL_UNIT_ORDER) + 1):
        runner = r2.UnitRunner()
        record = runner.run_unit(idx)
        uid = record["validation_unit_id"]
        results.append(
            {
                "index": idx,
                "validation_unit_id": uid,
                "install_route": record["install_route"],
                "result": record["result"],
                "classification": record["classification"],
                "runtime_pins_count": record["runtime_pins_count"],
                "requirements_lock_sha256": record["requirements_lock_sha256"],
                "immutable_image_id": record["immutable_image_id"],
                "elapsed_seconds": record["elapsed_seconds"],
                "evidence_dir": str(r2.UNITS_DIR / uid),
            }
        )
        print(
            f"UNIT {idx} {uid} -> {record['result']} ({record['classification']}) "
            f"pins={record['runtime_pins_count']}"
        )
        if record["result"] != "PASS":
            print("FIRST_MANDATORY_FAILURE_STOP")
            break

    payload = {
        "artifact": "R4_POETRY_CLOSURE_SUCCESSOR_QUALIFICATION_EVIDENCE",
        "schema_version": "env-canon-r4/poetry-closure-successor/qualification/1.0",
        "mission_id": "M17_D7_R4_POETRY_CLOSURE_SUCCESSOR_QUALIFICATION",
        "run_root": str(QUAL_ROOT),
        "unit_order": list(QUAL_UNIT_ORDER),
        "image_bindings": images,
        "results": results,
        "n_pass": sum(1 for r in results if r["result"] == "PASS"),
        "n_fail": sum(1 for r in results if r["result"] != "PASS"),
        "all_pass": all(r["result"] == "PASS" for r in results),
        "stopped_early": len(results) < len(QUAL_UNIT_ORDER),
    }
    out = QUAL_ROOT / "receipts" / "QUALIFICATION_EVIDENCE.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("QUALIFICATION_EVIDENCE=" + str(out))


if __name__ == "__main__":
    main()