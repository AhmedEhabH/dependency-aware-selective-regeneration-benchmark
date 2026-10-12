#!/usr/bin/env python3
"""M17 S9 - population closure identity impact audit (NO Full D7).

Recomputes, for every one of the 144 frozen validation units, the OLD canon
closure identity (name/version-flattened pins, the D7 R3 closure semantics)
and the NEW source-aware closure identity, and reports which units' source
identity is affected.  Pure static read of the store + local Git objects.

Writes ``research/source-fidelity-r1/POPULATION_CLOSURE_IMPACT_R1.json``.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(SRC_DIR))

from benchmark.wp2 import source_fidelity_r1 as sf  # noqa: E402

LOCK_DIR = Path(r"D:\wp2_env_store\artifacts\locks")
STORE_MANIFESTS = Path(r"D:\wp2_env_store\manifests")
REPO = r"C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\dist\pilot-repo-cache\saleor"
OUT = Path(__file__).resolve().parent / "POPULATION_CLOSURE_IMPACT_R1.json"


def main() -> int:
    task_commit: dict[str, str] = {}
    with open(STORE_MANIFESTS / "TASK_ENV_MATRIX.csv", newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            task_commit[row["task_id"]] = row["target_commit"]

    units: list[dict] = []
    with open(STORE_MANIFESTS / "VALIDATION_UNIT_MATRIX.csv", newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            members = [t for t in row["member_task_ids"].split(";") if t]
            units.append(
                {
                    "validation_unit_id": row["unit_id"],
                    "members": members,
                    "lock_type": row["lock_type"],
                }
            )

    changed: list[dict] = []
    unchanged: list[dict] = []
    for unit in sorted(units, key=lambda u: u["validation_unit_id"]):
        first_task = unit["members"][0]
        lock_path = LOCK_DIR / f"{first_task}_{unit['lock_type']}.toml"
        lock_text = lock_path.read_text(encoding="utf-8")
        commit = task_commit.get(first_task, "")
        closure = sf.derive_source_aware_closure(
            lock_text, commit, REPO, python_version="3.12", lock_format=unit["lock_type"],
        )
        old_pins = sorted({p.split("@", 1)[0] for p in closure["pins"]})
        old_identity = sf.closure_identity_sha256(old_pins)
        new_identity = closure["closure_identity_sha256"]
        affected_sources = sorted(
            {
                (r["name"], r["source_type"], r.get("source_reference") or "")
                for r in closure["records"]
                if r["source_type"] != sf.SOURCE_TYPE_REGISTRY
            }
        )
        entry = {
            "validation_unit_id": unit["validation_unit_id"],
            "member_task_ids": unit["members"],
            "lock_type": unit["lock_type"],
            "n_pins_old": len(old_pins),
            "n_pins_new": len(closure["pins"]),
            "old_canon_closure_identity_sha256": old_identity,
            "new_source_aware_closure_identity_sha256": new_identity,
            "source_identity_change": bool(affected_sources),
            "non_registry_sources": affected_sources,
            "n_fail_closed": closure["n_fail_closed"],
        }
        if affected_sources:
            changed.append(entry)
        else:
            unchanged.append(entry)

    report = {
        "mission": "M17_ENV_CANON_SOURCE_FIDELITY_AMENDMENT_R1_DESIGN_AND_FREEZE",
        "phase": "S9_POPULATION_CLOSURE_IMPACT_AUDIT",
        "full_d7_run": False,
        "n_units": len(units),
        "n_unchanged": len(unchanged),
        "n_changed": len(changed),
        "changed_unit_ids": sorted(u["validation_unit_id"] for u in changed),
        "changed_task_ids": sorted(
            tid for u in changed for tid in u["member_task_ids"]
        ),
        "changed": changed,
        "unchanged_unit_ids": sorted(u["validation_unit_id"] for u in unchanged),
        "why_changed": (
            "The old canon closure flattens every dependency to name==version "
            "and resolves the artifact by normalized distribution name/version, "
            "discarding the historical lock's directory-source identity.  The "
            "source-aware closure binds DIRECTORY/PATH dependencies to the exact "
            "historical source-tree hash at the target commit, so the closure "
            "identity changes only for units containing such dependencies.  The "
            "source-type audit determined exactly 2 units (vu-b9808f19ace4, "
            "vu-692af9112c6d) contain directory-source packages; no new semantic "
            "rule is required."
        ),
        "note_old_identity": (
            "old_canon_closure_identity_sha256 is the amendment's deterministic "
            "recomputation of the name/version-flattened closure; the frozen R3 "
            "receipt's closure_identity_sha256 field is recorded there for the "
            "12 calibration units as historical reference and is not overwritten."
        ),
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(f"n_units={report['n_units']} n_unchanged={report['n_unchanged']} n_changed={report['n_changed']}")
    print("changed_units:", report["changed_unit_ids"])
    for u in changed:
        print(" ", u["validation_unit_id"], u["member_task_ids"])
        print("   old:", u["old_canon_closure_identity_sha256"])
        print("   new:", u["new_source_aware_closure_identity_sha256"])
        print("   sources:", u["non_registry_sources"])
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())