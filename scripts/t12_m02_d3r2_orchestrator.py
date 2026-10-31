#!/usr/bin/env python3
"""T12 M02-D3-R2 — orchestrator: real Option-B physical execution identity.

Mission: T12_M02_D3R2_OPTION_B_PROCESS_20261028.  Replaces the sequential
same-PID bridge for REAL runs:

* ``preflight`` — read-only admission (platform boundary, frozen pins,
  RD-8/RD-9 gate state, current worktree reality, docker read-only state);
  verdict READY or STOP.
* ``dry-run``    — 13-arm NOT_RUN prospective plan + the four-arm pilot plan,
  PLUS the REVERSIBLE private scratch build of the four pilot execution
  trees (verified against the frozen matrix effective_tree_oid).  Verdict
  READY or STOP.  Zero model calls; no containers/databases started.
* ``run``        — RD-8 + RD-9 gated: ONE new OS child process per arm in the
  frozen control order NEG -> FULL_REFERENCE -> RM_CSS -> SIP; the child runs
  the REAL frozen engine once; the parent cross-checks child witness
  (pid == Popen.pid, nonce, verified process births, argv digest, worker
  source SHA), receipt provenance and bundle identity BEFORE the next arm;
  any control/infra failure stops before SIP.  NEVER reachable in this D3
  offline mission (authorization artifacts do not exist).

Frozen harness/harness pins are read-only; nothing here edits frozen code.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shlex
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

_SCRIPTS = Path(__file__).resolve().parent
PILOT_ARMS = ["SIP", "NEG", "FULL_REFERENCE", "RM_CSS"]
CONTROL_EXECUTION_ORDER = ["NEG", "FULL_REFERENCE", "RM_CSS", "SIP"]
WITHER_SCHEMA = "t12_m02_d3r2_worker_input_v1"
ORCH_SCHEMA_PREFLIGHT = "t12_m02_d3r2_preflight_v1"
ORCH_SCHEMA_DRYRUN = "t12_m02_d3r2_dryrun_v1"
ORCH_SCHEMA_RUN = "t12_m02_d3r2_run_v1"
# Post-kill grace wait that MEASURES whether a timed-out child actually
# terminated (teardown is verified, never asserted).
TERMINATION_GRACE_S = 5.0
# D4: bounded per-probe timeout for the post-timeout descendant containment
# audit (host process-tree, read-only docker ps -a, read-only DB scan).
CONTAINMENT_PROBE_TIMEOUT_S = 120


def _load(rel_name: str, mod_name: str) -> Any:
    spec = importlib.util.spec_from_file_location(mod_name, _SCRIPTS / f"{rel_name}.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


_adapt = _load("t12_m02_arm_adapter", "t12_m02_arm_adapter")
_exe = _load("t12_m02_execute_f2p", "t12_m02_execute_f2p")
_identity = _load("t12_m02_d3r2_identity", "t12_m02_d3r2_identity")
_receipts = _load("t12_m02_receipts", "t12_m02_receipts")


def matrix_pins(matrix_path: Path) -> dict[str, dict[str, str]]:
    rows = _exe._matrix_rows(matrix_path)
    return {r["arm_id"]: r for r in rows}


def read_test_authority(path: Path) -> dict[str, Any]:
    return dict(json.loads(path.read_text(encoding="utf-8")))


def read_classification(path: Path) -> dict[str, str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return dict(raw["changes"])


def baseline() -> dict[str, Any]:
    r = _exe._git(Path.cwd(), "rev-parse", "HEAD")
    b = subprocess.run(["git", "branch", "--show-current"], capture_output=True,
                       text=True, encoding="utf-8", check=False)
    return {
        "schema": "t12_m02_d3r2_baseline_v1",
        "branch": (b.stdout or "").strip(),
        "head": (r.stdout or "").strip(),
        "recorded_at_utc": _identity.utc_now(),
    }


# ---------------------------------------------------------------------------
# preflight
# ---------------------------------------------------------------------------
def preflight(args: argparse.Namespace, _out_root: Path) -> dict[str, Any]:
    """Read-only admission.  Verdict READY only when every provable engineering
    gate passes and the remaining run-mode requirements are explicitly typed
    (RD-8/RD-9 absent is a STOP for EXECUTION, never an engineering READY)."""
    worktree = Path(args.worktree)
    matrix_path = Path(args.matrix) if args.matrix else None
    plan_path = Path(args.plan) if args.plan else None
    probe = _identity.PlatformProbe()
    hard: list[str] = []

    bl = baseline()
    if not worktree.is_dir():
        hard.append("FROZEN_WORKTREE_MISSING")
    head = _exe._git(worktree, "rev-parse", "HEAD").stdout.strip() if worktree.is_dir() else None
    if head != _adapt.FROZEN_WORKTREE_HEAD:
        hard.append(f"WORKTREE_HEAD_DRIFT:{head} != {_adapt.FROZEN_WORKTREE_HEAD}")
    if matrix_path is None or not matrix_path.is_file():
        hard.append("REQUIRED_MATRIX_MISSING")
    else:
        ok, why = _adapt.check_matrix_file(matrix_path)
        if not ok:
            hard.append(f"MATRIX_HASH_MISMATCH:{why}")
    if plan_path is None or not plan_path.is_file():
        hard.append("REQUIRED_PLAN_MISSING")
    else:
        ok, why = _exe._plan_ok(plan_path)
        if not ok:
            hard.append(why)

    # RD-8/RD-9 are researcher-signed artifacts, NOT engineering gates: they
    # are recorded separately so the ENGINEERING verdict (ready/stop) is never
    # conflated with EXECUTION authorization (absent here, by design).
    rd8 = _exe.validate_rd8_decision(args.rd8_decision)
    auth = _exe.validate_authorization(args.authorization, PILOT_ARMS)
    authorization_state = {
        "rd8": rd8,
        "authorization": auth,
        "execution_allowed": rd8["status"] == "ADOPT_PILOT_ONLY" and auth["status"] == "GRANTED",
        "note": "absent by design in D3 (offline engineering); neither inferred nor generated",
    }

    # platform boundary (read-only WSL probes; no container/db started)
    platform = {
        "host_python_kind": probe.host_python_kind(),
        "expected_executor": "windows (frozen harness bridges via wsl.exe CLI)",
        "windows_executor": probe.windows_executor(),
        "wsl_distro": _identity.WSL_DISTRO,
        "distro_present": probe.distro_present(),
        "wsl_root_reachable": probe.root_reachable(),
        "clocks": probe.measure_clocks(),
        "linux_worktree_reality": [],
    }
    if not platform["distro_present"].get("present"):
        hard.append("WSL_DISTRO_MISSING")
    if not platform["wsl_root_reachable"].get("reachable"):
        hard.append("WSL_ROOT_UNREACHABLE")
    if platform["clocks"].get("status") != "MEASURED":
        hard.append("CLOCK_SKEW_UNMEASURED")

    # current reality of the frozen baseline worktree (FULL_REFERENCE tree)
    wt_reality = {}
    if platform["wsl_root_reachable"].get("reachable"):
        base_reality = _identity.linux_worktree_gate(
            probe, _identity.WORKTREE_PATTERN_LINUX,
            "b555542a98f62636173c6c82db80d380c083f180")
        # D5 remediation: a NARROW per-invocation git trust override
        # (git -c safe.directory=<exact path>) may re-measure the frozen tree
        # ONLY when (a) the operator EXPLICITLY requested it with the EXACT
        # frozen path and (b) the WSL stat ownership probe verified the path is
        # a directory.  It never writes git config, never uses a wildcard,
        # never changes ownership, and does NOT weaken the identity gate: the
        # tree OID must still be measured and equal the frozen value, and
        # status / staged-diff must be readable AND empty.
        trust_path = getattr(args, "worktree_git_trust", None)
        ownership = _identity.linux_worktree_ownership(
            probe, _identity.WORKTREE_PATTERN_LINUX)
        trust_admissible = (
            bool(trust_path)
            and trust_path == _identity.WORKTREE_PATTERN_LINUX
            and bool(ownership.get("stat_ok"))
            and bool(ownership.get("is_dir"))
        )
        wt_reality = base_reality
        trusted_reality = None
        if trust_admissible and not base_reality.get("pass"):
            trusted_reality = _identity.linux_worktree_gate(
                probe, _identity.WORKTREE_PATTERN_LINUX,
                "b555542a98f62636173c6c82db80d380c083f180",
                git_trust_path=_identity.WORKTREE_PATTERN_LINUX)
            wt_reality = trusted_reality
        # D5 Defect B: ANY failed Linux worktree identity gate (the ACTIVE
        # reality, i.e. after any admissible trust re-measure) is a typed hard
        # STOP -- never a silent READY.  The recovered PREFLIGHT showed verdict
        # READY with hard_stops [] while the gate reported pass=false (dubious
        # ownership / unreadable status / unverified OID).
        if not wt_reality.get("pass"):
            hard.append("LINUX_WORKTREE_GATE_FAILED:"
                        + " | ".join(wt_reality.get("reasons", [])[:6]))
        if trusted_reality is not None:
            wt_reality["base_without_trust"] = base_reality
        wt_reality["ownership"] = ownership
        wt_reality["git_trust_override"] = {
            "requested": trust_path,
            "exact_path": _identity.WORKTREE_PATTERN_LINUX,
            "applied": trust_admissible,
            "per_invocation_only": True,
            "writes_git_config": False,
            "global_safe_directory": False,
            "wildcard": False,
            "chown": False,
            "ownership_verified": bool(ownership.get("stat_ok")
                                        and ownership.get("is_dir")),
            "note": "git -c safe.directory=<exact path> per invocation only "
                    "after stat-verified path + ownership; tree OID must still "
                    "match the frozen value with readable+empty status/staged diff",
        }
        platform["linux_worktree_reality"] = [wt_reality]

    # engine pins (read-only hashes)
    engines = _exe._driver.engine_scripts_pin_status(worktree) if worktree.is_dir() else {}
    bad_engines = [rel for rel, st in engines.items() if not st.get("ok")]
    if bad_engines:
        hard.append("ENGINE_PIN_DRIFT:" + ",".join(bad_engines))

    # read-only docker state
    docker = None
    if platform["wsl_root_reachable"].get("reachable"):
        docker = probe.docker_preflight_reads()
        if not docker.get("server_ok"):
            hard.append("DOCKER_SERVER_UNREACHABLE")
        if not docker.get("pinned_image", {}).get("present"):
            hard.append("PINNED_IMAGE_MISSING")
        if docker.get("pg_fixture", {}).get("status") != "running":
            hard.append("PG_FIXTURE_NOT_RUNNING")
        if not docker.get("network", {}).get("internal"):
            hard.append("INTERNAL_NETWORK_MISSING")

    # container instance evidence is only capturable inside a REAL arm window:
    container_instances = {
        "container_instance_status": "CONTAINER_INSTANCE_NOT_MEASURED",
        "note": "docker-events per-arm window capture is a run-mode measure; "
                "preflight only proves the read-only probe surface",
    }
    db_scan: dict[str, Any] = {
        "T12_M02_DB_SCAN_CMD_configured": bool(os.environ.get("T12_M02_DB_SCAN_CMD")),
        "required_for_real_run": True,
    }
    if not db_scan["T12_M02_DB_SCAN_CMD_configured"]:
        db_scan["note"] = "operator must supply the read-only DB scan command before any run"

    # first calibration ADMISSION artifact is ENGINEERING-LEVEL only
    admission = {
        "first_calibration_authorized": False,
        "status": "NOT_AUTHORIZED",
        "note": "engineering gates only; RD-8 pilot derivation and RD-9 exclusive window/"

                "cap are researcher-signed artifacts and are ABSENT",
    }
    result = {
        "schema": ORCH_SCHEMA_PREFLIGHT,
        "mode": "PREFLIGHT",
        "baseline": bl,
        "verdict": "STOP" if hard else "READY",
        "hard_stops": hard,
        "platform": platform,
        "engines": engines,
        "docker_readonly": docker,
        "container_instances": container_instances,
        "db_scan": db_scan,
        "rd8": rd8,
        "authorization": auth,
        "authorization_state": authorization_state,
        "admission": admission,
        "all_13_not_run": True,
        "model_request_count": 0,
        "model_usd": 0.0,
        "env": "D3_ENGINEERING_ONLY",
        "generated_at_utc": _identity.utc_now(),
    }
    return result


# ---------------------------------------------------------------------------
# dry-run (read-only + reversible private scratch tree build)
# ---------------------------------------------------------------------------
def dry_run(args: argparse.Namespace, out_root: Path) -> dict[str, Any]:
    pre = preflight(args, out_root)
    worktree = Path(args.worktree)
    matrix_path = Path(args.matrix)
    plan_path = Path(args.plan)
    arms = [a for a in CONTROL_EXECUTION_ORDER if a in PILOT_ARMS]

    # 13-arm NOT_RUN enumeration (read-only)
    all_arms = _exe.build_plan(
        worktree, Path(args.source_repo) if args.source_repo else _adapt.FROZEN_SOURCE_SALEOR_REPO,
        matrix_path, plan_path,
        Path(args.scopes_dir) if args.scopes_dir else None,
        Path(args.classification) if args.classification else None,
        Path(args.test_authority) if args.test_authority else None,
        [a["arm_id"] for a in _adapt.load_arms()],
        args.worktrees_json, out_root / "dryrun_plan_out",
    )
    # prospective four-arm plan (all NOT_RUN)
    pilot = [_exe.physical_plan_for(a, matrix_by_arm=matrix_pins(matrix_path),
                                    worktrees={x: f"<PROPOSED_SCRATCH>/arm_{x}/wt_t"
                                               for x in PILOT_ARMS},
                                    out_root=out_root / "pilot_plan") for a in PILOT_ARMS]
    for p in pilot:
        p["status"] = "NOT_RUN"

    # REVERSIBLE PRIVATE scratch tree build for the pilot arms (mission 2)
    scratch_win = out_root / "scratch"
    scratch_linux = args.scratch_linux or "/root/t12_m02_d3r2_scratch_20261028"
    probe = _identity.PlatformProbe()
    scope_dir = Path(args.scopes_dir)
    classification = read_classification(Path(args.classification))
    test_authority = read_test_authority(Path(args.test_authority))
    matrix = matrix_pins(matrix_path)
    patches: dict[str, Any] = {}
    patch_issues: dict[str, str] = {}
    for arm in arms:
        row = matrix[arm]
        try:
            patches[arm] = _identity.materializer_patches(
                frozen_stage=worktree, arm=arm,
                scope_json=scope_dir / f"scope_{arm}.json",
                classification=classification, test_authority=test_authority,
                source_repo=Path(args.source_repo) if args.source_repo else _adapt.FROZEN_SOURCE_SALEOR_REPO,
                parent_commit=_adapt.FROZEN_PARENT,
                target_commit=_adapt.FROZEN_TARGET,
                task_id=_adapt.FROZEN_TASK,
                ref_pin_sha256=row["patch_sha256"],
                ref_pin_bytes=int(row["patch_bytes"]),
                scope_hash_pin=row["scope_hash"],
            )
            if not patches[arm]["pins_ok"]:
                patch_issues[arm] = ";".join(patches[arm]["issues"][:4])
        except Exception as exc:
            patch_issues[arm] = f"{type(exc).__name__}: {exc}"
    tree_build: dict[str, Any] = {}
    if not patch_issues:
        tree_build = _identity.build_scratch_arm_trees(
            probe=probe, scratch_root_windows=scratch_win,
            scratch_root_linux=scratch_linux,
            cache_repo_linux=_identity.LINUX_CACHE_REPO,
            parent_commit=_adapt.FROZEN_PARENT,
            patches_by_arm=patches, matrix_by_arm=matrix, arms=arms)
        tree_match = tree_build.get("all_match")
    else:
        tree_match = False
    trees_proven = bool(tree_match)
    verdict = pre.get("verdict")
    if not trees_proven:
        verdict = "STOP"
    return {
        "schema": ORCH_SCHEMA_DRYRUN,
        "mode": "DRY_RUN",
        "preflight": {k: pre.get(k) for k in ("verdict", "hard_stops", "platform",
                                              "docker_readonly", "db_scan", "rd8",
                                              "authorization", "admission")},
        "verdict": verdict,
        "thirteen_arms": {
            "count": len(all_arms["arms"]),
            "not_run": all_arms["all_status_not_run"],
            "model_usd": all_arms["total_prospective_model_usd"],
            "model_requests": all_arms["total_prospective_model_requests"],
        },
        "pilot_plan": {
            "arms": PILOT_ARMS,
            "control_order": CONTROL_EXECUTION_ORDER,
            "junit_per_arm": _exe.PILOT_JUNIT_PER_ARM,
            "junit_total": _exe.PILOT_JUNIT_PER_ARM * len(PILOT_ARMS),
            "nodes": list(_adapt.F2P_NODES),
            "nodes_pin": _adapt.F2P_NODES_SHA256,
            "per_arm": pilot,
            "model_request_count": 0,
            "model_usd": 0.0,
            "p2p": "NOT_QUALIFIED: strictly F2P-only calibration",
            "inferential_claim": "NONE: N=1 task, 3 nodes x 3 reps = stability only",
        },
        "patch_pins_reproduced": {a: (a not in patch_issues) for a in arms},
        "patch_issues": patch_issues,
        "scratch_trees": {
            "proven": trees_proven,
            "scratch_root_windows": str(scratch_win),
            "scratch_root_linux": scratch_linux,
            "builder": "minimal scratch-only builder (private/reversible; no source writes)",
            "detail": tree_build,
        },
        "container_instances": pre["container_instances"],
        "db_scan": pre["db_scan"],
        "admission_first_calibration": {
            "status": "NOT_AUTHORIZED",
            "RD8": "ABSENT (researcher-signed artifact; schema in FIRST_CALIBRATION_ADMISSION.json)",
            "RD9": "ABSENT (researcher-signed artifact; schema in FIRST_CALIBRATION_ADMISSION.json)",
        },
        "all_13_not_run": True,
        "generated_at_utc": _identity.utc_now(),
    }


# ---------------------------------------------------------------------------
# run (RD-8/RD-9 gated; never reached in D3)
# ---------------------------------------------------------------------------
def _derived_deadline_utc(
    authorization: dict[str, Any],
    budget: dict[str, Any],
    *,
    now_utc: Any | None = None,
) -> str:
    """Real UTC wall deadline for a gated run: the EARLIEST of
    now + authorization max_wall_s, now + budget max_wall_s and the approved
    RD-9 exclusivity-window end — i.e. bounded by BOTH the window end and the
    authorized wall cap.  Fail closed: an unparseable window end raises
    WALL_DEADLINE_INVALID."""
    import datetime

    window_end = _exe._parse_utc_iso(authorization.get("parsed_window_utc", {}).get("end"))
    if window_end is None:
        raise RuntimeError("WALL_DEADLINE_INVALID")
    now_dt: datetime.datetime = datetime_now() if now_utc is None else now_utc
    caps = [float(authorization.get("max_wall_s", 0.0)),
            float(budget.get("max_wall_s", 0.0))]
    remaining_window_s: float = float((window_end - now_dt).total_seconds())
    deadline_s = min(caps + [remaining_window_s])
    return (now_dt + datetime.timedelta(seconds=deadline_s)).isoformat()


def run(args: argparse.Namespace, out_root: Path) -> dict[str, Any]:
    """Gated real execution: one NEW OS child per arm.  Execution path exists
    ONLY to prove that real run-mode code uses the real pinned engine; D3
    cannot reach it (no RD-8/RD-9 artifacts exist)."""
    gates: dict[str, Any] = {}
    worktree = Path(args.worktree)
    arms = [a for a in CONTROL_EXECUTION_ORDER if a in PILOT_ARMS]
    rd8 = _exe.validate_rd8_decision(args.rd8_decision)
    auth = _exe.validate_authorization(args.authorization, PILOT_ARMS)
    hard: list[str] = []
    if rd8["status"] != "ADOPT_PILOT_ONLY":
        hard.append("RD8_APPROVAL_PENDING" if rd8.get("present") is False else "RD8_DECISION_INVALID")
    if auth["status"] != "GRANTED":
        hard.append("EXECUTION_NOT_AUTHORIZED" if auth.get("present") is False else "AUTHORIZATION_INVALID")
    if args.autorun_in_d3_flag != "NEVER_IN_D3":
        hard.append("AUTORUN_FLAG_MISSING_OR_WRONG")
    if not os.environ.get("T12_M02_DB_SCAN_CMD"):
        hard.append("TEARDOWN_SCAN_CMD_UNCONFIGURED")
    # D5 Defect A contract: --worktrees-json is a JSON FILE PATH in BOTH
    # modes (dry-run reads it through the shared planner; run() now too).
    # Live execution never parses inline JSON and never silently substitutes
    # proposed paths: every missing/malformed/inconsistent input is a typed
    # hard stop before ANY side effect.
    try:
        worktrees = _exe.resolve_worktrees_required(arms, args.worktrees_json)
    except ValueError as exc:
        worktrees = {}
        hard.append(str(exc))
    if hard:
        gates.update({
            "schema": ORCH_SCHEMA_RUN, "mode": "RUN",
            "outcome": "STOP_NOT_AUTHORIZED", "executed": False,
            "hard_stops": hard, "arms": [],
            "generated_at_utc": _identity.utc_now(),
        })
        return gates
    budget = _exe.validate_budget(Path(args.budget_json), args.wall_max_s, dict(auth))
    if budget["status"] != "OK":
        gates.update({"schema": ORCH_SCHEMA_RUN, "mode": "RUN",
                      "outcome": "STOP_GATE_NOT_OPEN", "executed": False,
                      "hard_stops": ["BUDGET_INVALID:" + budget["reason"]]})
        return gates

    matrix = matrix_pins(Path(args.matrix))
    scope_dir = Path(args.scopes_dir)
    sim_worker = args.worker_path or str(_SCRIPTS / "t12_m02_d3r2_worker.py")
    # Round 2 safety: forward a REAL UTC deadline bounded by BOTH the
    # approved RD-9 exclusivity-window end and the authorized max_wall_s
    # (the admitted budget), never None — so the wall cap is actually
    # enforced by run_arms_physical.
    deadline_utc = _derived_deadline_utc(auth, budget)
    return run_arms_physical(
        out_root=out_root, arms=arms, worktree=worktree,
        source_repo=Path(args.source_repo) if args.source_repo else _adapt.FROZEN_SOURCE_SALEOR_REPO,
        scope_dir=scope_dir, classification=Path(args.classification),
        test_authority=Path(args.test_authority), matrix=matrix,
        worktrees=worktrees,
        db_scan_cmd_env=os.environ.get("T12_M02_DB_SCAN_CMD"),
        worker_path=sim_worker, docker_events=True,
        deadline_utc=deadline_utc, spawner=None)


def spawn_worker_proc(worker_path: str, witness_input: Path, arm_dir: Path,
                      python_exe: str | None = None) -> tuple[Any, str]:
    """Launch ONE new OS child process (real subprocess; never reused)."""
    exe = python_exe or sys.executable
    argv = [exe, str(worker_path), "--witness-input", str(witness_input), "--out", str(arm_dir)]
    with open(arm_dir / "child_stdout.log", "w", encoding="utf-8") as so, \
         open(arm_dir / "child_stderr.log", "w", encoding="utf-8") as se:
        proc = subprocess.Popen(argv, stdout=so, stderr=se, text=True, encoding="utf-8")
    return proc, " ".join(argv)


def _split_db_scan_cmd(cmd: str | None) -> list[str]:
    """Split the operator-supplied read-only DB-scan command with the SAME
    semantics as the worker: POSIX splitting on POSIX, Windows splitting
    (posix=False) on Windows Python — quoted paths with spaces must survive as
    one token (proven scanner DB_SCAN_OPWS.ps1, never reinterpreted).

    Raises TEARDOWN_NOT_VERIFIED when no scanner is configured."""
    if not cmd:
        raise RuntimeError("TEARDOWN_NOT_VERIFIED: T12_M02_DB_SCAN_CMD not configured")
    return shlex.split(cmd, posix=(os.name != "nt"))


def _container_snapshot(probe: Any, timeout_s: int = CONTAINMENT_PROBE_TIMEOUT_S) -> dict[str, Any]:
    """Bounded READ-ONLY ``docker ps -a`` snapshot (never starts anything)."""
    r = probe.docker_readonly(
        ["ps", "-a", "--format", "{{.ID}}|{{.Names}}|{{.Image}}"], timeout_s)
    ok = getattr(r, "returncode", None) == 0
    lines = [ln.strip() for ln in (r.stdout or "").splitlines() if ln.strip()]
    return {
        "status": "MEASURED" if ok else "NOT_MEASURED",
        "containers": lines,
        "reason": str(r.stderr or "")[-200:] if not ok else "",
    }


def _process_tree_probe(child_pid: int, host_runner: Callable[..., Any],
                        timeout_s: int = CONTAINMENT_PROBE_TIMEOUT_S) -> dict[str, Any]:
    """HOST-side recursive descendant query (PowerShell/CIM): every Windows
    process whose ancestry reaches the killed child (incl. the wsl.exe clients
    the worker may have spawned).  Bounded; NOT_MEASURED on any probe failure.

    ``proc.kill()`` terminates only the direct Windows Python worker; this is
    the measured check that no descendent process survived it."""
    ps = (
        "$all = Get-CimInstance Win32_Process; "
        f"$root = @({int(child_pid)}); $desc = @(); "
        "while ($true) { $kids = @($all | Where-Object { $root -Contains $_.ParentProcessId }); "
        "if ($kids.Count -eq 0) { break }; "
        "$root = @($kids | ForEach-Object { $_.ProcessId }); $desc += $root; }; "
        "($desc | Select-Object -Unique) -join '|'"
    )
    r = host_runner(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps],
        None, timeout_s)
    if getattr(r, "returncode", None) != 0:
        return {"status": "NOT_MEASURED",
                "reason": f"process tree probe failed rc={r.returncode}: {(r.stderr or '')[-200:]}",
                "pids": []}
    pids = [p.strip() for p in (r.stdout or "").split("|") if p.strip()]
    return {"status": "MEASURED", "pids": pids}


def _db_scan_leftovers(db_scan_cmd_env: str | None, host_runner: Callable[..., Any],
                       timeout_s: int = CONTAINMENT_PROBE_TIMEOUT_S) -> dict[str, Any]:
    """Read-only DB leftover scan through the operator's proven scanner (same
    posix= semantics as the worker).  NOT_MEASURED on any failure."""
    if not db_scan_cmd_env:
        return {"status": "NOT_MEASURED",
                "reason": "T12_M02_DB_SCAN_CMD not configured", "leftovers": []}
    try:
        argv = _split_db_scan_cmd(db_scan_cmd_env)
    except Exception as exc:
        return {"status": "NOT_MEASURED",
                "reason": f"DB_SCAN_UNSPLITTABLE: {exc}", "leftovers": []}
    r = host_runner(argv, None, timeout_s)
    if getattr(r, "returncode", None) != 0:
        return {"status": "NOT_MEASURED",
                "reason": f"DB scan failed rc={getattr(r, 'returncode', None)}: {(r.stderr or '')[-200:]}",
                "leftovers": []}
    leftovers = [t.strip() for t in (r.stdout or "").splitlines()
                 if _receipts.DB_IDENTITY_RE.match(t.strip())]
    return {"status": "MEASURED", "leftovers": leftovers}


def containment_audit(
    *,
    child_pid: int,
    direct_child_exited: bool,
    probe: Any,
    baseline_containers: list[str] | None,
    db_scan_cmd_env: str | None,
    spawned_utc: str,
    host_runner: Callable[..., Any] | None = None,
    per_probe_timeout_s: int = CONTAINMENT_PROBE_TIMEOUT_S,
) -> dict[str, Any]:
    """MEASURED, bounded, post-timeout descendant containment audit.

    The parent's ``proc.kill()`` proves only the direct Windows Python worker
    ended; it is NOT proof that descendant WSL processes, Docker containers or
    DB activity ended.  This audit probes (all bounded, all best-effort with
    a typed NOT_MEASURED on failure):
      1. direct child exit (caller-measured post-kill grace wait);
      2. host process-tree descendants of the child (PowerShell/CIM);
      3. docker containers beyond the pre-spawn baseline (read-only ps -a);
      4. opws databases left by the run (operator's read-only scanner).

    Status is CONTAINMENT_VERIFIED ONLY when every probe measured EMPTY; any
    unmeasurable or resident resource => CONTAINMENT_UNVERIFIED with the
    resident resources REPORTED (the STOP contract: keep STOP and report
    unverified resources instead of claiming success).  The long-lived PG
    fixture is never deleted and never counted as a leftover.  Never raises."""
    host_runner = host_runner or _identity.make_host_runner(per_probe_timeout_s)
    tree = _process_tree_probe(child_pid, host_runner, per_probe_timeout_s)
    # Always attempt the read-only post-timeout docker snapshot (it reports
    # what is CURRENTLY resident even when no pre-spawn baseline exists);
    # attribution ("new vs baseline") additionally needs the pre-spawn shot.
    cur = _container_snapshot(probe, per_probe_timeout_s)
    docker_status = cur["status"]
    docker_reason = str(cur.get("reason") or "")
    new_containers: list[str] = []
    attribution_ok = baseline_containers is not None and docker_status == "MEASURED"
    if attribution_ok and baseline_containers is not None:
        baseline_set = set(baseline_containers)
        new_containers = [
            line for line in cur["containers"]
            if line not in baseline_set
            and f"|{_identity.PG_FIXTURE}|" not in line
            and not line.startswith("|")
        ]
    elif baseline_containers is None and docker_status == "MEASURED":
        docker_reason = "no pre-spawn docker baseline available; surviving containers cannot be attributed"
    db = _db_scan_leftovers(db_scan_cmd_env, host_runner, per_probe_timeout_s)
    resident = {
        "processes": tree.get("pids", []) if tree["status"] == "MEASURED" else [],
        "containers": new_containers,
        "opws_databases": db.get("leftovers", []) if db["status"] == "MEASURED" else [],
    }
    measured_clean = (
        bool(direct_child_exited)
        and tree["status"] == "MEASURED" and not tree.get("pids")
        and docker_status == "MEASURED" and attribution_ok and not new_containers
        and db["status"] == "MEASURED" and not db.get("leftovers")
    )
    return {
        "schema": "t12_m02_d3r2_containment_audit_v1",
        "status": "CONTAINMENT_VERIFIED" if measured_clean else "CONTAINMENT_UNVERIFIED",
        "direct_child_exited": bool(direct_child_exited),
        "resident_resources": resident,
        "probes": {
            "process_tree": tree,
            "docker": {"status": docker_status, "reason": docker_reason,
                        "new_containers": new_containers,
                        "attribution_ok": attribution_ok,
                        "baseline_containers": baseline_containers is not None,
                        "pg_fixture_preserved": True},
            "db_scan": db,
        },
        "spawned_utc": spawned_utc,
        "measured_at_utc": _identity.utc_now(),
        "bounded_by": {
            "per_probe_timeout_s": per_probe_timeout_s,
            "note": "every probe bounded separately; the audit never waits unboundedly",
        },
    }


def run_arms_physical(
    *,
    out_root: Path,
    arms: list[str],
    worktree: Path,
    source_repo: Path,
    scope_dir: Path,
    classification: Path,
    test_authority: Path,
    matrix: dict[str, dict[str, str]],
    worktrees: dict[str, str],
    db_scan_cmd_env: str | None,
    worker_path: str,
    docker_events: bool,
    deadline_utc: str | None,
    spawner: Callable[[str, Path, Path], tuple[Any, str]] | None = None,
    probe: Any = None,
    containment_host_runner: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """One child per arm, cross-checked by the parent, stop-before-SIP."""
    spawner = spawner or (lambda w, wi, ad: spawn_worker_proc(w, wi, ad))
    probe = probe if probe is not None else _identity.PlatformProbe()
    arms_results: list[dict[str, Any]] = []
    witnesses: list[tuple[str, dict[str, Any]]] = []
    note: list[str] = []
    overall = "FAIL"
    stop_reason: str | None = None
    deadline_dt: Any = None
    if deadline_utc is not None:
        deadline_dt = _exe._parse_utc_iso(deadline_utc)
        if deadline_dt is None:
            raise RuntimeError("WALL_DEADLINE_INVALID")
    for arm in arms:
        arm_dir = out_root / f"arm_{arm}"
        stage: dict[str, Any] = {"arm_id": arm, "status": "NOT_RUN",
                                 "control_outcome": "NOT_RUN"}
        if stop_reason is not None:
            stage["reason"] = stop_reason
            arms_results.append(stage)
            continue
        # Enforced BEFORE this arm spawns (deadline is re-checked every arm):
        # STOP, never start the arm, record truthful partial evidence with
        # the measured deadline and check time.
        if deadline_dt is not None:
            remaining_s = (deadline_dt - datetime_now()).total_seconds()
            if remaining_s <= 0:
                stage["reason"] = "WALL_DEADLINE_EXCEEDED"
                stage["stages"] = {
                    "deadline": {
                        "deadline_utc": deadline_dt.isoformat(),
                        "checked_utc": datetime_now().isoformat(),
                        "remaining_s": 0.0,
                    }
                }
                overall = "FAIL"
                stop_reason = "WALL_DEADLINE_EXCEEDED: stop-before-SIP"
                note.append("WALL_DEADLINE_EXCEEDED:" + arm)
                arms_results.append(stage)
                continue
        try:
            if arm_dir.exists():
                raise RuntimeError("ARM_DIR_REUSE")
            arm_dir.mkdir(parents=True, exist_ok=False)
            row = matrix[arm]
            wt_linux = worktrees.get(arm) or f"<MISSING_WORKTREE_FOR_{arm}>"
            if not wt_linux or wt_linux.startswith("<MISSING"):
                raise RuntimeError("WORKTREES_JSON_MISSING_ARM")
            nonce = _identity.new_nonce()
            witness_input = {
                "schema": WITHER_SCHEMA, "arm": arm, "arm_dir": str(arm_dir),
                "nonce": nonce,
                "worktree": str(worktree), "source_repo": str(source_repo),
                "scopes_dir": str(scope_dir), "classification": str(classification),
                "test_authority": str(test_authority),
                "worktree_linux": wt_linux, "effective_tree_oid": row["effective_tree_oid"],
                "scope_hash": row["scope_hash"], "patch_sha256": row["patch_sha256"],
                "patch_bytes": int(row["patch_bytes"]),
                "materializer_rel": _exe.MATERIALIZER_REL,
                "execution_id": _adapt.execution_id_for(arm, "M02E-PILOT"),
                "scratch_linux_base": os.environ.get("T12_M02_SCRATCH_LINUX", "/results"),
                "docker_events": docker_events,
                # D4: the worker's docker-events stream upper bound — the real
                # wall deadline (never None in a gated run), guaranteeing the
                # stream covers the engine interval with finite termination.
                "events_until_utc": deadline_utc,
                "db_scan_cmd_env_digest": _identity.argv_digest([db_scan_cmd_env or ""]),
            }
            (arm_dir / "witness_input.json").write_text(
                json.dumps(witness_input, indent=2), encoding="utf-8")
            pre_gate = _identity.linux_worktree_gate(probe, wt_linux, row["effective_tree_oid"])
            stage["stages"] = {"worktree_gate_pre": pre_gate}
            if not pre_gate["pass"]:
                raise RuntimeError("WORKTREE_GATE_FAILED_PRE:" + ";".join(pre_gate["reasons"]))
            spawned_utc = _identity.utc_now()
            # D4: read-only pre-spawn docker baseline (diffed at a wall timeout
            # to attribute surviving containers; never starts anything).
            baseline_snapshot = _container_snapshot(probe) if docker_events else {
                "status": "NOT_MEASURED", "containers": []}
            proc, argv_text = spawner(worker_path, arm_dir / "witness_input.json", arm_dir)
            child_pid = proc.pid
            run_done = False
            deadline_s = None
            if deadline_dt is not None:
                deadline_s = max(0.01, (deadline_dt - datetime_now()).total_seconds())
            try:
                rc = proc.wait(timeout=deadline_s)
                run_done = True
            except subprocess.TimeoutExpired:
                # Wall cap hit while the child is still running: STOP this
                # arm with truthful partial evidence.  ``proc.kill()`` only
                # terminates the direct Windows Python worker — descendant WSL
                # processes, Docker containers and DB activity MUST be MEASURED
                # (containment audit), never asserted.  Unverified resources
                # keep STOP and are reported; success is never claimed.
                run_done = False
                proc.kill()
                child_terminated = False
                try:
                    proc.wait(timeout=TERMINATION_GRACE_S)
                    child_terminated = True
                except subprocess.TimeoutExpired:
                    child_terminated = False
                audit = containment_audit(
                    child_pid=child_pid,
                    direct_child_exited=child_terminated,
                    probe=probe,
                    baseline_containers=(
                        list(baseline_snapshot.get("containers") or [])
                        if baseline_snapshot.get("status") == "MEASURED" else None),
                    db_scan_cmd_env=db_scan_cmd_env,
                    spawned_utc=spawned_utc,
                    host_runner=containment_host_runner)
                audit["baseline_container_snapshot"] = baseline_snapshot
                rc = -999
                stage["stages"]["child_spawn"] = {
                    "argv": argv_text,
                    "argv_digest": _identity.argv_digest(argv_text.split()),
                    "child_pid": child_pid,
                    "spawned_utc": spawned_utc,
                    "exit_code": None,
                    "ran_to_completion": False,
                    "wall_timeout": True,
                    "child_terminated_verified": child_terminated,
                }
                stage["stages"]["containment"] = audit
                note.append(f"CHILD_WALL_TIMEOUT:{arm} containment={audit['status']}")
                raise RuntimeError(
                    f"CHILD_WALL_TIMEOUT:{arm} terminated_verified={child_terminated} "
                    f"containment={audit['status']}") from None
            stage["stages"]["child_spawn"] = {
                "argv": argv_text, "argv_digest": _identity.argv_digest(argv_text.split()),
                "child_pid": child_pid, "spawned_utc": spawned_utc, "exit_code": rc,
                "ran_to_completion": run_done,
            }
            widx = arm_dir / "witness.json"
            if not widx.is_file():
                raise RuntimeError("WORKER_WITNESS_MISSING")
            w = json.loads(widx.read_text(encoding="utf-8"))
            stage["stages"]["child_witness"] = w
            if w.get("pid") != child_pid:
                raise RuntimeError(
                    f"WITNESS_PID_MISMATCH: witness {w.get('pid')} != Popen pid {child_pid} "
                    "(replayed or forged worker evidence)")
            vw = _identity.validate_witness(w)
            if vw["status"] != "PASS":
                raise RuntimeError("WITNESS_INVALID:" + ";".join(vw["issues"][:6]))
            witnesses.append((arm, w))
            # worktree checked AGAIN after use (mission 2)
            post_gate = _identity.linux_worktree_gate(probe, wt_linux, row["effective_tree_oid"])
            stage["stages"]["worktree_gate_post"] = post_gate
            if not post_gate["pass"]:
                raise RuntimeError("WORKTREE_GATE_FAILED_POST:" + ";".join(post_gate["reasons"]))
            if (arm_dir / "worker_stage.json").is_file():
                ws = json.loads((arm_dir / "worker_stage.json").read_text(encoding="utf-8"))
                stage["status"] = ws.get("status", "FAIL")
                stage["control_outcome"] = ws.get("control_outcome", "NOT_RUN")
                stage["worker_stage_status"] = ws.get("status")
                if rc != 0 and ws.get("status") == "FAIL":
                    raise RuntimeError("WORKER_ARM_FAILED:" + str(ws.get("reason"))[:300])
            if stage["status"] not in ("PASS", "CONTROL_EXPECTED"):
                stage["reason"] = stage.get("reason") or f"WORKER_ARM_FAILED rc={rc}"
                raise RuntimeError(stage["reason"])
            # receipt provenance (real validator)
            vres = _receipts.validate_run_receipt(arm_dir / "receipts")
            if vres["status"] != "PASS":
                raise RuntimeError("RECEIPT_INVALID_AFTER_RUN:" + ";".join(vres.get("issues") or [])[:8])
            stage["executed"] = True
        except Exception as exc:
            stage["status"] = "FAIL"
            stage["reason"] = f"{type(exc).__name__}: {exc}"
            overall = "FAIL"
            stop_reason = f"STOP_AFTER_{arm}_FAILURE (stop-before-SIP)"
        arms_results.append(stage)

    # cross-arm identity certificates
    identity_ok = True
    ident = None
    if len(witnesses) >= 2:
        ident = _identity.bundle_identity_check(witnesses)
        if ident["status"] != "PASS":
            identity_ok = False
            overall = "FAIL"
            note.append("IDENTITY_VIOLATION:" + ";".join(ident["issues"][:6]))
        else:
            note.append("PROCESS_IDENTITY_PROVEN:" +
                        ";".join(ident["signals"][:3]) if ident["signals"] else "PROCESS_IDENTITY_PROVEN")
    had_failure = any(a.get("status") == "FAIL" for a in arms_results)
    if not stop_reason and not had_failure and identity_ok:
        overall = "PASS"
    return {
        "schema": ORCH_SCHEMA_RUN, "mode": "RUN", "overall": overall,
        "arms": arms_results, "process_identity": ident if len(witnesses) >= 2 else None,
        "note": " | ".join(note) if note else "ok",
        "generated_at_utc": _identity.utc_now(),
    }


def datetime_now() -> Any:
    import datetime

    return datetime.datetime.now(datetime.UTC)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="t12_m02_d3r2_orchestrator",
                                 description="D3-R2 Option-B identity orchestrator (offline).")

    def _shared(p: argparse.ArgumentParser) -> None:
        p.add_argument("--out", required=True)
        p.add_argument("--worktree", default=str(_adapt.FROZEN_WORKTREE_ROOT_DEFAULT))
        p.add_argument("--source-repo", default=None)
        p.add_argument("--matrix", required=True)
        p.add_argument("--plan", required=True)
        p.add_argument("--scopes-dir", default=None)
        p.add_argument("--classification", default=None)
        p.add_argument("--test-authority", default=None)
        p.add_argument("--scratch-linux", default=None)
        p.add_argument(
            "--worktree-git-trust", default=None,
            help="exact frozen Linux worktree path for a NARROW per-invocation "
                 "git -c safe.directory=<path> override (D5: applied only after "
                 "stat-verified path + ownership; tree OID and clean status "
                 "still required; never global/wildcard/chown)")

    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("preflight")
    _shared(p)
    p.add_argument("--rd8-decision", default=None)
    p.add_argument("--authorization", default=None)
    p = sub.add_parser("dry-run")
    _shared(p)
    p.add_argument("--rd8-decision", default=None)
    p.add_argument("--authorization", default=None)
    p.add_argument("--worktrees-json", default=None)
    p = sub.add_parser("run")
    _shared(p)
    p.add_argument("--rd8-decision", default=None)
    p.add_argument("--authorization", default=None)
    p.add_argument("--budget-json", default=None)
    p.add_argument("--wall-max-s", type=float, default=None)
    p.add_argument("--worktrees-json", required=True)
    p.add_argument("--autorun-in-d3-flag", default=None)
    p.add_argument("--worker-path", default=None)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    out_root = Path(args.out)
    if out_root.exists():
        print(f"OUT_DIR_EXISTS: {out_root} (never reuse a results directory)", file=sys.stderr)
        return 5
    out_root.mkdir(parents=True, exist_ok=False)
    if args.command == "preflight":
        res = preflight(args, out_root)
        (out_root / "PREFLIGHT.json").write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
        print(json.dumps(res, indent=2, default=str))
        return 4 if res["verdict"] == "STOP" else 0
    if args.command == "dry-run":
        res = dry_run(args, out_root)
        (out_root / "EXECUTION_PLAN.json").write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
        print(json.dumps({k: res[k] for k in ("schema", "mode", "verdict", "thirteen_arms",
                                              "pilot_plan", "patch_pins_reproduced",
                                              "scratch_trees", "admission_first_calibration",
                                              "all_13_not_run", "generated_at_utc")}, indent=2))
        return 4 if res["verdict"] == "STOP" else 0
    if args.command == "run":
        res = run(args, out_root)
        (out_root / "RUN_GATE.json").write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
        print(json.dumps(res, indent=2, default=str))
        return 4 if str(res.get("outcome", "")).startswith("STOP") else (0 if res.get("overall") == "PASS" else 5)
    return 3


if __name__ == "__main__":
    sys.exit(main())
