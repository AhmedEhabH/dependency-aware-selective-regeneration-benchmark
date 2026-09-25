#!/usr/bin/env python3
"""WP-2 unchanged-test P2P candidate inventory V1 (amendment J) - ZERO API.

Deterministic inventory of candidate UNCHANGED tests associated with
modules/packages touched by each task (V1 rule: same top-level Saleor app as
any touched production file; test file unchanged by the target commit).

Node-level stable 3/3 pass on BOTH parent and target requires the Linux oracle
sweep; this inventory records the deterministic association and marks node
outcomes as PENDING the sweep. The candidate set is evaluator-only and invisible
to future generation/repair. Creating the inventory is NOT final preservation
validation (E2E-G6 remains the final rule).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

from benchmark.wp2.p2p_inventory_v1 import (  # noqa: E402
    P2P_INVENTORY_VERSION,
    associate_unchanged_test_files,
    top_level_app,
)

CACHE = PROJECT / "dist" / "pilot-repo-cache" / "saleor"
CENSUS = PROJECT / "research" / "wp2" / "wp2_saleor_main297_census_2026-09-22.json"
OUT = PROJECT / "research" / "wp2" / "wp2_unchanged_p2p_candidate_inventory_v1_2026-09-23.json"


def git(cache: Path, *args: str) -> subprocess.CompletedProcess[str]:
    cmd = ["git", "-C", str(cache), *args]
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=False)


def all_test_files_at_target(cache: Path, target: str) -> list[str]:
    r = git(cache, "ls-tree", "-r", "--name-only", target)
    from benchmark.wp2.oracle_semantics_v2 import is_test_path_v2
    return [p for p in r.stdout.splitlines() if is_test_path_v2(p)]


def main() -> int:
    census = {t["task_id"]: t for t in json.loads(CENSUS.read_text(encoding="utf-8"))["tasks"]}
    rows = []
    for tid in sorted(census):
        c = census[tid]
        if not c.get("changed_paths"):
            continue
        target = c["target_commit"]
        diff_paths = {cp["path"] for cp in c["changed_paths"]}
        from benchmark.wp2.oracle_semantics_v2 import is_test_path_v2
        touched_prod = [cp["path"] for cp in c["changed_paths"] if not is_test_path_v2(cp["path"])]
        all_tests = all_test_files_at_target(CACHE, target)
        associated = associate_unchanged_test_files(
            touched_production_files=touched_prod,
            all_test_files=all_tests,
            target_diff_paths=diff_paths,
        )
        rows.append({
            "task_id": tid,
            "target_commit": target,
            "touched_production_apps": sorted({top_level_app(p) for p in touched_prod}),
            "n_associated_unchanged_test_files": len(associated),
            "associated_unchanged_test_files": associated,
            "node_outcomes_status": "PENDING_LINUX_ORACLE_SWEEP",
        })

    artifact = {
        "artifact": "wp2_unchanged_p2p_candidate_inventory_v1",
        "date": "2026-09-23",
        "inventory_version": P2P_INVENTORY_VERSION,
        "rule": (
            "unchanged test file, same top-level Saleor app as touched "
            "production file; deterministic association (amendment J V1); "
            "node-level stable 3/3 pass on BOTH parent and target pending the "
            "Linux oracle sweep; coverage-based association is NOT primary V1"
        ),
        "evaluator_only": True,
        "invisible_to_generation_and_repair": True,
        "preservation_validation_complete": False,
        "final_oracle_rule": "E2E-G6 (frozen later)",
        "n_tasks": len(rows),
        "tasks": rows,
    }
    OUT.write_text(json.dumps(artifact, indent=1, ensure_ascii=False), encoding="utf-8")
    print("n_tasks:", len(rows))
    with_assoc = sum(1 for r in rows if r["n_associated_unchanged_test_files"] > 0)
    print("tasks with >=1 associated unchanged test file:", with_assoc)
    print("wrote", OUT.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
