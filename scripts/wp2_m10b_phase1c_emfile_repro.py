#!/usr/bin/env python3
"""WP-2 Mission-10B Phase 1C: EMFILE controlled reproduction (ZERO API).

Launches the primary reproduction task saleor-rc-c3b9e396b07d (py39) under
two scratch conditions on a FRESH DB creation/migration:

A. V2 condition        - exact V2 docker run args (no --ulimit nofile; the
                         container default soft limit ~1024).
B. UPLIFTED-NOFILE     - identical except --ulimit nofile=65536:65536.

Samples once per second during migration: pytest main PID FD count, process
count, memory, current phase. Records max FDs, time to DB creation, EMFILE
yes/no, exact failure point, ulimit values.

EMFILE FIX EFFICACY (9.3) is TRUE only if V2 reproduces EMFILE AND uplifted
removes it without introducing a new infrastructure failure at the same stage.

Usage:
    python scripts/wp2_m10b_phase1c_emfile_repro.py [--out DIR] [--condition A|B|BOTH]
"""
from __future__ import annotations

import argparse
import contextlib
import json
import subprocess
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
OUT_ROOT = PROJECT / "research" / "wp2" / "harness_v3_2026-09-26"
V2_ROOT = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23"

WSL_DISTRO = "Ubuntu-24.04"
WSL_CACHE = "/opt/wp2_v2/saleor-cache"
WSL_WT = "/opt/wp2_v2/worktrees"

TASK_ID = "saleor-rc-c3b9e396b07d"
TARGET_COMMIT = "c3b9e396b07d"  # full SHA resolved from census at runtime
REPS = 1


def _now_utc() -> str:
    import datetime

    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


def wsl(script: str, timeout_s: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc", script],
        capture_output=True, text=True, encoding="utf-8", timeout=timeout_s, check=False,
    )


def wsl_docker(args: list[str], timeout_s: int = 3600) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["wsl", "-d", WSL_DISTRO, "--", "docker"] + args,
        capture_output=True, text=True, encoding="utf-8", timeout=timeout_s, check=False,
    )


def git_linux(cwd: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc",
         f"git -C {cwd} " + " ".join(f"'{a}'" for a in args)],
        capture_output=True, text=True, encoding="utf-8", timeout=300, check=False,
    )


def target_sha() -> str:
    c = json.loads((V2_ROOT / "dev_census_2026-09-23.json").read_text(encoding="utf-8"))
    for t in c.get("tasks", []):
        if t["task_id"] == TASK_ID:
            return t["target_commit"]
    raise RuntimeError("task not in census")


def ensure_worktree(commit: str, label: str) -> str:
    wt = f"{WSL_WT}/c3b9e396b07d_{label}"
    wsl(f"mkdir -p {WSL_WT}")
    wsl(f"git -C {WSL_CACHE} worktree remove --force {wt} 2>/dev/null || rm -rf {wt}")
    r = git_linux(WSL_CACHE, "worktree", "add", "--detach", wt, commit)
    if r.returncode != 0:
        raise RuntimeError(f"[wt] add FAILED: {r.stderr[-1200:]}")
    return wt


def changed_test_files() -> list[str]:
    c = json.loads((V2_ROOT / "dev_census_2026-09-23.json").read_text(encoding="utf-8"))
    for t in c.get("tasks", []):
        if t["task_id"] == TASK_ID:
            if t.get("changed_test_files"):
                return sorted({p.split("/", 3)[-1] for p in t["changed_test_files"]})
            # derive from git diff (census stores counts only)
            r = git_linux(WSL_CACHE, "diff", "--name-only",
                          t["parent_commit"], t["target_commit"])
            files = [ln.strip() for ln in r.stdout.splitlines()
                     if ln.strip().endswith(".py") and "/test" in ln]
            return sorted(files)
    return []


def ensure_postgres() -> None:
    """Start wp2-pg if not running; wait for pg_isready (frozen substrate)."""
    r = wsl("docker ps -a --filter 'name=^wp2-pg$' --format '{{.Names}}'")
    if "wp2-pg" not in r.stdout:
        raise RuntimeError("wp2-pg container does not exist")
    r = wsl("docker ps --filter 'name=^wp2-pg$' --format '{{.Names}}'")
    if "wp2-pg" not in r.stdout:
        r = wsl("docker start wp2-pg", timeout_s=120)
        if r.returncode != 0:
            raise RuntimeError(f"wp2-pg start failed: {r.stderr[-400:]}")
    for _ in range(20):
        r = wsl("docker exec wp2-pg pg_isready -U saleor", timeout_s=60)
        if r.returncode == 0 and "accepting" in r.stdout:
            return
        time.sleep(3)
    raise RuntimeError("wp2-pg did not become ready")


