#!/usr/bin/env python3
"""T12 M02-D3-R2 — one-arm OS child (NEW interpreter PER arm).

Mission: T12_M02_D3R2_OPTION_B_PROCESS_20261028.  The parent orchestrator
launches ONE new OS process per arm (the frozen control order); this worker
executes exactly ONE arm through the REAL frozen engine once:

  1. truthful process witness (pid, parent pid, argv digest, worker source
     SHA, UTC start/end, monotonic birth markers, OS-verified process start);
  2. real frozen materializer subprocess (engineering record);
  3. real frozen ``harness_v3.run_state_v3`` with ``OpwsIsolatedRuntime``
     (frozen modules imported read-only from the frozen worktree);
  4. canonical JUnit evidence (9 per arm) + control classification;
  5. real post-run DB scan (operator-supplied command) + read-only snapshot
     hash of the scan;
  6. LIVE receipt built ONLY from measured evidence (no ``sample_run_receipt``
     seeding; network bytes NOT_MEASURED unless actually sampled) and validated
     by the real validator;
  7. bounded read-only docker-events capture for container INSTANCE evidence
     (an image digest is never presented as a container id).

This file is the deployable child of the D3-R2 orchestrator.  It is NEVER
invoked in this offline mission (``run`` stays RD-8/RD-9 gated and absent);
it exists so the run-mode path provably uses only real pinned engine
functions.  Test doubles appear only in unit tests.
"""
from __future__ import annotations

import argparse
import datetime
import importlib.util
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

_SCRIPTS = Path(__file__).resolve().parent


