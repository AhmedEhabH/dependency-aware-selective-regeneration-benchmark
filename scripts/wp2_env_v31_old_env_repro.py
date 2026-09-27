#!/usr/bin/env python3
"""WP-2 Env Closure V3.1 E4 - reproduce OLD (f86007e4) V3 install environments.

Scratch containers reproduce the exact OLD recipe: era image + nofile ulimit +
OLD main fragment (unchanged lock_install_script) + OLD task-specific dev
supplement (legacy_expected_dev_deps, the frozen Phase-1E manual list) +
TOOLING_INSTALL, in the same order as the frozen runner. Raw evidence (pip
freeze, python/pytest version, pytest --trace-config, pytest --markers, install
log, return codes) is captured. No scientific tests run here.

Persists research/wp2/harness_v3_2026-09-26/env_closure_v31_old_env/<task_id>.json
+ raw freeze/log files.

Usage:
    python scripts/wp2_env_v31_old_env_repro.py --all [--max-tasks N] [--task ID]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

OUT_ROOT = PROJECT / "research" / "wp2" / "harness_v3_2026-09-26"
CENSUS = json.loads((PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23" /
                     "dev_census_2026-09-23.json").read_text(encoding="utf-8"))
INVENTORY = json.loads((PROJECT / "research" / "wp2/" /
                        "wp2_dev_unchanged_p2p_candidate_inventory_v1_2026-09-25.json").read_text(encoding="utf-8"))
WSL_CACHE = "/opt/wp2_v2/saleor-cache"
WSL_WT = "/opt/wp2_v2/worktrees"
DISTRO = "Ubuntu-24.04"

from benchmark.wp2.harness_v3 import (  # noqa: E402
    LEGACY_EXPECTED_DEV_DEPS,
    NOFILE_HARD,
    NOFILE_SOFT,
    TOOLING_INSTALL,
    lock_install_script,
    target_manifests,
)

REPRO_ROOT = OUT_ROOT / "env_closure_v31_old_env"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def task_commits(task_id: str) -> tuple[str, str]:
    for t in CENSUS.get("tasks", []):
        if t["task_id"] == task_id:
            return t["parent_commit"], t["target_commit"]
    raise KeyError(task_id)


def era_of(task_id: str) -> str:
    for r in INVENTORY["tasks"]:
        if r["task_id"] == task_id:
            return r["era_key"]
    return ""


def wsl(script: str, timeout_s: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["wsl", "-d", DISTRO, "--", "bash", "-lc", script],
                          capture_output=True, text=True, encoding="utf-8", timeout=timeout_s)


def old_dev_fragment(task_id: str) -> str:
    pins = LEGACY_EXPECTED_DEV_DEPS.get(task_id, ())
    if not pins:
        return "echo NO_LOCKED_DEV_GROUP"
    return "uv pip install --python /opt/venv/bin/python " + " ".join(pins)


def reproduce_old(task_id: str) -> dict:
    parent, target = task_commits(task_id)
    era = era_of(task_id)
    tid = task_id.split("-")[-1][:12]
    wt = f"{WSL_WT}/{tid}_v31_old_t"
    wt_name = wt.rsplit("/", 1)[-1]
    t0 = time.monotonic()

    manifests = target_manifests(target)
    install_frag, install_mode, _ = lock_install_script(wt, manifests)
    dev_frag = old_dev_fragment(task_id)

    wsl(f"git -C {WSL_CACHE} worktree remove --force {wt} 2>/dev/null || rm -rf {wt}")
    r = wsl(f"git -C {WSL_CACHE} worktree add --detach {wt} {target}", timeout_s=180)
    if r.returncode != 0:
        return {"task_id": task_id, "status": "WORKTREE_FAIL",
                "error": r.stderr[-800:]}

    script = (
        "set -e; "
        "uv venv /opt/venv >/dev/null 2>&1 || true; "
        f"{install_frag}; "
        f"{dev_frag} >>/tmp/install.log 2>&1 "
        "|| { echo INSTALL_DEV_FAIL; tail -80 /tmp/install.log; exit 2; }; "
        f"{TOOLING_INSTALL} >>/tmp/install.log 2>&1 "
        "|| { echo TOOLING_FAIL; tail -80 /tmp/install.log; exit 2; }; "
        f"cd /workspace/{wt_name} && "
        "uv pip freeze --python /opt/venv/bin/python > /workspace/" + wt_name + "/freeze.txt; "
        "set +e; "
        "/opt/venv/bin/python -V > /workspace/" + wt_name + "/pyversion.txt 2>&1; "
        "/opt/venv/bin/python -m pytest -p no:cacheprovider -o addopts= "
        "--ds=saleor.tests.settings --version > /workspace/" + wt_name + "/pytestversion.txt 2>&1; "
        "/opt/venv/bin/python -m pytest -p no:cacheprovider -o addopts= "
        "--ds=saleor.tests.settings --trace-config > /workspace/" + wt_name + "/traceconfig.txt 2>&1; "
        "/opt/venv/bin/python -m pytest -p no:cacheprovider -o addopts= "
        "--ds=saleor.tests.settings --markers > /workspace/" + wt_name + "/markers.txt 2>&1; "
        "cp /tmp/install.log /workspace/" + wt_name + "/install.log; "
        "echo OLD_ENV_DONE"
    )
    rc = subprocess.run(
        ["wsl", "-d", DISTRO, "--", "bash", "-lc",
         "cat > " + wt + "/.v31_old.sh"],
        input=script.encode("utf-8"), capture_output=True, timeout=120)
    if rc.returncode != 0:
        return {"task_id": task_id, "status": "SCRIPT_WRITE_FAIL",
                "error": rc.stderr[-500:]}

    r = subprocess.run(
        ["wsl", "-d", DISTRO, "--", "docker", "run", "--rm", "--network", "host",
         "--ulimit", f"nofile={NOFILE_SOFT}:{NOFILE_HARD}",
         "-v", f"{wt}:/workspace/{wt_name}",
         "-v", "wp2-uv-cache:/root/.cache/uv",
         f"wp2-era-{era}", "bash", f"/workspace/{wt_name}/.v31_old.sh"],
        capture_output=True, text=True, encoding="utf-8", timeout=3600)
    container_rc = r.returncode
    stdout = r.stdout or ""
    stderr = r.stderr or ""

    def read_back(name: str) -> tuple[str, str | None]:
        rr = wsl(f"cat {wt}/{name} 2>/dev/null || echo __NO_FILE__")
        if "__NO_FILE__" in rr.stdout[:20]:
            return "", None
        return rr.stdout, _sha(rr.stdout)

    files = {}
    for name in ("freeze.txt", "pyversion.txt", "pytestversion.txt",
                 "traceconfig.txt", "markers.txt", "install.log"):
        text, sha = read_back(name)
        files[name] = {"sha256": sha, "lines": len(text.splitlines()) if text else 0}

    # persist raw evidence files under the repro root
    task_dir = REPRO_ROOT / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    for name in ("freeze.txt", "pyversion.txt", "pytestversion.txt",
                 "traceconfig.txt", "markers.txt", "install.log"):
        text, _ = read_back(name)
        (task_dir / name).write_text(text, encoding="utf-8", errors="replace", newline="")

    freeze_text, _ = read_back("freeze.txt")
    rec = {
        "task_id": task_id,
        "era_key": era,
        "target_commit": target,
        "install_mode": install_mode,
        "install_fragment": install_frag,
        "dev_fragment": dev_frag,
        "container_rc": container_rc,
        "old_env_repro_status": (
            "OK" if container_rc == 0 and files["freeze.txt"]["sha256"]
            else "OLD_ENV_UNREPRODUCIBLE"),
        "files": files,
        "freeze_sha256": files["freeze.txt"]["sha256"],
        "freeze_packages": len(freeze_text.splitlines()) if freeze_text else 0,
        "wall_s": round(time.monotonic() - t0, 1),
        "stdout_tail": stdout[-4000:],
        "stderr_tail": stderr[-1000:],
    }
    (task_dir / "record.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
    wsl(f"git -C {WSL_CACHE} worktree remove --force {wt} 2>/dev/null || rm -rf {wt}")
    wsl(f"git -C {WSL_CACHE} worktree prune 2>/dev/null || true")
    print(f"  {task_id} old={rec['old_env_repro_status']} mode={install_mode} "
          f"packages={rec['freeze_packages']} rc={container_rc} wall={rec['wall_s']}s")
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--max-tasks", type=int, default=9999)
    args = ap.parse_args()
    if args.task:
        tasks = [args.task]
    else:
        eng = json.loads((OUT_ROOT / "eng_v3_oracle_ready.json").read_text(encoding="utf-8"))
        tasks = sorted(eng["oracle_valid_union_task_ids"])
    done = 0
    for tid in tasks:
        if done >= args.max_tasks:
            break
        rec_path = REPRO_ROOT / tid / "record.json"
        if rec_path.exists():
            print(f"  {tid} already reproduced; skip")
            continue
        reproduce_old(tid)
        done += 1
    print(f"[E4] old-env reproduction complete (done this invocation: {done})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