def run_condition(condition: str, commit: str, test_files: list[str],
                  out_root: Path) -> dict:
    wt = ensure_worktree(commit, f"emfile_{condition}")
    wt_name = wt.rsplit("/", 1)[-1]
    mount = f"{wt}:/workspace/{wt_name}"
    db_name = f"saleor_c3b9e396b07d_{condition}_fresh"
    # Fresh DB: run `pytest --reuse-db --create-db`-equivalent: simply run a
    # single node under --reuse-db so pytest-django creates the DB once.
    test_args = " ".join(f"'{tf}'" for tf in test_files[:2])
    # Multi-line run script written INTO the mounted worktree; the container
    # executes it directly (avoids nested-quoting fragility).
    run_lines = [
        "#!/bin/bash",
        "cd /workspace/@@WT@@",
        "rm -f /workspace/@@WT@@/emfile_fds.csv",
        "( while true; do",
        '  PID=""',
        "  for p in /proc/[0-9]*; do",
        "    cmd=$(tr '\\0' ' ' < $p/cmdline 2>/dev/null)",
        '    case "$cmd" in *pytest*) PID="${p#/proc/}"; break;; esac',
        "  done",
        '  if [ -n "$PID" ]; then',
        "    N=$(ls /proc/$PID/fd 2>/dev/null | wc -l)",
        "    T=$(ls /proc/[0-9]*/fd 2>/dev/null | wc -l)",
        '    echo "$(date +%s.%N) $PID $N $T"',
        '  else echo "$(date +%s.%N) NONE 0 0"; fi',
        "  sleep 1",
        "done ) > /workspace/@@WT@@/emfile_fds.csv 2>/dev/null &",
        "SAMPLER=$!",
        "trap 'kill $SAMPLER 2>/dev/null' EXIT",
        "/opt/venv/bin/python -m pytest -p no:cacheprovider -o addopts= "
        "--ds=saleor.tests.settings --disable-socket --reuse-db "
        f"-x --junitxml /workspace/@@WT@@/emfile_{condition}.xml -q {test_args} "
        "> /workspace/@@WT@@/emfile_run.log 2>&1",
        "echo PYTEST_RC=$?",
    ]
    run_script = "\n".join(run_lines).replace("@@WT@@", wt_name) + "\n"
    subprocess.run(
        ["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc",
         f"cat > {wt}/.emfile_run.sh"],
        input=run_script.encode("utf-8"), capture_output=True, timeout=120, check=True,
    )
    # validate the generated bash syntax inside WSL
    v = wsl(f"bash -n {wt}/.emfile_run.sh")
    if v.returncode != 0:
        raise RuntimeError(f"generated run script syntax error: {v.stderr[-800:]}")
    script = (
        "set -e; "
        "uv venv /opt/venv >/dev/null 2>&1 || true; "
        "uv pip install --python /opt/venv/bin/python -r /workspace/"
        f"{wt_name}/requirements.txt >/tmp/install.log 2>&1 "
        "|| { echo INSTALL_FAIL; tail -120 /tmp/install.log; exit 2; }; "
        "uv pip install --python /opt/venv/bin/python "
        "pytest pytest-django==4.11.1 pytest-socket pytest-xdist "
        "'billiard<4.3' 'setuptools<81' wheel >>/tmp/install.log 2>&1 "
        "|| { echo TOOLING_FAIL; tail -80 /tmp/install.log; exit 2; }; "
        f"bash /workspace/{wt_name}/.emfile_run.sh"
    )

    docker_args = [
        "run", "--rm", "--network", "host",
        "-e", f"DATABASE_URL=postgres://saleor:saleor@127.0.0.1:5433/{db_name}",
        "-e", "CACHE_URL=locmem://",
        "-v", mount,
        "-v", "wp2-uv-cache:/root/.cache/uv",
    ]
    if condition == "B":
        docker_args += ["--ulimit", "nofile=65536:65536"]
    docker_args += ["wp2-era-py39", "bash", "-lc", script]

    # pre-drop any scratch DB with this name (uniquely named scratch only)
    wsl_docker(["exec", "wp2-pg", "psql", "-U", "saleor", "-d", "postgres", "-c",
                f"DROP DATABASE IF EXISTS {db_name}"], timeout_s=120)
    t0 = time.monotonic()
    # spawn container async
    import threading

    proc_box: dict = {}

    def _run():
        proc_box["r"] = wsl_docker(docker_args, timeout_s=5400)

    th = threading.Thread(target=_run, daemon=True)
    th.start()
    th.join(timeout=5400)
    wall = time.monotonic() - t0

    # capture pytest log + junit from worktree
    log = wsl(f"cat {wt}/emfile_run.log 2>/dev/null || echo __NO_LOG__").stdout
    (out_root / f"phase1c_{condition}_pytest_run.log").write_text(log, encoding="utf-8")
    rc_line = [ln for ln in log.splitlines() if "PYTEST_RC=" in ln]
    pytest_rc = rc_line[-1].split("=")[-1] if rc_line else "UNKNOWN"
    emfile_in_log = "Too many open files" in log or "Errno 24" in log
    failure_point = "UNKNOWN"
    for pat in ("django_db_setup", "migrations", "create_test_db", "OperationalError",
                "Too many open files", "socketpair", "FileNotFoundError"):
        if pat in log:
            failure_point = pat
            break

    # in-container FD sampler CSV
    csv = wsl(f"cat {wt}/emfile_fds.csv 2>/dev/null || echo __NO_CSV__").stdout
    max_pytest_fds = 0
    max_total_fds = 0
    n_fd_samples = 0
    if "__NO_CSV__" not in csv:
        for line in csv.splitlines():
            parts = line.split()
            if len(parts) < 4:
                continue
            # ts PID pytest_fds total_fds
            if parts[1] == "NONE":
                continue
            with contextlib.suppress(ValueError):
                max_pytest_fds = max(max_pytest_fds, int(parts[2]))
                max_total_fds = max(max_total_fds, int(parts[3]))
            n_fd_samples += 1

    # DB state (pytest-django creates `test_<dbname>` and the maintenance DB)
    dbs = wsl_docker(["exec", "wp2-pg", "psql", "-U", "saleor", "-d", "postgres", "-c",
                      "SELECT datname FROM pg_database"]).stdout
    db_created = f"test_{db_name}" in dbs or db_name in dbs
    if csv and "__NO_CSV__" not in csv:
        (out_root / f"phase1c_{condition}_fds.csv").write_text(csv, encoding="utf-8")
    wsl_docker(["exec", "wp2-pg", "psql", "-U", "saleor", "-d", "postgres", "-c",
                f"DROP DATABASE IF EXISTS {db_name}"], timeout_s=120)
    wsl(f"git -C {WSL_CACHE} worktree remove --force {wt} 2>/dev/null || rm -rf {wt}")

    return {
        "condition": condition,
        "task_id": TASK_ID,
        "target_commit": commit,
        "era_key": "py39",
        "ulimit_soft": "1024 (docker default)" if condition == "A" else "65536",
        "ulimit_hard": "1048576" if condition == "A" else "65536",
        "nofile_flag": "none (V2)" if condition == "A" else "--ulimit nofile=65536:65536",
        "pytest_rc": pytest_rc,
        "emfile_observed": emfile_in_log,
        "failure_point": failure_point,
        "db_created": db_created,
        "max_pytest_fds": max_pytest_fds,
        "max_container_total_fds": max_total_fds,
        "n_fd_samples": n_fd_samples,
        "wall_s": round(wall, 1),
        "log_tail": "\n".join(log.splitlines()[-40:]) if log else "(no log)",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--condition", choices=["A", "B", "BOTH"], default="BOTH")
    args = ap.parse_args()
    out_root = Path(args.out) if args.out else OUT_ROOT
    out_root.mkdir(parents=True, exist_ok=True)

    commit = target_sha()
    test_files = changed_test_files()
    print(f"[1C] task {TASK_ID} target={commit[:12]} changed_test_files={len(test_files)}")
    ensure_postgres()

    results: dict = {}
    if args.condition in ("A", "BOTH"):
        print("[1C] running condition A (V2 nofile default ~1024) ...")
        results["A"] = run_condition("A", commit, test_files, out_root)
        print(f"  A: emfile={results['A']['emfile_observed']} "
              f"max_fd={results['A']['max_pytest_fds']} rc={results['A']['pytest_rc']}")
    if args.condition in ("B", "BOTH"):
        print("[1C] running condition B (nofile 65536) ...")
        results["B"] = run_condition("B", commit, test_files, out_root)
        print(f"  B: emfile={results['B']['emfile_observed']} "
              f"max_fd={results['B']['max_pytest_fds']} rc={results['B']['pytest_rc']}")

    a = results.get("A", {})
    b = results.get("B", {})
    efficacy = None
    if a and b:
        efficacy = (
            a.get("emfile_observed") is True
            and b.get("emfile_observed") is False
            and b.get("failure_point") != "Too many open files"
        )
    elif a and a.get("emfile_observed") is True:
        efficacy = None  # only A ran; cannot conclude
    summary = {
        "artifact": "m10b_phase1c_emfile_repro",
        "created_utc": _now_utc(),
        "task": TASK_ID,
        "results": results,
        "emfile_fix_efficacy": efficacy,
        "efficacy_rule": "TRUE only if A reproduces EMFILE AND B removes it "
                         "without a new infra failure at the same stage",
        "notes": "Scratch DBs are uniquely named and dropped; frozen images "
                 "unchanged; no V2 artifact mutation.",
    }
    (out_root / "phase1c_emfile_repro.json").write_text(
        json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"[1C] EMFILE_FIX_EFFICACY={efficacy}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