def _load(rel_name: str, mod_name: str) -> Any:
    spec = importlib.util.spec_from_file_location(mod_name, _SCRIPTS / f"{rel_name}.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


_adapt = _load("t12_m02_arm_adapter", "t12_m02_arm_adapter")
_contract = _load("t12_m02_f2p_contract", "t12_m02_f2p_contract")
_exe = _load("t12_m02_execute_f2p", "t12_m02_execute_f2p")
_identity = _load("t12_m02_d3r2_identity", "t12_m02_d3r2_identity")
_receipts = _load("t12_m02_receipts", "t12_m02_receipts")

WORKER_SCHEMA = "t12_m02_d3r2_worker_input_v1"

# D4 safety constants for the per-arm container-instance event window:
# ``docker events --since`` is padded BEFORE the engine call by
# EVENT_SINCE_PAD_S (preflight-verified host<->WSL skew <= 0.5 s plus spawn
# latency), the daemon stream's ``--until`` is the REAL wall deadline the
# orchestrator forwarded (the worker must finish before it), the tail grace
# bounds a natural exit wait before terminate/kill and a validating rebuild
# tolerates inter-clock noise up to EVENT_WINDOW_TOLERANCE_S.
EVENT_SINCE_PAD_S = 5.0
EVENT_WINDOW_TOLERANCE_S = 5.0
EVENT_TAIL_GRACE_S = 15.0
EVENT_REAP_GRACE_S = 5.0


def _load_frozen(worktree: Path, rel: str, name: str) -> Any:
    return _exe._load_frozen_module(worktree, rel, name)


def _default_db_scan(cmd: str | None) -> list[str]:
    """Real read-only scan of the isolated PG fixture (operator-supplied)."""
    if not cmd:
        raise RuntimeError("TEARDOWN_NOT_VERIFIED: T12_M02_DB_SCAN_CMD not configured")
    return shlex.split(cmd, posix=(os.name != "nt"))


def run_arm(witness_input: Path, out_dir: Path, *, db_scan_cmd_env: str | None = None) -> dict[str, Any]:
    """Execute EXACTLY ONE arm; returns the arm stage result (never raises on
    scientific outcome; raises on engineering contract violations)."""
    cfg = json.loads(witness_input.read_text(encoding="utf-8"))
    if cfg.get("schema") != WORKER_SCHEMA:
        raise ValueError(f"worker input schema {cfg.get('schema')!r} != {WORKER_SCHEMA!r}")
    arm = cfg["arm"]
    worktree = Path(cfg["worktree"])
    source_repo = Path(cfg["source_repo"])
    scopes_dir = Path(cfg["scopes_dir"])
    classification = Path(cfg["classification"])
    test_authority = Path(cfg["test_authority"])
    wt_linux = cfg["worktree_linux"]
    expected_oid = cfg["effective_tree_oid"]
    pinned_oci = cfg.get("pinned_oci", _identity.PINNED_PY312_OCI_ID)
    stage: dict[str, Any] = {
        "schema": "t12_m02_d3r2_worker_stage_v1",
        "arm_id": arm,
        "status": "NOT_RUN",
        "control_outcome": "NOT_RUN",
        "stages": {},
        "worker_utc_start": _identity.utc_now(),
    }
    run_dir = out_dir / "receipts"
    witness = _identity.span_witness(
        nonce=_identity.new_nonce(),
        pid=int(os.getpid()),
        parent_pid=int(os.getppid()),
        argv=list(sys.argv),
        worker_script_path=Path(__file__).resolve(),
        monotonic_start_ns=time.monotonic_ns(),
        monotonic_end_ns=0,                    # filled at end
        start_utc=stage["worker_utc_start"],
        end_utc="",
        exit_code=0,
        worker_os_start=_identity.windows_os_process_start(int(os.getpid())),
    )
    try:
        # ---- 0) worktree admission on the OS that owns it, BEFORE side effects
        probe = _identity.PlatformProbe()
        gate = _identity.linux_worktree_gate(probe, wt_linux, expected_oid)
        stage["stages"]["worktree_gate_pre"] = gate
        if not gate["pass"]:
            raise RuntimeError("WORKTREE_GATE_FAILED_PRE:" + ";".join(gate["reasons"]))
        # ---- 1) real materializer (frozen CLI) ----
        mat_dir = out_dir / "materialize_record"
        argv = [
            "python", str(worktree / cfg["materializer_rel"]),
            "--repo", str(source_repo),
            "--parent", _adapt.FROZEN_PARENT,
            "--target", _adapt.FROZEN_TARGET,
            "--task-id", _adapt.FROZEN_TASK,
            "--scope-json", str(scopes_dir / f"scope_{arm}.json"),
            "--classification-json", str(classification),
            "--test-authority-json", str(test_authority),
            "--out-dir", str(mat_dir),
        ]
        proc = subprocess.run(argv, capture_output=True, text=True,
                              encoding="utf-8", timeout=900, check=False)
        if proc.returncode != 0:
            raise RuntimeError("MATERIALIZE_FAILED:" + (proc.stderr or "")[-400:])
        records = _exe._load_materialize_records(mat_dir)
        bad = [r for r in records
               if r.get("scope_hash") != cfg.get("scope_hash")
               or r.get("reference_patch_sha256") != cfg.get("patch_sha256")]
        if bad:
            raise RuntimeError("MATERIALIZER_RECORD_MISMATCH")
        stage["stages"]["materialize"] = {"exit": proc.returncode, "record_digests_match": True}
        # ---- 2) engine imports (real frozen modules) ----
        harness = _load_frozen(worktree, _exe.HARNESS_REL, "benchmark_harness_v3")
        isolated_mod = _load_frozen(worktree, _exe.ISOLATED_RUNTIME_REL, "benchmark_opws_isolated_runtime_v1")
        manifests = harness.target_manifests(_adapt.FROZEN_TARGET)
        fragment_raw, install_mode, install_evidence = harness.lock_install_script(wt_linux, manifests)
        if not isinstance(fragment_raw, str) or not fragment_raw.strip():
            raise RuntimeError("INSTALL_FRAGMENT_EMPTY")
        isolated = isolated_mod.OpwsIsolatedRuntime(
            worktree_linux=wt_linux,
            scratch_linux=f"{cfg['scratch_linux_base']}/{out_dir.parent.name}",
            scratch_windows=str(out_dir),
            db_commit_short=_exe.TASK8,
        )
        isolated.validate()
        stage["stages"]["engine_imports"] = {"ok": True, "install_mode": install_mode}
        # ---- 3) bounded READ-ONLY container-instance stream for this arm's
        # window: started BEFORE the engine call (concurrent capture; a docker
        # event stream is a daemon read with no side effects) and stopped right
        # after the engine returns.
        container_evidence = {"container_instance_status": "CONTAINER_INSTANCE_NOT_MEASURED",
                              "reason": "docker events capture disabled or unavailable"}
        events_cap: dict[str, Any] | None = None
        cap_proc: Any = None
        cap_file = out_dir / "docker_events_window.jsonl"
        run_start = _identity.utc_seconds()
        run_end: str | None = None
        # D4: the stream's ``--since`` is projected BEFORE the engine call
        # (padded), and its ``--until`` is the REAL wall deadline the
        # orchestrator forwarded (the worker must finish inside it) — so the
        # window DEMONSTRABLY covers the engine interval.  The old defect
        # projected ``until`` before ``run_state_v3`` and pushed the arm's
        # create/start events outside the stream; an unbounded or invented
        # bound is a fail-closed error.  The capture is finished (terminated/
        # awaited) on EVERY path including engine exceptions.
        since_proj, until_proj = "", ""
        if cfg.get("docker_events"):
            since_proj = _events_since_projection(run_start)
            until_proj = _events_until_projection(cfg)
            cap_proc, _ = _start_events_capture(cap_file, since=since_proj, until=until_proj)
        try:
            # ---- 4) the REAL frozen one-arm engine call ----
            result = harness.run_state_v3(
                era_key="py312",
                worktree_linux=wt_linux,
                tid=_exe.TID,
                state=arm,
                test_files=list(_adapt.F2P_NODES),
                install_fragment=fragment_raw,
                locked_dev_fragment="echo NO_LOCKED_DEV_GROUP",
                raw_junit_dir=str(run_dir / "engine_raw_junit"),
                timeout_s=7200,
                isolated=isolated,
            )
            run_end = _identity.utc_seconds()
        finally:
            # Always close + await the stream: success AND every exception
            # path.  ``_finish_events_capture`` never raises; the engine
            # exception (if any) still propagates to the outer handler.
            if cap_proc is not None:
                events_cap = _finish_events_capture(
                    cap_proc, cap_file, pinned_oci,
                    run_start=run_start, run_end=run_end,
                    since_proj=since_proj, until_proj=until_proj)
                cap_proc = None
                stage["stages"]["container_events"] = events_cap
        if events_cap is not None:
            if events_cap.get("status") == "MEASURED":
                container_evidence = {
                    "container_instance_status": "MEASURED",
                    "instances": str(events_cap.get("instances")),
                    "image_digest": pinned_oci,
                }
            else:
                container_evidence = {
                    "container_instance_status": "CONTAINER_INSTANCE_NOT_MEASURED",
                    "reason": str(events_cap.get("reason")),
                    "capture_log": str(cap_file.read_text(encoding="utf-8", errors="replace")[-1000:]
                                        if cap_file.exists() else ""),
                }
        stage["stages"]["run_state_v3"] = {
            "start_utc": run_start, "end_utc": run_end,
            "db_name": result.get("db_name"),
            "result_error": result.get("error"),
        }
        # ---- 5) honest evidence checks ----
        db_name = result.get("db_name")
        if not isinstance(db_name, str) or not _receipts.DB_IDENTITY_RE.match(db_name):
            raise RuntimeError("DB_IDENTITY_UNPROVEN")
        if result.get("db_cleanup") != "DROPPED_AFTER_JUNIT_PARSE":
            raise RuntimeError("DB_CLEANUP_UNPROVEN")
        junit_files = list(result.get("junit_files") or [])
        if len(junit_files) != _exe.PILOT_JUNIT_PER_ARM:
            raise RuntimeError(f"JUNIT_COUNT_MISMATCH:{len(junit_files)}")
        mapping = _exe._canonical_junit_map(run_dir / "engine_raw_junit", run_dir / "junit", arm)
        classifications = [
            _receipts.classify_junit(run_dir / "junit" / c) for c in sorted(mapping.values())
        ]
        expected = _adapt.CONTROL_EXPECTED_JUNIT.get(arm)
        observed = set(classifications)
        if expected is not None and observed != {expected}:
            raise RuntimeError(f"CONTROL_MISMATCH:{arm} expected {expected} observed {sorted(observed)}")
        # ---- 6) real teardown DB scan + read-only snapshot hash ----
        scan_cmd = db_scan_cmd_env or os.environ.get("T12_M02_DB_SCAN_CMD")
        if not scan_cmd:
            raise RuntimeError("TEARDOWN_NOT_VERIFIED: T12_M02_DB_SCAN_CMD not configured")
        scan_proc = subprocess.run(
            _default_db_scan(scan_cmd), capture_output=True, text=True,
            encoding="utf-8", timeout=120, check=False)
        if scan_proc.returncode != 0:
            raise RuntimeError("TEARDOWN_NOT_VERIFIED: DB scan failed rc="
                               f"{scan_proc.returncode}: {scan_proc.stderr[-300:]}")
        leftovers = [t.strip() for t in (scan_proc.stdout or "").splitlines()
                     if _receipts.DB_IDENTITY_RE.match(t.strip())]
        scan_path = run_dir / "post_run_db_scan.json"
        scan_path.write_text(json.dumps({
            "remaining_opws_m3b_databases": leftovers,
            "checked_at_utc": _identity.utc_now(),
            "scan_cmd_digest": _identity.argv_digest(_default_db_scan(scan_cmd)),
        }, indent=2), encoding="utf-8")
        scan_sha = _identity.file_sha256(scan_path)
        stage["stages"]["post_run_teardown"] = {
            "engine_db_cleanup": result.get("db_cleanup"),
            "leftovers": leftovers,
            "scan_artifact": str(scan_path),
            "scan_sha256": scan_sha,
            "db_deleted": len(leftovers) == 0,
        }
        if leftovers:
            raise RuntimeError(f"DB_LEFTOVER:{leftovers}")
        # ---- 7) LIVE receipt (no fixture seeding) + real validator ----
        julist = []
        for canon in sorted(mapping.values()):
            jf = run_dir / "junit" / canon
            julist.append(_identity.file_sha256(jf) if jf.is_file() else None)
        witness["monotonic_end_ns"] = time.monotonic_ns()
        witness["times"]["end_utc"] = _identity.utc_seconds()
        receipt = _receipts.live_run_receipt_template(
            arm_id=arm, run_token=cfg.get("execution_id", f"M02E-RUN-{arm}"),
            junit_classifications=classifications,
            db_identity=db_name,
            process={
                "pid": witness["pid"], "driver_argv": witness["argv"],
                "nonce": witness["nonce"], "process_birth": witness["process_birth"],
                "container_oci_id": pinned_oci,
            },
            times={"start_utc": run_start, "end_utc": run_end,
                   "monotonic": True, "wall_seconds": 0.0},
            resources={
                "cpu_seconds": _receipts.NOT_MEASURED,
                "peak_ram_mb": _receipts.NOT_MEASURED,
                "disk_bytes": _receipts.NOT_MEASURED,
                "network_bytes": _identity.live_network_policy(None, None),
                "sampler": "NOT_MEASURED: no resource sampler wired in this mode",
            },
            teardown={
                "present": True, "db_deleted": True,
                "path": "post_run_db_scan.json", "verified_by_post_run_scan": True,
                "post_run_db_scan": leftovers,
                "post_run_db_scan_sha256": scan_sha,
            },
            materialize_provenance={
                "materializer": cfg["materializer_rel"],
                "scope_hash": cfg["scope_hash"],
                "reference_patch_sha256": cfg["patch_sha256"],
                "record_digests_match": True,
                "record_dir": str(mat_dir),
            },
            junit_dir=run_dir / "junit",
            host={"hostname": os.environ.get("COMPUTERNAME", "HOST_UNSET"), "os": "WSL2/Windows"},
            environment={"environment_id": f"live-{_adapt.FROZEN_TASK}-{witness['nonce'][:8]}"},
            pinned_image={"image": "opws-py312-isolated", "oci_id": pinned_oci,
                          "resolved_by": "frozen resolve_runtime_image (engine first fail-closed step)"},
            container=container_evidence,
            junit_receipts_sha=julist,
        )
        receipt["database"]["db_scan_snapshot_sha256"] = scan_sha
        receipt["database"]["db_scan_artifact"] = "post_run_db_scan.json"
        receipt["junit_engine_native_to_canonical"] = mapping
        receipt["engine_native_junit_dir"] = str(run_dir / "engine_raw_junit")
        _identity.assert_live_receipt(receipt)
        _receipts.write_run_receipt(run_dir, receipt)
        vres = _receipts.validate_run_receipt(run_dir)
        issues = list(vres.get("issues") or [])
        stage["stages"]["receipt_validation"] = {"status": "PASS" if not issues else "STOP",
                                                 "issues": issues[:8]}
        if issues:
            raise RuntimeError("RECEIPT_INVALID:" + ";".join(issues[:6]))
        stage["status"] = ("CONTROL_EXPECTED" if arm == "NEG"
                           else ("PASS" if expected else "PASS"))
        stage["control_outcome"] = ("CONTROL_EXPECTED" if arm == "NEG"
                                    else ("CONTROL_PASS" if expected else "OUTCOME_DATA"))
        stage["executed"] = True
    except Exception as exc:
        stage["status"] = "FAIL"
        stage["reason"] = f"{type(exc).__name__}: {exc}"
    finally:
        witness["monotonic_end_ns"] = time.monotonic_ns()
        witness["times"]["end_utc"] = _identity.utc_seconds()
        witness["exit_code"] = 0 if stage["status"] in ("PASS", "CONTROL_EXPECTED") else 2
        stage["worker_utc_end"] = _identity.utc_now()
        (out_dir / "witness.json").write_text(
            json.dumps(witness, indent=2, default=str), encoding="utf-8")
        (out_dir / "worker_stage.json").write_text(
            json.dumps(stage, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"arm": arm, "status": stage["status"],
                      "reason": stage.get("reason")}, indent=2))
    return stage


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="t12_m02_d3r2_worker",
                                 description="one-arm D3-R2 engine child (offline mission: never invoked)")
    ap.add_argument("--witness-input", required=True)
    ap.add_argument("--out", required=True)
    return ap


