#!/usr/bin/env python3
"""R4 Poetry Closure Successor — S5 delta-only local artifact readiness.

Mission M17_D7_R4_POETRY_CLOSURE_SUCCESSOR_QUALIFICATION.

For every requirement newly restored (or otherwise changed) by the S4
population audit, use ONLY the already-qualified local artifact resolution
machinery and stores:

* qualified R4-A era-aware wheel resolution (``runtime_pins`` ->
  ``_resolve_pin_wheels``) against the local merged wheelhouse
  (``wheelhouse/<era>`` + ``built_wheelhouse/canon_r4b/<era>``);
* R4-C materialization is NOT executed here (no container, no Linux tree).

No network, no download, no Docker pull, no source acquisition, no image
build.  This is a delta-only readiness check derived from S4.

Required terminal result: 0 unresolved newly-required runtime artifacts.
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

AUDIT = PROJECT / "research" / "env-canon-r4" / "R4_POETRY_CLOSURE_SUCCESSOR_POPULATION_AUDIT.json"

ERA_BY_PYVER = {"3.12": "py312", "3.9": "py39", "3.8": "py38"}


def main() -> None:
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    changed = [r for r in audit["units"] if r["added_requirements"] or r["removed_requirements"]]
    if not changed:
        print("NO_CHANGED_UNITS")
        return

    total_added: set[str] = set()
    rows: list[dict] = []
    for row in changed:
        uid = row["validation_unit_id"]
        era = ERA_BY_PYVER.get(row["python_version"])
        if era is None:
            raise SystemExit(f"no era for {uid} py {row['python_version']}")
        added = row["added_requirements"]
        total_added |= set(added)
        r2.build_merged_wheelhouse(era)
        resolution = r2._resolve_pin_wheels(sorted(added), era)
        rows.append(
            {
                "validation_unit_id": uid,
                "install_route": row["install_route"],
                "python_version": row["python_version"],
                "wheelhouse_era": era,
                "added_count": len(added),
                "resolved_count": len(resolution["resolved"]),
                "missing": resolution["missing"],
                "incompatible": resolution["incompatible"],
                "resolved_sample": sorted(resolution["resolved"])[:10],
            }
        )

    n_missing = sum(len(r["missing"]) for r in rows)
    n_incompatible = sum(len(r["incompatible"]) for r in rows)

    payload = {
        "artifact": "R4_POETRY_CLOSURE_SUCCESSOR_DELTA_ARTIFACT_READINESS",
        "schema_version": "env-canon-r4/poetry-closure-successor/delta-artifact-readiness/1.0",
        "mission_id": "M17_D7_R4_POETRY_CLOSURE_SUCCESSOR_QUALIFICATION",
        "source_audit": str(AUDIT),
        "n_changed_units": len(changed),
        "n_unique_added_requirements": len(total_added),
        "n_unresolved_newly_required": n_missing + n_incompatible,
        "resolved_ok": (n_missing == 0 and n_incompatible == 0),
        "units": rows,
    }
    out = PROJECT / "research" / "env-canon-r4" / "R4_POETRY_CLOSURE_SUCCESSOR_DELTA_ARTIFACT_READINESS.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "n_changed_units": len(changed),
                "n_unique_added_requirements": len(total_added),
                "n_unresolved_newly_required": n_missing + n_incompatible,
                "resolved_ok": payload["resolved_ok"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    print("READINESS_OUT=" + str(out))


if __name__ == "__main__":
    main()
