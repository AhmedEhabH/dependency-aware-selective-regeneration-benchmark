#!/usr/bin/env python3
"""RUN_TO_RUN_DETERMINISM_SECONDARY_ANALYSIS (frozen prospective comparator).

MISSION: M17_D7_R4_POSTQUAL_SUCCESSOR_PREEXECUTION_FREEZE (Task H).

Prospectively specified BEFORE the successor scientific Full144 run, AFTER
observing the successful non-scientific R3.1 FULL144 qualification result.
This is a SECONDARY reproducibility analysis and is NOT evidence preregistered
before the qualification and does NOT replace or redefine the primary
scientific Full144 analysis.

Compares, per exact validation unit, the non-scientific R3.1 FULL144
qualification run root (A) and the successor scientific Full144 run root (B):

  primary compared fields : result, classification         (frozen schemas)
  additional predeclared   : immutable_image_id,
                             requirements_lock_sha256,
                             runtime_pins_count,
                             resolved_wheels_count
                             (schema env-canon-r4-full144/1.0 per-unit result.json)

Outputs:
  agreement_count / 144, disagreement_count, exact disagreement unit_ids, and
  per-unit compared-field deltas.

Any disagreement is reported as INSTABILITY, is investigated, and is NEVER
resolved by selectively rerunning/replacing the disagreeing unit.  It does not
silently rewrite either run's evidence.  This script never mutates either run
root.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

R3_1_QUALIFICATION_ROOT = Path(r"D:\WP2\runs\r4-successor-r3-qualification144-2026-10-16")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SystemExit(f"missing artifact: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"artifact {path} is not a JSON object")
    return data


def _frame(path: Path) -> dict[str, Any]:
    rec = _read_json(path)
    return {
        "validation_unit_id": rec.get("validation_unit_id"),
        "result": rec.get("result"),
        "classification": rec.get("classification"),
        "immutable_image_id": rec.get("immutable_image_id"),
        "requirements_lock_sha256": rec.get("requirements_lock_sha256"),
        "runtime_pins_count": rec.get("runtime_pins_count"),
        "resolved_wheels_count": (rec.get("artifact_provenance") or {}).get("resolved_wheels"),
    }


def ordered_unit_ids(root_a: Path) -> list[str]:
    prog = root_a / "R3_PROGRESS.json"
    if prog.is_file():
        comp = _read_json(prog).get("completed", [])
        ids = [str(c["validation_unit_id"]) for c in comp]
        if len(ids) == 144 and len(set(ids)) == 144:
            return ids
    receipt = root_a / "R3_SELECTION_RECEIPT.json"
    if receipt.is_file():
        units = _read_json(receipt).get("units", [])
        ids = [str(u["validation_unit_id"]) for u in units]
        if len(ids) == 144 and len(set(ids)) == 144:
            return ids
    raise SystemExit(f"cannot derive 144 ordered unit ids from {root_a}")


def compare(result_dir_b: Path) -> dict[str, Any]:
    ids = ordered_unit_ids(R3_1_QUALIFICATION_ROOT)
    b_units = result_dir_b / "units"

    disagreements: list[dict[str, Any]] = []
    compared = 0
    per_unit: list[dict[str, Any]] = []

    for idx, uid in enumerate(ids, start=1):
        a_path = R3_1_QUALIFICATION_ROOT / "units" / uid / "result.json"
        b_path = b_units / uid / "result.json"
        a = _frame(a_path)
        if not b_path.is_file():
            disagreements.append({"validation_unit_id": uid, "reason": "MISSING_B_UNIT_EVIDENCE"})
            per_unit.append({"index": idx, "validation_unit_id": uid, "agreement": False})
            continue
        b = _frame(b_path)

        fields = [
            "result",
            "classification",
            "immutable_image_id",
            "requirements_lock_sha256",
            "runtime_pins_count",
            "resolved_wheels_count",
        ]
        deltas = {f: {"A": a.get(f), "B": b.get(f)} for f in fields if a.get(f) != b.get(f)}
        agree = not deltas
        compared += 1
        per_unit.append({"index": idx, "validation_unit_id": uid, "agreement": agree})
        if deltas:
            disagreements.append({"validation_unit_id": uid, "deltas": deltas})

    return {
        "title": "RUN_TO_RUN_DETERMINISM_SECONDARY_ANALYSIS",
        "compared": compared,
        "total_units": len(ids),
        "agreement_count": compared - len(disagreements),
        "disagreement_count": len(disagreements),
        "disagreement_unit_ids": [d["validation_unit_id"] for d in disagreements],
        "disagreements": disagreements,
        "per_unit": per_unit,
        "verdict": "STABLE" if not disagreements else "INSTABILITY",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="RUN_TO_RUN_DETERMINISM_SECONDARY_ANALYSIS")
    ap.add_argument("--result-dir-b", required=True, help="successor scientific Full144 run root (B)")
    args = ap.parse_args()

    out = compare(Path(args.result_dir_b))
    print(json.dumps(out, indent=2, sort_keys=True))
    print(
        f"RUN_TO_RUN agreement={out['agreement_count']}/{out['total_units']} "
        f"disagreements={out['disagreement_count']} verdict={out['verdict']}"
    )
    return 1 if out["disagreement_count"] else 0


if __name__ == "__main__":
    sys.exit(main())