def _parse_events_utc(value: object) -> datetime.datetime | None:
    """Strict ISO-8601 UTC parse (Z or +00:00 only; None on anything else)."""
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        dt = datetime.datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.utcoffset() != datetime.timedelta(0):
        return None
    return dt.astimezone(datetime.UTC)


def _events_iso(dt: datetime.datetime) -> str:
    return dt.astimezone(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _events_since_projection(run_start_utc: str) -> str:
    """The ``docker events --since`` lower bound: padded BEFORE the engine
    interval so preflight-verified clock skew and spawn latency can never push
    the arm's first daemon event outside the stream."""
    dt = _parse_events_utc(run_start_utc)
    if dt is None:
        raise RuntimeError("EVENT_SINCE_INVALID")
    return _events_iso(dt - datetime.timedelta(seconds=EVENT_SINCE_PAD_S))


def _events_until_projection(cfg: dict[str, Any]) -> str:
    """The ``docker events --until`` upper bound: the REAL wall deadline
    forwarded by the orchestrator (bounded by the RD-9 exclusivity window and
    the authorized max_wall_s — never None).  This is a fixed bound the worker
    must finish inside, so it is GUARANTEED to be after the engine interval
    AND gives the daemon stream a finite termination even if this process is
    killed.  Fail closed when absent, unparseable or already past."""
    dt = _parse_events_utc(cfg.get("events_until_utc"))
    if dt is None or dt <= datetime.datetime.now(datetime.UTC):
        raise RuntimeError("EVENT_WINDOW_UNBOUNDED")
    return _events_iso(dt)


def _events_wall_epoch(value: Any) -> int:
    dt = _parse_events_utc(value)
    if dt is None:
        raise RuntimeError("EVENT_WINDOW_INVALID")
    return int(dt.timestamp())


def _start_events_capture(cap_file: Path, *, since: str, until: str) -> tuple[Any, Path]:
    """Start a bounded background ``docker events`` stream (read-only).

    ``--since`` is projected BEFORE the engine call (padded); ``--until`` is
    the real wall deadline the orchestrator forwarded, so the stream covers
    the actual engine interval and has a finite daemon-side bound.  stderr is
    captured to a side file so fail-closed diagnostics never lose the daemon
    error."""
    argv = ["wsl", "-d", _identity.WSL_DISTRO, "-u", "root", "--",
            "docker", "events", "--format", "{{json .}}",
            "--since", since, "--until", until]
    err_file = cap_file.with_suffix(".err")
    with open(cap_file, "w", encoding="utf-8") as fh, \
         open(err_file, "w", encoding="utf-8") as eh:
        proc = subprocess.Popen(argv, stdout=fh, stderr=eh, text=True, encoding="utf-8")
    return proc, cap_file


def _read_events(cap_file: Path) -> list[dict[str, Any]]:
    """Parse the capture file's JSONL lines (skipping any non-JSON line)."""
    events: list[dict[str, Any]] = []
    if cap_file.exists():
        for line in cap_file.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except Exception:
                continue
            events.append(ev)
    return events


def _finish_events_capture(
    proc: Any,
    cap_file: Path,
    image_digest: str,
    *,
    run_start: str | None = None,
    run_end: str | None = None,
    since_proj: str | None = None,
    until_proj: str | None = None,
    timeout_s: float = EVENT_TAIL_GRACE_S,
    reap_grace_s: float = EVENT_REAP_GRACE_S,
) -> dict[str, Any]:
    """Stop, bound and reap the capture; validate container-INSTANCE evidence.

    Bounded termination closed/awaited on EVERY path: bounded natural-exit
    wait -> terminate -> bounded grace wait -> kill -> bounded grace wait ->
    final poll and ``wait()`` reap.  Evidence is MEASURED only when docker
    emitted a create/start event for the pinned image whose REAL container
    instance id (never the image digest) sits inside the arm window; any
    empty, temporal, identity or stream anomaly fails closed to
    CONTAINER_INSTANCE_NOT_MEASURED.  Never raises."""
    window: dict[str, Any] = {
        "since_proj": since_proj, "until_proj": until_proj,
        "run_start_utc": run_start, "run_end_utc": run_end,
    }
    exited = proc.poll() is not None
    if not exited and timeout_s > 0:
        t_end = time.monotonic() + float(timeout_s)
        while time.monotonic() < t_end:
            time.sleep(0.1)
            if proc.poll() is not None:
                exited = True
                break
    terminated = False
    if not exited:
        try:
            proc.terminate()
            terminated = True
        except Exception:
            pass
        grace_end = time.monotonic() + float(reap_grace_s)
        while time.monotonic() < grace_end:
            time.sleep(0.1)
            if proc.poll() is not None:
                exited = True
                break
    killed = False
    if not exited:
        try:
            proc.kill()
            killed = True
        except Exception:
            pass
        grace_end = time.monotonic() + float(reap_grace_s)
        while time.monotonic() < grace_end:
            time.sleep(0.1)
            if proc.poll() is not None:
                exited = True
                break
    exited = proc.poll() is not None
    reaped = False
    if exited:
        try:
            proc.wait(timeout=float(reap_grace_s))
            reaped = True
        except Exception:
            reaped = False
    events = _read_events(cap_file)
    if not exited:
        return {
            "status": "CONTAINER_INSTANCE_NOT_MEASURED",
            "reason": "docker events capture process never exited after terminate/kill",
            "capture_exited": False, "terminated": terminated, "killed": killed,
            "reaped": reaped, "window": window, "events_seen": len(events), "instances": [],
        }
    if run_start is not None and run_end is None:
        # The engine call did not complete (exception): a finished arm window
        # was never measured, so instance evidence is NEVER claimed fail-closed.
        return {
            "status": "CONTAINER_INSTANCE_NOT_MEASURED",
            "reason": "engine interval end not measured (run did not complete); instance evidence unclaimed",
            "capture_exited": True, "terminated": terminated, "killed": killed,
            "reaped": reaped, "window": window, "events_seen": len(events),
            "instances": [],
        }
    img12 = str(image_digest).split(":")[-1][:12]
    start_epoch = _events_wall_epoch(since_proj) if since_proj is not None else None
    end_epoch = (_events_wall_epoch(run_end) if run_end is not None
                 else (_events_wall_epoch(until_proj) if until_proj is not None else None))
    tol = EVENT_WINDOW_TOLERANCE_S
    matched: list[dict[str, Any]] = []
    anomalies: list[str] = []
    for ev in events:
        ev_time = ev.get("time")
        action = str(ev.get("Action") or ev.get("action") or "")
        actor_json = json.dumps(ev.get("Actor") or {})
        if action not in ("create", "start"):
            continue
        if img12 not in actor_json:
            continue
        if not isinstance(ev_time, (int, float)):
            anomalies.append("EVENT_WITHOUT_TIMESTAMP")
            continue
        # relevant run window: the event must fall inside the arm window
        # (tolerant of the preflight-verified <= 0.5 s host<->WSL skew).
        if (start_epoch is not None and end_epoch is not None
                and not (start_epoch - tol <= float(ev_time) <= end_epoch + tol)):
            anomalies.append("EVENT_OUTSIDE_ARM_WINDOW")
            continue
        inst = str(ev.get("id") or (ev.get("Actor") or {}).get("ID") or "").strip()
        # a REAL container instance id: non-empty, long enough to be a daemon
        # id, and never the image digest (fail closed on substitution).
        if len(inst) < 12 or inst == image_digest or inst.lower().startswith("sha256:"):
            anomalies.append("EVENT_WITHOUT_INSTANCE_ID")
            continue
        matched.append({"container_id": inst, "action": action, "time": ev_time})
    if not matched:
        return {
            "status": "CONTAINER_INSTANCE_NOT_MEASURED",
            "reason": "no pinned-image create/start event with a real container instance id in the arm window",
            "capture_exited": True, "terminated": terminated, "killed": killed,
            "reaped": reaped, "window": window, "events_seen": len(events),
            "anomalies": anomalies, "instances": [],
        }
    return {
        "status": "MEASURED",
        "instances": matched,
        "capture_exited": True, "terminated": terminated, "killed": killed,
        "reaped": reaped, "window": window, "events_seen": len(events),
        "anomalies": anomalies, "image_digest": image_digest,
        "note": "container instance ids come from daemon events only; an image digest is never an instance id",
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=False)
    stage = run_arm(Path(args.witness_input), out_dir)
    return 0 if stage["status"] in ("PASS", "CONTROL_EXPECTED") else 2


if __name__ == "__main__":
    sys.exit(main())
