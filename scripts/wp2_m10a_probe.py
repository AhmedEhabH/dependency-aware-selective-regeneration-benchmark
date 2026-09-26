#!/usr/bin/env python3
"""WP-2 Mission-10A: optional ENG-only scratch environment probe (ZERO API).

NON-FROZEN, EXPLORATORY. Re-runs two logically distinct node sets per selected
ENG task in a scratch derivative of the frozen era image that ADDS the
project-declared historical test/dev dependency group that frozen V2 omitted.

  SET A - ERROR RECOVERY: V2 P2P-U COLLECTION_ERROR nodes attributable to the
          declared-but-missing dependency (count_queries/mocker).
  SET B - V2 NON-REGRESSION: all C4 DEV V2 nodes previously classified as
          BEHAVIORAL_F2P or P2P_ONLY for the task.

Scratch env = frozen era image + V2 deps_install_cmd + V2 TOOLING_INSTALL +
the omitted declared test/dev group at the exact historical locked versions.

All probe outputs are labeled NON_FROZEN_EXPLORATORY_ENV_PROBE and persisted
under research/wp2/mission10a_env_audit_2026-09-26/probe/<task>/. They are
NEVER merged into frozen V2 oracle artifacts.

Usage:
    python scripts/wp2_m10a_probe.py --task saleor-rc-74538ea00ce9 [--dry-run]
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

from benchmark.wp2.oracle_confirmation import parse_junit_with_failures  # noqa: E402
from benchmark.wp2.oracle_semantics_v2 import classify_node_v2  # noqa: E402
from scripts.wp2_linux_dryrun import (  # noqa: E402
    TOOLING_INSTALL,
    WSL_DISTRO,
    WSL_WT,
    deps_install_cmd,
    ensure_cache,
    ensure_era_images,
    ensure_postgres,
    wsl,
    wsl_docker,
)

OUT_ROOT = PROJECT / "research" / "wp2" / "mission10a_env_audit_2026-09-26"
PER_TEST_DEV = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23" / "per_test_dev_v2.jsonl"
CENSUS = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23" / "dev_census_2026-09-23.json"

REPS = 3

# Probe tasks frozen from probe_selection.json (deterministic, pre-probe).
PROBE_TASKS = {
    "saleor-rc-74538ea00ce9": {
        "era_key": "py312",
        "parent_commit": "edc4120f657f4620030d5bd8327883714b9e812b",
        "target_commit": "74538ea00ce938489bcd36b180e3b9b31f265e40",
        "python_requirement": "~3.12",
        "missing_packages": ["pytest-django-queries==1.2.0"],
        "dependency": "pytest-django-queries",
    },
    "saleor-rc-8f76ddc6267f": {
        "era_key": "py39",
        "parent_commit": "54fc7e6ef25f3662a53409af62b5784dc7b5f34f",
        "target_commit": "8f76ddc6267f6ddcdc6078f2a4a098bbb971b23b",
        "python_requirement": "~3.9",
        "missing_packages": ["pytest-django-queries==1.2.0"],
        "dependency": "pytest-django-queries",
    },
}


def ensure_postgres_running() -> None:
    """Start the wp2-pg container if it exists but is stopped; create via the
    shared helper only when absent. Guards against a name collision."""
    r = wsl("docker ps -a --filter 'name=^wp2-pg$' --format '{{.Names}}'")
    if "wp2-pg" in r.stdout:
        wsl_docker(["start", "wp2-pg"], timeout_s=120)
        time.sleep(3)
        return
    ensure_postgres()


def git_linux(workdir: str, *args: str) -> subprocess.CompletedProcess[str]:
    quoted = " ".join(f"'{a}'" for a in args)
    return wsl(f"git -C {workdir} {quoted}")


def derive_test_patch_linux(parent: str, target: str) -> str:
    from benchmark.wp2.oracle_semantics_v2 import is_test_path_v2

    r = git_linux("/opt/wp2_v2/saleor-cache", "diff", "--name-status", parent, target)
    paths = []
    for line in r.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and is_test_path_v2(parts[-1]):
            paths.append(parts[-1])
    if not paths:
        return ""
    r = git_linux("/opt/wp2_v2/saleor-cache", "diff", parent, target, "--", *paths)
    if r.returncode != 0:
        raise SystemExit(f"patch diff failed: {r.stderr}")
    return r.stdout


def ensure_worktrees(task_id: str, parent: str, target: str) -> dict:
    tid = task_id.split("-")[-1][:12]
    wt_t = f"{WSL_WT}/{tid}_m10a_probe_t"
    wt_p = f"{WSL_WT}/{tid}_m10a_probe_p"
    wsl(f"mkdir -p {WSL_WT}")
    wsl(f"git -C /opt/wp2_v2/saleor-cache worktree remove --force {wt_t} 2>/dev/null || rm -rf {wt_t}")
    wsl(f"git -C /opt/wp2_v2/saleor-cache worktree remove --force {wt_p} 2>/dev/null || rm -rf {wt_p}")
    r = git_linux("/opt/wp2_v2/saleor-cache", "worktree", "add", "--detach", wt_t, target)
    if r.returncode != 0:
        raise SystemExit(f"[wt] target add FAILED: {r.stderr[-1200:]}")
    r = git_linux("/opt/wp2_v2/saleor-cache", "worktree", "add", "--detach", wt_p, parent)
    if r.returncode != 0:
        raise SystemExit(f"[wt] parent add FAILED: {r.stderr[-1200:]}")
    patch = derive_test_patch_linux(parent, target)
    if patch:
        proc = subprocess.run(
            ["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc",
             "cat > /opt/wp2_v2/m10a_probe.patch"],
            input=patch.encode("utf-8"), capture_output=True, timeout=120,
        )
        if proc.returncode != 0:
            raise SystemExit(f"[wt] patch write FAILED: {proc.stderr[-500:]}")
        ap = git_linux(wt_p, "apply", "/opt/wp2_v2/m10a_probe.patch")
        if ap.returncode != 0:
            raise SystemExit(f"[wt] parent patch apply FAILED: {ap.stderr[-800:]}")
    return {"t": wt_t, "p": wt_p}


def run_probe_state(
    *,
    era_key: str,
    worktree_linux: str,
    tid: str,
    state: str,
    node_ids: list[str],
    missing_packages: list[str],
    timeout_s: int = 28800,
) -> dict:
    """One scratch container per state. V2 install + missing declared group,
    then 3 pytest invocations over the probe node set with per-run JUnit."""
    wt_name = worktree_linux.rsplit("/", 1)[-1]
    db_name = f"saleor_{tid}_m10a_probe_{state}"
    setup = deps_install_cmd(worktree_linux, era_key)
    jnames = [f"{tid}_m10a_{state}_r{rep}" for rep in range(REPS)]
    for jname in jnames:
        payload = "\n".join(node_ids) + "\n"
        subprocess.run(
            ["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc",
             f"cat > {worktree_linux}/{jname}.nodes"],
            input=payload.encode("utf-8"), capture_output=True, timeout=180,
        )
    runs_script_lines = []
    for i, jname in enumerate(jnames):
        logf = f"/workspace/{wt_name}/logs/run_{i}_{jname}.log"
        runs_script_lines.append(
            f"( mapfile -t NODES < /workspace/{wt_name}/{jname}.nodes && "
            "/opt/venv/bin/python -m pytest -p no:cacheprovider -o addopts= "
            "--ds=saleor.tests.settings --disable-socket --reuse-db "
            f"--junitxml /workspace/{wt_name}/{jname}.xml -q "
            f'\"${{NODES[@]}}\" >{logf} 2>&1; echo RUN_{i}_RC=$? >>{logf} )'
        )
    runs_script = " ; ".join(runs_script_lines)
    proc = subprocess.run(
        ["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc",
         f"cat > {worktree_linux}/.wp2_probe_runs.sh"],
        input=runs_script.encode("utf-8"), capture_output=True, timeout=120,
    )
    if proc.returncode != 0:
        return {"error": "RUNS_SCRIPT_WRITE_FAIL", "outcomes": {}, "failures": {}, "wall_s": None}
    missing_install = " ".join(missing_packages)
    script = (
        "set -e; "
        "uv venv /opt/venv >/dev/null 2>&1 || true; "
        f"{setup} >/tmp/install.log 2>&1 || {{ echo INSTALL_DEP_FAIL; tail -120 /tmp/install.log; exit 2; }}; "
        f"{TOOLING_INSTALL} >>/tmp/install.log 2>&1 || {{ echo INSTALL_TOOL_FAIL; tail -80 /tmp/install.log; exit 2; }}; "  # noqa: E501
        f"uv pip install --python /opt/venv/bin/python {missing_install} >>/tmp/install.log 2>&1 "
        f"|| {{ echo INSTALL_MISSING_FAIL; tail -80 /tmp/install.log; exit 2; }}; "
        f"mkdir -p /workspace/{wt_name}/logs; "
        f"cd /workspace/{wt_name} && bash /workspace/{wt_name}/.wp2_probe_runs.sh; echo ALL_RUNS_DONE"
    )
    t0 = time.monotonic()
    container_name = f"wp2-m10a-probe-{tid}-{state}"
    wsl_docker(["rm", "-f", container_name], timeout_s=60)
    r = wsl_docker(
        [
            "run", "--rm", "--network", "host",
            "--name", container_name,
            "-e", f"DATABASE_URL=postgres://saleor:saleor@127.0.0.1:5433/{db_name}",
            "-e", "CACHE_URL=locmem://",
            "-v", f"{worktree_linux}:/workspace/{wt_name}",
            "-v", "wp2-uv-cache:/root/.cache/uv",
            f"wp2-era-{era_key}",
            "bash", "-lc", script,
        ],
        timeout_s=timeout_s,
    )
    wall = round(time.monotonic() - t0, 1)
    if r.returncode != 0 and "INSTALL" in r.stdout:
        return {"error": "INSTALL_FAIL", "outcomes": {}, "failures": {}, "wall_s": wall,
                "stdout_tail": r.stdout[-2500:]}
    outcomes: dict[str, list[str]] = {}
    failures: dict[str, str] = {}
    for jname in jnames:
        rr = wsl(f"cat {worktree_linux}/{jname}.xml 2>/dev/null || echo __NO_FILE__")
        if "__NO_FILE__" in rr.stdout[:20]:
            for n in node_ids:
                outcomes.setdefault(n, []).append("missing")
            continue
        try:
            outs, fails = parse_junit_with_failures(rr.stdout)
        except Exception:
            outs, fails = {}, {}
        for n in node_ids:
            outcomes.setdefault(n, []).append(outs.get(n, "missing"))
            if n in fails:
                failures[n] = fails[n]
    return {
        "error": None,
        "wall_s": wall,
        "outcomes": outcomes,
        "failures": failures,
        "stdout_tail": r.stdout[-1000:],
    }


def drop_probe_dbs(tid: str) -> None:
    short = tid.split("-")[-1][:12]
    for state in ("t", "p"):
        db = f"saleor_{short}_m10a_probe_{state}"
        wsl_docker(
            ["exec", "wp2-pg", "psql", "-U", "saleor", "-d", "postgres", "-c",
             f"DROP DATABASE IF EXISTS {db} WITH (FORCE)"],
            timeout_s=120,
        )


def load_node_sets(task_id: str) -> dict:
    """SET A: V2 P2P-U COLLECTION_ERROR attributable nodes.
    SET B: V2 C4 BEHAVIORAL_F2P + P2P_ONLY nodes."""
    eng_root = PROJECT / "research" / "wp2" / "p2p_u_v2_eng_2026-09-25" / task_id / "cap200" / "A"
    set_a = []
    if (eng_root / "node_classes.json").exists():
        classes = json.loads((eng_root / "node_classes.json").read_text(encoding="utf-8"))
        for nid, cls in classes.items():
            if cls == "COLLECTION_ERROR":
                set_a.append(nid)
    set_b = []
    for line in PER_TEST_DEV.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["task_id"] != task_id:
            continue
        if r["classification"] in ("BEHAVIORAL_F2P", "P2P_ONLY"):
            set_b.append(r["node_id"])
    return {
        "set_a_error_recovery": sorted(set(set_a)),
        "set_b_v2_non_regression": sorted(set(set_b)),
    }


def classify_v2_oracle(node_id: str, outcomes_p: list[str], outcomes_t: list[str], failures: dict) -> str:
    """Classify under the frozen V2 oracle semantics (classify_node_v2).

    ``parent_collects_node`` is True when the node has any non-missing parent
    outcome (i.e. it was collected at parent+testpatch in the probe run).
    """
    p_collects = any(o != "missing" for o in outcomes_p)
    parent_fail = failures.get(node_id, "")
    return classify_node_v2(
        target_outcomes=list(outcomes_t),
        parent_outcomes=list(outcomes_p),
        parent_failure_text=parent_fail,
        parent_collects_node=p_collects,
        shared_test_support_failed=False,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.task not in PROBE_TASKS:
        print("task not in frozen probe set:", args.task)
        return 2
    cfg = PROBE_TASKS[args.task]
    out_root = OUT_ROOT / "probe" / args.task
    out_root.mkdir(parents=True, exist_ok=True)

    node_sets = load_node_sets(args.task)
    set_a = node_sets["set_a_error_recovery"]
    set_b = node_sets["set_b_v2_non_regression"]
    all_nodes = sorted(set(set_a) | set(set_b))
    print(f"[{args.task}] SET A (recovery) n={len(set_a)}; SET B (non-reg) n={len(set_b)}; union n={len(all_nodes)}")
    if not set_a:
        print("no SET A nodes; probe not required for this task")
        return 0

    if args.dry_run:
        print(json.dumps({
            "task": args.task,
            "era_key": cfg["era_key"],
            "missing_packages": cfg["missing_packages"],
            "set_a": len(set_a),
            "set_b": len(set_b),
            "union": len(all_nodes),
        }, indent=1))
        print("DRY_RUN_OK")
        return 0

    ensure_cache()
    ensure_era_images()
    ensure_postgres_running()

    wts = ensure_worktrees(args.task, cfg["parent_commit"], cfg["target_commit"])
    short = args.task.split("-")[-1][:12]

    results = {}
    for state in ("t", "p"):
        t0 = time.monotonic()
        res = run_probe_state(
            era_key=cfg["era_key"],
            worktree_linux=wts[state],
            tid=short,
            state=state,
            node_ids=all_nodes,
            missing_packages=cfg["missing_packages"],
        )
        results[state] = res
        results[state]["total_state_wall_s"] = round(time.monotonic() - t0, 1)
        print(f"[{state}] wall={results[state].get('total_state_wall_s')} error={res.get('error')}", flush=True)
        if res.get("error"):
            print(res.get("stdout_tail", "")[-1500:])
            drop_probe_dbs(args.task)
            return 3

    # Persist JUnit evidence
    junit_dir = out_root / "junit"
    junit_dir.mkdir(parents=True, exist_ok=True)
    for state in ("t", "p"):
        for jname in [f"{short}_m10a_{state}_r{rep}" for rep in range(REPS)]:
            rr = wsl(f"cat {wts[state]}/{jname}.xml 2>/dev/null || echo __NO_FILE__")
            if "__NO_FILE__" not in rr.stdout[:20]:
                (junit_dir / f"{jname}.xml").write_text(rr.stdout, encoding="utf-8")

    # Classify SET A and SET B
    set_a_results = {}
    set_b_results = {}
    for n in set_a:
        p = results["p"]["outcomes"].get(n, ["missing"] * REPS)
        t = results["t"]["outcomes"].get(n, ["missing"] * REPS)
        cls = classify_v2_oracle(n, p, t, results["p"]["failures"])
        set_a_results[n] = {"parent": list(p), "target": list(t), "class": cls}
    for n in set_b:
        p = results["p"]["outcomes"].get(n, ["missing"] * REPS)
        t = results["t"]["outcomes"].get(n, ["missing"] * REPS)
        cls = classify_v2_oracle(n, p, t, results["p"]["failures"])
        set_b_results[n] = {"parent": list(p), "target": list(t), "class": cls}

    from collections import Counter

    set_a_class_counts = Counter(v["class"] for v in set_a_results.values())
    set_b_class_counts = Counter(v["class"] for v in set_b_results.values())

    # V2 prior classes for SET B from per_test_dev_v2.jsonl
    v2_set_b_classes = {}
    for line in PER_TEST_DEV.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["task_id"] == args.task and r["classification"] in ("BEHAVIORAL_F2P", "P2P_ONLY"):
            v2_set_b_classes[r["node_id"]] = r["classification"]
    transitions = {}
    for n in set_b:
        v2 = v2_set_b_classes.get(n)
        probe = set_b_results[n]["class"]
        if v2 != probe:
            transitions[n] = {"v2": v2, "probe": probe}

    rec = {
        "artifact": "probe_results",
        "schema_version": "mission10a-probe-v1",
        "label": "NON_FROZEN_EXPLORATORY_ENV_PROBE",
        "created_utc": _now_utc(),
        "task_id": args.task,
        "era_key": cfg["era_key"],
        "python_requirement": cfg["python_requirement"],
        "missing_declared_group_installed": cfg["missing_packages"],
        "node_sets": {k: len(v) for k, v in node_sets.items()},
        "set_a_error_recovery_class_counts": dict(set_a_class_counts),
        "set_b_v2_non_regression_class_counts": dict(set_b_class_counts),
        "set_b_v2_class_transitions": transitions,
        "set_b_v2_non_regression_holds": not transitions,
        "results": {
            "set_a": set_a_results,
            "set_b": set_b_results,
        },
        "measurements": {
            "target_wall_s": results["t"].get("total_state_wall_s"),
            "parent_wall_s": results["p"].get("total_state_wall_s"),
            "target_error": results["t"].get("error"),
            "parent_error": results["p"].get("error"),
        },
    }
    (out_root / "probe_results.json").write_text(
        json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps({
        "set_a_recovery": dict(set_a_class_counts),
        "set_b_non_regression_holds": not transitions,
        "set_b_transitions": transitions,
    }, indent=1))

    drop_probe_dbs(args.task)
    wsl(f"git -C /opt/wp2_v2/saleor-cache worktree remove --force {wts['t']} 2>/dev/null || rm -rf {wts['t']}")
    wsl(f"git -C /opt/wp2_v2/saleor-cache worktree remove --force {wts['p']} 2>/dev/null || rm -rf {wts['p']}")
    return 0


def _now_utc() -> str:
    import datetime

    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


if __name__ == "__main__":
    raise SystemExit(main())
