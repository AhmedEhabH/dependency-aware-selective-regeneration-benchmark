#!/usr/bin/env python3
"""M17 S2 - population-wide dependency source-type audit.

Writes ``research/source-fidelity-r1/D7_DEPENDENCY_SOURCE_TYPE_AUDIT.csv``.

Classifies the historical lock source semantics of every dependency across the
frozen D7 population (219 tasks / 144 validation units / 184 poetry + 35 uv
locks) and determines where the current name/version-only canon loses source
identity.  This is a static, offline read of the read-only store.

Columns:
validation_unit_id, task_id, target_commit, package, version,
historical_source_type, historical_source_reference, source_tree_sha256,
current_canon_representation, source_identity_preserved, risk_class
"""
from __future__ import annotations

import csv
import sys
import tomllib
from collections import Counter
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(SRC_DIR))

from benchmark.wp2 import source_fidelity_r1 as sf  # noqa: E402

LOCK_DIR = Path(r"D:\wp2_env_store\artifacts\locks")
STORE_MANIFESTS = Path(r"D:\wp2_env_store\manifests")
OUT = Path(__file__).resolve().parent / "D7_DEPENDENCY_SOURCE_TYPE_AUDIT.csv"


def _load_task_units() -> dict[str, str]:
    """task_id -> validation_unit_id (and target_commit) from the frozen matrices."""
    task_commit: dict[str, str] = {}
    with open(STORE_MANIFESTS / "TASK_ENV_MATRIX.csv", newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            task_commit[row["task_id"]] = row["target_commit"]
    task_unit: dict[str, str] = {}
    with open(STORE_MANIFESTS / "VALIDATION_UNIT_MATRIX.csv", newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            for tid in row["member_task_ids"].split(";"):
                task_unit[tid] = row["unit_id"]
    return task_unit, task_commit


def main() -> int:
    task_unit, task_commit = _load_task_units()
    rows: list[dict[str, str]] = []
    counts: Counter = Counter()
    source_loss_tasks: set[str] = set()

    for lock_path in sorted(LOCK_DIR.glob("saleor-rc-*_*.toml")):
        task_id = lock_path.name.removesuffix("_poetry.toml").removesuffix("_uv.toml")
        lock_format = "uv" if lock_path.name.endswith("_uv.toml") else "poetry"
        unit = task_unit.get(task_id, "")
        commit = task_commit.get(task_id, "")
        with open(lock_path, "rb") as fh:
            data = tomllib.load(fh)
        for pkg in data.get("package", []):
            name = str(pkg.get("name", ""))
            version = str(pkg.get("version", ""))
            source = pkg.get("source")
            try:
                if lock_format == "uv":
                    source_type, reference = sf.classify_uv_source(source)
                else:
                    source_type, reference = sf.classify_poetry_source(source)
            except sf.AmbiguousSourceIdentity as exc:
                source_type, reference = sf.SOURCE_TYPE_UNKNOWN, str(exc)
            editable_self = lock_format == "uv" and sf.uv_editable_self(source)
            preserved = editable_self or source_type == sf.SOURCE_TYPE_REGISTRY
            risk = "NONE" if preserved else "HIGH"
            counts[source_type] += 1
            if not preserved:
                source_loss_tasks.add(task_id)
            canon_repr = (
                "editable self (task checkout at target commit)"
                if editable_self
                else f"{name}=={version}"
            )
            rows.append(
                {
                    "validation_unit_id": unit,
                    "task_id": task_id,
                    "target_commit": commit,
                    "package": name,
                    "version": version,
                    "historical_source_type": source_type,
                    "historical_source_reference": reference or "",
                    "source_tree_sha256": "",
                    "current_canon_representation": canon_repr,
                    "source_identity_preserved": str(preserved).upper(),
                    "risk_class": risk,
                }
            )

    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "validation_unit_id", "task_id", "target_commit", "package",
                "version", "historical_source_type",
                "historical_source_reference", "source_tree_sha256",
                "current_canon_representation", "source_identity_preserved",
                "risk_class",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    units = sorted({r["validation_unit_id"] for r in rows if r["source_identity_preserved"] == "FALSE"})
    print(f"rows: {len(rows)}")
    print("source_type_counts:", dict(counts))
    print(f"source_loss_tasks: {sorted(source_loss_tasks)}")
    print(f"source_loss_units: {units}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())