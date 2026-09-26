#!/usr/bin/env python3
"""WP-2 Mission-10B Phase 3: four-task ENG probe under Harness V3 (ZERO API).

Runs the full C4 changed-test oracle under the frozen Harness V3 candidate on
EXACTLY the four ENG probe tasks (workers=1, 3 parent + 3 target reps), and
produces the V2->V3 transition matrix + Phase-4 gate inputs.

Probe tasks (frozen order):
1. saleor-rc-c3b9e396b07d  py39  top ENG EMFILE example
2. saleor-rc-e25cf9b4a837  py38  strong py38 EMFILE example
3. saleor-rc-74538ea00ce9  py312 missing-dependency example (incl. JWT node)
4. saleor-rc-8f76ddc6267f  py39  cleaner V2 comparison task

Usage:
    python scripts/wp2_m10b_phase3_probe.py [--out DIR] [--task TID]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

from benchmark.wp2.harness_v3 import (  # noqa: E402
    base_image_id,
    clock_preflight,
    ensure_worktrees_v3,
    git_linux,
    lock_install_script,
    lockfile_sha256,
    now_utc,
    remove_worktrees_v3,
    run_state_v3,
    target_manifests,
)
from benchmark.wp2.oracle_semantics_v2 import classify_node_v2  # noqa: E402
from benchmark.wp2.oracle_semantics_v2 import (  # noqa: E402
    task_eligibility_v2 as _task_eligibility_v2,
)

V2_ROOT = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23"
OUT_ROOT = PROJECT / "research" / "wp2" / "harness_v3_2026-09-26"

PROBE_TASKS = [
    "saleor-rc-c3b9e396b07d",
    "saleor-rc-e25cf9b4a837",
    "saleor-rc-74538ea00ce9",
    "saleor-rc-8f76ddc6267f",
]

REPS = 3
WSL_CACHE = "/opt/wp2_v2/saleor-cache"


def git_local(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(PROJECT), *args],
                          capture_output=True, text=True, encoding="utf-8", check=False)


def load_v2_task(task_id: str) -> dict:
    for line in (V2_ROOT / "per_task_dev_v2.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["task_id"] == task_id:
            return r
    raise RuntimeError(f"task {task_id} not in per_task_dev_v2")


def load_v2_per_test(task_id: str) -> dict[str, dict]:
    out = {}
    for line in (V2_ROOT / "per_test_dev_v2.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["task_id"] == task_id:
            out[r["node_id"]] = r
    return out


def task_commits(task_id: str) -> tuple[str, str]:
    census = json.loads((V2_ROOT / "dev_census_2026-09-23.json").read_text(encoding="utf-8"))
    for t in census.get("tasks", []):
        if t["task_id"] == task_id:
            return t["parent_commit"], t["target_commit"]
    raise RuntimeError(f"{task_id} not in census")


def changed_test_files(parent: str, target: str) -> list[str]:
    r = git_linux(WSL_CACHE, "diff", "--name-only", parent, target)
    return sorted(ln.strip() for ln in r.stdout.splitlines()
                  if ln.strip().endswith(".py") and "/test" in ln)


def run_probe_task(task_id: str, out_root: Path) -> dict:
    parent, target = task_commits(task_id)
    v2_task = load_v2_task(task_id)
    era_key = v2_task["era_key"]
    v2_per_test = load_v2_per_test(task_id)
    test_files = changed_test_files(parent, target)
    print(f"[P3] {task_id} era={era_key} test_files={test_files}", flush=True)

    # clock preflight
    clock = clock_preflight()
    print(f"  clock: {clock['verdict']} pre={clock['pre']['median_skew_s']:+.3f}s")

    manifests = target_manifests(target)
    install_frag, install_mode, install_evidence = lock_install_script(
        "/x", manifests)
    wts = ensure_worktrees_v3(task_id, parent, target)
    tid = task_id.split("-")[-1][:12]
    img_id = base_image_id(era_key)

    # target state
    t0 = time.monotonic()
    tgt = run_state_v3(era_key=era_key, worktree_linux=wts["t"], tid=tid,
                       state="t", test_files=test_files,
                       install_fragment=install_frag, timeout_s=7200)
    t_wall = round(time.monotonic() - t0, 1)
    par = run_state_v3(era_key=era_key, worktree_linux=wts["p"], tid=tid,
                       state="p", test_files=test_files,
                       install_fragment=install_frag, timeout_s=7200)
    p_wall = round(time.monotonic() - t0, 1)

    # classify nodes with the SAME frozen oracle semantics v2
    all_nodes = sorted(set(tgt["junit"]) | set(par["junit"]))
    counts = {"BEHAVIORAL_F2P": 0, "SYMBOL_ABSENCE_F2P": 0, "PARENT_COLLECTION_ERROR": 0,
              "FLAKY": 0, "TARGET_ORACLE_INVALID": 0, "P2P_ONLY": 0,
              "OTHER_REVIEW_REQUIRED": 0}
    node_records = []
    for node in all_nodes:
        t_out = tgt["junit"].get(node, "missing")
        p_out = par["junit"].get(node, "missing")
        t_list = t_out if isinstance(t_out, list) else [t_out] * 3
        p_list = p_out if isinstance(p_out, list) else [p_out] * 3
        cls = classify_node_v2(
            target_outcomes=list(t_list),
            parent_outcomes=list(p_list),
            parent_failure_text=par["junit_failures"].get(node, ""),
            parent_collects_node=node in par["junit"],
            shared_test_support_failed=node not in par["junit"],
        )
        counts[cls] += 1
        node_records.append({
            "node_id": node, "v3_class": cls,
            "target_outcomes": list(t_list), "parent_outcomes": list(p_list),
            "v2_class": v2_per_test.get(node, {}).get("classification", "ABSENT_IN_V2"),
        })

    # eligibility under frozen semantics v2
    flags = _task_eligibility_v2(
        n_behavioral_f2p=counts["BEHAVIORAL_F2P"],
        n_symbol_absence_f2p=counts["SYMBOL_ABSENCE_F2P"],
        n_parent_collection_error=counts["PARENT_COLLECTION_ERROR"],
        environment_valid=True,
        task_collection_failure=False,
    )

    # transition matrix V2 -> V3 (node-level, from v2_per_test)
    transitions: dict[str, dict] = {}
    regressions = 0
    for rec in node_records:
        nid = rec["node_id"]
        v2 = rec["v2_class"]
        v3 = rec["v3_class"]
        if v2 in ("BEHAVIORAL_F2P", "SYMBOL_ABSENCE_F2P", "P2P_ONLY") and v2 != v3:
            transitions[nid] = {"v2": v2, "v3": v3, "outcomes": rec}
            if v2 in ("BEHAVIORAL_F2P", "SYMBOL_ABSENCE_F2P") and v3 in ("P2P_ONLY", "TARGET_ORACLE_INVALID"):
                regressions += 1

    # integrity
    v2_ids = set(v2_per_test)
    v3_ids = set(node_records)
    integrity = {
        "n_v2_nodes": len(v2_ids),
        "n_v3_nodes": len(v3_ids),
        "missing_in_v3": sorted(v2_ids - v3_ids),
        "orphan_in_v3": sorted(v3_ids - v2_ids),
        "ok": not (v2_ids - v3_ids) and not (v3_ids - v2_ids),
    }

    harness_sha = git_local("rev-parse", "HEAD").stdout.strip()
    result = {
        "task_id": task_id,
        "era_key": era_key,
        "parent_commit": parent,
        "target_commit": target,
        "test_files": test_files,
        "v2": {
            "classification": v2_task.get("classification"),
            "counts": v2_task.get("counts"),
            "eligibility": v2_task.get("eligibility"),
            "n_nodes": v2_task.get("n_nodes"),
        },
        "v3": {
            "classification": "BEHAVIORAL_F2P" if flags["PRIMARY_BEHAVIORAL_F2P_ELIGIBLE"] else "NOT_PRIMARY",
            "counts": counts,
            "eligibility": flags,
            "n_nodes": len(all_nodes),
            "primary_eligible": flags["PRIMARY_BEHAVIORAL_F2P_ELIGIBLE"],
        },
        "clock_preflight": clock,
        "install": {"mode": install_mode, "evidence": install_evidence},
        "manifest": {
            "task_id": task_id,
            "target_commit": target,
            "era": era_key,
            "frozen_base_image_id": img_id,
            "harness_v3_version": "wp2-harness-v3-2026-09-26",
            "runner_sha": harness_sha,
            "install_mode": install_mode,
            "lockfile_sha256": lockfile_sha256(manifests),
            "nofile_soft": 65536,
            "nofile_hard": 65536,
            "clock_pre_post": {
                "pre": clock["pre"]["median_skew_s"],
                "post": (clock.get("post") or {}).get("median_skew_s"),
            },
            "worker_count": 1,
            "db_names": {"t": tgt.get("db_name"), "p": par.get("db_name")},
        },
        "operations": {
            "target_wall_s": t_wall,
            "parent_wall_s": p_wall,
            "target_error": tgt.get("error"),
            "parent_error": par.get("error"),
        },
        "node_records": node_records,
        "transitions": transitions,
        "regression_candidates": regressions,
        "integrity": integrity,
    }
    remove_worktrees_v3(task_id)
    (out_root / f"phase3_probe_{task_id}.json").write_text(
        json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"  V2 counts={v2_task.get('counts')}", flush=True)
    print(f"  V3 counts={counts} integrity={integrity['ok']} transitions={len(transitions)}",
          flush=True)
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--task", default=None)
    args = ap.parse_args()
    out_root = Path(args.out) if args.out else OUT_ROOT
    out_root.mkdir(parents=True, exist_ok=True)

    tasks = [args.task] if args.task else PROBE_TASKS
    results = {}
    for tid in tasks:
        results[tid] = run_probe_task(tid, out_root)
    with (out_root / "phase3_probe_summary.json").open("w", encoding="utf-8") as fh:
        json.dump({"artifact": "m10b_phase3_probe_summary",
                   "created_utc": now_utc(), "tasks": results}, fh,
                  indent=1, ensure_ascii=False)
    print(f"[P3] complete {len(results)} tasks -> {out_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
