#!/usr/bin/env python3
"""WP-2 MAIN 220 Linux V2 summary + temporal strata (C2 acceptance) - ZERO API.

Reads per_task_v2.jsonl and produces the honest C2 summary:
- attempted / environment-install-failed / executable;
- primary behavioral eligible / symbol-absence / extended;
- per-era yields;
- temporal strata by target commit year;
- node-level classification counts.

Windows->Linux reconciliation is reported separately (docs).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

RUN_ROOT = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23"
PER_TASK = RUN_ROOT / "per_task_v2.jsonl"
CENSUS = PROJECT / "research" / "wp2" / "wp2_saleor_main297_census_2026-09-22.json"
CACHE = PROJECT / "dist" / "pilot-repo-cache" / "saleor"
OUT = RUN_ROOT / "summary_v2.json"


def git(cache: Path, *args: str) -> subprocess.CompletedProcess[str]:
    cmd = ["git", "-C", str(cache), *args]
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=False)


def commit_year(cache: Path, commit: str) -> int | None:
    r = git(cache, "log", "-1", "--format=%ct", commit)
    if r.returncode != 0 or not r.stdout.strip():
        return None
    import datetime
    return datetime.datetime.utcfromtimestamp(int(r.stdout.strip())).year


def main() -> int:
    rows = [json.loads(line) for line in PER_TASK.read_text(encoding="utf-8").splitlines() if line.strip()]
    census = {t["task_id"]: t for t in json.loads(CENSUS.read_text(encoding="utf-8"))["tasks"]}

    def is_env_failed(r: dict) -> bool:
        return sum(r.get("counts", {}).values()) == 0 and r.get("eligibility", {}).get("task_collection_failure", False)

    env_failed = [r for r in rows if is_env_failed(r)]
    executable = [r for r in rows if not is_env_failed(r)]
    behavioral = [r for r in rows if r.get("counts", {}).get("BEHAVIORAL_F2P", 0) > 0]
    symbol = [r for r in rows if r.get("counts", {}).get("SYMBOL_ABSENCE_F2P", 0) > 0]
    primary = [r for r in rows if r.get("eligibility", {}).get("PRIMARY_BEHAVIORAL_F2P_ELIGIBLE", False)]
    extended = sorted({r["task_id"] for r in behavioral} | {r["task_id"] for r in symbol})

    era_yield: dict[str, dict] = {}
    for era in sorted({r.get("era_key") for r in rows}):
        era_rows = [r for r in rows if r.get("era_key") == era]
        era_yield[era] = {
            "attempted": len(era_rows),
            "env_failed": sum(1 for r in era_rows if is_env_failed(r)),
            "executable": sum(1 for r in era_rows if not is_env_failed(r)),
            "behavioral_tasks": sum(1 for r in era_rows if r.get("counts", {}).get("BEHAVIORAL_F2P", 0) > 0),
            "symbol_tasks": sum(1 for r in era_rows if r.get("counts", {}).get("SYMBOL_ABSENCE_F2P", 0) > 0),
        }

    strata: dict[str, dict] = {}
    for r in rows:
        year = commit_year(CACHE, census.get(r["task_id"], {}).get("target_commit", ""))
        key = str(year or "UNKNOWN")
        s = strata.setdefault(key, {"attempted": 0, "env_failed": 0, "executable": 0,
                                    "behavioral_tasks": 0, "symbol_tasks": 0})
        s["attempted"] += 1
        if is_env_failed(r):
            s["env_failed"] += 1
        else:
            s["executable"] += 1
        if r.get("counts", {}).get("BEHAVIORAL_F2P", 0) > 0:
            s["behavioral_tasks"] += 1
        if r.get("counts", {}).get("SYMBOL_ABSENCE_F2P", 0) > 0:
            s["symbol_tasks"] += 1

    node_counts = {}
    for f in ("BEHAVIORAL_F2P", "SYMBOL_ABSENCE_F2P", "PARENT_COLLECTION_ERROR",
              "FLAKY", "TARGET_ORACLE_INVALID", "P2P_ONLY", "OTHER_REVIEW_REQUIRED"):
        node_counts[f] = sum(r.get("counts", {}).get(f, 0) for r in rows)

    summary = {
        "artifact": "wp2_main_linux_v2_summary",
        "date": "2026-09-23",
        "attempted": len(rows),
        "environment_install_failed": len(env_failed),
        "executable": len(executable),
        "primary_behavioral_eligible_tasks": len(primary),
        "symbol_absence_tasks": len(symbol),
        "extended_f2p_eligible_tasks": len(extended),
        "behavioral_task_ids": sorted(r["task_id"] for r in behavioral),
        "symbol_task_ids": sorted(r["task_id"] for r in symbol),
        "era_yield": era_yield,
        "temporal_strata_by_target_year": dict(sorted(strata.items())),
        "node_classification_counts": node_counts,
        "windows_v1_reference": {
            "attempted": 220,
            "environment_valid": 13,
            "behavioral_eligible_tasks": 8,
            "symbol_eligible_tasks": 1,
            "env_broken": 207,
        },
        "note": (
            "environment_install_failed tasks have all-zero node counts with "
            "task_collection_failure=True (genuine era dependency/native-lib "
            "attrition, not a harness defect); classification fields carry "
            "the per-task truth"
        ),
    }
    OUT.write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "attempted": len(rows),
        "environment_install_failed": len(env_failed),
        "executable": len(executable),
        "primary_behavioral_eligible_tasks": len(primary),
        "symbol_absence_tasks": len(symbol),
        "extended_f2p_eligible_tasks": len(extended),
        "era_yield": era_yield,
        "node_classification_counts": node_counts,
    }, indent=1))
    print("wrote", OUT.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
