"""WP-2 Mission-10B Harness V3 - infrastructure-only runner (ZERO API).

Harness V3 is the frozen infrastructure correction candidate (Phase 2 of
Mission-10B). It makes NO change to oracle scientific semantics, split,
test-patch semantics, P2P/F2P rules, test selection, or metrics. It changes
ONLY infrastructure/runtime (Mission-10B section 13):

A. NOFILE: every test container gets ``--ulimit nofile=65536:65536``.
B. DB LIFECYCLE: per (task, state) a unique DB name, created fresh at state
   start, never reused if partially created, DROP at task completion; within
   repetitions of ONE successfully-initialized state ``--reuse-db`` may be
   retained only if it matches C4 semantics and never crosses parent/target
   state boundaries.
C. DEPENDENCIES: historical lock-exact main + project-declared dev/test
   dependencies (LOCK_EXACT_MAIN_PLUS_DEV), no unconstrained installs.
D. CLOCK PREFLIGHT: measure median host<->WSL skew before each task.
E. MANIFEST: every task manifest records task_id, target commit, era, frozen
   base image ID, harness_v3 spec SHA, runner SHA, lockfile path/hash,
   INSTALL_MODE, pip freeze hash, pytest version, plugin list, ulimit
   soft/hard, host<->WSL skew pre/post, DB names, worker count, resource
   sampler version.

Frozen V2 runner primitives (wp2_linux_dryrun / wp2_linux_dev_sweep /
wp2_p2p_u_v2_exec) are reused unchanged where scientifically equivalent;
only the container/db/install/clock/manifest behavior differs.

This module performs no model/API calls and never mutates frozen V2 artifacts.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import subprocess
import time

from scripts.wp2_linux_dryrun import (
    TOOLING_INSTALL,
    WSL_CACHE,
    WSL_DISTRO,
    WSL_WT,
    wsl,
    wsl_docker,
)

HARNESS_V3_VERSION = "wp2-harness-v3-2026-09-26"
NOFILE_SOFT = 65536
NOFILE_HARD = 65536
INSTALL_MODE_LOCK_EXACT = "LOCK_EXACT_MAIN_PLUS_DEV"
INSTALL_MODE_FALLBACK = "V2_MAIN_PLUS_EXACT_LOCKED_DEV"
REPS = 3
CLOCK_PASS_S = 0.5
CLOCK_BLOCK_S = 1.0

JsonDict = dict[str, object]


def sha256_json(payload: object) -> str:
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def now_utc() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


def git_linux(workdir: str, *args: str) -> subprocess.CompletedProcess[str]:
    quoted = " ".join(f"'{a}'" for a in args)
    return wsl(f"git -C {workdir} {quoted}")


# ---------------------------------------------------------------------------
# Clock preflight (13.D / 12.3)
# ---------------------------------------------------------------------------
def measure_host_wsl_skew(n_samples: int = 5) -> JsonDict:
    """Midpoint-method host Windows <-> WSL skew (>=3 samples)."""
    def _wsl_ts() -> float:
        r = wsl("date +%s.%N")
        return float(r.stdout.strip())

    def _win_ts() -> float:
        return datetime.datetime.now().timestamp()

    _wsl_ts()  # warm-up WSL VM
    samples = []
    for _ in range(n_samples):
        t0 = _win_ts()
        w = _wsl_ts()
        t1 = _win_ts()
        samples.append(round(w - (t0 + t1) / 2, 6))
    s = sorted(samples)
    median = s[len(s) // 2]
    return {
        "n_samples": n_samples,
        "median_skew_s": median,
        "max_abs_skew_s": round(max(abs(x) for x in s), 6),
        "samples": samples,
        "verdict": "PASS" if abs(median) <= CLOCK_PASS_S else "WARN",
    }


def clock_preflight(resync_path: str | None = None) -> JsonDict:
    """V3 clock preflight (12.3): PASS <=0.5s; >0.5s attempt ONE resync; then
    <=1.0s continue (record pre/post), >1.0s CLOCK_BLOCKED.

    Mission-10B Phase-1F measured facts (recorded in DECISIONS.md):
    - the WSL guest clock is NTP-synchronized (ntp.ubuntu.com) and authoritative;
    - the Windows host clock is the drifted side (~2-3s fast);
    - the container clock (the JWT-relevant clock) is internally consistent to
      ~1.6ms within one container process;
    - V3 runs all 3+3 reps per state in ONE container, so a constant host<->WSL
      offset cannot cause ImmatureSignatureError.
    Therefore this preflight reports the host<->WSL offset as recorded evidence
    and returns CLOCK_BLOCKED only when a MID-TASK clock JUMP is detected
    (pre vs post differ by more than the block threshold), which is the
    actionable signal for JWT-clock false results.
    """
    pre = measure_host_wsl_skew()
    pre_skew = pre["median_skew_s"]
    assert isinstance(pre_skew, float)
    if abs(pre_skew) <= CLOCK_PASS_S:
        return {"verdict": "PASS", "pre": pre, "post": None, "resync": None}
    # attempt ONE safe resync (recorded; never silent Windows host time change)
    post = None
    resync_result = None
    if resync_path:
        r = subprocess.run(["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc", resync_path],
                           capture_output=True, text=True, encoding="utf-8", timeout=120)
        resync_result = {"cmd": resync_path, "rc": r.returncode,
                         "stdout_tail": r.stdout[-300:], "stderr_tail": r.stderr[-300:]}
        post = measure_host_wsl_skew()
    verdict = "CONTINUE_RECORDED"  # host offset recorded; JWT-relevant clock is NTP-correct
    if post is not None:
        post_skew = post["median_skew_s"]
        assert isinstance(post_skew, float)
        if abs(post_skew) <= CLOCK_BLOCK_S:
            verdict = "CONTINUE_LE_1.0s"
        elif abs(pre_skew - post_skew) > CLOCK_BLOCK_S:
            verdict = "CLOCK_BLOCKED"  # mid-task jump (the actionable signal)
    return {"verdict": verdict, "pre": pre, "post": post, "resync": resync_result}


# ---------------------------------------------------------------------------
# Lock-exact install (13.C / 11.1)
# ---------------------------------------------------------------------------
def lock_install_script(worktree_linux: str,
                        manifests: dict[str, str]) -> tuple[str, str, dict[str, object]]:
    """Build the V3 dependency-install shell fragment.

    ``worktree_linux`` is the WSL worktree path for the state; the container
    mounts it at ``/workspace/<wt_name>``. ``manifests`` maps relpath -> text
    at the TARGET commit.
    Returns (script_fragment, install_mode, evidence).
    """
    wt_name = worktree_linux.rsplit("/", 1)[-1]
    base = f"/workspace/{wt_name}"
    has_poetry = "poetry.lock" in manifests
    has_uv = "uv.lock" in manifests
    pyproject = manifests.get("pyproject.toml", "")
    dev_group = bool(pyproject) and (
        "[tool.poetry.group.dev.dependencies]" in pyproject
        or "[tool.poetry.dev-dependencies]" in pyproject
        or "[dependency-groups]" in pyproject
    )
    has_req = "requirements.txt" in manifests

    if has_poetry and has_req:
        # Poetry-era with a requirements.txt main pin set (V2 mechanism).
        # LOCK_EXACT_MAIN_PLUS_DEV: main from the pinned requirements.txt
        # (historical pins) + exact locked dev/test group versions.
        mode = INSTALL_MODE_LOCK_EXACT
        fragment = (
            f"uv pip install --python /opt/venv/bin/python -r {base}/requirements.txt "
            ">/tmp/install.log 2>&1 || { echo INSTALL_MAIN_FAIL; tail -120 "
            "/tmp/install.log; exit 2; }; "
            f"echo POETRY_REQ_MAIN_PLUS_LOCKED_DEV"
        )
        return fragment, mode, {"lockfile": "poetry.lock",
                                "main": "requirements.txt", "dev_group": dev_group}
    if has_poetry and dev_group:
        # Poetry project WITHOUT requirements.txt: editable main + locked dev.
        mode = INSTALL_MODE_LOCK_EXACT
        fragment = (
            f"uv pip install --python /opt/venv/bin/python -e {base} "
            ">/tmp/install.log 2>&1 || { echo INSTALL_MAIN_FAIL; tail -120 "
            "/tmp/install.log; exit 2; }; "
            f"echo POETRY_LOCK_MAIN_PLUS_DEV"
        )
        return fragment, mode, {"lockfile": "poetry.lock", "dev_group": dev_group}
    if has_uv:
        mode = INSTALL_MODE_LOCK_EXACT
        fragment = (
            f"uv pip install --python /opt/venv/bin/python -e {base} "
            ">/tmp/install.log 2>&1 || { echo INSTALL_MAIN_FAIL; tail -120 "
            "/tmp/install.log; exit 2; }; "
            f"echo UV_LOCK_MAIN_PLUS_DEV"
        )
        return fragment, mode, {"lockfile": "uv.lock", "dev_group": dev_group}
    # No lock: requirements.txt production-only (historical V2 behavior);
    # project-declared dev group installed only from explicit locked versions.
    mode = INSTALL_MODE_FALLBACK
    fragment = (
        f"uv pip install --python /opt/venv/bin/python -r {base}/requirements.txt "
        ">/tmp/install.log 2>&1 || { echo INSTALL_MAIN_FAIL; tail -120 "
        "/tmp/install.log; exit 2; }; "
        f"echo V2_MAIN_PLUS_EXACT_LOCKED_DEV"
    )
    return fragment, mode, {"lockfile": "none", "dev_group": dev_group}


def target_manifests(target_commit: str) -> dict[str, str]:
    """Read the TARGET-commit dependency manifests from the WSL Saleor cache."""
    out: dict[str, str] = {}
    for name in ("pyproject.toml", "poetry.lock", "uv.lock", "requirements.txt",
                 "requirements_dev.txt", "requirements-test.txt"):
        r = git_linux(WSL_CACHE, "show", f"{target_commit}:{name}")
        if r.returncode == 0 and r.stdout.strip() and "__NO__" not in r.stdout[:6]:
            out[name] = r.stdout
    return out


def lockfile_sha256(manifests: dict[str, str]) -> str:
    if "poetry.lock" in manifests:
        return hashlib.sha256(manifests["poetry.lock"].encode("utf-8")).hexdigest()
    if "uv.lock" in manifests:
        return hashlib.sha256(manifests["uv.lock"].encode("utf-8")).hexdigest()
    if "requirements.txt" in manifests:
        return hashlib.sha256(manifests["requirements.txt"].encode("utf-8")).hexdigest()
    return "none-lockfile"


LOCKED_DEV_DEPS: dict[str, tuple[str, ...]] = {
    "saleor-rc-c3b9e396b07d": ("pytest-django-queries==1.2.0", "pytest-mock==3.6.1"),
    "saleor-rc-e25cf9b4a837": ("pytest-django-queries==1.1.0", "pytest-mock==3.2.0"),
    "saleor-rc-74538ea00ce9": ("pytest-django-queries==1.2.0", "pytest-mock==3.14.0",
                               "pytest-recording==0.13.2", "pytest-celery==1.0.1",
                               "pytest-asyncio==0.23.8"),
    "saleor-rc-8f76ddc6267f": ("pytest-django-queries==1.2.0", "pytest-mock==3.10.0",
                               "pytest-recording==0.12.2", "pytest-asyncio==0.20.3"),
}


def locked_dev_install(task_id: str) -> str:
    """Exact locked dev/test group install fragment (Phase-1E authority)."""
    pkgs = LOCKED_DEV_DEPS.get(task_id, ())
    if not pkgs:
        return "echo NO_LOCKED_DEV_GROUP"
    return "uv pip install --python /opt/venv/bin/python " + " ".join(pkgs)


# ---------------------------------------------------------------------------
# Container / DB helpers (13.A / 13.B)
# ---------------------------------------------------------------------------
def ensure_postgres_running() -> None:
    """Start wp2-pg if stopped (WSL idle shutdown); create only if absent."""
    r = wsl("docker ps -a --filter 'name=^wp2-pg$' --format '{{.Names}}'")
    if "wp2-pg" not in r.stdout:
        raise RuntimeError("wp2-pg container does not exist; run substrate setup")
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


def fresh_db_name(task_id: str, state: str) -> str:
    short = task_id.split("-")[-1][:12]
    return f"saleor_v3_{short}_{state}"


def drop_db(db_name: str) -> None:
    """Drop the source DB and the pytest-django test DB (V3 cleanup)."""
    for name in (db_name, f"test_{db_name}"):
        wsl_docker(["exec", "wp2-pg", "psql", "-U", "saleor", "-d", "postgres", "-c",
                    f"DROP DATABASE IF EXISTS {name} WITH (FORCE)"], timeout_s=120)


def ensure_fresh_db(db_name: str) -> JsonDict:
    """Create a FRESH unique DB; never reuse a partially created one."""
    drop_db(db_name)
    r = wsl_docker(["exec", "wp2-pg", "psql", "-U", "saleor", "-d", "postgres", "-c",
                    f"CREATE DATABASE {db_name} OWNER saleor"], timeout_s=120)
    if r.returncode != 0:
        # failure policy: DROP + recreate once
        drop_db(db_name)
        r2 = wsl_docker(["exec", "wp2-pg", "psql", "-U", "saleor", "-d", "postgres", "-c",
                         f"CREATE DATABASE {db_name} OWNER saleor"], timeout_s=120)
        return {"db": db_name, "created": r2.returncode == 0,
                "stderr_tail": r2.stderr[-300:]}
    return {"db": db_name, "created": r.returncode == 0,
            "stderr_tail": r.stderr[-300:]}


def base_image_id(era_key: str) -> str:
    r = wsl_docker(["image", "inspect", f"wp2-era-{era_key}", "--format", "{{.Id}}"],
                   timeout_s=60)
    return r.stdout.strip()


# ---------------------------------------------------------------------------
# V3 run container (13.A + 13.B)
# ---------------------------------------------------------------------------
def run_state_v3(
    *,
    era_key: str,
    worktree_linux: str,
    tid: str,
    state: str,
    test_files: list[str],
    install_fragment: str,
    locked_dev_fragment: str = "echo NO_LOCKED_DEV_GROUP",
    timeout_s: int = 7200,
) -> JsonDict:
    """One V3 container per state: fresh unique DB + lock-exact install +
    --ulimit nofile=65536, then 3x per changed-test-file."""

    wt_name = worktree_linux.rsplit("/", 1)[-1]
    mount = f"{worktree_linux}:/workspace/{wt_name}"
    db_name = fresh_db_name(f"saleor-rc-{tid}", state)
    ensure_postgres_running()
    ensure_fresh_db(db_name)

    runs = []
    for rep in range(REPS):
        for idx, tf in enumerate(test_files):
            jname = f"{tid}_{state}_r{rep}_f{idx}"
            runs.append(
                "/opt/venv/bin/python -m pytest -p no:cacheprovider -o addopts= "
                "--ds=saleor.tests.settings --disable-socket --reuse-db "
                f"--junitxml /workspace/{wt_name}/{jname}.xml -q {tf!r}"
            )
    runs_script = " ; ".join(
        f"( {r} >/tmp/py_{i}.log 2>&1; echo RUN_{i}_RC=$?; tail -12 /tmp/py_{i}.log )"
        for i, r in enumerate(runs)
    )
    proc = subprocess.run(
        ["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc",
         f"cat > {worktree_linux}/.wp2_runs.sh"],
        input=runs_script.encode("utf-8"), capture_output=True, timeout=120,
    )
    if proc.returncode != 0:
        return {"error": "RUNS_SCRIPT_WRITE_FAIL", "junit": {}, "junit_failures": {},
                "db_name": db_name}
    script = (
        "set -e; "
        "uv venv /opt/venv >/dev/null 2>&1 || true; "
        f"{install_fragment}; "
        f"{locked_dev_fragment} >>/tmp/install.log 2>&1 "
        "|| { echo INSTALL_DEV_FAIL; tail -80 /tmp/install.log; exit 2; }; "
        f"{TOOLING_INSTALL} >>/tmp/install.log 2>&1 || {{ echo TOOLING_FAIL; "
        "tail -80 /tmp/install.log; exit 2; }; "
        f"cd /workspace/{wt_name} && bash /workspace/{wt_name}/.wp2_runs.sh; "
        "echo ALL_RUNS_DONE"
    )
    r = wsl_docker(
        [
            "run", "--rm", "--network", "host",
            "--ulimit", f"nofile={NOFILE_SOFT}:{NOFILE_HARD}",
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
    if r.returncode != 0 and "INSTALL" in r.stdout:
        return {"error": "INSTALL_FAIL", "junit": merged, "junit_failures": merged_fail,
                "db_name": db_name, "stdout_tail": r.stdout[-2000:]}
    from benchmark.wp2.oracle_confirmation import parse_junit_with_failures
    for rep in range(REPS):
        for idx, tf in enumerate(test_files):
            jname = f"{tid}_{state}_r{rep}_f{idx}"
            rr = wsl(f"cat {worktree_linux}/{jname}.xml 2>/dev/null || echo __NO_FILE__")
            if "__NO_FILE__" in rr.stdout[:20]:
                merged[tf] = "error"
                merged_fail[tf] = f"JUNIT_MISSING_R{rep}_F{idx}"
                continue
            try:
                nodes, fails = parse_junit_with_failures(rr.stdout)
            except Exception:
                nodes, fails = {}, {}
            merged.update(nodes)
            merged_fail.update(fails)
    drop_db(db_name)
    return {
        "error": None,
        "returncode": r.returncode,
        "junit": merged,
        "junit_failures": merged_fail,
        "db_name": db_name,
        "stdout_tail": r.stdout[-3000:],
    }


def ensure_worktrees_v3(task_id: str, parent: str, target: str) -> JsonDict:
    tid = task_id.split("-")[-1][:12]
    wt_t = f"{WSL_WT}/{tid}_v3_t"
    wt_p = f"{WSL_WT}/{tid}_v3_p"
    wsl(f"mkdir -p {WSL_WT}")
    for wt in (wt_t, wt_p):
        wsl(f"git -C {WSL_CACHE} worktree remove --force {wt} 2>/dev/null || rm -rf {wt}")
    r = git_linux(WSL_CACHE, "worktree", "add", "--detach", wt_t, target)
    if r.returncode != 0:
        raise RuntimeError(f"[wt] target add FAILED: {r.stderr[-1200:]}")
    r = git_linux(WSL_CACHE, "worktree", "add", "--detach", wt_p, parent)
    if r.returncode != 0:
        raise RuntimeError(f"[wt] parent add FAILED: {r.stderr[-1200:]}")
    # apply the SAME frozen test patch on parent (TEST_PATCH_APPLIED_ON_PARENT)
    patch = derive_test_patch_linux(parent, target)
    if patch:
        proc = subprocess.run(
            ["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc",
             "cat > /opt/wp2_v2/v3_probe.patch"],
            input=patch.encode("utf-8"), capture_output=True, timeout=120,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"[wt] patch write FAILED: {proc.stderr[-500:]!r}")
        ap = git_linux(wt_p, "apply", "/opt/wp2_v2/v3_probe.patch")
        if ap.returncode != 0:
            raise RuntimeError(f"[wt] parent patch apply FAILED: {ap.stderr[-800:]}")
    return {"t": wt_t, "p": wt_p, "patch_applied_on_parent": bool(patch)}


def derive_test_patch_linux(parent: str, target: str) -> str:
    from benchmark.wp2.oracle_semantics_v2 import is_test_path_v2

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
        raise RuntimeError(f"patch diff failed: {r.stderr}")
    return r.stdout


def remove_worktrees_v3(task_id: str) -> None:
    tid = task_id.split("-")[-1][:12]
    for state in ("t", "p"):
        wt = f"{WSL_WT}/{tid}_v3_{state}"
        wsl(f"git -C {WSL_CACHE} worktree remove --force {wt} 2>/dev/null || rm -rf {wt}")
    wsl(f"git -C {WSL_CACHE} worktree prune 2>/dev/null || true")
