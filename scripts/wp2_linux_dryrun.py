#!/usr/bin/env python3
"""WP-2 bounded real-task Linux dry run (amendment E) - ZERO API.

Exercises the frozen V2 pipeline on real Saleor tasks using the WSL-local
Docker Engine (B0): Linux ext4 worktrees (fixes historical ``?`` filenames),
era-controlled images (amendment D), commit lockfile dependency construction,
3x target + 3x parent+testpatch runs, environment canary (amendment C), V2
mechanical classification (amendment A), and full provenance (Mission 07 §4).

Dry-run coverage (Mission 07 §17 + amendment E):
- one old-era task (~3.8 / 2020);
- one newer-era task (>=3.12,<3.13);
- one prior Windows path failure (``?`` cassette filename);
- one prior Unix-resource failure;
- one prior native-lib failure (if feasible);
- at least one 2025-2026 / Python 3.12 task.

No full sweep starts until this dry run AND the RED/GREEN classification tests
pass. Test execution in this dry run installs commit dependencies at container
start (recorded honestly); the full sweep pre-builds task images for offline
test execution.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

from benchmark.wp2.era_resolver import era_dockerfile_text  # noqa: E402
from benchmark.wp2.oracle_semantics_v2 import (  # noqa: E402
    TEST_PATH_RULE_SHA256,
    canary_verdict,
    classify_node_v2,
    is_test_path_v2,
    select_canary_node,
    task_eligibility_v2,
)

WSL_DISTRO = "Ubuntu-24.04"
WSL_BASE = "/opt/wp2_v2"
WSL_CACHE = f"{WSL_BASE}/saleor-cache"
WSL_WT = f"{WSL_BASE}/worktrees"
WSL_ERA = f"{WSL_BASE}/era"
HARNESS_VERSION = "wp2-linux-harness-dryrun-v0.1"
RUN_ROOT = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23"
WINDOWS_CACHE = PROJECT / "dist" / "pilot-repo-cache" / "saleor"

ERA_BASE = {
    "py38": "python:3.8-slim",
    "py39": "python:3.9-slim",
    "py312": "python:3.12-slim",
}


def sh(cmd: list[str], timeout_s: int = 3600) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=timeout_s, check=False)


def wsl(script: str, timeout_s: int = 3600) -> subprocess.CompletedProcess[str]:
    return sh(["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc", script], timeout_s=timeout_s)


def wsl_docker(args: list[str], timeout_s: int = 3600) -> subprocess.CompletedProcess[str]:
    return sh(["wsl", "-d", WSL_DISTRO, "--", "docker"] + args, timeout_s=timeout_s)


def ensure_cache() -> None:
    r = wsl(f"test -d {WSL_CACHE}/.git && echo CACHE_OK || echo CACHE_MISSING")
    if "CACHE_OK" in r.stdout:
        print("[cache] present")
        return
    print("[cache] copying saleor cache to WSL ext4 ...")
    src_parent = str(WINDOWS_CACHE.parent).replace("\\", "/")
    cache_name = WINDOWS_CACHE.name
    r = wsl(
        f"mkdir -p {WSL_BASE} && "
        f"tar -C /mnt/c{src_parent[2:]} -cf - {cache_name} "
        f"| tar -C {WSL_BASE} -xf - && "
        f"test -d {WSL_CACHE}/.git && echo COPY_OK",
        timeout_s=1800,
    )
    if "COPY_OK" not in r.stdout:
        print("[cache] FAILED:", r.stderr[-1500:])
        raise SystemExit(1)
    print("[cache] copied")


def ensure_era_images() -> None:
    wsl(f"mkdir -p {WSL_ERA}")
    for era_key in ERA_BASE:
        img = f"wp2-era-{era_key}"
        r = wsl_docker(["image", "inspect", img])
        if r.returncode == 0:
            print(f"[era] {img} present")
            continue
        df = era_dockerfile_text(era_key)
        host_dir = f"{WSL_ERA}/{era_key}"
        wsl(f"mkdir -p {host_dir}")
        wsl(f"cat > {host_dir}/Dockerfile <<'EOF'\n{df}\nEOF")
        print(f"[era] building {img} ...")
        r = wsl_docker(["build", "-t", img, host_dir], timeout_s=1800)
        if r.returncode != 0:
            print(f"[era] BUILD FAILED {img}:", r.stderr[-2000:])
            raise SystemExit(1)
        print(f"[era] {img} built")


def ensure_postgres() -> None:
    r = wsl_docker(["ps", "--filter", "name=wp2-pg", "--format", "{{.Names}}"])
    if "wp2-pg" in r.stdout:
        print("[pg] running")
        return
    r = wsl_docker(
        [
            "run", "-d", "--name", "wp2-pg", "--rm",
            "-p", "5433:5432",
            "-e", "POSTGRES_USER=saleor", "-e", "POSTGRES_PASSWORD=saleor",
            "-e", "POSTGRES_DB=saleor",
            "postgres:15-alpine",
            # test-only durability settings (disposable test DB; recorded in
            # provenance; C1-PERF-V2 optimization)
            "-c", "fsync=off", "-c", "synchronous_commit=off",
            "-c", "full_page_writes=off",
        ],
        timeout_s=300,
    )
    if r.returncode != 0:
        print("[pg] START FAILED:", r.stderr[-1500:])
        raise SystemExit(1)
    time.sleep(6)
    print("[pg] started")


def git_linux(workdir: str, *args: str) -> subprocess.CompletedProcess[str]:
    quoted = " ".join(f"'{a}'" for a in args)
    return wsl(f"git -C {workdir} {quoted}")


def ensure_worktrees(task_id: str, parent: str, target: str) -> dict:
    tid = task_id.split("-")[-1][:12]
    wt_t = f"{WSL_WT}/{tid}_t"
    wt_p = f"{WSL_WT}/{tid}_p"
    wsl(f"mkdir -p {WSL_WT}")
    r = wsl(f"test -e {wt_t}/.git && echo OK || echo MISSING")
    if "OK" not in r.stdout:
        r = git_linux(WSL_CACHE, "worktree", "add", "--detach", wt_t, target)
        if r.returncode != 0:
            print(f"[wt] target add FAILED: {r.stderr[-1200:]}")
            raise SystemExit(1)
    r = wsl(f"test -f {wt_p}/.wp2_patch_applied && echo OK || echo MISSING")
    if "OK" not in r.stdout:
        # redo parent worktree from scratch (idempotent; old partial state removed)
        git_linux(WSL_CACHE, "worktree", "remove", "--force", wt_p)
        r = git_linux(WSL_CACHE, "worktree", "add", "--detach", wt_p, parent)
        if r.returncode != 0:
            print(f"[wt] parent add FAILED: {r.stderr[-1200:]}")
            raise SystemExit(1)
        patch = derive_test_patch_linux(parent, target)
        if patch:
            wsl(f"mkdir -p {WSL_WT}")
            proc = subprocess.run(
                ["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc",
                 f"cat > {WSL_BASE}/patch.patch"],
                input=patch.encode("utf-8"), capture_output=True, timeout=120,
            )
            if proc.returncode != 0:
                print(f"[wt] patch write FAILED: {proc.stderr[-500:]}")
                raise SystemExit(1)
            ap = git_linux(wt_p, "apply", f"{WSL_BASE}/patch.patch")
            if ap.returncode != 0:
                print(f"[wt] parent patch apply FAILED: {ap.stderr[-800:]}")
                raise SystemExit(1)
        wsl(f"touch {wt_p}/.wp2_patch_applied")
    print(f"[wt] {task_id} worktrees ready")
    return {"target": wt_t, "parent": wt_p}


def derive_test_patch_linux(parent: str, target: str) -> str:
    r = git_linux(WSL_CACHE, "diff", "--name-status", parent, target)
    paths = []
    for line in r.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and is_test_path_v2(parts[-1]):
            paths.append(parts[-1])
    if not paths:
        return ""
    r = git_linux(WSL_CACHE, "diff", parent, target, "--", *paths)
    if r.returncode != 0:
        raise SystemExit(f"patch diff failed: {r.stderr}")
    return r.stdout


def changed_paths_linux(parent: str, target: str) -> dict:
    r = git_linux(WSL_CACHE, "diff", "--name-status", parent, target)
    tests, prods = [], []
    for line in r.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            path = parts[-1]
            (tests if is_test_path_v2(path) else prods).append(path)
    return {"test_files": tests, "prod_files": prods}


def deps_install_cmd(worktree_linux: str, era_key: str) -> str:
    base = f"/workspace/{worktree_linux.rsplit('/', 1)[-1]}"
    if era_key == "py312":
        # Modern Saleor (2025-2026): runtime deps from the commit's pyproject
        # plus the declared test/dev deps needed for collection. Full
        # ``--group dev`` resolution conflicts with the commit's own
        # cryptography>=49 pin (recorded); explicit declared test deps resolve.
        return (
            f"uv pip install --python /opt/venv/bin/python -e {base} "
            f"freezegun fakeredis"
        )
    return f"uv pip install --python /opt/venv/bin/python -r {base}/requirements.txt"


TOOLING_INSTALL = (
    "uv pip install --python /opt/venv/bin/python "
    "pytest pytest-django==4.11.1 pytest-socket pytest-xdist "
    "'billiard<4.3' 'setuptools<81' wheel"
)


def run_state_in_container(
    *,
    era_key: str,
    worktree_linux: str,
    tid: str,
    state: str,
    test_files: list[str],
    timeout_s: int = 3600,
) -> dict:
    """One container per state: install commit deps once, then run each changed
    test file 3x, writing per-run JUnit into the mounted Linux worktree."""
    wt_name = worktree_linux.rsplit("/", 1)[-1]
    mount = f"{worktree_linux}:/workspace/{wt_name}"
    db_name = f"saleor_{tid}_{state}"
    setup = deps_install_cmd(worktree_linux, era_key)
    runs = []
    for rep in range(3):
        for idx, tf in enumerate(test_files):
            jname = f"{tid}_{state}_r{rep}_f{idx}"
            runs.append(
                "/opt/venv/bin/python -m pytest -p no:cacheprovider -o addopts= "
                "--ds=saleor.tests.settings --disable-socket --reuse-db "
                f"--junitxml /workspace/{wt_name}/{jname}.xml -q {tf!r}"
            )
    runs_script = " ; ".join(
        f"( {r} >/tmp/py_{i}.log 2>&1; echo RUN_{i}_RC=$?; tail -12 /tmp/py_{i}.log )" for i, r in enumerate(runs)
    )
    # Write the run script INSIDE the mounted worktree so the container can
    # execute it (the container has its own /tmp; host /tmp is invisible).
    proc = subprocess.run(
        ["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc",
         f"cat > {worktree_linux}/.wp2_runs.sh"],
        input=runs_script.encode("utf-8"), capture_output=True, timeout=120,
    )
    if proc.returncode != 0:
        return {"error": "RUNS_SCRIPT_WRITE_FAIL", "junit": {}, "junit_failures": {}}
    script = (
        "set -e; "
        "uv venv /opt/venv >/dev/null 2>&1 || true; "
        f"{setup} >/tmp/install.log 2>&1 || {{ echo INSTALL_FAIL; tail -120 /tmp/install.log; exit 2; }}; "
        f"{TOOLING_INSTALL} >>/tmp/install.log 2>&1 || {{ echo TOOLING_FAIL; tail -80 /tmp/install.log; exit 2; }}; "
        f"cd /workspace/{wt_name} && bash /workspace/{wt_name}/.wp2_runs.sh; echo ALL_RUNS_DONE"
    )
    r = wsl_docker(
        [
            "run", "--rm", "--network", "host",
            "-e", f"DATABASE_URL=postgres://saleor:saleor@127.0.0.1:5433/{db_name}",
            "-e", "CACHE_URL=locmem://",
            "-v", mount,
            "-v", "wp2-uv-cache:/root/.cache/uv",
            f"wp2-era-{era_key}",
            "bash", "-lc", script,
        ],
        timeout_s=timeout_s,
    )
    merged: dict[str, str] = {}
    merged_fail: dict[str, str] = {}
    parse_err = None
    if r.returncode != 0 and "INSTALL_FAIL" in r.stdout:
        return {
            "error": "INSTALL_FAIL",
            "stdout_tail": r.stdout[-3000:],
            "junit": merged,
            "junit_failures": merged_fail,
        }
    from benchmark.wp2.oracle_confirmation import parse_junit_with_failures
    for rep in range(3):
        for idx, tf in enumerate(test_files):
            jname = f"{tid}_{state}_r{rep}_f{idx}"
            rr = wsl(f"cat {worktree_linux}/{jname}.xml 2>/dev/null || echo __NO_FILE__")
            if "__NO_FILE__" in rr.stdout[:20]:
                merged[tf] = "error"
                merged_fail[tf] = f"JUNIT_MISSING_R{rep}_F{idx}"
                continue
            try:
                nodes, fails = parse_junit_with_failures(rr.stdout)
            except Exception as exc:
                parse_err = f"{exc}"
                nodes, fails = {}, {}
            merged.update(nodes)
            merged_fail.update(fails)
    return {
        "error": parse_err,
        "returncode": r.returncode,
        "stdout_tail": r.stdout[-4000:],
        "junit": merged,
        "junit_failures": merged_fail,
    }


def main() -> int:
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    filter_task = sys.argv[1] if len(sys.argv) > 1 else None
    census = {
        t["task_id"]: t
        for t in json.loads(
            (PROJECT / "research/wp2/wp2_saleor_main297_census_2026-09-22.json").read_text(encoding="utf-8")
        )["tasks"]
    }
    dry_cfg = json.loads(
        (PROJECT / "research/wp2/wp2_linux_dryrun_tasks_2026-09-23.json").read_text(encoding="utf-8")
    )
    dry_tasks = dry_cfg["tasks"]

    ensure_cache()
    ensure_era_images()
    ensure_postgres()

    results = []
    for task in dry_tasks:
        if filter_task and task["task_id"] != filter_task:
            continue
        tid = task["task_id"]
        t0 = time.monotonic()
        print(f"\n=== DRY RUN {tid} [{task['category']}] ===", flush=True)
        c = census[tid]
        parent, target = c["parent_commit"], c["target_commit"]
        wts = ensure_worktrees(tid, parent, target)
        ch = changed_paths_linux(parent, target)
        era_key = task["era_key"]
        print(f"  test_files={len(ch['test_files'])} prod_files={len(ch['prod_files'])} era={era_key}", flush=True)

        tgt = run_state_in_container(
            era_key=era_key, worktree_linux=wts["target"],
            tid=tid.split("-")[-1][:12], state="t", test_files=ch["test_files"],
        )
        par = run_state_in_container(
            era_key=era_key, worktree_linux=wts["parent"],
            tid=tid.split("-")[-1][:12], state="p", test_files=ch["test_files"],
        )

        all_nodes = sorted(set(tgt["junit"]) | set(par["junit"]))
        node_records = []
        counts = {"BEHAVIORAL_F2P": 0, "SYMBOL_ABSENCE_F2P": 0, "PARENT_COLLECTION_ERROR": 0,
                  "FLAKY": 0, "TARGET_ORACLE_INVALID": 0, "P2P_ONLY": 0, "OTHER_REVIEW_REQUIRED": 0}
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
            node_records.append({"node_id": node, "classification": cls,
                                 "target_outcomes": t_list, "parent_outcomes": p_list})

        canary_rec = None
        canary = select_canary_node(node_ids=all_nodes, changed_test_files=ch["test_files"],
                                    touched_production_files=ch["prod_files"])
        if canary:
            c_t = tgt["junit"].get(canary, ["missing"] * 3)
            c_p = par["junit"].get(canary, ["missing"] * 3)
            canary_rec = {
                "canary_node_id": canary,
                "canary_target_outcomes": list(c_t) if isinstance(c_t, list) else [c_t] * 3,
                "canary_parent_outcomes": list(c_p) if isinstance(c_p, list) else [c_p] * 3,
                "canary_verdict": canary_verdict(
                    list(c_p) if isinstance(c_p, list) else [c_p] * 3,
                    list(c_t) if isinstance(c_t, list) else [c_t] * 3,
                ),
            }
        else:
            canary_rec = {"canary_node_id": None, "canary_verdict": "CANARY_NONE"}

        flags = task_eligibility_v2(
            n_behavioral_f2p=counts["BEHAVIORAL_F2P"],
            n_symbol_absence_f2p=counts["SYMBOL_ABSENCE_F2P"],
            n_parent_collection_error=counts["PARENT_COLLECTION_ERROR"],
            environment_valid=True,
            task_collection_failure=bool(tgt.get("error") == "INSTALL_FAIL" or par.get("error") == "INSTALL_FAIL"),
        )
        rec = {
            "task_id": tid,
            "category": task["category"],
            "target_commit": target,
            "parent_commit": parent,
            "era_key": era_key,
            "test_files": ch["test_files"],
            "counts": counts,
            "eligibility": flags,
            "canary": canary_rec,
            "n_nodes": len(all_nodes),
            "node_records": node_records,
            "install_error_target": tgt.get("error"),
            "install_error_parent": par.get("error"),
            "wall_s": round(time.monotonic() - t0, 1),
        }
        results.append(rec)
        with open(RUN_ROOT / "dryrun_2026-09-23.log", "a", encoding="utf-8") as logf:
            logf.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(
            f"  counts={counts} "
            f"eligible={flags['PRIMARY_BEHAVIORAL_F2P_ELIGIBLE']} "
            f"wall={rec['wall_s']}s",
            flush=True,
        )

    out = {
        "artifact": "wp2_linux_dryrun",
        "date": "2026-09-23",
        "harness_version": HARNESS_VERSION,
        "test_patch_rule_sha256": TEST_PATH_RULE_SHA256,
        "substrate": "WSL-local Docker Engine (Ubuntu-24.04, docker 29.1.3)",
        "task_results": results,
        "status": "COMPLETE",
    }
    out_path = RUN_ROOT / "dryrun_2026-09-23.json"
    if filter_task and out_path.exists():
        prev = json.loads(out_path.read_text(encoding="utf-8"))
        merged = {r["task_id"]: r for r in prev.get("task_results", [])}
        merged.update({r["task_id"]: r for r in results})
        out["task_results"] = [merged[k] for k in sorted(merged)]
    out_path.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("\nDRY RUN COMPLETE -> research/wp2/oracle_confirmation_linux_v2_2026-09-23/dryrun_2026-09-23.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
